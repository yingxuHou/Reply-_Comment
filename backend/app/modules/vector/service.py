from __future__ import annotations

import os
import time
from datetime import datetime
from typing import List, Optional
from uuid import UUID

import numpy as np
from rapidfuzz import fuzz
from sqlmodel import Session, col, delete, select

from app.core.config import settings
from app.modules.kb.models import KnowledgeChunk, KnowledgeItemRevision
from app.modules.kb.service import iter_current_chunks
from app.modules.vector.embedding import get_embedding_client
from app.modules.vector.faiss_store import FaissVectorStore
from app.modules.vector.models import VectorIndex, VectorQueryLog, VectorRecord


def _index_dir(kb_id: UUID, kb_version: int) -> str:
    return os.path.join(settings.vector_dir, str(kb_id), str(kb_version))


def _index_path(kb_id: UUID, kb_version: int) -> str:
    return os.path.join(_index_dir(kb_id, kb_version), "index.faiss")


def _lexical_score(query: str, text: str) -> float:
    if not query or not text:
        return 0.0
    return float(fuzz.partial_ratio(query, text)) / 100.0


def _hybrid_score(vec_score: float, lex_score: float) -> float:
    return 0.75 * float(vec_score) + 0.25 * float(lex_score)


def get_latest_index(session: Session, kb_id: UUID, kb_version: Optional[int]) -> Optional[VectorIndex]:
    stmt = select(VectorIndex).where(VectorIndex.kb_id == kb_id)
    if kb_version is not None:
        stmt = stmt.where(VectorIndex.kb_version == kb_version)
    stmt = stmt.order_by(VectorIndex.created_at.desc())
    return session.exec(stmt).first()


def reindex_kb(session: Session, kb_id: UUID, kb_version: int) -> VectorIndex:
    embedder = get_embedding_client()

    chunks = list(iter_current_chunks(session, kb_id))
    texts = [ch.content for ch in chunks]
    if not texts:
        session.exec(delete(VectorIndex).where((VectorIndex.kb_id == kb_id) & (VectorIndex.kb_version == kb_version)))
        session.exec(delete(VectorRecord).where((VectorRecord.kb_id == kb_id) & (VectorRecord.kb_version == kb_version)))
        session.commit()
        empty_index = VectorIndex(
            kb_id=kb_id,
            kb_version=kb_version,
            provider=embedder.provider,
            model=embedder.model,
            dim=0,
            index_path=_index_path(kb_id, kb_version),
        )
        session.add(empty_index)
        session.commit()
        session.refresh(empty_index)
        return empty_index

    vectors = embedder.embed(texts)
    dim = int(vectors.shape[1])
    store = FaissVectorStore(dim=dim)
    store.add(vectors)

    index_path = _index_path(kb_id, kb_version)
    store.save(index_path)

    session.exec(delete(VectorIndex).where((VectorIndex.kb_id == kb_id) & (VectorIndex.kb_version == kb_version)))
    session.exec(delete(VectorRecord).where((VectorRecord.kb_id == kb_id) & (VectorRecord.kb_version == kb_version)))
    session.commit()

    idx = VectorIndex(
        kb_id=kb_id,
        kb_version=kb_version,
        provider=embedder.provider,
        model=embedder.model,
        dim=dim,
        index_path=index_path,
    )
    session.add(idx)
    session.commit()
    session.refresh(idx)

    for pos, ch in enumerate(chunks):
        session.add(
            VectorRecord(
                kb_id=kb_id,
                kb_version=kb_version,
                vector_pos=pos,
                chunk_id=ch.id,
                revision_id=ch.revision_id,
            )
        )
    session.commit()
    return idx


def search(
    session: Session,
    kb_id: UUID,
    query: str,
    top_k: int,
    kb_version: Optional[int],
) -> tuple[int, List[dict]]:
    started = time.time()
    embedder = get_embedding_client()
    idx = get_latest_index(session, kb_id, kb_version)
    if not idx or idx.dim == 0:
        latency_ms = int((time.time() - started) * 1000)
        _log_query(session, kb_id, kb_version or 0, query, top_k, embedder, latency_ms, meta_json='{"empty":true}')
        return latency_ms, []

    store = FaissVectorStore.load(idx.index_path)
    qv = embedder.embed([query])[0]
    hits = store.search(qv, top_k=top_k * 5)

    records = session.exec(
        select(VectorRecord).where(
            (VectorRecord.kb_id == kb_id) & (VectorRecord.kb_version == idx.kb_version) & col(VectorRecord.vector_pos).in_([h.pos for h in hits])
        )
    ).all()
    record_by_pos = {r.vector_pos: r for r in records}

    chunk_ids = [record_by_pos[h.pos].chunk_id for h in hits if h.pos in record_by_pos]
    chunks = session.exec(select(KnowledgeChunk).where(col(KnowledgeChunk.id).in_(chunk_ids))).all()
    chunk_by_id = {c.id: c for c in chunks}

    scored: List[dict] = []
    for h in hits:
        rec = record_by_pos.get(h.pos)
        if not rec:
            continue
        ch = chunk_by_id.get(rec.chunk_id)
        if not ch:
            continue
        lex = _lexical_score(query, ch.content)
        score = _hybrid_score(h.score, lex)
        scored.append(
            {
                "chunk_id": ch.id,
                "revision_id": ch.revision_id,
                "score": score,
                "content": ch.content,
            }
        )
    scored.sort(key=lambda x: x["score"], reverse=True)
    scored = scored[:top_k]

    latency_ms = int((time.time() - started) * 1000)
    _log_query(session, kb_id, idx.kb_version, query, top_k, embedder, latency_ms, meta_json="")
    return latency_ms, scored


def _log_query(session: Session, kb_id: UUID, kb_version: int, query: str, top_k: int, embedder, latency_ms: int, meta_json: str) -> None:
    ql = VectorQueryLog(
        kb_id=kb_id,
        kb_version=kb_version,
        query=query,
        top_k=top_k,
        provider=embedder.provider,
        model=embedder.model,
        latency_ms=latency_ms,
        created_at=datetime.utcnow(),
        meta_json=meta_json,
    )
    session.add(ql)
    session.commit()

