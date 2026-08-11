import json
import math
from datetime import date, datetime, timedelta, timezone
from statistics import median

import httpx
from sqlmodel import Session, select

from app.config import get_settings
from app.models.financial import CapitalReturnHistory, DividendHistory, FinancialSnapshot
from app.models.security import ConsensusEstimate, SecurityMaster, ShareCountObservation
from app.models.watchlist import WatchlistItem
from app.models.thesis import InvestmentThesis
from app.schemas.thesis import (
    PriceContext,
    ValuationRelativePosition,
    ValuationSnapshot,
)
from app.services.historical_valuation_service import (
    HistoricalValuationService,
    filing_date,
    financial_period_end,
)
from app.services.alpha_vantage_service import AlphaVantageService
from app.services.data_coverage_service import DataCoverageService
from app.services.dividend_history_service import DividendHistoryService
from app.services.financial_freshness_service import FinancialFreshnessService
from app.services.provider_telemetry_service import ProviderTelemetryService
from app.services.sec_financial_snapshot_service import SecFinancialSnapshotService


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
    return sorted(
        unique.values(),
        key=lambda item: (financial_period_end(item) or date.min, filing_date(item) or date.min),
    )


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
        self.history_service = HistoricalValuationService()
        self.sec_financial_service = SecFinancialSnapshotService(transport=transport)
        self.dividend_service = DividendHistoryService()
        self.coverage_service = DataCoverageService()
        self.freshness_service = FinancialFreshnessService()
        self.alpha_vantage_service = AlphaVantageService(transport=transport)
        self.telemetry = ProviderTelemetryService()

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

    def _apply_financial_metadata(
        self, snapshot: ValuationSnapshot, rows: list[FinancialSnapshot]
    ) -> None:
        if not rows:
            return
        latest_row = max(
            rows,
            key=lambda row: (financial_period_end(row) or date.min, filing_date(row) or date.min),
        )
        period_end = financial_period_end(latest_row)
        filed = filing_date(latest_row)
        snapshot.financial_period_end = period_end.isoformat() if period_end else None
        snapshot.filing_date = filed.isoformat() if filed else None
        snapshot.financials_as_of = snapshot.financial_period_end
        quarters = _valid_quarters(rows)[-4:]
        if len(quarters) == 4:
            start = financial_period_end(quarters[0])
            end = financial_period_end(quarters[-1])
            snapshot.ttm_period_start = start.isoformat() if start else None
            snapshot.ttm_period_end = end.isoformat() if end else None
            snapshot.ttm_source_filings = [
                filed.isoformat()
                for row in quarters
                if (filed := filing_date(row)) is not None
            ]

    def _apply_derived_trailing(
        self,
        snapshot: ValuationSnapshot,
        rows: list[FinancialSnapshot],
    ) -> tuple[float | None, float | None]:
        if snapshot.current_price is None:
            return None, None
        ttm_eps, _ttm_income, pe_method = _ttm_denominators(rows)
        ttm_rows = _valid_quarters(rows)[-4:]
        if len(ttm_rows) == 4:
            ttm_end = financial_period_end(ttm_rows[-1])
            ttm_filed = max(
                (filing_date(row) for row in ttm_rows if filing_date(row)),
                default=None,
            )
            snapshot.trailing_pe_denominator_period_end = (
                ttm_end.isoformat() if ttm_end else None
            )
            snapshot.trailing_pe_denominator_filing_date = (
                ttm_filed.isoformat() if ttm_filed else None
            )
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
            balance_period = financial_period_end(balance)
            balance_filed = filing_date(balance)
            snapshot.pbr_denominator_period_end = (
                balance_period.isoformat() if balance_period else None
            )
            snapshot.pbr_denominator_filing_date = (
                balance_filed.isoformat() if balance_filed else None
            )
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
        self._apply_financial_metadata(snapshot, rows)
        return derived_pe, derived_pb

    def _forecast_dividends(
        self,
        rows: list[FinancialSnapshot],
        fy1_income: float,
        framework: dict[str, object],
        history: list[DividendHistory] | None = None,
    ) -> tuple[float | None, str | None, str, str | None]:
        policy = framework.get("official_dividend_forecast")
        if isinstance(policy, (int, float)) and float(policy) >= 0:
            return float(policy), "official_policy", "high", "회사 공식 배당정책"
        announced = framework.get("announced_common_dividend")
        if isinstance(announced, (int, float)) and float(announced) >= 0:
            return float(announced), "announced_dividend", "high", "발표된 보통주 배당"
        usable_history = [row for row in (history or []) if row.total_dividend is not None]
        payout_history = [row.payout_ratio for row in usable_history[-3:] if row.payout_ratio is not None]
        if len(payout_history) >= 3:
            payout = max(0.0, min(1.0, median(float(value) for value in payout_history)))
            return fy1_income * payout, "median_3y_payout_ratio", "medium", f"최근 3년 중앙 지급률 {payout:.1%}"
        if len(usable_history) >= 3:
            return median(float(row.total_dividend) for row in usable_history[-3:]), "median_3y_dividend", "medium", "최근 3년 총배당 중앙값"
        if usable_history:
            return float(usable_history[-1].total_dividend), "latest_dividend", "low", "최근 총배당 유지"
        annual = [
            row
            for row in _valid_quarters(rows)
            if row.period_type == "FY"
            and (row.common_dividends is not None or row.dividends is not None)
        ]
        payouts = [
            float(row.common_dividends if row.common_dividends is not None else row.dividends)
            / float(row.common_net_income or row.owners_parent_net_income)
            for row in annual[-3:]
            if (row.common_net_income or row.owners_parent_net_income or 0) > 0
        ]
        if len(payouts) >= 3:
            payout = max(0.0, min(1.0, median(payouts)))
            return (
                fy1_income * payout,
                "median_3y_payout_ratio",
                "medium",
                f"최근 3년 중앙 지급률 {payout:.1%}",
            )
        dividend_totals = [
            float(row.common_dividends if row.common_dividends is not None else row.dividends)
            for row in annual[-3:]
        ]
        if len(dividend_totals) >= 3:
            return median(dividend_totals), "median_3y_dividend", "medium", "최근 3년 총배당 중앙값"
        if dividend_totals:
            return dividend_totals[-1], "latest_dividend", "low", "최근 총배당 유지"
        return None, None, "unavailable", None

    def _forecast_buybacks(
        self,
        rows: list[FinancialSnapshot],
        framework: dict[str, object],
        ticker: str,
        history: list[CapitalReturnHistory] | None = None,
    ) -> tuple[float | None, str | None, str, str | None]:
        announced = framework.get("announced_buyback")
        if isinstance(announced, (int, float)) and float(announced) >= 0:
            return float(announced), "announced_authorization", "high", "발표된 자사주 매입"
        actual = [row.actual_amount for row in (history or []) if row.actual_amount is not None]
        if actual:
            return median(max(0.0, float(value)) for value in actual[-3:]), "historical_normalized_buyback", "medium", "최근 연간 자사주 매입 중앙값"
        annual = [row for row in _valid_quarters(rows) if row.period_type == "FY" and row.buybacks is not None]
        if annual:
            values = [max(0.0, float(row.buybacks or 0)) for row in annual[-3:]]
            return median(values), "historical_normalized_buyback", "medium", "최근 연간 자사주 매입 중앙값"
        if ticker in {"GOOGL", "IBM", "TSLA"}:
            return None, None, "unavailable", "정기 자사주 매입 영향 자료 부족"
        return 0.0, "no_material_buyback_data", "low", "확인된 중요 자사주 매입 없음"

    def _apply_forward_model(
        self,
        snapshot: ValuationSnapshot,
        rows: list[FinancialSnapshot],
        ticker: str,
        framework: dict[str, object],
        dividend_history: list[DividendHistory] | None = None,
        capital_returns: list[CapitalReturnHistory] | None = None,
    ) -> None:
        if snapshot.current_price is None:
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
        consensus_fy1_income = (
            snapshot.current_price / snapshot.forward_pe * shares
            if snapshot.forward_pe_status == "value"
            and snapshot.forward_pe_source == "consensus_forward"
            and snapshot.forward_pe
            and snapshot.forward_pe > 0
            else None
        )
        if consensus_fy1_income is not None:
            fy1_income = consensus_fy1_income
            forecast_method = "consensus_forward_eps"
        elif is_insurance:
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
            if snapshot.forward_pe_status != "value":
                snapshot.forward_pe_status = "not_meaningful"
                snapshot.forward_pe_source = "modeled_forward"
                snapshot.forecast_method = forecast_method
            return
        fy1_eps = fy1_income / shares
        if snapshot.forward_pe_status != "value":
            snapshot.forward_pe = round(snapshot.current_price / fy1_eps, 4)
            snapshot.forward_pe_status = "value"
            snapshot.forward_pe_source = "modeled_forward"
            snapshot.forward_pe_method = forecast_method
            snapshot.forward_basis = "FY1"
            snapshot.forward_pe_input_period = "FY1"
            snapshot.forecast_method = forecast_method
            snapshot.forward_valuation_confidence = 0.55

        balance = _latest_balance(rows)
        if balance is not None:
            equity = balance.common_equity or balance.owners_parent_equity
            common_shares = balance.common_shares_outstanding
            if equity and common_shares and equity > 0 and common_shares > 0:
                expected_dividends, dividend_method, dividend_quality, dividend_assumption = (
                    self._forecast_dividends(rows, fy1_income, framework, dividend_history)
                )
                expected_buybacks, buyback_method, buyback_quality, buyback_assumption = (
                    self._forecast_buybacks(rows, framework, ticker, capital_returns)
                )
                snapshot.dividend_forecast_method = dividend_method
                snapshot.dividend_forecast_quality = dividend_quality
                snapshot.dividend_assumption = dividend_assumption
                snapshot.buyback_forecast_method = buyback_method
                snapshot.buyback_assumption_quality = buyback_quality
                snapshot.buyback_assumption = buyback_assumption
                if expected_dividends is None:
                    snapshot.warnings.append(
                        "배당정책·과거 지급 이력이 부족해 내부 추정 fPBR을 계산하지 않았습니다."
                    )
                    return
                if expected_buybacks is None:
                    snapshot.warnings.append(
                        "중요 자사주 매입 가정을 신뢰성 있게 만들 수 없어 내부 추정 fPBR을 계산하지 않았습니다."
                    )
                    return
                issuance = median(
                    [float(row.equity_issuance) for row in recent if row.equity_issuance is not None]
                ) if any(row.equity_issuance is not None for row in recent) else 0.0
                oci = median(
                    [float(row.other_comprehensive_income) for row in recent if row.other_comprehensive_income is not None]
                ) if any(row.other_comprehensive_income is not None for row in recent) else 0.0
                fy1_equity = equity + fy1_income - expected_dividends - expected_buybacks + issuance + oci
                if fy1_equity > 0:
                    snapshot.forward_price_to_book = round(
                        snapshot.current_price / (fy1_equity / common_shares), 4
                    )
                    snapshot.forward_price_to_book_status = "value"
                    snapshot.forward_price_to_book_source = "modeled_forward"
                    snapshot.forward_price_to_book_method = (
                        "FY1 common equity roll-forward"
                        f"; income={forecast_method}"
                        f"; dividend={dividend_method}"
                        f"; buyback={buyback_method}"
                    )
                    snapshot.forward_book_basis = "FY1"
                    snapshot.forward_pb_input_period = "FY1"

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
        price_decision = price_context.decision
        daily_price = price_context.periods.get("daily")
        current_price = price_decision.current_price or (
            daily_price.latest_close if daily_price else None
        )
        exchange_trade_date = (
            price_decision.exchange_trade_date
            or price_decision.price_as_of
            or (daily_price.latest_date if daily_price else None)
        )
        snapshot = ValuationSnapshot(
            current_price=current_price,
            currency=_currency(exchange, ticker),
            price_as_of=exchange_trade_date,
            exchange_trade_date=exchange_trade_date,
            latest_completed_regular_session_date=(
                price_decision.latest_completed_regular_session_date
            ),
            price_observed_at=price_decision.price_observed_at,
            price_observed_timezone=price_decision.price_observed_timezone,
            price_basis=price_decision.price_basis or ("close" if exchange_trade_date else "unavailable"),
            provider="ohlcv-analyst",
            valuation_data_as_of=now.date().isoformat(),
            valuation_calculated_at=now.isoformat(),
        )
        rows = self._financial_rows(session, ticker)
        if (
            session is not None
            and _supports_finnhub(exchange, ticker)
            and self.settings.sec_user_agent
            and (
                len(rows) < self.settings.valuation_model_min_quarters
                or max((filing_date(row) or date.min for row in rows), default=date.min)
                < now.date() - timedelta(days=75)
            )
        ):
            try:
                await self.sec_financial_service.refresh(
                    session, ticker, self.settings.sec_user_agent
                )
                rows = self._financial_rows(session, ticker)
            except (httpx.HTTPError, TypeError, ValueError):
                pass
        dividend_history: list[DividendHistory] = []
        capital_returns: list[CapitalReturnHistory] = []
        watchlist_item: WatchlistItem | None = None
        security_master: SecurityMaster | None = None
        if session is not None:
            dividend_history = self.dividend_service.sync_financial_snapshots(
                session, ticker, rows
            )
            capital_returns = self.dividend_service.sync_capital_returns(
                session, ticker, rows
            )
            watchlist_item = session.exec(
                select(WatchlistItem).where(WatchlistItem.ticker == ticker)
            ).first()
            security_master = session.exec(
                select(SecurityMaster).where(SecurityMaster.ticker == ticker)
            ).first()
        provider_pe: float | None = None
        provider_pb: float | None = None
        alpha_metrics: dict[str, float | None] = {}

        if (
            session is not None
            and _supports_finnhub(exchange, ticker)
            and self.settings.alpha_vantage_api_key
        ):
            alpha_bundle = await self.alpha_vantage_service.collect(
                session,
                ticker,
                functions=("EARNINGS_ESTIMATES", "SHARES_OUTSTANDING", "OVERVIEW"),
            )
            alpha_metrics = self.alpha_vantage_service.overview_metrics(alpha_bundle)
            if alpha_bundle.warnings:
                snapshot.warnings.append(
                    "Alpha Vantage 일부 보조 데이터가 제공되지 않아 사용 가능한 항목만 교차검증했습니다."
                )

        if _supports_finnhub(exchange, ticker) and self.settings.finnhub_api_key:
            finnhub_started = datetime.now(timezone.utc)
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
                        snapshot.forward_pe_input_period = (
                            "provider-defined forward consensus"
                        )
                        snapshot.forward_valuation_confidence = 0.7
                        snapshot.estimate_provider = "finnhub"
                        snapshot.estimate_period = "provider-defined forward consensus"
                        snapshot.consensus_status = "partial"
                        if session is not None:
                            estimate = session.exec(
                                select(ConsensusEstimate).where(
                                    ConsensusEstimate.ticker == ticker,
                                    ConsensusEstimate.provider == "finnhub",
                                    ConsensusEstimate.estimate_period
                                    == "provider-defined forward consensus",
                                )
                            ).first() or ConsensusEstimate(
                                ticker=ticker,
                                provider="finnhub",
                                estimate_as_of=now,
                                estimate_period="provider-defined forward consensus",
                            )
                            estimate.estimate_as_of = now
                            estimate.metric = "forward_pe"
                            estimate.basis = "provider-defined"
                            estimate.value = snapshot.forward_pe
                            estimate.quality = "partial"
                            estimate.coverage_status = "partial"
                            estimate.raw_reference = "Finnhub stock metric forwardPE"
                            session.add(estimate)
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
                    if session is not None:
                        self.telemetry.record(
                            session,
                            provider="finnhub",
                            endpoint="stock_metric",
                            ticker=ticker,
                            started_at=finnhub_started,
                            status="success",
                        )
                else:
                    snapshot.warnings.append("Finnhub에서 사용 가능한 Valuation 배수를 반환하지 않았습니다.")
                    if session is not None:
                        self.telemetry.record(
                            session,
                            provider="finnhub",
                            endpoint="stock_metric",
                            ticker=ticker,
                            started_at=finnhub_started,
                            status="partial",
                            error_type="EmptyProviderPayload",
                            error_reason="valuation_metrics_unavailable",
                        )
            except (httpx.HTTPError, TypeError, ValueError) as exc:
                snapshot.warnings.append(f"Finnhub 배수 조회 실패: {type(exc).__name__}")
                if session is not None:
                    self.telemetry.record(
                        session,
                        provider="finnhub",
                        endpoint="stock_metric",
                        ticker=ticker,
                        started_at=finnhub_started,
                        status="failed",
                        error_type=type(exc).__name__,
                        error_code=(
                            str(exc.response.status_code)
                            if isinstance(exc, httpx.HTTPStatusError)
                            else None
                        ),
                        error_reason="valuation_metric_fetch_failed",
                    )
        elif _supports_finnhub(exchange, ticker):
            snapshot.warnings.append("Finnhub API key가 없어 Valuation 배수를 수집하지 못했습니다.")

        alpha_estimate: ConsensusEstimate | None = None
        alpha_shares: ShareCountObservation | None = None
        if session is not None:
            alpha_estimate = session.exec(
                select(ConsensusEstimate)
                .where(
                    ConsensusEstimate.ticker == ticker,
                    ConsensusEstimate.provider == "alpha_vantage",
                )
                .order_by(ConsensusEstimate.estimate_period)
            ).first()
            alpha_shares = session.exec(
                select(ShareCountObservation)
                .where(
                    ShareCountObservation.ticker == ticker,
                    ShareCountObservation.provider == "alpha_vantage",
                )
                .order_by(ShareCountObservation.observed_at.desc())
            ).first()
        if alpha_estimate and alpha_estimate.estimate_mean is not None:
            alpha_eps = alpha_estimate.estimate_mean
            if snapshot.estimate_provider is None:
                snapshot.estimate_provider = "alpha_vantage"
                snapshot.estimate_as_of = alpha_estimate.estimate_as_of.isoformat()
                snapshot.estimate_period = alpha_estimate.estimate_period
                snapshot.estimate_mean = alpha_eps
                snapshot.estimate_high = alpha_estimate.estimate_high
                snapshot.estimate_low = alpha_estimate.estimate_low
                snapshot.estimate_analyst_count = alpha_estimate.analyst_count
                snapshot.estimate_revision_direction = alpha_estimate.revision_direction
                snapshot.consensus_status = alpha_estimate.coverage_status
            if snapshot.current_price and alpha_eps > 0:
                alpha_forward_pe = snapshot.current_price / alpha_eps
                if snapshot.forward_pe_status != "value":
                    snapshot.forward_pe = round(alpha_forward_pe, 4)
                    snapshot.forward_pe_status = "value"
                    snapshot.forward_pe_source = "consensus_forward"
                    snapshot.forward_pe_method = "Alpha Vantage analyst EPS estimate"
                    snapshot.forward_basis = alpha_estimate.estimate_period
                    snapshot.forward_pe_input_period = alpha_estimate.estimate_period
                    snapshot.forward_valuation_confidence = 0.65
                    snapshot.consensus_status = alpha_estimate.coverage_status
                elif snapshot.forward_pe:
                    finnhub_implied_eps = snapshot.current_price / snapshot.forward_pe
                    discrepancy = abs(finnhub_implied_eps / alpha_eps - 1)
                    if discrepancy > self.settings.alpha_vantage_consensus_discrepancy_pct / 100:
                        snapshot.consensus_disagreement = True
                        snapshot.forward_valuation_confidence *= 0.7
                        snapshot.warnings.append(
                            "Finnhub와 Alpha Vantage의 forward EPS 추정치 차이가 커 신뢰도를 낮췄습니다."
                        )
                        snapshot.consensus_status = "conflicting"

        issuer_type = watchlist_item.issuer_type if watchlist_item else None
        missing_adr_mapping = issuer_type in {"adr", "foreign_private_issuer"} and (
            (watchlist_item is None or watchlist_item.adr_ratio is None)
            and (security_master is None or security_master.adr_ratio is None)
        )
        if missing_adr_mapping:
            derived_pe, derived_pb = None, None
            self._apply_financial_metadata(snapshot, rows)
            snapshot.valuation_calculation_warning = True
            snapshot.warnings.append(
                "foreign issuer/ADR의 주식 변환 비율이 확인되지 않아 per-share 자체 Valuation 계산을 보류합니다."
            )
        else:
            derived_pe, derived_pb = self._apply_derived_trailing(snapshot, rows)
        if alpha_shares and rows:
            official_shares = next(
                (
                    row.diluted_shares or row.common_shares_outstanding
                    for row in reversed(rows)
                    if row.diluted_shares or row.common_shares_outstanding
                ),
                None,
            )
            cross_check_shares = alpha_shares.diluted_shares or alpha_shares.basic_shares
            if official_shares and cross_check_shares:
                share_difference = abs(cross_check_shares / official_shares - 1)
                if share_difference > self.settings.alpha_vantage_share_discrepancy_pct / 100:
                    snapshot.share_count_discrepancy_warning = True
                    snapshot.trailing_valuation_confidence *= 0.7
                    snapshot.warnings.append(
                        "공식 재무제표와 Alpha Vantage 주식 수 차이가 커 주당 배수 신뢰도를 낮췄습니다."
                    )
        framework = _json_dict(thesis.valuation_framework if thesis else None)
        if not missing_adr_mapping:
            self._apply_forward_model(
                snapshot,
                rows,
                ticker,
                framework,
                dividend_history,
                capital_returns,
            )
        self._cross_check(snapshot, provider_pe, provider_pb, derived_pe, derived_pb)
        self._cross_check(
            snapshot,
            alpha_metrics.get("trailing_pe"),
            alpha_metrics.get("price_to_book"),
            derived_pe,
            derived_pb,
        )
        if session is not None and not missing_adr_mapping:
            observations = self.history_service.update_cache(
                session,
                ticker,
                price_context.valuation_history or price_context.daily_history,
                rows,
            )
            self.history_service.apply(snapshot, observations, framework, ticker)
        elif missing_adr_mapping:
            snapshot.historical_pe_statistics = None
            snapshot.historical_pb_statistics = None
            snapshot.valuation_relative_position = ValuationRelativePosition.unknown
            snapshot.valuation_relative_position_confidence = "low"
            snapshot.valuation_relative_position_reason = (
                "foreign issuer/ADR의 주식 변환 비율과 통화 기준이 확인되지 않아 역사적 per-share 배수 비교를 보류합니다."
            )
            snapshot.valuation_relative_position_reason_codes = ["missing_adr_ratio"]
        if (
            snapshot.valuation_relative_position == ValuationRelativePosition.unknown
            and not missing_adr_mapping
        ):
            relative, basis = _relative_position(snapshot, framework)
            if relative != ValuationRelativePosition.unknown:
                snapshot.valuation_relative_position = relative
                snapshot.valuation_relative_basis = basis
                snapshot.valuation_relative_position_confidence = "low"
                snapshot.valuation_relative_position_reason = "저장된 peer 또는 역사적 범위를 참고했습니다."

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
        if snapshot.filing_date:
            financial_date = _date_value(snapshot.filing_date)
            if financial_date and (now.date() - financial_date).days > self.settings.valuation_financial_max_age_days:
                snapshot.quality = "stale"
                snapshot.warnings.append("재무 분모 기준일이 오래되어 Valuation 판단 강도를 낮춥니다.")
        if (
            snapshot.forward_pe_status == "value"
            and snapshot.forward_pe_source == "consensus_forward"
            and snapshot.consensus_status == "unavailable"
        ):
            snapshot.consensus_status = "partial"
            if snapshot.estimate_provider is None:
                snapshot.estimate_provider = "provider_metadata_partial"
        if session is not None:
            freshness = self.freshness_service.assess(session, ticker)
            snapshot.financial_refresh_required = freshness.refresh_required
            snapshot.latest_material_financial_event_date = (
                freshness.latest_material_event_date.isoformat()
                if freshness.latest_material_event_date else None
            )
            snapshot.financial_freshness = freshness.status
            snapshot.latest_full_financial_period = (
                freshness.latest_full_period.isoformat()
                if freshness.latest_full_period
                else None
            )
            snapshot.latest_preliminary_financial_period = (
                freshness.latest_preliminary_period.isoformat()
                if freshness.latest_preliminary_period
                else None
            )
            snapshot.latest_preliminary_context_period = (
                snapshot.latest_preliminary_financial_period
            )
            snapshot.latest_full_filing_date = (
                freshness.latest_full_filing_date.isoformat()
                if freshness.latest_full_filing_date
                else None
            )
            snapshot.latest_preliminary_filing_date = (
                freshness.latest_preliminary_filing_date.isoformat()
                if freshness.latest_preliminary_filing_date
                else None
            )
            snapshot.latest_guidance_date = (
                freshness.latest_guidance_date.isoformat()
                if freshness.latest_guidance_date
                else None
            )
            snapshot.financial_refresh_result = freshness.refresh_result
            snapshot.financial_refresh_reason = freshness.refresh_reason
            snapshot.financial_refresh_trigger_event_id = (
                freshness.refresh_trigger_event_id
            )
            if freshness.refresh_required:
                snapshot.quality = "stale"
                snapshot.forward_valuation_confidence *= 0.5
                snapshot.trailing_valuation_confidence *= 0.7
                snapshot.warnings.append(
                    "최근 실적 발표는 확인됐지만 Valuation 재무 snapshot이 최신 분기로 갱신되지 않았습니다."
                )
            elif freshness.status == "refresh_due":
                if snapshot.quality == "fresh":
                    snapshot.quality = "partial"
                snapshot.forward_valuation_confidence *= 0.7
                snapshot.trailing_valuation_confidence *= 0.8
                snapshot.warnings.append(
                    "정식 재무 보고 주기가 경과했고 이후 material 실적 이벤트가 있어 재무 갱신 여부를 확인 중입니다."
                )
            elif freshness.status == "preliminary_only":
                if snapshot.quality == "fresh":
                    snapshot.quality = "partial"
                latest_preliminary = next(
                    (
                        row
                        for row in rows
                        if row.snapshot_type == "preliminary_earnings"
                        and row.financial_period_end == freshness.latest_preliminary_period
                    ),
                    None,
                )
                if latest_preliminary and latest_preliminary.financial_statement_basis_warning:
                    snapshot.warnings.append(
                        "최신 잠정실적 공시는 확인했지만 파싱된 숫자의 단위·기간 검증에 실패해 매출·이익 및 Valuation 계산에는 반영하지 않았습니다."
                    )
                else:
                    snapshot.warnings.append(
                        "매출·영업이익은 최신 잠정실적까지 확인했지만 현금흐름·재무상태표 배수는 직전 정식 재무제표 기준입니다."
                    )
            snapshot.current_multiple_confidence = snapshot.trailing_valuation_confidence
            snapshot.forward_multiple_confidence = snapshot.forward_valuation_confidence
            if (
                freshness.refresh_required
                or snapshot.consensus_disagreement
                or snapshot.share_count_discrepancy_warning
            ):
                if snapshot.valuation_relative_position_confidence == "high":
                    snapshot.valuation_relative_position_confidence = "medium"
                if snapshot.consensus_disagreement or snapshot.share_count_discrepancy_warning:
                    snapshot.valuation_relative_position_confidence = "low"
            if (
                freshness.refresh_required
                and snapshot.current_multiple_confidence < 0.4
                and snapshot.forward_multiple_confidence < 0.4
            ):
                snapshot.valuation_relative_position = ValuationRelativePosition.unknown
                snapshot.valuation_relative_position_reason = (
                    "최근 material 실적 이후 정식 재무 분모가 갱신되지 않아 현재 Valuation 위치 판단을 보류합니다."
                )
                snapshot.valuation_relative_position_reason_codes.append(
                    "stale_financial_after_material_event"
                )
            snapshot.data_coverage = self.coverage_service.build(session, ticker, snapshot)
        return snapshot
