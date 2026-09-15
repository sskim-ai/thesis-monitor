from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.services.direction_timing_ownership_service import DirectionalCoreCandidate


class FrozenStrictModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class PersistenceSourceDomain(StrEnum):
    CANONICAL_MODEL_ACCEPTED = "CANONICAL_MODEL_ACCEPTED"
    MANUAL_USER_AUTHORED = "MANUAL_USER_AUTHORED"
    LEGACY_UNVERIFIED = "LEGACY_UNVERIFIED"


class PersistenceEligibility(StrEnum):
    ELIGIBLE_CANONICAL = "ELIGIBLE_CANONICAL"
    INELIGIBLE_MANUAL_ONLY = "INELIGIBLE_MANUAL_ONLY"
    INELIGIBLE_LEGACY_UNVERIFIED = "INELIGIBLE_LEGACY_UNVERIFIED"
    REJECTED_INVALID_RECEIPT = "REJECTED_INVALID_RECEIPT"
    REJECTED_STALE = "REJECTED_STALE"
    REJECTED_QUARANTINED = "REJECTED_QUARANTINED"
    IDEMPOTENT_ALREADY_APPLIED = "IDEMPOTENT_ALREADY_APPLIED"


class ReceiptStatus(StrEnum):
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    QUARANTINED = "QUARANTINED"


class SourceEvidenceSnapshotIdentity(FrozenStrictModel):
    contract: Literal["source-evidence-snapshot-identity-v1"] = (
        "source-evidence-snapshot-identity-v1"
    )
    packet_contract: str = Field(min_length=1)
    hash_algorithm: Literal["SHA-256"] = "SHA-256"
    packet_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    subject_ticker: str = Field(min_length=1)
    component_hashes: dict[str, str | None]

    @model_validator(mode="after")
    def validate_component_hashes(self) -> "SourceEvidenceSnapshotIdentity":
        for name, digest in self.component_hashes.items():
            if not name:
                raise ValueError("source_component_hash_name_missing")
            if digest is not None and (
                len(digest) != 64 or any(character not in "0123456789abcdef" for character in digest)
            ):
                raise ValueError(f"source_component_hash_invalid:{name}")
        return self


class CanonicalAcceptanceReceiptV1(FrozenStrictModel):
    # Field order is part of the frozen 25-field public audit envelope.
    receipt_contract_version: Literal["canonical-acceptance-receipt-v1"] = (
        "canonical-acceptance-receipt-v1"
    )
    acceptance_id: str = Field(pattern=r"^ca1_[0-9a-f]{64}$")
    receipt_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    receipt_status: ReceiptStatus
    trusted_issuer_id: str
    generation_id: str = Field(min_length=1)
    generation_generated_at: datetime
    ticker: str = Field(min_length=1)
    thesis_version: int = Field(gt=0)
    assessment_date: date
    effective_at: datetime
    accepted_at: datetime
    source_packet_id: str = Field(min_length=1)
    packet_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    source_evidence_snapshot_identity: SourceEvidenceSnapshotIdentity
    accepted_payload_contract_version: str = Field(min_length=1)
    canonical_serialization_contract: Literal["canonical-json-utf8-sorted-compact-v1"] = (
        "canonical-json-utf8-sorted-compact-v1"
    )
    final_composed_candidate_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    canonical_semantic_audit_contract: str = Field(min_length=1)
    canonical_semantic_audit_status: str = Field(min_length=1)
    finalization_status: str = Field(min_length=1)
    core_immutability_status: str = Field(min_length=1)
    core_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    stance_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    quarantine_reason_codes: tuple[str, ...]

    @model_validator(mode="after")
    def require_aware_timestamps(self) -> "CanonicalAcceptanceReceiptV1":
        for value in (
            self.generation_generated_at,
            self.effective_at,
            self.accepted_at,
        ):
            if value.tzinfo is None or value.utcoffset() is None:
                raise ValueError("canonical_receipt_timestamp_must_be_offset_aware")
        return self


@dataclass(frozen=True, slots=True)
class TrustedFinalizationResult:
    generation_id: str
    generation_generated_at: datetime
    ticker: str
    thesis_version: int
    assessment_date: date
    effective_at: datetime
    source_packet_id: str
    source_packet_bytes: bytes
    source_evidence_snapshot_identity: SourceEvidenceSnapshotIdentity
    accepted_payload_contract_version: str
    accepted_payload: DirectionalCoreCandidate
    canonical_semantic_audit_contract: str
    canonical_semantic_audit_status: str
    finalization_status: str
    core_immutability_status: str
    core_hash: str
    stance_hash: str
    quarantine_reason_codes: tuple[str, ...]
    security_basis_provenance: dict[str, object]


class ReceiptVerification(FrozenStrictModel):
    valid: bool
    eligibility: PersistenceEligibility
    errors: tuple[str, ...]


class WarningObservationValue(StrEnum):
    CONFIRMED = "CONFIRMED"
    WORSENED = "WORSENED"
    RECOVERED = "RECOVERED"
    UNRESOLVED = "UNRESOLVED"


class CanonicalWarningObservationV1(FrozenStrictModel):
    contract: Literal["canonical-warning-observation-v1"] = (
        "canonical-warning-observation-v1"
    )
    warning_type: str = Field(min_length=1)
    condition_contract_version: str = Field(min_length=1)
    condition_identity: str = Field(min_length=1)
    observation: WarningObservationValue
    transition_reason_code: str = Field(min_length=1)
    transition_reason_version: str = Field(min_length=1)
    evidence_refs: tuple[str, ...]


class NotificationEventKind(StrEnum):
    DAILY_SUMMARY_NOTIFICATION = "DAILY_SUMMARY_NOTIFICATION"
    MATERIAL_STATE_TRANSITION_NOTIFICATION = "MATERIAL_STATE_TRANSITION_NOTIFICATION"


class DailySummaryNotificationV1(FrozenStrictModel):
    event_kind: Literal["DAILY_SUMMARY_NOTIFICATION"] = "DAILY_SUMMARY_NOTIFICATION"
    schedule_run_id: str = Field(min_length=1)
    channel: str = Field(min_length=1)
    payload_contract_version: str = Field(min_length=1)
    payload: dict[str, object]


class MaterialTransitionNotificationV1(FrozenStrictModel):
    event_kind: Literal["MATERIAL_STATE_TRANSITION_NOTIFICATION"] = (
        "MATERIAL_STATE_TRANSITION_NOTIFICATION"
    )
    channel: str = Field(min_length=1)
    payload_contract_version: str = Field(min_length=1)
    payload: dict[str, object]


class PersistenceApplicationResult(FrozenStrictModel):
    eligibility: PersistenceEligibility
    acceptance_id: str | None
    receipt_hash: str | None
    history_inserted: bool
    current_advanced: bool
    warning_transition_ids: tuple[str, ...]
    outbox_event_ids: tuple[str, ...]
    denial_reason: str | None = None


class CurrentAssessmentReadV2(FrozenStrictModel):
    status: Literal["AVAILABLE", "UNAVAILABLE"]
    source_domain: PersistenceSourceDomain | None
    automation_eligible: bool
    acceptance_id: str | None
    receipt_hash: str | None
    canonical_payload: dict[str, object] | None
    reason: str | None


class AssessmentHistoryReadV2(FrozenStrictModel):
    source_domain: PersistenceSourceDomain
    automation_eligible: bool
    ticker: str
    assessment_date: date
    acceptance_id: str | None
    legacy_assessment_id: int | None
    canonical_payload: dict[str, object] | None
    legacy_business_delta_projection: str | None
    legacy_projection_status: Literal["SUPPORTED", "UNSUPPORTED", "NOT_APPLICABLE"]
