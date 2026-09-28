from types import SimpleNamespace

import pytest

from scripts import r2b_r6_continuation as r6


@pytest.mark.parametrize('stage', ['market', 'core', 'canary', 'repair'])
def test_continuation_cannot_dispatch_upstream_or_extra_stage(stage):
    with pytest.raises(ValueError, match='r6_market_core_dispatch_forbidden'):
        r6.Continuation.invoke(SimpleNamespace(), stage, {}, {})


@pytest.mark.parametrize('fail_stage,fail_batch,expected_a,expected_b', [
    ('pass-a', 2, 2, 0), ('pass-b', 2, 8, 2), ('render', 0, 8, 8)])
def test_fail_stop_no_retry_or_later_stage(tmp_path, fail_stage, fail_batch, expected_a, expected_b):
    proof = SimpleNamespace(root=tmp_path, report=tmp_path/'report', sealed=tmp_path/'sealed',
        gen='fixture', inherited=[], ledger=[], arows={}, brows={},
        limits={'core':{'limit':{}}, 'pass-a':{}, 'pass-b':{}}, verify=lambda:None, publish=lambda:None)
    requests = [dict(market='fictional', batch=i, subjects=['fictional']) for i in range(1, 9)]
    proof.hydrate_a = lambda:requests
    for request in requests:
        request['directory'] = str(tmp_path/f"request-{request['batch']}")
        r6.p.write(tmp_path/f"request-{request['batch']}"/'subject-context.json', {'fictional':{}})
    proof.before_b = lambda:requests

    def bounded(stage, spec, request):
        proof.ledger.append(dict(stage=stage, attempts=1))
        if stage == fail_stage and spec['batch'] == fail_batch:
            raise ValueError('fixture-first-failure')
        if spec['batch'] == 8:
            target = proof.arows if stage == 'pass-a' else proof.brows
            target.update({str(i):{} for i in range(21)})
            proof.limits[stage] = {'limit':{}}

    def render():
        raise ValueError('fixture-render-failure')

    proof.bounded, proof.render = bounded, render
    r6.Continuation.run(proof)
    receipt = r6.p.read(tmp_path/'report/execution-complete.json')
    assert receipt['calls'] == {'market':0, 'core':0, 'pass-a':expected_a, 'pass-b':expected_b}
    assert receipt['messages'] == receipt['retry'] == 0
    assert receipt['cumulative_calls']['market'] == 2
    assert receipt['cumulative_calls']['core'] == 8
    assert len(proof.ledger) == expected_a + expected_b
    with pytest.raises(ValueError, match='one_execution_only'):
        (tmp_path/'report/model-structural-ledger.json').write_text('{}')
        r6.Continuation.run(proof)


def test_bad_upstream_hash_stops_before_extraction(tmp_path, monkeypatch):
    monkeypatch.setattr(r6, 'network_guard', lambda:None)
    archive = tmp_path/'wrong.zip'
    archive.write_bytes(b'not the authorized R5 ZIP')
    root = tmp_path/'execution'
    with pytest.raises(ValueError, match='R2B_R6_UPSTREAM_MARKET_CORE_FREEZE_DRIFT'):
        r6.stage(root, archive)
    assert not root.exists()
