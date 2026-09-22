from __future__ import annotations

import hashlib
import json
from collections.abc import Sequence
from typing import Literal, Protocol

from pydantic import Field

from app.services.cross_market_decision_engine_service import (
    EvidenceClaim,
    EvidencePolarity,
    EvidenceReasonRole,
    FrozenModel,
    PolarityEvidenceClaim,
)


CONTRACT_VERSION = "stage2-maturity-polarity-adapter-v1"
ATOMIC_IDENTITY_CONTRACT = "maturity-atomic-claim-identity-v1"
CLAIM_REF_PREFIX = "maturity-claim:"


class MaturityAtomicClaim(FrozenModel):
    contract: Literal["maturity-atomic-claim-identity-v1"] = ATOMIC_IDENTITY_CONTRACT
    claim_ref: str = Field(pattern=r"^maturity-claim:[0-9a-f]{64}$")
    ticker: str
    claim: PolarityEvidenceClaim

    @property
    def parent_source_refs(self) -> tuple[str, ...]:
        return self.claim.evidence_refs


class MaturityClaimAssignment(Protocol):
    supporting_evidence_refs: tuple[str, ...]
    contradicting_evidence_refs: tuple[str, ...]
    supporting_claim_refs: tuple[str, ...]
    contradicting_claim_refs: tuple[str, ...]


def _canonical_sha256(value: object) -> str:
    payload = json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode()).hexdigest()


def maturity_atomic_claim_ref(*, ticker: str, claim: EvidenceClaim) -> str:
    """Identify a structured proposition independently from its assigned polarity."""
    identity = {
        "contract": ATOMIC_IDENTITY_CONTRACT,
        "ticker": ticker,
        "text": claim.text,
        "evidence_refs": sorted(claim.evidence_refs),
        "logical_condition": (
            claim.logical_condition.model_dump(mode="json")
            if claim.logical_condition is not None
            else None
        ),
    }
    return CLAIM_REF_PREFIX + _canonical_sha256(identity)


def _owned_claim(
    *,
    ticker: str,
    claim: EvidenceClaim,
    polarity: EvidencePolarity,
) -> MaturityAtomicClaim:
    polarity_claim = PolarityEvidenceClaim(
        text=claim.text,
        evidence_refs=claim.evidence_refs,
        logical_condition=claim.logical_condition,
        polarity=polarity,
        reason_role=EvidenceReasonRole.FUNDAMENTAL,
    )
    return MaturityAtomicClaim(
        claim_ref=maturity_atomic_claim_ref(ticker=ticker, claim=claim),
        ticker=ticker,
        claim=polarity_claim,
    )


def stage2_maturity_atomic_claim_catalog(
    *,
    ticker: str,
    buy_drivers: Sequence[EvidenceClaim],
    sell_drivers: Sequence[EvidenceClaim],
) -> tuple[MaturityAtomicClaim, ...]:
    """Project frozen structured drivers through the existing polarity vocabulary."""
    projected = (
        *(
            _owned_claim(ticker=ticker, claim=claim, polarity=EvidencePolarity.BULLISH)
            for claim in buy_drivers
        ),
        *(
            _owned_claim(ticker=ticker, claim=claim, polarity=EvidencePolarity.BEARISH)
            for claim in sell_drivers
        ),
    )
    by_ref: dict[str, MaturityAtomicClaim] = {}
    for row in projected:
        existing = by_ref.get(row.claim_ref)
        if existing is not None and existing != row:
            raise ValueError(f"maturity_atomic_claim_identity_conflict:{row.claim_ref}")
        by_ref[row.claim_ref] = row
    return tuple(by_ref[key] for key in sorted(by_ref))


def maturity_atomic_assignment_errors(
    assignments: Sequence[MaturityClaimAssignment],
    *,
    catalog: Sequence[MaturityAtomicClaim],
) -> tuple[str, ...]:
    by_ref = {row.claim_ref: row for row in catalog}
    errors: list[str] = []
    for index, assignment in enumerate(assignments):
        supporting_claims = tuple(assignment.supporting_claim_refs)
        contradicting_claims = tuple(assignment.contradicting_claim_refs)
        if not supporting_claims:
            errors.append(f"maturity_atomic_claim_identity_missing:{index}:supporting")
        if len(supporting_claims) != len(set(supporting_claims)):
            errors.append(f"maturity_duplicate_supporting_atomic_claim:{index}")
        if len(contradicting_claims) != len(set(contradicting_claims)):
            errors.append(f"maturity_duplicate_contradicting_atomic_claim:{index}")
        overlap = set(supporting_claims) & set(contradicting_claims)
        errors.extend(
            f"maturity_same_atomic_claim_overlap:{index}:{claim_ref}"
            for claim_ref in sorted(overlap)
        )
        unknown = (set(supporting_claims) | set(contradicting_claims)) - set(by_ref)
        errors.extend(
            f"maturity_unknown_atomic_claim:{index}:{claim_ref}"
            for claim_ref in sorted(unknown)
        )

        known_supporting = tuple(
            by_ref[claim_ref] for claim_ref in supporting_claims if claim_ref in by_ref
        )
        known_contradicting = tuple(
            by_ref[claim_ref] for claim_ref in contradicting_claims if claim_ref in by_ref
        )
        expected_supporting_sources = {
            source_ref
            for claim in known_supporting
            for source_ref in claim.parent_source_refs
        }
        expected_contradicting_sources = {
            source_ref
            for claim in known_contradicting
            for source_ref in claim.parent_source_refs
        }
        actual_supporting_sources = set(assignment.supporting_evidence_refs)
        actual_contradicting_sources = set(assignment.contradicting_evidence_refs)
        if expected_supporting_sources != actual_supporting_sources:
            errors.append(f"maturity_supporting_source_claim_mismatch:{index}")
        if expected_contradicting_sources != actual_contradicting_sources:
            errors.append(f"maturity_contradicting_source_claim_mismatch:{index}")

        parent_overlap = actual_supporting_sources & actual_contradicting_sources
        for source_ref in sorted(parent_overlap):
            support_children = {
                claim.claim_ref
                for claim in known_supporting
                if source_ref in claim.parent_source_refs
            }
            contradict_children = {
                claim.claim_ref
                for claim in known_contradicting
                if source_ref in claim.parent_source_refs
            }
            if not support_children or not contradict_children or support_children & contradict_children:
                errors.append(
                    f"maturity_unproven_parent_source_overlap:{index}:{source_ref}"
                )
    return tuple(dict.fromkeys(errors))
