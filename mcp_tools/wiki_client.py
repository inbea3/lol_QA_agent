from __future__ import annotations

from urllib.parse import quote

from config.settings import settings
from mcp_tools.runner import call_mcp_tool


def _fetch_url(url: str) -> str:
    return call_mcp_tool(
        settings.fetch_mcp,
        "fetch",
        {"url": url, "max_length": settings.fetch_max_length},
    )


def call_wiki_mcp(query: str) -> str:
    if not settings.fetch_mcp_enabled:
        return "（Fetch MCP 未启用）"

    urls = [
        settings.wiki_search_url.format(query=quote(query)),
        settings.wiki_fallback_url.format(query=quote(query)),
    ]
    errors: list[str] = []

    for url in urls:
        try:
            content = _fetch_url(url)
            if content.strip().lower().startswith("failed to fetch"):
                errors.append(f"{url}: {content[:200]}")
                continue
            return f"【抓取来源】{url}\n\n{content}"
        except Exception as e:
            errors.append(f"{url}: {e}")

    return (
        "（Fetch MCP 未能抓取外网页面，可能为站点 403 或网络问题。"
        "请优先依赖本地 RAG 知识库。）\n"
        + "\n".join(errors[:2])
    )
