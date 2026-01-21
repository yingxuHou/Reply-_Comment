from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel


class KnowledgeBase(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    slug: str = Field(index=True, unique=True)
    name: str
    description: str = ""
    published_version: int = Field(default=0, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    updated_at: datetime = Field(default_factory=datetime.utcnow, index=True)


class KnowledgeItem(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    kb_id: UUID = Field(foreign_key="knowledgebase.id", index=True)
    key: str = Field(index=True)
    title: str
    tags: str = ""
    is_active: bool = Field(default=True, index=True)
    current_revision_id: Optional[UUID] = Field(default=None, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    updated_at: datetime = Field(default_factory=datetime.utcnow, index=True)


class KnowledgeItemRevision(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    item_id: UUID = Field(foreign_key="knowledgeitem.id", index=True)
    revision: int = Field(index=True)
    content: str
    source: str = ""
    status: str = Field(default="draft", index=True)
    published_version: Optional[int] = Field(default=None, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)


class KnowledgeChunk(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    revision_id: UUID = Field(foreign_key="knowledgeitemrevision.id", index=True)
    chunk_index: int = Field(index=True)
    content: str
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)

