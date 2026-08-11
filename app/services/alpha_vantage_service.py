import json
import math
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone

import httpx
from sqlmodel import Session, select

from app.config import get_settings
from app.models.financial import DividendHistory
from app.models.security import (
    ConsensusEstimate,
    ProviderResponseCache,
    ShareCountObservation,
)
from app.services.provider_telemetry_service import ProviderTelemetryService


def _number(value: object) -> float | None:
    try:
        number = float(str(value).replace(",", ""))
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _integer(value: object) -> int | None:
    number = _number(value)
    return int(number) if number is not None else None


def _date(value: object) -> date | None:
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError:
        return None


def _first_list(payload: dict[str, object], *keys: str) -> list[dict[str, object]]:
    for key in keys:
        value = payload.get(key)
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]
    return []


def _provider_error_reason(payload: dict[str, object]) -> str | None:
    message = str(
        payload.get("Error Message")
        or payload.get("Note")
        or payload.get("Information")
        or ""
    ).lower()
    if not message:
        return "empty_payload" if not payload else None
    if "frequency" in message or "rate limit" in message or "call volume" in message:
        return "rate_limit"
    if "api key" in message or "apikey" in message:
        return "authentication_failed"
    if "symbol" in message or "invalid" in message:
        return "unsupported_symbol"
    return "provider_error_message"


@dataclass
class AlphaVantageBundle:
    ticker: str
    payloads: dict[str, dict[str, object]] = field(default_factory=dict)
    statuses: dict[str, str] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)


class AlphaVantageService:
    _request_count = 0
    _request_date: date | None = None
    base_url = "https://www.alphavantage.co/query"

    def __init__(self, transport: httpx.AsyncBaseTransport | None = None) -> None:
        self.settings = get_settings()
        self.transport = transport
        self.telemetry = ProviderTelemetryService()

    def _cached(
        self, session: Session, ticker: str, data_type: str
    ) -> ProviderResponseCache | None:
        row = session.exec(
            select(ProviderResponseCache).where(
                ProviderResponseCache.provider == "alpha_vantage",
                ProviderResponseCache.ticker == ticker,
                ProviderResponseCache.data_type == data_type,
            )
        ).first()
        if row and row.status == "success" and row.expires_at:
            expires = row.expires_at
            if expires.tzinfo is None:
                expires = expires.replace(tzinfo=timezone.utc)
            if expires > datetime.now(timezone.utc):
                return row
        return None

    async def _fetch(
        self, session: Session, ticker: str, function: str
    ) -> tuple[dict[str, object], str]:
        started_at = datetime.now(timezone.utc)
        cached = self._cached(session, ticker, function)
        if cached:
            try:
                payload = json.loads(cached.payload)
            except json.JSONDecodeError:
                payload = {}
            self.telemetry.record(
                session,
                provider="alpha_vantage",
                endpoint=function,
                ticker=ticker,
                started_at=started_at,
                status="cache_hit",
            )
            return (payload if isinstance(payload, dict) else {}), "cached"
        if not self.settings.alpha_vantage_api_key:
            self.telemetry.record(
                session,
                provider="alpha_vantage",
                endpoint=function,
                ticker=ticker,
                started_at=started_at,
                status="skipped_not_configured",
                skip_reason="api_key_not_configured",
            )
            return {}, "skipped_not_configured"
        today = datetime.now(timezone.utc).date()
        if self.__class__._request_date != today:
            self.__class__._request_date = today
            self.__class__._request_count = 0
        if self.__class__._request_count >= self.settings.alpha_vantage_request_budget:
            self.telemetry.record(
                session,
                provider="alpha_vantage",
                endpoint=function,
                ticker=ticker,
                started_at=started_at,
                status="skipped_budget_exhausted",
                skip_reason="configured_daily_request_budget_exhausted",
            )
            return {}, "skipped_budget_exhausted"
        self.__class__._request_count += 1
        now = datetime.now(timezone.utc)
        row = session.exec(
            select(ProviderResponseCache).where(
                ProviderResponseCache.provider == "alpha_vantage",
                ProviderResponseCache.ticker == ticker,
                ProviderResponseCache.data_type == function,
            )
        ).first() or ProviderResponseCache(
            provider="alpha_vantage", ticker=ticker, data_type=function
        )
        caught_exc: Exception | None = None
        failure_reason: str | None = None
        try:
            async with httpx.AsyncClient(
                timeout=self.settings.valuation_provider_timeout_seconds,
                transport=self.transport,
            ) as client:
                response = await client.get(
                    self.base_url,
                    params={
                        "function": function,
                        "symbol": ticker,
                        "apikey": self.settings.alpha_vantage_api_key,
                    },
                )
                response.raise_for_status()
                payload = response.json()
            if not isinstance(payload, dict):
                failure_reason = "invalid_response_schema"
                raise ValueError(failure_reason)
            failure_reason = _provider_error_reason(payload)
            if failure_reason:
                raise ValueError(failure_reason)
            row.status = "success"
            row.payload = json.dumps(payload)
            row.last_success_at = now
            row.last_error = None
            status = "fresh"
        except (httpx.HTTPError, ValueError, TypeError) as exc:
            caught_exc = exc
            if failure_reason is None:
                failure_reason = (
                    "http_status_error"
                    if isinstance(exc, httpx.HTTPStatusError)
                    else "network_error"
                    if isinstance(exc, httpx.HTTPError)
                    else "parse_error"
                )
            payload = {}
            row.status = "failed"
            row.payload = "{}"
            row.last_error = type(exc).__name__
            status = "rate_limited" if failure_reason == "rate_limit" else "provider_failed"
        row.fetched_at = now
        row.expires_at = now + timedelta(hours=self.settings.alpha_vantage_cache_hours)
        session.add(row)
        session.flush()
        status_code = (
            str(caught_exc.response.status_code)
            if isinstance(caught_exc, httpx.HTTPStatusError)
            else None
        )
        self.telemetry.record(
            session,
            provider="alpha_vantage",
            endpoint=function,
            ticker=ticker,
            started_at=started_at,
            status="success" if status == "fresh" else status,
            error_type=row.last_error,
            error_code=status_code,
            error_reason=(failure_reason if status != "fresh" else None),
        )
        return payload, status

    async def collect(
        self,
        session: Session,
        ticker: str,
        functions: tuple[str, ...] = (
            "EARNINGS_ESTIMATES",
            "SHARES_OUTSTANDING",
            "DIVIDENDS",
            "SPLITS",
            "OVERVIEW",
        ),
    ) -> AlphaVantageBundle:
        result = AlphaVantageBundle(ticker=ticker)
        for function in functions:
            payload, status = await self._fetch(session, ticker, function)
            result.payloads[function] = payload
            result.statuses[function] = status
            if status in {"provider_failed", "rate_limited"}:
                result.warnings.append(f"{function}:{status}")
        self._store_estimates(session, ticker, result.payloads.get("EARNINGS_ESTIMATES", {}))
        self._store_shares(session, ticker, result.payloads.get("SHARES_OUTSTANDING", {}))
        self._store_dividends(session, ticker, result.payloads.get("DIVIDENDS", {}))
        session.flush()
        return result

    def _store_estimates(
        self, session: Session, ticker: str, payload: dict[str, object]
    ) -> None:
        rows = _first_list(
            payload,
            "annualEarningsEstimates",
            "annual_earnings_estimates",
            "annualEstimates",
            "estimates",
        )
        annual_rows = [
            item
            for item in rows
            if str(item.get("horizon", "fiscal year")).lower() == "fiscal year"
        ]
        for item in annual_rows[:3]:
            period = str(
                item.get("fiscalDateEnding")
                or item.get("fiscal_date_ending")
                or item.get("date")
                or "FY1"
            )
            as_of = datetime.now(timezone.utc)
            existing = session.exec(
                select(ConsensusEstimate).where(
                    ConsensusEstimate.ticker == ticker,
                    ConsensusEstimate.provider == "alpha_vantage",
                    ConsensusEstimate.estimate_period == period,
                )
            ).first()
            row = existing or ConsensusEstimate(
                ticker=ticker,
                provider="alpha_vantage",
                estimate_as_of=as_of,
                estimate_period=period,
            )
            row.estimate_as_of = as_of
            row.metric = "eps"
            row.basis = "FY1"
            row.estimate_mean = _number(
                item.get("estimatedEPS")
                or item.get("estimated_eps")
                or item.get("estimateMean")
                or item.get("eps_estimate_average")
            )
            row.value = row.estimate_mean
            row.estimate_high = _number(
                item.get("estimatedEPSHigh")
                or item.get("estimateHigh")
                or item.get("eps_estimate_high")
            )
            row.estimate_low = _number(
                item.get("estimatedEPSLow")
                or item.get("estimateLow")
                or item.get("eps_estimate_low")
            )
            row.revenue_estimate_mean = _number(
                item.get("estimatedRevenue")
                or item.get("revenueEstimateMean")
                or item.get("revenue_estimate_average")
            )
            row.analyst_count = _integer(
                item.get("numberOfAnalysts")
                or item.get("analystCount")
                or item.get("eps_estimate_analyst_count")
            )
            revisions_up = _integer(
                item.get("eps_estimate_revision_up_trailing_30_days")
            ) or 0
            revisions_down = _integer(
                item.get("eps_estimate_revision_down_trailing_30_days")
            ) or 0
            row.revision_count = revisions_up + revisions_down
            row.revision_direction = (
                "up" if revisions_up > revisions_down else "down" if revisions_down > revisions_up else "unchanged"
            )
            row.quality = "fresh" if row.estimate_mean is not None else "partial"
            row.coverage_status = (
                "full"
                if row.estimate_mean is not None
                and row.analyst_count is not None
                and period != "FY1"
                else "partial"
                if row.estimate_mean is not None
                else "unavailable"
            )
            row.raw_reference = str(item.get("horizon") or "fiscal year")
            session.add(row)

    def _store_shares(
        self, session: Session, ticker: str, payload: dict[str, object]
    ) -> None:
        rows = _first_list(payload, "annualReports", "quarterlyReports", "data")
        if not rows and payload:
            rows = [payload]
        for item in rows[:4]:
            period = str(item.get("fiscalDateEnding") or item.get("date") or "latest")
            shares = _number(
                item.get("reportedSharesOutstanding")
                or item.get("sharesOutstanding")
                or item.get("SharesOutstanding")
            )
            diluted = _number(item.get("dilutedShares") or item.get("diluted_shares"))
            if shares is None and diluted is None:
                continue
            row = session.exec(
                select(ShareCountObservation).where(
                    ShareCountObservation.ticker == ticker,
                    ShareCountObservation.provider == "alpha_vantage",
                    ShareCountObservation.period == period,
                )
            ).first() or ShareCountObservation(
                ticker=ticker, provider="alpha_vantage", period=period
            )
            row.basic_shares = shares
            row.diluted_shares = diluted or shares
            row.quality = "fresh"
            session.add(row)

    def _store_dividends(
        self, session: Session, ticker: str, payload: dict[str, object]
    ) -> None:
        rows = _first_list(payload, "data", "dividends")
        for item in rows:
            record_date = _date(item.get("recordDate") or item.get("record_date"))
            payment_date = _date(item.get("paymentDate") or item.get("payment_date"))
            dps = _number(item.get("amount") or item.get("dividendAmount"))
            if record_date is None or dps is None:
                continue
            existing = session.exec(
                select(DividendHistory).where(
                    DividendHistory.ticker == ticker,
                    DividendHistory.record_date == record_date,
                    DividendHistory.provider == "alpha_vantage",
                )
            ).first()
            if existing:
                continue
            session.add(
                DividendHistory(
                    ticker=ticker,
                    fiscal_year=record_date.year,
                    payment_date=payment_date,
                    record_date=record_date,
                    dividend_per_share=dps,
                    source="Alpha Vantage DIVIDENDS",
                    provider="alpha_vantage",
                    quality="partial",
                )
            )

    @staticmethod
    def overview_metrics(bundle: AlphaVantageBundle) -> dict[str, float | None]:
        payload = bundle.payloads.get("OVERVIEW", {})
        return {
            "trailing_pe": _number(payload.get("PERatio")),
            "forward_pe": _number(payload.get("ForwardPE")),
            "price_to_book": _number(payload.get("PriceToBookRatio")),
            "shares_outstanding": _number(payload.get("SharesOutstanding")),
        }
