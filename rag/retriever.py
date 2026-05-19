from __future__ import annotations

from dataclasses import dataclass

from config.settings import settings
from database.connection import md_connection, vector_connection
from rag.bm25 import bm25_search
from rag.embedder import Embedder


@dataclass
class RetrievedChunk:
    chunk_id: int
    document_id: int
    doc_title: str
    chunk_content: str
    score: float
    markdown_content: str | None = None
    bm25_score: float | None = None
    vector_score: float | None = None


class RAGRetriever:
    def __init__(self, top_k: int | None = None) -> None:
        self.top_k = top_k or settings.rag_top_k
        self.embedder = Embedder()

    def search(self, query: str, top_k: int | None = None) -> list[RetrievedChunk]:
        k = top_k or self.top_k
        candidate_k = max(k, settings.hybrid_candidate_k)

        backend = settings.retrieval_backend.lower()
        if backend == "bm25":
            return self._attach_markdown(self._search_bm25(query, k))
        if backend == "vector":
            return self._attach_markdown(self._search_vector(query, k))
        return self._attach_markdown(self._search_hybrid(query, k, candidate_k))

    def _search_bm25(self, query: str, k: int) -> list[RetrievedChunk]:
        return [
            RetrievedChunk(
                chunk_id=c.chunk_id,
                document_id=c.document_id,
                doc_title=c.doc_title,
                chunk_content=c.chunk_content,
                score=score,
                bm25_score=score,
            )
            for c, score in bm25_search(query, k)
        ]

    def _search_vector(self, query: str, k: int) -> list[RetrievedChunk]:
        query_vec = self.embedder.embed_query(query)
        vec_literal = "[" + ",".join(f"{v:.8f}" for v in query_vec) + "]"

        with vector_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, document_id, doc_title, chunk_content,
                           1 - (chunk_embedding <=> %s::vector) AS score
                    FROM lol_knowledge_chunks
                    WHERE chunk_embedding IS NOT NULL
                    ORDER BY chunk_embedding <=> %s::vector
                    LIMIT %s
                    """,
                    (vec_literal, vec_literal, k),
                )
                rows = cur.fetchall()

        return [
            RetrievedChunk(
                chunk_id=r[0],
                document_id=r[1],
                doc_title=r[2] or "",
                chunk_content=r[3],
                score=float(r[4]),
                vector_score=float(r[4]),
            )
            for r in rows
        ]

    def _search_hybrid(self, query: str, k: int, candidate_k: int) -> list[RetrievedChunk]:
        bm25_hits = self._search_bm25(query, candidate_k)
        vector_hits = self._search_vector(query, candidate_k)
        return self._rrf_merge(bm25_hits, vector_hits, k)

    def _rrf_merge(
        self,
        bm25_hits: list[RetrievedChunk],
        vector_hits: list[RetrievedChunk],
        top_k: int,
    ) -> list[RetrievedChunk]:
        """RRF 融合 BM25 与向量两路排序结果。"""
        rrf_k = settings.rrf_k
        fused: dict[int, float] = {}
        chunks: dict[int, RetrievedChunk] = {}

        for rank, hit in enumerate(bm25_hits):
            fused[hit.chunk_id] = fused.get(hit.chunk_id, 0.0) + 1.0 / (rrf_k + rank + 1)
            chunks[hit.chunk_id] = hit

        for rank, hit in enumerate(vector_hits):
            fused[hit.chunk_id] = fused.get(hit.chunk_id, 0.0) + 1.0 / (rrf_k + rank + 1)
            if hit.chunk_id not in chunks:
                chunks[hit.chunk_id] = hit
            else:
                existing = chunks[hit.chunk_id]
                if hit.vector_score is not None:
                    existing.vector_score = hit.vector_score

        ranked_ids = sorted(fused.keys(), key=lambda cid: fused[cid], reverse=True)[:top_k]
        results: list[RetrievedChunk] = []
        for cid in ranked_ids:
            hit = chunks[cid]
            results.append(
                RetrievedChunk(
                    chunk_id=hit.chunk_id,
                    document_id=hit.document_id,
                    doc_title=hit.doc_title,
                    chunk_content=hit.chunk_content,
                    score=fused[cid],
                    bm25_score=hit.bm25_score,
                    vector_score=hit.vector_score,
                )
            )
        return results

    def _attach_markdown(self, hits: list[RetrievedChunk]) -> list[RetrievedChunk]:
        if not hits:
            return []
        doc_ids = list({h.document_id for h in hits})
        md_map = self._load_documents(doc_ids)
        for hit in hits:
            hit.markdown_content = md_map.get(hit.document_id)
        return hits

    def _load_documents(self, document_ids: list[int]) -> dict[int, str]:
        with md_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, markdown_content
                    FROM lol_knowledge_documents
                    WHERE id = ANY(%s)
                    """,
                    (document_ids,),
                )
                rows = cur.fetchall()
        return {r[0]: r[1] for r in rows}

    def format_context(self, chunks: list[RetrievedChunk]) -> str:
        if not chunks:
            return "（知识库未检索到相关内容）"

        parts: list[str] = []
        seen_docs: set[int] = set()
        for i, c in enumerate(chunks, 1):
            score_detail = f"RRF={c.score:.4f}"
            if c.bm25_score is not None:
                score_detail += f", BM25={c.bm25_score:.3f}"
            if c.vector_score is not None:
                score_detail += f", 向量={c.vector_score:.3f}"
            block = [
                f"[片段{i}] 文档《{c.doc_title}》(document_id={c.document_id}, {score_detail})"
            ]
            block.append(c.chunk_content)
            if c.document_id not in seen_docs and c.markdown_content:
                seen_docs.add(c.document_id)
                block.append("\n--- 关联完整 MD 原文（节选） ---")
                excerpt = c.markdown_content[:2000]
                if len(c.markdown_content) > 2000:
                    excerpt += "\n...（原文已截断）"
                block.append(excerpt)
            parts.append("\n".join(block))
        return "\n\n".join(parts)
