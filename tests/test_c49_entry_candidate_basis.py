"""Fictional B input -> selectable candidate -> B2 timing; no model/source calls."""
from copy import deepcopy

import pytest

from app.services.canonical_monitoring_input import b_input
from app.services.detailed_stock_message_v2 import _entry_lines
from app.services.entry_candidate_basis import assess_entry_candidates, restrict_entry_candidates
from app.services.new_buyer_base_contract import timing
from app.services.new_buyer_input_owner import tactical_catalog
from app.services.unified_snapshot_contract import digest
from scripts import r2b_r2_contract as b_contract
from scripts.m12cn_policy_contract import build_subject_catalog
from scripts.m12co_entry_range_contract import build_subject_candidate_coverage
from scripts.m12da_source_use_contract import (
    build_source_use_projection, build_trusted_source_authority_manifest,
    freeze_source_use_binding, freeze_source_use_input_expectation,
)
from tests.test_c43_offline import fixture as entry_fixture


TICKER, SECURITY, GENERATION, SESSION = 'X', 'id', 'source-c49', '2026-11-23'


def raw_context(timeframe='daily'):
    context = entry_fixture()
    context['source_evidence_binding']['source_generation_id'] = GENERATION
    context['source_use_projection'].update(ticker=TICKER, source_generation_id=GENERATION)
    if timeframe != 'daily':
        context['decision_evidence'][2]['statement']['timeframe'] = timeframe
        context['decision_evidence'][3]['statement']['timeframe'] = timeframe
        context['decision_evidence'].append(dict(ref_id='canonical:chart:' + timeframe,
            as_of='2026-11-16' if timeframe == 'weekly' else '2026-10-01', label=timeframe,
            statement=dict(timeframe=timeframe, quality='available', currency='USD',
                price_basis='adjusted', candle=dict(close=9.5), completed_bar_only=True,
                evaluation_as_of=SESSION)))
        context['source_use_projection']['source_permissions'].append(dict(
            ref_id='canonical:chart:' + timeframe, allowed_uses=['ENTRY']))
    return context


def canonical_inputs(timeframe, *, close=10):
    """Use real source-use projection, emitted B context and selection schema."""
    rows = raw_context(timeframe)['decision_evidence']
    rows[0]['label'] = 'price'
    rows[1]['statement']['candle']['close'] = close
    rows.extend([
        dict(ref_id='canonical:chart:stored_price_rules', as_of='2026-01-01', label='chart_price_rules',
            statement=dict(currency='USD', support_zone_low=1100, support_zone_high=1125)),
        dict(ref_id='canonical:chart:v3:reference', as_of=SESSION, label='chart_price_structure_v3_zone',
            statement=dict(role='nearest_support', raw_low=9, raw_high=11, currency='USD',
                           source_refs=['unresolved-reference'], eligibility='ELIGIBLE')),
        dict(ref_id='canonical:chart:support:missing-frame', as_of=SESSION, label='chart_support_zone',
            statement=dict(zone_low=9, zone_high=11, currency='USD')),
    ])
    for row in rows:
        row['category'] = 'price_structure'
    packet = dict(ticker=TICKER, market='us', assessment_date='2026-11-24', evidence=rows)
    ownership = dict(ticker=TICKER, core_ref_ids=[], timing_ref_ids=[r['ref_id'] for r in rows])
    catalog = build_subject_catalog(context=dict(evidence_packets=[packet], evidence_ownership=[ownership]),
                                    ticker=TICKER, atomic_claims=[])
    subject = build_subject_candidate_coverage(market='us', packet=packet, ownership=ownership)
    subject.update(decision_evidence=deepcopy(rows), security_valuation_basis_state=dict(state='UNRESOLVED'))
    manifest = build_trusted_source_authority_manifest(ticker=TICKER,
        source_generation_id=GENERATION, catalog=catalog, source_metadata=rows)
    expectation = freeze_source_use_input_expectation(ticker=TICKER,
        source_generation_id=GENERATION, execution_generation_id='exec-c49', catalog=catalog,
        source_metadata=rows, authority_manifest=manifest)
    projection = build_source_use_projection(ticker=TICKER, input_generation_id=GENERATION,
        execution_generation_id='exec-c49', catalog=catalog, authority_manifest=manifest,
        current_input_expectation=expectation)
    binding = freeze_source_use_binding(projection=projection, authority_manifest=manifest,
                                         current_input_expectation=expectation)
    chain = dict(projection=projection, binding=binding, expectation=expectation,
                 source_generation_id=GENERATION, execution_generation_id='exec-c49')
    # Direction capability is immaterial to this entry-only integration fixture.
    capability = dict(positive=['fixture:business'], negative=[], holder_support=['fixture:business'],
        holder_risk=[], holder_reduce=[], confidence=[], quality=[], condition=[], risk_triggers={},
        sell_eligible=[], current_stress=[])
    classification = dict(ticker=TICKER, archetype='DURABLE_FRANCHISE', valuation_regime_tier='BASE')
    return (dict(ticker=TICKER, valuation_view=dict(security_id=SECURITY)), catalog, subject,
            chain, classification, capability)


def selected_timing(context, selected):
    catalog = tactical_catalog(context, TICKER, SECURITY, source_generation_id=GENERATION)
    return timing(dict(ticker=TICKER, security_id=SECURITY, selected_tactical_candidate=selected,
        current_price=context['current_price'], tactical_catalog=catalog))


@pytest.mark.parametrize('timeframe', ['daily', 'weekly', 'monthly'])
def test_actual_b_selection_and_b2_share_completed_support_eligibility(timeframe):
    inputs = canonical_inputs(timeframe)
    before = deepcopy(inputs)
    context, entries, valuation = b_input(*inputs)
    assert inputs == before
    assert len(entries['tactical_candidates']) == 1
    candidate = entries['tactical_candidates'][0]
    assert candidate['source_label'] == 'chart_support_zone' and candidate['eligible']
    assert context['tactical_candidates'] == entries['tactical_candidates']
    schema = b_contract.decision_schema('EVIDENCE_BASED', inputs[-1], valuation, entries, {})
    assert schema['properties']['tactical_choice']['enum'] == [candidate['candidate_id']]
    refs = [context['current_price']['ref_id'], 'canonical:chart:daily',
            'canonical:chart:' + timeframe, *candidate['evidence_refs']]
    permissions = {row['ref_id']: row['allowed_uses']
                   for row in context['source_use_projection']['source_permissions']}
    assert all('ENTRY' in permissions[ref] for ref in refs)
    result = selected_timing(context, candidate['candidate_id'])
    assert (result['state'], result['relation']) == ('FAVORABLE_NOW', 'INSIDE')
    assert result['evidence_refs'] == sorted([context['current_price']['ref_id'], *candidate['evidence_refs']])
    excluded = [row for row in context['entry_candidate_diagnostics'] if not row['eligible']]
    reasons = {reason for row in excluded for reason in row['failure_reasons']}
    assert {'STORED_PRICE_RULE_REFERENCE_ONLY', 'V3_COMPLETED_FRAME_BASIS_MISSING',
            'SUPPORT_TIMEFRAME_MISSING_OR_MISMATCH'} <= reasons
    # The old strategy's date and V3's missing frame remain untouched in evidence.
    assert next(r for r in context['decision_evidence'] if r['label'] == 'chart_price_rules')['as_of'] == '2026-01-01'
    assert 'timeframe' not in next(r for r in context['decision_evidence']
                                 if r['label'] == 'chart_price_structure_v3_zone')['statement']
    lines, _ = _entry_lines(dict(new_buyer='WAIT', reason_class='VALUATION_BURDENSOME', timing_context=result),
        dict(ticker=TICKER, security_id=SECURITY, source_generation=GENERATION,
             authority_digests=dict(context=digest(context))), context, 'us', SESSION)
    assert '지지 구간 안' in lines[1] and '가치평가 부담 완화 대기' in lines[-1]


def test_no_eligible_candidate_has_valid_schema_and_explained_render_without_promoting_reference():
    inputs = canonical_inputs('weekly', close=9.999999999)
    context, entries, valuation = b_input(*inputs)
    assert entries['tactical_candidates'] == context['tactical_candidates'] == []
    schema = b_contract.decision_schema('EVIDENCE_BASED', inputs[-1], valuation, entries, {})
    assert schema['properties']['tactical_choice']['enum'] == ['UNRESOLVED']
    result = selected_timing(context, 'UNRESOLVED')
    assert result['state'] == 'UNRESOLVED' and result['evidence_refs'] == []
    lines, refs = _entry_lines(dict(new_buyer='ATTRACTIVE', reason_class='QUALIFIED_VALUATION_CONTEXT_SUPPORTIVE',
        timing_context=result), dict(ticker=TICKER, security_id=SECURITY, source_generation=GENERATION,
        authority_digests=dict(context=digest(context))), context, 'us', SESSION)
    assert '기준가격과 일봉 종가 연결 확인 필요' in lines[1]
    assert 'UNRESOLVED' not in '\n'.join(lines) and '신규 매수 검토 가능' not in '\n'.join(lines)
    assert refs == ()


def test_preexisting_source_use_exclusion_keeps_its_reason_and_cannot_reenter_b_choices():
    context = raw_context()
    context['tactical_candidates'] = deepcopy(context['r2_eligible_range_catalog']['tactical_candidates'])
    context['source_use_projection']['source_permissions'][2]['allowed_uses'] = ['DISPLAY']
    context, entries = restrict_entry_candidates(context, dict(tactical_candidates=[]),
        ticker=TICKER, security_id=SECURITY, source_generation_id=GENERATION)
    assert entries['tactical_candidates'] == []
    diagnostic = context['entry_candidate_diagnostics'][0]
    assert {'SUPPORT_ENTRY_DENIED', 'SOURCE_USE_OR_CURRENCY_INELIGIBLE'} <= set(diagnostic['failure_reasons'])
    result = selected_timing(context, 'UNRESOLVED')
    lines, _ = _entry_lines(dict(new_buyer='ATTRACTIVE', reason_class='QUALIFIED_VALUATION_CONTEXT_SUPPORTIVE',
        timing_context=result), dict(ticker=TICKER, security_id=SECURITY, source_generation=GENERATION,
        authority_digests=dict(context=digest(context))), context, 'us', SESSION)
    assert '현재 적격 지지 구간 없음' in lines[1]


@pytest.mark.parametrize('gap,expected', [
    ('generation', 'SOURCE_GENERATION_MISMATCH'),
    ('ticker', 'TICKER_MISMATCH'),
    ('security', 'SECURITY_MISMATCH'),
    ('daily_currency', 'DAILY_FRAME_CURRENCY_MISMATCH'),
    ('daily_basis', 'DAILY_FRAME_PRICE_BASIS_MISMATCH'),
    ('price_evidence', 'PRICE_EVIDENCE_MISSING'),
    ('price_entry', 'PRICE_ENTRY_DENIED'),
    ('daily_entry', 'DAILY_ENTRY_DENIED'),
    ('support_entry', 'SUPPORT_ENTRY_DENIED'),
    ('support_frame_entry', 'SUPPORT_FRAME_ENTRY_DENIED'),
    ('partial_week', 'SUPPORT_FRAME_INCOMPLETE'),
    ('candidate_as_of', 'ZONE_SESSION_MISMATCH'),
])
def test_saved_context_diagnostic_names_exact_failure_and_never_rewrites_input(gap, expected):
    context = raw_context('weekly')
    candidate = context['r2_eligible_range_catalog']['tactical_candidates'][0]
    if gap == 'generation':
        context['source_use_projection']['source_generation_id'] = 'another-run'
    elif gap in ('ticker', 'security'):
        candidate['ticker' if gap == 'ticker' else 'security_id'] = 'another-security'
    elif gap == 'daily_currency':
        context['decision_evidence'][1]['statement']['currency'] = 'KRW'
    elif gap == 'daily_basis':
        context['decision_evidence'][1]['statement']['price_basis'] = 'unadjusted'
    elif gap == 'price_evidence':
        context['decision_evidence'] = context['decision_evidence'][1:]
    elif gap == 'partial_week':
        context['decision_evidence'][-1]['statement']['completion_state'] = 'PARTIAL'
    elif gap == 'candidate_as_of':
        candidate['as_of'] = '2026-11-16'
    else:
        index = dict(price_entry=0, daily_entry=1, support_entry=2, support_frame_entry=-1)[gap]
        context['source_use_projection']['source_permissions'][index]['allowed_uses'] = ['DISPLAY']
    before = deepcopy(context)
    rows = assess_entry_candidates(context, ticker=TICKER, security_id=SECURITY,
                                   source_generation_id=GENERATION)
    assert context == before
    assert not rows[0]['eligible'] and expected in rows[0]['failure_reasons']
    assert rows[0]['basis_proofs'][0]['passed'] is False
    assert expected in rows[0]['basis_proofs'][0]['failure_reasons']
    after, entries = restrict_entry_candidates(context, context['r2_eligible_range_catalog'],
        ticker=TICKER, security_id=SECURITY, source_generation_id=GENERATION)
    assert entries['tactical_candidates'] == [] and after['entry_candidate_diagnostics'][0]['failure_reasons']
    if gap == 'candidate_as_of':
        assert rows[0]['as_of'] == '2026-11-16'
