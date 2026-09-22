from __future__ import annotations

from copy import deepcopy

import pytest

from scripts.m12cq_two_pass_contract import (
    PASS_B_CONTRACT,
    PassBBatchOutput,
    eligible_material_risk_refs,
    validate_new_buyer_consistency,
    validate_pass_b_batch,
)


def _claim(claim_ref: str, parent_ref: str, *, polarity: str = "BEARISH") -> dict[str, object]:
    return {
        "claim_ref": claim_ref,
        "ticker": "RENAMED",
        "claim": {
            "text": "검증된 일반화 근거입니다.",
            "polarity": polarity,
            "reason_role": "FUNDAMENTAL",
            "logical_condition": None,
        },
        "parent_source_refs": [parent_ref],
    }


def _catalog() -> dict[str, object]:
    return {
        "ticker": "RENAMED",
        "all_evidence_refs": [
            "business:risk",
            "canonical:valuation",
            "canonical:security_basis:current",
            "canonical:financial_quality:current",
            "canonical:price",
            "timing:support",
        ],
        "core_evidence_refs": [
            "business:risk",
            "canonical:valuation",
            "canonical:security_basis:current",
            "canonical:financial_quality:current",
        ],
        "timing_evidence_refs": ["canonical:price", "timing:support"],
        "valuation_evidence_refs": ["canonical:valuation"],
        "material_disclosure_failure_refs": [],
        "positive_quality_refs": [],
        "claim_refs": [
            "claim:support",
            "claim:risk",
            "claim:valuation",
            "claim:security",
            "claim:quality",
        ],
        "atomic_claims": [
            _claim("claim:support", "business:risk", polarity="BULLISH"),
            _claim("claim:risk", "business:risk"),
            _claim("claim:valuation", "canonical:valuation"),
            _claim("claim:security", "canonical:security_basis:current"),
            _claim("claim:quality", "canonical:financial_quality:current"),
        ],
        "entry_catalog": {
            "ticker": "RENAMED",
            "current_price": {
                "value": 120.0,
                "currency": "USD",
                "as_of": "2026-09-18",
                "ref_id": "canonical:price",
            },
            "tactical_candidates": [
                {
                    "ticker": "RENAMED",
                    "candidate_id": "tactical:one",
                    "low": 80.0,
                    "high": 100.0,
                    "currency": "USD",
                    "evidence_refs": ["timing:support"],
                }
            ],
            "unresolved_policy": {"tactical_unresolved_reason": "unavailable"},
        },
    }


def _capability(*, expose_risk: bool = True) -> dict[str, object]:
    branches: list[dict[str, object]] = []
    if expose_risk:
        branches.append(
            {
                "stance": "WAIT",
                "reason_class": "EXECUTION_OR_THESIS_RISK",
                "allowed_evidence_refs": ["claim:risk", "business:risk"],
                "allowed_tactical_choices": ["UNRESOLVED"],
                "prerequisite": "material_bearish_business_evidence_available",
            }
        )
    return {"ticker": "RENAMED", "new_buyer": {"branches": branches}}


def _decision(
    *,
    holder: str = "HOLDABLE",
    thesis_state: str = "INTACT",
    reason_class: str = "EXECUTION_OR_THESIS_RISK",
    refs: list[str] | None = None,
) -> dict[str, object]:
    return {
        "ticker": "RENAMED",
        "overall_direction": "BUY",
        "new_buyer": "WAIT",
        "holder": holder,
        "directional_balance": {"buy": 6.0, "sell": 4.0},
        "decision_confidence": "MEDIUM",
        "decisive_supporting_claim_refs": ["claim:support"],
        "decisive_contradicting_claim_refs": ["claim:risk"],
        "thesis_state": thesis_state,
        "holder_reason_class": "NOT_APPLICABLE",
        "holder_reason": "기존 보유 판단은 독립적으로 유지합니다.",
        "holder_reason_evidence_refs": [],
        "new_buyer_reason_class": reason_class,
        "new_buyer_reason": "신규 자금은 위험 해소를 기다립니다.",
        "new_buyer_reason_refs": ["claim:risk"] if refs is None else refs,
        "tactical_choice": "UNRESOLVED",
        "re_evaluate_conditions": ["위험 근거의 해소 여부를 확인합니다."],
        "valuation_affects": [],
        "rule_trace": [
            "ARCHETYPE_REGIME_FREEZE",
            "EVIDENCE_OWNERSHIP",
            "DETERMINISTIC_FUNDAMENTAL_OPTION",
            "NEW_BUYER_CONSISTENCY",
        ],
        "policy_summary": "세 판단 축을 독립적으로 검증했습니다.",
    }


def _resolved_option() -> dict[str, object]:
    return {
        "ticker": "RENAMED",
        "status": "RESOLVED",
        "low": 80.0,
        "high": 100.0,
        "currency": "USD",
    }


def _entry(*, resolved: bool = True) -> dict[str, object]:
    return {
        "entry_range_status": "ENTRY_RANGE_RESOLVED" if resolved else "ENTRY_RANGE_UNRESOLVED",
        "tactical_entry_band": {
            "status": "RESOLVED",
            "high": 100.0,
        },
    }


@pytest.mark.parametrize(
    ("holder", "thesis_state"),
    [
        ("HOLDABLE", "INTACT"),
        ("REVIEW", "MIXED"),
        ("HOLDABLE", "STRENGTHENING"),
    ],
)
def test_risk_wait_is_independent_from_holder_and_thesis_axes(
    holder: str,
    thesis_state: str,
) -> None:
    result = validate_new_buyer_consistency(
        decision=_decision(holder=holder, thesis_state=thesis_state),
        policy_option=_resolved_option(),
        entry_range=_entry(),
        catalog=_catalog(),
        capability=_capability(),
    )

    assert result["status"] == "PASS"


def test_existing_fundamental_unresolved_wait_remains_valid() -> None:
    option = {"ticker": "RENAMED", "status": "UNRESOLVED"}
    result = validate_new_buyer_consistency(
        decision=_decision(reason_class="FUNDAMENTAL_UNRESOLVED", refs=["canonical:valuation"]),
        policy_option=option,
        entry_range=_entry(resolved=False),
        catalog=_catalog(),
    )

    assert result["status"] == "PASS"


def test_existing_tactical_wait_remains_valid() -> None:
    result = validate_new_buyer_consistency(
        decision=_decision(reason_class="TACTICAL_TIMING", refs=["timing:support"]),
        policy_option=_resolved_option(),
        entry_range=_entry(),
        catalog=_catalog(),
    )

    assert result["status"] == "PASS"


@pytest.mark.parametrize(
    "refs",
    [
        [],
        ["canonical:valuation"],
        ["canonical:security_basis:current"],
        ["canonical:financial_quality:current"],
        ["other:subject:risk"],
    ],
)
def test_risk_wait_rejects_missing_or_ineligible_refs(refs: list[str]) -> None:
    result = validate_new_buyer_consistency(
        decision=_decision(refs=refs),
        policy_option=_resolved_option(),
        entry_range=_entry(),
        catalog=_catalog(),
        capability=_capability(),
    )

    assert "risk_wait_requires_eligible_material_risk_evidence" in result["errors"]
    assert "wait_without_authorized_structured_condition" in result["errors"]


def test_risk_wait_rejects_when_capability_did_not_expose_branch() -> None:
    result = validate_new_buyer_consistency(
        decision=_decision(),
        policy_option=_resolved_option(),
        entry_range=_entry(),
        catalog=_catalog(),
        capability=_capability(expose_risk=False),
    )

    assert "risk_wait_requires_eligible_material_risk_evidence" in result["errors"]


def _batch(decision: dict[str, object]) -> PassBBatchOutput:
    return PassBBatchOutput.model_validate(
        {
            "contract": PASS_B_CONTRACT,
            "generation_id": "generation",
            "packet_id": "packet",
            "market": "us",
            "assessment_date": "2026-09-18",
            "decisions": [decision],
        }
    )


def test_new_buyer_risk_does_not_authorize_holder_review() -> None:
    decision = _decision(holder="REVIEW")
    decision["holder_reason_class"] = "THESIS_UNCERTAINTY"
    decision["holder_reason_evidence_refs"] = ["canonical:valuation"]
    result = validate_pass_b_batch(
        _batch(decision),
        expected_identity={
            "generation_id": "generation",
            "packet_id": "packet",
            "market": "us",
            "assessment_date": "2026-09-18",
        },
        subjects=("RENAMED",),
        catalogs={"RENAMED": _catalog()},
        pass_a_by_ticker={"RENAMED": {"archetype": "DURABLE_FRANCHISE"}},
    )

    assert "RENAMED:review_supported_only_by_valuation" in result["errors"]


def test_new_buyer_risk_does_not_authorize_overall_downgrade() -> None:
    decision = _decision()
    decision["overall_direction"] = "HOLD"
    decision["decisive_supporting_claim_refs"] = ["claim:valuation"]
    result = validate_pass_b_batch(
        _batch(decision),
        expected_identity={
            "generation_id": "generation",
            "packet_id": "packet",
            "market": "us",
            "assessment_date": "2026-09-18",
        },
        subjects=("RENAMED",),
        catalogs={"RENAMED": _catalog()},
        pass_a_by_ticker={"RENAMED": {"archetype": "DURABLE_FRANCHISE"}},
    )

    assert "RENAMED:overall_nonbuy_supported_only_by_valuation_or_timing" in result["errors"]


def test_eligible_risk_catalog_excludes_valuation_security_and_quality_only_claims() -> None:
    assert eligible_material_risk_refs(_catalog()) == {"claim:risk", "business:risk"}


def test_risk_wait_subject_ownership_is_fail_closed() -> None:
    catalog = deepcopy(_catalog())
    catalog["ticker"] = "OTHER"
    result = validate_new_buyer_consistency(
        decision=_decision(),
        policy_option=_resolved_option(),
        entry_range=_entry(),
        catalog=catalog,
        capability=_capability(),
    )

    assert "risk_wait_requires_eligible_material_risk_evidence" in result["errors"]
