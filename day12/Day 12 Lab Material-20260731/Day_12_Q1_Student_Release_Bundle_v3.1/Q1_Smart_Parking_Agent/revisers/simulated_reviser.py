from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def revise(current_source: str, evidence: dict, repair_number: int) -> str:
    """Return a deterministic instructor-prepared candidate for repeatable teaching."""
    del current_source, evidence
    number = min(repair_number + 1, 2)
    path = ROOT / "revisers" / "simulated_candidates" / f"candidate_{number}.cpp"
    return path.read_text(encoding="utf-8")
