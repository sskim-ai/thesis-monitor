import argparse
import asyncio
import json

from sqlmodel import Session, select

from app.database import engine
from app.models.watchlist import WatchlistItem
from app.services.ohlcv_client import OhlcvClient


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Read-only OHLCV structure smoke test for the active monitored universe."
    )
    parser.add_argument(
        "--ticker",
        action="append",
        dest="tickers",
        help="Restrict the smoke test to one or more active tickers.",
    )
    parser.add_argument("--concurrency", type=int, default=4)
    parser.add_argument(
        "--compact",
        action="store_true",
        help="Print one compact coverage row per ticker.",
    )
    return parser.parse_args()


def _nearest(zones: object, limit: int) -> list[dict[str, object]]:
    if not isinstance(zones, list):
        return []
    fields = (
        "zone_low",
        "zone_high",
        "timeframe",
        "strength",
        "distance_pct",
    )
    return [
        {key: zone.get(key) for key in fields if zone.get(key) is not None}
        for zone in zones[:limit]
        if isinstance(zone, dict)
    ]


async def _inspect(
    item: WatchlistItem,
    semaphore: asyncio.Semaphore,
) -> dict[str, object]:
    async with semaphore:
        try:
            context = await OhlcvClient().fetch_price_context(item.ticker)
        except Exception as exc:
            return {
                "ticker": item.ticker,
                "market": "kr" if item.ticker.isdigit() else "us",
                "status": "unavailable",
                "error": type(exc).__name__,
            }
    structure = context.chart.structure
    if not structure:
        return {
            "ticker": item.ticker,
            "market": "kr" if item.ticker.isdigit() else "us",
            "status": "unavailable",
            "error": "structure_missing",
        }
    local = structure.get("local_pivots") or {}
    major = structure.get("major_swings") or {}
    major_by_timeframe = major.get("by_timeframe") or {}
    boxes = structure.get("boxes") or {}
    fibonacci = structure.get("fibonacci") or {}
    risk_reward = structure.get("risk_reward") or {}
    chart_state = structure.get("chart_state") or {}
    invalidation = structure.get("invalidation") or {}
    availability = structure.get("availability") or {}
    return {
        "ticker": item.ticker,
        "market": "kr" if item.ticker.isdigit() else "us",
        "status": "available",
        "as_of_date": structure.get("as_of_date"),
        "chart_quality": context.chart.quality,
        "price_basis": structure.get("price_basis"),
        "availability": availability,
        "local_pivot_counts": {
            timeframe: len(local.get(timeframe) or [])
            for timeframe in ("daily", "weekly", "monthly")
        },
        "major_swing_counts": {
            timeframe: len(major_by_timeframe.get(timeframe) or [])
            for timeframe in ("daily", "weekly", "monthly")
        },
        "major_primary_timeframe": major.get("primary_timeframe"),
        "nearest_supports": _nearest((structure.get("zones") or {}).get("support"), 2),
        "nearest_resistance": _nearest((structure.get("zones") or {}).get("resistance"), 1),
        "active_zones": _nearest((structure.get("zones") or {}).get("active"), 2),
        "box_counts": {
            timeframe: len(boxes.get(timeframe) or [])
            for timeframe in ("daily", "weekly", "monthly")
        },
        "major_anchors": structure.get("major_anchors"),
        "fibonacci_sets": sorted(fibonacci),
        "risk_reward": risk_reward.get("current_price"),
        "invalidation": invalidation,
        "chart_state": {
            "state": chart_state.get("state"),
            "confidence": chart_state.get("confidence"),
            "reasons": chart_state.get("reasons"),
            "blocking_unknowns": chart_state.get("blocking_unknowns"),
        },
        "supply": (structure.get("supply_classification") or {}).get("classification"),
        "unavailable_fields": structure.get("unavailable_fields"),
    }


async def _main() -> None:
    args = _arguments()
    with Session(engine) as session:
        query = (
            select(WatchlistItem)
            .where(WatchlistItem.active.is_(True))
            .order_by(WatchlistItem.ticker)
        )
        items = list(session.exec(query).all())
    if args.tickers:
        requested = {ticker.upper() for ticker in args.tickers}
        items = [item for item in items if item.ticker.upper() in requested]
    semaphore = asyncio.Semaphore(max(1, args.concurrency))
    rows = await asyncio.gather(*(_inspect(item, semaphore) for item in items))
    state_distribution: dict[str, int] = {}
    for row in rows:
        chart_state = row.get("chart_state")
        if isinstance(chart_state, dict):
            state = str(chart_state.get("state") or "unavailable")
        else:
            state = "unavailable"
        state_distribution[state] = state_distribution.get(state, 0) + 1
    output_rows = rows
    if args.compact:
        output_rows = [
            {
                "ticker": row.get("ticker"),
                "market": row.get("market"),
                "status": row.get("status"),
                "as_of_date": row.get("as_of_date"),
                "chart_quality": row.get("chart_quality"),
                "local_pivot_counts": row.get("local_pivot_counts"),
                "major_swing_counts": row.get("major_swing_counts"),
                "nearest_support": (row.get("nearest_supports") or [None])[0],
                "nearest_resistance": (row.get("nearest_resistance") or [None])[0],
                "fibonacci_sets": row.get("fibonacci_sets"),
                "risk_reward": (
                    (row.get("risk_reward") or {}).get("ratio")
                    if isinstance(row.get("risk_reward"), dict)
                    else None
                ),
                "chart_state": row.get("chart_state"),
                "unavailable_fields": row.get("unavailable_fields"),
                "error": row.get("error"),
            }
            for row in rows
        ]
    print(
        json.dumps(
            {
                "active_total": len(rows),
                "market_counts": {
                    "kr": sum(row.get("market") == "kr" for row in rows),
                    "us": sum(row.get("market") == "us" for row in rows),
                },
                "state_distribution": state_distribution,
                "rows": output_rows,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    asyncio.run(_main())
