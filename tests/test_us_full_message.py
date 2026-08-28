from __future__ import annotations

from app.services.us_full_message_service import (
    preserve_us_full_message_layout,
    render_us_full_market_message,
)
from app.services.us_market_digest_plan_service import build_us_market_digest_plan


def _fact(
    symbol: str,
    fact_type: str,
    value: float,
    *,
    label: str,
) -> dict[str, object]:
    return {
        "fact_id": f"market:{fact_type.removeprefix('market_')}:{symbol}",
        "fact_type": fact_type,
        "as_of_date": "2026-08-27",
        "fields": {
            "series_code": symbol,
            "label": label,
            "return_pct": value,
            "temporal_role": "CURRENT_OBSERVATION",
            "today_signal_eligible": True,
            "structured_state": "CURRENT_DIRECTIONAL",
        },
    }


def _context() -> dict[str, object]:
    facts = [
        _fact("SPY", "market_index", 0.6553, label="S&P500"),
        _fact("QQQ", "market_index", 1.3692, label="Nasdaq"),
        _fact("IWM", "market_index", 0.2944, label="Russell 2000"),
        _fact("SOXX", "market_sector", 1.9461, label="반도체"),
        _fact("RSP", "market_style", -0.2972, label="S&P500 동일가중"),
        _fact("XLK", "market_sector", 3.1558, label="정보기술"),
        _fact("XLP", "market_sector", -1.3794, label="필수소비재"),
    ]
    context: dict[str, object] = {"fact_catalog": facts, "key_change_fact_ids": []}
    context["us_market_digest_plan"] = build_us_market_digest_plan(context).to_dict()
    return context


def test_full_message_owns_index_and_sector_numbers_in_fixed_order() -> None:
    rendered = render_us_full_market_message(_context())

    assert rendered.status == "PASS"
    assert rendered.section_order == (
        "HEADER",
        "INDEX_BLOCK",
        "MARKET_INTERNAL",
        "NEXT_CHECK",
    )
    assert rendered.text.startswith("🇺🇸 미국시장 마감\n\n📈 주요 지수")
    for line in (
        "• SPY +0.66%",
        "• QQQ +1.37%",
        "• IWM +0.29%",
        "• SOXX +1.95%",
        "• RSP -0.30%",
        "• 업종 강세: 정보기술 +3.16%",
        "• 업종 약세: 필수소비재 -1.38%",
    ):
        assert rendered.text.count(line) == 1
    assert rendered.text.index("📈 주요 지수") < rendered.text.index("🔎 시장 내부")
    assert rendered.text.index("🔎 시장 내부") < rendered.text.index("📌 다음 확인")


def test_full_message_renders_verified_night_returns_without_levels() -> None:
    context = _context()
    context["night_futures"] = [
        {
            "fact_id": "market:night_futures:1",
            "series_code": "KRX_KOSPI200_NIGHT_FUT",
            "change_pct": 0.67,
        },
        {
            "fact_id": "market:night_futures:2",
            "series_code": "KRX_KOSDAQ150_NIGHT_FUT",
            "change_pct": -0.28,
        },
    ]

    rendered = render_us_full_market_message(context)

    assert rendered.status == "PASS"
    assert "🌙 한국 야간선물\n• KOSPI200 야간선물 +0.67%" in rendered.text
    assert "• KOSDAQ150 야간선물 -0.28%" in rendered.text
    assert rendered.night_fact_ids == (
        "market:night_futures:1",
        "market:night_futures:2",
    )


def test_incomplete_index_tuple_fails_closed_for_new_layout() -> None:
    context = _context()
    context["fact_catalog"] = [
        row
        for row in context["fact_catalog"]
        if row["fields"]["series_code"] != "RSP"
    ]
    context["us_market_digest_plan"] = build_us_market_digest_plan(context).to_dict()

    rendered = render_us_full_market_message(context)

    assert rendered.status == "FAIL"
    assert "missing_current_index_return:RSP" in rendered.validation_errors


def test_adaptive_output_can_only_replace_bounded_next_check() -> None:
    deterministic = render_us_full_market_message(_context()).text
    candidate = """🤖 분석

🎯 판단
다른 요약입니다.

📌 다음 확인
• 다음 세션의 참여 폭을 확인합니다.
"""

    preserved = preserve_us_full_message_layout(
        candidate,
        deterministic_text=deterministic,
    )

    assert preserved.startswith("🇺🇸 미국시장 마감")
    assert "• SPY +0.66%" in preserved
    assert "• 다음 세션의 참여 폭을 확인합니다." in preserved
    assert "다른 요약입니다" not in preserved


def test_relative_equity_fact_is_not_promoted_to_macro_slot() -> None:
    context = _context()
    relative = {
        "fact_id": "market:relative:SOXX:SPY",
        "fact_type": "market_relative",
        "as_of_date": "2026-08-27",
        "fields": {
            "series_code": "SOXX_SPY",
            "temporal_role": "CURRENT_OBSERVATION",
            "today_signal_eligible": True,
            "structured_state": "CURRENT_DIRECTIONAL",
        },
    }
    context["fact_catalog"].append(relative)
    context["key_change_fact_ids"] = [relative["fact_id"]]

    plan = build_us_market_digest_plan(context)
    macro = plan.items[-1]

    assert macro.slot.value == "MACRO_CONTEXT"
    assert macro.selected is False
    assert macro.evidence_refs == ()


def test_legacy_stored_plan_cannot_reuse_relative_equity_as_macro() -> None:
    context = _context()
    relative = {
        "fact_id": "market:relative:SOXX:SPY",
        "fact_type": "market_relative",
        "as_of_date": "2026-08-27",
        "fields": {
            "series_code": "SOXX_SPY",
            "temporal_role": "CURRENT_OBSERVATION",
            "today_signal_eligible": True,
            "structured_state": "CURRENT_DIRECTIONAL",
        },
    }
    context["fact_catalog"].append(relative)
    items = list(context["us_market_digest_plan"]["items"])
    items[-1] = {
        "slot": "MACRO_CONTEXT",
        "priority": 5,
        "claim_text": "보조 거시 맥락에서는 거시 지표가 변화 없음했습니다.",
        "materiality": "legacy invalid ownership",
        "evidence_refs": [relative["fact_id"]],
        "numeric_refs": [],
        "temporal_roles": ["CURRENT_OBSERVATION"],
        "observation_dates": ["2026-08-27"],
        "omission_reason": "SELECTED",
        "required_consumption": False,
    }
    context["us_market_digest_plan"]["items"] = items

    rendered = render_us_full_market_message(context)

    assert rendered.status == "PASS"
    assert "🌐 보조 시장환경" not in rendered.text
    assert "변화 없음했습니다" not in rendered.text
