from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from app.jobs.probe_krx_night_futures import expected_latest_completed_krx_session
from app.macro.providers.base import MacroProvider
from app.macro.providers.krx import KrxNightFuturesProvider
from app.services.market_session import is_exchange_session_date
from app.services.night_futures_publication_telemetry_service import (
    DEFAULT_OBSERVER_HORIZON,
    default_telemetry_directory,
    load_group_attempts,
    observation_group_id,
    record_attempt_best_effort,
)


KST = ZoneInfo("Asia/Seoul")
OBSERVER_SLOTS = {(8, 45): "post_deadline_0845", (9, 15): "horizon_0915"}


def _slot(current: datetime) -> str | None:
    return OBSERVER_SLOTS.get((current.hour, current.minute))


async def run_night_futures_publication_observer(
    *,
    as_of: datetime | None = None,
    provider: MacroProvider | None = None,
    telemetry_directory: Path | None = None,
) -> dict[str, object]:
    observed_at = as_of or datetime.now(timezone.utc)
    if observed_at.tzinfo is None:
        return {
            "status": "SKIPPED",
            "reason": "timezone_unverified",
            "provider_calls": 0,
            "production_effect": 0,
        }
    current = observed_at.astimezone(KST)
    role = _slot(current)
    if role is None:
        return {
            "status": "SKIPPED",
            "reason": "outside_observer_slot",
            "provider_calls": 0,
            "production_effect": 0,
        }
    if not is_exchange_session_date("XKRX", current.date()):
        return {
            "status": "SKIPPED",
            "reason": "not_normal_xkrx_session",
            "provider_calls": 0,
            "production_effect": 0,
        }

    expected = expected_latest_completed_krx_session(current.date())
    group_id = observation_group_id(current.date(), expected)
    directory = telemetry_directory or default_telemetry_directory()
    prior = load_group_attempts(directory, current.date(), group_id)
    if any(
        item.terminal_classification == "EXPECTED_SESSION_PRESENT_READY"
        for item in prior
    ):
        return {
            "status": "SKIPPED",
            "reason": "expected_pair_already_ready",
            "provider_calls": 0,
            "production_effect": 0,
        }

    selected_provider = provider or KrxNightFuturesProvider()
    started_at = datetime.now(timezone.utc) if as_of is None else observed_at
    result = None
    error = None
    try:
        result = await selected_provider.collect(current)
    except Exception as exc:  # noqa: BLE001
        error = type(exc).__name__
    ended_at = datetime.now(timezone.utc) if as_of is None else observed_at
    archive = record_attempt_best_effort(
        market_date=current.date(),
        started_at=started_at,
        ended_at=ended_at,
        role=f"observer_{role}",
        production_or_observer="observer",
        expected_session=expected,
        result=result,
        error=error,
        directory=directory,
        horizon_reached=(current.time().replace(tzinfo=None) >= DEFAULT_OBSERVER_HORIZON),
    )
    return {
        "status": archive["status"],
        "role": role,
        "expected_night_bas_dd": expected.isoformat() if expected else None,
        "classification": archive.get("classification"),
        "terminal_state": archive.get("terminal_state"),
        "provider_calls": 1,
        "telemetry_writes": int(archive["status"] == "RECORDED"),
        "production_market_summary_writes": 0,
        "telegram_writes": 0,
        "production_effect": 0,
        "credential_exposure": 0,
    }


def main() -> None:
    result = asyncio.run(run_night_futures_publication_observer())
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, default=str))


if __name__ == "__main__":
    main()
