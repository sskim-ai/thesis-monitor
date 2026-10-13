"""Synthetic mechanics only, not real semantic or investment-policy approval.

Execution belongs to the parent's protective validation harness.
"""

from datetime import date
import json
from pathlib import Path

import pytest

from app.services import directional_balance_service
from app.services.economic_claim_qualification import (
    EconomicClaimProposal,
    POLICY,
    policy_sha256,
)
from app.services.native_input_admission import BackendAdmissionRegistry
from app.services.reported_economic_claim_consumer import ReportedRoleCandidate
from app.services.reviewed_balanced_synthesis import (
    CONTRACT,
    RENDERED_CLAIM,
    RULE,
    BackendReviewedSynthesisOwner,
    BackendSynthesisClaimPolicy,
    SynthesisPolicyContinuity,
    SynthesisReviewDecision,
    build_reported_synthesis_invocation,
    synthesis_review_bindings,
)
from app.services.reviewed_economic_property import (
    BackendReviewedPropertyOwner,
    EconomicReviewDecision,
)
from app.services.reviewed_narrative_risk import (
    BackendNarrativeSourceOwner,
    BackendReviewedNarrativeRiskOwner,
    NarrativeSpan,
)
from app.services.unified_snapshot_contract import digest
from tests.test_reported_fact_owner import owner_fixture
from tests.test_reviewed_narrative_risk import (
    encoded,
    reseal_source,
    reviewed_args,
    sha,
    source_fixture_args,
)


def _anchor_owner(fact_owner, source):
    review = b"SYNTHETIC_ANCHOR_REVIEW_NOT_REAL_AUTHORITY"
    proposal = b"SYNTHETIC_HISTORICAL_OPERATING_IMPROVEMENT"
    reg = fact_owner.registration
    decision = EconomicReviewDecision(
        review_event_id="synthetic-anchor-review",
        reviewer="synthetic-reviewer",
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
            "FILING_NARRATIVE", "UNSEALED_AMENDMENTS", "UNDISCLOSED_ADJUSTMENTS",
            "CAUSE", "RECURRENCE", "CURRENTNESS", "FUTURE_RISKS",
        ),
    )
    raw = decision.model_dump_json().encode()
    return BackendReviewedPropertyOwner(
        fact_owner=fact_owner,
        decision_bytes=raw,
        trusted_decision_sha256=sha(raw),
        review_bytes=review,
        trusted_review_sha256=sha(review),
        proposal_bytes=proposal,
        source_bytes=source,
        trusted_source_sha256=sha(source),
        execution_generation_id="synthetic-r17-consumer",
    )


def synthesis_owner_fixture(
    identity="UNSEEN_SYNTHESIS_US", *, market="US", security_type="common_stock",
    amount=30, mutate=None, old_qualification_sha=None,
):
    source_args, paragraphs = source_fixture_args(
        identity, market=market, security_type=security_type, amount=amount
    )
    extra = (
        b"<p>Historical product price increases supported the reported period.</p>",
        b"<p>Fixed and banded prices differ from market-priced agreements.</p>",
        b"<p>Take-or-pay commitments have performance and enforcement limitations.</p>",
        b"<p>Management durability expectations remain expectations, not facts.</p>",
        b"<p>Minimum commitments exclude some contracts and restrict supply flexibility.</p>",
    )
    html = source_args["artifacts"]["html"].replace(
        b"</body>", b"".join(extra) + b"</body>"
    )
    reseal_source(source_args, html=html)
    source = BackendNarrativeSourceOwner(**source_args)
    risk_args, risk_decision = reviewed_args(source, paragraphs)
    spans = risk_decision.spans + tuple(
        NarrativeSpan(
            category="MITIGATION",
            start_byte=html.index(raw),
            end_byte=html.index(raw) + len(raw),
            raw_sha256=sha(raw),
        )
        for raw in extra
    )
    risk_raw = risk_decision.model_copy(update={"spans": spans}).model_dump_json().encode()
    risk_args.update(decision_bytes=risk_raw, trusted_decision_sha256=sha(risk_raw))
    risk = BackendReviewedNarrativeRiskOwner(**risk_args)
    _, fact_args = owner_fixture(
        identity, market=market, security_type=security_type, current_amount=amount
    )
    anchor = _anchor_owner(source_args["fact_owner"], fact_args["artifacts"]["companyfacts"])
    bindings = synthesis_review_bindings(anchor, risk)
    names = (
        "economic_claim_qualification.py", "directional_balance_service.py",
        "native_economic_core.py", "accepted_decision_v2_runtime_service.py",
        "fundamental_holder_stance_service.py",
    )
    sources = {
        name: sha(Path(directional_balance_service.__file__).with_name(name).read_bytes())
        for name in names
    }
    current_qualification = sources["economic_claim_qualification.py"]
    if old_qualification_sha is not None:
        sources["economic_claim_qualification.py"] = old_qualification_sha
    old_policy = digest(dict(
        policy=POLICY,
        implementation=sources["economic_claim_qualification.py"],
        inherited_semantics=sources["directional_balance_service.py"],
    ))
    proposal = b"SYNTHETIC_JOINT_HISTORICAL_ROLE_PROPOSAL_NOT_REAL_AUTHORITY"
    review = encoded(dict(
        decision="BALANCED_SYNTHESIS_ROLE_ELIGIBLE",
        permission=dict(
            role="DECISIVE_REASON", interpretation_type="BALANCED_SYNTHESIS",
            polarity="MIXED", allowed_confidences=["LOW"], uncertainty="LIMITED",
            consumer="CORE", use_axis="CORE_DIRECTION",
        ),
        approved_rendered_claim=RENDERED_CLAIM,
        proposal=dict(sha256=sha(proposal)),
        policy_version=POLICY,
        policy_sha256=old_policy,
        policy_source_sha256=sources,
        source_artifacts_sha256={
            key: bindings[key] for key in (
                "anchor_source_sha256", "source_artifact_sha256",
                "anchor_review_artifact_sha256", "risk_review_artifact_sha256",
                "anchor_independent_review_sha256", "risk_independent_review_sha256",
            )
        },
        subject=dict(
            security_id=bindings["security_id"], cik=bindings["issuer_id"],
            filed=bindings["filed"], statement_date=bindings["statement_date"],
            source_cutoff=bindings["cutoff"],
        ),
        lineage=dict(
            source_generation=bindings["source_generation_id"],
            original_owner_execution=bindings["owner_execution_generation_id"],
            R17_review=bindings["anchor_review_event_id"],
            R18_review=bindings["risk_review_event_id"],
        ),
        required_span_ranges=[[s.start_byte, s.end_byte] for s in spans],
        synthetic=True,
    ))
    continuity_review = b"SYNTHETIC_GUARD_ONLY_CONTINUITY_NOT_REAL_REVIEW"
    bridge = SynthesisPolicyContinuity(
        decision="APPROVE_TECHNICAL_GUARD_ONLY_CONTINUITY",
        semantic_review_sha256=sha(review),
        semantic_policy_sha256=old_policy,
        current_policy_sha256=policy_sha256(),
        semantic_qualification_source_sha256=sources["economic_claim_qualification.py"],
        current_qualification_source_sha256=current_qualification,
        independent_review_sha256=sha(continuity_review),
    ).model_dump_json().encode()
    decision = SynthesisReviewDecision(
        **bindings,
        review_event_id="synthetic-synthesis-review",
        reviewer="synthetic-reviewer",
        mandate="R19_USER_AUTHORIZED_EXISTING_POLICY_QUALIFICATION",
        decision="BALANCED_SYNTHESIS_ROLE_ELIGIBLE",
        proposal_sha256=sha(proposal),
        independent_review_sha256=sha(review),
        semantic_policy_sha256=old_policy,
        policy_sha256=policy_sha256(),
        policy_continuity_sha256=sha(bridge),
    )
    raw = decision.model_dump_json().encode()
    args = dict(
        anchor_owner=anchor,
        risk_owner=risk,
        decision_bytes=raw,
        trusted_decision_sha256=sha(raw),
        review_bytes=review,
        trusted_review_sha256=sha(review),
        policy_continuity_bytes=bridge,
        trusted_policy_continuity_sha256=sha(bridge),
        continuity_review_bytes=continuity_review,
        trusted_continuity_review_sha256=sha(continuity_review),
        proposal_bytes=proposal,
        execution_generation_id="synthetic-r19-consumer",
    )
    if mutate:
        mutate(args, decision)
    return BackendReviewedSynthesisOwner(**args), args


def synthesis_fixture(identity="UNSEEN_SYNTHESIS_US", **kwargs):
    owner, _ = synthesis_owner_fixture(identity, **kwargs)
    inv = build_reported_synthesis_invocation(
        owner, invocation_id="synthetic-synthesis-role", assessment_as_of=date(2026, 10, 12)
    )
    scope = inv.request.invocation
    proposal = EconomicClaimProposal(
        claim_id="synthetic-synthesis",
        security_id=scope.security_id,
        generation_id=scope.generation_id,
        source_generation_id=scope.source_generation_id,
        requested_role="DECISIVE_REASON",
        interpretation_type="BALANCED_SYNTHESIS",
        polarity="MIXED",
        uncertainty="LIMITED",
        support_refs=tuple(s.support_ref for s in inv._policy.bundle.supports),
        policy_sha256=policy_sha256(),
    )
    return owner, inv, ReportedRoleCandidate(proposal=proposal, confidence="LOW")


invocation_fixture = synthesis_fixture


def _replace_decision(args, decision, **changes):
    raw = decision.model_copy(update=changes).model_dump_json().encode()
    args.update(decision_bytes=raw, trusted_decision_sha256=sha(raw))


@pytest.mark.parametrize("identity,market,kind", [
    ("UNSEEN_SYNTHESIS_US", "US", "common_stock"),
    ("UNSEEN_SYNTHESIS_KR", "KR", "common_stock"),
    ("UNSEEN_SYNTHESIS_ADS", "US", "depositary_receipt"),
    ("UNSEEN_SYNTHESIS_FINANCIAL", "US", "common_stock"),
    ("UNSEEN_SYNTHESIS_CYCLICAL", "US", "common_stock"),
    ("UNSEEN_SYNTHESIS_INCOMPLETE", "US", "common_stock"),
])
def test_generic_joint_role_preserves_all_original_context(identity, market, kind):
    owner, inv, candidate = synthesis_fixture(identity, market=market, security_type=kind)
    a = owner.admission
    assert type(inv._policy) is BackendSynthesisClaimPolicy
    assert a.contract == CONTRACT and a.review.rule_version == RULE
    assert owner._anchor_owner._owner is owner._risk_owner._owner
    assert a.review.facts == owner._owner.facts
    assert len(inv._registry.bundle.metrics) == 4
    for metric, fact in zip(inv._registry.bundle.metrics, a.review.facts, strict=True):
        assert metric.value == fact.value
        assert metric.input_sha256 == fact.occurrence_sha256
        assert metric.owner_contract == CONTRACT
        assert metric.owner_receipt_sha256 == a.admission_sha256
    claim, receipt, supports = inv._policy.qualify(
        candidate.proposal, request=inv.request, invocation=inv
    )
    assert claim.text == RENDERED_CLAIM and len(claim.text) <= 420
    assert receipt.role == "DECISIVE_REASON"
    assert not receipt.accepted_model_judgment
    assert not receipt.objective_investment_truth_proven
    assert tuple(s.property for s in supports) == (
        "BUSINESS_ANCHOR", "BUSINESS_RISK", "COUNTEREVIDENCE"
    )
    assert {s.economic_lineage for s in supports} == {a.review.anchor_source_sha256}
    assert all(s.allowed_confidences == ("LOW",) for s in supports)
    assert all(not s.independent_of_supports for s in supports)
    narrative = inv._policy.narrative_packet_binding()
    assert len(narrative["narrative_context"]) == 10
    for excerpt, span in zip(narrative["narrative_context"], a.review.spans, strict=True):
        assert excerpt == owner._source_owner.excerpt(span)
        assert excerpt["raw_sha256"] == span.raw_sha256
    text = " ".join(row["text"] for row in narrative["narrative_context"])
    assert "after June 30" in text and "future revenue" in text
    assert "expected" not in claim.text and "HOLD" not in claim.text
    joint = inv._policy.synthesis_packet_binding()
    assert joint["anchor_admission_sha256"] == a.anchor_property.admission_sha256
    assert joint["risk_admission_sha256"] == a.risk_property.admission_sha256
    assert joint["anchor_review_sha256"] == a.anchor_property.review_artifact_sha256
    assert joint["risk_review_sha256"] == a.risk_property.review_artifact_sha256
    assert not a.review.complete_core_authorized and not a.review.grants_holder_stance


@pytest.mark.parametrize("field", [
    "decision_bytes", "review_bytes", "policy_continuity_bytes",
    "continuity_review_bytes", "proposal_bytes",
])
def test_unpinned_byte_changes_cannot_replace_review_store(field):
    def mutate(args, _):
        args[field] += b" "
    with pytest.raises(ValueError):
        synthesis_owner_fixture(mutate=mutate)


def test_caller_reviewer_label_is_not_backend_review_authority():
    def mutate(args, decision):
        args["decision_bytes"] = decision.model_copy(
            update={"reviewer": "caller-approved"}
        ).model_dump_json().encode()
        assert sha(args["decision_bytes"]) != args["trusted_decision_sha256"]

    with pytest.raises(ValueError, match="ANCHOR_MISMATCH"):
        synthesis_owner_fixture(mutate=mutate)


@pytest.mark.parametrize("field,value", [
    ("source_generation_id", "other-generation"),
    ("source_kind", "REAL_SEALED_SOURCE"),
    ("anchor_review_artifact_sha256", "a" * 64),
    ("risk_review_artifact_sha256", "a" * 64),
    ("source_owner_sha256", "a" * 64),
    ("narrative_source_binding_sha256", "a" * 64),
    ("anchor_execution_generation_id", "other-execution"),
    ("policy_sha256", "a" * 64),
    ("grants_holder_stance", True),
    ("assigns_balance_bucket", True),
])
def test_resealed_decision_still_requires_exact_source_and_scope(field, value):
    with pytest.raises(ValueError):
        synthesis_owner_fixture(
            mutate=lambda args, d: _replace_decision(args, d, **{field: value})
        )


def test_stable_decision_does_not_transfer_live_capabilities():
    first, first_args = synthesis_owner_fixture()
    second, second_args = synthesis_owner_fixture()
    assert first_args["decision_bytes"] == second_args["decision_bytes"]
    assert first.admission.admission_sha256 != second.admission.admission_sha256
    recreated = BackendReviewedSynthesisOwner(**(
        second_args | dict(
            decision_bytes=first_args["decision_bytes"],
            trusted_decision_sha256=first_args["trusted_decision_sha256"],
        )
    ))
    assert recreated.resolve(recreated.admission) == recreated.admission
    with pytest.raises(ValueError, match="UNISSUED"):
        second.resolve(first.admission)
    with pytest.raises(ValueError, match="SAME_ORIGINAL_LIVE_FACT_OWNER"):
        BackendReviewedSynthesisOwner(**(first_args | dict(risk_owner=second._risk_owner)))
    for old in (first.admission.anchor_property, first.admission.risk_property):
        with pytest.raises(ValueError, match="UNISSUED"):
            first.resolve(old)


def test_exact_span_set_and_bytes_are_live_requirements():
    with pytest.raises(ValueError):
        synthesis_owner_fixture(
            mutate=lambda args, d: _replace_decision(args, d, spans=d.spans[:-1])
        )
    owner, inv, candidate = synthesis_fixture()
    owner._source_owner._raw += b"altered"
    with pytest.raises(ValueError):
        inv._policy.qualify(candidate.proposal, request=inv.request, invocation=inv)
    assert not inv._policy._issued


@pytest.mark.parametrize("changes", [
    dict(requested_role="HOLDER_REASON", interpretation_type="HOLDER_REASSESSMENT"),
    dict(requested_role="BUY_DRIVER", interpretation_type="BUSINESS_SUPPORT"),
    dict(asserts_causality=True),
    dict(asserts_recurrence=True),
    dict(asserts_independent_corroboration=True),
    dict(use_axis="OVERALL_DIRECTION"),
    dict(uncertainty="QUALIFIED"),
    dict(asserts_currentness=True),
    dict(decision="HOLD"),
])
def test_only_reviewed_role_meaning_can_qualify(changes):
    _, inv, candidate = synthesis_fixture()
    changed = candidate.proposal.model_dump(mode="json") | changes
    with pytest.raises(ValueError):
        proposal = EconomicClaimProposal.model_validate(changed)
        inv._policy.qualify(proposal, request=inv.request, invocation=inv)
    assert not inv._policy._issued


def test_even_exact_numeric_claims_and_missing_counterevidence_are_denied():
    _, inv, candidate = synthesis_fixture()
    metric = inv._registry.bundle.metrics[0]
    for change in (
        dict(numeric_assertions=[dict(evidence_ref=metric.metric_ref, value=metric.value)]),
        dict(support_refs=candidate.proposal.support_refs[:-1]),
    ):
        proposal = EconomicClaimProposal.model_validate(
            candidate.proposal.model_dump(mode="json") | change
        )
        with pytest.raises(ValueError):
            inv._policy.qualify(proposal, request=inv.request, invocation=inv)
    assert not inv._policy._issued


def test_rehashed_metric_projection_and_support_changes_cannot_broaden_review():
    _, inv, candidate = synthesis_fixture()
    bundle = inv._registry.bundle
    changed = bundle.model_copy(update={"metrics": (
        bundle.metrics[0].model_copy(update={"value": bundle.metrics[0].value + 1}),
        *bundle.metrics[1:],
    )})
    registry = BackendAdmissionRegistry(
        changed, expected_bundle_sha256=digest(changed.model_dump(mode="json"))
    )
    with pytest.raises(ValueError, match="EXACT_FACT_PROJECTION"):
        inv._policy.verify_backend(registry)
    policy = inv._policy.bundle
    inv._policy._json = policy.model_copy(update={
        "supports": policy.supports[:-1],
    }).model_dump_json()
    with pytest.raises(ValueError):
        inv._policy.qualify(candidate.proposal, request=inv.request, invocation=inv)
    assert not inv._policy._issued


@pytest.mark.parametrize("which", ["synthesis", "anchor", "risk", "source", "fact"])
def test_every_original_owner_lifetime_remains_required(which):
    owner, inv, candidate = synthesis_fixture()
    if which == "fact":
        owner._owner._admitted.clear()
    else:
        target = {
            "synthesis": owner, "anchor": owner._anchor_owner,
            "risk": owner._risk_owner, "source": owner._source_owner,
        }[which]
        target.revoke(target.admission)
    with pytest.raises(ValueError):
        inv._policy.qualify(candidate.proposal, request=inv.request, invocation=inv)
    with pytest.raises(ValueError):
        inv._policy.narrative_packet_binding()
    with pytest.raises(ValueError):
        inv._policy.synthesis_packet_binding()
    assert not inv._policy._issued


def test_new_generation_and_review_cutoff_are_required():
    owner, args = synthesis_owner_fixture()
    for generation in (
        owner.admission.review.source_generation_id,
        owner.admission.review.owner_execution_generation_id,
        owner.admission.anchor_property.execution_generation_id,
        owner.admission.risk_property.execution_generation_id,
    ):
        with pytest.raises(ValueError, match="NEW_REVIEW_CONSUMER_GENERATION"):
            BackendReviewedSynthesisOwner(**(args | dict(execution_generation_id=generation)))
    with pytest.raises(ValueError, match="NOT_AVAILABLE_AT_ASSESSMENT"):
        build_reported_synthesis_invocation(
            owner, invocation_id="too-early", assessment_as_of=date(2026, 8, 31)
        )


def test_explicit_policy_bridge_preserves_original_semantic_review():
    owner, args = synthesis_owner_fixture(old_qualification_sha="b" * 64)
    original = json.loads(args["review_bytes"])
    assert original["policy_sha256"] != policy_sha256()
    assert owner.admission.review.semantic_policy_sha256 == original["policy_sha256"]
    assert owner.admission.review.policy_sha256 == policy_sha256()
    bridge = SynthesisPolicyContinuity.model_validate_json(args["policy_continuity_bytes"])
    for field in (
        "semantic_review_sha256", "semantic_policy_sha256", "current_policy_sha256",
        "semantic_qualification_source_sha256", "current_qualification_source_sha256",
        "independent_review_sha256",
    ):
        raw = bridge.model_copy(update={field: "a" * 64}).model_dump_json().encode()
        changed = args | dict(
            policy_continuity_bytes=raw, trusted_policy_continuity_sha256=sha(raw)
        )
        _replace_decision(changed, owner.admission.review, policy_continuity_sha256=sha(raw))
        with pytest.raises(ValueError, match="CONTINUITY"):
            BackendReviewedSynthesisOwner(**changed)


@pytest.mark.parametrize("field", [
    "permission", "approved_rendered_claim", "source_artifacts_sha256",
    "subject", "required_span_ranges",
])
def test_pinned_bridge_cannot_change_original_review_scope_or_sources(field):
    owner, args = synthesis_owner_fixture()
    review = json.loads(args["review_bytes"])
    review[field] = {} if isinstance(review[field], dict) else []
    raw = encoded(review)
    bridge = SynthesisPolicyContinuity.model_validate_json(args["policy_continuity_bytes"])
    bridge_raw = bridge.model_copy(update={
        "semantic_review_sha256": sha(raw),
    }).model_dump_json().encode()
    args.update(
        review_bytes=raw, trusted_review_sha256=sha(raw),
        policy_continuity_bytes=bridge_raw, trusted_policy_continuity_sha256=sha(bridge_raw),
    )
    _replace_decision(
        args, owner.admission.review,
        independent_review_sha256=sha(raw), policy_continuity_sha256=sha(bridge_raw),
    )
    with pytest.raises(ValueError, match="SEMANTIC_REVIEW"):
        BackendReviewedSynthesisOwner(**args)
