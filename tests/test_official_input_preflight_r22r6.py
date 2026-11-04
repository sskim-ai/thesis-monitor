import asyncio
import io
import json
from dataclasses import asdict, replace
from pathlib import Path
from types import SimpleNamespace

import pytest

from app.jobs import accepted_decision_v2_runtime as runtime
from app.jobs import production_model_worker as worker
from app.services import official_codex_shadow_transport_service as transport
from app.services.production_model_transport import CONTRACT
from app.services.official_transport_input_preflight import PREFLIGHT_REJECT_EXIT
from test_official_codex_shadow_transport import invocation as invocation


@pytest.mark.parametrize("carrier", ["prompt", "schema"])
def test_actual_runtime_denies_rehashed_fixture_before_binding(invocation, monkeypatch, carrier):
    if carrier == "prompt":
        invocation['prompt'].write_text('prefix\nFROZEN_CONTEXT:\n{"provenance":"TEST_ONLY"}')
    else:
        invocation['schema'].write_text('{"type":"object","provenance":"TEST_ONLY"}')
    invocation['official_shadow'] = replace(invocation['official_shadow'],
        prompt_sha256=transport.file_sha256(invocation['prompt']),
        schema_sha256=transport.file_sha256(invocation['schema']))
    monkeypatch.setattr(transport, 'validate_binding', lambda *a, **k: pytest.fail('binding reached'))
    with pytest.raises(ValueError, match='^production_test_only_fixture_forbidden$'):
        runtime._invoke_signed_in_codex(**invocation)
    assert not invocation['output'].exists()
    assert not invocation['log'].exists()
    assert not invocation['output'].with_suffix('.json.invocation').exists()


@pytest.mark.parametrize("case", ['normal', 'fixture', 'schema-drift', 'duplicate-schema'])
def test_actual_worker_composes_preflight_before_frozen_executor(invocation, monkeypatch, case):
    if case in {'fixture', 'schema-drift'}:
        invocation['prompt'].write_text('prefix\nFROZEN_CONTEXT:\n{"provenance":"TEST_ONLY"}')
    if case == 'duplicate-schema':
        invocation['schema'].write_text('{"type":"object","type":"array"}')
    request = invocation['official_shadow']
    frame = dict(contract=CONTRACT, directory=str(invocation['cwd'].parent),
        binding=json.loads(json.dumps(asdict(request.binding), default=str)),
        request_id=request.request_id, prompt_sha256=transport.file_sha256(invocation['prompt']),
        schema_sha256=transport.file_sha256(invocation['schema']))
    if case == 'schema-drift':
        invocation['schema'].write_bytes(b'changed')
    calls = []
    def executor(**kwargs):
        calls.append(kwargs)
        return {'fixture_only': True}
    monkeypatch.setattr(worker, 'invoke_official_bound', executor)
    monkeypatch.setattr(worker.sys, 'stdin', SimpleNamespace(buffer=io.BytesIO(json.dumps(frame).encode())))
    receipt_path = invocation['cwd'].parent/'transport-receipt.json'
    if case == 'normal':
        worker.main()
        assert json.loads(receipt_path.read_bytes())['status'] == 'PASS'
    else:
        monkeypatch.setattr(worker, 'durable_json', lambda *a, **k: pytest.fail('receipt write reached'))
        assert worker.main() == PREFLIGHT_REJECT_EXIT
        assert not receipt_path.exists()
    assert len(calls) == (1 if case == 'normal' else 0)
    assert not invocation['output'].exists()
    assert not invocation['log'].exists()
    assert not invocation['output'].with_suffix('.json.invocation').exists()


def test_parent_boundary_rejection_is_not_retried_by_actual_bridge(invocation, tmp_path):
    from app.services.production_runtime_bridge import ProductionRuntimeBridgeV1
    from tests.test_production_model_transport import Process, payload, transport as parent_transport

    class Rejected(Process):
        async def communicate(self, data):
            self.frame = json.loads(data)
            return b'', b''

    process = Rejected(returncode=PREFLIGHT_REJECT_EXIT)
    model, calls = parent_transport(invocation, tmp_path, process)
    bridge = SimpleNamespace(model=model, _native_owner_parents={})
    with pytest.raises(ValueError, match='^production_official_transport_boundary_reject$'):
        asyncio.run(ProductionRuntimeBridgeV1._invoke(bridge, None, 'CORE', {'payload': payload('CORE')}, tmp_path/'bridge'))
    assert len(calls) == model.total == 1
    assert (tmp_path/'bridge/attempt-1/intent.json').is_file()
    assert not (tmp_path/'bridge/attempt-2').exists()
    assert not (Path(process.frame['directory'])/'transport-receipt.json').exists()
    assert not (Path(process.frame['directory'])/'raw-output.json').exists()
