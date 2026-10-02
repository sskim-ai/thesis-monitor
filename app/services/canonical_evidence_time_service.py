"""Canonical source time is distinct from the evidence projection context clock."""
from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from datetime import datetime
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


CONTRACT = "canonical-evidence-time-v1"


class SourceTimeKind(StrEnum):
    SOURCE_AS_OF = "SOURCE_AS_OF"
    UNDATED_DETERMINISTIC_METADATA = "UNDATED_DETERMINISTIC_METADATA"
    SOURCE_DATE_UNAVAILABLE = "SOURCE_DATE_UNAVAILABLE"


# Exact metadata families emitted by build_source_fact_catalog. This does not
# classify economic observations merely because their date happens to be empty.
UNDATED_METADATA_OWNERS = frozenset({
    ("security_identity:current", "security_identity", "deterministic_security_identity"),
    ("security_basis:current", "security_basis", "deterministic_per_security_basis"),
    ("valuation:book_quality", "valuation_quality", "deterministic_valuation_coherence"),
})


class CanonicalEvidenceTime(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    contract: Literal["canonical-evidence-time-v1"] = CONTRACT
    kind: SourceTimeKind
    subject_ticker: str = Field(min_length=1)
    canonical_ref: str = Field(min_length=1)
    canonical_fact_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    projection_at: str | None = None

    @field_validator("projection_at")
    @classmethod
    def projection_clock(cls, value):
        if value is not None:
            # A source packet can declare a date-only assessment clock. It is
            # never used as source availability or as an economic period.
            datetime.fromisoformat(value.replace("Z", "+00:00"))
        return value


def fact_sha256(fact: Mapping[str, object]) -> str:
    return hashlib.sha256(json.dumps(fact, ensure_ascii=False, sort_keys=True,
        separators=(",", ":"), default=str).encode()).hexdigest()


def source_as_of(fact: Mapping[str, object]) -> str | None:
    value = fact.get("as_of_date")
    if value is not None and not isinstance(value, str):
        raise ValueError("canonical_source_date_type_invalid")
    return value


def source_time_kind(fact: Mapping[str, object]) -> SourceTimeKind:
    value = source_as_of(fact)
    if value:
        return SourceTimeKind.SOURCE_AS_OF
    owner = (fact.get("fact_id"), fact.get("fact_type"), fact.get("source"))
    if all(isinstance(part, str) for part in owner) and owner in UNDATED_METADATA_OWNERS:
        return SourceTimeKind.UNDATED_DETERMINISTIC_METADATA
    return SourceTimeKind.SOURCE_DATE_UNAVAILABLE


def project_canonical_time(fact: Mapping[str, object], *, ticker: str,
                           projection_at: str | None) -> CanonicalEvidenceTime:
    return CanonicalEvidenceTime(kind=source_time_kind(fact), subject_ticker=ticker,
        canonical_ref="canonical:" + str(fact["fact_id"]),
        canonical_fact_sha256=fact_sha256(fact), projection_at=projection_at)


def validate_canonical_time(fact: Mapping[str, object], evidence: Mapping[str, object], *,
                            ticker: str) -> None:
    expected_ref = "canonical:" + str(fact["fact_id"])
    if (evidence.get("ref_id") != expected_ref
            or evidence.get("source_ref") != "stock.fact_catalog." + str(fact["fact_id"])):
        raise ValueError("canonical_projection_ref_mismatch")
    if evidence.get("as_of") != source_as_of(fact):
        raise ValueError("canonical_projection_source_date_mismatch")
    kind = source_time_kind(fact)
    if kind == SourceTimeKind.SOURCE_DATE_UNAVAILABLE:
        raise ValueError("canonical_undated_source_unclassified")
    metadata = evidence.get("source_time")
    if metadata is None:
        if kind == SourceTimeKind.UNDATED_DETERMINISTIC_METADATA:
            raise ValueError("canonical_undated_metadata_binding_required")
        # Pre-contract dated facts still require the exact original source date.
        return
    bound = CanonicalEvidenceTime.model_validate(metadata)
    expected = project_canonical_time(fact, ticker=ticker, projection_at=bound.projection_at)
    if bound != expected:
        raise ValueError("canonical_projection_time_binding_mismatch")
