from __future__ import annotations

import json
import os
from datetime import date, datetime
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from app.providers.krx_publication_provider import (
    KrxPublicationReadiness,
    PublicationReadinessStatus,
)


KRX_PUBLICATION_TELEMETRY_VERSION = "krx-publication-telemetry-v1"
KRX_PROVIDER_ROLE_POLICY_VERSION = "krx-time-slot-provider-role-v1"
KRX_EXACT_SLOT_CAPTURE_VERSION = "krx-exact-slot-capture-v1"

KrxObservationTimeSlot = Literal[
    "SAME_DAY_CLOSE_1605",
    "NEXT_MORNING_0805",
    "T_PLUS_1_RECONCILIATION",
]
KrxCaptureOrigin = Literal["launchd_calendar", "manual", "legacy_unspecified"]
KrxProviderRole = Literal[
    "SAME_DAY_CLOSE_PRIMARY",
    "NEXT_MORNING_PRIMARY",
    "T_PLUS_1_AUTHORITATIVE_RECONCILIATION",
    "HISTORICAL_ONLY",
]
KrxProviderRoleStatus = Literal[
    "SUPPORTED",
    "CANDIDATE",
    "NOT_SUPPORTED",
    "NOT_YET_PROVEN",
]


class KrxPublicationTelemetryRecord(BaseModel):
    contract_version: Literal["krx-publication-telemetry-v1"] = (
        KRX_PUBLICATION_TELEMETRY_VERSION
    )
    capture_contract_version: Literal["krx-exact-slot-capture-v1"] = (
        KRX_EXACT_SLOT_CAPTURE_VERSION
    )
    observation: KrxPublicationReadiness
    time_slot: KrxObservationTimeSlot | None = None
    capture_origin: KrxCaptureOrigin = "legacy_unspecified"
    scheduled_for: datetime | None = None
    normal_session: bool = True

    @model_validator(mode="after")
    def validate_scheduled_capture(self) -> "KrxPublicationTelemetryRecord":
        if self.scheduled_for is not None and self.scheduled_for.tzinfo is None:
            raise ValueError("scheduled capture time must be timezone-aware")
        if self.capture_origin == "launchd_calendar" and (
            self.time_slot is None or self.scheduled_for is None
        ):
            raise ValueError("launchd capture requires an exact slot and scheduled time")
        return self


class KrxPublicationTimeline(BaseModel):
    contract_version: Literal["krx-publication-telemetry-v1"] = (
        KRX_PUBLICATION_TELEMETRY_VERSION
    )
    target_session: date
    observations: list[KrxPublicationTelemetryRecord] = Field(default_factory=list)
    first_non_empty_at: datetime | None = None
    first_complete_at: datetime | None = None
    observed_complete_by: datetime | None = None
    last_empty_at: datetime | None = None
    publication_window_start: datetime | None = None
    publication_window_end: datetime | None = None
    latest_readiness: PublicationReadinessStatus | None = None

    @model_validator(mode="after")
    def validate_observation_order(self) -> "KrxPublicationTimeline":
        observed_at = [item.observation.observed_at for item in self.observations]
        if any(value.tzinfo is None for value in observed_at):
            raise ValueError("publication telemetry times must be timezone-aware")
        if observed_at != sorted(observed_at) or len(observed_at) != len(set(observed_at)):
            raise ValueError("publication telemetry must be strictly append-only")
        if any(
            item.observation.target_session != self.target_session
            for item in self.observations
        ):
            raise ValueError("publication telemetry cannot mix target sessions")
        if self.first_complete_at and not self.observed_complete_by:
            raise ValueError("first complete requires an observed-complete bound")
        if bool(self.publication_window_start) != bool(self.publication_window_end):
            raise ValueError("publication window requires both interval bounds")
        return self


class KrxProviderRoleEvidence(BaseModel):
    time_slot: KrxObservationTimeSlot
    target_session: date
    observed_at: datetime
    readiness: PublicationReadinessStatus
    normal_session: bool = True


class KrxProviderRoleDecision(BaseModel):
    role: KrxProviderRole
    status: KrxProviderRoleStatus
    observed_sessions: int
    complete_sessions: int
    incomplete_sessions: int
    required_complete_sessions: int
    reason: str


class KrxProviderRoleMatrix(BaseModel):
    contract_version: Literal["krx-time-slot-provider-role-v1"] = (
        KRX_PROVIDER_ROLE_POLICY_VERSION
    )
    decisions: list[KrxProviderRoleDecision]


def build_krx_publication_timeline(
    records: list[KrxPublicationTelemetryRecord],
) -> KrxPublicationTimeline:
    if not records:
        raise ValueError("publication timeline requires at least one observation")
    target_session = records[0].observation.target_session
    observed_at = [record.observation.observed_at for record in records]
    if observed_at != sorted(observed_at) or len(observed_at) != len(set(observed_at)):
        raise ValueError("publication telemetry must be strictly append-only")
    if any(record.observation.target_session != target_session for record in records):
        raise ValueError("publication telemetry cannot mix target sessions")

    first_non_empty = next(
        (
            record.observation.observed_at
            for record in records
            if any(item.row_count > 0 for item in record.observation.endpoints)
        ),
        None,
    )
    complete_index = next(
        (
            index
            for index, record in enumerate(records)
            if record.observation.status == "PROVIDER_COMPLETE"
        ),
        None,
    )
    observed_complete_by = (
        records[complete_index].observation.observed_at
        if complete_index is not None
        else None
    )
    first_complete = observed_complete_by if complete_index not in {None, 0} else None
    last_empty = next(
        (
            record.observation.observed_at
            for record in reversed(records)
            if record.observation.status == "MARKET_COMPLETED_PROVIDER_PENDING"
        ),
        None,
    )
    window_start: datetime | None = None
    window_end: datetime | None = None
    if complete_index not in {None, 0}:
        prior = records[complete_index - 1].observation
        if prior.status in {"MARKET_COMPLETED_PROVIDER_PENDING", "PROVIDER_PARTIAL"}:
            window_start = prior.observed_at
            window_end = observed_complete_by

    return KrxPublicationTimeline(
        target_session=target_session,
        observations=records,
        first_non_empty_at=first_non_empty,
        first_complete_at=first_complete,
        observed_complete_by=observed_complete_by,
        last_empty_at=last_empty,
        publication_window_start=window_start,
        publication_window_end=window_end,
        latest_readiness=records[-1].observation.status,
    )


def load_krx_publication_records(path: Path) -> list[KrxPublicationTelemetryRecord]:
    if not path.exists():
        return []
    records: list[KrxPublicationTelemetryRecord] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            records.append(KrxPublicationTelemetryRecord.model_validate_json(line))
        except ValueError as exc:
            raise ValueError(
                f"invalid KRX publication telemetry at line {line_number}"
            ) from exc
    return records


def append_krx_publication_observation(
    observation: KrxPublicationReadiness,
    directory: Path,
    *,
    time_slot: KrxObservationTimeSlot | None = None,
    capture_origin: KrxCaptureOrigin = "legacy_unspecified",
    scheduled_for: datetime | None = None,
    normal_session: bool = True,
) -> KrxPublicationTimeline:
    path = directory / f"{observation.target_session.isoformat()}.jsonl"
    records = load_krx_publication_records(path)
    record = KrxPublicationTelemetryRecord(
        observation=observation,
        time_slot=time_slot,
        capture_origin=capture_origin,
        scheduled_for=scheduled_for,
        normal_session=normal_session,
    )
    candidate = [*records, record]
    timeline = build_krx_publication_timeline(candidate)

    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = (
        json.dumps(record.model_dump(mode="json"), sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")
    descriptor = os.open(path, os.O_APPEND | os.O_CREAT | os.O_WRONLY, 0o600)
    try:
        os.write(descriptor, encoded)
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    return timeline


def role_evidence_from_records(
    records: list[KrxPublicationTelemetryRecord],
) -> list[KrxProviderRoleEvidence]:
    return [
        KrxProviderRoleEvidence(
            time_slot=record.time_slot,
            target_session=record.observation.target_session,
            observed_at=record.observation.observed_at,
            readiness=record.observation.status,
            normal_session=record.normal_session,
        )
        for record in records
        if record.time_slot is not None
        and record.capture_origin == "launchd_calendar"
    ]


def _decide_role(
    *,
    role: KrxProviderRole,
    evidence: list[KrxProviderRoleEvidence],
    required_complete_sessions: int,
) -> KrxProviderRoleDecision:
    latest_by_session: dict[date, KrxProviderRoleEvidence] = {}
    for item in sorted(evidence, key=lambda value: value.observed_at):
        if item.normal_session:
            latest_by_session[item.target_session] = item
    latest = list(latest_by_session.values())
    complete = sum(item.readiness == "PROVIDER_COMPLETE" for item in latest)
    incomplete = len(latest) - complete

    if complete >= required_complete_sessions and incomplete == 0:
        status: KrxProviderRoleStatus = "SUPPORTED"
        reason = "required normal-session complete observations passed"
    elif complete > 0:
        status = "CANDIDATE"
        reason = "complete evidence exists but the multi-session gate is not closed"
    elif len(latest) >= 3:
        status = "NOT_SUPPORTED"
        reason = "three or more normal-session observations completed without readiness"
    else:
        status = "NOT_YET_PROVEN"
        reason = "insufficient time-slot-specific normal-session evidence"
    return KrxProviderRoleDecision(
        role=role,
        status=status,
        observed_sessions=len(latest),
        complete_sessions=complete,
        incomplete_sessions=incomplete,
        required_complete_sessions=required_complete_sessions,
        reason=reason,
    )


def determine_krx_provider_roles(
    evidence: list[KrxProviderRoleEvidence],
    *,
    historical_supported: bool,
) -> KrxProviderRoleMatrix:
    slot_to_role: list[tuple[KrxObservationTimeSlot, KrxProviderRole, int]] = [
        ("SAME_DAY_CLOSE_1605", "SAME_DAY_CLOSE_PRIMARY", 5),
        ("NEXT_MORNING_0805", "NEXT_MORNING_PRIMARY", 5),
        (
            "T_PLUS_1_RECONCILIATION",
            "T_PLUS_1_AUTHORITATIVE_RECONCILIATION",
            3,
        ),
    ]
    decisions = [
        _decide_role(
            role=role,
            evidence=[item for item in evidence if item.time_slot == slot],
            required_complete_sessions=required,
        )
        for slot, role, required in slot_to_role
    ]
    decisions.append(
        KrxProviderRoleDecision(
            role="HISTORICAL_ONLY",
            status="SUPPORTED" if historical_supported else "NOT_YET_PROVEN",
            observed_sessions=0,
            complete_sessions=0,
            incomplete_sessions=0,
            required_complete_sessions=1,
            reason=(
                "archive-only historical retrieval and breadth validation passed"
                if historical_supported
                else "historical capability has not been validated"
            ),
        )
    )
    return KrxProviderRoleMatrix(decisions=decisions)
