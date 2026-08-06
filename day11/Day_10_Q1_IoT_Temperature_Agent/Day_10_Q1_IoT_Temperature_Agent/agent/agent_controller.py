"""Agent controller for Lab 1: IoT Temperature Agent.

This controller demonstrates:
  - MCP tool calls over stdio
  - internal vs external average calculation
  - HTTP call to a mock weather server
  - deterministic, simulated LLM, and optional real LLM report generation
  - bounded loop mode with exit conditions

Example:
  python agent/agent_controller.py --calculator internal --report deterministic
  python agent/agent_controller.py --calculator external --report simulated-llm
  python agent/agent_controller.py --calculator external --report simulated-llm --loop --interval 20 --timeout 120
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import select
import sys
import time
from pathlib import Path
from typing import Any

import requests
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Allow imports from this folder when script is run from project root.
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
sys.path.insert(0, str(CURRENT_DIR))

import report_deterministic  # noqa: E402
import report_real_llm_optional  # noqa: E402
import report_simulated_llm  # noqa: E402


def load_config(path: str) -> dict[str, Any]:
    config_path = Path(path)
    if not config_path.is_absolute():
        config_path = PROJECT_ROOT / config_path
    return json.loads(config_path.read_text(encoding="utf-8"))


def extract_tool_payload(result: Any) -> dict[str, Any]:
    """Convert MCP SDK tool result into a Python dictionary.

    Depending on SDK version, content may be returned as structured content or
    as text content. This helper keeps the lab code easy to inspect.
    """
    if hasattr(result, "structuredContent") and result.structuredContent is not None:
        return dict(result.structuredContent)

    if hasattr(result, "structured_content") and result.structured_content is not None:
        return dict(result.structured_content)

    content = getattr(result, "content", None)
    if content:
        first = content[0]
        text = getattr(first, "text", None)
        if text is not None:
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                return {"error": False, "text": text}

    # Last-resort fallback for unexpected SDK object shapes.
    return {"error": True, "message": f"Cannot parse MCP result: {result!r}"}


def get_current_temperature(weather_url: str) -> dict[str, Any]:
    response = requests.get(weather_url, timeout=5)
    response.raise_for_status()
    return response.json()


def build_context(avg_payload: dict[str, Any], weather_payload: dict[str, Any]) -> dict[str, Any]:
    avg = float(avg_payload["average"])
    current = float(weather_payload["temperature_c"])

    return {
        "historical_average_temperature_c": avg,
        "current_singapore_temperature_c": current,
        "difference_c": current - avg,
        "location": weather_payload.get("location", "Singapore"),
        "condition": weather_payload.get("condition", "Unknown"),
        "source": weather_payload.get("source", "unknown"),
        "instruction": "Generate a short report and advise whether aircon should be turned on.",
        "constraints": [
            "Use no more than 120 words",
            "Do not invent sensor data",
            "Mention both temperatures",
        ],
    }


def generate_report(context: dict[str, Any], mode: str) -> str:
    if mode == "deterministic":
        return report_deterministic.generate_report(context)
    if mode == "simulated-llm":
        return report_simulated_llm.generate_report(context)
    if mode == "real-llm":
        return report_real_llm_optional.generate_report(context)
    raise ValueError(f"Unknown report mode: {mode}")


def user_pressed_q() -> bool:
    """Non-blocking q check.

    On POSIX systems, this checks stdin with select().
    On Windows, it uses msvcrt if available.

    The controller also has timeout and max-iteration exit conditions, so this
    is only a convenience feature.
    """
    if os.name == "nt":
        try:
            import msvcrt  # type: ignore

            if msvcrt.kbhit():
                ch = msvcrt.getwch()
                return ch.lower() == "q"
        except Exception:
            return False
        return False

    try:
        ready, _, _ = select.select([sys.stdin], [], [], 0)
        if ready:
            return sys.stdin.readline().strip().lower() == "q"
    except Exception:
        return False

    return False


def print_step(message: str) -> None:
    """Print a visible step marker for teaching/debugging."""
    print(f"[Agent] {message}")


async def run_once(
    session: ClientSession,
    config: dict[str, Any],
    calculator: str,
    report: str,
) -> str:
    temperature_file = config.get("temperature_file", "numbers.txt")
    weather_url = config.get("weather_url", "http://localhost:60004/current_temperature")

    print_step(f"Calling MCP tool: read_temperature_file(path='{temperature_file}')")
    read_result = await session.call_tool(
        "read_temperature_file",
        arguments={"path": temperature_file},
    )
    read_payload = extract_tool_payload(read_result)

    if read_payload.get("error"):
        raise RuntimeError(f"read_temperature_file failed: {read_payload}")

    values = read_payload.get("values", [])
    print_step(f"Tool result: read {len(values)} temperature values")

    if calculator == "internal":
        print_step("Calling MCP tool: calculate_average_internal(numbers)")
        avg_result = await session.call_tool(
            "calculate_average_internal",
            arguments={"numbers": values},
        )
    elif calculator == "external":
        print_step(f"Calling MCP tool: calculate_average_external(path='{temperature_file}')")
        print_step("This MCP tool wraps the external C++ executable configured in config.json")
        avg_result = await session.call_tool(
            "calculate_average_external",
            arguments={"path": temperature_file},
        )
    else:
        raise ValueError(f"Unknown calculator mode: {calculator}")

    avg_payload = extract_tool_payload(avg_result)

    if avg_payload.get("error"):
        raise RuntimeError(f"average calculation failed: {avg_payload}")

    print_step(
        "Tool result: "
        f"count={avg_payload.get('count')}, "
        f"sum={float(avg_payload.get('sum')):.2f}, "
        f"average={float(avg_payload.get('average')):.2f}"
    )

    print_step(f"Calling HTTP service: {weather_url}")
    weather_payload = get_current_temperature(weather_url)

    print_step(
        "HTTP result: "
        f"location={weather_payload.get('location')}, "
        f"temperature={weather_payload.get('temperature_c')} C, "
        f"condition={weather_payload.get('condition')}"
    )

    print_step("Building structured context for report generation")
    context = build_context(avg_payload, weather_payload)

    print_step(f"Generating report using mode: {report}")
    return generate_report(context, report)


async def main_async(args: argparse.Namespace) -> None:
    config = load_config(args.config)

    server_script = PROJECT_ROOT / "mcp_servers" / "temperature_mcp_server.py"

    server_params = StdioServerParameters(
        command=sys.executable,
        args=[str(server_script), "--config", args.config],
        cwd=str(PROJECT_ROOT),
    )

    print_step("Starting MCP server over stdio")
    print_step(f"MCP server script: {server_script}")
    print()

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            print_step("Initializing MCP client session")
            await session.initialize()

            print_step("Discovering MCP tools")
            tools = await session.list_tools()

            print("Discovered MCP tools:")
            for tool in tools.tools:
                print(f"  - {tool.name}")
            print()

            start_time = time.time()
            iteration = 0

            max_iterations = args.max_iterations or int(config.get("max_iterations", 6))
            timeout_seconds = args.timeout or int(config.get("timeout_seconds", 120))
            interval = args.interval or int(config.get("loop_interval_seconds", 20))

            while True:
                iteration += 1

                print("=" * 72)
                print(f"Iteration {iteration}")
                print("=" * 72)

                try:
                    report_text = await run_once(
                        session=session,
                        config=config,
                        calculator=args.calculator,
                        report=args.report,
                    )
                    print()
                    print(report_text)
                except Exception as exc:
                    print(f"ERROR: {exc}")
                    print("Exit condition reached: unrecoverable tool or service error.")
                    break

                if not args.loop:
                    break

                if iteration >= max_iterations:
                    print("Exit condition reached: max iterations.")
                    break

                if time.time() - start_time >= timeout_seconds:
                    print("Exit condition reached: timeout.")
                    break

                print(f"\nWaiting {interval} seconds. Press q then Enter to stop, or Ctrl+C.")

                sleep_start = time.time()
                while time.time() - sleep_start < interval:
                    if user_pressed_q():
                        print("Exit condition reached: user pressed q.")
                        return
                    await asyncio.sleep(0.25)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Lab 1 IoT Temperature Agent Controller"
    )

    parser.add_argument(
        "--config",
        default="config.json",
        help="Path to config.json. Default: config.json",
    )

    parser.add_argument(
        "--calculator",
        choices=["internal", "external"],
        default="internal",
        help="Average-calculation implementation: internal Python tool or external C++ executable wrapper.",
    )

    parser.add_argument(
        "--report",
        choices=["deterministic", "simulated-llm", "real-llm"],
        default="deterministic",
        help="Report generation mode.",
    )

    parser.add_argument(
        "--loop",
        action="store_true",
        help="Run the controller repeatedly until an exit condition is reached.",
    )

    parser.add_argument(
        "--interval",
        type=int,
        default=None,
        help="Seconds between loop iterations. If omitted, use config.json.",
    )

    parser.add_argument(
        "--timeout",
        type=int,
        default=None,
        help="Maximum loop runtime in seconds. If omitted, use config.json.",
    )

    parser.add_argument(
        "--max-iterations",
        type=int,
        default=None,
        help="Maximum number of loop iterations. If omitted, use config.json.",
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    try:
        asyncio.run(main_async(args))
    except KeyboardInterrupt:
        print("\nExit condition reached: Ctrl+C / KeyboardInterrupt.")


if __name__ == "__main__":
    main()