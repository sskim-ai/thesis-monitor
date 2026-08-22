from datetime import date, datetime
from zoneinfo import ZoneInfo

from app.jobs.probe_krx_night_futures import expected_latest_completed_krx_session
from app.services.xkrx_role_target_service import resolve_xkrx_role_target


KST = ZoneInfo("Asia/Seoul")


def _at(day: int, hour: int, minute: int) -> datetime:
    return datetime(2026, 8, day, hour, minute, tzinfo=KST)


def _at_date(year: int, month: int, day: int, hour: int, minute: int) -> datetime:
    return datetime(year, month, day, hour, minute, tzinfo=KST)


def test_saturday_roles_resolve_target_before_wallclock_session_gate() -> None:
    night = resolve_xkrx_role_target(
        _at(22, 8, 45),
        "night_futures_post_deadline_observer",
    )
    publication = resolve_xkrx_role_target(
        _at(22, 8, 5),
        "krx_next_morning_publication",
    )
    same_day = resolve_xkrx_role_target(
        _at(22, 16, 5),
        "krx_same_day_publication",
    )

    assert night.target_session_date == expected_latest_completed_krx_session(
        date(2026, 8, 22)
    )
    assert night.target_xkrx_business_date == date(2026, 8, 21)
    assert night.observation_eligible is True
    assert night.calendar_evidence["wallclock_is_xkrx_session"] is False
    assert publication.target_session_date == date(2026, 8, 21)
    assert publication.observation_eligible is True
    assert same_day.observation_eligible is False
    assert same_day.skip_reason == "no_valid_role_target"


def test_sunday_and_monday_roles_use_exchange_calendar_not_date_subtraction() -> None:
    sunday_night = resolve_xkrx_role_target(
        _at(23, 8, 45),
        "night_futures_post_deadline_observer",
    )
    sunday_publication = resolve_xkrx_role_target(
        _at(23, 8, 5),
        "krx_next_morning_publication",
    )
    monday_publication = resolve_xkrx_role_target(
        _at(24, 8, 5),
        "krx_next_morning_publication",
    )

    assert sunday_night.target_session_date == date(2026, 8, 22)
    assert sunday_publication.target_session_date == date(2026, 8, 21)
    assert monday_publication.target_session_date == date(2026, 8, 21)


def test_holiday_and_day_after_holiday_keep_prior_completed_target() -> None:
    holiday_morning = resolve_xkrx_role_target(
        _at(17, 8, 5),
        "krx_next_morning_publication",
    )
    holiday_close = resolve_xkrx_role_target(
        _at(17, 16, 5),
        "krx_same_day_publication",
    )
    day_after = resolve_xkrx_role_target(
        _at(18, 8, 5),
        "krx_next_morning_publication",
    )

    assert holiday_morning.target_session_date == date(2026, 8, 14)
    assert holiday_morning.observation_eligible is True
    assert holiday_close.observation_eligible is False
    assert day_after.target_session_date == date(2026, 8, 14)


def test_consecutive_holidays_and_weekend_traverse_to_last_xkrx_session() -> None:
    saturday = resolve_xkrx_role_target(
        _at_date(2026, 9, 26, 8, 5),
        "krx_next_morning_publication",
    )
    monday = resolve_xkrx_role_target(
        _at_date(2026, 9, 28, 8, 5),
        "krx_next_morning_publication",
    )

    assert saturday.target_session_date == date(2026, 9, 23)
    assert monday.target_session_date == date(2026, 9, 23)
    assert saturday.observation_eligible is True
    assert monday.observation_eligible is True


def test_year_end_special_closure_uses_exchange_calendar_target() -> None:
    morning = resolve_xkrx_role_target(
        _at_date(2026, 12, 31, 8, 5),
        "krx_next_morning_publication",
    )
    close = resolve_xkrx_role_target(
        _at_date(2026, 12, 31, 16, 5),
        "krx_same_day_publication",
    )

    assert morning.target_session_date == date(2026, 12, 30)
    assert morning.observation_eligible is True
    assert close.observation_eligible is False
    assert close.skip_reason == "no_valid_role_target"


def test_night_production_and_observer_share_canonical_target_resolver() -> None:
    production = resolve_xkrx_role_target(_at(22, 8, 20), "night_futures_production")
    observer = resolve_xkrx_role_target(
        _at(22, 9, 15),
        "night_futures_post_deadline_observer",
    )

    assert production.target_session_date == observer.target_session_date
    assert production.target_xkrx_business_date == observer.target_xkrx_business_date
    assert production.calendar_evidence["target_basis"] == (
        "night-futures-session-basis-v1"
    )
