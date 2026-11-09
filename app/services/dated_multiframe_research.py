"""Reuse dated D; ordinary HTTP W/M; calendar-bounded historical technical input."""
from calendar import monthrange
from copy import copy
from datetime import date,timedelta
import hashlib,json
from pathlib import Path
import httpx
from app.schemas.thesis import PriceContext
from app.services.dated_technical_research import safe_endpoint,write_new
from app.services.market_session import market_session_for_ticker,_exchange_calendar
from app.services.ohlcv_provider_integrity_service import inspect_normalized_ohlcv_rows
from app.services.provider_native_technical import MAX_COUNTS,FORMULAS


def period_end(label,timeframe,market):
    """Interpret an unchanged label by its containing calendar period."""
    if timeframe=='daily':return label
    if timeframe=='weekly':end=label+timedelta(days=6-label.weekday())
    elif timeframe=='monthly':end=label.replace(day=monthrange(label.year,label.month)[1])
    else:raise ValueError('unsupported_timeframe')
    calendar=_exchange_calendar('XKRX' if market=='kr' else 'XNYS')
    if end<calendar.first_session.date() or end>calendar.last_session.date():
        import exchange_calendars
        calendar=exchange_calendars.get_calendar('XKRX' if market=='kr' else 'XNYS',
            start=label-timedelta(days=370),end=end+timedelta(days=370))
    return calendar.date_to_session(end,direction='previous').date()


def select_historical(bars,*,timeframe,market,cutoff):
    inspection=inspect_normalized_ohlcv_rows(bars,timeframe=timeframe)
    if bars and not inspection.valid:raise ValueError('invalid_historical_OHLCV')
    labels=[date.fromisoformat(b['date']) for b in bars]
    latest=max(labels) if labels else None
    used=[];excluded=[];ends={}
    for row,label in zip(bars,labels):
        end=period_end(label,timeframe,market);marker=str(row.get('bar_state') or row.get('completion_state') or '').upper()
        reason=None
        if marker in {'PARTIAL','PROVISIONAL','OPEN','LIVE','UNCONFIRMED','UNKNOWN','INVALID'}:reason='explicit_unconfirmed'
        elif label==latest:reason='latest_ambiguous_period_excluded'
        elif end>cutoff or label>cutoff:reason='period_ends_after_analysis_cutoff'
        if reason:excluded.append(dict(original_label=row['date'],period_end=end.isoformat(),reason=reason))
        else:used.append(row);ends[row['date']]=end.isoformat()
    return used,excluded,ends


async def fetch_wm(client,*,symbol,market,timeframe,observed_at,analysis_cutoff,output,run_id,remaining):
    if timeframe not in {'weekly','monthly'}:raise ValueError('WM_only_no_daily_refetch')
    endpoint=safe_endpoint(client.settings.ohlcv_base_url);output=Path(output)
    if output.exists() or any(p.is_symlink() for p in (output,*output.parents)):raise ValueError('new_plain_output_required')
    output.mkdir(parents=True)
    params=dict(symbol=symbol,market=market.upper(),periods=timeframe,count=MAX_COUNTS[timeframe],
        include_indicators='true',indicator_limit=5,adjusted='true',include_investor_flows='false')
    headers={'X-Research-Run':run_id,'X-Research-Remaining-Max':str(remaining)}
    key=client.settings.ohlcv_api_key or client.settings.action_api_key
    if key:headers['X-API-Key']=key
    receipt=dict(symbol=symbol,market=market,timeframe=timeframe,params=params,
        observed_at=observed_at.isoformat(),analysis_cutoff=analysis_cutoff.isoformat(),
        scope='dated_technical_analysis',current_price_qualified=False,valuation_qualified=False)
    try:
        async with httpx.AsyncClient(base_url=endpoint,transport=client.transport,
                timeout=client.settings.ohlcv_timeout_seconds,follow_redirects=False) as c:
            response=await c.get('/ohlcv',params=params,headers=headers)
        raw=response.content;write_new(output/'response.body',raw)
        receipt.update(HTTP_status=response.status_code,body_sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw),
            physical_cumulative_count=int(response.headers.get('X-Research-Physical-Count','-1')),
            budget_instance=response.headers.get('X-Research-Budget-Instance'))
        if response.headers.get('X-Research-Budget-Protocol')!='simple-research-budget-v1':raise ValueError('cost_meter_missing')
        if response.status_code!=200:raise ValueError('HTTP_error_STOP_no_retry')
        if len(raw)>8*1024**2:raise ValueError('response_too_large')
        payload=response.json()
        if payload.get('meta',{}).get('provider')!='kiwoom' or set(payload.get('periods',{}))!={timeframe}:raise ValueError('response_provider_or_period_mismatch')
        bars,_,_=client._decode_period_payload(payload,ticker=symbol,period=timeframe,adjusted=True,
            response_body_sha256=receipt['body_sha256'])
        used,excluded,ends=select_historical(bars,timeframe=timeframe,market=market,cutoff=analysis_cutoff)
        write_new(output/'valid-historical-bars.json',json.dumps(used,ensure_ascii=False,indent=2).encode())
        receipt.update(returned=len(bars),used=len(used),excluded=excluded,
            latest_original_label=bars[-1]['date'] if bars else None,
            last_used_original_label=used[-1]['date'] if used else None,
            last_used_period_end=ends[used[-1]['date']] if used else None,
            period_end_by_original_label=ends,status='DATED_WM_RECEIVED' if used else 'TIMEFRAME_UNAVAILABLE')
        return bars,receipt
    except Exception as exc:
        receipt.update(status='FAILED_NO_RETRY',failure_type=type(exc).__name__)
        if isinstance(exc,ValueError) and str(exc).replace('_','').isalnum():receipt['failure_code']=str(exc)
        raise
    finally:write_new(output/'receipt.json',json.dumps(receipt,ensure_ascii=False,indent=2).encode())


def assemble(client,*,daily_root,wm_sources,symbol,market,observed_at,output):
    """Original daily response/selection remains immutable, no source recollection."""
    daily_root=Path(daily_root);receipt=json.loads((daily_root/'receipt.json').read_text())
    raw=(daily_root/'response.body').read_bytes()
    if hashlib.sha256(raw).hexdigest()!=receipt['body_sha256']:raise ValueError('daily_source_changed')
    cutoff=date.fromisoformat(receipt['actual_historical_as_of'])
    daily,_,_=client._decode_period_payload(json.loads(raw),ticker=symbol,period='daily',adjusted=True,
        response_body_sha256=receipt['body_sha256'])
    chosen=json.loads((daily_root/'valid-historical-bars.json').read_text())
    if not all(row in daily for row in chosen):raise ValueError('daily_selection_changed')
    approved={'daily':{r['date'] for r in chosen}};periods={'daily':daily};selection={}
    for tf,(bars,wm_receipt) in wm_sources.items():
        used,excluded,ends=select_historical(bars,timeframe=tf,market=market,cutoff=cutoff)
        approved[tf]={r['date'] for r in used};periods[tf]=bars
        selection[tf]=dict(original_label=used[-1]['date'] if used else None,
            completed_period_end=ends[used[-1]['date']] if used else None,returned=len(bars),used=len(used),excluded=excluded)
    analysis=copy(client)
    analysis.completion_verifier=lambda row,tf,bound:row['date'] in approved.get(tf,set())
    context=analysis._finalize_native_context(ticker=symbol,context=PriceContext(price_source_scope='dated_technical_only'),
        adjusted_bars=periods,technical_acquisition={'request_count':0,'retry_count':0,'failure_classes':[]},
        as_of=observed_at,price_structure_enabled=True,dated_analysis_as_of=cutoff)
    from app.services.packet_owned_technical_context_service import load_packet_owned_technical_context
    from app.services.cross_market_decision_engine_service import build_decision_evidence_packet,compact_ai_context
    from app.services.kr_price_structure_selective_rollout_service import build_kr_price_structure_rollout_decision
    from app.services.us_price_structure_selective_rollout_service import build_us_price_structure_rollout_decision
    technical=load_packet_owned_technical_context(context.technical_context_payload(),ticker=symbol)
    packet=build_decision_evidence_packet(packet={'packet_id':'dated-DWM-'+symbol,'market':market,'assessment_date':cutoff.isoformat()},
        stock={'ticker':symbol,'company_name':symbol,'fact_catalog':[]},technical_context=technical)
    prompt=compact_ai_context(packet)
    prompt['dated_period_labels_and_ends']=selection
    prompt['native_field_semantics']=dict(FORMULAS,RETURN_20D='20 bars of the stated timeframe, NOT always20 calendar days',
        RETURN_60D='60 bars of the stated timeframe, NOT always60 calendar days')
    renderer=build_kr_price_structure_rollout_decision if market=='kr' else build_us_price_structure_rollout_decision
    rendered=renderer(context.chart.structure['price_structure_v3'],ticker=symbol,monitored_subject=True,enabled=True)
    if rendered.render_validation_errors:raise ValueError('SR_numeric_binding_failed')
    result=dict(symbol=symbol,market=market,daily_as_of=cutoff.isoformat(),observed_at=observed_at.isoformat(),
        WM_selection=selection,technical_input=context.technical_context_payload(),model_input_preview=prompt,
        SR=rendered.to_dict(),NO_SEND=rendered.section or 'NO_SR_CONFIRMED',models_called=0,
        current_price_qualified=False,valuation_qualified=False)
    output=Path(output)
    if output.exists():raise ValueError('new_combined_output_required')
    output.mkdir(parents=True)
    write_new(output/'TECHNICAL_MODEL_INPUT.json',json.dumps(prompt,ensure_ascii=False,indent=2).encode())
    write_new(output/'NO_SEND.json',json.dumps(result,ensure_ascii=False,indent=2).encode())
    write_new(output/'NO_SEND.md',('DATED D/W/M / NO-SEND\nDaily historical as-of: '+cutoff.isoformat()
        +'\nW/M original labels and completed ends: '+json.dumps(selection,ensure_ascii=False)+'\n'+result['NO_SEND']).encode())
    return result
