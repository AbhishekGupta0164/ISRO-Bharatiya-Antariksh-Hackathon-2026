"""Exposure Credit API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from apps.backend.services.exposure_credit import (
    GRADE_TABLE,
    apply_route_credits,
    calculate_route_credits,
    get_leaderboard,
    get_or_create_wallet,
    grade_city,
    route_credits_to_dict,
    wallet_to_dict,
)

router = APIRouter(tags=["Exposure Credits"])


@router.get("/credits/grade-table")
def get_grade_table():
    """Get the AQI → Grade → Credit mapping table."""
    return {
        "grades": [
            {
                "grade": g["grade"],
                "max_aqi": g["max_aqi"],
                "label": g["label"],
                "emoji": g["emoji"],
                "credits_per_segment": g["credits"],
                "color": g["color"],
            }
            for g in GRADE_TABLE
        ]
    }


@router.get("/credits/wallet/{user_id}")
def get_wallet(user_id: str):
    """Get or create a user's exposure credit wallet."""
    wallet = get_or_create_wallet(user_id)
    return wallet_to_dict(wallet)


@router.post("/credits/calculate")
def calculate_credits(
    route: list[str],
    is_eco: bool = Query(False, description="Is this the eco route?"),
):
    """Preview credit impact for a route without applying it."""
    if len(route) < 2:
        raise HTTPException(status_code=400, detail="Route must have at least 2 cities")
    rc = calculate_route_credits(route, is_eco_route=is_eco)
    return route_credits_to_dict(rc)


@router.post("/credits/apply/{user_id}")
def apply_credits(
    user_id: str,
    route: list[str],
    is_eco: bool = Query(False, description="Was this the eco route?"),
    shortest_route: list[str] | None = None,
):
    """Apply route credits to a user's wallet."""
    if len(route) < 2:
        raise HTTPException(status_code=400, detail="Route must have at least 2 cities")
    rc = calculate_route_credits(route, is_eco_route=is_eco, shortest_route=shortest_route)
    wallet = apply_route_credits(user_id, rc)
    return {
        "credits": route_credits_to_dict(rc),
        "wallet": wallet_to_dict(wallet),
    }


@router.get("/credits/city-grade/{city_code}")
def get_city_grade(city_code: str):
    """Get exposure grade for a specific city."""
    city_code = city_code.strip().upper()
    cg = grade_city(city_code)
    if not cg:
        raise HTTPException(
            status_code=404, detail=f"City {city_code} not found or AQI unavailable"
        )
    return {
        "city_code": cg.city_code,
        "city_name": cg.city_name,
        "aqi": cg.aqi,
        "grade": cg.grade,
        "grade_label": cg.grade_label,
        "emoji": cg.emoji,
        "credit_delta": cg.credit_delta,
        "color": cg.color,
    }


@router.get("/credits/leaderboard")
def leaderboard():
    """Get top users by exposure credits."""
    return {"leaderboard": get_leaderboard()}
