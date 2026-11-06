"""TEST_ONLY lane and capture; no real key, network or operation change."""
from datetime import datetime,timezone
import asyncio
import hashlib
import os
from pathlib import Path

import pytest

from app.services import registered_identity_source_parent as identity_parent
from app.services import prospective_class_c_owner as owner,pending_source_parent as pending
from app.services import kiwoom_global_lane as lane
from app.services import current_scoped_source_dispatch as dispatch,current_scoped_worker_bridge as bridge
from app.services import scoped_worker_launch as launch,sealed_source_transport as transport
from app.services.kiwoom_participant_session import ParticipatingSession
from test_c10r_identity_discovery import discovery_capture
from test_minimal_class_c_export import POLICY


def prepare(tmp_path,monkeypatch):
    directory=tmp_path/'SYNTHETIC_LANE';directory.mkdir(mode=0o700)
    monkeypatch.setattr(lane,'boot_identity',lambda:'SYNTHETIC_C10R_BOOT')
    lane._atomic(directory/'activation.json',dict(protocol=lane.PROTOCOL,generation='C10R_SYNTHETIC',
        boot_identity=lane.boot_identity(),implementation_sha256=hashlib.sha256(Path(lane.__file__).read_bytes()).hexdigest()))
    lane._atomic(directory/'state.json',dict(protocol=lane.PROTOCOL,generation='C10R_SYNTHETIC',
        boot_identity=lane.boot_identity(),last_end=None,in_flight=False,halted=False,sequence=0,pid=os.getpid()))
    fd=os.open(directory/'lane.lock',os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600);os.close(fd)
    monkeypatch.setenv('KIWOOM_GLOBAL_LANE_REQUIRED','1')
    monkeypatch.setattr(lane,'_loaded_lane',lane.GlobalKiwoomLane(directory,boot=lane.boot_identity))
    session=ParticipatingSession(modules=(dispatch,bridge,launch,transport),caller_kind='CLI')
    approval,capture,_,_=discovery_capture(tmp_path,ticker='999999',market='kr')
    h,_=owner.issue_identity_discovery_owner(approval=approval,capture=capture,generation_id='SYNTHETIC',policy=POLICY)
    return dict(discovery_owner=h,discovery_generation='SYNTHETIC',subjects=('999999',),
        session=session,generation_id='SYNTHETIC_IDENTITY',cutoff=datetime.now(timezone.utc),
        code_sha='a'*40,provider_config_sha256='b'*64,enabled=True)


def test_identity_parent_is_finite_read_only_and_one_use(tmp_path,monkeypatch):
    args=prepare(tmp_path,monkeypatch)
    parent,wire=identity_parent.issue_parent(**args)
    receipt=pending.resolve_parent(parent,plan=wire['request_plan'])
    assert receipt['scope']==identity_parent.PURPOSE
    assert receipt['planned_attempts']==12 and receipt['maximum_attempts']==20
    assert not any(receipt[k] for k in ('source_use','financial_use','valuation','model_use','ACTIVE','send'))
    assert {d.endpoint_operation for d in wire['request_plan'].descriptors}=={'credential_exchange','ka10099','ka10001'}
    assert all(d.transient_retry_max==0 for d in wire['request_plan'].descriptors)
    with pytest.raises(ValueError,match='one_dispatch_only'):identity_parent.issue_parent(**args)
    owner.revoke_identity_discovery(args['discovery_owner'])
    with pytest.raises(ValueError):pending.resolve_parent(parent,plan=wire['request_plan'])


@pytest.mark.parametrize('change',['default_off','forged','wrong_generation','outside_subject'])
def test_identity_parent_requires_original_registered_discovery(tmp_path,monkeypatch,change):
    args=prepare(tmp_path,monkeypatch)
    if change=='default_off':args['enabled']=False
    if change=='forged':args['discovery_owner']={}
    if change=='wrong_generation':args['discovery_generation']='WRONG'
    if change=='outside_subject':args['subjects']=('000000',)
    with pytest.raises((ValueError,TypeError)):identity_parent.issue_parent(**args)


def test_unselected_chain_persists_original_no_io_decision():
    from types import SimpleNamespace
    from app.services.market_component_execution import drain_selected_market_slots
    from app.services.sealed_response_binding import SlotNotSelected
    class Run:
        used={'kr_market:page1'}
        plan=SimpleNamespace(descriptors=[SimpleNamespace(logical_request_id='kr_market:page'+str(n)) for n in (1,2,3)])
        def resolve(self,key):
            if key.endswith('3'):assert 'kr_market:page2' in self.used
            raise SlotNotSelected('SYNTHETIC_N_CONTINUATION')
        def skip_unselected(self,key):self.used.add(key)
    run=Run()
    asyncio.run(drain_selected_market_slots(None,run))
    assert run.used=={'kr_market:page1','kr_market:page2','kr_market:page3'}


def test_identity_only_original_private_worker_with_dummy_key(tmp_path,monkeypatch):
    import httpx
    from app.services import market_component_execution as execution
    from app.services.market_worker_rpc import MarketWorkerRPC
    from app.providers.kiwoom_rest_client import KiwoomRestClient
    from app.services.scoped_worker_launch import DUMMY
    args=prepare(tmp_path,monkeypatch)
    parent,wire=identity_parent.issue_parent(**args)
    calls=[]
    def response(request):
        calls.append(request.headers.get('api-id') or 'auth')
        if request.url.path=='/oauth2/token':
            return httpx.Response(200,json=dict(return_code=0,token='TEST_ONLY_TOKEN',expires_dt='20991231235959'))
        if request.headers['api-id']=='ka10099':
            body=dict(return_code=0,list=[dict(code='999999',name='SYNTHETIC',marketCode='0',marketName='KOSPI')])
        else:body=dict(return_code=0,stk_cd='999999',stk_nm='SYNTHETIC')
        return httpx.Response(200,json=body,headers={'cont-yn':'N','next-key':''})
    run,transport,worker,windows=execution.prepare_capture(parent=parent,wire=wire,
        session=args['session'],base=tmp_path/'identity-worker',credentials=dict(DUMMY),
        inner=httpx.MockTransport(response),external_root='/Users/sskim/Codex/ohlcv-analyst',identity_only=True)
    async def action():
        client=KiwoomRestClient(**DUMMY,max_retries=0,request_interval_seconds=0,
            transport=MarketWorkerRPC(worker))
        try:
            first=await client.request(endpoint='/api/dostk/stkinfo',api_id='ka10099',body={'mrkt_tp':'0'})
            second=await client.request(endpoint='/api/dostk/stkinfo',api_id='ka10001',body={'stk_cd':'999999'})
            assert first.payload['list'][0]['code']==second.payload['stk_cd']
        finally:
            await worker.shutdown();await transport.shutdown()
    asyncio.run(action())
    assert windows is None and run.physical_attempts==3
    assert calls==['auth','ka10099','ka10001'] and worker.process.returncode==0
    assert not pending.resolve_parent(parent)['source_use']


def test_campaign_scope_is_bounded_and_does_not_change_legacy_scope(tmp_path,monkeypatch):
    from datetime import timedelta
    from app.services import pending_source_intake as intake
    args=prepare(tmp_path,monkeypatch)
    approval=owner._DISCOVERY[args['discovery_owner']]['approval']
    now=datetime.now(timezone.utc)
    kw=dict(approval=approval,session=args['session'],generation_id='CAMPAIGN',source_generation_id='CAMPAIGN',
        campaign_plan_sha256='c'*64,maximum_physical_attempts=20,expires_at=now+timedelta(minutes=20),enabled=True)
    for change in ({'maximum_physical_attempts':21},{'expires_at':now+timedelta(minutes=46)}, {'enabled':False}):
        with pytest.raises(ValueError):intake.record_backend_campaign_scope(**dict(kw,**change))
    handle=intake.record_backend_campaign_scope(**kw)
    state,_=intake._scope(handle)
    assert state['policy']=='FINITE_MANUAL_SOURCE_CAMPAIGN_V2'
    assert state['expires']==kw['expires_at'] and state['maximum_physical_attempts']==20
    with pytest.raises(ValueError):intake.record_backend_campaign_scope(**kw)


def test_stock_worker_only_executes_its_frozen_completed_close(tmp_path,monkeypatch):
    import json
    import httpx
    from test_c9_intake_bridge import prepared,scoped_wire
    from tests.test_p3g_pending_worker import local_read_closure
    from app.services.scoped_external_code_manifest import REQUIRED_V2,CONTRACT_V2
    from app.services.scoped_worker_launch import DUMMY
    from app.services.unified_snapshot_contract import encoded
    args=prepare(tmp_path,monkeypatch)
    sub=tmp_path/'us-case';sub.mkdir()
    _,_,_,adapted,_=prepared(sub)
    config,_,_,at=scoped_wire()
    config=config.model_copy(update={'capture_selection':config.capture_selection.model_copy(update={'us_completed_closes':True})})
    parent,wire=pending.issue_parent(intake_owner=adapted,config=config,session=args['session'],
        generation_id='C8_TEST',cutoff=at,code_sha='a'*40,provider_config_sha256='b'*64,maximum_attempts=4,enabled=True)
    from app.services.scoped_source_plan import _sessions
    pair=next(p for p in _sessions(at)[1] if p.market=='us')
    calls=[]
    def response(request):
        api=request.headers.get('api-id');calls.append(api or 'auth')
        if not api:return httpx.Response(200,json=dict(return_code=0,token='TEST_ONLY_TOKEN',expires_dt='20991231235959'))
        data=dict(return_code=0,result_list=[dict(dt=d.strftime('%Y%m%d'),open_pric='10',high_pric='12',low_pric='9',cur_prc='11',trde_qty='100') for d in (pair.target,pair.prior)])
        return httpx.Response(200,json=data,headers={'cont-yn':'N','next-key':''})
    from app.services import market_component_execution as execution
    # Reuse its audited closure builder without creating a second authority.
    root=Path(__file__).resolve().parents[1];external=Path('/Users/sskim/Codex/ohlcv-analyst')
    plan=wire['request_plan'];out=sub/'worker';out.mkdir(mode=0o700)
    run=dispatch.CurrentScopedDispatcher(parent=parent,plan=plan,root=sub/'dispatch',
        owners={d.normalizer:d.owner_sha256 for d in plan.descriptors},config_identities={'kiwoom':'b'*64},
        credential_presence={'kiwoom':True},secrets=tuple(DUMMY.values()),account_pacer=args['session']._lane)
    sealed=transport.SealedSourceTransport(run,httpx.MockTransport(response),providers={'kiwoom'})
    pins={n:dict(bytes=(external/n).stat().st_size,sha256=hashlib.sha256((external/n).read_bytes()).hexdigest()) for n in REQUIRED_V2}
    stock=dict(contract='current-scoped-stock-capture-v1',run_id='C8_TEST',acquisition_id='SYNTHETIC_CLOSE',
        frozen_at=at.isoformat(),reads=[r.model_dump(mode='json') for r in wire['stock_reads']],owner_files=json.loads(wire['owner_files_json']))
    frozen=sub/'frozen.json'
    envelope=dict(stage=str(root),output=str(out),external_root=str(external),external_pins=pins,external_code_contract=CONTRACT_V2,
        stock_plan=stock,request_interval=1.5,latest_completed_us_session=str(pair.target),us_market_symbols=[],
        read_paths=local_read_closure()+[str(external/n) for n in sorted(pins)],pending_handoff=pending.public_handoff(parent),
        market_wire_templates={d.logical_request_id:d.model_dump(mode='json') for d in plan.descriptors if d.endpoint_operation=='usa20590'})
    frozen.write_bytes(encoded(envelope))
    worker=bridge.ScopedBridge(parent=parent,original_plan=plan,transport=sealed,worker=root/'scripts/current_scoped_source_worker.py',
        frozen=frozen,sha=hashlib.sha256(frozen.read_bytes()).hexdigest(),output=out,credentials=dict(DUMMY),market_reads=[],
        source_session=args['session'],custody_policy=launch.CUSTODY_POLICY)
    async def action():
        try:
            await worker.command({'stocks':True})
            key='completed_close:NEWUS';request,_,_=run.resolve(key)
            value=await worker.command({'market_wire':dict(logical_id=key,request_json=request)})
            assert value['status']==200
        finally:await worker.shutdown();await sealed.shutdown()
    asyncio.run(action())
    assert calls==['auth','usa06012','usa20590'] and run.physical_attempts==3
