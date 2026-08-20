from __future__ import annotations

from typing import Mapping

from app.services.industry_reasoning_service import build_industry_reasoning_plan


RUNTIME_SPECIFICITY_CONTRACT = "runtime-message-specificity-v2"
RUNTIME_REASONING_OWNERSHIP_CONTRACT = "runtime-reasoning-ownership-v1"
CANONICAL_SUPPLY_FLOW_TUPLE_CONTRACT = "canonical-supply-flow-tuple-v1"
NUMERIC_PRIMARY_OWNER_CONTRACT = "numeric-primary-owner-v1"

_BUSINESS_EARNINGS_FIELDS = {
    "revenue",
    "segment_revenue",
    "gross_profit",
    "gross_margin_pct",
    "operating_income",
    "operating_margin_pct",
    "net_income",
    "unit_volume",
    "average_selling_price",
    "capacity_utilization",
}


def _mapping(value: object) -> dict[str, object]:
    return dict(value) if isinstance(value, Mapping) else {}


def _security_identity_policy(stock: dict[str, object]) -> dict[str, object]:
    identity_fact = next(
        (
            item
            for item in stock.get("fact_catalog", [])
            if isinstance(item, dict) and item.get("fact_id") == "security_identity:current"
        ),
        {},
    )
    basis_fact = next(
        (
            item
            for item in stock.get("fact_catalog", [])
            if isinstance(item, dict) and item.get("fact_id") == "security_basis:current"
        ),
        {},
    )
    identity_fields = _mapping(_mapping(identity_fact).get("fields"))
    basis_fields = _mapping(_mapping(basis_fact).get("fields"))
    identity_state = str(identity_fields.get("identity_state") or "unknown")
    ratio_state = str(basis_fields.get("depositary_ratio_state") or "unknown")
    depositary_reasoning_allowed = identity_state == "verified_depositary"
    ratio_reasoning_allowed = bool(
        depositary_reasoning_allowed
        and ratio_state == "verified"
        and identity_fields.get("depositary_ratio") is not None
        and identity_fields.get("depositary_ratio_direction")
        and identity_fields.get("depositary_ratio_source")
    )
    return {
        "owner": "security_identity",
        "identity_state": identity_state,
        "depositary_reasoning_allowed": depositary_reasoning_allowed,
        "depositary_ratio_reasoning_allowed": ratio_reasoning_allowed,
        "generic_basis_caution_allowed": identity_state in {"unknown", "conflict"},
        "suppression_reason": (
            None
            if ratio_reasoning_allowed
            else "security_identity_not_depositary"
            if identity_state in {"verified_non_depositary", "domestic_common"}
            else "depositary_ratio_not_verified"
        ),
    }


def _candidate(
    *,
    category: str,
    value: str,
    base_tier: int,
    owner: str,
    evidence_type: str,
    decision_role: str,
    section: str,
    specificity_key: str,
    fact_ids: list[str] | None = None,
    metadata: dict[str, object] | None = None,
) -> dict[str, object]:
    candidate = {
        "category": category,
        "value": value,
        "base_tier": base_tier,
        "owner": owner,
        "evidence_type": evidence_type,
        "decision_role": decision_role,
        "section": section,
        "specificity_key": specificity_key,
        "materiality": "decision_relevant",
        "fact_ids": fact_ids or [],
    }
    if metadata:
        candidate["metadata"] = metadata
    return candidate


def _business_earnings_policy(stock: dict[str, object]) -> dict[str, object]:
    business_facts: list[dict[str, object]] = []
    for item in stock.get("fact_catalog", []):
        if not isinstance(item, dict):
            continue
        fact_id = str(item.get("fact_id") or "")
        if not fact_id.startswith("earnings:") or item.get("prose_eligible") is not True:
            continue
        fields = _mapping(item.get("fields"))
        eligible_fields = sorted(_BUSINESS_EARNINGS_FIELDS.intersection(fields))
        if eligible_fields:
            business_facts.append(
                {
                    "fact_id": fact_id,
                    "eligible_fields": eligible_fields,
                }
            )
    return {
        "owner": "business_earnings",
        "business_fact_candidates": business_facts,
        "minimum_numeric_anchor_count": 0,
        "valuation_numeric_filler_allowed": False,
        "valuation_owned_semantics": [
            "bvps",
            "forward_pe",
            "historical_pb_percentile",
            "historical_pe_percentile",
            "price_to_book",
            "trailing_pe",
            "ttm_eps",
        ],
        "missing_business_fact_policy": "use_industry_specific_unknown",
        "generic_numeric_summary_scaffold": "prohibited_portfolio_template",
    }


def _changed_transition(value: object) -> bool:
    transition = str(value or "")
    if "_to_" not in transition:
        return False
    previous, current = transition.split("_to_", 1)
    return bool(previous and current and previous != current)


def _risk_reward_delta_policy(delta: dict[str, object]) -> dict[str, object]:
    rr_change = str(delta.get("rr_change") or "")
    material_reasons: list[str] = []
    if rr_change in {"became_available", "became_unavailable"}:
        material_reasons.append("risk_reward_availability_transition")
    if _changed_transition(delta.get("chart_state_change")):
        material_reasons.append("chart_state_transition")
    if _changed_transition(delta.get("confirmation_transition")):
        material_reasons.append("confirmation_lifecycle_transition")
    for field in ("support_change", "resistance_change"):
        state = str(delta.get(field) or "")
        if state not in {"", "unchanged", "unavailable"}:
            material_reasons.append(field)
    candidate_allowed = bool(material_reasons) and rr_change in {
        "improved",
        "deteriorated",
        "became_available",
        "became_unavailable",
    }
    return {
        "owner": "price_context",
        "change_state": rr_change or "unavailable",
        "decision_candidate_allowed": candidate_allowed,
        "material_transition_reasons": material_reasons,
        "standalone_previous_current_pair_allowed": False,
        "comparison_rendering": (
            "integrate_with_primary_price_transition"
            if candidate_allowed
            else "suppress_non_material_delta"
        ),
        "suppression_reason": None if candidate_allowed else "no_material_price_transition",
    }


def _structured_field_policy(stock: dict[str, object]) -> dict[str, object]:
    supply_semantics = {
        str(item.get("semantic_type") or "")
        for item in stock.get("numeric_registry", [])
        if isinstance(item, dict) and item.get("prose_allowed") is True
    }
    required_supply_semantics = {
        "foreign_net_buy_qty",
        "foreign_net_buy_qty_5d",
        "foreign_net_buy_qty_20d",
        "institution_net_buy_qty",
        "institution_net_buy_qty_5d",
        "institution_net_buy_qty_20d",
    }
    return {
        "supply_flow": {
            "contract": CANONICAL_SUPPLY_FLOW_TUPLE_CONTRACT,
            "enabled": required_supply_semantics.issubset(supply_semantics),
            "owner": "positioning",
            "metric_family": "supply_flow",
            "actors": ["foreign", "institution"],
            "horizons": ["1d", "5d", "20d"],
            "structured_tuple_repetition": "allowed",
            "interpretive_prose_repetition": "quality_checked",
            "missing_cell_policy": "specific_unknown",
        }
    }


def _numeric_primary_owner_policy() -> dict[str, object]:
    return {
        "contract": NUMERIC_PRIMARY_OWNER_CONTRACT,
        "current_price_risk_reward_ratio": {
            "owner": "price_context",
            "primary_text_ref": "price_positioning.text",
            "exact_value_occurrence_limit": 1,
            "secondary_sections": "meaning_only_without_exact_number",
            "transition_exception": "canonical_material_transition_only",
        },
    }


def build_runtime_specificity_plan(stock: dict[str, object]) -> dict[str, object]:
    """Expose verified stock-specific choices before prose generation."""
    monitoring = _mapping(stock.get("monitoring_state"))
    delta = _mapping(monitoring.get("delta"))
    deterministic = _mapping(stock.get("deterministic_assessment"))
    industry = build_industry_reasoning_plan(stock)
    routing = _mapping(stock.get("knowledge_routing"))
    framework_roles = _mapping(routing.get("framework_roles"))
    security_policy = _security_identity_policy(stock)
    business_policy = _business_earnings_policy(stock)
    rr_policy = _risk_reward_delta_policy(delta)
    candidates: list[dict[str, object]] = []

    business_change = str(deterministic.get("business_thesis_change") or "no_material_change")
    if business_change != "no_material_change":
        candidates.append(
            _candidate(
                category="business_thesis",
                value=business_change,
                base_tier=1,
                owner="business_earnings",
                evidence_type="deterministic_assessment",
                decision_role="thesis_delta",
                section="core_judgment",
                specificity_key=f"{industry.primary_framework}:business:{business_change}",
            )
        )
    confirmation = str(delta.get("confirmation_transition") or "")
    if confirmation and not confirmation.endswith("_to_not_reached"):
        candidates.append(
            _candidate(
                category="price_lifecycle",
                value=confirmation,
                base_tier=2,
                owner="price_context",
                evidence_type="monitoring_transition",
                decision_role="entry_confirmation",
                section="price_positioning",
                specificity_key=f"price_lifecycle:{confirmation}",
                fact_ids=["monitoring:confirmation_transition"],
            )
        )
    rr_change = str(delta.get("rr_change") or "")
    if rr_policy["decision_candidate_allowed"]:
        candidates.append(
            _candidate(
                category="risk_reward",
                value=rr_change,
                base_tier=3,
                owner="price_context",
                evidence_type="chart_structure",
                decision_role="entry_asymmetry",
                section="price_positioning",
                specificity_key=f"price_rr:{rr_change}",
                fact_ids=["monitoring:risk_reward_transition"],
                metadata={
                    "material_transition_reasons": rr_policy[
                        "material_transition_reasons"
                    ],
                    "standalone_previous_current_pair_allowed": False,
                },
            )
        )
    supply = str(delta.get("supply_transition") or "")
    if supply and supply not in {"unchanged", "unavailable"}:
        candidates.append(
            _candidate(
                category="supply",
                value=supply,
                base_tier=3,
                owner="positioning",
                evidence_type="actor_horizon_flow",
                decision_role="positioning_context",
                section="supply_analysis",
                specificity_key=f"positioning:{supply}:{industry.primary_framework}",
            )
        )
    valuation = str(delta.get("valuation_change") or "")
    if valuation not in {"", "unchanged_or_unavailable"}:
        candidates.append(
            _candidate(
                category="valuation",
                value=valuation,
                base_tier=2,
                owner="valuation",
                evidence_type="typed_valuation",
                decision_role="expectation_context",
                section="valuation_analysis",
                specificity_key=f"valuation:{valuation}:{industry.primary_framework}",
            )
        )
    if not candidates:
        missing_driver = next(iter(industry.missing_drivers), "company_evidence")
        candidates.append(
            _candidate(
                category="no_material_delta",
                value="use_current_decision_context",
                base_tier=4,
                owner="industry_driver",
                evidence_type="industry_specific_unknown",
                decision_role="next_confirmation",
                section="core_judgment",
                specificity_key=(
                    f"{industry.primary_framework}:{missing_driver}:{industry.next_confirmation}"
                ),
            )
        )

    required_price_facts = [
        str(item.get("fact_id"))
        for item in _mapping(stock.get("state_grounding_requirements")).get("price", [])
        if isinstance(item, dict) and item.get("fact_id")
    ]
    return {
        "contract": RUNTIME_SPECIFICITY_CONTRACT,
        "ownership_contract": RUNTIME_REASONING_OWNERSHIP_CONTRACT,
        "decision_candidates": candidates,
        "primary_framework": industry.primary_framework,
        "framework_confidence": industry.confidence,
        "framework_ownership": {
            "investment_industry": list(framework_roles.get("investment_industry", [])),
            "price_context": list(framework_roles.get("price_context", [])),
            "security_identity": list(framework_roles.get("security_identity", [])),
        },
        "security_reasoning_policy": security_policy,
        "business_earnings_policy": business_policy,
        "risk_reward_delta_policy": rr_policy,
        "structured_field_policy": _structured_field_policy(stock),
        "numeric_primary_owner_policy": _numeric_primary_owner_policy(),
        "financial_caution_policy": {
            "owner": "financial_lineage",
            "generic_cross_ticker_sentence": "suppress",
            "user_visible": "specific_decision_material_limitation_only",
            "missing_denominator": "fail_closed",
        },
        "suppressed_candidates": (
            []
            if security_policy["depositary_ratio_reasoning_allowed"]
            else [
                {
                    "owner": "security_identity",
                    "category": "depositary_ratio",
                    "reason": security_policy["suppression_reason"],
                }
            ]
        ),
        "available_driver_families": list(industry.available_fact_families),
        "missing_driver_candidates": list(industry.missing_drivers[:3]),
        "observer_focus": industry.observer_focus,
        "holder_focus": industry.holder_focus,
        "next_confirmation": industry.next_confirmation,
        "required_current_price_fact_ids": list(dict.fromkeys(required_price_facts)),
        "user_visible_methodology_policy": "suppress_unless_needed_to_prevent_misinterpretation",
        "selection_constraints": {
            "one_primary_owner_per_evidence": True,
            "generic_cash_flow_tail_requires_industry_driver": True,
            "cross_ticker_template_reuse": ("suppress_or_ground_with_subject_specific_evidence"),
            "synonym_only_variation": "not_credit",
        },
    }
