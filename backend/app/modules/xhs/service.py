from __future__ import annotations

import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from app.modules.reply.intent import detect_intent


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _xhs_json_dir() -> Path:
    return _repo_root() / "xhs" / "json"


def _detect_latest_files() -> Tuple[Path, Path]:
    d = _xhs_json_dir()
    contents = sorted(d.glob("search_contents_*.json"))
    comments = sorted(d.glob("search_comments_*.json"))
    if not contents or not comments:
        raise FileNotFoundError("missing_xhs_json_files")
    return contents[-1], comments[-1]


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _to_int_like(v: Any) -> int:
    s = str(v or "").strip()
    if not s:
        return 0
    try:
        if s.endswith("万"):
            return int(float(s[:-1]) * 10000)
        return int(float(s))
    except Exception:
        return 0


def list_notes(q: str = "") -> Tuple[List[Dict[str, Any]], Dict[str, str]]:
    contents_path, comments_path = _detect_latest_files()
    notes = _load_json(contents_path)
    q2 = (q or "").strip().lower()
    if q2:
        def hit(n: Dict[str, Any]) -> bool:
            t = (str(n.get("title") or "") + "\n" + str(n.get("desc") or "") + "\n" + str(n.get("tag_list") or "")).lower()
            return q2 in t or q2 in str(n.get("note_id") or "").lower()

        notes = [n for n in notes if hit(n)]
    source = {"contents": contents_path.name, "comments": comments_path.name}
    out: List[Dict[str, Any]] = []
    for n in notes:
        out.append(
            {
                "note_id": str(n.get("note_id") or ""),
                "type": str(n.get("type") or ""),
                "title": str(n.get("title") or ""),
                "desc": str(n.get("desc") or ""),
                "tag_list": str(n.get("tag_list") or ""),
                "nickname": str(n.get("nickname") or ""),
                "liked_count": str(n.get("liked_count") or ""),
                "collected_count": str(n.get("collected_count") or ""),
                "comment_count": str(n.get("comment_count") or ""),
                "share_count": str(n.get("share_count") or ""),
                "time": int(n.get("time")) if n.get("time") is not None else None,
                "note_url": str(n.get("note_url") or ""),
                "source_keyword": str(n.get("source_keyword") or ""),
            }
        )
    return out, source


def _normalize_comment(c: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "comment_id": str(c.get("comment_id") or ""),
        "note_id": str(c.get("note_id") or ""),
        "content": str(c.get("content") or ""),
        "like_count": str(c.get("like_count") or ""),
        "create_time": int(c.get("create_time")) if c.get("create_time") is not None else None,
        "nickname": str(c.get("nickname") or ""),
        "user_id": str(c.get("user_id") or ""),
        "ip_location": str(c.get("ip_location") or ""),
        "sub_comment_count": str(c.get("sub_comment_count") or ""),
        "parent_comment_id": str(c.get("parent_comment_id") or ""),
    }


def list_comments(
    note_id: str,
    offset: int,
    limit: int,
    sort: str,
    q: str,
) -> Tuple[List[Dict[str, Any]], int]:
    _, comments_path = _detect_latest_files()
    comments = _load_json(comments_path)
    rows = [c for c in comments if str(c.get("note_id") or "") == note_id]
    q2 = (q or "").strip().lower()
    if q2:
        rows = [c for c in rows if q2 in str(c.get("content") or "").lower()]

    if sort == "time":
        rows.sort(key=lambda c: int(c.get("create_time") or 0), reverse=True)
    else:
        rows.sort(key=lambda c: _to_int_like(c.get("like_count")), reverse=True)

    total = len(rows)
    offset2 = max(0, int(offset))
    limit2 = min(max(1, int(limit)), 500)
    slice_rows = rows[offset2 : offset2 + limit2]
    return [_normalize_comment(c) for c in slice_rows], total


def analyze_note(note_id: str, max_samples: int = 500) -> Dict[str, Any]:
    rows, total = list_comments(note_id=note_id, offset=0, limit=max_samples, sort="like", q="")
    counter: Counter[str] = Counter()
    for c in rows:
        r = detect_intent(str(c.get("content") or ""))
        counter[r.intent] += 1

    top_comments = rows[:10]
    return {
        "note_id": note_id,
        "total_comments": total,
        "top_comments": top_comments,
        "intent_counts": dict(counter),
        "generated_at": datetime.utcnow(),
    }
