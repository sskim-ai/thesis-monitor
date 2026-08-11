import json
import math
from datetime import date, datetime, timezone
from statistics import median

import httpx
from sqlmodel import Session, select

from app.config import get_settings
from app.models.financial import FinancialSnapshot
from app.models.thesis import InvestmentThesis
from app.schemas.thesis import (
    PriceContext,
    ValuationRelativePosition,
    ValuationSnapshot,
)


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


def _json_dict(value: str | None) -> dict[str, object]:
    try:
        parsed = json.loads(value or "{}")
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _valid_quarters(rows: list[FinancialSnapshot]) -> list[FinancialSnapshot]:
    unique: dict[tuple[int | None, str | None], FinancialSnapshot] = {}
    for row in sorted(rows, key=lambda item: item.reported_date or date.min):
        if row.financial_statement_basis_warning or row.margin_quality_review:
            continue
        if row.period_type not in {"Q1", "H1", "Q3", "FY"}:
            continue
        if row.revenue is None and row.net_income is None and row.diluted_eps is None:
            continue
        unique[(row.fiscal_year, row.period_type)] = row
    return sorted(unique.values(), key=lambda item: item.reported_date or date.min)


def _ttm_denominators(
    rows: list[FinancialSnapshot],
) -> tuple[float | None, float | None, str | None]:
    quarters = _valid_quarters(rows)[-4:]
    if len(quarters) < 4:
        return None, None, None
    eps_values = [row.diluted_eps for row in quarters]
    if all(value is not None for value in eps_values):
        return sum(float(value) for value in eps_values if value is not None), None, "TTM diluted EPS"
    income_values = [row.common_net_income or row.owners_parent_net_income for row in quarters]
    shares = next(
        (
            row.diluted_shares or row.common_shares_outstanding
            for row in reversed(quarters)
            if row.diluted_shares or row.common_shares_outstanding
        ),
        None,
    )
    if all(value is not None for value in income_values) and shares and shares > 0:
        common_income = sum(float(value) for value in income_values if value is not None)
        return common_income / shares, common_income, "TTM owners-parent net income"
    return None, None, None


def _latest_balance(rows: list[FinancialSnapshot]) -> FinancialSnapshot | None:
    return next(
        (
            row
            for row in sorted(rows, key=lambda item: item.reported_date or date.min, reverse=True)
            if (row.common_equity or row.owners_parent_equity)
            and row.common_shares_outstanding
            and not row.financial_statement_basis_warning
        ),
        None,
    )


def _relative_position(
    snapshot: ValuationSnapshot,
    framework: dict[str, object],
) -> tuple[ValuationRelativePosition, str | None]:
    method = str(framework.get("primary_method", "")).lower()
    metric = "price_to_book" if any(term in method for term in ("p/b", "pbr", "roe")) else "forward_pe"
    value = getattr(snapshot, metric)
    if value is None and metric == "forward_pe":
        metric = "trailing_pe"
        value = snapshot.trailing_pe
    ranges = framework.get("historical_multiple_range") or framework.get("peer_multiple_range")
    if not isinstance(ranges, dict) or value is None:
        return ValuationRelativePosition.unknown, None
    low = ranges.get(f"{metric}_low", ranges.get("low"))
    high = ranges.get(f"{metric}_high", ranges.get("high"))
    if not isinstance(low, (int, float)) or not isinstance(high, (int, float)) or low >= high:
        return ValuationRelativePosition.unknown, None
    midpoint = (float(low) + float(high)) / 2
    if value < float(low):
        position = ValuationRelativePosition.discounted
    elif value < midpoint:
        position = ValuationRelativePosition.somewhat_discounted
    elif value <= float(high):
        position = ValuationRelativePosition.neutral
    elif value <= float(high) * 1.2:
        position = ValuationRelativePosition.somewhat_premium
    else:
        position = ValuationRelativePosition.premium
    return position, f"{metric} 비교 범위 {float(low):.1f}~{float(high):.1f}배"


class ValuationSnapshotService:
    def __init__(self, transport: httpx.AsyncBaseTransport | None = None) -> None:
        self.settings = get_settings()
        self.transport = transport

    def _financial_rows(
        self,
        session: Session | None,
        ticker: str,
    ) -> list[FinancialSnapshot]:
        if session is None:
            return []
        return list(
            session.exec(
                select(FinancialSnapshot)
                .where(FinancialSnapshot.ticker == ticker)
                .order_by(FinancialSnapshot.reported_date)
            ).all()
        )

    def _apply_derived_trailing(
        self,
        snapshot: ValuationSnapshot,
        rows: list[FinancialSnapshot],
    ) -> tuple[float | None, float | None]:
        if snapshot.current_price is None:
            return None, None
        ttm_eps, _ttm_income, pe_method = _ttm_denominators(rows)
        derived_pe: float | None = None
        if ttm_eps is not None and ttm_eps <= 0:
            if snapshot.trailing_pe_status != "value":
                snapshot.trailing_pe_status = "not_meaningful"
                snapshot.trailing_pe_source = "derived_trailing"
                snapshot.trailing_pe_method = pe_method
        elif ttm_eps:
            derived_pe = round(snapshot.current_price / ttm_eps, 4)
            if snapshot.trailing_pe_status != "value":
                snapshot.trailing_pe = derived_pe
                snapshot.trailing_pe_status = "value"
                snapshot.trailing_pe_source = "derived_trailing"
                snapshot.trailing_pe_method = pe_method
                snapshot.trailing_valuation_confidence = 0.85

        balance = _latest_balance(rows)
        derived_pb: float | None = None
        if balance is not None and snapshot.current_price is not None:
            equity = balance.common_equity or balance.owners_parent_equity
            shares = balance.common_shares_outstanding
            if equity and shares and equity > 0 and shares > 0:
                bvps = equity / shares
                derived_pb = round(snapshot.current_price / bvps, 4)
                if snapshot.price_to_book_status != "value":
                    snapshot.price_to_book = derived_pb
                    snapshot.price_to_book_status = "value"
                    snapshot.price_to_book_source = "derived_trailing"
                    snapshot.price_to_book_method = "latest owners-parent common equity / current common shares"
                    snapshot.trailing_valuation_confidence = max(
                        snapshot.trailing_valuation_confidence, 0.85
                    )
        if rows:
            latest_date = max((row.financials_as_of or row.reported_date for row in rows if row.financials_as_of or row.reported_date), default=None)
            snapshot.financials_as_of = latest_date.isoformat() if latest_date else None
        return derived_pe, derived_pb

    def _apply_forward_model(
        self,
        snapshot: ValuationSnapshot,
        rows: list[FinancialSnapshot],
        ticker: str,
        framework: dict[str, object],
    ) -> None:
        if snapshot.current_price is None or snapshot.forward_pe_status == "value":
            return
        method = str(framework.get("primary_method", "")).lower()
        if ticker in {"RXRX", "WRD"} or any(
            term in method
            for term in ("risk-adjusted npv", "unit economics", "sotp", "sum-of-the-parts")
        ):
            if ticker in {"RXRX", "WRD"} and any(
                (row.common_net_income or row.owners_parent_net_income or 0) < 0
                for row in _valid_quarters(rows)[-4:]
            ):
                snapshot.forward_pe_status = "not_meaningful"
                snapshot.forward_pe_source = "modeled_forward"
            return
        quarters = _valid_quarters(rows)
        minimum = self.settings.valuation_model_min_quarters
        if len(quarters) < minimum:
            return
        recent = quarters[-minimum:]
        shares = next(
            (row.diluted_shares or row.common_shares_outstanding for row in reversed(recent) if row.diluted_shares or row.common_shares_outstanding),
            None,
        )
        if not shares or shares <= 0:
            return
        is_insurance = ticker == "003690" or any(
            term in method for term in ("p/b", "pbr", "roe")
        )
        if is_insurance:
            balance = _latest_balance(rows)
            equity = (balance.common_equity or balance.owners_parent_equity) if balance else None
            if not equity or equity <= 0:
                return
            roe_values: list[float] = []
            for row in recent:
                row_equity = row.common_equity or row.owners_parent_equity
                if not row_equity or row_equity <= 0:
                    continue
                if row.common_net_income is not None:
                    roe_values.append(float(row.common_net_income) * 4 / float(row_equity))
                elif row.diluted_eps is not None and row.common_shares_outstanding:
                    bvps = float(row_equity) / float(row.common_shares_outstanding)
                    if bvps > 0:
                        roe_values.append(float(row.diluted_eps) * 4 / bvps)
            if not roe_values:
                return
            fy1_income = equity * median(roe_values)
            forecast_method = "normalized_roe"
        else:
            if any(row.revenue is None or row.common_net_income is None for row in recent):
                return
            current_revenue = sum(float(row.revenue) for row in recent[-4:] if row.revenue is not None)
            prior_revenue = sum(float(row.revenue) for row in recent[-8:-4] if row.revenue is not None)
            if current_revenue <= 0 or prior_revenue <= 0:
                return
            growth = max(
                self.settings.valuation_model_growth_floor,
                min(self.settings.valuation_model_growth_cap, current_revenue / prior_revenue - 1),
            )
            margins = [
                float(row.common_net_income) / float(row.revenue)
                for row in recent
                if row.common_net_income is not None and row.revenue not in {None, 0}
            ]
            if len(margins) < minimum:
                return
            latest_ttm_margin = sum(float(row.common_net_income) for row in recent[-4:]) / current_revenue
            normalized_margin = median(margins)
            forecast_method = "normalized_net_margin"
            if ticker in {"000660", "MU"}:
                modeled_margin = normalized_margin
                forecast_method = "cycle_adjusted"
            else:
                modeled_margin = latest_ttm_margin * 0.6 + normalized_margin * 0.4
            fy1_income = current_revenue * (1 + growth) * float(modeled_margin)
        if fy1_income <= 0:
            snapshot.forward_pe_status = "not_meaningful"
            snapshot.forward_pe_source = "modeled_forward"
            snapshot.forecast_method = forecast_method
            return
        fy1_eps = fy1_income / shares
        snapshot.forward_pe = round(snapshot.current_price / fy1_eps, 4)
        snapshot.forward_pe_status = "value"
        snapshot.forward_pe_source = "modeled_forward"
        snapshot.forward_pe_method = forecast_method
        snapshot.forward_basis = "FY1"
        snapshot.forecast_method = forecast_method
        snapshot.forward_valuation_confidence = 0.55

        balance = _latest_balance(rows)
        if balance is not None:
            equity = balance.common_equity or balance.owners_parent_equity
            common_shares = balance.common_shares_outstanding
            if equity and common_shares and equity > 0 and common_shares > 0:
                expected_dividends = balance.dividends or 0.0
                fy1_equity = equity + fy1_income - expected_dividends
                if fy1_equity > 0:
                    snapshot.forward_price_to_book = round(
                        snapshot.current_price / (fy1_equity / common_shares), 4
                    )
                    snapshot.forward_price_to_book_status = "value"
                    snapshot.forward_price_to_book_source = "modeled_forward"
                    snapshot.forward_price_to_book_method = "FY1 common equity roll-forward"
                    snapshot.forward_book_basis = "FY1"
                    if balance.dividends is None:
                        snapshot.warnings.append(
                            "내부 추정 fPBR은 배당 자료 부족으로 배당 0 가정을 사용했습니다."
                        )

    def _cross_check(
        self,
        snapshot: ValuationSnapshot,
        provider_pe: float | None,
        provider_pb: float | None,
        derived_pe: float | None,
        derived_pb: float | None,
    ) -> None:
        threshold = self.settings.valuation_discrepancy_threshold_pct / 100
        for label, provider_value, derived_value in (
            ("PER", provider_pe, derived_pe),
            ("PBR", provider_pb, derived_pb),
        ):
            if provider_value and derived_value:
                difference = abs(provider_value / derived_value - 1)
                if difference > threshold:
                    snapshot.valuation_discrepancy_warning = True
                    snapshot.warnings.append(
                        f"provider {label}와 자체 계산값 차이가 커 분모·주식수·기준일 확인이 필요합니다."
                    )

    async def fetch(
        self,
        ticker: str,
        exchange: str | None,
        price_context: PriceContext,
        as_of: datetime | None = None,
        *,
        session: Session | None = None,
        thesis: InvestmentThesis | None = None,
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
        rows = self._financial_rows(session, ticker)
        provider_pe: float | None = None
        provider_pb: float | None = None

        if _supports_finnhub(exchange, ticker) and self.settings.finnhub_api_key:
            try:
                async with httpx.AsyncClient(
                    base_url="https://finnhub.io/api/v1",
                    timeout=self.settings.valuation_provider_timeout_seconds,
                    transport=self.transport,
                ) as client:
                    response = await client.get(
                        "/stock/metric",
                        params={"symbol": ticker, "metric": "all", "token": self.settings.finnhub_api_key},
                    )
                    response.raise_for_status()
                    payload = response.json()
                metrics = payload.get("metric", {}) if isinstance(payload, dict) else {}
                if isinstance(metrics, dict) and metrics:
                    eps_ttm = metrics.get("epsTTM")
                    provider_pe = _positive_number(metrics.get("peTTM"))
                    if provider_pe is not None:
                        snapshot.trailing_pe = provider_pe
                        snapshot.trailing_pe_status = "value"
                        snapshot.trailing_pe_source = "provider"
                        snapshot.trailing_pe_method = "Finnhub peTTM"
                        snapshot.trailing_valuation_confidence = 0.75
                    elif isinstance(eps_ttm, (int, float)) and float(eps_ttm) <= 0:
                        snapshot.trailing_pe_status = "not_meaningful"
                        snapshot.trailing_pe_source = "provider"
                    snapshot.forward_pe = _positive_number(metrics.get("forwardPE"))
                    if snapshot.forward_pe is not None:
                        snapshot.forward_pe_status = "value"
                        snapshot.forward_pe_source = "consensus_forward"
                        snapshot.forward_pe_method = "Finnhub forwardPE"
                        snapshot.forward_basis = "provider-defined forward consensus"
                        snapshot.forward_valuation_confidence = 0.7
                    provider_pb = _positive_number(metrics.get("pbQuarterly") or metrics.get("pbAnnual"))
                    if provider_pb is not None:
                        snapshot.price_to_book = provider_pb
                        snapshot.price_to_book_status = "value"
                        snapshot.price_to_book_source = "provider"
                        snapshot.price_to_book_method = "Finnhub reported P/B"
                    snapshot.provider = "ohlcv-analyst + finnhub"
                    denominator_date = _date_value(payload.get("metricAsOf") or payload.get("asOfDate"))
                    snapshot.denominator_as_of = denominator_date.isoformat() if denominator_date else None
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
                else:
                    snapshot.warnings.append("Finnhub에서 사용 가능한 Valuation 배수를 반환하지 않았습니다.")
            except (httpx.HTTPError, TypeError, ValueError) as exc:
                snapshot.warnings.append(f"Finnhub 배수 조회 실패: {type(exc).__name__}")
        elif _supports_finnhub(exchange, ticker):
            snapshot.warnings.append("Finnhub API key가 없어 Valuation 배수를 수집하지 못했습니다.")

        derived_pe, derived_pb = self._apply_derived_trailing(snapshot, rows)
        framework = _json_dict(thesis.valuation_framework if thesis else None)
        self._apply_forward_model(snapshot, rows, ticker, framework)
        self._cross_check(snapshot, provider_pe, provider_pb, derived_pe, derived_pb)
        relative, basis = _relative_position(snapshot, framework)
        snapshot.valuation_relative_position = relative
        snapshot.valuation_relative_basis = basis

        if rows and snapshot.provider == "ohlcv-analyst":
            snapshot.provider = "ohlcv-analyst + financial-statements"
        if snapshot.quality == "unavailable":
            if any(
                status in {"value", "not_meaningful"}
                for status in (
                    snapshot.trailing_pe_status,
                    snapshot.forward_pe_status,
                    snapshot.price_to_book_status,
                    snapshot.forward_price_to_book_status,
                )
            ):
                snapshot.quality = "partial"
            elif snapshot.current_price is not None:
                snapshot.quality = "partial"
        if not _supports_finnhub(exchange, ticker) and not rows:
            snapshot.warnings.append(
                "현재 연결된 재무 데이터로 신뢰 가능한 PER/PBR 분모를 만들 수 없어 자료 없음으로 표시합니다."
            )
        if snapshot.financials_as_of:
            financial_date = _date_value(snapshot.financials_as_of)
            if financial_date and (now.date() - financial_date).days > self.settings.valuation_financial_max_age_days:
                snapshot.quality = "stale"
                snapshot.warnings.append("재무 분모 기준일이 오래되어 Valuation 판단 강도를 낮춥니다.")
        return snapshot
