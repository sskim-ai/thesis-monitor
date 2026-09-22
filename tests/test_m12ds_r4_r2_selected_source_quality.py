from copy import deepcopy
from datetime import date
import json

import pytest

from scripts.m12ds_r4_r2_selected_source_quality import (
    apply_selected_gate, assert_selection, comparison_bundle, select_source,
)
from scripts.m12dr_financial_source_authority import source_quality
from app.services.sec_financial_snapshot_service import _companyfacts_snapshots
from tests.test_external_api_accuracy import _companyfact_entry, _companyfacts_payload

CUTOFF = date(2026, 9, 22)


def fixture(ticker='RENAMED'):
    current = dict(_companyfact_entry(30, fp='Q2', start='2026-04-01', end='2026-06-30',
                                     filed='2026-08-01'), accn='0000001234-26-000123', form='10-Q')
    prior = dict(current, start='2025-04-01', end='2025-06-30', val=-20)
    payload = _companyfacts_payload('us-gaap', {
        'Revenues': [dict(r, val=100) for r in (current, prior)],
        'RevenueFromContractWithCustomerExcludingAssessedTax': [dict(r, val=10) for r in (current, prior)],
        'OperatingIncomeLoss': [current, prior]})
    payload['cik'] = 1234
    return sorted(_companyfacts_snapshots(payload, ticker), key=lambda r: r.financial_period_end)


def packet(row):
    source = dict(provider=row.provider, period=str(row.financial_period_end),
        filing_date=str(row.filing_date), fiscal_year=row.fiscal_year,
        period_scope=row.period_scope, period_type=row.period_type,
        is_cumulative=row.is_cumulative, source_type=row.snapshot_type)
    return dict(ticker=row.ticker, fact_catalog=[dict(fact_id='earnings:current', fact_type='earnings',
        financial_quality=dict(source_snapshot=source),
        fields={m: dict(value=getattr(row, m), currency=row.currency)
                for m in ('revenue', 'operating_income') if getattr(row, m) is not None})])


def binding(row):
    return dict(ticker=row.ticker, status='PASS', issuer_id='CIK:0000001234')


def select(row, rows, stock=None, issuer=None):
    return select_source(stock=stock or packet(row), rows=rows, binding=issuer or binding(row), cutoff=CUTOFF)


def compare(current, rows, audit):
    return comparison_bundle(selected=current, rows=rows, audit=audit, binding=binding(current),
        cutoff=CUTOFF, generation='renamed-synthetic-generation', database_sha256='f' * 64)


def foreign(row):
    row = row.model_copy(deep=True)
    row.provider = 'sec_foreign_filing'
    row.source_filing_id = '0000001234-26-000123'
    row.source = 'https://www.sec.gov/Archives/edgar/data/1234/000000123426000123/ex99.htm'
    row.financial_hard_errors = '[]'
    row.currency = 'TWD'
    row.revenue = 100.0
    row.raw_financial_fields = json.dumps([dict(field='revenue', value=100, currency='TWD',
        source='sec_foreign_filing', parse_method='sec_foreign_release')])
    return row


@pytest.mark.parametrize('name', ['ALPHA', 'RENAMED', 'ZZZZ'])
def test_clean_selected_provider_survives_unrelated_old_conflict(name):
    prior, old = fixture(name)
    current = foreign(old)
    old.financial_period_end = date(2024, 12, 31)
    selected, audit = select(current, [old, prior, current])
    assert selected is current and not audit['selection_errors']
    assert audit['selected_field_usability']['revenue']['source_quality_usable']
    assert audit['alternate_sources'][0]['hard_errors'] == ['sec_business_occurrence_conflict']
    assert audit['alternate_sources'][0]['provider'] == 'sec_companyfacts'
    bundle, quality = compare(selected, [old, prior, current], audit)
    assert bundle is quality is None
    assert all(r['errors'] for r in audit['comparative_attempts'])
    assert any('cross_provider_reconciliation_owner_missing' in r['errors'] for r in audit['comparative_attempts'])


def test_selected_foreign_conflict_remains_owned_by_selected_source():
    _, row = fixture()
    row = foreign(row)
    row.financial_hard_errors = '["provider_occurrence_conflict"]'
    _, audit = select(row, [row])
    assert not audit['selected_field_usability']['revenue']['source_quality_usable']
    assert audit['selected']['hard_errors'] == ['provider_occurrence_conflict']


def test_old_same_provider_period_conflict_does_not_taint_clean_field():
    prior, current = fixture()
    selected, audit = select(current, [prior, current])
    assert selected is current
    assert not audit['selected_field_usability']['revenue']['source_quality_usable']
    assert audit['selected_field_usability']['operating_income']['source_quality_usable']
    bundle, quality = compare(current, [prior, current], audit)
    assert quality['status'] == 'PASS'
    assert source_quality(bundle) == quality
    assert [r['metric'] for r in quality['comparative_observations']] == ['operating_income']


@pytest.mark.parametrize('change', ['currency', 'provider', 'duration', 'scope', 'basis', 'issuer', 'receipt', 'future'])
def test_comparison_mismatch_fails_without_reconciliation(change):
    prior, current = fixture()
    _, audit = select(current, [prior, current])
    if change == 'currency':
        prior.currency = 'TWD'
    elif change == 'provider':
        prior.provider = 'sec_foreign_filing'
    elif change == 'scope':
        prior.period_scope = 'annual'
    elif change == 'basis':
        prior.fs_div = 'OFS'
    elif change == 'receipt':
        prior.source_filing_id = 'another-document'
    elif change == 'future':
        prior.filing_date = date(2027, 1, 1)
    else:
        raw = json.loads(prior.raw_financial_fields)
        witness = next(r for r in raw if r.get('field') == 'operating_income')
        witness['issuer_cik' if change == 'issuer' else 'period_start'] = '9999' if change == 'issuer' else '2025-01-01'
        prior.raw_financial_fields = json.dumps(raw)
    bundle, quality = compare(current, [prior, current], audit)
    assert bundle is quality is None


@pytest.mark.parametrize('change', ['ticker', 'provider', 'document', 'period', 'currency', 'row', 'basis'])
def test_frozen_selected_source_switch_fails_closed(change):
    prior, current = fixture()
    _, audit = select(current, [prior, current])
    if change == 'period':
        current.financial_period_end = date(2026, 3, 31)
    elif change == 'document':
        current.source_filing_id = 'another'
    elif change == 'row':
        current.raw_financial_fields = '[]'
    elif change == 'basis':
        current.fs_div = 'CFS'
    else:
        setattr(current, change, 'mismatch')
    with pytest.raises(ValueError, match='selected_source_identity_drift'):
        assert_selection(current, audit)


def test_same_projection_multiple_documents_is_not_disambiguated_by_value():
    _, current = fixture()
    duplicate = current.model_copy(deep=True)
    duplicate.source_filing_id = 'another'
    selected, audit = select(current, [duplicate, current])
    assert selected is None
    assert audit['selection_errors'] == ['selected_source_projection_missing_or_ambiguous']


def test_packet_document_claim_and_issuer_mismatch_fail_closed():
    _, current = fixture()
    stock = packet(current)
    stock['fact_catalog'][0]['field_quality'] = {'field': {'source_filing_identifier': 'wrong'}}
    assert select(current, [current], stock=stock)[0] is None
    assert select(current, [current], issuer={**binding(current), 'issuer_id': 'CIK:0000009999'})[0] is None
    f = foreign(current)
    f.source_filing_id = 'wrong'
    assert select(f, [f])[0] is None


def test_absolute_selected_foreign_row_does_not_grant_direction():
    _, row = fixture()
    row = foreign(row)
    _, audit = select(row, [row])
    gate = dict(status='DIRECTIONAL_BUSINESS_SOURCE_READY', directional_source_refs=['canonical:earnings:current'])
    apply_selected_gate(gate, audit, [])
    assert gate['status'] == 'SOURCE_COMPARISON_UNAVAILABLE'
    assert gate['directional_source_refs'] == []
    assert not gate['ready_for_authority_aware_core_preflight']


def test_ref_local_denial_does_not_clear_independent_source():
    _, current = fixture()
    _, audit = select(current, [current])
    gate = dict(status='DIRECTIONAL_BUSINESS_SOURCE_READY', directional_source_refs=[
        'canonical:earnings:current', 'canonical:other-owned-observation'])
    apply_selected_gate(gate, audit, ['canonical:comparison'])
    assert gate['directional_source_refs'] == ['canonical:comparison', 'canonical:other-owned-observation']


def test_bundle_recomputes_selected_identity():
    prior, current = fixture()
    _, audit = select(current, [prior, current])
    bundle, _ = compare(current, [prior, current], audit)
    bad = deepcopy(bundle)
    bad['selected_source_identity']['document'] = 'changed'
    with pytest.raises(ValueError, match='selected_source_identity_mismatch'):
        source_quality(bad)


def test_absent_unrelated_field_does_not_invent_taint_on_existing_accepted_source():
    entry = dict(_companyfact_entry(100, fp='FY', start='2025-01-01', end='2025-12-31',
                                   filed='2026-03-01'), accn='0000001234-26-000123', form='10-K')
    payload = _companyfacts_payload('us-gaap', {'Revenues': [entry]})
    payload['cik'] = 1234
    row = _companyfacts_snapshots(payload, 'RENAMED')[0]
    _, audit = select(row, [row])
    assert not audit['selection_errors']
    assert audit['selected_field_usability']['revenue']['source_quality_usable']
    assert not audit['selected_field_usability']['operating_income']['amount_present']
    gate = dict(status='DIRECTIONAL_BUSINESS_SOURCE_READY', directional_source_refs=['canonical:earnings:current'])
    apply_selected_gate(gate, audit, [])
    assert gate['directional_source_refs'] == ['canonical:earnings:current']
