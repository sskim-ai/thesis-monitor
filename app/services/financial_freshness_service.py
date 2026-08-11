from dataclasses import dataclass
from datetime import date

from sqlmodel import Session, select

from app.models.event import Event
from app.models.financial import FinancialSnapshot
from app.config import get_settings


_FINANCIAL_TYPES = {
    "earnings_beat",
    "earnings_miss",
    "earnings_surprise",
    "guidance_change",
    "revenue_guidance_change",
    "margin_guidance_change",
    "financial_report",
}
_OFFICIAL_FINANCIAL_PROVIDERS = {"opendart", "sec_edgar", "company_ir"}


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
    latest_full_filing_date: date | None = None
    latest_preliminary_filing_date: date | None = None
    refresh_reason: str | None = None
    refresh_trigger_event_id: int | None = None


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


def _period(row: FinancialSnapshot | None) -> date | None:
    return (row.financial_period_end or row.financials_as_of) if row else None


def _filing_date(row: FinancialSnapshot | None) -> date | None:
    return (row.filing_date or row.reported_date) if row else None


class FinancialFreshnessService:
    def assess(
        self, session: Session, ticker: str, *, as_of: date | None = None
    ) -> FinancialFreshness:
        today = as_of or date.today()
        events = list(
            session.exec(
                select(Event).where(Event.ticker == ticker).order_by(Event.date.desc())
            ).all()
        )
        material_events = [event for event in events if _material(event)]
        latest_event = material_events[0] if material_events else None
        period_events = [event for event in material_events if event.reporting_period_end]
        latest_period_event = max(
            period_events,
            key=lambda event: (event.reporting_period_end or date.min, event.date),
            default=None,
        )
        rows = list(
            session.exec(
                select(FinancialSnapshot)
                .where(FinancialSnapshot.ticker == ticker)
                .order_by(
                    FinancialSnapshot.financial_period_end.desc(),
                    FinancialSnapshot.filing_date.desc(),
                )
            ).all()
        )
        full_row = next(
            (row for row in rows if row.snapshot_type == "full_statement"), None
        )
        preliminary_row = next(
            (row for row in rows if row.snapshot_type == "preliminary_earnings"),
            None,
        )
        row = full_row or preliminary_row or (rows[0] if rows else None)
        latest_guidance = next(
            (
                event
                for event in material_events
                if event.guidance_changed
                or event.revenue_guidance_changed
                or event.margin_guidance_changed
            ),
            None,
        )
        full_period = _period(full_row)
        preliminary_period = _period(preliminary_row)
        available_period = max(
            (period for period in (full_period, preliminary_period) if period),
            default=None,
        )
        metadata = {
            "latest_full_period": full_period,
            "latest_preliminary_period": preliminary_period,
            "latest_guidance_date": latest_guidance.date if latest_guidance else None,
            "latest_full_filing_date": _filing_date(full_row),
            "latest_preliminary_filing_date": _filing_date(preliminary_row),
        }

        for event in material_events:
            event.financial_refresh_required = False
            session.add(event)

        if latest_event is None and row is None:
            return FinancialFreshness(
                "unavailable",
                None,
                None,
                None,
                False,
                "provider_not_supported",
                **metadata,
            )

        refresh_event: Event | None = None
        refresh_reason: str | None = None
        if latest_period_event and (
            available_period is None
            or (latest_period_event.reporting_period_end or date.min) > available_period
        ):
            refresh_event = latest_period_event
            refresh_reason = "newer_reporting_period_detected"
        elif row is None and latest_event is not None:
            refresh_event = latest_event
            refresh_reason = "latest_financial_event_without_snapshot"
        elif (
            latest_event
            and latest_event.provider in _OFFICIAL_FINANCIAL_PROVIDERS
            and latest_event.reporting_period_end is None
            and latest_event.document_type in {"full_statement", "preliminary_earnings"}
        ):
            refresh_event = latest_event
            refresh_reason = "official_financial_period_unresolved"

        if refresh_event:
            refresh_event.financial_refresh_required = True
            session.add(refresh_event)
            result = (
                "parsing_failed"
                if refresh_event.document_type in {"full_statement", "preliminary_earnings"}
                else "filing_not_available"
            )
            return FinancialFreshness(
                "refresh_required",
                latest_event.date if latest_event else None,
                _period(row),
                _filing_date(row),
                True,
                refresh_reason,
                **metadata,
                refresh_result=result,
                refresh_reason=refresh_reason,
                refresh_trigger_event_id=refresh_event.id,
            )

        preliminary_is_newer = bool(
            preliminary_period
            and (full_period is None or preliminary_period > full_period)
        )
        unresolved_foreign_filing = bool(
            latest_event
            and latest_event.provider == "sec_edgar"
            and latest_event.financial_report_filed
            and latest_event.reporting_period_end is None
            and any(form in latest_event.title.lower() for form in ("filed 6-k", "filed 20-f"))
        )
        if unresolved_foreign_filing and not preliminary_is_newer:
            return FinancialFreshness(
                "foreign_filing_partial",
                latest_event.date if latest_event else None,
                _period(row),
                _filing_date(row),
                False,
                "foreign_filing_partial",
                **metadata,
                refresh_result="foreign_filing_partial",
                refresh_reason="foreign_filing_period_or_statement_not_normalized",
                refresh_trigger_event_id=latest_event.id if latest_event else None,
            )
        cadence_days = get_settings().financial_reporting_cadence_days
        full_period_age = (today - full_period).days if full_period else None
        full_filing = _filing_date(full_row)
        cadence_due = bool(
            full_period_age is not None
            and full_period_age > cadence_days
            and (
                latest_event is not None
                and (full_filing is None or latest_event.date > full_filing)
            )
        )
        if cadence_due and not preliminary_is_newer:
            trigger = latest_event
            return FinancialFreshness(
                "refresh_due",
                latest_event.date if latest_event else None,
                _period(row),
                _filing_date(row),
                False,
                "reporting_cadence_exceeded",
                **metadata,
                refresh_result="refresh_due",
                refresh_reason=(
                    f"latest full reporting period is older than {cadence_days} days "
                    "and a later material earnings event exists"
                ),
                refresh_trigger_event_id=trigger.id if trigger else None,
            )
        return FinancialFreshness(
            "preliminary_only" if preliminary_is_newer else "current",
            latest_event.date if latest_event else None,
            _period(row),
            _filing_date(row),
            False,
            "preliminary_ahead_of_full_statement" if preliminary_is_newer else None,
            **metadata,
            refresh_result="preliminary_only" if preliminary_is_newer else "refresh_completed",
            refresh_reason=(
                "preliminary_income_statement_is_newer_than_full_statement"
                if preliminary_is_newer
                else "same_or_older_reporting_period_already_available"
            ),
        )
