from __future__ import annotations

import re
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date, datetime
from enum import StrEnum

from pydantic import Field, field_validator, model_validator

from app.services.cross_market_decision_engine_service import (
    DecisionEvidenceRef,
    EvidenceCategory,
    EvidenceClaim,
    FrozenModel,
)


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


class MaturityProvenanceStatus(StrEnum):
    CONCRETE_ONLY = "CONCRETE_ONLY"
    CONCRETE_WITH_SYMBOLIC_REFS = "CONCRETE_WITH_SYMBOLIC_REFS"
    SYMBOLIC_ONLY_NO_CONCRETE_DATE = "SYMBOLIC_ONLY_NO_CONCRETE_DATE"


class SymbolicMaturityEvidenceKind(StrEnum):
    EARNINGS_PERIOD_PLACEHOLDER = "EARNINGS_PERIOD_PLACEHOLDER"
    FINANCIAL_QUALITY_LIMITATION = "FINANCIAL_QUALITY_LIMITATION"


@dataclass(frozen=True)
class MaturityProvenanceProjection:
    as_of: str | None
    provenance_status: MaturityProvenanceStatus | None
    concrete_dates: tuple[str, ...]
    symbolic_ref_ids: tuple[str, ...]
    invalid_ref_ids: tuple[str, ...]


def _structured_statement(row: DecisionEvidenceRef) -> Mapping[str, object] | None:
    try:
        parsed = json.loads(row.statement)
    except (json.JSONDecodeError, TypeError):
        return None
    return parsed if isinstance(parsed, Mapping) else None


def symbolic_maturity_evidence_kind(
    row: DecisionEvidenceRef,
) -> SymbolicMaturityEvidenceKind | None:
    """Recognize intentional nondate provenance from canonical producer metadata."""
    if (
        row.category != EvidenceCategory.EARNINGS
        or not row.ref_id.startswith("canonical:")
        or row.as_of != "latest"
        or row.value is not None
        or row.source_ref != f"stock.fact_catalog.{row.ref_id.removeprefix('canonical:')}"
    ):
        return None
    statement = _structured_statement(row)
    if statement is None:
        return None
    if row.label == "financial_quality" and (
        statement.get("decision_version") == "financial-quality-taint-v2"
        and "source_period" in statement
        and statement.get("source_period") is None
        and statement.get("source_type") == "unknown"
        and statement.get("state") == "unknown"
        and isinstance(statement.get("reason_codes"), list)
    ):
        return SymbolicMaturityEvidenceKind.FINANCIAL_QUALITY_LIMITATION
    if row.label == "earnings" and (
        statement.get("period") == "latest"
        and "period_label" in statement
        and statement.get("period_label") is None
        and "period_type" in statement
        and statement.get("period_type") is None
        and statement.get("financial_period_required") is True
        and statement.get("preliminary") is False
    ):
        return SymbolicMaturityEvidenceKind.EARNINGS_PERIOD_PLACEHOLDER
    return None


def project_maturity_provenance(
    evidence_by_ref: Mapping[str, DecisionEvidenceRef],
    ref_ids: Sequence[str],
) -> MaturityProvenanceProjection:
    concrete_dates: set[str] = set()
    symbolic_ref_ids: set[str] = set()
    invalid_ref_ids: set[str] = set()
    normalized_ref_ids = tuple(sorted(set(ref_ids)))
    if not normalized_ref_ids:
        invalid_ref_ids.add("<empty>")
    for ref_id in normalized_ref_ids:
        row = evidence_by_ref.get(ref_id)
        if row is None:
            invalid_ref_ids.add(ref_id)
            continue
        concrete = concrete_evidence_date(row.as_of)
        if concrete is not None:
            concrete_dates.add(concrete.isoformat())
            continue
        if symbolic_maturity_evidence_kind(row) is not None:
            symbolic_ref_ids.add(ref_id)
            continue
        invalid_ref_ids.add(ref_id)

    status: MaturityProvenanceStatus | None = None
    as_of: str | None = None
    if not invalid_ref_ids:
        if concrete_dates and symbolic_ref_ids:
            status = MaturityProvenanceStatus.CONCRETE_WITH_SYMBOLIC_REFS
            as_of = max(concrete_dates)
        elif concrete_dates:
            status = MaturityProvenanceStatus.CONCRETE_ONLY
            as_of = max(concrete_dates)
        elif symbolic_ref_ids:
            status = MaturityProvenanceStatus.SYMBOLIC_ONLY_NO_CONCRETE_DATE

    return MaturityProvenanceProjection(
        as_of=as_of,
        provenance_status=status,
        concrete_dates=tuple(sorted(concrete_dates)),
        symbolic_ref_ids=tuple(sorted(symbolic_ref_ids)),
        invalid_ref_ids=tuple(sorted(invalid_ref_ids)),
    )


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


class DriverEvidenceMaturityV2(FrozenModel):
    driver: str = Field(min_length=2, max_length=120)
    decisive: bool
    maturity: EvidenceMaturity
    supporting_evidence_refs: tuple[str, ...] = Field(min_length=1, max_length=6)
    contradicting_evidence_refs: tuple[str, ...] = Field(default=(), max_length=6)
    supporting_claim_refs: tuple[str, ...] = Field(default=(), max_length=6)
    contradicting_claim_refs: tuple[str, ...] = Field(default=(), max_length=6)
    what_remains_unproven: EvidenceClaim
    as_of: str | None
    provenance_status: MaturityProvenanceStatus

    @field_validator("as_of")
    @classmethod
    def as_of_is_null_or_real_calendar_date(cls, value: str | None) -> str | None:
        if value is not None and concrete_evidence_date(value) is None:
            raise ValueError("maturity_as_of_invalid_calendar_date")
        return value

    @model_validator(mode="after")
    def provenance_shape_is_consistent(self) -> DriverEvidenceMaturityV2:
        supporting = set(self.supporting_claim_refs)
        contradicting = set(self.contradicting_claim_refs)
        if supporting & contradicting:
            raise ValueError("maturity_atomic_claim_polarity_overlap")
        symbolic_only = (
            self.provenance_status
            == MaturityProvenanceStatus.SYMBOLIC_ONLY_NO_CONCRETE_DATE
        )
        if symbolic_only != (self.as_of is None):
            raise ValueError("maturity_provenance_status_date_mismatch")
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
    drivers: Sequence[DriverEvidenceMaturity | DriverEvidenceMaturityV2],
) -> frozenset[EvidenceMaturity]:
    return frozenset(row.maturity for row in drivers if row.decisive)
