from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.services.directional_decision_material_stability_service import (
    classify_directional_core_decision_material_stability,
    classify_directional_core_legacy_stability,
)
from app.services.directional_financial_context_service import (
    validate_directional_financial_semantics,
)
from app.services.financial_framework_claim_service import (
    FrameworkReferenceRole,
    candidate_financial_framework_claims,
    framework_reference_is_application,
)
from app.services.fundamental_holder_stance_service import (
    FundamentalHolderRiskProfile,
    derive_fundamental_holder_stance,
)


FIXTURES = json.loads(
    Path("fixtures/financial_framework_negation_holder_stability_m12ad.json").read_text()
)


def _candidate(text: str) -> dict[str, object]:
    return {"sector_interpretation": {"text": text, "evidence_refs": []}}


@pytest.mark.parametrize(
    "case", FIXTURES["contrastive_positive"], ids=lambda row: row["id"]
)
def test_structural_contrastive_replacement_is_not_application(case):
    candidate = _candidate(case["text"])
    claims = candidate_financial_framework_claims(candidate)
    assert {claim.framework for claim in claims} == set(case["frameworks"])
    assert {claim.role for claim in claims} == {
        FrameworkReferenceRole.CONTRASTIVE_REPLACEMENT
    }
    assert not any(framework_reference_is_application(claim) for claim in claims)
    result = validate_directional_financial_semantics(
        candidate,
        supplied_refs=(),
        allowed_ref_ids=(),
        sector_framework="insurance",
    )
    assert result.valid, result


def test_contrastive_exclusion_does_not_immunize_actual_sell_driver_use():
    candidate = {
        "sector_interpretation": {
            "text": "순부채 틀이 아니라 규제자본으로 판단한다.",
            "evidence_refs": [],
        },
        "sell_drivers": [
            {"text": "순부채가 높아 SELL 근거다.", "evidence_refs": []}
        ],
    }
    claims = candidate_financial_framework_claims(candidate)
    assert {claim.role for claim in claims} == {
        FrameworkReferenceRole.CONTRADICTORY_MIXED_USE
    }
    result = validate_directional_financial_semantics(
        candidate,
        supplied_refs=(),
        allowed_ref_ids=(),
        sector_framework="insurance",
    )
    assert not result.valid


@pytest.mark.parametrize(
    "case", FIXTURES["holder_profiles"], ids=lambda row: row["id"]
)
def test_holder_contract_is_generic_and_score_free(case):
    decision = derive_fundamental_holder_stance(
        FundamentalHolderRiskProfile(**case["profile"])
    )
    assert decision.stance.value == case["expected"]


def _core(
    *,
    buy: float,
    direction: str = "HOLD",
    delta: str = "UNCHANGED",
    buyer: str = "WAIT",
    holder: str = "REVIEW",
    confidence: str = "LOW",
) -> dict[str, object]:
    lean = "NOT_HOLD"
    if direction == "HOLD":
        lean = "BUY_LEAN" if buy == 5.5 else "SELL_LEAN" if buy == 4.5 else "NEUTRAL"
    return {
        "ticker": "TEST",
        "overall_direction": direction,
        "directional_balance": {"buy": buy, "sell": 10 - buy},
        "hold_lean": lean,
        "directional_confidence": confidence,
        "business_thesis_change": delta,
        "fundamental_new_buyer": {"stance": buyer},
        "fundamental_holder": {"stance": holder},
    }


@pytest.mark.parametrize(
    ("cores", "expected"),
    [
        (
            [_core(buy=5.0), _core(buy=5.5), _core(buy=5.5)],
            "CALIBRATION_VARIANCE_SAME_DIRECTION",
        ),
        (
            [_core(buy=6.0, direction="BUY"), _core(buy=6.5, direction="BUY"), _core(buy=6.0, direction="BUY")],
            "CALIBRATION_VARIANCE_SAME_DIRECTION",
        ),
        (
            [_core(buy=4.0, direction="SELL"), _core(buy=3.5, direction="SELL"), _core(buy=4.0, direction="SELL")],
            "CALIBRATION_VARIANCE_SAME_DIRECTION",
        ),
        (
            [_core(buy=5.0), _core(buy=4.0, direction="SELL"), _core(buy=5.0)],
            "PRIMARY_DIRECTION_UNSTABLE",
        ),
        (
            [_core(buy=5.0), _core(buy=5.0, holder="REDUCE"), _core(buy=5.0)],
            "HOLDER_STANCE_UNSTABLE",
        ),
        (
            [_core(buy=5.0), _core(buy=5.0, buyer="AVOID"), _core(buy=5.0)],
            "NEW_BUYER_STANCE_UNSTABLE",
        ),
        (
            [_core(buy=5.0), _core(buy=5.0, confidence="MEDIUM"), _core(buy=5.0)],
            "DECISION_STABLE",
        ),
        (
            [_core(buy=5.0), _core(buy=5.0, delta="WEAKENED"), _core(buy=5.0)],
            "BUSINESS_DELTA_UNSTABLE",
        ),
    ],
)
def test_decision_material_stability_classes(cores, expected):
    result = classify_directional_core_decision_material_stability(cores)
    assert result["classification"] == expected


def test_legacy_formal_view_remains_separate_from_material_view():
    cores = [_core(buy=5.0), _core(buy=5.5), _core(buy=5.5)]
    legacy = classify_directional_core_legacy_stability(cores)
    material = classify_directional_core_decision_material_stability(cores)
    assert legacy["classification"] == "BOUNDARY_UNCERTAINTY"
    assert material["classification"] == "CALIBRATION_VARIANCE_SAME_DIRECTION"
    assert material["readiness_blocking"] is False
