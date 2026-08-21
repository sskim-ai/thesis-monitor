from __future__ import annotations

import hashlib
from dataclasses import replace
from datetime import date
from decimal import Decimal

from app.services.cash_flow_capital_efficiency_service import (
    EligibilityStatus,
    FactType,
    FinancialFact,
    Metric,
    PeriodIdentity,
    PeriodType,
)
from app.services.working_capital_core_service import (
    WorkingCapitalCoreSnapshot,
    build_working_capital_core_snapshot,
)
from app.services.working_capital_shadow_consumption_service import (
    FreshnessState,
    UnknownResolutionState,
    UsageMode,
    build_working_capital_reasoning_context,
    render_working_capital_reasoning,
    validate_working_capital_reasoning,
)


CURRENT = date(2026, 6, 30)
PRIOR = date(2025, 6, 30)
AVAILABLE = date(2026, 8, 1)
CUTOFF = date(2026, 8, 21)


def _fact(
    metric: Metric,
    value: str,
    *,
    period_end: date,
    fiscal_year: int,
    semantic: str,
    available: date,
    balance_scope: str | None = None,
) -> FinancialFact:
    is_balance = metric in {
        Metric.INVENTORY,
        Metric.TRADE_AR,
        Metric.BROAD_AR,
        Metric.TRADE_AP,
        Metric.BROAD_AP,
    }
    start = period_end if is_balance else date(fiscal_year, 1, 1)
    token = hashlib.sha256(
        f"{metric.value}|{value}|{period_end}|{semantic}|{available}".encode()
    ).hexdigest()[:20]
    return FinancialFact(
        fact_id=f"fact:{token}",
        issuer_id="sec:0000000001",
        metric=metric,
        value=Decimal(value),
        currency="USD",
        unit="USD",
        period=PeriodIdentity(
            start=start,
            end=period_end,
            period_type=PeriodType.POINT_IN_TIME if is_balance else PeriodType.YTD,
            fiscal_year=fiscal_year,
            fiscal_quarter=2,
        ),
        entity_scope="issuer_level",
        statement_basis="issuer_reported",
        reported_or_derived="reported",
        source_provider="sec_edgar_companyfacts",
        source_document_id=f"document:{token}",
        filing_date=available,
        source_occurrence_id=f"occurrence:{token}",
        raw_payload_sha256=hashlib.sha256(token.encode()).hexdigest(),
        semantic_mapping=semantic,
        fact_type=FactType.REPORTED,
        source_document_type="10-Q",
        source_semantic=semantic,
        quality="REPORTED_VERIFIED",
        eligibility=EligibilityStatus.ELIGIBLE,
        restatement_policy_id="latest-authoritative-exact-semantic-v1",
        as_of_date=available,
        source_available_at=available,
        balance_scope=balance_scope,
        net_gross_scope="net" if balance_scope else None,
    )


def _flow_facts() -> list[FinancialFact]:
    return [
        _fact(
            Metric.REVENUE,
            "220",
            period_end=CURRENT,
            fiscal_year=2026,
            semantic="us-gaap:Revenues",
            available=AVAILABLE,
        ),
        _fact(
            Metric.REVENUE,
            "200",
            period_end=PRIOR,
            fiscal_year=2025,
            semantic="us-gaap:Revenues",
            available=date(2025, 8, 1),
        ),
        _fact(
            Metric.COGS,
            "165",
            period_end=CURRENT,
            fiscal_year=2026,
            semantic="us-gaap:CostOfRevenue",
            available=AVAILABLE,
        ),
        _fact(
            Metric.COGS,
            "150",
            period_end=PRIOR,
            fiscal_year=2025,
            semantic="us-gaap:CostOfRevenue",
            available=date(2025, 8, 1),
        ),
    ]


def _balance_pair(metric: Metric) -> list[FinancialFact]:
    semantic = {
        Metric.INVENTORY: "us-gaap:InventoryNet",
        Metric.TRADE_AR: "us-gaap:AccountsReceivableTradeCurrent",
        Metric.BROAD_AR: "us-gaap:AccountsReceivableNetCurrent",
        Metric.TRADE_AP: "us-gaap:AccountsPayableTradeCurrent",
        Metric.BROAD_AP: "us-gaap:AccountsPayableAndAccruedLiabilitiesCurrent",
    }[metric]
    return [
        _fact(
            metric,
            "120",
            period_end=CURRENT,
            fiscal_year=2026,
            semantic=semantic,
            available=AVAILABLE,
            balance_scope="current" if metric != Metric.INVENTORY else "total",
        ),
        _fact(
            metric,
            "100",
            period_end=PRIOR,
            fiscal_year=2025,
            semantic=semantic,
            available=date(2025, 8, 1),
            balance_scope="current" if metric != Metric.INVENTORY else "total",
        ),
    ]


def _snapshot(
    metric: Metric = Metric.INVENTORY,
    *,
    industry: str = "memory_semiconductor",
    financial_type: str = "non_financial",
) -> WorkingCapitalCoreSnapshot:
    return build_working_capital_core_snapshot(
        (*_balance_pair(metric), *_flow_facts()),
        issuer_id="sec:0000000001",
        industry=industry,
        financial_type=financial_type,
        as_of_date=CUTOFF,
    )


def _context(
    snapshot: WorkingCapitalCoreSnapshot,
    *,
    industry: str = "memory_semiconductor",
    text: str = "재고 전환과 현금흐름을 확인합니다.",
    unknowns: tuple[str, ...] = (),
    cutoff: date = CUTOFF,
    provisional: date | None = None,
    formal: date | None = None,
    cash_flow_period: date | None = None,
):
    return build_working_capital_reasoning_context(
        snapshot,
        ticker="TEST",
        market="US_FOREIGN",
        packet_id="packet:test",
        assessment_date=cutoff,
        cutoff=cutoff,
        industry=industry,
        monitoring_text=text,
        existing_unknowns=unknowns,
        latest_formal_balance_date=formal,
        latest_provisional_period_end=provisional,
        cash_flow_period_end=cash_flow_period,
    )


def _maps(snapshot: WorkingCapitalCoreSnapshot):
    facts = {item.fact_id: item for item in snapshot.canonical_facts}
    relations = {
        item.relation_id: item for item in snapshot.relations if item.relation_id
    }
    return facts, relations


def test_current_inventory_relation_is_selected_and_bound() -> None:
    snapshot = _snapshot()
    context = _context(snapshot, cash_flow_period=CURRENT)
    reasoning = render_working_capital_reasoning(context)
    facts, relations = _maps(snapshot)

    assert context.shadow_used is True
    assert context.freshness_state == FreshnessState.CURRENT_FORMAL
    assert context.usage_mode == UsageMode.INVENTORY_RELATION
    assert context.cash_flow_alignment_state == "COMPATIBLE_FORMAL_PERIOD"
    assert reasoning is not None
    assert reasoning.numeric_claims[0].display == "10.0%p"
    assert validate_working_capital_reasoning(
        context, facts, relations, reasoning
    ) == ()


def test_relation_with_one_future_input_is_excluded() -> None:
    snapshot = _snapshot()
    context = _context(snapshot, cutoff=date(2026, 7, 31))

    assert context.shadow_used is False
    assert context.selected_relation is None
    assert any(
        item["reason"].startswith("future_fact_after_cutoff")
        for item in context.point_in_time_exclusions
    )


def test_newer_formal_period_never_uses_older_relation_as_current() -> None:
    snapshot = _snapshot()
    context = _context(snapshot, formal=date(2026, 9, 30))

    assert context.shadow_used is False
    assert context.selected_relation is None
    assert any(
        item["reason"] == "relation_not_latest_formal_balance"
        for item in context.point_in_time_exclusions
    )


def test_formal_lagging_provisional_is_context_only_and_not_rendered() -> None:
    snapshot = _snapshot()
    context = _context(snapshot, provisional=date(2026, 9, 30))

    assert context.freshness_state == FreshnessState.FORMAL_LAGGING_PROVISIONAL
    assert context.usage_mode == UsageMode.CONTEXT_ONLY
    assert context.consumption_eligible is True
    assert context.shadow_used is False
    assert render_working_capital_reasoning(context) is None


def test_broad_ar_preserves_broad_semantic_label() -> None:
    snapshot = _snapshot(
        Metric.BROAD_AR,
        industry="cloud_platform_software",
    )
    context = _context(
        snapshot,
        industry="cloud_platform_software",
        text="매출채권과 Cloud 매출 전환을 확인합니다.",
    )
    reasoning = render_working_capital_reasoning(context)
    facts, relations = _maps(snapshot)

    assert context.usage_mode == UsageMode.BROAD_AR_RELATION
    assert reasoning is not None
    assert "광의 매출채권" in reasoning.text
    assert "거래성 범위가 확인되지 않은" in reasoning.text
    assert validate_working_capital_reasoning(
        context, facts, relations, reasoning
    ) == ()


def test_broad_ar_mislabeled_as_trade_is_rejected() -> None:
    snapshot = _snapshot(
        Metric.BROAD_AR,
        industry="cloud_platform_software",
    )
    context = _context(
        snapshot,
        industry="cloud_platform_software",
        text="매출채권을 확인합니다.",
    )
    reasoning = render_working_capital_reasoning(context)
    facts, relations = _maps(snapshot)
    assert reasoning is not None
    bad = replace(reasoning, text=reasoning.text + " 거래 매출채권이 확인됐습니다.")

    assert "broad_ar_mislabeled_trade_ar" in validate_working_capital_reasoning(
        context, facts, relations, bad
    )


def test_broad_ap_never_implies_supplier_payables() -> None:
    snapshot = _snapshot(Metric.BROAD_AP, industry="general_non_financial")
    context = _context(
        snapshot,
        industry="general_non_financial",
        text="매입채무 지급 구조를 확인합니다.",
    )
    reasoning = render_working_capital_reasoning(context)
    facts, relations = _maps(snapshot)
    assert reasoning is not None
    bad = replace(reasoning, text=reasoning.text + " 공급업체 매입채무입니다.")

    assert "broad_ap_mislabeled_trade_ap" in validate_working_capital_reasoning(
        context, facts, relations, bad
    )


def test_exact_trade_ap_is_allowed_without_dpo_or_supplier_causality() -> None:
    snapshot = _snapshot(Metric.TRADE_AP, industry="general_non_financial")
    context = _context(
        snapshot,
        industry="general_non_financial",
        text="거래 매입채무와 매출원가의 관계를 확인합니다.",
    )
    reasoning = render_working_capital_reasoning(context)
    facts, relations = _maps(snapshot)

    assert context.usage_mode == UsageMode.TRADE_AP_RELATION
    assert reasoning is not None
    assert "거래 매입채무" in reasoning.text
    assert "DPO" not in reasoning.text
    assert validate_working_capital_reasoning(
        context, facts, relations, reasoning
    ) == ()


def test_contract_assets_and_accrued_liabilities_are_rejected() -> None:
    ar_snapshot = _snapshot(Metric.TRADE_AR, industry="industrial_epc")
    ar_context = _context(
        ar_snapshot,
        industry="industrial_epc",
        text="매출채권과 수주 전환을 확인합니다.",
    )
    ar_reasoning = render_working_capital_reasoning(ar_context)
    ar_facts, ar_relations = _maps(ar_snapshot)
    assert ar_reasoning is not None
    ar_bad = replace(ar_reasoning, text=ar_reasoning.text + " 계약자산도 같습니다.")
    assert "contract_asset_leakage" in validate_working_capital_reasoning(
        ar_context, ar_facts, ar_relations, ar_bad
    )

    ap_snapshot = _snapshot(Metric.BROAD_AP, industry="general_non_financial")
    ap_context = _context(
        ap_snapshot,
        industry="general_non_financial",
        text="매입채무를 확인합니다.",
    )
    ap_reasoning = render_working_capital_reasoning(ap_context)
    ap_facts, ap_relations = _maps(ap_snapshot)
    assert ap_reasoning is not None
    ap_bad = replace(ap_reasoning, text=ap_reasoning.text + " 미지급비용입니다.")
    assert "accrued_liability_leakage" in validate_working_capital_reasoning(
        ap_context, ap_facts, ap_relations, ap_bad
    )


def test_causal_overclaim_and_advanced_ratios_are_rejected() -> None:
    snapshot = _snapshot(Metric.TRADE_AR, industry="industrial_epc")
    context = _context(
        snapshot,
        industry="industrial_epc",
        text="매출채권을 확인합니다.",
    )
    reasoning = render_working_capital_reasoning(context)
    facts, relations = _maps(snapshot)
    assert reasoning is not None
    causal = replace(reasoning, text=reasoning.text + " 고객이 대금을 안 냈습니다.")
    ratio = replace(reasoning, text=reasoning.text + " DSO는 45일입니다.")

    assert "unsupported_causal_overclaim" in validate_working_capital_reasoning(
        context, facts, relations, causal
    )
    assert "unsupported_advanced_working_capital_ratio" in (
        validate_working_capital_reasoning(context, facts, relations, ratio)
    )


def test_exact_unknown_is_resolved_without_false_remaining_claim() -> None:
    snapshot = _snapshot(Metric.TRADE_AR, industry="industrial_epc")
    context = _context(
        snapshot,
        industry="industrial_epc",
        text="매출채권을 확인합니다.",
        unknowns=("매출채권의 비교 가능한 흐름이 확인되지 않았습니다.",),
    )

    assert context.resolved_unknowns[0].state == UnknownResolutionState.RESOLVED_EXACT
    assert context.remaining_unknowns == ()


def test_broad_unknown_narrows_but_does_not_resolve_trade_scope() -> None:
    snapshot = _snapshot(
        Metric.BROAD_AR,
        industry="cloud_platform_software",
    )
    context = _context(
        snapshot,
        industry="cloud_platform_software",
        text="매출채권을 확인합니다.",
        unknowns=("매출채권의 흐름이 확인되지 않았습니다.",),
    )

    assert (
        context.resolved_unknowns[0].state
        == UnknownResolutionState.RESOLVED_BROAD_ONLY
    )
    assert "거래 매출채권" in context.remaining_unknowns[0]


def test_insurance_is_not_applicable_and_unknown_is_removed() -> None:
    snapshot = _snapshot(
        industry="insurance_reinsurance",
        financial_type="financial",
    )
    context = _context(
        snapshot,
        industry="insurance_reinsurance",
        unknowns=("재고와 매출채권이 확인되지 않았습니다.",),
    )

    assert context.freshness_state == FreshnessState.NOT_APPLICABLE
    assert context.usage_mode == UsageMode.NOT_APPLICABLE
    assert context.resolved_unknowns[0].state == UnknownResolutionState.NOT_APPLICABLE
    assert context.remaining_unknowns == ()


def test_biotech_context_is_suppressed_even_when_relation_exists() -> None:
    snapshot = _snapshot(
        Metric.BROAD_AP,
        industry="biotech",
        financial_type="pre_profit_biotech",
    )
    context = _context(
        snapshot,
        industry="biotech",
        text="임상 cash burn과 runway를 확인합니다.",
    )

    assert context.shadow_used is False
    assert context.selected_relation is None
    assert render_working_capital_reasoning(context) is None


def test_low_materiality_fact_resolves_availability_unknown_without_prose() -> None:
    snapshot = _snapshot(
        Metric.TRADE_AR,
        industry="biotech",
        financial_type="pre_profit_biotech",
    )
    context = _context(
        snapshot,
        industry="biotech",
        text="임상 cash burn과 runway를 확인합니다.",
        unknowns=("거래 매출채권을 확인할 수 없습니다.",),
    )

    assert context.shadow_used is False
    assert context.selected_relation is None
    assert context.resolved_unknowns[0].state == UnknownResolutionState.RESOLVED_EXACT
    assert context.remaining_unknowns == ()
    assert render_working_capital_reasoning(context) is None


def test_incompatible_cash_flow_period_is_suppressed_without_causal_link() -> None:
    snapshot = _snapshot()
    context = _context(snapshot, cash_flow_period=date(2026, 3, 31))
    reasoning = render_working_capital_reasoning(context)

    assert context.shadow_used is True
    assert context.cash_flow_alignment_state == "PERIOD_MISMATCH_SUPPRESSED"
    assert context.cash_flow_context_used is False
    assert reasoning is not None
    assert "현금흐름 문맥" not in reasoning.text


def test_relation_gap_tamper_and_state_mutations_are_rejected() -> None:
    snapshot = _snapshot()
    context = _context(snapshot)
    reasoning = render_working_capital_reasoning(context)
    facts, relations = _maps(snapshot)
    assert reasoning is not None
    bad_claim = replace(reasoning.numeric_claims[0], value="999")
    bad = replace(reasoning, numeric_claims=(bad_claim,))

    errors = validate_working_capital_reasoning(
        context,
        facts,
        relations,
        bad,
        thesis_status_changed=True,
        valuation_changed=True,
        warning_changed=True,
    )
    assert "numeric_value_mismatch" in errors
    assert "working_capital_based_thesis_status_change" in errors
    assert "working_capital_based_valuation_change" in errors
    assert "working_capital_based_warning_change" in errors
