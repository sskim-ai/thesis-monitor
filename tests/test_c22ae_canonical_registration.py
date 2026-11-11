"""New v2 contracts only: synthetic rows/wires, no current DB or model calls."""
from copy import deepcopy
from datetime import datetime,timedelta,timezone
import json
import sqlite3
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pytest

from app.services import prospective_class_c_owner as reg
from app.services.minimal_class_c_export import captured_private_snapshot,project_captured_export
from app.services.onboarding_readiness_service import canonical_registration_eligibility
from app.services.selected_source_registration import capture_approved_markets
from app.services.selected_run_lifecycle import SelectedRunLedger
from app.services.unified_snapshot_contract import digest
from tests.test_minimal_class_c_export import database,POLICY


def setup(tmp_path,subjects=(('NEWUS','us'),('999999','kr')),mutate=None):
    tmp_path.mkdir(parents=True,exist_ok=True)
    p=database(tmp_path,list(subjects))
    if mutate:
        with sqlite3.connect(p.database) as db:mutate(db)
    now=datetime.now(timezone.utc)
    approval=reg.record_backend_approval(reg.ApprovalDecision(event_id='OFFLINE_ONE_EVENT',approved=True,
        user_message_sha256=digest('OFFLINE_SYNTHETIC_NOT_HUMAN_APPROVAL'),effective_at=now-timedelta(seconds=1),
        expires_at=now+timedelta(hours=3),subjects=p.subjects))
    children={m:dict(generation='OFFLINE_'+m.upper(),subjects=sorted(t for t,k in subjects if k==m)) for m in ('us','kr')}
    ledger=SelectedRunLedger(path=tmp_path/'budget.jsonl',approval=approval,master_id='OFFLINE_MASTER',children=children,
        provider_caps={'kis':4,'kiwoom':1},max_http=5,max_models=100,
        database_identity=dict(path=str(p.database),device=p.device,inode=p.inode))
    settings=SimpleNamespace(database_url='sqlite:///'+str(p.database))
    return p,approval,children,ledger,settings


def capture(tmp_path,**kwargs):
    p,approval,children,ledger,settings=setup(tmp_path,**kwargs)
    result=capture_approved_markets(settings=settings,runtime_directory=tmp_path,approval=approval,
        generations={m:c['generation'] for m,c in children.items()},policy=POLICY,ledger=ledger,
        audit_path=tmp_path/'audit.json',enabled=True)
    return p,approval,children,ledger,result


def test_one_canonical_capture_cached_before_two_owners_and_private_safe(tmp_path,monkeypatch):
    import app.services.onboarding_readiness_service as canonical
    original=canonical.canonical_registration_eligibility;calls=[]
    def observed(**kw):
        calls.append(kw['ticker']);return original(**kw)
    monkeypatch.setattr(canonical,'canonical_registration_eligibility',observed)
    p,approval,children,ledger,(handle,owners,receipt)=capture(tmp_path)
    assert sorted(calls)==sorted(p.subjects) and ledger.state()['db_select_actual']==5
    assert set(owners)=={'us','kr'} and len({id(o) for o in owners.values()})==2
    audit=json.loads((tmp_path/'audit.json').read_text())
    assert all(r['canonical_eligible'] for r in audit['subjects'])
    assert 'selected private' not in (tmp_path/'audit.json').read_text()
    assert all(r['row_present']['active_investmentthesis'] for r in audit['subjects'])
    for m,o in owners.items():
        document,row=reg._state(o)
        assert document==project_captured_export(handle,market=m,session_key=row['calendar']['target'],policy=POLICY)
    assert len(calls)==2
    with sqlite3.connect(p.database) as db:db.execute("UPDATE watchlistitem SET active=0")
    assert all(r['canonical_eligible'] for r in audit['subjects'])
    for m,o in owners.items():reg.require_generation(o,children[m]['generation'])
    with pytest.raises(ValueError,match='unissued_capture'):
        project_captured_export(audit,market='us',session_key='2026-11-10',policy=POLICY)


def test_missing_and_inactive_reasons_are_observed_not_inferred(tmp_path):
    cases=[('MISSING_WATCHLIST',"DELETE FROM watchlistitem WHERE ticker='NEWUS'"),
        ('INACTIVE_MONITORING',"UPDATE watchlistitem SET active=0 WHERE ticker='NEWUS'"),
        ('MONITORING_NOT_REQUESTED',"UPDATE watchlistitem SET monitoring_requested=0 WHERE ticker='NEWUS'"),
        ('ONBOARDING_NOT_ACTIVE',"UPDATE watchlistitem SET onboarding_state='PENDING_ONBOARDING' WHERE ticker='NEWUS'"),
        ('PRODUCTION_NOT_ELIGIBLE',"UPDATE watchlistitem SET production_eligible=0 WHERE ticker='NEWUS'"),
        ('MISSING_SECURITY_IDENTITY',"DELETE FROM securitymaster WHERE ticker='NEWUS'"),
        ('MISSING_ACTIVE_THESIS',"DELETE FROM investmentthesis WHERE ticker='NEWUS'"),
        ('FIRST_ELIGIBLE_SESSION_NOT_REACHED',"UPDATE watchlistitem SET first_eligible_session='2099-01-01' WHERE ticker='NEWUS'"),
        ('ACTIVATED_AFTER_CUTOFF',"UPDATE watchlistitem SET activated_at='2099-01-01' WHERE ticker='NEWUS'"),
        ('MARKET_CLASSIFICATION_MISMATCH',"UPDATE securitymaster SET exchange='KOSPI' WHERE ticker='NEWUS'")]
    for i,(reason,sql) in enumerate(cases):
        folder=tmp_path/str(i)
        p,approval,children,ledger,settings=setup(folder,mutate=lambda db:db.execute(sql))
        with pytest.raises(ValueError):
            capture_approved_markets(settings=settings,runtime_directory=folder,approval=approval,
                generations={m:c['generation'] for m,c in children.items()},policy=POLICY,ledger=ledger,
                audit_path=folder/'audit.json',enabled=True)
        audit=json.loads((folder/'audit.json').read_text())
        row=next(r for r in audit['subjects'] if r['ticker']=='NEWUS')
        assert reason in row['excluded_reasons']+row['scope_denials']
        assert ledger.state()['http_total']==ledger.state()['model_total']==0
        assert ledger.state()['db_select_actual']==5


def test_empty_and_outside_approval_have_distinct_original_failures(tmp_path):
    p,approval,children,ledger,settings=setup(tmp_path,mutate=lambda db:db.execute("UPDATE watchlistitem SET active=0 WHERE ticker='NEWUS'"))
    with pytest.raises(ValueError,match='NO_ELIGIBLE_SUBJECT_FOR_MARKET'):
        capture_approved_markets(settings=settings,runtime_directory=tmp_path,approval=approval,
            generations={m:c['generation'] for m,c in children.items()},policy=POLICY,ledger=ledger,
            audit_path=tmp_path/'audit.json',enabled=True)
    # A separate synthetic capture, not a second live query or grant refill.
    _,_,_,_,(handle,_,_)=capture(tmp_path/'other')
    decision=reg.ApprovalDecision(event_id='OFFLINE_OTHER_SCOPE',approved=True,user_message_sha256=digest('other'),
        effective_at=datetime.now(timezone.utc)-timedelta(seconds=1),expires_at=datetime.now(timezone.utc)+timedelta(minutes=5),
        subjects=('NOT_REGISTERED',))
    with pytest.raises(ValueError,match='ELIGIBLE_SUBJECT_OUTSIDE_APPROVAL'):
        reg.issue_prospective_owner(approval=reg.record_backend_approval(decision),capture=handle,market='us',
            generation_id='OTHER_SCOPE',source_generation_id='OTHER_SCOPE',policy=POLICY)


def test_same_rules_for_selected_full_and_added_removed_cohort(tmp_path):
    from app.services.model_execution_plan import CohortSubject,FrozenCohort,compile_model_plan
    subjects=tuple([(str(100000+i),'kr') for i in range(8)]+[('NEW'+str(i),'us') for i in range(14)])
    _,_,_,_,(handle,owners,receipt)=capture(tmp_path,subjects=subjects)
    versions={}
    for m,o in owners.items():
        doc,row=reg._state(o)
        for r in doc['universe']['eligibility_audit']:versions[r['ticker']]=r
    assert len(versions)==22 and all(r['canonical_eligible'] for r in versions.values())
    for ids in ([subjects[0][0],subjects[-1][0]],[t for t,m in subjects],[t for t,m in subjects[:-1]]):
        selected=[versions[t] for t in ids]
        assert all(r['canonical_eligible'] for r in selected)
        at=receipt['cutoff'];c=FrozenCohort('OFFLINE_COHORT','OFFLINE_SOURCE','2026-09-25',at,at,
            tuple(CohortSubject(r['detected_market'],r['ticker'],'security:'+r['ticker'],at,digest(r)) for r in selected),
            tuple((m,digest('PLANNING_ONLY')) for m in sorted({r['detected_market'] for r in selected})),digest(ids))
        plan=compile_model_plan(c,topology='CANONICAL_PRODUCTION')
        assert len(plan.slots)==len(c.market_subjects)+3*sum((len(ts)+2)//3 for ts in c.market_subjects.values())+len(ids)
    assert all(r['contract']=='canonical-monitoring-registration-v1' for r in versions.values())


def test_shared_worker_attaches_without_grant_refill_and_backend_revoke_stops(tmp_path):
    p,approval,children,ledger,(handle,owners,receipt)=capture(tmp_path)
    for m in ('us','kr'):ledger._event('PLAN',market=m,sha256=digest(m))
    binding=ledger.worker_binding();worker=SelectedRunLedger.attach_worker(binding)
    key=worker.before_http(market='kr',provider='kis',logical_id='auth',plan_sha256=digest('kr'))
    worker.result(key,ok=True)
    assert ledger.state()['http_total']==1
    reg.revoke_approval(approval)
    with pytest.raises(ValueError,match='terminal'):
        worker.before_http(market='kr',provider='kis',logical_id='next',plan_sha256=digest('kr'))
    assert ledger.state()['state']=='STOPPED_NO_SEND' and ledger.state()['http_total']==1
    bad=dict(binding,identity_sha256='0'*64)
    with pytest.raises(ValueError,match='identity_changed'):SelectedRunLedger.attach_worker(bad)


@pytest.mark.parametrize('mode,physical', [('cap',4),('ttl',0),('transport',1),('forbidden',1)])
def test_original_kis_guarded_transport_counts_before_wire_in_separate_process(tmp_path,mode,physical):
    _,_,_,ledger,_=capture(tmp_path)
    for m in ('us','kr'):ledger._event('PLAN',market=m,sha256=digest(m))
    binding=tmp_path/'binding.json';binding.write_text(json.dumps(ledger.worker_binding()))
    output=tmp_path/'wire.json';repo=Path(__file__).resolve().parents[1]
    env=dict(os.environ,THESIS_MONITOR_ENV_FILE='',DATABASE_URL='sqlite://',PYTHONDONTWRITEBYTECODE='1',PYTHONPATH=str(repo))
    child=subprocess.run([sys.executable,'-B',str(repo/'tests/c22ae_kis_wire_probe.py'),str(binding),str(output),mode],
        cwd=repo,env=env,capture_output=True,timeout=30)
    assert child.returncode==0,child.stderr.decode()
    observed=json.loads(output.read_bytes())
    assert observed['sent']==physical==ledger.state()['http_total']
    assert ledger.state()['model_total']==0 and observed['real_HTTP']==0
    if mode=='cap':assert 'scope_or_budget' in observed['terminal']
    if mode=='ttl':assert 'window_expired' in observed['terminal']
    if mode in ('transport','forbidden'):assert observed['state']=='STOPPED_NO_SEND'


def test_added_registered_subject_changes_plan_not_canonical_rule(tmp_path):
    from app.models.security import SecurityMaster
    from app.services.selected_source_plan import build_stock_plan,COUNTS
    from app.services.selected_source_composition import SelectedSourceRunBinding
    subjects=tuple(('NEW'+str(i),'us') for i in range(23))+ (('999999','kr'),)
    _,_,_,_,(handle,owners,receipt)=capture(tmp_path,subjects=subjects)
    raw,_=captured_private_snapshot(handle)
    identities={r['ticker']:SecurityMaster.model_validate(r).model_dump(mode='json')
        for r in json.loads(raw)['securitymaster'] if r['ticker'].startswith('NEW')}
    plan=build_stock_plan(market='us',identities=identities,at=datetime.fromisoformat(receipt['cutoff']),
        generation='OFFLINE_EXPANDED',code_sha='1'*40,counts=COUNTS)
    assert len(plan.subjects)==23 and len(plan.reads)==23*4
    doc,_=reg._state(owners['us'])
    assert len(doc['universe']['eligible_subjects'])==23
    assert all(r['canonical_eligible'] for r in doc['universe']['eligibility_audit'])
    assert SelectedSourceRunBinding.model_fields['subjects'].metadata==type(plan).model_fields['subjects'].metadata


def test_selected_source_cannot_omit_one_campaign_accounting():
    from app.services.selected_source_context import freeze_registered_child
    from app.services.selected_source_dispatch import SelectedSourceDispatcher
    with pytest.raises(ValueError,match='one_campaign_ledger_required'):
        freeze_registered_child(registration_owner=None,policy=POLICY,code_sha='1'*40,native={},native_owner_root='.',
            config_identities={},configured_kr_pages=20,listing_rows=[],kis_static_hashes={},enabled=True)
    with pytest.raises(ValueError,match='one_campaign_ledger_required'):
        SelectedSourceDispatcher(plan={},compiler_args={},kis_plan=None,registration_owner=None,policy=POLICY,
            config_identities={},credential_presence={},repository_root='.',root='.',
            approved_plan_sha256='0'*64,approved_provider_caps={},guard=lambda:None,enabled=True)


def test_identity_provider_denial_does_not_erase_observed_registration_audit(tmp_path):
    from app.services.unified_source_policy import UnifiedSourcePolicy
    _,approval,children,ledger,settings=setup(tmp_path)
    with pytest.raises(ValueError):
        capture_approved_markets(settings=settings,runtime_directory=tmp_path,approval=approval,
            generations={m:c['generation'] for m,c in children.items()},
            policy=UnifiedSourcePolicy(frozenset({'canonical_local'})),ledger=ledger,
            audit_path=tmp_path/'audit.json',enabled=True)
    audit=json.loads((tmp_path/'audit.json').read_bytes())
    assert all(r['canonical_eligible'] for r in audit['subjects'])
    assert all(v['original_source_role_denials'][0]['reason']=='identity_provider_not_permitted'
        for v in audit['markets'].values())
    assert ledger.state()['http_total']==ledger.state()['model_total']==0


def test_reserved_preconnect_argument_failure_keeps_one_actual_connection(tmp_path):
    _,approval,children,ledger,settings=setup(tmp_path)
    ledger._event('DB_INTENT');ledger._event('DB_OPEN');ledger.stop('OBSERVED_ARGUMENT_BIND_FAILURE_HTTP_DB_ZERO')
    ledger.correct_preopen_wiring(evidence_sha256=digest('SYNTHETIC_CALLBACK_NEVER_ENTERED'),
        observed_connections=0,observed_selects=0,reserved_argument_failure=True)
    counts=[]
    def connect(database_uri,**kwargs):
        counts.append(True)
        assert len(counts)==1
        return sqlite3.connect(database_uri,**kwargs)
    capture_approved_markets(settings=settings,runtime_directory=tmp_path,approval=approval,
        generations={m:c['generation'] for m,c in children.items()},policy=POLICY,ledger=ledger,
        audit_path=tmp_path/'audit.json',enabled=True,connect=connect)
    state=ledger.state()
    assert len(counts)==state['db_connection_attempts']==1
    assert state['db_select_actual']==5 and state['reserved_connection_continued']
    with pytest.raises(ValueError):ledger.correct_preopen_wiring(evidence_sha256=digest('second'),
        observed_connections=0,observed_selects=0,reserved_argument_failure=True)


def test_custom_connector_argument_binding_fails_before_reserving_open(tmp_path):
    _,approval,children,ledger,settings=setup(tmp_path)
    def bad_connector(uri,**kwargs):pytest.fail('callback must not be entered')
    with pytest.raises(TypeError):
        capture_approved_markets(settings=settings,runtime_directory=tmp_path,approval=approval,
            generations={m:c['generation'] for m,c in children.items()},policy=POLICY,ledger=ledger,
            audit_path=tmp_path/'audit.json',enabled=True,connect=bad_connector)
    assert ledger.state()['db_connection_attempts']==ledger.state()['db_select_actual']==0


def test_absent_registration_does_not_invent_a_wrong_market(tmp_path):
    p,approval,children,ledger,settings=setup(tmp_path,mutate=lambda db:db.execute("DELETE FROM watchlistitem WHERE ticker='NEWUS'"))
    with pytest.raises(ValueError,match='NO_ELIGIBLE_SUBJECT_FOR_MARKET'):
        capture_approved_markets(settings=settings,runtime_directory=tmp_path,approval=approval,
            generations={m:c['generation'] for m,c in children.items()},policy=POLICY,ledger=ledger,
            audit_path=tmp_path/'audit.json',enabled=True)
    row=next(r for r in json.loads((tmp_path/'audit.json').read_bytes())['subjects'] if r['ticker']=='NEWUS')
    assert row['detected_market'] is None and row['scope_denials']==[]
    assert row['market_classification_state']=='NOT_OBSERVED_MISSING_REGISTRATION'
    assert row['excluded_reasons']==['MISSING_WATCHLIST']
