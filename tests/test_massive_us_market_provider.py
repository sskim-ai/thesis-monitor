from datetime import date
import asyncio
import json
from pathlib import Path

import httpx
import pytest

from app.providers.massive_us_market_provider import MassiveUsMarketProvider


SESSION = date(2026, 8, 14)
PREVIOUS = date(2026, 8, 13)


def _grouped(rows: list[dict[str, object]]) -> dict[str, object]:
    return {"status": "OK", "adjusted": True, "resultsCount": len(rows), "results": rows}


def _envelope(payload: dict[str, object]) -> dict[str, object]:
    return {"response_sha256": "a" * 64, "payload": payload}


def _reference(ticker: str, security_type: str = "CS") -> dict[str, object]:
    return {
        "ticker": ticker,
        "active": True,
        "market": "stocks",
        "locale": "us",
        "currency_name": "usd",
        "type": security_type,
        "primary_exchange": "XNAS",
        "name": f"{ticker} Inc.",
    }


def test_universe_filters_funds_and_requires_previous_adjusted_close(tmp_path: Path) -> None:
    provider = MassiveUsMarketProvider(api_key="test", cache_dir=tmp_path)
    current = _envelope(
        _grouped(
            [
                {"T": "COMMON", "c": 11, "v": 100},
                {"T": "ETF", "c": 20, "v": 100},
                {"T": "NEW", "c": 5, "v": 100},
            ]
        )
    )
    previous = _envelope(
        _grouped([{"T": "COMMON", "c": 10}, {"T": "ETF", "c": 20}])
    )
    reference = {
        "rows": [_reference("COMMON"), _reference("ETF", "ETF"), _reference("NEW")]
    }

    rows, exclusions = provider.normalize(
        session_date=SESSION, current=current, previous=previous, reference=reference
    )
    values = {row.ticker: row for row in rows}

    assert values["COMMON"].eligible is True
    assert values["ETF"].eligible is False
    assert values["NEW"].eligible is False
    assert exclusions["ineligible_security_type"] == 1
    assert exclusions["previous_adjusted_close_missing"] == 1


def test_grouped_daily_uses_bearer_header_and_atomic_cache(tmp_path: Path) -> None:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json=_grouped([{"T": "A", "c": 10, "v": 2}]))

    provider = MassiveUsMarketProvider(
        api_key="secret-test-key",
        base_url="https://api.example.test",
        cache_dir=tmp_path,
        transport=httpx.MockTransport(handler),
    )
    first = asyncio.run(provider.grouped_daily(SESSION))
    second = asyncio.run(provider.grouped_daily(SESSION))

    assert len(seen) == 1
    assert seen[0].headers["Authorization"] == "Bearer secret-test-key"
    assert "apiKey" not in str(seen[0].url)
    assert first == second
    cache = tmp_path / "us_market_daily" / f"{SESSION}.json"
    assert json.loads(cache.read_text())["request_date"] == str(SESSION)


def test_reference_pagination_is_order_independent(tmp_path: Path) -> None:
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if calls == 1:
            return httpx.Response(
                200,
                json={
                    "results": [_reference("B")],
                    "next_url": "https://api.example.test/v3/reference/tickers?cursor=next",
                },
            )
        return httpx.Response(200, json={"results": [_reference("A")]})

    provider = MassiveUsMarketProvider(
        api_key="test",
        base_url="https://api.example.test",
        cache_dir=tmp_path,
        transport=httpx.MockTransport(handler),
    )
    result = asyncio.run(provider.reference_tickers(SESSION))

    assert calls == 2
    assert {item["ticker"] for item in result["rows"]} == {"A", "B"}
    assert result["page_count"] == 2


def test_rate_limit_and_plan_denial_fail_closed(tmp_path: Path) -> None:
    provider = MassiveUsMarketProvider(
        api_key="test",
        base_url="https://api.example.test",
        cache_dir=tmp_path,
        transport=httpx.MockTransport(lambda _request: httpx.Response(429, json={"error": "limit"})),
    )

    with pytest.raises(httpx.HTTPStatusError):
        asyncio.run(provider.grouped_daily(SESSION))


def test_stale_or_corrupt_cached_session_fails_closed(tmp_path: Path) -> None:
    cache = tmp_path / "us_market_daily" / f"{SESSION}.json"
    cache.parent.mkdir(parents=True)
    cache.write_text(
        json.dumps(
            {
                "request_date": str(PREVIOUS),
                "payload": _grouped([{"T": "A", "c": 10, "v": 2}]),
            }
        )
    )
    provider = MassiveUsMarketProvider(api_key="test", cache_dir=tmp_path)

    with pytest.raises(ValueError, match="date mismatch"):
        asyncio.run(provider.grouped_daily(SESSION))


def test_duplicate_grouped_ticker_fails_closed(tmp_path: Path) -> None:
    provider = MassiveUsMarketProvider(
        api_key="test",
        base_url="https://api.example.test",
        cache_dir=tmp_path,
        transport=httpx.MockTransport(
            lambda _request: httpx.Response(
                200,
                json=_grouped([{"T": "A", "c": 10}, {"T": "A", "c": 11}]),
            )
        ),
    )

    with pytest.raises(ValueError, match="duplicate"):
        asyncio.run(provider.grouped_daily(SESSION))
