from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation, localcontext
from enum import StrEnum

from pydantic import BaseModel, ConfigDict

from app.services.ohlcv_completed_bar_finality_service import (
    BarFinality,
    SEMANTICS_KEY,
    assess_completed_bar_finality,
)
from app.services.technical_feature_dependency_service import (
    DependencyClassification,
    DependencyKind,
    assess_feature_dependency,
)


CONTRACT_VERSION = "ohlcv-multi-timeframe-feature-engine-v1"
TIMEFRAMES = ("daily", "weekly", "monthly")
REQUESTED_COUNTS = {"daily": 1200, "weekly": 600, "monthly": 300}
PROVIDER_REQUEST_LIMIT = 1000


class FeatureStatus(StrEnum):
    ELIGIBLE = "ELIGIBLE"
    PARTIAL = "PARTIAL"
    UNAVAILABLE = "UNAVAILABLE"


class FrozenModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class TechnicalFeatureFact(FrozenModel):
    fact_id: str
    ticker: str
    timeframe: str
    semantic: str
    value: Decimal | str
    unit: str
    formula: str
    minimum_history: int
    as_of: str
    input_basis: str
    completed_bar_only: bool = True
    source_sha256: str
    dependency_kind: DependencyKind = DependencyKind.FINITE
    dependency_start: str | None = None
    dependency_end: str | None = None
    dependency_bar_count: int = 0
    dependency_source_sha256: str | None = None
    dependency_classification: DependencyClassification = DependencyClassification.SAFE


class TimeframeFeatureSet(FrozenModel):
    timeframe: str
    status: FeatureStatus
    as_of: str | None
    requested_count: int
    provider_request_count: int
    actual_count: int
    completed_count: int
    provisional_count: int
    source_limitation: str | None
    facts: tuple[TechnicalFeatureFact, ...] = ()
    source_integrity_state: str = "VALID"
    final_bar_count: int = 0
    unconfirmed_count: int = 0
    invalid_source_row_count: int = 0
    safe_feature_count: int = 0
    invalid_feature_count: int = 0
    dependency_blocked_count: int = 0
    invalid_source_rows: tuple[dict[str, object], ...] = ()
    blocked_features: tuple[str, ...] = ()
    recovery_provenance: tuple[dict[str, object], ...] = ()


class MultiTimeframeFeaturePacket(FrozenModel):
    contract: str = CONTRACT_VERSION
    ticker: str
    adjustment_basis: str
    cutoff: str
    daily: TimeframeFeatureSet
    weekly: TimeframeFeatureSet
    monthly: TimeframeFeatureSet
    packet_sha256: str


@dataclass(frozen=True)
class _Bar:
    as_of: date
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal | None


@dataclass(frozen=True)
class _NormalizedBarSet:
    bars: tuple[_Bar, ...]
    provisional_count: int
    unconfirmed_count: int
    invalid_rows: tuple[dict[str, object], ...]
    invalid_dates: tuple[date, ...]
    recovery_provenance: tuple[dict[str, object], ...]


def _decimal(value: object) -> Decimal | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None
    return number if number.is_finite() else None


def _rounded(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.000001"))


def _stable_id(*parts: object) -> str:
    material = "|".join(str(part) for part in parts)
    return "technical-feature:" + hashlib.sha256(material.encode()).hexdigest()[:24]


def _canonical_sha(value: object) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )
    return hashlib.sha256(payload.encode()).hexdigest()


def _is_completed(row: Mapping[str, object]) -> bool:
    for key in ("is_complete", "completed", "is_closed"):
        if key in row:
            return bool(row[key])
    state = str(row.get("bar_state") or row.get("completion_state") or "").upper()
    if state:
        return state in {"COMPLETE", "COMPLETED", "CLOSED", "FINAL"}
    # The repository OHLCV endpoint returns only completed bars unless it explicitly
    # marks a current provisional bar. The absence of a marker preserves that contract.
    return True


def _normalize_bars(
    rows: Sequence[Mapping[str, object]], cutoff: date
) -> _NormalizedBarSet:
    completed: dict[date, _Bar] = {}
    provisional = 0
    unconfirmed = 0
    invalid_rows: list[dict[str, object]] = []
    invalid_dates: list[date] = []
    recovery: list[dict[str, object]] = []
    observed: dict[date, str] = {}

    def reject(row: Mapping[str, object], reason: str, bar_date: date | None) -> None:
        invalid_rows.append(
            {
                "date": bar_date.isoformat() if bar_date is not None else row.get("date"),
                "reason": reason,
                "row_fingerprint": _canonical_sha(
                    {key: row.get(key) for key in ("date", "open", "high", "low", "close", "volume")}
                ),
            }
        )
        if bar_date is not None:
            invalid_dates.append(bar_date)
            completed.pop(bar_date, None)

    for row in rows:
        try:
            as_of = date.fromisoformat(str(row.get("date") or "")[:10])
        except ValueError:
            reject(row, "invalid_bar_date", None)
            continue
        if as_of > cutoff:
            provisional += 1
            continue
        open_value = _decimal(row.get("open"))
        high = _decimal(row.get("high"))
        low = _decimal(row.get("low"))
        close = _decimal(row.get("close"))
        if None in {open_value, high, low, close}:
            reject(row, "missing_or_invalid_ohlc", as_of)
            continue
        assert open_value is not None and high is not None and low is not None and close is not None
        if SEMANTICS_KEY in row:
            finality = assess_completed_bar_finality(row, cutoff=cutoff)
            if finality.state == BarFinality.INVALID:
                reject(row, "bar_finality_invalid", as_of)
                continue
            if finality.state == BarFinality.PROVISIONAL:
                provisional += 1
                continue
            if finality.state == BarFinality.UNCONFIRMED:
                unconfirmed += 1
                continue
            if finality.completed_close_value is not None:
                close = finality.completed_close_value
        elif not _is_completed(row):
            provisional += 1
            continue
        if (
            min(open_value, high, low, close) <= 0
            or high < low
            or not low <= open_value <= high
            or not low <= close <= high
        ):
            reject(row, "invalid_ohlc_relation", as_of)
            continue
        volume = _decimal(row.get("volume"))
        if volume is not None and volume < 0:
            reject(row, "negative_volume", as_of)
            continue
        row_sha = _canonical_sha(
            {key: row.get(key) for key in ("date", "open", "high", "low", "close", "volume")}
        )
        if as_of in observed:
            if observed[as_of] != row_sha:
                reject(row, "duplicate_bar_conflict", as_of)
            continue
        observed[as_of] = row_sha
        completed[as_of] = _Bar(
            as_of=as_of,
            open=open_value,
            high=high,
            low=low,
            close=close,
            volume=volume,
        )
        provenance = row.get("_recovery_provenance")
        if isinstance(provenance, Mapping):
            recovery.append(dict(provenance))
    return _NormalizedBarSet(
        bars=tuple(completed[key] for key in sorted(completed)),
        provisional_count=provisional,
        unconfirmed_count=unconfirmed,
        invalid_rows=tuple(invalid_rows),
        invalid_dates=tuple(sorted(set(invalid_dates))),
        recovery_provenance=tuple(recovery),
    )


def _mean(values: Sequence[Decimal]) -> Decimal:
    return sum(values, Decimal(0)) / Decimal(len(values))


def _stddev(values: Sequence[Decimal]) -> Decimal:
    if len(values) < 2:
        return Decimal(0)
    mean = _mean(values)
    variance = sum(((value - mean) ** 2 for value in values), Decimal(0)) / Decimal(
        len(values)
    )
    with localcontext() as context:
        context.prec = 34
        return variance.sqrt()


def _ema_series(values: Sequence[Decimal], period: int) -> list[Decimal | None]:
    result: list[Decimal | None] = [None] * len(values)
    if len(values) < period:
        return result
    seed = _mean(values[:period])
    result[period - 1] = seed
    multiplier = Decimal(2) / Decimal(period + 1)
    previous = seed
    for index in range(period, len(values)):
        previous = (values[index] - previous) * multiplier + previous
        result[index] = previous
    return result


def _wilder_series(values: Sequence[Decimal], period: int) -> list[Decimal | None]:
    result: list[Decimal | None] = [None] * len(values)
    if len(values) < period:
        return result
    previous = _mean(values[:period])
    result[period - 1] = previous
    for index in range(period, len(values)):
        previous = (previous * Decimal(period - 1) + values[index]) / Decimal(period)
        result[index] = previous
    return result


def _latest(values: Sequence[Decimal | None]) -> Decimal | None:
    return next((value for value in reversed(values) if value is not None), None)


def _state(value: Decimal, lower: Decimal, upper: Decimal) -> str:
    if value > upper:
        return "ABOVE"
    if value < lower:
        return "BELOW"
    return "INSIDE"


def _true_ranges(bars: Sequence[_Bar]) -> list[Decimal]:
    values: list[Decimal] = []
    for index, bar in enumerate(bars):
        if index == 0:
            values.append(bar.high - bar.low)
            continue
        previous_close = bars[index - 1].close
        values.append(
            max(
                bar.high - bar.low,
                abs(bar.high - previous_close),
                abs(bar.low - previous_close),
            )
        )
    return values


def _rsi(closes: Sequence[Decimal], period: int = 14) -> Decimal | None:
    if len(closes) <= period:
        return None
    changes = [closes[index] - closes[index - 1] for index in range(1, len(closes))]
    gains = [max(value, Decimal(0)) for value in changes]
    losses = [max(-value, Decimal(0)) for value in changes]
    average_gain = _latest(_wilder_series(gains, period))
    average_loss = _latest(_wilder_series(losses, period))
    if average_gain is None or average_loss is None:
        return None
    if average_loss == 0:
        return Decimal(100)
    relative_strength = average_gain / average_loss
    return Decimal(100) - Decimal(100) / (Decimal(1) + relative_strength)


def _adx(bars: Sequence[_Bar], period: int = 14) -> tuple[Decimal, Decimal, Decimal] | None:
    if len(bars) < period * 2:
        return None
    tr = _true_ranges(bars)[1:]
    plus_dm: list[Decimal] = []
    minus_dm: list[Decimal] = []
    for index in range(1, len(bars)):
        up = bars[index].high - bars[index - 1].high
        down = bars[index - 1].low - bars[index].low
        plus_dm.append(up if up > down and up > 0 else Decimal(0))
        minus_dm.append(down if down > up and down > 0 else Decimal(0))
    atr = _wilder_series(tr, period)
    plus = _wilder_series(plus_dm, period)
    minus = _wilder_series(minus_dm, period)
    dx: list[Decimal] = []
    latest_plus = latest_minus = None
    for tr_value, plus_value, minus_value in zip(atr, plus, minus, strict=True):
        if tr_value in {None, Decimal(0)} or plus_value is None or minus_value is None:
            continue
        latest_plus = plus_value / tr_value * Decimal(100)
        latest_minus = minus_value / tr_value * Decimal(100)
        denominator = latest_plus + latest_minus
        dx.append(
            abs(latest_plus - latest_minus) / denominator * Decimal(100)
            if denominator
            else Decimal(0)
        )
    adx = _latest(_wilder_series(dx, period))
    if adx is None or latest_plus is None or latest_minus is None:
        return None
    return adx, latest_plus, latest_minus


def _fact(
    *,
    ticker: str,
    timeframe: str,
    semantic: str,
    value: Decimal | str,
    unit: str,
    formula: str,
    minimum_history: int,
    as_of: date,
    input_basis: str,
    source_sha256: str,
    dependency_kind: DependencyKind,
    dependency_start: str,
    dependency_end: str,
    dependency_bar_count: int,
    dependency_source_sha256: str,
    dependency_classification: DependencyClassification,
) -> TechnicalFeatureFact:
    normalized = _rounded(value) if isinstance(value, Decimal) else value
    return TechnicalFeatureFact(
        fact_id=_stable_id(
            ticker, timeframe, semantic, as_of.isoformat(), normalized, source_sha256
        ),
        ticker=ticker,
        timeframe=timeframe,
        semantic=semantic,
        value=normalized,
        unit=unit,
        formula=formula,
        minimum_history=minimum_history,
        as_of=as_of.isoformat(),
        input_basis=input_basis,
        source_sha256=source_sha256,
        dependency_kind=dependency_kind,
        dependency_start=dependency_start,
        dependency_end=dependency_end,
        dependency_bar_count=dependency_bar_count,
        dependency_source_sha256=dependency_source_sha256,
        dependency_classification=dependency_classification,
    )


def _feature_facts(
    ticker: str,
    timeframe: str,
    bars: Sequence[_Bar],
    adjustment_basis: str,
    invalid_dates: Sequence[date] = (),
) -> tuple[tuple[TechnicalFeatureFact, ...], tuple[str, ...]]:
    if not bars:
        return (), ()
    closes = [bar.close for bar in bars]
    highs = [bar.high for bar in bars]
    lows = [bar.low for bar in bars]
    volumes = [bar.volume for bar in bars]
    as_of = bars[-1].as_of
    source_sha = _canonical_sha(
        [
            [bar.as_of.isoformat(), str(bar.open), str(bar.high), str(bar.low), str(bar.close), str(bar.volume)]
            for bar in bars
        ]
    )
    facts: list[TechnicalFeatureFact] = []
    blocked: list[str] = []

    def add(
        semantic: str,
        value: Decimal | str | None,
        unit: str,
        formula: str,
        minimum_history: int,
    ) -> None:
        if value is None:
            return
        dependency = assess_feature_dependency(
            semantic=semantic,
            minimum_history=minimum_history,
            row_dates=[bar.as_of for bar in bars],
            invalid_dates=invalid_dates,
        )
        if dependency.classification in {
            DependencyClassification.UNSAFE_DEPENDS_ON_BAD_ROW,
            DependencyClassification.UNAVAILABLE_OTHER_REASON,
        }:
            blocked.append(semantic)
            return
        dependency_bars = bars[-dependency.dependency_bar_count :]
        dependency_sha = _canonical_sha(
            [
                [
                    bar.as_of.isoformat(),
                    str(bar.open),
                    str(bar.high),
                    str(bar.low),
                    str(bar.close),
                    str(bar.volume),
                ]
                for bar in dependency_bars
            ]
        )
        assert dependency.dependency_start is not None
        assert dependency.dependency_end is not None
        facts.append(
            _fact(
                ticker=ticker,
                timeframe=timeframe,
                semantic=semantic,
                value=value,
                unit=unit,
                formula=formula,
                minimum_history=minimum_history,
                as_of=as_of,
                input_basis=adjustment_basis,
                source_sha256=source_sha,
                dependency_kind=dependency.dependency_kind,
                dependency_start=dependency.dependency_start,
                dependency_end=dependency.dependency_end,
                dependency_bar_count=dependency.dependency_bar_count,
                dependency_source_sha256=dependency_sha,
                dependency_classification=dependency.classification,
            )
        )

    close = closes[-1]
    add("close", close, "price", "completed_bar_close", 1)
    for window in (1, 5, 10, 20, 60, 120, 252):
        if len(closes) > window and closes[-window - 1] != 0:
            add(
                f"return_{window}",
                (close / closes[-window - 1] - Decimal(1)) * Decimal(100),
                "percent",
                f"(close_t / close_t-{window} - 1) * 100",
                window + 1,
            )

    for window in (20, 60, 120, 252):
        if len(closes) < window:
            continue
        window_high = max(highs[-window:])
        window_low = min(lows[-window:])
        add(f"rolling_high_{window}", window_high, "price", "max(high, window)", window)
        add(f"rolling_low_{window}", window_low, "price", "min(low, window)", window)
        add(
            f"distance_from_high_{window}",
            (close / window_high - Decimal(1)) * Decimal(100),
            "percent",
            "(close / rolling_high - 1) * 100",
            window,
        )
        add(
            f"distance_from_low_{window}",
            (close / window_low - Decimal(1)) * Decimal(100),
            "percent",
            "(close / rolling_low - 1) * 100",
            window,
        )
        peak = closes[-window]
        max_drawdown = Decimal(0)
        for value in closes[-window:]:
            peak = max(peak, value)
            max_drawdown = min(max_drawdown, (value / peak - Decimal(1)) * Decimal(100))
        add(
            f"max_drawdown_{window}",
            max_drawdown,
            "percent",
            "min(close / running_peak - 1) * 100",
            window,
        )

    if len(highs) >= 21:
        higher_highs = sum(highs[index] > highs[index - 1] for index in range(len(highs) - 19, len(highs)))
        lower_lows = sum(lows[index] < lows[index - 1] for index in range(len(lows) - 19, len(lows)))
        add("higher_high_count_20", Decimal(higher_highs), "count", "count(high_t > high_t-1)", 21)
        add("lower_low_count_20", Decimal(lower_lows), "count", "count(low_t < low_t-1)", 21)
        add(
            "trend_sequence_20",
            "HIGHER_HIGH_DOMINANT" if higher_highs > lower_lows else "LOWER_LOW_DOMINANT" if lower_lows > higher_highs else "MIXED",
            "state",
            "compare higher-high and lower-low counts over 20 transitions",
            21,
        )

    ema_values: dict[int, list[Decimal | None]] = {}
    for window in (5, 10, 20, 50, 100, 200):
        if len(closes) >= window:
            sma = _mean(closes[-window:])
            add(f"sma_{window}", sma, "price", f"mean(close, {window})", window)
            add(
                f"close_vs_sma_{window}",
                (close / sma - Decimal(1)) * Decimal(100),
                "percent",
                f"(close / sma_{window} - 1) * 100",
                window,
            )
        ema_values[window] = _ema_series(closes, window)
        ema = _latest(ema_values[window])
        if ema is not None:
            add(f"ema_{window}", ema, "price", f"EMA(close, {window})", window)

    ema12 = _ema_series(closes, 12)
    ema26 = _ema_series(closes, 26)
    macd_series: list[Decimal | None] = [
        fast - slow if fast is not None and slow is not None else None
        for fast, slow in zip(ema12, ema26, strict=True)
    ]
    compact_macd = [value for value in macd_series if value is not None]
    signal_compact = _ema_series(compact_macd, 9)
    macd = _latest(macd_series)
    signal = _latest(signal_compact)
    if macd is not None and signal is not None:
        histogram = macd - signal
        add("macd_12_26", macd, "price", "EMA12 - EMA26", 26)
        add("macd_signal_9", signal, "price", "EMA(MACD, 9)", 34)
        add("macd_histogram", histogram, "price", "MACD - signal", 34)
        add(
            "macd_state",
            ("BULLISH" if macd > signal else "BEARISH" if macd < signal else "NEUTRAL")
            + ("_ABOVE_ZERO" if macd > 0 else "_BELOW_ZERO" if macd < 0 else "_AT_ZERO"),
            "state",
            "MACD position versus signal and zero",
            34,
        )

    rsi = _rsi(closes)
    add("rsi_14", rsi, "index", "Wilder RSI(close, 14)", 15)
    if rsi is not None:
        add(
            "rsi_state",
            "OVERBOUGHT" if rsi >= 70 else "OVERSOLD" if rsi <= 30 else "NEUTRAL",
            "state",
            "RSI >= 70, <= 30, otherwise neutral",
            15,
        )

    true_ranges = _true_ranges(bars)
    atr = _latest(_wilder_series(true_ranges, 14))
    add("atr_14", atr, "price", "Wilder average true range, 14", 14)
    if atr is not None:
        add("atr_pct_14", atr / close * Decimal(100), "percent", "ATR14 / close * 100", 14)
    if len(closes) >= 21:
        returns = [
            closes[index] / closes[index - 1] - Decimal(1)
            for index in range(len(closes) - 19, len(closes))
        ]
        annualizer = {"daily": Decimal(252), "weekly": Decimal(52), "monthly": Decimal(12)}[
            timeframe
        ]
        with localcontext() as context:
            context.prec = 34
            volatility = _stddev(returns) * annualizer.sqrt() * Decimal(100)
        add("realized_volatility_20", volatility, "percent", "std(simple return, 20) * sqrt(periods/year) * 100", 21)
    if len(bars) >= 2:
        latest_gap = (bars[-1].open / bars[-2].close - Decimal(1)) * Decimal(100)
        add("gap_latest", latest_gap, "percent", "(open_t / close_t-1 - 1) * 100", 2)

    if len(closes) >= 20:
        middle = _mean(closes[-20:])
        deviation = _stddev(closes[-20:])
        upper = middle + deviation * Decimal(2)
        lower = middle - deviation * Decimal(2)
        add("bollinger_20_2_mid", middle, "price", "SMA20", 20)
        add("bollinger_20_2_upper", upper, "price", "SMA20 + 2 * population_stddev20", 20)
        add("bollinger_20_2_lower", lower, "price", "SMA20 - 2 * population_stddev20", 20)
        add("bollinger_20_2_state", _state(close, lower, upper), "state", "close versus Bollinger 20/2", 20)

    adx = _adx(bars)
    if adx is not None:
        adx_value, plus_di, minus_di = adx
        add("adx_14", adx_value, "index", "Wilder ADX, 14", 28)
        add("plus_di_14", plus_di, "index", "+DM / ATR * 100", 28)
        add("minus_di_14", minus_di, "index", "-DM / ATR * 100", 28)
        add("dmi_state", "PLUS_DI_DOMINANT" if plus_di > minus_di else "MINUS_DI_DOMINANT" if minus_di > plus_di else "BALANCED", "state", "compare +DI14 and -DI14", 28)

    for window in (10, 20):
        if len(closes) > window and closes[-window - 1] != 0:
            add(f"roc_{window}", (close / closes[-window - 1] - Decimal(1)) * Decimal(100), "percent", f"(close / close_t-{window} - 1) * 100", window + 1)

    if len(bars) >= 16:
        highest = max(highs[-14:])
        lowest = min(lows[-14:])
        if highest > lowest:
            k_values: list[Decimal] = []
            for index in range(len(bars) - 3, len(bars)):
                start = index - 13
                if start < 0:
                    continue
                local_high = max(highs[start : index + 1])
                local_low = min(lows[start : index + 1])
                if local_high > local_low:
                    k_values.append((closes[index] - local_low) / (local_high - local_low) * Decimal(100))
            if k_values:
                add("stochastic_k_14", k_values[-1], "index", "(close - low14) / (high14 - low14) * 100", 14)
                add("stochastic_d_3", _mean(k_values), "index", "SMA(stochastic_k, 3)", 16)

    valid_volume = all(value is not None and value >= 0 for value in volumes)
    if valid_volume:
        numeric_volumes = [value for value in volumes if value is not None]
        if len(numeric_volumes) >= 20:
            average_volume = _mean(numeric_volumes[-20:])
            if average_volume:
                add("volume_ratio_20", numeric_volumes[-1] / average_volume, "ratio", "volume / SMA(volume, 20)", 20)
            obv = Decimal(0)
            for index in range(1, len(closes)):
                if closes[index] > closes[index - 1]:
                    obv += numeric_volumes[index]
                elif closes[index] < closes[index - 1]:
                    obv -= numeric_volumes[index]
            add("obv", obv, "volume", "cumulative signed volume", 2)
            money_flow_volume: list[Decimal] = []
            for bar in bars[-20:]:
                spread = bar.high - bar.low
                multiplier = ((bar.close - bar.low) - (bar.high - bar.close)) / spread if spread else Decimal(0)
                assert bar.volume is not None
                money_flow_volume.append(multiplier * bar.volume)
            denominator = sum(numeric_volumes[-20:], Decimal(0))
            if denominator:
                add("cmf_20", sum(money_flow_volume, Decimal(0)) / denominator, "ratio", "sum(money-flow volume, 20) / sum(volume, 20)", 20)
        if len(bars) >= 15:
            typical = [(bar.high + bar.low + bar.close) / Decimal(3) for bar in bars]
            positive = Decimal(0)
            negative = Decimal(0)
            for index in range(len(bars) - 13, len(bars)):
                assert bars[index].volume is not None
                flow = typical[index] * bars[index].volume
                if typical[index] > typical[index - 1]:
                    positive += flow
                elif typical[index] < typical[index - 1]:
                    negative += flow
            mfi = Decimal(100) if negative == 0 else Decimal(100) - Decimal(100) / (Decimal(1) + positive / negative)
            add("mfi_14", mfi, "index", "money flow index, 14", 15)

    if len(bars) >= 21:
        prior_high = max(highs[-21:-1])
        prior_low = min(lows[-21:-1])
        add("donchian_high_20", prior_high, "price", "max(high, prior 20 completed bars)", 21)
        add("donchian_low_20", prior_low, "price", "min(low, prior 20 completed bars)", 21)
        add("donchian_breakout_20", "UPSIDE" if close > prior_high else "DOWNSIDE" if close < prior_low else "INSIDE", "state", "close versus prior 20-bar Donchian channel", 21)

    return tuple(facts), tuple(dict.fromkeys(blocked))


def build_multi_timeframe_feature_packet(
    *,
    ticker: str,
    periods: Mapping[str, Sequence[Mapping[str, object]]],
    cutoff: date,
    adjustment_basis: str = "adjusted_close",
) -> MultiTimeframeFeaturePacket:
    values: dict[str, TimeframeFeatureSet] = {}
    for timeframe in TIMEFRAMES:
        raw = periods.get(timeframe) or ()
        normalized = _normalize_bars(raw, cutoff)
        bars = normalized.bars
        requested = REQUESTED_COUNTS[timeframe]
        provider_request = min(requested, PROVIDER_REQUEST_LIMIT)
        limitation = (
            f"provider_request_cap_{PROVIDER_REQUEST_LIMIT}"
            if requested > PROVIDER_REQUEST_LIMIT
            else None
        )
        facts, blocked = _feature_facts(
            ticker,
            timeframe,
            bars,
            adjustment_basis,
            normalized.invalid_dates,
        )
        status = FeatureStatus.ELIGIBLE if facts else FeatureStatus.UNAVAILABLE
        if facts and (
            len(bars) < requested
            or limitation
            or normalized.invalid_rows
            or normalized.provisional_count
            or normalized.unconfirmed_count
        ):
            status = FeatureStatus.PARTIAL
        values[timeframe] = TimeframeFeatureSet(
            timeframe=timeframe,
            status=status,
            as_of=bars[-1].as_of.isoformat() if bars else None,
            requested_count=requested,
            provider_request_count=provider_request,
            actual_count=len(raw),
            completed_count=len(bars),
            provisional_count=normalized.provisional_count,
            source_limitation=limitation,
            facts=facts,
            source_integrity_state=(
                "INVALID_ROWS_PRESENT" if normalized.invalid_rows else "VALID"
            ),
            final_bar_count=len(bars),
            unconfirmed_count=normalized.unconfirmed_count,
            invalid_source_row_count=len(normalized.invalid_rows),
            safe_feature_count=len(facts),
            invalid_feature_count=len(blocked),
            dependency_blocked_count=len(blocked),
            invalid_source_rows=normalized.invalid_rows,
            blocked_features=blocked,
            recovery_provenance=normalized.recovery_provenance,
        )
    hash_payload = {
        key: values[key].model_dump(mode="json") for key in TIMEFRAMES
    }
    return MultiTimeframeFeaturePacket(
        ticker=ticker,
        adjustment_basis=adjustment_basis,
        cutoff=cutoff.isoformat(),
        daily=values["daily"],
        weekly=values["weekly"],
        monthly=values["monthly"],
        packet_sha256=_canonical_sha(hash_payload),
    )


def feature_catalog() -> tuple[dict[str, object], ...]:
    """Return the stable, documented feature families implemented by this engine."""
    return (
        {"family": "returns", "semantics": ["return_1", "return_5", "return_10", "return_20", "return_60", "return_120", "return_252"]},
        {"family": "range_and_drawdown", "semantics": ["rolling_high_{20,60,120,252}", "rolling_low_{20,60,120,252}", "distance_from_high", "distance_from_low", "max_drawdown", "trend_sequence_20"]},
        {"family": "trend", "semantics": ["sma_{5,10,20,50,100,200}", "ema_{5,10,20,50,100,200}", "close_vs_sma"]},
        {"family": "macd", "semantics": ["macd_12_26", "macd_signal_9", "macd_histogram", "macd_state"]},
        {"family": "momentum", "semantics": ["rsi_14", "roc_{10,20}", "stochastic_k_14", "stochastic_d_3"]},
        {"family": "volatility", "semantics": ["atr_14", "atr_pct_14", "realized_volatility_20", "gap_latest", "bollinger_20_2"]},
        {"family": "directional", "semantics": ["adx_14", "plus_di_14", "minus_di_14", "dmi_state"]},
        {"family": "volume", "semantics": ["volume_ratio_20", "obv", "cmf_20", "mfi_14"], "availability": "requires_valid_volume"},
        {"family": "breakout", "semantics": ["donchian_high_20", "donchian_low_20", "donchian_breakout_20"]},
    )
