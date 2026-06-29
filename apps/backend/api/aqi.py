"""AQI API endpoints — real-time air quality data for 50+ cities."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from apps.backend.services.aqi_service import (
    CITY_PROFILES,
    city_aqi_to_dict,
    fetch_all_cities_aqi,
    fetch_aqi_by_coords,
    fetch_city_aqi,
    search_cities,
)

router = APIRouter(tags=["Air Quality"])


@router.get("/aqi")
def get_all_aqi(
    region: str | None = Query(
        None, description="Filter: north, south, east, west, central, metro"
    ),
):
    """Get real-time AQI for all 50+ configured Indian cities."""
    all_data = fetch_all_cities_aqi()
    if not all_data:
        raise HTTPException(status_code=503, detail="Unable to fetch AQI data. Try again later.")

    cities = [city_aqi_to_dict(aqi) for aqi in all_data.values()]

    # Optional region filter
    if region:
        region_map = {
            "north": [
                "A",
                "B",
                "C",
                "D",
                "E",
                "CHD",
                "AMR",
                "LDH",
                "DHR",
                "SML",
                "KNP",
                "ALD",
                "MRT",
                "NDA",
                "GZB",
                "FBD",
                "GGN",
                "GWL",
                "JAM",
                "SRN",
            ],
            "south": ["CHN", "BLR", "HYD", "COK", "TRV", "MYS", "VIZ", "MDR", "CBE", "TRC", "VJW"],
            "east": ["F", "PAT", "GYA", "RAN", "BBS", "GUW", "IMP", "SHL"],
            "west": ["MUM", "PNE", "AMD", "SRT", "UDR", "JDH", "GOA", "RAJ", "VDR"],
            "central": ["BPL", "IND", "JBP", "NGP", "RPR"],
            "metro": ["A", "MUM", "BLR", "CHN", "HYD", "F", "PNE", "AMD"],
        }
        allowed = set(region_map.get(region.lower(), []))
        if allowed:
            cities = [c for c in cities if c["city_code"] in allowed]

    return {"cities": cities, "count": len(cities), "total_configured": len(CITY_PROFILES)}


@router.get("/aqi/search")
def search_aqi_cities(q: str = Query(..., description="Search query (city name or code)")):
    """Search available cities by name or code."""
    results = search_cities(q)
    if not results:
        return {"results": [], "count": 0, "query": q}
    return {"results": results, "count": len(results), "query": q}


@router.get("/aqi/coords")
def get_aqi_by_coordinates(
    lat: float = Query(..., description="Latitude"),
    lon: float = Query(..., description="Longitude"),
    name: str = Query("Custom Location", description="Optional location name"),
):
    """Get real-time AQI for ANY latitude/longitude on earth."""
    aqi_data = fetch_aqi_by_coords(lat, lon, name)
    if not aqi_data:
        raise HTTPException(status_code=503, detail="Unable to fetch AQI for these coordinates.")
    return city_aqi_to_dict(aqi_data)


@router.get("/aqi/{city_code}")
def get_city_aqi(city_code: str):
    """Get real-time AQI for a specific city by code."""
    city_code = city_code.strip().upper()
    if city_code not in CITY_PROFILES:
        raise HTTPException(
            status_code=404,
            detail=f"City '{city_code}' not found. Use /api/v1/aqi/search?q=<name> to find cities.",
        )
    aqi_data = fetch_city_aqi(city_code)
    if not aqi_data:
        raise HTTPException(status_code=503, detail=f"Unable to fetch AQI for {city_code}.")
    return city_aqi_to_dict(aqi_data)


@router.get("/aqi-cities")
def get_configured_cities(
    region: str | None = Query(None, description="Filter by region"),
):
    """List all 50+ configured cities."""
    cities = [
        {"code": code, "name": p["name"], "lat": p["lat"], "lon": p["lon"]}
        for code, p in CITY_PROFILES.items()
    ]
    return {"cities": cities, "count": len(cities)}
