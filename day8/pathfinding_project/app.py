from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from flask import (
    Flask,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from src.auth import editor_required, is_editor_authenticated
from src.map_loader import (
    Edge,
    MapDataError,
    Node,
    load_map,
    save_edges,
    save_nodes,
)
from src.pathfinder import (
    InvalidNodeError,
    NoPathError,
    PathResult,
    shortest_path,
)


BASE_DIR = Path(__file__).resolve().parent


def _number_label(value: float) -> str:
    return str(int(value)) if value.is_integer() else f"{value:g}"


def _svg_model(
    nodes: dict[int, Node],
    edges: dict[int, Edge],
    highlighted_path: list[int] | None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    width = 900
    height = 520
    padding = 70

    x_values = [node.x for node in nodes.values()]
    y_values = [node.y for node in nodes.values()]
    min_x, max_x = min(x_values), max(x_values)
    min_y, max_y = min(y_values), max(y_values)

    x_range = max(max_x - min_x, 1)
    y_range = max(max_y - min_y, 1)

    positions: dict[int, tuple[float, float]] = {}
    svg_nodes: list[dict[str, Any]] = []

    for node in sorted(nodes.values(), key=lambda item: item.node_id):
        px = padding + ((node.x - min_x) / x_range) * (width - 2 * padding)
        py = height - padding - (
            ((node.y - min_y) / y_range) * (height - 2 * padding)
        )
        positions[node.node_id] = (px, py)
        svg_nodes.append(
            {
                "id": node.node_id,
                "x": round(px, 2),
                "y": round(py, 2),
                "type_id": node.type_id,
                "name": node.name.replace("_", " "),
            }
        )

    route_pairs: set[frozenset[int]] = set()
    if highlighted_path:
        route_pairs = {
            frozenset((highlighted_path[index], highlighted_path[index + 1]))
            for index in range(len(highlighted_path) - 1)
        }

    svg_edges: list[dict[str, Any]] = []
    for edge in sorted(edges.values(), key=lambda item: item.edge_id):
        x1, y1 = positions[edge.node_a]
        x2, y2 = positions[edge.node_b]
        svg_edges.append(
            {
                "id": edge.edge_id,
                "x1": round(x1, 2),
                "y1": round(y1, 2),
                "x2": round(x2, 2),
                "y2": round(y2, 2),
                "label_x": round((x1 + x2) / 2, 2),
                "label_y": round((y1 + y2) / 2 - 7, 2),
                "distance": _number_label(edge.distance),
                "highlighted": (
                    frozenset((edge.node_a, edge.node_b)) in route_pairs
                ),
            }
        )

    return svg_nodes, svg_edges


def create_app(
    node_file: str | Path | None = None,
    edge_file: str | Path | None = None,
    testing: bool = False,
) -> Flask:
    app = Flask(__name__)
    app.config.update(
        SECRET_KEY=os.getenv(
            "FLASK_SECRET_KEY",
            "development-secret-change-this",
        ),
        EDITOR_PASSWORD=os.getenv("EDITOR_PASSWORD", "bootcamp123"),
        NODE_FILE=str(node_file or BASE_DIR / "data" / "Node_Info.txt"),
        EDGE_FILE=str(edge_file or BASE_DIR / "data" / "Graph_Path.txt"),
        TESTING=testing,
    )

    def current_map():
        return load_map(
            app.config["NODE_FILE"],
            app.config["EDGE_FILE"],
        )

    @app.route("/", methods=["GET", "POST"])
    def index():
        nodes, edges = current_map()
        result: PathResult | None = None
        error_message: str | None = None
        selected_start: int | None = None
        selected_end: int | None = None

        if request.method == "POST":
            try:
                selected_start = int(request.form["start_id"])
                selected_end = int(request.form["end_id"])
                result = shortest_path(
                    nodes,
                    edges.values(),
                    selected_start,
                    selected_end,
                )
            except (KeyError, ValueError):
                error_message = "Start and end nodes must be valid integers."
            except (InvalidNodeError, NoPathError) as exc:
                error_message = str(exc)

        highlighted = result.path if result else None
        svg_nodes, svg_edges = _svg_model(nodes, edges, highlighted)

        return render_template(
            "index.html",
            nodes=sorted(nodes.values(), key=lambda node: node.node_id),
            result=result,
            error_message=error_message,
            selected_start=selected_start,
            selected_end=selected_end,
            svg_nodes=svg_nodes,
            svg_edges=svg_edges,
            is_editor=is_editor_authenticated(),
            distance_label=(
                _number_label(result.total_distance) if result else None
            ),
        )

    @app.route("/editor/login", methods=["GET", "POST"])
    def editor_login():
        if request.method == "POST":
            supplied_password = request.form.get("password", "")
            if supplied_password == app.config["EDITOR_PASSWORD"]:
                session["editor_authenticated"] = True
                flash("Editor login successful.", "success")
                return redirect(url_for("editor"))
            return render_template(
                "login.html",
                error_message="Incorrect editor password.",
            ), 401

        return render_template("login.html", error_message=None)

    @app.post("/editor/logout")
    def editor_logout():
        session.clear()
        flash("You have been logged out.", "success")
        return redirect(url_for("index"))

    @app.get("/editor")
    @editor_required
    def editor():
        nodes, edges = current_map()
        return render_template(
            "editor.html",
            nodes=sorted(nodes.values(), key=lambda node: node.node_id),
            edges=sorted(edges.values(), key=lambda edge: edge.edge_id),
        )

    @app.post("/editor/node/add")
    @editor_required
    def add_node():
        try:
            nodes, edges = current_map()
            node_id = int(request.form["node_id"])
            if node_id in nodes:
                raise ValueError(f"Node ID {node_id} already exists.")

            node = Node(
                node_id=node_id,
                x=float(request.form["x"]),
                y=float(request.form["y"]),
                type_id=int(request.form["type_id"]),
                name=request.form["name"].strip(),
            )
            if node.type_id not in {0, 1, 2, 3, 4}:
                raise ValueError("TypeID must be from 0 to 4.")
            if not node.name or any(character.isspace() for character in node.name):
                raise ValueError("Node name must be non-empty and contain no spaces.")

            nodes[node_id] = node
            save_nodes(app.config["NODE_FILE"], nodes)
            save_edges(app.config["EDGE_FILE"], edges)
            flash(f"Node {node_id} added.", "success")
        except (KeyError, ValueError, MapDataError) as exc:
            flash(str(exc), "error")

        return redirect(url_for("editor"))

    @app.post("/editor/node/<int:node_id>/update")
    @editor_required
    def update_node(node_id: int):
        try:
            nodes, _ = current_map()
            if node_id not in nodes:
                raise ValueError(f"Node ID {node_id} does not exist.")

            updated = Node(
                node_id=node_id,
                x=float(request.form["x"]),
                y=float(request.form["y"]),
                type_id=int(request.form["type_id"]),
                name=request.form["name"].strip(),
            )
            if updated.type_id not in {0, 1, 2, 3, 4}:
                raise ValueError("TypeID must be from 0 to 4.")
            if not updated.name or any(
                character.isspace() for character in updated.name
            ):
                raise ValueError("Node name must be non-empty and contain no spaces.")

            nodes[node_id] = updated
            save_nodes(app.config["NODE_FILE"], nodes)
            flash(f"Node {node_id} updated.", "success")
        except (KeyError, ValueError, MapDataError) as exc:
            flash(str(exc), "error")

        return redirect(url_for("editor"))

    @app.post("/editor/node/<int:node_id>/delete")
    @editor_required
    def delete_node(node_id: int):
        try:
            nodes, edges = current_map()
            if node_id not in nodes:
                raise ValueError(f"Node ID {node_id} does not exist.")

            connected_edges = [
                edge.edge_id
                for edge in edges.values()
                if node_id in {edge.node_a, edge.node_b}
            ]
            if connected_edges:
                raise ValueError(
                    "Delete connected paths first. Connected edge IDs: "
                    + ", ".join(map(str, connected_edges))
                )

            del nodes[node_id]
            save_nodes(app.config["NODE_FILE"], nodes)
            flash(f"Node {node_id} deleted.", "success")
        except (ValueError, MapDataError) as exc:
            flash(str(exc), "error")

        return redirect(url_for("editor"))

    @app.post("/editor/edge/add")
    @editor_required
    def add_edge():
        try:
            nodes, edges = current_map()
            edge_id = int(request.form["edge_id"])
            node_a = int(request.form["node_a"])
            node_b = int(request.form["node_b"])
            distance = float(request.form["distance"])

            if edge_id in edges:
                raise ValueError(f"Edge ID {edge_id} already exists.")
            if node_a not in nodes or node_b not in nodes:
                raise ValueError("Both edge endpoints must exist.")
            if distance < 0:
                raise ValueError("Distance cannot be negative.")

            edges[edge_id] = Edge(edge_id, node_a, node_b, distance)
            save_edges(app.config["EDGE_FILE"], edges)
            flash(f"Edge {edge_id} added.", "success")
        except (KeyError, ValueError, MapDataError) as exc:
            flash(str(exc), "error")

        return redirect(url_for("editor"))

    @app.post("/editor/edge/<int:edge_id>/update")
    @editor_required
    def update_edge(edge_id: int):
        try:
            nodes, edges = current_map()
            if edge_id not in edges:
                raise ValueError(f"Edge ID {edge_id} does not exist.")

            node_a = int(request.form["node_a"])
            node_b = int(request.form["node_b"])
            distance = float(request.form["distance"])

            if node_a not in nodes or node_b not in nodes:
                raise ValueError("Both edge endpoints must exist.")
            if distance < 0:
                raise ValueError("Distance cannot be negative.")

            edges[edge_id] = Edge(edge_id, node_a, node_b, distance)
            save_edges(app.config["EDGE_FILE"], edges)
            flash(f"Edge {edge_id} updated.", "success")
        except (KeyError, ValueError, MapDataError) as exc:
            flash(str(exc), "error")

        return redirect(url_for("editor"))

    @app.post("/editor/edge/<int:edge_id>/delete")
    @editor_required
    def delete_edge(edge_id: int):
        try:
            _, edges = current_map()
            if edge_id not in edges:
                raise ValueError(f"Edge ID {edge_id} does not exist.")
            del edges[edge_id]
            save_edges(app.config["EDGE_FILE"], edges)
            flash(f"Edge {edge_id} deleted.", "success")
        except (ValueError, MapDataError) as exc:
            flash(str(exc), "error")

        return redirect(url_for("editor"))

    @app.errorhandler(MapDataError)
    def handle_map_error(error):
        return render_template("map_error.html", error_message=str(error)), 500

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
