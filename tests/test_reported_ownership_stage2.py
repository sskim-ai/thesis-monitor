"""SYNTHETIC_MODEL_OWNED_TRANSPORT_PROOF; no model judgment is produced."""

import pytest

from app.services.accepted_decision_v2_runtime_service import validate_accepted_v2_stage2_candidate
from app.services.native_accepted_ownership import BackendOwnershipRegistry
from app.services.native_economic_core import BackendInvocation, InvocationSpec
from tests.native_economic_fixtures import synthetic_economic
from tests.test_native_accepted_ownership import downstream
from tests.test_reported_fact_owner import owner_fixture
from app.services.cross_market_decision_engine_service import DecisionEvidencePacket


def transport_fixture():
    registry, policy, original, bound = synthetic_economic()
    scope = original.request.invocation
    spec = InvocationSpec.model_validate({k: getattr(scope, k) for k in InvocationSpec.model_fields})
    spec = spec.model_copy(update={"execution_purpose": "ACCEPTED_CORE_MODEL_REPROOF"})
    invocation = BackendInvocation(original.request.reference_request, registry=registry,
                                   spec=spec, economic_policy=policy)
    ledger = BackendOwnershipRegistry(offline_reproof=False)
    handle = ledger.begin(invocation, model="SYNTHETIC_TRANSPORT_NOT_MODEL_CALL", effort="TEST_ONLY")
    receipt = ledger.complete(handle, bound.model_candidate.model_dump_json().encode())
    core = bound.model_candidate.candidate
    packet = DecisionEvidencePacket(packet_id="synthetic-stage2-transport", ticker=core.ticker,
        company_name="SYNTHETIC", market="us", assessment_date="2026-10-09", horizon="fixture",
        evidence=(), prohibited_claims=(), evidence_sha256="a" * 64)
    ledger.bind_downstream_packet(receipt, invocation=invocation, candidate=core, packet=packet)
    return ledger, receipt, invocation, core, packet, policy


@pytest.mark.parametrize("probe,expected", [
    ("bare", "BACKEND_ISSUED_OWNERSHIP_REQUIRED"),
    ("forged_id", "UNISSUED_ACCEPTED_OUTPUT"),
    ("other_registry", "UNISSUED_ACCEPTED_OUTPUT"),
    ("revoked", "STALE_OR_SUPERSEDED_ACCEPTED_OUTPUT"),
    ("superseded", "STALE_OR_SUPERSEDED_ACCEPTED_OUTPUT"),
    ("candidate", "ISSUED_CANDIDATE_BINDING_MISMATCH"),
    ("packet", "DOWNSTREAM_PACKET_IDENTITY_GENERATION_MISMATCH"),
    ("policy", "ISSUED_OWNERSHIP_BINDING_MISMATCH"),
    ("issuer", "ISSUED_OWNERSHIP_BINDING_MISMATCH"),
    ("generation", "ISSUED_OWNERSHIP_BINDING_MISMATCH"),
])
def test_actual_stage2_ownership_gate_adversarial(probe, expected):
    ledger, receipt, invocation, core, packet, policy = transport_fixture()
    if probe == "bare":
        receipt = core
    elif probe == "forged_id":
        receipt = receipt.model_copy(update={"accepted_output_id": "a" * 64})
    elif probe == "other_registry":
        ledger = BackendOwnershipRegistry(offline_reproof=False)
    elif probe == "revoked":
        ledger.revoke(receipt)
    elif probe == "superseded":
        ledger.begin(invocation, model="SYNTHETIC_RETRY", effort="TEST_ONLY")
    elif probe == "candidate":
        core = core.model_copy(update={"confidence": "LOW"})
    elif probe == "packet":
        packet = packet.model_copy(update={"evidence_sha256": "b" * 64})
    else:
        field = {"policy": "policy_sha", "issuer": "security_id", "generation": "generation_id"}[probe]
        receipt = receipt.model_copy(update={field: "a" * 64})
    result = validate_accepted_v2_stage2_candidate(packet, downstream(core), core, policy.bundle.ownership,
        authority_native_v2=True, accepted_ownership=receipt, ownership_registry=ledger,
        backend_invocation=invocation)
    assert not result.valid
    assert result.errors == (expected,)


def test_positive_transport_lookup_is_not_real_model_or_complete_stage2_semantics():
    ledger, receipt, invocation, core, packet, _ = transport_fixture()
    proof = ledger.verify_downstream_packet(receipt, invocation=invocation, candidate=core, packet=packet)
    assert proof["generation_id"] == invocation.request.invocation.generation_id
    assert proof["accepted_output_id"] == receipt.accepted_output_id
    ledger.revoke(receipt)
    with pytest.raises(ValueError, match="STALE_OR_SUPERSEDED"):
        ledger.resolve(receipt, invocation=invocation, candidate=core)


def test_fact_comparison_cannot_issue_core_ownership_without_grant():
    owner, _ = owner_fixture()
    admitted = [owner.admit(f) for f in owner.facts if f.field == "revenue"]
    result = owner.compare(*admitted)
    _, _, invocation, _ = synthetic_economic()
    # Use the exact native invocation IDs, not a substituted source generation.
    # A different real source must fail even before its missing directional grant.
    ledger = BackendOwnershipRegistry()
    with pytest.raises(ValueError, match="FACT_REQUEST_IDENTITY_MISMATCH"):
        ledger.begin_with_reported_interpretation(invocation, model="TEST", effort="TEST",
            fact_owner=owner, interpretation=result, use_axis="CORE_DIRECTION")
    assert ledger.attempt_states() == ()
    f = admitted[0].fact
    with pytest.raises(ValueError, match="FACT_USE_GRANT_MISSING"):
        owner.authorize_interpretation(result, axis="CORE_DIRECTION", security_id=f.security_id,
            execution_generation_id=f.execution_generation_id, source_generation_id=f.source_generation_id)


def test_registry_lifetime_is_not_public_receipt_transport():
    ledger, receipt, invocation, core, packet, _ = transport_fixture()
    replacement = BackendOwnershipRegistry(offline_reproof=False)
    with pytest.raises(ValueError, match="UNISSUED_ACCEPTED_OUTPUT"):
        replacement.verify_downstream_packet(receipt, invocation=invocation, candidate=core, packet=packet)
