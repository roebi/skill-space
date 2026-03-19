"""Embedder — thin wrapper around sentence-transformers."""

from __future__ import annotations

from functools import lru_cache


@lru_cache(maxsize=1)
def _model():
    from sentence_transformers import SentenceTransformer  # type: ignore[import-untyped]

    return SentenceTransformer("all-MiniLM-L6-v2")  # 80MB, 384-dim, offline-capable


class Embedder:
    def encode(self, text: str) -> list[float]:
        return _model().encode(text, normalize_embeddings=True).tolist()
