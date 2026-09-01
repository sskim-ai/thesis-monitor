from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from datetime import date
from decimal import Decimal, InvalidOperation
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict

from app.services.ohlcv_feature_engine_service import (
    MultiTimeframeFeaturePacket,
    TIMEFRAMES,
    build_multi_timeframe_feature_packet,
)
from app.services.ohlcv_provider_integrity_service import OhlcvIntegrityEvent


CONTRACT_VERSION = "packet-owned-technical-context-v1"
TIMEFRAME_KEYS = {"daily": "D", "weekly": "W", "monthly": "M"}


class TechnicalContextStatus(StrEnum):
    FULL = "FULL"
    PARTIAL_SAFE = "PARTIAL_SAFE"
    UNAVAILABLE = "UNAVAILABLE"
    INVALID = "INVALID"


class TechnicalFreshnessState(StrEnum):
    CURRENT = "CURRENT"
    TIMEFRAME_CURRENT = "TIMEFRAME_CURRENT"
    STALE = "STALE"
    UNAVAILABLE = "UNAVAILABLE"
    INVALID = "INVALID"


class FrozenModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class TimeframeTechnicalQuality(FrozenModel):
    timeframe: Literal["daily", "weekly", "monthly"]
    status: TechnicalContextStatus
    freshness_state: TechnicalFreshnessState
    last_completed_bar: str | None = None
    expected_completed_bar: str | None = None
    bar_count: int = 0
    feature_count: int = 0
    usable_for_current_reasoning: bool = False
    reasons: tuple[str, ...] = ()


class OhlcvAcquisitionTelemetry(FrozenModel):
    started_at: str | None = None
    completed_at: str | None = None
    request_count: int = 0
    success_count: int = 0
    retry_count: int = 0
    connection_error_count: int = 0
    timeout_count: int = 0
    server_error_count: int = 0
    non_retryable_error_count: int = 0
    cache_use_count: int = 0
    raw_bars_validated_count: int = 0
    invalid_raw_row_count: int = 0
    malformed_refetch_count: int = 0
    transient_malformed_recovered_count: int = 0
    stable_malformed_unresolved_count: int = 0
    intermittent_malformed_unresolved_count: int = 0
    failure_classes: tuple[str, ...] = ()
    integrity_events: tuple[OhlcvIntegrityEvent, ...] = ()


class PacketOwnedTechnicalContext(FrozenModel):
    contract: Literal["packet-owned-technical-context-v1"] = CONTRACT_VERSION
    technical_context_id: str
    ticker: str
    market: Literal["kr", "us"]
    session: str
    as_of: str
    source: str = "ohlcv_analyst"
    source_version: str = "ohlcv-http-v1"
    adjustment_basis: str = "adjusted_close"
    currency: Literal["KRW", "USD"]
    security_identity: str
    status: TechnicalContextStatus
    freshness_state: TechnicalFreshnessState
    last_completed_bar: dict[str, str | None]
    bar_counts: dict[str, int]
    quality: dict[str, TimeframeTechnicalQuality]
    features: MultiTimeframeFeaturePacket | None = None
    raw_bar_fingerprint: str
    feature_fingerprint: str | None = None
    acquisition: OhlcvAcquisitionTelemetry = OhlcvAcquisitionTelemetry()
    failure_reason: str | None = None
    cautions: tuple[str, ...] = ()


def _canonical_sha(value: object) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )
    return hashlib.sha256(payload.encode()).hexdigest()


def _decimal(value: object) -> Decimal | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None
    return number if number.is_finite() else None


def _validate_rows(
    rows: Sequence[Mapping[str, object]],
    *,
    cutoff: date,
) -> tuple[list[Mapping[str, object]], tuple[str, ...], str | None]:
    reasons: list[str] = []
    valid: list[Mapping[str, object]] = []
    observed_dates: list[date] = []
    for row in rows:
        try:
            bar_date = date.fromisoformat(str(row.get("date") or "")[:10])
        except ValueError:
            reasons.append("invalid_bar_date")
            continue
        if bar_date > cutoff:
            reasons.append("future_bar")
            continue
        values = tuple(_decimal(row.get(key)) for key in ("open", "high", "low", "close"))
        if any(value is None for value in values):
            reasons.append("missing_or_invalid_ohlc")
            continue
        open_value, high, low, close = values
        assert open_value is not None and high is not None and low is not None and close is not None
        if (
            min(values) <= 0
            or high < low
            or not low <= open_value <= high
            or not low <= close <= high
        ):
            reasons.append("invalid_ohlc_relation")
            continue
        volume = _decimal(row.get("volume"))
        if volume is not None and volume < 0:
            reasons.append("negative_volume")
            continue
        observed_dates.append(bar_date)
        valid.append(row)
    if len(observed_dates) != len(set(observed_dates)):
        reasons.append("duplicate_bar_timestamp")
    if observed_dates != sorted(observed_dates):
        reasons.append("bar_timestamp_ordering")
    return (
        valid,
        tuple(dict.fromkeys(reasons)),
        (max(observed_dates).isoformat() if observed_dates else None),
    )


def _context_id(
    *,
    ticker: str,
    market: str,
    cutoff: date,
    raw_fingerprint: str,
    feature_fingerprint: str | None,
) -> str:
    value = "|".join(
        (ticker, market, cutoff.isoformat(), raw_fingerprint, feature_fingerprint or "")
    )
    return "technical-context:" + hashlib.sha256(value.encode()).hexdigest()[:24]


def build_packet_owned_technical_context(
    *,
    ticker: str,
    market: Literal["kr", "us"],
    session: str,
    as_of: str,
    periods: Mapping[str, Sequence[Mapping[str, object]]],
    cutoff: date,
    expected_daily_completed: str | None,
    acquisition: Mapping[str, object] | OhlcvAcquisitionTelemetry | None = None,
    source: str = "ohlcv_analyst",
    source_version: str = "ohlcv-http-v1",
) -> PacketOwnedTechnicalContext:
    validated: dict[str, list[Mapping[str, object]]] = {}
    errors: dict[str, tuple[str, ...]] = {}
    latest: dict[str, str | None] = {}
    raw_identity: dict[str, object] = {}
    for timeframe in TIMEFRAMES:
        rows = [row for row in periods.get(timeframe, ()) if isinstance(row, Mapping)]
        safe_rows, reasons, last_bar = _validate_rows(rows, cutoff=cutoff)
        validated[timeframe] = safe_rows
        errors[timeframe] = reasons
        latest[timeframe] = last_bar
        raw_identity[timeframe] = [
            {key: row.get(key) for key in ("date", "open", "high", "low", "close", "volume")}
            for row in rows
        ]
    raw_fingerprint = _canonical_sha(raw_identity)
    invalid = any(errors[timeframe] for timeframe in TIMEFRAMES)
    features = None
    if not invalid:
        features = build_multi_timeframe_feature_packet(
            ticker=ticker,
            periods=validated,
            cutoff=cutoff,
        )
    quality: dict[str, TimeframeTechnicalQuality] = {}
    cautions: list[str] = []
    for timeframe in TIMEFRAMES:
        key = TIMEFRAME_KEYS[timeframe]
        reasons = list(errors[timeframe])
        feature_set = getattr(features, timeframe) if features is not None else None
        feature_count = len(feature_set.facts) if feature_set is not None else 0
        expected = expected_daily_completed if timeframe == "daily" else None
        if reasons:
            state = TechnicalContextStatus.INVALID
            freshness = TechnicalFreshnessState.INVALID
        elif not validated[timeframe] or feature_count == 0:
            state = TechnicalContextStatus.UNAVAILABLE
            freshness = TechnicalFreshnessState.UNAVAILABLE
            reasons.append("timeframe_unavailable")
        elif timeframe == "daily" and expected and latest[timeframe] != expected:
            state = TechnicalContextStatus.PARTIAL_SAFE
            freshness = TechnicalFreshnessState.STALE
            reasons.append("daily_last_completed_session_mismatch")
        else:
            state = TechnicalContextStatus.FULL
            freshness = (
                TechnicalFreshnessState.CURRENT
                if timeframe == "daily"
                else TechnicalFreshnessState.TIMEFRAME_CURRENT
            )
        usable = state == TechnicalContextStatus.FULL
        quality[key] = TimeframeTechnicalQuality(
            timeframe=timeframe,  # type: ignore[arg-type]
            status=state,
            freshness_state=freshness,
            last_completed_bar=latest[timeframe],
            expected_completed_bar=expected,
            bar_count=len(validated[timeframe]),
            feature_count=feature_count,
            usable_for_current_reasoning=usable,
            reasons=tuple(dict.fromkeys(reasons)),
        )
        cautions.extend(f"{key}:{reason}" for reason in reasons)
    states = {row.status for row in quality.values()}
    if TechnicalContextStatus.INVALID in states:
        status = TechnicalContextStatus.INVALID
        freshness_state = TechnicalFreshnessState.INVALID
        features = None
    elif states == {TechnicalContextStatus.FULL}:
        status = TechnicalContextStatus.FULL
        freshness_state = TechnicalFreshnessState.CURRENT
    elif states == {TechnicalContextStatus.UNAVAILABLE}:
        status = TechnicalContextStatus.UNAVAILABLE
        freshness_state = TechnicalFreshnessState.UNAVAILABLE
    else:
        status = TechnicalContextStatus.PARTIAL_SAFE
        freshness_state = (
            TechnicalFreshnessState.STALE
            if quality["D"].freshness_state == TechnicalFreshnessState.STALE
            else TechnicalFreshnessState.TIMEFRAME_CURRENT
        )
    telemetry = (
        acquisition
        if isinstance(acquisition, OhlcvAcquisitionTelemetry)
        else OhlcvAcquisitionTelemetry.model_validate(acquisition or {})
    )
    feature_fingerprint = features.packet_sha256 if features is not None else None
    reason = ",".join(dict.fromkeys(cautions)) or None
    return PacketOwnedTechnicalContext(
        technical_context_id=_context_id(
            ticker=ticker,
            market=market,
            cutoff=cutoff,
            raw_fingerprint=raw_fingerprint,
            feature_fingerprint=feature_fingerprint,
        ),
        ticker=ticker,
        market=market,
        session=session,
        as_of=as_of,
        source=source,
        source_version=source_version,
        currency="KRW" if market == "kr" else "USD",
        security_identity=ticker,
        status=status,
        freshness_state=freshness_state,
        last_completed_bar={TIMEFRAME_KEYS[key]: value for key, value in latest.items()},
        bar_counts={TIMEFRAME_KEYS[key]: len(value) for key, value in validated.items()},
        quality=quality,
        features=features,
        raw_bar_fingerprint=raw_fingerprint,
        feature_fingerprint=feature_fingerprint,
        acquisition=telemetry,
        failure_reason=reason,
        cautions=tuple(dict.fromkeys(cautions)),
    )


def unavailable_packet_owned_technical_context(
    *,
    ticker: str,
    market: Literal["kr", "us"],
    session: str,
    as_of: str,
    reason: str,
) -> PacketOwnedTechnicalContext:
    raw_fingerprint = _canonical_sha({"ticker": ticker, "reason": reason})
    quality = {
        key: TimeframeTechnicalQuality(
            timeframe=timeframe,  # type: ignore[arg-type]
            status=TechnicalContextStatus.UNAVAILABLE,
            freshness_state=TechnicalFreshnessState.UNAVAILABLE,
            reasons=(reason,),
        )
        for timeframe, key in TIMEFRAME_KEYS.items()
    }
    return PacketOwnedTechnicalContext(
        technical_context_id=_context_id(
            ticker=ticker,
            market=market,
            cutoff=date.fromisoformat(as_of[:10]),
            raw_fingerprint=raw_fingerprint,
            feature_fingerprint=None,
        ),
        ticker=ticker,
        market=market,
        session=session,
        as_of=as_of,
        currency="KRW" if market == "kr" else "USD",
        security_identity=ticker,
        status=TechnicalContextStatus.UNAVAILABLE,
        freshness_state=TechnicalFreshnessState.UNAVAILABLE,
        last_completed_bar={"D": None, "W": None, "M": None},
        bar_counts={"D": 0, "W": 0, "M": 0},
        quality=quality,
        raw_bar_fingerprint=raw_fingerprint,
        failure_reason=reason,
        cautions=(reason,),
    )


def load_packet_owned_technical_context(
    value: object,
    *,
    ticker: str,
) -> PacketOwnedTechnicalContext:
    context = PacketOwnedTechnicalContext.model_validate(value)
    if context.ticker != ticker:
        raise ValueError("packet_owned_technical_context_ticker_mismatch")
    return context


def packet_owned_context_for_stock(
    *,
    packet: Mapping[str, object],
    stock: Mapping[str, object],
) -> PacketOwnedTechnicalContext:
    ticker = str(stock.get("ticker") or "").upper()
    market = str(packet.get("market") or "").lower()
    if market not in {"kr", "us"}:
        raise ValueError("packet_technical_context_market_invalid")
    raw = stock.get("technical_context")
    if isinstance(raw, Mapping):
        try:
            return load_packet_owned_technical_context(raw, ticker=ticker)
        except ValueError:
            reason = "packet_technical_context_invalid"
    else:
        reason = "packet_technical_context_missing"
    return unavailable_packet_owned_technical_context(
        ticker=ticker,
        market="kr" if market == "kr" else "us",
        session="unknown",
        as_of=str(packet.get("generated_at") or packet.get("assessment_date") or ""),
        reason=reason,
    )
