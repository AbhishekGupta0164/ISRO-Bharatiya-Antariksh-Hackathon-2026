"""Route Network API — exposes the full city graph with live AQI weights."""

from __future__ import annotations

from fastapi import APIRouter

from apps.backend.services.aqi_service import (
    fetch_all_cities_aqi,
    get_edge_pollution,
    get_pollution_weight_for_city,
)
from apps.backend.services.route_service import EDGE_DISTANCES

router = APIRouter(tags=["Route Network"])


# City display metadata (coords relative to an 800×500 canvas)
CITY_META: dict[str, dict] = {
    "A": {"name": "Delhi", "x": 80, "y": 80},
    "B": {"name": "Jaipur", "x": 180, "y": 140},
    "C": {"name": "Agra", "x": 220, "y": 100},
    "D": {"name": "Varanasi", "x": 420, "y": 150},
    "E": {"name": "Lucknow", "x": 380, "y": 100},
    "F": {"name": "Kolkata", "x": 700, "y": 200},
    "AMD": {"name": "Ahmedabad", "x": 100, "y": 220},
    "MUM": {"name": "Mumbai", "x": 80, "y": 320},
    "PNE": {"name": "Pune", "x": 120, "y": 340},
    "HYD": {"name": "Hyderabad", "x": 280, "y": 360},
    "BLR": {"name": "Bengaluru", "x": 220, "y": 450},
    "CHN": {"name": "Chennai", "x": 320, "y": 460},
}


def _aqi_to_color(aqi: float) -> str:
    """Return a hex color for an AQI value."""
    if aqi <= 50:
        return "#10b981"  # green
    elif aqi <= 100:
        return "#f59e0b"  # yellow
    elif aqi <= 150:
        return "#f97316"  # orange
    elif aqi <= 200:
        return "#ef4444"  # red
    elif aqi <= 300:
        return "#a855f7"  # purple
    else:
        return "#7f1d1d"  # maroon


@router.get("/route-network")
def get_route_network():
    """Return full city graph: nodes with AQI data + edges with distances & pollution."""
    all_aqi = fetch_all_cities_aqi()

    nodes = []
    for code, meta in CITY_META.items():
        aqi_data = all_aqi.get(code)
        aqi_val = int(aqi_data.aqi) if aqi_data else 0
        category = aqi_data.category if aqi_data else "Unknown"
        weight = get_pollution_weight_for_city(code)
        nodes.append(
            {
                "id": code,
                "name": meta["name"],
                "x": meta["x"],
                "y": meta["y"],
                "aqi": aqi_val,
                "category": category,
                "color": _aqi_to_color(aqi_val),
                "pollution_weight": round(weight, 4),
            }
        )

    edges = []
    for (c1, c2), dist in EDGE_DISTANCES.items():
        pollution = get_edge_pollution(c1, c2)
        avg_aqi_a = all_aqi.get(c1)
        avg_aqi_b = all_aqi.get(c2)
        avg_aqi = int(
            ((avg_aqi_a.aqi if avg_aqi_a else 0) + (avg_aqi_b.aqi if avg_aqi_b else 0)) / 2
        )
        edges.append(
            {
                "source": c1,
                "target": c2,
                "distance": dist,
                "pollution": round(pollution, 4),
                "avg_aqi": avg_aqi,
                "color": _aqi_to_color(avg_aqi),
            }
        )

    return {
        "nodes": nodes,
        "edges": edges,
        "total_nodes": len(nodes),
        "total_edges": len(edges),
    }
