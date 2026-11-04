"""Opt-in reported context policy. Authenticity never grants an economic role.

The backend policy capability retains the original fact owner and issues a new
use/lineage grant. It does not rewrite the earlier DISPLAY-only owner receipt.
"""
from __future__ import annotations

import hashlib
from datetime import date
from pathlib import Path
import secrets
from typing import Literal

from app.services.native_input_admission import Closed, Identity, SHA
from app.services.reported_fact_owner import BackendReportedFactOwner, ReportedFact, ReportedPolicyResult
from app.services.unified_snapshot_contract import digest

POLICY = "reported-fact-governed-context-v1"
AUTHORITY = "REV63P-R15:TASK_AUTHORIZED_OFFLINE_POLICY"
AXIS = "CORE_REPORTED_CONTEXT"


def policy_sha():
    return digest(dict(version=POLICY, authority=AUTHORITY,
                       implementation=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()))


class ReportedContextGrant(Closed):
    contract: Literal["reported-fact-context-grant-v2"] = "reported-fact-context-grant-v2"
    grant_id: Identity
    policy_version: Literal["reported-fact-governed-context-v1"] = POLICY
    policy_sha256: SHA
    issuing_authority: Literal["REV63P-R15:TASK_AUTHORIZED_OFFLINE_POLICY"] = AUTHORITY
    invocation_id: Identity
    security_id: Identity
    market: Literal["us", "kr"]
    source_envelope_sha256: SHA
    source_generation_id: Identity
    owner_execution_generation_id: Identity
    execution_generation_id: Identity
    lineage_rule: Literal["SEALED_FACT_REUSE_NOT_FRESH_OBSERVATION"] = "SEALED_FACT_REUSE_NOT_FRESH_OBSERVATION"
    consumer: Literal["CORE"] = "CORE"
    fact_axis: Literal["CORE_CONTEXT"] = "CORE_CONTEXT"
    native_axis: Literal["CORE_REPORTED_CONTEXT"] = AXIS
    facts: tuple[ReportedFact, ReportedFact]
    comparison: ReportedPolicyResult
    grant_sha256: SHA
    materiality: Literal["UNKNOWN"] = "UNKNOWN"
    causal_attribution: Literal["UNKNOWN"] = "UNKNOWN"
    recurrence: Literal["UNKNOWN"] = "UNKNOWN"
    interpretation_confidence: Literal["NOT_AUTHORIZED"] = "NOT_AUTHORIZED"
    permitted_roles: tuple[()] = ()
    permitted_wording: Literal["REPORTED_PERIOD_VALUES_AND_ARITHMETIC_ONLY"] = "REPORTED_PERIOD_VALUES_AND_ARITHMETIC_ONLY"
    denied_implications: tuple[str, ...] = (
        "VALUATION", "CORE_DIRECTION", "OVERALL_CONTEXT", "OVERALL_DIRECTION",
        "HOLDER_CONTEXT", "HOLDER_DIRECTION", "NEWBUYER_CONTEXT", "NEWBUYER_DIRECTION",
        "CURRENT_ECONOMIC_TRUTH", "INDEPENDENT_CORROBORATION", "ACCEPTED_CORE",
    )


class ReportedContextScope(Closed):
    """Separate v4 attachment scope; never an alias for valuation permission."""
    contract: Literal["native-reported-context-scope-v1"] = "native-reported-context-scope-v1"
    invocation_id: Identity
    security_id: Identity
    generation_id: Identity
    source_generation_id: Identity
    assessment_as_of: date
    consumer: Literal["CORE"] = "CORE"
    allowed_use_axes: tuple[Literal["CORE_REPORTED_CONTEXT"], ...]
    source_envelope_sha256: SHA


class BackendReportedContextPolicy:
    """Trusted composition only; public hashes/JSON are not issuing capabilities."""

    def __init__(self, owner: BackendReportedFactOwner):
        if not isinstance(owner, BackendReportedFactOwner):
            raise ValueError("BACKEND_REPORTED_FACT_OWNER_REQUIRED")
        self._owner = owner
        self._issued = {}

    def issue(self, comparison, *, invocation_id, execution_generation_id):
        result = self._owner.verify_interpretation(comparison)
        facts = self._owner.authorize_interpretation(result, axis="DISPLAY",
            security_id=result.security_id, execution_generation_id=result.execution_generation_id,
            source_generation_id=result.source_generation_id)
        current, prior = facts
        # Owner comparison quality already checks occurrence/filing and conflict.
        # These are type-specific comparability constraints, not investment thresholds.
        if (current.field, current.concept, current.currency, current.statement_basis, current.share_basis) != (
                prior.field, prior.concept, prior.currency, prior.statement_basis, prior.share_basis):
            raise ValueError("CONTEXT_COMPARISON_BASIS_MISMATCH")
        if current.period_end <= prior.period_end or current.duration_days != prior.duration_days:
            raise ValueError("CONTEXT_COMPARISON_PERIOD_MISMATCH")
        body = dict(grant_id=secrets.token_hex(24), policy_sha256=policy_sha(),
            invocation_id=invocation_id, security_id=result.security_id,
            market=self._owner.registration.market.lower(),
            source_envelope_sha256=digest(sorted({f.raw_source_sha256 for f in self._owner.facts})),
            source_generation_id=result.source_generation_id,
            owner_execution_generation_id=result.execution_generation_id,
            execution_generation_id=execution_generation_id, facts=facts, comparison=result)
        grant = ReportedContextGrant(**body, grant_sha256=digest({
            k: [f.model_dump(mode="json") for f in v] if k == "facts" else
            v.model_dump(mode="json") if k == "comparison" else v for k, v in body.items()}))
        self._issued[grant.grant_id] = grant.model_dump_json()
        return grant

    def verify(self, grant, *, invocation_id, security_id, execution_generation_id,
               source_generation_id, consumer="CORE", native_axis=AXIS):
        if not isinstance(grant, ReportedContextGrant):
            raise ValueError("ISSUED_CONTEXT_GRANT_REQUIRED")
        if self._issued.get(grant.grant_id) != grant.model_dump_json():
            raise ValueError("UNISSUED_OR_CHANGED_CONTEXT_GRANT")
        if (invocation_id, security_id, execution_generation_id, source_generation_id, consumer, native_axis) != (
                grant.invocation_id, grant.security_id, grant.execution_generation_id,
                grant.source_generation_id, grant.consumer, grant.native_axis):
            raise ValueError("CONTEXT_INVOCATION_AXIS_IDENTITY_MISMATCH")
        if grant.policy_sha256 != policy_sha():
            raise ValueError("CONTEXT_POLICY_CHANGED")
        facts = self._owner.authorize_interpretation(grant.comparison, axis="DISPLAY",
            security_id=grant.security_id, execution_generation_id=grant.owner_execution_generation_id,
            source_generation_id=grant.source_generation_id)
        if tuple(facts) != grant.facts:
            raise ValueError("CONTEXT_SOURCE_BINDING_MISMATCH")
        return grant


class RoleEvidenceState(Closed):
    """Evidence requirements, not caller authorization or an investment classifier."""
    material_anchor: Literal["QUALIFIED", "UNKNOWN", "NEGLIGIBLE_OR_ZERO_BASE"]
    mechanism: Literal["QUALIFIED", "UNKNOWN"]
    recurrence: Literal["RECURRING", "NONRECURRING", "UNKNOWN"]
    counterevidence: Literal["CHECKED_NO_MATERIAL_CONFLICT", "MATERIAL_CONFLICT", "MISSING_REQUIRED"]
    independent_support: bool
    all_core_roles: bool


class RoleEligibility(Closed):
    policy_version: Literal["reported-role-requirements-v1"] = "reported-role-requirements-v1"
    disposition: Literal["CONTEXT_ONLY", "CAUTION_CONTEXT", "ELIGIBLE_FOR_EXISTING_ROLE_REVIEW"]
    missing_requirements: tuple[str, ...]
    confidence_ceiling: Literal["NOT_AUTHORIZED"] = "NOT_AUTHORIZED"
    authority_state: Literal["PROPOSED_REQUIRES_DECISION"] = "PROPOSED_REQUIRES_DECISION"
    automatic_roles: tuple[()] = ()
    complete_core_eligible: Literal[False] = False
    new_investment_preference_authorized: Literal[False] = False


def role_requirements(state: RoleEvidenceState) -> RoleEligibility:
    """Inactive review proposal for a recurring-operating-driver profile.

    This is not a universal directional policy: inherited rules allow qualified
    current evidence with uncertain future durability. It cannot issue grants,
    cap a native decision, or replace the inherited ordinal economic validator.
    """
    state = RoleEvidenceState.model_validate(state.model_dump(mode="json"))
    missing = []
    for condition, reason in (
        (state.material_anchor == "QUALIFIED", "MATERIAL_ANCHOR"),
        (state.mechanism == "QUALIFIED", "BUSINESS_MECHANISM"),
        (state.recurrence == "RECURRING", "RECURRING_BASIS"),
        (state.counterevidence == "CHECKED_NO_MATERIAL_CONFLICT", "COUNTEREVIDENCE_DISPOSITION"),
        (state.independent_support, "INDEPENDENT_SUPPORT_FOR_SYNTHESIS"),
    ):
        if not condition:
            missing.append(reason)
    disposition = "CONTEXT_ONLY" if missing else "ELIGIBLE_FOR_EXISTING_ROLE_REVIEW"
    if state.recurrence == "NONRECURRING" or state.counterevidence == "MATERIAL_CONFLICT":
        disposition = "CAUTION_CONTEXT"
    if not state.all_core_roles:
        missing.append("OTHER_REQUIRED_CORE_ROLES")
    return RoleEligibility(disposition=disposition, missing_requirements=tuple(missing))
