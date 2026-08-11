import json
import math
from datetime import date, datetime, timezone
from statistics import mean, median

from sqlmodel import Session, select

from app.config import get_settings
from app.models.financial import FinancialSnapshot, HistoricalValuationObservation
from app.schemas.thesis import (
    HistoricalPricePoint,
    HistoricalValuationStatistics,
    ValuationRelativePosition,
    ValuationSnapshot,
)


_PERIOD_MONTH_DAY = {
    "Q1": (3, 31),
    "H1": (6, 30),
    "Q3": (9, 30),
    "FY": (12, 31),
}


def financial_period_end(row: FinancialSnapshot) -> date | None:
    if row.financial_period_end:
        return row.financial_period_end
    if row.fiscal_year and row.period_type in _PERIOD_MONTH_DAY:
        month, day = _PERIOD_MONTH_DAY[row.period_type]
        return date(row.fiscal_year, month, day)
    return row.financials_as_of


def filing_date(row: FinancialSnapshot) -> date | None:
    return row.filing_date or row.reported_date


def _eligible_rows(rows: list[FinancialSnapshot], observation_date: date) -> list[FinancialSnapshot]:
    latest_by_period: dict[tuple[int | None, str | None], FinancialSnapshot] = {}
    for row in rows:
        if row.snapshot_type != "full_statement":
            continue
        available = filing_date(row)
        if available is None or available > observation_date:
            continue
        if row.financial_statement_basis_warning or row.margin_quality_review:
            continue
        key = (row.fiscal_year, row.period_type)
        current = latest_by_period.get(key)
        if current is None or (filing_date(current) or date.min) < available:
            latest_by_period[key] = row
    return sorted(
        latest_by_period.values(),
        key=lambda row: (financial_period_end(row) or date.min, filing_date(row) or date.min),
    )


def point_in_time_denominators(
    rows: list[FinancialSnapshot], observation_date: date
) -> tuple[float | None, float | None, list[FinancialSnapshot], FinancialSnapshot | None]:
    eligible = _eligible_rows(rows, observation_date)
    quarters = [
        row
        for row in eligible
        if row.period_type in _PERIOD_MONTH_DAY
        and (row.diluted_eps is not None or row.common_net_income is not None or row.owners_parent_net_income is not None)
    ][-4:]
    ttm_eps: float | None = None
    if len(quarters) == 4:
        eps_values = [row.diluted_eps for row in quarters]
        if all(value is not None for value in eps_values):
            ttm_eps = sum(float(value) for value in eps_values if value is not None)
        else:
            incomes = [row.common_net_income or row.owners_parent_net_income for row in quarters]
            shares = next(
                (
                    row.diluted_shares or row.common_shares_outstanding
                    for row in reversed(quarters)
                    if row.diluted_shares or row.common_shares_outstanding
                ),
                None,
            )
            if all(value is not None for value in incomes) and shares and shares > 0:
                ttm_eps = sum(float(value) for value in incomes if value is not None) / float(shares)
    balance = next(
        (
            row
            for row in reversed(eligible)
            if (row.common_equity or row.owners_parent_equity)
            and row.common_shares_outstanding
            and row.common_shares_outstanding > 0
        ),
        None,
    )
    bvps: float | None = None
    if balance:
        equity = balance.common_equity or balance.owners_parent_equity
        if equity and equity > 0:
            bvps = float(equity) / float(balance.common_shares_outstanding)
    return ttm_eps, bvps, quarters, balance


def _weekly_prices(prices: list[HistoricalPricePoint]) -> list[HistoricalPricePoint]:
    by_week: dict[tuple[int, int], HistoricalPricePoint] = {}
    for point in sorted(prices, key=lambda item: item.date):
        iso = point.date.isocalendar()
        by_week[(iso.year, iso.week)] = point
    return sorted(by_week.values(), key=lambda item: item.date)


def _weekly_observations(
    observations: list[HistoricalValuationObservation],
) -> list[HistoricalValuationObservation]:
    by_week: dict[tuple[int, int], HistoricalValuationObservation] = {}
    for observation in sorted(observations, key=lambda item: item.observation_date):
        iso = observation.observation_date.isocalendar()
        by_week[(iso.year, iso.week)] = observation
    return sorted(by_week.values(), key=lambda item: item.observation_date)


def _percentile(values: list[float], percentile: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    index = (len(ordered) - 1) * percentile / 100
    lower = math.floor(index)
    upper = math.ceil(index)
    if lower == upper:
        return ordered[lower]
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (index - lower)


def _statistics(
    metric: str,
    current: float | None,
    observations: list[HistoricalValuationObservation],
    *,
    raw_observation_count: int,
    minimum_observations: int,
    minimum_days: int,
) -> HistoricalValuationStatistics | None:
    values = [
        float(getattr(item, metric))
        for item in observations
        if getattr(item, metric) is not None
    ]
    if not values:
        return None
    dates = [item.observation_date for item in observations if getattr(item, metric) is not None]
    current_percentile = None
    if current is not None:
        current_percentile = round(sum(value <= current for value in values) / len(values) * 100, 1)
    lookback_years = ((max(dates) - min(dates)).days / 365.25) if len(dates) > 1 else 0.0
    history_days = (max(dates) - min(dates)).days if len(dates) > 1 else 0
    sufficient = len(values) >= minimum_observations and (
        history_days >= minimum_days or minimum_observations <= 1
    )
    history_quality = (
        "high"
        if len(values) >= 156 and lookback_years >= 3
        else "medium"
        if len(values) >= 52 and lookback_years >= 1
        else "low"
        if sufficient
        else "insufficient"
    )
    if not sufficient:
        current_percentile = None
    return HistoricalValuationStatistics(
        metric=metric,
        current_value=current,
        historical_median=round(median(values), 4),
        historical_mean=round(mean(values), 4),
        percentile_10=round(_percentile(values, 10), 4) if sufficient else None,
        percentile_25=round(_percentile(values, 25), 4) if sufficient else None,
        percentile_50=round(_percentile(values, 50), 4) if sufficient else None,
        percentile_75=round(_percentile(values, 75), 4) if sufficient else None,
        percentile_90=round(_percentile(values, 90), 4) if sufficient else None,
        current_percentile=current_percentile,
        observation_count=len(values),
        lookback_years=round(lookback_years, 1),
        history_start_date=min(dates).isoformat(),
        history_end_date=max(dates).isoformat(),
        target_lookback_years=5.0,
        history_coverage_ratio=round(min(1.0, lookback_years / 5.0), 3),
        raw_observation_count=raw_observation_count,
        deduplicated_observation_count=len(values),
        sampling_frequency="weekly_last_valid_close",
        history_quality=history_quality,
    )


def _position_from_percentile(value: float, settings: object) -> ValuationRelativePosition:
    if value <= settings.valuation_history_discounted_percentile:
        return ValuationRelativePosition.discounted
    if value <= settings.valuation_history_somewhat_discounted_percentile:
        return ValuationRelativePosition.somewhat_discounted
    if value < settings.valuation_history_somewhat_premium_percentile:
        return ValuationRelativePosition.neutral
    if value < settings.valuation_history_premium_percentile:
        return ValuationRelativePosition.somewhat_premium
    return ValuationRelativePosition.premium


class HistoricalValuationService:
    def __init__(self) -> None:
        self.settings = get_settings()

    def update_cache(
        self,
        session: Session,
        ticker: str,
        prices: list[HistoricalPricePoint],
        rows: list[FinancialSnapshot],
    ) -> list[HistoricalValuationObservation]:
        if not prices or not rows:
            return list(
                session.exec(
                    select(HistoricalValuationObservation)
                    .where(HistoricalValuationObservation.ticker == ticker)
                    .order_by(HistoricalValuationObservation.observation_date)
                ).all()
            )
        existing = {
            item.observation_date: item
            for item in session.exec(
                select(HistoricalValuationObservation).where(
                    HistoricalValuationObservation.ticker == ticker
                )
            ).all()
        }
        latest_filing = max((filing_date(row) for row in rows if filing_date(row)), default=None)
        rebuild_from = max(existing) if existing else date.min
        if latest_filing and existing:
            latest_cached_filing = max(
                (item.filing_date for item in existing.values() if item.filing_date),
                default=None,
            )
            if latest_cached_filing is None or latest_filing > latest_cached_filing:
                rebuild_from = latest_filing
        sampled = _weekly_prices(prices)
        now = datetime.now(timezone.utc)
        for point in sampled:
            if point.date in existing and point.date < rebuild_from:
                continue
            ttm_eps, bvps, quarters, balance = point_in_time_denominators(rows, point.date)
            pe = point.close / ttm_eps if ttm_eps and ttm_eps > 0 else None
            pb = point.close / bvps if bvps and bvps > 0 else None
            warnings: list[str] = []
            if len(quarters) == 4 and ttm_eps:
                incomes = [
                    row.common_net_income or row.owners_parent_net_income
                    for row in quarters
                ]
                shares = next(
                    (
                        row.diluted_shares or row.common_shares_outstanding
                        for row in reversed(quarters)
                        if row.diluted_shares or row.common_shares_outstanding
                    ),
                    None,
                )
                if all(value is not None for value in incomes) and shares and shares > 0:
                    income_eps = sum(float(value) for value in incomes if value is not None) / float(shares)
                    discrepancy = abs(ttm_eps - income_eps) / max(abs(ttm_eps), abs(income_eps)) * 100
                    if discrepancy > self.settings.valuation_history_cross_check_threshold_pct:
                        pe = None
                        warnings.append("historical_pe_cross_check_failed")
            if (
                balance
                and balance.common_equity
                and balance.owners_parent_equity
                and balance.common_shares_outstanding
            ):
                common_bvps = float(balance.common_equity) / float(balance.common_shares_outstanding)
                owners_bvps = float(balance.owners_parent_equity) / float(balance.common_shares_outstanding)
                discrepancy = abs(common_bvps - owners_bvps) / max(abs(common_bvps), abs(owners_bvps)) * 100
                if discrepancy > self.settings.valuation_history_cross_check_threshold_pct:
                    pb = None
                    warnings.append("historical_pb_cross_check_failed")
            if pe is not None and (pe <= 0 or pe > self.settings.valuation_history_max_pe):
                pe = None
            if pb is not None and (pb <= 0 or pb > self.settings.valuation_history_max_pb):
                pb = None
            filing_used = max(
                [row for row in [*quarters, balance] if row is not None],
                key=lambda row: filing_date(row) or date.min,
                default=None,
            )
            source_filings = [
                (filing_date(row) or date.min).isoformat() for row in quarters
            ]
            observation = existing.get(point.date) or HistoricalValuationObservation(
                ticker=ticker, observation_date=point.date, price=point.close
            )
            observation.price = point.close
            observation.financial_filing_id = filing_used.id if filing_used else None
            observation.filing_date = filing_date(filing_used) if filing_used else None
            observation.financial_period_end = financial_period_end(filing_used) if filing_used else None
            observation.ttm_period_start = financial_period_end(quarters[0]) if quarters else None
            observation.ttm_period_end = financial_period_end(quarters[-1]) if quarters else None
            observation.ttm_source_filings = json.dumps(source_filings)
            observation.ttm_eps = ttm_eps
            observation.bvps = bvps
            observation.trailing_pe = pe
            observation.price_to_book = pb
            observation.quality = "fresh" if pe is not None or pb is not None else "unavailable"
            observation.warnings = json.dumps(warnings)
            iso = point.date.isocalendar()
            observation.sampling_frequency = "weekly_last_valid_close"
            observation.iso_year = iso.year
            observation.iso_week = iso.week
            observation.updated_at = now
            session.add(observation)
        session.flush()
        return list(
            session.exec(
                select(HistoricalValuationObservation)
                .where(HistoricalValuationObservation.ticker == ticker)
                .order_by(HistoricalValuationObservation.observation_date)
            ).all()
        )

    def apply(
        self,
        snapshot: ValuationSnapshot,
        observations: list[HistoricalValuationObservation],
        framework: dict[str, object],
        ticker: str,
    ) -> None:
        raw_count = len(observations)
        observations = _weekly_observations(observations)
        snapshot.historical_pe_statistics = _statistics(
            "trailing_pe",
            snapshot.trailing_pe,
            observations,
            raw_observation_count=raw_count,
            minimum_observations=self.settings.valuation_history_min_observations,
            minimum_days=self.settings.valuation_history_min_days,
        )
        snapshot.historical_pb_statistics = _statistics(
            "price_to_book",
            snapshot.price_to_book,
            observations,
            raw_observation_count=raw_count,
            minimum_observations=self.settings.valuation_history_min_observations,
            minimum_days=self.settings.valuation_history_min_days,
        )
        qualities = [
            stats.history_quality
            for stats in (snapshot.historical_pe_statistics, snapshot.historical_pb_statistics)
            if stats is not None
        ]
        snapshot.historical_distribution_confidence = (
            0.9 if "high" in qualities else 0.7 if "medium" in qualities else 0.4 if "low" in qualities else 0.1
        )
        method = str(framework.get("primary_method", "")).lower()
        framework_text = json.dumps(framework, ensure_ascii=False).lower()
        max_lookback = max(
            snapshot.historical_pe_statistics.lookback_years if snapshot.historical_pe_statistics else 0,
            snapshot.historical_pb_statistics.lookback_years if snapshot.historical_pb_statistics else 0,
        )
        if max_lookback and max_lookback < self.settings.valuation_history_minimum_years:
            snapshot.historical_comparability = "low"
        if any(
            marker in framework_text
            for marker in ("spin-off", "spinoff", "사업 믹스 변화", "대규모 인수", "회계기준 변화")
        ):
            snapshot.historical_comparability = "low"
        special_unknown = ticker in {"RXRX", "WRD", "TSLA"} or any(
            term in method for term in ("risk-adjusted npv", "unit economics", "scenario-based")
        )
        if special_unknown:
            snapshot.valuation_relative_position = ValuationRelativePosition.unknown
            snapshot.valuation_relative_position_reason = (
                "주 평가 방식에 필요한 시나리오·단위경제성 자료가 없어 PER/PBR만으로 위치를 확정하지 않습니다."
            )
            snapshot.valuation_relative_position_confidence = "low"
            return
        pe = snapshot.historical_pe_statistics
        pb = snapshot.historical_pb_statistics
        min_count = self.settings.valuation_history_min_observations
        pe_pct = pe.current_percentile if pe and pe.observation_count >= min_count else None
        pb_pct = pb.current_percentile if pb and pb.observation_count >= min_count else None
        if pe_pct is not None and pb_pct is not None:
            snapshot.valuation_primary_signal = f"PER 역사적 백분위 {pe_pct:.0f}"
            snapshot.valuation_secondary_signals = [f"PBR 역사적 백분위 {pb_pct:.0f}"]
            if abs(pe_pct - pb_pct) >= 40:
                snapshot.valuation_signal_conflict = True
                snapshot.valuation_relative_position_reason_codes.append("conflicting_multiples")
                snapshot.valuation_signal_summary = (
                    f"PER는 역사적 {pe_pct:.0f} 백분위, PBR은 {pb_pct:.0f} 백분위로 신호가 엇갈립니다."
                )
        is_cycle = ticker in {"000660", "MU"} or "cycle" in method
        is_insurance = ticker == "003690" or any(term in method for term in ("p/b", "pbr", "roe"))
        is_sotp = any(term in method for term in ("sotp", "sum-of-the-parts"))
        selected: list[float] = []
        basis: list[str] = []
        if is_insurance or is_cycle or is_sotp:
            if pb_pct is not None:
                selected.append(pb_pct)
                basis.append(f"PBR 역사적 백분위 {pb_pct:.0f}")
            if not is_cycle and not is_insurance and pe_pct is not None:
                selected.append(pe_pct)
                basis.append(f"PER 역사적 백분위 {pe_pct:.0f}")
        else:
            if pe_pct is not None:
                selected.append(pe_pct)
                basis.append(f"PER 역사적 백분위 {pe_pct:.0f}")
            if pb_pct is not None:
                selected.append(pb_pct)
                basis.append(f"PBR 역사적 백분위 {pb_pct:.0f}")
        if not selected:
            snapshot.valuation_relative_position = ValuationRelativePosition.unknown
            snapshot.valuation_relative_position_reason = (
                "point-in-time 역사적 배수 관측치가 충분하지 않습니다."
            )
            snapshot.valuation_relative_position_confidence = "low"
            snapshot.valuation_relative_position_reason_codes.append("insufficient_history")
            return
        combined = median(selected)
        if snapshot.valuation_signal_conflict and not (is_cycle or is_insurance or is_sotp):
            combined = 50.0
        snapshot.valuation_relative_position = _position_from_percentile(combined, self.settings)
        snapshot.valuation_relative_basis = " · ".join(basis)
        snapshot.valuation_relative_position_confidence = (
            "high" if min((pe.observation_count if pe_pct is not None and pe else 9999), (pb.observation_count if pb_pct is not None and pb else 9999)) >= 156 else "medium"
        )
        if snapshot.historical_comparability == "low":
            snapshot.valuation_relative_position_confidence = "low"
            snapshot.valuation_relative_position_reason = (
                "현재 시스템에 확보된 point-in-time 재무 이력이 충분하지 않거나 사업구조 변화가 있어 장기 역사적 비교 신뢰도가 낮습니다."
            )
            if is_cycle:
                snapshot.valuation_relative_position_reason += (
                    " 사이클 기업의 낮은 trailing PER는 저평가 신호로 자동 해석하지 않습니다."
                )
            snapshot.valuation_relative_position_reason_codes.append("low_comparability")
            return
        if is_cycle:
            snapshot.valuation_relative_position_reason = (
                "사이클 기업은 낮은 trailing PER를 할인 근거로 쓰지 않고 PBR과 정상화 이익을 우선했습니다."
            )
        elif is_sotp:
            snapshot.valuation_relative_position_reason = (
                "SOTP가 주 평가 방식이므로 역사적 PER/PBR은 참고 수준으로만 반영했습니다."
            )
            snapshot.valuation_relative_position_confidence = "low"
        else:
            snapshot.valuation_relative_position_reason = snapshot.valuation_signal_summary or (
                "현재 배수를 그 시점에 공개된 재무정보로 재구성한 역사적 분포와 비교했습니다."
            )
