from copy import deepcopy
import json

import pytest

from app.services.fresh_financial_stock_owner import assemble_fresh_stock
from app.services.unified_snapshot_contract import digest
from app.services.unified_stock_acquisition import UNIVERSE
from scripts.fresh_source_only_export import (
    EXCLUDED, project_cohort, reject_review_contamination, source_only_market,
)
from scripts.m12da_source_use_contract import canonical_sha256
from scripts.r2b_sealed_blind_preflight import source_only_stock
from tests.rev10_cohort_fixtures import stocks, RUN


@pytest.fixture(scope='module')
def cohort(tmp_path_factory):
    inputs = stocks(tmp_path_factory.mktemp('fresh-only'))
    values = {t: assemble_fresh_stock(**i) for t, i in inputs.items()}
    authority = dict(contract='fixture-source-authority', authority_records=[])
    authority['authority_manifest_sha256'] = canonical_sha256(authority)
    packets = {m: dict(market=m, stocks={t: values[t] for t in ts},
        market_sources=dict(run_id=RUN, component=dict(value={'observations': []})),
        optional_denials=['UNAVAILABLE_NOT_ZERO'], publication_context={},
        night_and_publication_context={'night': {'status': 'UNAVAILABLE'}})
        for m, ts in UNIVERSE.items()}
    return dict(packets=packets, authority_graph=dict(stocks={t: {'authority': deepcopy(authority)} for t in values}))


def item(cohort, ticker='IBM'):
    return next(p['stocks'][ticker] for p in cohort['packets'].values() if ticker in p['stocks'])


@pytest.mark.parametrize('ticker', [t for ts in UNIVERSE.values() for t in ts])
def test_all22_fresh_shapes_without_legacy_fields(cohort, ticker):
    stock = item(cohort, ticker)
    original = digest(stock)
    assert 'financial_bindings' not in stock
    output = source_only_stock(stock, cohort['authority_graph']['stocks'][ticker])
    assert 'financial_bindings' not in json.dumps(output)
    assert output['financial']['selected_financial_owner'] == stock['selected_financial_owner']
    assert output['financial']['financial_source_graph'] == stock['financial_source_graph']
    assert output['facts'] == stock['packet']['stocks'][0]['fact_catalog']
    assert len(output['facts']) == len({f['fact_id'] for f in output['facts']})
    assert output['quality']['quality_view'] == stock['quality_view']
    assert output['valuation']['metrics'] == stock['valuation_view']['metrics']
    assert output['price']['completed_session_current_price'] == stock['completed_session_current_price']
    assert output['technical']['technical_context'] == stock['packet']['stocks'][0]['technical_context']
    assert output['flow_positioning'] == stock['packet']['stocks'][0]['price_and_positioning']
    assert output['financial']['comparison_denials'] == stock['comparison_denials']
    assert output['financial']['financial_state'] == stock['financial_state']
    if stock['selected_financial_owner']['bridge_receipt']:
        assert output['financial']['selected_source_fields'] is None
        assert output['financial']['direct_projection_role'] == 'UNSELECTED_DIRECT_OWNER'
        assert output['financial']['selected_financial_owner']['selected_fact_ids']
        assert output['quality']['quality_view']['receipt']['state'] == stock['quality_view']['receipt']['state']
    else:
        assert output['financial']['selected_source_fields']['fields'] == stock['projection']['fields']
        assert output['financial']['direct_projection_role'] == 'SELECTED_DIRECT_OWNER'
    if 'event_view' in stock:
        assert output['events']['event_view'] == stock['event_view']
    assert not {'ownership', 'evidence_packet', 'packet', 'knowledge_routing', 'thesis'} & output.keys()
    reject_review_contamination(output)
    assert digest(stock) == original
    output['facts'].clear()
    assert digest(stock) == original


def test_whole_exact22_plus_two_markets_no_legacy(cohort):
    output = project_cohort(cohort, generation_id=RUN, whole_source_sha256=digest(cohort))
    assert output['audit']['stock_count'] == 22
    assert output['audit']['market_count'] == 2
    for m, packet in cohort['packets'].items():
        assert output['markets'][m]['market_sources'] == packet['market_sources']
        assert output['markets'][m]['optional_denials'] == packet['optional_denials']
        assert 'stocks' not in output['markets'][m]


@pytest.mark.parametrize('damage', ['missing_owner', 'outside_graph', 'duplicate_fact', 'missing_fact',
                                   'changed_node', 'changed_envelope', 'changed_projection', 'generation'])
def test_financial_binding_fail_closed(cohort, damage):
    stock = deepcopy(item(cohort))
    if damage == 'missing_owner':
        del stock['selected_financial_owner']
    elif damage == 'outside_graph':
        del stock['source_graph'][next(iter(stock['financial_source_graph']))]
    elif damage in {'duplicate_fact', 'missing_fact'}:
        facts = stock['packet']['stocks'][0]['fact_catalog']
        if damage == 'duplicate_fact':
            facts.append(deepcopy(facts[-1]))
        else:
            ids = stock['selected_financial_owner']['selected_fact_ids']
            facts[:] = [f for f in facts if f['fact_id'] != ids[0]]
        stock['packet_sha256'] = stock['diagnostic_packet_sha256'] = digest(stock['packet'])
    elif damage == 'changed_node':
        stock['financial_source_graph'][next(iter(stock['financial_source_graph']))]['fact_sha256'] = '0'*64
    elif damage == 'changed_envelope':
        stock['selected_financial_owner']['selected_fact_ids'] = []
    elif damage == 'changed_projection':
        stock['projection']['fields'] = []
    else:
        stock['fresh_run_id'] = 'not-this-generation'
    with pytest.raises(ValueError, match='source_only_'):
        source_only_stock(stock, cohort['authority_graph']['stocks']['IBM'])


def test_qualified_valuation_needs_receipt(cohort):
    stock = deepcopy(item(cohort))
    metric = next(m for m in stock['valuation_view']['metrics'] if m['status'] == 'QUALIFIED')
    del metric['native_snapshot']['source_receipt_sha256']
    with pytest.raises(ValueError):
        source_only_stock(stock, cohort['authority_graph']['stocks']['IBM'])


@pytest.mark.parametrize('key', sorted(EXCLUDED | {'overall_direction', 'buy_sell_balance', 'rendered_message'}))
@pytest.mark.parametrize('serialized', [False, True])
def test_downstream_injection_any_depth_rejected(cohort, key, serialized):
    stock = deepcopy(item(cohort))
    payload = {key: 'not-source-evidence'}
    stock['injected'] = {'deep': [json.dumps(payload) if serialized else payload]}
    with pytest.raises(ValueError, match='forbidden'):
        source_only_stock(stock, cohort['authority_graph']['stocks']['IBM'])


def test_market_output_is_rejected(cohort):
    packet = deepcopy(cohort['packets']['us'])
    packet['market_sources']['model_output'] = 'excluded'
    with pytest.raises(ValueError, match='forbidden'):
        source_only_market(packet, generation_id=RUN)


@pytest.mark.parametrize('damage', ['roster', 'source_hash', 'market_generation', 'stock_generation'])
def test_whole_identity_and_roster_fail_closed(cohort, damage):
    whole = deepcopy(cohort)
    if damage == 'roster':
        del whole['packets']['us']['stocks']['IBM']
    elif damage == 'market_generation':
        whole['packets']['us']['market_sources']['run_id'] = 'other'
    elif damage == 'stock_generation':
        whole['packets']['us']['stocks']['IBM']['fresh_run_id'] = 'other'
    with pytest.raises(ValueError, match='source_only_'):
        project_cohort(whole, generation_id=RUN,
                      whole_source_sha256='0'*64 if damage == 'source_hash' else digest(whole))
