from datetime import date, datetime, time, timezone
from hashlib import sha256
from zoneinfo import ZoneInfo

import httpx

from app.config import get_settings
from app.macro.providers.base import CollectedObservation, MacroProviderResult
from app.services.market_session import us_market_session, is_exchange_session_date
from app.services.ohlcv_completed_bar_finality_service import (
    annotate_normalized_bar, assess_completed_bar_finality, BarFinality,
)


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


def completed_market_bars(payload, as_of):
    """Select exchange-local source rows; never shift a date to fit the cutoff."""
    completed = us_market_session(as_of).latest_completed_regular_session_date
    provider = (payload.get('meta') or {}).get('provider', '')
    normalized = []
    for raw in payload.get('periods', {}).get('daily', []):
        stamp = str(raw.get('date') or '')
        if len(stamp) == 10:
            day = date.fromisoformat(stamp)
        else:
            timestamp = datetime.fromisoformat(stamp.replace('Z', '+00:00'))
            if timestamp.tzinfo is None:
                raise ValueError('ambiguous_source_timestamp')
            day = timestamp.astimezone(ZoneInfo('America/New_York')).date()
        if not is_exchange_session_date('XNYS', day):
            continue
        normalized.append({**raw, 'date': day.isoformat()})
    if len({r['date'] for r in normalized}) != len(normalized):
        raise ValueError('duplicate_source_session')
    rows = sorted(normalized, key=lambda r: r['date'])
    eligible = []
    for index, row in enumerate(rows):
        if date.fromisoformat(row['date']) > completed:
            continue
        annotated = annotate_normalized_bar(row, provider=provider, market='US', timeframe='daily',
                                             has_later_chart_row=index < len(rows) - 1)
        finality = assess_completed_bar_finality(annotated, cutoff=completed)
        if finality.state == BarFinality.FINAL:
            eligible.append((row, finality.source))
    if len(eligible) < 2 or eligible[-1][0]['date'] != completed.isoformat():
        raise ValueError('completed_session_and_previous_close_required')
    previous, latest = eligible[-2][0], eligible[-1][0]
    prior_session = us_market_session(datetime.combine(completed, time(0), tzinfo=ZoneInfo('America/New_York'))).latest_completed_regular_session_date
    if previous['date'] != prior_session.isoformat():
        raise ValueError('previous_session_gap')
    return latest, previous, dict(contract='completed-market-session-v1',
        completed_session_date=completed.isoformat(), previous_session_date=previous['date'],
        source_provider=provider, selected_raw_date=latest['date'],
        finality_basis=eligible[-1][1], assessed_at=as_of.isoformat(),
        return_basis='adjusted_close_to_previous_completed_session', dates_relabelled=False)


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
                            "count": 3,
                            "include_indicators": "false",
                            "indicator_limit": 0,
                            "adjusted": "true",
                        },
                    )
                    response.raise_for_status()
                    latest, previous, receipt = completed_market_bars(response.json(), as_of)
                    observed_at = datetime.fromisoformat(latest['date']).replace(tzinfo=timezone.utc)
                    receipt['source_sha256'] = sha256(response.content).hexdigest()
                    receipt['series_code'] = symbol
                    result.observations.append(
                        CollectedObservation(
                            series_code=symbol,
                            category=category,
                            observed_at=observed_at,
                            value=float(latest["close"]),
                            unit="usd",
                            frequency="daily",
                            market_session="us_regular",
                            quality_status='fresh',
                            previous_value=float(previous['close']),
                            change_value=float(latest['close']) - float(previous['close']),
                            change_pct=round((float(latest['close']) / float(previous['close']) - 1) * 100, 4),
                            source_url=f"{self.settings.ohlcv_base_url.rstrip('/')}/ohlcv",
                            raw_payload={'completed_session_receipt': receipt,
                                         'selected_bar': latest, 'previous_bar': previous,
                                         'source_response': response.json()},
                        )
                    )
                except (httpx.HTTPError, KeyError, TypeError, ValueError) as exc:
                    result.warnings.append(f"{symbol}: {type(exc).__name__}")
        return result
