from __future__ import annotations

import asyncio
import plistlib
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from app.jobs.observe_krx_publication import (
    exact_slot_capture_request,
    run_exact_slot_capture,
)
from app.providers.krx_publication_provider import (
    CORE_READINESS_ENDPOINTS,
    KrxEndpointReadiness,
    KrxPublicationReadiness,
)
from app.services.krx_publication_service import load_krx_publication_records


KST = ZoneInfo("Asia/Seoul")


class FakeProvider:
    configured = True

    def __init__(self, status: str = "MARKET_COMPLETED_PROVIDER_PENDING") -> None:
        self.calls: list[date] = []
        self.status = status

    async def probe_publication_readiness(
        self,
        *,
        target_session: date,
        latest_completed_session: date,
        observed_at: datetime,
    ) -> KrxPublicationReadiness:
        self.calls.append(target_session)
        ready = self.status == "PROVIDER_COMPLETE"
        endpoints = [
            KrxEndpointReadiness(
                endpoint=endpoint,
                status="READY" if ready else "EMPTY",
                http_status=200,
                row_count=1 if ready else 0,
                provider_dates=[target_session] if ready else [],
                payload_sha256="a" * 64,
            )
            for endpoint in CORE_READINESS_ENDPOINTS
        ]
        return KrxPublicationReadiness(
            status=self.status,
            target_session=target_session,
            latest_completed_session=latest_completed_session,
            observed_at=observed_at,
            endpoints=endpoints,
            last_empty_at=None if ready else observed_at,
            observed_complete_by=observed_at if ready else None,
            current_snapshot_promotable=ready,
        )


def test_same_day_exact_slot_targets_current_xkrx_session() -> None:
    request, reason = exact_slot_capture_request(
        datetime(2026, 8, 20, 16, 5, 12, tzinfo=KST)
    )

    assert reason == "scheduled"
    assert request is not None
    assert request.time_slot == "SAME_DAY_CLOSE_1605"
    assert request.target_session == date(2026, 8, 20)
    assert request.scheduled_for.minute == 5
    assert request.scheduled_for.second == 0


def test_next_morning_exact_slot_targets_preceding_xkrx_session() -> None:
    request, reason = exact_slot_capture_request(
        datetime(2026, 8, 20, 8, 5, 7, tzinfo=KST)
    )

    assert reason == "scheduled"
    assert request is not None
    assert request.time_slot == "NEXT_MORNING_0805"
    assert request.target_session == date(2026, 8, 19)


def test_holiday_close_weekend_close_and_wrong_minute_skip_before_provider_access() -> None:
    cases = [
        datetime(2026, 8, 17, 16, 5, tzinfo=KST),
        datetime(2026, 8, 16, 16, 5, tzinfo=KST),
        datetime(2026, 8, 20, 16, 6, tzinfo=KST),
    ]

    reasons = [exact_slot_capture_request(value)[1] for value in cases]

    assert reasons == [
        "no_valid_role_target",
        "no_valid_role_target",
        "outside_exact_slot",
    ]


def test_saturday_and_sunday_0805_target_latest_completed_friday_session() -> None:
    saturday, saturday_reason = exact_slot_capture_request(
        datetime(2026, 8, 22, 8, 5, tzinfo=KST)
    )
    sunday, sunday_reason = exact_slot_capture_request(
        datetime(2026, 8, 23, 8, 5, tzinfo=KST)
    )

    assert saturday_reason == sunday_reason == "scheduled"
    assert saturday is not None and sunday is not None
    assert saturday.target_session == sunday.target_session == date(2026, 8, 21)


def test_repeated_same_slot_is_noop_before_provider_call(tmp_path: Path) -> None:
    provider = FakeProvider()
    observed_at = datetime(2026, 8, 22, 8, 5, tzinfo=KST)

    first = asyncio.run(
        run_exact_slot_capture(
            as_of=observed_at,
            capture_origin="launchd_calendar",
            telemetry_directory=tmp_path,
            provider=provider,
        )
    )
    second = asyncio.run(
        run_exact_slot_capture(
            as_of=observed_at,
            capture_origin="launchd_calendar",
            telemetry_directory=tmp_path,
            provider=provider,
        )
    )

    assert first["status"] == "RECORDED"
    assert second["reason"] == "target_already_observed"
    assert provider.calls == [date(2026, 8, 21)]


def test_sunday_skips_terminal_saturday_target_but_retries_pending_target(
    tmp_path: Path,
) -> None:
    complete = FakeProvider(status="PROVIDER_COMPLETE")
    saturday = datetime(2026, 8, 22, 8, 5, tzinfo=KST)
    sunday = datetime(2026, 8, 23, 8, 5, tzinfo=KST)
    asyncio.run(
        run_exact_slot_capture(
            as_of=saturday,
            capture_origin="launchd_calendar",
            telemetry_directory=tmp_path / "complete",
            provider=complete,
        )
    )

    terminal = asyncio.run(
        run_exact_slot_capture(
            as_of=sunday,
            capture_origin="launchd_calendar",
            telemetry_directory=tmp_path / "complete",
            provider=complete,
        )
    )

    pending = FakeProvider()
    asyncio.run(
        run_exact_slot_capture(
            as_of=saturday,
            capture_origin="launchd_calendar",
            telemetry_directory=tmp_path / "pending",
            provider=pending,
        )
    )
    retried = asyncio.run(
        run_exact_slot_capture(
            as_of=sunday,
            capture_origin="launchd_calendar",
            telemetry_directory=tmp_path / "pending",
            provider=pending,
        )
    )

    assert terminal["reason"] == "target_already_terminal"
    assert complete.calls == [date(2026, 8, 21)]
    assert retried["status"] == "RECORDED"
    assert pending.calls == [date(2026, 8, 21), date(2026, 8, 21)]


def test_wrong_minute_run_writes_nothing_and_calls_nothing(tmp_path: Path) -> None:
    provider = FakeProvider()

    result = asyncio.run(
        run_exact_slot_capture(
            as_of=datetime(2026, 8, 20, 16, 6, tzinfo=KST),
            capture_origin="launchd_calendar",
            telemetry_directory=tmp_path,
            provider=provider,
        )
    )

    assert result["status"] == "SKIPPED"
    assert result["provider_calls"] == 0
    assert provider.calls == []
    assert list(tmp_path.iterdir()) == []


def test_natural_exact_slot_writes_sanitized_append_only_record(tmp_path: Path) -> None:
    provider = FakeProvider()

    result = asyncio.run(
        run_exact_slot_capture(
            as_of=datetime(2026, 8, 20, 16, 5, 4, tzinfo=KST),
            capture_origin="launchd_calendar",
            telemetry_directory=tmp_path,
            provider=provider,
        )
    )

    path = tmp_path / "2026-08-20.jsonl"
    records = load_krx_publication_records(path)
    assert result["status"] == "RECORDED"
    assert result["user_visible_integration"] is False
    assert result["credential_exposure"] == 0
    assert result["structured_snapshot_status"] == "PERSISTED_PUBLICATION_PENDING"
    assert (tmp_path / "structured-market-context" / "kr" / "2026-08-20.json").exists()
    assert provider.calls == [date(2026, 8, 20)]
    assert len(records) == 1
    assert records[0].capture_origin == "launchd_calendar"
    assert records[0].time_slot == "SAME_DAY_CLOSE_1605"
    assert "AUTH_KEY" not in path.read_text(encoding="utf-8")


def test_launch_agent_is_telemetry_only_and_has_no_run_at_load() -> None:
    root = Path(__file__).resolve().parents[1]
    with (
        root / "ops/com.seungsoo.thesis-monitor.krx-publication-telemetry.plist"
    ).open("rb") as stream:
        config = plistlib.load(stream)

    command = config["ProgramArguments"][-1]
    assert "app.jobs.observe_krx_publication" in command
    assert "monitor_daily" not in command
    assert "telegram" not in command.lower()
    assert config["StartCalendarInterval"] == [
        {"Hour": 8, "Minute": 5},
        {"Hour": 16, "Minute": 5},
    ]
    assert "RunAtLoad" not in config
