"""Synthetic policy mechanics; never actual issuer approval or model receipts."""
from copy import deepcopy
import pytest

from app.services import vnext_unified_judgment as m
from app.services import vnext_balanced_stage_review as stage
from test_vnext_balanced_research_v2 import case, directional


def fixture(*identity, side=None):
    p, old, registry = directional(side) if side else case(*identity)
    for e in p['base']['evidence']:
        if e['field'].startswith('financial.'):
            e['data']['interpretation_eligible'] = True
        if e['field'].startswith('valuation.'):
            e['data']['overall_direction_use'] = True
    b = old['balanced']
    v = dict(contract=m.CONTRACT, security_id=p['base']['public_security']['canonical_security_id'],
        action='NONE',authority='MODEL_INTERPRETATION',holder_basis='VIRTUAL',
        business='ADVERSE' if side=='SELL' else 'POSITIVE',
        economic_drivers_positive=[dict(d,assertion='OBSERVED_CHANGE') for d in old['economic_drivers_positive']],
        economic_drivers_negative=[dict(d,assertion='OBSERVED_CHANGE') for d in old['economic_drivers_negative']],
        **{k:deepcopy(b[k]) for k in ('business_quality_denials','active_material_risk_refs',
            'active_material_risk_reason','confidence_veto_refs','valuation','overall','holder_virtual',
            'newbuyer_change_condition')},newbuyer_confidence='MEDIUM', technical_review=None,
        adjudication_changes='No separate prior judgment in this synthetic example.')
    for axis in ('valuation','overall','holder_virtual'):
        a = v[axis]
        a['confidence'] = 'NOT_SEPARATELY_ISSUED' if a.get('stance',a.get('judgment'))=='NOT_ISSUED' else 'MEDIUM'
    return p,v,registry


def check(p,v,r,packet=None):
    packet = packet or m.build_bundle(p,registry=r)
    return m.validate_and_render(v,packet,registry=r,economic_loader=lambda:deepcopy(p))


@pytest.mark.parametrize('valuation,expected',[('SUPPORTIVE','ATTRACTIVE'),('NEUTRAL','WAIT'),('BURDENSOME','WAIT')])
def test_original_b2_choices_without_fair_value_or_label_quota(valuation,expected):
    p,v,r=fixture();v['valuation']['judgment']=valuation
    result=check(p,v,r)['decision']
    assert result['newbuyer_fundamental']==expected
    assert result['model_output']['overall']['stance']=='NOT_ISSUED'
    assert result['timing_scope']=='NOT_ISSUED' and not result['send']


@pytest.mark.parametrize('side',['BUY','SELL'])
def test_original_material_anchor_ordinal_and_distinct_support(side):
    p,v,r=fixture(side=side)
    assert check(p,v,r)['decision']['model_output']['overall']['stance']==side


def test_current_structural_risk_still_avoid():
    p,v,r=fixture()
    p['base']['evidence'][0]['data']['fields']['structural_risk_verified']=True
    v['economic_drivers_negative']=deepcopy(v['economic_drivers_positive'])
    v['business']='MIXED';v['active_material_risk_refs']=['business']
    v['active_material_risk_reason']='Current material structural impairment.'
    assert check(p,v,r)['decision']['newbuyer_fundamental']=='AVOID'
    p['base']['evidence'][0]['freshness']='DATED_REFERENCE_NOT_CURRENT_REQUALIFICATION'
    with pytest.raises(ValueError,match='risk_not_current'):check(p,v,r)


@pytest.mark.parametrize('axis',['MECHANISM','RECURRENCE','STRUCTURAL_RISK'])
def test_reported_change_does_not_prove_cause_recurrence_or_structural_risk(axis):
    p,v,r=fixture();v['economic_drivers_positive'][0]['assertion']=axis
    with pytest.raises(ValueError,match='unsupported'):check(p,v,r)


@pytest.mark.parametrize('change',['identity','action','authority','number','foreign_ref','revoked','changed_packet'])
def test_exact_source_and_semantic_negatives(change):
    p,v,r=fixture();packet=m.build_bundle(p,registry=r)
    if change=='identity':v['security_id']='OTHER'
    if change=='action':v['action']='BUY'
    if change=='authority':v['authority']='BACKEND_APPROVED'
    if change=='number':v['valuation']['reasoning']='Buy at 100.'
    if change=='foreign_ref':v['valuation']['refs']=['other-security']
    if change=='revoked':r.revoke(v['security_id'],p['base']['evidence'][0]['source_sha'])
    if change=='changed_packet':packet['admissibility'][0]['candidate_decision_axis']=[]
    with pytest.raises(ValueError):check(p,v,r,packet)


@pytest.mark.parametrize('text',['매수세가 약해지는 관측이다.','매도세가 강해지는 관측이다.',
    '매수 압력과 약세가 공존한다.','Observed buying pressure is mixed.'])
def test_observation_words_not_trade_commands(text):
    m.prose(text)


@pytest.mark.parametrize('text',['지금 매수하세요.','지금 매도해 주세요.','Buy now.',
    'Guaranteed profit.','사용자의 보유 수량이다.','발송을 승인한다.','현재가가 유리하다.'])
def test_actual_commands_holdings_and_authority_still_denied(text):
    with pytest.raises(ValueError):m.prose(text)


def test_outer_dated_wrapper_not_blanket_direction_denial_but_actual_denial_preserved():
    p,v,r=fixture(side='BUY')
    for e in p['base']['evidence']:e['direction_allowed']=False
    assert check(p,v,r)['decision']['model_output']['overall']['stance']=='BUY'
    p['base']['evidence'][0]['data']['direction_allowed']=False
    with pytest.raises(ValueError,match='direction_not_authorized'):check(p,v,r)


def test_context_valuation_cannot_leak_to_overall():
    p,v,r=fixture(side='BUY');p['base']['evidence'][1]['data']['overall_direction_use']=False
    with pytest.raises(ValueError,match='valuation_use_denied'):check(p,v,r)


@pytest.mark.parametrize('change',['anchor','correlated','counterevidence','balance'])
def test_original_overall_gates(change):
    p,v,r=fixture(side='SELL' if change=='counterevidence' else 'BUY')
    if change=='anchor':v['overall']['anchor_refs']=[]
    if change=='counterevidence':v['overall']['counterevidence_refs']=[]
    if change=='balance':v['overall']['balance']={'buy':5.0,'sell':5.0}
    if change=='correlated':
        v['overall']['corroborating_refs']=['business']
    with pytest.raises(ValueError):check(p,v,r)


@pytest.mark.parametrize('country,kind,ticker',[('KR','common_stock','UNSEEN_KR'),('US','common_stock','UNSEEN_US'),
    ('US','ADS','UNSEEN_ADS'),('KR','financial','UNSEEN_FIN'),('US','cyclical','UNSEEN_CYCLE')])
def test_evidence_equivalence_not_ticker_rules(country,kind,ticker):
    p,v,r=fixture(ticker,country,kind)
    assert check(p,v,r)['decision']['newbuyer_fundamental']=='ATTRACTIVE'


def test_modes_do_not_recompute_decision():
    p,v,r=fixture();result=check(p,v,r)
    context=dict(observed_as_of=p['base']['as_of'],completed_market_session='2026-10-28',
        freshness_by_source={},required_market_fields={'state':'NOT_CHECKED'},current_price_denials=[],source_revisions={})
    a=m.output_eligibility(result['decision'],mode='DATED_REPLAY',**context)
    b=m.output_eligibility(result['decision'],mode='DAILY_NO_SEND',**context)
    assert a['decision_sha256']==b['decision_sha256']==result['decision_sha256']
    assert a!=b and not a['send'] and not b['send']


def test_unified_version_bound_before_approval_or_model_call():
    from test_vnext_balanced_stage_review import cap,MemoryController
    from test_vnext_balanced_research import fixture as old_fixture
    p,v,r=old_fixture();old,_=cap(p,v,r)
    p2,v2,r2=fixture();bundle=m.build_bundle(p2,registry=r2)
    with pytest.raises(ValueError,match='VERSION_MISMATCH_PRECALL'):
        MemoryController().run_stage(invocation_id='unified',account='test',packet=bundle,
            stage='ADJUDICATION',version=stage.UNIFIED,knowledge={},registry=r2,
            source_loader=lambda:bundle,approval=lambda _:pytest.fail('approval called'),
            account_lease=lambda:None,invoke=lambda *_:pytest.fail('model called'),prior=old)
    schema=stage.output_schema(bundle,stage.UNIFIED)
    assert schema['properties']['security_id']['const']==v2['security_id']
    assert m.ENABLED_BY_DEFAULT is False


def test_adjudication_change_must_explain_not_silently_flip():
    _,v,_=fixture();changed=deepcopy(v);changed['valuation']['judgment']='BURDENSOME'
    with pytest.raises(ValueError,match='change_explanation'):m.validate_transition(changed,v)


@pytest.mark.parametrize('enabled,primary,review',[(False,False,object()),(True,True,object()),(True,False,None)])
def test_invalid_unified_dispatch_rejected_before_capture(enabled,primary,review):
    from types import SimpleNamespace
    from app.services.vnext_daily_bridge import DailyResearchBridge
    bridge=DailyResearchBridge.__new__(DailyResearchBridge)
    bridge._source=lambda *a,**k:pytest.fail('source capture reached')
    controller=SimpleNamespace(enabled=True,config=SimpleNamespace(environment='test',mode='write'))
    with pytest.raises(ValueError,match='unified_'):
        bridge.execute(controller,allow_capture=True,allow_primary=primary,
            unified_review=review,unified_enabled=enabled)
