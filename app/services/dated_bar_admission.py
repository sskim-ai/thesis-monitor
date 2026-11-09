"""C22A v2 dated row selection. QA stays separate from technical/model output."""
from datetime import date
import re
from app.services.ohlcv_provider_integrity_service import inspect_normalized_ohlcv_rows
from app.services.unified_snapshot_contract import digest

POLICY='DATED_ISOLATED_PRICE_ROW_ADMISSION_V2'
PRICE_RELATIONS={'HIGH_LT_OPEN','HIGH_LT_CLOSE','LOW_GT_OPEN','LOW_GT_CLOSE','LOW_GT_HIGH'}


def two_year_threshold(cutoff):
    try:return cutoff.replace(year=cutoff.year-2)
    except ValueError:return cutoff.replace(year=cutoff.year-2,day=28)


def admit_rows(bars,*,ticker,market,timeframe,cutoff):
    inspection=inspect_normalized_ohlcv_rows(bars,timeframe=timeframe)
    if inspection.valid:return list(bars),None
    captures=set()
    for row in bars:
        cap=row.get('_native_capture',{})
        if (cap.get('code')!=ticker or cap.get('market')!=market or cap.get('timeframe')!=timeframe
                or cap.get('adjusted') is not True or not re.fullmatch('[a-f0-9]{64}',cap.get('response_body_sha256') or '')
                or digest({k:v for k,v in row.items() if k not in {'_native_capture','supply_demand'}})!=cap.get('normalized_bar_sha256')):
            raise ValueError('source_binding_mismatch_no_row_admission')
        captures.add((cap.get('provider'),cap.get('exchange'),cap.get('response_body_sha256')))
    issues=inspection.issues;bad_dates={i.bar_date for i in issues}
    if len(captures)!=1:raise ValueError('source_binding_mismatch_no_row_admission')
    if len(bad_dates)!=1 or not issues or any(str(i.violation) not in PRICE_RELATIONS for i in issues):
        raise ValueError('not_isolated_price_relation_error')
    bad=next(iter(bad_dates));bad_day=date.fromisoformat(bad)
    if bad_day<=two_year_threshold(cutoff):kind='OLD_ISOLATED_PRICE_ROW'
    elif bad==max(row['date'] for row in bars):kind='RECENT_LATEST_PRICE_ROW_DATED_HISTORY_ONLY'
    else:raise ValueError('recent_nonlatest_error_not_admitted')
    accepted=[row for row in bars if row['date']!=bad]
    if len(bars)-len(accepted)!=1 or not inspect_normalized_ohlcv_rows(accepted,timeframe=timeframe).valid:
        raise ValueError('remaining_source_invalid')
    qa=dict(policy=POLICY,source_sha256=next(iter(captures))[2],ticker=ticker,timeframe=timeframe,
        cutoff=cutoff.isoformat(),bad_date=bad,violations=sorted({str(i.violation) for i in issues}),
        excluded=1,remaining_normal_rows=len(accepted),kind=kind)
    return accepted,qa
