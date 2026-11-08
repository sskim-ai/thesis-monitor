"""TEST_ONLY runtime roots; never enroll a live service or original registration."""
import asyncio
from copy import deepcopy
from datetime import datetime,timedelta,timezone
import hashlib,hmac,json,os
from pathlib import Path
import httpx
import pytest
from app.config import Settings
from app.services import native_source_v2 as v2
from app.services import ohlcv_client as cli
from app.services.unified_snapshot_contract import digest,encoded
from app.services.unified_source_observer import OhlcvRead,OhlcvReceiptObserver
from app.services.unified_source_policy import UnifiedSourcePolicy
from app.services.current_scoped_source_owner import CurrentScopedSourceParent
from app.services.packet_owned_technical_context_service import load_packet_owned_technical_context
from app.services.cross_market_decision_engine_service import build_decision_evidence_packet,compact_ai_context
from app.services.kr_price_structure_selective_rollout_service import build_kr_price_structure_rollout_decision
from app.services.us_price_structure_selective_rollout_service import build_us_price_structure_rollout_decision
from test_provider_native_technical import raw_payload

NOW=datetime(2026,11,8,14,30,tzinfo=timezone.utc)

def read(market):
    return v2.NativeReadV2(role=market+'-daily',symbol='047810' if market=='kr' else 'CORZ',market=market,
        security_id='SYNTHETIC:'+market,issuer_id='SYNTHETIC-ISSUER:'+market,session='2026-11-06',
        exchange='KRX' if market=='kr' else 'NASDAQ',currency='KRW' if market=='kr' else 'USD',
        count=300,indicator_limit=5,include_investor_flows=market=='kr')

def v1_read(market,flows=False):
    r=read(market);p=r.params()
    if not flows:p.pop('include_investor_flows')
    return OhlcvRead(role=r.role,symbol=r.symbol,market=market,provider='ohlcv_analyst',response_provider='kiwoom',
        period='daily',adjusted=True,session_date=r.session,params=p,max_requests=1)

@pytest.mark.parametrize('market',['kr','us'])
def test_baseline_v1_rejects_explicit_flow_field(market):
    with pytest.raises(ValueError,match='source_request_field_not_authorized'):v1_read(market,True)

def test_baseline_v1_frozen_query_mismatch_without_send(tmp_path):
    r=v1_read('kr');hits=[]
    observer=OhlcvReceiptObserver(root=tmp_path/'v1',run_id='TEST',attempt_id='TEST',reads=(r,),
        policy=UnifiedSourcePolicy(frozenset({'ohlcv_analyst','kiwoom'})))
    async def run():
        async with httpx.AsyncClient(base_url='https://native.invalid',transport=httpx.MockTransport(lambda req:hits.append(req))) as c:
            await observer.get(c,'/ohlcv',params=read('kr').params())
    with pytest.raises(ValueError,match='source_request_outside_frozen_plan'):asyncio.run(run())
    assert not hits

def test_baseline_direct_kiwoom_parent_is_not_native_root():
    with pytest.raises(ValueError,match='native_runtime_root_required'):
        v2.issue_parent(runtime=CurrentScopedSourceParent(),reads=[read('kr')])


def harness(monkeypatch,tmp_path,markets=('kr',),maximum=None,fault=None):
    monkeypatch.setattr(v2,'_now',lambda:NOW)
    reads=tuple(read(m) for m in markets)
    # White-box TEST_ONLY fixture. This is not a production registration issuer.
    root=v2.NativeRuntimeRoot();lease={'active':True}
    def registration():
        if not lease['active']:raise ValueError('TEST_ONLY_registration_closed')
    state=v2._Runtime(mode='TEST_ONLY',issuer_id='fixture-issuer',caller_id='fixture-caller',
        account_sha256='a'*64,service_code_sha256='b'*64,service_config_sha256='c'*64,
        endpoint='https://native.invalid',generation_id='C21U_TEST_ONLY',expires=NOW+timedelta(minutes=5),
        bindings=tuple((r.market,r.symbol,r.security_id,r.issuer_id,r.exchange,r.currency,r.session.isoformat()) for r in reads),
        registration_check=registration,key=b'SYNTHETIC signing key, no credential',physical_max=maximum or 2*len(reads))
    v2._ROOTS[root]=state
    parent,receipt=v2.issue_parent(runtime=root,reads=reads)
    observer=v2.NativeObserverV2(parent=parent,root=tmp_path/'native-source')
    physical=[];service=[]
    def downstream(request):
        physical.append(request.url.path)
        return httpx.Response(403 if fault=='http403' else 200,json={'fixture_page':'PUBLIC_SYNTHETIC'})
    meter=v2.PhysicalBudgetTransport(runtime=root,transport=httpx.MockTransport(downstream),maximum=state.physical_max)
    async def handle(request):
        service.append(dict(request.url.params));p=dict(request.url.params)
        p['count']=int(p['count']);p['indicator_limit']=int(p['indicator_limit'])
        selected=next(r for r in reads if r.symbol==p['symbol'])
        start=len(meter.calls)
        async with httpx.AsyncClient(base_url='https://downstream.invalid',transport=meter) as inner:
            await inner.post('/oauth2/token')
            await inner.post('/chart/page')
        payload=raw_payload(selected.symbol,selected.market,'daily',85)
        rows=payload['periods']['daily'];native=deepcopy(rows[-1]['indicators'])
        for row in rows[-5:]:
            row['indicators']=deepcopy(native)
            if selected.market=='kr':row['investor_flow']={'foreign_net_buy_qty':7,'foreign_net_buy_qty_20':140}
        if fault=='ticker':payload['resolved_symbol']['code']='OTHER'
        if fault=='duplicate':rows.append(deepcopy(rows[-1]))
        if fault=='partial':rows[-1]['bar_state']='PARTIAL'
        if fault=='ohlc':rows[-1]['low']=rows[-1]['high']+1
        body=json.dumps(payload).encode()
        headers=meter.proof(nonce=request.headers['X-Native-Source-Nonce'],params=p,body=body,start=start)
        if fault in ('account','service','issuer','caller','missing_pages'):
            proof=json.loads(headers['X-Native-Source-Proof'])
            if fault=='missing_pages':proof['raw_pages']=[]
            else:proof[{'account':'account_sha256','service':'service_code_sha256','issuer':'issuer','caller':'caller'}[fault]]='WRONG'
            headers['X-Native-Source-Proof']=encoded(proof).decode()
            headers['X-Native-Source-Signature']=hmac.new(state.key,encoded(proof),'sha256').hexdigest()
        if fault=='signature':headers['X-Native-Source-Signature']='0'*64
        return httpx.Response(200,content=body,headers=headers)
    settings=Settings(_env_file=None,ohlcv_base_url=state.endpoint,monitor_retry_attempts=1,
        kr_price_structure_v3_enabled=True,us_price_structure_v3_enabled=True)
    monkeypatch.setattr(cli,'get_settings',lambda:settings)
    class MutationClient(cli.OhlcvClient):
        def _observe_normalization(self,response,bars,supply,inspection):
            if fault=='parser':bars[-1]['close']+=.01
            return super()._observe_normalization(response,bars,supply,inspection)
        async def _get_period(self,c,params):
            response=await super()._get_period(c,params)
            if fault=='body':response._content=response.content+b' '
            return response
    client=MutationClient(transport=httpx.MockTransport(handle),source_observer=observer)
    return dict(root=root,state=state,lease=lease,reads=reads,parent=parent,observer=observer,client=client,
        meter=meter,physical=physical,service=service,receipt=receipt)

def fetch(h,r):
    return asyncio.run(v2.fetch_native_daily(client=h['client'],observer=h['observer'],read=r,as_of=NOW))

def test_v2_two_markets_source_to_original_sr_no_send(monkeypatch,tmp_path):
    from app.services import packet_owned_technical_context_service as packet
    from app.services import price_structure_wave_fibonacci_v3_service as structure
    def forbidden(*a,**k):pytest.fail('Native indicator recomputation')
    monkeypatch.setattr(packet,'build_multi_timeframe_feature_packet',forbidden)
    monkeypatch.setattr(structure,'_bollinger_sources',forbidden)
    monkeypatch.setattr(structure,'_provisional_bollinger_sources',forbidden)
    h=harness(monkeypatch,tmp_path,('kr','us'));results=[];outputs=[]
    for r in h['reads']:
        context,cap,receipt=fetch(h,r);results.append((context,cap))
        native=context.technical_context_payload()['native_view']
        assert receipt['mode']=='TEST_ONLY' and native['periods']['daily']['completed_count']==85
        assert native['periods']['daily']['indicators']['RSI14']==47.123456789
        assert native['periods']['daily']['indicators']['MA288'] is None
        assert native['periods']['weekly']['status']=='UNAVAILABLE'
        assert context.decision.current_price is None
        if r.market=='kr':assert context.supply.foreign_net_buy_qty_20==140
        else:assert not context.supply.available
        technical=load_packet_owned_technical_context(context.technical_context_payload(),ticker=r.symbol)
        evidence=build_decision_evidence_packet(packet={'packet_id':'C21U_TEST','market':r.market,'assessment_date':r.session.isoformat()},
            stock={'ticker':r.symbol,'company_name':'SYNTHETIC','fact_catalog':[]},technical_context=technical)
        runtime=context.chart.structure['price_structure_v3']
        fn=build_kr_price_structure_rollout_decision if r.market=='kr' else build_us_price_structure_rollout_decision
        rendered=fn(runtime,ticker=r.symbol,monitored_subject=True,enabled=True)
        assert rendered.section and rendered.numeric_bindings and not rendered.render_validation_errors
        outputs.append({'market':r.market,'source':receipt,'prompt':compact_ai_context(evidence),
            'renderer':rendered.to_dict(),'NO_SEND':rendered.section})
    for context,cap in results:
        assert v2.consume_result(parent=h['parent'],result=cap,context=context)['scope']==list(v2.SCOPE)
    assert len(h['service'])==2 and len(h['physical'])==4 and len(h['meter'].calls)==4
    target=Path(os.environ['C21U_OUTPUT']);target.mkdir(exist_ok=True)
    (target/'TWO_MARKET_TEST_ONLY.json').write_text(json.dumps(outputs,ensure_ascii=False,indent=2))
    for row in outputs:(target/(row['market']+'-NO_SEND.md')).write_text('SYNTHETIC TEST_ONLY\n'+row['NO_SEND'])

@pytest.mark.parametrize('fault',['ticker','signature','account','service','issuer','missing_pages','duplicate','partial','ohlc','parser','body'])
def test_source_failures_issue_no_result_and_no_retry(monkeypatch,tmp_path,fault):
    h=harness(monkeypatch,tmp_path,fault=fault)
    with pytest.raises((ValueError,httpx.HTTPError)):fetch(h,h['reads'][0])
    assert len(h['service'])==1 and len(h['physical'])==2
    assert v2._PARENTS[h['parent']]['failed']
    assert not any(s['parent'] is h['parent'] for s in v2._RESULTS.values())

@pytest.mark.parametrize('alter',['extra','flow'])
def test_exact_frozen_params_reject_before_send(monkeypatch,tmp_path,alter):
    h=harness(monkeypatch,tmp_path);params=h['reads'][0].params()
    if alter=='extra':params['ignored']='x'
    else:params['include_investor_flows']='false'
    async def run():
        async with httpx.AsyncClient(base_url=h['state'].endpoint,transport=h['client'].transport) as c:
            await h['observer'].get(c,'/ohlcv',params=params)
    with pytest.raises(ValueError,match='native_wire_outside_exact_plan'):asyncio.run(run())
    assert not h['service'] and not h['physical']

@pytest.mark.parametrize('stop',['expired','revoked','registration','process','signature'])
def test_parent_trust_roots_not_receipt_booleans(monkeypatch,tmp_path,stop):
    h=harness(monkeypatch,tmp_path)
    if stop=='expired':h['state'].expires=NOW-timedelta(seconds=1)
    if stop=='revoked':v2.revoke_parent(h['parent'])
    if stop=='registration':h['lease']['active']=False
    if stop=='process':v2._PARENTS[h['parent']]['pid']=-1
    if stop=='signature':v2._PARENTS[h['parent']]['signature']='0'*64
    with pytest.raises(ValueError):fetch(h,h['reads'][0])
    assert not h['service'] and not h['physical']

def test_replay_and_result_tamper_denied(monkeypatch,tmp_path):
    h=harness(monkeypatch,tmp_path);r=h['reads'][0]
    context,cap,_=fetch(h,r)
    context.decision.current_price=999
    with pytest.raises(ValueError,match='context_changed'):v2.consume_result(parent=h['parent'],result=cap,context=context)
    with pytest.raises(ValueError,match='replay'):fetch(h,r)
    assert len(h['service'])==1 and len(h['physical'])==2

def test_physical_exhaustion_invalidates_uncommitted_cohort(monkeypatch,tmp_path):
    h=harness(monkeypatch,tmp_path,('kr','us'),maximum=3)
    context,cap,_=fetch(h,h['reads'][0])
    with pytest.raises(ValueError,match='cohort_not_committed'):v2.consume_result(parent=h['parent'],result=cap,context=context)
    with pytest.raises(ValueError,match='native_physical_budget'):fetch(h,h['reads'][1])
    assert len(h['physical'])==3 and h['meter'].stopped
    with pytest.raises(ValueError):v2.consume_result(parent=h['parent'],result=cap,context=context)

def test_auth_failure_stops_all_later_physical_sends(monkeypatch,tmp_path):
    h=harness(monkeypatch,tmp_path,fault='http403')
    with pytest.raises(httpx.HTTPStatusError):fetch(h,h['reads'][0])
    assert len(h['physical'])==1 and h['meter'].stopped
    async def run():
        async with httpx.AsyncClient(base_url='https://downstream.invalid',transport=h['meter']) as c:await c.post('/chart')
    with pytest.raises(ValueError,match='STOP'):asyncio.run(run())
    assert len(h['physical'])==1

def test_protected_entry_and_live_runtime_fail_closed(monkeypatch,tmp_path):
    h=harness(monkeypatch,tmp_path);h['client'].source_observer=None
    with pytest.raises(ValueError,match='protected_observer'):fetch(h,h['reads'][0])
    with pytest.raises(ValueError,match='signed_service_runtime'):v2.bind_live_runtime(participant=h['receipt'])
    with pytest.raises(ValueError,match='native_runtime_root_required'):v2.issue_parent(runtime=v2.NativeRuntimeRoot(),reads=h['reads'])
    assert not h['service'] and not h['physical']


def test_added_caller_identity_mismatch(monkeypatch,tmp_path):
    h=harness(monkeypatch,tmp_path,fault='caller')
    with pytest.raises(ValueError,match='caller|issuer'):fetch(h,h['reads'][0])
    assert not any(s['parent'] is h['parent'] for s in v2._RESULTS.values())


def test_added_missing_raw_artifact_without_deleting_files(monkeypatch,tmp_path):
    h=harness(monkeypatch,tmp_path)
    original=Path.read_bytes
    def missing(path):
        if path.suffix=='.body' and h['observer'].root in path.parents:raise FileNotFoundError('TEST_ONLY simulated missing artifact')
        return original(path)
    monkeypatch.setattr(Path,'read_bytes',missing)
    with pytest.raises(FileNotFoundError):fetch(h,h['reads'][0])
    assert v2._PARENTS[h['parent']]['failed']
    assert not any(s['parent'] is h['parent'] for s in v2._RESULTS.values())


def test_added_result_receipt_replay_and_generation_reissue_denied(monkeypatch,tmp_path):
    h=harness(monkeypatch,tmp_path);context,cap,receipt=fetch(h,h['reads'][0])
    v2.consume_result(parent=h['parent'],result=cap,context=context)
    with pytest.raises(ValueError,match='replay'):v2.consume_result(parent=h['parent'],result=cap,context=context)
    with pytest.raises(ValueError,match='capability'):v2.consume_result(parent=h['parent'],result=receipt,context=context)
    with pytest.raises(ValueError,match='already_issued'):v2.issue_parent(runtime=h['root'],reads=h['reads'])


def test_final_private_technical_payload_and_public_receipt_not_authority(monkeypatch,tmp_path):
    h=harness(monkeypatch,tmp_path/'receipt');context,cap,receipt=fetch(h,h['reads'][0])
    receipt['scope'].append('OVERALL_DIRECTION')
    accepted=v2.consume_result(parent=h['parent'],result=cap,context=context)
    assert accepted['scope']==list(v2.SCOPE) and 'OVERALL_DIRECTION' not in accepted['scope']
    other=harness(monkeypatch,tmp_path/'private');context,cap,_=fetch(other,other['reads'][0])
    assert context.model_dump(mode='json').get('_technical_context_payload') is None
    context._technical_context_payload['native_view']['periods']['daily']['indicators']['RSI14']=999
    with pytest.raises(ValueError,match='context_changed'):
        v2.consume_result(parent=other['parent'],result=cap,context=context)


@pytest.mark.parametrize('change',['account','budget'])
def test_final_runtime_binding_frozen_and_no_signing_state_exposed(monkeypatch,tmp_path,change):
    h=harness(monkeypatch,tmp_path)
    endpoint=h['observer'].require_read(h['reads'][0])
    assert type(endpoint) is str and endpoint==h['state'].endpoint
    h['receipt']['scope'].append('OVERALL_DIRECTION')
    assert v2._PARENTS[h['parent']]['receipt']['scope']==v2.SCOPE
    if change=='account':h['state'].account_sha256='d'*64
    else:h['state'].physical_max+=1
    with pytest.raises(ValueError,match='runtime_binding_changed'):fetch(h,h['reads'][0])
    assert not h['service'] and not h['physical']
