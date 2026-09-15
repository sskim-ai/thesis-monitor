from __future__ import annotations

from decimal import Decimal

import pytest

from app.services.cross_market_decision_engine_service import (
    DecisionEvidenceRef,
    EvidenceCategory,
    FinancialContext,
    FinancialEvidenceQuality,
    FinancialEvidenceStatus,
    FinancialPeriod,
    FinancialPeriodType,
)
from app.services.directional_financial_context_service import (
    PROSPECTIVE_CONDITION_NOMINALIZATION_CONTRACT,
    FinancialClaimRole,
    financial_claim_role,
    validate_directional_financial_semantics,
)
from app.services.financial_framework_claim_service import (
    CLAIM_SPAN_CONTRACT_VERSION,
    FrameworkClaim,
    candidate_financial_framework_claims,
)


def _configured_ref(
    *,
    source_ref: str = "stock.thesis.weaken_signals",
    statement: str = "현금창출 저하와 순부채 증가가 동반",
) -> DecisionEvidenceRef:
    return DecisionEvidenceRef(
        ref_id=f"configured:{source_ref.rsplit('.', 1)[-1]}",
        category=EvidenceCategory.RISKS,
        label="설정된 미래 논리 조건",
        statement=statement,
        source_ref=source_ref,
    )


def _unrelated_ref() -> DecisionEvidenceRef:
    return _configured_ref(statement="재고 증가가 장기화")


def _partial_debt_ref() -> DecisionEvidenceRef:
    return DecisionEvidenceRef(
        ref_id="canonical:short-term-borrowings",
        category=EvidenceCategory.EARNINGS,
        label="단기차입금",
        statement="100",
        value=Decimal("100"),
        unit="USD",
        source_ref="stock.fact_catalog.short_term_borrowings",
        financial_context=FinancialContext(
            metric="short_term_borrowings",
            currency="USD",
            unit_scale=1,
            period=FinancialPeriod(
                type=FinancialPeriodType.POINT_IN_TIME,
                end="2026-06-30",
            ),
            entity_scope="consolidated",
            statement_basis="formal_financial_statement",
            evidence_status=FinancialEvidenceStatus.DIRECT_REPORTED,
            quality=FinancialEvidenceQuality.VERIFIED,
        ),
    )


def _claims(
    candidate: dict[str, object], refs: tuple[DecisionEvidenceRef, ...]
) -> tuple[FrameworkClaim, ...]:
    return tuple(
        claim
        for claim in candidate_financial_framework_claims(
            candidate,
            metric_by_ref={
                ref.ref_id: ref.financial_context.metric
                for ref in refs
                if ref.financial_context is not None
            },
        )
        if claim.framework == "net_debt" and claim.text
    )


def _roles(
    candidate: dict[str, object], refs: tuple[DecisionEvidenceRef, ...]
) -> tuple[FinancialClaimRole, ...]:
    evidence_by_ref = {ref.ref_id: ref for ref in refs}
    return tuple(
        financial_claim_role(claim, evidence_by_ref=evidence_by_ref)
        for claim in _claims(candidate, refs)
    )


def _validation(
    candidate: dict[str, object], refs: tuple[DecisionEvidenceRef, ...]
):
    return validate_directional_financial_semantics(
        candidate,
        supplied_refs=refs,
        allowed_ref_ids=tuple(ref.ref_id for ref in refs),
    )


def _risk_candidate(text: str, refs: tuple[DecisionEvidenceRef, ...]) -> dict[str, object]:
    return {
        "risk_context": {
            "text": text,
            "evidence_refs": [ref.ref_id for ref in refs],
        }
    }


def test_contract_version_is_frozen() -> None:
    assert (
        PROSPECTIVE_CONDITION_NOMINALIZATION_CONTRACT
        == "prospective-financial-condition-nominalization-v1"
    )


@pytest.mark.parametrize(
    ("text", "source_ref"),
    (
        (
            "현금창출 저하와 순부채 증가의 동반 확인은 추가 하향 조건이다.",
            "stock.thesis.weaken_signals",
        ),
        ("순부채 증가 확인이 하향 재평가 조건이다.", "stock.thesis.weaken_signals"),
        ("순부채 증가의 발생은 무효화 조건이다.", "stock.thesis.invalidation_signals"),
        ("순부채 증가는 모니터링할 약화 조건이다.", "stock.thesis.weaken_signals"),
        (
            "confirmation of worsening net debt would be a downside condition.",
            "stock.thesis.weaken_signals",
        ),
        (
            "confirmation of worsening net debt is a reevaluation trigger.",
            "stock.thesis.weaken_signals",
        ),
        (
            "net debt worsening is a monitored downside condition.",
            "stock.thesis.weaken_signals",
        ),
    ),
)
def test_nom_cond_p01_to_p05_are_supported_prospective_conditions(
    text: str, source_ref: str
) -> None:
    configured = _configured_ref(source_ref=source_ref)
    candidate = _risk_candidate(text, (configured,))
    claims = _claims(candidate, (configured,))
    assert len(claims) == 1
    assert claims[0].span_contract == CLAIM_SPAN_CONTRACT_VERSION
    assert _roles(candidate, (configured,)) == (
        FinancialClaimRole.PROSPECTIVE_RISK_SCENARIO,
    )
    result = _validation(candidate, (configured,))
    assert result.valid, result
    assert result.partial_debt_total_claim_count == 0


@pytest.mark.parametrize(
    "text",
    (
        "순부채 증가가 확인됐다.",
        "현금창출 저하와 순부채 증가가 함께 확인됐다.",
        "순부채가 증가했고 이는 하향 조건이다.",
        "순부채 증가의 확인은 하향 조건이며 현재 이미 충족됐다.",
        "현재 순부채가 높다는 점이 하향 조건이다.",
        "confirmation of net debt growth has occurred and is a downside condition.",
    ),
)
def test_nom_cond_current_negative_fixtures_remain_current(text: str) -> None:
    configured = _configured_ref()
    candidate = _risk_candidate(text, (configured,))
    assert _roles(candidate, (configured,)) == (
        FinancialClaimRole.CURRENT_DIRECTIONAL_BASIS,
    )
    result = _validation(candidate, (configured,))
    assert not result.valid
    assert "net_debt_claim_without_complete_net_debt_evidence" in result.errors


def test_nom_cond_n05_without_configured_support_fails_closed() -> None:
    partial = _partial_debt_ref()
    candidate = _risk_candidate("순부채 증가는 하향 조건이다.", (partial,))
    assert _roles(candidate, (partial,)) == (
        FinancialClaimRole.UNKNOWN_OR_AMBIGUOUS,
    )
    result = _validation(candidate, (partial,))
    assert not result.valid
    assert "net_debt_claim_without_complete_net_debt_evidence" in result.errors


def test_framework_unrelated_configured_support_does_not_launder_nominal_form() -> None:
    unrelated = _unrelated_ref()
    candidate = _risk_candidate("순부채 증가는 하향 조건이다.", (unrelated,))
    assert _roles(candidate, (unrelated,)) == (
        FinancialClaimRole.UNKNOWN_OR_AMBIGUOUS,
    )
    assert not _validation(candidate, (unrelated,)).valid


def test_same_field_nonfinancial_current_and_nominal_future_are_clause_local() -> None:
    configured = _configured_ref()
    text = "현재 경쟁 압박은 위험이며, 순부채 증가의 확인은 추가 하향 조건이다."
    candidate = _risk_candidate(text, (configured,))
    claims = _claims(candidate, (configured,))
    assert len(claims) == 1
    assert claims[0].local_clause_text == "순부채 증가의 확인은 추가 하향 조건이다"
    assert _roles(candidate, (configured,)) == (
        FinancialClaimRole.PROSPECTIVE_RISK_SCENARIO,
    )
    assert _validation(candidate, (configured,)).valid


def test_same_local_clause_current_fulfillment_keeps_current_precedence() -> None:
    configured = _configured_ref()
    candidate = _risk_candidate(
        "현재 순부채가 증가했고 이 증가는 하향 조건이다.", (configured,)
    )
    assert _roles(candidate, (configured,)) == (
        FinancialClaimRole.CURRENT_DIRECTIONAL_BASIS,
    )
    assert not _validation(candidate, (configured,)).valid


def test_current_numeric_nominal_form_does_not_use_nominal_exemption() -> None:
    configured = _configured_ref()
    candidate = _risk_candidate("순부채 100 증가는 하향 조건이다.", (configured,))
    assert _roles(candidate, (configured,)) == (
        FinancialClaimRole.CURRENT_NUMERIC_CLAIM,
    )
    assert not _validation(candidate, (configured,)).valid
