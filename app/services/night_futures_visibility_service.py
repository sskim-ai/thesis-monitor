from __future__ import annotations

from dataclasses import dataclass
from app.services.official_night_market_eligibility_service import night_market_eligibility


CONTRACT_VERSION = "night-futures-user-visibility-v1"
SESSION_DATE_CONVENTION_PENDING = "SESSION_DATE_CONVENTION_PENDING"


@dataclass(frozen=True)
class NightFuturesVisibility:
    visible: bool
    suppression_reason: str | None


def night_futures_user_facing_visibility(
    market_scope: str,
    *, context: dict | None = None,
) -> NightFuturesVisibility:
    """Final-night US visibility requires the source-owned typed context."""
    if market_scope.strip().lower() == "us":
        source = context or {}
        session = source.get("session") or {}
        if any(night_market_eligibility(
            row, market="us", assessment_date=session.get("assessment_date"),
            completed_session_date=session.get("latest_completed_regular_session_date"),
        )["eligible"] for row in source.get("night_futures") or []):
            return NightFuturesVisibility(visible=True, suppression_reason=None)
        return NightFuturesVisibility(
            visible=False,
            suppression_reason=SESSION_DATE_CONVENTION_PENDING,
        )
    return NightFuturesVisibility(visible=True, suppression_reason=None)
