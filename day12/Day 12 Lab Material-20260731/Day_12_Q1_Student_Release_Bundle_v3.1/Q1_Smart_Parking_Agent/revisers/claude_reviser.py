from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _extract_cpp(text: str) -> str:
    """Extract a complete C++ program from Claude's response."""
    if "```cpp" in text:
        return text.split("```cpp", 1)[1].split("```", 1)[0].strip() + "\n"
    if "```" in text:
        return text.split("```", 1)[1].split("```", 1)[0].strip() + "\n"
    return text.strip() + "\n"


def revise(current_source: str, evidence: dict, repair_number: int) -> str:
    """Ask Claude Code to return a repaired complete C++ source file."""
    del repair_number

    executable = shutil.which("claude")
    if executable is None:
        raise RuntimeError(
            "Claude Code CLI was not found on PATH. "
            "Run 'claude --version' to verify the installation."
        )

    rules_path = ROOT / "specs" / "settlement_rules.txt"
    rules = rules_path.read_text(encoding="utf-8")

    prompt = f"""
You are repairing one C++17 source file in a controlled teaching lab.

Return only the complete revised C++ source code.
Do not include explanations or Markdown commentary.
Do not change the command-line interface.
Do not change the required JSON output fields.
Make the smallest repair supported by the compiler and test evidence.

Follow these settlement rules:

{rules}

Current C++ source:

```cpp
{current_source}
```

Compiler and test evidence:

{json.dumps(evidence, indent=2)}

Security restrictions:

- Do not add network access.
- Do not add filesystem access.
- Do not add shell-command execution.
- Do not launch another process.
- Do not modify the test files.
- Do not weaken validation merely to make a test pass.

Return the complete revised C++ source now.
""".strip()

    completed = subprocess.run(
        [
            executable,
            "-p",
            prompt,
            "--max-turns",
            "3",
            "--output-format",
            "text",
        ],
        capture_output=True,
        text=True,
        timeout=180,
        cwd=ROOT,
    )

    if completed.returncode != 0:
        stdout = completed.stdout[-4000:].strip()
        stderr = completed.stderr[-4000:].strip()
        raise RuntimeError(
            "Claude Code failed "
            f"(exit code {completed.returncode}).\n"
            f"STDOUT:\n{stdout or '<empty>'}\n"
            f"STDERR:\n{stderr or '<empty>'}"
        )

    source = _extract_cpp(completed.stdout)

    if "int main" not in source:
        raise RuntimeError(
            "Claude's response did not contain an int main function.\n"
            f"Response preview:\n{completed.stdout[-2000:]}"
        )

    if len(source) < 500:
        raise RuntimeError(
            "Claude's response was too short to be a complete C++ program.\n"
            f"Response preview:\n{completed.stdout[-2000:]}"
        )

    return source
