from __future__ import annotations

import asyncio
from typing import Any

from config.mcp_config import McpServerConfig
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


def _extract_tool_text(result: Any) -> str:
    parts: list[str] = []
    for block in result.content or []:
        text = getattr(block, "text", None)
        if text:
            parts.append(text)
    return "\n".join(parts).strip()


async def _call_tool_async(
    config: McpServerConfig,
    tool_name: str,
    arguments: dict[str, Any],
) -> str:
    params = StdioServerParameters(command=config.command, args=config.args)
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(tool_name, arguments=arguments)
            return _extract_tool_text(result)


def call_mcp_tool(
    config: McpServerConfig,
    tool_name: str,
    arguments: dict[str, Any] | None = None,
) -> str:
    return asyncio.run(_call_tool_async(config, tool_name, arguments or {}))
