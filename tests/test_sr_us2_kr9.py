"""Changed SR dates, original subset ports, and exact-day namespaces only."""
import asyncio
from copy import deepcopy
from dataclasses import replace
from datetime import datetime,timedelta,timezone
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from app.jobs import unified_market_snapshot as job
from app.services import us_dated_source_sr as sr
from app.services.detailed_stock_message_v2 import _us_sr_rows
from app.services.model_timeout_retry import B2_US2_DIAGNOSTIC_V1, b2_retry_binding, read_no_send_partition
from app.services.unified_snapshot_contract import digest
from tests import test_c22bf_timeout as old, test_v8_mixed_retry as mixed
from tests.test_manual_source_budget import offline_only

ROOT=Path('/Users/sskim/Documents/Codex/2026-07-04/the')
PREVIOUS=ROOT/'maintenance/20261120-pr52-uskr-per-ticker-session'


@pytest.fixture(autouse=True)
def no_worker(monkeypatch):
    def denied(*a,**k):raise AssertionError('NO_REAL_MODEL_IN_OFFLINE_TEST')
    monkeypatch.setattr(asyncio,'create_subprocess_exec',denied)


def retained(ticker):
    schedule=json.loads((PREVIOUS/'SCHEDULE_INSTALL_RECEIPT.json').read_bytes())
    source=Path(schedule['run_root'])/'source'
    frozen=json.loads((source/'production-frozen-source-plan.json').read_bytes())
    periods,receipts={},{}
    for index,entry in enumerate(frozen['stock_plan']['reads'],1):
        if entry['subject']!=ticker or not entry['role'].startswith('adjusted_'):continue
        p=source/'native/stocks'/f'role-{index:03d}.receipt.json';receipt=json.loads(p.read_bytes())
        raw=(p.parent/receipt['normalized_artifact']).read_bytes()
        assert hashlib.sha256(raw).hexdigest()==receipt['normalized_sha256']
        periods[entry['timeframe']]=json.loads(raw);receipts[entry['role']]=receipt
    return dict(enabled=True,ticker=ticker,security_id=receipts['adjusted_daily']['entry']['canonical_security_id'],
        generation=frozen['generation_id'],cutoff='2026-11-19',observed_at=frozen['stock_plan']['frozen_at'],
        periods=periods,receipts=receipts,provider_limit=1000)


def rendered(ref,args):
    from tests.test_pr52_v11_us_sr_reference import source_for
    source=source_for(ref,args);source['fresh_run_id']=args['generation']
    source['packet']['source_time_domains']['run_id']=args['generation']
    source['packet']['stocks'][0]['ticker']=args['ticker']
    source['source_graph']['price:current']['ticker']=args['ticker']
    base=SimpleNamespace(source_stock=source,source_generation_id=args['generation'],accepted_calibration=SimpleNamespace(entries={}))
    return _us_sr_rows(SimpleNamespace(market='us',ticker=args['ticker']),base,
        dict(entry_timing=dict(state='UNRESOLVED')),args['security_id'])


def test_retained_googl_normal_reference_unchanged(monkeypatch):
    import subprocess
    args=retained('GOOGL');before=digest(args)
    original={};exec(subprocess.check_output(['git','show','HEAD:app/services/us_dated_source_sr.py'],text=True),original)
    old_ref=original['attach']({},**args)['price_structure_v3']
    current=sr.attach({},**args)['price_structure_v3']
    assert current==old_ref and current['as_of']=='2026-11-19' and len(current['zones'])==3
    assert all('2026-11-19' in r.text for r in rendered(current,args))
    assert digest(args)==before


def test_retained_mu_excludes_one_bad_day_and_renders_previous_official_day():
    args=retained('MU');before=digest(args)
    ref=sr.attach({},**args)['price_structure_v3']
    assert ref['target_session']=='2026-11-19' and ref['as_of']==ref['reference_as_of']=='2026-11-18'
    assert sr.valid_reference_lineage(ref) and not ref['eligible_for_b2_timing'] and not ref['eligible_for_current_price']
    assert ref['latest_daily_exclusion']['excluded_row']['low']>ref['latest_daily_exclusion']['excluded_row']['close']
    rows=rendered(ref,args)
    assert rows and all('2026-11-18' in r.text and '2026-11-19 해당 일봉 불일치 제외' in r.text for r in rows)
    assert digest(args)==before


def test_fallback_missing_old_future_partial_identity_and_hash_denials(monkeypatch):
    from tests.test_pr52_v11_us_sr_reference import data
    args,_,rollout=data.__wrapped__(monkeypatch)
    args.update(cutoff='2026-11-19',observed_at='2026-11-20T08:10:00+09:00')
    args['periods']['daily'].append(dict(args['periods']['daily'][-1],date='2026-11-19',close=80))
    for receipt in args['receipts'].values():receipt['entry']['latest_completed_session']='2026-11-19'
    rollout.numeric_bindings[0]['as_of']='2026-11-18'
    assert sr.attach({},**args)['price_structure_v3']['as_of']=='2026-11-18'
    other=deepcopy(args);other['ticker']='OTHER'
    for r in other['receipts'].values():r['entry']['subject']='OTHER'
    rollout.numeric_bindings[0]['security_basis']='US_LISTED:OTHER'
    assert sr.attach({},**other)['price_structure_v3']['as_of']=='2026-11-18'
    for kind in ('missing','too_old','partial','future','adjustment','identity'):
        bad=deepcopy(args)
        if kind=='missing':bad['periods']['daily'].pop()
        elif kind=='too_old':bad['periods']['daily'].pop(-2)
        elif kind=='partial':bad['periods']['daily'][-1]['bar_state']='PARTIAL'
        elif kind=='future':bad['periods']['daily'].append(dict(bad['periods']['daily'][-1],date='2026-11-20'))
        elif kind=='adjustment':bad['receipts']['adjusted_daily']['entry']['adjusted']=False
        else:bad['receipts']['adjusted_daily']['entry']['canonical_security_id']='OTHER'
        assert sr.attach({},**bad)=={}
    rollout.numeric_bindings[0]['security_basis']='US_LISTED:MU'
    ref=sr.attach({},**args)['price_structure_v3']
    for field in ('reference_row_sha256','source_plan_sha256'):
        changed=deepcopy(ref);changed['latest_daily_exclusion'][field]='0'*64
        assert not rendered(changed,args)


def test_no_safe_zone_still_omitted(monkeypatch):
    from tests.test_pr52_v11_us_sr_reference import data
    args,_,rollout=data.__wrapped__(monkeypatch);rollout.numeric_bindings=[]
    assert sr.attach({},**args)=={}


def subset_budget(tmp_path,plan,cap):
    from app.services import prospective_class_c_owner as reg
    from app.services.selected_run_lifecycle import SelectedRunLedger
    from app.services.production_model_profile import SolHighCallBudget
    from app.services.unified_stock_acquisition import UNIVERSE
    now=datetime.now(timezone.utc)
    a=reg.record_backend_approval(reg.ApprovalDecision(event_id='SYNTHETIC_US2',approved=True,
        user_message_sha256=digest('OFFLINE'),effective_at=now-timedelta(seconds=1),expires_at=now+timedelta(hours=1),subjects=UNIVERSE['us']))
    ledger=SelectedRunLedger(path=tmp_path/'campaign.jsonl',approval=a,master_id='SYNTHETIC_US2',
        children={'us':dict(generation=plan.cohort.source_generation,subjects=list(UNIVERSE['us']))},
        provider_caps={'kiwoom':1},max_http=1,max_models=8,database_identity=dict(path='NO_DB',device=0,inode=0),
        staged_markets=True,runtime_cap=dict(endpoints={'fixture':[]}),wallclock_seconds_max=3600,b2_retry_policy=B2_US2_DIAGNOSTIC_V1)
    original=ledger._apply
    def apply(s,event,v):
        if event=='OPEN':s.update(active_markets=['us'],sources={'us':digest('SYNTHETIC_SOURCE_ONLY')})
        return original(s,event,v)
    ledger._apply=apply;binding=b2_retry_binding(plan,B2_US2_DIAGNOSTIC_V1)
    ledger._event('MODEL_PLAN',market='us',sha256=plan.sha256,slots=6,slot_ids=[s.slot_id for s in plan.slots],
        slot_stages=binding['slot_stages'],b2_retry_binding=binding)
    runtime=tmp_path/'runtime'
    return SolHighCallBudget(plan=plan,approved_max_invocations=8,approved_plan_sha256=plan.sha256,
        journal_path=runtime/'invocation-ledger'/plan.cohort.run_id/'events.jsonl',run_ledger=ledger,b2_retry_policy=B2_US2_DIAGNOSTIC_V1),runtime


def test_us2_both_b2_retry_once_to_three_messages_and_cold(tmp_path,monkeypatch):
    monkeypatch.setattr(old,'admitted_budget',subset_budget);transport=old.transport
    def injected(folder,patch,budget,runtime,outcomes,recorded):
        stream=[]
        for i,value in enumerate(outcomes):
            if i>=4:stream.append('timeout')
            stream.append(value)
        return transport(folder,patch,budget,runtime,iter(stream),recorded)
    monkeypatch.setattr(old,'transport',injected)
    f=mixed.fixture_run(tmp_path,monkeypatch,cap=1,limited=False,subjects=job.US2_SUBJECTS)
    assert f.result['status']=='RENDER_VERIFIED_NO_SEND',f.result.get('error_chain')
    assert len(f.calls)==8 and len(f.budget.accepted)==6 and len(f.result['messages'])==3
    assert {m['message_id'] for m in f.result['messages']}=={'MARKET_US','GOOGL','MU'}
    assert read_no_send_partition(f.cycle,plan=f.plan,invocation_journal=f.budget.journal.path)['count']==3
    assert f.budget.run_ledger.state()['model_total']==8


def test_us2_original_source_coverage_census_not_full14(tmp_path):
    from tests.test_newbuyer_b2_v2_coverage import source
    from app.services.current_source_coverage import seal_inputs,compose,SEMANTICS
    owners={t:source(tmp_path/t,ticker=t,generation='SYNTHETIC_US2') for t in job.US2_SUBJECTS}
    seal=seal_inputs(owners,subjects=list(job.US2_SUBJECTS),semantics_version=SEMANTICS)
    result=compose(owners,subjects=list(job.US2_SUBJECTS),generations={t:'SYNTHETIC_US2' for t in owners},
        input_seal=seal,input_seal_sha256=seal['receipt_sha256'],semantics_version=SEMANTICS)
    assert result['coverage']['coverage_complete'] and result['census'] is not None
    assert {r['ticker'] for r in result['coverage']['rows']}==set(job.US2_SUBJECTS)


def test_two_subject_original_monitoring_owner_and_model_plan(tmp_path,monkeypatch):
    from tests.test_c22ad_lifecycle import admitted_source
    from app.services.model_execution_plan import compile_model_plan
    from app.services.research_no_send_run import MarketResearchChild
    source,owner,cohort,_,_,_=admitted_source(tmp_path,monkeypatch,subjects=job.US2_SUBJECTS)
    plan=compile_model_plan(cohort,topology='CANONICAL_PRODUCTION')
    child=MarketResearchChild(plan,owner);child.verify()
    assert set(source['stocks'])==set(source['prepared'])==set(job.US2_SUBJECTS)
    assert all(v['mode']=='EVIDENCE_BASED' for v in source['prepared'].values())
    assert b2_retry_binding(plan,B2_US2_DIAGNOSTIC_V1)['maximum']==8 and len(plan.slots)==6
    owner.close()


def test_actual_us2_and_kr_once_capture_freeze_pre_http(tmp_path,monkeypatch):
    from tests.test_local_launchd_entry import original_cycle_probe
    from app.services.selected_source_plan import request_budget,SelectedRequestPlan
    for market,tag in (('us','us2-20261120-1234abcd'),('kr','kr-20261120-1234abcd')):
        with monkeypatch.context() as patch:
            def runtime(execution):
                p=tmp_path/'private'/execution;p.mkdir(parents=True,mode=0o700);return p
            patch.setattr(job,'_local_model_runtime',runtime)
            result=original_cycle_probe(tmp_path/market,market,patch,one_shot_tag=tag)
            assert result['financial_HTTP']==result['models']==0
            frozen=json.loads((tmp_path/market/'source/production-frozen-source-plan.json').read_bytes())
            assert set(frozen['plan']['subjects'])==set(job.US2_SUBJECTS if market=='us' else ('000660','003690','005490','005930','010120','012450','047810','086280'))
            if market=='us':
                receipt=json.loads((tmp_path/market/'us2-before-http.json').read_bytes())
                assert receipt['financial_subjects']==list(job.US2_SUBJECTS)
                assert receipt['actual_plan_budget']['total']<=sum(job.US2_CAPS.values())
            else:assert (tmp_path/market/'source/kis-plan.json').is_file()


def test_full14_retry_budget_unchanged_and_news_subset_disclosure():
    from app.services.unified_stock_acquisition import UNIVERSE
    from app.services.model_execution_plan import compile_model_plan
    from app.services.selected_news_rate_limit import disclose,STATUS,PROVIDER
    p=old.listed_plan(UNIVERSE['us']);full=compile_model_plan(replace(p.cohort,limitation_subjects=('SKHY',)),topology='CANONICAL_PRODUCTION')
    binding=b2_retry_binding(full)
    assert (binding['base_slots'],len(binding['b2_slots']),binding['maximum'])==(29,13,42)
    events=[dict(binding=dict(denial=STATUS,provider=PROVIDER,evidence=[],rate_limit=dict(subject=t))) for t in job.US2_SUBJECTS]
    assert all(t in disclose(dict(text='Synthetic market'),events,expected_count=2)['text'] for t in job.US2_SUBJECTS)
    with pytest.raises(ValueError):disclose(dict(text='Synthetic market'),events,expected_count=14)


def test_exact_day_kr_and_us2_tags_regular_rules_and_consumed_once(tmp_path,monkeypatch):
    from app.services.unified_market_run import target_session
    from tests.test_local_launchd_entry import configuration,code_pin
    now=datetime.fromisoformat('2026-11-20T20:00:00+09:00')
    assert str(job.latest_one_shot_session('kr',now))=='2026-11-20'
    assert str(job.latest_one_shot_session('us',now))=='2026-11-19'
    assert job.latest_one_shot_session('kr',datetime.fromisoformat('2026-11-21T00:01:00+09:00')) is None
    assert job.latest_one_shot_session('kr',datetime.fromisoformat('2026-11-20T15:29:00+09:00')) is None
    assert target_session('us',now) is None and str(target_session('kr',now))=='2026-11-20'
    assert job.one_shot_scope('us','us2-20261120-1234abcd')
    with pytest.raises(ValueError):job.one_shot_scope('kr','us2-20261120-1234abcd')
    code_pin(monkeypatch);path,_=configuration(tmp_path,'kr');calls=[]
    async def cycle(*a,**k):calls.append(1);return dict(status='RENDER_VERIFIED_NO_SEND',normal_messages_sent=False)
    monkeypatch.setattr(job,'_local_registered_cycle',cycle)
    tag='kr-20261120-1234abcd'
    assert asyncio.run(job.run_local_scheduled(path,'kr',now=now,one_shot_tag=tag))['status']=='RENDER_VERIFIED_NO_SEND'
    assert asyncio.run(job.run_local_scheduled(path,'kr',now=now,one_shot_tag=tag))['reason']=='SESSION_ALREADY_CONSUMED'
    assert len(calls)==1
