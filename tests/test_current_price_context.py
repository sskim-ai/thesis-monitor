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
    assert selected["registered_confirmation"]["rendering_class"] == (
        "HISTORICAL_REFERENCE"
    )
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
        "deterministic_assessment": {
            "business_thesis_change": "no_material_change"
        },
        "monitoring_state": _price_context()["monitoring_state"],
        "state_grounding_requirements": {
            "price": [
                {
                    "fact_id": "chart:structure:risk_reward:current_price",
                    "field_paths": ["fields.ratio"],
                }
            ]
        },
        "fact_catalog": [],
    }

    plan = build_runtime_specificity_plan(stock)

    assert plan["contract"] == "runtime-message-specificity-v1"
    assert plan["primary_framework"] == "transport_logistics"
    assert plan["decision_candidates"][0]["category"] == "price_lifecycle"
    assert plan["required_current_price_fact_ids"] == [
        "chart:structure:risk_reward:current_price"
    ]
