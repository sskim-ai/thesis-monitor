import asyncio
from collections.abc import Sequence
from datetime import date, datetime, timezone

import httpx
from sqlmodel import Session

from app.config import get_settings
from app.schemas.thesis import (
    HistoricalPricePoint,
    PriceContext,
    PriceDecisionContext,
    PricePeriodSummary,
)
from app.services.market_session import market_session_for_ticker
from app.services.provider_telemetry_service import ProviderTelemetryService


PERIOD_COUNTS = {
    "daily": 500,
    "weekly": 300,
    "monthly": 100,
}


def _number(value: object) -> float | None:
    if isinstance(value, (int, float)):
        return float(value)
    return None


def _summarize_bars(requested_count: int, bars: Sequence[dict[str, object]]) -> PricePeriodSummary:
    closes = [_number(bar.get("close")) for bar in bars]
    closes = [value for value in closes if value is not None]
    highs = [_number(bar.get("high")) for bar in bars]
    highs = [value for value in highs if value is not None]
    lows = [_number(bar.get("low")) for bar in bars]
    lows = [value for value in lows if value is not None]
    latest = bars[-1] if bars else {}
    latest_close = closes[-1] if closes else None
    previous_close = closes[-2] if len(closes) >= 2 else None

    period_return = None
    if len(closes) >= 2 and closes[0] != 0:
        period_return = round((closes[-1] / closes[0] - 1) * 100, 2)

    range_position = None
    if latest_close is not None and highs and lows:
        range_low = min(lows)
        range_high = max(highs)
        if range_high > range_low:
            range_position = round((latest_close - range_low) / (range_high - range_low) * 100, 2)

    return PricePeriodSummary(
        requested_count=requested_count,
        actual_count=len(bars),
        latest_date=str(latest.get("date")) if latest.get("date") else None,
        previous_close=previous_close,
        latest_close=latest_close,
        latest_high=_number(latest.get("high")),
        latest_low=_number(latest.get("low")),
        period_return_pct=period_return,
        range_position_pct=range_position,
    )


class OhlcvClient:
    def __init__(self, transport: httpx.AsyncBaseTransport | None = None) -> None:
        self.settings = get_settings()
        self.transport = transport

    async def _request_period(
        self,
        client: httpx.AsyncClient,
        ticker: str,
        period: str,
        count: int,
    ) -> tuple[PricePeriodSummary, list[dict[str, object]]]:
        last_error: Exception | None = None
        attempts = max(1, self.settings.monitor_retry_attempts)
        for attempt in range(attempts):
            try:
                response = await client.get(
                    "/ohlcv",
                    params={
                        "symbol": ticker,
                        "periods": period,
                        "count": count,
                        "include_indicators": "true",
                        "indicator_limit": 1,
                        "adjusted": "true",
                    },
                )
                response.raise_for_status()
                payload = response.json()
                bars = payload.get("periods", {}).get(period, [])
                if not isinstance(bars, list):
                    bars = []
                return _summarize_bars(count, bars), bars
            except (httpx.HTTPError, ValueError) as exc:
                last_error = exc
                if attempt + 1 < attempts:
                    delay = self.settings.monitor_retry_base_seconds * (2**attempt)
                    if delay > 0:
                        await asyncio.sleep(delay)
        assert last_error is not None
        raise last_error

    async def fetch_price_context(
        self,
        ticker: str,
        as_of: datetime | None = None,
        session: Session | None = None,
    ) -> PriceContext:
        api_key = self.settings.ohlcv_api_key or self.settings.action_api_key
        headers = {"X-API-Key": api_key} if api_key else {}
        context = PriceContext()
        async with httpx.AsyncClient(
            base_url=self.settings.ohlcv_base_url.rstrip("/"),
            headers=headers,
            timeout=self.settings.ohlcv_timeout_seconds,
            transport=self.transport,
        ) as client:
            for period, count in PERIOD_COUNTS.items():
                started_at = datetime.now(timezone.utc)
                try:
                    summary, bars = await self._request_period(
                        client, ticker, period, count
                    )
                    context.periods[period] = summary
                    if period in {"daily", "weekly"}:
                        for bar in bars:
                            close = _number(bar.get("close"))
                            raw_date = bar.get("date")
                            if close is None or close <= 0 or not raw_date:
                                continue
                            try:
                                bar_date = date.fromisoformat(str(raw_date)[:10])
                            except ValueError:
                                continue
                            point = HistoricalPricePoint(date=bar_date, close=close)
                            if period == "daily":
                                context.daily_history.append(point)
                            else:
                                context.valuation_history.append(point)
                    if session is not None:
                        ProviderTelemetryService().record(
                            session,
                            provider="ohlcv_analyst",
                            endpoint=f"ohlcv_{period}",
                            ticker=ticker,
                            started_at=started_at,
                            status="success",
                        )
                except (httpx.HTTPError, ValueError) as exc:
                    context.warnings.append(f"{period}: {type(exc).__name__}")
                    if session is not None:
                        ProviderTelemetryService().record(
                            session,
                            provider="ohlcv_analyst",
                            endpoint=f"ohlcv_{period}",
                            ticker=ticker,
                            started_at=started_at,
                            status="failed",
                            error_type=type(exc).__name__,
                            error_reason="ohlcv_request_failed",
                        )
        context.available = any(item.actual_count > 0 for item in context.periods.values())
        daily = context.periods.get("daily")
        session = market_session_for_ticker(ticker, as_of)
        latest_date = daily.latest_date if daily else None
        is_live_bar = (
            session.session == "open"
            and latest_date == session.market_date.isoformat()
        )
        context.decision = PriceDecisionContext(
            current_price=daily.latest_close if daily else None,
            currency="KRW" if ticker.isdigit() else "USD",
            price_as_of=latest_date,
            price_basis="intraday" if is_live_bar else "close" if latest_date else "unavailable",
            market_session=session.session,
            assessment_state="provisional" if is_live_bar else "final",
        )
        return context
