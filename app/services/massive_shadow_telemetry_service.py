from __future__ import annotations

import hashlib
import json
import os
from datetime import date, datetime, time
from pathlib import Path
from typing import Literal
from zoneinfo import ZoneInfo

from pydantic import BaseModel

from app.providers.massive_us_market_provider import massive_reference_session_age
from app.services.market_cross_section_service import MarketCrossSection


MASSIVE_SHADOW_TELEMETRY_VERSION = "massive-0805-shadow-v1"
SEOUL = ZoneInfo("Asia/Seoul")


class MassiveShadowObservation(BaseModel):
    contract: Literal["massive-0805-shadow-v1"] = MASSIVE_SHADOW_TELEMETRY_VERSION
    target_session: date
    observed_at: datetime
    readiness: Literal[
        "READY_AT_0805",
        "LATE_BUT_BEFORE_0815",
        "LATE_AFTER_0815",
        "INCOMPLETE",
        "PROVIDER_ERROR",
    ]
    request_status: str
    grouped_row_count: int
    reference_request_date: date
    reference_cache_age_calendar_days: int
    reference_cache_age_trading_days: int
    eligible_count: int
    advance_count: int
    decline_count: int
    unchanged_count: int
    previous_session_complete: bool
    calculation_finish_time: datetime
    provider_latency_seconds: float | None
    errors: list[str]
    grouped_response_sha256: str
    reference_response_sha256: str


def classify_massive_readiness(
    *, observed_at: datetime, complete: bool, provider_error: bool = False
) -> str:
    if provider_error:
        return "PROVIDER_ERROR"
    if not complete:
        return "INCOMPLETE"
    local = observed_at.astimezone(SEOUL)
    observed_time = local.timetz().replace(tzinfo=None)
    if observed_time <= time(8, 5):
        return "READY_AT_0805"
    if observed_time <= time(8, 15):
        return "LATE_BUT_BEFORE_0815"
    return "LATE_AFTER_0815"


def build_massive_shadow_observation(
    *,
    section: MarketCrossSection,
    current_envelope: dict[str, object],
    previous_envelope: dict[str, object],
    reference_envelope: dict[str, object],
    observed_at: datetime,
    errors: list[str] | None = None,
) -> MassiveShadowObservation:
    if observed_at.tzinfo is None:
        raise ValueError("Massive telemetry observation time must be timezone-aware")
    breadth = section.breadth
    current_payload = current_envelope.get("payload")
    previous_payload = previous_envelope.get("payload")
    current_rows = (
        current_payload.get("results") if isinstance(current_payload, dict) else None
    )
    previous_rows = (
        previous_payload.get("results") if isinstance(previous_payload, dict) else None
    )
    complete = bool(
        breadth
        and section.quality.coverage == "full"
        and section.quality.freshness == "fresh"
        and isinstance(current_rows, list)
        and current_rows
        and isinstance(previous_rows, list)
        and previous_rows
    )
    reference_date = date.fromisoformat(str(reference_envelope["request_date"]))
    reference_trading_age = massive_reference_session_age(
        reference_date,
        section.session_date,
    )
    return MassiveShadowObservation(
        target_session=section.session_date,
        observed_at=observed_at,
        readiness=classify_massive_readiness(
            observed_at=observed_at,
            complete=complete,
        ),
        request_status="ok" if complete else "incomplete",
        grouped_row_count=len(current_rows) if isinstance(current_rows, list) else 0,
        reference_request_date=reference_date,
        reference_cache_age_calendar_days=(section.session_date - reference_date).days,
        reference_cache_age_trading_days=reference_trading_age,
        eligible_count=breadth.eligible_count if breadth else 0,
        advance_count=breadth.advance_count if breadth else 0,
        decline_count=breadth.decline_count if breadth else 0,
        unchanged_count=breadth.unchanged_count if breadth else 0,
        previous_session_complete=bool(previous_rows),
        calculation_finish_time=datetime.now(tz=SEOUL),
        provider_latency_seconds=(
            float(current_envelope["latency_seconds"])
            if isinstance(current_envelope.get("latency_seconds"), (int, float))
            else None
        ),
        errors=errors or [],
        grouped_response_sha256=str(current_envelope.get("response_sha256") or ""),
        reference_response_sha256=str(reference_envelope.get("response_sha256") or ""),
    )


def persist_massive_shadow_observation(
    observation: MassiveShadowObservation, directory: Path
) -> Path:
    path = directory / f"{observation.target_session.isoformat()}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = observation.model_dump(mode="json")
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    envelope = {
        "observation": payload,
        "observation_sha256": hashlib.sha256(encoded).hexdigest(),
    }
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(
        json.dumps(envelope, sort_keys=True, separators=(",", ":")),
        encoding="utf-8",
    )
    os.replace(temporary, path)
    return path
