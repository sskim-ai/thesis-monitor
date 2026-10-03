"""Fictional NewBuyer capability probes, never investment decisions."""
from copy import deepcopy
from itertools import product

import pytest

from scripts import newbuyer_b2_contract as b


def subject():
    return dict(ticker='SYN_A', security_id='security-A', frozen_overall='BUY',
        capability=dict(positive=['business:p'], negative=[], holder_risk=[],
                        confidence=[], quality=[]),
        facts={'valuation:per': dict(metric='PER', asset_relevance_proven=False)},
        current_price=dict(value=100, currency='USD', basis='regular_close',
                           as_of='2026-10-01', ref_id='price:current'),
        tactical_catalog=[dict(candidate_id='zone', ticker='SYN_A', security_id='security-A',
            low=90, high=110, currency='USD', price_basis='regular_close', as_of='2026-10-01',
            eligible=True, relation_basis_proven=True, evidence_refs=['entry:zone'])],
        selected_tactical_candidate='zone', absolute_discount=None)


def instantiate(schema):
    if 'const' in schema:
        return deepcopy(schema['const'])
    if schema.get('type') == 'object':
        return {k: instantiate(v) for k, v in schema['properties'].items()}
    if schema.get('type') == 'array':
        return schema['items'].get('enum', [])[:max(1, schema['minItems'])]
    raise AssertionError('unsupported fixture schema')


def probes(sub):
    return [instantiate(s) for s in b.output_schema(sub)['anyOf']]


def choose(sub, *, state='SUPPORTIVE', stance='ATTRACTIVE', reason=None):
    return next(r for r in probes(sub) if r['valuation_context']['state'] == state
                and r['new_buyer'] == stance and (reason is None or r['reason_class'] == reason))


@pytest.mark.parametrize('overall,pos,neg,risk', product(('BUY', 'HOLD', 'SELL'), (False, True),
                                                       (False, True), (False, True)))
def test_complete_business_truth_table(overall, pos, neg, risk):
    sub = subject()
    sub['frozen_overall'] = overall
    sub['capability'].update(positive=['p'] if pos else [], negative=['n'] if neg else [],
                             holder_risk=['r'] if risk else [])
    rows = probes(sub)
    assert all(b.validate_output(r, sub)['status'] == 'PASS' for r in rows)
    stances = {r['new_buyer'] for r in rows}
    assert ('ATTRACTIVE' in stances) == (overall == 'BUY' and pos and not neg and not risk)
    if risk:
        assert stances == {'AVOID'}


@pytest.mark.parametrize('state', b.MODEL_REASONS)
def test_economic_state_is_judgment_not_availability(state):
    sub = subject()
    raw = choose(sub, state=state, stance='ATTRACTIVE' if state == 'SUPPORTIVE' else 'WAIT')
    assert b.validate_output(raw, sub)['status'] == 'PASS'
    assert not b.validate_output(raw, sub)['economic_correctness_proven']
    assert raw['valuation_context']['authority'] == (
        'NOT_RESOLVED' if state == 'UNRESOLVED' else 'MODEL_JUDGED')


@pytest.mark.parametrize('mutation', ['cross_ref', 'empty_ref', 'authority', 'free_prose',
    'fair_value', 'numeric', 'overall', 'holder', 'duplicate_ref', 'business_ref', 'timing'])
def test_closed_model_output_rejects_unowned_fields(mutation):
    sub = subject()
    raw = choose(sub)
    val = raw['valuation_context']
    if mutation == 'cross_ref':
        val['valuation_evidence_refs'] = ['valuation:other']
    elif mutation == 'empty_ref':
        val['valuation_evidence_refs'] = []
    elif mutation == 'authority':
        val['authority'] = 'SOURCE_DETERMINISTIC'
    elif mutation == 'duplicate_ref':
        val['valuation_evidence_refs'] *= 2
    elif mutation == 'business_ref':
        val['business_evidence_refs'] = ['valuation:per']
    elif mutation == 'timing':
        raw['timing_context']['state'] = 'WAIT_FOR_ZONE'
    else:
        raw[mutation] = 'target 200' if mutation == 'free_prose' else 200
    assert b.validate_output(raw, sub)['status'] == 'FAIL'


@pytest.mark.parametrize('reason', ['VALUATION_UNRESOLVED', 'CONFIDENCE_UNCERTAINTY',
    'NO_CLEAN_ENTRY', 'ENTRY_TIMING_UNRESOLVED', 'PRICE_NOT_FAVORABLE',
    'VALUATION_NEUTRAL', 'VALUATION_BURDENSOME', 'BUSINESS_MIXED', 'BUSINESS_GATE_NOT_MET'])
def test_every_wait_reason_rejects_false_predicate(reason):
    sub = subject()
    raw = choose(sub, state='BURDENSOME' if reason == 'VALUATION_NEUTRAL' else 'NEUTRAL',
                 stance='WAIT')
    raw.update(reason_class=reason, reason_evidence_refs=[])
    assert b.validate_output(raw, sub)['status'] == 'FAIL'


def test_truthful_wait_with_supportive_judgment_and_confidence():
    sub = subject()
    sub['capability']['confidence'] = ['confidence:c']
    raw = choose(sub, stance='WAIT', reason='CONFIDENCE_UNCERTAINTY')
    assert b.validate_output(raw, sub)['status'] == 'PASS'
    raw['reason_evidence_refs'] = ['confidence:unowned']
    assert b.validate_output(raw, sub)['status'] == 'FAIL'


def test_reason_valuation_refs_must_match_selected_judgment():
    sub = subject()
    sub['facts']['valuation:forward'] = dict(metric='FORWARD_PE', asset_relevance_proven=False)
    raw = choose(sub, state='NEUTRAL', stance='WAIT', reason='VALUATION_NEUTRAL')
    raw['reason_evidence_refs'] = ['valuation:per']
    raw['valuation_context']['valuation_evidence_refs'] = ['valuation:forward']
    assert b.validate_output(raw, sub)['status'] == 'FAIL'


@pytest.mark.parametrize('price,state,relation', [(90, 'FAVORABLE_NOW', 'INSIDE'),
    (110, 'FAVORABLE_NOW', 'INSIDE'), (100, 'FAVORABLE_NOW', 'INSIDE'),
    (89, 'WAIT_FOR_ZONE', 'BELOW'), (111, 'WAIT_FOR_ZONE', 'ABOVE')])
def test_timing_boundaries(price, state, relation):
    sub = subject()
    sub['current_price']['value'] = price
    assert (b.timing(sub)['state'], b.timing(sub)['relation']) == (state, relation)
    plan = b.presentation_plan(choose(sub), sub)
    assert plan['fundamental_attractiveness'] == 'ATTRACTIVE' and plan['entry_timing'] == state
    assert not plan['bare_buy_label_allowed'] and not plan['production_delivery_allowed']


@pytest.mark.parametrize('gap', ['choice', 'price', 'basis', 'date', 'currency', 'unowned',
    'inverted', 'security', 'ticker', 'ineligible', 'duplicate', 'nan', 'infinity', 'refs'])
def test_timing_fails_closed(gap):
    sub = subject()
    row = sub['tactical_catalog'][0]
    if gap == 'choice':
        sub['selected_tactical_candidate'] = 'missing'
    elif gap == 'price':
        sub['current_price']['value'] = None
    elif gap == 'duplicate':
        sub['tactical_catalog'].append(deepcopy(row))
    else:
        key, value = {'basis': ('price_basis', 'adjusted'), 'date': ('as_of', '2026-09-01'),
            'currency': ('currency', 'KRW'), 'unowned': ('relation_basis_proven', False),
            'inverted': ('low', 120), 'security': ('security_id', 'other'),
            'ticker': ('ticker', 'other'), 'ineligible': ('eligible', False),
            'nan': ('low', 'NaN'), 'infinity': ('high', 'Infinity'),
            'refs': ('evidence_refs', [])}[gap]
        row[key] = value
    assert b.timing(sub)['state'] == 'UNRESOLVED'
    raw = choose(sub, state='NEUTRAL', stance='WAIT', reason='ENTRY_TIMING_UNRESOLVED')
    assert b.validate_output(raw, sub)['status'] == 'PASS'


@pytest.mark.parametrize('risk', [False, True])
def test_owned_absolute_discount_is_separate_and_risk_precedes_both_paths(risk):
    sub = subject()
    sub['absolute_discount'] = dict(evidence_refs=['owned:absolute:range'])
    if risk:
        sub['capability']['holder_risk'] = ['risk:current']
    rows = probes(sub)
    assert all(b.validate_output(r, sub)['status'] == 'PASS' for r in rows)
    if risk:
        assert {r['new_buyer'] for r in rows} == {'AVOID'}
        rows[0]['active_risk_refs'] = []
        assert b.validate_output(rows[0], sub)['status'] == 'FAIL'
    else:
        assert len(rows) == 1
        assert rows[0]['reason_class'] == 'VALID_FUNDAMENTAL_DISCOUNT'
        assert rows[0]['decision_path'] == 'ABSOLUTE_FUNDAMENTAL_RANGE'
        assert rows[0]['valuation_context']['authority'] == 'SOURCE_DETERMINISTIC'


def test_pbr_only_without_relevance_and_empty_valuation_never_support():
    sub = subject()
    sub['facts']['valuation:per']['metric'] = 'PBR'
    assert {r['valuation_context']['state'] for r in probes(sub)} == {'UNRESOLVED'}
    sub['facts'] = {}
    assert {r['new_buyer'] for r in probes(sub)} == {'WAIT'}
