"""Opt-in semantic source review before economic support admission.

The implemented authority is deliberately narrow: a reported operating-result
comparison is an operating account observation, not a qualified business anchor.
This producer never manufactures an EconomicSupport or directional grant from
growth. Substantive materiality/causal review needs a separately governed owner.
All capabilities are backend composition objects, not deserializable authority.
"""

from __future__ import annotations

from datetime import date
import hashlib
import json
from pathlib import Path
import secrets
from threading import RLock
from typing import Literal

from pydantic import Field

from app.services.native_input_admission import Closed, Identity, SHA
from app.services.reported_fact_owner import BackendReportedFactOwner
from app.services.reported_fact_use_policy import BackendReportedContextPolicy
from app.services.unified_snapshot_contract import digest

CONTRACT = "real-economic-property-owner-v1"
POLICY = "reported-operating-account-semantic-review-v1"
AUTHORITY = "REV63P-R17:OFFLINE_EXISTING_SEMANTICS_TECHNICAL_QUALIFICATION"


def policy_sha256():
    from app.services import directional_balance_service

    return digest(
        dict(
            version=POLICY,
            authority=AUTHORITY,
            implementation=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            inherited_economic_policy=hashlib.sha256(
                Path(directional_balance_service.__file__).read_bytes()
            ).hexdigest(),
        )
    )


class SourceSpan(Closed):
    artifact_sha256: SHA
    json_pointer: str
    content_sha256: SHA
    source_role: Literal["FACT_OCCURRENCE", "ACCOUNT_DEFINITION"]


class PropertyProposal(Closed):
    security_id: Identity
    issuer_id: Identity
    source_generation_id: Identity
    owner_execution_generation_id: Identity
    execution_generation_id: Identity
    invocation_id: Identity
    comparison_sha256: SHA
    property_type: Literal[
        "REPORTED_OPERATING_COMPARISON",
        "BUSINESS_ANCHOR",
        "CAUSAL_MECHANISM",
        "RECURRENCE",
        "INDEPENDENT_CORROBORATION",
    ]
    requested_role: (
        Literal["BUY_DRIVER", "SELL_DRIVER", "DECISIVE_REASON", "HOLDER_REASON"] | None
    ) = None
    consumer: Literal["CORE", "HOLDER", "OVERALL", "NEWBUYER"] = "CORE"
    use_axis: Literal[
        "CORE_CONTEXT",
        "CORE_DIRECTION",
        "HOLDER_CONTEXT",
        "HOLDER_DIRECTION",
        "OVERALL_DIRECTION",
        "NEWBUYER_DIRECTION",
    ] = "CORE_CONTEXT"
    asserts_causality: bool = False
    asserts_recurrence: bool = False
    asserts_independence: bool = False
    policy_sha256: SHA


class ReviewItem(Closed):
    category: Identity
    state: Literal[
        "AVAILABLE_SUPPORTING",
        "AVAILABLE_CONTRADICTORY",
        "MISSING_REQUIRED",
        "MISSING_OPTIONAL",
        "NOT_APPLICABLE",
    ]
    source_spans: tuple[SourceSpan, ...] = ()
    reason_code: Identity


class PropertyReview(Closed):
    contract: Literal["real-economic-property-review-v1"] = "real-economic-property-review-v1"
    review_id: Identity
    proposal: PropertyProposal
    fact_owner_sha256: SHA
    source_spans: tuple[SourceSpan, ...]
    fact_admission_sha256: tuple[SHA, ...]
    period_start: date
    period_end: date
    prior_period_start: date
    prior_period_end: date
    currency: Identity
    basis: Identity
    current_value: float = Field(allow_inf_nan=False)
    prior_value: float = Field(allow_inf_nan=False)
    delta: float = Field(allow_inf_nan=False)
    growth_pct: float | None = Field(allow_inf_nan=False)
    denominator_state: Literal["POSITIVE", "ZERO", "NEGATIVE"]
    semantic_meaning: Literal["REPORTED_OPERATING_RESULT_NOT_NET_INCOME_OR_RECURRING_PROFIT"]
    economic_materiality: Literal["NOT_ESTABLISHED_BY_SCALE_OR_GROWTH"]
    causal_mechanism: Literal["NOT_ESTABLISHED"]
    recurrence: Literal["UNRESOLVED_NOT_NONRECURRING"]
    interpretation_confidence: Literal["NOT_AUTHORIZED"]
    counterevidence: tuple[ReviewItem, ...]
    disposition: Literal[
        "BOUNDED_DESCRIPTIVE_PROPERTY_SUPPORTED",
        "REQUIRED_EVIDENCE_MISSING",
        "POLICY_DECISION_REQUIRED",
        "SOURCE_COMPARISON_CONFLICT",
    ]
    blocking_gates: tuple[Identity, ...]
    eligible_roles: tuple[()] = ()
    reviewer_authority: Literal["REV63P-R17:OFFLINE_EXISTING_SEMANTICS_TECHNICAL_QUALIFICATION"] = (
        AUTHORITY
    )
    authority_scope: Literal["ACCOUNT_MEANING_ONLY_NOT_INVESTMENT_MATERIALITY_APPROVAL"] = (
        "ACCOUNT_MEANING_ONLY_NOT_INVESTMENT_MATERIALITY_APPROVAL"
    )
    request_sha256: SHA
    invocation_sha256: SHA
    review_sha256: SHA


class PropertyAdmission(Closed):
    contract: Literal["real-economic-property-owner-v1"] = CONTRACT
    admission_id: Identity
    review: PropertyReview
    policy_version: Literal["reported-operating-account-semantic-review-v1"] = POLICY
    provenance: Literal["SEALED_SOURCE_TECHNICAL_REVIEW", "SYNTHETIC_TEST_SOURCE"]
    permitted_use_axes: tuple[Literal["CORE_CONTEXT"], ...] = ("CORE_CONTEXT",)
    economic_role_eligible: Literal[False] = False
    accepted_economic_output: Literal[False] = False
    admission_sha256: SHA


class BackendRealEconomicPropertyOwner:
    """Live-parent-bound producer; caller hashes, labels and reviewer IDs grant nothing.

    Constructor source pins belong to trusted backend composition. The native
    consumer accepts neither this constructor's arguments nor an imported review.
    The active technical policy cannot issue any investment role, even with a
    caller's claimed approval. A new semantic authority requires a new policy.
    """

    def __init__(
        self,
        *,
        fact_owner,
        companyfacts: bytes,
        trusted_source_sha256: str,
        parent,
        invocation_id: str,
        provenance: str,
    ):
        from app.services.native_owner_session import BackendOwnerParent

        if (
            type(fact_owner) is not BackendReportedFactOwner
            or type(parent) is not BackendOwnerParent
        ):
            raise ValueError("LIVE_BACKEND_FACT_AND_PARENT_CAPABILITIES_REQUIRED")
        if (
            type(companyfacts) is not bytes
            or hashlib.sha256(companyfacts).hexdigest() != trusted_source_sha256
        ):
            raise ValueError("INDEPENDENT_PROPERTY_SOURCE_ANCHOR_REQUIRED")
        if provenance not in {"SEALED_SOURCE_TECHNICAL_REVIEW", "SYNTHETIC_TEST_SOURCE"}:
            raise ValueError("EXPLICIT_PROPERTY_SOURCE_PROVENANCE_REQUIRED")
        raw = json.loads(companyfacts)
        registration = fact_owner.registration
        if str(int(raw["cik"])) != str(int(registration.issuer_id)):
            raise ValueError("PROPERTY_SOURCE_ISSUER_MISMATCH")
        if not fact_owner.facts or any(
            f.raw_source_sha256 != trusted_source_sha256 for f in fact_owner.facts
        ):
            raise ValueError("PROPERTY_SOURCE_FACT_OWNER_MISMATCH")
        inv = parent.invocation(invocation_id)
        request = inv.verify(inv.request)
        scope = request.invocation
        if (scope.security_id, scope.source_generation_id) != (
            registration.security_id,
            registration.source_generation_id,
        ):
            raise ValueError("PROPERTY_PARENT_SOURCE_IDENTITY_MISMATCH")
        if (
            not isinstance(inv._reported_policy, BackendReportedContextPolicy)
            or inv._reported_policy._owner is not fact_owner
        ):
            raise ValueError("EXACT_LIVE_FACT_OWNER_INVOCATION_REQUIRED")
        self._owner, self._parent, self._invocation = fact_owner, parent, inv
        self._key, self._raw, self._sha = invocation_id, raw, trusted_source_sha256
        self._provenance = provenance
        self._reviews, self._admissions, self._revoked = {}, {}, set()
        self._lock = RLock()

    def _live(self):
        inv = self._parent.invocation(self._key)
        if inv is not self._invocation:
            raise ValueError("PROPERTY_PARENT_CAPABILITY_REPLACED")
        return inv.verify(inv.request)

    def _span(self, pointer, value, role):
        return SourceSpan(
            artifact_sha256=self._sha,
            json_pointer=pointer,
            content_sha256=digest(value),
            source_role=role,
        )

    def review(self, proposal, comparison):
        with self._lock:
            request = self._live()
            p = PropertyProposal.model_validate(proposal.model_dump(mode="json"))
            result = self._owner.verify_interpretation(comparison)
            registration, scope = self._owner.registration, request.invocation
            if (
                p.security_id,
                p.issuer_id,
                p.source_generation_id,
                p.owner_execution_generation_id,
                p.execution_generation_id,
                p.invocation_id,
                p.comparison_sha256,
            ) != (
                scope.security_id,
                registration.issuer_id,
                scope.source_generation_id,
                registration.execution_generation_id,
                scope.generation_id,
                scope.invocation_id,
                result.interpretation_sha256,
            ):
                raise ValueError("PROPERTY_SECURITY_SOURCE_EXECUTION_BINDING_MISMATCH")
            if p.policy_sha256 != policy_sha256():
                raise ValueError("PROPERTY_POLICY_IDENTITY_MISMATCH")
            if p.consumer != "CORE" or p.use_axis not in {"CORE_CONTEXT", "CORE_DIRECTION"}:
                raise ValueError("PROPERTY_CONSUMER_USE_NOT_AUTHORIZED")
            grants = getattr(request, "reported_contexts", ())
            if result not in tuple(g.comparison for g in grants):
                raise ValueError("PROPERTY_REQUEST_COMPARISON_MEMBERSHIP_MISSING")
            facts = self._owner.authorize_interpretation(
                result,
                axis="DISPLAY",
                security_id=p.security_id,
                execution_generation_id=p.owner_execution_generation_id,
                source_generation_id=p.source_generation_id,
            )
            current, prior = facts
            if any(
                (f.field, f.taxonomy, f.concept)
                != ("operating_income", "us-gaap", "OperatingIncomeLoss")
                for f in facts
            ):
                raise ValueError("PROPERTY_ACCOUNT_SEMANTIC_POLICY_NOT_APPLICABLE")
            if (
                current.currency,
                current.statement_basis,
                current.share_basis,
                current.duration_days,
            ) != (prior.currency, prior.statement_basis, prior.share_basis, prior.duration_days):
                raise ValueError("PROPERTY_COMPARISON_BASIS_MISMATCH")
            concept = self._raw["facts"][current.taxonomy][current.concept]
            definition = concept.get("description")
            if not isinstance(definition, str) or not definition.strip():
                raise ValueError("ACCOUNT_DEFINITION_SOURCE_MISSING")
            prefix = f"/facts/{current.taxonomy}/{current.concept}"
            spans = [self._span(prefix + "/description", definition, "ACCOUNT_DEFINITION")]
            conflicts = []
            for fact in facts:
                rows = concept["units"][fact.currency]
                occurrence = rows[fact.occurrence_ordinal]
                if digest(occurrence) != fact.occurrence_sha256:
                    raise ValueError("PROPERTY_SOURCE_OCCURRENCE_MISMATCH")
                spans.append(
                    self._span(
                        f"{prefix}/units/{fact.currency}/{fact.occurrence_ordinal}",
                        occurrence,
                        "FACT_OCCURRENCE",
                    )
                )
                for index, row in enumerate(rows):
                    if (
                        (row.get("start"), row.get("end"))
                        == (fact.period_start.isoformat(), fact.period_end.isoformat())
                        and row.get("filed", "9999") <= registration.cutoff.isoformat()
                        and row.get("val") != fact.value
                    ):
                        conflicts.append(
                            self._span(
                                f"{prefix}/units/{fact.currency}/{index}", row, "FACT_OCCURRENCE"
                            )
                        )
            directional = (
                p.requested_role is not None
                or p.use_axis != "CORE_CONTEXT"
                or p.property_type != "REPORTED_OPERATING_COMPARISON"
            )
            gaps = []
            if conflicts:
                gaps.append("COUNTEREVIDENCE_SOURCE_COMPARISON_CONFLICT")
            if directional:
                gaps.extend(
                    (
                        "MATERIALITY_EVIDENCE_GAP",
                        "ECONOMIC_PROPERTY_SEMANTIC_REVIEW_AUTHORITY_REQUIRED",
                        "COUNTEREVIDENCE_QUALIFICATION_GAP",
                        "FACT_USE_GRANT_GAP",
                    )
                )
            if p.asserts_causality or p.property_type == "CAUSAL_MECHANISM":
                gaps.append("CAUSAL_RELEVANCE_GAP")
            if p.asserts_recurrence or p.property_type == "RECURRENCE":
                gaps.append("RECURRENCE_EVIDENCE_GAP")
            if p.asserts_independence or p.property_type == "INDEPENDENT_CORROBORATION":
                gaps.append("CORRELATED_SOURCE_NOT_INDEPENDENT_SUPPORT")
            items = (
                ReviewItem(
                    category="COMPARABLE_RAW_CONFLICT",
                    state="AVAILABLE_CONTRADICTORY" if conflicts else "AVAILABLE_SUPPORTING",
                    source_spans=tuple(conflicts or spans[1:]),
                    reason_code="EXACT_SEALED_CONCEPT_PERIOD_SCAN_NOT_EXHAUSTIVE_FILING_REVIEW",
                ),
                ReviewItem(
                    category="REPORTING_BASIS",
                    state="AVAILABLE_SUPPORTING",
                    source_spans=tuple(spans),
                    reason_code="OWNED_COMPATIBLE_ACCOUNT_AND_PERIOD",
                ),
                ReviewItem(
                    category="AMENDMENT_AND_STRUCTURAL_OPERATING_REVIEW",
                    state="MISSING_REQUIRED" if directional else "MISSING_OPTIONAL",
                    reason_code="COMPANYFACTS_NOT_COMPLETE_FILING_NARRATIVE_REVIEW",
                ),
                ReviewItem(
                    category="MECHANISM",
                    state="MISSING_REQUIRED"
                    if p.asserts_causality or p.property_type == "CAUSAL_MECHANISM"
                    else "MISSING_OPTIONAL",
                    reason_code="NOT_INFERRED_FROM_ACCOUNT_VALUE",
                ),
                ReviewItem(
                    category="RECURRENCE",
                    state="MISSING_REQUIRED"
                    if p.asserts_recurrence or p.property_type == "RECURRENCE"
                    else "MISSING_OPTIONAL",
                    reason_code="ABSENCE_NOT_NONRECURRING_EVIDENCE",
                ),
            )
            body = dict(
                review_id=secrets.token_hex(24),
                proposal=p,
                fact_owner_sha256=result.source_owner_sha256,
                source_spans=tuple(spans),
                fact_admission_sha256=result.supporting_admission_sha256,
                period_start=current.period_start,
                period_end=current.period_end,
                prior_period_start=prior.period_start,
                prior_period_end=prior.period_end,
                currency=current.currency,
                basis=current.statement_basis,
                current_value=current.value,
                prior_value=prior.value,
                delta=result.delta,
                growth_pct=result.growth_pct,
                denominator_state="POSITIVE"
                if prior.value > 0
                else "NEGATIVE"
                if prior.value < 0
                else "ZERO",
                semantic_meaning="REPORTED_OPERATING_RESULT_NOT_NET_INCOME_OR_RECURRING_PROFIT",
                economic_materiality="NOT_ESTABLISHED_BY_SCALE_OR_GROWTH",
                causal_mechanism="NOT_ESTABLISHED",
                recurrence="UNRESOLVED_NOT_NONRECURRING",
                interpretation_confidence="NOT_AUTHORIZED",
                counterevidence=items,
                disposition="SOURCE_COMPARISON_CONFLICT"
                if conflicts
                else "REQUIRED_EVIDENCE_MISSING"
                if gaps
                else "BOUNDED_DESCRIPTIVE_PROPERTY_SUPPORTED",
                blocking_gates=tuple(gaps),
                request_sha256=scope.request_sha256,
                invocation_sha256=scope.invocation_scope_sha256,
            )
            normalized = {
                k: v.model_dump(mode="json")
                if isinstance(v, Closed)
                else [x.model_dump(mode="json") for x in v]
                if isinstance(v, tuple) and v and isinstance(v[0], Closed)
                else v.isoformat()
                if isinstance(v, date)
                else v
                for k, v in body.items()
            }
            review = PropertyReview(**body, review_sha256=digest(normalized))
            self._reviews[review.review_id] = review.model_dump_json()
            return review

    def admit(self, review):
        with self._lock:
            self._live()
            if (
                not isinstance(review, PropertyReview)
                or self._reviews.get(review.review_id) != review.model_dump_json()
            ):
                raise ValueError("UNISSUED_PROPERTY_REVIEW_OR_FORGED_REVIEWER")
            if review.proposal.policy_sha256 != policy_sha256():
                raise ValueError("PROPERTY_POLICY_IDENTITY_MISMATCH")
            if (
                review.disposition != "BOUNDED_DESCRIPTIVE_PROPERTY_SUPPORTED"
                or review.blocking_gates
            ):
                raise ValueError("REAL_ECONOMIC_PROPERTY_EVIDENCE_OR_AUTHORITY_GAP")
            existing = next(
                (
                    a
                    for a in self._admissions.values()
                    if json.loads(a)["review"]["review_id"] == review.review_id
                ),
                None,
            )
            if existing is not None:
                admission = PropertyAdmission.model_validate_json(existing)
                if admission.admission_id in self._revoked:
                    raise ValueError("PROPERTY_ADMISSION_REVOKED")
                return admission
            body = dict(
                admission_id=secrets.token_hex(24), review=review, provenance=self._provenance
            )
            admission = PropertyAdmission(
                **body, admission_sha256=digest(body | {"review": review.model_dump(mode="json")})
            )
            self._admissions[admission.admission_id] = admission.model_dump_json()
            return admission

    def resolve(self, admission, *, parent, invocation_id, consumer, use_axis):
        with self._lock:
            self._live()
            if parent is not self._parent or invocation_id != self._key:
                raise ValueError("PROPERTY_WRONG_PARENT_OR_INVOCATION")
            if (
                not isinstance(admission, PropertyAdmission)
                or self._admissions.get(admission.admission_id) != admission.model_dump_json()
            ):
                raise ValueError("UNISSUED_OR_CHANGED_PROPERTY_ADMISSION")
            if admission.admission_id in self._revoked:
                raise ValueError("PROPERTY_ADMISSION_REVOKED")
            if admission.review.proposal.policy_sha256 != policy_sha256():
                raise ValueError("PROPERTY_POLICY_IDENTITY_MISMATCH")
            if consumer != "CORE" or use_axis not in admission.permitted_use_axes:
                raise ValueError("PROPERTY_ECONOMIC_USE_NOT_AUTHORIZED")
            return admission

    def revoke(self, admission):
        with self._lock:
            self.resolve(
                admission,
                parent=self._parent,
                invocation_id=self._key,
                consumer="CORE",
                use_axis="CORE_CONTEXT",
            )
            self._revoked.add(admission.admission_id)

    def admitted_count(self):
        return len(self._admissions)
