"""Only changed manifest boundaries; no real credentials, DB or worker launch."""
from copy import deepcopy
import ast
import hashlib
import importlib.abc
import importlib.util
from pathlib import Path
from types import ModuleType, SimpleNamespace
import pytest
from app.services.scoped_external_code_manifest import (
    CONTRACT_V2, REQUIRED_V2, validate_external_manifest,
)
from app.services import manual_scoped_source_runtime as manual
from app.services import current_class_c_source_bridge as registration
from app.services.unified_snapshot_contract import encoded
from tests.test_manual_scoped_source_runtime import case, p2g_case, runtime, POLICY, CONFIG


def pins():
    return {n:dict(bytes=0,sha256='a'*64) for n in REQUIRED_V2}


def test_explicit_version_preserves_legacy_and_has_no_authority_return():
    assert validate_external_manifest({str(i):{} for i in range(25)}) is None
    assert validate_external_manifest(pins(), CONTRACT_V2) is None
    with pytest.raises(ValueError,match='legacy'):
        validate_external_manifest(pins())
    with pytest.raises(ValueError,match='contract_or_closure'):
        validate_external_manifest(pins(), 'future-unapproved')


@pytest.mark.parametrize('change', ['missing_lazy','extra_main','path_escape','bad_hash','boolean_bytes','oversize'])
def test_exact_minimal_closure_rejects_addition_omission_and_bad_pins(change):
    p=pins()
    if change=='missing_lazy': del p['app/services/runtime_maintenance.py']
    elif change=='extra_main': p['app/main.py']=dict(bytes=1,sha256='b'*64)
    elif change=='path_escape': p['../.env']=p.pop('app/config.py')
    elif change=='bad_hash': p['app/config.py']['sha256']='NOT_A_HASH'
    elif change=='boolean_bytes': p['app/config.py']['bytes']=True
    elif change=='oversize': p['app/config.py']['bytes']=1024*1024+1
    with pytest.raises(ValueError): validate_external_manifest(p,CONTRACT_V2)


def test_v2_is_bound_to_original_parent_and_consumer_before_io(case,tmp_path):
    c=case
    native=tmp_path/'v2-native'
    native.mkdir()
    c['native_root']=native
    c['native_pins']={}
    for name in REQUIRED_V2:
        path=native/name;path.parent.mkdir(parents=True,exist_ok=True)
        path.write_bytes(b'# TEST_ONLY\n')
        c['native_pins'][name]=dict(bytes=12,sha256=manual.sha256_bytes(path.read_bytes()))
    kwargs=deepcopy({k:v for k,v in c['kwargs'].items() if k not in {'capture','owners','policy'}})
    kwargs.update(capture=c['kwargs']['capture'],owners=c['owners'],policy=POLICY)
    keys={'run_id','acquisition_id','instruction_sha','implementation_sha','owner_files',
          'owner_head','settings_sha256','request_environment_sha256'}
    kwargs['stock_metadata']={k:v for k,v in c['stock'].model_dump(mode='json').items() if k in keys}
    kwargs['stock_metadata']['owner_files']={n:v['sha256'] for n,v in c['native_pins'].items()}
    kwargs['counts']={m:dict(adjusted_daily=1000,adjusted_weekly=700,
        adjusted_monthly=300,unadjusted_weekly_valuation=300) for m in ('kr','us')}
    c['handle'],c['stock'],c['frozen']=registration.prepare_current_bridge(**kwargs,enabled=True)
    c['prepare']=dict(class_c_bridge=c['handle'],frozen=c['frozen'],stock_plan=c['stock'],
        policy=POLICY,maximum_attempts=20,provider_config_sha256=CONFIG)
    handle,dispatcher,worker,envelope=runtime(c,tmp_path)
    with pytest.raises(ValueError,match='legacy'):
        manual.bind_runtime(handle,dispatcher=dispatcher,worker_bridge=worker)
    envelope['external_code_contract']=CONTRACT_V2
    worker.frozen.write_bytes(encoded(envelope));worker.sha=manual.sha256_bytes(worker.frozen.read_bytes())
    value=manual.bind_runtime(handle,dispatcher=dispatcher,worker_bridge=worker)
    assert value['runtime_bound'] and not value['actual_source_issued']
    assert dispatcher.physical_attempts==0 and worker.process is None
    # Self-rehashing the lazy dependency cannot change the original parent's pins.
    path=native/'app/services/kiwoom_global_lane.py';path.write_bytes(b'# changed\n')
    envelope['external_pins']['app/services/kiwoom_global_lane.py']=dict(bytes=path.stat().st_size,
        sha256=manual.sha256_bytes(path.read_bytes()))
    worker.frozen.write_bytes(encoded(envelope));worker.sha=manual.sha256_bytes(worker.frozen.read_bytes())
    with pytest.raises(ValueError,match='pin_format_or_identity'):
        manual.bind_runtime(handle,dispatcher=dispatcher,worker_bridge=worker)
    assert dispatcher.physical_attempts==0 and worker.process is None


def loader(tmp_path):
    tree=ast.parse((manual.ROOT/'scripts/current_scoped_source_worker.py').read_bytes())
    cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='PinnedLoader')
    scope=dict(importlib=importlib,Path=Path,hashlib=hashlib,owner_root=tmp_path,
        frozen={'external_code_contract':CONTRACT_V2},CONTRACT_V2=CONTRACT_V2,pins={})
    exec(compile(ast.Module(body=[cls],type_ignores=[]),'original-loader-class','exec'),scope)
    return scope,scope['PinnedLoader']()


@pytest.mark.parametrize('condition',['valid','tampered','symlink'])
def test_original_loader_rechecks_bytes_and_refuses_symlink_before_read(tmp_path,monkeypatch,condition):
    scope, instance=loader(tmp_path)
    path=tmp_path/'app/config.py';path.parent.mkdir()
    raw=b'TEST_VALUE = 7\n';path.write_bytes(raw)
    scope['pins']['app/config.py']=dict(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
    mod=ModuleType('app.config');mod.__spec__=SimpleNamespace(origin=str(path))
    if condition=='valid':
        instance.exec_module(mod)
        assert mod.TEST_VALUE==7
    elif condition=='tampered':
        path.write_bytes(b'TEST_VALUE = 8\n')
        with pytest.raises(AssertionError):instance.exec_module(mod)
    else:
        target=tmp_path/'synthetic-private.py';target.write_bytes(raw)
        path.unlink();path.symlink_to(target)
        with monkeypatch.context() as m:
            m.setattr(Path,'read_bytes',lambda _:pytest.fail('SYMLINK_CONTENT_MUST_NOT_BE_READ'))
            with pytest.raises(PermissionError,match='SIZE_OR_PATH'):instance.exec_module(mod)


def test_original_loader_rejects_unapproved_lazy_dependency(tmp_path):
    _,instance=loader(tmp_path)
    with pytest.raises(PermissionError,match='UNAPPROVED_EXTERNAL_CODE_DEPENDENCY'):
        instance.find_spec('app.services.unapproved_dependency')
