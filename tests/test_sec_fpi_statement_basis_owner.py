from copy import deepcopy

import pytest

from app.services.sec_fpi_statement_basis_owner import POLICY,select_basis,verify_basis
from app.services.unified_snapshot_contract import digest
from test_sec_foreign_statement_scope import statement,source


def inputs(ticker='UNSEEN_ADS',issuer='1234'):
    meta=source(issuer)
    security=dict(cik=issuer,canonical_company_id='issuer:'+issuer,canonical_security_id='security:'+ticker)
    plan=dict(security=security,provider='sec_edgar',financial_owner_policy='EXACT_FISCAL_ANNUAL_AND_CURRENT_FPI_V1',
        issuer=issuer,ticker=ticker,identity_sha256=digest(security),run_id='source-fixture',cutoff='2026-10-21T00:00:00+00:00')
    return dict(plan=plan,filing=meta['filing'],source_url=meta['source_url'],policy=POLICY,execution_generation='policy-fixture')


@pytest.mark.parametrize('ticker,issuer',[('UNSEEN_ADS','1234'),('MU','1235'),('TSM','1236'),('005930','1237'),('000660','1238')])
def test_generic_consolidated_selected_without_economic_grant(ticker,issuer):
    raw=(statement('Separate','999','888')+statement('Consolidated')).encode();kw=inputs(ticker,issuer)
    receipt=select_basis(raw,**kw)
    assert verify_basis(receipt,raw,**kw)==receipt
    assert receipt['status']=='PASS' and receipt['selected_basis']=='consolidated'
    assert len(receipt['selected_occurrence_ids'])==2
    assert not receipt['source_use_eligible'] and not receipt['direction_eligible']
    assert receipt['rejected_alternate_scopes'][0]['statement_basis']=='separate'
    assert receipt['source_generation']!=receipt['execution_generation']


@pytest.mark.parametrize('raw',[
    statement('Separate'),
    statement('Consolidated',prior='unavailable')+statement('Separate'),
    statement('Consolidated',extra='<tr><td>Revenue</td><td>151</td><td>100</td></tr>')+statement('Separate'),
    statement('Consolidated')+statement('Consolidated','151'),
    statement('Consolidated')+statement('Consolidated'),
    statement('Consolidated',prior_header='2025-01-01 to 2025-06-30'),
    statement('Consolidated').replace('US dollars','unknown currency'),
    statement('Consolidated').replace('Consolidated Statements','Unclassified Statements'),
])
def test_ambiguous_or_unqualified_never_falls_back(raw):
    r=select_basis(raw.encode(),**inputs())
    assert r['status']=='BLOCKED' and not r['selected_occurrence_ids']
    assert r['selected_basis'] is None and not r['separate_fallback']


@pytest.mark.parametrize('field',['policy','generation','issuer','raw','value','grant','scope','receipt'])
def test_rehashed_receipt_or_wrong_input_fails(field):
    raw=(statement('Consolidated')+statement('Separate')).encode();kw=inputs()
    r=select_basis(raw,**kw);bad=deepcopy(r)
    if field=='policy':bad['policy']['version']=2
    elif field=='generation':bad['execution_generation']='other'
    elif field=='issuer':bad['issuer_cik']='0000005678'
    elif field=='raw':raw=raw.replace(b'150',b'151')
    elif field=='value':bad['original_scope_audit']['partitions'][0]['occurrences'][0]['value']=1
    elif field=='grant':bad['source_use_eligible']=True
    elif field=='scope':bad['selected_basis']='separate'
    else:bad['receipt_sha256']='f'*64
    if field!='receipt':bad['receipt_sha256']=digest({k:v for k,v in bad.items() if k!='receipt_sha256'})
    with pytest.raises(ValueError,match='source_replay_mismatch'):verify_basis(bad,raw,**kw)


@pytest.mark.parametrize('field',['policy','execution_generation','identity'])
def test_explicit_authorization_required(field):
    kw=inputs()
    if field=='identity':kw['plan']['security']['cik']='9999'
    else:kw[field]=None
    with pytest.raises(ValueError):select_basis(statement('Consolidated').encode(),**kw)


def test_unknown_original_owner_policy_not_authority():
    kw=inputs();kw['plan']['financial_owner_policy']='caller-approved'
    with pytest.raises(ValueError):select_basis(statement('Consolidated').encode(),**kw)


def test_separate_currency_and_value_do_not_contaminate_qualified_consolidated():
    raw=(statement('Consolidated')+statement('Separate','150','100').replace('US dollars','Korean won')).encode()
    r=select_basis(raw,**inputs())
    assert r['status']=='PASS' and len(r['selected_occurrence_ids'])==2
    assert len(r['original_scope_audit']['partitions'])==2


def test_bad_operating_field_does_not_invalidate_independent_revenue():
    raw=statement('Consolidated',extra='<tr><td>Operating income</td><td>30</td><td>20</td></tr>'
        '<tr><td>Operating income</td><td>31</td><td>20</td></tr>').encode()
    r=select_basis(raw,**inputs())
    decisions={x['field']:x for x in r['field_decisions'] if x['period_role']=='single-quarter'}
    assert decisions['revenue']['status']=='PASS' and decisions['operating_income']['status']=='BLOCKED'
    assert len(r['selected_occurrence_ids'])==2


def test_conflicting_quarter_cannot_fall_back_to_same_endpoint_half_year():
    quarter=statement('Consolidated',extra='<tr><td>Revenue</td><td>151</td><td>100</td></tr>')
    half=statement('Consolidated').replace('04-01','01-01')
    r=select_basis((quarter+half).encode(),**inputs())
    assert r['status']=='BLOCKED'
    assert 'UNRESOLVED_REPORTED_QUARTER_NO_HALF_YEAR_SUBSTITUTION' in r['field_decisions'][2]['denial_reasons']
    only=select_basis(half.encode(),**inputs())
    assert only['status']=='PASS' and len(only['selected_occurrence_ids'])==2


@pytest.mark.parametrize('defect',['currency','units','caption','period'])
def test_competing_unparseable_statement_still_blocks(defect):
    bad=statement('Consolidated','151')
    if defect=='currency':bad=bad.replace('US dollars','unresolved currency')
    elif defect=='units':bad=bad.replace('In millions of US dollars','In unknown units of US dollars')
    elif defect=='caption':bad=bad.replace('Consolidated Statements of Income','Consolidated and Separate Statements of Income')
    else:bad=bad.replace('2026-04-01 to 2026-06-30','Q2 2026').replace('2025-04-01 to 2025-06-30','Q2 2025')
    r=select_basis((statement('Consolidated')+bad).encode(),**inputs())
    assert r['status']=='BLOCKED' and r['unresolved_consolidated_cells']


def test_receipt_policy_does_not_alias_authoritative_rule():
    raw=statement('Consolidated').encode();before=select_basis(raw,**inputs())
    before['policy']['periods'].clear();before['policy']['fields'].clear()
    after=select_basis(raw,**inputs())
    assert after['status']=='PASS' and after['policy']['fields']==['revenue','operating_income']
