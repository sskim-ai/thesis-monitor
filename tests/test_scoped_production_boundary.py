"""Production-shaped synthetic chain; no live registration, keys or HTTP."""
import asyncio
from copy import deepcopy
from datetime import date, timedelta
import hashlib
import json
import os
from pathlib import Path
import time

import httpx
import pytest

from tests.test_current_class_c_source_bridge import case as registration_case, CONFIG
from tests.test_manual_scoped_source_runtime import POLICY
from app.services import current_class_c_source_bridge as registration
from app.services import current_scoped_source_owner as owners
from app.services import current_scoped_source_results as results
from app.services import kiwoom_global_lane as lane_module
from app.services import manual_scoped_source_runtime as manual
from app.services.current_scoped_source_dispatch import CurrentScopedDispatcher
from app.services.current_scoped_worker_bridge import ScopedBridge
from app.services.scoped_worker_launch import CUSTODY_POLICY, DUMMY, prepare
from app.services.sealed_source_transport import SealedSourceTransport
from app.services.scoped_external_code_manifest import CONTRACT_V2
from app.services.unified_snapshot_contract import encoded


@pytest.fixture
def chain(registration_case, tmp_path, monkeypatch):
    # Pinned code-only inputs are prepared by the task harness before this run.
    inputs = json.loads(Path(os.environ['P2K_CODE_INPUTS']).read_bytes())
    for name, pin in inputs['files'].items():
        raw=Path(name).read_bytes()
        assert dict(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())==pin
    root=tmp_path/'lane';root.mkdir(mode=0o700)
    activation=dict(protocol=lane_module.PROTOCOL,generation='P2K_SYNTHETIC',boot_identity='test-boot',
        implementation_sha256=hashlib.sha256(Path(lane_module.__file__).read_bytes()).hexdigest())
    state=dict(protocol=lane_module.PROTOCOL,generation='P2K_SYNTHETIC',boot_identity='test-boot',
        last_end=None,in_flight=False,halted=False,sequence=0,pid=0)
    for name,value in [('activation.json',activation),('state.json',state)]:
        (root/name).write_bytes(encoded(value));(root/name).chmod(0o600)
    (root/'lane.lock').touch(mode=0o600)
    lane=lane_module.GlobalKiwoomLane(root,boot=lambda:'test-boot',lock_timeout=.2)
    monkeypatch.setattr(lane_module,'DEFAULT_ROOT',tmp_path/'unused-host-root')
    monkeypatch.setattr(lane_module,'_loaded_lane',None)
    monkeypatch.delenv('KIWOOM_GLOBAL_LANE_REQUIRED',raising=False)
    # Only the isolated test lane is substituted; the original participant
    # constructor and loaded-code identity checks are executed, not mocked.
    monkeypatch.setattr(lane_module,'configured_lane',lambda:lane)
    monkeypatch.setattr(lane_module,'boot_identity',lambda:'test-boot')
    from app.services.kiwoom_participant_session import ParticipatingSession
    from app.services import current_scoped_worker_bridge, current_scoped_source_dispatch
    from app.services import scoped_worker_launch, sealed_source_transport
    session=ParticipatingSession(modules=(current_scoped_worker_bridge,current_scoped_source_dispatch,
        scoped_worker_launch,sealed_source_transport),caller_kind='CLI')
    c=registration_case
    issued={m:owners.registration.issue_prospective_owner(approval=c['approval'],
        capture=c['kwargs']['capture'],market=m,source_generation_id='SYNTHETIC_REGISTRATION',
        generation_id='P2K_TEST_ONLY',policy=POLICY)[0] for m in ('kr','us')}
    kwargs=deepcopy({k:v for k,v in c['kwargs'].items() if k not in {'capture','owners','policy'}})
    kwargs.update(capture=c['kwargs']['capture'],owners=issued,policy=POLICY)
    kwargs['stock_metadata'].update(run_id='P2K_TEST_ONLY',
        owner_files={n:v['sha256'] for n,v in inputs['external_pins'].items()})
    kwargs['counts']={m:dict(adjusted_daily=1000,adjusted_weekly=700,adjusted_monthly=300,
        unadjusted_weekly_valuation=300) for m in ('kr','us')}
    reg,stock,frozen=registration.prepare_current_bridge(**kwargs,enabled=True)
    handle=manual.prepare(class_c_bridge=reg,frozen=frozen,stock_plan=stock,policy=POLICY,
        maximum_attempts=20,provider_config_sha256=CONFIG,enabled=True)
    parent,wire,scoped_stock=manual.inputs(handle)
    plan=wire['request_plan']
    run=CurrentScopedDispatcher(parent=parent,plan=plan,root=tmp_path/'dispatch',
        owners={d.normalizer:d.owner_sha256 for d in plan.descriptors},
        config_identities={'kiwoom':CONFIG},credential_presence={'kiwoom':True},
        secrets=tuple(DUMMY.values()),account_pacer=lane)
    output=tmp_path/'worker';output.mkdir(mode=0o700)
    envelope=dict(stage=str(manual.ROOT),output=str(output),external_root=inputs['external_root'],
        external_pins=inputs['external_pins'],external_code_contract=CONTRACT_V2,
        stock_plan=scoped_stock,request_interval=1.5,latest_completed_us_session=frozen['sessions']['us'],
        us_market_symbols=[],read_paths=list(inputs['files']))
    path=tmp_path/'frozen.json';path.write_bytes(encoded(envelope))
    calls=[];fault={}
    async def respond(request):
        calls.append(dict(api=request.headers.get('api-id','credential_exchange'),at=time.monotonic()))
        if fault.get('kind')=='timeout':raise httpx.ReadTimeout('synthetic',request=request)
        if fault.get('kind')=='cancel':raise asyncio.CancelledError()
        if fault.get('kind') in ('403','429'):
            return httpx.Response(int(fault['kind']),json={'return_code':9})
        if request.url.path=='/oauth2/token':
            return httpx.Response(200,json=dict(return_code=0,token='TEST_ONLY_DUMMY_TOKEN',expires_dt='20990101000000'))
        body=json.loads(request.content)
        read=next(r for r in wire['stock_reads'] if r.subject==body['stk_cd'])
        day=date.fromisoformat(read.latest_completed_session)
        rows=[]
        while len(rows)<1000:
            if day.weekday()<5:
                rows.append(dict(dt=day.strftime('%Y%m%d'),open_pric='100',high_pric='110',
                    low_pric='90',cur_prc='105',trde_qty='1000'))
            day-=timedelta(days=1)
        return httpx.Response(200,json=dict(return_code=0,
            **{('output' if read.market=='kr' else 'result_list'):rows}),headers={'cont-yn':'N','next-key':''})
    inner=httpx.MockTransport(respond)
    worker=ScopedBridge(parent=parent,original_plan=plan,
        transport=SealedSourceTransport(run,inner,providers={'kiwoom'}),
        worker=manual.ROOT/'scripts/current_scoped_source_worker.py',frozen=path,
        sha=hashlib.sha256(path.read_bytes()).hexdigest(),output=output,credentials=dict(DUMMY),market_reads=(),
        source_session=session,custody_policy=CUSTODY_POLICY)
    manual.bind_runtime(handle,dispatcher=run,worker_bridge=worker)
    return dict(handle=handle,parent=parent,wire=wire,run=run,worker=worker,lane=lane,calls=calls,root=tmp_path,fault=fault)


def test_real_scoped_bridge_to_original_consumer(chain, monkeypatch):
    c=chain;w=c['worker']
    async def flow():
        try:
            captured=await manual.command(c['handle'],{'stocks':True})
            assert captured['status']=='CAPTURE_COMPLETE_NOT_QUALIFIED'
            for n in (1,2):
                replay=await manual.command(c['handle'],{'replay':n})
                assert all(r['status']=='PASS' for r in replay['rows'])
            for r in c['wire']['stock_reads']:
                projection=await manual.command(c['handle'],{'projection':r.entry_id})
                assert projection['status']=='COMPLETED_PROJECTION_REPLAY_PASS',projection
        finally:await w.shutdown()
    asyncio.run(flow())
    assert w.process.returncode==0
    state=json.loads((c['lane'].root/'state.json').read_bytes())
    assert state['sequence']==3 and not state['halted'] and not state['in_flight']
    assert c['run'].physical_attempts==len(c['calls'])==3
    physical=[json.loads(p.read_bytes()) for p in sorted((c['run'].root/'physical').glob('attempt-*.json'))
        if not p.name.endswith('.start.json')]
    assert [r['account_pacing']['sequence'] for r in physical]==[1,2,3]
    assert all(r['account_pacing']['pid']==os.getpid() for r in physical)
    assert all(r['account_pacing']['started_monotonic']-r['account_pacing']['previous_end']>=1.5
        for r in physical[1:])
    consumed=[]
    for r in c['wire']['stock_reads']:
        cap=results.issue_source_result(c['parent'],dispatcher=c['run'],entry_id=r.entry_id)
        consumed_value=results.read_source_rows(c['parent'],cap,dispatcher=c['run'],entry_id=r.entry_id)
        rows,receipt=consumed_value['rows'],consumed_value['receipt']
        assert len(rows)==1000 and receipt['native_use'] is False and receipt['model_use'] is False
        with pytest.raises(ValueError):results.read_source_rows(c['parent'],cap,dispatcher=c['run'],entry_id=r.entry_id,consumer='NATIVE')
        with monkeypatch.context() as m:
            pid=os.getpid();m.setattr(results.os,'getpid',lambda:pid+1)
            with pytest.raises(ValueError):results.consume_source_result(c['parent'],cap,dispatcher=c['run'],entry_id=r.entry_id)
        consumed.append(receipt)
    (c['root']/'E2E.json').write_bytes(encoded(dict(test_only=True,original_consumer=consumed,
        physical_mock_requests=physical,worker_pid=w.process.pid,source_live_authority=False)))
    (c['root']/'COLD_INPUT.json').write_bytes(encoded(dict(test_only=True,
        capture=str(c['run'].root),plan=c['run'].plan.model_dump(mode='json'),
        receipts={k:v['receipt_sha256'] for k,v in c['run'].results.items()})))
    # Original bytes still gate a previously issued capability.
    source=w.output/'projection-002.json'
    original=source.read_bytes()
    changed=original+b' '
    (c['root']/'REJECTED_PROJECTION.json').write_bytes(changed)
    source.write_bytes(changed)
    try:
        with pytest.raises(ValueError):results.consume_source_result(c['parent'],cap,dispatcher=c['run'],entry_id=r.entry_id)
    finally:source.write_bytes(original)
    (c['root']/'NEGATIVES.json').write_bytes(encoded(dict(wrong_consumer='DENIED',
        changed_parent_pid='DENIED',changed_projection='DENIED',
        original_sha256=hashlib.sha256(original).hexdigest(),rejected_sha256=hashlib.sha256(changed).hexdigest())))


@pytest.mark.parametrize('kind',['credentials','transport','pacer','closure','session','policy'])
def test_no_live_or_unbound_launch(chain,kind):
    w=chain['worker']
    if kind=='credentials':w.credentials={'app_key':'NON_DUMMY','secret_key':'NOT_A_SECRET'}
    elif kind=='transport':w.transport.inner=httpx.AsyncBaseTransport()
    elif kind=='pacer':chain['run']._account_pacer=None
    elif kind=='session':w.source_session=None
    elif kind=='policy':w.custody_policy='caller-created-policy'
    else:
        body=json.loads(w.frozen.read_bytes());body['read_paths'].append('/not-read/private.env')
        w.frozen.write_bytes(encoded(body));w.sha=hashlib.sha256(w.frozen.read_bytes()).hexdigest()
    with pytest.raises(ValueError):prepare(w)
    assert w.process is None and not chain['calls']


@pytest.mark.parametrize('kind',['403','429','timeout','cancel'])
def test_original_parent_slot_failure_latches(chain,kind):
    c=chain;w=c['worker']
    c['fault']['kind']=kind
    async def flow():
        try:
            with pytest.raises(BaseException):await manual.command(c['handle'],{'stocks':True})
        finally:await w.shutdown()
    asyncio.run(flow())
    state=json.loads((c['lane'].root/'state.json').read_bytes())
    assert state['halted'] and not state['in_flight'] and state['sequence']==1
    assert c['run'].physical_attempts==len(c['calls'])==1
    assert w.process.returncode is not None
    with pytest.raises(ValueError):results.issue_source_result(c['parent'],dispatcher=c['run'],entry_id=c['wire']['stock_reads'][0].entry_id)
    assert not (w.output/'process-end.json').read_text().find('NORMAL_END')>=0


def test_budget_and_duplicate_dispatch_are_not_replenished(chain,tmp_path):
    c=chain;run=c['run'];plan=c['wire']['request_plan']
    with pytest.raises(ValueError,match='already_claimed'):
        CurrentScopedDispatcher(parent=c['parent'],plan=plan,root=tmp_path/'duplicate',
            owners={d.normalizer:d.owner_sha256 for d in plan.descriptors},config_identities={'kiwoom':CONFIG},
            credential_presence={'kiwoom':True},account_pacer=c['lane'])
    run.maximum_attempts+=1
    with pytest.raises(BaseException,match='budget_changed'):run._require_parent()
    assert not c['calls']


def test_closed_original_participant_denies_before_worker(chain):
    c=chain;w=c['worker']
    w.source_session.close_admission()
    with pytest.raises(BaseException):asyncio.run(manual.command(c['handle'],{'stocks':True}))
    assert w.process is None and not c['calls']
    assert w._closed and w._failure


def test_actual_fork_cannot_inherit_parent_or_duplicate_global_slot(chain):
    c=chain
    readfd,writefd=os.pipe()
    with c['lane'].sync_slot():
        pid=os.fork()
        if pid==0:
            os.close(readfd)
            outcome={}
            try:
                try:c['run']._require_parent()
                except ValueError:outcome['inherited_parent']='DENIED'
                try:
                    other=lane_module.GlobalKiwoomLane(c['lane'].root,boot=lambda:'test-boot',lock_timeout=.1)
                    with other.sync_slot():outcome['duplicate_slot']='UNEXPECTED'
                except lane_module.GlobalLaneStop:outcome['duplicate_slot']='DENIED'
                os.write(writefd,encoded(outcome))
            finally:os._exit(0)
        os.close(writefd)
        raw=os.read(readfd,4096);os.close(readfd)
        _,status=os.waitpid(pid,0)
        assert status==0
        assert json.loads(raw)==dict(inherited_parent='DENIED',duplicate_slot='DENIED')
    state=json.loads((c['lane'].root/'state.json').read_bytes())
    assert state['sequence']==1 and not state['halted'] and not state['in_flight']
    assert not c['calls']
