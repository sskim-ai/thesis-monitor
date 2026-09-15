from __future__ import annotations

import json
from datetime import UTC, date, datetime, time

from sqlalchemy import Engine, MetaData, Table, inspect, select

from app.models.accepted_assessment import (
    accepted_assessment_v2,
    assessment_source_registry_v2,
    canonical_acceptance_receipt_v1,
    monitoring_current_state_v2,
)
from app.schemas.accepted_assessment_v2 import (
    AssessmentHistoryReadV2,
    CurrentAssessmentReadV2,
    PersistenceSourceDomain,
)
from app.services.accepted_assessment_persistence_service import (
    PersistenceV2IntegrityError,
    receipt_from_row,
    require_local_ephemeral_engine,
    validate_extract_consistency,
)
from app.services.canonical_acceptance_receipt_service import (
    SECURITY_BASIS_PROVENANCE_COMPONENT,
    verify_canonical_acceptance_receipt,
)


_LEGACY_BUSINESS_DELTA = {
    "STRENGTHENED": "strengthened",
    "UNCHANGED": "no_material_change",
    "WEAKENED": "weakened",
    "UNRESOLVED": None,
}


def project_canonical_business_delta_to_legacy(value: str) -> tuple[str | None, str]:
    if value not in _LEGACY_BUSINESS_DELTA:
        return None, "UNSUPPORTED"
    projection = _LEGACY_BUSINESS_DELTA[value]
    return projection, "SUPPORTED" if projection is not None else "UNSUPPORTED"


def _legacy_current(engine: Engine, ticker: str) -> CurrentAssessmentReadV2:
    inspector = inspect(engine)
    if not inspector.has_table("thesisassessment"):
        return CurrentAssessmentReadV2(
            status="UNAVAILABLE",
            source_domain=None,
            automation_eligible=False,
            acceptance_id=None,
            receipt_hash=None,
            canonical_payload=None,
            reason="no_v2_or_legacy_assessment",
        )
    legacy = Table("thesisassessment", MetaData(), autoload_with=engine)
    with engine.connect() as connection:
        row = connection.execute(
            select(legacy)
            .where(legacy.c.ticker == ticker)
            .order_by(legacy.c.assessment_date.desc(), legacy.c.id.desc())
            .limit(1)
        ).mappings().first()
        if row is None:
            return CurrentAssessmentReadV2(
                status="UNAVAILABLE",
                source_domain=None,
                automation_eligible=False,
                acceptance_id=None,
                receipt_hash=None,
                canonical_payload=None,
                reason="no_v2_or_legacy_assessment",
            )
        source = PersistenceSourceDomain.LEGACY_UNVERIFIED
        if inspector.has_table(assessment_source_registry_v2.name):
            classified = connection.execute(
                select(assessment_source_registry_v2.c.source_domain).where(
                    assessment_source_registry_v2.c.legacy_assessment_id == row["id"]
                )
            ).scalar_one_or_none()
            if classified is not None:
                source = PersistenceSourceDomain(str(classified))
    return CurrentAssessmentReadV2(
        status="AVAILABLE",
        source_domain=source,
        automation_eligible=False,
        acceptance_id=None,
        receipt_hash=None,
        canonical_payload=None,
        reason="legacy_manual_compatibility_read",
    )


def read_current_assessment_v2(
    engine: Engine,
    ticker: str,
    *,
    allow_local_ephemeral: bool = False,
) -> CurrentAssessmentReadV2:
    require_local_ephemeral_engine(engine, explicitly_enabled=allow_local_ephemeral)
    inspector = inspect(engine)
    required = {
        monitoring_current_state_v2.name,
        accepted_assessment_v2.name,
        canonical_acceptance_receipt_v1.name,
    }
    if not required.issubset(inspector.get_table_names()):
        return _legacy_current(engine, ticker)
    with engine.connect() as connection:
        current = connection.execute(
            select(monitoring_current_state_v2).where(
                monitoring_current_state_v2.c.ticker == ticker
            )
        ).mappings().first()
        if current is None:
            return _legacy_current(engine, ticker)
        acceptance_id = str(current["latest_acceptance_id"])
        history = connection.execute(
            select(accepted_assessment_v2).where(
                accepted_assessment_v2.c.acceptance_id == acceptance_id
            )
        ).mappings().first()
        receipt_row = connection.execute(
            select(canonical_acceptance_receipt_v1).where(
                canonical_acceptance_receipt_v1.c.acceptance_id == acceptance_id
            )
        ).mappings().first()
    if history is None or receipt_row is None:
        return CurrentAssessmentReadV2(
            status="UNAVAILABLE",
            source_domain=PersistenceSourceDomain.CANONICAL_MODEL_ACCEPTED,
            automation_eligible=False,
            acceptance_id=acceptance_id,
            receipt_hash=None,
            canonical_payload=None,
            reason="corrupt_v2_current_pointer",
        )
    try:
        validate_extract_consistency(history)
        payload = json.loads(str(history["canonical_payload_json"]))
        receipt = receipt_from_row(receipt_row)
        verification = verify_canonical_acceptance_receipt(
            receipt,
            accepted_payload=payload,
        )
        if (
            not verification.valid
            or receipt.acceptance_id != acceptance_id
            or receipt.ticker != ticker
            or history["acceptance_id"] != acceptance_id
            or history["ticker"] != ticker
            or history["canonical_payload_sha256"]
            != receipt.final_composed_candidate_hash
            or history["security_basis_provenance_sha256"]
            != receipt.source_evidence_snapshot_identity.component_hashes.get(
                SECURITY_BASIS_PROVENANCE_COMPONENT
            )
            or current["latest_effective_at_utc"] != history["effective_at_utc"]
            or current["latest_generation_generated_at_utc"]
            != history["generation_generated_at_utc"]
            or current["latest_generation_id"] != history["generation_id"]
            or current["latest_ordering_acceptance_id"] != acceptance_id
        ):
            raise PersistenceV2IntegrityError("v2_current_integrity_failure")
    except (ValueError, TypeError, json.JSONDecodeError, PersistenceV2IntegrityError):
        return CurrentAssessmentReadV2(
            status="UNAVAILABLE",
            source_domain=PersistenceSourceDomain.CANONICAL_MODEL_ACCEPTED,
            automation_eligible=False,
            acceptance_id=acceptance_id,
            receipt_hash=(str(receipt_row["receipt_hash"]) if receipt_row else None),
            canonical_payload=None,
            reason="corrupt_v2_current_pointer",
        )
    return CurrentAssessmentReadV2(
        status="AVAILABLE",
        source_domain=PersistenceSourceDomain.CANONICAL_MODEL_ACCEPTED,
        automation_eligible=True,
        acceptance_id=acceptance_id,
        receipt_hash=receipt.receipt_hash,
        canonical_payload=payload,
        reason=None,
    )


def read_assessment_history_v2(
    engine: Engine,
    ticker: str,
    *,
    allow_local_ephemeral: bool = False,
) -> tuple[AssessmentHistoryReadV2, ...]:
    require_local_ephemeral_engine(engine, explicitly_enabled=allow_local_ephemeral)
    inspector = inspect(engine)
    results: list[tuple[tuple[object, ...], AssessmentHistoryReadV2]] = []
    with engine.connect() as connection:
        if inspector.has_table(accepted_assessment_v2.name):
            canonical_rows = connection.execute(
                select(accepted_assessment_v2).where(accepted_assessment_v2.c.ticker == ticker)
            ).mappings().all()
            receipt_rows = {
                str(row["acceptance_id"]): row
                for row in connection.execute(
                    select(canonical_acceptance_receipt_v1).where(
                        canonical_acceptance_receipt_v1.c.ticker == ticker
                    )
                )
                .mappings()
                .all()
            }
            for row in canonical_rows:
                validate_extract_consistency(row)
                payload = json.loads(str(row["canonical_payload_json"]))
                acceptance_id = str(row["acceptance_id"])
                receipt_row = receipt_rows.get(acceptance_id)
                if receipt_row is None:
                    raise PersistenceV2IntegrityError("v2_history_receipt_missing")
                receipt = receipt_from_row(receipt_row)
                verification = verify_canonical_acceptance_receipt(
                    receipt,
                    accepted_payload=payload,
                )
                if (
                    not verification.valid
                    or receipt.acceptance_id != acceptance_id
                    or receipt.ticker != ticker
                    or row["canonical_payload_sha256"]
                    != receipt.final_composed_candidate_hash
                    or row["security_basis_provenance_sha256"]
                    != receipt.source_evidence_snapshot_identity.component_hashes.get(
                        SECURITY_BASIS_PROVENANCE_COMPONENT
                    )
                ):
                    raise PersistenceV2IntegrityError("v2_history_integrity_failure")
                projection, projection_status = project_canonical_business_delta_to_legacy(
                    str(row["canonical_business_delta"])
                )
                results.append(
                    (
                        (
                            _as_utc(row["effective_at_utc"]),
                            _as_utc(row["generation_generated_at_utc"]),
                            row["generation_id"],
                            acceptance_id,
                        ),
                        AssessmentHistoryReadV2(
                            source_domain=PersistenceSourceDomain.CANONICAL_MODEL_ACCEPTED,
                            automation_eligible=True,
                            ticker=ticker,
                            assessment_date=row["assessment_date"],
                            acceptance_id=acceptance_id,
                            legacy_assessment_id=None,
                            canonical_payload=payload,
                            legacy_business_delta_projection=projection,
                            legacy_projection_status=projection_status,
                        ),
                    )
                )
        if inspector.has_table("thesisassessment"):
            legacy = Table("thesisassessment", MetaData(), autoload_with=engine)
            legacy_rows = connection.execute(
                select(legacy).where(legacy.c.ticker == ticker)
            ).mappings().all()
            registry: dict[int, str] = {}
            if inspector.has_table(assessment_source_registry_v2.name):
                registry = {
                    int(row["legacy_assessment_id"]): str(row["source_domain"])
                    for row in connection.execute(select(assessment_source_registry_v2))
                    .mappings()
                    .all()
                }
            for row in legacy_rows:
                assessment_date = row["assessment_date"]
                if isinstance(assessment_date, str):
                    assessment_date = date.fromisoformat(assessment_date)
                source = PersistenceSourceDomain(
                    registry.get(
                        int(row["id"]),
                        PersistenceSourceDomain.LEGACY_UNVERIFIED.value,
                    )
                )
                results.append(
                    (
                        (
                            datetime.combine(assessment_date, time.min, tzinfo=UTC),
                            datetime.min.replace(tzinfo=UTC),
                            "",
                            str(row["id"]),
                        ),
                        AssessmentHistoryReadV2(
                            source_domain=source,
                            automation_eligible=False,
                            ticker=ticker,
                            assessment_date=assessment_date,
                            acceptance_id=None,
                            legacy_assessment_id=int(row["id"]),
                            canonical_payload=None,
                            legacy_business_delta_projection=(
                                str(row.get("business_thesis_change") or row.get("status") or "")
                                or None
                            ),
                            legacy_projection_status="NOT_APPLICABLE",
                        ),
                    )
                )
    results.sort(key=lambda item: item[0], reverse=True)
    return tuple(item[1] for item in results)


def _as_utc(value: object) -> datetime:
    if not isinstance(value, datetime):
        raise PersistenceV2IntegrityError("history_ordering_timestamp_invalid")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)
