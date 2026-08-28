from __future__ import annotations

import json
from pathlib import Path

from app.services.current_price_context_service import fallback_price_context_errors
from app.services.kr_price_structure_selective_rollout_service import (
    build_kr_price_structure_rollout_decision,
)
from app.services.price_structure_v3_renderer_service import (
    PriceStructureRender,
    render_current_price_structure,
    validate_price_structure_render,
)


FIXTURE = (
    Path(__file__).parent
    / "fixtures"
    / "run44_000660_v3_validator_incident.json"
)


def _run44_fixture() -> dict[str, object]:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def _partial_bollinger(
    zone_id: str,
    *,
    role: str,
    timeframe: str,
    low: str,
    high: str,
) -> dict[str, object]:
    return {
        "zone_id": zone_id,
        "raw_low": low,
        "raw_high": high,
        "display": f"약 ${low}~${high}",
        "currency": "USD",
        "source_refs": [f"source:{zone_id}"],
        "source_families": [f"PROVISIONAL_BOLLINGER_{timeframe.upper()}"],
        "price_anchor_refs": [],
        "source_timeframe": timeframe,
        "source_timeframes": [timeframe],
        "distance_pct": "8.0",
        "proximity_tier": "RELEVANT",
        "active_relevance": "ACTIVE_STRUCTURAL",
        "current_role": role,
        "as_of": "2026-08-28",
        "indicator_observation_dates": ["2026-08-28"],
        "indicator_bar_states": ["PARTIAL"],
        "observation_timestamps": ["2026-08-28T16:30:00-04:00"],
        "indicator_bar_starts": ["2026-08-03"],
        "indicator_bar_expected_closes": ["2026-08-31"],
    }


def _provisional_summary(
    *,
    support: dict[str, object] | None,
    resistance: dict[str, object] | None,
) -> dict[str, object]:
    unavailable = {"classification": "UNAVAILABLE", "zone": None}
    return {
        "nearest_support": unavailable,
        "nearest_resistance": unavailable,
        "major_structural_support": unavailable,
        "major_structural_resistance": unavailable,
        "dynamic_bollinger_support": None,
        "dynamic_bollinger_resistance": None,
        "provisional_bollinger_support": support,
        "provisional_bollinger_resistance": resistance,
        "fib_sr_confluence": None,
        "fib_sr_confluence_state": "UNAVAILABLE",
    }


def _render_provisional(
    summary: dict[str, object],
) -> PriceStructureRender:
    return render_current_price_structure(
        summary,
        ticker="TEST",
        as_of="2026-08-28",
        current_price="100",
        currency="USD",
        include_current_price=False,
        enforce_user_visible_proximity=True,
        security_basis="US:TEST",
        adjustment_basis="split_adjusted",
    )


def test_run44_intentional_dynamic_omission_does_not_fail_legacy_validator() -> None:
    incident = _run44_fixture()
    context = incident["price_structure_v3"]
    decision = build_kr_price_structure_rollout_decision(
        context,
        ticker="000660",
        monitored_subject=True,
        enabled=True,
    )

    assert incident["packet_id"] == "2026-08-28-kr-run-44-4606feed1396"
    assert decision.render_validation_errors == ()
    assert "• 가까운 지지: 약 159.2만~160.6만원 · 일봉 볼린저 중첩" in (
        decision.section or ""
    )
    assert "약 186.7만~187.7만원" not in (decision.section or "")
    assert "v3-zone:4b6cff0ad3bea3ef381d" not in decision.displayed_zone_ids
    assert fallback_price_context_errors(
        incident["current_price_context"],
        decision.section or "",
        validated_v3_render=True,
    ) == []


def test_run44_selected_confluence_is_required_by_v3_validator() -> None:
    incident = _run44_fixture()
    context = incident["price_structure_v3"]
    decision = build_kr_price_structure_rollout_decision(
        context,
        ticker="000660",
        monitored_subject=True,
        enabled=True,
    )
    assert decision.section is not None
    broken = PriceStructureRender(
        section=decision.section.replace(" · 일봉 볼린저 중첩", ""),
        numeric_bindings=decision.numeric_bindings,
        confluence_decision=None,
        displayed_zone_ids=decision.displayed_zone_ids,
    )

    validation = validate_price_structure_render(broken)

    assert validation.status == "FAIL"
    assert any(
        error.startswith("dynamic_bollinger_confluence_label_missing:")
        for error in validation.errors
    )


def test_selected_dynamic_resistance_missing_fails_validation() -> None:
    incident = _run44_fixture()
    context = incident["price_structure_v3"]
    dynamic_resistance = context["summary"]["dynamic_bollinger_resistance"]
    summary = {
        "nearest_support": {"classification": "UNAVAILABLE", "zone": None},
        "nearest_resistance": {"classification": "UNAVAILABLE", "zone": None},
        "major_structural_support": {
            "classification": "UNAVAILABLE",
            "zone": None,
        },
        "major_structural_resistance": {
            "classification": "UNAVAILABLE",
            "zone": None,
        },
        "dynamic_bollinger_support": None,
        "dynamic_bollinger_resistance": dynamic_resistance,
        "provisional_bollinger_support": None,
        "provisional_bollinger_resistance": None,
        "fib_sr_confluence": None,
        "fib_sr_confluence_state": "UNAVAILABLE",
    }
    render = render_current_price_structure(
        summary,
        ticker="000660",
        as_of="2026-08-28",
        current_price="1653000",
        currency="KRW",
        include_current_price=False,
        enforce_user_visible_proximity=True,
        security_basis="KR:000660",
        adjustment_basis="adjusted_close",
    )
    broken = PriceStructureRender(
        section="📐 현재 가격 구조",
        numeric_bindings=render.numeric_bindings,
        confluence_decision=render.confluence_decision,
        displayed_zone_ids=render.displayed_zone_ids,
    )

    validation = validate_price_structure_render(broken)

    assert validation.status == "FAIL"
    assert validation.errors == (
        "render_binding_mismatch:DYNAMIC_BOLLINGER_RESISTANCE",
    )


def test_unselected_provisional_candidate_is_not_a_render_obligation() -> None:
    daily_support = _partial_bollinger(
        "provisional-daily-support",
        role="SUPPORT",
        timeframe="daily",
        low="90",
        high="92",
    )
    monthly_resistance = _partial_bollinger(
        "provisional-monthly-resistance",
        role="RESISTANCE",
        timeframe="monthly",
        low="120",
        high="125",
    )

    render = _render_provisional(
        _provisional_summary(
            support=daily_support,
            resistance=monthly_resistance,
        )
    )

    assert validate_price_structure_render(render).status == "PASS"
    assert "약 $120~$125" in render.section
    assert "약 $90~$92" not in render.section
    assert "provisional-daily-support" not in render.displayed_zone_ids


def test_selected_provisional_candidate_missing_fails_validation() -> None:
    monthly_resistance = _partial_bollinger(
        "provisional-monthly-resistance",
        role="RESISTANCE",
        timeframe="monthly",
        low="120",
        high="125",
    )
    render = _render_provisional(
        _provisional_summary(support=None, resistance=monthly_resistance)
    )
    broken = PriceStructureRender(
        section="📐 현재 가격 구조",
        numeric_bindings=render.numeric_bindings,
        confluence_decision=render.confluence_decision,
        displayed_zone_ids=render.displayed_zone_ids,
    )

    validation = validate_price_structure_render(broken)

    assert validation.status == "FAIL"
    assert validation.errors == (
        "provisional_bollinger_label_missing:provisional-monthly-resistance",
    )


def test_v3_off_preserves_legacy_dynamic_resistance_requirement() -> None:
    incident = _run44_fixture()
    errors = fallback_price_context_errors(
        incident["current_price_context"],
        "현재가 기준 차트 손익비는 계산하지 않습니다.",
        validated_v3_render=False,
    )

    assert errors == ["fallback_dynamic_resistance_not_rendered"]
