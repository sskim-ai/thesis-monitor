"""Synthetic field mechanics, not real issuer approval or accepted judgments."""
from copy import deepcopy
import json
import pytest
from app.services import bounded_financial_projection as projection
from app.services import vnext_financial_reuse as reuse
from app.services import vnext_unified_judgment as engine
from test_vnext_unified_judgment import fixture


def case(monkeypatch, tmp_path, security=None):
    security=security or dict(ticker='UNSEEN',canonical_security_id='US:UNSEEN',canonical_company_id='CIK:1234',country='US',cik='1234')
    plan=dict(provider='sec_edgar',issuer='1234',ticker=security['ticker'],security=security,
              run_id='synthetic-old-generation',cutoff='2026-10-30T00:00:00+00:00')
    filing=dict(role='current',form='10-Q',accessionNumber='0000001234-26-000001',reportDate='2026-09-30',filingDate='2026-10-20')
    cell=dict(val=-11791,start='2026-01-01',end='2026-09-30',accn=filing['accessionNumber'],
              form='10-Q',filed='2026-10-20',fy=2026,fp='Q3',frame='CY2026Q3YTD')
    payload=dict(cik=1234,facts={'us-gaap':{'NetCashProvidedByUsedInOperatingActivities':{'units':{'USD':[cell]}},
                'Assets':{'units':{'USD':[{k:v for k,v in dict(cell,val=155011).items() if k!='start'}]}}}})
    monkeypatch.setattr(projection,'project',lambda *a,**kw:{})
    monkeypatch.setattr(projection,'_raw',lambda *a:json.dumps(payload).encode())
    args=dict(plan=plan,acquisition=dict(selected_filings=[filing],companyfacts_artifact='raw.json'),
              directory=tmp_path,receipts=[],expected_projection={},security=security)
    return args,payload


def test_exact_ytd_instant_negative_sign_and_no_direction(monkeypatch,tmp_path):
    args,payload=case(monkeypatch,tmp_path)
    result=reuse.replay_reported_context(**args)
    assert len(result['facts'])==2
    cf,bs=result['facts']
    assert cf['fields']['current_value']==-11791
    assert cf['fields']['period_type']=='year_to_date_cumulative'
    assert bs['fields']['period_start']==bs['fields']['period_end']=='2026-09-30'
    assert bs['fields']['period_kind']=='instant'
    assert cf['interpretation_eligible'] is False and cf['fields']['direction_allowed'] is False
    for f in result['facts']: assert reuse.verify_reported_context(f,args['security'])


@pytest.mark.parametrize('key,value',[
    ('period_start','2026-07-01'),('period_kind','instant'),('current_value',11791),
    ('currency','KRW'),('unit_scale',1000000),('statement_basis','separate'),
    ('source_generation','fresh-now'),('issuer_id','9999'),('canonical_security_id','OTHER'),
    ('direction_allowed',True),('valuation_denominator_eligible',True),('recurrence_verified',True),
    ('source_receipt','another-filing'),('semantic','PretaxIncome'),('period_end','2026-06-30')])
def test_rehashed_caller_fact_cannot_override_original(monkeypatch,tmp_path,key,value):
    args,payload=case(monkeypatch,tmp_path);fact=reuse.replay_reported_context(**args)['facts'][0]
    forged=deepcopy(fact);forged['fields'][key]=value
    with pytest.raises(ValueError):reuse.verify_reported_context(forged,args['security'])


@pytest.mark.parametrize('change',['raw','unissued','security','ads','original_projection','path','symlink'])
def test_original_live_replay_and_plain_source_boundaries(monkeypatch,tmp_path,change):
    args,payload=case(monkeypatch,tmp_path);fact=reuse.replay_reported_context(**args)['facts'][0]
    sec=deepcopy(args['security'])
    if change=='raw':payload['facts']['us-gaap']['Assets']['units']['USD'][0]['val']+=1
    elif change=='unissued':fact['fields']['context_projection_sha256']='0'*64
    elif change=='security':sec['canonical_security_id']='OTHER'
    elif change=='ads':sec['adr_ratio']=5
    elif change=='original_projection':monkeypatch.setattr(projection,'project',lambda *a,**kw:{'changed':True})
    else:
        if change=='path':args['receipts']=[dict(logical_id='x:one',artifact='../outside.json')]
        else:
            (tmp_path/'one.plan.json').write_text('{}');(tmp_path/'alias.json').symlink_to(tmp_path/'one.plan.json')
            args['receipts']=[dict(logical_id='x:one',artifact='alias.json')]
        with pytest.raises(ValueError):reuse.replay_reported_context(**args)
        return
    with pytest.raises(ValueError):reuse.verify_reported_context(fact,sec)


@pytest.mark.parametrize('mutation',['issuer','filing_date','currency','instant_start','duplicate','missing_duration'])
def test_source_quality_mutations_not_accepted(monkeypatch,tmp_path,mutation):
    args,payload=case(monkeypatch,tmp_path)
    cf=payload['facts']['us-gaap']['NetCashProvidedByUsedInOperatingActivities']['units']['USD'][0]
    if mutation=='issuer':
        payload['cik']=9999
        with pytest.raises(ValueError,match='issuer'):reuse.replay_reported_context(**args)
        return
    if mutation=='filing_date':cf['filed']='2026-10-19'
    if mutation=='currency':payload['facts']['us-gaap']['NetCashProvidedByUsedInOperatingActivities']['units']={'KRW':[cf]}
    if mutation=='instant_start':payload['facts']['us-gaap']['Assets']['units']['USD'][0]['start']='2026-01-01'
    if mutation=='duplicate':payload['facts']['us-gaap']['NetCashProvidedByUsedInOperatingActivities']['units']['USD'].append(deepcopy(cf))
    if mutation=='missing_duration':del cf['start']
    result=reuse.replay_reported_context(**args)
    metric='assets' if mutation=='instant_start' else 'operating_cashflow'
    assert not any(f['fields']['metric']==metric for f in result['facts'])


def test_original_dart_interim_cf_remains_xbrl_required():
    from app.services.opendart_financial_recovery_service import select_basis_occurrence,FIELD_SPECS
    from app.services.kr_financial_lineage_service import _bounds
    r=dict(account_id='ifrs-full_CashFlowsFromUsedInOperatingActivities',sj_div='CF',thstrm_amount='700',fs_div='CFS')
    selected=select_basis_occurrence([r],FIELD_SPECS['operating_cash_flow'],basis='CFS')
    assert selected.reason=='structured_cash_flow_period_ambiguous'
    assert _bounds(year=2026,report_code='11012',statement_type='CF',amount_role='current',amount_variant='standalone')==(None,None,None)
    role,start,end=_bounds(year=2026,report_code='11012',statement_type='BS',amount_role='current',amount_variant='standalone')
    assert role=='point_in_time' and start==end


@pytest.mark.parametrize('identity',['US:NEW','KR:NEW','US:NEW_ADS'])
def test_unseen_identity_uses_same_owner_rules(monkeypatch,tmp_path,identity):
    args,payload=case(monkeypatch,tmp_path)
    args['security']['canonical_security_id']=identity
    result=reuse.replay_reported_context(**args)
    assert len(result['facts'])==2 and all(reuse.verify_reported_context(f,args['security']) for f in result['facts'])
    assert not any(f['fields']['valuation_denominator_eligible'] for f in result['facts'])


@pytest.mark.parametrize('axis',['driver','valuation','holder','overall'])
def test_unified_actual_validator_denies_context_as_decision_support(monkeypatch,tmp_path,axis):
    p,v,r=fixture();args,payload=case(monkeypatch,tmp_path,p['base']['public_security'])
    fact=reuse.replay_reported_context(**args)['facts'][0]
    row=deepcopy(p['base']['evidence'][0]);row.update(ref='cf-context',field='financial.operating_cashflow',data=fact)
    p['base']['evidence'].append(row)
    bundle=engine.build_bundle(p,registry=r)
    assert bundle['admissibility'][-1]['candidate_decision_axis']==[]
    assert 'reported_context_implementation' in bundle
    if axis=='driver':v['economic_drivers_positive'][0]['refs']=['cf-context']
    else:v[{'valuation':'valuation','holder':'holder_virtual','overall':'overall'}[axis]]['refs']=['cf-context']
    with pytest.raises(ValueError):engine.validate_and_render(v,bundle,registry=r,economic_loader=lambda:p)
