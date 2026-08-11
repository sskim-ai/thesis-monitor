from datetime import date

from sqlmodel import Session, select

from app.models.event import CanonicalIssue, Event
from app.models.financial import DividendHistory, FinancialSnapshot, HistoricalValuationObservation
from app.models.watchlist import WatchlistItem
from app.schemas.thesis import DataCoverage, ValuationSnapshot
from app.services.financial_freshness_service import FinancialFreshnessService


def _issuer_type(item: WatchlistItem | None, events: list[Event]) -> str:
    if item and item.issuer_type:
        return item.issuer_type
    if item and (item.exchange or "").upper() == "KRX":
        return "krx"
    if any("filed 20-f" in event.title.lower() or "filed 6-k" in event.title.lower() for event in events):
        return "foreign_private_issuer"
    return "domestic_us"


def _coverage(value: bool, partial: bool = False) -> str:
    return "partial" if partial else "full" if value else "unavailable"


class DataCoverageService:
    def build(
        self,
        session: Session,
        ticker: str,
        snapshot: ValuationSnapshot | None = None,
    ) -> DataCoverage:
        item = session.exec(select(WatchlistItem).where(WatchlistItem.ticker == ticker)).first()
        rows = list(session.exec(select(FinancialSnapshot).where(FinancialSnapshot.ticker == ticker)).all())
        events = list(session.exec(select(Event).where(Event.ticker == ticker)).all())
        dividends = list(session.exec(select(DividendHistory).where(DividendHistory.ticker == ticker)).all())
        issues = list(session.exec(select(CanonicalIssue).where(CanonicalIssue.ticker == ticker)).all())
        history = list(
            session.exec(
                select(HistoricalValuationObservation).where(
                    HistoricalValuationObservation.ticker == ticker
                )
            ).all()
        )
        issuer_type = _issuer_type(item, events)
        freshness = FinancialFreshnessService().assess(session, ticker)
        reasons: list[str] = []
        if not rows:
            reasons.append("provider_not_supported")
        if freshness.refresh_required:
            reasons.append(freshness.reason_code or "stale_data")
        history_years = (
            (max(row.observation_date for row in history) - min(row.observation_date for row in history)).days / 365.25
            if len(history) > 1 else 0.0
        )
        if item and item.created_at.date() < date.today().replace(year=max(1, date.today().year - 5)) and history_years < 3:
            reasons.append("insufficient_history")
        if issuer_type in {"adr", "foreign_private_issuer"}:
            if item is None or item.adr_ratio is None:
                reasons.append("missing_adr_ratio")
        valuation_status = "unavailable"
        valuation_confidence = 0.0
        if snapshot is not None:
            valuation_status = snapshot.quality
            valuation_confidence = max(
                snapshot.trailing_valuation_confidence,
                snapshot.forward_valuation_confidence,
            )
        price_status = "fresh" if snapshot and snapshot.current_price is not None else "unavailable"
        financial_status = "full" if len(rows) >= 8 else "partial" if rows else "unavailable"
        foreign_status = (
            financial_status if issuer_type in {"adr", "foreign_private_issuer"} else "not_applicable"
        )
        return DataCoverage(
            issuer_type=issuer_type,
            financial_coverage_status=financial_status,
            financials=financial_status,
            earnings="fresh" if any(event.event_type in {"guidance_change", "earnings_beat", "earnings_miss"} for event in events) else "partial",
            price=price_status,
            valuation=valuation_status,
            dividend=_coverage(bool(dividends), any(row.quality != "fresh" for row in dividends)),
            capital_actions=_coverage(bool(issues)),
            foreign_filing=foreign_status,
            financial_freshness=freshness.status,
            business_thesis_confidence=0.85 if events or freshness.status == "current" else 0.6,
            valuation_confidence=valuation_confidence,
            price_confidence=0.9 if price_status == "fresh" else 0.3,
            macro_impact_confidence=0.75,
            reason_codes=list(dict.fromkeys(reasons)),
        )
