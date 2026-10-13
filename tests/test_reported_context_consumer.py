"""Synthetic policy/transport proofs; no accepted model judgments."""
from datetime import date
import json

import pytest

from app.services.accepted_decision_v2_runtime_service import (
    accepted_v2_fundamental_core_prompt, build_accepted_v2_economic_core_invocation,
    build_accepted_v2_production_context,
)
from app.services.native_accepted_ownership import BackendOwnershipRegistry
from app.services.native_economic_core import InvocationSpec, economic_admission_gap
from app.services.native_input_admission import BackendAdmissionRegistry, BackendOwnerBundle, UseAxis
from app.services.reported_fact_use_policy import (
    BackendReportedContextPolicy, ReportedContextScope, RoleEvidenceState, role_requirements,
)
from app.services.unified_snapshot_contract import digest
from tests.test_reported_fact_owner import owner_fixture


def context_invocation(owner, *, invocation_id="context-proof", execution="context-execution", market="us"):
    admissions = [owner.admit(f) for f in owner.facts]
    comparisons = [owner.compare(*sorted((a for a in admissions if a.fact.field == field),
                                        key=lambda a: a.fact.period_end, reverse=True))
                   for field in sorted({a.fact.field for a in admissions})]
    policy = BackendReportedContextPolicy(owner)
    grants = tuple(policy.issue(c, invocation_id=invocation_id, execution_generation_id=execution)
                   for c in comparisons)
    f = grants[0].facts[0]
    bundle = BackendOwnerBundle(security_id=f.security_id, ticker=f.ticker, market=market,
        generation_id=execution, source_generation_id=f.source_generation_id,
        source_envelope_sha256=digest(sorted({x.raw_source_sha256 for g in grants for x in g.facts})),
        metrics=(), issuer_context=None)
    registry = BackendAdmissionRegistry(bundle, expected_bundle_sha256=digest(bundle.model_dump(mode="json")))
    context = build_accepted_v2_production_context(packet={}, evidence_packets=(), claim_id=invocation_id,
        authority_native_v2=True, admission_registry=registry, admission_input=dict(
            security_id=f.security_id, generation_id=execution, source_generation_id=f.source_generation_id,
            metric_refs=(), issuer_context=None))
    spec = InvocationSpec(invocation_id=invocation_id, security_id=f.security_id,
        generation_id=execution, source_generation_id=f.source_generation_id,
        assessment_as_of=date(2026,10,10), intended_consumer="CORE",
        allowed_use_axes=(UseAxis.CORE_VISIBILITY, UseAxis.CORE_DIRECTION),
        forbidden_use_axes=tuple(a for a in UseAxis if a not in {UseAxis.CORE_VISIBILITY, UseAxis.CORE_DIRECTION}))
    args = dict(context=context, admission_registry=registry, invocation_spec=spec,
                authority_native_v2=True, reported_context_policy=policy, reported_contexts=grants,
                reported_context_scope=ReportedContextScope(invocation_id=spec.invocation_id,
                    security_id=spec.security_id, generation_id=spec.generation_id,
                    source_generation_id=spec.source_generation_id, assessment_as_of=spec.assessment_as_of,
                    allowed_use_axes=("CORE_REPORTED_CONTEXT",), source_envelope_sha256=bundle.source_envelope_sha256))
    return build_accepted_v2_economic_core_invocation(**args), policy, grants, args


def consume(ledger, inv, receipt, request=None):
    return accepted_v2_fundamental_core_prompt(request or inv.request, backend_invocation=inv,
        context_ownership=receipt, ownership_registry=ledger)


@pytest.mark.parametrize("identity,market,kind", [("UNSEEN_US_CONTEXT","US","common_stock"),
    ("UNSEEN_KR_CONTEXT","KR","common_stock"),("UNSEEN_ADS_CONTEXT","US","depositary_receipt")])
def test_real_native_context_contract_without_economic_promotion(identity,market,kind):
    owner, _ = owner_fixture(identity, market=market, security_type=kind)
    inv, _, grants, _ = context_invocation(owner, market=market.lower())
    ledger = BackendOwnershipRegistry()
    handle = ledger.begin_reported_context(inv)
    receipt = ledger.complete_reported_context(handle)
    prompt = consume(ledger, inv, receipt)
    assert prompt == inv.request.prompt
    assert "NON_DIRECTIONAL_REPORTED_FACT_CONTEXT" in prompt
    assert receipt.contract.endswith("fact-v2") and not receipt.accepted_model_judgment
    assert all(g.permitted_roles == () and g.materiality == "UNKNOWN" for g in grants)
    assert all(g.owner_execution_generation_id == "fixture-execution" for g in grants)
    assert all(g.execution_generation_id == "context-execution" for g in grants)
    schema = json.loads(inv.request.response_schema_json)
    assert schema["properties"]["interpretation_refs"]["items"]["enum"] == []
    assert economic_admission_gap(inv.request, invocation=inv).accepted_directional_judgment is False
    assert ledger.complete_reported_context(handle) == receipt
    assert consume(ledger, inv, receipt) == prompt


@pytest.mark.parametrize("field,value", [("security_id","wrong"),("source_generation_id","wrong"),
    ("execution_generation_id","wrong"),("policy_sha256","a"*64), ("grant_sha256","a"*64),
    ("native_axis","CORE_DIRECTION"),("consumer","HOLDER"),("materiality","QUALIFIED")])
def test_changed_grant_rejected_before_native_request(field,value):
    owner, _ = owner_fixture()
    _, _, grants, args = context_invocation(owner)
    with pytest.raises(ValueError):
        build_accepted_v2_economic_core_invocation(**(args | dict(reported_contexts=(grants[0].model_copy(update={field:value}),))))


@pytest.mark.parametrize("field,value", [("issuer_id","9999"),("filing_accession","wrong"),
    ("occurrence_sha256","a"*64),("raw_source_sha256","a"*64),("value",987.654321)])
def test_changed_supporting_fact_cannot_be_rehashed(field,value):
    owner, _ = owner_fixture()
    _, _, grants, args = context_invocation(owner)
    g = grants[0]
    forged = g.model_copy(update={"facts":(g.facts[0].model_copy(update={field:value}),g.facts[1])})
    forged = forged.model_copy(update={"grant_sha256":digest(forged.model_dump(mode="json"))})
    with pytest.raises(ValueError, match="UNISSUED_OR_CHANGED_CONTEXT"):
        build_accepted_v2_economic_core_invocation(**(args | dict(reported_contexts=(forged,))))


@pytest.mark.parametrize("field,value", [("request_sha","a"*64),("invocation_sha","a"*64),
    ("packet_sha","a"*64),("policy_sha",("a"*64,)),("context_output_id","forged"),
    ("security_id","wrong"),("generation_id","wrong"),("use_axis","CORE_DIRECTION")])
def test_native_consumer_rejects_changed_receipt(field,value):
    owner, _ = owner_fixture()
    inv, _, _, _ = context_invocation(owner)
    ledger = BackendOwnershipRegistry()
    receipt = ledger.complete_reported_context(ledger.begin_reported_context(inv))
    with pytest.raises(ValueError):
        consume(ledger, inv, receipt.model_copy(update={field:value}))
    assert consume(ledger, inv, receipt) == inv.request.prompt


def test_lifetime_retry_revocation_and_no_public_rehydration():
    owner, _ = owner_fixture()
    inv, _, _, args = context_invocation(owner)
    ledger = BackendOwnershipRegistry()
    h1 = ledger.begin_reported_context(inv)
    r1 = ledger.complete_reported_context(h1)
    for other in (BackendOwnershipRegistry(), BackendOwnershipRegistry(offline_reproof=False)):
        with pytest.raises(ValueError, match="UNISSUED_CONTEXT"):
            consume(other, inv, r1)
    twin = build_accepted_v2_economic_core_invocation(**args)
    with pytest.raises(ValueError, match="INVOCATION_MISMATCH"):
        consume(ledger, twin, r1)
    h2 = ledger.begin_reported_context(inv)
    with pytest.raises(ValueError, match="SUPERSEDED"):
        ledger.complete_reported_context(h1)
    with pytest.raises(ValueError, match="SUPERSEDED"):
        consume(ledger, inv, r1)
    r2 = ledger.complete_reported_context(h2)
    assert r2.attempt_number == 2
    assert consume(ledger, inv, r2)
    ledger.revoke(r2)
    with pytest.raises(ValueError, match="REVOKED"):
        consume(ledger, inv, r2)
    with pytest.raises(ValueError, match="CLOSED_CONTEXT"):
        ledger.complete_reported_context(h2)
    r3 = ledger.complete_reported_context(ledger.begin_reported_context(inv))
    assert consume(ledger, inv, r3)
    assert not ledger.attempt_states()  # No accepted-economic cache entry was created.


def test_v1_downgrade_and_unissued_native_consumer():
    from tests.test_native_accepted_ownership import setup_owned

    owner, _ = owner_fixture()
    inv, _, _, _ = context_invocation(owner)
    ledger = BackendOwnershipRegistry()
    with pytest.raises(ValueError, match="FACT_V2_CONTEXT_ROUTE_REQUIRED"):
        ledger.begin(inv, model="SYNTHETIC_ONLY", effort="test")
    with pytest.raises(ValueError, match="FACT_V2_CONTEXT_OWNERSHIP_REQUIRED"):
        consume(ledger, inv, None)
    v1_ledger, _, v1, _, _, _, _ = setup_owned()
    for receipt in (v1, v1.model_copy(update={"contract":"backend-reported-context-ownership-fact-v2"})):
        with pytest.raises(ValueError, match="FACT_V2_CONTEXT_OWNERSHIP_REQUIRED"):
            consume(v1_ledger, inv, receipt)
    assert not ledger.attempt_states()


@pytest.mark.parametrize("field", ["prompt","response_schema_json"])
def test_prompt_or_schema_packet_mutation(field):
    owner, _ = owner_fixture()
    inv, _, _, _ = context_invocation(owner)
    ledger = BackendOwnershipRegistry()
    r = ledger.complete_reported_context(ledger.begin_reported_context(inv))
    with pytest.raises(ValueError, match="IDENTITY_BINDING"):
        consume(ledger, inv, r, inv.request.model_copy(update={field:"forged"}))


@pytest.mark.parametrize("changes,expected", [
    ({"mechanism":"UNKNOWN","recurrence":"UNKNOWN"}, "CONTEXT_ONLY"),
    ({"material_anchor":"NEGLIGIBLE_OR_ZERO_BASE"}, "CONTEXT_ONLY"),
    ({"recurrence":"NONRECURRING"}, "CAUTION_CONTEXT"),
    ({"counterevidence":"MATERIAL_CONFLICT"}, "CAUTION_CONTEXT"),
    ({"independent_support":False}, "CONTEXT_ONLY"),
    ({"all_core_roles":False}, "ELIGIBLE_FOR_EXISTING_ROLE_REVIEW"),
])
def test_generic_policy_consistency(changes,expected):
    state = RoleEvidenceState(material_anchor="QUALIFIED", mechanism="QUALIFIED", recurrence="RECURRING",
        counterevidence="CHECKED_NO_MATERIAL_CONFLICT", independent_support=True, all_core_roles=True)
    result = role_requirements(state.model_copy(update=changes))
    assert result.disposition == expected
    assert not result.automatic_roles and not result.complete_core_eligible
    assert result.authority_state == "PROPOSED_REQUIRES_DECISION"
    assert result.confidence_ceiling == "NOT_AUTHORIZED"


def test_future_filing_rejected_for_past_assessment():
    owner, _ = owner_fixture()
    _, _, _, args = context_invocation(owner)
    earlier = date(2026,5,1)
    args["invocation_spec"] = args["invocation_spec"].model_copy(update={"assessment_as_of":earlier})
    args["reported_context_scope"] = args["reported_context_scope"].model_copy(update={"assessment_as_of":earlier})
    with pytest.raises(ValueError, match="NOT_AVAILABLE_AT_ASSESSMENT"):
        build_accepted_v2_economic_core_invocation(**args)


def test_context_requires_explicit_scope_and_native_visibility():
    owner, _ = owner_fixture()
    _, _, _, args = context_invocation(owner)
    for scope in (None, args["reported_context_scope"].model_copy(update={"allowed_use_axes":()})):
        with pytest.raises(ValueError, match="SCOPE"):
            build_accepted_v2_economic_core_invocation(**(args | dict(reported_context_scope=scope)))
    allowed = (UseAxis.CORE_VALUATION_CONTEXT,)
    spec = args["invocation_spec"].model_copy(update=dict(allowed_use_axes=allowed,
        forbidden_use_axes=tuple(a for a in UseAxis if a not in allowed)))
    with pytest.raises(ValueError, match="CONSUMER_SCOPE"):
        build_accepted_v2_economic_core_invocation(**(args | dict(invocation_spec=spec)))


@pytest.mark.parametrize("field,value", [("source_envelope_sha256","a"*64),("market","kr")])
def test_two_genuine_capabilities_require_same_source_envelope(field,value):
    owner, _ = owner_fixture()
    _, _, _, args = context_invocation(owner)
    bundle = args["admission_registry"].bundle.model_copy(update={field:value})
    registry = BackendAdmissionRegistry(bundle, expected_bundle_sha256=digest(bundle.model_dump(mode="json")))
    from app.services.native_authority_core import build_context
    context = build_context(admission_input=dict(security_id=bundle.security_id,
        generation_id=bundle.generation_id, source_generation_id=bundle.source_generation_id,
        metric_refs=()), registry=registry, request_id=args["context"].request_id)
    scope = args["reported_context_scope"].model_copy(update={"source_envelope_sha256":bundle.source_envelope_sha256})
    with pytest.raises(ValueError, match="SOURCE_ENVELOPE"):
        build_accepted_v2_economic_core_invocation(**(args | dict(admission_registry=registry,
            context=context, reported_context_scope=scope)))


@pytest.mark.parametrize("context_first", [True, False])
def test_genuine_v1_v4_cannot_share_invocation_identity(context_first):
    from tests.native_economic_fixtures import synthetic_economic
    _, _, legacy, _ = synthetic_economic()
    owner, _ = owner_fixture()
    context, _, _, _ = context_invocation(owner, invocation_id=legacy.request.invocation.invocation_id)
    ledger = BackendOwnershipRegistry()
    if context_first:
        ledger.begin_reported_context(context)
        with pytest.raises(ValueError, match="INVOCATION_ROUTE"):
            ledger.begin(legacy, model="OFFLINE_ONLY", effort="NONE")
    else:
        ledger.begin(legacy, model="OFFLINE_ONLY", effort="NONE")
        with pytest.raises(ValueError, match="INVOCATION_ROUTE"):
            ledger.begin_reported_context(context)
