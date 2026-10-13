from copy import deepcopy
import inspect

import pytest

from app.services.accepted_decision_v2_runtime_service import (
    validate_accepted_v2_fundamental_core,
    build_accepted_v2_economic_core_invocation,
)
from app.services.native_economic_core import (
    accept_economic_candidate,
    materialize_economic_candidate,
    economic_batch_output,
    downstream_model_judgment_handoff,
    BoundEconomicCandidate,
)
from tests.native_economic_fixtures import synthetic_economic, invocation_for
from tests.native_authority_fixtures import output_for, native_input
from app.services.native_authority_core import build_context


def reject(out, inv, pattern):
    with pytest.raises(ValueError, match=pattern):
        accept_economic_candidate(out, inv.request, invocation=inv)
    assert validate_accepted_v2_fundamental_core(
        out, None, request=inv.request, backend_invocation=inv
    )


def test_native_economic_and_reference_conjunction():
    _, _, inv, out = synthetic_economic()
    accepted = accept_economic_candidate(out, inv.request, invocation=inv)
    assert accepted.candidate == out.model_candidate.candidate
    assert accepted.provenance == "TEST_CANDIDATE_NOT_ACCEPTED_MODEL_JUDGMENT"
    assert (
        validate_accepted_v2_fundamental_core(
            out, None, request=inv.request, backend_invocation=inv
        )
        == ()
    )
    assert not accepted.downstream_decision_handoff
    assert not accepted.same_generation_model_judgment
    with pytest.raises(ValueError, match="NOT_ACCEPTED_MODEL_JUDGMENT"):
        downstream_model_judgment_handoff(accepted)
    assert economic_batch_output([out], [inv.request], invocations=[inv]) == (accepted,)


def test_economic_gate_default_off():
    assert (
        inspect.signature(build_accepted_v2_economic_core_invocation)
        .parameters["authority_native_v2"]
        .default
        is False
    )
    with pytest.raises(ValueError, match="feature_disabled"):
        build_accepted_v2_economic_core_invocation(
            context=None, admission_registry=None, invocation_spec=None
        )


def test_valid_refs_do_not_bypass_existing_economic_invariants():
    _, _, inv, out = synthetic_economic()
    raw = out.model_dump(mode="json")
    raw["model_candidate"]["candidate"]["directional_balance"] = {"buy": 6, "sell": 4}
    reject(raw, inv, "REJECT_ECONOMIC_SEMANTICS:fundamental_core_directional_balance_mismatch")


@pytest.mark.parametrize(
    "field",
    [
        "security_id",
        "generation_id",
        "source_generation_id",
        "request_sha256",
        "invocation_scope_sha256",
    ],
)
def test_output_identity(field):
    _, _, inv, out = synthetic_economic()
    raw = out.model_dump(mode="json")
    raw[field] = "a" * 64
    reject(raw, inv, "REJECT_OUTPUT_IDENTITY_BINDING")


@pytest.mark.parametrize(
    "field", ["owner_ref", "admission_sha256", "authority_sha256", "temporal_sha256"]
)
def test_owner_binding(field):
    _, _, inv, out = synthetic_economic()
    raw = out.model_dump(mode="json")
    raw["references"]["claims"][0]["evidence"][0][field] = "a" * 64
    reject(raw, inv, "REJECT_OWNER_ADMISSION_TEMPORAL_BINDING")


def test_store_only_omitted_request_ref():
    r, policy, _, out = synthetic_economic()
    inv = invocation_for(r, refs=[r.bundle.metrics[0].metric_ref], policy=policy)
    out = materialize_economic_candidate(
        out.model_candidate.model_dump(mode="json"), inv.request, invocation=inv
    )
    reject(out, inv, "REJECT_REQUEST_MEMBERSHIP")


def test_owner_grant_does_not_grant_invocation_scope():
    from tests.native_authority_fixtures import synthetic_registry

    r = synthetic_registry(grants={"METRIC_A": {"HOLDER_CONTEXT": "ALLOWED"}})
    inv = invocation_for(r)
    refs = output_for(r, inv.request.reference_request, axis="HOLDER_CONTEXT")
    with pytest.raises(ValueError, match="REJECT_INVOCATION_CONSUMER_SCOPE"):
        inv.accept_references(refs, inv.request)
    holder = invocation_for(r, consumer="HOLDER")
    assert holder.accept_references(refs, holder.request)
    _, _, _, candidate = synthetic_economic()
    raw = candidate.model_dump(mode="json")
    raw.update(
        request_sha256=inv.request.invocation.request_sha256,
        invocation_scope_sha256=inv.request.invocation.invocation_scope_sha256,
        security_id=r.bundle.security_id,
        generation_id=r.bundle.generation_id,
        source_generation_id=r.bundle.source_generation_id,
        references=refs,
    )
    reject(raw, inv, "REJECT_INVOCATION_CONSUMER_SCOPE")


@pytest.mark.parametrize("field", ["prompt", "response_schema_json"])
def test_request_mutation(field):
    _, _, inv, out = synthetic_economic()
    q = inv.request.model_copy(update={field: "forged"})
    with pytest.raises(ValueError, match="REJECT_REQUEST_IDENTITY_BINDING"):
        accept_economic_candidate(out, q, invocation=inv)


@pytest.mark.parametrize(
    "field",
    [
        "policy_sha256",
        "validator_sha256",
        "owner_sha256",
        "authority_sha256",
        "prompt_sha256",
        "schema_sha256",
    ],
)
def test_request_pins_all_authorities(field):
    _, _, inv, out = synthetic_economic()
    q = inv.request.model_copy(
        update={"invocation": inv.request.invocation.model_copy(update={field: "a" * 64})}
    )
    with pytest.raises(ValueError, match="REJECT_REQUEST_IDENTITY_BINDING"):
        accept_economic_candidate(out, q, invocation=inv)


@pytest.mark.parametrize(
    "text",
    [
        "987.654321 is undervalued",
        "Guaranteed profit",
        "denominator period is 2025-06-30",
        "Unrelated issuer is cheap",
    ],
)
def test_unowned_narrative_with_valid_refs(text):
    _, _, inv, out = synthetic_economic()
    raw = out.model_dump(mode="json")
    raw["model_candidate"]["candidate"]["decisive_reason"]["text"] = text
    reject(raw, inv, "REJECT_UNSUPPORTED_ECONOMIC_INTERPRETATION")


def test_balance_summary_not_unadmitted_side_channel():
    _, _, inv, out = synthetic_economic()
    raw = out.model_dump(mode="json")
    raw["model_candidate"]["candidate"]["balance_summary"] = "unowned claim"
    reject(raw, inv, "REJECT_UNOWNED_BALANCE_NARRATIVE")


def test_claim_cannot_hide_behind_different_authorized_refs():
    _, _, inv, out = synthetic_economic()
    raw = out.model_dump(mode="json")
    raw["references"]["claims"][0] = deepcopy(raw["references"]["claims"][1])
    reject(raw, inv, "REJECT_UNSUPPORTED_ECONOMIC_INTERPRETATION")


def test_reference_only_or_fake_abstention_never_economic_output():
    _, _, inv, out = synthetic_economic()
    for raw in (out.references.model_dump(mode="json"), {"abstention": "missing history"}):
        reject(raw, inv, "validation error")
    raw = out.model_dump(mode="json")
    raw["model_candidate"]["candidate"]["buy_drivers"][0]["evidence_refs"] = []
    reject(raw, inv, "validation error")


@pytest.mark.parametrize(
    "identity,market,security_type",
    [
        ("UNSEEN_US_R10", "us", "common_stock"),
        ("UNSEEN_KR_R10", "kr", "common_stock"),
        ("UNSEEN_ADS_R10", "us", "depositary_receipt"),
    ],
)
def test_same_native_contract_generality(identity, market, security_type):
    _, _, inv, out = synthetic_economic(identity, market=market, security_type=security_type)
    result = accept_economic_candidate(out, inv.request, invocation=inv)
    assert result.candidate.decision == "HOLD"
    assert result.candidate.directional_balance.buy == 5


@pytest.mark.parametrize(
    "field,value",
    [
        ("UNADMITTED_PROBE_RATIO", 987.654321),
        ("free_prose", "cheap"),
        ("date", "2025-06-30"),
        ("owner_ref", "FORGED"),
    ],
)
def test_closed_issuer_context_before_native_request(field, value):
    r, _, _, _ = synthetic_economic()
    data = native_input(r)
    data["issuer_context"][field] = value
    with pytest.raises(ValueError):
        build_context(admission_input=data, registry=r, request_id="injected")


def test_no_silent_optional_history_requirement():
    r, _, inv, out = synthetic_economic()
    assert all(
        t.value is None
        for m in r.bundle.metrics
        for t in m.temporal
        if t.field in {"metric_as_of", "denominator_period_end"}
    )
    assert accept_economic_candidate(out, inv.request, invocation=inv)
    assert r.bundle.metrics[0].value == 12.25


def test_typed_insufficiency_is_not_fake_abstention_or_zero():
    from app.services.native_economic_core import economic_admission_gap

    r, _, inv, _ = synthetic_economic()
    assert economic_admission_gap(inv.request, invocation=inv) is None
    absent = invocation_for(r)
    gap = economic_admission_gap(absent.request, invocation=absent)
    assert set(gap.missing_interpretation_roles) == {
        "BUY_DRIVER",
        "SELL_DRIVER",
        "DECISIVE_REASON",
        "HOLDER_REASON",
    }
    assert not gap.accepted_abstention and not gap.accepted_directional_judgment
    assert (
        gap.preserved_admitted_refs
        == absent.request.reference_request.context.request_evidence_membership
    )
    assert all(m.value == 12.25 for m in r.bundle.metrics)


@pytest.mark.parametrize(
    "axis,state",
    [
        ("CORE_DIRECTION", "DENIED"),
        ("CORE_DIRECTION", "UNSPECIFIED"),
        ("CORE_VISIBILITY", "UNSPECIFIED"),
        ("CORE_VISIBILITY", "DENIED"),
    ],
)
def test_real_acceptance_rejects_absent_direction_or_visibility(axis, state):
    from tests.native_authority_fixtures import synthetic_registry

    r = synthetic_registry(grants={"METRIC_A": {axis: state}})
    inv = invocation_for(r)
    _, _, _, candidate = synthetic_economic()
    raw = candidate.model_dump(mode="json")
    raw.update(
        request_sha256=inv.request.invocation.request_sha256,
        invocation_scope_sha256=inv.request.invocation.invocation_scope_sha256,
        security_id=r.bundle.security_id,
        generation_id=r.bundle.generation_id,
        source_generation_id=r.bundle.source_generation_id,
        references=output_for(r, inv.request.reference_request),
    )
    reject(raw, inv, "REJECT_CONSUMER_AUTHORITY|REJECT_CORE_INPUT_VISIBILITY")


def test_core_grant_not_overall_entitlement_on_native_acceptance():
    r, _, inv, out = synthetic_economic()
    raw = out.model_dump(mode="json")
    raw["references"]["claims"][0]["consumer"] = "OVERALL"
    raw["references"]["claims"][0]["use_axis"] = "OVERALL_DIRECTION"
    reject(raw, inv, "REJECT_INVOCATION_CONSUMER_SCOPE")
    assert (
        r.bundle.metrics[0]
        .use(
            __import__(
                "app.services.native_input_admission", fromlist=["UseAxis"]
            ).UseAxis.OVERALL_DIRECTION
        )
        .value
        == "DENIED"
    )


def test_changed_temporal_context_cannot_be_promoted():
    _, _, inv, out = synthetic_economic()
    q = inv.request
    raw = q.model_dump(mode="json")
    raw["reference_request"]["context"]["metric_authority_envelopes"][0]["temporal"][1]["value"] = (
        "2025-06-30"
    )
    from app.services.native_economic_core import EconomicRequest

    with pytest.raises(ValueError):
        altered = EconomicRequest.model_validate(raw)
        accept_economic_candidate(out, altered, invocation=inv)


def test_bound_shape_revalidates_model_copy():
    _, _, inv, out = synthetic_economic()
    bad = out.model_copy(update={"model_candidate": {"garbage": 1}})
    with pytest.raises(ValueError):
        accept_economic_candidate(bad, inv.request, invocation=inv)
    assert BoundEconomicCandidate.model_validate(out) == out


@pytest.mark.parametrize(
    "field,value", [("decision", "BUY"), ("holder", "REDUCE"), ("confidence", "HIGH")]
)
def test_review_reason_cannot_be_reused_for_unapproved_conclusion(field, value):
    _, _, inv, out = synthetic_economic()
    raw = out.model_dump(mode="json")
    core = raw["model_candidate"]["candidate"]
    if field == "holder":
        core["holder_axis"]["stance"] = value
    else:
        core[field] = value
    if field == "decision":
        core["directional_balance"] = {"buy": 6, "sell": 4}
    reject(raw, inv, "REJECT_INTERPRETATION_CONCLUSION_COMPATIBILITY")


def test_actual_stage2_ownership_boundary_rejects_offline_receipt():
    from app.services.accepted_decision_v2_runtime_service import (
        validate_accepted_v2_candidate_ownership,
    )

    _, policy, inv, out = synthetic_economic()
    receipt = accept_economic_candidate(out, inv.request, invocation=inv)
    assert validate_accepted_v2_candidate_ownership(None, receipt, policy.bundle.ownership) == (
        "native_offline_candidate_not_accepted_model_handoff",
    )
    # Bare legacy candidates are still governed by the legacy trust boundary.
    assert validate_accepted_v2_fundamental_core(receipt.candidate, policy.bundle.ownership) == ()


def test_holder_or_visibility_restriction_filters_prompt_before_exposure():
    from app.services.native_input_admission import BackendAdmissionRegistry, BackendOwnerBundle
    from app.services.native_economic_core import BackendEconomicPolicy, EconomicPolicyBundle
    from app.services.unified_snapshot_contract import digest
    from app.services.native_economic_core import bound_reference

    r, policy, _, _ = synthetic_economic()
    holder = invocation_for(r, consumer="HOLDER", policy=policy)
    assert policy.bundle.interpretations[0].claim.text not in holder.request.prompt
    bundle = r.bundle.model_dump(mode="json")
    for m in bundle["metrics"]:
        for p in m["permissions"]:
            if p["axis"] == "CORE_VISIBILITY":
                p["state"] = "DENIED"
    b = BackendOwnerBundle.model_validate(bundle)
    denied = BackendAdmissionRegistry(b, expected_bundle_sha256=digest(b.model_dump(mode="json")))
    p = policy.bundle.model_dump(mode="json")
    p["backend_bundle_sha256"] = digest(b.model_dump(mode="json"))
    for row in p["interpretations"]:
        row["evidence"] = [
            bound_reference(denied, r).model_dump(mode="json")
            for r in row["claim"]["evidence_refs"]
        ]
    p = EconomicPolicyBundle.model_validate(p)
    sealed = BackendEconomicPolicy(
        p, expected_policy_sha256=digest(p.model_dump(mode="json")), registry=denied
    )
    hidden = invocation_for(denied, policy=sealed)
    assert p.interpretations[0].claim.text not in hidden.request.prompt


def test_native_prompt_provides_distinct_ticker_and_security_id():
    from app.services.native_input_admission import BackendAdmissionRegistry, BackendOwnerBundle
    from app.services.unified_snapshot_contract import digest
    import json

    r, _, _, _ = synthetic_economic()
    raw = r.bundle.model_dump(mode="json")
    raw["ticker"] = "DISPLAY_ONLY"
    b = BackendOwnerBundle.model_validate(raw)
    r = BackendAdmissionRegistry(b, expected_bundle_sha256=digest(b.model_dump(mode="json")))
    inv = invocation_for(r)
    assert '"canonical_ticker":"DISPLAY_ONLY"' in inv.request.prompt
    assert (
        json.loads(inv.request.response_schema_json)["$defs"]["AcceptedV2FundamentalCoreCandidate"][
            "properties"
        ]["ticker"]["const"]
        == "DISPLAY_ONLY"
    )
    assert inv.request.invocation.security_id != "DISPLAY_ONLY"


def test_temporal_conflict_or_future_owner_period_not_admitted_by_catalog():
    from app.services.native_economic_core import _interpretation_eligible, InvocationSpec
    from app.services.native_input_admission import TimeState

    r, policy, inv, _ = synthetic_economic()
    row = policy.bundle.interpretations[0]
    spec = InvocationSpec.model_validate_json(inv._spec_json)
    reference = inv.request.reference_request
    metric = reference.context.metric_authority_envelopes[0]
    for state, value in [
        (TimeState.INVALID_CONFLICT, None),
        (TimeState.VERIFIED_METRIC_AS_OF, "2099-01-01"),
    ]:
        fields = tuple(
            t.model_copy(
                update={
                    "state": state,
                    "value": value,
                    "owner_ref": metric.owner_ref,
                    "source_artifact_sha256": metric.source_artifact_sha256,
                }
            )
            if t.field == "metric_as_of"
            else t
            for t in metric.temporal
        )
        changed = metric.model_copy(update={"temporal": fields})
        q = reference.model_copy(
            update={
                "context": reference.context.model_copy(
                    update={
                        "metric_authority_envelopes": (
                            changed,
                            *reference.context.metric_authority_envelopes[1:],
                        )
                    }
                )
            }
        )
        assert not _interpretation_eligible(row, q, spec)


@pytest.mark.parametrize(
    "observed,allowed",
    [
        ("2026-10-01", True),
        ("2026-10-01T12:00:00Z", True),
        ("2099-01-01", False),
        ("2020-01-01", False),
        ("2026-10-09/2099-01-01", False),
        ("2026-10-09garbage", False),
        ("2026-10-09T12:00:00", False),
        ("2026-02-30", False),
        ("0001-01-01T00:00:00+01:00", False),
        ("9999-12-31T23:59:59-01:00", False),
    ],
)
def test_sealed_verified_temporal_policy_through_actual_native_acceptance(observed, allowed):
    from app.services.native_input_admission import BackendAdmissionRegistry, BackendOwnerBundle
    from app.services.native_economic_core import (
        BackendEconomicPolicy,
        EconomicPolicyBundle,
        bound_reference,
    )
    from app.services.unified_snapshot_contract import digest

    r, original, _, candidate = synthetic_economic()
    body = r.bundle.model_dump(mode="json")
    for metric in body["metrics"]:
        for temporal in metric["temporal"]:
            if temporal["field"] == "metric_as_of":
                temporal.update(
                    value=observed,
                    state="VERIFIED_METRIC_AS_OF",
                    owner_ref=metric["owner_ref"],
                    source_artifact_sha256=metric["source_artifact_sha256"],
                )
    bundle = BackendOwnerBundle.model_validate(body)
    registry = BackendAdmissionRegistry(
        bundle, expected_bundle_sha256=digest(bundle.model_dump(mode="json"))
    )
    body = original.bundle.model_dump(mode="json")
    body["backend_bundle_sha256"] = digest(bundle.model_dump(mode="json"))
    for row in body["interpretations"]:
        row["evidence"] = [
            bound_reference(registry, ref).model_dump(mode="json")
            for ref in row["claim"]["evidence_refs"]
        ]
        row["temporal_rules"] = [
            dict(
                field="metric_as_of", allowed_states=["VERIFIED_METRIC_AS_OF"], maximum_age_days=30
            )
        ]
    policy = EconomicPolicyBundle.model_validate(body)
    backend = BackendEconomicPolicy(
        policy, expected_policy_sha256=digest(policy.model_dump(mode="json")), registry=registry
    )
    inv = invocation_for(registry, policy=backend)
    candidate = materialize_economic_candidate(
        candidate.model_candidate.model_dump(mode="json"), inv.request, invocation=inv
    )
    if allowed:
        assert accept_economic_candidate(candidate, inv.request, invocation=inv)
    else:
        reject(candidate, inv, "REJECT_ECONOMIC_REQUEST_SCHEMA")
