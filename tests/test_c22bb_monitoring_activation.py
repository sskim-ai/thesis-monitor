import asyncio
import json
import sqlite3
from collections import Counter
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from zipfile import ZipFile

import pytest
from sqlalchemy import event
from sqlmodel import SQLModel, Session, create_engine, select

from app.models.company import Company
from app.models.security import SecurityMaster
from app.models.thesis import InvestmentThesis, ThesisAssessment
from app.models.watchlist import WatchlistItem
from app.services import onboarding_readiness_service as readiness
from app.services import research_no_send_run as research
from app.services.model_execution_plan import CohortSubject, FrozenCohort, compile_model_plan
from app.services.onboarding_reconciler_service import OnboardingAttemptMode, resume_onboarding_subject
from app.services.unified_persisted_projection import project_local_seed
from app.services.production_source_context import POLICY
from app.services.unified_snapshot_contract import digest
from app.services.unified_stock_acquisition import UNIVERSE
from tests.test_onboarding_readiness_service import _engine, _seed_ready_prerequisites


PENDING = {'IBM','SKHY','SNDK','TSM'}
AT = datetime(2026,11,13,10,30,tzinfo=UTC)
FIRST_CYCLE = date(2026,11,14)  # Saturday KST, after the US Friday close.


def seed(session, tmp_path, ticker):
    exchange = 'KRX' if ticker.isdigit() else 'NYSE' if ticker in {'IBM','TSM'} else 'NASDAQ'
    item = _seed_ready_prerequisites(session,tmp_path,ticker=ticker,exchange=exchange,company_name=ticker)
    company = session.exec(select(Company).where(Company.ticker==ticker)).one()
    sec = session.exec(select(SecurityMaster).where(SecurityMaster.ticker==ticker)).one()
    thesis = session.exec(select(InvestmentThesis).where(InvestmentThesis.ticker==ticker)).one()
    item.created_at = company.created_at = sec.updated_at = thesis.created_at = AT-timedelta(days=1)
    item.registration_requested_at = item.created_at
    if ticker in {'SKHY','TSM'}:
        item.issuer_type = sec.issuer_type = 'adr'
        sec.security_type = 'ads'
        sec.country = 'KR' if ticker=='SKHY' else 'TW'
        sec.adr_ratio = None
    if ticker in PENDING:
        item.onboarding_decision_readiness = '{}'
    session.commit()
    return item


def forbidden(*args, **kwargs):
    raise AssertionError('unexpected worker, model or identity writer')


def test_sealed_six_of_seven_and_actual_writer_selector_split(tmp_path, monkeypatch):
    root = Path(__file__).resolve().parents[3]
    prior, = (root/'maintenance/20261112-c22an-v1').glob('*FINAL_RESULT.zip')
    with ZipFile(prior) as z:
        report=json.loads(z.read('ONBOARDING_STAGE_STATUS.json'))
    assert (report['registered_count'],report['active_count'])==(22,18)
    assert {t for t,r in report['subjects'].items() if not r['active']}==PENDING
    expected=[r.value for r in readiness.OnboardingRequirement if r!=readiness.OnboardingRequirement.DECISION_READINESS]
    assert all(report['subjects'][t]['completed_stages']==expected
        and report['subjects'][t]['remaining_blockers']==['DECISION_READINESS'] for t in PENDING)

    engine=_engine()
    with Session(engine) as session:
        rows = {t:seed(session,tmp_path,t) for ts in UNIVERSE.values() for t in ts}
        for t in set(rows)-PENDING:
            r=rows[t]
            r.active=r.production_eligible=True
            r.onboarding_state='ACTIVE'
            r.activated_at=AT-timedelta(hours=1)
        session.commit()
        for r in rows.values():
            session.refresh(r)
        old = {t:r.model_dump() for t,r in rows.items() if t not in PENDING}
        preserved = {m: [r.model_dump() for r in session.exec(select(m).order_by(m.id)).all()]
            for m in (SecurityMaster,Company,InvestmentThesis,ThesisAssessment)}
        updates=[]
        event.listen(engine,'before_cursor_execute',lambda conn,cur,sql,*args:
            updates.append(sql) if sql.lstrip().upper().startswith(('UPDATE','INSERT','DELETE')) else None)
        monkeypatch.setattr(readiness.SecurityMasterService,'ensure',forbidden)
        activation=readiness.activate_existing_monitoring_subjects(session,subjects=sorted(PENDING),
            data_dir=tmp_path,as_of=AT)
        for t in sorted(PENDING):
            r=rows[t]
            assert activation[t]['status']=='ACTIVE_MONITORING_ONLY'
            result=readiness.evaluate_onboarding_readiness(session,r,data_dir=tmp_path,as_of=AT)
            assert result.monitoring_ready and not result.onboarding_ready
            assert result.completed_requirements==tuple(expected)
            assert r.active and not r.production_eligible and r.onboarding_state=='ACTIVE'
            assert r.first_eligible_session==FIRST_CYCLE
            assert r.onboarding_failure_stage=='DECISION_READINESS' and r.onboarding_decision_readiness=='{}'
            if t in {'SKHY','TSM'}:
                assert 'SECURITY_MASTER:per_share_depositary_basis' in result.safe_unavailable_requirements
        session.commit()
        assert len(updates)==4 and all(s.startswith('UPDATE watchlistitem SET') for s in updates)
        readiness.activate_existing_monitoring_subjects(session,subjects=sorted(PENDING),data_dir=tmp_path,as_of=AT)
        session.commit()
        assert len(updates)==4
        for t in old:
            session.refresh(rows[t])
        assert old=={t:rows[t].model_dump() for t in old}
        assert preserved=={m: [r.model_dump() for r in session.exec(select(m).order_by(m.id)).all()] for m in preserved}
        cutoff=AT+timedelta(hours=13)
        formal=readiness.production_universe_snapshot(session,'us',cutoff=cutoff,session_key='daily_us')
        before=readiness.production_universe_snapshot(session,'us',cutoff=AT,session_key='daily_us',monitoring_only=True)
        selected=readiness.production_universe_snapshot(session,'us',cutoff=cutoff,session_key='daily_us',monitoring_only=True)
        assert {r.ticker for r in formal.eligible_items}==set(UNIVERSE['us'])-PENDING
        assert {r.ticker for r in before.eligible_items}==set(UNIVERSE['us'])-PENDING
        assert {r.ticker for r in selected.eligible_items}==set(UNIVERSE['us'])
        proj=project_local_seed(session,market='us',session_key='2026-11-13',
            cutoff=cutoff,policy=POLICY,monitoring_only=True)
        assert set(proj['universe']['eligible_subjects'])==set(UNIVERSE['us'])
        assert proj['production_seed_qualified'] is False
        strict_kr=readiness.production_universe_snapshot(session,'kr',cutoff=cutoff,session_key='daily_kr')
        assert {r.ticker for r in strict_kr.eligible_items}==set(UNIVERSE['kr'])
        for n, calls in ((10,23),(14,30)):
            pin=digest('fixture')
            subjects=tuple(CohortSubject('us',t,'fixture:'+t,cutoff.isoformat(),pin)
                           for t in proj['universe']['eligible_subjects'][:n])
            cohort=FrozenCohort('synthetic','synthetic-source','2026-11-13',cutoff.isoformat(),
                cutoff.isoformat(),subjects,(('us',pin),),pin)
            plan=compile_model_plan(cohort,topology='CANONICAL_PRODUCTION')
            assert len(plan.slots)==calls
            assert Counter(t for s in plan.slots if s.stage=='B2' for t in s.subjects)==Counter(s.ticker for s in subjects)


@pytest.mark.parametrize('reason',['mutated_evidence','wrong_listing','future_evidence','disabled','missing_profile'])
def test_monitoring_activation_does_not_waive_identity_and_provenance(tmp_path, reason):
    engine=_engine()
    with Session(engine) as session:
        item=seed(session,tmp_path,'SKHY')
        if reason in {'mutated_evidence','future_evidence'}:
            evidence=json.loads(item.onboarding_initial_evidence)
            if reason=='mutated_evidence':
                evidence['current_price']=987
            else:
                from app.services.onboarding_evidence_service import initial_evidence_fingerprint
                evidence['as_of']=(AT+timedelta(days=1)).isoformat()
                evidence['fingerprint']=initial_evidence_fingerprint(evidence)
            item.onboarding_initial_evidence=json.dumps(evidence)
        elif reason=='wrong_listing':
            item.exchange='NYSE'
        elif reason=='disabled':
            item.monitoring_requested=False
        else:
            (tmp_path/'company_profile_provenance'/'SKHY.json').unlink()
        session.commit()
        session.refresh(item)
        old=item.model_dump()
        readiness.reconcile_onboarding(session,item,data_dir=tmp_path,as_of=AT,activation_only=True)
        assert item.model_dump()==old and not item.active
        session.rollback()


def test_backdated_activation_refused_and_optional_decision_does_not_demote(tmp_path):
    engine=_engine()
    with Session(engine) as session:
        item=seed(session,tmp_path,'IBM')
        with pytest.raises(ValueError,match='monitoring_first_session_before_next_eligible_cycle'):
            readiness.reconcile_onboarding(session,item,data_dir=tmp_path,as_of=AT,activation_only=True,
                first_eligible_session=AT.date())
        assert not item.active
        result=asyncio.run(resume_onboarding_subject(session,item,origin='fixture',
            mode=OnboardingAttemptMode.PREFLIGHT,as_of=AT,data_dir=tmp_path,
            evidence_builder=forbidden,decision_builder=forbidden,baseline_builder=forbidden))
        assert result.active and not result.production_eligible
        assert result.attempted_stages==() and result.remaining_blockers==('DECISION_READINESS',)
        assert result.first_eligible_session==FIRST_CYCLE.isoformat()


def test_four_item_writer_rolls_back_when_one_flush_fails(tmp_path):
    engine=_engine()
    with Session(engine) as session:
        for t in sorted(PENDING):
            seed(session,tmp_path,t)
        def stop_third(conn,cur,sql,params,*args):
            if sql.startswith('UPDATE watchlistitem SET') and params[-1]==3:
                raise RuntimeError('synthetic third update failure')
        event.listen(engine,'before_cursor_execute',stop_third)
        with pytest.raises(RuntimeError,match='synthetic third update failure'):
            with session.begin():
                readiness.activate_existing_monitoring_subjects(session,subjects=sorted(PENDING),
                    data_dir=tmp_path,as_of=AT)
        rows=session.exec(select(WatchlistItem)).all()
        assert len(rows)==4 and all(not r.active and r.activated_at is None for r in rows)


def test_original_readonly_owner_keeps_production_and_monitoring_scopes_separate(tmp_path, monkeypatch):
    from app.services import prospective_class_c_owner as owner
    from app.services import minimal_class_c_export as export
    from app.services.minimal_class_c_export import ExportPermission, capture_authorized_class_c

    db=tmp_path/'synthetic.sqlite3'
    engine=create_engine('sqlite:///'+str(db))
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        item=seed(session,tmp_path,'IBM')
        readiness.reconcile_onboarding(session,item,data_dir=tmp_path,as_of=AT,activation_only=True)
        session.commit()
    engine.dispose()
    captured_at=AT+timedelta(hours=13)
    now=captured_at+timedelta(seconds=5)
    class FrozenClock(datetime):
        @classmethod
        def now(cls, tz=None):
            return captured_at.astimezone(tz)
    monkeypatch.setattr(export,'datetime',FrozenClock)
    monkeypatch.setattr(owner,'_now',lambda:now)
    approval=owner.record_backend_approval(owner.ApprovalDecision(event_id='fixture-bb',
        user_message_sha256=digest('fixture-bb'),approved=True,effective_at=now-timedelta(minutes=1),
        expires_at=now+timedelta(minutes=10),subjects=('IBM',)))
    st=db.stat()
    capture=capture_authorized_class_c(ExportPermission(
        'fixture-bb',True,db,st.st_dev,st.st_ino,('IBM',)),connect=sqlite3.connect)
    with pytest.raises(ValueError,match='NO_ELIGIBLE_SUBJECT_FOR_MARKET'):
        owner.issue_prospective_owner(approval=approval,capture=capture,market='us',
            source_generation_id='strict',generation_id='strict',policy=POLICY)
    handle, consumed=owner.issue_prospective_owner(approval=approval,capture=capture,market='us',
        source_generation_id='monitor',generation_id='monitor',policy=POLICY,monitoring_only=True)
    assert consumed['universe']['eligible_subjects']==['IBM'] and consumed['roles']['universe']['eligible']
    assert consumed['prospective_owner_receipt']['monitoring_only'] is True
    assert consumed['production_seed_qualified'] is False
    assert owner.replay_captured_local_seed(handle,policy=POLICY)['universe']['eligible_subjects']==['IBM']


def test_multibatch_local_time_can_be_bounded_without_changing_worker_or_campaign():
    def bound(stage,calls):
        return research._split_stage_deadline(dict(stage=stage,planned_calls=calls,
            per_call_seconds=600,overhead_seconds=30,total_seconds=600*calls+30,retries=0),900)

    async def run():
        now=asyncio.get_running_loop().time()
        clock=SimpleNamespace(time=lambda: now)
        timer=research._StageTimer(bound('CORE',5),clock,now+950)
        async with timer.timeout:
            timer.timeout.reschedule(now+900)
            now+=606.877
            timer.check()
            timer.switch('worker')
            assert timer.deadline['per_call_seconds']==600 and timer.deadline['retries']==0
            now+=344
            with pytest.raises(TimeoutError,match='research_campaign_deadline'):
                timer.check()
    assert bound('MARKET',1)['local_seconds']==600 and bound('B2',14)['local_seconds']==600
    assert bound('RENDER',0)['local_seconds']==30
    asyncio.run(run())


def test_late_core_preserves_accepted_batch_without_committing_stage(tmp_path, monkeypatch):
    from app.services import production_runtime_bridge as runtime
    from app.services.research_artifact_budget import ResearchArtifactBudget, artifact_scope
    from app.services.unified_run_artifacts import load_json

    plan=SimpleNamespace(slots=[SimpleNamespace(stage=s) for s in ['MARKET']+['CORE']*4],validate=lambda:None)
    core_calls=[]
    stopped=[]
    budget=SimpleNamespace(stop=lambda **kw:stopped.append(kw))
    class Bridge(runtime.ProductionRuntimeBridgeV1):
        child=SimpleNamespace(plan=SimpleNamespace(slots=plan.slots,validate=plan.validate,
            cohort=SimpleNamespace(run_id='fixture')))
        model=SimpleNamespace(call_budget=budget)
        child_binding={}

        def __init__(self):
            self._native_owner_parents={}

        def snapshot(self):
            return dict(child_binding=dict(run_id='fixture',market='us',source_generation='source'),
                collection=dict(production_envelope=dict(generation_id='fixture'),
                    market='us',monitoring_input=dict(source_generation_id='source')))

        async def stage(self, request, directory):
            if request['stage']=='CORE':
                self.execution_profile=None
                self.model=SimpleNamespace(call_budget=None,request=self.synthetic_model)
                await self._invoke(SimpleNamespace(accept=lambda *a: None),'CORE',
                    dict(batch=1,subjects=['FIXTURE'],payload=dict(input={},response_schema={'type':'object'})),
                    directory/'model-1')
                self.model=SimpleNamespace(call_budget=budget)
                timer=research.current_stage_timer()
                timer.loop=SimpleNamespace(time=lambda:timer.began+606.877)
            return SimpleNamespace(model_dump=lambda **kw:dict(stage=request['stage'],run_id='fixture',
                generation_id='fixture',snapshot_sha256=request['snapshot_sha256'],status='PASS',errors=[]))

        @staticmethod
        async def synthetic_model(payload, **kwargs):
            core_calls.append(kwargs['timeout'])
            return b'{}'

    monkeypatch.setattr(research,'validate_stage_v2',lambda *a: None)
    root=tmp_path/'cycle'
    async def run():
        artifacts=ResearchArtifactBudget(roots={root:'result'})
        with artifact_scope(artifacts):
            return await research._run(Bridge(),root,local_output_rejection=False,
                artifacts=artifacts,campaign_end=asyncio.get_running_loop().time()+16200)
    result=asyncio.run(run())
    assert result['status']=='FAILED_NO_SEND' and stopped==[{'global_stop':True}] and core_calls==[600]
    assert [r['status'] for r in result['stage_receipts']]==['PASS','INTENT']
    assert result['stage_receipts'][-1]['timing']['local_seconds']==pytest.approx(606.877)
    attempt=root/'core/model-1/attempt-1'
    assert load_json(attempt/'receipt.json')['classification']=='ACCEPTED'
    assert (attempt/'response.raw').read_bytes()==b'{}' and not (root/'core/response.json').exists()
