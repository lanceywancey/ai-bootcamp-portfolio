from pathlib import Path

import pytest

from app import create_app


NODE_DATA = """\
# NodeID X Y TypeID Name
0 10 10 0 School_A
1 25 12 1 Shop_A
2 40 20 2 Mall_A
3 55 30 3 HDB_A
4 70 25 4 Park_A
5 82 45 1 Isolated_Shop
"""

EDGE_DATA = """\
# EdgeID NodeA NodeB Distance
0 0 1 120
1 1 2 180
2 0 3 250
3 3 4 160
4 4 2 100
5 1 3 140
"""


@pytest.fixture
def map_files(tmp_path: Path):
    node_file = tmp_path / "Node_Info.txt"
    edge_file = tmp_path / "Graph_Path.txt"
    node_file.write_text(NODE_DATA, encoding="utf-8")
    edge_file.write_text(EDGE_DATA, encoding="utf-8")
    return node_file, edge_file


@pytest.fixture
def app(map_files):
    node_file, edge_file = map_files
    application = create_app(node_file, edge_file, testing=True)
    application.config.update(
        EDITOR_PASSWORD="test-password",
        SECRET_KEY="test-secret",
    )
    return application


@pytest.fixture
def client(app):
    return app.test_client()
