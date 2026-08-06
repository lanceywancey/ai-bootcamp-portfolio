from __future__ import annotations

from dataclasses import dataclass
import heapq
from math import inf
from typing import Dict, Iterable, List

from src.map_loader import Edge, Node


class PathfindingError(ValueError):
    """Base class for pathfinding errors."""


class InvalidNodeError(PathfindingError):
    """Raised when a start or end node does not exist."""


class NoPathError(PathfindingError):
    """Raised when the destination cannot be reached."""


@dataclass(frozen=True)
class PathResult:
    path: List[int]
    total_distance: float


def shortest_path(
    nodes: Dict[int, Node],
    edges: Iterable[Edge],
    start_id: int,
    end_id: int,
) -> PathResult:
    if start_id not in nodes:
        raise InvalidNodeError(f"Invalid start node ID: {start_id}")
    if end_id not in nodes:
        raise InvalidNodeError(f"Invalid end node ID: {end_id}")
    if start_id == end_id:
        return PathResult([start_id], 0.0)

    adjacency: Dict[int, list[tuple[int, float]]] = {
        node_id: [] for node_id in nodes
    }
    for edge in edges:
        adjacency[edge.node_a].append((edge.node_b, edge.distance))
        adjacency[edge.node_b].append((edge.node_a, edge.distance))

    # Sorting makes equal-cost results deterministic.
    for neighbours in adjacency.values():
        neighbours.sort(key=lambda item: item[0])

    distances = {node_id: inf for node_id in nodes}
    previous: Dict[int, int] = {}
    distances[start_id] = 0.0
    queue: list[tuple[float, int]] = [(0.0, start_id)]

    while queue:
        current_distance, current = heapq.heappop(queue)

        if current_distance != distances[current]:
            continue
        if current == end_id:
            break

        for neighbour, edge_distance in adjacency[current]:
            candidate = current_distance + edge_distance
            if candidate < distances[neighbour]:
                distances[neighbour] = candidate
                previous[neighbour] = current
                heapq.heappush(queue, (candidate, neighbour))

    if distances[end_id] == inf:
        raise NoPathError(
            f"No path exists between node {start_id} and node {end_id}"
        )

    path = [end_id]
    while path[-1] != start_id:
        path.append(previous[path[-1]])
    path.reverse()

    return PathResult(path, distances[end_id])
