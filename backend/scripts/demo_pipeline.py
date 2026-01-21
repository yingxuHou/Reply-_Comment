from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.db import session_scope, create_db_and_tables
from app.modules.kb.service import ensure_default_kb, create_item, publish_kb
from app.modules.reply.service import suggest_reply
from app.modules.vector.service import reindex_kb


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))

def _detect_latest_xhs_files(repo_root: Path) -> tuple[Path, Path]:
    d = repo_root / "xhs" / "json"
    contents = sorted(d.glob("search_contents_*.json"))
    comments = sorted(d.glob("search_comments_*.json"))
    if not contents or not comments:
        raise FileNotFoundError("missing_xhs_json_files")
    return contents[-1], comments[-1]


def main():
    create_db_and_tables()
    repo_root = _repo_root()
    contents_path, comments_path = _detect_latest_xhs_files(repo_root)

    posts = _load_json(contents_path)
    comments = _load_json(comments_path)

    with session_scope() as session:
        kb = ensure_default_kb(session)
        items = session.exec(
            __select_items(kb_id=kb.id)
        ).all()
        if not items:
            create_item(
                session,
                kb_id=kb.id,
                key="shipping",
                title="发货与物流",
                tags="物流,发货",
                content="一般 48 小时内发货，偏远地区时效可能延长。需要加急可以留言说明。",
                source="demo",
            )
            create_item(
                session,
                kb_id=kb.id,
                key="after_sales",
                title="售后与退换",
                tags="售后,退换",
                content="如遇到质量问题请先描述现象并提供必要的订单信息（不要公开隐私）。支持按平台规则处理退换。",
                source="demo",
            )
            create_item(
                session,
                kb_id=kb.id,
                key="promo",
                title="优惠与活动",
                tags="优惠,活动",
                content="如有平台活动，以详情页展示为准。需要我帮你看适用的优惠可以告诉我预算和型号偏好。",
                source="demo",
            )

        publish_kb(session, kb.id)
        kb = ensure_default_kb(session)
        reindex_kb(session, kb_id=kb.id, kb_version=kb.published_version)

        post = posts[0]
        note_title = post.get("title", "")
        note_desc = post.get("desc", "")

        printed = 0
        for c in comments:
            if c.get("note_id") != post.get("note_id"):
                continue
            text = (c.get("content") or "").strip()
            if not text:
                continue
            result = suggest_reply(
                session=session,
                kb_id=kb.id,
                comment_id=c.get("comment_id", ""),
                note_id=c.get("note_id", ""),
                comment_text=text,
                note_title=note_title,
                note_desc=note_desc,
                top_k=5,
                kb_version=kb.published_version,
                inject_sales=True,
            )
            print("COMMENT:", text)
            print("REPLY  :", result["reply"])
            print("LEAD   :", result["lead_level"], result["lead_score"], result["lead_signals"])
            print("----")
            printed += 1
            if printed >= 5:
                break


def __select_items(kb_id):
    from sqlmodel import select

    from app.modules.kb.models import KnowledgeItem

    return select(KnowledgeItem).where(KnowledgeItem.kb_id == kb_id)


if __name__ == "__main__":
    main()
