from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

import exchange_calendars as exchange_calendar


NIGHT_FUTURES_SESSION_DATE_CONTRACT = "night-futures-session-date-v2"
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
