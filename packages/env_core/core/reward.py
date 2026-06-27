from __future__ import annotations


def calculate_reward(distance: float, pollution: float, reached_destination: bool = False) -> float:
    reward = -(pollution * 0.7 + distance * 0.3)
    reward += 0.5 * max(0.0, 10.0 - pollution)
    if reached_destination:
        reward += 100.0
    return reward
