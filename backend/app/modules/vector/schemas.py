from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ReindexResponse(BaseModel):
    kb_id: UUID
    kb_version: int
    provider: str
    model: str
    dim: int
    indexed_chunks: int


class SearchRequest(BaseModel):
    query: str = Field(min_length=1)
    top_k: int = Field(default=5, ge=1, le=50)
    kb_version: Optional[int] = None


class SearchHitRead(BaseModel):
    chunk_id: UUID
    revision_id: UUID
    score: float
    content: str


class SearchResponse(BaseModel):
    kb_id: UUID
    kb_version: int
    query: str
    hits: List[SearchHitRead]
    latency_ms: int
    created_at: datetime
