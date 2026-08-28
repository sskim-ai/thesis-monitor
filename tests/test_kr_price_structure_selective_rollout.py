from __future__ import annotations

from app.services.kr_price_structure_selective_rollout_service import (
    KrPriceStructureEligibility,
    apply_current_price_structure_section,
    build_kr_price_structure_rollout_decision,
    extract_current_price_structure_section,
    preserve_current_price_structure_section,
    preserve_price_structure_sections,
    replace_legacy_price_surface,
    suppress_current_price_structure_surface,
)


def _zone(
    zone_id: str,
    low: int,
    high: int,
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
        "currency": "KRW",
        "source_refs": [f"source:{zone_id}"],
        "source_families": ["PIVOT_WEEKLY"],
        "price_anchor_refs": [f"source:{zone_id}"],
        "source_timeframe": "weekly",
        "source_timeframes": ["weekly"],
        "distance_pct": "2.0",
        "proximity_tier": tier,
        "active_relevance": relevance,
        "current_role": role,
        "as_of": "2026-08-27",
    }


def _context(*, family_consensus_safe: bool = True) -> dict[str, object]:
    return {
        "ticker": "005490",
        "market": "KR",
        "as_of": "2026-08-27",
        "current_price": "328000",
        "currency": "KRW",
        "selection_errors": [],
        "partial_bar_used_for_pivot_confirmation": 0,
        "family_consensus_safe": family_consensus_safe,
        "summary": {
            "nearest_support": {
                "zone": _zone("nearest-support", 318000, 326000, "약 31.8만~32.6만원")
            },
            "nearest_resistance": {
                "zone": _zone("nearest-resistance", 330000, 342000, "약 33만~34.2만원")
            },
            "major_structural_support": {
                "zone": _zone("major-support", 308000, 317000, "약 30.8만~31.7만원")
            },
            "major_structural_resistance": {
                "zone": _zone("major-resistance", 425000, 438000, "약 42.5만~43.8만원")
            },
            "fib_sr_confluence": _zone(
                "fib-confluence",
                386000,
                396000,
                "약 38.6만~39.6만원",
            ),
            "fib_sr_confluence_state": "DIRECT_SR_CONFLUENCE",
        },
    }


def test_eligible_kr_subject_renders_nearest_major_and_safe_fib() -> None:
    decision = build_kr_price_structure_rollout_decision(
        _context(),
        ticker="005490",
        monitored_subject=True,
        enabled=True,
    )

    assert decision.eligibility == KrPriceStructureEligibility.ELIGIBLE
    assert decision.section is not None
    assert "가격 구조 기준 종가(정규장): 328,000원" in decision.section
    assert "가까운 지지: 약 31.8만~32.6만원" in decision.section
    assert "가까운 저항: 약 33만~34.2만원" in decision.section
    assert "주요 구조 지지: 약 30.8만~31.7만원" in decision.section
    assert "주요 구조 저항: 약 42.5만~43.8만원" in decision.section
    assert "Fib/SR 겹침: 약 38.6만~39.6만원" in decision.section
    assert {item["fact_ref"] for item in decision.numeric_bindings} == {
        "nearest-support",
        "nearest-resistance",
        "major-support",
        "major-resistance",
        "fib-confluence",
        "structure-close:005490:2026-08-27",
    }
    assert "목표" not in decision.section
    assert "손절" not in decision.section


def test_sr_only_suppresses_unproven_fib_without_empty_placeholder() -> None:
    decision = build_kr_price_structure_rollout_decision(
        _context(family_consensus_safe=False),
        ticker="005490",
        monitored_subject=True,
        enabled=True,
    )

    assert decision.eligibility == KrPriceStructureEligibility.ELIGIBLE_SR_ONLY
    assert decision.section is not None
    assert "가까운 지지" in decision.section
    assert "가까운 저항" in decision.section
    assert "Fib" not in decision.section
    assert all(
        item["semantic_type"] != "FIB_SR_CONFLUENCE"
        for item in decision.numeric_bindings
    )


def test_disabled_or_out_of_scope_subject_never_renders() -> None:
    disabled = build_kr_price_structure_rollout_decision(
        _context(),
        ticker="005490",
        monitored_subject=True,
        enabled=False,
    )
    us = build_kr_price_structure_rollout_decision(
        {**_context(), "market": "US"},
        ticker="MU",
        monitored_subject=True,
        enabled=True,
    )
    unmonitored = build_kr_price_structure_rollout_decision(
        _context(),
        ticker="005490",
        monitored_subject=False,
        enabled=True,
    )

    assert disabled.section is None
    assert disabled.denial_reasons == ("kr_price_structure_rollout_disabled",)
    assert us.section is None
    assert "kr_market_scope_required" in us.denial_reasons
    assert unmonitored.section is None
    assert "subject_outside_monitored_kr_universe" in unmonitored.denial_reasons


def test_omit_and_blocked_states_do_not_fail_the_stock_message() -> None:
    omitted_context = {**_context(), "summary": {}}
    blocked_context = {**_context(), "selection_errors": ["future_endpoint"]}

    omitted = build_kr_price_structure_rollout_decision(
        omitted_context,
        ticker="005490",
        monitored_subject=True,
        enabled=True,
    )
    blocked = build_kr_price_structure_rollout_decision(
        blocked_context,
        ticker="005490",
        monitored_subject=True,
        enabled=True,
    )

    assert omitted.eligibility == KrPriceStructureEligibility.OMIT_PRICE_STRUCTURE
    assert omitted.section is None
    assert blocked.eligibility == KrPriceStructureEligibility.BLOCKED
    assert blocked.section is None


def test_partial_bar_pivot_confirmation_blocks_rendering() -> None:
    context = {**_context(), "partial_bar_used_for_pivot_confirmation": 1}

    decision = build_kr_price_structure_rollout_decision(
        context,
        ticker="005490",
        monitored_subject=True,
        enabled=True,
    )

    assert decision.eligibility == KrPriceStructureEligibility.BLOCKED
    assert decision.section is None


def test_relevant_and_long_horizon_nearest_receive_structural_labels() -> None:
    context = _context(family_consensus_safe=False)
    summary = context["summary"]
    summary["nearest_support"] = {
        "zone": _zone(
            "nearest-support",
            198000,
            200000,
            "약 19.8만~20만원",
            tier="RELEVANT",
            relevance="ACTIVE_STRUCTURAL",
        )
    }
    summary["nearest_resistance"] = {
        "zone": _zone(
            "nearest-resistance",
            452000,
            460000,
            "약 45.2만~46만원",
            tier="LONG_HORIZON",
            relevance="LONG_HORIZON_HISTORICAL",
        )
    }

    decision = build_kr_price_structure_rollout_decision(
        context,
        ticker="005930",
        monitored_subject=True,
        enabled=True,
    )

    assert decision.section is not None
    assert "가까운 지지" not in decision.section
    assert "가까운 저항" not in decision.section
    assert "주요 구조 지지: 약 19.8만~20만원" in decision.section
    assert "장기 구조 저항: 약 45.2만~46만원" in decision.section
    assert decision.render_validation_errors == ()


def test_all_failed_coverage_blocks_but_safe_higher_timeframe_allows_sr() -> None:
    failed = {
        **_context(family_consensus_safe=False),
        "coverage": {
            timeframe: {"status": "FAIL", "completed_count": 0}
            for timeframe in ("daily", "weekly", "monthly")
        },
    }
    higher_timeframe_safe = {
        **failed,
        "coverage": {
            "daily": {"status": "FAIL", "completed_count": 0},
            "weekly": {"status": "PARTIAL", "completed_count": 599},
            "monthly": {"status": "PARTIAL", "completed_count": 299},
        },
    }

    blocked = build_kr_price_structure_rollout_decision(
        failed,
        ticker="005490",
        monitored_subject=True,
        enabled=True,
    )
    allowed = build_kr_price_structure_rollout_decision(
        higher_timeframe_safe,
        ticker="005490",
        monitored_subject=True,
        enabled=True,
    )

    assert blocked.eligibility == KrPriceStructureEligibility.BLOCKED
    assert blocked.section is None
    assert allowed.eligibility == KrPriceStructureEligibility.ELIGIBLE_SR_ONLY
    assert allowed.section is not None


def test_verified_provider_limit_partial_safe_allows_sr_without_claiming_full() -> None:
    context = {
        **_context(family_consensus_safe=False),
        "coverage": {
            "daily": {
                "status": "PARTIAL_SAFE",
                "requested_count": 1200,
                "completed_count": 1000,
                "provider_limit": 1000,
                "provider_limit_hit": True,
                "denial_reason": "provider_limit",
            },
            "weekly": {"status": "PARTIAL", "completed_count": 599},
            "monthly": {"status": "PARTIAL", "completed_count": 299},
        },
    }

    decision = build_kr_price_structure_rollout_decision(
        context,
        ticker="005930",
        monitored_subject=True,
        enabled=True,
    )

    assert decision.eligibility == KrPriceStructureEligibility.ELIGIBLE_SR_ONLY
    assert decision.section is not None
    assert context["coverage"]["daily"]["status"] != "PASS"


def test_current_structure_is_inserted_before_separate_stored_rules() -> None:
    message = """🏢 POSCO홀딩스(005490)

💰 가격
현재가: 328,000원

🧭 기존 등록 가격 규칙
• 기존 확인선 350,000원

📐 Valuation
현재 Valuation: 중립"""
    section = build_kr_price_structure_rollout_decision(
        _context(family_consensus_safe=False),
        ticker="005490",
        monitored_subject=True,
        enabled=True,
    ).section
    assert section is not None

    rendered = apply_current_price_structure_section(message, section)

    assert rendered.index("📐 현재 가격 구조") < rendered.index(
        "🧭 기존 등록 가격 규칙"
    )
    assert extract_current_price_structure_section(rendered) == section
    preserved = preserve_current_price_structure_section(message, rendered)
    assert "💰 가격" not in preserved
    assert extract_current_price_structure_section(preserved) == section
    assert "🧭 기존 등록 가격 규칙" in preserved


def test_legacy_price_surface_is_replaced_and_registered_rule_is_relabelled() -> None:
    message = """🏢 POSCO홀딩스(005490)

💰 가격
현재가: 339,500원
신규 관찰자:
• 동적 지지: 333,398원~345,602원
보유자:
• 차트 무효화 가격: 326,277원
가격 규칙 이력:
• 등록 확인선 344,000원은 아직 도달하지 않았습니다.

📊 수급
외국인 순매수

📐 Valuation
현재 Valuation: 중립"""
    section = build_kr_price_structure_rollout_decision(
        _context(family_consensus_safe=False),
        ticker="005490",
        monitored_subject=True,
        enabled=True,
    ).section
    assert section is not None

    rendered = replace_legacy_price_surface(message, section)

    assert "동적 지지" not in rendered
    assert "차트 무효화 가격" not in rendered
    assert "📐 현재 가격 구조" in rendered
    assert "🧭 기존 등록 가격 규칙" in rendered
    assert "기존 확인선 344,000원" in rendered
    assert rendered.index("📐 현재 가격 구조") < rendered.index("📊 수급")


def test_price_structure_suppression_preserves_only_stored_rules() -> None:
    message = """🏢 Example

💰 가격
현재가: $10.00
가격 규칙 이력:
• 등록 확인선 $12.00

📊 수급
없음"""

    rendered = suppress_current_price_structure_surface(message)

    assert "현재가" not in rendered
    assert "💰 가격" not in rendered
    assert "🧭 기존 등록 가격 규칙" in rendered
    assert "기존 확인선 $12.00" in rendered


def test_adaptive_message_preserves_current_and_stored_sections_as_a_pair() -> None:
    adaptive = """🤖 AI 보조 종목 점검

🏢 POSCO홀딩스(005490)

🎯 판단
사업 판단입니다.

📊 수급
외국인 순매수

📌 다음 확인
• 실적 확인"""
    reference = """🏢 POSCO홀딩스(005490)

📐 현재 가격 구조
• 기준 종가: 328,000원
• 가까운 지지: 약 31.8만~32.6만원

🧭 기존 등록 가격 규칙
• 기존 확인선 350,000원

📊 수급
외국인 순매수"""

    rendered = preserve_price_structure_sections(adaptive, reference)

    assert rendered.count("📐 현재 가격 구조") == 1
    assert rendered.count("🧭 기존 등록 가격 규칙") == 1
    assert rendered.index("📐 현재 가격 구조") < rendered.index(
        "🧭 기존 등록 가격 규칙"
    )
    assert rendered.index("🧭 기존 등록 가격 규칙") < rendered.index("📊 수급")
