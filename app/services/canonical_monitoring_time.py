"""Current evidence-time projection with unchanged canonical fact ownership."""
from copy import deepcopy
from types import SimpleNamespace
from app.services.direction_timing_ownership_service import OwnedEvidencePacket, verified_owned_packet_view
from app.services.canonical_evidence_time_service import validate_canonical_time
from app.services.cross_market_decision_engine_service import build_decision_evidence_packet
from app.services.unified_snapshot_contract import digest
from app.services.unified_run_artifacts import sha256_bytes
prior = SimpleNamespace(OwnedEvidencePacket=OwnedEvidencePacket, digest=digest, sha=sha256_bytes)

def reproject_time(stock):
    """Use the repaired producer but preserve every non-time field of the seal."""
    owned = verified_owned_packet_view(stock)
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
    core_refs = owned.core_refs
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
        if before["as_of"] != row["as_of"] or before["source_time"] != row["source_time"]:
            changes.append(receipt)
    if changes:
        raise ValueError("owned_evidence_time_derivative_authority_required")
    # A no-op keeps the original sanitized owned rows, not raw packet rows.
    verified_owned_packet_view(result)
    assert result["packet"] == stock["packet"]
    return result, matrix, changes
