from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass
from datetime import date
from decimal import Decimal
from enum import StrEnum
from functools import lru_cache
from pathlib import Path
from typing import Mapping, Sequence

from app.services.cash_flow_capital_efficiency_service import FinancialFact, Metric
from app.services.cash_flow_shadow_consumption_service import (
    CashFlowReasoningContext,
    FreshnessState,
)


CONTRACT_VERSION = "baseline-cash-flow-claim-consistency-v1"
CANONICAL_FACTS_REPORT = "20260820-phase9-0b-canonical-facts.json"


class ClaimMetric(StrEnum):
    OCF = "operating_cash_flow"
    FCF = "free_cash_flow"
    CASH_BURN = "cash_burn"


class ClaimState(StrEnum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    TURN_POSITIVE_REQUIRED = "turn_positive_required"
    UNAVAILABLE = "unavailable"


class ClaimScope(StrEnum):
    BACKEND_PPE_ONLY = "backend_ppe_only"
    MANAGEMENT_DEFINED = "management_defined"
    UNKNOWN = "unknown"


class ClaimCurrentness(StrEnum):
    EXPLICIT_CURRENT = "explicit_current"
    IMPLIED_CURRENT = "implied_current"
    HISTORICAL_QUALIFIED = "historical_qualified"
    FUTURE_CONDITION = "future_condition"
    UNKNOWN = "unknown"


class ConsistencyResult(StrEnum):
    CONSISTENT = "CONSISTENT"
    QUALIFIER_REQUIRED = "QUALIFIER_REQUIRED"
    STALE_CONFLICT = "STALE_CONFLICT"
    UNSUPPORTED_CLAIM = "UNSUPPORTED_CLAIM"
    NOT_COMPARABLE = "NOT_COMPARABLE"
    NO_CANONICAL_CHECK_AVAILABLE = "NO_CANONICAL_CHECK_AVAILABLE"


class RenderAction(StrEnum):
    KEEP = "KEEP"
    QUALIFY = "QUALIFY"
    SUPPRESS = "SUPPRESS"


@dataclass(frozen=True)
class CanonicalMetricEvidence:
    fact_id: str
    metric: str
    value: Decimal
    sign: ClaimState
    period_start: date
    period_end: date
    period_type: str
    fiscal_year: int
    fiscal_quarter: int | None
    scope: ClaimScope
    entity_scope: str
    currency: str
    unit: str
    filing_date: date


@dataclass(frozen=True)
class CanonicalCashFlowEvidence:
    ticker: str
    freshness_state: str
    fcf: CanonicalMetricEvidence | None
    ocf: CanonicalMetricEvidence | None
    denial_reasons: tuple[str, ...] = ()


@dataclass(frozen=True)
class BaselineCashFlowClaim:
    claim_id: str
    ticker: str
    text_ref: str
    section: str
    owner: str
    origin_type: str
    origin_version: str | None
    claim_span: str
    span_start: int
    span_end: int
    pattern_type: str
    metric_semantic: ClaimMetric
    state_or_sign: ClaimState
    period_type: str
    scope: ClaimScope
    entity_scope: str | None
    currency: str | None
    claim_currentness: ClaimCurrentness
    provenance_refs: tuple[str, ...]
    provenance_valid: bool


@dataclass(frozen=True)
class CashFlowClaimDecision:
    claim: BaselineCashFlowClaim
    canonical_comparison_fact_id: str | None
    comparability: str
    consistency_result: ConsistencyResult
    render_action: RenderAction
    suppression_reason: str | None = None
    required_qualifier: str | None = None


@dataclass(frozen=True)
class BaselineTextRepair:
    text: str
    decisions: tuple[CashFlowClaimDecision, ...]


_PATTERNS: tuple[tuple[str, re.Pattern[str], ClaimMetric, ClaimState], ...] = (
    (
        "fcf_turn_positive",
        re.compile(
            r"(?:PPE(?:-only|\s*기준)?\s*)?(?:FCF|잉여현금흐름)\s*흑자\s*전환(?:이|가|을|를)?",
            re.IGNORECASE,
        ),
        ClaimMetric.FCF,
        ClaimState.TURN_POSITIVE_REQUIRED,
    ),
    (
        "fcf_negative",
        re.compile(
            r"(?:PPE(?:-only|\s*기준)?\s*)?(?:FCF|잉여현금흐름)(?:은|는|이|가)?\s*(?:적자|음수)(?:로|가|이|은|는)?",
            re.IGNORECASE,
        ),
        ClaimMetric.FCF,
        ClaimState.NEGATIVE,
    ),
    (
        "fcf_positive",
        re.compile(
            r"(?:PPE(?:-only|\s*기준)?\s*)?(?:FCF|잉여현금흐름)(?:은|는|이|가)?\s*(?:흑자|양수)(?:로|가|이|은|는)?",
            re.IGNORECASE,
        ),
        ClaimMetric.FCF,
        ClaimState.POSITIVE,
    ),
    (
        "ocf_negative",
        re.compile(
            r"(?:OCF|영업현금흐름)(?:은|는|이|가)?\s*(?:적자|음수)(?:로|가|이|은|는)?",
            re.IGNORECASE,
        ),
        ClaimMetric.OCF,
        ClaimState.NEGATIVE,
    ),
    (
        "ocf_positive",
        re.compile(
            r"(?:OCF|영업현금흐름)(?:은|는|이|가)?\s*(?:흑자|양수)(?:로|가|이|은|는)?",
            re.IGNORECASE,
        ),
        ClaimMetric.OCF,
        ClaimState.POSITIVE,
    ),
    (
        "cash_burn",
        re.compile(
            r"(?:(?:높은|큰|지속되는|확대되는|증가하는|가속되는|급증하는)\s*"
            r"(?:현금소진|cash\s*burn)|(?:현금소진|cash\s*burn)(?:이|가)?\s*"
            r"(?:크|높|지속|확대|증가|가속|급증))",
            re.IGNORECASE,
        ),
        ClaimMetric.CASH_BURN,
        ClaimState.NEGATIVE,
    ),
    (
        "cash_flow_unavailable",
        re.compile(
            r"(?:(?:OCF|FCF|영업현금흐름|잉여현금흐름)[^.!?\n]{0,36}"
            r"(?:없|미확인|확인되지|확인할\s*수\s*없))",
            re.IGNORECASE,
        ),
        ClaimMetric.FCF,
        ClaimState.UNAVAILABLE,
    ),
)
_CURRENT = re.compile(r"현재|이번\s*(?:분기|반기|연도)|최신", re.IGNORECASE)
_HISTORICAL = re.compile(
    r"20\d{2}(?:년|[-.]\d{1,2})|과거|이전|전년|직전|FY\s*20\d{2}",
    re.IGNORECASE,
)
_FUTURE_SECTIONS = {
    "strengthen_signals",
    "weaken_signals",
    "invalidation_signals",
    "validation_metrics",
    "persistent_risks",
    "next_checks",
    "watch_items",
}
_RENDERED_SECTION_HEADINGS = {
    "🎯 핵심": "core_thesis",
    "🎯 핵심 판단": "core_judgment",
    "📈 사업·실적": "business_earnings",
    "🚨 오늘 새 경고": "new_warnings",
    "⚠️ 기존 경고": "open_warnings",
    "⚠️ 데이터 주의": "data_cautions",
    "👁 핵심 감시": "persistent_risks",
    "📌 다음 확인": "next_checks",
    "⚠️ 미확인": "unknowns",
    "📐 Valuation": "valuation_analysis",
}
_LEGACY_PLACEHOLDER_PROVENANCE = {
    "saved_thesis",
    "backfilled_saved_thesis",
    "custom_gpt",
}


def _repository_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _canonical_report_path() -> Path:
    return _repository_root() / "docs" / "reports" / CANONICAL_FACTS_REPORT


def _as_date(value: object) -> date | None:
    if value in {None, ""}:
        return None
    try:
        return date.fromisoformat(str(value))
    except ValueError:
        return None


def financial_period_context(
    snapshot: Mapping[str, object],
) -> tuple[date | None, date | None]:
    formal = _as_date(snapshot.get("latest_full_financial_period"))
    preliminary = _as_date(snapshot.get("latest_preliminary_financial_period"))
    quality = snapshot.get("financial_quality")
    if formal is None and isinstance(quality, dict):
        source = quality.get("source_snapshot")
        if isinstance(source, dict) and source.get("source_type") != "preliminary_earnings":
            formal = _as_date(source.get("period"))
    if snapshot.get("earnings_context_is_preliminary") is True:
        preliminary = preliminary or _as_date(snapshot.get("latest_earnings_period"))
    return formal, preliminary


def _sign(value: Decimal) -> ClaimState:
    return ClaimState.POSITIVE if value >= 0 else ClaimState.NEGATIVE


def _scope(text: str, metric: ClaimMetric) -> ClaimScope:
    lowered = text.casefold()
    if "management" in lowered or "회사 정의" in text or "회사 보고" in text:
        return ClaimScope.MANAGEMENT_DEFINED
    if metric == ClaimMetric.FCF and ("ppe" in lowered or "ocf -" in lowered):
        return ClaimScope.BACKEND_PPE_ONLY
    return ClaimScope.UNKNOWN


def _period_type(text: str) -> str:
    lowered = text.casefold()
    if "ttm" in lowered:
        return "TTM"
    if "연간" in text or re.search(r"\bFY\b", text, re.IGNORECASE):
        return "FY"
    if "누계" in text or "ytd" in lowered or "상반기" in text:
        return "YTD"
    if "분기 단독" in text or "qtd" in lowered:
        return "QTD"
    return "unknown"


def _currentness(text: str, section: str, state: ClaimState) -> ClaimCurrentness:
    if section in _FUTURE_SECTIONS:
        return ClaimCurrentness.FUTURE_CONDITION
    if _CURRENT.search(text):
        return ClaimCurrentness.EXPLICIT_CURRENT
    if _HISTORICAL.search(text):
        return ClaimCurrentness.HISTORICAL_QUALIFIED
    if state in {
        ClaimState.POSITIVE,
        ClaimState.NEGATIVE,
        ClaimState.TURN_POSITIVE_REQUIRED,
        ClaimState.UNAVAILABLE,
    }:
        return ClaimCurrentness.IMPLIED_CURRENT
    return ClaimCurrentness.UNKNOWN


def _claim_id(
    ticker: str,
    text_ref: str,
    pattern_type: str,
    span_start: int,
    claim_span: str,
) -> str:
    raw = "|".join((ticker, text_ref, pattern_type, str(span_start), claim_span))
    return f"baseline-cashflow:{hashlib.sha256(raw.encode()).hexdigest()[:24]}"


def _claim_context(text: str, start: int, end: int) -> str:
    left = max(text.rfind(mark, 0, start) for mark in (".", "!", "?", "\n"))
    right_candidates = [
        position
        for mark in (".", "!", "?", "\n")
        if (position := text.find(mark, end)) >= 0
    ]
    right = min(right_candidates) if right_candidates else len(text)
    return text[left + 1 : right]


def rendered_message_cash_flow_sections(
    text: str,
) -> tuple[tuple[str, str, str], ...]:
    sections: list[tuple[str, str, str]] = []
    current_heading: str | None = None
    current_section: str | None = None
    lines: list[str] = []

    def flush() -> None:
        if current_heading and current_section:
            value = "\n".join(lines).strip()
            if value:
                sections.append((current_heading, current_section, value))

    for line in text.splitlines():
        heading = next(
            (
                key
                for key in _RENDERED_SECTION_HEADINGS
                if line.strip() == key
            ),
            None,
        )
        if heading:
            flush()
            current_heading = heading
            current_section = _RENDERED_SECTION_HEADINGS[heading]
            lines = []
        elif current_heading:
            lines.append(line)
    flush()
    if sections:
        return tuple(sections)
    return (("message", "production_delivery", text),)


def extract_baseline_cash_flow_claims(
    ticker: str,
    text: str,
    *,
    text_ref: str,
    section: str,
    origin_type: str,
    origin_version: str | None = None,
    owner: str = "business_earnings",
    provenance_refs: Sequence[str] = (),
    provenance_valid: bool = False,
) -> tuple[BaselineCashFlowClaim, ...]:
    claims: list[BaselineCashFlowClaim] = []
    occupied: list[tuple[int, int]] = []
    for pattern_type, pattern, metric, state in _PATTERNS:
        for match in pattern.finditer(text):
            if any(match.start() < end and match.end() > start for start, end in occupied):
                continue
            occupied.append((match.start(), match.end()))
            span = match.group(0)
            context = _claim_context(text, match.start(), match.end())
            claims.append(
                BaselineCashFlowClaim(
                    claim_id=_claim_id(
                        ticker, text_ref, pattern_type, match.start(), span
                    ),
                    ticker=ticker,
                    text_ref=text_ref,
                    section=section,
                    owner=owner,
                    origin_type=origin_type,
                    origin_version=origin_version,
                    claim_span=span,
                    span_start=match.start(),
                    span_end=match.end(),
                    pattern_type=pattern_type,
                    metric_semantic=metric,
                    state_or_sign=state,
                    period_type=_period_type(context),
                    scope=_scope(context, metric),
                    entity_scope=None,
                    currency=None,
                    claim_currentness=_currentness(context, section, state),
                    provenance_refs=tuple(provenance_refs),
                    provenance_valid=provenance_valid,
                )
            )
    return tuple(sorted(claims, key=lambda item: item.span_start))


@lru_cache(maxsize=4)
def _read_canonical_report(path: str) -> dict[str, object]:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("Canonical cash-flow report must be an object")
    return value


def _metric_evidence(row: Mapping[str, object]) -> CanonicalMetricEvidence:
    value = Decimal(str(row["value"]))
    metric = str(row["metric"])
    return CanonicalMetricEvidence(
        fact_id=str(row["fact_id"]),
        metric=metric,
        value=value,
        sign=_sign(value),
        period_start=date.fromisoformat(str(row["period_start"])),
        period_end=date.fromisoformat(str(row["period_end"])),
        period_type=str(row["period_type"]),
        fiscal_year=int(row["fiscal_year"]),
        fiscal_quarter=(
            int(row["fiscal_quarter"])
            if row.get("fiscal_quarter") is not None
            else None
        ),
        scope=(
            ClaimScope.BACKEND_PPE_ONLY
            if metric == Metric.FCF.value
            else ClaimScope.UNKNOWN
        ),
        entity_scope=str(row.get("entity_scope") or "unknown"),
        currency=str(row.get("currency") or "unknown"),
        unit=str(row.get("unit") or "unknown"),
        filing_date=date.fromisoformat(str(row["filing_date"])),
    )


def load_canonical_cash_flow_evidence(
    ticker: str,
    *,
    cutoff: date | str,
    latest_formal_period: date | None,
    latest_preliminary_period: date | None = None,
    report_path: Path | None = None,
) -> CanonicalCashFlowEvidence:
    cutoff_date = cutoff if isinstance(cutoff, date) else _as_date(cutoff)
    if cutoff_date is None:
        return CanonicalCashFlowEvidence(
            ticker=ticker,
            freshness_state="BLOCKED",
            fcf=None,
            ocf=None,
            denial_reasons=("assessment_cutoff_unavailable",),
        )
    path = report_path or _canonical_report_path()
    if not path.exists():
        return CanonicalCashFlowEvidence(
            ticker=ticker,
            freshness_state="REPORT_UNAVAILABLE",
            fcf=None,
            ocf=None,
            denial_reasons=("canonical_cash_flow_report_unavailable",),
        )
    report = _read_canonical_report(str(path.resolve()))
    records = {
        str(item.get("ticker")): item
        for item in report.get("active_universe") or ()
        if isinstance(item, dict) and item.get("ticker")
    }
    record = records.get(ticker)
    if not isinstance(record, dict):
        return CanonicalCashFlowEvidence(
            ticker=ticker,
            freshness_state="BLOCKED",
            fcf=None,
            ocf=None,
            denial_reasons=("subject_not_in_canonical_cash_flow_universe",),
        )
    if str(record.get("cash_flow_core_status")) == "NOT_APPLICABLE":
        return CanonicalCashFlowEvidence(
            ticker=ticker,
            freshness_state="NOT_APPLICABLE",
            fcf=None,
            ocf=None,
            denial_reasons=tuple(str(item) for item in record.get("denial_reasons") or ()),
        )
    facts = {
        str(item.get("fact_id")): item
        for item in report.get("canonical_facts") or ()
        if isinstance(item, dict)
        and item.get("ticker") == ticker
        and item.get("fact_id")
    }
    metrics = record.get("metrics") if isinstance(record.get("metrics"), dict) else {}

    def selected(metric_name: str) -> CanonicalMetricEvidence | None:
        value = metrics.get(metric_name) if isinstance(metrics, dict) else None
        fact_id = value.get("fact_id") if isinstance(value, dict) else None
        row = facts.get(str(fact_id)) if fact_id else None
        if not isinstance(row, dict) or str(row.get("eligibility")) != "ELIGIBLE":
            return None
        fact = _metric_evidence(row)
        return fact if fact.filing_date <= cutoff_date else None

    fcf = selected("fcf")
    ocf = selected("ocf")
    primary = fcf or ocf
    freshness = "BLOCKED"
    reasons = [str(item) for item in record.get("denial_reasons") or ()]
    if primary is None:
        reasons.append("point_in_time_primary_cash_flow_fact_unavailable")
    elif latest_formal_period is None:
        freshness = "FORMAL_ALIGNMENT_UNAVAILABLE"
    elif primary.period_end < latest_formal_period:
        freshness = "STALE_FORMAL"
    elif primary.period_end > latest_formal_period:
        freshness = "FORMAL_ALIGNMENT_UNAVAILABLE"
    elif latest_preliminary_period and latest_preliminary_period > latest_formal_period:
        freshness = "FORMAL_LAGGING_PROVISIONAL"
    else:
        freshness = "CURRENT_FORMAL"
    return CanonicalCashFlowEvidence(
        ticker=ticker,
        freshness_state=freshness,
        fcf=fcf,
        ocf=ocf,
        denial_reasons=tuple(dict.fromkeys(reasons)),
    )


def evidence_from_shadow_context(
    context: CashFlowReasoningContext,
    facts: Mapping[str, FinancialFact],
) -> CanonicalCashFlowEvidence:
    def convert(fact_id: str | None) -> CanonicalMetricEvidence | None:
        fact = facts.get(fact_id or "")
        if fact is None:
            return None
        return CanonicalMetricEvidence(
            fact_id=fact.fact_id,
            metric=fact.metric.value,
            value=fact.value,
            sign=_sign(fact.value),
            period_start=fact.period.start,
            period_end=fact.period.end,
            period_type=fact.period.period_type.value,
            fiscal_year=fact.period.fiscal_year,
            fiscal_quarter=fact.period.fiscal_quarter,
            scope=(
                ClaimScope.BACKEND_PPE_ONLY
                if fact.metric == Metric.FCF
                else ClaimScope.UNKNOWN
            ),
            entity_scope=fact.entity_scope,
            currency=fact.currency,
            unit=fact.unit,
            filing_date=fact.filing_date,
        )

    return CanonicalCashFlowEvidence(
        ticker=context.ticker,
        freshness_state=context.freshness_state.value,
        fcf=convert(context.fcf_fact_id),
        ocf=convert(context.ocf_fact_id),
        denial_reasons=context.suppression_reasons,
    )


def _period_qualifier(fact: CanonicalMetricEvidence) -> str:
    if fact.period_type == "FY":
        period = f"{fact.fiscal_year} 회계연도 연간"
    elif fact.period_type == "YTD" and fact.fiscal_quarter == 2:
        period = f"{fact.fiscal_year} 회계연도 상반기 누계"
    elif fact.period_type == "YTD" and fact.fiscal_quarter:
        period = f"{fact.fiscal_year} 회계연도 {fact.fiscal_quarter}분기 누계"
    elif fact.period_type == "QTD" and fact.fiscal_quarter:
        period = f"{fact.fiscal_year} 회계연도 {fact.fiscal_quarter}분기 단독"
    else:
        period = f"{fact.period_end.isoformat()} 종료 {fact.period_type}"
    if fact.metric == Metric.FCF.value:
        return f"{period} PPE 기준"
    return period


def evaluate_baseline_cash_flow_claim(
    claim: BaselineCashFlowClaim,
    evidence: CanonicalCashFlowEvidence,
) -> CashFlowClaimDecision:
    if claim.claim_currentness == ClaimCurrentness.FUTURE_CONDITION:
        return CashFlowClaimDecision(
            claim=claim,
            canonical_comparison_fact_id=None,
            comparability="conditional_not_current_state",
            consistency_result=ConsistencyResult.CONSISTENT,
            render_action=RenderAction.KEEP,
        )
    if claim.claim_currentness == ClaimCurrentness.HISTORICAL_QUALIFIED:
        action = RenderAction.KEEP if claim.provenance_valid else RenderAction.SUPPRESS
        result = (
            ConsistencyResult.NO_CANONICAL_CHECK_AVAILABLE
            if claim.provenance_valid
            else ConsistencyResult.UNSUPPORTED_CLAIM
        )
        return CashFlowClaimDecision(
            claim=claim,
            canonical_comparison_fact_id=None,
            comparability="historical_claim_requires_own_provenance",
            consistency_result=result,
            render_action=action,
            suppression_reason=(None if claim.provenance_valid else "historical_claim_provenance_missing"),
        )
    if evidence.freshness_state == "NOT_APPLICABLE":
        return CashFlowClaimDecision(
            claim=claim,
            canonical_comparison_fact_id=None,
            comparability="industry_not_applicable",
            consistency_result=ConsistencyResult.UNSUPPORTED_CLAIM,
            render_action=RenderAction.SUPPRESS,
            suppression_reason="generic_enterprise_cash_flow_not_applicable",
        )
    fact = evidence.fcf
    if claim.metric_semantic in {ClaimMetric.OCF, ClaimMetric.CASH_BURN}:
        fact = evidence.ocf or evidence.fcf
    if evidence.freshness_state != FreshnessState.CURRENT_FORMAL.value or fact is None:
        if claim.provenance_valid:
            return CashFlowClaimDecision(
                claim=claim,
                canonical_comparison_fact_id=None,
                comparability="current_canonical_check_unavailable",
                consistency_result=ConsistencyResult.NO_CANONICAL_CHECK_AVAILABLE,
                render_action=RenderAction.KEEP,
            )
        return CashFlowClaimDecision(
            claim=claim,
            canonical_comparison_fact_id=None,
            comparability="current_canonical_check_unavailable",
            consistency_result=ConsistencyResult.UNSUPPORTED_CLAIM,
            render_action=RenderAction.SUPPRESS,
            suppression_reason="current_claim_provenance_missing",
        )
    if claim.state_or_sign == ClaimState.UNAVAILABLE:
        return CashFlowClaimDecision(
            claim=claim,
            canonical_comparison_fact_id=fact.fact_id,
            comparability="current_formal_fact_available",
            consistency_result=ConsistencyResult.STALE_CONFLICT,
            render_action=RenderAction.SUPPRESS,
            suppression_reason="canonical_fact_resolves_unavailable_claim",
        )
    implied_sign = (
        ClaimState.NEGATIVE
        if claim.state_or_sign == ClaimState.TURN_POSITIVE_REQUIRED
        else claim.state_or_sign
    )
    if claim.scope == ClaimScope.MANAGEMENT_DEFINED:
        return CashFlowClaimDecision(
            claim=claim,
            canonical_comparison_fact_id=fact.fact_id,
            comparability="management_fcf_vs_backend_ppe_fcf",
            consistency_result=ConsistencyResult.NOT_COMPARABLE,
            render_action=(RenderAction.KEEP if claim.provenance_valid else RenderAction.SUPPRESS),
            suppression_reason=(None if claim.provenance_valid else "management_fcf_provenance_missing"),
        )
    if claim.period_type != "unknown" and claim.period_type != fact.period_type:
        return CashFlowClaimDecision(
            claim=claim,
            canonical_comparison_fact_id=fact.fact_id,
            comparability="period_type_mismatch",
            consistency_result=ConsistencyResult.NOT_COMPARABLE,
            render_action=(RenderAction.KEEP if claim.provenance_valid else RenderAction.SUPPRESS),
            suppression_reason=(None if claim.provenance_valid else "period_specific_claim_provenance_missing"),
        )
    if implied_sign != fact.sign:
        return CashFlowClaimDecision(
            claim=claim,
            canonical_comparison_fact_id=fact.fact_id,
            comparability="current_formal_primary_sign",
            consistency_result=(
                ConsistencyResult.STALE_CONFLICT
                if claim.provenance_valid
                else ConsistencyResult.UNSUPPORTED_CLAIM
            ),
            render_action=RenderAction.SUPPRESS,
            suppression_reason="current_primary_cash_flow_sign_disagrees",
        )
    if claim.metric_semantic == ClaimMetric.FCF and claim.scope == ClaimScope.UNKNOWN:
        return CashFlowClaimDecision(
            claim=claim,
            canonical_comparison_fact_id=fact.fact_id,
            comparability="sign_consistent_scope_unspecified",
            consistency_result=ConsistencyResult.QUALIFIER_REQUIRED,
            render_action=RenderAction.QUALIFY,
            required_qualifier=_period_qualifier(fact),
        )
    return CashFlowClaimDecision(
        claim=claim,
        canonical_comparison_fact_id=fact.fact_id,
        comparability="current_formal_primary_compatible",
        consistency_result=ConsistencyResult.CONSISTENT,
        render_action=RenderAction.KEEP,
    )


def _suppress_span(text: str, claim: BaselineCashFlowClaim) -> str:
    prefix = text[: claim.span_start]
    suffix = text[claim.span_end :]
    matched = text[claim.span_start : claim.span_end]
    if re.fullmatch(
        rf"\s*{re.escape(matched)}\s*(?:확인|미확인)?\s*[.!?]?\s*",
        text,
        flags=re.IGNORECASE,
    ):
        return ""
    conjunction = re.search(r"(?:,\s*|(?:와|과|및)\s*|·\s*)$", prefix)
    if conjunction:
        prefix = prefix[: conjunction.start()]
    replacement = ""
    if matched.endswith("로"):
        replacement = "로"
    elif matched.endswith(("이", "가")) and conjunction:
        replacement = "이"
    value = prefix + replacement + suffix
    return value.strip()


def _qualify_span(
    text: str,
    claim: BaselineCashFlowClaim,
    qualifier: str,
) -> str:
    span = text[claim.span_start : claim.span_end]
    if re.search(r"\bFCF\b", span, re.IGNORECASE):
        qualified = re.sub(
            r"\bFCF\b",
            f"{qualifier} FCF",
            span,
            count=1,
            flags=re.IGNORECASE,
        )
    else:
        qualified = f"{qualifier} {span}"
    return text[: claim.span_start] + qualified + text[claim.span_end :]


def repair_baseline_cash_flow_text(
    ticker: str,
    text: str,
    evidence: CanonicalCashFlowEvidence,
    *,
    text_ref: str,
    section: str,
    origin_type: str,
    origin_version: str | None = None,
    owner: str = "business_earnings",
    provenance_refs: Sequence[str] = (),
    provenance_valid: bool = False,
) -> BaselineTextRepair:
    claims = extract_baseline_cash_flow_claims(
        ticker,
        text,
        text_ref=text_ref,
        section=section,
        origin_type=origin_type,
        origin_version=origin_version,
        owner=owner,
        provenance_refs=provenance_refs,
        provenance_valid=provenance_valid,
    )
    decisions = tuple(evaluate_baseline_cash_flow_claim(item, evidence) for item in claims)
    repaired = text
    for decision in sorted(
        decisions,
        key=lambda item: item.claim.span_start,
        reverse=True,
    ):
        if decision.render_action == RenderAction.SUPPRESS:
            repaired = _suppress_span(repaired, decision.claim)
        elif decision.render_action == RenderAction.QUALIFY and decision.required_qualifier:
            repaired = _qualify_span(
                repaired,
                decision.claim,
                decision.required_qualifier,
            )
    return BaselineTextRepair(text=repaired, decisions=decisions)


def provenance_from_warning_state(
    state: Mapping[str, object] | None,
) -> tuple[tuple[str, ...], bool]:
    if not state:
        return (), False
    refs = tuple(str(item) for item in state.get("source_event_ids") or () if item)
    provider = str(state.get("source_provider") or state.get("source") or "")
    provenance_status = str(state.get("provenance_status") or "")
    valid = bool(refs) and provider not in _LEGACY_PLACEHOLDER_PROVENANCE
    valid = valid and provenance_status not in _LEGACY_PLACEHOLDER_PROVENANCE
    return refs, valid


def repair_baseline_cash_flow_items(
    ticker: str,
    items: Sequence[str],
    evidence: CanonicalCashFlowEvidence,
    *,
    section: str,
    origin_type: str,
    origin_version: str | None = None,
    provenance_by_text: Mapping[str, Mapping[str, object]] | None = None,
) -> tuple[list[str], tuple[CashFlowClaimDecision, ...]]:
    output: list[str] = []
    decisions: list[CashFlowClaimDecision] = []
    for index, item in enumerate(items):
        state = (provenance_by_text or {}).get(item)
        refs, valid = provenance_from_warning_state(state)
        repair = repair_baseline_cash_flow_text(
            ticker,
            item,
            evidence,
            text_ref=f"{section}[{index}]",
            section=section,
            origin_type=origin_type,
            origin_version=origin_version,
            provenance_refs=refs,
            provenance_valid=valid,
        )
        decisions.extend(repair.decisions)
        if repair.text:
            output.append(repair.text)
    return list(dict.fromkeys(output)), tuple(decisions)


def audit_shared_baseline_cash_flow_inputs(
    ticker: str,
    evidence: CanonicalCashFlowEvidence,
    *,
    core_thesis: str,
    assessment_summary: str,
    warning_groups: Mapping[str, Sequence[str]],
    origin_version: str,
    provenance_by_text: Mapping[str, Mapping[str, object]] | None = None,
) -> tuple[CashFlowClaimDecision, ...]:
    """Audit the same source fields for AI and fallback context identity."""
    decisions: list[CashFlowClaimDecision] = []
    for text_ref, section, value, origin_type in (
        ("shared.core_thesis", "core_thesis", core_thesis, "saved_thesis"),
        (
            "shared.assessment_summary",
            "assessment_summary",
            assessment_summary,
            "assessment",
        ),
    ):
        decisions.extend(
            repair_baseline_cash_flow_text(
                ticker,
                value,
                evidence,
                text_ref=text_ref,
                section=section,
                origin_type=origin_type,
                origin_version=origin_version,
            ).decisions
        )
    for section in sorted(warning_groups):
        _items, item_decisions = repair_baseline_cash_flow_items(
            ticker,
            warning_groups[section],
            evidence,
            section=f"shared.{section}",
            origin_type="assessment_warning",
            origin_version=origin_version,
            provenance_by_text=provenance_by_text,
        )
        decisions.extend(item_decisions)
    return tuple(decisions)


def baseline_suppressed_claim_ids(
    decisions: Sequence[CashFlowClaimDecision],
) -> tuple[str, ...]:
    return tuple(
        sorted(
            {
                item.claim.claim_id
                for item in decisions
                if item.render_action != RenderAction.KEEP
            }
        )
    )


def decision_to_dict(decision: CashFlowClaimDecision) -> dict[str, object]:
    value = asdict(decision)
    value["claim"]["metric_semantic"] = decision.claim.metric_semantic.value
    value["claim"]["state_or_sign"] = decision.claim.state_or_sign.value
    value["claim"]["scope"] = decision.claim.scope.value
    value["claim"]["claim_currentness"] = decision.claim.claim_currentness.value
    value["consistency_result"] = decision.consistency_result.value
    value["render_action"] = decision.render_action.value
    return value


def consistency_error(decision: CashFlowClaimDecision) -> str | None:
    if decision.render_action == RenderAction.KEEP:
        return None
    return {
        ConsistencyResult.QUALIFIER_REQUIRED: "baseline_cash_flow_qualifier_required",
        ConsistencyResult.STALE_CONFLICT: "baseline_cash_flow_stale_conflict",
        ConsistencyResult.UNSUPPORTED_CLAIM: "baseline_cash_flow_unsupported_claim",
        ConsistencyResult.NOT_COMPARABLE: "baseline_cash_flow_not_comparable",
        ConsistencyResult.NO_CANONICAL_CHECK_AVAILABLE: "baseline_cash_flow_unchecked_claim",
    }.get(decision.consistency_result, "baseline_cash_flow_consistency_error")
