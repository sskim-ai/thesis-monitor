"""Original engine -> real KR/US Source -> canonical B -> final B2 wire input.

Bars, financial responses and accepted economics are synthetic. Source owners,
native projections, B bindings, B2 request builders and wire rendering are real.
No financial/model network request is made and no economic result is asserted.
"""
from copy import deepcopy
import json
from types import SimpleNamespace

import pytest

from app.services import canonical_monitoring_domain as domain
from app.services import new_buyer_request_owner as b2
from app.services.canonical_monitoring_input import NATIVE_TECHNICAL_PROMPT
from app.services.completed_price_state import bind_source
from app.services.cross_market_decision_engine_service import DecisionEvidencePacket
from app.services.direction_timing_ownership_service import (
    build_owned_evidence_packet, technical_feature_inventory,
)
from app.services.fresh_financial_stock_owner import assemble_fresh_stock
from app.services.production_model_transport import render_prompt
from app.services.production_monitoring_session import ProductionMonitoringSession
from app.services.unified_snapshot_contract import digest
from scripts.m12cn_policy_contract import build_subject_catalog
from scripts.m12cq_two_pass_contract import build_pass_a_subject_context
from tests import test_c50_chart_statement as chart_fixture
from tests.test_c58_native_model_delivery import b2_with_native
from tests.test_c58_native_source import (
    forbid_tm_indicators, native_source_inputs, refresh_native_source,
)
from tests.test_c56_source_numeric import no_external as no_external


def captured_b_request(root, monkeypatch, case):
    """Exercise real B preparation/capture with explicit synthetic upstream economics.

    This is input wiring, not external dispatch or operational authorization.
    The existing fixture owns source-use inputs; only its accepted economic axis
    capability and the one-subject batch are supplied as synthetic session state.
    """
    fixture, ticker, source, _, _, _ = case
    recorded = {}

    def record(view, catalog, subject, chain, classification, capability):
        recorded.update(catalog=catalog, subject=subject, chain=chain,
                        classification=classification, capability=capability)
        return domain.pre.b_input(view, catalog, subject, chain, classification, capability)

    with monkeypatch.context() as fixture_patch:
        fixture_patch.setattr(chart_fixture, 'b_input', record)
        expected_context, _, _ = chart_fixture.bound_b_input(case)
    session = object.__new__(ProductionMonitoringSession)
    session.__dict__.update(market=fixture.market, gen=fixture.gen, source_gen=fixture.source_gen,
        sealed=root / 'sealed', requests=root / 'sealed' / 'requests',
        _frozen_cohort=None, _manual_source_owner=None, _native_owner_parent=None,
        limitation_subjects=frozenset(), source={'valuation_contexts': {ticker: None}},
        prepared={ticker: dict(mode='EVIDENCE_BASED', view=source)},
        cores={ticker: dict(effects={})}, arows={ticker: recorded['classification']},
        catalogs={ticker: recorded['catalog']}, subjects={ticker: recorded['subject']},
        chains={ticker: recorded['chain']}, caps={}, ranges={}, entries={}, bctx={},
        stage_manifests={}, captured={})
    session.batch_topology = lambda: [dict(market=fixture.market, batch=1, subjects=[ticker])]
    with monkeypatch.context() as economics:
        economics.setattr(domain.c.policy, 'axis_capability',
                          lambda *args: deepcopy(recorded['capability']))
        requests = session.before_b()
    assert len(requests) == 1
    session.captured['B'] = requests
    session.verify_model_build('B', requests[0])
    frozen = json.loads((session.sealed / 'pass-b-request-freeze.json').read_bytes())
    assert frozen == dict(generation_id=session.gen, requests=requests)
    assert session.stage_manifests['pass-b'] == digest(frozen)
    payload = requests[0]['payload']
    context = payload['input'][ticker]
    assert NATIVE_TECHNICAL_PROMPT in payload['prompt']
    assert context['native_technical_context'] == expected_context['native_technical_context']
    return context, payload


@pytest.mark.parametrize('market,ticker', [('kr', '005930'), ('us', 'CORZ')])
def test_original_source_values_reach_both_actual_model_wire_inputs(tmp_path, monkeypatch, market, ticker):
    inputs = native_source_inputs(tmp_path, ticker)
    forbid_tm_indicators(monkeypatch)
    refresh_native_source(inputs)
    original = deepcopy(inputs)
    source = assemble_fresh_stock(**inputs)
    assert source['status'] == 'PASS' and not source['mandatory_missing']
    stock = source['packet']['stocks'][0]
    packet = DecisionEvidencePacket.model_validate(source['evidence_packet'])
    owned = build_owned_evidence_packet(packet, stock=stock)
    inventory = technical_feature_inventory(owned)
    assert all(inventory[field] for field in ('rsi', 'macd', 'bollinger', 'moving_average', 'volume'))
    native_refs = {row.ref_id for row in packet.evidence if row.ref_id.startswith('native:')}
    assert native_refs and native_refs <= set(owned.timing_refs)
    assert native_refs.isdisjoint(owned.core_refs)

    session = SimpleNamespace(market=market, source_gen=source['fresh_run_id'],
                              gen='c58-offline-model-' + ticker, arows={}, bctx={})
    context, b_payload = captured_b_request(tmp_path / 'model-build', monkeypatch,
        (session, ticker, source, stock, packet, owned))
    native = context['native_technical_context']
    before = deepcopy(context)
    for timeframe, period in stock['technical_context']['native_view']['periods'].items():
        assert native['periods'][timeframe]['indicators'] == period['indicators']
        assert native['periods'][timeframe]['as_of'] == period['completed_as_of']
        assert native['periods'][timeframe]['calculation_row_count'] == period['returned_count']
        assert native['periods'][timeframe]['completed_row_count'] == period['completed_count']
    b_wire = json.loads(render_prompt(b_payload, 'B').decode().rsplit('\nFROZEN_CONTEXT:\n', 1)[1])[ticker]
    request = b2_with_native(context, security_id=source['valuation_view']['security_id'])
    payload = b2.provider_payload(request, expected_request_sha256=request['request_sha256'])
    b2_wire = json.loads(render_prompt(payload, 'B2').decode().rsplit('\nFROZEN_CONTEXT:\n', 1)[1])
    assert b_wire['native_technical_context'] == b2_wire['native_technical_context'] == native
    assert b2_wire['native_technical_context']['periods']['monthly']['indicators']['MA288'] is None
    assert b2_wire['native_technical_context']['periods']['monthly']['indicators']['MACD_OSC_320_640_9'] is not None

    ownership = dict(ticker=ticker, core_ref_ids=sorted(owned.core_refs),
                     timing_ref_ids=sorted(owned.timing_refs))
    view = dict(evidence_packets=[packet.model_dump(mode='json')], evidence_ownership=[ownership])
    catalog = build_subject_catalog(context=view, ticker=ticker, atomic_claims=[])
    pass_a = build_pass_a_subject_context(context=view, ticker=ticker, catalog=catalog)
    assert 'native:' not in json.dumps(pass_a)
    assert context == before and inputs == original


def test_existing_native_price_rebind_never_reverts_when_a_sidecar_is_missing(tmp_path, monkeypatch):
    inputs = native_source_inputs(tmp_path, 'CORZ')
    technical = inputs['technical_inputs']
    technical['receipts']['adjusted_daily'].pop('native_indicators')
    forbid_tm_indicators(monkeypatch)
    with pytest.raises(ValueError, match='native_indicator_artifact_required'):
        bind_source(technical, source=technical['completed_price_source'], artifacts={},
                    security=inputs['financial_inputs']['plan']['security'])
