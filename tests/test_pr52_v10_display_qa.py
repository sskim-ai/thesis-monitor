from copy import deepcopy
from types import SimpleNamespace

import pytest

from app.services.detailed_stock_message_service import (
    RowSelection, _localized_earnings_line, _numeric, _render_rows, _row,
)
from app.services.market_display_plan import build_display_plan, render_display_plan
from app.services.unified_snapshot_contract import digest
from tests.test_market_display_view import fresh
from tests.test_r9_rev7_detailed_renderer import inputs as inputs


def price_source(inputs, market):
    source = deepcopy(inputs['source_stock'])
    stock = source['packet']['stocks'][0]
    quote = stock['current_price_context']
    basis = 'regular_close' if market == 'us' else 'adjusted_close'
    quote['price_basis'] = basis
    stock['fact_catalog'][0]['fields'].update(price_as_of=quote['as_of_date'], price_basis=basis)
    source['source_graph']['price:current']['fact_sha256'] = digest(stock['fact_catalog'][0])
    source['completed_session_current_price'] = dict(
        contract='kiwoom-us-completed-session-price-v2' if market == 'us' else 'completed-session-current-price-v1',
        price_role='COMPLETED_REGULAR_SESSION_CLOSE', availability='AVAILABLE', ticker=stock['ticker'],
        generation_id=source['fresh_run_id'], current_price=100, currency='USD',
        adjustment_basis=basis, price_as_of=quote['as_of_date'], target_session=quote['as_of_date'])
    return source


@pytest.mark.parametrize('market,label', [('us', '완료 정규장 종가 (regular_close)'),
                                        ('kr', '완료 세션 차트 기준가격 (조정종가)')])
def test_owned_completed_price_label_without_numeric_or_rights_change(inputs, market, label):
    source = price_source(inputs, market)
    before = digest(source)
    row = _numeric(RowSelection(section='price', owner='source_numeric', ref='price:current',
        field_path='fields.current_price'), source)
    assert label in row.text and source['completed_session_current_price']['price_as_of'] in row.text
    assert row.text.endswith('100.00 USD') and digest(source) == before


@pytest.mark.parametrize('field,value', [('generation_id', 'other'), ('availability', 'UNAVAILABLE')])
def test_unqualified_completed_label_not_claimed(inputs, field, value):
    source = price_source(inputs, 'us')
    source['completed_session_current_price'][field] = value
    row = _numeric(RowSelection(section='price', owner='source_numeric', ref='price:current',
        field_path='fields.current_price'), source)
    assert '완료 정규장' not in row.text


def test_us_translation_requires_exact_owned_comparison():
    text = ('Reported revenue is higher versus the source-owned comparable period; source period 2026-09-30. '
            'Recurrence is not established by this observation.')
    fact = dict(fact_id='comparison', fact_type='earnings_comparison', fields=dict(metric='revenue',
        direction='higher', period_end='2026-09-30', prior_period_end='2025-09-30',
        source_ticker='MU', statement_basis='reported'))
    ev = SimpleNamespace(ref_id='e', label='earnings_comparison', as_of='2026-09-30',
        source_ref='stock.fact_catalog.comparison',
        source_time=SimpleNamespace(subject_ticker='MU', canonical_fact_sha256=digest(fact)))
    packet = SimpleNamespace(market='us', ticker='MU', evidence=[ev])
    source = dict(packet=dict(stocks=[dict(fact_catalog=[fact])]),
        source_graph={'comparison': dict(fact_sha256=digest(fact))})
    translated = _localized_earnings_line(text, packet=packet, source=source, refs=['e'])
    assert '2026-09-30' in translated and '2025-09-30' in translated and '매출액' in translated
    assert '이어질지는 확인할 수 없습니다' in translated
    ev.source_time.subject_ticker = 'OTHER'
    assert _localized_earnings_line(text, packet=packet, source=source, refs=['e']) == text


def test_dedup_visible_recovery_only_preserves_evidence_and_other_sections():
    packet = SimpleNamespace(company_name='fixture', ticker='SKHY', assessment_date='2026-11-19')
    rows = [_row('reevaluation', 'one', 'same', facts=('first',)),
            _row('reevaluation', 'two', 'same', facts=('second',)),
            _row('business', 'one', 'unchanged'), _row('business', 'two', 'unchanged')]
    before = digest([r.model_dump(mode='json') for r in rows])
    text = _render_rows(packet, rows)
    assert text.count('same') == 1 and text.count('unchanged') == 2
    assert digest([r.model_dump(mode='json') for r in rows]) == before


def test_macro_display_note_adds_no_directional_rights():
    result = fresh('us')
    source, context = result['packet']['market_context'], result['context']
    before = digest(result)
    plan = build_display_plan(source, market='us', assessment_date=result['packet']['assessment_date'],
        eligible_refs=context['request_eligible_refs'], display_view=result['views']['display'])
    note = next(i for i in plan.items if i.block_id == 'macro_note')
    assert note.proof['directional_authority_added'] is False
    assert not set(note.proof['display_only_refs']) & set(plan.eligible_refs)
    text = render_display_plan(plan, source, '시장 판단: 방향 혼재')
    assert note.text in text and '시장 판단: 방향 혼재' in text and digest(result) == before
    assert all(i.status == 'UNAVAILABLE' for i in plan.items if i.block_id == 'night')
