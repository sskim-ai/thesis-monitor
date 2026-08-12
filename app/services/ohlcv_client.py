import asyncio
import math
from collections.abc import Sequence
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import httpx
from sqlmodel import Session

from app.config import get_settings
from app.schemas.thesis import (
    HistoricalPricePoint,
    InvestorSupplyContext,
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
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        number = float(value)
        return number if math.isfinite(number) else None
    return None


_SUPPLY_NUMERIC_FIELDS = (
    "foreign_net_buy_qty",
    "institution_net_buy_qty",
    "individual_net_buy_qty",
    "foreign_net_buy_qty_5",
    "institution_net_buy_qty_5",
    "individual_net_buy_qty_5",
    "foreign_net_buy_qty_20",
    "institution_net_buy_qty_20",
    "individual_net_buy_qty_20",
    "foreign_holding_qty",
    "foreign_holding_ratio",
    "supply_score",
    "investor_net_buy_20_diff_ratio",
)

_SUPPLY_TEXT_FIELDS = (
    "supply_quality",
    "supply_quality_detail",
    "supply_primary_signal",
    "supply_foreign_flow_direction_20",
    "supply_institution_flow_direction_20",
    "supply_individual_flow_direction_20",
    "supply_confidence",
    "supply_validation_status",
    "supply_data_scope",
    "investor_net_buy_20_validation_status",
)

_SUPPLY_CONTENT_TEXT_FIELDS = (
    "supply_quality",
    "supply_quality_detail",
    "supply_primary_signal",
    "supply_foreign_flow_direction_20",
    "supply_institution_flow_direction_20",
    "supply_individual_flow_direction_20",
)

_SUPPLY_SIGNAL_FIELDS = (
    "supply_foreign_accumulation",
    "supply_institution_accumulation",
    "supply_individual_accumulation",
    "supply_foreign_institution_joint_accumulation",
    "supply_foreign_reentry_signal",
    "supply_foreign_exit_retail_absorption",
    "supply_foreign_exit_institution_retail_absorption",
    "supply_retail_chasing_warning",
    "supply_institutional_distribution_warning",
)


def _bar_values(bar: dict[str, object]) -> dict[str, object]:
    values = dict(bar)
    investor_flow = bar.get("investor_flow")
    if isinstance(investor_flow, dict):
        values.update(investor_flow)
    indicators = bar.get("indicators")
    if isinstance(indicators, dict):
        values.update(indicators)
    supply_demand = bar.get("supply_demand")
    if isinstance(supply_demand, dict):
        values.update(
            {f"supply_{key}": value for key, value in supply_demand.items()}
        )
    return values


def _investor_supply_context(bars: Sequence[dict[str, object]]) -> InvestorSupplyContext:
    candidates: list[tuple[date, dict[str, object]]] = []
    for bar in bars:
        raw_date = bar.get("date")
        if not raw_date:
            continue
        try:
            bar_date = date.fromisoformat(str(raw_date)[:10])
        except ValueError:
            continue
        values = _bar_values(bar)
        has_numeric = any(_number(values.get(field)) is not None for field in _SUPPLY_NUMERIC_FIELDS)
        has_text = any(
            str(values.get(field) or "").strip() for field in _SUPPLY_CONTENT_TEXT_FIELDS
        )
        has_signal = any(values.get(field) is True for field in _SUPPLY_SIGNAL_FIELDS)
        if has_numeric or has_text or has_signal:
            candidates.append((bar_date, values))
    if not candidates:
        return InvestorSupplyContext()
    bar_date, values = max(candidates, key=lambda item: item[0])

    def quantity(field: str) -> int | None:
        value = _number(values.get(field))
        return int(value) if value is not None else None

    def text(field: str) -> str | None:
        value = str(values.get(field) or "").strip()
        return value or None

    signals = [field.removeprefix("supply_") for field in _SUPPLY_SIGNAL_FIELDS if values.get(field) is True]
    divergence = text("supply_divergence_type")
    if divergence:
        signals.append(f"divergence:{divergence}")
    return InvestorSupplyContext(
        available=True,
        as_of_date=bar_date.isoformat(),
        foreign_net_buy_qty=quantity("foreign_net_buy_qty"),
        institution_net_buy_qty=quantity("institution_net_buy_qty"),
        individual_net_buy_qty=quantity("individual_net_buy_qty"),
        foreign_net_buy_qty_5=quantity("foreign_net_buy_qty_5"),
        institution_net_buy_qty_5=quantity("institution_net_buy_qty_5"),
        individual_net_buy_qty_5=quantity("individual_net_buy_qty_5"),
        foreign_net_buy_qty_20=quantity("foreign_net_buy_qty_20"),
        institution_net_buy_qty_20=quantity("institution_net_buy_qty_20"),
        individual_net_buy_qty_20=quantity("individual_net_buy_qty_20"),
        foreign_holding_qty=quantity("foreign_holding_qty"),
        foreign_holding_ratio=_number(values.get("foreign_holding_ratio")),
        score=_number(values.get("supply_score")),
        quality=text("supply_quality"),
        quality_detail=text("supply_quality_detail"),
        primary_signal=text("supply_primary_signal"),
        foreign_flow_direction_20=text("supply_foreign_flow_direction_20"),
        institution_flow_direction_20=text("supply_institution_flow_direction_20"),
        individual_flow_direction_20=text("supply_individual_flow_direction_20"),
        confidence=text("supply_confidence"),
        validation_status=text("supply_validation_status"),
        data_scope=text("supply_data_scope"),
        investor_20d_validation_status=text("investor_net_buy_20_validation_status"),
        investor_20d_diff_ratio=_number(values.get("investor_net_buy_20_diff_ratio")),
        signals=list(dict.fromkeys(signals)),
    )


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
        *,
        adjusted: bool = True,
        include_indicators: bool = True,
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
                        "include_indicators": str(include_indicators).lower(),
                        "indicator_limit": 1 if include_indicators else 0,
                        "adjusted": str(adjusted).lower(),
                    },
                )
                response.raise_for_status()
                payload = response.json()
                bars = payload.get("periods", {}).get(period, [])
                if not isinstance(bars, list):
                    bars = []
                supply_demand = payload.get("supply_demand")
                if period == "daily" and bars and isinstance(supply_demand, dict):
                    latest_bar = bars[-1]
                    if isinstance(latest_bar, dict):
                        bars[-1] = {**latest_bar, "supply_demand": supply_demand}
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
                    if period == "daily":
                        context.supply = _investor_supply_context(bars)
                    if period == "daily":
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
                            context.daily_history.append(point)
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
            started_at = datetime.now(timezone.utc)
            try:
                _, valuation_bars = await self._request_period(
                    client,
                    ticker,
                    "weekly",
                    PERIOD_COUNTS["weekly"],
                    adjusted=False,
                    include_indicators=False,
                )
                for bar in valuation_bars:
                    close = _number(bar.get("close"))
                    raw_date = bar.get("date")
                    if close is None or close <= 0 or not raw_date:
                        continue
                    try:
                        bar_date = date.fromisoformat(str(raw_date)[:10])
                    except ValueError:
                        continue
                    context.valuation_history.append(
                        HistoricalPricePoint(date=bar_date, close=close)
                    )
                if session is not None:
                    ProviderTelemetryService().record(
                        session,
                        provider="ohlcv_analyst",
                        endpoint="ohlcv_weekly_unadjusted_valuation",
                        ticker=ticker,
                        started_at=started_at,
                        status="success",
                    )
            except (httpx.HTTPError, ValueError) as exc:
                context.warnings.append(
                    f"valuation_history_unadjusted: {type(exc).__name__}"
                )
                if session is not None:
                    ProviderTelemetryService().record(
                        session,
                        provider="ohlcv_analyst",
                        endpoint="ohlcv_weekly_unadjusted_valuation",
                        ticker=ticker,
                        started_at=started_at,
                        status="failed",
                        error_type=type(exc).__name__,
                        error_reason="ohlcv_unadjusted_valuation_request_failed",
                    )
        context.available = any(item.actual_count > 0 for item in context.periods.values())
        daily = context.periods.get("daily")
        session_state = market_session_for_ticker(ticker, as_of)
        observed_at = as_of or datetime.now(timezone.utc)
        if observed_at.tzinfo is None:
            observed_at = observed_at.replace(tzinfo=timezone.utc)
        observed_local = observed_at.astimezone(ZoneInfo(session_state.timezone_name))
        raw_latest_date = daily.latest_date if daily else None
        latest_date = raw_latest_date
        date_shift_days = 0
        if raw_latest_date and session_state.session != "open":
            try:
                parsed_latest = date.fromisoformat(raw_latest_date[:10])
            except ValueError:
                parsed_latest = None
            if (
                parsed_latest is not None
                and parsed_latest > session_state.latest_completed_regular_session_date
            ):
                date_shift_days = (
                    parsed_latest - session_state.latest_completed_regular_session_date
                ).days
                latest_date = session_state.latest_completed_regular_session_date.isoformat()
                daily.latest_date = latest_date
        if date_shift_days:
            context.daily_history = [
                HistoricalPricePoint(
                    date=point.date - timedelta(days=date_shift_days),
                    close=point.close,
                )
                for point in context.daily_history
            ]
            context.valuation_history = [
                HistoricalPricePoint(
                    date=point.date - timedelta(days=date_shift_days),
                    close=point.close,
                )
                for point in context.valuation_history
            ]
        is_live_bar = (
            session_state.session == "open"
            and latest_date == session_state.market_date.isoformat()
        )
        context.decision = PriceDecisionContext(
            current_price=daily.latest_close if daily else None,
            currency="KRW" if ticker.isdigit() else "USD",
            price_as_of=latest_date,
            exchange_trade_date=latest_date,
            latest_completed_regular_session_date=(
                session_state.latest_completed_regular_session_date.isoformat()
            ),
            price_observed_at=observed_local.isoformat(),
            price_observed_timezone=session_state.timezone_name,
            price_basis="intraday" if is_live_bar else "close" if latest_date else "unavailable",
            market_session=session_state.session,
            assessment_state="provisional" if is_live_bar else "final",
        )
        return context
