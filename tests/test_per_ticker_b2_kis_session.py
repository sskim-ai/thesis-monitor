"""Changed boundaries only: synthetic workers and temporary registration DBs."""
import asyncio
from collections import Counter
from dataclasses import replace
from datetime import datetime, timedelta, timezone
import json
from types import SimpleNamespace

import pytest

from app.jobs import unified_market_snapshot as job
from app.services import prospective_class_c_owner as registration
from app.services.model_execution_plan import compile_model_plan
from app.services.model_invocation_journal import ModelInvocationJournal, read_invocation_journal
from app.services.model_timeout_retry import B2_PER_TICKER_ONE_RETRY_V1 as POLICY, b2_retry_binding, read_no_send_partition
from app.services.production_model_profile import SolHighCallBudget
from app.services.selected_run_lifecycle import SelectedRunLedger
from app.services.unified_snapshot_contract import digest
from tests import test_c22bf_timeout as old, test_v8_mixed_retry as mixed
from tests.test_manual_source_budget import offline_only


@pytest.fixture(autouse=True)
def no_workers(monkeypatch):
    def denied(*args, **kwargs):
        raise AssertionError('real worker forbidden in offline test')
    monkeypatch.setattr(asyncio, 'create_subprocess_exec', denied)


def admitted(tmp_path, plan, cap):
    now = datetime.now(timezone.utc)
    subjects = tuple(plan.cohort.market_subjects['us'])
    approval = registration.record_backend_approval(registration.ApprovalDecision(
        event_id='SYNTHETIC_PER_TICKER', approved=True, user_message_sha256=digest('SYNTHETIC'),
        effective_at=now-timedelta(seconds=1), expires_at=now+timedelta(hours=1), subjects=subjects))
    ledger = SelectedRunLedger(path=tmp_path/'campaign.jsonl', approval=approval, master_id='SYNTHETIC',
        children={'us':dict(generation=plan.cohort.source_generation, subjects=list(subjects))},
        provider_caps={'kiwoom':1}, max_http=1, max_models=42,
        database_identity=dict(path='SYNTHETIC_NO_DB', device=0, inode=0), staged_markets=True,
        runtime_cap=dict(endpoints={'fixture':[]}), wallclock_seconds_max=3600, b2_retry_policy=POLICY)
    original = ledger._apply
    def apply(state, event, value):
        if event == 'OPEN':
            state.update(active_markets=['us'], sources={'us':digest('test-owner')})
        return original(state, event, value)
    ledger._apply = apply
    binding = b2_retry_binding(plan)
    ledger._event('MODEL_PLAN', market='us', sha256=plan.sha256, slots=len(plan.slots),
        slot_ids=[s.slot_id for s in plan.slots], slot_stages=binding['slot_stages'], b2_retry_binding=binding)
    runtime = tmp_path/'runtime'
    budget = SolHighCallBudget(plan=plan, approved_max_invocations=42, approved_plan_sha256=plan.sha256,
        journal_path=runtime/'invocation-ledger'/plan.cohort.run_id/'events.jsonl', run_ledger=ledger,
        b2_retry_policy=POLICY)
    return budget, runtime


def scenario(tmp_path, monkeypatch, failures):
    monkeypatch.setattr(old, 'admitted_budget', admitted)
    transport = old.transport
    def injected(folder, patch, budget, runtime, outcomes, recorded):
        subjects = [s.subjects[0] for s in budget.plan.slots if s.stage == 'B2']
        stream = []
        for i, value in enumerate(outcomes):
            ticker = subjects[i-16] if i >= 16 else 'MARKET' if i == 0 else None
            errors = failures.get(ticker, [])
            stream.extend(errors)
            if errors != ['timeout', 'timeout']:
                stream.append(value)
        return transport(folder, patch, budget, runtime, iter(stream), recorded)
    monkeypatch.setattr(old, 'transport', injected)
    return mixed.fixture_run(tmp_path, monkeypatch, cap=1)


def test_all_13_b2_retry_once_42_starts_29_accepts_15_messages_and_cold(tmp_path, monkeypatch):
    from app.services.unified_stock_acquisition import UNIVERSE
    f = scenario(tmp_path, monkeypatch, {t:['timeout'] for t in UNIVERSE['us'] if t != 'SKHY'})
    assert f.result['status'] == 'RENDER_VERIFIED_NO_SEND', f.result.get('error_chain')
    assert len(f.calls) == f.budget.physical_calls == f.budget.run_ledger.state()['model_total'] == 42
    assert len(f.budget.accepted) == 29 and f.budget.retry_used == 13
    assert len(f.result['messages']) == 15
    assert next(m for m in f.result['messages'] if m['message_id']=='SKHY')['decision_mode'] == 'UNKNOWN_LIMIT'
    counts = Counter(c['slot_scope']['subjects'][0] for c in f.calls if c['stage']=='B2')
    assert len(counts) == 13 and set(counts.values()) == {2} and 'SKHY' not in counts
    b2 = next(r for r in f.result['stage_receipts'] if r['stage']=='B2')
    assert b2['deadline']['b2_retry_policy'] == b2_retry_binding(f.plan)
    assert b2['timing']['worker_windows'] == 26
    cold = read_no_send_partition(f.cycle, plan=f.plan, invocation_journal=f.budget.journal.path)
    assert cold['count'] == 15 and cold['physical_attempts'] == 42 and cold['timeout_retries'] == 13
    for ticker in counts:
        pair = [c for c in f.calls if c['slot_scope']['stage']=='B2' and c['slot_scope']['subjects']==[ticker]]
        assert pair[0]['request_id'] != pair[1]['request_id']
        assert all(pair[0][k] == pair[1][k] for k in ('slot_scope','prompt_sha256','schema_sha256','b2_retry_policy'))


@pytest.mark.parametrize('tickers', [('CPNG','TSM'), ('CPNG','TSM','WULF')])
def test_third_distinct_ticker_not_blocked_by_old_shared_cap(tmp_path, monkeypatch, tickers):
    f = scenario(tmp_path, monkeypatch, {t:['timeout'] for t in tickers})
    assert f.result['status'] == 'RENDER_VERIFIED_NO_SEND', f.result.get('error_chain')
    assert f.budget.physical_calls == 29+len(tickers) and f.budget.retry_used == len(tickers) and len(f.result['messages']) == 15


def test_second_timeout_preserves_mixed_contract_and_no_third_attempt(tmp_path, monkeypatch):
    f = scenario(tmp_path, monkeypatch, {'TSM':['timeout','timeout']})
    assert f.result['status'] == 'FAILED_NO_SEND' and 'messages' not in f.result
    assert sum(c['slot_scope']['subjects']==['TSM'] for c in f.calls) == 2
    assert not (f.cycle/'render/response.json').exists()
    assert f.result['stage_receipts'][-1]['stage'] == 'VALIDATE'
    assert json.loads((f.cycle/'b2/response.json').read_bytes())['output']['unissued']['TSM']['attempts'] == 2
    assert any(frame['file']=='production_runtime_bridge.py' and frame['function']=='stage'
        for error in f.result['error_chain'] for frame in error.get('frames',[]))


@pytest.mark.parametrize('failure', ['ambiguous','auth'])
def test_nonconfirmed_or_auth_failure_stops_without_retry(tmp_path, monkeypatch, failure):
    f = scenario(tmp_path, monkeypatch, {'CPNG':[failure]})
    assert f.result['status'] == 'FAILED_NO_SEND' and 'messages' not in f.result
    assert sum(c['slot_scope']['subjects']==['CPNG'] for c in f.calls) == 1
    assert f.budget.retry_used == 0


def test_full_us_market_timeout_retries_once_within_42(tmp_path, monkeypatch):
    f = scenario(tmp_path, monkeypatch, {'MARKET':['timeout']})
    assert f.result['status'] == 'RENDER_VERIFIED_NO_SEND' and len(f.calls) == 30 and f.budget.retry_used == 1


def test_journal_third_attempt_and_43rd_start_forbidden_legacy_readback(tmp_path):
    from app.services.unified_stock_acquisition import UNIVERSE
    base = old.listed_plan(UNIVERSE['us'])
    plan = compile_model_plan(replace(base.cohort, limitation_subjects=('SKHY',)), topology='CANONICAL_PRODUCTION')
    policy = b2_retry_binding(plan)
    journal = ModelInvocationJournal(tmp_path/'new.jsonl', plan_sha256=plan.sha256, maximum=42, b2_retry_policy=policy)
    for i, slot in enumerate(plan.slots):
        journal.transact('BIND', slot_id=slot.slot_id, scope=dict(slot_id=slot.slot_id, stage=slot.stage,
            subjects=list(slot.subjects), dependency_outputs={}))
        a = old.attempt(2*i+1)
        journal.transact('CONSUME', slot_id=slot.slot_id, attempt=a)
        if slot.stage == 'B2':
            journal.transact('TIMEOUT_CONFIRMED', slot_id=slot.slot_id, proof=old.proof(a))
            a = old.attempt(2*i+2, 2)
            journal.transact('RETRY_ATTEMPT', slot_id=slot.slot_id, attempt=a)
        journal.transact('ACCEPT', slot_id=slot.slot_id, attempt_id=a['attempt_id'], output_sha256=digest(i))
    before = journal.path.read_bytes()
    for event in ('CONSUME','RETRY_ATTEMPT'):
        with pytest.raises(ValueError):
            journal.transact(event, slot_id=plan.slots[-1].slot_id, attempt=old.attempt(999,3))
    assert journal.path.read_bytes() == before and read_invocation_journal(before)['physical_calls'] == 42
    for cap in (0,1,2):
        legacy = ModelInvocationJournal(tmp_path/f'legacy-{cap}.jsonl',plan_sha256=digest(cap),maximum=1+cap,retry_cap=cap)
        legacy.transact('BIND',slot_id='s',scope=dict(slot_id='s',stage='B2',dependency_outputs={}))
        legacy.transact('CONSUME',slot_id='s',**(dict(attempt=old.attempt(cap+100)) if cap else {}))
        assert read_invocation_journal(legacy.path.read_bytes())['physical_calls'] == 1
        assert 'b2_retry_policy' not in legacy.identity


def test_one_shot_latest_completed_only_regular_calendar_unchanged():
    from app.services.unified_market_run import target_session
    def dt(v): return datetime.fromisoformat(v)
    for hour in ('06:10','14:30','18:00','23:59'):
        now = dt(f'2026-11-20T{hour}:00+09:00')
        assert job.latest_one_shot_us_session(now).isoformat() == '2026-11-19'
    assert target_session('us',dt('2026-11-20T18:00:00+09:00')) is None
    assert target_session('us',dt('2026-11-20T06:10:00+09:00')).isoformat() == '2026-11-19'
    assert target_session('kr',dt('2026-11-20T15:35:00+09:00')).isoformat() == '2026-11-20'
    for value in ('2026-11-21T06:10:00+09:00','2026-11-26T18:00:00+09:00','2026-11-22T18:00:00+09:00'):
        assert job.latest_one_shot_us_session(dt(value)) is None
    assert job.latest_one_shot_us_session(dt('2026-11-20T18:00:00')) is None


def test_kis_plan_exact_readback_missing_tamper_and_scope_before_http(tmp_path):
    from app.services.selected_kis_sources import require_persisted_plan
    from tests.test_c22ab_selected_source import compile_market
    compiled, _, kis = compile_market('kr','005930')
    plan = compiled['plan']
    path = tmp_path/'kis-plan.json'
    with pytest.raises(FileNotFoundError):
        require_persisted_plan(tmp_path, kis, plan)
    path.write_text(json.dumps(kis))
    require_persisted_plan(tmp_path, kis, plan)
    path.write_text('{}')
    with pytest.raises(ValueError):
        require_persisted_plan(tmp_path, kis, plan)
    with pytest.raises(ValueError):
        require_persisted_plan(tmp_path, None, plan)
    with pytest.raises(ValueError):
        require_persisted_plan(tmp_path, kis, SimpleNamespace(kis_plan_sha256=digest(kis),subjects=('other',)))


def test_kis_child_diagnostic_is_bounded_type_only(tmp_path, monkeypatch):
    from app.services.production_source_transport import acquire_kis_worker
    (tmp_path/'production-frozen-source-plan.json').write_text('{}')
    class Worker:
        returncode = 1
        async def communicate(self, frame):
            return b'{"status":"FAIL","error_type":"FileNotFoundError"}', b'PRIVATE_URL_AND_KEY'
    async def worker(*args, **kwargs): return Worker()
    monkeypatch.setattr(asyncio,'create_subprocess_exec',worker)
    with pytest.raises(ValueError,match='production_kis_acquisition_failed'):
        asyncio.run(acquire_kis_worker(root=tmp_path,frozen={'generation_id':'SYNTHETIC'},plan={},
            credentials={'kis':['DUMMY','DUMMY']},remaining=1))
    raw = (tmp_path/'kis-worker-exit.json').read_text()
    receipt = json.loads(raw)
    assert receipt['error_type']=='FileNotFoundError' and receipt['returncode']==1 and receipt['child_reaped']
    assert 'PRIVATE_URL_AND_KEY' not in raw and 'DUMMY' not in raw


def test_actual_kr_and_us_callers_reach_collector_without_http(tmp_path, monkeypatch):
    from tests.test_local_launchd_entry import original_cycle_probe
    for market in ('kr','us'):
        with monkeypatch.context() as patch:
            def runtime(execution):
                path = tmp_path/'private-runtime'/execution
                path.mkdir(parents=True,mode=0o700)
                return path
            patch.setattr(job,'_local_model_runtime',runtime)
            value = original_cycle_probe(tmp_path/market, market, patch)
            assert value['financial_HTTP'] == value['models'] == 0


def test_actual_caller_and_factory_policy_forwarding():
    import inspect
    from app.services.production_adapter_factory import build_production_adapter
    from app.services import research_no_send_run as research
    from tests.test_local_us_timeout2 import test_actual_caller_ledger_model_and_intent_caps_preserve_kr
    test_actual_caller_ledger_model_and_intent_caps_preserve_kr()
    assert 'b2_retry_policy' in inspect.signature(build_production_adapter).parameters
    assert 'b2_retry_policy' in inspect.signature(research.build_research_no_send_adapter).parameters
