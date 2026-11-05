"""C9 changed boundaries only: no live HTTP, model or operating database."""
import json
import hashlib,os
from pathlib import Path
from datetime import datetime,timezone
from copy import deepcopy

import pytest

from app.services import prospective_class_c_owner as owner,pending_source_intake as intake
from app.services.minimal_class_c_export import captured_private_snapshot,MODELS
from app.services.unified_source_policy import UnifiedSourcePolicy
from app.services.onboarding_readiness_service import evaluate_source_intake
from app.services.vnext_composite_research import CompositeView
from app.services.vnext_research_store import ResearchStore
from test_c8_source_intake import pending
from test_minimal_class_c_export import POLICY


@pytest.mark.parametrize('field,value,code,probe',[
    ('identity_provider','','IDENTITY_PROVIDER_MISSING',True),
    ('identity_provider','mock','IDENTITY_PROVIDER_PROHIBITED',False),
    ('identity_quality','missing','IDENTITY_QUALITY_UNVERIFIED',True),
    ('identity_provider','Massive','IDENTITY_PROVIDER_PROHIBITED',False),
])
def test_separate_actual_provenance_operand(tmp_path,field,value,code,probe):
    _,_,_,r=pending(tmp_path,mutation=f"UPDATE securitymaster SET {field}='{value}'")
    subject=r['subjects']['NEWUS']
    assert code in subject['denials'] and subject['identity_probe_eligible']==probe
    assert not subject['registered_source_intake_eligible']


def prepared(tmp_path):
    approval,capture,handle,receipt=pending(tmp_path)
    decision=owner._approval(approval)
    scope=intake.record_backend_intake_scope(approval=approval,generation_id='C8_TEST',source_generation_id='C8_TEST',
        exclusive_use_confirmed=True,confirmation_sha256='b'*64,confirmed_at=decision.effective_at,enabled=True)
    adapted,document=intake.adapt_registered_intake(scope=scope,source_intake_owner=handle,
        subjects=('NEWUS',),policy=POLICY,enabled=True)
    return approval,capture,handle,adapted,document


def test_original_pending_adapter_can_consume_us_only_subset(tmp_path):
    _,_,_,adapted,document=prepared(tmp_path)
    result=intake.consume_intake(adapted,generation_id='C8_TEST',role='adjusted_daily',
        security_ids=('security:NEWUS',),session=document['calendar']['target'])
    assert result['contract']=='registered-source-intake-pending-adapter-v1'
    assert not any(result[k] for k in ('ACTIVE','production_eligible','MarketParent','native','valuation','send'))
    with pytest.raises(ValueError):owner.require_generation(adapted,'C8_TEST')


@pytest.mark.parametrize('change',['generation','role','subject','session','revoked','forged'])
def test_adapter_does_not_restore_or_broaden_authority(tmp_path,change):
    _,_,original,adapted,doc=prepared(tmp_path)
    if change=='revoked':owner.revoke_source_intake(original)
    if change=='forged':adapted=deepcopy(doc)
    with pytest.raises((ValueError,TypeError)):
        intake.consume_intake(adapted,generation_id='OTHER' if change=='generation' else 'C8_TEST',
            role='financial' if change=='role' else 'adjusted_daily',
            security_ids=('OTHER',) if change=='subject' else ('security:NEWUS',),
            session='2000-01-01' if change=='session' else doc['calendar']['target'])


def test_canonical_local_policy_remains_explicit(tmp_path):
    _,capture,_,_=pending(tmp_path)
    raw,_=captured_private_snapshot(capture);rows=json.loads(raw)
    data={t:MODELS[t].model_validate(v[0]) for t,v in rows.items()}
    r=evaluate_source_intake(data['watchlistitem'],data['securitymaster'],data['company'],data['investmentthesis'],
        cutoff=datetime.now(timezone.utc),policy=UnifiedSourcePolicy(frozenset({'sec_edgar'})))
    assert r['denials']==['POLICY_CANONICAL_LOCAL_NOT_PERMITTED'] and not r['identity_probe_eligible']


def test_same_composite_engine_reads_pending_intake_without_fake_active_rows(tmp_path):
    _,_,handle,_,_=prepared(tmp_path)
    store=ResearchStore(tmp_path/'derived.sqlite3')
    at=datetime.now(timezone.utc).isoformat()
    with store.connect() as c:c.execute('INSERT INTO research_run VALUES(?,?,?,?)',('ORIGINAL',at,at,'SOURCE_REFERENCE'))
    view=CompositeView(store,as_of=at,tickers=['NEWUS'],registration_owner=handle,
        registration_generation='C8_TEST',registration_policy=POLICY)
    packet=view.packet('NEWUS')
    assert packet['public_security']['canonical_security_id']=='security:NEWUS'
    assert not packet['evidence'] and not packet['send'] and not packet['strict_ready']
    with store.connect() as c:assert c.execute('SELECT count(*) FROM watchlistitem').fetchone()==(0,)
    assert view.registration_admission['purpose']=='RESEARCH_NO_SEND'


@pytest.mark.parametrize('change',['forged','wrong_generation','outside_subject','policy'])
def test_composite_intake_fails_before_data_use(tmp_path,change):
    _,_,handle,_,_=prepared(tmp_path)
    store=ResearchStore(tmp_path/'derived.sqlite3')
    with pytest.raises((ValueError,TypeError)):
        CompositeView(store,as_of=datetime.now(timezone.utc).isoformat(),
            tickers=['OTHER' if change=='outside_subject' else 'NEWUS'],
            registration_owner=owner.SourceIntakeOwner() if change=='forged' else handle,
            registration_generation='OTHER' if change=='wrong_generation' else 'C8_TEST',
            registration_policy=UnifiedSourcePolicy(frozenset()) if change=='policy' else POLICY)


def scoped_wire():
    from app.services.scoped_source_plan import ScopedConfig,HistoryCounts,ScopedSubject,ScopedCaptureSelectionV2,compile_scoped_wire_contract
    counts=HistoryCounts(**{r:2 for r in ('adjusted_daily','adjusted_weekly','adjusted_monthly','unadjusted_weekly_valuation')})
    config=ScopedConfig(subjects=(ScopedSubject(ticker='NEWUS',market='us',security_id='security:NEWUS',issuer_id='1234',venue='NASDAQ',currency='USD'),),
        kr_history=counts,us_history=counts,kr_max_pages=2,
        capture_selection=ScopedCaptureSelectionV2(contract='scoped-capture-selection-v2',
            stock_markets=('us',),stock_security_ids=('security:NEWUS',),stock_roles=('adjusted_daily',),
            market_contexts=(),us_completed_closes=False))
    identity=dict(ticker='NEWUS',canonical_security_id='security:NEWUS',exchange='NASDAQ')
    at=datetime.now(timezone.utc)
    wire=compile_scoped_wire_contract(config=config,identities={'NEWUS':identity},generation_id='C8_TEST',
        at=at,code_sha='a'*40,provider_config_sha256='b'*64,retries=0)
    stock=dict(contract='current-scoped-stock-capture-v1',run_id='C8_TEST',acquisition_id='source',frozen_at=at.isoformat(),
        reads=[r.model_dump(mode='json') for r in wire['stock_reads']],owner_files={'synthetic.py':'c'*64})
    return config,wire,stock,at


def test_historical_scoped_worker_plan_preserves_exact_original_bytes():
    from app.services.vnext_dated_technical_owner import CapturedScopedStockPlan
    _,wire,stock,_=scoped_wire()
    model=CapturedScopedStockPlan(stock)
    assert model.model_dump(mode='json')==stock
    assert all(d.transient_retry_max==0 for d in wire['request_plan'].descriptors)


def test_scoped_historical_plan_cannot_change_after_receipt_binding():
    from app.services.vnext_dated_technical_owner import CapturedScopedStockPlan
    _,_,stock,_=scoped_wire()
    model=CapturedScopedStockPlan(stock)
    stock['run_id']='TAMPERED'
    assert model.run_id=='C8_TEST'
    with pytest.raises(AttributeError):model.run_id='TAMPERED'


@pytest.mark.parametrize('change',['contract','extra','duplicate'])
def test_scoped_history_cannot_claim_another_plan_or_role(change):
    from app.services.vnext_dated_technical_owner import CapturedScopedStockPlan
    _,_,stock,_=scoped_wire()
    if change=='contract':stock['contract']='production-source-run-binding-v1'
    if change=='extra':stock['dispatch_allowed']=True
    if change=='duplicate':stock['reads']*=2
    with pytest.raises(ValueError):CapturedScopedStockPlan(stock)


def test_new_intake_reaches_original_us_only_pending_parent(tmp_path,monkeypatch):
    from app.services import kiwoom_global_lane as lane,pending_source_parent as parent
    from app.services import current_scoped_source_dispatch,current_scoped_worker_bridge,scoped_worker_launch,sealed_source_transport
    from app.services.kiwoom_participant_session import ParticipatingSession
    _,_,_,adapted,_=prepared(tmp_path)
    directory=tmp_path/'TEST_ONLY_LANE';directory.mkdir(mode=0o700)
    monkeypatch.setattr(lane,'boot_identity',lambda:'C9_TEST_ONLY_SYNTHETIC_BOOT')
    boot=lane.boot_identity()
    lane._atomic(directory/'activation.json',dict(protocol=lane.PROTOCOL,generation='C9_SYNTHETIC',boot_identity=boot,
        implementation_sha256=hashlib.sha256(Path(lane.__file__).read_bytes()).hexdigest()))
    lane._atomic(directory/'state.json',dict(protocol=lane.PROTOCOL,generation='C9_SYNTHETIC',boot_identity=boot,
        last_end=None,in_flight=False,halted=False,sequence=0,pid=os.getpid()))
    fd=os.open(directory/'lane.lock',os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600);os.close(fd)
    monkeypatch.setenv('KIWOOM_GLOBAL_LANE_REQUIRED','1');monkeypatch.setattr(lane,'_loaded_lane',lane.GlobalKiwoomLane(directory,boot=lane.boot_identity))
    session=ParticipatingSession(modules=(current_scoped_source_dispatch,current_scoped_worker_bridge,scoped_worker_launch,sealed_source_transport),caller_kind='CLI')
    config,_,_,at=scoped_wire()
    handle,wire=parent.issue_parent(intake_owner=adapted,config=config,session=session,
        generation_id='C8_TEST',cutoff=at,code_sha='a'*40,provider_config_sha256='b'*64,maximum_attempts=20,enabled=True)
    assert parent.resolve_parent(handle)['scope']=='SCOPED_SOURCE_ONLY_PENDING'
    assert {r.market for r in wire['stock_reads']}=={'us'}
    assert parent.public_handoff(handle)['plan_sha256']==wire['request_plan'].plan_sha256
    parent.revoke_parent(handle)
