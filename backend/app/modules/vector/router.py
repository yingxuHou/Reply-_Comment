from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app.core.db import get_session
from app.modules.kb.service import get_kb
from app.modules.vector.schemas import ReindexResponse, SearchRequest, SearchResponse
from app.modules.vector.service import get_latest_index, reindex_kb, search


router = APIRouter(tags=["vector"])


@router.post("/kbs/{kb_id}/reindex", response_model=ReindexResponse)
def reindex(kb_id: UUID, session: Session = Depends(get_session)):
    kb = get_kb(session, kb_id)
    if not kb:
        raise HTTPException(status_code=404, detail="kb_not_found")
    idx = reindex_kb(session, kb_id=kb_id, kb_version=kb.published_version)
    indexed_chunks = 0
    if idx.dim != 0:
        indexed_chunks = int(session.exec(select_count_vectors(kb_id=kb_id, kb_version=kb.published_version)).one())
    return ReindexResponse(
        kb_id=kb_id,
        kb_version=kb.published_version,
        provider=idx.provider,
        model=idx.model,
        dim=idx.dim,
        indexed_chunks=indexed_chunks,
    )


def select_count_vectors(kb_id: UUID, kb_version: int):
    from sqlmodel import func, select

    from app.modules.vector.models import VectorRecord

    return select(func.count()).select_from(VectorRecord).where(
        (VectorRecord.kb_id == kb_id) & (VectorRecord.kb_version == kb_version)
    )


@router.post("/kbs/{kb_id}/search", response_model=SearchResponse)
def search_kb(kb_id: UUID, payload: SearchRequest, session: Session = Depends(get_session)):
    kb = get_kb(session, kb_id)
    if not kb:
        raise HTTPException(status_code=404, detail="kb_not_found")
    latency_ms, hits = search(session, kb_id=kb_id, query=payload.query, top_k=payload.top_k, kb_version=payload.kb_version)
    idx = get_latest_index(session, kb_id, payload.kb_version)
    kb_version = payload.kb_version if payload.kb_version is not None else (idx.kb_version if idx else 0)
    return SearchResponse(
        kb_id=kb_id,
        kb_version=kb_version,
        query=payload.query,
        hits=hits,
        latency_ms=latency_ms,
        created_at=datetime_utc(),
    )


def datetime_utc():
    from datetime import datetime

    return datetime.utcnow()
