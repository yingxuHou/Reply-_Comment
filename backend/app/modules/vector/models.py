from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel


class VectorIndex(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    kb_id: UUID = Field(index=True)
    kb_version: int = Field(index=True)
    provider: str = Field(index=True)
    model: str = Field(index=True)
    dim: int
    index_path: str
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)


class VectorRecord(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    kb_id: UUID = Field(index=True)
    kb_version: int = Field(index=True)
    vector_pos: int = Field(index=True)
    chunk_id: UUID = Field(index=True)
    revision_id: UUID = Field(index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)


class VectorQueryLog(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    kb_id: UUID = Field(index=True)
    kb_version: int = Field(index=True)
    query: str
    top_k: int
    provider: str = Field(index=True)
    model: str = Field(index=True)
    latency_ms: int = Field(default=0, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    meta_json: str = ""

