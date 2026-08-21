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
    DERIVATION_VERSION,
    RelationDirection,
    build_working_capital_core_snapshot,
)
from app.services.working_capital_evidence_service import FreshnessState


def _fact(
    metric: Metric,
    value: str,
    *,
    start: date,
    end: date,
    fiscal_year: int,
    fiscal_quarter: int,
    semantic: str,
    available: date,
    balance_scope: str | None = None,
) -> FinancialFact:
    period_type = (
        PeriodType.POINT_IN_TIME
        if start == end
        else PeriodType.YTD
        if fiscal_quarter in {2, 3}
        else PeriodType.FY
        if fiscal_quarter == 4
        else PeriodType.QTD
    )
    token = hashlib.sha256(
        f"{metric.value}|{start}|{end}|{semantic}|{available}".encode()
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
            end=end,
            period_type=period_type,
            fiscal_year=fiscal_year,
            fiscal_quarter=fiscal_quarter,
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


def _comparable_facts() -> tuple[FinancialFact, ...]:
    current_date = date(2026, 6, 30)
    prior_date = date(2025, 6, 30)
    return (
        _fact(
            Metric.INVENTORY,
            "120",
            start=current_date,
            end=current_date,
            fiscal_year=2026,
            fiscal_quarter=2,
            semantic="us-gaap:InventoryNet",
            available=date(2026, 8, 1),
            balance_scope="total",
        ),
        _fact(
            Metric.INVENTORY,
            "100",
            start=prior_date,
            end=prior_date,
            fiscal_year=2025,
            fiscal_quarter=2,
            semantic="us-gaap:InventoryNet",
            available=date(2025, 8, 1),
            balance_scope="total",
        ),
        _fact(
            Metric.REVENUE,
            "220",
            start=date(2026, 1, 1),
            end=current_date,
            fiscal_year=2026,
            fiscal_quarter=2,
            semantic="us-gaap:Revenues",
            available=date(2026, 8, 1),
        ),
        _fact(
            Metric.REVENUE,
            "200",
            start=date(2025, 1, 1),
            end=prior_date,
            fiscal_year=2025,
            fiscal_quarter=2,
            semantic="us-gaap:Revenues",
            available=date(2025, 8, 1),
        ),
        _fact(
            Metric.COGS,
            "165",
            start=date(2026, 1, 1),
            end=current_date,
            fiscal_year=2026,
            fiscal_quarter=2,
            semantic="us-gaap:CostOfRevenue",
            available=date(2026, 8, 1),
        ),
        _fact(
            Metric.COGS,
            "150",
            start=date(2025, 1, 1),
            end=prior_date,
            fiscal_year=2025,
            fiscal_quarter=2,
            semantic="us-gaap:CostOfRevenue",
            available=date(2025, 8, 1),
        ),
    )


def test_canonical_delta_and_yoy_are_first_class_facts() -> None:
    snapshot = build_working_capital_core_snapshot(
        _comparable_facts(),
        issuer_id="sec:0000000001",
        industry="memory_semiconductor",
        as_of_date=date(2026, 8, 21),
    )
    movement = next(
        item for item in snapshot.metric_states if item.balance_metric == Metric.INVENTORY
    )

    assert movement.status == EligibilityStatus.ELIGIBLE
    assert movement.delta_fact is not None
    assert movement.delta_fact.metric == Metric.BALANCE_DELTA
    assert movement.delta_fact.value == Decimal(20)
    assert movement.delta_fact.fact_type == FactType.DERIVED_METRIC
    assert movement.delta_fact.input_fact_ids == (
        movement.current.fact_id,
        movement.prior.fact_id,
    )
    assert movement.yoy_fact is not None
    assert movement.yoy_fact.metric == Metric.BALANCE_YOY_GROWTH
    assert movement.yoy_fact.value == Decimal(20)
    assert movement.yoy_fact.currency == "dimensionless"
    assert movement.yoy_fact.unit == "percent"
    assert movement.yoy_fact.derivation_version == DERIVATION_VERSION
    assert movement.freshness_state == FreshnessState.CURRENT_FORMAL


def test_cross_growth_relation_has_raw_and_derived_lineage() -> None:
    snapshot = build_working_capital_core_snapshot(
        _comparable_facts(),
        issuer_id="sec:0000000001",
        industry="memory_semiconductor",
        as_of_date=date(2026, 8, 21),
    )
    relation = next(
        item
        for item in snapshot.relations
        if item.balance_metric == Metric.INVENTORY
        and item.flow_metric == Metric.REVENUE
    )
    facts = {item.fact_id: item for item in snapshot.canonical_facts}

    assert relation.status == EligibilityStatus.ELIGIBLE
    assert relation.direction == RelationDirection.GREATER
    assert relation.gap_percentage_points == Decimal(10)
    assert len(relation.input_fact_ids) == 6
    assert set(relation.input_fact_ids) <= facts.keys()
    assert facts[relation.balance_yoy_fact_id].metric == Metric.BALANCE_YOY_GROWTH
    assert facts[relation.flow_yoy_fact_id].metric == Metric.FLOW_YOY_GROWTH
    assert relation.current_balance_fact_id in relation.input_fact_ids
    assert relation.current_flow_fact_id in relation.input_fact_ids


def test_trade_and_broad_relation_identity_never_collapses() -> None:
    facts = list(_comparable_facts())
    for metric, semantic, scope, current, prior in (
        (Metric.TRADE_AR, "us-gaap:AccountsReceivableTradeCurrent", "current", "90", "75"),
        (Metric.BROAD_AR, "us-gaap:AccountsReceivableNetCurrent", "current", "110", "100"),
    ):
        facts.extend(
            (
                _fact(
                    metric,
                    current,
                    start=date(2026, 6, 30),
                    end=date(2026, 6, 30),
                    fiscal_year=2026,
                    fiscal_quarter=2,
                    semantic=semantic,
                    available=date(2026, 8, 1),
                    balance_scope=scope,
                ),
                _fact(
                    metric,
                    prior,
                    start=date(2025, 6, 30),
                    end=date(2025, 6, 30),
                    fiscal_year=2025,
                    fiscal_quarter=2,
                    semantic=semantic,
                    available=date(2025, 8, 1),
                    balance_scope=scope,
                ),
            )
        )
    snapshot = build_working_capital_core_snapshot(
        facts,
        issuer_id="sec:0000000001",
        industry="cloud_platform",
        as_of_date=date(2026, 8, 21),
    )
    relations = {
        item.balance_metric: item
        for item in snapshot.relations
        if item.flow_metric == Metric.REVENUE
        and item.balance_metric in {Metric.TRADE_AR, Metric.BROAD_AR}
    }

    assert relations[Metric.TRADE_AR].status == EligibilityStatus.ELIGIBLE
    assert relations[Metric.BROAD_AR].status == EligibilityStatus.ELIGIBLE
    assert relations[Metric.TRADE_AR].relation_id != relations[Metric.BROAD_AR].relation_id
    assert relations[Metric.TRADE_AR].balance_semantic != relations[Metric.BROAD_AR].balance_semantic


def test_zero_prior_preserves_delta_and_blocks_yoy_relation() -> None:
    facts = tuple(
        replace(item, value=Decimal(0))
        if item.metric == Metric.INVENTORY and item.period.fiscal_year == 2025
        else item
        for item in _comparable_facts()
    )
    snapshot = build_working_capital_core_snapshot(
        facts,
        issuer_id="sec:0000000001",
        industry="memory_semiconductor",
        as_of_date=date(2026, 8, 21),
    )
    movement = next(
        item for item in snapshot.metric_states if item.balance_metric == Metric.INVENTORY
    )
    relation = next(
        item
        for item in snapshot.relations
        if item.balance_metric == Metric.INVENTORY
        and item.flow_metric == Metric.REVENUE
    )

    assert movement.status == EligibilityStatus.PARTIAL
    assert movement.delta_fact is not None
    assert movement.yoy_fact is None
    assert movement.denial_reasons == ("non_positive_prior_denominator",)
    assert relation.status == EligibilityStatus.BLOCKED


def test_future_fact_is_excluded_and_historical_fact_is_not_relabelled_current() -> None:
    facts = tuple(
        replace(item, source_available_at=date(2026, 9, 1))
        if item.period.fiscal_year == 2026
        else item
        for item in _comparable_facts()
    )
    snapshot = build_working_capital_core_snapshot(
        facts,
        issuer_id="sec:0000000001",
        industry="memory_semiconductor",
        as_of_date=date(2026, 8, 21),
        latest_formal_balance_date=date(2026, 6, 30),
    )
    movement = next(
        item for item in snapshot.metric_states if item.balance_metric == Metric.INVENTORY
    )

    assert movement.status == EligibilityStatus.PARTIAL
    assert movement.current is not None
    assert movement.current.period.end == date(2025, 6, 30)
    assert movement.prior is None
    assert movement.freshness_state == FreshnessState.HISTORICAL_NOT_CURRENT
    assert all(
        item.source_available_at <= date(2026, 8, 21)
        for item in snapshot.canonical_facts
    )


def test_insurance_is_not_applicable_even_when_raw_facts_exist() -> None:
    snapshot = build_working_capital_core_snapshot(
        _comparable_facts(),
        issuer_id="sec:0000000001",
        industry="insurance_reinsurance",
        financial_type="financial",
        as_of_date=date(2026, 8, 21),
    )

    assert snapshot.industry_status == EligibilityStatus.NOT_APPLICABLE
    assert not snapshot.canonical_facts
    assert all(
        item.status == EligibilityStatus.NOT_APPLICABLE
        for item in snapshot.metric_states
    )
    assert all(
        item.status == EligibilityStatus.NOT_APPLICABLE
        for item in snapshot.relations
    )


def test_repeated_build_is_idempotent() -> None:
    first = build_working_capital_core_snapshot(
        _comparable_facts(),
        issuer_id="sec:0000000001",
        industry="memory_semiconductor",
        as_of_date=date(2026, 8, 21),
    )
    second = build_working_capital_core_snapshot(
        _comparable_facts(),
        issuer_id="sec:0000000001",
        industry="memory_semiconductor",
        as_of_date=date(2026, 8, 21),
    )

    assert [item.fact_id for item in first.canonical_facts] == [
        item.fact_id for item in second.canonical_facts
    ]
    assert [item.relation_id for item in first.relations] == [
        item.relation_id for item in second.relations
    ]
