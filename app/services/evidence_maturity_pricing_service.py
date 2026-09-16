from __future__ import annotations

import re
from datetime import date, datetime
from enum import StrEnum

from pydantic import Field, field_validator, model_validator

from app.services.cross_market_decision_engine_service import EvidenceClaim, FrozenModel


CONTRACT_VERSION = "evidence-maturity-pricing-v2"
ISO_DATE_PATTERN = r"^\d{4}-\d{2}-\d{2}$"
_ISO_DATE = re.compile(ISO_DATE_PATTERN)
_ISO_DATETIME_PREFIX = re.compile(r"^\d{4}-\d{2}-\d{2}T")


def concrete_evidence_date(value: str | None) -> date | None:
    """Return an explicitly encoded calendar date without resolving symbolic tokens."""
    if value is None:
        return None
    if _ISO_DATE.fullmatch(value):
        try:
            return date.fromisoformat(value)
        except ValueError:
            return None
    if not _ISO_DATETIME_PREFIX.match(value):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).date()
    except ValueError:
        return None


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
    supporting_claim_refs: tuple[str, ...] = Field(default=(), max_length=6)
    contradicting_claim_refs: tuple[str, ...] = Field(default=(), max_length=6)
    what_remains_unproven: EvidenceClaim
    as_of: str = Field(min_length=10, max_length=10, pattern=ISO_DATE_PATTERN)

    @field_validator("as_of")
    @classmethod
    def as_of_is_real_calendar_date(cls, value: str) -> str:
        if concrete_evidence_date(value) is None:
            raise ValueError("maturity_as_of_invalid_calendar_date")
        return value

    @model_validator(mode="after")
    def atomic_claims_are_distinct(self) -> DriverEvidenceMaturity:
        supporting = set(self.supporting_claim_refs)
        contradicting = set(self.contradicting_claim_refs)
        if supporting & contradicting:
            raise ValueError("maturity_atomic_claim_polarity_overlap")
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
