import asyncio
from datetime import date, datetime, timezone
from pathlib import Path

import httpx

from app.jobs.probe_dram_rss import (
    TREND_FORCE_SEMICONDUCTORS_RSS,
    USER_AGENT,
    fetch_live_probe,
    parse_dram_rss,
)


FIXTURE = Path("tests/fixtures/trendforce_semiconductors_rss.xml")


def _fixture_result():
    return parse_dram_rss(
        FIXTURE.read_text(encoding="utf-8"),
        fetched_at=datetime(2026, 8, 12, tzinfo=timezone.utc),
        run_date=date(2026, 8, 12),
    )


def test_daily_express_spot_prices_preserve_product_direction_and_date() -> None:
    result = _fixture_result()

    assert result.status == "ok"
    assert result.entry_count == 7
    assert result.entries[0].title == "Daily Express Aug.11,2026 Spot Market Today"
    assert result.entries[0].summary is not None
    assert result.entries[0].link.endswith("daily-20260811")
    assert result.entries[0].category == "Semiconductors"
    assert result.daily_express_count == 5
    assert result.dram_daily_express_count == 4
    assert result.price_parseable_daily_count == 3
    assert result.dram_price_observation_count == 3
    assert result.representative_product == "DDR4 8G (1Gx8) 3200"
    assert result.representative_product_observation_count == 3
    assert result.representative_product_coverage_pct == 75.0
    observations = {item.source_date: item for item in result.price_observations}
    assert observations[date(2026, 8, 11)].price_usd == 42.14
    assert observations[date(2026, 8, 11)].direction == "up"
    assert observations[date(2026, 8, 10)].direction == "down"
    assert observations[date(2026, 8, 7)].direction == "flat"
    assert all(item.reported_change_pct is None for item in observations.values())


def test_non_dram_and_commentary_only_daily_entries_do_not_create_prices() -> None:
    result = _fixture_result()

    source_titles = {item.source_title for item in result.price_observations}
    assert "Daily Express Aug.6,2026 Spot Market Today" not in source_titles
    assert "Daily Express Aug.5,2026 Spot Market Today" not in source_titles


def test_same_product_change_is_computed_without_linking_other_products() -> None:
    result = _fixture_result()

    assert result.latest_product == "DDR4 8G (1Gx8) 3200"
    assert result.latest_price_usd == 42.14
    assert result.computed_change_abs == 0.24
    assert result.computed_change_pct == 0.572792
    assert result.freshness_lag_calendar_days == 1


def test_different_products_are_not_connected_for_change_calculation() -> None:
    xml = """<rss><channel>
    <item><title>Daily Express Aug.11,2026 Spot Market Today</title>
    <link>https://example.test/1</link><pubDate>Tue, 11 Aug 2026 08:00:00 GMT</pubDate>
    <description>In the DRAM spot market, the average price of DDR5 16G 5600 rises to USD 9.5.</description></item>
    <item><title>Daily Express Aug.10,2026 Spot Market Today</title>
    <link>https://example.test/2</link><pubDate>Mon, 10 Aug 2026 08:00:00 GMT</pubDate>
    <description>In the DRAM spot market, the average price of DDR4 8G 3200 drops to USD 4.0.</description></item>
    </channel></rss>"""

    result = parse_dram_rss(xml, run_date=date(2026, 8, 12))

    assert result.dram_price_observation_count == 2
    assert result.representative_product_observation_count == 1
    assert result.computed_change_abs is None
    assert result.computed_change_pct is None


def test_reported_spot_change_is_preserved_only_when_explicit() -> None:
    xml = """<rss><channel><item>
    <title>Daily Express Aug.11,2026 Spot Market Today</title>
    <link>https://example.test/1</link><pubDate>Tue, 11 Aug 2026 08:00:00 GMT</pubDate>
    <description>In the DRAM spot market, the average price of DDR4 8G 3200 rises by 2.5% to USD 4.1.</description>
    </item></channel></rss>"""

    result = parse_dram_rss(xml, run_date=date(2026, 8, 12))

    assert result.price_observations[0].reported_change_pct == 2.5


def test_contract_news_requires_dram_and_pricing_context() -> None:
    result = _fixture_result()

    assert result.contract_news_count == 1
    news = result.contract_news[0]
    assert news.relevance == "high"
    assert news.reported_change_pct_low == 10
    assert news.reported_change_pct_high == 15
    assert "Launches New" not in news.title


def test_malformed_and_empty_rss_are_gracefully_unavailable() -> None:
    malformed = parse_dram_rss("<rss><channel>", run_date=date(2026, 8, 12))
    empty = parse_dram_rss("<rss><channel /></rss>", run_date=date(2026, 8, 12))

    assert malformed.status == "unavailable"
    assert malformed.reason is not None and malformed.reason.startswith("malformed_xml")
    assert empty.status == "unavailable"
    assert empty.reason == "empty_feed"


def test_live_fetch_uses_only_official_rss_once_with_identifying_user_agent() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, text=FIXTURE.read_text(encoding="utf-8"))

    result = asyncio.run(
        fetch_live_probe(
            transport=httpx.MockTransport(handler),
            run_date=date(2026, 8, 12),
        )
    )

    assert result.status == "ok"
    assert len(requests) == 1
    assert str(requests[0].url) == TREND_FORCE_SEMICONDUCTORS_RSS
    assert requests[0].headers["user-agent"] == USER_AGENT


def test_probe_source_contains_no_price_page_or_dramexchange_target() -> None:
    source = Path("app/jobs/probe_dram_rss.py").read_text(encoding="utf-8").lower()

    assert "trendforce.com/price" not in source
    assert "dramexchange.com" not in source
    assert source.count(TREND_FORCE_SEMICONDUCTORS_RSS.lower()) == 1


def test_http_failure_is_gracefully_unavailable_without_retry_loop() -> None:
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(503, request=request)

    result = asyncio.run(fetch_live_probe(transport=httpx.MockTransport(handler)))

    assert calls == 1
    assert result.status == "unavailable"
    assert result.reason == "rss_fetch_failed:HTTPStatusError"
