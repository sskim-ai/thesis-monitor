"""Explicit native GET capabilities. V1 and direct Kiwoom Parents are untouched.

There is no live runtime enroller in the current service. Bare objects, receipts
and toggles cannot populate this registry. Offline tests install TEST_ONLY roots;
those roots can send only through MockTransport. Live enrollment fails closed
until an independently reviewed service/physical-transport adapter exists.
"""
from dataclasses import dataclass, field
from datetime import date,datetime,timezone
import hashlib,hmac,json,os
from pathlib import Path
import secrets
from threading import RLock
from typing import Literal
from weakref import WeakKeyDictionary
import httpx
from pydantic import Field,model_validator
from app.schemas.thesis import PriceContext
from app.services.unified_snapshot_contract import ContractModel,digest,encoded
from app.services.unified_source_observer import capture_source_response
from app.services.unified_run_artifacts import durable_json
from app.services.provider_native_technical import ProviderNativeTechnicalView
from app.services.ohlcv_completed_bar_finality_service import assess_completed_bar_finality

SCOPE=('DATED_TECHNICAL_RESEARCH_ONLY','NO_SEND','NO_MODEL','NO_CURRENT_PRICE_OWNER','NO_VALUATION_OWNER')
CONTRACT='native-get-source-v2'
_ROOTS=WeakKeyDictionary();_PARENTS=WeakKeyDictionary();_RESULTS=WeakKeyDictionary()
_LOCK=RLock()
ROOT=Path(__file__).resolve().parents[2]
PINS=('app/services/native_source_v2.py','app/services/ohlcv_client.py',
      'app/services/provider_native_technical.py','app/services/ohlcv_completed_bar_finality_service.py')

def _now():return datetime.now(timezone.utc)
def _pins():return {n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in PINS}

class NativeReadV2(ContractModel):
    contract:Literal['native-get-source-v2']=CONTRACT
    route:Literal['/ohlcv']='/ohlcv'
    method:Literal['GET']='GET'
    source_provider:Literal['ohlcv_analyst']='ohlcv_analyst'
    response_provider:Literal['kiwoom']='kiwoom'
    role:str=Field(pattern=r'^[A-Za-z0-9_.:-]+$')
    symbol:str=Field(pattern=r'^[A-Za-z0-9.^_-]+$')
    market:Literal['kr','us']
    security_id:str=Field(min_length=1)
    issuer_id:str=Field(min_length=1)
    exchange:str=Field(min_length=1)
    currency:Literal['KRW','USD']
    session:date
    period:Literal['daily']='daily'
    adjusted:Literal[True]=True
    count:int=Field(ge=1,le=1000,strict=True)
    indicator_limit:int=Field(ge=1,le=5,strict=True)
    include_indicators:Literal[True]=True
    include_investor_flows:bool=Field(strict=True)

    @model_validator(mode='after')
    def exact_scope(self):
        if self.indicator_limit!=min(self.count,5) or self.include_investor_flows!=(self.market=='kr'):
            raise ValueError('native_read_scope_mismatch')
        venues={'kr':{'KRX','KOSPI','KOSDAQ'},'us':{'NASDAQ','NYSE','AMEX','ND','NY','NA','NYSEARCA','NYSE ARCA'}}
        if self.exchange not in venues[self.market] or self.currency!=('KRW' if self.market=='kr' else 'USD'):
            raise ValueError('native_registered_venue_currency_required')
        return self

    def params(self):
        return dict(symbol=self.symbol,periods=self.period,count=self.count,
            include_indicators='true',indicator_limit=self.indicator_limit,adjusted='true',
            include_investor_flows=str(self.include_investor_flows).lower())

class NativeRuntimeRoot:
    __slots__=('__weakref__',)
class NativeGetParent:
    __slots__=('__weakref__',)
class NativeSourceResult:
    __slots__=('__weakref__',)

@dataclass
class _Runtime:
    mode:str
    issuer_id:str
    caller_id:str
    account_sha256:str
    service_code_sha256:str
    service_config_sha256:str
    endpoint:str
    generation_id:str
    expires:datetime
    bindings:tuple
    registration_check:object=field(repr=False)
    key:bytes=field(repr=False)
    pid:int=field(default_factory=os.getpid)
    active:bool=True
    meter_id:str|None=None
    physical_max:int=44
    issued:bool=False

def bind_live_runtime(*,participant=None):
    """No new authority from caller JSON or an old direct-Kiwoom Parent.

    This is the first missing integration, not an approval prompt or a bypass.
    A later reviewed host adapter must bind original current registration,
    explicit native GET consent, loaded service/account/Lane and ALL physical
    sends before it can enroll a live runtime. None is available in this task.
    """
    raise ValueError('native_signed_service_runtime_and_physical_adapter_required')

def _runtime(root):
    if type(root) is not NativeRuntimeRoot or root not in _ROOTS:
        raise ValueError('native_runtime_root_required')
    state=_ROOTS[root]
    if not state.active or state.pid!=os.getpid() or _now()>=state.expires:
        raise ValueError('native_runtime_expired_revoked_or_process_changed')
    state.registration_check()
    return state

def revoke_runtime(root):
    _runtime(root).active=False

def issue_parent(*,runtime,reads):
    r=_runtime(runtime)
    reads=tuple(NativeReadV2.model_validate_json(v.model_dump_json()) for v in reads)
    if not reads or len(reads)>2 or len({v.role for v in reads})!=len(reads):
        raise ValueError('native_exact_bounded_plan_required')
    expected={(v.market,v.symbol,v.security_id,v.issuer_id,v.exchange,v.currency,v.session.isoformat()) for v in reads}
    if expected!=set(r.bindings):raise ValueError('native_registration_identity_mismatch')
    parent=NativeGetParent()
    with _LOCK:
        # One original generation per runtime, not a resettable request counter.
        if r.issued:raise ValueError('native_generation_already_issued')
        plan=tuple(encoded(v.params()).decode() for v in reads)
        body=dict(contract=CONTRACT,mode=r.mode,issuer=r.issuer_id,caller=r.caller_id,
            account_sha256=r.account_sha256,service_code_sha256=r.service_code_sha256,
            service_config_sha256=r.service_config_sha256,generation=r.generation_id,
            expires=r.expires.isoformat(),physical_HTTP_max=r.physical_max,service_GET_max=len(reads),
            reads=[v.model_dump(mode='json') for v in reads],scope=SCOPE)
        _PARENTS[parent]=dict(runtime=runtime,reads=reads,plan=plan,pins=_pins(),pid=os.getpid(),
            receipt=body,signature=hmac.new(r.key,encoded(body),'sha256').hexdigest(),used=set(),
            pending={},failed=False,revoked=False,last_physical=0,meter_id=None)
        r.issued=True
    return parent,json.loads(encoded(dict(body,signature=_PARENTS[parent]['signature'])))

def _parent(parent):
    if type(parent) is not NativeGetParent or parent not in _PARENTS:raise ValueError('native_parent_required_not_kiwoom_parent')
    s=_PARENTS[parent];r=_runtime(s['runtime'])
    if s['failed'] or s['revoked'] or s['pid']!=os.getpid() or s['pins']!=_pins():
        raise ValueError('native_parent_failed_revoked_or_code_changed')
    binding=dict(issuer=r.issuer_id,caller=r.caller_id,account_sha256=r.account_sha256,
        service_code_sha256=r.service_code_sha256,service_config_sha256=r.service_config_sha256,
        generation=r.generation_id,expires=r.expires.isoformat(),physical_HTTP_max=r.physical_max)
    if any(s['receipt'][k]!=v for k,v in binding.items()):raise ValueError('native_runtime_binding_changed')
    if not hmac.compare_digest(s['signature'],hmac.new(r.key,encoded(s['receipt']),'sha256').hexdigest()):
        raise ValueError('native_parent_signature_mismatch')
    return s,r

def revoke_parent(parent):
    s,_=_parent(parent);s['revoked']=True

class PhysicalBudgetTransport(httpx.AsyncBaseTransport):
    """One meter for auth/data/lookup/pages; no retries and sticky stop.

    Implemented and exercised offline, NOT installed into the running service.
    Existing provider top-level httpx.post cannot be claimed instrumented by it.
    """
    def __init__(self,*,runtime,transport,maximum):
        r=_runtime(runtime)
        if type(maximum) is not int or maximum!=r.physical_max or maximum<1 or r.meter_id is not None:raise ValueError('native_meter_exact_budget_required')
        if r.mode=='TEST_ONLY' and type(transport) is not httpx.MockTransport:raise ValueError('native_test_only_transport_required')
        self.runtime=runtime;self.transport=transport;self.maximum=maximum
        self._calls=[];self.stopped=False;self.meter_id=secrets.token_hex(16)
        r.meter_id=self.meter_id

    async def handle_async_request(self,request):
        _runtime(self.runtime)
        with _LOCK:
            if self.stopped or len(self._calls)>=self.maximum:
                self.stopped=True;raise ValueError('native_physical_budget_or_STOP')
            item=dict(ordinal=len(self._calls)+1,kind='auth' if request.url.path=='/oauth2/token' else 'data',sha256=None)
            self._calls.append(item)
        try:
            response=await self.transport.handle_async_request(request)
            response.request=request
            await response.aread();response.raise_for_status()
            item['sha256']=hashlib.sha256(response.content).hexdigest()
            return response
        except BaseException:
            self.stopped=True;raise

    def proof(self,*,nonce,params,body,start=0):
        r=_runtime(self.runtime)
        if self.stopped:raise ValueError('native_physical_STOP')
        data=dict(nonce=nonce,query_sha256=digest(params),body_sha256=hashlib.sha256(body).hexdigest(),
            issuer=r.issuer_id,caller=r.caller_id,account_sha256=r.account_sha256,
            service_code_sha256=r.service_code_sha256,service_config_sha256=r.service_config_sha256,
            generation=r.generation_id,meter_id=self.meter_id,physical_count=len(self._calls),
            raw_pages=[x['sha256'] for x in self._calls[start:] if x['kind']=='data'])
        return {'X-Native-Source-Proof':encoded(data).decode(),
            'X-Native-Source-Signature':hmac.new(r.key,encoded(data),'sha256').hexdigest()}

    @property
    def calls(self):return tuple(dict(x) for x in self._calls)

class NativeObserverV2:
    def __init__(self,*,parent,root):
        s,_=_parent(parent)
        if root.exists() or any(p.is_symlink() for p in (root,*root.parents)):
            raise ValueError('native_new_plain_capture_root_required')
        self.parent=parent;self.root=root
        durable_json(root/'plan.json',dict(s['receipt'],signature=s['signature']),exclusive=True)

    def require_read(self,read):
        s,r=_parent(self.parent)
        if read not in s['reads']:raise ValueError('native_read_outside_plan')
        return r.endpoint

    async def get(self,client,route,*,params):
        s,r=_parent(self.parent)
        try:
            if r.mode=='TEST_ONLY' and type(client._transport) is not httpx.MockTransport:
                raise ValueError('native_test_only_service_transport_required')
            frozen=encoded(params).decode()
            if route!='/ohlcv' or frozen not in s['plan'] or str(client.base_url).rstrip('/')!=r.endpoint:
                raise ValueError('native_wire_outside_exact_plan')
            with _LOCK:
                if frozen in s['used']:raise ValueError('native_GET_replay_or_budget_exhausted')
                s['used'].add(frozen)
            read=s['reads'][s['plan'].index(frozen)];nonce=secrets.token_hex(16)
            identity='read-'+str(len(s['used']))
            receipt=dict(contract=CONTRACT,mode=r.mode,read=read.model_dump(mode='json'),
                frozen_query=frozen,query_sha256=digest(params),nonce=nonce,
                parent_sha256=digest(s['receipt']),scope=SCOPE)
            async def send():
                response=await client.get(route,params=params,headers={'X-Native-Source-Nonce':nonce})
                if len(response.content)>8*1024**2:raise ValueError('native_response_size_exceeded')
                return response
            response=await capture_source_response(root=self.root,identity=identity,receipt=receipt,send=send)
            response.raise_for_status();_parent(self.parent)
            proof=json.loads(response.headers.get('X-Native-Source-Proof','{}'))
            signature=response.headers.get('X-Native-Source-Signature','')
            if not hmac.compare_digest(signature,hmac.new(r.key,encoded(proof),'sha256').hexdigest()):
                raise ValueError('native_service_signature_mismatch')
            expected=dict(nonce=nonce,query_sha256=digest(params),body_sha256=hashlib.sha256(response.content).hexdigest(),
                issuer=r.issuer_id,caller=r.caller_id,account_sha256=r.account_sha256,
                service_code_sha256=r.service_code_sha256,service_config_sha256=r.service_config_sha256,generation=r.generation_id)
            if any(proof.get(k)!=v for k,v in expected.items()):raise ValueError('native_service_account_issuer_or_body_mismatch')
            if (not proof.get('raw_pages') or not all(isinstance(v,str) and len(v)==64 for v in proof['raw_pages'])
                    or proof.get('meter_id')!=r.meter_id or type(proof.get('physical_count')) is not int
                    or not s['last_physical']<proof['physical_count']<=r.physical_max):
                raise ValueError('native_physical_budget_or_pages_unproven')
            s['last_physical']=proof['physical_count']
            payload=response.json();resolved=payload.get('resolved_symbol',{});meta=payload.get('meta',{})
            if (resolved.get('code')!=read.symbol or str(resolved.get('market','')).lower()!=read.market
                    or resolved.get('exchange')!=read.exchange
                    or meta.get('provider')!='kiwoom' or meta.get('adjusted') is not True
                    or set(payload.get('periods',{}))!={'daily'}):raise ValueError('native_response_identity_or_basis')
            s['pending'][id(response)]=dict(read=read,receipt=receipt,proof=proof,response=response,normalized=None)
            durable_json(self.root/(identity+'.proof.json'),dict(proof,signature=signature),exclusive=True)
            return response
        except BaseException:
            s['failed']=True;raise

    def normalized(self,response,*,normalized,contract,valid,fingerprint):
        from app.services.ohlcv_client import OhlcvClient
        s,_=_parent(self.parent)
        try:
            p=s['pending'].get(id(response))
            if p is None or p['normalized'] is not None or not valid:raise ValueError('native_normalization_or_replay_denied')
            read=p['read']
            identity,wire=response.extensions['unified_source_receipt']
            artifact=self.root/(identity+'.body')
            body_hash=hashlib.sha256(response.content).hexdigest()
            if (wire.get('artifact')!=identity+'.body' or artifact.is_symlink()
                    or hashlib.sha256(artifact.read_bytes()).hexdigest()!=body_hash
                    or p['proof']['body_sha256']!=body_hash):
                raise ValueError('native_raw_artifact_or_body_mismatch')
            bars,supply,_=OhlcvClient._decode_period_payload(response.json(),ticker=read.symbol,period='daily',adjusted=True,
                response_body_sha256=hashlib.sha256(response.content).hexdigest())
            if digest(dict(bars=bars,supply_demand=supply))!=digest(normalized):raise ValueError('native_parser_or_body_mismatch')
            if not bars or any(assess_completed_bar_finality(b,cutoff=read.session).state!='FINAL' for b in bars):
                raise ValueError('native_completed_daily_required')
            if bars[-1]['date']!=read.session.isoformat():raise ValueError('native_current_completed_session_mismatch')
            p['normalized']=digest(normalized)
            durable_json(self.root/(read.role+'.normalization.json'),dict(contract=contract,valid=True,
                fingerprint=fingerprint,normalized_sha256=p['normalized'],raw_sha256=hashlib.sha256(response.content).hexdigest(),
                scope=SCOPE,mode=s['receipt']['mode']),exclusive=True)
        except BaseException:
            s['failed']=True;raise

    def finish(self,read,context):
        s,r=_parent(self.parent)
        try:
            found=[p for p in s['pending'].values() if p['read']==read and p['normalized']]
            if len(found)!=1:raise ValueError('native_complete_receipt_required')
            view=ProviderNativeTechnicalView.model_validate(context.technical_context_payload()['native_view']).verify()
            if view.periods['daily'].status!='AVAILABLE' or view.periods['daily'].completed_as_of!=read.session.isoformat():
                raise ValueError('native_daily_projection_denied')
            result=NativeSourceResult()
            public=dict(contract=CONTRACT,mode=r.mode,source_hash=view.source_hash,view_sha256=view.view_sha256,
                parser_sha256=found[0]['normalized'],read=read.model_dump(mode='json'),scope=SCOPE,
                parent_sha256=digest(s['receipt']),physical_count=s['last_physical'],service_GET_count=len(s['used']))
            _RESULTS[result]=dict(parent=self.parent,receipt_json=encoded(public).decode(),
                context_sha256=digest(context.model_dump(mode='json')),
                technical_sha256=digest(context.technical_context_payload()),used=False)
            del s['pending'][id(found[0]['response'])]
            durable_json(self.root/(read.role+'.source-result.json'),public,exclusive=True)
            return result,json.loads(encoded(public))
        except BaseException:
            s['failed']=True;raise

def consume_result(*,parent,result,context):
    state,_=_parent(parent)
    if state['pending'] or len(state['used'])!=len(state['plan']):raise ValueError('native_cohort_not_committed')
    if type(result) is not NativeSourceResult or result not in _RESULTS:raise ValueError('native_result_capability_required')
    s=_RESULTS[result]
    if (s['parent'] is not parent or s['used'] or s['context_sha256']!=digest(context.model_dump(mode='json'))
            or s['technical_sha256']!=digest(context.technical_context_payload())):
        raise ValueError('native_result_replay_or_context_changed')
    s['used']=True
    return json.loads(s['receipt_json'])

async def fetch_native_daily(*,client,observer,read,as_of):
    """Protected entry: never fall back to client.get without a V2 Parent."""
    if type(observer) is not NativeObserverV2 or client.source_observer is not observer:
        raise ValueError('native_protected_observer_required')
    endpoint=observer.require_read(read)
    if client.settings.ohlcv_base_url.rstrip('/')!=endpoint or client.settings.monitor_retry_attempts!=1:
        raise ValueError('native_exact_endpoint_and_zero_retry_required')
    if client.completion_verifier is not None:raise ValueError('native_original_completion_owner_required')
    headers={'X-API-Key':client.settings.ohlcv_api_key or client.settings.action_api_key}
    headers={k:v for k,v in headers.items() if v}
    audit=dict(request_count=0,success_count=0,retry_count=0,failure_classes=[])
    try:
        async with httpx.AsyncClient(base_url=endpoint,transport=client.transport,headers=headers,
                                   timeout=client.settings.ohlcv_timeout_seconds) as h:
            summary,bars=await client._request_period(h,read.symbol,'daily',read.count,acquisition_audit=audit)
        context=PriceContext(price_source_scope='dated_technical_only',periods={'daily':summary})
        enabled=client.settings.kr_price_structure_v3_enabled if read.market=='kr' else client.settings.us_price_structure_v3_enabled
        context=client._finalize_native_context(ticker=read.symbol,context=context,adjusted_bars={'daily':bars},
            technical_acquisition=audit,as_of=as_of,price_structure_enabled=enabled)
        capability,receipt=observer.finish(read,context)
        return context,capability,receipt
    except BaseException:
        if observer.parent in _PARENTS:_PARENTS[observer.parent]['failed']=True
        raise
