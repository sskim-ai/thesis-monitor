"""Generic source-replayed period lineage; no live source or economic grant."""
from copy import deepcopy
from datetime import date
from hashlib import sha256
import json

import pytest

from app.services import sec_foreign_comparison_service as owner
from app.services.sec_reported_quarter_period import POLICY, METHOD, source_record


def document(*, year=2026, name='Unseen Issuer', extra='', end='September 30', basis='consolidated'):
    return (f'<html><body><p>{name} reported consolidated revenue for the third quarter ended {end}, {year}.</p>'
        f'{extra}<section><p>{name}\'s {year} third quarter {basis} results:</p>'
        '<p>Unit: NT$ million</p><table><tr><th>Metric</th>'
        f'<th>3Q{year%100:02d} Amount a</th><th>3Q{(year-1)%100:02d} Amount</th><th>2Q{year%100:02d} Amount</th></tr>'
        '<tr><td>Net sales</td><td>1200</td><td>1000</td><td>1100</td></tr>'
        '<tr><td>Income from operations</td><td>200</td><td>100</td><td>150</td></tr>'
        '</table><p>a: Figures have not been approved by Board of Directors</p></section></body></html>').encode()


def parse(raw, *, cik='9876543', accession='0009876543-26-000001', policy=POLICY):
    identity=dict(issuer_cik=cik,accession=accession,document_type='6-K',filing_date='2026-10-15',
        source_url=f'https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession.replace("-", "")}/release.htm')
    found=owner.extract_occurrences(raw.decode(),payload_sha256=sha256(raw).hexdigest(),
        quarter_period_policy=policy,**identity)
    return found,source_record(raw,**identity)


@pytest.mark.parametrize('name,cik', [('Unseen US ordinary','1234000'),('Unseen international ADS','5678000'),
    ('Unseen KR legal issuer','9988776'),('Financial issuer','9871234'),('Cyclical issuer','9991234')])
def test_equivalent_properties_not_ticker_rules(name,cik):
    values,sources=parse(document(name=name),cik=cik)
    assert len(values)==6
    assert all(not owner.occurrence_errors(o,date(2026,10,22),source_documents=sources) for o in values)
    current=owner.current_projection(values,source_documents=sources)
    assert current['period_end']=='2026-09-30'
    assert {o['period_start'] for o in values}=={'2026-07-01','2025-07-01','2026-04-01'}
    assert all(o['period_resolution_method']==METHOD for o in values)
    assert all(o['period_source_proof']['derivation']=='CALENDAR_RESULT_NOT_EXPLICIT_REPORTED_START' for o in values)


@pytest.mark.parametrize('mutation', ['bare','metadata','other_table','other_exhibit','forward','footnote',
    'noncalendar','wrongday','wrongyear','ytd','prior_wrong','monthly','annual','separate','wrong_units','no_yoy'])
def test_missing_or_incompatible_source_premise_denied(mutation):
    raw=document().decode()
    if mutation in {'bare','metadata'}:
        raw=raw.replace('reported consolidated revenue for the third quarter ended September 30, 2026.',
            '3Q26 fiscalYearEnd 1231 SEC reportDate 2026-09-30.' if mutation=='metadata' else 'reported revenue.')
    elif mutation=='other_table':raw=raw.replace('<p>Unseen Issuer reported','<table><tr><td>Unseen Issuer reported').replace('2026.</p>','2026.</td></tr></table>')
    elif mutation=='other_exhibit':raw=raw.replace('third quarter ended September 30, 2026','second quarter ended June 30, 2026')
    elif mutation=='forward':raw=raw.replace('reported consolidated revenue','projected guidance revenue')
    elif mutation=='footnote':raw=raw.replace('<p>Unseen Issuer reported','<footer><p>Unseen Issuer reported').replace('2026.</p>','2026.</p></footer>')
    elif mutation=='noncalendar':raw=raw.replace('<section>','<p>The fiscal year ends June 30.</p><section>')
    elif mutation=='wrongday':raw=raw.replace('September 30','September 29')
    elif mutation=='wrongyear':raw=raw.replace('September 30, 2026','September 30, 2025')
    elif mutation=='ytd':raw=raw.replace('third quarter consolidated results:', 'third quarter nine months YTD consolidated results:')
    elif mutation=='prior_wrong':raw=raw.replace('3Q25 Amount','3Q24 Amount')
    elif mutation=='monthly':raw=raw.replace('third quarter','monthly revenue')
    elif mutation=='annual':raw=raw.replace('third quarter','annual')
    elif mutation=='separate':raw=raw.replace('third quarter consolidated results:', 'third quarter separate statements of income')
    elif mutation=='wrong_units':raw=raw.replace('NT$ million','NT$ million and Unit: US$ billion')
    else:raw=raw.replace('3Q25 Amount','2Q26 Amount')
    values,sources=parse(raw.encode())
    assert not any(not owner.occurrence_errors(o,date(2026,10,22),source_documents=sources) for o in values)


@pytest.mark.parametrize('field,value', [('issuer_cik','0000000001'),('accession','0009876543-26-000002'),
    ('source_url','https://www.sec.gov/Archives/edgar/data/9876543/000987654326000001/other.htm'),
    ('document_type','20-F'),('period_start','2026-01-01'),('period_end','2026-09-29'),
    ('duration_days',273),('currency','USD'),('unit_scale',1000),('statement_basis','separate'),
    ('field','operating_income'),('value',12),('source_payload_sha256','0'*64),
    ('period_resolution_method','explicit_date_range')])
def test_rehashed_occurrence_cannot_self_issue_period(field,value):
    values,sources=parse(document());o=deepcopy(values[0]);o[field]=value
    o['occurrence_id']=owner.sha({k:v for k,v in o.items() if k!='occurrence_id'})
    assert owner.occurrence_errors(o,date(2026,10,22),source_documents=sources)
    assert owner.current_projection([o],source_documents=sources) is None


def test_raw_and_proof_tampering_and_absence():
    values,sources=parse(document());o=values[0]
    assert 'source_bound_quarter_raw_replay_required' in owner.occurrence_errors(o,date(2026,10,22))
    for mutation in ('raw','proof','header','row'):
        bad,docs=deepcopy(o),deepcopy(sources)
        if mutation=='raw':docs[o['source_payload_sha256']]['raw_utf8']+='different'
        elif mutation=='proof':bad['period_source_proof']['reported_end']='2026-06-30'
        elif mutation=='header':bad['source_cell']['headers'][0]['text']='3Q25 Amount'
        else:bad['source_cell']['row_label']='Income from operations'
        bad['source_row_identity']=owner.sha(dict(payload=bad['source_payload_sha256'],cell=bad['source_cell']))
        bad['occurrence_id']=owner.sha({k:v for k,v in bad.items() if k!='occurrence_id'})
        assert 'source_bound_quarter_raw_replay_required' in owner.occurrence_errors(bad,date(2026,10,22),source_documents=docs)


def test_legacy_explicit_period_and_bare_q_receipts_unchanged():
    raw=document().replace(b'3Q26 Amount a',b'2026-07-01 to 2026-09-30').replace(
        b'3Q25 Amount',b'2025-07-01 to 2025-09-30').replace(b'2Q26 Amount',b'2026-04-01 to 2026-06-30')
    legacy,_=parse(raw,policy=None);opted,_=parse(raw)
    assert legacy==opted and all(not owner.occurrence_errors(o,date(2026,10,22)) for o in legacy)
    assert owner.period_from_headers(['3Q26','1231','2026-09-30'])['period_start'] is None
    values,_=parse(document(),policy=None)
    assert all(o['period_start'] is None for o in values)


def test_roundtrip_preserves_source_bound_receipts_and_rejects_qoq_as_yoy():
    values,sources=parse(document())
    values,sources=json.loads(json.dumps([values,sources]))
    assert all(not owner.occurrence_errors(o,date(2026,10,22),source_documents=sources) for o in values)
    current=next(o for o in values if o['field']=='revenue' and o['period_end']=='2026-09-30')
    qoq=[o for o in values if o['period_end']=='2026-06-30']
    assert owner.authoritative_prior(current,qoq,date(2026,10,22))['status']=='FAIL'


@pytest.mark.parametrize('value', ['1,200x','1,200%','NaN'])
def test_malformed_amount_cannot_be_owned(value):
    found,sources=parse(document().replace(b'<td>1200</td>',f'<td>{value}</td>'.encode()))
    assert not any(o['field']=='revenue' and o['period_end']=='2026-09-30' for o in found)


@pytest.mark.parametrize('calendar_text', ['The fiscal year ends December 31.',
    'The fiscal year ended December 31.', 'The fiscal year ending December 31.'])
def test_unseen_explicit_calendar_year_remains_source_bound(calendar_text):
    values,sources=parse(document(name='Heldout FPI',extra=f'<p>{calendar_text}</p>'))
    assert len(values)==6
    assert all(not owner.occurrence_errors(o,date(2026,10,22),source_documents=sources) for o in values)


@pytest.mark.parametrize('calendar_text', ['The fiscal year ends March 31.',
    'The fiscal year ended January 31.', 'We use a 52-week fiscal reporting calendar.',
    'The 4-4-5 accounting calendar applies.'])
def test_unseen_non_calendar_or_week_based_fpi_is_not_inferred(calendar_text):
    values,sources=parse(document(name='Heldout other FPI',extra=f'<p>{calendar_text}</p>'))
    assert all(owner.occurrence_errors(o,date(2026,10,22),source_documents=sources) for o in values)


def test_receipt_is_not_a_quality_or_review_approval():
    values,sources=parse(document())
    assert all(not owner.occurrence_errors(o,date(2026,10,22),source_documents=sources) for o in values)
    assert all(o.get('document_evidence_class', {}).get('reviewed_financial_statement') is not True for o in values)
    assert all('Board of Directors' not in o['period_source_proof']['premise_text'] for o in values)
