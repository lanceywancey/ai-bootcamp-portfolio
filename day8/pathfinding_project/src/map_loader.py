from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, Tuple


class MapDataError(ValueError):
    """Raised when a map data file is invalid."""


@dataclass(frozen=True)
class Node:
    node_id: int
    x: float
    y: float
    type_id: int
    name: str


@dataclass(frozen=True)
class Edge:
    edge_id: int
    node_a: int
    node_b: int
    distance: float


def _data_lines(path: Path) -> Iterable[Tuple[int, str]]:
    if not path.exists():
        raise MapDataError(f"Map file not found: {path}")

    for line_number, raw_line in enumerate(
        path.read_text(encoding="utf-8").splitlines(),
        start=1,
    ):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        yield line_number, line


def load_nodes(path: str | Path) -> Dict[int, Node]:
    file_path = Path(path)
    nodes: Dict[int, Node] = {}

    for line_number, line in _data_lines(file_path):
        parts = line.split(maxsplit=4)
        if len(parts) != 5:
            raise MapDataError(
                f"{file_path.name}:{line_number}: expected "
                "'NodeID X Y TypeID Name'"
            )

        try:
            node_id = int(parts[0])
            x = float(parts[1])
            y = float(parts[2])
            type_id = int(parts[3])
        except ValueError as exc:
            raise MapDataError(
                f"{file_path.name}:{line_number}: invalid numeric value"
            ) from exc

        name = parts[4].strip()
        if not name:
            raise MapDataError(
                f"{file_path.name}:{line_number}: node name cannot be empty"
            )
        if node_id in nodes:
            raise MapDataError(
                f"{file_path.name}:{line_number}: duplicate node ID {node_id}"
            )
        if type_id not in {0, 1, 2, 3, 4}:
            raise MapDataError(
                f"{file_path.name}:{line_number}: TypeID must be from 0 to 4"
            )

        nodes[node_id] = Node(node_id, x, y, type_id, name)

    if not nodes:
        raise MapDataError(f"{file_path.name}: no nodes found")

    return nodes


def load_edges(
    path: str | Path,
    nodes: Dict[int, Node],
) -> Dict[int, Edge]:
    file_path = Path(path)
    edges: Dict[int, Edge] = {}

    for line_number, line in _data_lines(file_path):
        parts = line.split()
        if len(parts) != 4:
            raise MapDataError(
                f"{file_path.name}:{line_number}: expected "
                "'EdgeID NodeA NodeB Distance'"
            )

        try:
            edge_id = int(parts[0])
            node_a = int(parts[1])
            node_b = int(parts[2])
            distance = float(parts[3])
        except ValueError as exc:
            raise MapDataError(
                f"{file_path.name}:{line_number}: invalid numeric value"
            ) from exc

        if edge_id in edges:
            raise MapDataError(
                f"{file_path.name}:{line_number}: duplicate edge ID {edge_id}"
            )
        if node_a not in nodes or node_b not in nodes:
            raise MapDataError(
                f"{file_path.name}:{line_number}: edge {edge_id} references "
                "an unknown node"
            )
        if distance < 0:
            raise MapDataError(
                f"{file_path.name}:{line_number}: distance cannot be negative"
            )

        edges[edge_id] = Edge(edge_id, node_a, node_b, distance)

    return edges


def load_map(
    node_path: str | Path,
    edge_path: str | Path,
) -> tuple[Dict[int, Node], Dict[int, Edge]]:
    nodes = load_nodes(node_path)
    edges = load_edges(edge_path, nodes)
    return nodes, edges


def _format_number(value: float) -> str:
    return str(int(value)) if value.is_integer() else str(value)


def save_nodes(path: str | Path, nodes: Dict[int, Node]) -> None:
    output = ["# NodeID X Y TypeID Name"]
    for node_id in sorted(nodes):
        node = nodes[node_id]
        output.append(
            f"{node.node_id} {_format_number(node.x)} "
            f"{_format_number(node.y)} {node.type_id} {node.name}"
        )
    Path(path).write_text("\n".join(output) + "\n", encoding="utf-8")


def save_edges(path: str | Path, edges: Dict[int, Edge]) -> None:
    output = ["# EdgeID NodeA NodeB Distance"]
    for edge_id in sorted(edges):
        edge = edges[edge_id]
        output.append(
            f"{edge.edge_id} {edge.node_a} {edge.node_b} "
            f"{_format_number(edge.distance)}"
        )
    Path(path).write_text("\n".join(output) + "\n", encoding="utf-8")
