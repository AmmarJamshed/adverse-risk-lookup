"""Embedding service — BGE / sentence-transformers with FAISS fallback index."""

from __future__ import annotations

import hashlib
from functools import lru_cache
from pathlib import Path
from typing import Optional

import numpy as np

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger("embeddings")


class EmbeddingService:
    def __init__(self) -> None:
        settings = get_settings()
        self.model_name = settings.embedding_model
        self.dim = settings.embedding_dim
        self.use_faiss = settings.use_faiss_fallback
        self._model = None
        self._faiss_index = None
        self._faiss_ids: list[str] = []
        self._index_path = Path("data/faiss_index")
        self._index_path.mkdir(parents=True, exist_ok=True)

    def _load_model(self):
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer

                logger.info("loading_embedding_model", model=self.model_name)
                self._model = SentenceTransformer(self.model_name)
            except Exception as exc:
                logger.warning("embedding_model_unavailable", error=str(exc))
                self._model = False
        return self._model

    def embed(self, text: str) -> list[float]:
        text = (text or "").strip()
        if not text:
            return [0.0] * self.dim
        model = self._load_model()
        if model:
            vec = model.encode(text, normalize_embeddings=True)
            return vec.astype(float).tolist()
        # Deterministic hash-based fallback for offline / boot without model weights
        return self._hash_embed(text)

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        model = self._load_model()
        cleaned = [(t or "").strip() or " " for t in texts]
        if model:
            vecs = model.encode(cleaned, normalize_embeddings=True, batch_size=32)
            return [v.astype(float).tolist() for v in vecs]
        return [self._hash_embed(t) for t in cleaned]

    def _hash_embed(self, text: str) -> list[float]:
        digest = hashlib.sha512(text.encode("utf-8")).digest()
        rng = np.random.default_rng(int.from_bytes(digest[:8], "big"))
        vec = rng.standard_normal(self.dim)
        vec = vec / (np.linalg.norm(vec) + 1e-9)
        return vec.astype(float).tolist()

    @staticmethod
    def cosine(a: list[float], b: list[float]) -> float:
        va = np.array(a, dtype=float)
        vb = np.array(b, dtype=float)
        denom = (np.linalg.norm(va) * np.linalg.norm(vb)) + 1e-9
        return float(np.dot(va, vb) / denom)

    def add_to_faiss(self, item_id: str, vector: list[float]) -> None:
        if not self.use_faiss:
            return
        try:
            import faiss
        except ImportError:
            return
        vec = np.array([vector], dtype="float32")
        if self._faiss_index is None:
            self._faiss_index = faiss.IndexFlatIP(self.dim)
        self._faiss_index.add(vec)
        self._faiss_ids.append(item_id)

    def search_faiss(self, vector: list[float], top_k: int = 10) -> list[tuple[str, float]]:
        if not self.use_faiss or self._faiss_index is None or not self._faiss_ids:
            return []
        try:
            import faiss  # noqa: F401
        except ImportError:
            return []
        q = np.array([vector], dtype="float32")
        scores, indices = self._faiss_index.search(q, min(top_k, len(self._faiss_ids)))
        results: list[tuple[str, float]] = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0:
                continue
            results.append((self._faiss_ids[idx], float(score)))
        return results


_embedding: Optional[EmbeddingService] = None


def get_embeddings() -> EmbeddingService:
    global _embedding
    if _embedding is None:
        _embedding = EmbeddingService()
    return _embedding


@lru_cache
def warm_embeddings() -> bool:
    svc = get_embeddings()
    svc.embed("warmup")
    return True
