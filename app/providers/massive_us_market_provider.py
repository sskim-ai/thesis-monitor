from __future__ import annotations

import asyncio
import hashlib
import json
import os
import time
from collections import Counter
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import exchange_calendars as exchange_calendar
import httpx

from app.config import get_settings
from app.services.market_cross_section_service import (
    MarketCrossSection,
    MarketCrossSectionQuality,
    NormalizedMarketRow,
    calculate_market_breadth,
    concentration_from_proxy,
)


GROUPED_PATH = "/v2/aggs/grouped/locale/us/market/stocks/{session_date}"
REFERENCE_PATH = "/v3/reference/tickers"
ELIGIBLE_SECURITY_TYPES = frozenset({"CS", "ADRC", "OS", "NYRS"})
ELIGIBLE_PRIMARY_EXCHANGES = frozenset({"XNAS", "XNYS", "XASE", "ARCX", "BATS"})
UNIVERSE_VERSION = "massive-us-active-common-equities-v1"
REFERENCE_CACHE_MAX_TRADING_AGE = 1
NEW_YORK = ZoneInfo("America/New_York")
XNYS = exchange_calendar.get_calendar("XNYS")


def _canonical_json(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _sha256(value: object) -> str:
    return hashlib.sha256(_canonical_json(value)).hexdigest()


def _atomic_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_bytes(_canonical_json(payload))
    os.replace(temporary, path)


def massive_reference_session_age(cached_date: date, as_of: date) -> int:
    if cached_date > as_of:
        return -1
    try:
        cached_session = XNYS.date_to_session(cached_date, direction="next")
        as_of_session = XNYS.date_to_session(as_of, direction="previous")
        if cached_session > as_of_session:
            return -1
        return len(XNYS.sessions_in_range(cached_session, as_of_session)) - 1
    except (ValueError, IndexError):
        return -1


class MassiveUsMarketProvider:
    name = "massive"
    provider_role = "shadow"

    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str | None = None,
        cache_dir: Path | None = None,
        transport: httpx.AsyncBaseTransport | None = None,
        requests_per_minute: int | None = None,
    ) -> None:
        settings = get_settings()
        self.api_key = api_key if api_key is not None else settings.massive_api_key
        self.base_url = (base_url or settings.massive_base_url).rstrip("/")
        self.cache_dir = cache_dir or Path(settings.massive_cache_dir)
        self.transport = transport
        self.requests_per_minute = requests_per_minute or settings.massive_requests_per_minute
        self._last_request_at = 0.0
        self._request_lock = asyncio.Lock()
        self._last_response_metadata: dict[str, object] = {}

    @property
    def configured(self) -> bool:
        return bool(self.api_key)

    async def _rate_limit(self) -> None:
        if self.transport is not None or self.requests_per_minute <= 0:
            return
        minimum_interval = 60.0 / self.requests_per_minute
        wait = minimum_interval - (time.monotonic() - self._last_request_at)
        if wait > 0:
            await asyncio.sleep(wait)

    async def _get_json(
        self, client: httpx.AsyncClient, path_or_url: str, *, params: dict[str, object] | None = None
    ) -> tuple[dict[str, Any], float]:
        async with self._request_lock:
            last_response: httpx.Response | None = None
            total_latency = 0.0
            for attempt in range(3):
                await self._rate_limit()
                started = time.monotonic()
                response = await client.get(path_or_url, params=params)
                self._last_request_at = time.monotonic()
                total_latency += self._last_request_at - started
                last_response = response
                self._last_response_metadata = {
                    "status_code": response.status_code,
                    "rate_limit_headers": {
                        key.lower(): value
                        for key, value in response.headers.items()
                        if key.lower().startswith("x-ratelimit")
                        or key.lower() == "retry-after"
                    },
                }
                if response.status_code not in {429, 500, 502, 503, 504}:
                    break
                if attempt < 2:
                    retry_after = response.headers.get("Retry-After")
                    if retry_after and retry_after.isdigit():
                        await asyncio.sleep(min(float(retry_after), 60.0))
                    elif self.transport is not None:
                        await asyncio.sleep(0)
            if last_response is None:
                raise RuntimeError("Massive request did not produce a response")
            last_response.raise_for_status()
            payload = last_response.json()
            if not isinstance(payload, dict):
                raise ValueError("Massive response must be an object")
            return payload, total_latency

    def _daily_cache_path(self, session_date: date) -> Path:
        return self.cache_dir / "us_market_daily" / f"{session_date.isoformat()}.json"

    def _reference_cache_path(self, as_of: date) -> Path:
        return self.cache_dir / "reference" / f"us_active_{as_of.isoformat()}.json"

    @staticmethod
    def _validate_grouped_envelope(
        envelope: dict[str, Any], session_date: date
    ) -> dict[str, Any]:
        if envelope.get("request_date") != session_date.isoformat():
            raise ValueError("Massive grouped cache request date mismatch")
        payload = envelope.get("payload")
        if not isinstance(payload, dict):
            raise ValueError("Massive grouped payload must be an object")
        results = payload.get("results")
        if payload.get("status") != "OK" or payload.get("adjusted") is not True:
            raise ValueError("Massive grouped response is not an adjusted successful result")
        if not isinstance(results, list) or not results:
            raise ValueError("Massive grouped response has no market rows")
        tickers = [str(item.get("T")) for item in results if isinstance(item, dict)]
        if not tickers or len(tickers) != len(set(tickers)):
            raise ValueError("Massive grouped response contains missing or duplicate tickers")
        observed_dates = {
            datetime.fromtimestamp(float(item["t"]) / 1000, tz=timezone.utc)
            .astimezone(NEW_YORK)
            .date()
            for item in results
            if isinstance(item, dict) and isinstance(item.get("t"), (int, float))
        }
        if observed_dates and observed_dates != {session_date}:
            raise ValueError("Massive grouped rows do not match the requested session date")
        return envelope

    @staticmethod
    def _validate_reference_envelope(
        envelope: dict[str, Any], as_of: date, *, max_trading_age: int = 0
    ) -> dict[str, Any]:
        try:
            request_date = date.fromisoformat(str(envelope.get("request_date") or ""))
        except ValueError as error:
            raise ValueError("Massive reference cache request date is invalid") from error
        age = massive_reference_session_age(request_date, as_of)
        if age < 0 or age > max_trading_age:
            raise ValueError("Massive reference cache request date mismatch")
        rows = envelope.get("rows")
        if not isinstance(rows, list) or not rows:
            raise ValueError("Massive reference cache has no rows")
        tickers = [
            str(item.get("ticker"))
            for item in rows
            if isinstance(item, dict) and item.get("ticker")
        ]
        if len(tickers) != len(rows) or len(tickers) != len(set(tickers)):
            raise ValueError("Massive reference cache contains missing or duplicate tickers")
        return envelope

    def _reusable_reference_cache(self, as_of: date) -> Path | None:
        directory = self.cache_dir / "reference"
        if not directory.exists():
            return None
        candidates: list[tuple[date, Path]] = []
        for path in directory.glob("us_active_*.json"):
            try:
                value = date.fromisoformat(path.stem.removeprefix("us_active_"))
            except ValueError:
                continue
            age = massive_reference_session_age(value, as_of)
            if 0 <= age <= REFERENCE_CACHE_MAX_TRADING_AGE:
                candidates.append((value, path))
        return max(candidates, default=(date.min, None), key=lambda item: item[0])[1]

    async def grouped_daily(self, session_date: date, *, refresh: bool = False) -> dict[str, Any]:
        cache_path = self._daily_cache_path(session_date)
        if cache_path.exists() and not refresh:
            cached = json.loads(cache_path.read_text(encoding="utf-8"))
            if not isinstance(cached, dict):
                raise ValueError("Massive grouped cache must be an object")
            return self._validate_grouped_envelope(cached, session_date)
        if not self.api_key:
            raise RuntimeError("MASSIVE_API_KEY is not configured")
        headers = {"Authorization": f"Bearer {self.api_key}"}
        async with httpx.AsyncClient(
            base_url=self.base_url,
            headers=headers,
            timeout=60.0,
            transport=self.transport,
        ) as client:
            payload, latency = await self._get_json(
                client,
                GROUPED_PATH.format(session_date=session_date.isoformat()),
                params={"adjusted": "true", "include_otc": "false"},
            )
        envelope = {
            "provider": self.name,
            "request_date": session_date.isoformat(),
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "latency_seconds": latency,
            "http_metadata": self._last_response_metadata,
            "response_sha256": _sha256(payload),
            "payload": payload,
        }
        self._validate_grouped_envelope(envelope, session_date)
        _atomic_json(cache_path, envelope)
        return envelope

    async def reference_tickers(self, as_of: date, *, refresh: bool = False) -> dict[str, Any]:
        cache_path = self._reference_cache_path(as_of)
        reusable = cache_path if cache_path.exists() else self._reusable_reference_cache(as_of)
        if reusable is not None and not refresh:
            cached = json.loads(reusable.read_text(encoding="utf-8"))
            if not isinstance(cached, dict):
                raise ValueError("Massive reference cache must be an object")
            validated = self._validate_reference_envelope(
                cached,
                as_of,
                max_trading_age=REFERENCE_CACHE_MAX_TRADING_AGE,
            )
            return {
                **validated,
                "cache_reused_for": as_of.isoformat(),
                "cache_age_calendar_days": (
                    as_of - date.fromisoformat(str(validated["request_date"]))
                ).days,
                "cache_age_trading_days": massive_reference_session_age(
                    date.fromisoformat(str(validated["request_date"])),
                    as_of,
                ),
            }
        if not self.api_key:
            raise RuntimeError("MASSIVE_API_KEY is not configured")
        headers = {"Authorization": f"Bearer {self.api_key}"}
        rows: list[dict[str, Any]] = []
        latencies: list[float] = []
        page_http_metadata: list[dict[str, object]] = []
        next_url: str | None = REFERENCE_PATH
        params: dict[str, object] | None = {
            "market": "stocks",
            "locale": "us",
            "active": "true",
            "date": as_of.isoformat(),
            "limit": 1000,
            "sort": "ticker",
            "order": "asc",
        }
        async with httpx.AsyncClient(
            base_url=self.base_url,
            headers=headers,
            timeout=60.0,
            transport=self.transport,
        ) as client:
            while next_url:
                payload, latency = await self._get_json(client, next_url, params=params)
                latencies.append(latency)
                page_http_metadata.append(dict(self._last_response_metadata))
                results = payload.get("results")
                if not isinstance(results, list):
                    raise ValueError("Massive reference results must be a list")
                rows.extend(item for item in results if isinstance(item, dict))
                value = payload.get("next_url")
                next_url = str(value) if value else None
                params = None
        rows.sort(key=lambda item: str(item.get("ticker") or ""))
        envelope = {
            "provider": self.name,
            "request_date": as_of.isoformat(),
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "page_count": len(latencies),
            "latency_seconds": sum(latencies),
            "http_metadata": self._last_response_metadata,
            "page_http_metadata": page_http_metadata,
            "response_sha256": _sha256(rows),
            "rows": rows,
        }
        self._validate_reference_envelope(envelope, as_of)
        _atomic_json(cache_path, envelope)
        return envelope

    @staticmethod
    def _rows(envelope: dict[str, Any]) -> list[dict[str, Any]]:
        payload = envelope.get("payload")
        results = payload.get("results") if isinstance(payload, dict) else None
        if not isinstance(results, list):
            raise ValueError("Massive grouped results must be a list")
        return [item for item in results if isinstance(item, dict)]

    @staticmethod
    def _eligible_reference(item: dict[str, Any]) -> tuple[bool, list[str]]:
        reasons: list[str] = []
        if item.get("active") is not True:
            reasons.append("inactive")
        if str(item.get("market") or "").lower() != "stocks":
            reasons.append("non_stock_market")
        if str(item.get("locale") or "").lower() != "us":
            reasons.append("non_us_locale")
        if str(item.get("currency_name") or "").lower() not in {"usd", "us dollar"}:
            reasons.append("non_usd_currency")
        if str(item.get("type") or "") not in ELIGIBLE_SECURITY_TYPES:
            reasons.append("ineligible_security_type")
        if str(item.get("primary_exchange") or "") not in ELIGIBLE_PRIMARY_EXCHANGES:
            reasons.append("ineligible_primary_exchange")
        if "test issue" in str(item.get("name") or "").lower():
            reasons.append("test_issue")
        return not reasons, reasons

    def normalize(
        self,
        *,
        session_date: date,
        current: dict[str, Any],
        previous: dict[str, Any],
        reference: dict[str, Any],
    ) -> tuple[list[NormalizedMarketRow], Counter[str]]:
        current_by_ticker = {str(item.get("T")): item for item in self._rows(current) if item.get("T")}
        previous_by_ticker = {str(item.get("T")): item for item in self._rows(previous) if item.get("T")}
        reference_by_ticker = {
            str(item.get("ticker")): item
            for item in reference.get("rows", [])
            if isinstance(item, dict) and item.get("ticker")
        }
        normalized: list[NormalizedMarketRow] = []
        exclusions: Counter[str] = Counter()
        for ticker in sorted(current_by_ticker):
            raw = current_by_ticker[ticker]
            metadata = reference_by_ticker.get(ticker)
            reasons: list[str] = []
            if metadata is None:
                reasons.append("reference_missing")
            else:
                _eligible, reference_reasons = self._eligible_reference(metadata)
                reasons.extend(reference_reasons)
            previous_raw = previous_by_ticker.get(ticker)
            previous_close = previous_raw.get("c") if previous_raw else None
            if not isinstance(previous_close, (int, float)) or previous_close <= 0:
                reasons.append("previous_adjusted_close_missing")
                previous_close = None
            close = raw.get("c")
            if not isinstance(close, (int, float)) or close <= 0:
                exclusions["invalid_close"] += 1
                continue
            for reason in set(reasons):
                exclusions[reason] += 1
            normalized.append(
                NormalizedMarketRow(
                    ticker=ticker,
                    session_date=session_date,
                    close=float(close),
                    previous_close=float(previous_close) if previous_close is not None else None,
                    volume=float(raw["v"]) if isinstance(raw.get("v"), (int, float)) else None,
                    vwap=float(raw["vw"]) if isinstance(raw.get("vw"), (int, float)) else None,
                    security_type=str(metadata.get("type")) if metadata else None,
                    primary_exchange=str(metadata.get("primary_exchange")) if metadata else None,
                    currency=str(metadata.get("currency_name")) if metadata else None,
                    eligible=not reasons,
                    exclusion_reasons=sorted(set(reasons)),
                )
            )
        return normalized, exclusions

    async def collect(
        self,
        *,
        session_date: date,
        previous_session_date: date,
        refresh: bool = False,
        proxy_symbol: str = "SPY",
    ) -> MarketCrossSection:
        current = await self.grouped_daily(session_date, refresh=refresh)
        previous = await self.grouped_daily(previous_session_date, refresh=refresh)
        reference = await self.reference_tickers(session_date, refresh=refresh)
        rows, exclusions = self.normalize(
            session_date=session_date,
            current=current,
            previous=previous,
            reference=reference,
        )
        breadth = calculate_market_breadth(rows)
        proxy = next((row for row in rows if row.ticker == proxy_symbol), None)
        concentration: dict[str, object] = {}
        if proxy and proxy.return_pct is not None and breadth.equal_weight_return_pct is not None:
            concentration = concentration_from_proxy(
                proxy_symbol=proxy_symbol,
                proxy_return_pct=proxy.return_pct,
                equal_weight_return_pct=breadth.equal_weight_return_pct,
            )
        raw_count = len(self._rows(current))
        source_hash = _sha256(
            {
                "current": current.get("response_sha256"),
                "previous": previous.get("response_sha256"),
                "reference": reference.get("response_sha256"),
            }
        )
        return MarketCrossSection(
            market="US",
            session_date=session_date,
            as_of=datetime.now(timezone.utc),
            breadth=breadth,
            concentration=concentration,
            quality=MarketCrossSectionQuality(
                provider=self.name,
                provider_role=self.provider_role,
                coverage="full",
                freshness="fresh",
                universe_version=UNIVERSE_VERSION,
                raw_count=raw_count,
                eligible_count=breadth.eligible_count,
                excluded_count=raw_count - breadth.eligible_count,
                exclusion_reason_counts=dict(sorted(exclusions.items())),
                warnings=[
                    "Massive adjusted aggregates include split-adjusted volume; total volume and close-times-volume are audit-only."
                ],
                volume_semantics="split_adjusted_aggregate_volume",
                trading_value_semantics=(
                    "deterministic_close_times_adjusted_volume_estimate"
                ),
            ),
            source_payload_sha256=source_hash,
        )
