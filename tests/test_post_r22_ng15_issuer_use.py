"""Additional synthetic issuer-use boundaries, not real listing qualification.

All identities, ratios and receipts below are fictional test declarations.
No raw source, economic-transfer owner or native parent is issued here.
"""
from copy import deepcopy
from dataclasses import replace

import pytest

from app.services.issuer_business_bridge import bind_comparison, identity_bridge
from app.services.official_security_identity_service import OfficialSecurityIdentityEvidence
from app.services.unified_snapshot_contract import digest
from tests.test_issuer_business_bridge import comparison, fixture


def _declare_synthetic_identity(inputs, **changes):
    evidence = OfficialSecurityIdentityEvidence.from_payload(inputs['official'])
    inputs['official'] = replace(evidence, **changes).to_payload()
    inputs['expected_official_sha256'] = digest(inputs['official'])


def _assert_context_without_security_transfer(bridge):
    assert bridge['status'] == 'PASS'
    assert bridge['errors'] == []
    assert bridge['ISSUER_BUSINESS_EVIDENCE_ELIGIBLE'] is True
    assert bridge['scope'] == 'issuer_business_only'
    assert bridge['security_valuation_transfer'] is False
    assert bridge['SECURITY_PER_SHARE_BRIDGE_ELIGIBLE'] is False
    assert bridge['SECURITY_VALUATION_BRIDGE_ELIGIBLE'] is False


@pytest.mark.parametrize(('declared_ratio', 'direction'), [
    pytest.param(0.5, 'ordinary_shares_per_adr', id='matching-ratio'),
    pytest.param(2.0, 'ordinary_shares_per_adr', id='conflicting-ratio'),
    pytest.param(2.0, 'adrs_per_ordinary_share', id='reciprocal-direction'),
])
def test_ratio_declaration_is_not_a_security_use_owner(declared_ratio, direction):
    inputs = fixture()
    inputs['target']['adr_ratio'] = 0.5
    _declare_synthetic_identity(inputs, adr_ratio=declared_ratio,
                               adr_ratio_direction=direction)
    before = deepcopy(inputs)

    # Ratio qualification is not this context owner's responsibility or grant.
    bridge = identity_bridge(**inputs)
    _assert_context_without_security_transfer(bridge)
    original = comparison()
    bound = bind_comparison(deepcopy(original), original, bridge,
                            source_result_sha256=digest({'synthetic_source': original}))
    assert bound['issuer_business_bridge']['security_valuation_transfer'] is False
    assert bound['fields'] == original['fields']
    assert inputs == before


def test_listing_currency_cannot_convert_the_original_issuer_amounts():
    inputs = fixture()
    inputs['target'].update(currency='USD', adr_ratio=0.5)
    inputs['source']['currency'] = 'KRW'
    _declare_synthetic_identity(inputs, adr_ratio=0.5,
                               adr_ratio_direction='ordinary_shares_per_adr')
    bridge = identity_bridge(**inputs)
    _assert_context_without_security_transfer(bridge)
    original = comparison()
    original['fields'].update(current_value=120000, prior_comparable_value=100000,
                              delta=20000, growth_pct=20.0)
    before = deepcopy(original)

    bound = bind_comparison(deepcopy(original), original, bridge,
                            source_result_sha256=digest({'synthetic_source': original}))

    assert bound['fields'] == before['fields']
    assert bound['fields']['currency'] != inputs['target']['currency']
    assert bound['field_dependency_receipts'] == before['field_dependency_receipts']
    assert bound['issuer_business_bridge']['security_valuation_transfer'] is False
    assert original == before


def test_coherent_etf_identity_still_fails_the_instrument_boundary():
    inputs = fixture()
    inputs['target'].update(security_type='etf', issuer_type='fund')
    _declare_synthetic_identity(inputs, security_type='etf', issuer_type='fund',
                               security_title='Fictional Exchange Traded Fund')

    bridge = identity_bridge(**inputs)

    # Unlike a mismatched field, a coherent ETF must reach the type restriction.
    assert bridge['status'] == 'FAIL'
    assert bridge['errors'] == ['instrument_relationship_not_supported']
    assert bridge['ISSUER_BUSINESS_EVIDENCE_ELIGIBLE'] is False
    assert bridge['SECURITY_PER_SHARE_BRIDGE_ELIGIBLE'] is False
    assert bridge['SECURITY_VALUATION_BRIDGE_ELIGIBLE'] is False


def test_same_symbol_on_another_exchange_requires_its_own_identity():
    inputs = fixture()
    first = identity_bridge(**inputs)
    _assert_context_without_security_transfer(first)
    inputs['target'].update(exchange='NYSE', canonical_security_id='nyse-security')

    rejected = identity_bridge(**inputs)
    assert rejected['status'] == 'FAIL'
    assert rejected['errors'] == ['official_security_field_unverified:exchange']
    assert rejected['ISSUER_BUSINESS_EVIDENCE_ELIGIBLE'] is False

    _declare_synthetic_identity(inputs, exchange='NYSE')
    second = identity_bridge(**inputs)
    _assert_context_without_security_transfer(second)
    assert first['security_ticker'] == second['security_ticker']
    assert first['monitored_security_id'] != second['monitored_security_id']
    assert first['official_identity_sha256'] != second['official_identity_sha256']
    assert first['receipt_sha256'] != second['receipt_sha256']


def test_separately_valid_unrelated_listing_cannot_borrow_issuer_facts():
    inputs = fixture()
    first = identity_bridge(**inputs)
    _assert_context_without_security_transfer(first)
    original = comparison()
    source_sha = digest({'synthetic_source': original})
    accepted = bind_comparison(deepcopy(original), original, first,
                               source_result_sha256=source_sha)
    before = deepcopy(original)

    inputs['target'].update(ticker='OTHERADS', cik='0000000456',
                            canonical_company_id='other-sec-company',
                            canonical_security_id='other-nasdaq-security')
    inputs['source'].update(ticker='654321', corp_code='00999999',
                            canonical_company_id='other-dart-company',
                            canonical_security_id='other-krx-security')
    inputs['dart_rows'] = [{'stock_code': '654321', 'corp_code': '00999999'}]
    inputs['dart_receipt'].update(raw_sha256='c' * 64, request_sha256='d' * 64,
                                 logical_id='other-synthetic-list')
    # This is a fictional SEC-shaped fixture URL, never fetched or a public pin.
    _declare_synthetic_identity(inputs, ticker='OTHERADS', cik='0000000456',
        ordinary_share_identifier='654321', filing_accession='0000000456-26-000001',
        source_url='https://www.sec.gov/Archives/edgar/data/456/000000045626000001/prospectus.htm',
        source_reference='Unrelated synthetic SEC registration fixture')
    second = identity_bridge(**inputs)
    _assert_context_without_security_transfer(second)
    assert first['issuer_id'] != second['issuer_id']
    assert first['legal_issuer_id'] != second['legal_issuer_id']
    assert inputs['official']['evidence']['issuer_name'] == fixture()['official']['evidence']['issuer_name']

    with pytest.raises(ValueError, match='^issuer_business_original_fact_mismatch$'):
        bind_comparison(deepcopy(original), original, second, source_result_sha256=source_sha)

    assert accepted['issuer_business_bridge']['original_fact_sha256'] == digest(before)
    assert original == before
