"""Claim-specific independent review to owned, bounded economic support.

Trusted backend composition supplies the independently reviewed decision and its
immutable anchors. Neither model JSON nor native request callers can populate
this trust store. Deterministic checks bind the review, but do not make the
case-specific materiality judgment: that judgment belongs to the recorded review.
"""

from __future__ import annotations

from datetime import date
import hashlib
import json
import secrets
from threading import RLock
from typing import Literal

from pydantic import Field, model_validator

from app.services.native_input_admission import Closed, Identity, SHA
from app.services.reported_fact_owner import BackendReportedFactOwner, ReportedFact
from app.services.unified_snapshot_contract import digest
from app.services.economic_claim_qualification import BackendQualifiedEconomicPolicy

CONTRACT = "real-economic-property-owner-v1"
RULE = "reviewed-historical-operating-anchor-v1"


class EconomicReviewDecision(Closed):
    contract: Literal["independent-economic-property-review-v1"] = (
        "independent-economic-property-review-v1"
    )
    review_event_id: Identity
    reviewer: Identity
    mandate: Literal["R17_USER_AUTHORIZED_EXISTING_POLICY_QUALIFICATION"]
    rule_version: Literal["reviewed-historical-operating-anchor-v1"] = RULE
    decision: Literal["APPROVE_BOUNDED_EXISTING_POLICY_QUALIFICATION"]
    proposal_sha256: SHA
    independent_review_sha256: SHA
    inherited_policy_sha256: SHA
    source_kind: Literal["REAL_SEALED_SOURCE", "SYNTHETIC_REVIEW_FIXTURE"]
    source_artifact_sha256: SHA
    source_generation_id: Identity
    owner_execution_generation_id: Identity
    security_id: Identity
    issuer_id: Identity
    facts: tuple[ReportedFact, ...] = Field(min_length=4, max_length=4)
    property_type: Literal["BUSINESS_ANCHOR"] = "BUSINESS_ANCHOR"
    economic_meaning: Literal["HISTORICAL_REPORTED_OPERATING_PERFORMANCE_IMPROVEMENT"]
    materiality_basis: Literal["CASE_REVIEW_ENTITY_WIDE_ABSOLUTE_OPERATING_AND_REVENUE_SCALE"]
    permitted_role: Literal["BUY_DRIVER"] = "BUY_DRIVER"
    consumer: Literal["CORE"] = "CORE"
    use_axis: Literal["CORE_DIRECTION"] = "CORE_DIRECTION"
    allowed_confidences: tuple[Literal["LOW"], ...] = ("LOW",)
    uncertainty: Literal["LIMITED"] = "LIMITED"
    asserts_causality: Literal[False] = False
    asserts_recurrence: Literal[False] = False
    asserts_independence: Literal[False] = False
    counterevidence_scope: Literal["SEALED_EXACT_PERIOD_CONFLICT_BASIS_AND_DISCOVERY_INDEX"]
    unreviewed: tuple[
        Literal[
            "FILING_NARRATIVE",
            "UNSEALED_AMENDMENTS",
            "UNDISCLOSED_ADJUSTMENTS",
            "CAUSE",
            "RECURRENCE",
            "CURRENTNESS",
            "FUTURE_RISKS",
        ],
        ...,
    ]

    @model_validator(mode="after")
    def bounded_review(self):
        if (
            self.allowed_confidences != ("LOW",)
            or set(self.unreviewed)
            != {
                "FILING_NARRATIVE",
                "UNSEALED_AMENDMENTS",
                "UNDISCLOSED_ADJUSTMENTS",
                "CAUSE",
                "RECURRENCE",
                "CURRENTNESS",
                "FUTURE_RISKS",
            }
            or len(self.unreviewed) != 7
        ):
            raise ValueError("REVIEW_LIMITATIONS_MUST_REMAIN_EXPLICIT")
        return self


class ReviewedPropertyAdmission(Closed):
    contract: Literal["real-economic-property-owner-v1"] = CONTRACT
    admission_id: Identity
    review: EconomicReviewDecision
    review_artifact_sha256: SHA
    source_owner_sha256: SHA
    supporting_fact_admission_sha256: tuple[SHA, ...]
    execution_generation_id: Identity
    lineage: Literal["NEW_REVIEW_REFERENCES_UNCHANGED_HISTORICAL_OWNER"] = (
        "NEW_REVIEW_REFERENCES_UNCHANGED_HISTORICAL_OWNER"
    )
    admission_sha256: SHA


class BackendReviewedPropertyOwner:
    """Opaque review lookup with source semantics checked before any use grant.

    Expected anchors are backend-held immutable review-store inputs, not request
    parameters. Same-process hostile Python is outside this capability boundary.
    A new owner cannot resolve another owner's admission; no JSON rehydration.
    """

    def __init__(
        self,
        *,
        fact_owner,
        decision_bytes,
        trusted_decision_sha256,
        review_bytes,
        trusted_review_sha256,
        proposal_bytes,
        source_bytes,
        trusted_source_sha256,
        execution_generation_id,
    ):
        if type(fact_owner) is not BackendReportedFactOwner:
            raise ValueError("LIVE_REPORTED_FACT_OWNER_REQUIRED")
        for raw, expected in (
            (decision_bytes, trusted_decision_sha256),
            (review_bytes, trusted_review_sha256),
            (source_bytes, trusted_source_sha256),
        ):
            if type(raw) is not bytes or hashlib.sha256(raw).hexdigest() != expected:
                raise ValueError("INDEPENDENT_REVIEW_OR_SOURCE_ANCHOR_MISMATCH")
        decision = EconomicReviewDecision.model_validate_json(decision_bytes)
        from app.services import directional_balance_service
        from pathlib import Path

        if (
            decision.independent_review_sha256 != trusted_review_sha256
            or decision.proposal_sha256 != hashlib.sha256(proposal_bytes).hexdigest()
            or decision.inherited_policy_sha256
            != hashlib.sha256(Path(directional_balance_service.__file__).read_bytes()).hexdigest()
            or decision.source_artifact_sha256 != trusted_source_sha256
        ):
            raise ValueError("REVIEW_MANDATE_SOURCE_OR_POLICY_BINDING_MISMATCH")
        reg = fact_owner.registration
        if (
            decision.security_id,
            decision.issuer_id,
            decision.source_generation_id,
            decision.owner_execution_generation_id,
        ) != (
            reg.security_id,
            reg.issuer_id,
            reg.source_generation_id,
            reg.execution_generation_id,
        ):
            raise ValueError("REVIEW_SECURITY_ISSUER_GENERATION_MISMATCH")
        if (
            set(f.model_dump_json() for f in decision.facts)
            != set(f.model_dump_json() for f in fact_owner.facts)
            or len(set(f.model_dump_json() for f in decision.facts)) != 4
        ):
            raise ValueError("EXACT_REVIEWED_FACT_SET_REQUIRED")
        raw = json.loads(source_bytes)
        if str(int(raw["cik"])) != str(int(reg.issuer_id)):
            raise ValueError("REVIEW_SOURCE_ISSUER_MISMATCH")
        admissions = tuple(fact_owner.admit(f) for f in decision.facts)
        comparisons = []
        for field, concept in (
            ("revenue", "RevenueFromContractWithCustomerExcludingAssessedTax"),
            ("operating_income", "OperatingIncomeLoss"),
        ):
            pair = sorted(
                (a for a in admissions if a.fact.field == field),
                key=lambda a: a.fact.period_end,
                reverse=True,
            )
            if len(pair) != 2 or any(
                (a.fact.taxonomy, a.fact.concept, a.fact.raw_source_sha256)
                != ("us-gaap", concept, trusted_source_sha256)
                for a in pair
            ):
                raise ValueError("REVIEW_ACCOUNT_MEANING_NOT_APPLICABLE")
            current, prior = (a.fact for a in pair)
            if (
                current.currency,
                current.statement_basis,
                current.share_basis,
                current.duration_days,
            ) != (prior.currency, prior.statement_basis, prior.share_basis, prior.duration_days):
                raise ValueError("REVIEW_COMPARISON_BASIS_MISMATCH")
            result = fact_owner.compare(*pair)
            if result.factual_direction != "UP" or prior.value <= 0:
                raise ValueError("REVIEW_PROPOSITION_CONTRADICTS_FACTS")
            comparisons.append(result)
            for f in (current, prior):
                rows = raw["facts"][f.taxonomy][f.concept]["units"][f.currency]
                if digest(rows[f.occurrence_ordinal]) != f.occurrence_sha256:
                    raise ValueError("REVIEW_EXACT_OCCURRENCE_MISMATCH")
                for row in rows:
                    if (
                        (row.get("start"), row.get("end"))
                        == (f.period_start.isoformat(), f.period_end.isoformat())
                        and row.get("filed", "9999") <= reg.cutoff.isoformat()
                        and row.get("val") != f.value
                    ):
                        raise ValueError("REVIEW_SEALED_COUNTEREVIDENCE_CONFLICT")
        # Cross-account scale belongs to the same periods and accounting scope.
        grouped = {
            field: sorted(
                (f for f in decision.facts if f.field == field), key=lambda f: f.period_end
            )
            for field in ("revenue", "operating_income")
        }
        for revenue, operating in zip(grouped["revenue"], grouped["operating_income"], strict=True):
            if (
                revenue.period_start,
                revenue.period_end,
                revenue.currency,
                revenue.statement_basis,
                revenue.filing_accession,
            ) != (
                operating.period_start,
                operating.period_end,
                operating.currency,
                operating.statement_basis,
                operating.filing_accession,
            ):
                raise ValueError("REVIEW_BUSINESS_SCALE_BASIS_MISMATCH")
        body = dict(
            admission_id=secrets.token_hex(24),
            review=decision,
            review_artifact_sha256=trusted_decision_sha256,
            source_owner_sha256=comparisons[0].source_owner_sha256,
            supporting_fact_admission_sha256=tuple(a.admission_sha256 for a in admissions),
            execution_generation_id=execution_generation_id,
        )
        admission = ReviewedPropertyAdmission(
            **body, admission_sha256=digest(body | {"review": decision.model_dump(mode="json")})
        )
        self._owner, self._admissions, self._comparisons = (
            fact_owner,
            admissions,
            tuple(comparisons),
        )
        self._json, self._revoked, self._lock = admission.model_dump_json(), False, RLock()
        self._grants = {}

    @property
    def admission(self):
        return ReviewedPropertyAdmission.model_validate_json(self._json)

    def resolve(self, admission):
        with self._lock:
            if (
                self._revoked
                or not isinstance(admission, ReviewedPropertyAdmission)
                or admission.model_dump_json() != self._json
            ):
                raise ValueError("UNISSUED_CHANGED_OR_REVOKED_REVIEWED_PROPERTY")
            from app.services import directional_balance_service
            from pathlib import Path

            if (
                admission.review.inherited_policy_sha256
                != hashlib.sha256(
                    Path(directional_balance_service.__file__).read_bytes()
                ).hexdigest()
            ):
                raise ValueError("REVIEW_GOVERNING_POLICY_CHANGED")
            for a in self._admissions:
                self._owner.resolve(
                    a,
                    axis="DISPLAY",
                    security_id=admission.review.security_id,
                    execution_generation_id=admission.review.owner_execution_generation_id,
                    source_generation_id=admission.review.source_generation_id,
                )
            for result in self._comparisons:
                self._owner.verify_interpretation(result)
            return admission

    def revoke(self, admission):
        with self._lock:
            self.resolve(admission)
            self._revoked = True


class BackendReportedPropertyClaimPolicy(BackendQualifiedEconomicPolicy):
    """The real-property route cannot be downgraded to generic claim-v2."""

    def __init__(self, *args, property_owner, **kwargs):
        if type(property_owner) is not BackendReviewedPropertyOwner:
            raise ValueError("LIVE_REVIEWED_PROPERTY_OWNER_REQUIRED")
        self.reported_property_owner = property_owner
        self._property = property_owner.resolve(property_owner.admission)
        super().__init__(*args, **kwargs)
        self._verify_property_projection(kwargs["registry"])

    def _verify_property_projection(self, registry):
        from app.services.native_input_admission import UseAxis, UseState

        admission = self.reported_property_owner.resolve(self._property)
        decision = admission.review
        registration = self.reported_property_owner._owner.registration
        bundle = registry.bundle
        if (
            bundle.security_id,
            bundle.ticker,
            bundle.market,
            bundle.generation_id,
            bundle.source_generation_id,
            bundle.source_envelope_sha256,
            bundle.issuer_context,
        ) != (
            decision.security_id,
            registration.ticker,
            registration.market.lower(),
            admission.execution_generation_id,
            decision.source_generation_id,
            digest(dict(raw=decision.source_artifact_sha256, property=admission.admission_sha256)),
            None,
        ):
            raise ValueError("REVIEWED_PROPERTY_REGISTRY_IDENTITY_MISMATCH")
        by_ref = {"reported-fact:" + f.source_row_identity: f for f in decision.facts}
        if set(by_ref) != {m.metric_ref for m in registry.bundle.metrics}:
            raise ValueError("REVIEWED_PROPERTY_EXACT_FACT_MEMBERSHIP_REQUIRED")
        owner_ref = CONTRACT + ":" + admission.admission_id
        for m in registry.bundle.metrics:
            f = by_ref[m.metric_ref]
            if (
                m.security_id,
                m.security_type,
                m.source_generation_id,
                m.metric_type,
                m.value,
                m.unit,
                m.currency,
                m.share_basis,
                m.owner_contract,
                m.owner_ref,
                m.owner_receipt_sha256,
                m.source_artifact_sha256,
                m.input_sha256,
                m.generation_id,
            ) != (
                decision.security_id,
                registration.security_type,
                decision.source_generation_id,
                f.concept,
                f.value,
                f.currency,
                f.currency,
                f.share_basis,
                CONTRACT,
                owner_ref,
                admission.admission_sha256,
                f.raw_source_sha256,
                f.occurrence_sha256,
                admission.execution_generation_id,
            ):
                raise ValueError("REVIEWED_PROPERTY_FACT_PROJECTION_MISMATCH")
            if any(
                p.state
                != (
                    UseState.ALLOWED
                    if p.axis in {UseAxis.CORE_VISIBILITY, UseAxis.CORE_DIRECTION}
                    else UseState.UNSPECIFIED
                )
                for p in m.permissions
            ):
                raise ValueError("REVIEWED_PROPERTY_USE_GRANT_BROADENED")
            for t in m.temporal:
                known = t.field in {"source_statement_period", "financial_period"}
                expected_state = (
                    "VERIFIED_OWNER_PERIOD"
                    if known
                    else "NOT_APPLICABLE"
                    if t.field
                    in {"denominator_period_start", "denominator_period_end", "price_session"}
                    else "UNKNOWN_NOT_PROVIDED"
                )
                if (t.state.value, t.value) != (
                    expected_state,
                    f.period_end.isoformat() if known else None,
                ):
                    raise ValueError("REVIEWED_PROPERTY_TEMPORAL_PROMOTION")
        supports = self.bundle.supports
        if tuple(s.property for s in supports) != ("BUSINESS_ANCHOR", "COUNTEREVIDENCE"):
            raise ValueError("REVIEWED_PROPERTY_ROLE_SUPPORT_BROADENED")
        refs = tuple(m.metric_ref for m in registry.bundle.metrics)
        for s in supports:
            if (
                s.evidence_refs,
                s.allowed_confidences,
                s.state,
                s.property_owner_ref,
                s.economic_lineage,
                s.independent_of_supports,
            ) != (
                refs,
                decision.allowed_confidences,
                "AVAILABLE_SUPPORTING",
                owner_ref,
                decision.source_artifact_sha256,
                (),
            ):
                raise ValueError("REVIEWED_PROPERTY_SUPPORT_SCOPE_MISMATCH")
            if s.polarity != ("POSITIVE" if s.property == "BUSINESS_ANCHOR" else "MIXED"):
                raise ValueError("REVIEWED_PROPERTY_SUPPORT_POLARITY_MISMATCH")
        if self.bundle.source_kind != (
            "QUALIFIED_PROPERTY_OWNER"
            if decision.source_kind == "REAL_SEALED_SOURCE"
            else "SYNTHETIC_TEST_PROPERTIES"
        ):
            raise ValueError("REVIEWED_PROPERTY_PROVENANCE_SUBSTITUTION")

    def verify_backend(self, registry):
        self.reported_property_owner.resolve(self._property)
        self._verify_property_projection(registry)
        return super().verify_backend(registry)

    def qualify(self, proposal, *, request, invocation):
        reviewed = self.reported_property_owner.resolve(self._property)
        decision = reviewed.review
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
        ) != (
            decision.permitted_role,
            "BUSINESS_SUPPORT",
            "POSITIVE",
            "LIMITED",
            "CORE",
            "CORE_DIRECTION",
            False,
            False,
            False,
        ):
            raise ValueError("CLAIM_OUTSIDE_REVIEWED_ECONOMIC_PROPERTY_SCOPE")
        if proposal.support_refs != tuple(s.support_ref for s in self.bundle.supports):
            raise ValueError("REVIEWED_CLAIM_REQUIRED_SUPPORT_OMITTED")
        # Preserve the reviewed historical proposition in the consumed claim,
        # not only in accompanying ownership metadata.
        by_field = {
            field: sorted(
                (f for f in decision.facts if f.field == field), key=lambda f: f.period_end
            )
            for field in ("revenue", "operating_income")
        }
        prior, current = by_field["operating_income"]
        revenue_prior, revenue_current = by_field["revenue"]
        text = (
            f"Historical reported operating improvement ({prior.period_start}/{prior.period_end} to "
            f"{current.period_start}/{current.period_end}): operating income {prior.value} to {current.value}; "
            f"entity revenue {revenue_prior.value} to {revenue_current.value} {current.currency}. "
            "Bounded positive support, LOW/LIMITED. Cause, recurrence, normalization, independent corroboration, "
            "current truth and investment stance are not established."
        )
        from app.services.cross_market_decision_engine_service import EvidenceClaim

        rendered = EvidenceClaim(
            text=text,
            evidence_refs=tuple(m.metric_ref for m in invocation._registry.bundle.metrics),
        )
        claim, receipt, supports = super().qualify(proposal, request=request, invocation=invocation)
        if rendered.evidence_refs != claim.evidence_refs:
            raise ValueError("REVIEWED_RENDERING_EVIDENCE_MISMATCH")
        return rendered, receipt, supports


def build_reported_property_invocation(property_owner, *, invocation_id, assessment_as_of):
    """Backend-only assembly from the live approved property, never caller metrics."""
    from app.services.native_input_admission import (
        BackendAdmissionRegistry,
        BackendOwnerBundle,
        MetricAuthorityEnvelope,
        Permission,
        TemporalField,
        UseAxis,
    )
    from app.services.native_economic_core import InvocationSpec, bound_reference
    from app.services.native_authority_core import build_context
    from app.services.economic_claim_qualification import (
        ClaimPolicyBundle,
        EconomicSupport,
        policy_sha256,
    )
    from app.services.accepted_decision_v2_runtime_service import (
        AcceptedV2EvidenceOwnership,
        build_accepted_v2_economic_core_invocation,
    )
    from app.services.expectation_valuation_interaction_service import (
        ExpectationValuationInteraction,
    )

    admission = property_owner.resolve(property_owner.admission)
    d = admission.review
    if date.fromisoformat(str(assessment_as_of)) < max(f.filed for f in d.facts):
        raise ValueError("REVIEWED_FACT_NOT_AVAILABLE_AT_ASSESSMENT")
    metrics = []
    owner_ref = CONTRACT + ":" + admission.admission_id
    for f in d.facts:
        ref = "reported-fact:" + f.source_row_identity
        temporal = []
        for field in (
            "retrieval_timestamp",
            "metric_as_of",
            "denominator_period_start",
            "denominator_period_end",
            "source_statement_period",
            "price_session",
            "financial_period",
        ):
            known = field in {"source_statement_period", "financial_period"}
            temporal.append(
                TemporalField(
                    field=field,
                    value=f.period_end.isoformat() if known else None,
                    state="VERIFIED_OWNER_PERIOD"
                    if known
                    else "NOT_APPLICABLE"
                    if field
                    in {"denominator_period_start", "denominator_period_end", "price_session"}
                    else "UNKNOWN_NOT_PROVIDED",
                    owner_ref=owner_ref if known else None,
                    source_artifact_sha256=f.raw_source_sha256 if known else None,
                )
            )
        metrics.append(
            MetricAuthorityEnvelope(
                metric_ref=ref,
                metric_type=f.concept,
                value=f.value,
                unit=f.currency,
                security_id=f.security_id,
                security_type=property_owner._owner.registration.security_type,
                generation_id=admission.execution_generation_id,
                source_generation_id=f.source_generation_id,
                owner_contract=CONTRACT,
                owner_ref=owner_ref,
                owner_receipt_sha256=admission.admission_sha256,
                source_provider="SEC_COMPANYFACTS_SEALED",
                source_artifact_ref=f.raw_source_sha256,
                source_artifact_sha256=f.raw_source_sha256,
                currency=f.currency,
                share_basis=f.share_basis,
                authority_state="CLAIM_SPECIFIC_REVIEW_NOT_UNRESTRICTED_FACT_DIRECTION",
                permissions=tuple(
                    Permission(
                        axis=a,
                        state="ALLOWED"
                        if a in {UseAxis.CORE_VISIBILITY, UseAxis.CORE_DIRECTION}
                        else "UNSPECIFIED",
                        owner_evidence_ref=owner_ref + "#/" + a.value
                        if a in {UseAxis.CORE_VISIBILITY, UseAxis.CORE_DIRECTION}
                        else None,
                    )
                    for a in UseAxis
                ),
                temporal=tuple(temporal),
                caveats=(
                    "HISTORICAL_SEALED_REPORTED_PERFORMANCE_ONLY",
                    "NOT_CAUSE_RECURRENCE_INDEPENDENCE_OR_CURRENT_TRUTH",
                    "REVIEWED_BUY_DRIVER_ELIGIBILITY_NOT_BUY_DECISION",
                ),
                input_sha256=f.occurrence_sha256,
            )
        )
    source_envelope = digest(
        dict(raw=d.source_artifact_sha256, property=admission.admission_sha256)
    )
    bundle = BackendOwnerBundle(
        security_id=d.security_id,
        ticker=property_owner._owner.registration.ticker,
        market=property_owner._owner.registration.market.lower(),
        generation_id=admission.execution_generation_id,
        source_generation_id=d.source_generation_id,
        source_envelope_sha256=source_envelope,
        metrics=tuple(metrics),
        issuer_context=None,
    )
    registry = BackendAdmissionRegistry(
        bundle, expected_bundle_sha256=digest(bundle.model_dump(mode="json"))
    )
    refs = tuple(m.metric_ref for m in metrics)
    rows = []
    for kind, polarity in (("BUSINESS_ANCHOR", "POSITIVE"), ("COUNTEREVIDENCE", "MIXED")):
        rows.append(
            dict(
                support_ref="reviewed:" + kind,
                property=kind,
                evidence_refs=refs,
                evidence_bindings=tuple(
                    bound_reference(registry, r).model_dump(mode="json") for r in refs
                ),
                applies_to_supports=("reviewed:BUSINESS_ANCHOR",)
                if kind == "COUNTEREVIDENCE"
                else (),
                independent_of_supports=(),
                property_owner_ref=owner_ref,
                economic_lineage=d.source_artifact_sha256,
                polarity=polarity,
                state="AVAILABLE_SUPPORTING",
                temporal_rules=(
                    dict(
                        field="metric_as_of",
                        allowed_states=("UNKNOWN_NOT_PROVIDED",),
                        maximum_age_days=None,
                    ),
                    dict(
                        field="financial_period",
                        allowed_states=("VERIFIED_OWNER_PERIOD",),
                        maximum_age_days=None,
                    ),
                ),
                allowed_confidences=d.allowed_confidences,
            )
        )
    body = json.dumps(
        dict(
            security_id=d.security_id,
            generation_id=bundle.generation_id,
            source_generation_id=d.source_generation_id,
            owner_ref=owner_ref,
            properties=rows,
            backend_bundle_sha256=digest(bundle.model_dump(mode="json")),
            source_envelope_sha256=source_envelope,
        )
    ).encode()
    sha = hashlib.sha256(body).hexdigest()
    ownership = AcceptedV2EvidenceOwnership(
        ticker=bundle.ticker,
        core_ref_ids=refs,
        timing_ref_ids=(),
        expectation_valuation=ExpectationValuationInteraction(
            ticker=bundle.ticker,
            classification="UNKNOWN",
            expectation_refs=(),
            valuation_refs=(),
            independent_expectation_basis_refs=(),
            shared_underlying_refs=(),
            reason="NO_VALUATION_OR_EXPECTATION_AUTHORIZATION_IN_REPORTED_PROPERTY_REVIEW",
        ),
    )
    policy_bundle = ClaimPolicyBundle(
        security_id=d.security_id,
        generation_id=bundle.generation_id,
        source_generation_id=d.source_generation_id,
        backend_bundle_sha256=digest(bundle.model_dump(mode="json")),
        policy_owner=owner_ref,
        approval_version=RULE,
        ownership=ownership,
        supports=tuple(EconomicSupport(**row, property_source_sha256=sha) for row in rows),
        rule_sha256=policy_sha256(),
        source_kind="QUALIFIED_PROPERTY_OWNER"
        if d.source_kind == "REAL_SEALED_SOURCE"
        else "SYNTHETIC_TEST_PROPERTIES",
    )
    policy = BackendReportedPropertyClaimPolicy(
        policy_bundle,
        property_owner=property_owner,
        expected_policy_sha256=digest(policy_bundle.model_dump(mode="json")),
        registry=registry,
        property_sources={"reviewed": body},
        trusted_source_sha256={"reviewed": sha},
    )
    context = build_context(
        admission_input=dict(
            security_id=d.security_id,
            generation_id=bundle.generation_id,
            source_generation_id=d.source_generation_id,
            metric_refs=refs,
            issuer_context=None,
        ),
        registry=registry,
        request_id=invocation_id,
    )
    axes = (UseAxis.CORE_VISIBILITY, UseAxis.CORE_DIRECTION)
    spec = InvocationSpec(
        invocation_id=invocation_id,
        security_id=d.security_id,
        generation_id=bundle.generation_id,
        source_generation_id=d.source_generation_id,
        assessment_as_of=assessment_as_of,
        intended_consumer="CORE",
        allowed_use_axes=axes,
        forbidden_use_axes=tuple(a for a in UseAxis if a not in axes),
    )
    inv = build_accepted_v2_economic_core_invocation(
        context=context,
        admission_registry=registry,
        invocation_spec=spec,
        economic_policy=policy,
        authority_native_v2=True,
    )
    from app.services.reported_economic_claim_consumer import _build_role_request

    inv._reported_role_request_json = _build_role_request(inv).model_dump_json()
    return inv
