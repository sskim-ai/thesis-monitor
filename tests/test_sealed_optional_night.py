from copy import deepcopy
from datetime import datetime, timedelta

import pytest

from app.services.unified_snapshot_contract import digest
from scripts.r2b_r5_market_adapter import project_optional_night
from tests.night_owner_fixtures import night_fixture
from tests.test_r2b_r5_market_adapter import fixture, project


def evaluate(night):
    seed = dict(parent_run_id=night['original_run_id'], started_at=night['observed_at'],
        run_acquisitions={'night':digest(night['value'])})
    return project_optional_night(night, seed=seed,
        cutoff=datetime.fromisoformat(night['observed_at'])+timedelta(minutes=2))


def reseal(night):
    night['value_sha256'] = digest(night['value'])
    return night


@pytest.mark.parametrize('at,expected,state', [
    ('2026-10-06T23:59:59+09:00','2026-10-02','UNAVAILABLE_NO_CURRENT_FINAL_ROW'),
    ('2026-10-07T00:00:01+09:00','2026-10-06','UNAVAILABLE_BEFORE_FINALITY'),
    ('2026-10-07T00:28:00+09:00','2026-10-06','UNAVAILABLE_BEFORE_FINALITY'),
    ('2026-10-07T05:59:59+09:00','2026-10-06','UNAVAILABLE_BEFORE_FINALITY'),
    ('2026-10-07T06:00:00+09:00','2026-10-06','UNAVAILABLE_NO_CURRENT_FINAL_ROW'),
    ('2026-10-07T08:10:00+09:00','2026-10-06','UNAVAILABLE_NO_CURRENT_FINAL_ROW'),
    ('2026-10-04T08:10:00+09:00','2026-10-02','UNAVAILABLE_NO_CURRENT_FINAL_ROW'),
    ('2026-10-05T08:10:00+09:00','2026-10-02','UNAVAILABLE_NO_CURRENT_FINAL_ROW'),
])
def test_sealed_clock_rollover_finality_weekend_holiday(at, expected, state):
    rows, receipt = evaluate(night_fixture(at))
    assert not rows and receipt['state'] == state and receipt['coverage_resolved']
    assert receipt['observation_clock']['expected_reference_date'] == expected
    assert receipt['current_consumer_eligible_count'] == 0
    assert receipt['provider_outage_inferred'] is False


@pytest.mark.parametrize('case,count', [('empty',0),('stale',1),('available',1)])
def test_count_separation_preserves_all_source_rows(case, count):
    night = night_fixture(case=case)
    before = deepcopy(night)
    rows, receipt = evaluate(night)
    assert night == before
    assert receipt['producer_observation_count'] == count
    assert receipt['current_consumer_eligible_count'] == (case == 'available')
    assert receipt['state'] == ('AVAILABLE_FINAL' if case == 'available' else 'UNAVAILABLE_NO_CURRENT_FINAL_ROW')
    assert len(rows) == (case == 'available')


def test_before_finality_never_promotes_row_even_if_provider_claims_fresh():
    night = night_fixture('2026-10-07T00:28:00+09:00',case='available')
    row = night['value']['observations'][0]
    row['quality_status'] = 'fresh'
    row['raw_payload'].update(session_freshness='fresh', finality_valid=True)
    rows, receipt = evaluate(reseal(night))
    assert not rows and receipt['state'] == 'UNAVAILABLE_BEFORE_FINALITY'


def test_two_current_owners_fail_before_native_dictionary_collapses_them():
    night = night_fixture(case='available')
    extra = deepcopy(night['value']['observations'][0])
    extra['raw_payload']['contract_code'] = 'CONFLICTING'
    night['value']['observations'].append(extra)
    with pytest.raises(ValueError,match='INVALID_CONTRADICTORY_OWNERSHIP'):
        evaluate(reseal(night))


@pytest.mark.parametrize('field', ['original_receipts','observed_at'])
def test_absent_request_provenance_is_plan_gap(field):
    night = night_fixture()
    night.pop(field)
    seed = dict(parent_run_id='test', started_at='2026-09-27T08:00:00+00:00',
        run_acquisitions={'night':digest(night['value'])})
    with pytest.raises(ValueError,match='PLAN_GAP'):
        project_optional_night(night,seed=seed,cutoff=datetime.fromisoformat('2026-09-27T08:02:00+00:00'))


@pytest.mark.parametrize('change', ['hash','run','date','future','clock','finality'])
def test_complete_typed_denial_requires_bound_request_and_temporal_provenance(change):
    night = night_fixture()
    receipt = night['original_receipts'][0]
    if change == 'hash':
        receipt['artifact_sha256'] = 'f'*64
    elif change == 'run':
        receipt['run_id'] = 'another-generation'
    elif change == 'date':
        receipt['request']['params']['basDd'] = '20200101'
    elif change == 'future':
        receipt['received_at'] = '2099-01-01T00:00:00+00:00'
    elif change == 'clock':
        night['value']['telemetry']['expected_reference_date'] = '2020-01-01'
    else:
        night['value']['telemetry']['finality_valid'] = False
    with pytest.raises(ValueError):
        evaluate(reseal(night))


@pytest.mark.parametrize('case', ['empty','stale','available'])
def test_native_market_composition_unrelated_fields_unchanged(case):
    packet, seed, graph = fixture()
    before = project((packet,seed,graph))
    night = night_fixture(case=case)
    seed['run_acquisitions']['night'] = night['value_sha256']
    graph.update(night=night,run_seed_sha256=digest(seed))
    packet.update(night_and_publication_context=night,run_seed_sha256=digest(seed),authority_graph_sha256=digest(graph))
    after = project((packet,seed,graph))
    ctx = after['packet']['market_context']
    assert bool(ctx['night_futures']) == (case == 'available')
    assert after['receipt']['numeric_alias_binding']['status'] == 'PASS'
    assert {k:v for k,v in ctx['coverage'].items() if k != 'night_futures'} == {
        k:v for k,v in before['packet']['market_context']['coverage'].items() if k != 'night_futures'}
    assert [f for f in ctx['fact_catalog'] if not f['fact_type'].startswith('night_futures')] == before['packet']['market_context']['fact_catalog']
    if case != 'available':
        assert ctx['optional_denials']['night_futures']['coverage_resolved']
        assert ctx['optional_denials']['night_futures']['value'] is None


def test_selected_night_ref_retains_true_producer_index():
    night = night_fixture(case='stale')
    night['value']['observations'].extend(night_fixture(case='available')['value']['observations'])
    rows, receipt = evaluate(reseal(night))
    assert rows[0][0] == 1
    assert receipt['producer_observation_count'] == 2
    assert receipt['current_consumer_eligible_count'] == 1


def test_sealed_observation_can_follow_request_start_within_generation_window():
    night = night_fixture()
    observed = datetime.fromisoformat(night['observed_at'])
    start = observed-timedelta(seconds=10)
    for receipt in night['original_receipts']:
        receipt['requested_at'] = start.isoformat()
    seed = dict(parent_run_id='test',started_at=start.isoformat(),
        run_acquisitions={'night':night['value_sha256']})
    rows, receipt = project_optional_night(night,seed=seed,cutoff=observed+timedelta(minutes=2))
    assert not rows and receipt['state'] == 'UNAVAILABLE_NO_CURRENT_FINAL_ROW'
    assert datetime.fromisoformat(receipt['observation_clock']['observation_time_kst']) == observed
    seed['started_at'] = (observed+timedelta(seconds=1)).isoformat()
    with pytest.raises(ValueError,match='night_sealed_observation_clock_mismatch'):
        project_optional_night(night,seed=seed,cutoff=observed+timedelta(minutes=2))
