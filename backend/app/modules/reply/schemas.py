from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class CommentInput(BaseModel):
    comment_id: str = ""
    note_id: str = ""
    note_title: str = ""
    note_desc: str = ""
    user_id: str = ""
    nickname: str = ""
    content: str = Field(default="", description="评论内容")


class ReplyRequest(BaseModel):
    kb_id: UUID
    comment: CommentInput
    top_k: int = Field(default=5, ge=1, le=20)
    kb_version: Optional[int] = None
    inject_sales: bool = True


class UsedKnowledge(BaseModel):
    chunk_id: UUID
    revision_id: UUID
    score: float
    content: str


class ReplyResponse(BaseModel):
    kb_id: UUID
    kb_version: int
    intent: str
    intent_confidence: float
    reply: str
    used_knowledge: List[UsedKnowledge]
    lead_score: int
    lead_level: str
    lead_signals: List[str]
    next_actions: List[str]
    latency_ms: int
    created_at: datetime
    meta_json: str = ""
