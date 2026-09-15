from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import Connection, inspect, insert, select, update
from sqlmodel import Session

from app.models.accepted_assessment import assessment_source_registry_v2
from app.schemas.accepted_assessment_v2 import PersistenceSourceDomain


SOURCE_CLASSIFICATION_CONTRACT = "assessment-source-classification-v2"


class AssessmentSourceRegistryError(RuntimeError):
    pass


def classify_legacy_assessment(
    connection: Connection,
    *,
    assessment_id: int,
    source_domain: PersistenceSourceDomain,
    classified_at: datetime | None = None,
) -> bool:
    if source_domain == PersistenceSourceDomain.CANONICAL_MODEL_ACCEPTED:
        raise AssessmentSourceRegistryError("canonical_source_not_allowed_for_legacy_row")
    existing = connection.execute(
        select(assessment_source_registry_v2).where(
            assessment_source_registry_v2.c.legacy_assessment_id == assessment_id
        )
    ).mappings().first()
    values = {
        "source_domain": source_domain.value,
        "automation_eligible": False,
        "classification_contract": SOURCE_CLASSIFICATION_CONTRACT,
        "classified_at_utc": (classified_at or datetime.now(UTC)).astimezone(UTC),
    }
    if existing is None:
        connection.execute(
            insert(assessment_source_registry_v2).values(
                legacy_assessment_id=assessment_id,
                **values,
            )
        )
        return True
    if existing["source_domain"] == source_domain.value:
        return False
    if (
        existing["source_domain"] == PersistenceSourceDomain.LEGACY_UNVERIFIED.value
        and source_domain == PersistenceSourceDomain.MANUAL_USER_AUTHORED
    ):
        connection.execute(
            update(assessment_source_registry_v2)
            .where(assessment_source_registry_v2.c.legacy_assessment_id == assessment_id)
            .values(**values)
        )
        return True
    raise AssessmentSourceRegistryError("legacy_source_classification_conflict")


def classify_manual_assessment_in_session(
    session: Session,
    *,
    assessment_id: int,
    enabled: bool,
) -> bool:
    if not enabled:
        return False
    connection = session.connection()
    if not inspect(connection).has_table(assessment_source_registry_v2.name):
        raise AssessmentSourceRegistryError("enabled_manual_registry_table_missing")
    return classify_legacy_assessment(
        connection,
        assessment_id=assessment_id,
        source_domain=PersistenceSourceDomain.MANUAL_USER_AUTHORED,
    )
