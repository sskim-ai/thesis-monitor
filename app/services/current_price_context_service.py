from __future__ import annotations

from typing import Mapping


CURRENT_PRICE_CONTEXT_CONTRACT = "current-price-context-v1"


def _mapping(value: object) -> dict[str, object]:
    return dict(value) if isinstance(value, Mapping) else {}


def _number(value: object) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value)


def _zone(value: object) -> dict[str, object]:
    zone = _mapping(value)
    low = _number(zone.get("zone_low"))
    high = _number(zone.get("zone_high"))
    if zone.get("available") is not True or low is None or high is None:
        return {"available": False}
    return {
        "available": True,
        "zone_low": low,
        "zone_high": high,
        "timeframe": zone.get("timeframe"),
        "strength": zone.get("strength"),
        "source": zone.get("source"),
    }


def _confirmation_rendering_class(state: str, relevance: str) -> str:
    if state == "not_configured":
        return "UNAVAILABLE"
    if state == "not_reached" and relevance == "active":
        return "FUTURE_TRIGGER"
    if state in {"crossed", "retest_in_progress", "failed_breakout"}:
        return "ACTIVE_TRANSITION"
    if state in {"holding_above", "retest_held"}:
        return "HISTORICAL_REFERENCE"
    return "LIMITED_REFERENCE"


def select_current_price_context(
    price_context: Mapping[str, object],
) -> dict[str, object]:
    """Select current actionable price facts without calculating new values."""
    monitoring = _mapping(price_context.get("monitoring_state"))
    current = _mapping(monitoring.get("current"))
    structure = _mapping(current.get("price_structure"))
    decision = _mapping(price_context.get("decision"))
    if not structure:
        return {
            "contract": CURRENT_PRICE_CONTEXT_CONTRACT,
            "availability": "legacy_only",
            "reason": "monitoring_state_current_price_structure_unavailable",
            "current_price": _number(decision.get("current_price")),
            "currency": decision.get("currency"),
            "as_of_date": decision.get("price_as_of"),
            "price_basis": decision.get("price_basis"),
            "active_support": {"available": False},
            "active_resistance": {"available": False},
            "current_price_risk_reward": {"available": False},
            "chart_invalidation": {"available": False},
            "chart_state": {},
            "registered_confirmation": {
                "available": False,
                "rendering_class": "UNAVAILABLE",
            },
        }

    risk_reward = _mapping(structure.get("risk_reward"))
    current_rr = _mapping(risk_reward.get("current_price"))
    rr_ratio = _number(current_rr.get("ratio"))
    rr_available = risk_reward.get("available") is True and rr_ratio is not None
    invalidation = _mapping(structure.get("chart_invalidation"))
    invalidation_price = _number(invalidation.get("price"))
    confirmation = _mapping(
        _mapping(structure.get("registered_rule_state")).get("confirmation")
    )
    confirmation_state = str(confirmation.get("state") or "not_configured")
    confirmation_relevance = str(confirmation.get("relevance") or "unavailable")
    confirmation_price = _number(confirmation.get("price"))
    support = _zone(structure.get("active_support"))
    resistance = _zone(structure.get("active_resistance"))
    current_price = _number(structure.get("current_price"))
    available_count = sum(
        (
            current_price is not None,
            support.get("available") is True,
            resistance.get("available") is True,
            rr_available,
            invalidation.get("available") is True
            and invalidation_price is not None,
        )
    )
    return {
        "contract": CURRENT_PRICE_CONTEXT_CONTRACT,
        "availability": "ready" if available_count >= 4 else "partial",
        "current_price": current_price,
        "currency": decision.get("currency"),
        "as_of_date": structure.get("as_of_date"),
        "price_basis": structure.get("price_basis"),
        "active_support": support,
        "active_resistance": resistance,
        "current_price_risk_reward": {
            "available": rr_available,
            "ratio": rr_ratio if rr_available else None,
            "classification": current_rr.get("classification") if rr_available else None,
            "reason": None
            if rr_available
            else risk_reward.get("blocking_reason") or risk_reward.get("reason"),
        },
        "chart_invalidation": {
            "available": invalidation.get("available") is True
            and invalidation_price is not None,
            "price": invalidation_price,
            "reason": invalidation.get("reason"),
            "timeframe": invalidation.get("timeframe"),
            "chart_only": invalidation.get("chart_only"),
        },
        "chart_state": _mapping(structure.get("chart_state")),
        "registered_confirmation": {
            "available": confirmation_price is not None,
            "price": confirmation_price,
            "state": confirmation_state,
            "relevance": confirmation_relevance,
            "rendering_class": _confirmation_rendering_class(
                confirmation_state,
                confirmation_relevance,
            ),
            "crossed_at": confirmation.get("crossed_at"),
            "final_sessions_above": confirmation.get("final_sessions_above"),
            "automatically_promoted_to_support": False,
        },
    }


def fallback_price_context_errors(
    selection: Mapping[str, object],
    rendered_text: str,
) -> list[str]:
    """Fail closed when fallback prose contradicts the selected current context."""
    if selection.get("availability") == "legacy_only":
        return []
    errors: list[str] = []
    support = _mapping(selection.get("active_support"))
    resistance = _mapping(selection.get("active_resistance"))
    risk_reward = _mapping(selection.get("current_price_risk_reward"))
    confirmation = _mapping(selection.get("registered_confirmation"))
    if support.get("available") is True and "동적 지지" not in rendered_text:
        errors.append("fallback_dynamic_support_not_rendered")
    if resistance.get("available") is True and "동적 저항" not in rendered_text:
        errors.append("fallback_dynamic_resistance_not_rendered")
    if (
        risk_reward.get("available") is True
        and "현재가 기준 차트 손익비" not in rendered_text
    ):
        errors.append("fallback_current_price_rr_not_rendered")
    if confirmation.get("rendering_class") in {
        "ACTIVE_TRANSITION",
        "HISTORICAL_REFERENCE",
    } and "상향 확인 가격:" in rendered_text:
        errors.append("crossed_confirmation_rendered_as_future_trigger")
    if confirmation.get("automatically_promoted_to_support") is not False:
        errors.append("registered_confirmation_auto_promoted_to_support")
    return errors
