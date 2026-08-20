from __future__ import annotations

import os
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pytest

from app.providers.krx_publication_provider import (
    CORE_READINESS_ENDPOINTS,
    KrxEndpointReadiness,
    KrxPublicationReadiness,
    PublicationReadinessStatus,
)
from app.services.krx_publication_service import (
    KrxPublicationTelemetryRecord,
    append_krx_publication_observation,
    build_krx_publication_timeline,
    determine_krx_provider_roles,
    load_krx_publication_records,
    role_evidence_from_records,
)


SESSION = date(2026, 8, 18)
START = datetime(2026, 8, 18, 7, 5, tzinfo=timezone.utc)


def _observation(
    status: PublicationReadinessStatus,
    observed_at: datetime,
) -> KrxPublicationReadiness:
    endpoint_status = {
        "MARKET_COMPLETED_PROVIDER_PENDING": "EMPTY",
        "PROVIDER_PARTIAL": "READY",
        "PROVIDER_COMPLETE": "READY",
        "PROVIDER_ERROR": "ERROR",
        "STALE_PROVIDER_DATE": "STALE",
        "MARKET_NOT_COMPLETED": "EMPTY",
    }[status]
    endpoints = [
        KrxEndpointReadiness(
            endpoint=endpoint,
            status=endpoint_status,
            http_status=200,
            row_count=1 if endpoint_status == "READY" else 0,
            payload_sha256="a" * 64,
        )
        for endpoint in CORE_READINESS_ENDPOINTS
    ]
    if status == "PROVIDER_PARTIAL":
        endpoints[-1].status = "EMPTY"
        endpoints[-1].row_count = 0
    return KrxPublicationReadiness(
        status=status,
        target_session=SESSION,
        latest_completed_session=SESSION,
        observed_at=observed_at,
        endpoints=endpoints,
        observed_complete_by=observed_at if status == "PROVIDER_COMPLETE" else None,
        last_empty_at=(
            observed_at
            if status == "MARKET_COMPLETED_PROVIDER_PENDING"
            else None
        ),
        current_snapshot_promotable=status == "PROVIDER_COMPLETE",
    )


def _record(
    status: PublicationReadinessStatus,
    observed_at: datetime,
) -> KrxPublicationTelemetryRecord:
    return KrxPublicationTelemetryRecord(
        observation=_observation(status, observed_at)
    )


def test_timeline_tracks_observed_transition_without_false_provider_time() -> None:
    timeline = build_krx_publication_timeline(
        [
            _record("MARKET_COMPLETED_PROVIDER_PENDING", START),
            _record("PROVIDER_PARTIAL", START + timedelta(hours=1)),
            _record("PROVIDER_COMPLETE", START + timedelta(hours=2)),
        ]
    )

    assert timeline.first_non_empty_at == START + timedelta(hours=1)
    assert timeline.first_complete_at == START + timedelta(hours=2)
    assert timeline.observed_complete_by == START + timedelta(hours=2)
    assert timeline.publication_window_start == START + timedelta(hours=1)
    assert timeline.publication_window_end == START + timedelta(hours=2)


def test_initial_complete_is_only_an_observed_complete_upper_bound() -> None:
    timeline = build_krx_publication_timeline(
        [_record("PROVIDER_COMPLETE", START)]
    )

    assert timeline.first_non_empty_at == START
    assert timeline.first_complete_at is None
    assert timeline.observed_complete_by == START


def test_append_is_strict_and_private(tmp_path: Path) -> None:
    directory = tmp_path / "telemetry"
    append_krx_publication_observation(
        _observation("MARKET_COMPLETED_PROVIDER_PENDING", START),
        directory,
        time_slot="SAME_DAY_CLOSE_1605",
        capture_origin="launchd_calendar",
        scheduled_for=START,
    )

    path = directory / f"{SESSION.isoformat()}.jsonl"
    assert len(load_krx_publication_records(path)) == 1
    assert os.stat(path).st_mode & 0o777 == 0o600

    with pytest.raises(ValueError, match="strictly append-only"):
        append_krx_publication_observation(
            _observation("MARKET_COMPLETED_PROVIDER_PENDING", START),
            directory,
            time_slot="SAME_DAY_CLOSE_1605",
            capture_origin="launchd_calendar",
            scheduled_for=START,
        )
    assert len(load_krx_publication_records(path)) == 1


def test_only_launchd_exact_slot_records_count_as_role_evidence() -> None:
    manual = KrxPublicationTelemetryRecord(
        observation=_observation("PROVIDER_COMPLETE", START),
        time_slot="SAME_DAY_CLOSE_1605",
        capture_origin="manual",
        scheduled_for=START,
    )
    natural = KrxPublicationTelemetryRecord(
        observation=_observation("PROVIDER_COMPLETE", START + timedelta(days=1)),
        time_slot="SAME_DAY_CLOSE_1605",
        capture_origin="launchd_calendar",
        scheduled_for=START + timedelta(days=1),
    )

    evidence = role_evidence_from_records([manual, natural])

    assert len(evidence) == 1
    assert evidence[0].observed_at == START + timedelta(days=1)


def test_role_gates_remain_separate() -> None:
    records = [
        KrxPublicationTelemetryRecord(
            observation=_observation(
                "PROVIDER_COMPLETE", START + timedelta(days=offset)
            ).model_copy(
                update={"target_session": SESSION + timedelta(days=offset)}
            ),
            time_slot="SAME_DAY_CLOSE_1605",
            capture_origin="launchd_calendar",
            scheduled_for=START + timedelta(days=offset),
        )
        for offset in range(5)
    ]

    matrix = determine_krx_provider_roles(
        role_evidence_from_records(records),
        historical_supported=True,
    )
    decisions = {item.role: item.status for item in matrix.decisions}

    assert decisions["SAME_DAY_CLOSE_PRIMARY"] == "SUPPORTED"
    assert decisions["NEXT_MORNING_PRIMARY"] == "NOT_YET_PROVEN"
    assert decisions["T_PLUS_1_AUTHORITATIVE_RECONCILIATION"] == "NOT_YET_PROVEN"
    assert decisions["HISTORICAL_ONLY"] == "SUPPORTED"
