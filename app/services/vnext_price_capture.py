"""Public research charts through the pinned original parser and quality inspector."""
from datetime import date
import json
from pathlib import Path
import subprocess
import sys
import httpx
from app.services.vnext_research_store import encoded,digest,now
from app.services.vnext_public_capture import target_session,SystemicStop

def parse_original(body,market,timeframe,root,pins):
    return call_original(dict(body=body,market=market,timeframe=timeframe),root,pins)

def call_original(request,root,pins):
    script=Path(__file__).resolve().parents[2]/'scripts/vnext_ohlcv_parse_worker.py'
    result=subprocess.run([sys.executable,'-I','-S','-B',str(script),str(root),str(pins),str(Path(httpx.__file__).resolve().parents[1])],
        input=encoded(request),capture_output=True,timeout=30)
    if result.returncode:raise ValueError('original_parser_worker_failed')
    return json.loads(result.stdout)

async def chart(store,run_id,identity,as_of,client,transport,*,root,pins,count=1000,timeframe='daily',adjusted=True,max_pages=12,resume_sha=None,analytic_view_policy=None):
    from app.services.ohlcv_provider_integrity_service import inspect_normalized_ohlcv_rows
    if identity not in store.identities():raise ValueError('registered_chart_identity_mismatch')
    market=identity['country'].lower();ticker=identity['ticker']
    target,calendar=target_session(market,as_of)
    spec=parse_original({},market,timeframe,root,pins)
    if analytic_view_policy is not None:
        from app.services.vnext_timeframe_views import CONTRACT,analytic_view
        if analytic_view_policy!=CONTRACT or not adjusted or resume_sha is not None:
            raise ValueError('analytic_acquisition_policy_scope')
    if market=='kr':
        path='/api/dostk/chart';body=dict(stk_cd=ticker,base_dt=as_of.strftime('%Y%m%d'),upd_stkpc_tp='1' if adjusted else '0')
    else:
        exchange={'NASDAQ':'ND','NYSE':'NY','AMEX':'NA'}.get(identity['exchange'])
        if not exchange:raise ValueError('registered_exchange_missing')
        path='/api/us/chart';body=dict(stex_tp=exchange,stk_cd=ticker.replace('.','-'),strt_dt='',upd_stkpc_tp='1' if adjusted else '0',exrt_appl_tp='0')
    rows=[];pages=[];cursor='';continuation='N';seen=set();exhausted=False
    if resume_sha is not None:
        with store.connect() as c:
            found=c.execute('SELECT raw_path FROM source_capture WHERE run_id=? AND provider=? AND raw_sha=?',(run_id,'ChartReplay',resume_sha)).fetchall()
        if len(found)!=1:raise ValueError('resume_chart_membership_missing')
        raw=Path(found[0][0]).read_bytes()
        if digest(raw)!=resume_sha:raise ValueError('resume_chart_corruption')
        old=json.loads(raw)
        if (old['request_body']!=body or old['calendar']!=calendar or old['parser_sha256']!=spec['parser_sha256']
                or old['requested_rows']!=count or old['exhausted'] or not old['pages']):
            raise ValueError('resume_chart_contract_mismatch')
        pages=old['pages']
        for page in pages:
            with store.connect() as c:
                item=c.execute('SELECT raw_path FROM source_capture WHERE run_id=? AND provider=? AND raw_sha=?',(run_id,'Kiwoom',page['raw_sha256'])).fetchone()
            if item is None:raise ValueError('resume_page_membership_missing')
            raw=Path(item[0]).read_bytes()
            if digest(raw)!=page['raw_sha256']:raise ValueError('resume_page_corruption')
            rows.extend(parse_original(json.loads(raw),market,timeframe,root,pins)['rows'])
        continuation=pages[-1]['continuation'];cursor=pages[-1]['next_key']
        if continuation!='Y' or not cursor:raise ValueError('resume_cursor_missing')
        seen={''}|{p['next_key'] for p in pages[:-1]}
    async with httpx.AsyncClient(base_url=client.base_url,transport=transport,timeout=90,follow_redirects=False) as http:
        token=await client._access_token(http)
        for ordinal in range(len(pages)+1,len(pages)+max_pages+1):
            if cursor in seen:raise ValueError('chart_repeated_cursor')
            seen.add(cursor)
            response=await http.post(path,json=body,headers={'api-id':spec['api'],'authorization':'Bearer '+token,'cont-yn':continuation,'next-key':cursor})
            response.raise_for_status();data=response.json()
            if str(data.get('return_code','0'))!='0':raise SystemicStop('chart_provider_denial')
            parsed=parse_original(data,market,timeframe,root,pins)
            rows.extend(parsed['rows']);receipt=response.extensions['vnext']
            continuation=response.headers.get('cont-yn',data.get('cont_yn','N')).upper()
            cursor=response.headers.get('next-key',data.get('next_key',''))
            pages.append(dict(ordinal=ordinal,raw_sha256=receipt['raw_sha256'],captured_at=receipt['captured_at'],rows=parsed['input_rows'],continuation=continuation,next_key=cursor))
            exhausted=continuation!='Y'
            if continuation=='Y' and not cursor:raise ValueError('chart_missing_continuation_cursor')
            if analytic_view_policy:
                view=analytic_view(sorted(rows,key=lambda r:r['date']),timeframe=timeframe,
                    market=identity['country'],session=str(target))
                if exhausted or view['first_invalid'] or view['count']>=count:break
            elif exhausted or len([r for r in rows if r['date']<=str(target)])>=count:break
    dates=[r['date'] for r in rows]
    if len(set(dates))!=len(dates):raise ValueError('chart_duplicate_dates')
    if dates!=sorted(dates) and dates!=sorted(dates,reverse=True):raise ValueError('chart_page_order')
    # A subsequent chart period proves the earlier weekly/monthly period ended.
    completed=sorted([r for r in rows if r['date']<=str(target) and
        (timeframe=='daily' or r['date']<max(dates))],key=lambda r:r['date'])
    inspection=inspect_normalized_ohlcv_rows(completed,timeframe=timeframe,cutoff=target)
    bundle=dict(kind='CURRENT_CHART_REPLAY',calendar=calendar,request_body=body,pages=pages,
        parsed_rows=len(rows),completed_rows=len(completed),exhausted=exhausted,selected=completed[-count:],
        quality=inspection.model_dump(mode='json'),parser_sha256=spec['parser_sha256'],requested_rows=count,
        strict_native=False,full_owner_issued=False,resumed_from_sha256=resume_sha,
        acquisition_lineage='MULTI_CAPTURE_RESEARCH_ONLY' if resume_sha else 'SINGLE_RUN')
    if analytic_view_policy:
        bundle.update(analytic_view_policy=analytic_view_policy,source_kind='NATIVE',
            provider_timeframe_api=spec['api'],paging_stop=('SOURCE_EXHAUSTED' if exhausted else
                'FIRST_INVALID_OLDER_BAR' if view['first_invalid'] else 'REQUESTED_INDICATOR_WARMUP_REACHED' if view['count']>=count else 'PAGE_CAP'))
    sha=store.capture(run_id,'ChartReplay',digest([ticker,timeframe,adjusted,count,[p['raw_sha256'] for p in pages]]),encoded(bundle),dict(captured_at=pages[0]['captured_at'],kind='DERIVED_REPLAY_NOT_NEW_RAW'))
    role=('adjusted_' if adjusted else 'unadjusted_')+timeframe+('_valuation' if not adjusted else '')
    latest=bool(completed and completed[-1]['date']==str(target)) if timeframe=='daily' else bool(completed)
    if not inspection.valid:status='POLICY_DENIED';reason='ORIGINAL_OHLCV_QUALITY_FAILED'
    elif not latest:status='STALE';reason='LATEST_COMPLETED_SESSION_MISSING'
    elif len(completed)<count:status='SHORT_HISTORY' if exhausted else 'MISSING_SOURCE';reason='SOURCE_EXHAUSTED' if exhausted else 'PAGE_BUDGET_INCOMPLETE'
    else:status='SOURCE_REFERENCE';reason='RESEARCH_ONLY_NO_STRICT_OWNER'
    store.observation(run_id,ticker,'ohlcv.'+role,status,sha,dict(strict_native=False,reason=reason,
        rows=len(completed),requested_rows=count,source_exhausted=exhausted,calendar=calendar,quality_valid=inspection.valid,
        selected_rows=completed[-count:] if inspection.valid else [],original_full_owner_issued=False,adjusted=adjusted,
        current_capture=True,source_captured_at=pages[0]['captured_at']))
    close_quality=inspect_normalized_ohlcv_rows(completed[-1:],timeframe='daily',cutoff=target)
    if market=='kr' and timeframe=='daily' and close_quality.valid and latest:
        store.observation(run_id,ticker,'completed_close','CURRENT_VALID',sha,dict(strict_native=False,
            row=completed[-1],currency='KRW',calendar=calendar,adjusted=adjusted,
            validator='original_OHLCV_quality_and_completed_session',original_full_owner_issued=False,
            source_captured_at=pages[0]['captured_at'],price_basis='REPORTED_KR_DAILY_REFERENCE'))
    return dict(ticker=ticker,field='ohlcv.'+role,status=status,reason=reason,rows=len(completed),pages=len(pages),source_exhausted=exhausted)
