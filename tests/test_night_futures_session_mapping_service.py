from datetime import date, datetime

import pytest

from app.services.night_futures_session_mapping_service import (
    KST,
    map_latest_completed_krx_night_session,
)


@pytest.mark.parametrize(
    ("observed_at", "expected_regular", "expected_provider"),
    (
        (datetime(2026, 9, 2, 8, 20, tzinfo=KST), date(2026, 9, 1), date(2026, 9, 2)),
        (datetime(2026, 8, 10, 8, 20, tzinfo=KST), date(2026, 8, 7), date(2026, 8, 8)),
        (datetime(2026, 8, 18, 8, 20, tzinfo=KST), date(2026, 8, 14), date(2026, 8, 15)),
        (
            datetime(2027, 1, 4, 8, 20, tzinfo=KST),
            date(2026, 12, 30),
            date(2026, 12, 31),
        ),
    ),
)
def test_provider_end_date_mapping_uses_xkrx_calendar(
    observed_at: datetime,
    expected_regular: date,
    expected_provider: date,
) -> None:
    mapping = map_latest_completed_krx_night_session(observed_at)

    assert mapping is not None
    assert mapping.krx_regular_business_date == expected_regular
    assert mapping.ui_session_start_date == expected_regular
    assert mapping.provider_night_bas_dd == expected_provider
    assert mapping.provider_date_convention == "completed_session_end_date"


def test_before_close_does_not_treat_in_progress_session_as_final() -> None:
    mapping = map_latest_completed_krx_night_session(datetime(2026, 9, 2, 5, 30, tzinfo=KST))

    assert mapping is not None
    assert mapping.provider_night_bas_dd == date(2026, 9, 1)
    assert mapping.krx_regular_business_date == date(2026, 8, 31)


@pytest.mark.parametrize("us_session", (date(2026, 9, 1), date(2026, 8, 31)))
def test_us_session_date_is_metadata_not_mapping_input(us_session: date) -> None:
    mapping = map_latest_completed_krx_night_session(
        datetime(2026, 9, 2, 8, 20, tzinfo=KST),
        us_regular_session_date=us_session,
    )

    assert mapping is not None
    assert mapping.us_regular_session_date == us_session
    assert mapping.provider_night_bas_dd == date(2026, 9, 2)
