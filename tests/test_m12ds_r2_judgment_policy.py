from copy import deepcopy
import json

import pytest
from scripts.websocket_timeout_runtime_review_first_a_closeout import validate_json_schema

from scripts import m12ds_r2_judgment_policy as p
from scripts import m12ds_r2_schemas as s
from scripts import m12ds_r2_market as m
from scripts.m12ds_r2_ranges import valuation_policy, materialize_ranges, eligible_range_inputs
from scripts.m12cs_r1_provider_schema import project_provider_wire_schema
from scripts.m12da_source_use_contract import (
    SourceUse, build_trusted_source_authority_manifest, freeze_source_use_input_expectation,
    build_source_use_projection, freeze_source_use_binding, canonical_sha256,
)
from test_m12cp_valuation_policy import _subject
from test_m12cr_r1_typed_quality_contract import _security_packet
from scripts.m12cr_r1_typed_quality_contract import project_security_valuation_basis


def data(value=20, prior=None, ticker='FICTIONAL'):
    payload = {'operating_income':{'value':value}}
    if prior is not None:
        payload = {'metric':'operating_income','current_value':value,'prior_comparable_value':prior}
    rows = [{'ref_id':'source:business','category':'earnings','statement':json.dumps(payload),'as_of':'2026-06-30'}]
    authority = {'authority_records':[{'ref_id':rows[0]['ref_id'],'authority_state':'RESOLVED',
                                      'allowed_uses':['OVERALL_DIRECTION','CONTEXT']}]}
    observation = next(iter(p.observations(rows,authority).values()))
    claim = {'effect':observation['effect'],'text':'Model interpretation',
             'evidence_refs':[observation['source_ref']], 'observation_ids':[observation['observation_id']],
             'materiality':'CONTEXT_ONLY'}
    return rows,authority,claim


def bind(core, rows, *, denied=False, ticker='FICTIONAL'):
    refs = [r['ref_id'] for r in rows]
    catalog = {'ticker':ticker,'atomic_claims':core['atomic_claims'],'all_evidence_refs':refs,
               'core_evidence_refs':refs,'claim_refs':list(core['effects']), 'timing_evidence_refs':[],
               'valuation_evidence_refs':[], 'material_disclosure_failure_refs':[], 'positive_quality_refs':[]}
    uses = [SourceUse.CONTEXT] if denied else [SourceUse.CONTEXT,SourceUse.OVERALL_DIRECTION,SourceUse.PASS_A_ARCHETYPE]
    overrides = [{'ref_id':r['ref_id'],'catalog_sha256':canonical_sha256(catalog),
        'source_metadata_sha256':canonical_sha256(r),'source_type':'frozen_legacy_business_evidence',
        'source_scope':'exact_source_business_decision_owner','authority_basis':'test_only_exact_owner',
        'allowed_uses':uses,'prohibited_uses':[u for u in SourceUse if u not in uses]} for r in rows]
    authority = build_trusted_source_authority_manifest(ticker=ticker,source_generation_id='source',catalog=catalog,
        source_metadata=rows,trusted_owner_overrides=overrides)
    expectation = freeze_source_use_input_expectation(ticker=ticker,source_generation_id='source',
        execution_generation_id='execution',catalog=catalog,source_metadata=rows,authority_manifest=authority)
    projection = build_source_use_projection(ticker=ticker,input_generation_id='source',execution_generation_id='execution',
        catalog=catalog,authority_manifest=authority,current_input_expectation=expectation)
    binding = freeze_source_use_binding(projection=projection,authority_manifest=authority,current_input_expectation=expectation)
    chain = dict(projection=projection,binding=binding,expectation=expectation,authority=authority,
                 source_generation_id='source',execution_generation_id='execution')
    return chain,catalog


def capability(value=20, *, caution=False, risk=False, denied=False):
    rows,authority,claim = data(value)
    if risk:
        claim['materiality']='ACTIVE_MATERIAL_RISK'
    raw = {'claims':[claim]}
    if caution:
        raw['claims'].append(dict(effect='CONFIDENCE_ONLY',text='Recurrence is not established.',
                                 evidence_refs=['source:business'],observation_ids=[],materiality='CONTEXT_ONLY'))
    core = p.materialize_core('FICTIONAL',raw,rows,authority)
    chain,catalog = bind(core,rows,denied=denied)
    return p.axis_capability(core,chain,catalog,rows),core,chain,catalog,rows


def ranges():
    return {'fundamental_valid':False,'compensating_discount':False}


def decision(cap, *, overall='BUY', reason='OBSERVED_POSITIVE_DOMINANT', holder='HOLDABLE', buyer='WAIT'):
    return dict(overall_direction=overall,overall_reason_class=reason,confidence='MEDIUM',directional_buy_score=5,
        supporting_refs=cap['positive'],contradicting_refs=cap['negative'],confidence_caution_refs=cap['confidence'],
        data_quality_refs=cap['quality'],reevaluation_refs=cap['condition'],overall_reason='Observed evidence.',
        holder=holder,holder_reason_class='OBSERVED_OPERATING_STRESS' if holder=='REVIEW' else 'THESIS_INTACT_NO_ACTIVE_MATERIAL_TRIGGER',
        holder_reason_evidence_refs=cap['holder_risk'] if holder=='REVIEW' else cap['holder_support'],holder_reason='Evidence-driven.',
        new_buyer=buyer,new_buyer_reason_class='ACTIVE_ADVERSE_UNCOMPENSATED' if buyer=='AVOID' else 'VALUATION_UNRESOLVED',
        new_buyer_risk_refs=cap['holder_risk'] if buyer=='AVOID' else [],new_buyer_reason='Independent axis.',
        tactical_choice='UNRESOLVED')


def nested(row):
    return {'overall':{k:v for k,v in row.items() if k.startswith('overall_') or k in (
        'confidence','directional_buy_score','supporting_refs','contradicting_refs','confidence_caution_refs','data_quality_refs','reevaluation_refs')},
        'holder_axis':{k:v for k,v in row.items() if k.startswith('holder')},
        'new_buyer_axis':{k:v for k,v in row.items() if k.startswith('new_buyer')},'tactical_choice':row['tactical_choice']}


def test_positive_plus_uncertainty_no_fabricated_bearish_counterweight():
    cap,*_ = capability(caution=True)
    assert cap['positive'] and cap['confidence'] and not cap['negative']
    row = decision(cap,overall='HOLD',reason='POSITIVE_BUT_CONFIDENCE_CAPPED')
    assert p.validate_decision(row,cap,ranges())['status']=='PASS'
    schema = s.decision_schema(cap,ranges(),{})
    wire,_ = project_provider_wire_schema(schema)
    for shape in (schema,wire):
        assert not validate_json_schema(nested(row),shape)
    row['overall_direction']='SELL'
    row['overall_reason_class']='OBSERVED_NEGATIVE_DOMINANT'
    assert p.validate_decision(row,cap,ranges())['status']=='FAIL'


def test_caution_add_remove_does_not_create_direction():
    plain,*_ = capability()
    cautious,*_ = capability(caution=True)
    assert plain['positive']==cautious['positive']
    assert plain['negative']==cautious['negative']==[]
    rows,authority,_ = data()
    raw = {'claims':[dict(effect='CONFIDENCE_ONLY',text='Limited trend.',evidence_refs=['source:business'],
                          observation_ids=[],materiality='CONTEXT_ONLY')]}
    core = p.materialize_core('FICTIONAL',raw,rows,authority)
    chain,catalog = bind(core,rows)
    cap = p.axis_capability(core,chain,catalog,rows)
    assert cap['positive']==cap['negative']==[]
    with pytest.raises(ValueError,match='HOLDER_AXIS_CONTRACT_DEPENDENCY'):
        s.decision_schema(cap,ranges(),{})


def test_observed_loss_changes_eligibility_not_automatic_reduce():
    positive,*_ = capability(20)
    negative,*_ = capability(-20,risk=True)
    assert positive['positive'] and negative['negative']
    assert negative['holder_risk'] and not negative['holder_reduce']
    row = decision(negative,overall='SELL',reason='OBSERVED_NEGATIVE_DOMINANT',holder='REVIEW',buyer='AVOID')
    assert p.validate_decision(row,negative,ranges())['status']=='PASS'
    assert not validate_json_schema(nested(row),s.decision_schema(negative,ranges(),{}))
    row['holder']='REDUCE'
    assert p.validate_decision(row,negative,ranges())['status']=='FAIL'
    row['holder']='HOLDABLE'
    assert p.validate_decision(row,negative,ranges())['status']=='FAIL'


@pytest.mark.parametrize('holder',['HOLDABLE','REVIEW'])
def test_empty_holder_refs_rejected_internal_and_provider(holder):
    cap,*_ = capability(-20,risk=True) if holder=='REVIEW' else capability()
    row = decision(cap,overall='SELL' if holder=='REVIEW' else 'BUY',
                   reason='OBSERVED_NEGATIVE_DOMINANT' if holder=='REVIEW' else 'OBSERVED_POSITIVE_DOMINANT',holder=holder)
    schema = s.decision_schema(cap,ranges(),{})
    wire,_ = project_provider_wire_schema(schema)
    row['holder_reason_evidence_refs']=[]
    for shape in (schema,wire):
        assert validate_json_schema(nested(row),shape)
    assert p.validate_decision(row,cap,ranges())['status']=='FAIL'


@pytest.mark.parametrize('field',['supporting_refs','contradicting_refs','holder_reason_evidence_refs','new_buyer_risk_refs'])
def test_unknown_cross_axis_ref_denied(field):
    cap,*_ = capability(caution=True)
    row = decision(cap)
    row[field]=cap['confidence']
    assert p.validate_decision(row,cap,ranges())['status']=='FAIL'


@pytest.mark.parametrize('mutation',['claim','effects','metadata','authority','generation'])
def test_binding_tamper_fails_closed(mutation):
    cap,core,chain,catalog,rows = capability()
    if mutation=='claim':
        core['atomic_claims'][0]['claim']['text']='tampered'
    elif mutation=='effects':
        core['effects'][cap['positive'][0]]['effect']='DIRECTIONAL_NEGATIVE'
    elif mutation=='metadata':
        rows[0]['statement']='changed'
    elif mutation=='authority':
        chain['binding']['binding_sha256']='invalid'
    else:
        chain['execution_generation_id']='other'
    with pytest.raises(ValueError):
        p.axis_capability(core,chain,catalog,rows)


def test_claim_effect_cannot_widen_raw_source_permission():
    with pytest.raises(ValueError,match='without_source_entitlement'):
        capability(denied=True)


@pytest.mark.parametrize('effect',['CONFIDENCE_ONLY','REEVALUATION_CONDITION','DATA_QUALITY_ONLY'])
def test_non_observed_claim_cannot_borrow_observation(effect):
    rows,authority,claim = data()
    claim['effect']=effect
    with pytest.raises(ValueError):
        p.materialize_core('FICTIONAL',{'claims':[claim]},rows,authority)


def valuation(pe=(130,150),pb=(70,90),tier='BASE'):
    subject = _subject(pe=pe,pb=pb)
    subject['current_price']={'value':100,'currency':'USD'}
    classification = dict(archetype='STRUCTURAL_CYCLICAL_LEADER',valuation_regime_tier=tier)
    basis = project_security_valuation_basis(_security_packet())
    return subject,classification,basis


def test_method_conflict_no_pb_dominance_and_order_invariance():
    subject,classification,basis = valuation()
    first = valuation_policy(subject,classification,basis)
    subject['fundamental_candidates'].reverse()
    assert first==valuation_policy(subject,classification,basis)
    assert first['method_conflict'] and not first['fundamental_valid']
    assert len(first['method_audit'])==2


def test_single_earnings_method_low_confidence_and_aligned_intersection():
    subject,classification,basis = valuation(pb=None)
    single = valuation_policy(subject,classification,basis)
    assert single['fundamental_entry_status']=='SINGLE_METHOD_LOW_CONFIDENCE'
    assert single['fundamental_entry_confidence']=='LOW'
    subject,classification,basis = valuation(pe=(130,150),pb=(140,170))
    intersection = valuation_policy(subject,classification,basis)
    assert intersection['option']['low']==140 and intersection['option']['high']==150
    assert intersection['compensating_discount']


def test_unresolved_security_basis_cannot_create_discount():
    subject,classification,basis = valuation(pb=None)
    basis['state']='UNRESOLVED'
    result = valuation_policy(subject,classification,basis)
    assert not result['fundamental_valid'] and not result['compensating_discount']


def test_wait_tactical_zone_disjoint_from_fundamental_and_unresolved_allowed():
    subject,classification,basis = valuation()
    value = valuation_policy(subject,classification,basis)
    no_zone = materialize_ranges(value,{},'UNRESOLVED')
    cat = {'tactical_candidates':[dict(candidate_id='zone',low=80,high=90,currency='USD',evidence_refs=['technical:1'])]}
    zone = materialize_ranges(value,cat,'zone')
    assert zone['tactical_watch_status']=='RESOLVED'
    assert zone['render_warning']=='TACTICAL_WATCH_ZONE != FAIR_VALUE'
    assert {k:v for k,v in no_zone.items() if k.startswith('fundamental')}=={
        k:v for k,v in zone.items() if k.startswith('fundamental')}
    with pytest.raises(ValueError):
        materialize_ranges(value,cat,'UNRESOLVED')


def test_technical_range_cannot_create_attractive_or_avoid():
    cap,*_ = capability()
    row = decision(cap,buyer='ATTRACTIVE')
    row['new_buyer_reason_class']='VALID_FUNDAMENTAL_DISCOUNT'
    assert p.validate_decision(row,cap,ranges())['status']=='FAIL'
    row['new_buyer']='AVOID'
    row['new_buyer_reason_class']='ACTIVE_ADVERSE_UNCOMPENSATED'
    assert p.validate_decision(row,cap,ranges())['status']=='FAIL'


def test_range_source_authority_and_currency_never_bypassed():
    _,_,chain,_,_ = capability()
    subject = {'ticker':'FICTIONAL','current_price':{'value':100,'currency':'USD'},
               'fundamental_candidates':[{'candidate_id':'x','ticker':'FICTIONAL','currency':'USD','evidence_refs':['source:business']}]}
    selected,_,excluded = eligible_range_inputs(subject,{},chain)
    assert not selected['fundamental_candidates'] and excluded


def test_market_export_nonfeedback_session_guard_and_schema_parity():
    packet = {'market':'us','assessment_date':'2026-09-22','stocks':[{'decision':'UNTOUCHED'}],
              'market_context':{'fact_catalog':[], 'adapter_context':{
                  'session_context':{'latest_completed_regular_session_date':'2026-09-21'},'session_date':'2026-09-21',
                  'indices':[{'source_ref':'old','as_of_date':'2026-09-18'}, {'source_ref':'future','as_of_date':'2026-09-22'}]}}}
    frozen = deepcopy(packet)
    context = m.market_context(packet)
    assert not context['facts'] and set(context['suppressed_refs'])=={'old','future'}
    assert m.eligible_regimes(context)==['DATA_INSUFFICIENT']
    assert packet==frozen
    row = dict(market='US',regime='DATA_INSUFFICIENT',confidence='LOW',breadth_state='Unavailable',
               leadership='Unavailable',flows_or_participation='Unavailable',rates_or_macro_context='Unavailable',
               supporting_refs=[],contradicting_refs=[])
    assert not validate_json_schema(row,m.market_schema(context))
    assert m.validate_market(row,context)['status']=='PASS'
    row['regime']='BROAD_RISK_ON'
    assert m.validate_market(row,context)['status']=='FAIL'
    assert validate_json_schema(row,m.market_schema(context))


def test_market_no_stock_objects_referenced():
    import inspect
    from scripts.m12ds_r2_shadow_reproof import Reproof
    assert 'self.markets' not in inspect.getsource(Reproof.before_a)
    assert 'self.markets' not in inspect.getsource(Reproof.before_b)
    assert 'self.markets' not in inspect.getsource(Reproof.core)


def test_configured_condition_preserved_not_observed():
    from test_logical_condition_service import _source
    condition = _source().model_dump(mode='json')
    row = {'ref_id':'condition:future','category':'thesis','statement':'Future weakening condition.',
           'logical_condition':condition}
    authority = {'authority_records':[{'ref_id':row['ref_id'],'authority_state':'RESOLVED','allowed_uses':['CONTEXT','OVERALL_DIRECTION']}]}
    assert not p.observations([row],authority)
    claim = dict(effect='REEVALUATION_CONDITION',text='Future risk.',evidence_refs=[row['ref_id']],
                 observation_ids=[],materiality='CONTEXT_ONLY')
    core = p.materialize_core('GENERIC',{'claims':[claim]},[row],authority)
    assert core['atomic_claims'][0]['claim']['logical_condition']['source_condition_ref']=='K1'
    assert next(iter(core['effects'].values()))['effect']=='REEVALUATION_CONDITION'
    claim['effect']='DIRECTIONAL_NEGATIVE'
    with pytest.raises(ValueError):
        p.materialize_core('GENERIC',{'claims':[claim]},[row],authority)


def test_truncated_fact_projection_exact_binding_without_new_source():
    fields = {'metric':'revenue','current_value':120,'prior_comparable_value':100,'padding':'x'*2000}
    fact = {'fact_id':'earnings_comparison:fictional','as_of_date':'2026-06-30','fields':fields}
    row = {'ref_id':'canonical:'+fact['fact_id'],'source_ref':'stock.fact_catalog.'+fact['fact_id'],
           'category':'earnings','as_of':fact['as_of_date'],'statement':p._compact(fields)}
    packet = {'stocks':[{'ticker':'FICTIONAL','fact_catalog':[fact]}]}
    authority = {'authority_records':[{'ref_id':row['ref_id'],'authority_state':'RESOLVED','allowed_uses':['OVERALL_DIRECTION']}]}
    assert not p.observations([row],authority)
    bound = p.frozen_fact_fields(packet,'FICTIONAL',[row])
    observations = p.observations([row],authority,bound)
    assert len(observations)==1 and next(iter(observations.values()))['effect']=='DIRECTIONAL_POSITIVE'
    row['statement']='changed'
    with pytest.raises(ValueError,match='projection_mismatch'):
        p.frozen_fact_fields(packet,'FICTIONAL',[row])


def test_revenue_presence_never_claims_growth_or_profitability():
    rows,authority,_ = data()
    rows[0]['statement']=json.dumps({'revenue':{'value':25}})
    observation = next(iter(p.observations(rows,authority).values()))
    assert observation['prior_value'] is None
    assert 'does not establish growth, profitability or durability' in observation['text']
    assert 'higher' not in observation['text']
