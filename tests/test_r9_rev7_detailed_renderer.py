from copy import deepcopy

import pytest

from app.services.accepted_decision_v2_service import render_accepted_v2_production
from app.services.accepted_calibration_message_service import AcceptedDetailedCalibrationPlan
from app.services.current_fresh_valuation import CurrentMultiple, CurrentValuationView
from app.services.detailed_stock_message_service import (
    build_detailed_plan, detailed_render, final_detailed_audit, RowSelection, DetailedStockMessagePlan,
)
from app.services.numeric_semantic_registry import build_numeric_registry
from app.services.unified_snapshot_contract import digest
from tests.test_accepted_decision_v2_runtime import _packet
from tests.test_m12ds_r4_r1_production_calibration import plan_for


@pytest.fixture
def inputs():
    ep = _packet()
    accepted = plan_for(ep)
    quote = dict(contract='current-price-context-v1', current_price=100, currency='USD',
                 as_of_date=str(ep.assessment_date), price_basis='close')
    value = CurrentValuationView(ticker=ep.ticker, security_id='fixture-security', run_id='source-one',
        currency='USD', price=100, price_session=ep.assessment_date, price_basis='close',
        price_context_sha256=digest(quote), security_sha256='a'*64, financial_projection_sha256='b'*64,
        owner_output_sha256='c'*64, metrics=tuple(CurrentMultiple(metric=m, status='UNAVAILABLE',
            numerator=100, source_method='fixture', input_hashes=('a'*64,), denial_reason='UNAVAILABLE')
            for m in ('PER', 'PBR', 'fPER')))
    fact = dict(fact_id='price:current', fact_type='price', ticker=ep.ticker,
                as_of_date=str(ep.assessment_date), fields={'current_price':100, 'currency':'USD'})
    stock = dict(ticker=ep.ticker, current_price_context=quote,
                 fact_catalog=[fact], numeric_registry=build_numeric_registry([fact]))
    packet = dict(stocks=[stock], source_time_domains={'run_id':'source-one'})
    source = dict(contract='fresh-financial-stock-owner-v1', status='PASS', ticker=ep.ticker,
        fresh_run_id='source-one', packet=packet, packet_sha256=digest(packet),
        evidence_packet=ep.model_dump(mode='json'), valuation_view=value.model_dump(mode='json'),
        source_graph={fact['fact_id']:dict(fact_sha256=digest(fact))})
    core = dict(atomic_claims=[dict(claim_ref='claim:one', parent_source_refs=[ep.evidence[0].ref_id],
        claim=dict(text='Business evidence supports the current interpretation.', logical_condition=None))],
        effects={'claim:one':{'effect':'DIRECTIONAL_POSITIVE'}})
    core['binding_sha256'] = digest({'atomic':core['atomic_claims'], 'effects':core['effects']})
    a = {'ticker':ep.ticker, 'classification':'fixture'}
    provenance = dict(core_sha256=digest(core), pass_a_sha256=digest(a), pass_b_sha256=digest(accepted.decision),
        pass_b_input_sha256='d'*64, fresh_stock_sha256=digest(source))
    receipt = {**accepted.acceptance, 'stage_provenance_sha256':digest(provenance)}
    accepted = AcceptedDetailedCalibrationPlan(**{**accepted.model_dump(mode='json'),
        'stage_provenance':provenance, 'acceptance':receipt, 'acceptance_sha256':digest(receipt)})
    return dict(packet=ep, accepted=accepted, source_stock=source, core=core, pass_a=a, valuation=value,
        selections=[dict(section='price', owner='source_numeric', ref='price:current', field_path='fields.current_price'),
                    dict(section='business', owner='core_claim', ref='claim:one')])


def test_detailed_acceptance_and_production_entrypoint_exact_rebuild(inputs):
    plan = build_detailed_plan(**inputs)
    rendered = render_accepted_v2_production(inputs['packet'], plan)
    assert rendered.validation.valid
    assert 'AI 분석 판단: BUY' in rendered.text
    assert '사업·실적' in rendered.text and '현재 가격 구조' in rendered.text
    assert '수급·포지셔닝\n자료 부족' in rendered.text
    assert all(m + ': 판단 자료 부족' in rendered.text for m in ('PER','PBR','fPER'))
    assert final_detailed_audit(rendered.text, inputs['packet'], plan)['status'] == 'PASS'
    for forbidden in ('등록 가격 규칙', '데이터 주의', '다음 확인', '미확인 사항', 'claim:one', plan.acceptance_sha256):
        assert forbidden not in rendered.text
    assert build_detailed_plan(**inputs) == plan
    restored = DetailedStockMessagePlan.model_validate_json(plan.model_dump_json())
    assert detailed_render(inputs['packet'], restored).text == rendered.text


def test_legacy_calibration_serialization_has_no_detailed_provenance():
    from app.services.accepted_calibration_message_service import AcceptedCalibrationPlan
    old = plan_for(_packet())
    assert 'stage_provenance' not in old.model_dump(mode='json')
    assert AcceptedCalibrationPlan.model_validate_json(old.model_dump_json()) == old


@pytest.mark.parametrize('owner,path', [('source_numeric', None), ('core_claim', 'fields.value')])
def test_row_owner_requires_exact_field_shape(owner, path):
    with pytest.raises(ValueError, match='owner_field_path'):
        RowSelection(section='business', owner=owner, ref='fixture', field_path=path)


@pytest.mark.parametrize('suffix', ['\n등록 가격 규칙\n100', '\n데이터 주의\n추가', '\n다음 확인\n추가',
                                   '\n미확인 사항\n추가', '\n사업·실적\n추가'])
def test_posthoc_unaccepted_section_fails(inputs, suffix):
    plan = build_detailed_plan(**inputs)
    with pytest.raises(ValueError, match='post_render_mutation'):
        final_detailed_audit(detailed_render(inputs['packet'], plan).text + suffix, inputs['packet'], plan)


@pytest.mark.parametrize('section', ['registered_price_rules', 'data_caution', 'next_checks', 'unresolved'])
def test_forbidden_standalone_section_not_in_schema(section):
    with pytest.raises(ValueError):
        RowSelection(section=section, owner='source_numeric', ref='price:current')


@pytest.mark.parametrize('mutation', ['source', 'core', 'A', 'valuation', 'row', 'acceptance'])
def test_every_accepted_input_bound_again_at_render(inputs, mutation):
    plan = build_detailed_plan(**inputs)
    if mutation == 'source':
        changed = deepcopy(plan.source_stock)
        changed['fresh_run_id'] = 'old'
        plan = plan.model_copy(update={'source_stock':changed})
    elif mutation == 'core':
        changed = deepcopy(plan.core)
        changed['atomic_claims'][0]['claim']['text'] = 'Revenue rose 99%.'
        plan = plan.model_copy(update={'core':changed})
    elif mutation == 'A':
        plan = plan.model_copy(update={'pass_a':{}})
    elif mutation == 'valuation':
        plan = plan.model_copy(update={'valuation':plan.valuation.model_copy(update={'price':9})})
    elif mutation == 'row':
        plan = plan.model_copy(update={'rows':plan.rows[:-1]})
    else:
        plan = plan.model_copy(update={'acceptance_sha256':'0'*64})
    with pytest.raises(ValueError):
        detailed_render(inputs['packet'], plan)


def test_unbound_number_in_model_business_text_fails_even_when_resigned(inputs):
    core = inputs['core']
    core['atomic_claims'][0]['claim']['text'] = 'Revenue rose 99%.'
    core['binding_sha256'] = digest({'atomic':core['atomic_claims'], 'effects':core['effects']})
    accepted = inputs['accepted']
    provenance = {**accepted.stage_provenance, 'core_sha256':digest(core)}
    receipt = {**accepted.acceptance, 'stage_provenance_sha256':digest(provenance)}
    inputs['accepted'] = accepted.model_copy(update={'stage_provenance':provenance,
        'acceptance':receipt,'acceptance_sha256':digest(receipt)})
    with pytest.raises(ValueError, match='unbound_number'):
        build_detailed_plan(**inputs)
