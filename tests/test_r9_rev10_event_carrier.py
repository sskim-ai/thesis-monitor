import asyncio
from copy import deepcopy

import pytest

from app.services.accepted_decision_v2_service import render_accepted_v2_production
from app.services.cross_market_decision_engine_service import DecisionEvidencePacket
from app.services.current_fresh_valuation import CurrentValuationView
from app.services.detailed_stock_message_service import build_unknown_plan, final_detailed_audit
from scripts.m12ds_r4_offline_capture import capture_payload
from scripts.r2b_r9_full_fresh_requalification import load_stock_inputs, prepare_fresh_subject
from tests.rev9_source_fixtures import write_descriptor
from tests.rev10_source_fixtures import event_inputs, carrier_owner
from tests.test_r9_rev9_context_only import unknown_decision


@pytest.mark.parametrize('persisted', [False, True])
def test_event_current_only_unknown_final_boundary(tmp_path, persisted):
    inputs = event_inputs(tmp_path, persisted=persisted)
    original = deepcopy(inputs['event_inputs'])
    result = prepare_fresh_subject(inputs, execution_generation_id='synthetic-rev10')
    stock = result['stock']
    assert stock['status'] == 'PASS' and result['prepared']['mode'] == 'UNKNOWN_LIMIT'
    assert stock['quality_view']['fact'] is None
    assert len(stock['event_fact_refs']) == 1
    receipt = stock['event_view']['receipt']
    assert receipt['acquisition_class'] == ('PERSISTED_SOURCE_RECHECK' if persisted else 'FRESH_CURRENT_RUN')
    assert (receipt['original_run_id'] != receipt['current_run_id']) is persisted
    assert all('OVERALL_DIRECTION' not in r['allowed_uses'] for r in result['authority']['authority']['authority_records'])
    descriptor = write_descriptor(tmp_path, inputs)
    loaded = load_stock_inputs(tmp_path, descriptor, inputs['technical_inputs']['plan'])
    assert prepare_fresh_subject(loaded, execution_generation_id='synthetic-rev10') == result
    plan = build_unknown_plan(source_stock=stock, source_authority=result['authority'],
        local_seed=inputs['technical_inputs']['local_seed'], decision=unknown_decision(result['prepared']),
        execution_generation_id='synthetic-rev10', valuation=CurrentValuationView.model_validate(stock['valuation_view']))
    ep = DecisionEvidencePacket.model_validate(stock['evidence_packet'])
    rendered = render_accepted_v2_production(ep, plan)
    captured = asyncio.run(capture_payload(dict(type='thesis_assessment', ticker='CORZ', text=rendered.text, use_llm=False)))
    assert captured['prepared_text'] == rendered.text
    assert final_detailed_audit(captured['prepared_text'], ep, plan)['status'] == 'PASS'
    assert captured['production_sends'] == captured['network_requests'] == 0
    assert inputs['event_inputs'] == original


@pytest.mark.parametrize('change', ['run', 'market', 'start', 'availability', 'raw', 'classification'])
def test_event_carrier_binding_failure(tmp_path, change):
    inputs = event_inputs(tmp_path)
    c = inputs['event_inputs']
    if change == 'run':
        c['window']['run_id'] = 'wrong'
    elif change == 'market':
        c['source']['read']['market'] = 'kr'
    elif change == 'start':
        c['window']['collection_started_at'] = '2026-09-26T00:00:06+00:00'
    elif change == 'availability':
        c['window']['source_query_cutoff'] = c['window']['collection_started_at']
        c['window']['business_availability_cutoff'] = c['window']['collection_started_at']
    elif change == 'raw':
        c['source']['raw_response_b64'] = 'e30='
    else:
        c['acquisition_class'] = 'PERSISTED_SOURCE_RECHECK'
    with pytest.raises(ValueError):
        carrier_owner(inputs)


def test_source_publication_after_query_not_promoted(tmp_path):
    result = carrier_owner(event_inputs(tmp_path, future=True))
    assert result['facts'] == [] and not result['receipt']['selected']


def test_event_descriptor_escape_denied(tmp_path):
    inputs = event_inputs(tmp_path)
    descriptor = write_descriptor(tmp_path, inputs)
    descriptor['event_carrier']['path'] = '../outside.json'
    with pytest.raises(ValueError, match='relative_artifact'):
        load_stock_inputs(tmp_path, descriptor, inputs['technical_inputs']['plan'])
