"""Archive-only typed-quality binding and upstream completeness gate."""
from copy import deepcopy
import json

from app.services import canonical_business_quality_owner as canonical
from app.services.cross_market_decision_engine_service import _canonical_sha, build_decision_evidence_packet
from app.services.direction_timing_ownership_service import build_owned_evidence_packet
from app.services.packet_owned_technical_context_service import PacketOwnedTechnicalContext
from app.services.unified_snapshot_contract import digest
from scripts.m12cr_r1_typed_quality_contract import project_business_evidence_quality
from scripts.m12da_source_use_contract import build_trusted_source_authority_manifest
from scripts import r2b_r2_contract as previous_contract


def refresh_view_identity(view):
    """Bind the detached view, preserving the sealed packet's parent identity."""
    view["parent_packet_sha256"] = view.get("parent_packet_sha256") or view.get("packet_sha256")
    view["packet_sha256"] = digest(view["packet"])
    view["diagnostic_packet_sha256"] = view["packet_sha256"]
    ep = view["evidence_packet"]
    ep["evidence_sha256"] = _canonical_sha({k: ep[k] for k in
        ("evidence", "technical_context_id", "technical_context_status")})
    view["ownership"]["source_packet"] = deepcopy(ep)


def quality_source_view(stock, authority, local, *, cutoff):
    view, receipt = previous_contract.source_view(stock, authority, local, cutoff=cutoff)
    refresh_view_identity(view)
    receipt["derived_evidence_sha256"] = digest(view["evidence_packet"])
    receipt["derived_packet_sha256"] = view["packet_sha256"]
    receipt.pop("receipt_sha256")
    receipt["receipt_sha256"] = digest(receipt)
    return view, receipt


def bind_supplement(stock, authority, supplement, *, owner_inputs):
    canonical.verify(supplement, stock=stock, **owner_inputs)
    view, bound = deepcopy(stock), deepcopy(authority)
    fact, receipt = supplement["fact"], supplement["receipt"]
    raw = view["packet"]["stocks"][0]
    raw["fact_catalog"].append(deepcopy(fact))
    ep = build_decision_evidence_packet(packet=view["packet"], stock=raw,
        technical_context=PacketOwnedTechnicalContext.model_validate(raw["technical_context"]))
    owned = build_owned_evidence_packet(ep, stock=raw)
    ref = receipt["canonical_ref"]
    evidence = [r.model_dump(mode="json") for r in ep.evidence if r.ref_id == ref]
    canonical.require(len(evidence) == 1, "canonical_quality_projection_lost")
    canonical.require(json.loads(evidence[0]["statement"]) == fact["fields"], "quality_projection_truncated")
    view["evidence_packet"]["evidence"].extend(evidence)
    view["ownership"]["evidence"].extend(r.model_dump(mode="json") for r in owned.evidence if r.ref.ref_id == ref)
    view["ownership"]["source_packet"] = deepcopy(view["evidence_packet"])
    manifest = build_trusted_source_authority_manifest(ticker=stock["ticker"],
        source_generation_id=authority["authority"]["source_generation_id"],
        catalog={"ticker": stock["ticker"], "all_evidence_refs": [ref]}, source_metadata=evidence)
    canonical.require(manifest["status"] == "PASS", "quality_authority_registration_failed")
    record = manifest["authority_records"][0]
    canonical.require(set(record["allowed_uses"]) == {"CONTEXT", "CONFIDENCE"}, "quality_authority_widening")
    record.update(derivation_owner=canonical.CONTRACT, derivation_receipt_sha256=receipt["receipt_sha256"],
        source_input_bindings=deepcopy(receipt["inputs"]), canonical_fact_sha256=digest(fact),
        issuer_id=fact["issuer_id"], canonical_security_id=fact["canonical_security_id"])
    bound["authority"]["authority_records"].append(record)
    bound["authority"]["parent_authority_sha256"] = digest(authority["authority"])
    bound["authority"].pop("authority_manifest_sha256")
    bound["authority"]["authority_manifest_sha256"] = digest(bound["authority"])
    view["source_graph"][fact["fact_id"]] = dict(ticker=stock["ticker"], fact_sha256=digest(fact),
        source=canonical.CONTRACT, derivation_receipt_sha256=receipt["receipt_sha256"])
    view["evidence_reference_graph"][ref] = dict(ticker=stock["ticker"],
        source_ref=evidence[0]["source_ref"], evidence_sha256=digest(evidence[0]),
        input_hashes=deepcopy(view["input_hashes"]),
        technical_context_id=view["evidence_packet"]["technical_context_id"],
        derivation_receipt_sha256=receipt["receipt_sha256"])
    refresh_view_identity(view)
    return view, bound


def require_quality_owner(stock, authority, *, decision_mode):
    """No ref-less quality effect ever reaches this task's A context builder."""
    raw = stock["packet"]["stocks"][0]["fact_catalog"]
    facts = [f for f in raw if f["fact_type"] == "financial_quality"]
    if decision_mode == "UNKNOWN_LIMIT":
        records = authority["authority"]["authority_records"]
        canonical.require(not any("OVERALL_DIRECTION" in r["allowed_uses"] or "HOLDER_STANCE" in r["allowed_uses"]
                                  for r in records), "unknown_limit_directional_entitlement")
        canonical.require(not any(f["fact_type"] == "earnings_comparison" for f in raw),
                          "unknown_limit_financial_claim_present")
        return dict(source_presence="PROVEN_NOT_APPLICABLE", effect=None, source_refs=[],
                    applicability_owner="r2b-whole-decision-limitation-v1", directional_use_allowed=False)
    canonical.require(len(facts) == 1, canonical.MISSING)
    fact = facts[0]
    ref = "canonical:" + fact["fact_id"]
    rows = [r for r in stock["evidence_packet"]["evidence"] if r["ref_id"] == ref]
    records = [r for r in authority["authority"]["authority_records"] if r["ref_id"] == ref]
    canonical.require(len(rows) == len(records) == 1, "quality_fact_authority_missing")
    record, row = records[0], rows[0]
    canonical.require(record["ticker"] == stock["ticker"] and fact.get("ticker", stock["ticker"]) == stock["ticker"],
                      "quality_subject_mismatch")
    canonical.require(set(record["allowed_uses"]) == {"CONTEXT", "CONFIDENCE"}
                      and record["source_family"] == "typed_quality", "quality_directional_or_security_authority")
    canonical.require(record["source_metadata_sha256"] == digest(row)
                      and json.loads(row["statement"]) == fact["fields"], "quality_metadata_binding_mismatch")
    canonical.require(fact["fields"]["source_period"] == fact["as_of_date"] == record["source_period"],
                      "quality_source_period_mismatch")
    projected = project_business_evidence_quality(stock["evidence_packet"])
    canonical.require(projected["source_presence"] == "PRESENT" and projected["status"] == "MAPPED"
                      and projected["directional_use_allowed"] is False, "quality_projection_unowned")
    canonical.require(projected["effect"] == "NONE" or (projected["source_refs"] == [ref] and projected["reason"]),
                      "quality_confidence_without_support")
    return projected


def blind_materiality(supplement, blind_stock):
    """Conservative source-input inclusion audit, not a review of any verdict."""
    def codes(value):
        found = set()
        if isinstance(value, dict):
            for key, item in value.items():
                if key in {"reason_codes", "quality_reason_codes", "hard_errors", "soft_outliers",
                           "hard_denial_reasons", "denial_reasons", "reason", "denial_reason"}:
                    if isinstance(item, str):
                        found.add(item)
                    elif isinstance(item, list):
                        found.update(s for s in item if isinstance(s, str))
                found.update(codes(item))
        elif isinstance(value, list):
            for item in value:
                found.update(codes(item))
        elif isinstance(value, str) and value.startswith(("{", "[")):
            try:
                found.update(codes(json.loads(value)))
            except json.JSONDecodeError:
                pass
        return found
    known = codes(blind_stock)
    # New anomaly/conflict metadata can alter confidence. Its source-owned
    # reason must already have been in the source-only review, not just a hash.
    reasons = supplement["fact"]["fields"]["reason_codes"]
    missing = [r for r in reasons if r not in known]
    # The generic financial_hard_error is an existing category, but cannot on
    # its own substitute for the concrete underlying diagnosis.
    substantive = [r for r in missing if r != "financial_hard_error"]
    facts = {f["fact_id"]: digest(f) for s in blind_stock["source_packet"]["stocks"] for f in s["fact_catalog"]}
    missing_facts = [fid for fid, sha in supplement["receipt"]["input_fact_sha256"].items() if facts.get(fid) != sha]
    return dict(ticker=supplement["fact"]["ticker"], missing_quality_reasons=substantive,
        missing_or_changed_input_facts=missing_facts,
        reason_codes=reasons, status="MATERIAL_SOURCE_VIEW_CHANGED" if substantive or missing_facts else "ANNOTATION_ONLY",
        independent_assessment_content_read=False, source_only_stock_sha256=digest(blind_stock),
        supplement_sha256=digest(supplement),
        rule="No new source-owned anomaly/conflict diagnosis may enter a frozen blind comparison.")
