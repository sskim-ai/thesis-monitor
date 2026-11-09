"""Ordinary HTTP -> dated native technical context. No new authority layer."""
from copy import copy
from datetime import date,datetime,timezone
import hashlib,json
from pathlib import Path
from urllib.parse import urlsplit
import httpx
from app.schemas.thesis import PriceContext
from app.services.market_session import market_session_for_ticker
from app.services.ohlcv_provider_integrity_service import inspect_normalized_ohlcv_rows


def safe_endpoint(value):
    url=urlsplit(value)
    if url.username or url.password or url.query or url.fragment:
        raise ValueError('endpoint_must_not_embed_credentials')
    if url.scheme!='https' and not (url.scheme=='http' and url.hostname in {'127.0.0.1','localhost','::1'}):
        raise ValueError('remote_TLS_or_loopback_required')
    return value.rstrip('/')


def write_new(path,raw):
    with path.open('xb') as f:f.write(raw)


def safe_service_diagnostic(response):
    try:value=response.json().get('diagnostic')
    except (ValueError,AttributeError):return None
    if not isinstance(value,dict):return None
    import re
    if (value.get('phase') not in {'pre_send','transport','http_status','json_decode','provider_code','local_call','local_serialization','local_validation'}
            or type(value.get('global_stop')) is not bool
            or not re.fullmatch('[A-Za-z0-9_]{1,64}',str(value.get('error_type','')))
            or not re.fullmatch('[A-Za-z0-9_]{1,32}',str(value.get('api_id','')))):
        return None
    return {k:value.get(k) for k in ['phase','error_type','upstream_status','api_id','physical_count','global_stop']}


async def fetch_daily(client,*,symbol,market,history_through,observed_at,output,
                      run_id,physical_remaining=44,count=300,require_budget=True):
    if (market not in {'kr','us'} or symbol.isdigit()!=(market=='kr')
            or type(count) is not int or not 5<=count<=1000
            or observed_at.tzinfo is None or client.source_observer is not None):
        raise ValueError('dated_daily_request_invalid')
    endpoint=safe_endpoint(client.settings.ohlcv_base_url)
    state=market_session_for_ticker(symbol,observed_at)
    if history_through>state.latest_completed_regular_session_date:
        raise ValueError('history_after_completed_session')
    if not 1<=physical_remaining<=44:raise ValueError('physical_budget_exhausted')
    output=Path(output)
    if output.exists() or any(p.is_symlink() for p in (output,*output.parents)):
        raise ValueError('new_plain_output_required')
    output.mkdir(parents=True)
    params=dict(symbol=symbol,market=market.upper(),periods='daily',count=count,
        adjusted='true',include_indicators='true',indicator_limit=5,
        include_investor_flows=str(market=='kr').lower())
    headers={'X-Research-Run':run_id,'X-Research-Remaining-Max':str(physical_remaining)}
    key=client.settings.ohlcv_api_key or client.settings.action_api_key
    if key:headers['X-API-Key']=key
    receipt=dict(symbol=symbol,market=market,params=params,observed_at=observed_at.isoformat(),
        history_through=history_through.isoformat(),scope='dated_technical_analysis',
        latest_completed_session=state.latest_completed_regular_session_date.isoformat(),
        current_price_qualified=False,valuation_qualified=False,NO_SEND=True)
    try:
        async with httpx.AsyncClient(base_url=endpoint,transport=client.transport,
                timeout=client.settings.ohlcv_timeout_seconds,follow_redirects=False) as h:
            response=await h.get('/ohlcv',params=params,headers=headers)
        raw=response.content;write_new(output/'response.body',raw)
        receipt.update(body_sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw),HTTP_status=response.status_code)
        diagnostic=safe_service_diagnostic(response)
        if diagnostic:receipt['service_diagnostic']=diagnostic
        if response.headers.get('X-Research-Budget-Protocol')=='simple-research-budget-v1':
            receipt['physical_cumulative_count']=int(response.headers.get('X-Research-Physical-Count','0'))
            receipt['budget_instance']=response.headers.get('X-Research-Budget-Instance')
        if len(raw)>8*1024**2:raise ValueError('response_size_exceeded')
        if response.status_code!=200:raise ValueError('service_HTTP_failed_no_retry')
        if require_budget and response.headers.get('X-Research-Budget-Protocol')!='simple-research-budget-v1':
            raise ValueError('service_cost_meter_not_available')
        receipt['physical_cumulative_count']=int(response.headers.get('X-Research-Physical-Count','0'))
        receipt['budget_instance']=response.headers.get('X-Research-Budget-Instance')
        receipt['service_identity']=dict(module_sha256=response.headers.get('X-Research-Module-SHA256'),
            loaded_definitions_sha256=response.headers.get('X-Research-Loaded-Definitions-SHA256'),
            pid=int(response.headers.get('X-Research-Service-PID','0')),
            maintenance=response.headers.get('X-Research-Maintenance'))
        payload=response.json()
        if payload.get('meta',{}).get('provider')!='kiwoom':raise ValueError('unexpected_provider')
        if set(payload.get('periods',{}))!={'daily'}:raise ValueError('daily_response_required')
        bars,supply,_=client._decode_period_payload(payload,ticker=symbol,period='daily',adjusted=True,
            response_body_sha256=receipt['body_sha256'])
        from app.services.dated_bar_admission import admit_rows
        original_returned=len(bars)
        original_dates=[date.fromisoformat(b['date']) for b in bars]
        bars,qa=admit_rows(bars,ticker=symbol,market=market,timeframe='daily',cutoff=state.latest_completed_regular_session_date)
        if qa:write_new(output/'DEBUG_SOURCE_EXCLUSION.json',json.dumps(qa,ensure_ascii=False,indent=2).encode())
        inspection=inspect_normalized_ohlcv_rows(bars,timeframe='daily')
        if not inspection.valid:raise ValueError('invalid_OHLCV_no_refetch')
        observed_day=observed_at.astimezone(__import__('zoneinfo').ZoneInfo(state.timezone_name)).date()
        dates=[date.fromisoformat(b['date']) for b in bars]
        plausible_dates=[d for d in original_dates if d<=observed_day]
        latest=max(plausible_dates) if plausible_dates else None
        # Dated historical chart evidence, not a FINAL flag/current close owner.
        # Only a row followed by a later plausible chart row can be consumed.
        def historical(row,timeframe,cutoff):
            d=date.fromisoformat(row['date'])
            marker=str(row.get('bar_state') or row.get('completion_state') or '').upper()
            return (timeframe=='daily' and latest is not None and d<latest
                and d<=history_through and d<=cutoff
                and marker not in {'PARTIAL','PROVISIONAL','OPEN','LIVE','UNCONFIRMED','UNKNOWN','INVALID'})
        usable=[b for b in bars if historical(b,'daily',state.latest_completed_regular_session_date)]
        write_new(output/'valid-historical-bars.json',json.dumps(usable,ensure_ascii=False,indent=2).encode())
        receipt.update(returned_count=original_returned,usable_count=len(usable),excluded_count=original_returned-len(usable),
            last_historical_session=usable[-1]['date'] if usable else None,
            completion_basis='later_chart_row_dated_historical_only',latest_raw_date=bars[-1]['date'] if bars else None)
        if not usable:raise ValueError('no_proven_historical_daily_rows')
        actual_as_of=date.fromisoformat(usable[-1]['date'])
        receipt.update(actual_historical_as_of=actual_as_of.isoformat(),
            effective_analysis_as_of=actual_as_of.isoformat())
        analysis=copy(client);analysis.completion_verifier=historical
        context=analysis._finalize_native_context(ticker=symbol,context=PriceContext(price_source_scope='dated_technical_only'),
            adjusted_bars={'daily':bars},technical_acquisition={'request_count':1,'retry_count':0,'failure_classes':[]},
            as_of=observed_at,price_structure_enabled=True,dated_analysis_as_of=actual_as_of)
        from app.services.kr_price_structure_selective_rollout_service import build_kr_price_structure_rollout_decision
        from app.services.us_price_structure_selective_rollout_service import build_us_price_structure_rollout_decision
        render=build_kr_price_structure_rollout_decision if market=='kr' else build_us_price_structure_rollout_decision
        rendered=render(context.chart.structure['price_structure_v3'],ticker=symbol,monitored_subject=True,enabled=True)
        if rendered.render_validation_errors:raise ValueError('SR_numeric_binding_invalid')
        receipt['status']='DATED_TECHNICAL_ANALYSIS_READY'
        preview=dict(receipt=receipt,technical_input=context.technical_context_payload(),
            SR=rendered.to_dict(),NO_SEND=rendered.section or 'Dated technical structure unavailable; no levels invented.')
        write_new(output/'NO_SEND.json',json.dumps(preview,ensure_ascii=False,indent=2).encode())
        write_new(output/'NO_SEND.md',('DATED TECHNICAL RESEARCH / NO-SEND\n'
            +'Historical as-of: '+actual_as_of.isoformat()+'\nObserved at: '+observed_at.isoformat()
            +'\n'+preview['NO_SEND']).encode())
        return context,receipt
    except Exception as exc:
        receipt['status']='FAILED_NO_RETRY';receipt['failure_type']=type(exc).__name__
        # Do not serialize HTTP exceptions: their URLs can contain credentials.
        if isinstance(exc,ValueError):receipt['failure_code']=str(exc) if str(exc).replace('_','').isalnum() else 'invalid_response'
        raise
    finally:
        write_new(output/'receipt.json',json.dumps(receipt,ensure_ascii=False,indent=2).encode())
