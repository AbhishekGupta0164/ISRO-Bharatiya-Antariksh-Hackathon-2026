from __future__ import annotations


def grade_exposure(total_exposure: float) -> str:
    if total_exposure < 20:
        return "excellent"
    if total_exposure < 50:
        return "good"
    if total_exposure < 100:
        return "moderate"
    return "poor"
