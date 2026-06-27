"""Route service with real-time AQI integration.

Uses live air quality data (from Open-Meteo / WAQI) to compute edge
pollution weights instead of hardcoded values.  Falls back to default
weights when the AQI service is unreachable.
"""

from __future__ import annotations

from apps.backend.services import graph_store
from apps.backend.services.aqi_service import (
    fetch_all_cities_aqi,
    get_edge_pollution,
    get_pollution_weight_for_city,
)
from apps.backend.services.eco_route_model import choose_best_neighbor
from apps.simulator.evaluator import Graph, RLEnv, get_route
from packages.shared.utils import percent_improvement

# Default static distances (km) between cities — real distances along roads
EDGE_DISTANCES: dict[tuple[str, str], float] = {
    ("A", "B"): 280,  # Delhi → Jaipur
    ("A", "C"): 230,  # Delhi → Agra
    ("B", "D"): 680,  # Jaipur → Varanasi
    ("C", "D"): 540,  # Agra → Varanasi
    ("C", "E"): 330,  # Agra → Lucknow
    ("D", "E"): 300,  # Varanasi → Lucknow
    ("D", "F"): 680,  # Varanasi → Kolkata
    ("E", "F"): 990,  # Lucknow → Kolkata
    ("B", "AMD"): 680, # Jaipur -> Ahmedabad
    ("A", "AMD"): 940, # Delhi -> Ahmedabad
    ("AMD", "MUM"): 530, # Ahmedabad -> Mumbai
    ("MUM", "PNE"): 150, # Mumbai -> Pune
    ("PNE", "BLR"): 840, # Pune -> Bengaluru
    ("MUM", "HYD"): 710, # Mumbai -> Hyderabad
    ("HYD", "BLR"): 570, # Hyderabad -> Bengaluru
    ("BLR", "CHN"): 350, # Bengaluru -> Chennai
    ("HYD", "CHN"): 630, # Hyderabad -> Chennai
    ("F", "CHN"): 1670, # Kolkata -> Chennai
}


# =====================
# HELPERS
# =====================
def compute_exposure(graph: Graph, path: list[str]) -> float:
    total = 0.0
    for i in range(len(path) - 1):
        for n, dist, pol in graph.get_neighbors(path[i]):
            if n == path[i + 1]:
                total += dist * pol
    return round(total, 2)


def compute_distance(graph: Graph, path: list[str]) -> float:
    total = 0.0
    for i in range(len(path) - 1):
        for n, dist, _ in graph.get_neighbors(path[i]):
            if n == path[i + 1]:
                total += dist
    return round(total, 2)


def _build_graph_with_real_aqi(traffic_multiplier: float = 1.0) -> tuple[Graph, dict]:
    """Build the city graph using real-time AQI-based pollution weights."""
    # Pre-fetch all cities' AQI in one shot (cached)
    all_aqi = fetch_all_cities_aqi()

    g = Graph()
    aqi_info: dict[str, dict] = {}

    for (c1, c2), dist in EDGE_DISTANCES.items():
        pollution = get_edge_pollution(c1, c2) * traffic_multiplier
        g.add_road(c1, c2, dist, pollution)

    # Collect AQI summaries for the response
    for code, aqi_data in all_aqi.items():
        inflated_aqi = int(aqi_data.aqi * traffic_multiplier)
        aqi_info[code] = {
            "city": aqi_data.city_name,
            "aqi": inflated_aqi,
            "category": aqi_data.category,
            "dominant_pollutant": aqi_data.dominant_pollutant,
            "pollution_weight": get_pollution_weight_for_city(code) * traffic_multiplier,
            "source": aqi_data.source,
        }

    return g, aqi_info


def _build_graph() -> Graph:
    """Build a Graph instance from the persisted graph store."""
    g = Graph()
    data = graph_store.get_graph()
    for node_id in data["cities"]:
        g.add_city(node_id)
    for road in data["roads"]:
        g.add_road(road["from"], road["to"], road["distance"], road["pollution"])
    return g
# =====================
# MAIN SERVICE
# =====================
def get_route_service(start: str, end: str, traffic_multiplier: float = 1.0, route_type: str = "full"):
    """Compute eco-route using real-time AQI pollution data."""

    g, aqi_info = _build_graph_with_real_aqi(traffic_multiplier)

    # VALIDATION
    if start not in g.graph or end not in g.graph:
        return {"error": "Invalid start or end node"}

    # BASELINE ROUTE (shortest path)
    baseline = get_route(g, start, end, alpha=1.0)
    if baseline is None:
        return {"error": f"No path exists between '{start}' and '{end}'. Add roads to connect them."}
    shortest_path = baseline["path"]
    shortest_exposure = baseline["total_exposure"]

    paths = {}
    for rtype in ["shortest", "medium", "full"]:
        if rtype == "shortest":
            paths[rtype] = shortest_path
            continue

        env = RLEnv(g, start=start, destination=end)
        state = env.reset()
        path = [state]
    
        done = False
        visited = set()
        steps = 0
    
        while not done:
            visited.add(state)
    
            neighbors = g.get_neighbors(state)
            neighbors = [(n, d, p) for (n, d, p) in neighbors if n not in visited]
    
            if not neighbors:
                break
    
            action = choose_best_neighbor(
                type("obj", (), {"total_exposure": 0}),
                neighbors,
                destination=end,
                route_type=rtype,
            )
    
            next_state, reward, done = env.step(action)
    
            path.append(next_state)
            state = next_state
    
            steps += 1
            if steps > 20:
                break
    
        # FALLBACK
        if len(path) < 2 or path[-1] != end:
            paths[rtype] = shortest_path
        else:
            paths[rtype] = path

    eco_path = paths[route_type]

    # METRICS
    eco_exposure = compute_exposure(g, eco_path)
    eco_distance = compute_distance(g, eco_path)

    # IMPROVEMENT
    improvement_str = percent_improvement(shortest_exposure, eco_exposure)

    # EXPOSURE CREDITS
    from apps.backend.services.exposure_credit import (
        calculate_route_credits,
        route_credits_to_dict,
    )

    is_eco = eco_path != shortest_path
    eco_credits = calculate_route_credits(
        eco_path,
        distances=EDGE_DISTANCES,
        is_eco_route=is_eco,
        shortest_route=shortest_path,
    )
    shortest_credits = calculate_route_credits(
        shortest_path,
        distances=EDGE_DISTANCES,
        is_eco_route=False,
    )
    
    alternatives = []
    for rtype, rpath in paths.items():
        is_eco_r = rpath != shortest_path
        r_credits = calculate_route_credits(
            rpath,
            distances=EDGE_DISTANCES,
            is_eco_route=is_eco_r,
            shortest_route=shortest_path,
        )
        alternatives.append({
            "type": rtype,
            "route": rpath,
            "total_distance": compute_distance(g, rpath),
            "total_pollution": compute_exposure(g, rpath),
            "exposure_credits": route_credits_to_dict(r_credits)
        })

    # RESPONSE
    return {
        "route": eco_path,
        "total_distance": eco_distance,
        "total_pollution": eco_exposure,
        "shortest_route": shortest_path,
        "shortest_distance": compute_distance(g, shortest_path),
        "shortest_exposure": shortest_exposure,
        "improvement": improvement_str,
        "aqi_data": aqi_info,
        "data_source": "real-time",
        "exposure_credits": route_credits_to_dict(eco_credits),
        "shortest_credits": route_credits_to_dict(shortest_credits),
        "alternatives": alternatives
    }
