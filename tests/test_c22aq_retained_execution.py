"""New approval consumes old exact rows, never old authorization or execution."""
from copy import deepcopy
from datetime import datetime,timedelta,timezone
from types import SimpleNamespace

import pytest

from app.services.unified_snapshot_contract import digest


def test_new_approval_exact_retained_capture_no_backdate_or_old_ledger_reset(tmp_path,monkeypatch):
    from tests.test_c22an_registration_and_cohorts import synthetic_campaign
    from tests.test_minimal_class_c_export import POLICY
    from app.services import selected_source_registration as capture
    from app.services import prospective_class_c_owner as original
    from app.services.minimal_class_c_export import captured_source_cutoff
    from app.services.selected_run_lifecycle import SelectedRunLedger
    c=synthetic_campaign(tmp_path,monkeypatch)
    c.now[0]=datetime(2026,11,12,8,0,tzinfo=timezone.utc)
    args=dict(settings=SimpleNamespace(database_url='sqlite:///'+str(c.permission.database)),
        runtime_directory=tmp_path,generations={'kr':'SYNTHETIC_kr'},policy=POLICY,enabled=True)
    _,_,prior=capture.capture_approved_markets(**args,approval=c.approval,ledger=c.ledger)
    c.ledger.stop('OLD_FAILURE_MUST_REMAIN');old=c.ledger.path.read_bytes()
    c.now[0]+=timedelta(hours=2)
    decision=original.ApprovalDecision(event_id='SYNTHETIC_NEW_APPROVAL',approved=True,
        user_message_sha256=digest('NEW_SYNTHETIC_APPROVAL_NOT_LIVE'),effective_at=c.now[0],
        expires_at=c.now[0]+timedelta(hours=3),subjects=c.permission.subjects)
    approval=original.record_backend_approval(decision)
    children=deepcopy(c.ledger.identity['children'])
    children['kr'].update(retained_capture_sha256=digest(prior),execution_generation='NEW_EXECUTION_kr')
    ledger=SelectedRunLedger(path=tmp_path/'new-ledger.jsonl',approval=approval,master_id='NEW_EXECUTION',
        children=children,provider_caps={'sec_edgar':3},max_http=3,max_models=41,
        database_identity=c.ledger.identity['database_identity'],staged_markets=True,
        runtime_cap=c.ledger.identity['runtime_cap'])
    changed={**prior,'original_rows_sha256':'0'*64}
    with pytest.raises(ValueError,match='pin_required'):
        capture.capture_approved_markets(**args,approval=approval,ledger=ledger,reference_captures={'kr':changed})
    assert ledger.state()['db_connection_attempts']==0
    value,owners,receipt=capture.capture_approved_markets(**args,approval=approval,ledger=ledger,
        reference_captures={'kr':prior})
    _,owned=original._state(owners['kr'])
    assert receipt['permission_event']=='SYNTHETIC_NEW_APPROVAL'
    assert receipt['cutoff']!=prior['cutoff'] and owned['cutoff']==prior['cutoff']
    assert owned['effective_at']==owned['retained_consumption_authorized_at']==decision.effective_at.isoformat()
    assert owned['issued_at']>=owned['effective_at']>owned['cutoff']
    assert original.replay_captured_local_seed(owners['kr'],policy=POLICY)
    with pytest.raises(ValueError,match='exact_original_rows'):
        captured_source_cutoff(value,reference_capture=prior)
    assert captured_source_cutoff(value,reference_capture=prior,retained_capture_sha256=digest(prior))==prior['cutoff']
    assert ledger.state()['db_connection_attempts']==1 and ledger.state()['db_select_actual']==5
    assert c.ledger.path.read_bytes()==old
    with pytest.raises(ValueError):capture.capture_approved_markets(**args,approval=approval,ledger=ledger,reference_captures={'kr':prior})
    assert ledger.state()['db_connection_attempts']==1


def test_original_subject_and_stage_owner_separate_source_and_execution(tmp_path,monkeypatch):
    from app.services import scoped_monitoring_research as scoped
    from tests.test_c22ad_lifecycle import admitted_source
    original=scoped.prepare_scoped_research_source
    def prepare(**kwargs):return original(**kwargs,execution_generation='NEW_C22AQ_SYNTHETIC_EXECUTION')
    monkeypatch.setattr(scoped,'prepare_scoped_research_source',prepare)
    source,owner,cohort,registration,ledger,decision=admitted_source(tmp_path,monkeypatch)
    assert source['source_generation_id']=='US_CHILD'
    assert cohort.source_generation=='US_CHILD' and cohort.run_id=='NEW_C22AQ_SYNTHETIC_EXECUTION'
    assert source['prepared']['MU']['initial_chain']['source_generation_id']=='US_CHILD'
    assert source['prepared']['MU']['initial_chain']['execution_generation_id']==cohort.run_id
    assert owner.acceptance()['generation_id']==cohort.run_id
    cohort.verify_source_owner(owner)
    from app.services.model_execution_plan import compile_model_plan
    from app.services.production_model_profile import SolHighCallBudget
    plan=compile_model_plan(cohort,topology='CANONICAL_PRODUCTION')
    budget=SolHighCallBudget(plan=plan,approved_max_invocations=len(plan.slots),approved_plan_sha256=plan.sha256,
        journal_path=tmp_path/'new-invocation-ledger.jsonl')
    assert budget.state()['consumed']==0 and plan.slots[0].source_generation=='US_CHILD'
    owner.close()
