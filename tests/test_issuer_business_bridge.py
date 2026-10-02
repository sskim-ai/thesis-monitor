from copy import deepcopy
import pytest

from app.services.issuer_business_bridge import identity_bridge, evidence_scope, bind_comparison
from app.services.official_security_identity_service import OfficialSecurityIdentityEvidence
from app.services.unified_snapshot_contract import digest


def fixture():
    target = {'ticker': 'FICADR', 'cik': '0000000123', 'corp_code': None,
        'canonical_company_id': 'sec-company', 'canonical_security_id': 'nasdaq-security',
        'security_type': 'ads', 'issuer_type': 'adr', 'exchange': 'NASDAQ',
        'ordinary_share_identifier': None, 'adr_ratio': None}
    source = {'ticker': '123456', 'corp_code': '00123456', 'cik': None,
        'canonical_company_id': 'dart-company', 'canonical_security_id': 'krx-security',
        'security_type': 'common_stock', 'exchange': 'KRX'}
    official = OfficialSecurityIdentityEvidence(
        ticker='FICADR', issuer_name='Fictional Issuer', security_title='American Depositary Shares',
        security_type='ads', issuer_type='adr', exchange='NASDAQ',
        source_url='https://www.sec.gov/Archives/edgar/data/123/000000012326000001/prospectus.htm',
        source_form='424(b)(4)', filing_accession='0000000123-26-000001',
        as_of_date='2026-06-01', source_reference='SEC registration fixture',
        cik='0000000123', ordinary_share_identifier='123456').to_payload()
    return {'target': target, 'source': source, 'official': official,
        'expected_official_sha256': digest(official), 'cutoff': '2026-09-27T00:00:00+00:00',
        'dart_rows': [{'stock_code': '123456', 'corp_code': '00123456'}],
        'dart_receipt': {'stage': 'discovery', 'HTTP_status': 200, 'provider_status': '000',
            'raw_sha256': 'a' * 64, 'request_sha256': 'b' * 64, 'logical_id': 'captured-list'}}


def test_proven_issuer_without_share_ratio():
    args = fixture()
    before = deepcopy(args)
    result = identity_bridge(**args)
    assert result['status'] == 'PASS'
    assert result['ISSUER_BUSINESS_EVIDENCE_ELIGIBLE']
    assert not result['SECURITY_PER_SHARE_BRIDGE_ELIGIBLE']
    assert not result['SECURITY_VALUATION_BRIDGE_ELIGIBLE']
    assert args == before
    assert args['target']['adr_ratio'] is None


@pytest.mark.parametrize('mutation', [
    'same_name_different_cik', 'parent_subsidiary', 'missing_underlying', 'missing_issuer',
    'conflicting_cik', 'wrong_dart', 'conflicting_rows', 'hash', 'provider', 'tier',
    'future', 'wrong_url', 'wrong_accession', 'missing_field', 'field_mismatch',
    'unverified', 'source_type', 'warnings', 'canonical_id', 'receipt_missing', 'receipt_failed',
    'source_exchange', 'conflicting_corp', 'conflicting_underlying',
])
def test_identity_denials(mutation):
    a = fixture()
    if mutation == 'same_name_different_cik':
        a['target']['cik'] = '0000000999'
    elif mutation == 'parent_subsidiary':
        a['official']['evidence']['ordinary_share_identifier'] = '654321'
        a['official']['field_provenance']['ordinary_share_identifier']['value'] = '654321'
        a['expected_official_sha256'] = digest(a['official'])
    elif mutation == 'missing_underlying':
        a['official']['evidence']['ordinary_share_identifier'] = None
    elif mutation == 'missing_issuer':
        a['source']['corp_code'] = None
    elif mutation == 'conflicting_cik':
        a['source']['cik'] = '0000000999'
    elif mutation == 'wrong_dart':
        a['dart_rows'][0]['corp_code'] = '00999999'
    elif mutation == 'conflicting_rows':
        a['dart_rows'].append({'stock_code': '123456', 'corp_code': '00999999'})
    elif mutation == 'hash':
        a['expected_official_sha256'] = 'c' * 64
    elif mutation in {'provider', 'tier'}:
        a['official']['provider' if mutation == 'provider' else 'source_tier'] = 'local'
    elif mutation == 'future':
        a['cutoff'] = '2025-01-01'
    elif mutation == 'wrong_url':
        a['official']['field_provenance']['cik']['source_url'] = 'https://evil.test/123/'
    elif mutation == 'wrong_accession':
        a['official']['field_provenance']['cik']['filing_accession'] = 'other'
    elif mutation == 'missing_field':
        del a['official']['field_provenance']['ordinary_share_identifier']
    elif mutation == 'field_mismatch':
        a['official']['field_provenance']['ordinary_share_identifier']['value'] = '654321'
    elif mutation == 'unverified':
        a['official']['field_provenance']['ordinary_share_identifier']['verification_status'] = 'inferred'
    elif mutation == 'source_type':
        a['source']['security_type'] = 'subsidiary'
    elif mutation == 'warnings':
        a['target']['identity_warnings'] = ['conflict']
    elif mutation == 'canonical_id':
        a['source']['canonical_security_id'] = None
    elif mutation == 'receipt_missing':
        a['dart_receipt'] = {}
    elif mutation == 'receipt_failed':
        a['dart_receipt']['HTTP_status'] = 404
    elif mutation == 'source_exchange':
        a['source']['exchange'] = 'OTHER'
    elif mutation == 'conflicting_corp':
        a['target']['corp_code'] = '00999999'
    elif mutation == 'conflicting_underlying':
        a['target']['ordinary_share_identifier'] = '654321'
    if mutation != 'hash':
        a['expected_official_sha256'] = digest(a['official'])
    assert identity_bridge(**a)['status'] == 'FAIL'


@pytest.mark.parametrize('metric', [
    'price', 'ohlcv', 'technical', 'support_resistance', 'volume', 'kr_investor_flow',
    'eps', 'pe', 'pb', 'market_cap', 'dividend_yield', 'per_share_cash_flow', 'adr_ratio',
])
def test_security_metrics_never_cross(metric):
    assert not evidence_scope(metric=metric, subject_scope='legal_issuer',
        context_eligible=True, direction_eligible=True)['context_eligible']


@pytest.mark.parametrize('metric', ['revenue', 'operating_income', 'issuer_business_event'])
def test_scope_and_original_eligibility(metric):
    assert evidence_scope(metric=metric, subject_scope='legal_issuer',
        context_eligible=True, direction_eligible=True)['direction_eligible']
    assert not evidence_scope(metric=metric, subject_scope='security',
        context_eligible=True, direction_eligible=True)['direction_eligible']
    assert not evidence_scope(metric=metric, subject_scope='legal_issuer',
        context_eligible=True, direction_eligible=False)['direction_eligible']
    assert not evidence_scope(metric=metric, subject_scope='legal_issuer',
        context_eligible=True, direction_eligible=True, denied=True)['context_eligible']


def comparison():
    dependency = {'provider': 'opendart', 'prose_eligible': True, 'hard_denial_reasons': [],
        'lineage': {'source_provider': 'opendart'}}
    return {'fact_id': 'original', 'fact_type': 'earnings_comparison', 'prose_eligible': True,
        'interpretation_eligible': True, 'quality_receipt_sha256': 'q',
        'fields': {'metric': 'revenue', 'issuer_id': 'DART:00123456', 'source_ticker': '123456',
            'source_receipt': 'filing', 'source_occurrences': ['current', 'prior'],
            'currency': 'KRW', 'period_start': '2026-04-01', 'period_end': '2026-06-30'},
        'field_dependency_receipts': {'current': deepcopy(dependency), 'comparison': deepcopy(dependency)}}


def test_original_provenance_and_chain_preserved():
    original = comparison()
    projected = {**deepcopy(original), 'fact_id': 'projected'}
    result = bind_comparison(projected, original, identity_bridge(**fixture()), source_result_sha256='frozen')
    assert result['fields'] == original['fields']
    assert result['field_dependency_receipts'] == original['field_dependency_receipts']
    chain = result['issuer_business_bridge']
    assert chain['source_provider'] == 'opendart'
    assert chain['reference_type'] == 'ISSUER_LEVEL_CROSS_SECURITY_EVIDENCE'
    assert chain['monitored_security_id'] == 'nasdaq-security'
    assert chain['original_issuer_id'] == 'DART:00123456'
    assert chain['original_fact_sha256'] == digest(original)


@pytest.mark.parametrize('mutation', ['bridge', 'missing_bridge', 'denied', 'provider', 'metric',
    'period', 'currency', 'occurrence', 'quality', 'issuer', 'source_ticker', 'missing_source_hash'])
def test_binding_denies_tampering(mutation):
    original = comparison()
    projected = deepcopy(original)
    bridge = identity_bridge(**fixture())
    source_sha = 'frozen'
    if mutation == 'bridge':
        bridge['issuer_id'] = 'DART:00999999'
    elif mutation == 'missing_bridge':
        bridge = {}
    elif mutation == 'denied':
        original['field_dependency_receipts']['current']['hard_denial_reasons'] = ['tainted']
        projected = deepcopy(original)
    elif mutation == 'provider':
        original['field_dependency_receipts']['current']['provider'] = 'sec'
        projected = deepcopy(original)
    elif mutation == 'metric':
        original['fields']['metric'] = 'eps'
        projected = deepcopy(original)
    elif mutation in {'period', 'currency', 'occurrence'}:
        projected['fields'][{'period': 'period_end', 'currency': 'currency', 'occurrence': 'source_occurrences'}[mutation]] = 'wrong'
    elif mutation == 'quality':
        projected['quality_receipt_sha256'] = 'wrong'
    elif mutation == 'issuer':
        original['fields']['issuer_id'] = 'DART:00999999'
        projected = deepcopy(original)
    elif mutation == 'source_ticker':
        original['fields']['source_ticker'] = '654321'
        projected = deepcopy(original)
    elif mutation == 'missing_source_hash':
        source_sha = ''
    with pytest.raises(ValueError):
        bind_comparison(projected, original, bridge, source_result_sha256=source_sha)


def test_owner_rejects_recursive_bridge_before_source_replay():
    from app.services.bounded_financial_stock_owner import _issuer_business_facts
    with pytest.raises(ValueError, match='recursive'):
        _issuer_business_facts({}, {'source_inputs': {'issuer_business': {}}})
