from __future__ import annotations

from typing import Mapping


class SafeDict(dict):
    def __missing__(self, key):
        return "{" + str(key) + "}"


def render_template(tpl: str, variables: Mapping[str, str]) -> str:
    return tpl.format_map(SafeDict(**{k: str(v) for k, v in variables.items()}))


FALLBACK_TEMPLATES = {
    "praise": "谢谢你的喜欢～后面也会继续更新更实用的内容！",
    "question": "收到～方便说下你更关注哪一点（比如功能/使用场景/成本）我再给你更准确的建议。",
    "buy_intent": "可以的～你想要哪种规格/版本？我先帮你对一下适配情况，再把优惠信息给你。",
    "after_sales": "我来帮你处理～麻烦说下具体问题/订单情况（不需要发隐私），我给你对应的解决方案。",
    "complaint": "抱歉给你带来不好的体验。你方便描述下具体哪里不满意吗？我这边马上核实并给你处理方案。",
    "chat": "收到～我在的，有任何具体问题直接问我就行。",
    "empty": "收到～我这边看不到具体文字内容，你方便再补充一句吗？",
}

