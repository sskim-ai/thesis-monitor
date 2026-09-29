"""Immutable source view for a completed-session proof, before any indicators."""
from copy import deepcopy
from datetime import date, datetime

from app.services.price_structure_wave_fibonacci_v3_service import (
    _bar_period_bounds, _calendar_for_range, _latest_completed_session,
)
from app.services.unified_snapshot_contract import digest
from app.services.ohlcv_provider_integrity_service import inspect_normalized_ohlcv_rows

CONTRACT = "eligible-completed-session-bar-set-v1"


def eligible_completed_roles(roles, *, ticker, market, cutoff, observed_at,
                             adjustment_basis="provider_adjusted_price_v1"):
    if adjustment_basis != "provider_adjusted_price_v1":
        raise ValueError("completed_bar_adjustment_basis_mismatch")
    parsed = {}
    for role, rows in roles.items():
        dates = [date.fromisoformat(str(r["date"])[:10]) for r in rows]
        if dates != sorted(set(dates)):
            raise ValueError("completed_bar_duplicate_or_ordering")
        parsed[role] = dates
    daily = roles["adjusted_daily"]
    if cutoff not in parsed["adjusted_daily"]:
        raise ValueError("completed_bar_target_missing")
    _, calendar = _calendar_for_range(market.upper(),
        start=min(d for dates in parsed.values() for d in dates),
        end=max(max(d for dates in parsed.values() for d in dates), cutoff))
    at = datetime.fromisoformat(observed_at)
    if at.utcoffset() is None or _latest_completed_session(calendar, at) != cutoff:
        raise ValueError("completed_bar_target_calendar_mismatch")
    selected = {}
    receipts = {}
    safe_daily = [deepcopy(r) for r, d in zip(daily, parsed["adjusted_daily"], strict=True) if d <= cutoff]
    for role, rows in roles.items():
        frequency = role.removeprefix("adjusted_") if role.startswith("adjusted_") else "weekly"
        derived, excluded, included = [], [], []
        for row, day in zip(rows, parsed[role], strict=True):
            start, end = _bar_period_bounds(calendar, day, frequency)
            if day > cutoff or end > cutoff:
                excluded.append({"date": str(day), "reason": "OUT_OF_SCOPE_CURRENT_OR_FUTURE_SESSION"})
            else:
                included.append(deepcopy(row))
        if frequency == "daily":
            included = safe_daily
        elif role.startswith("adjusted_"):
            start, end = _bar_period_bounds(calendar, cutoff, frequency)
            if end > cutoff:
                part = [r for r in safe_daily if start <= date.fromisoformat(r["date"][:10]) <= cutoff]
                expected = [s.date().isoformat() for s in calendar.sessions_in_range(start, cutoff)]
                if [r["date"][:10] for r in part] != expected:
                    raise ValueError("completed_bar_partial_period_daily_coverage_missing")
                if not inspect_normalized_ohlcv_rows(part, timeframe="daily", cutoff=cutoff).valid:
                    raise ValueError("completed_bar_partial_period_daily_integrity")
                row = dict(date=str(start), open=part[0]["open"], close=part[-1]["close"],
                    high=max(r["high"] for r in part), low=min(r["low"] for r in part),
                    volume=sum(r["volume"] for r in part), bar_state="PARTIAL")
                if all(r.get("value") is not None for r in part):
                    row["value"] = sum(r["value"] for r in part)
                included.append(row)
                derived.append(dict(period_start=str(start), period_end=str(end),
                    as_of=str(cutoff), input_dates=expected, input_sha256=digest(part),
                    formula="OHLC_FIRST_MAX_MIN_LAST_SUM_VOLUME", output_sha256=digest(row)))
        selected[role] = included
        receipts[role] = dict(frequency=frequency,
            adjustment_basis=adjustment_basis if role.startswith("adjusted_") else "unadjusted",
            raw_corpus_sha256=digest(rows), excluded_rows=excluded,
            included_dates=[r["date"] for r in included], derived_periods=derived,
            eligible_bar_set_sha256=digest(included))
    receipt = dict(contract=CONTRACT, ticker=ticker, market=market, target_session=str(cutoff),
        raw_corpus_sha256=digest(roles), roles=receipts, eligible_bar_set_sha256=digest(selected))
    return selected, receipt
