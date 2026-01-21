import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.modules.leads.service import score_lead


def test_positive_comment_not_low():
    lead = score_lead("特别好闻，第一次买看到好多好评，期待效果")
    assert lead.level in {"medium", "high"}
    assert lead.score >= 35
    assert "正向反馈" in lead.signals
    assert "试用/入手意向" in lead.signals


def test_praise_only_stays_low():
    lead = score_lead("真的好闻")
    assert lead.level == "low"
    assert lead.score == 15
    assert "正向反馈" in lead.signals


def test_try_intent_is_medium():
    lead = score_lead("我想试试这个")
    assert lead.level == "medium"
    assert lead.score >= 35
    assert "试用/入手意向" in lead.signals


def test_strong_buy_is_high_and_clamped():
    lead = score_lead("链接发我，多少钱？")
    assert lead.level == "high"
    assert lead.score == 100


def test_negative_can_drop_to_zero():
    lead = score_lead("垃圾，别买")
    assert lead.level == "low"
    assert lead.score == 0

