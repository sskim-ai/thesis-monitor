from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from enum import StrEnum
from typing import Iterable

from app.config import get_settings
from app.services.adaptive_renderer_selector_service import (
    AdaptiveRenderer,
    AdaptiveRendererResult,
    run_adaptive_renderer,
)
from app.services.free_analyst_natural_packet_adapter_service import (
    NaturalPacketAdapterResult,
    normalize_natural_packet_message,
    validate_natural_packet_adapter_result,
)
from app.services.free_analyst_message_service import parse_rendered_message


CONTRACT_VERSION = "common-ai-core-v1"
CANARY_POLICY_VERSION = "free-analyst-adaptive-canary-v1"


class CommonAIAnalysisMode(StrEnum):
    CURRENT = "current"
    FREE_ANALYST_ADAPTIVE_CANARY = "free_analyst_adaptive_canary"
    FREE_ANALYST_ADAPTIVE = "free_analyst_adaptive"


@dataclass(frozen=True)
class ProductionCandidate:
    contract: str
    message_key: str
    market: str
    is_market_digest: bool
    source_text: str
    deterministic_text: str
    adapter: NaturalPacketAdapterResult | None
    result: AdaptiveRendererResult | None
    eligible: bool
    hard_validation: str
    errors: tuple[str, ...]

    @property
    def selected_renderer(self) -> AdaptiveRenderer | None:
        if self.result is None or self.result.decision is None:
            return None
        return self.result.decision.selected_renderer

    @property
    def renderer_selection_reasons(self) -> tuple[str, ...]:
        if self.result is None or self.result.decision is None:
            return ()
        return self.result.decision.selection_reasons

    @property
    def candidate_text(self) -> str:
        if self.eligible and self.result is not None:
            return self.result.final_text
        return self.deterministic_text

    def to_dict(self) -> dict[str, object]:
        return {
            "contract": self.contract,
            "message_key": self.message_key,
            "market": self.market,
            "is_market_digest": self.is_market_digest,
            "adapter": self.adapter.to_dict() if self.adapter else None,
            "result": self.result.to_dict() if self.result else None,
            "eligible": self.eligible,
            "hard_validation": self.hard_validation,
            "errors": list(self.errors),
            "selected_renderer": self.selected_renderer,
            "renderer_selection_reasons": list(self.renderer_selection_reasons),
        }


@dataclass(frozen=True)
class CanarySelectionRow:
    message_key: str
    canary_candidate: bool
    canary_selected: bool
    selection_reason: str
    final_simulated_delivery_mode: str


@dataclass(frozen=True)
class CanarySelection:
    contract: str
    policy_version: str
    selected_keys: tuple[str, ...]
    rows: tuple[CanarySelectionRow, ...]
    market_selected: int
    stock_selected: int
    total_selected: int

    def row_for(self, message_key: str) -> CanarySelectionRow:
        return next(row for row in self.rows if row.message_key == message_key)

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def configured_analysis_mode() -> CommonAIAnalysisMode:
    raw = get_settings().free_analyst_adaptive_mode
    return CommonAIAnalysisMode(raw)


def free_analyst_adaptive_kill_switch_open() -> bool:
    settings = get_settings()
    return bool(
        settings.free_analyst_adaptive_enabled
        and configured_analysis_mode() != CommonAIAnalysisMode.CURRENT
    )


def free_analyst_adaptive_canary_armed() -> bool:
    settings = get_settings()
    return bool(
        free_analyst_adaptive_kill_switch_open()
        and configured_analysis_mode() == CommonAIAnalysisMode.FREE_ANALYST_ADAPTIVE_CANARY
        and settings.ai_review_pilot_enabled
    )


def _hard_safety_errors(result: AdaptiveRendererResult) -> tuple[str, ...]:
    safety = result.safety
    errors: list[str] = []
    if result.status != "PASS":
        errors.append(result.fallback_reason or "adaptive_renderer_failed")
    if result.synthesis_validation.get("status") != "PASS":
        errors.append("synthesis_validation_failed")
    if safety.get("status") != "PASS":
        errors.append("adaptive_safety_failed")
    count_keys = (
        "fact_mismatch",
        "unsupported_causality",
        "temporal_violations",
        "trade_ar_leak",
        "hidden_arithmetic",
        "external_knowledge",
        "material_information_loss",
    )
    for key in count_keys:
        if int(safety.get(key) or 0):
            errors.append(key)
    if safety.get("unsupported_numeric_claims"):
        errors.append("unsupported_numeric_claims")
    return tuple(dict.fromkeys(errors))


def _preserve_required_stock_sections(
    result: AdaptiveRendererResult,
    *,
    source_text: str,
    market: str,
    is_market_digest: bool,
) -> AdaptiveRendererResult:
    if is_market_digest or result.rendered is None:
        return result
    expected_heading = "📊 거래량·포지셔닝" if market == "us" else "📊 수급"
    if expected_heading in result.final_text:
        return result
    supply = next(
        (
            section
            for section in parse_rendered_message(source_text).sections
            if section.key == "supply"
        ),
        None,
    )
    if supply is None:
        return result
    if "📊 포지셔닝" in result.final_text and supply.body in result.final_text:
        text = result.final_text.replace("📊 포지셔닝", expected_heading, 1)
    else:
        text = f"{result.final_text.rstrip()}\n\n{expected_heading}\n{supply.body}"
    return replace(result, rendered=replace(result.rendered, text=text), final_text=text)


def build_production_candidate(
    source_text: str,
    *,
    deterministic_text: str,
    message_key: str,
    market: str,
    is_market_digest: bool = False,
) -> ProductionCandidate:
    """Build one fail-closed candidate without delivery or persistence side effects."""
    try:
        adapter = normalize_natural_packet_message(
            source_text,
            benchmark_id=message_key,
            market=market,
        )
    except (TypeError, ValueError) as exc:
        return ProductionCandidate(
            contract=CONTRACT_VERSION,
            message_key=message_key,
            market=market,
            is_market_digest=is_market_digest,
            source_text=source_text,
            deterministic_text=deterministic_text,
            adapter=None,
            result=None,
            eligible=False,
            hard_validation="FAIL",
            errors=(f"natural_packet_adapter_error:{type(exc).__name__}",),
        )
    adapter_errors = validate_natural_packet_adapter_result(adapter)
    if adapter_errors:
        return ProductionCandidate(
            contract=CONTRACT_VERSION,
            message_key=message_key,
            market=market,
            is_market_digest=is_market_digest,
            source_text=source_text,
            deterministic_text=deterministic_text,
            adapter=adapter,
            result=None,
            eligible=False,
            hard_validation="FAIL",
            errors=adapter_errors,
        )
    try:
        result = run_adaptive_renderer(
            adapter.normalized_text,
            benchmark_id=message_key,
            deterministic_reference=deterministic_text,
        )
    except (LookupError, RuntimeError, TypeError, ValueError) as exc:
        return ProductionCandidate(
            contract=CONTRACT_VERSION,
            message_key=message_key,
            market=market,
            is_market_digest=is_market_digest,
            source_text=source_text,
            deterministic_text=deterministic_text,
            adapter=adapter,
            result=None,
            eligible=False,
            hard_validation="FAIL",
            errors=(f"adaptive_renderer_error:{type(exc).__name__}",),
        )
    result = _preserve_required_stock_sections(
        result,
        source_text=adapter.normalized_text,
        market=market,
        is_market_digest=is_market_digest,
    )
    errors = _hard_safety_errors(result)
    return ProductionCandidate(
        contract=CONTRACT_VERSION,
        message_key=message_key,
        market=market,
        is_market_digest=is_market_digest,
        source_text=source_text,
        deterministic_text=deterministic_text,
        adapter=adapter,
        result=result,
        eligible=not errors,
        hard_validation="PASS" if not errors else "FAIL",
        errors=errors,
    )


def _candidate_rank(candidate: ProductionCandidate) -> tuple[int, int, str]:
    renderer_rank = {
        AdaptiveRenderer.DIRECT_ANALYST: 3,
        AdaptiveRenderer.CONCISE_HYBRID: 2,
        AdaptiveRenderer.MINIMAL_VNEXT: 1,
        None: 0,
    }[candidate.selected_renderer]
    analysis_items = (
        len(candidate.result.analysis.analysis_items()) if candidate.result is not None else 0
    )
    return (-renderer_rank, -analysis_items, candidate.message_key)


def select_limited_canary(
    candidates: Iterable[ProductionCandidate],
    *,
    max_market: int = 1,
    max_stock: int = 2,
    max_total: int = 3,
) -> CanarySelection:
    if min(max_market, max_stock, max_total) < 0:
        raise ValueError("canary limits must be non-negative")
    rows = list(candidates)
    eligible_market = sorted(
        (row for row in rows if row.eligible and row.is_market_digest),
        key=_candidate_rank,
    )
    eligible_stock = sorted(
        (row for row in rows if row.eligible and not row.is_market_digest),
        key=_candidate_rank,
    )
    selected: list[ProductionCandidate] = eligible_market[: min(max_market, max_total)]
    remaining = max(0, max_total - len(selected))
    stock_limit = min(max_stock, remaining)

    selected_renderers: set[AdaptiveRenderer | None] = set()
    stock_selected: list[ProductionCandidate] = []
    for candidate in eligible_stock:
        if len(stock_selected) >= stock_limit:
            break
        if candidate.selected_renderer in selected_renderers:
            continue
        stock_selected.append(candidate)
        selected_renderers.add(candidate.selected_renderer)
    for candidate in eligible_stock:
        if len(stock_selected) >= stock_limit:
            break
        if candidate in stock_selected:
            continue
        stock_selected.append(candidate)
    selected.extend(stock_selected)
    selected_keys = tuple(row.message_key for row in selected)
    selected_set = set(selected_keys)

    audit_rows: list[CanarySelectionRow] = []
    for candidate in rows:
        is_selected = candidate.message_key in selected_set
        if is_selected:
            reason = "validated_material_candidate_within_canary_limits"
            mode = "free_analyst_adaptive_canary"
        elif not candidate.eligible:
            reason = "candidate_failed_fail_closed_gate"
            mode = "deterministic_fallback"
        else:
            reason = "eligible_not_selected_within_canary_limits"
            mode = "current_ai_existing"
        audit_rows.append(
            CanarySelectionRow(
                message_key=candidate.message_key,
                canary_candidate=candidate.eligible,
                canary_selected=is_selected,
                selection_reason=reason,
                final_simulated_delivery_mode=mode,
            )
        )
    return CanarySelection(
        contract=CONTRACT_VERSION,
        policy_version=CANARY_POLICY_VERSION,
        selected_keys=selected_keys,
        rows=tuple(audit_rows),
        market_selected=sum(row.is_market_digest for row in selected),
        stock_selected=sum(not row.is_market_digest for row in selected),
        total_selected=len(selected),
    )


def restrict_canary_selection(
    selection: CanarySelection,
    permitted_keys: Iterable[str],
    *,
    rejection_reason: str = "runtime_quality_fail_closed",
) -> CanarySelection:
    permitted = set(permitted_keys)
    selected = tuple(key for key in selection.selected_keys if key in permitted)
    selected_set = set(selected)
    rows: list[CanarySelectionRow] = []
    for row in selection.rows:
        if row.message_key in selected_set:
            rows.append(row)
        elif row.canary_selected:
            rows.append(
                CanarySelectionRow(
                    message_key=row.message_key,
                    canary_candidate=row.canary_candidate,
                    canary_selected=False,
                    selection_reason=rejection_reason,
                    final_simulated_delivery_mode="deterministic_fallback",
                )
            )
        else:
            rows.append(row)
    market_keys = {
        row.message_key
        for row in selection.rows
        if row.canary_selected and row.message_key.startswith("market:")
    }
    market_selected = len(selected_set.intersection(market_keys))
    return CanarySelection(
        contract=selection.contract,
        policy_version=selection.policy_version,
        selected_keys=selected,
        rows=tuple(rows),
        market_selected=market_selected,
        stock_selected=len(selected) - market_selected,
        total_selected=len(selected),
    )


def fail_closed_canary_selection(
    selection: CanarySelection,
    *,
    reason: str = "runtime_quality_set_failed",
) -> CanarySelection:
    return CanarySelection(
        contract=selection.contract,
        policy_version=selection.policy_version,
        selected_keys=(),
        rows=tuple(
            CanarySelectionRow(
                message_key=row.message_key,
                canary_candidate=row.canary_candidate,
                canary_selected=False,
                selection_reason=reason,
                final_simulated_delivery_mode="deterministic_fallback",
            )
            for row in selection.rows
        ),
        market_selected=0,
        stock_selected=0,
        total_selected=0,
    )


def candidate_provenance(
    candidate: ProductionCandidate,
    selection: CanarySelection,
) -> dict[str, object]:
    row = selection.row_for(candidate.message_key)
    return {
        "analysis_mode": CommonAIAnalysisMode.FREE_ANALYST_ADAPTIVE_CANARY,
        "free_analyst_generated": candidate.result is not None,
        "free_analyst_validation": (
            candidate.result.synthesis_validation.get("status")
            if candidate.result is not None
            else "FAIL"
        ),
        "selected_renderer": candidate.selected_renderer,
        "renderer_selection_reasons": list(candidate.renderer_selection_reasons),
        "hard_validation": candidate.hard_validation,
        "fallback_reason": (None if row.canary_selected else row.selection_reason),
        "final_delivery_mode": row.final_simulated_delivery_mode,
        "canary_candidate": row.canary_candidate,
        "canary_selected": row.canary_selected,
        "selection_reason": row.selection_reason,
    }
