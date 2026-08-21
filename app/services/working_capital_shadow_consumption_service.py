from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from enum import StrEnum
from typing import Mapping, Sequence

from app.services.cash_flow_capital_efficiency_service import (
    EligibilityStatus,
    FinancialFact,
    Metric,
)
from app.services.working_capital_core_service import (
    RelationDirection,
    WorkingCapitalCoreSnapshot,
    WorkingCapitalRelation,
)


CONTRACT_VERSION = "working-capital-shadow-consumption-v1"


class FreshnessState(StrEnum):
    CURRENT_FORMAL = "CURRENT_FORMAL"
    FORMAL_LAGGING_PROVISIONAL = "FORMAL_LAGGING_PROVISIONAL"
    STALE_CONTEXT_ONLY = "STALE_CONTEXT_ONLY"
    BLOCKED = "BLOCKED"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class UsageMode(StrEnum):
    INVENTORY_RELATION = "INVENTORY_RELATION"
    TRADE_AR_RELATION = "TRADE_AR_RELATION"
    BROAD_AR_RELATION = "BROAD_AR_RELATION"
    TRADE_AP_RELATION = "TRADE_AP_RELATION"
    BROAD_AP_RELATION = "BROAD_AP_RELATION"
    CONTEXT_ONLY = "CONTEXT_ONLY"
    SUPPRESSED = "SUPPRESSED"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class UnknownResolutionState(StrEnum):
    RESOLVED_EXACT = "RESOLVED_EXACT"
    RESOLVED_BROAD_ONLY = "RESOLVED_BROAD_ONLY"
    STILL_VALID = "STILL_VALID"
    STALE_CONTEXT_ONLY = "STALE_CONTEXT_ONLY"
    NOT_APPLICABLE = "NOT_APPLICABLE"


@dataclass(frozen=True)
class MetricContext:
    metric: Metric
    status: str
    current_fact_id: str | None
    yoy_fact_id: str | None
    semantic_label: str


@dataclass(frozen=True)
class SelectedRelation:
    relation_id: str
    family: str
    direction: RelationDirection
    balance_metric: Metric
    balance_semantic: str
    balance_scope: str | None
    flow_metric: Metric
    flow_semantic: str
    gap_percentage_points: Decimal
    input_fact_ids: tuple[str, ...]
    current_balance_fact_id: str
    balance_yoy_fact_id: str
    flow_yoy_fact_id: str
    applicability: str


@dataclass(frozen=True)
class UnknownResolution:
    original: str
    state: UnknownResolutionState
    replacement: str | None


@dataclass(frozen=True)
class WorkingCapitalNumericClaim:
    relation_id: str
    semantic_type: str
    value: str
    display: str
    input_fact_ids: tuple[str, ...]
    text_ref: str = "business_earnings.text"
    owner: str = "business_earnings"


@dataclass(frozen=True)
class WorkingCapitalShadowReasoning:
    text: str
    relation_ids: tuple[str, ...]
    fact_ids: tuple[str, ...]
    numeric_claims: tuple[WorkingCapitalNumericClaim, ...]


@dataclass(frozen=True)
class WorkingCapitalReasoningContext:
    ticker: str
    market: str
    packet_id: str
    assessment_date: date
    cutoff: date
    status: str
    usage_mode: UsageMode
    latest_formal_balance_date: date | None
    freshness_state: FreshnessState
    pit_state: str
    industry: str
    specificity_key: str
    industry_applicability: Mapping[str, str]
    materiality_reason: str | None
    metric_contexts: tuple[MetricContext, ...]
    selected_relation: SelectedRelation | None
    selected_fact_refs: tuple[str, ...]
    semantic_labels: tuple[str, ...]
    allowed_claims: tuple[str, ...]
    prohibited_claims: tuple[str, ...]
    resolved_unknowns: tuple[UnknownResolution, ...]
    remaining_unknowns: tuple[str, ...]
    suppression_reasons: tuple[str, ...]
    point_in_time_exclusions: tuple[dict[str, str], ...]
    cash_flow_alignment_state: str
    cash_flow_context_used: bool
    consumption_eligible: bool
    shadow_used: bool


_METRIC_LABELS = {
    Metric.INVENTORY: "재고",
    Metric.TRADE_AR: "거래 매출채권",
    Metric.BROAD_AR: "광의 매출채권",
    Metric.TRADE_AP: "거래 매입채무",
    Metric.BROAD_AP: "광의 매입채무",
}
_RELATION_KEYS = {
    (Metric.TRADE_AR, Metric.REVENUE): "trade_ar_vs_revenue",
    (Metric.BROAD_AR, Metric.REVENUE): "broad_ar_vs_revenue",
    (Metric.INVENTORY, Metric.REVENUE): "inventory_vs_revenue",
    (Metric.INVENTORY, Metric.COGS): "inventory_vs_cogs",
    (Metric.TRADE_AP, Metric.COGS): "trade_ap_vs_cogs",
    (Metric.BROAD_AP, Metric.COGS): "broad_ap_vs_cogs",
}
_USAGE_MODES = {
    Metric.INVENTORY: UsageMode.INVENTORY_RELATION,
    Metric.TRADE_AR: UsageMode.TRADE_AR_RELATION,
    Metric.BROAD_AR: UsageMode.BROAD_AR_RELATION,
    Metric.TRADE_AP: UsageMode.TRADE_AP_RELATION,
    Metric.BROAD_AP: UsageMode.BROAD_AP_RELATION,
}
_WORKING_CAPITAL_LANGUAGE = re.compile(
    r"재고|매출채권|매입채무|수취채권|지급채무|운전자본|working\s*capital|"
    r"receivables?|payables?|inventory",
    re.IGNORECASE,
)
_INVENTORY_LANGUAGE = re.compile(r"재고|inventory", re.IGNORECASE)
_AR_LANGUAGE = re.compile(r"매출채권|수취채권|receivables?", re.IGNORECASE)
_AP_LANGUAGE = re.compile(r"매입채무|지급채무|payables?", re.IGNORECASE)
_ADVANCED_RATIO_LANGUAGE = re.compile(
    r"(?:^|\s)DSO(?=\s|는|가|:)|매출채권회전일수|"
    r"(?:^|\s)DPO(?=\s|는|가|:)|매입채무회전일수|"
    r"inventory\s*days|재고(?:자산)?회전일수|\bCCC\b|현금전환주기",
    re.IGNORECASE,
)
_CAUSAL_OVERCLAIM = re.compile(
    r"고객(?:이|들이)?\s*(?:돈|대금)을?\s*안\s*냈|회수\s*불능|수요\s*붕괴(?:가)?\s*확정|"
    r"공급업체\s*지급\s*지연(?:이)?\s*확정|supplier\s*payment\s*delay(?:ed)?|"
    r"유동성(?:이|은)?\s*(?:개선|악화)(?:됐|되었|했다)|"
    r"수요(?:가|는)?\s*(?:개선|악화)(?:됐|되었|했다)\s*(?:것이)?\s*확정|"
    r"회수(?:가|는)?\s*(?:개선|악화)(?:됐|되었|했다)\s*(?:것이)?\s*확정",
    re.IGNORECASE,
)
_STATUS_OR_VALUATION_CHANGE = re.compile(
    r"투자\s*논리(?:를|가)?\s*(?:강화|약화|무효)|valuation(?:을|이)?\s*(?:상향|하향)|"
    r"밸류에이션(?:을|이)?\s*(?:상향|하향)|경고(?:를|가)?\s*(?:개시|종료)",
    re.IGNORECASE,
)


def _metric_contexts(snapshot: WorkingCapitalCoreSnapshot) -> tuple[MetricContext, ...]:
    return tuple(
        MetricContext(
            metric=item.balance_metric,
            status=item.status.value,
            current_fact_id=item.current.fact_id if item.current else None,
            yoy_fact_id=item.yoy_fact.fact_id if item.yoy_fact else None,
            semantic_label=_METRIC_LABELS[item.balance_metric],
        )
        for item in snapshot.metric_states
    )


def _relation_pit_reasons(
    relation: WorkingCapitalRelation,
    facts: Mapping[str, FinancialFact],
    *,
    cutoff: date,
) -> tuple[str, ...]:
    reasons: list[str] = []
    for fact_id in relation.input_fact_ids:
        fact = facts.get(fact_id)
        if fact is None:
            reasons.append(f"relation_input_missing:{fact_id}")
        elif fact.source_available_at is None:
            reasons.append(f"source_availability_missing:{fact_id}")
        elif fact.source_available_at > cutoff:
            reasons.append(f"future_fact_after_cutoff:{fact_id}")
    return tuple(reasons)


def _relation_family(relation: WorkingCapitalRelation) -> str:
    return _RELATION_KEYS[(relation.balance_metric, relation.flow_metric)]


def _relation_applicability(
    relation: WorkingCapitalRelation,
    applicability: Mapping[str, str],
) -> str:
    family = _relation_family(relation)
    if family.startswith(("trade_ar", "broad_ar")):
        return applicability.get("ar_vs_revenue", "SECONDARY")
    if family.startswith(("trade_ap", "broad_ap")):
        return applicability.get("ap_vs_cogs", "SECONDARY")
    return applicability.get(family, "SECONDARY")


def _preference(industry: str) -> tuple[str, ...]:
    if industry == "memory_semiconductor":
        return (
            "inventory_vs_cogs",
            "inventory_vs_revenue",
            "trade_ar_vs_revenue",
            "broad_ar_vs_revenue",
        )
    if industry == "automotive":
        return (
            "inventory_vs_revenue",
            "inventory_vs_cogs",
            "trade_ar_vs_revenue",
            "broad_ar_vs_revenue",
        )
    if industry == "steel_materials":
        return (
            "inventory_vs_revenue",
            "trade_ar_vs_revenue",
            "inventory_vs_cogs",
            "broad_ar_vs_revenue",
        )
    if industry in {"industrial_epc", "transport_logistics"}:
        return (
            "trade_ar_vs_revenue",
            "inventory_vs_revenue",
            "broad_ar_vs_revenue",
            "inventory_vs_cogs",
        )
    if industry == "aerospace_epc":
        return (
            "broad_ar_vs_revenue",
            "inventory_vs_revenue",
            "broad_ap_vs_cogs",
        )
    if industry in {"cloud_platform_software", "hpc_data_center"}:
        return (
            "broad_ar_vs_revenue",
            "trade_ar_vs_revenue",
            "inventory_vs_revenue",
            "broad_ap_vs_cogs",
        )
    return (
        "trade_ar_vs_revenue",
        "broad_ar_vs_revenue",
        "inventory_vs_revenue",
        "inventory_vs_cogs",
        "trade_ap_vs_cogs",
        "broad_ap_vs_cogs",
    )


def _explicit_materiality(family: str, text: str) -> bool:
    if family.startswith("inventory"):
        return bool(_INVENTORY_LANGUAGE.search(text))
    if "_ar_" in f"_{family}_":
        return bool(_AR_LANGUAGE.search(text))
    return bool(_AP_LANGUAGE.search(text))


def _materiality_reason(
    *,
    industry: str,
    family: str,
    applicability: str,
    monitoring_text: str,
) -> str | None:
    if applicability == "NOT_APPLICABLE":
        return None
    if _explicit_materiality(family, monitoring_text):
        return "existing_working_capital_driver_or_unknown"
    if applicability == "PRIMARY":
        return "industry_primary_relation"
    if industry in {"biotech", "special_financial_like"}:
        return None
    return None


def _specificity_key(industry: str, monitoring_text: str) -> str:
    lowered = monitoring_text.casefold()
    if industry == "memory_semiconductor":
        if "foundry" in lowered or "파운드리" in monitoring_text:
            return "memory_foundry"
        if "nand" in lowered or "ssd" in lowered:
            return "memory_nand"
        return "memory_hbm"
    if industry == "industrial_epc":
        return "order_conversion"
    if industry == "transport_logistics":
        return "freight_collection"
    if industry == "steel_materials":
        return "steel_spread"
    if industry == "automotive":
        return "vehicle_delivery"
    if industry == "cloud_platform_software":
        return "cloud_software_collection"
    if industry == "hpc_data_center":
        return "billing_conversion"
    return industry


def _selected_relation(
    relation: WorkingCapitalRelation,
    *,
    applicability: str,
) -> SelectedRelation:
    assert relation.relation_id is not None
    assert relation.direction is not None
    assert relation.balance_semantic is not None
    assert relation.flow_semantic is not None
    assert relation.gap_percentage_points is not None
    assert relation.current_balance_fact_id is not None
    assert relation.balance_yoy_fact_id is not None
    assert relation.flow_yoy_fact_id is not None
    return SelectedRelation(
        relation_id=relation.relation_id,
        family=_relation_family(relation),
        direction=relation.direction,
        balance_metric=relation.balance_metric,
        balance_semantic=relation.balance_semantic,
        balance_scope=relation.balance_scope,
        flow_metric=relation.flow_metric,
        flow_semantic=relation.flow_semantic,
        gap_percentage_points=relation.gap_percentage_points,
        input_fact_ids=relation.input_fact_ids,
        current_balance_fact_id=relation.current_balance_fact_id,
        balance_yoy_fact_id=relation.balance_yoy_fact_id,
        flow_yoy_fact_id=relation.flow_yoy_fact_id,
        applicability=applicability,
    )


def _current_available_metrics(
    snapshot: WorkingCapitalCoreSnapshot,
    *,
    formal_date: date | None,
    cutoff: date,
) -> frozenset[Metric]:
    if formal_date is None:
        return frozenset()
    available: set[Metric] = set()
    for item in snapshot.metric_states:
        fact = item.current
        if (
            item.status == EligibilityStatus.ELIGIBLE
            and fact is not None
            and fact.period.end == formal_date
            and fact.source_available_at is not None
            and fact.source_available_at <= cutoff
        ):
            available.add(item.balance_metric)
    return frozenset(available)


def _available_unknown_metric(
    value: str,
    available_metrics: frozenset[Metric],
) -> Metric | None:
    if _INVENTORY_LANGUAGE.search(value) and Metric.INVENTORY in available_metrics:
        return Metric.INVENTORY
    if _AR_LANGUAGE.search(value):
        if Metric.TRADE_AR in available_metrics:
            return Metric.TRADE_AR
        if Metric.BROAD_AR in available_metrics:
            return Metric.BROAD_AR
    if _AP_LANGUAGE.search(value):
        if Metric.TRADE_AP in available_metrics:
            return Metric.TRADE_AP
        if Metric.BROAD_AP in available_metrics:
            return Metric.BROAD_AP
    return None


def resolve_working_capital_unknowns(
    unknowns: Sequence[str],
    *,
    selected: SelectedRelation | None,
    freshness_state: FreshnessState,
    available_metrics: Sequence[Metric] = (),
) -> tuple[tuple[UnknownResolution, ...], tuple[str, ...]]:
    resolutions: list[UnknownResolution] = []
    remaining: list[str] = []
    known_metrics = frozenset(available_metrics)
    if selected is not None:
        known_metrics = known_metrics | {selected.balance_metric}
    for value in unknowns:
        if not _WORKING_CAPITAL_LANGUAGE.search(value):
            remaining.append(value)
            continue
        if freshness_state == FreshnessState.NOT_APPLICABLE:
            resolutions.append(
                UnknownResolution(value, UnknownResolutionState.NOT_APPLICABLE, None)
            )
            continue
        available_metric = _available_unknown_metric(value, known_metrics)
        if available_metric is None:
            state = (
                UnknownResolutionState.STALE_CONTEXT_ONLY
                if freshness_state
                in {
                    FreshnessState.FORMAL_LAGGING_PROVISIONAL,
                    FreshnessState.STALE_CONTEXT_ONLY,
                }
                else UnknownResolutionState.STILL_VALID
            )
            resolutions.append(UnknownResolution(value, state, value))
            remaining.append(value)
            continue
        if available_metric in {Metric.BROAD_AR, Metric.BROAD_AP}:
            noun = "거래 매출채권" if available_metric == Metric.BROAD_AR else "거래 매입채무"
            replacement = f"광의 잔액은 확인되지만 {noun}만의 정확한 범위는 아직 확인되지 않았습니다."
            resolutions.append(
                UnknownResolution(
                    value,
                    UnknownResolutionState.RESOLVED_BROAD_ONLY,
                    replacement,
                )
            )
            remaining.append(replacement)
        else:
            resolutions.append(
                UnknownResolution(value, UnknownResolutionState.RESOLVED_EXACT, None)
            )
    return tuple(resolutions), tuple(remaining)


def build_working_capital_reasoning_context(
    snapshot: WorkingCapitalCoreSnapshot,
    *,
    ticker: str,
    market: str,
    packet_id: str,
    assessment_date: date,
    cutoff: date,
    industry: str,
    monitoring_text: str = "",
    existing_unknowns: Sequence[str] = (),
    latest_formal_balance_date: date | None = None,
    latest_provisional_period_end: date | None = None,
    formal_lagging_provisional: bool = False,
    cash_flow_period_end: date | None = None,
) -> WorkingCapitalReasoningContext:
    facts = {item.fact_id: item for item in snapshot.canonical_facts}
    prohibited = (
        "future_fact_used",
        "stale_as_current",
        "broad_trade_semantic_mislabel",
        "contract_asset_as_trade_ar",
        "accrued_liability_as_trade_ap",
        "unsupported_causal_claim",
        "dso_inventory_days_dpo_ccc",
        "automatic_thesis_warning_or_valuation_change",
    )
    formal_date = latest_formal_balance_date or snapshot.latest_safe_working_capital_date
    available_metrics = _current_available_metrics(
        snapshot,
        formal_date=formal_date,
        cutoff=cutoff,
    )
    not_applicable = snapshot.industry_status == EligibilityStatus.NOT_APPLICABLE
    if not_applicable:
        resolved, remaining = resolve_working_capital_unknowns(
            existing_unknowns,
            selected=None,
            freshness_state=FreshnessState.NOT_APPLICABLE,
        )
        return WorkingCapitalReasoningContext(
            ticker,
            market,
            packet_id,
            assessment_date,
            cutoff,
            "NOT_APPLICABLE",
            UsageMode.NOT_APPLICABLE,
            formal_date,
            FreshnessState.NOT_APPLICABLE,
            "PASS",
            industry,
            _specificity_key(industry, monitoring_text),
            snapshot.industry_applicability,
            None,
            _metric_contexts(snapshot),
            None,
            (),
            (),
            (),
            prohibited,
            resolved,
            remaining,
            ("generic_working_capital_not_applicable",),
            (),
            "NOT_APPLICABLE",
            False,
            False,
            False,
        )

    pit_exclusions: list[dict[str, str]] = []
    candidates: list[tuple[int, WorkingCapitalRelation, str, str]] = []
    preference = _preference(industry)
    for relation in snapshot.relations:
        if relation.status != EligibilityStatus.ELIGIBLE or relation.relation_id is None:
            continue
        pit_reasons = _relation_pit_reasons(relation, facts, cutoff=cutoff)
        if pit_reasons:
            pit_exclusions.extend(
                {"relation_id": relation.relation_id, "reason": reason}
                for reason in pit_reasons
            )
            continue
        current = facts.get(relation.current_balance_fact_id or "")
        if current is None or formal_date is None:
            pit_exclusions.append(
                {
                    "relation_id": relation.relation_id,
                    "reason": "current_balance_or_formal_date_missing",
                }
            )
            continue
        if current.period.end != formal_date:
            pit_exclusions.append(
                {
                    "relation_id": relation.relation_id,
                    "reason": "relation_not_latest_formal_balance",
                }
            )
            continue
        family = _relation_family(relation)
        applicability = _relation_applicability(
            relation, snapshot.industry_applicability
        )
        materiality = _materiality_reason(
            industry=industry,
            family=family,
            applicability=applicability,
            monitoring_text=" ".join((monitoring_text, *existing_unknowns)),
        )
        if materiality is None:
            continue
        try:
            rank = preference.index(family)
        except ValueError:
            rank = len(preference)
        candidates.append((rank, relation, applicability, materiality))

    selected: SelectedRelation | None = None
    materiality_reason: str | None = None
    if candidates:
        _, relation, applicability, materiality_reason = min(
            candidates, key=lambda item: (item[0], item[1].relation_id or "")
        )
        selected = _selected_relation(relation, applicability=applicability)

    if formal_date is None:
        freshness = FreshnessState.BLOCKED
    elif selected is None:
        freshness = FreshnessState.BLOCKED
    else:
        current = facts[selected.current_balance_fact_id]
        if current.period.end < formal_date:
            freshness = FreshnessState.STALE_CONTEXT_ONLY
        elif current.period.end > formal_date:
            freshness = FreshnessState.BLOCKED
        elif formal_lagging_provisional or (
            latest_provisional_period_end
            and latest_provisional_period_end > formal_date
        ):
            freshness = FreshnessState.FORMAL_LAGGING_PROVISIONAL
        else:
            freshness = FreshnessState.CURRENT_FORMAL

    shadow_used = selected is not None and freshness == FreshnessState.CURRENT_FORMAL
    consumption_eligible = selected is not None and freshness in {
        FreshnessState.CURRENT_FORMAL,
        FreshnessState.FORMAL_LAGGING_PROVISIONAL,
    }
    suppression: list[str] = []
    if selected is None:
        suppression.append("no_material_current_relation")
    if freshness == FreshnessState.FORMAL_LAGGING_PROVISIONAL:
        suppression.append("newer_provisional_period_not_balance_aligned")
    elif freshness == FreshnessState.STALE_CONTEXT_ONLY:
        suppression.append("historical_relation_not_current")
    elif freshness == FreshnessState.BLOCKED:
        suppression.append("working_capital_context_blocked")
    resolved, remaining = resolve_working_capital_unknowns(
        existing_unknowns,
        selected=selected if shadow_used else None,
        freshness_state=(
            FreshnessState.CURRENT_FORMAL
            if available_metrics
            and freshness
            not in {
                FreshnessState.FORMAL_LAGGING_PROVISIONAL,
                FreshnessState.STALE_CONTEXT_ONLY,
            }
            else freshness
        ),
        available_metrics=available_metrics,
    )
    cash_flow_alignment = "NOT_PROVIDED"
    cash_flow_used = False
    if selected is not None and cash_flow_period_end is not None:
        current = facts[selected.current_balance_fact_id]
        if current.period.end == cash_flow_period_end:
            cash_flow_alignment = "COMPATIBLE_FORMAL_PERIOD"
            cash_flow_used = shadow_used
        else:
            cash_flow_alignment = "PERIOD_MISMATCH_SUPPRESSED"
    mode = (
        _USAGE_MODES[selected.balance_metric]
        if shadow_used and selected is not None
        else UsageMode.CONTEXT_ONLY
        if freshness == FreshnessState.FORMAL_LAGGING_PROVISIONAL
        else UsageMode.SUPPRESSED
    )
    status = "READY" if shadow_used else "CONTEXT_ONLY" if consumption_eligible else "SUPPRESSED"
    return WorkingCapitalReasoningContext(
        ticker=ticker,
        market=market,
        packet_id=packet_id,
        assessment_date=assessment_date,
        cutoff=cutoff,
        status=status,
        usage_mode=mode,
        latest_formal_balance_date=formal_date,
        freshness_state=freshness,
        pit_state="PASS" if not pit_exclusions else "PASS_WITH_EXCLUSIONS",
        industry=industry,
        specificity_key=_specificity_key(industry, monitoring_text),
        industry_applicability=snapshot.industry_applicability,
        materiality_reason=materiality_reason,
        metric_contexts=_metric_contexts(snapshot),
        selected_relation=selected,
        selected_fact_refs=selected.input_fact_ids if selected else (),
        semantic_labels=(
            (_METRIC_LABELS[selected.balance_metric], selected.flow_metric.value)
            if selected
            else ()
        ),
        allowed_claims=("typed_relation", "cautious_earnings_quality_context")
        if shadow_used
        else (),
        prohibited_claims=prohibited,
        resolved_unknowns=resolved,
        remaining_unknowns=remaining,
        suppression_reasons=tuple(dict.fromkeys(suppression)),
        point_in_time_exclusions=tuple(pit_exclusions),
        cash_flow_alignment_state=cash_flow_alignment,
        cash_flow_context_used=cash_flow_used,
        consumption_eligible=consumption_eligible,
        shadow_used=shadow_used,
    )


def _gap_display(value: Decimal) -> str:
    rounded = abs(value).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
    return f"{rounded}%p"


def _direction_text(selected: SelectedRelation) -> str:
    label = _METRIC_LABELS[selected.balance_metric]
    flow = "매출" if selected.flow_metric == Metric.REVENUE else "매출원가"
    if selected.direction == RelationDirection.EQUAL:
        return f"{label} 증가율은 {flow} 증가율과 같았습니다"
    comparator = "앞섰습니다" if selected.direction == RelationDirection.GREATER else "밑돌았습니다"
    return f"{label} 증가율은 {flow} 증가율보다 {_gap_display(selected.gap_percentage_points)} {comparator}"


def _industry_interpretation(
    selected: SelectedRelation,
    industry: str,
    specificity_key: str,
) -> str:
    metric = selected.balance_metric
    greater = selected.direction == RelationDirection.GREATER
    if metric == Metric.INVENTORY:
        if industry == "memory_semiconductor":
            if greater:
                mechanism = {
                    "memory_foundry": "메모리 믹스·파운드리 수율",
                    "memory_nand": "NAND ASP·SSD 수요",
                }.get(specificity_key, "ASP·HBM 믹스")
                return f"재고 전환은 {mechanism}도 함께 점검해야 하며, 이 관계만으로 공급과잉을 확정하지 않습니다."
            mechanism = {
                "memory_foundry": "메모리 믹스·파운드리 수율",
                "memory_nand": "NAND ASP·SSD 수요",
            }.get(specificity_key, "ASP·HBM 수요")
            return f"재고 정상화와 양립하지만 {mechanism} 개선을 확정하지 않습니다."
        if industry == "automotive":
            return "재고 전환은 인도량·인센티브·제품 믹스와 함께 확인하며 수요 방향을 확정하지 않습니다."
        if industry == "steel_materials":
            return "재고 전환은 철강 스프레드·원재료·물량과 함께 확인하며 사이클 방향을 확정하지 않습니다."
        return "재고 전환은 매출 인식과 제품 믹스를 함께 확인할 단서이며 수요 원인을 확정하지 않습니다."
    if metric in {Metric.TRADE_AR, Metric.BROAD_AR}:
        scope = (
            "거래 매출채권"
            if metric == Metric.TRADE_AR
            else "거래성 범위가 확인되지 않은 광의 매출채권"
        )
        if metric == Metric.TRADE_AR and specificity_key == "order_conversion":
            return "수주 매출의 회수 전환을 점검할 단서이지만 고객 지급 지연을 확정하지 않습니다."
        if metric == Metric.TRADE_AR and specificity_key == "freight_collection":
            return "운송 매출의 회수 전환을 점검할 단서이지만 고객 지급 지연을 확정하지 않습니다."
        if greater:
            return f"{scope}의 회수 품질을 점검할 단서이지만 고객 지급 지연을 확정하지 않습니다."
        return f"{scope}의 흐름은 회수 규율과 양립하지만 회수 개선을 확정하지 않습니다."
    scope = "거래 매입채무" if metric == Metric.TRADE_AP else "광의 매입채무"
    return f"{scope}의 변화는 지급 구조를 확인할 단서일 뿐 공급업체 지급 지연이나 유동성 변화를 확정하지 않습니다."


def render_working_capital_reasoning(
    context: WorkingCapitalReasoningContext,
) -> WorkingCapitalShadowReasoning | None:
    selected = context.selected_relation
    if not context.shadow_used or selected is None:
        return None
    first = _direction_text(selected)
    text = (
        f"{first}. "
        f"{_industry_interpretation(selected, context.industry, context.specificity_key)}"
    )
    if context.cash_flow_context_used:
        text += " 같은 정식 기간의 현금흐름 문맥을 보완하지만 현금흐름 변동의 원인으로 단정하지 않습니다."
    claims: tuple[WorkingCapitalNumericClaim, ...] = ()
    if selected.direction != RelationDirection.EQUAL:
        claims = (
            WorkingCapitalNumericClaim(
                relation_id=selected.relation_id,
                semantic_type=selected.family,
                value=str(selected.gap_percentage_points),
                display=_gap_display(selected.gap_percentage_points),
                input_fact_ids=selected.input_fact_ids,
            ),
        )
    return WorkingCapitalShadowReasoning(
        text=text,
        relation_ids=(selected.relation_id,),
        fact_ids=selected.input_fact_ids,
        numeric_claims=claims,
    )


def validate_working_capital_reasoning(
    context: WorkingCapitalReasoningContext,
    facts: Mapping[str, FinancialFact],
    relations: Mapping[str, WorkingCapitalRelation],
    reasoning: WorkingCapitalShadowReasoning | None,
    *,
    thesis_status_changed: bool = False,
    valuation_changed: bool = False,
    warning_changed: bool = False,
) -> tuple[str, ...]:
    errors: list[str] = []
    if reasoning is None:
        return ()
    text = reasoning.text
    selected = context.selected_relation
    if not context.shadow_used or selected is None:
        errors.append("suppressed_context_rendered")
        return tuple(errors)
    if context.freshness_state != FreshnessState.CURRENT_FORMAL:
        errors.append("stale_or_lagging_relation_rendered")
    if reasoning.relation_ids != (selected.relation_id,):
        errors.append("relation_not_primary_context")
    relation = relations.get(selected.relation_id)
    if relation is None:
        errors.append("canonical_relation_missing")
    else:
        if relation.direction != selected.direction:
            errors.append("relation_direction_mismatch")
        if relation.gap_percentage_points != selected.gap_percentage_points:
            errors.append("relation_gap_mismatch")
        if relation.input_fact_ids != selected.input_fact_ids:
            errors.append("relation_input_lineage_mismatch")
    for fact_id in reasoning.fact_ids:
        fact = facts.get(fact_id)
        if fact is None:
            errors.append("relation_fact_missing")
        elif fact.source_available_at is None or fact.source_available_at > context.cutoff:
            errors.append("future_fact_used")
    for claim in reasoning.numeric_claims:
        if claim.relation_id != selected.relation_id:
            errors.append("numeric_relation_mismatch")
        if Decimal(claim.value) != selected.gap_percentage_points:
            errors.append("numeric_value_mismatch")
        if claim.display != _gap_display(selected.gap_percentage_points):
            errors.append("numeric_display_mismatch")
        if claim.display not in text:
            errors.append("numeric_display_unresolved")
        if claim.input_fact_ids != selected.input_fact_ids:
            errors.append("numeric_lineage_mismatch")
        if claim.owner != "business_earnings":
            errors.append("numeric_owner_invalid")
    if selected.balance_metric == Metric.BROAD_AR and re.search(
        r"거래\s*매출채권|trade\s*receivables?", text, re.IGNORECASE
    ):
        errors.append("broad_ar_mislabeled_trade_ar")
    if selected.balance_metric == Metric.BROAD_AP and re.search(
        r"거래\s*매입채무|공급업체\s*매입채무|trade\s*payables?", text, re.IGNORECASE
    ):
        errors.append("broad_ap_mislabeled_trade_ap")
    if selected.balance_metric in {Metric.TRADE_AR, Metric.BROAD_AR} and re.search(
        r"계약자산|contract\s*assets?", text, re.IGNORECASE
    ):
        errors.append("contract_asset_leakage")
    if selected.balance_metric in {Metric.TRADE_AP, Metric.BROAD_AP} and re.search(
        r"미지급비용|accrued\s*liabilit", text, re.IGNORECASE
    ):
        errors.append("accrued_liability_leakage")
    if _ADVANCED_RATIO_LANGUAGE.search(text):
        errors.append("unsupported_advanced_working_capital_ratio")
    if _CAUSAL_OVERCLAIM.search(text):
        errors.append("unsupported_causal_overclaim")
    if _STATUS_OR_VALUATION_CHANGE.search(text):
        errors.append("working_capital_auto_state_change_claim")
    if thesis_status_changed:
        errors.append("working_capital_based_thesis_status_change")
    if valuation_changed:
        errors.append("working_capital_based_valuation_change")
    if warning_changed:
        errors.append("working_capital_based_warning_change")
    return tuple(dict.fromkeys(errors))


def context_to_dict(context: WorkingCapitalReasoningContext) -> dict[str, object]:
    selected = context.selected_relation
    return {
        "contract": CONTRACT_VERSION,
        "ticker": context.ticker,
        "market": context.market,
        "packet_id": context.packet_id,
        "assessment_date": context.assessment_date.isoformat(),
        "cutoff": context.cutoff.isoformat(),
        "status": context.status,
        "usage_mode": context.usage_mode.value,
        "latest_formal_balance_date": (
            context.latest_formal_balance_date.isoformat()
            if context.latest_formal_balance_date
            else None
        ),
        "freshness_state": context.freshness_state.value,
        "pit_state": context.pit_state,
        "industry": context.industry,
        "specificity_key": context.specificity_key,
        "industry_applicability": dict(context.industry_applicability),
        "materiality_reason": context.materiality_reason,
        "metric_contexts": [
            {
                "metric": item.metric.value,
                "status": item.status,
                "current_fact_id": item.current_fact_id,
                "yoy_fact_id": item.yoy_fact_id,
                "semantic_label": item.semantic_label,
            }
            for item in context.metric_contexts
        ],
        "selected_relations": (
            [
                {
                    "relation_id": selected.relation_id,
                    "family": selected.family,
                    "direction": selected.direction.value,
                    "balance_metric": selected.balance_metric.value,
                    "balance_semantic": selected.balance_semantic,
                    "balance_scope": selected.balance_scope,
                    "flow_metric": selected.flow_metric.value,
                    "flow_semantic": selected.flow_semantic,
                    "gap_percentage_points": str(selected.gap_percentage_points),
                    "input_fact_ids": list(selected.input_fact_ids),
                    "applicability": selected.applicability,
                }
            ]
            if selected
            else []
        ),
        "selected_fact_refs": list(context.selected_fact_refs),
        "semantic_labels": list(context.semantic_labels),
        "allowed_claims": list(context.allowed_claims),
        "prohibited_claims": list(context.prohibited_claims),
        "resolved_unknowns": [
            {
                "original": item.original,
                "state": item.state.value,
                "replacement": item.replacement,
            }
            for item in context.resolved_unknowns
        ],
        "remaining_unknowns": list(context.remaining_unknowns),
        "suppression_reasons": list(context.suppression_reasons),
        "point_in_time_exclusions": list(context.point_in_time_exclusions),
        "cash_flow_alignment_state": context.cash_flow_alignment_state,
        "cash_flow_context_used": context.cash_flow_context_used,
        "consumption_eligible": context.consumption_eligible,
        "shadow_used": context.shadow_used,
    }


def reasoning_to_dict(
    reasoning: WorkingCapitalShadowReasoning | None,
) -> dict[str, object] | None:
    if reasoning is None:
        return None
    return {
        "text": reasoning.text,
        "relation_ids": list(reasoning.relation_ids),
        "fact_ids": list(reasoning.fact_ids),
        "numeric_claims": [
            {
                "relation_id": item.relation_id,
                "semantic_type": item.semantic_type,
                "value": item.value,
                "display": item.display,
                "input_fact_ids": list(item.input_fact_ids),
                "text_ref": item.text_ref,
                "owner": item.owner,
            }
            for item in reasoning.numeric_claims
        ],
    }
