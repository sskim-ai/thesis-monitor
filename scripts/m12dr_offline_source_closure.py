"""Read-only M12DQ source reclassification. No provider or model entrypoints."""

from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sqlite3
import sys

from app.models.financial import FinancialSnapshot
from app.services.accepted_decision_v2_runtime_service import (
    AcceptedV2EvidenceOwnership,
    AcceptedV2ProductionContext,
    interaction_from_packet,
)
from app.services.direction_timing_ownership_service import build_owned_evidence_packet
from scripts.m12cn_policy_contract import build_subject_catalog
from scripts.m12da_source_use_contract import canonical_sha256
from scripts.m12dk_current_source_authority import freeze_current_source_binding
from scripts.m12dp_observed_business_coverage import evaluate_cohort
from scripts.m12dr_financial_source_authority import (
    FAMILY, build_source_authority, comparative_facts, issuer_projection_receipt, source_quality,
)
from app.services.financial_observation_quality_service import digest
from scripts.v2_production_cutover_preflight import (
    build_decision_evidence_packet, packet_owned_context_for_stock,
)
from scripts.m12ds_r4_r2_selected_source_quality import (
    apply_selected_gate, comparison_bundle, select_source,
)


def read(path):
    return json.loads(path.read_bytes())


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, default=str) + "\n")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def context(packet, generation):
    packets, ownership = [], []
    for stock in packet["stocks"]:
        ep = build_decision_evidence_packet(packet=packet, stock=stock,
                                            technical_context=packet_owned_context_for_stock(packet=packet, stock=stock))
        owned = build_owned_evidence_packet(ep, stock=stock)
        packets.append(ep)
        ownership.append(AcceptedV2EvidenceOwnership(
            ticker=stock["ticker"], core_ref_ids=tuple(sorted(owned.core_refs)),
            timing_ref_ids=tuple(sorted(owned.timing_refs)), expectation_valuation=interaction_from_packet(ep)))
    return AcceptedV2ProductionContext(
        packet_id=packet["packet_id"], claim_id=generation + "-" + packet["market"], market=packet["market"],
        assessment_date=packet["assessment_date"], source_packet_sha256=canonical_sha256(packet),
        selected_subjects=tuple(s["ticker"] for s in packet["stocks"]), evidence_packets=tuple(packets),
        evidence_ownership=tuple(ownership), prior_accepted=(),
        prepared_at=datetime.now(timezone.utc).isoformat()).model_dump(mode="json")


def run(baseline, output):
    if output.exists():
        raise ValueError("new_quality_output_directory_required")
    freeze = read(baseline / "report/coverage-input-freeze.json")
    for path, expected in freeze["files"].items():
        if sha(baseline / path) != expected:
            raise ValueError("baseline_source_drift")
    generation = freeze["source_generation_id"]
    packets = {m: read(baseline / f"snapshot/{m}-packet.json") for m in ("us", "kr")}
    coverage = read(baseline / "report/observed-business-source-coverage-matrix.json")
    binding_rows = read(baseline / "report/issuer-security-binding.json")
    if binding_rows["generation_id"] != generation:
        raise ValueError("issuer_binding_generation_mismatch")
    bindings = {r["ticker"]: r for r in binding_rows["rows"]}
    targets = [r["ticker"] for r in coverage["subjects"]
               if r["market"] == "kr" and r["status"] == "SOURCE_QUALITY_UNUSABLE"]
    sec_targets = [r["ticker"] for r in coverage["subjects"] if r["market"] == "us"]
    database = baseline / "private/isolated-data/thesis_monitor.sqlite3"
    db_before = sha(database)
    bundles, qualities, projections = {}, {}, []
    selected_rows, source_rows, selected_audits = {}, {}, {}
    with sqlite3.connect(database.as_uri() + "?mode=ro", uri=True) as db:
        db.row_factory = sqlite3.Row
        for packet in packets.values():
            for stock in packet["stocks"]:
                ticker = stock["ticker"]
                rows = [FinancialSnapshot.model_validate(dict(r)) for r in db.execute(
                    "select * from financialsnapshot where ticker=? order by financial_period_end, filing_date, id",
                    (ticker,))]
                selected, audit = select_source(stock=stock, rows=rows, binding=bindings[ticker],
                    cutoff=datetime.fromisoformat(packet["assessment_date"]).date())
                selected_rows[ticker], source_rows[ticker], selected_audits[ticker] = selected, rows, audit
        for ticker in targets:
            stock = next(s for s in packets["kr"]["stocks"] if s["ticker"] == ticker)
            earnings = [f for f in stock["fact_catalog"] if f.get("fact_type") == "earnings"]
            if len(earnings) != 1:
                raise ValueError("quality_target_exact_earnings_snapshot_missing")
            source = earnings[0]["financial_quality"]["source_snapshot"]
            rows = [FinancialSnapshot.model_validate(dict(r)) for r in db.execute(
                "select * from financialsnapshot where ticker=? and financial_period_end=? "
                "and source_filing_id is not null and source_filing_id != ''", (ticker, source["period"]))]
            formals = [r for r in rows if r.snapshot_type == "full_statement"
                       and str(r.filing_date) == source["filing_date"]]
            prelims = [r for r in rows if r.snapshot_type == "preliminary_earnings"
                       and str(r.filing_date) <= packets["kr"]["assessment_date"]]
            if len(formals) != 1:
                raise ValueError("quality_formal_snapshot_ambiguous")
            preliminary = max(prelims, key=lambda r: r.filing_date) if prelims else None
            inputs = {"ticker": ticker, "cutoff": packets["kr"]["assessment_date"],
                      "formal": formals[0].model_dump(mode="json"),
                      "preliminary": preliminary.model_dump(mode="json") if preliminary else None}
            bundle = {"source_generation_id": generation, "source_inputs": inputs,
                      "source_inputs_sha256": digest(inputs), "frozen_database_sha256": db_before}
            bundles[ticker] = bundle
            qualities[ticker] = source_quality(bundle)
            stock["fact_catalog"].extend(comparative_facts(
                qualities[ticker], ticker=ticker, issuer_id=bindings[ticker]["issuer_id"]))
        for ticker in sec_targets:
            cutoff = packets["us"]["assessment_date"]
            formal = selected_rows[ticker]
            if formal is None:
                continue
            bundle, quality = comparison_bundle(selected=formal, rows=source_rows[ticker],
                audit=selected_audits[ticker], binding=bindings[ticker],
                cutoff=datetime.fromisoformat(cutoff).date(), generation=generation, database_sha256=db_before)
            if bundle is None:
                continue
            bundles[ticker], qualities[ticker] = bundle, quality
            stock = next(s for s in packets["us"]["stocks"] if s["ticker"] == ticker)
            stock["fact_catalog"].extend(comparative_facts(
                quality, ticker=ticker, issuer_id=bindings[ticker]["issuer_id"]))
    for stock in packets["us"]["stocks"]:
        underlying = ((stock.get("valuation") or {}).get("security_identity_provenance") or {}).get(
            "evidence", {}).get("ordinary_share_identifier")
        if underlying not in qualities or qualities[underlying]["status"] != "PASS":
            continue
        projection = issuer_projection_receipt(security_stock=stock, underlying_ticker=underlying,
                                               issuer_binding=bindings[underlying],
                                               cutoff=packets["us"]["assessment_date"])
        projections.append(projection)
        if projection["status"] == "PASS":
            stock["fact_catalog"].extend(comparative_facts(
                qualities[underlying], ticker=stock["ticker"], issuer_id=bindings[underlying]["issuer_id"],
                projection=projection))
    contexts = {m: context(packets[m], generation) for m in packets}
    inputs, authorities = [], {}
    for market, ctx in contexts.items():
        for ticker in sorted(ctx["selected_subjects"]):
            cat = build_subject_catalog(context=ctx, ticker=ticker, atomic_claims=[])
            ep = next(r for r in ctx["evidence_packets"] if r["ticker"] == ticker)
            metadata = [r for r in ep["evidence"] if r["ref_id"] in cat["all_evidence_refs"]]
            args = dict(ticker=ticker, source_generation_id=generation, source_packet=packets[market],
                        evidence_packet=ep, catalog=cat, source_metadata=metadata,
                        frozen_binding=freeze_current_source_binding(source_generation_id=generation,
                                                                     source_packet=packets[market], evidence_packet=ep))
            authorities[ticker] = build_source_authority(quality_bundles=bundles, issuer_bindings=bindings, **args)
            inputs.append({**args, "issuer_binding": bindings[ticker],
                           "expected_issuer_binding_sha256": canonical_sha256(bindings[ticker])})
    old_gate = evaluate_cohort(inputs, expected_subjects=sorted(bindings))
    gate = deepcopy(old_gate)
    for row in gate["subjects"]:
        ticker = row["ticker"]
        authority = authorities[ticker]
        newly_ready = [r["ref_id"] for r in authority["family_receipts"]
                       if r["source_family"] == FAMILY and not r["errors"]
                       and r["authority_state"] == "RESOLVED" and "OVERALL_DIRECTION" in r["allowed_uses"]]
        if (newly_ready and not row.get("binding_error")
                and row["status"] != "ISSUER_SECURITY_BINDING_UNRESOLVED"):
            row.update(status="DIRECTIONAL_BUSINESS_SOURCE_READY", ready_for_authority_aware_core_preflight=True,
                       directional_source_refs=sorted(set(row["directional_source_refs"] + newly_ready)),
                       source_authority=authority, extension_source_refs=newly_ready)
        audit = selected_audits[ticker]
        projection = next((p for p in projections if p["security_ticker"] == ticker and p["status"] == "PASS"), None)
        if projection:
            audit["issuer_business_projection"] = projection
            audit["selection_errors"] = []
            audit["selection_basis"] = "VERIFIED_ISSUER_BUSINESS_PROJECTION_NO_SECURITY_DENOMINATOR"
        elif ticker in sec_targets:
            apply_selected_gate(row, audit, newly_ready)
        audit["directional_source_refs"] = row["directional_source_refs"]
        audit["direction_status"] = row["status"]
        if ticker in qualities:
            audit["field_owned_quality_receipt"] = qualities[ticker]
    gate["ready_count"] = sum(r["status"] == "DIRECTIONAL_BUSINESS_SOURCE_READY" for r in gate["subjects"])
    gate["status_counts"] = dict(Counter(r["status"] for r in gate["subjects"]))
    complete = gate["ready_count"] == gate["active_count"] and not gate["binding_errors"]
    terminal = "M12DR_SOURCE_PASS_PENDING_BLIND_FREEZE" if complete else "M12DR_SOURCE_COVERAGE_STILL_INCOMPLETE"
    if any(q["status"] != "PASS" for q in qualities.values()):
        terminal = "M12DR_000660_QUALITY_SOURCE_STILL_UNUSABLE"
    elif any(p["status"] != "PASS" for p in projections):
        terminal = "M12DR_SKHY_ISSUER_BUSINESS_BINDING_FAILED"
    gate.update(terminal=terminal, source_generation_id=generation, allow_core_preflight=complete,
                allow_model_calls=False, next_gate="BLIND_FREEZE_THEN_CORE_PREFLIGHT" if complete else None)
    if sha(database) != db_before or any(sha(baseline / p) != h for p, h in freeze["files"].items()):
        raise ValueError("frozen_input_modified")
    write(output / "report/source-input-binding.json", {"baseline": str(baseline), **freeze,
                                                       "database_sha256": db_before, "database_unchanged": True})
    write(output / "report/quality-receipts.json", qualities)
    write(output / "report/foreign-filing-comparative-lineage-audit.json", {
        "rows": [row for row in selected_audits.values() if (row.get("selected") or {}).get("provider") == "sec_foreign_filing"]
    })
    write(output / "source/quality-inputs.json", bundles)
    write(output / "source/issuer-bindings.json", bindings)
    write(output / "report/issuer-business-projection.json", projections)
    write(output / "report/source-coverage.json", gate)
    write(output / "report/selected-source-quality-audit.json", {
        "contract": "m12ds-r4-r2-selected-source-quality-ownership-v1",
        "source_generation_id": generation, "database_sha256": db_before,
        "rows": [selected_audits[t] for t in sorted(selected_audits)]})
    for market in packets:
        write(output / f"snapshot/{market}-packet.json", packets[market])
        write(output / f"snapshot/{market}-context.json", contexts[market])
    print(json.dumps({"terminal": terminal, "ready": gate["ready_count"], "active": gate["active_count"],
                      "comparisons": {t: len(q["comparative_observations"]) for t, q in qualities.items()},
                      "model_calls": 0}, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    def offline(event, _args):
        if event in {"socket.connect", "socket.getaddrinfo", "subprocess.Popen", "os.system"}:
            raise RuntimeError("OFFLINE_SOURCE_BOUNDARY")

    sys.addaudithook(offline)
    run(args.baseline, args.output)


if __name__ == "__main__":
    main()
