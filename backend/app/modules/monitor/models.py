from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel


class ReplyEvent(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    kb_id: UUID = Field(index=True)
    kb_version: int = Field(index=True)
    comment_id: str = Field(index=True)
    note_id: str = Field(index=True)
    intent: str = Field(index=True)
    lead_score: int = Field(default=0, index=True)
    lead_level: str = Field(default="low", index=True)
    latency_ms: int = Field(default=0, index=True)
    llm_used: bool = Field(default=False, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    meta_json: str = ""

