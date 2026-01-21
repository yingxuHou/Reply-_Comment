from __future__ import annotations

import re
from datetime import datetime
from typing import Iterable, List, Optional
from uuid import UUID

from sqlmodel import Session, col, select

from app.core.config import settings
from app.modules.kb.models import KnowledgeBase, KnowledgeChunk, KnowledgeItem, KnowledgeItemRevision


_PARA_SPLIT_RE = re.compile(r"\n{2,}")


def _chunk_text(content: str) -> List[str]:
    parts = [p.strip() for p in _PARA_SPLIT_RE.split(content.strip())]
    parts = [p for p in parts if p]
    if not parts:
        return []
    return parts


def ensure_default_kb(session: Session) -> KnowledgeBase:
    kb = session.exec(select(KnowledgeBase).where(KnowledgeBase.slug == settings.default_kb_slug)).first()
    if kb:
        return kb
    kb = KnowledgeBase(slug=settings.default_kb_slug, name="默认知识库", description="系统默认知识库")
    session.add(kb)
    session.commit()
    session.refresh(kb)
    return kb


def list_kbs(session: Session) -> List[KnowledgeBase]:
    return list(session.exec(select(KnowledgeBase).order_by(KnowledgeBase.created_at.desc())))


def create_kb(session: Session, slug: str, name: str, description: str) -> KnowledgeBase:
    existing = session.exec(select(KnowledgeBase).where(KnowledgeBase.slug == slug)).first()
    if existing:
        raise ValueError("kb_slug_exists")
    kb = KnowledgeBase(slug=slug, name=name, description=description)
    session.add(kb)
    session.commit()
    session.refresh(kb)
    return kb


def get_kb(session: Session, kb_id: UUID) -> Optional[KnowledgeBase]:
    return session.get(KnowledgeBase, kb_id)


def get_kb_by_slug(session: Session, slug: str) -> Optional[KnowledgeBase]:
    return session.exec(select(KnowledgeBase).where(KnowledgeBase.slug == slug)).first()


def list_items(session: Session, kb_id: UUID, is_active: Optional[bool]) -> List[KnowledgeItem]:
    stmt = select(KnowledgeItem).where(KnowledgeItem.kb_id == kb_id)
    if is_active is not None:
        stmt = stmt.where(KnowledgeItem.is_active == is_active)
    return list(session.exec(stmt.order_by(KnowledgeItem.updated_at.desc())))


def create_item(
    session: Session,
    kb_id: UUID,
    key: str,
    title: str,
    tags: str,
    content: str,
    source: str,
) -> KnowledgeItem:
    existing = session.exec(
        select(KnowledgeItem).where((KnowledgeItem.kb_id == kb_id) & (KnowledgeItem.key == key))
    ).first()
    if existing:
        raise ValueError("item_key_exists")
    item = KnowledgeItem(kb_id=kb_id, key=key, title=title, tags=tags)
    session.add(item)
    session.commit()
    session.refresh(item)

    rev = KnowledgeItemRevision(item_id=item.id, revision=1, content=content, source=source, status="published")
    session.add(rev)
    session.commit()
    session.refresh(rev)

    item.current_revision_id = rev.id
    item.updated_at = datetime.utcnow()
    session.add(item)
    session.commit()

    _rebuild_chunks_for_revision(session, rev)
    return item


def update_item(session: Session, item_id: UUID, title: Optional[str], tags: Optional[str], is_active: Optional[bool]) -> KnowledgeItem:
    item = session.get(KnowledgeItem, item_id)
    if not item:
        raise ValueError("item_not_found")
    if title is not None:
        item.title = title
    if tags is not None:
        item.tags = tags
    if is_active is not None:
        item.is_active = is_active
    item.updated_at = datetime.utcnow()
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


def get_item(session: Session, item_id: UUID) -> Optional[KnowledgeItem]:
    return session.get(KnowledgeItem, item_id)


def list_revisions(session: Session, item_id: UUID) -> List[KnowledgeItemRevision]:
    return list(
        session.exec(
            select(KnowledgeItemRevision)
            .where(KnowledgeItemRevision.item_id == item_id)
            .order_by(KnowledgeItemRevision.revision.desc())
        )
    )


def create_revision(session: Session, item_id: UUID, content: str, source: str) -> KnowledgeItemRevision:
    item = session.get(KnowledgeItem, item_id)
    if not item:
        raise ValueError("item_not_found")
    last_rev = session.exec(
        select(KnowledgeItemRevision.revision)
        .where(KnowledgeItemRevision.item_id == item_id)
        .order_by(KnowledgeItemRevision.revision.desc())
    ).first()
    next_rev = int(last_rev or 0) + 1
    rev = KnowledgeItemRevision(item_id=item_id, revision=next_rev, content=content, source=source, status="draft")
    session.add(rev)
    session.commit()
    session.refresh(rev)
    _rebuild_chunks_for_revision(session, rev)
    return rev


def publish_revision(session: Session, item_id: UUID, revision_id: UUID) -> KnowledgeItem:
    item = session.get(KnowledgeItem, item_id)
    if not item:
        raise ValueError("item_not_found")
    rev = session.get(KnowledgeItemRevision, revision_id)
    if not rev or rev.item_id != item_id:
        raise ValueError("revision_not_found")
    rev.status = "published"
    session.add(rev)
    session.commit()

    item.current_revision_id = rev.id
    item.updated_at = datetime.utcnow()
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


def publish_kb(session: Session, kb_id: UUID) -> int:
    kb = session.get(KnowledgeBase, kb_id)
    if not kb:
        raise ValueError("kb_not_found")
    next_version = kb.published_version + 1
    kb.published_version = next_version
    kb.updated_at = datetime.utcnow()
    session.add(kb)
    session.commit()

    items = session.exec(select(KnowledgeItem).where(KnowledgeItem.kb_id == kb_id)).all()
    current_rev_ids = [it.current_revision_id for it in items if it.current_revision_id]
    if current_rev_ids:
        revs = session.exec(select(KnowledgeItemRevision).where(col(KnowledgeItemRevision.id).in_(current_rev_ids))).all()
        for r in revs:
            r.published_version = next_version
            session.add(r)
        session.commit()
    return next_version


def iter_current_chunks(session: Session, kb_id: UUID) -> Iterable[KnowledgeChunk]:
    items = session.exec(select(KnowledgeItem).where(KnowledgeItem.kb_id == kb_id)).all()
    rev_ids = [it.current_revision_id for it in items if it.is_active and it.current_revision_id]
    if not rev_ids:
        return []
    stmt = select(KnowledgeChunk).where(col(KnowledgeChunk.revision_id).in_(rev_ids)).order_by(KnowledgeChunk.created_at.asc())
    return session.exec(stmt)


def _rebuild_chunks_for_revision(session: Session, revision: KnowledgeItemRevision) -> None:
    existing = session.exec(select(KnowledgeChunk).where(KnowledgeChunk.revision_id == revision.id)).all()
    for ch in existing:
        session.delete(ch)
    session.commit()
    chunks = _chunk_text(revision.content)
    for idx, text in enumerate(chunks):
        session.add(KnowledgeChunk(revision_id=revision.id, chunk_index=idx, content=text))
    session.commit()

