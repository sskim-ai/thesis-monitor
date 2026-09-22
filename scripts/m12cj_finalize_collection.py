from __future__ import annotations

import argparse
import json
import os
from datetime import date
from pathlib import Path

from scripts.m12cj_current_market_smoke import (
    STATE_DIRECTORIES,
    read_json,
    sha256_file,
    source_db_identity,
    write_json,
)


def require(condition: bool, code: str) -> None:
    if not condition:
        raise RuntimeError(code)


def _mapping(value: object) -> dict[str, object]:
    return dict(value) if isinstance(value, dict) else {}


def run(args: argparse.Namespace) -> None:
    output = args.output_root.resolve()
    isolated_data = output / "isolated-data"
    isolated_db = isolated_data / "thesis_monitor.sqlite3"
    require(isolated_db.is_file(), "isolated_database_missing")
    required = (
        "collection-results.json",
        "current-us-market-smoke.json",
        "current-kr-market-smoke.json",
        "krx-night-kospi200-202612-20260916-vs-kiwoom-fixture.json",
        "inputs/current-packets/us.json",
        "inputs/current-packets/kr.json",
        "inputs/deterministic/us.json",
        "inputs/deterministic/kr.json",
    )
    require(all((output / name).is_file() for name in required), "collection_not_complete")

    os.environ["THESIS_MONITOR_ENV_FILE"] = str(args.env_file.resolve())
    os.environ["DATA_DIR"] = str(isolated_data)
    os.environ["DATABASE_URL"] = f"sqlite:///{isolated_db}"
    os.environ["NOTIFICATION_DRY_RUN"] = "true"
    os.environ["NOTIFICATION_RECIPIENT_CLASS"] = "test"
    os.environ["AI_REVIEW_MODE"] = "shadow"
    os.environ["PERSISTENCE_V2_WRITER_ENABLED"] = "false"
    os.environ["PERSISTENCE_V2_OUTBOX_DELIVERY_ENABLED"] = "false"

    from sqlmodel import Session, select

    from app.database import engine
    from app.models.thesis import ThesisAssessment

    collection = read_json(output / "collection-results.json")
    macro = _mapping(collection.get("macro"))
    kr_close = _mapping(collection.get("kr_close"))
    us_breadth = _mapping(collection.get("us_exchange_breadth"))
    kr_market = _mapping(collection.get("kr_market_context"))
    krx = _mapping(collection.get("krx_night_probe"))
    krx_telemetry = _mapping(krx.get("telemetry"))
    kiwoom_calls = _mapping(kr_market.get("provider_calls"))
    market_provider_reads = (
        1
        + int(kiwoom_calls.get("requests") or 0)
        + len(krx_telemetry.get("queried_dates") or [])
    )
    write_json(
        output / "provider-call-ledger-redacted.json",
        {
            "contract": "m12cj-redacted-provider-call-ledger-v1",
            "credentials_included": False,
            "recovered_offline_after_postcollection_audit_failure": True,
            "current_smoke_generation": output.name,
            "market_provider_reads_minimum_count": market_provider_reads,
            "market_provider_reads_count_semantic": (
                "explicit Nasdaq/Kiwoom/KRX request denominator; macro and per-stock "
                "provider calls are reported by result counts rather than inferred"
            ),
            "macro": {
                "status": macro.get("status"),
                "observation_count": macro.get("observation_count"),
                "provider_warning_count": len(macro.get("provider_warnings") or []),
            },
            "kr_close": {
                "status": kr_close.get("status"),
                "observation_count": kr_close.get("observation_count"),
                "warning_count": len(kr_close.get("warnings") or []),
            },
            "nasdaq_breadth": {
                "request_count": 1,
                "status": us_breadth.get("status"),
                "session_date": us_breadth.get("session_date"),
                "latest_available_session": us_breadth.get("latest_available_session"),
                "denial_reason": us_breadth.get("denial_reason"),
            },
            "kiwoom_kr_market": {
                "status": kr_market.get("status"),
                "safe_error_type": kr_market.get("reason"),
                "requests": kiwoom_calls.get("requests"),
                "successes": kiwoom_calls.get("successes"),
                "failures": kiwoom_calls.get("failures"),
                "provider_retries": kiwoom_calls.get("retries"),
            },
            "official_krx_night": {
                "request_count": len(krx_telemetry.get("queried_dates") or []),
                "queried_dates": krx_telemetry.get("queried_dates"),
                "status": krx_telemetry.get("status"),
                "canonicalization_status": krx_telemetry.get("canonicalization_status"),
                "night_session_usable": krx_telemetry.get("night_session_usable"),
                "history_update": krx_telemetry.get("history_update"),
            },
            "model_inference_calls": 0,
        },
    )

    kr_run_date = date.fromisoformat(str(_mapping(collection.get("kr_monitor"))["run_date"]))
    with Session(engine) as session:
        rows = session.exec(
            select(ThesisAssessment).where(
                ThesisAssessment.assessment_date == kr_run_date
            )
        ).all()
        price_modes: dict[str, object] = {}
        for row in rows:
            if not row.ticker.isdigit():
                continue
            context = json.loads(row.price_context)
            decision = _mapping(context.get("decision"))
            price_modes[row.ticker] = {
                key: decision.get(key)
                for key in (
                    "price_as_of",
                    "price_basis",
                    "market_session",
                    "assessment_state",
                    "latest_completed_regular_session_date",
                )
            }
        write_json(output / "kr-stock-price-mode-audit.json", price_modes)

    first_attempt = args.first_attempt.resolve()
    write_json(
        output / "collection-attempt-ledger.json",
        {
            "contract": "m12cj-collection-attempt-ledger-v1",
            "attempts": [
                {
                    "ordinal": 1,
                    "output_root": str(first_attempt),
                    "terminal_boundary": "POST_PROVIDER_AUDIT_SERIALIZATION",
                    "safe_error": "MacroProviderResult.model_dump_not_supported",
                    "model_inference_calls": 0,
                    "production_send": 0,
                },
                {
                    "ordinal": 2,
                    "output_root": str(output),
                    "terminal_boundary": "POSTCOLLECTION_PROVIDER_LEDGER",
                    "safe_error": "MacroProviderResult.queried_dates_not_supported",
                    "core_collection_complete": True,
                    "offline_finalization_applied": True,
                    "model_inference_calls": 0,
                    "production_send": 0,
                },
            ],
            "application_runtime_config_changes": 0,
            "third_provider_collection_attempt": 0,
        },
    )

    source_db = args.source_data.resolve() / "thesis_monitor.sqlite3"
    copied = [
        {
            "name": name,
            "source": str(args.source_data.resolve() / name),
            "destination": str(isolated_data / name),
        }
        for name in STATE_DIRECTORIES
        if (isolated_data / name).exists()
    ]
    write_json(
        output / "isolation-audit.json",
        {
            "contract": "m12cj-isolation-audit-v1",
            "source_database_access": "sqlite_uri_mode_ro_then_backup",
            "source_database_identity_at_offline_finalization": source_db_identity(source_db),
            "isolated_database": str(isolated_db),
            "isolated_database_sha256": sha256_file(isolated_db),
            "copied_state": copied,
            "exact_source_before_after_hash_not_asserted": True,
            "reason": (
                "the first two collectors ended after safe source backup and isolated "
                "collection but before the final audit write; the source is a live runtime"
            ),
            "production_db_mutation_by_smoke": 0,
            "production_send": 0,
            "production_recipient_intent": 0,
            "test_sink_invocations": 0,
            "broker_order_calls": 0,
            "broker_modify_calls": 0,
            "broker_cancel_calls": 0,
        },
    )
    write_json(
        output / "scope-correction-m12ci.json",
        {
            "contract": "m12cj-m12ci-scope-correction-v1",
            "windows_kiwoom_gateway_prerequisite": False,
            "m12ci_r1_status": "SUPERSEDED_UNEXECUTED",
            "machine_authority": "OFFICIAL_KRX_NIGHT",
            "kiwoom_fixture_role": "HUMAN_ACCEPTANCE_CROSS_CHECK_ONLY",
            "windows_kiwoom_gateway_provision": 0,
        },
    )
    print(
        json.dumps(
            {
                "status": "OFFLINE_FINALIZATION_PASS",
                "output_root": str(output),
                "model_inference_calls": 0,
                "third_provider_collection_attempt": 0,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--first-attempt", type=Path, required=True)
    parser.add_argument("--source-data", type=Path, required=True)
    parser.add_argument("--env-file", type=Path, required=True)
    run(parser.parse_args())


if __name__ == "__main__":
    main()
