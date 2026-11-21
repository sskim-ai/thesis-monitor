"""C32's six changed boundaries only; synthetic Source and workers, no live I/O."""
import asyncio
from dataclasses import replace
from datetime import datetime
import json
import socket
import sqlite3

import pytest

from app.services import model_timeout_retry as timeout
from app.services.model_execution_plan import compile_model_plan
from app.services.model_invocation_journal import ModelInvocationJournal, read_invocation_journal
from app.services.unified_snapshot_contract import digest
from app.services.unified_stock_acquisition import UNIVERSE
from tests import test_c22bf_timeout as old, test_per_ticker_b2_kis_session as full


@pytest.fixture(autouse=True)
def no_live(monkeypatch):
    def denied(*args, **kwargs):
        raise AssertionError('C32 offline test attempted live I/O')
    for owner, name in ((socket.socket,'connect'), (socket.socket,'connect_ex'),
                        (socket.socket,'sendto'), (sqlite3,'connect'), (asyncio,'create_subprocess_exec')):
        monkeypatch.setattr(owner,name,denied)


def market_calls(f):
    return [c for c in f.calls if c['stage'] == 'MARKET']


def test_first_success_one_market_acceptance_no_retry(tmp_path, monkeypatch):
    f = full.scenario(tmp_path,monkeypatch,{})
    assert f.result['status'] == 'RENDER_VERIFIED_NO_SEND' and len(f.result['messages']) == 15
    assert len(market_calls(f)) == 1 and f.budget.physical_calls == 29 and f.budget.retry_used == 0
    slot = next(s.slot_id for s in f.plan.slots if s.stage == 'MARKET')
    assert slot in f.budget.accepted and f.budget.run_ledger.state()['http_total'] == 0
    before = f.budget.journal.path.read_bytes()
    with pytest.raises(ValueError):
        f.budget.record_acceptance(slot,payload_sha256=f.budget.bound[slot]['payload_sha256'],output_sha256=digest('again'))
    assert f.budget.journal.path.read_bytes() == before


def test_market_timeout_then_success_shared_b2_ledger_timer_and_partition(tmp_path, monkeypatch):
    f = full.scenario(tmp_path,monkeypatch,{'MARKET':['timeout'],'CPNG':['timeout']})
    assert f.result['status'] == 'RENDER_VERIFIED_NO_SEND' and len(f.result['messages']) == 15
    pair = market_calls(f)
    assert len(pair) == 2 and pair[0]['request_id'] != pair[1]['request_id']
    assert all(pair[0][k] == pair[1][k] for k in ('slot_scope','prompt_sha256','schema_sha256','model','effort','timeout'))
    assert all(c['execution_policy']['max_calls'] == 1 and c['execution_policy']['retries'] == 0 for c in pair)
    assert f.budget.physical_calls == f.budget.run_ledger.state()['model_total'] == len(f.calls) == 31
    assert f.budget.retry_used == 2 and len(f.budget.accepted) == 29
    stage = f.result['stage_receipts'][0]
    assert stage['deadline']['market_timeout_retry_cap'] == 1 and stage['timing']['worker_windows'] == 2
    assert stage['deadline']['local_seconds'] == 600 and stage['deadline']['per_call_seconds'] == 600
    journal = read_invocation_journal(f.budget.journal.path.read_bytes())
    proof = journal['timeouts'][pair[0]['slot_scope']['slot_id']][0]
    assert proof['worker_group_reaped'] and proof['remote_completion_and_billing'] == 'UNOBSERVED'
    assert f.budget.run_ledger.state()['http_total'] == 0
    cold = timeout.read_no_send_partition(f.cycle,plan=f.plan,invocation_journal=f.budget.journal.path)
    assert cold['count'] == 15 and cold['physical_attempts'] == 31 and cold['timeout_retries'] == 2
    assert next(m for m in f.result['messages'] if m['message_id']=='SKHY')['decision_mode'] == 'UNKNOWN_LIMIT'


def test_two_market_timeouts_exactly_two_no_send_stop(tmp_path, monkeypatch):
    f = full.scenario(tmp_path,monkeypatch,{'MARKET':['timeout','timeout']})
    assert f.result['status'] == 'FAILED_NO_SEND' and 'messages' not in f.result
    assert len(f.calls) == f.budget.physical_calls == f.budget.run_ledger.state()['model_total'] == 2
    assert f.budget.stopped and not f.budget.accepted and f.budget.retry_used == 1
    journal = read_invocation_journal(f.budget.journal.path.read_bytes())
    assert len(next(iter(journal['timeouts'].values()))) == 2
    assert f.budget.run_ledger.state()['state'] == 'STOPPED_NO_SEND'
    assert not (f.cycle/'render/response.json').exists()


def test_non_timeout_ambiguous_late_and_unreaped_never_retry(tmp_path, monkeypatch):
    worker = old.FixtureWorker
    for kind in ('auth','ambiguous','late','unreaped','nonzero','malformed'):
        with monkeypatch.context() as patch:
            class RejectedWorker(worker):
                async def communicate(self, raw):
                    result = await super().communicate(raw)
                    directory = __import__('pathlib').Path(json.loads(raw)['directory'])
                    if kind == 'late':
                        (directory/'raw-output.json').write_bytes(b'{}')
                    elif kind == 'unreaped':
                        patch.setattr(timeout.os,'killpg',lambda *args:None)
                    elif kind == 'nonzero':
                        self.returncode = 1
                    elif kind == 'malformed':
                        (directory/'transport-receipt.json').write_text(json.dumps(dict(status='FAIL',error_code='FINAL_OUTPUT_MALFORMED')))
                    return result
            patch.setattr(old,'FixtureWorker',RejectedWorker)
            f = full.scenario(tmp_path/kind,patch,{'MARKET':[kind if kind in ('auth','ambiguous') else 'timeout']})
            assert f.result['status'] == 'FAILED_NO_SEND' and len(f.calls) == 1, kind
            assert f.budget.retry_used == 0 and not f.budget.accepted, kind


def test_expired_source_lease_or_budget_stops_before_second_worker(tmp_path, monkeypatch):
    worker = old.FixtureWorker
    for kind in ('source','lease','deadline','budget'):
        with monkeypatch.context() as patch:
            captured = {}
            admitted = full.admitted
            def capture(*args):
                budget,runtime = admitted(*args)
                captured['budget'] = budget
                return budget,runtime
            patch.setattr(full,'admitted',capture)
            class ExpiredWorker(worker):
                async def communicate(self, raw):
                    result = await super().communicate(raw)
                    budget = captured['budget']
                    def expired(*args, **kwargs):
                        raise ValueError('SYNTHETIC_'+kind+'_EXPIRED')
                    if kind == 'source':
                        patch.setattr(type(budget.plan.cohort),'verify_source_owner',expired)
                    elif kind == 'lease':
                        patch.setattr(budget.run_ledger,'worker_binding',expired)
                    elif kind == 'deadline':
                        patch.setattr(budget.run_ledger,'_external',expired)
                    else:
                        budget.maximum = 1
                    return result
            patch.setattr(old,'FixtureWorker',ExpiredWorker)
            f = full.scenario(tmp_path/kind,patch,{'MARKET':['timeout']})
            assert f.result['status'] == 'FAILED_NO_SEND' and len(f.calls) == 1, kind
            assert not f.budget.accepted and f.budget.stopped, kind


def test_shared_42_cap_unchanged_b2_third_attempt_input_drift_and_kr_scope(tmp_path):
    from app.services.unified_market_run import target_session
    base = old.listed_plan(UNIVERSE['us'])
    plan = compile_model_plan(replace(base.cohort,limitation_subjects=('SKHY',)),topology='CANONICAL_PRODUCTION')
    binding = timeout.b2_retry_binding(plan)
    journal = ModelInvocationJournal(tmp_path/'cap.jsonl',plan_sha256=plan.sha256,maximum=42,b2_retry_policy=binding)
    retried_b2 = 0
    for i,slot in enumerate(plan.slots):
        journal.transact('BIND',slot_id=slot.slot_id,scope=dict(slot_id=slot.slot_id,stage=slot.stage,subjects=list(slot.subjects),dependency_outputs={}))
        a = old.attempt(10*i+1)
        journal.transact('CONSUME',slot_id=slot.slot_id,attempt=a)
        if slot.stage == 'MARKET' or slot.stage == 'B2' and retried_b2 < 12:
            journal.transact('TIMEOUT_CONFIRMED',slot_id=slot.slot_id,proof=old.proof(a))
            before = journal.path.read_bytes()
            with pytest.raises(ValueError):
                journal.transact('RETRY_ATTEMPT',slot_id=slot.slot_id,attempt=old.attempt(10*i+2,2,digest('changed')))
            assert journal.path.read_bytes() == before
            a = old.attempt(10*i+2,2)
            journal.transact('RETRY_ATTEMPT',slot_id=slot.slot_id,attempt=a)
            retried_b2 += slot.stage == 'B2'
            with pytest.raises(ValueError):
                journal.transact('RETRY_ATTEMPT',slot_id=slot.slot_id,attempt=old.attempt(10*i+3,3))
        elif slot.stage == 'B2':
            journal.transact('TIMEOUT_CONFIRMED',slot_id=slot.slot_id,proof=old.proof(a))
            with pytest.raises(ValueError):
                journal.transact('RETRY_ATTEMPT',slot_id=slot.slot_id,attempt=old.attempt(10*i+2,2))
            break
        journal.transact('ACCEPT',slot_id=slot.slot_id,attempt_id=a['attempt_id'],output_sha256=digest(i))
    assert read_invocation_journal(journal.path.read_bytes())['physical_calls'] == 42
    assert timeout.retry_policy_limits(timeout.B2_PER_TICKER_ONE_RETRY_V1) == (29,13,42)
    assert timeout.market_timeout_retry_cap(None) == 0
    assert timeout.market_timeout_retry_cap(dict(binding,policy=timeout.B2_US2_DIAGNOSTIC_V1)) == 0
    assert target_session('kr',datetime.fromisoformat('2026-11-21T15:35:00+09:00')) is None
    assert target_session('kr',datetime.fromisoformat('2026-11-23T15:35:00+09:00')).isoformat() == '2026-11-23'
