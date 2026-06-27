from __future__ import annotations


def greedy_policy(scores: dict[str, float]) -> str:
    if not scores:
        raise ValueError("No scores available")
    return min(scores, key=scores.get)
