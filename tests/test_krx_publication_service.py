from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pytest

from app.providers.krx_kr_market_provider import (
    CORE_READINESS_ENDPOINTS,
    KrxEndpointReadiness,
    KrxPublicationReadiness,
    PublicationReadinessStatus,
)
from app.services.krx_publication_service import (
    KrxProviderRoleEvidence,
    KrxPublicationTelemetryRecord,
    append_krx_publication_observation,
    build_krx_publication_timeline,
    determine_krx_provider_roles,
    load_krx_publication_records,
)


SESSION = date(2026, 8, 18)
START = datetime(2026, 8, 18, 11, 27, tzinfo=timezone.utc)


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
            row_count=(1 if endpoint_status == "READY" else 0),
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
        observed_complete_by=(observed_at if status == "PROVIDER_COMPLETE" else None),
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


def test_timeline_tracks_observed_transition_without_false_publication_time() -> None:
    records = [
        _record("MARKET_COMPLETED_PROVIDER_PENDING", START),
        _record("PROVIDER_PARTIAL", START + timedelta(hours=1)),
        _record("PROVIDER_COMPLETE", START + timedelta(hours=2)),
    ]

    timeline = build_krx_publication_timeline(records)

    assert timeline.first_non_empty_at == START + timedelta(hours=1)
    assert timeline.first_complete_at == START + timedelta(hours=2)
    assert timeline.observed_complete_by == START + timedelta(hours=2)
    assert timeline.last_empty_at == START
    assert timeline.publication_window_start == START + timedelta(hours=1)
    assert timeline.publication_window_end == START + timedelta(hours=2)


def test_initial_complete_is_only_an_observed_complete_upper_bound() -> None:
    timeline = build_krx_publication_timeline(
        [_record("PROVIDER_COMPLETE", START)]
    )

    assert timeline.first_non_empty_at == START
    assert timeline.first_complete_at is None
    assert timeline.observed_complete_by == START
    assert timeline.publication_window_start is None
    assert timeline.publication_window_end is None


def test_append_only_telemetry_rejects_non_monotonic_observation(tmp_path: Path) -> None:
    directory = tmp_path / "telemetry"
    append_krx_publication_observation(
        _observation("MARKET_COMPLETED_PROVIDER_PENDING", START),
        directory,
    )

    with pytest.raises(ValueError, match="strictly append-only"):
        append_krx_publication_observation(
            _observation(
                "MARKET_COMPLETED_PROVIDER_PENDING",
                START - timedelta(minutes=1),
            ),
            directory,
        )

    path = directory / f"{SESSION.isoformat()}.jsonl"
    assert len(load_krx_publication_records(path)) == 1


def _role_evidence(
    slot: str,
    session_offset: int,
    readiness: PublicationReadinessStatus,
) -> KrxProviderRoleEvidence:
    return KrxProviderRoleEvidence(
        time_slot=slot,
        target_session=SESSION + timedelta(days=session_offset),
        observed_at=START + timedelta(days=session_offset),
        readiness=readiness,
    )


def test_one_morning_complete_is_candidate_not_same_day_primary() -> None:
    matrix = determine_krx_provider_roles(
        [
            _role_evidence(
                "SAME_DAY_CLOSE_1605",
                0,
                "MARKET_COMPLETED_PROVIDER_PENDING",
            ),
            _role_evidence("NEXT_MORNING_0805", 0, "PROVIDER_COMPLETE"),
        ],
        historical_supported=True,
    )
    decisions = {item.role: item for item in matrix.decisions}

    assert decisions["SAME_DAY_CLOSE_PRIMARY"].status == "NOT_YET_PROVEN"
    assert decisions["NEXT_MORNING_PRIMARY"].status == "CANDIDATE"
    assert decisions["T_PLUS_1_AUTHORITATIVE_RECONCILIATION"].status == (
        "NOT_YET_PROVEN"
    )
    assert decisions["HISTORICAL_ONLY"].status == "SUPPORTED"


def test_five_clean_same_day_sessions_support_primary_role() -> None:
    matrix = determine_krx_provider_roles(
        [
            _role_evidence("SAME_DAY_CLOSE_1605", offset, "PROVIDER_COMPLETE")
            for offset in range(5)
        ],
        historical_supported=True,
    )
    same_day = next(
        item for item in matrix.decisions if item.role == "SAME_DAY_CLOSE_PRIMARY"
    )

    assert same_day.status == "SUPPORTED"
    assert same_day.complete_sessions == 5


def test_three_pending_sessions_mark_time_slot_not_supported() -> None:
    matrix = determine_krx_provider_roles(
        [
            _role_evidence(
                "SAME_DAY_CLOSE_1605",
                offset,
                "MARKET_COMPLETED_PROVIDER_PENDING",
            )
            for offset in range(3)
        ],
        historical_supported=True,
    )
    same_day = next(
        item for item in matrix.decisions if item.role == "SAME_DAY_CLOSE_PRIMARY"
    )

    assert same_day.status == "NOT_SUPPORTED"
