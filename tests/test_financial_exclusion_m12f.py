from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.services.cross_market_decision_engine_service import FinancialPeriodType
from app.services.directional_financial_context_service import (
    validate_directional_financial_semantics,
)
from app.services.financial_framework_claim_service import (
    FrameworkClaimKind,
    candidate_financial_framework_claims,
    financial_framework_claims,
)
from scripts import directional_financial_context_m12 as m12


FIXTURES = json.loads(Path("fixtures/financial_exclusion_m12f.json").read_text())


def validate(text, *, sector="bank_or_insurer", refs=(), extra=None):
    candidate = {"sector_interpretation": {"text": text, "evidence_refs": []}, **(extra or {})}
    return validate_directional_financial_semantics(
        candidate,
        supplied_refs=refs,
        allowed_ref_ids=tuple(r.ref_id for r in refs),
        sector_framework=sector,
    )


@pytest.mark.parametrize("text", FIXTURES["positive"])
def test_explicit_exclusion_passes_without_metric_application(text):
    claims = financial_framework_claims(text)
    assert claims
    assert all(c.kind == FrameworkClaimKind.EXPLICIT_EXCLUSION for c in claims)
    assert validate(text).valid


@pytest.mark.parametrize("text", FIXTURES["negative"])
def test_assertion_ambiguity_and_mixed_scope_fail_closed(text):
    claims = financial_framework_claims(text)
    assert any(c.kind != FrameworkClaimKind.EXPLICIT_EXCLUSION for c in claims)
    assert not validate(text).valid


def test_no_cross_field_exclusion_immunity():
    result = validate(
        FIXTURES["positive"][0],
        extra={"risk_context": {"text": "운전자본 악화가 위험이다.", "evidence_refs": []}},
    )
    assert "financial_sector_generic_reasoning" in result.errors


def test_conditions_are_also_scoped_and_auditable():
    candidate = {
        "fundamental_new_buyer": {
            "confirmation_business_condition": "순부채가 낮으면 수익성이 좋아진다.",
            "confirmation_business_condition_refs": ["plain:sector"],
        }
    }
    claims = candidate_financial_framework_claims(candidate)
    assert claims[0].field_path == "fundamental_new_buyer.confirmation_business_condition"
    assert claims[0].evidence_refs == ("plain:sector",)
    assert not validate(FIXTURES["positive"][0], extra=candidate).valid


def net_debt_ref():
    return m12._financial_ref(
        "GENERIC",
        "complete-net-debt",
        "net_debt",
        "100",
        period_type=FinancialPeriodType.POINT_IN_TIME,
        start=None,
        end="2026-06-30",
        derived=True,
    )


def test_complete_nonfinancial_net_debt_still_passes_but_sector_use_fails():
    ref = net_debt_ref()
    candidate = {"claim": {"text": "순부채 잔액은 재무 부담이다.", "evidence_refs": [ref.ref_id]}}
    for sector, expected in (("standard_operating_company", True), ("insurance", False)):
        result = validate_directional_financial_semantics(
            candidate,
            supplied_refs=(ref,),
            allowed_ref_ids=(ref.ref_id,),
            sector_framework=sector,
        )
        assert result.valid == expected


def test_no_exclusion_immunity_for_industrial_material_anchor():
    ref = net_debt_ref()
    result = validate(
        FIXTURES["positive"][0],
        refs=(ref,),
        extra={"material_directional_anchor_basis": [ref.ref_id]},
    )
    assert "financial_sector_industrial_financial_anchor_used" in result.errors


def test_nonfinancial_missing_net_debt_still_rejected():
    assert not validate("순부채가 높다.", sector="standard_operating_company").valid
    assert validate("순부채 틀은 적용하지 않는다.", sector="standard_operating_company").valid


def test_original_eight_subject_output_is_not_rewritten():
    from scripts import directional_financial_context_m12g as grounding

    path = Path(
        "docs/reports/20260909-bounded-financial-context-boundary-calibration-full-fictional-canary/38-run-1-context-02.json"
    )
    document = json.loads(path.read_text())
    row = next(r for r in document["rows"] if r["ticker"] == "FIC-FIN-08")
    assert set(row["errors"]) == {
        "net_debt_claim_without_complete_net_debt_evidence",
        "financial_sector_generic_reasoning",
    }
    _, owned, catalogs, _ = m12.fictional_inputs("m12f-offline-test")
    batch = m12.DirectionalCoreBatch(
        packet_id="m12f-offline-test",
        candidates=(m12.DirectionalCoreCandidate.model_validate(row["core"]),),
    )
    rows, audit = grounding._audit_core_batch_with_grounding(batch, owned=owned, catalogs=catalogs)
    assert audit["status"] == "PASS", rows
    assert row["status"] == "FAIL"
