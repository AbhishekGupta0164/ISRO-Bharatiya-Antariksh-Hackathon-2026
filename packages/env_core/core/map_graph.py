from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Edge:
    target: str
    distance: float
    pollution: float


class MapGraph:
    def __init__(self) -> None:
        self._graph: dict[str, list[Edge]] = {}

    def add_city(self, city: str) -> None:
        self._graph.setdefault(city, [])

    def add_road(self, city1: str, city2: str, distance: float, pollution: float) -> None:
        self.add_city(city1)
        self.add_city(city2)
        self._graph[city1].append(Edge(city2, distance, pollution))
        self._graph[city2].append(Edge(city1, distance, pollution))

    def get_neighbors(self, city: str) -> list[tuple[str, float, float]]:
        return [(e.target, e.distance, e.pollution) for e in self._graph.get(city, [])]
