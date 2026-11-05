"""Dated research projection through the existing external indicator engine.

No Provider/API boot, indicator formulas, source-use grants or investment stance.
"""
import gzip,hashlib,importlib.util,json,re
from datetime import date,datetime,timedelta
from functools import lru_cache
from pathlib import Path
from zoneinfo import ZoneInfo
import pandas as pd
from app.services.ohlcv_provider_integrity_service import inspect_normalized_ohlcv_rows
from app.services.market_session import exchange_calendar
from app.services.unified_snapshot_contract import digest,encoded

CONTRACT='historical-original-indicator-projection-v1'

def load_engine(root,expected_sha256):
    root=Path(root).absolute();path=root/'app/indicators/technical.py'
    if any(p.is_symlink() for p in (path,*path.parents)):
        raise ValueError('indicator_engine_symlink_denied')
    raw=path.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=expected_sha256:
        raise ValueError('indicator_engine_source_changed')
    spec=importlib.util.spec_from_file_location('original_ohlcv_technical_'+expected_sha256,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module

def requirements(columns,timeframe):
    unit={'daily':'TRADING_DAY_BARS','weekly':'WEEK_BARS','monthly':'MONTH_BARS'}[timeframe]
    out={}
    for key in columns:
        if re.fullmatch(r'MA\d+',key):n=int(key[2:]);minimum=n
        elif key.startswith('BB_'):n=int(key.split('_')[1]);minimum=n
        elif key.startswith('ENV_'):n=int(key.split('_')[1]);minimum=n
        elif key=='RSI14':n=14;minimum=15
        elif key.startswith('MACD_OSC_'):n=int(key.split('_')[3]);minimum=1
        elif key.startswith('MACD'):n=26;minimum=1
        elif key in ('VOLUME_MA20','VOLUME_RATIO_20'):n=20;minimum=1
        elif key in ('RETURN_20D','RETURN_60D'):n=int(key.split('_')[1][:-1]);minimum=n+1
        elif key=='DRAWDOWN_52W':n=252;minimum=1
        else:raise ValueError('indicator_engine_unreviewed_column')
        out[key]=dict(minimum_numeric_rows=minimum,coverage_reference_bars=n,period_unit=unit,
            label=f'{key}: {n} {unit}',reference_is_stability_guarantee=False)
    return out

def _period(d,timeframe):
    if timeframe=='daily':return d.isoformat()
    if timeframe=='weekly':return (d-timedelta(days=d.weekday())).isoformat()
    return d.replace(day=1).isoformat()

@lru_cache(maxsize=128)
def _calendar_periods(market,start,end,timeframe):
    cal=exchange_calendar.get_calendar('XKRX' if market=='kr' else 'XNYS',
        start=date.fromisoformat(start)-timedelta(days=40),end=date.fromisoformat(end)+timedelta(days=40))
    sessions=cal.sessions_in_range(start,end)
    keys=list(dict.fromkeys(_period(s.date(),timeframe) for s in sessions))
    return {key:i for i,key in enumerate(keys)}

def project_indicators(rows,*,read,observed_at,generation,raw_sha256,engine,algorithm_sha256):
    if (not rows or observed_at.utcoffset() is None or not raw_sha256
            or any(not re.fullmatch(r'[a-f0-9]{64}',s) for s in raw_sha256)
            or read.owner!='ohlcv_analyst.KiwoomProvider.get_bars'):
        raise ValueError('indicator_original_source_identity_required')
    ordered=sorted(rows,key=lambda r:r['date']);cutoff=observed_at.astimezone(ZoneInfo('Asia/Seoul' if read.market=='kr' else 'America/New_York')).date()
    counts={}
    for row in ordered:counts[str(row.get('date'))]=counts.get(str(row.get('date')),0)+1
    parsed=[]
    for row in ordered:
        try:d=date.fromisoformat(str(row['date']))
        except (KeyError,ValueError):continue
        if d<=cutoff:parsed.append(d)
    periods=_calendar_periods(read.market,min(parsed).replace(day=1).isoformat(),cutoff.isoformat(),read.timeframe) if parsed else {}
    segments=[];current=[];previous=None;invalid=[];gaps=[]
    for row in ordered:
        quality=inspect_normalized_ohlcv_rows([row],timeframe=read.timeframe,cutoff=cutoff)
        reason=[i.violation.value for i in quality.issues]
        d=str(row.get('date'));period=None
        try:period=_period(date.fromisoformat(d),read.timeframe)
        except ValueError:pass
        if counts[d]!=1:reason.append('DUPLICATE_SOURCE_LABEL')
        if period not in periods:reason.append('NONTRADING_SOURCE_PERIOD')
        if reason:
            if current:segments.append(current)
            current=[];previous=None;invalid.append(dict(date=d,reasons=reason,row_sha256=digest(row)));continue
        index=periods[period]
        if previous is not None and index!=previous+1:
            if current:segments.append(current)
            current=[];gaps.append(dict(date=d,reason='INSUFFICIENT_CONTIGUOUS_VALID_HISTORY'))
        current.append(row);previous=index
    if current:segments.append(current)
    derived=[]
    for segment_id,segment in enumerate(segments,1):
        calculated=engine.add_indicators(pd.DataFrame(segment))
        for ordinal,(_,result) in enumerate(calculated.iterrows(),1):
            derived.append(dict(date=str(result['date']),segment=segment_id,contiguous_valid_bars=ordinal,
                row_sha256=digest(segment[ordinal-1]),indicators=engine.indicator_dict(result)))
    descriptor=requirements(engine.INDICATOR_COLUMNS,read.timeframe)
    last=derived[-1] if derived else None
    availability={}
    for key,rule in descriptor.items():
        n=last['contiguous_valid_bars'] if last else 0
        number=last['indicators'][key] if last else None
        availability[key]=dict(**rule,numeric_available=number is not None,
            status='UNAVAILABLE' if number is None else 'CALCULATED_WITH_LIMITED_HISTORY' if n<rule['coverage_reference_bars'] else 'CALCULATED_REFERENCE_SPAN_COVERED',
            reason='INSUFFICIENT_CONTIGUOUS_VALID_HISTORY' if n<rule['minimum_numeric_rows'] else
                'ORIGINAL_ENGINE_NULL_OR_MISSING_VOLUME_OR_ZERO_DENOMINATOR' if number is None else
                'REFERENCE_COVERAGE_NOT_NUMERIC_GATE',
            ewm_stability='NOT_CERTIFIED' if key.startswith('MACD') else 'NOT_APPLICABLE')
    payload=dict(contract=CONTRACT,security_id=read.canonical_security_id,ticker=read.subject,market=read.market,
        timeframe=read.timeframe,role=read.role,adjusted=read.adjusted,
        basis='ADJUSTED_CHART' if read.adjusted else 'UNADJUSTED_CHART',generation=generation,
        observed_at=observed_at.isoformat(),target_session=read.latest_completed_session,
        INDICATOR_SOURCE='ohlcv-analyst',algorithm_sha=algorithm_sha256,adapter_sha=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        original_raw_sha=raw_sha256,original_rows_sha=digest(ordered),valid_bars=len(derived),invalid_rows=invalid,gaps=gaps,
        last_valid_as_of=last['date'] if last else None,
        scope='AS_OF_HISTORICAL_ONLY' if not last or last['date']!=str(ordered[-1]['date']) else 'LATEST_VALID_SNAPSHOT',
        technical_window_status='SEGMENTED_VALID_SOURCE_ROWS_ONLY',provider_period_label_authority='UNVERIFIED' if read.timeframe!='daily' else 'SOURCE_DATE_ONLY',
        quote_finality='NOT_CLAIMED',current_eligibility=False,technical_signal=False,valuation_use=False,native_use=False,
        independent_evidence_group='UNADJUSTED_WEEKLY_SOURCE_ONLY_NOT_ADDITIONAL_ADJUSTED_TECHNICAL_VOTE' if not read.adjusted else read.role,
        investor_flows='NOT_FETCHED',indicator_requirements=descriptor,latest_availability=availability,
        bars=derived,pandas_version=pd.__version__)
    return payload

def cached_project(cache,rows,**kwargs):
    cache=Path(cache);cache.mkdir(mode=0o700,parents=True,exist_ok=True)
    identity=dict(rows=digest(rows),read=kwargs['read'].model_dump(mode='json'),observed_at=kwargs['observed_at'].isoformat(),
        generation=kwargs['generation'],raw_sha256=kwargs['raw_sha256'],algorithm_sha=kwargs['algorithm_sha256'],
        adapter_sha=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),pandas=pd.__version__)
    key=digest(identity);path=cache/(key+'.json.gz')
    if path.exists():
        with gzip.open(path,'rb') as f:value=json.load(f)
        if value['identity']!=identity or digest(value['projection'])!=value['projection_sha256']:
            raise ValueError('indicator_cache_identity_or_hash_mismatch')
        return path,value,False
    projection=project_indicators(rows,**kwargs)
    value=dict(identity=identity,projection=projection,projection_sha256=digest(projection))
    with path.open('xb') as file:
        with gzip.GzipFile(fileobj=file,mode='wb',mtime=0,compresslevel=1) as z:z.write(encoded(value))
    path.chmod(0o600)
    return path,value,True
