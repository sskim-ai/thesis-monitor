from dataclasses import replace

import pytest

from app.jobs import accepted_decision_v2_runtime as runtime
from app.services import official_codex_shadow_transport_service as transport
from test_official_codex_shadow_transport import invocation as invocation


@pytest.mark.parametrize("body", [b'changed', b'{"type":"object"}tail', b'{"type":"object","type":"array"}'])
def test_bound_malformed_schema_uses_typed_error_without_effects(invocation, monkeypatch, body):
    invocation['schema'].write_bytes(body)
    invocation['official_shadow'] = replace(invocation['official_shadow'], schema_sha256=transport.file_sha256(invocation['schema']))
    monkeypatch.setattr(transport.subprocess, 'run', lambda *a, **k: pytest.fail('unexpected spawn'))
    with pytest.raises(transport.OfficialShadowError, match='^INPUT_ENCODING_OR_SCHEMA_INVALID$') as caught:
        runtime._invoke_signed_in_codex(**invocation)
    assert caught.value.process_started is False
    assert not invocation['output'].exists()
    assert not invocation['log'].exists()
    assert not invocation['output'].with_name(invocation['output'].name + '.invocation').exists()


@pytest.mark.parametrize(('body', 'error'), [
    ('prefix\nFROZEN_CONTEXT:\n{"x":1,"x":2}', 'production_frozen_context_duplicate_key'),
    ('prefix\nFROZEN_CONTEXT:\n{}tail', 'production_frozen_context_json_invalid'),
    ('prefix\nFROZEN_CONTEXT:\n{"ticker":"FIC-FIN-01"}', 'production_test_only_fixture_forbidden'),
    ('prefix\nFROZEN_CONTEXT:\n{"provenance":"TEST_ONLY"}', 'production_test_only_fixture_forbidden'),
])
def test_official_bound_prompt_rejection_precedes_claim_and_spawn(invocation, monkeypatch, body, error):
    invocation['prompt'].write_text(body)
    invocation['official_shadow'] = replace(invocation['official_shadow'], prompt_sha256=transport.file_sha256(invocation['prompt']))
    monkeypatch.setattr(transport.subprocess, 'run', lambda *a, **k: pytest.fail('unexpected spawn'))
    with pytest.raises(ValueError, match=error):
        runtime._invoke_signed_in_codex(**invocation)
    assert not invocation['output'].exists()
    assert not invocation['log'].exists()
    assert not invocation['output'].with_name(invocation['output'].name + '.invocation').exists()


def test_schema_drift_precedes_fixture_prompt_inspection(invocation, monkeypatch):
    invocation['prompt'].write_text('prefix\nFROZEN_CONTEXT:\n{"provenance":"TEST_ONLY"}')
    invocation['official_shadow'] = replace(invocation['official_shadow'], prompt_sha256=transport.file_sha256(invocation['prompt']))
    invocation['schema'].write_bytes(b'changed')
    monkeypatch.setattr(transport.subprocess, 'run', lambda *a, **k: pytest.fail('unexpected spawn'))
    with pytest.raises(transport.OfficialShadowError, match='^SCHEMA_DRIFT$'):
        runtime._invoke_signed_in_codex(**invocation)
    assert not invocation['output'].exists()
    assert not invocation['log'].exists()
