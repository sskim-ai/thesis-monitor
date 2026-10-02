"""Synthetic current/research family separation and KR-only execution guards."""
from copy import deepcopy
from datetime import datetime
from pathlib import Path

import pytest

from app.services.current_fresh_valuation import CurrentMultiple, CurrentValuationView
from app.services.kr_forward_valuation_context import (
    KrForwardValuationView, calibration_context, forward_bindings,
)
from app.services.kr_forward_valuation_message import valuation_rows
from app.services.provider_valuation_calibration_context import (
    validate_calibration_output, require_direction_isolation, with_axis_refs,
)
from app.services.whole_source_code_owner_registry import WholeSourceCodeOwnerRegistry
from app.services.unified_snapshot_contract import digest
from scripts import kis_current_fy1_owner as owner
from scripts.kr8_fy1_models import Kr8Execution
from scripts.r9_rev11_live import source_disk_minimum
from scripts.r2b_r5_execution import Execution
from tests.test_kis_current_fy1_owner import ASOF, eps, price_inputs, owned_actions, reseal


def view(value='30', *, missing=False):
    e=reseal(eps(value),query_time=ASOF)
    r=reseal(e,metric='PER',unit='MULTIPLE',state='KIS_PROVIDER_FY1_PER_SNAPSHOT',value='9.5')
    price=action=None
    if missing:
        e=r={'state':'UNAVAILABLE_NO_KIS_RESEARCH_ESTIMATE','value':None}
    elif float(value)>0:
        args=price_inputs()
        args['eps']=e
        price=owner.price_receipt(**args)
        action=owned_actions(price)
    native=CurrentValuationView(ticker='123456',security_id='synthetic-security',run_id='fictional',
        currency='KRW',price=100,price_session='2026-09-30',price_basis='close',
        price_context_sha256='a'*64,security_sha256='b'*64,financial_projection_sha256='c'*64,
        owner_output_sha256='d'*64,metrics=tuple(CurrentMultiple(metric=m,status='UNAVAILABLE',
            numerator=100,source_method='fixture',input_hashes=('a'*64,),denial_reason='UNAVAILABLE')
            for m in ('PER','PBR','fPER')))
    return KrForwardValuationView(native=native,as_of=ASOF,fresh_plan_sha256='e'*64,
        source_corpus_sha256='f'*64,kis=dict(security_code='123456',eps=e,provider_per=r,
            price=price,action=action,current_fper=owner.current_fper(e,price,action)))


def output(context):
    refs={r['metric']:r['fact_ref'] for r in context['metric_states']}
    return dict(overall=dict(overall_reason='Observed business evidence',supporting_refs=['business']),
        new_buyer_axis=dict(new_buyer_reason='현재가 기준 fPER valuation caution',
            new_buyer_valuation_refs=[refs['CURRENT_FY1_FPER']]),
        holder_axis=dict(holder_reason='KIS 리서치 fPER snapshot context',
            holder_valuation_refs=[refs['RESEARCH_FY1_PER']]))


def test_separate_current_and_research_refs_decimal_labels_and_dates():
    v=view()
    ctx=calibration_context(v)
    assert [r['metric'] for r in ctx['metric_states']]==['PER','PBR','CURRENT_FY1_FPER','RESEARCH_FY1_PER','FY1_EPS']
    assert len(ctx['facts'])==3
    assert validate_calibration_output(output(ctx),ctx)['status']=='PASS'
    bindings=forward_bindings(v)
    assert bindings['FY1_EPS']['registry']['unit']=='KRW'
    assert bindings['CURRENT_FY1_FPER']['fact']['decimal_value'].startswith('3.333')
    rows=valuation_rows(v)
    text=str([r.model_dump(mode='json') for r in rows])
    assert '현재가 기준 fPER(FY1): 3.33배' in text
    assert 'KIS 리서치 fPER(FY1): 9.50배' in text
    assert '2026-09-30 정규장 종가 기준' in text and '2026-07-01 추정' in text
    assert len({r.row_id for r in rows})==3


@pytest.mark.parametrize('value', ['0','-2'])
def test_nonpositive_is_nm_not_zero_or_missing(value):
    v=view(value)
    states=calibration_context(v)['metric_states']
    assert states[2]['state']=='NOT_MEANINGFUL' and states[2]['value'] is None
    assert states[4]['value']==value
    assert 'N/M' in str(valuation_rows(v)[0])


def test_unavailable_no_numeric_refs_and_no_synthetic_zero():
    ctx=calibration_context(view(missing=True))
    assert not ctx['facts'] and all(r['value'] is None for r in ctx['metric_states'])
    assert '자료 없음' in str(valuation_rows(view(missing=True)))


@pytest.mark.parametrize('change', ['security','stale','unit','research_period','research_identity','derived_value'])
def test_identity_freshness_units_fiscal_and_derived_tamper_rejected(change):
    raw=view().model_dump(mode='json')
    if change=='security':
        raw['kis']['security_code']='654321'
    elif change=='stale':
        raw['as_of']='2026-10-02T12:00:00+09:00'
    elif change=='derived_value':
        raw['kis']['current_fper']=reseal(raw['kis']['current_fper'],value='999')
    else:
        key,val={'unit':('unit','USD_PER_SHARE'),'research_period':('period','2027.12E'),
            'research_identity':('security',{})}[change]
        raw['kis']['provider_per']=reseal(raw['kis']['provider_per'],**{key:val})
    with pytest.raises(ValueError):
        KrForwardValuationView.model_validate(raw)


@pytest.mark.parametrize('stage',['core','pass-a','overall'])
def test_forward_valuation_never_business_direction(stage):
    ctx=calibration_context(view())
    ref=next(iter(ctx['facts']))
    for raw in ({stage:{'evidence_refs':[ref]}},{stage:{'valuation_context':ctx}}):
        with pytest.raises(ValueError,match='directional'):
            require_direction_isolation(raw)


@pytest.mark.parametrize('mutation',['overall','other_ticker','wrong_family','nonaxis'])
def test_output_requires_exact_family_axis_refs(mutation):
    ctx=calibration_context(view())
    raw=output(ctx)
    if mutation=='overall':
        raw['overall']['overall_reason']='FY1 EPS implies BUY'
    elif mutation=='other_ticker':
        raw['holder_axis']['holder_valuation_refs']=['kr-forward-valuation:other:RESEARCH_FY1_PER']
    elif mutation=='wrong_family':
        raw['holder_axis']['holder_valuation_refs']=raw['new_buyer_axis']['new_buyer_valuation_refs']
    else:
        raw['holder_axis']['holder_reason_evidence_refs']=raw['holder_axis']['holder_valuation_refs']
    with pytest.raises(ValueError):
        validate_calibration_output(raw,ctx)


def test_axis_schema_does_not_expand_business_capabilities():
    from scripts.m12ds_r2_schemas import obj,refs
    ctx=calibration_context(view())
    schema=obj(dict(overall=obj(dict(supporting_refs=refs(['business']))),
        new_buyer_axis={'anyOf':[obj(dict(new_buyer_reason={'type':'string'}))]},
        holder_axis={'anyOf':[obj(dict(holder_reason={'type':'string'}))]}))
    before=deepcopy(schema)
    out=with_axis_refs(schema,ctx)
    assert out['properties']['overall']==before['properties']['overall'] and schema==before
    assert ctx==calibration_context(view())


def test_kr8_registry_opt_in_and_storage_defaults_unchanged():
    root=Path(__file__).resolve().parents[1]
    default=WholeSourceCodeOwnerRegistry.freeze(root)
    kr=WholeSourceCodeOwnerRegistry.freeze(root,profile='fresh_kr8')
    assert len(default.entries)==27 and len(kr.entries)>27
    assert not any('kr8' in e.path for e in default.entries)
    assert source_disk_minimum(kr_only=True,native_valuation=True)==10
    assert source_disk_minimum(kr_only=False,native_valuation=True)==12


def test_kr_model_scope_budget_topology_no_us_dispatch():
    controller=object.__new__(Kr8Execution)
    assert len(controller.batch_topology())==3
    assert all(r['market']=='kr' for r in controller.batch_topology())
    assert sum(controller.CALL_LIMITS.values())==10
    assert Execution.SUBJECT_COUNT==22 and Execution.MARKET_SCOPES==('us','kr')
    with pytest.raises(Exception,match='US_REQUEST_FORBIDDEN'):
        controller.capture('market',dict(market='us',subjects=[]),{},{},'fictional')


def test_clock_and_view_roundtrip():
    v=view()
    assert v.as_of==datetime.fromisoformat(ASOF)
    assert KrForwardValuationView.model_validate_json(v.model_dump_json()).model_dump(mode='json')==v.model_dump(mode='json')
    assert calibration_context(v)['valuation_view_sha256']==digest(v.model_dump(mode='json'))


def test_real_typed_renderer_preserves_base_per_pbr_and_rejects_mutation(monkeypatch):
    from tests import test_r9_rev7_detailed_renderer as fixture
    from app.services.accepted_calibration_message_service import AcceptedDetailedCalibrationPlan
    from app.services.accepted_decision_v2_service import render_accepted_v2_production
    from app.services.detailed_stock_message_service import build_detailed_plan
    from app.services.kr_forward_valuation_message import build_plan,audit
    ep=fixture._packet().model_copy(update={'ticker':'123456','market':'kr'})
    monkeypatch.setattr(fixture,'_packet',lambda:ep)
    args=fixture.inputs.__wrapped__()
    native=args['valuation'].model_copy(update={'currency':'KRW','security_id':'synthetic-security'})
    args['valuation']=native
    args['source_stock']['valuation_view']=native.model_dump(mode='json')
    accepted=args['accepted']
    provenance={**accepted.stage_provenance,'fresh_stock_sha256':digest(args['source_stock'])}
    receipt={**accepted.acceptance,'stage_provenance_sha256':digest(provenance)}
    args['accepted']=AcceptedDetailedCalibrationPlan(**{**accepted.model_dump(mode='json'),
        'stage_provenance':provenance,'acceptance':receipt,'acceptance_sha256':digest(receipt)})
    base=build_detailed_plan(**args)
    forward=view().model_copy(update={'native':native})
    plan=build_plan(ep,base,forward)
    original=[r for r in base.rows if r.row_id in ('valuation:PER','valuation:PBR')]
    assert [r for r in plan.rows if r.row_id in ('valuation:PER','valuation:PBR')]==original
    assert len(plan.rows)==len(base.rows)+2
    rendered=render_accepted_v2_production(ep,plan)
    assert rendered.validation.valid
    assert audit(rendered.text,ep,plan)['status']=='PASS'
    assert '현재가 기준 fPER(FY1): 3.33배' in rendered.text
    assert 'KIS 리서치 fPER(FY1): 9.50배' in rendered.text
    with pytest.raises(ValueError,match='post_render_mutation'):
        audit(rendered.text+'0',ep,plan)
    with pytest.raises(ValueError,match='plan_drift'):
        render_accepted_v2_production(ep,plan.model_copy(update={'rows':plan.rows[:-1]}))
