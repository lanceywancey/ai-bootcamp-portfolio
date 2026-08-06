import pytest

from src.map_loader import Edge, Node, load_map
from src.pathfinder import InvalidNodeError, NoPathError, shortest_path


def test_normal_shortest_path(map_files):
    nodes, edges = load_map(*map_files)
    result = shortest_path(nodes, edges.values(), 0, 2)

    assert result.path == [0, 1, 2]
    assert result.total_distance == 300


def test_start_equals_end(map_files):
    nodes, edges = load_map(*map_files)
    result = shortest_path(nodes, edges.values(), 2, 2)

    assert result.path == [2]
    assert result.total_distance == 0


def test_invalid_start_node(map_files):
    nodes, edges = load_map(*map_files)

    with pytest.raises(InvalidNodeError, match="Invalid start"):
        shortest_path(nodes, edges.values(), 99, 2)


def test_invalid_end_node(map_files):
    nodes, edges = load_map(*map_files)

    with pytest.raises(InvalidNodeError, match="Invalid end"):
        shortest_path(nodes, edges.values(), 0, 99)


def test_disconnected_destination(map_files):
    nodes, edges = load_map(*map_files)

    with pytest.raises(NoPathError, match="No path exists"):
        shortest_path(nodes, edges.values(), 0, 5)


def test_multiple_equal_shortest_paths_are_handled():
    nodes = {
        0: Node(0, 0, 0, 0, "A"),
        1: Node(1, 1, 1, 1, "B"),
        2: Node(2, 1, -1, 1, "C"),
        3: Node(3, 2, 0, 2, "D"),
    }
    edges = [
        Edge(0, 0, 1, 1),
        Edge(1, 1, 3, 1),
        Edge(2, 0, 2, 1),
        Edge(3, 2, 3, 1),
    ]

    result = shortest_path(nodes, edges, 0, 3)

    assert result.path in ([0, 1, 3], [0, 2, 3])
    assert result.total_distance == 2
