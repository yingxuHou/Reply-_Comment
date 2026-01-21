from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from typing import List, Optional

from app.core.db import get_session
from app.modules.kb import service
from app.modules.kb.schemas import (
    KnowledgeBaseCreate,
    KnowledgeBaseRead,
    KnowledgeItemCreate,
    KnowledgeItemRead,
    KnowledgeItemUpdate,
    KnowledgeRevisionCreate,
    KnowledgeRevisionRead,
    PublishKnowledgeBaseResponse,
)


router = APIRouter(tags=["kb"])


@router.get("/kbs", response_model=List[KnowledgeBaseRead])
def list_kbs(session: Session = Depends(get_session)):
    service.ensure_default_kb(session)
    return service.list_kbs(session)


@router.post("/kbs", response_model=KnowledgeBaseRead)
def create_kb(payload: KnowledgeBaseCreate, session: Session = Depends(get_session)):
    try:
        return service.create_kb(session, slug=payload.slug, name=payload.name, description=payload.description)
    except ValueError as e:
        if str(e) == "kb_slug_exists":
            raise HTTPException(status_code=409, detail="kb_slug_exists")
        raise


@router.post("/kbs/{kb_id}/publish", response_model=PublishKnowledgeBaseResponse)
def publish_kb(kb_id: UUID, session: Session = Depends(get_session)):
    try:
        v = service.publish_kb(session, kb_id)
        return PublishKnowledgeBaseResponse(kb_id=kb_id, published_version=v)
    except ValueError as e:
        if str(e) == "kb_not_found":
            raise HTTPException(status_code=404, detail="kb_not_found")
        raise


@router.get("/kbs/{kb_id}/items", response_model=List[KnowledgeItemRead])
def list_items(kb_id: UUID, is_active: Optional[bool] = None, session: Session = Depends(get_session)):
    if not service.get_kb(session, kb_id):
        raise HTTPException(status_code=404, detail="kb_not_found")
    return service.list_items(session, kb_id=kb_id, is_active=is_active)


@router.post("/kbs/{kb_id}/items", response_model=KnowledgeItemRead)
def create_item(kb_id: UUID, payload: KnowledgeItemCreate, session: Session = Depends(get_session)):
    if not service.get_kb(session, kb_id):
        raise HTTPException(status_code=404, detail="kb_not_found")
    try:
        return service.create_item(
            session,
            kb_id=kb_id,
            key=payload.key,
            title=payload.title,
            tags=payload.tags,
            content=payload.content,
            source=payload.source,
        )
    except ValueError as e:
        if str(e) == "item_key_exists":
            raise HTTPException(status_code=409, detail="item_key_exists")
        raise


@router.get("/items/{item_id}", response_model=KnowledgeItemRead)
def get_item(item_id: UUID, session: Session = Depends(get_session)):
    item = service.get_item(session, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="item_not_found")
    return item


@router.patch("/items/{item_id}", response_model=KnowledgeItemRead)
def update_item(item_id: UUID, payload: KnowledgeItemUpdate, session: Session = Depends(get_session)):
    try:
        return service.update_item(session, item_id, title=payload.title, tags=payload.tags, is_active=payload.is_active)
    except ValueError as e:
        if str(e) == "item_not_found":
            raise HTTPException(status_code=404, detail="item_not_found")
        raise


@router.get("/items/{item_id}/revisions", response_model=List[KnowledgeRevisionRead])
def list_revisions(item_id: UUID, session: Session = Depends(get_session)):
    item = service.get_item(session, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="item_not_found")
    return service.list_revisions(session, item_id)


@router.post("/items/{item_id}/revisions", response_model=KnowledgeRevisionRead)
def create_revision(item_id: UUID, payload: KnowledgeRevisionCreate, session: Session = Depends(get_session)):
    try:
        return service.create_revision(session, item_id=item_id, content=payload.content, source=payload.source)
    except ValueError as e:
        if str(e) == "item_not_found":
            raise HTTPException(status_code=404, detail="item_not_found")
        raise


@router.post("/items/{item_id}/revisions/{revision_id}/publish", response_model=KnowledgeItemRead)
def publish_revision(item_id: UUID, revision_id: UUID, session: Session = Depends(get_session)):
    try:
        return service.publish_revision(session, item_id=item_id, revision_id=revision_id)
    except ValueError as e:
        if str(e) == "item_not_found":
            raise HTTPException(status_code=404, detail="item_not_found")
        if str(e) == "revision_not_found":
            raise HTTPException(status_code=404, detail="revision_not_found")
        raise

