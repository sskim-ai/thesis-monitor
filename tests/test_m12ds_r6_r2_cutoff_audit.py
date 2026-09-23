from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from scripts.m12ds_r6_r2_cutoff_audit import calendar_times, session_at, task_time


def test_us_production_cutoff_is_still_after_hours_in_summer():
    result = session_at(datetime(2026, 9, 23, 8, 5, tzinfo=ZoneInfo("Asia/Seoul")), "US")
    assert result["exchange_local"] == "2026-09-22T19:05:00-04:00"
    assert result["intended_completed_session"] == "2026-09-22"
    assert result["after_hours_may_still_be_active"]
    assert result["schedule_is_not_source_finality"]


def test_winter_offset_not_hardcoded():
    result = session_at(datetime(2026, 1, 7, 8, 5, tzinfo=ZoneInfo("Asia/Seoul")), "US")
    assert result["exchange_local"] == "2026-01-06T18:05:00-05:00"


def test_kr_noon_not_production_postclose():
    noon = session_at(datetime(2026, 9, 23, 12, 53, tzinfo=ZoneInfo("Asia/Seoul")), "KR")
    production = session_at(datetime(2026, 9, 23, 16, 5, tzinfo=ZoneInfo("Asia/Seoul")), "KR")
    assert noon["regular_session_state"] == "INTRADAY"
    assert noon["intended_completed_session"] == "2026-09-22"
    assert production["regular_session_state"] == "POST_CLOSE"
    assert production["intended_completed_session"] == "2026-09-23"


def test_holiday_uses_exchange_calendar_not_weekday():
    result = session_at(datetime(2026, 9, 8, 8, 5, tzinfo=ZoneInfo("Asia/Seoul")), "US")
    assert result["regular_session_state"] == "NON_SESSION"
    assert result["intended_completed_session"] == "2026-09-04"


@pytest.mark.parametrize("value", [{}, {"StartCalendarInterval": {"Hour": 8}},
    {"StartCalendarInterval": {"Hour": 8, "Minute": 5, "Weekday": 1}},
    {"StartCalendarInterval": {"Hour": True, "Minute": 5}},
    {"StartCalendarInterval": {"Hour": 24, "Minute": 0}}])
def test_ambiguous_schedule_fail_closed(value):
    with pytest.raises(ValueError):
        calendar_times(value)


def test_task_rule_and_naive_cutoff_fail_closed():
    assert task_time("RRULE:FREQ=DAILY;BYHOUR=8;BYMINUTE=15") == (8, 15)
    with pytest.raises(ValueError):
        task_time("RRULE:FREQ=WEEKLY;BYHOUR=8;BYMINUTE=15")
    with pytest.raises(ValueError):
        session_at(datetime(2026, 9, 23), "US")
