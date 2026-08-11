from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo


NEW_YORK = ZoneInfo("America/New_York")
SEOUL = ZoneInfo("Asia/Seoul")


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


def us_market_session(as_of: datetime | None = None) -> MarketSessionState:
    current = as_of or datetime.now(timezone.utc)
    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)
    eastern = current.astimezone(NEW_YORK)
    if eastern.weekday() >= 5:
        return MarketSessionState(
            "closed",
            "final",
            eastern.date(),
            _previous_weekday(eastern.date()),
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
            else _previous_weekday(eastern.date())
        ),
        timezone_name=NEW_YORK.key,
    )


def korea_market_session(as_of: datetime | None = None) -> MarketSessionState:
    current = as_of or datetime.now(timezone.utc)
    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)
    seoul = current.astimezone(SEOUL)
    if seoul.weekday() >= 5:
        return MarketSessionState(
            "closed",
            "final",
            seoul.date(),
            _previous_weekday(seoul.date()),
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
            else _previous_weekday(seoul.date())
        ),
        timezone_name=SEOUL.key,
    )


def market_session_for_ticker(
    ticker: str,
    as_of: datetime | None = None,
) -> MarketSessionState:
    return korea_market_session(as_of) if ticker.isdigit() else us_market_session(as_of)
