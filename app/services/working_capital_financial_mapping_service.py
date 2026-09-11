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
from app.services.financial_validation import UNIT_MULTIPLIERS
from app.services.opendart_financial_recovery_service import Filing
from app.services.opendart_xbrl_service import XbrlFact, reconcile_xbrl_instant_fact
from app.services.working_capital_evidence_service import OfficialFinancialOccurrence


CONTRACT_VERSION = "inventory-receivables-working-capital-v1"
BALANCE_DELTA_FORMULA = "balance_absolute_delta"
NO_WORKING_CAPITAL_FORMULA_POLICY = "NO_UNIVERSAL_OPERATING_WORKING_CAPITAL"
CONTRACT_ASSET_POLICY = "SEPARATE_WORKING_CAPITAL_CONTEXT"
CONTRACT_LIABILITY_POLICY = "SEPARATE_WORKING_CAPITAL_CONTEXT"

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
    "11011",
    "11012",
    "11013",
    "11014",
}

_FISCAL_PERIOD_BY_REPORT_CODE = {
    "11013": "Q1",
    "11012": "Q2",
    "11014": "Q3",
    "11011": "FY",
}


class ComponentRole(StrEnum):
    INVENTORY_AGGREGATE = "INVENTORY_AGGREGATE"
    INVENTORY_COMPONENT = "INVENTORY_COMPONENT"
    TRADE_RECEIVABLE = "TRADE_RECEIVABLE"
    BROAD_RECEIVABLE_CONTEXT = "BROAD_RECEIVABLE_CONTEXT"
    TRADE_PAYABLE = "TRADE_PAYABLE"
    BROAD_PAYABLE_CONTEXT = "BROAD_PAYABLE_CONTEXT"
    CURRENT_BALANCE_CONTEXT = "CURRENT_BALANCE_CONTEXT"
    CONTRACT_CONTEXT = "CONTRACT_CONTEXT"


class SectorRoute(StrEnum):
    GENERIC_OPERATING_COMPANY = "GENERIC_OPERATING_COMPANY"
    CONTEXT_ONLY = "CONTEXT_ONLY"
    SECTOR_FRAMEWORK_REQUIRED = "SECTOR_FRAMEWORK_REQUIRED"


class ComparisonKind(StrEnum):
    PRIOR_YEAR_COMPARABLE = "prior_year_comparable"
    PRIOR_YEAR_END = "prior_year_end"


@dataclass(frozen=True)
class WorkingCapitalRegistryEntry:
    metric: Metric
    namespace: str
    tag: str
    role: ComponentRole
    balance_scope: str
    net_gross_scope: str
    priority: int = 100

    @property
    def semantic(self) -> str:
        return f"{self.namespace}:{self.tag}"


WORKING_CAPITAL_SEMANTIC_REGISTRY = (
    WorkingCapitalRegistryEntry(
        Metric.INVENTORY,
        "us-gaap",
        "InventoryNet",
        ComponentRole.INVENTORY_AGGREGATE,
        "inventory_total",
        "net",
    ),
    WorkingCapitalRegistryEntry(
        Metric.INVENTORY,
        "ifrs-full",
        "Inventories",
        ComponentRole.INVENTORY_AGGREGATE,
        "inventory_total",
        "issuer_reported",
    ),
    WorkingCapitalRegistryEntry(
        Metric.INVENTORY,
        "ifrs-full",
        "InventoriesTotal",
        ComponentRole.INVENTORY_AGGREGATE,
        "inventory_total",
        "issuer_reported",
        95,
    ),
    WorkingCapitalRegistryEntry(
        Metric.INVENTORY_COMPONENT,
        "us-gaap",
        "InventoryRawMaterials",
        ComponentRole.INVENTORY_COMPONENT,
        "inventory_raw_materials",
        "issuer_reported",
    ),
    WorkingCapitalRegistryEntry(
        Metric.INVENTORY_COMPONENT,
        "us-gaap",
        "InventoryWorkInProcess",
        ComponentRole.INVENTORY_COMPONENT,
        "inventory_work_in_process",
        "issuer_reported",
    ),
    WorkingCapitalRegistryEntry(
        Metric.INVENTORY_COMPONENT,
        "us-gaap",
        "InventoryFinishedGoods",
        ComponentRole.INVENTORY_COMPONENT,
        "inventory_finished_goods",
        "issuer_reported",
    ),
    WorkingCapitalRegistryEntry(
        Metric.INVENTORY_COMPONENT,
        "ifrs-full",
        "RawMaterialsAndConsumables",
        ComponentRole.INVENTORY_COMPONENT,
        "inventory_raw_materials",
        "issuer_reported",
    ),
    WorkingCapitalRegistryEntry(
        Metric.INVENTORY_COMPONENT,
        "ifrs-full",
        "WorkInProgress",
        ComponentRole.INVENTORY_COMPONENT,
        "inventory_work_in_process",
        "issuer_reported",
    ),
    WorkingCapitalRegistryEntry(
        Metric.INVENTORY_COMPONENT,
        "ifrs-full",
        "FinishedGoods",
        ComponentRole.INVENTORY_COMPONENT,
        "inventory_finished_goods",
        "issuer_reported",
    ),
    WorkingCapitalRegistryEntry(
        Metric.TRADE_AR,
        "us-gaap",
        "AccountsReceivableTradeCurrent",
        ComponentRole.TRADE_RECEIVABLE,
        "trade_receivables_current",
        "issuer_reported",
    ),
    WorkingCapitalRegistryEntry(
        Metric.TRADE_AR,
        "ifrs-full",
        "CurrentTradeReceivables",
        ComponentRole.TRADE_RECEIVABLE,
        "trade_receivables_current",
        "issuer_reported",
    ),
    WorkingCapitalRegistryEntry(
        Metric.TRADE_AR,
        "ifrs-full",
        "NoncurrentTradeReceivables",
        ComponentRole.TRADE_RECEIVABLE,
        "trade_receivables_noncurrent",
        "issuer_reported",
    ),
    WorkingCapitalRegistryEntry(
        Metric.TRADE_AR,
        "ifrs-full",
        "TradeReceivables",
        ComponentRole.TRADE_RECEIVABLE,
        "trade_receivables_total",
        "issuer_reported",
        105,
    ),
    WorkingCapitalRegistryEntry(
        Metric.BROAD_AR,
        "us-gaap",
        "AccountsReceivableNetCurrent",
        ComponentRole.BROAD_RECEIVABLE_CONTEXT,
        "broad_receivables_current",
        "net",
    ),
    WorkingCapitalRegistryEntry(
        Metric.BROAD_AR,
        "us-gaap",
        "AccountsReceivableNet",
        ComponentRole.BROAD_RECEIVABLE_CONTEXT,
        "broad_receivables_total",
        "net",
    ),
    WorkingCapitalRegistryEntry(
        Metric.BROAD_AR,
        "us-gaap",
        "AccountsReceivableGrossCurrent",
        ComponentRole.BROAD_RECEIVABLE_CONTEXT,
        "broad_receivables_current",
        "gross",
        90,
    ),
    WorkingCapitalRegistryEntry(
        Metric.BROAD_AR,
        "us-gaap",
        "AccountsAndOtherReceivablesNetCurrent",
        ComponentRole.BROAD_RECEIVABLE_CONTEXT,
        "broad_receivables_current",
        "net",
        90,
    ),
    WorkingCapitalRegistryEntry(
        Metric.BROAD_AR,
        "us-gaap",
        "AccountsAndNotesReceivableNet",
        ComponentRole.BROAD_RECEIVABLE_CONTEXT,
        "broad_receivables_total",
        "net",
        85,
    ),
    WorkingCapitalRegistryEntry(
        Metric.BROAD_AR,
        "ifrs-full",
        "TradeAndOtherCurrentReceivables",
        ComponentRole.BROAD_RECEIVABLE_CONTEXT,
        "broad_receivables_current",
        "issuer_reported",
    ),
    WorkingCapitalRegistryEntry(
        Metric.BROAD_AR,
        "ifrs-full",
        "TradeAndOtherReceivables",
        ComponentRole.BROAD_RECEIVABLE_CONTEXT,
        "broad_receivables_total",
        "issuer_reported",
        95,
    ),
    WorkingCapitalRegistryEntry(
        Metric.TRADE_AP,
        "us-gaap",
        "AccountsPayableTradeCurrent",
        ComponentRole.TRADE_PAYABLE,
        "trade_payables_current",
        "issuer_reported",
    ),
    WorkingCapitalRegistryEntry(
        Metric.TRADE_AP,
        "ifrs-full",
        "TradePayables",
        ComponentRole.TRADE_PAYABLE,
        "trade_payables_total",
        "issuer_reported",
        105,
    ),
    WorkingCapitalRegistryEntry(
        Metric.TRADE_AP,
        "ifrs-full",
        "TradeAndOtherCurrentPayablesToTradeSuppliers",
        ComponentRole.TRADE_PAYABLE,
        "trade_payables_current",
        "issuer_reported",
    ),
    WorkingCapitalRegistryEntry(
        Metric.BROAD_AP,
        "us-gaap",
        "AccountsPayableCurrent",
        ComponentRole.BROAD_PAYABLE_CONTEXT,
        "broad_payables_current",
        "issuer_reported",
    ),
    WorkingCapitalRegistryEntry(
        Metric.BROAD_AP,
        "us-gaap",
        "AccountsPayableAndAccruedLiabilitiesCurrent",
        ComponentRole.BROAD_PAYABLE_CONTEXT,
        "broad_payables_current",
        "issuer_reported",
        90,
    ),
    WorkingCapitalRegistryEntry(
        Metric.BROAD_AP,
        "ifrs-full",
        "TradeAndOtherCurrentPayables",
        ComponentRole.BROAD_PAYABLE_CONTEXT,
        "broad_payables_current",
        "issuer_reported",
    ),
    WorkingCapitalRegistryEntry(
        Metric.BROAD_AP,
        "ifrs-full",
        "TradeAndOtherPayables",
        ComponentRole.BROAD_PAYABLE_CONTEXT,
        "broad_payables_total",
        "issuer_reported",
        95,
    ),
    WorkingCapitalRegistryEntry(
        Metric.CURRENT_ASSETS,
        "us-gaap",
        "AssetsCurrent",
        ComponentRole.CURRENT_BALANCE_CONTEXT,
        "current_assets_total",
        "gross",
    ),
    WorkingCapitalRegistryEntry(
        Metric.CURRENT_ASSETS,
        "ifrs-full",
        "CurrentAssets",
        ComponentRole.CURRENT_BALANCE_CONTEXT,
        "current_assets_total",
        "gross",
    ),
    WorkingCapitalRegistryEntry(
        Metric.CURRENT_LIABILITIES,
        "us-gaap",
        "LiabilitiesCurrent",
        ComponentRole.CURRENT_BALANCE_CONTEXT,
        "current_liabilities_total",
        "gross",
    ),
    WorkingCapitalRegistryEntry(
        Metric.CURRENT_LIABILITIES,
        "ifrs-full",
        "CurrentLiabilities",
        ComponentRole.CURRENT_BALANCE_CONTEXT,
        "current_liabilities_total",
        "gross",
    ),
    WorkingCapitalRegistryEntry(
        Metric.CONTRACT_ASSETS,
        "us-gaap",
        "ContractWithCustomerAssetNetCurrent",
        ComponentRole.CONTRACT_CONTEXT,
        "contract_assets_current",
        "net",
    ),
    WorkingCapitalRegistryEntry(
        Metric.CONTRACT_ASSETS,
        "ifrs-full",
        "CurrentContractAssets",
        ComponentRole.CONTRACT_CONTEXT,
        "contract_assets_current",
        "issuer_reported",
    ),
    WorkingCapitalRegistryEntry(
        Metric.CONTRACT_LIABILITIES,
        "us-gaap",
        "ContractWithCustomerLiabilityCurrent",
        ComponentRole.CONTRACT_CONTEXT,
        "contract_liabilities_current",
        "gross",
    ),
    WorkingCapitalRegistryEntry(
        Metric.CONTRACT_LIABILITIES,
        "ifrs-full",
        "CurrentContractLiabilities",
        ComponentRole.CONTRACT_CONTEXT,
        "contract_liabilities_current",
        "gross",
    ),
)

REGISTRY_BY_SEMANTIC = {
    entry.semantic: entry for entry in WORKING_CAPITAL_SEMANTIC_REGISTRY
}

EXCLUDED_SEMANTIC_REASONS = {
    "ifrs-full:OtherCurrentReceivables": "broad_receivable_not_trade",
    "ifrs-full:OtherNoncurrentReceivables": "broad_receivable_not_trade",
    "dart:ShortTermOtherReceivablesNet": "broad_receivable_not_trade",
    "us-gaap:FinancingReceivableExcludingAccruedInterestAfterAllowanceForCreditLossCurrent": (
        "loan_receivable_not_trade"
    ),
    "ifrs-full:LoansReceivable": "loan_receivable_not_trade",
    "ifrs-full:OtherCurrentPayables": "nontrade_payable_not_trade",
    "dart:CurrentNontradePayables": "nontrade_payable_not_trade",
    "ifrs-full:Assets": "total_assets_not_inventory",
    "us-gaap:Assets": "total_assets_not_inventory",
    "ifrs-full:Liabilities": "total_liabilities_not_trade_payables",
    "us-gaap:Liabilities": "total_liabilities_not_trade_payables",
}

_FINANCIAL_SECTOR_FRAMEWORKS = {
    "bank",
    "insurance",
    "reinsurance",
    "financial_institution",
    "bank_or_insurer",
}

_CONTEXT_ONLY_FRAMEWORKS = {
    "asset_light_services",
    "cloud_platform",
    "holding_company",
    "pre_profit_technology",
    "saas",
    "software_platform",
}

_COMPARABLE_METRICS = frozenset(
    {
        Metric.INVENTORY,
        Metric.INVENTORY_COMPONENT,
        Metric.TRADE_AR,
        Metric.BROAD_AR,
        Metric.TRADE_AP,
        Metric.BROAD_AP,
        Metric.CURRENT_ASSETS,
        Metric.CURRENT_LIABILITIES,
        Metric.CONTRACT_ASSETS,
        Metric.CONTRACT_LIABILITIES,
    }
)


@dataclass(frozen=True)
class WorkingCapitalMappingBatch:
    facts: tuple[FinancialFact, ...]
    direct_facts: tuple[FinancialFact, ...]
    derived_facts: tuple[FinancialFact, ...]
    denials: tuple[dict[str, str], ...]
    sector_route: SectorRoute
    source_candidates: int
    extracted_occurrences: int
    exact_duplicates_suppressed: int
    source_conflicts: int
    aggregate_precedence_count: int
    overlap_conflict_count: int
    overlap_blocked_count: int
    gross_net_precedence_count: int


def sector_route(analysis_framework: str) -> SectorRoute:
    normalized = analysis_framework.strip().lower()
    if normalized in _FINANCIAL_SECTOR_FRAMEWORKS:
        return SectorRoute.SECTOR_FRAMEWORK_REQUIRED
    if normalized in _CONTEXT_ONLY_FRAMEWORKS:
        return SectorRoute.CONTEXT_ONLY
    return SectorRoute.GENERIC_OPERATING_COMPANY


def _decimal(value: object) -> Decimal | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        parsed = Decimal(str(value).replace(",", "").strip())
    except (InvalidOperation, ValueError):
        return None
    return parsed if parsed.is_finite() else None


def _date(value: object) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError:
        return None


def _normalized_amount(
    occurrence: OfficialFinancialOccurrence,
) -> tuple[Decimal, str, str] | None:
    if occurrence.unit is None:
        return None
    unit = occurrence.unit.strip()
    normalized_unit = " ".join(unit.lower().split())
    if len(unit) == 3 and unit.isalpha():
        unit_currency = unit.upper()
        multiplier = Decimal(1)
    else:
        definition = UNIT_MULTIPLIERS.get(normalized_unit)
        if definition is None:
            return None
        unit_currency, raw_multiplier = definition
        multiplier = Decimal(str(raw_multiplier))
    currency = str(occurrence.currency or unit_currency).upper()
    if currency != unit_currency:
        return None
    return occurrence.value * multiplier, currency, unit_currency


def _point_period(occurrence: OfficialFinancialOccurrence) -> PeriodIdentity | None:
    if occurrence.period_end is None or occurrence.fiscal_year is None:
        return None
    fiscal_period = occurrence.fiscal_period or ""
    fiscal_quarter = (
        int(fiscal_period[1])
        if fiscal_period in {"Q1", "Q2", "Q3", "Q4"}
        else 4
        if fiscal_period == "FY"
        else None
    )
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
    identity = "|".join(
        (
            CONTRACT_VERSION,
            occurrence.source_provider,
            occurrence.issuer_id,
            occurrence.source_document_id or "",
            occurrence.semantic,
            occurrence.period_end.isoformat() if occurrence.period_end else "",
            occurrence.unit or "",
            occurrence.entity_scope or "",
            occurrence.statement_basis or "",
            occurrence.frame or "",
            occurrence.source_column or "",
        )
    )
    return f"working-capital-occurrence:{hashlib.sha256(identity.encode()).hexdigest()[:24]}"


def _reported_fact_id(
    occurrence: OfficialFinancialOccurrence,
    entry: WorkingCapitalRegistryEntry,
    period: PeriodIdentity,
) -> str:
    identity = "|".join(
        (
            CONTRACT_VERSION,
            occurrence.issuer_id,
            entry.metric.value,
            entry.balance_scope,
            entry.net_gross_scope,
            period.end.isoformat(),
            occurrence.entity_scope or "",
            occurrence.statement_basis or "",
            occurrence.currency or "",
            _occurrence_id(occurrence),
        )
    )
    return f"working-capital-reported:{hashlib.sha256(identity.encode()).hexdigest()[:24]}"


def _denial(
    occurrence: OfficialFinancialOccurrence | None,
    reason: str,
    *,
    metric: str = "working_capital",
) -> dict[str, str]:
    return {
        "metric": metric,
        "source_semantic": occurrence.semantic if occurrence else "",
        "source_document_id": (
            occurrence.source_document_id or "" if occurrence else ""
        ),
        "reason": reason,
    }


def _canonicalize_occurrence(
    occurrence: OfficialFinancialOccurrence,
    *,
    as_of_date: date,
    route: SectorRoute,
) -> tuple[FinancialFact | None, str | None]:
    if route == SectorRoute.SECTOR_FRAMEWORK_REQUIRED:
        return None, "sector_not_applicable"
    if occurrence.semantic in EXCLUDED_SEMANTIC_REASONS:
        return None, EXCLUDED_SEMANTIC_REASONS[occurrence.semantic]
    entry = REGISTRY_BY_SEMANTIC.get(occurrence.semantic)
    if entry is None:
        return None, "unsupported_semantic"
    if occurrence.source_document_type not in FORMAL_FORMS:
        return None, "formal_filing_required"
    if occurrence.source_document_id is None:
        return None, "source_document_id_missing"
    if occurrence.filing_date is None or occurrence.filing_date > as_of_date:
        return None, "filing_date_unavailable_or_after_as_of"
    if occurrence.entity_scope is None or occurrence.statement_basis is None:
        return None, "entity_or_statement_basis_missing"
    if occurrence.raw_payload_sha256 is None or len(occurrence.raw_payload_sha256) != 64:
        return None, "raw_payload_sha256_missing"
    normalized = _normalized_amount(occurrence)
    if normalized is None:
        return None, "currency_or_unit_missing_or_unsupported"
    value, currency, unit = normalized
    if value < 0:
        return None, "negative_balance_requires_source_review"
    period = _point_period(occurrence)
    if period is None:
        return None, "point_in_time_context_unresolved"
    cautions = [entry.role.value.lower()]
    if entry.role in {
        ComponentRole.BROAD_RECEIVABLE_CONTEXT,
        ComponentRole.BROAD_PAYABLE_CONTEXT,
    }:
        cautions.append("broad_balance_not_trade_only")
    if entry.role == ComponentRole.INVENTORY_COMPONENT:
        cautions.append("inventory_component_not_aggregate")
    if entry.role == ComponentRole.CONTRACT_CONTEXT:
        cautions.append("separate_working_capital_context_only")
    if entry.role == ComponentRole.CURRENT_BALANCE_CONTEXT:
        cautions.append("not_operating_working_capital")
    if route == SectorRoute.CONTEXT_ONLY:
        cautions.append("sector_context_only")
    transform = "identity_reported_amount"
    if occurrence.value != value or occurrence.unit != unit:
        transform = (
            f"multiply_source_unit_by_{value / occurrence.value}"
            if occurrence.value
            else "normalize_zero_to_canonical_unit"
        )
    return (
        FinancialFact(
            fact_id=_reported_fact_id(occurrence, entry, period),
            issuer_id=occurrence.issuer_id,
            metric=entry.metric,
            value=value,
            currency=currency,
            unit=unit,
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
            source_sign="nonnegative_balance",
            normalization_transform=transform,
            quality="REPORTED_VERIFIED",
            eligibility=EligibilityStatus.ELIGIBLE,
            cautions=tuple(cautions),
            restatement_policy_id="latest-authoritative-exact-semantic-v1",
            as_of_date=as_of_date,
            source_available_at=occurrence.filing_date,
            balance_scope=entry.balance_scope,
            net_gross_scope=entry.net_gross_scope,
        ),
        None,
    )


def _economic_key(occurrence: OfficialFinancialOccurrence) -> tuple[object, ...]:
    return (
        occurrence.issuer_id,
        occurrence.semantic,
        occurrence.period_end,
        occurrence.unit,
        occurrence.entity_scope,
        occurrence.statement_basis,
        occurrence.source_column,
    )


def _fact_context_key(fact: FinancialFact) -> tuple[object, ...]:
    return (
        fact.issuer_id,
        fact.period,
        fact.currency,
        fact.unit,
        fact.entity_scope,
        fact.statement_basis,
    )


def _apply_overlap_precedence(
    facts: Sequence[FinancialFact],
) -> tuple[list[FinancialFact], list[dict[str, str]], int, int, int, int]:
    selected = list(facts)
    denials: list[dict[str, str]] = []
    aggregate_precedence = 0
    overlap_conflicts = 0
    overlap_blocked = 0
    gross_net_precedence = 0
    contexts = {_fact_context_key(fact) for fact in selected}
    for context in contexts:
        context_facts = [fact for fact in selected if _fact_context_key(fact) == context]
        inventory_totals = [fact for fact in context_facts if fact.metric == Metric.INVENTORY]
        inventory_children = [
            fact for fact in context_facts if fact.metric == Metric.INVENTORY_COMPONENT
        ]
        if inventory_totals and inventory_children:
            overlap_conflicts += 1
            aggregate_precedence += len(inventory_children)
            overlap_blocked += len(inventory_children)
            for child in inventory_children:
                selected.remove(child)
                denials.append(
                    {
                        "metric": child.metric.value,
                        "source_semantic": child.semantic_mapping,
                        "source_document_id": child.source_document_id,
                        "reason": "aggregate_child_overlap",
                    }
                )

        for metric in (Metric.TRADE_AR, Metric.BROAD_AR):
            metric_facts = [fact for fact in context_facts if fact.metric == metric]
            totals = [
                fact for fact in metric_facts if (fact.balance_scope or "").endswith("_total")
            ]
            children = [
                fact for fact in metric_facts if not (fact.balance_scope or "").endswith("_total")
            ]
            if totals and children:
                overlap_conflicts += 1
                aggregate_precedence += len(children)
                overlap_blocked += len(children)
                for child in children:
                    if child not in selected:
                        continue
                    selected.remove(child)
                    denials.append(
                        {
                            "metric": child.metric.value,
                            "source_semantic": child.semantic_mapping,
                            "source_document_id": child.source_document_id,
                            "reason": "aggregate_child_overlap",
                        }
                    )

        scope_groups: dict[tuple[Metric, str], list[FinancialFact]] = {}
        for fact in context_facts:
            if fact in selected:
                scope_groups.setdefault(
                    (fact.metric, fact.balance_scope or ""), []
                ).append(fact)
        for scope_facts in scope_groups.values():
            net = [fact for fact in scope_facts if fact.net_gross_scope == "net"]
            gross = [fact for fact in scope_facts if fact.net_gross_scope == "gross"]
            if not net or not gross:
                continue
            overlap_conflicts += 1
            gross_net_precedence += len(gross)
            overlap_blocked += len(gross)
            for gross_fact in gross:
                selected.remove(gross_fact)
                denials.append(
                    {
                        "metric": gross_fact.metric.value,
                        "source_semantic": gross_fact.semantic_mapping,
                        "source_document_id": gross_fact.source_document_id,
                        "reason": "gross_net_basis_mismatch",
                    }
                )
    return (
        selected,
        denials,
        aggregate_precedence,
        overlap_conflicts,
        overlap_blocked,
        gross_net_precedence,
    )


def canonicalize_working_capital_occurrences(
    occurrences: Iterable[OfficialFinancialOccurrence],
    *,
    as_of_date: date,
    analysis_framework: str,
) -> WorkingCapitalMappingBatch:
    route = sector_route(analysis_framework)
    values = tuple(occurrences)
    grouped: dict[tuple[object, ...], list[OfficialFinancialOccurrence]] = {}
    for occurrence in values:
        grouped.setdefault(_economic_key(occurrence), []).append(occurrence)

    facts: list[FinancialFact] = []
    denials: list[dict[str, str]] = []
    duplicates = 0
    conflicts = 0
    for group in grouped.values():
        eligible_dates = [
            item.filing_date
            for item in group
            if item.filing_date is not None and item.filing_date <= as_of_date
        ]
        if not eligible_dates:
            denials.append(_denial(group[0], "filing_date_unavailable_or_after_as_of"))
            continue
        latest_date = max(eligible_dates)
        latest = [item for item in group if item.filing_date == latest_date]
        latest_document = max(item.source_document_id or "" for item in latest)
        authoritative = [
            item for item in latest if (item.source_document_id or "") == latest_document
        ]
        if len({item.value for item in authoritative}) != 1:
            conflicts += 1
            denials.append(_denial(authoritative[0], "source_conflict"))
            continue
        duplicates += len(authoritative) - 1
        context_candidates = [
            item
            for item in group
            if item.fiscal_year is not None and item.fiscal_period is not None
        ]
        framed = [item for item in context_candidates if item.frame]
        annual = [
            item
            for item in context_candidates
            if item.source_document_type in {"10-K", "10-K/A", "20-F", "20-F/A"}
            and item.fiscal_period == "FY"
        ]
        context = min(
            framed or annual or context_candidates or group,
            key=lambda item: (
                item.filing_date or date.max,
                item.source_document_id or "",
            ),
        )
        selected_occurrence = replace(
            authoritative[0],
            fiscal_year=context.fiscal_year,
            fiscal_period=context.fiscal_period,
        )
        fact, reason = _canonicalize_occurrence(
            selected_occurrence,
            as_of_date=as_of_date,
            route=route,
        )
        if fact is None:
            denials.append(
                _denial(selected_occurrence, reason or "canonicalization_blocked")
            )
        else:
            facts.append(fact)

    exact_groups: dict[tuple[object, ...], list[FinancialFact]] = {}
    for fact in facts:
        exact_groups.setdefault(
            (
                *_fact_context_key(fact),
                fact.metric,
                fact.balance_scope,
                fact.net_gross_scope,
            ),
            [],
        ).append(fact)
    exact_selected: list[FinancialFact] = []
    for group in exact_groups.values():
        if len({fact.value for fact in group}) != 1:
            conflicts += 1
            denials.append(
                {
                    "metric": group[0].metric.value,
                    "source_semantic": group[0].semantic_mapping,
                    "source_document_id": group[0].source_document_id,
                    "reason": "source_conflict",
                }
            )
            continue
        duplicates += len(group) - 1
        exact_selected.append(
            max(
                group,
                key=lambda fact: (
                    REGISTRY_BY_SEMANTIC[fact.semantic_mapping].priority,
                    fact.filing_date,
                    fact.fact_id,
                ),
            )
        )
    (
        direct_facts,
        precedence_denials,
        aggregate_precedence,
        overlap_conflicts,
        overlap_blocked,
        gross_net_precedence,
    ) = _apply_overlap_precedence(exact_selected)
    denials.extend(precedence_denials)
    direct_facts.sort(
        key=lambda fact: (
            fact.issuer_id,
            fact.period.end,
            fact.metric.value,
            fact.balance_scope or "",
            fact.fact_id,
        )
    )
    return WorkingCapitalMappingBatch(
        facts=tuple(direct_facts),
        direct_facts=tuple(direct_facts),
        derived_facts=(),
        denials=tuple(denials),
        sector_route=route,
        source_candidates=len(values),
        extracted_occurrences=len(values),
        exact_duplicates_suppressed=duplicates,
        source_conflicts=conflicts,
        aggregate_precedence_count=aggregate_precedence,
        overlap_conflict_count=overlap_conflicts,
        overlap_blocked_count=overlap_blocked,
        gross_net_precedence_count=gross_net_precedence,
    )


def _same_comparison_basis(
    current: FinancialFact,
    prior: FinancialFact,
) -> tuple[str, ...]:
    reasons: list[str] = []
    for field_name in (
        "issuer_id",
        "metric",
        "semantic_mapping",
        "currency",
        "unit",
        "entity_scope",
        "statement_basis",
        "balance_scope",
        "net_gross_scope",
        "restatement_policy_id",
    ):
        if getattr(current, field_name) != getattr(prior, field_name):
            reasons.append(f"{field_name}_mismatch")
    if current.period.period_type != PeriodType.POINT_IN_TIME or (
        prior.period.period_type != PeriodType.POINT_IN_TIME
    ):
        reasons.append("point_in_time_mismatch")
    if current.metric not in _COMPARABLE_METRICS:
        reasons.append("unsupported_comparison_metric")
    if current.fact_id == prior.fact_id:
        reasons.append("comparison_same_fact")
    if prior.period.end >= current.period.end:
        reasons.append("prior_not_before_current")
    return tuple(dict.fromkeys(reasons))


def comparison_compatibility_reasons(
    current: FinancialFact,
    prior: FinancialFact,
    comparison_kind: ComparisonKind,
) -> tuple[str, ...]:
    reasons = list(_same_comparison_basis(current, prior))
    if comparison_kind == ComparisonKind.PRIOR_YEAR_COMPARABLE:
        gap = (current.period.end - prior.period.end).days
        if current.period.fiscal_year != prior.period.fiscal_year + 1:
            reasons.append("fiscal_year_not_prior_comparable")
        if current.period.fiscal_quarter != prior.period.fiscal_quarter:
            reasons.append("fiscal_quarter_mismatch")
        if abs(gap - 365) > 14:
            reasons.append("point_in_time_mismatch")
    elif comparison_kind == ComparisonKind.PRIOR_YEAR_END:
        if current.period.fiscal_year != prior.period.fiscal_year + 1:
            reasons.append("fiscal_year_not_prior_year_end")
        if prior.period.fiscal_quarter != 4:
            reasons.append("prior_year_end_required")
        if current.period.fiscal_quarter not in {1, 2, 3}:
            reasons.append("interim_current_period_required")
    else:
        reasons.append("comparison_kind_ambiguous")
    return tuple(dict.fromkeys(reasons))


def _derived_fact_id(
    current: FinancialFact,
    prior: FinancialFact,
    comparison_kind: ComparisonKind,
) -> str:
    identity = "|".join(
        (
            CONTRACT_VERSION,
            BALANCE_DELTA_FORMULA,
            comparison_kind.value,
            current.metric.value,
            current.balance_scope or "",
            current.net_gross_scope or "",
            current.period.end.isoformat(),
            prior.period.end.isoformat(),
            current.fact_id,
            prior.fact_id,
        )
    )
    return f"working-capital-derived:{hashlib.sha256(identity.encode()).hexdigest()[:24]}"


def derive_balance_absolute_delta(
    current: FinancialFact,
    prior: FinancialFact,
    *,
    comparison_kind: ComparisonKind,
    as_of_date: date,
) -> tuple[FinancialFact | None, tuple[str, ...]]:
    reasons = comparison_compatibility_reasons(current, prior, comparison_kind)
    if reasons:
        return None, reasons
    fact_id = _derived_fact_id(current, prior, comparison_kind)
    source_available_dates = [
        fact.source_available_at for fact in (current, prior) if fact.source_available_at
    ]
    if len(source_available_dates) != 2:
        return None, ("source_availability_missing",)
    raw_sha = hashlib.sha256(
        f"{current.raw_payload_sha256}|{prior.raw_payload_sha256}".encode()
    ).hexdigest()
    return (
        FinancialFact(
            fact_id=fact_id,
            issuer_id=current.issuer_id,
            metric=Metric.BALANCE_DELTA,
            value=current.value - prior.value,
            currency=current.currency,
            unit=current.unit,
            period=current.period,
            entity_scope=current.entity_scope,
            statement_basis=current.statement_basis,
            reported_or_derived="derived",
            source_provider="canonical_financial_derivation",
            source_document_id=f"derived:{fact_id.rsplit(':', maxsplit=1)[-1]}",
            filing_date=max(current.filing_date, prior.filing_date),
            source_occurrence_id=f"derived-occurrence:{fact_id.rsplit(':', maxsplit=1)[-1]}",
            raw_payload_sha256=raw_sha,
            semantic_mapping=current.semantic_mapping,
            fact_type=FactType.DERIVED_METRIC,
            source_document_type="derived_metric",
            source_semantic=None,
            source_reported_value=None,
            source_reported_unit=None,
            source_sign="derived_signed_balance_change",
            normalization_transform=None,
            derivation_formula=BALANCE_DELTA_FORMULA,
            derivation_version=CONTRACT_VERSION,
            input_fact_ids=(current.fact_id, prior.fact_id),
            quality="DERIVED_SAFE",
            eligibility=EligibilityStatus.ELIGIBLE,
            cautions=(
                "balance_change_not_interpreted",
                f"source_metric:{current.metric.value}",
                f"comparison_kind:{comparison_kind.value}",
            ),
            restatement_policy_id=current.restatement_policy_id,
            as_of_date=as_of_date,
            source_available_at=max(source_available_dates),
            balance_scope=current.balance_scope,
            net_gross_scope=current.net_gross_scope,
            comparison_kind=comparison_kind.value,
        ),
        (),
    )


def derive_safe_balance_deltas(
    facts: Iterable[FinancialFact],
    *,
    as_of_date: date,
) -> tuple[tuple[FinancialFact, ...], tuple[dict[str, str], ...]]:
    values = tuple(facts)
    latest_by_identity: dict[tuple[object, ...], FinancialFact] = {}
    for fact in values:
        if fact.metric not in _COMPARABLE_METRICS:
            continue
        identity = (
            fact.issuer_id,
            fact.metric,
            fact.semantic_mapping,
            fact.currency,
            fact.unit,
            fact.entity_scope,
            fact.statement_basis,
            fact.balance_scope,
            fact.net_gross_scope,
        )
        selected = latest_by_identity.get(identity)
        if selected is None or (
            fact.period.end,
            fact.filing_date,
            fact.fact_id,
        ) > (
            selected.period.end,
            selected.filing_date,
            selected.fact_id,
        ):
            latest_by_identity[identity] = fact

    derived: list[FinancialFact] = []
    denials: list[dict[str, str]] = []
    for current in latest_by_identity.values():
        comparable = [
            prior
            for prior in values
            if not comparison_compatibility_reasons(
                current, prior, ComparisonKind.PRIOR_YEAR_COMPARABLE
            )
        ]
        comparison_kind = ComparisonKind.PRIOR_YEAR_COMPARABLE
        candidates = comparable
        if not candidates:
            candidates = [
                prior
                for prior in values
                if not comparison_compatibility_reasons(
                    current, prior, ComparisonKind.PRIOR_YEAR_END
                )
            ]
            comparison_kind = ComparisonKind.PRIOR_YEAR_END
        if len(candidates) != 1:
            denials.append(
                {
                    "metric": current.metric.value,
                    "source_semantic": current.semantic_mapping,
                    "source_document_id": current.source_document_id,
                    "reason": (
                        "source_conflict"
                        if len(candidates) > 1
                        else "prior_comparable_missing"
                    ),
                }
            )
            continue
        delta, reasons = derive_balance_absolute_delta(
            current,
            candidates[0],
            comparison_kind=comparison_kind,
            as_of_date=as_of_date,
        )
        if delta is None:
            denials.append(
                {
                    "metric": current.metric.value,
                    "source_semantic": current.semantic_mapping,
                    "source_document_id": current.source_document_id,
                    "reason": reasons[0],
                }
            )
        else:
            derived.append(delta)
    derived.sort(key=lambda fact: (fact.issuer_id, fact.metric.value, fact.fact_id))
    return tuple(derived), tuple(denials)


def build_working_capital_mapping_batch(
    occurrences: Iterable[OfficialFinancialOccurrence],
    *,
    as_of_date: date,
    analysis_framework: str,
    source_candidates: int | None = None,
) -> WorkingCapitalMappingBatch:
    direct = canonicalize_working_capital_occurrences(
        occurrences,
        as_of_date=as_of_date,
        analysis_framework=analysis_framework,
    )
    derived, derivation_denials = derive_safe_balance_deltas(
        direct.direct_facts,
        as_of_date=as_of_date,
    )
    return replace(
        direct,
        facts=tuple([*direct.direct_facts, *derived]),
        derived_facts=derived,
        denials=tuple([*direct.denials, *derivation_denials]),
        source_candidates=(
            direct.source_candidates if source_candidates is None else source_candidates
        ),
    )


def extract_sec_working_capital_occurrences(
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
    selected_semantics = set(REGISTRY_BY_SEMANTIC) | set(EXCLUDED_SEMANTIC_REASONS)
    occurrences: list[OfficialFinancialOccurrence] = []
    for semantic in sorted(selected_semantics):
        namespace, tag = semantic.split(":", maxsplit=1)
        concepts = facts.get(namespace)
        if not isinstance(concepts, Mapping):
            continue
        concept = concepts.get(tag)
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
                value = _decimal(row.get("val"))
                if value is None:
                    continue
                unit = str(source_unit)
                occurrences.append(
                    OfficialFinancialOccurrence(
                        issuer_id=f"sec:{cik}",
                        value=value,
                        currency=(unit.upper() if len(unit) == 3 else None),
                        unit=unit,
                        period_start=None,
                        period_end=_date(row.get("end")),
                        fiscal_year=(
                            int(str(row["fy"]))
                            if str(row.get("fy") or "").isdigit()
                            else None
                        ),
                        fiscal_period=(
                            str(row.get("fp")) if row.get("fp") else None
                        ),
                        source_provider="sec_edgar_companyfacts",
                        source_document_id=(
                            str(row.get("accn")) if row.get("accn") else None
                        ),
                        source_document_type=(
                            str(row.get("form")) if row.get("form") else None
                        ),
                        filing_date=_date(row.get("filed")),
                        namespace=namespace,
                        tag=tag,
                        raw_payload_sha256=raw_payload_sha256,
                        entity_scope="issuer_level",
                        statement_basis="issuer_reported_balance_sheet",
                        frame=str(row.get("frame")) if row.get("frame") else None,
                        source_column="val",
                    )
                )
    return tuple(occurrences)


def build_sec_working_capital_mapping_batch(
    payload: Mapping[str, object],
    *,
    raw_payload_sha256: str,
    as_of_date: date,
    analysis_framework: str,
) -> WorkingCapitalMappingBatch:
    occurrences = extract_sec_working_capital_occurrences(
        payload,
        raw_payload_sha256=raw_payload_sha256,
    )
    return build_working_capital_mapping_batch(
        occurrences,
        as_of_date=as_of_date,
        analysis_framework=analysis_framework,
        source_candidates=len(occurrences),
    )


def _semantic_from_account_id(account_id: str) -> str | None:
    if "_" not in account_id:
        return None
    namespace, tag = account_id.split("_", maxsplit=1)
    return f"{namespace}:{tag}"


def promote_opendart_working_capital_facts(
    filing: Filing,
    rows_by_basis: Mapping[str, list[dict[str, object]]],
    xbrl_facts: Iterable[XbrlFact],
    *,
    raw_payload_sha256: str,
    as_of_date: date,
    analysis_framework: str,
) -> WorkingCapitalMappingBatch:
    cfs_rows = [
        row for row in rows_by_basis.get("CFS", []) if row.get("sj_div") == "BS"
    ]
    ofs_rows = [
        row for row in rows_by_basis.get("OFS", []) if row.get("sj_div") == "BS"
    ]
    selected_rows = cfs_rows or ofs_rows
    source_basis = "CFS" if cfs_rows else "OFS"
    statement_basis = "consolidated" if source_basis == "CFS" else "separate"
    current_fiscal_period = _FISCAL_PERIOD_BY_REPORT_CODE.get(filing.report_code)
    facts = tuple(xbrl_facts)
    occurrences: list[OfficialFinancialOccurrence] = []
    pre_denials: list[dict[str, str]] = []
    candidate_count = 0
    recognized = set(REGISTRY_BY_SEMANTIC) | set(EXCLUDED_SEMANTIC_REASONS)
    for row in selected_rows:
        account_id = str(row.get("account_id") or "")
        semantic = _semantic_from_account_id(account_id)
        if semantic not in recognized:
            continue
        candidate_count += 1
        source_identity = (
            str(row.get("rcept_no") or "") == filing.receipt_no
            and str(row.get("reprt_code") or "") == filing.report_code
            and str(row.get("bsns_year") or "") == str(filing.business_year)
            and str(row.get("corp_code") or "") == filing.corp_code
            and str(row.get("fs_div") or "") == source_basis
        )
        if not source_identity:
            pre_denials.append(
                {
                    "metric": "working_capital",
                    "source_semantic": semantic or "",
                    "source_document_id": filing.receipt_no,
                    "reason": "filing_identity_mismatch",
                }
            )
            continue
        if current_fiscal_period is None:
            pre_denials.append(
                {
                    "metric": "working_capital",
                    "source_semantic": semantic or "",
                    "source_document_id": filing.receipt_no,
                    "reason": "source_amount_currency_or_period_missing",
                }
            )
            continue
        namespace, tag = account_id.split("_", maxsplit=1)
        for source_column, fiscal_year, fiscal_period in (
            ("thstrm_amount", filing.business_year, current_fiscal_period),
            ("frmtrm_amount", filing.business_year - 1, "FY"),
        ):
            value = _decimal(row.get(source_column))
            currency = str(row.get("currency") or "").upper()
            if value is None:
                continue
            if currency != "KRW":
                pre_denials.append(
                    {
                        "metric": "working_capital",
                        "source_semantic": semantic or "",
                        "source_document_id": filing.receipt_no,
                        "reason": "source_amount_currency_or_period_missing",
                    }
                )
                continue
            match = reconcile_xbrl_instant_fact(
                facts,
                taxonomy_element=tag,
                value=value,
                unit_ref="KRW",
                statement_basis=statement_basis,
                entity_identifier=filing.corp_code,
            )
            if match is None:
                pre_denials.append(
                    {
                        "metric": "working_capital",
                        "source_semantic": semantic or "",
                        "source_document_id": filing.receipt_no,
                        "reason": "exact_context_unresolved",
                    }
                )
                continue
            occurrences.append(
                OfficialFinancialOccurrence(
                    issuer_id=f"opendart:{filing.corp_code}",
                    value=value,
                    currency=currency,
                    unit=str(match.unit_ref or ""),
                    period_start=None,
                    period_end=match.context.period_end,
                    fiscal_year=fiscal_year,
                    fiscal_period=fiscal_period,
                    source_provider="opendart_xbrl",
                    source_document_id=filing.receipt_no,
                    source_document_type=filing.report_code,
                    filing_date=filing.receipt_date,
                    namespace=namespace,
                    tag=tag,
                    raw_payload_sha256=raw_payload_sha256,
                    entity_scope="issuer_level",
                    statement_basis=statement_basis,
                    frame=match.context_ref,
                    source_column=source_column,
                )
            )
    batch = build_working_capital_mapping_batch(
        occurrences,
        as_of_date=as_of_date,
        analysis_framework=analysis_framework,
        source_candidates=candidate_count,
    )
    return replace(batch, denials=tuple([*pre_denials, *batch.denials]))


def registry_audit() -> tuple[dict[str, object], ...]:
    return tuple(
        {
            "canonical_metric": entry.metric.value,
            "source_semantic": entry.semantic,
            "role": entry.role.value,
            "balance_scope": entry.balance_scope,
            "net_gross_scope": entry.net_gross_scope,
            "priority": entry.priority,
        }
        for entry in WORKING_CAPITAL_SEMANTIC_REGISTRY
    )
