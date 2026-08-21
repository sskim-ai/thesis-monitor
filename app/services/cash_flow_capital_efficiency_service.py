from __future__ import annotations

import hashlib
from dataclasses import dataclass, field, replace
from datetime import date, timedelta
from decimal import Decimal
from enum import StrEnum
from typing import Iterable, Mapping


CONTRACT_VERSION = "cash-flow-capital-efficiency-v1"


class PeriodType(StrEnum):
    QTD = "QTD"
    YTD = "YTD"
    FY = "FY"
    TTM = "TTM"
    POINT_IN_TIME = "POINT_IN_TIME"


class EligibilityStatus(StrEnum):
    ELIGIBLE = "ELIGIBLE"
    PARTIAL = "PARTIAL"
    BLOCKED = "BLOCKED"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class FactType(StrEnum):
    REPORTED = "REPORTED"
    DERIVED_PERIOD = "DERIVED_PERIOD"
    DERIVED_METRIC = "DERIVED_METRIC"


class Metric(StrEnum):
    OCF = "operating_cash_flow"
    CAPEX = "ppe_capex_cash_outflow"
    FCF = "free_cash_flow_ppe"
    REVENUE = "revenue"
    NET_INCOME = "net_income"
    OPERATING_INCOME = "operating_income"
    PRETAX_INCOME = "pretax_income"
    TAX_EXPENSE = "tax_expense"
    INVENTORY = "inventory"
    TRADE_AR = "trade_accounts_receivable"
    BROAD_AR = "accounts_receivable_broad"
    TOTAL_AR = "total_accounts_receivable"
    TRADE_AP = "trade_accounts_payable"
    BROAD_AP = "accounts_payable_broad"
    TOTAL_AP = "total_accounts_payable"
    COGS = "cost_of_goods_sold"
    PURCHASES = "purchases"
    EQUITY = "equity"
    INTEREST_BEARING_DEBT = "interest_bearing_debt"
    EXCESS_CASH = "excess_cash"
    OCF_MARGIN = "operating_cash_flow_margin"
    FCF_MARGIN = "free_cash_flow_margin_ppe"
    CAPEX_INTENSITY = "capex_intensity_ppe"
    OCF_TO_NET_INCOME = "operating_cash_flow_to_net_income"
    BALANCE_DELTA = "working_capital_balance_delta"
    BALANCE_YOY_GROWTH = "working_capital_balance_yoy_growth"
    FLOW_YOY_GROWTH = "financial_flow_yoy_growth"
    DSO = "days_sales_outstanding"
    INVENTORY_DAYS = "inventory_days"
    DPO = "days_payables_outstanding"
    CCC = "cash_conversion_cycle"
    ROIC = "return_on_invested_capital"


class CapexScope(StrEnum):
    PPE_ONLY = "ppe_only"
    INTANGIBLES_ONLY = "intangibles_only"
    CAPITALIZED_SOFTWARE_ONLY = "capitalized_software_only"
    PPE_PLUS_INTANGIBLES = "ppe_plus_intangibles"
    REPORTED_COMPANY_CAPEX = "reported_company_capex"
    UNKNOWN = "unknown_scope"


@dataclass(frozen=True)
class PeriodIdentity:
    start: date
    end: date
    period_type: PeriodType
    fiscal_year: int
    fiscal_quarter: int | None = None

    def __post_init__(self) -> None:
        if self.end < self.start:
            raise ValueError("period_end_before_start")
        if self.period_type == PeriodType.POINT_IN_TIME and self.start != self.end:
            raise ValueError("point_in_time_requires_one_date")
        if self.fiscal_quarter is not None and self.fiscal_quarter not in {1, 2, 3, 4}:
            raise ValueError("invalid_fiscal_quarter")

    @property
    def duration_days(self) -> int:
        return (self.end - self.start).days + 1


@dataclass(frozen=True)
class FinancialFact:
    fact_id: str
    issuer_id: str
    metric: Metric
    value: Decimal
    currency: str
    unit: str
    period: PeriodIdentity
    entity_scope: str
    statement_basis: str
    reported_or_derived: str
    source_provider: str
    source_document_id: str
    filing_date: date
    source_occurrence_id: str
    raw_payload_sha256: str
    semantic_mapping: str
    fact_type: FactType = FactType.REPORTED
    source_document_type: str | None = None
    source_semantic: str | None = None
    source_reported_value: Decimal | None = None
    source_reported_unit: str | None = None
    source_sign: str | None = None
    normalization_transform: str | None = None
    capex_scope: CapexScope | None = None
    derivation_formula: str | None = None
    derivation_version: str | None = None
    input_fact_ids: tuple[str, ...] = ()
    quality: str = "REPORTED_VERIFIED"
    eligibility: EligibilityStatus = EligibilityStatus.ELIGIBLE
    denial_reason: str | None = None
    cautions: tuple[str, ...] = ()
    restatement_policy_id: str | None = None
    as_of_date: date | None = None
    source_available_at: date | None = None
    balance_scope: str | None = None
    net_gross_scope: str | None = None


def financial_fact_from_mapping(row: Mapping[str, object]) -> FinancialFact:
    """Restore a canonical cash-flow fact from an audited report row."""
    capex_scope = row.get("capex_scope")
    return FinancialFact(
        fact_id=str(row["fact_id"]),
        issuer_id=str(row["issuer_id"]),
        metric=Metric(str(row["metric"])),
        value=Decimal(str(row["value"])),
        currency=str(row["currency"]),
        unit=str(row["unit"]),
        period=PeriodIdentity(
            start=date.fromisoformat(str(row["period_start"])),
            end=date.fromisoformat(str(row["period_end"])),
            period_type=PeriodType(str(row["period_type"])),
            fiscal_year=int(str(row["fiscal_year"])),
            fiscal_quarter=(
                int(str(row["fiscal_quarter"]))
                if row.get("fiscal_quarter") is not None
                else None
            ),
        ),
        entity_scope=str(row["entity_scope"]),
        statement_basis=str(row["statement_basis"]),
        reported_or_derived=str(row["reported_or_derived"]),
        source_provider=str(row["source_provider"]),
        source_document_id=str(row["source_document_id"]),
        filing_date=date.fromisoformat(str(row["filing_date"])),
        source_occurrence_id=str(row["source_occurrence_id"]),
        raw_payload_sha256=str(row["raw_payload_sha256"]),
        semantic_mapping=str(row.get("semantic_mapping") or ""),
        fact_type=FactType(str(row["fact_type"])),
        source_document_type=(
            str(row["source_document_type"])
            if row.get("source_document_type") is not None
            else None
        ),
        source_semantic=(
            str(row["source_semantic"])
            if row.get("source_semantic") is not None
            else None
        ),
        source_reported_value=(
            Decimal(str(row["source_reported_value"]))
            if row.get("source_reported_value") is not None
            else None
        ),
        source_reported_unit=(
            str(row["source_reported_unit"])
            if row.get("source_reported_unit") is not None
            else None
        ),
        source_sign=(
            str(row["source_sign"]) if row.get("source_sign") is not None else None
        ),
        normalization_transform=(
            str(row["normalization_transform"])
            if row.get("normalization_transform") is not None
            else None
        ),
        capex_scope=CapexScope(str(capex_scope)) if capex_scope else None,
        derivation_formula=(
            str(row["derivation_formula"])
            if row.get("derivation_formula") is not None
            else None
        ),
        derivation_version=(
            str(row["derivation_version"])
            if row.get("derivation_version") is not None
            else None
        ),
        input_fact_ids=tuple(str(item) for item in row.get("input_fact_ids") or ()),
        quality=str(row.get("quality") or "REPORTED_VERIFIED"),
        eligibility=EligibilityStatus(str(row.get("eligibility") or "ELIGIBLE")),
        denial_reason=(
            str(row["denial_reason"])
            if row.get("denial_reason") is not None
            else None
        ),
        cautions=tuple(str(item) for item in row.get("cautions") or ()),
        restatement_policy_id=(
            str(row["restatement_policy_id"])
            if row.get("restatement_policy_id") is not None
            else None
        ),
        as_of_date=(
            date.fromisoformat(str(row["as_of_date"]))
            if row.get("as_of_date") is not None
            else None
        ),
        source_available_at=(
            date.fromisoformat(str(row["source_available_at"]))
            if row.get("source_available_at") is not None
            else None
        ),
        balance_scope=(
            str(row["balance_scope"])
            if row.get("balance_scope") is not None
            else None
        ),
        net_gross_scope=(
            str(row["net_gross_scope"])
            if row.get("net_gross_scope") is not None
            else None
        ),
    )


@dataclass(frozen=True)
class EligibilityDecision:
    status: EligibilityStatus
    fact: FinancialFact | None = None
    reasons: tuple[str, ...] = ()
    audit: dict[str, object] = field(default_factory=dict)


def _blocked(*reasons: str) -> EligibilityDecision:
    return EligibilityDecision(EligibilityStatus.BLOCKED, reasons=tuple(reasons))


def _derived_id(metric: Metric, formula: str, inputs: Iterable[FinancialFact]) -> str:
    payload = "|".join(
        [CONTRACT_VERSION, metric.value, formula, *(fact.fact_id for fact in inputs)]
    )
    return f"cashflow:{hashlib.sha256(payload.encode()).hexdigest()[:24]}"


def _combined_raw_sha(facts: Iterable[FinancialFact]) -> str:
    payload = "|".join(item.raw_payload_sha256 for item in facts)
    return hashlib.sha256(payload.encode()).hexdigest()


def _common_compatibility(facts: Iterable[FinancialFact]) -> tuple[str, ...]:
    values = list(facts)
    if not values:
        return ("input_facts_missing",)
    reasons: list[str] = []
    for field_name in (
        "issuer_id",
        "currency",
        "unit",
        "entity_scope",
        "statement_basis",
    ):
        if len({getattr(item, field_name) for item in values}) != 1:
            reasons.append(f"{field_name}_mismatch")
    if any(item.eligibility != EligibilityStatus.ELIGIBLE for item in values):
        reasons.append("input_fact_not_eligible")
    if any(item.quality not in {"REPORTED_VERIFIED", "DERIVED_SAFE"} for item in values):
        reasons.append("input_fact_quality_tainted")
    return tuple(reasons)


def _same_period(facts: Iterable[FinancialFact]) -> tuple[str, ...]:
    values = list(facts)
    if len({item.period for item in values}) != 1:
        return ("period_mismatch",)
    return ()


def normalize_capex_cash_outflow(
    fact: FinancialFact,
    *,
    capex_scope: CapexScope,
) -> EligibilityDecision:
    if fact.metric != Metric.CAPEX:
        return _blocked("metric_is_not_capex")
    if capex_scope == CapexScope.UNKNOWN:
        return _blocked("capex_scope_unknown")
    if capex_scope != CapexScope.PPE_ONLY:
        return EligibilityDecision(
            EligibilityStatus.PARTIAL,
            reasons=("non_baseline_capex_component_preserved_separately",),
        )
    if fact.source_sign == "negative_cash_outflow":
        normalized = abs(fact.value)
        transform = "absolute_value_of_negative_cash_outflow"
    elif fact.source_sign == "positive_payment_magnitude":
        normalized = fact.value
        transform = "identity_positive_payment_magnitude"
    else:
        return _blocked("capex_source_sign_unknown")
    if normalized < 0:
        return _blocked("normalized_capex_negative")
    return EligibilityDecision(
        EligibilityStatus.ELIGIBLE,
        fact=replace(
            fact,
            value=normalized,
            capex_scope=capex_scope,
            source_reported_value=(
                fact.source_reported_value
                if fact.source_reported_value is not None
                else fact.value
            ),
            source_reported_unit=fact.source_reported_unit or fact.unit,
            normalization_transform=transform,
        ),
    )


def q1_ytd_as_qtd(fact: FinancialFact) -> EligibilityDecision:
    if fact.period.period_type != PeriodType.YTD or fact.period.fiscal_quarter != 1:
        return _blocked("q1_ytd_required")
    if not 70 <= fact.period.duration_days <= 110:
        return _blocked("q1_duration_not_quarter_like")
    qtd_period = replace(fact.period, period_type=PeriodType.QTD)
    formula = "Q1_QTD_EQUALS_VERIFIED_Q1_YTD"
    return EligibilityDecision(
        EligibilityStatus.ELIGIBLE,
        fact=replace(
            fact,
            fact_id=_derived_id(fact.metric, formula, (fact,)),
            period=qtd_period,
            reported_or_derived="derived_period",
            fact_type=FactType.DERIVED_PERIOD,
            derivation_formula=formula,
            derivation_version=CONTRACT_VERSION,
            input_fact_ids=(fact.fact_id,),
            quality="DERIVED_SAFE",
        ),
    )


def derive_qtd_from_ytd(
    current_ytd: FinancialFact,
    prior_ytd: FinancialFact,
) -> EligibilityDecision:
    reasons = list(_common_compatibility((current_ytd, prior_ytd)))
    if current_ytd.metric != prior_ytd.metric:
        reasons.append("metric_mismatch")
    if current_ytd.semantic_mapping != prior_ytd.semantic_mapping:
        reasons.append("semantic_mapping_mismatch")
    if any(
        item.period.period_type != PeriodType.YTD
        for item in (current_ytd, prior_ytd)
    ):
        reasons.append("ytd_inputs_required")
    if current_ytd.period.fiscal_year != prior_ytd.period.fiscal_year:
        reasons.append("fiscal_year_mismatch")
    if current_ytd.period.start != prior_ytd.period.start:
        reasons.append("fiscal_year_start_mismatch")
    current_quarter = current_ytd.period.fiscal_quarter
    prior_quarter = prior_ytd.period.fiscal_quarter
    if (
        current_quarter is None
        or prior_quarter is None
        or current_quarter != prior_quarter + 1
    ):
        reasons.append("adjacent_ytd_quarters_required")
    if current_ytd.period.end <= prior_ytd.period.end:
        reasons.append("current_ytd_not_later")
    if (
        not current_ytd.restatement_policy_id
        or current_ytd.restatement_policy_id != prior_ytd.restatement_policy_id
    ):
        reasons.append("restatement_compatibility_unverified")
    if reasons:
        return _blocked(*dict.fromkeys(reasons))
    period = PeriodIdentity(
        start=prior_ytd.period.end + timedelta(days=1),
        end=current_ytd.period.end,
        period_type=PeriodType.QTD,
        fiscal_year=current_ytd.period.fiscal_year,
        fiscal_quarter=current_quarter,
    )
    formula = "CURRENT_YTD_MINUS_PRIOR_QUARTER_YTD"
    return EligibilityDecision(
        EligibilityStatus.ELIGIBLE,
        fact=replace(
            current_ytd,
            fact_id=_derived_id(
                current_ytd.metric, formula, (current_ytd, prior_ytd)
            ),
            value=current_ytd.value - prior_ytd.value,
            period=period,
            reported_or_derived="derived_period",
            fact_type=FactType.DERIVED_PERIOD,
            source_document_id=(
                f"{current_ytd.source_document_id}+{prior_ytd.source_document_id}"
            ),
            source_occurrence_id=(
                f"{current_ytd.source_occurrence_id}+{prior_ytd.source_occurrence_id}"
            ),
            raw_payload_sha256=_combined_raw_sha((current_ytd, prior_ytd)),
            derivation_formula=formula,
            derivation_version=CONTRACT_VERSION,
            input_fact_ids=(current_ytd.fact_id, prior_ytd.fact_id),
            quality="DERIVED_SAFE",
        ),
    )


def derive_ttm(
    prior_fy: FinancialFact,
    current_ytd: FinancialFact,
    prior_comparable_ytd: FinancialFact,
) -> EligibilityDecision:
    facts = (prior_fy, current_ytd, prior_comparable_ytd)
    reasons = list(_common_compatibility(facts))
    if len({item.metric for item in facts}) != 1:
        reasons.append("metric_mismatch")
    if len({item.semantic_mapping for item in facts}) != 1:
        reasons.append("semantic_mapping_mismatch")
    if prior_fy.period.period_type != PeriodType.FY:
        reasons.append("prior_fy_required")
    if any(
        item.period.period_type != PeriodType.YTD
        for item in (current_ytd, prior_comparable_ytd)
    ):
        reasons.append("current_and_prior_ytd_required")
    if current_ytd.period.fiscal_year != prior_fy.period.fiscal_year + 1:
        reasons.append("current_ytd_fiscal_year_mismatch")
    if prior_comparable_ytd.period.fiscal_year != prior_fy.period.fiscal_year:
        reasons.append("prior_comparable_fiscal_year_mismatch")
    if current_ytd.period.fiscal_quarter != prior_comparable_ytd.period.fiscal_quarter:
        reasons.append("ytd_quarter_mismatch")
    if current_ytd.period.duration_days != prior_comparable_ytd.period.duration_days:
        reasons.append("ytd_duration_mismatch")
    if current_ytd.period.end <= prior_comparable_ytd.period.end:
        reasons.append("current_ytd_not_after_prior_comparable")
    restatement_ids = {item.restatement_policy_id for item in facts}
    if None in restatement_ids or len(restatement_ids) != 1:
        reasons.append("restatement_compatibility_unverified")
    if reasons:
        return _blocked(*dict.fromkeys(reasons))
    period = PeriodIdentity(
        start=prior_comparable_ytd.period.end + timedelta(days=1),
        end=current_ytd.period.end,
        period_type=PeriodType.TTM,
        fiscal_year=current_ytd.period.fiscal_year,
    )
    if not 330 <= period.duration_days <= 400:
        return _blocked("ttm_duration_not_annual_like")
    formula = "PRIOR_FY_PLUS_CURRENT_YTD_MINUS_PRIOR_COMPARABLE_YTD"
    return EligibilityDecision(
        EligibilityStatus.ELIGIBLE,
        fact=replace(
            current_ytd,
            fact_id=_derived_id(current_ytd.metric, formula, facts),
            value=prior_fy.value + current_ytd.value - prior_comparable_ytd.value,
            period=period,
            reported_or_derived="derived_period",
            fact_type=FactType.DERIVED_PERIOD,
            source_document_id="+".join(item.source_document_id for item in facts),
            source_occurrence_id="+".join(item.source_occurrence_id for item in facts),
            raw_payload_sha256=_combined_raw_sha(facts),
            derivation_formula=formula,
            derivation_version=CONTRACT_VERSION,
            input_fact_ids=tuple(item.fact_id for item in facts),
            quality="DERIVED_SAFE",
        ),
    )


def derive_fcf(ocf: FinancialFact, capex: FinancialFact) -> EligibilityDecision:
    reasons = [*_common_compatibility((ocf, capex)), *_same_period((ocf, capex))]
    if ocf.metric != Metric.OCF:
        reasons.append("ocf_metric_required")
    if capex.metric != Metric.CAPEX:
        reasons.append("capex_metric_required")
    if capex.capex_scope != CapexScope.PPE_ONLY:
        reasons.append("baseline_fcf_requires_ppe_only_capex")
    if capex.value < 0:
        reasons.append("capex_must_be_positive_magnitude")
    if ocf.source_document_id != capex.source_document_id:
        reasons.append("source_document_mismatch")
    if reasons:
        return _blocked(*dict.fromkeys(reasons))
    formula = "OCF_MINUS_PPE_CAPEX_CASH_OUTFLOW"
    return EligibilityDecision(
        EligibilityStatus.ELIGIBLE,
        fact=replace(
            ocf,
            fact_id=_derived_id(Metric.FCF, formula, (ocf, capex)),
            metric=Metric.FCF,
            value=ocf.value - capex.value,
            reported_or_derived="derived",
            fact_type=FactType.DERIVED_METRIC,
            source_provider="canonical_derivation",
            source_document_type="derived_metric",
            source_document_id=f"{ocf.source_document_id}+{capex.source_document_id}",
            source_occurrence_id=(
                f"{ocf.source_occurrence_id}+{capex.source_occurrence_id}"
            ),
            raw_payload_sha256=_combined_raw_sha((ocf, capex)),
            semantic_mapping="backend_fcf_ppe_only",
            source_semantic=None,
            source_reported_value=None,
            source_reported_unit=None,
            source_sign=None,
            normalization_transform=None,
            capex_scope=CapexScope.PPE_ONLY,
            derivation_formula=formula,
            derivation_version=CONTRACT_VERSION,
            input_fact_ids=(ocf.fact_id, capex.fact_id),
            quality="DERIVED_SAFE",
        ),
    )


def derive_ratio(
    numerator: FinancialFact,
    denominator: FinancialFact,
    *,
    metric: Metric,
) -> EligibilityDecision:
    allowed = {
        Metric.OCF_MARGIN: (Metric.OCF, Metric.REVENUE),
        Metric.FCF_MARGIN: (Metric.FCF, Metric.REVENUE),
        Metric.CAPEX_INTENSITY: (Metric.CAPEX, Metric.REVENUE),
        Metric.OCF_TO_NET_INCOME: (Metric.OCF, Metric.NET_INCOME),
    }
    expected = allowed.get(metric)
    if expected is None:
        return _blocked("unsupported_ratio_metric")
    reasons = [
        *_common_compatibility((numerator, denominator)),
        *_same_period((numerator, denominator)),
    ]
    if (numerator.metric, denominator.metric) != expected:
        reasons.append("ratio_metric_dependencies_mismatch")
    if denominator.value <= 0:
        reasons.append("non_positive_denominator")
    if reasons:
        return _blocked(*dict.fromkeys(reasons))
    formula = f"{numerator.metric.value}_DIVIDED_BY_{denominator.metric.value}"
    return EligibilityDecision(
        EligibilityStatus.ELIGIBLE,
        fact=replace(
            numerator,
            fact_id=_derived_id(metric, formula, (numerator, denominator)),
            metric=metric,
            value=numerator.value / denominator.value,
            unit="ratio",
            reported_or_derived="derived",
            source_document_id=(
                f"{numerator.source_document_id}+{denominator.source_document_id}"
            ),
            source_occurrence_id=(
                f"{numerator.source_occurrence_id}+{denominator.source_occurrence_id}"
            ),
            semantic_mapping=metric.value,
            source_reported_value=None,
            source_sign=None,
            derivation_formula=formula,
            input_fact_ids=(numerator.fact_id, denominator.fact_id),
            quality="DERIVED_SAFE",
        ),
    )


def derive_balance_delta(
    current: FinancialFact,
    comparison: FinancialFact,
) -> EligibilityDecision:
    reasons = list(_common_compatibility((current, comparison)))
    if current.metric != comparison.metric:
        reasons.append("metric_mismatch")
    if any(
        item.period.period_type != PeriodType.POINT_IN_TIME
        for item in (current, comparison)
    ):
        reasons.append("point_in_time_inputs_required")
    if current.period.end <= comparison.period.end:
        reasons.append("comparison_not_earlier")
    if reasons:
        return _blocked(*dict.fromkeys(reasons))
    formula = "CURRENT_BALANCE_MINUS_COMPARISON_BALANCE"
    return EligibilityDecision(
        EligibilityStatus.ELIGIBLE,
        fact=replace(
            current,
            fact_id=_derived_id(Metric.BALANCE_DELTA, formula, (current, comparison)),
            metric=Metric.BALANCE_DELTA,
            value=current.value - comparison.value,
            reported_or_derived="derived",
            source_document_id=f"{current.source_document_id}+{comparison.source_document_id}",
            source_occurrence_id=(
                f"{current.source_occurrence_id}+{comparison.source_occurrence_id}"
            ),
            derivation_formula=formula,
            input_fact_ids=(current.fact_id, comparison.fact_id),
            quality="DERIVED_SAFE",
        ),
    )


def derive_working_capital_days(
    flow: FinancialFact,
    beginning_balance: FinancialFact,
    ending_balance: FinancialFact,
    *,
    metric: Metric,
) -> EligibilityDecision:
    dependencies = {
        Metric.DSO: (Metric.REVENUE, Metric.TRADE_AR),
        Metric.INVENTORY_DAYS: (Metric.COGS, Metric.INVENTORY),
        Metric.DPO: (Metric.PURCHASES, Metric.TRADE_AP),
    }
    expected = dependencies.get(metric)
    if expected is None:
        return _blocked("unsupported_working_capital_days_metric")
    facts = (flow, beginning_balance, ending_balance)
    reasons = list(_common_compatibility(facts))
    if flow.metric != expected[0]:
        reasons.append("flow_metric_mismatch")
    if beginning_balance.metric != expected[1] or ending_balance.metric != expected[1]:
        reasons.append("balance_semantic_scope_mismatch")
    if flow.period.period_type == PeriodType.POINT_IN_TIME:
        reasons.append("duration_flow_required")
    if any(
        item.period.period_type != PeriodType.POINT_IN_TIME
        for item in (beginning_balance, ending_balance)
    ):
        reasons.append("average_balance_points_required")
    if beginning_balance.period.end != flow.period.start - timedelta(days=1):
        reasons.append("beginning_balance_date_mismatch")
    if ending_balance.period.end != flow.period.end:
        reasons.append("ending_balance_date_mismatch")
    if flow.value <= 0:
        reasons.append("non_positive_flow_denominator")
    if reasons:
        return _blocked(*dict.fromkeys(reasons))
    average_balance = (beginning_balance.value + ending_balance.value) / Decimal(2)
    formula = "AVERAGE_BALANCE_DIVIDED_BY_FLOW_TIMES_ACTUAL_PERIOD_DAYS"
    return EligibilityDecision(
        EligibilityStatus.ELIGIBLE,
        fact=replace(
            flow,
            fact_id=_derived_id(metric, formula, facts),
            metric=metric,
            value=average_balance / flow.value * Decimal(flow.period.duration_days),
            unit="days",
            reported_or_derived="derived",
            source_document_id="+".join(item.source_document_id for item in facts),
            source_occurrence_id="+".join(item.source_occurrence_id for item in facts),
            semantic_mapping=metric.value,
            source_reported_value=None,
            derivation_formula=formula,
            input_fact_ids=tuple(item.fact_id for item in facts),
            quality="DERIVED_SAFE",
        ),
    )


def derive_ccc(
    dso: FinancialFact,
    inventory_days: FinancialFact,
    dpo: FinancialFact,
) -> EligibilityDecision:
    facts = (dso, inventory_days, dpo)
    reasons = [*_common_compatibility(facts), *_same_period(facts)]
    if tuple(item.metric for item in facts) != (
        Metric.DSO,
        Metric.INVENTORY_DAYS,
        Metric.DPO,
    ):
        reasons.append("all_ccc_components_required")
    if reasons:
        return _blocked(*dict.fromkeys(reasons))
    formula = "DSO_PLUS_INVENTORY_DAYS_MINUS_DPO"
    return EligibilityDecision(
        EligibilityStatus.ELIGIBLE,
        fact=replace(
            dso,
            fact_id=_derived_id(Metric.CCC, formula, facts),
            metric=Metric.CCC,
            value=dso.value + inventory_days.value - dpo.value,
            reported_or_derived="derived",
            source_document_id="+".join(item.source_document_id for item in facts),
            source_occurrence_id="+".join(item.source_occurrence_id for item in facts),
            semantic_mapping=Metric.CCC.value,
            derivation_formula=formula,
            input_fact_ids=tuple(item.fact_id for item in facts),
            quality="DERIVED_SAFE",
        ),
    )


def derive_standard_roic(
    operating_income: FinancialFact,
    pretax_income: FinancialFact,
    tax_expense: FinancialFact,
    beginning_equity: FinancialFact,
    ending_equity: FinancialFact,
    beginning_debt: FinancialFact,
    ending_debt: FinancialFact,
    beginning_excess_cash: FinancialFact,
    ending_excess_cash: FinancialFact,
    *,
    industry_applicability: str,
    excess_cash_policy_id: str | None,
) -> EligibilityDecision:
    if industry_applicability == "financial_industry_not_applicable":
        return EligibilityDecision(
            EligibilityStatus.NOT_APPLICABLE,
            reasons=("generic_roic_not_applicable_to_financial_industry",),
        )
    facts = (
        operating_income,
        pretax_income,
        tax_expense,
        beginning_equity,
        ending_equity,
        beginning_debt,
        ending_debt,
        beginning_excess_cash,
        ending_excess_cash,
    )
    reasons = list(_common_compatibility(facts))
    if (operating_income.metric, pretax_income.metric, tax_expense.metric) != (
        Metric.OPERATING_INCOME,
        Metric.PRETAX_INCOME,
        Metric.TAX_EXPENSE,
    ):
        reasons.append("nopat_metric_dependencies_mismatch")
    if any(
        item.metric != Metric.EQUITY
        for item in (beginning_equity, ending_equity)
    ):
        reasons.append("equity_inputs_required")
    if any(
        item.metric != Metric.INTEREST_BEARING_DEBT
        for item in (beginning_debt, ending_debt)
    ):
        reasons.append("interest_bearing_debt_inputs_required")
    if any(
        item.metric != Metric.EXCESS_CASH
        for item in (beginning_excess_cash, ending_excess_cash)
    ):
        reasons.append("verified_excess_cash_inputs_required")
    if not excess_cash_policy_id:
        reasons.append("excess_cash_policy_unverified")
    elif any(
        item.semantic_mapping != f"verified_excess_cash_policy:{excess_cash_policy_id}"
        for item in (beginning_excess_cash, ending_excess_cash)
    ):
        reasons.append("excess_cash_policy_mismatch")
    if _same_period((operating_income, pretax_income, tax_expense)):
        reasons.append("nopat_period_mismatch")
    if pretax_income.value <= 0:
        reasons.append("non_positive_pretax_income")
    else:
        tax_rate = tax_expense.value / pretax_income.value
        if tax_rate < 0 or tax_rate > 1:
            reasons.append("effective_tax_rate_out_of_range")
    if any(
        item.period.period_type != PeriodType.POINT_IN_TIME
        for item in facts[3:]
    ):
        reasons.append("invested_capital_point_inputs_required")
    if beginning_equity.period.end != operating_income.period.start - timedelta(days=1):
        reasons.append("beginning_invested_capital_date_mismatch")
    if ending_equity.period.end != operating_income.period.end:
        reasons.append("ending_invested_capital_date_mismatch")
    if reasons:
        return _blocked(*dict.fromkeys(reasons))
    tax_rate = tax_expense.value / pretax_income.value
    nopat = operating_income.value * (Decimal(1) - tax_rate)
    beginning_capital = (
        beginning_equity.value
        + beginning_debt.value
        - beginning_excess_cash.value
    )
    ending_capital = (
        ending_equity.value + ending_debt.value - ending_excess_cash.value
    )
    average_capital = (beginning_capital + ending_capital) / Decimal(2)
    if average_capital <= 0:
        return _blocked("non_positive_average_invested_capital")
    formula = "EBIT_TIMES_ONE_MINUS_ETR_DIVIDED_BY_AVERAGE_INVESTED_CAPITAL"
    return EligibilityDecision(
        EligibilityStatus.ELIGIBLE,
        fact=replace(
            operating_income,
            fact_id=_derived_id(Metric.ROIC, formula, facts),
            metric=Metric.ROIC,
            value=nopat / average_capital,
            unit="ratio",
            reported_or_derived="derived",
            source_document_id="+".join(item.source_document_id for item in facts),
            source_occurrence_id="+".join(item.source_occurrence_id for item in facts),
            semantic_mapping=f"standard_roic:{excess_cash_policy_id}",
            derivation_formula=formula,
            input_fact_ids=tuple(item.fact_id for item in facts),
            quality="DERIVED_SAFE",
        ),
        audit={
            "effective_tax_rate": str(tax_rate),
            "nopat": str(nopat),
            "average_invested_capital": str(average_capital),
        },
    )
