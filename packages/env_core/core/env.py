from __future__ import annotations

from dataclasses import dataclass

from packages.env_core.core.reward import calculate_reward


@dataclass
class StepResult:
    location: str
    reward: float
    done: bool
    total_exposure: float


class SimpleEnv:
    def __init__(self, graph, start: str, destination: str, max_steps: int = 50) -> None:
        self.graph = graph
        self.start = start
        self.destination = destination
        self.max_steps = max_steps
        self.reset()

    def reset(self) -> str:
        self.location = self.start
        self.total_exposure = 0.0
        self.steps = 0
        return self.location

    def step(self, action: str) -> StepResult:
        for node, distance, pollution in self.graph.get_neighbors(self.location):
            if node == action:
                self.location = node
                self.total_exposure += distance * pollution
                self.steps += 1
                done = node == self.destination or self.steps >= self.max_steps
                reward = calculate_reward(
                    distance,
                    pollution,
                    reached_destination=node == self.destination,
                )
                return StepResult(node, reward, done, self.total_exposure)
        raise ValueError(f"Invalid action: {action}")
