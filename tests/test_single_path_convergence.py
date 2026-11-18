"""Changed entry boundaries only; no live Source, model, DB or send claims."""
import asyncio
from datetime import date
from types import SimpleNamespace

import pytest

from app.jobs import unified_market_snapshot as job
from app.services import production_adapter_factory as factory
from app.services import production_source_backend as backend
from app.services.production_runtime_bridge import ProductionRuntimeBridgeV1
from app.services.production_source_backend import CanonicalProductionSourceBackend
from app.services.research_no_send_run import MarketResearchChild, PreparedResearchBridge
from tests.test_c22aa_research_boundaries import plan


def test_prepared_session_is_the_production_session_method():
    assert PreparedResearchBridge._session is ProductionRuntimeBridgeV1._session
    assert PreparedResearchBridge.stage is ProductionRuntimeBridgeV1.stage


def test_manual_factory_alias_uses_production_factory(monkeypatch):
    calls=[]
    monkeypatch.setattr(factory, 'build_production_adapter', lambda settings, **kwargs:calls.append((settings,kwargs)) or 'same')
    settings=object()
    child=object()
    assert factory.build_research_adapter(enabled=True,settings=settings,child=child,binding={'original':'mapping'})=='same'
    assert calls==[(settings,dict(child=child,binding={'original':'mapping'}))]


@pytest.mark.parametrize('port', ['source_transport','model_transport','notifier'])
def test_prepared_factory_cannot_inject_an_alternate_port(port):
    with pytest.raises(ValueError,match='no_alternate'):
        factory.build_production_adapter(None,child=object(),**{port:object()})


def test_factory_rejects_planning_owner_before_any_worker(tmp_path):
    child=MarketResearchChild(plan(),None)
    with pytest.raises(ValueError,match='SOURCE_OWNER_REQUIRED'):
        factory.build_production_adapter(None,child=child,runtime_root=tmp_path/'never')
    assert not (tmp_path/'never').exists()
    with pytest.raises(ValueError,match='original_child_required'):
        factory.build_production_adapter(None,binding={})


@pytest.mark.parametrize('mode', ['LIVE_SEND','OFFLINE_REPLAY','PLAN_ONLY'])
def test_registered_entry_rejects_unauthorized_external_mode_before_source(mode,monkeypatch):
    def forbidden(**kwargs):raise AssertionError('collector entered')
    monkeypatch.setattr(CanonicalProductionSourceBackend,'prepare_registered',forbidden)
    with pytest.raises(ValueError,match='source_only_or_explicit_no_send'):
        asyncio.run(job.run_registered(None,source={},mode=mode))


def test_registered_entry_requires_one_shared_source_model_ledger(monkeypatch):
    def forbidden(**kwargs):raise AssertionError('collector entered')
    monkeypatch.setattr(CanonicalProductionSourceBackend,'prepare_registered',forbidden)
    with pytest.raises(ValueError,match='same_source_model_ledger'):
        asyncio.run(job.run_registered(None,source={'run_ledger':object()},
            model={'run_ledger':object()},mode='LIVE_NO_SEND'))


def test_source_only_returns_before_factory_and_closes_original_child(monkeypatch):
    events=[]
    child=SimpleNamespace(verify=lambda:events.append('verify'),market='us',plan=SimpleNamespace(sha256='plan',slots=(1,2)),
        owner=SimpleNamespace(acceptance=lambda:{'original':'receipt'},close=lambda:events.append('close')))
    async def admitted(**kwargs):
        events.append('source')
        return child,{}
    monkeypatch.setattr(CanonicalProductionSourceBackend,'prepare_registered',admitted)
    monkeypatch.setattr(job,'load_adapter',lambda *a,**k:pytest.fail('model factory entered'))
    result=asyncio.run(job.run_registered(None,source={},mode='SOURCE_ONLY'))
    assert result['status']=='SOURCE_ADMISSION_PASS' and result['normal_messages_sent'] is False
    assert events==['source','verify','close']


def test_fresh_model_plan_is_bound_only_after_source_admission(monkeypatch):
    events=[]
    ledger=SimpleNamespace(bind_model_plan=lambda c:events.append('bind_model_plan'))
    child=SimpleNamespace(verify=lambda:events.append('verify'),market='us',binding=lambda:{'original':'binding'},
        plan=SimpleNamespace(sha256='new-owner-verified-plan',cohort=SimpleNamespace(cutoff='2026-11-11T00:00:00+00:00')),
        owner=SimpleNamespace(close=lambda:events.append('close')))
    async def admitted(**kwargs):
        events.append('source')
        return child,{}
    def factory(settings,**kwargs):
        events.append('factory')
        assert kwargs['child'] is child and kwargs['approved_plan_sha256']==child.plan.sha256
        assert kwargs['approved_max_invocations']==2 and kwargs['run_ledger'] is ledger
        return object()
    class Engine:
        async def run(self,market,day):
            events.append('shared_cycle')
            return {'normal_messages_sent':False}
    monkeypatch.setattr(CanonicalProductionSourceBackend,'prepare_registered',admitted)
    monkeypatch.setattr(job,'load_adapter',factory)
    monkeypatch.setattr(job,'build_engine',lambda *a,**k:Engine())
    model={'run_ledger':ledger,'approved_max_invocations':2}
    result=asyncio.run(job.run_registered(None,source={'run_ledger':ledger,
        'frozen':{'stock_plan':{'implementation_sha':'a'*40}}},model=model,mode='LIVE_NO_SEND'))
    assert result=={'normal_messages_sent':False} and 'approved_plan_sha256' not in model
    assert events==['source','verify','factory','bind_model_plan','shared_cycle','close']


def test_registered_source_cannot_accept_public_owner_or_untyped_plan(tmp_path):
    args=dict(settings=None,registration_owner={'PASS':True},run_ledger=object(),root=tmp_path,
        compiler={},credentials={},policy=None,deadline=0)
    with pytest.raises(ValueError,match='selected_plan_required'):
        asyncio.run(CanonicalProductionSourceBackend.prepare_registered(frozen={},**args))
    with pytest.raises(ValueError,match='live_backend_owner'):
        asyncio.run(CanonicalProductionSourceBackend.prepare_registered(
            frozen={'scope':'SELECTED_ORIGINAL_RESEARCH_V1','generation_id':'not-authority'},**args))


def test_registered_collector_reuses_original_ports_in_order(tmp_path,monkeypatch):
    from app.services import prospective_class_c_owner as reg, selected_source_preparation as preparation
    from app.services.unified_run_artifacts import durable_json
    from tests.test_c22ab_selected_source import compile_market
    compiled,_,_=compile_market('us','NEWX')
    request_plan=compiled['plan']
    events=[]
    ledger=SimpleNamespace(state=lambda:{'plans':{'us':request_plan.plan_sha256}},worker_binding=lambda:{'original':'ledger'},
        source_captured=lambda m:events.append('captured'),source_owned=lambda c:events.append('owned'))
    frozen=dict(scope='SELECTED_ORIGINAL_RESEARCH_V1',generation_id=request_plan.generation_id,
        plan=request_plan.model_dump(mode='json'),shared_run_ledger=ledger.worker_binding())
    root=tmp_path/'source'
    durable_json(root/'production-frozen-source-plan.json',frozen,exclusive=True)
    child=SimpleNamespace(verify=lambda:events.append('child.verify'),plan=SimpleNamespace(validate=lambda:events.append('plan.validate')),
        owner=SimpleNamespace(close=lambda:events.append('closed')))
    monkeypatch.setattr(reg,'require_generation',lambda *args:None)
    monkeypatch.setattr(backend,'require_captured_phase',lambda *args:events.append('stocks'))
    monkeypatch.setattr(backend,'market_inputs',lambda *args:events.append('market'))
    monkeypatch.setattr(backend,'seal_collection',lambda *args,**kwargs:events.append('seal') or {})
    monkeypatch.setattr(backend,'verify_collection_seal',lambda *args:events.append('verify.seal'))
    monkeypatch.setattr(preparation,'prepare_child',lambda **kwargs:events.append('prepare_child') or (child,{'synthetic':True}))
    class Collector:
        async def collect(self,**kwargs):
            events.append('collect')
            assert kwargs['root']==root and kwargs['frozen']==frozen and kwargs['retained_sec']=={'bounded':'reference'}
            return {'synthetic':True}
    import time
    actual,proof=asyncio.run(backend.CanonicalProductionSourceBackend.prepare_registered(settings=None,
        registration_owner=object(),run_ledger=ledger,root=root,frozen=frozen,compiler={},credentials={},policy=None,
        deadline=time.monotonic()+600,retained_sec={'bounded':'reference'},transport=Collector()))
    assert actual is child and proof=={'synthetic':True}
    assert events==['collect','captured','stocks','market','seal','verify.seal','prepare_child','child.verify','plan.validate','owned']


def test_registry_does_not_ignore_prepared_arguments():
    with pytest.raises(ValueError,match='production_registry_required'):
        job.load_adapter(SimpleNamespace(unified_snapshot_adapter_version='disabled'),child=object())


def test_prepared_cycle_parses_serialized_cohort_cutoff(tmp_path,monkeypatch):
    from app.services import research_no_send_run as research
    from app.services.unified_market_run import RunConfiguration, UnifiedMarketRun
    from app.services.unified_runtime_v2 import CONTRACT

    # Date dispatch only; Source authority is exercised by the separate
    # original-constructor integration, not this shape-only fixture.
    bridge=object.__new__(PreparedResearchBridge)
    bridge.model=SimpleNamespace(call_budget=None)
    bridge.child=SimpleNamespace(verify=lambda:None,market='us',plan=SimpleNamespace(
        cohort=SimpleNamespace(cutoff='2026-11-11T00:00:00+00:00',assessment_date='2026-11-11')))
    calls=[]
    async def shared(ports,**kwargs):
        calls.append((ports,kwargs['split_model_timing']))
        return {'status':'OFFLINE_DATE_DISPATCH_ONLY'}
    monkeypatch.setattr(research,'run_prepared_research',shared)
    engine=UnifiedMarketRun(RunConfiguration(root=tmp_path,debug_destination=None,repo_commit='fixture',
        scheduler_identity='fixture',adapter_fingerprint='fixture',runtime_contract=CONTRACT,
        stage_timeout_seconds=600,collection_timeout_seconds=600),bridge)
    assert asyncio.run(engine.run('us',date(2026,11,11)))=={'status':'OFFLINE_DATE_DISPATCH_ONLY'}
    bridge.model=SimpleNamespace(call_budget=SimpleNamespace(run_ledger=SimpleNamespace(
        identity={'wallclock_seconds_max':600})))
    assert asyncio.run(engine.run('us',date(2026,11,11)))=={'status':'OFFLINE_DATE_DISPATCH_ONLY'}
    with pytest.raises(ValueError,match='market_day_or_completed_session'):
        asyncio.run(engine.run('us',date(2026,11,12)))
    assert calls==[(bridge,False),(bridge,True)] and not list(tmp_path.iterdir())
