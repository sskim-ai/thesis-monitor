"""V3-only regression. Synthetic registration/lane, no actual account or DB."""
import asyncio
from copy import deepcopy
import importlib.util
import json
import os
from pathlib import Path
import sqlite3
import subprocess
from types import SimpleNamespace

import httpx
import pytest

from app.services import source_parent_canary_v3 as v3
from app.services import official_registered_source_runtime as r
from app.services import manual_scoped_source_runtime as manual
from app.services import prospective_class_c_owner as owner
from app.services.unified_snapshot_contract import digest
from tests.test_official_registered_source_runtime import case, local_lane, cli

spec=importlib.util.spec_from_file_location('v3_cli_test',r.ROOT/'scripts/official_source_canary_v3.py')
entry=importlib.util.module_from_spec(spec);spec.loader.exec_module(entry)


@pytest.fixture
def v3case(case,monkeypatch):
    r._BOUNDARIES.pop(case['boundary'])
    case['boundary']=v3.admit_readonly(case['database'],case['approval'],enabled=True)
    case['boundary_policy']=v3.DB_POLICY
    def no_mock_os(*a):
        pytest.fail('V3 MUST NOT CLAIM OS WRITE DENIAL')
    monkeypatch.setattr(r,'_os_decisions',no_mock_os)
    return case


@pytest.mark.parametrize('markets',[('kr',),('kr','us')])
def test_original_exporter_owners_same_memory_and_exact_scoped_plan(v3case,markets,monkeypatch):
    import app.services.minimal_class_c_export as export
    original=export.read_authorized_rows
    receipts=[]; connections=[]
    def capture(permission,**kw):
        def connect(database_uri,**kwargs):
            connections.append((database_uri,kwargs));return sqlite3.connect(database_uri,**kwargs)
        rows,receipt=original(permission,connect=connect)
        receipts.append(receipt);return rows,receipt
    monkeypatch.setattr(export,'read_authorized_rows',capture)
    counters={'registration_session_attempts':0}
    scope=v3.CanaryScope(markets=markets,us_http=12 if 'us' in markets else 0)
    with r.capture_registered_runtime(**v3case,capture_markets=markets,counters=counters) as (handle,public):
        plan=v3.validate_plan(handle,scope)
        assert plan['planned']=={'auth':1,'kr':7,'us':12 if 'us' in markets else 0}
        assert public['boundary_policy']==v3.DB_POLICY
        assert public['registration']['SELECT']==5 and not public['private_rows_exported']
        assert not public['financial_or_economic_authority']
        assert 'core_thesis' not in json.dumps(public)
        assert manual.completed_sessions(handle)['us']
    assert len(connections)==len(receipts)==1
    assert connections[0][0].endswith('?mode=ro') and connections[0][1]['uri'] is True
    q=receipts[0]
    assert q['query_only'] and q['sqlite_mode']=='ro' and q['total_changes']==0 and not q['denied_queries']
    assert sum(x['operation']=='SELECT' for x in q['query_trace'])==5
    assert counters==dict(registration_session_attempts=1,registration_sessions_completed=1,SELECT=5)
    assert v3case['boundary'] not in v3._READS
    with pytest.raises(ValueError):owner._approval(v3case['approval'])
    with pytest.raises(ValueError):manual.inputs(handle)


@pytest.mark.parametrize('kind',['json','unissued','revoked','process','identity','second_session','default_off'])
def test_readonly_boundary_denies_before_query(v3case,kind,tmp_path,monkeypatch):
    args=dict(v3case);opened=[]
    monkeypatch.setattr(r,'capture_authorized_class_c',lambda p:opened.append(p))
    if kind=='default_off':
        with pytest.raises(ValueError,match='default_off'):
            v3.admit_readonly(args['database'],args['approval'])
        return
    if kind=='json':args['boundary']={'readonly':True}
    elif kind=='unissued':args['boundary']=v3.TrustedReadonlyRegistration()
    elif kind=='revoked':owner.revoke_approval(args['approval'])
    elif kind=='process':v3._READS[args['boundary']]['pid']=-1
    elif kind=='identity':v3._READS[args['boundary']]['identity']=(-1,-1)
    else:v3.require_readonly(args['boundary'],args['database'],args['approval'],consume=True)
    with pytest.raises((ValueError,TypeError)):
        with r.capture_registered_runtime(**args):pytest.fail('NO QUERY AUTHORITY')
    assert opened==[]


def test_sql_authorizer_cannot_write_attach_or_read_unlisted(v3case):
    from app.services.minimal_class_c_export import QueryBoundary
    c=sqlite3.connect(v3case['database'].as_uri()+'?mode=ro',uri=True)
    try:
        c.execute('PRAGMA query_only=ON')
        b=QueryBoundary();b.boot=False;c.set_authorizer(b)
        for statement in ('DELETE FROM watchlistitem',"ATTACH ':memory:' AS extra",
                          'SELECT name FROM sqlite_master','PRAGMA query_only=OFF'):
            with pytest.raises(sqlite3.DatabaseError):c.execute(statement)
        assert c.total_changes==0 and len(b.denied)==4
    finally:c.close()


def test_original_os_denial_is_not_replaced(v3case,monkeypatch):
    def denied(*a,**k):raise PermissionError('SYNTHETIC_OS_DENIAL')
    monkeypatch.setattr(r,'capture_authorized_class_c',denied)
    with pytest.raises(PermissionError,match='OS_DENIAL'):
        with r.capture_registered_runtime(**v3case):pytest.fail('NO BYPASS')
    assert v3case['boundary'] not in v3._READS


def test_v2_still_demands_effective_os_denial(case,monkeypatch):
    monkeypatch.setattr(r,'_os_decisions',lambda p:{'write':False})
    with pytest.raises(ValueError,match='effective_os'):
        with r.capture_registered_runtime(**case):pytest.fail('V2 CHANGED')


def test_v2_release_migration_does_not_silently_change_old_gates(monkeypatch):
    path=r.ROOT/'ops/manual-source-parent.json';m=json.loads(path.read_bytes())
    monkeypatch.setattr(cli.sys,'executable',m['interpreter'])
    actual=cli.validate_manifest(path,cli.pin(path)['sha256'])
    assert actual['contract']=='official-manual-scoped-source-parent-v2'
    assert actual['activation_digest']=='1b56b3c6b01135f9c8f7c46460f208f50c50119d8579a11bb38bf1ac90c59560'
    assert actual['limits']['US_bytes']==12*v3.GIB and not actual['owner_approved']
    with pytest.raises(ValueError):cli.require_canary_installation(actual,'NO_OLD_APPROVAL_REUSE')


@pytest.mark.parametrize('kind',['valid','digest','generation','boot','implementation','lock','halted','inflight','schema'])
def test_release_rebase_preserves_actual_security_fields(local_lane,kind):
    lane,active,m,state=local_lane
    activation=json.loads((active.root/'activation.json').read_bytes())
    anchor=dict(activation=deepcopy(activation),official_digest=digest(activation),lock_identity=list(active.lock_identity))
    args=dict(activation=activation,state=state,anchor=anchor,lock_identity=active.lock_identity,
        current_boot=activation['boot_identity'],implementation_sha=cli.pin(lane.__file__)['sha256'])
    if kind=='digest':anchor['official_digest']='0'*64
    elif kind=='generation':state['generation']='OTHER'
    elif kind=='boot':args['current_boot']='OTHER'
    elif kind=='implementation':args['implementation_sha']='0'*64
    elif kind=='lock':args['lock_identity']=(0,0)
    elif kind=='halted':state['halted']=True
    elif kind=='inflight':state['in_flight']=True
    elif kind=='schema':state['undocumented']=True
    if kind=='valid':assert v3.validate_activation(**args)['sequence_observed']==0
    else:
        with pytest.raises(ValueError):v3.validate_activation(**args)


def test_actual_parent_on_synthetic_lane_and_immutable_state(local_lane):
    lane,active,m,state=local_lane
    m['activation_anchor']=dict(activation=json.loads((active.root/'activation.json').read_bytes()),
        official_digest=m['activation_digest'],lock_identity=m['lock_identity'])
    before=(active.root/'state.json').read_bytes()
    session,proof=v3.admit_parent(m,cli)
    session.close_admission()
    assert proof['physical_slots']==0 and before==(active.root/'state.json').read_bytes()


def test_real_boot_denial_propagates_without_fallback(local_lane,monkeypatch):
    lane,active,m,_=local_lane
    def denied():raise lane.GlobalLaneStop('global_lane_boot_identity_unavailable')
    monkeypatch.setattr(lane,'boot_identity',denied)
    with pytest.raises(lane.GlobalLaneStop,match='boot_identity_unavailable'):v3.admit_parent(m,cli)


def test_one_parent_slot_per_physical_attempt_and_no_duplicate(v3case,local_lane,tmp_path):
    from app.services.current_scoped_source_dispatch import CurrentScopedDispatcher
    from app.services.sealed_source_transport import CapturedFragment
    from app.services.unified_live_source_transport import SourceSafetyStop
    _,active,_,_=local_lane
    with r.capture_registered_runtime(**v3case,capture_markets=('kr',)) as (handle,_):
        parent,wire,_=manual.inputs(handle);plan=wire['request_plan']
        run=CurrentScopedDispatcher(parent=parent,plan=plan,root=tmp_path/'dispatch',
            owners={d.normalizer:d.owner_sha256 for d in plan.descriptors},
            config_identities={'kiwoom':v3case['config_identities']['kiwoom']},credential_presence={'kiwoom':True},
            account_pacer=active)
        d=next(d for d in plan.descriptors if d.endpoint_operation=='ka10081' and d.page_ordinal==1)
        q=json.loads(d.request_json);calls=[]
        async def flow():
            transport=httpx.MockTransport(lambda req:(calls.append(True) or httpx.Response(200,json={'return_code':0})))
            request=httpx.Request(q['method'],q['url'],headers=q['headers'],content=q['body'].encode())
            await run.execute(d.logical_request_id,request,transport=transport,normalize=CapturedFragment(d))
            assert json.loads((active.root/'state.json').read_bytes())['sequence']==1
            with pytest.raises(SourceSafetyStop):
                await run.execute(d.logical_request_id,request,transport=transport,normalize=CapturedFragment(d))
        asyncio.run(flow())
        assert len(calls)==run.physical_attempts==1
        assert json.loads((active.root/'state.json').read_bytes())['halted'] is True


@pytest.mark.parametrize('free,passes',[(6*v3.GIB,True),(6*v3.GIB-1,False),(11*v3.GIB,True)])
def test_canary_guard_only_not_full_guard(tmp_path,monkeypatch,free,passes):
    monkeypatch.setattr(v3.os,'statvfs',lambda p:SimpleNamespace(f_bavail=free,f_frsize=1))
    if passes:assert v3.check_space([tmp_path],v3.CanaryScope())[0]['required_bytes']==6*v3.GIB
    else:
        with pytest.raises(ValueError,match='headroom'):v3.check_space([tmp_path],v3.CanaryScope())
    with pytest.raises(ValueError,match='headroom'):r.check_space([tmp_path])


def test_source_plan_cannot_use_unapproved_us(v3case):
    with r.capture_registered_runtime(**v3case) as (handle,_):
        with pytest.raises(ValueError,match='D1000_scope'):
            v3.validate_plan(handle,v3.CanaryScope(markets=('kr',),us_http=0))


def test_manifest_checks_core_once_but_other_code_on_import(monkeypatch):
    path=r.ROOT/'ops/manual-source-parent-v3.json';m=json.loads(path.read_bytes())
    monkeypatch.setattr(entry.sys,'executable',m['interpreter'])
    reads=[];original=entry.pin
    def track(p):reads.append(str(p));return original(p)
    monkeypatch.setattr(entry,'pin',track)
    value,loader=entry.validate_manifest(path,cli.pin(path)['sha256'])
    assert len(reads)==len(entry.CORE)+1 and len(value['source_pins'])>len(entry.CORE)
    finder=loader.PinnedApplicationImports(value)
    finder.pins['app/services/market_session.py']={'bytes':0,'sha256':'0'*64}
    with pytest.raises(ValueError,match='import_pin_mismatch'):
        finder.find_spec('app.services.market_session',[str(r.ROOT/'app/services')])


def test_single_grant_cancellation_and_claim_do_not_reuse(v3case,monkeypatch,tmp_path):
    monkeypatch.setattr(__import__('sys').stdin,'isatty',lambda:True)
    monkeypatch.setattr(__import__('sys').stdout,'isatty',lambda:True)
    monkeypatch.setattr('builtins.input',lambda:'CANCEL')
    with pytest.raises(ValueError,match='confirmation_denied'):
        v3.confirm_grant('a'*64,'SYNTHETIC_CURRENT',dict(database=str(v3case['database']),
            execution_plan_sha256='b'*64),v3.CanaryScope())
    c={'output_root':str(tmp_path/'claimed')}
    cli.claim_current_invocation(c,'a'*64,'SYNTHETIC_CURRENT')
    with pytest.raises(FileExistsError):cli.claim_current_invocation(c,'a'*64,'SYNTHETIC_CURRENT')


def test_fresh_process_release_review_does_not_import_app_or_touch_host(tmp_path):
    path=r.ROOT/'ops/manual-source-parent-v3.json';m=json.loads(path.read_bytes())
    out=subprocess.run([m['interpreter'],'-I','-B',str(r.ROOT/'scripts/official_source_canary_v3.py'),
        '--preflight','--dry-run','--manifest-sha256',cli.pin(path)['sha256'],
        '--invocation-id','V3_SYNTHETIC_DRY_REVIEW'],capture_output=True,timeout=30,
        env={'PATH':'/usr/bin:/bin','LC_ALL':'C','PYTHONDONTWRITEBYTECODE':'1'},cwd=tmp_path)
    assert out.returncode==0 and not out.stderr
    value=json.loads(out.stdout)
    assert value['status']=='REVIEW_ONLY_NO_APP_IMPORT_OR_OPTIN'
    assert value['financial_calls']==value['database_sessions']==value['models']==0
    (tmp_path/'v3-dry-process.json').write_bytes(out.stdout)
