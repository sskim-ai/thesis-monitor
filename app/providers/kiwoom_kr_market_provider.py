from __future__ import annotations

import re
from datetime import date, datetime
from typing import Literal
from urllib.parse import urlsplit

import httpx
from pydantic import BaseModel, Field, model_validator

from app.config import get_settings
from app.services.market_cross_section_service import (
    MarketBreadth,
    MarketCrossSection,
    MarketCrossSectionQuality,
    MarketFlowFact,
    MarketIndexFact,
    MarketSectorFact,
)


CAPABILITY_PATH = "/v1/kr-market/capabilities"
SNAPSHOT_PATH = "/v1/kr-market/snapshot"
CONTRACT_VERSION = "kiwoom-kr-market-gateway-v1"
CapabilityStatus = Literal[
    "SUPPORTED",
    "PARTIAL",
    "UNSUPPORTED",
    "NOT_CONFIGURED",
    "PENDING_PROVIDER_APPROVAL",
]

_SENSITIVE_KEY_RE = re.compile(
    r"(?:^|_)(?:account|app_?key|certificate|credential|hts_?id|password|secret|token)(?:_|$)",
    re.IGNORECASE,
)


def validate_gateway_url(value: str) -> str:
    parsed = urlsplit(value)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("Kiwoom gateway URL must be an absolute HTTP(S) URL")
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ValueError("Kiwoom gateway credentials and query parameters are forbidden")
    return value.rstrip("/")


def contains_sensitive_data(value: object) -> bool:
    if isinstance(value, dict):
        return any(
            (
                str(key) != "account_data_exposed"
                and bool(_SENSITIVE_KEY_RE.search(str(key)))
            )
            or (str(key) == "account_data_exposed" and item is not False)
            or contains_sensitive_data(item)
            for key, item in value.items()
        )
    if isinstance(value, list):
        return any(contains_sensitive_data(item) for item in value)
    return False


class KiwoomCapabilityMetric(BaseModel):
    metric: str
    status: CapabilityStatus
    tr_or_function: str | None = None
    request_scope: Literal[
        "market_summary", "sector_summary", "all_stock_multirow", "index", "unsupported"
    ]
    rows_per_request: int | None = None
    worst_case_pages: int | None = None
    pagination: bool = False
    verified_in_koa_studio: bool = False
    denominator_semantics_verified: bool = False
    notes: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_supported(self) -> "KiwoomCapabilityMetric":
        if self.status == "SUPPORTED":
            if not self.verified_in_koa_studio or not self.tr_or_function:
                raise ValueError("supported Kiwoom metric requires verified TR evidence")
            if self.request_scope == "all_stock_multirow" and (
                not self.rows_per_request or not self.worst_case_pages
            ):
                raise ValueError("multi-row capability requires request-volume evidence")
        return self


class KiwoomKrMarketCapabilities(BaseModel):
    contract_version: Literal["kiwoom-kr-market-gateway-v1"] = CONTRACT_VERSION
    captured_at: datetime
    gateway_platform: Literal["Windows OCX gateway"]
    source: Literal["gateway_live", "gateway_fixture"]
    metrics: list[KiwoomCapabilityMetric]
    rate_limit_per_second: int = 5
    rate_limit_per_minute: int = 100
    rate_limit_per_hour: int = 1000
    account_data_exposed: Literal[False] = False

    @model_validator(mode="after")
    def validate_payload(self) -> "KiwoomKrMarketCapabilities":
        if self.captured_at.tzinfo is None:
            raise ValueError("capability timestamp must be timezone-aware")
        names = [item.metric for item in self.metrics]
        if len(names) != len(set(names)):
            raise ValueError("capability metrics must be unique")
        return self

    def metric(self, name: str) -> KiwoomCapabilityMetric | None:
        return next((item for item in self.metrics if item.metric == name), None)

    @property
    def efficient_breadth_supported(self) -> bool:
        direct = self.metric("market_breadth")
        rows = self.metric("all_stock_multirow")
        return bool(
            direct
            and direct.status == "SUPPORTED"
            and direct.denominator_semantics_verified
        ) or bool(
            rows
            and rows.status == "SUPPORTED"
            and rows.denominator_semantics_verified
            and (rows.worst_case_pages or 0) <= 20
        )


class KiwoomKrMarketSnapshot(BaseModel):
    contract_version: Literal["kiwoom-kr-market-gateway-v1"] = CONTRACT_VERSION
    session_date: date
    as_of: datetime
    source: Literal["kiwoom"] = "kiwoom"
    quality: Literal["verified", "partial", "stale"]
    universe_version: str
    indices: list[MarketIndexFact] = Field(default_factory=list)
    breadth: MarketBreadth | None = None
    sectors: list[MarketSectorFact] = Field(default_factory=list)
    market_flows: list[MarketFlowFact] = Field(default_factory=list)
    source_payload_sha256: str

    @model_validator(mode="after")
    def validate_snapshot(self) -> "KiwoomKrMarketSnapshot":
        if self.as_of.tzinfo is None:
            raise ValueError("snapshot timestamp must be timezone-aware")
        if self.quality == "stale" and self.breadth is not None:
            raise ValueError("stale snapshot cannot publish current breadth")
        return self


class KiwoomKrMarketProvider:
    name = "kiwoom"
    provider_role = "bridge_shadow"

    def __init__(
        self,
        *,
        gateway_url: str | None = None,
        api_key: str | None = None,
        timeout_seconds: float | None = None,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        settings = get_settings()
        configured_url = gateway_url if gateway_url is not None else settings.kiwoom_gateway_url
        self.gateway_url = validate_gateway_url(configured_url) if configured_url else None
        self.api_key = api_key if api_key is not None else settings.kiwoom_gateway_api_key
        self.timeout_seconds = timeout_seconds or settings.kiwoom_gateway_timeout_seconds
        self.transport = transport

    @property
    def configured(self) -> bool:
        return bool(self.gateway_url and self.api_key)

    def _headers(self) -> dict[str, str]:
        return {"X-Gateway-API-Key": self.api_key or ""}

    async def capabilities(self) -> KiwoomKrMarketCapabilities:
        if not self.configured:
            raise RuntimeError("Kiwoom market gateway is not configured")
        async with httpx.AsyncClient(
            base_url=self.gateway_url,
            headers=self._headers(),
            timeout=self.timeout_seconds,
            transport=self.transport,
        ) as client:
            response = await client.get(CAPABILITY_PATH)
            response.raise_for_status()
            payload = response.json()
        if contains_sensitive_data(payload):
            raise ValueError("Kiwoom gateway response contains sensitive account data")
        return KiwoomKrMarketCapabilities.model_validate(payload)

    async def collect(self, session_date: date) -> MarketCrossSection:
        capabilities = await self.capabilities()
        if not capabilities.efficient_breadth_supported:
            raise RuntimeError("efficient market-wide Kiwoom breadth is not verified")
        async with httpx.AsyncClient(
            base_url=self.gateway_url,
            headers=self._headers(),
            timeout=self.timeout_seconds,
            transport=self.transport,
        ) as client:
            response = await client.get(
                SNAPSHOT_PATH,
                params={"date": session_date.isoformat()},
            )
            response.raise_for_status()
            payload = response.json()
        if contains_sensitive_data(payload):
            raise ValueError("Kiwoom gateway response contains sensitive account data")
        snapshot = KiwoomKrMarketSnapshot.model_validate(payload)
        if snapshot.session_date != session_date:
            raise ValueError("Kiwoom snapshot session date mismatch")
        if snapshot.quality != "verified" or snapshot.breadth is None:
            raise RuntimeError("Kiwoom breadth snapshot is not verified and complete")
        return MarketCrossSection(
            market="KR",
            session_date=snapshot.session_date,
            as_of=snapshot.as_of,
            indices=snapshot.indices,
            breadth=snapshot.breadth,
            sectors=snapshot.sectors,
            market_flows=snapshot.market_flows,
            quality=MarketCrossSectionQuality(
                provider=self.name,
                provider_role=self.provider_role,
                coverage="full",
                freshness="fresh",
                universe_version=snapshot.universe_version,
                raw_count=snapshot.breadth.eligible_count,
                eligible_count=snapshot.breadth.eligible_count,
                excluded_count=0,
            ),
            source_payload_sha256=snapshot.source_payload_sha256,
        )
