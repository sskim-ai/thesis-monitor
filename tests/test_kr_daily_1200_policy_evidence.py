from __future__ import annotations

from datetime import date
from types import SimpleNamespace

from scripts.kr_daily_1200_policy_evidence import TICKERS, _gates
from scripts.kr_price_structure_daily_nearest_repair import (
    _daily_session_diagnostics,
)


def _rows() -> list[dict[str, object]]:
    return [
        {
            "ticker": ticker,
            "coverage": {
                "daily": {
                    "requested_count": 1200,
                    "provider_limit": 1000,
                    "provider_returned_count": 1000,
                    "completed_count": 1000,
                    "actual_count": 1000,
                    "status": "PARTIAL_SAFE",
                    "denial_reason": "provider_limit",
                }
            },
            "daily_session_diagnostics": {
                "duplicate_count": 0,
                "ordering": "ascending",
            },
            "validator": {"errors": []},
            "old_render_new_validator": {
                "status": "FAIL" if ticker == "000660" else "PASS"
            },
        }
        for ticker in TICKERS
    ]


def test_daily_session_diagnostics_detects_duplicate_and_ordering() -> None:
    context = SimpleNamespace(
        daily_history=(
            SimpleNamespace(date=date(2026, 8, 25)),
            SimpleNamespace(date=date(2026, 8, 24)),
            SimpleNamespace(date=date(2026, 8, 24)),
        )
    )

    diagnostics = _daily_session_diagnostics(context)

    assert diagnostics["deduped_total"] == 2
    assert diagnostics["duplicate_count"] == 1
    assert diagnostics["ordering"] == "invalid"


def test_official_2026_closure_is_not_reported_as_data_gap() -> None:
    context = SimpleNamespace(
        daily_history=(
            SimpleNamespace(date=date(2026, 6, 2)),
            SimpleNamespace(date=date(2026, 6, 4)),
        )
    )

    diagnostics = _daily_session_diagnostics(context)

    assert diagnostics["gap_count"] == 0
    assert diagnostics["calendar_library_overexpectation_dates"] == ["2026-06-03"]


def test_verified_partial_safe_replay_passes_without_claiming_full() -> None:
    gates = _gates(_rows())

    assert gates["KR_DAILY_1200_COVERAGE"] == "VERIFIED_PARTIAL_SAFE_1000"
    assert gates["PROVIDER_LIMIT_MISREPORTED_AS_FULL"] == 0
    assert gates["KR_DAILY_1200_REPAIR"] == "REPLAY_PASS_READY_FOR_PREENABLE"


def test_replay_fails_when_provider_limit_response_is_not_exact() -> None:
    rows = _rows()
    rows[0]["coverage"]["daily"]["provider_returned_count"] = 999  # type: ignore[index]

    gates = _gates(rows)

    assert gates["KR_DAILY_1200_COVERAGE"] == "FAIL"
    assert gates["KR_DAILY_1200_REPAIR"] == "FAIL"


def test_replay_fails_on_duplicate_consumer_bar() -> None:
    rows = _rows()
    rows[0]["daily_session_diagnostics"]["duplicate_count"] = 1  # type: ignore[index]

    gates = _gates(rows)

    assert gates["CONSUMER_RESPONSE_DUPLICATE_BAR"] == 1
    assert gates["KR_DAILY_1200_REPAIR"] == "FAIL"
