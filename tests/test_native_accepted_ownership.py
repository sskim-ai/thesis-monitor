"""Offline backend issuance proof; no fixture is an accepted model judgment."""

from copy import deepcopy
import inspect
import json
from types import SimpleNamespace

import pytest

from app.services.accepted_decision_v2_runtime_service import (
    accepted_v2_fundamental_core_sha256,
    validate_accepted_v2_candidate_ownership,
    validate_accepted_v2_stage2_candidate,
)
from app.services.native_accepted_ownership import AcceptedOwnership, BackendOwnershipRegistry
from app.services.native_economic_core import accept_economic_candidate
from app.services.cross_market_decision_engine_service import DecisionEvidencePacket
from tests.native_economic_fixtures import synthetic_economic


def setup_owned(identity="UNSEEN_OWNERSHIP_US", *, market="us", security_type="common_stock"):
    _, policy, invocation, bound = synthetic_economic(identity, market=market, security_type=security_type)
    ledger = BackendOwnershipRegistry()
    handle = ledger.begin(invocation, model="OFFLINE_MODEL_FIXTURE", effort="OFFLINE_EFFORT")
    raw = bound.model_candidate.model_dump_json().encode()
    receipt = ledger.complete(handle, raw)
    return ledger, handle, receipt, invocation, bound, policy, raw


def downstream(core):
    return SimpleNamespace(
        **{name: getattr(core, name) for name in type(core).model_fields},
        fundamental_core_sha256=accepted_v2_fundamental_core_sha256(core),
        new_buyer_axis=SimpleNamespace(reason=core.decisive_reason),
    )


def native(ledger, receipt, invocation, bound, policy, **changes):
    core = bound.model_candidate.candidate
    kwargs = dict(authority_native_v2=True, accepted_ownership=receipt,
                  ownership_registry=ledger, backend_invocation=invocation,
                  offline_ownership_reproof=True)
    kwargs.update(changes)
    return validate_accepted_v2_candidate_ownership(downstream(core), core, policy.bundle.ownership, **kwargs)


def test_issuance_lookup_native_boundary_and_default_off():
    ledger, _, receipt, invocation, bound, policy, _ = setup_owned()
    assert isinstance(receipt, AcceptedOwnership)
    assert receipt.provenance == "OFFLINE_TRANSPORT_FIXTURE"
    assert receipt.accepted_owner == "OFFLINE_VALIDATION_REPROOF"
    assert native(ledger, receipt, invocation, bound, policy) == ()
    assert "TEST_CANDIDATE_NOT_ACCEPTED_MODEL_JUDGMENT" in native(
        ledger, receipt, invocation, bound, policy, offline_ownership_reproof=False)
    assert inspect.signature(validate_accepted_v2_candidate_ownership).parameters["authority_native_v2"].default is False
    core = bound.model_candidate.candidate
    assert validate_accepted_v2_candidate_ownership(downstream(core), core, policy.bundle.ownership) == ()


@pytest.mark.parametrize("field", [
    "request_sha", "prompt_sha", "schema_sha", "invocation_sha", "security_id",
    "generation_id", "source_generation_id", "model", "effort", "attempt_id",
    "raw_response_sha", "validated_candidate_sha", "semantic_validation_sha",
    "authority_validation_sha", "policy_sha", "validator_sha",
])
def test_copied_fields_do_not_authorize_changed_receipt(field):
    ledger, _, receipt, invocation, bound, policy, _ = setup_owned()
    forged = receipt.model_copy(update={field: "a" * 64})
    assert native(ledger, forged, invocation, bound, policy) == ("ISSUED_OWNERSHIP_BINDING_MISMATCH",)


def test_public_fields_unissued_id_wrong_registry_and_forged_capability():
    ledger, _, receipt, invocation, bound, policy, raw = setup_owned()
    forged = receipt.model_copy(update={"accepted_output_id": "a" * 64})
    assert native(ledger, forged, invocation, bound, policy) == ("UNISSUED_ACCEPTED_OUTPUT",)
    assert native(BackendOwnershipRegistry(), receipt, invocation, bound, policy) == ("UNISSUED_ACCEPTED_OUTPUT",)
    with pytest.raises(ValueError, match="UNISSUED_ATTEMPT_CAPABILITY"):
        ledger.complete({"attempt_id": receipt.attempt_id}, raw)


def test_provenance_field_edit_cannot_promote_test_receipt():
    ledger, _, receipt, invocation, bound, policy, _ = setup_owned()
    forged = receipt.model_copy(update={"provenance": "MODEL_TRANSPORT", "accepted_owner": "BACKEND_MODEL_RUNTIME"})
    assert native(ledger, forged, invocation, bound, policy, offline_ownership_reproof=False) == (
        "ISSUED_OWNERSHIP_BINDING_MISMATCH",)
    with pytest.raises(ValueError, match="EXECUTION_PURPOSE_PROVENANCE_MISMATCH"):
        BackendOwnershipRegistry(offline_reproof=False).begin(invocation, model="fixture", effort="fixture")


def test_wrapper_removal_never_creates_backend_issuance():
    ledger, _, _, invocation, bound, policy, _ = setup_owned()
    test_output = accept_economic_candidate(bound, invocation.request, invocation=invocation)
    for value in (test_output, test_output.candidate, test_output.model_dump(mode="json"), None):
        assert native(ledger, value, invocation, bound, policy) == ("BACKEND_ISSUED_OWNERSHIP_REQUIRED",)
    handle = ledger.begin(invocation, model="fixture", effort="fixture")
    with pytest.raises(ValueError):
        ledger.complete(handle, test_output.model_dump_json().encode())
    assert ledger.attempt_states()[-1]["status"] == "REJECTED"


def test_invalid_first_valid_second_no_rejected_response_revival():
    _, policy, invocation, bound = synthetic_economic()
    ledger = BackendOwnershipRegistry()
    first = ledger.begin(invocation, model="fixture", effort="fixture")
    invalid = bound.model_candidate.model_dump(mode="json")
    invalid["candidate"]["directional_balance"] = dict(buy=6, sell=4)
    with pytest.raises(ValueError, match="REJECT_ECONOMIC_SEMANTICS"):
        ledger.complete(first, json.dumps(invalid).encode())
    raw = bound.model_candidate.model_dump_json().encode()
    with pytest.raises(ValueError, match="CLOSED_REJECTED_ATTEMPT"):
        ledger.complete(first, raw)
    second = ledger.begin(invocation, model="fixture", effort="fixture")
    receipt = ledger.complete(second, raw)
    assert receipt.attempt_number == 2
    assert native(ledger, receipt, invocation, bound, policy) == ()
    with pytest.raises(ValueError, match="SUPERSEDED_ATTEMPT"):
        ledger.complete(first, raw)


def test_duplicate_identical_response_idempotent_conflict_rejected_and_retry_revokes():
    ledger, handle, receipt, invocation, bound, policy, raw = setup_owned()
    assert ledger.complete(handle, raw) == receipt
    with pytest.raises(ValueError, match="RESPONSE_CONFLICT"):
        ledger.complete(handle, raw + b"\n")
    replacement = ledger.begin(invocation, model="fixture", effort="fixture")
    assert native(ledger, receipt, invocation, bound, policy) == ("STALE_OR_SUPERSEDED_ACCEPTED_OUTPUT",)
    current = ledger.complete(replacement, raw)
    assert current.accepted_output_id != receipt.accepted_output_id
    assert native(ledger, current, invocation, bound, policy) == ()


def test_wrong_invocation_same_public_request_and_changed_candidate_fail():
    ledger, _, receipt, invocation, bound, policy, _ = setup_owned()
    assert native(ledger, receipt, deepcopy(invocation), bound, policy) == ("BACKEND_INVOCATION_CAPABILITY_MISMATCH",)
    core = bound.model_candidate.candidate.model_copy(update={"confidence": "LOW"})
    errors = validate_accepted_v2_candidate_ownership(
        downstream(core), core, policy.bundle.ownership, authority_native_v2=True,
        accepted_ownership=receipt, ownership_registry=ledger, backend_invocation=invocation,
        offline_ownership_reproof=True)
    assert errors == ("ISSUED_CANDIDATE_BINDING_MISMATCH",)


@pytest.mark.parametrize("identity,market,security_type", [
    ("UNSEEN_US_OWNED", "us", "common_stock"),
    ("UNSEEN_KR_OWNED", "kr", "common_stock"),
    ("UNSEEN_ADS_OWNED", "us", "depositary_receipt"),
])
def test_unseen_same_backend_and_native_contract(identity, market, security_type):
    ledger, _, receipt, invocation, bound, policy, _ = setup_owned(identity, market=market, security_type=security_type)
    assert native(ledger, receipt, invocation, bound, policy) == ()
    assert receipt.security_id == invocation.request.invocation.security_id
    assert receipt.provenance == "OFFLINE_TRANSPORT_FIXTURE"


def test_feature_gate_required_even_with_valid_ownership():
    ledger, _, receipt, invocation, bound, policy, _ = setup_owned()
    assert native(ledger, receipt, invocation, bound, policy, authority_native_v2=False) == (
        "native_ownership_requires_explicit_feature_gate",)


@pytest.mark.parametrize("field", ["prompt", "response_schema_json"])
def test_changed_pinned_request_cannot_issue(field):
    _, _, invocation, bound = synthetic_economic()
    ledger = BackendOwnershipRegistry()
    handle = ledger.begin(invocation, model="fixture", effort="fixture")
    invocation._request_json = invocation.request.model_copy(update={field: "forged"}).model_dump_json()
    with pytest.raises(ValueError, match="REJECT_REQUEST_IDENTITY_BINDING"):
        ledger.complete(handle, bound.model_candidate.model_dump_json().encode())
    assert ledger.attempt_states()[-1]["status"] == "REJECTED"


def test_offline_ownership_never_produces_ordinary_stage2_acceptance():
    ledger, _, receipt, invocation, bound, policy, _ = setup_owned()
    core = bound.model_candidate.candidate
    for offline in (True, False):
        result = validate_accepted_v2_stage2_candidate(
            None, downstream(core), core, policy.bundle.ownership,
            authority_native_v2=True, accepted_ownership=receipt, ownership_registry=ledger,
            backend_invocation=invocation, offline_ownership_reproof=offline)
        assert not result.valid
        assert result.errors == ("TEST_CANDIDATE_NOT_ACCEPTED_MODEL_JUDGMENT",)


def test_backend_downstream_packet_binding_is_exact_and_nontransferable():
    ledger, _, receipt, invocation, bound, _, _ = setup_owned()
    core = bound.model_candidate.candidate
    packet = DecisionEvidencePacket(packet_id="offline-packet-generation-a", ticker=core.ticker,
        company_name="SYNTHETIC", market="us", assessment_date="2026-10-09", horizon="fixture",
        evidence=(), prohibited_claims=(), evidence_sha256="a" * 64)
    args = dict(invocation=invocation, candidate=core, packet=packet, allow_offline_reproof=True)
    with pytest.raises(ValueError, match="UNISSUED_DOWNSTREAM_PACKET_BINDING"):
        ledger.verify_downstream_packet(receipt, **args)
    binding = ledger.bind_downstream_packet(receipt, **args)
    assert ledger.verify_downstream_packet(receipt, **args) == binding
    assert binding["generation_id"] == receipt.generation_id
    for changed in (packet.model_copy(update={"packet_id": "another-generation"}),
                    packet.model_copy(update={"assessment_date": "2026-10-10"}),
                    packet.model_copy(update={"evidence_sha256": "b" * 64})):
        with pytest.raises(ValueError, match="DOWNSTREAM_PACKET_IDENTITY_GENERATION_MISMATCH"):
            ledger.verify_downstream_packet(receipt, **(args | dict(packet=changed)))
        with pytest.raises(ValueError, match="DOWNSTREAM_PACKET_REBIND_FORBIDDEN"):
            ledger.bind_downstream_packet(receipt, **(args | dict(packet=changed)))
    with pytest.raises(ValueError, match="TEST_CANDIDATE_NOT_ACCEPTED_MODEL_JUDGMENT"):
        ledger.verify_downstream_packet(receipt, **(args | dict(allow_offline_reproof=False)))
