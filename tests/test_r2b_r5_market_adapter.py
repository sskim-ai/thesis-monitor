from copy import deepcopy
import socket

import pytest
from sqlmodel import Session

from app.services.unified_snapshot_contract import digest
from scripts.r2b_r5_market_adapter import (
    PUBLICATIONS, contract_inventory, numeric_alias_audit, project_sealed_market_context,
    registered_projection,
)


def fixture(market='us'):
    publications = {'class-c/' + role + '.json': dict(source_sha256='a'*64,
        projection=dict(contract='unified-class-c-owner-projection-v1', eligible=True, values=[]))
        for role in PUBLICATIONS}
    if market == 'us':
        value = dict(observations=[dict(series_code='SPY', observed_at='2026-09-25T00:00:00Z',
            value=100, change_pct=1, quality_status='fresh')])
    else:
        value = dict(indices=[dict(symbol='KOSPI', label='KOSPI', close=100, return_pct=1,
                source_ref='source:index')], sectors=[dict(sector='Industrial', taxonomy='test',
                metric_role='actual_sector_breadth', return_pct=1.5, listed_count=10,
                source_ref='source:sector')],
            breadth=dict(eligible_count=10, advance_count=6, decline_count=3, unchanged_count=1,
                advance_ratio=2/3, ad_ratio=2, median_return_pct=None, equal_weight_return_pct=None,
                positive_return_pct=60, negative_return_pct=30, total_trading_volume=None,
                total_trading_value=None), breadth_by_scope=[])
    component = dict(value=value, value_sha256=digest(value), provider='kiwoom_rest' if market=='kr' else 'ohlcv_analyst',
        session='2026-09-23' if market=='kr' else '2026-09-25', original_source_time='2026-09-27T08:01:00Z',
        eligibility=dict(contract='test-owner'), source=dict(role='kr_local_indices_sectors_breadth' if market=='kr' else 'us_market_prices',
            artifact_sha256='b'*64))
    source = dict(component=component, run_id='test', attempt_id='test:'+market, cutoff='2026-09-27T08:02:00Z')
    versions = {name:'a'*64 for name in publications}
    denials = dict(kr_market_investor_flows=dict(status='OPTIONAL_UNAVAILABLE', value=None))
    night = dict(value={'observations': []}, value_sha256=digest({'observations': []}))
    seed = dict(parent_run_id='test', attempts={market:'test:'+market}, attempt_hashes={market:digest(source)},
        started_at='2026-09-27T08:00:00Z', optional_denial_set_sha256=digest(denials),
        class_c_version_set_sha256=digest(versions), run_acquisitions=dict(night=night['value_sha256']),
        proof_mode='AD_HOC_LIVE_SOURCE_PROOF')
    graph = dict(run_seed_sha256=digest(seed), markets={market:source}, class_c=versions,
        publication_context=publications, optional_denials=denials, night=night)
    packet = dict(market=market, run_seed_sha256=digest(seed), authority_graph_sha256=digest(graph),
        market_sources=deepcopy(source), publication_context=publications, class_c_versions=versions,
        optional_denials=denials, night_and_publication_context=night)
    return packet, seed, graph


def project(parts):
    packet, seed, graph = parts
    return project_sealed_market_context(packet, seed, graph, expected_authority_sha256=digest(graph))


@pytest.mark.parametrize('market', ['us', 'kr'])
def test_exact_consumer_deterministic_without_network_db_or_live_cache(monkeypatch, market):
    def deny(*args, **kwargs):
        raise AssertionError('live dependency forbidden')
    monkeypatch.setattr(socket, 'create_connection', deny)
    monkeypatch.setattr(Session, 'exec', deny)
    from app.services import ai_review_service as live
    monkeypatch.setattr(live, 'load_current_cross_section', deny)
    monkeypatch.setattr(live, 'load_structured_market_context', deny)
    parts = fixture(market)
    before = deepcopy(parts)
    first, second = project(parts), project(parts)
    assert first == second and parts == before
    assert first['context']['parity_status'] == 'PASS'
    assert first['receipt']['session']['status'] == 'PASS'
    assert first['receipt']['numeric_boundary']['status'] == 'PASS'
    assert first['receipt']['numeric_alias_binding']['status'] == 'PASS'
    assert first['packet']['market_context']['optional_denials']['kr_market_investor_flows']['value'] is None


@pytest.mark.parametrize('field', ['market', 'run_seed_sha256', 'market_sources'])
def test_changed_source_authority_is_not_repaired(field):
    parts = fixture()
    if field == 'market_sources':
        parts[0][field]['component']['value']['observations'][0]['value'] = 999
    else:
        parts[0][field] = 'wrong'
    with pytest.raises((ValueError, KeyError)):
        project(parts)


@pytest.mark.parametrize('market', ['us', 'kr'])
def test_unqualified_session_cannot_be_relabelled(market):
    packet, seed, graph = fixture(market)
    source = graph['markets'][market]
    source['component']['session'] = '2026-09-28'
    seed['attempt_hashes'][market] = digest(source)
    graph['run_seed_sha256'] = digest(seed)
    packet.update(market_sources=deepcopy(source), run_seed_sha256=digest(seed), authority_graph_sha256=digest(graph))
    with pytest.raises(ValueError, match='completed_session'):
        project((packet, seed, graph))


def test_missing_required_cross_section_is_not_empty_context():
    packet, seed, graph = fixture('kr')
    source = graph['markets']['kr']
    source['component']['value']['indices'] = []
    source['component']['value_sha256'] = digest(source['component']['value'])
    seed['attempt_hashes']['kr'] = digest(source)
    graph['run_seed_sha256'] = digest(seed)
    packet.update(market_sources=deepcopy(source), run_seed_sha256=digest(seed), authority_graph_sha256=digest(graph))
    with pytest.raises(ValueError, match='mandatory_market_source_missing'):
        project((packet, seed, graph))


def test_alias_number_must_bind_to_canonical_registry():
    result = project(fixture('kr'))
    result['context']['facts']['source:index']['close'] += 1
    assert numeric_alias_audit(result['context'], result['packet']['market_context'])['status'] == 'FAIL'


def test_consumer_inventory_has_no_live_or_new_policy_owner():
    inventory = contract_inventory()
    assert inventory['historical_values_reused'] is False
    assert all(r['source_ref_requirement'] and r['coverage_requirement'] for r in inventory['rows'])
    assert {'market_context.session', 'market_context.numeric_registry', 'market_context.coverage'} <= {
        r['path'] for r in inventory['rows'] if r['mandatory']}


def test_unregistered_optional_observation_number_is_explicitly_withheld():
    facts=[dict(fact_id='market:breakeven_inflation:T10YIE',fact_type='market_breakeven_inflation',
        as_of_date='2026-09-25',fields=dict(level_pct=2.3,change_bp=0,previous_level_pct=2.3))]
    projected,denied=registered_projection(facts)
    assert facts[0]['fields']['previous_level_pct']==2.3
    assert projected[0]['fields']==dict(level_pct=2.3,change_bp=0)
    assert denied[0]['model_visible'] is False and denied[0]['value']==2.3


def test_unregistered_alias_cannot_hide_behind_registered_siblings():
    result=project(fixture('kr'))
    result['context']['facts']['source:index']['invented_number']=10
    assert numeric_alias_audit(result['context'],result['packet']['market_context'])['status']=='FAIL'
