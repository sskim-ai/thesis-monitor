"""C21Z ordinary HTTP batches. Plan by default; never re-fetch a used output."""
import argparse,asyncio,hashlib,json,sys,uuid
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
    root=Path(root);ledger=json.loads((root/'SUMMARY.json').read_text());entries={}
    if ledger.get('prior_failed_summary'):
        _,entries=read_history(Path(ledger['prior_failed_summary']).parent)
    for stock in ledger['securities']:
        for rec in stock['receipts']:
            key=(stock['symbol'],rec['timeframe']);path=root/(stock['market']+'-'+stock['symbol'])/rec['timeframe']
            if key in entries:raise ValueError('duplicate_role_in_history_STOP')
            if hashlib.sha256((path/'response.body').read_bytes()).hexdigest()!=rec['body_sha256']:raise ValueError('prior_raw_changed_STOP')
            entries[key]=path
    return ledger,entries


async def execute(args):
    import httpx
    from app.services.ohlcv_client import OhlcvClient
    from app.services.dated_technical_research import fetch_daily,safe_endpoint,write_new
    from app.services.dated_multiframe_research import fetch_wm,assemble
    from app.services.market_session import market_session_for_ticker
    batches=prepare_plan(args.plan);root=Path(args.output)
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
    if root.exists() or any(p.is_symlink() for p in (root,*root.parents)):raise ValueError('fresh_plain_output_required_no_retry')
    root.mkdir(parents=True)
    client=OhlcvClient();endpoint=safe_endpoint(client.settings.ohlcv_base_url)
    headers={};key=client.settings.ohlcv_api_key or client.settings.action_api_key
    if key:headers['X-API-Key']=key
    async with httpx.AsyncClient(base_url=endpoint,headers=headers,timeout=client.settings.ohlcv_timeout_seconds,follow_redirects=False) as c:
        r=await c.options('/ohlcv')
    feature=r.json() if r.status_code==200 else {}
    if feature.get('GET_max')!=4 or feature.get('physical_max')!=44 or feature.get('retry')!=0:
        raise ValueError('existing_service_cost_scope_mismatch_STOP')
    ledger=dict(status='RUNNING',GET_max=60,physical_max=655,GETs=0,physical_HTTP=0,
        physical_count_confirmed=True,model=0,DB=0,send=0,retry=0,service_restarts=0,securities=[])
    if prior:
        ledger.update(GETs=prior['GETs'],physical_HTTP=prior['physical_HTTP'],
            prior_failed_summary=str(previous/'SUMMARY.json'),prior_failed_summary_sha256=hashlib.sha256((previous/'SUMMARY.json').read_bytes()).hexdigest(),
            prior_securities=prior['securities'],continuation_user_approval='나머지 종목에서도 실패 발생하더라도 사유 남기고 끝까지 수집해줘',
            retry_of_failed_security=False)
    instance=None
    try:
        for b in batches:
            if ledger['GETs']+b['GET_max']>60 or ledger['physical_HTTP']+b['physical_max']>655:
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
                remaining=min(44-run_total,655-ledger['physical_HTTP'])
                if remaining<1:raise ValueError('physical_budget_exhausted_STOP')
                output=stockroot/tf;ledger['GETs']+=1;failure=None
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
                print(json.dumps(dict(symbol=symbol,timeframe=tf,GETs=ledger['GETs'],physical_HTTP=ledger['physical_HTTP'],status=receipt.get('status'))),flush=True)
                if failure:
                    if isinstance(failure,ValueError) and str(failure) in {'invalid_OHLCV_no_refetch','invalid_historical_OHLCV'}:
                        quality_failures.append(dict(timeframe=tf,reason=str(failure),original_preserved=True))
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
            (root/'PROGRESS.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2))
        else:ledger['status']='ALL_REMAINING_ROLES_ATTEMPTED_QUALITY_FAILURES_PRESERVED' if prior else 'LIVE_20_STOCKS_DWM_COLLECTED_NO_SEND'
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
    a=p.parse_args()
    if not a.live:
        print(json.dumps(dict(mode='PLAN_ONLY_NO_HTTP',batches=prepare_plan(a.plan),GET_max=60,physical_max=655,retry=0,model=0,DB=0,send=0)));return
    try:asyncio.run(execute(a))
    except Exception as exc:
        detail=str(exc);safe=detail if isinstance(exc,ValueError) and detail.replace('_','').isalnum() else type(exc).__name__
        print('BATCH_STOP:'+safe,file=sys.stderr);raise SystemExit(1) from None


if __name__=='__main__':main()
