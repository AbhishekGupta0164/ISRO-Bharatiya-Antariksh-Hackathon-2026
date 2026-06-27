"""
Persistent graph store — cities, coordinates, and roads saved to data/graph.json.
Provides thread-safe read/write with auto-initialization of default data.
"""

from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parents[3]           # EcoNav-AI root
GRAPH_FILE = BASE_DIR / "data" / "graph.json"

_lock = threading.Lock()

# ---- Default Graph (shipped with the app) ----
DEFAULT_CITIES: dict[str, dict[str, Any]] = {
    "A": {"name": "Delhi",    "lat": 28.6139, "lng": 77.2090},
    "B": {"name": "Jaipur",   "lat": 26.9124, "lng": 75.7873},
    "C": {"name": "Agra",     "lat": 27.1767, "lng": 78.0081},
    "D": {"name": "Varanasi", "lat": 25.3176, "lng": 82.9739},
    "E": {"name": "Lucknow",  "lat": 26.8467, "lng": 80.9462},
    "F": {"name": "Kolkata",  "lat": 22.5726, "lng": 88.3639},
}

DEFAULT_ROADS: list[dict[str, Any]] = [
    {"from": "A", "to": "B", "distance": 235.3, "pollution": 10},
    {"from": "A", "to": "C", "distance": 178.1, "pollution": 3},
    {"from": "B", "to": "D", "distance": 739.0, "pollution": 2},
    {"from": "C", "to": "D", "distance": 536.6, "pollution": 6},
    {"from": "C", "to": "E", "distance": 293.4, "pollution": 1},
    {"from": "D", "to": "E", "distance": 264.4, "pollution": 2},
    {"from": "D", "to": "F", "distance": 627.0, "pollution": 8},
    {"from": "E", "to": "F", "distance": 887.0, "pollution": 1},
]


def _default_data() -> dict:
    return {"cities": DEFAULT_CITIES, "roads": DEFAULT_ROADS}


def _ensure_file() -> None:
    if not GRAPH_FILE.exists():
        GRAPH_FILE.parent.mkdir(parents=True, exist_ok=True)
        _save(_default_data())


def _load() -> dict:
    _ensure_file()
    with open(GRAPH_FILE, "r", encoding="utf-8") as fp:
        return json.load(fp)


def _save(data: dict) -> None:
    GRAPH_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(GRAPH_FILE, "w", encoding="utf-8") as fp:
        json.dump(data, fp, indent=2, ensure_ascii=False)


# ===================== PUBLIC API =====================

def get_graph() -> dict:
    """Return the full graph data: {cities: {...}, roads: [...]}."""
    with _lock:
        return _load()


def get_cities() -> dict[str, dict[str, Any]]:
    with _lock:
        return _load()["cities"]


def get_roads() -> list[dict[str, Any]]:
    with _lock:
        return _load()["roads"]


def add_city(node_id: str, name: str, lat: float, lng: float) -> dict:
    """Add a new city node. Returns updated cities dict."""
    node_id = node_id.strip().upper()
    with _lock:
        data = _load()
        if node_id in data["cities"]:
            raise ValueError(f"City node '{node_id}' already exists")
        data["cities"][node_id] = {"name": name.strip(), "lat": lat, "lng": lng}
        _save(data)
        return data["cities"]


def remove_city(node_id: str) -> dict:
    """Remove a city and all roads connected to it."""
    node_id = node_id.strip().upper()
    with _lock:
        data = _load()
        if node_id not in data["cities"]:
            raise ValueError(f"City node '{node_id}' does not exist")
        del data["cities"][node_id]
        data["roads"] = [
            r for r in data["roads"]
            if r["from"] != node_id and r["to"] != node_id
        ]
        _save(data)
        return data["cities"]


def add_road(from_id: str, to_id: str, distance: float, pollution: float) -> list:
    """Add a road between two existing cities. Returns updated roads list."""
    from_id = from_id.strip().upper()
    to_id = to_id.strip().upper()
    with _lock:
        data = _load()
        if from_id not in data["cities"]:
            raise ValueError(f"City node '{from_id}' does not exist")
        if to_id not in data["cities"]:
            raise ValueError(f"City node '{to_id}' does not exist")
        if from_id == to_id:
            raise ValueError("Cannot create a road from a city to itself")
        # Check for duplicate
        for r in data["roads"]:
            if (r["from"] == from_id and r["to"] == to_id) or \
               (r["from"] == to_id and r["to"] == from_id):
                raise ValueError(f"Road between '{from_id}' and '{to_id}' already exists")
        data["roads"].append({
            "from": from_id,
            "to": to_id,
            "distance": distance,
            "pollution": pollution,
        })
        _save(data)
        return data["roads"]


def remove_road(from_id: str, to_id: str) -> list:
    """Remove a road between two cities."""
    from_id = from_id.strip().upper()
    to_id = to_id.strip().upper()
    with _lock:
        data = _load()
        original_len = len(data["roads"])
        data["roads"] = [
            r for r in data["roads"]
            if not ((r["from"] == from_id and r["to"] == to_id) or
                    (r["from"] == to_id and r["to"] == from_id))
        ]
        if len(data["roads"]) == original_len:
            raise ValueError(f"No road found between '{from_id}' and '{to_id}'")
        _save(data)
        return data["roads"]


def reset_graph() -> dict:
    """Reset to default cities and roads."""
    with _lock:
        data = _default_data()
        _save(data)
        return data


# ===================== SMART ADD =====================

def next_node_id() -> str:
    """Return the next available single-letter node ID (A-Z)."""
    data = _load()
    used = set(data["cities"].keys())
    for c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
        if c not in used:
            return c
    # Fallback to two-letter IDs
    for c1 in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
        for c2 in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
            combo = c1 + c2
            if combo not in used:
                return combo
    raise ValueError("No available node IDs")


def _haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Haversine distance between two lat/lng points in km."""
    import math
    R = 6371  # Earth radius in km
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlng / 2) ** 2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _estimate_pollution(distance_km: float) -> int:
    """Estimate a pollution AQI index based on distance (longer routes = varied)."""
    import random
    random.seed(int(distance_km * 100))
    if distance_km < 200:
        return random.randint(1, 4)
    elif distance_km < 500:
        return random.randint(3, 7)
    else:
        return random.randint(5, 10)





def geocode_city(city_name: str) -> dict | None:
    """Look up lat/lng for a city name using OpenStreetMap Nominatim (free, no API key)."""
    import requests as _req
    try:
        resp = _req.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q": city_name, "format": "json", "limit": 1, "addressdetails": 1},
            headers={"User-Agent": "EcoNav-AI/1.0"},
            timeout=5,
        )
        if resp.status_code == 200 and resp.json():
            result = resp.json()[0]
            return {
                "lat": float(result["lat"]),
                "lng": float(result["lon"]),
                "display_name": result.get("display_name", city_name),
            }
    except Exception:
        pass
    return None


def smart_add_city(city_name: str, connect_count: int = 3) -> dict:
    """
    Adds a city by name only. Automatically:
      1. Geocodes the city to get lat/lng
      2. Assigns the next available Node ID
      3. Connects to the nearest `connect_count` existing cities with realistic distances
    Returns a summary dict with what was created.
    """
    city_name = city_name.strip()
    if not city_name:
        raise ValueError("City name cannot be empty")

    # Check for duplicate name
    data = _load()
    for info in data["cities"].values():
        if info["name"].lower() == city_name.lower():
            raise ValueError(f"A city named '{city_name}' already exists in the graph")

    # Geocode
    geo = geocode_city(city_name)
    if geo is None:
        raise ValueError(f"Could not find coordinates for '{city_name}'. Check the spelling.")

    lat, lng = geo["lat"], geo["lng"]
    node_id = next_node_id()

    # Add the city
    with _lock:
        data = _load()
        data["cities"][node_id] = {"name": city_name, "lat": lat, "lng": lng}

        # Calculate distances to all existing cities and connect to nearest ones
        distances = []
        for nid, info in data["cities"].items():
            if nid == node_id:
                continue
            dist_km = _haversine_km(lat, lng, info["lat"], info["lng"])
            distances.append((nid, info["name"], dist_km))

        distances.sort(key=lambda x: x[2])
        nearest = distances[:connect_count]

        roads_added = []
        for nid, nname, dist_km in nearest:
            distance_km = round(dist_km, 1)
            pollution = _estimate_pollution(dist_km)
            road = {"from": node_id, "to": nid, "distance": distance_km, "pollution": pollution}
            data["roads"].append(road)
            roads_added.append({
                "to_id": nid,
                "to_name": nname,
                "distance_km": distance_km,
                "pollution": pollution,
            })

        _save(data)

    return {
        "node_id": node_id,
        "city_name": city_name,
        "lat": lat,
        "lng": lng,
        "roads_added": roads_added,
    }

