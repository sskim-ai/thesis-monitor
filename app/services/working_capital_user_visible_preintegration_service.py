from __future__ import annotations

import copy
import hashlib
import json
import re
from dataclasses import asdict, dataclass
from datetime import date
from enum import StrEnum
from pathlib import Path
from typing import Mapping, Sequence

from app.config import get_settings
from app.services.working_capital_runtime_evidence_service import (
    load_working_capital_snapshot,
)
from app.services.working_capital_shadow_consumption_service import (
    build_working_capital_reasoning_context,
    context_to_dict as reasoning_context_to_dict,
    reasoning_to_dict,
    render_working_capital_reasoning,
)


CONTRACT_VERSION = "working-capital-user-visible-v1"
RELATION_SEMANTICS_CONTRACT = "working-capital-relation-semantics-v1"
SIGNED_GAP_FIELD = "fields.gap_percentage_points_signed"
ABSOLUTE_GAP_FIELD = "fields.gap_percentage_points_abs"
ENABLE_GATE_VERSION = "working-capital-user-visible-enable-gate-v1"
PREVIEW_EVIDENCE_STATE = "PREVIEW_ONLY_NOT_ENABLEMENT_EVIDENCE"
ENABLED_EVIDENCE_STATE = "NATURAL_PROOF_GATED_USER_VISIBLE"
ENABLEMENT_READINESS_REPORT = "20260822-phase9-1e-1-readiness.json"


class WorkingCapitalMetricFamily(StrEnum):
    INVENTORY = "inventory"
    EXACT_TRADE_AR = "trade_accounts_receivable"


class WorkingCapitalUserVisibleMode(StrEnum):
    OFF = "OFF"
    SELECTIVE_INVENTORY = "SELECTIVE_INVENTORY"
    SELECTIVE_EXACT_TRADE_AR = "SELECTIVE_EXACT_TRADE_AR"
    SELECTIVE_INVENTORY_AND_EXACT_TRADE_AR = "SELECTIVE_INVENTORY_AND_EXACT_TRADE_AR"


class NaturalProofState(StrEnum):
    NOT_OBSERVED = "NOT_OBSERVED"
    LIVE_PASS = "LIVE_PASS"
    LIVE_FAIL = "LIVE_FAIL"


@dataclass(frozen=True)
class NaturalProofEvidence:
    metric_family: WorkingCapitalMetricFamily
    state: NaturalProofState
    packet_id: str | None = None
    receipt_id: str | None = None
    fact_ids: tuple[str, ...] = ()
    relation_ids: tuple[str, ...] = ()
    pit_safe: bool = False
    semantic_safe: bool = False
    causal_safe: bool = False
    numeric_binding_safe: bool = False
    production_influence_count: int = 0
    evidence_ref: str | None = None

    @property
    def verified_live_pass(self) -> bool:
        return all(
            (
                self.state == NaturalProofState.LIVE_PASS,
                bool(self.packet_id),
                bool(self.receipt_id),
                bool(self.fact_ids),
                bool(self.relation_ids),
                self.pit_safe,
                self.semantic_safe,
                self.causal_safe,
                self.numeric_binding_safe,
                self.production_influence_count == 0,
                bool(self.evidence_ref),
            )
        )


@dataclass(frozen=True)
class EnablementGate:
    contract: str
    gate_id: str
    metric_family: WorkingCapitalMetricFamily
    natural_proof_state: NaturalProofState
    canonical_core_state: str
    shadow_consumption_state: str
    runtime_canary_state: str
    open_p0: tuple[str, ...]
    open_material_p1: tuple[str, ...]
    semantic_validation_state: str
    causal_guard_state: str
    numeric_binding_state: str
    ai_fallback_parity_state: str
    eligible_for_enablement: bool
    blocking_reasons: tuple[str, ...]
    evidence_ref: str | None


@dataclass(frozen=True)
class ModePreflight:
    requested_mode: WorkingCapitalUserVisibleMode
    effective_mode: WorkingCapitalUserVisibleMode
    accepted: bool
    blocking_reasons: tuple[str, ...]
    gate_refs: tuple[str, ...]


@dataclass(frozen=True)
class WorkingCapitalUserVisibleContext:
    contract: str
    evidence_state: str
    working_capital_user_visible_context_id: str
    ticker: str
    packet_id: str
    assessment_date: str
    cutoff: str
    feature_mode: WorkingCapitalUserVisibleMode
    preview_target_mode: WorkingCapitalUserVisibleMode
    metric_family: WorkingCapitalMetricFamily
    semantic_scope: str
    balance_date: str
    currentness: str
    pit_state: str
    relation_id: str
    relation_family: str
    direction: str
    gap_percentage_points: str
    display_value: str
    selected_fact_ids: tuple[str, ...]
    industry: str
    industry_applicability: str
    materiality_reason: str
    display_reason: str
    numeric_owner: str
    resolved_unknowns: tuple[str, ...]
    remaining_unknowns: tuple[str, ...]
    allowed_claims: tuple[str, ...]
    prohibited_claims: tuple[str, ...]
    ai_enabled: bool
    fallback_enabled: bool
    user_visible_enabled: bool
    preview_selected: bool
    enablement_gate_ref: str
    suppression_reasons: tuple[str, ...]
    cash_flow_context_id: str | None
    cash_flow_period_end: str | None
    cash_flow_alignment_state: str


@dataclass(frozen=True)
class PreviewRendering:
    channel: str
    context_id: str
    ticker: str
    metric_family: WorkingCapitalMetricFamily
    relation_id: str
    selected_fact_ids: tuple[str, ...]
    semantic_scope: str
    balance_date: str
    direction: str
    display_value: str
    resolved_unknowns: tuple[str, ...]
    suppression_reasons: tuple[str, ...]
    numeric_owner: str
    text: str | None
    user_visible_enabled: bool


def _canonical_json(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")


def _identity(prefix: str, value: object) -> str:
    digest = hashlib.sha256(_canonical_json(value)).hexdigest()[:24]
    return f"{prefix}-{digest}"


def resolve_user_visible_mode(
    value: object | None = None,
) -> WorkingCapitalUserVisibleMode:
    candidate = value if value is not None else get_settings().working_capital_user_visible_mode
    try:
        return WorkingCapitalUserVisibleMode(str(candidate).strip().upper())
    except ValueError:
        return WorkingCapitalUserVisibleMode.OFF


def metric_families_for_mode(
    mode: WorkingCapitalUserVisibleMode,
) -> tuple[WorkingCapitalMetricFamily, ...]:
    if mode == WorkingCapitalUserVisibleMode.SELECTIVE_INVENTORY:
        return (WorkingCapitalMetricFamily.INVENTORY,)
    if mode == WorkingCapitalUserVisibleMode.SELECTIVE_EXACT_TRADE_AR:
        return (WorkingCapitalMetricFamily.EXACT_TRADE_AR,)
    if mode == WorkingCapitalUserVisibleMode.SELECTIVE_INVENTORY_AND_EXACT_TRADE_AR:
        return (
            WorkingCapitalMetricFamily.INVENTORY,
            WorkingCapitalMetricFamily.EXACT_TRADE_AR,
        )
    return ()


def natural_proof_from_receipt(
    metric_family: WorkingCapitalMetricFamily,
    receipt: Mapping[str, object] | None,
    sidecar: Mapping[str, object] | None,
    *,
    evidence_ref: str | None,
) -> NaturalProofEvidence:
    if not receipt:
        return NaturalProofEvidence(metric_family, NaturalProofState.NOT_OBSERVED)
    selected = receipt.get("selected_metric_families")
    selected_tickers = tuple(
        sorted(
            str(ticker)
            for ticker, family in (selected.items() if isinstance(selected, dict) else ())
            if str(family) == metric_family.value
        )
    )
    if not selected_tickers:
        return NaturalProofEvidence(metric_family, NaturalProofState.NOT_OBSERVED)

    selected_facts = receipt.get("selected_fact_ids")
    selected_relations = receipt.get("selected_relation_ids")
    fact_ids = tuple(
        sorted(
            {
                str(fact_id)
                for ticker in selected_tickers
                for fact_id in (
                    selected_facts.get(ticker, ()) if isinstance(selected_facts, dict) else ()
                )
            }
        )
    )
    relation_ids = tuple(
        sorted(
            {
                str(relation_id)
                for ticker in selected_tickers
                for relation_id in (
                    selected_relations.get(ticker, ())
                    if isinstance(selected_relations, dict)
                    else ()
                )
            }
        )
    )
    sidecar_subjects = sidecar.get("subjects") if isinstance(sidecar, dict) else None
    selected_contexts = [
        sidecar_subjects.get(ticker)
        for ticker in selected_tickers
        if isinstance(sidecar_subjects, dict)
    ]
    pit_safe = bool(selected_contexts) and all(
        isinstance(context, dict)
        and str(context.get("pit_state")) in {"PASS", "PASS_WITH_EXCLUSIONS"}
        and str(context.get("freshness_state")) == "CURRENT_FORMAL"
        for context in selected_contexts
    )
    binding = receipt.get("numeric_binding")
    numeric_safe = isinstance(binding, dict) and all(
        int(binding.get(key) or 0) == 0 for key in ("manual", "rejected", "unresolved")
    )
    semantic_safe = int(receipt.get("semantic_error_count") or 0) == 0
    causal_safe = semantic_safe and int(receipt.get("quality_error_count") or 0) == 0
    production_influence = int(receipt.get("production_influence_count") or 0)
    passed = all(
        (
            receipt.get("status") == "COMPLETE_PASS",
            bool(receipt.get("packet_id")),
            bool(receipt.get("receipt_id")),
            bool(fact_ids),
            bool(relation_ids),
            pit_safe,
            semantic_safe,
            causal_safe,
            numeric_safe,
            production_influence == 0,
            bool(evidence_ref),
        )
    )
    return NaturalProofEvidence(
        metric_family=metric_family,
        state=NaturalProofState.LIVE_PASS if passed else NaturalProofState.LIVE_FAIL,
        packet_id=str(receipt.get("packet_id") or "") or None,
        receipt_id=str(receipt.get("receipt_id") or "") or None,
        fact_ids=fact_ids,
        relation_ids=relation_ids,
        pit_safe=pit_safe,
        semantic_safe=semantic_safe,
        causal_safe=causal_safe,
        numeric_binding_safe=numeric_safe,
        production_influence_count=production_influence,
        evidence_ref=evidence_ref,
    )


def build_enablement_gate(
    metric_family: WorkingCapitalMetricFamily,
    proof: NaturalProofEvidence,
    *,
    canonical_core_state: str = "COMPLETE",
    shadow_consumption_state: str = "CLOSED_RETROSPECTIVE",
    runtime_canary_state: str = "DEPLOYED_PENDING_NATURAL",
    open_p0: Sequence[str] = (),
    open_material_p1: Sequence[str] = (),
    semantic_validation_state: str = "PASS",
    causal_guard_state: str = "PASS",
    numeric_binding_state: str = "PASS",
    ai_fallback_parity_state: str = "PASS",
) -> EnablementGate:
    blockers: list[str] = []
    if proof.state == NaturalProofState.NOT_OBSERVED:
        blockers.append("natural_proof_not_observed")
    elif proof.state == NaturalProofState.LIVE_FAIL:
        blockers.append("natural_proof_failed")
    elif not proof.verified_live_pass:
        blockers.append("natural_proof_evidence_incomplete")
    if canonical_core_state != "COMPLETE":
        blockers.append("canonical_core_not_complete")
    if shadow_consumption_state != "CLOSED_RETROSPECTIVE":
        blockers.append("shadow_consumption_not_closed")
    if runtime_canary_state not in {"DEPLOYED_PENDING_NATURAL", "LIVE_PASS"}:
        blockers.append("runtime_canary_not_safe")
    if open_p0:
        blockers.append("open_p0")
    if open_material_p1:
        blockers.append("open_material_p1")
    if semantic_validation_state != "PASS":
        blockers.append("semantic_validation_not_passed")
    if causal_guard_state != "PASS":
        blockers.append("causal_guard_not_passed")
    if numeric_binding_state != "PASS":
        blockers.append("numeric_binding_not_passed")
    if ai_fallback_parity_state != "PASS":
        blockers.append("ai_fallback_parity_not_passed")
    identity = {
        "contract": ENABLE_GATE_VERSION,
        "metric_family": metric_family.value,
        "proof": asdict(proof),
        "states": {
            "canonical": canonical_core_state,
            "shadow": shadow_consumption_state,
            "canary": runtime_canary_state,
            "semantic": semantic_validation_state,
            "causal": causal_guard_state,
            "numeric": numeric_binding_state,
            "ai_fallback_parity": ai_fallback_parity_state,
        },
        "open_p0": sorted(open_p0),
        "open_material_p1": sorted(open_material_p1),
    }
    return EnablementGate(
        contract=ENABLE_GATE_VERSION,
        gate_id=_identity("wc-enable-gate", identity),
        metric_family=metric_family,
        natural_proof_state=proof.state,
        canonical_core_state=canonical_core_state,
        shadow_consumption_state=shadow_consumption_state,
        runtime_canary_state=runtime_canary_state,
        open_p0=tuple(sorted(open_p0)),
        open_material_p1=tuple(sorted(open_material_p1)),
        semantic_validation_state=semantic_validation_state,
        causal_guard_state=causal_guard_state,
        numeric_binding_state=numeric_binding_state,
        ai_fallback_parity_state=ai_fallback_parity_state,
        eligible_for_enablement=not blockers,
        blocking_reasons=tuple(blockers),
        evidence_ref=proof.evidence_ref,
    )


def preflight_enablement_mode(
    requested: object,
    gates: Mapping[WorkingCapitalMetricFamily, EnablementGate],
) -> ModePreflight:
    mode = resolve_user_visible_mode(requested)
    if mode == WorkingCapitalUserVisibleMode.OFF:
        return ModePreflight(mode, mode, True, (), ())
    if mode != WorkingCapitalUserVisibleMode.SELECTIVE_INVENTORY:
        return ModePreflight(
            requested_mode=mode,
            effective_mode=WorkingCapitalUserVisibleMode.OFF,
            accepted=False,
            blocking_reasons=("inventory_only_rollout_policy",),
            gate_refs=(),
        )
    blockers: list[str] = []
    gate_refs: list[str] = []
    for family in metric_families_for_mode(mode):
        gate = gates.get(family)
        if gate is None:
            blockers.append(f"{family.value}:enablement_gate_missing")
            continue
        gate_refs.append(gate.gate_id)
        blockers.extend(f"{family.value}:{reason}" for reason in gate.blocking_reasons)
        if not gate.eligible_for_enablement and not gate.blocking_reasons:
            blockers.append(f"{family.value}:enablement_denied")
    return ModePreflight(
        requested_mode=mode,
        effective_mode=(mode if not blockers else WorkingCapitalUserVisibleMode.OFF),
        accepted=not blockers,
        blocking_reasons=tuple(dict.fromkeys(blockers)),
        gate_refs=tuple(gate_refs),
    )


def _resolved_unknown_texts(context: Mapping[str, object]) -> tuple[str, ...]:
    return tuple(
        str(item.get("original"))
        for item in context.get("resolved_unknowns") or ()
        if isinstance(item, dict) and item.get("state") == "RESOLVED_EXACT" and item.get("original")
    )


def _relation_semantic_error(
    family: WorkingCapitalMetricFamily,
    relation: Mapping[str, object],
) -> str | None:
    balance_metric = str(relation.get("balance_metric") or "")
    balance_scope = str(relation.get("balance_scope") or "")
    semantic = str(relation.get("balance_semantic") or "")
    relation_family = str(relation.get("family") or "")
    if family == WorkingCapitalMetricFamily.INVENTORY:
        if balance_metric != "inventory" or balance_scope != "total":
            return "inventory_not_exact_total"
        if "inventor" not in semantic.lower():
            return "inventory_semantic_not_verified"
        if relation_family not in {"inventory_vs_revenue", "inventory_vs_cogs"}:
            return "inventory_relation_not_supported"
        return None
    if balance_metric != "trade_accounts_receivable":
        return "trade_ar_metric_not_exact"
    if relation_family != "trade_ar_vs_revenue":
        return "trade_ar_relation_not_supported"
    normalized = semantic.lower()
    if "trade" not in normalized or "receiv" not in normalized:
        return "trade_ar_semantic_not_exact"
    return None


def build_preview_context(
    subject: Mapping[str, object],
    gate: EnablementGate,
    *,
    preview_target_mode: WorkingCapitalUserVisibleMode,
    feature_mode: WorkingCapitalUserVisibleMode = WorkingCapitalUserVisibleMode.OFF,
    cash_flow_context_id: str | None = None,
    cash_flow_period_end: str | None = None,
) -> WorkingCapitalUserVisibleContext | None:
    raw_family = subject.get("runtime_selected_metric")
    try:
        family = WorkingCapitalMetricFamily(str(raw_family))
    except ValueError:
        return None
    if family not in metric_families_for_mode(preview_target_mode):
        return None
    context = subject.get("context")
    reasoning = subject.get("reasoning")
    if not isinstance(context, dict) or not isinstance(reasoning, dict):
        return None
    relations = context.get("selected_relations")
    claims = reasoning.get("numeric_claims")
    if not isinstance(relations, list) or len(relations) != 1:
        return None
    if not isinstance(claims, list) or len(claims) != 1:
        return None
    relation = relations[0]
    claim = claims[0]
    if not isinstance(relation, dict) or not isinstance(claim, dict):
        return None

    suppression_reasons: list[str] = []
    semantic_error = _relation_semantic_error(family, relation)
    if semantic_error:
        suppression_reasons.append(semantic_error)
    if subject.get("selector_parity") is not True:
        suppression_reasons.append("selector_parity_failed")
    if context.get("freshness_state") != "CURRENT_FORMAL":
        suppression_reasons.append("not_current_formal")
    if context.get("pit_state") not in {"PASS", "PASS_WITH_EXCLUSIONS"}:
        suppression_reasons.append("pit_not_safe")
    if claim.get("owner") != "business_earnings":
        suppression_reasons.append("numeric_owner_invalid")
    resolved_unknowns = _resolved_unknown_texts(context)
    balance_date = str(context.get("latest_formal_balance_date") or "")
    if not cash_flow_context_id:
        cash_flow_alignment_state = "NOT_PRESENT"
    elif not cash_flow_period_end:
        cash_flow_alignment_state = "PERIOD_UNVERIFIED"
    elif cash_flow_period_end != balance_date:
        cash_flow_alignment_state = "INCOMPATIBLE_PERIOD"
    else:
        cash_flow_alignment_state = "COMPATIBLE_PERIOD_END"
    if cash_flow_alignment_state == "COMPATIBLE_PERIOD_END" and not resolved_unknowns:
        suppression_reasons.append("cash_flow_higher_priority_no_incremental_unknown_resolution")

    relation_id = str(relation.get("relation_id") or "")
    fact_ids = tuple(str(item) for item in relation.get("input_fact_ids") or ())
    display_value = str(claim.get("display") or "")
    gap = str(relation.get("gap_percentage_points") or "")
    if not relation_id or not fact_ids or not display_value or not gap:
        suppression_reasons.append("relation_lineage_incomplete")
    preview_selected = not suppression_reasons
    ticker = str(subject.get("ticker") or context.get("ticker") or "")
    identity = {
        "contract": CONTRACT_VERSION,
        "ticker": ticker,
        "packet_id": context.get("packet_id"),
        "relation_id": relation_id,
        "fact_ids": fact_ids,
        "preview_target_mode": preview_target_mode.value,
        "gate_ref": gate.gate_id,
        "suppression_reasons": suppression_reasons,
    }
    enabled = bool(
        preview_selected
        and feature_mode != WorkingCapitalUserVisibleMode.OFF
        and gate.eligible_for_enablement
        and family in metric_families_for_mode(feature_mode)
    )
    return WorkingCapitalUserVisibleContext(
        contract=CONTRACT_VERSION,
        evidence_state=(ENABLED_EVIDENCE_STATE if enabled else PREVIEW_EVIDENCE_STATE),
        working_capital_user_visible_context_id=_identity("wc-visible", identity),
        ticker=ticker,
        packet_id=str(context.get("packet_id") or ""),
        assessment_date=str(context.get("assessment_date") or ""),
        cutoff=str(context.get("cutoff") or ""),
        feature_mode=feature_mode,
        preview_target_mode=preview_target_mode,
        metric_family=family,
        semantic_scope=(
            "exact_total_inventory"
            if family == WorkingCapitalMetricFamily.INVENTORY
            else "exact_trade_accounts_receivable"
        ),
        balance_date=balance_date,
        currentness=str(context.get("freshness_state") or ""),
        pit_state=str(context.get("pit_state") or ""),
        relation_id=relation_id,
        relation_family=str(relation.get("family") or ""),
        direction=str(relation.get("direction") or ""),
        gap_percentage_points=gap,
        display_value=display_value,
        selected_fact_ids=fact_ids,
        industry=str(subject.get("industry") or context.get("industry") or ""),
        industry_applicability=str(relation.get("applicability") or ""),
        materiality_reason=str(context.get("materiality_reason") or ""),
        display_reason=(
            "selected_incremental_to_compatible_cash_flow"
            if preview_selected and cash_flow_alignment_state == "COMPATIBLE_PERIOD_END"
            else (
                "selected_current_formal_material_relation"
                if preview_selected
                else "suppressed_by_user_visible_guard"
            )
        ),
        numeric_owner="business_earnings",
        resolved_unknowns=resolved_unknowns if preview_selected else (),
        remaining_unknowns=tuple(str(item) for item in context.get("remaining_unknowns") or ()),
        allowed_claims=(
            "typed_relation",
            "cautious_earnings_quality_context",
            "one_primary_relation",
        ),
        prohibited_claims=(
            "broad_ar_as_exact_trade_ar",
            "inventory_component_as_total",
            "working_capital_causal_overclaim",
            "dso_inventory_days_dpo_ccc",
            "working_capital_only_status_or_valuation_change",
            "duplicate_exact_number_outside_business_earnings",
        ),
        ai_enabled=enabled,
        fallback_enabled=enabled,
        user_visible_enabled=enabled,
        preview_selected=preview_selected,
        enablement_gate_ref=gate.gate_id,
        suppression_reasons=tuple(suppression_reasons),
        cash_flow_context_id=cash_flow_context_id,
        cash_flow_period_end=cash_flow_period_end,
        cash_flow_alignment_state=cash_flow_alignment_state,
    )


_INDUSTRY_TAIL = {
    "memory_semiconductor": "ASP·제품 믹스·메모리 수요와 함께 확인하며 사이클 방향을 확정하지 않습니다.",
    "automotive": "인도량·인센티브·제품 믹스와 함께 확인하며 수요 방향을 확정하지 않습니다.",
    "steel_materials": "철강 스프레드·원재료·물량과 함께 확인하며 사이클 방향을 확정하지 않습니다.",
    "industrial_epc": "수주 매출의 회수 전환을 점검하되 고객 지급 지연을 확정하지 않습니다.",
    "transport_logistics": "운송 매출의 회수 전환을 점검하되 고객 지급 지연을 확정하지 않습니다.",
}


def render_preview(
    context: WorkingCapitalUserVisibleContext,
    *,
    channel: str,
) -> PreviewRendering:
    text: str | None = None
    if context.preview_selected:
        metric_label = (
            "재고 증가율"
            if context.metric_family == WorkingCapitalMetricFamily.INVENTORY
            else "거래 매출채권 증가율"
        )
        flow_label = (
            "매출원가 증가율" if context.relation_family.endswith("_vs_cogs") else "매출 증가율"
        )
        direction = "앞섰습니다" if context.direction == "GREATER" else "밑돌았습니다"
        tail = _INDUSTRY_TAIL.get(
            context.industry,
            "운전자본 전환을 점검하되 원인을 단정하지 않습니다.",
        )
        text = f"{metric_label}은 {flow_label}보다 {context.display_value} {direction}. {tail}"
    return PreviewRendering(
        channel=channel,
        context_id=context.working_capital_user_visible_context_id,
        ticker=context.ticker,
        metric_family=context.metric_family,
        relation_id=context.relation_id,
        selected_fact_ids=context.selected_fact_ids,
        semantic_scope=context.semantic_scope,
        balance_date=context.balance_date,
        direction=context.direction,
        display_value=context.display_value,
        resolved_unknowns=context.resolved_unknowns,
        suppression_reasons=context.suppression_reasons,
        numeric_owner=context.numeric_owner,
        text=text,
        user_visible_enabled=context.user_visible_enabled,
    )


_UNSUPPORTED_LANGUAGE = re.compile(
    r"(?:DSO|CCC|Inventory\s*Days|DPO|재고일수|"
    r"고객(?:이|의)?\s*지급\s*지연(?:이|을)?\s*확정(?!하지)|"
    r"수요\s*(?:붕괴|부진)\s*확정(?!하지)|공급과잉\s*확정(?!하지)|"
    r"채널\s*스터핑|valuation|밸류에이션\s*(?:상향|하향))",
    re.IGNORECASE,
)


def validate_preview(
    context: WorkingCapitalUserVisibleContext,
    rendering: PreviewRendering,
    *,
    thesis_status_changed: bool = False,
    valuation_changed: bool = False,
) -> tuple[str, ...]:
    errors: list[str] = []
    if rendering.context_id != context.working_capital_user_visible_context_id:
        errors.append("context_id_mismatch")
    if rendering.metric_family != context.metric_family:
        errors.append("metric_family_mismatch")
    if rendering.relation_id != context.relation_id:
        errors.append("relation_id_mismatch")
    if rendering.selected_fact_ids != context.selected_fact_ids:
        errors.append("fact_lineage_mismatch")
    if rendering.numeric_owner != "business_earnings":
        errors.append("numeric_owner_invalid")
    if context.user_visible_enabled:
        if context.evidence_state != ENABLED_EVIDENCE_STATE:
            errors.append("enabled_evidence_marker_missing")
        if not rendering.user_visible_enabled:
            errors.append("enabled_rendering_state_mismatch")
    else:
        if context.evidence_state != PREVIEW_EVIDENCE_STATE:
            errors.append("preview_evidence_marker_missing")
        if rendering.user_visible_enabled:
            errors.append("feature_off_user_visible_leak")
    if not context.preview_selected:
        if rendering.text is not None:
            errors.append("suppressed_context_rendered")
        return tuple(errors)
    text = rendering.text or ""
    if not text:
        errors.append("selected_context_missing_text")
    if text.count(context.display_value) != 1:
        errors.append("primary_numeric_claim_count_invalid")
    if _UNSUPPORTED_LANGUAGE.search(text):
        errors.append("unsupported_semantic_or_causal_claim")
    if context.metric_family == WorkingCapitalMetricFamily.EXACT_TRADE_AR:
        if "거래 매출채권" not in text:
            errors.append("exact_trade_ar_label_missing")
    elif "재고" not in text:
        errors.append("inventory_label_missing")
    if thesis_status_changed:
        errors.append("working_capital_only_status_change")
    if valuation_changed:
        errors.append("working_capital_only_valuation_change")
    return tuple(errors)


def preview_parity_errors(
    ai: PreviewRendering,
    fallback: PreviewRendering,
) -> tuple[str, ...]:
    comparable = (
        "context_id",
        "ticker",
        "metric_family",
        "relation_id",
        "selected_fact_ids",
        "semantic_scope",
        "balance_date",
        "direction",
        "display_value",
        "resolved_unknowns",
        "suppression_reasons",
        "numeric_owner",
        "user_visible_enabled",
    )
    return tuple(
        f"ai_fallback_{field}_mismatch"
        for field in comparable
        if getattr(ai, field) != getattr(fallback, field)
    )


def context_to_dict(context: WorkingCapitalUserVisibleContext) -> dict[str, object]:
    return asdict(context)


def rendering_to_dict(rendering: PreviewRendering) -> dict[str, object]:
    return asdict(rendering)


def gate_to_dict(gate: EnablementGate) -> dict[str, object]:
    return asdict(gate)


def _repository_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _read_json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return value


def enablement_gates_from_report(
    path: Path | None = None,
) -> dict[WorkingCapitalMetricFamily, EnablementGate]:
    report_path = path or (
        _repository_root() / "docs" / "reports" / ENABLEMENT_READINESS_REPORT
    )
    if not report_path.exists():
        return {}
    payload = _read_json(report_path)
    proof_rows = payload.get("natural_proofs")
    if not isinstance(proof_rows, dict):
        return {}
    gates: dict[WorkingCapitalMetricFamily, EnablementGate] = {}
    for family in WorkingCapitalMetricFamily:
        row = proof_rows.get(family.value)
        if not isinstance(row, dict):
            continue
        try:
            state = NaturalProofState(str(row.get("state") or "NOT_OBSERVED"))
        except ValueError:
            state = NaturalProofState.LIVE_FAIL
        proof = NaturalProofEvidence(
            metric_family=family,
            state=state,
            packet_id=str(row.get("packet_id") or "") or None,
            receipt_id=str(row.get("receipt_id") or "") or None,
            fact_ids=tuple(str(item) for item in row.get("fact_ids") or ()),
            relation_ids=tuple(str(item) for item in row.get("relation_ids") or ()),
            pit_safe=row.get("pit_safe") is True,
            semantic_safe=row.get("semantic_safe") is True,
            causal_safe=row.get("causal_safe") is True,
            numeric_binding_safe=row.get("numeric_binding_safe") is True,
            production_influence_count=int(row.get("production_influence_count") or 0),
            evidence_ref=str(row.get("evidence_ref") or "") or None,
        )
        validation = payload.get("validation")
        validation = validation if isinstance(validation, dict) else {}
        gates[family] = build_enablement_gate(
            family,
            proof,
            canonical_core_state=str(payload.get("canonical_core_state") or "UNKNOWN"),
            shadow_consumption_state=str(
                payload.get("shadow_consumption_state") or "UNKNOWN"
            ),
            runtime_canary_state=str(payload.get("runtime_canary_state") or "UNKNOWN"),
            open_p0=tuple(str(item) for item in payload.get("open_p0") or ()),
            open_material_p1=tuple(
                str(item) for item in payload.get("open_material_p1") or ()
            ),
            semantic_validation_state=str(
                validation.get("semantic") or "UNKNOWN"
            ),
            causal_guard_state=str(validation.get("causal") or "UNKNOWN"),
            numeric_binding_state=str(validation.get("numeric") or "UNKNOWN"),
            ai_fallback_parity_state=str(
                validation.get("ai_fallback_parity") or "UNKNOWN"
            ),
        )
    return gates


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
        context = analysis.get("working_capital_user_visible")
        if isinstance(context, dict):
            return dict(context)
    return {}


def select_user_visible_inventory(
    *,
    ticker: str,
    market: str,
    packet_id: str,
    assessment_date: date,
    industry: str,
    monitoring_text: str,
    existing_unknowns: Sequence[str],
    latest_formal_balance_date: date | None,
    latest_provisional_period_end: date | None,
    cash_flow_context_id: str | None,
    cash_flow_period_end: date | None,
    rollout_mode: object | None = None,
    gates: Mapping[WorkingCapitalMetricFamily, EnablementGate] | None = None,
    canonical_report_path: Path | None = None,
    previous_user_visible_context: Mapping[str, object] | None = None,
) -> WorkingCapitalUserVisibleContext | None:
    mode = resolve_user_visible_mode(rollout_mode)
    active_gates = dict(gates or enablement_gates_from_report())
    preflight = preflight_enablement_mode(mode, active_gates)
    if not preflight.accepted or preflight.effective_mode != mode or mode == WorkingCapitalUserVisibleMode.OFF:
        return None
    loaded = load_working_capital_snapshot(
        ticker,
        as_of=assessment_date,
        report_path=canonical_report_path,
    )
    if loaded is None:
        return None
    snapshot, record = loaded
    latest_formal = max(
        (
            item
            for item in (
                snapshot.latest_safe_working_capital_date,
                latest_formal_balance_date,
            )
            if item is not None
        ),
        default=None,
    )
    reasoning_context = build_working_capital_reasoning_context(
        snapshot,
        ticker=ticker,
        market=market,
        packet_id=packet_id,
        assessment_date=assessment_date,
        cutoff=assessment_date,
        industry=industry or str(record.get("industry") or ""),
        monitoring_text=monitoring_text,
        existing_unknowns=existing_unknowns,
        latest_formal_balance_date=latest_formal,
        latest_provisional_period_end=latest_provisional_period_end,
        cash_flow_period_end=cash_flow_period_end,
    )
    reasoning = render_working_capital_reasoning(reasoning_context)
    if reasoning is None or reasoning_context.selected_relation is None:
        return None
    family = WorkingCapitalMetricFamily(
        reasoning_context.selected_relation.balance_metric.value
    )
    if family != WorkingCapitalMetricFamily.INVENTORY:
        return None
    subject = {
        "ticker": ticker,
        "industry": industry or str(record.get("industry") or ""),
        "runtime_selected_metric": family.value,
        "selector_parity": True,
        "context": reasoning_context_to_dict(reasoning_context),
        "reasoning": reasoning_to_dict(reasoning),
    }
    gate = active_gates.get(family)
    if gate is None:
        return None
    selected = build_preview_context(
        subject,
        gate,
        preview_target_mode=WorkingCapitalUserVisibleMode.SELECTIVE_INVENTORY,
        feature_mode=mode,
        cash_flow_context_id=cash_flow_context_id,
        cash_flow_period_end=(cash_flow_period_end.isoformat() if cash_flow_period_end else None),
    )
    if selected is None or not selected.user_visible_enabled:
        return None
    if (
        cash_flow_context_id
        and selected.cash_flow_alignment_state != "COMPATIBLE_PERIOD_END"
    ):
        return None
    previous_id = str(
        (previous_user_visible_context or {}).get(
            "working_capital_user_visible_context_id"
        )
        or ""
    )
    if previous_id and previous_id == selected.working_capital_user_visible_context_id:
        return None
    previous_relation = str(
        (previous_user_visible_context or {}).get("relation_id") or ""
    )
    previous_facts = tuple(
        str(item)
        for item in (previous_user_visible_context or {}).get("selected_fact_ids") or ()
    )
    if (
        (previous_user_visible_context or {}).get("user_visible_enabled") is True
        and previous_relation == selected.relation_id
        and previous_facts == selected.selected_fact_ids
    ):
        return None
    return selected


def safe_select_user_visible_inventory(**kwargs: object) -> WorkingCapitalUserVisibleContext | None:
    try:
        return select_user_visible_inventory(**kwargs)
    except Exception:  # noqa: BLE001
        return None


def resolve_selected_inventory_unknowns(
    unknowns: Sequence[str],
    context: WorkingCapitalUserVisibleContext | None,
) -> tuple[str, ...]:
    if context is None or not context.user_visible_enabled:
        return tuple(unknowns)
    resolved = set(context.resolved_unknowns)
    return tuple(item for item in unknowns if item not in resolved)


def fact_catalog_entries(
    context: WorkingCapitalUserVisibleContext | None,
) -> list[dict[str, object]]:
    if context is None or not context.user_visible_enabled:
        return []
    return [
        {
            "fact_id": context.relation_id,
            "fact_type": "working_capital_inventory_relation",
            "as_of_date": context.balance_date,
            "source": "canonical_working_capital_relation",
            "fields": {
                "relation_semantics_contract": RELATION_SEMANTICS_CONTRACT,
                "gap_percentage_points_signed": float(
                    context.gap_percentage_points
                ),
                "gap_percentage_points_abs": abs(float(context.gap_percentage_points)),
                "direction": context.direction,
                "relation_family": context.relation_family,
                "lhs_semantic": "inventory_growth",
                "rhs_semantic": (
                    "cogs_growth"
                    if context.relation_family == "inventory_vs_cogs"
                    else "revenue_growth"
                ),
                "comparison_basis": "year_over_year_growth_rate_percentage_points",
                "balance_date": context.balance_date,
                "semantic_scope": context.semantic_scope,
                "input_fact_ids": list(context.selected_fact_ids),
                "working_capital_user_visible_context_id": (
                    context.working_capital_user_visible_context_id
                ),
            },
            "prose_eligible": True,
            "interpretation_eligible": True,
            "numeric_registry_eligible": True,
        },
        *(
            {
                "fact_id": fact_id,
                "fact_type": "working_capital_lineage_input",
                "as_of_date": context.balance_date,
                "source": "canonical_working_capital_fact",
                "fields": {
                    "relation_id": context.relation_id,
                    "semantic_scope": context.semantic_scope,
                },
                "prose_eligible": False,
                "interpretation_eligible": False,
                "numeric_registry_eligible": False,
            }
            for fact_id in context.selected_fact_ids
        ),
    ]


def _direction_matches_value(direction: str, value: float) -> bool:
    if value < 0:
        return direction == "LOWER"
    if value > 0:
        return direction == "GREATER"
    return direction == "EQUAL"


def ensure_relation_semantics(packet: Mapping[str, object]) -> dict[str, object]:
    """Add typed signed relation fields to legacy in-memory packets only."""
    upgraded = copy.deepcopy(dict(packet))
    stocks = upgraded.get("stocks")
    if not isinstance(stocks, list):
        return upgraded
    for stock in stocks:
        if not isinstance(stock, dict):
            continue
        context = stock.get("working_capital_user_visible")
        facts = stock.get("fact_catalog")
        if not isinstance(context, Mapping) or not isinstance(facts, list):
            continue
        relation_id = str(context.get("relation_id") or "")
        relation_family = str(context.get("relation_family") or "")
        direction = str(context.get("direction") or "")
        if relation_family not in {"inventory_vs_cogs", "inventory_vs_revenue"}:
            continue
        try:
            signed_gap = float(context["gap_percentage_points"])
        except (KeyError, TypeError, ValueError):
            continue
        if not _direction_matches_value(direction, signed_gap):
            continue
        changed = False
        for fact in facts:
            if not isinstance(fact, dict) or str(fact.get("fact_id") or "") != relation_id:
                continue
            if fact.get("fact_type") != "working_capital_inventory_relation":
                continue
            fields = fact.get("fields")
            if not isinstance(fields, dict):
                continue
            try:
                absolute_gap = float(fields["gap_percentage_points_abs"])
            except (KeyError, TypeError, ValueError):
                continue
            if abs(abs(signed_gap) - absolute_gap) > 1e-9:
                continue
            fields.update(
                {
                    "relation_semantics_contract": RELATION_SEMANTICS_CONTRACT,
                    "gap_percentage_points_signed": signed_gap,
                    "direction": direction,
                    "relation_family": relation_family,
                    "lhs_semantic": "inventory_growth",
                    "rhs_semantic": (
                        "cogs_growth"
                        if relation_family == "inventory_vs_cogs"
                        else "revenue_growth"
                    ),
                    "comparison_basis": (
                        "year_over_year_growth_rate_percentage_points"
                    ),
                }
            )
            changed = True
            break
        if changed:
            from app.services.numeric_semantic_registry import build_numeric_registry

            stock["numeric_registry"] = build_numeric_registry(facts)
    return upgraded


_LOWER_WORDING = re.compile(r"밑돌|낮(?:았|은|다)|하회|\b(?:lower|below|trails?)\b", re.I)
_HIGHER_WORDING = re.compile(
    r"앞섰|웃돌|높(?:았|은|다)|상회|\b(?:higher|above|exceeds?)\b",
    re.I,
)


def _directional_text_matches_context(
    text: str,
    context: Mapping[str, object],
) -> bool:
    family = str(context.get("relation_family") or "")
    direction = str(context.get("direction") or "")
    lowered = text.lower()
    if "재고" not in text and "inventory" not in lowered:
        return False
    if family == "inventory_vs_cogs":
        comparator_matches = "매출원가" in text or bool(re.search(r"\bcogs?\b", lowered))
    elif family == "inventory_vs_revenue":
        comparator_matches = (
            ("매출" in text and "매출원가" not in text)
            or bool(re.search(r"\brevenue\b", lowered))
        )
    else:
        return False
    lower = bool(_LOWER_WORDING.search(text))
    higher = bool(_HIGHER_WORDING.search(text))
    return bool(
        comparator_matches
        and ((direction == "LOWER" and lower and not higher)
             or (direction == "GREATER" and higher and not lower))
    )


def normalize_directional_numeric_refs(
    packet: Mapping[str, object],
    output_value: object,
) -> tuple[object, dict[str, object]]:
    """Retarget an unambiguous legacy abs ref to the typed signed relation."""
    if not isinstance(output_value, Mapping):
        return output_value, {"contract": RELATION_SEMANTICS_CONTRACT, "upgrades": []}
    output = copy.deepcopy(dict(output_value))
    stocks = {
        str(item.get("ticker") or ""): item
        for item in packet.get("stocks", [])
        if isinstance(item, Mapping)
    }
    upgrades: list[dict[str, object]] = []
    for review in output.get("stock_reviews", []):
        if not isinstance(review, dict):
            continue
        ticker = str(review.get("ticker") or "")
        stock = stocks.get(ticker)
        if not isinstance(stock, Mapping):
            continue
        context = stock.get("working_capital_user_visible")
        refs = review.get("numeric_fact_refs")
        business = review.get("business_earnings")
        text = business.get("text") if isinstance(business, Mapping) else None
        if not isinstance(context, Mapping) or not isinstance(refs, list) or not isinstance(text, str):
            continue
        relation_id = str(context.get("relation_id") or "")
        signed_available = any(
            isinstance(item, Mapping)
            and str(item.get("fact_id") or "") == relation_id
            and item.get("field_path") == SIGNED_GAP_FIELD
            and item.get("prose_allowed") is True
            for item in stock.get("numeric_registry", [])
        )
        if not signed_available or not _directional_text_matches_context(text, context):
            continue
        for ref in refs:
            if not isinstance(ref, dict):
                continue
            if (
                str(ref.get("fact_id") or "") != relation_id
                or ref.get("field_path") != ABSOLUTE_GAP_FIELD
                or ref.get("text_ref") != "business_earnings.text"
            ):
                continue
            placeholder = f"{{{{numeric:{ref.get('ref_id')}}}}}"
            if text.count(placeholder) != 1:
                continue
            ref["field_path"] = SIGNED_GAP_FIELD
            upgrades.append(
                {
                    "ticker": ticker,
                    "ref_id": ref.get("ref_id"),
                    "fact_id": relation_id,
                    "from": ABSOLUTE_GAP_FIELD,
                    "to": SIGNED_GAP_FIELD,
                }
            )
    return output, {
        "contract": RELATION_SEMANTICS_CONTRACT,
        "status": "applied" if upgrades else "no_change",
        "upgrades": upgrades,
    }
