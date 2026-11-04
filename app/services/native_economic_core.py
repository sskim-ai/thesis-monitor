"""Default-off economic admission layered over the native v2 reference contract.

The backend interpretation catalog is an independent trust root, not model prose
or a registration input. This version supports exact approved narratives only.
No implementation here approves an interpretation of real corporate evidence.
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, date, datetime
import re
from pathlib import Path
from typing import Literal

from pydantic import Field, model_validator

from app.services.accepted_decision_v2_runtime_service import (
    AcceptedV2EvidenceOwnership,
    AcceptedV2FundamentalCoreCandidate,
)
from app.services.cross_market_decision_engine_service import EvidenceClaim
from app.services.contract_schema_validation import validate_json_schema
from app.services.native_input_admission import (
    SHA,
    Identity,
    Closed,
    Consumer,
    UseAxis,
    UseState,
    TimeState,
    BackendAdmissionRegistry,
)
from app.services.native_authority_core import (
    NativeCoreRequest,
    NativeCoreAuthorityOutput,
    BoundEvidenceReference,
    accept_native_core_output,
    build_native_core_request,
)
from app.services.unified_snapshot_contract import digest
from app.services.reported_fact_use_policy import BackendReportedContextPolicy, ReportedContextGrant, ReportedContextScope

Role = Literal["BUY_DRIVER", "SELL_DRIVER", "DECISIVE_REASON", "HOLDER_REASON"]
CONTRACT = "native-economic-core-request-v3"
POLICY = "native-economic-core-conjunction-v1"


class InterpretationTemporalRule(Closed):
    field: Literal[
        "metric_as_of",
        "denominator_period_start",
        "denominator_period_end",
        "source_statement_period",
        "financial_period",
    ]
    allowed_states: tuple[TimeState, ...] = Field(min_length=1)
    maximum_age_days: int | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def no_conflict_or_retrieval_promotion(self):
        if set(self.allowed_states) & {TimeState.INVALID_CONFLICT, TimeState.RETRIEVAL_TIME_ONLY}:
            raise ValueError("UNQUALIFIED_TEMPORAL_STATE_CANNOT_AUTHORIZE_INTERPRETATION")
        return self


class EconomicInterpretation(Closed):
    interpretation_ref: Identity
    role: Role
    polarity: Literal["POSITIVE", "NEGATIVE", "MIXED", "UNCERTAIN"]
    uncertainty: Literal["QUALIFIED", "LIMITED", "UNRESOLVED"]
    use_axis: Literal["CORE_DIRECTION"] = "CORE_DIRECTION"
    claim: EvidenceClaim
    evidence: tuple[BoundEvidenceReference, ...] = Field(min_length=1)
    interpretation_owner_ref: Identity
    interpretation_receipt_sha256: SHA
    allowed_decisions: tuple[Literal["BUY", "HOLD", "SELL"], ...] = Field(min_length=1)
    allowed_holder_stances: tuple[Literal["HOLDABLE", "REVIEW", "REDUCE"], ...] = Field(
        min_length=1
    )
    allowed_confidences: tuple[Literal["LOW", "MEDIUM", "HIGH"], ...] = Field(min_length=1)
    temporal_rules: tuple[InterpretationTemporalRule, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def refs_and_polarity(self):
        if self.claim.evidence_refs != tuple(x.evidence_ref for x in self.evidence):
            raise ValueError("INTERPRETATION_SOURCE_REFS_MISMATCH")
        if self.role == "BUY_DRIVER" and self.polarity != "POSITIVE":
            raise ValueError("BUY_DRIVER_POLARITY_MISMATCH")
        if self.role == "SELL_DRIVER" and self.polarity != "NEGATIVE":
            raise ValueError("SELL_DRIVER_POLARITY_MISMATCH")
        if self.uncertainty == "UNRESOLVED":
            raise ValueError("UNRESOLVED_INTERPRETATION_NOT_DIRECTIONAL")
        fields = [r.field for r in self.temporal_rules]
        if len(fields) != len(set(fields)) or "metric_as_of" not in fields:
            raise ValueError("EXPLICIT_NON_DUPLICATE_METRIC_TEMPORAL_POLICY_REQUIRED")
        return self


class EconomicPolicyBundle(Closed):
    contract: Literal["backend-economic-interpretations-v1"] = "backend-economic-interpretations-v1"
    security_id: Identity
    generation_id: Identity
    source_generation_id: Identity
    backend_bundle_sha256: SHA
    policy_owner: Identity
    approval_version: Identity
    ownership: AcceptedV2EvidenceOwnership
    interpretations: tuple[EconomicInterpretation, ...]


class BackendEconomicPolicy:
    """Injected by backend composition, never deserialized from a caller request."""

    def __init__(self, bundle, *, expected_policy_sha256, registry):
        bundle = EconomicPolicyBundle.model_validate(bundle.model_dump(mode="json"))
        if digest(bundle.model_dump(mode="json")) != expected_policy_sha256:
            raise ValueError("INDEPENDENT_ECONOMIC_POLICY_ANCHOR_REQUIRED")
        b = registry.bundle
        if (
            bundle.security_id,
            bundle.generation_id,
            bundle.source_generation_id,
            bundle.backend_bundle_sha256,
            bundle.ownership.ticker,
        ) != (
            b.security_id,
            b.generation_id,
            b.source_generation_id,
            digest(b.model_dump(mode="json")),
            b.ticker,
        ):
            raise ValueError("ECONOMIC_POLICY_IDENTITY_MISMATCH")
        ids = [x.interpretation_ref for x in bundle.interpretations]
        if len(ids) != len(set(ids)):
            raise ValueError("DUPLICATE_INTERPRETATION")
        for row in bundle.interpretations:
            for use in row.evidence:
                receipt = registry.receipt(use.evidence_ref)
                expected = bound_reference(registry, use.evidence_ref)
                if use != expected or receipt.security_id != bundle.security_id:
                    raise ValueError("INTERPRETATION_OWNER_BINDING_MISMATCH")
                if not registry.allowed(use.evidence_ref, Consumer.CORE, UseAxis.CORE_DIRECTION):
                    raise ValueError("INTERPRETATION_DIRECTION_NOT_GRANTED")
        self._json = bundle.model_dump_json()

    @property
    def bundle(self):
        return EconomicPolicyBundle.model_validate_json(self._json)


class InvocationSpec(Closed):
    invocation_id: Identity
    execution_purpose: Literal["OFFLINE_CONTRACT_REPROOF", "ACCEPTED_CORE_MODEL_REPROOF"] = (
        "OFFLINE_CONTRACT_REPROOF"
    )
    security_id: Identity
    generation_id: Identity
    source_generation_id: Identity
    assessment_as_of: date
    intended_consumer: Consumer
    allowed_use_axes: tuple[UseAxis, ...] = Field(min_length=1)
    forbidden_use_axes: tuple[UseAxis, ...]

    @model_validator(mode="after")
    def partition(self):
        allowed, denied = set(self.allowed_use_axes), set(self.forbidden_use_axes)
        if (
            len(allowed) != len(self.allowed_use_axes)
            or len(denied) != len(self.forbidden_use_axes)
            or allowed & denied
            or allowed | denied != set(UseAxis)
        ):
            raise ValueError("EXACT_INVOCATION_AXIS_PARTITION_REQUIRED")
        if any(a.value.split("_", 1)[0] != self.intended_consumer.value for a in allowed):
            raise ValueError("INVOCATION_CROSS_CONSUMER_GRANT")
        return self


class InvocationScope(InvocationSpec):
    request_sha256: SHA
    prompt_sha256: SHA
    schema_sha256: SHA
    policy_sha256: SHA
    validator_sha256: SHA
    authority_sha256: SHA
    owner_sha256: SHA
    invocation_scope_sha256: SHA


class EconomicModelCandidate(Closed):
    candidate: AcceptedV2FundamentalCoreCandidate
    interpretation_refs: tuple[Identity, ...] = Field(min_length=4)


class EconomicRequest(Closed):
    contract: Literal["native-economic-core-request-v3"] = CONTRACT
    reference_request: NativeCoreRequest
    invocation: InvocationScope
    economic_policy_sha256: SHA | None
    prompt: str
    response_schema_json: str


class ReportedEconomicRequest(EconomicRequest):
    """Typed non-directional attachment; not an economic evidence/role grant."""
    contract: Literal["native-economic-core-reported-context-v4"] = "native-economic-core-reported-context-v4"
    reported_contexts: tuple[ReportedContextGrant, ...] = Field(min_length=1)
    reported_context_scope: ReportedContextScope


class ClaimEconomicRequest(EconomicRequest):
    contract: Literal["native-economic-claim-request-v5"] = "native-economic-claim-request-v5"
    claim_policy_sha256: SHA


def _decode_request(value):
    kind = {"native-economic-core-reported-context-v4": ReportedEconomicRequest,
            "native-economic-claim-request-v5": ClaimEconomicRequest}.get(value.get("contract"), EconomicRequest)
    return kind.model_validate(value)


def decode_model_candidate(value):
    from app.services.economic_claim_qualification import QualifiedEconomicModelCandidate

    kind = QualifiedEconomicModelCandidate if "economic_claims" in value else EconomicModelCandidate
    return kind.model_validate(value)


class BoundEconomicCandidate(Closed):
    contract: Literal["native-economic-core-candidate-v3"] = "native-economic-core-candidate-v3"
    request_sha256: SHA
    invocation_scope_sha256: SHA
    security_id: Identity
    generation_id: Identity
    source_generation_id: Identity
    model_candidate: EconomicModelCandidate
    references: NativeCoreAuthorityOutput


def decode_bound_candidate(value):
    if "economic_claims" in value.get("model_candidate", {}):
        from app.services.economic_claim_qualification import QualifiedEconomicModelCandidate

        class QualifiedBoundCandidate(BoundEconomicCandidate):
            model_candidate: QualifiedEconomicModelCandidate

        return QualifiedBoundCandidate.model_validate(value)
    return BoundEconomicCandidate.model_validate(value)


class OfflineEconomicAcceptance(Closed):
    contract: Literal["native-economic-offline-acceptance-v1"] = (
        "native-economic-offline-acceptance-v1"
    )
    provenance: Literal["TEST_CANDIDATE_NOT_ACCEPTED_MODEL_JUDGMENT"] = (
        "TEST_CANDIDATE_NOT_ACCEPTED_MODEL_JUDGMENT"
    )
    candidate: AcceptedV2FundamentalCoreCandidate
    request_sha256: SHA
    invocation_scope_sha256: SHA
    source_generation_id: Identity
    reference_output: NativeCoreAuthorityOutput
    economic_policy_sha256: SHA
    same_generation_model_judgment: Literal[False] = False
    downstream_decision_handoff: Literal[False] = False


class EconomicAdmissionGap(Closed):
    contract: Literal["native-economic-admission-gap-v1"] = "native-economic-admission-gap-v1"
    decision_axis: Literal["CORE"] = "CORE"
    security_id: Identity
    generation_id: Identity
    source_generation_id: Identity
    request_sha256: SHA
    missing_interpretation_roles: tuple[Role, ...]
    preserved_admitted_refs: tuple[Identity, ...]
    reason: Literal["MISSING_QUALIFIED_ECONOMIC_INTERPRETATIONS"] = (
        "MISSING_QUALIFIED_ECONOMIC_INTERPRETATIONS"
    )
    accepted_abstention: Literal[False] = False
    accepted_directional_judgment: Literal[False] = False


def bound_reference(registry, ref):
    receipt = registry.receipt(ref)
    return BoundEvidenceReference(
        evidence_ref=ref,
        owner_ref=receipt.owner_ref,
        admission_sha256=digest(receipt.model_dump(mode="json")),
        authority_sha256=receipt.authority_sha256,
        temporal_sha256=receipt.temporal_sha256,
    )


def _validator_sha():
    from app.services import native_authority_core, native_input_admission
    from app.services import accepted_decision_v2_runtime_service as native
    from app.services import directional_balance_service, expectation_valuation_interaction_service
    from app.services import stage2_maturity_polarity_adapter_service

    return digest(
        [
            hashlib.sha256(Path(p).read_bytes()).hexdigest()
            for p in (
                __file__,
                Path(__file__).with_name("native_accepted_ownership.py"),
                Path(__file__).with_name("reported_fact_use_policy.py"),
                Path(__file__).with_name("economic_claim_qualification.py"),
                native.__file__,
                native_authority_core.__file__,
                native_input_admission.__file__,
                directional_balance_service.__file__,
                expectation_valuation_interaction_service.__file__,
                stage2_maturity_polarity_adapter_service.__file__,
            )
        ]
    )


def _interpretation_eligible(row, reference, spec):
    if (
        spec.intended_consumer != Consumer.CORE
        or UseAxis.CORE_DIRECTION not in spec.allowed_use_axes
        or UseAxis.CORE_VISIBILITY not in spec.allowed_use_axes
        or not set(row.claim.evidence_refs) <= set(reference.context.request_evidence_membership)
    ):
        return False
    metrics = {m.metric_ref: m for m in reference.context.metric_authority_envelopes}
    for ref in row.claim.evidence_refs:
        metric = metrics.get(ref)
        if metric is None or metric.use(UseAxis.CORE_VISIBILITY) != UseState.ALLOWED:
            return False
        temporal = {t.field: t for t in metric.temporal}
        for rule in row.temporal_rules:
            field = temporal[rule.field]
            if field.state not in rule.allowed_states:
                return False
            if field.value is not None:
                try:
                    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", field.value):
                        observed = date.fromisoformat(field.value)
                    elif re.fullmatch(
                        r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})",
                        field.value,
                    ):
                        observed = (
                            datetime.fromisoformat(field.value.replace("Z", "+00:00"))
                            .astimezone(UTC)
                            .date()
                        )
                    else:
                        return False
                except (ValueError, OverflowError):
                    return False
                age = (spec.assessment_as_of - observed).days
                if age < 0 or (rule.maximum_age_days is not None and age > rule.maximum_age_days):
                    return False
    return True


def _request(reference, spec, policy, reported_contexts=(), reported_context_scope=None):
    c = reference.context
    if (spec.security_id, spec.generation_id, spec.source_generation_id) != (
        c.security_id,
        c.generation_id,
        c.source_generation_id,
    ):
        raise ValueError("INVOCATION_IDENTITY_MISMATCH")
    rows = (
        ()
        if policy is None
        else tuple(
            r for r in policy.bundle.interpretations if _interpretation_eligible(r, reference, spec)
        )
    )
    qualified_claims = getattr(policy, "claim_contract", None) is not None
    if qualified_claims and reported_contexts:
        raise ValueError("CONTEXT_RECEIPT_NOT_ECONOMIC_CLAIM_AUTHORITY")
    if qualified_claims:
        from app.services.economic_claim_qualification import QualifiedEconomicModelCandidate
        schema = QualifiedEconomicModelCandidate.model_json_schema()
    else:
        schema = EconomicModelCandidate.model_json_schema()
    schema["$defs"]["AcceptedV2FundamentalCoreCandidate"]["properties"]["ticker"]["const"] = (
        c.ticker
    )
    if not qualified_claims:
        schema["properties"]["interpretation_refs"]["items"]["enum"] = [
            r.interpretation_ref for r in rows
        ]
    schema["$defs"]["EvidenceClaim"]["properties"]["evidence_refs"]["items"]["enum"] = list(
        c.request_evidence_membership
    )
    prompt = (
        "Native economic Core v3, offline contract reproof only. Preserve the existing "
        "BUY/HOLD/SELL balance policy and independent fundamental Holder stance. "
        "Price and technical inputs are invisible. Use only backend-approved interpretations "
        "with exact roles, narratives and refs. No unsupported numeric/date/prose claims. "
        "Copy balance_summary as the buy-driver texts followed by sell-driver texts joined by ' / '. "
        "If required economic interpretations are absent, no economic candidate is admissible; "
        "HOLD is not abstention. Reference admission is not economic acceptance.\n"
        + json.dumps(
            dict(
                invocation=spec.model_dump(mode="json"),
                canonical_ticker=c.ticker,
                interpretations=[r.model_dump(mode="json") for r in rows],
            ),
            sort_keys=True,
            separators=(",", ":"),
        )
    )
    if qualified_claims:
        from app.services.directional_balance_service import ORDINAL_CALIBRATION_PROMPT
        prompt = (
            "Native typed economic-claim qualification, offline only. Model proposes economic "
            "roles and synthesis; backend checks exact admitted support and existing Core semantics. "
            "No numeric growth-to-decision rule. Price/Timing is invisible. "
            "Use typed claim proposals and the bounded renderer; arbitrary prose/numbers do not "
            "create source authority. Missing required roles is an admission gap, not abstention.\n"
            + ORDINAL_CALIBRATION_PROMPT + "\n" + json.dumps(dict(
                invocation=spec.model_dump(mode="json"),
                policy=policy.bundle.model_dump(mode="json")), sort_keys=True, separators=(",", ":"))
        )
    if reported_contexts:
        prompt += (
            "\nNON_DIRECTIONAL_REPORTED_FACT_CONTEXT: sealed historical reporting only. "
            "These attachments grant CORE_REPORTED_CONTEXT, not valuation or direction. "
            "They cannot satisfy BUY_DRIVER, SELL_DRIVER, DECISIVE_REASON or HOLDER_REASON. "
            "Unknown materiality, cause, recurrence and interpretation confidence remain unknown.\n"
            + json.dumps(dict(scope=reported_context_scope.model_dump(mode="json"),
                contexts=[g.model_dump(mode="json") for g in reported_contexts]), sort_keys=True, separators=(",", ":"))
        )
    policy_sha = digest(
        dict(
            version=POLICY,
            economic_policy=(policy.bundle.model_dump(mode="json") if policy else None),
        )
    )
    request_type = ClaimEconomicRequest if qualified_claims else ReportedEconomicRequest if reported_contexts else EconomicRequest
    basis = dict(
        contract="native-economic-claim-request-v5" if qualified_claims else "native-economic-core-reported-context-v4" if reported_contexts else CONTRACT,
        reference_request=reference.model_dump(mode="json"),
        invocation=spec.model_dump(mode="json"),
        prompt=prompt,
        schema=schema,
        policy_sha256=policy_sha,
        validator_sha256=_validator_sha(),
    )
    fields = dict(
        **spec.model_dump(mode="json"),
        request_sha256=digest(basis),
        prompt_sha256=digest(prompt),
        schema_sha256=digest(schema),
        policy_sha256=policy_sha,
        validator_sha256=basis["validator_sha256"],
        authority_sha256=reference.authorization.authority_sha256,
        owner_sha256=reference.authorization.owner_sha256,
    )
    scope = InvocationScope(**fields, invocation_scope_sha256=digest(fields))
    return request_type(
        reference_request=reference,
        invocation=scope,
        economic_policy_sha256=digest(policy.bundle.model_dump(mode="json")) if policy else None,
        prompt=prompt,
        response_schema_json=json.dumps(schema, sort_keys=True, separators=(",", ":")),
        **({"reported_contexts": reported_contexts, "reported_context_scope":reported_context_scope} if reported_contexts else {}),
        **({"claim_policy_sha256": policy.bundle.rule_sha256} if qualified_claims else {}),
    )


class BackendInvocation:
    """Backend-retained invocation, not accepted from model/caller JSON.

    Request identity includes the scope specification; the final scope seal binds
    that request digest. The two-stage digest avoids a circular self-hash.
    """

    def __init__(self, reference_request, *, registry, spec, economic_policy=None,
                 reported_context_policy=None, reported_contexts=(), reported_context_scope=None):
        if not isinstance(registry, BackendAdmissionRegistry):
            raise ValueError("BACKEND_REGISTRY_REQUIRED")
        if economic_policy is not None and not isinstance(economic_policy, BackendEconomicPolicy):
            raise ValueError("BACKEND_ECONOMIC_POLICY_REQUIRED")
        rebuilt = build_native_core_request(reference_request.context, registry=registry)
        if reference_request != rebuilt:
            raise ValueError("REJECT_REQUEST_IDENTITY_BINDING")
        spec = InvocationSpec.model_validate(spec.model_dump(mode="json"))
        if economic_policy is not None:
            if getattr(economic_policy, "claim_contract", None) is not None:
                economic_policy.verify_backend(registry)
            else:
                b = economic_policy.bundle
                economic_policy = BackendEconomicPolicy(
                    b, expected_policy_sha256=digest(b.model_dump(mode="json")), registry=registry
                )
        self._registry, self._policy = registry, economic_policy
        if bool(reported_contexts) != (reported_context_policy is not None):
            raise ValueError("CONTEXT_GRANTS_AND_BACKEND_POLICY_REQUIRED")
        if bool(reported_contexts) != (reported_context_scope is not None):
            raise ValueError("EXPLICIT_REPORTED_CONTEXT_INVOCATION_SCOPE_REQUIRED")
        if reported_contexts and not isinstance(reported_context_policy, BackendReportedContextPolicy):
            raise ValueError("BACKEND_REPORTED_CONTEXT_POLICY_REQUIRED")
        self._reported_policy = reported_context_policy
        self._reported_contexts = tuple(reported_contexts)
        self._reported_scope = ReportedContextScope.model_validate(
            reported_context_scope.model_dump(mode="json")) if reported_context_scope is not None else None
        self._verify_reported_contexts(spec)
        self._spec_json = spec.model_dump_json()
        self._request_json = _request(rebuilt, spec, economic_policy, self._reported_contexts, self._reported_scope).model_dump_json()

    def _verify_reported_contexts(self, spec):
        if not self._reported_contexts:
            return
        if spec.intended_consumer != Consumer.CORE or UseAxis.CORE_VISIBILITY not in spec.allowed_use_axes:
            raise ValueError("REPORTED_CONTEXT_CONSUMER_SCOPE_MISMATCH")
        scope = self._reported_scope
        if (scope.invocation_id, scope.security_id, scope.generation_id, scope.source_generation_id,
                scope.assessment_as_of, scope.allowed_use_axes, scope.source_envelope_sha256) != (
                spec.invocation_id, spec.security_id, spec.generation_id, spec.source_generation_id,
                spec.assessment_as_of, ("CORE_REPORTED_CONTEXT",), self._registry.bundle.source_envelope_sha256):
            raise ValueError("REPORTED_CONTEXT_SCOPE_BINDING_MISMATCH")
        refs = [g.grant_id for g in self._reported_contexts]
        if len(refs) != len(set(refs)):
            raise ValueError("DUPLICATE_REPORTED_CONTEXT_GRANT")
        for grant in self._reported_contexts:
            if any(f.ticker != self._registry.bundle.ticker for f in grant.facts):
                raise ValueError("CONTEXT_REGISTERED_TICKER_MISMATCH")
            if (grant.market, grant.source_envelope_sha256) != (self._registry.bundle.market, scope.source_envelope_sha256):
                raise ValueError("CONTEXT_REGISTERED_SOURCE_ENVELOPE_MISMATCH")
            if any(f.filed > spec.assessment_as_of or f.period_end > spec.assessment_as_of for f in grant.facts):
                raise ValueError("CONTEXT_FACT_NOT_AVAILABLE_AT_ASSESSMENT")
            self._reported_policy.verify(grant, invocation_id=spec.invocation_id,
                security_id=spec.security_id, execution_generation_id=spec.generation_id,
                source_generation_id=spec.source_generation_id)

    @property
    def request(self):
        return _decode_request(json.loads(self._request_json))

    def verify(self, request):
        if getattr(self._policy, "claim_contract", None) is not None:
            self._policy.verify_backend(self._registry)
        request = _decode_request(request.model_dump(mode="json"))
        pinned = self.request
        rebuilt_ref = build_native_core_request(
            pinned.reference_request.context, registry=self._registry
        )
        spec = InvocationSpec.model_validate_json(self._spec_json)
        self._verify_reported_contexts(spec)
        expected = _request(rebuilt_ref, spec, self._policy, self._reported_contexts, self._reported_scope)
        if request != pinned or pinned != expected:
            raise ValueError("REJECT_REQUEST_IDENTITY_BINDING")
        return request

    def accept_references(self, output, request):
        request = self.verify(request)
        output = NativeCoreAuthorityOutput.model_validate(
            output.model_dump(mode="json")
            if isinstance(output, NativeCoreAuthorityOutput)
            else output
        )
        for claim in output.claims:
            if (
                claim.consumer != request.invocation.intended_consumer
                or claim.use_axis not in request.invocation.allowed_use_axes
            ):
                raise ValueError("REJECT_INVOCATION_CONSUMER_SCOPE")
        return accept_native_core_output(
            output,
            request.reference_request,
            registry=self._registry,
            expected_request_sha256=request.reference_request.authorization.request_sha256,
        )


def _claim_rows(candidate):
    return [
        *(("BUY_DRIVER", c) for c in candidate.buy_drivers),
        *(("SELL_DRIVER", c) for c in candidate.sell_drivers),
        ("DECISIVE_REASON", candidate.decisive_reason),
        ("HOLDER_REASON", candidate.holder_axis.reason),
    ]


def materialize_economic_candidate(value, request, *, invocation):
    """Backend hashes only; typed support and existing semantic gates run below.

    This is not independent proof of free-form economic entailment or truth.
    """
    invocation.verify(request)
    value = decode_model_candidate(value)
    claims = [
        dict(
            consumer="CORE",
            use_axis="CORE_DIRECTION",
            evidence=[bound_reference(invocation._registry, r) for r in c.evidence_refs],
        )
        for _, c in _claim_rows(value.candidate)
    ]
    c = request.reference_request.context
    raw = dict(
        request_sha256=request.invocation.request_sha256,
        invocation_scope_sha256=request.invocation.invocation_scope_sha256,
        security_id=c.security_id,
        generation_id=c.generation_id,
        source_generation_id=c.source_generation_id,
        model_candidate=value.model_dump(mode="json"),
        references=NativeCoreAuthorityOutput(
            request_sha256=request.reference_request.authorization.request_sha256,
            security_id=c.security_id,
            generation_id=c.generation_id,
            source_generation_id=c.source_generation_id,
            claims=claims,
        ),
    )
    return decode_bound_candidate(raw)


def accept_economic_candidate(output, request, *, invocation):
    """One AND path: backend invocation, native reference AND economic invariants."""
    if not isinstance(invocation, BackendInvocation):
        raise ValueError("BACKEND_PINNED_INVOCATION_REQUIRED")
    request = invocation.verify(request)
    output = decode_bound_candidate(
        output.model_dump(mode="json") if isinstance(output, BoundEconomicCandidate) else output
    )
    c = request.reference_request.context
    if (
        output.request_sha256,
        output.invocation_scope_sha256,
        output.security_id,
        output.generation_id,
        output.source_generation_id,
    ) != (
        request.invocation.request_sha256,
        request.invocation.invocation_scope_sha256,
        c.security_id,
        c.generation_id,
        c.source_generation_id,
    ):
        raise ValueError("REJECT_OUTPUT_IDENTITY_BINDING")
    invocation.accept_references(output.references, request)
    if request.invocation.intended_consumer != Consumer.CORE:
        raise ValueError("REJECT_INVOCATION_CONSUMER_SCOPE")
    if validate_json_schema(
        output.model_candidate.model_dump(mode="json"), json.loads(request.response_schema_json)
    ):
        raise ValueError("REJECT_ECONOMIC_REQUEST_SCHEMA")
    policy = invocation._policy
    if policy is None:
        raise ValueError("ECONOMIC_INTERPRETATION_AUTHORITY_MISSING_NO_ABSTENTION_POLICY")
    rows = _claim_rows(output.model_candidate.candidate)
    qualified_claims = getattr(policy, "claim_contract", None) is not None
    if qualified_claims:
        policy.validate_model(output.model_candidate, request=request, invocation=invocation)
    by_id = {r.interpretation_ref: r for r in policy.bundle.interpretations}
    refs = output.model_candidate.interpretation_refs
    if len(rows) != len(refs) or len(output.references.claims) != len(rows):
        raise ValueError("CLAIM_OWNERSHIP_COVERAGE_MISMATCH")
    for (role, claim), ref, bound in zip(rows, refs, output.references.claims, strict=True):
        if qualified_claims:
            if (bound.consumer != Consumer.CORE or bound.use_axis != UseAxis.CORE_DIRECTION
                    or tuple(b.evidence_ref for b in bound.evidence) != claim.evidence_refs):
                raise ValueError("CLAIM_REFERENCE_SCOPE_MISMATCH")
            continue
        interpretation = by_id.get(ref)
        if (
            interpretation is None
            or interpretation.role != role
            or interpretation.claim != claim
            or interpretation.evidence != bound.evidence
            or bound.consumer != Consumer.CORE
            or bound.use_axis != UseAxis.CORE_DIRECTION
        ):
            raise ValueError("REJECT_UNSUPPORTED_ECONOMIC_INTERPRETATION")
    core = output.model_candidate.candidate
    spec = InvocationSpec.model_validate_json(invocation._spec_json)
    for ref in refs:
        if qualified_claims:
            continue
        row = by_id[ref]
        if not _interpretation_eligible(row, request.reference_request, spec):
            raise ValueError("REJECT_INTERPRETATION_TEMPORAL_OR_INVOCATION_USE")
        if (
            core.decision not in row.allowed_decisions
            or core.confidence not in row.allowed_confidences
            or core.holder_axis.stance not in row.allowed_holder_stances
        ):
            raise ValueError("REJECT_INTERPRETATION_CONCLUSION_COMPATIBILITY")
    if core.balance_summary != " / ".join(x.text for x in (*core.buy_drivers, *core.sell_drivers)):
        raise ValueError("REJECT_UNOWNED_BALANCE_NARRATIVE")
    from app.services.accepted_decision_v2_runtime_service import (
        validate_accepted_v2_fundamental_core,
    )

    errors = validate_accepted_v2_fundamental_core(core, policy.bundle.ownership)
    if errors:
        raise ValueError("REJECT_ECONOMIC_SEMANTICS:" + ",".join(errors))
    return OfflineEconomicAcceptance(
        candidate=core,
        request_sha256=output.request_sha256,
        invocation_scope_sha256=output.invocation_scope_sha256,
        source_generation_id=output.source_generation_id,
        reference_output=output.references,
        economic_policy_sha256=request.economic_policy_sha256,
    )


def economic_batch_output(outputs, requests, *, invocations):
    if len(outputs) != len(requests) or len(requests) != len(invocations) or not outputs:
        raise ValueError("ECONOMIC_BATCH_SCOPE_MISMATCH")
    if len({r.invocation.invocation_id for r in requests}) != len(requests):
        raise ValueError("DUPLICATE_INVOCATION")
    if (
        len(
            {
                (
                    r.invocation.generation_id,
                    r.invocation.source_generation_id,
                    r.reference_request.context.market,
                )
                for r in requests
            }
        )
        != 1
    ):
        raise ValueError("ECONOMIC_BATCH_GENERATION_MARKET_MISMATCH")
    if len({r.invocation.security_id for r in requests}) != len(requests):
        raise ValueError("DUPLICATE_BATCH_SECURITY")
    return tuple(
        accept_economic_candidate(o, r, invocation=i)
        for o, r, i in zip(outputs, requests, invocations, strict=True)
    )


def downstream_model_judgment_handoff(_offline_receipt):
    raise ValueError("OFFLINE_TEST_CANDIDATE_NOT_ACCEPTED_MODEL_JUDGMENT")


def economic_admission_gap(request, *, invocation):
    """Missing directional owners are a contract gap, not a fabricated HOLD/abstention."""
    request = invocation.verify(request)
    spec = InvocationSpec.model_validate_json(invocation._spec_json)
    roles = (
        set()
        if invocation._policy is None
        else {
            row.role
            for row in invocation._policy.bundle.interpretations
            if _interpretation_eligible(row, request.reference_request, spec)
        }
    )
    missing = tuple(
        r
        for r in ("BUY_DRIVER", "SELL_DRIVER", "DECISIVE_REASON", "HOLDER_REASON")
        if r not in roles
    )
    if not missing:
        return None
    return EconomicAdmissionGap(
        security_id=request.invocation.security_id,
        generation_id=request.invocation.generation_id,
        source_generation_id=request.invocation.source_generation_id,
        request_sha256=request.invocation.request_sha256,
        missing_interpretation_roles=missing,
        preserved_admitted_refs=request.reference_request.context.request_evidence_membership,
    )
