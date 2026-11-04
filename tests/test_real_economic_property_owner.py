"""Synthetic producer-boundary controls; no real issuer or model qualification."""

import hashlib
import json

import pytest

from app.services.real_economic_property_owner import (
    BackendRealEconomicPropertyOwner,
    PropertyProposal,
    policy_sha256,
)
from app.services.reported_fact_owner import BackendReportedFactOwner
from app.services.economic_interpretation_policy import ReportedStatementInput
from app.services.sec_financial_snapshot_service import _companyfacts_snapshots
from app.services.sec_business_field_quality_service import sha
from app.services.native_owner_session import (
    BackendOwnerParent,
    ParentAdmissionManifest,
    ParentInvocationBinding,
)
from app.services.unified_snapshot_contract import digest
from tests.test_reported_fact_owner import owner_fixture
from tests.test_reported_context_consumer import context_invocation


def parent_for(inv):
    q = inv.request.invocation
    scope = dict(
        run_id="property-review-offline",
        market=inv._registry.bundle.market,
        generation_id=q.generation_id,
        source_generation_id=q.source_generation_id,
        snapshot_sha256=digest(
            ["EXPLICIT_TEST_SOURCE_BINDING", inv._registry.bundle.source_envelope_sha256]
        ),
    )
    manifest = ParentAdmissionManifest(
        **scope,
        invocations=(
            ParentInvocationBinding(
                invocation_id=q.invocation_id,
                security_id=q.security_id,
                request_sha256=q.request_sha256,
                admission_bundle_sha256=digest(inv._registry.bundle.model_dump(mode="json")),
                source_envelope_sha256=inv._registry.bundle.source_envelope_sha256,
            ),
        ),
    )
    parent = BackendOwnerParent(
        authority_native_v2=True,
        **scope,
        admission_manifest=manifest,
        expected_manifest_sha256=digest(manifest.model_dump(mode="json")),
    )
    parent.register(inv)
    return parent


def property_fixture(
    identity="UNSEEN_PROPERTY_US", *, market="US", security_type="common_stock", amount=30
):
    _, args = owner_fixture(
        identity, market=market, security_type=security_type, current_amount=amount
    )
    raw = json.loads(args["artifacts"]["companyfacts"])
    raw["facts"]["us-gaap"]["OperatingIncomeLoss"]["description"] = (
        "The net result for the period of deducting operating expenses from operating revenues."
    )
    body = json.dumps(raw).encode()
    artifacts = dict(args["artifacts"], companyfacts=body)
    acquisition = json.loads(artifacts["companyfacts_receipt"])
    acquisition["raw_sha256"] = hashlib.sha256(body).hexdigest()
    artifacts["companyfacts_receipt"] = json.dumps(acquisition).encode()
    prior, current = sorted(
        _companyfacts_snapshots(raw, identity), key=lambda x: x.financial_period_end
    )
    statements = [
        ReportedStatementInput(**{k: getattr(row, k) for k in ReportedStatementInput.model_fields})
        for row in (current, prior)
    ]
    comparison = args["comparison"].model_copy(
        update=dict(
            source_artifact_sha256=(sha(raw),), formal=statements[0], comparison=statements[1]
        )
    )
    owner = BackendReportedFactOwner(
        **(
            args
            | dict(
                artifacts=artifacts,
                comparison=comparison,
                trusted_artifact_sha256={
                    k: hashlib.sha256(v).hexdigest() for k, v in artifacts.items()
                },
            )
        )
    )
    inv, _, grants, _ = context_invocation(owner, market=market.lower())
    parent = parent_for(inv)
    producer = BackendRealEconomicPropertyOwner(
        fact_owner=owner,
        companyfacts=body,
        trusted_source_sha256=hashlib.sha256(body).hexdigest(),
        parent=parent,
        invocation_id=inv.request.invocation.invocation_id,
        provenance="SYNTHETIC_TEST_SOURCE",
    )
    result = next(g.comparison for g in grants if g.facts[0].field == "operating_income")
    q = inv.request.invocation
    proposal = PropertyProposal(
        security_id=q.security_id,
        issuer_id=owner.registration.issuer_id,
        source_generation_id=q.source_generation_id,
        owner_execution_generation_id=owner.registration.execution_generation_id,
        execution_generation_id=q.generation_id,
        invocation_id=q.invocation_id,
        comparison_sha256=result.interpretation_sha256,
        property_type="REPORTED_OPERATING_COMPARISON",
        policy_sha256=policy_sha256(),
    )
    return producer, proposal, result, parent, inv, owner, body


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
def test_same_semantic_producer_without_investment_promotion(identity, market, kind):
    p, proposed, result, parent, inv, *_ = property_fixture(
        identity, market=market, security_type=kind
    )
    review = p.review(proposed, result)
    assert review.disposition == "BOUNDED_DESCRIPTIVE_PROPERTY_SUPPORTED"
    assert review.economic_materiality == "NOT_ESTABLISHED_BY_SCALE_OR_GROWTH"
    admission = p.admit(review)
    assert p.admit(review) == admission
    assert not admission.economic_role_eligible and not admission.accepted_economic_output
    assert (
        p.resolve(
            admission,
            parent=parent,
            invocation_id=proposed.invocation_id,
            consumer="CORE",
            use_axis="CORE_CONTEXT",
        )
        == admission
    )
    receipt = parent.complete(parent.begin(proposed.invocation_id))
    assert parent.context_prompt(proposed.invocation_id, receipt) == inv.request.prompt
    assert not parent._registry.attempt_states()


@pytest.mark.parametrize(
    "field,value",
    [
        ("security_id", "wrong"),
        ("issuer_id", "9999"),
        ("source_generation_id", "wrong"),
        ("owner_execution_generation_id", "wrong"),
        ("execution_generation_id", "wrong"),
        ("invocation_id", "wrong"),
        ("comparison_sha256", "a" * 64),
        ("policy_sha256", "a" * 64),
        ("consumer", "HOLDER"),
        ("use_axis", "OVERALL_DIRECTION"),
    ],
)
def test_proposal_identity_axis_before_admission(field, value):
    p, proposed, result, *_ = property_fixture()
    with pytest.raises(ValueError):
        p.review(proposed.model_copy(update={field: value}), result)
    assert p.admitted_count() == 0


@pytest.mark.parametrize(
    "change,gap",
    [
        (
            {
                "property_type": "BUSINESS_ANCHOR",
                "requested_role": "BUY_DRIVER",
                "use_axis": "CORE_DIRECTION",
            },
            "FACT_USE_GRANT_GAP",
        ),
        ({"asserts_causality": True}, "CAUSAL_RELEVANCE_GAP"),
        ({"asserts_recurrence": True}, "RECURRENCE_EVIDENCE_GAP"),
        ({"asserts_independence": True}, "CORRELATED_SOURCE_NOT_INDEPENDENT_SUPPORT"),
    ],
)
def test_no_semantic_approval_from_authentic_fact_or_growth(change, gap):
    p, proposed, result, *_ = property_fixture(amount=9000)
    review = p.review(proposed.model_copy(update=change), result)
    assert gap in review.blocking_gates
    with pytest.raises(ValueError, match="EVIDENCE_OR_AUTHORITY_GAP"):
        p.admit(review)
    assert p.admitted_count() == 0
    assert p.admit(p.review(proposed, result))


@pytest.mark.parametrize(
    "field,value",
    [
        ("review_id", "forged"),
        ("review_sha256", "a" * 64),
        ("reviewer_authority", "CALLER_APPROVED"),
        ("disposition", "BOUNDED_DESCRIPTIVE_PROPERTY_SUPPORTED"),
        ("blocking_gates", ()),
    ],
)
def test_rehashed_labels_or_reviewer_do_not_approve_role(field, value):
    p, proposed, result, *_ = property_fixture()
    review = p.review(
        proposed.model_copy(
            update=dict(property_type="BUSINESS_ANCHOR", requested_role="BUY_DRIVER")
        ),
        result,
    )
    changed = review.model_copy(update={field: value})
    with pytest.raises(ValueError):
        p.admit(changed)
    assert p.admitted_count() == 0


@pytest.mark.parametrize(
    "axis",
    [
        "CORE_DIRECTION",
        "CORE_VALUATION_CONTEXT",
        "OVERALL_DIRECTION",
        "HOLDER_CONTEXT",
        "NEWBUYER_DIRECTION",
    ],
)
def test_property_context_cannot_authorize_economic_use(axis):
    p, proposed, result, parent, *_ = property_fixture()
    admission = p.admit(p.review(proposed, result))
    with pytest.raises(ValueError, match="ECONOMIC_USE_NOT_AUTHORIZED"):
        p.resolve(
            admission,
            parent=parent,
            invocation_id=proposed.invocation_id,
            consumer="CORE",
            use_axis=axis,
        )


def test_receipt_provenance_registry_and_parent_lifetime():
    p, proposed, result, parent, inv, *_ = property_fixture()
    admission = p.admit(p.review(proposed, result))
    args = dict(
        parent=parent,
        invocation_id=proposed.invocation_id,
        consumer="CORE",
        use_axis="CORE_CONTEXT",
    )
    for field, value in (
        ("provenance", "SEALED_SOURCE_TECHNICAL_REVIEW"),
        ("admission_id", "unissued"),
        ("admission_sha256", "a" * 64),
    ):
        with pytest.raises(ValueError, match="UNISSUED_OR_CHANGED"):
            p.resolve(admission.model_copy(update={field: value}), **args)
    other, *_ = property_fixture()
    with pytest.raises(ValueError):
        other.resolve(admission, **args)
    with pytest.raises(ValueError, match="WRONG_PARENT_OR_INVOCATION"):
        p.resolve(admission, **(args | dict(parent=object())))
    p.revoke(admission)
    with pytest.raises(ValueError, match="REVOKED"):
        p.resolve(admission, **args)
    with pytest.raises(ValueError, match="REVOKED"):
        p.admit(admission.review)
    replacement = p.admit(p.review(proposed, result))
    assert p.resolve(replacement, **args)
    parent.close()
    with pytest.raises(ValueError, match="PARENT"):
        p.resolve(replacement, **args)
