"""Native source values through the real B, B2 and renderer transformations.

All prices, indicator values and accepted economic judgments are fictional. The
tests do not invoke a provider/model or re-create an investment conclusion.
"""
from copy import deepcopy
from datetime import date
import json
import socket

import pytest

from app.services import new_buyer_base_contract as b1
from app.services import new_buyer_input_owner as b1_owner
from app.services import new_buyer_request_owner as b2
from app.services import new_buyer_v2_contract as contract
from app.services import production_message_renderer as renderer
from app.services.canonical_monitoring_input import native_technical_context
from app.services.cross_market_decision_engine_service import build_decision_evidence_packet
from app.services.direction_timing_ownership_service import build_owned_evidence_packet
from app.services.detailed_stock_message_v2 import _entry_lines
from app.services.kr_forward_valuation_context import calibration_context
from app.services.packet_owned_technical_context_service import build_native_packet_context
from app.services.production_b2_execution import authorize_b2
from app.services.provider_native_technical import (
    FORMULA_VERSION, FORMULAS, INDICATORS, build_owned_provider_native_view,
)
from app.services.unified_snapshot_contract import digest
from app.services.vnext_execution_profile import SOL_HIGH_V1
from scripts.kis_eps_wire_calibration import sealed
from scripts.m12cn_policy_contract import build_subject_catalog
from scripts.m12cq_two_pass_contract import build_pass_a_subject_context
from scripts.newbuyer_fper_prerequisite_scope import blocker_census
from tests.test_c50_chart_statement import (
    BAR_DATES, SESSION, bound_b_input, produced_case, renderer_case,
)
from tests.test_kr_forward_valuation_integration import view as valuation_fixture
from tests.test_newbuyer_b2_shadow import inputs as first_request_inputs
from tests.test_newbuyer_b2_contract import instantiate
from tests.test_newbuyer_b2_v2 import inputs as b2_inputs


@pytest.fixture(autouse=True)
def no_external(monkeypatch):
    def denied(*args, **kwargs):
        raise AssertionError('C58_MODEL_DELIVERY_EXTERNAL_IO_DENIED')
    monkeypatch.setattr(socket.socket, 'connect', denied)
    monkeypatch.setattr(socket, 'getaddrinfo', denied)


def native_case(market, *, blocked=()):
    """Real native producer and ownership on the existing renderer source fixture."""
    session, ticker, source, stock, _, _ = produced_case(market, 'daily')
    periods, artifacts = {}, {}
    for ordinal, (timeframe, day) in enumerate(BAR_DATES.items()):
        rows = [dict(date=label, open=10, high=11, low=9, close=10,
                     volume=1000, bar_state='FINAL') for label in ('2026-09-01', day)]
        values = {field: index + 0.123456789 + ordinal for index, field in enumerate(INDICATORS)}
        values.update(RSI14=47.123456789 + ordinal, MACD=0.123456789 + ordinal, MA288=None)
        artifacts[timeframe] = dict(contract='provider-native-stock-indicators-v1',
            provider='ohlcv_analyst', indicator_schema=FORMULA_VERSION, status='AVAILABLE',
            calculation_row_count=len(rows),
            rows=[dict(date=row['date'], indicators=deepcopy(values)) for row in rows])
        periods[timeframe] = rows
    native = build_owned_provider_native_view(ticker=ticker, market=market, periods=periods,
        native_indicators=artifacts, cutoff=date.fromisoformat(SESSION))
    technical = build_native_packet_context(view=native, session='closed',
        as_of=source['packet']['generated_at'])
    if blocked:
        quality = dict(technical.quality)
        for timeframe in blocked:
            key = {'daily': 'D', 'weekly': 'W', 'monthly': 'M'}[timeframe]
            quality[key] = quality[key].model_copy(update=dict(usable_for_current_reasoning=False,
                reasons=('EXISTING_COMPLETED_PRICE_COMPATIBILITY_DENIAL',)))
        technical = technical.model_copy(update={'quality': quality})
    stock['technical_context'] = technical.model_dump(mode='json')
    packet = build_decision_evidence_packet(packet=source['packet'], stock=stock,
                                            technical_context=technical)
    owned = build_owned_evidence_packet(packet, stock=stock)
    source.update(evidence_packet=packet.model_dump(mode='json'),
        ownership=owned.model_dump(mode='json'), packet_sha256=digest(source['packet']))
    return session, ticker, source, stock, packet, owned


def b2_with_native(context, *, security_id=None, frozen_authority=None, selected_candidate=None):
    """Use real B2 request/schema builders with explicit synthetic economics."""
    data = b2_inputs(legacy=False)
    subject = data['v1_request']['subject']
    ticker = context['ticker']
    security_id = security_id or 'SYNTHETIC:' + ticker
    generation = context['source_evidence_binding']['source_generation_id']
    tactical = b1_owner.tactical_catalog(context, ticker, security_id, source_generation_id=generation)
    selected_candidate = selected_candidate or next(
        (row['candidate_id'] for row in tactical if row.get('eligible')), 'UNRESOLVED')
    subject.update(ticker=ticker, security_id=security_id, source_generation_id=generation,
        native_technical_context=deepcopy(context['native_technical_context']),
        current_price=deepcopy(context['current_price']), tactical_catalog=tactical,
        selected_tactical_candidate=selected_candidate)
    if frozen_authority is not None:
        subject['frozen_authority'] = deepcopy(frozen_authority)
    else:
        subject['frozen_authority']['context'] = digest(context)
    for fact in subject['facts'].values():
        fact.update(ticker=ticker, security_id=security_id)
    data['v1_request']['output_schema'] = b1.output_schema(subject)
    data['v1_request']['request_sha256'] = digest({k: v for k, v in data['v1_request'].items()
                                                  if k != 'request_sha256'})
    row = {k: v for k, v in data['coverage']['rows'][0].items() if k != 'receipt_sha256'}
    row = sealed(dict(row, ticker=ticker, canonical_security_id=security_id, source_generation=generation))
    coverage = {k: v for k, v in data['coverage'].items() if k != 'receipt_sha256'}
    data['coverage'] = sealed(dict(coverage, rows=[row]))
    data['census'] = blocker_census([row], expected_subjects=[ticker])
    data.update(coverage_sha=data['coverage']['receipt_sha256'], census_sha=data['census']['receipt_sha256'])
    return b2.build_request(**data)


def outputs(request):
    """Explicit fictional technical judgments on the existing economics branches."""
    model_input = request['provider_request']['input']
    values = []
    for branch in request['output_schema']['anyOf']:
        result = {key: instantiate(value) for key, value in branch['properties'].items()
                  if key != 'technical_assessment'}
        technical = branch['properties'].get('technical_assessment')
        if technical is not None:
            if 'anyOf' in technical:
                technical = next(branch for branch in technical['anyOf']
                                 if 'change' not in branch['properties'])
            refs = contract.technical_refs(model_input)
            result['technical_assessment'] = (dict(state='MIXED', evidence_refs=refs[:1],
                reason='지표의 방향과 가격 위치를 함께 확인합니다.') if refs else
                {key: deepcopy(value['const']) for key, value in technical['properties'].items()})
        assert contract.validate_output(result, model_input)['status'] == 'PASS'
        values.append(result)
    return values


@pytest.mark.parametrize('market', ['kr', 'us'])
def test_original_values_and_formulas_reach_b_and_b2_but_not_core_a(market):
    case = native_case(market)
    _, ticker, source, stock, packet, owned = case
    before = deepcopy((stock, packet.model_dump(mode='json')))
    context, _, _ = bound_b_input(case)
    native = context['native_technical_context']
    source_native = stock['technical_context']['native_view']
    assert stock['technical_context']['features'] is None
    assert native['formula_semantics'] == FORMULAS
    for timeframe in BAR_DATES:
        period = native['periods'][timeframe]
        assert period['indicators'] == source_native['periods'][timeframe]['indicators']
        assert set(period['indicators']) == set(INDICATORS)
        assert period['as_of'] == BAR_DATES[timeframe]
        assert period['indicators']['MA288'] is None
        ref = period['evidence_refs']['RSI14']
        assert ref in {row['ref_id'] for row in context['decision_evidence']}
        assert ref not in owned.core_refs and ref in owned.timing_refs
    request = b2_with_native(context)
    payload = b2.provider_payload(request, expected_request_sha256=request['request_sha256'])
    assert json.loads(json.dumps(payload))['input']['native_technical_context'] == native
    assert 'technical_assessment' in request['output_schema']['anyOf'][0]['properties']
    ownership = dict(ticker=ticker, core_ref_ids=sorted(owned.core_refs), timing_ref_ids=sorted(owned.timing_refs))
    input_view = dict(evidence_packets=[packet.model_dump(mode='json')], evidence_ownership=[ownership])
    catalog = build_subject_catalog(context=input_view, ticker=ticker, atomic_claims=[])
    a = build_pass_a_subject_context(context=input_view, ticker=ticker, catalog=catalog)
    assert 'native:' not in json.dumps(a) and '47.123456789' not in json.dumps(a)
    assert (stock, packet.model_dump(mode='json')) == before
    assert source['evidence_packet'] == packet.model_dump(mode='json')


def test_first_b2_owner_preserves_the_same_bundle_without_a_second_calculation():
    context, _, _ = bound_b_input(native_case('kr'))
    args = first_request_inputs(calibration_context(valuation_fixture()))
    args['context']['native_technical_context'] = deepcopy(context['native_technical_context'])
    before = deepcopy(args['context'])
    request = b1_owner.build_request(**args)
    assert request['subject']['native_technical_context'] == context['native_technical_context']
    assert args['context'] == before


def test_audit_only_values_stay_null_in_b_and_b2_and_do_not_enable_interpretation():
    context, _, _ = bound_b_input(native_case('us', blocked=tuple(BAR_DATES)))
    native = context['native_technical_context']
    for period in native['periods'].values():
        assert period['status'] == 'UNAVAILABLE' and not period['evidence_refs']
        assert all(value is None for value in period['indicators'].values())
        assert 'EXISTING_COMPLETED_PRICE_COMPATIBILITY_DENIAL' in period['reasons']
    request = b2_with_native(context)
    for output in outputs(request):
        assert output['technical_assessment']['state'] == 'INSUFFICIENT'
        assert output['technical_assessment']['evidence_refs'] == []


@pytest.mark.parametrize('mutation', ['unknown_ref', 'unbound_number', 'missing_assessment'])
def test_b2_rejects_uncited_or_unbound_native_interpretation(mutation):
    context, _, _ = bound_b_input(native_case('us'))
    request = b2_with_native(context)
    output = outputs(request)[0]
    if mutation == 'unknown_ref':
        output['technical_assessment']['evidence_refs'] = ['native:unprovided']
    elif mutation == 'unbound_number':
        output['technical_assessment']['reason'] = 'RSI14가 70으로 상승했습니다.'
    else:
        output.pop('technical_assessment')
    assert b2.validate_result(dict(new_buyer_shadow=output), request,
        expected_request_sha256=request['request_sha256'])['status'] == 'FAIL'


def test_original_indicator_names_with_digits_are_valid_qualitative_prose():
    text = 'RSI14 주봉의 모멘텀과 MA144의 방향은 지지하지만 BB_50_2.25_UPPER 부근의 부담을 함께 봅니다.'
    assert contract.technical_reason(text, []) == text


def test_changed_source_number_cannot_be_laundered_into_native_bundle():
    case = native_case('us')
    context, _, _ = bound_b_input(case)
    ref = context['native_technical_context']['periods']['daily']['evidence_refs']['RSI14']
    next(row for row in context['decision_evidence'] if row['ref_id'] == ref)['value'] = '99.9'
    with pytest.raises(ValueError, match='native_model_source_value_mismatch'):
        native_technical_context(case[2], context)


@pytest.mark.parametrize('market', ['kr', 'us'])
def test_real_renderer_shows_adverse_technical_view_without_changing_fundamental_axes(monkeypatch, market):
    case = native_case(market)
    session, ticker, source, _, _, _ = case
    context, entries, _ = bound_b_input(case)
    candidate = entries['tactical_candidates'][0]
    accepted, _, old_request = renderer_case(case, context, candidate)
    request = b2_with_native(context, security_id=source['valuation_view']['security_id'],
        frozen_authority=old_request['provider_request']['input']['authority_digests'],
        selected_candidate=candidate['candidate_id'])
    output = next(row for row in outputs(request) if row['new_buyer'] == 'ATTRACTIVE')
    output['technical_assessment'] = dict(state='ADVERSE',
        evidence_refs=[context['native_technical_context']['periods']['daily']['evidence_refs']['RSI14']],
        reason='RSI14의 모멘텀 약화를 확인하고 진입 확인 신호를 기다립니다.')
    # The selected candidate and backend timing remain the same as the old request.
    assert output['timing_context'] == old_request['provider_request']['input']['timing_context']
    auth = authorize_b2(request, generation_id=session.gen, source_generation_id=session.source_gen,
        source_envelope_sha256=digest('synthetic envelope'), owner_sha256=digest('synthetic owner'),
        core_sha256=digest(session.cores[ticker]), pass_a_sha256=digest(session.arows[ticker]),
        pass_b_sha256=digest(session.brows[ticker]), execution_profile=SOL_HIGH_V1)
    raw = dict(new_buyer_shadow=output)
    result = dict(contract='production-b2-accepted-result-v1', generation_id=session.gen,
        ticker=ticker, security_id=source['valuation_view']['security_id'],
        request_sha256=auth.request_sha256, authorization_sha256=digest(auth.model_dump(mode='json')),
        output=raw, output_sha256=digest(raw), status='PASS', attempts=[], semantic_retries=0)
    session.b2_request = lambda key: request
    monkeypatch.setattr(renderer, 'stock_plan', lambda *args: accepted)
    message = renderer.stock_message(session, ticker,
        dict(result=result, authorization=auth.model_dump(mode='json')), execution_profile=SOL_HIGH_V1)
    assert message['NO_SEND'] is True
    assert '기술지표 판단: 약화' in message['text']
    assert '신규 매수자: 기업 매력 있음' in message['text']
    assert 'AI 분석 판단: BUY' in message['text'] and '보유자: HOLD' in message['text']
    assert '지지 구간 안' in message['text'] and '신규 매수 검토 가능' not in message['text']
    assert '기술지표 개선 또는 확인 신호 대기' in message['text']


def test_legacy_request_keeps_its_existing_prompt_and_output():
    request = b2.build_request(**b2_inputs(legacy=False))
    assert request['provider_request']['prompt'] == contract.PROMPT
    assert all('technical_assessment' not in output for output in outputs(request))


@pytest.mark.parametrize('state', ['MIXED', 'INSUFFICIENT'])
def test_mixed_or_incomplete_technical_interpretation_is_not_a_universal_entry_veto(state):
    context, _, _ = bound_b_input(native_case('us'))
    request = b2_with_native(context)
    output = next(row for row in outputs(request) if row['new_buyer'] == 'ATTRACTIVE')
    output['technical_assessment'].update(state=state,
        reason='지표 간 관계를 함께 확인하며 가격 위치와 별도로 해석합니다.')
    lines, refs = _entry_lines(output, request['provider_request']['input'], context, 'us', SESSION)
    assert lines[-1] == '최종 신규매수 행동: 신규 매수 검토 가능'
    assert set(output['technical_assessment']['evidence_refs']) <= set(refs)
