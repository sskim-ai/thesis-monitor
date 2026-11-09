"""Eight focused offline boundaries; actual source paths are supplied by the task."""
from copy import deepcopy
import importlib.util
import json
import os
from pathlib import Path
import socket
import sqlite3

import pytest
from pydantic import ValidationError
from app.services.dated_economic_research import consume_research, meaningful
from app.services.cross_market_decision_engine_service import DecisionEvidencePacket

ROOT = Path(os.environ['C22D_SOURCE_ROOT'])
HERE = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('dated_runner', HERE / 'scripts/dated_economic_research.py')
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)
TICKERS = ('005930', '000660', 'MU', '047810', 'CORZ')


@pytest.fixture(scope='module')
def sources():
    return {t: json.loads((ROOT / 'maintenance/20261109-c22c/investment-inputs' / (t + '.json')).read_text()) for t in TICKERS}


def view(packet, **kwargs):
    return consume_research(packet, input_sha256=runner.digest(runner.encoded(packet)), **kwargs)


def test_legacy_mismatch_not_a_research_failure(sources):
    packet = sources['005930']
    with pytest.raises(ValidationError) as failure:
        DecisionEvidencePacket.model_validate(packet['technical'])
    locations = [e['loc'] for e in failure.value.errors()]
    assert ('evidence_sha256',) in locations
    result = view(packet)
    assert result['DATED_RESEARCH_EVIDENCE_READY']
    assert 'evidence_sha256' not in result['technical']
    assert all('source_ref' not in row for row in result['technical']['evidence'])
    assert not result['legacy_MODEL_INPUT_VALID'] and not result['STRICT_NATIVE_STAGE_READY']


def test_all_33_originals_and_nine_comparisons_exact(sources):
    counts = []; total = 0
    for packet in sources.values():
        result = view(packet); counts.append(result['economic_driver_count'])
        assert packet['economic']['original_economic_driver_count'] == 0
        for old, new in zip(packet['economic']['evidence'], result['financial_observations'], strict=True):
            assert old['data']['fields'] == new['original_fields']
            assert old['source_sha'] == new['source_sha']
            assert old['ref'] == new['original_ref']
            assert old['lineage_group'] == new['lineage_group']
            if new['role'] == 'QUANTITATIVE_COMPARISON':
                assert new['original_quality']['interpretation_eligible'] is True
                assert new['original_fields']['recurrence_verified'] is False
                assert new['analytic_observation']['delta'] == old['data']['fields']['delta']
                assert not any(new[k] for k in ('verified_mechanism','structural_risk_verified','strict_owner_issued'))
            total += 1
        assert result['financial_numeric_catalog']
    assert counts == [2, 1, 2, 2, 2] and total == 33


def test_period_and_item_specific_cautions(sources):
    mu = view(sources['MU']); corz = view(sources['CORZ'])
    for row in mu['business_change_candidates']:
        fiscal = row['source_fields']['fiscal_comparability']
        assert (fiscal['current_weeks'], fiscal['prior_weeks']) == (53, 52)
        assert fiscal['value_adjustment'] is None
    income = [r for r in corz['financial_observations'] if r['field'] == 'financial.owners_parent_net_income']
    assert len(income) == 2 and {r['original_fields']['period_type'] for r in income} == {'year_to_date_cumulative', 'reported_quarter_duration'}
    assert all(r['role'] == 'DATED_OBSERVATION_ONLY' for r in income)
    hy = view(sources['000660'])
    assert hy['business_change_candidates'][0]['source_fields']['anomaly_cautions']
    kai = {r['field']:r['source_fields']['delta'] for r in view(sources['047810'])['business_change_candidates']}
    assert kai['financial.revenue'] > 0 and kai['financial.operating_income'] < 0


def test_empty_expectations_not_promoted_or_global_block(sources):
    assert not any(meaningful(v) for v in ('{}', '{} ', '', None, [], {'a': '{}'}))
    for packet in sources.values():
        result = view(packet)
        assert result['excluded_placeholders']
        assert not result['market_expectations']['source_evidence']
        assert result['market_expectations']['status'] in {'UNVERIFIED', 'CONDITIONAL'}
        assert result['ECONOMIC_REASONING_INPUT_READY']
        assert not result['STRICT_NATIVE_STAGE_READY']


def test_kr_facts_and_real_us_raw_receipts_no_fabrication(sources):
    assert sum(len(p['prior_approved_valuation_facts']) for p in sources.values()) == 8
    metadata = json.loads((ROOT / 'maintenance/20261106-c16/FINNHUB_RESULT.json').read_text())
    archive = ROOT / 'work/thesis-monitor-vnext-balanced-20261029/data/vnext/c16-20261106/finnhub/archive'
    recovered = {}
    for ticker in ('MU', 'CORZ'):
        facts, contexts, evidence = runner.original_finnhub(archive, metadata, ticker)
        result = view(sources[ticker], extra_valuation=facts, public_context=contexts)
        recovered[ticker] = {v['metric']:v['value'] for v in result['valuation']}
        assert evidence and result['business_mechanism']['source_context']
        assert not any(v['metric'] == 'FY1_EPS' for v in facts)
        assert result['market_expectations']['status'] == 'UNVERIFIED'
        bad = deepcopy(facts); bad[0]['requested_security_id'] = 'OTHER'
        with pytest.raises(ValueError, match='identity_mismatch'):
            view(sources[ticker], extra_valuation=bad)
        bad_metadata = deepcopy(metadata)
        row = next(r for r in bad_metadata['rows'] if r['ticker'] == ticker)
        row['metrics'][0]['raw_sha256'] = '0' * 64
        with pytest.raises(ValueError, match='original_snapshot_mismatch:raw'):
            runner.original_finnhub(archive, bad_metadata, ticker)
    assert recovered == {'MU': {'PER':9.1001, 'PBR':7.8202, 'FORWARD_PE':4.94962}, 'CORZ':{'PBR':0.37506}}
    for ticker in ('005930','000660','047810'):
        result = view(sources[ticker])
        assert [v['original_fact'] for v in result['valuation']] == sources[ticker]['prior_approved_valuation_facts']


def test_no_network_db_or_legacy_stage_and_strict_code_unchanged(sources, monkeypatch):
    def deny(*args, **kwargs):
        raise AssertionError('unexpected side effect')
    monkeypatch.setattr(socket, 'socket', deny)
    monkeypatch.setattr(sqlite3, 'connect', deny)
    for packet in sources.values():
        result = view(packet)
        assert result['NO_SEND'] and result['model_executed'] is False
        assert result['no_current_price_grant']
    preflight = json.loads((ROOT / 'maintenance/20261109-c22d-v2/CONTRACT_PREFLIGHT.json').read_text())
    for record in preflight['source_code']:
        current = HERE / 'app/services' / Path(record['path']).name
        assert runner.digest(current.read_bytes()) == record['sha256']


def test_sourced_context_and_shared_forecast_not_independent(sources):
    packet = sources['047810']; original = packet['prior_approved_valuation_facts']
    assert any(v['metric'] == 'FY1_EPS' for v in original)
    result = view(packet, public_context=[dict(ticker='047810', category='expectations', content='{}', source_ref='not-valid')])
    interaction = result['expectation_valuation_interaction']
    assert not result['market_expectations']['source_evidence']
    assert result['market_expectations']['analyst_forecast_references']
    assert interaction.get('classification') != 'INDEPENDENT'
    for key in ('business_mechanism', 'structural_risk'):
        assert result[key]
    assert not {'Overall','NewBuyer','Holder','stance'}.intersection(result)
    assert all(q['evidence_refs'] for q in result['business_mechanism']['analytic_questions'])


def test_native_numbers_nulls_quality_and_sr_unchanged(sources):
    for packet in sources.values():
        original = deepcopy(packet); result = view(packet)
        native = packet['technical']['technical_context_quality']['provider_native']
        assert result['technical']['technical_context_quality']['provider_native'] == native
        assert result['dated_price_structure'] == packet['dated_price_structure']
        assert native['current_price_qualified'] is False
        assert all(len(p['indicators']) == 38 for p in native['periods'].values() if p['status'] == 'AVAILABLE')
        assert result['technical'].get('data_quality_cautions') == packet['technical'].get('data_quality_cautions')
        assert packet == original
