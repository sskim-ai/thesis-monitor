from __future__ import annotations

from dataclasses import dataclass


CONTRACT_VERSION = "night-futures-user-visibility-v1"
SESSION_DATE_CONVENTION_PENDING = "SESSION_DATE_CONVENTION_PENDING"


@dataclass(frozen=True)
class NightFuturesVisibility:
    visible: bool
    suppression_reason: str | None


def night_futures_user_facing_visibility(
    market_scope: str,
) -> NightFuturesVisibility:
    """Return the temporary user-facing visibility decision for night futures."""
    if market_scope.strip().lower() == "us":
        return NightFuturesVisibility(
            visible=False,
            suppression_reason=SESSION_DATE_CONVENTION_PENDING,
        )
    return NightFuturesVisibility(visible=True, suppression_reason=None)
