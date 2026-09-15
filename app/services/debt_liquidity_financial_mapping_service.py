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
from app.services.opendart_xbrl_service import (
    XbrlFact,
    reconcile_xbrl_instant_fact,
)
from app.services.working_capital_evidence_service import OfficialFinancialOccurrence


CONTRACT_VERSION = "interest-bearing-debt-liquidity-v1"
CANONICAL_FINANCIAL_SOURCE = "canonical_financial_fact"
DEBT_SCOPE = "complete_borrowings_bonds_convertibles_excluding_lease_liabilities"
NET_DEBT_SCOPE = "complete_debt_less_cash_and_cash_equivalents"
LEASE_LIABILITY_POLICY = "SEPARATE_CONTEXT_ONLY"
RESTRICTED_CASH_POLICY = "EXCLUDE_FROM_NET_DEBT_CASH_BASIS"

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
    CASH_BASIS = "CASH_BASIS"
    RESTRICTED_CASH_CONTEXT = "RESTRICTED_CASH_CONTEXT"
    COMBINED_CASH_CONTEXT = "COMBINED_CASH_CONTEXT"
    DEBT_COMPONENT = "DEBT_COMPONENT"
    LEASE_CONTEXT = "LEASE_CONTEXT"


class DebtCompletenessStatus(StrEnum):
    COMPLETE = "COMPLETE"
    PARTIAL = "PARTIAL"
    UNKNOWN = "UNKNOWN"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class SectorRoute(StrEnum):
    GENERIC_OPERATING_COMPANY = "GENERIC_OPERATING_COMPANY"
    SECTOR_FRAMEWORK_REQUIRED = "SECTOR_FRAMEWORK_REQUIRED"


@dataclass(frozen=True)
class DebtLiquidityRegistryEntry:
    metric: Metric
    namespace: str
    tag: str
    role: ComponentRole
    component_group: str
    priority: int = 100

    @property
    def semantic(self) -> str:
        return f"{self.namespace}:{self.tag}"


DEBT_LIQUIDITY_SEMANTIC_REGISTRY = (
    DebtLiquidityRegistryEntry(
        Metric.CASH_AND_CASH_EQUIVALENTS,
        "us-gaap",
        "CashAndCashEquivalentsAtCarryingValue",
        ComponentRole.CASH_BASIS,
        "cash_and_cash_equivalents_only",
    ),
    DebtLiquidityRegistryEntry(
        Metric.CASH_AND_CASH_EQUIVALENTS,
        "ifrs-full",
        "CashAndCashEquivalents",
        ComponentRole.CASH_BASIS,
        "cash_and_cash_equivalents_only",
    ),
    DebtLiquidityRegistryEntry(
        Metric.CASH_AND_RESTRICTED_CASH,
        "us-gaap",
        "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents",
        ComponentRole.COMBINED_CASH_CONTEXT,
        "cash_and_restricted_cash_combined",
    ),
    DebtLiquidityRegistryEntry(
        Metric.RESTRICTED_CASH_CURRENT,
        "us-gaap",
        "RestrictedCashAndCashEquivalentsCurrent",
        ComponentRole.RESTRICTED_CASH_CONTEXT,
        "restricted_cash_current",
    ),
    DebtLiquidityRegistryEntry(
        Metric.RESTRICTED_CASH_NONCURRENT,
        "us-gaap",
        "RestrictedCashAndCashEquivalentsNoncurrent",
        ComponentRole.RESTRICTED_CASH_CONTEXT,
        "restricted_cash_noncurrent",
    ),
    DebtLiquidityRegistryEntry(
        Metric.SHORT_TERM_BORROWINGS,
        "us-gaap",
        "ShortTermBorrowings",
        ComponentRole.DEBT_COMPONENT,
        "short_term_borrowings",
    ),
    DebtLiquidityRegistryEntry(
        Metric.CURRENT_INTEREST_BEARING_DEBT,
        "us-gaap",
        "DebtCurrent",
        ComponentRole.DEBT_COMPONENT,
        "current_debt_aggregate",
    ),
    DebtLiquidityRegistryEntry(
        Metric.CURRENT_PORTION_LONG_TERM_DEBT,
        "us-gaap",
        "LongTermDebtCurrent",
        ComponentRole.DEBT_COMPONENT,
        "current_portion_long_term_debt",
    ),
    DebtLiquidityRegistryEntry(
        Metric.LONG_TERM_BORROWINGS,
        "us-gaap",
        "LongTermDebtNoncurrent",
        ComponentRole.DEBT_COMPONENT,
        "long_term_borrowings",
    ),
    DebtLiquidityRegistryEntry(
        Metric.NOTES_PAYABLE_CURRENT,
        "us-gaap",
        "NotesPayableCurrent",
        ComponentRole.DEBT_COMPONENT,
        "notes_payable_current",
    ),
    DebtLiquidityRegistryEntry(
        Metric.NOTES_PAYABLE_NONCURRENT,
        "us-gaap",
        "NotesPayableNoncurrent",
        ComponentRole.DEBT_COMPONENT,
        "notes_payable_noncurrent",
    ),
    DebtLiquidityRegistryEntry(
        Metric.CONVERTIBLE_DEBT_CURRENT,
        "us-gaap",
        "ConvertibleDebtCurrent",
        ComponentRole.DEBT_COMPONENT,
        "convertible_debt_current",
    ),
    DebtLiquidityRegistryEntry(
        Metric.CONVERTIBLE_DEBT_NONCURRENT,
        "us-gaap",
        "ConvertibleDebtNoncurrent",
        ComponentRole.DEBT_COMPONENT,
        "convertible_debt_noncurrent",
    ),
    DebtLiquidityRegistryEntry(
        Metric.LEASE_LIABILITIES_CURRENT,
        "us-gaap",
        "FinanceLeaseLiabilityCurrent",
        ComponentRole.LEASE_CONTEXT,
        "lease_liability_current",
    ),
    DebtLiquidityRegistryEntry(
        Metric.LEASE_LIABILITIES_NONCURRENT,
        "us-gaap",
        "FinanceLeaseLiabilityNoncurrent",
        ComponentRole.LEASE_CONTEXT,
        "lease_liability_noncurrent",
    ),
    DebtLiquidityRegistryEntry(
        Metric.LEASE_LIABILITIES_CURRENT,
        "us-gaap",
        "OperatingLeaseLiabilityCurrent",
        ComponentRole.LEASE_CONTEXT,
        "lease_liability_current",
        90,
    ),
    DebtLiquidityRegistryEntry(
        Metric.LEASE_LIABILITIES_NONCURRENT,
        "us-gaap",
        "OperatingLeaseLiabilityNoncurrent",
        ComponentRole.LEASE_CONTEXT,
        "lease_liability_noncurrent",
        90,
    ),
    DebtLiquidityRegistryEntry(
        Metric.SHORT_TERM_BORROWINGS,
        "ifrs-full",
        "ShorttermBorrowings",
        ComponentRole.DEBT_COMPONENT,
        "short_term_borrowings",
    ),
    DebtLiquidityRegistryEntry(
        Metric.CURRENT_INTEREST_BEARING_DEBT,
        "ifrs-full",
        "CurrentBorrowingsAndCurrentPortionOfNoncurrentBorrowings",
        ComponentRole.DEBT_COMPONENT,
        "current_borrowings_aggregate",
    ),
    DebtLiquidityRegistryEntry(
        Metric.CURRENT_INTEREST_BEARING_DEBT,
        "ifrs-full",
        "CurrentLoansReceivedAndCurrentPortionOfNoncurrentLoansReceived",
        ComponentRole.DEBT_COMPONENT,
        "current_borrowings_aggregate",
        95,
    ),
    DebtLiquidityRegistryEntry(
        Metric.SHORT_TERM_BORROWINGS,
        "dart",
        "CurrentLoansReceived",
        ComponentRole.DEBT_COMPONENT,
        "short_term_borrowings",
    ),
    DebtLiquidityRegistryEntry(
        Metric.CURRENT_PORTION_LONG_TERM_DEBT,
        "ifrs-full",
        "CurrentPortionOfLongtermBorrowings",
        ComponentRole.DEBT_COMPONENT,
        "current_portion_long_term_debt",
    ),
    DebtLiquidityRegistryEntry(
        Metric.LONG_TERM_BORROWINGS,
        "ifrs-full",
        "LongtermBorrowings",
        ComponentRole.DEBT_COMPONENT,
        "long_term_borrowings",
    ),
    DebtLiquidityRegistryEntry(
        Metric.LONG_TERM_BORROWINGS,
        "ifrs-full",
        "NoncurrentPortionOfNoncurrentLoansReceived",
        ComponentRole.DEBT_COMPONENT,
        "long_term_borrowings",
        95,
    ),
    DebtLiquidityRegistryEntry(
        Metric.BONDS_PAYABLE_CURRENT,
        "dart",
        "CurrentPortionOfNoncurrentBondsIssued",
        ComponentRole.DEBT_COMPONENT,
        "bonds_payable_current",
    ),
    DebtLiquidityRegistryEntry(
        Metric.BONDS_PAYABLE_NONCURRENT,
        "ifrs-full",
        "NoncurrentPortionOfNoncurrentBondsIssued",
        ComponentRole.DEBT_COMPONENT,
        "bonds_payable_noncurrent",
    ),
    DebtLiquidityRegistryEntry(
        Metric.LEASE_LIABILITIES_CURRENT,
        "ifrs-full",
        "CurrentLeaseLiabilities",
        ComponentRole.LEASE_CONTEXT,
        "lease_liability_current",
    ),
    DebtLiquidityRegistryEntry(
        Metric.LEASE_LIABILITIES_NONCURRENT,
        "ifrs-full",
        "NoncurrentLeaseLiabilities",
        ComponentRole.LEASE_CONTEXT,
        "lease_liability_noncurrent",
    ),
)

REGISTRY_BY_SEMANTIC = {
    entry.semantic: entry for entry in DEBT_LIQUIDITY_SEMANTIC_REGISTRY
}

TOTAL_LIABILITY_SEMANTICS = {
    "us-gaap:Liabilities",
    "us-gaap:LiabilitiesCurrent",
    "us-gaap:LiabilitiesNoncurrent",
    "ifrs-full:Liabilities",
    "ifrs-full:CurrentLiabilities",
    "ifrs-full:NoncurrentLiabilities",
}

UNSUPPORTED_DEBT_SEMANTICS = {
    "dart:CurrentPortionOfConvertibleRedeemablePreferredStockLiabilities",
    "dart:HybridBonds",
    "us-gaap:LongTermDebtAndFinanceLeaseObligationsCurrent",
    "us-gaap:LongTermDebtAndFinanceLeaseObligationsNoncurrent",
}

DEBT_COMPONENT_METRICS = frozenset(
    {
        Metric.SHORT_TERM_BORROWINGS,
        Metric.CURRENT_PORTION_LONG_TERM_DEBT,
        Metric.CURRENT_INTEREST_BEARING_DEBT,
        Metric.LONG_TERM_BORROWINGS,
        Metric.BONDS_PAYABLE_CURRENT,
        Metric.BONDS_PAYABLE_NONCURRENT,
        Metric.NOTES_PAYABLE_CURRENT,
        Metric.NOTES_PAYABLE_NONCURRENT,
        Metric.CONVERTIBLE_DEBT_CURRENT,
        Metric.CONVERTIBLE_DEBT_NONCURRENT,
    }
)

_CURRENT_AGGREGATE_CHILDREN = frozenset(
    {
        Metric.SHORT_TERM_BORROWINGS,
        Metric.CURRENT_PORTION_LONG_TERM_DEBT,
    }
)

_FULL_CURRENT_DEBT_CHILDREN = frozenset(
    {
        *_CURRENT_AGGREGATE_CHILDREN,
        Metric.BONDS_PAYABLE_CURRENT,
        Metric.NOTES_PAYABLE_CURRENT,
        Metric.CONVERTIBLE_DEBT_CURRENT,
    }
)

_CURRENT_DEBT_METRICS = frozenset(
    {
        Metric.CURRENT_INTEREST_BEARING_DEBT,
        Metric.SHORT_TERM_BORROWINGS,
        Metric.CURRENT_PORTION_LONG_TERM_DEBT,
        Metric.BONDS_PAYABLE_CURRENT,
        Metric.NOTES_PAYABLE_CURRENT,
        Metric.CONVERTIBLE_DEBT_CURRENT,
    }
)

_NONCURRENT_DEBT_METRICS = frozenset(
    {
        Metric.LONG_TERM_BORROWINGS,
        Metric.BONDS_PAYABLE_NONCURRENT,
        Metric.NOTES_PAYABLE_NONCURRENT,
        Metric.CONVERTIBLE_DEBT_NONCURRENT,
    }
)

_COMPONENT_ORDER = {
    metric: index
    for index, metric in enumerate(
        (
            Metric.CURRENT_INTEREST_BEARING_DEBT,
            Metric.SHORT_TERM_BORROWINGS,
            Metric.CURRENT_PORTION_LONG_TERM_DEBT,
            Metric.BONDS_PAYABLE_CURRENT,
            Metric.NOTES_PAYABLE_CURRENT,
            Metric.CONVERTIBLE_DEBT_CURRENT,
            Metric.LONG_TERM_BORROWINGS,
            Metric.BONDS_PAYABLE_NONCURRENT,
            Metric.NOTES_PAYABLE_NONCURRENT,
            Metric.CONVERTIBLE_DEBT_NONCURRENT,
        )
    )
}

_FINANCIAL_SECTOR_FRAMEWORKS = {
    "bank",
    "insurance",
    "reinsurance",
    "financial_institution",
    "bank_or_insurer",
}


@dataclass(frozen=True)
class DirectCanonicalizationBatch:
    facts: tuple[FinancialFact, ...]
    denials: tuple[dict[str, str], ...]
    extracted_occurrences: int
    exact_duplicates_suppressed: int
    source_conflicts: int


@dataclass(frozen=True)
class DebtCompletenessAssessment:
    status: DebtCompletenessStatus
    selected_fact_ids: tuple[str, ...] = ()
    reasons: tuple[str, ...] = ()
    aggregate_precedence_count: int = 0
    component_precedence_count: int = 0
    overlap_conflict_count: int = 0
    overlap_blocked_count: int = 0


@dataclass(frozen=True)
class DebtLiquidityBatch:
    facts: tuple[FinancialFact, ...]
    direct_facts: tuple[FinancialFact, ...]
    denials: tuple[dict[str, str], ...]
    completeness: DebtCompletenessAssessment
    sector_route: SectorRoute
    extracted_occurrences: int
    exact_duplicates_suppressed: int
    source_conflicts: int
    source_candidates: int = 0


def sector_route(analysis_framework: str) -> SectorRoute:
    if analysis_framework.strip().lower() in _FINANCIAL_SECTOR_FRAMEWORKS:
        return SectorRoute.SECTOR_FRAMEWORK_REQUIRED
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


def _point_period(
    occurrence: OfficialFinancialOccurrence,
) -> PeriodIdentity | None:
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
    payload = "|".join(
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
        )
    )
    digest = hashlib.sha256(payload.encode()).hexdigest()[:24]
    return f"debt-liquidity-occurrence:{digest}"


def _reported_fact_id(
    occurrence: OfficialFinancialOccurrence,
    entry: DebtLiquidityRegistryEntry,
    period: PeriodIdentity,
) -> str:
    payload = "|".join(
        (
            CONTRACT_VERSION,
            occurrence.issuer_id,
            entry.metric.value,
            period.end.isoformat(),
            occurrence.entity_scope or "",
            occurrence.statement_basis or "",
            occurrence.currency or "",
            _occurrence_id(occurrence),
        )
    )
    return f"debt-liquidity-reported:{hashlib.sha256(payload.encode()).hexdigest()[:24]}"


def _denial(
    occurrence: OfficialFinancialOccurrence | None,
    reason: str,
    *,
    metric: str | None = None,
) -> dict[str, str]:
    return {
        "metric": metric or "debt_liquidity",
        "source_semantic": occurrence.semantic if occurrence else "",
        "source_document_id": (
            occurrence.source_document_id or "" if occurrence else ""
        ),
        "reason": reason,
    }


def _canonicalize_direct_occurrence(
    occurrence: OfficialFinancialOccurrence,
    *,
    as_of_date: date,
    route: SectorRoute,
    holding_company: bool,
) -> tuple[FinancialFact | None, str | None]:
    if route == SectorRoute.SECTOR_FRAMEWORK_REQUIRED:
        return None, "financial_sector_not_applicable"
    if occurrence.semantic in TOTAL_LIABILITY_SEMANTICS:
        return None, "total_liabilities_not_interest_bearing_debt"
    if occurrence.semantic in UNSUPPORTED_DEBT_SEMANTICS:
        return None, "unsupported_component_semantic"
    entry = REGISTRY_BY_SEMANTIC.get(occurrence.semantic)
    if entry is None:
        return None, "semantic_not_registered"
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
    cautions = [entry.component_group]
    if entry.role == ComponentRole.LEASE_CONTEXT:
        cautions.append("lease_liabilities_separate_context_only")
    elif entry.role == ComponentRole.RESTRICTED_CASH_CONTEXT:
        cautions.append("restricted_cash_excluded_from_net_debt_cash_basis")
    elif entry.role == ComponentRole.COMBINED_CASH_CONTEXT:
        cautions.append("combined_cash_and_restricted_cash_not_net_debt_eligible")
    elif entry.metric in {
        Metric.CONVERTIBLE_DEBT_CURRENT,
        Metric.CONVERTIBLE_DEBT_NONCURRENT,
    }:
        cautions.append("convertible_dilution_terms_not_evaluated")
    if holding_company:
        cautions.append(
            "holding_company_parent_subsidiary_funding_separation_not_resolved"
        )
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
            balance_scope=entry.component_group,
            net_gross_scope="gross",
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
    )


def canonicalize_debt_liquidity_occurrences(
    occurrences: Iterable[OfficialFinancialOccurrence],
    *,
    as_of_date: date,
    analysis_framework: str,
    holding_company: bool = False,
) -> DirectCanonicalizationBatch:
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
            denials.append(
                _denial(group[0], "filing_date_unavailable_or_after_as_of")
            )
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
        selected = authoritative[0]
        fact, reason = _canonicalize_direct_occurrence(
            selected,
            as_of_date=as_of_date,
            route=route,
            holding_company=holding_company,
        )
        if fact is None:
            denials.append(_denial(selected, reason or "canonicalization_blocked"))
        else:
            facts.append(fact)

    by_metric: dict[tuple[object, ...], list[FinancialFact]] = {}
    for fact in facts:
        by_metric.setdefault(
            (
                fact.issuer_id,
                fact.metric,
                fact.period,
                fact.currency,
                fact.unit,
                fact.entity_scope,
                fact.statement_basis,
            ),
            [],
        ).append(fact)
    selected_facts: list[FinancialFact] = []
    for metric_facts in by_metric.values():
        if len({fact.value for fact in metric_facts}) != 1:
            conflicts += 1
            denials.append(
                _denial(
                    None,
                    "source_conflict",
                    metric=metric_facts[0].metric.value,
                )
            )
            continue
        duplicates += len(metric_facts) - 1
        selected_facts.append(
            max(
                metric_facts,
                key=lambda fact: (
                    REGISTRY_BY_SEMANTIC[fact.semantic_mapping].priority,
                    fact.filing_date,
                    fact.fact_id,
                ),
            )
        )
    selected_facts.sort(
        key=lambda fact: (
            fact.issuer_id,
            fact.period.end,
            fact.metric.value,
            fact.fact_id,
        )
    )
    return DirectCanonicalizationBatch(
        facts=tuple(selected_facts),
        denials=tuple(denials),
        extracted_occurrences=len(values),
        exact_duplicates_suppressed=duplicates,
        source_conflicts=conflicts,
    )


def _compatibility_reasons(facts: Sequence[FinancialFact]) -> tuple[str, ...]:
    if not facts:
        return ("missing_debt_components",)
    reasons: list[str] = []
    fields = (
        ("issuer_id", "entity_scope_mismatch"),
        ("currency", "currency_mismatch"),
        ("unit", "unit_mismatch"),
        ("period", "point_in_time_mismatch"),
        ("entity_scope", "entity_scope_mismatch"),
        ("statement_basis", "statement_basis_mismatch"),
        ("source_document_id", "source_document_mismatch"),
    )
    for field_name, reason in fields:
        if len({getattr(fact, field_name) for fact in facts}) != 1:
            reasons.append(reason)
    if any(fact.period.period_type != PeriodType.POINT_IN_TIME for fact in facts):
        reasons.append("point_in_time_required")
    if any(fact.eligibility != EligibilityStatus.ELIGIBLE for fact in facts):
        reasons.append("input_fact_not_eligible")
    return tuple(dict.fromkeys(reasons))


def _component_overlap_reasons(
    facts: Sequence[FinancialFact],
) -> tuple[str, ...]:
    scopes = [fact.balance_scope for fact in facts]
    if any(scope is None for scope in scopes) or len(scopes) != len(set(scopes)):
        return ("component_overlap",)
    scope_set = set(scopes)
    if "current_debt_aggregate" in scope_set and scope_set.intersection(
        {
            "short_term_borrowings",
            "current_portion_long_term_debt",
            "bonds_payable_current",
            "notes_payable_current",
            "convertible_debt_current",
        }
    ):
        return ("component_overlap",)
    if "current_borrowings_aggregate" in scope_set and scope_set.intersection(
        {"short_term_borrowings", "current_portion_long_term_debt"}
    ):
        return ("component_overlap",)
    return ()


def assess_debt_completeness(
    facts: Sequence[FinancialFact],
    *,
    analysis_framework: str,
    statement_inventory_complete: bool,
    unsupported_semantics: Sequence[str] = (),
) -> DebtCompletenessAssessment:
    if sector_route(analysis_framework) == SectorRoute.SECTOR_FRAMEWORK_REQUIRED:
        return DebtCompletenessAssessment(
            DebtCompletenessStatus.NOT_APPLICABLE,
            reasons=("financial_sector_not_applicable",),
        )
    components = [fact for fact in facts if fact.metric in DEBT_COMPONENT_METRICS]
    if not statement_inventory_complete:
        return DebtCompletenessAssessment(
            DebtCompletenessStatus.UNKNOWN,
            reasons=("debt_scope_incomplete",),
        )
    if unsupported_semantics:
        return DebtCompletenessAssessment(
            DebtCompletenessStatus.PARTIAL,
            reasons=("unsupported_component_semantic",),
        )
    if not components:
        return DebtCompletenessAssessment(
            DebtCompletenessStatus.UNKNOWN,
            reasons=("missing_debt_components",),
        )
    compatibility = _compatibility_reasons(components)
    if compatibility:
        return DebtCompletenessAssessment(
            DebtCompletenessStatus.PARTIAL,
            reasons=compatibility,
        )

    selected = list(components)
    aggregate_precedence = 0
    current_aggregates = [
        fact
        for fact in selected
        if fact.metric == Metric.CURRENT_INTEREST_BEARING_DEBT
    ]
    if current_aggregates:
        excluded_children = (
            _FULL_CURRENT_DEBT_CHILDREN
            if any(
                fact.balance_scope == "current_debt_aggregate"
                for fact in current_aggregates
            )
            else _CURRENT_AGGREGATE_CHILDREN
        )
        children = [
            fact for fact in selected if fact.metric in excluded_children
        ]
        aggregate_precedence = len(children)
        selected = [
            fact
            for fact in selected
            if fact.metric not in excluded_children
        ]
    selected.sort(key=lambda fact: (_COMPONENT_ORDER[fact.metric], fact.fact_id))
    represented = {fact.metric for fact in selected}
    if not represented.intersection(_CURRENT_DEBT_METRICS) or not represented.intersection(
        _NONCURRENT_DEBT_METRICS
    ):
        return DebtCompletenessAssessment(
            DebtCompletenessStatus.PARTIAL,
            selected_fact_ids=tuple(fact.fact_id for fact in selected),
            reasons=("debt_scope_incomplete",),
            aggregate_precedence_count=aggregate_precedence,
        )
    return DebtCompletenessAssessment(
        DebtCompletenessStatus.COMPLETE,
        selected_fact_ids=tuple(fact.fact_id for fact in selected),
        aggregate_precedence_count=aggregate_precedence,
    )


def _combined_sha(facts: Sequence[FinancialFact]) -> str:
    payload = "|".join(
        f"{fact.fact_id}:{fact.raw_payload_sha256}" for fact in facts
    )
    return hashlib.sha256(payload.encode()).hexdigest()


def _derived_id(
    metric: Metric,
    formula: str,
    facts: Sequence[FinancialFact],
) -> str:
    payload = "|".join(
        (
            CONTRACT_VERSION,
            metric.value,
            formula,
            facts[0].period.end.isoformat(),
            facts[0].entity_scope,
            facts[0].statement_basis,
            *(fact.fact_id for fact in facts),
        )
    )
    return f"debt-liquidity-derived:{hashlib.sha256(payload.encode()).hexdigest()[:24]}"


def derive_interest_bearing_debt_total(
    direct_facts: Sequence[FinancialFact],
    completeness: DebtCompletenessAssessment,
) -> tuple[FinancialFact | None, tuple[str, ...]]:
    if completeness.status != DebtCompletenessStatus.COMPLETE:
        return None, completeness.reasons or ("debt_scope_incomplete",)
    by_id = {fact.fact_id: fact for fact in direct_facts}
    inputs = [by_id.get(fact_id) for fact_id in completeness.selected_fact_ids]
    if any(fact is None for fact in inputs):
        return None, ("missing_debt_components",)
    selected = tuple(fact for fact in inputs if fact is not None)
    if any(fact.metric not in DEBT_COMPONENT_METRICS for fact in selected):
        return None, ("unsupported_component_semantic",)
    reasons = _compatibility_reasons(selected)
    if reasons:
        return None, reasons
    represented = {fact.metric for fact in selected}
    if not represented.intersection(_CURRENT_DEBT_METRICS) or not represented.intersection(
        _NONCURRENT_DEBT_METRICS
    ):
        return None, ("debt_scope_incomplete",)
    overlap_reasons = _component_overlap_reasons(selected)
    if overlap_reasons:
        return None, overlap_reasons
    first = selected[0]
    formula = "interest_bearing_debt_total"
    derivation_key = "|".join(item.fact_id for item in selected)
    fact = replace(
        first,
        fact_id=_derived_id(
            Metric.INTEREST_BEARING_DEBT_TOTAL,
            formula,
            selected,
        ),
        metric=Metric.INTEREST_BEARING_DEBT_TOTAL,
        value=sum((item.value for item in selected), Decimal(0)),
        reported_or_derived="derived",
        source_provider="canonical_derivation",
        source_document_type="derived_metric",
        source_occurrence_id=(
            "debt-liquidity-derivation:"
            + hashlib.sha256(derivation_key.encode()).hexdigest()[:24]
        ),
        raw_payload_sha256=_combined_sha(selected),
        semantic_mapping="verified_non_overlapping_interest_bearing_debt_components",
        fact_type=FactType.DERIVED_METRIC,
        source_semantic=None,
        source_reported_value=None,
        source_reported_unit=None,
        source_sign=None,
        normalization_transform=None,
        derivation_formula=formula,
        derivation_version=CONTRACT_VERSION,
        input_fact_ids=tuple(item.fact_id for item in selected),
        quality="DERIVED_SAFE",
        cautions=("lease_liabilities_excluded_from_debt_scope",),
        balance_scope=DEBT_SCOPE,
        net_gross_scope="gross",
    )
    return fact, ()


def derive_net_debt(
    debt_total: FinancialFact,
    cash: FinancialFact,
) -> tuple[FinancialFact | None, tuple[str, ...]]:
    reasons = list(_compatibility_reasons((debt_total, cash)))
    if debt_total.metric != Metric.INTEREST_BEARING_DEBT_TOTAL:
        reasons.append("complete_interest_bearing_debt_total_required")
    if debt_total.balance_scope != DEBT_SCOPE:
        reasons.append("debt_scope_incomplete")
    if cash.metric != Metric.CASH_AND_CASH_EQUIVALENTS:
        reasons.append("missing_cash")
    if cash.balance_scope != "cash_and_cash_equivalents_only":
        reasons.append("restricted_cash_ambiguity")
    if reasons:
        return None, tuple(dict.fromkeys(reasons))
    inputs = (debt_total, cash)
    formula = "net_debt"
    derivation_key = "|".join(item.fact_id for item in inputs)
    fact = replace(
        debt_total,
        fact_id=_derived_id(Metric.NET_DEBT, formula, inputs),
        metric=Metric.NET_DEBT,
        value=debt_total.value - cash.value,
        source_document_type="derived_metric",
        source_occurrence_id=(
            "debt-liquidity-derivation:"
            + hashlib.sha256(derivation_key.encode()).hexdigest()[:24]
        ),
        raw_payload_sha256=_combined_sha(inputs),
        semantic_mapping="complete_debt_less_cash_and_cash_equivalents",
        input_fact_ids=(debt_total.fact_id, cash.fact_id),
        derivation_formula=formula,
        derivation_version=CONTRACT_VERSION,
        cautions=(
            "lease_liabilities_excluded_from_debt_scope",
            "restricted_cash_not_netted",
        ),
        balance_scope=NET_DEBT_SCOPE,
        net_gross_scope="net",
    )
    return fact, ()


def build_debt_liquidity_batch(
    occurrences: Iterable[OfficialFinancialOccurrence],
    *,
    as_of_date: date,
    analysis_framework: str,
    statement_inventory_complete: bool,
    unsupported_semantics: Sequence[str] = (),
    holding_company: bool = False,
    source_candidates: int = 0,
) -> DebtLiquidityBatch:
    route = sector_route(analysis_framework)
    direct = canonicalize_debt_liquidity_occurrences(
        occurrences,
        as_of_date=as_of_date,
        analysis_framework=analysis_framework,
        holding_company=holding_company,
    )
    latest_components = [
        fact for fact in direct.facts if fact.metric in DEBT_COMPONENT_METRICS
    ]
    if latest_components:
        latest_end = max(fact.period.end for fact in latest_components)
        latest_filing = max(
            fact.filing_date
            for fact in latest_components
            if fact.period.end == latest_end
        )
        latest_components = [
            fact
            for fact in latest_components
            if fact.period.end == latest_end and fact.filing_date == latest_filing
        ]
    completeness = assess_debt_completeness(
        latest_components,
        analysis_framework=analysis_framework,
        statement_inventory_complete=statement_inventory_complete,
        unsupported_semantics=unsupported_semantics,
    )
    denials = list(direct.denials)
    derived: list[FinancialFact] = []
    debt_total, debt_reasons = derive_interest_bearing_debt_total(
        latest_components,
        completeness,
    )
    if debt_total is None:
        denials.append(
            {
                "metric": Metric.INTEREST_BEARING_DEBT_TOTAL.value,
                "source_semantic": "",
                "source_document_id": "",
                "reason": debt_reasons[0],
            }
        )
    else:
        derived.append(debt_total)
        cash_candidates = [
            fact
            for fact in direct.facts
            if fact.metric == Metric.CASH_AND_CASH_EQUIVALENTS
            and fact.period.end == debt_total.period.end
            and fact.filing_date == debt_total.filing_date
        ]
        if len(cash_candidates) != 1:
            denials.append(
                {
                    "metric": Metric.NET_DEBT.value,
                    "source_semantic": "",
                    "source_document_id": debt_total.source_document_id,
                    "reason": (
                        "missing_cash"
                        if not cash_candidates
                        else "source_conflict"
                    ),
                }
            )
        else:
            net_debt, net_reasons = derive_net_debt(
                debt_total,
                cash_candidates[0],
            )
            if net_debt is None:
                denials.append(
                    {
                        "metric": Metric.NET_DEBT.value,
                        "source_semantic": cash_candidates[0].semantic_mapping,
                        "source_document_id": debt_total.source_document_id,
                        "reason": net_reasons[0],
                    }
                )
            else:
                derived.append(net_debt)
    return DebtLiquidityBatch(
        facts=tuple([*direct.facts, *derived]),
        direct_facts=direct.facts,
        denials=tuple(denials),
        completeness=completeness,
        sector_route=route,
        extracted_occurrences=direct.extracted_occurrences,
        exact_duplicates_suppressed=direct.exact_duplicates_suppressed,
        source_conflicts=direct.source_conflicts,
        source_candidates=source_candidates,
    )


def _payload_semantics(payload: Mapping[str, object]) -> set[str]:
    facts = payload.get("facts")
    if not isinstance(facts, Mapping):
        return set()
    return {
        f"{namespace}:{tag}"
        for namespace, concepts in facts.items()
        if isinstance(concepts, Mapping)
        for tag in concepts
    }


def extract_sec_debt_liquidity_occurrences(
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
    selected_semantics = set(REGISTRY_BY_SEMANTIC) | TOTAL_LIABILITY_SEMANTICS
    selected_semantics |= UNSUPPORTED_DEBT_SEMANTICS
    output: list[OfficialFinancialOccurrence] = []
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
                if (
                    not isinstance(row, Mapping)
                    or row.get("form") not in FORMAL_FORMS
                ):
                    continue
                value = _decimal(row.get("val"))
                if value is None:
                    continue
                unit = str(source_unit)
                output.append(
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
    return tuple(output)


def build_sec_debt_liquidity_batch(
    payload: Mapping[str, object],
    *,
    raw_payload_sha256: str,
    as_of_date: date,
    analysis_framework: str,
    holding_company: bool = False,
) -> DebtLiquidityBatch:
    semantics = _payload_semantics(payload)
    unsupported = sorted(semantics & UNSUPPORTED_DEBT_SEMANTICS)
    occurrences = extract_sec_debt_liquidity_occurrences(
        payload,
        raw_payload_sha256=raw_payload_sha256,
    )
    return build_debt_liquidity_batch(
        occurrences,
        as_of_date=as_of_date,
        analysis_framework=analysis_framework,
        statement_inventory_complete=bool(payload.get("facts")),
        unsupported_semantics=unsupported,
        holding_company=holding_company,
        source_candidates=len(occurrences),
    )


def _semantic_from_account_id(account_id: str) -> str | None:
    if "_" not in account_id:
        return None
    namespace, tag = account_id.split("_", maxsplit=1)
    return f"{namespace}:{tag}"


def promote_opendart_debt_liquidity_facts(
    filing: Filing,
    rows_by_basis: Mapping[str, list[dict[str, object]]],
    xbrl_facts: Iterable[XbrlFact],
    *,
    raw_payload_sha256: str,
    as_of_date: date,
    analysis_framework: str,
    holding_company: bool = False,
) -> DebtLiquidityBatch:
    cfs_rows = [
        row
        for row in rows_by_basis.get("CFS", [])
        if row.get("sj_div") == "BS"
    ]
    ofs_rows = [
        row
        for row in rows_by_basis.get("OFS", [])
        if row.get("sj_div") == "BS"
    ]
    selected_rows = cfs_rows or ofs_rows
    source_basis = "CFS" if cfs_rows else "OFS"
    statement_basis = "consolidated" if source_basis == "CFS" else "separate"
    fiscal_period = _FISCAL_PERIOD_BY_REPORT_CODE.get(filing.report_code)
    facts = tuple(xbrl_facts)
    occurrences: list[OfficialFinancialOccurrence] = []
    pre_denials: list[dict[str, str]] = []
    unsupported: list[str] = []
    candidate_count = 0
    recognized = set(REGISTRY_BY_SEMANTIC) | TOTAL_LIABILITY_SEMANTICS
    recognized |= UNSUPPORTED_DEBT_SEMANTICS
    for row in selected_rows:
        account_id = str(row.get("account_id") or "")
        semantic = _semantic_from_account_id(account_id)
        if semantic not in recognized:
            continue
        candidate_count += 1
        if semantic in UNSUPPORTED_DEBT_SEMANTICS:
            unsupported.append(semantic)
        source_identity = (
            str(row.get("rcept_no") or "") == filing.receipt_no
            and str(row.get("reprt_code") or "") == filing.report_code
            and str(row.get("bsns_year") or "") == str(filing.business_year)
            and str(row.get("corp_code") or "") == filing.corp_code
            and str(row.get("fs_div") or "") == source_basis
        )
        value = _decimal(row.get("thstrm_amount"))
        currency = str(row.get("currency") or "").upper()
        if not source_identity:
            pre_denials.append(
                {
                    "metric": "debt_liquidity",
                    "source_semantic": semantic or "",
                    "source_document_id": filing.receipt_no,
                    "reason": "filing_identity_mismatch",
                }
            )
            continue
        if value is None or currency != "KRW" or fiscal_period is None:
            pre_denials.append(
                {
                    "metric": "debt_liquidity",
                    "source_semantic": semantic or "",
                    "source_document_id": filing.receipt_no,
                    "reason": "source_amount_currency_or_period_missing",
                }
            )
            continue
        match = reconcile_xbrl_instant_fact(
            facts,
            taxonomy_element=account_id.split("_", maxsplit=1)[-1],
            value=value,
            unit_ref="KRW",
            statement_basis=statement_basis,
            entity_identifier=filing.corp_code,
        )
        if match is None:
            pre_denials.append(
                {
                    "metric": "debt_liquidity",
                    "source_semantic": semantic or "",
                    "source_document_id": filing.receipt_no,
                    "reason": "exact_xbrl_instant_context_unresolved",
                }
            )
            continue
        namespace, tag = account_id.split("_", maxsplit=1)
        occurrences.append(
            OfficialFinancialOccurrence(
                issuer_id=f"opendart:{filing.corp_code}",
                value=value,
                currency=currency,
                unit=str(match.unit_ref or ""),
                period_start=None,
                period_end=match.context.period_end,
                fiscal_year=filing.business_year,
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
                source_column="thstrm_amount",
            )
        )
    batch = build_debt_liquidity_batch(
        occurrences,
        as_of_date=as_of_date,
        analysis_framework=analysis_framework,
        statement_inventory_complete=bool(selected_rows and fiscal_period),
        unsupported_semantics=tuple(sorted(set(unsupported))),
        holding_company=holding_company,
        source_candidates=candidate_count,
    )
    return replace(batch, denials=tuple([*pre_denials, *batch.denials]))


def registry_audit() -> tuple[dict[str, object], ...]:
    return tuple(
        {
            "canonical_metric": entry.metric.value,
            "source_semantic": entry.semantic,
            "role": entry.role.value,
            "component_group": entry.component_group,
            "priority": entry.priority,
        }
        for entry in DEBT_LIQUIDITY_SEMANTIC_REGISTRY
    )
