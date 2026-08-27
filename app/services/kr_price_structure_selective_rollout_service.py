from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from enum import StrEnum

from app.config import get_settings
from app.services.price_structure_v3_family_consensus_service import (
    apply_family_consensus_feedback,
)
from app.services.price_structure_v3_renderer_service import (
    PriceStructureRender,
    classify_user_visible_sr,
    render_current_price_structure,
    validate_price_structure_render,
)
from app.services.price_structure_wave_fibonacci_v3_service import (
    WaveHypothesisSelection,
    WaveSelectionStatus,
    build_price_structure_wave_fib_v3,
)


CONTRACT_VERSION = "kr-price-structure-selective-rollout-v1"
RUNTIME_CONTEXT_VERSION = "kr-price-structure-runtime-context-v1"


class KrPriceStructureEligibility(StrEnum):
    ELIGIBLE = "ELIGIBLE"
    ELIGIBLE_SR_ONLY = "ELIGIBLE_SR_ONLY"
    OMIT_PRICE_STRUCTURE = "OMIT_PRICE_STRUCTURE"
    BLOCKED = "BLOCKED"


@dataclass(frozen=True)
class KrPriceStructureRolloutDecision:
    contract: str
    ticker: str
    market: str
    enabled: bool
    monitored_subject: bool
    eligibility: KrPriceStructureEligibility
    section: str | None
    numeric_bindings: tuple[dict[str, object], ...]
    displayed_zone_ids: tuple[str, ...]
    denial_reasons: tuple[str, ...]
    render_validation_errors: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _zone(selection: object) -> Mapping[str, object] | None:
    return_value = _mapping(selection).get("zone")
    return return_value if isinstance(return_value, Mapping) else None


def classify_kr_price_structure(
    context: Mapping[str, object],
) -> KrPriceStructureEligibility:
    selection_errors = context.get("selection_errors")
    if isinstance(selection_errors, Sequence) and not isinstance(
        selection_errors, (str, bytes)
    ) and selection_errors:
        return KrPriceStructureEligibility.BLOCKED
    if int(context.get("partial_bar_used_for_pivot_confirmation") or 0):
        return KrPriceStructureEligibility.BLOCKED
    coverage = _mapping(context.get("coverage"))
    if coverage and not any(
        _mapping(value).get("status") in {"PASS", "PARTIAL"}
        and int(_mapping(value).get("completed_count") or 0) > 0
        for value in coverage.values()
    ):
        return KrPriceStructureEligibility.BLOCKED
    summary = _mapping(context.get("summary"))
    visible_zones = [
        zone
        for key in (
            "nearest_support",
            "nearest_resistance",
            "major_structural_support",
            "major_structural_resistance",
        )
        if (zone := _zone(summary.get(key))) is not None
        and classify_user_visible_sr(zone) != "OMIT"
    ]
    if not visible_zones:
        return KrPriceStructureEligibility.OMIT_PRICE_STRUCTURE
    has_safe_fib = bool(
        context.get("family_consensus_safe") is True
        and isinstance(summary.get("fib_sr_confluence"), Mapping)
        and summary.get("fib_sr_confluence_state")
        in {"DIRECT_SR_CONFLUENCE", "NEAR_SR_CONFLUENCE"}
    )
    return (
        KrPriceStructureEligibility.ELIGIBLE
        if has_safe_fib
        else KrPriceStructureEligibility.ELIGIBLE_SR_ONLY
    )


def _summary_for_render(
    context: Mapping[str, object],
    eligibility: KrPriceStructureEligibility,
) -> dict[str, object]:
    summary = dict(_mapping(context.get("summary")))
    if eligibility == KrPriceStructureEligibility.ELIGIBLE_SR_ONLY:
        summary["fib_sr_confluence"] = None
        summary["fib_sr_confluence_state"] = "NO_FAMILY_STABLE_CONFLUENCE"
    return summary


def build_kr_price_structure_rollout_decision(
    context: Mapping[str, object],
    *,
    ticker: str,
    monitored_subject: bool,
    enabled: bool | None = None,
) -> KrPriceStructureRolloutDecision:
    market = str(context.get("market") or ("KR" if ticker.isdigit() else "US"))
    effective_enabled = (
        get_settings().kr_price_structure_v3_enabled
        if enabled is None
        else enabled
    )
    reasons: list[str] = []
    if market != "KR" or not ticker.isdigit():
        reasons.append("kr_market_scope_required")
    if not monitored_subject:
        reasons.append("subject_outside_monitored_kr_universe")
    eligibility = classify_kr_price_structure(context)
    if eligibility == KrPriceStructureEligibility.BLOCKED:
        reasons.append("price_structure_validation_blocked")
    elif eligibility == KrPriceStructureEligibility.OMIT_PRICE_STRUCTURE:
        reasons.append("no_safe_current_sr")
    if not effective_enabled:
        reasons.append("kr_price_structure_rollout_disabled")
    if reasons:
        return KrPriceStructureRolloutDecision(
            contract=CONTRACT_VERSION,
            ticker=ticker,
            market=market,
            enabled=effective_enabled,
            monitored_subject=monitored_subject,
            eligibility=eligibility,
            section=None,
            numeric_bindings=(),
            displayed_zone_ids=(),
            denial_reasons=tuple(reasons),
            render_validation_errors=(),
        )

    render: PriceStructureRender = render_current_price_structure(
        _summary_for_render(context, eligibility),
        ticker=ticker,
        as_of=str(context.get("as_of") or ""),
        current_price=context.get("current_price"),
        currency=str(context.get("currency") or "KRW"),
        include_current_price=True,
    )
    validation = validate_price_structure_render(render)
    if validation.status == "FAIL":
        return KrPriceStructureRolloutDecision(
            contract=CONTRACT_VERSION,
            ticker=ticker,
            market=market,
            enabled=effective_enabled,
            monitored_subject=monitored_subject,
            eligibility=KrPriceStructureEligibility.BLOCKED,
            section=None,
            numeric_bindings=(),
            displayed_zone_ids=(),
            denial_reasons=("price_structure_render_validation_failed",),
            render_validation_errors=validation.errors,
        )
    return KrPriceStructureRolloutDecision(
        contract=CONTRACT_VERSION,
        ticker=ticker,
        market=market,
        enabled=effective_enabled,
        monitored_subject=monitored_subject,
        eligibility=eligibility,
        section=render.section,
        numeric_bindings=render.numeric_bindings,
        displayed_zone_ids=render.displayed_zone_ids,
        denial_reasons=(),
        render_validation_errors=(),
    )


def build_kr_price_structure_runtime_context(
    *,
    ticker: str,
    cutoff: str,
    raw_by_timeframe: Mapping[str, Sequence[Mapping[str, object]]],
    observed_at: str,
    provider_limit: int,
) -> dict[str, object]:
    result = build_price_structure_wave_fib_v3(
        ticker=ticker,
        security_id=f"KR:{ticker}",
        market="KR",
        currency="KRW",
        adjustment_basis="provider_adjusted_price_v1",
        cutoff=cutoff,
        raw_by_timeframe=raw_by_timeframe,  # type: ignore[arg-type]
        observed_at=observed_at,
        provider_limit=provider_limit,
    )
    current_cycle = tuple(
        item
        for item in result.primary_monthly_hypotheses
        if item.source_degree == "PRIMARY_CURRENT_CYCLE"
    )
    candidate_ids = tuple(sorted(item.hypothesis_id for item in current_cycle))
    evidence_refs = tuple(
        dict.fromkeys(
            point.pivot_ref
            for hypothesis in current_cycle
            for point in hypothesis.endpoints
        )
    )[:16]
    if len(current_cycle) == 1:
        selected = current_cycle[0]
        selection = WaveHypothesisSelection(
            status=WaveSelectionStatus.SELECTED,
            hypothesis_id=selected.hypothesis_id,
            confidence="MEDIUM",
            reason_categories=("DETERMINISTIC_CURRENT_CYCLE",),
            evidence_refs=evidence_refs,
            endpoint_refs=tuple(point.pivot_ref for point in selected.endpoints),
            concise_reason="single deterministic current-cycle hypothesis",
            ticker=ticker,
            source_degree=selected.source_degree,
            cutoff=cutoff,
            adjustment_basis="provider_adjusted_price_v1",
        )
    elif 2 <= len(current_cycle) <= 3:
        selection = WaveHypothesisSelection(
            status=WaveSelectionStatus.AMBIGUOUS,
            competing_hypothesis_ids=candidate_ids,
            confidence="LOW",
            reason_categories=("DETERMINISTIC_CURRENT_CYCLE_SET",),
            evidence_refs=evidence_refs,
            concise_reason="all bounded current-cycle hypotheses require family consensus",
            ticker=ticker,
            source_degree=current_cycle[0].source_degree,
            cutoff=cutoff,
            adjustment_basis="provider_adjusted_price_v1",
        )
    else:
        selection = WaveHypothesisSelection(
            status=WaveSelectionStatus.INSUFFICIENT_STRUCTURE,
            confidence="LOW",
            reason_categories=("UNBOUNDED_OR_MISSING_CURRENT_CYCLE_SET",),
            evidence_refs=evidence_refs,
            concise_reason="Fib suppressed; deterministic SR remains available",
            ticker=ticker,
            cutoff=cutoff,
            adjustment_basis="provider_adjusted_price_v1",
        )
    safe_result = apply_family_consensus_feedback(result, (selection,))
    if safe_result.sr_base_layer is None:
        summary: dict[str, object] = {}
    else:
        summary = safe_result.sr_base_layer.summary.model_dump(mode="json")
    audit = _mapping(safe_result.family_consensus_audit)
    selection_errors = audit.get("selection_validation_errors")
    errors = (
        [str(value) for value in selection_errors]
        if isinstance(selection_errors, list)
        else []
    )
    context: dict[str, object] = {
        "contract": RUNTIME_CONTEXT_VERSION,
        "source_contract": safe_result.contract,
        "ticker": ticker,
        "market": "KR",
        "as_of": safe_result.as_of,
        "current_price": str(safe_result.current_price),
        "currency": safe_result.currency,
        "summary": summary,
        "selection_errors": errors,
        "partial_bar_used_for_pivot_confirmation": 0,
        "family_consensus_safe": bool(safe_result.fibonacci),
        "family_consensus_audit": safe_result.family_consensus_audit,
        "coverage": {
            timeframe: value.model_dump(mode="json")
            for timeframe, value in safe_result.coverage.items()
        },
    }
    context["eligibility"] = classify_kr_price_structure(context).value
    return context


_CURRENT_SECTION = re.compile(
    r"(?:^|\n\n)(?P<section>📐 현재 가격 구조\n.*?)(?=\n\n(?:📊 |🧭 |📐 Valuation|⚠️ |📌 )|\Z)",
    re.DOTALL,
)
_LEGACY_PRICE_SECTION = re.compile(
    r"(?:^|\n\n)(?P<section>💰[^\n]*\n.*?)(?=\n\n(?:📈 |🚨 |⚠️ |👁 |📍 |📊 |🧭 |📐 |📌 )|\Z)",
    re.DOTALL,
)


def extract_current_price_structure_section(message: str) -> str | None:
    match = _CURRENT_SECTION.search(message)
    return match.group("section").strip() if match else None


def apply_current_price_structure_section(message: str, section: str) -> str:
    if existing := _CURRENT_SECTION.search(message):
        start, end = existing.span("section")
        return message[:start] + section.strip() + message[end:]
    for marker in ("\n\n📊 수급", "\n\n🧭 기존 등록 가격 규칙", "\n\n📐 Valuation", "\n\n📌 다음 확인"):
        index = message.find(marker)
        if index >= 0:
            return message[:index].rstrip() + "\n\n" + section.strip() + message[index:]
    return message.rstrip() + "\n\n" + section.strip()


def replace_legacy_price_surface(message: str, section: str) -> str:
    match = _LEGACY_PRICE_SECTION.search(message)
    if match is None:
        return apply_current_price_structure_section(message, section)
    legacy = match.group("section")
    stored_match = re.search(r"가격 규칙 이력:\n(?P<body>.*)\Z", legacy, re.DOTALL)
    stored_section = ""
    if stored_match:
        stored_lines = [
            line.replace("• 등록 확인선 ", "• 기존 확인선 ", 1)
            for line in stored_match.group("body").splitlines()
            if line.strip()
        ]
        if stored_lines:
            stored_section = "\n\n" + "\n".join(
                ("🧭 기존 등록 가격 규칙", *stored_lines)
            )
    start, end = match.span("section")
    replacement = section.strip() + stored_section
    return message[:start] + replacement + message[end:]


def preserve_current_price_structure_section(
    message: str,
    reference: str,
) -> str:
    section = extract_current_price_structure_section(reference)
    return replace_legacy_price_surface(message, section) if section else message
