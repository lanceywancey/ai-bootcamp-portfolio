"""MCP server exposing IoT temperature lab tools.

Tools:
  - read_temperature_file(path)
  - calculate_average_internal(numbers)
  - calculate_average_external(path)

Run normally through the agent controller, or test with MCP Inspector.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("IoT Temperature MCP Server")

CONFIG: dict[str, Any] = {}
PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _resolve_project_path(path: str) -> Path:
    p = Path(path)
    if not p.is_absolute():
        p = PROJECT_ROOT / p
    return p.resolve()


def _load_config(config_path: str | None) -> dict[str, Any]:
    if config_path is None:
        config_file = PROJECT_ROOT / "config.json"
    else:
        config_file = _resolve_project_path(config_path)
    if config_file.exists():
        return json.loads(config_file.read_text(encoding="utf-8"))
    return {}


@mcp.tool()
def read_temperature_file(path: str) -> dict[str, Any]:
    """Read valid temperature values from a text file.

    Blank lines and lines starting with # are ignored.
    """
    file_path = _resolve_project_path(path)
    if not file_path.exists():
        return {"error": True, "message": f"File not found: {file_path}"}

    values: list[float] = []
    invalid_lines: list[dict[str, Any]] = []

    for line_no, raw_line in enumerate(file_path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        try:
            values.append(float(line))
        except ValueError:
            invalid_lines.append({"line": line_no, "text": raw_line})

    if invalid_lines:
        return {"error": True, "message": "Invalid numeric lines found", "invalid_lines": invalid_lines}
    if not values:
        return {"error": True, "message": "No valid temperature values found"}

    return {"error": False, "path": str(file_path), "values": values}


@mcp.tool()
def calculate_average_internal(numbers: list[float]) -> dict[str, Any]:
    """Calculate count, sum, and average directly inside the MCP server."""
    if not numbers:
        return {"error": True, "message": "numbers list is empty"}
    values = [float(x) for x in numbers]
    total = sum(values)
    return {"error": False, "count": len(values), "sum": total, "average": total / len(values)}


@mcp.tool()
def calculate_average_external(path: str) -> dict[str, Any]:
    """Calculate average by launching the external C++ executable.

    The executable path is read from config.json, key average_calculator_exe.
    The executable must print JSON to stdout.
    """
    exe = CONFIG.get("average_calculator_exe", "tools/average_calculator.exe" if os.name == "nt" else "tools/average_calculator")
    exe_path = _resolve_project_path(str(exe))
    input_path = _resolve_project_path(path)

    if not exe_path.exists():
        return {
            "error": True,
            "message": "External average calculator executable not found",
            "expected_path": str(exe_path),
            "hint": "Compile cpp/average_calculator.cpp and place the executable under tools/.",
        }
    if not input_path.exists():
        return {"error": True, "message": f"Input file not found: {input_path}"}

    try:
        result = subprocess.run(
            [str(exe_path), str(input_path)],
            capture_output=True,
            text=True,
            timeout=5,
            cwd=str(PROJECT_ROOT),
            check=False,
        )
    except subprocess.TimeoutExpired:
        return {"error": True, "message": "External calculator timed out"}

    if result.returncode != 0:
        return {
            "error": True,
            "message": "External calculator failed",
            "returncode": result.returncode,
            "stderr": result.stderr,
            "stdout": result.stdout,
        }

    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        return {
            "error": True,
            "message": "External calculator did not return valid JSON",
            "json_error": str(exc),
            "stdout": result.stdout,
            "stderr": result.stderr,
        }

    payload["error"] = False
    payload["source"] = "external_cpp_executable"
    return payload


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config.json")
    args = parser.parse_args()

    global CONFIG
    CONFIG = _load_config(args.config)

    # Important: logs/debug messages must go to stderr so stdout remains clean
    # for stdio JSON-RPC messages.
    print("IoT Temperature MCP Server starting over stdio", file=sys.stderr)
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
