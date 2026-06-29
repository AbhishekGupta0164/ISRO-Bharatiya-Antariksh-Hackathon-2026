"""Score route candidates by exposure and distance."""

from __future__ import annotations


def score_route(distance: float, exposure: float, alpha: float = 0.5) -> float:
    return alpha * distance + (1 - alpha) * exposure
