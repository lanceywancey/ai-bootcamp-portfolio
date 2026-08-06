from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

ROOT = Path(__file__).resolve().parents[1]


async def call_tool(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    parameters = StdioServerParameters(
        command=sys.executable,
        args=[str(ROOT / "mcp_tools" / "mcp_server.py")],
        cwd=str(ROOT),
    )
    async with stdio_client(parameters) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            result = await session.call_tool(name, arguments=arguments)
            if result.structuredContent is not None:
                return dict(result.structuredContent)
            if result.content:
                return json.loads(result.content[0].text)
            return {}
