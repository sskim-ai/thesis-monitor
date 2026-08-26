from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from datetime import date, timedelta
from decimal import Decimal
from typing import Literal

import exchange_calendars as exchange_calendar
from pydantic import BaseModel, ConfigDict

from app.services.ohlcv_structure_service import Timeframe


CONTRACT_VERSION = "ohlcv-1200-backfill-cache-v1"
BackfillStatus = Literal["PASS", "PARTIAL", "BLOCKED"]


class FrozenModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class HistoryCacheIdentity(FrozenModel):
    contract: str = CONTRACT_VERSION
    security_id: str
    listing_id: str
    timeframe: Timeframe
    adjustment_basis: str
    currency: str

    @property
    def cache_key(self) -> str:
        payload = self.model_dump(mode="json")
        material = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return f"ohlcv-history:{hashlib.sha256(material.encode()).hexdigest()}"


class HistoryPage(FrozenModel):
    page_id: str
    provider: str
    identity: HistoryCacheIdentity
    observed_at: str
    rows: tuple[dict[str, object], ...]


class CanonicalHistoryRow(FrozenModel):
    date: str
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal | None = None
    trading_value: Decimal | None = None
    source_page_ids: tuple[str, ...]


class HistoryBackfillResult(FrozenModel):
    contract: str = CONTRACT_VERSION
    identity: HistoryCacheIdentity
    cache_key: str
    requested_count: int
    actual_count: int
    first_bar_date: str | None
    last_bar_date: str | None
    revision_timestamp: str | None
    status: BackfillStatus
    rows: tuple[CanonicalHistoryRow, ...]
    duplicate_dates_deduplicated: tuple[str, ...] = ()
    conflicting_dates: tuple[str, ...] = ()
    missing_expected_dates: tuple[str, ...] = ()
    expected_session_exclusions: tuple[str, ...] = ()
    chronology_valid: bool
    denial_reasons: tuple[str, ...] = ()
    page_ids: tuple[str, ...] = ()
    evidence_sha256: str


class HistoryCacheUpdateAudit(FrozenModel):
    contract: str = CONTRACT_VERSION
    cache_hit: bool
    appended_dates: tuple[str, ...]
    revised_dates: tuple[str, ...]
    result: HistoryBackfillResult


def _decimal(value: object) -> Decimal:
    return Decimal(str(value))


def _normalized_row(raw: Mapping[str, object], page_id: str) -> CanonicalHistoryRow | None:
    raw_date = str(raw.get("date") or "")[:10]
    try:
        date.fromisoformat(raw_date)
    except ValueError:
        return None
    required = (raw.get("open"), raw.get("high"), raw.get("low"), raw.get("close"))
    if any(value is None for value in required):
        return None
    row = CanonicalHistoryRow(
        date=raw_date,
        open=_decimal(raw["open"]),
        high=_decimal(raw["high"]),
        low=_decimal(raw["low"]),
        close=_decimal(raw["close"]),
        volume=_decimal(raw["volume"]) if raw.get("volume") is not None else None,
        trading_value=(
            _decimal(raw["value"])
            if raw.get("value") is not None
            else _decimal(raw["trading_value"])
            if raw.get("trading_value") is not None
            else None
        ),
        source_page_ids=(page_id,),
    )
    if row.high < row.low or not (row.low <= row.open <= row.high) or not (
        row.low <= row.close <= row.high
    ):
        return None
    return row


def _economic_signature(row: CanonicalHistoryRow) -> tuple[object, ...]:
    return (
        row.open,
        row.high,
        row.low,
        row.close,
        row.volume,
        row.trading_value,
    )


def _expected_daily_sessions(
    market: Literal["KR", "US"],
    start: date,
    end: date,
) -> tuple[str, ...]:
    name = "XKRX" if market == "KR" else "XNYS"
    calendar = exchange_calendar.get_calendar(
        name,
        start=start - timedelta(days=370),
        end=end + timedelta(days=370),
    )
    return tuple(item.date().isoformat() for item in calendar.sessions_in_range(start, end))


def merge_history_pages(
    pages: Sequence[HistoryPage],
    *,
    identity: HistoryCacheIdentity,
    market: Literal["KR", "US"],
    requested_count: int,
    cutoff: str,
    expected_session_exclusions: Sequence[str] = (),
) -> HistoryBackfillResult:
    reasons: list[str] = []
    conflicts: list[str] = []
    duplicates: list[str] = []
    by_date: dict[str, CanonicalHistoryRow] = {}
    for page in pages:
        if page.identity != identity:
            reasons.append(f"identity_mismatch:{page.page_id}")
            continue
        for raw in page.rows:
            row = _normalized_row(raw, page.page_id)
            if row is None or row.date > cutoff:
                continue
            existing = by_date.get(row.date)
            if existing is None:
                by_date[row.date] = row
                continue
            if _economic_signature(existing) != _economic_signature(row):
                conflicts.append(row.date)
                continue
            duplicates.append(row.date)
            by_date[row.date] = existing.model_copy(
                update={
                    "source_page_ids": tuple(
                        dict.fromkeys(existing.source_page_ids + row.source_page_ids)
                    )
                }
            )
    ordered = tuple(by_date[key] for key in sorted(by_date))
    selected = ordered[-requested_count:]
    chronology_valid = all(
        selected[index - 1].date < selected[index].date for index in range(1, len(selected))
    )
    if not chronology_valid:
        reasons.append("chronology_invalid")
    missing: tuple[str, ...] = ()
    if selected and identity.timeframe == "daily":
        expected = _expected_daily_sessions(
            market,
            date.fromisoformat(selected[0].date),
            date.fromisoformat(selected[-1].date),
        )
        actual_dates = {row.date for row in selected}
        exclusions = set(expected_session_exclusions)
        missing = tuple(
            item for item in expected if item not in actual_dates and item not in exclusions
        )
    if conflicts:
        reasons.append("conflicting_duplicate_occurrence")
    if len(selected) < requested_count:
        reasons.append("short_available_history")
    if missing:
        reasons.append("missing_expected_sessions")
    status: BackfillStatus
    if conflicts or any(reason.startswith("identity_mismatch") for reason in reasons):
        status = "BLOCKED"
    elif reasons:
        status = "PARTIAL"
    else:
        status = "PASS"
    evidence_payload = {
        "identity": identity.model_dump(mode="json"),
        "requested_count": requested_count,
        "expected_session_exclusions": sorted(set(expected_session_exclusions)),
        "rows": [row.model_dump(mode="json") for row in selected],
        "page_ids": [page.page_id for page in pages],
    }
    evidence_sha = hashlib.sha256(
        json.dumps(evidence_payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return HistoryBackfillResult(
        identity=identity,
        cache_key=identity.cache_key,
        requested_count=requested_count,
        actual_count=len(selected),
        first_bar_date=selected[0].date if selected else None,
        last_bar_date=selected[-1].date if selected else None,
        revision_timestamp=max((page.observed_at for page in pages), default=None),
        status=status,
        rows=selected,
        duplicate_dates_deduplicated=tuple(sorted(set(duplicates))),
        conflicting_dates=tuple(sorted(set(conflicts))),
        missing_expected_dates=missing,
        expected_session_exclusions=tuple(sorted(set(expected_session_exclusions))),
        chronology_valid=chronology_valid,
        denial_reasons=tuple(dict.fromkeys(reasons)),
        page_ids=tuple(page.page_id for page in pages),
        evidence_sha256=evidence_sha,
    )


def update_cached_history(
    cached: HistoryBackfillResult,
    incremental_page: HistoryPage,
    *,
    market: Literal["KR", "US"],
    cutoff: str,
    expected_session_exclusions: Sequence[str] = (),
) -> HistoryCacheUpdateAudit:
    if incremental_page.identity != cached.identity:
        blocked = merge_history_pages(
            (incremental_page,),
            identity=cached.identity,
            market=market,
            requested_count=cached.requested_count,
            cutoff=cutoff,
            expected_session_exclusions=expected_session_exclusions,
        )
        return HistoryCacheUpdateAudit(
            cache_hit=True,
            appended_dates=(),
            revised_dates=(),
            result=blocked,
        )
    existing = {row.date: row for row in cached.rows}
    merged: dict[str, dict[str, object]] = {
        row.date: {
            "date": row.date,
            "open": row.open,
            "high": row.high,
            "low": row.low,
            "close": row.close,
            "volume": row.volume,
            "trading_value": row.trading_value,
        }
        for row in cached.rows
    }
    appended: list[str] = []
    revised: list[str] = []
    for raw in incremental_page.rows:
        normalized = _normalized_row(raw, incremental_page.page_id)
        if normalized is None or normalized.date > cutoff:
            continue
        previous = existing.get(normalized.date)
        if previous is None:
            appended.append(normalized.date)
        elif _economic_signature(previous) != _economic_signature(normalized):
            revised.append(normalized.date)
        merged[normalized.date] = dict(raw)
    consolidated = HistoryPage(
        page_id=f"cache-update:{incremental_page.page_id}",
        provider=incremental_page.provider,
        identity=cached.identity,
        observed_at=incremental_page.observed_at,
        rows=tuple(merged[key] for key in sorted(merged)),
    )
    result = merge_history_pages(
        (consolidated,),
        identity=cached.identity,
        market=market,
        requested_count=cached.requested_count,
        cutoff=cutoff,
        expected_session_exclusions=expected_session_exclusions,
    )
    return HistoryCacheUpdateAudit(
        cache_hit=True,
        appended_dates=tuple(sorted(set(appended))),
        revised_dates=tuple(sorted(set(revised))),
        result=result,
    )
