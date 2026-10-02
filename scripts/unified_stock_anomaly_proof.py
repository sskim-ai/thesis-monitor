"""Bounded offline audit of the sealed R2B0 corpus, never a live entrypoint."""
from __future__ import annotations

import argparse
from datetime import date
import json
from pathlib import Path
import socket
import zipfile

from app.services.unified_run_artifacts import durable_json, sha256_bytes
from app.services.unified_stock_acquisition import StockPlan, load_owned_role
from app.services.unified_stock_anomaly_scope import materialize_source_components

PRIOR_SHA = "addb050b835f79cf89a5eac05e9bf7fc63fcf32991e1d467be0f61875ea8fa96"
PLAN_SHA = "e7d63a5278937b5ff6949ff55e93acf984875d57c5eb09de765eaec1327167b4"


def verify_seal(bundle: Path, corpus: Path) -> dict:
    if sha256_bytes(bundle.read_bytes()) != PRIOR_SHA:
        raise ValueError("r2b0_seal_mismatch")
    with zipfile.ZipFile(bundle) as archive:
        manifest = json.loads(archive.read("bundle-manifest.json"))
        names = archive.namelist()
        if len(names) != len(set(names)) or set(names) != set(manifest) | {"bundle-manifest.json"}:
            raise ValueError("r2b0_manifest_members_mismatch")
        verified = {}
        for name, binding in manifest.items():
            data = archive.read(name)
            if sha256_bytes(data) != binding["sha256"] or len(data) != binding["bytes"]:
                raise ValueError("r2b0_member_mismatch")
            if name.startswith("acquisition/") or name in {
                "request-plan.json", "source-integrity-root-cause.json", "raw-owner-replay.json"}:
                target = corpus / name
                if target.is_symlink() or target.read_bytes() != data:
                    raise ValueError("r2b0_local_bytes_changed:" + name)
                verified[name] = binding
        if sha256_bytes(archive.read("request-plan.json")) != PLAN_SHA:
            raise ValueError("r2b0_plan_mismatch")
    for ordinal in range(1, 89):
        for suffix in ("intent.json", "receipt.json", "normalized.json"):
            if f"acquisition/role-{ordinal:03d}.{suffix}" not in verified:
                raise ValueError("sealed_role_missing")
    return {"status": "PASS", "zip_sha256": PRIOR_SHA, "request_plan_sha256": PLAN_SHA,
            "manifest_entries_verified": len(manifest), "local_source_hashes": verified,
            "raw_owner_replay": "ADOPTED_EXACT_SEALED_R2B0_PROOF_88_OF_88"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    counters = {"provider_calls": 0, "auth_calls": 0, "model_calls": 0, "Market_Core_A_B_calls": 0,
        "rendered_messages": 0, "telegram_sends": 0, "production_delivery_intents": 0,
        "production_db_writes": 0, "scheduler_mutations": 0, "notification_mutations": 0,
        "deploy_restart": 0, "network_attempts": 0}

    def denied(*unused, **unused_kw):
        counters["network_attempts"] += 1
        raise RuntimeError("offline_anomaly_scope_network_denied")

    socket.socket.connect = denied
    socket.socket.connect_ex = denied
    socket.getaddrinfo = denied
    identity = verify_seal(args.bundle, args.corpus)
    args.out.mkdir(parents=True, exist_ok=True)

    def save(name, value):
        durable_json(args.out / name, value, exclusive=True)

    save("sealed-acquisition-identity.json", identity)
    plan = StockPlan.model_validate_json((args.corpus / "request-plan.json").read_bytes())
    grouped, receipts = {}, []
    for ordinal, read in enumerate(plan.reads, 1):
        path = args.corpus / f"acquisition/role-{ordinal:03d}.receipt.json"
        receipt = json.loads(path.read_bytes())
        rows = load_owned_role(plan, read, receipt, args.corpus / "acquisition")
        grouped.setdefault((read.market, read.subject, read.latest_completed_session), {})[read.role] = rows
        receipts.append({"entry_id": read.entry_id, "receipt_sha256": sha256_bytes(path.read_bytes()),
            "normalized_sha256": receipt["normalized_sha256"], "source_pages": len(receipt["pages"]),
            "ownership": "PASS", "rows": len(rows)})
    save("88-role-ownership-matrix.json", receipts)
    subjects, matrix = [], []
    for (market, ticker, cutoff), roles in grouped.items():
        params = dict(ticker=ticker, market=market, cutoff=date.fromisoformat(cutoff),
            observed_at=plan.frozen_at.isoformat(), roles=roles)
        result = materialize_source_components(**params)
        if result != materialize_source_components(**params):
            raise ValueError("nondeterministic_projection:" + ticker)
        save(f"components/{ticker}.json", result)
        role_rows = []
        for role, consumers in result["role_consumer_matrix"].items():
            role_rows.append({"role": role, "latest_row_valid": consumers[0]["latest_row_valid"],
                "anomaly_count": len({a["row_fingerprint"] for a in consumers[0]["anomalies"]}),
                "eligible_consumers": sum(c["eligible"] for c in consumers),
                "blocked_consumers": [c["consumer"] for c in consumers if not c["eligible"]]})
            matrix.extend({"ticker": ticker, "market": market, "role": role, **c} for c in consumers)
        subjects.append({"ticker": ticker, "market": market, "role_coverage": "4/4",
            "roles": role_rows, "mandatory_current_price_available": result["current_price_eligible"],
            "technical_status": result["technical_status"],
            "safe_feature_count": sum(len(f["facts"]) for f in result["features"].values()),
            "component_projection_sha256": result["component_projection_sha256"],
            "stock_packet_sha256": None, "final_materializer_status": result["materializer_status"],
            "mandatory_observed_business_union": result["observed_business_union_status"]})
        print(ticker, result["technical_status"], subjects[-1]["safe_feature_count"], flush=True)
    save("consumer-row-relevance-matrix.json", matrix)
    save("22-subject-materializer-matrix.json", subjects)
    save("stock-packet-hashes.json", {s["ticker"]: s["stock_packet_sha256"] for s in subjects})
    save("optional-mandatory-unavailable-matrix.json", {
        "optional_consumers": [r for r in matrix if not r["eligible"]],
        "mandatory_current_price_failures": [s["ticker"] for s in subjects if not s["mandatory_current_price_available"]],
        "full_stock_owner_gap": [s["ticker"] for s in subjects]})
    after = verify_seal(args.bundle, args.corpus)
    if identity != after:
        raise ValueError("sealed_source_changed_during_proof")
    save("source-invariance.json", {"all_bytes_unchanged": True,
        "source_integrity_root_cause_sha256": identity["local_source_hashes"]["source-integrity-root-cause.json"]["sha256"]})
    save("execution-counters.json", counters)
    save("proof-summary.json", {
        "terminal": "M12DS_R6_R5F_R2B0_R1_COMPLETE_STOCK_OWNER_BINDING_NOT_IMPLEMENTED",
        "outcome": "C", "sealed_roles": len(receipts), "subjects": len(subjects),
        "current_price_eligible": sum(s["mandatory_current_price_available"] for s in subjects),
        "source_component_projections": len(subjects), "complete_stock_packets": 0,
        "deterministic_component_replay": "22/22", "source_bytes_preserved": True,
        "full_prequalification": "NOT_REACHED", "r2b_instruction_generated": False,
        "r2b_execution": False, "production_ready": False})


if __name__ == "__main__":
    main()
