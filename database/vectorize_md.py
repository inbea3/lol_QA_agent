"""将 is_vectorized=0 的 MD 分块并写入 Vector 库。"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.settings import settings
from database.connection import md_connection, vector_connection
from rag.chunking import split_text
from rag.embedder import Embedder


def _fetch_pending() -> list[dict]:
    with md_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, doc_title, markdown_content
                FROM lol_knowledge_documents
                WHERE is_vectorized = 0
                ORDER BY id
                """
            )
            rows = cur.fetchall()
    return [{"id": r[0], "doc_title": r[1], "markdown_content": r[2]} for r in rows]


def _mark_done(document_id: int) -> None:
    with md_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE lol_knowledge_documents
                SET is_vectorized = 1, update_time = NOW()
                WHERE id = %s
                """,
                (document_id,),
            )


def _clear_chunks(document_id: int) -> None:
    with vector_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM lol_knowledge_chunks WHERE document_id = %s",
                (document_id,),
            )


def vectorize_pending() -> int:
    docs = _fetch_pending()
    if not docs:
        print("没有待处理文档（is_vectorized = 0）。")
        return 0

    embedder = Embedder()
    seps = ["\n## ", "\n### ", "\n", "。", " ", ""]
    total = 0

    for doc in docs:
        doc_id = doc["id"]
        chunks = split_text(
            doc["markdown_content"],
            settings.chunk_size,
            settings.chunk_overlap,
            seps,
        )
        if not chunks:
            print(f"  跳过: [{doc_id}] {doc['doc_title']}")
            continue

        _clear_chunks(doc_id)
        vectors = embedder.embed_texts(chunks)

        with vector_connection() as conn:
            with conn.cursor() as cur:
                for idx, (text, vec) in enumerate(zip(chunks, vectors)):
                    vec_lit = "[" + ",".join(f"{v:.8f}" for v in vec) + "]"
                    cur.execute(
                        """
                        INSERT INTO lol_knowledge_chunks
                            (document_id, doc_title, chunk_index, chunk_content, chunk_embedding)
                        VALUES (%s, %s, %s, %s, %s::vector)
                        ON CONFLICT (document_id, chunk_index) DO UPDATE SET
                            doc_title = EXCLUDED.doc_title,
                            chunk_content = EXCLUDED.chunk_content,
                            chunk_embedding = EXCLUDED.chunk_embedding
                        """,
                        (doc_id, doc["doc_title"], idx, text, vec_lit),
                    )
                    total += 1

        _mark_done(doc_id)
        print(f"  完成: [{doc_id}] {doc['doc_title']} → {len(chunks)} 块")

    print(f"共处理 {len(docs)} 篇，写入 {total} 条分块。")
    return total


if __name__ == "__main__":
    vectorize_pending()
