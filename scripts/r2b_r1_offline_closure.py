"""Bounded, network-free date repair proof. No model/delivery route is called.

The original source and blind archives remain immutable. Reprojection produces a
separate view, not a replacement source or a widened authority manifest.
"""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
import json
from pathlib import Path
import sys

from app.services.canonical_evidence_time_service import validate_canonical_time
from app.services.cross_market_decision_engine_service import build_decision_evidence_packet
from app.services.structured_autonomy_shadow_service import ClaimSemanticMetadata
from scripts import m12ds_r4_r4_schemas as schemas
from scripts import r2b_sealed_blind_preflight as prior
from scripts.sealed_cohort_offline_proof import network_guard
from scripts.unified_event_union_proof import snapshot

BASE = "2829fd36ed9245b7c7199e134b531f7c9a0d226b"
BLIND_SHA = "d705d36dabfa99f8d096a2bce4ddf996229680650cb09a45abffb5d7e9213ec3"
BLOCKER_SHA = "72d1d9234af6158c649d34e536aa66e039ab7bd348fe9422b536d1315c9e5cf1"
RECEIPT_SHA = "f0f71fd39091369f280242d7a41af32a9cdbf3e0fa505fe2427f89b768eee26a"
SOURCE_HASHES = {
    "FullSourceRunSeed.json": "df3b7f1102fcacd27b70e594fb58b139644a7ba1daa18620279bf1a455916bdc",
    "us-whole-source-packet.json": "b2b603850e517c70d6a9a201b297952677d6542271f72db6f0eecbdebe09fdb1",
    "kr-whole-source-packet.json": "d3081027ec1203a5af09adc590b13ca81dce3c049a65b988606a0d3311f74845",
    "combined-full-source-packet.json": "c4fbc25ec81abe61c3981bfaa44204cc7e15cc252f25cbe6aedc6b2a1de9b44f",
    "full-source-authority-graph.json": "0b69d1913e139078ed42b0fb1c0b01928b065fd2d76863e3835622b3ee0992b6",
}


def reproject_time(stock):
    """Use the repaired producer but preserve every non-time field of the seal."""
    result = deepcopy(stock)
    ticker = stock["ticker"]
    sources = [s for s in stock["packet"]["stocks"] if s["ticker"] == ticker]
    if len(sources) != 1:
        raise ValueError("source_subject_identity_mismatch")
    source = sources[0]
    facts = {"canonical:" + f["fact_id"]: f for f in source["fact_catalog"]}
    if len(facts) != len(source["fact_catalog"]):
        raise ValueError("duplicate_canonical_fact_ref")
    produced = build_decision_evidence_packet(packet=stock["packet"], stock=source)
    projected = {r.ref_id: r.model_dump(mode="json") for r in produced.evidence}
    core_refs = prior.OwnedEvidencePacket.model_validate(stock["ownership"]).core_refs
    changes, matrix = [], []
    for row in result["evidence_packet"]["evidence"]:
        ref = row["ref_id"]
        if not ref.startswith("canonical:"):
            continue
        fact, fresh = facts[ref], projected[ref]
        before = deepcopy(row)
        if row["statement"] != fresh["statement"] or row["source_ref"] != fresh["source_ref"]:
            raise ValueError("non_time_canonical_projection_drift")
        row["as_of"], row["source_time"] = fresh["as_of"], fresh["source_time"]
        receipt = {"ticker": ticker, "ref_id": ref, "core_owned": ref in core_refs,
            "canonical_as_of": fact.get("as_of_date"), "before_as_of": before["as_of"],
            "after_as_of": row["as_of"], "source_time": row["source_time"],
            "canonical_fact_sha256": prior.digest(fact),
            "before_projection_sha256": prior.digest(before), "after_projection_sha256": prior.digest(row),
            "statement_sha256": prior.sha(row["statement"].encode()), "statement_bytes_unchanged": True,
            "non_time_fields_unchanged": {k: v for k, v in before.items() if k not in {"as_of", "source_time"}}
                == {k: v for k, v in row.items() if k not in {"as_of", "source_time"}}}
        try:
            validate_canonical_time(fact, row, ticker=ticker)
            receipt.update(status="PASS", error=None)
        except ValueError as exc:
            receipt.update(status="BLOCKED", error=str(exc))
        matrix.append(receipt)
        if before["as_of"] != row["as_of"]:
            changes.append(receipt)
    indexed = {r["ref_id"]: r for r in result["evidence_packet"]["evidence"]}
    result["ownership"]["source_packet"] = deepcopy(result["evidence_packet"])
    for item in result["ownership"]["evidence"]:
        item["ref"] = deepcopy(indexed[item["ref"]["ref_id"]])
    prior.OwnedEvidencePacket.model_validate(result["ownership"])
    assert result["packet"] == stock["packet"]
    return result, matrix, changes


def neutral_limit_contract_audit():
    claim = ClaimSemanticMetadata(claim_type="UNKNOWN_LIMIT", direction="OBSERVE")
    cap = {k: [] for k in ("positive", "negative", "confidence", "condition", "quality",
                           "holder_support", "holder_risk", "holder_reduce")}
    cap["risk_triggers"] = {}
    try:
        schemas.decision_schema(cap, {"fundamental_valid": False, "compensating_discount": False}, {})
        failure = None
    except ValueError as exc:
        failure = str(exc)
    return {"claim_semantics": claim.model_dump(mode="json"),
        "whole_decision_schema_error": failure,
        "accepted_whole_pipeline_neutral_limit": False if failure else None,
        "existing_owner": "scripts.m12ds_r2_schemas.decision_schema",
        "reason": "UNKNOWN_LIMIT/OBSERVE is claim-level. Every existing Holder branch requires an observed-business effect. No neutral Holder branch exists.",
        "investment_verdict_assigned": False, "new_policy_created": False}


def run(args):
    network = network_guard()
    reads = set()

    def audit(event, values):
        if event == "open" and isinstance(values[0], (str, bytes)):
            mode = values[1]
            if mode is None or "r" in mode:
                reads.add(str(values[0]))

    sys.addaudithook(audit)
    out = args.output
    out.mkdir(parents=True, exist_ok=False)
    def save(name, value):
        prior.save(out, name, value)
    save("state-before.json", snapshot(prior.REPO, args.operating))
    if prior.git("status", "--porcelain"):
        raise ValueError("clean_exact_commit_required")
    manifest = prior.read_verified_archive(args.source_zip, prior.SOURCE_ZIP_SHA)
    source = {}
    identity = []
    for name, wanted in SOURCE_HASHES.items():
        raw = (args.source / name).read_bytes()
        source[name] = json.loads(raw)
        if prior.digest(source[name]) != wanted:
            raise ValueError("sealed_source_semantic_hash_mismatch:" + name)
        if manifest["whole-1/" + name]["sha256"] != prior.sha(raw):
            raise ValueError("sealed_source_bytes_mismatch:" + name)
        identity.append({"file": name, "sha256": prior.sha(raw), "semantic_sha256": wanted})
    for path, expected in ((args.blind_zip, BLIND_SHA), (args.blocker_zip, BLOCKER_SHA),
                            (args.receipt, RECEIPT_SHA)):
        if prior.sha(path.read_bytes()) != expected:
            raise ValueError("sealed_artifact_identity_mismatch:" + path.name)
    receipt = json.loads(args.receipt.read_bytes())
    prior.durable_bytes(out / args.receipt.name, args.receipt.read_bytes(), exclusive=True)
    save("source-verification.json", {"status": "PASS", "source_files": identity,
        "source_zip_sha256": prior.SOURCE_ZIP_SHA, "manifest_entries_verified": len(manifest),
        "blind_zip_sha256": BLIND_SHA, "first_blocker_zip_sha256": BLOCKER_SHA,
        "neutral_receipt_sha256": RECEIPT_SHA, "external_review": "INDEPENDENT_FREEZE_RECEIVED",
        "external_freeze_is_receipt_assertion_not_content_inspection": True, "neutral_receipt": receipt})
    original = source["combined-full-source-packet.json"]
    derived = deepcopy(original)
    matrix, changes = [], []
    for market, tickers in prior.UNIVERSE.items():
        if set(original["packets"][market]["stocks"]) != set(tickers):
            raise ValueError("whole_cohort_identity_mismatch")
        for ticker in tickers:
            stock, rows, changed = reproject_time(original["packets"][market]["stocks"][ticker])
            derived["packets"][market]["stocks"][ticker] = stock
            matrix.extend(rows)
            changes.extend(changed)
    core_changes = [r for r in changes if r["core_owned"]]
    assert len(core_changes) == 51 and all(r["status"] == "PASS" for r in core_changes)
    assert all(r["non_time_fields_unchanged"] for r in matrix)
    assert original["authority_graph"] == derived["authority_graph"]
    assert prior.digest(original) == SOURCE_HASHES["combined-full-source-packet.json"]
    assert prior.sha(args.blind_zip.read_bytes()) == BLIND_SHA
    rows = []
    for market, tickers in prior.UNIVERSE.items():
        for ticker in tickers:
            try:
                row = prior.stock_preflight(derived["packets"][market]["stocks"][ticker],
                                            derived["authority_graph"]["stocks"][ticker])
            except ValueError as exc:
                row = {"ticker": ticker, "market": market, "status": "BLOCKED", "error": str(exc)}
            rows.append(row)
    audit_receipt = neutral_limit_contract_audit()
    assert audit_receipt["whole_decision_schema_error"] == "M12DS_R2_HOLDER_AXIS_CONTRACT_DEPENDENCY"
    ready = sum(r["status"] == "PASS" for r in rows)
    terminal = ("R2B_R1_ZERO_DIRECTIONAL_ENTITLEMENT_POLICY_DECISION_REQUIRED" if ready == 21
                and [r["ticker"] for r in rows if r["status"] != "PASS"] == ["SNDK"]
                else "R2B_R1_WHOLE_COHORT_SOURCE_PREFLIGHT_GAP")
    sndk = original["packets"]["us"]["stocks"]["SNDK"]
    authorities = original["authority_graph"]["stocks"]["SNDK"]["authority"]["authority_records"]
    event = [r for r in authorities if r["ref_id"].startswith("canonical:event:")]
    assert len(event) == 1 and event[0]["allowed_uses"] == ["CONTEXT"]
    assert not any("OVERALL_DIRECTION" in r["allowed_uses"] for r in authorities)
    save("canonical-projected-time-matrix.json", {"rows": matrix, "counts": dict(Counter(r["status"] for r in matrix))})
    save("affected-51-before-after.json", {"status": "PASS", "count": len(core_changes),
        "families": dict(Counter(r["ref_id"] for r in core_changes)), "rows": core_changes})
    save("whole-cohort-preflight.json", {"status": "BLOCKED", "ready_count": ready, "active_count": len(rows),
        "allow_model_dispatch": False, "rows": rows, "gate_owner": "scripts.r2b_sealed_blind_preflight.stock_preflight",
        "source_facts_preserved": True, "authority_widened": False,
        "current_input_dispatch_binding_reissued": False,
        "binding_note": "This is the exact Core source-use preflight on a date-only derived view. Original authority remains sealed. No model-ready binding or dispatch is claimed while neutral policy is absent."})
    save("neutral-limit-policy-audit.json", audit_receipt)
    save("sndk-entitlement-audit.json", {"typed_source_use_state": "ZERO_DIRECTIONAL_ENTITLEMENT_POLICY_DECISION_REQUIRED",
        "not_an_investment_verdict": True, "source_assembly": sndk["status"],
        "financial_state": sndk["financial_state"], "directional_ref_count": 0,
        "event_authority": event, "context_permission_unchanged": True,
        "persisted_event_receipt": sndk["persisted_event_receipt"], "authority_widened": False,
        "raw_source_sha256": prior.digest(sndk["packet"]), "authority_sha256": prior.digest(authorities)})
    save("date-only-projection.json", {"source_combined_sha256": prior.digest(original),
        "source_authority_graph_sha256": prior.digest(original["authority_graph"]),
        "stocks": {ticker: {"evidence_packet": stock["evidence_packet"], "ownership": stock["ownership"],
                           "original_packet_sha256": prior.digest(stock["packet"])}
            for packet in derived["packets"].values() for ticker, stock in packet["stocks"].items()}})
    save("execution-state.json", {"terminal": terminal, "generation_id": None, "dispatch_started": False,
        "prior_generation_id": "20260927-r2b-blind-20260927T131042Z",
        "market_calls": 0, "core_calls": 0, "a_calls": 0, "b_calls": 0,
        "provider_refresh": 0, "previews": 0, "expected_previews": 24,
        "monitoring_ai_result_bundle": None, "reveal_gate": "CLOSED",
        "independent_assessment_content_read": False, "network": network,
        "telegram": 0, "production_db_mutations": 0, "scheduler_mutations": 0,
        "main_merge": 0, "push": 0, "deploy": 0, "restart": 0})
    save("model-call-plan.json", {"conditional_only": True, "gated_off": True,
        "model": "gpt-5.6-sol", "effort": "xhigh", "market": 2, "core": 8, "a": 8, "b": 8,
        "max_seconds": 1200, "transport_retries": 0, "semantic_retries": 0, "fallback": 0, "judge": 0})
    save("repository-identities.json", {"base": BASE, "head": prior.git("rev-parse", "HEAD"),
        "branch": prior.git("branch", "--show-current"),
        "instruction_commit": prior.git("log", "-1", "--format=%H", "--", str(args.receipt.relative_to(prior.REPO))),
        "changed_files": prior.git("diff", "--name-only", BASE, "HEAD").splitlines(),
        "code_hashes": {p: prior.sha((prior.REPO / p).read_bytes()) for p in
                        prior.git("diff", "--name-only", BASE, "HEAD").splitlines()}})
    save("anti-contamination-receipt.json", {"independent_assessment_content_read": False,
        "external_review_file_discovery": False, "receipt_only": True,
        "prompts_generated": 0, "candidates_generated": 0, "model_calls": 0,
        "input_source_directory": str(args.source), "observed_read_paths_after_hook": sorted(reads),
        "evidence_scope": "Explicit source/receipt input allowlist and Python open audit; not a claim of OS-wide file isolation."})
    print(json.dumps({"terminal": terminal, "date_repairs": len(core_changes), "preflight_ready": ready,
        "subjects": len(rows), "model_calls": 0, "network": network,
        "other_blockers": [r for r in rows if r["status"] != "PASS"]}), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("output", "source", "source-zip", "blind-zip", "blocker-zip", "receipt", "operating"):
        parser.add_argument("--" + name, type=Path, required=True)
    run(parser.parse_args())
