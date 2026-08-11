import json
from datetime import datetime
from zoneinfo import ZoneInfo

import httpx
import pytest

from app.services.ohlcv_client import OhlcvClient


@pytest.mark.anyio
async def test_ohlcv_client_requests_each_period_and_accepts_shorter_history() -> None:
    requested: dict[str, int] = {}
    actual_counts = {"daily": 420, "weekly": 240, "monthly": 84}

    def handler(request: httpx.Request) -> httpx.Response:
        period = request.url.params["periods"]
        count = int(request.url.params["count"])
        requested[period] = count
        bars = [
            {
                "date": f"2026-01-{(index % 28) + 1:02d}",
                "open": 100 + index,
                "high": 102 + index,
                "low": 98 + index,
                "close": 101 + index,
                "volume": 1000,
                "indicators": {},
            }
            for index in range(actual_counts[period])
        ]
        return httpx.Response(
            200,
            content=json.dumps({"periods": {period: bars}}).encode(),
            headers={"Content-Type": "application/json"},
        )

    context = await OhlcvClient(transport=httpx.MockTransport(handler)).fetch_price_context("NVDA")

    assert requested == {"daily": 500, "weekly": 300, "monthly": 100}
    assert context.available is True
    assert context.periods["daily"].actual_count == 420
    assert context.periods["daily"].previous_close == 519
    assert context.periods["daily"].latest_close == 520
    assert context.periods["daily"].latest_high == 521
    assert context.periods["daily"].latest_low == 517
    assert context.periods["weekly"].actual_count == 240
    assert context.periods["monthly"].actual_count == 84


@pytest.mark.anyio
async def test_us_premarket_uses_latest_completed_regular_close_date() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        period = request.url.params["periods"]
        bars = [
            {
                "date": "2026-08-11",
                "open": 100,
                "high": 101,
                "low": 99,
                "close": 100,
                "volume": 1_000,
                "indicators": {},
            }
        ]
        return httpx.Response(200, json={"periods": {period: bars}})

    context = await OhlcvClient(
        transport=httpx.MockTransport(handler)
    ).fetch_price_context(
        "GOOGL",
        as_of=datetime(2026, 8, 11, 17, 20, tzinfo=ZoneInfo("Asia/Seoul")),
    )

    assert context.decision.market_session == "pre_market"
    assert context.decision.price_basis == "close"
    assert context.decision.exchange_trade_date == "2026-08-10"
    assert context.decision.latest_completed_regular_session_date == "2026-08-10"
