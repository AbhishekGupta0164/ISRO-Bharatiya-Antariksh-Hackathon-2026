"""Shared helper utilities for metrics and formatting."""

from __future__ import annotations


def percent_improvement(baseline: float, candidate: float) -> str:
    if baseline <= 0:
        return "N/A"
    improvement = ((baseline - candidate) / baseline) * 100
    return f"{improvement:.2f}% less pollution"
