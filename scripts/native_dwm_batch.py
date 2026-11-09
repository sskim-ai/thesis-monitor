"""C21Z ordinary HTTP batches. Plan by default; never re-fetch a used output."""
import argparse,asyncio,hashlib,json,os,shutil,sys,uuid
from datetime import date,datetime,timezone
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))


def prepare_plan(path):
    plan=json.loads(Path(path).read_text());batches=plan['batches']
    priority=['005930','000660','MU','TSM']
    assert len(batches)==20 and {b['ticker'] for b in batches}.isdisjoint({'047810','CORZ'})
    assert sum(b['GET_max'] for b in batches)==60 and sum(b['physical_max'] for b in batches)==655
    ordered=[next(b for b in batches if b['ticker']==t) for t in priority]+[b for b in batches if b['ticker'] not in priority]
    for b in ordered:
        assert b['GET_max']==3 and b['physical_max']<=44
        assert [(r['timeframe'],r['count']) for r in b['requests']]==[('daily',1000),('weekly',700),('monthly',300)]
    return ordered


def read_history(root):
    root=Path(root)
    if not (root/'SUMMARY.json').is_file():return read_sealed_progress(root)
    ledger=json.loads((root/'SUMMARY.json').read_text());entries={}
    if ledger.get('prior_failed_summary'):
        _,entries=read_history(Path(ledger['prior_failed_summary']).parent)
    for stock in ledger['securities']:
        for rec in stock['receipts']:
            key=(stock['symbol'],rec['timeframe']);path=root/(stock['market']+'-'+stock['symbol'])/rec['timeframe']
            if key in entries:raise ValueError('duplicate_role_in_history_STOP')
            if hashlib.sha256((path/'response.body').read_bytes()).hexdigest()!=rec['body_sha256']:raise ValueError('prior_raw_changed_STOP')
            entries[key]=path
    return ledger,entries


def read_sealed_progress(root):
    root=Path(root)
    if root.is_symlink():raise ValueError('resume_root_not_plain_STOP')
    ledger=json.loads((root/'PROGRESS.json').read_text());entries={}
    if ledger.get('in_flight_role') or not ledger.get('physical_count_confirmed'):
        raise ValueError('interrupted_request_outcome_unknown_no_refetch_STOP')
    seals=ledger.get('stock_seals',{})
    names={s['market']+'-'+s['symbol'] for s in ledger['securities']}
    if {p.name for p in root.iterdir() if p.is_dir()}!=names:
        raise ValueError('unsealed_stock_no_refetch_STOP')
    for stock in ledger['securities']:
        name=stock['market']+'-'+stock['symbol'];folder=root/name;seal=folder/'STOCK_SEAL.json'
        if (folder.is_symlink() or seal.is_symlink() or not seal.is_file()
                or hashlib.sha256(seal.read_bytes()).hexdigest()!=seals.get(name)):
            raise ValueError('unsealed_stock_no_refetch_STOP')
        content=json.loads(seal.read_text())
        if content['stock']!=stock:raise ValueError('progress_seal_mismatch_STOP')
        if {str(p.relative_to(folder)) for p in folder.rglob('*') if p.is_file()}!=set(content['files'])|{'STOCK_SEAL.json'}:
            raise ValueError('unsealed_partial_file_no_refetch_STOP')
        for name,meta in content['files'].items():
            relative=Path(name)
            if relative.is_absolute() or '..' in relative.parts:raise ValueError('unsafe_seal_path_STOP')
            path=folder/relative
            if (any(p.is_symlink() for p in [path,*path.parents]) or not path.is_file()
                    or path.stat().st_size!=meta['bytes']
                    or hashlib.sha256(path.read_bytes()).hexdigest()!=meta['sha256']):
                raise ValueError('sealed_file_changed_STOP')
        for rec in stock['receipts']:
            path=folder/rec['timeframe'];key=(stock['symbol'],rec['timeframe'])
            if (key in entries or rec.get('status') not in {'DATED_TECHNICAL_ANALYSIS_READY','DATED_WM_RECEIVED','TIMEFRAME_UNAVAILABLE'}
                    or hashlib.sha256((path/'response.body').read_bytes()).hexdigest()!=rec['body_sha256']):
                raise ValueError('failed_or_duplicate_role_no_refetch_STOP')
            entries[key]=path
    if len(entries)!=ledger['GETs']:
        raise ValueError('unaccounted_GET_no_refetch_STOP')
    ledger=dict(ledger,recovered_from_sealed_progress=True)
    return ledger,entries


def write_progress(root,ledger):
    temporary=root/'PROGRESS.json.tmp'
    with temporary.open('w') as f:
        json.dump(ledger,f,ensure_ascii=False,indent=2);f.flush();os.fsync(f.fileno())
    os.replace(temporary,root/'PROGRESS.json')
    fd=os.open(root,os.O_RDONLY)
    try:os.fsync(fd)
    finally:os.close(fd)


def recovered_plan(path,include_conditional=False):
    plan=json.loads(Path(path).read_text())
    assert plan['new_GET_max']==34 and plan['new_physical_max']==500
    batches=plan['batches'];keys=[(b['ticker'],r['timeframe']) for b in batches for r in b['requests']]
    assert len(keys)==33 and len(set(keys))==33 and all(b['GET_max']==3 and b['physical_max']<=44 for b in batches)
    assert all([(r['timeframe'],r['count']) for r in b['requests']]==[('daily',1000),('weekly',700),('monthly',300)] for b in batches)
    previous=plan['prior_requested_role_keys']
    assert not set(keys)&{tuple(k) for k in previous}
    if include_conditional:batches=batches+[plan['conditional_IBM_monthly']]
    return batches


def require_recovered_lane():
    state=Path.home()/'Library/Application Support/ThesisMonitor/KiwoomGlobalLane/state.json'
    if state.is_symlink():raise ValueError('Lane_state_not_plain')
    value=json.loads(state.read_text())
    if value.get('halted') is not False or value.get('in_flight') is not False:
        raise ValueError('GLOBAL_LANE_STOP_NO_GET_SENT')


def conditional_is_stable(ledger):
    return (ledger['GETs']==33 and len(ledger['securities'])==11
        and all(not s.get('source_quality_failures') and not s.get('consumer_failure_preserved_no_model')
            and s.get('status') in {'NATIVE_DWM_COMPLETE','NATIVE_DWM_PARTIAL_NULL'} for s in ledger['securities']))


async def execute(args):
    import httpx
    from app.services.ohlcv_client import OhlcvClient
    from app.services.dated_technical_research import fetch_daily,safe_endpoint,write_new
    from app.services.dated_multiframe_research import fetch_wm,assemble
    from app.services.market_session import market_session_for_ticker
    if args.recovered_stop_plan:
        if args.continue_other_stocks:raise ValueError('new_budget_cannot_reuse_old_continuation')
        require_recovered_lane()
        batches=recovered_plan(args.plan,args.include_conditional_ibm)
    else:batches=prepare_plan(args.plan)
    GET_max=34 if args.recovered_stop_plan else 60
    physical_max=500 if args.recovered_stop_plan else 655
    root=Path(args.output)
    prior=None;old_roles={}
    if args.continue_other_stocks:
        previous=Path(args.continue_other_stocks)
        prior,old_roles=read_history(previous)
        if (prior.get('failure_code')!='invalid_OHLCV_no_refetch' or not prior.get('physical_count_confirmed')
                or not 0<prior.get('GETs',0)<60 or not 0<prior.get('physical_HTTP',0)<655):
            raise ValueError('only_explicit_source_quality_continuation_allowed')
        pending=[]
        for b in batches:
            requests=[r for r in b['requests'] if (b['ticker'],r['timeframe']) not in old_roles]
            if requests:pending.append(dict(b,requests=requests,GET_max=len(requests),physical_max=sum(r['physical_max'] for r in requests)))
        batches=pending
        assert sum(b['GET_max'] for b in batches)+prior['GETs']==60
    if args.resume_sealed:
        if not args.recovered_stop_plan or args.continue_other_stocks:
            raise ValueError('sealed_resume_requires_same_delta_plan')
        previous=Path(args.resume_sealed);prior,old_roles=read_sealed_progress(previous)
        if prior['GET_max']!=GET_max or prior['physical_max']!=physical_max:
            raise ValueError('resume_budget_scope_changed_STOP')
        plan_keys={(b['ticker'],r['timeframe']) for b in batches for r in b['requests']}
        if not set(old_roles)<=plan_keys:raise ValueError('resume_roles_outside_plan_STOP')
        batches=[dict(b,requests=req,GET_max=len(req),physical_max=sum(r['physical_max'] for r in req))
            for b in batches if (req:=[r for r in b['requests'] if (b['ticker'],r['timeframe']) not in old_roles])]
    if root.exists() or any(p.is_symlink() for p in (root,*root.parents)):raise ValueError('fresh_plain_output_required_no_retry')
    root.mkdir(parents=True)
    if args.resume_sealed:
        # Copy only files covered by the validated stock seals into the fresh
        # continuation root. Original partial files are never resumed or sent.
        for stock in prior['securities']:
            name=stock['market']+'-'+stock['symbol'];source=previous/name
            seal=json.loads((source/'STOCK_SEAL.json').read_text())
            for namepart in [*seal['files'],'STOCK_SEAL.json']:
                dest=root/name/namepart;dest.parent.mkdir(parents=True,exist_ok=True)
                shutil.copyfile(source/namepart,dest)
    client=OhlcvClient();endpoint=safe_endpoint(client.settings.ohlcv_base_url)
    headers={};key=client.settings.ohlcv_api_key or client.settings.action_api_key
    if key:headers['X-API-Key']=key
    async with httpx.AsyncClient(base_url=endpoint,headers=headers,timeout=client.settings.ohlcv_timeout_seconds,follow_redirects=False) as c:
        r=await c.options('/ohlcv')
    feature=r.json() if r.status_code==200 else {}
    if feature.get('GET_max')!=4 or feature.get('physical_max')!=44 or feature.get('retry')!=0:
        raise ValueError('existing_service_cost_scope_mismatch_STOP')
    ledger=dict(status='RUNNING',GET_max=GET_max,physical_max=physical_max,GETs=0,physical_HTTP=0,
        physical_count_confirmed=True,model=0,DB=0,send=0,retry=0,service_restarts=0,securities=[])
    if prior:
        prior_file=previous/('PROGRESS.json' if args.resume_sealed else 'SUMMARY.json')
        ledger.update(GETs=prior['GETs'],physical_HTTP=prior['physical_HTTP'],
            prior_capture=str(prior_file),prior_capture_sha256=hashlib.sha256(prior_file.read_bytes()).hexdigest(),
            prior_securities=prior['securities'],continuation_user_approval='나머지 종목에서도 실패 발생하더라도 사유 남기고 끝까지 수집해줘',
            retry_of_failed_security=False)
        if args.resume_sealed:
            ledger.update(securities=prior['securities'],resumed_from_sealed_progress=str(previous),stock_seals=prior['stock_seals'])
        else:ledger['prior_failed_summary']=str(previous/'SUMMARY.json')
    instance=None
    try:
        for b in batches:
            if b.get('conditional_after_33'):
                if not conditional_is_stable(ledger):
                    ledger['optional_role_skipped']='prior33_not_stably_completed';continue
                require_recovered_lane()
            if ledger['GETs']+b['GET_max']>GET_max or ledger['physical_HTTP']+b['physical_max']>physical_max:
                ledger['status']='NOT_FETCHED_BUDGET';break
            symbol,market=b['ticker'],b['market'];stockroot=root/(market+'-'+symbol);stockroot.mkdir()
            run_id='c21z-'+uuid.uuid4().hex;observed=datetime.now(timezone.utc)
            stock=dict(symbol=symbol,market=market,run_id=run_id,observed_at=observed.isoformat(),receipts=[],physical_HTTP=0,status='RUNNING')
            ledger['securities'].append(stock);sources={};run_total=0
            daily_root=old_roles.get((symbol,'daily'))
            daily_receipt=json.loads((daily_root/'receipt.json').read_text()) if daily_root else {}
            if daily_receipt.get('status')!='DATED_TECHNICAL_ANALYSIS_READY':daily_root=None
            analysis_cutoff=date.fromisoformat(daily_receipt['actual_historical_as_of']) if daily_root else market_session_for_ticker(symbol,observed).latest_completed_regular_session_date
            quality_failures=[]
            for request in b['requests']:
                tf=request['timeframe']
                remaining=min(44-run_total,physical_max-ledger['physical_HTTP'])
                if remaining<1:raise ValueError('physical_budget_exhausted_STOP')
                output=stockroot/tf;ledger['GETs']+=1;failure=None
                ledger['in_flight_role']=[symbol,tf]
                write_progress(root,ledger)
                try:
                    if tf=='daily':
                        cutoff=market_session_for_ticker(symbol,observed).latest_completed_regular_session_date
                        _,receipt=await fetch_daily(client,symbol=symbol,market=market,history_through=cutoff,
                            observed_at=observed,output=output,run_id=run_id,physical_remaining=remaining,count=1000)
                        analysis_cutoff=date.fromisoformat(receipt['actual_historical_as_of'])
                        daily_root=output
                    else:
                        bars,receipt=await fetch_wm(client,symbol=symbol,market=market,timeframe=tf,observed_at=observed,
                            analysis_cutoff=analysis_cutoff,output=output,run_id=run_id,remaining=remaining)
                        sources[tf]=(bars,receipt)
                except Exception as exc:
                    failure=exc
                    receipt=json.loads((output/'receipt.json').read_text()) if (output/'receipt.json').is_file() else {}
                stock['receipts'].append(dict(receipt,timeframe=tf))
                count=receipt.get('physical_cumulative_count');current=receipt.get('budget_instance')
                if (type(count) is not int or not run_total<=count<=44 or not current
                        or (stock.get('budget_instance') and current!=stock['budget_instance'])):
                    ledger['physical_count_confirmed']=False;raise ValueError('physical_count_unconfirmed_STOP')
                # A different budget id is expected for each stock, not within it.
                stock['budget_instance']=current;delta=count-run_total;run_total=count
                ledger['physical_HTTP']+=delta;stock['physical_HTTP']=count
                stock['receipts'][-1]['physical_delta']=delta
                ledger.pop('in_flight_role',None)
                print(json.dumps(dict(symbol=symbol,timeframe=tf,GETs=ledger['GETs'],physical_HTTP=ledger['physical_HTTP'],status=receipt.get('status'))),flush=True)
                if failure:
                    if isinstance(failure,ValueError) and str(failure) in {'invalid_OHLCV_no_refetch','invalid_historical_OHLCV','not_isolated_price_relation_error','recent_nonlatest_error_not_admitted','remaining_source_invalid'}:
                        quality_failures.append(dict(timeframe=tf,reason=str(failure),original_preserved=True))
                        if tf=='daily':daily_root=None
                        continue
                    diagnostic=receipt.get('service_diagnostic',{})
                    if (diagnostic.get('global_stop') is False and type(diagnostic.get('upstream_status')) is int
                            and 500<=diagnostic['upstream_status']<=599):
                        quality_failures.append(dict(timeframe=tf,reason='received_upstream_5xx_no_retry',diagnostic=diagnostic))
                        continue
                    if (diagnostic.get('global_stop') is False
                            and diagnostic.get('phase') in {'local_call','local_serialization'}):
                        quality_failures.append(dict(timeframe=tf,reason='local_service_role_failure_no_retry',diagnostic=diagnostic))
                        if tf=='daily':daily_root=None
                        continue
                    raise failure
            try:
                if daily_root:
                    result=assemble(client,daily_root=daily_root,wm_sources=sources,symbol=symbol,market=market,
                        observed_at=observed,output=stockroot/'combined')
                    periods=result['technical_input']['native_view']['periods']
                    stock['status']='NATIVE_DWM_PARTIAL_NULL' if any(v is None for p in periods.values() for v in p['indicators'].values()) else 'NATIVE_DWM_COMPLETE'
                    if any(p['returned_count']<p['max_count'] for p in periods.values()):stock['history']='PARTIAL_HISTORY_VALID_NOT_BLOCKED'
                    stock['combined_output']=str(stockroot/'combined')
                else:
                    from app.services.dated_multiframe_research import select_historical
                    from app.services.provider_native_technical import build_provider_native_view
                    approved={tf:{r['date'] for r in select_historical(bars,timeframe=tf,market=market,cutoff=analysis_cutoff)[0]} for tf,(bars,_) in sources.items()}
                    view=build_provider_native_view(ticker=symbol,market=market,periods={tf:bars for tf,(bars,_) in sources.items()},cutoff=analysis_cutoff,
                        completion_verifier=lambda row,tf,cutoff:row['date'] in approved.get(tf,set()))
                    write_new(stockroot/'WM_ONLY_NATIVE_VIEW.json',view.model_dump_json(indent=2).encode())
                    write_new(stockroot/'NO_SEND.md',b'DATED W/M native input only. Daily source quality blocked; no D/W/M SR or investment decision invented. NO-SEND.')
                    stock['status']='DAILY_SOURCE_BLOCKED_WM_PRESERVED'
                stock['source_quality_failures']=quality_failures
            except Exception as exc:
                stock['status']='CONSUMER_FAILURE_PRESERVED';stock['failure_type']=type(exc).__name__
                stock['consumer_failure_preserved_no_model']=True
            # Durable individual stock seal before starting the next stock.
            members={str(p.relative_to(stockroot)):dict(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in stockroot.rglob('*') if p.is_file()}
            write_new(stockroot/'STOCK_SEAL.json',json.dumps(dict(stock=stock,files=members),ensure_ascii=False,indent=2).encode())
            ledger.setdefault('stock_seals',{})[market+'-'+symbol]=hashlib.sha256((stockroot/'STOCK_SEAL.json').read_bytes()).hexdigest()
            write_progress(root,ledger)
        else:ledger['status']='C22A_DELTA_SCOPE_ATTEMPTED_NO_SEND' if args.recovered_stop_plan else 'ALL_REMAINING_ROLES_ATTEMPTED_QUALITY_FAILURES_PRESERVED' if prior else 'LIVE_20_STOCKS_DWM_COLLECTED_NO_SEND'
    except Exception as exc:
        ledger['status']='FAILED_NO_RETRY_STOP';ledger['failure_type']=type(exc).__name__
        detail=str(exc)
        if isinstance(exc,ValueError) and detail.replace('_','').isalnum():ledger['failure_code']=detail
        if ledger['securities'] and ledger['securities'][-1]['status']=='RUNNING':ledger['securities'][-1]['status']='SOURCE_QUALITY_BLOCKED' if 'OHLCV' in detail else 'HTTP_FAILURE_STOP'
        raise
    finally:
        write_new(root/'SUMMARY.json',json.dumps(ledger,ensure_ascii=False,indent=2).encode())
        print(json.dumps({k:ledger[k] for k in ['status','GETs','physical_HTTP','physical_count_confirmed']}),flush=True)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--plan',required=True)
    p.add_argument('--live',action='store_true');p.add_argument('--output',required=True)
    p.add_argument('--continue-other-stocks',help='Explicit user-approved continuation after source-quality STOP only')
    p.add_argument('--recovered-stop-plan',action='store_true',help='Only after explicit operational approval and formal existing-Lane recovery')
    p.add_argument('--include-conditional-ibm',action='store_true')
    p.add_argument('--resume-sealed',help='Same delta budget only; verified complete stock seals, never partial requests')
    a=p.parse_args()
    if not a.live:
        batches=recovered_plan(a.plan,a.include_conditional_ibm) if a.recovered_stop_plan else prepare_plan(a.plan)
        print(json.dumps(dict(mode='PLAN_ONLY_NO_HTTP',batches=batches,GET_max=34 if a.recovered_stop_plan else 60,physical_max=500 if a.recovered_stop_plan else 655,retry=0,model=0,DB=0,send=0)));return
    try:asyncio.run(execute(a))
    except Exception as exc:
        detail=str(exc);safe=detail if isinstance(exc,ValueError) and detail.replace('_','').isalnum() else type(exc).__name__
        print('BATCH_STOP:'+safe,file=sys.stderr);raise SystemExit(1) from None


if __name__=='__main__':main()
