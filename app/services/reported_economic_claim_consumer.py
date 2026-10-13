"""Role-level reported fact-v2 transport, never a complete Core judgment."""

from typing import Literal
from pathlib import Path
import hashlib
from pydantic import Field

from app.services.native_input_admission import Closed, Identity, SHA
from app.services.economic_claim_qualification import EconomicClaimProposal
from app.services.cross_market_decision_engine_service import EvidenceClaim
from app.services.reported_fact_owner import ReportedFact
from app.services.unified_snapshot_contract import digest


class ReportedRoleCandidate(Closed):
    contract: Literal["reported-economic-role-candidate-v1"] = "reported-economic-role-candidate-v1"
    proposal: EconomicClaimProposal
    confidence: Literal["LOW"]
    provenance: Literal["TEST_CANDIDATE_NOT_ACCEPTED_MODEL_JUDGMENT"] = (
        "TEST_CANDIDATE_NOT_ACCEPTED_MODEL_JUDGMENT"
    )


class ReportedEconomicRoleRequest(Closed):
    """An offline role subrequest, not a replacement full-Core output schema."""

    contract: Literal["reported-economic-role-request-v1"] = "reported-economic-role-request-v1"
    native_request_sha256: SHA
    native_prompt_sha256: SHA
    native_schema_sha256: SHA
    native_invocation_sha256: SHA
    role_schema_sha256: SHA
    role_validator_sha256: SHA
    property_admission_sha256: SHA
    execution_purpose: Literal["OFFLINE_CONTRACT_REPROOF"] = "OFFLINE_CONTRACT_REPROOF"
    consumer: Literal["CORE"] = "CORE"
    use_axis: Literal["CORE_DIRECTION"] = "CORE_DIRECTION"
    required_role: Literal["BUY_DRIVER"] = "BUY_DRIVER"
    result_scope: Literal["ROLE_ELIGIBILITY_ONLY_NOT_COMPLETE_CORE"] = (
        "ROLE_ELIGIBILITY_ONLY_NOT_COMPLETE_CORE"
    )


class ReportedNarrativeExcerpt(Closed):
    category: Literal["RISK", "MECHANISM", "MITIGATION"]
    start_byte: int = Field(ge=0, strict=True)
    end_byte: int = Field(gt=0, strict=True)
    raw_sha256: SHA
    text: str = Field(min_length=1, max_length=5000)


class ReportedRiskRoleRequest(ReportedEconomicRoleRequest):
    contract: Literal["reported-risk-role-request-v1"] = "reported-risk-role-request-v1"
    required_role: Literal["SELL_DRIVER"] = "SELL_DRIVER"
    narrative_admission_sha256: SHA
    narrative_source_sha256: SHA
    narrative_span_sha256: tuple[SHA, ...]
    narrative_context: tuple[ReportedNarrativeExcerpt, ...] = Field(min_length=3, max_length=12)


class ReportedSynthesisRoleRequest(ReportedRiskRoleRequest):
    contract: Literal["reported-balanced-synthesis-role-request-v1"] = (
        "reported-balanced-synthesis-role-request-v1"
    )
    required_role: Literal["DECISIVE_REASON"] = "DECISIVE_REASON"
    anchor_admission_sha256: SHA
    risk_admission_sha256: SHA
    anchor_review_sha256: SHA
    risk_review_sha256: SHA
    original_owner_execution_generation_id: Identity
    anchor_execution_generation_id: Identity
    risk_execution_generation_id: Identity


def is_reported_property_policy(policy):
    from app.services.reviewed_economic_property import BackendReportedPropertyClaimPolicy
    from app.services.reviewed_narrative_risk import BackendNarrativeRiskClaimPolicy
    from app.services.reviewed_balanced_synthesis import BackendSynthesisClaimPolicy

    return type(policy) in {
        BackendReportedPropertyClaimPolicy, BackendNarrativeRiskClaimPolicy,
        BackendSynthesisClaimPolicy,
    }


def role_types(policy):
    from app.services.reviewed_narrative_risk import BackendNarrativeRiskClaimPolicy
    from app.services.reviewed_balanced_synthesis import BackendSynthesisClaimPolicy

    if not is_reported_property_policy(policy):
        raise ValueError("REPORTED_ECONOMIC_PROPERTY_POLICY_REQUIRED")
    if type(policy) is BackendNarrativeRiskClaimPolicy:
        return ReportedRiskRoleRequest, ReportedRiskClaimPacket, ReportedRiskClaimOwnership
    if type(policy) is BackendSynthesisClaimPolicy:
        return ReportedSynthesisRoleRequest, ReportedSynthesisClaimPacket, ReportedSynthesisClaimOwnership
    return ReportedEconomicRoleRequest, ReportedEconomicClaimPacket, ReportedEconomicClaimOwnership


def role_validator_sha256(*, narrative=False, synthesis=False):
    root = Path(__file__).parent
    return digest(
        {
            name: hashlib.sha256((root / name).read_bytes()).hexdigest()
            for name in (
                "reported_economic_claim_consumer.py",
                "reviewed_economic_property.py",
                "economic_claim_qualification.py",
                "native_accepted_ownership.py",
                "native_economic_core.py",
                "native_owner_session.py",
                "production_monitoring_session.py",
            )
            + (("reviewed_narrative_risk.py",) if narrative else ())
            + (("reviewed_balanced_synthesis.py",) if synthesis else ())
        }
    )


def _build_role_request(invocation):
    request_type, _, _ = role_types(invocation._policy)
    scope = invocation.verify(invocation.request).invocation
    policy = invocation._policy
    admission = policy.reported_property_owner.resolve(policy._property)
    narrative = (
        policy.narrative_packet_binding()
        if request_type in {ReportedRiskRoleRequest, ReportedSynthesisRoleRequest}
        else {}
    )
    if request_type is ReportedSynthesisRoleRequest:
        narrative.update(policy.synthesis_packet_binding())
    return request_type(
        native_request_sha256=scope.request_sha256,
        native_prompt_sha256=scope.prompt_sha256,
        native_schema_sha256=scope.schema_sha256,
        native_invocation_sha256=scope.invocation_scope_sha256,
        role_schema_sha256=digest(ReportedRoleCandidate.model_json_schema()),
        role_validator_sha256=(
            role_validator_sha256(
                narrative=True, synthesis=request_type is ReportedSynthesisRoleRequest
            )
            if request_type in {ReportedRiskRoleRequest, ReportedSynthesisRoleRequest}
            else role_validator_sha256()
        ),
        property_admission_sha256=admission.admission_sha256,
        execution_purpose=scope.execution_purpose,
        **narrative,
    )


def reported_role_request(invocation):
    frozen = getattr(invocation, "_reported_role_request_json", None)
    current = _build_role_request(invocation)
    if frozen != current.model_dump_json():
        raise ValueError("REPORTED_ROLE_REQUEST_SCHEMA_OR_VALIDATOR_CHANGED")
    return current


class ReportedEconomicClaimPacket(Closed):
    contract: Literal["native-reported-economic-claim-packet-v1"] = (
        "native-reported-economic-claim-packet-v1"
    )
    claim: EvidenceClaim
    candidate: ReportedRoleCandidate
    role: Literal["BUY_DRIVER"] = "BUY_DRIVER"
    security_id: Identity
    generation_id: Identity
    source_generation_id: Identity
    invocation_sha256: SHA
    request_sha256: SHA
    role_schema_sha256: SHA
    role_request_sha256: SHA
    property_admission_sha256: SHA
    review_sha256: SHA
    claim_eligibility_sha256: SHA
    facts: tuple[ReportedFact, ...]
    source_kind: Literal["REAL_SEALED_SOURCE", "SYNTHETIC_REVIEW_FIXTURE"]
    interpretation_scope: Literal["HISTORICAL_REPORTED_OPERATING_PERFORMANCE_ONLY"] = (
        "HISTORICAL_REPORTED_OPERATING_PERFORMANCE_ONLY"
    )
    causal_recurrence_independence_currentness: Literal["NOT_AUTHORIZED"] = "NOT_AUTHORIZED"
    accepted_Core: Literal[False] = False
    complete_economic_Stage2: Literal[False] = False


class ReportedEconomicClaimOwnership(Closed):
    contract: Literal["backend-reported-economic-claim-ownership-fact-v2"] = (
        "backend-reported-economic-claim-ownership-fact-v2"
    )
    output_id: Identity
    request_sha256: SHA
    invocation_sha256: SHA
    property_admission_sha256: SHA
    claim_eligibility_sha256: SHA
    packet_sha256: SHA
    role_schema_sha256: SHA
    role_request_sha256: SHA
    raw_response_sha256: SHA
    attempt_id: Identity
    attempt_number: int
    security_id: Identity
    generation_id: Identity
    source_generation_id: Identity
    consumer: Literal["CORE"] = "CORE"
    use_axis: Literal["CORE_DIRECTION"] = "CORE_DIRECTION"
    role: Literal["BUY_DRIVER"] = "BUY_DRIVER"
    accepted_model_judgment: Literal[False] = False


class ReportedRiskClaimPacket(ReportedEconomicClaimPacket):
    contract: Literal["native-reported-risk-claim-packet-v1"] = (
        "native-reported-risk-claim-packet-v1"
    )
    role: Literal["SELL_DRIVER"] = "SELL_DRIVER"
    interpretation_scope: Literal["HISTORICAL_DISCLOSED_CONDITIONAL_BUSINESS_RISK"] = (
        "HISTORICAL_DISCLOSED_CONDITIONAL_BUSINESS_RISK"
    )
    narrative_admission_sha256: SHA
    narrative_source_sha256: SHA
    narrative_span_sha256: tuple[SHA, ...]
    narrative_context: tuple[ReportedNarrativeExcerpt, ...] = Field(min_length=3, max_length=12)


class ReportedRiskClaimOwnership(ReportedEconomicClaimOwnership):
    contract: Literal["backend-reported-risk-claim-ownership-fact-v2"] = (
        "backend-reported-risk-claim-ownership-fact-v2"
    )
    role: Literal["SELL_DRIVER"] = "SELL_DRIVER"


class ReportedSynthesisClaimPacket(ReportedRiskClaimPacket):
    contract: Literal["native-reported-balanced-synthesis-packet-v1"] = (
        "native-reported-balanced-synthesis-packet-v1"
    )
    role: Literal["DECISIVE_REASON"] = "DECISIVE_REASON"
    interpretation_scope: Literal["HISTORICAL_BALANCED_ROLE_NOT_DIRECTIONAL_ADJUDICATION"] = (
        "HISTORICAL_BALANCED_ROLE_NOT_DIRECTIONAL_ADJUDICATION"
    )
    anchor_admission_sha256: SHA
    risk_admission_sha256: SHA
    anchor_review_sha256: SHA
    risk_review_sha256: SHA
    original_owner_execution_generation_id: Identity
    anchor_execution_generation_id: Identity
    risk_execution_generation_id: Identity


class ReportedSynthesisClaimOwnership(ReportedEconomicClaimOwnership):
    contract: Literal["backend-reported-balanced-synthesis-ownership-fact-v2"] = (
        "backend-reported-balanced-synthesis-ownership-fact-v2"
    )
    role: Literal["DECISIVE_REASON"] = "DECISIVE_REASON"


def validate_reported_role(candidate, *, invocation):
    _, packet_type, _ = role_types(invocation._policy)
    request = invocation.verify(invocation.request)
    candidate = ReportedRoleCandidate.model_validate(candidate.model_dump(mode="json"))
    policy = invocation._policy
    admission = policy.reported_property_owner.resolve(policy._property)
    if candidate.confidence not in admission.review.allowed_confidences:
        raise ValueError("REVIEWED_CLAIM_CONFIDENCE_NOT_AUTHORIZED")
    claim, eligibility, _ = policy.qualify(
        candidate.proposal, request=request, invocation=invocation
    )
    scope = request.invocation
    extra = {}
    if packet_type in {ReportedRiskClaimPacket, ReportedSynthesisClaimPacket}:
        extra = policy.narrative_packet_binding()
    if packet_type is ReportedSynthesisClaimPacket:
        extra.update(policy.synthesis_packet_binding())
    return packet_type(
        claim=claim,
        candidate=candidate,
        security_id=scope.security_id,
        generation_id=scope.generation_id,
        source_generation_id=scope.source_generation_id,
        invocation_sha256=scope.invocation_scope_sha256,
        request_sha256=scope.request_sha256,
        role_schema_sha256=digest(ReportedRoleCandidate.model_json_schema()),
        role_request_sha256=digest(reported_role_request(invocation).model_dump(mode="json")),
        property_admission_sha256=admission.admission_sha256,
        review_sha256=admission.review_artifact_sha256,
        claim_eligibility_sha256=digest(eligibility.model_dump(mode="json")),
        facts=admission.review.facts,
        source_kind=admission.review.source_kind,
        **extra,
    )


def consume_native_reported_economic_claim(parent, invocation_id, receipt, packet):
    """Actual opt-in session consumer, not a prompt-only or serialized echo proof."""
    # Close must not invalidate the parent between capability lookup and use.
    with parent._lock:
        inv = parent.invocation(invocation_id)
        return parent._registry.consume_reported_claim(receipt, invocation=inv, packet=packet)
