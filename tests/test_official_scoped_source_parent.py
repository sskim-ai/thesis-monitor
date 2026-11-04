"""Focused launcher tests. No real host admission, credentials, DB or HTTP."""
import asyncio
from copy import deepcopy
import importlib.util
import io
import json
import os
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('official_parent_under_test', ROOT/'scripts/official_scoped_source_parent.py')
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)


@pytest.fixture
def manifest():
    return json.loads((ROOT/'ops/manual-source-parent.json').read_bytes())


def test_installed_source_pins_and_review_only(manifest, monkeypatch):
    path=ROOT/'ops/manual-source-parent.json'
    monkeypatch.setattr(p.sys,'executable',manifest['interpreter'])
    result=p.validate_manifest(path,p.digest(path.read_bytes()))
    value,rc=p.main(['--preflight','--dry-run','--invocation-id','TEST_ONLY_REVIEW',
                    '--manifest-sha256',p.digest(path.read_bytes())])
    assert rc==0 and value['status']=='REVIEW_ONLY_NO_APP_IMPORT_OR_OPTIN'
    assert value['owner_approved'] is False and not value['source_owner_issued']
    assert result['default_enabled'] is False


@pytest.mark.parametrize('kind',['hash','source','environment','budget','purpose','module','approval','interpreter'])
def test_manifest_drift_denied(manifest,monkeypatch,kind):
    path=ROOT/'ops/manual-source-parent.json'
    if kind=='hash':
        with pytest.raises(p.AdmissionDenied):p.validate_manifest(path,'0'*64)
        return
    body=deepcopy(manifest)
    if kind=='source':body['source_pins']['scripts/official_scoped_source_parent.py']['sha256']='0'*64
    if kind=='environment':body['environment']['KIWOOM_MAINTENANCE_STARTUP']='0'
    if kind=='budget':body['limits']['HTTP']=21
    if kind=='purpose':body['purpose']='PRODUCTION'
    if kind=='module':body['modules']=body['modules'][:-1]
    if kind=='approval':body['owner_approved']=True
    if kind=='interpreter':body['interpreter']='/not/a/python'
    raw=p.encoded(body);read=Path.read_bytes
    monkeypatch.setattr(Path,'read_bytes',lambda self:raw if self==path else read(self))
    monkeypatch.setattr(p.sys,'executable',manifest['interpreter'])
    with pytest.raises(p.AdmissionDenied):p.validate_manifest(path,p.digest(raw))


@pytest.mark.parametrize('operation,invocation',[('collect','TEST_ONLY_1'),('preflight','x'),('canary','../escape')])
def test_operation_and_invocation_bound(manifest,operation,invocation):
    with pytest.raises(p.AdmissionDenied):p.review(manifest,'f'*64,operation,invocation)


def test_no_terminal_is_not_an_approval(monkeypatch):
    monkeypatch.setattr(p.sys,'stdin',io.StringIO('APPROVE'))
    with pytest.raises(p.AdmissionDenied,match='owner_terminal'):
        p.confirm_owner('a'*64,'TEST_ONLY_1','preflight')


def test_exact_local_confirmation_not_os_or_financial_grant(monkeypatch):
    monkeypatch.setattr(p.sys,'stdin',SimpleNamespace(isatty=lambda:True))
    monkeypatch.setattr(p.sys,'stdout',SimpleNamespace(isatty=lambda:True,write=lambda x:None,flush=lambda:None))
    monkeypatch.setattr('builtins.input',lambda:'APPROVE preflight TEST_ONLY_1 '+'a'*64)
    value=p.confirm_owner('a'*64,'TEST_ONLY_1','preflight')
    assert not value['os_permission_granted'] and not value['account_exclusivity_proven']


def test_wrong_local_confirmation_denied(monkeypatch):
    monkeypatch.setattr(p.sys,'stdin',SimpleNamespace(isatty=lambda:True))
    monkeypatch.setattr(p.sys,'stdout',SimpleNamespace(isatty=lambda:True,write=lambda x:None,flush=lambda:None))
    monkeypatch.setattr('builtins.input',lambda:'APPROVE old-run old-hash')
    with pytest.raises(p.AdmissionDenied,match='confirmation_denied'):
        p.confirm_owner('a'*64,'TEST_ONLY_1','preflight')


@pytest.mark.parametrize('event,args',[
    ('socket.connect',(None,('example.invalid',443))),('sqlite3.connect',('/private/protected.sqlite3',)),
    ('subprocess.Popen',('/bin/true',)),('os.remove',('/tmp/any',)),
    ('open',('/private/test/.env', 'r', os.O_RDONLY)),
    ('open',('/private/test/auth.json', 'r', os.O_RDONLY)),
    ('open',('/private/test/data.sqlite3-wal', 'r', os.O_RDONLY)),
    ('open',('/private/test/state.json', 'w', os.O_WRONLY|os.O_TRUNC)),
    ('open',('/private/test/lane.lock', 'w', os.O_RDWR|os.O_CREAT)),
])
def test_readonly_guard_denies_before_side_effect(event,args):
    guard=p.ReadOnlyPreflight('/private/test')
    with pytest.raises(p.AdmissionDenied):guard(event,args)
    assert len(guard.denials)==1


def test_readonly_guard_allows_original_lock_identity_open_only():
    guard=p.ReadOnlyPreflight('/private/test')
    guard('open',('/private/test/lane.lock',None,os.O_RDWR|os.O_NOFOLLOW))
    guard('open',('/private/test/activation.json','r',os.O_RDONLY))
    assert guard.denials==[]


def test_receipt_only_exclusive_creation_under_private_root(manifest,tmp_path):
    root=tmp_path/'receipts';root.mkdir(mode=0o700)
    m=deepcopy(manifest);m['owner_receipts_root']=str(root)
    dest=root/'TEST_ONLY_1.json'
    assert p.receipt_destination(m,'TEST_ONLY_1',dest)==dest
    guard=p.ReadOnlyPreflight('/private/test',dest)
    guard('open',(str(dest),'x',os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW))
    with pytest.raises(p.AdmissionDenied):guard('open',(str(dest),'w',os.O_WRONLY|os.O_TRUNC))
    p.write_public_receipt(dict(receipt_path=str(dest),test_only=True))
    with pytest.raises(p.AdmissionDenied):p.receipt_destination(m,'TEST_ONLY_1',dest)


def test_symlink_manifest_denied(tmp_path):
    link=tmp_path/'link';link.symlink_to(ROOT/'ops/manual-source-parent.json')
    with pytest.raises(p.AdmissionDenied,match='plain_path'):p.validate_manifest(link,'0'*64)


def test_old_unused_grant_cannot_open_canary(manifest):
    with pytest.raises(p.AdmissionDenied,match='current_canary_configuration_and_grant'):
        p.require_canary_installation(manifest,'TEST_ONLY_1')


def test_caller_json_cannot_attest_os_db_boundary(manifest):
    m=deepcopy(manifest)
    m['canary_installation'].update(current_invocation_id='TEST_ONLY_1',database='/private/fake.sqlite3',
        settings_file='/private/fake.env',os_readonly_launcher='caller-hash-not-authority')
    with pytest.raises(p.AdmissionDenied,match='current_canary_configuration_and_grant'):
        p.require_canary_installation(m,'TEST_ONLY_1')


def test_optin_before_import_and_no_maintenance_override(manifest,monkeypatch):
    monkeypatch.setattr(p.sys,'flags',SimpleNamespace(isolated=1))
    monkeypatch.setattr(p.sys,'dont_write_bytecode',True)
    monkeypatch.setattr(p.sys,'modules',{k:v for k,v in p.sys.modules.items() if not k.startswith('app')})
    monkeypatch.setattr(p.sys,'path',list(p.sys.path))
    monkeypatch.setattr(p.sys,'meta_path',list(p.sys.meta_path))
    monkeypatch.delenv('KIWOOM_GLOBAL_LANE_REQUIRED',raising=False)
    monkeypatch.setenv('KIWOOM_MAINTENANCE_STARTUP','1')
    with pytest.raises(p.AdmissionDenied,match='maintenance_hold'):p.bootstrap(manifest)
    assert 'KIWOOM_GLOBAL_LANE_REQUIRED' not in os.environ
    monkeypatch.setenv('KIWOOM_MAINTENANCE_STARTUP','0')
    p.bootstrap(manifest)
    assert os.environ['KIWOOM_GLOBAL_LANE_REQUIRED']=='1'
    assert isinstance(p.sys.meta_path[0],p.PinnedApplicationImports)


def test_unpinned_import_rejected_before_loader(manifest):
    finder=p.PinnedApplicationImports(dict(source_pins={}))
    with pytest.raises(p.AdmissionDenied,match='import_pin_mismatch'):
        finder.find_spec('app',[str(ROOT)])


def test_original_parent_boot_denial_not_replaced(manifest,monkeypatch):
    lane=SimpleNamespace(DEFAULT_ROOT=Path(manifest['lane_root']))
    maintenance=SimpleNamespace(assert_operation_allowed=lambda:None)
    def denied(**kwargs):raise ValueError('global_lane_boot_identity_unavailable')
    modules=[lane,maintenance,SimpleNamespace(ParticipatingSession=denied)]+[object()]*5
    monkeypatch.setattr(p.importlib,'import_module',lambda n:modules[p.MODULES.index(n)])
    monkeypatch.setattr(p,'lane_snapshot',lambda root:{'test_only':True})
    with pytest.raises(ValueError,match='boot_identity_unavailable'):p.admit_parent(manifest)


def test_original_runtime_rejects_receipt_instead_of_live_parent():
    from app.services import manual_scoped_source_runtime as manual
    with pytest.raises(ValueError,match='live_handle_required'):manual.inputs({'accepted':True})


def test_sanitized_errors_do_not_expose_private_exception():
    assert p.safe_error(ValueError('secret=EXAMPLE_NOT_REAL'))=='ValueError'
    assert p.safe_error(ValueError('global_lane_boot_identity_unavailable'))=='global_lane_boot_identity_unavailable'


def test_new_launcher_original_participant_on_test_only_lane(manifest,tmp_path,monkeypatch):
    from app.services import kiwoom_global_lane as lane
    from app.services.unified_snapshot_contract import digest, encoded
    root=tmp_path/'test-only-lane';root.mkdir(mode=0o700)
    activation=dict(protocol=lane.PROTOCOL,generation='LAUNCHER_TEST_ONLY',boot_identity='test-only-boot',
        implementation_sha256=p.digest(Path(lane.__file__).read_bytes()))
    state=dict(protocol=lane.PROTOCOL,generation='LAUNCHER_TEST_ONLY',boot_identity='test-only-boot',
        last_end=None,in_flight=False,halted=False,sequence=7,pid=0)
    for name,body in [('activation.json',activation),('state.json',state)]:
        (root/name).write_bytes(encoded(body));(root/name).chmod(0o600)
    (root/'lane.lock').touch(mode=0o600)
    actual=lane.GlobalKiwoomLane(root,boot=lambda:'test-only-boot')
    monkeypatch.setattr(lane,'DEFAULT_ROOT',root)
    monkeypatch.setattr(lane,'boot_identity',lambda:'test-only-boot')
    monkeypatch.setattr(lane,'configured_lane',lambda:actual)
    m=deepcopy(manifest);m.update(lane_root=str(root),activation_digest=digest(activation),
        lock_identity=list(actual.lock_identity))
    before=p.lane_snapshot(root)
    session,receipt=p.admit_parent(m)
    assert receipt['physical_slots']==0 and receipt['sequence_observed']==7
    assert receipt['child_policy']['effective_child_isolation'].startswith('NOT_RUN')
    assert receipt['parent']['caller_kind']=='CLI'
    session.close_admission()
    assert before==p.lane_snapshot(root)
