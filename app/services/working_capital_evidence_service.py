from __future__ import annotations

import hashlib
from dataclasses import dataclass, replace
from datetime import date
from decimal import Decimal, InvalidOperation
from enum import StrEnum
from typing import Iterable, Mapping, Sequence

from app.services.cash_flow_capital_efficiency_service import (
    EligibilityStatus,
    FactType,
    FinancialFact,
    Metric,
    PeriodIdentity,
    PeriodType,
)


CONTRACT_VERSION = "working-capital-evidence-v1"
RESTATEMENT_POLICY_ID = "latest-authoritative-exact-semantic-v1"

FORMAL_FORMS = {
    "10-K",
    "10-K/A",
    "10-Q",
    "10-Q/A",
    "20-F",
    "20-F/A",
    "40-F",
    "40-F/A",
    "6-K",
    "6-K/A",
}
ANNUAL_FORMS = {"10-K", "10-K/A", "20-F", "20-F/A", "40-F", "40-F/A"}


class FactKind(StrEnum):
    BALANCE = "BALANCE"
    FLOW = "FLOW"


class RelationType(StrEnum):
    BALANCE_INCREASED = "BALANCE_INCREASED"
    BALANCE_DECREASED = "BALANCE_DECREASED"
    BALANCE_UNCHANGED = "BALANCE_UNCHANGED"
    AR_GROWTH_GT_REVENUE_GROWTH = "AR_GROWTH_GT_REVENUE_GROWTH"
    AR_GROWTH_LT_REVENUE_GROWTH = "AR_GROWTH_LT_REVENUE_GROWTH"
    AR_GROWTH_EQ_REVENUE_GROWTH = "AR_GROWTH_EQ_REVENUE_GROWTH"
    INVENTORY_GROWTH_GT_REVENUE_GROWTH = (
        "INVENTORY_GROWTH_GT_REVENUE_GROWTH"
    )
    INVENTORY_GROWTH_LT_REVENUE_GROWTH = (
        "INVENTORY_GROWTH_LT_REVENUE_GROWTH"
    )
    INVENTORY_GROWTH_EQ_REVENUE_GROWTH = (
        "INVENTORY_GROWTH_EQ_REVENUE_GROWTH"
    )
    INVENTORY_GROWTH_GT_COGS_GROWTH = "INVENTORY_GROWTH_GT_COGS_GROWTH"
    INVENTORY_GROWTH_LT_COGS_GROWTH = "INVENTORY_GROWTH_LT_COGS_GROWTH"
    INVENTORY_GROWTH_EQ_COGS_GROWTH = "INVENTORY_GROWTH_EQ_COGS_GROWTH"
    AP_GROWTH_GT_COGS_GROWTH = "AP_GROWTH_GT_COGS_GROWTH"
    AP_GROWTH_LT_COGS_GROWTH = "AP_GROWTH_LT_COGS_GROWTH"
    AP_GROWTH_EQ_COGS_GROWTH = "AP_GROWTH_EQ_COGS_GROWTH"


class FreshnessState(StrEnum):
    CURRENT_FORMAL = "CURRENT_FORMAL"
    FORMAL_LAGGING_PROVISIONAL = "FORMAL_LAGGING_PROVISIONAL"
    HISTORICAL_NOT_CURRENT = "HISTORICAL_NOT_CURRENT"
    SOURCE_DATE_UNAVAILABLE = "SOURCE_DATE_UNAVAILABLE"


@dataclass(frozen=True)
class SemanticRegistryEntry:
    metric: Metric
    namespace: str
    tag: str
    fact_kind: FactKind
    semantic_scope: str
    balance_scope: str | None
    net_gross_scope: str | None
    priority: int

    @property
    def semantic(self) -> str:
        return f"{self.namespace}:{self.tag}"


SEC_SEMANTIC_REGISTRY = (
    SemanticRegistryEntry(
        Metric.INVENTORY,
        "us-gaap",
        "InventoryNet",
        FactKind.BALANCE,
        "total_inventory",
        "total",
        "net",
        100,
    ),
    SemanticRegistryEntry(
        Metric.INVENTORY,
        "ifrs-full",
        "Inventories",
        FactKind.BALANCE,
        "total_inventory",
        "total",
        "issuer_reported",
        100,
    ),
    SemanticRegistryEntry(
        Metric.INVENTORY,
        "ifrs-full",
        "InventoriesTotal",
        FactKind.BALANCE,
        "total_inventory",
        "total",
        "issuer_reported",
        95,
    ),
    SemanticRegistryEntry(
        Metric.TRADE_AR,
        "us-gaap",
        "AccountsReceivableTradeCurrent",
        FactKind.BALANCE,
        "trade_receivables",
        "current",
        "issuer_reported",
        100,
    ),
    SemanticRegistryEntry(
        Metric.TRADE_AR,
        "ifrs-full",
        "CurrentTradeReceivables",
        FactKind.BALANCE,
        "trade_receivables",
        "current",
        "issuer_reported",
        100,
    ),
    SemanticRegistryEntry(
        Metric.TRADE_AR,
        "ifrs-full",
        "TradeReceivables",
        FactKind.BALANCE,
        "trade_receivables",
        "issuer_reported_total",
        "issuer_reported",
        95,
    ),
    SemanticRegistryEntry(
        Metric.BROAD_AR,
        "us-gaap",
        "AccountsReceivableNetCurrent",
        FactKind.BALANCE,
        "accounts_receivable_not_proven_trade_only",
        "current",
        "net",
        100,
    ),
    SemanticRegistryEntry(
        Metric.BROAD_AR,
        "us-gaap",
        "AccountsAndOtherReceivablesNetCurrent",
        FactKind.BALANCE,
        "accounts_and_other_receivables",
        "current",
        "net",
        90,
    ),
    SemanticRegistryEntry(
        Metric.BROAD_AR,
        "us-gaap",
        "AccountsAndNotesReceivableNet",
        FactKind.BALANCE,
        "accounts_and_notes_receivable",
        "issuer_reported_total",
        "net",
        85,
    ),
    SemanticRegistryEntry(
        Metric.BROAD_AR,
        "ifrs-full",
        "TradeAndOtherCurrentReceivables",
        FactKind.BALANCE,
        "trade_and_other_receivables",
        "current",
        "issuer_reported",
        100,
    ),
    SemanticRegistryEntry(
        Metric.BROAD_AR,
        "ifrs-full",
        "TradeAndOtherReceivables",
        FactKind.BALANCE,
        "trade_and_other_receivables",
        "issuer_reported_total",
        "issuer_reported",
        90,
    ),
    SemanticRegistryEntry(
        Metric.TRADE_AP,
        "us-gaap",
        "AccountsPayableTradeCurrent",
        FactKind.BALANCE,
        "trade_payables",
        "current",
        "issuer_reported",
        100,
    ),
    SemanticRegistryEntry(
        Metric.TRADE_AP,
        "ifrs-full",
        "TradePayables",
        FactKind.BALANCE,
        "trade_payables",
        "issuer_reported_total",
        "issuer_reported",
        100,
    ),
    SemanticRegistryEntry(
        Metric.TRADE_AP,
        "ifrs-full",
        "TradeAndOtherCurrentPayablesToTradeSuppliers",
        FactKind.BALANCE,
        "trade_payables_to_suppliers",
        "current",
        "issuer_reported",
        95,
    ),
    SemanticRegistryEntry(
        Metric.BROAD_AP,
        "us-gaap",
        "AccountsPayableCurrent",
        FactKind.BALANCE,
        "accounts_payable_not_proven_trade_only",
        "current",
        "issuer_reported",
        100,
    ),
    SemanticRegistryEntry(
        Metric.BROAD_AP,
        "us-gaap",
        "AccountsPayableAndAccruedLiabilitiesCurrent",
        FactKind.BALANCE,
        "accounts_payable_and_accrued_liabilities",
        "current",
        "issuer_reported",
        90,
    ),
    SemanticRegistryEntry(
        Metric.BROAD_AP,
        "ifrs-full",
        "TradeAndOtherCurrentPayables",
        FactKind.BALANCE,
        "trade_and_other_payables",
        "current",
        "issuer_reported",
        100,
    ),
    SemanticRegistryEntry(
        Metric.BROAD_AP,
        "ifrs-full",
        "TradeAndOtherPayables",
        FactKind.BALANCE,
        "trade_and_other_payables",
        "issuer_reported_total",
        "issuer_reported",
        90,
    ),
    SemanticRegistryEntry(
        Metric.REVENUE,
        "us-gaap",
        "RevenueFromContractWithCustomerExcludingAssessedTax",
        FactKind.FLOW,
        "revenue_from_customers",
        None,
        None,
        100,
    ),
    SemanticRegistryEntry(
        Metric.REVENUE,
        "us-gaap",
        "Revenues",
        FactKind.FLOW,
        "revenue",
        None,
        None,
        90,
    ),
    SemanticRegistryEntry(
        Metric.REVENUE,
        "us-gaap",
        "SalesRevenueNet",
        FactKind.FLOW,
        "net_sales_revenue",
        None,
        None,
        85,
    ),
    SemanticRegistryEntry(
        Metric.REVENUE,
        "ifrs-full",
        "Revenue",
        FactKind.FLOW,
        "revenue",
        None,
        None,
        100,
    ),
    SemanticRegistryEntry(
        Metric.COGS,
        "us-gaap",
        "CostOfRevenue",
        FactKind.FLOW,
        "cost_of_revenue",
        None,
        None,
        100,
    ),
    SemanticRegistryEntry(
        Metric.COGS,
        "us-gaap",
        "CostOfGoodsAndServicesSold",
        FactKind.FLOW,
        "cost_of_goods_and_services_sold",
        None,
        None,
        95,
    ),
    SemanticRegistryEntry(
        Metric.COGS,
        "us-gaap",
        "CostOfGoodsSold",
        FactKind.FLOW,
        "cost_of_goods_sold",
        None,
        None,
        90,
    ),
    SemanticRegistryEntry(
        Metric.COGS,
        "ifrs-full",
        "CostOfSales",
        FactKind.FLOW,
        "cost_of_sales",
        None,
        None,
        100,
    ),
)
REGISTRY_BY_SEMANTIC = {entry.semantic: entry for entry in SEC_SEMANTIC_REGISTRY}


@dataclass(frozen=True)
class OfficialFinancialOccurrence:
    issuer_id: str
    value: Decimal
    currency: str | None
    unit: str | None
    period_start: date | None
    period_end: date | None
    fiscal_year: int | None
    fiscal_period: str | None
    source_provider: str
    source_document_id: str | None
    source_document_type: str | None
    filing_date: date | None
    namespace: str
    tag: str
    raw_payload_sha256: str | None
    entity_scope: str | None
    statement_basis: str | None
    frame: str | None = None
    source_column: str | None = None

    @property
    def semantic(self) -> str:
        return f"{self.namespace}:{self.tag}"


@dataclass(frozen=True)
class WorkingCapitalBatch:
    facts: tuple[FinancialFact, ...]
    denials: tuple[dict[str, str], ...]
    extracted_occurrences: int
    exact_duplicates_suppressed: int
    conflicts: int


@dataclass(frozen=True)
class ComparableSelection:
    status: EligibilityStatus
    current: FinancialFact | None
    prior: FinancialFact | None
    reasons: tuple[str, ...] = ()


@dataclass(frozen=True)
class ComparableMovement:
    status: EligibilityStatus
    current_fact_id: str | None
    prior_fact_id: str | None
    absolute_delta: Decimal | None
    growth_pct: Decimal | None
    direction: RelationType | None
    reasons: tuple[str, ...] = ()


@dataclass(frozen=True)
class CrossGrowthRelation:
    status: EligibilityStatus
    relation_id: str | None
    relation_type: RelationType | None
    percentage_point_difference: Decimal | None
    input_fact_ids: tuple[str, ...] = ()
    formula: str | None = None
    reasons: tuple[str, ...] = ()


def fact_available_at(fact: FinancialFact, cutoff: date) -> bool:
    return bool(
        fact.source_available_at is not None and fact.source_available_at <= cutoff
    )


def classify_freshness(
    fact: FinancialFact,
    *,
    latest_formal_balance_date: date,
    latest_provisional_period_end: date | None,
) -> FreshnessState:
    if fact.source_available_at is None:
        return FreshnessState.SOURCE_DATE_UNAVAILABLE
    if fact.period.end != latest_formal_balance_date:
        return FreshnessState.HISTORICAL_NOT_CURRENT
    if (
        latest_provisional_period_end is not None
        and latest_provisional_period_end > latest_formal_balance_date
    ):
        return FreshnessState.FORMAL_LAGGING_PROVISIONAL
    return FreshnessState.CURRENT_FORMAL


def _parse_date(value: object) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(str(value))
    except ValueError:
        return None


def _parse_decimal(value: object) -> Decimal | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        return Decimal(str(value).replace(",", ""))
    except (InvalidOperation, ValueError):
        return None


def _currency_from_unit(unit: str) -> str | None:
    normalized = unit.strip().upper()
    if len(normalized) == 3 and normalized.isalpha():
        return normalized
    return None


def _fiscal_quarter(value: str | None) -> int | None:
    if value in {"Q1", "Q2", "Q3", "Q4"}:
        return int(value[1])
    if value == "FY":
        return 4
    return None


def _flow_period(occurrence: OfficialFinancialOccurrence) -> PeriodIdentity | None:
    if (
        occurrence.period_start is None
        or occurrence.period_end is None
        or occurrence.fiscal_year is None
    ):
        return None
    duration = (occurrence.period_end - occurrence.period_start).days + 1
    fiscal_quarter = _fiscal_quarter(occurrence.fiscal_period)
    form = occurrence.source_document_type or ""
    if (
        occurrence.fiscal_period == "FY" or form in ANNUAL_FORMS
    ) and 330 <= duration <= 400:
        period_type = PeriodType.FY
        fiscal_quarter = 4
    elif fiscal_quarter == 1 and 70 <= duration <= 110:
        period_type = PeriodType.QTD
    elif fiscal_quarter in {2, 3} and 70 <= duration <= 110:
        period_type = PeriodType.QTD
    elif fiscal_quarter == 2 and 150 <= duration <= 210:
        period_type = PeriodType.YTD
    elif fiscal_quarter == 3 and 240 <= duration <= 300:
        period_type = PeriodType.YTD
    else:
        return None
    return PeriodIdentity(
        start=occurrence.period_start,
        end=occurrence.period_end,
        period_type=period_type,
        fiscal_year=occurrence.fiscal_year,
        fiscal_quarter=fiscal_quarter,
    )


def _point_period(occurrence: OfficialFinancialOccurrence) -> PeriodIdentity | None:
    if occurrence.period_end is None or occurrence.fiscal_year is None:
        return None
    fiscal_quarter = _fiscal_quarter(occurrence.fiscal_period)
    if fiscal_quarter is None:
        return None
    return PeriodIdentity(
        start=occurrence.period_end,
        end=occurrence.period_end,
        period_type=PeriodType.POINT_IN_TIME,
        fiscal_year=occurrence.fiscal_year,
        fiscal_quarter=fiscal_quarter,
    )


def _occurrence_id(occurrence: OfficialFinancialOccurrence) -> str:
    payload = "|".join(
        (
            occurrence.source_provider,
            occurrence.issuer_id,
            occurrence.source_document_id or "",
            occurrence.semantic,
            occurrence.period_start.isoformat() if occurrence.period_start else "",
            occurrence.period_end.isoformat() if occurrence.period_end else "",
            occurrence.unit or "",
            occurrence.frame or "",
            occurrence.source_column or "",
        )
    )
    return f"working-capital-occurrence:{hashlib.sha256(payload.encode()).hexdigest()[:24]}"


def _fact_id(
    occurrence: OfficialFinancialOccurrence,
    entry: SemanticRegistryEntry,
    period: PeriodIdentity,
) -> str:
    payload = "|".join(
        (
            CONTRACT_VERSION,
            occurrence.issuer_id,
            entry.metric.value,
            period.start.isoformat(),
            period.end.isoformat(),
            period.period_type.value,
            occurrence.entity_scope or "",
            occurrence.statement_basis or "",
            occurrence.currency or "",
            _occurrence_id(occurrence),
        )
    )
    return f"working-capital-reported:{hashlib.sha256(payload.encode()).hexdigest()[:24]}"


def _canonicalize_occurrence(
    occurrence: OfficialFinancialOccurrence,
    *,
    as_of_date: date,
) -> tuple[FinancialFact | None, str | None]:
    entry = REGISTRY_BY_SEMANTIC.get(occurrence.semantic)
    if entry is None:
        return None, "semantic_not_registered"
    if occurrence.source_document_type not in FORMAL_FORMS | {"OpenDART"}:
        return None, "formal_filing_required"
    if occurrence.source_document_id is None:
        return None, "source_document_id_missing"
    if occurrence.filing_date is None or occurrence.filing_date > as_of_date:
        return None, "filing_date_unavailable_or_after_as_of"
    if occurrence.currency is None or occurrence.unit is None:
        return None, "currency_or_unit_missing"
    if occurrence.entity_scope is None or occurrence.statement_basis is None:
        return None, "entity_or_statement_basis_missing"
    if occurrence.raw_payload_sha256 is None or len(occurrence.raw_payload_sha256) != 64:
        return None, "raw_payload_sha256_missing"
    period = (
        _point_period(occurrence)
        if entry.fact_kind == FactKind.BALANCE
        else _flow_period(occurrence)
    )
    if period is None:
        return None, "period_context_unresolved"
    if entry.fact_kind == FactKind.BALANCE and occurrence.value < 0:
        return None, "negative_balance_requires_source_review"
    fact = FinancialFact(
        fact_id=_fact_id(occurrence, entry, period),
        issuer_id=occurrence.issuer_id,
        metric=entry.metric,
        value=occurrence.value,
        currency=occurrence.currency,
        unit=occurrence.unit,
        period=period,
        entity_scope=occurrence.entity_scope,
        statement_basis=occurrence.statement_basis,
        reported_or_derived="reported",
        source_provider=occurrence.source_provider,
        source_document_id=occurrence.source_document_id,
        filing_date=occurrence.filing_date,
        source_occurrence_id=_occurrence_id(occurrence),
        raw_payload_sha256=occurrence.raw_payload_sha256,
        semantic_mapping=occurrence.semantic,
        fact_type=FactType.REPORTED,
        source_document_type=occurrence.source_document_type,
        source_semantic=occurrence.semantic,
        source_reported_value=occurrence.value,
        source_reported_unit=occurrence.unit,
        source_sign=(
            "nonnegative_balance"
            if entry.fact_kind == FactKind.BALANCE
            else "economic_signed_amount"
        ),
        normalization_transform="identity_reported_amount",
        quality="REPORTED_VERIFIED",
        eligibility=EligibilityStatus.ELIGIBLE,
        cautions=(entry.semantic_scope,),
        restatement_policy_id=RESTATEMENT_POLICY_ID,
        as_of_date=as_of_date,
        source_available_at=occurrence.filing_date,
        balance_scope=entry.balance_scope,
        net_gross_scope=entry.net_gross_scope,
    )
    return fact, None


def extract_sec_occurrences(
    payload: Mapping[str, object],
    *,
    raw_payload_sha256: str,
) -> tuple[OfficialFinancialOccurrence, ...]:
    cik = str(payload.get("cik") or "").strip().zfill(10)
    if not cik.strip("0"):
        return ()
    facts = payload.get("facts")
    if not isinstance(facts, Mapping):
        return ()
    output: list[OfficialFinancialOccurrence] = []
    for entry in SEC_SEMANTIC_REGISTRY:
        namespace = facts.get(entry.namespace)
        if not isinstance(namespace, Mapping):
            continue
        concept = namespace.get(entry.tag)
        if not isinstance(concept, Mapping):
            continue
        units = concept.get("units")
        if not isinstance(units, Mapping):
            continue
        for source_unit, rows in units.items():
            if not isinstance(rows, list):
                continue
            for row in rows:
                if not isinstance(row, Mapping) or row.get("form") not in FORMAL_FORMS:
                    continue
                value = _parse_decimal(row.get("val"))
                if value is None:
                    continue
                unit = str(source_unit)
                output.append(
                    OfficialFinancialOccurrence(
                        issuer_id=f"sec:{cik}",
                        value=value,
                        currency=_currency_from_unit(unit),
                        unit=unit,
                        period_start=_parse_date(row.get("start")),
                        period_end=_parse_date(row.get("end")),
                        fiscal_year=(
                            int(str(row["fy"]))
                            if str(row.get("fy") or "").isdigit()
                            else None
                        ),
                        fiscal_period=str(row.get("fp")) if row.get("fp") else None,
                        source_provider="sec_edgar_companyfacts",
                        source_document_id=(
                            str(row.get("accn")) if row.get("accn") else None
                        ),
                        source_document_type=(
                            str(row.get("form")) if row.get("form") else None
                        ),
                        filing_date=_parse_date(row.get("filed")),
                        namespace=entry.namespace,
                        tag=entry.tag,
                        raw_payload_sha256=raw_payload_sha256,
                        entity_scope="issuer_level",
                        statement_basis="issuer_reported",
                        frame=str(row.get("frame")) if row.get("frame") else None,
                        source_column="val",
                    )
                )
    return tuple(output)


def _economic_key(occurrence: OfficialFinancialOccurrence) -> tuple[object, ...]:
    return (
        occurrence.issuer_id,
        occurrence.semantic,
        occurrence.period_start,
        occurrence.period_end,
        occurrence.unit,
    )


def canonicalize_occurrences(
    occurrences: Iterable[OfficialFinancialOccurrence],
    *,
    as_of_date: date,
) -> WorkingCapitalBatch:
    values = [
        item
        for item in occurrences
        if item.filing_date is not None and item.filing_date <= as_of_date
    ]
    grouped: dict[tuple[object, ...], list[OfficialFinancialOccurrence]] = {}
    for occurrence in values:
        grouped.setdefault(_economic_key(occurrence), []).append(occurrence)
    facts: list[FinancialFact] = []
    denials: list[dict[str, str]] = []
    duplicates = 0
    conflicts = 0
    for group in grouped.values():
        ordered = sorted(
            group,
            key=lambda item: (
                item.filing_date or date.min,
                item.source_document_id or "",
            ),
        )
        entry = REGISTRY_BY_SEMANTIC.get(ordered[0].semantic)
        context_candidates = [
            item
            for item in ordered
            if item.fiscal_year is not None and item.fiscal_period is not None
        ]
        if entry and entry.fact_kind == FactKind.BALANCE:
            framed = [item for item in context_candidates if item.frame]
            annual = [
                item
                for item in context_candidates
                if item.source_document_type in ANNUAL_FORMS
                and item.fiscal_period == "FY"
            ]
            context_candidates = framed or annual or context_candidates
        context = min(
            context_candidates or ordered,
            key=lambda item: (
                item.filing_date or date.max,
                item.source_document_id or "",
            ),
        )
        latest_date = max(item.filing_date or date.min for item in ordered)
        latest = [item for item in ordered if item.filing_date == latest_date]
        latest_document = max(item.source_document_id or "" for item in latest)
        authoritative = [
            item for item in latest if (item.source_document_id or "") == latest_document
        ]
        distinct_values = {item.value for item in authoritative}
        if len(distinct_values) != 1:
            conflicts += 1
            denials.append(
                {
                    "source_semantic": authoritative[0].semantic,
                    "source_document_id": latest_document,
                    "reason": "same_occurrence_value_conflict",
                }
            )
            continue
        duplicates += len(authoritative) - 1
        selected = replace(
            authoritative[0],
            fiscal_year=context.fiscal_year,
            fiscal_period=context.fiscal_period,
        )
        fact, reason = _canonicalize_occurrence(selected, as_of_date=as_of_date)
        if fact is None:
            denials.append(
                {
                    "source_semantic": selected.semantic,
                    "source_document_id": selected.source_document_id or "",
                    "reason": reason or "canonicalization_blocked",
                }
            )
        else:
            facts.append(fact)
    facts.sort(
        key=lambda item: (
            item.issuer_id,
            item.metric.value,
            item.period.end,
            item.semantic_mapping,
            item.filing_date,
            item.fact_id,
        )
    )
    return WorkingCapitalBatch(
        facts=tuple(facts),
        denials=tuple(denials),
        extracted_occurrences=len(values),
        exact_duplicates_suppressed=duplicates,
        conflicts=conflicts,
    )


def build_sec_working_capital_batch(
    payload: Mapping[str, object],
    *,
    raw_payload_sha256: str,
    as_of_date: date,
) -> WorkingCapitalBatch:
    return canonicalize_occurrences(
        extract_sec_occurrences(payload, raw_payload_sha256=raw_payload_sha256),
        as_of_date=as_of_date,
    )


def _registry_priority(fact: FinancialFact) -> int:
    entry = REGISTRY_BY_SEMANTIC.get(fact.semantic_mapping)
    return entry.priority if entry else 0


def _same_fact_basis(left: FinancialFact, right: FinancialFact) -> bool:
    return all(
        getattr(left, field_name) == getattr(right, field_name)
        for field_name in (
            "metric",
            "semantic_mapping",
            "currency",
            "unit",
            "entity_scope",
            "statement_basis",
            "balance_scope",
            "net_gross_scope",
        )
    )


def _prior_year_comparable(left: FinancialFact, right: FinancialFact) -> bool:
    date_gap = (left.period.end - right.period.end).days
    return bool(
        left.period.period_type == PeriodType.POINT_IN_TIME
        and right.period.period_type == PeriodType.POINT_IN_TIME
        and left.period.fiscal_quarter is not None
        and left.period.fiscal_quarter == right.period.fiscal_quarter
        and left.period.fiscal_year == right.period.fiscal_year + 1
        and left.period.end > right.period.end
        and abs(date_gap - 365) <= 14
        and _same_fact_basis(left, right)
    )


def select_latest_comparable_balance(
    facts: Iterable[FinancialFact],
    *,
    metrics: Sequence[Metric],
) -> ComparableSelection:
    candidates = [
        fact
        for fact in facts
        if fact.metric in metrics
        and fact.period.period_type == PeriodType.POINT_IN_TIME
        and fact.eligibility == EligibilityStatus.ELIGIBLE
    ]
    if not candidates:
        return ComparableSelection(
            EligibilityStatus.BLOCKED, None, None, ("current_balance_missing",)
        )
    latest_date = max(item.period.end for item in candidates)
    current_candidates = sorted(
        (item for item in candidates if item.period.end == latest_date),
        key=lambda item: (
            _registry_priority(item),
            item.filing_date,
            item.fact_id,
        ),
        reverse=True,
    )
    for current in current_candidates:
        prior_candidates = [
            item for item in candidates if _prior_year_comparable(current, item)
        ]
        if prior_candidates:
            prior = max(
                prior_candidates,
                key=lambda item: (item.filing_date, item.fact_id),
            )
            return ComparableSelection(EligibilityStatus.ELIGIBLE, current, prior)
    return ComparableSelection(
        EligibilityStatus.PARTIAL,
        current_candidates[0],
        None,
        ("prior_year_comparable_balance_missing",),
    )


def derive_comparable_movement(
    selection: ComparableSelection,
) -> ComparableMovement:
    current = selection.current
    prior = selection.prior
    if current is None or prior is None:
        return ComparableMovement(
            selection.status,
            current.fact_id if current else None,
            None,
            None,
            None,
            None,
            selection.reasons or ("comparable_balance_missing",),
        )
    if not _prior_year_comparable(current, prior):
        return ComparableMovement(
            EligibilityStatus.BLOCKED,
            current.fact_id,
            prior.fact_id,
            None,
            None,
            None,
            ("prior_year_comparability_failed",),
        )
    delta = current.value - prior.value
    direction = (
        RelationType.BALANCE_INCREASED
        if delta > 0
        else RelationType.BALANCE_DECREASED
        if delta < 0
        else RelationType.BALANCE_UNCHANGED
    )
    if prior.value <= 0:
        return ComparableMovement(
            EligibilityStatus.PARTIAL,
            current.fact_id,
            prior.fact_id,
            delta,
            None,
            direction,
            ("non_positive_prior_denominator",),
        )
    return ComparableMovement(
        EligibilityStatus.ELIGIBLE,
        current.fact_id,
        prior.fact_id,
        delta,
        (delta / prior.value) * Decimal(100),
        direction,
    )


def _growth_for_selection(selection: ComparableSelection) -> Decimal | None:
    current = selection.current
    prior = selection.prior
    if current is None or prior is None or prior.value <= 0:
        return None
    if current.period.period_type == PeriodType.POINT_IN_TIME:
        if not _prior_year_comparable(current, prior):
            return None
    elif not _flow_pair_compatible(current, prior):
        return None
    return ((current.value - prior.value) / prior.value) * Decimal(100)


def _flow_pair_compatible(current: FinancialFact, prior: FinancialFact) -> bool:
    if not _same_fact_basis(current, prior):
        return False
    if current.period.period_type != prior.period.period_type:
        return False
    if current.period.period_type == PeriodType.POINT_IN_TIME:
        return False
    if current.period.fiscal_quarter != prior.period.fiscal_quarter:
        return False
    if current.period.fiscal_year != prior.period.fiscal_year + 1:
        return False
    return abs(current.period.duration_days - prior.period.duration_days) <= 2


def select_aligned_flow_pair(
    facts: Iterable[FinancialFact],
    *,
    metric: Metric,
    balances: ComparableSelection,
) -> ComparableSelection:
    if balances.current is None or balances.prior is None:
        return ComparableSelection(
            EligibilityStatus.BLOCKED,
            None,
            None,
            ("comparable_balance_pair_required",),
        )
    current_balance = balances.current
    prior_balance = balances.prior
    candidates = [
        fact
        for fact in facts
        if fact.metric == metric
        and fact.period.period_type != PeriodType.POINT_IN_TIME
        and fact.eligibility == EligibilityStatus.ELIGIBLE
    ]
    period_preference = {
        PeriodType.FY: 3,
        PeriodType.YTD: 2,
        PeriodType.QTD: 1,
    }
    current_candidates = sorted(
        (
            item
            for item in candidates
            if item.period.end == current_balance.period.end
            and item.period.fiscal_quarter
            == current_balance.period.fiscal_quarter
            and item.currency == current_balance.currency
            and item.unit == current_balance.unit
            and item.entity_scope == current_balance.entity_scope
            and item.statement_basis == current_balance.statement_basis
        ),
        key=lambda item: (
            period_preference.get(item.period.period_type, 0),
            _registry_priority(item),
            item.fact_id,
        ),
        reverse=True,
    )
    for current in current_candidates:
        prior_candidates = [
            item
            for item in candidates
            if item.period.end == prior_balance.period.end
            and _flow_pair_compatible(current, item)
        ]
        if prior_candidates:
            prior = max(
                prior_candidates,
                key=lambda item: (_registry_priority(item), item.fact_id),
            )
            return ComparableSelection(EligibilityStatus.ELIGIBLE, current, prior)
    return ComparableSelection(
        EligibilityStatus.BLOCKED,
        current_candidates[0] if current_candidates else None,
        None,
        ("compatible_filing_period_flow_pair_missing",),
    )


def _relation_type(
    balance_metric: Metric,
    flow_metric: Metric,
    difference: Decimal,
) -> RelationType | None:
    suffix = "GT" if difference > 0 else "LT" if difference < 0 else "EQ"
    mapping = {
        (Metric.TRADE_AR, Metric.REVENUE, "GT"): RelationType.AR_GROWTH_GT_REVENUE_GROWTH,
        (Metric.TRADE_AR, Metric.REVENUE, "LT"): RelationType.AR_GROWTH_LT_REVENUE_GROWTH,
        (Metric.TRADE_AR, Metric.REVENUE, "EQ"): RelationType.AR_GROWTH_EQ_REVENUE_GROWTH,
        (Metric.BROAD_AR, Metric.REVENUE, "GT"): RelationType.AR_GROWTH_GT_REVENUE_GROWTH,
        (Metric.BROAD_AR, Metric.REVENUE, "LT"): RelationType.AR_GROWTH_LT_REVENUE_GROWTH,
        (Metric.BROAD_AR, Metric.REVENUE, "EQ"): RelationType.AR_GROWTH_EQ_REVENUE_GROWTH,
        (Metric.INVENTORY, Metric.REVENUE, "GT"): RelationType.INVENTORY_GROWTH_GT_REVENUE_GROWTH,
        (Metric.INVENTORY, Metric.REVENUE, "LT"): RelationType.INVENTORY_GROWTH_LT_REVENUE_GROWTH,
        (Metric.INVENTORY, Metric.REVENUE, "EQ"): RelationType.INVENTORY_GROWTH_EQ_REVENUE_GROWTH,
        (Metric.INVENTORY, Metric.COGS, "GT"): RelationType.INVENTORY_GROWTH_GT_COGS_GROWTH,
        (Metric.INVENTORY, Metric.COGS, "LT"): RelationType.INVENTORY_GROWTH_LT_COGS_GROWTH,
        (Metric.INVENTORY, Metric.COGS, "EQ"): RelationType.INVENTORY_GROWTH_EQ_COGS_GROWTH,
        (Metric.TRADE_AP, Metric.COGS, "GT"): RelationType.AP_GROWTH_GT_COGS_GROWTH,
        (Metric.TRADE_AP, Metric.COGS, "LT"): RelationType.AP_GROWTH_LT_COGS_GROWTH,
        (Metric.TRADE_AP, Metric.COGS, "EQ"): RelationType.AP_GROWTH_EQ_COGS_GROWTH,
        (Metric.BROAD_AP, Metric.COGS, "GT"): RelationType.AP_GROWTH_GT_COGS_GROWTH,
        (Metric.BROAD_AP, Metric.COGS, "LT"): RelationType.AP_GROWTH_LT_COGS_GROWTH,
        (Metric.BROAD_AP, Metric.COGS, "EQ"): RelationType.AP_GROWTH_EQ_COGS_GROWTH,
    }
    return mapping.get((balance_metric, flow_metric, suffix))


def derive_cross_growth_relation(
    balances: ComparableSelection,
    flows: ComparableSelection,
) -> CrossGrowthRelation:
    balance_growth = _growth_for_selection(balances)
    flow_growth = _growth_for_selection(flows)
    if (
        balances.current is None
        or balances.prior is None
        or flows.current is None
        or flows.prior is None
        or balance_growth is None
        or flow_growth is None
    ):
        return CrossGrowthRelation(
            EligibilityStatus.BLOCKED,
            None,
            None,
            None,
            reasons=("safe_balance_and_flow_growth_required",),
        )
    if flows.current.value <= 0 or flows.prior.value <= 0:
        return CrossGrowthRelation(
            EligibilityStatus.BLOCKED,
            None,
            None,
            None,
            reasons=("non_positive_flow_denominator",),
        )
    if any(
        (
            balances.current.currency != flows.current.currency,
            balances.current.unit != flows.current.unit,
            balances.current.entity_scope != flows.current.entity_scope,
            balances.current.statement_basis != flows.current.statement_basis,
            balances.current.restatement_policy_id
            != flows.current.restatement_policy_id,
            balances.prior.restatement_policy_id != flows.prior.restatement_policy_id,
        )
    ):
        return CrossGrowthRelation(
            EligibilityStatus.BLOCKED,
            None,
            None,
            None,
            reasons=("balance_flow_basis_or_restatement_policy_mismatch",),
        )
    difference = balance_growth - flow_growth
    relation_type = _relation_type(
        balances.current.metric,
        flows.current.metric,
        difference,
    )
    if relation_type is None:
        return CrossGrowthRelation(
            EligibilityStatus.BLOCKED,
            None,
            None,
            None,
            reasons=("unsupported_cross_growth_relation",),
        )
    input_fact_ids = (
        balances.current.fact_id,
        balances.prior.fact_id,
        flows.current.fact_id,
        flows.prior.fact_id,
    )
    formula = "BALANCE_YOY_PCT_MINUS_FLOW_YOY_PCT"
    payload = "|".join((CONTRACT_VERSION, relation_type.value, *input_fact_ids))
    return CrossGrowthRelation(
        EligibilityStatus.ELIGIBLE,
        f"working-capital-relation:{hashlib.sha256(payload.encode()).hexdigest()[:24]}",
        relation_type,
        difference,
        input_fact_ids,
        formula,
    )


OPENDART_TAGS = {
    "ifrs-full_inventories": REGISTRY_BY_SEMANTIC["ifrs-full:Inventories"],
    "ifrs-full_tradereceivables": REGISTRY_BY_SEMANTIC[
        "ifrs-full:TradeReceivables"
    ],
    "ifrs-full_currenttradereceivables": REGISTRY_BY_SEMANTIC[
        "ifrs-full:CurrentTradeReceivables"
    ],
    "ifrs-full_tradeandothercurrentreceivables": REGISTRY_BY_SEMANTIC[
        "ifrs-full:TradeAndOtherCurrentReceivables"
    ],
    "ifrs-full_tradeandotherreceivables": REGISTRY_BY_SEMANTIC[
        "ifrs-full:TradeAndOtherReceivables"
    ],
    "ifrs-full_tradepayables": REGISTRY_BY_SEMANTIC["ifrs-full:TradePayables"],
    "ifrs-full_tradeandothercurrentpayablestotradesuppliers": REGISTRY_BY_SEMANTIC[
        "ifrs-full:TradeAndOtherCurrentPayablesToTradeSuppliers"
    ],
    "ifrs-full_tradeandothercurrentpayables": REGISTRY_BY_SEMANTIC[
        "ifrs-full:TradeAndOtherCurrentPayables"
    ],
    "ifrs-full_tradeandotherpayables": REGISTRY_BY_SEMANTIC[
        "ifrs-full:TradeAndOtherPayables"
    ],
    "ifrs-full_revenue": REGISTRY_BY_SEMANTIC["ifrs-full:Revenue"],
    "ifrs-full_costofsales": REGISTRY_BY_SEMANTIC["ifrs-full:CostOfSales"],
}


def _opendart_period(
    *,
    business_year: int,
    report_code: str,
    fact_kind: FactKind,
    source_column: str,
) -> tuple[date | None, date | None, str | None]:
    month = {"11013": 3, "11012": 6, "11014": 9, "11011": 12}.get(
        report_code
    )
    fiscal_period = {
        "11013": "Q1",
        "11012": "Q2",
        "11014": "Q3",
        "11011": "FY",
    }.get(report_code)
    if month is None or fiscal_period is None:
        return None, None, None
    day = 31 if month in {3, 12} else 30
    end = date(business_year, month, day)
    if fact_kind == FactKind.BALANCE:
        return None, end, fiscal_period
    if source_column == "thstrm_add_amount":
        return date(business_year, 1, 1), end, fiscal_period
    if source_column == "thstrm_amount":
        start_month = month - 2
        return date(business_year, start_month, 1), end, fiscal_period
    return None, None, None


def extract_opendart_occurrences(
    rows: Iterable[Mapping[str, object]],
    *,
    issuer_id: str,
    business_year: int,
    report_code: str,
    filing_date: date,
    source_document_id: str,
    raw_payload_sha256: str,
    requested_basis: str,
) -> tuple[OfficialFinancialOccurrence, ...]:
    basis = requested_basis.upper()
    if basis not in {"CFS", "OFS"}:
        return ()
    statement_basis = "consolidated" if basis == "CFS" else "separate"
    output: list[OfficialFinancialOccurrence] = []
    for row in rows:
        account_id = str(row.get("account_id") or "").lower()
        entry = OPENDART_TAGS.get(account_id)
        if entry is None:
            continue
        row_basis = str(row.get("fs_div") or basis).upper()
        if row_basis != basis:
            continue
        statement_type = str(row.get("sj_div") or "").upper()
        if entry.fact_kind == FactKind.BALANCE and statement_type != "BS":
            continue
        if entry.fact_kind == FactKind.FLOW and statement_type not in {"IS", "CIS"}:
            continue
        source_column = (
            "thstrm_amount"
            if entry.fact_kind == FactKind.BALANCE
            else "thstrm_add_amount"
            if report_code in {"11012", "11014"}
            else "thstrm_amount"
        )
        value = _parse_decimal(row.get(source_column))
        if value is None:
            continue
        start, end, fiscal_period = _opendart_period(
            business_year=business_year,
            report_code=report_code,
            fact_kind=entry.fact_kind,
            source_column=source_column,
        )
        output.append(
            OfficialFinancialOccurrence(
                issuer_id=issuer_id,
                value=value,
                currency=str(row.get("currency") or "").upper() or None,
                unit=str(row.get("currency") or "").upper() or None,
                period_start=start,
                period_end=end,
                fiscal_year=business_year,
                fiscal_period=fiscal_period,
                source_provider="opendart",
                source_document_id=source_document_id,
                source_document_type="OpenDART",
                filing_date=filing_date,
                namespace=entry.namespace,
                tag=entry.tag,
                raw_payload_sha256=raw_payload_sha256,
                entity_scope="issuer_level",
                statement_basis=statement_basis,
                frame=None,
                source_column=source_column,
            )
        )
    return tuple(output)


INDUSTRY_APPLICABILITY = {
    "memory_semiconductor": {
        "inventory": "PRIMARY",
        "ar": "SECONDARY",
        "ap": "SECONDARY",
        "ar_vs_revenue": "SECONDARY",
        "inventory_vs_revenue": "PRIMARY",
        "inventory_vs_cogs": "PRIMARY",
        "ap_vs_cogs": "SECONDARY",
    },
    "automotive": {
        "inventory": "PRIMARY",
        "ar": "SECONDARY",
        "ap": "SECONDARY",
        "ar_vs_revenue": "SECONDARY",
        "inventory_vs_revenue": "PRIMARY",
        "inventory_vs_cogs": "PRIMARY",
        "ap_vs_cogs": "SECONDARY",
    },
    "steel_materials": {
        "inventory": "PRIMARY",
        "ar": "PRIMARY",
        "ap": "SECONDARY",
        "ar_vs_revenue": "PRIMARY",
        "inventory_vs_revenue": "PRIMARY",
        "inventory_vs_cogs": "PRIMARY",
        "ap_vs_cogs": "SECONDARY",
    },
    "industrial_epc": {
        "inventory": "PRIMARY",
        "ar": "PRIMARY",
        "ap": "SECONDARY",
        "ar_vs_revenue": "PRIMARY",
        "inventory_vs_revenue": "SECONDARY",
        "inventory_vs_cogs": "SECONDARY",
        "ap_vs_cogs": "SECONDARY",
    },
    "aerospace_epc": {
        "inventory": "SECONDARY",
        "ar": "SECONDARY",
        "ap": "SECONDARY",
        "ar_vs_revenue": "SECONDARY",
        "inventory_vs_revenue": "SECONDARY",
        "inventory_vs_cogs": "CONTEXT_ONLY",
        "ap_vs_cogs": "CONTEXT_ONLY",
    },
    "transport_logistics": {
        "inventory": "CONTEXT_ONLY",
        "ar": "PRIMARY",
        "ap": "SECONDARY",
        "ar_vs_revenue": "PRIMARY",
        "inventory_vs_revenue": "CONTEXT_ONLY",
        "inventory_vs_cogs": "CONTEXT_ONLY",
        "ap_vs_cogs": "SECONDARY",
    },
    "cloud_platform_software": {
        "inventory": "CONTEXT_ONLY",
        "ar": "SECONDARY",
        "ap": "CONTEXT_ONLY",
        "ar_vs_revenue": "SECONDARY",
        "inventory_vs_revenue": "CONTEXT_ONLY",
        "inventory_vs_cogs": "CONTEXT_ONLY",
        "ap_vs_cogs": "CONTEXT_ONLY",
    },
    "hpc_data_center": {
        "inventory": "CONTEXT_ONLY",
        "ar": "SECONDARY",
        "ap": "SECONDARY",
        "ar_vs_revenue": "SECONDARY",
        "inventory_vs_revenue": "CONTEXT_ONLY",
        "inventory_vs_cogs": "CONTEXT_ONLY",
        "ap_vs_cogs": "CONTEXT_ONLY",
    },
    "biotech": {
        "inventory": "CONTEXT_ONLY",
        "ar": "CONTEXT_ONLY",
        "ap": "CONTEXT_ONLY",
        "ar_vs_revenue": "NOT_APPLICABLE",
        "inventory_vs_revenue": "NOT_APPLICABLE",
        "inventory_vs_cogs": "NOT_APPLICABLE",
        "ap_vs_cogs": "NOT_APPLICABLE",
    },
    "insurance_reinsurance": {
        key: "NOT_APPLICABLE"
        for key in (
            "inventory",
            "ar",
            "ap",
            "ar_vs_revenue",
            "inventory_vs_revenue",
            "inventory_vs_cogs",
            "ap_vs_cogs",
        )
    },
    "special_financial_like": {
        key: "CONTEXT_ONLY"
        for key in (
            "inventory",
            "ar",
            "ap",
            "ar_vs_revenue",
            "inventory_vs_revenue",
            "inventory_vs_cogs",
            "ap_vs_cogs",
        )
    },
    "general_non_financial": {
        "inventory": "SECONDARY",
        "ar": "SECONDARY",
        "ap": "SECONDARY",
        "ar_vs_revenue": "SECONDARY",
        "inventory_vs_revenue": "SECONDARY",
        "inventory_vs_cogs": "SECONDARY",
        "ap_vs_cogs": "SECONDARY",
    },
}


def industry_applicability(industry: str) -> Mapping[str, str]:
    return INDUSTRY_APPLICABILITY.get(
        industry, INDUSTRY_APPLICABILITY["general_non_financial"]
    )
