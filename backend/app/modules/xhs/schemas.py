from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class XhsNote(BaseModel):
    note_id: str
    type: str = ""
    title: str = ""
    desc: str = ""
    tag_list: str = ""
    nickname: str = ""
    liked_count: str = ""
    collected_count: str = ""
    comment_count: str = ""
    share_count: str = ""
    time: Optional[int] = None
    note_url: str = ""
    source_keyword: str = ""


class XhsComment(BaseModel):
    comment_id: str
    note_id: str
    content: str
    like_count: str = ""
    create_time: Optional[int] = None
    nickname: str = ""
    user_id: str = ""
    ip_location: str = ""
    sub_comment_count: str = ""
    parent_comment_id: str = ""


class ListNotesResponse(BaseModel):
    notes: List[XhsNote]
    total: int
    source_files: Dict[str, str]


class ListCommentsResponse(BaseModel):
    note_id: str
    total: int
    offset: int
    limit: int
    sort: str
    q: str = ""
    comments: List[XhsComment]


class AnalyzeNoteResponse(BaseModel):
    note_id: str
    total_comments: int
    top_comments: List[XhsComment]
    intent_counts: Dict[str, int]
    generated_at: datetime

