from __future__ import annotations

import hashlib
import json
from collections import Counter
from collections.abc import Callable, Mapping, Sequence
from decimal import Decimal, ROUND_HALF_UP
from enum import StrEnum
from statistics import median
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from app.services.multi_timeframe_price_structure_service import (
    CONTRACT_VERSION as PRICE_STRUCTURE_CONTRACT,
    TIMEFRAME_ORDER,
    MultiTimeframeSelection,
    PivotEvidence,
    PriceStructureEvidencePacket,
    ShadowPriceStructureResult,
    SynthesisSelection,
    TimeframeEvidence,
    TimeframeSelection,
    ZoneEvidence,
    build_shadow_price_structure_result,
    reference_select_price_structure,
)
from app.services.ohlcv_structure_service import LOCAL_CONFIG, Timeframe, normalize_structure_bars


PACKET_CONTRACT = "price-only-ai-anchor-packet-v1"
OUTPUT_CONTRACT = "variable-ai-swing-anchor-selection-v1"
STABILITY_CONTRACT = "ai-anchor-stability-policy-v1"

RECENT_WINDOW_LIMITS: dict[Timeframe, int] = {
    "monthly": 36,
    "weekly": 52,
    "daily": 90,
}
NEIGHBORHOOD_RADII: dict[Timeframe, int] = {
    "monthly": 2,
    "weekly": 3,
    "daily": 5,
}

ReasonCategory = Literal[
    "MAJOR_BASE",
    "BREAKOUT_ORIGIN",
    "HIGHER_LOW",
    "RETEST_SUPPORT",
    "PRIOR_HIGH_RECLAIM",
    "EXPANSION_SWING",
    "CORRECTIVE_LOW",
    "REJECTION_HIGH",
    "STRUCTURAL_CYCLE_LOW",
    "AMBIGUOUS_COMPETING_SWINGS",
]


class FrozenModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class CandleFeatures(FrozenModel):
    range: Decimal
    body: Decimal
    upper_wick: Decimal
    lower_wick: Decimal
    close_location: Decimal | None = None
    gap_relation: Literal["ABOVE_PRIOR_HIGH", "BELOW_PRIOR_LOW", "WITHIN_PRIOR_RANGE", "NONE"]
    volume_ratio: Decimal | None = None
    trading_value_ratio: Decimal | None = None
    high_relation: Literal["HIGHER_HIGH", "LOWER_HIGH", "EQUAL_HIGH", "NONE"]
    low_relation: Literal["HIGHER_LOW", "LOWER_LOW", "EQUAL_LOW", "NONE"]
    breakout: bool
    reclaim: bool
    rejection: bool


class AnchorBarEvidence(FrozenModel):
    bar_id: str
    ticker: str
    timeframe: Timeframe
    date: str
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal | None = None
    trading_value: Decimal | None = None
    features: CandleFeatures
    source_ref: str


class CandidateNeighborhood(FrozenModel):
    pivot_id: str
    center_bar_id: str
    bar_ids: tuple[str, ...]


class SwingSegmentEvidence(FrozenModel):
    segment_id: str
    timeframe: Timeframe
    start_pivot_ref: str
    end_pivot_ref: str
    start_bar_ref: str
    end_bar_ref: str
    bar_count: int
    price_change_pct: Decimal
    max_drawdown_pct: Decimal
    volume_end_to_start_ratio: Decimal | None = None
    breakout_bar_refs: tuple[str, ...] = ()
    reclaim_bar_refs: tuple[str, ...] = ()
    rejection_bar_refs: tuple[str, ...] = ()


class TimeframeAnchorEvidence(FrozenModel):
    timeframe: Timeframe
    analytical_role: str
    status: Literal["AVAILABLE", "INSUFFICIENT_STRUCTURE"]
    as_of: str | None
    total_canonical_bars_available: int
    recent_window_limit: int
    recent_raw_bar_count: int
    candidate_neighborhood_radius: int
    bars: tuple[AnchorBarEvidence, ...] = ()
    recent_bar_ids: tuple[str, ...] = ()
    pivots: tuple[PivotEvidence, ...] = ()
    sr_candidates: tuple[ZoneEvidence, ...] = ()
    candidate_neighborhoods: tuple[CandidateNeighborhood, ...] = ()
    swing_segments: tuple[SwingSegmentEvidence, ...] = ()
    eligible_candidate_count: int = 0
    included_candidate_count: int = 0
    omitted_candidate_count: int = 0
    omission_reasons: tuple[str, ...] = ()


class PriceOnlyAIAnchorPacket(FrozenModel):
    contract: str = PACKET_CONTRACT
    stage: Literal["ANCHOR_SELECTION"] = "ANCHOR_SELECTION"
    source_price_structure_contract: str = PRICE_STRUCTURE_CONTRACT
    ticker: str
    security_id: str
    market: Literal["KR", "US"]
    currency: str
    current_price: Decimal
    as_of: str
    cutoff: str
    adjustment_basis: str
    evidence_mode: Literal["COMPACT_RICH", "FULL_DEBUG"] = "COMPACT_RICH"
    source_evidence_sha256: str
    evidence_sha256: str
    monthly: TimeframeAnchorEvidence
    weekly: TimeframeAnchorEvidence
    daily: TimeframeAnchorEvidence


class AlternativeAnchorSelection(FrozenModel):
    low_pivot_id: str | None = None
    high_pivot_id: str | None = None
    correction_low_pivot_id: str | None = None
    reason_category: ReasonCategory


class VariableTimeframeSelection(FrozenModel):
    status: Literal["SELECTED", "INSUFFICIENT_STRUCTURE", "AMBIGUOUS"]
    support_zone_id: str | None = None
    resistance_zone_id: str | None = None
    fib_mode: Literal["RETRACEMENT", "EXTENSION", "BOTH", "NONE"] = "NONE"
    low_pivot_id: str | None = None
    high_pivot_id: str | None = None
    correction_low_pivot_id: str | None = None
    alternative: AlternativeAnchorSelection | None = None
    confidence: Literal["HIGH", "MEDIUM", "LOW"] = "LOW"
    reason_categories: tuple[ReasonCategory, ...] = Field(min_length=1, max_length=3)
    evidence_refs: tuple[str, ...] = Field(default=(), max_length=16)
    concise_reason: str = Field(default="", max_length=240)


class VariableAIAnchorOutput(FrozenModel):
    contract: Literal["variable-ai-swing-anchor-selection-v1"] = OUTPUT_CONTRACT
    ticker: str
    monthly: VariableTimeframeSelection
    weekly: VariableTimeframeSelection
    daily: VariableTimeframeSelection


class VariableAIAnchorBatchOutput(FrozenModel):
    contract: Literal["variable-ai-swing-anchor-selection-batch-v1"] = (
        "variable-ai-swing-anchor-selection-batch-v1"
    )
    selections: tuple[VariableAIAnchorOutput, ...]


class VariableAnchorValidation(FrozenModel):
    valid: bool
    errors: tuple[str, ...] = ()
    timeframe_status: dict[Timeframe, Literal["PASS", "OMITTED", "REJECTED"]]


class VariableAnchorExecutionResult(FrozenModel):
    status: Literal["PASS", "FAIL_CLOSED"]
    failure_reason: str | None = None
    output: VariableAIAnchorOutput | None = None
    validation: VariableAnchorValidation
    selection: MultiTimeframeSelection
    shadow: ShadowPriceStructureResult
    fallback_timeframes: tuple[Timeframe, ...] = ()
    packet_continues: bool = True


class StabilityClass(StrEnum):
    STABLE = "STABLE"
    MINOR_VARIATION = "MINOR_VARIATION"
    MATERIAL_VARIATION = "MATERIAL_VARIATION"


class TimeframeStability(FrozenModel):
    timeframe: Timeframe
    classification: StabilityClass
    run_count: int
    exact_signature_count: int
    low_anchor_frequency: dict[str, int]
    high_anchor_frequency: dict[str, int]
    correction_anchor_frequency: dict[str, int]
    fib_mode_frequency: dict[str, int]
    support_zone_frequency: dict[str, int]
    resistance_zone_frequency: dict[str, int]
    structure_equivalent: bool


class StockStabilityDecision(FrozenModel):
    contract: str = STABILITY_CONTRACT
    ticker: str
    monthly: TimeframeStability
    weekly: TimeframeStability
    daily: TimeframeStability
    user_visible_eligible: bool
    timeframe_fib_fallbacks: tuple[Timeframe, ...] = ()


def _decimal(value: object) -> Decimal:
    return Decimal(str(value))


def _rounded(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)


def _stable_id(prefix: str, *parts: object) -> str:
    material = "|".join(str(part) for part in parts)
    return f"{prefix}:{hashlib.sha256(material.encode()).hexdigest()[:20]}"


def _canonical_hash(value: object) -> str:
    payload = json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode()).hexdigest()


def _median_ratio(values: Sequence[Decimal], index: int) -> Decimal | None:
    if index <= 0 or not values[index]:
        return None
    history = [item for item in values[max(0, index - 20) : index] if item > 0]
    if not history:
        return None
    reference = Decimal(str(median(history)))
    return _rounded(values[index] / reference) if reference else None


def _bar_features(
    bars: Sequence[Mapping[str, object]],
    index: int,
) -> CandleFeatures:
    current = bars[index]
    open_price = _decimal(current["open"])
    high = _decimal(current["high"])
    low = _decimal(current["low"])
    close = _decimal(current["close"])
    price_range = high - low
    body = abs(close - open_price)
    previous = bars[index - 1] if index else None
    previous_high = _decimal(previous["high"]) if previous else None
    previous_low = _decimal(previous["low"]) if previous else None
    previous_close = _decimal(previous["close"]) if previous else None
    if previous_high is None or previous_low is None:
        gap = "NONE"
        high_relation = "NONE"
        low_relation = "NONE"
    else:
        gap = (
            "ABOVE_PRIOR_HIGH"
            if open_price > previous_high
            else "BELOW_PRIOR_LOW"
            if open_price < previous_low
            else "WITHIN_PRIOR_RANGE"
        )
        high_relation = (
            "HIGHER_HIGH" if high > previous_high else "LOWER_HIGH" if high < previous_high else "EQUAL_HIGH"
        )
        low_relation = (
            "HIGHER_LOW" if low > previous_low else "LOWER_LOW" if low < previous_low else "EQUAL_LOW"
        )
    volumes = [_decimal(item.get("volume") or 0) for item in bars]
    trading_values = [_decimal(item.get("trading_value") or 0) for item in bars]
    breakout = bool(previous_high is not None and close > previous_high)
    reclaim = bool(
        previous_low is not None
        and previous_close is not None
        and low < previous_low
        and close >= previous_close
    )
    rejection = bool(
        previous_high is not None
        and previous_low is not None
        and ((high > previous_high and close < previous_high) or (low < previous_low and close > previous_low))
    )
    return CandleFeatures(
        range=_rounded(price_range),
        body=_rounded(body),
        upper_wick=_rounded(high - max(open_price, close)),
        lower_wick=_rounded(min(open_price, close) - low),
        close_location=_rounded((close - low) / price_range) if price_range else None,
        gap_relation=gap,
        volume_ratio=_median_ratio(volumes, index),
        trading_value_ratio=_median_ratio(trading_values, index),
        high_relation=high_relation,
        low_relation=low_relation,
        breakout=breakout,
        reclaim=reclaim,
        rejection=rejection,
    )


def _anchor_bar(
    ticker: str,
    timeframe: Timeframe,
    adjustment_basis: str,
    raw: Mapping[str, object],
    features: CandleFeatures,
) -> AnchorBarEvidence:
    date = str(raw["date"])[:10]
    return AnchorBarEvidence(
        bar_id=_stable_id("price-bar", ticker, timeframe, date, adjustment_basis),
        ticker=ticker,
        timeframe=timeframe,
        date=date,
        open=_decimal(raw["open"]),
        high=_decimal(raw["high"]),
        low=_decimal(raw["low"]),
        close=_decimal(raw["close"]),
        volume=_decimal(raw["volume"]) if raw.get("volume") is not None else None,
        trading_value=(
            _decimal(raw["trading_value"]) if raw.get("trading_value") is not None else None
        ),
        features=features,
        source_ref=f"ohlcv-structure-v2:completed_bar:{timeframe}:{date}",
    )


def _segment(
    timeframe: Timeframe,
    start: PivotEvidence,
    end: PivotEvidence,
    bars: Sequence[AnchorBarEvidence],
) -> SwingSegmentEvidence | None:
    selected = [bar for bar in bars if start.date <= bar.date <= end.date]
    if not selected:
        return None
    running_high = selected[0].high
    max_drawdown = Decimal(0)
    for bar in selected:
        running_high = max(running_high, bar.high)
        if running_high:
            max_drawdown = max(max_drawdown, (running_high - bar.low) / running_high * 100)
    midpoint = max(1, len(selected) // 2)
    first_volumes = [bar.volume for bar in selected[:midpoint] if bar.volume is not None]
    last_volumes = [bar.volume for bar in selected[midpoint:] if bar.volume is not None]
    volume_ratio: Decimal | None = None
    if first_volumes and last_volumes:
        first = sum(first_volumes) / len(first_volumes)
        last = sum(last_volumes) / len(last_volumes)
        volume_ratio = _rounded(last / first) if first else None
    return SwingSegmentEvidence(
        segment_id=_stable_id("price-segment", timeframe, start.pivot_id, end.pivot_id),
        timeframe=timeframe,
        start_pivot_ref=start.pivot_id,
        end_pivot_ref=end.pivot_id,
        start_bar_ref=selected[0].bar_id,
        end_bar_ref=selected[-1].bar_id,
        bar_count=len(selected),
        price_change_pct=_rounded((end.price - start.price) / start.price * 100),
        max_drawdown_pct=_rounded(max_drawdown),
        volume_end_to_start_ratio=volume_ratio,
        breakout_bar_refs=tuple(bar.bar_id for bar in selected if bar.features.breakout),
        reclaim_bar_refs=tuple(bar.bar_id for bar in selected if bar.features.reclaim),
        rejection_bar_refs=tuple(bar.bar_id for bar in selected if bar.features.rejection),
    )


def _timeframe_anchor_evidence(
    packet: PriceStructureEvidencePacket,
    timeframe: Timeframe,
    raw_bars: Sequence[Mapping[str, object]],
    *,
    full_debug: bool,
) -> TimeframeAnchorEvidence:
    source: TimeframeEvidence = getattr(packet, timeframe)
    normalized = [
        {
            "date": bar.date,
            "open": bar.open,
            "high": bar.high,
            "low": bar.low,
            "close": bar.close,
            "volume": bar.volume,
            "trading_value": next(
                (
                    item.get("trading_value")
                    for item in raw_bars
                    if str(item.get("date") or "")[:10] == bar.date
                ),
                None,
            ),
        }
        for bar in normalize_structure_bars(raw_bars)
        if bar.date <= packet.cutoff
    ]
    rich_bars = tuple(
        _anchor_bar(
            packet.ticker,
            timeframe,
            packet.adjustment_basis,
            raw,
            _bar_features(normalized, index),
        )
        for index, raw in enumerate(normalized)
    )
    date_to_index = {bar.date: index for index, bar in enumerate(rich_bars)}
    recent_limit = len(rich_bars) if full_debug else RECENT_WINDOW_LIMITS[timeframe]
    recent_indices = set(range(max(0, len(rich_bars) - recent_limit), len(rich_bars)))
    radius = NEIGHBORHOOD_RADII[timeframe]
    included_indices = set(recent_indices)
    neighborhoods: list[CandidateNeighborhood] = []
    omitted: list[str] = []
    for pivot in source.pivots:
        center = date_to_index.get(pivot.date)
        if center is None:
            omitted.append(f"{pivot.pivot_id}:matching_completed_bar_missing")
            continue
        indices = tuple(range(max(0, center - radius), min(len(rich_bars), center + radius + 1)))
        included_indices.update(indices)
        neighborhoods.append(
            CandidateNeighborhood(
                pivot_id=pivot.pivot_id,
                center_bar_id=rich_bars[center].bar_id,
                bar_ids=tuple(rich_bars[index].bar_id for index in indices),
            )
        )
    included_bars = tuple(rich_bars[index] for index in sorted(included_indices))
    segment_values = tuple(
        segment
        for start, end in zip(source.pivots, source.pivots[1:])
        if (segment := _segment(timeframe, start, end, rich_bars)) is not None
    )
    return TimeframeAnchorEvidence(
        timeframe=timeframe,
        analytical_role=source.analytical_role,
        status=source.status,
        as_of=source.as_of,
        total_canonical_bars_available=len(rich_bars),
        recent_window_limit=recent_limit,
        recent_raw_bar_count=len(recent_indices),
        candidate_neighborhood_radius=radius,
        bars=included_bars,
        recent_bar_ids=tuple(rich_bars[index].bar_id for index in sorted(recent_indices)),
        pivots=source.pivots,
        sr_candidates=source.sr_candidates,
        candidate_neighborhoods=tuple(neighborhoods),
        swing_segments=segment_values,
        eligible_candidate_count=len(source.pivots),
        included_candidate_count=len(neighborhoods),
        omitted_candidate_count=len(omitted),
        omission_reasons=tuple(omitted),
    )


def build_price_only_ai_anchor_packet(
    packet: PriceStructureEvidencePacket,
    bars_by_timeframe: Mapping[Timeframe, Sequence[Mapping[str, object]]],
    *,
    market: Literal["KR", "US"],
    full_debug: bool = False,
) -> PriceOnlyAIAnchorPacket:
    values = {
        timeframe: _timeframe_anchor_evidence(
            packet,
            timeframe,
            bars_by_timeframe.get(timeframe, ()),
            full_debug=full_debug,
        )
        for timeframe in TIMEFRAME_ORDER
    }
    hash_material = {
        "contract": PACKET_CONTRACT,
        "stage": "ANCHOR_SELECTION",
        "source_price_structure_contract": PRICE_STRUCTURE_CONTRACT,
        "ticker": packet.ticker,
        "security_id": packet.security_id,
        "market": market,
        "currency": packet.currency,
        "current_price": str(packet.current_price),
        "as_of": packet.as_of,
        "cutoff": packet.cutoff,
        "adjustment_basis": packet.adjustment_basis,
        "evidence_mode": "FULL_DEBUG" if full_debug else "COMPACT_RICH",
        "source_evidence_sha256": packet.evidence_sha256,
        **{key: value.model_dump(mode="json") for key, value in values.items()},
    }
    return PriceOnlyAIAnchorPacket(
        ticker=packet.ticker,
        security_id=packet.security_id,
        market=market,
        currency=packet.currency,
        current_price=packet.current_price,
        as_of=packet.as_of,
        cutoff=packet.cutoff,
        adjustment_basis=packet.adjustment_basis,
        evidence_mode="FULL_DEBUG" if full_debug else "COMPACT_RICH",
        source_evidence_sha256=packet.evidence_sha256,
        evidence_sha256=_canonical_hash(hash_material),
        monthly=values["monthly"],
        weekly=values["weekly"],
        daily=values["daily"],
    )


_BANNED_EGRESS_KEYS = {
    "user",
    "user_id",
    "account",
    "account_id",
    "portfolio",
    "portfolio_size",
    "cost_basis",
    "private_notes",
    "thesis",
    "telegram",
    "telegram_id",
    "notification",
    "notification_metadata",
    "token",
    "secret",
    "password",
    "api_key",
    "auth_header",
}


def audit_price_only_evidence_egress(packet: PriceOnlyAIAnchorPacket) -> dict[str, object]:
    payload = packet.model_dump(mode="json")
    key_violations: list[str] = []
    fibonacci_fields: list[str] = []

    def visit(value: object, path: str) -> None:
        if isinstance(value, Mapping):
            for key, item in value.items():
                normalized = str(key).casefold()
                child = f"{path}.{key}" if path else str(key)
                if normalized in _BANNED_EGRESS_KEYS:
                    key_violations.append(child)
                if "fibonacci" in normalized or normalized.startswith("fib_"):
                    fibonacci_fields.append(child)
                visit(item, child)
        elif isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
            for index, item in enumerate(value):
                visit(item, f"{path}[{index}]")

    visit(payload, "")
    return {
        "contract": "price-only-evidence-egress-audit-v1",
        "status": "PASS" if not key_violations and not fibonacci_fields else "FAIL",
        "private_field_egress": len(key_violations),
        "secret_egress": sum(
            any(token in path for token in ("token", "secret", "password", "api_key", "auth"))
            for path in key_violations
        ),
        "unrelated_thesis_egress": sum("thesis" in path for path in key_violations),
        "precomputed_fibonacci_fields": len(fibonacci_fields),
        "violations": sorted([*key_violations, *fibonacci_fields]),
        "serialized_bytes": len(json.dumps(payload, ensure_ascii=False, separators=(",", ":"))),
    }


def to_price_structure_evidence_packet(
    packet: PriceOnlyAIAnchorPacket,
) -> PriceStructureEvidencePacket:
    timeframe_values = {
        timeframe: TimeframeEvidence(
            timeframe=timeframe,
            analytical_role=getattr(packet, timeframe).analytical_role,
            status=getattr(packet, timeframe).status,
            as_of=getattr(packet, timeframe).as_of,
            pivots=getattr(packet, timeframe).pivots,
            sr_candidates=getattr(packet, timeframe).sr_candidates,
            omitted_candidate_count=getattr(packet, timeframe).omitted_candidate_count,
        )
        for timeframe in TIMEFRAME_ORDER
    }
    return PriceStructureEvidencePacket(
        ticker=packet.ticker,
        security_id=packet.security_id,
        currency=packet.currency,
        current_price=packet.current_price,
        as_of=packet.as_of,
        cutoff=packet.cutoff,
        adjustment_basis=packet.adjustment_basis,
        evidence_mode="FULL_DEBUG",
        evidence_sha256=packet.source_evidence_sha256,
        monthly=timeframe_values["monthly"],
        weekly=timeframe_values["weekly"],
        daily=timeframe_values["daily"],
    )


def validate_variable_ai_anchor_output(
    packet: PriceOnlyAIAnchorPacket,
    output: VariableAIAnchorOutput,
) -> VariableAnchorValidation:
    errors: list[str] = []
    statuses: dict[Timeframe, Literal["PASS", "OMITTED", "REJECTED"]] = {}
    if output.ticker != packet.ticker:
        errors.append("ticker:mismatch")
        return VariableAnchorValidation(
            valid=False,
            errors=tuple(errors),
            timeframe_status={timeframe: "REJECTED" for timeframe in TIMEFRAME_ORDER},
        )
    for timeframe in TIMEFRAME_ORDER:
        evidence: TimeframeAnchorEvidence = getattr(packet, timeframe)
        selected: VariableTimeframeSelection = getattr(output, timeframe)
        zones = {item.zone_id: item for item in evidence.sr_candidates}
        pivots = {item.pivot_id: item for item in evidence.pivots}
        other_refs = {
            item.bar_id for item in evidence.bars
        } | {item.segment_id for item in evidence.swing_segments}
        timeframe_errors: list[str] = []
        for field_name in ("support_zone_id", "resistance_zone_id"):
            ref = getattr(selected, field_name)
            if ref is not None and ref not in zones:
                timeframe_errors.append(f"{timeframe}:{field_name}:unknown_or_cross_timeframe_ref")
        support = zones.get(selected.support_zone_id or "")
        resistance = zones.get(selected.resistance_zone_id or "")
        if support is not None and support.role not in {"SUPPORT", "ACTIVE"}:
            timeframe_errors.append(f"{timeframe}:support_zone_role_invalid")
        if resistance is not None and resistance.role != "RESISTANCE":
            timeframe_errors.append(f"{timeframe}:resistance_zone_role_invalid")
        valid_refs = {*zones, *pivots, *other_refs}
        if any(ref not in valid_refs for ref in selected.evidence_refs):
            timeframe_errors.append(f"{timeframe}:evidence_ref_invalid")
        selected_refs = {
            ref
            for ref in (
                selected.support_zone_id,
                selected.resistance_zone_id,
                selected.low_pivot_id,
                selected.high_pivot_id,
                selected.correction_low_pivot_id,
            )
            if ref is not None
        }
        if not selected_refs.issubset(set(selected.evidence_refs)):
            timeframe_errors.append(f"{timeframe}:selected_ref_missing_from_evidence_refs")
        if selected.status != "SELECTED":
            if any(
                (
                    selected.low_pivot_id,
                    selected.high_pivot_id,
                    selected.correction_low_pivot_id,
                )
            ):
                timeframe_errors.append(f"{timeframe}:non_selected_pivot_ref")
            if selected.fib_mode != "NONE":
                timeframe_errors.append(f"{timeframe}:non_selected_fibonacci")
            if selected.alternative is not None:
                timeframe_errors.append(f"{timeframe}:non_selected_alternative")
            errors.extend(timeframe_errors)
            statuses[timeframe] = "REJECTED" if timeframe_errors else "OMITTED"
            continue
        for field_name in ("low_pivot_id", "high_pivot_id", "correction_low_pivot_id"):
            ref = getattr(selected, field_name)
            if ref is not None and ref not in pivots:
                timeframe_errors.append(f"{timeframe}:{field_name}:unknown_or_cross_timeframe_ref")
        low = pivots.get(selected.low_pivot_id or "")
        high = pivots.get(selected.high_pivot_id or "")
        correction = pivots.get(selected.correction_low_pivot_id or "")
        if selected.fib_mode != "NONE":
            if low is None or high is None:
                timeframe_errors.append(f"{timeframe}:fib_anchor_missing")
            elif low.kind != "low" or high.kind != "high":
                timeframe_errors.append(f"{timeframe}:fib_anchor_kind_invalid")
            elif not (low.date < high.date and low.price < high.price):
                timeframe_errors.append(f"{timeframe}:fib_anchor_chronology_invalid")
        if selected.fib_mode in {"EXTENSION", "BOTH"}:
            if correction is None:
                timeframe_errors.append(f"{timeframe}:extension_correction_missing")
            elif low is None or high is None or not (
                correction.kind == "low"
                and correction.date > high.date
                and correction.price > low.price
            ):
                timeframe_errors.append(f"{timeframe}:extension_correction_invalid")
        alternative = selected.alternative
        if alternative is not None:
            alt_low = pivots.get(alternative.low_pivot_id or "")
            alt_high = pivots.get(alternative.high_pivot_id or "")
            alt_correction = pivots.get(alternative.correction_low_pivot_id or "")
            for field_name in (
                "low_pivot_id",
                "high_pivot_id",
                "correction_low_pivot_id",
            ):
                ref = getattr(alternative, field_name)
                if ref is not None and ref not in pivots:
                    timeframe_errors.append(
                        f"{timeframe}:alternative:{field_name}:unknown_or_cross_timeframe_ref"
                    )
            if (alt_low is None) != (alt_high is None):
                timeframe_errors.append(f"{timeframe}:alternative:anchor_pair_incomplete")
            elif alt_low is not None and alt_high is not None and not (
                alt_low.kind == "low"
                and alt_high.kind == "high"
                and alt_low.date < alt_high.date
                and alt_low.price < alt_high.price
            ):
                timeframe_errors.append(f"{timeframe}:alternative:chronology_invalid")
            if alt_correction is not None and (
                alt_high is None
                or alt_low is None
                or alt_correction.kind != "low"
                or alt_correction.date <= alt_high.date
                or alt_correction.price <= alt_low.price
            ):
                timeframe_errors.append(f"{timeframe}:alternative:correction_invalid")
        errors.extend(timeframe_errors)
        statuses[timeframe] = "REJECTED" if timeframe_errors else "PASS"
    return VariableAnchorValidation(valid=not errors, errors=tuple(errors), timeframe_status=statuses)


def _regime(
    current_price: Decimal,
    low: PivotEvidence | None,
    high: PivotEvidence | None,
    correction: PivotEvidence | None,
) -> str:
    if low is None or high is None:
        return "RANGE_OR_INSUFFICIENT"
    if correction is not None and current_price >= correction.price:
        return "UPTREND_PULLBACK_HELD"
    if current_price > high.price:
        return "ABOVE_CONFIRMED_SWING_HIGH"
    if low.price <= current_price <= high.price:
        return "RETRACEMENT_WITHIN_CONFIRMED_SWING"
    return "BELOW_CONFIRMED_SWING_LOW"


def _selection_with_fallback(
    packet: PriceOnlyAIAnchorPacket,
    output: VariableAIAnchorOutput | None,
    validation: VariableAnchorValidation,
) -> tuple[MultiTimeframeSelection, tuple[Timeframe, ...]]:
    legacy = to_price_structure_evidence_packet(packet)
    reference = reference_select_price_structure(legacy)
    values: dict[Timeframe, TimeframeSelection] = {}
    fallback: list[Timeframe] = []
    for timeframe in TIMEFRAME_ORDER:
        reference_value: TimeframeSelection = getattr(reference, timeframe)
        selected = getattr(output, timeframe) if output is not None else None
        if selected is None or validation.timeframe_status[timeframe] != "PASS":
            fallback.append(timeframe)
            values[timeframe] = reference_value.model_copy(
                update={
                    "fib_mode": "NONE",
                    "low_pivot_id": None,
                    "high_pivot_id": None,
                    "correction_low_pivot_id": None,
                    "evidence_refs": tuple(
                        ref
                        for ref in (
                            reference_value.support_zone_id,
                            reference_value.resistance_zone_id,
                        )
                        if ref is not None
                    ),
                    "concise_reason": "variable AI unavailable; deterministic SR preserved",
                }
            )
            continue
        evidence: TimeframeAnchorEvidence = getattr(packet, timeframe)
        pivots = {item.pivot_id: item for item in evidence.pivots}
        low = pivots.get(selected.low_pivot_id or "")
        high = pivots.get(selected.high_pivot_id or "")
        correction = pivots.get(selected.correction_low_pivot_id or "")
        values[timeframe] = TimeframeSelection(
            status="SELECTED",
            support_zone_id=selected.support_zone_id,
            resistance_zone_id=selected.resistance_zone_id,
            fib_mode=selected.fib_mode,
            low_pivot_id=selected.low_pivot_id,
            high_pivot_id=selected.high_pivot_id,
            correction_low_pivot_id=selected.correction_low_pivot_id,
            regime=_regime(packet.current_price, low, high, correction),  # type: ignore[arg-type]
            confidence=selected.confidence.casefold(),  # type: ignore[arg-type]
            evidence_refs=selected.evidence_refs,
            concise_reason=selected.concise_reason,
        )
    return (
        MultiTimeframeSelection(
            selection_source="approved_variable_ai_id_selection",
            monthly=values["monthly"],
            weekly=values["weekly"],
            daily=values["daily"],
            synthesis=SynthesisSelection(
                timeframe_agreement=reference.synthesis.timeframe_agreement,
                concise_summary="validated variable IDs with per-timeframe deterministic SR fallback",
            ),
        ),
        tuple(fallback),
    )


def execute_variable_anchor_selector(
    packet: PriceOnlyAIAnchorPacket,
    selector: Callable[[dict[str, object]], object],
) -> VariableAnchorExecutionResult:
    audit = audit_price_only_evidence_egress(packet)
    if audit["status"] != "PASS":
        raw_output: object = ValueError("price_only_egress_failed")
    else:
        try:
            raw_output = selector(packet.model_dump(mode="json"))
        except (TimeoutError, ConnectionError, RuntimeError, ValueError, TypeError) as exc:
            raw_output = exc
    output: VariableAIAnchorOutput | None = None
    failure_reason: str | None = None
    if isinstance(raw_output, Exception):
        failure_reason = type(raw_output).__name__
    else:
        try:
            if isinstance(raw_output, str):
                raw_output = json.loads(raw_output)
            output = VariableAIAnchorOutput.model_validate(raw_output)
        except (ValidationError, json.JSONDecodeError, TypeError, ValueError) as exc:
            failure_reason = type(exc).__name__
    if output is None:
        validation = VariableAnchorValidation(
            valid=False,
            errors=(f"runtime:{failure_reason or 'unavailable'}",),
            timeframe_status={timeframe: "REJECTED" for timeframe in TIMEFRAME_ORDER},
        )
    else:
        validation = validate_variable_ai_anchor_output(packet, output)
        if not validation.valid:
            failure_reason = "invalid_anchor_output"
    selection, fallback = _selection_with_fallback(packet, output, validation)
    shadow = build_shadow_price_structure_result(
        to_price_structure_evidence_packet(packet), selection
    )
    return VariableAnchorExecutionResult(
        status="PASS" if output is not None and validation.valid else "FAIL_CLOSED",
        failure_reason=failure_reason,
        output=output,
        validation=validation,
        selection=selection,
        shadow=shadow,
        fallback_timeframes=fallback,
    )


def _frequency(values: Sequence[str | None]) -> dict[str, int]:
    return dict(sorted(Counter(value or "NONE" for value in values).items()))


def _zone_equivalent(
    evidence: TimeframeAnchorEvidence,
    first_ref: str | None,
    second_ref: str | None,
) -> bool:
    if first_ref == second_ref:
        return True
    if first_ref is None or second_ref is None:
        return False
    zones = {item.zone_id: item for item in evidence.sr_candidates}
    first = zones.get(first_ref)
    second = zones.get(second_ref)
    if first is None or second is None or first.role != second.role:
        return False
    reference = (first.center + second.center) / 2
    tolerance = Decimal(str(LOCAL_CONFIG[evidence.timeframe].merge_pct))
    return abs(first.center - second.center) <= reference * tolerance


def _visible_fib_equivalent(
    timeframe: Timeframe,
    first: ShadowPriceStructureResult,
    second: ShadowPriceStructureResult,
) -> bool:
    left = sorted(item.calculated_price for item in first.selected_fibonacci[timeframe])
    right = sorted(item.calculated_price for item in second.selected_fibonacci[timeframe])
    if len(left) != len(right):
        return False
    tolerance = Decimal(str(LOCAL_CONFIG[timeframe].merge_pct))
    return all(
        abs(a - b) <= ((a + b) / 2) * tolerance
        for a, b in zip(left, right)
    )


def _timeframe_stability(
    packet: PriceOnlyAIAnchorPacket,
    timeframe: Timeframe,
    runs: Sequence[VariableAnchorExecutionResult],
) -> TimeframeStability:
    selections = [getattr(run.selection, timeframe) for run in runs]
    signatures = [
        (
            item.support_zone_id,
            item.resistance_zone_id,
            item.fib_mode,
            item.low_pivot_id,
            item.high_pivot_id,
            item.correction_low_pivot_id,
            item.regime,
        )
        for item in selections
    ]
    exact_count = max(Counter(signatures).values(), default=0)
    exact = bool(signatures and exact_count == len(signatures))
    evidence: TimeframeAnchorEvidence = getattr(packet, timeframe)
    equivalent = bool(runs)
    for index, first in enumerate(runs):
        for second in runs[index + 1 :]:
            left = getattr(first.selection, timeframe)
            right = getattr(second.selection, timeframe)
            equivalent = equivalent and left.regime == right.regime
            equivalent = equivalent and _zone_equivalent(
                evidence, left.support_zone_id, right.support_zone_id
            )
            equivalent = equivalent and _zone_equivalent(
                evidence, left.resistance_zone_id, right.resistance_zone_id
            )
            equivalent = equivalent and _visible_fib_equivalent(
                timeframe, first.shadow, second.shadow
            )
    classification = (
        StabilityClass.STABLE
        if exact
        else StabilityClass.MINOR_VARIATION
        if equivalent
        else StabilityClass.MATERIAL_VARIATION
    )
    return TimeframeStability(
        timeframe=timeframe,
        classification=classification,
        run_count=len(runs),
        exact_signature_count=exact_count,
        low_anchor_frequency=_frequency([item.low_pivot_id for item in selections]),
        high_anchor_frequency=_frequency([item.high_pivot_id for item in selections]),
        correction_anchor_frequency=_frequency(
            [item.correction_low_pivot_id for item in selections]
        ),
        fib_mode_frequency=_frequency([item.fib_mode for item in selections]),
        support_zone_frequency=_frequency([item.support_zone_id for item in selections]),
        resistance_zone_frequency=_frequency([item.resistance_zone_id for item in selections]),
        structure_equivalent=equivalent,
    )


def classify_anchor_stability(
    packet: PriceOnlyAIAnchorPacket,
    runs: Sequence[VariableAnchorExecutionResult],
) -> StockStabilityDecision:
    values = {
        timeframe: _timeframe_stability(packet, timeframe, runs)
        for timeframe in TIMEFRAME_ORDER
    }
    higher_stable = all(
        values[timeframe].classification != StabilityClass.MATERIAL_VARIATION
        for timeframe in ("monthly", "weekly")
    )
    fallbacks = tuple(
        timeframe
        for timeframe in TIMEFRAME_ORDER
        if values[timeframe].classification == StabilityClass.MATERIAL_VARIATION
    )
    return StockStabilityDecision(
        ticker=packet.ticker,
        monthly=values["monthly"],
        weekly=values["weekly"],
        daily=values["daily"],
        user_visible_eligible=higher_stable,
        timeframe_fib_fallbacks=fallbacks,
    )
