from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from datetime import UTC, date, datetime

from pydantic import ValidationError

from app.schemas.accepted_assessment_v2 import (
    CanonicalAcceptanceReceiptV1,
    PersistenceEligibility,
    ReceiptStatus,
    ReceiptVerification,
    SourceEvidenceSnapshotIdentity,
    TrustedFinalizationResult,
)
from app.services.direction_timing_ownership_service import (
    CORE_OUTPUT_CONTRACT,
    DirectionalCoreCandidate,
)


RECEIPT_CONTRACT_VERSION = "canonical-acceptance-receipt-v1"
CANONICAL_SERIALIZATION_CONTRACT = "canonical-json-utf8-sorted-compact-v1"
ACCEPTED_ASSESSMENT_CONTRACT = "accepted-assessment-v2"
TRUSTED_ISSUER_ID = "canonical_two_stage_finalizer_v1"
TRUSTED_ISSUERS = frozenset({TRUSTED_ISSUER_ID})
SUPPORTED_CANONICAL_AUDIT_CONTRACTS = frozenset({"directional-core-semantic-audit-v1"})
SECURITY_BASIS_PROVENANCE_COMPONENT = "security_basis_provenance_sha256"
_CANONICAL_TICKER = re.compile(r"^(?:[0-9]{6}|[A-Z][A-Z0-9.-]{0,14})$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


class CanonicalReceiptError(ValueError):
    pass


def _is_canonical_ticker(value: object) -> bool:
    return isinstance(value, str) and _CANONICAL_TICKER.fullmatch(value) is not None


def canonical_json(value: object) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )


def canonical_sha256(value: object) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def bytes_sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def normalize_utc(value: datetime, *, field: str) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise CanonicalReceiptError(f"{field}_must_be_offset_aware")
    return value.astimezone(UTC)


def canonical_timestamp(value: datetime, *, field: str) -> str:
    return normalize_utc(value, field=field).isoformat().replace("+00:00", "Z")


def source_evidence_snapshot_identity(
    *,
    packet_bytes: bytes,
    packet_contract: str,
    ticker: str,
    component_hashes: Mapping[str, str | None] | None = None,
) -> SourceEvidenceSnapshotIdentity:
    if not packet_contract:
        raise CanonicalReceiptError("source_packet_contract_missing")
    if not _is_canonical_ticker(ticker):
        raise CanonicalReceiptError("source_snapshot_ticker_not_canonical")
    components = dict(component_hashes or {})
    for key, digest in components.items():
        if not key:
            raise CanonicalReceiptError("source_component_hash_name_missing")
        if digest is not None and not _SHA256.fullmatch(digest):
            raise CanonicalReceiptError(f"source_component_hash_invalid:{key}")
    return SourceEvidenceSnapshotIdentity(
        packet_contract=packet_contract,
        packet_digest=bytes_sha256(packet_bytes),
        subject_ticker=ticker,
        component_hashes=components,
    )


def trusted_finalization_result(
    *,
    generation_id: str,
    generation_generated_at: datetime,
    ticker: str,
    thesis_version: int,
    assessment_date: date,
    effective_at: datetime,
    source_packet_id: str,
    source_packet_bytes: bytes,
    source_snapshot: SourceEvidenceSnapshotIdentity,
    accepted_payload: DirectionalCoreCandidate,
    canonical_semantic_audit_contract: str,
    canonical_semantic_audit_status: str,
    finalization_status: str,
    core_immutability_status: str,
    core_hash: str,
    stance_hash: str,
    quarantine_reason_codes: tuple[str, ...] = (),
    security_basis_provenance: Mapping[str, object] | None = None,
) -> TrustedFinalizationResult:
    """Construct the internal typed capability consumed by the receipt issuer."""

    if not isinstance(accepted_payload, DirectionalCoreCandidate):
        raise CanonicalReceiptError("trusted_payload_type_required")
    if not isinstance(source_snapshot, SourceEvidenceSnapshotIdentity):
        raise CanonicalReceiptError("trusted_source_snapshot_type_required")
    result = TrustedFinalizationResult(
        generation_id=generation_id,
        generation_generated_at=normalize_utc(
            generation_generated_at,
            field="generation_generated_at",
        ),
        ticker=ticker,
        thesis_version=thesis_version,
        assessment_date=assessment_date,
        effective_at=normalize_utc(effective_at, field="effective_at"),
        source_packet_id=source_packet_id,
        source_packet_bytes=bytes(source_packet_bytes),
        source_evidence_snapshot_identity=source_snapshot,
        accepted_payload_contract_version=CORE_OUTPUT_CONTRACT,
        accepted_payload=accepted_payload,
        canonical_semantic_audit_contract=canonical_semantic_audit_contract,
        canonical_semantic_audit_status=canonical_semantic_audit_status,
        finalization_status=finalization_status,
        core_immutability_status=core_immutability_status,
        core_hash=core_hash,
        stance_hash=stance_hash,
        quarantine_reason_codes=tuple(quarantine_reason_codes),
        security_basis_provenance=dict(security_basis_provenance or {}),
    )
    _trusted_result_errors(result, require_acceptance=True)
    return result


def _trusted_result_errors(
    result: TrustedFinalizationResult,
    *,
    require_acceptance: bool,
) -> tuple[str, ...]:
    errors: list[str] = []
    if not isinstance(result, TrustedFinalizationResult):
        return ("trusted_finalization_result_type_required",)
    if not isinstance(result.accepted_payload, DirectionalCoreCandidate):
        errors.append("trusted_payload_type_required")
    if not isinstance(
        result.source_evidence_snapshot_identity,
        SourceEvidenceSnapshotIdentity,
    ):
        errors.append("trusted_source_snapshot_type_required")
    if not isinstance(result.source_packet_bytes, bytes):
        errors.append("trusted_source_packet_bytes_required")
    if errors:
        if require_acceptance:
            raise CanonicalReceiptError(";".join(errors))
        return tuple(errors)
    if not result.generation_id:
        errors.append("generation_id_missing")
    if not _is_canonical_ticker(result.ticker):
        errors.append("ticker_not_canonical")
    if result.accepted_payload.ticker != result.ticker:
        errors.append("payload_ticker_mismatch")
    if result.thesis_version <= 0:
        errors.append("thesis_version_not_positive")
    if not result.source_packet_id:
        errors.append("source_packet_id_missing")
    for field, value in (
        ("generation_generated_at", result.generation_generated_at),
        ("effective_at", result.effective_at),
    ):
        if value.tzinfo is None or value.utcoffset() is None:
            errors.append(f"{field}_must_be_offset_aware")
    packet_hash = bytes_sha256(result.source_packet_bytes)
    snapshot = result.source_evidence_snapshot_identity
    if snapshot.packet_digest != packet_hash:
        errors.append("source_snapshot_packet_digest_mismatch")
    if snapshot.subject_ticker != result.ticker:
        errors.append("source_snapshot_ticker_mismatch")
    security_basis_hash = canonical_sha256(result.security_basis_provenance)
    if snapshot.component_hashes.get(SECURITY_BASIS_PROVENANCE_COMPONENT) != security_basis_hash:
        errors.append("security_basis_provenance_not_receipt_bound")
    if result.accepted_payload_contract_version != CORE_OUTPUT_CONTRACT:
        errors.append("accepted_payload_contract_unsupported")
    if result.canonical_semantic_audit_contract not in SUPPORTED_CANONICAL_AUDIT_CONTRACTS:
        errors.append("canonical_semantic_audit_contract_unsupported")
    if not _SHA256.fullmatch(result.core_hash):
        errors.append("core_hash_invalid")
    if not _SHA256.fullmatch(result.stance_hash):
        errors.append("stance_hash_invalid")
    if require_acceptance:
        if result.canonical_semantic_audit_status != "PASS":
            errors.append("canonical_semantic_audit_not_pass")
        if result.finalization_status != "PASS":
            errors.append("finalization_not_pass")
        if result.core_immutability_status != "PASS":
            errors.append("core_immutability_not_pass")
        if result.quarantine_reason_codes:
            errors.append("result_quarantined")
    if errors and require_acceptance:
        raise CanonicalReceiptError(";".join(errors))
    return tuple(errors)


def accepted_payload_dict(result: TrustedFinalizationResult) -> dict[str, object]:
    return result.accepted_payload.model_dump(mode="json")


def accepted_payload_hash(result: TrustedFinalizationResult) -> str:
    return canonical_sha256(accepted_payload_dict(result))


def _receipt_material(result: TrustedFinalizationResult) -> dict[str, object]:
    return {
        "receipt_contract_version": RECEIPT_CONTRACT_VERSION,
        "receipt_status": ReceiptStatus.ACCEPTED.value,
        "trusted_issuer_id": TRUSTED_ISSUER_ID,
        "generation_id": result.generation_id,
        "generation_generated_at": canonical_timestamp(
            result.generation_generated_at,
            field="generation_generated_at",
        ),
        "ticker": result.ticker,
        "thesis_version": result.thesis_version,
        "assessment_date": result.assessment_date.isoformat(),
        "effective_at": canonical_timestamp(result.effective_at, field="effective_at"),
        "source_packet_id": result.source_packet_id,
        "packet_hash": bytes_sha256(result.source_packet_bytes),
        "source_evidence_snapshot_identity": (
            result.source_evidence_snapshot_identity.model_dump(mode="json")
        ),
        "accepted_payload_contract_version": result.accepted_payload_contract_version,
        "canonical_serialization_contract": CANONICAL_SERIALIZATION_CONTRACT,
        "final_composed_candidate_hash": accepted_payload_hash(result),
        "canonical_semantic_audit_contract": result.canonical_semantic_audit_contract,
        "canonical_semantic_audit_status": result.canonical_semantic_audit_status,
        "finalization_status": result.finalization_status,
        "core_immutability_status": result.core_immutability_status,
        "core_hash": result.core_hash,
        "stance_hash": result.stance_hash,
        "quarantine_reason_codes": list(result.quarantine_reason_codes),
    }


def acceptance_id_for(result: TrustedFinalizationResult) -> str:
    if not isinstance(result, TrustedFinalizationResult):
        raise CanonicalReceiptError("trusted_finalization_result_type_required")
    _trusted_result_errors(result, require_acceptance=True)
    digest = canonical_sha256(
        {
            "domain": "canonical-acceptance-id-v1",
            "receipt_material": _receipt_material(result),
        }
    )
    return f"ca1_{digest}"


def issue_canonical_acceptance_receipt(
    result: TrustedFinalizationResult,
    *,
    accepted_at: datetime | None = None,
    existing_receipt: CanonicalAcceptanceReceiptV1 | None = None,
) -> CanonicalAcceptanceReceiptV1:
    if not isinstance(result, TrustedFinalizationResult):
        raise CanonicalReceiptError("trusted_finalization_result_type_required")
    _trusted_result_errors(result, require_acceptance=True)
    acceptance_id = acceptance_id_for(result)
    if existing_receipt is not None:
        verification = verify_canonical_acceptance_receipt(
            existing_receipt,
            trusted_result=result,
        )
        if not verification.valid or existing_receipt.acceptance_id != acceptance_id:
            raise CanonicalReceiptError("existing_receipt_identity_conflict")
        return existing_receipt

    issued_at = normalize_utc(accepted_at or datetime.now(UTC), field="accepted_at")
    values = {
        **_receipt_material(result),
        "acceptance_id": acceptance_id,
        "accepted_at": canonical_timestamp(issued_at, field="accepted_at"),
    }
    receipt_hash = canonical_sha256(
        {
            "domain": "canonical-acceptance-receipt-hash-v1",
            "receipt": values,
        }
    )
    return CanonicalAcceptanceReceiptV1.model_validate(
        {
            **values,
            "receipt_hash": receipt_hash,
        }
    )


def _receipt_acceptance_material(receipt: CanonicalAcceptanceReceiptV1) -> dict[str, object]:
    values = receipt.model_dump(mode="json")
    for field in ("acceptance_id", "receipt_hash", "accepted_at"):
        values.pop(field)
    return values


def recompute_acceptance_id(receipt: CanonicalAcceptanceReceiptV1) -> str:
    digest = canonical_sha256(
        {
            "domain": "canonical-acceptance-id-v1",
            "receipt_material": _receipt_acceptance_material(receipt),
        }
    )
    return f"ca1_{digest}"


def recompute_receipt_hash(receipt: CanonicalAcceptanceReceiptV1) -> str:
    values = receipt.model_dump(mode="json")
    values.pop("receipt_hash")
    return canonical_sha256(
        {
            "domain": "canonical-acceptance-receipt-hash-v1",
            "receipt": values,
        }
    )


def parse_receipt(value: object) -> CanonicalAcceptanceReceiptV1:
    try:
        return CanonicalAcceptanceReceiptV1.model_validate(value)
    except ValidationError as exc:
        raise CanonicalReceiptError("canonical_receipt_envelope_invalid") from exc


def verify_canonical_acceptance_receipt(
    receipt: CanonicalAcceptanceReceiptV1,
    *,
    trusted_result: TrustedFinalizationResult | None = None,
    accepted_payload: Mapping[str, object] | None = None,
) -> ReceiptVerification:
    errors: list[str] = []
    if not isinstance(receipt, CanonicalAcceptanceReceiptV1):
        return ReceiptVerification(
            valid=False,
            eligibility=PersistenceEligibility.REJECTED_INVALID_RECEIPT,
            errors=("canonical_receipt_type_required",),
        )
    if receipt.receipt_contract_version != RECEIPT_CONTRACT_VERSION:
        errors.append("receipt_contract_unsupported")
    if receipt.canonical_serialization_contract != CANONICAL_SERIALIZATION_CONTRACT:
        errors.append("canonical_serialization_contract_unsupported")
    if receipt.accepted_payload_contract_version != CORE_OUTPUT_CONTRACT:
        errors.append("accepted_payload_contract_unsupported")
    if receipt.trusted_issuer_id not in TRUSTED_ISSUERS:
        errors.append("trusted_issuer_not_allowed")
    if not _is_canonical_ticker(receipt.ticker):
        errors.append("ticker_not_canonical")
    if receipt.thesis_version <= 0:
        errors.append("thesis_version_not_positive")
    for field, value in (
        ("generation_generated_at", receipt.generation_generated_at),
        ("effective_at", receipt.effective_at),
        ("accepted_at", receipt.accepted_at),
    ):
        if value.tzinfo is None or value.utcoffset() is None:
            errors.append(f"{field}_must_be_offset_aware")
    if recompute_acceptance_id(receipt) != receipt.acceptance_id:
        errors.append("acceptance_id_mismatch")
    if recompute_receipt_hash(receipt) != receipt.receipt_hash:
        errors.append("receipt_hash_mismatch")
    if receipt.receipt_status != ReceiptStatus.ACCEPTED:
        errors.append("receipt_not_accepted")
    if receipt.canonical_semantic_audit_contract not in SUPPORTED_CANONICAL_AUDIT_CONTRACTS:
        errors.append("canonical_semantic_audit_contract_unsupported")
    if receipt.canonical_semantic_audit_status != "PASS":
        errors.append("canonical_semantic_audit_not_pass")
    if receipt.finalization_status != "PASS":
        errors.append("finalization_not_pass")
    if receipt.core_immutability_status != "PASS":
        errors.append("core_immutability_not_pass")
    if receipt.quarantine_reason_codes:
        errors.append("receipt_quarantined")
    if receipt.source_evidence_snapshot_identity.packet_digest != receipt.packet_hash:
        errors.append("source_snapshot_packet_digest_mismatch")
    if receipt.source_evidence_snapshot_identity.subject_ticker != receipt.ticker:
        errors.append("source_snapshot_ticker_mismatch")
    if accepted_payload is not None:
        if not isinstance(accepted_payload, Mapping):
            errors.append("accepted_payload_mapping_required")
        elif canonical_sha256(dict(accepted_payload)) != receipt.final_composed_candidate_hash:
            errors.append("accepted_payload_hash_mismatch")
    if trusted_result is not None:
        trusted_errors = _trusted_result_errors(trusted_result, require_acceptance=False)
        errors.extend(trusted_errors)
        expected = _receipt_material(trusted_result)
        actual = receipt.model_dump(mode="json")
        for field, expected_value in expected.items():
            if actual[field] != expected_value:
                errors.append(f"trusted_result_identity_mismatch:{field}")
        if receipt.acceptance_id != acceptance_id_for(trusted_result):
            errors.append("trusted_result_acceptance_id_mismatch")
    quarantined = receipt.receipt_status == ReceiptStatus.QUARANTINED or bool(
        receipt.quarantine_reason_codes
    )
    eligibility = (
        PersistenceEligibility.REJECTED_QUARANTINED
        if quarantined
        else PersistenceEligibility.REJECTED_INVALID_RECEIPT
        if errors
        else PersistenceEligibility.ELIGIBLE_CANONICAL
    )
    return ReceiptVerification(
        valid=not errors,
        eligibility=eligibility,
        errors=tuple(dict.fromkeys(errors)),
    )
