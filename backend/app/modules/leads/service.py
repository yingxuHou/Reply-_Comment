from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class LeadResult:
    score: int
    level: str
    signals: List[str]
    next_actions: List[str]
    features: Dict[str, int]


_BUY_STRONG = re.compile(r"(现在买|立刻买|马上下单|链接发我|怎么买|哪里买|有优惠吗|领券|多少一套|到手价|库存|有货吗)")
_BUY_WEAK = re.compile(r"(价格|多少钱|对比|推荐|适合我吗|规格|型号|尺码|发货|包邮|几天到|质保|售后)")
_AFTER_SALES = re.compile(r"(退货|退款|换货|保修|维修|质量问题|坏了|投诉)")
_NEG = re.compile(r"(垃圾|坑|骗子|智商税|差评|翻车|别买|失望)")
_QUESTION = re.compile(r"(\?|？|请问|怎么|为什么|能不能|可以吗)")
_POS_PRAISE = re.compile(r"(好闻|好用|喜欢|爱了|满意|惊艳|高级|绝了|太香了|真的香|不错|很棒|推荐)")
_TRY_INTENT = re.compile(r"(想买|准备入|准备买|想入|想试试|想尝试|入手|种草|期待|期待效果|第一次买|第一次入)")
_PURCHASED = re.compile(r"(已买|已经买|买了|刚买|已入手|已入|已下单|下单了|到手|收到了|回购|复购|再买|囤货)")


def score_lead(text: str) -> LeadResult:
    t = (text or "").strip()
    features = {
        "buy_strong": 1 if _BUY_STRONG.search(t) else 0,
        "buy_weak": 1 if _BUY_WEAK.search(t) else 0,
        "after_sales": 1 if _AFTER_SALES.search(t) else 0,
        "negative": 1 if _NEG.search(t) else 0,
        "question": 1 if _QUESTION.search(t) else 0,
        "pos_praise": 1 if _POS_PRAISE.search(t) else 0,
        "try_intent": 1 if _TRY_INTENT.search(t) else 0,
        "purchased": 1 if _PURCHASED.search(t) else 0,
    }

    score = 0
    signals: List[str] = []
    if features["buy_strong"]:
        score += 70
        signals.append("强购买意向")
    if features["buy_weak"]:
        score += 35
        signals.append("弱购买意向")
    if features["try_intent"]:
        score += 35
        signals.append("试用/入手意向")
    if features["purchased"]:
        score += 10
        signals.append("已购/复购")
    if features["pos_praise"]:
        score += 15
        signals.append("正向反馈")
    if features["question"]:
        score += 10
        signals.append("提问/咨询")
    if features["after_sales"]:
        score += 20
        signals.append("售后诉求")
    if features["negative"]:
        score -= 40
        signals.append("负面情绪")

    score = max(0, min(100, score))

    if score >= 70:
        level = "high"
    elif score >= 35:
        level = "medium"
    else:
        level = "low"

    next_actions = _suggest_next_actions(level, features)
    return LeadResult(score=score, level=level, signals=signals, next_actions=next_actions, features=features)


def _suggest_next_actions(level: str, features: Dict[str, int]) -> List[str]:
    actions: List[str] = []
    if features.get("after_sales"):
        return ["优先安抚情绪并收集问题细节", "提供明确的售后路径（不索取隐私）"]

    if level == "high":
        actions.append("追问关键参数以缩短决策（规格/预算/使用场景）")
        actions.append("给出清晰的下一步（领取优惠/下单方式/库存与发货）")
        actions.append("提示可继续留言补充需求，必要时引导私信但不留外链")
        return actions

    if level == "medium":
        actions.append("补充对比点与适配建议，降低疑虑")
        actions.append("用轻量方式告知活动信息（可选）")
        return actions

    actions.append("以互动/答疑为主，避免硬广")
    return actions
