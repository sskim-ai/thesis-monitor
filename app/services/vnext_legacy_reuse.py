"""Manual research adapters to existing producers, not a Native authority issuer."""
from dataclasses import asdict
from datetime import datetime
import json
from pathlib import Path

from app.services.vnext_research_store import digest, encoded, now
from app.services.vnext_public_capture import public_descriptor
from app.services.provider_native_valuation_snapshot import (
    derive_provider_snapshots, derive_forward_snapshot, INPUT_CONTRACT, FINNHUB_BASE, KIWOOM_ROUTE,
)
from app.services.unified_source_policy import UnifiedSourcePolicy


def bind_public_valuation_identity(current, historical_public):
    """Restore omitted name metadata from a backend-verified public snapshot.

    This grants no current identity: the original current provider validator
    must still match the name, exact security code, market and source receipts.
    """
    keys=('canonical_security_id','ticker','country','exchange','issuer_type','security_type')
    if (any(not current.get(k) or current.get(k)!=historical_public.get(k) for k in keys)
        or any(current[k]!=historical_public[k] for k in set(current)&set(historical_public))
        or not isinstance(historical_public.get('company_name'),str)
        or not historical_public['company_name'].strip()):
        raise ValueError('public_valuation_identity_lineage_mismatch')
    return dict(current,company_name=historical_public['company_name'])


def inherit_public(store, source_run, target_run, as_of):
    if source_run == target_run:
        raise ValueError('inheritance_must_not_relabel_original')
    with store.connect() as c:
        captures=c.execute('SELECT provider,request_key,raw_sha,raw_path,receipt_json FROM source_capture WHERE run_id=?',(source_run,)).fetchall()
        observations=c.execute('SELECT ticker,field,status,source_sha,payload_json FROM research_observation WHERE run_id=?',(source_run,)).fetchall()
    store.start_run(target_run,as_of)
    for provider,key,sha,path,receipt in captures:
        raw=Path(path).read_bytes()
        if digest(raw)!=sha:raise ValueError('inherited_source_corruption')
        old=json.loads(receipt)
        store.capture(target_run,provider,key,raw,dict(captured_at=old['captured_at'],
            kind='EXPLICIT_HISTORICAL_REUSE',source_run=source_run,original_receipt=old,
            original_receipt_sha256=digest(old),strict_native_owner=False))
    for ticker,field,status,sha,payload in observations:
        value=json.loads(payload)
        value.update(source_run=source_run,reused_at=now(),current_capture=False,
            source_captured_this_run=False,strict_native=False)
        if ticker.startswith('@MARKET:'):
            store.market_observation(target_run,ticker.split(':')[1],field,sha,value)
        else:store.observation(target_run,ticker,field,status,sha,value)
    return dict(source_run=source_run,target_run=target_run,captures=len(captures),
        observations=len(observations),raw_recollected=0,authority_reissued=False)


def descriptor(request):
    return {k:v for k,v in public_descriptor(request).items() if k!='page'}


def captured_inputs(store, run_id, provider, security, request):
    """Replay the actual HTTP receipt, never reconstruct authority from values."""
    with store.connect() as c:
        rows=c.execute('SELECT raw_path,receipt_json FROM source_capture WHERE run_id=? AND provider=?',(run_id,provider)).fetchall()
    matched=[]
    for path,text in rows:
        r=json.loads(text);d=r.get('request',{})
        if r.get('raw_birth')!='CURRENT_HTTP':continue
        route='https://'+d.get('host','')+d.get('path','')
        if route!=request['route'] or d.get('method')!=request['method']:continue
        if request['method']=='GET':
            if d.get('query')!=request['params']:continue
        else:
            if d.get('api')!=request['api_id'] or json.loads(d.get('body') or '{}')!=request['body']:continue
            if d.get('page','')!=request.get('continuation',{}).get('next-key',''):continue
        raw=Path(path).read_bytes()
        if digest(raw)!=r['raw_sha256']:raise ValueError('valuation_raw_corruption')
        receipt=dict(provider=provider.lower(),run_id=run_id,security_sha256=digest(security),
            source_sha256=digest(raw),acquisition_class='FRESH_CURRENT_RUN',http_status=r['status'],
            request=request,requested_at=r['started_at'],received_at=r['captured_at'],
            response_headers=r['response_headers'],research_capture_receipt_sha256=digest(r))
        matched.append(dict(raw=raw,receipt=receipt))
    if len(matched)!=1:raise ValueError('exact_current_capture_missing_or_ambiguous')
    return matched[0]


def native_valuation_inputs(store, run_id, security, provider, *, market_type=None, cutoff=None):
    """Shared receipt-to-validator builder for current collection and offline replay."""
    with store.connect() as c:
        start=c.execute('SELECT started_at FROM research_run WHERE run_id=?',(run_id,)).fetchone()
    if not start:raise ValueError('original_run_required')
    ticker=security['ticker']
    if provider=='finnhub':
        profile=captured_inputs(store,run_id,'Finnhub',security,dict(method='GET',route=FINNHUB_BASE+'profile2',params={'symbol':ticker}))
        metric=captured_inputs(store,run_id,'Finnhub',security,dict(method='GET',route=FINNHUB_BASE+'metric',params={'symbol':ticker,'metric':'all'}))
        identity={'profile':profile}
    elif provider=='kiwoom':
        pages=[];cursor=''
        for _ in range(5):
            req=dict(method='POST',route=KIWOOM_ROUTE,api_id='ka10099',body={'mrkt_tp':market_type},
                continuation={} if not cursor else {'cont-yn':'Y','next-key':cursor})
            page=captured_inputs(store,run_id,'Kiwoom',security,req);pages.append(page)
            body=json.loads(page['raw']);head=page['receipt']['response_headers']
            if any(r.get('code')==ticker for r in body.get('list',[])) or head.get('cont-yn')!='Y':break
            cursor=head.get('next-key','')
            if not cursor:raise ValueError('valuation_listing_cursor_missing')
        identity={'market_type':market_type,'list_pages':pages}
        metric=captured_inputs(store,run_id,'Kiwoom',security,dict(method='POST',route=KIWOOM_ROUTE,api_id='ka10001',body={'stk_cd':ticker}))
    else:raise ValueError('native_valuation_provider_unsupported')
    return dict(contract=INPUT_CONTRACT,provider=provider,identity_inputs=identity,**metric,
        run_started_at=datetime.fromisoformat(start[0]),cutoff=cutoff or datetime.fromisoformat(now()),
        policy=UnifiedSourcePolicy(frozenset({'finnhub','kiwoom_rest'})))


async def valuation(store,run_id,securities,settings,transport,*,market_types,client=None):
    from app.services.provider_native_valuation_acquisition import collect_native
    registered=store.identities()
    if any(s not in registered for s in securities):raise ValueError('valuation_unregistered_identity')
    inventory={s['ticker']:dict(provider='kiwoom',market_type=market_types[s['ticker']])
        if s['country']=='KR' else dict(provider='finnhub') for s in securities}
    outcomes=await collect_native(frozen={'valuation_slots':inventory},settings=settings,sealed=transport,client=client)
    result=[]
    for security in securities:
        ticker=security['ticker'];provider=inventory[ticker]['provider'];bound=[]
        try:
            inputs=native_valuation_inputs(store,run_id,security,provider,market_type=market_types.get(ticker))
            values=list(derive_provider_snapshots(inputs,security=security,run_id=run_id))
            if provider=='finnhub':values.append(derive_forward_snapshot(inputs,security=security,run_id=run_id))
            for value in values:
                snapshot=value.model_dump(mode='json') if hasattr(value,'model_dump') else value
                name=snapshot['metric']
                field='valuation.'+('FPER' if name=='FORWARD_PE' else name)
                if name not in ('PER','PBR','FORWARD_PE'):continue
                eligible=snapshot['display_eligible']
                store.observation(run_id,ticker,field,'SOURCE_REFERENCE' if eligible else 'POLICY_DENIED',
                    snapshot['raw_sha256'],dict(snapshot=snapshot,strict_native=False,current_capture=True,
                        source_captured_at=snapshot['retrieval_timestamp'],research_only=True))
                bound.append(dict(metric=name,state=snapshot['state'],value=snapshot['value']))
            result.append(dict(ticker=ticker,status='ORIGINAL_SNAPSHOT_VALIDATOR_REPLAY',metrics=bound))
        except (ValueError,KeyError,TypeError) as exc:
            result.append(dict(ticker=ticker,status='POLICY_DENIED',reason=type(exc).__name__,
                detail=str(exc) if str(exc).replace('_','').isalnum() else 'DETAILS_WITHHELD'))
    return dict(acquisition=outcomes,replay=result,strict_native=False)


async def macro(store,run_id,as_of,transport,*,fred_series=(),ecos=False):
    from app.macro.providers.fred import FredProvider
    from app.macro.providers.ecos import EcosProvider
    providers=[]
    if fred_series:providers.append(('US',FredProvider(transport,series=tuple(fred_series))))
    if ecos:providers.append(('KR',EcosProvider(transport)))
    result=[]
    for market,provider in providers:
        collected=await provider.collect(as_of)
        accepted=[]
        with store.connect() as c:
            hashes={r[0] for r in c.execute('SELECT raw_sha FROM source_capture WHERE run_id=? AND provider=?',(run_id,provider.name.upper()))}
        for ob in collected.observations:
            row=asdict(ob);row['observed_at']=ob.observed_at.isoformat()
            temporal=ob.raw_payload.get('publication_context',{})
            sha=temporal.get('response_sha256')
            if sha not in hashes:raise ValueError('macro_unbound_original_response')
            # Original publication quality is carried unchanged, not promoted to a Market Parent.
            store.market_observation(run_id,market,'macro.'+ob.series_code,sha,
                dict(observation=row,strict_native=False,current_capture=True,full_market_owner=False))
            accepted.append(ob.series_code)
        result.append(dict(provider=provider.name,observations=accepted,warnings=collected.warnings))
    return result
