"""Manual, private, no-send collection. Never invokes app startup or init_db."""
import argparse
import asyncio
from datetime import datetime,timezone
import json
import os
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.services.vnext_research_store import ResearchStore,encoded,now

def arguments():
    p=argparse.ArgumentParser()
    p.add_argument('--db',required=True)
    p.add_argument('--mode',choices=['bootstrap','refresh','validate','shadow','enrich'],required=True)
    p.add_argument('--markets',default='kr,us')
    p.add_argument('--as-of',default='auto')
    p.add_argument('--resume',default='NG62_REV2')
    p.add_argument('--no-send',action='store_true',default=True)
    p.add_argument('--dry-run',action='store_true')
    p.add_argument('--providers',default='SEC,OpenDART')
    p.add_argument('--kiwoom-quiet-until')
    p.add_argument('--resume-local-dns-repair',action='store_true')
    p.add_argument('--external-parser-root')
    p.add_argument('--external-parser-pins')
    p.add_argument('--charts',action='store_true')
    p.add_argument('--chart-roles',default='adjusted_daily')
    p.add_argument('--chart-page-limit',type=int,default=12)
    p.add_argument('--market-children',action='store_true')
    p.add_argument('--us-market-proxies',action='store_true')
    p.add_argument('--shadow-model',action='store_true')
    p.add_argument('--shadow-cases',default='')
    p.add_argument('--scope-plan')
    p.add_argument('--ledger-root')
    return p.parse_args()

async def main(args):
    db=Path(args.db).absolute()
    approved=Path(__file__).resolve().parents[1]/'data/vnext'
    if not db.is_relative_to(approved):raise ValueError('private_vnext_path_required')
    if not db.exists():raise ValueError('bootstrap_requires_authorized_private_snapshot_first')
    store=ResearchStore(db)
    with store.connect() as c:
        previous=c.execute('SELECT as_of FROM research_run WHERE run_id=?',(args.resume,)).fetchone()
    as_of=previous[0] if previous and args.as_of=='auto' else now() if args.as_of=='auto' else args.as_of
    cutoff=datetime.fromisoformat(as_of)
    if cutoff.tzinfo is None:raise ValueError('aware_cutoff_required')
    store.start_run(args.resume,as_of)
    markets=set(args.markets.split(','))
    if not markets <= {'kr','us'}:raise ValueError('unknown_market')
    identities=[r for r in store.identities() if r.get('country','').lower() in markets]
    result=dict(run_id=args.resume,as_of=as_of,registered=len(identities),mode=args.mode,
                no_send=True,strict_native_ready=0)
    if args.dry_run or args.mode in ('bootstrap','validate'):
        with store.connect() as c:
            result.update(row_counts={t:c.execute('SELECT count(*) FROM '+t).fetchone()[0] for t in
                ('watchlistitem','securitymaster','company','investmentthesis','source_capture','research_observation')},foreign_key_errors=c.execute('PRAGMA foreign_key_check').fetchall())
        result['provider_calls']=0
    elif args.mode=='shadow':
        from app.services.vnext_research_projection import derive_research_views
        result['technical_reference']=derive_research_views(store,args.resume)
        directory=db.parent/'shadow'/args.resume;directory.mkdir(parents=True,exist_ok=True)
        packets=[store.packet(args.resume,r['ticker']) for r in identities]
        for packet in packets:(directory/(packet['ticker']+'.json')).write_bytes(encoded(packet))
        for market in ('KR','US'):(directory/('market-'+market+'.json')).write_bytes(encoded(store.market_packet(args.resume,market)))
        result.update(packets=len(packets),nonempty=sum(bool(p['facts']) for p in packets),model_calls=0,
                      model_status='MODEL_NOT_RUN',live_authority=False)
        if args.shadow_cases:
            from app.services.vnext_shadow_research import evaluate
            from app.config import get_settings
            ledger=await evaluate(store,args.resume,args.shadow_cases.split(','),opt_in=args.shadow_model,
                                  settings=get_settings() if args.shadow_model else None)
            result.update(model_calls=len(ledger['events']),model_status='SHADOW_RESEARCH_ONLY' if ledger['events'] else 'PREVIEW_ONLY',
                          model_structure_pass=sum(e['status']=='STRUCTURE_PASS' for e in ledger['events']),
                          model_reserved_usd=sum(e['reserved_usd'] for e in ledger['events']))
            denied=next((e for e in ledger['events'] if e['status']=='MODEL_HTTP_DENIED'),None)
            if denied:result['model_status']='BLOCKED_HTTP_'+str(denied['http_status'])
    elif args.mode=='enrich':
        from app.config import get_settings
        from app.services.vnext_public_capture import PublicTransport
        from app.services.vnext_legacy_reuse import valuation,macro
        if not args.scope_plan or not args.ledger_root:raise ValueError('frozen_scope_and_ledger_required')
        plan=json.loads(Path(args.scope_plan).read_bytes())
        if plan['run_id']!=args.resume or plan['as_of']!=as_of:raise ValueError('enrichment_generation_mismatch')
        if not set(plan.get('subjects',[]))<={r['ticker'] for r in identities}:raise ValueError('unregistered_enrichment_subject')
        if os.statvfs(db.parent).f_bavail*os.statvfs(db.parent).f_frsize<12*1024**3:raise ValueError('enrichment_resource_guard')
        def gate(provider):
            if provider=='Kiwoom':
                until=datetime.fromisoformat(args.kiwoom_quiet_until) if args.kiwoom_quiet_until else None
                if not until or datetime.now(timezone.utc)>=until:raise ValueError('QUIET_WINDOW_NOT_QUALIFIED')
        settings=get_settings()
        secrets=[settings.finnhub_api_key,settings.fred_api_key,settings.ecos_api_key,settings.kiwoom_app_key,settings.kiwoom_secret_key]
        transport=PublicTransport(store,args.resume,scope_plan=plan,ledger_root=args.ledger_root,secrets=secrets,before_request=gate)
        try:
            selected=[s for s in identities if s['ticker'] in plan.get('subjects',[])]
            if selected:result['valuation']=await valuation(store,args.resume,selected,settings,transport,market_types=plan.get('market_types',{}))
            series=tuple(r['query']['series_id'] for r in plan['requests'] if r['host']=='api.stlouisfed.org')
            result['macro']=await macro(store,args.resume,cutoff,transport,fred_series=series,
                ecos=any(r['host']=='ecos.bok.or.kr' for r in plan['requests']))
            result['physical_attempts']=len(transport.events)
        finally:transport.finish()
    else:
        from app.config import get_settings
        from app.services.vnext_public_capture import PublicTransport,financial,completed_us_close,safe_error
        from app.providers.kiwoom_rest_client import KiwoomRestClient
        settings=get_settings()
        providers=set(args.providers.split(','))
        if not providers<={'SEC','OpenDART','Kiwoom'}:raise ValueError('unbudgeted_provider')
        result['credentials_present']={p:bool(v) for p,v in [('SEC',settings.sec_user_agent),('OpenDART',settings.opendart_api_key),('Kiwoom',settings.kiwoom_app_key and settings.kiwoom_secret_key),('model',settings.openai_api_key)]}
        result['model_configuration']=dict(model=settings.openai_narrative_model,task_cost_manifest='NOT_RESOLVED',calls=0)
        secrets=[settings.opendart_api_key,settings.kiwoom_app_key,settings.kiwoom_secret_key,settings.openai_api_key]
        transport=PublicTransport(store,args.resume,secrets=secrets,local_dns_repair=args.resume_local_dns_repair)
        client=KiwoomRestClient(transport=transport,max_retries=0,request_interval_seconds=1.5)
        results=[]
        checkpoint=db.parent/('checkpoint-'+args.resume+'.json')
        def checkpoint_now():
            checkpoint.write_bytes(encoded(dict(result,subjects=results,physical_attempts=len(transport.events),provider_stops=transport.stopped)))
        try:
            # Prices first. Unknown concurrent use postpones only this provider.
            if 'Kiwoom' in providers:
                until=datetime.fromisoformat(args.kiwoom_quiet_until) if args.kiwoom_quiet_until else None
                if not until or datetime.now(timezone.utc)>=until:
                    results.append(dict(provider='Kiwoom',status='NOT_ATTEMPTED',reason='QUIET_WINDOW_NOT_QUALIFIED'))
                else:
                    for identity in identities:
                        if identity.get('country')!='US':continue
                        try:
                            if datetime.now(timezone.utc)>=until:raise ValueError('quiet_window_ended')
                            row=await completed_us_close(store,args.resume,identity,cutoff,client,transport)
                        except Exception as exc:row=dict(ticker=identity['ticker'],provider='Kiwoom',status='NOT_ATTEMPTED',error=safe_error(exc))
                        results.append(row);checkpoint_now()
                        if 'Kiwoom' in transport.stopped:break
                    if args.charts and 'Kiwoom' not in transport.stopped:
                        from app.services.vnext_price_capture import chart
                        if not args.external_parser_root or not args.external_parser_pins:raise ValueError('pinned_original_parser_required')
                        from app.services.unified_stock_acquisition import ROLES
                        roles=args.chart_roles.split(',')
                        if not set(roles)<=set(ROLES) or not 1<=args.chart_page_limit<=12:raise ValueError('chart_role_scope')
                        for role in roles:
                            timeframe,adjusted=ROLES[role]
                            count=300 if role=='unadjusted_weekly_valuation' else dict(daily=1000,weekly=700,monthly=300)[timeframe]
                            for identity in identities:
                                try:
                                    if datetime.now(timezone.utc)>=until:raise ValueError('quiet_window_ended')
                                    row=await chart(store,args.resume,identity,cutoff,client,transport,
                                        root=args.external_parser_root,pins=args.external_parser_pins,count=count,
                                        timeframe=timeframe,adjusted=adjusted,max_pages=args.chart_page_limit)
                                except Exception as exc:row=dict(ticker=identity['ticker'],role=role,provider='Kiwoom',status='NOT_ATTEMPTED',error=safe_error(exc))
                                results.append(row);checkpoint_now()
                                if 'Kiwoom' in transport.stopped:break
            if args.market_children and 'Kiwoom' in providers and 'Kiwoom' not in transport.stopped:
                from app.services.vnext_market_capture import completed_kr_indices
                try:
                    if not args.kiwoom_quiet_until or datetime.now(timezone.utc)>=datetime.fromisoformat(args.kiwoom_quiet_until):raise ValueError('quiet_window_ended')
                    results.extend(await completed_kr_indices(store,args.resume,cutoff,client,transport));checkpoint_now()
                except Exception as exc:results.append(dict(market='KR',status='NOT_ATTEMPTED',error=safe_error(exc)))
            if args.us_market_proxies and 'Kiwoom' in providers and 'Kiwoom' not in transport.stopped:
                from app.services.vnext_market_capture import completed_us_proxies
                try:
                    if not args.kiwoom_quiet_until or datetime.now(timezone.utc)>=datetime.fromisoformat(args.kiwoom_quiet_until):raise ValueError('quiet_window_ended')
                    if not args.external_parser_root or not args.external_parser_pins:raise ValueError('pinned_original_parser_required')
                    results.extend(await completed_us_proxies(store,args.resume,cutoff,client,transport,root=args.external_parser_root,pins=args.external_parser_pins));checkpoint_now()
                except Exception as exc:results.append(dict(market='US',status='NOT_ATTEMPTED',error=safe_error(exc)))
            for identity in identities:
                provider='OpenDART' if identity.get('country')=='KR' else 'SEC'
                if provider not in providers:continue
                try:
                    if not result['credentials_present'][provider]:raise ValueError('provider_credentials_missing')
                    row=await financial(store,args.resume,identity,cutoff,settings,transport)
                except Exception as exc:row=dict(ticker=identity['ticker'],provider=provider,status='NOT_ATTEMPTED',error=safe_error(exc))
                results.append(row);checkpoint_now()
            result.update(subjects=results,physical_attempts=len(transport.events),provider_stops=transport.stopped)
        finally:transport.finish()
    output=db.parent/(args.mode+'-'+args.resume+'-'+datetime.now().strftime('%Y%m%dT%H%M%S')+'.json')
    output.write_bytes(encoded(result))
    print(json.dumps({k:result[k] for k in ('run_id','mode','registered','physical_attempts','row_counts','nonempty','provider_stops') if k in result}))

if __name__=='__main__':asyncio.run(main(arguments()))
