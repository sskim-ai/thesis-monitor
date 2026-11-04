"""A legitimate synthetic owner positive is not a full economic pipeline positive."""
from app.services.cross_market_decision_engine_service import build_decision_evidence_packet
from app.services.direction_timing_ownership_service import build_owned_evidence_packet
from scripts.m12dr_financial_source_authority import build_source_authority
from test_financial_observation_quality import authority_inputs


def test_derived_directional_owner_positive_and_actual_native_admission_gap():
    inputs = authority_inputs()
    authority = build_source_authority(**inputs)
    records = authority["authority"]["authority_records"]
    assert records and all("OVERALL_DIRECTION" in r["allowed_uses"] for r in records)
    assert all(not {"VALUATION", "ENTRY", "HOLDER_STANCE"} & set(r["allowed_uses"]) for r in records)
    packet = inputs["source_packet"]
    stock = packet["stocks"][0]
    evidence = build_decision_evidence_packet(packet=packet, stock=stock)
    owned = build_owned_evidence_packet(evidence, stock=stock)
    # Do not rewrite the producer's compatibility classification or its catalog.
    assert not set(r["ref_id"] for r in records) & set(owned.core_refs)
