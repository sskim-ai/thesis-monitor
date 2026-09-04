from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.services.validation_policy_shadow_service import (
    AISemanticReviewerIssue,
    AISemanticReviewerResult,
    ClaimOwner,
    DecisionFields,
    EvidenceOwnership,
    NumericOwnership,
    RepetitionClass,
    RepetitionObservation,
    ReviewerVerdict,
    RewriteDisposition,
    SemanticClaimType,
    StructuredSemanticClaim,
    ValidationClass,
    classify_repetition,
    evaluate_bounded_rewrite,
    evaluate_shadow_policy,
    inventory_summary,
    rewrite_snapshot,
    validate_ai_semantic_reviewer,
    validate_structured_claims,
    validator_inventory,
)
from scripts.validation_semantic_ownership_shadow import _family


GENERATION = "2026-09-04:shadow:1"


def _decision(direction: str = "HOLD") -> DecisionFields:
    return DecisionFields(
        overall_direction=direction,
        new_buyer_stance="WAIT",
        holder_stance="HOLD",
        buy_balance=4.5,
        sell_balance=5.5,
    )


def _evidence() -> dict[str, EvidenceOwnership]:
    return {
        "E1": EvidenceOwnership(
            evidence_ref="E1",
            ticker="TEST",
            generation_id=GENERATION,
            semantic_family="capital_efficiency",
            metric="ROIC",
        ),
        "E2": EvidenceOwnership(
            evidence_ref="E2",
            ticker="TEST",
            generation_id=GENERATION,
            semantic_family="valuation",
            metric="PBR",
        ),
        "E_OLD": EvidenceOwnership(
            evidence_ref="E_OLD",
            ticker="TEST",
            generation_id=GENERATION,
            semantic_family="valuation",
            metric="PBR",
            current=False,
        ),
    }


def _numeric() -> dict[str, NumericOwnership]:
    return {
        "N1": NumericOwnership(
            numeric_ref="N1",
            evidence_ref="E2",
            field_path="fields.price_to_book",
            semantic_type="PBR",
            unit="multiple",
        )
    }


def _claim(**overrides: object) -> StructuredSemanticClaim:
    values: dict[str, object] = {
        "claim_id": "C1",
        "ticker": "TEST",
        "generation_id": GENERATION,
        "claim_type": SemanticClaimType.FUTURE_VALIDATION_CONDITION,
        "topic": "capital_efficiency",
        "metrics": ("ROIC",),
        "direction": "IMPROVE",
        "evidence_refs": ("E1",),
        "text_ref": "next_checks[0]",
        "text": "CAPEX가 현금창출과 ROIC 개선으로 이어지는지 확인해야 합니다.",
    }
    values.update(overrides)
    return StructuredSemanticClaim(**values)


def test_validator_inventory_is_complete_and_exclusive() -> None:
    rules = validator_inventory()
    summary = inventory_summary(rules)

    assert summary["rules_inventoried_pct"] == 100
    assert summary["unclassified_rules"] == 0
    assert summary["total"] == summary["unique_rule_ids"]
    assert set(summary["class_counts"]) == {item.value for item in ValidationClass}
    assert all(rule.production_gate_impact for rule in rules)
    assert all(rule.false_negative_risk for rule in rules)


@pytest.mark.parametrize(
    ("category", "expected"),
    [
        ("valuation", "valuation"),
        ("VALUATION", "valuation"),
        ("expectations", "market_expectation"),
        ("EXPECTATIONS", "market_expectation"),
    ],
)
def test_shadow_category_family_is_case_insensitive(
    category: str, expected: str
) -> None:
    assert _family(category) == expected


@pytest.mark.parametrize(
    ("claim_text", "claim_type"),
    [
        ("ROIC가 개선되면 재평가합니다.", SemanticClaimType.FUTURE_VALIDATION_CONDITION),
        ("ROIC 개선으로 이어져야 합니다.", SemanticClaimType.FUTURE_VALIDATION_CONDITION),
        ("ROIC 악화로 이어질 수 있습니다.", SemanticClaimType.RISK_CONDITION),
        ("향후 ROIC가 회복돼야 합니다.", SemanticClaimType.FUTURE_VALIDATION_CONDITION),
    ],
)
def test_temporal_metric_ownership_uses_metadata_not_korean_grammar(
    claim_text: str,
    claim_type: SemanticClaimType,
) -> None:
    result = validate_structured_claims(
        [_claim(text=claim_text, claim_type=claim_type)],
        evidence=_evidence(),
        numeric=_numeric(),
        decision=_decision(),
    )

    assert result.class_ab_passed is True
    assert result.temporal_grammar_required_for_metric_ownership == 0


def test_current_numeric_claim_is_bound_to_exact_semantic() -> None:
    result = validate_structured_claims(
        [
            _claim(
                claim_type=SemanticClaimType.CURRENT_NUMERIC_FACT,
                topic="valuation",
                metrics=("PBR",),
                evidence_refs=("E2",),
                numeric_refs=("N1",),
                text="현재 PBR은 {{numeric:N1}}입니다.",
            )
        ],
        evidence=_evidence(),
        numeric=_numeric(),
        decision=_decision(),
    )

    assert result.class_ab_passed is True
    assert result.freeform_unbound_numeric == 0


def test_unbound_number_is_a_class_a_failure() -> None:
    result = validate_structured_claims(
        [
            _claim(
                claim_type=SemanticClaimType.CURRENT_NUMERIC_FACT,
                topic="valuation",
                metrics=("ROIC",),
                evidence_refs=("E1",),
                text="현재 ROIC는 12%입니다.",
            )
        ],
        evidence=_evidence(),
        numeric=_numeric(),
        decision=_decision(),
    )

    assert result.class_ab_passed is False
    assert result.freeform_unbound_numeric == 1
    assert {item.code for item in result.hard_issues} >= {
        "freeform_unbound_numeric",
        "current_numeric_fact_without_numeric_ref",
    }


@pytest.mark.parametrize(
    ("bad_evidence", "code"),
    [
        (
            EvidenceOwnership(
                evidence_ref="BAD",
                ticker="OTHER",
                generation_id=GENERATION,
                semantic_family="earnings",
            ),
            "cross_ticker_evidence_ref",
        ),
        (
            EvidenceOwnership(
                evidence_ref="BAD",
                ticker="TEST",
                generation_id="other-generation",
                semantic_family="earnings",
            ),
            "cross_generation_evidence_ref",
        ),
    ],
)
def test_cross_owner_evidence_remains_class_a(
    bad_evidence: EvidenceOwnership,
    code: str,
) -> None:
    result = validate_structured_claims(
        [_claim(evidence_refs=("BAD",))],
        evidence={"BAD": bad_evidence},
        numeric={},
        decision=_decision(),
    )

    assert code in {item.code for item in result.hard_issues}
    assert all(item.validation_class == ValidationClass.HARD_DETERMINISTIC for item in result.hard_issues)


def test_historical_fact_cannot_be_asserted_current() -> None:
    result = validate_structured_claims(
        [
            _claim(
                claim_type=SemanticClaimType.CURRENT_FACT,
                topic="valuation",
                metrics=("PBR",),
                evidence_refs=("E_OLD",),
                text="현재 장부가 배수는 낮은 편입니다.",
            )
        ],
        evidence=_evidence(),
        numeric=_numeric(),
        decision=_decision(),
    )

    assert {item.code for item in result.semantic_issues} == {"historical_evidence_asserted_current"}


@pytest.mark.parametrize(
    "text",
    [
        "자동 매도보다 사업 재평가가 먼저입니다.",
        "무조건 매도할 구간은 아닙니다.",
        "자동 매도 조건이 아니라 확인 조건입니다.",
    ],
)
def test_trade_language_is_not_reparsed_when_metadata_is_non_mandatory(text: str) -> None:
    result = validate_structured_claims(
        [_claim(claim_type=SemanticClaimType.HOLDER_REASSESSMENT, text=text)],
        evidence=_evidence(),
        numeric=_numeric(),
        decision=_decision("BUY"),
    )

    assert result.class_ab_passed is True


def test_explicit_mandatory_sell_metadata_contradiction_is_class_b() -> None:
    result = validate_structured_claims(
        [
            _claim(
                claim_type=SemanticClaimType.HOLDER_REASSESSMENT,
                text="반드시 전량 매도해야 합니다.",
                trade_action="SELL",
                trade_force="MANDATORY",
            )
        ],
        evidence=_evidence(),
        numeric=_numeric(),
        decision=_decision("BUY"),
    )

    assert {item.code for item in result.semantic_issues} == {"mandatory_sell_contradicts_decision"}


@pytest.mark.parametrize(
    "text",
    ["수주가 회복됐습니다.", "발주가 늘었습니다.", "제품가격이 개선됐습니다.", "사업을 지지합니다."],
)
def test_generic_business_tokens_do_not_claim_price_semantics(text: str) -> None:
    result = validate_structured_claims(
        [_claim(claim_type=SemanticClaimType.CURRENT_FACT, topic="business", text=text)],
        evidence=_evidence(),
        numeric=_numeric(),
        decision=_decision(),
    )

    assert result.class_ab_passed is True


def test_current_us_repetition_is_benign_bound_numeric_template() -> None:
    for span in (
        "{{numeric:N1}} 수준의 거래량 참여입니다.",
        "{{numeric:N2}} 수준의 현재 가격을 기준으로 봅니다.",
    ):
        assessment = classify_repetition(
            RepetitionObservation(
                normalized_span=span,
                owner=ClaimOwner.AI_WRITER,
                stock_count=14,
                evidence_signature_count=14,
                has_bound_numeric_token=True,
            )
        )
        assert assessment.classification == RepetitionClass.BENIGN_TEMPLATE_REPEAT
        assert assessment.hard_block_candidate is False


def test_long_identical_rationale_across_distinct_evidence_is_material_spam() -> None:
    assessment = classify_repetition(
        RepetitionObservation(
            normalized_span=(
                "사업과 재무와 가격과 수급을 함께 검토하면 모든 종목에서 같은 이유로 "
                "매수해야 하며 개별 증거 차이는 중요하지 않습니다."
            ),
            owner=ClaimOwner.AI_WRITER,
            stock_count=8,
            evidence_signature_count=8,
        )
    )

    assert assessment.classification == RepetitionClass.MATERIAL_SPAM_REPEAT
    assert assessment.hard_block_candidate is True


def test_renderer_and_required_safety_repetition_have_distinct_ownership() -> None:
    renderer = classify_repetition(
        RepetitionObservation(
            normalized_span="가격 기준",
            owner=ClaimOwner.DETERMINISTIC_RENDERER,
            stock_count=22,
            evidence_signature_count=22,
        )
    )
    safety = classify_repetition(
        RepetitionObservation(
            normalized_span="확인되지 않은 수치는 사용하지 않습니다.",
            owner=ClaimOwner.SAFETY_POLICY,
            stock_count=22,
            evidence_signature_count=0,
            is_required_safety=True,
        )
    )

    assert renderer.classification == RepetitionClass.RENDERER_OWNED_REPEAT
    assert safety.classification == RepetitionClass.REQUIRED_SAFETY_REPEAT


def test_bounded_rewrite_preserves_all_semantic_invariants() -> None:
    before = rewrite_snapshot([_claim()], _decision())
    after = rewrite_snapshot([_claim(text="현금창출과 ROIC의 연결을 다음 공시에서 확인합니다.")], _decision())
    result = evaluate_bounded_rewrite(before, after, attempted=True)

    assert result.disposition == RewriteDisposition.SUCCEEDED
    assert result.class_ab_rerun_required is True
    assert result.original_remains_eligible is True


def test_bounded_rewrite_cannot_add_metric_or_change_decision() -> None:
    before = rewrite_snapshot([_claim()], _decision())
    after = rewrite_snapshot([_claim(metrics=("ROIC", "FCF"))], _decision("SELL"))
    result = evaluate_bounded_rewrite(before, after, attempted=True)

    assert result.disposition == RewriteDisposition.REJECTED_INVARIANCE
    assert set(result.invariant_errors) == {"decision_fields", "metrics"}
    assert result.original_remains_eligible is True


def test_failed_soft_rewrite_keeps_class_ab_safe_original_eligible() -> None:
    validation = validate_structured_claims(
        [_claim()],
        evidence=_evidence(),
        numeric=_numeric(),
        decision=_decision(),
    )
    rewrite = evaluate_bounded_rewrite(rewrite_snapshot([_claim()], _decision()), None, attempted=True)
    policy = evaluate_shadow_policy(validation, class_c_warning_count=1, rewrite=rewrite)

    assert policy.old_policy_eligible is False
    assert policy.new_shadow_policy_eligible is True
    assert policy.rewrite_disposition == RewriteDisposition.FAILED_KEEP_ORIGINAL


def test_ai_semantic_reviewer_is_advisory_and_cannot_add_facts() -> None:
    valid = AISemanticReviewerResult(
        verdict=ReviewerVerdict.WARN,
        issues=(
            AISemanticReviewerIssue(
                code="material_substantive_repeat",
                confidence="HIGH",
                claim_ids=("C1",),
                evidence_refs=("E1",),
                explanation="same long rationale is reused",
            ),
        ),
        proposed_fact_refs=("E1",),
    )
    invalid = valid.model_copy(update={"proposed_fact_refs": ("E_NEW",), "external_fetch_performed": True})

    valid_result = validate_ai_semantic_reviewer(
        valid,
        allowed_claim_ids={"C1"},
        allowed_evidence_refs={"E1"},
        allowed_numeric_refs=set(),
    )
    invalid_result = validate_ai_semantic_reviewer(
        invalid,
        allowed_claim_ids={"C1"},
        allowed_evidence_refs={"E1"},
        allowed_numeric_refs=set(),
    )

    assert valid_result.valid is True
    assert valid_result.production_hard_gate is False
    assert invalid_result.valid is False
    assert set(invalid_result.errors) == {"external_fetch_not_allowed", "reviewer_added_fact"}


def test_generalized_incident_corpus_has_all_required_roles_and_zero_safety_regression() -> None:
    path = Path(__file__).parent / "fixtures" / "validation_policy_incident_corpus.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    cases = payload["cases"]
    required_roles = {
        "historical_false_positive",
        "true_positive",
        "semantically_adjacent",
        "unrelated_negative_control",
    }

    for family in {item["family"] for item in cases}:
        assert {item["role"] for item in cases if item["family"] == family} == required_roles
    assert all(
        item["new_verdict"] == "BLOCK"
        for item in cases
        if item["true_safety_risk"] is True
    )
    assert sum(
        item["old_verdict"] == "BLOCK"
        and item["new_verdict"] != "BLOCK"
        and item["true_safety_risk"] is False
        for item in cases
    ) >= 5


def test_repetition_incident_corpus_is_classified_by_ownership_not_exact_text() -> None:
    path = Path(__file__).parent / "fixtures" / "validation_policy_incident_corpus.json"
    cases = json.loads(path.read_text(encoding="utf-8"))["cases"]
    repetition_cases = [item for item in cases if item.get("kind") == "repetition"]

    for item in repetition_cases:
        assessment = classify_repetition(
            RepetitionObservation(
                normalized_span=item["text"],
                owner=ClaimOwner(item["owner"]),
                stock_count=item["stock_count"],
                evidence_signature_count=item["evidence_signature_count"],
                is_required_safety=item.get("is_required_safety", False),
                is_structural_heading=item.get("is_structural_heading", False),
                has_bound_numeric_token=item.get("has_bound_numeric_token", False),
            )
        )
        assert assessment.classification == RepetitionClass(item["expected_repetition_class"])
