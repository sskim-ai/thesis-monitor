"""Pure entry diagnostics for damaged statements; no source/model calls."""
from copy import deepcopy
import json

import pytest

from app.services.detailed_stock_message_v2 import _entry_lines
from app.services.entry_candidate_basis import assess_entry_candidates, restrict_entry_candidates, statement
from app.services.unified_snapshot_contract import digest
from tests.test_c49_entry_candidate_basis import (
    GENERATION, SECURITY, SESSION, TICKER, raw_context, selected_timing,
)


def long_statement(fields):
    value = dict(fields, diagnostic_padding='x'*1200)
    return json.dumps(value,ensure_ascii=False,separators=(',', ':'))


def truncated_statement(fields):
    raw = long_statement(fields)
    assert len(raw)>900
    return raw[:899]+'…'


def diagnose(context):
    before = deepcopy(context)
    rows = assess_entry_candidates(context,ticker=TICKER,security_id=SECURITY,
                                   source_generation_id=GENERATION)
    restricted, entries = restrict_entry_candidates(context,context['r2_eligible_range_catalog'],
        ticker=TICKER,security_id=SECURITY,source_generation_id=GENERATION)
    assert context==before and entries['tactical_candidates']==[]
    timing = selected_timing(restricted,'UNRESOLVED')
    lines, refs = _entry_lines(dict(new_buyer='ATTRACTIVE',
        reason_class='QUALIFIED_VALUATION_CONTEXT_SUPPORTIVE',timing_context=timing),
        dict(ticker=TICKER,security_id=SECURITY,source_generation=GENERATION,
             authority_digests=dict(context=digest(restricted))),restricted,'us',SESSION)
    text = '\n'.join(lines)
    assert not rows[0]['eligible'] and not rows[0]['relation_basis_proven']
    assert rows[0]['basis_proofs'][0]['passed'] is False
    assert refs==() and '신규 매수 검토 가능' not in text and 'UNRESOLVED' not in text
    return set(rows[0]['failure_reasons']), text


def test_899_char_prefix_and_ellipsis_names_json_damage_not_currency_or_close():
    context = raw_context()
    daily = context['decision_evidence'][1]
    daily['statement'] = truncated_statement(daily['statement'])
    assert len(daily['statement'])==900 and daily['statement'].endswith('…')
    assert statement(daily)=={}
    reasons, text = diagnose(context)
    assert reasons=={'DAILY_STATEMENT_INVALID_JSON','SUPPORT_STATEMENT_INVALID_JSON'}
    assert 'JSON 형식 손상' in text
    assert all(word not in text for word in ('통화 불일치','조정 기준 불일치','종가 연결'))


def test_damaged_completed_support_frame_cannot_imply_a_close_or_basis_mismatch():
    context = raw_context('weekly')
    weekly = context['decision_evidence'][-1]
    weekly['statement'] = truncated_statement(weekly['statement'])
    reasons, text = diagnose(context)
    assert reasons=={'SUPPORT_STATEMENT_INVALID_JSON'}
    assert 'JSON 형식 손상' in text and '통화 불일치' not in text and '조정 기준 불일치' not in text


def test_valid_json_array_is_a_shape_error_and_keeps_mapping_reader_compatible():
    context = raw_context()
    daily = context['decision_evidence'][1]
    daily['statement'] = '[{"currency":"USD"}]'
    assert statement(daily)=={}
    reasons, text = diagnose(context)
    assert reasons=={'DAILY_STATEMENT_NOT_OBJECT','SUPPORT_STATEMENT_NOT_OBJECT'}
    assert '구조화 형식 확인 필요' in text and 'JSON 형식 손상' not in text
    assert '통화 불일치' not in text


def test_valid_json_wrong_currency_still_reports_the_real_mismatch():
    context = raw_context()
    daily = context['decision_evidence'][1]
    fields = dict(daily['statement'],currency='KRW')
    daily['statement'] = json.dumps(fields)
    assert statement(daily)==fields
    reasons, text = diagnose(context)
    assert reasons=={'DAILY_FRAME_CURRENCY_MISMATCH','SUPPORT_FRAME_CURRENCY_MISMATCH'}
    assert '통화 불일치' in text and '형식 손상' not in text


@pytest.mark.parametrize('change,expected', [
    ('basis','DAILY_FRAME_PRICE_BASIS_MISMATCH'),
    ('partial','SUPPORT_FRAME_INCOMPLETE'),
    ('entry','SUPPORT_FRAME_ENTRY_DENIED'),
    ('identity','SECURITY_MISMATCH'),
])
def test_valid_source_basis_completion_entry_and_identity_checks_remain(change,expected):
    context = raw_context('weekly')
    if change=='basis':
        context['decision_evidence'][1]['statement']['price_basis']='unadjusted'
    elif change=='partial':
        context['decision_evidence'][-1]['statement']['completion_state']='PARTIAL'
    elif change=='entry':
        context['source_use_projection']['source_permissions'][-1]['allowed_uses']=['DISPLAY']
    else:
        context['decision_evidence'][-1]['security_id']='another-security'
    for row in context['decision_evidence']:
        row['statement']=json.dumps(row['statement'])
    reasons, text = diagnose(context)
    assert expected in reasons and not any('STATEMENT_' in reason for reason in reasons)
    assert '형식 손상' not in text


def test_complete_long_daily_statement_does_not_promote_a_stored_price_rule():
    context = raw_context()
    daily = context['decision_evidence'][1]
    daily['statement']=long_statement(daily['statement'])
    ref='canonical:chart:stored_price_rules'
    context['decision_evidence'][2].update(ref_id=ref,label='chart_price_rules',
        statement=json.dumps(dict(currency='USD',support_zone_low=9,support_zone_high=11)))
    context['source_use_projection']['source_permissions'][2]['ref_id']=ref
    context['r2_eligible_range_catalog']['tactical_candidates'][0]['evidence_refs']=[ref]
    reasons, text = diagnose(context)
    assert reasons=={'STORED_PRICE_RULE_REFERENCE_ONLY'}
    assert '등록 가격 규칙은 완료봉 지지 근거가 아님' in text and '형식 손상' not in text


def test_damaged_support_zone_does_not_invent_a_frame_or_zone_mismatch():
    context = raw_context()
    zone = context['decision_evidence'][2]
    zone['statement']=truncated_statement(zone['statement'])
    reasons, text = diagnose(context)
    assert reasons=={'ZONE_STATEMENT_INVALID_JSON'}
    assert 'JSON 형식 손상' in text and '통화 불일치' not in text
    assert '지지 봉 기간 미확정' not in text
