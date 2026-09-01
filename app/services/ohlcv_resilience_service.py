from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from enum import StrEnum

import httpx
from pydantic import BaseModel, ConfigDict


class OhlcvServiceHealth(StrEnum):
    READY = "READY"
    DEGRADED = "DEGRADED"
    UNAVAILABLE = "UNAVAILABLE"


class OhlcvServiceHealthResult(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    state: OhlcvServiceHealth
    process_alive: bool
    transport_reachable: bool
    data_endpoint_functional: bool
    latest_expected_completed_bar_available: bool
    observed_daily_bar: str | None = None
    expected_daily_bar: str | None = None
    attempt_count: int
    failure_classes: tuple[str, ...] = ()
    checked_at: str


async def probe_ohlcv_service(
    *,
    base_url: str,
    api_key: str,
    symbol: str,
    expected_daily_bar: str | None,
    attempts: int = 3,
    timeout_seconds: float = 5.0,
    retry_base_seconds: float = 0.25,
    transport: httpx.AsyncBaseTransport | None = None,
) -> OhlcvServiceHealthResult:
    bounded_attempts = max(1, min(attempts, 5))
    failures: list[str] = []
    transport_reachable = False
    process_alive = False
    observed_daily_bar = None
    for attempt in range(bounded_attempts):
        try:
            async with httpx.AsyncClient(
                base_url=base_url.rstrip("/"),
                headers={"X-API-Key": api_key} if api_key else {},
                timeout=timeout_seconds,
                transport=transport,
            ) as client:
                health = await client.get("/health")
                health.raise_for_status()
                process_alive = True
                transport_reachable = True
                response = await client.get(
                    "/ohlcv",
                    params={
                        "symbol": symbol,
                        "periods": "daily",
                        "count": 1,
                        "include_indicators": "false",
                        "indicator_limit": 0,
                        "adjusted": "true",
                    },
                )
                response.raise_for_status()
                payload = response.json()
                rows = payload.get("periods", {}).get("daily", [])
                if not isinstance(rows, list) or not rows or not isinstance(rows[-1], dict):
                    raise ValueError("ohlcv_data_probe_empty")
                observed_daily_bar = str(rows[-1].get("date") or "")[:10] or None
                expected_available = (
                    expected_daily_bar is None or observed_daily_bar == expected_daily_bar
                )
                return OhlcvServiceHealthResult(
                    state=(
                        OhlcvServiceHealth.READY
                        if expected_available
                        else OhlcvServiceHealth.DEGRADED
                    ),
                    process_alive=True,
                    transport_reachable=True,
                    data_endpoint_functional=True,
                    latest_expected_completed_bar_available=expected_available,
                    observed_daily_bar=observed_daily_bar,
                    expected_daily_bar=expected_daily_bar,
                    attempt_count=attempt + 1,
                    failure_classes=tuple(dict.fromkeys(failures)),
                    checked_at=datetime.now(UTC).isoformat(),
                )
        except (httpx.HTTPError, ValueError) as exc:
            failures.append(type(exc).__name__)
            if attempt + 1 < bounded_attempts and retry_base_seconds > 0:
                await asyncio.sleep(retry_base_seconds * (2**attempt))
    return OhlcvServiceHealthResult(
        state=(
            OhlcvServiceHealth.DEGRADED if transport_reachable else OhlcvServiceHealth.UNAVAILABLE
        ),
        process_alive=process_alive,
        transport_reachable=transport_reachable,
        data_endpoint_functional=False,
        latest_expected_completed_bar_available=False,
        observed_daily_bar=observed_daily_bar,
        expected_daily_bar=expected_daily_bar,
        attempt_count=bounded_attempts,
        failure_classes=tuple(dict.fromkeys(failures)),
        checked_at=datetime.now(UTC).isoformat(),
    )
