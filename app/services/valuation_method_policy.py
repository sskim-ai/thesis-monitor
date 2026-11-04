"""Versioned valuation-method qualification, currently shadow-only.

Receipt hashes bind bytes, not truth. The caller must supply an independently
reviewed shadow authority set. No production authority loader or persistence is
provided here; synthetic receipts cannot authorize a live valuation.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from enum import StrEnum
from typing import Annotated, Literal

from pydantic import Field, model_validator

from app.services.unified_snapshot_contract import ContractModel, digest


Sha256 = Annotated[str, Field(pattern=r"^[a-f0-9]{64}$")]
Nonempty = Annotated[str, Field(min_length=1, pattern=r".*\S.*")]
Domain = Literal["SYNTHETIC_TEST_AUTHORITY", "REVIEWED_SHADOW_AUTHORITY"]
POLICY_VERSION = "valuation-method-policy-v1"
MODEL_VERSION = "legacy-forward-arithmetic-v1"


class ForwardMethod(StrEnum):
    NORMALIZED_CYCLE_MARGIN = "NORMALIZED_CYCLE_MARGIN"
    BLENDED_NET_MARGIN_60_40 = "BLENDED_NET_MARGIN_60_40"
    NORMALIZED_ROE = "NORMALIZED_ROE"
    SPECIAL_SCENARIO_METHOD = "SPECIAL_SCENARIO_METHOD"
    FORWARD_MODEL_INAPPLICABLE = "FORWARD_MODEL_INAPPLICABLE"
    UNRESOLVED = "UNRESOLVED"


class HistoricalMethod(StrEnum):
    APPLICABLE = "HISTORICAL_MULTIPLE_APPLICABLE"
    INAPPLICABLE = "HISTORICAL_MULTIPLE_INAPPLICABLE"
    UNRESOLVED = "UNRESOLVED"


class EconomicProperty(StrEnum):
    REGULATED_INSURER = "REGULATED_INSURER"
    BANK_OR_BROKERAGE = "BANK_OR_BROKERAGE"
    MEMORY_SEMICONDUCTOR_EXPOSURE = "MEMORY_SEMICONDUCTOR_EXPOSURE"
    GENERIC_SEMICONDUCTOR = "GENERIC_SEMICONDUCTOR"
    CYCLE_SENSITIVE_EARNINGS = "CYCLE_SENSITIVE_EARNINGS"
    NORMALIZABLE_CYCLE_FINANCIALS = "NORMALIZABLE_CYCLE_FINANCIALS"
    ORDINARY_MARGIN_STATEMENTS = "ORDINARY_MARGIN_STATEMENTS"
    EQUITY_EARNINGS_ACCOUNTING_COMPATIBLE = "EQUITY_EARNINGS_ACCOUNTING_COMPATIBLE"
    SCENARIO_DEPENDENT = "SCENARIO_DEPENDENT"
    ORDINARY_FORWARD_INSUFFICIENT = "ORDINARY_FORWARD_INSUFFICIENT"
    ORDINARY_FORWARD_INAPPLICABLE = "ORDINARY_FORWARD_INAPPLICABLE"
    COMPARABLE_HISTORICAL_BASIS = "COMPARABLE_HISTORICAL_BASIS"
    ORDINARY_HISTORICAL_INSUFFICIENT = "ORDINARY_HISTORICAL_INSUFFICIENT"


class ValuationBinding(ContractModel):
    security_id: Nonempty
    market: Literal["us", "kr"]
    exchange: Nonempty
    security_type: Literal["common_stock"]
    generation: Nonempty
    as_of: date


class EvidenceReference(ContractModel):
    source_id: Nonempty
    owner: Nonempty
    field_scope: Nonempty
    period_end: date
    available_on: date
    raw_sha256: Sha256

    @model_validator(mode="after")
    def temporal_order(self):
        if self.period_end > self.available_on:
            raise ValueError("evidence_period_after_publication")
        return self


class DepositaryRatioEvidence(ContractModel):
    """A reviewed claim, not a default conversion inferred from a ticker."""

    contract: Literal["depositary-ratio-evidence-v1"] = "depositary-ratio-evidence-v1"
    listed_security_id: Nonempty
    underlying_security_id: Nonempty
    generation: Nonempty
    ordinary_shares_per_listed_share: Decimal = Field(gt=0, allow_inf_nan=False)
    listed_currency: Annotated[str, Field(pattern=r"^[A-Z]{3}$")]
    reporting_currency: Annotated[str, Field(pattern=r"^[A-Z]{3}$")]
    effective_from: date
    effective_until: date
    evidence: tuple[EvidenceReference, ...] = Field(min_length=1)


class DepositaryValuationBinding(ContractModel):
    """Isolated shadow binding; no FX or financial-input conversion is implied."""

    contract: Literal["depositary-valuation-binding-v1"] = "depositary-valuation-binding-v1"
    security_id: Nonempty
    market: Literal["us", "kr"]
    exchange: Nonempty
    security_type: Literal["ADS", "DEPOSITARY_RECEIPT"]
    underlying_security_id: Nonempty
    generation: Nonempty
    as_of: date
    listed_currency: Annotated[str, Field(pattern=r"^[A-Z]{3}$")]
    reporting_currency: Annotated[str, Field(pattern=r"^[A-Z]{3}$")]
    price_share_basis: Literal["listed_depositary_share"] = "listed_depositary_share"
    reporting_share_basis: Literal["underlying_ordinary_share"] = "underlying_ordinary_share"
    ratio_claims: tuple[DepositaryRatioEvidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def qualified_ratio_binding(self):
        if self.security_id == self.underlying_security_id:
            raise ValueError("depositary_underlying_cannot_equal_listing")
        ratios = set()
        for claim in self.ratio_claims:
            if claim.listed_security_id != self.security_id:
                raise ValueError("depositary_listing_mismatch")
            if claim.underlying_security_id != self.underlying_security_id:
                raise ValueError("depositary_underlying_mismatch")
            if claim.generation != self.generation:
                raise ValueError("depositary_generation_mismatch")
            if (claim.listed_currency, claim.reporting_currency) != (
                self.listed_currency, self.reporting_currency
            ):
                raise ValueError("depositary_currency_mismatch")
            if not claim.effective_from <= self.as_of <= claim.effective_until:
                raise ValueError("depositary_ratio_not_effective")
            if any(e.available_on > self.as_of for e in claim.evidence):
                raise ValueError("depositary_future_evidence")
            ratios.add(claim.ordinary_shares_per_listed_share)
        if len(ratios) != 1:
            raise ValueError("depositary_conflicting_ratios")
        return self


ValuationIdentity = ValuationBinding | DepositaryValuationBinding


class PropertyEvidence(ContractModel):
    property: EconomicProperty
    rationale: Nonempty
    evidence: tuple[EvidenceReference, ...] = Field(min_length=1)


class IssuerCharacteristics(ContractModel):
    contract: Literal["issuer-economic-characteristics-v1"] = "issuer-economic-characteristics-v1"
    authority_domain: Domain
    binding: ValuationIdentity
    reporting_basis: Nonempty
    properties: tuple[PropertyEvidence, ...]

    @model_validator(mode="after")
    def distinct_properties(self):
        keys = [p.property for p in self.properties]
        if len(set(keys)) != len(keys):
            raise ValueError("duplicate_economic_property")
        return self


class MethodApproval(ContractModel):
    contract: Literal["valuation-method-approval-v1"] = "valuation-method-approval-v1"
    policy_version: Literal["valuation-method-policy-v1"] = POLICY_VERSION
    authority_domain: Domain
    binding: ValuationIdentity
    axis: Literal["FORWARD_INCOME", "HISTORICAL_MULTIPLE"]
    method: ForwardMethod | HistoricalMethod
    historical_signal: Literal["PB_ONLY", "PE_AND_PB"] | None = None
    model_version: Literal["legacy-forward-arithmetic-v1"] = MODEL_VERSION
    characteristics_sha256: Sha256
    supporting_properties: tuple[EconomicProperty, ...] = Field(min_length=1)
    rationale: Nonempty
    policy_owner: str
    approval_version: str
    effective_from: date
    effective_until: date
    evidence: tuple[EvidenceReference, ...] = Field(min_length=1)
    selection_basis: Literal["REVIEWED_ECONOMIC_CRITERIA"] = "REVIEWED_ECONOMIC_CRITERIA"

    @model_validator(mode="after")
    def axis_contract(self):
        allowed = set(ForwardMethod) if self.axis == "FORWARD_INCOME" else set(HistoricalMethod)
        if self.method not in allowed:
            raise ValueError("method_axis_mismatch")
        if self.axis == "HISTORICAL_MULTIPLE" and self.method == HistoricalMethod.APPLICABLE:
            if self.historical_signal is None:
                raise ValueError("historical_signal_policy_required")
        elif self.historical_signal is not None:
            raise ValueError("unexpected_historical_signal_policy")
        if len(set(self.supporting_properties)) != len(self.supporting_properties):
            raise ValueError("duplicate_supporting_property")
        return self


class ShadowAuthority(ContractModel):
    purpose: Literal["VALUATION_SHADOW_ONLY"] = "VALUATION_SHADOW_ONLY"
    authority_domain: Domain
    binding: ValuationIdentity
    review_owner: Nonempty
    review_version: Nonempty
    characteristics_sha256: tuple[Sha256, ...]
    method_approval_sha256: tuple[Sha256, ...]
    input_qualification_sha256: tuple[Sha256, ...]


class AxisSelection(ContractModel):
    method: str = "UNRESOLVED"
    status: Literal["QUALIFIED_FOR_SHADOW", "UNRESOLVED"] = "UNRESOLVED"
    reason_codes: tuple[str, ...]
    approval_sha256: Sha256 | None = None
    historical_signal: Literal["PB_ONLY", "PE_AND_PB"] | None = None


class MethodSelection(ContractModel):
    contract: Literal["valuation-method-selection-v1"] = "valuation-method-selection-v1"
    binding: ValuationIdentity
    authority_domain: Domain
    eligible_as_production_authority: Literal[False] = False
    forward: AxisSelection
    historical: AxisSelection
    authority_sha256: Sha256


def receipt_sha256(receipt: ContractModel) -> str:
    return digest(receipt.model_dump(mode="json"))


_CRITERIA = {
    ForwardMethod.NORMALIZED_CYCLE_MARGIN: {
        EconomicProperty.CYCLE_SENSITIVE_EARNINGS,
        EconomicProperty.NORMALIZABLE_CYCLE_FINANCIALS,
    },
    ForwardMethod.BLENDED_NET_MARGIN_60_40: {EconomicProperty.ORDINARY_MARGIN_STATEMENTS},
    ForwardMethod.NORMALIZED_ROE: {EconomicProperty.EQUITY_EARNINGS_ACCOUNTING_COMPATIBLE},
    ForwardMethod.SPECIAL_SCENARIO_METHOD: {
        EconomicProperty.SCENARIO_DEPENDENT,
        EconomicProperty.ORDINARY_FORWARD_INSUFFICIENT,
    },
    ForwardMethod.FORWARD_MODEL_INAPPLICABLE: {EconomicProperty.ORDINARY_FORWARD_INAPPLICABLE},
    HistoricalMethod.APPLICABLE: {EconomicProperty.COMPARABLE_HISTORICAL_BASIS},
    HistoricalMethod.INAPPLICABLE: {EconomicProperty.ORDINARY_HISTORICAL_INSUFFICIENT},
}


def select_shadow_methods(
    binding: ValuationIdentity,
    characteristics: IssuerCharacteristics | None,
    approvals: tuple[MethodApproval, ...],
    authority: ShadowAuthority,
) -> MethodSelection:
    """Qualify each axis separately; this never qualifies model input values."""
    common = []
    if authority.binding != binding:
        common.append("AUTHORITY_BINDING_MISMATCH")
    if characteristics is None:
        common.append("ISSUER_CHARACTERISTICS_MISSING")
    else:
        if characteristics.binding != binding:
            common.append("CHARACTERISTICS_BINDING_MISMATCH")
        if characteristics.authority_domain != authority.authority_domain:
            common.append("CHARACTERISTICS_AUTHORITY_DOMAIN_MISMATCH")
        if receipt_sha256(characteristics) not in authority.characteristics_sha256:
            common.append("CHARACTERISTICS_NOT_REVIEWED")
        if any(e.available_on > binding.as_of for p in characteristics.properties for e in p.evidence):
            common.append("CHARACTERISTICS_FUTURE_EVIDENCE")

    def select(axis: str) -> AxisSelection:
        reasons = list(common)
        candidates = [p for p in approvals if p.axis == axis]
        if len(candidates) != 1:
            reasons.append("METHOD_APPROVAL_MISSING" if not candidates else "CONFLICTING_APPROVALS")
            return AxisSelection(reason_codes=tuple(reasons))
        policy = candidates[0]
        if policy.binding != binding:
            reasons.append("METHOD_BINDING_MISMATCH")
        if policy.authority_domain != authority.authority_domain:
            reasons.append("METHOD_AUTHORITY_DOMAIN_MISMATCH")
        if not policy.policy_owner.strip():
            reasons.append("POLICY_OWNER_MISSING")
        if not policy.approval_version.strip():
            reasons.append("APPROVAL_VERSION_MISSING")
        if not policy.effective_from <= binding.as_of <= policy.effective_until:
            reasons.append("METHOD_NOT_EFFECTIVE")
        if receipt_sha256(policy) not in authority.method_approval_sha256:
            reasons.append("METHOD_NOT_APPROVED")
        if any(e.available_on > binding.as_of for e in policy.evidence):
            reasons.append("METHOD_FUTURE_EVIDENCE")
        if characteristics is not None:
            if policy.characteristics_sha256 != receipt_sha256(characteristics):
                reasons.append("METHOD_CHARACTERISTICS_MISMATCH")
            available = {p.property for p in characteristics.properties}
            required = _CRITERIA.get(policy.method)
            if required is None:
                reasons.append("METHOD_UNRESOLVED")
            else:
                for item in sorted(required - set(policy.supporting_properties)):
                    reasons.append("APPROVED_CRITERION_MISSING:" + item)
                for item in sorted(set(policy.supporting_properties) - available):
                    reasons.append("PROPERTY_EVIDENCE_MISSING:" + item)
        if reasons:
            return AxisSelection(reason_codes=tuple(reasons))
        return AxisSelection(method=policy.method, status="QUALIFIED_FOR_SHADOW",
                             reason_codes=("REVIEWED_METHOD_CRITERIA_SATISFIED",),
                             approval_sha256=receipt_sha256(policy),
                             historical_signal=policy.historical_signal)

    return MethodSelection(binding=binding, authority_domain=authority.authority_domain,
                           forward=select("FORWARD_INCOME"), historical=select("HISTORICAL_MULTIPLE"),
                           authority_sha256=receipt_sha256(authority))
