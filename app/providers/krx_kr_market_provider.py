from __future__ import annotations

import asyncio
import hashlib
import json
import math
import os
import time
from collections import Counter
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Literal
from urllib.parse import urlsplit

import httpx
from pydantic import BaseModel, Field, model_validator

from app.config import get_settings
from app.services.market_cross_section_service import (
    MarketCrossSection,
    MarketCrossSectionQuality,
    MarketIndexFact,
    MarketSectorFact,
    NormalizedMarketRow,
    calculate_market_breadth,
)


KOSPI_DAILY_PATH = "sto/stk_bydd_trd"
KOSDAQ_DAILY_PATH = "sto/ksq_bydd_trd"
KOSPI_REFERENCE_PATH = "sto/stk_isu_base_info"
KOSDAQ_REFERENCE_PATH = "sto/ksq_isu_base_info"
KOSPI_INDEX_PATH = "idx/kospi_dd_trd"
KOSDAQ_INDEX_PATH = "idx/kosdaq_dd_trd"

UNIVERSE_VERSION = "krx-kospi-kosdaq-common-share-v1"
OFFICIAL_DAILY_REQUEST_LIMIT = 10_000
CapabilityStatus = Literal["SUPPORTED", "PARTIAL", "UNSUPPORTED"]
PublicationReadinessStatus = Literal[
    "MARKET_NOT_COMPLETED",
    "MARKET_COMPLETED_PROVIDER_PENDING",
    "PROVIDER_PARTIAL",
    "PROVIDER_COMPLETE",
    "PROVIDER_ERROR",
    "STALE_PROVIDER_DATE",
]
EndpointReadinessStatus = Literal["EMPTY", "PARTIAL", "READY", "ERROR", "STALE"]

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

MAJOR_INDEX_IDENTITIES = {
    ("KOSPI", "코스피"): ("KOSPI", "KOSPI"),
    ("KOSPI", "코스피 200"): ("KOSPI200", "KOSPI 200"),
    ("KOSDAQ", "코스닥"): ("KOSDAQ", "KOSDAQ"),
    ("KOSDAQ", "코스닥 150"): ("KOSDAQ150", "KOSDAQ 150"),
}

SECTOR_INDEX_IDENTITIES = {
    "코스피 200 커뮤니케이션서비스",
    "코스피 200 건설",
    "코스피 200 중공업",
    "코스피 200 철강/소재",
    "코스피 200 에너지/화학",
    "코스피 200 정보기술",
    "코스피 200 금융",
    "코스피 200 생활소비재",
    "코스피 200 경기소비재",
    "코스피 200 산업재",
    "코스피 200 헬스케어",
    "코스닥 150 정보기술",
    "코스닥 150 헬스케어",
    "코스닥 150 커뮤니케이션서비스",
    "코스닥 150 소재",
    "코스닥 150 산업재",
    "코스닥 150 필수소비재",
    "코스닥 150 자유소비재",
}


class KrxCapability(BaseModel):
    metric: str
    status: CapabilityStatus
    evidence: str
    notes: list[str] = Field(default_factory=list)


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
            raise ValueError("only a complete provider snapshot can be promoted")
        if self.status == "PROVIDER_COMPLETE" and self.observed_complete_by is None:
            raise ValueError("complete readiness requires observed-complete telemetry")
        if self.status == "PROVIDER_COMPLETE" and (
            {item.endpoint for item in self.endpoints} != set(CORE_READINESS_ENDPOINTS)
            or any(item.status != "READY" for item in self.endpoints)
        ):
            raise ValueError("complete readiness requires all core endpoints")
        return self


def krx_capability_matrix() -> list[KrxCapability]:
    return [
        KrxCapability(
            metric="major_indices",
            status="SUPPORTED",
            evidence="KOSPI and KOSDAQ series daily index APIs",
            notes=["KOSPI, KOSPI 200, KOSDAQ, and KOSDAQ 150 are explicit identities."],
        ),
        KrxCapability(
            metric="listed_security_universe",
            status="SUPPORTED",
            evidence="KOSPI and KOSDAQ issue basic-information APIs",
            notes=["Six-character short code and security/certificate classifications are present."],
        ),
        KrxCapability(
            metric="daily_close_return_volume_value",
            status="SUPPORTED",
            evidence="KOSPI and KOSDAQ daily trading APIs",
            notes=["Return uses the official comparison base and official KRX return."],
        ),
        KrxCapability(
            metric="common_share_breadth",
            status="PARTIAL",
            evidence="Deterministic calculation from official issue and daily-trading rows",
            notes=["The Open API response does not expose an explicit suspension flag."],
        ),
        KrxCapability(
            metric="market_wide_investor_flow",
            status="UNSUPPORTED",
            evidence="No market-wide investor-flow service in the approved Open API catalog",
        ),
        KrxCapability(
            metric="sector_participation",
            status="PARTIAL",
            evidence="KOSPI 200 and KOSDAQ 150 sector index returns",
            notes=["Sector price proxies are available; security-level sector breadth is not."],
        ),
        KrxCapability(
            metric="security_type_policy",
            status="PARTIAL",
            evidence="Security group, certificate type, listing date, and KOSDAQ segment metadata",
            notes=["Suspension status remains unavailable."],
        ),
    ]


def validate_krx_base_url(value: str) -> str:
    parsed = urlsplit(value)
    if parsed.scheme != "https" or not parsed.hostname:
        raise ValueError("KRX base URL must be an absolute HTTPS URL")
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ValueError("KRX base URL cannot contain credentials or query parameters")
    return value.rstrip("/")


def _canonical_json(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _sha256(value: object) -> str:
    return hashlib.sha256(_canonical_json(value)).hexdigest()


def _atomic_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_bytes(_canonical_json(payload))
    os.replace(temporary, path)


def _number(value: object) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        result = float(value)
    elif isinstance(value, str):
        cleaned = value.strip().replace(",", "")
        if cleaned in {"", "-"}:
            return None
        try:
            result = float(cleaned)
        except ValueError:
            return None
    else:
        return None
    return result if math.isfinite(result) else None


def _krx_date(value: object) -> date | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return datetime.strptime(text, "%Y%m%d").date()
    except ValueError:
        return None


def _identity_field(endpoint: str) -> tuple[str, ...]:
    if endpoint in {KOSPI_DAILY_PATH, KOSDAQ_DAILY_PATH}:
        return ("ISU_CD",)
    if endpoint in {KOSPI_REFERENCE_PATH, KOSDAQ_REFERENCE_PATH}:
        return ("ISU_SRT_CD",)
    return ("IDX_CLSS", "IDX_NM")


class KrxKrMarketProvider:
    name = "krx"
    provider_role = "primary"

    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str | None = None,
        cache_dir: Path | None = None,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        settings = get_settings()
        self.api_key = api_key if api_key is not None else settings.krx_open_api_key
        self.base_url = validate_krx_base_url(
            base_url or settings.krx_open_api_base_url
        )
        self.cache_dir = cache_dir or Path(settings.krx_cache_dir)
        self.transport = transport
        self._request_lock = asyncio.Lock()
        self._last_response_metadata: dict[str, object] = {}

    @property
    def configured(self) -> bool:
        return bool(self.api_key)

    def _cache_path(self, endpoint: str, session_date: date) -> Path:
        name = endpoint.replace("/", "_")
        return self.cache_dir / "market" / session_date.isoformat() / f"{name}.json"

    @staticmethod
    def _validate_envelope(
        envelope: dict[str, Any], *, endpoint: str, session_date: date
    ) -> dict[str, Any]:
        if envelope.get("endpoint") != endpoint:
            raise ValueError("KRX cache endpoint mismatch")
        if envelope.get("request_date") != session_date.isoformat():
            raise ValueError("KRX cache request date mismatch")
        rows = envelope.get("rows")
        if not isinstance(rows, list) or not rows:
            raise ValueError("KRX response has no rows for the requested session")
        expected_date = session_date.strftime("%Y%m%d")
        observed_dates = {
            str(row.get("BAS_DD"))
            for row in rows
            if isinstance(row, dict) and row.get("BAS_DD")
        }
        if observed_dates and observed_dates != {expected_date}:
            raise ValueError("KRX response session date mismatch")
        identity_fields = _identity_field(endpoint)
        identities = [
            tuple(str(row.get(field) or "") for field in identity_fields)
            for row in rows
            if isinstance(row, dict)
        ]
        if any(not all(identity) for identity in identities):
            raise ValueError("KRX response contains a missing identity")
        if endpoint in {
            KOSPI_DAILY_PATH,
            KOSDAQ_DAILY_PATH,
            KOSPI_REFERENCE_PATH,
            KOSDAQ_REFERENCE_PATH,
        } and any(len(identity[0]) != 6 for identity in identities):
            raise ValueError("KRX response contains a non-six-character short code")
        if len(identities) != len(set(identities)):
            raise ValueError("KRX response contains duplicate identities")
        return envelope

    async def _fetch_envelope(
        self, endpoint: str, session_date: date
    ) -> dict[str, Any]:
        if not self.api_key:
            raise RuntimeError("KRX_OPEN_API_KEY is not configured")

        async with self._request_lock:
            started = time.monotonic()
            async with httpx.AsyncClient(
                base_url=self.base_url,
                headers={"AUTH_KEY": self.api_key},
                timeout=30.0,
                transport=self.transport,
            ) as client:
                response = await client.get(
                    endpoint,
                    params={"basDd": session_date.strftime("%Y%m%d")},
                )
            latency = time.monotonic() - started
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict):
            raise ValueError("KRX response must be an object")
        rows = payload.get("OutBlock_1")
        if not isinstance(rows, list):
            raise ValueError("KRX response must contain OutBlock_1 rows")
        return {
            "provider": self.name,
            "endpoint": endpoint,
            "request_date": session_date.isoformat(),
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "latency_seconds": latency,
            "http_metadata": {
                "status_code": response.status_code,
                "rate_limit_headers": {
                    key.lower(): value
                    for key, value in response.headers.items()
                    if key.lower().startswith("x-ratelimit")
                    or key.lower() == "retry-after"
                },
            },
            "response_sha256": _sha256(payload),
            "row_count": len(rows),
            "rows": rows,
        }

    async def _request(
        self, endpoint: str, session_date: date, *, refresh: bool = False
    ) -> dict[str, Any]:
        cache_path = self._cache_path(endpoint, session_date)
        if cache_path.exists() and not refresh:
            cached = json.loads(cache_path.read_text(encoding="utf-8"))
            if not isinstance(cached, dict):
                raise ValueError("KRX cache must contain an object")
            return self._validate_envelope(
                cached, endpoint=endpoint, session_date=session_date
            )
        if not self.api_key:
            raise RuntimeError("KRX_OPEN_API_KEY is not configured")
        envelope = await self._fetch_envelope(endpoint, session_date)
        self._validate_envelope(
            envelope, endpoint=endpoint, session_date=session_date
        )
        _atomic_json(cache_path, envelope)
        self._last_response_metadata = dict(envelope["http_metadata"])
        return envelope

    async def probe_publication_readiness(
        self,
        *,
        target_session: date,
        latest_completed_session: date,
    ) -> KrxPublicationReadiness:
        observed_at = datetime.now(timezone.utc)
        if target_session > latest_completed_session:
            return KrxPublicationReadiness(
                status="MARKET_NOT_COMPLETED",
                target_session=target_session,
                latest_completed_session=latest_completed_session,
                observed_at=observed_at,
                current_snapshot_promotable=False,
                reason_codes=["target_session_not_completed"],
            )

        endpoint_results: list[KrxEndpointReadiness] = []
        expected_date = target_session.strftime("%Y%m%d")
        for endpoint in CORE_READINESS_ENDPOINTS:
            try:
                envelope = await self._fetch_envelope(endpoint, target_session)
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
            except RuntimeError:
                endpoint_results.append(
                    KrxEndpointReadiness(
                        endpoint=endpoint,
                        status="ERROR",
                        error_code="configuration_error",
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

            rows = self._rows(envelope)
            metadata = envelope.get("http_metadata") or {}
            latency = _number(envelope.get("latency_seconds"))
            common = {
                "endpoint": endpoint,
                "http_status": metadata.get("status_code"),
                "row_count": len(rows),
                "latency_seconds": latency,
                "payload_sha256": str(envelope.get("response_sha256") or "") or None,
            }
            if not rows:
                endpoint_results.append(
                    KrxEndpointReadiness(status="EMPTY", **common)
                )
                continue

            raw_dates = [str(row.get("BAS_DD") or "") for row in rows]
            parsed_dates = sorted(
                {parsed for value in raw_dates if (parsed := _krx_date(value))}
            )
            if any(not value for value in raw_dates):
                endpoint_results.append(
                    KrxEndpointReadiness(
                        status="ERROR",
                        provider_dates=parsed_dates,
                        error_code="provider_date_missing",
                        **common,
                    )
                )
                continue
            if len(parsed_dates) != len(set(raw_dates)):
                endpoint_results.append(
                    KrxEndpointReadiness(
                        status="ERROR",
                        provider_dates=parsed_dates,
                        error_code="provider_date_invalid",
                        **common,
                    )
                )
                continue
            if set(raw_dates) != {expected_date}:
                endpoint_results.append(
                    KrxEndpointReadiness(
                        status="STALE",
                        provider_dates=parsed_dates,
                        error_code="provider_date_mismatch",
                        **common,
                    )
                )
                continue
            try:
                self._validate_envelope(
                    envelope,
                    endpoint=endpoint,
                    session_date=target_session,
                )
            except (TypeError, ValueError):
                endpoint_results.append(
                    KrxEndpointReadiness(
                        status="ERROR",
                        provider_dates=parsed_dates,
                        error_code="identity_or_schema_error",
                        **common,
                    )
                )
                continue

            required = REQUIRED_INDEX_IDENTITIES.get(endpoint, set())
            observed_identities = {
                (str(row.get("IDX_CLSS") or ""), str(row.get("IDX_NM") or ""))
                for row in rows
            }
            missing = sorted(f"{item[0]}:{item[1]}" for item in required - observed_identities)
            if missing:
                endpoint_results.append(
                    KrxEndpointReadiness(
                        status="PARTIAL",
                        provider_dates=parsed_dates,
                        missing_required_identities=missing,
                        error_code="required_index_identity_missing",
                        **common,
                    )
                )
                continue
            endpoint_results.append(
                KrxEndpointReadiness(
                    status="READY",
                    provider_dates=parsed_dates,
                    **common,
                )
            )

        endpoint_states = {item.status for item in endpoint_results}
        reason_codes: list[str]
        if "ERROR" in endpoint_states:
            status: PublicationReadinessStatus = "PROVIDER_ERROR"
            reason_codes = ["one_or_more_core_endpoints_failed"]
        elif "STALE" in endpoint_states:
            status = "STALE_PROVIDER_DATE"
            reason_codes = ["provider_date_does_not_match_target_session"]
        elif endpoint_states == {"EMPTY"}:
            status = "MARKET_COMPLETED_PROVIDER_PENDING"
            reason_codes = ["all_core_endpoints_returned_empty_200"]
        elif endpoint_states == {"READY"}:
            status = "PROVIDER_COMPLETE"
            reason_codes = []
        else:
            status = "PROVIDER_PARTIAL"
            reason_codes = ["core_endpoint_bundle_not_complete"]

        complete = status == "PROVIDER_COMPLETE"
        empty = status == "MARKET_COMPLETED_PROVIDER_PENDING"
        return KrxPublicationReadiness(
            status=status,
            target_session=target_session,
            latest_completed_session=latest_completed_session,
            observed_at=observed_at,
            endpoints=endpoint_results,
            # A stateless point probe cannot know whether it is the first observation.
            # The append-only publication timeline owns first-observed semantics.
            first_non_empty_at=None,
            first_complete_at=None,
            observed_complete_by=observed_at if complete else None,
            last_empty_at=observed_at if empty else None,
            provider_publication_timestamp=None,
            current_snapshot_promotable=complete,
            reason_codes=reason_codes,
        )

    @staticmethod
    def _rows(envelope: dict[str, Any]) -> list[dict[str, Any]]:
        rows = envelope.get("rows")
        if not isinstance(rows, list):
            raise ValueError("KRX envelope rows are missing")
        return [row for row in rows if isinstance(row, dict)]

    @staticmethod
    def _is_spac(reference: dict[str, Any]) -> bool:
        segment = str(reference.get("SECT_TP_NM") or "")
        name = str(reference.get("ISU_ABBRV") or reference.get("ISU_NM") or "")
        return segment.startswith("SPAC") or "스팩" in name

    def normalize(
        self,
        *,
        session_date: date,
        daily_envelopes: list[dict[str, Any]],
        reference_envelopes: list[dict[str, Any]],
    ) -> tuple[list[NormalizedMarketRow], Counter[str]]:
        reference_by_ticker = {
            str(row.get("ISU_SRT_CD")): row
            for envelope in reference_envelopes
            for row in self._rows(envelope)
            if row.get("ISU_SRT_CD")
        }
        rows: list[NormalizedMarketRow] = []
        exclusions: Counter[str] = Counter()
        for envelope in daily_envelopes:
            for raw in self._rows(envelope):
                ticker = str(raw.get("ISU_CD") or "")
                reference = reference_by_ticker.get(ticker)
                reasons: list[str] = []
                if reference is None:
                    reasons.append("reference_missing")
                else:
                    if str(reference.get("MKT_TP_NM") or "") != str(
                        raw.get("MKT_NM") or ""
                    ):
                        reasons.append("market_identity_mismatch")
                    if str(reference.get("SECUGRP_NM") or "") != "주권":
                        reasons.append("ineligible_security_group")
                    if str(reference.get("KIND_STKCERT_TP_NM") or "") != "보통주":
                        reasons.append("ineligible_certificate_type")
                    if self._is_spac(reference):
                        reasons.append("spac")
                    listing_date_text = str(reference.get("LIST_DD") or "").strip()
                    listing_date = _krx_date(listing_date_text)
                    if not listing_date_text:
                        reasons.append("listing_date_missing")
                    elif listing_date is None:
                        reasons.append("listing_date_invalid")
                    elif listing_date == session_date:
                        reasons.append("new_listing_no_prior_close")
                    elif listing_date > session_date:
                        reasons.append("future_listing")

                close = _number(raw.get("TDD_CLSPRC"))
                change = _number(raw.get("CMPPREVDD_PRC"))
                return_pct = _number(raw.get("FLUC_RT"))
                previous_close = (
                    close - change
                    if close is not None and change is not None
                    else None
                )
                if close is None or close <= 0:
                    exclusions["invalid_close"] += 1
                    continue
                if previous_close is None or previous_close <= 0:
                    reasons.append("missing_comparable_previous_close")
                    previous_close = None
                if return_pct is None:
                    reasons.append("official_return_missing")
                for reason in set(reasons):
                    exclusions[reason] += 1
                market = str(raw.get("MKT_NM") or "")
                rows.append(
                    NormalizedMarketRow(
                        ticker=ticker,
                        session_date=session_date,
                        close=close,
                        previous_close=previous_close,
                        volume=_number(raw.get("ACC_TRDVOL")),
                        trading_value=_number(raw.get("ACC_TRDVAL")),
                        official_return_pct=return_pct,
                        security_type="common_share" if not reasons else None,
                        primary_exchange=market,
                        currency="KRW",
                        eligible=not reasons,
                        exclusion_reasons=sorted(set(reasons)),
                    )
                )
        return rows, exclusions

    def _index_facts(
        self, envelopes: list[dict[str, Any]]
    ) -> tuple[list[MarketIndexFact], list[MarketSectorFact]]:
        raw_rows = [row for envelope in envelopes for row in self._rows(envelope)]
        indices: list[MarketIndexFact] = []
        broad_returns: dict[str, float] = {}
        for raw in raw_rows:
            identity = (str(raw.get("IDX_CLSS") or ""), str(raw.get("IDX_NM") or ""))
            mapped = MAJOR_INDEX_IDENTITIES.get(identity)
            if mapped is None:
                continue
            close = _number(raw.get("CLSPRC_IDX"))
            if close is None or close <= 0:
                raise ValueError(f"KRX major index close is invalid: {identity[1]}")
            return_pct = _number(raw.get("FLUC_RT"))
            symbol, label = mapped
            indices.append(
                MarketIndexFact(
                    symbol=symbol,
                    label=label,
                    close=close,
                    return_pct=return_pct,
                    volume=_number(raw.get("ACC_TRDVOL")),
                    trading_value=_number(raw.get("ACC_TRDVAL")),
                )
            )
            if symbol in {"KOSPI200", "KOSDAQ150"} and return_pct is not None:
                broad_returns[symbol] = return_pct
        missing = set(value[0] for value in MAJOR_INDEX_IDENTITIES.values()) - {
            item.symbol for item in indices
        }
        if missing:
            raise ValueError("KRX major index identities are missing: " + ", ".join(sorted(missing)))

        sectors: list[MarketSectorFact] = []
        for raw in raw_rows:
            name = str(raw.get("IDX_NM") or "")
            if name not in SECTOR_INDEX_IDENTITIES:
                continue
            value = _number(raw.get("FLUC_RT"))
            benchmark = "KOSPI200" if name.startswith("코스피 200 ") else "KOSDAQ150"
            sectors.append(
                MarketSectorFact(
                    sector=name,
                    taxonomy=f"KRX_{benchmark}_SECTOR_INDEX",
                    metric_role="sector_price_proxy",
                    return_pct=value,
                    relative_return_pct=(
                        value - broad_returns[benchmark]
                        if value is not None and benchmark in broad_returns
                        else None
                    ),
                )
            )
        return sorted(indices, key=lambda item: item.symbol), sorted(
            sectors, key=lambda item: (item.taxonomy, item.sector)
        )

    async def collect(
        self,
        *,
        session_date: date,
        expected_session_date: date | None = None,
        refresh: bool = False,
    ) -> MarketCrossSection:
        if expected_session_date is not None and session_date != expected_session_date:
            raise ValueError("KRX requested session does not match the expected XKRX session")
        endpoints = (
            KOSPI_DAILY_PATH,
            KOSDAQ_DAILY_PATH,
            KOSPI_REFERENCE_PATH,
            KOSDAQ_REFERENCE_PATH,
            KOSPI_INDEX_PATH,
            KOSDAQ_INDEX_PATH,
        )
        envelopes = {
            endpoint: await self._request(endpoint, session_date, refresh=refresh)
            for endpoint in endpoints
        }
        daily = [envelopes[KOSPI_DAILY_PATH], envelopes[KOSDAQ_DAILY_PATH]]
        reference = [
            envelopes[KOSPI_REFERENCE_PATH],
            envelopes[KOSDAQ_REFERENCE_PATH],
        ]
        normalized, exclusions = self.normalize(
            session_date=session_date,
            daily_envelopes=daily,
            reference_envelopes=reference,
        )
        breadth = calculate_market_breadth(normalized)
        segment_rows = {
            segment: [row for row in normalized if row.primary_exchange == segment]
            for segment in ("KOSPI", "KOSDAQ")
        }
        breadth_by_segment = {
            segment: calculate_market_breadth(rows)
            for segment, rows in segment_rows.items()
        }
        indices, sectors = self._index_facts(
            [envelopes[KOSPI_INDEX_PATH], envelopes[KOSDAQ_INDEX_PATH]]
        )
        raw_count = sum(len(self._rows(item)) for item in daily)
        source_hash = _sha256(
            {
                endpoint: envelope.get("response_sha256")
                for endpoint, envelope in envelopes.items()
            }
        )
        as_of = max(
            datetime.fromisoformat(str(envelope["fetched_at"]))
            for envelope in envelopes.values()
        )
        return MarketCrossSection(
            market="KR",
            session_date=session_date,
            as_of=as_of,
            indices=indices,
            breadth=breadth,
            breadth_by_segment=breadth_by_segment,
            sectors=sectors,
            market_flows=[],
            quality=MarketCrossSectionQuality(
                provider=self.name,
                provider_role=self.provider_role,
                coverage="partial",
                freshness="fresh",
                universe_version=UNIVERSE_VERSION,
                raw_count=raw_count,
                eligible_count=breadth.eligible_count,
                excluded_count=raw_count - breadth.eligible_count,
                exclusion_reason_counts=dict(sorted(exclusions.items())),
                warnings=[
                    "KRX Open API does not expose a suspension flag; otherwise eligible zero-volume rows remain in the unchanged denominator.",
                    "SPAC exclusion uses official segment metadata plus the official issue-name marker for residual cases.",
                    "Sector facts are KRX sector-index price proxies, not security-level sector breadth.",
                    "Market-wide investor flows are unavailable in the approved KRX Open API catalog.",
                ],
                volume_semantics="raw_reported_shares",
                trading_value_semantics="official_reported",
            ),
            source_payload_sha256=source_hash,
        )
