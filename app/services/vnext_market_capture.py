"""Limited completed-market research children, never a FullMarket parent."""
import httpx
from app.services.vnext_public_capture import target_session
from app.services.kiwoom_kr_market_context_service import KiwoomKrMarketContextService,kiwoom_market_reads,SECTOR_ENDPOINT

async def completed_kr_indices(store,run_id,as_of,client,transport):
    target,calendar=target_session('kr',as_of);results=[]
    reads=[r for r in kiwoom_market_reads(session_date=target,max_pages=1,max_requests_per_page=1) if r.api_id=='ka20009']
    async with httpx.AsyncClient(base_url=client.base_url,transport=transport,timeout=90,follow_redirects=False) as http:
        token=await client._access_token(http)
        for read in reads:
            response=await http.post(SECTOR_ENDPOINT,json=read.body,headers={'api-id':read.api_id,'authorization':'Bearer '+token,'cont-yn':'N','next-key':''})
            response.raise_for_status()
            row=KiwoomKrMarketContextService._completed_history_row(history=response.json(),session_date=target,observed_at=as_of)
            receipt=response.extensions['vnext']
            store.market_observation(run_id,'KR',read.key,receipt['raw_sha256'],dict(row=row,calendar=calendar,
                strict_native=False,full_market_owner=False,source_captured_at=receipt['captured_at'],
                validator='KiwoomKrMarketContextService._completed_history_row',breadth=None,sectors=None,flows=None))
            results.append(dict(field=read.key,status='SOURCE_REFERENCE',session=str(target)))
    return results

async def completed_us_proxies(store,run_id,as_of,client,transport,*,root,pins):
    from app.services.vnext_price_capture import call_original,parse_original
    from app.services.native_completed_market import select_completed_daily_rows
    from app.macro.providers.market import normalize_market_observation
    target,calendar=target_session('us',as_of);results=[];lists={};list_sources=[]
    async with httpx.AsyncClient(base_url=client.base_url,transport=transport,timeout=90,follow_redirects=False) as http:
        token=await client._access_token(http)
        for exchange in ('ND','NY','NA'):
            response=await http.post('/api/us/stkinfo',json=dict(stex_tp=exchange),headers={'api-id':'usa10099','authorization':'Bearer '+token})
            response.raise_for_status();lists[exchange]=response.json();list_sources.append(response.extensions['vnext']['raw_sha256'])
        for symbol in ('SPY','QQQ'):
            resolution=call_original(dict(resolve=symbol,lists=lists),root,pins)['resolved']
            if not resolution or resolution['code']!=symbol:raise ValueError('market_proxy_identity_unresolved')
            response=await http.post('/api/us/chart',json=dict(stex_tp=resolution['exchange'],stk_cd=resolution['code'],strt_dt='',upd_stkpc_tp='1',exrt_appl_tp='0'),
                headers={'api-id':'usa06012','authorization':'Bearer '+token,'cont-yn':'N','next-key':''})
            response.raise_for_status();receipt=response.extensions['vnext']
            parsed=parse_original(response.json(),'us','daily',root,pins)
            pair=select_completed_daily_rows(parsed['rows'],target_session=str(target),count=2)
            child=normalize_market_observation(dict(periods=dict(daily=pair)),symbol=symbol,source_url='kiwoom:usa06012:sha256:'+receipt['raw_sha256'])
            store.market_observation(run_id,'US',symbol,receipt['raw_sha256'],dict(strict_native=False,full_market_owner=False,
                observation=dict(child.__dict__,observed_at=child.observed_at.isoformat()),calendar=calendar,
                source_captured_at=receipt['captured_at'],resolution=resolution,identity_source_digests=list_sources,
                scope='ORIGINAL_MARKET_COMPONENT_NOT_FULL_MARKET'))
            results.append(dict(field=symbol,status='SOURCE_REFERENCE',session=str(target)))
    return results
