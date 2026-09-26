from datetime import datetime, timedelta, timezone
import hashlib
from pathlib import Path

import httpx
from pydantic import TypeAdapter

from app.config import get_settings
from app.macro.providers.base import CollectedEvent, MacroProviderResult
from app.services.unified_run_acquisition import RunAcquisitionObserver


BIG_TECH = {"NVDA", "MSFT", "AAPL", "GOOGL", "AMZN", "META", "TSLA", "AVGO", "TSM"}


class FinnhubEarningsProvider:
    name = "finnhub_earnings"

    def __init__(self, transport: httpx.AsyncBaseTransport | None = None, *,
                 source_observer: RunAcquisitionObserver | None = None) -> None:
        self.settings = get_settings()
        self.transport = transport
        self.source_observer = source_observer

    async def collect(self, as_of: datetime) -> MacroProviderResult:
        if self.source_observer is not None:
            self.source_observer.begin(provider=self.name, role="earnings_calendar")
        try:
            result = await self._collect(as_of)
        except Exception as exc:
            if self.source_observer is not None:
                self._finish_receipt(None, type(exc).__name__)
            raise
        if self.source_observer is not None:
            self._finish_receipt(result, "owner_unavailable" if result.warnings else None)
        return result

    def _finish_receipt(self, result, denial):
        self.source_observer.finish(normalized=(
            TypeAdapter(MacroProviderResult).dump_python(result, mode="json") if result else None),
            contract="finnhub-earnings-calendar-owner-v1", denial=denial,
            fingerprint=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())

    async def _collect(self, as_of: datetime) -> MacroProviderResult:
        result = MacroProviderResult(provider=self.name)
        if not self.settings.finnhub_api_key:
            result.warnings.append("FINNHUB_API_KEY is not configured")
            return result
        start = as_of.date() - timedelta(days=1)
        end = as_of.date() + timedelta(days=2)
        try:
            async with httpx.AsyncClient(
                base_url="https://finnhub.io",
                timeout=self.settings.macro_provider_timeout_seconds,
                transport=self.transport,
            ) as client:
                params = {"from": start.isoformat(), "to": end.isoformat()}
                if self.source_observer is None:
                    response = await client.get("/api/v1/calendar/earnings",
                        params={**params, "token": self.settings.finnhub_api_key})
                else:
                    response = await self.source_observer.get(client, "/api/v1/calendar/earnings",
                        params=params, credential_params={"token": self.settings.finnhub_api_key})
                response.raise_for_status()
            rows = response.json().get("earningsCalendar", [])
            for row in rows:
                symbol = str(row.get("symbol", "")).upper()
                if symbol not in BIG_TECH:
                    continue
                event_date = datetime.fromisoformat(str(row["date"])).replace(
                    tzinfo=timezone.utc
                )
                actual = row.get("epsActual")
                estimate = row.get("epsEstimate")
                released = actual is not None
                result.events.append(
                    CollectedEvent(
                        event_key=f"earnings:{symbol}:{row['date']}:{row.get('quarter')}",
                        event_type="earnings",
                        category="big_tech_earnings",
                        title=f"{symbol} quarterly earnings",
                        country="US",
                        region="US",
                        scheduled_at=event_date,
                        released_at=event_date if released else None,
                        event_status="released" if released else "scheduled",
                        actual=float(actual) if actual is not None else None,
                        consensus=float(estimate) if estimate is not None else None,
                        unit="eps",
                        impact_level=4,
                        confirmed_facts=(
                            [f"EPS actual {actual}, estimate {estimate}"] if released else []
                        ),
                        unknowns=[] if released else ["Earnings have not been released"],
                        source_url="https://finnhub.io/docs/api/earnings-calendar",
                        source_reliability=0.8,
                    )
                )
        except (httpx.HTTPError, KeyError, TypeError, ValueError) as exc:
            result.warnings.append(f"earnings calendar: {type(exc).__name__}")
        return result
