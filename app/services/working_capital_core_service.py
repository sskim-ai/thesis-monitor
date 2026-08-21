from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from enum import StrEnum
from typing import Iterable, Mapping

from app.services.cash_flow_capital_efficiency_service import (
    EligibilityStatus,
    FactType,
    FinancialFact,
    Metric,
    PeriodType,
)
from app.services.working_capital_evidence_service import (
    CONTRACT_VERSION,
    ComparableSelection,
    FreshnessState,
    classify_freshness,
    fact_available_at,
    industry_applicability,
    select_aligned_flow_pair,
    select_latest_comparable_balance,
)


DERIVATION_VERSION = f"{CONTRACT_VERSION}:canonical-core-v1"
BALANCE_METRICS = (
    Metric.INVENTORY,
    Metric.TRADE_AR,
    Metric.BROAD_AR,
    Metric.TRADE_AP,
    Metric.BROAD_AP,
)


class RelationDirection(StrEnum):
    GREATER = "GREATER"
    LOWER = "LOWER"
    EQUAL = "EQUAL"


@dataclass(frozen=True)
class CanonicalMovement:
    status: EligibilityStatus
    balance_metric: Metric
    current: FinancialFact | None
    prior: FinancialFact | None
    delta_fact: FinancialFact | None
    yoy_fact: FinancialFact | None
    freshness_state: FreshnessState | None
    denial_reasons: tuple[str, ...] = ()
    cautions: tuple[str, ...] = ()


@dataclass(frozen=True)
class WorkingCapitalRelation:
    status: EligibilityStatus
    relation_id: str | None
    relation_type: str
    direction: RelationDirection | None
    balance_metric: Metric
    balance_semantic: str | None
    balance_scope: str | None
    flow_metric: Metric
    flow_semantic: str | None
    gap_percentage_points: Decimal | None
    current_balance_fact_id: str | None
    prior_balance_fact_id: str | None
    current_flow_fact_id: str | None
    prior_flow_fact_id: str | None
    balance_yoy_fact_id: str | None
    flow_yoy_fact_id: str | None
    input_fact_ids: tuple[str, ...]
    formula: str
    derivation_version: str
    denial_reasons: tuple[str, ...] = ()
    cautions: tuple[str, ...] = ()


@dataclass(frozen=True)
class WorkingCapitalCoreSnapshot:
    issuer_id: str
    as_of_date: date
    latest_safe_working_capital_date: date | None
    metric_states: tuple[CanonicalMovement, ...]
    relations: tuple[WorkingCapitalRelation, ...]
    canonical_facts: tuple[FinancialFact, ...]
    industry_applicability: Mapping[str, str]
    industry_status: EligibilityStatus
    denial_reasons: tuple[str, ...] = ()
    cautions: tuple[str, ...] = ()


def _combined_sha(facts: tuple[FinancialFact, ...]) -> str:
    payload = "|".join(item.raw_payload_sha256 for item in facts)
    return hashlib.sha256(payload.encode()).hexdigest()


def _derived_identity(
    metric: Metric,
    source_metric: Metric,
    formula: str,
    facts: tuple[FinancialFact, ...],
) -> str:
    payload = "|".join(
        (
            DERIVATION_VERSION,
            metric.value,
            source_metric.value,
            facts[0].semantic_mapping,
            facts[0].balance_scope or "",
            facts[0].net_gross_scope or "",
            formula,
            *(item.fact_id for item in facts),
        )
    )
    return hashlib.sha256(payload.encode()).hexdigest()[:24]


def _basis_reasons(facts: tuple[FinancialFact, ...]) -> tuple[str, ...]:
    if not facts:
        return ("derived_inputs_missing",)
    first = facts[0]
    reasons: list[str] = []
    for fact in facts:
        if fact.eligibility != EligibilityStatus.ELIGIBLE:
            reasons.append("input_not_eligible")
        if fact.quality not in {"REPORTED_VERIFIED", "DERIVED_SAFE"}:
            reasons.append("input_quality_not_safe")
        if fact.source_available_at is None:
            reasons.append("input_source_availability_missing")
        if fact.issuer_id != first.issuer_id:
            reasons.append("issuer_mismatch")
        if fact.currency != first.currency:
            reasons.append("currency_mismatch")
        if fact.unit != first.unit:
            reasons.append("unit_mismatch")
        if fact.entity_scope != first.entity_scope:
            reasons.append("entity_scope_mismatch")
        if fact.statement_basis != first.statement_basis:
            reasons.append("statement_basis_mismatch")
        if fact.restatement_policy_id != first.restatement_policy_id:
            reasons.append("restatement_policy_mismatch")
    return tuple(dict.fromkeys(reasons))


def _make_derived_fact(
    *,
    metric: Metric,
    source_metric: Metric,
    current: FinancialFact,
    prior: FinancialFact,
    value: Decimal,
    formula: str,
    unit: str,
    currency: str,
    as_of_date: date,
) -> FinancialFact:
    inputs = (current, prior)
    identity = _derived_identity(metric, source_metric, formula, inputs)
    source_available_at = max(
        item.source_available_at for item in inputs if item.source_available_at
    )
    semantic_mapping = ":".join(
        (
            CONTRACT_VERSION,
            source_metric.value,
            current.semantic_mapping,
            metric.value,
        )
    )
    cautions = tuple(
        dict.fromkeys(
            (
                *current.cautions,
                f"source_metric:{source_metric.value}",
                f"source_semantic:{current.semantic_mapping}",
                f"source_currency:{current.currency}",
                f"source_unit:{current.unit}",
            )
        )
    )
    return FinancialFact(
        fact_id=f"working-capital-derived:{identity}",
        issuer_id=current.issuer_id,
        metric=metric,
        value=value,
        currency=currency,
        unit=unit,
        period=current.period,
        entity_scope=current.entity_scope,
        statement_basis=current.statement_basis,
        reported_or_derived="derived",
        source_provider="canonical_derivation",
        source_document_id=f"derived:{identity}",
        filing_date=max(current.filing_date, prior.filing_date),
        source_occurrence_id=f"derived-occurrence:{identity}",
        raw_payload_sha256=_combined_sha(inputs),
        semantic_mapping=semantic_mapping,
        fact_type=FactType.DERIVED_METRIC,
        source_document_type="derived_metric",
        source_semantic=None,
        source_reported_value=None,
        source_reported_unit=None,
        source_sign="derived_signed_amount" if unit != "percent" else "derived_ratio",
        normalization_transform=None,
        derivation_formula=formula,
        derivation_version=DERIVATION_VERSION,
        input_fact_ids=(current.fact_id, prior.fact_id),
        quality="DERIVED_SAFE",
        eligibility=EligibilityStatus.ELIGIBLE,
        cautions=cautions,
        restatement_policy_id=current.restatement_policy_id,
        as_of_date=as_of_date,
        source_available_at=source_available_at,
        balance_scope=current.balance_scope,
        net_gross_scope=current.net_gross_scope,
    )


def _pair_reasons(selection: ComparableSelection) -> tuple[str, ...]:
    current = selection.current
    prior = selection.prior
    if current is None or prior is None:
        return selection.reasons or ("prior_year_comparable_balance_missing",)
    reasons = list(_basis_reasons((current, prior)))
    if current.metric != prior.metric:
        reasons.append("metric_mismatch")
    if current.semantic_mapping != prior.semantic_mapping:
        reasons.append("semantic_scope_mismatch")
    if current.balance_scope != prior.balance_scope:
        reasons.append("balance_scope_mismatch")
    if current.net_gross_scope != prior.net_gross_scope:
        reasons.append("net_gross_scope_mismatch")
    if any(
        item.period.period_type != PeriodType.POINT_IN_TIME
        for item in (current, prior)
    ):
        reasons.append("point_in_time_inputs_required")
    if current.period.fiscal_quarter != prior.period.fiscal_quarter:
        reasons.append("fiscal_quarter_mismatch")
    if current.period.fiscal_year != prior.period.fiscal_year + 1:
        reasons.append("fiscal_year_not_prior_comparable")
    return tuple(dict.fromkeys(reasons))


def derive_canonical_movement(
    selection: ComparableSelection,
    *,
    balance_metric: Metric,
    as_of_date: date,
    latest_formal_balance_date: date | None,
    latest_provisional_period_end: date | None = None,
) -> CanonicalMovement:
    current = selection.current
    prior = selection.prior
    freshness = (
        classify_freshness(
            current,
            latest_formal_balance_date=latest_formal_balance_date,
            latest_provisional_period_end=latest_provisional_period_end,
        )
        if current is not None and latest_formal_balance_date is not None
        else None
    )
    reasons = _pair_reasons(selection)
    if current is None or prior is None or reasons:
        return CanonicalMovement(
            selection.status if current is not None else EligibilityStatus.BLOCKED,
            balance_metric,
            current,
            prior,
            None,
            None,
            freshness,
            reasons,
        )
    delta = current.value - prior.value
    delta_fact = _make_derived_fact(
        metric=Metric.BALANCE_DELTA,
        source_metric=balance_metric,
        current=current,
        prior=prior,
        value=delta,
        formula="CURRENT_BALANCE_MINUS_PRIOR_YEAR_COMPARABLE_BALANCE",
        unit=current.unit,
        currency=current.currency,
        as_of_date=as_of_date,
    )
    if prior.value <= 0:
        return CanonicalMovement(
            EligibilityStatus.PARTIAL,
            balance_metric,
            current,
            prior,
            delta_fact,
            None,
            freshness,
            ("non_positive_prior_denominator",),
        )
    yoy_fact = _make_derived_fact(
        metric=Metric.BALANCE_YOY_GROWTH,
        source_metric=balance_metric,
        current=current,
        prior=prior,
        value=(delta / prior.value) * Decimal(100),
        formula="CURRENT_MINUS_PRIOR_DIVIDED_BY_PRIOR_TIMES_100",
        unit="percent",
        currency="dimensionless",
        as_of_date=as_of_date,
    )
    return CanonicalMovement(
        EligibilityStatus.ELIGIBLE,
        balance_metric,
        current,
        prior,
        delta_fact,
        yoy_fact,
        freshness,
    )


def _derive_flow_yoy(
    selection: ComparableSelection,
    *,
    flow_metric: Metric,
    as_of_date: date,
) -> tuple[FinancialFact | None, tuple[str, ...]]:
    current = selection.current
    prior = selection.prior
    if current is None or prior is None:
        return None, selection.reasons or ("comparable_flow_pair_missing",)
    reasons = list(_basis_reasons((current, prior)))
    if current.metric != flow_metric or prior.metric != flow_metric:
        reasons.append("flow_metric_mismatch")
    if current.semantic_mapping != prior.semantic_mapping:
        reasons.append("flow_semantic_scope_mismatch")
    if current.period.period_type != prior.period.period_type:
        reasons.append("flow_period_type_mismatch")
    if current.period.period_type == PeriodType.POINT_IN_TIME:
        reasons.append("duration_flow_required")
    if current.period.fiscal_quarter != prior.period.fiscal_quarter:
        reasons.append("flow_fiscal_quarter_mismatch")
    if current.period.fiscal_year != prior.period.fiscal_year + 1:
        reasons.append("flow_fiscal_year_not_prior_comparable")
    if abs(current.period.duration_days - prior.period.duration_days) > 2:
        reasons.append("flow_duration_mismatch")
    if prior.value <= 0:
        reasons.append("non_positive_flow_denominator")
    if reasons:
        return None, tuple(dict.fromkeys(reasons))
    return (
        _make_derived_fact(
            metric=Metric.FLOW_YOY_GROWTH,
            source_metric=flow_metric,
            current=current,
            prior=prior,
            value=((current.value - prior.value) / prior.value) * Decimal(100),
            formula="CURRENT_FLOW_MINUS_PRIOR_DIVIDED_BY_PRIOR_TIMES_100",
            unit="percent",
            currency="dimensionless",
            as_of_date=as_of_date,
        ),
        (),
    )


def derive_working_capital_relation(
    movement: CanonicalMovement,
    flows: ComparableSelection,
    *,
    flow_metric: Metric,
    as_of_date: date,
) -> tuple[WorkingCapitalRelation, FinancialFact | None]:
    relation_type = "YOY_GROWTH_COMPARISON"
    formula = "BALANCE_YOY_PERCENT_MINUS_FLOW_YOY_PERCENT"
    current_balance = movement.current
    prior_balance = movement.prior
    current_flow = flows.current
    prior_flow = flows.prior
    flow_yoy, flow_reasons = _derive_flow_yoy(
        flows,
        flow_metric=flow_metric,
        as_of_date=as_of_date,
    )
    balance_yoy = movement.yoy_fact
    reasons = list(movement.denial_reasons)
    reasons.extend(flow_reasons)
    if balance_yoy is None:
        reasons.append("balance_yoy_fact_required")
    if current_balance is not None and current_flow is not None:
        if current_balance.currency != current_flow.currency:
            reasons.append("balance_flow_currency_mismatch")
        if current_balance.unit != current_flow.unit:
            reasons.append("balance_flow_unit_mismatch")
        if current_balance.entity_scope != current_flow.entity_scope:
            reasons.append("balance_flow_entity_scope_mismatch")
        if current_balance.statement_basis != current_flow.statement_basis:
            reasons.append("balance_flow_statement_basis_mismatch")
        if (
            current_balance.restatement_policy_id
            != current_flow.restatement_policy_id
        ):
            reasons.append("balance_flow_restatement_policy_mismatch")
    reasons = list(dict.fromkeys(reasons))
    raw_ids = tuple(
        item.fact_id
        for item in (current_balance, prior_balance, current_flow, prior_flow)
        if item is not None
    )
    if reasons or balance_yoy is None or flow_yoy is None:
        return (
            WorkingCapitalRelation(
                EligibilityStatus.BLOCKED,
                None,
                relation_type,
                None,
                movement.balance_metric,
                current_balance.semantic_mapping if current_balance else None,
                current_balance.balance_scope if current_balance else None,
                flow_metric,
                current_flow.semantic_mapping if current_flow else None,
                None,
                current_balance.fact_id if current_balance else None,
                prior_balance.fact_id if prior_balance else None,
                current_flow.fact_id if current_flow else None,
                prior_flow.fact_id if prior_flow else None,
                balance_yoy.fact_id if balance_yoy else None,
                flow_yoy.fact_id if flow_yoy else None,
                raw_ids,
                formula,
                DERIVATION_VERSION,
                tuple(reasons),
            ),
            flow_yoy,
        )
    gap = balance_yoy.value - flow_yoy.value
    direction = (
        RelationDirection.GREATER
        if gap > 0
        else RelationDirection.LOWER
        if gap < 0
        else RelationDirection.EQUAL
    )
    input_ids = (
        current_balance.fact_id,
        prior_balance.fact_id,
        current_flow.fact_id,
        prior_flow.fact_id,
        balance_yoy.fact_id,
        flow_yoy.fact_id,
    )
    payload = "|".join(
        (
            DERIVATION_VERSION,
            relation_type,
            movement.balance_metric.value,
            current_balance.semantic_mapping,
            current_balance.balance_scope or "",
            flow_metric.value,
            current_flow.semantic_mapping,
            direction.value,
            *input_ids,
        )
    )
    relation_id = (
        f"working-capital-relation:{hashlib.sha256(payload.encode()).hexdigest()[:24]}"
    )
    return (
        WorkingCapitalRelation(
            EligibilityStatus.ELIGIBLE,
            relation_id,
            relation_type,
            direction,
            movement.balance_metric,
            current_balance.semantic_mapping,
            current_balance.balance_scope,
            flow_metric,
            current_flow.semantic_mapping,
            gap,
            current_balance.fact_id,
            prior_balance.fact_id,
            current_flow.fact_id,
            prior_flow.fact_id,
            balance_yoy.fact_id,
            flow_yoy.fact_id,
            input_ids,
            formula,
            DERIVATION_VERSION,
            cautions=("factual_growth_relation_only",),
        ),
        flow_yoy,
    )


def _not_applicable_movement(metric: Metric) -> CanonicalMovement:
    return CanonicalMovement(
        EligibilityStatus.NOT_APPLICABLE,
        metric,
        None,
        None,
        None,
        None,
        None,
        ("generic_working_capital_not_applicable",),
    )


def _not_applicable_relation(
    balance_metric: Metric,
    flow_metric: Metric,
) -> WorkingCapitalRelation:
    return WorkingCapitalRelation(
        EligibilityStatus.NOT_APPLICABLE,
        None,
        "YOY_GROWTH_COMPARISON",
        None,
        balance_metric,
        None,
        None,
        flow_metric,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        (),
        "BALANCE_YOY_PERCENT_MINUS_FLOW_YOY_PERCENT",
        DERIVATION_VERSION,
        ("generic_working_capital_not_applicable",),
    )


def build_working_capital_core_snapshot(
    facts: Iterable[FinancialFact],
    *,
    issuer_id: str,
    industry: str,
    as_of_date: date,
    financial_type: str | None = None,
    latest_formal_balance_date: date | None = None,
    latest_provisional_period_end: date | None = None,
) -> WorkingCapitalCoreSnapshot:
    all_facts = tuple(facts)
    visible = tuple(
        fact
        for fact in all_facts
        if fact.issuer_id == issuer_id and fact_available_at(fact, as_of_date)
    )
    missing_availability = sum(
        1
        for fact in all_facts
        if fact.issuer_id == issuer_id and fact.source_available_at is None
    )
    applicability = dict(industry_applicability(industry))
    not_applicable = (
        industry == "insurance_reinsurance" or financial_type == "financial"
    )
    if not_applicable:
        relations = (
            _not_applicable_relation(Metric.TRADE_AR, Metric.REVENUE),
            _not_applicable_relation(Metric.BROAD_AR, Metric.REVENUE),
            _not_applicable_relation(Metric.INVENTORY, Metric.REVENUE),
            _not_applicable_relation(Metric.INVENTORY, Metric.COGS),
            _not_applicable_relation(Metric.TRADE_AP, Metric.COGS),
            _not_applicable_relation(Metric.BROAD_AP, Metric.COGS),
        )
        return WorkingCapitalCoreSnapshot(
            issuer_id,
            as_of_date,
            None,
            tuple(_not_applicable_movement(metric) for metric in BALANCE_METRICS),
            relations,
            (),
            applicability,
            EligibilityStatus.NOT_APPLICABLE,
            ("generic_working_capital_not_applicable",),
        )
    formal_date = latest_formal_balance_date
    if formal_date is None:
        balance_dates = [
            fact.period.end
            for fact in visible
            if fact.metric in BALANCE_METRICS
            and fact.period.period_type == PeriodType.POINT_IN_TIME
        ]
        formal_date = max(balance_dates) if balance_dates else None
    movements: list[CanonicalMovement] = []
    for metric in BALANCE_METRICS:
        selection = select_latest_comparable_balance(visible, metrics=(metric,))
        movements.append(
            derive_canonical_movement(
                selection,
                balance_metric=metric,
                as_of_date=as_of_date,
                latest_formal_balance_date=formal_date,
                latest_provisional_period_end=latest_provisional_period_end,
            )
        )
    relations: list[WorkingCapitalRelation] = []
    flow_yoy_facts: list[FinancialFact] = []
    relation_specs = (
        (Metric.TRADE_AR, Metric.REVENUE),
        (Metric.BROAD_AR, Metric.REVENUE),
        (Metric.INVENTORY, Metric.REVENUE),
        (Metric.INVENTORY, Metric.COGS),
        (Metric.TRADE_AP, Metric.COGS),
        (Metric.BROAD_AP, Metric.COGS),
    )
    movement_by_metric = {item.balance_metric: item for item in movements}
    for balance_metric, flow_metric in relation_specs:
        movement = movement_by_metric[balance_metric]
        selection = ComparableSelection(
            movement.status,
            movement.current,
            movement.prior,
            movement.denial_reasons,
        )
        flows = select_aligned_flow_pair(
            visible,
            metric=flow_metric,
            balances=selection,
        )
        relation, flow_yoy = derive_working_capital_relation(
            movement,
            flows,
            flow_metric=flow_metric,
            as_of_date=as_of_date,
        )
        relations.append(relation)
        if flow_yoy is not None:
            flow_yoy_facts.append(flow_yoy)
    derived = [
        fact
        for movement in movements
        for fact in (movement.delta_fact, movement.yoy_fact)
        if fact is not None
    ]
    selected_raw_ids = {
        fact.fact_id
        for movement in movements
        for fact in (movement.current, movement.prior)
        if fact is not None
    }
    selected_raw_ids.update(
        fact_id
        for relation in relations
        for fact_id in relation.input_fact_ids[:4]
    )
    selected_raw = [fact for fact in visible if fact.fact_id in selected_raw_ids]
    unique_facts = {
        fact.fact_id: fact
        for fact in (*selected_raw, *derived, *flow_yoy_facts)
    }
    denial_reasons = (
        ("source_availability_missing",) if missing_availability else ()
    )
    return WorkingCapitalCoreSnapshot(
        issuer_id,
        as_of_date,
        formal_date,
        tuple(movements),
        tuple(relations),
        tuple(sorted(unique_facts.values(), key=lambda item: item.fact_id)),
        applicability,
        EligibilityStatus.ELIGIBLE,
        denial_reasons,
        ("audit_only_shadow_core", "no_user_visible_consumption"),
    )
