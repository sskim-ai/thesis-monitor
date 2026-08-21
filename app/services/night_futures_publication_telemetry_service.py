from __future__ import annotations

import hashlib
import json
import os
from datetime import date, datetime, time
from pathlib import Path
from typing import Literal
from zoneinfo import ZoneInfo

from pydantic import BaseModel, Field

from app.config import get_settings
from app.jobs.probe_krx_night_futures import TARGET_PRODUCTS
from app.macro.providers.base import MacroProviderResult
from app.services.market_session import preceding_exchange_session_date


KST = ZoneInfo("Asia/Seoul")
NIGHT_FUTURES_ATTEMPT_ARCHIVE_VERSION = "night-futures-attempt-archive-v1"
NIGHT_FUTURES_PUBLICATION_TELEMETRY_VERSION = (
    "night-futures-publication-telemetry-v1"
)
DEFAULT_OBSERVER_HORIZON = time(9, 15)

NightFuturesAttemptClassification = Literal[
    "PROVIDER_EMPTY",
    "PROVIDER_ERROR",
    "PARSER_ERROR",
    "CANONICALIZATION_ERROR",
    "STALE_PRIOR_SESSION_PRESENT",
    "EXPECTED_SESSION_ABSENT",
    "EXPECTED_SESSION_PRESENT_NO_MATCHING_DAY",
    "EXPECTED_SESSION_PRESENT_CONTRACT_MISMATCH",
    "EXPECTED_SESSION_PRESENT_PROVIDER_CONFLICT",
    "EXPECTED_SESSION_PRESENT_PARTIAL_READY",
    "EXPECTED_SESSION_PRESENT_READY",
]


class NightFuturesProductAttempt(BaseModel):
    product: str
    instrument: str
    contract: str | None = None
    maturity: str | None = None
    expected_night_bas_dd: date | None = None
    returned_night_bas_dd: date | None = None
    matched_day_bas_dd: date | None = None
    row_state: str
    readiness: str
    rejection_reason: str | None = None
    provider_change_crosscheck_status: str = "NOT_OBSERVED"


class NightFuturesAttemptRecord(BaseModel):
    contract_version: Literal["night-futures-attempt-archive-v1"] = (
        NIGHT_FUTURES_ATTEMPT_ARCHIVE_VERSION
    )
    publication_contract_version: Literal[
        "night-futures-publication-telemetry-v1"
    ] = NIGHT_FUTURES_PUBLICATION_TELEMETRY_VERSION
    attempt_id: str
    observation_group_id: str
    run_id: str
    market_packet_id: str | None = None
    market_date: date
    timestamp_start: datetime
    timestamp_end: datetime
    role: str
    production_or_observer: Literal["production", "observer"]
    expected_night_bas_dd: date | None
    expected_preceding_day_bas_dd: date | None
    xkrx_calendar_basis: str = "preceding-eligible-XKRX-DAY-v1"
    provider_http_statuses: list[int] = Field(default_factory=list)
    provider_business_dates_returned: list[date] = Field(default_factory=list)
    provider_night_business_dates_returned: list[date] = Field(default_factory=list)
    raw_row_count: int = 0
    parsed_row_count: int = 0
    candidate_product_count: int = 0
    ready_product_count: int = 0
    per_product: list[NightFuturesProductAttempt] = Field(default_factory=list)
    parser_status: str = "NOT_OBSERVED"
    canonicalization_status: str = "NOT_OBSERVED"
    provider_change_crosscheck_status: str = "NOT_OBSERVED"
    error: str | None = None
    raw_refs: list[dict[str, object]] = Field(default_factory=list)
    raw_sha256: str | None = None
    terminal_classification: NightFuturesAttemptClassification
    backup_path_provider_attempted: bool = False
    backup_path_reason: str = "backup AI path does not query night-futures provider"
    user_visible_integration: bool = False
    production_state_mutation: bool = False


class NightFuturesPublicationReceipt(BaseModel):
    contract_version: Literal[
        "night-futures-publication-telemetry-v1"
    ] = NIGHT_FUTURES_PUBLICATION_TELEMETRY_VERSION
    observation_group_id: str
    target_expected_session: date | None
    market_date: date
    terminal_state: str
    first_observed_ready_at: datetime | None = None
    first_observed_products: list[str] = Field(default_factory=list)
    raw_refs: list[dict[str, object]] = Field(default_factory=list)
    raw_sha256: str | None = None
    previous_observation_at: datetime | None = None
    previous_observation_state: str | None = None
    availability_interval: str | None = None
    first_provider_availability_time: str
    deadline_verdict: str = "DEADLINE_UNPROVEN"
    user_visible_integration: bool = False


def default_telemetry_directory() -> Path:
    return Path(get_settings().data_dir) / "telemetry/night-futures-publication"


def _as_kst(value: datetime) -> datetime:
    if value.tzinfo is None:
        raise ValueError("night-futures telemetry time must be timezone-aware")
    return value.astimezone(KST)


def observation_group_id(market_date: date, expected_session: date | None) -> str:
    identity = f"{market_date.isoformat()}|{expected_session or 'unknown'}"
    return "night-futures-" + hashlib.sha256(identity.encode()).hexdigest()[:16]


def attempt_id(group_id: str, role: str, started_at: datetime) -> str:
    identity = f"{group_id}|{role}|{started_at.isoformat()}"
    return "attempt-" + hashlib.sha256(identity.encode()).hexdigest()[:20]


def _group_directory(
    directory: Path,
    market_date: date,
    group_id: str,
) -> Path:
    return (
        directory
        / f"{market_date.year:04d}"
        / f"{market_date.month:02d}"
        / f"{market_date.day:02d}"
        / group_id
    )


def _atomic_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    descriptor = os.open(temporary, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    try:
        os.write(descriptor, encoded)
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    os.replace(temporary, path)


def _product_attempts(
    telemetry: dict[str, object],
) -> list[NightFuturesProductAttempt]:
    raw = telemetry.get("product_statuses")
    by_product: dict[str, NightFuturesProductAttempt] = {}
    if isinstance(raw, list):
        for item in raw:
            if not isinstance(item, dict):
                continue
            product = str(item.get("product") or "").strip()
            if not product:
                continue
            by_product[product] = NightFuturesProductAttempt(
                product=product,
                instrument=product,
                contract=(str(item["contract_code"]) if item.get("contract_code") else None),
                maturity=(str(item["maturity"]) if item.get("maturity") else None),
                expected_night_bas_dd=item.get("expected_night_bas_dd"),
                returned_night_bas_dd=item.get("returned_night_bas_dd"),
                matched_day_bas_dd=item.get("matched_day_bas_dd"),
                row_state=str(item.get("row_state") or "UNKNOWN"),
                readiness=str(item.get("readiness") or "NOT_READY"),
                rejection_reason=(
                    str(item["rejection_reason"])
                    if item.get("rejection_reason")
                    else None
                ),
                provider_change_crosscheck_status=str(
                    item.get("provider_change_crosscheck_status") or "NOT_OBSERVED"
                ),
            )
    return [
        by_product.get(product)
        or NightFuturesProductAttempt(
            product=product,
            instrument=product,
            row_state="NO_TELEMETRY",
            readiness="NOT_READY",
            rejection_reason="product_telemetry_unavailable",
        )
        for product in TARGET_PRODUCTS
    ]


def _date_values(value: object) -> list[date]:
    if not isinstance(value, list):
        return []
    result: set[date] = set()
    for item in value:
        if isinstance(item, date):
            result.add(item)
            continue
        try:
            result.add(date.fromisoformat(str(item)))
        except ValueError:
            continue
    return sorted(result)


def _raw_evidence(
    telemetry: dict[str, object],
) -> tuple[list[int], list[dict[str, object]], str | None]:
    statuses: set[int] = set()
    refs: list[dict[str, object]] = []
    raw_statuses = telemetry.get("date_statuses")
    if isinstance(raw_statuses, list):
        for item in raw_statuses:
            if not isinstance(item, dict):
                continue
            status = item.get("http_status")
            if isinstance(status, int):
                statuses.add(status)
            ref = {
                "service": "fut_bydd_trd",
                "query_date": item.get("query_date"),
                "http_status": status,
                "row_count": item.get("row_count", 0),
                "raw_payload_sha256": item.get("raw_payload_sha256"),
            }
            refs.append(ref)
    hashes = sorted(
        str(item["raw_payload_sha256"])
        for item in refs
        if item.get("raw_payload_sha256")
    )
    aggregate_sha = (
        hashlib.sha256("|".join(hashes).encode()).hexdigest() if hashes else None
    )
    return sorted(statuses), refs, aggregate_sha


def classify_attempt(
    *,
    telemetry: dict[str, object],
    products: list[NightFuturesProductAttempt],
    expected_session: date | None,
    error: str | None,
) -> NightFuturesAttemptClassification:
    reason = str(telemetry.get("reason") or "")
    if (
        error
        or str(telemetry.get("status") or "") == "not_configured"
        or reason.startswith("krx_fetch_failed:")
    ):
        return "PROVIDER_ERROR"
    raw_rows = int(telemetry.get("row_count") or 0)
    if raw_rows == 0:
        return "PROVIDER_EMPTY"
    if telemetry.get("parser_status") == "PARSER_ERROR":
        return "PARSER_ERROR"
    ready = [item for item in products if item.readiness == "READY"]
    if len(ready) == len(TARGET_PRODUCTS):
        return "EXPECTED_SESSION_PRESENT_READY"
    if ready:
        return "EXPECTED_SESSION_PRESENT_PARTIAL_READY"
    reasons = {item.rejection_reason for item in products}
    if "provider_change_conflict" in reasons:
        return "EXPECTED_SESSION_PRESENT_PROVIDER_CONFLICT"
    if "contract_or_maturity_mismatch" in reasons:
        return "EXPECTED_SESSION_PRESENT_CONTRACT_MISMATCH"
    if "matching_preceding_day_contract_unavailable" in reasons:
        return "EXPECTED_SESSION_PRESENT_NO_MATCHING_DAY"
    night_dates = _date_values(telemetry.get("returned_night_session_dates"))
    if expected_session and night_dates and max(night_dates) < expected_session:
        return "STALE_PRIOR_SESSION_PRESENT"
    if expected_session not in night_dates:
        return "EXPECTED_SESSION_ABSENT"
    return "CANONICALIZATION_ERROR"


def build_attempt_record(
    *,
    market_date: date,
    started_at: datetime,
    ended_at: datetime,
    role: str,
    production_or_observer: Literal["production", "observer"],
    expected_session: date | None,
    result: MacroProviderResult | None,
    error: str | None = None,
    market_packet_id: str | None = None,
) -> NightFuturesAttemptRecord:
    started = _as_kst(started_at)
    ended = _as_kst(ended_at)
    telemetry = dict(result.telemetry) if result is not None else {}
    products = _product_attempts(telemetry)
    group_id = observation_group_id(market_date, expected_session)
    http_statuses, raw_refs, raw_sha = _raw_evidence(telemetry)
    business_dates = _date_values(telemetry.get("returned_business_dates"))
    night_dates = _date_values(telemetry.get("returned_night_session_dates"))
    return NightFuturesAttemptRecord(
        attempt_id=attempt_id(group_id, role, started),
        observation_group_id=group_id,
        run_id=f"daily_us:{market_date.isoformat()}",
        market_packet_id=market_packet_id,
        market_date=market_date,
        timestamp_start=started,
        timestamp_end=ended,
        role=role,
        production_or_observer=production_or_observer,
        expected_night_bas_dd=expected_session,
        expected_preceding_day_bas_dd=(
            preceding_exchange_session_date("XKRX", expected_session)
            if expected_session
            else None
        ),
        provider_http_statuses=http_statuses,
        provider_business_dates_returned=business_dates,
        provider_night_business_dates_returned=night_dates,
        raw_row_count=int(telemetry.get("row_count") or 0),
        parsed_row_count=int(telemetry.get("parsed_row_count") or 0),
        candidate_product_count=sum(
            item.returned_night_bas_dd == expected_session for item in products
        ),
        ready_product_count=sum(item.readiness == "READY" for item in products),
        per_product=products,
        parser_status=str(telemetry.get("parser_status") or "NOT_OBSERVED"),
        canonicalization_status=str(
            telemetry.get("canonicalization_status") or "NOT_OBSERVED"
        ),
        provider_change_crosscheck_status=str(
            telemetry.get("provider_change_crosscheck_status") or "NOT_OBSERVED"
        ),
        error=error,
        raw_refs=raw_refs,
        raw_sha256=raw_sha,
        terminal_classification=classify_attempt(
            telemetry=telemetry,
            products=products,
            expected_session=expected_session,
            error=error,
        ),
    )


def persist_attempt(
    record: NightFuturesAttemptRecord,
    directory: Path | None = None,
) -> tuple[Path, bool]:
    root = directory or default_telemetry_directory()
    group = _group_directory(root, record.market_date, record.observation_group_id)
    path = group / "attempts" / f"{record.attempt_id}.json"
    if path.exists():
        return path, False
    _atomic_json(path, record.model_dump(mode="json"))
    return path, True


def load_group_attempts(
    directory: Path,
    market_date: date,
    group_id: str,
) -> list[NightFuturesAttemptRecord]:
    attempts = _group_directory(directory, market_date, group_id) / "attempts"
    if not attempts.exists():
        return []
    records = [
        NightFuturesAttemptRecord.model_validate_json(path.read_text(encoding="utf-8"))
        for path in attempts.glob("*.json")
    ]
    return sorted(records, key=lambda item: (item.timestamp_end, item.attempt_id))


def maybe_persist_terminal_receipt(
    *,
    directory: Path,
    market_date: date,
    group_id: str,
    horizon_reached: bool,
) -> NightFuturesPublicationReceipt | None:
    attempts = load_group_attempts(directory, market_date, group_id)
    ready_index = next(
        (
            index
            for index, item in enumerate(attempts)
            if item.terminal_classification == "EXPECTED_SESSION_PRESENT_READY"
        ),
        None,
    )
    if ready_index is None and not horizon_reached:
        return None
    ready = attempts[ready_index] if ready_index is not None else None
    previous = (
        attempts[ready_index - 1]
        if ready_index is not None and ready_index > 0
        else (attempts[-1] if attempts else None)
    )
    expected = attempts[0].expected_night_bas_dd if attempts else None
    if ready is not None:
        deadline = datetime.combine(market_date, time(8, 20), tzinfo=KST)
        backup = datetime.combine(market_date, time(8, 45), tzinfo=KST)
        if ready.timestamp_end <= deadline:
            terminal_state = "READY_WITHIN_PRODUCTION_WINDOW"
        elif ready.timestamp_end <= backup:
            terminal_state = "READY_SHORTLY_AFTER_DEADLINE"
        else:
            terminal_state = "READY_ONLY_AFTER_BACKUP_WINDOW"
        start = previous.timestamp_end if previous else deadline
        interval = f"({start.isoformat()},{ready.timestamp_end.isoformat()}]"
        first_time = interval
        products = [
            item.product for item in ready.per_product if item.readiness == "READY"
        ]
    else:
        terminal_state = "NOT_READY_WITHIN_OBSERVER_HORIZON"
        interval = None
        first_time = "UNKNOWN_WITHIN_HORIZON"
        products = []
    receipt = NightFuturesPublicationReceipt(
        observation_group_id=group_id,
        target_expected_session=expected,
        market_date=market_date,
        terminal_state=terminal_state,
        first_observed_ready_at=(ready.timestamp_end if ready else None),
        first_observed_products=products,
        raw_refs=(ready.raw_refs if ready else []),
        raw_sha256=(ready.raw_sha256 if ready else None),
        previous_observation_at=(previous.timestamp_end if previous else None),
        previous_observation_state=(
            previous.terminal_classification if previous else None
        ),
        availability_interval=interval,
        first_provider_availability_time=first_time,
    )
    path = _group_directory(directory, market_date, group_id) / "terminal-receipt.json"
    if not path.exists():
        _atomic_json(path, receipt.model_dump(mode="json"))
    return receipt


def record_attempt_best_effort(
    *,
    market_date: date,
    started_at: datetime,
    ended_at: datetime,
    role: str,
    production_or_observer: Literal["production", "observer"],
    expected_session: date | None,
    result: MacroProviderResult | None,
    error: str | None = None,
    market_packet_id: str | None = None,
    directory: Path | None = None,
    horizon_reached: bool = False,
) -> dict[str, object]:
    try:
        record = build_attempt_record(
            market_date=market_date,
            started_at=started_at,
            ended_at=ended_at,
            role=role,
            production_or_observer=production_or_observer,
            expected_session=expected_session,
            result=result,
            error=error,
            market_packet_id=market_packet_id,
        )
        root = directory or default_telemetry_directory()
        path, created = persist_attempt(record, root)
        receipt = maybe_persist_terminal_receipt(
            directory=root,
            market_date=market_date,
            group_id=record.observation_group_id,
            horizon_reached=horizon_reached,
        )
        return {
            "status": "RECORDED" if created else "IDEMPOTENT_REPLAY",
            "attempt_id": record.attempt_id,
            "classification": record.terminal_classification,
            "path": str(path),
            "terminal_state": receipt.terminal_state if receipt else None,
            "production_effect": 0,
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "status": "TELEMETRY_WRITE_FAILED",
            "error": type(exc).__name__,
            "production_effect": 0,
        }
