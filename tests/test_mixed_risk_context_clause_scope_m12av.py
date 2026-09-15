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
    ref_id: str = "configured:weaken-net-debt",
    *,
    statement: str = "FCF 감소와 순부채 증가가 동반",
) -> DecisionEvidenceRef:
    return DecisionEvidenceRef(
        ref_id=ref_id,
        category=EvidenceCategory.RISKS,
        label="설정된 미래 논리 조건",
        statement=statement,
        source_ref="stock.thesis.weaken_signals",
    )


def _structural_ref(ref_id: str = "current:structural-risk") -> DecisionEvidenceRef:
    return DecisionEvidenceRef(
        ref_id=ref_id,
        category=EvidenceCategory.RISKS,
        label="현재 구조적 위험",
        statement="현재 사업 구조에서 관찰된 비재무 위험",
        source_ref="stock.thesis.current_structural_risk",
    )


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
    return candidate_financial_framework_claims(
        candidate,
        metric_by_ref={
            ref.ref_id: ref.financial_context.metric
            for ref in refs
            if ref.financial_context is not None
        },
    )


def _roles(
    candidate: dict[str, object], refs: tuple[DecisionEvidenceRef, ...]
) -> tuple[FinancialClaimRole, ...]:
    evidence_by_ref = {ref.ref_id: ref for ref in refs}
    return tuple(
        financial_claim_role(claim, evidence_by_ref=evidence_by_ref)
        for claim in _claims(candidate, refs)
        if claim.framework == "net_debt" and claim.text
    )


def _validation(
    candidate: dict[str, object], refs: tuple[DecisionEvidenceRef, ...]
):
    return validate_directional_financial_semantics(
        candidate,
        supplied_refs=refs,
        allowed_ref_ids=tuple(ref.ref_id for ref in refs),
    )


@pytest.mark.parametrize(
    "text",
    (
        "경쟁에 따른 가격결정력 압박이 잠재 위험이며, 향후 구조적 현금유출이나 현금창출력·순부채의 동반 악화는 핵심 훼손 조건이다.",
        "운전자본 흡수가 지속될 가능성이 있으며, 향후 구조적 현금유출이나 현금창출력·순부채의 동반 악화는 핵심 위험 조건이다.",
        "비영업 지원이 반복되지 않을 가능성이 있으며, 향후 구조적 현금유출이나 현금창출력·순부채의 동반 악화는 핵심 위험 조건이다.",
    ),
)
def test_exact_m12au_mixed_risk_contexts_are_clause_local_prospective(
    text: str,
) -> None:
    structural = _structural_ref()
    configured = _configured_ref()
    candidate = {
        "risk_context": {
            "text": text,
            "evidence_refs": [structural.ref_id, configured.ref_id],
        }
    }
    claims = tuple(
        claim
        for claim in _claims(candidate, (structural, configured))
        if claim.framework == "net_debt" and claim.text
    )
    assert len(claims) == 1
    claim = claims[0]
    assert claim.span_contract == CLAIM_SPAN_CONTRACT_VERSION
    assert claim.full_field_text == text
    assert claim.local_clause_text.startswith("향후 구조적 현금유출")
    assert text[claim.local_clause_start : claim.local_clause_end] == claim.local_clause_text
    assert _roles(candidate, (structural, configured)) == (
        FinancialClaimRole.PROSPECTIVE_RISK_SCENARIO,
    )
    result = _validation(candidate, (structural, configured))
    assert result.valid, result
    assert result.partial_debt_total_claim_count == 0


@pytest.mark.parametrize(
    ("text", "expected_local"),
    (
        (
            "가격 압박이 현재 위험이며 향후 순부채가 증가하면 재평가한다.",
            "향후 순부채가 증가하면 재평가한다",
        ),
        (
            "가격 압박이 현재 위험이다: 향후 순부채가 증가하면 재평가한다.",
            "향후 순부채가 증가하면 재평가한다",
        ),
        (
            "competitive pressure is current while future net debt deterioration would trigger review.",
            "future net debt deterioration would trigger review",
        ),
    ),
)
def test_bounded_clause_delimiters_isolate_financial_occurrence(
    text: str, expected_local: str
) -> None:
    configured = _configured_ref()
    candidate = {
        "risk_context": {
            "text": text,
            "evidence_refs": [configured.ref_id],
        }
    }
    claims = tuple(claim for claim in _claims(candidate, (configured,)) if claim.text)
    assert len(claims) == 1
    assert claims[0].local_clause_text == expected_local
    assert _roles(candidate, (configured,)) == (
        FinancialClaimRole.PROSPECTIVE_RISK_SCENARIO,
    )


def test_prior_valid_conditional_net_debt_context_remains_prospective() -> None:
    configured = _configured_ref()
    candidate = {
        "risk_context": {
            "text": "현금창출력과 순부채의 동반 악화가 확인되면 핵심 위험이다.",
            "evidence_refs": [configured.ref_id],
        }
    }
    assert _roles(candidate, (configured,)) == (
        FinancialClaimRole.PROSPECTIVE_RISK_SCENARIO,
    )
    assert _validation(candidate, (configured,)).valid


@pytest.mark.parametrize(
    "text",
    (
        "현재 순부채가 높다.",
        "순부채가 이미 증가했다.",
        "향후에도 현재 순부채가 높다.",
    ),
)
def test_current_net_debt_claims_keep_magnitude_precedence(text: str) -> None:
    configured = _configured_ref()
    candidate = {
        "risk_context": {"text": text, "evidence_refs": [configured.ref_id]}
    }
    assert _roles(candidate, (configured,)) == (
        FinancialClaimRole.CURRENT_DIRECTIONAL_BASIS,
    )
    result = _validation(candidate, (configured,))
    assert not result.valid
    assert "net_debt_claim_without_complete_net_debt_evidence" in result.errors


def test_same_framework_current_and_future_claims_preserve_current_failure() -> None:
    configured = _configured_ref()
    candidate = {
        "risk_context": {
            "text": "현재 순부채가 높고, 향후 순부채가 더 증가하면 논리를 하향 재평가한다.",
            "evidence_refs": [configured.ref_id],
        }
    }
    assert _roles(candidate, (configured,)) == (
        FinancialClaimRole.CURRENT_DIRECTIONAL_BASIS,
        FinancialClaimRole.PROSPECTIVE_RISK_SCENARIO,
    )
    result = _validation(candidate, (configured,))
    assert not result.valid
    assert result.partial_debt_total_claim_count == 1


def test_unrelated_configured_ref_does_not_launder_future_net_debt_claim() -> None:
    unrelated = _configured_ref(statement="재고 증가가 장기화")
    candidate = {
        "risk_context": {
            "text": "향후 순부채가 증가하면 핵심 위험이다.",
            "evidence_refs": [unrelated.ref_id],
        }
    }
    assert _roles(candidate, (unrelated,)) == (
        FinancialClaimRole.UNKNOWN_OR_AMBIGUOUS,
    )
    assert not _validation(candidate, (unrelated,)).valid


def test_mixed_partial_current_ref_does_not_block_supported_future_clause() -> None:
    configured = _configured_ref()
    partial = _partial_debt_ref()
    candidate = {
        "risk_context": {
            "text": "경쟁 압박이 현재 위험이며, 향후 순부채가 증가하면 핵심 위험이다.",
            "evidence_refs": [partial.ref_id, configured.ref_id],
        }
    }
    assert _roles(candidate, (partial, configured)) == (
        FinancialClaimRole.PROSPECTIVE_RISK_SCENARIO,
    )
    assert _validation(candidate, (partial, configured)).valid


def test_business_reevaluation_contract_is_unchanged() -> None:
    configured = _configured_ref()
    candidate = {
        "business_reevaluation_down": [
            {
                "text": "현금창출력 감소와 순부채 확대가 함께 확인되면 하향 재평가한다.",
                "evidence_refs": [configured.ref_id],
            }
        ]
    }
    assert _roles(candidate, (configured,)) == (
        FinancialClaimRole.FUTURE_REEVALUATION_CONDITION,
    )
    assert _validation(candidate, (configured,)).valid
