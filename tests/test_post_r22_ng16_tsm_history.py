"""Bounded REV5 public decision-input replay through the original consumers.

No application imports or fixture reads at collection. This is not raw-document
reacquisition, a full project replay, or authority for current Q3/NG16. Main owns
the single final run; the existing NG15 public Q3 diagnostic remains separate.
"""

from copy import deepcopy
from hashlib import sha256
import importlib
import json
from pathlib import Path
import stat
from types import SimpleNamespace

import pytest


PUBLIC_ROOT = Path(
    '/Users/sskim/Documents/Codex/Reports/'
    '20261019-post-r22-ng16-historical-reintegration/tsm-history/rev5'
)
PUBLIC_PINS = {
    'TSM-financial-source-proof.json': (
        562740, '7dd35b9de47f48223722971aee4d1e4f9c4d183513b141a195a7693b9ce67f98'),
}
REV5_ARCHIVE_SHA256 = '3d0b90627ff48bb782c75dc6d1c95d693b13c9089118418606ca753b1325bc6e'
HISTORICAL_GENERATION = 'r5-rev2-20260927T093334+0900'
HISTORICAL_CUTOFF = '2026-09-27'
ISSUER = '0001046179'
SELECTED_ACCESSION = '0001046179-26-000541'
METRICS = ('revenue', 'operating_income')


@pytest.fixture(scope='module')
def owners():
    return SimpleNamespace(
        snapshot=importlib.import_module('app.models.financial').FinancialSnapshot,
        selection=importlib.import_module('app.services.sec_fpi_field_selection'),
        purpose=importlib.import_module('app.services.sec_fpi_financial_purpose'),
        authority=importlib.import_module('scripts.m12dr_financial_source_authority'),
        stock=importlib.import_module('app.services.bounded_financial_stock_owner'),
        quality=importlib.import_module('app.services.canonical_business_quality_owner'),
    )


@pytest.fixture(scope='module')
def history_bytes():
    name, (size, expected_hash) = next(iter(PUBLIC_PINS.items()))
    path = PUBLIC_ROOT / name
    info = path.lstat()
    assert stat.S_ISREG(info.st_mode), 'REV5_PUBLIC_INPUT_NOT_REGULAR'
    assert info.st_size == size, 'REV5_PUBLIC_INPUT_SIZE_CHANGED'
    raw = path.read_bytes()
    assert len(raw) == size, 'REV5_PUBLIC_INPUT_SIZE_CHANGED'
    assert sha256(raw).hexdigest() == expected_hash, 'REV5_PUBLIC_INPUT_PIN_CHANGED'
    return raw


@pytest.fixture
def history(history_bytes):
    proof = json.loads(history_bytes)
    assert proof['ticker'] == 'TSM'
    bundles = proof['source_quality']
    assert len(bundles) == 2
    assert all(bundle['source_generation_id'] == HISTORICAL_GENERATION for bundle in bundles)
    assert all(bundle['source_inputs']['cutoff'] == HISTORICAL_CUTOFF for bundle in bundles)
    assert bundles[0]['source_inputs']['foreign_candidates'] == bundles[1]['source_inputs']['foreign_candidates']
    assert len(bundles[0]['source_inputs']['foreign_candidates']) == 2
    return proof


def _rows(owners, history):
    return [owners.snapshot.model_validate(row)
            for row in history['source_quality'][0]['source_inputs']['foreign_candidates']]


def _comparison_inputs(history):
    # This is the original financial-only consumer's input slice, not a fabricated
    # full acquisition/projection or a source-qualified current-generation plan.
    plan = {'market': 'us', 'ticker': 'TSM', 'issuer': ISSUER}
    projection = {'quality_bundles': history['source_quality']}
    return plan, projection


def test_rev5_real_field_selection_keeps_nonfinancial_supersession_local(
        owners, history, record_property):
    selected, receipt = owners.selection.select_fields(
        history['purpose_documents'], _rows(owners, history),
        ticker='TSM', cutoff=HISTORICAL_CUTOFF, allow_inline_annual=False,
    )
    assert receipt == history['per_field_selection']
    assert receipt['status'] == 'PASS'
    assert receipt['source_accessions'] == [SELECTED_ACCESSION]
    assert receipt['period_end'] == '2026-06-30'
    assert len(selected) == 2
    expected = {
        metric: owners.snapshot.model_validate(bundle['source_inputs']['formal'])
        for metric, bundle in zip(METRICS, history['source_quality'], strict=True)
    }
    for row in selected:
        active = [metric for metric in METRICS if getattr(row, metric) is not None]
        assert len(active) == 1
        assert row.model_dump(mode='json') == expected[active[0]].model_dump(mode='json')
        assert row.net_income is None
    later = [doc for doc in history['purpose_documents']
             if doc['filing_date'] > '2026-08-14']
    assert {doc['purpose'] for doc in later} == {
        'DIVIDEND_OR_CAPITAL_RETURN', 'GOVERNANCE_OR_COMPENSATION',
        'REVENUE_DISCLOSURE_ONLY',
    }
    record_property('ng16_tsm_history_proof', json.dumps({
        'scope': 'HISTORICAL_DECISION_INPUT_REPLAY_NOT_CURRENT_QUALIFICATION',
        'archive_sha256': REV5_ARCHIVE_SHA256,
        'fixture_sha256': PUBLIC_PINS['TSM-financial-source-proof.json'][1],
        'source_generation': HISTORICAL_GENERATION,
        'cutoff': HISTORICAL_CUTOFF,
        'selection': receipt,
        'consumer': 'sec_fpi_field_selection.select_fields',
        'full_project_replayed': False,
        'current_q3_qualified': False,
    }, sort_keys=True))


@pytest.mark.parametrize('index,metric', [(0, 'revenue'), (1, 'operating_income')],
                         ids=['revenue', 'operating_income'])
def test_rev5_real_quality_replays_original_consumer(owners, history, index, metric):
    bundle = history['source_quality'][index]
    replay = owners.authority.source_quality(bundle)
    assert replay == bundle['quality']
    assert replay['status'] == 'PASS'
    assert [item['metric'] for item in replay['comparative_observations']] == [metric]
    comparison = replay['comparative_observations'][0]
    current = comparison['current']['lineage']['occurrence']
    prior = comparison['comparison']['lineage']['occurrence']
    assert (current['period_start'], current['period_end']) == ('2026-04-01', '2026-06-30')
    assert (prior['period_start'], prior['period_end']) == ('2025-04-01', '2025-06-30')
    assert current['accession'] == prior['accession'] == SELECTED_ACCESSION
    assert current['currency'] == prior['currency'] == 'TWD'
    assert current['unit_scale'] == prior['unit_scale'] == 1000
    assert current['statement_basis'] == prior['statement_basis'] == 'consolidated'


def test_rev5_real_comparison_materializer_preserves_field_scope(owners, history):
    facts, denials = owners.stock.reported_comparisons(*_comparison_inputs(history))
    assert denials == []
    assert len(facts) == 2
    assert {fact['fields']['metric'] for fact in facts} == set(METRICS)
    expected = {item['metric']: item for item in history['comparisons']}
    for fact in facts:
        fields = fact['fields']
        comparison = expected[fields['metric']]
        assert fields['current_value'] == comparison['current']['lineage']['amount']
        assert fields['prior_comparable_value'] == comparison['comparison']['lineage']['amount']
        assert fields['delta'] == comparison['delta']
        assert fields['issuer_id'] == 'CIK:' + ISSUER
        assert fields['source_receipt'] == SELECTED_ACCESSION
        assert fields['period_end'] == '2026-06-30'
        assert fields['recurrence_verified'] is False
        assert fact['issuer_projection'] is None
        assert fact['fact_type'] == 'earnings_comparison'
    assert any(item['field'] == 'net_income' for item in history['denials'])


def test_rev5_real_rows_newer_unknown_still_denies(owners, history):
    filing = {
        'accessionNumber': '0001046179-26-999999', 'filingDate': '2026-09-25',
        'form': '6-K', 'primaryDocument': 'synthetic-unknown.htm',
        'reportDate': '2026-09-25',
    }
    url = ('https://www.sec.gov/Archives/edgar/data/1046179/'
           '000104617926999999/synthetic-unknown.htm')
    unknown = owners.purpose.classify_document(
        b'<p>Synthetic negative fixture: Financial results attached</p>',
        url=url, filing=filing, plan={'issuer': ISSUER, 'cutoff': HISTORICAL_CUTOFF},
    )
    assert unknown['purpose'] == 'UNKNOWN_PURPOSE'
    assert unknown['financial_authority'] is False
    selected, receipt = owners.selection.select_fields(
        [*history['purpose_documents'], unknown], _rows(owners, history),
        ticker='TSM', cutoff=HISTORICAL_CUTOFF, allow_inline_annual=False,
    )
    assert selected == []
    assert receipt['status'] == 'BLOCKED'
    assert 'NEWER_DOCUMENT_PURPOSE_UNRESOLVED' in receipt['denial_reasons']
    assert all(url in receipt['fields'][metric]['unresolved_sources'] for metric in METRICS)


@pytest.mark.parametrize('mutation,reason', [
    ('input_hash', 'reported_quality_frozen_source_digest_mismatch'),
    ('stored_quality_receipt', 'financial_quality_replay_changed'),
], ids=['input_hash', 'stored_quality_receipt'])
def test_rev5_tampered_quality_cannot_reach_comparison_materializer(
        owners, history, mutation, reason):
    plan, projection = _comparison_inputs(deepcopy(history))
    bundle = projection['quality_bundles'][0]
    if mutation == 'input_hash':
        bundle['source_inputs_sha256'] = '0' * 64
    else:
        bundle['quality']['receipt_sha256'] = '0' * 64
    with pytest.raises(ValueError, match=reason):
        owners.stock.reported_comparisons(plan, projection)


def test_rev5_generation_cannot_be_relabelled_current(owners, history):
    plan, projection = _comparison_inputs(history)
    facts, denials = owners.stock.reported_comparisons(plan, projection)
    assert facts and not denials
    with pytest.raises(ValueError, match='fresh_quality_generation_or_subject_mismatch'):
        owners.quality.derive_fresh(
            projection=projection, facts=facts, ticker='TSM',
            security_id='synthetic-generation-negative-only',
            run_id='ng16-synthetic-not-an-authorized-generation',
        )
