from __future__ import annotations

import argparse
import asyncio
import json
from datetime import date, datetime
from pathlib import Path
import sys
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.providers.kiwoom_rest_client import KiwoomRestClient  # noqa: E402
from app.services.kiwoom_kr_market_context_service import (  # noqa: E402
    KA10066_AMOUNT_UNIT_KRW,
    KiwoomKrMarketContextService,
    persist_kiwoom_market_archive,
)


KST = ZoneInfo("Asia/Seoul")
FLOW_FIELDS = {
    "foreign": "frgnr_invsr",
    "institution": "orgn",
    "retail": "ind_invsr",
}


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Collect sanitized read-only Kiwoom KR market-context evidence."
    )
    parser.add_argument("--date", required=True, type=date.fromisoformat)
    parser.add_argument("--observed-at", type=datetime.fromisoformat)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--archive-directory", type=Path)
    return parser


def _signed_int(value: object) -> int:
    return int(str(value or "0").replace(",", "").strip() or "0")


def _top_stock_flows(archive: dict[str, object]) -> dict[str, object]:
    rows_by_market: dict[str, list[dict[str, object]]] = {"KOSPI": [], "KOSDAQ": []}
    responses = archive.get("responses")
    for response in responses if isinstance(responses, list) else []:
        if not isinstance(response, dict) or response.get("api_id") != "ka10066":
            continue
        request = response.get("request")
        payload = response.get("payload")
        if not isinstance(request, dict) or not isinstance(payload, dict):
            continue
        market = {"001": "KOSPI", "101": "KOSDAQ"}.get(str(request.get("mrkt_tp")))
        values = payload.get("opaf_invsr_trde")
        if market and isinstance(values, list):
            rows_by_market[market].extend(
                row for row in values if isinstance(row, dict)
            )
    result: dict[str, object] = {}
    for market, rows in rows_by_market.items():
        result[market] = {}
        for actor, field in FLOW_FIELDS.items():
            normalized = [
                {
                    "ticker": str(row.get("stk_cd") or "").removesuffix("_AL"),
                    "name": str(row.get("stk_nm") or ""),
                    "amount_krw": _signed_int(row.get(field)) * KA10066_AMOUNT_UNIT_KRW,
                }
                for row in rows
            ]
            result[market][actor] = {
                "top_buy": sorted(
                    (row for row in normalized if row["amount_krw"] > 0),
                    key=lambda row: (-int(row["amount_krw"]), str(row["ticker"])),
                )[:5],
                "top_sell": sorted(
                    (row for row in normalized if row["amount_krw"] < 0),
                    key=lambda row: (int(row["amount_krw"]), str(row["ticker"])),
                )[:5],
            }
    return result


async def _run(args: argparse.Namespace) -> dict[str, object]:
    observed_at = args.observed_at or datetime.now(KST)
    if observed_at.tzinfo is None:
        observed_at = observed_at.replace(tzinfo=KST)
    collection = await KiwoomKrMarketContextService(KiwoomRestClient()).collect(
        session_date=args.date,
        observed_at=observed_at,
    )
    archive_path = persist_kiwoom_market_archive(
        collection,
        directory=args.archive_directory,
    )
    section = collection.cross_section
    summary = {
        "contract_version": "kiwoom-kr-market-context-evidence-v1",
        "session_date": args.date.isoformat(),
        "observed_at": observed_at.isoformat(),
        "source_payload_sha256": section.source_payload_sha256,
        "archive_path": str(archive_path),
        "indices": [item.model_dump(mode="json") for item in section.indices],
        "breadth": section.breadth.model_dump(mode="json") if section.breadth else None,
        "breadth_by_scope": [
            item.model_dump(mode="json") for item in section.breadth_by_scope
        ],
        "size_context": [
            item.model_dump(mode="json")
            for item in section.sectors
            if item.market_scope == "KOSPI" and item.sector_code in {"002", "003", "004"}
        ],
        "sector_count": len(section.sectors),
        "top_sectors": [
            item.model_dump(mode="json")
            for item in sorted(
                (
                    item
                    for item in section.sectors
                    if not (
                        item.market_scope == "KOSPI"
                        and item.sector_code in {"002", "003", "004"}
                    )
                ),
                key=lambda item: (-(item.return_pct or 0.0), item.sector),
            )[:8]
        ],
        "bottom_sectors": [
            item.model_dump(mode="json")
            for item in sorted(
                (
                    item
                    for item in section.sectors
                    if not (
                        item.market_scope == "KOSPI"
                        and item.sector_code in {"002", "003", "004"}
                    )
                ),
                key=lambda item: ((item.return_pct or 0.0), item.sector),
            )[:8]
        ],
        "market_flows": [item.model_dump(mode="json") for item in section.market_flows],
        "top_stock_flows": _top_stock_flows(collection.sanitized_archive),
        "quality": section.quality.model_dump(mode="json"),
        "audit": collection.audit.model_dump(mode="json"),
    }
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    return summary


def main() -> None:
    result = asyncio.run(_run(_parser().parse_args()))
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
