from __future__ import annotations

from functools import lru_cache

from config.settings import settings


@lru_cache(maxsize=1)
def _load_vectorizer():
    from sklearn.feature_extraction.text import HashingVectorizer

    return HashingVectorizer(
        n_features=settings.embedding_dim,
        alternate_sign=False,
        norm="l2",
        analyzer="char",
        ngram_range=(1, 2),
    )


class Embedder:
    """本地哈希向量（512 维），用于混合检索中的向量路，无需 Hugging Face。"""

    def embed_query(self, text: str) -> list[float]:
        return self.embed_texts([text])[0]

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        matrix = _load_vectorizer().transform(texts)
        return [row.toarray().flatten().tolist() for row in matrix]
