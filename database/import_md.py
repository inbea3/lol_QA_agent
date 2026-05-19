"""将 inbox/ 目录下的 .md 文件导入 Neon MD 库。

用法：
  1. 把 Markdown 文件放进项目根目录的 inbox/
  2. 执行：python database/import_md.py
  3. 再执行：python database/vectorize_md.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import argparse

from database.connection import md_connection, vector_connection

INBOX_DIR = Path(__file__).resolve().parent.parent / "inbox"


def _clear_chunks(document_id: int) -> None:
    with vector_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM lol_knowledge_chunks WHERE document_id = %s",
                (document_id,),
            )


def _parse_title(content: str, fallback: str) -> str:
    for line in content.splitlines():
        line = line.strip()
        if line.startswith("# "):
            return line[2:].strip()
    return fallback


def import_file(path: Path, source: str = "general", upsert: bool = True) -> int:
    if not path.exists():
        raise FileNotFoundError(f"文件不存在: {path}")
    if path.suffix.lower() != ".md":
        raise ValueError(f"仅支持 .md 文件: {path}")

    content = path.read_text(encoding="utf-8").strip()
    if not content:
        raise ValueError(f"文件内容为空: {path}")

    title = _parse_title(content, path.stem)

    with md_connection() as conn:
        with conn.cursor() as cur:
            if upsert:
                cur.execute(
                    """
                    SELECT id FROM lol_knowledge_documents
                    WHERE doc_title = %s AND doc_source = %s
                    """,
                    (title, source),
                )
                row = cur.fetchone()
                if row:
                    doc_id = row[0]
                    cur.execute(
                        """
                        UPDATE lol_knowledge_documents
                        SET markdown_content = %s, is_vectorized = 0, update_time = NOW()
                        WHERE id = %s
                        """,
                        (content, doc_id),
                    )
                    _clear_chunks(doc_id)
                    print(f"  更新: [{doc_id}] {title} ← {path.name}")
                    return doc_id

            cur.execute(
                """
                INSERT INTO lol_knowledge_documents
                    (doc_title, doc_source, markdown_content, is_vectorized)
                VALUES (%s, %s, %s, 0)
                RETURNING id
                """,
                (title, source, content),
            )
            doc_id = cur.fetchone()[0]
            print(f"  新增: [{doc_id}] {title} ← {path.name}")
            return doc_id


def import_inbox(source: str = "general", upsert: bool = True) -> int:
    INBOX_DIR.mkdir(exist_ok=True)
    files = sorted(INBOX_DIR.glob("*.md"))
    if not files:
        print(f"inbox/ 中暂无 .md 文件，请先将 Markdown 放入: {INBOX_DIR}")
        return 0

    for path in files:
        import_file(path, source=source, upsert=upsert)
    print(f"\n共导入 {len(files)} 篇 → MD 库。请运行: python database/vectorize_md.py")
    return len(files)


def main() -> None:
    parser = argparse.ArgumentParser(description="从 inbox/ 导入 Markdown 到 MD 库")
    parser.add_argument(
        "file",
        nargs="?",
        help="仅导入指定文件名（须在 inbox/ 内），默认导入 inbox/ 下全部 .md",
    )
    parser.add_argument("--source", default="general", help="来源标签")
    parser.add_argument("--no-upsert", action="store_true", help="同标题+来源已存在则跳过（不更新）")
    args = parser.parse_args()

    upsert = not args.no_upsert
    if args.file:
        path = INBOX_DIR / args.file
        import_file(path, source=args.source, upsert=upsert)
        print("\n请运行: python database/vectorize_md.py")
    else:
        import_inbox(source=args.source, upsert=upsert)


if __name__ == "__main__":
    main()
