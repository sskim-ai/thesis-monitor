from __future__ import annotations

import hashlib
from dataclasses import dataclass, replace
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Iterable, Mapping

from app.services.cash_flow_capital_efficiency_service import (
    CapexScope,
    EligibilityDecision,
    EligibilityStatus,
    FactType,
    FinancialFact,
    Metric,
    PeriodIdentity,
    PeriodType,
    normalize_capex_cash_outflow,
)


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
RESTATEMENT_POLICY_ID = "sec-companyfacts-latest-authoritative-v1"


@dataclass(frozen=True)
class SemanticRegistryEntry:
    metric: Metric
    namespace: str
    tag: str
    statement_section: str
    economic_meaning: str
    sign_policy: str
    priority: int

    @property
    def semantic(self) -> str:
        return f"{self.namespace}:{self.tag}"


SEMANTIC_REGISTRY = (
    SemanticRegistryEntry(
        metric=Metric.OCF,
        namespace="us-gaap",
        tag="NetCashProvidedByUsedInOperatingActivities",
        statement_section="cash_flow_operating_activities",
        economic_meaning="net cash provided by or used in operating activities",
        sign_policy="economic_signed_amount",
        priority=100,
    ),
    SemanticRegistryEntry(
        metric=Metric.OCF,
        namespace="ifrs-full",
        tag="CashFlowsFromUsedInOperatingActivities",
        statement_section="cash_flow_operating_activities",
        economic_meaning="net cash from or used in operating activities",
        sign_policy="economic_signed_amount",
        priority=100,
    ),
    SemanticRegistryEntry(
        metric=Metric.CAPEX,
        namespace="us-gaap",
        tag="PaymentsToAcquirePropertyPlantAndEquipment",
        statement_section="cash_flow_investing_activities",
        economic_meaning="cash paid to acquire property plant and equipment",
        sign_policy="ppe_payment_cash_outflow",
        priority=100,
    ),
    SemanticRegistryEntry(
        metric=Metric.CAPEX,
        namespace="us-gaap",
        tag="PaymentsForAdditionsToPropertyPlantAndEquipment",
        statement_section="cash_flow_investing_activities",
        economic_meaning="cash paid for additions to property plant and equipment",
        sign_policy="ppe_payment_cash_outflow",
        priority=90,
    ),
    SemanticRegistryEntry(
        metric=Metric.CAPEX,
        namespace="ifrs-full",
        tag="PurchaseOfPropertyPlantAndEquipment",
        statement_section="cash_flow_investing_activities",
        economic_meaning="cash purchase of property plant and equipment",
        sign_policy="ppe_payment_cash_outflow",
        priority=100,
    ),
    SemanticRegistryEntry(
        metric=Metric.CAPEX,
        namespace="ifrs-full",
        tag="PurchaseOfPropertyPlantAndEquipmentClassifiedAsInvestingActivities",
        statement_section="cash_flow_investing_activities",
        economic_meaning="cash purchase of PPE classified as investing activities",
        sign_policy="ppe_payment_cash_outflow",
        priority=95,
    ),
)
REGISTRY_BY_SEMANTIC = {entry.semantic: entry for entry in SEMANTIC_REGISTRY}

REJECTED_SEMANTICS = {
    "us-gaap:NetCashProvidedByUsedInInvestingActivities": "generic_investing_cash_flow_not_ppe_capex",
    "us-gaap:PaymentsToAcquireBusinessesNetOfCashAcquired": "business_acquisition_excluded",
    "us-gaap:PaymentsToAcquireShorttermInvestments": "securities_purchase_excluded",
    "us-gaap:PaymentsToAcquireIntangibleAssets": "intangible_purchase_excluded",
    "us-gaap:PaymentsToAcquireProductiveAssets": "productive_assets_scope_ambiguous",
    "ifrs-full:CashFlowsFromUsedInInvestingActivities": "generic_investing_cash_flow_not_ppe_capex",
    "ifrs-full:PurchaseOfSubsidiariesNetOfCashAcquired": "business_acquisition_excluded",
    "ifrs-full:PurchaseOfIntangibleAssetsClassifiedAsInvestingActivities": "intangible_purchase_excluded",
}


@dataclass(frozen=True)
class OfficialFilingOccurrence:
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

    @property
    def semantic(self) -> str:
        return f"{self.namespace}:{self.tag}"


@dataclass(frozen=True)
class CanonicalizationBatch:
    facts: tuple[FinancialFact, ...]
    denials: tuple[dict[str, str], ...]
    extracted_occurrences: int
    exact_duplicates_suppressed: int
    conflicts: int


def _blocked(reason: str, occurrence: OfficialFilingOccurrence) -> EligibilityDecision:
    return EligibilityDecision(
        status=EligibilityStatus.BLOCKED,
        reasons=(reason,),
        audit={
            "issuer_id": occurrence.issuer_id,
            "source_document_id": occurrence.source_document_id,
            "source_semantic": occurrence.semantic,
        },
    )


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
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None


def _currency_from_unit(unit: str) -> str | None:
    normalized = unit.strip().upper()
    if len(normalized) == 3 and normalized.isalpha():
        return normalized
    return None


def _fiscal_quarter(fiscal_period: str | None) -> int | None:
    if fiscal_period in {"Q1", "Q2", "Q3", "Q4"}:
        return int(fiscal_period[1])
    return None


def classify_flow_period(occurrence: OfficialFilingOccurrence) -> PeriodIdentity | None:
    if (
        occurrence.period_start is None
        or occurrence.period_end is None
        or occurrence.fiscal_year is None
    ):
        return None
    duration = (occurrence.period_end - occurrence.period_start).days + 1
    form = occurrence.source_document_type or ""
    if occurrence.fiscal_period == "FY" and 330 <= duration <= 400:
        period_type = PeriodType.FY
        fiscal_quarter = 4
    elif form in ANNUAL_FORMS and 330 <= duration <= 400:
        period_type = PeriodType.FY
        fiscal_quarter = 4
    else:
        fiscal_quarter = _fiscal_quarter(occurrence.fiscal_period)
        if fiscal_quarter not in {1, 2, 3}:
            return None
        period_type = PeriodType.YTD
    return PeriodIdentity(
        start=occurrence.period_start,
        end=occurrence.period_end,
        period_type=period_type,
        fiscal_year=occurrence.fiscal_year,
        fiscal_quarter=fiscal_quarter,
    )


def _occurrence_id(occurrence: OfficialFilingOccurrence) -> str:
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
        )
    )
    return f"sec-occurrence:{hashlib.sha256(payload.encode()).hexdigest()[:24]}"


def _reported_fact_id(
    occurrence: OfficialFilingOccurrence,
    metric: Metric,
    period: PeriodIdentity,
) -> str:
    payload = "|".join(
        (
            occurrence.issuer_id,
            metric.value,
            period.start.isoformat(),
            period.end.isoformat(),
            period.period_type.value,
            occurrence.entity_scope or "",
            occurrence.statement_basis or "",
            occurrence.currency or "",
            _occurrence_id(occurrence),
        )
    )
    return f"cashflow-reported:{hashlib.sha256(payload.encode()).hexdigest()[:24]}"


def canonicalize_official_occurrence(
    occurrence: OfficialFilingOccurrence,
    *,
    as_of_date: date,
) -> EligibilityDecision:
    entry = REGISTRY_BY_SEMANTIC.get(occurrence.semantic)
    if entry is None:
        return _blocked(
            REJECTED_SEMANTICS.get(occurrence.semantic, "semantic_not_registered"),
            occurrence,
        )
    if occurrence.source_document_type not in FORMAL_FORMS:
        return _blocked("formal_filing_required", occurrence)
    if occurrence.source_document_id is None:
        return _blocked("source_document_id_missing", occurrence)
    if occurrence.filing_date is None or occurrence.filing_date > as_of_date:
        return _blocked("filing_date_unavailable_or_after_as_of", occurrence)
    if occurrence.currency is None or occurrence.unit is None:
        return _blocked("currency_or_unit_missing", occurrence)
    if occurrence.entity_scope is None:
        return _blocked("entity_scope_missing", occurrence)
    if occurrence.statement_basis is None:
        return _blocked("statement_basis_missing", occurrence)
    if occurrence.raw_payload_sha256 is None or len(occurrence.raw_payload_sha256) != 64:
        return _blocked("raw_payload_sha256_missing", occurrence)
    period = classify_flow_period(occurrence)
    if period is None:
        return _blocked("period_context_unresolved", occurrence)
    source_sign = "economic_signed_amount"
    normalization_transform = "identity_economic_signed_amount"
    if entry.metric == Metric.CAPEX:
        source_sign = (
            "negative_cash_outflow"
            if occurrence.value < 0
            else "positive_payment_magnitude"
        )
        normalization_transform = None
    fact = FinancialFact(
        fact_id=_reported_fact_id(occurrence, entry.metric, period),
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
        semantic_mapping=entry.semantic,
        fact_type=FactType.REPORTED,
        source_document_type=occurrence.source_document_type,
        source_semantic=entry.semantic,
        source_reported_value=occurrence.value,
        source_reported_unit=occurrence.unit,
        source_sign=source_sign,
        normalization_transform=normalization_transform,
        capex_scope=CapexScope.PPE_ONLY if entry.metric == Metric.CAPEX else None,
        quality="REPORTED_VERIFIED",
        eligibility=EligibilityStatus.ELIGIBLE,
        cautions=("sec_companyfacts_issuer_level_context",),
        restatement_policy_id=RESTATEMENT_POLICY_ID,
        as_of_date=as_of_date,
    )
    if entry.metric == Metric.CAPEX:
        return normalize_capex_cash_outflow(fact, capex_scope=CapexScope.PPE_ONLY)
    return EligibilityDecision(EligibilityStatus.ELIGIBLE, fact=fact)


def extract_sec_companyfacts_occurrences(
    payload: Mapping[str, object],
    *,
    raw_payload_sha256: str,
) -> tuple[OfficialFilingOccurrence, ...]:
    cik = str(payload.get("cik") or "").strip().zfill(10)
    if not cik.strip("0"):
        return ()
    facts = payload.get("facts")
    if not isinstance(facts, Mapping):
        return ()
    output: list[OfficialFilingOccurrence] = []
    for entry in SEMANTIC_REGISTRY:
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
                    OfficialFilingOccurrence(
                        issuer_id=f"sec:{cik}",
                        value=value,
                        currency=_currency_from_unit(unit),
                        unit=unit,
                        period_start=_parse_date(row.get("start")),
                        period_end=_parse_date(row.get("end")),
                        fiscal_year=(
                            int(row["fy"])
                            if isinstance(row.get("fy"), int | float | str)
                            and str(row.get("fy")).isdigit()
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
                        statement_basis="official_filing_cash_flow_statement",
                        frame=str(row.get("frame")) if row.get("frame") else None,
                    )
                )
    return tuple(output)


def _fact_period_key(fact: FinancialFact) -> tuple[object, ...]:
    return (
        fact.issuer_id,
        fact.metric,
        fact.period,
        fact.currency,
        fact.unit,
        fact.entity_scope,
        fact.statement_basis,
    )


def _economic_context_key(occurrence: OfficialFilingOccurrence) -> tuple[object, ...]:
    return (
        occurrence.issuer_id,
        occurrence.semantic,
        occurrence.period_start,
        occurrence.period_end,
        occurrence.unit,
    )


def _normalize_economic_fiscal_context(
    occurrences: tuple[OfficialFilingOccurrence, ...],
) -> tuple[OfficialFilingOccurrence, ...]:
    grouped: dict[tuple[object, ...], list[OfficialFilingOccurrence]] = {}
    for occurrence in occurrences:
        grouped.setdefault(_economic_context_key(occurrence), []).append(occurrence)
    normalized: list[OfficialFilingOccurrence] = []
    for values in grouped.values():
        context_sources = [
            item
            for item in values
            if item.filing_date is not None
            and item.fiscal_year is not None
            and item.fiscal_period is not None
        ]
        context_source = (
            min(
                context_sources,
                key=lambda item: (item.filing_date, item.source_document_id or ""),
            )
            if context_sources
            else None
        )
        for item in values:
            normalized.append(
                replace(
                    item,
                    fiscal_year=(
                        context_source.fiscal_year if context_source else item.fiscal_year
                    ),
                    fiscal_period=(
                        context_source.fiscal_period
                        if context_source
                        else item.fiscal_period
                    ),
                )
            )
    return tuple(normalized)


def _fact_authority_key(fact: FinancialFact) -> tuple[object, ...]:
    entry = REGISTRY_BY_SEMANTIC[fact.semantic_mapping]
    amended = 1 if (fact.source_document_type or "").endswith("/A") else 0
    return (fact.filing_date, amended, entry.priority, fact.source_document_id)


def canonicalize_sec_companyfacts(
    payload: Mapping[str, object],
    *,
    raw_payload_sha256: str,
    as_of_date: date,
) -> CanonicalizationBatch:
    occurrences = _normalize_economic_fiscal_context(
        extract_sec_companyfacts_occurrences(
            payload,
            raw_payload_sha256=raw_payload_sha256,
        )
    )
    decisions = [
        canonicalize_official_occurrence(item, as_of_date=as_of_date)
        for item in occurrences
    ]
    denials: list[dict[str, str]] = []
    eligible: list[FinancialFact] = []
    for occurrence, decision in zip(occurrences, decisions, strict=True):
        if decision.fact is None:
            denials.append(
                {
                    "source_occurrence_id": _occurrence_id(occurrence),
                    "source_semantic": occurrence.semantic,
                    "reason": decision.reasons[0],
                }
            )
        else:
            eligible.append(decision.fact)

    by_occurrence: dict[str, list[FinancialFact]] = {}
    for fact in eligible:
        by_occurrence.setdefault(fact.source_occurrence_id, []).append(fact)
    deduplicated: list[FinancialFact] = []
    duplicates = 0
    conflicts = 0
    for occurrence_id, values in by_occurrence.items():
        distinct = {item.value for item in values}
        if len(distinct) > 1:
            conflicts += 1
            denials.append(
                {
                    "source_occurrence_id": occurrence_id,
                    "source_semantic": values[0].semantic_mapping,
                    "reason": "source_occurrence_conflict",
                }
            )
            continue
        duplicates += len(values) - 1
        deduplicated.append(max(values, key=_fact_authority_key))

    by_period: dict[tuple[object, ...], list[FinancialFact]] = {}
    for fact in deduplicated:
        by_period.setdefault(_fact_period_key(fact), []).append(fact)
    selected = [max(values, key=_fact_authority_key) for values in by_period.values()]
    selected.sort(
        key=lambda fact: (
            fact.period.end,
            fact.period.start,
            fact.metric.value,
            fact.filing_date,
            fact.fact_id,
        )
    )
    return CanonicalizationBatch(
        facts=tuple(selected),
        denials=tuple(denials),
        extracted_occurrences=len(occurrences),
        exact_duplicates_suppressed=duplicates,
        conflicts=conflicts,
    )


def registry_audit() -> tuple[dict[str, object], ...]:
    return tuple(
        {
            "canonical_metric": entry.metric.value,
            "source_taxonomy": entry.namespace,
            "source_tag": entry.tag,
            "source_semantic": entry.semantic,
            "statement_section": entry.statement_section,
            "economic_meaning": entry.economic_meaning,
            "sign_policy": entry.sign_policy,
            "priority": entry.priority,
        }
        for entry in SEMANTIC_REGISTRY
    )


def rejected_semantic_audit() -> tuple[dict[str, str], ...]:
    return tuple(
        {"source_semantic": semantic, "denial_reason": reason}
        for semantic, reason in sorted(REJECTED_SEMANTICS.items())
    )


def fact_ids(facts: Iterable[FinancialFact]) -> tuple[str, ...]:
    return tuple(item.fact_id for item in facts)
