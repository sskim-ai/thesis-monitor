from datetime import datetime, timezone
import hashlib
from pathlib import Path

import httpx
from pydantic import TypeAdapter

from app.config import get_settings
from app.macro.providers.base import CollectedObservation, MacroProviderResult
from app.services.unified_source_observer import OhlcvReceiptObserver
from app.services.market_session import us_market_session


MARKET_SYMBOLS = {
    "SPY": "market_index",
    "QQQ": "market_index",
    "IWM": "market_index",
    "RSP": "style_size",
    "SOXX": "sector",
    "XLB": "sector",
    "XLC": "sector",
    "XLF": "sector",
    "XLE": "sector",
    "XLI": "sector",
    "XLK": "sector",
    "XLP": "sector",
    "XLRE": "sector",
    "XLU": "sector",
    "XLV": "sector",
    "XLY": "sector",
    "NVDA": "big_tech",
    "MSFT": "big_tech",
    "AAPL": "big_tech",
    "GOOGL": "big_tech",
    "AMZN": "big_tech",
    "META": "big_tech",
}


class OhlcvMarketProvider:
    name = "ohlcv_analyst"

    def __init__(self, transport: httpx.AsyncBaseTransport | None = None, *,
                 source_observer: OhlcvReceiptObserver | None = None) -> None:
        self.settings = get_settings()
        self.transport = transport
        self.source_observer = source_observer

    async def collect(self, as_of: datetime) -> MacroProviderResult:
        result = MacroProviderResult(provider=self.name)
        if self.source_observer is not None:
            self.source_observer.require_market_set(set(MARKET_SYMBOLS))
            if as_of.utcoffset() is None or self.source_observer.reads[0].session_date != (
                us_market_session(as_of).latest_completed_regular_session_date
            ):
                raise ValueError("market_plan_session_mismatch")
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
                    get = client.get if self.source_observer is None else (
                        lambda route, **kwargs: self.source_observer.get(client, route, **kwargs)
                    )
                    response = await get(
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
                    observation = CollectedObservation(
                            series_code=symbol,
                            category=category,
                            observed_at=observed_at,
                            value=float(latest["close"]),
                            unit="usd",
                            frequency="daily",
                            market_session="us_regular",
                            source_url=f"{self.settings.ohlcv_base_url.rstrip('/')}/ohlcv",
                    )
                    if self.source_observer is not None:
                        read = next(r for r in self.source_observer.reads if r.symbol == symbol)
                        if observed_at.date() != read.session_date or observed_at > as_of:
                            raise ValueError("market_source_session_mismatch")
                        normalized = TypeAdapter(CollectedObservation).dump_python(
                            observation, mode="json")
                        self.source_observer.normalized(response, normalized=normalized,
                            contract="us-market-observation-session-v1", valid=True,
                            fingerprint=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
                    result.observations.append(observation)
                except (httpx.HTTPError, KeyError, TypeError, ValueError) as exc:
                    result.warnings.append(f"{symbol}: {type(exc).__name__}")
        return result
