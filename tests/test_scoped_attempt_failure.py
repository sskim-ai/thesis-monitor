"""Exercise both real invoke/bounded paths with a strictly local fake transport."""
import json
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

import pytest

from scripts import us14_models as m
from scripts import scoped_attempt_failure as f
from scripts.rev46_kr_models import Rev46Kr8Execution
from scripts.r2b_r5_execution import Execution
from tests.test_us14_models import controller


@pytest.mark.parametrize('market', ['us', 'kr'])
@pytest.mark.parametrize('sequence,count,passed,failure_class', [
    (['transport'] * 3, 3, False, f.TRANSPORT),
    (['schema'] * 3, 3, False, f.TRANSPORT),
    (['malformed'] * 3, 3, False, f.TRANSPORT),
    (['semantic'], 1, False, f.SEMANTIC),
    (['systemic'], 1, False, f.SYSTEMIC),
    (['ok'], 1, True, None),
    (['transport', 'semantic'], 2, False, f.SEMANTIC),
    (['schema', 'ok'], 2, True, None),
])
def test_real_scoped_attempt_boundaries(tmp_path, monkeypatch, market, sequence, count, passed, failure_class):
    obj = controller()
    obj.__class__ = m.Us14Execution if market == 'us' else Rev46Kr8Execution
    obj.gen = 'rev58a-fictional-' + uuid4().hex
    obj.sealed = tmp_path / 'sealed'
    obj.verify = lambda: None
    obj.current_launch_context = lambda: {}
    obj.authorize_launch_context = lambda _: None
    obj.execution_policy = lambda: None
    # Exercise the host path contract without requiring a macOS root on CI.
    monkeypatch.setattr(m, 'Path', lambda value: tmp_path / 'official-runtime'
        if str(value) == '/private/tmp' else Path(value))
    monkeypatch.setattr(m.p, 'binding', lambda: None)
    monkeypatch.setattr(m.p.transport, 'OfficialShadowRequest', lambda binding, request_id, prompt, schema, **kw:
        SimpleNamespace(prompt_sha256=prompt, schema_sha256=schema))
    request_root = tmp_path / 'request'
    schema = dict(type='object', properties={'value': {'type': 'string'}}, required=['value'], additionalProperties=False)
    for name, value in [('provider-wire-schema.json', schema), ('internal-semantic-schema.json', schema)]:
        m.p.write(request_root / name, value)
    (request_root / 'prompt.txt').write_text('Synthetic immutable request, no external calls.')
    seen = []
    def transport(**kw):
        mode = sequence[len(seen)]
        seen.append(mode)
        kw['log'].write_text('')
        Path(str(kw['log']) + '.stderr').write_text('')
        if mode == 'transport':
            raise m.p.transport.OfficialShadowError('TRANSPORT_TIMEOUT')
        kw['output'].write_text('not json' if mode == 'malformed' else json.dumps(
            {'wrong': 'field'} if mode == 'schema' else {'value': mode}))
        return {'status': 'PASS', 'synthetic': True}
    monkeypatch.setattr(m.p.transport, 'invoke_official_shadow', transport)
    def stage(spec, request):
        raw, dest = obj.invoke('pass-a', spec, request)
        # Verify the durable raw receipt exists before entering local semantics.
        receipt = m.p.read(dest / 'raw-response-receipt.json')
        assert receipt['raw_response_sha256'] == m.p.sha(dest / 'raw-output.json')
        if raw['value'] == 'systemic':
            raise m.p.SystemicFailure('synthetic-authority-drift')
        obj.arows['partial'] = True
        Execution.receipt(obj, dest / 'semantic.json', {'status': 'FAIL' if raw['value'] == 'semantic' else 'PASS'})
    obj.pass_a = stage
    spec = dict(market=market, batch=1, subjects=['fictional-subject'])
    if failure_class == f.SYSTEMIC:
        with pytest.raises(m.p.SystemicFailure):
            obj.bounded('pass-a', spec, {'directory': str(request_root)})
    else:
        assert obj.bounded('pass-a', spec, {'directory': str(request_root)}) is passed
    assert len(seen) == count
    row = obj.ledger[0]
    assert row['attempts'] == len(row['attempt_receipts']) == count
    assert bool(obj.arows) == passed
    receipts = row['attempt_receipts']
    assert receipts[-1]['failure_class'] == failure_class
    assert len({r['request_sha256'] for r in receipts}) == 1
    assert len({r['logical_request_id'] for r in receipts}) == 1
    for ordinal, r in enumerate(receipts, 1):
        assert r['attempt'] == ordinal and r['stage'] == 'pass-a' and r['market'] == market
        path = obj.sealed / 'calls/pass-a' / market / 'batch-01' / f'attempt-{ordinal}'
        assert m.p.read(path / 'attempt-receipt.json') == r
        assert r['retry_eligible'] == (r['failure_class'] == f.TRANSPORT)
        if r['failure_class'] == f.SEMANTIC:
            assert r['provider_schema_status'] == 'PASS' and r['local_semantic_status'] == 'FAIL'
            assert m.p.read(path / 'semantic.json')['status'] == 'FAIL'
            assert r['raw_response_sha256'] == m.p.sha(path / 'raw-output.json')


def test_unknown_controller_error_never_gets_transport_retry():
    assert f.classify(RuntimeError('local bug'), {'provider_schema_status': 'PASS'}) == (f.SYSTEMIC, False)
    assert f.classify(m.p.BatchFailure('schema-looking-string'), None) == (f.SYSTEMIC, False)
