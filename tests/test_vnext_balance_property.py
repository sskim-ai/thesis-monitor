"""Synthetic arithmetic/authority boundaries; no live issuer or model approval."""
from copy import deepcopy
import json
import pytest
from app.services import bounded_financial_projection as projection
from app.services import vnext_financial_reuse as reuse
from app.services import vnext_unified_judgment as engine
from test_vnext_unified_judgment import fixture


def context(monkeypatch, tmp_path, security=None):
    security = security or dict(ticker='NEW', canonical_security_id='KR:NEW',
        canonical_company_id='DART:12345678', country='KR', corp_code='12345678')
    plan = dict(provider='opendart', issuer='12345678', ticker=security['ticker'],
        security=security, run_id='synthetic-frozen-generation', cutoff='2026-10-30T00:00:00+00:00')
    filing = dict(role='current', receipt_no='20260814000001', basis='CFS',
        business_year=2026, report_code='11012', receipt_date='2026-08-14')
    rows = [dict(rcept_no=filing['receipt_no'], corp_code=plan['issuer'], bsns_year='2026',
        reprt_code='11012', fs_div='CFS', sj_div='BS', account_id='ifrs-full_'+name,
        account_nm=name, thstrm_amount=str(value), currency='KRW', account_detail='-',
        thstrm_nm='Current half year', thstrm_dt='2026.06.30', ord=str(i))
        for i,(name,value) in enumerate([('Assets',100),('Liabilities',40),('Equity',60)])]
    payload = dict(status='000', list=rows)
    monkeypatch.setattr(projection, 'project', lambda *a, **kw: {})
    monkeypatch.setattr(projection, '_raw', lambda *a: json.dumps(payload).encode())
    args = dict(plan=plan, acquisition=dict(selected_filings=[filing],
        documents=[dict(filing=filing, artifact='statement.json')]), directory=tmp_path,
        receipts=[], expected_projection={}, security=security)
    facts = reuse.replay_reported_context(**args)['facts']
    assert len(facts) == 3
    return facts, security, payload, args


@pytest.mark.parametrize('identity', ['KR:NEW','US:NEW','US:NEW_ADS'])
def test_generic_exact_components_not_direction(monkeypatch, tmp_path, identity):
    security=dict(ticker='NEW',canonical_security_id=identity,canonical_company_id='DART:12345678',
        country=identity[:2],corp_code='12345678')
    facts, security, _, _ = context(monkeypatch,tmp_path,security)
    p=reuse.balance_composition_property(facts,security)
    assert p['factual_arithmetic_supported'] and p['residual']=='0'
    assert p['component_fractions']['equity']==dict(numerator='60',denominator='100')
    assert not any(p[k] for k in ('property_interpretation_qualified',
        'business_driver_eligible','valuation_metric_eligible','overall_direction_eligible',
        'independent_corroboration','current_qualified'))


@pytest.mark.parametrize('key,value', [('currency','USD'),('unit_scale',1000),
    ('source_receipt','amended'),('source_generation','new'),('period_end','2026-09-30'),
    ('statement_basis','separate'),('semantic','ifrs-full_EquityAttributableToOwnersOfParent'),
    ('current_value',999),('direction_allowed',True),('recurrence_verified',True),
    ('context_projection_sha256','f'*64)])
def test_forged_fields_fail_original_live_owner(monkeypatch,tmp_path,key,value):
    facts,security,_,_=context(monkeypatch,tmp_path)
    facts=deepcopy(facts);facts[0]['fields'][key]=value
    with pytest.raises(ValueError):reuse.balance_composition_property(facts,security)


@pytest.mark.parametrize('values,accepted', [([100,40,59],False),([0,0,0],False),
    ([100,120,-20],True),([100,0,100],True)])
def test_arithmetic_not_normative_quality(monkeypatch,tmp_path,values,accepted):
    _,security,payload,args=context(monkeypatch,tmp_path)
    for row,value in zip(payload['list'],values):row['thstrm_amount']=str(value)
    facts=reuse.replay_reported_context(**args)['facts']
    p=reuse.balance_composition_property(facts,security)
    assert p['factual_arithmetic_supported']==accepted
    assert p['business_driver_eligible'] is False


def test_source_mutation_and_duplicate_not_accepted(monkeypatch,tmp_path):
    facts,security,payload,_=context(monkeypatch,tmp_path)
    assert not reuse.balance_composition_property(facts+[facts[0]],security)['factual_arithmetic_supported']
    payload['list'][0]['thstrm_amount']='101'
    with pytest.raises(ValueError):reuse.balance_composition_property(facts,security)


def test_sec_parent_equity_never_total_equity(monkeypatch,tmp_path):
    from test_vnext_cfbs_context import case
    args,_=case(monkeypatch,tmp_path)
    facts=reuse.replay_reported_context(**args)['facts']
    assert reuse.balance_composition_property(facts,args['security'])['reason']=='EXACT_TOTAL_BALANCE_COMPONENTS_REQUIRED'


def integrated(monkeypatch,tmp_path):
    p,v,r=fixture()
    facts,_,_,_=context(monkeypatch,tmp_path,p['base']['public_security'])
    for fact in facts:
        row=deepcopy(p['base']['evidence'][0])
        row.update(ref='balance-'+fact['fields']['metric'],field='financial.'+fact['fields']['metric'],
            data=fact,source_sha=fact['fields']['original_raw_sha256'])
        p['base']['evidence'].append(row)
    return p,v,r


def test_optin_prompt_single_engine_and_modes(monkeypatch,tmp_path):
    p,v,r=integrated(monkeypatch,tmp_path)
    plain=engine.build_bundle(p,registry=r)
    assert 'factual_properties' not in plain
    b=engine.build_bundle(p,registry=r,factual_properties=True)
    assert b['factual_properties'][0]['factual_arithmetic_supported']
    assert b['admissibility']==plain['admissibility']
    assert 'DATED_FACTUAL_ACCOUNTING_EXPLANATION_ONLY' in engine.prompt(b,'BLIND',knowledge={},registry=r)
    result=engine.validate_and_render(v,b,registry=r,economic_loader=lambda:p,factual_properties=True)
    plain_result=engine.validate_and_render(v,plain,registry=r,economic_loader=lambda:p)
    assert result['decision']['model_output']==plain_result['decision']['model_output']
    c=dict(observed_as_of=p['base']['as_of'],completed_market_session='2026-10-28',freshness_by_source={},
        required_market_fields={'state':'NOT_CHECKED'},current_price_denials=[],source_revisions={})
    a=engine.output_eligibility(result['decision'],mode='DATED_REPLAY',**c)
    d=engine.output_eligibility(result['decision'],mode='DAILY_NO_SEND',**c)
    assert a['decision_sha256']==d['decision_sha256'] and not a['send'] and not d['send']


@pytest.mark.parametrize('axis',['driver','valuation','overall','holder','property_forge','revoked'])
def test_p1_cannot_issue_economic_rights(monkeypatch,tmp_path,axis):
    p,v,r=integrated(monkeypatch,tmp_path)
    b=engine.build_bundle(p,registry=r,factual_properties=True)
    if axis=='driver':v['economic_drivers_positive'][0]['refs']=['balance-assets']
    elif axis in ('valuation','overall','holder'):v['holder_virtual' if axis=='holder' else axis]['refs']=['balance-assets']
    elif axis=='property_forge':b['factual_properties'][0]['overall_direction_eligible']=True
    else:
        r.revoke(v['security_id'],p['base']['evidence'][-1]['source_sha'])
        rebuilt=engine.build_bundle(p,registry=r,factual_properties=True)
        assert not rebuilt['factual_properties'][0]['factual_arithmetic_supported']
    with pytest.raises(ValueError):
        engine.validate_and_render(v,b,registry=r,economic_loader=lambda:p,factual_properties=True)
