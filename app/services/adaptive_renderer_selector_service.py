from __future__ import annotations

from collections.abc import Callable
from dataclasses import asdict, dataclass
from enum import StrEnum

from app.services.free_analyst_message_service import (
    build_minimal_vnext_message,
    factual_parity_report,
)
from app.services.evidence_locked_free_analyst_service import (
    FreeAnalystAnalysis,
    InferenceRule,
    RenderedFreeAnalyst,
    build_free_analyst_analysis,
    render_free_analyst_direct,
    render_free_analyst_vnext_hybrid,
    rendered_safety_report,
    validate_free_analyst_analysis,
)


CONTRACT_VERSION = "adaptive-renderer-selector-v1"


class AdaptiveRenderer(StrEnum):
    DIRECT_ANALYST = "DIRECT_ANALYST"
    CONCISE_HYBRID = "CONCISE_HYBRID"
    MINIMAL_VNEXT = "MINIMAL_VNEXT"


class InformationElement(StrEnum):
    PRIMARY_CONCLUSION = "primary_conclusion"
    THESIS_LINKAGE = "thesis_linkage"
    ALTERNATIVE_INTERPRETATION = "alternative_interpretation"
    UNCERTAINTY_BOUNDARY = "uncertainty_boundary"
    EXPECTATION_VALUATION = "expectation_valuation"
    POSITIONING_SYNTHESIS = "positioning_synthesis"
    NEXT_CHECK = "next_check"
    MATERIAL_WARNING = "material_warning"


@dataclass(frozen=True)
class RendererInformationAudit:
    renderer: AdaptiveRenderer
    retained_elements: tuple[InformationElement, ...]
    dropped_elements: tuple[InformationElement, ...]
    material_dropped_elements: tuple[InformationElement, ...]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class SelectorDecision:
    contract: str
    benchmark_id: str
    selected_renderer: AdaptiveRenderer
    eligible_renderers: tuple[AdaptiveRenderer, ...]
    disallowed_renderers: tuple[AdaptiveRenderer, ...]
    selection_reasons: tuple[str, ...]
    direct_required_reasons: tuple[str, ...]
    minimal_forbidden_reasons: tuple[str, ...]
    expected_information_loss: tuple[InformationElement, ...]
    information_audits: tuple[RendererInformationAudit, ...]

    def audit_for(self, renderer: AdaptiveRenderer) -> RendererInformationAudit:
        return next(row for row in self.information_audits if row.renderer == renderer)

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class AdaptiveRendererResult:
    contract: str
    benchmark_id: str
    status: str
    analysis: FreeAnalystAnalysis
    synthesis_validation: dict[str, object]
    decision: SelectorDecision | None
    rendered: RenderedFreeAnalyst | None
    final_text: str
    final_delivery_mode: str
    fallback_reason: str | None
    safety: dict[str, object]

    def to_dict(self) -> dict[str, object]:
        return {
            "contract": self.contract,
            "benchmark_id": self.benchmark_id,
            "status": self.status,
            "analysis": self.analysis.to_dict(),
            "synthesis_validation": self.synthesis_validation,
            "decision": self.decision.to_dict() if self.decision else None,
            "rendered": (
                {
                    "renderer": self.rendered.renderer,
                    "text": self.rendered.text,
                    "sentence_supports": [asdict(row) for row in self.rendered.sentence_supports],
                }
                if self.rendered
                else None
            ),
            "final_text": self.final_text,
            "final_delivery_mode": self.final_delivery_mode,
            "fallback_reason": self.fallback_reason,
            "safety": self.safety,
        }


Selector = Callable[[FreeAnalystAnalysis, str], SelectorDecision]
Renderer = Callable[[str, FreeAnalystAnalysis, AdaptiveRenderer], RenderedFreeAnalyst]


def _normalized(value: str) -> str:
    return " ".join(value.casefold().strip().rstrip(".!?").split())


def _low_information_shape(analysis: FreeAnalystAnalysis) -> bool:
    return bool(
        analysis.top_findings
        and analysis.top_findings[0].rule_id == InferenceRule.TEMPORAL_EVIDENCE_BOUNDARY
        and not analysis.thesis_implications
        and not analysis.alternative_interpretations
        and not analysis.expectation_valuation_interaction
        and not analysis.positioning_synthesis
        and not analysis.unknowns
    )


def _unique_material_warning(analysis: FreeAnalystAnalysis) -> bool:
    if "warning" not in analysis.message_plan.selected_blocks:
        return False
    next_checks = {_normalized(row.check) for row in analysis.next_checks}
    return any(_normalized(row.unresolved_question) not in next_checks for row in analysis.unknowns)


def _available_elements(
    analysis: FreeAnalystAnalysis,
) -> dict[InformationElement, bool]:
    return {
        InformationElement.PRIMARY_CONCLUSION: bool(analysis.top_findings),
        InformationElement.THESIS_LINKAGE: bool(analysis.thesis_implications),
        InformationElement.ALTERNATIVE_INTERPRETATION: bool(analysis.alternative_interpretations),
        InformationElement.UNCERTAINTY_BOUNDARY: any(
            item.boundary for item in analysis.analysis_items()
        ),
        InformationElement.EXPECTATION_VALUATION: bool(analysis.expectation_valuation_interaction),
        InformationElement.POSITIONING_SYNTHESIS: bool(analysis.positioning_synthesis),
        InformationElement.NEXT_CHECK: bool(analysis.next_checks),
        InformationElement.MATERIAL_WARNING: _unique_material_warning(analysis),
    }


def _material_elements(
    analysis: FreeAnalystAnalysis,
) -> dict[InformationElement, bool]:
    available = _available_elements(analysis)
    positioning_is_primary = bool(
        analysis.positioning_synthesis
        and not analysis.thesis_implications
        and not analysis.alternative_interpretations
        and not analysis.expectation_valuation_interaction
    )
    return {
        InformationElement.PRIMARY_CONCLUSION: available[InformationElement.PRIMARY_CONCLUSION],
        InformationElement.THESIS_LINKAGE: available[InformationElement.THESIS_LINKAGE],
        InformationElement.ALTERNATIVE_INTERPRETATION: available[
            InformationElement.ALTERNATIVE_INTERPRETATION
        ],
        InformationElement.UNCERTAINTY_BOUNDARY: available[InformationElement.UNCERTAINTY_BOUNDARY],
        InformationElement.EXPECTATION_VALUATION: available[
            InformationElement.EXPECTATION_VALUATION
        ],
        InformationElement.POSITIONING_SYNTHESIS: positioning_is_primary,
        InformationElement.NEXT_CHECK: available[InformationElement.NEXT_CHECK],
        InformationElement.MATERIAL_WARNING: available[InformationElement.MATERIAL_WARNING],
    }


def _support_retention(
    analysis: FreeAnalystAnalysis,
    rendered: RenderedFreeAnalyst,
) -> dict[InformationElement, bool]:
    support_ids = {row.analysis_item_id for row in rendered.sentence_supports}
    primary_id = analysis.top_findings[0].item_id if analysis.top_findings else ""
    retained_items = {
        item.item_id: item for item in analysis.analysis_items() if item.item_id in support_ids
    }
    thesis_linkage_retained = any(
        item.item_id in support_ids for item in analysis.thesis_implications
    ) or any(
        retained.rule_id == thesis.rule_id
        and bool(set(retained.evidence_refs).intersection(thesis.evidence_refs))
        for retained in retained_items.values()
        for thesis in analysis.thesis_implications
    )
    alternative_retained = all(
        row.negative_interpretation.item_id in support_ids
        and (
            row.positive_interpretation.item_id in support_ids
            or row.positive_interpretation.item_id == primary_id
            and primary_id in support_ids
        )
        for row in analysis.alternative_interpretations
    )
    boundary_ids = {item.item_id for item in analysis.analysis_items() if item.boundary}
    return {
        InformationElement.PRIMARY_CONCLUSION: primary_id in support_ids,
        InformationElement.THESIS_LINKAGE: thesis_linkage_retained,
        InformationElement.ALTERNATIVE_INTERPRETATION: alternative_retained,
        InformationElement.UNCERTAINTY_BOUNDARY: bool(boundary_ids.intersection(support_ids)),
        InformationElement.EXPECTATION_VALUATION: any(
            item.item_id in support_ids for item in analysis.expectation_valuation_interaction
        ),
        InformationElement.POSITIONING_SYNTHESIS: any(
            item.item_id in support_ids for item in analysis.positioning_synthesis
        ),
        InformationElement.NEXT_CHECK: "next-check" in support_ids,
        InformationElement.MATERIAL_WARNING: False,
    }


def _minimal_retention(
    analysis: FreeAnalystAnalysis,
    minimal_text: str,
) -> dict[InformationElement, bool]:
    low_information = _low_information_shape(analysis)
    next_retained = any(row.check in minimal_text for row in analysis.next_checks)
    return {
        InformationElement.PRIMARY_CONCLUSION: low_information and bool(minimal_text),
        InformationElement.THESIS_LINKAGE: False,
        InformationElement.ALTERNATIVE_INTERPRETATION: False,
        InformationElement.UNCERTAINTY_BOUNDARY: low_information
        and any(marker in minimal_text for marker in ("신규 관측", "확정", "승격")),
        InformationElement.EXPECTATION_VALUATION: False,
        InformationElement.POSITIONING_SYNTHESIS: False,
        InformationElement.NEXT_CHECK: next_retained,
        InformationElement.MATERIAL_WARNING: False,
    }


def renderer_information_audit(
    current_ai_text: str,
    analysis: FreeAnalystAnalysis,
    renderer: AdaptiveRenderer,
) -> RendererInformationAudit:
    available = _available_elements(analysis)
    material = _material_elements(analysis)
    if renderer == AdaptiveRenderer.DIRECT_ANALYST:
        retained = _support_retention(analysis, render_free_analyst_direct(analysis))
    elif renderer == AdaptiveRenderer.CONCISE_HYBRID:
        retained = _support_retention(analysis, render_free_analyst_vnext_hybrid(analysis))
    else:
        retained = _minimal_retention(analysis, build_minimal_vnext_message(current_ai_text).text)
    retained_elements = tuple(
        element for element, exists in available.items() if exists and retained[element]
    )
    dropped_elements = tuple(
        element for element, exists in available.items() if exists and not retained[element]
    )
    material_dropped = tuple(element for element in dropped_elements if material[element])
    return RendererInformationAudit(
        renderer=renderer,
        retained_elements=retained_elements,
        dropped_elements=dropped_elements,
        material_dropped_elements=material_dropped,
    )


def select_adaptive_renderer(
    analysis: FreeAnalystAnalysis,
    current_ai_text: str,
) -> SelectorDecision:
    validation = validate_free_analyst_analysis(analysis)
    if validation.status != "PASS":
        raise ValueError("selector requires a validated Free Analyst object")

    audits = tuple(
        renderer_information_audit(current_ai_text, analysis, renderer)
        for renderer in AdaptiveRenderer
    )
    by_renderer = {row.renderer: row for row in audits}
    direct_reasons: list[str] = []
    if analysis.alternative_interpretations:
        direct_reasons.append("material_alternative_interpretation")
    if len(analysis.thesis_implications) > 1:
        direct_reasons.append("multiple_material_thesis_implications")
    if by_renderer[AdaptiveRenderer.CONCISE_HYBRID].material_dropped_elements:
        direct_reasons.append("hybrid_would_drop_material_boundary")

    minimal_forbidden: list[str] = []
    if analysis.thesis_implications:
        minimal_forbidden.append("meaningful_thesis_linkage")
    if analysis.alternative_interpretations:
        minimal_forbidden.append("material_ambiguity")
    if analysis.expectation_valuation_interaction:
        minimal_forbidden.append("expectation_verification_threshold")
    if analysis.positioning_synthesis:
        minimal_forbidden.append("cross_horizon_positioning_context")
    if analysis.top_findings and not _low_information_shape(analysis):
        minimal_forbidden.append("novel_supported_synthesis")

    if direct_reasons:
        selected = AdaptiveRenderer.DIRECT_ANALYST
        reasons = ("direct_required_to_preserve_analysis_balance", *direct_reasons)
    elif (
        _low_information_shape(analysis)
        and not by_renderer[AdaptiveRenderer.MINIMAL_VNEXT].material_dropped_elements
    ):
        selected = AdaptiveRenderer.MINIMAL_VNEXT
        reasons = (
            "reference_only_temporal_state",
            "no_material_synthesis_beyond_safe_source_boundary",
        )
    elif not by_renderer[AdaptiveRenderer.CONCISE_HYBRID].material_dropped_elements:
        selected = AdaptiveRenderer.CONCISE_HYBRID
        reasons = (
            "single_clear_primary_conclusion",
            "material_boundary_preserved_in_concise_form",
            "clear_next_check",
        )
    else:
        selected = AdaptiveRenderer.DIRECT_ANALYST
        reasons = ("direct_required_to_preserve_material_boundary",)

    selected_audit = by_renderer[selected]
    if selected_audit.material_dropped_elements:
        raise ValueError("selected renderer would drop material information")

    eligible: list[AdaptiveRenderer] = []
    for renderer in AdaptiveRenderer:
        audit = by_renderer[renderer]
        if audit.material_dropped_elements:
            continue
        if renderer == AdaptiveRenderer.MINIMAL_VNEXT and minimal_forbidden:
            continue
        if renderer == AdaptiveRenderer.CONCISE_HYBRID and direct_reasons:
            continue
        eligible.append(renderer)
    disallowed = tuple(renderer for renderer in AdaptiveRenderer if renderer not in eligible)

    return SelectorDecision(
        contract=CONTRACT_VERSION,
        benchmark_id=analysis.benchmark_id,
        selected_renderer=selected,
        eligible_renderers=tuple(eligible),
        disallowed_renderers=disallowed,
        selection_reasons=tuple(reasons),
        direct_required_reasons=tuple(dict.fromkeys(direct_reasons)),
        minimal_forbidden_reasons=tuple(dict.fromkeys(minimal_forbidden)),
        expected_information_loss=selected_audit.dropped_elements,
        information_audits=audits,
    )


def render_adaptive_candidate(
    current_ai_text: str,
    analysis: FreeAnalystAnalysis,
    renderer: AdaptiveRenderer,
) -> RenderedFreeAnalyst:
    if renderer == AdaptiveRenderer.DIRECT_ANALYST:
        return render_free_analyst_direct(analysis)
    if renderer == AdaptiveRenderer.CONCISE_HYBRID:
        return render_free_analyst_vnext_hybrid(analysis)
    minimal = build_minimal_vnext_message(current_ai_text)
    return RenderedFreeAnalyst(
        renderer=AdaptiveRenderer.MINIMAL_VNEXT.value,
        text=minimal.text,
        sentence_supports=(),
    )


def adaptive_renderer_safety_report(
    current_ai_text: str,
    analysis: FreeAnalystAnalysis,
    decision: SelectorDecision,
    rendered: RenderedFreeAnalyst,
    *,
    supporting_reference_text: str = "",
) -> dict[str, object]:
    audit = decision.audit_for(decision.selected_renderer)
    if decision.selected_renderer == AdaptiveRenderer.MINIMAL_VNEXT:
        parity = factual_parity_report(current_ai_text, rendered.text)
        safety = {
            "status": parity["status"],
            "fact_mismatch": parity["fact_mismatch"],
            "unsupported_numeric_claims": parity["unsupported_numeric_claims"],
            "unsupported_causality": parity["unsupported_causality"],
            "temporal_violations": parity["temporal_violations"],
            "trade_ar_leak": len(parity["trade_ar_user_visible_leaks"]),
            "hidden_arithmetic": 0,
            "external_knowledge": 0,
            "unsupported_synthesis": 0,
            "entity_owner_mismatch": 0,
            "ticker_owner_mismatch": 0,
            "market_owner_mismatch": 0,
            "packet_owner_mismatch": 0,
            "support_ref_owner_mismatch": 0,
            "industry_context_mismatch": 0,
            "thesis_driver_owner_mismatch": 0,
            "fact_ref_owner_mismatch": 0,
            "relation_owner_mismatch": 0,
            "expectation_owner_mismatch": 0,
        }
    else:
        evidence_source = "\n\n".join(
            value
            for value in (current_ai_text.strip(), supporting_reference_text.strip())
            if value
        )
        safety = rendered_safety_report(evidence_source, analysis, rendered)
    material_loss = len(audit.material_dropped_elements)
    status = "PASS" if safety["status"] == "PASS" and material_loss == 0 else "FAIL"
    return {
        **safety,
        "contract": CONTRACT_VERSION,
        "status": status,
        "selected_renderer": decision.selected_renderer,
        "material_information_loss": material_loss,
        "material_dropped_elements": list(audit.material_dropped_elements),
    }


def _fallback_result(
    *,
    benchmark_id: str,
    current_ai_text: str,
    deterministic_reference: str,
    analysis: FreeAnalystAnalysis,
    validation: dict[str, object],
    reason: str,
) -> AdaptiveRendererResult:
    text = deterministic_reference or current_ai_text
    issue_counts: dict[str, int] = {}
    for issue in validation.get("issues", []):
        if not isinstance(issue, dict):
            continue
        code = str(issue.get("code") or "")
        issue_counts[code] = issue_counts.get(code, 0) + 1
    return AdaptiveRendererResult(
        contract=CONTRACT_VERSION,
        benchmark_id=benchmark_id,
        status="FALLBACK",
        analysis=analysis,
        synthesis_validation=validation,
        decision=None,
        rendered=None,
        final_text=text,
        final_delivery_mode="DETERMINISTIC_FALLBACK",
        fallback_reason=reason,
        safety={
            "contract": CONTRACT_VERSION,
            "status": "PASS",
            "fact_mismatch": 0,
            "unsupported_numeric_claims": [],
            "unsupported_causality": 0,
            "temporal_violations": 0,
            "trade_ar_leak": 0,
            "hidden_arithmetic": 0,
            "external_knowledge": 0,
            "material_information_loss": 0,
            "entity_owner_mismatch": issue_counts.get("entity_owner_mismatch", 0),
            "ticker_owner_mismatch": issue_counts.get("ticker_owner_mismatch", 0),
            "market_owner_mismatch": issue_counts.get("market_owner_mismatch", 0),
            "packet_owner_mismatch": issue_counts.get("packet_owner_mismatch", 0),
            "support_ref_owner_mismatch": issue_counts.get("support_ref_owner_mismatch", 0),
            "industry_context_mismatch": (
                issue_counts.get("industry_context_owner_mismatch", 0)
                + issue_counts.get("industry_concept_ownership_mismatch", 0)
                + issue_counts.get("semantic_concept_declaration_mismatch", 0)
            ),
            "thesis_driver_owner_mismatch": issue_counts.get(
                "thesis_driver_owner_mismatch", 0
            ),
            "fact_ref_owner_mismatch": issue_counts.get("fact_ref_owner_mismatch", 0),
            "relation_owner_mismatch": issue_counts.get("relation_owner_mismatch", 0),
            "expectation_owner_mismatch": (
                issue_counts.get("expectation_owner_mismatch", 0)
                + issue_counts.get("expectation_level_mismatch", 0)
            ),
        },
    )


def run_adaptive_renderer(
    current_ai_text: str,
    *,
    benchmark_id: str,
    deterministic_reference: str = "",
    market: str | None = None,
    packet_owner: str | None = None,
    analysis_override: FreeAnalystAnalysis | None = None,
    selector: Selector = select_adaptive_renderer,
    renderer: Renderer = render_adaptive_candidate,
) -> AdaptiveRendererResult:
    analysis = analysis_override or build_free_analyst_analysis(
        current_ai_text,
        benchmark_id=benchmark_id,
        market=market,
        packet_owner=packet_owner,
        supporting_reference_text=deterministic_reference,
    )
    validation = validate_free_analyst_analysis(analysis).to_dict()
    if validation["status"] != "PASS":
        return _fallback_result(
            benchmark_id=benchmark_id,
            current_ai_text=current_ai_text,
            deterministic_reference=deterministic_reference,
            analysis=analysis,
            validation=validation,
            reason="free_analyst_validation_failed",
        )
    try:
        decision = selector(analysis, current_ai_text)
    except (LookupError, RuntimeError, ValueError):
        return _fallback_result(
            benchmark_id=benchmark_id,
            current_ai_text=current_ai_text,
            deterministic_reference=deterministic_reference,
            analysis=analysis,
            validation=validation,
            reason="selector_failed",
        )
    rendered = renderer(current_ai_text, analysis, decision.selected_renderer)
    safety = adaptive_renderer_safety_report(
        current_ai_text,
        analysis,
        decision,
        rendered,
        supporting_reference_text=deterministic_reference,
    )
    if safety["status"] != "PASS":
        return _fallback_result(
            benchmark_id=benchmark_id,
            current_ai_text=current_ai_text,
            deterministic_reference=deterministic_reference,
            analysis=analysis,
            validation=validation,
            reason="selected_renderer_validation_failed",
        )
    return AdaptiveRendererResult(
        contract=CONTRACT_VERSION,
        benchmark_id=benchmark_id,
        status="PASS",
        analysis=analysis,
        synthesis_validation=validation,
        decision=decision,
        rendered=rendered,
        final_text=rendered.text,
        final_delivery_mode="ADAPTIVE_VALIDATED_CANDIDATE",
        fallback_reason=None,
        safety=safety,
    )
