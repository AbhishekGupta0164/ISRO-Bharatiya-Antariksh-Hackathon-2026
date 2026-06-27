"""Route service with satellite grid pathfinding.

Uses A* search over the 0.1 degree India spatial grid, with a cost function
integrating satellite-derived PM2.5 and penalties for HCHO hotspots.
"""

from __future__ import annotations

import heapq
import numpy as np
from datetime import datetime

from apps.backend.services.aqi_service import CITY_PROFILES

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
from apps.backend.services.satellite_aqi_service import satellite_service, pm25_to_aqi
from apps.backend.services.eco_route_model import _weights
from models.hotspot.hcho_gridder import get_seasonal_composite
from models.hotspot.hotspot_detector import detect_hotspots

# India grid boundary config
LAT_MIN, LAT_MAX = 7.0, 37.0
LON_MIN, LON_MAX = 68.0, 98.0
RESOLUTION = 0.1
GRID_SIZE = 300

# Default city coordinates from profiles
def get_city_coords(node_id: str) -> tuple[float, float]:
    node_id = node_id.strip().upper()
    if node_id in CITY_PROFILES:
        return CITY_PROFILES[node_id]["lat"], CITY_PROFILES[node_id]["lon"]
    # If the node_id itself is a coord string "lat,lon"
    if "," in node_id:
        try:
            lat, lon = map(float, node_id.split(","))
            return lat, lon
        except ValueError:
            pass
    # Fallback to Delhi
    return 28.6139, 77.2090

def haversine_dist(lat1, lon1, lat2, lon2):
    R = 6371.0
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
    c = 2 * np.arcsin(np.sqrt(a))
    return R * c

def get_hcho_hotspots():
    """Fetches detected hotspots dynamically."""
    try:
        # Load seasonal composites and run DBSCAN detector
        date_str = datetime.today().strftime("%Y-%m-%d")
        comp = get_seasonal_composite(date_str, date_str)
        return detect_hotspots(comp)
    except Exception as e:
        print(f"[WARN] Failed fetching HCHO hotspots for routing: {e}")
        return []

def run_astar_grid(
    start_lat: float,
    start_lon: float,
    end_lat: float,
    end_lon: float,
    alpha: float,
    traffic_multiplier: float = 1.0,
    hotspots: list = None
) -> tuple[list[tuple[float, float]], float, float]:
    """
    Computes optimal path on 0.1 degree grid between start and end using A* search.
    Avoids cells within HCHO hotspot polygons.
    """
    if hotspots is None:
        hotspots = []
        
    # Get latest PM2.5 grid
    pm25_grid, _ = satellite_service.get_latest_satellite_grid()
    
    # Map lat/lon to grid indices
    start_r = int(np.clip(round((start_lat - LAT_MIN) / RESOLUTION), 0, GRID_SIZE - 1))
    start_c = int(np.clip(round((start_lon - LON_MIN) / RESOLUTION), 0, GRID_SIZE - 1))
    
    end_r = int(np.clip(round((end_lat - LAT_MIN) / RESOLUTION), 0, GRID_SIZE - 1))
    end_c = int(np.clip(round((end_lon - LON_MIN) / RESOLUTION), 0, GRID_SIZE - 1))
    
    # A* structures
    # pq: queue of (f_score, cost, (r, c), path_history, dist_history, exp_history)
    start_node = (start_r, start_c)
    end_node = (end_r, end_c)
    
    # Early escape if start matches end
    if start_node == end_node:
        lat = LAT_MIN + start_r * RESOLUTION
        lon = LON_MIN + start_c * RESOLUTION
        return [(lat, lon)], 0.0, 0.0
        
    pq = [(0.0, 0.0, start_node, [start_node], 0.0, 0.0)]
    visited = {} # cell -> min cost to reach
    
    # Search loop
    while pq:
        f, cost, (r, c), path, d_sum, exp_sum = heapq.heappop(pq)
        
        if (r, c) == end_node:
            # Convert grid path back to lat/lon
            coord_path = [(float(LAT_MIN + pr * RESOLUTION), float(LON_MIN + pc * RESOLUTION)) for (pr, pc) in path]
            return coord_path, d_sum, exp_sum
            
        if (r, c) in visited and visited[(r, c)] <= cost:
            continue
            
        visited[(r, c)] = cost
        
        # 8-way neighbors
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < GRID_SIZE and 0 <= nc < GRID_SIZE:
                # Step distance (orthogonal vs diagonal)
                is_diagonal = dr != 0 and dc != 0
                step_dist = 11.1 * np.sqrt(2) if is_diagonal else 11.1
                
                # Pollution exposure weight (PM2.5 mapped to 1-10 range)
                pm25 = float(pm25_grid[nr, nc])
                pollution_weight = pm25 / 40.0 # scale pm2.5 to typical weight range (0 to 10)
                pollution_weight = np.clip(pollution_weight, 1.0, 10.0) * traffic_multiplier
                
                # Hotspot Avoidance Penalty
                cell_lat = LAT_MIN + nr * RESOLUTION
                cell_lon = LON_MIN + nc * RESOLUTION
                
                hotspot_penalty = 0.0
                for hs in hotspots:
                    # If within 0.6 degrees (~60km) of hotspot centroid, penalize heavily
                    dist_to_hs = haversine_dist(cell_lat, cell_lon, hs.centroid_lat, hs.centroid_lon)
                    if dist_to_hs <= 60.0:
                        hotspot_penalty += 300.0 # massive pollution weight penalty
                        
                adjusted_pollution = pollution_weight + hotspot_penalty
                
                # Step Cost blend: cost = dist * (alpha + (1-alpha) * pollution)
                step_cost = step_dist * (alpha + (1.0 - alpha) * adjusted_pollution)
                
                new_cost = cost + step_cost
                new_d_sum = d_sum + step_dist
                new_exp_sum = exp_sum + (step_dist * pm25)
                
                # Heuristic: remaining straight line distance * alpha
                rem_lat = LAT_MIN + nr * RESOLUTION
                rem_lon = LON_MIN + nc * RESOLUTION
                h = alpha * haversine_dist(rem_lat, rem_lon, end_lat, end_lon)
                
                new_f = new_cost + h
                
                neighbor = (nr, nc)
                if neighbor not in visited or visited[neighbor] > new_cost:
                    heapq.heappush(pq, (new_f, new_cost, neighbor, path + [neighbor], new_d_sum, new_exp_sum))
                    
    # Fallback straight line segment if pathfinding fails
    return [(start_lat, start_lon), (end_lat, end_lon)], haversine_dist(start_lat, start_lon, end_lat, end_lon), 0.0

def is_valid_node(node_id: str) -> bool:
    node_id = node_id.strip().upper()
    if node_id in CITY_PROFILES:
        return True
    if "," in node_id:
        try:
            lat, lon = map(float, node_id.split(","))
            return LAT_MIN <= lat <= LAT_MAX and LON_MIN <= lon <= LON_MAX
        except ValueError:
            pass
    return False

def get_route_service(
    start: str,
    end: str,
    traffic_multiplier: float = 1.0,
    route_type: str = "full"
):
    """Compute eco-route using satellite grid pathfinding."""
    if not is_valid_node(start) or not is_valid_node(end):
        return {"error": "Invalid start or end node"}
        
    start_lat, start_lon = get_city_coords(start)
    end_lat, end_lon = get_city_coords(end)
    
    hotspots = get_hcho_hotspots()
    
    # 1. SHORTEST PATH (alpha = 1.0, ignores pollution)
    s_coords, s_dist, s_exp = run_astar_grid(start_lat, start_lon, end_lat, end_lon, alpha=1.0, traffic_multiplier=traffic_multiplier, hotspots=hotspots)
    s_route = [start] + [f"{lat:.4f},{lon:.4f}" for lat, lon in s_coords[1:-1]] + [end]
    
    # Define alphas for choices
    alphas = {
        "shortest": 1.0,
        "medium": 0.5,
        "full": _weights.get("distance_weight", 0.15)
    }
    
    paths = {}
    alt_coords = {}
    alt_metrics = {}
    
    for rtype, alpha in alphas.items():
        if rtype == "shortest":
            paths[rtype] = s_route
            alt_coords[rtype] = s_coords
            alt_metrics[rtype] = (s_dist, s_exp)
            continue
            
        coords, dist, exp = run_astar_grid(start_lat, start_lon, end_lat, end_lon, alpha=alpha, traffic_multiplier=traffic_multiplier, hotspots=hotspots)
        paths[rtype] = [start] + [f"{lat:.4f},{lon:.4f}" for lat, lon in coords[1:-1]] + [end]
        alt_coords[rtype] = coords
        alt_metrics[rtype] = (dist, exp)
        
    eco_path = paths[route_type]
    eco_dist, eco_exp = alt_metrics[route_type]
    
    # Improvement calculation
    improvement_pct = 0.0
    if s_exp > 0:
        improvement_pct = max(0.0, (s_exp - eco_exp) / s_exp * 100.0)
    improvement_str = f"{improvement_pct:.1f}% Improvement"
    
    # Credit engine integration
    from apps.backend.services.exposure_credit import calculate_route_credits, route_credits_to_dict
    
    is_eco = (route_type != "shortest")
    
    # Construct dummy distances dictionary mapping for compatibility
    distances_map = {}
    for i in range(len(eco_path) - 1):
        c1, c2 = eco_path[i], eco_path[i+1]
        lat1, lon1 = get_city_coords(c1)
        lat2, lon2 = get_city_coords(c2)
        distances_map[(c1, c2)] = haversine_dist(lat1, lon1, lat2, lon2)
        
    shortest_distances_map = {}
    for i in range(len(s_route) - 1):
        c1, c2 = s_route[i], s_route[i+1]
        lat1, lon1 = get_city_coords(c1)
        lat2, lon2 = get_city_coords(c2)
        shortest_distances_map[(c1, c2)] = haversine_dist(lat1, lon1, lat2, lon2)
        
    # Calculate credits
    eco_credits = calculate_route_credits(eco_path, distances=distances_map, is_eco_route=is_eco, shortest_route=s_route)
    shortest_credits = calculate_route_credits(s_route, distances=shortest_distances_map, is_eco_route=False)
    
    # Compile alternatives
    alternatives = []
    for rtype, rpath in paths.items():
        r_dist, r_exp = alt_metrics[rtype]
        r_coords = alt_coords[rtype]
        
        # Build coordinates list for custom geocoding rendering
        custom_coords = [[float(lat), float(lon)] for lat, lon in r_coords]
        
        r_distances = {}
        for i in range(len(rpath) - 1):
            c1, c2 = rpath[i], rpath[i+1]
            lat1, lon1 = get_city_coords(c1)
            lat2, lon2 = get_city_coords(c2)
            r_distances[(c1, c2)] = haversine_dist(lat1, lon1, lat2, lon2)
            
        r_credits = calculate_route_credits(rpath, distances=r_distances, is_eco_route=(rtype != "shortest"), shortest_route=s_route)
        
        alternatives.append({
            "type": rtype,
            "route": rpath,
            "custom_coords": custom_coords,
            "total_distance": round(r_dist, 2),
            "total_pollution": round(r_exp, 2),
            "exposure_credits": route_credits_to_dict(r_credits)
        })
        
    # Collect cities AQI details for display in frontend
    # Filter grid values for the 12 main cities profiles
    aqi_info = {}
    for code, profile in CITY_PROFILES.items():
        pm25 = satellite_service.get_pm25_for_coords(profile["lat"], profile["lon"])
        aqi_val = satellite_service.get_aqi_for_coords(profile["lat"], profile["lon"])
        
        aqi_info[code] = {
            "city": profile["name"],
            "aqi": aqi_val,
            "category": "Good" if aqi_val <= 50 else ("Moderate" if aqi_val <= 100 else "Unhealthy"),
            "dominant_pollutant": "PM2.5",
            "pollution_weight": pm25 / 40.0,
            "source": "Satellite GWR/LSTM"
        }
        
    return {
        "route": eco_path,
        "total_distance": round(eco_dist, 2),
        "total_pollution": round(eco_exp, 2),
        "shortest_route": s_route,
        "shortest_distance": round(s_dist, 2),
        "shortest_exposure": round(s_exp, 2),
        "improvement": improvement_str,
        "aqi_data": aqi_info,
        "data_source": "satellite-grid",
        "exposure_credits": route_credits_to_dict(eco_credits),
        "shortest_credits": route_credits_to_dict(shortest_credits),
        "alternatives": alternatives
    }
