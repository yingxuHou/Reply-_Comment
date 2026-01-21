import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.modules.leads.service import score_lead
from app.modules.reply.intent import detect_intent


def main():
    cases = [
        "怎么买？有优惠吗",
        "垃圾，别买",
        "请问这个能放到WPS里吗？",
        "退货怎么处理",
        "这个干发帽在哪里买呀 好可爱",
        "混油敏感能用吗，会闷痘吗",
        "我用着有点刺痛泛红，咋办",
    ]
    for t in cases:
        intent = detect_intent(t)
        lead = score_lead(t)
        print(t)
        print(intent.intent, intent.confidence, intent.reasons)
        print(lead.level, lead.score, lead.signals)
        print("---")


if __name__ == "__main__":
    main()
