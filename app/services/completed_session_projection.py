"""Opt-in source-only projection; historical normalizer and role gates unchanged."""
from datetime import date

from app.services.market_session import korea_market_session, us_market_session
from app.services.ohlcv_provider_integrity_service import inspect_normalized_ohlcv_rows
from app.services.unified_snapshot_contract import digest

CONTRACT = "completed-session-before-count-projection-v1"


def project_completed_rows(rows, *, read, cutoff, source_pages):
    """Input is every singleton-parsed original row, before owner dedup/truncation.

    This deterministic projection does not issue authority. Its trusted caller
    must bind original raw/parser replay, live dispatcher and current parent.
    """
    if read.timeframe != "daily" or not source_pages or cutoff.utcoffset() is None:
        raise ValueError("completed_projection_daily_source_required")
    session = (korea_market_session if read.market == "kr" else us_market_session)(cutoff)
    target = session.latest_completed_regular_session_date.isoformat()
    if read.latest_completed_session != target:
        raise ValueError("completed_projection_calendar_mismatch")
    dates = [str(r["date"]) for r in rows]
    if not rows or len(set(dates)) != len(dates):
        raise ValueError("completed_projection_duplicate_or_empty")
    for value in dates:
        if date.fromisoformat(value).isoformat() != value:
            raise ValueError("completed_projection_invalid_date")
    if dates != sorted(dates) and dates != sorted(dates, reverse=True):
        raise ValueError("completed_projection_page_order")
    query_date = date.fromisoformat(read.query_date[:4]+'-'+read.query_date[4:6]+'-'+read.query_date[6:8])
    if max(dates) > query_date.isoformat():
        raise ValueError("completed_projection_future_beyond_request")
    completed = sorted((dict(r) for r in rows if r["date"] <= target), key=lambda r:r["date"])
    inspection = inspect_normalized_ohlcv_rows(completed, timeframe="daily", cutoff=date.fromisoformat(target))
    if not inspection.valid:
        raise ValueError("completed_projection_original_quality_failed")
    if len(completed) < read.count or completed[-1]["date"] != target:
        raise ValueError("completed_projection_history_or_current_session_gap")
    selected = completed[-read.count:]
    receipt = dict(contract=CONTRACT, scope="SCOPED_SOURCE_ONLY", entry_id=read.entry_id,
        security_id=read.canonical_security_id, adjusted=read.adjusted,
        currency="KRW" if read.market=="kr" else "USD", target_session=target,
        cutoff=cutoff.isoformat(), calendar="XKRX" if read.market=="kr" else "XNYS",
        source_pages=source_pages, raw_parsed_rows=len(rows), completed_unique_rows=len(completed),
        excluded=[dict(date=r["date"],row_sha256=digest(r),reason="AFTER_COMPLETED_SESSION") for r in rows if r["date"]>target],
        requested_rows=read.count, selected_rows=len(selected), oldest_selected=selected[0]["date"],
        all_parsed_sha256=digest(rows), selected_sha256=digest(selected),
        original_quality_fingerprint=inspection.payload_fingerprint,
        raw_rewritten=False, technical_signal=False, economic_use=False, native_use=False)
    return selected, receipt


def finite_history(read, *, available_rows, exhausted, first_date, last_date):
    """Observed finite source history is not independent legal listing-date proof."""
    return dict(status="FINITE_LISTING_HISTORY" if exhausted and available_rows<read.count else "HISTORY_NOT_PROVEN_FINITE",
        available_rows=available_rows,requested_rows=read.count,first_source_date=first_date,last_source_date=last_date,
        legal_listing_date="NOT_INDEPENDENTLY_VERIFIED",timeframe=read.timeframe,
        period_anchor=read.timeframe in ("weekly","monthly"), adjustment=read.adjusted,
        role_use="HISTORY_LIMIT_UNAVAILABLE" if available_rows<read.count else "REQUIRES_OWNER_QUALIFICATION",
        underlying_price_substitution=False, native_use=False)
