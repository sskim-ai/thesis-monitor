from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Mapping
from datetime import UTC, date, datetime
from enum import StrEnum
from typing import Literal

import httpx
from pydantic import BaseModel, ConfigDict, Field

from app.config import get_settings
from app.services.ai_review_service import _chart_facts
from app.services.cross_market_decision_engine_service import (
    DecisionEvidencePacket,
    build_decision_evidence_packet,
)
from app.services.ohlcv_client import OhlcvClient
from app.services.packet_owned_technical_context_service import (
    TechnicalContextStatus,
    load_packet_owned_technical_context,
)
from app.utils.tickers import normalize_ticker


CONTRACT_VERSION = "coldstart-source-assembly-v1"
PACKET_SCHEMA_VERSION = "coldstart-research-packet-v1"
NORMALIZATION_VERSION = "production-source-reuse-v1"
BASE_CONTEXT_VERSION = "deterministic-coldstart-base-context-v1"


class FrozenModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class SourceAssemblyStatus(StrEnum):
    ASSEMBLED = "ASSEMBLED"
    OBJECTIVE_SOURCE_LIMIT = "OBJECTIVE_SOURCE_LIMIT"
    IDENTITY_UNRESOLVED = "IDENTITY_UNRESOLVED"
    UNSUPPORTED_SECURITY = "UNSUPPORTED_SECURITY"
    VALIDATION_BLOCK = "VALIDATION_BLOCK"


class SourceSecurityIdentity(FrozenModel):
    ticker: str
    company_name: str
    market: Literal["kr", "us"]
    exchange: str
    sector: str = ""
    industry: str = ""
    security_type: str = "common_stock"
    source: str
    source_as_of: str | None = None
    source_sha256: str


class SourceAssemblyResult(FrozenModel):
    contract: str = CONTRACT_VERSION
    status: SourceAssemblyStatus
    ticker: str
    market: Literal["kr", "us"]
    packet: dict[str, object] | None = None
    packet_sha256: str | None = None
    deterministic_base_context: str | None = None
    deterministic_base_context_sha256: str | None = None
    validation_errors: tuple[str, ...] = ()
    cautions: tuple[str, ...] = ()
    provider_audit: dict[str, object] = Field(default_factory=dict)
    production_db_mutation: Literal[0] = 0
    monitoring_registration: Literal[0] = 0
    ai_judgment_calls: Literal[0] = 0

    def decision_evidence_packet(self) -> DecisionEvidencePacket:
        if self.status != SourceAssemblyStatus.ASSEMBLED or self.packet is None:
            raise ValueError(f"assembled_packet_required:{self.ticker}")
        stocks = self.packet.get("stocks")
        if not isinstance(stocks, list) or len(stocks) != 1:
            raise ValueError(f"single_stock_packet_required:{self.ticker}")
        stock = stocks[0]
        if not isinstance(stock, Mapping):
            raise ValueError(f"stock_object_required:{self.ticker}")
        technical = load_packet_owned_technical_context(
            stock.get("technical_context"), ticker=self.ticker
        )
        return build_decision_evidence_packet(
            packet=self.packet,
            stock=stock,
            technical_context=technical,
        )


def canonical_sha256(value: object) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _normalized_as_of(value: datetime) -> datetime:
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


def _identity_from_mapping(
    ticker: str,
    market: Literal["kr", "us"],
    value: Mapping[str, object],
) -> SourceSecurityIdentity:
    source_material = {
        key: value.get(key)
        for key in (
            "ticker",
            "code",
            "company_name",
            "name",
            "market",
            "exchange",
            "sector",
            "industry",
            "security_type",
            "source",
            "source_as_of",
        )
    }
    resolved_ticker = str(value.get("ticker") or value.get("code") or "").strip().upper()
    if resolved_ticker != ticker:
        raise ValueError("source_identity_ticker_mismatch")
    resolved_market = str(value.get("market") or market).strip().lower()
    if resolved_market not in {market, market.upper().lower()}:
        raise ValueError("source_identity_market_mismatch")
    company_name = str(value.get("company_name") or value.get("name") or "").strip()
    exchange = str(value.get("exchange") or "").strip()
    if not company_name or not exchange:
        raise ValueError("source_identity_incomplete")
    return SourceSecurityIdentity(
        ticker=ticker,
        company_name=company_name,
        market=market,
        exchange=exchange,
        sector=str(value.get("sector") or "").strip(),
        industry=str(value.get("industry") or "").strip(),
        security_type=str(value.get("security_type") or "common_stock").strip(),
        source=str(value.get("source") or "approved_identity_source").strip(),
        source_as_of=(str(value.get("source_as_of")) if value.get("source_as_of") else None),
        source_sha256=canonical_sha256(source_material),
    )


async def _resolve_identity(
    ticker: str,
    market: Literal["kr", "us"],
    *,
    transport: httpx.AsyncBaseTransport | None = None,
) -> SourceSecurityIdentity:
    settings = get_settings()
    api_key = settings.ohlcv_api_key or settings.action_api_key
    headers = {"X-API-Key": api_key} if api_key else {}
    async with httpx.AsyncClient(
        base_url=settings.ohlcv_base_url.rstrip("/"),
        headers=headers,
        timeout=settings.ohlcv_timeout_seconds,
        transport=transport,
    ) as client:
        response = await client.get(
            "/symbol/resolve",
            params={"symbol": ticker, "market": market.upper()},
        )
        response.raise_for_status()
        body = response.json()
    resolved = body.get("resolved_symbol") if isinstance(body, Mapping) else None
    if not isinstance(resolved, Mapping):
        raise ValueError("source_identity_unresolved")
    return _identity_from_mapping(
        ticker,
        market,
        {
            **resolved,
            "ticker": resolved.get("code"),
            "company_name": resolved.get("name"),
            "source": "ohlcv_analyst_symbol_resolver",
        },
    )


def _price_fact(price: Mapping[str, object]) -> dict[str, object]:
    return {
        "fact_id": "price:current",
        "fact_type": "price",
        "as_of_date": str(price.get("price_as_of") or ""),
        "source": "ohlcv_analyst",
        "fields": {
            key: price.get(key)
            for key in (
                "current_price",
                "currency",
                "price_as_of",
                "exchange_trade_date",
                "latest_completed_regular_session_date",
                "price_basis",
                "market_session",
                "assessment_state",
            )
            if price.get(key) is not None
        },
    }


def _identity_facts(identity: SourceSecurityIdentity, as_of: str) -> list[dict[str, object]]:
    return [
        {
            "fact_id": "security_identity:current",
            "fact_type": "security_identity",
            "as_of_date": identity.source_as_of or as_of,
            "source": identity.source,
            "fields": {
                "ticker": identity.ticker,
                "company_name": identity.company_name,
                "market": identity.market,
                "exchange": identity.exchange,
                "security_type": identity.security_type,
                "source_sha256": identity.source_sha256,
            },
            "numeric_registry_eligible": False,
        },
        {
            "fact_id": "industry:classification",
            "fact_type": "industry_context",
            "as_of_date": identity.source_as_of or as_of,
            "source": identity.source,
            "fields": {
                "sector": identity.sector or "unclassified",
                "industry": identity.industry or "unclassified",
                "classification_use": "context_only",
            },
            "numeric_registry_eligible": False,
        },
    ]


def deterministic_base_context(packet: Mapping[str, object]) -> str:
    stocks = packet.get("stocks")
    if not isinstance(stocks, list) or len(stocks) != 1 or not isinstance(stocks[0], Mapping):
        raise ValueError("single_stock_packet_required")
    stock = stocks[0]
    source = packet.get("source_assembly")
    source = source if isinstance(source, Mapping) else {}
    lines = [
        f"[{stock.get('ticker')}] {stock.get('company_name')}",
        f"시장/업종: {packet.get('market')} / {stock.get('sector') or '미분류'} / "
        f"{stock.get('industry') or '미분류'}",
        f"가격 기준일: {source.get('price_as_of') or '확인 불가'}",
        "정식 monitoring thesis와 이전 판단은 사용하지 않았습니다.",
        "실적, 밸류에이션, 기업 이벤트가 packet에 없으면 Unknown으로 유지합니다.",
    ]
    return "\n".join(lines)


def _validation_errors(
    *,
    identity: SourceSecurityIdentity,
    as_of: datetime,
    price: Mapping[str, object],
    technical_status: str,
    facts: list[dict[str, object]],
) -> tuple[list[str], list[str], str, str]:
    errors: list[str] = []
    cautions: list[str] = []
    current_price = price.get("current_price")
    price_present = current_price is not None
    price_valid = (
        isinstance(current_price, (int, float))
        and not isinstance(current_price, bool)
        and math.isfinite(float(current_price))
        and current_price > 0
    )
    price_as_of = str(price.get("price_as_of") or "")[:10]
    price_date: date | None = None
    if price_as_of:
        try:
            price_date = date.fromisoformat(price_as_of)
        except ValueError:
            errors.append("price_as_of_invalid")

    technical_safe = technical_status in {
        TechnicalContextStatus.FULL,
        TechnicalContextStatus.PARTIAL_SAFE,
    }
    technical_unavailable = technical_status == TechnicalContextStatus.UNAVAILABLE
    if not technical_safe and not technical_unavailable:
        errors.append(f"technical_context_invalid:{technical_status}")

    price_context_readiness = "UNAVAILABLE"
    price_timing_readiness = (
        "UNAVAILABLE_SAFE" if technical_unavailable else "UNAVAILABLE"
    )
    if not price_present and not price_as_of:
        cautions.extend(("current_price_unavailable", "price_as_of_unavailable"))
        if technical_safe:
            errors.append("price_technical_context_inconsistent")
    elif not price_present or not price_as_of:
        errors.append("price_context_incomplete")
    elif not price_valid:
        errors.append("current_price_invalid")
    elif price_date is not None:
        if price_date > as_of.date():
            errors.append("future_price_fact")
        currency = str(price.get("currency") or "").strip()
        if not currency or currency.lower() == "unknown":
            errors.append("price_currency_unavailable")
        if str(price.get("price_basis") or "unavailable").lower() == "unavailable":
            errors.append("price_basis_inconsistent")
        price_context_readiness = "READY"
        if technical_safe:
            price_timing_readiness = "READY"
        elif technical_unavailable:
            cautions.append("technical_context_unavailable")

    if identity.security_type.lower() not in {
        "common_stock",
        "common stock",
        "ordinary_share",
        "ordinary share",
        "adr",
        "ads",
        "depositary_receipt",
    }:
        errors.append("unsupported_security_type")
    fact_ids = [str(fact.get("fact_id") or "") for fact in facts]
    if any(not fact_id for fact_id in fact_ids) or len(fact_ids) != len(set(fact_ids)):
        errors.append("fact_identity_invalid")
    return errors, cautions, price_context_readiness, price_timing_readiness


async def assemble_research_packet(
    ticker: str,
    as_of: datetime,
    mode: Literal["read_only"] = "read_only",
    *,
    identity: SourceSecurityIdentity | Mapping[str, object] | None = None,
    price_client: OhlcvClient | None = None,
    identity_transport: httpx.AsyncBaseTransport | None = None,
) -> SourceAssemblyResult:
    if mode != "read_only":
        raise ValueError("coldstart_source_assembly_read_only_required")
    normalized = normalize_ticker(ticker)
    market: Literal["kr", "us"] = "kr" if normalized.isdigit() else "us"
    current = _normalized_as_of(as_of)
    try:
        resolved = (
            identity
            if isinstance(identity, SourceSecurityIdentity)
            else _identity_from_mapping(normalized, market, identity)
            if isinstance(identity, Mapping)
            else await _resolve_identity(
                normalized,
                market,
                transport=identity_transport,
            )
        )
    except (httpx.HTTPError, TypeError, ValueError) as exc:
        return SourceAssemblyResult(
            status=SourceAssemblyStatus.IDENTITY_UNRESOLVED,
            ticker=normalized,
            market=market,
            validation_errors=(type(exc).__name__, str(exc)),
            provider_audit={"identity": "failed", "ohlcv": "not_called"},
        )

    try:
        price_context = await (price_client or OhlcvClient()).fetch_price_context(
            normalized,
            as_of=current,
            session=None,
        )
    except (httpx.HTTPError, TypeError, ValueError) as exc:
        return SourceAssemblyResult(
            status=SourceAssemblyStatus.OBJECTIVE_SOURCE_LIMIT,
            ticker=normalized,
            market=market,
            validation_errors=(type(exc).__name__, str(exc)),
            provider_audit={"identity": "success", "ohlcv": "failed"},
        )

    price = price_context.decision.model_dump(mode="json")
    chart = price_context.chart.model_dump(mode="json")
    technical = price_context.technical_context_payload()
    try:
        technical_context = load_packet_owned_technical_context(
            technical,
            ticker=normalized,
        )
    except ValueError as exc:
        return SourceAssemblyResult(
            status=SourceAssemblyStatus.VALIDATION_BLOCK,
            ticker=normalized,
            market=market,
            validation_errors=(str(exc),),
            provider_audit={"identity": "success", "ohlcv": "success"},
        )

    price_fact_available = (
        isinstance(price.get("current_price"), (int, float))
        and not isinstance(price.get("current_price"), bool)
        and bool(str(price.get("price_as_of") or "")[:10])
    )
    facts = [*_identity_facts(resolved, current.date().isoformat())]
    if price_fact_available:
        facts.append(_price_fact(price))
    facts.extend(_chart_facts(chart, str(price.get("currency") or "unknown")))
    errors, price_cautions, price_context_readiness, price_timing_readiness = _validation_errors(
        identity=resolved,
        as_of=current,
        price=price,
        technical_status=technical_context.status,
        facts=facts,
    )
    cautions = tuple(dict.fromkeys((*price_context.warnings, *price_cautions)))
    if errors:
        status = (
            SourceAssemblyStatus.UNSUPPORTED_SECURITY
            if "unsupported_security_type" in errors
            else SourceAssemblyStatus.VALIDATION_BLOCK
        )
        return SourceAssemblyResult(
            status=status,
            ticker=normalized,
            market=market,
            validation_errors=tuple(errors),
            cautions=cautions,
            provider_audit={
                "identity": "success",
                "ohlcv": "success",
                "technical_context": technical_context.status,
                "price_context_readiness": price_context_readiness,
                "price_timing_readiness": price_timing_readiness,
            },
        )

    unknowns = [
        "cold-start source packet에는 저장된 monitoring thesis가 없습니다.",
        "검증된 최신 실적과 밸류에이션 근거가 없으면 해당 판단은 보류합니다.",
        "기업별 실적 또는 사업 이벤트 확인이 다음 재평가 조건입니다.",
    ]
    stock = {
        "ticker": normalized,
        "company_name": resolved.company_name,
        "industry": resolved.industry,
        "sector": resolved.sector,
        "business_model": None,
        "thesis": {},
        "unknowns": unknowns,
        "market_transmission": {},
        "current_price_context": {
            "contract": "current-price-context-v1",
            "availability": (
                "ready"
                if price_timing_readiness == "READY"
                else "price_only"
                if price_context_readiness == "READY"
                else "unavailable"
            ),
            "current_price": price.get("current_price"),
            "currency": price.get("currency"),
            "as_of_date": price.get("price_as_of"),
            "price_basis": price.get("price_basis"),
        },
        "fact_catalog": facts,
        "technical_context": technical_context.model_dump(mode="json"),
        "data_cautions": [
            "unregistered_coldstart_context",
            "monitoring_thesis_unavailable",
            "fundamental_and_valuation_evidence_unavailable_unless_explicitly_present",
            *price_context.warnings,
        ],
    }
    packet_body: dict[str, object] = {
        "contract": CONTRACT_VERSION,
        "schema_version": PACKET_SCHEMA_VERSION,
        "normalization_version": NORMALIZATION_VERSION,
        "market": market,
        "assessment_date": current.date().isoformat(),
        "generated_at": current.isoformat(),
        "stocks": [stock],
        "source_assembly": {
            "mode": mode,
            "identity_source": resolved.source,
            "identity_source_sha256": resolved.source_sha256,
            "price_source": "ohlcv_analyst",
            "price_as_of": price.get("price_as_of"),
            "technical_context_id": technical_context.technical_context_id,
            "technical_context_status": technical_context.status,
            "price_context_readiness": price_context_readiness,
            "price_timing_readiness": price_timing_readiness,
            "directional_fundamental_readiness": "PENDING_FUNDAMENTAL_ENRICHMENT",
            "full_e2e_readiness": "PENDING_FUNDAMENTAL_ENRICHMENT",
            "monitoring_baseline_required": 0,
            "stored_monitoring_state_required": 0,
            "production_db_mutation": 0,
        },
    }
    packet_id = f"coldstart-{normalized}-{canonical_sha256(packet_body)[:20]}"
    packet = {**packet_body, "packet_id": packet_id}
    packet_sha = canonical_sha256(packet)
    base_context = deterministic_base_context(packet)
    result = SourceAssemblyResult(
        status=SourceAssemblyStatus.ASSEMBLED,
        ticker=normalized,
        market=market,
        packet=packet,
        packet_sha256=packet_sha,
        deterministic_base_context=base_context,
        deterministic_base_context_sha256=hashlib.sha256(
            base_context.encode("utf-8")
        ).hexdigest(),
        cautions=cautions,
        provider_audit={
            "identity": "success",
            "ohlcv": "success",
            "technical_context": technical_context.status,
            "price_context_readiness": price_context_readiness,
            "price_timing_readiness": price_timing_readiness,
            "price_request_count": technical_context.acquisition.request_count,
            "price_success_count": technical_context.acquisition.success_count,
            "price_cache_use_count": technical_context.acquisition.cache_use_count,
        },
    )
    result.decision_evidence_packet()
    return result
