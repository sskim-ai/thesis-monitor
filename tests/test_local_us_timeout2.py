"""Synthetic cap2 wiring; retained S/R diagnosis is separate from live admission."""
import ast
from collections import Counter
import json
from pathlib import Path

import pytest

from app.jobs import unified_market_snapshot as job
from app.services.model_invocation_journal import ModelInvocationJournal, read_invocation_journal
from app.services.unified_snapshot_contract import digest
from tests import test_c22bf_timeout as old
from tests import test_v8_mixed_retry as mixed


@pytest.fixture(autouse=True)
def no_live(monkeypatch):
    mixed.deny_live.__wrapped__(monkeypatch)


def scenario(tmp_path, monkeypatch, timeouts):
    transport = old.transport
    def injected(folder, patch, budget, runtime, outcomes, recorded):
        ordinary = [s.subjects[0] for s in budget.plan.slots if s.stage == 'B2']
        stream = []
        for i, value in enumerate(outcomes):
            subject = ordinary[i-16] if i >= 16 else 'MARKET' if i == 0 else None
            stream.extend(['timeout'] * timeouts.get(subject, 0))
            if timeouts.get(subject) != 2:
                stream.append(value)
        return transport(folder, patch, budget, runtime, iter(stream), recorded)
    monkeypatch.setattr(old, 'transport', injected)
    return mixed.fixture_run(tmp_path, monkeypatch, cap=2)


def test_two_distinct_b2_timeouts_keep_29_acceptances_and_15_messages(tmp_path, monkeypatch):
    f = scenario(tmp_path, monkeypatch, {'CPNG': 1, 'TSM': 1})
    assert f.result['status'] == 'RENDER_VERIFIED_NO_SEND', f.result.get('error_chain')
    assert len(f.plan.slots) == len(f.budget.accepted) == 29
    assert len(f.calls) == f.budget.physical_calls == f.budget.run_ledger.state()['model_total'] == 31
    assert f.budget.maximum == 31 and f.budget.retry_used == 2
    assert len(f.result['messages']) == 15 and all(m['NO_SEND'] for m in f.result['messages'])
    limited = next(m for m in f.result['messages'] if m['message_id'] == 'SKHY')
    assert limited['decision_mode'] == 'UNKNOWN_LIMIT'
    b2 = [c for c in f.calls if c['slot_scope']['stage'] == 'B2']
    counts = Counter(c['slot_scope']['subjects'][0] for c in b2)
    assert counts['CPNG'] == counts['TSM'] == 2 and 'SKHY' not in counts
    for ticker in ('CPNG', 'TSM'):
        pair = [c for c in b2 if c['slot_scope']['subjects'] == [ticker]]
        assert pair[0]['request_id'] != pair[1]['request_id']
        assert all(pair[0][k] == pair[1][k] for k in ('slot_scope', 'prompt_sha256', 'schema_sha256'))
        assert [c['attempt']['ordinal'] for c in pair] == [1, 2]
    journal = read_invocation_journal(f.budget.journal.path.read_bytes())
    assert journal['physical_calls'] == 31 and journal['retry_used'] == 2
    b2_receipt = next(r for r in f.result['stage_receipts'] if r['stage'] == 'B2')
    assert b2_receipt['deadline']['campaign_timeout_retry_cap'] == 2
    assert b2_receipt['timing']['worker_windows'] == 15
    assert all(r['status'] == 'PASS' for r in f.result['stage_receipts'])


def test_third_distinct_timeout_cannot_spend_a_third_shared_retry(tmp_path, monkeypatch):
    f = scenario(tmp_path, monkeypatch, {'CPNG': 1, 'TSM': 1, 'WULF': 1})
    assert f.result['status'] == 'FAILED_NO_SEND' and 'messages' not in f.result
    assert len(f.calls) == f.budget.physical_calls == 31 and f.budget.retry_used == 2
    b2 = json.loads((f.cycle/'b2/response.json').read_bytes())['output']
    assert list(b2['unissued']) == ['WULF']
    assert b2['unissued']['WULF']['attempts'] == 1
    assert not (f.cycle/'render/response.json').exists()
    assert sum(c['slot_scope']['subjects'] == ['WULF'] for c in f.calls) == 1


def test_same_slot_never_gets_attempt_three_with_remaining_shared_credit(tmp_path):
    path = tmp_path/'journal.jsonl'
    journal = ModelInvocationJournal(path, plan_sha256=digest('synthetic'), maximum=3, retry_cap=2)
    journal.transact('BIND', slot_id='one', scope=dict(slot_id='one', dependency_outputs={}, stage='B2'))
    for i in (1, 2):
        attempt = old.attempt(i, i)
        journal.transact('CONSUME' if i == 1 else 'RETRY_ATTEMPT', slot_id='one', attempt=attempt)
        journal.transact('TIMEOUT_CONFIRMED', slot_id='one', proof=old.proof(attempt))
    before = path.read_bytes()
    with pytest.raises(ValueError):
        journal.transact('RETRY_ATTEMPT', slot_id='one', attempt=old.attempt(3, 3))
    assert path.read_bytes() == before
    state = read_invocation_journal(before)
    assert state['physical_calls'] == 2 and state['retry_used'] == 1


def test_fresh_non_b2_timeout_does_not_retry(tmp_path, monkeypatch):
    f = scenario(tmp_path, monkeypatch, {'MARKET': 1})
    assert f.result['status'] == 'FAILED_NO_SEND' and 'messages' not in f.result
    assert len(f.calls) == f.budget.physical_calls == 1 and f.budget.retry_used == 0
    assert f.calls[0]['slot_scope']['stage'] == 'MARKET'


def test_actual_caller_ledger_model_and_intent_caps_preserve_kr():
    tree = ast.parse(Path(job.__file__).read_text())
    cycle = next(n for n in tree.body if isinstance(n, ast.AsyncFunctionDef) and n.name == '_local_registered_cycle')
    calls = [n for n in ast.walk(cycle) if isinstance(n, ast.Call)]
    ledger = next(n for n in calls if isinstance(n.func, ast.Name) and n.func.id == 'SelectedRunLedger')
    model = next(n for n in calls if isinstance(n.func, ast.Name) and n.func.id == 'dict'
        and any(k.arg == 'approved_max_invocations' for k in n.keywords))
    scheduled = next(n for n in tree.body if isinstance(n, ast.AsyncFunctionDef) and n.name == 'run_local_scheduled')
    intent = next(n for n in ast.walk(scheduled) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
        and n.func.id == 'dict' and any(k.arg == 'max_models' for k in n.keywords))
    def value(call, key, market):
        node = next(k.value for k in call.keywords if k.arg == key)
        return eval(compile(ast.Expression(node), '<literal-cap>', 'eval'), {'market': market})
    for market, maximum, retry in (('us', 31, 2), ('kr', 18, 0)):
        assert value(ledger, 'max_models', market) == value(intent, 'max_models', market) == maximum
        assert value(ledger, 'timeout_retry_cap', market) == value(model, 'timeout_retry_cap', market) == retry
        assert value(intent, 'timeout_retry_cap', market) == retry
    assert ast.unparse(next(k.value for k in model.keywords if k.arg == 'approved_max_invocations')) == "ledger.identity['max_models']"
    assert sum(job.LOCAL_CAPS['us'].values()) == 710 and sum(job.LOCAL_CAPS['kr'].values()) == 332
    assert value(ledger, 'wallclock_seconds_max', 'us') == 16200


def test_invalid_target_daily_row_cannot_create_a_dated_sr_reference(monkeypatch):
    from app.services import us_dated_source_sr as sr
    from tests.test_pr52_v11_us_sr_reference import data
    args, calls, _ = data.__wrapped__(monkeypatch)
    args.update(cutoff='2026-11-19', observed_at='2026-11-20T13:00:00+09:00')
    args['periods']['daily'][0]['date'] = '2026-11-18'
    args['periods']['daily'][-1].update(date='2026-11-19', close=80)
    for receipt in args['receipts'].values():
        receipt['entry']['latest_completed_session'] = args['cutoff']
    before = digest(args)
    assert sr.attach({}, **args) == {} and not calls
    assert digest(args) == before
    assert args['periods']['daily'][-1]['date'] == '2026-11-19'
