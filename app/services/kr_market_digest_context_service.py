from __future__ import annotations

from datetime import date, datetime

from app.services.market_context_adapter_service import (
    NormalizedMarketContext,
    market_context_adapter,
)
from app.services.structured_market_context_service import (
    load_current_cross_section,
    load_structured_market_context,
)


_PUBLICATION_STATE = {
    "AVAILABLE_CURRENT": "PROVIDER_COMPLETE",
    "PUBLICATION_PENDING": "MARKET_COMPLETED_PROVIDER_PENDING",
    "PARTIAL": "PROVIDER_PARTIAL",
    "AVAILABLE_PRIOR_SESSION": "UNAVAILABLE",
    "UNAVAILABLE": "UNAVAILABLE",
}


def load_current_kr_digest_context(
    assessment_date: date,
    *,
    as_of: datetime,
    cutoff: datetime,
) -> NormalizedMarketContext | None:
    """Load the same cached KR cross-section used by the AI market adapter."""
    try:
        envelope = load_structured_market_context(
            "kr",
            assessment_date,
            cutoff=cutoff,
        )
        cross_section = load_current_cross_section(
            "kr",
            assessment_date,
            cutoff=cutoff,
        )
    except (OSError, TypeError, ValueError):
        return None
    if envelope is None or cross_section is None:
        return None
    return market_context_adapter("kr").normalize(
        assessment_date=assessment_date,
        as_of=as_of,
        cutoff=cutoff,
        fact_catalog=[],
        coverage={},
        cross_section=cross_section,
        provider_publication_state=_PUBLICATION_STATE[envelope.publication_state],
    )
