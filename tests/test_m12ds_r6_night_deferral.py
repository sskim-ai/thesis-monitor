from copy import deepcopy

import pytest

from scripts.m12ds_r4_collect import night_collection_mode


def evidence():
    return ({'status': 'FAIL', 'errors': ['current_official_night_pair_unavailable', 'night_finality_unverified']},
            {'live_source': True, 'finality_valid': False, 'expected_reference_date': '2026-09-22',
             'date_statuses': [{'query_date': '2026-09-22', 'http_status': 200, 'result': 'empty'}]})


def test_missing_night_still_blocks_by_default():
    with pytest.raises(ValueError, match='night_source_gate_required'):
        night_collection_mode(*evidence())


def test_explicit_deferral_preserves_failed_receipt():
    gate, probe = evidence()
    before = deepcopy((gate, probe))
    assert night_collection_mode(gate, probe, defer_unavailable_night=True)
    assert (gate, probe) == before
    assert not night_collection_mode({'status': 'PASS'}, probe, defer_unavailable_night=True)


@pytest.mark.parametrize('mutation', ['arithmetic', 'http_error', 'wrong_date', 'not_live', 'final'])
def test_deferral_does_not_authorize_other_failures(mutation):
    gate, probe = evidence()
    if mutation == 'arithmetic':
        gate['errors'].append('KOSPI200:change_arithmetic')
    elif mutation == 'http_error':
        probe['date_statuses'][0]['http_status'] = 500
    elif mutation == 'wrong_date':
        probe['date_statuses'][0]['query_date'] = '2026-09-21'
    elif mutation == 'not_live':
        probe['live_source'] = False
    else:
        probe['finality_valid'] = True
    with pytest.raises(ValueError, match='night_source_gate_required'):
        night_collection_mode(gate, probe, defer_unavailable_night=True)
