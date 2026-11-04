"""Opt-in typed model-claim eligibility, not an investment decision engine.

Backend support admissions describe reviewed economic properties, not approved
issuer sentences. Model proposals select roles and support relationships. The
bounded renderer prevents arbitrary prose becoming a new source assertion.
Unsupported free-form reasoning requires a separate semantic admission policy.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import secrets
from typing import Literal

from pydantic import Field, model_validator

from app.services.native_input_admission import Closed, Identity, SHA, Consumer, UseAxis
from app.services.native_economic_core import (
    BackendEconomicPolicy,
    EconomicPolicyBundle,
    EconomicModelCandidate,
    InterpretationTemporalRule,
    bound_reference,
    _interpretation_eligible,
)
from app.services.cross_market_decision_engine_service import EvidenceClaim
from app.services.native_authority_core import BoundEvidenceReference
from app.services.unified_snapshot_contract import digest

CONTRACT = "generic-economic-claim-qualification-v1"
POLICY = "inherited-core-typed-claim-eligibility-v1"
Property = Literal[
    "BUSINESS_ANCHOR",
    "BUSINESS_RISK",
    "CAUSAL_MECHANISM",
    "RECURRENCE",
    "HOLDER_BASIS",
    "COUNTEREVIDENCE",
    "INDEPENDENT_CORROBORATION",
    "CURRENT_CORROBORATION",
    "STRONGER_ECONOMIC_SUPPORT",
]
Role = Literal["BUY_DRIVER", "SELL_DRIVER", "DECISIVE_REASON", "HOLDER_REASON"]


def policy_sha256():
    from app.services import directional_balance_service as balance

    return digest(
        dict(
            policy=POLICY,
            implementation=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            inherited_semantics=hashlib.sha256(Path(balance.__file__).read_bytes()).hexdigest(),
        )
    )


class EconomicSupport(Closed):
    """Backend-admitted property; never a field accepted from model output."""

    support_ref: Identity
    property: Property
    evidence_refs: tuple[Identity, ...] = Field(min_length=1, max_length=6)
    evidence_bindings: tuple[BoundEvidenceReference, ...] = Field(min_length=1, max_length=6)
    applies_to_supports: tuple[Identity, ...] = ()
    independent_of_supports: tuple[Identity, ...] = ()
    property_owner_ref: Identity
    property_source_sha256: SHA
    economic_lineage: Identity
    polarity: Literal["POSITIVE", "NEGATIVE", "MIXED", "UNCERTAIN"]
    state: Literal[
        "AVAILABLE_SUPPORTING",
        "AVAILABLE_CONTRADICTORY",
        "MISSING_REQUIRED",
        "MISSING_OPTIONAL",
        "NOT_APPLICABLE",
    ]
    temporal_rules: tuple[InterpretationTemporalRule, ...] = Field(min_length=1)
    allowed_confidences: tuple[Literal["LOW", "MEDIUM", "HIGH"], ...] = Field(min_length=1)

    @model_validator(mode="after")
    def exact_support_shape(self):
        if self.evidence_refs != tuple(r.evidence_ref for r in self.evidence_bindings):
            raise ValueError("SUPPORT_EXACT_ADMISSION_REFS_REQUIRED")
        fields = [r.field for r in self.temporal_rules]
        if len(fields) != len(set(fields)) or "metric_as_of" not in fields:
            raise ValueError("EXPLICIT_NON_DUPLICATE_METRIC_TEMPORAL_POLICY_REQUIRED")
        return self


class ClaimPolicyBundle(EconomicPolicyBundle):
    contract: Literal["backend-economic-claim-support-v1"] = "backend-economic-claim-support-v1"
    interpretations: tuple[()] = ()
    supports: tuple[EconomicSupport, ...]
    policy_version: Literal["inherited-core-typed-claim-eligibility-v1"] = POLICY
    rule_sha256: SHA
    source_kind: Literal["QUALIFIED_PROPERTY_OWNER", "SYNTHETIC_TEST_PROPERTIES"]


class NumericClaim(Closed):
    evidence_ref: Identity
    value: float = Field(allow_inf_nan=False)


class EconomicClaimProposal(Closed):
    contract: Literal["generic-economic-claim-qualification-v1"] = CONTRACT
    claim_id: Identity
    security_id: Identity
    generation_id: Identity
    source_generation_id: Identity
    requested_role: Role
    interpretation_type: Literal[
        "BUSINESS_SUPPORT", "BUSINESS_CAUTION", "BALANCED_SYNTHESIS", "HOLDER_REASSESSMENT"
    ]
    polarity: Literal["POSITIVE", "NEGATIVE", "MIXED", "UNCERTAIN"]
    uncertainty: Literal["QUALIFIED", "LIMITED"]
    support_refs: tuple[Identity, ...] = Field(min_length=1)
    numeric_assertions: tuple[NumericClaim, ...] = Field(default=(), max_length=2)
    asserts_causality: bool = False
    asserts_recurrence: bool = False
    asserts_independent_corroboration: bool = False
    consumer: Literal["CORE"] = "CORE"
    use_axis: Literal["CORE_DIRECTION"] = "CORE_DIRECTION"
    policy_version: Literal["inherited-core-typed-claim-eligibility-v1"] = POLICY
    policy_sha256: SHA


class QualifiedEconomicModelCandidate(EconomicModelCandidate):
    economic_claims: tuple[EconomicClaimProposal, ...] = Field(min_length=4)


class ClaimEligibilityReceipt(Closed):
    contract: Literal["backend-economic-claim-eligibility-v1"] = (
        "backend-economic-claim-eligibility-v1"
    )
    receipt_id: Identity
    claim_sha256: SHA
    request_sha256: SHA
    invocation_sha256: SHA
    security_id: Identity
    generation_id: Identity
    source_generation_id: Identity
    policy_sha256: SHA
    support_sha256: SHA
    evidence_refs: tuple[Identity, ...]
    owner_refs: tuple[Identity, ...]
    role: Role
    consumer: Literal["CORE"] = "CORE"
    use_axis: Literal["CORE_DIRECTION"] = "CORE_DIRECTION"
    accepted_model_judgment: Literal[False] = False
    objective_investment_truth_proven: Literal[False] = False


def render_claim(proposal, supports):
    """Render typed meaning, not arbitrary model prose beside a valid ref."""
    labels = {
        "BUSINESS_SUPPORT": "The admitted business anchor supports the positive business case",
        "BUSINESS_CAUTION": "The admitted business risk supports the negative business case",
        "BALANCED_SYNTHESIS": "The admitted business anchor and risk require balanced synthesis",
        "HOLDER_REASSESSMENT": "The admitted ownership basis supports reassessment of continued holding",
    }
    text = labels[proposal.interpretation_type]
    if proposal.asserts_causality:
        text += "; the asserted mechanism has admitted support"
    if proposal.asserts_recurrence:
        text += "; recurrence has admitted support"
    if proposal.asserts_independent_corroboration:
        text += "; distinct economic-lineage support is admitted"
    text += ". Uncertainty: " + proposal.uncertainty.lower() + "."
    for number in proposal.numeric_assertions:
        text += f" Observed {number.evidence_ref}: {number.value}."
    refs = tuple(dict.fromkeys(r for s in supports for r in s.evidence_refs))
    return EvidenceClaim(text=text, evidence_refs=refs)


class BackendQualifiedEconomicPolicy(BackendEconomicPolicy):
    """Live backend capability with independent, exact property-source anchors.

    Public output cannot instantiate this through any native request builder.
    The constructor is trusted composition, just as BackendAdmissionRegistry.
    Possession of a caller-recomputed payload digest is not that capability.
    """

    claim_contract = CONTRACT

    def __init__(
        self, bundle, *, expected_policy_sha256, registry, property_sources, trusted_source_sha256
    ):
        if any(m.owner_contract in {
            "real-economic-property-owner-v1", "real-narrative-risk-property-owner-v1",
            "real-balanced-synthesis-property-owner-v1",
        } for m in registry.bundle.metrics):
            from app.services.reported_economic_claim_consumer import is_reported_property_policy

            if not is_reported_property_policy(self):
                raise ValueError("REPORTED_FACT_PROPERTY_OWNER_ROUTE_REQUIRED")
        bundle = ClaimPolicyBundle.model_validate(bundle.model_dump(mode="json"))
        if digest(bundle.model_dump(mode="json")) != expected_policy_sha256:
            raise ValueError("INDEPENDENT_CLAIM_POLICY_ANCHOR_REQUIRED")
        if bundle.rule_sha256 != policy_sha256():
            raise ValueError("CLAIM_POLICY_VERSION_MISMATCH")
        base = EconomicPolicyBundle(
            **{k: getattr(bundle, k) for k in EconomicPolicyBundle.model_fields if k != "contract"}
        )
        super().__init__(
            base, expected_policy_sha256=digest(base.model_dump(mode="json")), registry=registry
        )
        if set(property_sources) != set(trusted_source_sha256):
            raise ValueError("EXACT_PROPERTY_SOURCE_ANCHORS_REQUIRED")
        admitted = {}
        for key, raw in property_sources.items():
            if (
                type(raw) is not bytes
                or hashlib.sha256(raw).hexdigest() != trusted_source_sha256[key]
            ):
                raise ValueError("PROPERTY_SOURCE_ANCHOR_MISMATCH")
            value = json.loads(raw)
            if set(value) != {
                "security_id",
                "generation_id",
                "source_generation_id",
                "owner_ref",
                "properties",
                "backend_bundle_sha256",
                "source_envelope_sha256",
            }:
                raise ValueError("CLOSED_PROPERTY_SOURCE_REQUIRED")
            if (value["security_id"], value["generation_id"], value["source_generation_id"]) != (
                bundle.security_id,
                bundle.generation_id,
                bundle.source_generation_id,
            ):
                raise ValueError("PROPERTY_SOURCE_IDENTITY_MISMATCH")
            if (value["backend_bundle_sha256"], value["source_envelope_sha256"]) != (
                bundle.backend_bundle_sha256,
                registry.bundle.source_envelope_sha256,
            ):
                raise ValueError("PROPERTY_SOURCE_ADMISSION_BINDING_MISMATCH")
            admitted[trusted_source_sha256[key]] = value
        ids = [s.support_ref for s in bundle.supports]
        if len(ids) != len(set(ids)):
            raise ValueError("DUPLICATE_SUPPORT_REF")
        for support in bundle.supports:
            if not set((*support.applies_to_supports, *support.independent_of_supports)) <= set(
                ids
            ):
                raise ValueError("SUPPORT_RELATION_TARGET_MISSING")
            source = admitted.get(support.property_source_sha256)
            body = support.model_dump(mode="json", exclude={"property_source_sha256"})
            if (
                source is None
                or source["owner_ref"] != support.property_owner_ref
                or body not in source["properties"]
            ):
                raise ValueError("UNADMITTED_ECONOMIC_PROPERTY")
            for ref in support.evidence_refs:
                registry.receipt(ref)
                if not registry.allowed(ref, Consumer.CORE, UseAxis.CORE_DIRECTION):
                    raise ValueError("PROPERTY_DIRECTION_AUTHORITY_MISSING")
            if support.evidence_bindings != tuple(
                bound_reference(registry, ref) for ref in support.evidence_refs
            ):
                raise ValueError("PROPERTY_SOURCE_ADMISSION_BINDING_MISMATCH")
        self._json = bundle.model_dump_json()
        self._registry = registry
        self._issued = {}

    @property
    def bundle(self):
        return ClaimPolicyBundle.model_validate_json(self._json)

    def verify_backend(self, registry):
        if registry is not self._registry or self.bundle.rule_sha256 != policy_sha256():
            raise ValueError("CLAIM_POLICY_BACKEND_OR_CODE_CHANGED")
        return self

    def qualify(self, proposal, *, request, invocation):
        request = invocation.verify(request)
        if invocation._policy is not self:
            raise ValueError("CLAIM_POLICY_INVOCATION_CAPABILITY_MISMATCH")
        proposal = EconomicClaimProposal.model_validate(proposal.model_dump(mode="json"))
        self.verify_backend(invocation._registry)
        scope = request.invocation
        if (proposal.security_id, proposal.generation_id, proposal.source_generation_id) != (
            scope.security_id,
            scope.generation_id,
            scope.source_generation_id,
        ):
            raise ValueError("CLAIM_SECURITY_GENERATION_MISMATCH")
        if proposal.policy_sha256 != self.bundle.rule_sha256:
            raise ValueError("CLAIM_POLICY_DIGEST_MISMATCH")
        if (
            scope.intended_consumer != Consumer.CORE
            or UseAxis.CORE_DIRECTION not in scope.allowed_use_axes
        ):
            raise ValueError("REJECT_INVOCATION_CONSUMER_SCOPE")
        by_id = {s.support_ref: s for s in self.bundle.supports}
        if len(set(proposal.support_refs)) != len(proposal.support_refs) or any(
            r not in by_id for r in proposal.support_refs
        ):
            raise ValueError("UNADMITTED_CLAIM_SUPPORT")
        supports = tuple(by_id[r] for r in proposal.support_refs)
        anchors = {
            s.support_ref
            for s in supports
            if s.property in {"BUSINESS_ANCHOR", "BUSINESS_RISK", "HOLDER_BASIS"}
        }
        closure = set(proposal.support_refs)
        while True:
            required_refs = {
                s.support_ref
                for s in self.bundle.supports
                if closure & set(s.applies_to_supports)
                and s.state not in {"MISSING_OPTIONAL", "NOT_APPLICABLE"}
            }
            expanded = closure | required_refs
            if expanded == closure:
                break
            closure = expanded
        obligations = [by_id[r] for r in closure]
        if any(s.support_ref not in proposal.support_refs for s in obligations):
            raise ValueError("APPLICABLE_COUNTEREVIDENCE_OR_SUPPORT_OMITTED")
        available = [
            s for s in supports if s.state in {"AVAILABLE_SUPPORTING", "AVAILABLE_CONTRADICTORY"}
        ]
        if any(s.state == "MISSING_REQUIRED" for s in supports):
            raise ValueError("CLAIM_REQUIRED_EVIDENCE_GAP")
        if not available:
            raise ValueError("CLAIM_REQUIRED_EVIDENCE_GAP")
        # Required checks are scoped to the proposed claim, not issuer-global.
        kinds = {s.property for s in available}
        supporting = [s for s in available if s.state == "AVAILABLE_SUPPORTING"]
        roles = {
            "BUY_DRIVER": ("BUSINESS_SUPPORT", "POSITIVE", {"BUSINESS_ANCHOR"}),
            "SELL_DRIVER": ("BUSINESS_CAUTION", "NEGATIVE", {"BUSINESS_RISK"}),
            "DECISIVE_REASON": (
                "BALANCED_SYNTHESIS",
                "MIXED",
                {"BUSINESS_ANCHOR", "BUSINESS_RISK"},
            ),
            "HOLDER_REASON": ("HOLDER_REASSESSMENT", "UNCERTAIN", {"HOLDER_BASIS"}),
        }
        kind, polarity, required = roles[proposal.requested_role]
        if (proposal.interpretation_type, proposal.polarity) != (
            kind,
            polarity,
        ) or not required <= kinds:
            raise ValueError("CLAIM_ROLE_SUPPORT_MISMATCH")
        if proposal.requested_role == "BUY_DRIVER" and not any(
            s.property == "BUSINESS_ANCHOR" and s.polarity == "POSITIVE" for s in supporting
        ):
            raise ValueError("MATERIAL_ANCHOR_POLARITY_MISMATCH")
        if proposal.requested_role == "SELL_DRIVER" and not any(
            s.property == "BUSINESS_RISK" and s.polarity == "NEGATIVE" for s in supporting
        ):
            raise ValueError("MATERIAL_RISK_POLARITY_MISMATCH")
        if "COUNTEREVIDENCE" not in kinds:
            raise ValueError("CLAIM_COUNTEREVIDENCE_REVIEW_MISSING")
        for asserted, category in (
            (proposal.asserts_causality, "CAUSAL_MECHANISM"),
            (proposal.asserts_recurrence, "RECURRENCE"),
        ):
            if asserted and not any(
                s.property == category
                and anchors & set(s.applies_to_supports)
                and s.polarity in {proposal.polarity, "MIXED"}
                for s in supporting
            ):
                raise ValueError("UNSUPPORTED_CAUSAL_OR_RECURRENCE_ASSERTION")
        if proposal.asserts_independent_corroboration:
            corroboration = [s for s in supporting if s.property == "INDEPENDENT_CORROBORATION"]
            anchor_rows = [s for s in supporting if s.property in required]
            if not any(
                _compatible_support(s, anchor_rows, proposal.polarity)
                and _independent(s, _relevant_anchors(anchor_rows, proposal.polarity))
                for s in corroboration
            ):
                raise ValueError("CORRELATED_SUPPORT_NOT_INDEPENDENT")
        if (
            any(s.state == "AVAILABLE_CONTRADICTORY" for s in available)
            and proposal.uncertainty != "LIMITED"
        ):
            raise ValueError("COUNTEREVIDENCE_UNCERTAINTY_NOT_PRESERVED")
        claim = render_claim(proposal, available)
        from types import SimpleNamespace

        for s in available:
            row = SimpleNamespace(
                claim=EvidenceClaim(text="typed support", evidence_refs=s.evidence_refs),
                temporal_rules=s.temporal_rules,
            )
            if not _interpretation_eligible(row, request.reference_request, scope):
                raise ValueError("CLAIM_REQUEST_MEMBERSHIP_TIME_OR_USE_GAP")
            for ref in s.evidence_refs:
                expected = next(b for b in s.evidence_bindings if b.evidence_ref == ref)
                if expected != bound_reference(invocation._registry, ref):
                    raise ValueError("CLAIM_OWNER_BINDING_MISMATCH")
        metrics = {m.metric_ref: m for m in self._registry.bundle.metrics}
        for assertion in proposal.numeric_assertions:
            if (
                assertion.evidence_ref not in claim.evidence_refs
                or metrics[assertion.evidence_ref].value != assertion.value
            ):
                raise ValueError("UNSUPPORTED_NUMERIC_CLAIM")
        key = digest(dict(claim=proposal.model_dump(mode="json"), request=scope.request_sha256))
        if key not in self._issued:
            self._issued[key] = ClaimEligibilityReceipt(
                receipt_id=secrets.token_hex(24),
                claim_sha256=digest(proposal.model_dump(mode="json")),
                request_sha256=scope.request_sha256,
                invocation_sha256=scope.invocation_scope_sha256,
                security_id=scope.security_id,
                generation_id=scope.generation_id,
                source_generation_id=scope.source_generation_id,
                policy_sha256=self.bundle.rule_sha256,
                support_sha256=digest([s.model_dump(mode="json") for s in available]),
                evidence_refs=claim.evidence_refs,
                owner_refs=tuple(sorted({s.property_owner_ref for s in available})),
                role=proposal.requested_role,
            ).model_dump_json()
        return claim, ClaimEligibilityReceipt.model_validate_json(self._issued[key]), available

    def resolve_claim(self, receipt, proposal, *, request, invocation):
        if not isinstance(receipt, ClaimEligibilityReceipt):
            raise ValueError("ISSUED_CLAIM_ELIGIBILITY_REQUIRED")
        key = digest(
            dict(claim=proposal.model_dump(mode="json"), request=request.invocation.request_sha256)
        )
        if self._issued.get(key) != receipt.model_dump_json():
            raise ValueError("UNISSUED_CLAIM_ELIGIBILITY")
        _, expected, _ = self.qualify(proposal, request=request, invocation=invocation)
        if expected != receipt:
            raise ValueError("CLAIM_ELIGIBILITY_BINDING_MISMATCH")
        return receipt

    def validate_model(self, model, *, request, invocation):
        from app.services.native_economic_core import _claim_rows

        model = QualifiedEconomicModelCandidate.model_validate(model.model_dump(mode="json"))
        rows = _claim_rows(model.candidate)
        if (
            len(rows) != len(model.economic_claims)
            or tuple(c.claim_id for c in model.economic_claims) != model.interpretation_refs
        ):
            raise ValueError("CLAIM_ROLE_COVERAGE_MISMATCH")
        if len(set(model.interpretation_refs)) != len(model.interpretation_refs):
            raise ValueError("DUPLICATE_MODEL_CLAIM_ID")
        receipts = []
        driver_supports = {"BUY_DRIVER": [], "SELL_DRIVER": []}
        for (role, output_claim), proposal in zip(rows, model.economic_claims, strict=True):
            claim, receipt, supports = self.qualify(
                proposal, request=request, invocation=invocation
            )
            if role != proposal.requested_role or output_claim != claim:
                raise ValueError("UNSUPPORTED_ECONOMIC_NARRATIVE_OR_ROLE")
            if any(model.candidate.confidence not in s.allowed_confidences for s in supports):
                raise ValueError("CLAIM_CONFIDENCE_NOT_AUTHORIZED")
            if role in driver_supports:
                driver_supports[role].append(supports)
            receipts.append(receipt)
        # Reify the inherited ordinal support floor without selecting a stance
        # or treating every unknown as negative evidence/a mechanical HOLD cap.
        for role, strength in (
            ("BUY_DRIVER", model.candidate.directional_balance.buy),
            ("SELL_DRIVER", model.candidate.directional_balance.sell),
        ):
            polarity = "POSITIVE" if role == "BUY_DRIVER" else "NEGATIVE"
            # Keep each proposed driver's support relationships intact. A
            # corroboration need not cover unrelated anchors in other claims.
            current = independent = stronger = False
            for supports in driver_supports[role]:
                anchors = _relevant_anchors(supports, polarity)
                for support in supports:
                    if support.state != "AVAILABLE_SUPPORTING" or not _compatible_support(
                        support, anchors, polarity
                    ):
                        continue
                    current |= support.property == "CURRENT_CORROBORATION"
                    independent |= support.property == "INDEPENDENT_CORROBORATION" and _independent(
                        support, anchors
                    )
                    stronger |= support.property == "STRONGER_ECONOMIC_SUPPORT"
            if strength >= 6 and not (current or independent):
                raise ValueError("ORDINAL_CURRENT_OR_INDEPENDENT_SUPPORT_GAP")
            if strength >= 6.5 and not stronger:
                raise ValueError("ORDINAL_STRONGER_SUPPORT_GAP")
        if model.candidate.holder_axis.stance != "REVIEW":
            raise ValueError("BOUNDED_HOLDER_REASSESSMENT_NOT_OTHER_HOLDER_STANCE")
        return tuple(receipts)


def _independent(support, anchors):
    return bool(anchors) and all(
        a.support_ref in support.independent_of_supports
        and a.economic_lineage != support.economic_lineage
        and not set(a.evidence_refs) & set(support.evidence_refs)
        for a in anchors
    )


def _relevant_anchors(supports, polarity):
    return [
        a
        for a in supports
        if a.property in {"BUSINESS_ANCHOR", "BUSINESS_RISK", "HOLDER_BASIS"}
        and a.polarity == polarity
        and a.state == "AVAILABLE_SUPPORTING"
    ]


def _compatible_support(support, anchors, polarity):
    relevant = _relevant_anchors(anchors, polarity)
    return (
        bool(relevant)
        and support.polarity == polarity
        and all(a.support_ref in support.applies_to_supports for a in relevant)
    )
