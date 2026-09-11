from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.services.directional_balance_service import DirectionalBalance
from app.services.directional_financial_context_service import (
    validate_directional_financial_semantics,
)
from app.services.directional_threshold_zone_service import (
    derive_directional_threshold_zone,
)
from app.services.financial_framework_claim_service import (
    FrameworkReferenceRole,
    candidate_financial_framework_claims,
    framework_reference_is_application,
)
from scripts import financial_framework_scope_threshold_zone_m12ac as m12ac


FIXTURES = json.loads(
    Path("fixtures/financial_framework_scope_threshold_zone_m12ac.json").read_text()
)


def _candidate(text: str) -> dict[str, object]:
    return {"sector_interpretation": {"text": text, "evidence_refs": []}}


@pytest.mark.parametrize(
    "case", FIXTURES["application_scope_positive"], ids=lambda row: row["id"]
)
def test_coordinated_contrastive_replacements_share_non_application_role(case):
    candidate = _candidate(case["text"])
    claims = candidate_financial_framework_claims(candidate)
    assert {claim.framework for claim in claims} == set(case["frameworks"])
    assert {claim.role.value for claim in claims} == {case["expected_role"]}
    assert not any(framework_reference_is_application(claim) for claim in claims)
    result = validate_directional_financial_semantics(
        candidate,
        supplied_refs=(),
        allowed_ref_ids=(),
        sector_framework="insurance",
    )
    assert result.valid, result


@pytest.mark.parametrize(
    "case", FIXTURES["application_scope_negative"], ids=lambda row: row["id"]
)
def test_actual_or_ambiguous_financial_framework_use_still_fails(case):
    candidate = _candidate(case["text"])
    claims = candidate_financial_framework_claims(candidate)
    assert claims
    assert any(framework_reference_is_application(claim) for claim in claims)
    result = validate_directional_financial_semantics(
        candidate,
        supplied_refs=(),
        allowed_ref_ids=(),
        sector_framework="insurance",
    )
    assert not result.valid


def test_cross_field_contradiction_marks_both_references_mixed_use():
    candidate = {
        "sector_interpretation": {
            "text": "순부채와 운전자본 대신 규제자본을 적용해야 한다.",
            "evidence_refs": [],
        },
        "sell_drivers": [
            {"text": "운전자본 악화와 순부채 부담이 SELL 근거다.", "evidence_refs": []}
        ],
    }
    claims = candidate_financial_framework_claims(candidate)
    assert {claim.role for claim in claims} == {
        FrameworkReferenceRole.CONTRADICTORY_MIXED_USE
    }


@pytest.mark.parametrize("case", FIXTURES["threshold_zones"], ids=lambda row: row["id"])
def test_threshold_zone_mapper_is_deterministic_and_non_mutating(case):
    balance = DirectionalBalance(buy=case["buy"], sell=case["sell"])
    observation = derive_directional_threshold_zone(
        overall_direction=case["direction"],
        directional_balance=balance,
        hold_lean=case["lean"],
    )
    assert observation.decision_threshold_zone.value == case["zone"]
    assert observation.overall_direction == case["direction"]
    assert observation.directional_balance == balance
    assert observation.hold_lean == case["lean"]


@pytest.mark.parametrize(
    ("direction", "buy", "sell", "lean"),
    [
        ("BUY", 5.5, 4.5, "BUY_LEAN"),
        ("SELL", 4.5, 5.5, "SELL_LEAN"),
        ("HOLD", 4.5, 5.5, "NEUTRAL"),
    ],
)
def test_threshold_zone_mapper_rejects_inconsistent_raw_state(
    direction, buy, sell, lean
):
    with pytest.raises(ValidationError):
        derive_directional_threshold_zone(
            overall_direction=direction,
            directional_balance=DirectionalBalance(buy=buy, sell=sell),
            hold_lean=lean,
        )


@pytest.mark.parametrize(
    ("buy", "sell"),
    [(5.25, 4.75), (6.0, 3.5), (-0.5, 10.5)],
)
def test_threshold_zone_mapper_does_not_repair_malformed_balance(buy, sell):
    with pytest.raises(ValidationError):
        DirectionalBalance(buy=buy, sell=sell)


def test_exact_m12ab_fic_fin_08_row_passes_without_rewrite():
    replay = m12ac._exact_m12ab_fic_fin_08()

    assert replay["status"] == "PASS", replay
    assert replay["source_output_rewritten"] is False
    assert replay["after_errors"] == []
    assert replay["roles"]["application_count"] == 0
    assert replay["roles"]["roles"] == ["CONTRASTIVE_REPLACEMENT"]


def test_option_f_is_absent_from_restored_model_contract():
    proof = m12ac._original_model_contract_proof()

    assert proof["status"] == "PASS", proof
    assert proof["contract"] == "directional-core-output-v1"
    assert proof["prompt_has_adjacent_boundary"] is False
    assert proof["schema_has_adjacent_boundary"] is False


def test_required_artifact_names_are_complete_and_unique():
    assert set(m12ac.SLUGS) == set(range(1, 67))
    assert len(set(m12ac.SLUGS.values())) == 66


def test_historical_m12aa_boundary_maps_to_one_zone_without_raw_rewrite():
    historical = json.loads(
        Path(
            "docs/reports/20260910-financial-framework-scope-regression-"
            "threshold-zone-architecture-full-sol-canary/"
            "08-fic-fin-05-historical-boundary-reuse-proof.json"
        ).read_text()
    )

    assert historical["raw_formal_class"] == "UNSTABLE"
    assert historical["derived_zone_class"] == "ZONE_STABLE"
    assert set(historical["derived_zone_values"]) == {"NEGATIVE_THRESHOLD_ZONE"}
    assert historical["non_hold_lean_normalization_change_count"] == 0
