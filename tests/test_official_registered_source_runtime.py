"""New original-registration edge. Synthetic DB and mocked OS decisions only."""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import importlib.util
import json
import os
from pathlib import Path
import sqlite3

import pytest

from app.services import official_registered_source_runtime as r
from app.services import manual_scoped_source_runtime as manual
from app.services import prospective_class_c_owner as owner
from app.services.unified_snapshot_contract import digest
from tests.test_minimal_class_c_export import database

spec=importlib.util.spec_from_file_location('official_registration_cli_test',r.ROOT/'scripts/official_scoped_source_parent.py')
cli=importlib.util.module_from_spec(spec);spec.loader.exec_module(cli)


@pytest.fixture
def case(tmp_path,monkeypatch):
    from app.services import kiwoom_global_lane as lane
    monkeypatch.setattr(lane,'DEFAULT_ROOT',tmp_path/'NO_REAL_LANE')
    monkeypatch.setattr(lane,'_loaded_lane',None)
    monkeypatch.delenv('KIWOOM_GLOBAL_LANE_REQUIRED',raising=False)
    permission=database(tmp_path,[(t,m) for m,ts in r.UNIVERSE.items() for t in ts])
    with sqlite3.connect(permission.database) as db:
        for n,(t,m) in enumerate([(t,m) for m,ts in r.UNIVERSE.items() for t in ts],1):
            db.execute('UPDATE securitymaster SET cik=?,corp_code=?,company_name=? WHERE ticker=?',
                (str(n) if m=='us' else None,str(n).zfill(8) if m=='kr' else None,f'Synthetic issuer {n}',t))
        db.execute("UPDATE securitymaster SET identity_provider='opendart' WHERE country='KR'")
    monkeypatch.setattr(r,'_os_decisions',lambda p:{(str(p)+suffix,op):True
        for suffix in ('','-wal','-shm','-journal') for op in r.WRITE_OPERATIONS})
    boundary=r.admit_os_boundary(permission.database)
    now=datetime.now(timezone.utc)
    decision=owner.ApprovalDecision(event_id='SYNTHETIC_NEW_EDGE_ONLY',user_message_sha256='a'*64,
        approved=True,effective_at=now,expires_at=now+timedelta(minutes=50),subjects=r.registered_subjects())
    approval=owner.record_backend_approval(decision)
    config=digest({'public':'SYNTHETIC_CONFIG_ONLY'})
    metadata=dict(run_id='synthetic-original-registration-edge',acquisition_id='synthetic-chart',
        instruction_sha='1'*40,implementation_sha='2'*40,
        owner_files={f'app/synthetic_{i}.py':'3'*64 for i in range(25)},owner_head='synthetic-not-git',
        settings_sha256=config,request_environment_sha256=config)
    return dict(approval=approval,boundary=boundary,database=permission.database,metadata=metadata,
        counts={m:dict(adjusted_daily=1000,adjusted_weekly=700,adjusted_monthly=300,
            unadjusted_weekly_valuation=300) for m in ('kr','us')},
        config_identities={p:config for p in ('kiwoom','sec_edgar','opendart','fred','eia','ecos',
            'krx_night_futures','google_news_rss','naver_news')})


def test_real_original_exporter_to_original_manual_plan_same_memory(case):
    counters={'registration_session_attempts':0}
    with r.capture_registered_runtime(**case,counters=counters) as (handle,public):
        parent,wire,stock=manual.inputs(handle)
        assert len(wire['stock_reads'])==2 and len(stock['reads'])==2
        assert {x.market for x in wire['stock_reads']}=={'kr','us'}
        assert all(x.count==1000 and x.role=='adjusted_daily' for x in wire['stock_reads'])
        assert public['registration']['SELECT']==5 and public['registration']['sessions']==1
        assert counters==dict(registration_session_attempts=1,registration_sessions_completed=1,SELECT=5)
        assert not public['private_rows_exported'] and not public['financial_or_economic_authority']
        text=json.dumps(public)
        assert 'core_thesis' not in text and 'selected private' not in text
        assert public['source_plan']['parent']['planned_attempts']==20
    with pytest.raises(ValueError):manual.inputs(handle)
    with pytest.raises(ValueError):owner._approval(case['approval'])


@pytest.mark.parametrize('kind',['json','unissued','wrong_process','wrong_database','lost_os','expired','revoked','extra_six'])
def test_new_edge_rejects_before_read(case,monkeypatch,kind,tmp_path):
    args=dict(case);reads=[]
    monkeypatch.setattr(r,'capture_authorized_class_c',lambda p:reads.append(p))
    if kind=='json':args['boundary']={'os_readonly':True}
    elif kind=='unissued':args['boundary']=r.EffectiveRegistrationBoundary()
    elif kind=='wrong_process':r._BOUNDARIES[case['boundary']]['pid']=-1
    elif kind=='wrong_database':args['database']=tmp_path/'unread_other.sqlite3'
    elif kind=='lost_os':monkeypatch.setattr(r,'_os_decisions',lambda p:{'write':False})
    elif kind=='expired':monkeypatch.setattr(owner,'_now',lambda:datetime.now(timezone.utc)+timedelta(hours=2))
    elif kind=='revoked':owner.revoke_approval(case['approval'])
    else:
        d=owner._approval(case['approval']).model_copy(update={'subjects':(*r.registered_subjects(),'META')})
        args['approval']=owner.record_backend_approval(d)
    with pytest.raises((ValueError,FileNotFoundError)): 
        with r.capture_registered_runtime(**args):pytest.fail('MUST_NOT_ISSUE')
    assert reads==[]


@pytest.mark.parametrize('op',r.WRITE_OPERATIONS)
def test_each_missing_os_write_denial_blocks(case,monkeypatch,op):
    monkeypatch.setattr(r,'_os_decisions',lambda p:{name:name!=op for name in r.WRITE_OPERATIONS})
    with pytest.raises(ValueError,match='effective_os_db_write_denial'):
        r.admit_os_boundary(case['database'])


def test_original_query_boundary_blocks_sql_write(case):
    from app.services.minimal_class_c_export import QueryBoundary
    boundary=QueryBoundary()
    assert boundary(sqlite3.SQLITE_UPDATE,'watchlistitem','active','main',None)==sqlite3.SQLITE_DENY
    assert boundary(sqlite3.SQLITE_READ,'other_private_table','body','main',None)==sqlite3.SQLITE_DENY
    assert len(boundary.denied)==2


def test_os_error_and_unconfined_host_do_not_issue(case,monkeypatch):
    monkeypatch.setattr(r,'_os_decisions',lambda p:{'kernel_write':False})
    with pytest.raises(ValueError):r.admit_os_boundary(case['database'])
    assert not hasattr(r.EffectiveRegistrationBoundary(),'approved')


def test_wrong_calendar_and_source_generation_do_not_reissue(case,monkeypatch):
    original=r.registration.prepare_current_bridge
    def changed(**kw):
        h,stock,frozen=original(**kw)
        frozen['sessions']['us']='1900-01-01'
        return h,stock,frozen
    monkeypatch.setattr(r.registration,'prepare_current_bridge',changed)
    with pytest.raises(ValueError,match='frozen_contract'):
        with r.capture_registered_runtime(**case):pytest.fail('BAD_SESSION')
    with pytest.raises(ValueError):owner._approval(case['approval'])


def test_revoke_on_downstream_failure(case):
    with pytest.raises(RuntimeError):
        with r.capture_registered_runtime(**case) as (handle,_):raise RuntimeError('TEST_ONLY')
    with pytest.raises(ValueError):manual.inputs(handle)
    assert case['boundary'] not in r._BOUNDARIES


def test_missing_current_config_before_any_grant():
    m=json.loads((r.ROOT/'ops/manual-source-parent.json').read_bytes())
    with pytest.raises(cli.AdmissionDenied,match='configuration_and_grant'):
        cli.require_canary_installation(m,'CURRENT_TEST_INVOCATION')


def test_original_os_interface_unavailable_before_database(monkeypatch):
    monkeypatch.setattr(r.sys,'platform','unsupported')
    with pytest.raises(ValueError,match='os_boundary_unavailable'):
        r.admit_os_boundary('/private/tmp/NEVER_OPEN.sqlite3')


def test_insufficient_space_never_lowers_us_guard(tmp_path,monkeypatch):
    from types import SimpleNamespace
    monkeypatch.setattr(r.os,'statvfs',lambda p:SimpleNamespace(f_bavail=11*1024**3,f_frsize=1))
    with pytest.raises(ValueError,match='writer_headroom'):r.check_space([tmp_path])


def test_canary_code_has_no_unconditional_previous_hard_stop():
    import inspect
    assert 'official_current_db_os_boundary_not_qualified' not in inspect.getsource(cli.require_canary_installation)
    assert 'capture_registered_runtime' in inspect.getsource(cli.run_canary)
    assert 'cold_readback' in inspect.getsource(cli.run_canary)


def test_missing_cold_authority_before_child():
    import asyncio
    with pytest.raises(cli.AdmissionDenied,match='cold_original_source'):
        asyncio.run(cli.cold_readback({},None,dict(status='UNISSUED',receipts=[]),Path('/not-written')))


@pytest.mark.parametrize('kind',['missing','denied','stale','code_changed','intent_changed'])
def test_current_owner_receipt_gate_before_any_live_input(tmp_path,kind):
    from types import SimpleNamespace
    m=json.loads((r.ROOT/'ops/manual-source-parent.json').read_bytes())
    m['owner_receipts_root']=str(tmp_path)
    now=datetime.now(timezone.utc)
    receipt=dict(status='READONLY_PARENT_ADMITTED_WORKER_AND_CANARY_PENDING',owner_approved=True,
        parent_closed=True,financial_calls=0,database_sessions=0,manifest_sha256='a'*64,
        invocation_id='SYNTHETIC_PREFLIGHT',reviewed_source_pins_sha256=cli.digest(cli.encoded(m['source_pins'])),
        reviewed_interpreter_pin=m['interpreter_pin'],owner_intent=dict(uid=os.getuid(),at=now.isoformat(),
            operation='preflight',manifest_sha256='a'*64,invocation_id='SYNTHETIC_PREFLIGHT'))
    if kind=='denied':receipt['status']='BLOCKED_OFFICIAL_PARENT'
    if kind=='stale':receipt['owner_intent']['at']=(now-timedelta(hours=2)).isoformat()
    if kind=='code_changed':receipt['reviewed_source_pins_sha256']='0'*64
    if kind=='intent_changed':receipt['owner_intent']['operation']='canary'
    path=tmp_path/'owner.json'
    path.write_bytes(cli.encoded(receipt));p=cli.pin(path)
    if kind=='missing':path.unlink()
    config={'owner_preflight':dict(path=str(path),pin=p,manifest_sha256='a'*64)}
    with pytest.raises((cli.AdmissionDenied,FileNotFoundError)):
        cli.require_owner_preflight(m,config,'b'*64)


@pytest.mark.parametrize('kind',['missing_pin','source_drift','manifest_hash','os_flag_only'])
def test_current_installation_identity_cannot_be_self_approved(monkeypatch,kind):
    path=r.ROOT/'ops/manual-source-parent.json';raw=path.read_bytes();m=json.loads(raw)
    monkeypatch.setattr(cli.sys,'executable',m['interpreter'])
    if kind=='os_flag_only':
        m['canary_installation']['os_readonly_approved']=True
        with pytest.raises(cli.AdmissionDenied):cli.require_canary_installation(m,'SYNTHETIC_INVOCATION')
        return
    if kind=='manifest_hash':
        with pytest.raises(cli.AdmissionDenied):cli.validate_manifest(path,'0'*64)
        return
    if kind=='missing_pin':del m['source_pins']['scripts/official_scoped_source_parent.py']
    else:m['source_pins']['app/services/official_registered_source_runtime.py']['sha256']='0'*64
    raw=cli.encoded(m);original=Path.read_bytes
    monkeypatch.setattr(Path,'read_bytes',lambda p:raw if p==path else original(p))
    with pytest.raises(cli.AdmissionDenied):cli.validate_manifest(path,cli.digest(raw))


@pytest.fixture
def local_lane(tmp_path,monkeypatch):
    from app.services import kiwoom_global_lane as lane
    from app.services.unified_snapshot_contract import encoded
    root=tmp_path/'lane';root.mkdir(mode=0o700)
    activation=dict(protocol=lane.PROTOCOL,generation='NEW_EDGE_TEST_ONLY',boot_identity='synthetic-boot',
        implementation_sha256=cli.digest(Path(lane.__file__).read_bytes()))
    state=dict(protocol=lane.PROTOCOL,generation='NEW_EDGE_TEST_ONLY',boot_identity='synthetic-boot',
        last_end=None,in_flight=False,halted=False,sequence=0,pid=0)
    for name,value in [('activation.json',activation),('state.json',state)]:
        (root/name).write_bytes(encoded(value));(root/name).chmod(0o600)
    (root/'lane.lock').touch(mode=0o600)
    active=lane.GlobalKiwoomLane(root,boot=lambda:'synthetic-boot')
    monkeypatch.setattr(lane,'DEFAULT_ROOT',root)
    monkeypatch.setattr(lane,'_loaded_lane',active)
    monkeypatch.setattr(lane,'boot_identity',lambda:'synthetic-boot')
    monkeypatch.setenv('KIWOOM_GLOBAL_LANE_REQUIRED','1')
    monkeypatch.setenv('KIWOOM_MAINTENANCE_STARTUP','0')
    m=json.loads((r.ROOT/'ops/manual-source-parent.json').read_bytes())
    m.update(lane_root=str(root),activation_digest=digest(activation),lock_identity=list(active.lock_identity))
    return lane,active,m,state


@pytest.mark.parametrize('kind',['optin','stop','inflight','lock_identity'])
def test_official_parent_uses_original_lane_denials(local_lane,monkeypatch,kind):
    lane,active,m,state=local_lane
    if kind=='optin':monkeypatch.delenv('KIWOOM_GLOBAL_LANE_REQUIRED')
    elif kind=='lock_identity':m['lock_identity']=[0,0]
    else:
        state['halted' if kind=='stop' else 'in_flight']=True
        (active.root/'state.json').write_bytes(cli.encoded(state))
    before=(active.root/'state.json').read_bytes()
    with pytest.raises((ValueError,RuntimeError)):cli.admit_parent(m)
    assert (active.root/'state.json').read_bytes()==before


def test_original_lane_duplicate_attempt_not_reset(case,local_lane,tmp_path):
    import asyncio
    import httpx
    from app.services.current_scoped_source_dispatch import CurrentScopedDispatcher
    from app.services.sealed_source_transport import CapturedFragment
    from app.services.unified_live_source_transport import SourceSafetyStop
    lane,active,_,_=local_lane
    with r.capture_registered_runtime(**case) as (handle,_):
        parent,wire,_=manual.inputs(handle);plan=wire['request_plan']
        run=CurrentScopedDispatcher(parent=parent,plan=plan,root=tmp_path/'dispatch',
            owners={d.normalizer:d.owner_sha256 for d in plan.descriptors},
            config_identities={'kiwoom':case['config_identities']['kiwoom']},credential_presence={'kiwoom':True},
            account_pacer=active)
        d=next(d for d in plan.descriptors if d.consumer_role.startswith('stock:') and d.page_ordinal==1)
        q=json.loads(d.request_json);calls=[]
        async def flow():
            transport=httpx.MockTransport(lambda req:(calls.append(req) or httpx.Response(200,json={'return_code':0})))
            request=httpx.Request(q['method'],q['url'],headers=q['headers'],content=q['body'].encode())
            await run.execute(d.logical_request_id,request,transport=transport,normalize=CapturedFragment(d))
            with pytest.raises(SourceSafetyStop,match='repeated_request'):
                await run.execute(d.logical_request_id,request,transport=transport,normalize=CapturedFragment(d))
        asyncio.run(flow())
        assert len(calls)==run.physical_attempts==1
        state=json.loads((active.root/'state.json').read_bytes())
        # Original halt() takes a non-HTTP stop slot; it must not be counted
        # as a second physical request or reset to hide the safety stop.
        assert state['sequence']==2 and state['halted'] and not state['in_flight']


def test_child_eof_closes_composition_and_revokes(case,monkeypatch):
    import asyncio
    from types import SimpleNamespace
    from app.services.unified_live_source_transport import SourceSafetyStop
    closed=[]
    async def eof(*args,**kwargs):raise SourceSafetyStop('scoped_worker_eof')
    async def shutdown():closed.append(True)
    monkeypatch.setattr(manual,'bind_runtime',lambda *a,**k:None)
    monkeypatch.setattr(manual,'command',eof)
    with r.capture_registered_runtime(**case) as (handle,_):
        with pytest.raises(SourceSafetyStop,match='eof'):
            asyncio.run(cli.consume_original_runtime(handle=handle,dispatcher=SimpleNamespace(maximum_attempts=20),
                worker_bridge=SimpleNamespace(shutdown=shutdown)))
        with pytest.raises(ValueError):manual.inputs(handle)
    assert closed==[True]


@pytest.mark.parametrize('mutation',['none','rows','receipt','generation','native','loader'])
def test_new_cold_process_reuses_sealed_p2k_bytes_without_worker_reboot(tmp_path,mutation):
    import asyncio
    import zipfile
    archive=r.ROOT.parent.parent/'maintenance/20261103-p2k-onepass/TM_P2K_ONEPASS_20261103_RESULT.zip'
    assert cli.digest(archive.read_bytes())=='8c3531c2b6b524f6a1c9016ff461390bc8d61fddce527bd9c1dc6153c35d90db'
    prefix='synthetic-final/test_real_scoped_bridge_to_ori0/'
    with zipfile.ZipFile(archive) as z:
        manifest=json.loads(z.read('manifest.json'))['members']
        def sealed(name):
            b=z.read(name);assert dict(bytes=len(b),sha256=cli.digest(b))==manifest[name];return b
        old=json.loads(sealed(prefix+'COLD_INPUT.json'))
        e2e=json.loads(sealed(prefix+'E2E.json'))
        capture=tmp_path/'capture';capture.mkdir()
        for name in manifest:
            if name.startswith(prefix+'dispatch/'):
                relative=Path(name[len(prefix+'dispatch/'):]);assert '..' not in relative.parts
                dest=capture/relative;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(sealed(name))
        artifacts=[]
        for i,receipt in enumerate(e2e['original_consumer'],1):
            rows=json.loads(sealed(prefix+f'worker/projection-{i:03d}.json'))['rows']
            path=capture/f'rows-{i}.json';path.write_bytes(cli.encoded(rows))
            artifacts.append(dict(entry_id=receipt['entry_id'],path=path.name,sha256=cli.digest(path.read_bytes())))
    m=json.loads((r.ROOT/'ops/manual-source-parent.json').read_bytes())
    request=dict(contract='official-issued-source-cold-v1',capture=str(capture),plan=old['plan'],
        receipts=old['receipts'],already_issued_source_receipts=e2e['original_consumer'],
        row_artifacts=artifacts,source_pins=m['source_pins'])
    if mutation=='rows':(capture/'rows-1.json').write_bytes(b'[]')
    elif mutation=='receipt':request['receipts'][next(iter(request['receipts']))]='0'*64
    elif mutation=='generation':request['plan']['generation_id']='WRONG'
    elif mutation=='native':request['already_issued_source_receipts'][0]['native_use']=True
    elif mutation=='loader':request['source_pins']['scripts/official_scoped_source_parent.py']['sha256']='0'*64
    path=tmp_path/'cold-input.json';path.write_bytes(cli.encoded(request))
    async def run():
        proc=await asyncio.create_subprocess_exec(m['interpreter'],'-I','-B',str(r.ROOT/'scripts/official_source_cold.py'),
            str(path),cli.digest(path.read_bytes()),stdout=asyncio.subprocess.PIPE,stderr=asyncio.subprocess.PIPE,
            env={'PATH':'/usr/bin:/bin','LC_ALL':'C','PYTHONDONTWRITEBYTECODE':'1'},cwd=str(tmp_path))
        out,err=await asyncio.wait_for(proc.communicate(),30)
        assert not err
        return proc.returncode,json.loads(out)
    rc,value=asyncio.run(run())
    (tmp_path/'cold-result.json').write_bytes(cli.encoded(value))
    if mutation=='none':
        assert rc==0 and value['pid']!=os.getpid() and not value['new_live_authority']
        assert len(value['accepted'])==3 and [x['rows'] for x in value['roles']]==[1000,1000]
    else:assert rc==2 and value['status']=='COLD_DENIED'


def test_new_composer_binds_exact_original_classes_without_starting_worker(case,local_lane,tmp_path,monkeypatch):
    import asyncio
    from types import SimpleNamespace
    from app.services.scoped_external_code_manifest import CONTRACT_V2, REQUIRED_V2
    from app.services.kiwoom_participant_session import ParticipatingSession
    from app.services.current_scoped_worker_bridge import ScopedBridge
    from app.services.sealed_source_transport import SealedSourceTransport
    lane,active,_,_=local_lane
    external=tmp_path/'SYNTHETIC_CODE_NOT_EXECUTED';external.mkdir()
    pins={}
    for name in sorted(REQUIRED_V2):
        p=external/name;p.parent.mkdir(parents=True,exist_ok=True)
        p.write_bytes(b'# Synthetic interface file, never executed.\n');pins[name]=cli.pin(p)
    m=json.loads((r.ROOT/'ops/manual-source-parent.json').read_bytes())
    m['original_external_code']=dict(pins)
    # The reviewed superset is not the 19-file runtime closure.
    m['original_external_code']['app/unused_reviewed.py']=dict(bytes=0,sha256=cli.digest(b''))
    assert r.original_external_pins(m,CONTRACT_V2)==pins
    case['metadata']['owner_files']={n:p['sha256'] for n,p in pins.items()}
    session=ParticipatingSession(modules=(lane,),caller_kind='CLI')
    def no_launch(*a,**k):pytest.fail('WORKER_MUST_NOT_START')
    monkeypatch.setattr(asyncio,'create_subprocess_exec',no_launch)
    settings=SimpleNamespace(kiwoom_app_key='SYNTHETIC_APP_KEY',kiwoom_secret_key='SYNTHETIC_SECRET',
        kiwoom_rest_base_url='https://api.kiwoom.com',kiwoom_rest_request_interval_seconds=1.5)
    async def flow():
        with r.capture_registered_runtime(**case) as (handle,_):
            dispatcher,worker=await r.bind_original_worker(handle=handle,manifest=m,
                configuration=dict(external_root=str(external),external_code_contract=CONTRACT_V2),
                settings=settings,session=session,output=tmp_path/'runtime')
            assert type(worker) is ScopedBridge and type(worker.transport) is SealedSourceTransport
            assert worker.transport.dispatcher is dispatcher and dispatcher._account_pacer is active
            assert manual.describe(handle)['runtime_bound']
            assert worker.process is None and dispatcher.physical_attempts==0
            await worker.shutdown();await worker.transport.inner.aclose()
        session.close_admission()
    asyncio.run(flow())


@pytest.mark.parametrize('kind',['missing','legacy'])
def test_external_runtime_contract_cannot_expand_authorized_code(kind):
    from app.services.scoped_external_code_manifest import CONTRACT_V2
    m=json.loads((r.ROOT/'ops/manual-source-parent.json').read_bytes())
    if kind=='missing':m['original_external_code'].pop('app/services/kiwoom_global_lane.py')
    with pytest.raises(ValueError):r.original_external_pins(m,None if kind=='legacy' else CONTRACT_V2)


def test_invocation_claim_is_exclusive_and_not_live_authority(tmp_path):
    config={'output_root':str(tmp_path/'current-attempt')}
    out=cli.claim_current_invocation(config,'a'*64,'SYNTHETIC_CURRENT')
    claim=(out/'invocation-claimed.json').read_bytes()
    assert 'NOT_A_SERIALIZED_CAPABILITY' in claim.decode()
    with pytest.raises(FileExistsError):cli.claim_current_invocation(config,'a'*64,'SYNTHETIC_CURRENT')
    assert (out/'invocation-claimed.json').read_bytes()==claim


def test_kernel_query_checks_all_four_paths_without_opening_database(monkeypatch):
    from types import SimpleNamespace
    calls=[]
    class Kernel:
        restype=None
        def __call__(self,pid,operation,filter_type,path):
            calls.append((pid,operation,filter_type,path));return 1
    kernel=Kernel()
    monkeypatch.setattr(r.sys,'platform','darwin')
    monkeypatch.setattr(r.ctypes,'CDLL',lambda *a,**k:SimpleNamespace(sandbox_check=kernel))
    result=r._os_decisions(Path('/private/tmp/NEVER_OPEN_PROTECTED.sqlite3'))
    assert len(result)==len(calls)==32 and all(result.values())
    assert {x[2] for x in calls}=={1} and len({x[3] for x in calls})==4


def test_source_safety_stop_is_preserved_as_terminal_report(monkeypatch):
    from app.services.unified_live_source_transport import SourceSafetyStop
    m=json.loads((r.ROOT/'ops/manual-source-parent.json').read_bytes())
    monkeypatch.setattr(cli,'validate_manifest',lambda *a:m)
    def fail(*a):raise SourceSafetyStop('SYNTHETIC_TERMINAL_NO_RETRY')
    monkeypatch.setattr(cli,'confirm_owner',fail)
    report,rc=cli.main(['--preflight','--manifest-sha256','a'*64,'--invocation-id','SYNTHETIC_FINAL'])
    assert rc==2 and report['exception_type']=='SourceSafetyStop'
    assert report['financial_calls']==report['database_sessions']==report['models']==0
