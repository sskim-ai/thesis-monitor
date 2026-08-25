from __future__ import annotations

import hashlib
import json
import time
from datetime import date, datetime, timezone
from typing import Literal
from urllib.parse import urlsplit

import httpx
from pydantic import BaseModel, Field, model_validator

from app.config import get_settings
from app.services.market_cross_section_service import (
    MarketCrossSection,
    MarketCrossSectionQuality,
    MarketIndexFact,
    MarketScopedBreadth,
    NormalizedMarketRow,
    calculate_market_breadth,
)


KOSPI_DAILY_PATH = "sto/stk_bydd_trd"
KOSDAQ_DAILY_PATH = "sto/ksq_bydd_trd"
KOSPI_INDEX_PATH = "idx/kospi_dd_trd"
KOSDAQ_INDEX_PATH = "idx/kosdaq_dd_trd"

CORE_READINESS_ENDPOINTS = (
    KOSPI_DAILY_PATH,
    KOSDAQ_DAILY_PATH,
    KOSPI_INDEX_PATH,
    KOSDAQ_INDEX_PATH,
)
REQUIRED_INDEX_IDENTITIES = {
    KOSPI_INDEX_PATH: {("KOSPI", "코스피"), ("KOSPI", "코스피 200")},
    KOSDAQ_INDEX_PATH: {("KOSDAQ", "코스닥"), ("KOSDAQ", "코스닥 150")},
}

PublicationReadinessStatus = Literal[
    "MARKET_NOT_COMPLETED",
    "MARKET_COMPLETED_PROVIDER_PENDING",
    "PROVIDER_PARTIAL",
    "PROVIDER_COMPLETE",
    "PROVIDER_ERROR",
    "STALE_PROVIDER_DATE",
]
EndpointReadinessStatus = Literal["EMPTY", "PARTIAL", "READY", "ERROR", "STALE"]


class KrxEndpointReadiness(BaseModel):
    endpoint: str
    status: EndpointReadinessStatus
    http_status: int | None = None
    row_count: int = 0
    provider_dates: list[date] = Field(default_factory=list)
    latency_seconds: float | None = None
    payload_sha256: str | None = None
    missing_required_identities: list[str] = Field(default_factory=list)
    error_code: str | None = None


class KrxPublicationReadiness(BaseModel):
    contract_version: Literal["krx-publication-readiness-v1"] = (
        "krx-publication-readiness-v1"
    )
    status: PublicationReadinessStatus
    target_session: date
    latest_completed_session: date
    observed_at: datetime
    endpoints: list[KrxEndpointReadiness] = Field(default_factory=list)
    first_non_empty_at: datetime | None = None
    first_complete_at: datetime | None = None
    observed_complete_by: datetime | None = None
    last_empty_at: datetime | None = None
    provider_publication_timestamp: datetime | None = None
    current_snapshot_promotable: bool = False
    reason_codes: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_promotion_boundary(self) -> "KrxPublicationReadiness":
        if self.observed_at.tzinfo is None:
            raise ValueError("publication observation must be timezone-aware")
        if self.current_snapshot_promotable != (self.status == "PROVIDER_COMPLETE"):
            raise ValueError("only a complete provider snapshot can be promotable")
        if self.status == "PROVIDER_COMPLETE" and self.observed_complete_by is None:
            raise ValueError("complete readiness requires observed-complete telemetry")
        if self.status == "PROVIDER_COMPLETE" and (
            {item.endpoint for item in self.endpoints} != set(CORE_READINESS_ENDPOINTS)
            or any(item.status != "READY" for item in self.endpoints)
        ):
            raise ValueError("complete readiness requires all core endpoints")
        return self


def validate_krx_base_url(value: str) -> str:
    parsed = urlsplit(value)
    if parsed.scheme != "https" or not parsed.hostname:
        raise ValueError("KRX base URL must be an absolute HTTPS URL")
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ValueError("KRX base URL cannot contain credentials or query parameters")
    return value.rstrip("/")


def _payload_sha256(payload: object) -> str:
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _provider_date(value: object) -> date | None:
    try:
        return datetime.strptime(str(value or "").strip(), "%Y%m%d").date()
    except ValueError:
        return None


def _number(value: object) -> float | None:
    try:
        return float(str(value).replace(",", "").strip())
    except (TypeError, ValueError):
        return None


def _normalized_stock_rows(
    rows: list[dict[str, object]],
    *,
    session_date: date,
    market_scope: str,
) -> list[NormalizedMarketRow]:
    values: list[NormalizedMarketRow] = []
    for raw in rows:
        ticker = str(raw.get("ISU_CD") or "").strip()
        close = _number(raw.get("TDD_CLSPRC"))
        change = _number(raw.get("CMPPREVDD_PRC"))
        volume = _number(raw.get("ACC_TRDVOL"))
        reasons: list[str] = []
        if not ticker:
            reasons.append("identity_missing")
        if close is None or close <= 0:
            continue
        previous_close = close - change if change is not None else None
        if previous_close is None or previous_close <= 0:
            reasons.append("previous_close_missing")
            previous_close = None
        values.append(
            NormalizedMarketRow(
                ticker=ticker,
                session_date=session_date,
                close=close,
                previous_close=previous_close,
                volume=volume,
                security_type=str(raw.get("SECT_TP_NM") or "") or None,
                primary_exchange=market_scope,
                currency="KRW",
                eligible=not reasons,
                exclusion_reasons=reasons,
            )
        )
    return values


def _official_activity(breadth: object, raw_rows: list[dict[str, object]]) -> object:
    if not hasattr(breadth, "model_copy"):
        return breadth
    trading_values = [_number(row.get("ACC_TRDVAL")) for row in raw_rows]
    volumes = [_number(row.get("ACC_TRDVOL")) for row in raw_rows]
    return breadth.model_copy(
        update={
            "total_trading_value": (
                sum(value for value in trading_values if value is not None)
                if any(value is not None for value in trading_values)
                else None
            ),
            "total_trading_volume": (
                sum(value for value in volumes if value is not None)
                if any(value is not None for value in volumes)
                else None
            ),
        }
    )


def _index_fact(
    rows: list[dict[str, object]],
    *,
    market: str,
    name: str,
) -> MarketIndexFact:
    row = next(
        (
            item
            for item in rows
            if str(item.get("IDX_CLSS") or "").strip() == market
            and str(item.get("IDX_NM") or "").strip() == name
        ),
        None,
    )
    if row is None:
        raise ValueError(f"required KRX index identity missing: {market}:{name}")
    close = _number(row.get("CLSPRC_IDX"))
    if close is None or close <= 0:
        raise ValueError(f"required KRX index close invalid: {market}:{name}")
    return MarketIndexFact(
        symbol=market,
        label=name,
        close=close,
        return_pct=_number(row.get("FLUC_RT")),
        volume=_number(row.get("ACC_TRDVOL")),
        trading_value=_number(row.get("ACC_TRDVAL")),
    )


def _row_identity(endpoint: str, row: dict[str, object]) -> tuple[str, ...]:
    if endpoint in {KOSPI_DAILY_PATH, KOSDAQ_DAILY_PATH}:
        return (str(row.get("ISU_CD") or "").strip(),)
    return (
        str(row.get("IDX_CLSS") or "").strip(),
        str(row.get("IDX_NM") or "").strip(),
    )


class KrxPublicationProvider:
    name = "krx_publication_readiness"

    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str | None = None,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        settings = get_settings()
        self.api_key = api_key if api_key is not None else settings.krx_open_api_key
        self.base_url = validate_krx_base_url(
            base_url or settings.krx_open_api_base_url
        )
        self.transport = transport

    @property
    def configured(self) -> bool:
        return bool(self.api_key)

    async def _fetch_endpoint(
        self,
        client: httpx.AsyncClient,
        endpoint: str,
        target_session: date,
    ) -> tuple[int, list[dict[str, object]], float, str]:
        started = time.monotonic()
        response = await client.get(
            endpoint,
            params={"basDd": target_session.strftime("%Y%m%d")},
        )
        latency = time.monotonic() - started
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict):
            raise ValueError("KRX response must be an object")
        raw_rows = payload.get("OutBlock_1")
        if not isinstance(raw_rows, list) or any(
            not isinstance(row, dict) for row in raw_rows
        ):
            raise ValueError("KRX response must contain object rows in OutBlock_1")
        rows = [row for row in raw_rows if isinstance(row, dict)]
        return response.status_code, rows, latency, _payload_sha256(payload)

    async def collect_market_cross_section(
        self,
        *,
        target_session: date,
        observed_at: datetime | None = None,
    ) -> MarketCrossSection:
        current = observed_at or datetime.now(timezone.utc)
        if current.tzinfo is None:
            raise ValueError("observed_at must be timezone-aware")
        if not self.api_key:
            raise RuntimeError("KRX Open API key is not configured")

        endpoint_rows: dict[str, list[dict[str, object]]] = {}
        endpoint_hashes: dict[str, str] = {}
        async with httpx.AsyncClient(
            base_url=self.base_url,
            headers={"AUTH_KEY": self.api_key},
            timeout=30.0,
            transport=self.transport,
        ) as client:
            for endpoint in CORE_READINESS_ENDPOINTS:
                _status, rows, _latency, payload_sha256 = await self._fetch_endpoint(
                    client,
                    endpoint,
                    target_session,
                )
                readiness, _dates, _missing, error_code = self._row_validation(
                    endpoint,
                    rows,
                    target_session,
                )
                if readiness != "READY":
                    raise RuntimeError(
                        "KRX structured market endpoint is not ready: "
                        f"{endpoint}:{readiness}:{error_code or 'incomplete'}"
                    )
                endpoint_rows[endpoint] = rows
                endpoint_hashes[endpoint] = payload_sha256

        kospi_raw = endpoint_rows[KOSPI_DAILY_PATH]
        kosdaq_raw = endpoint_rows[KOSDAQ_DAILY_PATH]
        kospi_rows = _normalized_stock_rows(
            kospi_raw,
            session_date=target_session,
            market_scope="KOSPI",
        )
        kosdaq_rows = _normalized_stock_rows(
            kosdaq_raw,
            session_date=target_session,
            market_scope="KOSDAQ",
        )
        kospi_breadth = _official_activity(
            calculate_market_breadth(kospi_rows),
            kospi_raw,
        )
        kosdaq_breadth = _official_activity(
            calculate_market_breadth(kosdaq_rows),
            kosdaq_raw,
        )
        all_rows = [*kospi_rows, *kosdaq_rows]
        all_raw = [*kospi_raw, *kosdaq_raw]
        breadth = _official_activity(calculate_market_breadth(all_rows), all_raw)
        eligible_count = sum(row.eligible for row in all_rows)
        exclusions: dict[str, int] = {}
        for row in all_rows:
            for reason in row.exclusion_reasons:
                exclusions[reason] = exclusions.get(reason, 0) + 1

        return MarketCrossSection(
            market="KR",
            session_date=target_session,
            as_of=current,
            indices=[
                _index_fact(
                    endpoint_rows[KOSPI_INDEX_PATH],
                    market="KOSPI",
                    name="코스피",
                ),
                _index_fact(
                    endpoint_rows[KOSDAQ_INDEX_PATH],
                    market="KOSDAQ",
                    name="코스닥",
                ),
            ],
            breadth=breadth,
            breadth_by_scope=[
                MarketScopedBreadth(scope="KOSPI", breadth=kospi_breadth),
                MarketScopedBreadth(scope="KOSDAQ", breadth=kosdaq_breadth),
            ],
            quality=MarketCrossSectionQuality(
                provider="KRX_OPEN_API",
                provider_role="official_primary",
                coverage="full",
                freshness="fresh",
                universe_version="krx-stock-daily-trading-rows-v1",
                raw_count=len(all_rows),
                eligible_count=eligible_count,
                excluded_count=len(all_rows) - eligible_count,
                exclusion_reason_counts=dict(sorted(exclusions.items())),
                volume_semantics="raw_reported_shares",
                trading_value_semantics="official_reported",
            ),
            source_payload_sha256=_payload_sha256(endpoint_hashes),
        )

    @staticmethod
    def _row_validation(
        endpoint: str,
        rows: list[dict[str, object]],
        target_session: date,
    ) -> tuple[EndpointReadinessStatus, list[date], list[str], str | None]:
        raw_dates = [str(row.get("BAS_DD") or "").strip() for row in rows]
        if any(not value for value in raw_dates):
            return "ERROR", [], [], "provider_date_missing"
        parsed_dates = [_provider_date(value) for value in raw_dates]
        if any(value is None for value in parsed_dates):
            return "ERROR", [], [], "provider_date_invalid"
        provider_dates = sorted({value for value in parsed_dates if value is not None})
        if provider_dates != [target_session]:
            return "STALE", provider_dates, [], "provider_date_mismatch"

        identities = [_row_identity(endpoint, row) for row in rows]
        if any(not all(identity) for identity in identities):
            return "ERROR", provider_dates, [], "identity_missing"
        if endpoint in {KOSPI_DAILY_PATH, KOSDAQ_DAILY_PATH} and any(
            len(identity[0]) != 6 for identity in identities
        ):
            return "ERROR", provider_dates, [], "short_code_invalid"
        if len(identities) != len(set(identities)):
            return "ERROR", provider_dates, [], "duplicate_identity"

        required = REQUIRED_INDEX_IDENTITIES.get(endpoint, set())
        missing = sorted(
            f"{market}:{name}" for market, name in required - set(identities)
        )
        if missing:
            return "PARTIAL", provider_dates, missing, "required_index_identity_missing"
        return "READY", provider_dates, [], None

    async def probe_publication_readiness(
        self,
        *,
        target_session: date,
        latest_completed_session: date,
        observed_at: datetime | None = None,
    ) -> KrxPublicationReadiness:
        current = observed_at or datetime.now(timezone.utc)
        if current.tzinfo is None:
            raise ValueError("observed_at must be timezone-aware")
        if target_session > latest_completed_session:
            return KrxPublicationReadiness(
                status="MARKET_NOT_COMPLETED",
                target_session=target_session,
                latest_completed_session=latest_completed_session,
                observed_at=current,
                reason_codes=["target_session_not_completed"],
            )

        endpoint_results: list[KrxEndpointReadiness] = []
        if not self.api_key:
            return KrxPublicationReadiness(
                status="PROVIDER_ERROR",
                target_session=target_session,
                latest_completed_session=latest_completed_session,
                observed_at=current,
                reason_codes=["provider_not_configured"],
            )

        async with httpx.AsyncClient(
            base_url=self.base_url,
            headers={"AUTH_KEY": self.api_key},
            timeout=30.0,
            transport=self.transport,
        ) as client:
            for endpoint in CORE_READINESS_ENDPOINTS:
                try:
                    http_status, rows, latency, payload_sha256 = (
                        await self._fetch_endpoint(client, endpoint, target_session)
                    )
                except httpx.HTTPStatusError as exc:
                    endpoint_results.append(
                        KrxEndpointReadiness(
                            endpoint=endpoint,
                            status="ERROR",
                            http_status=exc.response.status_code,
                            error_code="http_error",
                        )
                    )
                    continue
                except httpx.RequestError:
                    endpoint_results.append(
                        KrxEndpointReadiness(
                            endpoint=endpoint,
                            status="ERROR",
                            error_code="network_error",
                        )
                    )
                    continue
                except (TypeError, ValueError):
                    endpoint_results.append(
                        KrxEndpointReadiness(
                            endpoint=endpoint,
                            status="ERROR",
                            error_code="schema_error",
                        )
                    )
                    continue

                common = {
                    "endpoint": endpoint,
                    "http_status": http_status,
                    "row_count": len(rows),
                    "latency_seconds": latency,
                    "payload_sha256": payload_sha256,
                }
                if not rows:
                    endpoint_results.append(
                        KrxEndpointReadiness(status="EMPTY", **common)
                    )
                    continue
                status, dates, missing, error_code = self._row_validation(
                    endpoint, rows, target_session
                )
                endpoint_results.append(
                    KrxEndpointReadiness(
                        status=status,
                        provider_dates=dates,
                        missing_required_identities=missing,
                        error_code=error_code,
                        **common,
                    )
                )

        states = {item.status for item in endpoint_results}
        if "ERROR" in states:
            status: PublicationReadinessStatus = "PROVIDER_ERROR"
            reason_codes = ["one_or_more_core_endpoints_failed"]
        elif "STALE" in states:
            status = "STALE_PROVIDER_DATE"
            reason_codes = ["provider_date_does_not_match_target_session"]
        elif states == {"EMPTY"}:
            status = "MARKET_COMPLETED_PROVIDER_PENDING"
            reason_codes = ["all_core_endpoints_returned_empty_200"]
        elif states == {"READY"}:
            status = "PROVIDER_COMPLETE"
            reason_codes = []
        else:
            status = "PROVIDER_PARTIAL"
            reason_codes = ["core_endpoint_bundle_not_complete"]

        complete = status == "PROVIDER_COMPLETE"
        pending = status == "MARKET_COMPLETED_PROVIDER_PENDING"
        return KrxPublicationReadiness(
            status=status,
            target_session=target_session,
            latest_completed_session=latest_completed_session,
            observed_at=current,
            endpoints=endpoint_results,
            observed_complete_by=current if complete else None,
            last_empty_at=current if pending else None,
            current_snapshot_promotable=complete,
            reason_codes=reason_codes,
        )
