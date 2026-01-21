from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class IntentResult:
    intent: str
    confidence: float
    reasons: list[str]


_BUY_RE = re.compile(
    r"(怎么买|哪里买|哪买|求链接|蹲链接|链接|上车|购买|下单|到手价|优惠|券|活动|大促|价格|多少钱|有货吗|库存|发货|包邮|尺码|型号|版本|咨询)"
)
_AFTER_SALES_RE = re.compile(r"(售后|退货|退款|换货|保修|维修|质量|坏了|投诉|不适|过敏|泛红|刺痛|搓泥|闷痘|闭口)")
_PRAISE_RE = re.compile(r"(好棒|厉害|喜欢|爱了|太强|牛|绝了|学到了|谢谢|好看|好可爱|太美|好美|真香|种草|回购|安排|yyds)")
_NEG_RE = re.compile(r"(垃圾|坑|骗子|差评|别买|不好用|翻车|失望|智商税|踩雷)")
_QUESTION_RE = re.compile(r"(\?|？|怎么|如何|为何|为什么|能不能|可以吗|行吗|有没有|请问|在哪|哪里|怎么用|用法|顺序|叠加|搭配|会闷吗|能用吗|适合吗)")


def detect_intent(text: str) -> IntentResult:
    t = (text or "").strip()
    if not t:
        return IntentResult(intent="empty", confidence=0.9, reasons=["empty_text"])

    reasons: list[str] = []
    score_buy = 1.0 if _BUY_RE.search(t) else 0.0
    score_after = 1.0 if _AFTER_SALES_RE.search(t) else 0.0
    score_praise = 1.0 if _PRAISE_RE.search(t) else 0.0
    score_neg = 1.0 if _NEG_RE.search(t) else 0.0
    score_q = 1.0 if _QUESTION_RE.search(t) else 0.0

    if score_after:
        reasons.append("after_sales_keyword")
        return IntentResult(intent="after_sales", confidence=0.85, reasons=reasons)
    if score_buy:
        reasons.append("buy_keyword")
        return IntentResult(intent="buy_intent", confidence=0.85, reasons=reasons)
    if score_neg:
        reasons.append("negative_keyword")
        return IntentResult(intent="complaint", confidence=0.8, reasons=reasons)
    if score_praise:
        reasons.append("praise_keyword")
        return IntentResult(intent="praise", confidence=0.75, reasons=reasons)
    if score_q:
        reasons.append("question_pattern")
        return IntentResult(intent="question", confidence=0.7, reasons=reasons)

    return IntentResult(intent="chat", confidence=0.55, reasons=["fallback"])
