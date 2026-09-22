from copy import deepcopy

import pytest

from app.services.accepted_decision_v2_runtime_service import build_accepted_v2_production_context
from app.services.cross_market_decision_engine_service import DecisionEvidencePacket, DecisionEvidenceRef
from scripts.m12dr_fresh_blind_reproof import authority_core_schema, BatchFailure
from scripts.m12dc_fresh_source_use_two_pass_reproof import (
    project_provider_wire_schema, scan_provider_structured_output_schema,
)


def fixture():
    packets = []
    authority = {}
    for ticker in ("RENAMED_A", "RENAMED_B"):
        refs = [f"decision-evidence:{ticker}-{kind}" for kind in ("observed", "context")]
        packets.append(DecisionEvidencePacket(
            packet_id="fixture", ticker=ticker, company_name=ticker, market="us",
            assessment_date="2026-09-21", horizon="long term", evidence_sha256=ticker,
            evidence=tuple(DecisionEvidenceRef(ref_id=ref, category="thesis", label="evidence",
                                              statement="Observed business evidence", as_of="2026-06-30", source_ref="fixture")
                           for ref in refs), prohibited_claims=()))
        authority[ticker] = {"authority": {"authority_records": [
            {"ref_id": ref, "authority_state": "RESOLVED", "allowed_uses": ["CONTEXT", "OVERALL_DIRECTION"]
             if ref.endswith("observed") else ["CONTEXT"]} for ref in refs]}}
    context = build_accepted_v2_production_context(
        packet={"packet_id": "fixture", "market": "us", "assessment_date": "2026-09-21",
                "stocks": [{"ticker": p.ticker} for p in packets]}, claim_id="fresh", evidence_packets=tuple(packets))
    return context, authority


def test_core_schema_enforces_same_subject_directional_source_before_inference():
    context, authority = fixture()
    before = deepcopy(authority)
    schema, receipts = authority_core_schema(context, context.selected_subjects, authority)
    for index, ticker in enumerate(context.selected_subjects):
        driver = schema["$defs"][f"M12DRDriver{index}"]
        assert driver["properties"]["evidence_refs"]["items"]["enum"] == [f"decision-evidence:{ticker}-observed"]
        assert schema["$defs"][f"M12DRCore{index}"]["properties"]["ticker"]["const"] == ticker
        assert receipts[index]["directional_refs"] == [f"decision-evidence:{ticker}-observed"]
    wire, _ = project_provider_wire_schema(schema)
    assert scan_provider_structured_output_schema(wire)["status"] == "PASS"
    assert authority == before


def test_missing_directional_source_stops_core_schema():
    context, authority = fixture()
    for record in authority["RENAMED_A"]["authority"]["authority_records"]:
        record["allowed_uses"] = ["CONTEXT"]
    with pytest.raises(BatchFailure, match="CORE_DIRECTIONAL_SOURCE_UNAVAILABLE"):
        authority_core_schema(context, context.selected_subjects, authority)
