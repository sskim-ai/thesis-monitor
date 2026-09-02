from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from app.jobs.night_futures_publication_observer import (
    run_night_futures_publication_observer,
)
from app.macro.providers.base import MacroProviderResult
from app.services.night_futures_publication_telemetry_service import (
    build_attempt_record,
    load_group_attempts,
    observation_group_id,
    record_attempt_best_effort,
)


KST = ZoneInfo("Asia/Seoul")
MARKET_DATE = date(2026, 8, 21)
EXPECTED = date(2026, 8, 21)
PRECEDING = date(2026, 8, 20)


def _at(hour: int, minute: int) -> datetime:
    return datetime(2026, 8, 21, hour, minute, tzinfo=KST)


def _at_date(day: int, hour: int, minute: int) -> datetime:
    return datetime(2026, 8, day, hour, minute, tzinfo=KST)


def _at_date_second(day: int, hour: int, minute: int, second: int) -> datetime:
    return datetime(2026, 8, day, hour, minute, second, tzinfo=KST)


def _product(
    name: str,
    *,
    returned: date | None,
    ready: bool,
    reason: str | None = None,
) -> dict[str, object]:
    return {
        "product": name,
        "expected_night_bas_dd": EXPECTED.isoformat(),
        "returned_night_bas_dd": returned.isoformat() if returned else None,
        "matched_day_bas_dd": PRECEDING.isoformat() if ready else None,
        "contract_code": f"{name}-SEP",
        "maturity": "2026-09",
        "row_state": (
            "EXPECTED_SESSION_PRESENT"
            if returned == EXPECTED
            else "STALE_PRIOR_SESSION_PRESENT"
        ),
        "readiness": "READY" if ready else "NOT_READY",
        "rejection_reason": reason,
        "provider_change_crosscheck_status": "PASS" if ready else "NOT_OBSERVED",
    }


def _telemetry(
    *products: dict[str, object],
    night_dates: tuple[date, ...] = (EXPECTED,),
    row_count: int = 4,
    reason: str | None = None,
) -> dict[str, object]:
    dates = sorted({PRECEDING, *night_dates})
    return {
        "status": "ok" if row_count else "unavailable",
        "reason": reason,
        "row_count": row_count,
        "parsed_row_count": row_count,
        "returned_business_dates": [item.isoformat() for item in dates],
        "returned_night_session_dates": [item.isoformat() for item in night_dates],
        "product_statuses": list(products),
        "parser_status": "PASS" if row_count else "NOT_OBSERVED",
        "canonicalization_status": "PASS" if products else "NOT_OBSERVED",
        "provider_change_crosscheck_status": "PASS" if products else "NOT_OBSERVED",
        "date_statuses": [
            {
                "query_date": item.isoformat(),
                "row_count": 2,
                "http_status": 200,
                "raw_payload_sha256": str(index + 1) * 64,
            }
            for index, item in enumerate(dates)
        ],
    }


def _result(telemetry: dict[str, object]) -> MacroProviderResult:
    return MacroProviderResult(provider="krx_night_futures", telemetry=telemetry)


def _record(
    telemetry: dict[str, object],
    *,
    role: str = "production_gate_attempt_1",
) -> object:
    return build_attempt_record(
        market_date=MARKET_DATE,
        started_at=_at(8, 5),
        ended_at=_at(8, 6),
        role=role,
        production_or_observer="production",
        expected_session=EXPECTED,
        result=_result(telemetry),
    )


def test_attempt_preserves_distinct_business_dates_and_per_product_readiness() -> None:
    record = _record(
        _telemetry(
            _product("KOSPI200", returned=EXPECTED, ready=True),
            _product("KOSDAQ150", returned=EXPECTED, ready=True),
            night_dates=(date(2026, 8, 20), EXPECTED),
        )
    )

    assert record.provider_night_business_dates_returned == [
        date(2026, 8, 20),
        EXPECTED,
    ]
    assert record.ready_product_count == 2
    assert record.terminal_classification == "EXPECTED_SESSION_PRESENT_READY"
    assert {item.product for item in record.per_product} == {
        "KOSPI200",
        "KOSDAQ150",
    }
    assert record.raw_sha256 is not None
    assert record.expected_preceding_day_bas_dd == PRECEDING


def test_attempt_classifies_empty_stale_missing_day_conflict_and_partial() -> None:
    empty = _record(_telemetry(row_count=0, night_dates=()))
    stale = _record(
        _telemetry(
            _product(
                "KOSPI200",
                returned=date(2026, 8, 20),
                ready=False,
                reason="expected_session_absent",
            ),
            _product(
                "KOSDAQ150",
                returned=date(2026, 8, 20),
                ready=False,
                reason="expected_session_absent",
            ),
            night_dates=(date(2026, 8, 20),),
        )
    )
    missing_day = _record(
        _telemetry(
            _product(
                "KOSPI200",
                returned=EXPECTED,
                ready=False,
                reason="matching_preceding_day_contract_unavailable",
            ),
            _product(
                "KOSDAQ150",
                returned=EXPECTED,
                ready=False,
                reason="matching_preceding_day_contract_unavailable",
            ),
        )
    )
    conflict = _record(
        _telemetry(
            _product(
                "KOSPI200",
                returned=EXPECTED,
                ready=False,
                reason="provider_change_conflict",
            ),
            _product(
                "KOSDAQ150",
                returned=EXPECTED,
                ready=False,
                reason="provider_change_conflict",
            ),
        )
    )
    partial = _record(
        _telemetry(
            _product("KOSPI200", returned=EXPECTED, ready=True),
            _product(
                "KOSDAQ150",
                returned=EXPECTED,
                ready=False,
                reason="matching_preceding_day_contract_unavailable",
            ),
        )
    )

    assert empty.terminal_classification == "PROVIDER_EMPTY"
    assert stale.terminal_classification == "STALE_PRIOR_SESSION_PRESENT"
    assert (
        missing_day.terminal_classification
        == "EXPECTED_SESSION_PRESENT_NO_MATCHING_DAY"
    )
    assert (
        conflict.terminal_classification
        == "EXPECTED_SESSION_PRESENT_PROVIDER_CONFLICT"
    )
    assert partial.terminal_classification == "EXPECTED_SESSION_PRESENT_PARTIAL_READY"


def test_attempt_archive_is_idempotent_and_has_no_production_side_effect(
    tmp_path: Path,
) -> None:
    result = _result(
        _telemetry(
            _product("KOSPI200", returned=EXPECTED, ready=True),
            _product("KOSDAQ150", returned=EXPECTED, ready=True),
        )
    )
    kwargs = {
        "market_date": MARKET_DATE,
        "started_at": _at(8, 5),
        "ended_at": _at(8, 6),
        "role": "production_gate_attempt_1",
        "production_or_observer": "production",
        "expected_session": EXPECTED,
        "result": result,
        "directory": tmp_path,
    }

    first = record_attempt_best_effort(**kwargs)
    second = record_attempt_best_effort(**kwargs)
    group_id = observation_group_id(MARKET_DATE, EXPECTED)
    attempts = load_group_attempts(tmp_path, MARKET_DATE, group_id)

    assert first["status"] == "RECORDED"
    assert second["status"] == "IDEMPOTENT_REPLAY"
    assert len(attempts) == 1
    assert first["production_effect"] == 0


def test_archive_write_failure_is_isolated(monkeypatch, tmp_path: Path) -> None:
    def fail_write(_path, _payload):
        raise OSError("read-only")

    monkeypatch.setattr(
        "app.services.night_futures_publication_telemetry_service._atomic_json",
        fail_write,
    )
    result = record_attempt_best_effort(
        market_date=MARKET_DATE,
        started_at=_at(8, 5),
        ended_at=_at(8, 6),
        role="production_gate_attempt_1",
        production_or_observer="production",
        expected_session=EXPECTED,
        result=_result(_telemetry(row_count=0, night_dates=())),
        directory=tmp_path,
    )

    assert result == {
        "status": "TELEMETRY_WRITE_FAILED",
        "error": "OSError",
        "production_effect": 0,
    }


class _Provider:
    name = "krx_night_futures"

    def __init__(self, result: MacroProviderResult) -> None:
        self.result = result
        self.calls = 0

    async def collect(self, _as_of: datetime) -> MacroProviderResult:
        self.calls += 1
        return self.result


@pytest.mark.anyio
async def test_observer_stops_after_ready_and_never_writes_production(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(
        "app.jobs.night_futures_publication_observer.expected_latest_completed_krx_session",
        lambda _run_date: EXPECTED,
    )
    provider = _Provider(
        _result(
            _telemetry(
                _product("KOSPI200", returned=EXPECTED, ready=True),
                _product("KOSDAQ150", returned=EXPECTED, ready=True),
            )
        )
    )

    first = await run_night_futures_publication_observer(
        as_of=_at(8, 45),
        provider=provider,
        telemetry_directory=tmp_path,
    )
    second = await run_night_futures_publication_observer(
        as_of=_at(9, 15),
        provider=provider,
        telemetry_directory=tmp_path,
    )

    assert first["classification"] == "EXPECTED_SESSION_PRESENT_READY"
    assert first["terminal_state"] == "READY_SHORTLY_AFTER_DEADLINE"
    assert first["production_market_summary_writes"] == 0
    assert first["telegram_writes"] == 0
    assert second["reason"] == "target_already_terminal"
    assert provider.calls == 1


@pytest.mark.anyio
async def test_horizon_records_unknown_without_continuous_polling(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(
        "app.jobs.night_futures_publication_observer.expected_latest_completed_krx_session",
        lambda _run_date: EXPECTED,
    )
    provider = _Provider(_result(_telemetry(row_count=0, night_dates=())))

    first = await run_night_futures_publication_observer(
        as_of=_at(8, 45), provider=provider, telemetry_directory=tmp_path
    )
    horizon = await run_night_futures_publication_observer(
        as_of=_at(9, 15), provider=provider, telemetry_directory=tmp_path
    )

    assert first["terminal_state"] is None
    assert horizon["terminal_state"] == "NOT_READY_WITHIN_OBSERVER_HORIZON"
    assert provider.calls == 2


@pytest.mark.anyio
async def test_saturday_observer_reaches_role_target_and_same_slot_is_idempotent(
    tmp_path: Path,
) -> None:
    provider = _Provider(_result(_telemetry(row_count=0, night_dates=())))
    observed_at = _at_date(22, 8, 45)

    first = await run_night_futures_publication_observer(
        as_of=observed_at,
        provider=provider,
        telemetry_directory=tmp_path,
    )
    second = await run_night_futures_publication_observer(
        as_of=observed_at,
        provider=provider,
        telemetry_directory=tmp_path,
    )

    assert first["status"] == "RECORDED"
    assert first["expected_night_bas_dd"] == "2026-08-21"
    assert second["reason"] == "target_already_observed"
    assert provider.calls == 1


@pytest.mark.anyio
async def test_same_role_target_restart_with_later_seconds_is_idempotent(
    tmp_path: Path,
) -> None:
    provider = _Provider(_result(_telemetry(row_count=0, night_dates=())))

    first = await run_night_futures_publication_observer(
        as_of=_at_date_second(22, 8, 45, 1),
        provider=provider,
        telemetry_directory=tmp_path,
    )
    second = await run_night_futures_publication_observer(
        as_of=_at_date_second(22, 8, 45, 49),
        provider=provider,
        telemetry_directory=tmp_path,
    )

    assert first["status"] == "RECORDED"
    assert second["status"] == "SKIPPED"
    assert second["reason"] == "target_already_observed"
    assert second["provider_calls"] == 0
    assert provider.calls == 1


@pytest.mark.anyio
async def test_sunday_skips_same_target_after_saturday_horizon_terminal(
    tmp_path: Path,
) -> None:
    provider = _Provider(_result(_telemetry(row_count=0, night_dates=())))

    await run_night_futures_publication_observer(
        as_of=_at_date(22, 8, 45),
        provider=provider,
        telemetry_directory=tmp_path,
    )
    saturday_horizon = await run_night_futures_publication_observer(
        as_of=_at_date(22, 9, 15),
        provider=provider,
        telemetry_directory=tmp_path,
    )
    sunday = await run_night_futures_publication_observer(
        as_of=_at_date(23, 8, 45),
        provider=provider,
        telemetry_directory=tmp_path,
    )

    assert saturday_horizon["terminal_state"] == "NOT_READY_WITHIN_OBSERVER_HORIZON"
    assert sunday["reason"] == "target_already_terminal"
    assert provider.calls == 2


def test_launch_agent_has_two_post_production_slots_only() -> None:
    path = Path(
        "ops/com.seungsoo.thesis-monitor.night-futures-publication-observer.plist"
    )
    text = path.read_text(encoding="utf-8")

    assert "night_futures_publication_observer" in text
    assert text.count("<key>Hour</key>") == 2
    assert "<key>Minute</key><integer>45</integer>" in text
    assert "<key>Minute</key><integer>15</integer>" in text
    assert "telegram" not in text.lower()
