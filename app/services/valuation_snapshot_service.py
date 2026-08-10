import math
from datetime import date, datetime, timezone

import httpx

from app.config import get_settings
from app.schemas.thesis import PriceContext, ValuationSnapshot


def _positive_number(value: object) -> float | None:
    if not isinstance(value, (int, float)):
        return None
    number = float(value)
    return round(number, 4) if math.isfinite(number) and number > 0 else None


def _currency(exchange: str | None, ticker: str) -> str:
    if (exchange or "").upper() in {"KRX", "KOSPI", "KOSDAQ"} or ticker.isdigit():
        return "KRW"
    return "USD"


def _supports_finnhub(exchange: str | None, ticker: str) -> bool:
    return (
        (exchange or "").upper() in {"NASDAQ", "NYSE", "AMEX"}
        and ticker.isascii()
        and ticker.isalpha()
    )


def _date_value(value: object) -> date | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        return date.fromisoformat(value[:10])
    except ValueError:
        return None


class ValuationSnapshotService:
    def __init__(self, transport: httpx.AsyncBaseTransport | None = None) -> None:
        self.settings = get_settings()
        self.transport = transport

    async def fetch(
        self,
        ticker: str,
        exchange: str | None,
        price_context: PriceContext,
        as_of: datetime | None = None,
    ) -> ValuationSnapshot:
        now = as_of or datetime.now(timezone.utc)
        daily = price_context.periods.get("daily")
        snapshot = ValuationSnapshot(
            current_price=daily.latest_close if daily else None,
            currency=_currency(exchange, ticker),
            price_as_of=daily.latest_date if daily else None,
            price_basis=price_context.decision.price_basis,
            provider="ohlcv-analyst",
            valuation_data_as_of=now.date().isoformat(),
        )
        if not _supports_finnhub(exchange, ticker):
            snapshot.quality = "partial" if snapshot.current_price is not None else "unavailable"
            snapshot.warnings.append(
                "현재 연결된 배수 provider가 이 거래소 종목을 지원하지 않아 PER/PBR은 자료 없음입니다."
            )
            return snapshot
        if not self.settings.finnhub_api_key:
            snapshot.quality = "partial" if snapshot.current_price is not None else "unavailable"
            snapshot.warnings.append("Finnhub API key가 없어 Valuation 배수를 수집하지 못했습니다.")
            return snapshot

        try:
            async with httpx.AsyncClient(
                base_url="https://finnhub.io/api/v1",
                timeout=self.settings.valuation_provider_timeout_seconds,
                transport=self.transport,
            ) as client:
                response = await client.get(
                    "/stock/metric",
                    params={
                        "symbol": ticker,
                        "metric": "all",
                        "token": self.settings.finnhub_api_key,
                    },
                )
                response.raise_for_status()
                payload = response.json()
        except (httpx.HTTPError, TypeError, ValueError) as exc:
            snapshot.quality = "partial" if snapshot.current_price is not None else "unavailable"
            snapshot.warnings.append(f"Finnhub 배수 조회 실패: {type(exc).__name__}")
            return snapshot

        metrics = payload.get("metric", {}) if isinstance(payload, dict) else {}
        if not isinstance(metrics, dict) or not metrics:
            snapshot.quality = "partial" if snapshot.current_price is not None else "unavailable"
            snapshot.warnings.append("Finnhub에서 사용 가능한 Valuation 배수를 반환하지 않았습니다.")
            return snapshot

        eps_ttm = metrics.get("epsTTM")
        snapshot.trailing_pe = _positive_number(metrics.get("peTTM"))
        if snapshot.trailing_pe is not None:
            snapshot.trailing_pe_status = "value"
        elif isinstance(eps_ttm, (int, float)) and float(eps_ttm) < 0:
            snapshot.trailing_pe_status = "not_meaningful"

        snapshot.forward_pe = _positive_number(metrics.get("forwardPE"))
        if snapshot.forward_pe is not None:
            snapshot.forward_pe_status = "value"
            snapshot.forward_basis = "provider-defined forward consensus"

        snapshot.price_to_book = _positive_number(
            metrics.get("pbQuarterly") or metrics.get("pbAnnual")
        )
        if snapshot.price_to_book is not None:
            snapshot.price_to_book_status = "value"

        snapshot.provider = "ohlcv-analyst + finnhub"
        denominator_date = _date_value(
            payload.get("metricAsOf") or payload.get("asOfDate")
        )
        snapshot.denominator_as_of = (
            denominator_date.isoformat() if denominator_date else None
        )
        if denominator_date is None:
            snapshot.quality = "partial"
            snapshot.warnings.append(
                "Finnhub 배수 분모의 정확한 추정 기준일이 제공되지 않아 freshness를 부분 확인으로 표시합니다."
            )
        elif (now.date() - denominator_date).days > self.settings.valuation_snapshot_max_age_days:
            snapshot.quality = "stale"
            snapshot.warnings.append(
                "Valuation 배수 분모 기준일이 오래되어 최신 주가·실적을 완전히 반영하지 않을 수 있습니다."
            )
        else:
            snapshot.quality = "fresh"
        return snapshot
