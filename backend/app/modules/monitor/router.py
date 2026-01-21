from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.core.db import get_session
from app.modules.monitor.schemas import (
    MonitorNoteTopLeadsRequest,
    MonitorNoteTopLeadsResponse,
    MonitorOverviewRequest,
    MonitorOverviewResponse,
)
from app.modules.monitor.service import note_top_leads, overview


router = APIRouter(tags=["monitor"])


@router.post("/monitor/overview", response_model=MonitorOverviewResponse)
def monitor_overview(payload: MonitorOverviewRequest, session: Session = Depends(get_session)):
    return overview(session, since=payload.since, until=payload.until)


@router.post("/monitor/note-top-leads", response_model=MonitorNoteTopLeadsResponse)
def monitor_note_top_leads(payload: MonitorNoteTopLeadsRequest, session: Session = Depends(get_session)):
    rows = note_top_leads(session, note_id=payload.note_id, limit=payload.limit)
    return {
        "note_id": payload.note_id,
        "rows": [
            {
                "comment_id": r.comment_id,
                "intent": r.intent,
                "lead_score": r.lead_score,
                "lead_level": r.lead_level,
                "latency_ms": r.latency_ms,
                "created_at": r.created_at,
            }
            for r in rows
        ],
        "generated_at": __datetime_utc(),
    }


def __datetime_utc():
    from datetime import datetime

    return datetime.utcnow()

