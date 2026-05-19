from __future__ import annotations

import re

from config.settings import settings
from mcp_tools.runner import call_mcp_tool


def _parse_convert_time(query: str) -> dict[str, str] | None:
    m = re.search(
        r"(\d{1,2}:\d{2}).*?(Asia/Shanghai|UTC|America/New_York|Europe/London|"
        r"Asia/Tokyo|Asia/Seoul).*?(Asia/Shanghai|UTC|America/New_York|Europe/London|"
        r"Asia/Tokyo|Asia/Seoul)",
        query,
        re.I,
    )
    if not m:
        return None
    time_str, src, tgt = m.group(1), m.group(2), m.group(3)
    if src == tgt:
        return None
    return {"time": time_str, "source_timezone": src, "target_timezone": tgt}


def call_time_mcp(query: str) -> str:
    if not settings.time_mcp_enabled:
        return "（时间 MCP 未启用）"

    try:
        blocks: list[str] = [f"【用户问题】{query}"]

        current = call_mcp_tool(
            settings.time_mcp,
            "get_current_time",
            {"timezone": settings.mcp_timezone},
        )
        blocks.append(f"【当前时间 · {settings.mcp_timezone}】\n{current}")

        convert_args = _parse_convert_time(query)
        if convert_args:
            converted = call_mcp_tool(settings.time_mcp, "convert_time", convert_args)
            blocks.append(
                f"【时区转换 · {convert_args['source_timezone']} → "
                f"{convert_args['target_timezone']}】\n{converted}"
            )

        return "\n\n".join(blocks)
    except Exception as e:
        return f"（时间 MCP 调用失败: {e}。请确认: pip install mcp-server-time）"
