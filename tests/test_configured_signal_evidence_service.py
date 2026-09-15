from datetime import date

from app.services.configured_signal_evidence_service import (
    ConfiguredSignalFulfillmentEvidence,
    ConfiguredSignalFulfillmentState,
    build_configured_signal_evidence_view,
    validate_configured_signal_field_ownership,
)
from app.services.cross_market_decision_engine_service import (
    DecisionEvidenceRef,
    EvidenceCategory,
    FinancialComparison,
    FinancialComparisonKind,
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
    FrameworkClaim,
    FrameworkClaimKind,
    FrameworkReferenceRole,
)
from app.services.logical_condition_service import (
    LogicalSeverity,
    source_checkpoint_metric_refs,
    source_logical_condition,
)


def _configured_ref(
    ref_id: str = "configured:weaken",
    statement: str = "FCF 감소와 순부채 증가가 동반",
    source_ref: str = "stock.thesis.weaken_signals",
) -> DecisionEvidenceRef:
    return DecisionEvidenceRef(
        ref_id=ref_id,
        category=EvidenceCategory.RISKS,
        label="논리 약화 조건",
        statement=statement,
        as_of="2026-09-12",
        source_ref=source_ref,
        metric_refs=source_checkpoint_metric_refs(statement),
        logical_condition=source_logical_condition(
            subject="TEST",
            generation_id="generation",
            evidence_ref=ref_id,
            statement=statement,
            severity=LogicalSeverity.WEAKENING,
        ),
    )


def _financial_ref(ref_id: str, metric: str) -> DecisionEvidenceRef:
    return DecisionEvidenceRef(
        ref_id=ref_id,
        category=EvidenceCategory.EARNINGS_QUALITY,
        label=metric,
        statement=f"verified comparable {metric}",
        as_of="2026-09-12",
        source_ref=f"stock.fact_catalog.{metric}",
        financial_context=FinancialContext(
            metric=metric,
            currency="KRW",
            unit_scale=1,
            period=FinancialPeriod(
                type=FinancialPeriodType.POINT_IN_TIME,
                end=date(2026, 6, 30),
            ),
            entity_scope="consolidated",
            statement_basis="ifrs",
            evidence_status=FinancialEvidenceStatus.DIRECT_REPORTED,
            quality=FinancialEvidenceQuality.VERIFIED,
            comparison=FinancialComparison(
                kind=FinancialComparisonKind.PRIOR_YEAR_END,
                input_source_refs=(f"source.{metric}",),
            ),
        ),
    )


def _claim(ref_id: str) -> dict[str, object]:
    return {"text": "configured condition", "evidence_refs": [ref_id]}


def test_configured_only_signal_is_future_not_current_evidence() -> None:
    configured = _configured_ref()
    view = build_configured_signal_evidence_view(
        ticker="TEST", supplied_refs=(configured,)
    )
    item = view.by_ref[configured.ref_id]
    assert item.fulfillment_state == ConfiguredSignalFulfillmentState.CONFIGURED_ONLY
    assert not item.current_directional_driver_eligible
    assert item.future_reevaluation_eligible
    assert item.risk_context_eligible
    assert not item.material_anchor_eligible
    assert not item.dominant_evidence_eligible


def test_configured_signal_is_allowed_in_future_and_risk_fields() -> None:
    configured = _configured_ref()
    view = build_configured_signal_evidence_view(
        ticker="TEST", supplied_refs=(configured,)
    )
    candidate = {
        "ticker": "TEST",
        "business_reevaluation_down": [_claim(configured.ref_id)],
        "risk_context": _claim(configured.ref_id),
    }
    assert validate_configured_signal_field_ownership(candidate, view).valid


def test_configured_only_signal_is_rejected_from_current_fields() -> None:
    configured = _configured_ref()
    view = build_configured_signal_evidence_view(
        ticker="TEST", supplied_refs=(configured,)
    )
    candidates = (
        {"ticker": "TEST", "sell_drivers": [_claim(configured.ref_id)]},
        {"ticker": "TEST", "buy_drivers": [_claim(configured.ref_id)]},
        {
            "ticker": "TEST",
            "dominant_evidence": _claim(configured.ref_id),
        },
        {
            "ticker": "TEST",
            "core_investment_judgment": _claim(configured.ref_id),
        },
        {
            "ticker": "TEST",
            "material_directional_anchor_basis": [configured.ref_id],
        },
    )
    for candidate in candidates:
        result = validate_configured_signal_field_ownership(candidate, view)
        assert not result.valid
        assert result.errors == (
            "configured_future_signal_used_as_current_directional_driver",
        )
        assert result.configured_only_current_driver_violation_count == 1


def test_complete_current_net_debt_can_establish_fulfillment() -> None:
    configured = _configured_ref(
        statement="순부채 증가",
    )
    net_debt = _financial_ref("canonical:net-debt", "net_debt")
    view = build_configured_signal_evidence_view(
        ticker="TEST",
        supplied_refs=(configured, net_debt),
        verified_fulfillment_evidence=(
            ConfiguredSignalFulfillmentEvidence(
                signal_ref_id=configured.ref_id,
                current_evidence_refs=(net_debt.ref_id,),
            ),
        ),
    )
    item = view.by_ref[configured.ref_id]
    assert item.fulfillment_state == (
        ConfiguredSignalFulfillmentState.FULFILLED_BY_CURRENT_EVIDENCE
    )
    assert item.current_directional_driver_eligible
    assert validate_configured_signal_field_ownership(
        {"ticker": "TEST", "sell_drivers": [_claim(configured.ref_id)]},
        view,
    ).valid


def test_canonical_fcf_and_complete_net_debt_can_establish_joint_fulfillment() -> None:
    configured = _configured_ref(statement="FCF 감소와 순부채 증가가 동반")
    fcf = _financial_ref("canonical:fcf", "free_cash_flow_ppe")
    net_debt = _financial_ref("canonical:net-debt", "net_debt")
    view = build_configured_signal_evidence_view(
        ticker="TEST",
        supplied_refs=(configured, fcf, net_debt),
        verified_fulfillment_evidence=(
            ConfiguredSignalFulfillmentEvidence(
                signal_ref_id=configured.ref_id,
                current_evidence_refs=(fcf.ref_id, net_debt.ref_id),
            ),
        ),
    )

    assert view.by_ref[configured.ref_id].fulfillment_state == (
        ConfiguredSignalFulfillmentState.FULFILLED_BY_CURRENT_EVIDENCE
    )


def test_partial_debt_cannot_establish_net_debt_fulfillment() -> None:
    configured = _configured_ref(statement="순부채 증가")
    debt = _financial_ref("canonical:debt", "interest_bearing_debt_total")
    view = build_configured_signal_evidence_view(
        ticker="TEST",
        supplied_refs=(configured, debt),
        verified_fulfillment_evidence=(
            ConfiguredSignalFulfillmentEvidence(
                signal_ref_id=configured.ref_id,
                current_evidence_refs=(debt.ref_id,),
            ),
        ),
    )
    item = view.by_ref[configured.ref_id]
    assert item.fulfillment_state == ConfiguredSignalFulfillmentState.UNKNOWN
    assert not item.current_directional_driver_eligible


def test_ocf_ppe_proxy_cannot_establish_fcf_fulfillment() -> None:
    configured = _configured_ref(statement="FCF 감소")
    proxy = _financial_ref("canonical:proxy", "ocf_less_ppe_capex")
    view = build_configured_signal_evidence_view(
        ticker="TEST",
        supplied_refs=(configured, proxy),
        verified_fulfillment_evidence=(
            ConfiguredSignalFulfillmentEvidence(
                signal_ref_id=configured.ref_id,
                current_evidence_refs=(proxy.ref_id,),
            ),
        ),
    )
    assert view.by_ref[configured.ref_id].fulfillment_state == (
        ConfiguredSignalFulfillmentState.UNKNOWN
    )


def test_historical_condition_gets_field_error_not_net_debt_error() -> None:
    configured = _configured_ref()
    candidate = {
        "ticker": "TEST",
        "sell_drivers": [
            {
                "text": "현금창출 약화와 순부채 증가는 투자회수 논리를 훼손하는 조건이다.",
                "evidence_refs": [configured.ref_id],
            }
        ],
    }
    validation = validate_directional_financial_semantics(
        candidate,
        supplied_refs=(configured,),
        allowed_ref_ids=(configured.ref_id,),
    )
    assert "configured_future_signal_used_as_current_directional_driver" in (
        validation.errors
    )
    assert "net_debt_claim_without_complete_net_debt_evidence" not in (
        validation.errors
    )


def test_explicit_current_configured_claim_still_requires_current_evidence() -> None:
    configured = _configured_ref()
    candidate = {
        "ticker": "TEST",
        "sell_drivers": [
            {
                "text": "현재 FCF가 감소하고 순부채가 증가했다.",
                "evidence_refs": [configured.ref_id],
            }
        ],
    }
    validation = validate_directional_financial_semantics(
        candidate,
        supplied_refs=(configured,),
        allowed_ref_ids=(configured.ref_id,),
    )
    assert "configured_future_signal_used_as_current_directional_driver" in (
        validation.errors
    )
    assert "net_debt_claim_without_complete_net_debt_evidence" in validation.errors


def test_configured_claim_role_is_prospective_before_field_precedence() -> None:
    configured = _configured_ref()
    claim = FrameworkClaim(
        framework="net_debt",
        kind=FrameworkClaimKind.ASSERTION_OR_APPLICATION,
        role=FrameworkReferenceRole.APPLIED_DECISION_FRAMEWORK,
        field_path="sell_drivers[0].text",
        text="순부채 증가는 투자회수 논리를 훼손하는 조건이다.",
        evidence_refs=(configured.ref_id,),
    )
    assert financial_claim_role(
        claim,
        evidence_by_ref={configured.ref_id: configured},
    ) == FinancialClaimRole.CONFIGURED_CONDITIONAL_CHECK
