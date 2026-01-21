from __future__ import annotations

import hashlib
import os
import time
from dataclasses import dataclass
from typing import List

import httpx
import numpy as np

from app.core.config import settings


class EmbeddingClient:
    provider: str
    model: str

    def embed(self, texts: List[str]) -> np.ndarray:
        raise NotImplementedError


def _l2_normalize(vectors: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    norms = np.clip(norms, 1e-12, None)
    return vectors / norms


@dataclass
class MockHashEmbeddingClient(EmbeddingClient):
    dim: int = 384
    provider: str = "mock"
    model: str = "hash-v1"

    def embed(self, texts: List[str]) -> np.ndarray:
        vectors = np.zeros((len(texts), self.dim), dtype=np.float32)
        for i, t in enumerate(texts):
            h = hashlib.sha256(t.encode("utf-8", errors="ignore")).digest()
            seed = int.from_bytes(h[:8], "big", signed=False)
            rng = np.random.default_rng(seed)
            vectors[i] = rng.standard_normal(self.dim).astype(np.float32)
        return _l2_normalize(vectors)


@dataclass
class GLMEmbeddingClient(EmbeddingClient):
    api_key: str
    base_url: str
    model: str
    provider: str = "glm"
    timeout_s: float = 8.0

    def embed(self, texts: List[str]) -> np.ndarray:
        started = time.time()
        headers = {"Authorization": f"Bearer {self.api_key}"}
        payload = {"model": self.model, "input": texts}
        url = self.base_url.rstrip("/") + "/embeddings"
        with httpx.Client(timeout=self.timeout_s) as client:
            resp = client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
        vectors = [row["embedding"] for row in data.get("data", [])]
        arr = np.asarray(vectors, dtype=np.float32)
        if arr.ndim != 2 or arr.shape[0] != len(texts):
            raise RuntimeError("invalid_embedding_response")
        arr = _l2_normalize(arr)
        _ = started
        return arr


def get_embedding_client() -> EmbeddingClient:
    api_key = (settings.glm_api_key or "").strip()
    if api_key:
        return GLMEmbeddingClient(api_key=api_key, base_url=settings.glm_base_url, model=settings.glm_embed_model)
    dim_env = os.getenv("MOCK_EMBED_DIM", "").strip()
    dim = int(dim_env) if dim_env.isdigit() else 384
    return MockHashEmbeddingClient(dim=dim)

