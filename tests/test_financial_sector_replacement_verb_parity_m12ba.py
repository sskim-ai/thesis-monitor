from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.services.directional_financial_context_service import (
    validate_directional_financial_semantics,
)
from app.services.financial_framework_claim_service import (
    REPLACEMENT_APPLICATION_VERB_CONTRACT_VERSION,
    FrameworkReferenceRole,
    candidate_financial_framework_claims,
    framework_reference_is_application,
)


FIXTURE_PATH = Path(
    "tests/fixtures/financial_sector_replacement_verb_parity_m12ba.json"
)
FIXTURES = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def _candidate(text: str) -> dict[str, object]:
    return {"sector_interpretation": {"text": text, "evidence_refs": []}}


def _validate(text: str):
    return validate_directional_financial_semantics(
        _candidate(text),
        supplied_refs=(),
        allowed_ref_ids=(),
        sector_framework="insurance",
    )


def test_contract_and_fixture_inventory_are_frozen() -> None:
    assert (
        REPLACEMENT_APPLICATION_VERB_CONTRACT_VERSION
        == "korean-replacement-application-verb-v1"
    )
    assert {row["id"] for row in FIXTURES["positive"]} == {
        f"SECTOR-VERB-P{number:02d}" for number in range(1, 7)
    }
    assert {row["id"] for row in FIXTURES["negative"]} == {
        f"SECTOR-VERB-N{number:02d}" for number in range(1, 6)
    }


@pytest.mark.parametrize("case", FIXTURES["positive"], ids=lambda row: row["id"])
def test_valid_replacement_interpretation_verbs_are_contrastive(case) -> None:
    claims = candidate_financial_framework_claims(_candidate(case["text"]))
    assert {claim.framework for claim in claims} == set(case["frameworks"])
    assert {claim.role for claim in claims} == {
        FrameworkReferenceRole.CONTRASTIVE_REPLACEMENT
    }
    assert not any(framework_reference_is_application(claim) for claim in claims)
    result = _validate(case["text"])
    assert result.valid, result
    assert result.partial_debt_total_claim_count == 0
    assert result.financial_sector_generic_financial_context_leak_count == 0


@pytest.mark.parametrize(
    "case",
    FIXTURES["negative"][:4],
    ids=lambda row: row["id"],
)
def test_negative_or_unsupported_interpretation_does_not_gain_exemption(
    case,
) -> None:
    claims = candidate_financial_framework_claims(_candidate(case["text"]))
    assert {claim.framework for claim in claims} == set(case["frameworks"])
    assert not any(
        claim.role == FrameworkReferenceRole.CONTRASTIVE_REPLACEMENT
        for claim in claims
    )
    assert any(framework_reference_is_application(claim) for claim in claims)
    assert not _validate(case["text"]).valid


def test_possibility_language_does_not_create_a_replacement_claim() -> None:
    case = FIXTURES["negative"][4]
    claims = candidate_financial_framework_claims(_candidate(case["text"]))
    assert not claims
    assert _validate(case["text"]).valid


@pytest.mark.parametrize(
    ("text", "expected_role"),
    (
        (
            "은행·보험업의 자본과 보험 인수 기준을 적용하며 "
            "산업재식 부채·운전자본 틀은 사용하지 않는다.",
            FrameworkReferenceRole.EXPLICIT_NON_APPLICATION,
        ),
        (
            "보험사에는 산업회사식 순부채와 운전자본 틀을 적용하지 않고 "
            "인수 규율과 규제자본을 중심으로 본다.",
            FrameworkReferenceRole.CONTRASTIVE_REPLACEMENT,
        ),
        (
            "보험사에는 산업회사식 순부채·운전자본 틀을 적용하지 않고 "
            "언더라이팅과 규제자본을 중심으로 해석한다.",
            FrameworkReferenceRole.CONTRASTIVE_REPLACEMENT,
        ),
    ),
)
def test_exact_m12az_fic_fin_08_sentences_pass(
    text: str,
    expected_role: FrameworkReferenceRole,
) -> None:
    claims = candidate_financial_framework_claims(_candidate(text))
    assert claims
    assert {claim.role for claim in claims} == {expected_role}
    assert not any(framework_reference_is_application(claim) for claim in claims)
    result = _validate(text)
    assert result.valid, result


def test_separate_current_industrial_use_remains_hard() -> None:
    text = (
        "산업회사식 순부채 틀을 적용하지 않고 규제자본을 중심으로 해석하지만, "
        "현재 순부채가 높아 핵심 하방으로 본다."
    )
    claims = candidate_financial_framework_claims(_candidate(text))
    assert any(framework_reference_is_application(claim) for claim in claims)
    result = _validate(text)
    assert not result.valid
    assert "net_debt_claim_without_complete_net_debt_evidence" in result.errors
    assert "financial_sector_generic_reasoning" in result.errors


def test_replacement_verb_family_has_one_definition() -> None:
    source = Path(
        "app/services/financial_framework_claim_service.py"
    ).read_text(encoding="utf-8")
    assert source.count("_KO_REPLACEMENT_APPLICATION_VERB =") == 1
    assert source.count("+ _KO_REPLACEMENT_APPLICATION_VERB") == 2
