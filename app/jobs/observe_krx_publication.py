from __future__ import annotations

import argparse
import asyncio
import json
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from app.providers.krx_publication_provider import (
    CORE_READINESS_ENDPOINTS,
    KrxPublicationProvider,
)
from app.services.krx_publication_service import (
    KRX_EXACT_SLOT_CAPTURE_VERSION,
    KrxCaptureOrigin,
    KrxObservationTimeSlot,
    append_krx_publication_observation,
    load_krx_publication_records,
)
from app.services.xkrx_role_target_service import (
    XKRX_ROLE_TARGET_CONTRACT,
    resolve_xkrx_role_target,
)


KST = ZoneInfo("Asia/Seoul")
DEFAULT_TELEMETRY_DIRECTORY = Path(
    "data/telemetry/krx/publication-readiness"
)


@dataclass(frozen=True)
class KrxExactSlotCaptureRequest:
    time_slot: KrxObservationTimeSlot
    target_session: date
    scheduled_for: datetime


def exact_slot_capture_request(
    as_of: datetime,
) -> tuple[KrxExactSlotCaptureRequest | None, str]:
    if as_of.tzinfo is None:
        return None, "timezone_unverified"
    current = as_of.astimezone(KST)
    if (current.hour, current.minute) not in {(8, 5), (16, 5)}:
        return None, "outside_exact_slot"
    scheduled_for = current.replace(second=0, microsecond=0)
    if (current.hour, current.minute) == (16, 5):
        target = resolve_xkrx_role_target(current, "krx_same_day_publication")
        if not target.observation_eligible or target.target_session_date is None:
            return None, target.skip_reason or "no_valid_role_target"
        return (
            KrxExactSlotCaptureRequest(
                time_slot="SAME_DAY_CLOSE_1605",
                target_session=target.target_session_date,
                scheduled_for=scheduled_for,
            ),
            "scheduled",
        )

    target = resolve_xkrx_role_target(current, "krx_next_morning_publication")
    if not target.observation_eligible or target.target_session_date is None:
        return None, target.skip_reason or "no_valid_role_target"
    return (
        KrxExactSlotCaptureRequest(
            time_slot="NEXT_MORNING_0805",
            target_session=target.target_session_date,
            scheduled_for=scheduled_for,
        ),
        "scheduled",
    )


async def run_exact_slot_capture(
    *,
    as_of: datetime | None = None,
    capture_origin: KrxCaptureOrigin = "manual",
    telemetry_directory: Path = DEFAULT_TELEMETRY_DIRECTORY,
    provider: KrxPublicationProvider | None = None,
) -> dict[str, object]:
    current = as_of or datetime.now(timezone.utc)
    request, decision = exact_slot_capture_request(current)
    if request is None:
        return {
            "capture_contract_version": KRX_EXACT_SLOT_CAPTURE_VERSION,
            "status": "SKIPPED",
            "reason": decision,
            "observed_at": current.isoformat(),
            "provider_calls": 0,
            "telemetry_writes": 0,
            "user_visible_integration": False,
        }

    records = load_krx_publication_records(
        telemetry_directory / f"{request.target_session.isoformat()}.jsonl"
    )
    if any(
        item.time_slot == request.time_slot
        and item.scheduled_for == request.scheduled_for
        for item in records
    ):
        return {
            "capture_contract_version": KRX_EXACT_SLOT_CAPTURE_VERSION,
            "role_target_contract": XKRX_ROLE_TARGET_CONTRACT,
            "status": "SKIPPED",
            "reason": "target_already_observed",
            "time_slot": request.time_slot,
            "target_session": request.target_session.isoformat(),
            "provider_calls": 0,
            "telemetry_writes": 0,
            "user_visible_integration": False,
        }
    if any(item.observation.status == "PROVIDER_COMPLETE" for item in records):
        return {
            "capture_contract_version": KRX_EXACT_SLOT_CAPTURE_VERSION,
            "role_target_contract": XKRX_ROLE_TARGET_CONTRACT,
            "status": "SKIPPED",
            "reason": "target_already_terminal",
            "time_slot": request.time_slot,
            "target_session": request.target_session.isoformat(),
            "provider_calls": 0,
            "telemetry_writes": 0,
            "user_visible_integration": False,
        }

    publication_provider = provider or KrxPublicationProvider()
    if not publication_provider.configured:
        return {
            "capture_contract_version": KRX_EXACT_SLOT_CAPTURE_VERSION,
            "status": "CONFIGURATION_ERROR",
            "reason": "krx_open_api_key_not_configured",
            "time_slot": request.time_slot,
            "target_session": request.target_session.isoformat(),
            "provider_calls": 0,
            "telemetry_writes": 0,
            "user_visible_integration": False,
        }

    observation = await publication_provider.probe_publication_readiness(
        target_session=request.target_session,
        latest_completed_session=request.target_session,
        observed_at=current,
    )
    timeline = append_krx_publication_observation(
        observation,
        telemetry_directory,
        time_slot=request.time_slot,
        capture_origin=capture_origin,
        scheduled_for=request.scheduled_for,
        normal_session=True,
    )
    return {
        "capture_contract_version": KRX_EXACT_SLOT_CAPTURE_VERSION,
        "role_target_contract": XKRX_ROLE_TARGET_CONTRACT,
        "status": "RECORDED",
        "capture_origin": capture_origin,
        "time_slot": request.time_slot,
        "target_session": request.target_session.isoformat(),
        "scheduled_for": request.scheduled_for.isoformat(),
        "observed_at": observation.observed_at.isoformat(),
        "readiness": observation.status,
        "endpoint_rows": {
            item.endpoint: item.row_count for item in observation.endpoints
        },
        "payload_sha256": {
            item.endpoint: item.payload_sha256 for item in observation.endpoints
        },
        "timeline_observations": len(timeline.observations),
        "provider_calls": len(CORE_READINESS_ENDPOINTS),
        "telemetry_writes": 1,
        "user_visible_integration": False,
        "credential_exposure": 0,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Record a fail-closed exact-slot KRX publication observation."
    )
    parser.add_argument(
        "--capture-origin",
        choices=("launchd-calendar", "manual"),
        default="manual",
    )
    args = parser.parse_args()
    origin: KrxCaptureOrigin = (
        "launchd_calendar"
        if args.capture_origin == "launchd-calendar"
        else "manual"
    )
    result = asyncio.run(run_exact_slot_capture(capture_origin=origin))
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    if result["status"] == "CONFIGURATION_ERROR":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
