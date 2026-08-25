from __future__ import annotations

import csv
import hashlib
import io
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from email.utils import parsedate_to_datetime
from typing import Literal

import httpx
from pydantic import BaseModel, Field, model_validator

from app.config import get_settings
from app.services.market_session import us_market_session


CONTRACT_VERSION = "nasdaq-official-exchange-breadth-v1"
SOURCE_SCOPE = "NASDAQ_LISTED_ISSUES"
DAILY_FILE_PATH = "/dynamic/dailyfiles/daily{year}.csv"
REQUIRED_FIELDS = {"Date", "Advances", "Declines", "Unchanged"}


class NasdaqOfficialBreadthObservation(BaseModel):
    contract_version: Literal["nasdaq-official-exchange-breadth-v1"] = (
        CONTRACT_VERSION
    )
    source_scope: Literal["NASDAQ_LISTED_ISSUES"] = SOURCE_SCOPE
    session_date: date
    advances: int
    declines: int
    unchanged: int
    participation_denominator: int
    eligible_issue_count: int | None = None
    net_advances: int
    advance_share: float
    decline_share: float
    advance_decline_ratio: float | None
    source_url: str
    retrieved_at: datetime
    source_last_modified: datetime | None = None
    source_etag: str | None = None
    source_payload_sha256: str
    publication_state: Literal["AVAILABLE_CURRENT"] = "AVAILABLE_CURRENT"

    @model_validator(mode="after")
    def validate_counts(self) -> "NasdaqOfficialBreadthObservation":
        if min(self.advances, self.declines, self.unchanged) < 0:
            raise ValueError("Nasdaq breadth counts cannot be negative")
        if self.participation_denominator != (
            self.advances + self.declines + self.unchanged
        ):
            raise ValueError("Nasdaq breadth counts do not reconcile")
        if self.participation_denominator <= 0:
            raise ValueError("Nasdaq breadth denominator must be positive")
        if self.retrieved_at.tzinfo is None:
            raise ValueError("Nasdaq retrieval time must be timezone-aware")
        return self


class NasdaqOfficialBreadthResult(BaseModel):
    contract_version: Literal["nasdaq-official-exchange-breadth-v1"] = (
        CONTRACT_VERSION
    )
    target_session: date
    latest_available_session: date | None
    latest_completed_session: date
    publication_state: Literal["AVAILABLE_CURRENT", "PUBLICATION_PENDING"]
    observation: NasdaqOfficialBreadthObservation | None = None
    denial_reason: str | None = None
    source_url: str
    retrieved_at: datetime
    source_last_modified: datetime | None = None
    source_etag: str | None = None
    source_payload_sha256: str
    invalid_breadth_sessions: list[date] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_state(self) -> "NasdaqOfficialBreadthResult":
        available = self.publication_state == "AVAILABLE_CURRENT"
        if available != (self.observation is not None):
            raise ValueError("Nasdaq publication state and observation disagree")
        if available and self.denial_reason is not None:
            raise ValueError("available Nasdaq breadth cannot have a denial reason")
        if not available and not self.denial_reason:
            raise ValueError("pending Nasdaq breadth requires a denial reason")
        return self


def _whole_count(value: object, field: str) -> int:
    text = str(value or "").strip()
    try:
        parsed = Decimal(text)
    except InvalidOperation as exc:
        raise ValueError(f"invalid Nasdaq {field}") from exc
    if not parsed.is_finite() or parsed != parsed.to_integral_value() or parsed < 0:
        raise ValueError(f"invalid Nasdaq {field}")
    return int(parsed)


def _source_timestamp(value: str | None) -> datetime | None:
    if not value:
        return None
    parsed = parsedate_to_datetime(value)
    return parsed if parsed.tzinfo is not None else None


def parse_nasdaq_daily_market_file(
    payload: bytes,
    *,
    target_session: date,
    retrieved_at: datetime,
    source_url: str,
    source_last_modified: str | None = None,
    source_etag: str | None = None,
) -> NasdaqOfficialBreadthResult:
    if retrieved_at.tzinfo is None:
        raise ValueError("Nasdaq retrieval time must be timezone-aware")
    try:
        text = payload.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValueError("Nasdaq daily market file is not UTF-8") from exc
    reader = csv.DictReader(io.StringIO(text))
    if reader.fieldnames is None or not REQUIRED_FIELDS.issubset(reader.fieldnames):
        raise ValueError("Nasdaq daily market file fields are incomplete")
    rows: dict[date, tuple[int, int, int]] = {}
    seen_sessions: set[date] = set()
    invalid_sessions: list[date] = []
    for raw in reader:
        raw_date = str(raw.get("Date") or "").strip()
        try:
            session = datetime.strptime(raw_date, "%m/%d/%Y %H:%M:%S").date()
        except ValueError as exc:
            raise ValueError("invalid Nasdaq daily market session date") from exc
        if session in seen_sessions:
            raise ValueError("duplicate Nasdaq daily market session date")
        seen_sessions.add(session)
        try:
            rows[session] = (
                _whole_count(raw.get("Advances"), "advances"),
                _whole_count(raw.get("Declines"), "declines"),
                _whole_count(raw.get("Unchanged"), "unchanged"),
            )
        except ValueError:
            if session == target_session:
                raise
            invalid_sessions.append(session)
    if not rows:
        raise ValueError("Nasdaq daily market file has no rows")
    latest_available = max(rows)
    latest_completed = us_market_session(
        retrieved_at
    ).latest_completed_regular_session_date
    source_sha = hashlib.sha256(payload).hexdigest()
    last_modified = _source_timestamp(source_last_modified)
    common = {
        "target_session": target_session,
        "latest_available_session": latest_available,
        "latest_completed_session": latest_completed,
        "source_url": source_url,
        "retrieved_at": retrieved_at,
        "source_last_modified": last_modified,
        "source_etag": source_etag,
        "source_payload_sha256": source_sha,
        "invalid_breadth_sessions": invalid_sessions,
    }
    if target_session > latest_completed:
        return NasdaqOfficialBreadthResult(
            **common,
            publication_state="PUBLICATION_PENDING",
            denial_reason="target_session_not_completed",
        )
    counts = rows.get(target_session)
    if counts is None:
        return NasdaqOfficialBreadthResult(
            **common,
            publication_state="PUBLICATION_PENDING",
            denial_reason="exact_session_not_published",
        )
    advances, declines, unchanged = counts
    denominator = advances + declines + unchanged
    if denominator <= 0:
        raise ValueError("Nasdaq breadth denominator must be positive")
    observation = NasdaqOfficialBreadthObservation(
        session_date=target_session,
        advances=advances,
        declines=declines,
        unchanged=unchanged,
        participation_denominator=denominator,
        net_advances=advances - declines,
        advance_share=advances / denominator,
        decline_share=declines / denominator,
        advance_decline_ratio=(advances / declines if declines else None),
        source_url=source_url,
        retrieved_at=retrieved_at,
        source_last_modified=last_modified,
        source_etag=source_etag,
        source_payload_sha256=source_sha,
    )
    return NasdaqOfficialBreadthResult(
        **common,
        publication_state="AVAILABLE_CURRENT",
        observation=observation,
    )


class NasdaqTraderBreadthProvider:
    name = "NASDAQ_TRADER_YTD"
    provider_role = "official_primary_supplemental"

    def __init__(
        self,
        *,
        base_url: str | None = None,
        timeout_seconds: float | None = None,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        settings = get_settings()
        self.base_url = (base_url or settings.nasdaq_trader_base_url).rstrip("/")
        self.timeout_seconds = (
            timeout_seconds or settings.nasdaq_trader_timeout_seconds
        )
        self.transport = transport

    async def collect(
        self,
        *,
        session_date: date,
        retrieved_at: datetime,
    ) -> tuple[NasdaqOfficialBreadthResult, bytes]:
        path = DAILY_FILE_PATH.format(year=session_date.year)
        async with httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self.timeout_seconds,
            transport=self.transport,
            follow_redirects=True,
            headers={
                "User-Agent": "thesis-monitor/1.0 official-public-market-statistics"
            },
        ) as client:
            response = await client.get(path)
            response.raise_for_status()
        source_url = str(response.url)
        payload = response.content
        return (
            parse_nasdaq_daily_market_file(
                payload,
                target_session=session_date,
                retrieved_at=retrieved_at,
                source_url=source_url,
                source_last_modified=response.headers.get("last-modified"),
                source_etag=response.headers.get("etag"),
            ),
            payload,
        )
