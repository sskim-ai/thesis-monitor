from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from functools import lru_cache
from typing import Literal
from zoneinfo import ZoneInfo

import exchange_calendars as exchange_calendar


NEW_YORK = ZoneInfo("America/New_York")
SEOUL = ZoneInfo("Asia/Seoul")
MarketScope = Literal["us", "kr", "all"]

KR_EXCHANGES = {"KRX", "KOSPI", "KOSDAQ"}
US_EXCHANGES = {
    "NASDAQ",
    "NYSE",
    "AMEX",
    "NYSE ARCA",
    "NYSEARCA",
    "ARCA",
}


def market_scope_for_security(ticker: str, exchange: str | None) -> Literal["us", "kr", "unknown"]:
    normalized_exchange = " ".join(str(exchange or "").upper().replace("_", " ").split())
    if normalized_exchange in KR_EXCHANGES:
        return "kr"
    if normalized_exchange in US_EXCHANGES:
        return "us"
    if ticker.strip().isdigit():
        return "kr"
    return "unknown"


@dataclass(frozen=True)
class MarketSessionState:
    session: str
    assessment_state: str
    market_date: date
    latest_completed_regular_session_date: date
    timezone_name: str


def _previous_weekday(value: date) -> date:
    candidate = value - timedelta(days=1)
    while candidate.weekday() >= 5:
        candidate -= timedelta(days=1)
    return candidate


@lru_cache(maxsize=2)
def _exchange_calendar(name: str):
    return exchange_calendar.get_calendar(name)


def _exchange_session_dates(calendar_name: str, value: date) -> tuple[bool, date]:
    """Return whether value is a session and the preceding completed session."""
    calendar = _exchange_calendar(calendar_name)
    try:
        if calendar.is_session(value):
            session = calendar.date_to_session(value)
            return True, calendar.previous_session(session).date()
        previous = calendar.date_to_session(value, direction="previous")
        return False, previous.date()
    except ValueError:
        # Packaged exchange calendars cover a bounded date range. Preserve the
        # previous conservative behavior outside that range.
        return value.weekday() < 5, _previous_weekday(value)


def us_market_session(as_of: datetime | None = None) -> MarketSessionState:
    current = as_of or datetime.now(timezone.utc)
    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)
    eastern = current.astimezone(NEW_YORK)
    is_session, previous_session = _exchange_session_dates("XNYS", eastern.date())
    if not is_session:
        return MarketSessionState(
            "closed",
            "final",
            eastern.date(),
            previous_session,
            NEW_YORK.key,
        )

    clock = eastern.time().replace(tzinfo=None)
    if clock < time(4, 0):
        session = "closed"
    elif clock < time(9, 30):
        session = "pre_market"
    elif clock < time(16, 0):
        session = "open"
    elif clock < time(20, 0):
        session = "after_hours"
    else:
        session = "closed"
    return MarketSessionState(
        session=session,
        assessment_state="provisional" if session == "open" else "final",
        market_date=eastern.date(),
        latest_completed_regular_session_date=(
            eastern.date()
            if session in {"after_hours", "closed"} and clock >= time(16, 0)
            else previous_session
        ),
        timezone_name=NEW_YORK.key,
    )


def korea_market_session(as_of: datetime | None = None) -> MarketSessionState:
    current = as_of or datetime.now(timezone.utc)
    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)
    seoul = current.astimezone(SEOUL)
    is_session, previous_session = _exchange_session_dates("XKRX", seoul.date())
    if not is_session:
        return MarketSessionState(
            "closed",
            "final",
            seoul.date(),
            previous_session,
            SEOUL.key,
        )
    clock = seoul.time().replace(tzinfo=None)
    if clock < time(8, 0):
        session = "pre_market"
    elif clock < time(15, 30):
        session = "open"
    elif clock < time(20, 0):
        session = "after_hours"
    else:
        session = "closed"
    return MarketSessionState(
        session=session,
        assessment_state="provisional" if session == "open" else "final",
        market_date=seoul.date(),
        latest_completed_regular_session_date=(
            seoul.date()
            if session in {"after_hours", "closed"} and clock >= time(15, 30)
            else previous_session
        ),
        timezone_name=SEOUL.key,
    )


def market_session_for_ticker(
    ticker: str,
    as_of: datetime | None = None,
) -> MarketSessionState:
    return korea_market_session(as_of) if ticker.isdigit() else us_market_session(as_of)
