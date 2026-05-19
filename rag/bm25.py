from __future__ import annotations

import re
from dataclasses import dataclass

from rank_bm25 import BM25Okapi

from database.connection import vector_connection


def tokenize(text: str) -> list[str]:
    tokens = re.findall(r"[\u4e00-\u9fff]|[a-zA-Z0-9]+", text.lower())
    return tokens if tokens else list(text.strip())


@dataclass
class ChunkRecord:
    chunk_id: int
    document_id: int
    doc_title: str
    chunk_content: str


def load_all_chunks() -> list[ChunkRecord]:
    with vector_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, document_id, doc_title, chunk_content
                FROM lol_knowledge_chunks
                ORDER BY id
                """
            )
            rows = cur.fetchall()
    return [
        ChunkRecord(
            chunk_id=r[0],
            document_id=r[1],
            doc_title=r[2] or "",
            chunk_content=r[3],
        )
        for r in rows
    ]


def bm25_search(query: str, top_k: int) -> list[tuple[ChunkRecord, float]]:
    chunks = load_all_chunks()
    if not chunks:
        return []

    corpus = [tokenize(c.chunk_content) for c in chunks]
    bm25 = BM25Okapi(corpus)
    query_tokens = tokenize(query)
    if not query_tokens:
        return []

    scores = bm25.get_scores(query_tokens)
    ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)

    results: list[tuple[ChunkRecord, float]] = []
    for idx, score in ranked[:top_k]:
        if score <= 0:
            continue
        results.append((chunks[idx], float(score)))
    return results
