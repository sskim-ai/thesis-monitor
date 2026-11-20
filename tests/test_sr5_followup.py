"""Only the explicitly requested five-subject boundary; all live IO is denied."""
import asyncio
from dataclasses import replace
from datetime import datetime, timedelta, timezone
import json
import socket
from types import SimpleNamespace

import pytest

from app.jobs import unified_market_snapshot as job
from app.services.model_timeout_retry import B2_SR5_DIAGNOSTIC_V1, b2_retry_binding, read_no_send_partition
from app.services.unified_snapshot_contract import digest
from tests import test_c22bf_timeout as old, test_v8_mixed_retry as mixed


@pytest.fixture(autouse=True)
def no_live(monkeypatch):
    def denied(*args, **kwargs):
        raise AssertionError('SR5_OFFLINE_NO_NETWORK_OR_REAL_WORKER')
    for name in ('connect', 'connect_ex', 'sendto'):
        monkeypatch.setattr(socket.socket, name, denied)
    monkeypatch.setattr(asyncio, 'create_subprocess_exec', denied)


def test_original_capture_freezes_exact_five_and_issuer_before_HTTP(tmp_path, monkeypatch):
    from tests.test_local_launchd_entry import original_cycle_probe
    (tmp_path/'private-runtime').mkdir(mode=0o700)
    monkeypatch.setattr(job, '_local_model_runtime', lambda execution:tmp_path/'private-runtime')
    result=original_cycle_probe(tmp_path, 'us', monkeypatch, one_shot_tag='us5-20261120-1234abcd')
    frozen=json.loads((tmp_path/'source/production-frozen-source-plan.json').read_bytes())
    scope=json.loads((tmp_path/'us5-before-http.json').read_bytes())
    assert result['financial_HTTP']==result['models']==0
    assert tuple(frozen['plan']['subjects'])==job.SR5_SUBJECTS
    assert scope['financial_subjects']==['000660',*job.SR5_SUBJECTS]
    assert scope['actual_plan_budget']['total']<=scope['max_HTTP']==313
    assert scope['expected_B2_subjects']==['CRCL','HUT','TSM','WULF'] and scope['max_models']==15


def five_budget(tmp_path, plan, cap):
    from app.services import prospective_class_c_owner as reg
    from app.services.selected_run_lifecycle import SelectedRunLedger
    from app.services.production_model_profile import SolHighCallBudget
    from app.services.unified_stock_acquisition import UNIVERSE
    now=datetime.now(timezone.utc)
    approval=reg.record_backend_approval(reg.ApprovalDecision(event_id='SYNTHETIC_SR5',approved=True,
        user_message_sha256=digest('OFFLINE'),effective_at=now-timedelta(seconds=1),
        expires_at=now+timedelta(hours=1),subjects=UNIVERSE['us']))
    ledger=SelectedRunLedger(path=tmp_path/'campaign.jsonl',approval=approval,master_id='SYNTHETIC_SR5',
        children={'us':dict(generation=plan.cohort.source_generation,subjects=list(UNIVERSE['us']))},
        provider_caps={'kiwoom':1},max_http=1,max_models=15,database_identity=dict(path='NO_DB',device=0,inode=0),
        staged_markets=True,runtime_cap=dict(endpoints={'fixture':[]}),wallclock_seconds_max=3600,
        b2_retry_policy=B2_SR5_DIAGNOSTIC_V1)
    original=ledger._apply
    def apply(state,event,value):
        if event=='OPEN':state.update(active_markets=['us'],sources={'us':digest('SYNTHETIC_SOURCE')})
        return original(state,event,value)
    ledger._apply=apply
    binding=b2_retry_binding(plan,B2_SR5_DIAGNOSTIC_V1)
    ledger._event('MODEL_PLAN',market='us',sha256=plan.sha256,slots=11,slot_ids=[s.slot_id for s in plan.slots],
        slot_stages=binding['slot_stages'],b2_retry_binding=binding)
    runtime=tmp_path/'runtime'
    return SolHighCallBudget(plan=plan,approved_max_invocations=15,approved_plan_sha256=plan.sha256,
        journal_path=runtime/'invocation-ledger'/plan.cohort.run_id/'events.jsonl',run_ledger=ledger,
        b2_retry_policy=B2_SR5_DIAGNOSTIC_V1),runtime


def test_four_B2_retries_keep_SKHY_limitation_and_six_messages(tmp_path, monkeypatch):
    monkeypatch.setattr(old,'admitted_budget',five_budget)
    transport=old.transport
    def injected(folder,patch,budget,runtime,outcomes,recorded):
        stream=[]
        for index,value in enumerate(outcomes):
            if index>=7:stream.append('timeout')
            stream.append(value)
        return transport(folder,patch,budget,runtime,iter(stream),recorded)
    monkeypatch.setattr(old,'transport',injected)
    result=mixed.fixture_run(tmp_path,monkeypatch,cap=1,limited=True,subjects=job.SR5_SUBJECTS)
    assert result.result['status']=='RENDER_VERIFIED_NO_SEND',result.result.get('error_chain')
    assert len(result.calls)==15 and len(result.budget.accepted)==11 and len(result.result['messages'])==6
    assert not any(c['slot_scope']['stage']=='B2' and c['slot_scope']['subjects']==['SKHY'] for c in result.calls)
    assert next(m for m in result.result['messages'] if m['message_id']=='SKHY')['decision_mode']=='UNKNOWN_LIMIT'
    cold=read_no_send_partition(result.cycle,plan=result.plan,invocation_journal=result.budget.journal.path)
    assert cold['count']==6 and cold['timeout_retries']==4


def test_exact_policy_news_scope_and_existing_profiles_unchanged(monkeypatch):
    from app.services import production_message_renderer as render
    from app.services.model_execution_plan import compile_model_plan
    from app.services.model_timeout_retry import retry_policy_limits
    from app.services.selected_news_rate_limit import STATUS, PROVIDER
    base=old.listed_plan(job.SR5_SUBJECTS)
    with pytest.raises(ValueError):b2_retry_binding(base,B2_SR5_DIAGNOSTIC_V1)
    plan=compile_model_plan(replace(base.cohort,limitation_subjects=('SKHY',)),topology='CANONICAL_PRODUCTION')
    assert b2_retry_binding(plan,B2_SR5_DIAGNOSTIC_V1)['maximum']==15
    assert retry_policy_limits('B2_US2_DIAGNOSTIC_V1')==(6,2,8)
    assert retry_policy_limits('B2_PER_TICKER_ONE_RETRY_V1')==(29,13,42)
    assert job.one_shot_scope('us','us5-20261120-1234abcd')
    with pytest.raises(ValueError):job.one_shot_scope('kr','us5-20261120-1234abcd')
    monkeypatch.setattr(render.market_owner,'validate_market',lambda *a:{'status':'PASS'})
    monkeypatch.setattr(render.market_owner,'numeric_boundary',lambda *a:{'status':'PASS'})
    monkeypatch.setattr(render,'build_display_plan',lambda *a,**k:SimpleNamespace(model_dump=lambda **k:{}))
    monkeypatch.setattr(render,'AcceptedMarketCalibration',lambda **k:SimpleNamespace(model_dump=lambda **k:{}))
    monkeypatch.setattr(render,'render_daily_digest',lambda *a,**k:'Synthetic market')
    session=SimpleNamespace(market='us',gen='SYNTHETIC_SR5',markets={'us':{}},projected={'us':dict(
        packet=dict(market_context={},assessment_date='2026-11-19'),
        context=dict(request_eligible_refs=[],numeric_catalog={}),views=dict(display={}))},
        fresh_stocks={t:dict(event_view=dict(binding=dict(denial=STATUS,provider=PROVIDER,evidence=[],
            rate_limit=dict(subject=t)))) for t in job.SR5_SUBJECTS})
    assert all(t in render.market_message(session)['text'] for t in job.SR5_SUBJECTS)
    session.fresh_stocks.pop('WULF')
    with pytest.raises(ValueError):render.market_message(session)
