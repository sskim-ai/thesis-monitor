"""TEST_ONLY Parent/Worker/source boundaries. No official data or real keys."""
import asyncio
from datetime import datetime,timezone,timedelta
import json
from pathlib import Path
import pytest
from app.services import registered_valuation_source_intent as intent
from app.services import registered_valuation_source_parent as parent
from app.services import prospective_class_c_owner as registration,pending_source_parent as pending
from app.services.kis_estimate_source_contract import build_source_plan,EstimateSourceProbe
from scripts import kr8_kis_integration as kis
from test_c10r_identity_parent import prepare
from test_minimal_class_c_export import POLICY


def setup(tmp_path,monkeypatch):
    args=prepare(tmp_path,monkeypatch)
    original=registration._DISCOVERY[args['discovery_owner']]
    h,_=intent.issue_intent(approval=original['approval'],capture=original['capture'],
        generation_id='VALUATION_INTENT',policy=POLICY,enabled=True)
    return h,dict(intent=h,intent_generation='VALUATION_INTENT',subjects=('999999',),
        listing_rows=[dict(code='999999',marketCode='0')],session=args['session'],
        generation_id='VALUATION_SOURCE',cutoff=datetime.now(timezone.utc),
        code_sha='a'*40,provider_config_sha256='b'*64,enabled=True)


def test_distinct_default_off_and_legacy_scope_unchanged(tmp_path,monkeypatch):
    from app.services.registered_identity_source_parent import PURPOSE
    assert PURPOSE=='REGISTERED_IDENTITY_DISCOVERY_ONLY_V1' and PURPOSE!=intent.PURPOSE
    h,args=setup(tmp_path,monkeypatch)
    with pytest.raises(ValueError):parent.issue_parent(**dict(args,enabled=False))
    p,wire=parent.issue_parent(**args);r=pending.resolve_parent(p)
    assert r['scope']==intent.PURPOSE and r['maximum_attempts']==19 and len(wire['request_plan'].descriptors)==7
    assert not any(r[k] for k in ('source_use','financial_use','valuation','model_use','ACTIVE','send'))
    with pytest.raises(ValueError,match='already_claimed'):parent.issue_parent(**args)


@pytest.mark.parametrize('kind',['forged','wrong_generation','expired','pid','code_pin'])
def test_intent_rejects_invalid_capability(tmp_path,monkeypatch,kind):
    h,args=setup(tmp_path,monkeypatch);s=intent._LIVE[h]
    generation='VALUATION_INTENT'
    if kind=='forged':h={}
    if kind=='wrong_generation':generation='OTHER'
    if kind=='expired':s['expires']=datetime.now(timezone.utc)-timedelta(seconds=1)
    if kind=='pid':s['pid']=-1
    if kind=='code_pin':s['pins']={}
    with pytest.raises((ValueError,TypeError)):
        intent.require_intent(h,generation_id=generation,provider='kiwoom',subjects=('999999',))


def test_routing_ambiguity_and_conflict_not_guessed():
    from app.services.provider_native_valuation_acquisition import routing_markets
    with pytest.raises(ValueError,match='authority_missing'):
        routing_markets({'X':dict(country='KR',exchange='KRX')},listing_rows=[])
    with pytest.raises(ValueError,match='routing_conflict'):
        routing_markets({'X':dict(country='KR',exchange='KOSPI')},listing_rows=[dict(code='X',marketCode='10')])


@pytest.mark.parametrize('command',[{'stock':'X'},{'market_replay':1},{'market_wire':{'logical_id':'OTHER'}}])
def test_valuation_worker_rejects_non_frozen_command(command):
    with pytest.raises(PermissionError):parent.validate_worker_command({'reads':[]},{},command)


def test_account_lock_is_exclusive_and_not_cross_pid(tmp_path):
    lock=intent.ProviderAccountLock('finnhub','TEST_ONLY',root=tmp_path/'locks')
    try:
        with pytest.raises(BlockingIOError):intent.ProviderAccountLock('finnhub','TEST_ONLY',root=tmp_path/'locks')
        lock.pid=-1
        with pytest.raises(ValueError):lock.require()
    finally:lock.close()


def test_kis_source_9_17_is_not_full_plan_or_price_authority(tmp_path):
    from scripts.kis_estimate_capability_probe import Credentials,ProbeStop
    securities={t:dict(ticker=t,country='KR',exchange='KRX',currency='KRW',
        canonical_security_id='TEST:'+t,corp_code='TEST_ONLY') for t in kis.SUBJECTS}
    at=datetime.now(timezone.utc).isoformat()
    p=build_source_plan(generation_id='TEST_ONLY',as_of=at,securities=securities)
    assert p['stage1_max']==9 and p['total_physical_max']==17 and not p['qualified_FY1']
    full=kis.build_plan(generation='TEST_ONLY',as_of=at,securities=securities,static_hashes={})
    assert full['auth_max']+full['estimate_max']+full['identity_max']==17>9
    probe=EstimateSourceProbe(tmp_path,Credentials('DUMMY_KEY','DUMMY_SECRET'),None,plan=p,enabled=True)
    with pytest.raises(ProbeStop,match='PRICE_ACTION_OR_FY1_DENIED'):probe.fetch(kis.SUBJECTS[0],'price')
    with pytest.raises(ProbeStop,match='STAGE_INCOMPLETE'):probe.fetch(kis.SUBJECTS[0],'identity')


def test_valuation_original_worker_with_dummy_key(tmp_path,monkeypatch):
    import httpx
    from app.services import market_component_execution as execution
    from app.services.market_worker_rpc import MarketWorkerRPC
    from app.providers.kiwoom_rest_client import KiwoomRestClient
    from app.services.scoped_worker_launch import DUMMY
    h,args=setup(tmp_path,monkeypatch);p,wire=parent.issue_parent(**args)
    calls=[]
    def response(request):
        calls.append(request.headers.get('api-id') or 'auth')
        if request.url.path=='/oauth2/token':
            return httpx.Response(200,json=dict(return_code=0,token='TEST_ONLY_TOKEN',expires_dt='20991231235959'))
        if request.headers['api-id']=='ka10099':
            data=dict(return_code=0,list=[dict(code='999999',name='SYNTHETIC',marketCode='0',marketName='KOSPI')])
        else:data=dict(return_code=0,stk_cd='999999',stk_nm='SYNTHETIC',per='12',pbr='2')
        return httpx.Response(200,json=data,headers={'cont-yn':'N','next-key':''})
    run,transport,worker,windows=execution.prepare_capture(parent=p,wire=wire,session=args['session'],
        base=tmp_path/'worker',credentials=dict(DUMMY),inner=httpx.MockTransport(response),
        external_root='/Users/sskim/Codex/ohlcv-analyst',valuation_only=True)
    async def work():
        client=KiwoomRestClient(**DUMMY,max_retries=0,request_interval_seconds=0,transport=MarketWorkerRPC(worker))
        try:
            await client.request(endpoint='/api/dostk/stkinfo',api_id='ka10099',body={'mrkt_tp':'0'})
            await client.request(endpoint='/api/dostk/stkinfo',api_id='ka10001',body={'stk_cd':'999999'})
        finally:await worker.shutdown();await transport.shutdown()
    asyncio.run(work())
    assert windows is None and run.physical_attempts==3 and worker.process.returncode==0
    assert calls==['auth','ka10099','ka10001']
