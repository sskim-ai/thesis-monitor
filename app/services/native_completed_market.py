"""Completed-session selection for the opt-in native US Market bridge only."""
from datetime import date, datetime, timezone

from app.services.market_session import us_market_session


def select_completed_daily_rows(rows, *, target_session, count):
    target = date.fromisoformat(target_session)
    if count != 2:
        raise ValueError('native_market_exact_two_completed_rows_required')
    expected_prior = us_market_session(datetime.combine(target, datetime.min.time(), timezone.utc)
                                       ).latest_completed_regular_session_date.isoformat()
    dates = [row['date'] for row in rows]
    if len(dates) != len(set(dates)):
        raise ValueError('native_market_duplicate_session')
    by_date = {r['date']: r for r in rows}
    if target_session not in by_date:
        raise ValueError('native_market_target_completed_session_missing')
    if expected_prior not in by_date:
        raise ValueError('native_market_adjacent_completed_baseline_missing')
    return [by_date[expected_prior], by_date[target_session]]
