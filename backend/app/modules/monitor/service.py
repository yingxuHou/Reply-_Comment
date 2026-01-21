from __future__ import annotations

import json
from datetime import datetime
from typing import List, Optional

from sqlmodel import Session, func, select

from app.modules.monitor.models import ReplyEvent


def log_reply_event(
    session: Session,
    kb_id,
    kb_version: int,
    comment_id: str,
    note_id: str,
    intent: str,
    lead_score: int,
    lead_level: str,
    latency_ms: int,
    llm_used: bool,
    meta: dict,
) -> None:
    ev = ReplyEvent(
        kb_id=kb_id,
        kb_version=kb_version,
        comment_id=comment_id or "",
        note_id=note_id or "",
        intent=intent,
        lead_score=int(lead_score),
        lead_level=lead_level,
        latency_ms=int(latency_ms),
        llm_used=bool(llm_used),
        created_at=datetime.utcnow(),
        meta_json=json.dumps(meta or {}, ensure_ascii=False),
    )
    session.add(ev)
    session.commit()


def overview(session: Session, since: Optional[datetime], until: Optional[datetime]) -> dict:
    from sqlalchemy import case

    filters = []
    if since is not None:
        filters.append(ReplyEvent.created_at >= since)
    if until is not None:
        filters.append(ReplyEvent.created_at <= until)

    total = int(session.exec(select(func.count()).select_from(ReplyEvent).where(*filters)).one())
    if total == 0:
        return {
            "total_replies": 0,
            "avg_latency_ms": 0,
            "llm_rate": 0.0,
            "lead_high": 0,
            "lead_medium": 0,
            "lead_low": 0,
            "intent_counts": {},
            "generated_at": datetime.utcnow(),
        }

    avg_latency_raw = session.exec(select(func.avg(ReplyEvent.latency_ms)).where(*filters)).one()
    avg_latency = int(float(avg_latency_raw or 0.0))

    llm_rate_raw = session.exec(
        select(func.avg(case((ReplyEvent.llm_used == True, 1), else_=0))).where(*filters)
    ).one()
    llm_rate = float(llm_rate_raw or 0.0)

    lead_counts_rows = session.exec(
        select(ReplyEvent.lead_level, func.count()).where(*filters).group_by(ReplyEvent.lead_level)
    ).all()
    lead_counts = {lvl: int(cnt) for (lvl, cnt) in lead_counts_rows}
    lead_high = lead_counts.get("high", 0)
    lead_medium = lead_counts.get("medium", 0)
    lead_low = lead_counts.get("low", 0) + sum(v for k, v in lead_counts.items() if k not in {"high", "medium", "low"})

    intent_counts_rows = session.exec(select(ReplyEvent.intent, func.count()).where(*filters).group_by(ReplyEvent.intent)).all()
    intent_counts = {it: int(cnt) for (it, cnt) in intent_counts_rows}
    return {
        "total_replies": total,
        "avg_latency_ms": avg_latency,
        "llm_rate": llm_rate,
        "lead_high": lead_high,
        "lead_medium": lead_medium,
        "lead_low": lead_low,
        "intent_counts": intent_counts,
        "generated_at": datetime.utcnow(),
    }


def note_top_leads(session: Session, note_id: str, limit: int) -> List[ReplyEvent]:
    stmt = (
        select(ReplyEvent)
        .where(ReplyEvent.note_id == note_id)
        .order_by(ReplyEvent.lead_score.desc(), ReplyEvent.created_at.desc())
        .limit(limit)
    )
    return list(session.exec(stmt))
