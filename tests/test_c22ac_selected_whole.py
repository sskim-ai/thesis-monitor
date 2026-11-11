"""Changed selected boundaries only; all source/Owner positives are synthetic."""
import asyncio
from copy import deepcopy
from datetime import datetime,timezone
import hashlib,json,subprocess
from pathlib import Path

import pytest

from app.services.selected_source_composition import SelectedSourceRunBinding,code_fingerprints,project_market,validate_composition
from app.services.selected_source_plan import SelectedConsumerPolicy,compile_selected_plan,request_budget
from app.services.unified_snapshot_contract import digest,encoded
from tests.test_c22ab_selected_source import compile_market

AT=datetime(2026,11,11,8,tzinfo=timezone.utc)


def binding(market='us',subjects=('NEWX',),**changes):
    generation='SYNTHETIC_'+market.upper()
    value=dict(parent_run_id=generation,child_id=generation,master_id='SYNTHETIC_MASTER',
        market=market,subjects=subjects,target_session='2026-11-10' if market=='us' else '2026-11-11',started_at=AT,
        attempts={market:generation+':A1'},attempt_hashes={market:digest('market')},
        stock_cohort_hashes={market:digest('stock')},run_acquisitions={'stock':digest('stock')},
        universe_sha256=digest({market:subjects}),raw_owner_bindings={t:digest('raw:'+t) for t in subjects},
        selected_code_sha256=digest(code_fingerprints()))
    for key in ('source_policy_sha256','inventory_sha256','code_config_sha256','class_c_version_set_sha256',
                'night_publication_receipt_sha256','optional_denial_set_sha256','skhy_issuer_bridge_sha256',
                'source_authority_contract_sha256','fresh_stock_owner_set_sha256','request_plan_sha256','registration_receipt_sha256'):
        value[key]=digest(key)
    value.update(changes)
    return SelectedSourceRunBinding(**value)


def test_native_pin_semantic_migration_positive_negative():
    from tests.test_c20r2_name_variant import setup,derive,alter
    sec,raw=setup('999999','Registered Label','Provider Label')
    rows=derive(sec,raw)
    assert all(r.display_eligible and not r.overall_direction_use for r in rows)
    assert all(r.security_identity_receipt['name_diagnostics']==['REGISTERED_NAME_VARIANT_NONBLOCKING'] for r in rows)
    alter(raw,lambda b:b.update(stk_cd='999998'))
    assert all(not r.display_eligible for r in derive(sec,raw))
    sec,raw=setup('999999','Same','Same')
    good=derive(sec,raw)
    assert all(r.display_eligible and 'name_diagnostics' not in r.security_identity_receipt for r in good)
    alter(raw['identity_inputs']['list_pages'][0],lambda b:b['list'][0].update(marketCode='10'))
    assert all(not r.display_eligible for r in derive(sec,raw))


def test_selected_empty_kis_plan_validated_without_renaming():
    from tests.test_kis_no_estimate_owner import inputs
    from app.services.selected_kis_sources import build_plan
    from scripts.kis_no_estimate_owner import assess
    args=deepcopy(inputs('123456'));old=args['plan'];s=old['securities']['123456']
    s.update(ticker='123456',exchange='KRX',currency='KRW',corp_code='00123456')
    p=build_plan(generation=args['generation'],as_of=old['as_of'],securities={'123456':s},static_hashes={})
    args['plan']=p;args['request']['plan_sha256']=p['receipt_sha256'];args['receipt']['request']=deepcopy(args['request'])
    result=assess(**args)
    assert result['normal_empty_confirmed'] and result['owner_complete']
    args['plan']={**p,'maximum_physical_HTTP':999}
    with pytest.raises(ValueError):assess(**args)


def test_selected_binding_drift_cross_market_and_full22_preserved():
    seed=binding()
    assert seed.universe=={'us':('NEWX',)} and seed.us_only
    for changes in ({'child_id':'OTHER'},{'target_session':'2026-11-09'},
                    {'attempts':{'kr':'A'}},{'raw_owner_bindings':{'NEWX':'not-a-hash'}}):
        with pytest.raises(ValueError):binding(**changes)
    from tests.test_unified_stock_acquisition import plan
    full=plan.__wrapped__()
    assert len(full.reads)==88 and len(full.universe['us'])==14 and len(full.universe['kr'])==8
    from app.services.production_source_binding import ProductionSourceRunBinding
    with pytest.raises(ValueError):ProductionSourceRunBinding.model_validate(seed.model_dump(mode='json'))


def test_selected_required_budget_omits_only_unconsumed_optional_roles():
    total=legacy=0
    for market,ticker in [('us','NEWX'),('kr','123456')]:
        old,args,kis=compile_market(market,ticker)
        legacy+=request_budget(old,kis)['total']
        args['selected_consumer_policy']=SelectedConsumerPolicy()
        selected=compile_selected_plan(compiler_args=args,kis_plan=kis)
        total+=request_budget(selected,kis)['total']
        assert not any(d.endpoint_operation=='ka10066' for d in selected['plan'].descriptors)
        assert len(selected['candidate']['night_query_dates'])==(7 if market=='us' else 0)
        assert len(args['stock'].reads)==4
        assert all(d.transient_retry_max==0 for d in selected['plan'].descriptors)
    assert legacy==255 and total==186
    from app.services.selected_market_collection import SelectedKrMarketCollection
    service=SelectedKrMarketCollection(None,consumer_policy=SelectedConsumerPolicy())
    detail=asyncio.run(service._ka10066_pages(market_code='001'))
    assert not detail.complete and detail.rows==[] and detail.pages==0


def test_missing_market_and_raw_owner_are_not_source_authority():
    seed=binding()
    with pytest.raises(ValueError,match='context_or_code'):
        validate_composition(seed,stock_inputs={},market_inputs={},composition_metadata=None,fresh_context_inputs=None)
    with pytest.raises(ValueError,match='graph_contract'):
        project_market({},seed.model_dump(mode='json'),{'contract':'full-source-authority-graph-v1'},expected_authority_sha256=digest('none'))
    from app.services.selected_source_preparation import prepare_child
    with pytest.raises(ValueError,match='default_off'):
        prepare_child(root=None,frozen={},outcome={},policy=None,registration_owner=None)


def test_selected_composition_raw_time_and_registration_guards():
    # Shape-only synthetic metadata. The original economic kernel is NOT
    # invoked and no Source/Market/registration Owner is issued by this test.
    from app.services.selected_source_plan import SelectedStockPlan
    from app.services.selected_source_composition import raw_owner_binding
    from app.services.unified_source_composition import SourceRole,A
    compiled,args,_=compile_market('us','NEWX')
    data=args['stock'].model_dump(mode='json')
    data.update(planning_only=False,owner_files={'fixture.py':'0'*64},owner_head='0'*40,
        settings_sha256='0'*64,request_environment_sha256='0'*64)
    stock=SelectedStockPlan.model_validate(data)
    item=dict(technical_inputs=dict(plan=stock,receipts={'fixture':'not real raw'}),
        financial_inputs=dict(plan=dict(run_id=stock.run_id,cutoff=stock.frozen_at.isoformat(),
            security=args['identities']['NEWX']),receipts=[]))
    seed=binding(parent_run_id=stock.run_id,child_id=stock.run_id,raw_owner_bindings={'NEWX':raw_owner_binding(item)})
    meta=dict(selected_code_fingerprints=code_fingerprints(),selected_request_plan_sha256=seed.request_plan_sha256,
        selected_registration_receipt_sha256=seed.registration_receipt_sha256)
    role=SourceRole(key='us_market_prices',owner='us_market',market='us',symbol='*',provider='ohlcv_analyst',
        basis='adjusted_close',session=seed.target_session,acquisition_class=A,mandatory=True)
    markets={'us':{'native_aggregate':dict(run_id=stock.run_id,role=role)}}
    kwargs=dict(stock_inputs={'NEWX':{'fresh_financial_binding':item}},market_inputs=markets,
        composition_metadata=meta,fresh_context_inputs=dict(publications={'market_scope':'SELECTED_US'},night={}))
    assert validate_composition(seed,**kwargs)==seed
    bad=dict(meta,selected_registration_receipt_sha256=digest('wrong'))
    with pytest.raises(ValueError):validate_composition(seed,**{**kwargs,'composition_metadata':bad})
    item['financial_inputs']['receipts'].append({'tampered':True})
    with pytest.raises(ValueError,match='raw_or_security'):validate_composition(seed,**kwargs)


@pytest.mark.parametrize('ticker',['MU','005930'])
def test_original_fresh_stock_source_only_and_coverage_positive_negative(tmp_path,monkeypatch,ticker):
    # Reuse synthetic raw fixture builders, not the earlier test suite or any
    # accepted model output. The actual original SEC/valuation/quality owners run.
    from tests import test_newbuyer_b2_v2_coverage as fixture
    from app.services.current_source_coverage import seal_inputs,compose,SEMANTICS
    from app.services.canonical_source_inputs import fresh_authority_inputs
    from scripts.fresh_source_only_export import source_only_fresh_stock
    from app.services.direction_timing_ownership_service import verified_owned_packet_view
    captured={};original=fixture.assemble_fresh_stock
    def collect(**inputs):
        captured.update(inputs)
        return original(**inputs)
    monkeypatch.setattr(fixture,'assemble_fresh_stock',collect)
    owner=fixture.source(tmp_path/'source',ticker=ticker)
    verified_owned_packet_view(owner.stock)
    seal=seal_inputs({ticker:owner},subjects=[ticker],semantics_version=SEMANTICS)
    result=compose({ticker:owner},subjects=[ticker],generations={ticker:owner.generation},input_seal=seal,
        input_seal_sha256=seal['receipt_sha256'],semantics_version=SEMANTICS)
    assert result['coverage']['coverage_complete'] and result['census'] is not None
    assert owner.stock['contract']=='fresh-financial-stock-owner-v1'
    from scripts.m12dr_financial_source_authority import build_source_authority
    authority=build_source_authority(**fresh_authority_inputs(owner.stock,captured))
    assert source_only_fresh_stock(owner.stock,authority)['ticker']==ticker
    owner.stock['packet_sha256']='0'*64
    with pytest.raises(ValueError):
        compose({ticker:owner},subjects=[ticker],generations={ticker:owner.generation},input_seal=seal,
            input_seal_sha256=seal['receipt_sha256'],semantics_version=SEMANTICS)
    with pytest.raises(ValueError,match='source_only_fresh_contract_required'):
        source_only_fresh_stock({'contract':'C22C_EXISTING_SOURCE_DATED_INVESTMENT_INPUT'},{})


def test_original_kr_forward_positive_and_cross_security_negative():
    from tests.test_kr_forward_valuation_integration import view
    from app.services.kr_forward_valuation_context import KrForwardValuationView,calibration_context
    original=view()
    context=calibration_context(original)
    assert context['metric_states'][-1]['metric']=='FY1_EPS' and context['facts']
    assert context['allowed_axes']==['NEW_BUYER','HOLDER'] and not context['overall_direction_use']
    bad=original.model_dump(mode='json');bad['kis']['security_code']='654321'
    with pytest.raises(ValueError):KrForwardValuationView.model_validate(bad)


def test_selected_kr_coverage_forward_and_original_empty_protocol(tmp_path):
    from tests.test_newbuyer_b2_v2_coverage import source
    from app.services.selected_source_plan import build_stock_plan,COUNTS
    from app.services.selected_kis_sources import build_plan
    from app.services.unified_stock_event_input import make_read
    from app.services.selected_source_preparation import coverage_and_forward
    owner=source(tmp_path/'source',ticker='005930',empty=True)
    sec=owner.security;at=datetime.fromisoformat(owner.kis_plan['as_of']);gen=owner.generation
    stock=build_stock_plan(market='kr',identities={'005930':sec},at=at,generation=gen,code_sha='a'*40,counts=COUNTS)
    kp=build_plan(generation=gen,as_of=at.isoformat(),securities={'005930':dict(sec,currency='KRW')},static_hashes={})
    args=dict(stock=stock,identities={'005930':sec},news_reads=[make_read(security=sec,market='kr',run_id=gen,lookback_days=3,security_records=[sec])],
        config_identities={p:digest('fixture-'+p) for p in ('kiwoom','opendart','ecos','krx_night_futures','naver_news')},
        configured_kr_pages=20,kr_post_acquisition_completeness_approved=True,exact_financial_owner=True,
        valuation_market_types={'005930':'0'},transient_retry_max=0,selected_consumer_policy=SelectedConsumerPolicy())
    compiled=compile_selected_plan(compiler_args=args,kis_plan=kp)
    from app.services.market_session import korea_market_session
    seed=binding('kr',('005930',),parent_run_id=gen,child_id=gen,started_at=at,
        target_session=korea_market_session(at).latest_completed_regular_session_date.isoformat(),
        request_plan_sha256=compiled['plan'].plan_sha256)
    whole=dict(seed=seed.model_dump(mode='json'),packets={'kr':{'stocks':{'005930':owner.stock}}})
    evidence=deepcopy(owner.availability_inputs);evidence['request']['plan_sha256']=kp['receipt_sha256'];evidence['receipt']['request']=deepcopy(evidence['request'])
    folder=tmp_path/'kis/estimate';folder.mkdir(parents=True)
    (folder/'005930.body').write_bytes(evidence['raw'])
    for name in ('receipt','request'):(folder/('005930-'+name+'.json')).write_bytes(encoded(evidence[name]))
    view=dict(generation_id=gen,rows=[owner.kis_row],rows_sha256=digest([owner.kis_row]))
    cov,forward=coverage_and_forward(root=tmp_path,frozen=dict(plan=compiled['plan'].model_dump(mode='json'),security_records=[sec]),
        whole=whole,collection_seal_sha256=digest('synthetic-only'),kis_plan=kp,kis_view=view)
    assert cov['coverage']['coverage_complete'] and cov['census'] is not None
    assert forward['005930']['kis']['eps']['value'] is None


def test_selected_added_subjects_have_dynamic_slots_and_no_send_stage():
    from app.services.model_execution_plan import CohortSubject,FrozenCohort,compile_model_plan
    from app.services.research_no_send_run import RESEARCH_STAGES
    for n in (1,3,4):
        c=FrozenCohort('SYNTHETIC_RUN','SYNTHETIC_SOURCE','2026-11-10',AT.isoformat(),AT.isoformat(),
            tuple(CohortSubject('us','X'+str(i),'SEC:'+str(i),AT.isoformat(),digest(i)) for i in range(n)),
            (('us',digest('not-current-owner')),),digest('synthetic-only'))
        p=compile_model_plan(c,topology='CANONICAL_PRODUCTION')
        assert len(p.slots)==1+3*((n+2)//3)+n
    assert 'DELIVER' not in RESEARCH_STAGES and RESEARCH_STAGES[-1]=='RENDER'
