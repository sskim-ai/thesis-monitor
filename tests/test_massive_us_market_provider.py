from datetime import date, datetime, timezone
import asyncio
import json
from pathlib import Path

import httpx
import pytest

from app.providers.massive_us_market_provider import (
    MassiveUsMarketProvider,
    massive_reference_session_age,
)
from app.services.massive_shadow_telemetry_service import (
    build_massive_shadow_observation,
    classify_massive_readiness,
)


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


def test_reference_cache_reuses_previous_trading_day_without_network(
    tmp_path: Path,
) -> None:
    cache = tmp_path / "reference" / f"us_active_{SESSION}.json"
    cache.parent.mkdir(parents=True)
    cache.write_text(
        json.dumps(
            {
                "request_date": str(SESSION),
                "response_sha256": "b" * 64,
                "rows": [_reference("A")],
            }
        )
    )
    provider = MassiveUsMarketProvider(api_key=None, cache_dir=tmp_path)

    result = asyncio.run(provider.reference_tickers(date(2026, 8, 17)))

    assert result["cache_age_calendar_days"] == 3
    assert result["cache_age_trading_days"] == 1
    assert result["cache_reused_for"] == "2026-08-17"


def test_reference_cache_older_than_one_trading_day_window_is_rejected(
    tmp_path: Path,
) -> None:
    cache = tmp_path / "reference" / f"us_active_{SESSION}.json"
    cache.parent.mkdir(parents=True)
    cache.write_text(
        json.dumps(
            {
                "request_date": str(SESSION),
                "response_sha256": "b" * 64,
                "rows": [_reference("A")],
            }
        )
    )
    provider = MassiveUsMarketProvider(api_key=None, cache_dir=tmp_path)

    with pytest.raises(RuntimeError, match="not configured"):
        asyncio.run(provider.reference_tickers(date(2026, 8, 18)))


def test_reference_cache_age_uses_xnys_sessions_across_us_holiday() -> None:
    assert massive_reference_session_age(date(2026, 7, 2), date(2026, 7, 6)) == 1


def test_rate_limit_headers_are_recorded_without_credentials(tmp_path: Path) -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            headers={
                "X-RateLimit-Limit": "5",
                "X-RateLimit-Remaining": "4",
                "X-Request-Id": "private-request-id",
            },
            json=_grouped([{"T": "A", "c": 10, "v": 2}]),
        )

    provider = MassiveUsMarketProvider(
        api_key="secret-test-key",
        base_url="https://api.example.test",
        cache_dir=tmp_path,
        transport=httpx.MockTransport(handler),
    )

    result = asyncio.run(provider.grouped_daily(SESSION))

    assert result["http_metadata"]["rate_limit_headers"] == {
        "x-ratelimit-limit": "5",
        "x-ratelimit-remaining": "4",
    }
    assert "secret-test-key" not in json.dumps(result)
    assert "private-request-id" not in json.dumps(result)


def test_massive_collect_marks_adjusted_volume_as_audit_only(tmp_path: Path) -> None:
    provider = MassiveUsMarketProvider(api_key="test", cache_dir=tmp_path)
    provider.grouped_daily = lambda requested, refresh=False: _async_value(  # type: ignore[method-assign]
        {
            "request_date": str(requested),
            "response_sha256": "a" * 64,
            "payload": _grouped(
                [{"T": "A", "c": 11 if requested == SESSION else 10, "v": 2.5}]
            ),
        }
    )
    provider.reference_tickers = lambda requested, refresh=False: _async_value(  # type: ignore[method-assign]
        {
            "request_date": str(requested),
            "response_sha256": "b" * 64,
            "rows": [_reference("A")],
        }
    )

    section = asyncio.run(
        provider.collect(session_date=SESSION, previous_session_date=PREVIOUS)
    )

    assert section.breadth is not None
    assert section.breadth.total_trading_volume == 2.5
    assert section.quality.volume_semantics == "split_adjusted_aggregate_volume"
    assert section.quality.trading_value_semantics == (
        "deterministic_close_times_adjusted_volume_estimate"
    )


async def _async_value(value: object) -> object:
    return value


@pytest.mark.parametrize(
    ("hour", "minute", "complete", "expected"),
    [
        (8, 5, True, "READY_AT_0805"),
        (8, 10, True, "LATE_BUT_BEFORE_0815"),
        (8, 16, True, "LATE_AFTER_0815"),
        (8, 5, False, "INCOMPLETE"),
    ],
)
def test_shadow_readiness_classification(
    hour: int, minute: int, complete: bool, expected: str
) -> None:
    observed = datetime(2026, 8, 17, hour, minute, tzinfo=timezone.utc).astimezone()
    seoul_observed = datetime(2026, 8, 17, hour, minute, tzinfo=timezone.utc)
    if seoul_observed.utcoffset() == timezone.utc.utcoffset(None):
        # Build the asserted clock directly in the service timezone.
        from zoneinfo import ZoneInfo

        observed = datetime(2026, 8, 17, hour, minute, tzinfo=ZoneInfo("Asia/Seoul"))

    assert classify_massive_readiness(
        observed_at=observed,
        complete=complete,
    ) == expected


def test_shadow_observation_preserves_cache_age_and_counts(tmp_path: Path) -> None:
    provider = MassiveUsMarketProvider(api_key="test", cache_dir=tmp_path)
    provider.grouped_daily = lambda requested, refresh=False: _async_value(  # type: ignore[method-assign]
        {
            "request_date": str(requested),
            "response_sha256": "a" * 64,
            "payload": _grouped(
                [{"T": "A", "c": 11 if requested == SESSION else 10, "v": 2.5}]
            ),
        }
    )
    provider.reference_tickers = lambda requested, refresh=False: _async_value(  # type: ignore[method-assign]
        {
            "request_date": str(requested),
            "response_sha256": "b" * 64,
            "rows": [_reference("A")],
        }
    )
    section = asyncio.run(
        provider.collect(session_date=SESSION, previous_session_date=PREVIOUS)
    )
    current = asyncio.run(provider.grouped_daily(SESSION))
    previous = asyncio.run(provider.grouped_daily(PREVIOUS))
    reference = {
        "request_date": str(PREVIOUS),
        "response_sha256": "b" * 64,
        "rows": [_reference("A")],
    }

    observation = build_massive_shadow_observation(
        section=section,
        current_envelope=current,
        previous_envelope=previous,
        reference_envelope=reference,
        observed_at=datetime(2026, 8, 17, 8, 5, tzinfo=timezone.utc),
    )

    assert observation.grouped_row_count == 1
    assert observation.eligible_count == 1
    assert observation.reference_cache_age_calendar_days == 1
    assert observation.reference_cache_age_trading_days == 1
