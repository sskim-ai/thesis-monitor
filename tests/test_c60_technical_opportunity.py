"""Changed C60 boundaries; fictional technical observations, no live I/O."""
from copy import deepcopy
from datetime import date, timedelta
from fractions import Fraction
from types import SimpleNamespace

import pytest

from app.services.provider_native_technical import recent_completed_comparison
from app.services.entry_price_basis import fixed_rr2_bounds, rr2_display_interval
from app.services.detailed_stock_message_v2 import _buyer_action
from app.services import new_buyer_v2_contract as contract
from app.services import new_buyer_request_owner as owner
from tests.test_c58_native_model_delivery import (
    no_external, native_case, bound_b_input, b2_with_native, outputs,
)


def test_recent_comparison_preserves_actual_offsets_and_intervening_breach():
    rows = [dict(date=(date(2026, 10, 1)+timedelta(days=i)).isoformat(),
        close=close, volume=100+i, indicators={'MA33': 10, 'MACD': -i,
            'RSI14': None if i==4 else 40+i, 'MA288': None})
        for i,close in enumerate((11,12,9,9,11,12))]
    period = SimpleNamespace(status='AVAILABLE', rows=rows, completed_as_of=rows[-1]['date'],
        indicators=rows[-1]['indicators'], indicator_quality={'MA33':'PROVIDER_NATIVE',
        'MACD':'PROVIDER_NATIVE','RSI14':'PROVIDER_NATIVE','MA288':'UNAVAILABLE_PROVIDER_NULL_OR_MISSING'})
    before = deepcopy(rows)
    value = recent_completed_comparison(period)
    assert value['dates'] == [rows[i]['date'] for i in (5,4,0)]
    assert value['close'] == [12,11,11] and value['volume'] == [105,104,100]
    assert value['prior_indicators']['RSI14'] == [None,40]
    assert value['prior_indicators']['MACD'] == [-4,0]
    assert value['close_relations']['MA33'] == 'AABBAA'
    assert 'MACD' not in value['close_relations'] and 'MA288' not in value['prior_indicators']
    assert rows == before
    period.rows = rows[-2:]
    assert recent_completed_comparison(period)['dates'][2] is None
    period.status = 'INVALID'
    assert recent_completed_comparison(period) is None


@pytest.mark.parametrize('market', ['kr','us'])
def test_real_b_b2_wire_accepts_change_absent_unclear_and_adverse_improving(market):
    context, _, _ = bound_b_input(native_case(market))
    native = context['native_technical_context']
    assert native['comparison_version'] == 1
    for period in native['periods'].values():
        comp = period['recent_comparison']
        assert comp['dates'][0] == period['as_of'] and comp['dates'][2] is None
        for key in ('previous','lag5','close_relations'):
            assert len(comp[key]) == len(native['comparison_fields'])
            assert {f for f,v in zip(native['comparison_fields'],comp[key]) if v is not None} <= set(period['evidence_refs'])
    request = b2_with_native(context)
    payload = owner.provider_payload(request, expected_request_sha256=request['request_sha256'])
    assert payload['input']['native_technical_context'] == native
    output = outputs(request)[0]
    baseline = deepcopy(output['technical_assessment'])
    for state,change in [('MIXED',None),('MIXED','UNCLEAR'),('ADVERSE','IMPROVING'),
                         ('SUPPORTIVE','DETERIORATING')]:
        output['technical_assessment'] = dict(baseline,state=state)
        if change is not None:
            output['technical_assessment']['change'] = change
        assert owner.validate_result(dict(new_buyer_shadow=output),request,
            expected_request_sha256=request['request_sha256'])['status']=='PASS'
    # Existing sealed requests without the comparison marker retain their old shape.
    prior = deepcopy(payload['input'])
    prior['native_technical_context'].pop('comparison_version')
    assert 'properties' in contract.technical_assessment_schema(prior)


def test_no_history_leaks_from_denied_native_period():
    context, _, _ = bound_b_input(native_case('us', blocked=('daily',)))
    assert 'recent_comparison' not in context['native_technical_context']['periods']['daily']


@pytest.mark.parametrize('stance,relation,quality,state,change,breakout,expected', [
    ('ATTRACTIVE','ABOVE','SUPPORTED','SUPPORTIVE',None,False,'조건부 신규 매수 검토 가능'),
    ('ATTRACTIVE','ABOVE','SUPPORTED','MIXED','IMPROVING',False,'조건부 신규 매수 검토 가능'),
    ('ATTRACTIVE','ABOVE','SUPPORTED','MIXED',None,True,'조건부 신규 매수 검토 가능'),
    ('ATTRACTIVE','INSIDE','SUPPORTED','MIXED','IMPROVING',False,'조건부 신규 매수 검토 가능'),
    ('ATTRACTIVE','INSIDE','SUPPORTED','MIXED',None,False,'신규 매수 검토 가능'),
    ('ATTRACTIVE','ABOVE','SUPPORTED','MIXED','DETERIORATING',False,'기술지표 개선 또는 확인 신호 대기'),
    ('ATTRACTIVE','ABOVE','SUPPORTED','ADVERSE','IMPROVING',True,'기술지표 개선 또는 확인 신호 대기'),
    ('ATTRACTIVE','ABOVE','CAUTION','SUPPORTIVE','IMPROVING',False,'가격 조정 또는 신규 확인 신호 대기'),
    ('ATTRACTIVE','INSIDE','BLOCKED','MIXED','IMPROVING',False,'지지 이탈 구조 재검토'),
    ('AVOID','ABOVE','SUPPORTED','SUPPORTIVE','IMPROVING',True,'신규 매수 회피'),
    ('WAIT','INSIDE','SUPPORTED','SUPPORTIVE','IMPROVING',True,'가치평가 자료 확인 대기'),
])
def test_action_respects_economics_and_price_quality(stance,relation,quality,state,change,breakout,expected):
    technical = dict(state=state)
    if change is not None:
        technical['change'] = change
    assert _buyer_action(stance,relation,quality,reason_class='VALUATION_UNRESOLVED',
        confirmed_breakout=breakout,technical=technical)==expected


def test_fixed_rr2_exact_intersection_and_inward_display():
    a = fixed_rr2_bounds(support_low=96,support_high=99,invalidation=93,target=110)
    assert a['maximum'] == Fraction(296,3)
    assert rr2_display_interval(a,decimals=2) == ('96.00','98.66')
    b = fixed_rr2_bounds(support_low=90,support_high=95,invalidation=88,target=110)
    assert b['maximum'] == Fraction(286,3)
    assert rr2_display_interval(b,decimals=2) == ('90.00','95.00')
    empty = fixed_rr2_bounds(support_low=100,support_high=101,invalidation=90,target=110)
    assert empty['interval'] is None
    narrow = fixed_rr2_bounds(support_low='98.661',support_high='99',invalidation=93,target=110)
    assert narrow['interval'] is not None and rr2_display_interval(narrow,decimals=2) is None
    assert fixed_rr2_bounds(support_low=90,support_high=95,invalidation=88,target=94) is None
    assert fixed_rr2_bounds(support_low=90,support_high=95,invalidation=None,target=110) is None
