from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class MonitorOverviewRequest(BaseModel):
    since: Optional[datetime] = None
    until: Optional[datetime] = None


class MonitorOverviewResponse(BaseModel):
    total_replies: int
    avg_latency_ms: int
    llm_rate: float
    lead_high: int
    lead_medium: int
    lead_low: int
    intent_counts: Dict[str, int]
    generated_at: datetime


class MonitorNoteTopLeadsRequest(BaseModel):
    note_id: str = Field(min_length=1)
    limit: int = Field(default=20, ge=1, le=200)


class LeadRow(BaseModel):
    comment_id: str
    intent: str
    lead_score: int
    lead_level: str
    latency_ms: int
    created_at: datetime


class MonitorNoteTopLeadsResponse(BaseModel):
    note_id: str
    rows: List[LeadRow]
    generated_at: datetime

