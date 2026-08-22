from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from app.jobs.probe_krx_night_futures import expected_latest_completed_krx_session
from app.macro.providers.base import MacroProvider
from app.macro.providers.krx import KrxNightFuturesProvider
from app.services.night_futures_publication_telemetry_service import (
    DEFAULT_OBSERVER_HORIZON,
    default_telemetry_directory,
    load_group_attempts,
    load_target_attempts,
    observation_group_id,
    record_attempt_best_effort,
)
from app.services.xkrx_role_target_service import (
    XKRX_ROLE_TARGET_CONTRACT,
    resolve_xkrx_role_target,
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
    target = resolve_xkrx_role_target(
        current,
        "night_futures_post_deadline_observer",
        night_session_resolver=expected_latest_completed_krx_session,
    )
    if not target.observation_eligible or target.target_session_date is None:
        return {
            "status": "SKIPPED",
            "reason": target.skip_reason or "no_valid_role_target",
            "role_target_contract": XKRX_ROLE_TARGET_CONTRACT,
            "provider_calls": 0,
            "production_effect": 0,
        }

    expected = target.target_session_date
    group_id = observation_group_id(current.date(), expected)
    directory = telemetry_directory or default_telemetry_directory()
    target_attempts = load_target_attempts(directory, expected, current.date())
    exact_role = f"observer_{role}"
    if any(
        item.terminal_classification == "EXPECTED_SESSION_PRESENT_READY"
        or item.role == "observer_horizon_0915"
        for item in target_attempts
    ):
        return {
            "status": "SKIPPED",
            "reason": "target_already_terminal",
            "role_target_contract": XKRX_ROLE_TARGET_CONTRACT,
            "provider_calls": 0,
            "production_effect": 0,
        }
    if any(item.role == exact_role for item in target_attempts):
        return {
            "status": "SKIPPED",
            "reason": "target_already_observed",
            "role_target_contract": XKRX_ROLE_TARGET_CONTRACT,
            "provider_calls": 0,
            "production_effect": 0,
        }
    prior = load_group_attempts(directory, current.date(), group_id)
    if any(
        item.terminal_classification == "EXPECTED_SESSION_PRESENT_READY"
        for item in prior
    ):
        return {
            "status": "SKIPPED",
            "reason": "target_already_terminal",
            "role_target_contract": XKRX_ROLE_TARGET_CONTRACT,
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
        "role_target_contract": XKRX_ROLE_TARGET_CONTRACT,
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
