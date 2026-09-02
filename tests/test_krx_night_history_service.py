from __future__ import annotations

import hashlib
import json
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import pytest

from app.services.krx_night_history_service import (
    KRX_NIGHT_OHLC_FIELD_MAPPING,
    KrxNightDailyBar,
    KrxNightHistoryConflictError,
    build_same_contract_timeframes,
    load_history,
    normalize_krx_night_daily_bars,
    persist_krx_response,
    preserve_raw_krx_response,
    resolve_near_month,
    store_normalized_bar,
)
from app.services.market_session import is_exchange_session_date


RAW_SHA = "a" * 64


def _row(
    *,
    product: str = "코스피200 선물",
    name: str = "코스피200 F 202609 (야간)",
    contract: str = "A0169000",
    day: str = "20260901",
    open_: str = "1067.00",
    high: str = "1072.45",
    low: str = "1053.80",
    close: str = "1064.50",
) -> dict[str, str]:
    return {
        "BAS_DD": day,
        "PROD_NM": product,
        "MKT_NM": "야간",
        "ISU_CD": contract,
        "ISU_NM": name,
        "TDD_OPNPRC": open_,
        "TDD_HGPRC": high,
        "TDD_LWPRC": low,
        "TDD_CLSPRC": close,
        "ACC_TRDVOL": "22349",
        "CMPPREVDD_PRC": "-3.35",
    }


def _bar(
    day: date,
    *,
    product: str = "KOSPI200",
    contract: str = "A0169000",
    maturity: str = "2026-09",
    open_: float = 100.0,
    high: float = 103.0,
    low: float = 99.0,
    close: float = 101.0,
    fingerprint: str | None = None,
) -> KrxNightDailyBar:
    series = "KRX_KOSPI200_NIGHT_FUT" if product == "KOSPI200" else "KRX_KOSDAQ150_NIGHT_FUT"
    identity = f"{day}:NIGHT:{contract}"
    derived_fingerprint = hashlib.sha256(
        f"{identity}|{open_}|{high}|{low}|{close}".encode()
    ).hexdigest()
    return KrxNightDailyBar(
        fact_id=f"market:night_futures:daily:{series}:{contract}:{day}",
        instrument_root=product,
        series_code=series,
        contract_code=contract,
        contract_maturity=maturity,
        reference_date=day,
        open=open_,
        high=high,
        low=low,
        close=close,
        volume=100,
        official_change=1.0,
        bar_finality="FINAL",
        source_row_identity=identity,
        source_raw_sha256=RAW_SHA,
        source_raw_relative_path=f"raw/{day}.json",
        normalized_fingerprint=fingerprint or derived_fingerprint,
        fetched_at=datetime(2026, 9, 2, 8, tzinfo=UTC),
    )


def test_official_krx_ohlc_field_mapping_is_explicit() -> None:
    assert KRX_NIGHT_OHLC_FIELD_MAPPING["open"] == "TDD_OPNPRC"
    assert KRX_NIGHT_OHLC_FIELD_MAPPING["high"] == "TDD_HGPRC"
    assert KRX_NIGHT_OHLC_FIELD_MAPPING["low"] == "TDD_LWPRC"
    assert KRX_NIGHT_OHLC_FIELD_MAPPING["close"] == "TDD_CLSPRC"
    assert KRX_NIGHT_OHLC_FIELD_MAPPING["session"] == "MKT_NM"


def test_run51_official_rows_normalize_exact_ohlc_without_repair() -> None:
    payload = {
        "OutBlock_1": [
            _row(),
            _row(
                product="코스닥150 선물",
                name="코스닥150 F 202609 (야간)",
                contract="A0669000",
                open_="1440.00",
                high="1447.00",
                low="1415.50",
                close="1432.80",
            ),
        ]
    }
    result = normalize_krx_night_daily_bars(
        payload=payload,
        query_date=date(2026, 9, 1),
        fetched_at=datetime(2026, 9, 2, 8, tzinfo=UTC),
        raw_payload_sha256=RAW_SHA,
        raw_relative_path="raw/2026/09/01/a.json",
    )

    assert len(result.bars) == 2
    assert result.rejections == ()
    by_product = {bar.instrument_root: bar for bar in result.bars}
    assert (
        by_product["KOSPI200"].open,
        by_product["KOSPI200"].high,
        by_product["KOSPI200"].low,
        by_product["KOSPI200"].close,
    ) == (1067.0, 1072.45, 1053.8, 1064.5)
    assert (
        by_product["KOSDAQ150"].open,
        by_product["KOSDAQ150"].high,
        by_product["KOSDAQ150"].low,
        by_product["KOSDAQ150"].close,
    ) == (1440.0, 1447.0, 1415.5, 1432.8)


def test_malformed_ohlc_is_rejected_without_clipping_or_swapping() -> None:
    result = normalize_krx_night_daily_bars(
        payload={"OutBlock_1": [_row(open_="1100", high="1090")]},
        query_date=date(2026, 9, 1),
        fetched_at=datetime(2026, 9, 2, 8, tzinfo=UTC),
        raw_payload_sha256=RAW_SHA,
        raw_relative_path="raw/a.json",
    )

    assert result.bars == ()
    assert len(result.rejections) == 1
    assert result.rejections[0].reason == "ohlc_relation_invalid"


def test_raw_response_is_byte_preserved_and_idempotent(tmp_path: Path) -> None:
    body = json.dumps({"OutBlock_1": [_row()]}, ensure_ascii=False).encode()
    first, _payload, created = preserve_raw_krx_response(
        root=tmp_path,
        query_date=date(2026, 9, 1),
        fetched_at=datetime(2026, 9, 2, 8, tzinfo=UTC),
        http_status=200,
        raw_body=body,
    )
    second, _payload, created_again = preserve_raw_krx_response(
        root=tmp_path,
        query_date=date(2026, 9, 1),
        fetched_at=datetime(2026, 9, 2, 8, tzinfo=UTC),
        http_status=200,
        raw_body=body,
    )

    assert created is True
    assert created_again is False
    assert first.raw_payload_sha256 == second.raw_payload_sha256
    assert (tmp_path / first.raw_relative_path).read_bytes() == body


def test_daily_identity_does_not_overwrite_a_conflict(tmp_path: Path) -> None:
    first = _bar(date(2026, 9, 1), fingerprint="1" * 64)
    conflict = _bar(date(2026, 9, 1), close=102.0, fingerprint="2" * 64)
    assert store_normalized_bar(tmp_path, first) is True
    assert store_normalized_bar(tmp_path, first) is False
    with pytest.raises(KrxNightHistoryConflictError):
        store_normalized_bar(tmp_path, conflict)


def test_near_month_is_resolved_from_reference_date_not_hardcoded() -> None:
    bars = (
        _bar(
            date(2026, 12, 1),
            contract="DEC",
            maturity="2026-12",
        ),
        _bar(
            date(2026, 12, 1),
            contract="MAR",
            maturity="2027-03",
        ),
    )
    selected = resolve_near_month(bars, reference_date=date(2026, 12, 1))
    assert selected is not None
    assert selected.contract_code == "DEC"


def test_same_contract_weekly_monthly_use_xkrx_constituents_only(
    tmp_path: Path,
) -> None:
    start = date(2026, 8, 1)
    sessions = [
        start + timedelta(days=offset)
        for offset in range(31)
        if is_exchange_session_date("XKRX", start + timedelta(days=offset))
    ]
    for index, session in enumerate(sessions):
        store_normalized_bar(
            tmp_path,
            _bar(
                session,
                open_=100 + index,
                high=103 + index,
                low=99 + index,
                close=101 + index,
            ),
        )
    store_normalized_bar(
        tmp_path,
        _bar(
            date(2026, 9, 1),
            open_=1067.0,
            high=1072.45,
            low=1053.8,
            close=1064.5,
        ),
    )
    store_normalized_bar(
        tmp_path,
        _bar(
            date(2026, 9, 1),
            contract="DEC",
            maturity="2026-12",
            open_=2000,
            high=2100,
            low=1900,
            close=2050,
        ),
    )

    frames = build_same_contract_timeframes(
        tmp_path,
        instrument_root="KOSPI200",
        reference_date=date(2026, 9, 1),
        daily_change_value=-3.35,
        daily_change_pct=-0.3139,
        daily_baseline_date=date(2026, 8, 31),
        daily_baseline_close=1067.85,
    )

    assert frames is not None
    assert frames.contract_code == "A0169000"
    assert frames.daily.close == 1064.5
    assert frames.weekly.status == "IN_PROGRESS"
    assert frames.weekly.included_dates == (
        date(2026, 8, 31),
        date(2026, 9, 1),
    )
    assert frames.weekly.high == 1072.45
    assert frames.weekly.return_baseline_date == date(2026, 8, 28)
    assert frames.monthly.status == "IN_PROGRESS"
    assert frames.monthly.included_dates == (date(2026, 9, 1),)
    assert frames.monthly.return_baseline_date == date(2026, 8, 31)
    assert frames.monthly.return_pct == pytest.approx(
        (1064.5 - (101 + len(sessions) - 1)) / (101 + len(sessions) - 1) * 100
    )
    assert 2050 not in {frames.weekly.high, frames.monthly.high}


def test_missing_elapsed_constituent_is_partial_safe(tmp_path: Path) -> None:
    for day in (date(2026, 8, 28), date(2026, 9, 1)):
        store_normalized_bar(tmp_path, _bar(day))
    frames = build_same_contract_timeframes(
        tmp_path,
        instrument_root="KOSPI200",
        reference_date=date(2026, 9, 1),
    )
    assert frames is not None
    assert frames.weekly.quality == "PARTIAL_SAFE"
    assert frames.weekly.missing_dates == (date(2026, 8, 31),)


def test_persist_response_stores_both_products_and_raw_receipt(tmp_path: Path) -> None:
    body = json.dumps(
        {
            "OutBlock_1": [
                _row(),
                _row(
                    product="코스닥150 선물",
                    name="코스닥150 F 202609 (야간)",
                    contract="A0669000",
                    open_="1440",
                    high="1447",
                    low="1415.5",
                    close="1432.8",
                ),
            ]
        },
        ensure_ascii=False,
    ).encode()
    receipt, normalized, stored = persist_krx_response(
        root=tmp_path,
        query_date=date(2026, 9, 1),
        fetched_at=datetime(2026, 9, 2, 8, tzinfo=UTC),
        http_status=200,
        raw_body=body,
    )
    assert receipt.row_count == 2
    assert len(normalized.bars) == 2
    assert stored == 2
    assert len(load_history(tmp_path, instrument_root="KOSPI200")) == 1
    assert len(load_history(tmp_path, instrument_root="KOSDAQ150")) == 1
