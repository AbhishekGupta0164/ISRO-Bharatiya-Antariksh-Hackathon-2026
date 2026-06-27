"""Exposure calculation primitives."""

from __future__ import annotations


def compute_exposure(distance: float, pollution: float) -> float:
    return distance * pollution
