from copy import deepcopy
import json

import pytest

from scripts import m12ds_r3_policy as p, m12ds_r3_schemas as s
from scripts import m12ds_r3_market as market, m12ds_r3_transport as transport
from scripts import m12ds_r3_valuation_authority as valuation
from scripts.m12cs_r1_provider_schema import project_provider_wire_schema
from scripts.websocket_timeout_runtime_review_first_a_closeout import validate_json_schema
from test_m12ds_r2_judgment_policy import bind, decision, nested, ranges


def source(value=-20, prior=None):
    fields = {'operating_income': {'value': value}}
    if prior is not None:
        basis = dict(period_type='QTD', currency='USD', unit='currency', entity_scope='issuer', statement_basis='CFS')
        fields = dict(metric='operating_income', current_value=value, prior_comparable_value=prior,
                      comparison_type='YOY', current_period=dict(start='2026-04-01', end='2026-06-30', **basis),
                      prior_period=dict(start='2025-04-01', end='2025-06-30', **basis))
    rows = [dict(ref_id='source:business', category='earnings', statement=json.dumps(fields), as_of='2026-06-30')]
    authority = {'authority_records': [dict(ref_id='source:business', authority_state='RESOLVED', allowed_uses=['OVERALL_DIRECTION', 'CONTEXT'])]}
    return rows, authority


def capability(value=-20, prior=None, caution=True, risk=True):
    rows, authority = source(value, prior)
    obs = next(iter(p.observations(rows, authority).values()))
    raw = {'claims': [dict(effect=obs['effect'], text='Observed business fact.', evidence_refs=[obs['source_ref']],
                          observation_ids=[obs['observation_id']], materiality='ACTIVE_MATERIAL_RISK' if risk and value < 0 else 'CONTEXT_ONLY')]}
    if caution:
        raw['claims'].append(dict(effect='CONFIDENCE_ONLY', text='Recurrence remains unproven.', evidence_refs=['source:business'],
                                  observation_ids=[], materiality='CONTEXT_ONLY'))
    core = p.materialize_core('FICTIONAL', raw, rows, authority)
    chain, catalog = bind(core, rows)
    return p.axis_capability(core, chain, catalog, rows), core, chain, catalog, rows


def assert_parity(row, cap, val):
    schema = s.decision_schema(cap, val, {})
    wire, _ = project_provider_wire_schema(schema)
    assert p.validate_decision(row, cap, val)['status'] == 'PASS'
    for shape in (schema, wire):
        assert not validate_json_schema(nested(row), shape)


def test_preprofit_current_loss_review_avoid_not_automatic_sell():
    cap, *_ = capability()
    assert cap['current_stress'] and not cap['sell_eligible']
    row = decision(cap, overall='HOLD', reason='CURRENT_STRESS_WITHOUT_PROVEN_DETERIORATION', holder='REVIEW', buyer='AVOID')
    assert_parity(row, cap, ranges())
    row.update(overall_direction='SELL', overall_reason_class='OBSERVED_NEGATIVE_DOMINANT')
    assert p.validate_decision(row, cap, ranges())['status'] == 'FAIL'
    assert validate_json_schema(nested(row), s.decision_schema(cap, ranges(), {}))


def test_comparable_worsening_permits_sell_not_forces_it():
    cap, *_ = capability(-20, prior=5)
    assert cap['deterioration'] and cap['sell_eligible'] and not cap['current_stress']
    row = decision(cap, overall='SELL', reason='OBSERVED_NEGATIVE_DOMINANT', holder='REVIEW', buyer='AVOID')
    assert_parity(row, cap, ranges())


@pytest.mark.parametrize('field,value', [('currency', 'EUR'), ('entity_scope', 'subsidiary'), ('statement_basis', 'OFS'), ('period_type', 'YTD')])
def test_comparison_basis_mismatch_not_deterioration(field, value):
    rows, authority = source(-20, 5)
    fields = json.loads(rows[0]['statement'])
    fields['prior_period'][field] = value
    rows[0]['statement'] = json.dumps(fields)
    assert not p.observations(rows, authority)


def test_prior_value_without_period_owner_cannot_prove_deterioration():
    rows, authority = source(-20, 5)
    fields = json.loads(rows[0]['statement'])
    fields.pop('prior_period')
    rows[0]['statement'] = json.dumps(fields)
    assert not p.observations(rows, authority)


def test_existing_recomputed_comparison_owner_preserves_flat_period_projection():
    rows, authority = source(-20, 5)
    fields = dict(metric='operating_income', current_value=-20, prior_comparable_value=5,
                  period_start='2026-04-01', period_end='2026-06-30',
                  prior_period_start='2025-04-01', prior_period_end='2025-06-30')
    rows[0]['statement'] = valuation._compact(fields)
    authority['authority_records'][0].update(source_family=p.FAMILY, authority_basis=p.COMPARISON_CONTRACT,
        source_scope='exact_comparative_issuer_business_no_valuation')
    binding = {'source:business': {'fields': fields, 'fact_sha256': 'frozen-owner-digest'}}
    assert next(iter(p.observations(rows, authority, binding).values()))['effect'] == p.Effect.DETERIORATION
    assert not p.observations(rows, authority)
    authority['authority_records'][0]['authority_basis'] = 'unverified'
    assert not p.observations(rows, authority, binding)


@pytest.mark.parametrize('archetype', ['DURABLE_FRANCHISE', 'STRUCTURAL_CYCLICAL_LEADER', 'PROFITABLE_PREMIUM_GROWTH', 'MATURE_VALUE_DEFENSIVE'])
def test_established_positive_allows_buy_with_low_confidence(archetype):
    cap, *_ = capability(20)
    row = decision(cap)
    row['confidence'] = 'LOW'
    val = {**ranges(), 'option': {'archetype': archetype}}
    assert_parity(row, cap, val)
    assert cap['confidence'] and not cap['negative']


def test_realized_impairment_policy_requires_explicit_eligible_ref():
    cap, *_ = capability(-20, prior=5)
    ref = cap['negative'][0]
    cap.update(impairment=[ref], deterioration=[], sell_eligible=[ref])
    row = decision(cap, overall='SELL', reason='OBSERVED_NEGATIVE_DOMINANT', holder='REVIEW', buyer='AVOID')
    assert_parity(row, cap, ranges())
    # No realized-event source adapter exists in this frozen cohort; model wording cannot create one.
    rows, authority = source()
    raw = {'claims': [dict(effect='THESIS_IMPAIRMENT', text='Impaired', evidence_refs=['source:business'],
                           observation_ids=[], materiality='PERSISTENT_OR_IMPAIRED')]}
    with pytest.raises(ValueError, match='impairment_source_unavailable'):
        p.materialize_core('FICTIONAL', raw, rows, authority)


def test_active_adverse_without_discount_precedes_valuation_wait():
    cap, *_ = capability()
    row = decision(cap, overall='HOLD', reason='CURRENT_STRESS_WITHOUT_PROVEN_DETERIORATION', holder='REVIEW', buyer='WAIT')
    assert 'active_adverse_without_compensation_precedes_wait' in p.validate_decision(row, cap, ranges())['errors']
    assert validate_json_schema(nested(row), s.decision_schema(cap, ranges(), {}))
    compensated = {'fundamental_valid': True, 'compensating_discount': True}
    assert_parity(row, cap, compensated)


def test_confidence_cannot_be_a_negative_or_active_risk():
    cap, *_ = capability(20)
    row = decision(cap)
    assert_parity(row, cap, ranges())
    row['contradicting_refs'] = cap['confidence']
    assert p.validate_decision(row, cap, ranges())['status'] == 'FAIL'


def test_serialized_core_restoration_preserves_exact_capability_and_bytes():
    cap, core, chain, catalog, rows = capability()
    serialized = json.loads(json.dumps(core, sort_keys=True))
    serialized['effects'] = dict(reversed(list(serialized['effects'].items())))
    restored = p.canonical_core(serialized)
    actual = p.axis_capability(restored, chain, catalog, rows)
    assert actual == cap
    assert json.dumps(actual, sort_keys=True) == json.dumps(cap, sort_keys=True)
    assert list(restored['effects']) == [c['claim_ref'] for c in core['atomic_claims']]
    altered = deepcopy(serialized)
    next(iter(altered['effects'].values()))['materiality'] = 'PERSISTENT_OR_IMPAIRED'
    with pytest.raises(ValueError, match='binding_drift'):
        p.canonical_core(altered)


def market_packet():
    def fact(kind, code, value):
        return dict(fact_id=f'market:{kind}:{code}', fact_type={'index': 'market_index', 'sector': 'market_sector', 'style': 'market_style'}[kind],
                    as_of_date='2026-09-18', fields=dict(series_code=code, return_pct=value, quality='fresh'))
    facts = [fact('index', 'GENERIC_INDEX', 2), fact('sector', 'GENERIC_SECTOR', 3), fact('style', 'GENERIC_STYLE', 1)]
    facts.append(dict(fact_id='market:relative:generic', fact_type='market_sector_relative', as_of_date='2026-09-18',
                      fields={'source_fact_ids': [facts[1]['fact_id'], facts[0]['fact_id']], 'relative_return_pct': 1}))
    return dict(market='us', assessment_date='2026-09-21', market_context=dict(fact_catalog=facts,
        coverage={s: {'status': 'available', 'available_series': [code]} for s, code in
                  [('indices', 'GENERIC_INDEX'), ('sectors', 'GENERIC_SECTOR'), ('style_size', 'GENERIC_STYLE')]},
        adapter_context={'session_context': {'latest_completed_regular_session_date': '2026-09-18'}}))


def test_market_eligible_proxy_and_relative_parity_without_stock_feedback():
    packet = market_packet()
    before = deepcopy(packet)
    context = market.market_context(packet)
    assert len(context['facts']) == 4
    assert context['packet_eligible_refs'] == context['request_eligible_refs'] == sorted(context['facts'])
    assert packet == before and context['stock_feedback'] is False


@pytest.mark.parametrize('field,value', [('structured_state', 'SOURCE_UNAVAILABLE'), ('renderer_only', True), ('today_signal_eligible', False)])
def test_market_row_denial_overrides_available_coverage(field, value):
    packet = market_packet()
    packet['market_context']['fact_catalog'][0]['fields'][field] = value
    context = market.market_context(packet)
    assert 'market:index:GENERIC_INDEX' not in context['facts']
    assert 'market:relative:generic' not in context['facts']


def test_future_market_session_cannot_be_rescued_by_adapter_or_coverage():
    packet = market_packet()
    fact = packet['market_context']['fact_catalog'][0]
    fact['as_of_date'] = '2026-09-21'
    packet['market_context']['adapter_context']['indices'] = [dict(source_ref=fact['fact_id'], as_of_date='2026-09-21', return_pct=2)]
    context = market.market_context(packet)
    assert fact['fact_id'] not in context['facts']


def earnings_fixture():
    periods = ['2025-09-30', '2025-12-31', '2026-03-31', '2026-06-30']
    fields = {'ttm_eps': 4.0, 'trailing_pe': 10.0}
    quality = dict(decision_version='financial-quality-taint-v2', state='verified_usable', prose_eligible=True,
                   lineage_verification_status='verified', denial_reason=None, quality_reason_codes=[], source_type='derived_trailing',
                   dependency_fields=['earnings_quarter_series.eps'], dependency_periods=periods)
    fact = dict(fact_id='valuation:trailing_earnings', fact_type='valuation_interpretation', as_of_date='2026-09-18',
                fields=fields, valuation_scope='listed_security', interpretation_eligible=True, prose_eligible=True,
                field_quality={'fields.' + k: deepcopy(quality) for k in fields})
    val = dict(currency='USD', eps_currency='USD', eps_security_basis='current_security',
               security_identity_decision_version='security-identity-v2', security_identity_verification_status='verified',
               security_identity_state='verified_non_depositary', resolved_security_type='common_stock', is_depositary_security=False,
               trailing_pe_basis_status='directly_comparable', trailing_pe_basis_conflict=False, ttm_eps_usable=True,
               ttm_contains_preliminary=False, ttm_period_start=periods[0], ttm_period_end=periods[-1], **fields,
               financial_quality={'fields': {k: deepcopy(quality) for k in fields}},
               earnings_quarter_series=[dict(period=d, eps=1.0, filing='2026-08-01', normalized_eps_usable=True,
                   context_usable=True, eps_security_basis='current_security', eps_currency='USD', share_basis='reported_diluted_eps') for d in periods])
    stock = dict(ticker='FICTIONAL', valuation=val, fact_catalog=[fact])
    row = dict(ref_id='canonical:valuation:trailing_earnings', source_ref='stock.fact_catalog.valuation:trailing_earnings',
               label='valuation_interpretation', as_of=fact['as_of_date'], statement=valuation._compact(fields), numeric_prose_eligible=False)
    record = dict(source_metadata_sha256=p.canonical_sha256(row))
    return row, stock, {'assessment_date': '2026-09-21'}, record


def test_exact_security_earnings_fields_allow_valuation_without_prose_permission_widening():
    args = earnings_fixture()
    receipt = valuation.earnings_receipt(*args)
    assert receipt['status'] == 'PASS'
    assert not receipt['numeric_prose_permission_changed'] and not args[0]['numeric_prose_eligible']


@pytest.mark.parametrize('missing', [None, 'forward_eps_share_basis', 'forward_eps_security_basis', 'forward_eps_currency'])
def test_forward_entitlement_requires_its_own_denominator_not_trailing(missing):
    row, stock, packet, record = earnings_fixture()
    val, fact = stock['valuation'], stock['fact_catalog'][0]
    fields = {'forward_eps': 4.0, 'forward_pe': 10.0}
    quality = deepcopy(fact['field_quality']['fields.ttm_eps'])
    quality.update(source_type='consensus_forward', dependency_periods=['2027-06-30'],
                   dependency_fields=['independent_provider_consensus', 'verified_per_security_basis'])
    fact.update(fact_id='valuation:consensus_forward_earnings', fields=fields,
                field_quality={'fields.' + k: deepcopy(quality) for k in fields})
    val.update(**fields, forward_pe_source='consensus_forward', forward_pe_input_period='2027-06-30',
               forward_pe_basis_status='directly_comparable', forward_pe_basis_conflict=False,
               forward_eps_security_basis='current_security', forward_eps_currency='USD', forward_eps_share_basis='diluted_eps')
    val['financial_quality']['fields'].update({k: deepcopy(quality) for k in fields})
    row.update(ref_id='canonical:' + fact['fact_id'], source_ref='stock.fact_catalog.' + fact['fact_id'], statement=valuation._compact(fields))
    record['source_metadata_sha256'] = p.canonical_sha256(row)
    if missing:
        val.pop(missing)
    assert valuation.earnings_receipt(row, stock, packet, record)['status'] == ('FAIL' if missing else 'PASS')


@pytest.mark.parametrize('change', ['security', 'currency', 'share_basis', 'future_filing', 'period', 'value', 'metadata', 'denied_field', 'missing_field_owner'])
def test_earnings_tag_alone_never_grants_valuation(change):
    row, stock, packet, record = earnings_fixture()
    val, fact = stock['valuation'], stock['fact_catalog'][0]
    if change == 'security':
        val['is_depositary_security'] = True
    elif change == 'currency':
        val['eps_currency'] = 'EUR'
    elif change == 'share_basis':
        val['earnings_quarter_series'][0]['eps_security_basis'] = 'ordinary_share'
    elif change == 'future_filing':
        val['earnings_quarter_series'][0]['filing'] = '2026-09-22'
    elif change == 'period':
        val['ttm_period_start'] = '2026-01-01'
    elif change == 'value':
        val['ttm_eps'] = 5.0
    elif change == 'metadata':
        row['statement'] = '{}'
    elif change == 'denied_field':
        fact['field_quality']['fields.ttm_eps']['prose_eligible'] = False
    else:
        fact['field_quality'].clear()
    assert valuation.earnings_receipt(row, stock, packet, record)['status'] == 'FAIL'


@pytest.mark.parametrize('code,events,expected', [
    ('TRANSPORT_TIMEOUT', set(), 'TRANSIENT'), ('PROCESS_NONZERO', {'turn.started'}, 'TRANSIENT'),
    ('PROCESS_NONZERO', set(), 'BATCH_LOCAL'), ('FINAL_OUTPUT_EMPTY', {'turn.started'}, 'TRANSIENT'),
    ('FINAL_OUTPUT_MALFORMED', {'turn.started'}, 'BATCH_LOCAL'), ('SCHEMA_REJECT', {'turn.started'}, 'SYSTEMIC'),
    ('AUTH_FAILED', set(), 'SYSTEMIC'), ('BINARY_IDENTITY_MISMATCH', set(), 'SYSTEMIC')])
def test_transient_classification_is_explicit_and_narrow(code, events, expected):
    assert transport.classify(code, output_present=False, event_types=events, stderr='') == expected


@pytest.mark.parametrize('message', ['UnknownIssuer', 'invalid peer certificate', 'authentication failed', 'attempt to write a readonly database'])
def test_security_failure_never_retries(message):
    assert transport.classify('TRANSPORT_TIMEOUT', output_present=False, event_types={'turn.started'}, stderr=message) == 'SYSTEMIC'


def test_model_response_or_tool_event_precludes_transient_retry():
    assert transport.classify('TRANSPORT_TIMEOUT', output_present=True, event_types={'turn.started'}, stderr='') == 'BATCH_LOCAL'
    assert transport.classify(None, output_present=True, event_types={'turn.started'}, stderr='', tool_event=True) == 'SYSTEMIC'
