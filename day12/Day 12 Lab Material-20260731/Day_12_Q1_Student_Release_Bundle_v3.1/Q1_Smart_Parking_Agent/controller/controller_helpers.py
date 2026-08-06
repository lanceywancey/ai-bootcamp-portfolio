from __future__ import annotations

import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def source_hash(source: str) -> str:
    return hashlib.sha256(source.encode()).hexdigest()[:12]


def save_candidate(source: str, index: int) -> str:
    target = ROOT / "candidates" / f"candidate_{index}.cpp"
    target.write_text(source, encoding="utf-8")
    shutil.copyfile(target, ROOT / "workspace" / "settlement_engine.cpp")
    return str(target.relative_to(ROOT))


def write_trace(event: dict) -> None:
    event = {"timestamp": datetime.now(timezone.utc).isoformat(), **event}
    with (ROOT / "logs" / "trace.jsonl").open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(event) + "\n")


def write_final_state(state: dict) -> None:
    (ROOT / "state" / "final_state.json").write_text(json.dumps(state, indent=2), encoding="utf-8")
