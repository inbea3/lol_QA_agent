"""快速验证 MCP 是否可用。"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from mcp_tools.time_client import call_time_mcp
from mcp_tools.wiki_client import call_wiki_mcp


def main() -> None:
    print("=== Time MCP ===")
    print(call_time_mcp("现在几点？"))
    print("\n=== Fetch MCP ===")
    print(call_wiki_mcp("Yasuo")[:800], "...\n")


if __name__ == "__main__":
    main()
