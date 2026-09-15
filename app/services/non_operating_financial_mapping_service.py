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
from app.services.opendart_xbrl_service import XbrlFact, reconcile_xbrl_duration_fact
from app.services.working_capital_evidence_service import OfficialFinancialOccurrence


CONTRACT_VERSION = "non-operating-financial-income-effects-v1"
NET_FINANCIAL_EFFECT_FORMULA = "financial_income_minus_financial_cost"
NO_UNIVERSAL_NON_OPERATING_TOTAL_POLICY = "NO_UNIVERSAL_NON_OPERATING_TOTAL"
NO_NORMALIZED_EARNINGS_POLICY = "NO_ADJUSTED_OR_NORMALIZED_EARNINGS"

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
ANNUAL_FORMS = {"10-K", "10-K/A", "20-F", "20-F/A", "40-F", "40-F/A"}


class EconomicRole(StrEnum):
    INCOME = "INCOME"
    EXPENSE = "EXPENSE"
    GAIN = "GAIN"
    LOSS = "LOSS"
    NET_EFFECT = "NET_EFFECT"
    BROAD_CONTEXT = "BROAD_CONTEXT"
    INVESTMENT_RESULT = "INVESTMENT_RESULT"
    TAX_EFFECT = "TAX_EFFECT"
    CONTINUING_RESULT = "CONTINUING_RESULT"
    DISCONTINUED_RESULT = "DISCONTINUED_RESULT"


class PresentationType(StrEnum):
    DIRECT_AGGREGATE = "DIRECT_AGGREGATE"
    DIRECT_COMPONENT = "DIRECT_COMPONENT"
    BROAD_CONTEXT = "BROAD_CONTEXT"
    DERIVED_AGGREGATE = "DERIVED_AGGREGATE"


class SectorRoute(StrEnum):
    GENERIC_OPERATING_COMPANY = "GENERIC_OPERATING_COMPANY"
    CONTEXT_ONLY = "CONTEXT_ONLY"
    SECTOR_FRAMEWORK_REQUIRED = "SECTOR_FRAMEWORK_REQUIRED"


@dataclass(frozen=True)
class NonOperatingRegistryEntry:
    metric: Metric
    namespace: str
    tag: str
    economic_role: EconomicRole
    presentation_type: PresentationType
    financial_effect_scope: str
    continuity_scope: str = "unspecified"
    parent_scope: str | None = None
    priority: int = 100

    @property
    def semantic(self) -> str:
        return f"{self.namespace}:{self.tag}"


NON_OPERATING_SEMANTIC_REGISTRY = (
    NonOperatingRegistryEntry(
        Metric.FINANCIAL_INCOME,
        "ifrs-full",
        "FinanceIncome",
        EconomicRole.INCOME,
        PresentationType.DIRECT_AGGREGATE,
        "finance_income_aggregate",
    ),
    NonOperatingRegistryEntry(
        Metric.FINANCIAL_COST,
        "ifrs-full",
        "FinanceCosts",
        EconomicRole.EXPENSE,
        PresentationType.DIRECT_AGGREGATE,
        "finance_cost_aggregate",
    ),
    NonOperatingRegistryEntry(
        Metric.NET_FINANCIAL_INCOME_EFFECT,
        "ifrs-full",
        "FinanceIncomeCost",
        EconomicRole.NET_EFFECT,
        PresentationType.DIRECT_AGGREGATE,
        "finance_net_aggregate",
        priority=110,
    ),
    NonOperatingRegistryEntry(
        Metric.INTEREST_INCOME,
        "dart",
        "InterestIncomeFinanceIncome",
        EconomicRole.INCOME,
        PresentationType.DIRECT_COMPONENT,
        "interest_income_component",
        parent_scope="finance_income_aggregate",
    ),
    NonOperatingRegistryEntry(
        Metric.INTEREST_EXPENSE,
        "dart",
        "InterestExpenseFinanceExpense",
        EconomicRole.EXPENSE,
        PresentationType.DIRECT_COMPONENT,
        "interest_expense_component",
        parent_scope="finance_cost_aggregate",
    ),
    NonOperatingRegistryEntry(
        Metric.INTEREST_INCOME,
        "ifrs-full",
        "InterestIncome",
        EconomicRole.INCOME,
        PresentationType.DIRECT_COMPONENT,
        "interest_income_component",
        parent_scope="finance_income_aggregate",
    ),
    NonOperatingRegistryEntry(
        Metric.INTEREST_EXPENSE,
        "ifrs-full",
        "InterestExpense",
        EconomicRole.EXPENSE,
        PresentationType.DIRECT_COMPONENT,
        "interest_expense_component",
        parent_scope="finance_cost_aggregate",
    ),
    NonOperatingRegistryEntry(
        Metric.INTEREST_INCOME,
        "us-gaap",
        "InterestIncomeNonoperating",
        EconomicRole.INCOME,
        PresentationType.DIRECT_COMPONENT,
        "interest_income_component",
        parent_scope="finance_income_aggregate",
    ),
    NonOperatingRegistryEntry(
        Metric.INTEREST_EXPENSE,
        "us-gaap",
        "InterestExpenseNonOperating",
        EconomicRole.EXPENSE,
        PresentationType.DIRECT_COMPONENT,
        "interest_expense_component",
        parent_scope="finance_cost_aggregate",
    ),
    NonOperatingRegistryEntry(
        Metric.FOREIGN_EXCHANGE_GAIN,
        "ifrs-full",
        "NetForeignExchangeGain",
        EconomicRole.GAIN,
        PresentationType.DIRECT_COMPONENT,
        "foreign_exchange_gain_component",
        parent_scope="finance_income_aggregate",
    ),
    NonOperatingRegistryEntry(
        Metric.FOREIGN_EXCHANGE_LOSS,
        "ifrs-full",
        "NetForeignExchangeLoss",
        EconomicRole.LOSS,
        PresentationType.DIRECT_COMPONENT,
        "foreign_exchange_loss_component",
        parent_scope="finance_cost_aggregate",
    ),
    NonOperatingRegistryEntry(
        Metric.FOREIGN_EXCHANGE_NET_EFFECT,
        "us-gaap",
        "ForeignCurrencyTransactionGainLossBeforeTax",
        EconomicRole.NET_EFFECT,
        PresentationType.DIRECT_AGGREGATE,
        "foreign_exchange_net_effect",
    ),
    NonOperatingRegistryEntry(
        Metric.OTHER_INCOME_CONTEXT,
        "dart",
        "OtherGains",
        EconomicRole.BROAD_CONTEXT,
        PresentationType.BROAD_CONTEXT,
        "other_income_broad_context",
    ),
    NonOperatingRegistryEntry(
        Metric.OTHER_EXPENSE_CONTEXT,
        "dart",
        "OtherLosses",
        EconomicRole.BROAD_CONTEXT,
        PresentationType.BROAD_CONTEXT,
        "other_expense_broad_context",
    ),
    NonOperatingRegistryEntry(
        Metric.OTHER_INCOME_CONTEXT,
        "ifrs-full",
        "OtherIncome",
        EconomicRole.BROAD_CONTEXT,
        PresentationType.BROAD_CONTEXT,
        "other_income_broad_context",
    ),
    NonOperatingRegistryEntry(
        Metric.ASSET_DISPOSAL_GAIN,
        "ifrs-full",
        "GainsOnDisposalsOfPropertyPlantAndEquipment",
        EconomicRole.GAIN,
        PresentationType.DIRECT_COMPONENT,
        "ppe_disposal_gain_component",
        parent_scope="other_income_broad_context",
    ),
    NonOperatingRegistryEntry(
        Metric.ASSET_DISPOSAL_LOSS,
        "ifrs-full",
        "LossesOnDisposalsOfPropertyPlantAndEquipment",
        EconomicRole.LOSS,
        PresentationType.DIRECT_COMPONENT,
        "ppe_disposal_loss_component",
        parent_scope="other_expense_broad_context",
    ),
    NonOperatingRegistryEntry(
        Metric.ASSET_DISPOSAL_RESULT_CONTEXT,
        "us-gaap",
        "GainLossOnSaleOfPropertyPlantEquipment",
        EconomicRole.NET_EFFECT,
        PresentationType.DIRECT_COMPONENT,
        "ppe_disposal_net_result",
    ),
    NonOperatingRegistryEntry(
        Metric.FAIR_VALUE_GAIN,
        "dart",
        "GainsOnValuationOfFairValueFinancialAsset",
        EconomicRole.GAIN,
        PresentationType.DIRECT_COMPONENT,
        "financial_instrument_fair_value_gain",
        parent_scope="finance_income_aggregate",
    ),
    NonOperatingRegistryEntry(
        Metric.FAIR_VALUE_LOSS,
        "dart",
        "LossesOnValuationOfFairValueFinancialAsset",
        EconomicRole.LOSS,
        PresentationType.DIRECT_COMPONENT,
        "financial_instrument_fair_value_loss",
        parent_scope="finance_cost_aggregate",
    ),
    NonOperatingRegistryEntry(
        Metric.EQUITY_METHOD_RESULT_CONTEXT,
        "ifrs-full",
        "ShareOfProfitLossOfAssociatesAndJointVenturesAccountedForUsingEquityMethod",
        EconomicRole.INVESTMENT_RESULT,
        PresentationType.DIRECT_COMPONENT,
        "equity_method_investment_result",
    ),
    NonOperatingRegistryEntry(
        Metric.INCOME_TAX_EXPENSE,
        "ifrs-full",
        "IncomeTaxExpenseContinuingOperations",
        EconomicRole.TAX_EFFECT,
        PresentationType.DIRECT_AGGREGATE,
        "income_tax_expense_continuing_operations",
        continuity_scope="continuing_operations",
    ),
    NonOperatingRegistryEntry(
        Metric.INCOME_TAX_EXPENSE,
        "us-gaap",
        "IncomeTaxExpenseBenefit",
        EconomicRole.TAX_EFFECT,
        PresentationType.DIRECT_AGGREGATE,
        "income_tax_expense_benefit",
        continuity_scope="continuing_operations",
    ),
    NonOperatingRegistryEntry(
        Metric.CONTINUING_OPERATIONS_INCOME,
        "ifrs-full",
        "ProfitLossFromContinuingOperations",
        EconomicRole.CONTINUING_RESULT,
        PresentationType.DIRECT_AGGREGATE,
        "continuing_operations_result",
        continuity_scope="continuing_operations",
    ),
    NonOperatingRegistryEntry(
        Metric.CONTINUING_OPERATIONS_INCOME,
        "us-gaap",
        "IncomeLossFromContinuingOperations",
        EconomicRole.CONTINUING_RESULT,
        PresentationType.DIRECT_AGGREGATE,
        "continuing_operations_result",
        continuity_scope="continuing_operations",
    ),
    NonOperatingRegistryEntry(
        Metric.DISCONTINUED_OPERATIONS_RESULT,
        "ifrs-full",
        "ProfitLossFromDiscontinuedOperations",
        EconomicRole.DISCONTINUED_RESULT,
        PresentationType.DIRECT_AGGREGATE,
        "discontinued_operations_result",
        continuity_scope="discontinued_operations",
    ),
    NonOperatingRegistryEntry(
        Metric.DISCONTINUED_OPERATIONS_RESULT,
        "us-gaap",
        "IncomeLossFromDiscontinuedOperationsNetOfTax",
        EconomicRole.DISCONTINUED_RESULT,
        PresentationType.DIRECT_AGGREGATE,
        "discontinued_operations_result_net_of_tax",
        continuity_scope="discontinued_operations",
    ),
)

REGISTRY_BY_SEMANTIC = {
    entry.semantic: entry for entry in NON_OPERATING_SEMANTIC_REGISTRY
}

EXCLUDED_SEMANTIC_REASONS = {
    "us-gaap:OperatingIncomeLoss": "operating_metric_not_non_operating",
    "ifrs-full:ProfitLossFromOperatingActivities": (
        "operating_metric_not_non_operating"
    ),
    "ifrs-full:Revenue": "revenue_not_non_operating",
    "ifrs-full:OtherComprehensiveIncomeNetOfTaxExchangeDifferencesOnTranslation": (
        "oci_translation_not_profit_or_loss_fx"
    ),
    "ifrs-full:GainsLossesOnExchangeDifferencesOnTranslationNetOfTax": (
        "oci_translation_not_profit_or_loss_fx"
    ),
    "ifrs-full:EffectOfExchangeRateChangesOnCashAndCashEquivalents": (
        "cash_flow_fx_not_income_statement_fx"
    ),
    "dart:AdjustmentsForGainOnForeignExchangeTranslations": (
        "cash_flow_adjustment_not_direct_income_statement_effect"
    ),
    "dart:AdjustmentsForGainsOnChangeInFairValueOfDerivatives": (
        "cash_flow_adjustment_not_direct_income_statement_effect"
    ),
    "dart:AdjustmentsForLossesOnChangeInFairValueOfDerivatives": (
        "cash_flow_adjustment_not_direct_income_statement_effect"
    ),
}

_FINANCIAL_SECTOR_FRAMEWORKS = {
    "bank",
    "insurance",
    "reinsurance",
    "financial_institution",
    "bank_or_insurer",
}
_CONTEXT_ONLY_FRAMEWORKS = {"holding_company", "pre_profit_technology", "biotech"}

DENIAL_REASON_TAXONOMY = frozenset(
    {
        "sector_not_applicable",
        "aggregate_child_overlap",
        "period_context_unresolved",
        "period_mismatch",
        "currency_mismatch",
        "entity_scope_mismatch",
        "statement_basis_mismatch",
        "attribution_basis_mismatch",
        "continuing_discontinued_mismatch",
        "broad_context_not_specific",
        "sign_semantics_unresolved",
        "source_conflict",
        "exact_context_unresolved",
        "component_scope_incomplete",
    }
)


@dataclass(frozen=True)
class NonOperatingMappingBatch:
    facts: tuple[FinancialFact, ...]
    direct_facts: tuple[FinancialFact, ...]
    derived_facts: tuple[FinancialFact, ...]
    denials: tuple[dict[str, str], ...]
    overlap_events: tuple[dict[str, str], ...]
    sector_route: SectorRoute
    source_candidates: int
    extracted_occurrences: int
    exact_duplicates_suppressed: int
    source_conflicts: int
    aggregate_child_overlap_conflict_count: int
    aggregate_precedence_count: int
    child_detail_preserved_count: int
    sign_semantics_unresolved_count: int


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


def _flow_period(occurrence: OfficialFinancialOccurrence) -> PeriodIdentity | None:
    start = occurrence.period_start
    end = occurrence.period_end
    fiscal_period = occurrence.fiscal_period or ""
    if start is None or end is None or occurrence.fiscal_year is None or end < start:
        return None
    duration = (end - start).days + 1
    fiscal_quarter = (
        int(fiscal_period[1])
        if fiscal_period in {"Q1", "Q2", "Q3", "Q4"}
        else 4
        if fiscal_period == "FY"
        else None
    )
    if fiscal_period == "FY":
        if occurrence.source_document_type not in {*ANNUAL_FORMS, "11011"}:
            return None
        if not 330 <= duration <= 400:
            return None
        period_type = PeriodType.FY
    elif fiscal_quarter is not None:
        if occurrence.source_provider.startswith("opendart"):
            if occurrence.source_column in {"thstrm_add_amount", "frmtrm_add_amount"}:
                period_type = PeriodType.YTD
            elif occurrence.source_column in {
                "thstrm_amount",
                "frmtrm_amount",
                "frmtrm_q_amount",
            } and duration <= 120:
                period_type = PeriodType.QTD
            else:
                return None
        else:
            frame = (occurrence.frame or "").upper()
            if frame.endswith("YTD"):
                period_type = PeriodType.YTD
            elif 1 <= duration <= 120:
                period_type = PeriodType.QTD
            elif fiscal_quarter in {2, 3, 4} and duration <= 310:
                period_type = PeriodType.YTD
            else:
                return None
    else:
        return None
    return PeriodIdentity(
        start=start,
        end=end,
        period_type=period_type,
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
            occurrence.period_start.isoformat() if occurrence.period_start else "",
            occurrence.period_end.isoformat() if occurrence.period_end else "",
            occurrence.unit or "",
            occurrence.entity_scope or "",
            occurrence.statement_basis or "",
            occurrence.frame or "",
            occurrence.source_column or "",
        )
    )
    return f"non-operating-occurrence:{hashlib.sha256(identity.encode()).hexdigest()[:24]}"


def _reported_fact_id(
    occurrence: OfficialFinancialOccurrence,
    entry: NonOperatingRegistryEntry,
    period: PeriodIdentity,
) -> str:
    identity = "|".join(
        (
            CONTRACT_VERSION,
            occurrence.issuer_id,
            entry.metric.value,
            entry.financial_effect_scope,
            period.start.isoformat(),
            period.end.isoformat(),
            period.period_type.value,
            occurrence.entity_scope or "",
            occurrence.statement_basis or "",
            occurrence.currency or "",
            _occurrence_id(occurrence),
        )
    )
    return f"non-operating-reported:{hashlib.sha256(identity.encode()).hexdigest()[:24]}"


def _denial(
    occurrence: OfficialFinancialOccurrence | None,
    reason: str,
    *,
    metric: str = "non_operating_financial_effect",
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
    period = _flow_period(occurrence)
    if period is None:
        return None, "period_context_unresolved"
    cautions = ["recurrence_not_determined", "not_normalized_earnings"]
    if entry.presentation_type == PresentationType.BROAD_CONTEXT:
        cautions.append("broad_context_not_specific")
    if entry.economic_role == EconomicRole.INVESTMENT_RESULT:
        cautions.append("equity_method_separate_investment_result")
    if entry.economic_role == EconomicRole.TAX_EFFECT:
        cautions.extend(("tax_not_operating_performance", "effective_tax_rate_not_derived"))
    if entry.continuity_scope == "discontinued_operations":
        cautions.append("discontinued_not_ordinary_operating_performance")
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
            source_sign="source_reported_signed_amount",
            normalization_transform=transform,
            quality="REPORTED_VERIFIED",
            eligibility=EligibilityStatus.ELIGIBLE,
            cautions=tuple(cautions),
            restatement_policy_id="latest-authoritative-exact-semantic-v1",
            as_of_date=as_of_date,
            source_available_at=occurrence.filing_date,
            attribution_basis="total",
            financial_effect_scope=entry.financial_effect_scope,
            economic_role=entry.economic_role.value,
            presentation_type=entry.presentation_type.value,
            continuity_scope=entry.continuity_scope,
        ),
        None,
    )


def _economic_key(occurrence: OfficialFinancialOccurrence) -> tuple[object, ...]:
    return (
        occurrence.issuer_id,
        occurrence.semantic,
        occurrence.period_start,
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
        fact.attribution_basis,
        fact.source_document_id,
    )


def _mark_overlap_hierarchy(
    facts: Sequence[FinancialFact],
) -> tuple[list[FinancialFact], list[dict[str, str]], int, int, int]:
    output = list(facts)
    events: list[dict[str, str]] = []
    conflicts = 0
    aggregate_precedence = 0
    children_preserved = 0
    by_context: dict[tuple[object, ...], list[FinancialFact]] = {}
    for fact in output:
        by_context.setdefault(_fact_context_key(fact), []).append(fact)
    for context_facts in by_context.values():
        for parent_scope in (
            "finance_income_aggregate",
            "finance_cost_aggregate",
            "other_income_broad_context",
            "other_expense_broad_context",
        ):
            parents = [
                fact
                for fact in context_facts
                if fact.financial_effect_scope == parent_scope
            ]
            children = [
                fact
                for fact in context_facts
                if REGISTRY_BY_SEMANTIC[fact.semantic_mapping].parent_scope
                == parent_scope
            ]
            if not parents or not children:
                continue
            conflicts += 1
            aggregate_precedence += len(children)
            children_preserved += len(children)
            events.append(
                {
                    "reason": "aggregate_child_overlap",
                    "parent_scope": parent_scope,
                    "parent_fact_ids": ",".join(fact.fact_id for fact in parents),
                    "child_fact_ids": ",".join(fact.fact_id for fact in children),
                    "action": "aggregate_precedence_children_preserved_no_summation",
                }
            )
            for index, fact in enumerate(output):
                if fact in parents:
                    output[index] = replace(
                        fact,
                        cautions=tuple(
                            dict.fromkeys(
                                [*fact.cautions, "children_present_no_double_count"]
                            )
                        ),
                    )
                elif fact in children:
                    output[index] = replace(
                        fact,
                        cautions=tuple(
                            dict.fromkeys(
                                [*fact.cautions, "aggregate_parent_present_no_summation"]
                            )
                        ),
                    )
    return output, events, conflicts, aggregate_precedence, children_preserved


def canonicalize_non_operating_occurrences(
    occurrences: Iterable[OfficialFinancialOccurrence],
    *,
    as_of_date: date,
    analysis_framework: str,
) -> NonOperatingMappingBatch:
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
        eligible = [
            item
            for item in group
            if item.filing_date is not None and item.filing_date <= as_of_date
        ]
        if not eligible:
            denials.append(_denial(group[0], "filing_date_unavailable_or_after_as_of"))
            continue
        latest_date = max(item.filing_date for item in eligible if item.filing_date)
        latest = [item for item in eligible if item.filing_date == latest_date]
        latest_document = max(item.source_document_id or "" for item in latest)
        authoritative = [
            item for item in latest if (item.source_document_id or "") == latest_document
        ]
        if len({item.value for item in authoritative}) != 1:
            conflicts += 1
            denials.append(_denial(authoritative[0], "source_conflict"))
            continue
        duplicates += len(authoritative) - 1
        fact, reason = _canonicalize_occurrence(
            authoritative[0],
            as_of_date=as_of_date,
            route=route,
        )
        if fact is None:
            denials.append(_denial(authoritative[0], reason or "canonicalization_blocked"))
        else:
            facts.append(fact)

    exact_groups: dict[tuple[object, ...], list[FinancialFact]] = {}
    for fact in facts:
        exact_groups.setdefault(
            (
                _fact_context_key(fact),
                fact.metric,
                fact.financial_effect_scope,
                fact.continuity_scope,
            ),
            [],
        ).append(fact)
    selected: list[FinancialFact] = []
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
        selected.append(
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
        overlap_events,
        overlap_conflicts,
        aggregate_precedence,
        child_details,
    ) = _mark_overlap_hierarchy(selected)
    direct_facts.sort(
        key=lambda fact: (
            fact.issuer_id,
            fact.period.end,
            fact.period.period_type.value,
            fact.metric.value,
            fact.fact_id,
        )
    )
    return NonOperatingMappingBatch(
        facts=tuple(direct_facts),
        direct_facts=tuple(direct_facts),
        derived_facts=(),
        denials=tuple(denials),
        overlap_events=tuple(overlap_events),
        sector_route=route,
        source_candidates=len(values),
        extracted_occurrences=len(values),
        exact_duplicates_suppressed=duplicates,
        source_conflicts=conflicts,
        aggregate_child_overlap_conflict_count=overlap_conflicts,
        aggregate_precedence_count=aggregate_precedence,
        child_detail_preserved_count=child_details,
        sign_semantics_unresolved_count=0,
    )


def _derived_fact_id(income: FinancialFact, cost: FinancialFact) -> str:
    identity = "|".join(
        (
            CONTRACT_VERSION,
            NET_FINANCIAL_EFFECT_FORMULA,
            income.fact_id,
            cost.fact_id,
            income.period.start.isoformat(),
            income.period.end.isoformat(),
            income.currency,
            income.entity_scope,
            income.statement_basis,
        )
    )
    return f"non-operating-derived:{hashlib.sha256(identity.encode()).hexdigest()[:24]}"


def _derive_net_financial_effects(
    direct_facts: Sequence[FinancialFact],
    *,
    as_of_date: date,
) -> tuple[tuple[FinancialFact, ...], tuple[dict[str, str], ...], int]:
    contexts: dict[tuple[object, ...], list[FinancialFact]] = {}
    for fact in direct_facts:
        contexts.setdefault(_fact_context_key(fact), []).append(fact)
    derived: list[FinancialFact] = []
    denials: list[dict[str, str]] = []
    sign_unresolved = 0
    for context_facts in contexts.values():
        direct_net = [
            fact
            for fact in context_facts
            if fact.metric == Metric.NET_FINANCIAL_INCOME_EFFECT
        ]
        income = [fact for fact in context_facts if fact.metric == Metric.FINANCIAL_INCOME]
        cost = [fact for fact in context_facts if fact.metric == Metric.FINANCIAL_COST]
        if direct_net and income and cost:
            denials.append(
                {
                    "metric": Metric.NET_FINANCIAL_INCOME_EFFECT.value,
                    "source_semantic": direct_net[0].semantic_mapping,
                    "source_document_id": direct_net[0].source_document_id,
                    "reason": "official_direct_net_precedence",
                }
            )
            continue
        if not income and not cost:
            continue
        if len(income) != 1 or len(cost) != 1:
            template = (income or cost)[0]
            denials.append(
                {
                    "metric": Metric.NET_FINANCIAL_INCOME_EFFECT.value,
                    "source_semantic": template.semantic_mapping,
                    "source_document_id": template.source_document_id,
                    "reason": "component_scope_incomplete",
                }
            )
            continue
        income_fact, cost_fact = income[0], cost[0]
        if income_fact.value < 0 or cost_fact.value < 0:
            sign_unresolved += 1
            denials.append(
                {
                    "metric": Metric.NET_FINANCIAL_INCOME_EFFECT.value,
                    "source_semantic": (
                        f"{income_fact.semantic_mapping}|{cost_fact.semantic_mapping}"
                    ),
                    "source_document_id": income_fact.source_document_id,
                    "reason": "sign_semantics_unresolved",
                }
            )
            continue
        raw_sha = hashlib.sha256(
            f"{income_fact.raw_payload_sha256}|{cost_fact.raw_payload_sha256}".encode()
        ).hexdigest()
        fact_id = _derived_fact_id(income_fact, cost_fact)
        derived.append(
            FinancialFact(
                fact_id=fact_id,
                issuer_id=income_fact.issuer_id,
                metric=Metric.NET_FINANCIAL_INCOME_EFFECT,
                value=income_fact.value - cost_fact.value,
                currency=income_fact.currency,
                unit=income_fact.unit,
                period=income_fact.period,
                entity_scope=income_fact.entity_scope,
                statement_basis=income_fact.statement_basis,
                reported_or_derived="derived",
                source_provider="canonical_financial_derivation",
                source_document_id=income_fact.source_document_id,
                filing_date=max(income_fact.filing_date, cost_fact.filing_date),
                source_occurrence_id=f"derived:{fact_id}",
                raw_payload_sha256=raw_sha,
                semantic_mapping=NET_FINANCIAL_EFFECT_FORMULA,
                fact_type=FactType.DERIVED_METRIC,
                source_document_type=income_fact.source_document_type,
                source_semantic=NET_FINANCIAL_EFFECT_FORMULA,
                normalization_transform="financial_income_minus_positive_cost_magnitude",
                derivation_formula=NET_FINANCIAL_EFFECT_FORMULA,
                derivation_version=CONTRACT_VERSION,
                input_fact_ids=(income_fact.fact_id, cost_fact.fact_id),
                quality="DERIVED_VERIFIED",
                eligibility=EligibilityStatus.ELIGIBLE,
                cautions=(
                    "aggregate_only_no_child_summation",
                    "recurrence_not_determined",
                    "not_normalized_earnings",
                ),
                restatement_policy_id="same-document-compatible-aggregate-inputs-v1",
                as_of_date=as_of_date,
                source_available_at=max(
                    income_fact.source_available_at or income_fact.filing_date,
                    cost_fact.source_available_at or cost_fact.filing_date,
                ),
                attribution_basis=income_fact.attribution_basis,
                financial_effect_scope="finance_net_aggregate",
                economic_role=EconomicRole.NET_EFFECT.value,
                presentation_type=PresentationType.DERIVED_AGGREGATE.value,
                continuity_scope="unspecified",
            )
        )
    return tuple(derived), tuple(denials), sign_unresolved


def build_non_operating_mapping_batch(
    occurrences: Iterable[OfficialFinancialOccurrence],
    *,
    as_of_date: date,
    analysis_framework: str,
    source_candidates: int | None = None,
) -> NonOperatingMappingBatch:
    direct = canonicalize_non_operating_occurrences(
        occurrences,
        as_of_date=as_of_date,
        analysis_framework=analysis_framework,
    )
    derived, derivation_denials, sign_unresolved = _derive_net_financial_effects(
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
        sign_semantics_unresolved_count=sign_unresolved,
    )


def extract_sec_non_operating_occurrences(
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
                        period_start=_date(row.get("start")),
                        period_end=_date(row.get("end")),
                        fiscal_year=(
                            int(str(row["fy"]))
                            if str(row.get("fy") or "").isdigit()
                            else None
                        ),
                        fiscal_period=(str(row.get("fp")) if row.get("fp") else None),
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
                        statement_basis="issuer_reported_income_statement",
                        frame=str(row.get("frame")) if row.get("frame") else None,
                        source_column="val",
                    )
                )
    return tuple(occurrences)


def build_sec_non_operating_mapping_batch(
    payload: Mapping[str, object],
    *,
    raw_payload_sha256: str,
    as_of_date: date,
    analysis_framework: str,
) -> NonOperatingMappingBatch:
    occurrences = extract_sec_non_operating_occurrences(
        payload,
        raw_payload_sha256=raw_payload_sha256,
    )
    return build_non_operating_mapping_batch(
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


def _opendart_columns(report_code: str) -> tuple[tuple[str, int, str], ...]:
    if report_code == "11011":
        return (
            ("thstrm_amount", 0, "FY"),
            ("frmtrm_amount", -1, "FY"),
            ("bfefrmtrm_amount", -2, "FY"),
        )
    fiscal_period = {"11013": "Q1", "11012": "Q2", "11014": "Q3"}.get(
        report_code
    )
    if fiscal_period is None:
        return ()
    if fiscal_period == "Q1":
        return (
            ("thstrm_amount", 0, fiscal_period),
            ("frmtrm_amount", -1, fiscal_period),
        )
    return (
        ("thstrm_amount", 0, fiscal_period),
        ("thstrm_add_amount", 0, fiscal_period),
        ("frmtrm_q_amount", -1, fiscal_period),
        ("frmtrm_add_amount", -1, fiscal_period),
    )


def promote_opendart_non_operating_facts(
    filing: Filing,
    rows_by_basis: Mapping[str, list[dict[str, object]]],
    xbrl_facts: Iterable[XbrlFact],
    *,
    raw_payload_sha256: str,
    as_of_date: date,
    analysis_framework: str,
) -> NonOperatingMappingBatch:
    cfs_rows = [
        row
        for row in rows_by_basis.get("CFS", [])
        if row.get("sj_div") in {"IS", "CIS"}
    ]
    ofs_rows = [
        row
        for row in rows_by_basis.get("OFS", [])
        if row.get("sj_div") in {"IS", "CIS"}
    ]
    selected_rows = cfs_rows or ofs_rows
    source_basis = "CFS" if cfs_rows else "OFS"
    statement_basis = "consolidated" if source_basis == "CFS" else "separate"
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
                    "metric": "non_operating_financial_effect",
                    "source_semantic": semantic or "",
                    "source_document_id": filing.receipt_no,
                    "reason": "filing_identity_mismatch",
                }
            )
            continue
        namespace, tag = account_id.split("_", maxsplit=1)
        for source_column, fiscal_year_offset, fiscal_period in _opendart_columns(
            filing.report_code
        ):
            value = _decimal(row.get(source_column))
            if value is None:
                continue
            candidate_count += 1
            currency = str(row.get("currency") or "").upper()
            if currency != "KRW":
                pre_denials.append(
                    {
                        "metric": "non_operating_financial_effect",
                        "source_semantic": semantic or "",
                        "source_document_id": filing.receipt_no,
                        "reason": "source_amount_currency_or_period_missing",
                    }
                )
                continue
            match = reconcile_xbrl_duration_fact(
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
                        "metric": "non_operating_financial_effect",
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
                    period_start=match.context.period_start,
                    period_end=match.context.period_end,
                    fiscal_year=filing.business_year + fiscal_year_offset,
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
    batch = build_non_operating_mapping_batch(
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
            "economic_role": entry.economic_role.value,
            "presentation_type": entry.presentation_type.value,
            "financial_effect_scope": entry.financial_effect_scope,
            "continuity_scope": entry.continuity_scope,
            "parent_scope": entry.parent_scope,
            "priority": entry.priority,
        }
        for entry in NON_OPERATING_SEMANTIC_REGISTRY
    )
