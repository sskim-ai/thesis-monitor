"""Finite NG15 fiscal-owner regressions; execution belongs to Main's frozen runner.

No application imports or public reads at collection. Public fixtures are the
exact NG14 staged bytes below, not a live source or a new source-use grant.
Synthetic accounting labels describe fixtures, not jurisdictional qualification.
"""

from copy import deepcopy
from datetime import date
from hashlib import sha256
import importlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest


PUBLIC_ROOT = Path(
    '/Users/sskim/Documents/Codex/Reports/'
    '20261019-post-r22-ng14-personal-local/public-tsm-stage'
)
PUBLIC_PINS = {
    'public-tsm-financial-plan.json': (
        2157, '9c4ef4349812ca37ff83fd983a46a3da807a4246bee4d48382cf2b1ff85190df'),
    'request-005.plan.json': (
        439, 'a7b9e670ff40238a22ebac874a6de28c359d7aae8cd5fada4156c6af6b51e52f'),
    'request-004-attempt-1.body': (
        19113, 'c0003452553c8ebe31afb5d1aaa617e6e399474ff302b90ee2a584b5467ccd75'),
    'request-005-attempt-1.body': (
        28002, 'c4619e874538f8777e4af1ab86dc02374ff376074d6b95204ea60ca778ae76b8'),
    'request-006-attempt-1.body': (
        9552, '3abfa492245e25f8d73e93928ee738bf3f8c5365cf04bc6c1205eff0f424e273'),
}
SYNTHETIC_CIK = '0000999999'
SYNTHETIC_ACCESSION = '0000999999-26-000001'
SYNTHETIC_URL = (
    'https://www.sec.gov/Archives/edgar/data/999999/'
    '000099999926000001/synthetic.htm'
)


@pytest.fixture(scope='module')
def owners():
    return SimpleNamespace(**{
        key: importlib.import_module('app.services.' + name)
        for key, name in (
            ('projection', 'bounded_financial_projection'),
            ('foreign', 'sec_foreign_comparison_service'),
            ('purpose', 'sec_fpi_financial_purpose'),
            ('weeks', 'issuer_fiscal_week_policy'),
        )
    })


@pytest.fixture(scope='module')
def public_tsm():
    payloads = {}
    for name, (size, expected_hash) in PUBLIC_PINS.items():
        raw = (PUBLIC_ROOT / name).read_bytes()
        assert len(raw) == size, 'PUBLIC_TSM_SIZE_CHANGED'
        assert sha256(raw).hexdigest() == expected_hash, 'PUBLIC_TSM_PIN_CHANGED'
        payloads[name] = raw
    return payloads


def _statement(headers, *, accounting='IFRS', unit='Unit: NT$ million'):
    headings = ''.join('<th>' + header + '</th>' for header in headers)
    revenues = (1200, 1000, 3300, 2800)[:len(headers)]
    profits = (240, 180, 600, 500)[:len(headers)]
    rows = ''.join(
        '<tr><td>' + label + '</td>'
        + ''.join('<td>' + str(value) + '</td>' for value in values) + '</tr>'
        for label, values in (('Net sales', revenues), ('Income from operations', profits))
    )
    return (
        '<html><body><p>Synthetic ' + accounting + ' fixture.</p>'
        '<table><caption>Consolidated statements of income (' + unit + ')</caption>'
        '<tr><th>Metric</th>' + headings + '</tr>' + rows + '</table></body></html>'
    ).encode()


def _parse(owners, raw):
    return owners.foreign.parse_document(
        raw.decode(), issuer_cik=SYNTHETIC_CIK,
        accession=SYNTHETIC_ACCESSION, document_type='6-K',
        filing_date='2026-10-15', source_url=SYNTHETIC_URL, raw_payload=raw,
    )


@pytest.mark.parametrize('accounting', ['IFRS', 'K-IFRS', 'US GAAP'])
def test_explicit_q3_and_nine_month_columns_keep_separate_occurrences(owners, accounting):
    raw = _statement([
        'three months ended September 30, 2026',
        'three months ended September 30, 2025',
        'nine months ended September 30, 2026',
        'nine months ended September 30, 2025',
    ], accounting=accounting)
    occurrences = _parse(owners, raw)
    assert len(occurrences) == 8
    assert all(not owners.foreign.occurrence_errors(o, date(2026, 10, 18))
               for o in occurrences)
    quarter = [o for o in occurrences if o['period_scope'] == 'single-quarter']
    ytd = [o for o in occurrences if o['period_scope'] == 'other-duration']
    assert len(quarter) == len(ytd) == 4
    assert {o['period_start'][5:] for o in quarter} == {'07-01'}
    assert {o['period_start'][5:] for o in ytd} == {'01-01'}
    current = owners.foreign.current_projection(occurrences)
    assert current['revenue'] == 1_200_000_000
    assert current['operating_income'] == 240_000_000
    assert owners.foreign.current_projection(ytd) is None
    assert owners.foreign.current_projection(ytd, required_role='half-year') is None
    assert owners.foreign.current_projection(ytd, required_role='annual') is None


def test_rehashed_period_tuple_cannot_replace_missing_source_header_authority(owners):
    raw = _statement(['3Q26', '3Q25'])
    raw = raw.replace(b'<body>', b'<body><p>Third quarter ended September 30, 2026.</p>')
    occurrences = _parse(owners, raw)
    assert len(occurrences) == 4
    assert all(o['period_start'] is None for o in occurrences)
    assert owners.foreign.current_projection(occurrences) is None
    forged = deepcopy(occurrences)
    for occurrence in forged:
        year = 2026 if occurrence['source_cell']['column'] == 1 else 2025
        occurrence.update(owners.foreign.period_from_headers([
            f'{year}-07-01 to {year}-09-30']))
        occurrence['occurrence_id'] = owners.foreign.sha({
            k: v for k, v in occurrence.items() if k != 'occurrence_id'})
        errors = owners.foreign.occurrence_errors(occurrence, date(2026, 10, 18))
        assert 'foreign_occurrence_identity_mismatch' not in errors
        assert 'exact_period_context_unresolved' in errors
    assert owners.foreign.current_projection(forged) is None


def test_conflicting_currency_caption_has_no_numeric_field_authority(owners):
    raw = _statement(
        ['2026-07-01 to 2026-09-30', '2025-07-01 to 2025-09-30'],
        unit='Unit: NT$ million; Unit: US$ million',
    )
    assert _parse(owners, raw) == []


def test_mixed_current_currency_fields_do_not_form_a_statement(owners):
    headers = ['2026-07-01 to 2026-09-30', '2025-07-01 to 2025-09-30']
    twd = _parse(owners, _statement(headers))
    usd = _parse(owners, _statement(headers, unit='Unit: US$ million'))
    mixed = ([o for o in twd if o['field'] == 'revenue']
             + [o for o in usd if o['field'] == 'operating_income'])
    assert all(not owners.foreign.occurrence_errors(o, date(2026, 10, 18)) for o in mixed)
    assert owners.foreign.current_projection(mixed) is None


def test_52_53_week_pair_requires_issuer_bound_source_policy(owners):
    filing = dict(form='20-F', accessionNumber='0000999999-25-000001')
    raw = (
        'Our fiscal year ends on the Saturday nearest January 31 and typically consists of 52 weeks. '
        'Approximately every six years we have a 53-week fiscal year to align our calendar policy. '
        'Fiscal year 2025 was comprised of 52 weeks and ended on February 1, 2025. '
        'Fiscal year 2024 was comprised of 53 weeks and ended on February 3, 2024.'
    ).encode()
    proof = owners.weeks.extract_policy(raw, issuer=SYNTHETIC_CIK, filing=filing)
    assert proof['status'] == 'PROVEN'
    current = dict(
        context_eligible=True, canonical_company_id='synthetic-company',
        canonical_security_id='synthetic-security', provider_issuer_id=SYNTHETIC_CIK,
        source_provider='sec_edgar', source_document_id=filing['accessionNumber'],
        metric='revenue', semantic='statement_revenue', period_role='ANNUAL',
        statement_basis='consolidated', currency='USD', unit='USD', unit_scale=1,
        formal_state='FORMAL', period_start='2024-02-04', period_end='2025-02-01',
    )
    prior = {**current, 'period_start': '2023-01-29', 'period_end': '2024-02-03'}
    assert not owners.projection.paired(current, prior)
    assert owners.projection.paired({**current, 'issuer_fiscal_policy': proof}, prior)
    wrong_issuer = {**proof, 'issuer': '0000888888'}
    wrong_issuer['receipt_sha256'] = owners.weeks.digest({
        k: v for k, v in wrong_issuer.items() if k != 'receipt_sha256'})
    assert not owners.projection.paired({**current, 'issuer_fiscal_policy': wrong_issuer}, prior)
    assert not owners.projection.paired(
        {**current, 'period_role': 'SINGLE_QUARTER', 'issuer_fiscal_policy': proof},
        {**prior, 'period_role': 'SINGLE_QUARTER'},
    )


def test_unknown_newer_filing_does_not_license_older_explicit_quarter(owners):
    old = dict(
        purpose='FINANCIAL_STATEMENTS', accession='synthetic-older', filing_date='2025-10-15',
        economic_periods=[dict(start='2025-07-01', end='2025-09-30', role='single-quarter')],
    )
    newer = dict(
        purpose='UNKNOWN_PURPOSE', accession='synthetic-newer', filing_date='2026-10-15',
        economic_periods=[],
    )
    result = owners.purpose.select_economic_period([old, newer])
    assert result['status'] == 'BLOCKED'
    assert 'NEWER_FPI_PURPOSE_OR_PERIOD_UNRESOLVED' in result['denial_reasons']
    annual = {**old, 'economic_periods': [
        dict(start='2025-01-01', end='2025-12-31', role='annual')]}
    result = owners.purpose.select_economic_period([annual, newer])
    assert result['status'] == 'BLOCKED'
    assert result['source_accessions'] == []


def test_exact_public_latest_release_stops_at_cell_period_and_deck_authority(
        owners, public_tsm, record_property):
    plan = json.loads(public_tsm['public-tsm-financial-plan.json'])
    request = json.loads(public_tsm['request-005.plan.json'])
    assert request['plan_sha256'] == owners.projection.digest(plan)
    filing = request['filing']
    assert filing['accessionNumber'] == '0001046179-26-000726'
    base = request['url'].rsplit('/', 1)[0] + '/'
    cover = dict(
        filing=filing, url=base + filing['primaryDocument'],
        raw=public_tsm['request-004-attempt-1.body'],
    )
    release = owners.purpose.classify_document(
        public_tsm['request-005-attempt-1.body'], url=request['url'],
        filing=filing, plan=plan, context_documents=[cover],
    )
    occurrences = release['occurrences']
    assert len(occurrences) == 6
    assert {(o['source_cell']['table'], o['source_cell']['row'], o['source_cell']['column'])
            for o in occurrences} == {(2, row, col) for row in (2, 4) for col in (3, 6, 12)}
    assert {(o['field'], o['reported_value']) for o in occurrences} == {
        ('revenue', 1494243), ('revenue', 989918), ('revenue', 1270381),
        ('operating_income', 876445), ('operating_income', 500685),
        ('operating_income', 766603),
    }
    assert {(o['currency'], o['unit_scale']) for o in occurrences} == {('TWD', 1000000)}
    assert all(o['period_start'] is None and o['period_end'] is None for o in occurrences)
    assert all('exact_period_context_unresolved' in
               owners.foreign.occurrence_errors(o, date(2026, 10, 18)) for o in occurrences)
    assert release['valid_occurrence_ids'] == []
    assert release['economic_periods'] == []
    assert release['financial_authority'] is False
    assert owners.foreign.current_projection(occurrences) is None
    deck = owners.purpose.classify_document(
        public_tsm['request-006-attempt-1.body'], url=base + 'a3q26presentatione.htm',
        filing=filing, plan=plan, context_documents=[cover],
    )
    assert deck['purpose'] == 'UNKNOWN_PURPOSE'
    assert deck['unresolved_financial_content'] is True
    assert deck['occurrences'] == []
    assert deck['financial_authority'] is False
    assert deck['accession'] == release['accession']
    record_property('ng15_tsm_public_proof', json.dumps({
        'scope': 'LATEST_PUBLIC_DOCUMENT_DIAGNOSTIC_ONLY',
        'source_generation': plan['run_id'],
        'cutoff': plan['cutoff'],
        'accession': filing['accessionNumber'],
        'issuer_cik': plan['issuer'],
        'filing_date': filing['filingDate'],
        'verified_public_pins': {
            name: {'bytes': len(raw), 'sha256': sha256(raw).hexdigest()}
            for name, raw in public_tsm.items()
        },
        'release': {
            'source_url': release['source_url'],
            'source_sha256': release['source_payload_sha256'],
            'receipt_sha256': release['receipt_sha256'],
            'parsed_occurrence_count': len(occurrences),
            'valid_occurrence_count': len(release['valid_occurrence_ids']),
            'fields': sorted({o['field'] for o in occurrences}),
            'period_unknown_occurrence_count': sum(
                o['period_start'] is None and o['period_end'] is None for o in occurrences),
            'economic_periods': release['economic_periods'],
            'financial_authority': release['financial_authority'],
            'occurrences': [{
                'occurrence_id': o['occurrence_id'], 'field': o['field'],
                'source_cell': {key: o['source_cell'][key] for key in ('table', 'row', 'column')},
                'period_start': o['period_start'], 'period_end': o['period_end'],
            } for o in occurrences],
        },
        'deck': {
            'source_url': deck['source_url'],
            'source_sha256': deck['source_payload_sha256'],
            'receipt_sha256': deck['receipt_sha256'],
            'purpose': deck['purpose'],
            'unresolved_financial_content': deck['unresolved_financial_content'],
            'parsed_occurrence_count': len(deck['occurrences']),
            'valid_occurrence_count': len(deck['valid_occurrence_ids']),
            'financial_authority': deck['financial_authority'],
            'same_filing_as_release': deck['accession'] == release['accession'],
        },
        'full_project_replayed': False,
        'inherited_ng14_projection_sha256':
            '4cdb5ea60e43eeff585db90fc8d605fb2d5944d91d76202b0d60f1675007ba09',
        'inherited_ng14_owner_denial': 'EXPECTED_BUSINESS_QUALITY_OWNER_OUTPUT_MISSING',
        'inherited_evidence_is_current_execution': False,
        'new_source_use_grant': False,
    }, sort_keys=True))
