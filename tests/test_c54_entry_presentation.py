"""Changed entry explanations through existing source/B2/renderer paths only."""
from copy import deepcopy
from dataclasses import replace
import socket
from types import SimpleNamespace

import pytest

from app.services import production_message_renderer as renderer
from app.services import us_dated_source_sr as sr
from app.services.detailed_stock_message_v2 import (
    _entry_assessment, _entry_invalidation_row, _entry_lines, _us_sr_rows,
)
from app.services.unified_snapshot_contract import digest
from app.services.vnext_execution_profile import SOL_HIGH_V1
from tests import test_c50_chart_statement as complete
from tests.test_c43_offline import evaluate, fixture
from tests.test_c51_invalidation import invalidation
from tests.test_pr52_v11_us_sr_reference import data as sr_data, source_for


@pytest.fixture(autouse=True)
def no_live_io(monkeypatch):
    def denied(*args, **kwargs):
        raise AssertionError('C54_ENTRY_OFFLINE_ONLY')
    monkeypatch.setattr(socket.socket, 'connect', denied)
    monkeypatch.setattr(socket, 'getaddrinfo', denied)


def assess(context, *, selected=None):
    model_input, timing, _ = evaluate(context)
    if selected is not None:
        timing.update(selected=selected, relation='UNRESOLVED', state='UNRESOLVED')
    result = _entry_assessment(model_input, timing, context, 'us', '2026-11-23')
    output = dict(new_buyer='ATTRACTIVE', reason_class='QUALIFIED_VALUATION_CONTEXT_SUPPORTIVE',
                  timing_context=timing)
    lines, refs = _entry_lines(output, model_input, context, 'us', '2026-11-23', assessment=result)
    return result, '\n'.join(lines), refs


@pytest.mark.parametrize('ratio,classification', [(1.5, 'conditional'), (0.8, 'poor_chase')])
def test_current_rr_wait_explains_existing_threshold_and_uses_same_action_condition(ratio, classification):
    context = fixture()
    rr = context['decision_evidence'][4]['statement']
    rr.update(ratio=ratio, target=10 + 2 * ratio, classification=classification)
    before = deepcopy(context)
    result, text, refs = assess(context)
    assert result.quality == 'CAUTION'
    assert result.next_confirmation == '현재가 손익비 2배 이상 확인(기존 진입 검토 기준)'
    assert '가격 확인 조건: ' + result.next_confirmation in text
    assert '최종 신규매수 행동: ' + result.next_confirmation + ' 대기' in text
    assert '추가 가격 확인 대기' not in text and '신규 매수 검토 가능' not in text
    assert 'canonical:chart:structure:risk_reward:current_price' in refs
    assert context == before


def test_legacy_weekly_comparison_has_no_invented_break_recovery_or_clearance_rule():
    context = fixture()
    context['decision_evidence'][3]['statement'].update(status='higher_timeframe_review',
        weekly_bar_date='2026-11-16', current_recovery='support_reclaimed')
    result, text, _ = assess(context)
    assert result.quality == 'CAUTION' and result.next_confirmation is None
    assert '현재 선택 일봉 기준선의 위치 비교' in text and '과거 지지 이탈 여부 미확인' in text
    assert '추가 확인 조건 미정·대기' in text
    assert all(value not in text for value in ('이탈 후', '하단 회복', '다음 완료 주봉', '신규 매수 검토 가능'))


@pytest.mark.parametrize('case,code,phrase', [
    ('selection', 'ELIGIBLE_NOT_SELECTED', '적격 지지 후보가 있으나'),
    ('absent', 'NO_ELIGIBLE_SUPPORT', '현재 적격 지지 구간 없음'),
    ('currency', 'DATA_INCOMPATIBLE', '통화 불일치'),
])
def test_candidate_gap_classes_do_not_hide_selection_or_promote_reference_prices(case, code, phrase):
    context = fixture()
    selected = 'not-selected' if case == 'selection' else None
    if case == 'absent':
        context['r2_eligible_range_catalog']['tactical_candidates'] = []
        context['entry_candidate_diagnostics'] = [dict(candidate_id='registered-rule', eligible=False,
            failure_reasons=['STORED_PRICE_RULE_REFERENCE_ONLY'])]
    elif case == 'currency':
        context['decision_evidence'][1]['statement']['currency'] = 'KRW'
    before = deepcopy(context)
    result, text, refs = assess(context, selected=selected)
    assert result.reason_code == code and phrase in text
    assert result.quality == 'INSUFFICIENT_EVIDENCE'
    assert '신규 매수 검토 가능' not in text and 'UNRESOLVED' not in text
    assert result.invalidation_ref is None and refs == ()
    assert context == before


def test_display_only_invalidation_cannot_supply_price_or_supported_action():
    context = fixture()
    context['source_use_projection']['source_permissions'][3]['allowed_uses'] = ['DISPLAY']
    result, text, refs = assess(context)
    assert result.quality == 'INSUFFICIENT_EVIDENCE'
    assert result.reason_code == 'RISK_REWARD_INVALIDATION_UNLINKED'
    assert result.invalidation_ref is None
    assert 'canonical:chart:structure:invalidation' not in refs
    assert '신규 매수 검토 가능' not in text


@pytest.mark.parametrize('market', ['kr', 'us'])
@pytest.mark.parametrize('timeframe', ['daily', 'weekly'])
def test_real_renderer_distinguishes_current_daily_support_from_weekly_confirmation(monkeypatch, market, timeframe):
    chart = complete.chart_input(timeframe)
    chart['timeframes']['weekly']['candle']['close'] = 7
    chart['structure']['invalidation'] = invalidation(timeframe, weekly_date='2026-11-20')
    monkeypatch.setattr(complete, 'chart_input', lambda _: deepcopy(chart))
    case = complete.produced_case(market, timeframe)
    session, ticker, source, stock, packet, _ = case
    context, entries, _ = complete.bound_b_input(case)
    accepted, b2_row, request = complete.renderer_case(case, context, entries['tactical_candidates'][0])
    before = deepcopy((source, context, b2_row, request))
    monkeypatch.setattr(renderer, 'stock_plan', lambda *args: accepted)
    message = renderer.stock_message(session, ticker, b2_row, execution_profile=SOL_HIGH_V1)
    text = message['text']
    assert '지지 구간 안' in text and '완료 주봉(기준일 2026-11-20)' in text
    assert '선택 지지 무효화선(2026-11-23 ' in text
    assert text.count('진입 관찰 지지 구간(') == 1
    assert 'AI 분석 판단: BUY' in text and '보유자: HOLD' in text
    assert all(value not in text for value in ('이탈 후', '하단 회복', '추가 가격 확인 대기'))
    if timeframe == 'daily':
        assert '최종 신규매수 행동: 신규 매수 검토 가능' in text
        assert '과거 지지 이탈 여부 미확인' in text
        assert '다음 완료 주봉' not in text
    else:
        condition = '다음 완료 주봉 종가가 선택 지지 무효화선 이상인지 확인'
        assert '가격 확인 조건: ' + condition in text
        assert '최종 신규매수 행동: ' + condition + ' 대기' in text
        assert '신규 매수 검토 가능' not in text
    assert message['NO_SEND'] is True and (source, context, b2_row, request) == before


def test_invalidation_price_requires_the_existing_source_numeric_binding():
    case = complete.produced_case('us', 'daily')
    _, ticker, source, _, packet, _ = case
    context, _, _ = complete.bound_b_input(case)
    model_input = dict(ticker=ticker, security_id=source['valuation_view']['security_id'],
        source_generation='source-one', authority_digests=dict(context=digest(context)))
    from app.services.new_buyer_base_contract import timing
    from app.services.new_buyer_input_owner import tactical_catalog
    catalog = tactical_catalog(context, ticker, model_input['security_id'], source_generation_id='source-one')
    selected = catalog[0]['candidate_id']
    relation = timing(dict(ticker=ticker, security_id=model_input['security_id'],
        selected_tactical_candidate=selected, tactical_catalog=catalog, current_price=context['current_price']))
    result = _entry_assessment(model_input, relation, context, 'us', '2026-11-23')
    base = SimpleNamespace(source_stock=source)
    row = _entry_invalidation_row(packet, base, result, '2026-11-23')
    assert row is not None and '$8.00' in row.text
    assert row.numeric_registry_keys == ('chart:structure:invalidation:fields.price',)
    assert _entry_invalidation_row(packet, base, replace(result, invalidation_price=8.01), '2026-11-23') is None
    assert _entry_invalidation_row(packet, base, result, '2026-11-24') is None


def test_reference_sr_groups_its_date_and_scope_once_without_entry_authority_language(monkeypatch):
    args, _, rollout = sr_data.__wrapped__(monkeypatch)
    rollout.numeric_bindings.append(dict(rollout.numeric_bindings[0], semantic_type='NEAR_RESISTANCE',
        fact_ref='zone:two', source_refs=['pivot:two'], raw_low='110', raw_high='115'))
    rollout.displayed_zone_ids.append('zone:two')
    ref = sr.attach({}, **args)['price_structure_v3']
    source = source_for(ref, args)
    before = digest(source)
    base = SimpleNamespace(source_stock=source, source_generation_id='source-one')
    rows = _us_sr_rows(SimpleNamespace(market='us', ticker='MU'), base, {}, 'security-one')
    text = '\n'.join(row.text for row in rows)
    assert len(rows) == 3 and text.count(args['cutoff']) == 1
    assert '완료 조정봉 · USD' in text and '진입 관찰 지지 구간과 구분' in text
    assert '참고 가까운 지지: $90.00–$95.00' in text
    assert '참고 가까운 저항: $110.00–$115.00' in text
    assert all(value not in text for value in ('B2', '권한', 'V3', '현재가·평가배수'))
    assert digest(source) == before
