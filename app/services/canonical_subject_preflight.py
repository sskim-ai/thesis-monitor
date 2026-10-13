"""Canonical deterministic subject readiness; no controller or dispatch."""
import json
from app.services.direction_timing_ownership_service import verified_owned_packet_view
from app.services import canonical_monitoring_owner as owner
from app.services import canonical_monitoring_io as io
from app.services.canonical_monitoring_input import subject_inputs, a_input, b_input
from scripts import r2b_r2_contract as c

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

def preflight_subject(stock, authority, local, *, generation, cutoff, defer_b=False, source_view_owner=None):
    verified_owned_packet_view(stock)
    view, receipt = (source_view_owner or c.source_view)(stock, authority, local, cutoff=cutoff)
    cat, sub, chain = subject_inputs(view, authority, receipt, generation=generation)
    owned = verified_owned_packet_view(view)
    core_refs = owned.core_refs
    metadata = [r for r in sub["decision_evidence"] if r["ref_id"] in core_refs]
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
