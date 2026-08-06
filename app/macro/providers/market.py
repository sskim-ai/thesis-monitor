from datetime import datetime, timezone

import httpx

from app.config import get_settings
from app.macro.providers.base import CollectedObservation, MacroProviderResult


MARKET_SYMBOLS = {
    "SPY": "market_index",
    "QQQ": "market_index",
    "IWM": "market_index",
    "SOXX": "sector",
    "XLF": "sector",
    "XLE": "sector",
    "NVDA": "big_tech",
    "MSFT": "big_tech",
    "AAPL": "big_tech",
    "GOOGL": "big_tech",
    "AMZN": "big_tech",
    "META": "big_tech",
}


class OhlcvMarketProvider:
    name = "ohlcv_analyst"

    def __init__(self, transport: httpx.AsyncBaseTransport | None = None) -> None:
        self.settings = get_settings()
        self.transport = transport

    async def collect(self, as_of: datetime) -> MacroProviderResult:
        result = MacroProviderResult(provider=self.name)
        api_key = self.settings.ohlcv_api_key or self.settings.action_api_key
        headers = {"X-API-Key": api_key} if api_key else {}
        async with httpx.AsyncClient(
            base_url=self.settings.ohlcv_base_url.rstrip("/"),
            headers=headers,
            timeout=self.settings.ohlcv_timeout_seconds,
            transport=self.transport,
        ) as client:
            for symbol, category in MARKET_SYMBOLS.items():
                try:
                    response = await client.get(
                        "/ohlcv",
                        params={
                            "symbol": symbol,
                            "market": "US",
                            "periods": "daily",
                            "count": 2,
                            "include_indicators": "false",
                            "indicator_limit": 0,
                            "adjusted": "true",
                        },
                    )
                    response.raise_for_status()
                    bars = response.json().get("periods", {}).get("daily", [])
                    if not bars:
                        result.warnings.append(f"{symbol}: no daily bars")
                        continue
                    latest = bars[-1]
                    observed_at = datetime.fromisoformat(str(latest["date"])).replace(
                        tzinfo=timezone.utc
                    )
                    result.observations.append(
                        CollectedObservation(
                            series_code=symbol,
                            category=category,
                            observed_at=observed_at,
                            value=float(latest["close"]),
                            unit="usd",
                            frequency="daily",
                            market_session="us_regular",
                            source_url=f"{self.settings.ohlcv_base_url.rstrip('/')}/ohlcv",
                        )
                    )
                except (httpx.HTTPError, KeyError, TypeError, ValueError) as exc:
                    result.warnings.append(f"{symbol}: {type(exc).__name__}")
        return result
