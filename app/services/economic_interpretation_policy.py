"""Property-based interpretation qualification without inventing Core roles.

This opt-in layer executes existing financial comparison semantics. Source facts,
comparison meaning and a Core investment role are separate qualifications. The
currently governing rules do not authorize promotion of a comparison hint into
a BUY/SELL/Holder conclusion, nor an accepted abstention.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import Field

from app.services.business_delta_evidence_service import (
    FINANCIAL_COMPARISON_DIRECTION_CONTRACT,
    derive_financial_comparison_direction,
)
from app.services.cross_market_decision_engine_service import DecisionEvidenceRef
from app.services.native_input_admission import Closed, Identity, SHA
from app.services.sec_business_field_quality_service import reported_comparison_quality
from app.services.unified_snapshot_contract import digest


class ComparisonInput(Closed):
    contract: Literal["backend-financial-comparison-input-v1"] = "backend-financial-comparison-input-v1"
    security_id: Identity
    generation_id: Identity
    source_generation_id: Identity
    owner_ref: Identity
    source_artifact_sha256: tuple[SHA, ...] = Field(min_length=1)
    facts: tuple[DecisionEvidenceRef, ...] = Field(min_length=2)


class BackendComparisonInputs:
    """Backend-owned input anchor, never taken from a model/caller request.

    The upstream source-owner adapter must independently verify exact raw receipt,
    source identity and generation before constructing this capability. A payload
    hash is integrity, not a new corporate-evidence signature.
    """

    def __init__(self, value: ComparisonInput, *, expected_input_sha256: str):
        value = ComparisonInput.model_validate(value.model_dump(mode="json"))
        if digest(value.model_dump(mode="json")) != expected_input_sha256:
            raise ValueError("INDEPENDENT_COMPARISON_INPUT_ANCHOR_REQUIRED")
        refs = [f.ref_id for f in value.facts]
        source_refs = [f.source_ref for f in value.facts]
        if len(set(refs)) != len(refs) or len(set(source_refs)) != len(source_refs):
            raise ValueError("DUPLICATE_COMPARISON_FACT")
        if any(f.value is None or not Decimal(str(f.value)).is_finite() for f in value.facts):
            raise ValueError("STRUCTURED_FINITE_VALUE_REQUIRED_NO_PROSE_FALLBACK")
        self._json = value.model_dump_json()

    @property
    def inputs(self):
        return ComparisonInput.model_validate_json(self._json)


class InterpretationQualification(Closed):
    contract: Literal["generic-economic-interpretation-qualification-v1"] = (
        "generic-economic-interpretation-qualification-v1"
    )
    rule_id: str
    security_id: Identity
    generation_id: Identity
    source_generation_id: Identity
    required_supporting_refs: tuple[str, ...]
    input_sha256: SHA
    source_owner_ref: str
    comparison_qualified: bool
    interpretation_type: Literal["COMPARABLE_CASH_FLOW_HINT", "REPORTED_PERIOD_CHANGE", "UNRESOLVED"]
    observed_direction: tuple[str, ...]
    uncertainty_class: Literal["COMPARISON_ONLY", "UNRESOLVED"]
    semantic_scope: Literal["BUSINESS_DELTA_COMPARISON_ONLY", "ISSUER_REPORTED_COMPARISON_ONLY"]
    reason: str
    core_role_state: Literal["POLICY_RULE_NOT_AUTHORIZED"] = "POLICY_RULE_NOT_AUTHORIZED"
    permitted_core_roles: tuple[()] = ()
    permitted_native_direction_axes: tuple[()] = ()
    confidence_ceiling: None = None
    accepted_economic_candidate: Literal[False] = False
    limitation: str = "Comparison direction is not materiality, causal investment role, confidence or decision synthesis."


class ReportedStatementInput(Closed):
    ticker: Identity
    provider: Literal["sec_companyfacts"]
    currency: str
    source_filing_id: Identity
    filing_date: date
    financial_period_end: date
    period_scope: str
    revenue: float | None = Field(allow_inf_nan=False)
    operating_income: float | None = Field(allow_inf_nan=False)
    raw_financial_fields: str
    financial_hard_errors: str
    normalization_method: str | None
    financial_statement_basis_warning: bool
    period_mapping_validation_failed: bool
    margin_quality_review: bool


class ReportedComparisonInput(Closed):
    contract: Literal["backend-reported-comparison-input-v1"] = "backend-reported-comparison-input-v1"
    security_id: Identity
    ticker: Identity
    generation_id: Identity
    source_generation_id: Identity
    owner_ref: Identity
    source_artifact_sha256: tuple[SHA, ...] = Field(min_length=1)
    cutoff: date
    formal: ReportedStatementInput
    comparison: ReportedStatementInput


class BackendReportedComparison:
    """Pinned upstream statement-owner capsule, not a caller-owned dict."""

    def __init__(self, value, *, expected_input_sha256):
        value = ReportedComparisonInput.model_validate(value.model_dump(mode="json"))
        if digest(value.model_dump(mode="json")) != expected_input_sha256:
            raise ValueError("INDEPENDENT_REPORTED_INPUT_ANCHOR_REQUIRED")
        if value.formal.ticker != value.ticker or value.comparison.ticker != value.ticker:
            raise ValueError("REPORTED_STATEMENT_IDENTITY_MISMATCH")
        self._json = value.model_dump_json()

    @property
    def inputs(self):
        return ReportedComparisonInput.model_validate_json(self._json)


def qualify_cash_flow_comparison(*, inputs, current_ref, security_id, generation_id, source_generation_id):
    if not isinstance(inputs, BackendComparisonInputs):
        raise ValueError("BACKEND_OWNED_COMPARISON_INPUTS_REQUIRED")
    bundle = inputs.inputs
    if (security_id, generation_id, source_generation_id) != (
        bundle.security_id, bundle.generation_id, bundle.source_generation_id
    ):
        raise ValueError("COMPARISON_SECURITY_GENERATION_MISMATCH")
    by_ref = {f.ref_id: f for f in bundle.facts}
    if current_ref not in by_ref:
        raise ValueError("COMPARISON_REQUEST_MEMBERSHIP_MISMATCH")
    current = by_ref[current_ref]
    result = derive_financial_comparison_direction(current, {f.source_ref: f for f in bundle.facts})
    comparison = current.financial_context.comparison if current.financial_context else None
    refs = tuple(dict.fromkeys((current.source_ref, *(comparison.input_source_refs if comparison else ()))))
    if not set(refs).issubset({f.source_ref for f in bundle.facts}):
        raise ValueError("COMPARISON_SUPPORTING_REFERENCE_MEMBERSHIP_MISMATCH")
    return InterpretationQualification(
        rule_id=FINANCIAL_COMPARISON_DIRECTION_CONTRACT,
        security_id=security_id, generation_id=generation_id, source_generation_id=source_generation_id,
        required_supporting_refs=refs,
        input_sha256=digest(bundle.model_dump(mode="json")), source_owner_ref=bundle.owner_ref,
        comparison_qualified=result.comparability_safe,
        interpretation_type="COMPARABLE_CASH_FLOW_HINT" if result.comparability_safe else "UNRESOLVED",
        observed_direction=result.supported_change_directions,
        uncertainty_class="COMPARISON_ONLY" if result.comparability_safe else "UNRESOLVED",
        semantic_scope="BUSINESS_DELTA_COMPARISON_ONLY", reason=result.reason,
    )


def qualify_reported_comparison(*, inputs, security_id, generation_id, source_generation_id):
    """Execute the existing SEC field owner, not a new profitability rule.

    This backend composition function consumes admitted statement rows, never
    caller-supplied thesis facts. Its result cannot authorize a native Core claim.
    """
    if not isinstance(inputs, BackendReportedComparison):
        raise ValueError("BACKEND_OWNED_REPORTED_INPUTS_REQUIRED")
    bundle = inputs.inputs
    if (security_id, generation_id, source_generation_id) != (
        bundle.security_id, bundle.generation_id, bundle.source_generation_id
    ):
        raise ValueError("REPORTED_SECURITY_GENERATION_MISMATCH")
    receipt = reported_comparison_quality(formal=bundle.formal, comparison=bundle.comparison,
                                         ticker=bundle.ticker, cutoff=bundle.cutoff)
    qualified = []
    for observation in receipt["comparative_observations"]:
        refs = tuple(observation[k]["lineage"]["source_row_identity"] for k in ("current", "comparison"))
        qualified.append(InterpretationQualification(
            rule_id="sec-business-field-quality-v1:reported-comparison",
            security_id=security_id, generation_id=generation_id, source_generation_id=source_generation_id,
            required_supporting_refs=refs, input_sha256=digest(bundle.model_dump(mode="json")), source_owner_ref=bundle.owner_ref,
            comparison_qualified=True, interpretation_type="REPORTED_PERIOD_CHANGE",
            observed_direction=(observation["direction"],), uncertainty_class="COMPARISON_ONLY",
            semantic_scope="ISSUER_REPORTED_COMPARISON_ONLY",
            reason="QUALIFIED_REPORTED_COMPARISON_NOT_RECURRING_PROFIT_OR_CORE_ROLE",
        ))
    return receipt, tuple(qualified)


class AbstentionPolicyDecision(Closed):
    contract: Literal["native-core-abstention-policy-decision-v1"] = (
        "native-core-abstention-policy-decision-v1"
    )
    status: Literal["POLICY_AUTHORITY_GAP"] = "POLICY_AUTHORITY_GAP"
    governing_contract: Literal["v2-accepted-fundamental-core-v1"] = "v2-accepted-fundamental-core-v1"
    accepted_abstention: Literal[False] = False
    permitted_substitutions: tuple[()] = ()
    required_new_approval: tuple[str, ...] = (
        "Evidence search and admission attempts before abstention",
        "Required versus optional roles and affected use axes",
        "Distinct output type and per-consumer downstream/renderer behavior",
    )


def governing_abstention_policy():
    return AbstentionPolicyDecision()


def reject_unauthorized_abstention(_value):
    raise ValueError("POLICY_AUTHORITY_GAP:NO_ACCEPTED_CORE_ABSTENTION")
