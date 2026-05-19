"""初始化双库表结构；加 --check 可查看数据状态。"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import argparse

from database.connection import md_connection, vector_connection


def _run_sql_file(conn, path: Path) -> None:
    with conn.cursor() as cur:
        cur.execute(path.read_text(encoding="utf-8"))
    print(f"  OK: {path.name}")


def init_schema() -> None:
    db_dir = Path(__file__).parent
    print("[MD 库] 初始化表结构...")
    with md_connection() as conn:
        _run_sql_file(conn, db_dir / "schema_md.sql")

    print("[Vector 库] 初始化表结构...")
    with vector_connection() as conn:
        _run_sql_file(conn, db_dir / "schema_vector.sql")

    print("两套数据库表结构已就绪。")


def check_status() -> None:
    print("=== 环境检查 ===\n")
    with md_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM lol_knowledge_documents")
            md_count = cur.fetchone()[0]
            cur.execute(
                "SELECT COUNT(*) FROM lol_knowledge_documents WHERE is_vectorized = 0"
            )
            pending = cur.fetchone()[0]
            cur.execute(
                "SELECT COUNT(*) FROM lol_knowledge_documents WHERE is_vectorized = 1"
            )
            done = cur.fetchone()[0]

    with vector_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM lol_knowledge_chunks")
            chunk_count = cur.fetchone()[0]

    print(f"[MD 库] 文档 {md_count} 篇（已向量化 {done}，待处理 {pending}）")
    print(f"[Vector 库] 分块 {chunk_count} 条")

    if md_count == 0:
        print("\n下一步: 将 .md 放入 inbox/ 后运行 python database/import_md.py")
    elif pending > 0:
        print("\n下一步: python database/vectorize_md.py")
    else:
        print("\n可启动: python main.py")


def main() -> None:
    parser = argparse.ArgumentParser(description="数据库初始化与状态检查")
    parser.add_argument("--check", action="store_true", help="仅检查双库数据状态")
    args = parser.parse_args()
    init_schema() if not args.check else check_status()


if __name__ == "__main__":
    main()
