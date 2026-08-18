from __future__ import annotations

# ruff: noqa: E402

import argparse
import asyncio
import json
import sys
from datetime import date
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.providers.krx_kr_market_provider import (
    CORE_READINESS_ENDPOINTS,
    OFFICIAL_DAILY_REQUEST_LIMIT,
    KrxKrMarketProvider,
)
from app.services.krx_publication_service import (
    append_krx_publication_observation,
)
from app.services.market_session import korea_market_session


SEOUL = ZoneInfo("Asia/Seoul")
DEFAULT_TELEMETRY_DIRECTORY = (
    ROOT / "data" / "telemetry" / "krx" / "publication-readiness"
)


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Record one read-only KRX publication-readiness observation."
    )
    parser.add_argument("--target-session", required=True, type=date.fromisoformat)
    parser.add_argument("--latest-completed-session", type=date.fromisoformat)
    parser.add_argument(
        "--time-slot",
        choices=(
            "SAME_DAY_CLOSE_1605",
            "NEXT_MORNING_0805",
            "T_PLUS_1_RECONCILIATION",
        ),
    )
    parser.add_argument(
        "--telemetry-directory",
        type=Path,
        default=DEFAULT_TELEMETRY_DIRECTORY,
    )
    return parser.parse_args()


async def _run(args: argparse.Namespace) -> dict[str, object]:
    provider = KrxKrMarketProvider()
    if not provider.configured:
        raise RuntimeError("KRX_OPEN_API_KEY is not configured")
    latest_completed = args.latest_completed_session
    if latest_completed is None:
        latest_completed = (
            korea_market_session().latest_completed_regular_session_date
        )
    observation = await provider.probe_publication_readiness(
        target_session=args.target_session,
        latest_completed_session=latest_completed,
    )
    timeline = append_krx_publication_observation(
        observation,
        args.telemetry_directory,
        time_slot=args.time_slot,
    )
    return {
        "contract_version": timeline.contract_version,
        "target_session": args.target_session.isoformat(),
        "observed_at": observation.observed_at.isoformat(),
        "observed_at_kst": observation.observed_at.astimezone(SEOUL).isoformat(),
        "readiness": observation.status,
        "endpoints": [
            {
                "endpoint": endpoint.endpoint,
                "http_status": endpoint.http_status,
                "row_count": endpoint.row_count,
                "provider_dates": [value.isoformat() for value in endpoint.provider_dates],
                "latency_ms": (
                    round(endpoint.latency_seconds * 1000, 1)
                    if endpoint.latency_seconds is not None
                    else None
                ),
                "payload_sha256": endpoint.payload_sha256,
                "status": endpoint.status,
            }
            for endpoint in observation.endpoints
        ],
        "timeline": {
            "observation_count": len(timeline.observations),
            "first_non_empty_at": timeline.first_non_empty_at,
            "first_complete_at": timeline.first_complete_at,
            "observed_complete_by": timeline.observed_complete_by,
            "last_empty_at": timeline.last_empty_at,
            "publication_window_start": timeline.publication_window_start,
            "publication_window_end": timeline.publication_window_end,
        },
        "request_count": len(CORE_READINESS_ENDPOINTS),
        "official_daily_request_limit": OFFICIAL_DAILY_REQUEST_LIMIT,
        "credential_exposure": 0,
    }


def main() -> None:
    args = _arguments()
    payload = asyncio.run(_run(args))
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
