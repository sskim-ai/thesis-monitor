from types import SimpleNamespace
import json

import pytest

from scripts import m12ds_r3_transport as t


def setup(monkeypatch, tmp_path, outcomes):
    request_dir = tmp_path / 'request'
    request_dir.mkdir()
    (request_dir / 'prompt.txt').write_text('Frozen fictional prompt')
    schema = {'type': 'object', 'properties': {'value': {'const': 'valid'}}, 'required': ['value'], 'additionalProperties': False}
    for name in ('provider-wire-schema.json', 'internal-semantic-schema.json'):
        t.p.write(request_dir / name, schema)
    context = {'uid': 1, 'gid': 1, 'safe_environment': {}, 'state_access': {'effective_open_readwrite_without_write': True}}
    proof = SimpleNamespace(gen='fictional', report=tmp_path / 'report', sealed=tmp_path / 'sealed',
                            dependencies={}, ledger=[{'attempts': 0}], publish=lambda: None)
    t.p.write(proof.report / 'host-context.json', context)
    proof.preinvoke = lambda *args: None
    monkeypatch.setattr(t, 'RUNTIME_ROOT', tmp_path / 'runtime')
    monkeypatch.setattr(t.launch, 'context_receipt', lambda: context)
    monkeypatch.setattr(t.p, 'binding', lambda: None)
    monkeypatch.setattr(t.p.transport, 'OfficialShadowRequest', lambda binding, ns, prompt, schema:
                        SimpleNamespace(prompt_sha256=prompt, schema_sha256=schema))
    calls = []

    def fake(**kw):
        calls.append({'namespace': kw['state_namespace'], 'prompt': kw['prompt'].read_bytes(),
                      'schema': kw['schema'].read_bytes(), 'timeout': kw['timeout']})
        kw['log'].write_text(json.dumps({'type': 'turn.started'}) + '\n')
        outcome = outcomes[len(calls) - 1]
        if outcome == 'unexpected':
            raise RuntimeError('unexpected')
        if outcome == 'tool':
            kw['log'].write_text(json.dumps({'type': 'item.started', 'item': {'type': 'command_execution'}}))
        if outcome in ('valid', 'invalid', 'tool', 'drift'):
            t.p.write(kw['output'], {'value': 'invalid' if outcome == 'invalid' else 'valid'})
        if outcome == 'drift':
            (request_dir / 'prompt.txt').write_text('changed')
        if outcome in ('TRANSPORT_TIMEOUT', 'PROCESS_NONZERO', 'AUTH_MISSING'):
            raise t.p.transport.OfficialShadowError(outcome)
        return {'status': 'PASS'}

    monkeypatch.setattr(t.p.transport, 'invoke_official_shadow', fake)
    request = {'directory': str(request_dir)}
    spec = {'market': 'fictional', 'batch': 1, 'subjects': []}
    return proof, spec, request, calls


def test_identical_timeout_retry_preserves_both_receipts(monkeypatch, tmp_path):
    proof, spec, request, calls = setup(monkeypatch, tmp_path, ['TRANSPORT_TIMEOUT', 'valid'])
    raw, _ = t.invoke(proof, 'core', spec, request)
    assert raw == {'value': 'valid'}
    assert len(calls) == 2 and calls[0]['namespace'] != calls[1]['namespace']
    assert calls[0]['prompt'] == calls[1]['prompt'] and calls[0]['schema'] == calls[1]['schema']
    assert {c['timeout'] for c in calls} == {1200}
    receipts = proof.ledger[-1]['attempt_receipts']
    assert [r['classification'] for r in receipts] == ['TRANSIENT', 'PASS']
    assert len({r['logical_identity_sha256'] for r in receipts}) == 1


@pytest.mark.parametrize('outcomes,count,error', [
    (['TRANSPORT_TIMEOUT', 'TRANSPORT_TIMEOUT'], 2, t.p.BatchFailure),
    (['invalid'], 1, t.p.BatchFailure),
    (['AUTH_MISSING'], 1, t.p.SystemicFailure),
    (['tool'], 1, t.p.SystemicFailure),
    (['unexpected'], 1, t.p.SystemicFailure),
    (['drift'], 1, t.p.SystemicFailure),
])
def test_failures_never_get_unapproved_retry(monkeypatch, tmp_path, outcomes, count, error):
    proof, spec, request, calls = setup(monkeypatch, tmp_path, outcomes)
    with pytest.raises(error):
        t.invoke(proof, 'core', spec, request)
    assert len(calls) == count


def test_preinvoke_semantic_identity_failure_starts_no_process(monkeypatch, tmp_path):
    proof, spec, request, calls = setup(monkeypatch, tmp_path, [])
    def fail(*args):
        raise t.p.SystemicFailure('CORE_BINDING_DRIFT')
    proof.preinvoke = fail
    with pytest.raises(t.p.SystemicFailure):
        t.invoke(proof, 'pass-b', spec, request)
    assert calls == []


def test_certificate_error_in_event_stream_never_transient(tmp_path):
    path = tmp_path / 'events.jsonl'
    path.write_text(json.dumps({'type': 'error', 'message': 'invalid peer certificate: UnknownIssuer'}))
    assert t.event_security_failure(path)
    assert t.sanitize_events(path)[0] == [{'type': 'error', 'item_type': None}]
