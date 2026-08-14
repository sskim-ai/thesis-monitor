from __future__ import annotations

import argparse
import asyncio
from datetime import date, datetime, timezone
import json
import math
from pathlib import Path
import re
from typing import Literal
from urllib.parse import urlsplit

import httpx
from pydantic import BaseModel, Field, ValidationError, model_validator

from app.jobs.probe_krx_night_futures import KrxNightFutureObservation


PRODUCTS = ("KOSPI200", "KOSDAQ150")
GATEWAY_CAPABILITY_PATH = "/v1/night-futures/capabilities"
USER_AGENT = "thesis-monitor/Kiwoom-night-futures-capability-probe"
OPENAPI_PLUS_INFO_URL = "https://www.kiwoom.com/h/customer/download/VOpenApiInfoView"
OPENAPI_PLUS_GUIDE_URL = (
    "https://download.kiwoom.com/web/openapi/kiwoom_openapi_plus_devguide_ver_1.7.pdf"
)
REST_INFO_URL = "https://openapi.kiwoom.com/intro"

Capability = Literal["supported", "unsupported", "partial", "unknown"]
Product = Literal["KOSPI200", "KOSDAQ150"]
_SENSITIVE_KEY_RE = re.compile(
    r"(?:^|_)(?:account|app_?key|certificate|credential|hts_?id|password|secret|token)(?:_|$)",
    re.IGNORECASE,
)
_FINAL_SEMANTICS = {"official_close", "session_final_event", "post_close_snapshot"}


class KiwoomFinalNightClose(BaseModel):
    product: Product
    vendor_symbol: str
    contract_code: str
    contract_month: str
    expiry: date
    session_date: date
    session: Literal["night", "regular", "unknown"]
    status: Literal["live", "final"]
    final_price_semantics: Literal[
        "official_close",
        "session_final_event",
        "post_close_snapshot",
        "last_tick",
        "unknown",
    ]
    observed_at: datetime
    regular_close: float
    night_close: float
    point_change: float
    change_pct: float
    tick_size: float
    volume: int | None = None
    subscription_started_at: datetime
    first_tick_at: datetime
    last_tick_at: datetime
    session_finalized_at: datetime
    persisted_at: datetime
    available_for_digest_at: datetime
    digest_deadline_at: datetime

    @model_validator(mode="after")
    def validate_final_close(self) -> KiwoomFinalNightClose:
        if self.session != "night" or self.status != "final":
            raise ValueError("observation is not a finalized night-session close")
        if self.final_price_semantics not in _FINAL_SEMANTICS:
            raise ValueError("final close cannot be inferred from an unverified last tick")
        if not self.vendor_symbol.strip() or not self.contract_code.strip():
            raise ValueError("contract identity is required")
        if self.contract_month != self.expiry.strftime("%Y-%m"):
            raise ValueError("contract month and expiry do not match")
        if self.expiry < self.session_date:
            raise ValueError("expired contract cannot be the session front month")
        if not all(
            value.tzinfo is not None
            for value in (
                self.observed_at,
                self.subscription_started_at,
                self.first_tick_at,
                self.last_tick_at,
                self.session_finalized_at,
                self.persisted_at,
                self.available_for_digest_at,
                self.digest_deadline_at,
            )
        ):
            raise ValueError("gateway timestamps must be timezone-aware")
        if not (
            self.subscription_started_at
            <= self.first_tick_at
            <= self.last_tick_at
            <= self.session_finalized_at
            <= self.persisted_at
            <= self.available_for_digest_at
            <= self.digest_deadline_at
        ):
            raise ValueError("gateway lifecycle timestamps are inconsistent")
        if (
            not math.isfinite(self.regular_close)
            or not math.isfinite(self.night_close)
            or self.regular_close <= 0
            or self.night_close <= 0
            or not math.isfinite(self.tick_size)
            or self.tick_size <= 0
        ):
            raise ValueError("price and tick-size fields must be positive finite numbers")
        expected_change = self.night_close - self.regular_close
        expected_pct = expected_change / self.regular_close * 100
        if abs(self.point_change - expected_change) > self.tick_size + 1e-9:
            raise ValueError("point change is inconsistent with the two closes")
        pct_tolerance = self.tick_size / self.regular_close * 100 + 1e-9
        if abs(self.change_pct - expected_pct) > pct_tolerance:
            raise ValueError("percent change is inconsistent with the two closes")
        if self.volume is not None and self.volume < 0:
            raise ValueError("volume cannot be negative")
        return self


class KiwoomProductEvidence(BaseModel):
    product: Product
    product_supported: bool | None = None
    symbol_discovery: bool | None = None
    recent_month_identified: bool | None = None
    realtime_subscription: bool | None = None
    night_session_ticks: bool | None = None
    closing_phase_ticks: bool | None = None
    final_close_determined: bool | None = None
    session_identity_verified: bool | None = None
    contract_identity_verified: bool | None = None
    observation: KiwoomFinalNightClose | None = None


class KiwoomGatewayCapabilityPayload(BaseModel):
    contract_version: Literal["1"] = "1"
    api_family: Literal["openapi_plus", "rest"]
    platform: Literal["Windows OCX gateway"]
    captured_at: datetime
    products: list[dict[str, object]] = Field(default_factory=list)


class KiwoomProductCapability(BaseModel):
    product: Product
    capability: Capability
    symbol_discovery: bool | None = None
    realtime_support: bool | None = None
    night_session_support: bool | None = None
    closing_phase_support: bool | None = None
    final_close_support: bool | None = None
    session_identity_verified: bool | None = None
    contract_identity_verified: bool | None = None
    observation: KiwoomFinalNightClose | None = None
    reason: str


class KiwoomCapabilityProbeResult(BaseModel):
    status: Literal["ok", "not_configured", "unavailable"]
    source: Literal["official_documentation", "gateway_fixture", "gateway_live"]
    fetched_at: datetime
    api_family: str
    platform: str
    products: list[KiwoomProductCapability] = Field(default_factory=list)
    production_primary_enabled: bool = False
    production_decision: Literal["probe_only", "shadow_candidate", "not_enabled"]
    reason: str | None = None
    warnings: list[str] = Field(default_factory=list)

    def compact_summary(self) -> dict[str, object]:
        return {
            "status": self.status,
            "source": self.source,
            "api_family": self.api_family,
            "platform": self.platform,
            "products": [
                {
                    "product": item.product,
                    "capability": item.capability,
                    "reason": item.reason,
                    "final_close_captured": item.observation is not None,
                }
                for item in self.products
            ],
            "production_primary_enabled": self.production_primary_enabled,
            "production_decision": self.production_decision,
            "reason": self.reason,
            "warnings": self.warnings,
        }


class KiwoomKrxReconciliation(BaseModel):
    product: Product
    result: Literal["verified", "within_tick", "mismatch", "not_comparable"]
    regular_close_difference: float | None = None
    close_difference: float | None = None
    point_change_difference: float | None = None
    percent_change_difference: float | None = None
    reason: str


def _contains_sensitive_key(value: object) -> bool:
    if isinstance(value, dict):
        return any(
            _SENSITIVE_KEY_RE.search(str(key)) or _contains_sensitive_key(item)
            for key, item in value.items()
        )
    if isinstance(value, list):
        return any(_contains_sensitive_key(item) for item in value)
    return False


def documented_capability() -> KiwoomCapabilityProbeResult:
    return KiwoomCapabilityProbeResult(
        status="ok",
        source="official_documentation",
        fetched_at=datetime.now(timezone.utc),
        api_family="openapi_plus_and_rest",
        platform="Windows OCX for OpenAPI+; REST is multi-platform",
        products=[
            KiwoomProductCapability(
                product="KOSPI200",
                capability="partial",
                symbol_discovery=True,
                realtime_support=True,
                night_session_support=None,
                closing_phase_support=None,
                final_close_support=None,
                session_identity_verified=False,
                contract_identity_verified=True,
                reason=(
                    "OpenAPI+ documents KOSPI200 futures discovery and generic futures "
                    "realtime FIDs, but not current KRX night-session identity or final-close "
                    "semantics."
                ),
            ),
            KiwoomProductCapability(
                product="KOSDAQ150",
                capability="unsupported",
                symbol_discovery=False,
                realtime_support=None,
                night_session_support=None,
                closing_phase_support=None,
                final_close_support=None,
                session_identity_verified=False,
                contract_identity_verified=False,
                reason=(
                    "The current official OpenAPI+ product list is limited to stocks, "
                    "KOSPI200 futures, and KOSPI200 options; KOSDAQ150 futures are not listed."
                ),
            ),
        ],
        production_primary_enabled=False,
        production_decision="not_enabled",
        reason="No authenticated live night-session/final-close evidence is available.",
        warnings=[
            "Kiwoom REST officially supports domestic and US stocks, not domestic derivatives.",
            "OpenAPI+ requires a Windows OCX gateway and an authenticated live-session probe.",
        ],
    )


def _product_result(evidence: KiwoomProductEvidence) -> KiwoomProductCapability:
    required = (
        evidence.product_supported,
        evidence.symbol_discovery,
        evidence.recent_month_identified,
        evidence.realtime_subscription,
        evidence.night_session_ticks,
        evidence.closing_phase_ticks,
        evidence.final_close_determined,
        evidence.session_identity_verified,
        evidence.contract_identity_verified,
    )
    if evidence.product_supported is False:
        capability: Capability = "unsupported"
        reason = "Gateway explicitly reports the product as unsupported."
    elif (
        all(value is True for value in required)
        and evidence.observation is not None
        and evidence.observation.product == evidence.product
    ):
        capability = "supported"
        reason = "Night-session subscription, contract identity, and finalized close are verified."
    elif any(value is True for value in required) or evidence.product_supported is True:
        capability = "partial"
        reason = "Some capability exists, but final night-close evidence is incomplete."
    else:
        capability = "unknown"
        reason = "Gateway returned no conclusive capability evidence."
    return KiwoomProductCapability(
        product=evidence.product,
        capability=capability,
        symbol_discovery=evidence.symbol_discovery,
        realtime_support=evidence.realtime_subscription,
        night_session_support=evidence.night_session_ticks,
        closing_phase_support=evidence.closing_phase_ticks,
        final_close_support=evidence.final_close_determined,
        session_identity_verified=evidence.session_identity_verified,
        contract_identity_verified=evidence.contract_identity_verified,
        observation=evidence.observation if capability == "supported" else None,
        reason=reason,
    )


def parse_gateway_capability_payload(
    payload: object,
    *,
    source: Literal["gateway_fixture", "gateway_live"] = "gateway_fixture",
) -> KiwoomCapabilityProbeResult:
    fetched_at = datetime.now(timezone.utc)
    if _contains_sensitive_key(payload):
        return KiwoomCapabilityProbeResult(
            status="unavailable",
            source=source,
            fetched_at=fetched_at,
            api_family="unknown",
            platform="unknown",
            production_primary_enabled=False,
            production_decision="not_enabled",
            reason="gateway_payload_contains_sensitive_fields",
        )
    try:
        gateway = KiwoomGatewayCapabilityPayload.model_validate(payload)
    except ValidationError:
        return KiwoomCapabilityProbeResult(
            status="unavailable",
            source=source,
            fetched_at=fetched_at,
            api_family="unknown",
            platform="unknown",
            production_primary_enabled=False,
            production_decision="not_enabled",
            reason="gateway_payload_validation_failed",
        )
    product_names = [str(item.get("product") or "") for item in gateway.products]
    if len(set(product_names)) != len(product_names):
        return KiwoomCapabilityProbeResult(
            status="unavailable",
            source=source,
            fetched_at=fetched_at,
            api_family=gateway.api_family,
            platform=gateway.platform,
            production_primary_enabled=False,
            production_decision="not_enabled",
            reason="duplicate_product_capability_rows",
        )
    if gateway.api_family == "rest":
        return KiwoomCapabilityProbeResult(
            status="ok",
            source=source,
            fetched_at=fetched_at,
            api_family=gateway.api_family,
            platform=gateway.platform,
            products=[
                KiwoomProductCapability(
                    product=product,
                    capability="unsupported",
                    reason=(
                        "The official Kiwoom REST product contract excludes domestic "
                        "derivatives, so gateway claims cannot promote this product."
                    ),
                )
                for product in PRODUCTS
            ],
            production_primary_enabled=False,
            production_decision="not_enabled",
            reason="Kiwoom REST does not officially support domestic futures.",
        )
    evidence_by_product: dict[str, KiwoomProductEvidence] = {}
    invalid_products: set[str] = set()
    warnings: list[str] = []
    for item in gateway.products:
        product = str(item.get("product") or "")
        try:
            evidence = KiwoomProductEvidence.model_validate(item)
        except ValidationError:
            if product in PRODUCTS:
                invalid_products.add(product)
            else:
                warnings.append("Gateway returned an unrecognized product capability row.")
            continue
        evidence_by_product[evidence.product] = evidence
    products = [
        _product_result(evidence_by_product[product])
        if product in evidence_by_product
        else KiwoomProductCapability(
            product=product,
            capability="partial",
            reason="Gateway evidence for this product failed validation.",
        )
        if product in invalid_products
        else KiwoomProductCapability(
            product=product,
            capability="unknown",
            reason="Gateway did not return evidence for this product.",
        )
        for product in PRODUCTS
    ]
    supported = [item.product for item in products if item.capability == "supported"]
    return KiwoomCapabilityProbeResult(
        status="ok",
        source=source,
        fetched_at=fetched_at,
        api_family=gateway.api_family,
        platform=gateway.platform,
        products=products,
        production_primary_enabled=False,
        production_decision="shadow_candidate" if supported else "not_enabled",
        reason=(
            "Live evidence is eligible for shadow validation only. Primary promotion requires "
            "multi-session KRX reconciliation."
            if supported
            else "No product has complete finalized night-session evidence."
        ),
        warnings=warnings,
    )


def _gateway_endpoint(gateway_url: str) -> str | None:
    value = gateway_url.strip().rstrip("/")
    parsed = urlsplit(value)
    if (
        parsed.scheme not in {"http", "https"}
        or not parsed.hostname
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
    ):
        return None
    return f"{value}{GATEWAY_CAPABILITY_PATH}"


async def fetch_gateway_capability(
    gateway_url: str | None,
    *,
    transport: httpx.AsyncBaseTransport | None = None,
    timeout_seconds: float = 10.0,
) -> KiwoomCapabilityProbeResult:
    if not gateway_url:
        result = documented_capability()
        result.status = "not_configured"
        result.source = "gateway_live"
        result.reason = "Kiwoom gateway URL is not configured."
        return result
    endpoint = _gateway_endpoint(gateway_url)
    if endpoint is None:
        result = documented_capability()
        result.status = "unavailable"
        result.source = "gateway_live"
        result.reason = "Invalid gateway URL; credentials, query strings, and fragments are forbidden."
        return result
    try:
        async with httpx.AsyncClient(
            timeout=timeout_seconds,
            transport=transport,
            headers={"User-Agent": USER_AGENT},
        ) as client:
            response = await client.get(endpoint)
            response.raise_for_status()
            payload = response.json()
    except (httpx.HTTPError, ValueError, TypeError) as exc:
        result = documented_capability()
        result.status = "unavailable"
        result.source = "gateway_live"
        result.reason = f"gateway_fetch_failed:{type(exc).__name__}"
        return result
    return parse_gateway_capability_payload(payload, source="gateway_live")


def reconcile_with_krx(
    kiwoom: KiwoomFinalNightClose,
    krx: KrxNightFutureObservation,
) -> KiwoomKrxReconciliation:
    if (
        kiwoom.product != krx.product
        or kiwoom.contract_code != krx.contract_code
        or kiwoom.contract_month != krx.maturity
        or kiwoom.session_date != krx.source_date
    ):
        return KiwoomKrxReconciliation(
            product=kiwoom.product,
            result="not_comparable",
            reason="Product, contract, maturity, and session date must all match.",
        )
    if krx.change_pct is None:
        return KiwoomKrxReconciliation(
            product=kiwoom.product,
            result="not_comparable",
            reason="KRX percent change is unavailable for full reconciliation.",
        )
    regular_close_difference = kiwoom.regular_close - krx.regular_close
    close_difference = kiwoom.night_close - krx.night_close
    point_difference = kiwoom.point_change - krx.point_change
    percent_difference = kiwoom.change_pct - krx.change_pct
    if all(
        abs(value) <= 1e-9
        for value in (
            regular_close_difference,
            close_difference,
            point_difference,
            percent_difference,
        )
    ):
        result: Literal["verified", "within_tick", "mismatch"] = "verified"
        reason = "Kiwoom and KRX final values match exactly."
    else:
        percent_tolerance = kiwoom.tick_size / kiwoom.regular_close * 100 + 1e-9
        within_tick = (
            abs(regular_close_difference) <= kiwoom.tick_size + 1e-9
            and abs(close_difference) <= kiwoom.tick_size + 1e-9
            and abs(point_difference) <= kiwoom.tick_size + 1e-9
            and abs(percent_difference) <= percent_tolerance
        )
        result = "within_tick" if within_tick else "mismatch"
        reason = (
            "Difference is within the contract tick-size tolerance."
            if within_tick
            else "Final values differ by more than the contract tick-size tolerance."
        )
    return KiwoomKrxReconciliation(
        product=kiwoom.product,
        result=result,
        regular_close_difference=round(regular_close_difference, 8),
        close_difference=round(close_difference, 8),
        point_change_difference=round(point_difference, 8),
        percent_change_difference=round(percent_difference, 8),
        reason=reason,
    )


def _report(result: KiwoomCapabilityProbeResult) -> str:
    product_lines = "\n".join(
        f"- {item.product}: `{item.capability}` - {item.reason}"
        for item in result.products
    )
    return f"""# Kiwoom Night Futures Capability Validation

## Scope

This is a capability gate, not a production-provider rollout. No account, HTS ID,
certificate, password, API secret, or token was read, stored, logged, or committed.

## Official Contract Evidence

- OpenAPI+ service: {OPENAPI_PLUS_INFO_URL}
- OpenAPI+ guide: {OPENAPI_PLUS_GUIDE_URL}
- REST service: {REST_INFO_URL}
- OpenAPI+ is a Windows OCX service. Its current public product list includes stocks,
  KOSPI200 futures, and KOSPI200 options.
- The guide exposes KOSPI200 futures discovery and generic futures realtime FIDs, but it
  does not define current KRX night-session identity, closing-auction delivery, or a safe
  final-close rule.
- Kiwoom REST currently lists domestic and US stocks, not domestic derivatives.

## Product Decision

{product_lines}

## Gateway Contract

The probe accepts one normalized, credential-free gateway response at
`{GATEWAY_CAPABILITY_PATH}`. A product is `supported` only when symbol discovery,
front-month identity, realtime subscription, explicit night-session ticks, closing-phase
ticks, final-close semantics, session identity, contract identity, and a persisted final
observation are all verified.

Architecture:

`Kiwoom OpenAPI+ Windows gateway -> normalized capability/final close -> shadow validation`

`KRX official daily data -> same-product/same-contract/same-session reconciliation`

## Production Decision

- Status: `{result.production_decision}`
- Primary enabled: `{str(result.production_primary_enabled).lower()}`
- Reason: {result.reason or 'none'}

The production provider registry and Daily Digest source priority were not changed. KRX
remains the only production night-futures source until an authenticated live probe and
multi-session shadow reconciliation succeed independently for each product.

## Remaining Live Evidence

- Actual night-session subscription and ticks
- 05:50-06:00 closing-phase delivery
- Provider-defined final close and session-final event
- Persisted close availability before 08:05 KST
- Same-contract KRX reconciliation over multiple sessions, including rollover
"""


async def main() -> None:
    parser = argparse.ArgumentParser(
        description="Probe Kiwoom night-futures capability without exposing credentials."
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--live", action="store_true")
    mode.add_argument("--fixture", type=Path)
    parser.add_argument("--gateway-url")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()

    if args.fixture:
        try:
            payload = json.loads(args.fixture.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            result = KiwoomCapabilityProbeResult(
                status="unavailable",
                source="gateway_fixture",
                fetched_at=datetime.now(timezone.utc),
                api_family="unknown",
                platform="unknown",
                production_primary_enabled=False,
                production_decision="not_enabled",
                reason="fixture_load_failed",
            )
        else:
            result = parse_gateway_capability_payload(payload)
    elif args.live:
        result = await fetch_gateway_capability(args.gateway_url)
    else:
        result = documented_capability()

    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(_report(result), encoding="utf-8")
    print(json.dumps(result.compact_summary(), ensure_ascii=False, default=str))


if __name__ == "__main__":
    asyncio.run(main())
