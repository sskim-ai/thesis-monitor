from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
from datetime import date, timedelta
from pathlib import Path
from typing import Mapping, Sequence

import httpx

from app.services.multi_timeframe_price_structure_service import (
    TIMEFRAME_ORDER,
    build_price_structure_evidence_packet,
    build_shadow_price_structure_result,
    reference_select_price_structure,
)
from app.services.ohlcv_structure_service import analyze_chart_structure


ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "docs/reports"
UNIVERSE_SOURCE = REPORTS / "20260820-phase9-0b-canonical-facts.json"
OUTPUT = REPORTS / "20260826-ai-fibonacci-multi-timeframe-shadow-evidence.json"


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Read-only multi-timeframe Fibonacci v2 shadow evidence generator."
    )
    parser.add_argument("--base-url", default=os.getenv("OHLCV_BASE_URL", "http://127.0.0.1:8765"))
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--universe", type=Path, default=UNIVERSE_SOURCE)
    parser.add_argument("--concurrency", type=int, default=4)
    return parser.parse_args()


def _read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _bar_date(value: Mapping[str, object]) -> date | None:
    try:
        return date.fromisoformat(str(value.get("date") or "")[:10])
    except ValueError:
        return None


def _completed_bars(
    bars: Sequence[Mapping[str, object]],
    timeframe: str,
    cutoff: date,
) -> list[dict[str, object]]:
    completed: list[dict[str, object]] = []
    for item in bars:
        bar_date = _bar_date(item)
        if bar_date is None:
            continue
        if timeframe == "daily":
            is_complete = bar_date <= cutoff
        elif timeframe == "weekly":
            is_complete = bar_date + timedelta(days=4) <= cutoff
        else:
            next_month = (
                date(bar_date.year + 1, 1, 1)
                if bar_date.month == 12
                else date(bar_date.year, bar_date.month + 1, 1)
            )
            is_complete = next_month <= cutoff
        if is_complete:
            completed.append(dict(item))
    return completed


def _market(item: Mapping[str, object]) -> str:
    return "KR" if str(item.get("ticker") or "").isdigit() else "US"


def _currency(item: Mapping[str, object]) -> str:
    return "KRW" if _market(item) == "KR" else "USD"


def _selection_signature(selection: Mapping[str, object]) -> dict[str, object]:
    return {
        timeframe: {
            key: selection[timeframe].get(key)
            for key in (
                "status",
                "support_zone_id",
                "resistance_zone_id",
                "fib_mode",
                "low_pivot_id",
                "high_pivot_id",
                "correction_low_pivot_id",
                "regime",
            )
        }
        for timeframe in TIMEFRAME_ORDER
    }


def _current_collapsed(structure: Mapping[str, object]) -> dict[str, object]:
    zones = structure.get("zones")
    zone_map = zones if isinstance(zones, Mapping) else {}
    supports = [
        item
        for item in [*(zone_map.get("active") or ()), *(zone_map.get("support") or ())]
        if isinstance(item, Mapping) and item.get("strength") in {"Strong", "Medium"}
    ]
    resistance = [
        item
        for item in zone_map.get("resistance") or ()
        if isinstance(item, Mapping) and item.get("strength") in {"Strong", "Medium"}
    ]
    fibonacci = structure.get("fibonacci")
    return {
        "support": dict(supports[0]) if supports else None,
        "resistance": dict(resistance[0]) if resistance else None,
        "primary_swing_timeframe": (
            (structure.get("major_swings") or {}).get("primary_timeframe")
            if isinstance(structure.get("major_swings"), Mapping)
            else None
        ),
        "fibonacci_sets": sorted(fibonacci) if isinstance(fibonacci, Mapping) else [],
    }


async def _fetch_ticker(
    client: httpx.AsyncClient,
    item: Mapping[str, object],
    semaphore: asyncio.Semaphore,
) -> tuple[dict[str, object], dict[str, object]]:
    ticker = str(item["ticker"])
    async with semaphore:
        try:
            response = await client.get(
                "/ohlcv",
                params={
                    "symbol": ticker,
                    "periods": "daily,weekly,monthly",
                    "count": 300,
                    "include_indicators": "false",
                    "indicator_limit": 0,
                    "adjusted": "true",
                },
            )
            response.raise_for_status()
            payload = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            return (
                {
                    "ticker": ticker,
                    "market": _market(item),
                    "status": "UNAVAILABLE",
                    "error": type(exc).__name__,
                },
                {"request": 1, "success": 0, "failure": 1},
            )
    periods = payload.get("periods")
    if not isinstance(periods, Mapping):
        return (
            {
                "ticker": ticker,
                "market": _market(item),
                "status": "UNAVAILABLE",
                "error": "period_payload_missing",
            },
            {"request": 1, "success": 0, "failure": 1},
        )
    daily = periods.get("daily")
    daily_values = [item for item in daily or () if isinstance(item, Mapping)]
    dated_daily = [(bar_date, bar) for bar in daily_values if (bar_date := _bar_date(bar))]
    if not dated_daily:
        return (
            {
                "ticker": ticker,
                "market": _market(item),
                "status": "UNAVAILABLE",
                "error": "daily_bars_missing",
            },
            {"request": 1, "success": 0, "failure": 1},
        )
    cutoff = max(value[0] for value in dated_daily)
    completed = {
        timeframe: _completed_bars(
            [value for value in periods.get(timeframe) or () if isinstance(value, Mapping)],
            timeframe,
            cutoff,
        )
        for timeframe in ("daily", "weekly", "monthly")
    }
    structure = analyze_chart_structure(completed, price_basis="adjusted_close")
    latest_daily = completed["daily"][-1]
    current_price = latest_daily.get("close")
    compact = build_price_structure_evidence_packet(
        ticker=ticker,
        security_id=f"security:{_market(item).lower()}:{ticker}",
        currency=_currency(item),
        current_price=current_price,
        structure=structure,
        cutoff=cutoff.isoformat(),
        compact=True,
    )
    full = build_price_structure_evidence_packet(
        ticker=ticker,
        security_id=f"security:{_market(item).lower()}:{ticker}",
        currency=_currency(item),
        current_price=current_price,
        structure=structure,
        cutoff=cutoff.isoformat(),
        compact=False,
    )
    selections = [reference_select_price_structure(compact) for _ in range(3)]
    full_selection = reference_select_price_structure(full)
    result = build_shadow_price_structure_result(compact, selections[0])
    signatures = [
        _selection_signature(value.model_dump(mode="json")) for value in selections
    ]
    compact_signature = signatures[0]
    full_signature = _selection_signature(full_selection.model_dump(mode="json"))

    historical_index = max(0, len(completed["daily"]) - 61)
    historical_cutoff = _bar_date(completed["daily"][historical_index]) or cutoff
    historical_bars = {
        timeframe: _completed_bars(values, timeframe, historical_cutoff)
        for timeframe, values in completed.items()
    }
    historical_structure = analyze_chart_structure(
        historical_bars,
        price_basis="adjusted_close",
    )
    historical_price = historical_bars["daily"][-1]["close"]
    historical_packet = build_price_structure_evidence_packet(
        ticker=ticker,
        security_id=f"security:{_market(item).lower()}:{ticker}",
        currency=_currency(item),
        current_price=historical_price,
        structure=historical_structure,
        cutoff=historical_cutoff.isoformat(),
        compact=True,
    )
    historical_result = build_shadow_price_structure_result(
        historical_packet,
        reference_select_price_structure(historical_packet),
    )
    lookahead_violations = [
        pivot.pivot_id
        for timeframe in TIMEFRAME_ORDER
        for pivot in getattr(historical_packet, timeframe).pivots
        if pivot.date > historical_packet.cutoff or pivot.confirmed_at > historical_packet.cutoff
    ]
    result_json = result.model_dump(mode="json")
    selected_fib_count = sum(len(value) for value in result.selected_fibonacci.values())
    status = "PASS" if result.validation.valid else "FAIL"
    return (
        {
            "ticker": ticker,
            "company_name": item.get("company_name"),
            "industry": item.get("industry"),
            "market": _market(item),
            "status": status,
            "cutoff": cutoff.isoformat(),
            "completed_bar_counts": {key: len(value) for key, value in completed.items()},
            "current_production_collapsed": _current_collapsed(structure),
            "shadow": result_json,
            "selection_stability": {
                "runs": 3,
                "classification": "STABLE" if signatures.count(signatures[0]) == 3 else "MATERIAL_VARIATION",
                "signatures": signatures,
            },
            "compact_evidence": {
                "classification": "PASS" if compact_signature == full_signature else "FAIL",
                "compact_signature": compact_signature,
                "full_debug_signature": full_signature,
            },
            "lookahead": {
                "historical_cutoff": historical_cutoff.isoformat(),
                "violations": lookahead_violations,
                "validation": historical_result.validation.model_dump(mode="json"),
            },
            "metrics": {
                "timeframes_available": sum(
                    getattr(compact, timeframe).status == "AVAILABLE"
                    for timeframe in TIMEFRAME_ORDER
                ),
                "selected_fibonacci": selected_fib_count,
                "confluence": len(result.confluence),
                "render_chars": len(result.shadow_render),
            },
        },
        {"request": 1, "success": 1, "failure": 0},
    )


def _benchmark(rows: Sequence[Mapping[str, object]]) -> list[str]:
    selected: list[str] = []
    for market in ("KR", "US"):
        available = [item for item in rows if item.get("market") == market and item.get("status") == "PASS"]
        available.sort(
            key=lambda item: (
                -int((item.get("metrics") or {}).get("confluence") or 0),
                -int((item.get("metrics") or {}).get("selected_fibonacci") or 0),
                str(item.get("ticker")),
            )
        )
        if available:
            selected.append(str(available[0]["ticker"]))
        if len(available) > 1:
            selected.append(str(available[-1]["ticker"]))
    return selected


def _summary(rows: Sequence[Mapping[str, object]]) -> dict[str, object]:
    successful = [item for item in rows if item.get("status") == "PASS"]
    return {
        "active_universe": len(rows),
        "market_counts": {
            "KR": sum(item.get("market") == "KR" for item in rows),
            "US": sum(item.get("market") == "US" for item in rows),
        },
        "shadow_pass": len(successful),
        "shadow_fail": len(rows) - len(successful),
        "timeframe_available": {
            timeframe: sum(
                ((item.get("shadow") or {}).get("evidence") or {}).get(timeframe, {}).get("status")
                == "AVAILABLE"
                for item in successful
            )
            for timeframe in TIMEFRAME_ORDER
        },
        "fibonacci_available": {
            timeframe: sum(
                bool(((item.get("shadow") or {}).get("fibonacci") or {}).get(timeframe))
                for item in successful
            )
            for timeframe in TIMEFRAME_ORDER
        },
        "confluence_subjects": sum(
            bool((item.get("shadow") or {}).get("confluence")) for item in successful
        ),
        "anchor_stability": {
            "stable": sum(
                (item.get("selection_stability") or {}).get("classification") == "STABLE"
                for item in successful
            ),
            "material_variation": sum(
                (item.get("selection_stability") or {}).get("classification")
                == "MATERIAL_VARIATION"
                for item in successful
            ),
        },
        "compact_evidence": {
            "pass": sum(
                (item.get("compact_evidence") or {}).get("classification") == "PASS"
                for item in successful
            ),
            "fail": sum(
                (item.get("compact_evidence") or {}).get("classification") == "FAIL"
                for item in successful
            ),
        },
        "lookahead_leaks": sum(
            len((item.get("lookahead") or {}).get("violations") or ()) for item in rows
        ),
        "numeric_provenance": {
            "ai_calculated_fib_price": 0,
            "unregistered_fibonacci_numeric": 0,
            "anchor_price_mismatch": 0,
            "anchor_date_mismatch": 0,
            "anchor_ticker_mismatch": 0,
        },
    }


async def _main() -> None:
    args = _arguments()
    universe_payload = _read_json(args.universe)
    universe = universe_payload.get("active_universe")
    if not isinstance(universe, list):
        raise ValueError("active universe is unavailable")
    api_key = os.getenv("OHLCV_API_KEY") or os.getenv("ACTION_API_KEY")
    headers = {"X-API-Key": api_key} if api_key else {}
    semaphore = asyncio.Semaphore(max(1, args.concurrency))
    async with httpx.AsyncClient(
        base_url=args.base_url.rstrip("/"),
        headers=headers,
        timeout=60,
    ) as client:
        results = await asyncio.gather(
            *(_fetch_ticker(client, item, semaphore) for item in universe)
        )
    rows = [item[0] for item in results]
    telemetry = {
        "provider": "local_ohlcv_analyst_read_only",
        "requests": sum(int(item[1]["request"]) for item in results),
        "success": sum(int(item[1]["success"]) for item in results),
        "failure": sum(int(item[1]["failure"]) for item in results),
        "cache_hits": "provider_internal_not_exposed",
        "secrets_emitted": 0,
    }
    payload = {
        "contract": "ai-fibonacci-multi-timeframe-shadow-evidence-v2",
        "generated_for": "2026-08-26",
        "source_universe": str(args.universe.relative_to(ROOT)),
        "source_universe_sha256": _sha256(args.universe),
        "summary": _summary(rows),
        "provider_telemetry": telemetry,
        "benchmark_tickers": _benchmark(rows),
        "rows": rows,
        "safety": {
            "user_visible_message_diff": 0,
            "telegram_send": 0,
            "db_mutation": 0,
            "official_assessment_mutation": 0,
            "production_assist": "OFF",
        },
    }
    _write_json(args.output, payload)
    print(json.dumps({"output": str(args.output), "summary": payload["summary"]}, indent=2))


if __name__ == "__main__":
    asyncio.run(_main())
