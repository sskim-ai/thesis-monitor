from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping, Sequence
from enum import StrEnum

from pydantic import Field

from app.services.cross_market_decision_engine_service import (
    DecisionEvidenceRef,
    FinancialComparisonKind,
    FinancialEvidenceQuality,
    FrozenModel,
)
from app.services.logical_condition_service import CheckpointMetric


CONTRACT_VERSION = "configured-signal-evidence-view-v1"
VALIDATOR_CONTRACT = "configured-signal-field-ownership-validator-v1"

CURRENT_DIRECTIONAL_REFERENCE_FIELDS = (
    "buy_drivers",
    "sell_drivers",
    "dominant_evidence",
    "core_investment_judgment",
    "material_directional_anchor_basis",
)

_CONFIGURED_SOURCE_ROLES = {
    "stock.thesis.strengthen_signals": "STRENGTHEN_SIGNAL",
    "stock.thesis.weaken_signals": "WEAKEN_SIGNAL",
    "stock.thesis.invalidation_signals": "INVALIDATION_SIGNAL",
}
_CHECKPOINT_METRIC_REQUIREMENTS = {
    CheckpointMetric.OCF: frozenset({"operating_cash_flow"}),
    CheckpointMetric.PPE_CAPEX: frozenset({"ppe_capex_cash_outflow"}),
    CheckpointMetric.FCF: frozenset(
        {"free_cash_flow_ppe", "free_cash_flow", "reported_free_cash_flow"}
    ),
    CheckpointMetric.ROIC: frozenset({"return_on_invested_capital"}),
    CheckpointMetric.CCC: frozenset({"cash_conversion_cycle"}),
    CheckpointMetric.DSO: frozenset({"days_sales_outstanding"}),
    CheckpointMetric.DPO: frozenset({"days_payables_outstanding"}),
}
_NET_DEBT_LANGUAGE = re.compile(r"순부채|\b(?:industrial\s+)?net[ -]debt\b", re.IGNORECASE)


class ConfiguredSignalSourceRole(StrEnum):
    STRENGTHEN_SIGNAL = "STRENGTHEN_SIGNAL"
    WEAKEN_SIGNAL = "WEAKEN_SIGNAL"
    INVALIDATION_SIGNAL = "INVALIDATION_SIGNAL"


class ConfiguredSignalFulfillmentState(StrEnum):
    CONFIGURED_ONLY = "CONFIGURED_ONLY"
    FULFILLED_BY_CURRENT_EVIDENCE = "FULFILLED_BY_CURRENT_EVIDENCE"
    UNKNOWN = "UNKNOWN"


class ConfiguredSignalFulfillmentEvidence(FrozenModel):
    signal_ref_id: str = Field(min_length=1)
    current_evidence_refs: tuple[str, ...] = Field(min_length=1, max_length=12)


class ConfiguredSignalEvidenceItem(FrozenModel):
    ref_id: str
    source_ref: str
    source_role: ConfiguredSignalSourceRole
    fulfillment_state: ConfiguredSignalFulfillmentState
    fulfillment_evidence_refs: tuple[str, ...] = ()
    fulfillment_denial_reasons: tuple[str, ...] = ()
    current_directional_driver_eligible: bool
    future_reevaluation_eligible: bool
    risk_context_eligible: bool
    material_anchor_eligible: bool
    dominant_evidence_eligible: bool
    current_core_judgment_eligible: bool


class ConfiguredSignalEvidenceView(FrozenModel):
    contract: str = CONTRACT_VERSION
    ticker: str
    items: tuple[ConfiguredSignalEvidenceItem, ...] = ()
    view_sha256: str

    @property
    def by_ref(self) -> dict[str, ConfiguredSignalEvidenceItem]:
        return {item.ref_id: item for item in self.items}


class ConfiguredSignalFieldViolation(FrozenModel):
    field_path: str
    ref_id: str
    source_role: ConfiguredSignalSourceRole
    fulfillment_state: ConfiguredSignalFulfillmentState


class ConfiguredSignalFieldValidation(FrozenModel):
    contract: str = VALIDATOR_CONTRACT
    valid: bool
    errors: tuple[str, ...] = ()
    configured_signal_count: int = 0
    configured_only_signal_count: int = 0
    fulfilled_signal_count: int = 0
    unknown_fulfillment_signal_count: int = 0
    configured_only_current_driver_violation_count: int = 0
    configured_signal_false_fulfillment_count: int = 0
    violations: tuple[ConfiguredSignalFieldViolation, ...] = ()


def configured_signal_source_role(
    ref: DecisionEvidenceRef,
) -> ConfiguredSignalSourceRole | None:
    source_ref = ref.source_ref.casefold()
    for prefix, role in _CONFIGURED_SOURCE_ROLES.items():
        if source_ref == prefix or source_ref.startswith(f"{prefix}."):
            return ConfiguredSignalSourceRole(role)
    return None


def is_configured_signal_source_ref(source_ref: str) -> bool:
    folded = source_ref.casefold()
    return any(
        folded == prefix or folded.startswith(f"{prefix}.")
        for prefix in _CONFIGURED_SOURCE_ROLES
    )


def _canonical_sha256(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        ).encode("utf-8")
    ).hexdigest()


def _required_financial_metric_groups(
    signal: DecisionEvidenceRef,
) -> tuple[frozenset[str], ...]:
    logical_metrics = (
        signal.logical_condition.metric_refs
        if signal.logical_condition is not None
        else signal.metric_refs
    )
    groups = [
        _CHECKPOINT_METRIC_REQUIREMENTS[metric]
        for metric in logical_metrics
        if metric in _CHECKPOINT_METRIC_REQUIREMENTS
    ]
    if _NET_DEBT_LANGUAGE.search(signal.statement):
        groups.append(frozenset({"net_debt"}))
    return tuple(dict.fromkeys(groups))


def _safe_current_financial_metrics(
    refs: Sequence[DecisionEvidenceRef],
) -> set[str]:
    metrics: set[str] = set()
    for ref in refs:
        context = ref.financial_context
        if context is None or context.quality != FinancialEvidenceQuality.VERIFIED:
            continue
        comparison = context.comparison
        if comparison is None or comparison.kind == FinancialComparisonKind.NONE:
            continue
        metrics.add(context.metric)
    return metrics


def _fulfillment_state(
    signal: DecisionEvidenceRef,
    support_ref_ids: Sequence[str] | None,
    evidence_by_ref: Mapping[str, DecisionEvidenceRef],
) -> tuple[
    ConfiguredSignalFulfillmentState,
    tuple[str, ...],
    tuple[str, ...],
]:
    if not support_ref_ids:
        return ConfiguredSignalFulfillmentState.CONFIGURED_ONLY, (), ()

    support = tuple(
        evidence_by_ref[ref_id]
        for ref_id in support_ref_ids
        if ref_id in evidence_by_ref
    )
    reasons: list[str] = []
    if len(support) != len(support_ref_ids):
        reasons.append("fulfillment_evidence_ref_missing")
    if any(configured_signal_source_role(ref) is not None for ref in support):
        reasons.append("configured_signal_cannot_self_certify_fulfillment")

    required_groups = _required_financial_metric_groups(signal)
    if not required_groups:
        reasons.append("typed_fulfillment_capability_required")
    safe_metrics = _safe_current_financial_metrics(support)
    for group in required_groups:
        if not safe_metrics.intersection(group):
            reasons.append("required_current_financial_metric_missing")

    if reasons:
        return (
            ConfiguredSignalFulfillmentState.UNKNOWN,
            tuple(support_ref_ids),
            tuple(dict.fromkeys(reasons)),
        )
    return (
        ConfiguredSignalFulfillmentState.FULFILLED_BY_CURRENT_EVIDENCE,
        tuple(support_ref_ids),
        (),
    )


def build_configured_signal_evidence_view(
    *,
    ticker: str,
    supplied_refs: Sequence[DecisionEvidenceRef],
    verified_fulfillment_evidence: Sequence[
        ConfiguredSignalFulfillmentEvidence
    ] = (),
) -> ConfiguredSignalEvidenceView:
    evidence_by_ref = {ref.ref_id: ref for ref in supplied_refs}
    proof_by_signal = {
        proof.signal_ref_id: proof.current_evidence_refs
        for proof in verified_fulfillment_evidence
    }
    if len(proof_by_signal) != len(verified_fulfillment_evidence):
        raise ValueError("duplicate_configured_signal_fulfillment_proof")

    items: list[ConfiguredSignalEvidenceItem] = []
    for ref in supplied_refs:
        role = configured_signal_source_role(ref)
        if role is None:
            continue
        state, support_refs, denial_reasons = _fulfillment_state(
            ref,
            proof_by_signal.get(ref.ref_id),
            evidence_by_ref,
        )
        current_eligible = (
            state == ConfiguredSignalFulfillmentState.FULFILLED_BY_CURRENT_EVIDENCE
        )
        items.append(
            ConfiguredSignalEvidenceItem(
                ref_id=ref.ref_id,
                source_ref=ref.source_ref,
                source_role=role,
                fulfillment_state=state,
                fulfillment_evidence_refs=support_refs,
                fulfillment_denial_reasons=denial_reasons,
                current_directional_driver_eligible=current_eligible,
                future_reevaluation_eligible=role
                in {
                    ConfiguredSignalSourceRole.STRENGTHEN_SIGNAL,
                    ConfiguredSignalSourceRole.WEAKEN_SIGNAL,
                },
                risk_context_eligible=role
                in {
                    ConfiguredSignalSourceRole.WEAKEN_SIGNAL,
                    ConfiguredSignalSourceRole.INVALIDATION_SIGNAL,
                },
                material_anchor_eligible=current_eligible,
                dominant_evidence_eligible=current_eligible,
                current_core_judgment_eligible=current_eligible,
            )
        )

    ordered = tuple(sorted(items, key=lambda item: item.ref_id))
    identity = [item.model_dump(mode="json") for item in ordered]
    return ConfiguredSignalEvidenceView(
        ticker=ticker,
        items=ordered,
        view_sha256=_canonical_sha256(identity),
    )


def configured_signal_model_context(
    view: ConfiguredSignalEvidenceView,
) -> dict[str, dict[str, object]]:
    return {
        item.ref_id: {
            "source_role": item.source_role,
            "fulfillment_state": item.fulfillment_state,
            "current_directional_driver_eligible": (
                item.current_directional_driver_eligible
            ),
            "future_reevaluation_eligible": item.future_reevaluation_eligible,
            "risk_context_eligible": item.risk_context_eligible,
            "material_anchor_eligible": item.material_anchor_eligible,
            "dominant_evidence_eligible": item.dominant_evidence_eligible,
        }
        for item in view.items
    }


def current_directional_ref_ids(
    supplied_refs: Sequence[DecisionEvidenceRef],
    view: ConfiguredSignalEvidenceView,
) -> tuple[str, ...]:
    configured = view.by_ref
    return tuple(
        ref.ref_id
        for ref in supplied_refs
        if ref.ref_id not in configured
        or configured[ref.ref_id].current_directional_driver_eligible
    )


def _field_ref_rows(payload: Mapping[str, object]) -> tuple[tuple[str, str], ...]:
    rows: list[tuple[str, str]] = []
    for field in ("buy_drivers", "sell_drivers"):
        values = payload.get(field)
        if not isinstance(values, Sequence) or isinstance(values, (str, bytes)):
            continue
        for index, value in enumerate(values):
            if not isinstance(value, Mapping):
                continue
            refs = value.get("evidence_refs")
            if isinstance(refs, Sequence) and not isinstance(refs, (str, bytes)):
                rows.extend((f"{field}[{index}]", str(ref)) for ref in refs)

    for field in ("dominant_evidence", "core_investment_judgment"):
        value = payload.get(field)
        if not isinstance(value, Mapping):
            continue
        refs = value.get("evidence_refs")
        if isinstance(refs, Sequence) and not isinstance(refs, (str, bytes)):
            rows.extend((field, str(ref)) for ref in refs)

    anchors = payload.get("material_directional_anchor_basis")
    if isinstance(anchors, Sequence) and not isinstance(anchors, (str, bytes)):
        rows.extend(("material_directional_anchor_basis", str(ref)) for ref in anchors)
    return tuple(rows)


def validate_configured_signal_field_ownership(
    candidate: object,
    view: ConfiguredSignalEvidenceView,
) -> ConfiguredSignalFieldValidation:
    payload = (
        candidate.model_dump(mode="json")
        if hasattr(candidate, "model_dump")
        else candidate
    )
    if not isinstance(payload, Mapping):
        raise TypeError("configured_signal_candidate_mapping_required")
    by_ref = view.by_ref
    violations = tuple(
        ConfiguredSignalFieldViolation(
            field_path=field_path,
            ref_id=ref_id,
            source_role=by_ref[ref_id].source_role,
            fulfillment_state=by_ref[ref_id].fulfillment_state,
        )
        for field_path, ref_id in _field_ref_rows(payload)
        if ref_id in by_ref
        and not by_ref[ref_id].current_directional_driver_eligible
    )
    error = (
        ("configured_future_signal_used_as_current_directional_driver",)
        if violations
        else ()
    )
    return ConfiguredSignalFieldValidation(
        valid=not violations,
        errors=error,
        configured_signal_count=len(view.items),
        configured_only_signal_count=sum(
            item.fulfillment_state
            == ConfiguredSignalFulfillmentState.CONFIGURED_ONLY
            for item in view.items
        ),
        fulfilled_signal_count=sum(
            item.fulfillment_state
            == ConfiguredSignalFulfillmentState.FULFILLED_BY_CURRENT_EVIDENCE
            for item in view.items
        ),
        unknown_fulfillment_signal_count=sum(
            item.fulfillment_state == ConfiguredSignalFulfillmentState.UNKNOWN
            for item in view.items
        ),
        configured_only_current_driver_violation_count=len(violations),
        configured_signal_false_fulfillment_count=0,
        violations=violations,
    )
