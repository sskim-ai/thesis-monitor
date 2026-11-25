"""Test the observed CLI scratch layout without starting Codex or a model."""
import asyncio
from dataclasses import asdict
import json
import os
from pathlib import Path
from types import SimpleNamespace

import pytest

from app.services.codex_runtime_state_service import runtime_state_namespace_hash
from app.services.research_artifact_budget import (
    ArtifactCapacityError, FREE_GUARD, RESULT_CAP, WORK_CAP, ResearchArtifactBudget, artifact_scope,
)
from app.services.unified_run_artifacts import durable_json


@pytest.fixture(autouse=True)
def synthetic_free_space(monkeypatch):
    # Boundary tests must not depend on the test host having 12 GiB available.
    monkeypatch.setattr(os, 'statvfs', lambda path: SimpleNamespace(f_bavail=8 * 1024**2, f_frsize=4096))


def scratch_home(attempt):
    return attempt/'runtime-state'/runtime_state_namespace_hash(attempt.name)/'home'


def arg0(home):
    root = home/'tmp/arg0-macos'
    root.mkdir(parents=True, mode=0o700)
    folder = root/'codex-arg0Ab12Cd'
    folder.mkdir(mode=0o700)
    return folder


@pytest.fixture
def layout(tmp_path):
    runtime = tmp_path/'scratch'
    attempt = runtime/'attempt-one'
    cli = tmp_path/'qualified-cli'
    cli.write_bytes(b'x'*8192)
    cli.chmod(0o700)
    auth = tmp_path/'mock-auth'
    auth.write_text('fixture, not credentials')
    budget = ResearchArtifactBudget(roots={runtime:'scratch',tmp_path/'results':'result',tmp_path/'sources':'source'})
    budget.declare_cli_context(attempt,auth,qualified_cli=cli)
    home = scratch_home(attempt)
    helper = arg0(home)
    (home/'auth.json').symlink_to(auth)
    for name in ('apply_patch','applypatch'):
        (helper/name).symlink_to(cli)
    (helper/'.lock').write_bytes(b'')
    return SimpleNamespace(runtime=runtime,attempt=attempt,cli=cli,auth=auth,home=home,helper=helper,budget=budget)


def test_exact_links_are_counted_without_opening_targets(layout,monkeypatch):
    original = Path.open

    def checked_open(path,*args,**kwargs):
        assert path not in (layout.cli,layout.auth,layout.home/'auth.json',layout.helper/'applypatch',
            layout.helper/'apply_patch')
        return original(path,*args,**kwargs)

    monkeypatch.setattr(Path,'open',checked_open)
    totals = layout.budget.check(path=layout.attempt)
    links = (layout.home/'auth.json',layout.helper/'applypatch',layout.helper/'apply_patch')
    assert totals['scratch']==sum(p.lstat().st_size for p in links)
    assert totals['unique_files']==4 and totals['result']==0
    assert (layout.budget.result_cap,layout.budget.work_cap,layout.budget.free_guard)==(RESULT_CAP,WORK_CAP,FREE_GUARD)
    with pytest.raises(ArtifactCapacityError,match='RESEARCH_RESULT_CAP'):
        layout.budget.check(path=layout.attempt,added_result=RESULT_CAP+1)
    with pytest.raises(ArtifactCapacityError,match='RESEARCH_WORK_CAP'):
        layout.budget.check(path=layout.attempt,added_work=WORK_CAP)
    monkeypatch.setattr(os,'statvfs',lambda path:SimpleNamespace(f_bavail=0,f_frsize=4096))
    with pytest.raises(ArtifactCapacityError,match='RESEARCH_FREE_SPACE_GUARD'):
        layout.budget.check(path=layout.attempt)


@pytest.mark.parametrize('change',[
    'wrong-target','directory-target','unknown-name','wrong-namespace','duplicate-temp','symlink-parent',
    'source','result','auth-target','public-temp',
])
def test_unregistered_or_tampered_links_still_stop(layout,tmp_path,change):
    if change in {'wrong-target','directory-target'}:
        link = layout.helper/'applypatch'
        link.unlink()
        link.symlink_to(layout.auth if change=='wrong-target' else tmp_path)
    elif change=='unknown-name':
        (layout.helper/'other').symlink_to(layout.cli)
    elif change=='wrong-namespace':
        (arg0(layout.attempt/'runtime-state'/'not-this-invocation'/'home')/'applypatch').symlink_to(layout.cli)
    elif change=='duplicate-temp':
        second = layout.helper.with_name('codex-arg0Zy98Xw')
        second.mkdir(mode=0o700)
        (second/'apply_patch').symlink_to(layout.cli)
    elif change=='symlink-parent':
        (layout.helper.with_name('codex-arg0Zy98Xw')).symlink_to(layout.helper,target_is_directory=True)
    elif change=='auth-target':
        link = layout.home/'auth.json'
        link.unlink()
        link.symlink_to(layout.cli)
    elif change=='public-temp':
        layout.helper.chmod(0o755)
    else:
        folder = tmp_path/(change+'s')
        folder.mkdir()
        (folder/'applypatch').symlink_to(layout.cli)
    with pytest.raises(ValueError,match='research_artifact_unexpected_symlink'):
        layout.budget.measure()


@pytest.mark.parametrize('unexpected',[False,True])
def test_transport_midflight_scan_and_receipt_without_real_cli(tmp_path,monkeypatch,unexpected):
    from app.services import codex_runtime_binding as binding_service
    from app.services import production_model_transport as wire
    from app.services.official_codex_shadow_transport_service import command_prefix
    from app.services.production_model_profile import ModelCallSlot, SolHighCallBudget
    from app.services.unified_snapshot_contract import digest
    from app.services.vnext_execution_profile import SOL_HIGH_V1

    cli = tmp_path/'offline-cli'
    cli.write_text('not executed')
    cli.chmod(0o700)
    auth = tmp_path/'offline-auth'
    auth.touch()
    binding = binding_service.CurrentOfficialCodexBinding(executable=cli,executable_sha256=digest('fixture'),
        version='fixture',auth_method='fixture',home=str(tmp_path),codex_home=None,user_config_sha256=None,
        auth_source=str(auth))
    monkeypatch.setattr(wire,'validate_binding',lambda *a,**k:None)
    monkeypatch.setattr(binding_service,'parent_environment',lambda b,base:base)
    monkeypatch.setattr(wire,'sys',SimpleNamespace(platform='darwin',executable=wire.sys.executable))
    runtime = tmp_path/'scratch'
    artifacts = ResearchArtifactBudget(roots={runtime:'scratch'})
    payload = dict(prompt='Offline fixture only\nFROZEN_CONTEXT:\n{}\n',input={},
        response_schema={'type':'object'})
    budget = SolHighCallBudget([ModelCallSlot('TEST_KR','CORE',digest(payload),'stock')])
    started, scanned = [], []
    scan_finished = None

    class Worker:
        returncode = None
        pid = 99

        async def communicate(self,raw):
            frame = json.loads(raw)
            attempt = Path(frame['directory'])
            home = scratch_home(attempt)
            helper = arg0(home)
            (home/'auth.json').symlink_to(auth)
            for name in ('applypatch','apply_patch'):
                (helper/name).symlink_to(cli)
            if unexpected:
                (helper/'unknown').symlink_to(cli)
            await scan_finished.wait()
            out = attempt/'raw-output.json'
            out.write_bytes(b'{}')
            inputs = attempt/'approved-input'
            proof = dict(command=[str(cli),*command_prefix(SOL_HIGH_V1),'--output-schema',
                str(inputs/'provider-wire-schema.json'),'-o',str(out),'-'],
                qualification_sha256=None,**{k:frame[k] for k in ('execution_policy','request_id','prompt_sha256','schema_sha256')})
            durable_json(attempt/'transport-receipt.json',dict(status='PASS',transport=proof),exclusive=True)
            self.returncode = 0

        async def wait(self):
            self.returncode = -9
            return self.returncode

    async def factory(*args,**kwargs):
        started.append(1)
        return Worker()

    check = artifacts.check

    def observe(**kwargs):
        value = check(**kwargs)
        if started:
            scanned.append(1)
            scan_finished.set()
        return value

    wait = asyncio.wait
    monkeypatch.setattr(artifacts,'check',observe)
    monkeypatch.setattr(wire.asyncio,'wait',lambda tasks,timeout:wait(tasks,timeout=0.01))
    monkeypatch.setattr(wire.os,'killpg',lambda pid,signal:None)
    transport = wire.OfficialProductionModelTransport(binding=json.loads(json.dumps(asdict(binding),default=str)),
        runtime_root=runtime,worker_factory=factory,execution_profile=SOL_HIGH_V1,call_budget=budget)
    transport.bind_cycle(market='kr',run_id='offline')

    async def invoke():
        nonlocal scan_finished
        scan_finished = asyncio.Event()
        return await transport.request(payload,model=SOL_HIGH_V1.model,effort='high',timeout=600,stage='CORE',panel='TEST_KR')

    with artifact_scope(artifacts):
        if unexpected:
            with pytest.raises(ValueError,match='research_artifact_unexpected_symlink'):
                asyncio.run(invoke())
            assert not list(runtime.glob('*/raw-output.json'))
        else:
            assert asyncio.run(invoke())==b'{}'
            assert scanned and len(list(runtime.glob('*/parent-exit.json')))==1
    assert started==[1] and len(budget.used)==1 and transport.total==1
