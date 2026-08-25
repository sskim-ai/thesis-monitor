from __future__ import annotations

import hashlib
import json
from decimal import Decimal, ROUND_HALF_UP
from typing import Literal, Mapping, Sequence

from pydantic import BaseModel, ConfigDict, Field

from app.services.ohlcv_structure_service import LOCAL_CONFIG, Timeframe


CONTRACT_VERSION = "multi-timeframe-price-structure-shadow-v2"
FIBONACCI_CALCULATION_VERSION = "deterministic-fibonacci-v2"
TIMEFRAME_ORDER: tuple[Timeframe, ...] = ("monthly", "weekly", "daily")
TIMEFRAME_ROLES: dict[Timeframe, str] = {
    "monthly": "PRIMARY_STRUCTURAL_ZONE",
    "weekly": "INTERMEDIATE_ZONE",
    "daily": "NEAREST_TACTICAL_ZONE",
}

FibMode = Literal["RETRACEMENT", "EXTENSION", "BOTH", "NONE"]
SelectionStatus = Literal["SELECTED", "INSUFFICIENT_STRUCTURE"]
Agreement = Literal["ALIGNED", "MIXED", "CONFLICTING", "INSUFFICIENT"]
Regime = Literal[
    "UPTREND_PULLBACK_HELD",
    "ABOVE_CONFIRMED_SWING_HIGH",
    "RETRACEMENT_WITHIN_CONFIRMED_SWING",
    "BELOW_CONFIRMED_SWING_LOW",
    "RANGE_OR_INSUFFICIENT",
    "INSUFFICIENT",
]


class FrozenModel(BaseModel):
    model_config = ConfigDict(frozen=True)


class PivotEvidence(FrozenModel):
    pivot_id: str
    ticker: str
    timeframe: Timeframe
    kind: Literal["low", "high"]
    date: str
    confirmed_at: str
    price: Decimal
    adjustment_basis: str
    source_ref: str


class ZoneEvidence(FrozenModel):
    zone_id: str
    ticker: str
    timeframe: Timeframe
    role: Literal["SUPPORT", "RESISTANCE", "ACTIVE"]
    low: Decimal
    high: Decimal
    center: Decimal
    strength: str
    score: int
    source_pivot_dates: tuple[str, ...] = ()
    source_pivot_prices: tuple[Decimal, ...] = ()
    distance_pct: Decimal | None = None
    relation_to_current: Literal["BELOW", "ABOVE", "INSIDE"]


class TimeframeEvidence(FrozenModel):
    timeframe: Timeframe
    analytical_role: str
    status: Literal["AVAILABLE", "INSUFFICIENT_STRUCTURE"]
    as_of: str | None
    pivots: tuple[PivotEvidence, ...] = ()
    sr_candidates: tuple[ZoneEvidence, ...] = ()
    omitted_candidate_count: int = 0


class PriceStructureEvidencePacket(FrozenModel):
    contract: str = CONTRACT_VERSION
    ticker: str
    security_id: str
    currency: str
    current_price: Decimal
    as_of: str
    cutoff: str
    adjustment_basis: str
    evidence_mode: Literal["COMPACT", "FULL_DEBUG"]
    evidence_sha256: str
    monthly: TimeframeEvidence
    weekly: TimeframeEvidence
    daily: TimeframeEvidence


class TimeframeSelection(FrozenModel):
    status: SelectionStatus
    support_zone_id: str | None = None
    resistance_zone_id: str | None = None
    fib_mode: FibMode = "NONE"
    low_pivot_id: str | None = None
    high_pivot_id: str | None = None
    correction_low_pivot_id: str | None = None
    regime: Regime = "INSUFFICIENT"
    confidence: Literal["high", "medium", "low"] = "low"
    evidence_refs: tuple[str, ...] = ()
    concise_reason: str = ""


class SynthesisSelection(FrozenModel):
    primary_structural_timeframe: Literal["monthly"] = "monthly"
    intermediate_timeframe: Literal["weekly"] = "weekly"
    tactical_timeframe: Literal["daily"] = "daily"
    nearest_support_ref: str | None = None
    nearest_resistance_ref: str | None = None
    strongest_support_confluence_refs: tuple[str, ...] = ()
    strongest_resistance_confluence_refs: tuple[str, ...] = ()
    timeframe_agreement: Agreement = "INSUFFICIENT"
    concise_summary: str = ""


class MultiTimeframeSelection(FrozenModel):
    contract: str = CONTRACT_VERSION
    selection_source: str
    monthly: TimeframeSelection
    weekly: TimeframeSelection
    daily: TimeframeSelection
    synthesis: SynthesisSelection = Field(default_factory=SynthesisSelection)


class ValidationResult(FrozenModel):
    valid: bool
    errors: tuple[str, ...] = ()
    timeframe_status: dict[Timeframe, Literal["PASS", "REJECTED", "NOT_APPLICABLE"]]


class FibonacciLevel(FrozenModel):
    level_id: str
    ticker: str
    timeframe: Timeframe
    ratio: str
    mode: Literal["RETRACEMENT", "EXTENSION"]
    calculated_price: Decimal
    currency: str
    adjustment_basis: str
    as_of: str
    low_anchor_ref: str
    high_anchor_ref: str
    correction_anchor_ref: str | None = None
    formula: str
    calculation_version: str = FIBONACCI_CALCULATION_VERSION
    rounding: str = "0.000001_half_up"


class ConfluenceContributor(FrozenModel):
    ref_id: str
    timeframe: Timeframe
    kind: Literal["SUPPORT", "RESISTANCE", "ACTIVE", "FIBONACCI"]
    price: Decimal


class PriceConfluence(FrozenModel):
    confluence_id: str
    contributors: tuple[ConfluenceContributor, ...]
    timeframes: tuple[Timeframe, ...]
    zone_low: Decimal
    zone_high: Decimal
    tolerance_method: str
    tolerance_pct: Decimal
    current_price_relation: Literal["BELOW", "ABOVE", "INSIDE"]
    distance_pct: Decimal


class ShadowPriceStructureResult(FrozenModel):
    contract: str = CONTRACT_VERSION
    evidence: PriceStructureEvidencePacket
    selection: MultiTimeframeSelection
    validation: ValidationResult
    fibonacci: dict[Timeframe, tuple[FibonacciLevel, ...]]
    selected_fibonacci: dict[Timeframe, tuple[FibonacciLevel, ...]]
    confluence: tuple[PriceConfluence, ...]
    shadow_render: str
    user_visible: bool = False
    official_assessment_mutation: bool = False


def _decimal(value: object) -> Decimal:
    return Decimal(str(value))


def _rounded(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)


def _stable_id(prefix: str, *parts: object) -> str:
    material = "|".join(str(part) for part in parts)
    digest = hashlib.sha256(material.encode("utf-8")).hexdigest()[:20]
    return f"{prefix}:{digest}"


def _canonical_hash(value: object) -> str:
    payload = json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _timeframe_value(packet: PriceStructureEvidencePacket, timeframe: Timeframe) -> TimeframeEvidence:
    return getattr(packet, timeframe)


def _relation(low: Decimal, high: Decimal, current: Decimal) -> Literal["BELOW", "ABOVE", "INSIDE"]:
    if high < current:
        return "BELOW"
    if low > current:
        return "ABOVE"
    return "INSIDE"


def _zone_role(
    pivot_type: object,
    low: Decimal,
    high: Decimal,
    current: Decimal,
) -> Literal["SUPPORT", "RESISTANCE", "ACTIVE"]:
    relation = _relation(low, high, current)
    if relation == "INSIDE":
        return "ACTIVE"
    if str(pivot_type) == "low" or relation == "BELOW":
        return "SUPPORT"
    return "RESISTANCE"


def _distance_pct(low: Decimal, high: Decimal, current: Decimal) -> Decimal:
    relation = _relation(low, high, current)
    if relation == "BELOW":
        return _rounded((current - high) / current * Decimal(100))
    if relation == "ABOVE":
        return _rounded((low - current) / current * Decimal(100))
    return Decimal(0)


def _pivot_evidence(
    ticker: str,
    timeframe: Timeframe,
    adjustment_basis: str,
    value: Mapping[str, object],
) -> PivotEvidence | None:
    if value.get("kind") not in {"low", "high"}:
        return None
    if value.get("date") is None or value.get("confirmed_at") is None or value.get("price") is None:
        return None
    price = _decimal(value["price"])
    date = str(value["date"])
    confirmed_at = str(value["confirmed_at"])
    kind = str(value["kind"])
    return PivotEvidence(
        pivot_id=_stable_id(
            "price-pivot",
            ticker,
            timeframe,
            kind,
            date,
            confirmed_at,
            price,
            adjustment_basis,
        ),
        ticker=ticker,
        timeframe=timeframe,
        kind=kind,  # type: ignore[arg-type]
        date=date,
        confirmed_at=confirmed_at,
        price=price,
        adjustment_basis=adjustment_basis,
        source_ref=f"ohlcv-structure-v2:major_swing:{timeframe}:{date}:{kind}",
    )


def _zone_evidence(
    ticker: str,
    timeframe: Timeframe,
    current_price: Decimal,
    value: Mapping[str, object],
) -> ZoneEvidence | None:
    required = ("zone_low", "zone_high", "center")
    if any(value.get(key) is None for key in required):
        return None
    low = _decimal(value["zone_low"])
    high = _decimal(value["zone_high"])
    center = _decimal(value["center"])
    if low > high or not (low <= center <= high):
        return None
    role = _zone_role(value.get("pivot_type"), low, high, current_price)
    pivot_dates = tuple(str(item) for item in value.get("pivot_dates") or ())
    pivot_prices = tuple(_decimal(item) for item in value.get("pivot_prices") or ())
    zone_id = _stable_id(
        "price-zone",
        ticker,
        timeframe,
        role,
        low,
        high,
        ",".join(pivot_dates),
    )
    return ZoneEvidence(
        zone_id=zone_id,
        ticker=ticker,
        timeframe=timeframe,
        role=role,
        low=low,
        high=high,
        center=center,
        strength=str(value.get("strength") or "Weak"),
        score=int(value.get("score") or 0),
        source_pivot_dates=pivot_dates,
        source_pivot_prices=pivot_prices,
        distance_pct=_distance_pct(low, high, current_price),
        relation_to_current=_relation(low, high, current_price),
    )


def build_price_structure_evidence_packet(
    *,
    ticker: str,
    security_id: str,
    currency: str,
    current_price: object,
    structure: Mapping[str, object],
    cutoff: str,
    compact: bool = True,
) -> PriceStructureEvidencePacket:
    price = _decimal(current_price)
    if price <= 0:
        raise ValueError("current_price must be positive")
    as_of = str(structure.get("as_of_date") or "")
    if not as_of:
        raise ValueError("structure as_of_date is required")
    adjustment_basis = str(structure.get("price_basis") or "")
    if not adjustment_basis:
        raise ValueError("adjustment basis is required")
    all_zones = structure.get("all_zones")
    major = structure.get("major_swings")
    zones = all_zones if isinstance(all_zones, Sequence) else ()
    by_timeframe = major.get("by_timeframe") if isinstance(major, Mapping) else {}
    timeframe_values: dict[Timeframe, TimeframeEvidence] = {}
    for timeframe in TIMEFRAME_ORDER:
        raw_pivots = (
            by_timeframe.get(timeframe, ()) if isinstance(by_timeframe, Mapping) else ()
        )
        pivots = tuple(
            pivot
            for item in raw_pivots
            if isinstance(item, Mapping)
            and (pivot := _pivot_evidence(ticker, timeframe, adjustment_basis, item))
            is not None
            and pivot.date <= cutoff
            and pivot.confirmed_at <= cutoff
        )
        candidates = tuple(
            zone
            for item in zones
            if isinstance(item, Mapping)
            and item.get("timeframe") == timeframe
            and (zone := _zone_evidence(ticker, timeframe, price, item)) is not None
        )
        if compact:
            selected_candidates = tuple(
                zone for zone in candidates if zone.strength in {"Strong", "Medium"}
            )
        else:
            selected_candidates = candidates
        meaningful_zone_exists = any(
            zone.strength in {"Strong", "Medium"} for zone in candidates
        )
        status = (
            "AVAILABLE"
            if meaningful_zone_exists or len(pivots) >= 2
            else "INSUFFICIENT_STRUCTURE"
        )
        timeframe_values[timeframe] = TimeframeEvidence(
            timeframe=timeframe,
            analytical_role=TIMEFRAME_ROLES[timeframe],
            status=status,
            as_of=as_of,
            pivots=pivots,
            sr_candidates=selected_candidates,
            omitted_candidate_count=len(candidates) - len(selected_candidates),
        )
    hash_material = {
        "contract": CONTRACT_VERSION,
        "ticker": ticker,
        "security_id": security_id,
        "currency": currency,
        "current_price": str(price),
        "as_of": as_of,
        "cutoff": cutoff,
        "adjustment_basis": adjustment_basis,
        "evidence_mode": "COMPACT" if compact else "FULL_DEBUG",
        **{
            timeframe: timeframe_values[timeframe].model_dump(mode="json")
            for timeframe in TIMEFRAME_ORDER
        },
    }
    return PriceStructureEvidencePacket(
        ticker=ticker,
        security_id=security_id,
        currency=currency,
        current_price=price,
        as_of=as_of,
        cutoff=cutoff,
        adjustment_basis=adjustment_basis,
        evidence_mode="COMPACT" if compact else "FULL_DEBUG",
        evidence_sha256=_canonical_hash(hash_material),
        monthly=timeframe_values["monthly"],
        weekly=timeframe_values["weekly"],
        daily=timeframe_values["daily"],
    )


def _select_zone(
    evidence: TimeframeEvidence,
    role: Literal["SUPPORT", "RESISTANCE"],
) -> ZoneEvidence | None:
    candidates = [
        zone
        for zone in evidence.sr_candidates
        if zone.role == role or (role == "SUPPORT" and zone.role == "ACTIVE")
        if zone.strength in {"Strong", "Medium"}
    ]
    if not candidates:
        return None
    if evidence.timeframe == "daily":
        return min(candidates, key=lambda item: (item.distance_pct or Decimal(0), -item.score))
    return max(
        candidates,
        key=lambda item: (
            {"Strong": 2, "Medium": 1}.get(item.strength, 0),
            item.score,
            -(item.distance_pct or Decimal(0)),
        ),
    )


def _select_anchor_sequence(
    evidence: TimeframeEvidence,
) -> tuple[PivotEvidence | None, PivotEvidence | None, PivotEvidence | None]:
    pairs = [
        (low, high)
        for low in evidence.pivots
        if low.kind == "low"
        for high in evidence.pivots
        if high.kind == "high" and high.date > low.date and high.price > low.price
    ]
    if not pairs:
        return None, None, None
    if evidence.timeframe == "monthly":
        low, high = max(pairs, key=lambda pair: (pair[1].price - pair[0].price, pair[1].date))
    else:
        low, high = max(pairs, key=lambda pair: (pair[1].date, pair[0].date))
    corrections = [
        pivot
        for pivot in evidence.pivots
        if pivot.kind == "low" and pivot.date > high.date and pivot.price > low.price
    ]
    correction = corrections[-1] if corrections else None
    return low, high, correction


def _regime(
    evidence: TimeframeEvidence,
    current_price: Decimal,
    low: PivotEvidence | None,
    high: PivotEvidence | None,
    correction: PivotEvidence | None,
) -> Regime:
    if low is None or high is None:
        return "RANGE_OR_INSUFFICIENT"
    if correction is not None and current_price >= correction.price:
        return "UPTREND_PULLBACK_HELD"
    if current_price > high.price:
        return "ABOVE_CONFIRMED_SWING_HIGH"
    if low.price <= current_price <= high.price:
        return "RETRACEMENT_WITHIN_CONFIRMED_SWING"
    return "BELOW_CONFIRMED_SWING_LOW"


def reference_select_price_structure(
    packet: PriceStructureEvidencePacket,
    *,
    selection_source: str = "codex_archive_shadow_reference",
) -> MultiTimeframeSelection:
    values: dict[Timeframe, TimeframeSelection] = {}
    for timeframe in TIMEFRAME_ORDER:
        evidence = _timeframe_value(packet, timeframe)
        support = _select_zone(evidence, "SUPPORT")
        resistance = _select_zone(evidence, "RESISTANCE")
        low, high, correction = _select_anchor_sequence(evidence)
        if evidence.status == "INSUFFICIENT_STRUCTURE" and not any(
            (support, resistance, low, high)
        ):
            values[timeframe] = TimeframeSelection(
                status="INSUFFICIENT_STRUCTURE",
                concise_reason="confirmed timeframe evidence is insufficient",
            )
            continue
        fib_mode: FibMode = "NONE"
        if low is not None and high is not None:
            fib_mode = "BOTH" if correction is not None else "RETRACEMENT"
        refs = tuple(
            item
            for item in (
                support.zone_id if support else None,
                resistance.zone_id if resistance else None,
                low.pivot_id if low else None,
                high.pivot_id if high else None,
                correction.pivot_id if correction else None,
            )
            if item is not None
        )
        values[timeframe] = TimeframeSelection(
            status="SELECTED",
            support_zone_id=support.zone_id if support else None,
            resistance_zone_id=resistance.zone_id if resistance else None,
            fib_mode=fib_mode,
            low_pivot_id=low.pivot_id if low else None,
            high_pivot_id=high.pivot_id if high else None,
            correction_low_pivot_id=correction.pivot_id if correction else None,
            regime=_regime(evidence, packet.current_price, low, high, correction),
            confidence=(
                "high"
                if support is not None and resistance is not None and fib_mode != "NONE"
                else "medium"
                if any((support, resistance, fib_mode != "NONE"))
                else "low"
            ),
            evidence_refs=refs,
            concise_reason=f"{TIMEFRAME_ROLES[timeframe]} evidence selected by canonical IDs",
        )
    selected_zones = {
        zone.zone_id: zone
        for timeframe in TIMEFRAME_ORDER
        for zone in _timeframe_value(packet, timeframe).sr_candidates
    }
    support_refs = [
        value.support_zone_id
        for value in values.values()
        if value.support_zone_id in selected_zones
    ]
    resistance_refs = [
        value.resistance_zone_id
        for value in values.values()
        if value.resistance_zone_id in selected_zones
    ]
    nearest_support = min(
        support_refs,
        key=lambda ref: selected_zones[ref].distance_pct or Decimal(0),
        default=None,
    )
    nearest_resistance = min(
        resistance_refs,
        key=lambda ref: selected_zones[ref].distance_pct or Decimal(0),
        default=None,
    )
    direction = {
        "up"
        if "UPTREND" in value.regime or value.regime.startswith("ABOVE")
        else "down"
        if value.regime.startswith("BELOW")
        else "neutral"
        for value in values.values()
        if value.status == "SELECTED"
    }
    agreement: Agreement = (
        "INSUFFICIENT"
        if not direction
        else "CONFLICTING"
        if {"up", "down"}.issubset(direction)
        else "ALIGNED"
        if len(direction) == 1
        else "MIXED"
    )
    synthesis = SynthesisSelection(
        nearest_support_ref=nearest_support,
        nearest_resistance_ref=nearest_resistance,
        timeframe_agreement=agreement,
        concise_summary="monthly structural, weekly intermediate, daily tactical hierarchy preserved",
    )
    return MultiTimeframeSelection(
        selection_source=selection_source,
        monthly=values["monthly"],
        weekly=values["weekly"],
        daily=values["daily"],
        synthesis=synthesis,
    )


def validate_price_structure_selection(
    packet: PriceStructureEvidencePacket,
    selection: MultiTimeframeSelection,
) -> ValidationResult:
    errors: list[str] = []
    statuses: dict[Timeframe, Literal["PASS", "REJECTED", "NOT_APPLICABLE"]] = {}
    for timeframe in TIMEFRAME_ORDER:
        evidence = _timeframe_value(packet, timeframe)
        selected: TimeframeSelection = getattr(selection, timeframe)
        if selected.status == "INSUFFICIENT_STRUCTURE":
            if evidence.status == "AVAILABLE":
                errors.append(f"{timeframe}:available_evidence_not_analyzed")
                statuses[timeframe] = "REJECTED"
                continue
            statuses[timeframe] = "NOT_APPLICABLE"
            continue
        if evidence.status == "INSUFFICIENT_STRUCTURE":
            errors.append(f"{timeframe}:insufficient_evidence_selected")
            statuses[timeframe] = "REJECTED"
            continue
        zones = {item.zone_id: item for item in evidence.sr_candidates}
        pivots = {item.pivot_id: item for item in evidence.pivots}
        timeframe_errors: list[str] = []
        for field_name in ("support_zone_id", "resistance_zone_id"):
            ref = getattr(selected, field_name)
            if ref is not None and ref not in zones:
                timeframe_errors.append(f"{timeframe}:{field_name}:unknown_or_cross_timeframe_ref")
        support_zone = zones.get(selected.support_zone_id or "")
        resistance_zone = zones.get(selected.resistance_zone_id or "")
        if support_zone is not None and support_zone.role not in {"SUPPORT", "ACTIVE"}:
            timeframe_errors.append(f"{timeframe}:support_zone_role_invalid")
        if resistance_zone is not None and resistance_zone.role != "RESISTANCE":
            timeframe_errors.append(f"{timeframe}:resistance_zone_role_invalid")
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
            elif high is not None and not (
                correction.kind == "low"
                and correction.date > high.date
                and low is not None
                and correction.price > low.price
            ):
                timeframe_errors.append(f"{timeframe}:extension_correction_invalid")
        valid_refs = {*zones, *pivots}
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
        if any(
            pivot.date > packet.cutoff or pivot.confirmed_at > packet.cutoff
            for pivot in pivots.values()
        ):
            timeframe_errors.append(f"{timeframe}:lookahead_pivot")
        errors.extend(timeframe_errors)
        statuses[timeframe] = "REJECTED" if timeframe_errors else "PASS"
    return ValidationResult(valid=not errors, errors=tuple(errors), timeframe_status=statuses)


def calculate_timeframe_fibonacci(
    packet: PriceStructureEvidencePacket,
    selection: MultiTimeframeSelection,
) -> dict[Timeframe, tuple[FibonacciLevel, ...]]:
    validation = validate_price_structure_selection(packet, selection)
    result: dict[Timeframe, tuple[FibonacciLevel, ...]] = {}
    for timeframe in TIMEFRAME_ORDER:
        if validation.timeframe_status[timeframe] != "PASS":
            result[timeframe] = ()
            continue
        evidence = _timeframe_value(packet, timeframe)
        selected: TimeframeSelection = getattr(selection, timeframe)
        pivots = {item.pivot_id: item for item in evidence.pivots}
        low = pivots.get(selected.low_pivot_id or "")
        high = pivots.get(selected.high_pivot_id or "")
        correction = pivots.get(selected.correction_low_pivot_id or "")
        if selected.fib_mode == "NONE" or low is None or high is None:
            result[timeframe] = ()
            continue
        price_range = high.price - low.price
        levels: list[FibonacciLevel] = []
        if selected.fib_mode in {"RETRACEMENT", "BOTH"}:
            for ratio in (Decimal("0.382"), Decimal("0.500"), Decimal("0.618")):
                value = _rounded(high.price - price_range * ratio)
                levels.append(
                    FibonacciLevel(
                        level_id=_stable_id(
                            "price-fib",
                            packet.ticker,
                            timeframe,
                            "RETRACEMENT",
                            ratio,
                            low.pivot_id,
                            high.pivot_id,
                            value,
                        ),
                        ticker=packet.ticker,
                        timeframe=timeframe,
                        ratio=f"{ratio:.3f}",
                        mode="RETRACEMENT",
                        calculated_price=value,
                        currency=packet.currency,
                        adjustment_basis=packet.adjustment_basis,
                        as_of=packet.as_of,
                        low_anchor_ref=low.pivot_id,
                        high_anchor_ref=high.pivot_id,
                        formula="H - (H-L) * ratio",
                    )
                )
        if selected.fib_mode in {"EXTENSION", "BOTH"} and correction is not None:
            for ratio in (
                Decimal("0.618"),
                Decimal("1.000"),
                Decimal("1.618"),
                Decimal("2.618"),
            ):
                value = _rounded(correction.price + price_range * ratio)
                levels.append(
                    FibonacciLevel(
                        level_id=_stable_id(
                            "price-fib",
                            packet.ticker,
                            timeframe,
                            "EXTENSION",
                            ratio,
                            low.pivot_id,
                            high.pivot_id,
                            correction.pivot_id,
                            value,
                        ),
                        ticker=packet.ticker,
                        timeframe=timeframe,
                        ratio=f"{ratio:.3f}",
                        mode="EXTENSION",
                        calculated_price=value,
                        currency=packet.currency,
                        adjustment_basis=packet.adjustment_basis,
                        as_of=packet.as_of,
                        low_anchor_ref=low.pivot_id,
                        high_anchor_ref=high.pivot_id,
                        correction_anchor_ref=correction.pivot_id,
                        formula="C + (H-L) * ratio",
                    )
                )
        result[timeframe] = tuple(levels)
    return result


def select_relevant_fibonacci_levels(
    levels: Mapping[Timeframe, Sequence[FibonacciLevel]],
    current_price: Decimal,
    *,
    packet: PriceStructureEvidencePacket | None = None,
    selection: MultiTimeframeSelection | None = None,
    confluence: Sequence[PriceConfluence] = (),
    limit: int = 2,
) -> dict[Timeframe, tuple[FibonacciLevel, ...]]:
    confluence_refs = {
        contributor.ref_id
        for item in confluence
        for contributor in item.contributors
        if contributor.kind == "FIBONACCI"
    }
    selected: dict[Timeframe, tuple[FibonacciLevel, ...]] = {}
    for timeframe in TIMEFRAME_ORDER:
        candidates = list(levels.get(timeframe, ()))
        if packet is not None and selection is not None:
            evidence = _timeframe_value(packet, timeframe)
            timeframe_selection: TimeframeSelection = getattr(selection, timeframe)
            zone_refs = {
                ref
                for ref in (
                    timeframe_selection.support_zone_id,
                    timeframe_selection.resistance_zone_id,
                )
                if ref is not None
            }
            zones = [item for item in evidence.sr_candidates if item.zone_id in zone_refs]
            tolerance = Decimal(str(LOCAL_CONFIG[timeframe].merge_pct))
            candidates = [
                item
                for item in candidates
                if item.level_id in confluence_refs
                or abs(item.calculated_price - current_price) <= current_price * tolerance
                or any(
                    zone.low <= item.calculated_price <= zone.high
                    or abs(item.calculated_price - zone.center) <= zone.center * tolerance
                    for zone in zones
                )
            ]
        selected[timeframe] = tuple(
            sorted(
                candidates,
                key=lambda item: (
                    abs(item.calculated_price - current_price),
                    item.mode,
                    item.ratio,
                ),
            )[:limit]
        )
    return selected


def _contributors(
    packet: PriceStructureEvidencePacket,
    selection: MultiTimeframeSelection,
    selected_fibonacci: Mapping[Timeframe, Sequence[FibonacciLevel]],
) -> list[ConfluenceContributor]:
    values: list[ConfluenceContributor] = []
    for timeframe in TIMEFRAME_ORDER:
        evidence = _timeframe_value(packet, timeframe)
        selected: TimeframeSelection = getattr(selection, timeframe)
        zones = {item.zone_id: item for item in evidence.sr_candidates}
        for ref in (selected.support_zone_id, selected.resistance_zone_id):
            zone = zones.get(ref or "")
            if zone is not None:
                values.append(
                    ConfluenceContributor(
                        ref_id=zone.zone_id,
                        timeframe=timeframe,
                        kind=zone.role,
                        price=zone.center,
                    )
                )
        values.extend(
            ConfluenceContributor(
                ref_id=level.level_id,
                timeframe=timeframe,
                kind="FIBONACCI",
                price=level.calculated_price,
            )
            for level in selected_fibonacci.get(timeframe, ())
        )
    return values


def _pair_compatible(first: ConfluenceContributor, second: ConfluenceContributor) -> bool:
    if first.timeframe == second.timeframe:
        return False
    reference = (first.price + second.price) / Decimal(2)
    tolerance = Decimal(
        str(min(LOCAL_CONFIG[first.timeframe].merge_pct, LOCAL_CONFIG[second.timeframe].merge_pct))
    )
    return abs(first.price - second.price) <= reference * tolerance


def calculate_multi_timeframe_confluence(
    packet: PriceStructureEvidencePacket,
    selection: MultiTimeframeSelection,
    selected_fibonacci: Mapping[Timeframe, Sequence[FibonacciLevel]],
) -> tuple[PriceConfluence, ...]:
    candidates = _contributors(packet, selection, selected_fibonacci)
    clusters: list[list[ConfluenceContributor]] = []
    for contributor in sorted(candidates, key=lambda item: (item.price, item.ref_id)):
        matching = next(
            (
                cluster
                for cluster in clusters
                if all(_pair_compatible(contributor, member) for member in cluster)
            ),
            None,
        )
        if matching is None:
            clusters.append([contributor])
        else:
            matching.append(contributor)
    output: list[PriceConfluence] = []
    for cluster in clusters:
        timeframes = tuple(
            timeframe for timeframe in TIMEFRAME_ORDER if any(x.timeframe == timeframe for x in cluster)
        )
        if len(timeframes) < 2:
            continue
        prices = [item.price for item in cluster]
        low = min(prices)
        high = max(prices)
        tolerance = min(Decimal(str(LOCAL_CONFIG[item.timeframe].merge_pct)) for item in cluster)
        relation = _relation(low, high, packet.current_price)
        output.append(
            PriceConfluence(
                confluence_id=_stable_id(
                    "price-confluence", packet.ticker, *sorted(item.ref_id for item in cluster)
                ),
                contributors=tuple(cluster),
                timeframes=timeframes,
                zone_low=low,
                zone_high=high,
                tolerance_method="complete_link_min_timeframe_merge_pct",
                tolerance_pct=tolerance,
                current_price_relation=relation,
                distance_pct=_distance_pct(low, high, packet.current_price),
            )
        )
    return tuple(sorted(output, key=lambda item: (-len(item.timeframes), item.distance_pct)))


def _zone_text(zone: ZoneEvidence | None) -> str | None:
    if zone is None:
        return None
    labels = {"SUPPORT": "지지", "RESISTANCE": "저항", "ACTIVE": "현재 구간"}
    return f"{labels[zone.role]} {zone.low}-{zone.high}"


def _format_price(value: Decimal) -> str:
    return format(value.normalize(), "f")


def _regime_text(regime: str) -> str:
    return {
        "UPTREND_PULLBACK_HELD": "상승 구조의 조정 저점 유지",
        "ABOVE_CONFIRMED_SWING_HIGH": "확정 스윙 고점 상회",
        "RETRACEMENT_WITHIN_CONFIRMED_SWING": "확정 스윙 범위 안의 되돌림",
        "BELOW_CONFIRMED_SWING_LOW": "확정 스윙 저점 하회",
        "RANGE_OR_INSUFFICIENT": "방향 판단 근거 제한",
        "INSUFFICIENT": "구조 근거 부족",
    }.get(regime, regime)


def render_shadow_price_structure(
    packet: PriceStructureEvidencePacket,
    selection: MultiTimeframeSelection,
    selected_fibonacci: Mapping[Timeframe, Sequence[FibonacciLevel]],
    confluence: Sequence[PriceConfluence],
) -> str:
    labels = {
        "monthly": "월봉(구조)",
        "weekly": "주봉(중기)",
        "daily": "일봉(전술)",
    }
    lines: list[str] = []
    for timeframe in TIMEFRAME_ORDER:
        evidence = _timeframe_value(packet, timeframe)
        selected: TimeframeSelection = getattr(selection, timeframe)
        if selected.status == "INSUFFICIENT_STRUCTURE":
            lines.append(f"{labels[timeframe]}: 확인된 구조가 충분하지 않습니다.")
            continue
        zones = {item.zone_id: item for item in evidence.sr_candidates}
        parts = [_regime_text(selected.regime)]
        for ref in (selected.support_zone_id, selected.resistance_zone_id):
            text = _zone_text(zones.get(ref or ""))
            if text:
                parts.append(text)
        fib_values = selected_fibonacci.get(timeframe, ())
        if fib_values:
            levels = ", ".join(
                f"{'되돌림' if item.mode == 'RETRACEMENT' else '확장'} "
                f"{item.ratio} {_format_price(item.calculated_price)}"
                for item in fib_values[:2]
            )
            parts.append(f"Fib {levels}")
        lines.append(f"{labels[timeframe]}: {'; '.join(parts)}")
    if confluence:
        strongest = confluence[0]
        timeframe_text = "/".join(
            {"monthly": "월봉", "weekly": "주봉", "daily": "일봉"}[item]
            for item in strongest.timeframes
        )
        synthesis = (
            f"독립 시간축 {timeframe_text} 근거가 "
            f"{_format_price(strongest.zone_low)}-{_format_price(strongest.zone_high)}에서 겹칩니다."
        )
    else:
        synthesis = "독립 시간축 근거의 유의미한 가격 중첩은 확인되지 않았습니다."
    lines.append(f"종합: {synthesis}")
    return "\n".join(lines)


def build_shadow_price_structure_result(
    packet: PriceStructureEvidencePacket,
    selection: MultiTimeframeSelection,
) -> ShadowPriceStructureResult:
    validation = validate_price_structure_selection(packet, selection)
    fibonacci = calculate_timeframe_fibonacci(packet, selection)
    candidate_confluence = calculate_multi_timeframe_confluence(packet, selection, fibonacci)
    selected = select_relevant_fibonacci_levels(
        fibonacci,
        packet.current_price,
        packet=packet,
        selection=selection,
        confluence=candidate_confluence,
    )
    confluence = calculate_multi_timeframe_confluence(packet, selection, selected)
    return ShadowPriceStructureResult(
        evidence=packet,
        selection=selection,
        validation=validation,
        fibonacci=fibonacci,
        selected_fibonacci=selected,
        confluence=confluence,
        shadow_render=render_shadow_price_structure(packet, selection, selected, confluence),
    )
