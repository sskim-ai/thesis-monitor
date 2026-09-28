import asyncio
from copy import deepcopy

import pytest

from app.services.canonical_business_quality_owner import derive_fresh
from app.services.bounded_financial_projection import comparison_applicability
from app.services.cross_market_decision_engine_service import DecisionEvidencePacket
from app.services.current_fresh_valuation import CurrentValuationView
from app.services.detailed_stock_message_service import build_unknown_plan, final_detailed_audit
from app.services.accepted_decision_v2_service import render_accepted_v2_production
from app.services.unified_snapshot_contract import digest
from scripts.m12ds_r4_offline_capture import capture_payload
from scripts.r2b_r9_full_fresh_requalification import prepare_fresh_subject
from tests.rev8_source_fixtures import fresh_inputs


def unknown_decision(prepared):
    return dict(decision_mode='UNKNOWN_LIMIT', overall_direction='OBSERVE', new_buyer='OBSERVE', holder='OBSERVE',
        directional_buy_score=None, directional_sell_score=None, confidence=None,
        limitation_reason='ZERO_AUTHORIZED_DIRECTIONAL_EVIDENCE', unknowns=list(prepared['recovery']),
        required_next_evidence=list(prepared['recovery']))


@pytest.mark.parametrize('ticker', ['CORZ', 'IBM'])
def test_current_only_actual_sender_boundary(tmp_path, ticker):
    inputs = fresh_inputs(tmp_path, ticker, current_only=True)
    result = prepare_fresh_subject(inputs, execution_generation_id='offline-rev9')
    source, prepared = result['stock'], result['prepared']
    assert source['quality_view']['receipt']['applicability'] == 'QUALITY_NOT_APPLICABLE_NO_DIRECTIONAL_COMPARISON'
    assert source['quality_view']['fact'] is None
    assert all(f['fact_type'] != 'financial_quality' for f in source['packet']['stocks'][0]['fact_catalog'])
    assert all('OVERALL_DIRECTION' not in r['allowed_uses'] for r in prepared['initial_chain']['authority']['authority_records'])
    plan = build_unknown_plan(source_stock=source, source_authority=result['authority'],
        local_seed=inputs['technical_inputs']['local_seed'], decision=unknown_decision(prepared),
        execution_generation_id='offline-rev9', valuation=CurrentValuationView.model_validate(source['valuation_view']))
    packet = DecisionEvidencePacket.model_validate(source['evidence_packet'])
    rendered = render_accepted_v2_production(packet, plan)
    assert rendered.validation.valid
    capture = asyncio.run(capture_payload(dict(type='thesis_assessment', ticker=ticker,
        text=rendered.text, use_llm=False), max_chars=350))
    assert capture['prepared_text'] == rendered.text
    assert final_detailed_audit(capture['prepared_text'], packet, plan)['status'] == 'PASS'
    assert capture['production_sends'] == capture['network_requests'] == 0
    assert 'Valuation' in rendered.text and '신규 매수자: OBSERVE' in rendered.text
    assert not any(token in rendered.text for token in ('BUY', 'SELL', 'HOLD', 'REDUCE', '50:50'))
    assert all(row.text in '\n'.join(capture['chunks']) for row in plan.rows)


@pytest.mark.parametrize('corruption', ['lineage', 'prior_invalid', 'owner_missing', 'empty', 'comparison_lost'])
def test_absence_never_hides_owner_error(tmp_path, corruption):
    inputs = fresh_inputs(tmp_path, 'CORZ', current_only=corruption != 'comparison_lost')
    result = prepare_fresh_subject(inputs, execution_generation_id='offline-rev9')
    projection = deepcopy(result['stock']['projection'])
    if corruption == 'lineage':
        projection['fields'][0]['quality_errors'] = ['LINEAGE_UNRESOLVED']
        projection['fields'][0]['context_eligible'] = False
    elif corruption == 'prior_invalid':
        prior = deepcopy(projection['fields'][0])
        prior['current_prior_role'] = 'comparative'
        prior['quality_errors'] = ['currency_mismatch']
        projection['fields'].append(prior)
    elif corruption == 'owner_missing':
        projection['quality_bundles'] = []
    elif corruption == 'empty':
        projection['fields'] = []
    projection['comparison_applicability'] = comparison_applicability(projection)
    with pytest.raises(ValueError, match='EXPECTED_BUSINESS_QUALITY_OWNER_OUTPUT_MISSING'):
        derive_fresh(projection=projection, facts=[], ticker='CORZ', security_id='security-CORZ', run_id='run')


def test_failed_transport_never_becomes_unknown(tmp_path):
    inputs = fresh_inputs(tmp_path, 'CORZ', current_only=True)
    inputs['financial_inputs']['receipts'][0]['failure_class'] = 'timeout'
    with pytest.raises(ValueError):
        prepare_fresh_subject(inputs, execution_generation_id='offline-rev9')


def test_absence_receipt_tamper_not_accepted(tmp_path):
    inputs = fresh_inputs(tmp_path, 'CORZ', current_only=True)
    source = prepare_fresh_subject(inputs, execution_generation_id='offline-rev9')['stock']
    projection = source['projection']
    projection['comparison_applicability']['current_field_hashes'] = []
    projection['comparison_applicability']['receipt_sha256'] = digest(projection['comparison_applicability'])
    with pytest.raises(ValueError, match='comparison_absence_owner_missing'):
        derive_fresh(projection=projection, facts=[], ticker='CORZ', security_id='security-CORZ', run_id='run')
