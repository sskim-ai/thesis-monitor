from __future__ import annotations

import json
from decimal import Decimal

from app.services.cross_market_decision_engine_service import (
    DecisionEvidencePacket,
    DecisionEvidenceRef,
    EvidenceCategory,
    FinancialContext,
    FinancialDerivation,
    FinancialEvidenceQuality,
    FinancialEvidenceStatus,
    FinancialPeriod,
    FinancialPeriodType,
)
from app.services.direction_timing_ownership_service import (
    CORE_DOMAINS,
    TIMING_DOMAINS,
    EvidenceDomain,
    MonitoringTransitionSourceClass,
    build_owned_evidence_packet,
    monitoring_transition_source_class,
    stage_alias_catalogs,
)
from app.services.directional_financial_context_service import (
    FinancialClaimRole,
    financial_claim_role,
    validate_directional_financial_semantics,
)
from app.services.financial_framework_claim_service import (
    candidate_financial_framework_claims,
)
from scripts import business_delta_alias_balance_confidence_m12z as delta
from scripts import directional_core_price_timing_holdout as holdout


def _ref(
    fact_id: str,
    *,
    label: str = "monitoring_transition",
    category: EvidenceCategory = EvidenceCategory.EARNINGS_QUALITY,
    statement: str = "Comparable-period operating performance improved.",
    source_ref: str | None = None,
) -> DecisionEvidenceRef:
    return DecisionEvidenceRef(
        ref_id=f"canonical:{fact_id}",
        category=category,
        label=label,
        statement=statement,
        source_ref=source_ref or f"stock.fact_catalog.{fact_id}",
    )


def _packet(refs: tuple[DecisionEvidenceRef, ...]) -> DecisionEvidencePacket:
    return DecisionEvidencePacket(
        packet_id="m12ag-fixture",
        ticker="M12AG",
        company_name="M12AG Fixture",
        market="us",
        assessment_date="2026-09-11",
        horizon="12m",
        evidence=refs,
        prohibited_claims=(),
        evidence_sha256="m12ag-fixture-sha",
    )


def _ownership_fixture():
    confirmation = _ref(
        "monitoring:confirmation_transition",
        statement='{"transition":"crossed_to_holding_above"}',
    )
    risk_reward = _ref(
        "monitoring:risk_reward_transition",
        label="monitoring_metric_transition",
        statement='{"change_state":"deteriorated"}',
    )
    operating = _ref(
        "monitoring:operating_transition",
        category=EvidenceCategory.EARNINGS,
    )
    supply = _ref(
        "monitoring:supply_transition",
        category=EvidenceCategory.FLOWS,
        statement="Investor flow strengthened.",
    )
    unknown = _ref(
        "monitoring:unregistered_transition",
        statement="Unknown transition improved.",
    )
    stock = {
        "fact_catalog": [
            {
                "fact_id": "monitoring:operating_transition",
                "evidence_family": "BUSINESS_CURRENT",
            },
            {
                "fact_id": "monitoring:supply_transition",
                "evidence_family": "SUPPLY_POSITIONING",
            },
        ]
    }
    owned = build_owned_evidence_packet(
        _packet((confirmation, risk_reward, operating, supply, unknown)),
        stock=stock,
    )
    return confirmation, risk_reward, operating, supply, unknown, owned


def test_own_01_to_05_source_aware_transition_taxonomy_and_routing() -> None:
    confirmation, risk_reward, operating, supply, unknown, owned = (
        _ownership_fixture()
    )
    families = {
        "monitoring:operating_transition": "BUSINESS_CURRENT",
        "monitoring:supply_transition": "SUPPLY_POSITIONING",
    }
    assert monitoring_transition_source_class(
        confirmation, fact_family_by_id=families
    ) == MonitoringTransitionSourceClass.PRICE_CONFIRMATION_TRANSITION
    assert monitoring_transition_source_class(
        risk_reward, fact_family_by_id=families
    ) == MonitoringTransitionSourceClass.PRICE_RISK_REWARD_TRANSITION
    assert monitoring_transition_source_class(
        operating, fact_family_by_id=families
    ) == MonitoringTransitionSourceClass.FUNDAMENTAL_BUSINESS_TRANSITION
    assert monitoring_transition_source_class(
        supply, fact_family_by_id=families
    ) == MonitoringTransitionSourceClass.SUPPLY_FLOW_TRANSITION
    assert monitoring_transition_source_class(
        unknown, fact_family_by_id=families
    ) == MonitoringTransitionSourceClass.UNKNOWN_MONITORING_TRANSITION

    domains = owned.domain_by_ref
    assert domains[confirmation.ref_id] == EvidenceDomain.TECHNICAL_STATE
    assert domains[risk_reward.ref_id] == EvidenceDomain.RISK_REWARD_PRICE
    assert domains[operating.ref_id] == EvidenceDomain.BUSINESS_CURRENT
    assert domains[supply.ref_id] == EvidenceDomain.SUPPLY_POSITIONING
    assert domains[unknown.ref_id] == EvidenceDomain.AUDIT_TELEMETRY
    assert operating.ref_id in owned.core_refs
    assert confirmation.ref_id in owned.timing_refs
    assert risk_reward.ref_id in owned.timing_refs
    assert supply.ref_id in owned.timing_refs
    assert unknown.ref_id not in owned.core_refs | owned.timing_refs
    assert all(domains[ref] in CORE_DOMAINS for ref in owned.core_refs)
    assert all(domains[ref] in TIMING_DOMAINS for ref in owned.timing_refs)

    core, timing = stage_alias_catalogs(owned)
    assert confirmation.ref_id not in core.by_ref
    assert risk_reward.ref_id not in core.by_ref
    assert confirmation.ref_id in timing.by_ref
    assert risk_reward.ref_id in timing.by_ref


def _delta_fixture():
    confirmation, risk_reward, operating, supply, unknown, owned = (
        _ownership_fixture()
    )
    current_thesis = DecisionEvidenceRef(
        ref_id="decision-evidence:current-thesis",
        category=EvidenceCategory.THESIS,
        label="핵심 투자 논리",
        statement="The current thesis is favorable and operating quality improved.",
        source_ref="stock.thesis.core_thesis",
    )
    deterioration = _ref(
        "fundamental:margin-deterioration",
        category=EvidenceCategory.EARNINGS,
        statement="Comparable-period operating margin deteriorated.",
    )
    packet = _packet(
        (
            confirmation,
            risk_reward,
            operating,
            supply,
            unknown,
            current_thesis,
            deterioration,
        )
    )
    stock = {
        "fact_catalog": [
            {
                "fact_id": "monitoring:operating_transition",
                "evidence_family": "BUSINESS_CURRENT",
            },
            {
                "fact_id": "monitoring:supply_transition",
                "evidence_family": "SUPPLY_POSITIONING",
            },
            {
                "fact_id": "fundamental:margin-deterioration",
                "evidence_family": "EARNINGS_FINANCIAL_CURRENT",
            },
        ]
    }
    owned = build_owned_evidence_packet(packet, stock=stock)
    core_catalog, _ = stage_alias_catalogs(owned)
    context = holdout._owned_context(owned, core_catalog)
    return {
        "confirmation": confirmation,
        "risk_reward": risk_reward,
        "operating": operating,
        "current_thesis": current_thesis,
        "deterioration": deterioration,
        "owned": owned,
        "catalog": core_catalog,
        "context": context,
    }


def _delta_candidate(change: str, refs: tuple[str, ...]) -> dict[str, object]:
    return {
        "ticker": "M12AG",
        "business_thesis_change": change,
        "business_thesis_context": {"evidence_refs": list(refs)},
    }


def test_delta_real_01_price_confirmation_cannot_strengthen() -> None:
    fixture = _delta_fixture()
    result = delta.business_delta_audit(
        _delta_candidate("STRENGTHENED", (fixture["confirmation"].ref_id,)),
        fixture["context"],
        fixture["catalog"],
        owned=fixture["owned"],
    )
    assert result["status"] == "FAIL"


def test_delta_real_02_risk_reward_cannot_weaken() -> None:
    fixture = _delta_fixture()
    result = delta.business_delta_audit(
        _delta_candidate("WEAKENED", (fixture["risk_reward"].ref_id,)),
        fixture["context"],
        fixture["catalog"],
        owned=fixture["owned"],
    )
    assert result["status"] == "FAIL"


def test_delta_real_03_current_favorable_thesis_is_not_change_evidence() -> None:
    fixture = _delta_fixture()
    result = delta.business_delta_audit(
        _delta_candidate("STRENGTHENED", (fixture["current_thesis"].ref_id,)),
        fixture["context"],
        fixture["catalog"],
        owned=fixture["owned"],
    )
    assert result["status"] == "FAIL"
    assert result["linked_evidence"][0]["delta_evidence_eligible"] is False


def test_delta_real_04_fundamental_operating_change_can_strengthen() -> None:
    fixture = _delta_fixture()
    result = delta.business_delta_audit(
        _delta_candidate("STRENGTHENED", (fixture["operating"].ref_id,)),
        fixture["context"],
        fixture["catalog"],
        owned=fixture["owned"],
    )
    assert result["status"] == "PASS", result


def test_delta_real_05_conflicting_fundamental_changes_can_be_unresolved() -> None:
    fixture = _delta_fixture()
    result = delta.business_delta_audit(
        _delta_candidate(
            "UNRESOLVED",
            (
                fixture["operating"].ref_id,
                fixture["deterioration"].ref_id,
            ),
        ),
        fixture["context"],
        fixture["catalog"],
        owned=fixture["owned"],
    )
    assert result["status"] == "PASS", result


def _financial_ref(metric: str) -> DecisionEvidenceRef:
    source_ref = f"stock.fact_catalog.{metric}"
    return DecisionEvidenceRef(
        ref_id=f"canonical:{metric}",
        category=EvidenceCategory.EARNINGS,
        label=metric,
        statement=json.dumps({"value": "100"}),
        value=Decimal("100"),
        unit="USD",
        source_ref=source_ref,
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
                    version="m12ag-fixture-v1",
                )
                if metric == "net_debt"
                else None
            ),
        ),
    )


def _financial_validation(
    candidate: dict[str, object], refs: tuple[DecisionEvidenceRef, ...]
):
    return validate_directional_financial_semantics(
        candidate,
        supplied_refs=refs,
        allowed_ref_ids=tuple(ref.ref_id for ref in refs),
    )


def test_net_01_current_unsupported_net_debt_claim_fails() -> None:
    component = _financial_ref("short_term_borrowings")
    result = _financial_validation(
        {"claims": [{"text": "순부채가 증가했다.", "evidence_refs": [component.ref_id]}]},
        (component,),
    )
    assert not result.valid
    assert "net_debt_claim_without_complete_net_debt_evidence" in result.errors


def test_net_02_current_unsupported_directional_basis_fails() -> None:
    component = _financial_ref("short_term_borrowings")
    result = _financial_validation(
        {
            "sell_drivers": [
                {
                    "text": "순부채 부담이 현재 SELL 근거다.",
                    "evidence_refs": [component.ref_id],
                }
            ]
        },
        (component,),
    )
    assert not result.valid


def test_net_03_conditional_future_net_debt_check_passes() -> None:
    component = _financial_ref("short_term_borrowings")
    candidate = {
        "business_reevaluation_down": [
            {
                "text": "순부채 증가가 확인되면 논리가 약화된다.",
                "evidence_refs": [component.ref_id],
            }
        ]
    }
    result = _financial_validation(candidate, (component,))
    claims = candidate_financial_framework_claims(candidate)
    assert financial_claim_role(claims[0]) == FinancialClaimRole.FUTURE_REEVALUATION_CONDITION
    assert result.valid, result


def test_net_04_configured_weakening_condition_passes() -> None:
    component = _financial_ref("short_term_borrowings")
    result = _financial_validation(
        {
            "business_reevaluation_down": [
                {
                    "text": "FCF 감소와 순부채 증가가 함께 나타나면 재평가한다.",
                    "evidence_refs": [component.ref_id],
                }
            ]
        },
        (component,),
    )
    assert result.valid, result


def test_net_05_conditional_text_does_not_immunize_current_claim_elsewhere() -> None:
    component = _financial_ref("short_term_borrowings")
    result = _financial_validation(
        {
            "business_reevaluation_down": [
                {
                    "text": "순부채가 늘어나는 경우 재평가한다.",
                    "evidence_refs": [component.ref_id],
                }
            ],
            "risk_context": {
                "text": "순부채가 이미 증가해 현재 부담이다.",
                "evidence_refs": [component.ref_id],
            },
        },
        (component,),
    )
    assert not result.valid


def test_net_06_complete_typed_net_debt_supports_current_assertion() -> None:
    net_debt = _financial_ref("net_debt")
    result = _financial_validation(
        {
            "risk_context": {
                "text": "순부채가 현재 증가한 상태다.",
                "evidence_refs": [net_debt.ref_id],
            }
        },
        (net_debt,),
    )
    assert result.valid, result
