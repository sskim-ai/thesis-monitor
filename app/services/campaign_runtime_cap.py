"""Shared cost limiter over SelectedRunLedger's existing file, not authorization.

This module has no app imports so the ordinary OHLCV service can use identical
code without importing a second app package. It never creates a journal, grants
Source rights or replaces the account Lane. The approved backend creates it.
"""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re


def encoded(value):
    return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()


def digest(value):
    return hashlib.sha256(encoded(value)).hexdigest()


def runtime_state():
    return dict(total=0,providers={},pending={},attempts={},stopped_providers=[],first_external_failure=None)


OPTIONAL_NEWS_429 = 'SELECTED_US_OPTIONAL_NEWS_429_V1'


def optional_news_attempt(attempt, identity):
    scope = attempt.get('optional_news', {})
    child = identity.get('children', {}).get('us', {})
    return (identity.get('runtime_cap', {}).get('optional_news_429') == OPTIONAL_NEWS_429
        and attempt.get('provider') == 'google_news_rss' and attempt.get('market') == 'us'
        and attempt.get('phase') == 'SOURCE' and attempt.get('method') == 'GET'
        and attempt.get('endpoint') == 'GOOGLE_NEWS_RSS'
        and attempt.get('owner') == 'SelectedSourceDispatcher'
        and attempt.get('generation') == child.get('generation')
        and attempt.get('subject') in child.get('subjects', ())
        and scope.get('logical_id') == 'events:' + attempt.get('subject', '')
        and scope.get('mandatory') is False and scope.get('operation') == 'news'
        and all(re.fullmatch('[a-f0-9]{64}', scope.get(k, ''))
                for k in ('plan_sha256', 'descriptor_sha256')))


def optional_news_result(attempt, identity):
    return (optional_news_attempt(attempt, identity)
        and attempt.get('outcome') == 'HTTP_RESPONSE' and attempt.get('status') == 429)


def apply_runtime_event(state,event,value,identity):
    if event=='PHYSICAL_INTENT':
        caps=identity['runtime_cap']
        provider=value['provider']
        key=value['attempt_id']
        if (market:=identity.get('fresh_timeout_retry_market')) and (
                value['market']!=market or value['phase']!='SOURCE'):
            raise ValueError('PHYSICAL_FRESH_TIMEOUT_RETRY_MARKET_SCOPE')
        if (key in state['attempts'] or provider in state['stopped_providers']
                or (identity.get('staged_markets') and state['pending'])
                or state['first_external_failure'] is not None
                or state['total']>=identity['max_http']
                or state['providers'].get(provider,0)>=identity['provider_caps'].get(provider,0)):
            raise ValueError('CAP_EXHAUSTED_OR_ATTEMPT_ALREADY_USED')
        if value['generation']!=identity['children'][value['market']]['generation']:
            raise ValueError('PHYSICAL_CAMPAIGN_GENERATION_MISMATCH')
        state['total']+=1
        state['providers'][provider]=state['providers'].get(provider,0)+1
        state['attempts'][key]=value
        state['pending'][key]=value
    elif event=='PHYSICAL_DISPATCH':
        key=value['attempt_id']
        if key not in state['pending'] or state['pending'][key].get('transport_entered'):
            raise ValueError('PHYSICAL_DISPATCH_WITHOUT_NEW_INTENT')
        state['pending'][key]['transport_entered']=True
        state['attempts'][key]['transport_entered']=True
    elif event=='PHYSICAL_RESULT':
        key=value['attempt_id']
        if key not in state['pending']:
            raise ValueError('PHYSICAL_RESULT_WITHOUT_PENDING_INTENT')
        provider=state['pending'].pop(key)['provider']
        state['attempts'][key]={**state['attempts'][key],**value}
        if (not optional_news_result(state['attempts'][key], identity)
                and identity['runtime_cap'].get('stop_on_first_external_failure') and
                (value['outcome']=='TRANSPORT_UNKNOWN' or (value.get('status') or 0)>=400)):
            state['first_external_failure']=key
        if value.get('status') in (401,403,429) or value['outcome']=='TRANSPORT_UNKNOWN':
            if provider not in state['stopped_providers']:
                state['stopped_providers'].append(provider)
    else:
        raise ValueError('UNKNOWN_PHYSICAL_EVENT')


class RuntimeCap:
    def __init__(self,binding):
        self.path=Path(binding['path'])
        if (not self.path.is_absolute() or not self.path.is_file()
                or any(p.is_symlink() for p in (self.path,*self.path.parents))):
            raise ValueError('EXISTING_CAMPAIGN_JOURNAL_REQUIRED')
        self.pin=binding['identity_sha256']
        self._locked()

    def _locked(self,event=None,value=None):
        with os.fdopen(os.open(self.path,os.O_RDWR|os.O_APPEND|os.O_NOFOLLOW),'r+b') as stream:
            fcntl.flock(stream,fcntl.LOCK_EX)
            raw=stream.read()
            if not raw or not raw.endswith(b'\n'):
                raise ValueError('CAMPAIGN_JOURNAL_MISSING_OR_TORN')
            state=runtime_state()
            previous=None
            identity=None
            terminal=False
            capture_cutoff=None
            market_capture_cutoffs={}
            pending_markets=[]
            rendered_markets=set()
            frozen_plans={}
            closed_source=set()
            for sequence,line in enumerate(raw.splitlines()):
                row=json.loads(line)
                pin=row.pop('sha256')
                if identity is None:
                    identity=row['identity']
                    if digest(identity)!=self.pin:
                        raise ValueError('CAMPAIGN_JOURNAL_CHAIN_DRIFT')
                if (row['identity']!=identity
                        or row['sequence']!=sequence or row['previous']!=previous or digest(row)!=pin):
                    raise ValueError('CAMPAIGN_JOURNAL_CHAIN_DRIFT')
                if row['event'] in ('STOP','RENDER'):terminal=True
                if row['event']=='DB_INTENT':pending_markets=row['value'].get('markets',list(identity['children']))
                if row['event']=='REGISTRATION':
                    capture_cutoff=row['value']['receipt']['cutoff']
                    market_capture_cutoffs.update({m:capture_cutoff for m in pending_markets})
                if row['event']=='PLAN':
                    frozen_plans[row['value']['market']]=row['value']['sha256']
                if row['event']=='CAPTURE':closed_source.add(row['value']['market'])
                if identity.get('staged_markets') and row['event'] in ('RENDER_MARKET','MARKET_FAILED'):
                    rendered_markets.add(row['value']['market'])
                    if rendered_markets==set(identity['children']):terminal=True
                if row['event'].startswith('PHYSICAL_'):
                    apply_runtime_event(state,row['event'],row['value'],identity)
                previous=pin
            if not identity.get('runtime_cap'):
                raise ValueError('RUNTIME_LIMITER_NOT_ENABLED')
            if event is None:
                state['terminal']=terminal
                return identity,state
            if event=='PHYSICAL_INTENT':
                if value.get('optional_news') and (not optional_news_attempt(value, identity)
                        or value['optional_news']['plan_sha256'] != frozen_plans.get(value['market'])):
                    raise ValueError('PHYSICAL_OPTIONAL_NEWS_FROZEN_PLAN_MISMATCH')
                now=datetime.now(timezone.utc)
                if (terminal or not datetime.fromisoformat(identity['authorized_at'])<=now<
                        datetime.fromisoformat(identity['expires_at'])):
                    raise ValueError('CAMPAIGN_EXPIRED_OR_STOPPED')
                if identity.get('staged_markets'):
                    capture_cutoff=market_capture_cutoffs.get(value['market']) if value['phase']=='SOURCE' else None
                    if value['phase']=='SOURCE' and capture_cutoff is None:
                        raise ValueError('CAMPAIGN_CURRENT_MARKET_CAPTURE_REQUIRED')
                if identity.get('fresh_timeout_retry_market') and (
                        value['market'] not in frozen_plans or value['market'] in closed_source):
                    raise ValueError('CAMPAIGN_FROZEN_OPEN_SOURCE_REQUIRED')
                if capture_cutoff and now>=datetime.fromisoformat(capture_cutoff)+timedelta(hours=1):
                    raise ValueError('CAMPAIGN_ORIGINAL_CAPTURE_WINDOW_EXPIRED')
                maximum=identity.get('wallclock_seconds_max')
                if maximum is not None and (now-datetime.fromisoformat(identity['authorized_at'])).total_seconds()>=maximum:
                    raise ValueError('CAMPAIGN_WALLCLOCK_EXHAUSTED')
            apply_runtime_event(state,event,value,identity)
            row=dict(identity=identity,sequence=sequence+1,previous=previous,event=event,value=value,
                recorded_at=datetime.now(timezone.utc).isoformat())
            row['sha256']=digest(row)
            stream.write(encoded(row)+b'\n')
            stream.flush()
            os.fsync(stream.fileno())
            return identity,state

    def state(self):
        return self._locked()[1]

    def require_current(self):
        identity,state=self._locked()
        now=datetime.now(timezone.utc)
        if state['terminal'] or state['first_external_failure'] is not None or not datetime.fromisoformat(identity['authorized_at'])<=now<datetime.fromisoformat(identity['expires_at']):
            raise ValueError('CAMPAIGN_EXPIRED_OR_STOPPED')
        return identity

    def reserve(self,*,provider,method,host,path,market,subject,phase,owner,
                request_sha256,attempt_id=None,optional_news=None):
        identity,_=self._locked()
        child=identity['children'].get(market,{})
        market_subjects = identity['runtime_cap'].get('market_subjects',{}).get(market,()) if phase=='SOURCE' else ()
        if subject not in (*child.get('subjects',()),*market_subjects,'*') or phase not in ('ONBOARDING','SOURCE'):
            raise ValueError('PHYSICAL_SUBJECT_OR_PHASE_OUTSIDE_CAMPAIGN')
        matches=[rule for rule in identity['runtime_cap']['endpoints'].get(provider,())
            if method in rule['methods'] and host==rule['host'] and path.startswith(rule['prefix'])]
        if not matches:
            raise ValueError('PHYSICAL_ENDPOINT_OUTSIDE_CAMPAIGN')
        rule=max(matches,key=lambda r:len(r['prefix']))
        if not re.fullmatch('[A-Za-z0-9_.:-]{1,100}',owner):
            raise ValueError('PHYSICAL_OWNER_LABEL_INVALID')
        key=attempt_id or digest([identity['master_id'],child['generation'],phase,subject,provider,request_sha256])
        value=dict(attempt_id=key,campaign_id=identity['master_id'],generation=child['generation'],
            provider=provider,endpoint=rule['endpoint'],method=method,subject=subject,market=market,
            phase=phase,owner=owner,worker_pid=os.getpid(),timestamp=datetime.now(timezone.utc).isoformat(),
            request_sha256=request_sha256)
        if optional_news is not None:
            value['optional_news'] = deepcopy(optional_news)
        self._locked('PHYSICAL_INTENT',value)
        return key

    def finish(self,key,*,status=None,error=None):
        value=dict(attempt_id=key,status=status,outcome='TRANSPORT_UNKNOWN' if error else 'HTTP_RESPONSE')
        if error:value['error_type']=type(error).__name__
        self._locked('PHYSICAL_RESULT',value)

    def dispatched(self,key):
        self._locked('PHYSICAL_DISPATCH',dict(attempt_id=key))


_SECRET=re.compile(r'key|secret|token|authorization|password|cookie',re.I)


def public_fingerprint(*,method,endpoint,query=(),body=None,api_id=None):
    def clean(value):
        if isinstance(value,dict):
            return {k:clean(v) for k,v in value.items() if not _SECRET.search(k)}
        if isinstance(value,list):return [clean(v) for v in value]
        return value
    return digest(dict(method=method,endpoint=endpoint,
        query=sorted((k,v) for k,v in query if not _SECRET.search(k)),body=clean(body),api_id=api_id))


def reserve_request(cap,request,*,provider,market,subject,phase,owner,optional_news=None):
    try:body=json.loads(request.content) if request.content else None
    except (ValueError,RuntimeError):body=None
    # ECOS credentials can be in the path; record only the approved endpoint label.
    identity,_=cap._locked()
    rules=[r for r in identity['runtime_cap']['endpoints'].get(provider,())
        if request.url.host==r['host'] and request.url.path.startswith(r['prefix'])]
    if (request.url.scheme!='https' or not any((request.url.port or 443) in r.get('ports',[443]) for r in rules)):
        raise ValueError('PHYSICAL_TLS_OR_PORT_OUTSIDE_CAMPAIGN')
    endpoint=max(rules,key=lambda r:len(r['prefix']))['endpoint'] if rules else 'UNAPPROVED'
    route=endpoint if any(r.get('path_contains_credentials') for r in rules) else endpoint+':'+request.url.path
    if provider == 'ecos' and request.url.path.startswith('/api/StatisticSearch/'):
        # The API key occupies exactly one path component. Keep only the public
        # table/date/item identity so different currencies are separate attempts;
        # a repeated request for the same currency still has the same identity.
        public = re.fullmatch(r'/api/StatisticSearch/[^/]+/(json/kr/1/100/731Y001/D/'
                              r'\d{8}/\d{8}/(?:0000002|0000003))', request.url.path)
        if public is None:
            raise ValueError('PHYSICAL_ECOS_PUBLIC_ROUTE_REQUIRED')
        route = endpoint + ':/api/StatisticSearch/[REDACTED]/' + public[1]
    cursor=digest(request.headers.get('next-key',''))
    fingerprint=public_fingerprint(method=request.method,endpoint=route,query=request.url.params.multi_items(),
        body=body,api_id=[request.headers.get('api-id') or request.headers.get('tr_id'),cursor])
    return cap.reserve(provider=provider,method=request.method,host=request.url.host,path=request.url.path,
        market=market,subject=subject,phase=phase,owner=owner,request_sha256=fingerprint,
        optional_news=optional_news)


def provider_for_request(cap,request):
    identity,_=cap._locked()
    matches={provider for provider,rules in identity['runtime_cap']['endpoints'].items()
        for rule in rules if request.method in rule['methods'] and request.url.host==rule['host']
        and request.url.path.startswith(rule['prefix'])}
    if len(matches)!=1:
        raise ValueError('PHYSICAL_ENDPOINT_PROVIDER_UNBOUND')
    return matches.pop()


class _TransportMixin:
    def _setup(self,*,binding,market,subject,phase,owner,inner):
        self.cap=RuntimeCap(binding)
        self.context=dict(market=market,subject=subject,phase=phase,owner=owner)
        self.inner=inner


# Shared code is imported in each service's own app namespace; never co-import
# Thesis Monitor and ohlcv-analyst app packages into one process.
import httpx


class MeteredAsyncTransport(_TransportMixin,httpx.AsyncBaseTransport):
    def __init__(self,*,binding,market,subject='*',phase='ONBOARDING',owner='OriginalProvider',inner=None,
                 optional_news=None):
        self._setup(binding=binding,market=market,subject=subject,phase=phase,owner=owner,
            inner=inner if inner is not None else httpx.AsyncHTTPTransport(retries=0))
        if optional_news is not None:
            self.context['optional_news'] = optional_news

    async def handle_async_request(self,request):
        provider=provider_for_request(self.cap,request)
        key=reserve_request(self.cap,request,provider=provider,**self.context)
        try:
            self.cap.dispatched(key)
            response=await self.inner.handle_async_request(request)
            await response.aread()
        except BaseException as exc:
            self.cap.finish(key,error=exc)
            raise
        self.cap.finish(key,status=response.status_code)
        return response

    async def aclose(self):
        pass  # The campaign owns its shared underlying transport lifetime.


class MeteredSyncTransport(_TransportMixin,httpx.BaseTransport):
    def __init__(self,*,binding,market,subject='*',phase='SOURCE',owner='OriginalWorker',inner=None):
        self._setup(binding=binding,market=market,subject=subject,phase=phase,owner=owner,
            inner=inner if inner is not None else httpx.HTTPTransport(retries=0))

    def handle_request(self,request):
        provider=provider_for_request(self.cap,request)
        key=reserve_request(self.cap,request,provider=provider,**self.context)
        try:
            self.cap.dispatched(key)
            response=self.inner.handle_request(request)
            response.read()
        except BaseException as exc:
            self.cap.finish(key,error=exc)
            raise
        self.cap.finish(key,status=response.status_code)
        return response

    def close(self):
        self.inner.close()


class CampaignOhlcvTransport(httpx.AsyncBaseTransport):
    """An internal service GET is not charged as an external Kiwoom POST."""
    def __init__(self,*,binding,market,subject,phase='ONBOARDING',inner=None):
        self.binding=deepcopy(binding)
        self.cap=RuntimeCap(binding)
        self.market,self.subject,self.phase=market,subject,phase
        self.inner=inner if inner is not None else httpx.AsyncHTTPTransport(retries=0)
        self._service_checked=False

    def require_binding(self,ledger,ticker):
        if ledger.worker_binding()!=self.binding or ticker!=self.subject:
            raise ValueError('OHLCV_CAMPAIGN_BINDING_CHANGED')

    async def handle_async_request(self,request):
        if (request.method!='GET' or request.url.path!='/ohlcv'
                or request.url.host not in ('127.0.0.1','localhost','::1')
                or request.url.params.get('symbol')!=self.subject):
            raise ValueError('OHLCV_ORDINARY_LOCAL_CAMPAIGN_ROUTE_REQUIRED')
        # Validate the existing durable journal before asking the local service.
        identity=self.cap.require_current()
        allowed=identity['children'][self.market]['subjects']
        if self.phase=='SOURCE':
            allowed=[*allowed,*identity['runtime_cap'].get('market_subjects',{}).get(self.market,())]
        if self.subject not in allowed:
            raise ValueError('OHLCV_SUBJECT_OUTSIDE_CAMPAIGN')
        if not self._service_checked:
            probe=httpx.Request('OPTIONS',request.url.copy_with(query=None),headers=request.headers)
            support=await self.inner.handle_async_request(probe)
            await support.aread()
            if support.status_code!=200 or support.json().get('campaign_budget_protocol')!='selected-run-physical-cap-v1':
                raise ValueError('PHYSICAL_EGRESS_NOT_METERED_SERVICE_NOT_PREPARED')
            self._service_checked=True
        request.headers['X-Campaign-Budget']=json.dumps(dict(binding=self.binding,
            market=self.market,subject=self.subject,phase=self.phase),separators=(',',':'))
        request.headers['X-Research-Run']='campaign_'+digest([self.binding,self.subject,self.phase])[:40]
        request.headers['X-Research-Remaining-Max']='44'
        return await self.inner.handle_async_request(request)

    async def aclose(self):
        pass
