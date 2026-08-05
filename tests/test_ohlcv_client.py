import json

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
    assert context.periods["weekly"].actual_count == 240
    assert context.periods["monthly"].actual_count == 84
