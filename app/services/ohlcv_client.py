import asyncio
import hashlib
import math
import time
from collections.abc import Sequence
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import httpx
from sqlmodel import Session

from app.config import get_settings
from app.schemas.thesis import (
    ChartCandleContext,
    ChartTimeframeContext,
    HistoricalPricePoint,
    InvestorSupplyContext,
    PriceContext,
    PriceDecisionContext,
    PricePeriodSummary,
)
from app.services.market_session import market_session_for_ticker
from app.services.kr_investor_flow_service import (
    build_investor_flow_reconciliation,
    serialized_reconciliation_payload,
)
from app.services.kr_price_structure_selective_rollout_service import (
    build_kr_price_structure_runtime_context,
)
from app.services.us_price_structure_selective_rollout_service import (
    build_us_price_structure_runtime_context,
)
from app.services.ohlcv_structure_service import analyze_chart_structure
from app.services.packet_owned_technical_context_service import (
    build_packet_owned_technical_context,
)
from app.services.provider_telemetry_service import ProviderTelemetryService


PERIOD_COUNTS = {
    "daily": 500,
    "weekly": 300,
    "monthly": 100,
}
PRICE_STRUCTURE_PERIOD_COUNTS = {
    "daily": 1200,
    "weekly": 600,
    "monthly": 300,
}
OHLCV_PROVIDER_REQUEST_LIMIT = 1000

_DAILY_BOLLINGER_UPPER = {
    "3_month": "BB_36_1.541_UPPER",
    "5_month": "BB_60_1.541_UPPER",
    "6_month": "BB_50_2.25_UPPER",
    "12_month": "BB_144_1.541_UPPER",
    "24_month": "BB_288_1.541_UPPER",
    "54_month": "BB_300_3.33_UPPER",
}
_UNAVAILABLE_PROVIDER_CHART_FIELDS = ("trading_value_ratio",)


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
    "other_corp_net_buy_qty",
    "domestic_foreign_net_buy_qty",
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
        values.update({f"supply_{key}": value for key, value in supply_demand.items()})
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
        has_numeric = any(
            _number(values.get(field)) is not None for field in _SUPPLY_NUMERIC_FIELDS
        )
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

    signals = [
        field.removeprefix("supply_")
        for field in _SUPPLY_SIGNAL_FIELDS
        if values.get(field) is True
    ]
    divergence = text("supply_divergence_type")
    if divergence:
        signals.append(f"divergence:{divergence}")
    provider_primary_signal = text("supply_primary_signal")
    reconciliation = build_investor_flow_reconciliation(
        bars,
        provider_primary_signal=provider_primary_signal,
    )
    supply = InvestorSupplyContext(
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
        primary_signal=str(reconciliation.get("primary_signal") or "unavailable"),
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
    internal = serialized_reconciliation_payload(reconciliation)
    internal["provider_primary_signal"] = provider_primary_signal
    supply.set_reconciliation_payload(internal)
    return supply


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


def _round(value: float | None) -> float | None:
    return round(value, 6) if value is not None else None


def _chart_timeframe_context(
    timeframe: str,
    bars: Sequence[dict[str, object]],
    summary: PricePeriodSummary,
) -> ChartTimeframeContext:
    latest = _bar_values(bars[-1]) if bars else {}
    open_price = _number(latest.get("open"))
    high = _number(latest.get("high"))
    low = _number(latest.get("low"))
    close = _number(latest.get("close"))
    price_range = high - low if high is not None and low is not None and high > low else None
    body_pct = (
        (close - open_price) / open_price * 100
        if close is not None and open_price not in {None, 0}
        else None
    )
    range_pct = (
        price_range / open_price * 100
        if price_range is not None and open_price not in {None, 0}
        else None
    )
    close_location = (
        (close - low) / price_range * 100
        if close is not None and low is not None and price_range is not None
        else None
    )
    upper_wick = (
        (high - max(open_price, close)) / price_range * 100
        if high is not None
        and open_price is not None
        and close is not None
        and price_range is not None
        else None
    )
    lower_wick = (
        (min(open_price, close) - low) / price_range * 100
        if low is not None
        and open_price is not None
        and close is not None
        and price_range is not None
        else None
    )
    bollinger_upper: dict[str, float] = {}
    bollinger_distance: dict[str, float] = {}
    if timeframe == "daily":
        for label, field in _DAILY_BOLLINGER_UPPER.items():
            value = _number(latest.get(field))
            if value in {None, 0}:
                continue
            bollinger_upper[label] = value
            if close not in {None, 0}:
                bollinger_distance[label] = round((close / value - 1) * 100, 4)
    return ChartTimeframeContext(
        timeframe=timeframe,
        as_of_date=summary.latest_date,
        quality="available" if bars else "unavailable",
        candle=ChartCandleContext(
            open=open_price,
            high=high,
            low=low,
            close=close,
            volume=_number(latest.get("volume")),
            trading_value=_number(latest.get("value")),
            body_pct=_round(body_pct),
            range_pct=_round(range_pct),
            close_location_pct=_round(close_location),
            upper_wick_pct=_round(upper_wick),
            lower_wick_pct=_round(lower_wick),
        ),
        period_return_pct=summary.period_return_pct,
        range_position_pct=summary.range_position_pct,
        bollinger_upper=bollinger_upper,
        bollinger_distance_pct=bollinger_distance,
        volume_ratio_20=_number(latest.get("VOLUME_RATIO_20")),
        rsi_14=_number(latest.get("RSI14")),
        macd=_number(latest.get("MACD")),
        macd_signal=_number(latest.get("MACD_SIGNAL")),
        macd_histogram=_number(latest.get("MACD_HIST")),
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
        acquisition_audit: dict[str, object] | None = None,
    ) -> tuple[PricePeriodSummary, list[dict[str, object]]]:
        last_error: Exception | None = None
        attempts = max(1, min(self.settings.monitor_retry_attempts, 5))
        provider_count = min(count, OHLCV_PROVIDER_REQUEST_LIMIT)
        deadline = time.monotonic() + max(0.1, self.settings.ohlcv_timeout_seconds)
        for attempt in range(attempts):
            if acquisition_audit is not None:
                acquisition_audit["request_count"] = (
                    int(acquisition_audit.get("request_count") or 0) + 1
                )
                if attempt:
                    acquisition_audit["retry_count"] = (
                        int(acquisition_audit.get("retry_count") or 0) + 1
                    )
            try:
                response = await client.get(
                    "/ohlcv",
                    params={
                        "symbol": ticker,
                        "periods": period,
                        "count": provider_count,
                        "include_indicators": str(include_indicators).lower(),
                        "indicator_limit": 1 if include_indicators else 0,
                        "adjusted": str(adjusted).lower(),
                    },
                )
                response.raise_for_status()
                payload = response.json()
                resolved = payload.get("resolved_symbol")
                if isinstance(resolved, dict):
                    resolved_code = str(resolved.get("code") or "").upper()
                    if resolved_code and resolved_code != ticker.upper():
                        raise ValueError("ohlcv_security_identity_mismatch")
                meta = payload.get("meta")
                if (
                    isinstance(meta, dict)
                    and meta.get("adjusted") is not None
                    and bool(meta.get("adjusted")) != adjusted
                ):
                    raise ValueError("ohlcv_adjustment_basis_mismatch")
                bars = payload.get("periods", {}).get(period, [])
                if not isinstance(bars, list):
                    bars = []
                supply_demand = payload.get("supply_demand")
                if period == "daily" and bars and isinstance(supply_demand, dict):
                    latest_bar = bars[-1]
                    if isinstance(latest_bar, dict):
                        bars[-1] = {**latest_bar, "supply_demand": supply_demand}
                if acquisition_audit is not None:
                    acquisition_audit["success_count"] = (
                        int(acquisition_audit.get("success_count") or 0) + 1
                    )
                return _summarize_bars(count, bars), bars
            except ValueError as exc:
                if acquisition_audit is not None:
                    failures = acquisition_audit.setdefault("failure_classes", [])
                    if isinstance(failures, list):
                        failures.append(str(exc) or type(exc).__name__)
                raise
            except httpx.HTTPError as exc:
                last_error = exc
                retryable = isinstance(
                    exc,
                    (
                        httpx.ConnectError,
                        httpx.ConnectTimeout,
                        httpx.ReadTimeout,
                        httpx.RemoteProtocolError,
                    ),
                ) or (isinstance(exc, httpx.HTTPStatusError) and exc.response.status_code >= 500)
                if acquisition_audit is not None:
                    failures = acquisition_audit.setdefault("failure_classes", [])
                    if isinstance(failures, list):
                        failures.append(type(exc).__name__)
                    if isinstance(exc, httpx.ConnectError):
                        key = "connection_error_count"
                    elif isinstance(exc, (httpx.ConnectTimeout, httpx.ReadTimeout)):
                        key = "timeout_count"
                    elif isinstance(exc, httpx.HTTPStatusError) and exc.response.status_code >= 500:
                        key = "server_error_count"
                    else:
                        key = "non_retryable_error_count"
                    acquisition_audit[key] = int(acquisition_audit.get(key) or 0) + 1
                if not retryable or attempt + 1 >= attempts:
                    raise
                jitter_seed = hashlib.sha256(f"{ticker}|{period}|{attempt}".encode()).digest()[0]
                jitter = 0.9 + (jitter_seed / 255) * 0.2
                delay = self.settings.monitor_retry_base_seconds * (2**attempt) * jitter
                if time.monotonic() + delay >= deadline:
                    raise
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
        adjusted_bars: dict[str, list[dict[str, object]]] = {}
        technical_acquisition: dict[str, object] = {
            "started_at": datetime.now(timezone.utc).isoformat(),
            "request_count": 0,
            "success_count": 0,
            "retry_count": 0,
            "connection_error_count": 0,
            "timeout_count": 0,
            "server_error_count": 0,
            "cache_use_count": 0,
            "failure_classes": [],
        }
        price_structure_enabled = (
            self.settings.kr_price_structure_v3_enabled
            if ticker.isdigit()
            else self.settings.us_price_structure_v3_enabled
        )
        period_counts = PRICE_STRUCTURE_PERIOD_COUNTS if price_structure_enabled else PERIOD_COUNTS
        async with httpx.AsyncClient(
            base_url=self.settings.ohlcv_base_url.rstrip("/"),
            headers=headers,
            timeout=self.settings.ohlcv_timeout_seconds,
            transport=self.transport,
        ) as client:
            for period, count in period_counts.items():
                started_at = datetime.now(timezone.utc)
                try:
                    summary, bars = await self._request_period(
                        client,
                        ticker,
                        period,
                        count,
                        acquisition_audit=technical_acquisition,
                    )
                    context.periods[period] = summary
                    adjusted_bars[period] = bars
                    context.chart.timeframes[period] = _chart_timeframe_context(
                        period, bars, summary
                    )
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
                context.warnings.append(f"valuation_history_unadjusted: {type(exc).__name__}")
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
        context.chart.available = bool(context.chart.timeframes)
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
                if chart_daily := context.chart.timeframes.get("daily"):
                    chart_daily.as_of_date = latest_date
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
            shifted_bars: dict[str, list[dict[str, object]]] = {}
            for period, bars in adjusted_bars.items():
                shifted_bars[period] = []
                for bar in bars:
                    shifted = dict(bar)
                    try:
                        shifted_date = date.fromisoformat(str(bar.get("date") or "")[:10])
                    except ValueError:
                        pass
                    else:
                        shifted["date"] = (
                            shifted_date - timedelta(days=date_shift_days)
                        ).isoformat()
                    shifted_bars[period].append(shifted)
            adjusted_bars = shifted_bars
        is_live_bar = (
            session_state.session == "open" and latest_date == session_state.market_date.isoformat()
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
        chart_daily = context.chart.timeframes.get("daily")
        context.chart.as_of_date = latest_date
        context.chart.price_basis = "adjusted_intraday" if is_live_bar else "adjusted_close"
        context.chart.quality = (
            "provisional"
            if is_live_bar
            else "fresh"
            if latest_date == session_state.latest_completed_regular_session_date.isoformat()
            else "stale"
            if latest_date
            else "unavailable"
        )
        if chart_daily is not None:
            chart_daily.quality = context.chart.quality
            chart_daily.price_basis = context.chart.price_basis
        for timeframe, chart_period in context.chart.timeframes.items():
            if timeframe != "daily":
                chart_period.price_basis = "adjusted_close"
        context.chart.structure = analyze_chart_structure(
            adjusted_bars,
            timeframe_contexts={
                timeframe: value.model_dump(mode="json")
                for timeframe, value in context.chart.timeframes.items()
            },
            investor_supply=context.supply,
            price_basis=context.chart.price_basis,
        )
        if price_structure_enabled:
            try:
                builder = (
                    build_kr_price_structure_runtime_context
                    if ticker.isdigit()
                    else build_us_price_structure_runtime_context
                )
                context.chart.structure["price_structure_v3"] = builder(
                    ticker=ticker,
                    cutoff=(session_state.latest_completed_regular_session_date.isoformat()),
                    raw_by_timeframe=adjusted_bars,
                    observed_at=observed_local.isoformat(),
                    provider_limit=OHLCV_PROVIDER_REQUEST_LIMIT,
                )
            except (TypeError, ValueError) as exc:
                context.warnings.append(f"price_structure_v3: {type(exc).__name__}")
        structure_unavailable = context.chart.structure.get("unavailable_fields", [])
        context.chart.unavailable_fields = list(
            dict.fromkeys(
                [
                    *_UNAVAILABLE_PROVIDER_CHART_FIELDS,
                    *(structure_unavailable if isinstance(structure_unavailable, list) else []),
                ]
            )
        )
        context.chart.warnings = list(context.warnings)
        technical_acquisition["completed_at"] = datetime.now(timezone.utc).isoformat()
        failure_classes = technical_acquisition.get("failure_classes")
        if isinstance(failure_classes, list):
            technical_acquisition["failure_classes"] = tuple(
                dict.fromkeys(str(item) for item in failure_classes)
            )
        technical_context = build_packet_owned_technical_context(
            ticker=ticker,
            market="kr" if ticker.isdigit() else "us",
            session=session_state.session,
            as_of=observed_local.isoformat(),
            periods=adjusted_bars,
            cutoff=session_state.latest_completed_regular_session_date,
            expected_daily_completed=(
                session_state.latest_completed_regular_session_date.isoformat()
            ),
            acquisition=technical_acquisition,
        )
        context.set_technical_context_payload(technical_context.model_dump(mode="json"))
        return context
