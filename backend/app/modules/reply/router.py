from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app.core.db import get_session
from app.modules.kb.service import get_kb
from app.modules.reply.schemas import ReplyRequest, ReplyResponse
from app.modules.reply.service import suggest_reply


router = APIRouter(tags=["reply"])


@router.post("/reply/suggest", response_model=ReplyResponse)
def reply_suggest(payload: ReplyRequest, session: Session = Depends(get_session)):
    kb = get_kb(session, payload.kb_id)
    if not kb:
        raise HTTPException(status_code=404, detail="kb_not_found")
    result = suggest_reply(
        session=session,
        kb_id=payload.kb_id,
        comment_id=payload.comment.comment_id,
        note_id=payload.comment.note_id,
        comment_text=payload.comment.content,
        note_title=payload.comment.note_title,
        note_desc=payload.comment.note_desc,
        top_k=payload.top_k,
        kb_version=payload.kb_version,
        inject_sales=payload.inject_sales,
    )
    return result
