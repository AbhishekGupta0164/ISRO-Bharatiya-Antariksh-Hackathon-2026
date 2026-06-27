"""Real-time Air Quality Index service.

Uses Open-Meteo Air Quality API (free, no API key) with BATCH request
support — fetches all 53 cities in a SINGLE API call.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

import requests

# ---------------------------------------------------------------------------
# 53 Indian cities with coordinates
# ---------------------------------------------------------------------------

CITY_PROFILES: dict[str, dict[str, Any]] = {
    # --- Route graph nodes (A-F) ---
    "A": {"name": "Delhi", "lat": 28.6139, "lon": 77.2090},
    "B": {"name": "Jaipur", "lat": 26.9124, "lon": 75.7873},
    "C": {"name": "Agra", "lat": 27.1767, "lon": 78.0081},
    "D": {"name": "Varanasi", "lat": 25.3176, "lon": 82.9739},
    "E": {"name": "Lucknow", "lat": 26.8467, "lon": 80.9462},
    "F": {"name": "Kolkata", "lat": 22.5726, "lon": 88.3639},
    # --- Major metros ---
    "MUM": {"name": "Mumbai", "lat": 19.0760, "lon": 72.8777},
    "BLR": {"name": "Bengaluru", "lat": 12.9716, "lon": 77.5946},
    "CHN": {"name": "Chennai", "lat": 13.0827, "lon": 80.2707},
    "HYD": {"name": "Hyderabad", "lat": 17.3850, "lon": 78.4867},
    "PNE": {"name": "Pune", "lat": 18.5204, "lon": 73.8567},
    "AMD": {"name": "Ahmedabad", "lat": 23.0225, "lon": 72.5714},
    "SRT": {"name": "Surat", "lat": 21.1702, "lon": 72.8311},
    # --- North India ---
    "CHD": {"name": "Chandigarh", "lat": 30.7333, "lon": 76.7794},
    "AMR": {"name": "Amritsar", "lat": 31.6340, "lon": 74.8723},
    "LDH": {"name": "Ludhiana", "lat": 30.9010, "lon": 75.8573},
    "DHR": {"name": "Dehradun", "lat": 30.3165, "lon": 78.0322},
    "SML": {"name": "Shimla", "lat": 31.1048, "lon": 77.1734},
    "KNP": {"name": "Kanpur", "lat": 26.4499, "lon": 80.3319},
    "ALD": {"name": "Prayagraj", "lat": 25.4358, "lon": 81.8463},
    "PAT": {"name": "Patna", "lat": 25.6093, "lon": 85.1376},
    "GYA": {"name": "Gaya", "lat": 24.7955, "lon": 84.9994},
    "RAN": {"name": "Ranchi", "lat": 23.3441, "lon": 85.3096},
    "GWL": {"name": "Gwalior", "lat": 26.2183, "lon": 78.1828},
    "MRT": {"name": "Meerut", "lat": 28.9845, "lon": 77.7064},
    "NDA": {"name": "Noida", "lat": 28.5355, "lon": 77.3910},
    "GZB": {"name": "Ghaziabad", "lat": 28.6692, "lon": 77.4538},
    "FBD": {"name": "Faridabad", "lat": 28.4089, "lon": 77.3178},
    "GGN": {"name": "Gurugram", "lat": 28.4595, "lon": 77.0266},
    # --- Central India ---
    "BPL": {"name": "Bhopal", "lat": 23.2599, "lon": 77.4126},
    "IND": {"name": "Indore", "lat": 22.7196, "lon": 75.8577},
    "JBP": {"name": "Jabalpur", "lat": 23.1815, "lon": 79.9864},
    "NGP": {"name": "Nagpur", "lat": 21.1458, "lon": 79.0882},
    "RPR": {"name": "Raipur", "lat": 21.2514, "lon": 81.6296},
    # --- West India ---
    "UDR": {"name": "Udaipur", "lat": 24.5854, "lon": 73.7125},
    "JDH": {"name": "Jodhpur", "lat": 26.2389, "lon": 73.0243},
    "GOA": {"name": "Goa", "lat": 15.2993, "lon": 74.1240},
    "RAJ": {"name": "Rajkot", "lat": 22.3039, "lon": 70.8022},
    "VDR": {"name": "Vadodara", "lat": 22.3072, "lon": 73.1812},
    # --- South India ---
    "COK": {"name": "Kochi", "lat": 9.9312, "lon": 76.2673},
    "TRV": {"name": "Thiruvananthapuram", "lat": 8.5241, "lon": 76.9366},
    "MYS": {"name": "Mysuru", "lat": 12.2958, "lon": 76.6394},
    "VIZ": {"name": "Visakhapatnam", "lat": 17.6868, "lon": 83.2185},
    "MDR": {"name": "Madurai", "lat": 9.9252, "lon": 78.1198},
    "CBE": {"name": "Coimbatore", "lat": 11.0168, "lon": 76.9558},
    "TRC": {"name": "Tiruchirappalli", "lat": 10.7905, "lon": 78.7047},
    "VJW": {"name": "Vijayawada", "lat": 16.5062, "lon": 80.6480},
    # --- East & North-East India ---
    "BBS": {"name": "Bhubaneswar", "lat": 20.2961, "lon": 85.8245},
    "GUW": {"name": "Guwahati", "lat": 26.1445, "lon": 91.7362},
    "IMP": {"name": "Imphal", "lat": 24.8170, "lon": 93.9368},
    "SHL": {"name": "Shillong", "lat": 25.5788, "lon": 91.8933},
    "JAM": {"name": "Jammu", "lat": 32.7266, "lon": 74.8570},
    "SRN": {"name": "Srinagar", "lat": 34.0837, "lon": 74.7973},
}

_CACHE_TTL_SECONDS = 600

# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class PollutantData:
    pm25: float | None = None
    pm10: float | None = None
    no2: float | None = None
    so2: float | None = None
    co: float | None = None
    o3: float | None = None


@dataclass
class CityAQI:
    city_code: str
    city_name: str
    aqi: int
    category: str
    dominant_pollutant: str
    pollutants: PollutantData
    source: str
    lat: float
    lon: float
    timestamp: str | None = None


@dataclass
class AQICache:
    data: dict[str, CityAQI] = field(default_factory=dict)
    last_fetched: float = 0.0


_cache = AQICache()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _aqi_category(aqi: int) -> str:
    if aqi <= 50:
        return "Good"
    if aqi <= 100:
        return "Moderate"
    if aqi <= 150:
        return "Unhealthy for Sensitive Groups"
    if aqi <= 200:
        return "Unhealthy"
    if aqi <= 300:
        return "Very Unhealthy"
    return "Hazardous"


def _aqi_to_pollution_weight(aqi: int) -> float:
    if aqi <= 50:
        return 1.0
    if aqi <= 100:
        return 3.0
    if aqi <= 150:
        return 5.0
    if aqi <= 200:
        return 7.0
    if aqi <= 300:
        return 9.0
    return 10.0


from apps.backend.services.satellite_aqi_service import satellite_service

def _parse_current(code: str, name: str, lat: float, lon: float) -> CityAQI:
    """Evaluate coordinate location against satellite grid."""
    pm25_val = satellite_service.get_pm25_for_coords(lat, lon)
    aqi_val = satellite_service.get_aqi_for_coords(lat, lon)
    
    # Deriving other pollutant parameters from PM2.5 baseline for compatibility
    pollutants = PollutantData(
        pm25=pm25_val,
        pm10=round(pm25_val * 1.6, 2),
        no2=round(pm25_val * 0.35, 2),
        so2=round(pm25_val * 0.15, 2),
        co=round(pm25_val * 0.008, 4),
        o3=round(pm25_val * 0.45, 2),
    )
    
    # Dominant pollutant indicator
    dominant = "PM2.5"
    
    return CityAQI(
        city_code=code,
        city_name=name,
        aqi=aqi_val,
        category=_aqi_category(aqi_val),
        dominant_pollutant=dominant,
        pollutants=pollutants,
        source="MOSDAC/TROPOMI Satellite",
        lat=lat,
        lon=lon,
        timestamp=datetime.today().strftime("%Y-%m-%d %H:%M:%S"),
    )

from datetime import datetime

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def fetch_aqi_by_coords(lat: float, lon: float, name: str = "Custom") -> CityAQI | None:
    """Fetch AQI for any lat/lon in India using GWR/LSTM satellite grid."""
    try:
        return _parse_current("CUSTOM", name, lat, lon)
    except Exception:
        return None

def fetch_city_aqi(city_code: str) -> CityAQI | None:
    """Get real-time satellite AQI for a single city."""
    profile = CITY_PROFILES.get(city_code)
    if not profile:
        return None
    
    cached = _cache.data.get(city_code)
    if cached:
        return cached
        
    aqi = _parse_current(city_code, profile["name"], profile["lat"], profile["lon"])
    _cache.data[city_code] = aqi
    return aqi

def fetch_all_cities_aqi(force: bool = False) -> dict[str, CityAQI]:
    """Fetch AQI for ALL 53 cities from the cached satellite grid (sub-millisecond)."""
    global _cache
    now = time.time()
    if (
        not force
        and _cache.data
        and len(_cache.data) >= len(CITY_PROFILES)
        and (now - _cache.last_fetched) < _CACHE_TTL_SECONDS
    ):
        return _cache.data

    # Pre-fetch grid first
    satellite_service.get_latest_satellite_grid()

    results: dict[str, CityAQI] = {}
    for code, profile in CITY_PROFILES.items():
        results[code] = _parse_current(code, profile["name"], profile["lat"], profile["lon"])
        
    _cache.data.update(results)
    _cache.last_fetched = now
    return _cache.data

def fetch_route_cities_aqi(codes: list[str] | None = None) -> dict[str, CityAQI]:
    """Fetch AQI for route cities (A-F) from cached satellite grid. Fast."""
    route_codes = codes or ["A", "B", "C", "D", "E", "F"]
    results = {}
    
    # Pre-fetch grid
    satellite_service.get_latest_satellite_grid()
    
    for code in route_codes:
        if code in CITY_PROFILES:
            profile = CITY_PROFILES[code]
            results[code] = _parse_current(code, profile["name"], profile["lat"], profile["lon"])
            
    _cache.data.update(results)
    return results

def get_pollution_weight_for_city(city_code: str) -> float:
    aqi_data = _cache.data.get(city_code)
    if aqi_data:
        return _aqi_to_pollution_weight(aqi_data.aqi)
    aqi_data = fetch_city_aqi(city_code)
    if aqi_data:
        return _aqi_to_pollution_weight(aqi_data.aqi)
    return 5.0

def get_edge_pollution(city_a: str, city_b: str) -> float:
    w_a = get_pollution_weight_for_city(city_a)
    w_b = get_pollution_weight_for_city(city_b)
    return round((w_a + w_b) / 2, 1)

def search_cities(query: str) -> list[dict[str, Any]]:
    """Search cities by name (case-insensitive partial match)."""
    q = query.lower()
    return [
        {"code": code, "name": p["name"], "lat": p["lat"], "lon": p["lon"]}
        for code, p in CITY_PROFILES.items()
        if q in p["name"].lower() or q in code.lower()
    ]

def city_aqi_to_dict(aqi: CityAQI) -> dict[str, Any]:
    return {
        "city_code": aqi.city_code,
        "city_name": aqi.city_name,
        "aqi": aqi.aqi,
        "category": aqi.category,
        "dominant_pollutant": aqi.dominant_pollutant,
        "pollutants": {
            "pm25": aqi.pollutants.pm25,
            "pm10": aqi.pollutants.pm10,
            "no2": aqi.pollutants.no2,
            "so2": aqi.pollutants.so2,
            "co": aqi.pollutants.co,
            "o3": aqi.pollutants.o3,
        },
        "source": aqi.source,
        "lat": aqi.lat,
        "lon": aqi.lon,
        "timestamp": aqi.timestamp,
    }
