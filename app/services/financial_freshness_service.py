from dataclasses import dataclass
from datetime import date

from sqlmodel import Session, select

from app.models.event import Event
from app.models.financial import FinancialSnapshot


_FINANCIAL_TYPES = {
    "earnings_beat",
    "earnings_miss",
    "earnings_surprise",
    "guidance_change",
    "revenue_guidance_change",
    "margin_guidance_change",
    "financial_report",
}


@dataclass(frozen=True)
class FinancialFreshness:
    status: str
    latest_material_event_date: date | None
    latest_snapshot_date: date | None
    latest_filing_date: date | None
    refresh_required: bool
    reason_code: str | None = None
    latest_full_period: date | None = None
    latest_preliminary_period: date | None = None
    latest_guidance_date: date | None = None
    latest_consensus_date: date | None = None
    refresh_result: str = "unavailable"


def _material(event: Event) -> bool:
    return event.event_type in _FINANCIAL_TYPES or any(
        (
            event.guidance_changed,
            event.revenue_guidance_changed,
            event.margin_guidance_changed,
            event.earnings_guidance_changed,
            event.cash_flow_guidance_changed,
            event.financial_report_filed,
            event.fcf_impact_known,
        )
    )


class FinancialFreshnessService:
    def assess(self, session: Session, ticker: str) -> FinancialFreshness:
        events = list(
            session.exec(
                select(Event).where(Event.ticker == ticker).order_by(Event.date.desc())
            ).all()
        )
        latest_event = next((event for event in events if _material(event)), None)
        rows = list(session.exec(
            select(FinancialSnapshot)
            .where(FinancialSnapshot.ticker == ticker)
            .order_by(FinancialSnapshot.filing_date.desc(), FinancialSnapshot.reported_date.desc())
        ).all())
        full_row = next(
            (row for row in rows if row.snapshot_type == "full_statement"),
            None,
        )
        preliminary_row = next(
            (row for row in rows if row.snapshot_type == "preliminary_earnings"),
            None,
        )
        row = full_row or (rows[0] if rows else None)
        snapshot_date = row.financial_period_end or row.financials_as_of if row else None
        filing_date = row.filing_date or row.reported_date if row else None
        latest_guidance = next(
            (
                event.date
                for event in events
                if event.guidance_changed
                or event.revenue_guidance_changed
                or event.margin_guidance_changed
            ),
            None,
        )
        metadata = {
            "latest_full_period": (
                full_row.financial_period_end or full_row.financials_as_of
                if full_row
                else None
            ),
            "latest_preliminary_period": (
                preliminary_row.financial_period_end or preliminary_row.financials_as_of
                if preliminary_row
                else None
            ),
            "latest_guidance_date": latest_guidance,
        }
        if latest_event is None and row is None:
            return FinancialFreshness(
                "unavailable", None, None, None, False,
                "provider_not_supported", **metadata,
            )
        if row is None:
            return FinancialFreshness(
                "refresh_pending", latest_event.date if latest_event else None, None, None, True,
                "latest_financial_event_without_snapshot", **metadata,
                refresh_result="filing_not_available",
            )
        refresh_required = bool(latest_event and (filing_date is None or latest_event.date > filing_date))
        if refresh_required:
            for event in events:
                if _material(event) and event.date > (filing_date or date.min):
                    event.financial_refresh_required = True
                    session.add(event)
            return FinancialFreshness(
                "refresh_pending", latest_event.date, snapshot_date, filing_date, True,
                "financial_event_newer_than_snapshot", **metadata,
                refresh_result=("preliminary_only" if preliminary_row else "filing_not_available"),
            )
        return FinancialFreshness(
            "current", latest_event.date if latest_event else None, snapshot_date, filing_date,
            False, **metadata, refresh_result="refresh_completed"
        )
