import pytest

from app.services.current_price_context_service import (
    fallback_price_context_errors,
    select_current_price_context,
)
from app.services.runtime_specificity_service import build_runtime_specificity_plan


def _price_context(
    *,
    rr_available: bool = True,
    confirmation_state: str = "holding_above",
) -> dict[str, object]:
    return {
        "decision": {"current_price": 206_500, "currency": "KRW"},
        "monitoring_state": {
            "current": {
                "price_structure": {
                    "as_of_date": "2026-08-18",
                    "price_basis": "adjusted_close",
                    "current_price": 206_500,
                    "active_support": {
                        "available": True,
                        "zone_low": 201_392.4,
                        "zone_high": 208_607.6,
                        "timeframe": "daily",
                        "strength": "Medium",
                        "source": "dynamic",
                    },
                    "active_resistance": {
                        "available": True,
                        "zone_low": 211_867.1,
                        "zone_high": 218_132.9,
                        "timeframe": "daily",
                        "strength": "Medium",
                        "source": "dynamic",
                    },
                    "risk_reward": (
                        {
                            "available": True,
                            "current_price": {
                                "ratio": 0.535306,
                                "classification": "poor_chase",
                            },
                        }
                        if rr_available
                        else {"available": False, "reason": "resistance_unavailable"}
                    ),
                    "chart_invalidation": {
                        "available": True,
                        "price": 196_473.9,
                        "chart_only": True,
                    },
                    "chart_state": {"state": "WAIT", "confidence": "medium"},
                    "registered_rule_state": {
                        "confirmation": {
                            "price": 200_000,
                            "state": confirmation_state,
                            "relevance": "background",
                        }
                    },
                }
            },
            "delta": {
                "confirmation_transition": f"crossed_to_{confirmation_state}",
                "rr_change": "unchanged",
                "supply_transition": "mixed_horizons",
                "valuation_change": "unchanged_or_unavailable",
            },
        },
    }


def test_current_price_context_prioritizes_dynamic_structure_and_history() -> None:
    selected = select_current_price_context(_price_context())

    assert selected["availability"] == "ready"
    assert selected["current_price_risk_reward"]["ratio"] == 0.535306
    assert selected["registered_confirmation"]["rendering_class"] == ("HISTORICAL_REFERENCE")
    assert selected["registered_confirmation"]["automatically_promoted_to_support"] is False


def test_fallback_context_rejects_crossed_confirmation_as_future_trigger() -> None:
    selected = select_current_price_context(_price_context())
    errors = fallback_price_context_errors(
        selected,
        "동적 지지 201,392원~208,608원, 동적 저항 211,867원~218,133원, "
        "현재가 기준 차트 손익비 0.54배, 상향 확인 가격: 200,000원",
    )

    assert "crossed_confirmation_rendered_as_future_trigger" in errors


def test_current_price_context_keeps_structural_rr_unavailable() -> None:
    selected = select_current_price_context(_price_context(rr_available=False))

    assert selected["current_price_risk_reward"] == {
        "available": False,
        "ratio": None,
        "classification": None,
        "reason": "resistance_unavailable",
    }


def test_runtime_specificity_plan_uses_material_candidates_without_quota() -> None:
    stock = {
        "ticker": "086280",
        "industry": "Transportation and Logistics",
        "company_profile": {"quality": "verified"},
        "knowledge_routing": {
            "industry_key": "shipping",
            "industry_routing": {
                "confidence": "high",
                "source": "normalized_profile_taxonomy",
            },
        },
        "deterministic_assessment": {"business_thesis_change": "no_material_change"},
        "monitoring_state": _price_context()["monitoring_state"],
        "state_grounding_requirements": {
            "price": [
                    {
                        "fact_id": "chart:structure:risk_reward:current_price",
                        "field_paths": ["fields.ratio"],
                        "reason": "current_price_risk_reward",
                    }
            ]
        },
        "fact_catalog": [
            {
                "fact_id": "security_identity:current",
                "fields": {"identity_state": "verified_non_depositary"},
            },
            {
                "fact_id": "security_basis:current",
                "fields": {"depositary_ratio_state": "not_applicable"},
            },
            {
                "fact_id": "chart:structure:risk_reward:current_price",
                "fact_type": "chart_risk_reward_current_price",
                "fields": {"ratio": 0.535306},
            },
        ],
        "current_price_context": select_current_price_context(_price_context()),
    }

    plan = build_runtime_specificity_plan(stock)

    assert plan["contract"] == "runtime-message-specificity-v2"
    assert plan["ownership_contract"] == "runtime-reasoning-ownership-v1"
    assert plan["primary_framework"] == "transport_logistics"
    assert plan["decision_candidates"][0]["category"] == "price_lifecycle"
    assert plan["decision_candidates"][0]["owner"] == "price_context"
    assert plan["decision_candidates"][0]["section"] == "price_positioning"
    assert plan["required_current_price_fact_ids"] == ["chart:structure:risk_reward:current_price"]
    assert plan["price_fact_ownership"]["current_rr_fact_id"] == (
        "chart:structure:risk_reward:current_price"
    )
    assert plan["price_fact_ownership"]["unavailable_fact_ids"] == []
    assert plan["business_earnings_policy"] == {
        "owner": "business_earnings",
        "business_fact_candidates": [],
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
    assert plan["risk_reward_delta_policy"]["decision_candidate_allowed"] is False
    assert plan["risk_reward_delta_policy"]["standalone_previous_current_pair_allowed"] is False
    assert plan["security_reasoning_policy"] == {
        "owner": "security_identity",
        "identity_state": "verified_non_depositary",
        "depositary_reasoning_allowed": False,
        "depositary_ratio_reasoning_allowed": False,
        "generic_basis_caution_allowed": False,
        "suppression_reason": "security_identity_not_depositary",
    }
    assert plan["suppressed_candidates"] == [
        {
            "owner": "security_identity",
            "category": "depositary_ratio",
            "reason": "security_identity_not_depositary",
        }
    ]


def test_runtime_specificity_excludes_unavailable_rr_fact_from_price_ownership() -> None:
    stock = {
        "knowledge_routing": {
            "industry_routing": {"confidence": "low"},
            "framework_roles": {},
        },
        "deterministic_assessment": {"business_thesis_change": "no_material_change"},
        "monitoring_state": _price_context(rr_available=False)["monitoring_state"],
        "state_grounding_requirements": {
            "price": [
                {
                    "fact_id": "price:current",
                    "field_paths": ["fields.current_price"],
                    "reason": "current_price",
                },
                {
                    "fact_id": "chart:structure:nearest_supports:1",
                    "field_paths": ["fields.zone_low", "fields.zone_high"],
                    "reason": "active_support",
                },
                {
                    "fact_id": "chart:structure:nearest_resistance:1",
                    "field_paths": ["fields.zone_low", "fields.zone_high"],
                    "reason": "active_resistance",
                },
            ]
        },
        "fact_catalog": [
            {"fact_id": "price:current", "fact_type": "price"},
            {
                "fact_id": "chart:structure:nearest_supports:1",
                "fact_type": "chart_support_zone",
            },
            {
                "fact_id": "chart:structure:nearest_resistance:1",
                "fact_type": "chart_resistance_zone",
            },
        ],
        "current_price_context": select_current_price_context(
            _price_context(rr_available=False)
        ),
    }

    ownership = build_runtime_specificity_plan(stock)["price_fact_ownership"]

    assert ownership["current_price_fact_id"] == "price:current"
    assert ownership["support_context_id"] == "chart:structure:nearest_supports:1"
    assert ownership["resistance_context_id"] == (
        "chart:structure:nearest_resistance:1"
    )
    assert ownership["current_rr_fact_id"] is None
    assert ownership["unavailable_fact_ids"] == [
        "chart:structure:risk_reward:current_price"
    ]
    assert "chart:structure:risk_reward:current_price" not in ownership[
        "allowed_fact_ids"
    ]


def test_runtime_specificity_plan_preserves_verified_depositary_ratio_reasoning() -> None:
    stock = {
        "knowledge_routing": {
            "industry_key": "semiconductor_foundry",
            "industry_routing": {"confidence": "high"},
            "framework_roles": {
                "investment_industry": ["semiconductor_foundry_valuation"],
                "price_context": [],
                "security_identity": ["adr_share_basis"],
            },
        },
        "deterministic_assessment": {"business_thesis_change": "no_material_change"},
        "monitoring_state": {},
        "state_grounding_requirements": {"price": []},
        "fact_catalog": [
            {
                "fact_id": "security_identity:current",
                "fields": {
                    "identity_state": "verified_depositary",
                    "depositary_ratio": 0.1,
                    "depositary_ratio_direction": "ordinary_shares_per_adr",
                    "depositary_ratio_source": "https://example.test/filing",
                },
            },
            {
                "fact_id": "security_basis:current",
                "fields": {"depositary_ratio_state": "verified"},
            },
        ],
    }

    plan = build_runtime_specificity_plan(stock)

    assert plan["security_reasoning_policy"]["depositary_reasoning_allowed"] is True
    assert plan["security_reasoning_policy"]["depositary_ratio_reasoning_allowed"] is True
    assert plan["suppressed_candidates"] == []


@pytest.mark.parametrize(
    ("identity_state", "generic_allowed", "suppression_reason"),
    (
        ("domestic_common", False, "security_identity_not_depositary"),
        ("unknown", True, "depositary_ratio_not_verified"),
        ("conflict", True, "depositary_ratio_not_verified"),
    ),
)
def test_runtime_specificity_plan_fails_depositary_reasoning_closed(
    identity_state: str,
    generic_allowed: bool,
    suppression_reason: str,
) -> None:
    stock = {
        "knowledge_routing": {
            "industry_key": "general",
            "industry_routing": {"confidence": "low"},
            "framework_roles": {
                "investment_industry": [],
                "price_context": [],
                "security_identity": ["adr_share_basis"],
            },
        },
        "deterministic_assessment": {"business_thesis_change": "no_material_change"},
        "monitoring_state": {},
        "state_grounding_requirements": {"price": []},
        "fact_catalog": [
            {
                "fact_id": "security_identity:current",
                "fields": {"identity_state": identity_state},
            },
            {
                "fact_id": "security_basis:current",
                "fields": {"depositary_ratio_state": "unknown"},
            },
        ],
    }

    policy = build_runtime_specificity_plan(stock)["security_reasoning_policy"]

    assert policy["depositary_reasoning_allowed"] is False
    assert policy["depositary_ratio_reasoning_allowed"] is False
    assert policy["generic_basis_caution_allowed"] is generic_allowed
    assert policy["suppression_reason"] == suppression_reason


def test_runtime_specificity_plan_keeps_business_facts_out_of_valuation_fillers() -> None:
    stock = {
        "knowledge_routing": {
            "industry_key": "general",
            "industry_routing": {"confidence": "medium"},
        },
        "deterministic_assessment": {"business_thesis_change": "no_material_change"},
        "monitoring_state": {"delta": {}},
        "state_grounding_requirements": {"price": []},
        "fact_catalog": [
            {
                "fact_id": "earnings:2026-06-30",
                "prose_eligible": True,
                "fields": {
                    "revenue": {"value": 100, "currency": "USD"},
                    "operating_margin_pct": 18.5,
                    "period": "2026-06-30",
                },
            },
            {
                "fact_id": "valuation:current",
                "prose_eligible": True,
                "fields": {"ttm_eps": 3.2, "bvps": 11.0},
            },
        ],
    }

    policy = build_runtime_specificity_plan(stock)["business_earnings_policy"]

    assert policy["business_fact_candidates"] == [
        {
            "fact_id": "earnings:2026-06-30",
            "eligible_fields": ["operating_margin_pct", "revenue"],
        }
    ]
    assert policy["valuation_numeric_filler_allowed"] is False
    assert policy["minimum_numeric_anchor_count"] == 0


def test_runtime_specificity_plan_requires_material_rr_transition() -> None:
    stock = {
        "knowledge_routing": {
            "industry_key": "general",
            "industry_routing": {"confidence": "medium"},
        },
        "deterministic_assessment": {"business_thesis_change": "no_material_change"},
        "monitoring_state": {
            "delta": {
                "chart_state_change": "WAIT_to_HOLD",
                "confirmation_transition": "not_reached_to_crossed",
                "rr_change": "deteriorated",
                "support_change": "shifted_up",
                "resistance_change": "unchanged",
            }
        },
        "state_grounding_requirements": {"price": []},
        "fact_catalog": [],
    }

    plan = build_runtime_specificity_plan(stock)
    policy = plan["risk_reward_delta_policy"]

    assert policy["decision_candidate_allowed"] is True
    assert policy["standalone_previous_current_pair_allowed"] is False
    assert policy["material_transition_reasons"] == [
        "chart_state_transition",
        "confirmation_lifecycle_transition",
        "support_change",
    ]
    rr_candidate = next(
        item for item in plan["decision_candidates"] if item["category"] == "risk_reward"
    )
    assert rr_candidate["owner"] == "price_context"
    assert rr_candidate["metadata"]["standalone_previous_current_pair_allowed"] is False


def test_runtime_specificity_plan_exposes_structured_supply_and_rr_owner_contracts() -> None:
    supply_semantics = (
        "foreign_net_buy_qty",
        "foreign_net_buy_qty_5d",
        "foreign_net_buy_qty_20d",
        "institution_net_buy_qty",
        "institution_net_buy_qty_5d",
        "institution_net_buy_qty_20d",
    )
    stock = {
        "knowledge_routing": {
            "industry_key": "general",
            "industry_routing": {"confidence": "medium"},
        },
        "deterministic_assessment": {"business_thesis_change": "no_material_change"},
        "monitoring_state": {"delta": {}},
        "state_grounding_requirements": {"price": []},
        "fact_catalog": [],
        "numeric_registry": [
            {"semantic_type": semantic, "prose_allowed": True}
            for semantic in supply_semantics
        ],
    }

    plan = build_runtime_specificity_plan(stock)
    supply = plan["structured_field_policy"]["supply_flow"]
    rr = plan["numeric_primary_owner_policy"][
        "current_price_risk_reward_ratio"
    ]

    assert supply["contract"] == "canonical-supply-flow-tuple-v1"
    assert supply["enabled"] is True
    assert supply["structured_tuple_repetition"] == "allowed"
    assert supply["interpretive_prose_repetition"] == "quality_checked"
    assert rr["primary_text_ref"] == "price_positioning.text"
    assert rr["exact_value_occurrence_limit"] == 1
    assert plan["financial_caution_policy"]["generic_cross_ticker_sentence"] == (
        "suppress"
    )
