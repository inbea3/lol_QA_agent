from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

from config.mcp_config import McpServerConfig

ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")


def _parse_args(value: str) -> list[str]:
    return [p for p in value.split() if p]


def _require(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise ValueError(f"缺少环境变量: {name}")
    return value


def _optional(name: str, default: str = "") -> str:
    return os.getenv(name, default)


@dataclass(frozen=True)
class DbConfig:
    host: str
    database: str
    user: str
    password: str
    sslmode: str = "require"

    @property
    def dsn(self) -> str:
        return (
            f"host={self.host} dbname={self.database} user={self.user} "
            f"password={self.password} sslmode={self.sslmode}"
        )


@dataclass(frozen=True)
class Settings:
    root_dir: Path
    md_db: DbConfig
    vector_db: DbConfig
    model_name: str
    api_key: str
    base_url: str
    retrieval_backend: str
    embedding_dim: int
    chunk_size: int
    chunk_overlap: int
    rag_top_k: int
    hybrid_candidate_k: int
    rrf_k: int
    time_mcp: McpServerConfig
    time_mcp_enabled: bool
    fetch_mcp: McpServerConfig
    fetch_mcp_enabled: bool
    mcp_timezone: str
    fetch_max_length: int
    wiki_search_url: str
    wiki_fallback_url: str
    memory_max_turns: int


settings = Settings(
    root_dir=ROOT_DIR,
    md_db=DbConfig(
        host=_require("MD_PGHOST"),
        database=_require("MD_PGDATABASE"),
        user=_require("MD_PGUSER"),
        password=_require("MD_PGPASSWORD"),
        sslmode=_optional("MD_PGSSLMODE", "require"),
    ),
    vector_db=DbConfig(
        host=_require("VECTOR_PGHOST"),
        database=_require("VECTOR_PGDATABASE"),
        user=_require("VECTOR_PGUSER"),
        password=_require("VECTOR_PGPASSWORD"),
        sslmode=_optional("VECTOR_PGSSLMODE", "require"),
    ),
    model_name=_require("MODEL_NAME"),
    api_key=_require("API_KEY"),
    base_url=_require("BASE_URL"),
    retrieval_backend=_optional("RETRIEVAL_BACKEND", "hybrid"),
    embedding_dim=int(_optional("EMBEDDING_DIM", "512")),
    chunk_size=int(_optional("CHUNK_SIZE", "500")),
    chunk_overlap=int(_optional("CHUNK_OVERLAP", "80")),
    rag_top_k=int(_optional("RAG_TOP_K", "5")),
    hybrid_candidate_k=int(_optional("HYBRID_CANDIDATE_K", "20")),
    rrf_k=int(_optional("RRF_K", "60")),
    time_mcp=McpServerConfig(
        command=_optional("TIME_MCP_COMMAND", "python"),
        args=_parse_args(_optional("TIME_MCP_ARGS", "-m mcp_server_time")),
    ),
    time_mcp_enabled=_optional("TIME_MCP_ENABLED", "true").lower() == "true",
    fetch_mcp=McpServerConfig(
        command=_optional("FETCH_MCP_COMMAND", "python"),
        args=_parse_args(_optional("FETCH_MCP_ARGS", "-m mcp_server_fetch")),
    ),
    fetch_mcp_enabled=_optional("FETCH_MCP_ENABLED", "true").lower() == "true",
    mcp_timezone=_optional("MCP_TIMEZONE", "Asia/Shanghai"),
    fetch_max_length=int(_optional("FETCH_MAX_LENGTH", "6000")),
    wiki_search_url=_optional(
        "WIKI_SEARCH_URL",
        "https://leagueoflegends.fandom.com/wiki/Special:Search?query={query}",
    ),
    wiki_fallback_url=_optional(
        "WIKI_FALLBACK_URL",
        "https://en.wikipedia.org/w/index.php?search={query}",
    ),
    memory_max_turns=int(_optional("MEMORY_MAX_TURNS", "10")),
)
