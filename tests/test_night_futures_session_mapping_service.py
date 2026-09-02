from datetime import date, datetime

import pytest

from app.services.night_futures_session_mapping_service import (
    KST,
    US_MORNING_NIGHT_REFERENCE_DATE_CONTRACT,
    classify_provider_reference_date,
    map_latest_completed_krx_night_session,
    resolve_us_morning_night_reference_date,
)


@pytest.mark.parametrize(
    ("observed_at", "expected"),
    (
        (datetime(2026, 9, 2, 8, 0, tzinfo=KST), date(2026, 9, 1)),
        (datetime(2026, 9, 2, 8, 20, tzinfo=KST), date(2026, 9, 1)),
        (datetime(2026, 8, 10, 8, 0, tzinfo=KST), date(2026, 8, 7)),
        (datetime(2026, 8, 18, 8, 0, tzinfo=KST), date(2026, 8, 14)),
        (datetime(2026, 9, 28, 8, 0, tzinfo=KST), date(2026, 9, 23)),
        (datetime(2026, 9, 1, 8, 0, tzinfo=KST), date(2026, 8, 31)),
        (datetime(2027, 1, 4, 8, 0, tzinfo=KST), date(2026, 12, 30)),
        # US Labor Day is not an input; XKRX was open on 2026-09-07.
        (datetime(2026, 9, 8, 8, 0, tzinfo=KST), date(2026, 9, 7)),
    ),
)
def test_us_morning_reference_uses_previous_valid_xkrx_business_date(
    observed_at: datetime,
    expected: date,
) -> None:
    mapping = resolve_us_morning_night_reference_date(observed_at)

    assert mapping is not None
    assert mapping.contract == US_MORNING_NIGHT_REFERENCE_DATE_CONTRACT
    assert mapping.expected_reference_date == expected
    assert mapping.expected_reference_date < observed_at.date()
    assert mapping.exchange_calendar == "XKRX"
    assert mapping.session_clock_finality == "FINAL_BY_06_00_KST"


def test_finality_is_independent_from_us_morning_reference_date() -> None:
    before = resolve_us_morning_night_reference_date(
        datetime(2026, 9, 2, 5, 30, tzinfo=KST)
    )
    after = resolve_us_morning_night_reference_date(
        datetime(2026, 9, 2, 8, 0, tzinfo=KST)
    )

    assert before is not None and after is not None
    assert before.expected_reference_date == after.expected_reference_date == date(
        2026, 9, 1
    )
    assert before.session_clock_finality == "BEFORE_06_00_KST"
    assert after.session_clock_finality == "FINAL_BY_06_00_KST"


@pytest.mark.parametrize(
    ("provider_date", "expected_relation"),
    (
        (date(2026, 9, 1), "DATE_MATCH"),
        (date(2026, 8, 31), "STALE_PRIOR_REFERENCE"),
        (date(2026, 9, 2), "UNEXPECTED_FUTURE_REFERENCE"),
    ),
)
def test_provider_reference_date_relation_is_explicit(
    provider_date: date,
    expected_relation: str,
) -> None:
    assert (
        classify_provider_reference_date(provider_date, date(2026, 9, 1))
        == expected_relation
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
