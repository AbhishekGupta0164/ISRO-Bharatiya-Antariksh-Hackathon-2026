from fastapi import APIRouter, HTTPException

from apps.backend.schemas.graph_schema import CityIn, RoadIn, RoadRemoveIn
from apps.backend.services import graph_store

router = APIRouter()


@router.get("/graph")
def get_graph():
    """Return the full city/road graph."""
    return graph_store.get_graph()


@router.get("/cities")
def list_cities():
    """List all city nodes with their metadata."""
    return graph_store.get_cities()


@router.get("/roads")
def list_roads():
    """List all roads (edges) in the graph."""
    return graph_store.get_roads()


@router.post("/cities")
def add_city(body: CityIn):
    """Add a new city node to the graph."""
    try:
        cities = graph_store.add_city(body.node_id, body.name, body.lat, body.lng)
        return {"status": "success", "message": f"City '{body.name}' added as node {body.node_id.upper()}", "cities": cities}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/cities/{node_id}")
def remove_city(node_id: str):
    """Remove a city and all its connected roads."""
    try:
        cities = graph_store.remove_city(node_id)
        return {"status": "success", "message": f"City '{node_id.upper()}' removed", "cities": cities}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/roads")
def add_road(body: RoadIn):
    """Add a road between two existing cities."""
    try:
        roads = graph_store.add_road(body.from_id, body.to_id, body.distance, body.pollution)
        return {"status": "success", "message": f"Road {body.from_id.upper()} ↔ {body.to_id.upper()} added", "roads": roads}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/roads")
def remove_road(body: RoadRemoveIn):
    """Remove a road between two cities."""
    try:
        roads = graph_store.remove_road(body.from_id, body.to_id)
        return {"status": "success", "message": f"Road {body.from_id.upper()} ↔ {body.to_id.upper()} removed", "roads": roads}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/smart-add")
def smart_add_city(body: dict):
    """
    Smart city addition — just provide a city name.
    Automatically geocodes, assigns node ID, and connects to nearest cities.
    Body: {"city_name": "Mumbai"}
    """
    city_name = body.get("city_name", "").strip()
    if not city_name:
        raise HTTPException(status_code=400, detail="city_name is required")
    try:
        result = graph_store.smart_add_city(city_name)
        return {"status": "success", "message": f"✅ '{city_name}' added as node {result['node_id']}", **result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/graph/reset")
def reset_graph():
    """Reset the graph to the default 6-city network."""
    data = graph_store.reset_graph()
    return {"status": "success", "message": "Graph reset to defaults", **data}

