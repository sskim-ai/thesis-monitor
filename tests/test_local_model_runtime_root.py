"""Filesystem/caller boundaries only; no Source authority or actual CLI calls."""
import ast
import asyncio
import inspect
import json
import os
from pathlib import Path
import stat
from types import SimpleNamespace

import pytest

from app.jobs import unified_market_snapshot as job
from app.services import production_model_transport as transport
from app.services.research_artifact_budget import ResearchArtifactBudget


def os_home(monkeypatch, path):
    path.mkdir(parents=True, mode=0o700)
    monkeypatch.setattr(job.pwd, 'getpwuid', lambda uid: SimpleNamespace(pw_dir=str(path)))
    monkeypatch.setenv('HOME', str(path.parent/'untrusted-launchd-HOME'))
    return path


def original_transport_guard(monkeypatch, runtime):
    binding=SimpleNamespace(executable='/usr/bin/false')
    monkeypatch.setattr(transport, 'binding_from_json', lambda value: binding)
    monkeypatch.setattr(transport, 'validate_binding', lambda *args, **kwargs: None)
    return transport.OfficialProductionModelTransport(binding={},runtime_root=runtime)


def test_us_kr_private_generation_roots_pass_original_repository_guard(tmp_path,monkeypatch):
    home=os_home(monkeypatch,tmp_path/'os-home')
    roots=[]
    for market in ('us','kr'):
        execution='local-'+market+'-2026-11-19-consumer'
        for _ in range(2):
            root=job._local_model_runtime(execution);roots.append(root)
            assert root.is_relative_to(home/'Library/Application Support/ThesisMonitor/private-model-runtime')
            assert root.lstat().st_uid==os.getuid() and stat.S_IMODE(root.stat().st_mode)==0o700
            assert not root.is_symlink() and not any((p/'.git').exists() for p in (root,*root.parents))
            assert original_transport_guard(monkeypatch,root).runtime_root==root.resolve()
    assert len(set(roots))==4


def test_git_ancestor_is_rejected_without_hiding_marker(tmp_path,monkeypatch):
    home=os_home(monkeypatch,tmp_path/'repo-home')
    marker=home/'.git';marker.write_text('gitdir: synthetic-only\n')
    with pytest.raises(ValueError,match='production_model_input_root_inside_repository'):
        job._local_model_runtime('local-us-consumer')
    with pytest.raises(ValueError,match='production_model_input_root_inside_repository'):
        original_transport_guard(monkeypatch,home/'model-runtime')
    assert marker.is_file() and not (home/'Library').exists()


def test_symlink_permissions_and_wrong_owner_are_rejected(tmp_path,monkeypatch):
    for kind in ('symlink','permissions','owner'):
        with monkeypatch.context() as patch:
            home=os_home(patch,tmp_path/kind)
            base=home/'Library/Application Support/ThesisMonitor/private-model-runtime'
            base.parent.mkdir(parents=True)
            if kind=='symlink':
                target=home/'other';target.mkdir(mode=0o700);base.symlink_to(target,target_is_directory=True)
            else:
                base.mkdir(mode=0o755 if kind=='permissions' else 0o700)
                if kind=='permissions':base.chmod(0o755)
            if kind=='owner':
                actual=Path.lstat
                def wrong_owner(path,*args,**kwargs):
                    info=actual(path,*args,**kwargs)
                    return SimpleNamespace(st_mode=info.st_mode,st_uid=os.getuid()+1) if path==base else info
                patch.setattr(Path,'lstat',wrong_owner)
            with pytest.raises(ValueError):job._local_model_runtime('local-us-consumer')
            assert base.is_symlink() or not list(base.iterdir())


def test_runtime_failure_precedes_registration_native_and_configuration(tmp_path,monkeypatch):
    def rejected(execution):raise ValueError('SYNTHETIC_RUNTIME_PREFLIGHT_REJECTED')
    monkeypatch.setattr(job,'_local_model_runtime',rejected)
    # Missing all later configuration fields proves they have not been read.
    with pytest.raises(ValueError,match='SYNTHETIC_RUNTIME_PREFLIGHT_REJECTED'):
        asyncio.run(job._local_registered_cycle(SimpleNamespace(market='us'),tmp_path,'2026-11-19'))
    assert not list(tmp_path.iterdir())


def test_actual_caller_preflight_artifact_roots_and_journal_match(tmp_path,monkeypatch):
    os_home(monkeypatch,tmp_path/'os-home')
    folder=tmp_path/'source-repo';folder.mkdir();(folder/'.git').write_text('synthetic-marker\n')
    def after_preflight():raise RuntimeError('SYNTHETIC_STOP_BEFORE_SOURCE')
    config=SimpleNamespace(market='kr',source_configuration=SimpleNamespace(read=after_preflight))
    with pytest.raises(RuntimeError,match='SYNTHETIC_STOP_BEFORE_SOURCE'):
        asyncio.run(job._local_registered_cycle(config,folder,'2026-11-19'))
    receipt=json.loads((folder/'model-runtime-preflight.json').read_bytes())
    runtime=Path(receipt['runtime_root']);execution=receipt['execution']
    journal=runtime/'invocation-ledger'/execution/'events.jsonl'
    assert receipt['journal_path']==str(journal) and receipt['before_registration_and_financial_HTTP'] is True
    budget=ResearchArtifactBudget(roots={Path(p):role for p,role in receipt['artifact_roots'].items()})
    assert budget.category(folder)=='source' and budget.category(folder/'results')=='result'
    assert budget.category(runtime)==budget.category(journal)=='scratch'
    tree=ast.parse(inspect.getsource(job._local_registered_cycle))
    model=next(n.value for n in ast.walk(tree) if isinstance(n,ast.Assign)
        and any(isinstance(t,ast.Name) and t.id=='model' for t in n.targets))
    assert ast.unparse(next(k.value for k in model.keywords if k.arg=='runtime_root'))=='runtime'
    assert ast.unparse(next(k.value for k in model.keywords if k.arg=='journal_path'))=="runtime / 'invocation-ledger' / execution / 'events.jsonl'"
