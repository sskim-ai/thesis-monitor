from __future__ import annotations

from datetime import date, timedelta

from app.services.cross_market_decision_engine_service import (
    DecisionCandidate,
    EvidenceCategory,
    EvidenceClaim,
    build_decision_evidence_packet,
    canonicalize_candidate_metadata,
    decision_message_quality,
    render_shadow_decision,
    validate_decision_candidate,
)
from app.services.logical_condition_service import (
    ClaimLogicalCondition,
    LogicalCoverageMode,
    LogicalOperator,
    source_claim_expression,
)
from app.services.ohlcv_feature_engine_service import build_multi_timeframe_feature_packet


def _bars(count: int) -> list[dict[str, object]]:
    return [
        {
            "date": (date(2025, 1, 1) + timedelta(days=index)).isoformat(),
            "open": 100 + index,
            "high": 101 + index,
            "low": 99 + index,
            "close": 100 + index,
            "volume": 1_000_000 + index,
        }
        for index in range(count)
    ]


def _packet_and_candidate() -> tuple[object, DecisionCandidate]:
    technical = build_multi_timeframe_feature_packet(
        ticker="TEST",
        periods={"daily": _bars(260), "weekly": _bars(120), "monthly": _bars(80)},
        cutoff=date(2026, 1, 1),
    )
    packet = build_decision_evidence_packet(
        packet={
            "packet_id": "2026-01-01-us-run-test",
            "market": "us",
            "assessment_date": "2026-01-01",
        },
        stock={
            "ticker": "TEST",
            "company_name": "Test Corp",
            "thesis": {
                "core_thesis": "반복 매출과 수익성 회복이 장기 논리의 중심이다.",
                "time_horizon": "12-24개월",
                "strengthen_signals": ["수익성 회복이 현금창출과 함께 이어지는 경우"],
                "weaken_signals": ["수요 둔화와 마진 하락이 함께 확인되는 경우"],
                "invalidation_signals": ["핵심 고객 기반이 구조적으로 훼손되는 경우"],
                "market_expectations": {"summary": "회복 기대가 주가에 반영되어 있다."},
                "macro_exposures": [{"factor": "금리", "direction": "negative"}],
            },
            "unknowns": ["회복의 지속성은 다음 정식 실적에서 확인이 필요하다."],
            "market_transmission": {"state": "neutral"},
            "current_price_context": {"state": "above_support"},
            "fact_catalog": [
                {
                    "fact_id": "earnings:latest",
                    "fact_type": "earnings",
                    "as_of_date": "2026-01-01",
                    "fields": {"trend": "improving"},
                },
                {
                    "fact_id": "valuation:current",
                    "fact_type": "valuation",
                    "as_of_date": "2026-01-01",
                    "fields": {"context": "expectations_elevated"},
                },
            ],
            "data_cautions": [],
        },
        technical_features=technical,
    )
    by_category = {}
    for ref in packet.evidence:
        by_category.setdefault(ref.category, ref.ref_id)
    numeric_ref = next(
        ref.ref_id
        for ref in packet.evidence
        if ref.category == EvidenceCategory.TECHNICAL_FEATURE
        and ref.label == "daily:return_20"
    )
    candidate = DecisionCandidate(
        ticker="TEST",
        decision="HOLD",
        reasoning_grade="VERY_HIGH",
        confidence="MEDIUM",
        confidence_reason="MATERIAL_EVIDENCE_CONFLICT",
        horizon="12-24개월",
        timing="NEUTRAL",
        timing_basis=EvidenceClaim(
            text="확인 가능한 가격 구조가 진입에 일방적인 우호 또는 불리 신호를 주지 않는다.",
            evidence_refs=(by_category[EvidenceCategory.PRICE_STRUCTURE],),
        ),
        hold_reason="BALANCED_EVIDENCE",
        decisive_reason=EvidenceClaim(
            text="사업 회복 논리는 유효하지만 현재 기대와 남은 검증 부담이 균형을 이룬다.",
            evidence_refs=(
                by_category[EvidenceCategory.THESIS],
                by_category[EvidenceCategory.EXPECTATIONS],
            ),
        ),
        why_not_buy=EvidenceClaim(
            text="회복 기대가 먼저 반영돼 추가 상승 비대칭이 아직 충분하지 않다.",
            evidence_refs=(by_category[EvidenceCategory.EXPECTATIONS],),
        ),
        why_not_sell=EvidenceClaim(
            text="반복 매출과 수익성 회복 가능성이 하방 우위를 확정하지 못하게 한다.",
            evidence_refs=(by_category[EvidenceCategory.THESIS],),
        ),
        supporting_evidence=(
            EvidenceClaim(
                text="확인된 실적 방향과 가격 추세는 논리의 유지와 양립한다.",
                evidence_refs=(
                    by_category[EvidenceCategory.EARNINGS],
                    numeric_ref,
                ),
            ),
        ),
        opposing_evidence=(
            EvidenceClaim(
                text="회복 기대가 먼저 반영되어 실적 검증 전 추가 확신은 제한된다.",
                evidence_refs=(by_category[EvidenceCategory.RISKS],),
            ),
        ),
        unknowns=(
            EvidenceClaim(
                text="회복의 지속성은 다음 정식 실적에서 확인해야 한다.",
                evidence_refs=(by_category[EvidenceCategory.UNKNOWN],),
            ),
        ),
        upgrade_condition=EvidenceClaim(
            text="현금창출을 동반한 수익성 회복이 이어지면 상향 판단을 재검토한다.",
            evidence_refs=(by_category[EvidenceCategory.THESIS],),
        ),
        downgrade_condition=EvidenceClaim(
            text="수요 둔화와 마진 하락이 함께 확인되면 하향 판단을 재검토한다.",
            evidence_refs=(by_category[EvidenceCategory.RISKS],),
        ),
        selected_numeric_fact_refs=(numeric_ref,),
        selected_evidence_plan=(
            EvidenceCategory.THESIS,
            EvidenceCategory.EARNINGS,
            EvidenceCategory.EXPECTATIONS,
            EvidenceCategory.RISKS,
            EvidenceCategory.UNKNOWN,
            EvidenceCategory.PRICE_STRUCTURE,
            EvidenceCategory.TECHNICAL_FEATURE,
        ),
    )
    return packet, candidate


def test_valid_ai_owned_candidate_renders_with_backend_numeric_binding() -> None:
    packet, candidate = _packet_and_candidate()
    validation = validate_decision_candidate(packet, candidate)
    assert validation.valid is True
    assert validation.numeric_claim_count == 1
    assert validation.automatically_bound_numeric_count == 1
    rendered = render_shadow_decision(packet, candidate)
    assert "AI 종합 판단: HOLD" in rendered.text
    assert "왜 BUY가 아닌가" in rendered.text
    assert "왜 SELL이 아닌가" in rendered.text
    assert "추론등급: 매우 높음" in rendered.text
    assert "판단 확신도: 중간" in rendered.text
    assert "판단 기준: 핵심 근거 충돌" in rendered.text
    assert "단기 타이밍: 중립" in rendered.text
    assert "상향 조건:" in rendered.text
    assert "하향 조건:" in rendered.text
    assert "주문 또는 자동매매 지시가 아닙니다" in rendered.text
    assert decision_message_quality([rendered])["status"] == "PASS"


def test_candidate_rejects_freeform_numbers_orders_and_unsupported_metrics() -> None:
    packet, candidate = _packet_and_candidate()
    broken = candidate.model_copy(
        update={
            "decisive_reason": EvidenceClaim(
                text="지금 시장가 주문으로 전량 매수하고 FCF yield 5%를 기대한다.",
                evidence_refs=candidate.decisive_reason.evidence_refs,
            )
        }
    )
    errors = validate_decision_candidate(packet, broken).errors
    assert "automated_trade_or_order_language" in errors
    assert "unsupported_metric_or_inference" in errors
    assert "freeform_exact_numeric_claim" in errors


def test_candidate_rejects_unknown_refs_and_unowned_horizon() -> None:
    packet, candidate = _packet_and_candidate()
    broken = candidate.model_copy(
        update={
            "horizon": "1개월",
            "unknowns": (
                EvidenceClaim(text="근거가 없다.", evidence_refs=("missing:ref",)),
            ),
        }
    )
    errors = validate_decision_candidate(packet, broken).errors
    assert "horizon_not_owned_by_monitoring_thesis" in errors
    assert "unknown_evidence_ref:missing:ref" in errors


def test_category_plan_is_backend_derived_from_ai_selected_refs() -> None:
    packet, candidate = _packet_and_candidate()
    incomplete = candidate.model_copy(
        update={"selected_evidence_plan": (EvidenceCategory.THESIS,)}
    )
    assert "selected_evidence_plan_incomplete" in validate_decision_candidate(
        packet, incomplete
    ).errors
    normalized = canonicalize_candidate_metadata(packet, incomplete)
    assert validate_decision_candidate(packet, normalized).valid is True


def test_hold_requires_reason_and_directional_decisions_reject_hold_reason() -> None:
    packet, candidate = _packet_and_candidate()
    missing = candidate.model_copy(update={"hold_reason": "NOT_HOLD"})
    assert "hold_reason_missing" in validate_decision_candidate(packet, missing).errors

    directional = candidate.model_copy(
        update={"decision": "SELL", "hold_reason": "OPTIONALITY_OFFSETS_DOWNSIDE"}
    )
    assert "hold_reason_present_for_directional_decision" in validate_decision_candidate(
        packet, directional
    ).errors


def test_timing_and_confidence_require_independent_evidence_basis() -> None:
    packet, candidate = _packet_and_candidate()
    non_timing = candidate.model_copy(
        update={
            "timing": "UNFAVORABLE",
            "timing_basis": candidate.why_not_buy,
        }
    )
    assert "directional_timing_without_usable_evidence" in validate_decision_candidate(
        packet, non_timing
    ).errors

    unsupported_high = candidate.model_copy(
        update={"confidence": "HIGH", "confidence_reason": "DATA_QUALITY_LIMIT"}
    )
    assert "high_confidence_without_convergent_evidence" in validate_decision_candidate(
        packet, unsupported_high
    ).errors


def test_change_conditions_must_be_asymmetric_and_evidence_owned() -> None:
    packet, candidate = _packet_and_candidate()
    symmetric = candidate.model_copy(
        update={"downgrade_condition": candidate.upgrade_condition}
    )
    assert "symmetric_decision_change_conditions" in validate_decision_candidate(
        packet, symmetric
    ).errors

    unowned = candidate.model_copy(
        update={
            "downgrade_condition": EvidenceClaim(
                text="하방 조건을 점검한다.", evidence_refs=("missing:condition",)
            )
        }
    )
    assert "unknown_evidence_ref:missing:condition" in validate_decision_candidate(
        packet, unowned
    ).errors


def test_source_owned_or_condition_survives_packet_and_candidate_validation() -> None:
    packet, candidate = _packet_and_candidate()
    source = next(
        ref
        for ref in packet.evidence
        if ref.label == "무효화 조건" and ref.logical_condition is not None
    )
    logical = source.logical_condition
    assert logical is not None
    assert logical.expression.type == LogicalOperator.LEAF

    source_packet = build_decision_evidence_packet(
        packet={
            "packet_id": "2026-01-01-us-run-logical",
            "market": "us",
            "assessment_date": "2026-01-01",
        },
        stock={
            "ticker": "GENERIC",
            "thesis": {
                "core_thesis": "계약 전환이 장기 논리의 중심이다.",
                "invalidation_signals": ["계약 취소 또는 반복적인 준공 실패"],
            },
        },
    )
    source_ref = next(
        ref
        for ref in source_packet.evidence
        if ref.label == "무효화 조건" and ref.logical_condition is not None
    )
    source_logical = source_ref.logical_condition
    assert source_logical is not None
    assert source_logical.expression.type == LogicalOperator.ANY_OF

    valid_claim = EvidenceClaim(
        text="원천 무효화 조건을 그대로 재점검한다.",
        evidence_refs=(source_ref.ref_id,),
        logical_condition=ClaimLogicalCondition(
            source_condition_ref=source_logical.expression.condition_id,
            coverage_mode=LogicalCoverageMode.FULL,
            severity=source_logical.severity,
            expression=source_claim_expression(source_logical.expression),
        ),
    )
    generic_candidate = candidate.model_copy(
        update={"ticker": "GENERIC", "downgrade_condition": valid_claim}
    )
    errors = validate_decision_candidate(source_packet, generic_candidate).errors
    assert not any(error.startswith("logical_condition_") for error in errors)

    narrowed = valid_claim.logical_condition
    assert narrowed is not None
    narrowed = narrowed.model_copy(
        update={
            "expression": narrowed.expression.model_copy(
                update={"type": LogicalOperator.ALL_OF}
            )
        }
    )
    broken = generic_candidate.model_copy(
        update={
            "downgrade_condition": valid_claim.model_copy(
                update={"logical_condition": narrowed}
            )
        }
    )
    assert "logical_condition_full_semantic_mismatch" in validate_decision_candidate(
        source_packet, broken
    ).errors
