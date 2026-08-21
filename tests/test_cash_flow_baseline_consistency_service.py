from datetime import date
from decimal import Decimal

from app.services.cash_flow_baseline_consistency_service import (
    BaselineCashFlowClaim,
    CanonicalCashFlowEvidence,
    CanonicalMetricEvidence,
    ClaimScope,
    ClaimState,
    ConsistencyResult,
    RenderAction,
    evaluate_baseline_cash_flow_claim,
    extract_baseline_cash_flow_claims,
    financial_period_context,
    repair_baseline_cash_flow_text,
    rendered_message_cash_flow_sections,
)


def _metric(
    value: str,
    *,
    metric: str = "free_cash_flow_ppe",
    period_type: str = "YTD",
) -> CanonicalMetricEvidence:
    amount = Decimal(value)
    return CanonicalMetricEvidence(
        fact_id=f"fact:{metric}:{value}:{period_type}",
        metric=metric,
        value=amount,
        sign=ClaimState.POSITIVE if amount >= 0 else ClaimState.NEGATIVE,
        period_start=date(2026, 1, 1),
        period_end=date(2026, 6, 30),
        period_type=period_type,
        fiscal_year=2026,
        fiscal_quarter=2,
        scope=(
            ClaimScope.BACKEND_PPE_ONLY
            if metric == "free_cash_flow_ppe"
            else ClaimScope.UNKNOWN
        ),
        entity_scope="issuer_level",
        currency="USD",
        unit="USD",
        filing_date=date(2026, 7, 23),
    )


def _evidence(
    fcf: str | None,
    *,
    ocf: str | None = None,
    freshness: str = "CURRENT_FORMAL",
) -> CanonicalCashFlowEvidence:
    return CanonicalCashFlowEvidence(
        ticker="TEST",
        freshness_state=freshness,
        fcf=_metric(fcf) if fcf is not None else None,
        ocf=(
            _metric(ocf, metric="operating_cash_flow")
            if ocf is not None
            else None
        ),
    )


def _claim(
    text: str,
    *,
    section: str = "core_thesis",
    provenance_valid: bool = False,
) -> BaselineCashFlowClaim:
    claims = extract_baseline_cash_flow_claims(
        "TEST",
        text,
        text_ref="test.text",
        section=section,
        origin_type="fixture",
        provenance_refs=("fact:source",) if provenance_valid else (),
        provenance_valid=provenance_valid,
    )
    assert len(claims) == 1
    return claims[0]


def test_current_positive_fcf_suppresses_unproven_negative_claim() -> None:
    decision = evaluate_baseline_cash_flow_claim(
        _claim("현재 FCF 적자입니다."),
        _evidence("10"),
    )

    assert decision.consistency_result == ConsistencyResult.UNSUPPORTED_CLAIM
    assert decision.render_action == RenderAction.SUPPRESS


def test_current_negative_fcf_requires_period_and_ppe_scope_qualifier() -> None:
    repair = repair_baseline_cash_flow_text(
        "TEST",
        "현재 FCF 적자입니다.",
        _evidence("-10"),
        text_ref="test.text",
        section="core_thesis",
        origin_type="fixture",
    )

    assert repair.decisions[0].consistency_result == ConsistencyResult.QUALIFIER_REQUIRED
    assert "2026 회계연도 상반기 누계 PPE 기준 FCF 적자" in repair.text


def test_explicit_historical_negative_claim_with_provenance_is_preserved() -> None:
    decision = evaluate_baseline_cash_flow_claim(
        _claim("2025년 FCF 적자였습니다.", provenance_valid=True),
        _evidence("10"),
    )

    assert decision.consistency_result == ConsistencyResult.NO_CANONICAL_CHECK_AVAILABLE
    assert decision.render_action == RenderAction.KEEP


def test_prior_negative_claim_without_period_is_not_current_substitute() -> None:
    decision = evaluate_baseline_cash_flow_claim(
        _claim("FCF 적자입니다."),
        _evidence("10"),
    )

    assert decision.render_action == RenderAction.SUPPRESS


def test_management_fcf_and_ppe_fcf_are_not_directly_compared() -> None:
    decision = evaluate_baseline_cash_flow_claim(
        _claim("회사 정의 FCF 적자입니다.", provenance_valid=True),
        _evidence("10"),
    )

    assert decision.consistency_result == ConsistencyResult.NOT_COMPARABLE
    assert decision.render_action == RenderAction.KEEP


def test_unknown_scope_claim_without_provenance_fails_closed() -> None:
    decision = evaluate_baseline_cash_flow_claim(
        _claim("현재 FCF 적자입니다."),
        _evidence(None),
    )

    assert decision.consistency_result == ConsistencyResult.UNSUPPORTED_CLAIM
    assert decision.render_action == RenderAction.SUPPRESS


def test_negative_ocf_does_not_create_negative_fcf() -> None:
    decision = evaluate_baseline_cash_flow_claim(
        _claim("현재 FCF 적자입니다."),
        _evidence(None, ocf="-20"),
    )

    assert decision.canonical_comparison_fact_id is None
    assert decision.render_action == RenderAction.SUPPRESS


def test_stale_fact_is_not_used_as_current_substitute() -> None:
    decision = evaluate_baseline_cash_flow_claim(
        _claim("현재 FCF 적자입니다."),
        _evidence("-10", freshness="STALE_FORMAL"),
    )

    assert decision.consistency_result == ConsistencyResult.UNSUPPORTED_CLAIM
    assert decision.render_action == RenderAction.SUPPRESS


def test_provenance_backed_claim_can_survive_without_canonical_check() -> None:
    decision = evaluate_baseline_cash_flow_claim(
        _claim("현재 FCF 적자입니다.", provenance_valid=True),
        _evidence(None),
    )

    assert decision.consistency_result == ConsistencyResult.NO_CANONICAL_CHECK_AVAILABLE
    assert decision.render_action == RenderAction.KEEP


def test_turn_positive_requirement_detects_implied_current_negative_state() -> None:
    decision = evaluate_baseline_cash_flow_claim(
        _claim("FCF 흑자 전환이 필요합니다."),
        _evidence("10"),
    )

    assert decision.consistency_result == ConsistencyResult.UNSUPPORTED_CLAIM
    assert decision.render_action == RenderAction.SUPPRESS


def test_negative_cash_burn_control_remains_consistent_with_negative_ocf() -> None:
    decision = evaluate_baseline_cash_flow_claim(
        _claim("현재 높은 현금소진이 이어집니다."),
        _evidence("-30", ocf="-20"),
    )

    assert decision.consistency_result == ConsistencyResult.CONSISTENT
    assert decision.render_action == RenderAction.KEEP


def test_cash_burn_metric_reference_is_not_treated_as_current_negative_state() -> None:
    claims = extract_baseline_cash_flow_claims(
        "TEST",
        "핵심 확인 지표는 현금소진과 희석입니다.",
        text_ref="test.text",
        section="validation_metrics",
        origin_type="fixture",
    )

    assert claims == ()


def test_unrelated_ttm_valuation_label_does_not_scope_fcf_claim() -> None:
    claim = _claim("현재 FCF 적자입니다.\nPER는 TTM EPS 기준입니다.")

    assert claim.period_type == "unknown"
    assert claim.claim_currentness.value == "explicit_current"


def test_rendered_watch_risk_keeps_future_ownership() -> None:
    sections = rendered_message_cash_flow_sections(
        "🎯 핵심\n현재 FCF 적자입니다.\n\n"
        "👁 핵심 감시\n• fleet 확대에도 손실과 현금소진 증가"
    )

    assert sections == (
        ("🎯 핵심", "core_thesis", "현재 FCF 적자입니다."),
        ("👁 핵심 감시", "persistent_risks", "• fleet 확대에도 손실과 현금소진 증가"),
    )
    core = evaluate_baseline_cash_flow_claim(
        _claim(sections[0][2], section=sections[0][1]),
        _evidence("10"),
    )
    watch = evaluate_baseline_cash_flow_claim(
        _claim(sections[1][2], section=sections[1][1]),
        _evidence("10"),
    )
    assert core.render_action == RenderAction.SUPPRESS
    assert watch.render_action == RenderAction.KEEP


def test_tsla_sentence_repair_preserves_non_cash_flow_reasoning() -> None:
    text = (
        "Robotaxi/FSD/AI의 고마진 수익화가 장기 기업가치의 핵심이다. "
        "현재는 매출·인도 회복에도 영업이익률 저하와 FCF 적자로 투자 논리에 "
        "초기 균열이 있으며, 향후 자동차·서비스 마진 회복, Robotaxi 경제성, "
        "FCF 흑자 전환이 증명되어야 한다."
    )
    repair = repair_baseline_cash_flow_text(
        "TEST",
        text,
        _evidence("352000000"),
        text_ref="thesis.core_thesis",
        section="core_thesis",
        origin_type="saved_thesis",
    )

    assert "FCF 적자" not in repair.text
    assert "FCF 흑자 전환" not in repair.text
    assert "영업이익률 저하로 투자 논리에 초기 균열" in repair.text
    assert "Robotaxi 경제성이 증명되어야 한다" in repair.text


def test_financial_period_context_normalizes_formal_and_preliminary_dates() -> None:
    formal, preliminary = financial_period_context(
        {
            "latest_full_financial_period": "2026-06-30",
            "latest_preliminary_financial_period": "2026-09-30",
        }
    )

    assert formal == date(2026, 6, 30)
    assert preliminary == date(2026, 9, 30)
