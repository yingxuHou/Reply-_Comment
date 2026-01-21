from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class KnowledgeBaseCreate(BaseModel):
    slug: str = Field(min_length=1)
    name: str = Field(min_length=1)
    description: str = ""


class KnowledgeBaseRead(BaseModel):
    id: UUID
    slug: str
    name: str
    description: str
    published_version: int
    created_at: datetime
    updated_at: datetime


class KnowledgeItemCreate(BaseModel):
    key: str = Field(min_length=1)
    title: str = Field(min_length=1)
    tags: str = ""
    content: str = Field(min_length=1)
    source: str = ""


class KnowledgeItemUpdate(BaseModel):
    title: Optional[str] = None
    tags: Optional[str] = None
    is_active: Optional[bool] = None


class KnowledgeItemRead(BaseModel):
    id: UUID
    kb_id: UUID
    key: str
    title: str
    tags: str
    is_active: bool
    current_revision_id: Optional[UUID]
    created_at: datetime
    updated_at: datetime


class KnowledgeRevisionCreate(BaseModel):
    content: str = Field(min_length=1)
    source: str = ""


class KnowledgeRevisionRead(BaseModel):
    id: UUID
    item_id: UUID
    revision: int
    content: str
    source: str
    status: str
    published_version: Optional[int]
    created_at: datetime


class PublishKnowledgeBaseResponse(BaseModel):
    kb_id: UUID
    published_version: int

