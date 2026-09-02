from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

import exchange_calendars as exchange_calendar


NIGHT_FUTURES_SESSION_DATE_CONTRACT = "night-futures-session-date-v2"
US_MORNING_NIGHT_REFERENCE_DATE_CONTRACT = (
    "us-morning-night-reference-date-v3"
)
KST = ZoneInfo("Asia/Seoul")
NIGHT_SESSION_COMPLETION_TIME = time(6, 0)


@dataclass(frozen=True)
class NightFuturesSessionMapping:
    contract: str
    observation_time_kst: datetime
    us_regular_session_date: date | None
    krx_regular_business_date: date
    night_session_business_date: date
    provider_night_bas_dd: date
    provider_date_convention: str
    ui_session_start_date: date
    session_clock_finality: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class UsMorningNightReferenceDate:
    contract: str
    observation_time_kst: datetime
    us_regular_session_date: date | None
    expected_reference_date: date
    exchange_calendar: str
    reference_rule: str
    session_clock_finality: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def resolve_us_morning_night_reference_date(
    observation_time: datetime,
    *,
    us_regular_session_date: date | None = None,
    max_lookback_days: int = 20,
) -> UsMorningNightReferenceDate | None:
    """Resolve the product reference date for the US morning digest.

    The date owner is XKRX, not the US session and not calendar subtraction.
    Finality remains an independent wall-clock condition.
    """
    observation_kst = (
        observation_time.replace(tzinfo=KST)
        if observation_time.tzinfo is None
        else observation_time.astimezone(KST)
    )
    try:
        calendar = exchange_calendar.get_calendar("XKRX")
        for days_back in range(1, max_lookback_days + 1):
            candidate = observation_kst.date() - timedelta(days=days_back)
            if not calendar.is_session(candidate):
                continue
            return UsMorningNightReferenceDate(
                contract=US_MORNING_NIGHT_REFERENCE_DATE_CONTRACT,
                observation_time_kst=observation_kst,
                us_regular_session_date=us_regular_session_date,
                expected_reference_date=candidate,
                exchange_calendar="XKRX",
                reference_rule=(
                    "latest_valid_xkrx_business_date_strictly_before_kst_date"
                ),
                session_clock_finality=(
                    "FINAL_BY_06_00_KST"
                    if observation_kst.timetz().replace(tzinfo=None)
                    >= NIGHT_SESSION_COMPLETION_TIME
                    else "BEFORE_06_00_KST"
                ),
            )
    except (ValueError, IndexError, TypeError):
        return None
    return None


def classify_provider_reference_date(
    provider_raw_bas_dd: date | None,
    expected_reference_date: date | None,
) -> str:
    if provider_raw_bas_dd is None or expected_reference_date is None:
        return "UNVERIFIED"
    if provider_raw_bas_dd == expected_reference_date:
        return "DATE_MATCH"
    if provider_raw_bas_dd < expected_reference_date:
        return "STALE_PRIOR_REFERENCE"
    return "UNEXPECTED_FUTURE_REFERENCE"


def map_latest_completed_krx_night_session(
    observation_time: datetime,
    *,
    us_regular_session_date: date | None = None,
    max_lookback_days: int = 10,
) -> NightFuturesSessionMapping | None:
    observation_kst = (
        observation_time.replace(tzinfo=KST)
        if observation_time.tzinfo is None
        else observation_time.astimezone(KST)
    )
    latest_possible_end = observation_kst.date()
    if observation_kst.timetz().replace(tzinfo=None) < NIGHT_SESSION_COMPLETION_TIME:
        latest_possible_end -= timedelta(days=1)
    try:
        calendar = exchange_calendar.get_calendar("XKRX")
        for days_back in range(max_lookback_days):
            provider_end_date = latest_possible_end - timedelta(days=days_back)
            regular_business_date = provider_end_date - timedelta(days=1)
            if not calendar.is_session(regular_business_date):
                continue
            return NightFuturesSessionMapping(
                contract=NIGHT_FUTURES_SESSION_DATE_CONTRACT,
                observation_time_kst=observation_kst,
                us_regular_session_date=us_regular_session_date,
                krx_regular_business_date=regular_business_date,
                night_session_business_date=provider_end_date,
                provider_night_bas_dd=provider_end_date,
                provider_date_convention="completed_session_end_date",
                ui_session_start_date=regular_business_date,
                session_clock_finality="COMPLETED_BY_06_00_KST",
            )
    except (ValueError, IndexError, TypeError):
        return None
    return None
