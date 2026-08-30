from __future__ import annotations

from enum import StrEnum

from pydantic import Field, model_validator

from app.services.cross_market_decision_engine_service import EvidenceClaim, FrozenModel


CONTRACT_VERSION = "evidence-maturity-pricing-v2"


class EvidenceMaturity(StrEnum):
    EARLY = "EARLY"
    PARTIAL = "PARTIAL"
    CONFIRMED = "CONFIRMED"
    MIXED = "MIXED"
    UNKNOWN = "UNKNOWN"


class MarketExpectation(StrEnum):
    DEPRESSED = "depressed"
    LOW = "low"
    BALANCED = "balanced"
    ELEVATED = "elevated"
    VERY_HIGH = "very_high"
    SPECULATIVE = "speculative"
    UNKNOWN = "unknown"


class PricingRequirement(StrEnum):
    CONSERVATIVE_OUTCOME_SUFFICIENT = "CONSERVATIVE_OUTCOME_SUFFICIENT"
    BASE_CASE_REQUIRED = "BASE_CASE_REQUIRED"
    OPTIMISTIC_CASE_REQUIRED = "OPTIMISTIC_CASE_REQUIRED"
    BULL_CASE_REQUIRED = "BULL_CASE_REQUIRED"
    UNKNOWN = "UNKNOWN"


class DriverEvidenceMaturity(FrozenModel):
    driver: str = Field(min_length=2, max_length=120)
    decisive: bool
    maturity: EvidenceMaturity
    supporting_evidence_refs: tuple[str, ...] = Field(min_length=1, max_length=6)
    contradicting_evidence_refs: tuple[str, ...] = Field(default=(), max_length=6)
    what_remains_unproven: EvidenceClaim
    as_of: str = Field(min_length=10, max_length=35)

    @model_validator(mode="after")
    def references_are_distinct(self) -> DriverEvidenceMaturity:
        supporting = set(self.supporting_evidence_refs)
        contradicting = set(self.contradicting_evidence_refs)
        if supporting & contradicting:
            raise ValueError("maturity_reference_polarity_overlap")
        return self


class OverallMaturityAssessment(FrozenModel):
    maturity: EvidenceMaturity
    basis: EvidenceClaim


class MarketExpectationAssessment(FrozenModel):
    level: MarketExpectation
    basis: EvidenceClaim


class PricingRequirementAssessment(FrozenModel):
    requirement: PricingRequirement
    basis: EvidenceClaim
    valuation_basis: EvidenceClaim
    expectation_basis: EvidenceClaim
    key_assumption: EvidenceClaim
    unknowns: tuple[EvidenceClaim, ...] = Field(min_length=1, max_length=3)


def decisive_maturities(
    drivers: tuple[DriverEvidenceMaturity, ...],
) -> frozenset[EvidenceMaturity]:
    return frozenset(row.maturity for row in drivers if row.decisive)
