from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import date
from pathlib import Path

from app.services.night_futures_publication_telemetry_service import (
    NightFuturesAttemptRecord,
    default_telemetry_directory,
)


def build_evidence(directory: Path, market_date: date) -> dict[str, object]:
    day = (
        directory
        / f"{market_date.year:04d}"
        / f"{market_date.month:02d}"
        / f"{market_date.day:02d}"
    )
    groups: list[dict[str, object]] = []
    if day.exists():
        for group in sorted(path for path in day.iterdir() if path.is_dir()):
            attempts = [
                NightFuturesAttemptRecord.model_validate_json(
                    path.read_text(encoding="utf-8")
                )
                for path in sorted((group / "attempts").glob("*.json"))
            ]
            attempts.sort(key=lambda item: (item.timestamp_end, item.attempt_id))
            receipt_path = group / "terminal-receipt.json"
            receipt = (
                json.loads(receipt_path.read_text(encoding="utf-8"))
                if receipt_path.exists()
                else None
            )
            groups.append(
                {
                    "observation_group_id": group.name,
                    "target_expected_session": (
                        attempts[0].expected_night_bas_dd.isoformat()
                        if attempts and attempts[0].expected_night_bas_dd
                        else None
                    ),
                    "attempt_count": len(attempts),
                    "production_attempts": sum(
                        item.production_or_observer == "production" for item in attempts
                    ),
                    "observer_attempts": sum(
                        item.production_or_observer == "observer" for item in attempts
                    ),
                    "classification_counts": dict(
                        Counter(item.terminal_classification for item in attempts)
                    ),
                    "attempts": [
                        {
                            "attempt_id": item.attempt_id,
                            "role": item.role,
                            "timestamp_start": item.timestamp_start.isoformat(),
                            "timestamp_end": item.timestamp_end.isoformat(),
                            "classification": item.terminal_classification,
                            "night_bas_dd_inventory": [
                                value.isoformat()
                                for value in item.provider_night_business_dates_returned
                            ],
                            "ready_products": [
                                value.product
                                for value in item.per_product
                                if value.readiness == "READY"
                            ],
                            "raw_sha256": item.raw_sha256,
                        }
                        for item in attempts
                    ],
                    "terminal_receipt": receipt,
                }
            )
    return {
        "contract": "night-futures-publication-telemetry-v1",
        "market_date": market_date.isoformat(),
        "source": "stored_attempt_archive_only",
        "provider_calls": 0,
        "groups": groups,
        "deadline_policy_decision": "DEADLINE_UNPROVEN",
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Summarize stored night-futures publication telemetry."
    )
    parser.add_argument("--market-date", type=date.fromisoformat, required=True)
    parser.add_argument("--directory", type=Path, default=None)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()
    payload = build_evidence(
        args.directory or default_telemetry_directory(),
        args.market_date,
    )
    encoded = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded + "\n", encoding="utf-8")
    print(encoded)


if __name__ == "__main__":
    main()
