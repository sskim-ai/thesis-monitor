"""Original synthetic owners; an unproven crosswalk never becomes admission."""
from copy import deepcopy
import json

import pytest

from app.services.canonical_native_admission import (
    CanonicalNativeAdmission,
    CanonicalNativeGap,
    CanonicalToNativeAdmissionProducer,
    _property_crosswalk,
    _source_input_bundle,
    _subject_evidence,
)
from app.services.canonical_native_source_owner import (
    CanonicalPreparedSourceOwner, prepare_owned_monitoring_source,
)
from app.services.native_authority_core import (
    build_context, build_native_core_request, materialize_native_reference_output, prompt_context,
)
from app.services.native_economic_core import InvocationSpec
from app.services.native_input_admission import Consumer, NativeAdmissionInput, UseAxis, UseState
from app.services.unified_snapshot_contract import digest
from app.services.unified_stock_acquisition import UNIVERSE
from tests.test_post_r22_ng18_manual_native import original_source as _original_source_fixture
from tests.test_reviewed_economic_property import reviewed_fixture

original_source = _original_source_fixture


@pytest.mark.parametrize("market,ticker", [(m, t) for m, ts in UNIVERSE.items() for t in ts])
def test_all22_original_canonical_source_to_native_visibility_input(
        original_source, market, ticker, record_property):
    owner = original_source[1]
    admission = CanonicalToNativeAdmissionProducer(owner).produce_source_inputs(
        ticker, request_id="ng18-source-input:" + ticker)
    assert type(admission) is CanonicalNativeAdmission
    assert admission.source_owner is owner and admission.ticker == ticker
    registry, request, receipt = admission.registry, admission.reference_request, admission.receipt
    assert admission.policy is None
    assert request.context.market == market and request.context.ticker == ticker
    assert receipt["admission_scope"] == "CORE_VISIBILITY_ONLY"
    assert not receipt["model_dispatch_allowed"] and receipt["consumer_gaps"]
    metrics = registry.bundle.metrics
    assert metrics and request.context.metric_authority_envelopes == metrics
    subject = owner.resolve_subject(ticker)
    comparisons, _ = _subject_evidence(subject, ticker)
    assert len(metrics) == len(comparisons) * 2
    occurrences = {row["metric_ref"]: row for row in receipt["source_occurrences"]}
    for metric in metrics:
        row = occurrences[metric.metric_ref]
        fact, projection = comparisons[row["canonical_ref"]]
        source = fact["field_dependency_receipts"][row["role"]]["lineage"]
        assert projection.kind == "COMPARISON"
        assert metric.value == source["amount"]
        assert metric.currency == source["currency"] == metric.unit
        assert metric.security_id == projection.security_id
        assert metric.generation_id == subject["generation_id"]
        assert metric.source_generation_id == subject["source_generation_id"]
        assert metric.source_artifact_sha256 == digest(fact) == row["fact_sha256"]
        assert metric.input_sha256 == digest(fact["field_dependency_receipts"][row["role"]])
        assert row["source_row_identity"] == source["source_row_identity"]
        assert row["issuer_id"] == fact["fields"]["issuer_id"]
        assert row["provider_issuer_id"] == projection.issuer_id
        assert metric.source_provider == ("opendart" if market == "kr" else "sec_edgar")
        assert row["lineage_sha256"] == digest(source)
        assert metric.owner_receipt_sha256 == digest(row["owner_receipt"])
        assert registry.receipt(metric.metric_ref).source_artifact_sha256 == digest(fact)
        temporal = {field.field: field for field in metric.temporal}
        assert temporal["source_statement_period"].value == (
            source["amount_period_start"] + "/" + source["amount_period_end"])
        assert temporal["financial_period"].value == source["amount_period_end"]
        assert temporal["retrieval_timestamp"].value is None
        assert temporal["metric_as_of"].value is None
        assert temporal["price_session"].value is None and metric.share_basis is None
        for axis in UseAxis:
            consumer = Consumer(axis.value.split("_", 1)[0])
            visible = axis == UseAxis.CORE_VISIBILITY
            assert metric.use(axis) == (UseState.ALLOWED if visible else UseState.UNSPECIFIED)
            assert registry.allowed(metric.metric_ref, consumer, axis) is visible
    value = NativeAdmissionInput(security_id=request.context.security_id,
        generation_id=request.context.generation_id, source_generation_id=request.context.source_generation_id,
        metric_refs=tuple(m.metric_ref for m in metrics))
    context = build_context(admission_input=value, registry=registry, request_id=request.context.request_id)
    assert context == request.context
    assert build_native_core_request(context, registry=registry) == request
    # Original Native prompt exposes restrictions, not numeric business inputs,
    # when visibility is the only grant. Do not relabel it valuation/direction.
    payload = prompt_context(context)
    assert payload["NON_DIRECTIONAL_VALUATION_CONTEXT"] == payload["DIRECTIONAL_EVIDENCE"] == []
    assert payload["issuer_financial_context"] is None
    assert payload["authority_restrictions"]
    assert json.loads(request.prompt.split("\n", 1)[1]) == payload
    record_property("ng18_source_input_admission", dict(
        provenance="SYNTHETIC_ORIGINAL_FULL_SOURCE_TO_NATIVE_INPUT", ticker=ticker, market=market,
        request_sha256=request.authorization.request_sha256, metrics=len(metrics),
        granted_axes=["CORE_VISIBILITY"], native_numeric_prompt_consumer=False,
        manual_parent_proven=False, economic_qualification=False,
        consumer_gaps=receipt["consumer_gaps"]))


@pytest.mark.parametrize("ticker", ["000660", "CORZ"])
def test_source_input_native_validator_denies_every_nonvisibility_axis(original_source, ticker):
    admission = CanonicalToNativeAdmissionProducer(original_source[1]).produce_source_inputs(
        ticker, request_id="ng18-source-input-denial:" + ticker)
    registry, request = admission.registry, admission.reference_request
    ref = request.context.request_evidence_membership[0]
    for axis in UseAxis:
        if axis == UseAxis.CORE_VISIBILITY:
            continue
        with pytest.raises(ValueError, match="REJECT_CONSUMER_AUTHORITY"):
            materialize_native_reference_output(dict(selections=[dict(
                consumer=axis.value.split("_", 1)[0], use_axis=axis.value, evidence_refs=[ref])]),
                request, registry=registry,
                expected_request_sha256=request.authorization.request_sha256)


@pytest.mark.parametrize("kind", ["QUALITY", "ISSUER_CONTEXT"])
def test_noncomparison_cannot_enter_source_input_mapper(original_source, kind):
    subject = original_source[1].resolve_subject("CORZ")
    comparisons, _ = _subject_evidence(subject, "CORZ")
    ref, (fact, projection) = next(iter(comparisons.items()))
    with pytest.raises(ValueError, match="comparison_issuer_scope_mismatch"):
        _source_input_bundle(subject, "CORZ", {
            ref: (fact, projection.model_copy(update={"kind": kind}))})


def test_empty_comparison_does_not_create_source_input_bundle(original_source):
    with pytest.raises(ValueError, match="economic_comparison_source_inputs_required"):
        _source_input_bundle(original_source[1].resolve_subject("CORZ"), "CORZ", {})


def test_closed_original_source_revokes_issued_visibility_input(original_source):
    _, owner = prepare_owned_monitoring_source(enabled=True, **original_source[2])
    try:
        admission = CanonicalToNativeAdmissionProducer(owner).produce_source_inputs(
            "000660", request_id="ng18-source-input-close")
        admission.verify()
    finally:
        owner.close()
    with pytest.raises(ValueError, match="live_source_owner_required"):
        admission.verify()
    with pytest.raises(ValueError, match="live_source_owner_required"):
        _ = admission.reference_request


def test_rehashed_visibility_registry_cannot_escalate_live_admission(original_source):
    admission = CanonicalToNativeAdmissionProducer(original_source[1]).produce_source_inputs(
        "CORZ", request_id="ng18-source-input-registry-tamper")
    registry = admission.registry
    forged = registry.bundle.model_dump(mode="json")
    for permission in forged["metrics"][0]["permissions"]:
        if permission["axis"] == "CORE_DIRECTION":
            permission.update(state="ALLOWED",
                owner_evidence_ref=forged["metrics"][0]["owner_ref"] + "#/CORE_DIRECTION")
    registry._bundle_json = json.dumps(forged)
    registry._anchor = digest(forged)
    with pytest.raises(ValueError, match="source_input_mapping_changed"):
        admission.verify()


@pytest.mark.parametrize("ticker", ["CORZ", "000660", "SKHY"])
def test_original_full_source_to_typed_property_gap(original_source, ticker):
    _, owner, _ = original_source
    before = digest(owner.source())
    gap = CanonicalToNativeAdmissionProducer(owner).produce(ticker, request_id="ng18:" + ticker)
    assert type(gap) is CanonicalNativeGap
    assert "INDEPENDENT_ECONOMIC_PROPERTY_OWNER_REQUIRED" in gap.reasons
    assert not gap.native_admission_issued and not gap.model_dispatch_allowed
    assert gap.source_relationship_sha256 == owner.resolve_subject(ticker)["source_relationship_sha256"]
    assert not hasattr(gap, "registry") and not hasattr(gap, "reference_request")
    assert digest(owner.source()) == before


def test_actual_economic_d02_does_not_mint_native_core_direction(original_source):
    _, owner, _ = original_source
    subject = owner.resolve_subject("CORZ")
    comparisons, _ = _subject_evidence(subject, "CORZ")
    assert comparisons
    for _, projection in comparisons.values():
        assert "OVERALL_DIRECTION" in projection.allowed_uses
        assert "CORE_DIRECTION" not in projection.allowed_uses
        assert not projection.security_valuation_transfer
    gap = CanonicalToNativeAdmissionProducer(owner).produce("CORZ", request_id="ng18:context-not-direction")
    assert type(gap) is CanonicalNativeGap and not gap.native_admission_issued


@pytest.mark.parametrize("field", ["projection", "binding", "expectation"])
def test_missing_current_d02_denied_by_original_validator(original_source, field):
    subject = original_source[1].resolve_subject("CORZ")
    subject["prepared"]["initial_chain"][field] = {}
    with pytest.raises(ValueError, match="current_d01_d02_required"):
        _subject_evidence(subject, "CORZ")
    # Only the returned copy was changed. No fabricated source capability issued.
    assert isinstance(CanonicalToNativeAdmissionProducer(original_source[1]).produce(
        "CORZ", request_id="ng18:unchanged-owner"), CanonicalNativeGap)


@pytest.mark.parametrize("field,value", [
    ("metadata", []), ("frozen_fact_fields", {}), ("observed_propositions", {}),
])
def test_caller_core_input_not_original_projection(original_source, field, value):
    subject = original_source[1].resolve_subject("CORZ")
    subject["prepared"]["core_input"][field] = value
    with pytest.raises(ValueError, match="canonical_core_input_mismatch"):
        _subject_evidence(subject, "CORZ")


@pytest.mark.parametrize("field,value", [
    ("market", "kr"), ("generation_id", "wrong-generation"),
    ("source_generation_id", "wrong-source"), ("cutoff", "2027-01-01T00:00:00+00:00"),
])
def test_original_subject_scope_cannot_be_relabelled(original_source, field, value):
    subject = original_source[1].resolve_subject("CORZ")
    subject[field] = value
    with pytest.raises(ValueError, match="subject_identity_or_readiness_mismatch"):
        _subject_evidence(subject, "CORZ")


def test_canonical_source_hash_does_not_replace_property_owner(original_source):
    subject = original_source[1].resolve_subject("CORZ")
    comparisons, _ = _subject_evidence(subject, "CORZ")
    with pytest.raises(ValueError, match="live_independent_property_owner_required"):
        _property_crosswalk(subject, "CORZ", comparisons, {
            "source_sha256": digest(subject), "status": "PASS", "allowed": True,
        })


def test_two_genuine_but_unrelated_owners_do_not_establish_crosswalk(original_source):
    _, source_owner, _ = original_source
    property_owner, invocation, _ = reviewed_fixture("CORZ")
    gap = CanonicalToNativeAdmissionProducer(source_owner).produce(
        "CORZ", request_id="ng18:unrelated-property", property_owner=property_owner)
    assert type(gap) is CanonicalNativeGap
    assert "INDEPENDENT_PROPERTY_SOURCE_SCOPE_MISMATCH" in gap.reasons
    assert not gap.native_admission_issued
    assert invocation.request.invocation.execution_purpose == "OFFLINE_CONTRACT_REPROOF"


def test_revoked_independent_owner_is_not_a_reusable_receipt(original_source):
    property_owner, _, _ = reviewed_fixture("CORZ")
    property_owner.revoke(property_owner.admission)
    with pytest.raises(ValueError, match="REVOKED"):
        CanonicalToNativeAdmissionProducer(original_source[1]).produce(
            "CORZ", request_id="ng18:revoked-property", property_owner=property_owner)


def test_original_native_builder_positive_is_separate_from_canonical_crosswalk():
    property_owner, invocation, _ = reviewed_fixture("NG18_UNSEEN_OWNER")
    request = invocation.request.reference_request
    assert build_native_core_request(request.context, registry=invocation._registry) == request
    assert request.context.request_evidence_membership
    assert all(metric.use(UseAxis.CORE_DIRECTION) == UseState.ALLOWED
               for metric in request.context.metric_authority_envelopes)
    assert property_owner.resolve(property_owner.admission)
    assert not isinstance(invocation, CanonicalNativeAdmission)
    assert invocation.request.invocation.execution_purpose == "OFFLINE_CONTRACT_REPROOF"
    # Main's separate manual scope must not rename this existing contract.
    raw = deepcopy(invocation.request.invocation.model_dump(mode="json"))
    raw = {key: raw[key] for key in InvocationSpec.model_fields}
    raw["execution_purpose"] = "MANUAL_SHADOW_UNSENT"
    with pytest.raises(ValueError):
        InvocationSpec.model_validate(raw)


@pytest.mark.parametrize("caller", [None, {}, {"status": "PASS"}, object()])
def test_source_capability_not_a_caller_manifest(caller):
    with pytest.raises(ValueError, match="live_source_capability_required"):
        CanonicalToNativeAdmissionProducer(caller)


def test_unissued_exact_type_source_handle_still_fails():
    source = object.__new__(CanonicalPreparedSourceOwner)
    with pytest.raises(ValueError, match="live_source_owner_required"):
        CanonicalToNativeAdmissionProducer(source).produce("CORZ", request_id="ng18:unissued")


def test_native_admission_constructor_and_unissued_handle_fail_closed():
    with pytest.raises(ValueError, match="backend_admission_issuance_required"):
        CanonicalNativeAdmission()
    forged = object.__new__(CanonicalNativeAdmission)
    with pytest.raises(ValueError, match="live_admission_required"):
        forged.verify()
    with pytest.raises(ValueError, match="live_admission_required"):
        _ = forged.reference_request
