#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Universal OHLCV Structure / Elliott / Fibonacci / Zone Engine

Purpose
-------
- Detect confirmed/provisional pivots from OHLCV
- Build support/resistance zones and balance boxes
- Search Elliott impulse hypotheses using hard rules + soft scoring
- Support automatic long-cycle anchor selection or user override
- Produce Fibonacci retracement/extension levels and wave-5 projection clusters
- Use optional Bollinger / volume / MACD / investor-flow columns when available
- Return JSON suitable for downstream Codex/report/chart logic

Required columns
----------------
date, open, high, low, close, volume

Optional columns
----------------
value
VOLUME_RATIO_20, RSI14, MACD, MACD_SIGNAL, MACD_HIST
BB_36_1.541_UPPER, BB_60_1.541_UPPER, BB_50_2.25_UPPER,
BB_144_1.541_UPPER, BB_288_1.541_UPPER, BB_300_3.33_UPPER
supply_* columns

Design principle
----------------
Pivot creates endpoint candidates.
Elliott hard rules reject invalid sequences.
Fibonacci / Bollinger / volume / lower-timeframe confirmation add confidence.
Never force a 1-2-3-4-5 count when the data only supports a partial impulse.
"""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

TF_CONFIG: Dict[str, Dict[str, float]] = {
    "daily": {
        "zone_lookback": 300,
        "pivot_left": 3,
        "pivot_right": 3,
        "group_pct": 0.0175,
        "zone_width_cap": 0.06,
        "box_width_cap": 0.12,
        "confluence_pct": 0.015,
        "box_recent_bars": 10,
        "box_close_inside_min": 0.40,
        "box_overlap_min": 0.60,
    },
    "weekly": {
        "zone_lookback": 60,
        "pivot_left": 2,
        "pivot_right": 2,
        "group_pct": 0.0225,
        "zone_width_cap": 0.08,
        "box_width_cap": 0.15,
        "confluence_pct": 0.020,
        "box_recent_bars": 6,
        "box_close_inside_min": 0.40,
        "box_overlap_min": 0.60,
    },
    "monthly": {
        "zone_lookback": 60,
        "pivot_left": 2,
        "pivot_right": 2,
        "group_pct": 0.0300,
        "zone_width_cap": 0.12,
        "box_width_cap": 0.20,
        "confluence_pct": 0.025,
        "box_recent_bars": 6,
        "box_close_inside_min": 0.40,
        "box_overlap_min": 0.50,
    },
}

BB_UPPER_COLS = {
    "3m": "BB_36_1.541_UPPER",
    "5m": "BB_60_1.541_UPPER",
    "6m": "BB_50_2.25_UPPER",
    "12m": "BB_144_1.541_UPPER",
    "24m": "BB_288_1.541_UPPER",
    "54m": "BB_300_3.33_UPPER",
}

FIB_RETRACE_LEVELS = (0.236, 0.382, 0.500, 0.618, 0.786)
WAVE3_REFERENCE_EXTENSIONS = (1.000, 1.618, 2.000, 2.618, 4.236)
WAVE5_W1_MULTIPLES = (0.618, 1.000, 1.618, 2.618)


@dataclass
class Pivot:
    idx: int
    date: str
    kind: str  # "low" or "high"
    price: float
    confirmed: bool
    atr14: float
    source_tf: str


@dataclass
class Zone:
    low: float
    high: float
    center: float
    role: str
    score: float
    sources: List[Dict[str, Any]] = field(default_factory=list)
    reaction_count: int = 0
    width_pct: float = 0.0


@dataclass
class Box:
    low: float
    high: float
    center: float
    width_pct: float
    close_inside_ratio: float
    range_overlap_ratio: float
    touched_lower: bool
    touched_upper: bool
    score: float
    label: str = "BALANCE_BOX"


# ---------------------------------------------------------------------------
# IO / preprocessing
# ---------------------------------------------------------------------------

def _safe_float(x: Any) -> Optional[float]:
    try:
        if pd.isna(x):
            return None
        return float(x)
    except Exception:
        return None


def load_ohlcv(path: str | Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    required = {"date", "open", "high", "low", "close", "volume"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"{path}: required columns missing: {sorted(missing)}")

    df = df.copy()
    df["date"] = pd.to_datetime(df["date"], errors="raise")
    for c in ("open", "high", "low", "close", "volume"):
        df[c] = pd.to_numeric(df[c], errors="coerce")
    if "value" in df.columns:
        df["value"] = pd.to_numeric(df["value"], errors="coerce")

    df = df.dropna(subset=["date", "open", "high", "low", "close"])
    df = df.sort_values("date").drop_duplicates("date", keep="last").reset_index(drop=True)
    df["ATR14"] = calculate_atr(df, 14)
    return df


def calculate_atr(df: pd.DataFrame, n: int = 14) -> pd.Series:
    prev_close = df["close"].shift(1)
    tr = pd.concat(
        [
            (df["high"] - df["low"]).abs(),
            (df["high"] - prev_close).abs(),
            (df["low"] - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    return tr.rolling(n, min_periods=1).mean()


# ---------------------------------------------------------------------------
# Pivot detection
# ---------------------------------------------------------------------------

def detect_pivots(
    df: pd.DataFrame,
    timeframe: str,
    left: Optional[int] = None,
    right: Optional[int] = None,
    lookback: Optional[int] = None,
    assume_last_incomplete: bool = True,
) -> List[Pivot]:
    """
    Confirmed pivot:
      low[i] < all left lows and <= all required right lows
      high[i] > all left highs and >= all required right highs

    Tail points can be emitted as provisional pivots when there are fewer than
    `right` completed bars to the right. This is critical for current wave-3/4
    candidates near the end of the dataset.
    """
    tf = TF_CONFIG[timeframe]
    left = int(left if left is not None else tf["pivot_left"])
    right = int(right if right is not None else tf["pivot_right"])

    start = 0
    if lookback is not None and len(df) > lookback:
        start = len(df) - int(lookback)

    completed_end = len(df) - 2 if assume_last_incomplete else len(df) - 1
    pivots: List[Pivot] = []

    for i in range(max(left, start), len(df)):
        left_lows = df.loc[i - left : i - 1, "low"]
        left_highs = df.loc[i - left : i - 1, "high"]
        if len(left_lows) < left:
            continue

        available_right = min(right, len(df) - 1 - i)
        if available_right > 0:
            right_lows = df.loc[i + 1 : i + available_right, "low"]
            right_highs = df.loc[i + 1 : i + available_right, "high"]
            right_low = float(right_lows.min())
            right_high = float(right_highs.max())
        else:
            right_low = float("inf")
            right_high = -float("inf")

        completed_right = max(0, min(right, completed_end - i))
        confirmed = completed_right >= right

        low_i = float(df.at[i, "low"])
        high_i = float(df.at[i, "high"])

        is_low = low_i < float(left_lows.min()) and low_i <= right_low
        is_high = high_i > float(left_highs.max()) and high_i >= right_high

        if is_low:
            pivots.append(
                Pivot(
                    idx=i,
                    date=df.at[i, "date"].strftime("%Y-%m-%d"),
                    kind="low",
                    price=low_i,
                    confirmed=confirmed,
                    atr14=float(df.at[i, "ATR14"]),
                    source_tf=timeframe,
                )
            )
        if is_high:
            pivots.append(
                Pivot(
                    idx=i,
                    date=df.at[i, "date"].strftime("%Y-%m-%d"),
                    kind="high",
                    price=high_i,
                    confirmed=confirmed,
                    atr14=float(df.at[i, "ATR14"]),
                    source_tf=timeframe,
                )
            )

    return sorted(pivots, key=lambda p: (p.idx, 0 if p.kind == "low" else 1))


# ---------------------------------------------------------------------------
# Generic scoring helpers
# ---------------------------------------------------------------------------

def band_score(
    x: float,
    ideal_lo: float,
    ideal_hi: float,
    allowed_lo: float,
    allowed_hi: float,
    max_score: float = 2.0,
) -> float:
    if x < allowed_lo or x > allowed_hi:
        return -999.0
    if ideal_lo <= x <= ideal_hi:
        return max_score
    if x < ideal_lo:
        return max_score * (x - allowed_lo) / max(ideal_lo - allowed_lo, 1e-12)
    return max_score * (allowed_hi - x) / max(allowed_hi - ideal_hi, 1e-12)


def nearest_fib_distance(value: float, levels: Sequence[float]) -> Tuple[float, float]:
    level = min(levels, key=lambda z: abs(z - value))
    return float(level), abs(value - level)


def normalized_price_distance(a: float, b: float) -> float:
    return abs(a - b) / max((abs(a) + abs(b)) / 2.0, 1e-12)


# ---------------------------------------------------------------------------
# Elliott impulse search
# ---------------------------------------------------------------------------

def _row_index_for_date(df: pd.DataFrame, date: str) -> int:
    dt = pd.Timestamp(date)
    exact = df.index[df["date"] == dt]
    if len(exact):
        return int(exact[0])
    # nearest calendar row
    return int((df["date"] - dt).abs().idxmin())


def make_anchor(
    monthly: pd.DataFrame,
    date: str,
    price: Optional[float] = None,
) -> Pivot:
    idx = _row_index_for_date(monthly, date)
    p = float(price if price is not None else monthly.at[idx, "low"])
    return Pivot(
        idx=idx,
        date=monthly.at[idx, "date"].strftime("%Y-%m-%d"),
        kind="low",
        price=p,
        confirmed=True,
        atr14=float(monthly.at[idx, "ATR14"]),
        source_tf="monthly",
    )


def _endpoint_technical_bonus(df: pd.DataFrame, pivot: Pivot, wave_role: str) -> Tuple[float, List[str]]:
    """
    Optional indicators only add a small confidence bonus.
    They never override Elliott hard rules.
    """
    score = 0.0
    reasons: List[str] = []
    row = df.iloc[pivot.idx]

    vr = _safe_float(row.get("VOLUME_RATIO_20"))
    hist = _safe_float(row.get("MACD_HIST"))

    if wave_role == "wave3_high":
        if vr is not None and vr >= 1.20:
            score += 0.35
            reasons.append(f"wave3 volume expansion {vr:.2f}")
        if hist is not None and hist > 0:
            score += 0.25
            reasons.append("wave3 MACD histogram positive")

        # Strong wave-3 often expands above short/mid Bollinger upper lines.
        upper_values = []
        for c in (
            "BB_36_1.541_UPPER",
            "BB_60_1.541_UPPER",
            "BB_50_2.25_UPPER",
        ):
            v = _safe_float(row.get(c))
            if v is not None:
                upper_values.append(v)
        if upper_values and pivot.price > min(upper_values):
            score += 0.20
            reasons.append("wave3 price expanded through short/mid Bollinger upper")

    if wave_role == "wave4_low":
        if vr is not None and vr >= 1.20:
            score += 0.10
            reasons.append(f"wave4 high-volume reaction {vr:.2f}")

    return score, reasons


def weekly_pivot_confirmation(
    point: Pivot,
    weekly_pivots: Sequence[Pivot],
    same_kind: bool = True,
    max_days: int = 45,
    max_price_distance: float = 0.06,
) -> Tuple[float, Optional[Dict[str, Any]]]:
    if not weekly_pivots:
        return 0.0, None
    target_date = pd.Timestamp(point.date)
    candidates = []
    for p in weekly_pivots:
        if same_kind and p.kind != point.kind:
            continue
        days = abs((pd.Timestamp(p.date) - target_date).days)
        pdist = normalized_price_distance(p.price, point.price)
        if days <= max_days and pdist <= max_price_distance:
            candidates.append((days + pdist * 100.0, p, days, pdist))
    if not candidates:
        return 0.0, None
    _, p, days, pdist = min(candidates, key=lambda x: x[0])
    bonus = 0.50 if p.confirmed else 0.25
    return bonus, {
        "weekly_date": p.date,
        "weekly_price": p.price,
        "weekly_confirmed": p.confirmed,
        "day_distance": days,
        "price_distance_pct": pdist * 100.0,
    }


def _w5_projection_raw(
    w0: Pivot,
    w1: Pivot,
    w2: Pivot,
    w3: Pivot,
    w4: Pivot,
) -> List[Dict[str, Any]]:
    l1 = w1.price - w0.price
    l3 = w3.price - w2.price
    span_03 = w3.price - w0.price

    out: List[Dict[str, Any]] = []
    for mult in WAVE5_W1_MULTIPLES:
        out.append(
            {
                "method": f"W4 + W1*{mult}",
                "price": w4.price + l1 * mult,
                "family": "wave1_multiple",
            }
        )

    for mult in (0.382, 0.500, 0.618, 1.000):
        out.append(
            {
                "method": f"W4 + W3*{mult}",
                "price": w4.price + l3 * mult,
                "family": "wave3_multiple",
            }
        )

    for mult in (0.500, 0.618, 1.000):
        out.append(
            {
                "method": f"W4 + (W0->W3)*{mult}",
                "price": w4.price + span_03 * mult,
                "family": "span03_multiple",
            }
        )

    return sorted(out, key=lambda x: x["price"])


def cluster_projection_levels(
    levels: Sequence[Dict[str, Any]],
    tolerance_pct: float = 0.025,
) -> List[Dict[str, Any]]:
    if not levels:
        return []
    clusters: List[List[Dict[str, Any]]] = []
    for level in sorted(levels, key=lambda x: x["price"]):
        if not clusters:
            clusters.append([level])
            continue
        prev_center = float(np.median([x["price"] for x in clusters[-1]]))
        if normalized_price_distance(prev_center, level["price"]) <= tolerance_pct:
            clusters[-1].append(level)
        else:
            clusters.append([level])

    out = []
    for c in clusters:
        prices = [x["price"] for x in c]
        out.append(
            {
                "low": min(prices),
                "high": max(prices),
                "center": float(np.median(prices)),
                "methods": [x["method"] for x in c],
                "method_count": len(c),
            }
        )
    return sorted(out, key=lambda x: (-x["method_count"], x["center"]))


def fib_retracements(high: float, low: float) -> Dict[str, float]:
    """
    For a rise low -> high, returns downside retracement prices.
    """
    span = high - low
    return {
        f"{level:.3f}": high - span * level
        for level in FIB_RETRACE_LEVELS
    }


def rebound_fib(high: float, low: float) -> Dict[str, float]:
    """
    For a decline high -> low, returns recovery / rebound resistance prices.
    """
    span = high - low
    return {
        f"{level:.3f}": low + span * level
        for level in FIB_RETRACE_LEVELS
    }


def impulse_hypotheses_for_anchor(
    monthly: pd.DataFrame,
    anchor: Pivot,
    weekly_pivots: Optional[Sequence[Pivot]] = None,
    assume_last_incomplete: bool = True,
    max_results: int = 10,
) -> List[Dict[str, Any]]:
    pivs = detect_pivots(
        monthly,
        "monthly",
        left=2,
        right=2,
        lookback=None,
        assume_last_incomplete=assume_last_incomplete,
    )
    lows = [p for p in pivs if p.kind == "low"]
    highs = [p for p in pivs if p.kind == "high"]

    hypotheses: List[Dict[str, Any]] = []
    n_after_anchor = max(1, len(monthly) - 1 - anchor.idx)

    for w1 in highs:
        if w1.idx <= anchor.idx or w1.price <= anchor.price:
            continue
        # W1 must be a running maximum from W0 to its endpoint.
        if float(monthly.loc[anchor.idx : w1.idx, "high"].max()) > w1.price + 1e-9:
            continue

        l1 = w1.price - anchor.price
        if l1 <= 0:
            continue

        for w2 in lows:
            if w2.idx <= w1.idx:
                continue
            if not (anchor.price < w2.price < w1.price):
                continue
            # W2 endpoint should be the deepest low seen since W1.
            if float(monthly.loc[w1.idx : w2.idx, "low"].min()) < w2.price - 1e-9:
                continue

            r2 = (w1.price - w2.price) / l1
            w2s = band_score(r2, 0.500, 0.618, 0.236, 0.900)
            if w2s < 0:
                continue

            for w3 in highs:
                if w3.idx <= w2.idx or w3.price <= w1.price:
                    continue
                # W3 should be a running maximum since W2.
                if float(monthly.loc[w2.idx : w3.idx, "high"].max()) > w3.price + 1e-9:
                    continue

                l3 = w3.price - w2.price
                ext3 = l3 / l1
                if ext3 < 1.0:
                    continue

                for w4 in lows:
                    if w4.idx <= w3.idx:
                        continue
                    # Standard impulse hard rule: W4 must not overlap W1 price territory.
                    if not (w1.price < w4.price < w3.price):
                        continue
                    if float(monthly.loc[w3.idx : w4.idx, "low"].min()) < w4.price - 1e-9:
                        continue

                    r4 = (w3.price - w4.price) / l3
                    w4s = band_score(r4, 0.236, 0.500, 0.146, 0.786)
                    if w4s < 0:
                        continue

                    score = 0.0
                    reasons: List[str] = []
                    score += w2s
                    reasons.append(f"W2 retracement={r2:.3f}")
                    score += w4s
                    reasons.append(f"W4 retracement={r4:.3f}")

                    if ext3 >= 1.618:
                        score += 2.0
                    elif ext3 >= 1.0:
                        score += 1.0
                    if ext3 >= 2.618:
                        score += 1.0
                    if ext3 >= 4.236:
                        score += 0.5
                    reasons.append(f"W3/W1 extension={ext3:.3f}")

                    if ext3 >= 4.236:
                        reasons.append("W3 classified as strongly extended")
                    elif ext3 >= 2.618:
                        reasons.append("W3 classified as extended")

                    # Confirmation status: provisional endpoints are allowed but penalized.
                    confirmation_points = (w1, w2, w3, w4)
                    confirmed_count = sum(int(p.confirmed) for p in confirmation_points)
                    score += 0.50 * confirmed_count
                    score -= 0.35 * (4 - confirmed_count)

                    # Primary-degree preference: broad span and current relevance.
                    span_ratio = (w4.idx - anchor.idx) / n_after_anchor
                    score += 3.0 * max(0.0, min(span_ratio, 1.0))
                    amplitude_ratio = max(w3.price / anchor.price, 1.0)
                    score += min(2.0, math.log(amplitude_ratio, 2) / 3.0)

                    # Optional indicator confirmation.
                    b3, r3 = _endpoint_technical_bonus(monthly, w3, "wave3_high")
                    b4, r4_reason = _endpoint_technical_bonus(monthly, w4, "wave4_low")
                    score += b3 + b4
                    reasons.extend(r3 + r4_reason)

                    weekly_conf: Dict[str, Any] = {}
                    if weekly_pivots:
                        for name, pt in (("wave1", w1), ("wave2", w2), ("wave3", w3), ("wave4", w4)):
                            b, info = weekly_pivot_confirmation(pt, weekly_pivots)
                            score += b
                            if info:
                                weekly_conf[name] = info

                    # Search a standard non-truncated W5 candidate after W4.
                    w5_candidates: List[Tuple[float, Pivot, Dict[str, Any]]] = []
                    for w5 in highs:
                        if w5.idx <= w4.idx:
                            continue
                        if w5.price <= w3.price:
                            continue

                        l5 = w5.price - w4.price
                        # Hard rule: Wave 3 cannot be the shortest of 1,3,5.
                        if l3 < min(l1, l5):
                            continue

                        projections = _w5_projection_raw(anchor, w1, w2, w3, w4)
                        distances = [
                            normalized_price_distance(w5.price, x["price"])
                            for x in projections
                        ]
                        min_dist = min(distances) if distances else 1.0
                        w5_score = max(0.0, 1.5 * (1.0 - min_dist / 0.10))
                        if w5.confirmed:
                            w5_score += 0.5
                        w5_candidates.append(
                            (
                                w5_score,
                                w5,
                                {"nearest_projection_distance_pct": min_dist * 100.0},
                            )
                        )

                    w5_result = None
                    status = "W4_CANDIDATE_W5_UNCONFIRMED"
                    if w5_candidates:
                        w5_score, w5, meta = max(w5_candidates, key=lambda x: x[0])
                        score += w5_score
                        status = "W5_CANDIDATE"
                        w5_result = {**asdict(w5), **meta}

                    projection_raw = _w5_projection_raw(anchor, w1, w2, w3, w4)
                    projection_clusters = cluster_projection_levels(projection_raw, tolerance_pct=0.025)

                    hypotheses.append(
                        {
                            "score": round(score, 6),
                            "status": status,
                            "degree": "primary_monthly_candidate",
                            "wave0": asdict(anchor),
                            "wave1": asdict(w1),
                            "wave2": asdict(w2),
                            "wave3": asdict(w3),
                            "wave4": asdict(w4),
                            "wave5": w5_result,
                            "metrics": {
                                "wave1_length": l1,
                                "wave2_retracement": r2,
                                "wave3_length": l3,
                                "wave3_vs_wave1_extension": ext3,
                                "wave4_retracement_of_wave3": r4,
                                "wave3_extended": bool(ext3 >= 2.618),
                                "wave3_strongly_extended": bool(ext3 >= 4.236),
                            },
                            "hard_rules": {
                                "wave2_above_wave0": True,
                                "wave3_above_wave1": True,
                                "wave4_above_wave1_high": True,
                                "wave3_not_shortest": None if w5_result is None else True,
                            },
                            "fib": {
                                "wave1_retracement_prices": fib_retracements(w1.price, anchor.price),
                                "wave3_retracement_prices": fib_retracements(w3.price, w2.price),
                                "primary_cycle_retracement_prices": fib_retracements(w3.price, anchor.price),
                                "current_rebound_prices": rebound_fib(w3.price, w4.price),
                                "wave5_projection_raw": projection_raw,
                                "wave5_projection_clusters": projection_clusters,
                            },
                            "weekly_confirmation": weekly_conf,
                            "reasons": reasons,
                        }
                    )

    return sorted(hypotheses, key=lambda x: x["score"], reverse=True)[:max_results]


def auto_anchor_candidates(
    monthly: pd.DataFrame,
    weekly_pivots: Optional[Sequence[Pivot]] = None,
    cycle_lookback_years: float = 8.0,
    assume_last_incomplete: bool = True,
    max_anchors: int = 5,
) -> List[Dict[str, Any]]:
    """
    Search recent major monthly pivot lows as possible primary-cycle starts.
    The engine intentionally returns several candidates because Elliott degree is
    not uniquely identifiable from price alone.
    """
    pivs = detect_pivots(
        monthly,
        "monthly",
        left=2,
        right=2,
        lookback=None,
        assume_last_incomplete=assume_last_incomplete,
    )
    cutoff = monthly["date"].max() - pd.DateOffset(years=int(math.ceil(cycle_lookback_years)))
    low_candidates = [
        p for p in pivs
        if p.kind == "low" and pd.Timestamp(p.date) >= cutoff
    ]

    results = []
    max_date = monthly["date"].max()

    for anchor in low_candidates:
        age_years = (max_date - pd.Timestamp(anchor.date)).days / 365.25
        if age_years < 1.0:
            continue

        hyps = impulse_hypotheses_for_anchor(
            monthly,
            anchor,
            weekly_pivots=weekly_pivots,
            assume_last_incomplete=assume_last_incomplete,
            max_results=3,
        )
        if not hyps:
            continue

        # Base quality: anchor near the lowest low of the prior 24 months.
        lo_24 = float(monthly.loc[max(0, anchor.idx - 24) : anchor.idx, "low"].min())
        base_quality = 1.0 if normalized_price_distance(anchor.price, lo_24) <= 0.05 else 0.0

        # Mild preference for more recent anchors inside the allowed lookback.
        recency = max(0.0, 1.0 - age_years / cycle_lookback_years)

        top = hyps[0]
        anchor_score = top["score"] + base_quality + recency
        results.append(
            {
                "anchor": asdict(anchor),
                "anchor_score": round(anchor_score, 6),
                "base_quality_bonus": base_quality,
                "recency_bonus": recency,
                "best_impulse": top,
            }
        )

    return sorted(results, key=lambda x: x["anchor_score"], reverse=True)[:max_anchors]


# ---------------------------------------------------------------------------
# Support / resistance / confluence zones
# ---------------------------------------------------------------------------

def _adaptive_group_tolerance(price: float, atr14: float, timeframe: str) -> float:
    pct = TF_CONFIG[timeframe]["group_pct"]
    return max(price * pct, atr14 * 0.50)


def group_pivots_by_price(
    pivots: Sequence[Pivot],
    timeframe: str,
    kind: Optional[str] = None,
) -> List[List[Pivot]]:
    pts = [p for p in pivots if kind is None or p.kind == kind]
    if not pts:
        return []
    pts = sorted(pts, key=lambda p: p.price)
    groups: List[List[Pivot]] = [[pts[0]]]

    for p in pts[1:]:
        prev = groups[-1][-1]
        center = float(np.median([x.price for x in groups[-1]]))
        atr_ref = float(np.median([x.atr14 for x in groups[-1]] + [p.atr14]))
        tol = _adaptive_group_tolerance(center, atr_ref, timeframe)
        if p.price - prev.price <= tol:
            groups[-1].append(p)
        else:
            groups.append([p])
    return groups


def _pivot_group_to_zone(group: Sequence[Pivot], timeframe: str) -> Optional[Zone]:
    prices = [p.price for p in group]
    center = float(np.median(prices))
    atr_ref = float(np.median([p.atr14 for p in group]))
    padding = min(atr_ref * 0.10, center * 0.01)
    lo = min(prices) - padding
    hi = max(prices) + padding
    width_pct = (hi - lo) / max(center, 1e-12)
    if width_pct > TF_CONFIG[timeframe]["zone_width_cap"]:
        return None

    sources = [
        {
            "kind": f"pivot_{p.kind}",
            "date": p.date,
            "price": p.price,
            "confirmed": p.confirmed,
            "timeframe": p.source_tf,
        }
        for p in group
    ]
    score = 1.0 + max(0, len(group) - 1) * 0.70
    confirmed_count = sum(int(p.confirmed) for p in group)
    score += confirmed_count * 0.15

    return Zone(
        low=float(lo),
        high=float(hi),
        center=center,
        role="UNCLASSIFIED",
        score=float(score),
        sources=sources,
        reaction_count=len(group),
        width_pct=float(width_pct),
    )


def bollinger_point_anchors(df: pd.DataFrame, timeframe: str) -> List[Zone]:
    if len(df) == 0:
        return []
    row = df.iloc[-1]
    out = []
    for label, col in BB_UPPER_COLS.items():
        v = _safe_float(row.get(col))
        if v is None:
            continue
        out.append(
            Zone(
                low=v,
                high=v,
                center=v,
                role="UNCLASSIFIED",
                score=1.20,
                sources=[
                    {
                        "kind": "bollinger_upper",
                        "name": label,
                        "column": col,
                        "price": v,
                        "timeframe": timeframe,
                    }
                ],
                reaction_count=0,
                width_pct=0.0,
            )
        )
    return out


def fib_point_anchors(fib_sets: Dict[str, Dict[str, float]], timeframe: str) -> List[Zone]:
    out = []
    for fib_name, levels in fib_sets.items():
        for level, price in levels.items():
            if price is None or not np.isfinite(price):
                continue
            out.append(
                Zone(
                    low=float(price),
                    high=float(price),
                    center=float(price),
                    role="UNCLASSIFIED",
                    score=1.40,
                    sources=[
                        {
                            "kind": "fibonacci",
                            "name": fib_name,
                            "level": str(level),
                            "price": float(price),
                            "timeframe": timeframe,
                        }
                    ],
                    reaction_count=0,
                    width_pct=0.0,
                )
            )
    return out


def merge_confluent_zones(
    zones: Sequence[Zone],
    timeframe: str,
) -> List[Zone]:
    if not zones:
        return []

    tolerance_pct = TF_CONFIG[timeframe]["confluence_pct"]
    ordered = sorted(zones, key=lambda z: z.center)
    groups: List[List[Zone]] = [[ordered[0]]]

    for z in ordered[1:]:
        prev_center = float(np.median([x.center for x in groups[-1]]))
        if normalized_price_distance(prev_center, z.center) <= tolerance_pct:
            groups[-1].append(z)
        else:
            groups.append([z])

    merged: List[Zone] = []
    for g in groups:
        lo = min(z.low for z in g)
        hi = max(z.high for z in g)
        center = float(np.median([z.center for z in g]))
        cap = TF_CONFIG[timeframe]["zone_width_cap"]

        # Do not create an over-wide "everything zone".
        if (hi - lo) / max(center, 1e-12) > cap:
            merged.extend(g)
            continue

        source_list = []
        score = 0.0
        reactions = 0
        source_kinds = set()
        source_tfs = set()
        for z in g:
            source_list.extend(z.sources)
            score += z.score
            reactions += z.reaction_count
            for s in z.sources:
                source_kinds.add(s.get("kind"))
                source_tfs.add(s.get("timeframe"))

        # Confluence bonus for independent evidence.
        if len(source_kinds) >= 2:
            score += 1.0
        if len(source_tfs) >= 2:
            score += 0.5

        merged.append(
            Zone(
                low=float(lo),
                high=float(hi),
                center=center,
                role="UNCLASSIFIED",
                score=float(score),
                sources=source_list,
                reaction_count=reactions,
                width_pct=float((hi - lo) / max(center, 1e-12)),
            )
        )

    return sorted(merged, key=lambda z: z.center)


def classify_zones(zones: Sequence[Zone], current_price: float) -> List[Zone]:
    out = []
    for z in zones:
        zz = Zone(**asdict(z))
        if zz.high < current_price:
            zz.role = "SUPPORT"
        elif zz.low > current_price:
            zz.role = "RESISTANCE"
        else:
            zz.role = "CURRENT_ZONE"
        out.append(zz)
    return out


def detect_boxes(
    df: pd.DataFrame,
    zones: Sequence[Zone],
    timeframe: str,
    max_boxes: int = 5,
) -> List[Box]:
    cfg = TF_CONFIG[timeframe]
    recent_n = int(cfg["box_recent_bars"])
    recent = df.tail(recent_n).copy()
    if len(recent) < 3:
        return []

    candidates: List[Box] = []

    # Candidate boundaries come from nearby zone edges.
    lows = sorted(set(float(z.low) for z in zones))
    highs = sorted(set(float(z.high) for z in zones))

    for lo in lows:
        for hi in highs:
            if hi <= lo:
                continue
            center = (lo + hi) / 2.0
            width_pct = (hi - lo) / max(center, 1e-12)
            if width_pct > cfg["box_width_cap"]:
                continue

            close_inside = ((recent["close"] >= lo) & (recent["close"] <= hi)).mean()
            overlap = (
                np.maximum(
                    0.0,
                    np.minimum(recent["high"].to_numpy(), hi)
                    - np.maximum(recent["low"].to_numpy(), lo),
                )
                > 0
            ).mean()

            touched_lower = bool((recent["low"] <= lo * 1.01).any())
            touched_upper = bool((recent["high"] >= hi * 0.99).any())

            if (
                close_inside >= cfg["box_close_inside_min"]
                and overlap >= cfg["box_overlap_min"]
            ):
                score = (
                    close_inside * 2.0
                    + overlap * 2.0
                    + float(touched_lower)
                    + float(touched_upper)
                    - width_pct
                )
                candidates.append(
                    Box(
                        low=lo,
                        high=hi,
                        center=center,
                        width_pct=width_pct,
                        close_inside_ratio=float(close_inside),
                        range_overlap_ratio=float(overlap),
                        touched_lower=touched_lower,
                        touched_upper=touched_upper,
                        score=float(score),
                    )
                )

    # Remove highly redundant boxes.
    selected: List[Box] = []
    for b in sorted(candidates, key=lambda x: x.score, reverse=True):
        redundant = False
        for s in selected:
            if (
                normalized_price_distance(b.low, s.low) <= 0.02
                and normalized_price_distance(b.high, s.high) <= 0.02
            ):
                redundant = True
                break
        if not redundant:
            selected.append(b)
        if len(selected) >= max_boxes:
            break
    return selected


def build_zones(
    df: pd.DataFrame,
    timeframe: str,
    fib_sets: Optional[Dict[str, Dict[str, float]]] = None,
    assume_last_incomplete: bool = True,
) -> Dict[str, Any]:
    cfg = TF_CONFIG[timeframe]
    pivs = detect_pivots(
        df,
        timeframe,
        lookback=int(cfg["zone_lookback"]),
        assume_last_incomplete=assume_last_incomplete,
    )

    base_zones: List[Zone] = []
    for kind in ("low", "high"):
        for group in group_pivots_by_price(pivs, timeframe, kind=kind):
            z = _pivot_group_to_zone(group, timeframe)
            if z is not None:
                base_zones.append(z)

    base_zones.extend(bollinger_point_anchors(df, timeframe))
    if fib_sets:
        base_zones.extend(fib_point_anchors(fib_sets, timeframe))

    merged = merge_confluent_zones(base_zones, timeframe)
    current = float(df.iloc[-1]["close"])
    classified = classify_zones(merged, current)
    boxes = detect_boxes(df, classified, timeframe)

    # Sort practical levels by distance from current price.
    supports = sorted(
        [z for z in classified if z.role in ("SUPPORT", "CURRENT_ZONE")],
        key=lambda z: abs(current - z.center),
    )
    resistances = sorted(
        [z for z in classified if z.role in ("RESISTANCE", "CURRENT_ZONE")],
        key=lambda z: abs(current - z.center),
    )

    return {
        "timeframe": timeframe,
        "current_price": current,
        "pivots": [asdict(p) for p in pivs],
        "zones_all": [asdict(z) for z in classified],
        "supports_nearest": [asdict(z) for z in supports[:8]],
        "resistances_nearest": [asdict(z) for z in resistances[:8]],
        "boxes": [asdict(b) for b in boxes],
    }


# ---------------------------------------------------------------------------
# Full stock analysis
# ---------------------------------------------------------------------------

def _fib_sets_from_hypothesis(hyp: Optional[Dict[str, Any]]) -> Dict[str, Dict[str, float]]:
    if not hyp:
        return {}
    fib = hyp.get("fib", {})
    out = {}
    for key in (
        "primary_cycle_retracement_prices",
        "wave1_retracement_prices",
        "wave3_retracement_prices",
        "current_rebound_prices",
    ):
        if key in fib:
            out[key] = {k: float(v) for k, v in fib[key].items()}
    return out


def analyze_stock(
    daily: pd.DataFrame,
    weekly: pd.DataFrame,
    monthly: pd.DataFrame,
    anchor_mode: str = "auto",
    anchor_date: Optional[str] = None,
    anchor_price: Optional[float] = None,
    cycle_lookback_years: float = 8.0,
    assume_last_incomplete: bool = True,
) -> Dict[str, Any]:
    weekly_pivs = detect_pivots(
        weekly,
        "weekly",
        lookback=None,
        assume_last_incomplete=assume_last_incomplete,
    )

    auto_candidates = auto_anchor_candidates(
        monthly,
        weekly_pivots=weekly_pivs,
        cycle_lookback_years=cycle_lookback_years,
        assume_last_incomplete=assume_last_incomplete,
        max_anchors=5,
    )

    user_hypotheses: List[Dict[str, Any]] = []
    selected_hyp: Optional[Dict[str, Any]] = None
    selected_anchor: Optional[Dict[str, Any]] = None

    if anchor_mode in ("user", "hybrid") and anchor_date:
        anchor = make_anchor(monthly, anchor_date, anchor_price)
        user_hypotheses = impulse_hypotheses_for_anchor(
            monthly,
            anchor,
            weekly_pivots=weekly_pivs,
            assume_last_incomplete=assume_last_incomplete,
            max_results=10,
        )
        if user_hypotheses:
            selected_hyp = user_hypotheses[0]
            selected_anchor = asdict(anchor)

    if selected_hyp is None and auto_candidates:
        selected_hyp = auto_candidates[0]["best_impulse"]
        selected_anchor = auto_candidates[0]["anchor"]

    fib_sets = _fib_sets_from_hypothesis(selected_hyp)

    zones = {
        "daily": build_zones(
            daily,
            "daily",
            fib_sets=fib_sets,
            assume_last_incomplete=assume_last_incomplete,
        ),
        "weekly": build_zones(
            weekly,
            "weekly",
            fib_sets=fib_sets,
            assume_last_incomplete=assume_last_incomplete,
        ),
        "monthly": build_zones(
            monthly,
            "monthly",
            fib_sets=fib_sets,
            assume_last_incomplete=assume_last_incomplete,
        ),
    }

    latest = monthly.iloc[-1]
    identity = {
        "symbol": latest.get("symbol") if "symbol" in monthly.columns else None,
        "code": latest.get("code") if "code" in monthly.columns else None,
        "name": latest.get("name") if "name" in monthly.columns else None,
        "market": latest.get("market") if "market" in monthly.columns else None,
        "sector": latest.get("sector") if "sector" in monthly.columns else None,
    }

    return {
        "engine": {
            "name": "universal_ohlcv_structure_elliott_engine",
            "version": "1.0.0",
            "assume_last_incomplete": assume_last_incomplete,
            "anchor_mode": anchor_mode,
            "cycle_lookback_years": cycle_lookback_years,
        },
        "identity": identity,
        "selected_anchor": selected_anchor,
        "selected_impulse": selected_hyp,
        "user_anchor_hypotheses": user_hypotheses,
        "auto_anchor_candidates": auto_candidates,
        "zones": zones,
        "interpretation_rules": {
            "pivot_first": True,
            "fibonacci_is_validator_not_endpoint_generator": True,
            "hard_rules_override_soft_scores": True,
            "partial_impulse_allowed": True,
            "wave4_candidate_requires_future_wave5_confirmation": True,
            "nontruncated_wave5_requires_break_above_wave3": True,
        },
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    ap = argparse.ArgumentParser(
        description="Universal OHLCV support/resistance + Elliott/Fibonacci engine"
    )
    ap.add_argument("--daily", required=True, help="daily OHLCV CSV")
    ap.add_argument("--weekly", required=True, help="weekly OHLCV CSV")
    ap.add_argument("--monthly", required=True, help="monthly OHLCV CSV")
    ap.add_argument(
        "--anchor-mode",
        choices=("auto", "user", "hybrid"),
        default="auto",
        help="auto: automatic anchor; user/hybrid: use --anchor-date",
    )
    ap.add_argument("--anchor-date", default=None, help="e.g. 2023-01-02")
    ap.add_argument("--anchor-price", type=float, default=None)
    ap.add_argument("--cycle-lookback-years", type=float, default=8.0)
    ap.add_argument(
        "--last-bar-complete",
        action="store_true",
        help="set only when the latest bar of each timeframe is known complete",
    )
    ap.add_argument("--out", required=True, help="output JSON")
    args = ap.parse_args()

    daily = load_ohlcv(args.daily)
    weekly = load_ohlcv(args.weekly)
    monthly = load_ohlcv(args.monthly)

    result = analyze_stock(
        daily=daily,
        weekly=weekly,
        monthly=monthly,
        anchor_mode=args.anchor_mode,
        anchor_date=args.anchor_date,
        anchor_price=args.anchor_price,
        cycle_lookback_years=args.cycle_lookback_years,
        assume_last_incomplete=not args.last_bar_complete,
    )

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2, default=str)

    print(f"saved: {out}")


if __name__ == "__main__":
    main()
