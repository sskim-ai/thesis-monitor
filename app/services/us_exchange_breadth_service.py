from __future__ import annotations

import os
from datetime import date, datetime
from pathlib import Path

from app.config import get_settings
from app.providers.nasdaq_trader_breadth_provider import (
    NasdaqOfficialBreadthObservation,
    NasdaqTraderBreadthProvider,
)
from app.services.market_cross_section_service import (
    MarketBreadth,
    MarketCrossSection,
    MarketCrossSectionQuality,
    MarketScopedBreadth,
)
from app.services.structured_market_context_service import (
    StructuredMarketContextEnvelope,
    persist_structured_market_context,
)


def _cross_section(
    observation: NasdaqOfficialBreadthObservation,
) -> MarketCrossSection:
    breadth = MarketBreadth(
        eligible_count=observation.participation_denominator,
        advance_count=observation.advances,
        decline_count=observation.declines,
        unchanged_count=observation.unchanged,
        advance_ratio=observation.advance_share,
        ad_ratio=observation.advance_decline_ratio,
        median_return_pct=None,
        equal_weight_return_pct=None,
        positive_return_pct=observation.advance_share * 100,
        negative_return_pct=observation.decline_share * 100,
        total_trading_volume=None,
        total_trading_value=None,
    )
    return MarketCrossSection(
        market="US",
        session_date=observation.session_date,
        as_of=observation.retrieved_at,
        breadth=breadth,
        breadth_by_scope=[
            MarketScopedBreadth(scope=observation.source_scope, breadth=breadth)
        ],
        quality=MarketCrossSectionQuality(
            provider="NASDAQ_TRADER_YTD",
            provider_role="official_primary_supplemental",
            coverage="full",
            freshness="fresh",
            universe_version="nasdaq-listed-issues-official-v1",
            raw_count=observation.participation_denominator,
            eligible_count=observation.participation_denominator,
            excluded_count=0,
            warnings=[
                "Scope is Nasdaq-listed issues, not NYSE or all-US breadth.",
                "The source does not publish a separate eligible-issue denominator.",
            ],
        ),
        source_payload_sha256=observation.source_payload_sha256,
    )


def persist_nasdaq_daily_file(
    payload: bytes,
    *,
    year: int,
    source_sha256: str,
    directory: Path | None = None,
) -> Path:
    root = directory or (
        Path(get_settings().data_dir) / "market-context" / "nasdaq-trader" / "raw"
    )
    path = root / str(year) / f"{source_sha256}.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_bytes(payload)
    os.replace(temporary, path)
    return path


async def collect_and_persist_us_exchange_breadth(
    *,
    session_date: date,
    observed_at: datetime,
) -> dict[str, object]:
    """Collect official Nasdaq breadth without making the US packet dependent on it."""
    settings = get_settings()
    if not settings.nasdaq_us_exchange_breadth_enabled:
        return {"status": "NOT_ENABLED", "packet_continues": True}
    result, payload = await NasdaqTraderBreadthProvider().collect(
        session_date=session_date,
        retrieved_at=observed_at,
    )
    archive_path = persist_nasdaq_daily_file(
        payload,
        year=session_date.year,
        source_sha256=result.source_payload_sha256,
    )
    section = _cross_section(result.observation) if result.observation else None
    envelope = StructuredMarketContextEnvelope(
        market="US",
        session_date=session_date,
        retrieved_at=observed_at,
        provider="NASDAQ_TRADER_YTD",
        publication_state=result.publication_state,
        source_refs=[
            result.source_url,
            f"nasdaq-trader-archive:{archive_path.relative_to(Path(settings.data_dir))}",
        ],
        source_payload_sha256=result.source_payload_sha256,
        cross_section=section,
        data_gaps=(
            []
            if section is not None
            else [
                f"nasdaq_breadth:{result.denial_reason or 'unavailable'}",
                "nyse_breadth_unavailable",
                "us_participant_flow_not_supported",
            ]
        ),
    )
    cache_path = persist_structured_market_context(envelope)
    return {
        "status": result.publication_state,
        "packet_continues": True,
        "session_date": session_date.isoformat(),
        "latest_available_session": (
            result.latest_available_session.isoformat()
            if result.latest_available_session
            else None
        ),
        "source_payload_sha256": result.source_payload_sha256,
        "archive_path": str(archive_path),
        "cache_path": str(cache_path),
        "denial_reason": result.denial_reason,
    }
