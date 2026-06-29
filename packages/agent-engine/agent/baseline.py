from __future__ import annotations


def choose_lowest_pollution(neighbors: list[tuple[str, float, float]]) -> str:
    if not neighbors:
        raise ValueError("No neighbors available")
    return min(neighbors, key=lambda item: item[2])[0]
