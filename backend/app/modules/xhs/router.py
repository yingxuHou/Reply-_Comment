from __future__ import annotations

from typing import List

from fastapi import APIRouter, HTTPException, Query

from app.modules.xhs import service
from app.modules.xhs.schemas import AnalyzeNoteResponse, ListCommentsResponse, ListNotesResponse, XhsComment, XhsNote


router = APIRouter(tags=["xhs"])


@router.get("/xhs/notes", response_model=ListNotesResponse)
def list_notes(q: str = ""):
    try:
        notes, source = service.list_notes(q=q)
        return ListNotesResponse(notes=[XhsNote(**n) for n in notes], total=len(notes), source_files=source)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="missing_xhs_json_files")


@router.get("/xhs/notes/{note_id}/comments", response_model=ListCommentsResponse)
def list_comments(
    note_id: str,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    sort: str = Query(default="like", pattern="^(like|time)$"),
    q: str = "",
):
    try:
        rows, total = service.list_comments(note_id=note_id, offset=offset, limit=limit, sort=sort, q=q)
        return ListCommentsResponse(
            note_id=note_id,
            total=total,
            offset=offset,
            limit=limit,
            sort=sort,
            q=q,
            comments=[XhsComment(**c) for c in rows],
        )
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="missing_xhs_json_files")


@router.get("/xhs/notes/{note_id}/analyze", response_model=AnalyzeNoteResponse)
def analyze_note(note_id: str, max_samples: int = Query(default=500, ge=50, le=2000)):
    try:
        r = service.analyze_note(note_id=note_id, max_samples=max_samples)
        return AnalyzeNoteResponse(
            note_id=r["note_id"],
            total_comments=r["total_comments"],
            top_comments=[XhsComment(**c) for c in r["top_comments"]],
            intent_counts=r["intent_counts"],
            generated_at=r["generated_at"],
        )
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="missing_xhs_json_files")

