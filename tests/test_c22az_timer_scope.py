"""Production timer boundaries with no database, network or model subprocess."""
import asyncio
from types import SimpleNamespace

import pytest

from app.services import research_no_send_run as research
from app.services.official_codex_shadow_transport_service import classify_input_events
from app.services.production_model_transport import OfficialProductionModelTransport
from app.services.vnext_execution_profile import SOL_HIGH_V1


@pytest.mark.parametrize(('local', 'worker', 'campaign', 'error'), [
    (216.9, 550, 16200, None),
    (600.1, 0, 16200, 'research_local_deadline'),
    (216.9, 0, 216.9, 'research_campaign_deadline'),
    (216.9, 550, 700, 'research_campaign_deadline'),
])
def test_production_scope_uses_distinct_bounded_clocks(local, worker, campaign, error):
    async def exercise():
        clock = [0.0]
        timer = research._StageTimer(dict(local_seconds=600, per_call_seconds=600,
            overhead_seconds=30, planned_calls=1), SimpleNamespace(time=lambda: clock[0]), campaign)
        # Use the real asyncio deadline mechanism; the large relative time is
        # virtual, and no suspension or subprocess is needed for these checks.
        loop_time = asyncio.get_running_loop().time()
        timer.campaign_end += loop_time
        clock[0] = timer.began = loop_time
        async with timer.timeout:
            timer.timeout.reschedule(min(clock[0]+600,timer.campaign_end))
            clock[0] += local
            timer.switch('worker')
            assert timer.timeout.when() == min(clock[0]+630,timer.campaign_end)
            clock[0] += worker
            timer.switch('local')
            assert timer.receipt()['local_seconds'] == local
            assert timer.receipt()['worker_seconds'] == worker
            assert timer.receipt()['worker_windows'] == 1
            assert timer.timeout.when() == min(clock[0]+600-local,timer.campaign_end)

    if error:
        with pytest.raises(TimeoutError, match=error):
            asyncio.run(exercise())
    else:
        asyncio.run(exercise())


def test_cli_limit_and_incomplete_events_are_not_acceptance(tmp_path, monkeypatch):
    import hashlib
    import subprocess

    from app.services import official_codex_production_executor as cli
    from app.services.official_codex_shadow_transport_service import OfficialShadowError
    from app.services.production_model_profile import SolHighWirePolicy

    cwd = tmp_path/'approved-input'
    cwd.mkdir()
    prompt, schema = cwd/'prompt.txt', cwd/'provider-wire-schema.json'
    prompt.write_bytes(b'Dated public fixture')
    schema.write_bytes(b'{}')
    request = SimpleNamespace(binding=SimpleNamespace(qualification_sha256='fixture', executable_sha256='fixture'),
        execution_policy=SolHighWirePolicy(), request_id='offline', model_plan_scope=None,
        prompt_sha256=hashlib.sha256(prompt.read_bytes()).hexdigest(),
        schema_sha256=hashlib.sha256(schema.read_bytes()).hexdigest())
    monkeypatch.setattr(cli, 'validate_binding', lambda *a, **k: None)
    monkeypatch.setattr(cli, 'invocation_environment', lambda *a, **k: None)
    calls = []

    def fake_cli(command, *, timeout, stdout, **kwargs):
        calls.append(timeout)
        stdout.write(b'{"type":"thread.started"}\n{"type":"turn.started"}\n')
        raise subprocess.TimeoutExpired(command, 600.1)

    monkeypatch.setattr(cli.subprocess, 'run', fake_cli)
    log, output = tmp_path/'events.jsonl', tmp_path/'raw-output.json'
    with pytest.raises(OfficialShadowError, match='TRANSPORT_TIMEOUT') as failed:
        cli.invoke_official_bound(codex_bin='not-executed', prompt=prompt, output=output, log=log,
            schema=schema, cwd=cwd, timeout=SOL_HIGH_V1.timeout_seconds,
            state_namespace='offline', request=request, receipt_contract='offline')
    assert failed.value.process_started and calls == [600] and not output.exists()
    assert classify_input_events(log.read_bytes())['state'] == 'INPUT_BOUNDARY_UNVERIFIED'


def test_split_transport_cancellation_kills_and_reaps_worker(tmp_path, monkeypatch):
    import json
    from app.services import production_model_transport as wire
    from app.services.research_artifact_budget import artifact_scope

    killed, consumed = [], []
    monkeypatch.setattr(wire, 'validate_binding', lambda *a, **k: None)
    monkeypatch.setattr(wire.os, 'killpg', lambda pid, sig: killed.append(pid))

    async def exercise():
        started = asyncio.Event()
        path = None

        class Worker:
            pid, returncode = 123, None

            async def communicate(self, frame):
                nonlocal path
                path = json.loads(frame)['directory']
                assert research.current_stage_timer().phase == 'worker'
                started.set()
                await asyncio.Future()

            async def wait(self):
                self.returncode = -9

        async def factory(*args, **kwargs):
            return Worker()

        model = object.__new__(OfficialProductionModelTransport)
        model.execution_profile, model.worker_factory = SOL_HIGH_V1, factory
        model.call_budget = SimpleNamespace(plan=None, maximum=1,
            consume=lambda *a, **k: consumed.append(1) or 1,
            run_ledger=SimpleNamespace(worker_binding=lambda: None))
        model.binding, model.binding_json = SimpleNamespace(executable='offline'), {}
        model.runtime_root, model.cycle, model.counts, model.total, model.secrets = tmp_path, ('us','offline'), {}, 0, ()
        loop = asyncio.get_running_loop()
        timer = research._StageTimer(dict(local_seconds=600, per_call_seconds=600,
            overhead_seconds=30, planned_calls=1), loop, loop.time()+16200)

        async def invoke():
            token = research._stage_timer.set(timer)
            try:
                async with timer.timeout:
                    timer.timeout.reschedule(loop.time()+600)
                    await model.request(dict(prompt='Public fixture\nFROZEN_CONTEXT:\n{}', input={},
                        response_schema={'type':'object'}),
                        model=SOL_HIGH_V1.model, effort='high', timeout=600, stage='MARKET', panel='US_MARKET')
            finally:
                research._stage_timer.reset(token)

        with artifact_scope(None):
            task = asyncio.create_task(invoke())
            await started.wait()
            task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await task
        assert consumed == [1] and killed == [123]
        with open(path+'/parent-exit.json') as handle:
            assert json.load(handle) == {'status':'INTERRUPTED', 'child_reaped':True}
        assert research.current_stage_timer() is None

    asyncio.run(exercise())
