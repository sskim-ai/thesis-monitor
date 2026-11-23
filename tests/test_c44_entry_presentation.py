"""Changed presentation boundaries only; raw B2 economics and timing stay frozen."""
from copy import deepcopy
from types import SimpleNamespace

import pytest

from app.services.detailed_stock_message_v2 import _completed_price_session, _entry_lines
from tests.test_c43_offline import evaluate, fixture


def lines_for(context, *, selected=None, reason="QUALIFIED_VALUATION_CONTEXT_SUPPORTIVE"):
    model_input, timing, _ = evaluate(context)
    if selected is not None:
        timing.update(selected=selected, relation="UNRESOLVED", state="UNRESOLVED")
    output = dict(new_buyer="ATTRACTIVE", reason_class=reason,
                  valuation_context=dict(state="SUPPORTIVE"), timing_context=timing)
    before = deepcopy((context, output))
    lines, refs = _entry_lines(output, model_input, context, "us", "2026-11-23")
    assert (context, output) == before
    return "\n".join(lines), refs


def test_confirmed_above_reports_remaining_price_condition_without_new_buy_path():
    context = fixture()
    context["r2_eligible_range_catalog"]["tactical_candidates"][0]["high"] = 9.5
    context["decision_evidence"][2]["statement"]["zone_high"] = 9.5
    ref = "canonical:chart:structure:state"
    state = dict(ref_id=ref, as_of="2026-11-23", label="chart_state",
        statement=dict(state="CONFIRM_ENTRY", user_semantics="confirmed_breakout_not_buy_command",
                       reasons=["two_close_breakout", "volume_ratio_confirmed"]))
    context["decision_evidence"].append(state)
    permission = dict(ref_id=ref, allowed_uses=["ENTRY"])
    context["source_use_projection"]["source_permissions"].append(permission)
    text, refs = lines_for(context)
    assert "지지 구간 위" in text and "돌파·거래량 확인 완료" in text
    assert "선택된 지지 구간 기준의 진입은 가격 조정 대기" in text
    assert "신규 확인 신호 대기" not in text and "신규 매수 검토 가능" not in text
    assert ref in refs
    for key, value in (("permission", "DISPLAY"), ("as_of", "2026-11-20")):
        permission["allowed_uses"] = [value] if key == "permission" else ["ENTRY"]
        state["as_of"] = value if key == "as_of" else "2026-11-23"
        text, refs = lines_for(context)
        assert "신규 확인 신호 대기" in text and "확인 완료" not in text
        assert ref not in refs


@pytest.mark.parametrize("gap,expected", [
    ("daily", "일봉 데이터 부족"),
    ("display_only_support", "현재 적격 지지 구간 없음"),
    ("selection", "선택된 진입 구간 확인 필요"),
    ("currency", "통화 불일치"),
    ("basis", "조정 기준 불일치"),
])
def test_unresolved_explains_observed_gap_without_promoting_reference_support(gap, expected):
    context = fixture()
    selected = None
    if gap == "daily":
        context["decision_evidence"][1]["statement"]["quality"] = "unavailable"
    elif gap == "display_only_support":
        context["source_use_projection"]["source_permissions"][2]["allowed_uses"] = ["DISPLAY"]
    elif gap == "selection":
        selected = "absent"
    elif gap == "currency":
        context["decision_evidence"][1]["statement"]["currency"] = "KRW"
    else:
        context["decision_evidence"][1]["statement"]["price_basis"] = "unadjusted"
    text, _ = lines_for(context, selected=selected)
    assert expected in text
    assert all(raw not in text for raw in ("UNRESOLVED", "FAVORABLE_NOW", "PRICE_ZONE_", "QUALIFIED_VALUATION_"))
    assert "신규 매수 검토 가능" not in text


def test_unknown_reason_does_not_invent_economic_cause_or_expose_internal_code():
    text, _ = lines_for(fixture(), reason="FUTURE_UNKNOWN_REASON")
    assert "신규매수 판단 근거 확인 필요" in text and "FUTURE_UNKNOWN_REASON" not in text
    assert "부담스러운 가치평가" not in text and "활성 중대 위험" not in text


def test_completed_session_never_falls_back_to_assessment_or_quote_date():
    packet = SimpleNamespace(market="us", ticker="X", assessment_date="2026-11-24")
    source = dict(packet=dict(stocks=[dict(current_price_context=dict(as_of_date="2026-11-23"))]))
    base = SimpleNamespace(source_generation_id="g", source_stock=source)
    assert _completed_price_session(packet, base, "id") is None
    projection = dict(generation_id="g", market="us", ticker="X", canonical_security_id="id",
                      target_session="2026-11-23")
    source["completed_session_current_price"] = projection
    assert _completed_price_session(packet, base, "id") == "2026-11-23"
    for key in ("generation_id", "market", "ticker", "canonical_security_id"):
        source["completed_session_current_price"] = dict(projection, **{key: "other"})
        with pytest.raises(ValueError, match="price_session_identity_mismatch"):
            _completed_price_session(packet, base, "id")
