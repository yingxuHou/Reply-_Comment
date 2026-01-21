import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Tuple


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def save_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def is_cream_focused(post: Dict[str, Any]) -> bool:
    text = (post.get("title", "") + "\n" + post.get("desc", "") + "\n" + post.get("tag_list", "")).lower()
    keys = ["面霜", "太空霜", "小蜜罐", "紫熨斗", "淡纹霜", "抗老", "复颜", "玻色因", "胶原"]
    return any(k.lower() in text for k in keys)


INTENT_PATTERNS: List[Tuple[str, re.Pattern]] = [
    ("怀疑广告/水军", re.compile(r"(广告|水军|恰饭|推广|变成广告|也是打上广告|软广)")),
    ("求链接/怎么买", re.compile(r"(怎么买|哪里买|链接|上车|下单|购买|到手价|优惠|券|活动|大促)")),
    ("肤质适配/能不能用", re.compile(r"(干皮|油皮|混油|敏感|痘|闭口|孕|哺乳|学生|适合|能用吗|会闷吗)")),
    ("用法/搭配", re.compile(r"(怎么用|叠加|顺序|妆前|早晚|用量|搭配|能不能.*一起)")),
    ("效果反馈/种草", re.compile(r"(好用|想买|已下单|回购|种草|效果|爱了|绝了|真香|安排)")),
    ("售后/不适/踩雷", re.compile(r"(不适|过敏|泛红|刺痛|搓泥|踩雷|不行|翻车|退货|退款)")),
]


def classify_intents(comments: List[Dict[str, Any]]) -> Dict[str, int]:
    counts = {name: 0 for name, _ in INTENT_PATTERNS}
    for c in comments:
        text = (c.get("content") or "").strip()
        if not text:
            continue
        for name, pat in INTENT_PATTERNS:
            if pat.search(text):
                counts[name] += 1
    return counts


def pick_comments(post: Dict[str, Any]) -> List[Dict[str, Any]]:
    comments = post.get("top_comments") or []
    comments = [c for c in comments if (c.get("content") or "").strip()]
    comments.sort(key=lambda c: int(c.get("like_count") or 0), reverse=True)

    picks: List[Dict[str, Any]] = []
    seen = set()
    for c in comments:
        if len(picks) >= 6:
            break
        cid = c.get("comment_id")
        if cid in seen:
            continue
        picks.append(c)
        seen.add(cid)

    for c in comments:
        if len(picks) >= 10:
            break
        text = c.get("content") or ""
        if re.search(r"(广告|水军|恰饭|推广)", text) and c.get("comment_id") not in seen:
            picks.append(c)
            seen.add(c.get("comment_id"))
    return picks


def generate_reply_for_comment(post: Dict[str, Any], comment_text: str) -> str:
    title = post.get("title") or ""
    tag = post.get("tag_list") or ""
    ctx = f"{title}\n{tag}"

    t = (comment_text or "").strip()
    if not t:
        return "收到～我这边看不到具体文字内容，你方便再补充一句吗？"

    if re.search(r"(广告|水军|恰饭|推广|变成广告|软广)", t):
        return "理解你的顾虑～如果是合作内容一般会在笔记里标注；我这边可以把产品信息/用法/适合肤质讲清楚，你更关心肤感还是淡纹紧致这块？"

    if re.search(r"(怎么买|哪里买|链接|下单|到手价|优惠|券|活动|大促)", t):
        return "可以的～活动价会随平台券和档期变化。你现在是想入轻盈版还是滋润版？告诉我肤质（干/油/混合/敏感）我帮你选更合适的，并提醒你叠券思路。"

    if re.search(r"(干皮|油皮|混油|敏感|痘|闭口|适合|能用吗|会闷吗)", t):
        return "先看肤质更稳：干皮/秋冬更建议滋润版，混合/油皮更建议轻盈版；如果是敏感期建议先小范围试用、把用量从少到多循序加。你属于哪种肤质、现在有没有在刷酸/用A醇？"

    if re.search(r"(怎么用|顺序|妆前|早晚|用量|搭配|叠加)", t):
        return "一般建议：洁面→水/精华→面霜（黄豆大小）→白天加防晒；做妆前的话薄涂一层，等 2-3 分钟再上底妆会更贴。你现在用的精华是哪一类（补水/修护/抗老）？我给你更具体的搭配。"

    if re.search(r"(过敏|刺痛|泛红|搓泥|踩雷|翻车)", t):
        return "抱抱～如果出现刺痛泛红建议先停用，回到基础保湿修护；也可能是叠加酸/VA类导致的刺激或用量过多。你现在的护肤步骤和最近是否在刷酸/用A醇？我帮你排查一下。"

    if re.search(r"(回购|想买|好用|种草|已下单|真香|效果)", t):
        return "谢谢喜欢～如果你愿意分享下肤质和使用场景（通勤/熬夜/空调房），我也可以给你一套更省事的“日常维稳 + 重点抗老”搭配思路。"

    if "太空霜" in ctx:
        return "太空霜这个很多人会当“修护/封闭”用：更适合晚间薄涂、干燥或屏障不稳时用来锁水。你是更想解决干燥起皮还是细纹松弛？"

    if "小蜜罐" in ctx:
        return "小蜜罐这类更偏“保湿+支撑感”的面霜路线。你现在最在意的是肤感清爽、还是淡纹紧致？我按你的优先级给你建议。"

    return "收到～你更想了解哪个点：肤质适配、用法搭配、还是活动/优惠信息？我按你关心的给你讲清楚。"


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    report_path = repo_root / "docs" / "xhs_loreal_cream_report.json"
    report = load_json(report_path)
    posts = report.get("selected_posts") or []
    posts = [p for p in posts if is_cream_focused(p)]

    md: List[str] = []
    md.append("# 欧莱雅面霜相关帖子与评论区分析（自动生成）")
    md.append("")
    md.append(f"- 数据源：{report.get('files',{})}")
    md.append(f"- 过滤后的帖子数：{len(posts)}")
    md.append("")

    for post in posts:
        title = post.get("title") or ""
        note_id = post.get("note_id") or ""
        tag_list = post.get("tag_list") or ""
        desc = (post.get("desc") or "").replace("\n", " ").strip()
        intents = classify_intents(post.get("top_comments") or [])
        picks = pick_comments(post)

        md.append("## " + title)
        md.append(f"- note_id：{note_id}")
        md.append(f"- 标签：{tag_list}")
        md.append(f"- 内容摘要：{desc[:160]}{'…' if len(desc)>160 else ''}")
        md.append("- 评论意图分布（基于 top_comments 关键词粗分）：")
        md.append("  " + "；".join([f"{k} {v}" for k, v in intents.items() if v]))
        md.append("")
        md.append("### 建议回复（挑选代表性评论）")
        for c in picks:
            ctext = c.get("content") or ""
            nick = c.get("nickname") or ""
            likes = c.get("like_count") or 0
            reply = generate_reply_for_comment(post, ctext)
            md.append(f"- 评论（{nick}｜赞{likes}）：{ctext}")
            md.append(f"  - 建议回复：{reply}")
        md.append("")

    out_path = repo_root / "docs" / "xhs_loreal_cream_replies.md"
    save_text(out_path, "\n".join(md))
    print(f"Wrote replies: {out_path}")


if __name__ == "__main__":
    main()
