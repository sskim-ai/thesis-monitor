"""Repeated canonical owner passes must not repeatedly fabricate identical calendars."""
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

from app.services import price_structure_wave_fibonacci_v3_service as owner


@pytest.mark.parametrize("market", ["US", "KR"])
def test_exact_range_calendar_reuse_preserves_sessions_and_period_bounds(monkeypatch, market):
    original = owner.exchange_calendar.get_calendar
    calls = []
    def observed(name, **kwargs):
        calls.append((name, kwargs))
        return original(name, **kwargs)
    monkeypatch.setattr(owner.exchange_calendar, "get_calendar", observed)
    starts = [date(2023, 1, 1), date(2013, 1, 1), date(2001, 1, 1)]
    end = date(2026, 10, 8)
    first = [owner._calendar_for_range(market, start=start, end=end)[1] for start in starts]
    second = [owner._calendar_for_range(market, start=start, end=end)[1] for start in starts]
    for start, before, after in zip(starts, first, second, strict=True):
        reference = original("XNYS" if market == "US" else "XKRX",
            start=start - timedelta(days=370), end=end + timedelta(days=370))
        assert before.schedule.equals(after.schedule)
        assert reference.schedule.equals(after.schedule)
        for timeframe in ("daily", "weekly", "monthly"):
            assert owner._bar_period_bounds(before, end, timeframe) == owner._bar_period_bounds(after, end, timeframe)
        at = datetime(2026, 10, 8, 16, 10, tzinfo=ZoneInfo("Asia/Seoul"))
        assert owner._latest_completed_session(before, at) == owner._latest_completed_session(after, at)
    assert len(calls) == len(starts)


def test_calendar_cache_is_bounded_and_factory_identity_is_part_of_key():
    calls = []
    def factory(name, **kwargs):
        value = object()
        calls.append((name, kwargs, value))
        return value
    first = owner._exact_range_calendar(factory, "XNYS", date(2020, 1, 1), date(2026, 1, 1))
    assert owner._exact_range_calendar(factory, "XNYS", date(2020, 1, 1), date(2026, 1, 1)) is first
    assert owner._exact_range_calendar(factory, "XKRX", date(2020, 1, 1), date(2026, 1, 1)) is not first
    assert owner._exact_range_calendar(factory, "XNYS", date(2020, 1, 1), date(2026, 1, 2)) is not first
    def other_factory(name, **kwargs):
        return object()
    assert owner._exact_range_calendar(other_factory, "XNYS", date(2020, 1, 1), date(2026, 1, 1)) is not first
    assert len(calls) == 3
    assert owner._exact_range_calendar.cache_info().maxsize == 32
