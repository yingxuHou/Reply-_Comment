import json
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class Post:
    note_id: str
    title: str
    desc: str
    tag_list: str
    nickname: str
    comment_count: str
    liked_count: str
    note_url: str


@dataclass
class Comment:
    note_id: str
    comment_id: str
    content: str
    like_count: str
    nickname: str


def parse_like_count(v: Any) -> int:
    s = str(v or "").strip()
    if not s:
        return 0
    try:
        if s.endswith("万"):
            return int(float(s[:-1]) * 10000)
        return int(float(s))
    except Exception:
        return 0


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def detect_latest_files(xhs_json_dir: Path) -> Tuple[Path, Path]:
    contents = sorted(xhs_json_dir.glob("search_contents_*.json"))
    comments = sorted(xhs_json_dir.glob("search_comments_*.json"))
    if not contents or not comments:
        raise FileNotFoundError("missing search_contents_*.json or search_comments_*.json")
    return contents[-1], comments[-1]


def normalize_post(p: Dict[str, Any]) -> Post:
    return Post(
        note_id=str(p.get("note_id") or ""),
        title=str(p.get("title") or ""),
        desc=str(p.get("desc") or ""),
        tag_list=str(p.get("tag_list") or ""),
        nickname=str(p.get("nickname") or ""),
        comment_count=str(p.get("comment_count") or ""),
        liked_count=str(p.get("liked_count") or ""),
        note_url=str(p.get("note_url") or ""),
    )


def normalize_comment(c: Dict[str, Any]) -> Comment:
    return Comment(
        note_id=str(c.get("note_id") or ""),
        comment_id=str(c.get("comment_id") or ""),
        content=str(c.get("content") or "").replace("\n", " ").strip(),
        like_count=str(c.get("like_count") or ""),
        nickname=str(c.get("nickname") or ""),
    )


def is_loreal_skincare_post(p: Post) -> bool:
    text = (p.title + "\n" + p.desc + "\n" + p.tag_list).lower()
    keywords = ["面霜", "太空霜", "小蜜罐", "紫熨斗", "复颜", "胶原", "玻色因"]
    brand_hit = ("欧莱雅" in (p.title + p.desc + p.tag_list)) or ("l'oreal" in text) or ("loreal" in text)
    return brand_hit and any(k.lower() in text for k in keywords)


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    xhs_json_dir = repo_root / "xhs" / "json"
    contents_path, comments_path = detect_latest_files(xhs_json_dir)

    posts_raw = load_json(contents_path)
    comments_raw = load_json(comments_path)

    posts = [normalize_post(p) for p in posts_raw]
    comments = [normalize_comment(c) for c in comments_raw]

    by_note: Dict[str, List[Comment]] = defaultdict(list)
    for c in comments:
        by_note[c.note_id].append(c)

    skincare_posts = [p for p in posts if is_loreal_skincare_post(p)]
    skincare_posts.sort(key=lambda p: len(by_note.get(p.note_id, [])), reverse=True)

    report: Dict[str, Any] = {
        "files": {"contents": contents_path.name, "comments": comments_path.name},
        "all_posts": len(posts),
        "all_comments": len(comments),
        "selected_posts": [],
    }

    for p in skincare_posts:
        cs = [c for c in by_note.get(p.note_id, []) if c.content]
        top_cs = sorted(cs, key=lambda c: parse_like_count(c.like_count), reverse=True)[:30]
        report["selected_posts"].append(
            {
                "note_id": p.note_id,
                "title": p.title,
                "author": p.nickname,
                "liked_count": p.liked_count,
                "comment_count": p.comment_count,
                "tag_list": p.tag_list,
                "desc": p.desc[:400],
                "top_comments": [
                    {
                        "comment_id": c.comment_id,
                        "nickname": c.nickname,
                        "like_count": parse_like_count(c.like_count),
                        "content": c.content[:300],
                    }
                    for c in top_cs
                ],
            }
        )

    out_path = repo_root / "docs" / "xhs_loreal_cream_report.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote report: {out_path}")


if __name__ == "__main__":
    main()
