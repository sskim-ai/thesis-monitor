import json
from datetime import datetime, timezone

import httpx
from sqlmodel import Session, select

from app.config import get_settings
from app.models.security import ProviderResponseCache, SecurityMaster
from app.services.provider_telemetry_service import ProviderTelemetryService
from app.services.security_identity_service import (
    TIER_A_AUTHORITATIVE,
    TIER_D_INFERRED_DEFAULT,
    identity_source_tier,
)


OPENFIGI_CANONICALIZATION_VERSION = "openfigi-candidate-selection-v2"

_EXCHANGE_IDENTITIES = {
    "NASDAQ": {"NASDAQ", "XNAS", "NAS", "NGS", "NMS", "UW", "UQ"},
    "NYSE": {"NYSE", "XNYS", "UN"},
    "AMEX": {"AMEX", "XASE", "UA"},
}


def _normalized(value: object) -> str:
    return " ".join(str(value or "").strip().upper().split())


def _normalized_security_type(value: object) -> str:
    normalized = _normalized(value).replace("-", "_").replace(" ", "_")
    if normalized in {
        "ADR",
        "ADS",
        "DEPOSITARY_RECEIPT",
        "AMERICAN_DEPOSITARY_RECEIPT",
        "AMERICAN_DEPOSITARY_SHARE",
    }:
        return "ads"
    if normalized in {"COMMON_STOCK", "COMMON_SHARE", "COMMON", "COMMON_SHARES"}:
        return "common_stock"
    return normalized.lower()


def _candidate_identity(item: dict[str, object]) -> dict[str, object]:
    return {
        "ticker": _normalized(item.get("ticker")),
        "name": _normalized(item.get("name")),
        "exchange_codes": sorted(
            {
                value
                for value in (
                    _normalized(item.get("exchCode")),
                    _normalized(item.get("micCode")),
                    _normalized(item.get("exchangeCode")),
                )
                if value
            }
        ),
        "share_class": _normalized(
            item.get("shareClass") or item.get("securityDescription")
        ),
        "market_sector": _normalized(item.get("marketSector")),
        "security_type": _normalized_security_type(
            item.get("securityType2") or item.get("securityType")
        ),
        "figi": str(item.get("figi") or ""),
        "composite_figi": str(item.get("compositeFIGI") or ""),
        "share_class_figi": str(item.get("shareClassFIGI") or ""),
    }


def canonicalize_openfigi_candidates(
    security: SecurityMaster,
    candidates: list[dict[str, object]],
) -> dict[str, object]:
    aliases = json.loads(security.aliases or "[]")
    identity_terms = {
        _normalized(security.company_name),
        _normalized(security.legal_name),
        *(_normalized(alias) for alias in aliases),
    }
    identity_terms.discard("")
    expected_exchange = _normalized(security.exchange)
    accepted_exchange_codes = _EXCHANGE_IDENTITIES.get(
        expected_exchange, {expected_exchange}
    )
    audited: list[dict[str, object]] = []
    eligible: list[tuple[int, str, dict[str, object]]] = []

    for item in candidates:
        identity = _candidate_identity(item)
        reasons: list[str] = []
        score = 0
        if identity["ticker"] != security.ticker.upper():
            reasons.append("ticker_mismatch")
        else:
            score += 100
        provider_name = str(identity["name"])
        if not any(
            term and (term in provider_name or provider_name in term)
            for term in identity_terms
        ):
            reasons.append("issuer_name_mismatch")
        else:
            score += 40
        candidate_exchanges = set(identity["exchange_codes"])
        if expected_exchange:
            if not candidate_exchanges:
                reasons.append("exchange_identity_missing")
            elif not candidate_exchanges.intersection(accepted_exchange_codes):
                reasons.append("exchange_mismatch")
            else:
                score += 30
        if security.share_class:
            expected_class = _normalized(security.share_class)
            candidate_class = str(identity["share_class"])
            if candidate_class and expected_class in candidate_class:
                score += 20
            elif (
                candidate_class
                and identity_source_tier(
                    security.identity_provider, security.identity_quality
                )
                != TIER_D_INFERRED_DEFAULT
            ):
                reasons.append("share_class_mismatch")
        if identity["security_type"] in {"common_stock", "ads"}:
            score += 10
        else:
            reasons.append("security_type_missing_or_unsupported")
        if identity["market_sector"]:
            if identity["market_sector"] != "EQUITY":
                reasons.append("market_sector_mismatch")
            else:
                score += 5
        stable_id = "|".join(
            str(identity[key])
            for key in ("figi", "composite_figi", "share_class_figi", "security_type")
        )
        accepted = not reasons
        audit = {
            "identity": identity,
            "accepted": accepted,
            "score": score,
            "rejection_reasons": reasons,
            "raw_candidate": item,
        }
        audited.append(audit)
        if accepted:
            eligible.append((score, stable_id, item))

    eligible.sort(key=lambda value: (-value[0], value[1]))
    selected: dict[str, object] | None = None
    status = "not_found"
    reason = "no_exact_instrument_match"
    if eligible:
        top_score = eligible[0][0]
        top = [item for item in eligible if item[0] == top_score]
        if len(top) == 1:
            selected = top[0][2]
            status = "selected"
            reason = "unique_exact_instrument_match"
        else:
            status = "ambiguous"
            reason = "multiple_equal_exact_instrument_matches"
    return {
        "decision_version": OPENFIGI_CANONICALIZATION_VERSION,
        "status": status,
        "reason": reason,
        "selected": selected,
        "candidate_audit": sorted(
            audited,
            key=lambda value: json.dumps(
                value["identity"], sort_keys=True, ensure_ascii=True
            ),
        ),
    }


class OpenFigiProvider:
    name = "openfigi"
    endpoint = "https://api.openfigi.com/v3/mapping"

    def __init__(self, transport: httpx.AsyncBaseTransport | None = None) -> None:
        self.settings = get_settings()
        self.transport = transport
        self.telemetry = ProviderTelemetryService()

    async def enrich(
        self, session: Session, security: SecurityMaster
    ) -> tuple[bool, str]:
        started_at = datetime.now(timezone.utc)
        request: dict[str, str] = {"idType": "TICKER", "idValue": security.ticker}
        headers = {"Content-Type": "application/json"}
        if self.settings.openfigi_api_key:
            headers["X-OPENFIGI-APIKEY"] = self.settings.openfigi_api_key
        try:
            async with httpx.AsyncClient(
                timeout=self.settings.valuation_provider_timeout_seconds,
                transport=self.transport,
            ) as client:
                response = await client.post(
                    self.endpoint, headers=headers, json=[request]
                )
                response.raise_for_status()
                payload = response.json()
            data = payload[0].get("data", []) if isinstance(payload, list) and payload else []
            matches = [item for item in data if isinstance(item, dict)]
            if not matches:
                self._cache(session, security.ticker, "mapping_not_found", {})
                self.telemetry.record(
                    session,
                    provider=self.name,
                    endpoint="mapping",
                    ticker=security.ticker,
                    started_at=started_at,
                    status="partial",
                    error_type="MappingNotFound",
                    error_reason="no_matching_instrument",
                )
                return False, "mapping_not_found"
            resolution = canonicalize_openfigi_candidates(security, matches)
            match = resolution.get("selected")
            if not isinstance(match, dict):
                self._cache(
                    session,
                    security.ticker,
                    str(resolution["status"]),
                    {
                        "request": request,
                        "resolution": resolution,
                    },
                )
                self.telemetry.record(
                    session,
                    provider=self.name,
                    endpoint="mapping",
                    ticker=security.ticker,
                    started_at=started_at,
                    status="partial",
                    error_type="IdentityAmbiguous",
                    error_reason=str(resolution["reason"]),
                )
                return False, str(resolution["reason"])
            if (
                identity_source_tier(
                    security.identity_provider, security.identity_quality
                )
                == TIER_A_AUTHORITATIVE
            ):
                self._cache(
                    session,
                    security.ticker,
                    "audit_only",
                    {
                        "request": request,
                        "resolution": resolution,
                        "write_decision": "authoritative_identity_preserved",
                    },
                )
                self.telemetry.record(
                    session,
                    provider=self.name,
                    endpoint="mapping",
                    ticker=security.ticker,
                    started_at=started_at,
                    status="success",
                )
                return False, "authoritative_identity_preserved"
            security.figi = str(match.get("figi") or "") or security.figi
            security.security_type = _normalized_security_type(
                match.get("securityType2") or match.get("securityType")
            ) or security.security_type
            security.share_class = str(match.get("securityDescription") or "") or security.share_class
            if security.security_type == "ads":
                security.issuer_type = "adr"
                security.adr_identifier = security.ticker
            else:
                security.issuer_type = "domestic_us" if security.country == "US" else security.issuer_type
                security.adr_identifier = None
                security.ordinary_share_identifier = None
                security.adr_ratio = None
                security.adr_ratio_source = None
                security.adr_ratio_as_of = None
            security.identity_provider = "openfigi_deterministic_match"
            security.identity_quality = "verified"
            aliases = json.loads(security.aliases or "[]")
            name = str(match.get("name") or "").strip().lower()
            if name and name not in aliases:
                aliases.append(name)
                security.aliases = json.dumps(aliases)
            session.add(security)
            session.flush()
            self._cache(
                session,
                security.ticker,
                "success",
                {
                    "request": request,
                    "resolution": resolution,
                    "write_decision": "deterministic_reference_identity_applied",
                },
            )
            self.telemetry.record(
                session,
                provider=self.name,
                endpoint="mapping",
                ticker=security.ticker,
                started_at=started_at,
                status="success",
            )
            return True, "mapped"
        except (httpx.HTTPError, ValueError, TypeError, KeyError, IndexError) as exc:
            status_code = (
                str(exc.response.status_code)
                if isinstance(exc, httpx.HTTPStatusError)
                else None
            )
            self.telemetry.record(
                session,
                provider=self.name,
                endpoint="mapping",
                ticker=security.ticker,
                started_at=started_at,
                status="failed",
                error_type=type(exc).__name__,
                error_code=status_code,
                error_reason="mapping_request_failed",
            )
            return False, type(exc).__name__

    def _cache(
        self,
        session: Session,
        ticker: str,
        status: str,
        payload: dict[str, object],
    ) -> None:
        now = datetime.now(timezone.utc)
        row = session.exec(
            select(ProviderResponseCache).where(
                ProviderResponseCache.provider == self.name,
                ProviderResponseCache.ticker == ticker,
                ProviderResponseCache.data_type == "mapping",
            )
        ).first() or ProviderResponseCache(
            provider=self.name,
            ticker=ticker,
            data_type="mapping",
        )
        row.status = status
        row.payload = json.dumps(payload)
        row.fetched_at = now
        row.last_success_at = now if status == "success" else row.last_success_at
        row.last_error = None if status == "success" else status
        session.add(row)
