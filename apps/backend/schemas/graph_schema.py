from typing import Any, Dict, List

from pydantic import BaseModel, Field


class CityIn(BaseModel):
    node_id: str = Field(..., description="Unique uppercase letter ID, e.g. 'G'")
    name: str = Field(..., description="Human-readable city name, e.g. 'Mumbai'")
    lat: float = Field(..., description="Latitude")
    lng: float = Field(..., description="Longitude")


class RoadIn(BaseModel):
    from_id: str = Field(..., alias="from", description="Source city node ID")
    to_id: str = Field(..., alias="to", description="Destination city node ID")
    distance: float = Field(..., gt=0, description="Distance in km")
    pollution: float = Field(..., ge=0, description="AQI / pollution index")

    class Config:
        populate_by_name = True


class RoadRemoveIn(BaseModel):
    from_id: str = Field(..., alias="from", description="Source city node ID")
    to_id: str = Field(..., alias="to", description="Destination city node ID")

    class Config:
        populate_by_name = True


class CityOut(BaseModel):
    name: str
    lat: float
    lng: float


class GraphOut(BaseModel):
    cities: Dict[str, CityOut]
    roads: List[Dict[str, Any]]
