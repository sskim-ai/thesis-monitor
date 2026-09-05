from __future__ import annotations

from app.services.production_validation_policy_service import (
    RepetitionClass,
    RewriteDisposition,
    classify_repeated_span,
    evaluate_bounded_rewrite,
    evaluate_production_quality,
)


def _quality() -> dict[str, object]:
    return {
        "duplicate_threshold": 3,
        "numeric_label_quality": {
            "source_label_mismatch_count": 0,
            "instrument_label_mismatch_count": 0,
            "period_label_mismatch_count": 0,
            "zone_role_mismatch_count": 0,
            "redundant_authored_label_count": 0,
            "repeated_bound_label_count": 0,
            "postposition_mismatch_count": 0,
        },
        "message_set_completeness": {"passed": True},
        "observer_holder": [{"ticker": "A", "distinct": True}],
        "supply_routing": {
            "us_kr_style_horizon_count": 0,
            "generic_us_supply_count": 0,
            "generic_us_investor_flow_unknown_count": 0,
        },
        "kr_supply_numeric_coverage": [],
        "numeric_ownership": {"hard_checks_passed": True},
        "numeric_primary_ownership": {"hard_checks_passed": True},
        "repeated_sentences": [],
        "template_skeleton_repeats": [],
    }


def test_benign_typed_repetition_is_soft_and_delivery_eligible() -> None:
    quality = _quality()
    quality["template_skeleton_repeats"] = [
        {"skeleton": "현재가는 <numeric> 수준입니다.", "stock_count": 14}
    ]
    decision = evaluate_production_quality(quality)

    assert decision["delivery_eligible"] is True
    assert decision["soft_quality_count"] > 0
    assert decision["semantic_hard_count"] == 0


def test_long_identical_rationale_across_different_evidence_stays_blocked() -> None:
    quality = _quality()
    quality["repeated_sentences"] = [
        {
            "sentence": (
                "서로 다른 사업 근거를 가진 종목인데도 장기간 동일한 원인과 결과를 "
                "반복해 개별 기업의 핵심 위험을 가리는 실질적인 논리를 그대로 사용합니다."
            ),
            "stock_count": 4,
            "evidence_signature_count": 4,
            "classification": "substantive",
        }
    ]
    decision = evaluate_production_quality(quality)

    assert decision["delivery_eligible"] is False
    assert "material_spam_repeat" in decision["semantic_hard"]


def test_numeric_basis_mismatch_remains_hard() -> None:
    quality = _quality()
    quality["numeric_label_quality"]["period_label_mismatch_count"] = 1  # type: ignore[index]
    decision = evaluate_production_quality(quality)

    assert decision["delivery_eligible"] is False
    assert decision["hard_deterministic_count"] == 1


def test_numeric_particle_error_is_soft_but_unknown_fact_is_hard() -> None:
    soft = evaluate_production_quality(
        _quality(),
        binding_errors=("A:numeric_fact_ref_raw_postposition:price:text",),
    )
    hard = evaluate_production_quality(
        _quality(),
        binding_errors=("A:numeric_fact_ref_source_not_found:price",),
    )

    assert soft["delivery_eligible"] is True
    assert hard["delivery_eligible"] is False


def test_repetition_taxonomy_preserves_required_and_material_classes() -> None:
    assert classify_repeated_span(
        "필수 안전 문구",
        stock_count=14,
        required_safety=True,
    ) == RepetitionClass.REQUIRED_SAFETY_REPEAT
    assert classify_repeated_span(
        "현재가는 <numeric> 수준입니다.",
        stock_count=14,
        typed_template=True,
    ) == RepetitionClass.BENIGN_TEMPLATE_REPEAT


def test_bounded_rewrite_preserves_all_structured_invariants() -> None:
    before = {
        "decision_fields": {"decision": "HOLD"},
        "claim_types": ["RISK_CONDITION"],
        "condition_expression_refs": ["K1"],
        "evidence_refs": ["E1"],
        "numeric_refs": ["N1"],
        "price_refs": ["P1"],
        "new_buyer_stance": "WAIT",
        "holder_stance": "HOLD",
        "severity": ["WEAKENING"],
        "text": "old",
    }
    after = {**before, "text": "new"}

    result = evaluate_bounded_rewrite(before, after, attempted=True)
    assert result.disposition == RewriteDisposition.SUCCEEDED
    assert result.class_ab_rerun_required is True


def test_failed_or_semantically_changed_rewrite_keeps_safe_original() -> None:
    failed = evaluate_bounded_rewrite({}, None, attempted=True)
    changed = evaluate_bounded_rewrite(
        {"decision_fields": "HOLD"},
        {"decision_fields": "SELL"},
        attempted=True,
    )

    assert failed.disposition == RewriteDisposition.FAILED_KEEP_ORIGINAL
    assert failed.original_remains_eligible is True
    assert changed.disposition == RewriteDisposition.REJECTED_INVARIANCE
    assert changed.original_remains_eligible is True


def test_rewrite_attempt_is_bounded_to_one() -> None:
    result = evaluate_bounded_rewrite({}, {}, attempted=True, attempt_count=2)
    assert result.invariant_errors == ("rewrite_attempt_limit",)
    assert result.attempt_count == 1
