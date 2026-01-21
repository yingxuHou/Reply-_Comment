from __future__ import annotations

import json
import time
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from sqlmodel import Session

from app.modules.reply.glm_chat import get_chat_client
from app.modules.reply.intent import detect_intent
from app.modules.reply.policy import enforce_style, redact_sensitive
from app.modules.reply.templates import FALLBACK_TEMPLATES
from app.modules.leads.service import score_lead
from app.modules.monitor.service import log_reply_event
from app.modules.vector.service import get_latest_index, search as vector_search


def suggest_reply(
    session: Session,
    kb_id: UUID,
    comment_id: str,
    note_id: str,
    comment_text: str,
    note_title: str,
    note_desc: str,
    top_k: int,
    kb_version: Optional[int],
    inject_sales: bool,
) -> dict:
    started = time.time()
    intent = detect_intent(comment_text)
    lead = score_lead(comment_text)

    latency_retrieval, hits = vector_search(
        session,
        kb_id=kb_id,
        query=_build_query(note_title, note_desc, comment_text, intent.intent),
        top_k=top_k,
        kb_version=kb_version,
    )
    idx = get_latest_index(session, kb_id, kb_version)
    used_version = kb_version if kb_version is not None else (idx.kb_version if idx else 0)

    reply_text = _generate_reply(
        comment_text=comment_text,
        note_title=note_title,
        note_desc=note_desc,
        intent=intent.intent,
        knowledge_hits=hits,
        inject_sales=inject_sales,
    )
    reply_text = enforce_style(redact_sensitive(reply_text))

    latency_ms = int((time.time() - started) * 1000)
    meta_json = json.dumps(
        {"retrieval_ms": latency_retrieval, "intent_reasons": intent.reasons},
        ensure_ascii=False,
    )
    llm_used = bool(get_chat_client())
    log_reply_event(
        session=session,
        kb_id=kb_id,
        kb_version=used_version,
        comment_id=comment_id,
        note_id=note_id,
        intent=intent.intent,
        lead_score=lead.score,
        lead_level=lead.level,
        latency_ms=latency_ms,
        llm_used=llm_used,
        meta={"retrieval_ms": latency_retrieval},
    )
    return {
        "kb_id": kb_id,
        "kb_version": used_version,
        "intent": intent.intent,
        "intent_confidence": intent.confidence,
        "reply": reply_text,
        "used_knowledge": hits,
        "lead_score": lead.score,
        "lead_level": lead.level,
        "lead_signals": lead.signals,
        "next_actions": lead.next_actions,
        "latency_ms": latency_ms,
        "created_at": datetime.utcnow(),
        "meta_json": meta_json,
    }


def _build_query(note_title: str, note_desc: str, comment_text: str, intent: str) -> str:
    parts = [p.strip() for p in [note_title, note_desc, comment_text] if (p or "").strip()]
    base = "\n".join(parts[:3])
    return f"[意图]{intent}\n{base}"


def _generate_reply(
    comment_text: str,
    note_title: str,
    note_desc: str,
    intent: str,
    knowledge_hits: List[dict],
    inject_sales: bool,
) -> str:
    client = get_chat_client()
    if not client:
        return FALLBACK_TEMPLATES.get(intent, FALLBACK_TEMPLATES["chat"])

    knowledge_block = "\n\n".join([f"- {h['content']}" for h in knowledge_hits[:5]])
    sales_hint = ""
    if inject_sales and intent in {"buy_intent", "question"}:
        sales_hint = "如果对方表现出购买/咨询意向，用不冒犯的方式引导私信或继续提问，避免硬广。"

    system = (
        "你是评论区的客服兼销售助理，语气自然礼貌，回复短而明确。"
        "不要编造事实；如果知识不足，就先澄清问题。"
        "不要输出任何手机号/微信号/外链。"
    )
    user = (
        f"帖子标题：{note_title}\n"
        f"帖子内容：{note_desc}\n"
        f"评论：{comment_text}\n\n"
        f"可用知识（可能为空）：\n{knowledge_block}\n\n"
        f"意图：{intent}\n"
        f"额外要求：{sales_hint}\n"
        "请输出一条最合适的中文回复。"
    )
    result = client.chat(messages=[{"role": "system", "content": system}, {"role": "user", "content": user}], temperature=0.3)
    return result.content.strip() or FALLBACK_TEMPLATES.get(intent, FALLBACK_TEMPLATES["chat"])
