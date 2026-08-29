from __future__ import annotations

import json
from pathlib import Path

from app.services.cross_market_decision_engine_service import (
    DecisionEvidencePacket,
    DecisionEvidenceRef,
    EvidenceCategory,
)
from scripts.cross_market_decision_quality_review import (
    AxisStates,
    IndependentReview,
    ReviewClaim,
    _agreement_category,
    _strict_json_schema,
    _validate_review,
)


ROOT = Path(__file__).resolve().parents[1]


def _claim(ref_id: str, text: str = "검증된 근거에 따른 판단입니다.") -> ReviewClaim:
    return ReviewClaim(text=text, evidence_refs=(ref_id,))


def _packet() -> DecisionEvidencePacket:
    ref = DecisionEvidenceRef(
        ref_id="canonical:test:thesis",
        category=EvidenceCategory.THESIS,
        label="핵심 투자 논리",
        statement="검증된 사업 논리",
        source_ref="fixture",
    )
    return DecisionEvidencePacket(
        packet_id="packet-test",
        ticker="TEST",
        company_name="Test",
        market="us",
        assessment_date="2026-08-29",
        horizon="6-24개월",
        evidence=(ref,),
        prohibited_claims=(),
        evidence_sha256="fixture-sha",
    )


def _review() -> IndependentReview:
    ref_id = "canonical:test:thesis"
    claim = _claim(ref_id)
    return IndependentReview(
        ticker="TEST",
        independent_decision="HOLD",
        confidence="MEDIUM",
        timing="NEUTRAL",
        decisive_reason=claim,
        strongest_bull_case=claim,
        strongest_bear_case=claim,
        why_not_buy=claim,
        why_not_sell=claim,
        key_unknown=claim,
        valuation_assessment=claim,
        expectation_assessment=claim,
        technical_assessment=claim,
        data_quality_assessment=claim,
        decision_change_conditions=(claim, claim),
        axis_states=AxisStates(
            business_quality="NEUTRAL",
            earnings_trajectory="NEUTRAL",
            earnings_quality="UNKNOWN",
            market_expectations="NEUTRAL",
            valuation="UNKNOWN",
            catalyst_profile="NEUTRAL",
            structural_risk="NEUTRAL",
            macro_sensitivity="NEUTRAL",
            market_sector_context="NEUTRAL",
            positioning_flows="NEUTRAL",
            price_structure="NEUTRAL",
            technical_momentum="NEUTRAL",
            data_quality="NEUTRAL",
        ),
        fundamental_technical_conflict="MIXED",
        new_buyer_view=claim,
        holder_view=claim,
        hold_primary_reason="BALANCED_EVIDENCE",
        confidence_basis="MIXED",
        timing_basis=claim,
        data_quality_limitations=("NONE",),
        material_ohlcv_families=(),
        macd_decision_contribution="NONE",
        macd_timing_contribution="NONE",
        macd_evidence_refs=(),
    )


def test_label_blind_review_accepts_exact_evidence_refs() -> None:
    assert _validate_review(_packet(), _review()) == []


def test_review_rejects_unknown_refs_and_order_language() -> None:
    invalid = _claim("canonical:test:missing", "즉시 매수해야 합니다.")
    errors = _validate_review(
        _packet(), _review().model_copy(update={"decisive_reason": invalid})
    )
    assert "order_command_language" in errors
    assert "unknown_evidence_ref:canonical:test:missing" in errors


def test_agreement_category_is_not_distribution_driven() -> None:
    assert _agreement_category("HOLD", "SELL", "ALIGNED", 0) == "ONE_STEP_DISAGREEMENT"
    assert _agreement_category("BUY", "SELL", "ALIGNED", 0) == "TWO_STEP_DISAGREEMENT"
    assert _agreement_category("HOLD", "HOLD", "MATERIAL_CONFLICT", 0) == (
        "SAME_DECISION_MATERIAL_REASON_CONFLICT"
    )


def test_output_schema_is_strict() -> None:
    schema = _strict_json_schema(IndependentReview.model_json_schema())
    assert schema["additionalProperties"] is False
    assert set(schema["required"]) == set(schema["properties"])


def test_committed_quality_review_gates_are_fail_closed() -> None:
    value = json.loads(
        (ROOT / "docs/reports/20260829-decision-quality-review.json").read_text()
    )
    gates = value["gates"]
    assert gates["BASELINE_SUBJECT_COUNT"] == 20
    assert gates["INDEPENDENT_REVIEW_COUNT"] == 20
    assert gates["MATERIAL_DISAGREEMENT_COUNT"] == 5
    assert gates["ADJUDICATION_COUNT"] == 5
    assert gates["FINAL_REVIEW_BUY_COUNT"] == 2
    assert gates["FINAL_REVIEW_HOLD_COUNT"] == 15
    assert gates["FINAL_REVIEW_SELL_COUNT"] == 3
    assert gates["OPEN_P0"] == 0
    assert gates["OPEN_MATERIAL_P1"] == 4
    assert gates["CANARY_RECOMMENDATION"] == "NOT_READY"
    assert gates["PRODUCTION_CANARY_ENABLED"] is False
    assert gates["PRODUCTION_DECISION_MESSAGE_SENT"] == 0


def test_review_has_two_sided_evidence_and_no_macd_ownership() -> None:
    value = json.loads(
        (ROOT / "docs/reports/20260829-decision-quality-review.json").read_text()
    )
    assert len(value["records"]) == 20
    for row in value["records"]:
        review = row["independent"]
        assert review["strongest_bull_case"]["text"]
        assert review["strongest_bear_case"]["text"]
        assert review["why_not_buy"]["evidence_refs"]
        assert review["why_not_sell"]["evidence_refs"]
        assert review["macd_decision_contribution"] != "DECISIVE"
    proposed = value["portfolio_audit"]["proposed_canary_set"]
    assert len(proposed) <= 6
    assert all(len(ticker) <= 12 and " " not in ticker for ticker in proposed)
