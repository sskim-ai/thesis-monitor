from copy import deepcopy

import pytest

from app.services.accepted_calibration_message_service import (
    AcceptedMarketCalibration, calibration_market_render, digest,
)
from app.services.accepted_directional_balance_service import accepted_directional_balance, compatible_buy_scores
from app.services.market_numeric_claim_service import (
    numeric_catalog, validate_catalog, render_typed_market_facts, final_market_numeric_audit,
    narrative_errors,
)
from tests.test_m12ds_r4_r1_night_eligibility import row as night_row


def source():
    facts = [dict(fact_id=ref, fact_type='market_index', as_of_date='2026-09-21',
                  fields=dict(label=label, return_pct=value, quality='fresh',
                              today_signal_eligible=True, temporal_role='CURRENT_OBSERVATION'))
             for ref, label, value in [('index:large','Large 500',1.0),('index:growth','Growth',2.0)]]
    facts += [dict(fact_id='relative', fact_type='market_growth_relative', as_of_date='2026-09-21',
                   fields=dict(subject_label='Growth',benchmark_label='Large 500',relative_return_pct=1.0,
                               source_fact_ids=['index:growth','index:large'],today_signal_eligible=True,
                               temporal_role='CURRENT_OBSERVATION')),
              dict(fact_id='rate',fact_type='market_real_yield',as_of_date='2026-09-21',
                   fields=dict(label='10년 실질금리',level_pct=2.34,previous_level_pct=2.33,
                               today_signal_eligible=True,temporal_role='CURRENT_OBSERVATION'))]
    registry = [dict(fact_id=f['fact_id'],field_path='fields.'+key,value=f['fields'][key],
                     unit='pct',registered=allowed,prose_allowed=allowed,scope='market')
                for f in facts for key in ('return_pct','relative_return_pct','level_pct','previous_level_pct')
                if key in f['fields'] for allowed in [key!='previous_level_pct']]
    return dict(session=dict(market='us',assessment_date='2026-09-22',latest_completed_regular_session_date='2026-09-21'),
                fact_catalog=facts,numeric_registry=registry,night_futures=[])


def catalog(s):
    return numeric_catalog(s,market='us',assessment_date='2026-09-22',eligible_refs=[f['fact_id'] for f in s['fact_catalog']])


def test_market_numbers_bind_labels_dates_units_and_derived_parents():
    s = source()
    c = catalog(s)
    assert validate_catalog(c,s)['status']=='PASS'
    text = render_typed_market_facts(c,s)
    assert '2.34%' in text and '2.33' not in text
    assert 'Large 500 대비 Growth: +1.00pp' in text
    relation = next(c for c in c['claims'] if c['derivation_formula'])
    assert relation['input_fact_refs']==['index:growth','index:large']
    assert all(x['source_fact_ref'] and x['field_path'] and x['observation_date'] and x['formatter']
               for claim in c['claims'] for x in claim['components'])
    assert final_market_numeric_audit(text+'\n\n시장 해석',c,s,'시장 해석')['status']=='PASS'
    assert final_market_numeric_audit(text+'\n추가 2.33%',c,s,'시장 해석')['status']=='FAIL'


@pytest.mark.parametrize('literal',['금리 2.33%','10년물','202609','2026-09-21','S&P500','숫자 ２','수익 ½'])
def test_no_date_tenor_maturity_or_unicode_numeric_exemption(literal):
    assert narrative_errors(dict(rates_or_macro_context=literal))


@pytest.mark.parametrize('mutation', ['date','stale','quality','unit','value','permission','label'])
def test_invalid_market_value_never_rendered(mutation):
    s=source()
    f=s['fact_catalog'][0]
    r=s['numeric_registry'][0]
    if mutation=='date':
        f['as_of_date']='2026-09-23'
    elif mutation=='stale':
        f['fields']['today_signal_eligible']=False
    elif mutation=='quality':
        f['fields']['quality']='unavailable'
    elif mutation=='unit':
        r['unit']='USD'
    elif mutation=='value':
        r['value']=99
    elif mutation=='permission':
        r['prose_allowed']=False
    else:
        f['fields'].pop('label')
    c=catalog(s)
    assert not any(x['field_path']=='fields.return_pct' and x['source_fact_ref']=='index:large'
                   for claim in c['claims'] if claim['claim_type']=='OBSERVED_MARKET_VALUE'
                   and not claim['derivation_formula'] for x in claim['components'])


def test_stale_or_wrong_relative_parent_not_consumed():
    for key,value in [('as_of_date','2026-09-18'),('fact_id','different')]:
        s=source()
        s['fact_catalog'][0][key]=value
        assert not any(c['derivation_formula'] for c in catalog(s)['claims'])
    s=source()
    s['fact_catalog'][2]['fields']['relative_return_pct']=99
    s['numeric_registry'][2]['value']=99
    assert not any(c['derivation_formula'] for c in catalog(s)['claims'])


def test_catalog_drift_and_session_identity_fail_closed():
    s=source()
    c=catalog(s)
    c['claims'][1]['rendered_text']+=' 99%'
    assert validate_catalog(c,s)['status']=='FAIL'
    for key,value in [('assessment_date','2026-09-23'),('market','kr'),('latest_completed_regular_session_date','2026-09-23')]:
        changed=deepcopy(s)
        changed['session'][key]=value
        with pytest.raises(ValueError,match='session_identity'):
            catalog(changed)


@pytest.mark.parametrize('native', [False,True,'public_projection'])
def test_night_exact_final_pair_and_timeframes_bind_in_actual_market_renderer(native):
    s=source()
    n=night_row()
    s['night_futures']=[n]
    s['fact_catalog'].append(dict(fact_id=n['fact_id'],fact_type='night_futures',as_of_date=n['session_date'],
                                  fields=deepcopy(n) if native else {k:v for k,v in n.items() if k!='night_timeframes'}))
    if native=='public_projection':
        from app.services.ai_review_service import _public_value
        s['fact_catalog'][-1]['fields']=_public_value(s['fact_catalog'][-1]['fields'])
    c=catalog(s)
    claims=[x for x in c['claims'] if x['claim_type']=='OFFICIAL_NIGHT']
    assert len(claims)==1
    assert '종가 101.00' in claims[0]['rendered_text'] and '202612' in claims[0]['rendered_text']
    decision=dict(market='US',regime='MIXED',confidence='MEDIUM',breadth_state='시장 폭은 혼재합니다.',
                  leadership='일부 업종이 주도합니다.',flows_or_participation='수급은 확인이 필요합니다.',
                  rates_or_macro_context='야간선물은 다음 한국 시장의 참고 자료입니다.')
    receipt=dict(status='PASS',errors=[],market='us',assessment_date='2026-09-22',
                 source_context_sha256=digest(s),decision_sha256=digest(decision),numeric_catalog_sha256=digest(c))
    plan=AcceptedMarketCalibration(market='us',assessment_date='2026-09-22',source_context=s,decision=decision,
                                   acceptance=receipt,acceptance_sha256=digest(receipt),numeric_catalog=c)
    text=calibration_market_render(plan)
    assert claims[0]['rendered_text'] in text
    bad=deepcopy(s)
    bad['night_futures'][0]['reference_price']=99
    assert not any(x['claim_type']=='OFFICIAL_NIGHT' for x in catalog(bad)['claims'])
    assert validate_catalog(c,bad)['status']=='FAIL'
    wrong=deepcopy(s)
    wrong['fact_catalog'][-1]['fields']['night_timeframes']={'wrong':'frames'}
    with pytest.raises(ValueError,match='binding_mismatch'):
        catalog(wrong)
    n['night_timeframes']['daily']['return_pct']=2
    s['night_futures']=[n]
    assert not any(x['claim_type']=='OFFICIAL_NIGHT' for x in catalog(s)['claims'])


def test_kr_typed_numeric_capture_and_us_session_separation():
    s=source()
    s['session']['market']='kr'
    c=numeric_catalog(s,market='kr',assessment_date='2026-09-22',eligible_refs=[f['fact_id'] for f in s['fact_catalog']])
    text=render_typed_market_facts(c,s)
    assert text.startswith('한국 시장 점검')
    assert final_market_numeric_audit(text+'\n\n해석',c,s,'해석')['status']=='PASS'


def test_semantic_validator_rejects_balance_before_render(monkeypatch):
    from scripts import m12ds_r4_r4_policy as policy
    monkeypatch.setattr(policy.r3,'validate_decision',lambda *a:dict(status='PASS',errors=[]))
    assert policy.validate_decision(dict(overall_direction='HOLD',directional_buy_score=6),{}, {})['status']=='FAIL'
    assert policy.validate_decision(dict(overall_direction='HOLD',directional_buy_score=5),{}, {})['status']=='PASS'


@pytest.mark.parametrize('direction,values',[('BUY',tuple(x/2 for x in range(12,21))),('HOLD',(4.5,5,5.5)),('SELL',tuple(x/2 for x in range(9)))])
def test_exact_balance_contract(direction,values):
    assert compatible_buy_scores(direction)==values
    for buy in values:
        pair=accepted_directional_balance(buy,direction)
        assert pair.buy+pair.sell==10


@pytest.mark.parametrize('direction,buy',[('HOLD',6.5),('HOLD',4),('HOLD',6),('BUY',5.8),('BUY',6.6),('SELL',5),('BUY',True)])
def test_r3_invalid_balances_rejected_without_rounding_or_relabel(direction,buy):
    with pytest.raises(ValueError):
        accepted_directional_balance(buy,direction)


def test_schema_uses_the_same_canonical_allowed_sets(monkeypatch):
    from scripts import m12ds_r4_r4_schemas as schema
    monkeypatch.setattr(schema.r3,'decision_schema',lambda *a:dict(properties=dict(overall=dict(anyOf=[
        dict(properties=dict(overall_direction=dict(enum=[d]))) for d in ('BUY','HOLD','SELL')]))))
    result=schema.decision_schema({}, {}, {})
    for branch in result['properties']['overall']['anyOf']:
        p=branch['properties']
        assert tuple(p['directional_buy_score']['enum'])==compatible_buy_scores(p['overall_direction']['enum'][0])
