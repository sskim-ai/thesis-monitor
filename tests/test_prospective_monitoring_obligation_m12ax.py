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
    PROSPECTIVE_MONITORING_OBLIGATION_CONTRACT,
    FinancialClaimRole,
    _prospective_monitoring_obligation_family,
    financial_claim_role,
    validate_directional_financial_semantics,
)
from app.services.financial_framework_claim_service import (
    FrameworkClaim,
    candidate_financial_framework_claims,
)


def _configured_ref(
    *,
    source_ref: str = "stock.thesis.weaken_signals",
    statement: str = "현금창출력 감소와 순부채 증가가 동반",
) -> DecisionEvidenceRef:
    return DecisionEvidenceRef(
        ref_id=f"configured:{source_ref.rsplit('.', 1)[-1]}",
        category=EvidenceCategory.RISKS,
        label="설정된 미래 논리 조건",
        statement=statement,
        source_ref=source_ref,
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


def _risk_candidate(text: str, refs: tuple[DecisionEvidenceRef, ...]) -> dict[str, object]:
    return {
        "risk_context": {
            "text": text,
            "evidence_refs": [ref.ref_id for ref in refs],
        }
    }


def _claims(
    candidate: dict[str, object], refs: tuple[DecisionEvidenceRef, ...]
) -> tuple[FrameworkClaim, ...]:
    metric_by_ref = {
        ref.ref_id: ref.financial_context.metric
        for ref in refs
        if ref.financial_context is not None
    }
    return tuple(
        claim
        for claim in candidate_financial_framework_claims(candidate, metric_by_ref=metric_by_ref)
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


def _validation(candidate: dict[str, object], refs: tuple[DecisionEvidenceRef, ...]):
    return validate_directional_financial_semantics(
        candidate,
        supplied_refs=refs,
        allowed_ref_ids=tuple(ref.ref_id for ref in refs),
    )


def test_monitoring_obligation_contract_version_is_frozen() -> None:
    assert (
        PROSPECTIVE_MONITORING_OBLIGATION_CONTRACT
        == "prospective-financial-monitoring-obligation-v1"
    )


@pytest.mark.parametrize(
    ("text", "source_ref", "family"),
    (
        (
            "현금창출력 감소와 순부채 증가의 동반 여부를 감시해야 한다.",
            "stock.thesis.weaken_signals",
            "KOREAN_GAMSI",
        ),
        (
            "순부채 증가 여부를 모니터링해야 한다.",
            "stock.thesis.weaken_signals",
            "KOREAN_MONITORING",
        ),
        (
            "순부채 악화 여부를 주시해야 한다.",
            "stock.thesis.invalidation_signals",
            "KOREAN_JUSI",
        ),
        (
            "순부채 증가를 추적해야 한다.",
            "stock.thesis.weaken_signals",
            "KOREAN_TRACK",
        ),
        (
            "순부채 증가 여부를 점검해야 한다.",
            "stock.thesis.weaken_signals",
            "KOREAN_INSPECT",
        ),
        (
            "monitor whether cash generation weakens and net debt rises.",
            "stock.thesis.weaken_signals",
            "ENGLISH_MONITOR",
        ),
        (
            "net-debt deterioration should be monitored.",
            "stock.thesis.invalidation_signals",
            "ENGLISH_MONITOR",
        ),
        (
            "the net-debt risk needs monitoring.",
            "stock.thesis.invalidation_signals",
            "ENGLISH_MONITOR",
        ),
    ),
)
def test_supported_monitoring_obligations_are_prospective(
    text: str, source_ref: str, family: str
) -> None:
    configured = _configured_ref(source_ref=source_ref)
    candidate = _risk_candidate(text, (configured,))
    assert _prospective_monitoring_obligation_family(text) == family
    assert _roles(candidate, (configured,)) == (FinancialClaimRole.PROSPECTIVE_RISK_SCENARIO,)
    result = _validation(candidate, (configured,))
    assert result.valid, result
    assert result.partial_debt_total_claim_count == 0


def test_nonfinancial_current_clause_does_not_contaminate_monitoring_clause() -> None:
    configured = _configured_ref()
    candidate = _risk_candidate(
        "경쟁 위험은 현재 존재하며, 순부채 증가 여부는 감시해야 한다.",
        (configured,),
    )
    claims = _claims(candidate, (configured,))
    assert len(claims) == 1
    assert claims[0].local_clause_text == "순부채 증가 여부는 감시해야 한다"
    assert _roles(candidate, (configured,)) == (FinancialClaimRole.PROSPECTIVE_RISK_SCENARIO,)
    assert _validation(candidate, (configured,)).valid


@pytest.mark.parametrize(
    "text",
    (
        "현재 순부채가 높아 감시해야 한다.",
        "순부채가 이미 증가해 모니터링해야 한다.",
        "순부채 증가가 확인돼 계속 주시해야 한다.",
        "현재 순부채가 높고 추가 증가 여부를 감시해야 한다.",
        "감시 대상이지만 현재 순부채가 과도하다.",
        "net debt is currently high and must be monitored.",
    ),
)
def test_current_magnitude_or_fulfillment_keeps_precedence(text: str) -> None:
    configured = _configured_ref()
    candidate = _risk_candidate(text, (configured,))
    assert _roles(candidate, (configured,)) == (FinancialClaimRole.CURRENT_DIRECTIONAL_BASIS,)
    result = _validation(candidate, (configured,))
    assert not result.valid
    assert "net_debt_claim_without_complete_net_debt_evidence" in result.errors


def test_monitoring_obligation_without_configured_support_fails_closed() -> None:
    partial = _partial_debt_ref()
    candidate = _risk_candidate(
        "순부채 증가 여부를 감시해야 한다.",
        (partial,),
    )
    assert _roles(candidate, (partial,)) == (FinancialClaimRole.UNKNOWN_OR_AMBIGUOUS,)
    result = _validation(candidate, (partial,))
    assert not result.valid
    assert "net_debt_claim_without_complete_net_debt_evidence" in result.errors


def test_unrelated_configured_support_does_not_launder_monitoring_form() -> None:
    unrelated = _configured_ref(statement="재고 증가가 장기화")
    candidate = _risk_candidate(
        "순부채 증가 여부를 감시해야 한다.",
        (unrelated,),
    )
    assert _roles(candidate, (unrelated,)) == (FinancialClaimRole.UNKNOWN_OR_AMBIGUOUS,)
    assert not _validation(candidate, (unrelated,)).valid


def test_current_numeric_monitoring_form_requires_current_evidence() -> None:
    configured = _configured_ref()
    candidate = _risk_candidate("순부채 100 증가 여부를 감시해야 한다.", (configured,))
    assert _roles(candidate, (configured,)) == (FinancialClaimRole.CURRENT_NUMERIC_CLAIM,)
    assert not _validation(candidate, (configured,)).valid
