from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from datetime import date
from statistics import median
from typing import Literal, Mapping, Sequence

from app.schemas.thesis import InvestorSupplyContext


ALGORITHM_VERSION = "ohlcv-structure-v1"
Timeframe = Literal["daily", "weekly", "monthly"]
PivotKind = Literal["low", "high"]
SwingKind = Literal["low", "high"]


@dataclass(frozen=True)
class StructureBar:
    index: int
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: float | None = None


@dataclass(frozen=True)
class LocalPivot:
    index: int
    date: str
    price: float
    kind: PivotKind
    timeframe: Timeframe
    prominence: float
    min_required: float
    atr: float
    volume: float | None
    validated: bool = True


@dataclass(frozen=True)
class MajorSwing:
    index: int
    date: str
    price: float
    kind: SwingKind
    timeframe: Timeframe
    threshold: float
    atr: float
    pct_threshold: float
    bars_since_previous: int
    confirmed_at: str


@dataclass(frozen=True)
class LocalPivotConfig:
    left: int
    right: int
    confirmation_horizon: int
    prominence_pct: float
    prominence_atr: float
    merge_pct: float
    padding_pct: float
    width_cap_pct: float
    box_width_pct: float
    box_lookback: int


@dataclass(frozen=True)
class MajorSwingConfig:
    pct_threshold: float
    atr_multiple: float
    min_leg_bars: int
    lookback: int


LOCAL_CONFIG: dict[Timeframe, LocalPivotConfig] = {
    "daily": LocalPivotConfig(5, 5, 10, 0.02, 1.0, 0.0175, 0.003, 0.05, 0.10, 20),
    "weekly": LocalPivotConfig(3, 3, 5, 0.03, 1.25, 0.0225, 0.005, 0.07, 0.125, 12),
    "monthly": LocalPivotConfig(2, 2, 3, 0.05, 1.5, 0.03, 0.0075, 0.10, 0.175, 6),
}

MAJOR_CONFIG: dict[Timeframe, MajorSwingConfig] = {
    "daily": MajorSwingConfig(0.08, 2.5, 10, 300),
    "weekly": MajorSwingConfig(0.12, 2.5, 4, 156),
    "monthly": MajorSwingConfig(0.18, 2.0, 2, 60),
}

_RECENCY = {
    "daily": ((20, 2), (60, 1)),
    "weekly": ((8, 2), (20, 1)),
    "monthly": ((3, 2), (6, 1)),
}


def _number(value: object) -> float | None:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        result = float(value)
        return result if math.isfinite(result) else None
    return None


def _round(value: float | None) -> float | None:
    return round(value, 6) if value is not None and math.isfinite(value) else None


def normalize_structure_bars(
    raw_bars: Sequence[Mapping[str, object]],
    *,
    lookback: int | None = None,
) -> list[StructureBar]:
    normalized: list[tuple[date, Mapping[str, object]]] = []
    for raw in raw_bars:
        if not isinstance(raw, Mapping):
            raise TypeError("OHLCV structure engines require raw bar mappings")
        raw_date = str(raw.get("date") or "")[:10]
        try:
            parsed_date = date.fromisoformat(raw_date)
        except ValueError:
            continue
        values = [_number(raw.get(key)) for key in ("open", "high", "low", "close")]
        if any(value is None or value <= 0 for value in values):
            continue
        open_price, high, low, close = (float(value) for value in values if value is not None)
        if high < low or high < max(open_price, close) or low > min(open_price, close):
            continue
        normalized.append((parsed_date, raw))
    normalized.sort(key=lambda item: item[0])
    if lookback is not None:
        normalized = normalized[-lookback:]
    return [
        StructureBar(
            index=index,
            date=parsed_date.isoformat(),
            open=float(raw["open"]),
            high=float(raw["high"]),
            low=float(raw["low"]),
            close=float(raw["close"]),
            volume=_number(raw.get("volume")),
        )
        for index, (parsed_date, raw) in enumerate(normalized)
    ]


def calc_wilder_atr(
    raw_bars: Sequence[Mapping[str, object]] | Sequence[StructureBar],
    period: int = 14,
) -> list[float | None]:
    if not raw_bars or period <= 0:
        return []
    bars = (
        list(raw_bars)
        if isinstance(raw_bars[0], StructureBar)
        else normalize_structure_bars(raw_bars)  # type: ignore[arg-type]
    )
    true_ranges: list[float] = []
    for index, bar in enumerate(bars):
        previous_close = bars[index - 1].close if index else bar.close
        true_ranges.append(
            max(
                bar.high - bar.low,
                abs(bar.high - previous_close),
                abs(bar.low - previous_close),
            )
        )
    values: list[float | None] = [None] * len(bars)
    if len(bars) < period:
        return values
    current = sum(true_ranges[:period]) / period
    values[period - 1] = current
    for index in range(period, len(bars)):
        current = (current * (period - 1) + true_ranges[index]) / period
        values[index] = current
    return values


def _tie_winner(
    bars: Sequence[StructureBar],
    indices: Sequence[int],
) -> int:
    max_volume = max((bars[index].volume or 0.0) for index in indices)
    volume_winners = [
        index for index in indices if (bars[index].volume or 0.0) == max_volume
    ]
    midpoint = (min(indices) + max(indices)) / 2
    return min(volume_winners, key=lambda index: (abs(index - midpoint), index))


def detect_local_pivots(
    raw_bars: Sequence[Mapping[str, object]],
    timeframe: Timeframe,
) -> list[LocalPivot]:
    config = LOCAL_CONFIG[timeframe]
    bars = normalize_structure_bars(raw_bars, lookback=300 if timeframe == "daily" else 120 if timeframe == "weekly" else 60)
    atr = calc_wilder_atr(bars)
    pivots: list[LocalPivot] = []
    for index in range(config.left, len(bars) - config.right):
        atr_value = atr[index]
        if atr_value is None:
            continue
        start = index - config.left
        stop = index + config.right + 1
        for kind in ("low", "high"):
            prices = [getattr(bar, kind) for bar in bars[start:stop]]
            candidate = min(prices) if kind == "low" else max(prices)
            price = getattr(bars[index], kind)
            if price != candidate:
                continue
            tied = [
                candidate_index
                for candidate_index in range(start, stop)
                if getattr(bars[candidate_index], kind) == candidate
            ]
            if index != _tie_winner(bars, tied):
                continue
            horizon = config.confirmation_horizon
            left_bars = bars[max(0, index - horizon):index]
            right_bars = bars[index + 1:min(len(bars), index + horizon + 1)]
            if not left_bars or not right_bars:
                continue
            if kind == "low":
                prominence = min(
                    max(bar.high for bar in left_bars) - price,
                    max(bar.high for bar in right_bars) - price,
                )
            else:
                prominence = min(
                    price - min(bar.low for bar in left_bars),
                    price - min(bar.low for bar in right_bars),
                )
            minimum = max(price * config.prominence_pct, atr_value * config.prominence_atr)
            if prominence + 1e-12 < minimum:
                continue
            pivots.append(
                LocalPivot(
                    index=index,
                    date=bars[index].date,
                    price=price,
                    kind=kind,  # type: ignore[arg-type]
                    timeframe=timeframe,
                    prominence=prominence,
                    min_required=minimum,
                    atr=atr_value,
                    volume=bars[index].volume,
                )
            )
    return sorted(pivots, key=lambda item: (item.index, item.kind))


def _split_wide_group(
    group: list[LocalPivot],
    timeframe: Timeframe,
) -> list[list[LocalPivot]]:
    config = LOCAL_CONFIG[timeframe]
    prices = [pivot.price for pivot in group]
    center = median(prices)
    atr_value = median([pivot.atr for pivot in group])
    padding = max(atr_value * 0.25, center * config.padding_pct)
    width = max(prices) + padding - (min(prices) - padding)
    if center <= 0 or width / center <= config.width_cap_pct or len(group) < 2:
        return [group]
    ordered = sorted(group, key=lambda item: (item.price, item.date))
    gaps = [ordered[index + 1].price - ordered[index].price for index in range(len(ordered) - 1)]
    split_at = max(range(len(gaps)), key=lambda index: (gaps[index], -index)) + 1
    return [
        *_split_wide_group(ordered[:split_at], timeframe),
        *_split_wide_group(ordered[split_at:], timeframe),
    ]


def _recency_score(timeframe: Timeframe, bars_ago: int) -> int:
    for maximum, score in _RECENCY[timeframe]:
        if bars_ago <= maximum:
            return score
    return 0


def build_price_zones(
    pivots: Sequence[LocalPivot],
    timeframe: Timeframe,
    *,
    bar_count: int,
) -> list[dict[str, object]]:
    config = LOCAL_CONFIG[timeframe]
    zones: list[dict[str, object]] = []
    for kind in ("low", "high"):
        ordered = sorted(
            (pivot for pivot in pivots if pivot.kind == kind),
            key=lambda item: (item.price, item.date),
        )
        groups: list[list[LocalPivot]] = []
        current: list[LocalPivot] = []
        for pivot in ordered:
            if not current:
                current = [pivot]
                continue
            center = median(item.price for item in current)
            atr_value = median([item.atr for item in [*current, pivot]])
            tolerance = max(center * config.merge_pct, atr_value * 0.5)
            if abs(pivot.price - center) <= tolerance:
                current.append(pivot)
            else:
                groups.extend(_split_wide_group(current, timeframe))
                current = [pivot]
        if current:
            groups.extend(_split_wide_group(current, timeframe))
        for group in groups:
            prices = [pivot.price for pivot in group]
            center = float(median(prices))
            atr_value = float(median([pivot.atr for pivot in group]))
            padding = max(atr_value * 0.25, center * config.padding_pct)
            latest_index = max(pivot.index for pivot in group)
            reaction_score = min(4, len(group))
            recency_score = _recency_score(timeframe, max(0, bar_count - 1 - latest_index))
            zones.append(
                {
                    "zone_low": _round(min(prices) - padding),
                    "zone_high": _round(max(prices) + padding),
                    "center": _round(center),
                    "pivot_type": kind,
                    "pivot_count": len(group),
                    "reaction_count": len(group),
                    "timeframe": timeframe,
                    "atr": _round(atr_value),
                    "padding": _round(padding),
                    "score": reaction_score + recency_score,
                    "reaction_score": reaction_score,
                    "recency_score": recency_score,
                    "higher_timeframe_score": 0,
                    "bollinger_overlap": False,
                    "fibonacci_overlap": False,
                    "strength": "Weak",
                    "pivot_dates": [pivot.date for pivot in group],
                    "pivot_prices": [_round(pivot.price) for pivot in group],
                    "latest_reaction_date": max(pivot.date for pivot in group),
                }
            )
    return zones


def _zones_overlap(first: Mapping[str, object], second: Mapping[str, object]) -> bool:
    first_center = float(first["center"])
    second_center = float(second["center"])
    first_atr = float(first.get("atr") or 0)
    tolerance = max(first_center * 0.01, first_atr * 0.5)
    return abs(first_center - second_center) <= tolerance


def score_price_zones(
    zones_by_timeframe: Mapping[str, Sequence[Mapping[str, object]]],
    *,
    bollinger_values: Sequence[float] = (),
    fibonacci_values: Sequence[float] = (),
) -> list[dict[str, object]]:
    scored: list[dict[str, object]] = []
    for timeframe in ("daily", "weekly", "monthly"):
        for original in zones_by_timeframe.get(timeframe, []):
            zone = dict(original)
            overlaps = 0
            for other_timeframe in ("daily", "weekly", "monthly"):
                if other_timeframe == timeframe:
                    continue
                if any(
                    _zones_overlap(zone, other)
                    for other in zones_by_timeframe.get(other_timeframe, [])
                ):
                    overlaps += 1
            higher_score = 3 if overlaps >= 2 else 2 if overlaps == 1 else 0
            center = float(zone["center"])
            atr_value = float(zone.get("atr") or 0)
            overlap_tolerance = max(center * 0.01, atr_value * 0.5)
            bollinger = any(
                float(zone["zone_low"]) <= value <= float(zone["zone_high"])
                or abs(value - center) <= overlap_tolerance
                for value in bollinger_values
            )
            fibonacci = any(
                float(zone["zone_low"]) <= value <= float(zone["zone_high"])
                or abs(value - center) <= overlap_tolerance
                for value in fibonacci_values
            )
            score = int(zone["reaction_score"]) + int(zone["recency_score"])
            score += higher_score + (2 if bollinger else 0) + (1 if fibonacci else 0)
            zone.update(
                {
                    "higher_timeframe_score": higher_score,
                    "bollinger_overlap": bollinger,
                    "fibonacci_overlap": fibonacci,
                    "score": min(12, score),
                    "strength": "Strong" if score >= 8 else "Medium" if score >= 5 else "Weak",
                }
            )
            scored.append(zone)
    return scored


def classify_price_zones(
    zones: Sequence[Mapping[str, object]],
    current_price: float,
) -> dict[str, list[dict[str, object]]]:
    result: dict[str, list[dict[str, object]]] = {
        "support": [],
        "resistance": [],
        "active": [],
    }
    low_zones = sorted(
        (
            zone
            for zone in zones
            if zone.get("pivot_type") == "low"
            and float(zone["zone_low"]) <= current_price
        ),
        key=lambda item: float(item["center"]),
        reverse=True,
    )
    support_ranks = {id(zone): index + 1 for index, zone in enumerate(low_zones)}
    for original in zones:
        zone = dict(original)
        low = float(zone["zone_low"])
        high = float(zone["zone_high"])
        if zone.get("pivot_type") == "low":
            zone["support_rank"] = support_ranks.get(id(original))
        if high < current_price:
            zone["distance_pct"] = _round((current_price - high) / current_price * 100)
            result["support"].append(zone)
        elif low > current_price:
            zone["distance_pct"] = _round((low - current_price) / current_price * 100)
            result["resistance"].append(zone)
        else:
            zone["distance_to_lower_pct"] = _round((current_price - low) / current_price * 100)
            zone["distance_to_upper_pct"] = _round((high - current_price) / current_price * 100)
            result["active"].append(zone)
    result["support"].sort(key=lambda item: current_price - float(item["zone_high"]))
    result["resistance"].sort(key=lambda item: float(item["zone_low"]) - current_price)
    result["active"].sort(key=lambda item: abs(float(item["center"]) - current_price))
    return result


def detect_boxes(
    raw_bars: Sequence[Mapping[str, object]],
    zones: Sequence[Mapping[str, object]],
    timeframe: Timeframe,
) -> list[dict[str, object]]:
    config = LOCAL_CONFIG[timeframe]
    bars = normalize_structure_bars(raw_bars, lookback=config.box_lookback)
    if len(bars) < config.box_lookback or len(zones) < 2:
        return []
    ordered = sorted(zones, key=lambda item: float(item["center"]))
    boxes: list[dict[str, object]] = []
    for lower_index, lower in enumerate(ordered[:-1]):
        for upper in ordered[lower_index + 1:]:
            if lower.get("pivot_type") != "low" or upper.get("pivot_type") != "high":
                continue
            box_low = float(lower["center"])
            box_high = float(upper["center"])
            center = (box_low + box_high) / 2
            if center <= 0 or (box_high - box_low) / center > config.box_width_pct:
                continue
            closes_inside = sum(box_low <= bar.close <= box_high for bar in bars)
            inside_ratio = closes_inside / len(bars)
            lower_tolerance = max(box_low * 0.005, float(lower.get("atr") or 0) * 0.25)
            upper_tolerance = max(box_high * 0.005, float(upper.get("atr") or 0) * 0.25)
            lower_touches = sum(abs(bar.low - box_low) <= lower_tolerance for bar in bars)
            upper_touches = sum(abs(bar.high - box_high) <= upper_tolerance for bar in bars)
            if inside_ratio < 0.60 or lower_touches < 2 or upper_touches < 2:
                continue
            boxes.append(
                {
                    "timeframe": timeframe,
                    "box_low": _round(box_low),
                    "box_high": _round(box_high),
                    "width_pct": _round((box_high - box_low) / center * 100),
                    "inside_close_ratio": _round(inside_ratio),
                    "lower_reactions": lower_touches,
                    "upper_reactions": upper_touches,
                    "confirmation_bars": len(bars),
                }
            )
    boxes.sort(key=lambda item: (-float(item["inside_close_ratio"]), float(item["width_pct"])))
    return boxes[:3]


def _major_threshold(
    price: float,
    atr_value: float,
    config: MajorSwingConfig,
) -> float:
    return max(price * config.pct_threshold, atr_value * config.atr_multiple)


def detect_major_swings(
    raw_bars: Sequence[Mapping[str, object]],
    timeframe: Timeframe,
) -> list[MajorSwing]:
    config = MAJOR_CONFIG[timeframe]
    bars = normalize_structure_bars(raw_bars, lookback=config.lookback)
    atr = calc_wilder_atr(bars)
    if len(bars) < 14 or atr[13] is None:
        return []
    start = 13
    min_index = max_index = start
    direction: Literal["up", "down"] | None = None
    candidate_index = start
    swings: list[MajorSwing] = []

    def add_swing(index: int, kind: SwingKind, confirmed_index: int) -> None:
        atr_value = atr[index]
        if atr_value is None:
            return
        price = bars[index].high if kind == "high" else bars[index].low
        bars_since_previous = (
            abs(index - swings[-1].index)
            if swings
            else abs(confirmed_index - index)
        )
        swings.append(
            MajorSwing(
                index=index,
                date=bars[index].date,
                price=price,
                kind=kind,
                timeframe=timeframe,
                threshold=_major_threshold(price, atr_value, config),
                atr=atr_value,
                pct_threshold=config.pct_threshold,
                bars_since_previous=bars_since_previous,
                confirmed_at=bars[confirmed_index].date,
            )
        )

    for index in range(start + 1, len(bars)):
        bar = bars[index]
        if direction is None:
            if bar.low < bars[min_index].low:
                min_index = index
            if bar.high > bars[max_index].high:
                max_index = index
            min_atr = atr[min_index]
            max_atr = atr[max_index]
            up_ready = (
                min_atr is not None
                and index - min_index >= config.min_leg_bars
                and bar.close - bars[min_index].low
                >= _major_threshold(bars[min_index].low, min_atr, config)
            )
            down_ready = (
                max_atr is not None
                and index - max_index >= config.min_leg_bars
                and bars[max_index].high - bar.close
                >= _major_threshold(bars[max_index].high, max_atr, config)
            )
            if up_ready and (not down_ready or min_index <= max_index):
                add_swing(min_index, "low", index)
                direction = "up"
                candidate_index = index
            elif down_ready:
                add_swing(max_index, "high", index)
                direction = "down"
                candidate_index = index
            continue
        if direction == "up":
            if bar.high > bars[candidate_index].high:
                candidate_index = index
            candidate_atr = atr[candidate_index]
            if (
                candidate_atr is not None
                and candidate_index - swings[-1].index >= config.min_leg_bars
                and bars[candidate_index].high - bar.close
                >= _major_threshold(bars[candidate_index].high, candidate_atr, config)
            ):
                add_swing(candidate_index, "high", index)
                direction = "down"
                candidate_index = index
        else:
            if bar.low < bars[candidate_index].low:
                candidate_index = index
            candidate_atr = atr[candidate_index]
            if (
                candidate_atr is not None
                and candidate_index - swings[-1].index >= config.min_leg_bars
                and bar.close - bars[candidate_index].low
                >= _major_threshold(bars[candidate_index].low, candidate_atr, config)
            ):
                add_swing(candidate_index, "low", index)
                direction = "up"
                candidate_index = index
    return swings


def _swing_dict(swing: MajorSwing) -> dict[str, object]:
    value = asdict(swing)
    value["price"] = _round(swing.price)
    value["threshold"] = _round(swing.threshold)
    value["atr"] = _round(swing.atr)
    return value


def select_major_anchors(
    major_swings: Sequence[MajorSwing],
    raw_bars: Sequence[Mapping[str, object]],
) -> dict[str, dict[str, object] | None]:
    if not major_swings:
        return {
            "major_base_low": None,
            "breakout_start": None,
            "first_higher_low": None,
            "dominant_major_high": None,
            "recent_major_high": None,
        }
    bars = normalize_structure_bars(raw_bars)
    base_candidates: list[MajorSwing] = []
    for candidate in (swing for swing in major_swings if swing.kind == "low"):
        previous_highs = [
            swing for swing in major_swings if swing.kind == "high" and swing.index < candidate.index
        ]
        later_highs = [
            swing for swing in major_swings if swing.kind == "high" and swing.index > candidate.index
        ]
        if not previous_highs or not later_highs:
            continue
        dominant = max(later_highs, key=lambda item: item.price)
        rise = dominant.price - candidate.price
        broke_previous = any(
            bar.index > candidate.index and bar.close > previous_highs[-1].price for bar in bars
        )
        if rise >= max(candidate.price * 0.20, candidate.atr * 4) and broke_previous:
            base_candidates.append(candidate)
    major_base = (
        min(base_candidates, key=lambda item: (item.price, item.index))
        if base_candidates
        else None
    )

    breakout_start: MajorSwing | None = None
    for index in range(20, len(bars)):
        if bars[index].close <= max(bar.close for bar in bars[index - 20:index]):
            continue
        preceding_lows = [
            swing for swing in major_swings if swing.kind == "low" and swing.index < index
        ]
        if preceding_lows:
            breakout_start = preceding_lows[-1]

    first_higher_low: MajorSwing | None = None
    if major_base is not None:
        previous_high: MajorSwing | None = None
        for swing in major_swings:
            if swing.index <= major_base.index:
                continue
            if swing.kind == "high":
                previous_high = swing
                continue
            if swing.price <= major_base.price * 1.05 or previous_high is None:
                continue
            later_break = any(
                later.kind == "high"
                and later.index > swing.index
                and later.price > previous_high.price
                for later in major_swings
            )
            if later_break:
                first_higher_low = swing
                break

    anchor_start = major_base or breakout_start
    later_highs = [
        swing
        for swing in major_swings
        if swing.kind == "high" and (anchor_start is None or swing.index > anchor_start.index)
    ]
    dominant_high = max(later_highs, key=lambda item: item.price) if later_highs else None
    recent_high = later_highs[-1] if later_highs else None

    def anchor_value(
        swing: MajorSwing | None,
        anchor_type: str,
        confidence: str,
    ) -> dict[str, object] | None:
        if swing is None:
            return None
        return {
            "anchor_type": anchor_type,
            "price": _round(swing.price),
            "date": swing.date,
            "timeframe": swing.timeframe,
            "confidence": confidence,
            "source": "major_swing_engine",
        }

    return {
        "major_base_low": anchor_value(major_base, "major_base_low", "high"),
        "breakout_start": anchor_value(breakout_start, "breakout_start", "medium"),
        "first_higher_low": anchor_value(first_higher_low, "first_higher_low", "high"),
        "dominant_major_high": anchor_value(dominant_high, "dominant_major_high", "high"),
        "recent_major_high": anchor_value(recent_high, "recent_major_high", "high"),
    }


def build_tentative_elliott_count(
    major_swings: Sequence[MajorSwing],
    anchors: Mapping[str, Mapping[str, object] | None],
) -> dict[str, object]:
    base = anchors.get("major_base_low") or anchors.get("breakout_start")
    if base is None:
        return {"available": False, "tentative_count": True, "reason": "major_anchor_unavailable"}
    start_date = str(base["date"])
    start_index = next(
        (index for index, swing in enumerate(major_swings) if swing.date == start_date and swing.kind == "low"),
        None,
    )
    if start_index is None:
        return {"available": False, "tentative_count": True, "reason": "anchor_not_in_major_swings"}
    sequence = list(major_swings[start_index:start_index + 6])
    expected = ["low", "high", "low", "high", "low", "high"]
    if len(sequence) < 4 or [swing.kind for swing in sequence] != expected[:len(sequence)]:
        return {"available": False, "tentative_count": True, "reason": "insufficient_major_sequence"}
    if sequence[2].price <= sequence[0].price:
        return {"available": False, "tentative_count": True, "reason": "wave2_broke_wave1_start"}
    if sequence[3].price <= sequence[1].price:
        return {"available": False, "tentative_count": True, "reason": "wave3_not_higher_high"}
    overlap = len(sequence) >= 5 and sequence[4].price <= sequence[1].price
    confidence = "low" if overlap or len(sequence) < 6 else "medium"
    return {
        "available": True,
        "tentative_count": True,
        "confidence": confidence,
        "possible_diagonal": overlap,
        "usable_in_core": confidence != "low",
        "points": [
            {
                "wave": label,
                "date": swing.date,
                "price": _round(swing.price),
                "kind": swing.kind,
                "timeframe": swing.timeframe,
                "source": "major_swing_engine",
            }
            for label, swing in zip(("start", "wave1", "wave2", "wave3", "wave4", "wave5"), sequence)
        ],
        "blocking_unknowns": ["historical_volume_confirmation_unavailable"],
    }


def _fibonacci_set(
    anchor_type: str,
    low: Mapping[str, object] | None,
    high: Mapping[str, object] | None,
) -> dict[str, object] | None:
    if low is None or high is None:
        return None
    low_price = float(low["price"])
    high_price = float(high["price"])
    if high_price <= low_price or str(high["date"]) <= str(low["date"]):
        return None
    price_range = high_price - low_price
    confidence_rank = {"low": 0, "medium": 1, "high": 2}
    low_confidence = str(low["confidence"])
    high_confidence = str(high["confidence"])
    confidence = min(
        (low_confidence, high_confidence),
        key=lambda value: confidence_rank.get(value, -1),
    )
    return {
        "anchor_type": anchor_type,
        "low_price": _round(low_price),
        "low_date": low["date"],
        "high_price": _round(high_price),
        "high_date": high["date"],
        "timeframe": low["timeframe"],
        "confidence": confidence,
        "source": "major_swing_engine",
        "retracements": {
            str(ratio): _round(high_price - ratio * price_range)
            for ratio in (0.382, 0.5, 0.618)
        },
        "extensions": {
            str(ratio): _round(low_price + ratio * price_range)
            for ratio in (0.618, 1.0, 1.618, 2.618)
        },
    }


def calculate_fibonacci_sets(
    anchors: Mapping[str, Mapping[str, object] | None],
) -> dict[str, dict[str, object]]:
    values: dict[str, dict[str, object]] = {}
    candidates = (
        ("long_term", "major_base_low", "dominant_major_high"),
        ("medium_term", "first_higher_low", "recent_major_high"),
        ("breakout", "breakout_start", "recent_major_high"),
    )
    for name, low_key, high_key in candidates:
        result = _fibonacci_set(name, anchors.get(low_key), anchors.get(high_key))
        if result is not None:
            values[name] = result
    return values


def classify_supply_context(
    supply: InvestorSupplyContext | Mapping[str, object] | None,
) -> dict[str, object]:
    if supply is None:
        return {"classification": "unavailable", "horizon": None, "confidence": "low"}
    values = supply.model_dump() if isinstance(supply, InvestorSupplyContext) else dict(supply)
    if not values.get("available"):
        return {"classification": "unavailable", "horizon": None, "confidence": "low"}
    horizon: str | None = None
    foreign: float | None = None
    institution: float | None = None
    individual: float | None = None
    for suffix, label in (("_20", "20d"), ("_5", "5d"), ("", "1d")):
        candidate_foreign = _number(values.get(f"foreign_net_buy_qty{suffix}"))
        candidate_institution = _number(values.get(f"institution_net_buy_qty{suffix}"))
        if candidate_foreign is None or candidate_institution is None:
            continue
        horizon = label
        foreign = candidate_foreign
        institution = candidate_institution
        individual = _number(values.get(f"individual_net_buy_qty{suffix}"))
        break
    if horizon is None or foreign is None or institution is None:
        return {"classification": "unavailable", "horizon": None, "confidence": "low"}
    if foreign < 0 and institution < 0:
        classification = "distribution"
    elif foreign > 0 and institution > 0:
        classification = "strong_joint"
    elif foreign > 0:
        classification = "foreign_led"
    elif institution > 0:
        classification = "institution_led"
    elif individual is not None and individual > 0:
        classification = "retail_led"
    else:
        classification = "mixed"
    return {
        "classification": classification,
        "horizon": horizon,
        "confidence": "high" if horizon == "20d" else "medium",
        "foreign": foreign,
        "institution": institution,
        "individual": individual,
    }


def calculate_invalidation(
    support: Mapping[str, object] | None,
    *,
    current_price: float,
    daily_atr: float | None,
    weekly_atr: float | None,
    daily_bars: Sequence[StructureBar],
    weekly_bars: Sequence[StructureBar],
    volume_ratio: float | None,
    supply_classification: str,
    scenario: str = "support_entry",
) -> dict[str, object]:
    if support is None:
        return {"available": False, "reason": "support_unavailable"}
    timeframe = str(support.get("timeframe") or "daily")
    atr_value = weekly_atr if timeframe == "weekly" else daily_atr
    if atr_value is None:
        return {"available": False, "reason": "atr_unavailable"}
    entry = (
        (float(support["zone_low"]) + float(support["zone_high"])) / 2
        if scenario == "support_entry"
        else current_price
    )
    pct_buffer = 0.015 if timeframe == "weekly" else 0.01
    buffer = max(atr_value * 0.5, entry * pct_buffer)
    invalidation = float(support["zone_low"]) - buffer
    daily_closes = [bar.close for bar in daily_bars[-2:]]
    hard_daily = len(daily_closes) == 2 and all(close < invalidation for close in daily_closes)
    hard_weekly = bool(weekly_bars and weekly_bars[-1].close < invalidation)
    accelerated = bool(
        daily_bars
        and daily_bars[-1].close < invalidation
        and volume_ratio is not None
        and volume_ratio >= 1.2
        and supply_classification == "distribution"
    )
    wick_only = bool(
        daily_bars
        and daily_bars[-1].low < invalidation <= daily_bars[-1].close
        and (volume_ratio is None or volume_ratio < 1.2)
    )
    status = (
        "accelerated_invalid"
        if accelerated
        else "hard_invalid"
        if hard_daily or hard_weekly
        else "wick_only_review"
        if wick_only
        else "intact"
    )
    return {
        "available": True,
        "scenario": scenario,
        "timeframe": timeframe,
        "entry": _round(entry),
        "support_low": support["zone_low"],
        "buffer": _round(buffer),
        "price": _round(invalidation),
        "status": status,
        "hard_daily": hard_daily,
        "hard_weekly": hard_weekly,
        "accelerated": accelerated,
        "wick_only": wick_only,
        "chart_only": True,
    }


def calculate_risk_reward(
    *,
    current_price: float,
    resistance: Mapping[str, object] | None,
    invalidation: Mapping[str, object],
    support: Mapping[str, object] | None = None,
) -> dict[str, object]:
    if resistance is None or invalidation.get("available") is not True:
        return {"available": False, "reason": "resistance_or_invalidation_unavailable"}
    target = float(resistance["zone_low"])
    invalidation_price = float(invalidation["price"])

    def scenario(entry: float, label: str) -> dict[str, object] | None:
        upside = target - entry
        downside = entry - invalidation_price
        if upside <= 0 or downside <= 0:
            return None
        ratio = upside / downside
        return {
            "scenario": label,
            "entry": _round(entry),
            "target": _round(target),
            "target_basis": "nearest_strong_or_medium_resistance_lower_bound",
            "invalidation": _round(invalidation_price),
            "upside": _round(upside),
            "downside": _round(downside),
            "ratio": _round(ratio),
            "classification": "attractive" if ratio >= 2 else "conditional" if ratio >= 1 else "poor_chase",
        }

    current = scenario(current_price, "current_price")
    support_entry = None
    if support is not None:
        midpoint = (float(support["zone_low"]) + float(support["zone_high"])) / 2
        support_entry = scenario(midpoint, "support_midpoint_not_order_price")
    if current is None and support_entry is None:
        return {"available": False, "reason": "non_positive_upside_or_downside"}
    return {
        "available": True,
        "current_price": current,
        "support_entry": support_entry,
        "nearest_target_enforced": True,
    }


def determine_chart_state(
    *,
    current_price: float,
    classified_zones: Mapping[str, Sequence[Mapping[str, object]]],
    all_zones: Sequence[Mapping[str, object]],
    invalidation: Mapping[str, object],
    risk_reward: Mapping[str, object],
    daily_bars: Sequence[StructureBar],
    volume_ratio: float | None,
    upper_wick_pct: float | None,
    close_location_pct: float | None,
    supply: Mapping[str, object],
    bollinger_values: Mapping[str, float],
    fibonacci_sets: Mapping[str, Mapping[str, object]],
    major_swing_count: int,
) -> dict[str, object]:
    supply_classification = str(supply.get("classification") or "unavailable")
    blockers: list[str] = []
    if supply_classification == "unavailable":
        blockers.append("verified_supply_unavailable")
    invalid_status = str(invalidation.get("status") or "unavailable")
    if invalid_status in {"hard_invalid", "accelerated_invalid"}:
        return {
            "state": "INVALID",
            "confidence": "high",
            "reasons": [invalid_status],
            "blocking_unknowns": blockers,
            "user_semantics": "price_scenario_reassessment",
        }

    extension_levels = [
        float(value)
        for fib in fibonacci_sets.values()
        for key, value in dict(fib.get("extensions") or {}).items()
        if key in {"1.618", "2.618"}
    ]
    long_resistance = [
        float(zone["zone_low"])
        for zone in classified_zones.get("resistance", [])
        if zone.get("strength") == "Strong" and zone.get("timeframe") in {"weekly", "monthly"}
    ]
    trim_levels = [
        *long_resistance,
        *(value for key, value in bollinger_values.items() if key in {"24_month", "54_month"}),
        *extension_levels,
    ]
    near_trim_level = any(
        level > 0 and abs(current_price - level) / current_price <= 0.02 for level in trim_levels
    )
    trim_signals = sum(
        (
            volume_ratio is not None and volume_ratio >= 1.5,
            upper_wick_pct is not None and upper_wick_pct >= 35,
            close_location_pct is not None and close_location_pct <= 55,
            supply_classification == "distribution",
        )
    )
    if near_trim_level and trim_signals >= 2:
        return {
            "state": "TRIM",
            "confidence": "medium" if blockers else "high",
            "reasons": ["near_long_term_reference", f"exhaustion_signals:{trim_signals}"],
            "blocking_unknowns": blockers,
            "user_semantics": "holder_position_management",
        }

    crossed = [
        zone
        for zone in all_zones
        if zone.get("pivot_type") == "high"
        and zone.get("strength") in {"Strong", "Medium"}
        and float(zone["zone_high"]) < current_price
        and len(daily_bars) >= 2
        and daily_bars[-1].close > float(zone["zone_high"])
        and daily_bars[-2].close > float(zone["zone_high"])
    ]
    crossed.sort(key=lambda zone: current_price - float(zone["zone_high"]))
    if crossed and volume_ratio is not None and volume_ratio >= 1.2:
        confidence = (
            "high"
            if supply_classification == "strong_joint"
            else "medium"
            if supply_classification in {"foreign_led", "institution_led"}
            else "low"
        )
        if supply_classification == "unavailable":
            blockers.append("supply_dependent_confirmation_limited")
        blockers.append("trading_value_ratio_unavailable")
        return {
            "state": "CONFIRM_ENTRY",
            "confidence": confidence,
            "reasons": ["two_close_breakout", "volume_ratio_confirmed"],
            "blocking_unknowns": list(dict.fromkeys(blockers)),
            "breakout_zone": dict(crossed[0]),
            "user_semantics": "confirmed_breakout_not_buy_command",
        }

    active_supports = [
        zone
        for zone in classified_zones.get("active", [])
        if zone.get("pivot_type") == "low" and zone.get("strength") in {"Strong", "Medium"}
    ]
    scenario_rr = risk_reward.get("support_entry")
    ratio = float(scenario_rr.get("ratio")) if isinstance(scenario_rr, dict) else None
    acceptable_volume = volume_ratio is not None and 0.8 <= volume_ratio <= 1.1
    not_distribution = supply_classification != "distribution"
    if active_supports and acceptable_volume and not_distribution and ratio is not None:
        rank = int(active_supports[0].get("support_rank") or 1)
        if rank >= 2 and ratio >= 2:
            return {
                "state": "SECOND_SUPPORT_ENTRY",
                "confidence": "medium" if blockers else "high",
                "reasons": ["inside_second_support", "quiet_volume", "rr_at_least_2"],
                "blocking_unknowns": blockers,
                "user_semantics": "second_support_scenario_not_order",
            }
        if ratio >= 1.5:
            return {
                "state": "SUPPORT_ENTRY",
                "confidence": "medium" if blockers or ratio < 2 else "high",
                "reasons": ["inside_primary_support", "quiet_volume", "rr_at_least_1_5"],
                "blocking_unknowns": blockers,
                "user_semantics": "support_scenario_not_order",
            }

    nearest_resistance = next(
        (
            zone
            for zone in classified_zones.get("resistance", [])
            if zone.get("strength") in {"Strong", "Medium"}
        ),
        None,
    )
    current_rr = risk_reward.get("current_price")
    current_ratio = float(current_rr.get("ratio")) if isinstance(current_rr, dict) else None
    wait_reasons: list[str] = []
    if current_ratio is not None and current_ratio < 1.5:
        wait_reasons.append("rr_below_1_5")
    if nearest_resistance is not None and float(nearest_resistance["distance_pct"]) <= 2:
        wait_reasons.append("strong_or_medium_resistance_within_2pct")
    if supply_classification == "distribution":
        wait_reasons.append("distribution")
    if wait_reasons:
        return {
            "state": "WAIT",
            "confidence": "medium",
            "reasons": wait_reasons,
            "blocking_unknowns": blockers,
            "user_semantics": "price_structure_wait_not_sell_command",
        }

    support_exists = any(
        zone.get("strength") in {"Strong", "Medium"}
        for zone in [
            *classified_zones.get("support", []),
            *classified_zones.get("active", []),
        ]
    )
    if major_swing_count >= 3 and support_exists and invalid_status == "intact":
        return {
            "state": "HOLD",
            "confidence": "medium" if blockers else "high",
            "reasons": ["major_structure_and_support_intact"],
            "blocking_unknowns": blockers,
            "user_semantics": "holder_structure_not_new_entry",
        }
    return {
        "state": "WAIT",
        "confidence": "low" if blockers else "medium",
        "reasons": ["support_or_breakout_setup_absent"],
        "blocking_unknowns": blockers,
        "user_semantics": "insufficient_setup",
    }


def analyze_chart_structure(
    raw_by_timeframe: Mapping[str, Sequence[Mapping[str, object]]],
    *,
    timeframe_contexts: Mapping[str, Mapping[str, object]] | None = None,
    investor_supply: InvestorSupplyContext | Mapping[str, object] | None = None,
    price_basis: str = "adjusted_close",
) -> dict[str, object]:
    timeframe_contexts = timeframe_contexts or {}
    bars_by_timeframe = {
        timeframe: normalize_structure_bars(
            raw_by_timeframe.get(timeframe, []),
            lookback=300 if timeframe == "daily" else 156 if timeframe == "weekly" else 60,
        )
        for timeframe in ("daily", "weekly", "monthly")
    }
    atr_series = {
        timeframe: calc_wilder_atr(bars)
        for timeframe, bars in bars_by_timeframe.items()
    }
    atr_output = {
        timeframe: {
            "available": bool(values and values[-1] is not None),
            "period": 14,
            "method": "wilder_recursive",
            "value": _round(values[-1]) if values else None,
            "source": "deterministic_engine",
        }
        for timeframe, values in atr_series.items()
    }
    local_pivots = {
        timeframe: detect_local_pivots(raw_by_timeframe.get(timeframe, []), timeframe)  # type: ignore[arg-type]
        for timeframe in ("daily", "weekly", "monthly")
    }
    raw_zones = {
        timeframe: build_price_zones(
            local_pivots[timeframe],  # type: ignore[index]
            timeframe,  # type: ignore[arg-type]
            bar_count=len(bars_by_timeframe[timeframe]),
        )
        for timeframe in ("daily", "weekly", "monthly")
    }
    major_swings_by_timeframe = {
        timeframe: detect_major_swings(raw_by_timeframe.get(timeframe, []), timeframe)  # type: ignore[arg-type]
        for timeframe in ("daily", "weekly", "monthly")
    }
    primary_timeframe: Timeframe = (
        "weekly" if len(bars_by_timeframe["weekly"]) >= 60 else "daily"
    )
    primary_swings = major_swings_by_timeframe[primary_timeframe]
    anchors = select_major_anchors(
        primary_swings,
        raw_by_timeframe.get(primary_timeframe, []),
    )
    elliott = build_tentative_elliott_count(primary_swings, anchors)
    fibonacci = calculate_fibonacci_sets(anchors)
    fib_retracements = [
        float(value)
        for item in fibonacci.values()
        for key, value in dict(item.get("retracements") or {}).items()
        if key in {"0.382", "0.5", "0.618"}
    ]
    daily_context = dict(timeframe_contexts.get("daily") or {})
    bollinger_values = {
        key: float(value)
        for key, value in dict(daily_context.get("bollinger_upper") or {}).items()
        if _number(value) is not None
    }
    all_zones = score_price_zones(
        raw_zones,
        bollinger_values=list(bollinger_values.values()),
        fibonacci_values=fib_retracements,
    )
    daily_bars = bars_by_timeframe["daily"]
    current_price = daily_bars[-1].close if daily_bars else None
    classified = (
        classify_price_zones(all_zones, current_price)
        if current_price is not None
        else {"support": [], "resistance": [], "active": []}
    )
    boxes = {
        timeframe: detect_boxes(
            raw_by_timeframe.get(timeframe, []),
            raw_zones[timeframe],
            timeframe,  # type: ignore[arg-type]
        )
        for timeframe in ("daily", "weekly", "monthly")
    }
    eligible_supports = [
        zone
        for zone in [*classified["active"], *classified["support"]]
        if zone.get("strength") in {"Strong", "Medium"}
    ]
    eligible_resistances = [
        zone
        for zone in classified["resistance"]
        if zone.get("strength") in {"Strong", "Medium"}
    ]
    support = eligible_supports[0] if eligible_supports else None
    resistance = eligible_resistances[0] if eligible_resistances else None
    supply = classify_supply_context(investor_supply)
    volume_ratio = _number(daily_context.get("volume_ratio_20"))
    daily_candle = dict(daily_context.get("candle") or {})
    invalidation = (
        calculate_invalidation(
            support,
            current_price=current_price,
            daily_atr=_number(atr_output["daily"].get("value")),
            weekly_atr=_number(atr_output["weekly"].get("value")),
            daily_bars=daily_bars,
            weekly_bars=bars_by_timeframe["weekly"],
            volume_ratio=volume_ratio,
            supply_classification=str(supply["classification"]),
        )
        if current_price is not None
        else {"available": False, "reason": "current_price_unavailable"}
    )
    risk_reward = (
        calculate_risk_reward(
            current_price=current_price,
            resistance=resistance,
            invalidation=invalidation,
            support=support,
        )
        if current_price is not None
        else {"available": False, "reason": "current_price_unavailable"}
    )
    chart_state = (
        determine_chart_state(
            current_price=current_price,
            classified_zones=classified,
            all_zones=all_zones,
            invalidation=invalidation,
            risk_reward=risk_reward,
            daily_bars=daily_bars,
            volume_ratio=volume_ratio,
            upper_wick_pct=_number(daily_candle.get("upper_wick_pct")),
            close_location_pct=_number(daily_candle.get("close_location_pct")),
            supply=supply,
            bollinger_values=bollinger_values,
            fibonacci_sets=fibonacci,
            major_swing_count=len(primary_swings),
        )
        if current_price is not None
        else {
            "state": "WAIT",
            "confidence": "low",
            "reasons": ["current_price_unavailable"],
            "blocking_unknowns": [],
        }
    )
    as_of_date = daily_bars[-1].date if daily_bars else None
    unavailable: list[str] = []
    availability = {
        "atr": any(item["available"] for item in atr_output.values()),
        "local_pivots": any(local_pivots.values()),
        "support_resistance": bool(all_zones),
        "box_ranges": any(boxes.values()),
        "major_swings": bool(primary_swings),
        "elliott_wave": bool(elliott.get("available")),
        "fibonacci": bool(fibonacci),
        "risk_reward": bool(risk_reward.get("available")),
        "invalidation": bool(invalidation.get("available")),
        "chart_state_machine": current_price is not None,
    }
    unavailable.extend(key for key, value in availability.items() if not value)
    return {
        "algorithm_version": ALGORITHM_VERSION,
        "source": "thesis_monitor_deterministic_ohlcv_structure",
        "as_of_date": as_of_date,
        "price_basis": price_basis,
        "availability": availability,
        "unavailable_fields": unavailable,
        "atr": atr_output,
        "local_pivots": {
            timeframe: [asdict(pivot) for pivot in pivots]
            for timeframe, pivots in local_pivots.items()
        },
        "zones": classified,
        "all_zones": all_zones,
        "boxes": boxes,
        "major_swings": {
            "primary_timeframe": primary_timeframe,
            "fallback_used": primary_timeframe == "daily",
            "points": [_swing_dict(swing) for swing in primary_swings],
            "by_timeframe": {
                timeframe: [_swing_dict(swing) for swing in swings]
                for timeframe, swings in major_swings_by_timeframe.items()
            },
        },
        "major_anchors": anchors,
        "elliott": elliott,
        "fibonacci": fibonacci,
        "invalidation": invalidation,
        "risk_reward": risk_reward,
        "supply_classification": supply,
        "chart_state": chart_state,
    }
