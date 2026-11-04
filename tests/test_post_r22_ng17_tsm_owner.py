"""NG17 real public Q3 evidence negatives; Main owns the single final run.

No application imports or fixture reads during collection. Historical mutation
controls are not current-source positives or a new source-use grant.
"""

from copy import deepcopy
from datetime import date
from decimal import Decimal
from hashlib import sha256
import importlib
import json
import os
from pathlib import Path
import stat
from types import SimpleNamespace

import pytest

from tests.test_post_r22_ng15_tsm_owner import PUBLIC_PINS as NG14_PINS
from tests.test_post_r22_ng15_tsm_owner import PUBLIC_ROOT as NG14_ROOT
from tests.test_post_r22_ng16_tsm_history import PUBLIC_PINS as REV5_PINS
from tests.test_post_r22_ng16_tsm_history import PUBLIC_ROOT as REV5_ROOT


ADDITIONAL_PUBLIC_PINS = {
    'request-001-attempt-1.body': (162358, '8fafb91b40c2c0bd75e3efd8977f177e69a566fa2700bebf150cc2820fadd272'),
    'request-003-attempt-1.body': (2218, '193a95ef5c74fdbe6e1bbc10c727118502dc8e5c312bb0506150ba59058fde8f'),
    'request-008.plan.json': (437, '41dc49daeffbab4af1630abc959f281f18440ca5333ea68b0414db5be185de70'),
    'request-008-attempt-1.body': (88897, 'ee081c92b750e63db95ac0225d4752a36d0c793a12b3452f3ae2f76ce77487ee'),
}
PUBLIC_READ_ALLOWLIST = {
    **{NG14_ROOT / name: pin for name, pin in {**NG14_PINS, **ADDITIONAL_PUBLIC_PINS}.items()},
    **{REV5_ROOT / name: pin for name, pin in REV5_PINS.items()},
}
CUTOFF = '2026-10-18'
ACCESSION = '0001046179-26-000726'


def _read_public(path):
    path = Path(path)
    if path not in PUBLIC_READ_ALLOWLIST:
        raise ValueError('NG17_TSM_PUBLIC_READ_NOT_ALLOWLISTED')
    assert path.resolve() == path, 'NG17_TSM_PUBLIC_SYMLINK'
    size, expected_hash = PUBLIC_READ_ALLOWLIST[path]
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(fd, 'rb') as stream:
        info = os.fstat(stream.fileno())
        assert stat.S_ISREG(info.st_mode) and info.st_size == size
        raw = stream.read(size + 1)
    assert len(raw) == size and sha256(raw).hexdigest() == expected_hash
    return raw


@pytest.fixture(scope='module')
def public_inputs():
    return {path.name: _read_public(path) for path in PUBLIC_READ_ALLOWLIST}


@pytest.fixture(scope='module')
def owners():
    return SimpleNamespace(
        snapshot=importlib.import_module('app.models.financial').FinancialSnapshot,
        foreign=importlib.import_module('app.services.sec_foreign_comparison_service'),
        purpose=importlib.import_module('app.services.sec_fpi_financial_purpose'),
        selection=importlib.import_module('app.services.sec_fpi_field_selection'),
        projection=importlib.import_module('app.services.bounded_financial_projection'),
        quality=importlib.import_module('app.services.canonical_business_quality_owner'),
        boundary=importlib.import_module('app.services.sec_foreign_statement_boundary_service'),
    )


@pytest.fixture
def history(public_inputs):
    return json.loads(public_inputs['TSM-financial-source-proof.json'])


@pytest.fixture
def current(owners, public_inputs):
    plan = json.loads(public_inputs['public-tsm-financial-plan.json'])
    request = json.loads(public_inputs['request-005.plan.json'])
    assert request['plan_sha256'] == owners.projection.digest(plan)
    filing = request['filing']
    assert filing['accessionNumber'] == ACCESSION
    base = request['url'].rsplit('/', 1)[0] + '/'
    cover = dict(filing=filing, url=base + filing['primaryDocument'],
                 raw=public_inputs['request-004-attempt-1.body'])
    documents = [owners.purpose.classify_document(
        public_inputs[name], url=base + filename, filing=filing, plan=plan,
        context_documents=[cover],
    ) for name, filename in (
        ('request-005-attempt-1.body', 'a3q26e_withguidancexfinal.htm'),
        ('request-006-attempt-1.body', 'a3q26presentatione.htm'),
    )]
    assert all(not document['financial_authority'] for document in documents)
    return SimpleNamespace(plan=plan, release=documents[0], deck=documents[1])


def _prior_q3(owners, history, scope='single-quarter'):
    result = []
    for raw in history['source_quality'][0]['source_inputs']['foreign_candidates']:
        row = owners.snapshot.model_validate(raw)
        result.extend(o for o in owners.foreign.occurrences(row)
                      if o['period_end'] == '2025-09-30' and o['period_scope'] == scope)
    assert {o['field'] for o in result} == {'revenue', 'operating_income'}
    return result


@pytest.mark.parametrize('documents', ['release', 'deck', 'both'])
def test_real_current_q3_blocks_historical_q2_field_selection(
        owners, history, current, documents):
    rows = [owners.snapshot.model_validate(row) for row in
            history['source_quality'][0]['source_inputs']['foreign_candidates']]
    baseline, old = owners.selection.select_fields(
        history['purpose_documents'], rows, ticker='TSM', cutoff=CUTOFF,
        allow_inline_annual=False,
    )
    assert len(baseline) == 2 and old['period_end'] == '2026-06-30'
    added = ([current.release, current.deck] if documents == 'both'
             else [getattr(current, documents)])
    selected, receipt = owners.selection.select_fields(
        [*history['purpose_documents'], *added], rows,
        ticker='TSM', cutoff=CUTOFF, allow_inline_annual=False,
    )
    assert selected == [] and receipt['status'] == 'BLOCKED'
    assert receipt['source_accessions'] == []
    assert 'NEWER_DOCUMENT_PURPOSE_UNRESOLVED' in receipt['denial_reasons']
    for metric in ('revenue', 'operating_income'):
        assert all(d['document_identity'] in receipt['fields'][metric]['unresolved_sources']
                   for d in added)


def test_real_metadata_and_monthly_source_do_not_supply_q3_bounds(
        owners, public_inputs, current):
    submissions = json.loads(public_inputs['request-001-attempt-1.body'])
    assert submissions['cik'] == '0001046179'
    assert submissions['fiscalYearEnd'] == '1231'
    recent = submissions['filings']['recent']
    index = recent['accessionNumber'].index(ACCESSION)
    assert recent['reportDate'][index] == '2026-09-30'
    unresolved = owners.foreign.period_from_headers([
        '3Q26', submissions['fiscalYearEnd'], recent['reportDate'][index]])
    assert unresolved['period_start'] is None and unresolved['period_end'] is None
    request = json.loads(public_inputs['request-008.plan.json'])
    assert request['filing']['accessionNumber'] == '0001046179-26-000680'
    assert request['plan_sha256'] == owners.projection.digest(current.plan)
    monthly = owners.purpose.classify_document(
        public_inputs['request-008-attempt-1.body'], url=request['url'],
        filing=request['filing'], plan=current.plan,
    )
    assert monthly['financial_authority'] is False
    assert not any(p['role'] == 'single-quarter' for p in monthly['economic_periods'])
    period = owners.purpose.select_economic_period([monthly, current.release, current.deck])
    assert period['status'] == 'BLOCKED' and period['period_end'] is None


def test_real_prior_q3_cannot_complete_current_missing_period(owners, history, current):
    prior = _prior_q3(owners, history)
    assert all(not owners.foreign.occurrence_errors(o, date.fromisoformat(CUTOFF)) for o in prior)
    assert {o['period_start'] for o in prior} == {'2025-07-01'}
    assert {o['source_payload_sha256'] for o in prior} == {
        '6840b97d113f011a776b3da19cc37247b1833585aac922c8b4f525b7a01bfb8b'}
    assert len(current.release['occurrences']) == 6
    for occurrence in current.release['occurrences']:
        authority = owners.foreign.authoritative_prior(
            occurrence, prior, date.fromisoformat(CUTOFF))
        assert authority['status'] == 'FAIL' and authority['accession'] is None
        assert 'exact_period_context_unresolved' in owners.foreign.occurrence_errors(
            occurrence, date.fromisoformat(CUTOFF))
    assert owners.foreign.current_projection(current.release['occurrences']) is None


def test_actual_same_filing_deck_is_neither_independent_review_nor_exact_units(
        owners, public_inputs, current):
    index = json.loads(public_inputs['request-003-attempt-1.body'])
    names = {entry['name'] for entry in index['directory']['item']}
    assert {'a3q26e_withguidancexfinal.htm', 'a3q26presentatione.htm'} <= names
    cover = public_inputs['request-004-attempt-1.body'].decode()
    assert 'a3q26presentatione.htm' in cover and 'a3q26e_withguidancexfinal.htm' in cover
    release = public_inputs['request-005-attempt-1.body'].decode()
    deck = public_inputs['request-006-attempt-1.body'].decode()
    parser = owners.purpose.PlainText()
    parser.feed(deck)
    text = ' '.join(parser.parts)
    assert 'Guidance' in text and '4Q26' in text and '3Q26' in text
    assert '1,494.24' in text and 'NT$ billions' in text
    # The known same-filing rounded figure is not a second exact amount owner.
    assert Decimal('1494.24') * 10**9 != Decimal('1494243') * 10**6
    assert owners.boundary.document_evidence_class(release) is None
    assert owners.boundary.document_evidence_class(deck) is None
    assert current.deck['accession'] == current.release['accession']
    assert current.deck['purpose'] == 'UNKNOWN_PURPOSE'
    assert current.deck['unresolved_financial_content'] is True
    assert current.deck['financial_authority'] is False
    assert current.deck['occurrences'] == []


def test_current_zero_facts_cannot_become_authentic_absence(owners, current):
    # This negative-only consumer input is not a replayed full acquisition.
    projection = dict(
        comparisons=[], fields=[], quality_bundles=[], comparison_candidates=[],
        denials=[{'reason': 'exact_period_context_unresolved'}],
        latest_selected_period_unavailable=True,
        freshness={'full_financial_freshness': 'unknown'},
        fpi_purpose={'documents': [current.release, current.deck]},
    )
    applicability = owners.projection.comparison_applicability(projection)
    assert applicability['state'] == 'QUALITY_EXPECTED_OWNER_OUTPUT_MISSING'
    assert applicability['direction_eligible'] is False
    projection['comparison_applicability'] = applicability
    with pytest.raises(ValueError, match='EXPECTED_BUSINESS_QUALITY_OWNER_OUTPUT_MISSING'):
        owners.quality.derive_fresh(
            projection=projection, facts=[], ticker='TSM',
            security_id=current.plan['security']['canonical_security_id'],
            run_id=current.plan['run_id'],
        )


@pytest.mark.parametrize('mutation,reason', [
    ('wrong_issuer', 'foreign_document_binding_invalid'),
    ('million_scale', 'foreign_currency_unit_value_invalid'),
    ('wrong_prior_year', 'exact_period_context_unresolved'),
    ('nine_months_as_quarter', 'exact_period_context_unresolved'),
    ('week_calendar', 'exact_period_context_unresolved'),
])
def test_original_prior_q3_validator_rejects_rehashed_source_misuse(
        owners, history, mutation, reason):
    scope = 'other-duration' if mutation == 'nine_months_as_quarter' else 'single-quarter'
    occurrence = deepcopy(next(o for o in _prior_q3(owners, history, scope)
                               if o['field'] == 'revenue'))
    assert not owners.foreign.occurrence_errors(occurrence, date.fromisoformat(CUTOFF))
    if mutation == 'wrong_issuer':
        occurrence['issuer_cik'] = '0000999999'
    elif mutation == 'million_scale':
        occurrence['unit_scale'] = 1000000
        occurrence['value'] = occurrence['reported_value'] * 1000000
    elif mutation == 'wrong_prior_year':
        occurrence.update(owners.foreign.period_from_headers(['2024-07-01 to 2024-09-30']))
    elif mutation == 'nine_months_as_quarter':
        occurrence.update(period_scope='single-quarter', period_type='Q3',
                          is_cumulative=False, duration_days=92)
    else:
        occurrence.update(owners.foreign.period_from_headers(['2025-06-29 to 2025-09-27']))
    occurrence['occurrence_id'] = owners.foreign.sha({
        key: value for key, value in occurrence.items() if key != 'occurrence_id'})
    errors = owners.foreign.occurrence_errors(occurrence, date.fromisoformat(CUTOFF))
    assert 'foreign_occurrence_identity_mismatch' not in errors
    assert reason in errors
    assert owners.foreign.current_projection([occurrence]) is None
