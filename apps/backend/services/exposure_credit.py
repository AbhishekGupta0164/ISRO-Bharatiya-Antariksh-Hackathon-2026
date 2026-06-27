"""Exposure Credit Engine — gamified health currency.

Credits are earned/lost based on real-time AQI of cities traversed.
Green routes earn credits, polluted routes cost credits.

Grade System:
  A (🟢 AQI ≤ 50)   → +10 credits/segment  "Pristine Air"
  B (🟡 AQI 51-100)  → +5  credits/segment  "Acceptable"
  C (🟠 AQI 101-150) → +0  credits/segment  "Moderate Risk"
  D (🔴 AQI 151-200) → -5  credits/segment  "High Risk"
  E (🟣 AQI 201-300) → -15 credits/segment  "Dangerous"
  F (⚫ AQI 300+)    → -25 credits/segment  "Hazardous"
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import asdict, dataclass, field
from typing import Any

from apps.backend.services.aqi_service import (
    _cache,
    fetch_city_aqi,
)

# ---------------------------------------------------------------------------
# Credit config
# ---------------------------------------------------------------------------

DEFAULT_STARTING_CREDITS = 100
MAX_CREDITS = 1000
MIN_CREDITS = 0

GRADE_TABLE = [
    {
        "max_aqi": 50,
        "grade": "A",
        "label": "Pristine Air",
        "emoji": "🟢",
        "credits": +15,  # Increased from +10
        "color": "#4CAF50",
    },
    {
        "max_aqi": 100,
        "grade": "B",
        "label": "Acceptable",
        "emoji": "🟡",
        "credits": +8,   # Increased from +5
        "color": "#FFC107",
    },
    {
        "max_aqi": 150,
        "grade": "C",
        "label": "Moderate Risk",
        "emoji": "🟠",
        "credits": 0,    # Corrected from -5 (as per docstring)
        "color": "#FF9800",
    },
    {
        "max_aqi": 200,
        "grade": "D",
        "label": "High Risk",
        "emoji": "🔴",
        "credits": -25,  # Increased from -15
        "color": "#F44336",
    },
    {
        "max_aqi": 300,
        "grade": "E",
        "label": "Dangerous",
        "emoji": "🟣",
        "credits": -50,  # Increased from -30
        "color": "#9C27B0",
    },
    {
        "max_aqi": 999,
        "grade": "F",
        "label": "Hazardous",
        "emoji": "⚫",
        "credits": -100, # Increased from -50
        "color": "#7E0023",
    },
]

# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class CityGrade:
    city_code: str
    city_name: str
    aqi: int
    grade: str
    grade_label: str
    emoji: str
    credit_delta: int
    color: str


@dataclass
class SegmentCredit:
    from_city: str
    to_city: str
    from_aqi: int
    to_aqi: int
    avg_aqi: int
    grade: str
    emoji: str
    credit_delta: int
    distance: float


@dataclass
class RouteCredits:
    route: list[str]
    segments: list[SegmentCredit]
    total_credit_change: int
    grade_summary: str
    overall_grade: str
    overall_emoji: str
    city_grades: list[CityGrade]
    eco_bonus: int  # bonus for choosing eco route over shortest
    final_credit_change: int  # total + eco_bonus


@dataclass
class UserWallet:
    user_id: str
    credits: int = DEFAULT_STARTING_CREDITS
    total_earned: int = 0
    total_lost: int = 0
    trips_taken: int = 0
    green_trips: int = 0
    history: list[dict] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)


# ---------------------------------------------------------------------------
# In-memory wallet store (persists to JSON file)
# ---------------------------------------------------------------------------

_WALLETS_PATH = os.path.join(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")),
    "data",
    "wallets.json",
)

_wallets: dict[str, UserWallet] = {}


def _load_wallets():
    global _wallets
    if os.path.exists(_WALLETS_PATH):
        try:
            with open(_WALLETS_PATH, "r") as f:
                raw = json.load(f)
            for uid, data in raw.items():
                _wallets[uid] = UserWallet(**data)
        except Exception:
            _wallets = {}


def _save_wallets():
    os.makedirs(os.path.dirname(_WALLETS_PATH), exist_ok=True)
    with open(_WALLETS_PATH, "w") as f:
        json.dump({uid: asdict(w) for uid, w in _wallets.items()}, f, indent=2)


_load_wallets()


# ---------------------------------------------------------------------------
# Grading helpers
# ---------------------------------------------------------------------------


def get_grade_for_aqi(aqi: int) -> dict:
    """Get grade info for a given AQI value."""
    for g in GRADE_TABLE:
        if aqi <= g["max_aqi"]:
            return g
    return GRADE_TABLE[-1]


def grade_city(city_code: str) -> CityGrade | None:
    """Grade a city based on its current AQI."""
    aqi_data = _cache.data.get(city_code) or fetch_city_aqi(city_code)
    if not aqi_data:
        return None
    g = get_grade_for_aqi(aqi_data.aqi)
    return CityGrade(
        city_code=city_code,
        city_name=aqi_data.city_name,
        aqi=aqi_data.aqi,
        grade=g["grade"],
        grade_label=g["label"],
        emoji=g["emoji"],
        credit_delta=g["credits"],
        color=g["color"],
    )


def grade_segment(from_code: str, to_code: str, distance: float = 0) -> SegmentCredit:
    """Calculate credit delta for a route segment between two cities."""
    aqi_from = _cache.data.get(from_code)
    aqi_to = _cache.data.get(to_code)

    from_aqi = aqi_from.aqi if aqi_from else 100
    to_aqi = aqi_to.aqi if aqi_to else 100
    avg_aqi = max(from_aqi, to_aqi) # Maximize exposure risk instead of averaging


    g = get_grade_for_aqi(avg_aqi)

    return SegmentCredit(
        from_city=from_code,
        to_city=to_code,
        from_aqi=from_aqi,
        to_aqi=to_aqi,
        avg_aqi=avg_aqi,
        grade=g["grade"],
        emoji=g["emoji"],
        credit_delta=g["credits"],
        distance=distance,
    )


# ---------------------------------------------------------------------------
# Route credit calculation
# ---------------------------------------------------------------------------


def calculate_route_credits(
    route: list[str],
    distances: dict[tuple[str, str], float] | None = None,
    is_eco_route: bool = False,
    shortest_route: list[str] | None = None,
) -> RouteCredits:
    """Calculate total exposure credits for a route based on real-time AQI."""
    segments: list[SegmentCredit] = []
    city_grades: list[CityGrade] = []

    # Grade each city
    for code in route:
        cg = grade_city(code)
        if cg:
            city_grades.append(cg)

    # Grade each segment
    for i in range(len(route) - 1):
        dist = 0.0
        if distances:
            key = (route[i], route[i + 1])
            rev_key = (route[i + 1], route[i])
            dist = distances.get(key, distances.get(rev_key, 0.0))

        seg = grade_segment(route[i], route[i + 1], dist)
        segments.append(seg)

    total_change = sum(s.credit_delta for s in segments)

    # Eco bonus / Shortest path penalty
    eco_bonus = 0
    if is_eco_route and shortest_route and route != shortest_route:
        # Calculate what the shortest route would have cost
        shortest_segments = []
        for i in range(len(shortest_route) - 1):
            seg = grade_segment(shortest_route[i], shortest_route[i + 1])
            shortest_segments.append(seg)
        shortest_change = sum(s.credit_delta for s in shortest_segments)

        # Significant Reward for choosing the healthier route
        improvement = total_change - shortest_change
        eco_bonus = max(0, improvement) + 20  # +20 flat bonus for being eco-conscious
    
    elif not is_eco_route and shortest_route and route == shortest_route:
        # Penalty for choosing the polluting shortest path instead of a healthier alternative
        if total_change < 0:
            eco_bonus = -30  # "Shortest Path Penalty" to encourage exploring eco routes

    final_change = total_change + eco_bonus

    # Determine overall grade
    if segments:
        avg_segment_aqi = sum(s.avg_aqi for s in segments) // len(segments)
    else:
        avg_segment_aqi = 0
    overall_g = get_grade_for_aqi(avg_segment_aqi)

    # Build summary
    positive = sum(1 for s in segments if s.credit_delta > 0)
    negative = sum(1 for s in segments if s.credit_delta < 0)
    neutral = sum(1 for s in segments if s.credit_delta == 0)

    if final_change > 0:
        summary = f"🎉 You earned {final_change} credits! ({positive} clean, {neutral} moderate, {negative} polluted segments)"
    elif final_change < 0:
        summary = f"⚠️ You lost {abs(final_change)} credits. ({negative} polluted, {neutral} moderate, {positive} clean segments)"
    else:
        summary = f"➡️ No credit change. ({neutral} moderate segments)"

    return RouteCredits(
        route=route,
        segments=segments,
        total_credit_change=total_change,
        grade_summary=summary,
        overall_grade=overall_g["grade"],
        overall_emoji=overall_g["emoji"],
        city_grades=city_grades,
        eco_bonus=eco_bonus,
        final_credit_change=final_change,
    )


# ---------------------------------------------------------------------------
# Wallet management
# ---------------------------------------------------------------------------


def get_or_create_wallet(user_id: str) -> UserWallet:
    if user_id not in _wallets:
        _wallets[user_id] = UserWallet(user_id=user_id)
        _save_wallets()
    return _wallets[user_id]


def apply_route_credits(user_id: str, route_credits: RouteCredits) -> UserWallet:
    """Apply route credit changes to user wallet."""
    wallet = get_or_create_wallet(user_id)

    delta = route_credits.final_credit_change
    old_balance = wallet.credits
    wallet.credits = max(MIN_CREDITS, min(MAX_CREDITS, wallet.credits + delta))

    if delta > 0:
        wallet.total_earned += delta
    elif delta < 0:
        wallet.total_lost += abs(delta)

    wallet.trips_taken += 1
    if route_credits.overall_grade in ("A", "B"):
        wallet.green_trips += 1

    wallet.history.insert(
        0,
        {
            "route": route_credits.route,
            "credit_change": delta,
            "eco_bonus": route_credits.eco_bonus,
            "grade": route_credits.overall_grade,
            "old_balance": old_balance,
            "new_balance": wallet.credits,
            "timestamp": time.time(),
        },
    )
    wallet.history = wallet.history[:20]  # keep last 20
    wallet.updated_at = time.time()

    _save_wallets()
    return wallet


def get_leaderboard() -> list[dict]:
    """Get top users by credits."""
    sorted_wallets = sorted(_wallets.values(), key=lambda w: w.credits, reverse=True)
    return [
        {
            "user_id": w.user_id,
            "credits": w.credits,
            "trips": w.trips_taken,
            "green_trips": w.green_trips,
            "green_ratio": round(w.green_trips / max(w.trips_taken, 1) * 100, 1),
        }
        for w in sorted_wallets[:10]
    ]


# ---------------------------------------------------------------------------
# Serialization
# ---------------------------------------------------------------------------


def route_credits_to_dict(rc: RouteCredits) -> dict[str, Any]:
    return {
        "route": rc.route,
        "segments": [
            {
                "from": s.from_city,
                "to": s.to_city,
                "from_aqi": s.from_aqi,
                "to_aqi": s.to_aqi,
                "avg_aqi": s.avg_aqi,
                "grade": s.grade,
                "emoji": s.emoji,
                "credit_delta": s.credit_delta,
                "distance": s.distance,
            }
            for s in rc.segments
        ],
        "city_grades": [
            {
                "city_code": cg.city_code,
                "city_name": cg.city_name,
                "aqi": cg.aqi,
                "grade": cg.grade,
                "grade_label": cg.grade_label,
                "emoji": cg.emoji,
                "credit_delta": cg.credit_delta,
                "color": cg.color,
            }
            for cg in rc.city_grades
        ],
        "total_credit_change": rc.total_credit_change,
        "eco_bonus": rc.eco_bonus,
        "final_credit_change": rc.final_credit_change,
        "overall_grade": rc.overall_grade,
        "overall_emoji": rc.overall_emoji,
        "grade_summary": rc.grade_summary,
    }


def wallet_to_dict(w: UserWallet) -> dict[str, Any]:
    level = "🌱 Seedling"
    if w.credits >= 500:
        level = "🌳 Eco Champion"
    elif w.credits >= 300:
        level = "🌿 Green Warrior"
    elif w.credits >= 200:
        level = "☘️ Eco Explorer"
    elif w.credits >= 100:
        level = "🍀 Green Starter"

    return {
        "user_id": w.user_id,
        "credits": w.credits,
        "level": level,
        "total_earned": w.total_earned,
        "total_lost": w.total_lost,
        "trips_taken": w.trips_taken,
        "green_trips": w.green_trips,
        "green_ratio": round(w.green_trips / max(w.trips_taken, 1) * 100, 1),
        "history": w.history[:10],
    }
