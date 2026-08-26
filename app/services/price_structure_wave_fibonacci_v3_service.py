from __future__ import annotations

import hashlib
import json
import math
import statistics
import time
from collections.abc import Mapping, Sequence
from datetime import date, datetime, timedelta, timezone
from decimal import ROUND_CEILING, ROUND_FLOOR, ROUND_HALF_UP, Decimal
from enum import StrEnum
from typing import Literal
from zoneinfo import ZoneInfo

import exchange_calendars as exchange_calendar
from pydantic import BaseModel, ConfigDict, Field

from app.services.ohlcv_structure_service import Timeframe


CONTRACT_VERSION = "price-structure-wave-fibonacci-v3"
HISTORY_CONTRACT = "ohlcv-long-history-contract-v1"
WAVE_CONTRACT = "primary-monthly-wave-hypothesis-v1"
FIBONACCI_CONTRACT = "wave-fibonacci-source-provenance-v1"
CONFLUENCE_CONTRACT = "multi-timeframe-sr-confluence-v3"
SHADOW_POLICY = "price-structure-v3-shadow-policy-v1"
CALCULATION_VERSION = "wave-fibonacci-deterministic-v3"
BAR_COMPLETION_CONTRACT = "ohlcv-bar-completion-v1"
HISTORY_CACHE_CONTRACT = "ohlcv-1200-backfill-cache-v1"
WAVE_DEGREE_CONTRACT = "wave-degree-current-cycle-v1"
AI_FEEDBACK_CONTRACT = "price-structure-v3-ai-feedback-loop-v1"
FIB_FAMILY_DEPENDENCY_CONTRACT = "fib-family-endpoint-dependency-v1"
FAMILY_CONSENSUS_CONTRACT = "fib-family-consensus-v1"

TIMEFRAME_ORDER: tuple[Timeframe, ...] = ("monthly", "weekly", "daily")
HISTORY_REQUESTS: dict[Timeframe, int] = {
    "daily": 1200,
    "weekly": 600,
    "monthly": 300,
}
PROVIDER_INTERFACE_LIMIT = 1000
PIVOT_WINDOWS: dict[Timeframe, tuple[int, int]] = {
    "daily": (3, 3),
    "weekly": (2, 2),
    "monthly": (2, 2),
}
GROUPING_PCT: dict[Timeframe, Decimal] = {
    "daily": Decimal("0.0175"),
    "weekly": Decimal("0.0225"),
    "monthly": Decimal("0.0300"),
}
CONFLUENCE_PCT: dict[Timeframe, Decimal] = {
    "daily": Decimal("0.0200"),
    "weekly": Decimal("0.0250"),
    "monthly": Decimal("0.0300"),
}
BOX_WINDOWS: dict[Timeframe, int] = {"daily": 20, "weekly": 12, "monthly": 6}
TIMEFRAME_IMPORTANCE: dict[Timeframe, int] = {"daily": 1, "weekly": 2, "monthly": 3}

PivotKind = Literal["LOW", "HIGH"]
ConfirmationStatus = Literal["CONFIRMED", "PROVISIONAL"]
BarState = Literal["COMPLETE", "PARTIAL"]
ZoneRole = Literal["SUPPORT", "RESISTANCE", "CURRENT_ZONE"]
CoverageStatus = Literal["PASS", "PARTIAL", "FAIL"]
HypothesisStatus = Literal[
    "VALID_CONFIRMED",
    "VALID_PROVISIONAL",
    "AMBIGUOUS",
    "NONE",
]
WaveDegree = Literal[
    "GRAND_CYCLE",
    "PRIMARY_CURRENT_CYCLE",
    "INTERMEDIATE",
    "TACTICAL",
]


class FrozenModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class PriceBar(FrozenModel):
    contract: str = BAR_COMPLETION_CONTRACT
    bar_id: str | None = None
    date: str
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal | None = None
    trading_value: Decimal | None = None
    timeframe: Timeframe | None = None
    period_start: str | None = None
    period_end: str | None = None
    market_calendar: str | None = None
    observed_at: str | None = None
    bar_state: BarState = "COMPLETE"


class LongHistoryCoverage(FrozenModel):
    contract: str = HISTORY_CONTRACT
    timeframe: Timeframe
    requested_count: int
    provider_returned_count: int
    actual_count: int
    completed_count: int
    actual_start_date: str | None
    actual_end_date: str | None
    provider_limit: int | None
    provider_limit_hit: bool
    history_complete_to_listing: bool
    adjustment_basis: str
    status: CoverageStatus
    denial_reason: str | None = None


class PivotPoint(FrozenModel):
    pivot_id: str
    ticker: str
    timeframe: Timeframe
    bar_date: str
    pivot_bar_date: str | None = None
    required_right_bar_count: int = 0
    confirmation_date: str | None
    pivot_confirmation_date: str | None = None
    confirmation_bar_ids: tuple[str, ...] = ()
    kind: PivotKind
    price: Decimal
    atr14: Decimal | None
    status: ConfirmationStatus
    adjustment_basis: str
    source_ref: str


class ZoneSource(FrozenModel):
    source_id: str
    evidence_type: Literal["PIVOT", "BOLLINGER", "FIBONACCI", "BOX", "PRIOR_HIGH_LOW"]
    evidence_family: str
    method_family: str
    source_timeframe: Timeframe
    source_degree: str
    confluence_target_timeframe: Timeframe
    price: Decimal
    status: Literal["CONFIRMED", "PROVISIONAL", "PROJECTION"]
    family_stability: Literal["EXACT_INVARIANT", "PRICE_EQUIVALENT"] | None = None
    consensus_set_id: str | None = None
    equivalence_class_id: str | None = None


class TechnicalZone(FrozenModel):
    zone_id: str
    ticker: str
    timeframe: Timeframe
    low: Decimal
    high: Decimal
    center: Decimal
    current_role: ZoneRole
    structural_importance: int
    proximity_pct: Decimal
    evidence_family_score: Decimal
    confirmation_quality: Decimal
    reaction_count: int
    last_meaningful_interaction: str | None
    historical_role: ZoneRole | None = None
    reclaim_status: Literal["NOT_TESTED", "RECLAIMED", "LOST", "INSIDE"] = "NOT_TESTED"
    sources: tuple[ZoneSource, ...]
    confluence_stability: Literal[
        "CONFLUENCE_EXACT_INVARIANT",
        "CONFLUENCE_PRICE_EQUIVALENT",
        "CONFLUENCE_MATERIAL_VARIATION",
    ] | None = None


class WaveEndpoint(FrozenModel):
    label: Literal["W0", "W1", "W2", "W3", "W4", "W5"]
    pivot_ref: str
    date: str
    price: Decimal
    status: ConfirmationStatus


class MonthlyWaveHypothesis(FrozenModel):
    contract: str = WAVE_CONTRACT
    hypothesis_id: str
    ticker: str
    source_timeframe: Literal["monthly"] = "monthly"
    source_degree: WaveDegree = "PRIMARY_CURRENT_CYCLE"
    status: Literal["VALID_CONFIRMED", "VALID_PROVISIONAL"]
    wave_state: Literal["W4_CANDIDATE_W5_UNCONFIRMED", "W5_CANDIDATE"]
    endpoints: tuple[WaveEndpoint, ...]
    hard_rules: dict[str, bool]
    score: Decimal
    score_components: dict[str, Decimal]
    weekly_confirmation_refs: tuple[str, ...] = ()


class FibonacciReference(FrozenModel):
    contract: str = FIBONACCI_CONTRACT
    fib_id: str
    ticker: str
    currency: str
    source_timeframe: Timeframe
    source_degree: str
    confluence_target_timeframe: Timeframe
    wave_hypothesis_id: str
    family: Literal[
        "WAVE1_RETRACEMENT",
        "WAVE3_RETRACEMENT",
        "PRIMARY_CYCLE_RETRACEMENT",
        "CURRENT_REBOUND",
        "WAVE5_PROJECTION",
    ]
    method_family: str
    ratio: str
    endpoint_refs: tuple[str, ...]
    formula: str
    calculated_price: Decimal
    rounding: str = "0.000001_half_up"
    status: Literal["CONFIRMED", "PROVISIONAL", "PROJECTION"]
    as_of: str
    calculation_version: str = CALCULATION_VERSION
    dependency_contract: str = FIB_FAMILY_DEPENDENCY_CONTRACT
    required_endpoint_labels: tuple[str, ...] = ()
    family_stability: Literal["EXACT_INVARIANT", "PRICE_EQUIVALENT"] | None = None
    consensus_set_id: str | None = None
    consensus_candidate_ids: tuple[str, ...] = ()
    equivalence_class_id: str | None = None


class WaveSelectionStatus(StrEnum):
    SELECTED = "SELECTED"
    AMBIGUOUS = "AMBIGUOUS"
    INSUFFICIENT_STRUCTURE = "INSUFFICIENT_STRUCTURE"


class WaveHypothesisSelection(FrozenModel):
    status: WaveSelectionStatus
    hypothesis_id: str | None = None
    alternative_hypothesis_id: str | None = None
    competing_hypothesis_ids: tuple[str, ...] = Field(default=(), max_length=3)
    equivalence_class_id: str | None = None
    confidence: Literal["HIGH", "MEDIUM", "LOW"] = "LOW"
    reason_categories: tuple[str, ...] = Field(min_length=1, max_length=3)
    evidence_refs: tuple[str, ...] = Field(default=(), max_length=16)
    endpoint_refs: tuple[str, ...] = Field(default=(), max_length=6)
    concise_reason: str = Field(default="", max_length=240)
    ticker: str | None = None
    source_degree: WaveDegree | None = None
    cutoff: str | None = None
    adjustment_basis: str | None = None


class WaveSelectionValidation(FrozenModel):
    valid: bool
    errors: tuple[str, ...] = ()
    valid_abstention: bool = False


class WaveFeedbackAudit(FrozenModel):
    contract: str = AI_FEEDBACK_CONTRACT
    selection: WaveHypothesisSelection
    validation: WaveSelectionValidation
    selected_hypothesis_id: str | None = None
    selected_hypothesis_fed_to_engine: bool = False
    deterministic_sr_preserved: bool = True


class PriceStructureWaveFibV3Result(FrozenModel):
    contract: str = CONTRACT_VERSION
    shadow_policy: str = SHADOW_POLICY
    ticker: str
    security_id: str
    market: Literal["KR", "US"]
    currency: str
    adjustment_basis: str
    as_of: str
    current_price: Decimal
    coverage: dict[Timeframe, LongHistoryCoverage]
    pivots: dict[Timeframe, tuple[PivotPoint, ...]]
    sr_maps: dict[Timeframe, tuple[TechnicalZone, ...]]
    primary_monthly_hypotheses: tuple[MonthlyWaveHypothesis, ...]
    selected_hypothesis_id: str | None
    primary_hypothesis_status: HypothesisStatus
    fibonacci: tuple[FibonacciReference, ...]
    timeframe_zone_maps: dict[Timeframe, tuple[TechnicalZone, ...]]
    cross_timeframe_confluence: tuple[TechnicalZone, ...]
    shadow_render: str
    computation_ms: Decimal
    degree_candidate_counts: dict[WaveDegree, int] = Field(default_factory=dict)
    feedback_audit: WaveFeedbackAudit | None = None
    family_consensus_audit: dict[str, object] | None = None
    user_visible: bool = False
    business_thesis_mutation: bool = False
    official_assessment_mutation: bool = False


def _decimal(value: object) -> Decimal:
    return Decimal(str(value))


def _rounded(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)


def _stable_id(prefix: str, *parts: object) -> str:
    material = "|".join(str(part) for part in parts)
    return f"{prefix}:{hashlib.sha256(material.encode()).hexdigest()[:20]}"


def _canonical_hash(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, ensure_ascii=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode()).hexdigest()


def _parse_observed_at(value: str, *, market: Literal["KR", "US"]) -> datetime:
    zone = ZoneInfo("Asia/Seoul" if market == "KR" else "America/New_York")
    normalized = value.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=zone)
    return parsed.astimezone(zone)


def _calendar_for_range(
    market: Literal["KR", "US"],
    *,
    start: date,
    end: date,
):
    name = "XKRX" if market == "KR" else "XNYS"
    return name, exchange_calendar.get_calendar(
        name,
        start=start - timedelta(days=370),
        end=end + timedelta(days=370),
    )


def _latest_completed_session(calendar, observed_at: datetime) -> date | None:
    observed_date = observed_at.date()
    try:
        if calendar.is_session(observed_date):
            session = calendar.date_to_session(observed_date)
            close = calendar.session_close(session).to_pydatetime().astimezone(
                observed_at.tzinfo or timezone.utc
            )
            if observed_at >= close:
                return session.date()
            return calendar.previous_session(session).date()
        return calendar.date_to_session(observed_date, direction="previous").date()
    except (ValueError, IndexError, TypeError):
        return None


def _bar_period_bounds(calendar, bar_date: date, timeframe: Timeframe) -> tuple[date, date]:
    if timeframe == "daily":
        return bar_date, bar_date
    if timeframe == "weekly":
        calendar_start = bar_date - timedelta(days=bar_date.weekday())
        calendar_end = calendar_start + timedelta(days=6)
    else:
        calendar_start = bar_date.replace(day=1)
        next_month = (
            calendar_start.replace(year=calendar_start.year + 1, month=1)
            if calendar_start.month == 12
            else calendar_start.replace(month=calendar_start.month + 1)
        )
        calendar_end = next_month - timedelta(days=1)
    sessions = calendar.sessions_in_range(calendar_start, calendar_end)
    if len(sessions) == 0:
        return calendar_start, calendar_end
    return sessions[0].date(), sessions[-1].date()


def normalize_completed_bars(
    raw_bars: Sequence[Mapping[str, object]],
    *,
    cutoff: str,
    timeframe: Timeframe | None = None,
    market: Literal["KR", "US"] | None = None,
    observed_at: str | None = None,
) -> tuple[PriceBar, ...]:
    parsed_dates = [
        date.fromisoformat(str(raw.get("date"))[:10])
        for raw in raw_bars
        if raw.get("date") and str(raw.get("date"))[:10] <= cutoff
    ]
    calendar = None
    calendar_name: str | None = None
    completed_session: date | None = None
    normalized_observed_at: str | None = None
    if timeframe is not None and market is not None and observed_at is not None and parsed_dates:
        observed = _parse_observed_at(observed_at, market=market)
        calendar_name, calendar = _calendar_for_range(
            market,
            start=min(parsed_dates),
            end=max(max(parsed_dates), observed.date()),
        )
        completed_session = _latest_completed_session(calendar, observed)
        normalized_observed_at = observed.isoformat()
    normalized: dict[str, PriceBar] = {}
    for raw in raw_bars:
        bar_date = str(raw.get("date") or "")[:10]
        if not bar_date or bar_date > cutoff:
            continue
        required = (raw.get("open"), raw.get("high"), raw.get("low"), raw.get("close"))
        if any(value is None for value in required):
            continue
        period_start = bar_date
        period_end = bar_date
        state: BarState = "COMPLETE"
        if calendar is not None and timeframe is not None:
            start, end = _bar_period_bounds(
                calendar,
                date.fromisoformat(bar_date),
                timeframe,
            )
            period_start = start.isoformat()
            period_end = end.isoformat()
            state = (
                "COMPLETE"
                if completed_session is not None and end <= completed_session
                else "PARTIAL"
            )
        bar = PriceBar(
            bar_id=_stable_id(
                "v3-bar",
                market or "legacy",
                timeframe or "unknown",
                bar_date,
                period_start,
                period_end,
            ),
            date=bar_date,
            open=_decimal(raw["open"]),
            high=_decimal(raw["high"]),
            low=_decimal(raw["low"]),
            close=_decimal(raw["close"]),
            volume=_decimal(raw["volume"]) if raw.get("volume") is not None else None,
            trading_value=(
                _decimal(raw.get("value"))
                if raw.get("value") is not None
                else _decimal(raw.get("trading_value"))
                if raw.get("trading_value") is not None
                else None
            ),
            timeframe=timeframe,
            period_start=period_start,
            period_end=period_end,
            market_calendar=calendar_name,
            observed_at=normalized_observed_at,
            bar_state=state,
        )
        if bar.high < bar.low or not (bar.low <= bar.open <= bar.high) or not (
            bar.low <= bar.close <= bar.high
        ):
            continue
        normalized[bar_date] = bar
    return tuple(normalized[key] for key in sorted(normalized))


def prepare_long_history(
    raw_bars: Sequence[Mapping[str, object]],
    *,
    timeframe: Timeframe,
    cutoff: str,
    adjustment_basis: str,
    market: Literal["KR", "US"] | None = None,
    observed_at: str | None = None,
    provider_limit: int | None = PROVIDER_INTERFACE_LIMIT,
) -> tuple[tuple[PriceBar, ...], LongHistoryCoverage]:
    completed = normalize_completed_bars(
        raw_bars,
        cutoff=cutoff,
        timeframe=timeframe,
        market=market,
        observed_at=observed_at,
    )
    requested = HISTORY_REQUESTS[timeframe]
    provider_returned = len(completed)
    complete_bars = tuple(bar for bar in completed if bar.bar_state == "COMPLETE")
    partial_bars = tuple(bar for bar in completed if bar.bar_state == "PARTIAL")
    selected = tuple(sorted(complete_bars[-requested:] + partial_bars, key=lambda bar: bar.date))
    actual = len(selected)
    completed_count = len(complete_bars[-requested:])
    limit_hit = bool(
        provider_limit is not None
        and provider_returned >= provider_limit
        and completed_count < requested
    )
    complete_to_listing = completed_count < requested and not limit_hit
    if completed_count >= requested:
        status: CoverageStatus = "PASS"
        reason = None
    elif completed_count > max(PIVOT_WINDOWS[timeframe]) * 2 + 3:
        status = "PARTIAL"
        reason = "provider_limit" if limit_hit else "short_listing_or_available_history"
    else:
        status = "FAIL"
        reason = "insufficient_completed_history"
    coverage = LongHistoryCoverage(
        timeframe=timeframe,
        requested_count=requested,
        provider_returned_count=provider_returned,
        actual_count=actual,
        completed_count=completed_count,
        actual_start_date=selected[0].date if selected else None,
        actual_end_date=selected[-1].date if selected else None,
        provider_limit=provider_limit,
        provider_limit_hit=limit_hit,
        history_complete_to_listing=complete_to_listing,
        adjustment_basis=adjustment_basis,
        status=status,
        denial_reason=reason,
    )
    return selected, coverage


def _true_ranges(bars: Sequence[PriceBar]) -> tuple[Decimal, ...]:
    ranges: list[Decimal] = []
    previous: Decimal | None = None
    for bar in bars:
        values = [bar.high - bar.low]
        if previous is not None:
            values.extend((abs(bar.high - previous), abs(bar.low - previous)))
        ranges.append(max(values))
        previous = bar.close
    return tuple(ranges)


def _atr_at(true_ranges: Sequence[Decimal], index: int, window: int = 14) -> Decimal | None:
    start = max(0, index - window + 1)
    values = true_ranges[start : index + 1]
    if not values:
        return None
    return _rounded(sum(values) / Decimal(len(values)))


def detect_pivots(
    bars: Sequence[PriceBar],
    *,
    ticker: str,
    timeframe: Timeframe,
    adjustment_basis: str,
) -> tuple[PivotPoint, ...]:
    left, right = PIVOT_WINDOWS[timeframe]
    ranges = _true_ranges(bars)
    pivots: list[PivotPoint] = []
    for index, bar in enumerate(bars):
        if index < left:
            continue
        available_right = min(right, len(bars) - index - 1)
        left_bars = bars[index - left : index]
        right_bars = bars[index + 1 : index + 1 + available_right]
        is_low = all(bar.low < other.low for other in left_bars) and all(
            bar.low <= other.low for other in right_bars
        )
        is_high = all(bar.high > other.high for other in left_bars) and all(
            bar.high >= other.high for other in right_bars
        )
        if not is_low and not is_high:
            continue
        confirmation_bars = tuple(right_bars[:right])
        confirmation_ready = (
            bar.bar_state == "COMPLETE"
            and len(confirmation_bars) == right
            and all(item.bar_state == "COMPLETE" for item in confirmation_bars)
        )
        status: ConfirmationStatus = "CONFIRMED" if confirmation_ready else "PROVISIONAL"
        confirmation = confirmation_bars[-1].date if confirmation_ready else None
        confirmation_ids = tuple(
            item.bar_id or _stable_id("v3-bar-legacy", timeframe, item.date)
            for item in confirmation_bars
            if item.bar_state == "COMPLETE"
        )
        for kind, price, eligible in (
            ("LOW", bar.low, is_low),
            ("HIGH", bar.high, is_high),
        ):
            if not eligible:
                continue
            pivots.append(
                PivotPoint(
                    pivot_id=_stable_id(
                        "v3-pivot",
                        ticker,
                        timeframe,
                        kind,
                        bar.date,
                        price,
                        status,
                        adjustment_basis,
                    ),
                    ticker=ticker,
                    timeframe=timeframe,
                    bar_date=bar.date,
                    pivot_bar_date=bar.date,
                    required_right_bar_count=right,
                    confirmation_date=confirmation,
                    pivot_confirmation_date=confirmation,
                    confirmation_bar_ids=(confirmation_ids if confirmation_ready else ()),
                    kind=kind,  # type: ignore[arg-type]
                    price=price,
                    atr14=_atr_at(ranges, index),
                    status=status,
                    adjustment_basis=adjustment_basis,
                    source_ref=f"ohlcv:{timeframe}:{bar.date}",
                )
            )
    return tuple(sorted(pivots, key=lambda pivot: (pivot.bar_date, pivot.kind)))


def _role(low: Decimal, high: Decimal, current: Decimal) -> ZoneRole:
    if high < current:
        return "SUPPORT"
    if low > current:
        return "RESISTANCE"
    return "CURRENT_ZONE"


def _proximity(low: Decimal, high: Decimal, current: Decimal) -> Decimal:
    if current == 0:
        return Decimal(0)
    role = _role(low, high, current)
    if role == "SUPPORT":
        return _rounded((current - high) / current * Decimal(100))
    if role == "RESISTANCE":
        return _rounded((low - current) / current * Decimal(100))
    return Decimal(0)


def _zone_source_for_pivot(pivot: PivotPoint, target: Timeframe) -> ZoneSource:
    return ZoneSource(
        source_id=pivot.pivot_id,
        evidence_type="PIVOT",
        evidence_family=f"PIVOT_{pivot.timeframe.upper()}",
        method_family="PIVOT_GROUP",
        source_timeframe=pivot.timeframe,
        source_degree=f"{pivot.timeframe.upper()}_PRICE_STRUCTURE",
        confluence_target_timeframe=target,
        price=pivot.price,
        status=pivot.status,
    )


def build_pivot_zones(
    pivots: Sequence[PivotPoint],
    *,
    ticker: str,
    timeframe: Timeframe,
    current_price: Decimal,
) -> tuple[TechnicalZone, ...]:
    output: list[TechnicalZone] = []
    for kind in ("LOW", "HIGH"):
        candidates = sorted(
            (pivot for pivot in pivots if pivot.kind == kind), key=lambda pivot: pivot.price
        )
        groups: list[list[PivotPoint]] = []
        for pivot in candidates:
            if not groups:
                groups.append([pivot])
                continue
            group = groups[-1]
            center = sum(item.price for item in group) / Decimal(len(group))
            atr_values = [item.atr14 for item in group + [pivot] if item.atr14 is not None]
            atr_tolerance = (
                max(atr_values) * Decimal("0.50") if atr_values else Decimal(0)
            )
            tolerance = max(center * GROUPING_PCT[timeframe], atr_tolerance)
            if abs(pivot.price - center) <= tolerance:
                group.append(pivot)
            else:
                groups.append([pivot])
        for group in groups:
            center = _rounded(sum(item.price for item in group) / Decimal(len(group)))
            atr_values = [item.atr14 for item in group if item.atr14 is not None]
            atr = sum(atr_values) / Decimal(len(atr_values)) if atr_values else Decimal(0)
            padding = min(atr * Decimal("0.10"), center * Decimal("0.01"))
            raw_low = min(item.price for item in group) - padding
            raw_high = max(item.price for item in group) + padding
            width_cap = center * GROUPING_PCT[timeframe] * Decimal(2)
            if raw_high - raw_low > width_cap:
                low = center - width_cap / Decimal(2)
                high = center + width_cap / Decimal(2)
            else:
                low, high = raw_low, raw_high
            low, high = _rounded(max(low, Decimal(0))), _rounded(high)
            confirmed = sum(item.status == "CONFIRMED" for item in group)
            structural = TIMEFRAME_IMPORTANCE[timeframe] * 10 + min(len(group), 9)
            last_date = max(item.bar_date for item in group)
            sources = tuple(_zone_source_for_pivot(item, timeframe) for item in group)
            output.append(
                TechnicalZone(
                    zone_id=_stable_id(
                        "v3-pivot-zone", ticker, timeframe, kind, low, high, *(s.source_id for s in sources)
                    ),
                    ticker=ticker,
                    timeframe=timeframe,
                    low=low,
                    high=high,
                    center=center,
                    current_role=_role(low, high, current_price),
                    structural_importance=structural,
                    proximity_pct=_proximity(low, high, current_price),
                    evidence_family_score=_rounded(Decimal(1) + Decimal(len(group) - 1) * Decimal("0.25")),
                    confirmation_quality=_rounded(Decimal(confirmed) / Decimal(len(group))),
                    reaction_count=len(group),
                    last_meaningful_interaction=last_date,
                    sources=sources,
                )
            )
    return rank_zones(output)


def _bollinger_sources(
    bars: Sequence[PriceBar],
    *,
    ticker: str,
    timeframe: Timeframe,
) -> tuple[ZoneSource, ...]:
    if len(bars) < 20:
        return ()
    closes = [float(bar.close) for bar in bars[-20:]]
    mean = Decimal(str(statistics.fmean(closes)))
    deviation = Decimal(str(statistics.pstdev(closes)))
    points = {
        "LOWER_20_2": mean - deviation * Decimal(2),
        "MID_20": mean,
        "UPPER_20_2": mean + deviation * Decimal(2),
    }
    return tuple(
        ZoneSource(
            source_id=_stable_id("v3-bollinger", ticker, timeframe, name, price, bars[-1].date),
            evidence_type="BOLLINGER",
            evidence_family=f"BOLLINGER_{timeframe.upper()}",
            method_family=name,
            source_timeframe=timeframe,
            source_degree=f"{timeframe.upper()}_PRICE_STRUCTURE",
            confluence_target_timeframe=timeframe,
            price=_rounded(price),
            status="CONFIRMED",
        )
        for name, price in points.items()
        if price > 0
    )


def _balance_box_source(
    bars: Sequence[PriceBar],
    *,
    ticker: str,
    timeframe: Timeframe,
) -> ZoneSource | None:
    window = BOX_WINDOWS[timeframe]
    if len(bars) < window:
        return None
    recent = bars[-window:]
    closes = sorted(bar.close for bar in recent)
    low = closes[len(closes) // 4]
    high = closes[(len(closes) * 3) // 4]
    center = (low + high) / Decimal(2)
    if center <= 0 or (high - low) / center > Decimal("0.15"):
        return None
    inside = sum(low <= bar.close <= high for bar in recent)
    if inside / len(recent) < 0.55:
        return None
    return ZoneSource(
        source_id=_stable_id("v3-balance-box", ticker, timeframe, low, high, recent[-1].date),
        evidence_type="BOX",
        evidence_family="BALANCE_BOX",
        method_family="CLOSE_OCCUPANCY_IQR",
        source_timeframe=timeframe,
        source_degree=f"{timeframe.upper()}_PRICE_STRUCTURE",
        confluence_target_timeframe=timeframe,
        price=_rounded(center),
        status="CONFIRMED",
    )


def _running_high(bars: Sequence[PriceBar], start: str, end: str) -> Decimal:
    return max(bar.high for bar in bars if start <= bar.date <= end)


def _running_low(bars: Sequence[PriceBar], start: str, end: str) -> Decimal:
    return min(bar.low for bar in bars if start <= bar.date <= end)


def _fib_fit(value: Decimal, references: Sequence[Decimal]) -> Decimal:
    return min(abs(value - reference) for reference in references)


def _endpoint(label: str, pivot: PivotPoint) -> WaveEndpoint:
    return WaveEndpoint(
        label=label,  # type: ignore[arg-type]
        pivot_ref=pivot.pivot_id,
        date=pivot.bar_date,
        price=pivot.price,
        status=pivot.status,
    )


def _weekly_confirmations(
    endpoints: Sequence[WaveEndpoint],
    weekly_pivots: Sequence[PivotPoint],
) -> tuple[str, ...]:
    refs: list[str] = []
    for endpoint in endpoints:
        expected_kind = "LOW" if endpoint.label in {"W0", "W2", "W4"} else "HIGH"
        endpoint_ordinal = _date_ordinal(endpoint.date)
        for pivot in weekly_pivots:
            if pivot.kind != expected_kind or pivot.price == 0:
                continue
            date_distance = abs(_date_ordinal(pivot.bar_date) - endpoint_ordinal)
            price_distance = abs(pivot.price - endpoint.price) / endpoint.price
            if date_distance <= 45 and price_distance <= Decimal("0.06"):
                refs.append(pivot.pivot_id)
                break
    return tuple(refs)


def _date_ordinal(value: str) -> int:
    year, month, day = (int(part) for part in value[:10].split("-"))
    return year * 372 + month * 31 + day


def _month_distance(start: str, end: str) -> int:
    start_year, start_month, _ = (int(part) for part in start[:10].split("-"))
    end_year, end_month, _ = (int(part) for part in end[:10].split("-"))
    return max((end_year - start_year) * 12 + end_month - start_month, 0)


def _monthly_wave_degree(span_months: int) -> WaveDegree:
    if span_months >= 84:
        return "GRAND_CYCLE"
    if span_months >= 24:
        return "PRIMARY_CURRENT_CYCLE"
    return "INTERMEDIATE"


def generate_primary_monthly_hypotheses(
    monthly_bars: Sequence[PriceBar],
    monthly_pivots: Sequence[PivotPoint],
    weekly_pivots: Sequence[PivotPoint],
    *,
    ticker: str,
    max_hypotheses: int = 8,
    search_horizon: int = 180,
) -> tuple[MonthlyWaveHypothesis, ...]:
    if len(monthly_bars) < 12:
        return ()
    search_start = monthly_bars[max(0, len(monthly_bars) - search_horizon)].date
    pivots = [pivot for pivot in monthly_pivots if pivot.bar_date >= search_start]
    lows = [pivot for pivot in pivots if pivot.kind == "LOW"][-16:]
    highs = [pivot for pivot in pivots if pivot.kind == "HIGH"][-20:]
    hypotheses: list[MonthlyWaveHypothesis] = []
    for w0 in lows:
        w1s = [
            pivot
            for pivot in highs
            if pivot.bar_date > w0.bar_date
            and pivot.price > w0.price
            and pivot.price == _running_high(monthly_bars, w0.bar_date, pivot.bar_date)
        ][-6:]
        for w1 in w1s:
            w2s = [
                pivot
                for pivot in lows
                if pivot.bar_date > w1.bar_date
                and w0.price < pivot.price < w1.price
                and pivot.price == _running_low(monthly_bars, w1.bar_date, pivot.bar_date)
            ][-5:]
            for w2 in w2s:
                w3s = [
                    pivot
                    for pivot in highs
                    if pivot.bar_date > w2.bar_date
                    and pivot.price > w1.price
                    and pivot.price == _running_high(monthly_bars, w2.bar_date, pivot.bar_date)
                ][-5:]
                for w3 in w3s:
                    w4s = [
                        pivot
                        for pivot in lows
                        if pivot.bar_date > w3.bar_date
                        and w1.price < pivot.price < w3.price
                        and pivot.price == _running_low(monthly_bars, w3.bar_date, pivot.bar_date)
                    ][-4:]
                    for w4 in w4s:
                        w5_candidates = [
                            pivot
                            for pivot in highs
                            if pivot.bar_date > w4.bar_date and pivot.price > w3.price
                        ]
                        w5 = w5_candidates[-1] if w5_candidates else None
                        wave1 = w1.price - w0.price
                        wave3 = w3.price - w2.price
                        wave5 = w5.price - w4.price if w5 is not None else None
                        hard_rules = {
                            "w1_above_w0": w1.price > w0.price,
                            "w1_running_max": w1.price
                            == _running_high(monthly_bars, w0.bar_date, w1.bar_date),
                            "w2_between_w0_w1": w0.price < w2.price < w1.price,
                            "w2_deepest_low": w2.price
                            == _running_low(monthly_bars, w1.bar_date, w2.bar_date),
                            "w3_above_w1": w3.price > w1.price,
                            "w3_running_max": w3.price
                            == _running_high(monthly_bars, w2.bar_date, w3.bar_date),
                            "w4_above_w1_below_w3": w1.price < w4.price < w3.price,
                            "w4_deepest_low": w4.price
                            == _running_low(monthly_bars, w3.bar_date, w4.bar_date),
                            "w5_above_w3_or_unconfirmed": w5 is None or w5.price > w3.price,
                            "w3_not_shortest": (
                                w5 is None or wave5 is None or wave3 >= min(wave1, wave5)
                            ),
                        }
                        if not all(hard_rules.values()):
                            continue
                        w2_ratio = (w1.price - w2.price) / wave1
                        w4_ratio = (w3.price - w4.price) / wave3
                        fib_penalty = _fib_fit(
                            w2_ratio,
                            (Decimal("0.382"), Decimal("0.5"), Decimal("0.618"), Decimal("0.786")),
                        ) + _fib_fit(
                            w4_ratio,
                            (Decimal("0.236"), Decimal("0.382"), Decimal("0.5"), Decimal("0.618")),
                        )
                        endpoints = [_endpoint("W0", w0), _endpoint("W1", w1), _endpoint("W2", w2), _endpoint("W3", w3), _endpoint("W4", w4)]
                        if w5 is not None:
                            endpoints.append(_endpoint("W5", w5))
                        confirmations = _weekly_confirmations(endpoints, weekly_pivots)
                        confirmed_count = sum(point.status == "CONFIRMED" for point in endpoints)
                        provisional_count = len(endpoints) - confirmed_count
                        magnitude = Decimal(str(math.log(float(w3.price / w0.price))))
                        recency = Decimal(_date_ordinal(w4.bar_date)) / Decimal(1_000_000)
                        components = {
                            "hard_rule": Decimal(10),
                            "magnitude": _rounded(magnitude),
                            "fib_fit": _rounded(max(Decimal(0), Decimal(2) - fib_penalty * Decimal(5))),
                            "weekly_confirmation": Decimal(len(confirmations)) * Decimal("0.5"),
                            "confirmation": Decimal(confirmed_count) * Decimal("0.25")
                            - Decimal(provisional_count) * Decimal("0.25"),
                            "recency": _rounded(recency),
                        }
                        score = _rounded(sum(components.values()))
                        status = (
                            "VALID_CONFIRMED"
                            if provisional_count == 0
                            else "VALID_PROVISIONAL"
                        )
                        hypotheses.append(
                            MonthlyWaveHypothesis(
                                hypothesis_id=_stable_id(
                                    "v3-monthly-wave",
                                    ticker,
                                    *(point.pivot_ref for point in endpoints),
                                ),
                                ticker=ticker,
                                status=status,
                                wave_state=(
                                    "W5_CANDIDATE"
                                    if w5 is not None
                                    else "W4_CANDIDATE_W5_UNCONFIRMED"
                                ),
                                endpoints=tuple(endpoints),
                                hard_rules=hard_rules,
                                score=score,
                                score_components=components,
                                weekly_confirmation_refs=confirmations,
                            )
                        )
    unique = {hypothesis.hypothesis_id: hypothesis for hypothesis in hypotheses}
    if not unique:
        return ()
    classified: list[MonthlyWaveHypothesis] = []
    for item in unique.values():
        w0_date = next(point.date for point in item.endpoints if point.label == "W0")
        span_months = _month_distance(w0_date, item.endpoints[-1].date)
        degree = _monthly_wave_degree(span_months)
        components = dict(item.score_components)
        components["magnitude"] = min(components["magnitude"], Decimal(2))
        if degree == "PRIMARY_CURRENT_CYCLE":
            recency_fit = Decimal(max(84 - span_months, 0)) / Decimal(30)
        elif degree == "GRAND_CYCLE":
            recency_fit = min(Decimal(span_months) / Decimal(120), Decimal(1))
        else:
            recency_fit = Decimal(span_months) / Decimal(24)
        components["degree_fit"] = Decimal(2)
        components["degree_recency_fit"] = _rounded(recency_fit)
        components.pop("recency", None)
        score = _rounded(sum(components.values()))
        classified.append(
            item.model_copy(
                update={
                    "hypothesis_id": _stable_id(
                        "v3-monthly-wave",
                        ticker,
                        degree,
                        *(point.pivot_ref for point in item.endpoints),
                    ),
                    "source_degree": degree,
                    "score_components": components,
                    "score": score,
                }
            )
        )

    def ordered(values: Sequence[MonthlyWaveHypothesis]) -> list[MonthlyWaveHypothesis]:
        return sorted(
            values,
            key=lambda item: (item.score, item.endpoints[-1].date, item.hypothesis_id),
            reverse=True,
        )[:max_hypotheses]

    current = ordered(
        [item for item in classified if item.source_degree == "PRIMARY_CURRENT_CYCLE"]
    )
    grand = ordered([item for item in classified if item.source_degree == "GRAND_CYCLE"])
    intermediate = ordered(
        [item for item in classified if item.source_degree == "INTERMEDIATE"]
    )
    return tuple(current + grand + intermediate)


def validate_wave_hypothesis_selection(
    selection: WaveHypothesisSelection,
    hypotheses: Sequence[MonthlyWaveHypothesis],
    *,
    ticker: str | None = None,
    cutoff: str | None = None,
    adjustment_basis: str | None = None,
    strict_context: bool = False,
    equivalence_class_members: Mapping[str, Sequence[str]] | None = None,
) -> WaveSelectionValidation:
    hypothesis_map = {hypothesis.hypothesis_id: hypothesis for hypothesis in hypotheses}
    valid_ids = set(hypothesis_map)
    errors: list[str] = []
    if selection.status == WaveSelectionStatus.SELECTED:
        if selection.hypothesis_id not in valid_ids:
            errors.append("unknown_hypothesis_id")
        if selection.alternative_hypothesis_id is not None and (
            selection.alternative_hypothesis_id not in valid_ids
        ):
            errors.append("unknown_alternative_hypothesis_id")
        if selection.competing_hypothesis_ids:
            errors.append("selected_requires_empty_competing_ids")
        selected = hypothesis_map.get(selection.hypothesis_id or "")
        alternative = hypothesis_map.get(selection.alternative_hypothesis_id or "")
        if selected is not None and alternative is not None:
            if alternative.hypothesis_id == selected.hypothesis_id:
                errors.append("alternative_matches_selected_hypothesis_id")
            if alternative.ticker != selected.ticker:
                errors.append("alternative_ticker_mismatch")
            if alternative.source_degree != selected.source_degree:
                errors.append("alternative_degree_mismatch")
        if ticker is not None and selection.ticker != ticker:
            errors.append("ticker_mismatch")
        if (
            selected is not None
            and selection.source_degree is not None
            and selection.source_degree != selected.source_degree
        ):
            errors.append("source_degree_mismatch")
        if cutoff is not None and selection.cutoff != cutoff:
            errors.append("cutoff_mismatch")
        if adjustment_basis is not None and selection.adjustment_basis != adjustment_basis:
            errors.append("adjustment_basis_mismatch")
        if selected is not None:
            expected_refs = tuple(point.pivot_ref for point in selected.endpoints)
            if selection.endpoint_refs and selection.endpoint_refs != expected_refs:
                errors.append("endpoint_refs_mismatch")
            if cutoff is not None and any(point.date > cutoff for point in selected.endpoints):
                errors.append("future_endpoint")
        if selection.equivalence_class_id is not None:
            members = set(
                (equivalence_class_members or {}).get(selection.equivalence_class_id, ())
            )
            if not members:
                errors.append("unknown_equivalence_class_id")
            elif selection.hypothesis_id not in members or (
                selection.alternative_hypothesis_id is not None
                and selection.alternative_hypothesis_id not in members
            ):
                errors.append("hypothesis_equivalence_class_mismatch")
        if strict_context:
            if selection.ticker is None:
                errors.append("missing_ticker")
            if selection.source_degree is None:
                errors.append("missing_source_degree")
            if selection.cutoff is None:
                errors.append("missing_cutoff")
            if selection.adjustment_basis is None:
                errors.append("missing_adjustment_basis")
            if not selection.endpoint_refs:
                errors.append("missing_endpoint_refs")
        return WaveSelectionValidation(valid=not errors, errors=tuple(errors))
    if selection.hypothesis_id is not None or selection.alternative_hypothesis_id is not None:
        errors.append("abstention_requires_null_ids")
    if selection.status == WaveSelectionStatus.AMBIGUOUS and selection.competing_hypothesis_ids:
        competing = selection.competing_hypothesis_ids
        if len(competing) < 2 or len(set(competing)) != len(competing):
            errors.append("ambiguous_requires_two_or_three_unique_ids")
        unknown = [value for value in competing if value not in valid_ids]
        if unknown:
            errors.append("unknown_competing_hypothesis_id")
        known = [hypothesis_map[value] for value in competing if value in hypothesis_map]
        if len({item.ticker for item in known}) > 1:
            errors.append("competing_ticker_mismatch")
        if len({item.source_degree for item in known}) > 1:
            errors.append("competing_degree_mismatch")
        if (
            selection.source_degree is not None
            and known
            and any(item.source_degree != selection.source_degree for item in known)
        ):
            errors.append("source_degree_mismatch")
        if selection.equivalence_class_id is not None:
            members = set(
                (equivalence_class_members or {}).get(selection.equivalence_class_id, ())
            )
            if not members:
                errors.append("unknown_equivalence_class_id")
            elif not set(competing).issubset(members):
                errors.append("competing_equivalence_class_mismatch")
        if ticker is not None and selection.ticker is not None and selection.ticker != ticker:
            errors.append("ticker_mismatch")
        if cutoff is not None and selection.cutoff is not None and selection.cutoff != cutoff:
            errors.append("cutoff_mismatch")
        if (
            adjustment_basis is not None
            and selection.adjustment_basis is not None
            and selection.adjustment_basis != adjustment_basis
        ):
            errors.append("adjustment_basis_mismatch")
    elif selection.competing_hypothesis_ids:
        errors.append("insufficient_structure_requires_empty_competing_ids")
    if selection.status == WaveSelectionStatus.INSUFFICIENT_STRUCTURE and (
        selection.equivalence_class_id is not None
    ):
        errors.append("insufficient_structure_requires_null_class")
    return WaveSelectionValidation(
        valid=not errors,
        errors=tuple(errors),
        valid_abstention=not errors,
    )


def classify_wave_selection_consensus(
    selections: Sequence[WaveHypothesisSelection],
    hypotheses: Sequence[MonthlyWaveHypothesis],
) -> Literal["STABLE", "MINOR_VARIATION", "MATERIAL_VARIATION", "VALID_ABSTENTION"]:
    if not selections:
        return "MATERIAL_VARIATION"
    validations = [validate_wave_hypothesis_selection(selection, hypotheses) for selection in selections]
    if not all(validation.valid for validation in validations):
        return "MATERIAL_VARIATION"
    if all(validation.valid_abstention for validation in validations):
        return "VALID_ABSTENTION"
    ids = [selection.hypothesis_id for selection in selections]
    if len(set(ids)) == 1 and None not in ids:
        return "STABLE"
    hypothesis_map = {hypothesis.hypothesis_id: hypothesis for hypothesis in hypotheses}
    selected = [hypothesis_map[value] for value in ids if value in hypothesis_map]
    if len(selected) != len(selections):
        return "MATERIAL_VARIATION"
    signatures = {
        (
            item.status,
            item.wave_state,
            tuple((point.label, point.date) for point in item.endpoints[-2:]),
        )
        for item in selected
    }
    return "MINOR_VARIATION" if len(signatures) == 1 else "MATERIAL_VARIATION"


def calculate_wave_fibonacci(
    hypothesis: MonthlyWaveHypothesis,
    *,
    ticker: str,
    currency: str,
    as_of: str,
    targets: Sequence[Timeframe] = TIMEFRAME_ORDER,
) -> tuple[FibonacciReference, ...]:
    endpoints = {point.label: point for point in hypothesis.endpoints}
    required = {"W0", "W1", "W2", "W3", "W4"}
    if not required.issubset(endpoints):
        return ()
    w0, w1, w2, w3, w4 = (endpoints[label] for label in ("W0", "W1", "W2", "W3", "W4"))
    provisional = any(point.status == "PROVISIONAL" for point in (w3, w4))
    families: list[tuple[str, str, tuple[str, ...], str, Decimal, tuple[Decimal, ...], str]] = [
        (
            "WAVE1_RETRACEMENT",
            "WAVE1_RETRACEMENT",
            (w0.pivot_ref, w1.pivot_ref),
            "W1-(W1-W0)*ratio",
            w1.price,
            (w1.price - w0.price,),
            "subtract",
        ),
        (
            "WAVE3_RETRACEMENT",
            "WAVE3_RETRACEMENT",
            (w2.pivot_ref, w3.pivot_ref),
            "W3-(W3-W2)*ratio",
            w3.price,
            (w3.price - w2.price,),
            "subtract",
        ),
        (
            "PRIMARY_CYCLE_RETRACEMENT",
            "PRIMARY_CYCLE_RETRACEMENT",
            (w0.pivot_ref, w3.pivot_ref),
            "W3-(W3-W0)*ratio",
            w3.price,
            (w3.price - w0.price,),
            "subtract",
        ),
        (
            "CURRENT_REBOUND",
            "CURRENT_REBOUND",
            (w3.pivot_ref, w4.pivot_ref),
            "W4+(W3-W4)*ratio",
            w4.price,
            (w3.price - w4.price,),
            "add",
        ),
    ]
    references: list[FibonacciReference] = []
    for family, method, refs, formula, base, spans, operation in families:
        ratios = (
            Decimal("0.236"),
            Decimal("0.382"),
            Decimal("0.500"),
            Decimal("0.618"),
            Decimal("0.786"),
        )
        for ratio in ratios:
            price = base - spans[0] * ratio if operation == "subtract" else base + spans[0] * ratio
            for target in targets:
                references.append(
                    _fib_reference(
                        hypothesis,
                        ticker=ticker,
                        currency=currency,
                        as_of=as_of,
                        target=target,
                        family=family,
                        method=method,
                        ratio=ratio,
                        refs=refs,
                        formula=formula,
                        price=price,
                        status="PROVISIONAL" if provisional else "CONFIRMED",
                    )
                )
    projections = (
        ("WAVE1_MULTIPLE", w1.price - w0.price, (Decimal("0.618"), Decimal("1.0"), Decimal("1.618"), Decimal("2.618")), (w0.pivot_ref, w1.pivot_ref, w4.pivot_ref), "W4+(W1-W0)*ratio"),
        ("WAVE3_MULTIPLE", w3.price - w2.price, (Decimal("0.382"), Decimal("0.5"), Decimal("0.618"), Decimal("1.0")), (w2.pivot_ref, w3.pivot_ref, w4.pivot_ref), "W4+(W3-W2)*ratio"),
        ("SPAN03_MULTIPLE", w3.price - w0.price, (Decimal("0.5"), Decimal("0.618"), Decimal("1.0")), (w0.pivot_ref, w3.pivot_ref, w4.pivot_ref), "W4+(W3-W0)*ratio"),
    )
    for method, span, ratios, refs, formula in projections:
        for ratio in ratios:
            for target in targets:
                references.append(
                    _fib_reference(
                        hypothesis,
                        ticker=ticker,
                        currency=currency,
                        as_of=as_of,
                        target=target,
                        family="WAVE5_PROJECTION",
                        method=method,
                        ratio=ratio,
                        refs=refs,
                        formula=formula,
                        price=w4.price + span * ratio,
                        status="PROJECTION",
                    )
                )
    return tuple(references)


def _fib_reference(
    hypothesis: MonthlyWaveHypothesis,
    *,
    ticker: str,
    currency: str,
    as_of: str,
    target: Timeframe,
    family: str,
    method: str,
    ratio: Decimal,
    refs: tuple[str, ...],
    formula: str,
    price: Decimal,
    status: str,
) -> FibonacciReference:
    calculated = _rounded(price)
    return FibonacciReference(
        fib_id=_stable_id(
            "v3-wave-fib",
            ticker,
            hypothesis.hypothesis_id,
            family,
            method,
            ratio,
            target,
            calculated,
        ),
        ticker=ticker,
        currency=currency,
        source_timeframe="monthly",
        source_degree=hypothesis.source_degree,
        confluence_target_timeframe=target,
        wave_hypothesis_id=hypothesis.hypothesis_id,
        family=family,  # type: ignore[arg-type]
        method_family=method,
        ratio=str(ratio),
        endpoint_refs=refs,
        formula=formula,
        calculated_price=calculated,
        status=status,  # type: ignore[arg-type]
        as_of=as_of,
        required_endpoint_labels=tuple(
            point.label
            for point in hypothesis.endpoints
            if point.pivot_ref in refs
        ),
    )


def _fib_source(reference: FibonacciReference) -> ZoneSource:
    return ZoneSource(
        source_id=reference.fib_id,
        evidence_type="FIBONACCI",
        evidence_family=reference.family,
        method_family=reference.method_family,
        source_timeframe=reference.source_timeframe,
        source_degree=reference.source_degree,
        confluence_target_timeframe=reference.confluence_target_timeframe,
        price=reference.calculated_price,
        status=reference.status,
        family_stability=reference.family_stability,
        consensus_set_id=reference.consensus_set_id,
        equivalence_class_id=reference.equivalence_class_id,
    )


def _source_key(source: ZoneSource) -> tuple[str, str, str, str]:
    if source.evidence_type == "FIBONACCI":
        return (
            source.evidence_type,
            source.evidence_family,
            source.method_family,
            source.source_degree,
        )
    return (
        source.evidence_type,
        source.evidence_family,
        source.source_timeframe,
        source.method_family,
    )


def _source_score(sources: Sequence[ZoneSource]) -> Decimal:
    base = {
        "PIVOT": Decimal("1.0"),
        "BOLLINGER": Decimal("1.2"),
        "FIBONACCI": Decimal("1.4"),
        "BOX": Decimal("1.1"),
        "PRIOR_HIGH_LOW": Decimal("1.0"),
    }
    score = Decimal(0)
    seen: set[tuple[str, str, str, str]] = set()
    for source in sources:
        key = _source_key(source)
        if key in seen:
            continue
        seen.add(key)
        score += base[source.evidence_type]
    types = {source.evidence_type for source in sources}
    timeframes = {source.source_timeframe for source in sources}
    if len(types) > 1:
        score += Decimal("0.5") * Decimal(len(types) - 1)
    if len(timeframes) > 1:
        score += Decimal("0.75") * Decimal(len(timeframes) - 1)
    return _rounded(score)


def merge_zone_sources(
    sources: Sequence[ZoneSource],
    *,
    ticker: str,
    timeframe: Timeframe,
    current_price: Decimal,
) -> tuple[TechnicalZone, ...]:
    ordered = sorted(sources, key=lambda item: (item.price, item.source_id))
    groups: list[list[ZoneSource]] = []
    for source in ordered:
        if not groups:
            groups.append([source])
            continue
        group = groups[-1]
        candidate_prices = [item.price for item in group] + [source.price]
        center = sum(candidate_prices) / Decimal(len(candidate_prices))
        width = max(candidate_prices) - min(candidate_prices)
        if width <= center * CONFLUENCE_PCT[timeframe]:
            group.append(source)
        else:
            groups.append([source])
    zones: list[TechnicalZone] = []
    for group in groups:
        center = _rounded(sum(item.price for item in group) / Decimal(len(group)))
        padding = center * Decimal("0.0025")
        low = _rounded(max(Decimal(0), min(item.price for item in group) - padding))
        high = _rounded(max(item.price for item in group) + padding)
        unique_families = {_source_key(source) for source in group}
        confirmation = Decimal(
            sum(source.status == "CONFIRMED" for source in group)
        ) / Decimal(len(group))
        fib_stabilities = {
            source.family_stability
            for source in group
            if source.evidence_type == "FIBONACCI" and source.family_stability is not None
        }
        confluence_stability = None
        if "PRICE_EQUIVALENT" in fib_stabilities:
            confluence_stability = "CONFLUENCE_PRICE_EQUIVALENT"
        elif "EXACT_INVARIANT" in fib_stabilities:
            confluence_stability = "CONFLUENCE_EXACT_INVARIANT"
        zones.append(
            TechnicalZone(
                zone_id=_stable_id(
                    "v3-zone", ticker, timeframe, low, high, *(source.source_id for source in group)
                ),
                ticker=ticker,
                timeframe=timeframe,
                low=low,
                high=high,
                center=center,
                current_role=_role(low, high, current_price),
                structural_importance=max(
                    TIMEFRAME_IMPORTANCE[source.source_timeframe] for source in group
                )
                * 10
                + min(len(unique_families), 9),
                proximity_pct=_proximity(low, high, current_price),
                evidence_family_score=_source_score(group),
                confirmation_quality=_rounded(confirmation),
                reaction_count=sum(source.evidence_type == "PIVOT" for source in group),
                last_meaningful_interaction=None,
                sources=tuple(group),
                confluence_stability=confluence_stability,
            )
        )
    return rank_zones(zones)


def rank_zones(zones: Sequence[TechnicalZone], limit: int = 12) -> tuple[TechnicalZone, ...]:
    return tuple(
        sorted(
            zones,
            key=lambda zone: (
                zone.structural_importance,
                zone.evidence_family_score,
                zone.confirmation_quality,
                zone.reaction_count,
                -zone.proximity_pct,
                zone.center,
            ),
            reverse=True,
        )[:limit]
    )


def build_timeframe_zone_map(
    *,
    ticker: str,
    timeframe: Timeframe,
    bars: Sequence[PriceBar],
    pivot_zones: Sequence[TechnicalZone],
    fibonacci: Sequence[FibonacciReference],
    current_price: Decimal,
) -> tuple[TechnicalZone, ...]:
    sources: list[ZoneSource] = []
    for zone in pivot_zones:
        sources.extend(zone.sources)
    sources.extend(_bollinger_sources(bars, ticker=ticker, timeframe=timeframe))
    box = _balance_box_source(bars, ticker=ticker, timeframe=timeframe)
    if box is not None:
        sources.append(box)
    sources.extend(
        _fib_source(reference)
        for reference in fibonacci
        if reference.confluence_target_timeframe == timeframe
    )
    return merge_zone_sources(
        sources,
        ticker=ticker,
        timeframe=timeframe,
        current_price=current_price,
    )


def build_cross_timeframe_confluence(
    maps: Mapping[Timeframe, Sequence[TechnicalZone]],
    *,
    ticker: str,
    current_price: Decimal,
) -> tuple[TechnicalZone, ...]:
    sources: list[ZoneSource] = []
    for timeframe in TIMEFRAME_ORDER:
        for zone in maps.get(timeframe, ())[:8]:
            sources.extend(zone.sources)
    merged = merge_zone_sources(
        sources,
        ticker=ticker,
        timeframe="daily",
        current_price=current_price,
    )
    return tuple(
        zone
        for zone in merged
        if len({source.source_timeframe for source in zone.sources}) >= 2
        and len({_source_key(source) for source in zone.sources}) >= 2
    )


def _primary_status(
    hypotheses: Sequence[MonthlyWaveHypothesis],
) -> HypothesisStatus:
    if not hypotheses:
        return "NONE"
    if len(hypotheses) >= 2 and hypotheses[0].score - hypotheses[1].score < Decimal("0.25"):
        return "AMBIGUOUS"
    return hypotheses[0].status


def _compact_decimal(value: Decimal, *, grouped: bool = False) -> str:
    rendered = format(value.normalize(), "f")
    if "." in rendered:
        rendered = rendered.rstrip("0").rstrip(".")
    if not grouped:
        return rendered
    integer, dot, fraction = rendered.partition(".")
    grouped_integer = f"{int(integer):,}"
    return f"{grouped_integer}{dot}{fraction}" if dot else grouped_integer


def _outward_display_bounds(
    low: Decimal,
    high: Decimal,
    *,
    preferred_quantum: Decimal,
    current_price: Decimal | None,
    role: ZoneRole | None,
) -> tuple[Decimal, Decimal]:
    quantum = preferred_quantum
    for _ in range(12):
        displayed_low = (low / quantum).to_integral_value(rounding=ROUND_FLOOR) * quantum
        displayed_high = (high / quantum).to_integral_value(rounding=ROUND_CEILING) * quantum
        if (
            current_price is None
            or role is None
            or _role(displayed_low, displayed_high, current_price) == role
        ):
            return displayed_low, displayed_high
        quantum /= Decimal(10)
    return low, high


def format_technical_price_zone(
    low: Decimal,
    high: Decimal,
    *,
    currency: str,
    current_price: Decimal | None = None,
    role: ZoneRole | None = None,
) -> str:
    """Format a technical zone without changing its canonical numeric bounds."""
    if low > high:
        raise ValueError("technical zone low must not exceed high")
    preferred_quantum = Decimal("1000") if currency == "KRW" else Decimal("0.01")
    displayed_low, displayed_high = _outward_display_bounds(
        low,
        high,
        preferred_quantum=preferred_quantum,
        current_price=current_price,
        role=role,
    )
    if currency == "KRW":
        if max(abs(displayed_low), abs(displayed_high)) >= Decimal("10000"):
            rendered_low = _compact_decimal(displayed_low / Decimal("10000"))
            rendered_high = _compact_decimal(displayed_high / Decimal("10000"))
            return f"약 {rendered_low}만~{rendered_high}만원"
        return (
            f"약 {_compact_decimal(displayed_low, grouped=True)}"
            f"~{_compact_decimal(displayed_high, grouped=True)}원"
        )
    prefix = {"USD": "$", "TWD": "NT$", "JPY": "¥", "EUR": "€"}.get(currency)
    rendered_low = _compact_decimal(displayed_low, grouped=True)
    rendered_high = _compact_decimal(displayed_high, grouped=True)
    if prefix is not None:
        return f"약 {prefix}{rendered_low}~{prefix}{rendered_high}"
    return f"약 {rendered_low}~{rendered_high} {currency}"


def _render_zone(
    zone: TechnicalZone | None,
    currency: str,
    *,
    current_price: Decimal | None,
) -> str:
    if zone is None:
        return "없음"
    rendered = format_technical_price_zone(
        zone.low,
        zone.high,
        currency=currency,
        current_price=current_price,
        role=zone.current_role,
    )
    return f"{rendered} ({zone.current_role})"


def render_shadow_v3(
    *,
    result_maps: Mapping[Timeframe, Sequence[TechnicalZone]],
    hypotheses: Sequence[MonthlyWaveHypothesis],
    primary_status: HypothesisStatus,
    cross: Sequence[TechnicalZone],
    currency: str,
    current_price: Decimal | None = None,
) -> str:
    labels = {"monthly": "월봉 — 구조", "weekly": "주봉 — 중기", "daily": "일봉 — 단기"}
    lines = ["📐 가격 구조 v3 (shadow)"]
    for timeframe in TIMEFRAME_ORDER:
        zones = result_maps.get(timeframe, ())
        supports = [zone for zone in zones if zone.current_role == "SUPPORT"]
        resistances = [zone for zone in zones if zone.current_role == "RESISTANCE"]
        nearest_support = min(supports, key=lambda zone: zone.proximity_pct, default=None)
        nearest_resistance = min(resistances, key=lambda zone: zone.proximity_pct, default=None)
        lines.append(labels[timeframe])
        lines.append(
            f"• 지지: {_render_zone(nearest_support, currency, current_price=current_price)}"
        )
        lines.append(
            f"• 저항: {_render_zone(nearest_resistance, currency, current_price=current_price)}"
        )
        if timeframe == "monthly":
            if hypotheses:
                lines.append(f"• 파동: {hypotheses[0].wave_state} / {primary_status}")
            else:
                lines.append("• 파동: 유효한 bullish standard impulse 없음")
    nearest = min(cross, key=lambda zone: zone.proximity_pct, default=None)
    structural = max(cross, key=lambda zone: zone.structural_importance, default=None)
    lines.append("종합")
    lines.append(
        f"• 가장 가까운 교차구간: {_render_zone(nearest, currency, current_price=current_price)}"
    )
    lines.append(
        f"• 가장 중요한 구조구간: {_render_zone(structural, currency, current_price=current_price)}"
    )
    lines.append("• provisional/projection은 확인 후보이며 목표가가 아닙니다.")
    return "\n".join(lines)


def build_price_structure_wave_fib_v3(
    *,
    ticker: str,
    security_id: str,
    market: Literal["KR", "US"],
    currency: str,
    adjustment_basis: str,
    cutoff: str,
    raw_by_timeframe: Mapping[Timeframe, Sequence[Mapping[str, object]]],
    observed_at: str | None = None,
    provider_limit: int | None = PROVIDER_INTERFACE_LIMIT,
) -> PriceStructureWaveFibV3Result:
    started = time.perf_counter()
    histories: dict[Timeframe, tuple[PriceBar, ...]] = {}
    coverage: dict[Timeframe, LongHistoryCoverage] = {}
    pivots: dict[Timeframe, tuple[PivotPoint, ...]] = {}
    sr_maps: dict[Timeframe, tuple[TechnicalZone, ...]] = {}
    for timeframe in TIMEFRAME_ORDER:
        bars, item_coverage = prepare_long_history(
            raw_by_timeframe.get(timeframe, ()),
            timeframe=timeframe,
            cutoff=cutoff,
            adjustment_basis=adjustment_basis,
            market=market,
            observed_at=observed_at,
            provider_limit=provider_limit,
        )
        histories[timeframe] = bars
        coverage[timeframe] = item_coverage
        pivots[timeframe] = detect_pivots(
            bars,
            ticker=ticker,
            timeframe=timeframe,
            adjustment_basis=adjustment_basis,
        )
    latest_bars = histories["daily"] or histories["weekly"] or histories["monthly"]
    current_price = latest_bars[-1].close if latest_bars else Decimal(0)
    for timeframe in TIMEFRAME_ORDER:
        sr_maps[timeframe] = build_pivot_zones(
            pivots[timeframe],
            ticker=ticker,
            timeframe=timeframe,
            current_price=current_price,
        )
    hypotheses = generate_primary_monthly_hypotheses(
        histories["monthly"],
        pivots["monthly"],
        pivots["weekly"],
        ticker=ticker,
    )
    current_cycle = tuple(
        item for item in hypotheses if item.source_degree == "PRIMARY_CURRENT_CYCLE"
    )
    primary_status = _primary_status(current_cycle)
    selected = current_cycle[0] if current_cycle and primary_status != "AMBIGUOUS" else None
    fibonacci = (
        calculate_wave_fibonacci(
            selected,
            ticker=ticker,
            currency=currency,
            as_of=cutoff,
        )
        if selected is not None
        else ()
    )
    maps: dict[Timeframe, tuple[TechnicalZone, ...]] = {}
    for timeframe in TIMEFRAME_ORDER:
        maps[timeframe] = build_timeframe_zone_map(
            ticker=ticker,
            timeframe=timeframe,
            bars=histories[timeframe],
            pivot_zones=sr_maps[timeframe],
            fibonacci=fibonacci,
            current_price=current_price,
        )
    cross = build_cross_timeframe_confluence(
        maps,
        ticker=ticker,
        current_price=current_price,
    )
    render = render_shadow_v3(
        result_maps=maps,
        hypotheses=hypotheses,
        primary_status=primary_status,
        cross=cross,
        currency=currency,
        current_price=current_price,
    )
    elapsed = _rounded(Decimal(str((time.perf_counter() - started) * 1000)))
    return PriceStructureWaveFibV3Result(
        ticker=ticker,
        security_id=security_id,
        market=market,
        currency=currency,
        adjustment_basis=adjustment_basis,
        as_of=cutoff,
        current_price=current_price,
        coverage=coverage,
        pivots=pivots,
        sr_maps=sr_maps,
        primary_monthly_hypotheses=hypotheses,
        selected_hypothesis_id=selected.hypothesis_id if selected is not None else None,
        primary_hypothesis_status=primary_status,
        fibonacci=fibonacci,
        timeframe_zone_maps=maps,
        cross_timeframe_confluence=cross,
        shadow_render=render,
        computation_ms=elapsed,
        degree_candidate_counts={
            degree: sum(item.source_degree == degree for item in hypotheses)
            for degree in (
                "GRAND_CYCLE",
                "PRIMARY_CURRENT_CYCLE",
                "INTERMEDIATE",
                "TACTICAL",
            )
        },
    )


def apply_wave_selection_feedback(
    result: PriceStructureWaveFibV3Result,
    selection: WaveHypothesisSelection,
    *,
    raw_by_timeframe: Mapping[Timeframe, Sequence[Mapping[str, object]]],
    observed_at: str | None = None,
    provider_limit: int | None = PROVIDER_INTERFACE_LIMIT,
) -> PriceStructureWaveFibV3Result:
    validation = validate_wave_hypothesis_selection(
        selection,
        result.primary_monthly_hypotheses,
        ticker=result.ticker,
        cutoff=result.as_of,
        adjustment_basis=result.adjustment_basis,
        strict_context=selection.status == WaveSelectionStatus.SELECTED,
    )
    selected = None
    if validation.valid and selection.status == WaveSelectionStatus.SELECTED:
        selected = next(
            (
                item
                for item in result.primary_monthly_hypotheses
                if item.hypothesis_id == selection.hypothesis_id
            ),
            None,
        )
    histories: dict[Timeframe, tuple[PriceBar, ...]] = {}
    for timeframe in TIMEFRAME_ORDER:
        histories[timeframe], _ = prepare_long_history(
            raw_by_timeframe.get(timeframe, ()),
            timeframe=timeframe,
            cutoff=result.as_of,
            adjustment_basis=result.adjustment_basis,
            market=result.market,
            observed_at=observed_at,
            provider_limit=provider_limit,
        )
    fibonacci = (
        calculate_wave_fibonacci(
            selected,
            ticker=result.ticker,
            currency=result.currency,
            as_of=result.as_of,
        )
        if selected is not None
        else ()
    )
    maps: dict[Timeframe, tuple[TechnicalZone, ...]] = {}
    for timeframe in TIMEFRAME_ORDER:
        maps[timeframe] = build_timeframe_zone_map(
            ticker=result.ticker,
            timeframe=timeframe,
            bars=histories[timeframe],
            pivot_zones=result.sr_maps[timeframe],
            fibonacci=fibonacci,
            current_price=result.current_price,
        )
    cross = build_cross_timeframe_confluence(
        maps,
        ticker=result.ticker,
        current_price=result.current_price,
    )
    selected_status: HypothesisStatus = selected.status if selected is not None else "NONE"
    render = render_shadow_v3(
        result_maps=maps,
        hypotheses=(selected,) if selected is not None else (),
        primary_status=selected_status,
        cross=cross,
        currency=result.currency,
        current_price=result.current_price,
    )
    audit = WaveFeedbackAudit(
        selection=selection,
        validation=validation,
        selected_hypothesis_id=selected.hypothesis_id if selected is not None else None,
        selected_hypothesis_fed_to_engine=selected is not None,
    )
    return result.model_copy(
        update={
            "selected_hypothesis_id": selected.hypothesis_id if selected is not None else None,
            "primary_hypothesis_status": selected_status,
            "fibonacci": fibonacci,
            "timeframe_zone_maps": maps,
            "cross_timeframe_confluence": cross,
            "shadow_render": render,
            "feedback_audit": audit,
        }
    )


def wave_hypothesis_packet(
    result: PriceStructureWaveFibV3Result,
    *,
    monthly_bars: Sequence[PriceBar],
    weekly_pivots: Sequence[PivotPoint],
) -> dict[str, object]:
    hypotheses = []
    for hypothesis in result.primary_monthly_hypotheses:
        hypotheses.append(
            {
                "hypothesis_id": hypothesis.hypothesis_id,
                "source_degree": hypothesis.source_degree,
                "status": hypothesis.status,
                "wave_state": hypothesis.wave_state,
                "endpoints": [
                    {
                        "label": point.label,
                        "pivot_ref": point.pivot_ref,
                        "date": point.date,
                        "status": point.status,
                    }
                    for point in hypothesis.endpoints
                ],
                "hard_rules": hypothesis.hard_rules,
                "score_components": {
                    key: str(value) for key, value in hypothesis.score_components.items()
                },
                "weekly_confirmation_refs": list(hypothesis.weekly_confirmation_refs),
            }
        )
    packet = {
        "contract": "price-only-ai-wave-hypothesis-packet-v1",
        "ticker": result.ticker,
        "market": result.market,
        "cutoff": result.as_of,
        "adjustment_basis": result.adjustment_basis,
        "selection_echo_required": [
            "ticker",
            "source_degree",
            "cutoff",
            "adjustment_basis",
            "endpoint_refs",
        ],
        "degree_candidate_counts": result.degree_candidate_counts,
        "hypotheses": hypotheses,
        "monthly_candle_context": [
            {
                "date": bar.date,
                "open": str(bar.open),
                "high": str(bar.high),
                "low": str(bar.low),
                "close": str(bar.close),
                "volume": str(bar.volume) if bar.volume is not None else None,
            }
            for bar in monthly_bars[-36:]
        ],
        "weekly_endpoint_confirmation": [
            {
                "pivot_ref": pivot.pivot_id,
                "date": pivot.bar_date,
                "kind": pivot.kind,
                "status": pivot.status,
            }
            for pivot in weekly_pivots[-24:]
        ],
        "prohibited": [
            "invent_endpoint",
            "calculate_fibonacci",
            "calculate_sr",
            "return_raw_price",
        ],
    }
    packet["evidence_sha256"] = _canonical_hash(packet)
    return packet
