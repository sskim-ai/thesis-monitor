from datetime import datetime
from zoneinfo import ZoneInfo

from app.services.market_session import korea_market_session, us_market_session


SEOUL = ZoneInfo("Asia/Seoul")
NEW_YORK = ZoneInfo("America/New_York")


def test_kr_substitute_holiday_uses_previous_exchange_session() -> None:
    state = korea_market_session(datetime(2026, 8, 17, 17, 0, tzinfo=SEOUL))

    assert state.session == "closed"
    assert state.assessment_state == "final"
    assert state.market_date.isoformat() == "2026-08-17"
    assert state.latest_completed_regular_session_date.isoformat() == "2026-08-14"


def test_kr_session_before_open_uses_previous_exchange_session() -> None:
    state = korea_market_session(datetime(2026, 8, 18, 7, 30, tzinfo=SEOUL))

    assert state.session == "pre_market"
    assert state.latest_completed_regular_session_date.isoformat() == "2026-08-14"


def test_kr_session_after_close_uses_same_exchange_session() -> None:
    state = korea_market_session(datetime(2026, 8, 18, 16, 5, tzinfo=SEOUL))

    assert state.session == "after_hours"
    assert state.latest_completed_regular_session_date.isoformat() == "2026-08-18"


def test_us_regular_session_behavior_is_unchanged() -> None:
    pre_market = us_market_session(
        datetime(2026, 8, 17, 8, 0, tzinfo=NEW_YORK)
    )
    after_hours = us_market_session(
        datetime(2026, 8, 17, 17, 0, tzinfo=NEW_YORK)
    )

    assert pre_market.session == "pre_market"
    assert pre_market.latest_completed_regular_session_date.isoformat() == "2026-08-14"
    assert after_hours.session == "after_hours"
    assert after_hours.latest_completed_regular_session_date.isoformat() == "2026-08-17"
