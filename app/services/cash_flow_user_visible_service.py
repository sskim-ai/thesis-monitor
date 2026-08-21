from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from enum import StrEnum
from functools import lru_cache
from pathlib import Path
from typing import Iterable, Mapping, Sequence

from app.config import get_settings
from app.services.cash_flow_capital_efficiency_service import (
    CapexScope,
    EligibilityStatus,
    FinancialFact,
    Metric,
    financial_fact_from_mapping,
)
from app.services.cash_flow_shadow_consumption_service import (
    CashFlowReasoningContext,
    FreshnessState,
    RelationType,
    UsageMode,
    build_cash_flow_reasoning_context,
    period_label,
    resolve_cash_flow_unknowns,
)
from app.services.numeric_semantic_registry import (
    NUMERIC_SEMANTICS,
    canonical_display_value,
)


CONTRACT_VERSION = "cash-flow-user-visible-v1"
CANONICAL_FACTS_REPORT = "20260820-phase9-0b-canonical-facts.json"
FORMAL_PERIOD_REPORT = "20260820-phase9-0a-coverage.json"


class CashFlowRolloutMode(StrEnum):
    OFF = "OFF"
    SELECTIVE_CURRENT_FORMAL_FULL_FCF = "SELECTIVE_CURRENT_FORMAL_FULL_FCF"


class SelectionState(StrEnum):
    OFF = "OFF"
    SELECTED = "SELECTED"
    SUPPRESSED = "SUPPRESSED"
    NOT_APPLICABLE = "NOT_APPLICABLE"


@dataclass(frozen=True)
class UserVisibleCashFlowSelection:
    ticker: str
    market: str
    industry: str
    rollout_mode: CashFlowRolloutMode
    selection_state: SelectionState
    selection_reason: str
    assessment_date: date
    context_id: str | None
    reasoning_context: CashFlowReasoningContext | None
    facts: tuple[FinancialFact, ...]
    primary_fact_id: str | None
    baseline_consistency_state: str
    suppressed_baseline_claim_ids: tuple[str, ...]
    resolved_unknown_ids: tuple[str, ...]
    rendered_text: str | None
    evidence_signature: str | None
    display_reason: str | None

    @property
    def user_visible_enabled(self) -> bool:
        return self.selection_state == SelectionState.SELECTED


_CASH_FLOW_UNKNOWN = re.compile(
    r"(?:OCF|FCF|CAPEX)|영업현금흐름|잉여현금흐름|현금흐름|현금전환|"
    r"PPE\s*(?:CAPEX|취득)",
    re.IGNORECASE,
)
_ALLOWED_SOURCE_CAUTION = {"sec_companyfacts_issuer_level_context"}


def resolve_rollout_mode(value: object | None = None) -> CashFlowRolloutMode:
    candidate = (
        value
        if value is not None
        else get_settings().cash_flow_user_visible_mode
    )
    try:
        return CashFlowRolloutMode(str(candidate).strip().upper())
    except ValueError:
        return CashFlowRolloutMode.OFF


def context_from_notification_payload(payload: object) -> dict[str, object]:
    value = payload
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError:
            return {}
    if not isinstance(value, dict):
        return {}
    candidates: list[object] = [value]
    deterministic = value.get("deterministic_payload")
    if isinstance(deterministic, dict):
        candidates.append(deterministic)
    for candidate in candidates:
        if not isinstance(candidate, dict):
            continue
        analysis = candidate.get("analysis_context")
        if not isinstance(analysis, dict):
            continue
        context = analysis.get("cash_flow_user_visible")
        if isinstance(context, dict):
            return dict(context)
    return {}


def _repository_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _report_path() -> Path:
    return _repository_root() / "docs" / "reports" / CANONICAL_FACTS_REPORT


def _formal_period_report_path() -> Path:
    return _repository_root() / "docs" / "reports" / FORMAL_PERIOD_REPORT


@lru_cache(maxsize=4)
def _read_report(path: str) -> dict[str, object]:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("Canonical cash-flow report must be an object")
    return value


def _validated_formal_period(
    ticker: str,
    *,
    report_path: Path | None = None,
) -> date | None:
    path = report_path or _formal_period_report_path()
    if not path.exists():
        return None
    report = _read_report(str(path.resolve()))
    row = next(
        (
            item
            for item in report.get("active_universe") or ()
            if isinstance(item, dict) and str(item.get("ticker")) == ticker
        ),
        None,
    )
    if not isinstance(row, dict) or not row.get("latest_formal_period"):
        return None
    try:
        return date.fromisoformat(str(row["latest_formal_period"]))
    except ValueError:
        return None


def _canonical_json(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")


def _selection(
    *,
    ticker: str,
    market: str,
    industry: str,
    mode: CashFlowRolloutMode,
    state: SelectionState,
    reason: str,
    assessment_date: date,
    context: CashFlowReasoningContext | None = None,
    facts: Iterable[FinancialFact] = (),
    primary_fact_id: str | None = None,
    baseline_state: str = "PASS",
    suppressed_claim_ids: Sequence[str] = (),
    resolved_unknown_ids: Sequence[str] = (),
    rendered_text: str | None = None,
    evidence_signature: str | None = None,
    display_reason: str | None = None,
) -> UserVisibleCashFlowSelection:
    normalized_suppressions = tuple(sorted(set(suppressed_claim_ids)))
    context_id = None
    if state == SelectionState.SELECTED and context is not None:
        identity = {
            "contract": CONTRACT_VERSION,
            "ticker": ticker,
            "market": market,
            "rollout_mode": mode.value,
            "assessment_date": assessment_date.isoformat(),
            "primary_period": (
                context.primary_period.end.isoformat()
                if context.primary_period is not None
                else None
            ),
            "ocf_fact_id": context.ocf_fact_id,
            "capex_fact_id": context.capex_fact_id,
            "fcf_fact_id": context.fcf_fact_id,
            "baseline_suppressions": normalized_suppressions,
        }
        context_id = f"cf-visible-{hashlib.sha256(_canonical_json(identity)).hexdigest()[:24]}"
    return UserVisibleCashFlowSelection(
        ticker=ticker,
        market=market,
        industry=industry,
        rollout_mode=mode,
        selection_state=state,
        selection_reason=reason,
        assessment_date=assessment_date,
        context_id=context_id,
        reasoning_context=context,
        facts=tuple(facts) if state == SelectionState.SELECTED else (),
        primary_fact_id=primary_fact_id if state == SelectionState.SELECTED else None,
        baseline_consistency_state=baseline_state,
        suppressed_baseline_claim_ids=normalized_suppressions,
        resolved_unknown_ids=tuple(sorted(set(resolved_unknown_ids))),
        rendered_text=rendered_text if state == SelectionState.SELECTED else None,
        evidence_signature=evidence_signature,
        display_reason=display_reason,
    )


def _lineage_error(
    context: CashFlowReasoningContext,
    facts: Mapping[str, FinancialFact],
) -> str | None:
    fcf = facts.get(context.fcf_fact_id or "")
    ocf = facts.get(context.ocf_fact_id or "")
    capex = facts.get(context.capex_fact_id or "")
    if fcf is None or ocf is None or capex is None:
        return "full_fcf_input_fact_missing"
    if fcf.metric != Metric.FCF or ocf.metric != Metric.OCF or capex.metric != Metric.CAPEX:
        return "cash_flow_metric_identity_mismatch"
    if tuple(fcf.input_fact_ids) != (ocf.fact_id, capex.fact_id):
        if set(fcf.input_fact_ids) != {ocf.fact_id, capex.fact_id}:
            return "fcf_input_lineage_incomplete"
    if capex.capex_scope != CapexScope.PPE_ONLY:
        return "capex_scope_not_ppe_only"
    if any(item.eligibility != EligibilityStatus.ELIGIBLE for item in (ocf, capex, fcf)):
        return "cash_flow_input_not_eligible"
    if any(item.quality not in {"REPORTED_VERIFIED", "DERIVED_SAFE"} for item in (ocf, capex, fcf)):
        return "cash_flow_input_quality_tainted"
    if any(set(item.cautions) - _ALLOWED_SOURCE_CAUTION for item in (ocf, capex, fcf)):
        return "cash_flow_input_has_material_caution"
    if len({item.period for item in (ocf, capex, fcf)}) != 1:
        return "cash_flow_period_mismatch"
    for field_name in ("issuer_id", "currency", "unit", "entity_scope", "statement_basis"):
        if len({getattr(item, field_name) for item in (ocf, capex, fcf)}) != 1:
            return f"cash_flow_{field_name}_mismatch"
    if fcf.value != ocf.value - capex.value:
        return "fcf_arithmetic_mismatch"
    return None


def _relation_note(context: CashFlowReasoningContext) -> str:
    relation = next(
        (
            item.relation
            for item in context.deterministic_relations
            if item.metric == Metric.FCF
        ),
        None,
    )
    return {
        RelationType.NEGATIVE_TO_POSITIVE: "전년 비교기간의 음수에서 양수로 전환됐고",
        RelationType.POSITIVE_TO_NEGATIVE: "전년 비교기간의 양수에서 음수로 전환됐고",
        RelationType.POSITIVE_HIGHER: "전년 비교기간보다 늘었고",
        RelationType.POSITIVE_LOWER: "전년 비교기간보다 줄었고",
        RelationType.NEGATIVE_LESS_NEGATIVE: "전년 비교기간보다 음수 폭이 줄었고",
        RelationType.NEGATIVE_MORE_NEGATIVE: "전년 비교기간보다 음수 폭이 커졌고",
    }.get(relation, "")


def _evidence_signature(context: CashFlowReasoningContext) -> str:
    identity = {
        "ticker": context.ticker,
        "ocf_fact_id": context.ocf_fact_id,
        "capex_fact_id": context.capex_fact_id,
        "fcf_fact_id": context.fcf_fact_id,
        "relations": [
            {
                "metric": item.metric.value,
                "current_fact_id": item.current_fact_id,
                "prior_fact_id": item.prior_fact_id,
                "relation": item.relation.value,
            }
            for item in context.deterministic_relations
        ],
    }
    return f"cf-evidence-{hashlib.sha256(_canonical_json(identity)).hexdigest()[:24]}"


def _same_visible_evidence(
    previous: Mapping[str, object] | None,
    *,
    signature: str,
    context: CashFlowReasoningContext,
) -> bool:
    if not previous or previous.get("user_visible_enabled") is not True:
        return False
    previous_signature = str(previous.get("evidence_signature") or "")
    if previous_signature:
        return previous_signature == signature
    return (
        previous.get("primary_fact_ref") == context.fcf_fact_id
        and previous.get("deterministic_relations")
        == [
            {
                "metric": item.metric.value,
                "current_fact_id": item.current_fact_id,
                "prior_fact_id": item.prior_fact_id,
                "relation": item.relation.value,
            }
            for item in context.deterministic_relations
        ]
    )


def _render(
    context: CashFlowReasoningContext,
    facts: Mapping[str, FinancialFact],
    *,
    industry: str,
    source_text: str,
) -> str | None:
    fcf = facts.get(context.fcf_fact_id or "")
    if fcf is None or context.primary_period is None:
        return None
    label = period_label(context.primary_period)
    amount = canonical_display_value(
        NUMERIC_SEMANTICS["free_cash_flow_ppe"],
        float(fcf.value),
        fcf.currency,
    )
    if amount is None:
        return None
    relation = _relation_note(context)
    lowered = source_text.casefold()
    if industry == "cloud_platform_software" and any(
        marker in lowered for marker in ("software", "consulting", "red hat")
    ):
        reinvestment_subject = "Software·Consulting 사업의 PPE 투자"
        consequence = "Software·Consulting 전환과 인수자금 부담을 함께 봅니다."
    elif industry == "cloud_platform_software":
        reinvestment_subject = "AI·Cloud 확장의 PPE 투자"
        consequence = "AI·Cloud 투자 회수는 Cloud 성장·마진과 함께 봅니다."
    elif industry == "memory_semiconductor":
        reinvestment_subject = "메모리 증설의 PPE 투자"
        consequence = "ASP·제품 믹스·재고 사이클과 설비투자 시점을 함께 봅니다."
    elif industry == "hpc_data_center":
        reinvestment_subject = "build-out 단계의 PPE 투자"
        consequence = "build-out 재투자는 가동·청구 전환과 자금조달을 함께 봅니다."
    elif industry == "biotech":
        reinvestment_subject = "연구개발 단계의 PPE 투자"
        consequence = "현금소진 근거로만 쓰며 보유현금 근거 없이 runway를 계산하지 않습니다."
    elif industry == "automotive":
        reinvestment_subject = "자동차 성장투자의 PPE 투자"
        consequence = "자동차 마진과 성장투자 회수를 함께 봅니다."
    elif "usdc" in lowered:
        reinvestment_subject = "준비금·플랫폼 사업의 PPE 투자"
        consequence = "준비금 수익과 비이자 플랫폼 수익의 현금전환을 함께 봅니다."
    else:
        reinvestment_subject = "사업 운영의 PPE 투자"
        consequence = "사업 성과와 PPE 재투자 부담을 나눠 봅니다."
    sentence = f"{label} {reinvestment_subject} 후 잉여현금흐름은 {amount}입니다."
    interpretation = f"{relation} {consequence}" if relation else consequence
    return f"{sentence} {interpretation}"


def select_user_visible_cash_flow(
    *,
    ticker: str,
    cutoff: date | str,
    latest_formal_period: date | None,
    latest_preliminary_period: date | None = None,
    existing_unknowns: Sequence[str] = (),
    materiality_signals: Sequence[str] = (),
    source_text: str = "",
    suppressed_baseline_claim_ids: Sequence[str] = (),
    baseline_unresolved_conflicts: Sequence[str] = (),
    rollout_mode: object | None = None,
    report_path: Path | None = None,
    formal_period_report_path: Path | None = None,
    previous_user_visible_context: Mapping[str, object] | None = None,
) -> UserVisibleCashFlowSelection:
    cutoff_date = cutoff if isinstance(cutoff, date) else date.fromisoformat(cutoff)
    validated_formal_period = _validated_formal_period(
        ticker,
        report_path=formal_period_report_path,
    )
    latest_formal_period = max(
        (
            item
            for item in (latest_formal_period, validated_formal_period)
            if item is not None
        ),
        default=None,
    )
    mode = resolve_rollout_mode(rollout_mode)
    if mode == CashFlowRolloutMode.OFF:
        return _selection(
            ticker=ticker,
            market="unknown",
            industry="",
            mode=mode,
            state=SelectionState.OFF,
            reason="rollout_mode_off",
            assessment_date=cutoff_date,
            suppressed_claim_ids=suppressed_baseline_claim_ids,
        )
    path = (report_path or _report_path()).resolve()
    if not path.exists():
        return _selection(
            ticker=ticker,
            market="unknown",
            industry="",
            mode=mode,
            state=SelectionState.SUPPRESSED,
            reason="canonical_cash_flow_report_unavailable",
            assessment_date=cutoff_date,
            suppressed_claim_ids=suppressed_baseline_claim_ids,
        )
    report = _read_report(str(path))
    record = next(
        (
            item
            for item in report.get("active_universe") or ()
            if isinstance(item, dict) and str(item.get("ticker")) == ticker
        ),
        None,
    )
    if not isinstance(record, dict):
        return _selection(
            ticker=ticker,
            market="unknown",
            industry="",
            mode=mode,
            state=SelectionState.SUPPRESSED,
            reason="subject_not_in_canonical_cash_flow_universe",
            assessment_date=cutoff_date,
            suppressed_claim_ids=suppressed_baseline_claim_ids,
        )
    market = str(record.get("market") or "unknown").upper()
    industry = str(record.get("industry") or "")
    if str(record.get("cash_flow_core_status")) == "NOT_APPLICABLE":
        return _selection(
            ticker=ticker,
            market=market,
            industry=industry,
            mode=mode,
            state=SelectionState.NOT_APPLICABLE,
            reason="financial_industry_not_applicable",
            assessment_date=cutoff_date,
            suppressed_claim_ids=suppressed_baseline_claim_ids,
        )
    if market not in {"US", "US_FOREIGN"} or not str(
        record.get("source") or ""
    ).startswith("SEC"):
        return _selection(
            ticker=ticker,
            market=market,
            industry=industry,
            mode=mode,
            state=SelectionState.SUPPRESSED,
            reason="initial_market_or_source_scope_excluded",
            assessment_date=cutoff_date,
            suppressed_claim_ids=suppressed_baseline_claim_ids,
        )
    facts = tuple(
        financial_fact_from_mapping(item)
        for item in report.get("canonical_facts") or ()
        if isinstance(item, dict) and str(item.get("ticker")) == ticker
    )
    facts_by_id = {item.fact_id: item for item in facts}
    metrics = record.get("metrics") if isinstance(record.get("metrics"), dict) else {}
    fcf_metric = metrics.get("fcf") if isinstance(metrics, dict) else None
    preferred_fcf = (
        str(fcf_metric.get("fact_id"))
        if isinstance(fcf_metric, dict) and fcf_metric.get("fact_id")
        else None
    )
    context = build_cash_flow_reasoning_context(
        ticker=ticker,
        industry=str(record.get("industry") or ""),
        financial_type=str(record.get("financial_type") or "non_financial"),
        core_status=str(record.get("cash_flow_core_status") or "BLOCKED"),
        facts=facts,
        cutoff=cutoff_date,
        latest_formal_period=latest_formal_period,
        latest_provisional_period=latest_preliminary_period,
        latest_operating_earnings_period=(
            latest_preliminary_period or latest_formal_period
        ),
        preferred_fcf_fact_id=preferred_fcf,
        existing_unknowns=existing_unknowns,
        materiality_signals=materiality_signals,
    )
    state = (
        SelectionState.NOT_APPLICABLE
        if context.freshness_state == FreshnessState.NOT_APPLICABLE
        else SelectionState.SUPPRESSED
    )
    base_required = (
        context.usage_mode == UsageMode.FULL_FCF_CONTEXT,
        context.freshness_state == FreshnessState.CURRENT_FORMAL,
        context.consumption_eligible,
        not baseline_unresolved_conflicts,
    )
    if not all(base_required):
        reason = (
            "baseline_consistency_unresolved"
            if baseline_unresolved_conflicts
            else "ocf_only_user_visible_excluded"
            if context.usage_mode == UsageMode.OCF_ONLY_CONTEXT
            else "capex_only_user_visible_excluded"
            if context.usage_mode == UsageMode.CAPEX_CONTEXT_ONLY
            else context.suppression_reasons[0]
            if context.suppression_reasons
            else "full_fcf_current_formal_materiality_gate_failed"
        )
        return _selection(
            ticker=ticker,
            market=market,
            industry=industry,
            mode=mode,
            state=state,
            reason=reason,
            assessment_date=cutoff_date,
            context=context,
            baseline_state=("FAIL" if baseline_unresolved_conflicts else "PASS"),
            suppressed_claim_ids=suppressed_baseline_claim_ids,
        )
    if lineage_error := _lineage_error(context, facts_by_id):
        return _selection(
            ticker=ticker,
            market=market,
            industry=industry,
            mode=mode,
            state=SelectionState.SUPPRESSED,
            reason=lineage_error,
            assessment_date=cutoff_date,
            context=context,
            suppressed_claim_ids=suppressed_baseline_claim_ids,
        )
    resolved_unknown_ids = tuple(
        f"cash-flow-unknown:{hashlib.sha256(f'{ticker}|{index}|{value}'.encode()).hexdigest()[:20]}"
        for index, value in enumerate(existing_unknowns)
        if _CASH_FLOW_UNKNOWN.search(value)
    )
    signature = _evidence_signature(context)
    if not context.shadow_used:
        return _selection(
            ticker=ticker,
            market=market,
            industry=industry,
            mode=mode,
            state=SelectionState.SUPPRESSED,
            reason=(
                context.suppression_reasons[0]
                if context.suppression_reasons
                else "cash_flow_not_material"
            ),
            assessment_date=cutoff_date,
            context=context,
            baseline_state=("REPAIRED" if suppressed_baseline_claim_ids else "PASS"),
            suppressed_claim_ids=suppressed_baseline_claim_ids,
            resolved_unknown_ids=resolved_unknown_ids,
            evidence_signature=signature,
            display_reason="SUPPRESSED_NOT_MATERIAL",
        )
    if _same_visible_evidence(
        previous_user_visible_context,
        signature=signature,
        context=context,
    ):
        return _selection(
            ticker=ticker,
            market=market,
            industry=industry,
            mode=mode,
            state=SelectionState.SUPPRESSED,
            reason="unchanged_visible_cash_flow_context",
            assessment_date=cutoff_date,
            context=context,
            baseline_state=("REPAIRED" if suppressed_baseline_claim_ids else "PASS"),
            suppressed_claim_ids=suppressed_baseline_claim_ids,
            resolved_unknown_ids=resolved_unknown_ids,
            evidence_signature=signature,
            display_reason="SUPPRESSED_NO_DELTA",
        )
    rendered = _render(
        context,
        facts_by_id,
        industry=str(record.get("industry") or ""),
        source_text=source_text,
    )
    if not rendered:
        return _selection(
            ticker=ticker,
            market=market,
            industry=industry,
            mode=mode,
            state=SelectionState.SUPPRESSED,
            reason="cash_flow_optional_renderer_failed",
            assessment_date=cutoff_date,
            context=context,
            suppressed_claim_ids=suppressed_baseline_claim_ids,
            resolved_unknown_ids=resolved_unknown_ids,
            evidence_signature=signature,
            display_reason="SUPPRESSED_RENDERER_FAILURE",
        )
    previous_visible = bool(
        previous_user_visible_context
        and previous_user_visible_context.get("user_visible_enabled") is True
    )
    display_reason = (
        "MATERIAL_NEW_FORMAL_PERIOD"
        if previous_visible
        else "RESOLVED_PRIOR_UNKNOWN"
        if resolved_unknown_ids
        else "FIRST_SAFE_EXPOSURE"
    )
    selected_facts = tuple(
        facts_by_id[fact_id]
        for fact_id in (context.ocf_fact_id, context.capex_fact_id, context.fcf_fact_id)
        if fact_id and fact_id in facts_by_id
    )
    return _selection(
        ticker=ticker,
        market=market,
        industry=industry,
        mode=mode,
        state=SelectionState.SELECTED,
        reason=context.materiality_reason or "material_current_formal_full_fcf",
        assessment_date=cutoff_date,
        context=context,
        facts=selected_facts,
        primary_fact_id=context.fcf_fact_id,
        baseline_state=("REPAIRED" if suppressed_baseline_claim_ids else "PASS"),
        suppressed_claim_ids=suppressed_baseline_claim_ids,
        resolved_unknown_ids=resolved_unknown_ids,
        rendered_text=rendered,
        evidence_signature=signature,
        display_reason=display_reason,
    )


def safe_select_user_visible_cash_flow(
    **kwargs: object,
) -> UserVisibleCashFlowSelection:
    try:
        return select_user_visible_cash_flow(**kwargs)
    except Exception as exc:  # noqa: BLE001
        cutoff = kwargs.get("cutoff")
        try:
            cutoff_date = (
                cutoff if isinstance(cutoff, date) else date.fromisoformat(str(cutoff))
            )
        except ValueError:
            cutoff_date = date.today()
        mode = resolve_rollout_mode(kwargs.get("rollout_mode"))
        return _selection(
            ticker=str(kwargs.get("ticker") or "unknown"),
            market="unknown",
            industry="",
            mode=mode,
            state=(SelectionState.OFF if mode == CashFlowRolloutMode.OFF else SelectionState.SUPPRESSED),
            reason=f"cash_flow_optional_enrichment_failed:{type(exc).__name__}",
            assessment_date=cutoff_date,
            suppressed_claim_ids=tuple(
                str(item)
                for item in kwargs.get("suppressed_baseline_claim_ids") or ()
            ),
            display_reason="SUPPRESSED_OPTIONAL_FAILURE",
        )


def resolve_selected_unknowns(
    unknowns: Sequence[str],
    selection: UserVisibleCashFlowSelection,
    *,
    industry: str,
    source_text: str,
) -> tuple[str, ...]:
    context = selection.reasoning_context
    if context is None or not selection.resolved_unknown_ids:
        return tuple(unknowns)
    resolved, _audit = resolve_cash_flow_unknowns(
        unknowns,
        context,
        industry=industry,
        source_text=source_text,
    )
    return resolved


def _numeric_value(value: Decimal) -> int | float:
    return int(value) if value == value.to_integral_value() else float(value)


def fact_catalog_entries(
    selection: UserVisibleCashFlowSelection,
) -> list[dict[str, object]]:
    if not selection.user_visible_enabled:
        return []
    fact_type_by_metric = {
        Metric.OCF: "cash_flow_ocf",
        Metric.CAPEX: "cash_flow_ppe_capex",
        Metric.FCF: "cash_flow_fcf_ppe",
    }
    return [
        {
            "fact_id": fact.fact_id,
            "fact_type": fact_type_by_metric[fact.metric],
            "as_of_date": fact.period.end.isoformat(),
            "source": "canonical_cash_flow_fact",
            "fields": {
                "value": _numeric_value(fact.value),
                "currency": fact.currency,
                "period_start": fact.period.start.isoformat(),
                "period_end": fact.period.end.isoformat(),
                "period_type": fact.period.period_type.value,
                "fiscal_year": str(fact.period.fiscal_year),
                "fiscal_quarter": (
                    str(fact.period.fiscal_quarter)
                    if fact.period.fiscal_quarter is not None
                    else None
                ),
                "entity_scope": fact.entity_scope,
                "statement_basis": fact.statement_basis,
                "capex_scope": fact.capex_scope.value if fact.capex_scope else None,
                "input_fact_ids": list(fact.input_fact_ids),
                "cash_flow_user_visible_context_id": selection.context_id,
            },
            "prose_eligible": True,
            "interpretation_eligible": True,
            "numeric_registry_eligible": True,
        }
        for fact in selection.facts
    ]


def selection_to_dict(
    selection: UserVisibleCashFlowSelection,
) -> dict[str, object]:
    context = selection.reasoning_context
    fcf = next(
        (item for item in selection.facts if item.fact_id == selection.primary_fact_id),
        None,
    )
    return {
        "contract": CONTRACT_VERSION,
        "ticker": selection.ticker,
        "market": selection.market,
        "industry": selection.industry,
        "status": selection.selection_state.value,
        "rollout_mode": selection.rollout_mode.value,
        "selection_state": selection.selection_state.value,
        "selection_reason": selection.selection_reason,
        "display_reason": selection.display_reason,
        "evidence_signature": selection.evidence_signature,
        "assessment_date": selection.assessment_date.isoformat(),
        "cutoff": selection.assessment_date.isoformat(),
        "cash_flow_user_visible_context_id": selection.context_id,
        "primary_period": (
            {
                "period_start": context.primary_period.start.isoformat(),
                "period_end": context.primary_period.end.isoformat(),
                "period_type": context.primary_period.period_type.value,
                "fiscal_year": context.primary_period.fiscal_year,
                "fiscal_quarter": context.primary_period.fiscal_quarter,
            }
            if context and context.primary_period
            else None
        ),
        "filing_date": (
            context.primary_filing_date.isoformat()
            if context and context.primary_filing_date
            else None
        ),
        "financial_currency": fcf.currency if fcf else None,
        "freshness_state": context.freshness_state.value if context else None,
        "pit_state": (
            "PASS" if context and not context.point_in_time_exclusions else "NOT_SELECTED"
        ),
        "industry_applicability": context.industry_applicability if context else None,
        "materiality_reason": context.materiality_reason if context else None,
        "primary_metric": Metric.FCF.value if fcf else None,
        "primary_fact_ref": selection.primary_fact_id,
        "ocf_fact_ref": context.ocf_fact_id if context else None,
        "ppe_capex_fact_ref": context.capex_fact_id if context else None,
        "fcf_fact_ref": context.fcf_fact_id if context else None,
        "deterministic_relations": (
            [
                {
                    "metric": item.metric.value,
                    "current_fact_id": item.current_fact_id,
                    "prior_fact_id": item.prior_fact_id,
                    "relation": item.relation.value,
                }
                for item in context.deterministic_relations
            ]
            if context
            else []
        ),
        "baseline_consistency_state": selection.baseline_consistency_state,
        "resolved_unknown_ids": list(selection.resolved_unknown_ids),
        "suppressed_baseline_claim_ids": list(
            selection.suppressed_baseline_claim_ids
        ),
        "allowed_sections": ["business_earnings"] if fcf else [],
        "prohibited_claims": (
            list(context.prohibited_claims)
            if context
            else ["cash_flow_user_visible_when_disabled"]
        ),
        "ai_enabled": selection.user_visible_enabled,
        "fallback_enabled": selection.user_visible_enabled,
        "user_visible_enabled": selection.user_visible_enabled,
        "rendered_fallback_text": selection.rendered_text,
    }
