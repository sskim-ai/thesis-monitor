"""Diagnostic ordering only; reviewed fixtures remain TEST_ONLY."""
from copy import deepcopy
import json
from pathlib import Path

import pytest

from app.services.accepted_decision_v2_runtime_service import (
    build_accepted_v2_production_context,
)
from app.services.cross_market_decision_engine_service import (
    DecisionEvidencePacket,
    DecisionEvidenceRef,
)
from app.services.reviewed_fixture_authority import build_reviewed_core_fixture
from scripts import m12dr_fresh_blind_reproof as reproof
from scripts.m12dc_fresh_source_use_two_pass_reproof import (
    project_provider_wire_schema,
    scan_provider_structured_output_schema,
)


def reviewed_inputs():
    recipes = Path(__file__).parents[1] / "app/fixtures/reviewed_packet_recipes.json"
    arguments = json.loads(recipes.read_bytes())["recipes"]["core:batch"]["arguments"]
    context = build_reviewed_core_fixture(
        packet=arguments["packet"], claim_id=arguments["claim_id"],
        evidence_packets=tuple(
            DecisionEvidencePacket.model_validate(row)
            for row in arguments["evidence_packets"]
        ),
    )
    authorities = {
        owned.ticker: {
            "authority": {
                "authority_records": [
                    {"ref_id": ref, "authority_state": "RESOLVED",
                     "allowed_uses": ["OVERALL_DIRECTION"]}
                    for ref in owned.core_ref_ids
                ],
            },
        }
        for owned in context.evidence_ownership
    }
    return context, authorities


def forbid_schema(*args, **kwargs):
    raise AssertionError("generic schema ran before the required rejection")


def test_empty_owned_refs_reject_caller_direction_before_schema(monkeypatch):
    packet = DecisionEvidencePacket(
        packet_id="unowned", ticker="UNSEEN", company_name="Unseen", market="us",
        assessment_date="2026-09-21", horizon="long term", evidence_sha256="fixture",
        evidence=(DecisionEvidenceRef(
            ref_id="unowned-ref", category="thesis", label="Unowned",
            statement="Caller assertion", source_ref="fixture",
        ),), prohibited_claims=(),
    )
    context = build_accepted_v2_production_context(
        packet={"packet_id": "unowned", "market": "us", "assessment_date": "2026-09-21",
                "stocks": [{"ticker": "UNSEEN"}]},
        claim_id="unowned", evidence_packets=(packet,),
    )
    authorities = {"UNSEEN": {"authority": {"authority_records": [{
        "ref_id": "unowned-ref", "authority_state": "RESOLVED",
        "allowed_uses": ["OVERALL_DIRECTION"],
    }]}}}
    monkeypatch.setattr(reproof.core_owner, "accepted_v2_fundamental_core_output_schema", forbid_schema)
    with pytest.raises(reproof.BatchFailure, match="CORE_DIRECTIONAL_SOURCE_UNAVAILABLE:UNSEEN"):
        reproof.authority_core_schema(context, context.selected_subjects, authorities)


def test_nonempty_owned_refs_with_context_only_grant_reject_before_schema(monkeypatch):
    context, authorities = reviewed_inputs()
    assert all(row.core_ref_ids for row in context.evidence_ownership)
    for row in authorities.values():
        for record in row["authority"]["authority_records"]:
            record["allowed_uses"] = ["CONTEXT"]
    before = deepcopy(authorities)
    monkeypatch.setattr(reproof.core_owner, "accepted_v2_fundamental_core_output_schema", forbid_schema)
    with pytest.raises(reproof.BatchFailure, match="CORE_DIRECTIONAL_SOURCE_UNAVAILABLE"):
        reproof.authority_core_schema(context, context.selected_subjects, authorities)
    assert authorities == before


def test_invalid_context_seal_precedes_directional_check(monkeypatch):
    context, authorities = reviewed_inputs()
    changed = context.model_copy(update={"claim_id": "caller-changed"})
    for row in authorities.values():
        row["authority"]["authority_records"] = []
    monkeypatch.setattr(reproof.core_owner, "accepted_v2_fundamental_core_output_schema", forbid_schema)
    with pytest.raises(ValueError, match="reviewed_fixture_unissued_revoked_or_changed"):
        reproof.authority_core_schema(changed, context.selected_subjects, authorities)


def test_invalid_subject_precedes_directional_check(monkeypatch):
    context, authorities = reviewed_inputs()
    monkeypatch.setattr(reproof.core_owner, "accepted_v2_fundamental_core_output_schema", forbid_schema)
    with pytest.raises(ValueError, match="v2_fundamental_core_identity_subject_mismatch"):
        reproof.authority_core_schema(context, ("NOT_IN_REQUEST",), authorities)


def test_other_subject_permission_does_not_supply_direction(monkeypatch):
    context, authorities = reviewed_inputs()
    first, second = context.selected_subjects[:2]
    authorities[first] = deepcopy(authorities[second])
    monkeypatch.setattr(reproof.core_owner, "accepted_v2_fundamental_core_output_schema", forbid_schema)
    with pytest.raises(reproof.BatchFailure, match="CORE_DIRECTIONAL_SOURCE_UNAVAILABLE:" + first):
        reproof.authority_core_schema(context, context.selected_subjects, authorities)


def test_reviewed_test_only_schema_preserves_subject_order_and_exact_refs():
    context, authorities = reviewed_inputs()
    for row in authorities.values():
        records = row["authority"]["authority_records"]
        records.append({
            "ref_id": "not-owned-by-this-request",
            "authority_state": "RESOLVED",
            "allowed_uses": ["OVERALL_DIRECTION"],
        })
    before = deepcopy(authorities)
    context_before = context.model_dump_json()
    selected = tuple(reversed(context.selected_subjects))
    schema, receipts = reproof.authority_core_schema(context, selected, authorities)
    ownership = {row.ticker: row for row in context.evidence_ownership}
    assert [row["ticker"] for row in receipts] == list(selected)
    for index, ticker in enumerate(selected):
        expected = sorted(ownership[ticker].core_ref_ids)
        directional = [authorities[ticker]["authority"]["authority_records"][0]["ref_id"]]
        assert receipts[index]["same_subject_core_refs"] == expected
        assert receipts[index]["directional_refs"] == directional
        driver = schema["$defs"][f"M12DRDriver{index}"]
        assert driver["properties"]["evidence_refs"]["items"]["enum"] == directional
        core = schema["$defs"][f"M12DRCore{index}"]["properties"]
        assert core["ticker"]["const"] == ticker
        assert schema["properties"]["cores"]["items"]["anyOf"][index] == {
            "$ref": f"#/$defs/M12DRCore{index}",
        }
        for role in ("buy_drivers", "sell_drivers"):
            assert core[role]["items"] == {"$ref": f"#/$defs/M12DRDriver{index}"}
        assert core["decisive_reason"] == {"$ref": f"#/$defs/M12DRDriver{index}"}
        assert schema["$defs"][f"M12DRClaim{index}"]["properties"]["evidence_refs"]["items"]["enum"] == expected
    wire, _ = project_provider_wire_schema(schema)
    assert schema["test_only_provenance"]["provenance"] == "TEST_ONLY"
    assert wire["test_only_provenance"] == schema["test_only_provenance"]
    scan = scan_provider_structured_output_schema(wire)
    assert scan["status"] == "FAIL"
    assert any(row["keyword"] == "test_only_provenance" for row in scan["unsupported_keywords"])
    assert authorities == before
    assert context.model_dump_json() == context_before
