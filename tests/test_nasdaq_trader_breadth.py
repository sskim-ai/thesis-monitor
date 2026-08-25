from __future__ import annotations

import asyncio
from datetime import UTC, date, datetime

import httpx
import pytest

from app.providers.nasdaq_trader_breadth_provider import (
    NasdaqTraderBreadthProvider,
    parse_nasdaq_daily_market_file,
)
from app.services.market_context_adapter_service import UsMarketContextAdapter
from app.services.market_cross_section_service import (
    MarketBreadth,
    MarketCrossSection,
    MarketCrossSectionQuality,
    MarketScopedBreadth,
)


RETRIEVED_AT = datetime(2026, 8, 25, 23, 0, tzinfo=UTC)
TARGET = date(2026, 8, 20)
CSV = (
    '"Date","N100","Advances","Declines","Unchanged"\r\n'
    "8/19/2026 0:00:00,29426.02,2932.00,2110.00,264.00\r\n"
    "8/20/2026 0:00:00,29213.16,1761.00,3252.00,266.00\r\n"
).encode()


def test_parse_exact_completed_session_and_derived_relations() -> None:
    result = parse_nasdaq_daily_market_file(
        CSV,
        target_session=TARGET,
        retrieved_at=RETRIEVED_AT,
        source_url="https://www.nasdaqtrader.test/daily2026.csv",
        source_last_modified="Tue, 25 Aug 2026 14:30:04 GMT",
        source_etag='"fixture"',
    )

    assert result.publication_state == "AVAILABLE_CURRENT"
    observation = result.observation
    assert observation is not None
    assert observation.source_scope == "NASDAQ_LISTED_ISSUES"
    assert observation.advances == 1761
    assert observation.declines == 3252
    assert observation.unchanged == 266
    assert observation.participation_denominator == 5279
    assert observation.eligible_issue_count is None
    assert observation.net_advances == -1491
    assert observation.advance_share == pytest.approx(1761 / 5279)
    assert observation.decline_share == pytest.approx(3252 / 5279)
    assert observation.advance_decline_ratio == pytest.approx(1761 / 3252)


def test_exact_session_missing_remains_publication_pending() -> None:
    result = parse_nasdaq_daily_market_file(
        CSV,
        target_session=date(2026, 8, 24),
        retrieved_at=RETRIEVED_AT,
        source_url="https://www.nasdaqtrader.test/daily2026.csv",
    )

    assert result.publication_state == "PUBLICATION_PENDING"
    assert result.observation is None
    assert result.latest_available_session == TARGET
    assert result.denial_reason == "exact_session_not_published"


def test_incomplete_session_is_never_promoted() -> None:
    payload = CSV + b"8/25/2026 0:00:00,29000,2000,2000,100\r\n"
    retrieved_during_session = datetime(2026, 8, 25, 18, 0, tzinfo=UTC)
    result = parse_nasdaq_daily_market_file(
        payload,
        target_session=date(2026, 8, 25),
        retrieved_at=retrieved_during_session,
        source_url="https://www.nasdaqtrader.test/daily2026.csv",
    )

    assert result.publication_state == "PUBLICATION_PENDING"
    assert result.denial_reason == "target_session_not_completed"


@pytest.mark.parametrize(
    "payload",
    [
        b'Date,Advances,Declines\n8/20/2026 0:00:00,1,2\n',
        b'Date,Advances,Declines,Unchanged\n,1,2,3\n',
        b'Date,Advances,Declines,Unchanged\n8/20/2026 0:00:00,1.5,2,3\n',
        (
            b'Date,Advances,Declines,Unchanged\n'
            b'8/20/2026 0:00:00,1,2,3\n'
            b'8/20/2026 0:00:00,1,2,3\n'
        ),
    ],
)
def test_malformed_file_fails_closed(payload: bytes) -> None:
    with pytest.raises(ValueError):
        parse_nasdaq_daily_market_file(
            payload,
            target_session=TARGET,
            retrieved_at=RETRIEVED_AT,
            source_url="https://www.nasdaqtrader.test/daily2026.csv",
        )


def test_zero_declines_suppresses_ad_ratio() -> None:
    payload = (
        b"Date,Advances,Declines,Unchanged\n"
        b"8/20/2026 0:00:00,10,0,2\n"
    )
    result = parse_nasdaq_daily_market_file(
        payload,
        target_session=TARGET,
        retrieved_at=RETRIEVED_AT,
        source_url="https://www.nasdaqtrader.test/daily2026.csv",
    )

    assert result.observation is not None
    assert result.observation.advance_decline_ratio is None


def test_official_provider_fetches_one_year_file() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(
            200,
            content=CSV,
            headers={"last-modified": "Tue, 25 Aug 2026 14:30:04 GMT"},
        )

    provider = NasdaqTraderBreadthProvider(
        base_url="https://www.nasdaqtrader.test",
        timeout_seconds=1,
        transport=httpx.MockTransport(handler),
    )
    result, payload = asyncio.run(
        provider.collect(session_date=TARGET, retrieved_at=RETRIEVED_AT)
    )

    assert result.publication_state == "AVAILABLE_CURRENT"
    assert payload == CSV
    assert [request.url.path for request in requests] == [
        "/dynamic/dailyfiles/daily2026.csv"
    ]


def test_common_adapter_preserves_nasdaq_scope_and_provenance() -> None:
    breadth = MarketBreadth(
        eligible_count=5279,
        advance_count=1761,
        decline_count=3252,
        unchanged_count=266,
        advance_ratio=1761 / 5279,
        ad_ratio=1761 / 3252,
        median_return_pct=None,
        equal_weight_return_pct=None,
        positive_return_pct=1761 / 5279 * 100,
        negative_return_pct=3252 / 5279 * 100,
        total_trading_volume=None,
        total_trading_value=None,
    )
    section = MarketCrossSection(
        market="US",
        session_date=TARGET,
        as_of=RETRIEVED_AT,
        breadth=breadth,
        breadth_by_scope=[
            MarketScopedBreadth(scope="NASDAQ_LISTED_ISSUES", breadth=breadth)
        ],
        quality=MarketCrossSectionQuality(
            provider="NASDAQ_TRADER_YTD",
            provider_role="official_primary_supplemental",
            coverage="full",
            freshness="fresh",
            universe_version="nasdaq-listed-issues-official-v1",
            raw_count=5279,
            eligible_count=5279,
        ),
        source_payload_sha256="a" * 64,
    )

    context = UsMarketContextAdapter().normalize(
        assessment_date=date(2026, 8, 21),
        as_of=RETRIEVED_AT,
        cutoff=RETRIEVED_AT,
        fact_catalog=[],
        cross_section=section,
        provider_publication_state="PROVIDER_COMPLETE",
    )

    assert context.breadth_by_scope[0].scope == "NASDAQ_LISTED_ISSUES"
    assert context.market_flows == []
    relations = {item.metric: item for item in context.deterministic_relations}
    assert relations["net_advances"].result == -1491
    assert relations["advance_share"].input_refs == [
        "cross-section:NASDAQ_TRADER_YTD:breadth"
    ]
    assert relations["advance_decline_ratio"].result == pytest.approx(1761 / 3252)
