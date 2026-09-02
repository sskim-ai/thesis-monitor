from __future__ import annotations

import argparse
import asyncio
import json
import os
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import httpx

from app.jobs.probe_krx_night_futures import (
    KRX_FUTURES_DAILY_URL,
    USER_AGENT,
)
from app.services.krx_night_history_service import (
    KRX_NIGHT_HISTORY_CONTRACT,
    load_cached_response,
    persist_krx_response,
)
from app.services.market_session import is_exchange_session_date
from scripts.kr_market_preenable_evidence import load_env_values


BACKFILL_CONTRACT = "krx-night-historical-backfill-v1"


def _atomic_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def _sessions(start: date, end: date) -> tuple[date, ...]:
    return tuple(
        current
        for offset in range((end - start).days + 1)
        if is_exchange_session_date("XKRX", current := start + timedelta(days=offset))
    )


async def _run(args: argparse.Namespace) -> None:
    if args.start > args.end or args.end > args.cutoff:
        raise ValueError("historical_backfill_date_boundary_invalid")
    values = load_env_values(args.env_file)
    api_key = values.get("KRX_OPEN_API_KEY") or ""
    if not api_key:
        raise ValueError("krx_open_api_key_not_configured")
    sessions = _sessions(args.start, args.end)
    rows: list[dict[str, object]] = []
    request_count = 0
    cache_hit_count = 0
    stored_bar_count = 0
    normalized_bar_count = 0
    rejection_count = 0
    async with httpx.AsyncClient(
        timeout=30.0,
        headers={"AUTH_KEY": api_key, "User-Agent": USER_AGENT},
    ) as client:
        for query_date in sessions:
            cached = load_cached_response(args.history_root, query_date)
            if cached is not None:
                receipt, raw_body = cached
                cache_hit_count += 1
                source = "CACHE"
                fetched_at = receipt.fetched_at
            else:
                response = await client.get(
                    KRX_FUTURES_DAILY_URL,
                    params={"basDd": query_date.strftime("%Y%m%d")},
                )
                response.raise_for_status()
                raw_body = response.content
                request_count += 1
                source = "HISTORICAL_BACKFILL"
                fetched_at = datetime.now(UTC)
                await asyncio.sleep(args.request_delay_seconds)
            receipt, normalized, stored = persist_krx_response(
                root=args.history_root,
                query_date=query_date,
                fetched_at=fetched_at,
                http_status=200,
                raw_body=raw_body,
            )
            stored_bar_count += stored
            normalized_bar_count += len(normalized.bars)
            rejection_count += len(normalized.rejections)
            rows.append(
                {
                    "query_date": query_date,
                    "source": source,
                    "raw_payload_sha256": receipt.raw_payload_sha256,
                    "raw_row_count": receipt.row_count,
                    "normalized_bar_count": len(normalized.bars),
                    "stored_bar_count": stored,
                    "rejection_count": len(normalized.rejections),
                }
            )
    result = {
        "contract": BACKFILL_CONTRACT,
        "history_contract": KRX_NIGHT_HISTORY_CONTRACT,
        "namespace": args.namespace,
        "source": "official KRX fut_bydd_trd",
        "start": args.start,
        "end": args.end,
        "cutoff": args.cutoff,
        "post_cutoff_dates_used": 0,
        "production_run51_packet_mutation": 0,
        "request_count": request_count,
        "success_count": request_count,
        "failure_count": 0,
        "cache_hit_count": cache_hit_count,
        "expected_session_count": len(sessions),
        "normalized_bar_count": normalized_bar_count,
        "stored_bar_count": stored_bar_count,
        "rejection_count": rejection_count,
        "rows": rows,
    }
    _atomic_json(args.output, result)
    print(
        json.dumps(
            {
                key: result[key]
                for key in (
                    "request_count",
                    "success_count",
                    "cache_hit_count",
                    "expected_session_count",
                    "normalized_bar_count",
                    "stored_bar_count",
                    "rejection_count",
                )
            },
            sort_keys=True,
        )
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--env-file", type=Path, required=True)
    parser.add_argument("--history-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--start", type=date.fromisoformat, required=True)
    parser.add_argument("--end", type=date.fromisoformat, required=True)
    parser.add_argument("--cutoff", type=date.fromisoformat, required=True)
    parser.add_argument(
        "--namespace",
        default="TEST/HISTORICAL_BACKFILL",
    )
    parser.add_argument("--request-delay-seconds", type=float, default=0.2)
    asyncio.run(_run(parser.parse_args()))


if __name__ == "__main__":
    main()
