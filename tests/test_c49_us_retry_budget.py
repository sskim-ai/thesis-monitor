"""Synthetic US workers: preserve all initial calls inside the approved 42 total."""
import json

import pytest

from app.services.model_invocation_journal import read_invocation_journal
from app.services.model_timeout_retry import b2_retry_binding, b2_retry_budget_bounds, read_no_send_partition
from app.services.research_no_send_run import TERMINAL
from app.services.unified_snapshot_contract import digest
from app.services.unified_stock_acquisition import UNIVERSE
from tests import test_c22bf_timeout as old, test_per_ticker_b2_kis_session as per_ticker
from tests.test_c22aa_research_boundaries import req
from tests.test_manual_source_budget import offline_only


@pytest.mark.parametrize('extra_timeout', [False, True])
def test_us14_keeps_42_cap_and_original_timeout_when_retry_pool_is_spent(tmp_path,monkeypatch,extra_timeout):
    subjects = UNIVERSE['us']
    failures = {'MARKET':['timeout'], **{t:['timeout'] for t in subjects[:11]}}
    if extra_timeout:
        failures[subjects[11]] = ['timeout']
    f = per_ticker.scenario(tmp_path,monkeypatch,failures,limited=False)
    assert len(f.plan.slots)==30 and len(f.budget.b2_retry_policy['b2_slots'])==14
    assert f.budget.b2_retry_policy['maximum']==44
    assert f.budget.maximum==f.budget.run_ledger.identity['max_models']==42
    assert f.budget.journal.identity['maximum']==42 and f.budget.retry_capacity==12
    assert f.budget.timeout_retry_cap==0 and f.budget.retry_used==12
    assert len(f.calls)==f.budget.physical_calls==f.budget.run_ledger.state()['model_total']
    assert all(len(a)<=2 for a in f.budget.attempts.values())
    if not extra_timeout:
        assert f.result['status']==TERMINAL, f.result.get('error_chain')
        assert len(f.result['messages'])==15 and len(f.budget.accepted)==30 and len(f.calls)==42
        assert not f.result.get('unissued') and not f.result.get('limitation_receipts')
        cold=read_no_send_partition(f.cycle,plan=f.plan,invocation_journal=f.budget.journal.path)
        assert cold['count']==15 and cold['physical_attempts']==42 and cold['timeout_retries']==12
    else:
        assert f.result['status']=='FAILED_NO_SEND' and 'messages' not in f.result
        assert f.result['first_failure']['type']=='ModelTransportError'
        assert len(f.calls)==40 and len(f.budget.used)==28
        assert not f.budget.exhausted and not (f.cycle/'b2'/subjects[11]/'unissued.json').exists()
        slot=next(s for s in f.plan.slots if s.stage=='B2' and s.subjects==(subjects[11],))
        journal=read_invocation_journal(f.budget.journal.path.read_bytes())
        assert len(journal['attempts'][slot.slot_id])==len(journal['timeouts'][slot.slot_id])==1
        assert journal['timeouts'][slot.slot_id][0]['error']=='TRANSPORT_TIMEOUT'


def test_journal_and_selected_ledger_reserve_remaining_initial_calls(tmp_path):
    plan=old.listed_plan(UNIVERSE['us'])
    budget,_=per_ticker.admitted(tmp_path,plan,0)
    assert b2_retry_budget_bounds(b2_retry_binding(plan))==(30,44)
    assert b2_retry_budget_bounds(b2_retry_binding(plan),retry_cap=1)==(45,45)
    for index,slot in enumerate(plan.slots):
        row=req(plan,slot)
        scope=budget.bind_stage(slot.stage,row)
        first=old.attempt(2*index+1)
        budget.consume(None,slot.stage,row['payload_sha256'],slot_scope=scope,attempt=first)
        if slot.stage in ('MARKET','B2'):
            available=budget.confirmed_timeout(slot.slot_id,old.proof(first))
            second=old.attempt(2*index+2,2)
            if budget.retry_used==12:
                assert not available and budget.physical_calls==40 and len(budget.used)==28
                assert not budget.exhausted
                journal_before=budget.journal.path.read_bytes()
                ledger_before=budget.run_ledger.path.read_bytes()
                with pytest.raises(ValueError,match='selected_model_retry_scope_or_budget'):
                    budget.consume(None,slot.stage,row['payload_sha256'],slot_scope=scope,attempt=second)
                assert budget.journal.path.read_bytes()==journal_before
                assert budget.run_ledger.path.read_bytes()==ledger_before
                with pytest.raises(ValueError,match='model_journal_retry_unavailable'):
                    budget.journal.transact('RETRY_ATTEMPT',slot_id=slot.slot_id,attempt=second)
                assert budget.journal.path.read_bytes()==journal_before
                assert json.loads(journal_before.splitlines()[-1])['event']=='TIMEOUT_CONFIRMED'
                return
            assert available
            budget.consume(None,slot.stage,row['payload_sha256'],slot_scope=scope,attempt=second)
        budget.record_acceptance(slot.slot_id,payload_sha256=row['payload_sha256'],output_sha256=digest(index))
    pytest.fail('the fixture never reached the shared retry budget boundary')
