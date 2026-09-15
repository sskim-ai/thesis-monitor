from __future__ import annotations

import pytest

from app.services.directional_financial_context_service import (
    FCF_PROSPECTIVE_REQUIREMENT_CONTRACT,
    FinancialClaimRole,
    fcf_prospective_requirement_family,
    fcf_temporal_claim_role,
    fcf_temporal_claim_spans,
    financial_claim_row_requires_current_fcf_evidence,
    financial_claim_rows,
    validate_directional_financial_semantics,
)


def _candidate(text: str, *, field: str = "business_thesis_context") -> dict[str, object]:
    return {
        "ticker": "M12BG",
        field: {
            "text": text,
            "evidence_refs": [],
        },
    }


def _row(text: str, *, field: str = "business_thesis_context"):
    rows = financial_claim_rows(_candidate(text, field=field))
    assert len(rows) == 1
    return rows[0]


def _requires_current(text: str, *, field: str = "business_thesis_context") -> bool:
    return financial_claim_row_requires_current_fcf_evidence(
        _row(text, field=field),
        evidence_by_ref={},
    )


def _validate(text: str, *, field: str = "business_thesis_context"):
    return validate_directional_financial_semantics(
        _candidate(text, field=field),
        supplied_refs=(),
        allowed_ref_ids=(),
    )


@pytest.mark.parametrize(
    "text",
    (
        "성장이 FCF와 ROIC 개선으로 이어져야 한다는 기존 논리가 유지된다.",
        "실제 FCF와 ROIC 증명이 필요하다.",
        "FCF 개선이 확인되어야 투자 논리를 강화한다.",
        "FCF 개선의 입증이 필요하다.",
        "FCF가 투자 확대를 상쇄해야 한다.",
        "growth must translate into improved free cash flow.",
        "proof of FCF improvement is still needed.",
    ),
)
def test_prospective_fcf_requirements_do_not_require_current_evidence(
    text: str,
) -> None:
    assert fcf_prospective_requirement_family(text) is not None
    assert not _requires_current(text)
    assert _validate(text).valid

    span = fcf_temporal_claim_spans(_row(text))[0]
    assert (
        fcf_temporal_claim_role(span, evidence_by_ref={})
        == FinancialClaimRole.PROSPECTIVE_VERIFICATION_REQUIREMENT
    )


@pytest.mark.parametrize(
    "text",
    (
        "현재 FCF가 개선됐다.",
        "FCF 개선이 이미 확인됐다.",
        "실제 FCF 개선이 증명됐다.",
        "현재 FCF는 100이다.",
        "현재 FCF가 악화돼 향후 개선이 필요하다.",
        "현재 FCF가 약해 개선이 필요하다.",
        "현재 현금흐름이 부족해 FCF 개선이 필요하다.",
        "FCF 개선은 필요하지만 현재 FCF는 이미 감소했다.",
        "FCF improvement is needed, but FCF has already declined.",
        "FCF is weak and needs to improve.",
    ),
)
def test_current_fcf_claims_remain_hard_without_current_fcf_evidence(
    text: str,
) -> None:
    result = _validate(text)
    assert _requires_current(text)
    assert not result.valid
    assert result.unsupported_current_fcf_claim_count == 1
    assert "unsupported_current_fcf_claim" in result.errors


@pytest.mark.parametrize(
    "field",
    (
        "buy_drivers",
        "sell_drivers",
        "dominant_evidence",
    ),
)
def test_prospective_fcf_requirement_cannot_be_current_directional_evidence(
    field: str,
) -> None:
    candidate = {
        "ticker": "M12BG",
        field: [
            {
                "text": "FCF 개선의 입증이 필요하다.",
                "evidence_refs": [],
            }
        ],
    }
    result = validate_directional_financial_semantics(
        candidate,
        supplied_refs=(),
        allowed_ref_ids=(),
    )

    assert not result.valid
    assert result.unsupported_current_fcf_claim_count == 0
    assert result.prospective_fcf_requirement_directional_violation_count == 1
    assert "prospective_fcf_requirement_used_as_current_directional_evidence" in result.errors


def test_core_judgment_can_state_an_unresolved_fcf_requirement() -> None:
    result = _validate(
        "FCF 개선의 추가 입증이 필요하다.",
        field="core_investment_judgment",
    )

    assert result.valid
    assert result.unsupported_current_fcf_claim_count == 0
    assert result.prospective_fcf_requirement_directional_violation_count == 0


def test_m12bg_contract_version_is_frozen() -> None:
    assert FCF_PROSPECTIVE_REQUIREMENT_CONTRACT == "fcf-prospective-requirement-v1"
