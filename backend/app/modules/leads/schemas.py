from __future__ import annotations

from typing import Dict, List

from pydantic import BaseModel, Field


class LeadScoreRequest(BaseModel):
    text: str = Field(min_length=1)


class LeadScoreResponse(BaseModel):
    score: int
    level: str
    signals: List[str]
    next_actions: List[str]
    features: Dict[str, int]

