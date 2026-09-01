from __future__ import annotations

from datetime import date

import httpx
import pytest

from app.services.ohlcv_client import OhlcvClient
from app.services.ohlcv_provider_integrity_service import (
    MalformedRefetchOutcome,
    OhlcvViolation,
    audit_uniform_adjustment,
    inspect_normalized_ohlcv_rows,
)


def _bar(
    *,
    bar_date: str = "2026-08-31",
    open_price: object = 100,
    high: object = 105,
    low: object = 95,
    close: object = 102,
    volume: object = 1_000,
) -> dict[str, object]:
    return {
        "date": bar_date,
        "open": open_price,
        "high": high,
        "low": low,
        "close": close,
        "volume": volume,
    }


def _payload(period: str, bars: list[dict[str, object]]) -> dict[str, object]:
    return {
        "resolved_symbol": {"code": "TEST"},
        "meta": {"provider": "kiwoom", "adjusted": True},
        "periods": {period: bars},
    }


def _audit() -> dict[str, object]:
    return {
        "request_count": 0,
        "success_count": 0,
        "retry_count": 0,
        "connection_error_count": 0,
        "timeout_count": 0,
        "server_error_count": 0,
        "non_retryable_error_count": 0,
        "cache_use_count": 0,
        "failure_classes": [],
    }


@pytest.mark.parametrize(
    ("bar", "expected"),
    (
        (_bar(high=101, close=102), OhlcvViolation.HIGH_LT_CLOSE),
        (_bar(low=101), OhlcvViolation.LOW_GT_OPEN),
        (_bar(high=90, low=95), OhlcvViolation.LOW_GT_HIGH),
        (_bar(open_price=float("nan")), OhlcvViolation.NONFINITE_VALUE),
    ),
)
def test_malformed_ohlc_negative_controls_fail_closed(
    bar: dict[str, object],
    expected: OhlcvViolation,
) -> None:
    inspection = inspect_normalized_ohlcv_rows([bar], timeframe="daily")

    assert inspection.valid is False
    assert expected in {issue.violation for issue in inspection.issues}
    assert inspection.invalid_row_count == 1


def test_duplicate_conflict_and_future_bar_fail_closed() -> None:
    first = _bar()
    conflicting = _bar(close=103)

    inspection = inspect_normalized_ohlcv_rows(
        [first, conflicting],
        timeframe="daily",
        cutoff=date(2026, 8, 30),
    )

    violations = {issue.violation for issue in inspection.issues}
    assert OhlcvViolation.DUPLICATE_CONFLICT in violations
    assert OhlcvViolation.FUTURE_BAR in violations


def test_provider_schema_drift_fails_closed() -> None:
    renamed_high = _bar()
    renamed_high["highest"] = renamed_high.pop("high")

    inspection = inspect_normalized_ohlcv_rows([renamed_high], timeframe="daily")

    assert inspection.valid is False
    assert {issue.violation for issue in inspection.issues} == {
        OhlcvViolation.MISSING_OHLC_FIELD
    }


@pytest.mark.anyio
async def test_transient_malformed_content_gets_one_bounded_refetch() -> None:
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        bars = [_bar(high=101, close=102)] if calls == 1 else [_bar()]
        return httpx.Response(200, json=_payload("daily", bars))

    audit = _audit()
    client = OhlcvClient(transport=httpx.MockTransport(handler))
    async with httpx.AsyncClient(
        base_url="http://ohlcv.test",
        transport=client.transport,
    ) as http_client:
        _, bars = await client._request_period(
            http_client,
            "TEST",
            "daily",
            1,
            acquisition_audit=audit,
        )

    assert calls == 2
    assert bars[0]["high"] == 105
    assert audit["malformed_refetch_count"] == 1
    assert audit["transient_malformed_recovered_count"] == 1
    event = audit["integrity_events"][0]  # type: ignore[index]
    assert event["outcome"] == MalformedRefetchOutcome.PROVIDER_REFETCH_RECOVERED
    assert event["first_payload_fingerprint"] != event["second_payload_fingerprint"]


@pytest.mark.anyio
async def test_stable_bad_provider_remains_invalid_without_synthetic_repair() -> None:
    calls = 0
    malformed = _bar(open_price=106, high=105)

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(200, json=_payload("daily", [malformed]))

    audit = _audit()
    client = OhlcvClient(transport=httpx.MockTransport(handler))
    async with httpx.AsyncClient(
        base_url="http://ohlcv.test",
        transport=client.transport,
    ) as http_client:
        _, bars = await client._request_period(
            http_client,
            "TEST",
            "daily",
            1,
            acquisition_audit=audit,
        )

    assert calls == 2
    assert bars[0]["open"] == 106
    assert bars[0]["high"] == 105
    assert audit["stable_malformed_unresolved_count"] == 1
    event = audit["integrity_events"][0]  # type: ignore[index]
    assert event["outcome"] == MalformedRefetchOutcome.STABLE_BAD_SOURCE


@pytest.mark.parametrize(
    ("price_factor", "volume_factor"),
    (("0.5", "2"), ("5", "0.2"), ("1", "1")),
)
def test_corporate_action_adjustment_fixtures_require_uniform_ohlc(
    price_factor: str,
    volume_factor: str,
) -> None:
    raw = _bar(volume=1_000)
    adjusted = {
        **raw,
        **{
            field: float(str(raw[field])) * float(price_factor)
            for field in ("open", "high", "low", "close")
        },
        "volume": float(str(raw["volume"])) * float(volume_factor),
    }

    audit = audit_uniform_adjustment(raw, adjusted)

    assert audit.compatible is True
    assert audit.price_factor == price_factor
    assert audit.volume_factor == volume_factor
    assert inspect_normalized_ohlcv_rows([adjusted], timeframe="daily").valid is True


def test_partial_field_adjustment_is_rejected() -> None:
    raw = _bar()
    adjusted = {**raw, "close": 51}

    audit = audit_uniform_adjustment(raw, adjusted)

    assert audit.compatible is False
    assert audit.reason == "mixed_field_adjustment"
