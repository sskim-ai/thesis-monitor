"""Offline R2 proof, explicit source corpus plus read-only Class-C capture."""

import argparse
import json
from pathlib import Path
import socket
import sqlite3
import zipfile

from sqlalchemy import event
from sqlmodel import Session, create_engine

from app.services.unified_class_c_owners import project_local_seed, project_reported_financial
from app.services.unified_run_artifacts import durable_json, sha256_bytes
from app.services.unified_snapshot_contract import digest
from app.services.unified_source_composition import C, SourceRole
from app.services.unified_source_policy import UnifiedSourcePolicy
from app.services.unified_stock_acquisition import StockPlan, UNIVERSE
from app.services.unified_stock_owner import assemble_stock, validate_assembled
from scripts.unified_stock_anomaly_proof import verify_seal


R1_SHA = "fa2303620ff762778606aaac32cfc97520d07f469a523a9463ded43e150d4ee1"
POLICY = UnifiedSourcePolicy(frozenset({"canonical_local", "local", "local+openfigi",
    "sec_official_identity", "sec_edgar", "sec_companyfacts", "sec_foreign_filing", "opendart"}))


def r1_identity(path):
    if sha256_bytes(path.read_bytes()) != R1_SHA:
        raise ValueError("r1_zip_identity_mismatch")
    with zipfile.ZipFile(path) as archive:
        manifest = json.loads(archive.read("bundle-manifest.json"))
        if set(archive.namelist()) != set(manifest) | {"bundle-manifest.json"}:
            raise ValueError("r1_manifest_members_mismatch")
        for name, item in manifest.items():
            raw = archive.read(name)
            if sha256_bytes(raw) != item["sha256"] or len(raw) != item["bytes"]:
                raise ValueError("r1_manifest_hash_mismatch")
        components = {t: json.loads(archive.read("proof-final/components/" + t + ".json"))
            for ts in UNIVERSE.values() for t in ts}
    return {"sha256": R1_SHA, "manifest_entries_verified": len(manifest)}, components


def capture(db, out, plan):
    reads = set()

    def authorize(action, table, column, database, trigger):
        if action == sqlite3.SQLITE_READ:
            if table not in {"watchlistitem", "securitymaster", "investmentthesis", "company",
                             "financialsnapshot", "event"}:
                return sqlite3.SQLITE_DENY
            reads.add((table, column))
        return sqlite3.SQLITE_OK

    def connect():
        connection = sqlite3.connect(f"{db.resolve().as_uri()}?mode=ro", uri=True)
        connection.execute("PRAGMA query_only=ON")
        connection.set_authorizer(authorize)
        return connection
    engine = create_engine("sqlite://", creator=connect)
    queries = []

    @event.listens_for(engine, "before_cursor_execute")
    def guard(conn, cursor, statement, parameters, context, executemany):
        if not statement.lstrip().upper().startswith(("SELECT", "PRAGMA")):
            raise RuntimeError("readonly_capture_sql_write_denied")
        queries.append(sha256_bytes(statement.encode()))
    try:
        with Session(engine) as session:
            for market, tickers in UNIVERSE.items():
                session_key = next(r.latest_completed_session for r in plan.reads if r.market == market)
                local = project_local_seed(session, market=market, session_key=session_key,
                    cutoff=plan.frozen_at, policy=POLICY)
                durable_json(out / f"class-c/local-{market}.json", local, exclusive=True)
                for ticker in tickers:
                    family = "sec_financial_fundamental_domains" if market == "us" else "opendart_financial_fundamental_domains"
                    role = SourceRole(key=family + ":" + ticker, owner="project_reported_financial",
                        market=market, symbol=ticker, acquisition_class=C, mandatory=False,
                        provider="sec_companyfacts" if market == "us" else "opendart",
                        basis="direct_reported_issuer_financial", session=session_key)
                    projection = project_reported_financial(session, role=family, ticker=ticker,
                        cutoff=plan.frozen_at, policy=POLICY)
                    durable_json(out / f"class-c/financial-{ticker}.json", {
                        "contract": "unified-persisted-owner-input-v1", "family": family,
                        "role": role.model_dump(mode="json"), "projection": projection}, exclusive=True)
    finally:
        engine.dispose()
    durable_json(out / "class-c-capture-receipt.json", {"database_mode": "ro;query_only=ON",
        "source_cutoff": plan.frozen_at.isoformat(), "read_statement_hashes": queries,
        "read_columns": sorted(reads),
        "prior_ai_assessment_reads": 0, "production_db_writes": 0,
        "source_class": "VERSIONED_PERSISTED_ALLOWED_NOT_NEW_PROVIDER_ACQUISITION"}, exclusive=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("capture", "prove"))
    for name in ("corpus", "r1-bundle", "output"):
        parser.add_argument("--" + name, required=True, type=Path)
    parser.add_argument("--database", type=Path)
    parser.add_argument("--proof-tag", default="proof-final")
    args = parser.parse_args()
    counters = {k: 0 for k in ("provider_calls", "auth", "alpha_vantage", "massive", "model_calls",
        "Market_Core_A_B_model_calls", "rendered_messages", "telegram_sends", "production_delivery_intents",
        "production_db_writes", "scheduler_mutations", "notification_mutations", "deploy_restart", "network_attempts")}

    def deny(*unused, **unused_kw):
        counters["network_attempts"] += 1
        raise RuntimeError("offline_stock_owner_network_denied")
    socket.socket.connect = socket.socket.connect_ex = socket.getaddrinfo = deny
    identity = verify_seal(args.corpus / "thesis-monitor-20260926-m12ds-r6-r5f-r2b0-report.zip", args.corpus)
    r1, components = r1_identity(args.r1_bundle)
    plan = StockPlan.model_validate_json((args.corpus / "request-plan.json").read_bytes())
    out = args.output
    if Path(args.proof_tag).name != args.proof_tag or args.proof_tag in {".", ".."}:
        raise ValueError("invalid_proof_tag")
    if args.mode == "capture":
        for name, value in (("R2B0-source-identity.json", identity), ("R1-identity.json", r1)):
            path = out / name
            if path.exists():
                if json.loads(path.read_bytes()) != value:
                    raise ValueError("existing_source_identity_changed")
            else:
                durable_json(path, value, exclusive=True)
        capture(args.database, out, plan)
        return
    proof = out / args.proof_tag
    rows = []
    for market, tickers in UNIVERSE.items():
        local = json.loads((out / f"class-c/local-{market}.json").read_bytes())
        for ticker in tickers:
            receipts, artifacts = {}, {}
            for index, read in enumerate(plan.reads, 1):
                if read.subject != ticker:
                    continue
                receipt = json.loads((args.corpus / f"acquisition/role-{index:03d}.receipt.json").read_bytes())
                receipts[read.role] = receipt
                for path in [receipt["normalized_artifact"], *[p["artifact"] for p in receipt["pages"]]]:
                    artifacts[path] = (args.corpus / "acquisition" / path).read_bytes()
            financial = json.loads((out / f"class-c/financial-{ticker}.json").read_bytes())
            hashes = {"local": digest(local), "financial": digest(financial),
                "components": digest(components[ticker]), "receipts": digest(receipts),
                "plan": digest(plan.model_dump(mode="json"))}
            params = dict(plan=plan, ticker=ticker, receipts=receipts, artifacts=artifacts,
                local_seed=local, financial=financial, components=components[ticker],
                expected_hashes=hashes, policy=POLICY)
            try:
                result = assemble_stock(**params)
            except ValueError as exc:
                failure = {"ticker": ticker, "market": market, "status": "BLOCKED",
                    "mandatory_missing": [str(exc)], "packet_sha256": None,
                    "role_coverage": "4/4", "current_price_eligible": components[ticker]["current_price_eligible"],
                    "safe_technical_facts": sum(len(f["facts"]) for f in components[ticker]["features"].values()),
                    "observed_business_cardinality": 0, "financial_state": {"status": "OWNER_BINDING_FAILED"},
                    "input_hashes": hashes, "numeric_registry_count": 0,
                    "numeric_registry_unregistered": None, "replay_exact": False}
                durable_json(proof / f"assembled/{ticker}.json", failure, exclusive=True)
                rows.append(failure)
                print(ticker, "BLOCKED", str(exc), flush=True)
                continue
            if result != assemble_stock(**params):
                raise ValueError("stock_owner_replay_nondeterministic")
            validate_assembled(result, expected_result_sha256=digest(result))
            durable_json(proof / f"assembled/{ticker}.json", result, exclusive=True)
            rows.append({"ticker": ticker, "market": market, "role_coverage": "4/4",
                "current_price_eligible": components[ticker]["current_price_eligible"],
                "safe_technical_facts": sum(len(f["facts"]) for f in components[ticker]["features"].values()),
                **{k: result[k] for k in ("status", "mandatory_missing", "packet_sha256", "diagnostic_packet_sha256",
                    "observed_business_cardinality", "financial_state")},
                "numeric_registry_count": len(result["packet"]["stocks"][0]["numeric_registry"]),
                "numeric_registry_unregistered": len(result["numeric_registry_unregistered"]),
                "replay_exact": True})
            print(ticker, result["status"], result["mandatory_missing"], flush=True)
    durable_json(proof / "22-subject-matrix.json", rows, exclusive=True)
    durable_json(proof / "source-invariance.json", {"unchanged": identity == verify_seal(
        args.corpus / "thesis-monitor-20260926-m12ds-r6-r5f-r2b0-report.zip", args.corpus),
        "r1_unchanged": r1 == r1_identity(args.r1_bundle)[0]}, exclusive=True)
    durable_json(proof / "execution-counters.json", counters, exclusive=True)


if __name__ == "__main__":
    main()
