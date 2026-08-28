from __future__ import annotations

from app.services.kr_price_structure_selective_rollout_service import (
    KrPriceStructureEligibility,
)
from app.services.us_price_structure_selective_rollout_service import (
    build_us_price_structure_rollout_decision,
)


def _zone(
    zone_id: str,
    low: float,
    high: float,
    display: str,
    *,
    tier: str = "NEAR",
    relevance: str = "ACTIVE_NEAR",
) -> dict[str, object]:
    role = "RESISTANCE" if "resistance" in zone_id else "SUPPORT"
    return {
        "zone_id": zone_id,
        "raw_low": str(low),
        "raw_high": str(high),
        "display": display,
        "currency": "USD",
        "source_refs": [f"source:{zone_id}"],
        "source_timeframe": "weekly",
        "source_timeframes": ["weekly"],
        "distance_pct": "2.0",
        "proximity_tier": tier,
        "active_relevance": relevance,
        "current_role": role,
    }


def _context(*, family_consensus_safe: bool = True) -> dict[str, object]:
    return {
        "ticker": "MU",
        "market": "US",
        "as_of": "2026-08-27",
        "current_price": "126.50",
        "currency": "USD",
        "selection_errors": [],
        "partial_bar_used_for_pivot_confirmation": 0,
        "family_consensus_safe": family_consensus_safe,
        "summary": {
            "nearest_support": {
                "zone": _zone("nearest-support", 121.0, 123.5, "$121.00~$123.50")
            },
            "nearest_resistance": {
                "zone": _zone(
                    "nearest-resistance", 129.0, 132.0, "$129.00~$132.00"
                )
            },
            "major_structural_support": {
                "zone": _zone("major-support", 112.0, 116.0, "$112.00~$116.00")
            },
            "major_structural_resistance": {
                "zone": _zone(
                    "major-resistance", 139.0, 145.0, "$139.00~$145.00"
                )
            },
            "fib_sr_confluence": _zone(
                "fib-confluence", 130.0, 133.0, "$130.00~$133.00"
            ),
            "fib_sr_confluence_state": "DIRECT_SR_CONFLUENCE",
        },
    }


def test_eligible_us_subject_renders_backend_owned_usd_structure() -> None:
    decision = build_us_price_structure_rollout_decision(
        _context(), ticker="MU", monitored_subject=True, enabled=True
    )

    assert decision.eligibility == KrPriceStructureEligibility.ELIGIBLE
    assert decision.section is not None
    assert "기준 종가: $126.50" in decision.section
    assert "가까운 지지: $121.00~$123.50" in decision.section
    assert "가까운 저항: $129.00~$132.00" in decision.section
    assert "Fib/SR 겹침: $130.00~$133.00" in decision.section
    assert {item["fact_ref"] for item in decision.numeric_bindings} == {
        "nearest-support",
        "nearest-resistance",
        "major-support",
        "major-resistance",
        "fib-confluence",
        "current-price:MU:2026-08-27",
    }
    assert "목표" not in decision.section
    assert "손절" not in decision.section


def test_us_sr_only_and_safe_omit_are_not_failures() -> None:
    sr_only = build_us_price_structure_rollout_decision(
        _context(family_consensus_safe=False),
        ticker="TSLA",
        monitored_subject=True,
        enabled=True,
    )
    omitted = build_us_price_structure_rollout_decision(
        {**_context(), "summary": {}},
        ticker="RXRX",
        monitored_subject=True,
        enabled=True,
    )

    assert sr_only.eligibility == KrPriceStructureEligibility.ELIGIBLE_SR_ONLY
    assert sr_only.section is not None
    assert "Fib" not in sr_only.section
    assert omitted.eligibility == KrPriceStructureEligibility.OMIT_PRICE_STRUCTURE
    assert omitted.section is None


def test_us_rollout_is_market_scoped_and_default_off() -> None:
    disabled = build_us_price_structure_rollout_decision(
        _context(), ticker="MU", monitored_subject=True, enabled=False
    )
    kr = build_us_price_structure_rollout_decision(
        {**_context(), "market": "KR"},
        ticker="005930",
        monitored_subject=True,
        enabled=True,
    )
    unmonitored = build_us_price_structure_rollout_decision(
        _context(), ticker="MU", monitored_subject=False, enabled=True
    )

    assert disabled.section is None
    assert disabled.denial_reasons == ("us_price_structure_rollout_disabled",)
    assert "us_market_scope_required" in kr.denial_reasons
    assert "subject_outside_monitored_us_universe" in unmonitored.denial_reasons


def test_partial_bar_or_selection_error_blocks_us_render() -> None:
    partial = build_us_price_structure_rollout_decision(
        {**_context(), "partial_bar_used_for_pivot_confirmation": 1},
        ticker="TSM",
        monitored_subject=True,
        enabled=True,
    )
    future = build_us_price_structure_rollout_decision(
        {**_context(), "selection_errors": ["future_endpoint"]},
        ticker="SKHY",
        monitored_subject=True,
        enabled=True,
    )

    assert partial.eligibility == KrPriceStructureEligibility.BLOCKED
    assert partial.section is None
    assert future.eligibility == KrPriceStructureEligibility.BLOCKED
    assert future.section is None
