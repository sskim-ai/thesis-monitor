from __future__ import annotations

import argparse
import asyncio
from datetime import date, timedelta
import json

import httpx

from app.providers.massive_us_market_provider import MassiveUsMarketProvider


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Probe Massive US daily market breadth")
    parser.add_argument("--date", required=True, type=date.fromisoformat)
    parser.add_argument("--previous-date", type=date.fromisoformat)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--refresh", action="store_true")
    return parser


async def _run(args: argparse.Namespace) -> dict[str, object]:
    provider = MassiveUsMarketProvider()
    if not args.live:
        return {
            "status": "not_run",
            "configured": provider.configured,
            "reason": "Pass --live to call Massive; credentials are never printed.",
        }
    previous_date = args.previous_date
    if previous_date is None:
        for offset in range(1, 8):
            candidate = args.date - timedelta(days=offset)
            try:
                await provider.grouped_daily(candidate, refresh=args.refresh)
            except (httpx.HTTPError, ValueError):
                continue
            previous_date = candidate
            break
    if previous_date is None:
        raise RuntimeError("No previous completed session was found in the prior seven days")
    section = await provider.collect(
        session_date=args.date,
        previous_session_date=previous_date,
        refresh=args.refresh,
    )
    current = await provider.grouped_daily(args.date)
    rows = provider._rows(current)
    tickers = sorted(str(item.get("T")) for item in rows if item.get("T"))
    payload = current.get("payload") if isinstance(current.get("payload"), dict) else {}
    return {
        "status": "ok",
        "plan_access": "grouped_daily_and_reference_available",
        "session_date": args.date.isoformat(),
        "previous_session_date": previous_date.isoformat(),
        "http_status": 200,
        "row_count": len(rows),
        "first_ticker_examples": tickers[:5],
        "last_ticker_examples": tickers[-5:],
        "field_coverage": sorted({key for row in rows for key in row}),
        "response_latency_seconds": current.get("latency_seconds"),
        "adjusted": payload.get("adjusted"),
        "data_freshness": section.quality.freshness,
        "duplicate_ticker_count": len(tickers) - len(set(tickers)),
        "missing_close_count": sum(not isinstance(row.get("c"), (int, float)) for row in rows),
        "missing_volume_count": sum(not isinstance(row.get("v"), (int, float)) for row in rows),
        "eligible_count": section.breadth.eligible_count if section.breadth else 0,
        "breadth": section.breadth.model_dump(mode="json") if section.breadth else None,
        "concentration": section.concentration,
        "universe_version": section.quality.universe_version,
        "exclusion_reason_counts": section.quality.exclusion_reason_counts,
        "response_sha256": current.get("response_sha256"),
    }


def main() -> None:
    result = asyncio.run(_run(_parser().parse_args()))
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
