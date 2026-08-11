import json
from datetime import datetime, timezone

import httpx
from sqlmodel import Session, select

from app.config import get_settings
from app.models.security import ProviderResponseCache, SecurityMaster
from app.services.provider_telemetry_service import ProviderTelemetryService


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
            exact_ticker = [
                item
                for item in matches
                if str(item.get("ticker", "")).upper() == security.ticker
            ]
            aliases = json.loads(security.aliases or "[]")
            identity_terms = {
                security.company_name.lower(),
                security.legal_name.lower() if security.legal_name else "",
                *(str(alias).lower() for alias in aliases),
            }
            candidate_matches = exact_ticker or matches
            match = next(
                (
                    item
                    for item in candidate_matches
                    if any(
                        term
                        and (
                            term in str(item.get("name") or "").strip().lower()
                            or str(item.get("name") or "").strip().lower() in term
                        )
                        for term in identity_terms
                    )
                ),
                candidate_matches[0],
            )
            provider_name = str(match.get("name") or "").strip().lower()
            name_matches = any(
                term and (term in provider_name or provider_name in term)
                for term in identity_terms
            )
            ticker_matches = str(match.get("ticker", "")).upper() == security.ticker
            if not ticker_matches or not name_matches:
                warnings = json.loads(security.identity_warnings or "[]")
                warning = "OpenFIGI mapping과 기존 Security Master 회사 식별자가 일치하지 않습니다."
                if warning not in warnings:
                    warnings.append(warning)
                security.identity_warnings = json.dumps(warnings, ensure_ascii=False)
                session.add(security)
                self._cache(session, security.ticker, "mismatch", match)
                self.telemetry.record(
                    session,
                    provider=self.name,
                    endpoint="mapping",
                    ticker=security.ticker,
                    started_at=started_at,
                    status="partial",
                    error_type="IdentityMismatch",
                    error_reason="security_master_mismatch",
                )
                return False, "identity_mismatch"
            security.figi = str(match.get("figi") or "") or security.figi
            security.security_type = str(match.get("securityType2") or match.get("securityType") or security.security_type)
            security.share_class = str(match.get("securityDescription") or "") or security.share_class
            security.identity_provider = "local+openfigi"
            security.identity_quality = "full" if security.figi else security.identity_quality
            name = str(match.get("name") or "").strip().lower()
            if name and name not in aliases:
                aliases.append(name)
                security.aliases = json.dumps(aliases)
            session.add(security)
            session.flush()
            self._cache(session, security.ticker, "success", match)
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
