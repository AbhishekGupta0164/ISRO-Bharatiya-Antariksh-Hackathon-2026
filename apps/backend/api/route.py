from fastapi import APIRouter, HTTPException

from apps.backend.schemas.route_schema import RouteRequest, RouteResponse
from apps.backend.services.route_service import get_route_service

router = APIRouter()


@router.post("/eco-route", response_model=RouteResponse)
def eco_route(req: RouteRequest):

    result = get_route_service(req.start, req.end, req.traffic_multiplier, req.route_type)

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    return result
