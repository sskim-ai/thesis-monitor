"""Explicit synthetic method/interpretation authority; never real issuer receipts."""

from app.services.native_input_admission import UseAxis
from app.services.native_authority_core import build_context
from app.services.native_economic_core import (
    BackendEconomicPolicy,
    EconomicPolicyBundle,
    EconomicInterpretation,
    InvocationSpec,
    bound_reference,
    materialize_economic_candidate,
)
from app.services.accepted_decision_v2_runtime_service import (
    build_accepted_v2_economic_core_invocation,
    AcceptedV2EvidenceOwnership,
    AcceptedV2FundamentalCoreCandidate,
)
from app.services.expectation_valuation_interaction_service import ExpectationValuationInteraction
from app.services.unified_snapshot_contract import digest
from tests.native_authority_fixtures import synthetic_registry, native_input


def invocation_for(registry, *, refs=None, consumer="CORE", policy=None):
    context = build_context(
        admission_input=native_input(registry, refs),
        registry=registry,
        request_id="offline-economic-invocation",
    )
    axes = tuple(a for a in UseAxis if a.value.split("_", 1)[0] == consumer)
    spec = InvocationSpec(
        invocation_id="offline-economic-invocation",
        security_id=registry.bundle.security_id,
        generation_id=registry.bundle.generation_id,
        source_generation_id=registry.bundle.source_generation_id,
        assessment_as_of="2026-10-09",
        intended_consumer=consumer,
        allowed_use_axes=axes,
        forbidden_use_axes=tuple(a for a in UseAxis if a not in axes),
    )
    return build_accepted_v2_economic_core_invocation(
        context=context,
        admission_registry=registry,
        invocation_spec=spec,
        economic_policy=policy,
        authority_native_v2=True,
    )


def synthetic_economic(
    identity="UNSEEN_US_NATIVE_ECONOMIC", *, market="us", security_type="common_stock"
):
    r = synthetic_registry(identity, market=market, security_type=security_type)
    a, b = [m.metric_ref for m in r.bundle.metrics]
    claims = [
        (
            "BUY_DRIVER",
            "POSITIVE",
            "Qualified operating improvement supports the business case.",
            a,
        ),
        ("SELL_DRIVER", "NEGATIVE", "Qualified execution risk limits the business case.", b),
        ("DECISIVE_REASON", "MIXED", "Business improvement and execution risk remain balanced.", a),
        (
            "HOLDER_REASON",
            "UNCERTAIN",
            "Holding rationale requires reassessment of execution risk.",
            b,
        ),
    ]
    rows = tuple(
        EconomicInterpretation(
            interpretation_ref=f"synthetic-interpretation:{n}",
            role=role,
            polarity=polarity,
            uncertainty="LIMITED",
            claim=dict(text=text, evidence_refs=[ref]),
            evidence=(bound_reference(r, ref),),
            interpretation_owner_ref="SYNTHETIC_TEST_INTERPRETATION_OWNER",
            interpretation_receipt_sha256=digest(
                ["TEST_ONLY_NOT_CORPORATE_EVIDENCE", n, text, ref]
            ),
            allowed_decisions=("HOLD",),
            allowed_holder_stances=("REVIEW",),
            allowed_confidences=("MEDIUM",),
            temporal_rules=({"field": "metric_as_of", "allowed_states": ["UNKNOWN_NOT_PROVIDED"]},),
        )
        for n, (role, polarity, text, ref) in enumerate(claims)
    )
    ownership = AcceptedV2EvidenceOwnership(
        ticker=identity,
        core_ref_ids=(a, b),
        timing_ref_ids=(),
        expectation_valuation=ExpectationValuationInteraction(
            ticker=identity,
            classification="UNKNOWN",
            expectation_refs=(),
            valuation_refs=(),
            independent_expectation_basis_refs=(),
            shared_underlying_refs=(),
            reason="SYNTHETIC_NO_EXPECTATION_VALUATION_ANCHORS",
        ),
    )
    policy = EconomicPolicyBundle(
        security_id=r.bundle.security_id,
        generation_id=r.bundle.generation_id,
        source_generation_id=r.bundle.source_generation_id,
        backend_bundle_sha256=digest(r.bundle.model_dump(mode="json")),
        policy_owner="SYNTHETIC_TEST_OWNER",
        approval_version="SYNTHETIC_V1",
        ownership=ownership,
        interpretations=rows,
    )
    backend = BackendEconomicPolicy(
        policy, expected_policy_sha256=digest(policy.model_dump(mode="json")), registry=r
    )
    inv = invocation_for(r, policy=backend)
    core = AcceptedV2FundamentalCoreCandidate(
        ticker=identity,
        decision="HOLD",
        directional_balance=dict(buy=5, sell=5),
        buy_drivers=(rows[0].claim,),
        sell_drivers=(rows[1].claim,),
        balance_summary=rows[0].claim.text + " / " + rows[1].claim.text,
        confidence="MEDIUM",
        decisive_reason=rows[2].claim,
        holder_axis=dict(stance="REVIEW", reason=rows[3].claim),
    )
    model = dict(
        candidate=core.model_dump(mode="json"),
        interpretation_refs=[x.interpretation_ref for x in rows],
    )
    output = materialize_economic_candidate(model, inv.request, invocation=inv)
    return r, backend, inv, output
