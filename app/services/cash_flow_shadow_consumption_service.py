from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from enum import StrEnum
from typing import Iterable, Mapping, Sequence

from app.services.cash_flow_capital_efficiency_service import (
    EligibilityStatus,
    FinancialFact,
    Metric,
    PeriodIdentity,
    PeriodType,
)


CONTRACT_VERSION = "cash-flow-shadow-consumption-v1"


class FreshnessState(StrEnum):
    CURRENT_FORMAL = "CURRENT_FORMAL"
    FORMAL_LAGGING_PROVISIONAL = "FORMAL_LAGGING_PROVISIONAL"
    STALE_FORMAL = "STALE_FORMAL"
    FORMAL_ALIGNMENT_UNAVAILABLE = "FORMAL_ALIGNMENT_UNAVAILABLE"
    BLOCKED = "BLOCKED"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class UsageMode(StrEnum):
    FULL_FCF_CONTEXT = "FULL_FCF_CONTEXT"
    OCF_ONLY_CONTEXT = "OCF_ONLY_CONTEXT"
    CAPEX_CONTEXT_ONLY = "CAPEX_CONTEXT_ONLY"
    LATEST_FORMAL_CONTEXT_ONLY = "LATEST_FORMAL_CONTEXT_ONLY"
    SUPPRESSED = "SUPPRESSED"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class EarningsAlignmentState(StrEnum):
    ALIGNED = "ALIGNED"
    CASH_FLOW_NEWER = "CASH_FLOW_NEWER_THAN_OPERATING_EARNINGS"
    OPERATING_EARNINGS_NEWER = "OPERATING_EARNINGS_NEWER_THAN_CASH_FLOW"
    UNKNOWN = "UNKNOWN"


class RelationType(StrEnum):
    POSITIVE_HIGHER = "positive_to_positive_higher"
    POSITIVE_LOWER = "positive_to_positive_lower"
    NEGATIVE_LESS_NEGATIVE = "negative_to_negative_less_negative"
    NEGATIVE_MORE_NEGATIVE = "negative_to_negative_more_negative"
    NEGATIVE_TO_POSITIVE = "negative_to_positive"
    POSITIVE_TO_NEGATIVE = "positive_to_negative"
    ZERO_TO_POSITIVE = "zero_to_positive"
    ZERO_TO_NEGATIVE = "zero_to_negative"
    POSITIVE_TO_ZERO = "positive_to_zero"
    NEGATIVE_TO_ZERO = "negative_to_zero"
    UNCHANGED = "unchanged"


@dataclass(frozen=True)
class ComparableRelation:
    metric: Metric
    current_fact_id: str
    prior_fact_id: str
    relation: RelationType


@dataclass(frozen=True)
class ShadowNumericClaim:
    fact_id: str
    semantic_type: str
    value: str
    display: str
    currency: str
    unit: str
    text_ref: str = "business_earnings.text"
    owner: str = "business_earnings"


@dataclass(frozen=True)
class ShadowReasoning:
    text: str
    fact_ids: tuple[str, ...]
    numeric_claims: tuple[ShadowNumericClaim, ...]


@dataclass(frozen=True)
class CashFlowReasoningContext:
    ticker: str
    status: str
    usage_mode: UsageMode
    point_in_time_cutoff: date
    primary_period: PeriodIdentity | None
    primary_filing_date: date | None
    freshness_state: FreshnessState
    earnings_alignment_state: EarningsAlignmentState
    industry_applicability: str
    materiality_reason: str | None
    ocf_fact_id: str | None
    capex_fact_id: str | None
    fcf_fact_id: str | None
    prior_comparable_refs: tuple[str, ...]
    deterministic_relations: tuple[ComparableRelation, ...]
    consumption_eligible: bool
    shadow_used: bool
    allowed_reasoning_roles: tuple[str, ...]
    prohibited_claims: tuple[str, ...]
    suppression_reasons: tuple[str, ...]
    point_in_time_exclusions: tuple[dict[str, str], ...]


_CASH_FLOW_LANGUAGE = re.compile(
    r"(?:OCF|FCF|CAPEX)|영업현금흐름|잉여현금흐름|현금흐름|현금전환|현금소진|"
    r"설비투자|PPE\s*(?:CAPEX|취득)",
    re.IGNORECASE,
)
_CASH_FLOW_MISSING = re.compile(
    r"(?=.*(?:OCF|FCF|영업현금흐름|잉여현금흐름))"
    r"(?=.*(?:없|미확인|확인되지|확인할\s*수\s*없|부족)).+",
    re.IGNORECASE,
)
_CURRENT_LANGUAGE = re.compile(r"현재|이번\s*분기|최신\s*(?:분기|FCF|현금)")
_MANAGEMENT_FCF_LANGUAGE = re.compile(
    r"회사(?:가|의)?\s*(?:보고(?:한)?|정의(?:한)?)?\s*FCF|management[- ]defined\s*FCF",
    re.IGNORECASE,
)
_UNSUPPORTED_METRICS = re.compile(
    r"FCF\s*(?:yield|수익률|/\s*share|주당)|EV\s*/\s*FCF|P\s*/\s*FCF|"
    r"\bROIC\b|자본수익률|\bCCC\b|현금전환주기|\bDSO\b|\bDPO\b|"
    r"재고일수",
    re.IGNORECASE,
)
_RUNWAY_MONTHS = re.compile(r"(?:runway|현금\s*여력).{0,16}\d+(?:\.\d+)?\s*개월")


def industry_cash_flow_applicability(
    industry: str,
    *,
    financial_type: str,
) -> str:
    if financial_type == "financial" or industry == "insurance_reinsurance":
        return "NOT_APPLICABLE"
    if industry == "biotech":
        return "PRIMARY_AS_CASH_BURN"
    if industry in {
        "memory_semiconductor",
        "cloud_platform_software",
        "automotive",
        "transport_logistics",
        "steel_materials",
        "industrial_epc",
        "aerospace_epc",
        "hpc_data_center",
    }:
        return "PRIMARY"
    return "SECONDARY"


def _fact_sort_key(fact: FinancialFact) -> tuple[object, ...]:
    return (
        fact.period.end,
        fact.period.start,
        fact.filing_date,
        fact.fact_id,
    )


def point_in_time_facts(
    facts: Iterable[FinancialFact],
    *,
    cutoff: date,
) -> tuple[tuple[FinancialFact, ...], tuple[dict[str, str], ...]]:
    values = tuple(facts)
    by_id = {item.fact_id: item for item in values}
    excluded: dict[str, str] = {}
    for fact in values:
        if fact.filing_date is None:
            excluded[fact.fact_id] = "source_filing_date_missing"
        elif fact.filing_date > cutoff:
            excluded[fact.fact_id] = "future_filing_after_replay_cutoff"

    changed = True
    while changed:
        changed = False
        for fact in values:
            if fact.fact_id in excluded or not fact.input_fact_ids:
                continue
            if any(fact_id not in by_id for fact_id in fact.input_fact_ids):
                excluded[fact.fact_id] = "derived_input_fact_missing"
                changed = True
            elif any(fact_id in excluded for fact_id in fact.input_fact_ids):
                excluded[fact.fact_id] = "derived_input_not_point_in_time_safe"
                changed = True

    safe = tuple(item for item in values if item.fact_id not in excluded)
    audit = tuple(
        {"fact_id": fact_id, "reason": reason}
        for fact_id, reason in sorted(excluded.items())
    )
    return safe, audit


def classify_relation(prior: Decimal, current: Decimal) -> RelationType:
    if current == prior:
        return RelationType.UNCHANGED
    if prior < 0 < current:
        return RelationType.NEGATIVE_TO_POSITIVE
    if prior > 0 > current:
        return RelationType.POSITIVE_TO_NEGATIVE
    if prior == 0:
        return (
            RelationType.ZERO_TO_POSITIVE
            if current > 0
            else RelationType.ZERO_TO_NEGATIVE
        )
    if current == 0:
        return (
            RelationType.POSITIVE_TO_ZERO
            if prior > 0
            else RelationType.NEGATIVE_TO_ZERO
        )
    if prior > 0 and current > 0:
        return (
            RelationType.POSITIVE_HIGHER
            if current > prior
            else RelationType.POSITIVE_LOWER
        )
    return (
        RelationType.NEGATIVE_LESS_NEGATIVE
        if current > prior
        else RelationType.NEGATIVE_MORE_NEGATIVE
    )


def _comparison_compatible(current: FinancialFact, prior: FinancialFact) -> bool:
    if current.fact_id == prior.fact_id or current.metric != prior.metric:
        return False
    if current.period.period_type != prior.period.period_type:
        return False
    if current.period.duration_days != prior.period.duration_days:
        return False
    if current.period.fiscal_year != prior.period.fiscal_year + 1:
        return False
    if current.period.fiscal_quarter != prior.period.fiscal_quarter:
        return False
    if prior.period.end >= current.period.end:
        return False
    return all(
        getattr(current, field_name) == getattr(prior, field_name)
        for field_name in (
            "issuer_id",
            "currency",
            "unit",
            "entity_scope",
            "statement_basis",
            "semantic_mapping",
        )
    )


def select_prior_comparable(
    current: FinancialFact,
    facts: Iterable[FinancialFact],
) -> FinancialFact | None:
    candidates = [item for item in facts if _comparison_compatible(current, item)]
    return max(candidates, key=_fact_sort_key) if candidates else None


def _primary_fact(
    facts: Sequence[FinancialFact],
    metric: Metric,
    *,
    preferred_fact_id: str | None = None,
) -> FinancialFact | None:
    candidates = [
        item
        for item in facts
        if item.metric == metric
        and item.eligibility == EligibilityStatus.ELIGIBLE
        and item.period.period_type in {PeriodType.YTD, PeriodType.FY}
    ]
    if preferred_fact_id:
        preferred = next(
            (item for item in candidates if item.fact_id == preferred_fact_id), None
        )
        if preferred is not None:
            return preferred
    return max(candidates, key=_fact_sort_key) if candidates else None


def _input_facts(
    fact: FinancialFact | None,
    facts: Mapping[str, FinancialFact],
) -> tuple[FinancialFact | None, FinancialFact | None]:
    if fact is None or fact.metric != Metric.FCF or len(fact.input_fact_ids) != 2:
        return None, None
    values = [facts.get(fact_id) for fact_id in fact.input_fact_ids]
    ocf = next((item for item in values if item and item.metric == Metric.OCF), None)
    capex = next((item for item in values if item and item.metric == Metric.CAPEX), None)
    return ocf, capex


def _freshness(
    primary: FinancialFact,
    *,
    latest_formal_period: date | None,
    latest_provisional_period: date | None,
) -> FreshnessState:
    if latest_formal_period is None:
        return FreshnessState.FORMAL_ALIGNMENT_UNAVAILABLE
    if primary.period.end < latest_formal_period:
        return FreshnessState.STALE_FORMAL
    if primary.period.end > latest_formal_period:
        return FreshnessState.FORMAL_ALIGNMENT_UNAVAILABLE
    if latest_provisional_period and latest_provisional_period > latest_formal_period:
        return FreshnessState.FORMAL_LAGGING_PROVISIONAL
    return FreshnessState.CURRENT_FORMAL


def _earnings_alignment(
    primary: FinancialFact,
    latest_operating_earnings_period: date | None,
) -> EarningsAlignmentState:
    if latest_operating_earnings_period is None:
        return EarningsAlignmentState.UNKNOWN
    if primary.period.end == latest_operating_earnings_period:
        return EarningsAlignmentState.ALIGNED
    if primary.period.end > latest_operating_earnings_period:
        return EarningsAlignmentState.CASH_FLOW_NEWER
    return EarningsAlignmentState.OPERATING_EARNINGS_NEWER


def _materiality_reason(
    *,
    applicability: str,
    existing_unknowns: Sequence[str],
    materiality_signals: Sequence[str],
) -> str | None:
    if any(_CASH_FLOW_LANGUAGE.search(item) for item in existing_unknowns):
        return "existing_cash_flow_unknown"
    if any(_CASH_FLOW_LANGUAGE.search(item) for item in materiality_signals):
        return "existing_cash_flow_driver"
    if applicability.startswith("PRIMARY"):
        return "industry_primary_cash_flow"
    return None


def build_cash_flow_reasoning_context(
    *,
    ticker: str,
    industry: str,
    financial_type: str,
    core_status: str,
    facts: Iterable[FinancialFact],
    cutoff: date,
    latest_formal_period: date | None,
    latest_provisional_period: date | None = None,
    latest_operating_earnings_period: date | None = None,
    preferred_fcf_fact_id: str | None = None,
    existing_unknowns: Sequence[str] = (),
    materiality_signals: Sequence[str] = (),
) -> CashFlowReasoningContext:
    applicability = industry_cash_flow_applicability(
        industry, financial_type=financial_type
    )
    prohibited = (
        "future_fact_used",
        "stale_as_current",
        "mixed_period_comparison",
        "management_fcf_mislabel",
        "fcf_yield_or_per_share",
        "ccc_or_roic",
        "automatic_thesis_or_valuation_change",
    )
    if applicability == "NOT_APPLICABLE" or core_status == "NOT_APPLICABLE":
        return CashFlowReasoningContext(
            ticker=ticker,
            status="NOT_APPLICABLE",
            usage_mode=UsageMode.NOT_APPLICABLE,
            point_in_time_cutoff=cutoff,
            primary_period=None,
            primary_filing_date=None,
            freshness_state=FreshnessState.NOT_APPLICABLE,
            earnings_alignment_state=EarningsAlignmentState.UNKNOWN,
            industry_applicability=applicability,
            materiality_reason=None,
            ocf_fact_id=None,
            capex_fact_id=None,
            fcf_fact_id=None,
            prior_comparable_refs=(),
            deterministic_relations=(),
            consumption_eligible=False,
            shadow_used=False,
            allowed_reasoning_roles=(),
            prohibited_claims=prohibited,
            suppression_reasons=("financial_industry_not_applicable",),
            point_in_time_exclusions=(),
        )

    safe, pit_exclusions = point_in_time_facts(facts, cutoff=cutoff)
    by_id = {item.fact_id: item for item in safe}
    fcf = _primary_fact(
        safe, Metric.FCF, preferred_fact_id=preferred_fcf_fact_id
    )
    ocf, capex = _input_facts(fcf, by_id)
    base_mode = UsageMode.FULL_FCF_CONTEXT
    primary = fcf
    if primary is None:
        ocf = _primary_fact(safe, Metric.OCF)
        capex = None
        primary = ocf
        base_mode = UsageMode.OCF_ONLY_CONTEXT
    if primary is None:
        capex = _primary_fact(safe, Metric.CAPEX)
        primary = capex
        base_mode = UsageMode.CAPEX_CONTEXT_ONLY
    if primary is None:
        reasons = ["canonical_cash_flow_fact_unavailable"]
        if pit_exclusions:
            reasons.append("point_in_time_safe_fact_unavailable")
        return CashFlowReasoningContext(
            ticker=ticker,
            status="BLOCKED",
            usage_mode=UsageMode.SUPPRESSED,
            point_in_time_cutoff=cutoff,
            primary_period=None,
            primary_filing_date=None,
            freshness_state=FreshnessState.BLOCKED,
            earnings_alignment_state=EarningsAlignmentState.UNKNOWN,
            industry_applicability=applicability,
            materiality_reason=None,
            ocf_fact_id=None,
            capex_fact_id=None,
            fcf_fact_id=None,
            prior_comparable_refs=(),
            deterministic_relations=(),
            consumption_eligible=False,
            shadow_used=False,
            allowed_reasoning_roles=(),
            prohibited_claims=prohibited,
            suppression_reasons=tuple(reasons),
            point_in_time_exclusions=pit_exclusions,
        )

    freshness = _freshness(
        primary,
        latest_formal_period=latest_formal_period,
        latest_provisional_period=latest_provisional_period,
    )
    materiality = _materiality_reason(
        applicability=applicability,
        existing_unknowns=existing_unknowns,
        materiality_signals=materiality_signals,
    )
    consumption_eligible = freshness in {
        FreshnessState.CURRENT_FORMAL,
        FreshnessState.FORMAL_LAGGING_PROVISIONAL,
    }
    shadow_used = freshness == FreshnessState.CURRENT_FORMAL and materiality is not None
    suppression: list[str] = []
    usage_mode = base_mode
    status = "READY"
    if freshness == FreshnessState.FORMAL_LAGGING_PROVISIONAL:
        usage_mode = UsageMode.LATEST_FORMAL_CONTEXT_ONLY
        status = "CONTEXT_ONLY"
        suppression.append("newer_provisional_period_not_cash_flow_aligned")
    elif freshness != FreshnessState.CURRENT_FORMAL:
        usage_mode = UsageMode.SUPPRESSED
        status = "SUPPRESSED"
        suppression.append(freshness.value.lower())
    elif materiality is None:
        usage_mode = UsageMode.SUPPRESSED
        status = "SUPPRESSED"
        shadow_used = False
        suppression.append("cash_flow_not_material_to_current_reasoning")

    relations: list[ComparableRelation] = []
    prior_ids: list[str] = []
    for current in (ocf, capex, fcf):
        if current is None:
            continue
        prior = select_prior_comparable(current, safe)
        if prior is None:
            continue
        prior_ids.append(prior.fact_id)
        relations.append(
            ComparableRelation(
                metric=current.metric,
                current_fact_id=current.fact_id,
                prior_fact_id=prior.fact_id,
                relation=classify_relation(prior.value, current.value),
            )
        )

    return CashFlowReasoningContext(
        ticker=ticker,
        status=status,
        usage_mode=usage_mode,
        point_in_time_cutoff=cutoff,
        primary_period=primary.period,
        primary_filing_date=primary.filing_date,
        freshness_state=freshness,
        earnings_alignment_state=_earnings_alignment(
            primary, latest_operating_earnings_period
        ),
        industry_applicability=applicability,
        materiality_reason=materiality,
        ocf_fact_id=ocf.fact_id if ocf else None,
        capex_fact_id=capex.fact_id if capex else None,
        fcf_fact_id=fcf.fact_id if fcf else None,
        prior_comparable_refs=tuple(prior_ids),
        deterministic_relations=tuple(relations),
        consumption_eligible=consumption_eligible,
        shadow_used=shadow_used,
        allowed_reasoning_roles=("business_earnings", "earnings_quality"),
        prohibited_claims=prohibited,
        suppression_reasons=tuple(suppression),
        point_in_time_exclusions=pit_exclusions,
    )


def format_financial_amount(fact: FinancialFact) -> str:
    value = fact.value
    absolute = abs(value)
    suffix = ""
    divisor = Decimal(1)
    if absolute >= Decimal("1000000000"):
        divisor = Decimal("1000000000")
        suffix = "B"
    elif absolute >= Decimal("1000000"):
        divisor = Decimal("1000000")
        suffix = "M"
    elif absolute >= Decimal("1000"):
        divisor = Decimal("1000")
        suffix = "K"
    scaled = value / divisor
    rendered = f"{scaled:.2f}".rstrip("0").rstrip(".")
    prefix = {"USD": "$", "TWD": "NT$", "KRW": "₩"}.get(
        fact.currency, f"{fact.currency} "
    )
    return f"{prefix}{rendered}{suffix}"


def period_label(period: PeriodIdentity) -> str:
    if period.period_type == PeriodType.FY:
        return f"{period.fiscal_year} 회계연도 연간"
    if period.period_type == PeriodType.YTD:
        if period.fiscal_quarter == 2:
            return f"{period.fiscal_year} 회계연도 상반기 누계"
        if period.fiscal_quarter:
            return f"{period.fiscal_year} 회계연도 {period.fiscal_quarter}분기 누계"
        return f"{period.fiscal_year} 회계연도 누계"
    if period.period_type == PeriodType.QTD:
        return f"{period.fiscal_year} 회계연도 {period.fiscal_quarter}분기 단독"
    return f"{period.end.isoformat()} 종료 TTM"


def _industry_driver(industry: str, source_text: str) -> str:
    lowered = source_text.casefold()
    if industry == "memory_semiconductor":
        if "첨단공정" in source_text or "wafer" in lowered or "foundry" in lowered:
            return "semiconductor_foundry"
        if "nand" in lowered and "hbm" not in lowered:
            return "memory_nand"
        return "memory_hbm"
    if industry == "cloud_platform_software":
        if "software" in lowered or "consulting" in lowered or "red hat" in lowered:
            return "software_services"
        return "cloud_platform"
    if industry == "hpc_data_center":
        if "코로케이션" in source_text or "colocation" in lowered:
            return "colocation_billing"
        if (
            "hpc lease" in lowered
            or "lease revenue" in lowered
            or "가동 전력" in source_text
        ):
            return "hpc_lease"
        if "billing" in lowered:
            return "colocation_billing"
        return "project_noi"
    if industry == "general_non_financial" and "usdc" in lowered:
        return "stablecoin_platform"
    return industry


def _claim(fact: FinancialFact) -> ShadowNumericClaim:
    return ShadowNumericClaim(
        fact_id=fact.fact_id,
        semantic_type=fact.metric.value,
        value=str(fact.value),
        display=format_financial_amount(fact),
        currency=fact.currency,
        unit=fact.unit,
    )


def _alignment_subject(driver: str) -> str:
    return {
        "cloud_platform": "Cloud 성장·마진",
        "software_services": "Software·Consulting 성장",
        "colocation_billing": "코로케이션 가동·청구",
        "hpc_lease": "HPC lease 가동·청구",
        "project_noi": "계약 가동·NOI",
        "memory_hbm": "HBM·메모리 ASP",
        "memory_nand": "NAND 수요·ASP",
        "semiconductor_foundry": "첨단공정 수요·마진",
        "biotech": "임상·milestone",
        "automotive": "자동차 마진·성장투자",
        "stablecoin_platform": "준비금·비이자 수익",
    }.get(driver, "사업 성과")


def render_shadow_reasoning(
    context: CashFlowReasoningContext,
    facts: Mapping[str, FinancialFact],
    *,
    industry: str,
    source_text: str,
) -> ShadowReasoning | None:
    if not context.shadow_used or context.primary_period is None:
        return None
    label = period_label(context.primary_period)
    driver = _industry_driver(industry, source_text)
    fcf = facts.get(context.fcf_fact_id or "")
    ocf = facts.get(context.ocf_fact_id or "")
    capex = facts.get(context.capex_fact_id or "")
    if context.usage_mode == UsageMode.OCF_ONLY_CONTEXT and ocf is not None:
        claim = _claim(ocf)
        text = (
            f"{label} 영업현금흐름은 {claim.display}로 확인되지만 검증된 PPE 취득 현금지출이 "
            "없어 잉여현금흐름은 계산하지 않습니다. 계약 가동·NOI와 "
            "프로젝트 자금조달을 함께 확인해야 합니다."
        )
        if context.earnings_alignment_state != EarningsAlignmentState.ALIGNED:
            text += (
                f" 기존 {_alignment_subject(driver)} 문맥과 기간이 달라 해당 성과 변화와 "
                "직접 연결하지 않습니다."
            )
        return ShadowReasoning(text, (ocf.fact_id,), (claim,))
    if fcf is None or ocf is None or capex is None:
        return None
    claim = _claim(fcf)
    sign = "양수" if fcf.value >= 0 else "음수"
    relation = next(
        (
            item.relation.value
            for item in context.deterministic_relations
            if item.metric == Metric.FCF
        ),
        None,
    )
    relation_note = {
        RelationType.NEGATIVE_TO_POSITIVE.value: "전년 비교기간의 음수에서 양수로 전환됐지만 지속성은 별도 확인이 필요합니다.",
        RelationType.POSITIVE_TO_NEGATIVE.value: "전년 비교기간의 양수에서 음수로 전환됐고 OCF와 재투자 요인을 나눠 봐야 합니다.",
        RelationType.POSITIVE_HIGHER.value: "전년 비교기간보다 늘었지만 이를 구조적 개선으로 자동 확정하지 않습니다.",
        RelationType.POSITIVE_LOWER.value: "전년 비교기간보다 줄었지만 OCF와 재투자 변화를 분리해야 합니다.",
        RelationType.NEGATIVE_LESS_NEGATIVE.value: "전년 비교기간보다 적자 폭이 줄었지만 현금소진이 끝났다는 뜻은 아닙니다.",
        RelationType.NEGATIVE_MORE_NEGATIVE.value: "전년 비교기간보다 적자 폭이 커졌고 OCF와 PPE 재투자의 기여를 나눠 봐야 합니다.",
    }.get(relation, "비교 가능한 전년 현금흐름 없이 단일기간 수치만으로 구조 변화를 확정하지 않습니다.")
    if driver == "cloud_platform":
        text = (
            f"{label} 잉여현금흐름(OCF-PPE CAPEX 기준)은 {claim.display}로 {sign}입니다. "
            f"AI·Cloud 투자 회수는 Cloud 성장과 마진을 함께 봐야 하며, {relation_note}"
        )
    elif driver == "software_services":
        text = (
            f"{label} PPE-only 잉여현금흐름은 {claim.display}로 {sign}입니다. 회사 정의 FCF와 "
            f"혼동하지 않고 Software·Consulting 전환과 함께 해석하며, {relation_note}"
        )
    elif driver in {"colocation_billing", "hpc_lease", "project_noi"}:
        mechanism = {
            "colocation_billing": "코로케이션 가동·청구",
            "hpc_lease": "HPC lease 가동 전력·청구",
            "project_noi": "계약 가동·NOI",
        }[driver]
        text = (
            f"{label} 잉여현금흐름(OCF-PPE CAPEX 기준)은 {claim.display}로 {sign}입니다. "
            f"build-out 재투자를 사업 실패로 자동 해석하지 않고 {mechanism}, 자금조달을 "
            f"함께 확인하며, {relation_note}"
        )
    elif driver == "memory_hbm":
        text = (
            f"{label} PPE 재투자 후 잉여현금흐름은 {claim.display}로 {sign}입니다. ASP·HBM "
            f"믹스·재고 사이클과 CAPEX 시점을 분리해 지속성을 판단하며, {relation_note}"
        )
    elif driver == "memory_nand":
        text = (
            f"{label} PPE 재투자 후 잉여현금흐름은 {claim.display}로 {sign}입니다. NAND ASP·"
            f"데이터센터 수요·재고와 설비투자 시점을 분리해 지속성을 판단하며, {relation_note}"
        )
    elif driver == "semiconductor_foundry":
        text = (
            f"{label} PPE 재투자 후 잉여현금흐름은 {claim.display}로 {sign}입니다. 첨단공정 "
            f"가동률·wafer ASP·마진과 투자 회수를 함께 확인하며, {relation_note}"
        )
    elif driver == "biotech":
        text = (
            f"{label} 잉여현금흐름(OCF-PPE CAPEX 기준)은 {claim.display}로 {sign}이며 현금소진 "
            f"근거로만 사용합니다. 보유현금·milestone·조달 근거 없이 runway를 계산하지 않으며, {relation_note}"
        )
    elif driver == "automotive":
        text = (
            f"{label} PPE 재투자 후 잉여현금흐름은 {claim.display}로 {sign}입니다. 자동차 "
            f"마진과 성장투자 회수를 함께 보고 단일 현금흐름으로 신사업 논리를 무효화하지 않으며, {relation_note}"
        )
    elif driver == "stablecoin_platform":
        text = (
            f"{label} 잉여현금흐름(OCF-PPE CAPEX 기준)은 {claim.display}로 {sign}입니다. 준비금 "
            f"수익과 비이자 플랫폼 수익의 현금전환을 분리해 확인하며, {relation_note}"
        )
    else:
        text = (
            f"{label} 잉여현금흐름(OCF-PPE CAPEX 기준)은 {claim.display}로 {sign}입니다. "
            f"사업 성과와 재투자 부담을 분리해 해석하며, {relation_note}"
        )
    if context.earnings_alignment_state != EarningsAlignmentState.ALIGNED:
        text += (
            f" 기존 {_alignment_subject(driver)} 문맥과 기간이 달라 해당 성과 변화와 "
            "직접 연결하지 않습니다."
        )
    return ShadowReasoning(
        text=text,
        fact_ids=(ocf.fact_id, capex.fact_id, fcf.fact_id),
        numeric_claims=(claim,),
    )


def _remaining_unknown(industry: str, source_text: str) -> str:
    driver = _industry_driver(industry, source_text)
    return {
        "cloud_platform": "Cloud 성장·마진과 AI 투자 회수의 지속성은 여전히 미확인입니다.",
        "software_services": "Software·Consulting 성장과 인수자금·부채의 장기 부담은 여전히 미확인입니다.",
        "colocation_billing": "가동 전력의 청구 전환, 코로케이션 마진과 희석 경로는 여전히 미확인입니다.",
        "hpc_lease": "가동·건설 전력의 lease 매출 전환과 남은 자금조달·희석 경로는 여전히 미확인입니다.",
        "project_noi": "계약 전력의 가동·NOI와 프로젝트별 자금조달 구조는 여전히 미확인입니다.",
        "memory_hbm": "ASP·HBM 믹스·재고와 사이클 현금창출의 지속성은 여전히 미확인입니다.",
        "memory_nand": "NAND ASP·데이터센터 수요·재고와 사이클 현금창출의 지속성은 여전히 미확인입니다.",
        "semiconductor_foundry": "첨단공정 가동률·wafer ASP·마진과 투자 회수의 지속성은 여전히 미확인입니다.",
        "biotech": "임상 일정·milestone·보유현금과 추가 조달 필요 시점은 여전히 미확인입니다.",
        "automotive": "자동차 마진·재고와 성장투자 회수 속도는 여전히 미확인입니다.",
        "stablecoin_platform": "USDC 점유율, 비이자 수익과 수익배분의 지속성은 여전히 미확인입니다.",
    }.get(driver, "사업 성과와 재투자의 지속 가능한 연결은 여전히 미확인입니다.")


def _lagging_unknown(industry: str, source_text: str) -> str:
    driver = _industry_driver(industry, source_text)
    consequence = {
        "memory_hbm": "HBM·메모리 ASP와 사이클 현금전환",
        "memory_nand": "NAND 수요·재고와 사이클 현금전환",
        "semiconductor_foundry": "첨단공정 수요·마진과 투자 회수",
        "stablecoin_platform": "준비금·비이자 수익의 현금전환",
        "cloud_platform": "Cloud 성장·마진의 현금전환",
        "software_services": "Software·Consulting 성장의 현금전환",
        "colocation_billing": "코로케이션 가동·청구의 현금전환",
        "hpc_lease": "HPC lease 가동·청구의 현금전환",
        "project_noi": "계약 가동·NOI의 현금전환",
        "biotech": "임상·milestone 이후 현금소진 경로",
        "automotive": "자동차 마진과 성장투자의 현금전환",
    }.get(driver, "사업 성과의 현금전환")
    return (
        "최신 잠정 실적 기간과 정렬되는 정식 OCF·PPE CAPEX·FCF가 없어 "
        f"{consequence}의 현재 방향은 아직 판단하지 않습니다."
    )


def resolve_cash_flow_unknowns(
    unknowns: Sequence[str],
    context: CashFlowReasoningContext,
    *,
    industry: str,
    source_text: str,
) -> tuple[tuple[str, ...], dict[str, int]]:
    output = list(unknowns)
    matching = [index for index, value in enumerate(output) if _CASH_FLOW_LANGUAGE.search(value)]
    audit = {"before": len(matching), "resolved": 0, "still_valid": 0, "suppressed_not_applicable": 0}
    if not matching:
        return tuple(output), audit
    if context.freshness_state == FreshnessState.NOT_APPLICABLE:
        for index in reversed(matching):
            output.pop(index)
        if industry == "insurance_reinsurance":
            output.append("합산비율, 자기자본이익률과 자본적정성의 동행은 여전히 미확인입니다.")
        audit["suppressed_not_applicable"] = len(matching)
        return tuple(output), audit
    if context.shadow_used:
        first = matching[0]
        if context.usage_mode == UsageMode.OCF_ONLY_CONTEXT:
            output[first] = (
                "영업현금흐름은 확인되지만 검증된 PPE 취득 현금지출이 없어 "
                "최신 FCF는 계산하지 않습니다."
            )
            audit["still_valid"] = 1
        else:
            output[first] = _remaining_unknown(industry, source_text)
            audit["resolved"] = 1
        for index in reversed(matching[1:]):
            output.pop(index)
            audit["resolved"] += 1
        return tuple(output), audit
    if context.freshness_state == FreshnessState.FORMAL_LAGGING_PROVISIONAL:
        output[matching[0]] = _lagging_unknown(industry, source_text)
        for index in reversed(matching[1:]):
            output.pop(index)
        audit["still_valid"] = 1
        return tuple(output), audit
    audit["still_valid"] = len(matching)
    return tuple(output), audit


def validate_shadow_reasoning(
    context: CashFlowReasoningContext,
    facts: Mapping[str, FinancialFact],
    reasoning: ShadowReasoning | None,
    *,
    unknowns: Sequence[str] = (),
    valuation_changed: bool = False,
    thesis_status_changed: bool = False,
) -> tuple[str, ...]:
    errors: list[str] = []
    text = reasoning.text if reasoning else ""
    if context.freshness_state == FreshnessState.NOT_APPLICABLE and reasoning:
        errors.append("industry_not_applicable_used")
    if context.freshness_state in {
        FreshnessState.STALE_FORMAL,
        FreshnessState.FORMAL_ALIGNMENT_UNAVAILABLE,
        FreshnessState.FORMAL_LAGGING_PROVISIONAL,
    } and reasoning:
        errors.append("stale_or_lagging_fact_rendered")
        if _CURRENT_LANGUAGE.search(text):
            errors.append("stale_as_current")
    if reasoning and not context.shadow_used:
        errors.append("suppressed_context_rendered")
    allowed = {
        item
        for item in (context.ocf_fact_id, context.capex_fact_id, context.fcf_fact_id)
        if item
    }
    if reasoning:
        for fact_id in reasoning.fact_ids:
            fact = facts.get(fact_id)
            if fact is None:
                errors.append("cash_flow_fact_missing")
            elif fact_id not in allowed:
                errors.append("cash_flow_fact_not_primary_context")
            elif fact.filing_date > context.point_in_time_cutoff:
                errors.append("future_fact_used")
        for claim in reasoning.numeric_claims:
            fact = facts.get(claim.fact_id)
            if fact is None:
                errors.append("numeric_fact_missing")
                continue
            if claim.fact_id not in reasoning.fact_ids:
                errors.append("numeric_fact_not_in_reasoning_lineage")
            if claim.semantic_type != fact.metric.value:
                errors.append("numeric_semantic_mismatch")
            if Decimal(claim.value) != fact.value:
                errors.append("numeric_value_mismatch")
            if claim.display != format_financial_amount(fact) or claim.display not in text:
                errors.append("numeric_display_unresolved")
            if claim.currency != fact.currency or claim.unit != fact.unit:
                errors.append("numeric_currency_or_unit_mismatch")
            if claim.owner != "business_earnings":
                errors.append("cash_flow_numeric_owner_invalid")
            if fact.period.period_type == PeriodType.YTD and "분기" in text and "누계" not in text:
                errors.append("ytd_mislabeled_as_quarter")
            if fact.metric == Metric.CAPEX and "PPE" not in text:
                errors.append("capex_scope_overclaim")
        if (
            "잉여현금흐름" in text
            and context.fcf_fact_id not in reasoning.fact_ids
            and "계산하지 않습니다" not in text
        ):
            errors.append("fcf_claim_without_fact")
        if _MANAGEMENT_FCF_LANGUAGE.search(text) and "혼동하지" not in text:
            errors.append("management_fcf_mislabel")
        if _UNSUPPORTED_METRICS.search(text):
            errors.append("unsupported_cash_flow_metric")
        if _RUNWAY_MONTHS.search(text):
            errors.append("unsupported_runway_inference")
    if context.shadow_used and context.fcf_fact_id and any(
        _CASH_FLOW_MISSING.search(value) for value in unknowns
    ):
        errors.append("resolved_unknown_claimed_missing")
    if valuation_changed:
        errors.append("cashflow_based_valuation_change")
    if thesis_status_changed:
        errors.append("cashflow_based_thesis_status_change")
    return tuple(dict.fromkeys(errors))


def context_to_dict(context: CashFlowReasoningContext) -> dict[str, object]:
    period = context.primary_period
    return {
        "contract": CONTRACT_VERSION,
        "ticker": context.ticker,
        "status": context.status,
        "usage_mode": context.usage_mode.value,
        "point_in_time_cutoff": context.point_in_time_cutoff.isoformat(),
        "primary_period": (
            {
                "period_start": period.start.isoformat(),
                "period_end": period.end.isoformat(),
                "period_type": period.period_type.value,
                "fiscal_year": period.fiscal_year,
                "fiscal_quarter": period.fiscal_quarter,
                "duration_days": period.duration_days,
            }
            if period
            else None
        ),
        "filing_date": (
            context.primary_filing_date.isoformat()
            if context.primary_filing_date
            else None
        ),
        "freshness_state": context.freshness_state.value,
        "earnings_alignment_state": context.earnings_alignment_state.value,
        "industry_applicability": context.industry_applicability,
        "materiality_reason": context.materiality_reason,
        "ocf_fact_ref": context.ocf_fact_id,
        "capex_fact_ref": context.capex_fact_id,
        "fcf_fact_ref": context.fcf_fact_id,
        "prior_comparable_refs": list(context.prior_comparable_refs),
        "deterministic_relations": [
            {
                "metric": item.metric.value,
                "current_fact_id": item.current_fact_id,
                "prior_fact_id": item.prior_fact_id,
                "relation": item.relation.value,
            }
            for item in context.deterministic_relations
        ],
        "consumption_eligible": context.consumption_eligible,
        "shadow_used": context.shadow_used,
        "allowed_reasoning_roles": list(context.allowed_reasoning_roles),
        "prohibited_claims": list(context.prohibited_claims),
        "suppression_reasons": list(context.suppression_reasons),
        "point_in_time_exclusions": list(context.point_in_time_exclusions),
    }


def reasoning_to_dict(reasoning: ShadowReasoning | None) -> dict[str, object] | None:
    if reasoning is None:
        return None
    return {
        "text": reasoning.text,
        "fact_ids": list(reasoning.fact_ids),
        "numeric_claims": [
            {
                "fact_id": item.fact_id,
                "semantic_type": item.semantic_type,
                "value": item.value,
                "display": item.display,
                "currency": item.currency,
                "unit": item.unit,
                "text_ref": item.text_ref,
                "owner": item.owner,
            }
            for item in reasoning.numeric_claims
        ],
    }
