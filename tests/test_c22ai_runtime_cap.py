"""C22AI changed egress only. Synthetic approvals are never live approvals."""
import asyncio
from datetime import datetime,timedelta,timezone
import json
import multiprocessing
import os
from pathlib import Path
import socket
import sqlite3
import subprocess
import sys

import httpx
import pytest

from app.services import prospective_class_c_owner as approvals
from app.services.selected_run_lifecycle import SelectedRunLedger
from app.services.campaign_runtime_cap import RuntimeCap,MeteredAsyncTransport,MeteredSyncTransport,CampaignOhlcvTransport
from app.services.unified_snapshot_contract import digest


@pytest.fixture(autouse=True)
def no_network_or_database(monkeypatch):
    def deny(*a,**k):raise PermissionError('C22AI_TEST_REAL_IO_FORBIDDEN')
    monkeypatch.setattr(socket.socket,'connect',deny)
    monkeypatch.setattr(socket,'create_connection',deny)
    monkeypatch.setattr(socket,'getaddrinfo',deny)
    monkeypatch.setattr(sqlite3,'connect',deny)


def ledger(tmp_path,maximum=300,providers=None):
    now=datetime.now(timezone.utc)
    approval=approvals.record_backend_approval(approvals.ApprovalDecision(
        event_id='C22AI_SYNTHETIC_NOT_USER_APPROVAL',approved=True,user_message_sha256=digest('TEST_ONLY'),
        effective_at=now-timedelta(seconds=1),expires_at=now+timedelta(hours=1),subjects=('TEST','123456')))
    endpoint=dict(methods=['GET','POST'],host='wire.test',prefix='/',endpoint='SYNTHETIC_WIRE')
    return SelectedRunLedger(path=tmp_path/'shared.jsonl',approval=approval,master_id='C22AI_SYNTHETIC',
        children={'us':dict(generation='TEST_US',subjects=['TEST']),
            'kr':dict(generation='TEST_KR',subjects=['123456'])},provider_caps=providers or {'kiwoom':400},
        max_http=maximum,max_models=14,database_identity={'synthetic':True},onboarding=True,
        runtime_cap={'endpoints':{p:[endpoint] for p in (providers or {'kiwoom':400})}},
        wallclock_seconds_max=3600)


def reserve(cap,n,provider='kiwoom'):
    return cap.reserve(provider=provider,method='POST',host='wire.test',path='/chart',market='us',
        subject='TEST',phase='ONBOARDING',owner='MockWorker',request_sha256=digest(n))


def test_300th_reserved_301st_denied_provider_sum_can_exceed_global(tmp_path):
    journal=ledger(tmp_path)
    cap=RuntimeCap(journal.worker_binding())
    for n in range(300):reserve(cap,n)
    with pytest.raises(ValueError,match='CAP_EXHAUSTED'):
        reserve(cap,300)
    cold=RuntimeCap(journal.worker_binding())
    assert cold.state()['total']==300 and len(cold.state()['pending'])==300
    # Reservation boundary proof only; no 300 real or mocked network sends.
    assert journal.state()['http_total']==300


def test_provider_cap_first_and_no_second_charge_at_logical_boundary(tmp_path):
    journal=ledger(tmp_path,maximum=300,providers={'kiwoom':1,'kis':10})
    cap=RuntimeCap(journal.worker_binding())
    key=reserve(cap,'one')
    cap.dispatched(key);cap.finish(key,status=200)
    with pytest.raises(ValueError,match='CAP_EXHAUSTED'):
        reserve(cap,'two')
    key=reserve(cap,'independent','kis')
    cap.finish(key,status=200)
    assert cap.state()['total']==2 and journal.state()['http']=={'kiwoom':1,'kis':1}


@pytest.mark.parametrize('status',[429,401,503])
def test_provider_errors_no_automatic_retry(tmp_path,status):
    journal=ledger(tmp_path)
    calls=[]
    def send(request):
        calls.append(1)
        return httpx.Response(status)
    async def run():
        transport=MeteredAsyncTransport(binding=journal.worker_binding(),market='us',subject='TEST',
            inner=httpx.MockTransport(send))
        async with httpx.AsyncClient(transport=transport) as client:
            await client.get('https://wire.test/page?number=1')
            with pytest.raises(ValueError,match='CAP_EXHAUSTED'):
                await client.get('https://wire.test/page?number=1')
    asyncio.run(run())
    assert calls==[1] and journal.state()['http_total']==1


def test_pages_redirect_and_refetch_are_distinct_or_refused_not_hidden(tmp_path):
    journal=ledger(tmp_path,maximum=3)
    calls=[]
    def send(request):
        calls.append(str(request.url))
        return httpx.Response(302,headers={'location':'/page?number=2'}) if len(calls)==1 else httpx.Response(200)
    async def run():
        transport=MeteredAsyncTransport(binding=journal.worker_binding(),market='us',subject='TEST',
            inner=httpx.MockTransport(send))
        async with httpx.AsyncClient(transport=transport,follow_redirects=False) as client:
            response=await client.get('https://wire.test/page?number=1')
            assert response.status_code==302 and len(calls)==1
            await client.get('https://wire.test/page?number=2')
            with pytest.raises(ValueError,match='ALREADY_USED'):
                await client.get('https://wire.test/page?number=2')
            await client.post('https://wire.test/page',json={'page':3})
    asyncio.run(run())
    assert len(calls)==journal.state()['http_total']==3


def test_transport_timeout_spent_and_missing_binding_fails_before_send(tmp_path):
    journal=ledger(tmp_path)
    count=[]
    def send(request):
        count.append(1)
        raise httpx.ReadTimeout('TEST_ONLY',request=request)
    transport=MeteredSyncTransport(binding=journal.worker_binding(),market='us',subject='TEST',
        phase='ONBOARDING',inner=httpx.MockTransport(send))
    with pytest.raises(httpx.ReadTimeout):
        transport.handle_request(httpx.Request('POST','https://wire.test/chart'))
    with pytest.raises(ValueError,match='CAP_EXHAUSTED'):
        transport.handle_request(httpx.Request('POST','https://wire.test/chart',json={'different':1}))
    with pytest.raises(ValueError,match='JOURNAL_REQUIRED'):
        RuntimeCap({'path':str(tmp_path/'absent'),'identity_sha256':digest('none')})
    with pytest.raises(ValueError,match='TLS_OR_PORT'):
        transport.handle_request(httpx.Request('GET','http://wire.test/chart'))
    assert count==[1] and journal.state()['http_total']==1


def child_reserve(binding,start,queue):
    cap=RuntimeCap(binding)
    accepted=0
    for n in range(start,start+10):
        try:reserve(cap,n)
        except ValueError:continue
        accepted+=1
    queue.put(accepted)


def test_atomic_multiprocess_counter_no_overdraw(tmp_path):
    journal=ledger(tmp_path,maximum=25)
    binding=journal.worker_binding()
    context=multiprocessing.get_context('fork')
    queue=context.Queue()
    workers=[context.Process(target=child_reserve,args=(binding,i*10,queue)) for i in range(4)]
    for worker in workers:worker.start()
    for worker in workers:
        worker.join(20)
        assert worker.exitcode==0
    assert sum(queue.get(timeout=2) for _ in workers)==25
    assert RuntimeCap(binding).state()['total']==25
    queue.close()


def child_crash(binding):
    reserve(RuntimeCap(binding),'crashed_unresolved')
    os._exit(17)


def test_crash_unknown_intent_is_preserved_not_refunded_or_replayed(tmp_path):
    journal=ledger(tmp_path)
    context=multiprocessing.get_context('fork')
    worker=context.Process(target=child_crash,args=(journal.worker_binding(),))
    worker.start();worker.join(10)
    assert worker.exitcode==17
    cap=RuntimeCap(journal.worker_binding())
    assert cap.state()['total']==1 and len(cap.state()['pending'])==1
    with pytest.raises(ValueError,match='ALREADY_USED'):
        reserve(cap,'crashed_unresolved')


@pytest.mark.parametrize('maximum,expected',[(2,2),(1,1)])
def test_original_external_sender_child_posts_share_journal_and_cap(tmp_path,maximum,expected):
    journal=ledger(tmp_path,maximum=maximum)
    root=Path(__file__).resolve().parents[3]
    script=root/'maintenance/20261111-c22ai-v1/external_mock_probe.py'
    frame=dict(binding=journal.worker_binding(),posts=2)
    result=subprocess.run([sys.executable,'-B',str(script)],input=json.dumps(frame),capture_output=True,
        text=True,timeout=20,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'))
    assert result.returncode==0,result.stderr
    report=json.loads(result.stdout)
    assert report['lower_mock_POST']==report['reserved']==report['lane_entries']==expected
    assert report['lane_stopped'] is False and report['real_HTTP']==0
    assert report['status']==(200 if maximum==2 else 502)
    assert journal.state()['http_total']==expected


def test_internal_ohlcv_get_is_not_charged_and_old_service_rejected(tmp_path):
    journal=ledger(tmp_path)
    methods=[]
    def send(request):
        methods.append(request.method)
        if request.method=='OPTIONS':return httpx.Response(200,json={'campaign_budget_protocol':'selected-run-physical-cap-v1'})
        assert 'X-Campaign-Budget' in request.headers
        return httpx.Response(200,json={})
    async def run():
        transport=CampaignOhlcvTransport(binding=journal.worker_binding(),market='us',subject='TEST',
            inner=httpx.MockTransport(send))
        async with httpx.AsyncClient(transport=transport) as client:
            await client.get('http://127.0.0.1:8765/ohlcv?symbol=TEST')
        old=CampaignOhlcvTransport(binding=journal.worker_binding(),market='us',subject='TEST',
            inner=httpx.MockTransport(lambda r:httpx.Response(200,json={})))
        with pytest.raises(ValueError,match='SERVICE_NOT_PREPARED'):
            await old.handle_async_request(httpx.Request('GET','http://127.0.0.1:8765/ohlcv?symbol=TEST'))
    asyncio.run(run())
    assert methods==['OPTIONS','GET'] and journal.state()['http_total']==0


def test_kis_original_worker_dispatch_metering_not_double_counted(tmp_path,monkeypatch):
    from types import SimpleNamespace
    from app.jobs import production_kis_worker as worker
    from scripts.kr8_kis_integration import dispatch_accounted_kis_request
    journal=ledger(tmp_path,providers={'kis':2})
    journal._event('DB_INTENT')
    receipt={'cutoff':datetime.now(timezone.utc).isoformat(),'SYNTHETIC_NOT_SOURCE':True}
    journal._event('REGISTRATION',selects=1,receipt=receipt,sha256=digest(receipt))
    for market in ('us','kr'):journal._event('PLAN',market=market,sha256=digest(market))
    root=tmp_path/'kis-worker'
    root.mkdir()
    plan={'SYNTHETIC_NOT_SOURCE':True}
    frozen=dict(scope='SELECTED_ORIGINAL_RESEARCH_V1',generation_id='TEST_KR',shared_run_ledger=journal.worker_binding())
    (root/'production-frozen-source-plan.json').write_text(json.dumps(frozen))
    (root/'kis-plan.json').write_text(json.dumps(plan))
    (root/'acquisition-outcome.json').write_text('{}')
    monkeypatch.setattr(worker,'_source_plan',lambda f:SimpleNamespace(kis_plan_sha256=digest(plan),
        plan_sha256=digest('kr'),subjects=('123456',)))
    monkeypatch.setattr(worker,'current_inventories',lambda *a:{'SYNTHETIC_NOT_INVENTORY':True})
    def acquire(*args,**kwargs):
        kwargs['guard']()
        child=kwargs['physical_accounting']
        def send(request):
            assert child.state()['http_total']==1
            return httpx.Response(200,json={})
        dispatch_accounted_kis_request(httpx.Request('GET','https://wire.test/estimate?symbol=123456'),send,
            accounting=child,source_plan_sha256=digest('kr'),logical_id='kis-wire:1')
        return 'SYNTHETIC_MOCK_ONLY_NOT_REAL_KIS'
    monkeypatch.setattr(worker.kis,'acquire',acquire)
    frame=dict(contract='production-kis-worker-authorization-v1',root=str(root),
        frozen_sha256=__import__('hashlib').sha256((root/'production-frozen-source-plan.json').read_bytes()).hexdigest(),
        plan_sha256=digest(plan),seconds_remaining=10,credentials=dict(app_key='SYNTHETIC',app_secret='SYNTHETIC'))
    context=multiprocessing.get_context('fork')
    queue=context.Queue()
    def run():queue.put(worker.run(frame))
    process=context.Process(target=run)
    process.start();process.join(10)
    assert process.exitcode==0 and queue.get(timeout=1)=='SYNTHETIC_MOCK_ONLY_NOT_REAL_KIS'
    queue.close()
    assert journal.state()['http_total']==1
    with pytest.raises(ValueError,match='ACCOUNTING_REQUIRED'):
        dispatch_accounted_kis_request(httpx.Request('GET','https://wire.test/estimate'),lambda r:None,
            accounting=None,source_plan_sha256=digest('kr'),logical_id='missing')


def test_four_onboarding_plus_ten_monitoring_model_intents_15_denied(tmp_path):
    journal=ledger(tmp_path)
    for market,ticker in (('us','TEST'),('kr','123456')):
        for stage in ('CORE','DECISION'):
            key=journal.before_onboarding_model(market=market,ticker=ticker,stage=stage,payload_sha256=digest(stage))
            journal.onboarding_model_result(key,ok=True,output_sha256=digest('TEST_ONLY'))
    journal._event('DB_INTENT')
    receipt={'cutoff':datetime.now(timezone.utc).isoformat(),'SYNTHETIC_NOT_OWNER':True}
    journal._event('REGISTRATION',selects=1,receipt=receipt,sha256=digest(receipt))
    for market in ('us','kr'):journal._event('PLAN',market=market,sha256=digest(market))
    for market in ('us','kr'):
        journal._event('CAPTURE',market=market)
        journal._event('SOURCE',market=market,sha256=digest('TEST_ONLY_NOT_SOURCE'))
    for market in ('us','kr'):
        journal._event('MODEL_PLAN',market=market,sha256=digest('models:'+market),slots=5,
            slot_ids=[market+str(i) for i in range(5)])
    for market in ('us','kr'):
        for i in range(5):
            key='MODEL:'+market+str(i)
            journal._event('INTENT',key=key,kind='MODEL',market=market,slot=market+str(i),plan=digest('models:'+market))
            journal.result(key,ok=True)
    with pytest.raises(ValueError,match='scope_or_budget'):
        journal._event('INTENT',key='MODEL:15',kind='MODEL',market='us',slot='us0',plan=digest('models:us'))
    assert journal.state()['model_total']==14 and journal.state()['http_total']==0


def test_native_source_glue_forwards_same_ledger_to_dispatcher_and_kis(tmp_path,monkeypatch):
    """Wiring-only mocks, explicitly not original Source/registration acceptance."""
    import time
    from types import SimpleNamespace
    from app.services import production_source_transport as source
    from app.services import selected_source_dispatch,selected_source_plan
    journal=ledger(tmp_path)
    root=tmp_path/'source'
    root.mkdir()
    (root/'production-frozen-source-plan.json').write_text('{}')
    (root/'acquisition-outcome.json').write_text('{"phases":{}}')
    observed=[]
    fake_plan=SimpleNamespace(plan_sha256=digest('SYNTHETIC_PLAN'))
    monkeypatch.setattr(selected_source_plan,'compile_selected_plan',lambda **k:{'plan':fake_plan})
    monkeypatch.setattr(selected_source_plan,'request_budget',lambda *a:{'providers':{'kiwoom':1}})
    class Dispatcher:
        def __init__(self,**kwargs):
            assert kwargs['run_ledger'] is journal
            observed.append('original-selected-dispatcher-port')
    async def capture(**kwargs):
        assert isinstance(kwargs['dispatcher'],Dispatcher)
        observed.append('original-acquire-all-port')
    async def kis_worker(**kwargs):
        assert kwargs['run_ledger'] is journal
        observed.append('original-kis-worker-port')
    monkeypatch.setattr(selected_source_dispatch,'SelectedSourceDispatcher',Dispatcher)
    monkeypatch.setattr(source,'acquire_all',capture)
    transport=source.NativeProductionSourceTransport(SimpleNamespace(),http_transport_factory=lambda:httpx.MockTransport(lambda r:httpx.Response(200)),
        kis_worker=kis_worker,run_ledger=journal,registration_owner=object(),source_policy=object())
    asyncio.run(transport.collect(root=root,frozen={'scope':'SELECTED_ORIGINAL_RESEARCH_V1','plan':{},
        'config_identities':{},'generation_id':'TEST_KR'},compiler={},kis_plan={'SYNTHETIC':True},
        credentials={},deadline=time.monotonic()+10))
    assert observed==['original-selected-dispatcher-port','original-acquire-all-port','original-kis-worker-port']
    assert journal.state()['http_total']==journal.state()['model_total']==0


def test_original_auth_reused_across_cohort_GETs_without_second_physical_attempt(tmp_path):
    journal=ledger(tmp_path,maximum=1)
    root=Path(__file__).resolve().parents[3]
    frame=dict(binding=journal.worker_binding(),posts=0,auth_reuse=True)
    result=subprocess.run([sys.executable,'-B',str(root/'maintenance/20261111-c22ai-v1/external_mock_probe.py')],
        input=json.dumps(frame),capture_output=True,text=True,timeout=20)
    assert result.returncode==0,result.stderr
    value=json.loads(result.stdout)
    assert value['status']==200 and value['lower_mock_POST']==value['reserved']==1
    assert value['lane_entries']==1 and value['lane_stopped'] is False
    assert journal.state()['http_total']==1
