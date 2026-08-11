import json

import httpx
from sqlmodel import Session

from app.config import get_settings
from app.models.security import SecurityMaster


class OpenFigiProvider:
    name = "openfigi"
    endpoint = "https://api.openfigi.com/v3/mapping"

    def __init__(self, transport: httpx.AsyncBaseTransport | None = None) -> None:
        self.settings = get_settings()
        self.transport = transport

    async def enrich(
        self, session: Session, security: SecurityMaster
    ) -> tuple[bool, str]:
        request: dict[str, str] = {"idType": "TICKER", "idValue": security.ticker}
        if security.exchange and not security.ticker.isdigit():
            request["exchCode"] = security.exchange.upper()
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
                return False, "mapping_not_found"
            match = matches[0]
            security.figi = str(match.get("figi") or "") or security.figi
            security.security_type = str(match.get("securityType2") or match.get("securityType") or security.security_type)
            security.share_class = str(match.get("securityDescription") or "") or security.share_class
            security.identity_provider = "local+openfigi"
            security.identity_quality = "full" if security.figi else security.identity_quality
            aliases = json.loads(security.aliases or "[]")
            name = str(match.get("name") or "").strip().lower()
            if name and name not in aliases:
                aliases.append(name)
                security.aliases = json.dumps(aliases)
            session.add(security)
            session.flush()
            return True, "mapped"
        except (httpx.HTTPError, ValueError, TypeError, KeyError, IndexError) as exc:
            return False, type(exc).__name__
