"""Source failure classification, separate from genuine local integrity failure."""
import asyncio
from copy import deepcopy
import json

import httpx
import pytest

from app.services.canonical_source_replay import market_inputs, require_captured_phase
from app.services.unified_run_artifacts import durable_json
from tests.test_production_runtime_v2 import DAY, setup
from tests.test_r9_rev11_sealed_dispatch import execute, runner


def capture(tmp_path, phase='us-market'):
    dispatcher = runner(tmp_path)
    calls = []

    def denied(request):
        calls.append(request)
        return httpx.Response(400, json={'error': 'SYNTHETIC_NONTRANSIENT_DENIAL'})

    final = execute(dispatcher, denied)
    root = tmp_path/'source'
    root.mkdir()
    dispatcher.root.rename(root/'dispatch')
    state = dict(status='FAILED', error_class='HTTPStatusError', failure_provenance=dict(
        phase=phase, generation_id=dispatcher.plan.generation_id,
        plan_sha256=dispatcher.plan.plan_sha256, failed_receipts={'fred-1': final['receipt_sha256']}))
    durable_json(root/f'phase-{phase}.json', state, exclusive=True)
    frozen = dict(generation_id=dispatcher.plan.generation_id,
        plan=dispatcher.plan.model_dump(mode='json'), sessions={'us': '2026-09-28'})
    outcome = dict(phases={phase: state}, logical_results={'fred-1': final})
    assert len(calls) == 1 and len(final['attempts']) == 1
    assert final['status'] == 'FAILED' and final['attempts'][0]['status'] == 400
    assert final['attempts'][0]['retry'] is False and final['attempts'][0]['transient'] is False
    return root, frozen, outcome


def test_captured_failure_is_typed_without_fabricating_query(tmp_path):
    root, frozen, outcome = capture(tmp_path)
    with pytest.raises(ValueError, match='SOURCE_PARTIAL:captured_phase_failure:us-market'):
        market_inputs(root, frozen, outcome, None)
    assert not (root/'markets/us-query.json').exists()


def test_failed_mandatory_stock_phase_uses_the_same_boundary(tmp_path):
    root, frozen, outcome = capture(tmp_path, 'stocks')
    with pytest.raises(ValueError, match='captured_phase_failure:stocks'):
        require_captured_phase(root, frozen, outcome, 'stocks')


@pytest.mark.parametrize('status', ['PASS', 'SUCCESS', 'CAPTURED_NOT_QUALIFIED'])
def test_success_with_missing_artifact_is_hard(tmp_path, status):
    with pytest.raises(FileNotFoundError):
        market_inputs(tmp_path, {'sessions': {'us': '2026-09-28'}},
                      {'phases': {'us-market': {'status': status}}}, None)


@pytest.mark.parametrize('fault', ['missing_phase', 'wrong_generation', 'wrong_plan', 'wrong_hash',
    'no_receipts', 'unknown_request', 'phase_mismatch', 'missing_final', 'corrupt_final',
    'raw_corrupt', 'raw_missing', 'attempt_corrupt', 'directory', 'unreadable', 'symlink'])
def test_unproven_or_corrupt_failure_receipt_stays_hard(tmp_path, monkeypatch, fault):
    root, frozen, outcome = capture(tmp_path)
    phase = root/'phase-us-market.json'
    final = root/'dispatch/receipts/fred-1/final.json'
    raw = root/'dispatch/receipts/fred-1/attempt-1.body'
    if fault == 'missing_phase':
        phase.unlink()
    elif fault in {'wrong_generation', 'wrong_plan', 'wrong_hash', 'no_receipts', 'unknown_request'}:
        proof = outcome['phases']['us-market']['failure_provenance']
        if fault == 'wrong_generation':
            proof['generation_id'] = 'different-generation'
        elif fault == 'wrong_plan':
            proof['plan_sha256'] = '0'*64
        elif fault == 'wrong_hash':
            proof['failed_receipts']['fred-1'] = '0'*64
        elif fault == 'no_receipts':
            proof['failed_receipts'] = {}
        else:
            proof['failed_receipts'] = {'unplanned': '0'*64}
        phase.write_text(json.dumps(outcome['phases']['us-market']))
    elif fault == 'phase_mismatch':
        phase.write_text('{}')
    elif fault == 'missing_final':
        final.unlink()
    elif fault == 'corrupt_final':
        final.write_text('{')
    elif fault == 'raw_corrupt':
        raw.write_bytes(b'corrupted')
    elif fault == 'raw_missing':
        raw.unlink()
    elif fault == 'attempt_corrupt':
        (raw.parent/'attempt-1.json').write_text('{}')
    elif fault == 'directory':
        phase.unlink()
        phase.mkdir()
    elif fault == 'unreadable':
        original = type(phase).read_bytes

        def denied(path):
            if path == phase:
                raise PermissionError('synthetic read denied')
            return original(path)

        monkeypatch.setattr(type(phase), 'read_bytes', denied)
    else:
        saved = phase.with_suffix('.saved')
        phase.rename(saved)
        phase.symlink_to(saved)
    with pytest.raises(OSError):
        market_inputs(root, frozen, outcome, None)


@pytest.mark.parametrize('body', [b'{', b'{}', b'{"observed_at":"bad-date"}'])
def test_success_with_corrupt_query_is_hard(tmp_path, body):
    (tmp_path/'markets').mkdir()
    (tmp_path/'markets/us-query.json').write_bytes(body)
    with pytest.raises(OSError, match='market_query_receipt_corrupt'):
        market_inputs(tmp_path, {'sessions': {'us': '2026-09-28'}},
                      {'phases': {'us-market': {'status': 'CAPTURED_NOT_QUALIFIED'}}}, None)


@pytest.mark.parametrize('captured', [True, False])
def test_real_attempt_boundary_only_completes_expected_source_failure(tmp_path, captured):
    root, frozen, outcome = capture(tmp_path)
    if not captured:
        outcome = deepcopy(outcome)
        outcome['phases']['us-market'] = {'status': 'CAPTURED_NOT_QUALIFIED'}
    engine, ports = setup(tmp_path, 'us')

    async def collect(request, directory):
        ports.calls.append(request)
        return market_inputs(root, frozen, outcome, None)

    ports.collect = collect
    result = asyncio.run(engine.run('us', DAY))
    assert result['status'] == 'FAILED' and not ports.stages
    assert len(ports.calls) == (3 if captured else 1)
    for attempt in result['attempts']:
        assert ('completed_at' in attempt) is captured
        if captured:
            assert attempt['status'] == 'INCOMPLETE'
            assert attempt['error_type'] == 'ValueError'
    assert len(ports.notifications) == 1
    assert not (root/'markets/us-query.json').exists()
