"""Read-only parity preflight for R5F-R2; never invokes providers or AI owners."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sqlite3

from sqlalchemy import create_engine
from sqlmodel import Session

from app.services.ai_review_service import validate_market_packet_session_parity
from app.services.onboarding_readiness_service import production_universe_snapshot
from app.services.unified_run_artifacts import durable_json
from app.services.unified_snapshot_contract import digest
from app.services.unified_source_replay import prohibited_provider


def file_hash(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def read(path: Path):
    return json.loads(path.read_bytes())


def current_universe(database: Path, at: datetime) -> dict:
    def connect():
        connection = sqlite3.connect(f"{database.as_uri()}?mode=ro", uri=True)
        connection.execute("PRAGMA query_only = ON")
        return connection

    engine = create_engine("sqlite://", creator=connect)
    try:
        with Session(engine) as session:
            return {
                market: production_universe_snapshot(
                    session, market, cutoff=at, session_key=f"daily_{market}",
                ).to_dict() for market in ("us", "kr")
            }
    finally:
        engine.dispose()


def provider_telemetry_audit(rows: list[dict]) -> dict:
    counts = {}
    forbidden = []
    for row in rows:
        provider = row["provider"]
        current = counts.setdefault(provider, {"success_events": 0, "failure_events": 0,
                                               "skipped_events": 0})
        for prefix in ("success", "failure", "skip"):
            key = "skipped_events" if prefix == "skip" else f"{prefix}_events"
            current[key] += int(row.get(prefix + "_delta", 0))
        if prohibited_provider(provider) and (
            int(row.get("success_delta", 0)) or int(row.get("failure_delta", 0))
        ):
            forbidden.append({k: row.get(k) for k in (
                "provider", "endpoint", "ticker", "success_delta", "failure_delta",
            )})
    return {"provider_events": counts, "prohibited_acquisition_events": forbidden,
            "interpretation": "historical_telemetry_events_not_exact_HTTP_call_counts",
            "current_task_provider_calls": 0}


def raw_ohlcv_artifacts(root: Path) -> list[dict]:
    """Search only declared source archive areas, never another run or operating cache."""
    result = []
    for relative in ("source", "private/source-results", "private/current-packets",
                     "private/isolated-data/market", "private/isolated-data/market-context"):
        for path in sorted((root / relative).rglob("*.json")):
            if path.is_symlink() or path.stat().st_size > 16 * 1024 * 1024:
                continue
            try:
                payload = read(path)
            except (ValueError, OSError):
                continue
            # OHLCV owner's HTTP boundary expects these at the payload root.
            if (isinstance(payload, dict) and isinstance(payload.get("periods"), dict)
                    and isinstance(payload.get("resolved_symbol"), dict)):
                result.append({"path": str(path.relative_to(root)), "sha256": file_hash(path)})
    return result


def audit_archive(root: Path, universe: dict) -> dict:
    manifest_path = root / "report/source-snapshot-manifest.json"
    manifest = read(manifest_path)
    manifest_rows = {r["market"]: r for r in manifest["rows"]}
    telemetry_path = root / "report/provider-telemetry.json"
    telemetry = provider_telemetry_audit(read(telemetry_path)["rows"])
    ledger_path = root / "report/source-call-ledger.json"
    ledger = read(ledger_path)
    prices = []
    markets = []
    for market in ("us", "kr"):
        raw_path = root / f"private/current-packets/{market}.json"
        projected_path = root / f"snapshot/{market}-packet.json"
        packet = read(projected_path)
        expected = universe[market]["eligible_subjects"]
        actual = [s["ticker"] for s in packet["stocks"]]
        binding = manifest_rows[market]
        markets.append({
            "market": market, "subjects": actual, "canonical_subjects_equal": actual == expected,
            "raw_packet_sha256": file_hash(raw_path),
            "projected_packet_sha256": file_hash(projected_path),
            "manifest_binding_pass": file_hash(raw_path) == binding["raw_sha256"]
            and file_hash(projected_path) == binding["projected_sha256"],
            "generated_at": packet["generated_at"],
            "session_validation": validate_market_packet_session_parity(packet),
            "message_ids": [f"MARKET_{market.upper()}", *actual],
            "expected_message_count": len(expected) + 1,
        })
        for stock in packet["stocks"]:
            technical = stock.get("technical_context") or {}
            prices.append({
                "market": market, "ticker": stock["ticker"],
                "owner": "app.services.ohlcv_client.OhlcvClient._request_period",
                "source": technical.get("source"),
                "normalized_bar_fingerprint": technical.get("raw_bar_fingerprint"),
                "acquisition": technical.get("acquisition"),
                "periods": ["daily", "weekly", "monthly", "weekly_unadjusted_valuation"],
                "role_bound_raw_receipt": "NOT_FOUND_IN_DECLARED_ARCHIVE",
                "qualification": "BLOCKED_NOT_RAW_RESPONSE_PROOF",
            })
    discovered = raw_ohlcv_artifacts(root)
    return {
        "archive": str(root), "generation_id": manifest["generation_id"],
        "audit_scope": "DECLARED_SOURCE_ARCHIVE_NOT_GLOBAL_FILESYSTEM",
        "source_manifest_sha256": file_hash(manifest_path),
        "telemetry_sha256": file_hash(telemetry_path),
        "source_call_ledger_sha256": file_hash(ledger_path),
        "source_call_owner_names": [r["owner"] for r in ledger["rows"]],
        "markets": markets, "ohlcv_receipt_coverage": prices,
        "standalone_ohlcv_response_candidates": discovered,
        "historical_provider_telemetry": telemetry,
        "source_parity": "BLOCKED",
        "blockers": [
            "OHLCV_REQUEST_RESPONSE_NORMALIZATION_ROLE_BINDING_ABSENT",
            "OPERATING_DATABASE_AND_CACHE_COPY_NOT_ATTEMPT_OWNERSHIP_PROOF",
        ] + (["HISTORICAL_ACQUISITION_NOT_ZERO_ALPHA"]
             if telemetry["prohibited_acquisition_events"] else []),
        "live_model_gate": "NOT_REACHED_SECTION_8_FAILED",
        "adapter_qualified": False,
    }


def run(database: Path, roots: list[Path], output: Path) -> dict:
    if output.exists():
        raise FileExistsError("immutable_preflight_output_exists")
    at = datetime.now(timezone.utc)
    database_before = file_hash(database)
    universe = current_universe(database, at)
    if [len(universe[m]["eligible_subjects"]) for m in ("us", "kr")] != [14, 8]:
        raise ValueError("canonical_population_drift")
    receipt = {
        "contract": "r5f-r2-offline-source-adapter-preflight-v1", "observed_at": at.isoformat(),
        "universe": universe, "universe_hash": digest(universe),
        "archives": [audit_archive(root, universe) for root in roots],
        "database_before_sha256": database_before, "database_after_sha256": file_hash(database),
        "database_connection": "mode=ro; PRAGMA query_only=ON",
        "production_mutations": 0, "provider_calls": 0, "model_calls": 0,
        "telegram_sends": 0, "scheduler_mutations": 0, "remote_push": 0,
        "status": "M12DS_R6_R5F_R2_ADAPTER_PARITY_GAP_REMAINS",
        "adapter_registered": False, "ready_for_promotion": False,
    }
    durable_json(output, receipt, exclusive=True)
    return receipt


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", required=True, type=Path)
    parser.add_argument("--archive", required=True, action="append", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    result = run(args.database, args.archive, args.output)
    print(json.dumps({"status": result["status"], "archives": len(result["archives"]),
                      "model_calls": 0, "provider_calls": 0}))
