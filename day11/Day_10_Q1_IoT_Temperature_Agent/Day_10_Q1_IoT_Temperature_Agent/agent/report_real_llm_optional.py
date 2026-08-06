"""Optional real LLM report generator using Claude Code CLI.

This file is optional. The required lab does not need Claude Code or a paid API key.

Requirement:
  Claude Code must be installed and authenticated.

Manual test:
  claude -p "Write one sentence about Singapore weather."
"""

from __future__ import annotations

import json
import shutil
import subprocess
from typing import Any


def generate_report(context: dict[str, Any]) -> str:
    prompt = (
        "Generate a concise temperature comfort report.\n"
        "Compare the historical indoor average temperature with the current "
        "Singapore temperature and advise whether air-conditioning should be "
        "turned on.\n"
        "Do not invent data. Use no more than 120 words.\n\n"
        "Context JSON:\n"
        f"{json.dumps(context, indent=2)}"
    )

    claude_path = shutil.which("claude")

    if claude_path is None:
        return (
            "Claude Code CLI is not found in PATH.\n\n"
            "Install and login to Claude Code first, or use the simulated LLM mode.\n\n"
            "The prompt that would be sent to Claude Code is:\n\n"
            f"{prompt}"
        )

    print(f"[Real LLM] Calling Claude Code CLI at: {claude_path}")
    print("[Real LLM] Sending structured temperature context to Claude Code")

    try:
        result = subprocess.run(
            [claude_path, "-p", prompt],
            capture_output=True,
            text=True,
            timeout=90,
        )
    except subprocess.TimeoutExpired:
        return "Claude Code CLI timed out after 90 seconds."

    if result.returncode != 0:
        return (
            "Claude Code CLI returned an error.\n\n"
            f"Command:\n{claude_path} -p <prompt>\n\n"
            f"stderr:\n{result.stderr}\n\n"
            f"stdout:\n{result.stdout}\n\n"
            f"Prompt was:\n{prompt}"
        )

    output = result.stdout.strip()

    if not output:
        return (
            "Claude Code CLI returned empty output.\n\n"
            f"Prompt was:\n{prompt}"
        )

    return output