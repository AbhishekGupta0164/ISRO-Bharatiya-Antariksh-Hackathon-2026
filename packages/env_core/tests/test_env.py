from __future__ import annotations

import random

from apps.simulator.evaluator import Graph
from packages.env_core.envs.pollution_env.env import PollutionEnv


def test_graph():
    g = Graph()
    g.add_road("A", "B", 5, 10)
    g.add_road("A", "C", 8, 3)

    assert len(g.get_neighbors("A")) == 2


def test_rl_env():
    random.seed(42)
    g = Graph()

    g.add_road("A", "B", 5, 10)
    g.add_road("A", "C", 8, 3)
    g.add_road("B", "D", 2, 2)
    g.add_road("C", "D", 4, 6)
    g.add_road("C", "E", 7, 1)
    g.add_road("D", "E", 1, 2)
    g.add_road("D", "F", 6, 8)
    g.add_road("E", "F", 3, 1)

    env = PollutionEnv(g, start="A", destination="F")
    state = env.reset()
    done = False
    info = {"total_exposure": 0.0}

    for _ in range(20):
        if done:
            break
        actions = env.get_possible_actions()
        action = random.choice(actions)
        next_state, _, done, info = env.step(action)
        state = next_state

    assert isinstance(state, str)
    assert info["total_exposure"] >= 0
