"""Adapter and OFF-path tests use only fictional, local provider fixtures."""
from copy import deepcopy
from types import SimpleNamespace

import pytest

from app.config import Settings
from app.services.kr_forward_valuation_context import calibration_context as kr_context
from app.services.provider_valuation_calibration_context import calibration_context
from app.services.unified_snapshot_contract import digest
from scripts import newbuyer_b2_shadow as s
from scripts import newbuyer_b2_contract as b
from scripts.r2b_r5_execution import Execution
from scripts.m12da_source_use_contract import canonical_source_metadata_sha256
from tests.test_newbuyer_b2_contract import probes
from tests.test_kr_forward_valuation_integration import view
from tests.test_r9_rev29_valuation_integration import build_valuation

ON = SimpleNamespace(newbuyer_qualified_valuation_shadow=True)
OFF = SimpleNamespace(newbuyer_qualified_valuation_shadow=False)


def inputs(vc):
    ticker = vc['ticker']
    core = dict(atomic_claims=[dict(claim_ref='business:p')],
                effects={'business:p': dict(effect='DIRECTIONAL_POSITIVE')})
    core['binding_sha256'] = digest(dict(atomic=core['atomic_claims'], effects=core['effects']))
    cap = dict(ticker=ticker, positive=['business:p'], negative=[], holder_risk=[],
               confidence=[], quality=[], core_binding_sha256=core['binding_sha256'],
               source_binding_sha256='a'*64)
    a = dict(ticker=ticker, archetype='NOT_AN_ASSET_RELEVANCE_OWNER')
    context = dict(ticker=ticker, valuation_context=vc,
        source_evidence_binding=dict(ticker=ticker, source_use_binding_sha256='a'*64,
                                    emitted_evidence_sha256=canonical_source_metadata_sha256([]),
                                    source_generation_id=vc['run_id']),
        source_use_projection=dict(source_permissions=[], binding_sha256='a'*64), r2_policy_capability=cap,
        frozen_pass_a_classification=a, r2_core_effects=core['effects'], decision_evidence=[],
        current_price={}, r2_eligible_range_catalog=dict(tactical_candidates=[], fundamental_candidates=[]),
        r2_valuation=dict(fundamental_valid=False, compensating_discount=False))
    return dict(settings=ON, context=context, core=core, pass_a=a,
                accepted=dict(overall_direction='BUY', tactical_choice='UNRESOLVED', holder='HOLDABLE'),
                source_generation_id=vc['run_id'])


@pytest.fixture
def request_inputs(tmp_path):
    return inputs(calibration_context(build_valuation(tmp_path)[0]))


def test_off_default_and_explicit_controller_path_never_dispatches():
    assert Settings(_env_file=None).newbuyer_qualified_valuation_shadow is False
    assert s.build_request(settings=OFF, context=None, accepted=None, core=None,
                           pass_a=None, source_generation_id=None) is None
    controller = object.__new__(Execution)
    assert controller.newbuyer_shadow_requests(OFF) == {}


def test_frozen_adapter_request_no_mutation_and_real_controller_entry(request_inputs):
    args = request_inputs
    before = digest({k: v for k, v in args.items() if k != 'settings'})
    request = s.build_request(**args)
    assert digest({k: v for k, v in args.items() if k != 'settings'}) == before
    assert not request['dispatch_authorized'] and not request['persistence_authorized']
    assert not request['delivery_authorized']
    assert all(s.validate_result(raw, request)['status'] == 'PASS' for raw in probes(request['subject']))
    assert request['provider_dialect_validation']['status'] == 'PASS'
    assert request['provider_wire_schema']['type'] == 'object'
    assert 'anyOf' not in request['provider_wire_schema']
    assert all(s.validate_wire_result(dict(new_buyer_shadow=raw), request)['status'] == 'PASS'
               for raw in probes(request['subject']))
    controller = object.__new__(Execution)
    ticker = args['context']['ticker']
    controller.bctx, controller.brows = {ticker: args['context']}, {ticker: args['accepted']}
    controller.cores, controller.arows = {ticker: args['core']}, {ticker: args['pass_a']}
    controller.source_gen = args['source_generation_id']
    assert controller.newbuyer_shadow_requests(ON) == {ticker: request}


@pytest.mark.parametrize('gap', ['cross_security', 'generation', 'unit', 'unqualified',
    'fact_identity', 'asof_binding', 'core_binding', 'core_effects', 'cap_ref', 'pass_a'])
def test_input_authority_gaps_fail_closed(request_inputs, gap):
    args = request_inputs
    vc = args['context']['valuation_context']
    row = vc['metric_states'][0]
    fact = vc['facts'][row['fact_ref']]
    if gap == 'cross_security':
        vc['security_id'] = 'other-security'
    elif gap == 'generation':
        args['source_generation_id'] = 'other-generation'
    elif gap == 'unit':
        fact['registry']['unit'] = 'USD'
    elif gap == 'unqualified':
        row['state'] = 'UNAVAILABLE'
    elif gap == 'fact_identity':
        fact['fact']['ticker'] = 'OTHER'
    elif gap == 'asof_binding':
        fact['fact']['provider_snapshot']['retrieval_timestamp'] = '2026-10-01T00:00:00Z'
    elif gap == 'core_binding':
        args['core']['binding_sha256'] = 'b'*64
    elif gap == 'core_effects':
        args['context']['r2_core_effects'] = {}
    elif gap == 'cap_ref':
        args['context']['r2_policy_capability']['positive'] = ['invented:positive']
    else:
        args['pass_a'] = dict(ticker='OTHER')
    vc['context_sha256'] = digest({k: v for k, v in vc.items() if k != 'context_sha256'})
    with pytest.raises((ValueError, KeyError)):
        s.build_request(**args)


def test_kr_house_research_current_only_without_eps_owner():
    vc = kr_context(view())
    request = s.build_request(**inputs(vc))
    facts = request['subject']['facts']
    assert len(facts) == 1
    fact = next(iter(facts.values()))
    assert fact['metric'] == 'CURRENT_FY1_FPER'
    assert fact['source_kind'] == 'KIS_HOUSE_RESEARCH_NOT_CONSENSUS'
    assert fact['metadata']['estimate_date'] and fact['metadata']['price_date']


def test_us_horizon_policy_not_promoted_to_provider_fact(request_inputs):
    request = s.build_request(**request_inputs)
    fact = next(f for f in request['subject']['facts'].values() if f['metric'] == 'FORWARD_PE')
    assert fact['metadata']['horizon_authority'] == 'USER_AUTHORIZED_PRODUCT_POLICY'
    assert fact['metadata']['provider_horizon'] is None
    assert 'EPS' not in {f['metric'] for f in request['subject']['facts'].values()}
    assert request['subject']['absolute_discount'] is None


def test_request_tamper_or_model_owned_timing_cannot_validate(request_inputs):
    request = s.build_request(**request_inputs)
    raw = probes(request['subject'])[0]
    broken = deepcopy(request)
    broken['subject']['frozen_overall'] = 'SELL'
    with pytest.raises(ValueError, match='request_drift'):
        s.validate_result(raw, broken)
    raw['timing_context']['state'] = 'FAVORABLE_NOW'
    assert s.validate_result(raw, request)['status'] == 'FAIL'


def test_wire_projection_does_not_lose_local_uniqueness_or_closed_shape(request_inputs):
    from tests.test_newbuyer_b2_contract import choose
    request = s.build_request(**request_inputs)
    raw = choose(request['subject'])
    raw['valuation_context']['valuation_evidence_refs'] *= 2
    result = s.validate_wire_result(dict(new_buyer_shadow=raw), request)
    assert result['status'] == 'FAIL'
    assert 'uniqueItems' not in request['provider_dialect_validation']['keyword_counts']
    raw = choose(request['subject'])
    assert s.validate_wire_result(dict(new_buyer_shadow=raw, holder='REDUCE'), request)['status'] == 'FAIL'


def test_owned_range_flags_alone_do_not_grant_absolute_positive(request_inputs):
    args = request_inputs
    args['context']['r2_valuation'].update(fundamental_valid=True, compensating_discount=True,
        option=dict(status='RESOLVED', ticker=args['context']['ticker'], evidence_refs=['range:r'],
                    currency='USD', low=100, high=200, option_id='range:option'))
    args['context']['current_price'] = dict(value=50, currency='USD')
    with pytest.raises(ValueError, match='absolute_range_owner_binding'):
        s.build_request(**args)


def test_existing_deterministic_absolute_owner_is_preserved():
    from tests.test_m12ds_r2_judgment_policy import valuation
    from scripts.m12ds_r2_ranges import valuation_policy
    sub, a, basis = valuation(pe=(130, 150), pb=None)
    value = valuation_policy(sub, a, basis)
    assert value['fundamental_valid'] and value['compensating_discount']
    context = dict(ticker=sub['ticker'], current_price=sub['current_price'], r2_valuation=value,
        deterministic_fundamental_option=value['option'],
        r2_eligible_range_catalog=dict(fundamental_candidates=sub['fundamental_candidates']),
        source_use_projection=dict(source_permissions=[dict(ref_id=ref, allowed_uses=['VALUATION'])
            for ref in value['option']['evidence_refs']]))
    owned = s.absolute_discount(context)
    assert owned['evidence_refs'] == sorted(value['option']['evidence_refs'])
    context['r2_valuation']['security_gate']['basis_state'] = 'UNRESOLVED'
    with pytest.raises(ValueError, match='absolute_range_owner_binding'):
        s.absolute_discount(context)


def timing_input():
    price = dict(value=100, currency='USD', basis='regular_close', as_of='2026-10-01',
                 ref_id='price:current')
    evidence = [dict(ref_id='price:current', as_of=price['as_of'],
        statement=dict(current_price=100, currency='USD', price_basis='regular_close',
                       price_as_of=price['as_of'])),
        dict(ref_id='zone:current', as_of=price['as_of'], label='chart_support_zone',
             statement=dict(zone_low=90, zone_high=110, currency='USD', timeframe='daily')),
        dict(ref_id='canonical:chart:daily', as_of=price['as_of'],
             statement=dict(candle=dict(close=100), currency='USD', price_basis='unadjusted',
                            quality='available'))]
    return dict(current_price=price, decision_evidence=evidence,
        source_use_projection=dict(source_permissions=[dict(ref_id='zone:current', allowed_uses=['ENTRY'])]),
        r2_eligible_range_catalog=dict(tactical_candidates=[dict(candidate_id='zone',
            ticker='SYN_A', security_id='security-A', low=90, high=110, currency='USD',
            evidence_refs=['zone:current'])]))


@pytest.mark.parametrize('gap', [None, 'permission', 'currency', 'date', 'basis', 'price',
                                'zone', 'security', 'duplicate_ref'])
def test_timing_adapter_uses_exact_owned_price_zone_chain(gap):
    from tests.test_newbuyer_b2_contract import subject
    context = timing_input()
    if gap == 'permission':
        context['source_use_projection']['source_permissions'][0]['allowed_uses'] = ['CONTEXT']
    elif gap == 'currency':
        context['decision_evidence'][0]['statement']['currency'] = 'KRW'
    elif gap == 'date':
        context['decision_evidence'][1]['as_of'] = '2026-09-01'
    elif gap == 'basis':
        context['decision_evidence'][2]['statement']['price_basis'] = 'adjusted'
    elif gap == 'price':
        context['decision_evidence'][2]['statement']['candle']['close'] = 99
    elif gap == 'zone':
        context['decision_evidence'][1]['statement']['zone_low'] = 80
    elif gap == 'security':
        context['r2_eligible_range_catalog']['tactical_candidates'][0]['security_id'] = 'other'
    elif gap == 'duplicate_ref':
        context['decision_evidence'].append(deepcopy(context['decision_evidence'][0]))
        with pytest.raises(ValueError, match='duplicate_evidence_identity'):
            s.tactical_catalog(context, 'SYN_A', 'security-A')
        return
    sub = subject()
    sub['tactical_catalog'] = s.tactical_catalog(context, 'SYN_A', 'security-A')
    assert b.timing(sub)['state'] == ('FAVORABLE_NOW' if gap is None else 'UNRESOLVED')
