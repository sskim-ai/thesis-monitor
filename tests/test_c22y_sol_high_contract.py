"""New profile boundaries only. All CLI/model/installation responses are fixtures."""
import asyncio
from dataclasses import asdict, replace
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from app.services import official_codex_shadow_transport_service as cli
from app.services import production_model_transport as wire
from app.services.official_codex_production_executor import invoke_official_bound
from app.services.official_transport_input_preflight import preflight_official_input
from app.services.production_model_profile import ModelCallSlot, SolHighCallBudget, SolHighWirePolicy
from app.services.production_b2_execution import authorize_b2, execute_b2, parse_authorization, ModelTransportError, SemanticReject
from app.services.production_runtime_bridge import ProductionRuntimeBridgeV1
from app.services.unified_run_artifacts import durable_json
from app.services.unified_snapshot_contract import digest
from app.services.vnext_execution_profile import SOL_HIGH_V1
from tests.test_official_codex_shadow_transport import invocation as original_fixture
from tests.test_production_b2_execution import request_and_auth, body, Transport


@pytest.fixture
def installation(tmp_path, monkeypatch):
    old = original_fixture.__wrapped__(tmp_path, monkeypatch)
    return old, qualify_fixture(old)


def qualify_fixture(old):
    binding = old['official_shadow'].binding
    receipt = json.loads(binding.qualification_path.read_bytes())
    receipt.update(contract=cli.QUALIFICATION_V2, command_prefix=list(cli.command_prefix(SOL_HIGH_V1)),
        execution_profile=SOL_HIGH_V1.model_request(), profile_contract=SOL_HIGH_V1.contract,
        options_review_status='LOCAL_OPTIONS_REVIEWED', model_entitlement='UNKNOWN_UNTIL_APPROVED_CALL')
    path = binding.qualification_path.with_name('sol-high-offline-fixture.json')
    path.write_text(json.dumps(receipt))
    return replace(binding, qualification_path=path, qualification_sha256=cli.file_sha256(path))


def payload(stage):
    context = {'source': 'offline synthetic public evidence'}
    prompt = 'Offline boundary test'
    if stage != 'B2':
        prompt += '\nFROZEN_CONTEXT:\n' + json.dumps(context)
    return dict(prompt=prompt, input=context, response_schema={'type': 'object'})


def fake_cli(command, **kwargs):
    assert command[command.index('-m') + 1] == SOL_HIGH_V1.model
    assert 'model_reasoning_effort="high"' in command
    assert 'model_reasoning_effort="xhigh"' not in command
    assert '--ignore-user-config' in command and '--ignore-rules' in command
    assert 'features.shell_tool=false' in command and 'features.unified_exec=false' in command
    assert kwargs['timeout'] == 600
    Path(command[command.index('-o') + 1]).write_bytes(b'{}')
    kwargs['stdout'].write(b'{"type":"thread.started"}\n{"type":"turn.completed"}\n')
    return SimpleNamespace(returncode=0)


class OfflineWorker:
    returncode = 0
    pid = 123456789

    async def communicate(self, raw):
        self.frame = json.loads(raw)
        request = wire.request_from_frame(self.frame)
        root = Path(self.frame['directory'])
        inputs = root / 'approved-input'
        preflight_official_input(prompt=inputs / 'prompt.txt', schema=inputs / 'provider-wire-schema.json',
            cwd=inputs, request=request)
        proof = invoke_official_bound(codex_bin=str(request.binding.executable), prompt=inputs / 'prompt.txt',
            schema=inputs / 'provider-wire-schema.json', output=root / 'raw-output.json', log=root / 'events.jsonl',
            cwd=inputs, timeout=600, state_namespace=request.request_id, request=request,
            receipt_contract=self.frame['contract'])
        durable_json(root / 'transport-receipt.json', dict(status='PASS', transport=proof), exclusive=True)
        return b'', b''


@pytest.mark.parametrize('stage', ['MARKET', 'CORE', 'A', 'B', 'B2'])
def test_profile_worker_cli_and_receipt_same_identity(installation, tmp_path, monkeypatch, stage):
    _, binding = installation
    calls = []
    monkeypatch.setattr(cli.subprocess, 'run', fake_cli)
    value = payload(stage)
    panel = 'US_MARKET' if stage == 'MARKET' else 'GENERIC_SECURITY'
    budget = SolHighCallBudget([ModelCallSlot(panel, stage, digest(value), 'market' if stage == 'MARKET' else 'stock')])
    process = OfflineWorker()
    async def factory(*args, **kwargs):
        calls.append(args)
        return process
    transport = wire.OfficialProductionModelTransport(binding=json.loads(json.dumps(asdict(binding), default=str)),
        runtime_root=tmp_path / 'transport', worker_factory=factory,
        execution_profile=SOL_HIGH_V1, call_budget=budget)
    transport.bind_cycle(market='us', run_id='offline-current')
    assert asyncio.run(transport.request(value, model=SOL_HIGH_V1.model, effort='high', timeout=600,
        stage=stage, panel=panel)) == b'{}'
    assert len(calls) == len(budget.used) == 1
    assert wire.request_from_frame(process.frame).execution_policy == SolHighWirePolicy()
    transport.bind_cycle(market='us', run_id='offline-another-cycle')
    with pytest.raises(ValueError, match='budget_exhausted'):
        asyncio.run(transport.request(value, model=SOL_HIGH_V1.model, effort='high', timeout=600, stage=stage, panel=panel))
    assert len(calls) == 1


def test_old_qualification_and_wrong_profile_receipts_rejected(installation):
    old, binding = installation
    cli.validate_binding(old['official_shadow'].binding, old['codex_bin'])
    assert cli.command_prefix() == cli.COMMAND_PREFIX
    with pytest.raises(cli.OfficialShadowError, match='PROVENANCE_UNVERIFIED'):
        cli.validate_binding(old['official_shadow'].binding, old['codex_bin'], profile=SOL_HIGH_V1)
    cli.validate_binding(binding, str(binding.executable), profile=SOL_HIGH_V1)
    receipt = json.loads(binding.qualification_path.read_bytes())
    receipt['command_prefix'] = list(cli.COMMAND_PREFIX)
    binding.qualification_path.write_text(json.dumps(receipt))
    binding = replace(binding, qualification_sha256=cli.file_sha256(binding.qualification_path))
    with pytest.raises(cli.OfficialShadowError, match='CONTROL_UNVERIFIED'):
        cli.validate_binding(binding, str(binding.executable), profile=SOL_HIGH_V1)


@pytest.mark.parametrize('failure', ['transport', 'timeout', 'form', 'schema', 'semantic'])
def test_bridge_no_retry_at_every_failure(tmp_path, failure):
    calls = []
    async def request(*args, **kwargs):
        calls.append(kwargs)
        if failure == 'transport':
            raise ModelTransportError('offline')
        if failure == 'timeout':
            raise TimeoutError('offline')
        return b'not json' if failure == 'form' else b'{}'
    def accept(*args):
        raise ValueError('offline semantic rejection')
    bridge = SimpleNamespace(_native_owner_parents={}, execution_profile=SOL_HIGH_V1,
        model=SimpleNamespace(request=request))
    value = payload('CORE')
    if failure == 'schema':
        value['response_schema'] = {'type': 'object', 'required': ['missing']}
    with pytest.raises((ModelTransportError, SemanticReject)):
        asyncio.run(ProductionRuntimeBridgeV1._invoke(bridge, SimpleNamespace(market='us', accept=accept),
            'CORE', dict(payload=value, subjects=['GENERIC_SECURITY']), tmp_path / 'bridge'))
    assert len(calls) == 1 and calls[0]['model'] == SOL_HIGH_V1.model
    assert not (tmp_path / 'bridge/attempt-2').exists()


@pytest.mark.parametrize('error', [ModelTransportError('offline'), TimeoutError(), b'not json', b'{}'])
def test_b2_new_profile_one_attempt_preserves_old_default(tmp_path, error):
    request, legacy, binding = request_and_auth()
    assert legacy.model == 'gpt-5.6-sol' and legacy.transport_form_retries == 2
    auth = authorize_b2(request, **binding, execution_profile=SOL_HIGH_V1)
    assert auth.model == SOL_HIGH_V1.model and auth.effort == 'high' and auth.transport_form_retries == 0
    transport = Transport([error, body(request)])
    with pytest.raises(ModelTransportError):
        asyncio.run(execute_b2(request, auth, current_binding=binding, transport=transport, directory=tmp_path))
    assert len(transport.calls) == 1
    with pytest.raises(ValueError, match='retry_forbidden'):
        authorize_b2(request, **binding, execution_profile=SOL_HIGH_V1, retries=2)


def test_finite_six_plan_per_panel_and_no_relabel():
    slots = [ModelCallSlot(p, s, digest([p, s]), k) for p, stages, k in
             [('US_MARKET', ['MARKET'], 'market'), ('KR_MARKET', ['MARKET'], 'market'),
              ('GENERIC_US', ['BLIND', 'ADJUDICATION'], 'stock'), ('GENERIC_KR', ['BLIND', 'ADJUDICATION'], 'stock')]
             for s in stages]
    budget = SolHighCallBudget(slots)
    for slot in slots:
        budget.consume(slot.panel, slot.stage, slot.payload_sha256)
    assert len(budget.used) == 6
    with pytest.raises(ValueError):
        budget.consume(slots[0].panel, 'MARKET', slots[0].payload_sha256)
    with pytest.raises(ValueError):
        SolHighCallBudget(slots + [ModelCallSlot('OTHER', 'B2', digest('extra'), 'stock')])
    with pytest.raises(ValueError, match='panel_context_limit'):
        SolHighCallBudget([ModelCallSlot('ONE', s, digest(s), 'stock') for s in ('CORE', 'A', 'B')])
    with pytest.raises(ValueError, match='stage_not_authorized'):
        wire.render_prompt(payload('BLIND'), 'BLIND')


def test_worker_policy_drift_and_no_send_pre_model(installation, tmp_path):
    _, binding = installation
    frame = dict(contract=wire.CONTRACT_V2, directory=str(tmp_path), binding={}, request_id='offline',
        prompt_sha256=digest('p'), schema_sha256=digest('s'), execution_policy=asdict(SolHighWirePolicy()),
        authorization_sha256=digest('absent'))
    frame['execution_policy']['retries'] = 2
    with pytest.raises(ValueError, match='policy_drift'):
        wire.request_from_frame(frame)
    bridge = SimpleNamespace(execution_profile=SOL_HIGH_V1)
    with pytest.raises(ValueError, match='no_send'):
        asyncio.run(ProductionRuntimeBridgeV1.stage(bridge, {'stage': 'DELIVER'}, tmp_path))


def test_b2_renderer_profile_parse_and_semantic_owner_unchanged(tmp_path):
    request, legacy, binding = request_and_auth()
    auth = authorize_b2(request, **binding, execution_profile=SOL_HIGH_V1)
    assert parse_authorization(auth.model_dump(mode='json'), execution_profile=SOL_HIGH_V1) == auth
    with pytest.raises(ValueError):
        parse_authorization(auth.model_dump(mode='json'))
    with pytest.raises(ValueError):
        parse_authorization(legacy.model_dump(mode='json'), execution_profile=SOL_HIGH_V1)
    transport = Transport([body(request)])
    result = asyncio.run(execute_b2(request, auth, current_binding=binding, transport=transport, directory=tmp_path))
    assert result['status'] == 'PASS' and len(result['attempts']) == 1
    assert result['authorization_sha256'] == digest(auth.model_dump(mode='json'))


def test_unavailable_diagnostic_no_fallback_or_secret_text():
    from app.services.official_codex_production_executor import _availability_failure
    assert _availability_failure(b'{"error":{"code":"model_not_found","message":"private text"}}') == 'MODEL_ENTITLEMENT_OR_QUOTA_UNAVAILABLE'
    assert _availability_failure(b'not a machine error') == 'PROCESS_NONZERO'
    assert _availability_failure(b'{"error":{"code":[],"type":{}}}') == 'PROCESS_NONZERO'
