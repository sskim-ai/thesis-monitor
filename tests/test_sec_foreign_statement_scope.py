from copy import deepcopy
from datetime import date
import json

import pytest

from app.models.financial import FinancialSnapshot
from app.services.sec_foreign_statement_scope import inspect_scopes, verify_scope_audit
from app.services.sec_foreign_comparison_service import foreign_comparison_quality, current_projection, period_from_headers
from app.services.unified_snapshot_contract import digest


def statement(basis, current='150', prior='100', extra='', prior_header='2025-04-01 to 2025-06-30'):
    return f'''<h2>{basis} Statements of Income</h2><p>In millions of US dollars</p>
    <table><tr><td></td><td>2026-04-01 to 2026-06-30</td><td>{prior_header}</td></tr>
    <tr><td>Revenue</td><td>{current}</td><td>{prior}</td></tr>{extra}</table>'''


def source(issuer='1234'):
    accession=f'{int(issuer):010d}-26-000010'
    return dict(issuer_cik=issuer, filing=dict(accessionNumber=accession,form='6-K',
        filingDate='2026-08-18', reportDate='2026-08-18',primaryDocument='main.htm'),
        source_url=f'https://www.sec.gov/Archives/edgar/data/{int(issuer)}/{accession.replace("-", "")}/main.htm',
        cutoff='2026-10-21')


def quality_of(items):
    p=current_projection(items)
    row=FinancialSnapshot(ticker='UNSEEN',period='2026-Q2',provider='sec_foreign_filing',
        snapshot_type='preliminary_earnings',period_scope='single-quarter',period_type='Q2',
        financial_period_end=date(2026,6,30),filing_date=date(2026,8,18),
        source_filing_id=source()['filing']['accessionNumber'],source=source()['source_url'],
        currency='USD',revenue=p['revenue'],
        raw_financial_fields=json.dumps([dict(field='foreign_business_occurrences',occurrences=items)]))
    return foreign_comparison_quality(formal=row,candidates=[],ticker='UNSEEN',cutoff=date(2026,10,21))


@pytest.mark.parametrize('issuer,ticker', [('1234','UNSEEN_US'),('5678','UNSEEN_KR'),('9876','UNSEEN_ADS'),('8765','TSM'),('7654','MU'),('6543','000660')])
def test_generic_partition_no_selection_or_permission(issuer,ticker):
    raw=(statement('Separate','999','888')+statement('Consolidated')).encode()
    audit=inspect_scopes(raw,**source(issuer))
    assert verify_scope_audit(audit,raw,**source(issuer))==audit
    assert audit['selected_basis'] is None and not audit['source_use_eligible']
    assert not audit['direction_eligible'] and not audit['valuation_eligible']
    assert [p['statement_basis'] for p in audit['partitions']]==['consolidated','separate']
    for part in audit['partitions']:
        projection=part['diagnostic_projections']['single-quarter']
        row=FinancialSnapshot(ticker=ticker,period='2026-Q2',provider='sec_foreign_filing',
            snapshot_type='preliminary_earnings',period_scope='single-quarter',period_type='Q2',
            financial_period_end=date(2026,6,30),filing_date=date(2026,8,18),
            source_filing_id=source(issuer)['filing']['accessionNumber'],source=source(issuer)['source_url'],
            currency='USD',revenue=projection['revenue'],
            raw_financial_fields=json.dumps([dict(field='foreign_business_occurrences',occurrences=part['occurrences'])]))
        quality=foreign_comparison_quality(formal=row,candidates=[],ticker=ticker,cutoff=date(2026,10,21))
        assert quality['fields']['revenue']['status']=='PASS'
    assert audit['status']=='FOREIGN_STATEMENT_BASIS_POLICY_AUTHORITY_PENDING'


@pytest.mark.parametrize('basis', ['Separate','Consolidated'])
def test_single_scope_still_has_no_authority(basis):
    audit=inspect_scopes(statement(basis).encode(),**source())
    assert len(audit['partitions'])==1 and audit['selected_basis'] is None


def test_conflicting_consolidated_does_not_fall_back():
    raw=(statement('Consolidated',extra='<tr><td>Revenue</td><td>151</td><td>100</td></tr>')+statement('Separate')).encode()
    audit=inspect_scopes(raw,**source())
    assert audit['partitions'][0]['diagnostic_projections']['single-quarter'] is None
    assert audit['partitions'][1]['diagnostic_projections']['single-quarter']
    assert audit['selected_basis'] is None


def test_cross_basis_prior_not_paired():
    raw=(statement('Consolidated',prior='unavailable')+statement('Separate',current='unavailable')).encode()
    audit=inspect_scopes(raw,**source())
    assert all(len(p['valid_occurrence_ids'])==1 for p in audit['partitions'])
    items=[o for p in audit['partitions'] for o in p['occurrences']]
    assert {(o['statement_basis'],o['period_end']) for o in items}=={('consolidated','2026-06-30'),('separate','2025-06-30')}
    q=quality_of(items)
    assert q['status']=='FAIL' and not q['comparative_observations']
    assert 'comparison_statement_basis_mismatch' in q['fields']['revenue']['denial_reasons']
    assert audit['selected_basis'] is None


@pytest.mark.parametrize('prior', ['Q2 2025','2025-01-01 to 2025-06-30','2025-04-02 to 2025-06-30'])
def test_exact_periods_retained_no_repair_by_label(prior):
    audit=inspect_scopes(statement('Consolidated',prior_header=prior).encode(),**source())
    assert not audit['source_use_eligible']
    assert len(audit['partitions'][0]['occurrences'])==2
    items=audit['partitions'][0]['occurrences']
    original=period_from_headers([prior])
    assert all(items[1][k]==v for k,v in original.items())
    q=quality_of(items)
    assert q['status']=='FAIL' and not q['comparative_observations']


@pytest.mark.parametrize('mutation', ['basis','value','scale','period','caption','issuer','filing','raw_sha','cutoff','grant','selected','drop_scope','drop_occurrence'])
def test_caller_rehashed_receipt_denied(mutation):
    raw=(statement('Consolidated')+statement('Separate')).encode()
    audit=inspect_scopes(raw,**source()); altered=deepcopy(audit)
    o=altered['partitions'][0]['occurrences'][0]
    if mutation=='basis':o['statement_basis']='separate'
    elif mutation=='value':o['value']=1
    elif mutation=='scale':o['unit_scale']=1
    elif mutation=='period':o['period_start']='2026-01-01'
    elif mutation=='caption':o['statement_boundary']['caption']='Separate Statements of Income'
    elif mutation=='issuer':altered['issuer_cik']='0000005678'
    elif mutation=='filing':altered['filing']['accessionNumber']='0000001234-26-000011'
    elif mutation=='raw_sha':altered['document_sha256']='f'*64
    elif mutation=='cutoff':altered['cutoff']='2026-10-22'
    elif mutation=='grant':altered['source_use_eligible']=True
    elif mutation=='selected':altered['selected_basis']='consolidated'
    elif mutation=='drop_scope':altered['partitions'].pop()
    elif mutation=='drop_occurrence':altered['partitions'][0]['occurrences'].pop()
    altered['receipt_sha256']=digest({k:v for k,v in altered.items() if k!='receipt_sha256'})
    with pytest.raises(ValueError,match='source_replay_mismatch'):
        verify_scope_audit(altered,raw,**source())


@pytest.mark.parametrize('mutation', ['raw','issuer','url','accession','amendment','date'])
def test_original_document_binding_recomputed(mutation):
    raw=statement('Consolidated').encode(); meta=source()
    audit=inspect_scopes(raw,**meta)
    if mutation=='raw':raw=raw.replace(b'150',b'151')
    elif mutation=='issuer':meta['issuer_cik']='5678'
    elif mutation=='url':meta['source_url']=meta['source_url'].replace('main.htm','other.htm')
    elif mutation=='accession':meta['filing']['accessionNumber']='0000001234-26-000011'
    elif mutation=='amendment':meta['filing']['form']='6-K/A'
    elif mutation=='date':meta['filing']['filingDate']='2026-08-19'
    with pytest.raises(ValueError,match='source_replay_mismatch'):
        verify_scope_audit(audit,raw,**meta)
