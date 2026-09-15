from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.services.cross_market_decision_engine_service import (
    DecisionEvidenceRef,
    EvidenceCategory,
    FinancialContext,
    FinancialDerivation,
    FinancialEvidenceQuality,
    FinancialEvidenceStatus,
    FinancialPeriod,
    FinancialPeriodType,
)
from app.services.directional_financial_context_service import (
    FINANCIAL_CLAIM_ROW_CONTRACT,
    FinancialClaimFieldRole,
    financial_claim_rows,
    validate_directional_financial_semantics,
)


FIXTURE = json.loads(
    (
        Path(__file__).parent
        / "fixtures/ppe_proxy_fcf_claim_scope_m12ar.json"
    ).read_text(encoding="utf-8")
)


def _proxy_ref() -> DecisionEvidenceRef:
    return DecisionEvidenceRef(
        ref_id="canonical:proxy",
        category=EvidenceCategory.EARNINGS,
        label="cash_conversion_ocf_less_ppe",
        statement="OCF less PPE acquisition cash outflow is positive.",
        source_ref="stock.fact_catalog.cash_flow_fcf_ppe",
        financial_context=FinancialContext(
            metric="ocf_less_ppe_capex",
            currency="USD",
            unit_scale=1,
            period=FinancialPeriod(
                type=FinancialPeriodType.YTD,
                start="2026-01-01",
                end="2026-06-30",
                duration_days=181,
            ),
            entity_scope="consolidated",
            statement_basis="formal_financial_statement",
            evidence_status=FinancialEvidenceStatus.DERIVED_SAFE,
            quality=FinancialEvidenceQuality.VERIFIED,
            derivation=FinancialDerivation(
                formula="ocf_less_ppe_capex",
                input_source_refs=("canonical:ocf", "canonical:ppe"),
                version="cash-flow-capital-efficiency-v1",
            ),
            limitations=("ppe_only_not_management_defined_fcf",),
        ),
    )


def _configured_ref(ref_id: str, source_ref: str) -> DecisionEvidenceRef:
    return DecisionEvidenceRef(
        ref_id=ref_id,
        category=EvidenceCategory.THESIS,
        label=ref_id,
        statement=ref_id,
        source_ref=source_ref,
    )


@pytest.fixture
def supplied_refs() -> tuple[DecisionEvidenceRef, ...]:
    return (
        _proxy_ref(),
        _configured_ref(
            "configured:strengthen",
            "stock.thesis.strengthen_signals.fcf_reacceleration",
        ),
        _configured_ref(
            "configured:invalidation",
            "stock.thesis.invalidation_signals.fcf_stagnation",
        ),
    )


def _validate(
    candidate: object,
    supplied_refs: tuple[DecisionEvidenceRef, ...],
):
    return validate_directional_financial_semantics(
        candidate,
        supplied_refs=supplied_refs,
        allowed_ref_ids=tuple(ref.ref_id for ref in supplied_refs),
    )


def test_financial_claim_row_v2_binds_stage2_sibling_refs() -> None:
    candidate = {
        "core": {"text": "현재 현금창출을 확인했다.", "evidence_refs": ["core"]},
        "fundamental_new_buyer": {
            "summary": "FCF 가속은 아직 확인되지 않았다.",
            "confirmation_business_condition": "FCF 재가속이 확인되어야 한다.",
            "confirmation_business_condition_refs": ["buyer"],
        },
        "fundamental_holder": {
            "summary": "현재 보유 근거를 유지한다.",
            "business_invalidation_condition": "FCF가 감소하면 재검토한다.",
            "business_invalidation_condition_refs": ["holder"],
        },
        "nested": [{"text": "중첩 문장", "evidence_refs": ["nested"]}],
    }

    rows = {row.field_path: row for row in financial_claim_rows(candidate)}

    assert {row.contract for row in rows.values()} == {FINANCIAL_CLAIM_ROW_CONTRACT}
    assert rows["core.text"].bound_evidence_refs == ("core",)
    assert rows[
        "fundamental_new_buyer.confirmation_business_condition"
    ].bound_evidence_refs == ("buyer",)
    assert rows[
        "fundamental_new_buyer.confirmation_business_condition"
    ].field_semantic_role == FinancialClaimFieldRole.STANCE_CONFIRMATION_CONDITION
    assert rows[
        "fundamental_holder.business_invalidation_condition"
    ].bound_evidence_refs == ("holder",)
    assert rows[
        "fundamental_holder.business_invalidation_condition"
    ].field_semantic_role == FinancialClaimFieldRole.STANCE_INVALIDATION_CONDITION
    assert rows["fundamental_new_buyer.summary"].bound_evidence_refs == ()
    assert rows["nested[0].text"].bound_evidence_refs == ("nested",)


@pytest.mark.parametrize("row", FIXTURE["negative"], ids=lambda row: row["id"])
def test_direct_or_explicit_proxy_as_fcf_remains_hard_failure(
    row: dict[str, object],
    supplied_refs: tuple[DecisionEvidenceRef, ...],
) -> None:
    refs = ["canonical:proxy"] if row["refs"] else []
    result = _validate(
        {"claim": {"text": row["text"], "evidence_refs": refs}},
        supplied_refs,
    )

    assert not result.valid
    assert result.affirmative_proxy_as_fcf_violation_count >= 1
    assert "ppe_only_cash_conversion_proxy_called_fcf" in result.errors


@pytest.mark.parametrize("row", FIXTURE["positive"], ids=lambda row: row["id"])
def test_unrelated_or_disclaimed_fcf_claims_pass(
    row: dict[str, object],
    supplied_refs: tuple[DecisionEvidenceRef, ...],
) -> None:
    ref_ids = {
        "proxy": "canonical:proxy",
        "configured_strengthen": "configured:strengthen",
        "configured_invalidation": "configured:invalidation",
    }
    field = str(row["field"])
    claim: dict[str, object] = {field: row["text"]}
    refs = [ref_ids[str(ref)] for ref in row["refs"]]
    if field == "confirmation_business_condition":
        claim["confirmation_business_condition_refs"] = refs
        candidate = {
            "proxy": {
                "text": "OCF less PPE is positive.",
                "evidence_refs": ["canonical:proxy"],
            },
            "fundamental_new_buyer": claim,
        }
    elif field == "business_invalidation_condition":
        claim["business_invalidation_condition_refs"] = refs
        candidate = {
            "proxy": {
                "text": "OCF less PPE is positive.",
                "evidence_refs": ["canonical:proxy"],
            },
            "fundamental_holder": claim,
        }
    elif field == "summary":
        candidate = {
            "proxy": {
                "text": "OCF less PPE is positive.",
                "evidence_refs": ["canonical:proxy"],
            },
            "fundamental_new_buyer": claim,
        }
    else:
        claim["evidence_refs"] = refs
        candidate = {"claim": claim}

    result = _validate(candidate, supplied_refs)

    assert result.valid
    assert result.affirmative_proxy_as_fcf_violation_count == 0
    assert result.unsupported_current_fcf_claim_count == 0


def test_cross_field_proxy_scope_isolated_but_direct_mislabel_still_fails(
    supplied_refs: tuple[DecisionEvidenceRef, ...],
) -> None:
    configured_condition = {
        "confirmation_business_condition": "FCF growth must reaccelerate.",
        "confirmation_business_condition_refs": ["configured:strengthen"],
    }
    safe = _validate(
        {
            "field_a": {
                "text": "OCF less PPE is positive.",
                "evidence_refs": ["canonical:proxy"],
            },
            "fundamental_new_buyer": configured_condition,
        },
        supplied_refs,
    )
    unsafe = _validate(
        {
            "field_a": {
                "text": "FCF is positive.",
                "evidence_refs": ["canonical:proxy"],
            },
            "fundamental_new_buyer": configured_condition,
        },
        supplied_refs,
    )

    assert safe.valid
    assert not unsafe.valid
    assert unsafe.affirmative_proxy_as_fcf_violation_count == 1


def test_unbound_current_fcf_claim_fails_separately_from_proxy_mislabel(
    supplied_refs: tuple[DecisionEvidenceRef, ...],
) -> None:
    result = _validate(
        {
            "proxy": {
                "text": "OCF less PPE is positive.",
                "evidence_refs": ["canonical:proxy"],
            },
            "core_judgment": {"text": "현재 FCF는 양수다.", "evidence_refs": []},
        },
        supplied_refs,
    )

    assert not result.valid
    assert result.affirmative_proxy_as_fcf_violation_count == 0
    assert result.unsupported_current_fcf_claim_count == 1
    assert result.errors == ("unsupported_current_fcf_claim",)


def test_tsla_not_management_fcf_disclaimer_regression(
    supplied_refs: tuple[DecisionEvidenceRef, ...],
) -> None:
    result = _validate(
        {
            "claim": {
                "text": "현금 전환 대용치이며 관리 기준 잉여현금흐름이 아니다.",
                "evidence_refs": ["canonical:proxy"],
            }
        },
        supplied_refs,
    )

    assert result.valid
    assert result.explicit_not_fcf_disclaimer_count == 1
