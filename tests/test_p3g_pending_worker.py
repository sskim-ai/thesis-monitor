"""P3G synthetic capabilities and original isolated Worker; no Provider network."""
import ast,asyncio,hashlib,json,os,subprocess,sys
from copy import deepcopy
from datetime import datetime,timedelta,timezone
from pathlib import Path

import httpx
import pytest
from sqlmodel import Session

from tests.test_p3f_source_intake import pending
from app.services import pending_source_intake as intake,pending_source_parent as adapter
from app.services import kiwoom_global_lane as lane
from app.services import current_scoped_source_dispatch as dispatch,current_scoped_worker_bridge as bridge_module
from app.services import scoped_worker_launch as launch,sealed_source_transport as sealed
from app.services.kiwoom_participant_session import ParticipatingSession
from app.services.scoped_source_plan import ScopedConfig,ScopedSubject,HistoryCounts,ScopedCaptureSelectionV2
from app.services.minimal_class_c_export import capture_authorized_class_c,captured_private_snapshot,MODELS
from app.services.unified_snapshot_contract import digest,encoded

ROOT=Path(__file__).resolve().parents[1]


@pytest.fixture
def prepared(pending,tmp_path,monkeypatch):
    args,approval,engine,permission=pending
    with Session(engine) as session:
        item=session.get(MODELS['securitymaster'],1);item.cik='00000123';session.add(item);session.commit()
    cap=capture_authorized_class_c(permission);raw,_=captured_private_snapshot(cap)
    owner,receipt=intake.issue_intake(**dict(args,capture=cap,expected_capture_sha256=digest(json.loads(raw))))
    directory=tmp_path/'isolated-test-lane';directory.mkdir(mode=0o700)
    boot=lane.boot_identity()
    activation=dict(protocol=lane.PROTOCOL,generation='SYNTHETIC_P3G',boot_identity=boot,
        implementation_sha256=hashlib.sha256(Path(lane.__file__).read_bytes()).hexdigest())
    lane._atomic(directory/'activation.json',activation)
    lane._atomic(directory/'state.json',dict(protocol=lane.PROTOCOL,generation='SYNTHETIC_P3G',boot_identity=boot,
        last_end=None,in_flight=False,halted=False,sequence=0,pid=os.getpid()))
    fd=os.open(directory/'lane.lock',os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600);os.close(fd)
    selected_lane=lane.GlobalKiwoomLane(directory)
    monkeypatch.setenv('KIWOOM_GLOBAL_LANE_REQUIRED','1');monkeypatch.setattr(lane,'_loaded_lane',selected_lane)
    modules=(dispatch,bridge_module,launch,sealed)
    session=ParticipatingSession(modules=modules,caller_kind='CLI')
    counts=HistoryCounts(**{r:2 for r in ('adjusted_daily','adjusted_weekly','adjusted_monthly','unadjusted_weekly_valuation')})
    subject=ScopedSubject(ticker='FUTURE',market='us',security_id='security-future',issuer_id='00000123',venue='NASDAQ',currency='USD')
    config=ScopedConfig(subjects=(subject,),kr_history=counts,us_history=counts,kr_max_pages=2,
        capture_selection=ScopedCaptureSelectionV2(contract='scoped-capture-selection-v2',stock_security_ids=(subject.security_id,),
            stock_roles=('adjusted_daily',),market_contexts=(),us_completed_closes=False))
    kw=dict(intake_owner=owner,config=config,session=session,generation_id='SYNTHETIC',
        cutoff=datetime.now(timezone.utc),code_sha='a'*40,provider_config_sha256='b'*64,maximum_attempts=3,enabled=True)
    return kw,owner,tmp_path


def test_pending_parent_typed_one_use_and_unchanged_active_owner(prepared):
    args,owner,_=prepared
    parent,wire=adapter.issue_parent(**args)
    assert intake.require_live_worker_adapter(owner,parent=parent)['scope']==adapter.PURPOSE
    with pytest.raises(ValueError,match='one_dispatch'):adapter.issue_parent(**args)
    with pytest.raises(ValueError):adapter.resolve_parent(adapter.public_handoff(parent))
    from app.services import current_scoped_source_owner as active
    with pytest.raises(ValueError):active.resolve_parent(parent)
    fake=wire['request_plan'].model_copy(update={'generation_id':'OLD'})
    with pytest.raises(ValueError):adapter.resolve_parent(parent,plan=fake)
    adapter.revoke_parent(parent)
    with pytest.raises(ValueError):adapter.resolve_parent(parent)


@pytest.mark.parametrize('mutation',['market','role','code','session','PID'])
def test_pending_parent_mutation_denial(prepared,mutation,monkeypatch):
    args,_,_=prepared
    if mutation=='role':
        args=dict(args,config=args['config'].model_copy(update={'capture_selection':None}))
        with pytest.raises(ValueError):adapter.issue_parent(**args)
        return
    parent,wire=adapter.issue_parent(**args)
    if mutation=='code':monkeypatch.setattr(adapter,'pins',lambda:{'changed':'x'})
    elif mutation=='PID':monkeypatch.setattr(adapter.os,'getpid',lambda:-1)
    elif mutation=='session':
        from app.services import prospective_class_c_owner as clocks
        original=clocks.completed_clock
        monkeypatch.setattr(clocks,'completed_clock',lambda m,at:dict(original(m,at),target='2000-01-01'))
    else:
        state=adapter._LIVE[parent]
        state['wire']['stock_reads']=(state['wire']['stock_reads'][0].model_copy(update={'market':'kr'}),)
        # Exact role identity/session is checked against the original intake market.
        state['wire']['stock_reads'][0].__dict__['latest_completed_session']='2000-01-01'
    with pytest.raises(ValueError):adapter.resolve_parent(parent,plan=wire['request_plan'])


def local_read_closure():
    todo=['scripts/current_scoped_source_worker.py'];seen=set()
    while todo:
        name=todo.pop()
        if name in seen:continue
        path=ROOT/name;seen.add(name);parts=Path(name).parts
        for depth in range(1,len(parts)):
            init='/'.join(parts[:depth])+'/__init__.py'
            if (ROOT/init).is_file() and init not in seen:todo.append(init)
        for node in ast.walk(ast.parse(path.read_bytes())):
            if isinstance(node,ast.Import):names=[a.name for a in node.names]
            elif isinstance(node,ast.ImportFrom) and node.module:
                module=node.module if not node.level else '.'.join(parts[:-node.level])+'.'+node.module
                names=[module]+[module+'.'+a.name for a in node.names]
            else:continue
            for module in names:
                if module.startswith(('app.','scripts.')):
                    for candidate in (module.replace('.','/')+'.py',module.replace('.','/')+'/__init__.py'):
                        if (ROOT/candidate).is_file() and candidate not in seen:todo.append(candidate)
    return [str(ROOT/n) for n in sorted(seen)]


def test_original_isolated_worker_pending_capture_and_independent_cold(prepared):
    from app.services import current_scoped_source_results as results
    from app.services.scoped_external_code_manifest import REQUIRED_V2,CONTRACT_V2
    from app.services.registered_source_batch import Batch
    from app.services.prospective_class_c_owner import completed_clock
    args,_,tmp=prepared
    parent,wire=adapter.issue_parent(**args)
    plan=wire['request_plan'];read=wire['stock_reads'][0]
    rows=[dict(dt=day.replace('-',''),open_pric='10',high_pric='12',low_pric='9',cur_prc='11',trde_qty='100')
        for day in (read.latest_completed_session,str(next(s.prior for s in wire['sessions'] if s.market=='us')))]
    def respond(request):
        if request.url.path=='/oauth2/token':
            return httpx.Response(200,json=dict(return_code=0,token='TEST_ONLY_TOKEN',expires_dt='20991231235959',token_type='Bearer'))
        return httpx.Response(200,json=dict(return_code=0,result_list=rows),headers={'cont-yn':'N','next-key':''})
    owners={d.normalizer:d.owner_sha256 for d in plan.descriptors}
    run=dispatch.CurrentScopedDispatcher(parent=parent,plan=plan,root=tmp/'capture',owners=owners,
        config_identities={'kiwoom':'b'*64},credential_presence={'kiwoom':True},
        secrets=(*launch.DUMMY.values(),'TEST_ONLY_TOKEN'),account_pacer=args['session']._lane)
    transport=sealed.SealedSourceTransport(run,httpx.MockTransport(respond),providers={'kiwoom'})
    output=tmp/'worker';output.mkdir(mode=0o700)
    external=Path('/Users/sskim/Codex/ohlcv-analyst')
    pins={}
    for n in REQUIRED_V2:
        path=external/n
        assert path.is_file() and not path.is_symlink()
        raw=path.read_bytes();pins[n]=dict(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
    stock=dict(contract='current-scoped-stock-capture-v1',run_id='SYNTHETIC',acquisition_id='SYNTHETIC-STOCK',
        frozen_at=plan.frozen_at.isoformat(),reads=[r.model_dump(mode='json') for r in wire['stock_reads']],
        owner_files=json.loads(wire['owner_files_json']))
    envelope=dict(stage=str(ROOT),output=str(output),external_root=str(external),external_pins=pins,
        external_code_contract=CONTRACT_V2,stock_plan=stock,request_interval=1.5,
        latest_completed_us_session=read.latest_completed_session,us_market_symbols=[],
        read_paths=local_read_closure()+[str(external/n) for n in sorted(pins)],pending_handoff=adapter.public_handoff(parent))
    frozen=tmp/'frozen.json';frozen.write_bytes(encoded(envelope))
    bridge=bridge_module.ScopedBridge(parent=parent,original_plan=plan,transport=transport,
        worker=ROOT/'scripts/current_scoped_source_worker.py',frozen=frozen,
        sha=hashlib.sha256(frozen.read_bytes()).hexdigest(),output=output,credentials=dict(launch.DUMMY),
        market_reads=[],source_session=args['session'],custody_policy=launch.CUSTODY_POLICY)
    results.bind_capture(parent,wire,stock,run,run.root,output,bridge)
    async def go():
        try:
            assert (await bridge.command({'stocks':True}))['status']=='CAPTURE_COMPLETE_NOT_QUALIFIED'
            for number in (1,2):assert (await bridge.command({'replay':number}))['status']=='REPLAY_RESULT'
            assert (await bridge.command({'projection':read.entry_id}))['status']=='COMPLETED_PROJECTION_REPLAY_PASS'
        finally:await bridge.shutdown();await transport.shutdown()
    asyncio.run(go())
    cap=results.issue_source_result(parent,dispatcher=run,entry_id=read.entry_id)
    value=results.read_source_rows(parent,cap,dispatcher=run,entry_id=read.entry_id)
    receipt=value['receipt']
    assert receipt['source_evidence_state']=='SOURCE_OBSERVED_PENDING' and receipt['native_use'] is False
    assert run.physical_attempts==2 and bridge._pending_ack
    assert json.loads((output/'effective-settings.json').read_bytes())['os_policy_denials']['network-outbound']
    raw=encoded(value['rows']);session_dates={m:completed_clock(m,datetime.now(timezone.utc))['target'] for m in ('kr','us')}
    batch=Batch('P3G_SYNTHETIC',('security-future',),('adjusted_daily',),tuple(sorted(session_dates.items())),
        (datetime.now(timezone.utc)+timedelta(minutes=5)).isoformat(),3)
    data=dict(contract='registered-source-batch-cold-v1',batch=batch.public(),batch_id=batch.batch_id,
        batch_sha256=digest(batch.public()),plan=run.plan.model_dump(mode='json'),receipts=[receipt],
        expected_reads=[read.model_dump(mode='json')],artifacts=[dict(entry_id=read.entry_id,sha256=hashlib.sha256(raw).hexdigest())])
    consumer="""import sys,json,base64
from app.services.registered_source_batch import validate_cold_roles
x=json.load(sys.stdin);raw=base64.b64decode(x['raw']);out=validate_cold_roles(x['data'],lambda a:(raw,json.loads(raw)))
print(json.dumps(out))
"""
    import base64
    payload=dict(data=data,raw=base64.b64encode(raw).decode())
    for tampered in (False,True):
        source=deepcopy(payload)
        if tampered:source['data']['receipts'][0]['native_use']=True
        r=subprocess.run([sys.executable,'-B','-c',consumer],input=json.dumps(source),capture_output=True,text=True,
            timeout=30,env={**os.environ,'THESIS_MONITOR_ENV_FILE':''},cwd=ROOT)
        assert (r.returncode==0) is (not tampered)
    record=os.environ.get('P3G_ACTUAL_WORKER_RECEIPT')
    if record:
        Path(record).write_bytes(encoded(dict(status='ORIGINAL_WORKER_SYNTHETIC_PASS',worker_pid=bridge.process.pid,
            kernel_isolation=True,physical_mock_attempts=run.physical_attempts,external_code_files=len(pins),
            child_read_closure=len(envelope['read_paths']),Cold_positive=True,Cold_tamper_denied=True,
            financial_HTTP=0,source_scope=receipt['source_evidence_state'],real_Source=False)))
