"""Source-only session projection. A query quote is not a regular-session close."""
from datetime import date
from decimal import Decimal,InvalidOperation
from zoneinfo import ZoneInfo
from app.services.ohlcv_provider_integrity_service import inspect_normalized_ohlcv_rows
from app.services.unified_snapshot_contract import digest

CONTRACT='price-session-projection-v1'

def project_price_session(rows, *, read, frozen_at, observed_at, source_pages):
    if (not rows or read.timeframe!='daily' or observed_at.utcoffset() is None
            or frozen_at.utcoffset() is None or observed_at<frozen_at or not source_pages
            or any(len(p['sha256'])!=64 for p in source_pages)):
        raise ValueError('price_session_source_custody_required')
    cutoff=observed_at.astimezone(ZoneInfo('Asia/Seoul' if read.market=='kr' else 'America/New_York')).date()
    ordered=sorted(rows,key=lambda r:r['date'])
    dates=[date.fromisoformat(str(r['date'])) for r in ordered]
    if len(dates)!=len(set(dates)) or any(d>cutoff for d in dates):
        raise ValueError('price_session_duplicate_or_future_date')
    latest=ordered[-1]
    inspection=inspect_normalized_ohlcv_rows(ordered,timeframe='daily',cutoff=cutoff)
    latest_check=inspect_normalized_ohlcv_rows([latest],timeframe='daily',cutoff=cutoff)
    violations=[i.violation.value for i in latest_check.issues]
    try:
        q=Decimal(str(latest['close']));hi=Decimal(str(latest['high']));lo=Decimal(str(latest['low']))
        valid_quote=q.is_finite() and q>0
    except (KeyError,ValueError,InvalidOperation):valid_quote=False
    # Only the close enclosure issue may be a quote/session mismatch; no other
    # OHLC violation becomes valid by separating this quote.
    outside=valid_quote and set(violations)<= {'HIGH_LT_CLOSE','LOW_GT_CLOSE'} and bool(violations)
    quote_semantics=('SESSION_UNCONFIRMED_OUTSIDE_REGULAR_RANGE' if outside else
        'PROVIDER_QUERY_TIME_QUOTE' if valid_quote else 'UNAVAILABLE_SOURCE_QUALITY')
    quote=dict(semantics=quote_semantics,value=latest.get('close') if valid_quote else None,
        session='UNCONFIRMED',trade_timestamp=None,observed_at=observed_at.isoformat(),
        observed_time_is_trade_time=False,regular_close=False,verified_extended_hours=False,
        basis_comparison='UNVERIFIED_ACROSS_FIELDS',price_difference=None,extended_hours_change_pct=None,
        finality_claim='NOT_CLAIMED',strict_close_eligible=False)
    invalid_dates={i.bar_date for i in inspection.issues}
    historical=[r for r in ordered if str(r['date']) not in invalid_dates and str(r['date'])<read.latest_completed_session]
    # Preserve only the uninterrupted valid suffix before the unresolved row.
    suffix=[]
    candidates=[r for r in ordered if str(r['date'])<str(latest['date'])]
    for r in reversed(candidates):
        if str(r['date']) in invalid_dates:break
        suffix.append(r)
    suffix.reverse()
    value=dict(contract=CONTRACT,security_id=read.canonical_security_id,market=read.market,
        exchange=read.exchange,currency='KRW' if read.market=='kr' else 'USD',
        owner=read.owner,provider=read.provider,api_id=read.api_id,adjusted=read.adjusted,
        target_trade_session=read.latest_completed_session,source_session=str(latest['date']),
        observed_at=observed_at.isoformat(),frozen_at=frozen_at.isoformat(),
        source_pages=source_pages,rows_sha256=digest(ordered),latest_row_sha256=digest(latest),
        quote=quote,latest_violations=violations,
        bar_status='CHART_OHLC_VALID_SESSION_NOT_CERTIFIED' if latest_check.valid else
            'UNRESOLVED_LATEST_BAR' if outside else 'TRUE_BAR_INTEGRITY_INVALID',
        unresolved_latest_bar=not latest_check.valid,
        historical_valid_rows=len(historical),valid_historical_suffix_count=len(suffix),
        latest_valid_session=str(suffix[-1]['date']) if suffix else None,
        historical_reference='TECHNICAL_REFERENCE_AS_OF_PRIOR_VALID_SESSION_ONLY',
        historical_reference_granted=False,continuity='CALENDAR_WINDOW_NOT_INDEPENDENTLY_GRANTED',
        missing_required_window=max(0,read.count-len(suffix)),
        qualified_current_bar_window=inspection.valid and len(ordered)>=read.count,
        regular_bar_close=None,extended_hours_verified=None,strict_completed_regular_close=None,
        current_source_authority=False,valuation_use=False,native_use=False,technical_signal=False)
    value['sha256']=digest(value)
    return value

def validate_price_session(value, *, rows, read, frozen_at, observed_at, source_pages):
    if value!=project_price_session(rows,read=read,frozen_at=frozen_at,observed_at=observed_at,source_pages=source_pages):
        raise ValueError('price_session_replay_identity_or_semantics_mismatch')
    return dict(status='PRICE_SESSION_COLD_RECOMPUTED',current_authority=False,
        strict_close=False,extended_hours_verified=False)

def render_price_session(value):
    core=dict(value);expected=core.pop('sha256')
    if digest(core)!=expected or any(value[k] for k in ('current_source_authority','valuation_use','native_use','technical_signal')):
        raise ValueError('price_session_display_scope_denied')
    return (f"{value['quote']['value']} {value['currency']} | "
        'Kiwoom query-time observation (trade session UNCONFIRMED) | '
        f"source {value['source_session']} | observed {value['observed_at']} | "
        'NOT a certified regular close or verified after-hours trade')
