"""Synthetic authority-store controls; actual sealed case is a separate proof."""

from datetime import date
import hashlib
from pathlib import Path

import pytest

from app.services import directional_balance_service
from app.services.reviewed_economic_property import (
    BackendReviewedPropertyOwner,
    EconomicReviewDecision,
    build_reported_property_invocation,
)
from app.services.reported_economic_claim_consumer import ReportedRoleCandidate
from app.services.economic_claim_qualification import EconomicClaimProposal, policy_sha256
from app.services.native_accepted_ownership import BackendOwnershipRegistry
from tests.test_real_economic_property_owner import property_fixture, parent_for
from tests.test_native_owner_session import composition, session


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def reviewed_fixture(
    identity="UNSEEN_REVIEW_US",
    *,
    market="US",
    security_type="common_stock",
    mutate=None,
    amount=30,
):
    _, _, _, old_parent, _, fact_owner, source = property_fixture(
        identity, market=market, security_type=security_type, amount=amount
    )
    old_parent.close()
    review = b"SYNTHETIC_TEST_REVIEW_NOT_REAL_AUTHORITY"
    proposal = b"SYNTHETIC_BOUNDED_HISTORICAL_OPERATING_CLAIM"
    reg = fact_owner.registration
    decision = EconomicReviewDecision(
        review_event_id="synthetic-review",
        reviewer="synthetic-test-owner",
        mandate="R17_USER_AUTHORIZED_EXISTING_POLICY_QUALIFICATION",
        decision="APPROVE_BOUNDED_EXISTING_POLICY_QUALIFICATION",
        proposal_sha256=sha(proposal),
        independent_review_sha256=sha(review),
        inherited_policy_sha256=sha(Path(directional_balance_service.__file__).read_bytes()),
        source_kind="SYNTHETIC_REVIEW_FIXTURE",
        source_artifact_sha256=sha(source),
        source_generation_id=reg.source_generation_id,
        owner_execution_generation_id=reg.execution_generation_id,
        security_id=reg.security_id,
        issuer_id=reg.issuer_id,
        facts=fact_owner.facts,
        economic_meaning="HISTORICAL_REPORTED_OPERATING_PERFORMANCE_IMPROVEMENT",
        materiality_basis="CASE_REVIEW_ENTITY_WIDE_ABSOLUTE_OPERATING_AND_REVENUE_SCALE",
        counterevidence_scope="SEALED_EXACT_PERIOD_CONFLICT_BASIS_AND_DISCOVERY_INDEX",
        unreviewed=(
            "FILING_NARRATIVE",
            "UNSEALED_AMENDMENTS",
            "UNDISCLOSED_ADJUSTMENTS",
            "CAUSE",
            "RECURRENCE",
            "CURRENTNESS",
            "FUTURE_RISKS",
        ),
    )
    raw = decision.model_dump_json().encode()
    args = dict(
        fact_owner=fact_owner,
        decision_bytes=raw,
        trusted_decision_sha256=sha(raw),
        review_bytes=review,
        trusted_review_sha256=sha(review),
        proposal_bytes=proposal,
        source_bytes=source,
        trusted_source_sha256=sha(source),
        execution_generation_id="synthetic-reviewed-consumer",
    )
    if mutate:
        mutate(args, decision)
    owner = BackendReviewedPropertyOwner(**args)
    inv = build_reported_property_invocation(
        owner, invocation_id="reviewed-role-test", assessment_as_of=date(2026, 10, 11)
    )
    s = inv.request.invocation
    claim = EconomicClaimProposal(
        claim_id="bounded-business-support",
        security_id=s.security_id,
        generation_id=s.generation_id,
        source_generation_id=s.source_generation_id,
        requested_role="BUY_DRIVER",
        interpretation_type="BUSINESS_SUPPORT",
        polarity="POSITIVE",
        uncertainty="LIMITED",
        support_refs=tuple(s.support_ref for s in inv._policy.bundle.supports),
        policy_sha256=policy_sha256(),
    )
    return owner, inv, ReportedRoleCandidate(proposal=claim, confidence="LOW")


def issue(parent, inv, candidate):
    handle = parent.begin(inv.request.invocation.invocation_id)
    receipt = parent.complete(handle, candidate.model_dump_json().encode())
    packet = parent._registry.reported_claim_packet(receipt, invocation=inv)
    return handle, receipt, packet


@pytest.mark.parametrize(
    "identity,market,kind",
    [
        ("UNSEEN_US", "US", "common_stock"),
        ("UNSEEN_KR", "KR", "common_stock"),
        ("UNSEEN_ADS", "US", "depositary_receipt"),
        ("UNSEEN_FINANCIAL", "US", "common_stock"),
        ("UNSEEN_CYCLICAL", "US", "common_stock"),
        ("UNSEEN_SOURCE_FORWARD", "US", "common_stock"),
        ("UNSEEN_INCOMPLETE", "US", "common_stock"),
    ],
)
def test_equivalent_reviewed_property_role_without_complete_core(identity, market, kind):
    owner, inv, candidate = reviewed_fixture(identity, market=market, security_type=kind)
    parent = parent_for(inv)
    handle, receipt, packet = issue(parent, inv, candidate)
    key = inv.request.invocation.invocation_id
    assert parent.reported_economic_claim(key, receipt, packet) == packet
    assert parent.reported_economic_claim(key, receipt, packet) == packet
    assert parent.complete(handle, candidate.model_dump_json().encode()) == receipt
    assert not packet.accepted_Core and not packet.complete_economic_Stage2
    assert packet.source_kind == "SYNTHETIC_REVIEW_FIXTURE"
    assert not parent._registry._accepted
    with pytest.raises(ValueError):
        parent.economic_candidate(key, receipt, packet)
    owner.revoke(owner.admission)
    with pytest.raises(ValueError, match="REVOKED"):
        parent._registry.reported_claim_packet(receipt, invocation=inv)
    with pytest.raises(ValueError, match="REVOKED"):
        parent.reported_economic_claim(key, receipt, packet)


@pytest.mark.parametrize(
    "field,value",
    [
        ("security_id", "wrong"),
        ("issuer_id", "999"),
        ("source_generation_id", "wrong"),
        ("owner_execution_generation_id", "wrong"),
        ("reviewer", "self-approved"),
        ("source_kind", "REAL_SEALED_SOURCE"),
        ("inherited_policy_sha256", "a" * 64),
        ("independent_review_sha256", "a" * 64),
        ("use_axis", "OVERALL_DIRECTION"),
        ("asserts_causality", True),
        ("asserts_recurrence", True),
        ("unreviewed", ()),
    ],
)
def test_public_rehash_does_not_change_backend_review_pin(field, value):
    def mutate(args, d):
        args["decision_bytes"] = d.model_copy(update={field: value}).model_dump_json().encode()

    with pytest.raises(ValueError):
        reviewed_fixture(mutate=mutate)


@pytest.mark.parametrize(
    "field,value",
    [
        ("issuer_id", "999"),
        ("filing_accession", "wrong"),
        ("occurrence_ordinal", 99999),
        ("period_end", "2020-01-01"),
        ("currency", "EUR"),
        ("source_generation_id", "wrong"),
    ],
)
def test_review_cannot_substitute_original_owner_fact_even_when_backend_pin_changes(field, value):
    def mutate(args, d):
        facts = list(d.facts)
        facts[0] = facts[0].model_copy(update={field: value})
        raw = d.model_copy(update={"facts": tuple(facts)}).model_dump_json().encode()
        args.update(decision_bytes=raw, trusted_decision_sha256=sha(raw))

    with pytest.raises(ValueError):
        reviewed_fixture(mutate=mutate)


@pytest.mark.parametrize(
    "field,value",
    [
        ("security_id", "wrong"),
        ("generation_id", "wrong"),
        ("source_generation_id", "wrong"),
        ("policy_sha256", "a" * 64),
        ("consumer", "HOLDER"),
        ("use_axis", "CORE_CONTEXT"),
        ("asserts_causality", True),
        ("asserts_recurrence", True),
        ("asserts_independent_corroboration", True),
        ("uncertainty", "QUALIFIED"),
        ("requested_role", "DECISIVE_REASON"),
        ("support_refs", ("reviewed:BUSINESS_ANCHOR",)),
        ("numeric_assertions", ({"evidence_ref": "unknown", "value": 987.654321},)),
    ],
)
def test_claim_scope_rejection_precedes_ownership(field, value):
    _, inv, candidate = reviewed_fixture()
    parent = parent_for(inv)
    changed = candidate.model_copy(
        update={"proposal": candidate.proposal.model_copy(update={field: value})}
    )
    with pytest.raises(ValueError):
        issue(parent, inv, changed)
    assert not parent._registry._reported_claim_issued
    assert not parent._registry._accepted
    assert issue(parent, inv, candidate)[1]


@pytest.mark.parametrize(
    "field,value", [("confidence", "HIGH"), ("provenance", "ACCEPTED_MODEL_JUDGMENT")]
)
def test_unadmitted_output_provenance_confidence(field, value):
    _, inv, candidate = reviewed_fixture()
    parent = parent_for(inv)
    with pytest.raises(ValueError):
        issue(parent, inv, candidate.model_copy(update={field: value}))
    assert not parent._registry._reported_claim_issued


def test_actual_stage_session_consumer_and_lifecycle(tmp_path):
    _, inv, candidate = reviewed_fixture()
    parent, scope, body = composition(inv)
    key = inv.request.invocation.invocation_id
    first = session(tmp_path / "first", parent, scope, body)
    handle, receipt, packet = issue(parent, inv, candidate)
    assert first.native_reported_economic_claim(key, receipt, packet) == packet
    next_session = session(tmp_path / "next", parent, scope, body)
    assert next_session.native_reported_economic_claim(key, receipt, packet) == packet
    with pytest.raises(ValueError):
        BackendOwnershipRegistry(offline_reproof=True).consume_reported_claim(
            receipt, invocation=inv, packet=packet
        )
    for field, value in (
        ("output_id", "unissued"),
        ("packet_sha256", "a" * 64),
        ("request_sha256", "a" * 64),
    ):
        with pytest.raises(ValueError):
            first.native_reported_economic_claim(
                key, receipt.model_copy(update={field: value}), packet
            )
    with pytest.raises(ValueError):
        first.native_reported_economic_claim(
            key, receipt, packet.model_copy(update={"generation_id": "wrong"})
        )
    retry = parent.begin(key)
    with pytest.raises(ValueError, match="SUPERSEDED"):
        first.native_reported_economic_claim(key, receipt, packet)
    current = parent.complete(retry, candidate.model_dump_json().encode())
    now = parent._registry.reported_claim_packet(current, invocation=inv)
    assert next_session.native_reported_economic_claim(key, current, now) == now
    parent.revoke(current)
    with pytest.raises(ValueError, match="REVOKED"):
        next_session.native_reported_economic_claim(key, current, now)
    pending = parent.begin(key)
    parent.cancel(pending)
    with pytest.raises(ValueError):
        parent.complete(pending, candidate.model_dump_json().encode())
    parent.close()
    with pytest.raises(ValueError):
        first.native_reported_economic_claim(key, current, now)


def test_genuine_generic_and_v1_routes_cannot_carry_reviewed_fact_property():
    _, inv, candidate = reviewed_fixture()
    registry = BackendOwnershipRegistry(offline_reproof=True)
    with pytest.raises(ValueError, match="ROUTE"):
        registry.begin(inv, model="fixture", effort="fixture")
    with pytest.raises(ValueError, match="ROUTE"):
        registry.begin_claims(inv, model="fixture", effort="fixture")
    assert not registry._accepted


@pytest.mark.parametrize(
    "field", ["security_id", "source_generation_id", "generation_id", "ticker", "market"]
)
def test_consistently_relabelled_registry_cannot_reuse_genuine_review(field):
    from app.services.native_input_admission import BackendAdmissionRegistry
    from app.services.unified_snapshot_contract import digest

    _, inv, _ = reviewed_fixture()
    bundle = inv._registry.bundle
    value = "kr" if field == "market" else "wrong"
    metrics = tuple(
        m.model_copy(update={field: value})
        if field in {"security_id", "source_generation_id", "generation_id"}
        else m
        for m in bundle.metrics
    )
    changed = bundle.model_copy(update={field: value, "metrics": metrics})
    registry = BackendAdmissionRegistry(
        changed, expected_bundle_sha256=digest(changed.model_dump(mode="json"))
    )
    with pytest.raises(ValueError, match="REGISTRY_IDENTITY"):
        inv._policy._verify_property_projection(registry)


@pytest.mark.parametrize("change", ["schema", "validator"])
def test_role_schema_validator_is_pinned_before_attempt_and_retry(monkeypatch, change):
    from app.services import reported_economic_claim_consumer as module

    _, inv, candidate = reviewed_fixture()
    parent = parent_for(inv)
    _, receipt, packet = issue(parent, inv, candidate)
    if change == "schema":
        monkeypatch.setattr(
            module.ReportedRoleCandidate,
            "model_json_schema",
            classmethod(lambda cls, **kw: {"changed": True}),
        )
    else:
        monkeypatch.setattr(module, "role_validator_sha256", lambda: "a" * 64)
    with pytest.raises(ValueError, match="SCHEMA_OR_VALIDATOR"):
        parent.begin(inv.request.invocation.invocation_id)
    with pytest.raises(ValueError, match="SCHEMA_OR_VALIDATOR"):
        parent.reported_economic_claim(inv.request.invocation.invocation_id, receipt, packet)


def test_historical_proposition_is_in_consumed_claim_and_cannot_be_removed():
    _, inv, candidate = reviewed_fixture()
    parent = parent_for(inv)
    _, receipt, packet = issue(parent, inv, candidate)
    for term in (
        "Historical reported operating",
        "Cause, recurrence",
        "current truth",
        "not established",
        "investment stance are not established",
    ):
        assert term in packet.claim.text
    changed = packet.model_copy(
        update={"claim": packet.claim.model_copy(update={"text": "BUY NOW"})}
    )
    with pytest.raises(ValueError, match="PACKET_BINDING"):
        parent.reported_economic_claim(inv.request.invocation.invocation_id, receipt, changed)


def test_wrong_request_parent_and_completed_attempt_conflict():
    _, inv, candidate = reviewed_fixture()
    parent = parent_for(inv)
    handle, receipt, packet = issue(parent, inv, candidate)
    with pytest.raises(ValueError, match="RESPONSE_CONFLICT"):
        parent.complete(handle, candidate.model_dump_json().encode() + b" ")
    with pytest.raises(ValueError):
        parent.reported_economic_claim("unadmitted-invocation", receipt, packet)
    _, other, _ = reviewed_fixture()
    other_parent = parent_for(other)
    with pytest.raises(ValueError):
        other_parent.reported_economic_claim(
            other.request.invocation.invocation_id, receipt, packet
        )
    assert not parent._registry._accepted and not other_parent._registry._accepted


def test_contradictory_owned_observation_cannot_be_approved_as_improvement():
    with pytest.raises(ValueError, match="CONTRADICTS_FACTS"):
        reviewed_fixture(amount=1)


def test_rendered_numbers_preserve_owned_float_precision():
    amount = 30.123456789012344
    owner, inv, candidate = reviewed_fixture(amount=amount)
    parent = parent_for(inv)
    _, receipt, packet = issue(parent, inv, candidate)
    assert str(amount) in packet.claim.text
    assert all(str(f.value) in packet.claim.text for f in owner.admission.review.facts)
    assert (
        parent.reported_economic_claim(inv.request.invocation.invocation_id, receipt, packet)
        == packet
    )
