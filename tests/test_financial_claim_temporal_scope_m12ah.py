from __future__ import annotations

import json
from decimal import Decimal

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
    FinancialClaimRole,
    financial_claim_role,
    validate_directional_financial_semantics,
)
from app.services.financial_framework_claim_service import (
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
        label="논리 약화 조건",
        statement=statement,
        source_ref="stock.thesis.weaken_signals",
    )


def _financial_ref(metric: str) -> DecisionEvidenceRef:
    return DecisionEvidenceRef(
        ref_id=f"canonical:{metric}",
        category=EvidenceCategory.EARNINGS,
        label=metric,
        statement=json.dumps({"value": "100"}),
        value=Decimal("100"),
        unit="USD",
        source_ref=f"stock.fact_catalog.{metric}",
        financial_context=FinancialContext(
            metric=metric,
            currency="USD",
            unit_scale=1,
            period=FinancialPeriod(
                type=FinancialPeriodType.POINT_IN_TIME,
                end="2026-06-30",
            ),
            entity_scope="consolidated",
            statement_basis="formal_financial_statement",
            evidence_status=(
                FinancialEvidenceStatus.DERIVED_SAFE
                if metric == "net_debt"
                else FinancialEvidenceStatus.DIRECT_REPORTED
            ),
            quality=FinancialEvidenceQuality.VERIFIED,
            derivation=(
                FinancialDerivation(
                    formula="net_debt",
                    input_source_refs=(
                        "stock.fact_catalog.interest_bearing_debt_total",
                        "stock.fact_catalog.cash_and_cash_equivalents",
                    ),
                    version="m12ah-fixture-v1",
                )
                if metric == "net_debt"
                else None
            ),
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


def _role(
    candidate: dict[str, object], refs: tuple[DecisionEvidenceRef, ...]
) -> FinancialClaimRole:
    claims = tuple(claim for claim in _claims(candidate, refs) if claim.text)
    assert len(claims) == 1
    return financial_claim_role(
        claims[0],
        evidence_by_ref={ref.ref_id: ref for ref in refs},
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
        "현금창출 감소와 순부채 증가가 핵심 위험이다.",
        "현금창출 악화와 순부채 증가의 동반 발생이 주요 리스크다.",
        "순부채 증가 위험을 모니터링한다.",
        "weaker cash generation alongside rising net debt is a key risk",
        "the risk of net debt increasing while FCF weakens",
    ),
)
def test_temp_p01_to_p03_prospective_risk_context_passes(text: str) -> None:
    ref = _configured_ref()
    candidate = {
        "risk_context": {"text": text, "evidence_refs": [ref.ref_id]}
    }
    assert _role(candidate, (ref,)) == FinancialClaimRole.PROSPECTIVE_RISK_SCENARIO
    assert _validation(candidate, (ref,)).valid


def test_temp_p04_explicit_english_future_condition_passes() -> None:
    ref = _configured_ref()
    candidate = {
        "business_reevaluation_down": [
            {
                "text": "if FCF weakens while net debt rises, the thesis should be reevaluated",
                "evidence_refs": [ref.ref_id],
            }
        ]
    }
    assert _role(candidate, (ref,)) == FinancialClaimRole.FUTURE_REEVALUATION_CONDITION
    assert _validation(candidate, (ref,)).valid


def test_temp_p05_complete_current_net_debt_passes() -> None:
    ref = _financial_ref("net_debt")
    candidate = {
        "risk_context": {
            "text": "현재 순부채가 증가했다.",
            "evidence_refs": [ref.ref_id],
        }
    }
    assert _role(candidate, (ref,)) == FinancialClaimRole.CURRENT_DIRECTIONAL_BASIS
    assert _validation(candidate, (ref,)).valid


def test_temp_p06_conditional_numeric_threshold_is_not_current_numeric() -> None:
    ref = _configured_ref()
    candidate = {
        "business_reevaluation_down": [
            {
                "text": "if net debt / EBITDA exceeds 3x, reevaluate",
                "evidence_refs": [ref.ref_id],
            }
        ]
    }
    assert _role(candidate, (ref,)) == FinancialClaimRole.FUTURE_REEVALUATION_CONDITION
    assert _validation(candidate, (ref,)).valid


@pytest.mark.parametrize(
    "text",
    (
        "현재 순부채 부담이 높다.",
        "순부채가 증가했다.",
        "높은 순부채가 핵심 위험이다.",
        "순부채 증가는 이미 확인된 핵심 위험이다.",
        "net debt has increased",
        "net debt is currently high",
        "higher net debt is weighing on financial resilience",
    ),
)
def test_temp_n01_n02_n05_n06_current_claims_still_fail(text: str) -> None:
    configured = _configured_ref()
    candidate = {
        "risk_context": {
            "text": text,
            "evidence_refs": [configured.ref_id],
        }
    }
    assert _role(candidate, (configured,)) == FinancialClaimRole.CURRENT_DIRECTIONAL_BASIS
    result = _validation(candidate, (configured,))
    assert not result.valid
    assert "net_debt_claim_without_complete_net_debt_evidence" in result.errors


def test_temp_n03_always_current_sell_driver_still_fails() -> None:
    configured = _configured_ref()
    candidate = {
        "sell_drivers": [
            {
                "text": "순부채가 높아 SELL 근거다.",
                "evidence_refs": [configured.ref_id],
            }
        ]
    }
    assert _role(candidate, (configured,)) == FinancialClaimRole.CURRENT_DIRECTIONAL_BASIS
    assert not _validation(candidate, (configured,)).valid


def test_temp_n04_cross_field_current_use_overrides_prospective_context() -> None:
    configured = _configured_ref()
    candidate = {
        "risk_context": {
            "text": "순부채 증가가 핵심 위험이다.",
            "evidence_refs": [configured.ref_id],
        },
        "sell_drivers": [
            {
                "text": "순부채가 높아 SELL 근거다.",
                "evidence_refs": [configured.ref_id],
            }
        ],
    }
    result = _validation(candidate, (configured,))
    assert not result.valid
    assert result.partial_debt_total_claim_count == 1


@pytest.mark.parametrize(
    "text",
    (
        "순부채 증가가 부담이다.",
        "net debt growth is a concern.",
    ),
)
def test_temp_ambiguous_without_configured_provenance_fails_closed(text: str) -> None:
    partial = _financial_ref("short_term_borrowings")
    candidate = {
        "risk_context": {"text": text, "evidence_refs": [partial.ref_id]}
    }
    assert _role(candidate, (partial,)) == FinancialClaimRole.UNKNOWN_OR_AMBIGUOUS
    assert not _validation(candidate, (partial,)).valid


def test_temp_provenance_conflict_does_not_launder_partial_current_ref() -> None:
    configured = _configured_ref()
    partial = _financial_ref("short_term_borrowings")
    candidate = {
        "risk_context": {
            "text": "현금창출 감소와 순부채 증가가 핵심 위험이다.",
            "evidence_refs": [configured.ref_id, partial.ref_id],
        }
    }
    assert _role(candidate, (configured, partial)) == FinancialClaimRole.UNKNOWN_OR_AMBIGUOUS
    assert not _validation(candidate, (configured, partial)).valid


def test_temp_mixed_current_and_prospective_clause_fails_closed() -> None:
    configured = _configured_ref()
    candidate = {
        "risk_context": {
            "text": "현재 현금창출이 약하고, 순부채가 더 증가하는 경우가 핵심 위험이다.",
            "evidence_refs": [configured.ref_id],
        }
    }
    assert _role(candidate, (configured,)) == FinancialClaimRole.CURRENT_DIRECTIONAL_BASIS
    assert not _validation(candidate, (configured,)).valid


def test_m12ag_005490_exact_risk_context_replays_as_prospective() -> None:
    refs = (
        _configured_ref(
            "decision-evidence:30eb7b45f4a7dacf1700",
            statement="FCF 감소와 순부채 증가가 동반",
        ),
        _configured_ref(
            "decision-evidence:94be39ae695cc6dc42e4",
            statement="CAPEX 증가에도 ROIC가 하락",
        ),
        _configured_ref(
            "decision-evidence:c0703efb51b207666566",
            statement="전환·희석 가능 주식수가 의미 있게 증가",
        ),
    )
    candidate = {
        "risk_context": {
            "text": (
                "현금창출과 순부채의 동반 악화, 투자 대비 자본효율 하락, "
                "희석 확대가 핵심 위험이다."
            ),
            "evidence_refs": [ref.ref_id for ref in refs],
        }
    }
    assert _role(candidate, refs) == FinancialClaimRole.PROSPECTIVE_RISK_SCENARIO
    result = _validation(candidate, refs)
    assert result.valid, result
    assert result.partial_debt_total_claim_count == 0
