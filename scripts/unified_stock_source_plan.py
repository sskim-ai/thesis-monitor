"""Freeze/check the one-shot source plan without making provider requests."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
import subprocess
import zipfile

from app.config import Settings
from app.services.ohlcv_client import OHLCV_PROVIDER_REQUEST_LIMIT, PERIOD_COUNTS, PRICE_STRUCTURE_PERIOD_COUNTS
from app.services.unified_run_artifacts import durable_bytes, durable_json, sha256_bytes
from app.services.unified_snapshot_contract import digest
from app.services.unified_stock_acquisition import UNIVERSE, ROLES, StockPlan, coverage, make_reads, validate_role
from scripts.unified_adapter_preflight import current_universe
from scripts.unified_snapshot_inventory import inventory


PRIOR_SHA = "4ddc75eae2e189c6f81a1a989f9956c64f2837f610524829e55f4af0700ee23e"


def git(root, *args):
    return subprocess.check_output(["git", *args], cwd=root, text=True).strip()


def state(root, operating):
    settings = Settings(_env_file=operating / ".env")
    values = settings.model_dump(mode="json")
    return {"head": git(root, "rev-parse", "HEAD"), "branch": git(root, "branch", "--show-current"),
            "clean": not git(root, "status", "--porcelain"),
            "operating_head": git(operating, "rev-parse", "HEAD"),
            "operating_clean": not git(operating, "status", "--porcelain"),
            "config": {"operating_env_sha256": sha256_bytes((operating / ".env").read_bytes()),
                "effective_settings_sha256": digest(values),
                "provider_settings_sha256": digest({k: v for k, v in values.items() if any(
                    term in k for term in ("provider", "api", "ohlcv", "kiwoom", "alpha", "macro"))}),
                "tracked": {p: sha256_bytes((root / p).read_bytes()) for p in ("app/config.py", ".env.example")}},
            "scheduler": inventory(Path.home(), operating), "secret_values_exported": False}


def freeze(root, operating, out, owner_config, prior_zip, instruction_sha):
    if sha256_bytes(prior_zip.read_bytes()) != PRIOR_SHA:
        raise ValueError("prior_r5_identity_mismatch")
    with zipfile.ZipFile(prior_zip) as archive:
        manifest = json.loads(archive.read("bundle-manifest.json"))
        if set(archive.namelist()) != set(manifest) | {"bundle-manifest.json"}:
            raise ValueError("prior_bundle_manifest_mismatch")
        for name, binding in manifest.items():
            data = archive.read(name)
            if sha256_bytes(data) != binding["sha256"] or len(data) != binding["bytes"]:
                raise ValueError("prior_bundle_artifact_mismatch")
    before = state(root, operating)
    if not before["clean"] or not before["operating_clean"]:
        raise ValueError("clean_worktree_and_operating_required")
    at = datetime.now(timezone.utc)
    db = operating / "data/thesis_monitor.sqlite3"
    universe = current_universe(db, at)
    with sqlite3.connect(f"{db.as_uri()}?mode=ro", uri=True) as connection:
        connection.execute("PRAGMA query_only=ON")
        connection.row_factory = sqlite3.Row
        identities = {r["ticker"]: dict(r) for r in connection.execute(
            "SELECT ticker,canonical_security_id,exchange FROM securitymaster")}
    settings = Settings(_env_file=operating / ".env")
    if settings.ohlcv_base_url.rstrip("/") != "http://127.0.0.1:8765":
        raise ValueError("configured_ohlcv_owner_not_local_verified_owner")
    owner = json.loads(owner_config.read_bytes())
    if not owner["owner_clean"] or not owner["live_provider"] or not owner["credentials_present"] or owner["environment"] != "real":
        raise ValueError("owner_configuration_not_ready")
    counts = {}
    for market in UNIVERSE:
        enabled = settings.us_price_structure_v3_enabled if market == "us" else settings.kr_price_structure_v3_enabled
        configured = PRICE_STRUCTURE_PERIOD_COUNTS if enabled else PERIOD_COUNTS
        counts[market] = {role: (PERIOD_COUNTS["weekly"] if not adjusted else
            max(min(configured[period], OHLCV_PROVIDER_REQUEST_LIMIT), 300 if period == "monthly" else 700))
            for role, (period, adjusted) in ROLES.items()}
    plan = StockPlan(run_id="m12ds-r6-r5f-r2b0-" + at.strftime("%Y%m%dT%H%M%SZ"),
        acquisition_id="stock-source-only-one-shot-" + at.strftime("%Y%m%dT%H%M%SZ"),
        frozen_at=at, instruction_sha=instruction_sha, implementation_sha=before["head"],
        universe_sha256=digest(universe), reads=make_reads(universe, identities, at=at, counts=counts),
        **{k: owner[k] for k in ("owner_files", "owner_head", "settings_sha256", "request_environment_sha256")})
    durable_json(out / "state-before.json", before, exclusive=True)
    durable_json(out / "canonical-universe.json", universe, exclusive=True)
    durable_json(out / "canonical-identities.json", {t: identities[t] for ts in UNIVERSE.values() for t in ts}, exclusive=True)
    durable_json(out / "prior-r5-identity.json", {"status": "VERIFIED", "zip_sha256": PRIOR_SHA,
        "manifest_entries": len(manifest), "final": "fdc1a1e69f3941676927b38c4d81ba4b4d6d369c",
        "krx_historical_owner_sha256": "68991ed322b5d067f46e6d0a1ae4f9151533ff10177e4d31ab61997c39210937",
        "krx_historical_aggregate_sha256": "27ff01fb38ccae666ff254a5f5c8c0ebad011d76fa9828db85181afca1b30ee0",
        "krx_recollected": False, "krx_relabelled_current": False}, exclusive=True)
    durable_json(out / "request-plan.json", plan.model_dump(mode="json"), exclusive=True)
    file_hash = sha256_bytes((out / "request-plan.json").read_bytes())
    durable_bytes(out / "request-plan.json.sha256", (file_hash + "  request-plan.json\n").encode(), exclusive=True)
    print(json.dumps({"plan_entries": len(plan.reads), "plan_file_sha256": file_hash,
                      "run_id": plan.run_id, "instruction_sha": instruction_sha, "implementation_sha": before["head"]}))


def verify(out):
    plan = StockPlan.model_validate_json((out / "request-plan.json").read_bytes())
    raw_root = out / "acquisition"
    replay = {r["entry_id"]: r for r in json.loads((out / "raw-owner-replay.json").read_bytes())}
    rows = []
    for ordinal, read in enumerate(plan.reads, 1):
        receipt = json.loads((raw_root / f"role-{ordinal:03d}.receipt.json").read_bytes())
        try:
            row = validate_role(plan, read, receipt, raw_root)
            if replay[read.entry_id]["status"] != "PASS":
                raise ValueError("independent_raw_owner_replay_failed")
        except (ValueError, KeyError, OSError) as exc:
            row = {"entry_id": read.entry_id, "status": "FAIL", "error": str(exc),
                   "source_status": receipt["status"], "source_error_class": receipt.get("error_class")}
        rows.append(row)
    result = coverage(plan, rows)
    durable_json(out / "coverage.json", result, exclusive=True)
    durable_json(out / "failure-matrix.json", [r for r in rows if r["status"] != "PASS"], exclusive=True)
    print(json.dumps({k: v for k, v in result.items() if k != "rows"}))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("freeze", "verify", "after"))
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--operating", required=True, type=Path)
    parser.add_argument("--owner-config", type=Path)
    parser.add_argument("--prior-zip", type=Path)
    parser.add_argument("--instruction-sha")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    if args.mode == "freeze":
        freeze(root, args.operating, args.output, args.owner_config, args.prior_zip, args.instruction_sha)
    elif args.mode == "verify":
        verify(args.output)
    else:
        after = state(root, args.operating)
        before = json.loads((args.output / "state-before.json").read_bytes())
        def stable_scheduler(value):
            return {k: v for k, v in value.items() if k != "observed_at"}
        checks = {"config_unchanged": before["config"] == after["config"],
                  "operating_head_unchanged": before["operating_head"] == after["operating_head"],
                  "operating_clean": after["operating_clean"], "worktree_clean": after["clean"],
                  "scheduler_unchanged": stable_scheduler(before["scheduler"]) == stable_scheduler(after["scheduler"])}
        durable_json(args.output / "state-after.json", after, exclusive=True)
        durable_json(args.output / "state-invariance.json", checks, exclusive=True)
        if not all(checks.values()):
            raise ValueError("source_only_state_invariance_failed")
        print(json.dumps(checks))


if __name__ == "__main__":
    main()
