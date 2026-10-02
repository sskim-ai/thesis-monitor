from pathlib import Path

import pytest

from scripts import us14_models as m


def controller():
    obj = object.__new__(m.Us14Execution)
    for key in ('cores', 'arows', 'brows', 'markets', 'entries', 'limits'):
        setattr(obj, key, {})
    obj.ledger = []
    obj.active_batches = None
    obj.publish = lambda: None
    return obj


def test_us14_topology_and_bounded_budget_leave_legacy_unchanged():
    obj = controller()
    assert len(obj.batch_topology()) == 5
    assert sum(len(r['subjects']) for r in obj.batch_topology()) == 14
    assert all(r['market'] == 'us' and '000660' not in r['subjects'] for r in obj.batch_topology())
    assert (obj.TIMEOUT_SECONDS, obj.MAX_RETRIES, obj.MESSAGE_COUNT) == (600, 2, 15)
    assert (m.FreshExecution.TIMEOUT_SECONDS, m.FreshExecution.MAX_RETRIES, m.FreshExecution.MESSAGE_COUNT) == (1200, 0, 24)


@pytest.mark.parametrize('failures,expected', [(0,1),(1,2),(2,3),(3,3)])
def test_only_failed_logical_calls_retry_unchanged_request(failures, expected):
    obj = controller()
    seen = []
    request = {'directory': '/same-frozen'}
    def core(spec, req):
        assert not obj.cores
        seen.append(req)
        obj.ledger[-1]['attempts'] += 1
        obj.cores['IBM'] = 'partial'
        if len(seen) <= failures:
            raise m.p.BatchFailure('SCHEMA_REJECT')
    obj.core = core
    spec = dict(market='us', batch=1, subjects=['IBM'])
    assert obj.bounded('core', spec, request) == (failures < 3)
    assert len(seen) == expected and all(r is request for r in seen)
    assert bool(obj.cores) == (failures < 3)
    with pytest.raises(m.p.BatchFailure, match='already_attempted'):
        obj.bounded('core', spec, request)


def test_prelaunch_failure_and_systemic_failure_never_retry():
    for dispatched in (False, True):
        obj = controller()
        def core(spec, req):
            obj.ledger[-1]['attempts'] += int(dispatched)
            raise m.p.SystemicFailure('frozen_input_changed')
        obj.core = core
        with pytest.raises(m.p.SystemicFailure):
            obj.bounded('core', dict(market='us', batch=1, subjects=['IBM']), {'directory': str(Path('/frozen'))})
        assert obj.ledger[0]['attempts'] == int(dispatched)


@pytest.mark.parametrize('failing_batch', [None, 2])
def test_stage_sweep_continues_independent_batches_without_rerunning_success(tmp_path, failing_batch):
    obj = controller()
    obj.root, obj.report, obj.sealed = tmp_path, tmp_path/'report', tmp_path/'sealed'
    obj.gen = obj.source_gen = 'synthetic-no-network'
    obj.limits = {s: {} for s in m.STAGES}
    obj.verify = lambda: None
    def request(spec):
        return dict(spec, directory='/frozen/'+str(spec['batch']))
    initial = dict(market=[request(dict(market='us', batch=1, subjects=[]))],
        core=[request(r) for r in obj.full_topology()])
    m.p.write(obj.sealed/'initial-requests.json', initial)
    obj.frozen = dict(stage_manifests={}, initial_request_manifest_sha256=m.p.sha(obj.sealed/'initial-requests.json'))
    seen = []
    def stage_call(stage, spec, req):
        obj.ledger[-1]['attempts'] += 1
        seen.append((stage, spec['batch']))
        if stage == 'core' and spec['batch'] == failing_batch:
            raise m.p.BatchFailure('synthetic-semantic-reject')
        target = {'market': obj.markets, 'core': obj.cores, 'pass-a': obj.arows, 'pass-b': obj.brows}[stage]
        target.update({t: {} for t in spec['subjects']} if stage != 'market' else {'us': {}})
    for stage in m.STAGES:
        setattr(obj, stage.replace('-', '_'), lambda spec, req, stage=stage: stage_call(stage, spec, req))
    obj.before_a = obj.before_b = lambda: [request(r) for r in obj.batch_topology()]
    def render():
        (tmp_path/'messages').mkdir()
        for subject in ('MARKET_US', *m.SUBJECTS):
            (tmp_path/'messages'/f'{subject}.txt').write_text('fixture')
    obj.render = render
    obj.run()
    complete = m.p.read(obj.report/'execution-complete.json')
    if failing_batch is None:
        assert complete['terminal'] == obj.SUCCESS_TERMINAL
        assert complete['messages'] == 15 and complete['retry'] == 0
        assert complete['calls'] == obj.CALL_LIMITS
    else:
        assert complete['terminal'] == obj.FAILURE_TERMINAL and complete['messages'] == 0
        assert seen.count(('core', failing_batch)) == 3
        assert ('core', 5) in seen and ('pass-b', 5) in seen
        assert not any((stage, failing_batch) in seen for stage in ('pass-a', 'pass-b'))
        assert complete['calls'] == dict(market=1, core=7, **{'pass-a':4, 'pass-b':4})


def test_rev46_kr_attempt_policy_preserves_kis_owner_and_legacy():
    from scripts.rev46_kr_models import Rev46Kr8Execution
    from scripts.kr8_fy1_models import Kr8Execution
    obj = object.__new__(Rev46Kr8Execution)
    obj.active_batches = None
    assert len(obj.batch_topology()) == 3
    assert sum(len(r['subjects']) for r in obj.batch_topology()) == 8
    assert Rev46Kr8Execution.valuation_context is Kr8Execution.valuation_context
    assert Rev46Kr8Execution.forward_view is Kr8Execution.forward_view
    assert (obj.TIMEOUT_SECONDS, obj.MAX_RETRIES, obj.ATTEMPT_BUDGET) == (600,2,30)
    assert (Kr8Execution.TIMEOUT_SECONDS, Kr8Execution.MAX_RETRIES) == (1200,0)


@pytest.mark.parametrize('market,max_calls', [('us', 16), ('kr', 10)])
def test_scope_policy_uses_actual_freeze_and_rejects_cross_scope(market, max_calls):
    from scripts.rev46_kr_models import Rev46Kr8Execution
    cls = m.Us14Execution if market == 'us' else Rev46Kr8Execution
    obj = object.__new__(cls)
    obj.frozen = dict(timeout_seconds=600, max_calls=max_calls, retries=2)
    assert obj.execution_policy() == m.p.transport.OfficialShadowExecutionPolicy(600, max_calls, 2)
    obj.frozen['max_calls'] = 10 if max_calls == 16 else 16
    with pytest.raises(m.p.BatchFailure, match='scoped_execution_policy_drift'):
        obj.execution_policy()


@pytest.mark.parametrize('market,max_calls', [('us', 16), ('kr', 10)])
def test_launch_identity_contains_frozen_scoped_policy(tmp_path, monkeypatch, market, max_calls):
    from types import SimpleNamespace
    from scripts.rev46_kr_models import Rev46Kr8Execution
    cls = m.Us14Execution if market == 'us' else Rev46Kr8Execution
    obj = object.__new__(cls)
    obj.report, obj.sealed = tmp_path/'report', tmp_path/'sealed'
    obj.source_gen = 'sealed-source-fixture'
    obj.frozen = dict(timeout_seconds=600, max_calls=max_calls, retries=2,
        controller={'head': 'synthetic-head'}, fresh_source_replay={'first_sha256': 'whole-source'},
        source_only_zip_sha256='zip')
    m.p.write(obj.report/'execution-freeze.json', obj.frozen)
    m.p.write(obj.sealed/'initial-requests.json', {'fixture_only': True})
    monkeypatch.setattr(m.p, 'binding', lambda: SimpleNamespace(
        executable_sha256='executable', qualification_sha256='qualification'))
    identity = obj.identity()
    assert identity.execution_policy == obj.execution_policy()
    assert (identity.timeout_seconds, identity.max_calls, identity.retries) == (600, max_calls, 2)
