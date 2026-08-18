from __future__ import annotations

from typing import Mapping

from app.services.industry_reasoning_service import build_industry_reasoning_plan


RUNTIME_SPECIFICITY_CONTRACT = "runtime-message-specificity-v1"


def _mapping(value: object) -> dict[str, object]:
    return dict(value) if isinstance(value, Mapping) else {}


def build_runtime_specificity_plan(stock: dict[str, object]) -> dict[str, object]:
    """Expose verified stock-specific choices before prose generation."""
    monitoring = _mapping(stock.get("monitoring_state"))
    delta = _mapping(monitoring.get("delta"))
    deterministic = _mapping(stock.get("deterministic_assessment"))
    industry = build_industry_reasoning_plan(stock)
    candidates: list[dict[str, object]] = []

    business_change = str(
        deterministic.get("business_thesis_change") or "no_material_change"
    )
    if business_change != "no_material_change":
        candidates.append(
            {
                "category": "business_thesis",
                "value": business_change,
                "base_tier": 1,
            }
        )
    confirmation = str(delta.get("confirmation_transition") or "")
    if confirmation and not confirmation.endswith("_to_not_reached"):
        candidates.append(
            {
                "category": "price_lifecycle",
                "value": confirmation,
                "base_tier": 2,
                "fact_ids": ["monitoring:confirmation_transition"],
            }
        )
    rr_change = str(delta.get("rr_change") or "")
    if rr_change in {"improved", "deteriorated", "became_available", "became_unavailable"}:
        candidates.append(
            {
                "category": "risk_reward",
                "value": rr_change,
                "base_tier": 3,
                "fact_ids": ["monitoring:risk_reward_transition"],
            }
        )
    supply = str(delta.get("supply_transition") or "")
    if supply and supply not in {"unchanged", "unavailable"}:
        candidates.append(
            {
                "category": "supply",
                "value": supply,
                "base_tier": 3,
            }
        )
    valuation = str(delta.get("valuation_change") or "")
    if valuation not in {"", "unchanged_or_unavailable"}:
        candidates.append(
            {
                "category": "valuation",
                "value": valuation,
                "base_tier": 2,
            }
        )
    if not candidates:
        candidates.append(
            {
                "category": "no_material_delta",
                "value": "use_current_decision_context",
                "base_tier": 4,
            }
        )

    required_price_facts = [
        str(item.get("fact_id"))
        for item in _mapping(stock.get("state_grounding_requirements")).get(
            "price", []
        )
        if isinstance(item, dict) and item.get("fact_id")
    ]
    return {
        "contract": RUNTIME_SPECIFICITY_CONTRACT,
        "decision_candidates": candidates,
        "primary_framework": industry.primary_framework,
        "framework_confidence": industry.confidence,
        "available_driver_families": list(industry.available_fact_families),
        "missing_driver_candidates": list(industry.missing_drivers[:3]),
        "observer_focus": industry.observer_focus,
        "holder_focus": industry.holder_focus,
        "next_confirmation": industry.next_confirmation,
        "required_current_price_fact_ids": list(dict.fromkeys(required_price_facts)),
        "user_visible_methodology_policy": "suppress_unless_needed_to_prevent_misinterpretation",
    }
