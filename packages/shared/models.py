"""Typed models used by shared utility flows."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RouteEdge:
    target: str
    distance: float
    pollution: float


@dataclass(frozen=True)
class RouteMetrics:
    total_distance: float
    total_pollution: float
    total_exposure: float
