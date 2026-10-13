"""Pinned joint historical review, not a stance or complete-Core decision.

Only trusted backend composition supplies the review-store bytes and anchors.
Stable source/review commitments allow preseal across live owner lifetimes;
they are not capabilities. Admission receipts bind the exact live owners.
"""

from __future__ import annotations

from datetime import date
import hashlib
import json
from pathlib import Path
import secrets
from threading import RLock
from typing import Literal

from pydantic import Field, model_validator

from app.services.economic_claim_qualification import (
    BackendQualifiedEconomicPolicy,
    ClaimPolicyBundle,
    EconomicClaimProposal,
    EconomicSupport,
    POLICY,
    policy_sha256,
)
from app.services.native_input_admission import Closed, Identity, SHA
from app.services.reported_fact_owner import BackendReportedFactOwner, ReportedFact
from app.services.reviewed_economic_property import (
    BackendReviewedPropertyOwner,
    ReviewedPropertyAdmission,
)
from app.services.reviewed_narrative_risk import (
    BackendReviewedNarrativeRiskOwner,
    NarrativeSpan,
    ReviewedNarrativeRiskAdmission,
    _project_bundle as _risk_project_bundle,
    _scale_ownership,
    _support_rows as _risk_support_rows,
)
from app.services.unified_snapshot_contract import digest

CONTRACT = "real-balanced-synthesis-property-owner-v1"
RULE = "reviewed-historical-balanced-synthesis-v1"
RENDERED_CLAIM = (
    "The admitted business anchor and risk require balanced synthesis. "
    "Uncertainty: limited."
)


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


class SynthesisPolicyContinuity(Closed):
    contract: Literal["reviewed-synthesis-policy-continuity-v1"] = (
        "reviewed-synthesis-policy-continuity-v1"
    )
    decision: Literal["APPROVE_TECHNICAL_GUARD_ONLY_CONTINUITY"]
    semantic_review_sha256: SHA
    semantic_policy_sha256: SHA
    current_policy_sha256: SHA
    semantic_qualification_source_sha256: SHA
    current_qualification_source_sha256: SHA
    independent_review_sha256: SHA
    economic_semantics_unchanged: Literal[True] = True
    holder_authority: Literal[False] = False


class SynthesisReviewDecision(Closed):
    contract: Literal["independent-balanced-synthesis-review-v1"] = (
        "independent-balanced-synthesis-review-v1"
    )
    review_event_id: Identity
    reviewer: Identity
    mandate: Literal["R19_USER_AUTHORIZED_EXISTING_POLICY_QUALIFICATION"]
    rule_version: Literal["reviewed-historical-balanced-synthesis-v1"] = RULE
    decision: Literal["BALANCED_SYNTHESIS_ROLE_ELIGIBLE"]
    proposal_sha256: SHA
    independent_review_sha256: SHA
    semantic_policy_sha256: SHA
    policy_sha256: SHA
    policy_continuity_sha256: SHA
    source_kind: Literal["REAL_SEALED_SOURCE", "SYNTHETIC_REVIEW_FIXTURE"]
    security_id: Identity
    issuer_id: Identity
    source_generation_id: Identity
    owner_execution_generation_id: Identity
    source_owner_sha256: SHA
    anchor_review_artifact_sha256: SHA
    risk_review_artifact_sha256: SHA
    anchor_independent_review_sha256: SHA
    risk_independent_review_sha256: SHA
    anchor_review_event_id: Identity
    risk_review_event_id: Identity
    anchor_execution_generation_id: Identity
    risk_execution_generation_id: Identity
    anchor_source_sha256: SHA
    source_artifact_sha256: SHA
    narrative_source_binding_sha256: SHA
    facts: tuple[ReportedFact, ...] = Field(min_length=4, max_length=4)
    spans: tuple[NarrativeSpan, ...] = Field(min_length=3, max_length=12)
    filed: date
    statement_date: date
    cutoff: date
    permitted_role: Literal["DECISIVE_REASON"] = "DECISIVE_REASON"
    interpretation_type: Literal["BALANCED_SYNTHESIS"] = "BALANCED_SYNTHESIS"
    polarity: Literal["MIXED"] = "MIXED"
    consumer: Literal["CORE"] = "CORE"
    use_axis: Literal["CORE_DIRECTION"] = "CORE_DIRECTION"
    allowed_confidences: tuple[Literal["LOW"], ...] = ("LOW",)
    uncertainty: Literal["LIMITED"] = "LIMITED"
    counterevidence_scope: Literal[
        "EXACT_ANCHOR_AND_ALL_RISK_MITIGANT_TEMPORAL_SPANS"
    ] = "EXACT_ANCHOR_AND_ALL_RISK_MITIGANT_TEMPORAL_SPANS"
    temporal_scope: Literal["HISTORICAL_REPORTED_PERIOD_AND_DISCLOSED_SUBSEQUENT_EVENTS"] = (
        "HISTORICAL_REPORTED_PERIOD_AND_DISCLOSED_SUBSEQUENT_EVENTS"
    )
    economic_independence: Literal["COMMON_ISSUER_LINEAGE_NOT_INDEPENDENT_CORROBORATION"] = (
        "COMMON_ISSUER_LINEAGE_NOT_INDEPENDENT_CORROBORATION"
    )
    asserts_realization: Literal[False] = False
    asserts_causality: Literal[False] = False
    asserts_recurrence: Literal[False] = False
    asserts_independence: Literal[False] = False
    asserts_currentness: Literal[False] = False
    asserts_forecast: Literal[False] = False
    asserts_stance: Literal[False] = False
    assigns_balance_bucket: Literal[False] = False
    grants_holder_stance: Literal[False] = False
    accepted_abstention: Literal[False] = False
    complete_core_authorized: Literal[False] = False

    @model_validator(mode="after")
    def bounded_joint_review(self):
        if (
            self.allowed_confidences != ("LOW",)
            or len({f.model_dump_json() for f in self.facts}) != 4
            or {s.category for s in self.spans} != {"RISK", "MECHANISM", "MITIGATION"}
            or len({(s.start_byte, s.end_byte) for s in self.spans}) != len(self.spans)
            or not self.statement_date <= self.filed <= self.cutoff
        ):
            raise ValueError("SYNTHESIS_EXACT_SOURCES_AND_LIMITS_REQUIRED")
        return self


class ReviewedSynthesisAdmission(Closed):
    contract: Literal["real-balanced-synthesis-property-owner-v1"] = CONTRACT
    admission_id: Identity
    review: SynthesisReviewDecision
    review_artifact_sha256: SHA
    anchor_property: ReviewedPropertyAdmission
    risk_property: ReviewedNarrativeRiskAdmission
    source_owner_sha256: SHA
    execution_generation_id: Identity
    lineage: Literal["NEW_JOINT_REVIEW_REFERENCES_UNCHANGED_ANCHOR_RISK_AND_FACT_OWNERS"] = (
        "NEW_JOINT_REVIEW_REFERENCES_UNCHANGED_ANCHOR_RISK_AND_FACT_OWNERS"
    )
    admission_sha256: SHA


def synthesis_review_bindings(anchor_owner, risk_owner):
    """Stable preseal inputs, never an approval or live admission receipt."""
    if (
        type(anchor_owner) is not BackendReviewedPropertyOwner
        or type(risk_owner) is not BackendReviewedNarrativeRiskOwner
    ):
        raise ValueError("SYNTHESIS_EXACT_LIVE_REVIEWED_OWNERS_REQUIRED")
    anchor = anchor_owner.resolve(anchor_owner.admission)
    risk = risk_owner.resolve(risk_owner.admission)
    if (
        type(anchor_owner._owner) is not BackendReportedFactOwner
        or anchor_owner._owner is not risk_owner._owner
        or risk_owner._source_owner._owner is not anchor_owner._owner
    ):
        raise ValueError("SYNTHESIS_SAME_ORIGINAL_LIVE_FACT_OWNER_REQUIRED")
    reg = anchor_owner._owner.registration
    a, r = anchor.review, risk.review
    identity = (
        reg.security_id,
        reg.issuer_id,
        reg.source_generation_id,
        reg.execution_generation_id,
    )
    for review in (a, r):
        if (
            review.security_id,
            review.issuer_id,
            review.source_generation_id,
            review.owner_execution_generation_id,
        ) != identity:
            raise ValueError("SYNTHESIS_ORIGINAL_SOURCE_IDENTITY_MISMATCH")
    facts = anchor_owner._owner.facts
    expected = {f.model_dump_json() for f in facts}
    if (
        len(facts) != 4
        or expected != {f.model_dump_json() for f in a.facts}
        or expected != {f.model_dump_json() for f in r.facts}
        or anchor.source_owner_sha256 != risk.source_owner_sha256
        or a.source_kind != r.source_kind
        or any(f.raw_source_sha256 != a.source_artifact_sha256 for f in facts)
        or _sha(risk_owner._source_owner._raw) != r.source_artifact_sha256
    ):
        raise ValueError("SYNTHESIS_ORIGINAL_FACT_OR_PROVENANCE_MISMATCH")
    for span in r.spans:
        risk_owner._source_owner.excerpt(span)
    return dict(
        source_kind=a.source_kind,
        security_id=reg.security_id,
        issuer_id=reg.issuer_id,
        source_generation_id=reg.source_generation_id,
        owner_execution_generation_id=reg.execution_generation_id,
        source_owner_sha256=anchor.source_owner_sha256,
        anchor_review_artifact_sha256=anchor.review_artifact_sha256,
        risk_review_artifact_sha256=risk.review_artifact_sha256,
        anchor_independent_review_sha256=a.independent_review_sha256,
        risk_independent_review_sha256=r.independent_review_sha256,
        anchor_review_event_id=a.review_event_id,
        risk_review_event_id=r.review_event_id,
        anchor_execution_generation_id=anchor.execution_generation_id,
        risk_execution_generation_id=risk.execution_generation_id,
        anchor_source_sha256=a.source_artifact_sha256,
        source_artifact_sha256=r.source_artifact_sha256,
        narrative_source_binding_sha256=r.source_binding_sha256,
        facts=tuple(f.model_dump(mode="json") for f in facts),
        spans=tuple(s.model_dump(mode="json") for s in r.spans),
        filed=r.filed.isoformat(),
        statement_date=r.statement_date.isoformat(),
        cutoff=r.cutoff.isoformat(),
    )


class BackendReviewedSynthesisOwner:
    """Trusted immutable review store over two exact live predecessor owners."""

    def __init__(
        self,
        *,
        anchor_owner,
        risk_owner,
        decision_bytes,
        trusted_decision_sha256,
        review_bytes,
        trusted_review_sha256,
        policy_continuity_bytes,
        trusted_policy_continuity_sha256,
        continuity_review_bytes,
        trusted_continuity_review_sha256,
        proposal_bytes,
        execution_generation_id,
    ):
        for raw, expected in (
            (decision_bytes, trusted_decision_sha256),
            (review_bytes, trusted_review_sha256),
            (policy_continuity_bytes, trusted_policy_continuity_sha256),
            (continuity_review_bytes, trusted_continuity_review_sha256),
        ):
            if type(raw) is not bytes or _sha(raw) != expected:
                raise ValueError("INDEPENDENT_SYNTHESIS_REVIEW_ANCHOR_MISMATCH")
        d = SynthesisReviewDecision.model_validate_json(decision_bytes)
        if (
            type(proposal_bytes) is not bytes
            or d.proposal_sha256 != _sha(proposal_bytes)
            or d.independent_review_sha256 != trusted_review_sha256
            or d.policy_continuity_sha256 != trusted_policy_continuity_sha256
            or d.policy_sha256 != policy_sha256()
        ):
            raise ValueError("SYNTHESIS_REVIEW_PROPOSAL_OR_POLICY_BINDING_MISMATCH")
        bridge = SynthesisPolicyContinuity.model_validate_json(policy_continuity_bytes)
        if bridge.independent_review_sha256 != trusted_continuity_review_sha256:
            raise ValueError("SYNTHESIS_INDEPENDENT_POLICY_CONTINUITY_REVIEW_MISMATCH")
        _verify_policy_continuity(d, review_bytes, bridge)
        bindings = synthesis_review_bindings(anchor_owner, risk_owner)
        if digest(d.model_dump(mode="json", include=set(bindings))) != digest(bindings):
            raise ValueError("SYNTHESIS_EXACT_SOURCE_REVIEW_AND_TIME_BINDING_REQUIRED")
        if execution_generation_id in {
            d.source_generation_id,
            d.owner_execution_generation_id,
            d.anchor_execution_generation_id,
            d.risk_execution_generation_id,
        }:
            raise ValueError("SYNTHESIS_NEW_REVIEW_CONSUMER_GENERATION_REQUIRED")
        admission = ReviewedSynthesisAdmission(
            admission_id=secrets.token_hex(24),
            review=d,
            review_artifact_sha256=trusted_decision_sha256,
            anchor_property=anchor_owner.resolve(anchor_owner.admission),
            risk_property=risk_owner.resolve(risk_owner.admission),
            source_owner_sha256=d.source_owner_sha256,
            execution_generation_id=execution_generation_id,
            admission_sha256="0" * 64,
        )
        admission = admission.model_copy(
            update={
                "admission_sha256": digest(
                    admission.model_dump(mode="json", exclude={"admission_sha256"})
                )
            }
        )
        self._anchor_owner, self._risk_owner = anchor_owner, risk_owner
        self._owner, self._source_owner = anchor_owner._owner, risk_owner._source_owner
        self._review_bytes, self._bridge_json = review_bytes, bridge.model_dump_json()
        self._json, self._revoked, self._lock = admission.model_dump_json(), False, RLock()

    @property
    def admission(self):
        return ReviewedSynthesisAdmission.model_validate_json(self._json)

    def resolve(self, admission):
        with self._lock:
            if (
                self._revoked
                or type(admission) is not ReviewedSynthesisAdmission
                or admission.model_dump_json() != self._json
            ):
                raise ValueError("UNISSUED_CHANGED_OR_REVOKED_SYNTHESIS_PROPERTY")
            if admission.review.policy_sha256 != policy_sha256():
                raise ValueError("SYNTHESIS_GOVERNING_POLICY_CHANGED")
            _verify_policy_continuity(
                admission.review,
                self._review_bytes,
                SynthesisPolicyContinuity.model_validate_json(self._bridge_json),
            )
            self._anchor_owner.resolve(admission.anchor_property)
            self._risk_owner.resolve(admission.risk_property)
            bindings = synthesis_review_bindings(self._anchor_owner, self._risk_owner)
            if digest(
                admission.review.model_dump(mode="json", include=set(bindings))
            ) != digest(bindings):
                raise ValueError("SYNTHESIS_LIVE_SOURCE_OR_REVIEW_CHANGED")
            return admission

    def revoke(self, admission):
        with self._lock:
            self.resolve(admission)
            self._revoked = True


def _verify_policy_continuity(decision, review_bytes, bridge):
    """Bind an unchanged semantic approval through a separately pinned bridge."""
    review = json.loads(review_bytes)
    permission = dict(
        role="DECISIVE_REASON",
        interpretation_type="BALANCED_SYNTHESIS",
        polarity="MIXED",
        allowed_confidences=["LOW"],
        uncertainty="LIMITED",
        consumer="CORE",
        use_axis="CORE_DIRECTION",
    )
    if (
        not isinstance(review, dict)
        or review.get("decision") != "BALANCED_SYNTHESIS_ROLE_ELIGIBLE"
        or review.get("permission") != permission
        or review.get("approved_rendered_claim") != RENDERED_CLAIM
        or review.get("proposal", {}).get("sha256") != decision.proposal_sha256
        or review.get("policy_version") != POLICY
        or review.get("policy_sha256") != decision.semantic_policy_sha256
    ):
        raise ValueError("SYNTHESIS_ORIGINAL_SEMANTIC_REVIEW_SCOPE_MISMATCH")
    _verify_semantic_sources(decision, review)
    sources = review.get("policy_source_sha256", {})
    names = (
        "economic_claim_qualification.py",
        "directional_balance_service.py",
        "native_economic_core.py",
        "accepted_decision_v2_runtime_service.py",
        "fundamental_holder_stance_service.py",
    )
    if not all(name in sources for name in names):
        raise ValueError("SYNTHESIS_SEMANTIC_POLICY_SOURCE_BINDING_REQUIRED")
    current = {name: _sha(Path(__file__).with_name(name).read_bytes()) for name in names}
    old_policy = digest(
        dict(
            policy=POLICY,
            implementation=sources["economic_claim_qualification.py"],
            inherited_semantics=sources["directional_balance_service.py"],
        )
    )
    if (
        bridge.semantic_review_sha256,
        bridge.semantic_policy_sha256,
        bridge.current_policy_sha256,
        bridge.semantic_qualification_source_sha256,
        bridge.current_qualification_source_sha256,
    ) != (
        decision.independent_review_sha256,
        old_policy,
        decision.policy_sha256,
        sources["economic_claim_qualification.py"],
        current["economic_claim_qualification.py"],
    ) or old_policy != decision.semantic_policy_sha256:
        raise ValueError("SYNTHESIS_POLICY_CONTINUITY_BINDING_MISMATCH")
    if any(current[name] != sources[name] for name in names[1:]):
        raise ValueError("SYNTHESIS_UNREVIEWED_GOVERNING_SEMANTIC_CHANGE")


def _verify_semantic_sources(decision, review):
    # Artifact names are review metadata, not issuer-specific runtime rules.
    sources = review.get("source_artifacts_sha256", {})
    required = {
        decision.anchor_source_sha256,
        decision.source_artifact_sha256,
        decision.anchor_review_artifact_sha256,
        decision.risk_review_artifact_sha256,
        decision.anchor_independent_review_sha256,
        decision.risk_independent_review_sha256,
    }
    if not isinstance(sources, dict) or not required <= set(sources.values()):
        raise ValueError("SYNTHESIS_SEMANTIC_REVIEW_SOURCE_MISMATCH")
    subject = review.get("subject", {})
    lineage = review.get("lineage", {})
    if (
        subject.get("security_id") != decision.security_id
        or str(int(subject.get("cik", "-1"))) != str(int(decision.issuer_id))
        or subject.get("filed") != decision.filed.isoformat()
        or subject.get("statement_date") != decision.statement_date.isoformat()
        or subject.get("source_cutoff") != decision.cutoff.isoformat()
        or lineage.get("source_generation") != decision.source_generation_id
        or lineage.get("original_owner_execution") != decision.owner_execution_generation_id
        or lineage.get("R17_review") != decision.anchor_review_event_id
        or lineage.get("R18_review") != decision.risk_review_event_id
        or review.get("required_span_ranges")
        != [[s.start_byte, s.end_byte] for s in decision.spans]
    ):
        raise ValueError("SYNTHESIS_SEMANTIC_REVIEW_IDENTITY_OR_CONTEXT_MISMATCH")


def _project_bundle(admission):
    """Retain the inherited exact four-fact projection; rebind its new owner."""
    from app.services.native_input_admission import BackendOwnerBundle, UseState

    original = _risk_project_bundle(admission.risk_property)
    by_ref = {m.metric_ref: m for m in original.metrics}
    owner_ref = CONTRACT + ":" + admission.admission_id
    metrics = tuple(
        m.model_copy(
            update=dict(
                generation_id=admission.execution_generation_id,
                owner_contract=CONTRACT,
                owner_ref=owner_ref,
                owner_receipt_sha256=admission.admission_sha256,
                authority_state="REVIEWED_HISTORICAL_BALANCED_SYNTHESIS_ROLE_ONLY",
                permissions=tuple(
                    p.model_copy(
                        update={
                            "owner_evidence_ref": owner_ref + "#/" + p.axis.value
                            if p.state == UseState.ALLOWED
                            else None
                        }
                    )
                    for p in m.permissions
                ),
                temporal=tuple(
                    t.model_copy(update={"owner_ref": owner_ref if t.owner_ref else None})
                    for t in m.temporal
                ),
                caveats=(
                    "HISTORICAL_ANCHOR_AND_CONDITIONAL_RISK_JOINT_REVIEW_ONLY",
                    "COMMON_ISSUER_LINEAGE_NOT_INDEPENDENT_CORROBORATION",
                    "ALL_REVIEWED_MITIGANTS_AND_TEMPORAL_CONTEXT_REQUIRED",
                    "NO_CURRENTNESS_FORECAST_STANCE_ORDINAL_HOLDER_OR_COMPLETE_CORE",
                ),
            )
        )
        for m in (
            by_ref["reported-fact:" + f.source_row_identity] for f in admission.review.facts
        )
    )
    result = original.model_copy(
        update=dict(
            generation_id=admission.execution_generation_id,
            metrics=metrics,
            source_envelope_sha256=digest(
                dict(
                    anchor=admission.anchor_property.admission_sha256,
                    risk=admission.risk_property.admission_sha256,
                    original_owner=admission.source_owner_sha256,
                    raw_anchor=admission.review.anchor_source_sha256,
                    raw_narrative=admission.review.source_artifact_sha256,
                    property=admission.admission_sha256,
                )
            ),
        )
    )
    return BackendOwnerBundle.model_validate(result.model_dump(mode="json"))


def _support_rows(admission, registry):
    template = _risk_support_rows(admission.risk_property, registry)[0]
    return [
        template
        | dict(
            support_ref="reviewed-synthesis:" + kind,
            property=kind,
            polarity=polarity,
            applies_to_supports=(
                "reviewed-synthesis:BUSINESS_ANCHOR",
                "reviewed-synthesis:BUSINESS_RISK",
            )
            if kind == "COUNTEREVIDENCE"
            else (),
            property_owner_ref=CONTRACT + ":" + admission.admission_id,
            economic_lineage=admission.review.anchor_source_sha256,
        )
        for kind, polarity in (
            ("BUSINESS_ANCHOR", "POSITIVE"),
            ("BUSINESS_RISK", "NEGATIVE"),
            ("COUNTEREVIDENCE", "MIXED"),
        )
    ]


def _ownership(bundle):
    original = _scale_ownership(bundle)
    return original.model_copy(
        update={
            "expectation_valuation": original.expectation_valuation.model_copy(
                update={"reason": "NO_VALUATION_OR_EXPECTATION_AUTHORITY_IN_SYNTHESIS_REVIEW"}
            )
        }
    )


class BackendSynthesisClaimPolicy(BackendQualifiedEconomicPolicy):
    """One reviewed role through the existing claim engine, never a stance engine."""

    def __init__(self, *args, property_owner, **kwargs):
        if type(property_owner) is not BackendReviewedSynthesisOwner:
            raise ValueError("LIVE_REVIEWED_SYNTHESIS_OWNER_REQUIRED")
        self.reported_property_owner = property_owner
        self._property = property_owner.resolve(property_owner.admission)
        super().__init__(*args, **kwargs)
        self._verify_property_projection(kwargs["registry"])

    @property
    def property_admission_sha256(self):
        return self.assert_property_live().admission_sha256

    @property
    def role_source_kind(self):
        return self.assert_property_live().review.source_kind

    def assert_property_live(self):
        return self.reported_property_owner.resolve(self._property)

    def _verify_property_projection(self, registry):
        a = self.assert_property_live()
        if registry.bundle != _project_bundle(a):
            raise ValueError("SYNTHESIS_EXACT_FACT_PROJECTION_REQUIRED")
        if self.bundle.ownership != _ownership(registry.bundle):
            raise ValueError("SYNTHESIS_OWNERSHIP_SCOPE_BROADENED")
        rows = _support_rows(a, registry)
        if len(self.bundle.supports) != len(rows) or any(
            s != EconomicSupport(**row, property_source_sha256=s.property_source_sha256)
            for s, row in zip(self.bundle.supports, rows, strict=True)
        ):
            raise ValueError("SYNTHESIS_SUPPORT_OR_COUNTEREVIDENCE_SCOPE_CHANGED")
        if (
            self.bundle.policy_owner,
            self.bundle.approval_version,
            self.bundle.source_kind,
        ) != (
            CONTRACT + ":" + a.admission_id,
            RULE,
            "QUALIFIED_PROPERTY_OWNER"
            if a.review.source_kind == "REAL_SEALED_SOURCE"
            else "SYNTHETIC_TEST_PROPERTIES",
        ):
            raise ValueError("SYNTHESIS_REVIEW_OR_PROVENANCE_SUBSTITUTION")

    def verify_backend(self, registry):
        self._verify_property_projection(registry)
        return super().verify_backend(registry)

    def narrative_packet_binding(self):
        """Historical raw-source quotations, not newly asserted current truth."""
        a = self.assert_property_live()
        return dict(
            narrative_admission_sha256=a.admission_sha256,
            narrative_source_sha256=a.review.source_artifact_sha256,
            narrative_span_sha256=tuple(s.raw_sha256 for s in a.review.spans),
            narrative_context=tuple(
                self.reported_property_owner._source_owner.excerpt(s)
                for s in a.review.spans
            ),
        )

    def synthesis_packet_binding(self):
        a = self.assert_property_live()
        return dict(
            anchor_admission_sha256=a.anchor_property.admission_sha256,
            risk_admission_sha256=a.risk_property.admission_sha256,
            anchor_review_sha256=a.anchor_property.review_artifact_sha256,
            risk_review_sha256=a.risk_property.review_artifact_sha256,
            original_owner_execution_generation_id=a.review.owner_execution_generation_id,
            anchor_execution_generation_id=a.anchor_property.execution_generation_id,
            risk_execution_generation_id=a.risk_property.execution_generation_id,
        )

    def qualify(self, proposal, *, request, invocation):
        a = self.assert_property_live()
        proposal = EconomicClaimProposal.model_validate(proposal.model_dump(mode="json"))
        if (
            proposal.requested_role,
            proposal.interpretation_type,
            proposal.polarity,
            proposal.uncertainty,
            proposal.consumer,
            proposal.use_axis,
            proposal.asserts_causality,
            proposal.asserts_recurrence,
            proposal.asserts_independent_corroboration,
            proposal.numeric_assertions,
        ) != (
            "DECISIVE_REASON",
            "BALANCED_SYNTHESIS",
            "MIXED",
            "LIMITED",
            "CORE",
            "CORE_DIRECTION",
            False,
            False,
            False,
            (),
        ):
            raise ValueError("CLAIM_OUTSIDE_REVIEWED_SYNTHESIS_SCOPE")
        if proposal.support_refs != tuple(s.support_ref for s in self.bundle.supports):
            raise ValueError("SYNTHESIS_REQUIRED_SUPPORT_OR_COUNTEREVIDENCE_OMITTED")
        if request.invocation.assessment_as_of < max(
            a.review.cutoff, *(f.filed for f in a.review.facts)
        ):
            raise ValueError("SYNTHESIS_REVIEW_NOT_AVAILABLE_AT_ASSESSMENT")
        result = super().qualify(proposal, request=request, invocation=invocation)
        if result[0].text != RENDERED_CLAIM:
            raise ValueError("SYNTHESIS_REVIEWED_RENDERING_CHANGED")
        self.assert_property_live()
        return result


def build_reported_synthesis_invocation(property_owner, *, invocation_id, assessment_as_of):
    """Trusted factory; freeze the role request only after exact-type dispatch."""
    from app.services.native_input_admission import BackendAdmissionRegistry, UseAxis
    from app.services.native_economic_core import InvocationSpec
    from app.services.native_authority_core import build_context
    from app.services.accepted_decision_v2_runtime_service import (
        build_accepted_v2_economic_core_invocation,
    )
    from app.services.reported_economic_claim_consumer import _build_role_request

    if type(property_owner) is not BackendReviewedSynthesisOwner:
        raise ValueError("LIVE_REVIEWED_SYNTHESIS_OWNER_REQUIRED")
    a = property_owner.resolve(property_owner.admission)
    if date.fromisoformat(str(assessment_as_of)) < max(
        a.review.cutoff, *(f.filed for f in a.review.facts)
    ):
        raise ValueError("SYNTHESIS_REVIEW_NOT_AVAILABLE_AT_ASSESSMENT")
    bundle = _project_bundle(a)
    bundle_sha = digest(bundle.model_dump(mode="json"))
    registry = BackendAdmissionRegistry(bundle, expected_bundle_sha256=bundle_sha)
    refs = tuple(m.metric_ref for m in bundle.metrics)
    owner_ref = CONTRACT + ":" + a.admission_id
    rows = _support_rows(a, registry)
    body = json.dumps(
        dict(
            security_id=bundle.security_id,
            generation_id=bundle.generation_id,
            source_generation_id=bundle.source_generation_id,
            owner_ref=owner_ref,
            properties=rows,
            backend_bundle_sha256=bundle_sha,
            source_envelope_sha256=bundle.source_envelope_sha256,
        )
    ).encode()
    source_sha = _sha(body)
    policy_bundle = ClaimPolicyBundle(
        security_id=bundle.security_id,
        generation_id=bundle.generation_id,
        source_generation_id=bundle.source_generation_id,
        backend_bundle_sha256=bundle_sha,
        policy_owner=owner_ref,
        approval_version=RULE,
        ownership=_ownership(bundle),
        supports=tuple(
            EconomicSupport(**row, property_source_sha256=source_sha) for row in rows
        ),
        rule_sha256=policy_sha256(),
        source_kind="QUALIFIED_PROPERTY_OWNER"
        if a.review.source_kind == "REAL_SEALED_SOURCE"
        else "SYNTHETIC_TEST_PROPERTIES",
    )
    policy = BackendSynthesisClaimPolicy(
        policy_bundle,
        property_owner=property_owner,
        expected_policy_sha256=digest(policy_bundle.model_dump(mode="json")),
        registry=registry,
        property_sources={"reviewed-synthesis": body},
        trusted_source_sha256={"reviewed-synthesis": source_sha},
    )
    context = build_context(
        admission_input=dict(
            security_id=bundle.security_id,
            generation_id=bundle.generation_id,
            source_generation_id=bundle.source_generation_id,
            metric_refs=refs,
            issuer_context=None,
        ),
        registry=registry,
        request_id=invocation_id,
    )
    axes = (UseAxis.CORE_VISIBILITY, UseAxis.CORE_DIRECTION)
    spec = InvocationSpec(
        invocation_id=invocation_id,
        security_id=bundle.security_id,
        generation_id=bundle.generation_id,
        source_generation_id=bundle.source_generation_id,
        assessment_as_of=assessment_as_of,
        intended_consumer="CORE",
        allowed_use_axes=axes,
        forbidden_use_axes=tuple(axis for axis in UseAxis if axis not in axes),
    )
    inv = build_accepted_v2_economic_core_invocation(
        context=context,
        admission_registry=registry,
        invocation_spec=spec,
        economic_policy=policy,
        authority_native_v2=True,
    )
    request = _build_role_request(inv)
    if (
        request.required_role != "DECISIVE_REASON"
        or request.property_admission_sha256 != a.admission_sha256
    ):
        raise ValueError("SYNTHESIS_NATIVE_ROLE_REQUEST_BINDING_MISMATCH")
    binding = policy.narrative_packet_binding() | policy.synthesis_packet_binding()
    for name, expected in binding.items():
        actual = getattr(request, name, None)
        if name == "narrative_context" and actual is not None:
            actual = tuple(row.model_dump(mode="json") for row in actual)
        if actual != expected:
            raise ValueError("SYNTHESIS_NATIVE_ROLE_CONTEXT_BINDING_MISMATCH")
    inv._reported_role_request_json = request.model_dump_json()
    return inv
