import pytest

from app.services.structured_autonomy_shadow_service import ClaimSemanticMetadata
from scripts import m12ds_r4_r4_policy as policy
from scripts import m12ds_r4_r4_schemas as schemas
from test_m12ds_r2_judgment_policy import bind, ranges


def test_unknown_limit_observe_is_claim_semantics_not_a_complete_decision():
    metadata = ClaimSemanticMetadata(claim_type="UNKNOWN_LIMIT", direction="OBSERVE")
    assert metadata.claim_type.value == "UNKNOWN_LIMIT"
    with pytest.raises(ValueError, match="unknown_limit_direction_invalid"):
        ClaimSemanticMetadata(claim_type="UNKNOWN_LIMIT", direction="IMPROVE")


def test_context_only_core_cannot_supply_holder_or_directional_authority():
    rows = [{"ref_id": "event:fictional", "category": "earnings",
             "statement": "Unreviewed context only.", "as_of": "2026-06-30"}]
    authority = {"authority_records": [{"ref_id": rows[0]["ref_id"],
        "authority_state": "RESOLVED", "allowed_uses": ["CONTEXT"]}]}
    assert policy.observations(rows, authority) == {}
    schema = schemas.core_schema({"FICTIONAL": {"metadata": rows, "authority": authority}})
    assert schema
    core = policy.materialize_core("FICTIONAL", {"claims": [{
        "effect": "CONFIDENCE_ONLY", "text": "Source review is incomplete.",
        "evidence_refs": [rows[0]["ref_id"]], "observation_ids": [],
        "materiality": "CONTEXT_ONLY"}]}, rows, authority)
    chain, catalog = bind(core, rows, denied=True)
    cap = policy.axis_capability(core, chain, catalog, rows)
    assert cap["confidence"]
    assert not any(cap[k] for k in ("positive", "negative", "holder_support", "holder_risk", "holder_reduce"))
    with pytest.raises(ValueError, match="M12DS_R2_HOLDER_AXIS_CONTRACT_DEPENDENCY"):
        schemas.decision_schema(cap, ranges(), {})
    assert authority["authority_records"][0]["allowed_uses"] == ["CONTEXT"]
