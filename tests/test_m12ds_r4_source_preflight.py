from copy import deepcopy

import pytest

from scripts.m12ds_r4_source_preflight import gate


def fixture():
    probe = dict(live_source=True, night_session_usable=True, session_freshness='fresh',
                 finality_valid=True, expected_reference_date='2026-09-21', observations=[])
    canonical, rows = [], []
    for product in ('KOSPI200', 'KOSDAQ150'):
        item = dict(product=product, session_date='2026-09-21', reference_date_match=True,
            finality_valid=True, night_close=101, reference_price=100, point_change=1, change_pct=1,
            night_source_record_id=product + '-N', reference_source_record_id=product + '-D',
            night_source_payload_sha256='night-sha', reference_source_payload_sha256='day-sha')
        probe['observations'].append(item)
        canonical.append(dict(raw_payload={'product': product}, value=101, previous_value=100,
                              change_value=1, change_pct=1))
        rows.extend([{'row_identity': product + '-N', 'response_sha256': 'night-sha'},
                     {'row_identity': product + '-D', 'response_sha256': 'day-sha'}])
    return probe, canonical, rows


def test_verified_pairs_do_not_claim_downstream_render_pass():
    result = gate(*fixture())
    assert result['status'] == 'PASS'
    assert result['downstream_render_status'] == 'NOT_RUN'


@pytest.mark.parametrize('field,value', [('live_source', False), ('finality_valid', False),
    ('night_session_usable', False), ('session_freshness', 'stale'),
    ('expected_reference_date', '2026-09-22')])
def test_unverified_current_source_fails(field, value):
    probe, canonical, rows = fixture()
    probe[field] = value
    assert gate(probe, canonical, rows)['status'] == 'FAIL'


def test_missing_product_is_not_legitimate_publication_unavailability():
    probe, canonical, rows = fixture()
    probe['observations'].pop()
    result = gate(probe, canonical, rows)
    assert result['status'] == 'FAIL'
    assert not result['publication_unavailable_proven']


@pytest.mark.parametrize('field', ['value', 'previous_value', 'change_value', 'change_pct'])
def test_wrong_canonical_value_or_baseline_fails(field):
    probe, canonical, rows = fixture()
    canonical[0][field] += 1
    assert gate(probe, canonical, rows)['status'] == 'FAIL'


def test_raw_identity_hash_and_exact_occurrence_required():
    probe, canonical, rows = fixture()
    changed = deepcopy(rows)
    changed[0]['response_sha256'] = 'wrong'
    assert gate(probe, canonical, changed)['status'] == 'FAIL'
    assert gate(probe, canonical, rows + [rows[0]])['status'] == 'FAIL'


def test_arithmetic_cannot_be_hidden_by_consistent_canonical_copy():
    probe, canonical, rows = fixture()
    probe['observations'][0]['change_pct'] = 2
    canonical[0]['change_pct'] = 2
    assert gate(probe, canonical, rows)['status'] == 'FAIL'
