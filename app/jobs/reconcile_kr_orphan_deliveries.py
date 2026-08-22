from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path

from sqlmodel import Session

from app.config import get_settings
from app.database import engine, init_db
from app.services.notification_delivery_integrity_service import (
    KrOrphanIncident,
    OrphanReconciliationError,
    reconcile_kr_orphan_incident,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Dry-run or reconcile one exact KR no-packet delivery incident."
    )
    parser.add_argument("--run-id", type=int, required=True)
    parser.add_argument("--run-date", type=date.fromisoformat, required=True)
    parser.add_argument("--packet-id", required=True)
    parser.add_argument("--expected-stock-count", type=int, required=True)
    parser.add_argument("--expected-digest-count", type=int, default=1)
    parser.add_argument("--apply", action="store_true")
    return parser


def main() -> None:
    args = _parser().parse_args()
    incident = KrOrphanIncident(
        run_id=args.run_id,
        run_date=args.run_date,
        packet_id=args.packet_id,
        expected_stock_count=args.expected_stock_count,
        expected_digest_count=args.expected_digest_count,
    )
    init_db()
    try:
        with Session(engine) as session:
            result = reconcile_kr_orphan_incident(
                session,
                incident,
                data_dir=Path(get_settings().data_dir),
                apply=args.apply,
            )
    except OrphanReconciliationError as exc:
        print(
            json.dumps(
                {
                    "contract": "kr-orphan-delivery-reconciliation-v1",
                    "result": "aborted",
                    "reason": str(exc),
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        raise SystemExit(2) from exc
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
