from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.services.directional_financial_context_service import (
    validate_directional_financial_semantics,
)
from app.services.financial_framework_claim_service import (
    CONTRACT_VERSION,
    FrameworkReferenceRole,
    candidate_financial_framework_claims,
    financial_framework_claims,
    framework_reference_is_application,
)


FIXTURE_PATH = Path(
    "tests/fixtures/financial_sector_exclusion_connective_scope_m12aq.json"
)
FIXTURES = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def _candidate(text: str) -> dict[str, object]:
    return {"sector_interpretation": {"text": text, "evidence_refs": []}}


def _validate(candidate: dict[str, object]):
    return validate_directional_financial_semantics(
        candidate,
        supplied_refs=(),
        allowed_ref_ids=(),
        sector_framework="insurance",
    )


def test_contract_version_and_fixture_inventory_are_frozen() -> None:
    assert CONTRACT_VERSION == "financial-framework-claim-scope-v2"
    assert {row["id"] for row in FIXTURES["positive"]} == {
        "SECTOR-EXCL-P01",
        "SECTOR-EXCL-P02",
        "SECTOR-EXCL-P03",
        "SECTOR-EXCL-P04",
        "SECTOR-EXCL-P05",
        "SECTOR-EXCL-P06",
    }
    assert {row["id"] for row in FIXTURES["negative"]} == {
        "SECTOR-EXCL-N01",
        "SECTOR-EXCL-N02",
        "SECTOR-EXCL-N03",
        "SECTOR-EXCL-N04",
        "SECTOR-EXCL-N05",
    }


@pytest.mark.parametrize("case", FIXTURES["positive"], ids=lambda row: row["id"])
def test_connective_exclusions_apply_to_the_coordinated_left_object(case) -> None:
    candidate = _candidate(case["text"])
    claims = candidate_financial_framework_claims(candidate)
    assert {claim.framework for claim in claims} == set(case["frameworks"])
    assert {claim.role for claim in claims} == {
        FrameworkReferenceRole.CONTRASTIVE_REPLACEMENT
    }
    assert not any(framework_reference_is_application(claim) for claim in claims)
    result = _validate(candidate)
    assert result.valid, result
    assert result.partial_debt_total_claim_count == 0
    assert result.financial_sector_generic_financial_context_leak_count == 0


@pytest.mark.parametrize("case", FIXTURES["negative"], ids=lambda row: row["id"])
def test_negated_or_actual_framework_use_remains_fail_closed(case) -> None:
    candidate = _candidate(case["text"])
    claims = candidate_financial_framework_claims(candidate)
    assert {claim.framework for claim in claims} == set(case["frameworks"])
    assert any(framework_reference_is_application(claim) for claim in claims)
    assert not _validate(candidate).valid


def test_exact_m12ap_sentence_has_no_backward_predicate_leakage() -> None:
    text = (
        "보험사이므로 산업회사식 순부채와 운전자본 틀을 배제하고 "
        "인수 규율과 규제자본을 중심으로 본다."
    )
    claims = financial_framework_claims(text)
    assert {claim.framework for claim in claims} == {
        "net_debt",
        "working_capital",
    }
    assert {claim.role for claim in claims} == {
        FrameworkReferenceRole.CONTRASTIVE_REPLACEMENT
    }
    result = _validate(_candidate(text))
    assert result.valid, result
    assert "net_debt_claim_without_complete_net_debt_evidence" not in result.errors
    assert "financial_sector_generic_reasoning" not in result.errors


def test_exclusion_is_local_and_does_not_immunize_a_current_claim() -> None:
    candidate = {
        "sector_interpretation": {
            "text": "산업회사식 순부채 틀을 배제하고 규제자본을 본다.",
            "evidence_refs": [],
        },
        "sell_drivers": [
            {"text": "하지만 현재 순부채가 높아 SELL이다.", "evidence_refs": []}
        ],
    }
    claims = candidate_financial_framework_claims(candidate)
    assert {claim.role for claim in claims} == {
        FrameworkReferenceRole.CONTRADICTORY_MIXED_USE
    }
    result = _validate(candidate)
    assert not result.valid
    assert "net_debt_claim_without_complete_net_debt_evidence" in result.errors
    assert "financial_sector_generic_reasoning" in result.errors


@pytest.mark.parametrize(
    "text",
    (
        "보험사에는 산업회사식 순부채와 운전자본 대신 보험 인수 규율과 규제자본 기준을 적용해야 한다.",
        "보험사이므로 산업회사식 순부채·운전자본 틀이 아니라 인수 규율과 규제자본으로 판단한다.",
        "보험사이므로 인수 규율과 규제자본을 적용하며 산업회사식 순부채·운전자본 틀은 배제한다.",
    ),
)
def test_prior_contrastive_and_explicit_exclusion_forms_still_pass(text: str) -> None:
    claims = candidate_financial_framework_claims(_candidate(text))
    assert claims
    assert not any(framework_reference_is_application(claim) for claim in claims)
    assert _validate(_candidate(text)).valid
