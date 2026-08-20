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

    def __init__(self) -> None:
        self.calls: list[date] = []

    async def probe_publication_readiness(
        self,
        *,
        target_session: date,
        latest_completed_session: date,
        observed_at: datetime,
    ) -> KrxPublicationReadiness:
        self.calls.append(target_session)
        endpoints = [
            KrxEndpointReadiness(
                endpoint=endpoint,
                status="EMPTY",
                http_status=200,
                payload_sha256="a" * 64,
            )
            for endpoint in CORE_READINESS_ENDPOINTS
        ]
        return KrxPublicationReadiness(
            status="MARKET_COMPLETED_PROVIDER_PENDING",
            target_session=target_session,
            latest_completed_session=latest_completed_session,
            observed_at=observed_at,
            endpoints=endpoints,
            last_empty_at=observed_at,
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


def test_holiday_weekend_and_wrong_minute_skip_before_provider_access() -> None:
    cases = [
        datetime(2026, 8, 17, 16, 5, tzinfo=KST),
        datetime(2026, 8, 16, 8, 5, tzinfo=KST),
        datetime(2026, 8, 20, 16, 6, tzinfo=KST),
    ]

    reasons = [exact_slot_capture_request(value)[1] for value in cases]

    assert reasons == [
        "not_normal_xkrx_session",
        "not_normal_xkrx_session",
        "outside_exact_slot",
    ]


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
