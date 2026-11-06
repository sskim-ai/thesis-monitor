"""Bounded manual public-source adapter. No server, scheduler, send or orders."""
import asyncio
from datetime import datetime, timedelta, timezone
import fcntl
import json
import os
from pathlib import Path
import time
import httpx
from app.services.vnext_research_store import digest, encoded, now
from app.services.bounded_financial_acquisition import BoundedReader, SystemicStop, make_plan, collect

CAPS = {'Kiwoom':250, 'SEC':120, 'OpenDART':100}
HOSTS = {'api.kiwoom.com':'Kiwoom','data.sec.gov':'SEC','www.sec.gov':'SEC','opendart.fss.or.kr':'OpenDART'}
OPTIONAL_HOSTS = {'finnhub.io':'Finnhub','api.stlouisfed.org':'FRED','ecos.bok.or.kr':'ECOS'}

def public_descriptor(request):
    auth=request.url.path=='/oauth2/token'
    path=request.url.path
    if request.url.host=='ecos.bok.or.kr':
        pieces=path.split('/')
        if len(pieces)>3 and pieces[2]=='KeyStatisticList':pieces[3]='REDACTED'
        path='/'.join(pieces)
    query={k:v for k,v in request.url.params.multi_items() if k.lower() not in ('crtfc_key','token','api_key')}
    return dict(host=request.url.host,path=path,query=query,method=request.method,
        api=request.headers.get('api-id',''),body=None if auth else request.content.decode(),
        page=request.headers.get('next-key',''))

def official_dns_host(host):
    if isinstance(host,bytes):
        try:host=host.decode('ascii')
        except UnicodeError:return False
    return host in HOSTS

def safe_error(exc):
    # Exception URLs can contain API keys. Never stringify HTTP/transport errors.
    message=str(exc)
    return {'type':type(exc).__name__, 'code':message if message.replace('_','').isalnum() and len(message)<150 else 'DETAILS_WITHHELD'}

class PublicTransport(httpx.AsyncBaseTransport):
    def __init__(self, store, run_id, *, secrets=(), inner=None, interval=1.5, local_dns_repair=False, before_request=None,
                 scope_plan=None, ledger_root=None, global_lane=None):
        self.store,self.run_id,self.secrets=store,run_id,tuple(x for x in secrets if x)
        self.inner=inner
        self.global_lane=global_lane
        self.interval=interval
        self.before_request=before_request
        self.scope_plan=json.loads(encoded(scope_plan)) if scope_plan is not None else None
        self.caps=CAPS if scope_plan is None else self.scope_plan['limits']
        if scope_plan is not None:
            if not self.caps or any(k not in set(HOSTS.values())|set(OPTIONAL_HOSTS.values()) or type(v)!=int or v<0 for k,v in self.caps.items()):
                raise ValueError('invalid_scoped_provider_limits')
            if any(v>CAPS[k] for k,v in self.caps.items() if k in CAPS):raise ValueError('scoped_budget_widening')
        log_root=Path(ledger_root) if ledger_root else store.path.parent
        log_root.mkdir(parents=True,exist_ok=True)
        self.log=log_root/'http-ledger.json'
        self.lock=open(store.path.parent/'manual-collector.lock','a')
        fcntl.flock(self.lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if self.scope_plan is not None:
            frozen=log_root/'scope-plan.json'
            if frozen.exists() and frozen.read_bytes()!=encoded(self.scope_plan):
                self.finish()
                raise ValueError('scoped_plan_changed')
            if not frozen.exists():frozen.write_bytes(encoded(self.scope_plan))
        self.events=json.loads(self.log.read_text()) if self.log.exists() else []
        self.local_dns_repair=local_dns_repair
        if local_dns_repair:
            for row in self.events:
                if ('status' not in row and row.get('error',{}).get('code')=='provider_DNS_scope'
                        and row.get('stop')=='TRANSPORT_OR_BOUNDARY_STOP'):
                    row.setdefault('local_repair',dict(code='DNS_BYTES_HOST_V1',at=now(),attempt_still_charged=True))
            self.save()
        self.stopped={r['provider']:r.get('stop') or 'UNCERTAIN_PREVIOUS_ATTEMPT' for r in self.events
                      if (r.get('stop') or not r.get('ended_at')) and not r.get('local_repair')}
        self.last={}
        for row in self.events:
            if row.get('ended_at'):
                age=max(0,(datetime.now(timezone.utc)-datetime.fromisoformat(row['ended_at'])).total_seconds())
                self.last[row['provider']]=time.monotonic()-age

    def save(self):
        tmp=self.log.with_suffix('.pending');tmp.write_bytes(encoded(self.events));os.replace(tmp,self.log)

    async def aclose(self):
        # Original clients may close this shared transport between logical reads.
        pass

    def finish(self):
        fcntl.flock(self.lock,fcntl.LOCK_UN);self.lock.close()

    async def handle_async_request(self, request):
        provider=(HOSTS|OPTIONAL_HOSTS if self.scope_plan is not None else HOSTS).get(request.url.host)
        if not provider or request.url.scheme!='https' or request.url.port not in (None,443):
            raise SystemicStop('official_endpoint_scope_denied')
        auth=request.url.path=='/oauth2/token'
        api=request.headers.get('api-id','')
        descriptor=public_descriptor(request)
        if self.scope_plan is not None:
            match={k:v for k,v in descriptor.items() if k!='page'}
            if provider not in self.caps or match not in self.scope_plan['requests']:
                raise SystemicStop('frozen_request_scope_denied')
            if descriptor['page'] and self.scope_plan.get('allow_pagination') is False:
                self.stopped[provider]='SCOPED_PAGINATION_NOT_AUTHORIZED'
                raise SystemicStop('scoped_pagination_not_authorized')
        if provider=='Kiwoom':
            if request.method!='POST' or (not auth and (api,request.url.path) not in {
                ('usa20590','/api/us/mrkcond'),('ka10081','/api/dostk/chart'),
                ('ka10082','/api/dostk/chart'),('ka10083','/api/dostk/chart'),
                ('usa06012','/api/us/chart'),('usa06013','/api/us/chart'),('usa06014','/api/us/chart'),
                ('ka20009','/api/dostk/sect'),('usa10099','/api/us/stkinfo')}
                and not (self.scope_plan is not None and (api,request.url.path) in {
                    ('ka10099','/api/dostk/stkinfo'),('ka10001','/api/dostk/stkinfo')})):
                raise SystemicStop('read_only_kiwoom_allowlist_denied')
        elif request.method!='GET':raise SystemicStop('official_GET_required')
        key=digest(descriptor)
        if not auth:
            from app.services.public_capture_storage import find_capture
            old=find_capture(self.store,self.run_id,provider,key)
            if old:
                receipt=json.loads(old[1]);raw=Path(old[0]).read_bytes()
                if digest(raw)!=receipt['raw_sha256']:raise SystemicStop('cached_source_corruption')
                return httpx.Response(receipt['status'],content=raw,headers=receipt['response_headers'],extensions={'vnext':dict(receipt,reused=True)})
        if provider in self.stopped:raise SystemicStop('provider_stopped_'+provider)
        if self.before_request:self.before_request(provider)
        if sum(r['provider']==provider for r in self.events)>=self.caps[provider]:raise SystemicStop('physical_budget_exhausted_'+provider)
        lane=self.global_lane if provider=='Kiwoom' else None
        if provider=='Kiwoom' and self.inner is None:
            from app.services.kiwoom_global_lane import configured_lane
            configured=configured_lane()
            if lane is not None and lane is not configured:
                raise SystemicStop('global_lane_capability_mismatch')
            lane=configured
        await asyncio.sleep(max(0,self.interval-(time.monotonic()-self.last.get(provider,0))))
        row=dict(provider=provider,run_id=self.run_id,ordinal=len(self.events)+1,endpoint=descriptor['path'],api=api,auth=auth,
                 started_at=now(),request_key=None if auth else key)
        self.events.append(row);self.save()
        try:
            async def consume(transport):
                response=await transport.handle_async_request(request)
                parts=[];size=0
                try:
                    async for part in response.aiter_bytes():
                        size+=len(part)
                        if size>32*1024**2:raise SystemicStop('response_budget_exhausted')
                        parts.append(part)
                finally:await response.aclose()
                return response,b''.join(parts)
            async def physical():
                if self.inner is not None:return await consume(self.inner)
                async with httpx.AsyncHTTPTransport(verify=True,trust_env=False,retries=0) as transport:
                    return await asyncio.wait_for(consume(transport),90)
            if lane is not None:
                from app.services.kiwoom_global_lane import validate_envelope
                async with lane.slot() as lease:
                    response,raw=await physical()
                    row['status']=response.status_code
                    row['global_lane']=dict(lease)
                    # Validation is inside the physical lease, including token
                    # parsing. A rejected envelope leaves the durable halt set.
                    checked=httpx.Response(response.status_code,content=raw,headers=response.headers,request=request)
                    payload=validate_envelope(checked)
                    if auth:
                        if not payload.get('token') or not payload.get('expires_dt'):
                            raise SystemicStop('auth_response_incomplete')
                        datetime.strptime(str(payload['expires_dt']),'%Y%m%d%H%M%S')
                        self.secrets=(*self.secrets,str(payload['token']))
            else:response,raw=await physical()
            row['status']=response.status_code
            if response.status_code in (401,403,429) or 300<=response.status_code<400:
                row['stop']='HTTP_AUTH_RATE_OR_REDIRECT';self.stopped[provider]=row['stop']
            if not auth and any(s.encode() in raw for s in self.secrets):raise SystemicStop('secret_echo_denied')
            headers={k:v for k,v in response.headers.items() if k.lower() in ('content-type','cont-yn','next-key')}
            receipt=dict(row,captured_at=now(),raw_sha256=digest(raw),raw_bytes=len(raw),response_headers=headers,
                         raw_birth='CURRENT_HTTP',strict_native_owner=False,request=descriptor)
            if not auth and response.status_code==200:
                self.store.capture(self.run_id,provider,key,raw,receipt)
            if provider=='OpenDART' and response.status_code==200:
                if request.url.path=='/api/corpCode.xml' and raw.startswith(b'PK'):
                    from app.providers.opendart_corp_codes import _parse_corp_code_zip
                    status='000' if _parse_corp_code_zip(raw) else 'EMPTY_CORPORATE_IDENTITY'
                else:
                    status=json.loads(raw).get('status')
                row['provider_status']=status
                if status not in ('000','013'):
                    row['stop']='PROVIDER_STATUS_DENIAL';self.stopped[provider]=row['stop']
            if provider=='Kiwoom' and response.status_code==200 and str(json.loads(raw).get('return_code','0'))!='0':
                row['stop']='PROVIDER_RETURN_CODE_DENIAL';self.stopped[provider]=row['stop']
            required=self.scope_plan.get('required_identity') if self.scope_plan is not None else None
            if provider=='Kiwoom' and api=='ka10099' and required is not None and response.status_code==200:
                matches=[v for v in json.loads(raw).get('list',[]) if v.get('code')==required['ticker']]
                if len(matches)!=1 or str(matches[0].get('marketCode'))!=required['market_type']:
                    row['stop']='SCOPED_IDENTITY_NOT_ESTABLISHED';self.stopped[provider]=row['stop']
            return httpx.Response(response.status_code,content=raw,headers=headers,extensions={'vnext':receipt})
        except BaseException as exc:
            row['error']=safe_error(exc);row['stop']='TRANSPORT_OR_BOUNDARY_STOP';self.stopped[provider]=row['stop']
            raise
        finally:
            row['ended_at']=now();self.last[provider]=time.monotonic();self.save()

class ResearchReader(BoundedReader):
    def response_metadata(self,response):
        return {'vnext_source_birth':response.extensions.get('vnext')}

def target_session(market, as_of):
    from app.services.price_structure_wave_fibonacci_v3_service import _calendar_for_range,_latest_completed_session
    name,cal=_calendar_for_range(market.upper(),start=as_of.date()-timedelta(days=20),end=as_of.date()+timedelta(days=7))
    target=_latest_completed_session(cal,as_of)
    if target is None:raise ValueError('completed_session_unresolved')
    return target,dict(calendar=name,as_of=as_of.isoformat(),session=str(target))

async def financial(store, run_id, identity, as_of, settings, transport, *, maximum_attempts=None):
    if identity not in store.identities():raise ValueError('registered_financial_identity_mismatch')
    from app.services.bounded_financial_projection import project
    from app.services.bounded_financial_stock_owner import reported_comparisons
    from app.services.sec_fpi_statement_basis_owner import POLICY
    market=identity['country'].lower();ticker=identity['ticker']
    root=store.path.parent/'financial'/run_id/ticker
    finished=root/'research-result.json'
    if finished.exists():
        old=json.loads(finished.read_text())
        repairable=transport.local_dns_repair and old.get('status')=='PROVIDER_LIMIT' and all(
            e.get('code') in ('provider_DNS_scope','provider_stopped_SEC','provider_stopped_OpenDART') for e in old.get('errors',[]))
        if not repairable:return old
    root.mkdir(parents=True,exist_ok=True)
    attempt=root/('attempt-%03d'%(len(list(root.glob('attempt-*')))+1));attempt.mkdir()
    plan=make_plan(identity,market=market,cutoff=as_of,run_id=run_id,all_subjects_fresh=True,exact_financial_owner=market=='us')
    if maximum_attempts is not None:
        if type(maximum_attempts) is not int or not 1<=maximum_attempts<=plan['maximum_attempts_per_request']:
            raise ValueError('financial_attempt_budget_cannot_widen')
        plan['maximum_attempts_per_request']=maximum_attempts
        plan['maximum_retries_per_request']=maximum_attempts-1
        plan['maximum_HTTP_attempts']=plan['maximum_logical_requests']*maximum_attempts
    (attempt/'frozen-plan.json').write_bytes(encoded(plan))
    reader=ResearchReader(plan,attempt,api_key=settings.opendart_api_key,user_agent=settings.sec_user_agent,transport=transport)
    result=dict(ticker=ticker,strict_owner='NOT_ISSUED',status='NOT_ATTEMPTED',facts=[],errors=[])
    try:
        acquisition=await collect(reader)
        (attempt/'acquisition.json').write_bytes(encoded(acquisition))
        options=dict(field_semantics=True)
        if '6-K' in plan['forms']:options.update(statement_basis_policy=POLICY,basis_execution_generation=run_id)
        projection=project(plan,acquisition,attempt,reader.receipts,**options)
        facts,denied=reported_comparisons(plan,projection)
        (attempt/'projection.json').write_bytes(encoded(projection))
        result.update(status='SOURCE_REFERENCE' if facts else 'POLICY_DENIED',facts=facts,denials=denied,
                      projection_sha256=digest(projection),period_authority='ORIGINAL_PARSER_QUALITY_REPLAY_ONLY')
        for fact in facts:
            # Bind the exact projection to a captured evidence index. No new L3 permission.
            raw=encoded(dict(plan=plan,acquisition=acquisition,receipts=reader.receipts,projection=projection))
            sha=store.capture(run_id,'FinancialReplay',ticker,raw,dict(captured_at=now(),kind='DERIVED_REPLAY_NOT_NEW_RAW'))
            store.observation(run_id,ticker,'financial.'+fact['fields']['metric'],'SOURCE_REFERENCE',sha,
                dict(fact=fact,strict_native=False,original_owner_issued=False,source_captured_this_run=True))
    except Exception as exc:
        result.update(status='PROVIDER_LIMIT' if transport.stopped else 'POLICY_DENIED',errors=[safe_error(exc)])
        if hasattr(reader,'output_state'):(attempt/'partial-acquisition.json').write_bytes(encoded(reader.output_state))
    (attempt/'original-receipts.json').write_bytes(encoded(reader.receipts))
    (attempt/'research-result.json').write_bytes(encoded(result))
    finished.write_bytes(encoded(result))
    return result

async def completed_us_close(store,run_id,identity,as_of,client,transport):
    if identity not in store.identities():raise ValueError('registered_close_identity_mismatch')
    from app.services.kiwoom_completed_close_owner import validate_completed_daily_row
    target,calendar=target_session('us',as_of)
    exchange={'NASDAQ':'ND','NYSE':'NY','AMEX':'NA'}.get(identity['exchange'])
    if not exchange:raise ValueError('registered_exchange_missing')
    async with httpx.AsyncClient(base_url=client.base_url,transport=transport,timeout=90,follow_redirects=False) as http:
        token=await client._access_token(http)
        response=await http.post('/api/us/mrkcond',json=dict(stex_tp=exchange,stk_cd=identity['ticker'],base_dt=target.strftime('%Y%m%d')),
            headers={'api-id':'usa20590','authorization':'Bearer '+token,'cont-yn':'N','next-key':''})
    response.raise_for_status()
    row,integrity=validate_completed_daily_row(response.content,target)
    receipt=response.extensions['vnext']
    store.observation(run_id,identity['ticker'],'completed_close','CURRENT_VALID',receipt['raw_sha256'],
        dict(row=row,currency='USD',calendar=calendar,source_captured_at=receipt['captured_at'],
             strict_native=False,original_full_owner_issued=False,validator='kiwoom_completed_close_owner.validate_completed_daily_row',
             adjustment='PROVIDER_HISTORICAL_DAILY_CLOSE',integrity=integrity.model_dump(mode='json')))
    return dict(ticker=identity['ticker'],status='CURRENT_VALID',session=str(target),original_full_owner=False)
