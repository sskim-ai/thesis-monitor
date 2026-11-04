"""Bounded original-consumer attempts; source visibility is not manual admission.

The NG18 synthetic source fixture has no authenticated whole-capture replay or
live prospective Class-C owners. Never manufacture that missing parent. The
two explicit boundary tests record NOT_PROVEN even when their denial asserts
correctly. All fixtures stay inside a single pytest process/generation.
"""
from contextlib import contextmanager
from copy import deepcopy
import json

import pytest

from app.services.canonical_native_admission import (
    CanonicalNativeAdmission, CanonicalNativeGap, CanonicalToNativeAdmissionProducer,
    _source_input_bundle, _subject_evidence,
)
from app.services.canonical_native_source_owner import prepare_owned_monitoring_source
from app.services.manual_native_owner import (
    BackendManualNativeParent, issue_manual_native_parents, original_market_acceptance,
)
from app.services.manual_shadow_source_session import ManualShadowSourceSession
from app.services.native_authority_core import (
    materialize_native_reference_output, prompt_context,
)
from app.services.native_input_admission import Consumer, UseAxis, UseState
from app.services.production_monitoring_session import ProductionMonitoringSession
from app.services.unified_snapshot_contract import digest
from app.services.unified_stock_acquisition import UNIVERSE
from tests.ng19_timing import emit, observe_original_calls, span
from tests.rev8_source_fixtures import POLICY
from tests.test_post_r22_ng18_manual_native import original_source_args


FIRST = (("kr", UNIVERSE["kr"][0]), ("us", UNIVERSE["us"][0]))
REMAINING = tuple((market, ticker) for market in ("kr", "us")
                  for ticker in UNIVERSE[market][1:])
HELD_OUT = ("035420", "NVDA", "UNREGISTERED")
MANUAL_MISSING_GATE = "AUTHENTICATED_WHOLE_CAPTURE_AND_LIVE_PROSPECTIVE_CLASS_C_REQUIRED"


@pytest.fixture(scope="module")
def source_case(tmp_path_factory):
    owner = None
    with observe_original_calls("ng19-source-fixture"):
        with span("owner_fixture", subjects=22):
            args = original_source_args(tmp_path_factory.mktemp("ng19-source"))
        with span("whole_source", subjects=22):
            source, owner = prepare_owned_monitoring_source(enabled=True, **args)
    source_pin, whole_pin = digest(source), digest(args["whole"])
    try:
        yield source, owner, args
        assert digest(source) == source_pin and digest(args["whole"]) == whole_pin
    finally:
        if owner is not None:
            owner.close()


def _produce(owner, ticker, suffix="positive"):
    with span("per_subject_build", ticker=ticker), observe_original_calls("ng19-" + suffix):
        result = CanonicalToNativeAdmissionProducer(owner).produce_source_inputs(
            ticker, request_id="ng19:" + suffix + ":" + ticker)
    assert type(result) is CanonicalNativeAdmission
    assert result.ticker == ticker and result.source_owner is owner
    return result


def _exact_reference(owner, admission, market, ticker):
    # Cache only this returned view locally. Each original accessor still runs
    # its full validator; no application cache or private registry is touched.
    with span("source_extraction", ticker=ticker):
        subject = owner.resolve_subject(ticker)
        comparisons, _ = _subject_evidence(subject, ticker)
    with span("reference_request", ticker=ticker):
        request = admission.reference_request
    context = request.context
    assert context.market == market and context.ticker == ticker
    assert context.generation_id == subject["generation_id"]
    assert context.source_generation_id == subject["source_generation_id"]
    assert context.request_id == "ng19:positive:" + ticker
    metrics = context.metric_authority_envelopes
    assert comparisons and len(metrics) == 2 * len(comparisons)
    expected_refs = {ref + ":" + role for ref in comparisons for role in ("current", "comparison")}
    assert {metric.metric_ref for metric in metrics} == expected_refs
    assert set(context.request_evidence_membership) == expected_refs
    receipts = {row.evidence_ref: row for row in context.input_admission}
    assert set(receipts) == expected_refs
    for metric in metrics:
        ref, role = metric.metric_ref.rsplit(":", 1)
        fact, projection = comparisons[ref]
        dependency = fact["field_dependency_receipts"][role]
        lineage = dependency["lineage"]
        assert projection.kind == "COMPARISON"
        assert metric.value == lineage["amount"]
        assert metric.currency == metric.unit == lineage["currency"]
        # Listing market never substitutes for the statement currency. The
        # existing FPI fixture is TWD even though the security is US-listed.
        assert metric.currency == fact["fields"]["currency"]
        assert metric.security_id == projection.security_id == context.security_id
        assert metric.generation_id == context.generation_id
        assert metric.source_generation_id == context.source_generation_id
        assert metric.source_artifact_sha256 == receipts[metric.metric_ref].source_artifact_sha256 == digest(fact)
        assert metric.input_sha256 == digest(dependency)
        assert metric.source_artifact_ref == ref
        assert metric.source_provider == ("opendart" if market == "kr" else "sec_edgar")
        assert metric.share_basis is None
        assert lineage["source_row_identity"] in fact["fields"]["source_occurrences"]
        temporal = {field.field: field.value for field in metric.temporal}
        assert temporal["source_statement_period"] == lineage["amount_period_start"] + "/" + lineage["amount_period_end"]
        assert temporal["financial_period"] == lineage["amount_period_end"]
        assert all(temporal[key] is None for key in (
            "metric_as_of", "retrieval_timestamp", "price_session",
            "denominator_period_start", "denominator_period_end"))
        for axis in UseAxis:
            assert metric.use(axis) == (UseState.ALLOWED if axis == UseAxis.CORE_VISIBILITY else UseState.UNSPECIFIED)
    # Reconstruct only the deterministic view from already extracted evidence,
    # not another full-22 owner, admission, registry or parent.
    bundle, crosswalk = _source_input_bundle(subject, ticker, comparisons)
    assert context.backend_bundle_sha256 == digest(bundle.model_dump(mode="json"))
    assert context.source_envelope_sha256 == digest(crosswalk)
    rows = {row["metric_ref"]: row for row in crosswalk["occurrences"]}
    for metric in metrics:
        row = rows[metric.metric_ref]
        fact, projection = comparisons[row["canonical_ref"]]
        assert row["issuer_id"] == fact["fields"]["issuer_id"]
        assert row["provider_issuer_id"] == projection.issuer_id
        assert metric.owner_receipt_sha256 == digest(row["owner_receipt"])
        assert row["owner_receipt"]["granted_axes"] == ["CORE_VISIBILITY"]
    payload = prompt_context(context)
    assert payload["DIRECTIONAL_EVIDENCE"] == payload["NON_DIRECTIONAL_VALUATION_CONTEXT"] == []
    assert payload["issuer_financial_context"] is None and payload["authority_restrictions"]
    assert json.loads(request.prompt.split("\n", 1)[1]) == payload
    return dict(market=market, ticker=ticker, status="SOURCE_REFERENCE_PASS",
        request_sha256=request.authorization.request_sha256,
        generation_id=context.generation_id, source_generation_id=context.source_generation_id,
        metrics=len(metrics), granted_axes=["CORE_VISIBILITY"], manual_positive="NOT_PROVEN",
        model_calls=0, b2_enabled=False)


def test_first_kr_us_source_exact_views(source_case, record_property):
    owner = source_case[1]
    rows = []
    for market, ticker in FIRST:
        rows.append(_exact_reference(owner, _produce(owner, ticker), market, ticker))
        emit("subject_completed", **rows[-1])
    record_property("ng19_first_source_views", rows)


@pytest.mark.parametrize("market,ticker", REMAINING, ids=[m + "-" + t for m, t in REMAINING])
def test_remaining_subject_exact_view(source_case, market, ticker, record_property):
    assert len(REMAINING) == 20 and (market, ticker) not in FIRST
    row = _exact_reference(source_case[1], _produce(source_case[1], ticker), market, ticker)
    emit("subject_completed", **row)
    record_property("ng19_source_view", row)


@contextmanager
def _new_stage(source_case, root, market):
    source, owner, args = source_case
    with span("source_extraction", market=market):
        scoped = owner.source(market)
    with span("original_stage_constructor", market=market):
        stage = ProductionMonitoringSession(root, market=market, generation_id=args["generation"],
            source_generation_id=source["source_generation_id"], source=scoped,
            manual_native_v1=True, manual_source_owner=owner)
    yield stage


def _accept_market(stage):
    with span("market_replay", market=stage.market):
        request = stage.build("MARKET")[0]
        stage.freeze_stage("market", [request])
        context = request["payload"]["input"]
        output = dict(market=stage.market.upper(), regime="DATA_INSUFFICIENT", confidence="LOW",
            breadth_state="Synthetic scope probe.", leadership="No investment conclusion.",
            flows_or_participation="No investment conclusion.",
            rates_or_macro_context="No investment conclusion.",
            supporting_refs=list(context["facts"])[:1], contradicting_refs=[])
        stage.accept("MARKET", request, output)
        receipt = original_market_acceptance(stage)
    assert receipt["request_sha256"] == digest(request)
    assert receipt["output_sha256"] == digest(output)
    assert ("MARKET", request["batch"]) in stage._accepted_batches
    return receipt


@pytest.mark.parametrize("market", ["kr", "us"])
def test_original_market_then_native_missing_parent(source_case, tmp_path, market, record_property):
    with _new_stage(source_case, tmp_path / market, market) as stage:
        acceptance = _accept_market(stage)
        with span("original_consumer_attempt", market=market), observe_original_calls("ng19-parent-attempt"):
            with pytest.raises(ValueError, match="^NATIVE_SESSION_FEATURE_DISABLED$"):
                stage.native_manual_request(UNIVERSE[market][0])
        assert stage._native_owner_parent is None and "CORE" not in stage.captured
        record_property("ng19_original_consumer_attempt", dict(
            status="NOT_PROVEN", market=market, market_accepted=True,
            market_request_sha256=acceptance["request_sha256"],
            first_missing_gate=MANUAL_MISSING_GATE,
            native_error="NATIVE_SESSION_FEATURE_DISABLED", native_positive_subjects=[],
            parent_issued=False, b2_enabled=False))


def test_manual_constructor_first_missing_original_gate(tmp_path, record_property):
    # There is intentionally no substitute factory, forged prospective owner,
    # uninitialized instance or copied private owner registry here.
    with span("manual_original_gate_attempt"):
        with pytest.raises(ValueError, match="manual_shadow_exact_live_market_owners_required"):
            ManualShadowSourceSession(tmp_path / "absent-capture", output_root=tmp_path / "unsent",
                frozen={}, outcome={}, policy=POLICY, prospective_owners={},
                source_file_sha256={}, expected_code_fingerprints={}, enabled=True,
                native_admission_enabled=True)
    assert not (tmp_path / "unsent").exists()
    record_property("ng19_manual_attempt", dict(status="NOT_PROVEN", first_missing_gate=MANUAL_MISSING_GATE,
        admit_native_reached=False, native_manual_request_completed=False,
        no_fake_factory=True, synthetic_approval_issued=False, b2_enabled=False))


@pytest.mark.parametrize("market", ["kr", "us"])
def test_economic_and_b2_denials_after_original_market(source_case, tmp_path, market, record_property):
    with _new_stage(source_case, tmp_path / market, market) as stage:
        _accept_market(stage)
        ticker = UNIVERSE[market][0]
        operations = (
            ("build_core", lambda: stage.build("CORE"), "MANUAL_NATIVE_ADMISSION_REQUIRED_BEFORE_CORE"),
            ("capture_core", lambda: stage.capture("core", {}, {}, {}, ""), "MANUAL_NATIVE_ECONOMIC_CONSUMER_CONTRACT_PENDING"),
            ("freeze_core", lambda: stage.freeze_stage("core", []), "MANUAL_NATIVE_ECONOMIC_CONSUMER_CONTRACT_PENDING"),
            ("accept_core", lambda: stage.accept("CORE", {}, {}), "MANUAL_NATIVE_ECONOMIC_CONSUMER_CONTRACT_PENDING"),
            ("economic_prompt", lambda: stage.native_context_prompt("unissued", {}), "MANUAL_INPUT_RECEIPT_IS_NOT_ACCEPTED_ECONOMIC_OWNERSHIP"),
            ("economic_candidate", lambda: stage.native_economic_candidate("unissued", {}, {}), "MANUAL_INPUT_RECEIPT_IS_NOT_ACCEPTED_ECONOMIC_OWNERSHIP"),
            ("b2", lambda: stage.b2_request(ticker), "MANUAL_NATIVE_B2_COVERAGE_CENSUS_NOT_AUTHORIZED"),
        )
        for name, call, reason in operations:
            with span("negative", case=name, market=market):
                with pytest.raises(ValueError, match=reason):
                    call()
        assert set(stage.captured) == {"MARKET"}
        assert not stage.cores and not stage.arows and not stage.brows
        record_property("ng19_economic_boundary", dict(market=market, economic_positive=False,
            status="NG19_LOCAL_ECONOMIC_OWNER_PENDING", b2_enabled=False))


@pytest.mark.parametrize("field,value", [
    ("market", "kr"), ("generation_id", "other-generation"),
    ("source_generation_id", "other-source"), ("cutoff", "2027-01-01T00:00:00+00:00"),
])
def test_subject_identity_negative_fresh_copy(source_case, field, value):
    with span("negative", case=field):
        subject = source_case[1].resolve_subject(UNIVERSE["us"][0])
        subject[field] = value
        with pytest.raises(ValueError, match="subject_identity_or_readiness_mismatch"):
            _subject_evidence(subject, UNIVERSE["us"][0])


@pytest.mark.parametrize("field", ["projection", "binding", "expectation"])
def test_missing_d02_negative_fresh_copy(source_case, field):
    with span("negative", case="missing_" + field):
        subject = source_case[1].resolve_subject(UNIVERSE["us"][0])
        subject["prepared"]["initial_chain"][field] = {}
        with pytest.raises(ValueError, match="current_d01_d02_required"):
            _subject_evidence(subject, UNIVERSE["us"][0])


@pytest.mark.parametrize("field", ["ticker", "security", "issuer"])
def test_fact_identity_negative_fresh_copy(source_case, field):
    ticker = UNIVERSE["us"][0]
    with span("negative", case=field):
        subject = source_case[1].resolve_subject(ticker)
        if field == "ticker":
            with pytest.raises(ValueError, match="subject_identity_or_readiness_mismatch"):
                _subject_evidence(subject, "UNREGISTERED")
            return
        comparisons, _ = _subject_evidence(subject, ticker)
        changed = deepcopy(comparisons)
        ref, (fact, projection) = next(iter(changed.items()))
        if field == "security":
            # An extra comparison cannot introduce a second security identity.
            changed[ref + ":foreign-security"] = (fact, projection.model_copy(update={"security_id": "other-security"}))
            reason = "comparison_security_scope_mismatch"
        else:
            changed[ref] = (fact, projection.model_copy(update={"issuer_id": "other-issuer"}))
            reason = "comparison_issuer_scope_mismatch"
        with pytest.raises(ValueError, match=reason):
            _source_input_bundle(subject, ticker, changed)


@pytest.mark.parametrize("ticker", HELD_OUT)
def test_held_out_membership_stays_denied(source_case, ticker):
    with span("negative", case="not_enrolled", ticker=ticker):
        with pytest.raises(ValueError, match="subject_not_owned"):
            source_case[1].resolve_subject(ticker)


@pytest.mark.parametrize("market", ["kr", "us"])
def test_visibility_cannot_grant_other_axes(source_case, market):
    ticker = UNIVERSE[market][0]
    admission = _produce(source_case[1], ticker, "axis-negative")
    with span("negative", case="every_nonvisibility_axis", market=market):
        request, registry = admission.reference_request, admission.registry
        ref = request.context.request_evidence_membership[0]
        visible = dict(selections=[dict(consumer="CORE", use_axis="CORE_VISIBILITY", evidence_refs=[ref])])
        claim = materialize_native_reference_output(visible, request, registry=registry,
            expected_request_sha256=request.authorization.request_sha256)
        assert claim.claims[0].use_axis == UseAxis.CORE_VISIBILITY
        assert claim.claims[0].evidence[0].evidence_ref == ref
        for axis in UseAxis:
            consumer = Consumer(axis.value.split("_", 1)[0])
            assert registry.allowed(ref, consumer, axis) is (axis == UseAxis.CORE_VISIBILITY)
            if axis != UseAxis.CORE_VISIBILITY:
                with pytest.raises(ValueError, match="REJECT_CONSUMER_AUTHORITY"):
                    materialize_native_reference_output(dict(selections=[dict(
                        consumer=consumer.value, use_axis=axis.value, evidence_refs=[ref])]),
                        request, registry=registry, expected_request_sha256=request.authorization.request_sha256)
        with pytest.raises(ValueError, match="REJECT_REQUEST_IDENTITY_BINDING"):
            materialize_native_reference_output(visible, request, registry=registry,
                expected_request_sha256="0" * 64)


def test_wrong_request_id_cannot_reuse_request_authorization(source_case):
    admission = _produce(source_case[1], UNIVERSE["us"][0], "request-negative")
    request, registry = admission.reference_request, admission.registry
    changed = request.model_copy(update={"context": request.context.model_copy(update={"request_id": "ng19:wrong"})})
    visible = dict(selections=[dict(consumer="CORE", use_axis="CORE_VISIBILITY",
        evidence_refs=[request.context.request_evidence_membership[0]])])
    with span("negative", case="wrong_request_id"):
        with pytest.raises(ValueError, match="REJECT_REQUEST_IDENTITY_BINDING"):
            materialize_native_reference_output(visible, changed, registry=registry,
                expected_request_sha256=request.authorization.request_sha256)


@pytest.mark.parametrize("change", ["source", "prepared", "generation", "source_generation", "market"])
def test_original_stage_drift_fresh_session(source_case, tmp_path, change):
    with _new_stage(source_case, tmp_path / change, "us") as stage:
        if change == "source":
            stage.source["valuation_contexts"][UNIVERSE["us"][0]] = {"unowned": 1}
            reason = "MANUAL_SOURCE_EXTRACTION_MISMATCH"
        elif change == "prepared":
            stage.prepared[UNIVERSE["us"][0]]["mode"] = "UNKNOWN_LIMIT"
            reason = "NATIVE_SESSION_SOURCE_CONTENT_DRIFT"
        elif change == "market":
            stage.market = "kr"
            reason = "MANUAL_SOURCE_EXTRACTION_MISMATCH"
        else:
            setattr(stage, "gen" if change == "generation" else "source_gen", "wrong")
            reason = "MANUAL_SOURCE_GENERATION_MISMATCH"
        with span("negative", case=change):
            with pytest.raises(ValueError, match=reason):
                stage.build("MARKET")
        assert not stage.root.exists() and not stage.captured


def test_closed_fresh_source_revokes_reference(source_case):
    owner = None
    with span("negative", case="source_closed"):
        try:
            _, owner = prepare_owned_monitoring_source(enabled=True, **deepcopy(source_case[2]))
            admission = _produce(owner, UNIVERSE["us"][0], "closed")
            owner.close()
            with pytest.raises(ValueError, match="live_source_owner_required"):
                _ = admission.reference_request
        finally:
            if owner is not None:
                owner.close()


def test_missing_or_serialized_owner_cannot_issue_parent(source_case):
    with span("negative", case="serialized_ownership"):
        relationship = source_case[1].relationship("us")
        with pytest.raises(ValueError, match="live_source_capability_required"):
            CanonicalToNativeAdmissionProducer(relationship)
        with pytest.raises(ValueError, match="source_session_required"):
            issue_manual_native_parents({"nested": {"source_owner": relationship}, "active": True}, {})
        with pytest.raises(ValueError, match="backend_issuance_required"):
            BackendManualNativeParent()
        with pytest.raises(TypeError):
            json.dumps({"nested": {"source_owner": source_case[1]}})


def test_original_economic_owner_gap_is_separate(source_case, record_property):
    ticker = UNIVERSE["us"][0]
    with span("negative", case="missing_economic_property_owner"):
        result = CanonicalToNativeAdmissionProducer(source_case[1]).produce(ticker, request_id="ng19:economic-gap")
    assert type(result) is CanonicalNativeGap
    assert "INDEPENDENT_ECONOMIC_PROPERTY_OWNER_REQUIRED" in result.reasons
    assert not result.native_admission_issued and not result.model_dispatch_allowed
    record_property("ng19_property_gap", result.model_dump(mode="json"))
