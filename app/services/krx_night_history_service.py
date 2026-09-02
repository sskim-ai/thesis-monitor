from __future__ import annotations

import hashlib
import json
import math
import os
from datetime import date, datetime, time, timedelta
from pathlib import Path
from typing import Literal, Mapping

from pydantic import BaseModel

from app.config import get_settings
from app.jobs.probe_krx_night_futures import (
    KRX_FUTURES_DAILY_URL,
    KRX_SERVICE_NAME,
    KST,
    _integer,
    _maturity,
    _number,
    _rows,
    _session,
    _target_product,
)
from app.services.market_session import is_exchange_session_date


KRX_NIGHT_DAILY_OHLC_CONTRACT = "krx-night-daily-ohlc-v1"
KRX_NIGHT_HISTORY_CONTRACT = "krx-night-history-store-v1"
KRX_NIGHT_DWM_CONTRACT = "krx-night-same-contract-dwm-v1"
KRX_NIGHT_RAW_RECEIPT_CONTRACT = "krx-night-raw-response-receipt-v1"

SERIES_CODES = {
    "KOSPI200": "KRX_KOSPI200_NIGHT_FUT",
    "KOSDAQ150": "KRX_KOSDAQ150_NIGHT_FUT",
}

KRX_NIGHT_OHLC_FIELD_MAPPING = {
    "date": "BAS_DD",
    "instrument_root": "PROD_NM + ISU_NM",
    "contract": "ISU_CD + ISU_NM maturity",
    "session": "MKT_NM",
    "open": "TDD_OPNPRC",
    "high": "TDD_HGPRC",
    "low": "TDD_LWPRC",
    "close": "TDD_CLSPRC",
    "volume": "ACC_TRDVOL",
    "official_change": "CMPPREVDD_PRC",
}


class KrxNightHistoryConflictError(ValueError):
    pass


class KrxNightRawResponseReceipt(BaseModel):
    contract: Literal["krx-night-raw-response-receipt-v1"] = KRX_NIGHT_RAW_RECEIPT_CONTRACT
    service: str = KRX_SERVICE_NAME
    source_url: str = KRX_FUTURES_DAILY_URL
    query_date: date
    fetched_at: datetime
    http_status: int
    raw_payload_sha256: str
    raw_size_bytes: int
    row_count: int
    field_names: tuple[str, ...]
    raw_relative_path: str


class KrxNightDailyBar(BaseModel):
    contract: Literal["krx-night-daily-ohlc-v1"] = KRX_NIGHT_DAILY_OHLC_CONTRACT
    fact_id: str
    instrument_root: Literal["KOSPI200", "KOSDAQ150"]
    series_code: str
    contract_code: str
    contract_maturity: str
    reference_date: date
    session: Literal["NIGHT"] = "NIGHT"
    open: float
    high: float
    low: float
    close: float
    volume: int | None = None
    official_change: float | None = None
    official_change_pct: float | None = None
    bar_finality: Literal["FINAL", "UNFINALIZED"]
    quality: Literal["VALID"] = "VALID"
    source_row_identity: str
    source_raw_sha256: str
    source_raw_relative_path: str
    normalized_fingerprint: str
    fetched_at: datetime


class KrxNightRowRejection(BaseModel):
    source_row_identity: str
    reference_date: date | None = None
    instrument_root: str | None = None
    contract_code: str | None = None
    reason: str
    source_raw_sha256: str


class KrxNightNormalizationResult(BaseModel):
    contract: str = KRX_NIGHT_DAILY_OHLC_CONTRACT
    query_date: date
    raw_payload_sha256: str
    bars: tuple[KrxNightDailyBar, ...] = ()
    rejections: tuple[KrxNightRowRejection, ...] = ()


class KrxNightAggregateBar(BaseModel):
    contract: str = KRX_NIGHT_DWM_CONTRACT
    fact_id: str
    instrument_root: str
    series_code: str
    contract_code: str
    contract_maturity: str
    timeframe: Literal["DAILY", "WEEKLY", "MONTHLY"]
    bar_start_date: date
    reference_date: date
    open: float
    high: float
    low: float
    close: float
    status: Literal[
        "FINAL",
        "IN_PROGRESS",
        "SAME_CONTRACT_PARTIAL_PERIOD",
    ]
    quality: Literal["VALID", "PARTIAL_SAFE"]
    expected_dates: tuple[date, ...]
    included_dates: tuple[date, ...]
    missing_dates: tuple[date, ...]
    future_expected_dates: tuple[date, ...]
    aggregation_start_date: date
    gap_value: float | None = None
    gap_pct: float | None = None
    gap_baseline_date: date | None = None
    gap_baseline_close: float | None = None
    gap_baseline_semantic: str | None = None
    change_value: float | None = None
    return_pct: float | None = None
    return_baseline_date: date | None = None
    return_baseline_close: float | None = None
    return_baseline_semantic: str | None = None
    source_fact_ids: tuple[str, ...]
    source_raw_sha256: tuple[str, ...]
    source_fingerprints: tuple[str, ...]


class KrxNightTimeframes(BaseModel):
    contract: str = KRX_NIGHT_DWM_CONTRACT
    instrument_root: str
    series_code: str
    contract_code: str
    contract_maturity: str
    reference_date: date
    daily: KrxNightAggregateBar
    weekly: KrxNightAggregateBar
    monthly: KrxNightAggregateBar


class KrxNightHistoryUpdate(BaseModel):
    contract: str = KRX_NIGHT_HISTORY_CONTRACT
    source_mode: str
    request_count: int = 0
    cache_hit_count: int = 0
    raw_receipt_count: int = 0
    normalized_bar_count: int = 0
    stored_bar_count: int = 0
    unchanged_bar_count: int = 0
    rejection_count: int = 0
    raw_payload_sha256: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()


def default_krx_night_history_directory() -> Path:
    return Path(get_settings().data_dir) / "market/krx-night-history"


def _atomic_bytes(path: Path, value: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    descriptor = os.open(temporary, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    try:
        os.write(descriptor, value)
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    os.replace(temporary, path)


def _atomic_json(path: Path, value: object) -> None:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")
    _atomic_bytes(path, encoded)


def _canonical_sha(value: object) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _date_value(value: object) -> date | None:
    text = str(value or "").strip()
    try:
        return datetime.strptime(text, "%Y%m%d").date()
    except ValueError:
        return None


def _raw_paths(root: Path, query_date: date, raw_sha: str) -> tuple[Path, Path]:
    directory = root / "raw" / f"{query_date:%Y}" / f"{query_date:%m}" / f"{query_date:%d}"
    return directory / f"{raw_sha}.json", directory / f"{raw_sha}.receipt.json"


def preserve_raw_krx_response(
    *,
    root: Path,
    query_date: date,
    fetched_at: datetime,
    http_status: int,
    raw_body: bytes,
) -> tuple[KrxNightRawResponseReceipt, object, bool]:
    raw_sha = hashlib.sha256(raw_body).hexdigest()
    try:
        payload = json.loads(raw_body)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("krx_raw_response_not_json") from exc
    rows = _rows(payload)
    raw_path, receipt_path = _raw_paths(root, query_date, raw_sha)
    created = False
    if raw_path.exists():
        if raw_path.read_bytes() != raw_body:
            raise KrxNightHistoryConflictError("raw_sha_path_content_conflict")
    else:
        _atomic_bytes(raw_path, raw_body)
        created = True
    receipt = KrxNightRawResponseReceipt(
        query_date=query_date,
        fetched_at=fetched_at,
        http_status=http_status,
        raw_payload_sha256=raw_sha,
        raw_size_bytes=len(raw_body),
        row_count=len(rows),
        field_names=tuple(sorted({key for row in rows for key in row})),
        raw_relative_path=str(raw_path.relative_to(root)),
    )
    if receipt_path.exists():
        existing = KrxNightRawResponseReceipt.model_validate_json(
            receipt_path.read_text(encoding="utf-8")
        )
        if existing.raw_payload_sha256 != raw_sha:
            raise KrxNightHistoryConflictError("raw_receipt_identity_conflict")
    else:
        _atomic_json(receipt_path, receipt.model_dump(mode="json"))
    return receipt, payload, created


def _bar_fact_id(product: str, contract_code: str, reference_date: date) -> str:
    return (
        "market:night_futures:daily:"
        f"{SERIES_CODES[product]}:{contract_code}:{reference_date.isoformat()}"
    )


def normalize_krx_night_daily_bars(
    *,
    payload: object,
    query_date: date,
    fetched_at: datetime,
    raw_payload_sha256: str,
    raw_relative_path: str,
) -> KrxNightNormalizationResult:
    finality = (
        "FINAL"
        if fetched_at.astimezone(KST) >= datetime.combine(query_date, time(6), tzinfo=KST)
        else "UNFINALIZED"
    )
    bars: list[KrxNightDailyBar] = []
    rejections: list[KrxNightRowRejection] = []
    for index, item in enumerate(_rows(payload)):
        if _session(item.get("MKT_NM")) != "night":
            continue
        product = _target_product(item.get("PROD_NM"), item.get("ISU_NM"))
        if product is None:
            continue
        reference_date = _date_value(item.get("BAS_DD"))
        contract_code = str(item.get("ISU_CD") or "").strip()
        contract_name = str(item.get("ISU_NM") or "").strip()
        maturity = _maturity(contract_name)
        identity = ":".join(
            (
                reference_date.isoformat() if reference_date else "unknown-date",
                "NIGHT",
                contract_code or f"row-{index}",
            )
        )
        values = {
            "open": _number(item.get("TDD_OPNPRC")),
            "high": _number(item.get("TDD_HGPRC")),
            "low": _number(item.get("TDD_LWPRC")),
            "close": _number(item.get("TDD_CLSPRC")),
        }
        reason: str | None = None
        if reference_date is None or reference_date != query_date:
            reason = "reference_date_invalid_or_mismatched"
        elif not contract_code or maturity is None:
            reason = "contract_identity_unavailable"
        elif any(value is None or not math.isfinite(value) for value in values.values()):
            reason = "ohlc_non_finite_or_missing"
        elif any(value <= 0 for value in values.values() if value is not None):
            reason = "ohlc_non_positive"
        elif not (
            values["low"] <= values["open"] <= values["high"]
            and values["low"] <= values["close"] <= values["high"]
        ):
            reason = "ohlc_relation_invalid"
        if reason is not None:
            rejections.append(
                KrxNightRowRejection(
                    source_row_identity=identity,
                    reference_date=reference_date,
                    instrument_root=product,
                    contract_code=contract_code or None,
                    reason=reason,
                    source_raw_sha256=raw_payload_sha256,
                )
            )
            continue
        assert reference_date is not None and maturity is not None
        normalized = {
            "instrument_root": product,
            "series_code": SERIES_CODES[product],
            "contract_code": contract_code,
            "contract_maturity": maturity,
            "reference_date": reference_date.isoformat(),
            "session": "NIGHT",
            **values,
            "volume": _integer(item.get("ACC_TRDVOL")),
            "official_change": _number(item.get("CMPPREVDD_PRC")),
            "source_raw_sha256": raw_payload_sha256,
        }
        bars.append(
            KrxNightDailyBar(
                fact_id=_bar_fact_id(product, contract_code, reference_date),
                instrument_root=product,
                series_code=SERIES_CODES[product],
                contract_code=contract_code,
                contract_maturity=maturity,
                reference_date=reference_date,
                open=float(values["open"]),
                high=float(values["high"]),
                low=float(values["low"]),
                close=float(values["close"]),
                volume=normalized["volume"],
                official_change=normalized["official_change"],
                bar_finality=finality,
                source_row_identity=identity,
                source_raw_sha256=raw_payload_sha256,
                source_raw_relative_path=raw_relative_path,
                normalized_fingerprint=_canonical_sha(normalized),
                fetched_at=fetched_at,
            )
        )
    return KrxNightNormalizationResult(
        query_date=query_date,
        raw_payload_sha256=raw_payload_sha256,
        bars=tuple(bars),
        rejections=tuple(rejections),
    )


def _daily_path(root: Path, bar: KrxNightDailyBar) -> Path:
    return (
        root
        / "daily"
        / bar.instrument_root
        / bar.contract_code
        / f"{bar.reference_date:%Y}"
        / f"{bar.reference_date:%m}"
        / f"{bar.reference_date:%d}.json"
    )


def store_normalized_bar(root: Path, bar: KrxNightDailyBar) -> bool:
    if bar.bar_finality != "FINAL":
        return False
    path = _daily_path(root, bar)
    if path.exists():
        existing = KrxNightDailyBar.model_validate_json(path.read_text(encoding="utf-8"))
        if existing.normalized_fingerprint != bar.normalized_fingerprint:
            raise KrxNightHistoryConflictError(
                f"normalized_bar_identity_conflict:{bar.source_row_identity}"
            )
        return False
    _atomic_json(path, bar.model_dump(mode="json"))
    return True


def persist_krx_response(
    *,
    root: Path,
    query_date: date,
    fetched_at: datetime,
    http_status: int,
    raw_body: bytes,
) -> tuple[KrxNightRawResponseReceipt, KrxNightNormalizationResult, int]:
    receipt, payload, _created = preserve_raw_krx_response(
        root=root,
        query_date=query_date,
        fetched_at=fetched_at,
        http_status=http_status,
        raw_body=raw_body,
    )
    normalized = normalize_krx_night_daily_bars(
        payload=payload,
        query_date=query_date,
        fetched_at=fetched_at,
        raw_payload_sha256=receipt.raw_payload_sha256,
        raw_relative_path=receipt.raw_relative_path,
    )
    stored = sum(store_normalized_bar(root, bar) for bar in normalized.bars)
    return receipt, normalized, stored


def load_cached_response(
    root: Path,
    query_date: date,
) -> tuple[KrxNightRawResponseReceipt, bytes] | None:
    directory = root / "raw" / f"{query_date:%Y}" / f"{query_date:%m}" / f"{query_date:%d}"
    receipts = sorted(directory.glob("*.receipt.json"))
    for path in reversed(receipts):
        receipt = KrxNightRawResponseReceipt.model_validate_json(path.read_text(encoding="utf-8"))
        raw_path = root / receipt.raw_relative_path
        if raw_path.exists() and hashlib.sha256(raw_path.read_bytes()).hexdigest() == (
            receipt.raw_payload_sha256
        ):
            return receipt, raw_path.read_bytes()
    return None


def _load_bar(path: Path) -> KrxNightDailyBar | None:
    try:
        return KrxNightDailyBar.model_validate_json(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def load_history(
    root: Path,
    *,
    instrument_root: str,
    contract_code: str | None = None,
    start: date | None = None,
    end: date | None = None,
) -> tuple[KrxNightDailyBar, ...]:
    base = root / "daily" / instrument_root
    if contract_code:
        bases = (base / contract_code,)
    else:
        bases = tuple(path for path in base.glob("*") if path.is_dir())
    bars = [
        bar
        for directory in bases
        for path in directory.glob("*/*/*.json")
        if (bar := _load_bar(path)) is not None
        and (start is None or bar.reference_date >= start)
        and (end is None or bar.reference_date <= end)
    ]
    return tuple(sorted(bars, key=lambda item: (item.reference_date, item.contract_code)))


def _maturity_key(value: str) -> tuple[int, int]:
    year, month = value.split("-", 1)
    return int(year), int(month)


def resolve_near_month(
    bars: tuple[KrxNightDailyBar, ...],
    *,
    reference_date: date,
) -> KrxNightDailyBar | None:
    candidates = [
        bar
        for bar in bars
        if bar.reference_date == reference_date
        and bar.bar_finality == "FINAL"
        and _maturity_key(bar.contract_maturity) >= (reference_date.year, reference_date.month)
    ]
    return min(candidates, key=lambda item: _maturity_key(item.contract_maturity), default=None)


def _session_dates(start: date, end: date) -> tuple[date, ...]:
    if end < start:
        return ()
    return tuple(
        current
        for offset in range((end - start).days + 1)
        if is_exchange_session_date("XKRX", current := start + timedelta(days=offset))
    )


def _period_bounds(reference_date: date, timeframe: str) -> tuple[date, date]:
    if timeframe == "WEEKLY":
        start = reference_date - timedelta(days=reference_date.weekday())
        return start, start + timedelta(days=6)
    if timeframe == "MONTHLY":
        start = reference_date.replace(day=1)
        next_month = (
            start.replace(year=start.year + 1, month=1)
            if start.month == 12
            else start.replace(month=start.month + 1)
        )
        return start, next_month - timedelta(days=1)
    return reference_date, reference_date


def _previous_bounds(start: date, timeframe: str) -> tuple[date, date]:
    if timeframe == "WEEKLY":
        return start - timedelta(days=7), start - timedelta(days=1)
    previous_end = start - timedelta(days=1)
    return previous_end.replace(day=1), previous_end


def _complete_baseline(
    all_contract_bars: Mapping[date, KrxNightDailyBar],
    *,
    start: date,
    timeframe: str,
) -> KrxNightDailyBar | None:
    previous_start, previous_end = _previous_bounds(start, timeframe)
    expected = _session_dates(previous_start, previous_end)
    bars = [all_contract_bars[value] for value in expected if value in all_contract_bars]
    if not expected or len(bars) != len(expected):
        return None
    return bars[-1]


def _aggregate(
    *,
    instrument_root: str,
    selected: KrxNightDailyBar,
    timeframe: Literal["WEEKLY", "MONTHLY"],
    same_contract: Mapping[date, KrxNightDailyBar],
    all_product: Mapping[date, tuple[KrxNightDailyBar, ...]],
) -> KrxNightAggregateBar:
    start, end = _period_bounds(selected.reference_date, timeframe)
    expected = _session_dates(start, end)
    elapsed = tuple(value for value in expected if value <= selected.reference_date)
    future = tuple(value for value in expected if value > selected.reference_date)
    included = [same_contract[value] for value in elapsed if value in same_contract]
    if not included:
        raise ValueError(f"same_contract_{timeframe.lower()}_constituents_unavailable")
    missing = tuple(value for value in elapsed if value not in same_contract)
    alternate_contract_before_start = any(
        value < included[0].reference_date and all_product.get(value) for value in missing
    )
    partial_contract_period = bool(alternate_contract_before_start)
    if partial_contract_period:
        status = "SAME_CONTRACT_PARTIAL_PERIOD"
    elif future:
        status = "IN_PROGRESS"
    else:
        status = "FINAL"
    quality = "PARTIAL_SAFE" if missing else "VALID"
    baseline = _complete_baseline(
        same_contract,
        start=start,
        timeframe=timeframe,
    )
    close = included[-1].close
    change_value = close - baseline.close if baseline is not None else None
    return_pct = (
        change_value / baseline.close * 100
        if baseline is not None and baseline.close != 0
        else None
    )
    return KrxNightAggregateBar(
        fact_id=(
            f"market:night_futures:{timeframe.lower()}:"
            f"{selected.series_code}:{selected.contract_code}:"
            f"{selected.reference_date.isoformat()}"
        ),
        instrument_root=instrument_root,
        series_code=selected.series_code,
        contract_code=selected.contract_code,
        contract_maturity=selected.contract_maturity,
        timeframe=timeframe,
        bar_start_date=start,
        reference_date=selected.reference_date,
        open=included[0].open,
        high=max(item.high for item in included),
        low=min(item.low for item in included),
        close=close,
        status=status,
        quality=quality,
        expected_dates=expected,
        included_dates=tuple(item.reference_date for item in included),
        missing_dates=missing,
        future_expected_dates=future,
        aggregation_start_date=included[0].reference_date,
        change_value=change_value,
        return_pct=return_pct,
        return_baseline_date=baseline.reference_date if baseline else None,
        return_baseline_close=baseline.close if baseline else None,
        return_baseline_semantic=(
            f"previous_completed_same_contract_{timeframe.lower()}_close" if baseline else None
        ),
        source_fact_ids=tuple(item.fact_id for item in included),
        source_raw_sha256=tuple(dict.fromkeys(item.source_raw_sha256 for item in included)),
        source_fingerprints=tuple(item.normalized_fingerprint for item in included),
    )


def build_same_contract_timeframes(
    root: Path,
    *,
    instrument_root: str,
    reference_date: date,
    daily_change_value: float | None = None,
    daily_change_pct: float | None = None,
    daily_baseline_date: date | None = None,
    daily_baseline_close: float | None = None,
) -> KrxNightTimeframes | None:
    lookback = reference_date.replace(day=1) - timedelta(days=45)
    all_bars = load_history(
        root,
        instrument_root=instrument_root,
        start=lookback,
        end=reference_date,
    )
    selected = resolve_near_month(all_bars, reference_date=reference_date)
    if selected is None:
        return None
    daily_baseline_valid = bool(
        daily_baseline_date is not None
        and daily_baseline_close is not None
        and math.isfinite(daily_baseline_close)
        and daily_baseline_close > 0
    )
    canonical_daily_change = (
        selected.close - daily_baseline_close if daily_baseline_valid else None
    )
    canonical_daily_return = (
        canonical_daily_change / daily_baseline_close * 100
        if canonical_daily_change is not None and daily_baseline_close is not None
        else None
    )
    canonical_daily_gap = (
        selected.open - daily_baseline_close if daily_baseline_valid else None
    )
    canonical_daily_gap_pct = (
        canonical_daily_gap / daily_baseline_close * 100
        if canonical_daily_gap is not None and daily_baseline_close is not None
        else None
    )
    daily_baseline_valid = bool(
        daily_baseline_valid
        and (
            daily_change_value is None
            or canonical_daily_change is not None
            and math.isclose(
                daily_change_value,
                canonical_daily_change,
                rel_tol=0,
                abs_tol=0.011,
            )
        )
        and (
            daily_change_pct is None
            or canonical_daily_return is not None
            and math.isclose(
                daily_change_pct,
                canonical_daily_return,
                rel_tol=0,
                abs_tol=0.011,
            )
        )
    )
    if not daily_baseline_valid:
        canonical_daily_change = None
        canonical_daily_return = None
        canonical_daily_gap = None
        canonical_daily_gap_pct = None
    same_contract = {
        bar.reference_date: bar
        for bar in all_bars
        if bar.contract_code == selected.contract_code and bar.bar_finality == "FINAL"
    }
    by_date: dict[date, tuple[KrxNightDailyBar, ...]] = {}
    for value in {bar.reference_date for bar in all_bars}:
        by_date[value] = tuple(bar for bar in all_bars if bar.reference_date == value)
    daily = KrxNightAggregateBar(
        fact_id=selected.fact_id,
        instrument_root=instrument_root,
        series_code=selected.series_code,
        contract_code=selected.contract_code,
        contract_maturity=selected.contract_maturity,
        timeframe="DAILY",
        bar_start_date=reference_date,
        reference_date=reference_date,
        open=selected.open,
        high=selected.high,
        low=selected.low,
        close=selected.close,
        status="FINAL",
        quality="VALID",
        expected_dates=(reference_date,),
        included_dates=(reference_date,),
        missing_dates=(),
        future_expected_dates=(),
        aggregation_start_date=reference_date,
        gap_value=canonical_daily_gap,
        gap_pct=canonical_daily_gap_pct,
        gap_baseline_date=daily_baseline_date if daily_baseline_valid else None,
        gap_baseline_close=daily_baseline_close if daily_baseline_valid else None,
        gap_baseline_semantic=(
            "night_open_minus_validated_preceding_regular_day_close"
            if daily_baseline_valid
            else None
        ),
        change_value=canonical_daily_change,
        return_pct=canonical_daily_return,
        return_baseline_date=daily_baseline_date if daily_baseline_valid else None,
        return_baseline_close=daily_baseline_close if daily_baseline_valid else None,
        return_baseline_semantic=(
            "completed_night_close_minus_immediately_preceding_day_close"
            if daily_baseline_valid
            else None
        ),
        source_fact_ids=(selected.fact_id,),
        source_raw_sha256=(selected.source_raw_sha256,),
        source_fingerprints=(selected.normalized_fingerprint,),
    )
    return KrxNightTimeframes(
        instrument_root=instrument_root,
        series_code=selected.series_code,
        contract_code=selected.contract_code,
        contract_maturity=selected.contract_maturity,
        reference_date=reference_date,
        daily=daily,
        weekly=_aggregate(
            instrument_root=instrument_root,
            selected=selected,
            timeframe="WEEKLY",
            same_contract=same_contract,
            all_product=by_date,
        ),
        monthly=_aggregate(
            instrument_root=instrument_root,
            selected=selected,
            timeframe="MONTHLY",
            same_contract=same_contract,
            all_product=by_date,
        ),
    )


def persist_live_probe_history(
    probe: object,
    *,
    root: Path | None = None,
) -> KrxNightHistoryUpdate:
    payloads = getattr(probe, "source_payloads_by_date", {})
    bodies = getattr(probe, "source_response_bodies_by_date", {})
    live_source = bool(getattr(probe, "live_source", False))
    if not live_source or not isinstance(payloads, dict) or not isinstance(bodies, dict):
        return KrxNightHistoryUpdate(source_mode="NOT_LIVE")
    target_root = root or default_krx_night_history_directory()
    stored = 0
    unchanged = 0
    normalized_count = 0
    rejected = 0
    hashes: list[str] = []
    errors: list[str] = []
    for query_date in sorted(bodies):
        body = bodies[query_date]
        if not isinstance(query_date, date) or not isinstance(body, bytes):
            errors.append("invalid_probe_capture_identity")
            continue
        try:
            receipt, normalized, stored_count = persist_krx_response(
                root=target_root,
                query_date=query_date,
                fetched_at=getattr(probe, "fetched_at"),
                http_status=200,
                raw_body=body,
            )
        except (OSError, ValueError) as exc:
            errors.append(f"{query_date}:{type(exc).__name__}")
            continue
        hashes.append(receipt.raw_payload_sha256)
        normalized_count += len(normalized.bars)
        rejected += len(normalized.rejections)
        stored += stored_count
        unchanged += len(normalized.bars) - stored_count
    return KrxNightHistoryUpdate(
        source_mode="LIVE_INCREMENTAL",
        request_count=len(bodies),
        raw_receipt_count=len(hashes),
        normalized_bar_count=normalized_count,
        stored_bar_count=stored,
        unchanged_bar_count=unchanged,
        rejection_count=rejected,
        raw_payload_sha256=tuple(hashes),
        errors=tuple(errors),
    )
