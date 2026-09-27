"""Whole sealed cohort readiness. Offline probes are never model candidates."""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import zipfile

from app.services.direction_timing_ownership_service import OwnedEvidencePacket
from scripts import r2b_r2_contract as c
from scripts import r2b_r1_offline_closure as r1
from scripts import r2b_sealed_blind_preflight as io
from scripts import m12dc_fresh_source_use_two_pass_reproof as owner
from scripts.m12co_entry_range_contract import build_subject_candidate_coverage
from scripts.m12cr_r1_typed_quality_contract import project_business_evidence_quality, project_security_valuation_basis
from scripts.m12dj_source_authority_preflight import preflight_current_pass_a_subject
from scripts.m12ds_r2_ranges import eligible_range_inputs, valuation_policy
from scripts.m12cq_two_pass_contract import build_pass_b_subject_context, validate_pass_b_transformation
from scripts.sealed_cohort_offline_proof import network_guard


class SourceReadAudit:
    """Exact source-file allowlist; external assessment content stays sealed."""

    def __init__(self, allowed, protected_roots):
        self.allowed = {Path(p).resolve() for p in allowed}
        self.roots = tuple(Path(p).resolve() for p in protected_roots)
        self.reads = Counter()
        self.denials = []

    def __call__(self, event, args):
        if event != "open" or not isinstance(args[0], (str, bytes, Path)):
            return
        path = Path(args[0].decode() if isinstance(args[0], bytes) else args[0]).resolve()
        if "INDEPENDENT_BLIND_ASSESSMENT" in path.name.upper():
            self.denials.append("external_assessment_content_forbidden")
            raise PermissionError("external_assessment_content_forbidden")
        mode = args[1]
        reading = mode is None or "r" in mode or "+" in mode
        if reading and any(path.is_relative_to(root) for root in self.roots):
            if path not in self.allowed:
                self.denials.append("source_read_outside_allowlist")
                raise PermissionError("source_read_outside_allowlist")
            self.reads[str(path)] += 1

    def receipt(self):
        return dict(allowlist=sorted(map(str, self.allowed)), reads=dict(self.reads), denials=self.denials,
                    independent_assessment_content_read=False, scope="preflight_python_open_events")


def require_whole_ready(receipt):
    expected = {ticker for tickers in io.UNIVERSE.values() for ticker in tickers}
    rows = receipt.get("rows", [])
    c._require(receipt.get("status") == "PASS" and receipt.get("ready") == 22
               and len(rows) == 22 and {r["ticker"] for r in rows} == expected,
               "whole_cohort_model_input_gap")
    for row in rows:
        c._require(all(row.get(stage) == "PASS" for stage in ("Core", "A", "B", "NewBuyer", "Holder")),
                   "whole_cohort_stage_gap")
        if row["decision_mode"] == "EVIDENCE_BASED":
            c._require(row.get("a_materialization", {}).get("status") == "PASS", "materialization_proof_missing")
    return {"status": "READY_FOR_REQUEST_FREEZE", "actual_model_dispatch_authorized": False}


def schema_check(schema):
    wire, projection = owner.project_provider_wire_schema(schema)
    check = owner.scan_provider_structured_output_schema(wire)
    c._require(check["status"] == "PASS", "provider_schema_dialect")
    return {"internal_sha256": io.digest(schema), "wire_sha256": io.digest(wire),
            "dialect": check, "projection": projection}


def synthetic_shape_probe(schema):
    """Exercise deterministic plumbing only, never an investment/model result."""
    if "const" in schema:
        return schema["const"]
    if "enum" in schema:
        values = schema["enum"]
        return "UNRESOLVED" if "UNRESOLVED" in values else values[0]
    if "anyOf" in schema:
        return synthetic_shape_probe(schema["anyOf"][0])
    kind = schema.get("type")
    if kind == "object":
        return {key: synthetic_shape_probe(value) for key, value in schema["properties"].items()}
    if kind == "array":
        return [synthetic_shape_probe(schema["items"])] * schema.get("minItems", 0)
    if kind == "string":
        return "Offline materialization probe, not an investment conclusion."
    if kind in {"integer", "number"}:
        return schema.get("minimum", 0)
    if kind == "boolean":
        return False
    if kind == "null":
        return None
    raise ValueError("unsupported_offline_probe_schema")


def materialization_probe(ticker, schema, context):
    output = synthetic_shape_probe(schema)
    rows, receipt = owner.materialize_future_pass_a(
        output, subjects=(ticker,), subject_contexts={ticker: context})
    return rows, {**receipt, "synthetic_only": True, "actual_model_output": False}


def subject_inputs(view, authority, receipt, *, generation, atomic=()):
    source_generation = authority["authority"]["source_generation_id"]
    cat, metadata, chain = c.bound_chain(view, authority, atomic=list(atomic), generation=generation,
                                       source_generation=source_generation, view_receipt=receipt)
    owned = OwnedEvidencePacket.model_validate(view["ownership"])
    ownership = {"ticker": view["ticker"], "core_ref_ids": sorted(owned.core_refs),
                 "timing_ref_ids": sorted(owned.timing_refs)}
    sub = build_subject_candidate_coverage(market=view["market"], packet=view["evidence_packet"], ownership=ownership)
    sub.update(decision_evidence=metadata,
        business_evidence_quality_state=project_business_evidence_quality(view["evidence_packet"]),
        security_valuation_basis_state=project_security_valuation_basis(view["evidence_packet"]),
        directional_disclosure_quality_refs=sorted(set(cat["material_disclosure_failure_refs"] + cat["positive_quality_refs"])))
    return cat, sub, chain


def a_input(view, cat, sub, chain, authority):
    return preflight_current_pass_a_subject(ticker=view["ticker"], source_generation_id=chain["source_generation_id"],
        execution_generation_id=chain["execution_generation_id"], catalog=cat, source_packet=sub,
        authority=chain["authority"], projection=chain["projection"], binding=chain["binding"], expectation=chain["expectation"],
        prohibited_pass_a_source_refs=authority["pass_a_visibility_exclusions"])


def b_input(view, cat, sub, chain, classification, capability):
    range_subject, entries, exclusions = eligible_range_inputs(sub, cat["entry_catalog"], chain)
    valuation = valuation_policy(range_subject, classification, sub["security_valuation_basis_state"])
    valuation["source_use_exclusions"] = exclusions
    common = dict(catalog=cat, source_use_view=chain["projection"], source_use_binding=chain["binding"],
        source_use_expectation=chain["expectation"], source_generation_id=chain["source_generation_id"],
        execution_generation_id=chain["execution_generation_id"], require_source_use=True)
    ctx = build_pass_b_subject_context(context=owner.m12db._source_context(view["ticker"], sub),
        ticker=view["ticker"], pass_a=classification, policy_option=valuation["option"], **common)
    common.pop("require_source_use")
    transform = validate_pass_b_transformation(context=ctx, raw_source_metadata=sub["decision_evidence"], **common)
    c._require(transform["status"] == "PASS", "pass_b_transformation_failed")
    ctx.update(r2_policy_capability=capability, r2_valuation=valuation, r2_eligible_range_catalog=entries)
    return ctx, entries, valuation


def preflight_subject(stock, authority, local, *, generation, cutoff, defer_b=False):
    view, receipt = c.source_view(stock, authority, local, cutoff=cutoff)
    cat, sub, chain = subject_inputs(view, authority, receipt, generation=generation)
    owned = OwnedEvidencePacket.model_validate(view["ownership"])
    metadata = [r for r in sub["decision_evidence"] if r["ref_id"] in owned.core_refs]
    fields = c.policy.frozen_fact_fields(stock["packet"], stock["ticker"], metadata)
    obs = c.policy.observations(metadata, chain["authority"], fields)
    mode = c.decision_mode(stock, chain["authority"], obs)
    core_input = dict(ticker=stock["ticker"], metadata=metadata, authority=chain["authority"],
                      frozen_fact_fields=fields, observed_propositions=obs, decision_mode=mode)
    recovery = c.limitation_catalog(stock, chain["authority"]) if mode == "UNKNOWN_LIMIT" else {}
    row = {"ticker": stock["ticker"], "market": stock["market"], "decision_mode": mode,
        "source_assembly": stock["status"], "source_packet_sha256": io.digest(stock["packet"]),
        "source_view_receipt": receipt, "visible_refs": sorted(r["ref_id"] for r in sub["decision_evidence"]),
        "source_authority_unchanged": True, "source_generation_id": chain["source_generation_id"],
        "denied_refs": receipt["denied_refs"], "canonical_source_time_unclassified": 0,
        "source_view_binding_sha256": io.digest(chain["binding"])}
    prepared = dict(view=view, view_receipt=receipt, source_authority=authority, core_input=core_input,
                    mode=mode, recovery=recovery, initial_chain=chain, catalog=cat, subject=sub)
    if mode == "UNKNOWN_LIMIT":
        cap = {k: [] for k in c.DIRECTION_BUCKETS}
        schema = c.unknown_schema(recovery)
        probe = dict(decision_mode=mode, overall_direction="OBSERVE", new_buyer="OBSERVE", holder="OBSERVE",
            directional_buy_score=None, directional_sell_score=None, confidence=None,
            limitation_reason="ZERO_AUTHORIZED_DIRECTIONAL_EVIDENCE", unknowns=list(recovery),
            required_next_evidence=list(recovery))
        c.validate_unknown(probe, mode=mode, recovery=recovery, capability=cap)
        row.update(Core="PASS", A="PASS", B="PASS", NewBuyer="PASS", Holder="PASS",
                   schema=schema_check(schema), negative_direction_capability=0,
                   prospective_source_recovery=recovery)
    else:
        core_schema = c.schemas.core_schema({stock["ticker"]: core_input})
        # Mechanical availability probes, not generated candidates or expected decisions.
        probe = {"claims": [{"effect": o["effect"], "text": "Offline source capability probe.",
            "evidence_refs": [o["source_ref"]], "observation_ids": [key], "materiality": "CONTEXT_ONLY"}
            for key, o in obs.items()]}
        core = c.policy.materialize_core(stock["ticker"], probe, metadata, chain["authority"], fields)
        cat, sub, chain = subject_inputs(view, authority, receipt, generation=generation, atomic=core["atomic_claims"])
        cap = c.policy.axis_capability(core, chain, cat, sub["decision_evidence"])
        gate = a_input(view, cat, sub, chain, authority)
        row.update(Core="PASS", A=gate["receipt"]["status"], a_preflight=gate["receipt"],
                   core_schema=schema_check(core_schema))
        c._require(gate["receipt"]["status"] == "PASS", "A_preflight:" + json.dumps(gate["receipt"]["denial_reason_counts"]))
        ctx = gate["model_context"]
        schema = owner.future_pass_a_batch_schema(subjects=[stock["ticker"]], subject_contexts={stock["ticker"]: ctx},
            source_use_inputs={stock["ticker"]: dict(catalog=cat, chain=chain,
                source_metadata=sub["decision_evidence"], source_generation_id=chain["source_generation_id"], execution_generation_id=generation)})
        row["a_schema"] = schema_check(schema)
        row["a_visible_refs"] = sorted(r["ref_id"] for r in ctx.get("eligible_non_price_evidence", []))
        rows, materialization = materialization_probe(stock["ticker"], schema, ctx)
        row["a_materialization"] = materialization
        row["business_quality_projection"] = sub["business_evidence_quality_state"]
        if materialization["status"] != "PASS":
            row.update(status="BLOCKED", A="BLOCKED", B="DEPENDENCY_BLOCKED", NewBuyer="BLOCKED",
                       Holder="BLOCKED", blocker="A_DETERMINISTIC_QUALITY_MATERIALIZATION_GAP",
                       exact_errors=materialization.get("legacy_semantic", {}).get("errors", []),
                       missing_ref_family="canonical:financial_quality:<source-period>",
                       offline_availability_probes_only=True)
            return row, prepared
        classification = rows[0]
        if defer_b:
            prepared["b_probe_inputs"] = dict(cat=cat, sub=sub, chain=chain,
                classification=classification, capability=cap)
            row.update(status="A_READY", A="PASS", NewBuyer="PASS", B="DEFERRED", Holder="DEFERRED",
                       blocker=None, offline_availability_probes_only=True)
            return row, prepared
        bctx, entries, valuation = b_input(view, cat, sub, chain, classification, cap)
        row.update(B="PASS", NewBuyer="PASS", Holder="PASS", b_schema=schema_check(
            c.decision_schema(mode, cap, valuation, entries, {})), b_context_sha256=io.digest(bctx))
    row.update(status="PASS", blocker=None, offline_availability_probes_only=True)
    return row, prepared


def run(args):
    network = network_guard()
    out = args.output
    out.mkdir(parents=True, exist_ok=False)
    audit = SourceReadAudit([args.source / name for name in r1.SOURCE_HASHES] + [
        args.source_zip, args.blind_zip, args.receipt],
        [args.source.parent, args.source_zip.parent, args.receipt.parent])
    sys.addaudithook(audit)
    manifest = io.read_verified_archive(args.source_zip, io.SOURCE_ZIP_SHA)
    source = {}
    for name, wanted in r1.SOURCE_HASHES.items():
        raw = (args.source / name).read_bytes()
        source[name] = json.loads(raw)
        c._require(io.digest(source[name]) == wanted and io.sha(raw) == manifest["whole-1/" + name]["sha256"],
                   "sealed_source_mismatch:" + name)
    for path, expected in ((args.blind_zip, r1.BLIND_SHA), (args.receipt, r1.RECEIPT_SHA)):
        c._require(io.sha(path.read_bytes()) == expected, "blind_or_receipt_identity")
    combined = source["combined-full-source-packet.json"]
    generation = "20260928-r2b-r2-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    rows, prepared = [], {}
    with zipfile.ZipFile(args.source_zip) as archive:
        for market, tickers in io.UNIVERSE.items():
            local = json.loads(archive.read(f"input/sealed-live/class-c/local-{market}.json"))
            c._require(set(combined["packets"][market]["stocks"]) == set(tickers), "exact_universe")
            for ticker in tickers:
                try:
                    row, inputs = preflight_subject(combined["packets"][market]["stocks"][ticker],
                        combined["authority_graph"]["stocks"][ticker], local,
                        generation=generation, cutoff=combined["seed"]["started_at"])
                    prepared[ticker] = inputs
                except (ValueError, KeyError, TypeError) as exc:
                    row = {"ticker": ticker, "market": market, "status": "BLOCKED", "blocker": str(exc)}
                rows.append(row)
                print(json.dumps({k: row.get(k) for k in ("ticker", "status", "decision_mode", "blocker")}), flush=True)
    ready = sum(r["status"] == "PASS" for r in rows)
    summary = dict(generation_id=generation, status="PASS" if ready == 22 else "BLOCKED", ready=ready,
        active_count=len(rows), modes=dict(Counter(r.get("decision_mode") for r in rows)),
        model_calls=0, provider_calls=0, network=network, independent_assessment_read=False,
        blind_sha256=r1.BLIND_SHA, receipt_sha256=r1.RECEIPT_SHA, source_hashes=r1.SOURCE_HASHES,
        implementation=io.git("rev-parse", "HEAD"), worktree_clean=not bool(io.git("status", "--porcelain")),
        probes_not_model_outputs=True, all_request_binding_sealed=False, allow_model_dispatch=False)
    summary.update(terminal="READY_FOR_REQUEST_FREEZE" if ready == 22 else "R2B_R2_WHOLE_COHORT_MODEL_INPUT_GAP",
                   stage_ready={stage: sum(r.get(stage) == "PASS" for r in rows)
                                for stage in ("Core", "A", "B", "NewBuyer", "Holder")})
    io.save(out, "preflight.json", {**summary, "rows": rows})
    io.save(out, "prepared-inputs.json", prepared)
    io.save(out, "summary.json", summary)
    io.save(out, "source-read-audit.json", audit.receipt())
    print(json.dumps(summary), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("output", "source", "source-zip", "blind-zip", "receipt"):
        parser.add_argument("--" + name, type=Path, required=True)
    run(parser.parse_args())
