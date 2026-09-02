from __future__ import annotations

import asyncio
from datetime import UTC, datetime

import httpx
import pytest

from app.config import get_settings
from app.macro.providers.fred import FRED_SERIES, FredProvider


def test_nominal_treasury_curve_uses_official_fred_series() -> None:
    assert {"DGS3", "DGS5", "DGS10", "DGS30"} <= FRED_SERIES.keys()
    assert all(FRED_SERIES[series] == ("rates", "percent", "daily") for series in (
        "DGS3",
        "DGS5",
        "DGS10",
        "DGS30",
    ))


def test_fred_collects_immediately_previous_valid_observation_first(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("FRED_API_KEY", "test-key")
    get_settings.cache_clear()

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "observations": [
                    {
                        "date": "2026-09-01",
                        "value": "4.21",
                        "realtime_start": "2026-09-02",
                        "realtime_end": "2026-09-02",
                    },
                    {"date": "2026-08-31", "value": "."},
                    {
                        "date": "2026-08-28",
                        "value": "4.17",
                        "realtime_start": "2026-09-02",
                        "realtime_end": "2026-09-02",
                    },
                ]
            },
            request=request,
        )

    result = asyncio.run(
        FredProvider(transport=httpx.MockTransport(handler)).collect(
            datetime(2026, 9, 2, tzinfo=UTC)
        )
    )

    dgs10 = [item for item in result.observations if item.series_code == "DGS10"]
    assert [item.observed_at.date().isoformat() for item in dgs10] == [
        "2026-08-28",
        "2026-09-01",
    ]
    assert [item.value for item in dgs10] == [4.17, 4.21]
    assert result.warnings == []
    get_settings.cache_clear()
