"""C45 reason/action and accepted support regression boundaries; all data is fictional."""
from copy import deepcopy

import pytest

from app.services import production_message_renderer as renderer
from app.services.detailed_stock_message_v2 import _entry_lines
from app.services.vnext_execution_profile import SOL_HIGH_V1
from tests.test_c43_offline import fixture, evaluate
from tests.test_c44_renderer_replay import synthetic_renderer_case


def message_lines(context, *, reason="BUSINESS_GATE_NOT_MET", stance="WAIT"):
    model_input, timing, _ = evaluate(context)
    output = dict(new_buyer=stance, reason_class=reason, timing_context=timing)
    before = deepcopy((context, output))
    lines, refs = _entry_lines(output, model_input, context, "us", "2026-11-23")
    assert (context, output) == before
    return lines, refs


@pytest.mark.parametrize("reason,expected", [
    ("BUSINESS_GATE_NOT_MET", "사업 근거 확인 대기"),
    ("BUSINESS_MIXED", "사업 근거 혼재 해소 대기"),
    ("VALUATION_BURDENSOME", "가치평가 부담 완화 대기"),
    ("VALUATION_UNRESOLVED", "가치평가 자료 확인 대기"),
])
def test_same_supported_location_keeps_distinct_accepted_wait_reasons(reason, expected):
    lines, _ = message_lines(fixture(), reason=reason)
    assert "지지 구간 안" in lines[1]
    assert lines[-1] == "최종 신규매수 행동: " + expected
    assert "신규 매수 검토 가능" not in "\n".join(lines)


def test_structural_invalidation_is_visible_even_when_business_already_waits():
    context = fixture()
    context["decision_evidence"][3]["statement"]["status"] = "hard_invalid"
    lines, refs = message_lines(context)
    assert "사업 근거 요건 미충족" in lines[0]
    assert "무효화 조건 충족" in lines[1]
    assert "지지 이탈 구조 재검토" in lines[2]
    assert "canonical:chart:structure:invalidation" in refs
    avoided, _ = message_lines(context, reason="ACTIVE_ADVERSE_UNCOMPENSATED", stance="AVOID")
    assert "신규 매수 회피" in avoided[2]


@pytest.mark.parametrize("market", ["kr", "us"])
@pytest.mark.parametrize("timeframe", ["daily", "weekly"])
def test_full_stock_renderer_displays_selected_support_without_reference_v3(monkeypatch, market, timeframe):
    session, ticker, accepted, row, request = synthetic_renderer_case(
        market, include_support=True, support_timeframe=timeframe)
    before = deepcopy((session.fresh_stocks, session.bctx, row, request))
    monkeypatch.setattr(renderer, "stock_plan", lambda *args: accepted)
    message = renderer.stock_message(session, ticker, row, execution_profile=SOL_HIGH_V1)
    assert message["text"].count("진입 관찰 지지 구간(") == 1
    expected = "2026-11-23 일봉·조정봉" if timeframe == "daily" else "2026-11-23 평가·2026-11-20 주봉 완료봉·조정봉"
    assert expected in message["text"]
    assert "신규 매수 검토 가능" in message["text"]
    assert "보유자: HOLD" in message["text"]
    assert "AI 분석 판단: BUY" in message["text"]
    assert message["NO_SEND"] is True
    assert (session.fresh_stocks, session.bctx, row, request) == before
