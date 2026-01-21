from __future__ import annotations

import os
from dataclasses import dataclass
from typing import List

import numpy as np

try:
    import faiss  # type: ignore

    _HAS_FAISS = True
except Exception:
    faiss = None  # type: ignore
    _HAS_FAISS = False


@dataclass
class SearchHit:
    pos: int
    score: float


class FaissVectorStore:
    def __init__(self, dim: int):
        self.dim = dim
        if _HAS_FAISS:
            self._index = faiss.IndexFlatIP(dim)  # type: ignore[attr-defined]
        else:
            self._vectors = np.zeros((0, dim), dtype=np.float32)

    @property
    def size(self) -> int:
        if _HAS_FAISS:
            return int(self._index.ntotal)
        return int(self._vectors.shape[0])

    def add(self, vectors: np.ndarray) -> None:
        if vectors.dtype != np.float32:
            vectors = vectors.astype(np.float32)
        if vectors.ndim != 2 or vectors.shape[1] != self.dim:
            raise ValueError("invalid_vectors_shape")
        if _HAS_FAISS:
            self._index.add(vectors)
        else:
            if self._vectors.size == 0:
                self._vectors = vectors
            else:
                self._vectors = np.concatenate([self._vectors, vectors], axis=0)

    def search(self, query_vector: np.ndarray, top_k: int) -> List[SearchHit]:
        if query_vector.ndim == 1:
            query_vector = query_vector.reshape(1, -1)
        if query_vector.dtype != np.float32:
            query_vector = query_vector.astype(np.float32)
        if _HAS_FAISS:
            scores, idxs = self._index.search(query_vector, top_k)
            hits: List[SearchHit] = []
            for pos, score in zip(idxs[0].tolist(), scores[0].tolist()):
                if pos < 0:
                    continue
                hits.append(SearchHit(pos=int(pos), score=float(score)))
            return hits

        if self._vectors.size == 0:
            return []
        scores = (self._vectors @ query_vector[0]).astype(np.float32)
        k = min(int(top_k), int(scores.shape[0]))
        if k <= 0:
            return []
        idxs = np.argpartition(-scores, kth=k - 1)[:k]
        idxs = idxs[np.argsort(-scores[idxs])]
        return [SearchHit(pos=int(i), score=float(scores[int(i)])) for i in idxs]

    def save(self, index_path: str) -> None:
        os.makedirs(os.path.dirname(os.path.abspath(index_path)), exist_ok=True)
        if _HAS_FAISS:
            faiss.write_index(self._index, index_path)  # type: ignore[attr-defined]
            return
        np.save(index_path + ".npy", self._vectors)

    @staticmethod
    def load(index_path: str) -> "FaissVectorStore":
        if _HAS_FAISS and os.path.exists(index_path):
            index = faiss.read_index(index_path)  # type: ignore[attr-defined]
            dim = int(index.d)
            store = FaissVectorStore(dim=dim)
            store._index = index
            return store

        npy_path = index_path + ".npy"
        if not os.path.exists(npy_path):
            raise FileNotFoundError("index_file_not_found")
        vectors = np.load(npy_path).astype(np.float32)
        store = FaissVectorStore(dim=int(vectors.shape[1]))
        store._vectors = vectors
        return store
