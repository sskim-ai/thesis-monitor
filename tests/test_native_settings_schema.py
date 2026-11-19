"""Only canonical-to-Native child settings mapping; no live Source or model."""
import ast
import asyncio
from copy import deepcopy
import json
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pytest

from app.config import Settings
from app.services.production_source_configuration import native_child_environment
from app.services.production_source_context import inspect_native
from app.services.sealed_native_bridge import SealedNativeBridge
from app.services.unified_live_source_transport import SourceSafetyStop
from app.services.unified_run_artifacts import sha256_bytes
from scripts.unified_stock_source_worker import encoded
from tests.test_native_env_path_parity import native, packet, MARKER
from tests.test_manual_source_budget import offline_only

BASE = 'a5012d008ad217304ed8c5ccac7a8e05220c4926'
REPO = Path(__file__).resolve().parents[1]


@pytest.fixture
def schema(native, offline_only, monkeypatch):
    n = native
    n.env.write_text('KIWOOM_APP_KEY=' + MARKER + '\nKIWOOM_SECRET_KEY=' + MARKER + '_2\n'
        'ENABLE_LIVE_PROVIDERS=true\n')
    for key in ('ENABLE_LIVE_PROVIDERS', 'KIWOOM_REST_BASE_URL'):
        monkeypatch.delenv(key, raising=False)
    n.settings = Settings(_env_file=n.env)
    return n


def inspect(n, name):
    folder = n.tmp / name
    folder.mkdir()
    return inspect_native(n.config, folder, settings_env_file=str(n.env), settings=n.settings)


def bridge(n, value, monkeypatch, name, *, bad_input=False, mapped=True):
    from app.services import sealed_native_bridge as module
    assert module.sys.executable == sys.executable
    # Original Bridge launch/env and r9 main/guards run. Only Native acquisition
    # and replay bodies are stubs, and r9 still blocks direct network access.
    script = '''import json,sys
from pathlib import Path
from scripts import r9_rev11_native_worker as w
root=Path(sys.argv[sys.argv.index('--owner-root')+1])
frozen=json.loads(Path(sys.argv[sys.argv.index('--input')+1]).read_bytes())
def acquire(plan,out,owner,settings,**kw):
    from app.config import Settings
    p=frozen['native_owner']['settings_env_file']
    assert w.stock_worker.owner_configuration(root,Settings(_env_file=p),settings_env_file=p)==frozen['native_owner']
    out.mkdir(parents=True)
    return {'SYNTHETIC_ONLY':True}
def replay(plan,out,owner,**kw):
    (out.parent/'raw-owner-replay.json').write_text(json.dumps([{'status':'PASS'}]))
w.stock_worker.acquire=acquire
w.stock_worker.replay=replay
w.main()
'''
    monkeypatch.setattr(module, 'native_worker_command', lambda: (sys.executable, '-B', '-c', script))
    path = n.tmp / (name + '.json')
    path.write_bytes(encoded(value))
    output = n.tmp / (name + '-out')
    output.mkdir()
    return SealedNativeBridge(owner_root=n.root, input_path=path,
        input_sha256='0' * 64 if bad_input else sha256_bytes(path.read_bytes()), output=output,
        transport=SimpleNamespace(dispatcher=SimpleNamespace(results={}, plan=SimpleNamespace(generation_id='SYNTHETIC_ENV'))),
        market_reads=[], settings=n.settings if mapped else None)


def test_mapping_is_qualified_two_keys_only_and_never_changes_parent(schema, monkeypatch):
    n = schema
    monkeypatch.setenv('UNRELATED_SETTING', 'unchanged')
    before = dict(os.environ)
    child = native_child_environment(n.settings)
    assert dict(os.environ) == before
    assert {k for k in set(before) | set(child) if before.get(k) != child.get(k)} <= {
        'ENABLE_LIVE_PROVIDER', 'KIWOOM_BASE_URL_REAL'}
    assert child['ENABLE_LIVE_PROVIDER'] == str(n.settings.enable_live_providers).lower()
    assert child['KIWOOM_BASE_URL_REAL'] == n.settings.kiwoom_rest_base_url
    for update in ({'enable_live_providers': False}, {'kiwoom_rest_base_url': 'https://openapi.kiwoom.com'}):
        with pytest.raises(ValueError, match='CANONICAL_LIVE_OR_ENDPOINT_NOT_QUALIFIED'):
            native_child_environment(n.settings.model_copy(update=update))
    for key, value in (('ENABLE_LIVE_PROVIDER', 'false'), ('KIWOOM_BASE_URL_REAL', 'https://invalid.example')):
        with monkeypatch.context() as m:
            m.setenv(key, value)
            snapshot = dict(os.environ)
            with pytest.raises(ValueError, match='native_child_settings_environment_conflict'):
                native_child_environment(n.settings)
            assert dict(os.environ) == snapshot


def test_inspect_and_actual_bridge_child_share_file_settings_and_owner(schema, monkeypatch):
    n = schema
    before = dict(os.environ)
    raw = n.env.read_bytes()
    owner = inspect(n, 'qualified')
    assert owner['owner_clean'] and owner['credentials_present'] and owner['live_provider']
    assert owner['settings_env_file_sha256'] == sha256_bytes(raw)
    assert owner['base_url'] == n.settings.kiwoom_rest_base_url
    assert MARKER not in json.dumps(owner)
    original_launch = asyncio.create_subprocess_exec
    launches = []
    async def launch(*args, **kwargs):
        assert args[0] == sys.executable
        assert kwargs['env'] == native_child_environment(n.settings)
        launches.append(True)
        return await original_launch(*args, **kwargs)
    monkeypatch.setattr(asyncio, 'create_subprocess_exec', launch)
    async def run():
        b = bridge(n, packet(n, owner), monkeypatch, 'normal')
        try:
            assert (await b.command({'stocks': True}))['status'] == 'STOCK_CAPTURE_COMPLETE_NOT_QUALIFIED'
            assert (await b.command({'replay-stocks': True}))['status'] == 'PASS'
        finally:
            await b.shutdown()
        assert b.exit_receipt['returncode'] == 0
    asyncio.run(run())
    assert launches == [True] and dict(os.environ) == before
    assert n.env.read_bytes() == raw and not (n.root / '.env').exists()
    assert not subprocess.check_output(['/usr/bin/git', 'status', '--porcelain'], cwd=n.root).strip()


def test_file_owner_and_plan_drift_fail_closed_on_mapped_child(schema, monkeypatch):
    n = schema
    owner = inspect(n, 'negative')
    async def run():
        b = bridge(n, packet(n, owner), monkeypatch, 'input-pin', bad_input=True)
        with pytest.raises(SourceSafetyStop, match='native_input_drift'):
            await b.command({'stocks': True})
        assert b.process is None
        for index, field in enumerate(('owner_head', 'settings_sha256')):
            bad = packet(n, deepcopy(owner))
            if field == 'owner_head':
                bad['native_owner'][field] = '0' * 40
            else:
                bad['stock_plan'][field] = '0' * 64
            b = bridge(n, bad, monkeypatch, 'bad-' + str(index))
            with pytest.raises(SourceSafetyStop, match='native_worker_stopped'):
                await b.command({'stocks': True})
            assert b.exit_receipt['returncode'] != 0
        b = bridge(n, packet(n, owner), monkeypatch, 'changed-file')
        n.env.write_bytes(n.env.read_bytes() + b'# drift\n')
        with pytest.raises(SourceSafetyStop, match='native_worker_stopped'):
            await b.command({'stocks': True})
        assert b.exit_receipt['returncode'] != 0
    asyncio.run(run())


def test_legacy_inspector_and_bridge_do_not_apply_mapping(schema, monkeypatch):
    n = schema
    from app.services import production_source_context as context
    observed = []
    original_run = context.subprocess.run
    def call(*args, **kwargs):
        observed.append(kwargs.get('env'))
        return original_run(*args, **kwargs)
    monkeypatch.setattr(context.subprocess, 'run', call)
    with pytest.raises(ValueError, match='production_native_owner_not_qualified'):
        inspect_native(n.config, n.tmp, settings_env_file=str(n.env))
    assert observed == [None]
    b = bridge(n, {}, monkeypatch, 'legacy', mapped=False)
    assert b._settings is None


def test_only_selected_us_routine_mapping_changes_and_existing_policies_stay():
    names = ['app/jobs/unified_market_snapshot.py', 'app/services/canonical_source_acquisition.py']
    for name in names:
        before = ast.parse(subprocess.check_output(['/usr/bin/git', 'show', BASE + ':' + name], cwd=REPO))
        current = ast.parse((REPO / name).read_bytes())
        function = 'inspect_native' if name == names[0] else 'SealedNativeBridge'
        call = next(n for n in ast.walk(current) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == function)
        keyword = next(k for k in call.keywords if k.arg == 'settings')
        expression = ast.unparse(keyword.value)
        assert ("market == 'us'" in expression if name == names[0] else
            all(v in expression for v in ('selected', 'us_only', 'not test_scope', 'routine_us_no_send_source_seconds')))
        call.keywords.remove(keyword)
        assert ast.dump(before) == ast.dump(current)
    # No changes to budgets, timers, DB root, S/R, B2, SKHY, profile or schedule.
    tree = ast.parse((REPO / 'app/services/production_source_configuration.py').read_bytes())
    assert not any(isinstance(n, ast.Subscript) and isinstance(n.ctx, ast.Store)
        and ast.unparse(n.value) == 'os.environ' for n in ast.walk(tree))
