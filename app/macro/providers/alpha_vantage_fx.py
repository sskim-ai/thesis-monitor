import asyncio
from datetime import datetime, timezone
import math
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import httpx

from app.config import get_settings
from app.macro.providers.base import CollectedObservation, MacroProviderResult
from app.services.alpha_vantage_service import alpha_vantage_error_reason


ALPHA_VANTAGE_QUERY_URL = "https://www.alphavantage.co/query"
ALPHA_VANTAGE_SOURCE_URL = "https://www.alphavantage.co/"
EXCHANGE_RATE_KEY = "Realtime Currency Exchange Rate"
PAIRS = (
    ("USD", "USDKRW_KR_CLOSE", 1.0, "KRW per USD"),
    ("JPY", "JPYKRW100_KR_CLOSE", 100.0, "KRW per 100 JPY"),
    ("EUR", "EURKRW_KR_CLOSE", 1.0, "KRW per EUR"),
)


def _field(payload: dict[str, object], suffix: str) -> object | None:
    return next((value for key, value in payload.items() if key.endswith(suffix)), None)


def _number(value: object) -> float | None:
    try:
        number = float(str(value).replace(",", "").strip())
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _provider_timestamp(value: object, timezone_name: object) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    zone_name = str(timezone_name or "UTC").strip() or "UTC"
    try:
        zone = ZoneInfo(zone_name)
    except ZoneInfoNotFoundError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=zone)
    return parsed.astimezone(timezone.utc)


class AlphaVantageKrCloseFxProvider:
    name = "alpha_vantage_fx_close"

    def __init__(
        self,
        transport: httpx.AsyncBaseTransport | None = None,
        request_interval_seconds: float = 12.1,
    ) -> None:
        self.settings = get_settings()
        self.transport = transport
        self.request_interval_seconds = max(0.0, request_interval_seconds)

    async def collect(self, as_of: datetime) -> MacroProviderResult:
        if not self.settings.alpha_vantage_api_key:
            return MacroProviderResult(
                provider=self.name,
                warnings=["api_key_not_configured"],
            )
        observations: list[CollectedObservation] = []
        warnings: list[str] = []
        async with httpx.AsyncClient(
            timeout=self.settings.macro_provider_timeout_seconds,
            transport=self.transport,
        ) as client:
            for index, (from_currency, series_code, scale, unit) in enumerate(PAIRS):
                if index and self.request_interval_seconds:
                    await asyncio.sleep(self.request_interval_seconds)
                try:
                    response = await client.get(
                        ALPHA_VANTAGE_QUERY_URL,
                        params={
                            "function": "CURRENCY_EXCHANGE_RATE",
                            "from_currency": from_currency,
                            "to_currency": "KRW",
                            "apikey": self.settings.alpha_vantage_api_key,
                        },
                    )
                    response.raise_for_status()
                    payload = response.json()
                except (httpx.HTTPError, ValueError, TypeError) as exc:
                    warnings.append(f"{from_currency}/KRW:{type(exc).__name__}")
                    continue
                if not isinstance(payload, dict):
                    warnings.append(f"{from_currency}/KRW:invalid_response_schema")
                    continue
                reason = alpha_vantage_error_reason(payload)
                if reason:
                    warnings.append(f"{from_currency}/KRW:{reason}")
                    continue
                quote = payload.get(EXCHANGE_RATE_KEY)
                if not isinstance(quote, dict):
                    warnings.append(f"{from_currency}/KRW:missing_exchange_rate")
                    continue
                raw_rate = _number(_field(quote, "Exchange Rate"))
                last_refreshed = _field(quote, "Last Refreshed")
                provider_timezone = _field(quote, "Time Zone")
                observed_at = _provider_timestamp(last_refreshed, provider_timezone)
                if raw_rate is None or observed_at is None:
                    warnings.append(f"{from_currency}/KRW:invalid_exchange_rate")
                    continue
                observations.append(
                    CollectedObservation(
                        series_code=series_code,
                        category="fx_close",
                        observed_at=observed_at,
                        value=raw_rate * scale,
                        unit=unit,
                        frequency="daily",
                        market_session="kr_close",
                        source_url=ALPHA_VANTAGE_SOURCE_URL,
                        raw_payload={
                            "provider_last_refreshed": str(last_refreshed),
                            "provider_timezone": str(provider_timezone),
                            "retrieved_at": as_of.isoformat(),
                            "from_currency": from_currency,
                            "to_currency": "KRW",
                            "raw_rate": raw_rate,
                            "scale": scale,
                        },
                    )
                )
        return MacroProviderResult(
            provider=self.name,
            observations=observations,
            warnings=warnings,
        )
