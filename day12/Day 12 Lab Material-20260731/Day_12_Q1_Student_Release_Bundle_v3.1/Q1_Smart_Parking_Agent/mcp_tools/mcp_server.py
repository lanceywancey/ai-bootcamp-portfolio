from __future__ import annotations

import json
import os
import platform
import subprocess
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

ROOT = Path(__file__).resolve().parents[1]
ALLOWED_SOURCE_ROOTS = (ROOT / "workspace", ROOT / "candidates", ROOT / "revisers")
ALLOWED_TEST_ROOTS = (ROOT / "tests", ROOT / "instructor_tests")
mcp = FastMCP("Smart Parking Lab Tools")


def _safe_path(relative_path: str, allowed_roots: tuple[Path, ...]) -> Path:
    path = (ROOT / relative_path).resolve()
    if not any(path == root.resolve() or root.resolve() in path.parents for root in allowed_roots):
        raise ValueError(f"path outside allowed roots: {relative_path}")
    return path


def _compiler() -> str:
    override = os.environ.get("CXX")
    if override:
        return override
    return "clang++" if platform.system() == "Darwin" else "g++"


def _executable_path() -> Path:
    suffix = ".exe" if os.name == "nt" else ""
    return ROOT / "workspace" / f"settlement_engine{suffix}"


@mcp.tool()
def compile_cpp(source_path: str = "workspace/settlement_engine.cpp") -> dict[str, Any]:
    """Compile one permitted C++ candidate and return structured evidence."""
    source = _safe_path(source_path, ALLOWED_SOURCE_ROOTS)
    executable = _executable_path()
    command = [_compiler(), "-std=c++17", str(source), "-O0", "-o", str(executable)]
    completed = subprocess.run(command, capture_output=True, text=True, timeout=30, cwd=ROOT)
    return {
        "success": completed.returncode == 0,
        "exit_code": completed.returncode,
        "compiler": command[0],
        "source_path": str(source.relative_to(ROOT)),
        "executable_path": str(executable.relative_to(ROOT)),
        "stdout": completed.stdout[-4000:],
        "stderr": completed.stderr[-4000:],
    }


def _arguments(data: dict[str, Any]) -> list[str]:
    names = ["parking_minutes", "vehicle_type", "import_wh", "import_rate_cents_per_kwh",
             "export_wh", "export_rate_cents_per_kwh", "vehicle_v2g", "station_v2g",
             "owner_opt_in", "soc_after_export", "minimum_departure_soc"]
    return [str(int(data[name])) if isinstance(data[name], bool) else str(data[name]) for name in names]


def _matches(actual: dict[str, Any], expected: dict[str, Any]) -> tuple[bool, str]:
    for key, value in expected.items():
        if key == "error_contains":
            if value not in str(actual.get("error", "")):
                return False, f"error does not contain {value!r}"
        elif actual.get(key) != value:
            return False, f"{key}: expected {value!r}, observed {actual.get(key)!r}"
    return True, ""


@mcp.tool()
def run_tests(test_file: str = "tests/example_tests.json") -> dict[str, Any]:
    """Run JSON test cases against the compiled engine and return structured failures."""
    tests_path = _safe_path(test_file, ALLOWED_TEST_ROOTS)
    executable = _executable_path()
    if not executable.exists():
        return {"success": False, "passed": 0, "failed": 0, "total": 0,
                "failure_signature": "missing_executable", "failures": [{"reason": "compile first"}]}
    tests = json.loads(tests_path.read_text(encoding="utf-8"))
    failures: list[dict[str, Any]] = []
    for case in tests:
        completed = subprocess.run([str(executable), *_arguments(case["input"])], capture_output=True,
                                   text=True, timeout=5, cwd=ROOT)
        try:
            actual = json.loads(completed.stdout.strip())
        except json.JSONDecodeError:
            actual = {"status": "invalid_output", "raw": completed.stdout[-1000:]}
        matched, reason = _matches(actual, case["expected"])
        if not matched:
            failures.append({"name": case["name"], "reason": reason,
                             "expected": case["expected"], "actual": actual})
    signature_text = json.dumps([(f["name"], f["reason"]) for f in failures], sort_keys=True)
    import hashlib
    signature = hashlib.sha256(signature_text.encode()).hexdigest()[:12]
    return {"success": not failures, "passed": len(tests) - len(failures),
            "failed": len(failures), "total": len(tests),
            "failure_signature": signature, "failures": failures}


if __name__ == "__main__":
    mcp.run(transport="stdio")
