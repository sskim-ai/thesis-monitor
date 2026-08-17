from __future__ import annotations

import argparse
import asyncio
from datetime import date, datetime
import json
from pathlib import Path
from zoneinfo import ZoneInfo

from app.providers.massive_us_market_provider import MassiveUsMarketProvider
from app.services.massive_shadow_telemetry_service import (
    build_massive_shadow_observation,
    persist_massive_shadow_observation,
)


SEOUL = ZoneInfo("Asia/Seoul")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Record a sanitized Massive 08:05 shadow readiness observation"
    )
    parser.add_argument("--date", required=True, type=date.fromisoformat)
    parser.add_argument("--previous-date", required=True, type=date.fromisoformat)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/cache/massive/telemetry"),
    )
    return parser


async def _run(args: argparse.Namespace) -> dict[str, object]:
    provider = MassiveUsMarketProvider()
    section = await provider.collect(
        session_date=args.date,
        previous_session_date=args.previous_date,
    )
    current = await provider.grouped_daily(args.date)
    previous = await provider.grouped_daily(args.previous_date)
    reference = await provider.reference_tickers(args.date)
    observation = build_massive_shadow_observation(
        section=section,
        current_envelope=current,
        previous_envelope=previous,
        reference_envelope=reference,
        observed_at=datetime.now(tz=SEOUL),
    )
    path = persist_massive_shadow_observation(observation, args.output_dir)
    return {
        "status": "ok",
        "path": str(path),
        "observation": observation.model_dump(mode="json"),
    }


def main() -> None:
    print(json.dumps(asyncio.run(_run(_parser().parse_args())), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
