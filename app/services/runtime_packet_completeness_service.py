from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Literal


CURRENT_PRICE_RR_FACT_ID = "chart:structure:risk_reward:current_price"
CURRENT_PRICE_RR_FIELD_PATH = "fields.ratio"
CURRENT_PRICE_RR_SEMANTIC = "current_price_risk_reward_ratio"

CurrentPriceRRStatus = Literal[
    "READY",
    "UNAVAILABLE_BY_CONTRACT",
    "BUG_MISSING_FACT",
    "BUG_INVALID_FACT",
    "BUG_MISSING_NUMERIC_PATH",
    "BUG_INVALID_NUMERIC_PATH",
]


def _mapping(value: object) -> dict[str, object]:
    return value if isinstance(value, dict) else {}


def _number(value: object) -> float | None:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    return None


@dataclass(frozen=True)
class CurrentPriceRRPacketPreflight:
    status: CurrentPriceRRStatus
    required: bool
    reason: str
    fact_present: bool
    numeric_path_present: bool
    expected_value: float | None
    fact_value: float | None
    registry_value: float | None
    semantic_type: str | None
    unit: str | None
    canonical_display_value: str | None

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


def current_price_rr_packet_preflight(
    stock: dict[str, object],
) -> CurrentPriceRRPacketPreflight:
    """Classify current-price RR as unavailable by contract or missing by bug."""
    current = _mapping(_mapping(stock.get("monitoring_state")).get("current"))
    structure = _mapping(current.get("price_structure"))
    risk_reward = _mapping(structure.get("risk_reward"))
    expected_value = _number(_mapping(risk_reward.get("current_price")).get("ratio"))
    if risk_reward.get("available") is not True or expected_value is None:
        reason = str(
            risk_reward.get("blocking_reason")
            or risk_reward.get("reason")
            or "current_price_rr_unavailable"
        )
        return CurrentPriceRRPacketPreflight(
            status="UNAVAILABLE_BY_CONTRACT",
            required=False,
            reason=reason,
            fact_present=False,
            numeric_path_present=False,
            expected_value=expected_value,
            fact_value=None,
            registry_value=None,
            semantic_type=None,
            unit=None,
            canonical_display_value=None,
        )

    fact = next(
        (
            item
            for item in stock.get("fact_catalog", [])
            if isinstance(item, dict)
            and item.get("fact_id") == CURRENT_PRICE_RR_FACT_ID
        ),
        None,
    )
    if fact is None:
        return CurrentPriceRRPacketPreflight(
            status="BUG_MISSING_FACT",
            required=True,
            reason="calculated_current_price_rr_not_canonicalized",
            fact_present=False,
            numeric_path_present=False,
            expected_value=expected_value,
            fact_value=None,
            registry_value=None,
            semantic_type=None,
            unit=None,
            canonical_display_value=None,
        )
    fact_value = _number(_mapping(fact.get("fields")).get("ratio"))
    if fact_value != expected_value:
        return CurrentPriceRRPacketPreflight(
            status="BUG_INVALID_FACT",
            required=True,
            reason="canonical_rr_value_does_not_match_monitoring_state",
            fact_present=True,
            numeric_path_present=False,
            expected_value=expected_value,
            fact_value=fact_value,
            registry_value=None,
            semantic_type=None,
            unit=None,
            canonical_display_value=None,
        )

    registry = next(
        (
            item
            for item in stock.get("numeric_registry", [])
            if isinstance(item, dict)
            and item.get("fact_id") == CURRENT_PRICE_RR_FACT_ID
            and item.get("field_path") == CURRENT_PRICE_RR_FIELD_PATH
        ),
        None,
    )
    if registry is None:
        return CurrentPriceRRPacketPreflight(
            status="BUG_MISSING_NUMERIC_PATH",
            required=True,
            reason="canonical_rr_not_registered",
            fact_present=True,
            numeric_path_present=False,
            expected_value=expected_value,
            fact_value=fact_value,
            registry_value=None,
            semantic_type=None,
            unit=None,
            canonical_display_value=None,
        )
    registry_value = _number(registry.get("value"))
    semantic_type = str(registry.get("semantic_type") or "") or None
    unit = str(registry.get("unit") or "") or None
    display = str(registry.get("canonical_display_value") or "") or None
    if (
        registry_value != expected_value
        or semantic_type != CURRENT_PRICE_RR_SEMANTIC
        or unit != "x"
        or registry.get("registered") is not True
        or registry.get("prose_allowed") is not True
        or display is None
    ):
        return CurrentPriceRRPacketPreflight(
            status="BUG_INVALID_NUMERIC_PATH",
            required=True,
            reason="rr_registry_semantic_unit_or_value_mismatch",
            fact_present=True,
            numeric_path_present=True,
            expected_value=expected_value,
            fact_value=fact_value,
            registry_value=registry_value,
            semantic_type=semantic_type,
            unit=unit,
            canonical_display_value=display,
        )
    return CurrentPriceRRPacketPreflight(
        status="READY",
        required=True,
        reason="current_price_rr_numeric_path_complete",
        fact_present=True,
        numeric_path_present=True,
        expected_value=expected_value,
        fact_value=fact_value,
        registry_value=registry_value,
        semantic_type=semantic_type,
        unit=unit,
        canonical_display_value=display,
    )
