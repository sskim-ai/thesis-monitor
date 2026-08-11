from datetime import date

from sqlmodel import Session

from app.schemas.company import (
    AnalysisDataStatus,
    AnalysisEarningsSnapshot,
    AnalysisHistoricalValuation,
    AnalysisPricePeriod,
    AnalysisPriceSnapshot,
    AnalysisValuationSnapshot,
    TickerAnalysisSnapshot,
)
from app.schemas.thesis import (
    DataCoverage,
    HistoricalValuationStatistics,
    PriceContext,
    ValuationSnapshot,
)
from app.services.collection_service import CollectionService
from app.services.data_coverage_service import DataCoverageService
from app.services.ohlcv_client import OhlcvClient
from app.services.valuation_snapshot_service import ValuationSnapshotService
from app.utils.tickers import normalize_ticker


def _historical_summary(
    statistics: HistoricalValuationStatistics | None,
) -> AnalysisHistoricalValuation | None:
    if statistics is None:
        return None
    return AnalysisHistoricalValuation(
        current_value=statistics.current_value,
        median=statistics.historical_median,
        current_percentile=statistics.current_percentile,
        lookback_years=statistics.lookback_years,
    )


def _relative_position(snapshot: ValuationSnapshot) -> str:
    value = snapshot.valuation_relative_position
    return value.value if hasattr(value, "value") else str(value)


def _unique(items: list[str]) -> list[str]:
    return list(dict.fromkeys(item for item in items if item))


class TickerAnalysisSnapshotService:
    """Build a compact analysis snapshot without mutating investment state."""

    def __init__(
        self,
        collection_service: CollectionService | None = None,
        price_client: OhlcvClient | None = None,
        valuation_service: ValuationSnapshotService | None = None,
        coverage_service: DataCoverageService | None = None,
    ) -> None:
        self.collection_service = collection_service or CollectionService()
        self.price_client = price_client or OhlcvClient()
        self.valuation_service = valuation_service or ValuationSnapshotService()
        self.coverage_service = coverage_service or DataCoverageService()

    async def fetch(self, session: Session, ticker: str) -> TickerAnalysisSnapshot:
        normalized_ticker = normalize_ticker(ticker)
        profile = await self.collection_service.get_company_profile(session, normalized_ticker)

        price_failed = False
        try:
            price_context = await self.price_client.fetch_price_context(
                normalized_ticker, session=session
            )
        except Exception:  # noqa: BLE001
            price_failed = True
            price_context = PriceContext()

        valuation_failed = False
        try:
            valuation_snapshot = await self.valuation_service.fetch(
                normalized_ticker,
                profile.exchange or "",
                price_context,
                session=session,
                thesis=None,
            )
        except Exception:  # noqa: BLE001
            valuation_failed = True
            valuation_snapshot = ValuationSnapshot(
                current_price=price_context.decision.current_price,
                currency=price_context.decision.currency,
                price_as_of=price_context.decision.price_as_of,
            )

        try:
            coverage = self.coverage_service.build(session, normalized_ticker, valuation_snapshot)
        except Exception:  # noqa: BLE001
            coverage = valuation_snapshot.data_coverage or DataCoverage()

        periods = {
            name: AnalysisPricePeriod(
                latest_close=summary.latest_close,
                window_return_pct=summary.period_return_pct,
                range_position_pct=summary.range_position_pct,
                actual_count=summary.actual_count,
            )
            for name in ("daily", "weekly", "monthly")
            if (summary := price_context.periods.get(name)) is not None
        }
        decision = price_context.decision
        current_position = (
            decision.current_position
            if decision.registered_rules_available
            and decision.current_position != "가격 위치 자료 없음"
            else None
        )
        price = AnalysisPriceSnapshot(
            available=price_context.available,
            current_price=decision.current_price,
            currency=decision.currency,
            price_as_of=decision.price_as_of,
            market_session=decision.market_session,
            current_position=current_position,
            periods=periods,
        )
        earnings = AnalysisEarningsSnapshot(
            latest_period=valuation_snapshot.latest_earnings_period,
            is_preliminary=valuation_snapshot.earnings_context_is_preliminary,
            financial_currency=valuation_snapshot.financial_currency,
            revenue=valuation_snapshot.latest_revenue,
            operating_income=valuation_snapshot.latest_operating_income,
            operating_margin=valuation_snapshot.latest_operating_margin,
            qoq_revenue_growth=valuation_snapshot.latest_revenue_qoq,
            qoq_operating_income_growth=(valuation_snapshot.latest_operating_income_qoq),
            yoy_revenue_growth=valuation_snapshot.latest_revenue_yoy,
            yoy_operating_income_growth=(valuation_snapshot.latest_operating_income_yoy),
            ttm_eps=valuation_snapshot.ttm_eps,
            ttm_contains_preliminary=valuation_snapshot.ttm_contains_preliminary,
        )
        valuation = AnalysisValuationSnapshot(
            current_price=valuation_snapshot.current_price,
            ttm_eps=valuation_snapshot.ttm_eps,
            bvps=valuation_snapshot.bvps,
            forward_eps=valuation_snapshot.forward_eps,
            forward_bvps=valuation_snapshot.forward_bvps,
            trailing_pe=valuation_snapshot.trailing_pe,
            price_to_book=valuation_snapshot.price_to_book,
            forward_pe=valuation_snapshot.forward_pe,
            forward_price_to_book=valuation_snapshot.forward_price_to_book,
            valuation_relative_position=_relative_position(valuation_snapshot),
            valuation_relative_position_confidence=(
                valuation_snapshot.valuation_relative_position_confidence
            ),
            historical_pe=_historical_summary(valuation_snapshot.historical_pe_statistics),
            historical_pb=_historical_summary(valuation_snapshot.historical_pb_statistics),
        )

        cautions: list[str] = []
        if price_failed or not price_context.available:
            cautions.append("현재 가격 데이터를 확인하지 못했습니다.")
        if valuation_failed or not any(
            value is not None
            for value in (
                valuation.trailing_pe,
                valuation.price_to_book,
                valuation.forward_pe,
                valuation.forward_price_to_book,
            )
        ):
            cautions.append(
                "현재 Valuation 계산에 필요한 재무 데이터를 충분히 확인하지 못했습니다."
            )
        if (
            valuation_snapshot.earnings_context_is_preliminary
            and valuation_snapshot.earnings_context_usable
            and not valuation_snapshot.eps_per_usable
        ):
            if "per_share_basis_insufficient" in coverage.reason_codes:
                cautions.append(
                    "최근 공식 잠정실적의 매출·영업이익은 반영했지만 주당 기준을 확인하지 못해 자체 PER 계산은 보류했습니다."
                )
            else:
                cautions.append(
                    "최신 잠정실적은 매출·영업이익에 반영했지만 EPS 기준이 없어 PER는 이전 기준입니다."
                )
        if (
            valuation_snapshot.forward_pe_reference_caution
            and valuation_snapshot.forward_pe is not None
        ):
            cautions.append("fPER는 산출 기간이나 이익 기준이 명확하지 않아 참고 수준입니다.")
        if coverage.full_financial_freshness == "stale":
            cautions.append("정식 재무제표가 오래되어 PBR 판단 강도를 낮춥니다.")
        if (
            "missing_adr_ratio" in coverage.reason_codes
            and "per_share_basis_insufficient" not in coverage.reason_codes
        ):
            cautions.append("ADR 비율을 확인하지 못해 주당 Valuation 일부를 계산하지 못했습니다.")
        if "per_share_basis_insufficient" in coverage.reason_codes and not (
            valuation_snapshot.earnings_context_is_preliminary
            and valuation_snapshot.earnings_context_usable
            and not valuation_snapshot.eps_per_usable
        ):
            basis_statuses = {
                valuation_snapshot.trailing_pe_basis_status,
                valuation_snapshot.price_to_book_basis_status,
                valuation_snapshot.forward_pe_basis_status,
                valuation_snapshot.forward_price_to_book_basis_status,
            }
            if "currency_mismatch" in basis_statuses:
                cautions.append(
                    "가격 통화와 주당 실적 기준 통화가 달라 자체 PER/PBR 계산을 보류했습니다."
                )
            else:
                cautions.append(
                    "ADR/외국 상장주식의 주당 기준을 확인하지 못해 자체 PER/PBR 계산을 보류했습니다."
                )
        if valuation_snapshot.multiple_basis_conflicts:
            cautions.append("같은 기준으로 계산한 Valuation 값이 크게 달라 판단 강도를 낮췄습니다.")
        if "preliminary_validation_failed" in coverage.reason_codes:
            cautions.append("최근 잠정실적 숫자를 검증하지 못해 현재 이익 계산에서 제외했습니다.")

        as_of = (
            valuation_snapshot.valuation_data_as_of
            or valuation_snapshot.price_as_of
            or decision.price_as_of
            or date.today().isoformat()
        )
        earnings_status = coverage.earnings
        if valuation_snapshot.earnings_context_usable:
            earnings_status = (
                coverage.preliminary_financial_quality
                if valuation_snapshot.earnings_context_is_preliminary
                else coverage.full_financial_quality
            )
        return TickerAnalysisSnapshot(
            ticker=normalized_ticker,
            company_name=profile.company_name,
            exchange=profile.exchange,
            as_of=as_of,
            price=price,
            earnings=earnings,
            valuation=valuation,
            data_status=AnalysisDataStatus(
                price=coverage.price_quality or coverage.price,
                earnings=earnings_status,
                valuation=coverage.valuation,
                financial_freshness=coverage.financial_freshness,
            ),
            cautions=_unique(cautions),
        )
