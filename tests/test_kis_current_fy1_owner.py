"""All positive action-coverage fixtures are synthetic, not official source proof."""
from copy import deepcopy
from hashlib import sha256
import json

import httpx
import pytest

from scripts import kis_current_fy1_owner as p
from scripts import kis_current_fy1_probe as t
from scripts.kis_eps_wire_calibration import sealed
from scripts.kis_estimate_capability_probe import Credentials, ProbeStop
from scripts.kis_fy1_semantic_owner import Evidence, SemanticGap

CODE = '123456'
ASOF = '2026-10-01T12:00:00+09:00'


def ev(value):
    raw = json.dumps(value).encode()
    return Evidence(raw, sha256(raw).hexdigest())


def reseal(receipt, **changes):
    receipt = deepcopy(receipt)
    receipt.pop('receipt_sha256', None)
    return sealed({**receipt, **changes})


def eps(value='30'):
    return sealed({'contract': p.SNAPSHOT, 'state': 'KIS_FY1_EPS_ESTIMATE_SNAPSHOT',
        'security_code': CODE, 'value': value, 'metric': 'EPS', 'unit': 'KRW_PER_SHARE',
        'source_kind': 'KIS_HOUSE_RESEARCH_NOT_CONSENSUS', 'estdate': '2026-07-01',
        'period': '2026.12E', 'estimate_sha256': 'a' * 64, 'overall_direction_use': False,
        'allowed_roles': p.ALLOWED_ROLES, 'prohibited_roles': p.PROHIBITED_ROLES,
        'security': {'state': 'QUALIFIED', 'request_code': CODE, 'short_code': CODE,
            'provider_product_number': '00000A' + CODE, 'estimate_sht_cd': 'A' + CODE,
            'product_type': '300', 'standard_code': 'KR7' + CODE + '007'}})


def docs():
    return {'price': {'params': {'FID_ORG_ADJ_PRC': {'0': 'UNADJUSTED', '1': 'ADJUSTED'}}},
        'actions': {f: {'path': '/uapi/domestic-stock/v1/ksdinfo/' + spec[0]} for f, spec in p.ROUTES.items()}}


def wire_receipt(evidence, path, tr, params, *, continuation='', request_cont=''):
    return {'http_status': 200, 'raw_sha256': evidence.sha256,
        'ended_at': '2026-10-01T12:02:00+09:00', 'response_headers': {'tr_cont': continuation},
        'request': {'method': 'GET', 'path': path, 'tr_id': tr, 'params': params,
            'redirects': False, 'tr_cont': request_cont, 'started_at': '2026-10-01T12:01:00+09:00'}}


def price_inputs():
    raw = {'rt_cd': '0', 'output': [
        {'stck_bsop_date': '20261001', 'stck_clpr': '999', 'stck_lwpr': '990', 'stck_hgpr': '999', 'stck_oprc': '995'},
        {'stck_bsop_date': '20260930', 'stck_clpr': '100', 'stck_lwpr': '90', 'stck_hgpr': '110', 'stck_oprc': '95'}]}
    source = ev(raw)
    return {'eps': eps(), 'security': {'ticker': CODE, 'canonical_security_id': 'synthetic-security',
        'standard_code': eps()['security']['standard_code'], 'exchange': 'KRX', 'currency': 'KRW'},
        'evidence': source, 'receipt': wire_receipt(source, p.PRICE_PATH, p.PRICE_TR, p.price_params(CODE)),
        'calendar': p.calendar_receipt(ASOF), 'documentation': docs()}


def owned_actions(price, **changes):
    """Hypothetical independent effective-date authority, not KIS raw schedule inference."""
    return sealed({'contract': p.ACTION, 'state': 'NO_SHARE_UNIT_CHANGE_IN_WINDOW',
        'security_code': CODE, 'canonical_security_id': price['canonical_security_id'],
        'estimate_date': eps()['estdate'], 'price_date': price['session_date'],
        'share_unit_changing': False, 'queried_families': list(p.ROUTES), 'denial_reasons': [], **changes})


def family(f, rows=None, **kwargs):
    evidence = ev({'rt_cd': '0', 'output1': rows or []})
    path, tr, _ = p.ROUTES[f]
    receipt = wire_receipt(evidence, '/uapi/domestic-stock/v1/ksdinfo/' + path, tr,
        p.action_params(f, '2026-07-01', '2026-09-30'), **kwargs)
    return evidence, receipt


def test_unadjusted_completed_close_and_source_reproduction():
    inputs = price_inputs()
    result = p.price_receipt(**inputs)
    assert result['close'] == '100' and result['session_date'] == '2026-09-30'
    assert result['fid_org_adj_prc'] == '0'
    assert result['excluded_rows'] == [{'session': '2026-10-01', 'reason': 'INCOMPLETE_OR_LATER'}]
    p.validate_price_receipt(result, **inputs)
    with pytest.raises(SemanticGap):
        p.validate_price_receipt(reseal(result, close='101'), **inputs)


@pytest.mark.parametrize('change', [
    lambda i: i['receipt']['request']['params'].update(FID_ORG_ADJ_PRC='1'),
    lambda i: i['receipt']['request']['params'].update(FID_INPUT_ISCD='654321'),
    lambda i: i['receipt']['request']['params'].update(FID_COND_MRKT_DIV_CODE='UN'),
    lambda i: i['receipt'].update(raw_sha256='0' * 64),
    lambda i: i['receipt'].update(http_status=302),
    lambda i: i['security'].update(currency='USD'),
    lambda i: i['security'].update(ticker='654321'),
    lambda i: i['security'].update(standard_code='KR7654321007'),
    lambda i: i['calendar'].update(latest_completed_session='2026-10-01'),
    lambda i: i['receipt']['request'].update(started_at='2026-09-30T12:00:00+09:00'),
    lambda i: i['documentation']['price']['params']['FID_ORG_ADJ_PRC'].update({'0': 'ADJUSTED'}),
])
def test_price_identity_currency_adjustment_calendar_negatives(change):
    inputs = price_inputs()
    change(inputs)
    with pytest.raises((SemanticGap, ValueError)):
        p.price_receipt(**inputs)


@pytest.mark.parametrize('mutation', ['missing', 'duplicate', 'wrong_date', 'wrong_security', 'bad_ohlc', 'nonfinite'])
def test_price_target_row_negatives(mutation):
    i = price_inputs()
    raw = i['evidence'].payload()
    if mutation == 'missing':
        raw['output'].pop()
    elif mutation == 'duplicate':
        raw['output'].append(deepcopy(raw['output'][1]))
    elif mutation == 'wrong_date':
        raw['output'][1]['stck_bsop_date'] = '20260929'
    elif mutation == 'wrong_security':
        raw['output'][1]['sht_cd'] = '654321'
    else:
        raw['output'][1]['stck_clpr'] = '120' if mutation == 'bad_ohlc' else 'NaN'
    i['evidence'] = ev(raw)
    i['receipt']['raw_sha256'] = i['evidence'].sha256
    with pytest.raises(SemanticGap):
        p.price_receipt(**i)


@pytest.mark.parametrize(('at', 'expected'), [
    ('2026-10-01T15:29:59+09:00', '2026-09-30'),
    ('2026-10-01T15:30:00+09:00', '2026-10-01'),
    ('2026-09-27T12:00:00+09:00', '2026-09-23'),
])
def test_calendar_recomputed_no_intraday_or_holiday_guess(at, expected):
    assert p.calendar_receipt(at)['latest_completed_session'] == expected


def test_successful_queries_do_not_prove_effective_window_absence():
    families = {f: p.action_family_receipt(f, '2026-07-01', '2026-09-30', [family(f)], docs()) for f in p.ROUTES}
    assert all(f['state'] == 'COMPLETE_QUERY' for f in families.values())
    receipt = p.compatibility_receipt(eps(), p.price_receipt(**price_inputs()), families)
    assert receipt['state'] == 'CORPORATE_ACTION_SOURCE_INCOMPLETE'
    assert receipt['share_unit_changing'] is None
    assert len(receipt['denial_reasons']) == 5


@pytest.mark.parametrize('mutation', ['failed', 'missing_output', 'wrong_filter', 'continuation', 'duplicate_page', 'wrong_security'])
def test_action_source_completeness(mutation):
    f = 'paidin_capin'
    evidence, receipt = family(f)
    pages = [(evidence, receipt)]
    if mutation == 'failed':
        receipt['http_status'] = 500
    elif mutation == 'missing_output':
        evidence = ev({'rt_cd': '0'})
        receipt['raw_sha256'] = evidence.sha256
        pages = [(evidence, receipt)]
    elif mutation == 'wrong_filter':
        receipt['request']['params']['GB1'] = '1'
    elif mutation == 'continuation':
        receipt['response_headers']['tr_cont'] = 'M'
    elif mutation == 'duplicate_page':
        receipt['response_headers']['tr_cont'] = 'M'
        second = deepcopy(receipt)
        second['request']['tr_cont'] = 'N'
        second['response_headers']['tr_cont'] = 'D'
        pages.append((evidence, second))
    else:
        pages = [family(f, [{'sht_cd': 'A123456'}])]
    result = p.action_family_receipt(f, '2026-07-01', '2026-09-30', pages, docs())
    assert result['state'] == 'SOURCE_INCOMPLETE'


def test_all_five_effective_families_no_event_and_cash_dividend():
    assert p.effective_window_state([], '2026-07-01', '2026-09-30', complete_families=p.ROUTES) == 'NO_SHARE_UNIT_CHANGE_IN_WINDOW'
    assert p.effective_window_state([{'family': 'CASH_DIVIDEND'}], '2026-07-01', '2026-09-30',
        complete_families=p.ROUTES) == 'NO_SHARE_UNIT_CHANGE_IN_WINDOW'
    assert p.effective_window_state([], '2026-07-01', '2026-09-30',
        complete_families=['bonus_issue']) == 'CORPORATE_ACTION_SOURCE_INCOMPLETE'


@pytest.mark.parametrize('family_name', p.ROUTES)
@pytest.mark.parametrize(('day', 'blocked'), [('2026-06-30', False), ('2026-07-01', False),
    ('2026-07-02', True), ('2026-09-30', True), ('2026-10-01', False)])
def test_each_share_unit_family_effective_date_not_announcement(family_name, day, blocked):
    event = {'family': family_name, 'effective_date': day,
             'effective_date_authority': 'OWNED_SECURITY_UNIT_EFFECTIVE_DATE', 'announcement_date': '2026-06-01'}
    state = p.effective_window_state([event], '2026-07-01', '2026-09-30', complete_families=p.ROUTES)
    assert state == ('SHARE_UNIT_CHANGE_REQUIRES_ADJUSTMENT' if blocked else 'NO_SHARE_UNIT_CHANGE_IN_WINDOW')


def test_record_and_listing_dates_never_promoted_to_effective():
    with pytest.raises(SemanticGap, match='EFFECTIVE_DATE'):
        p.evaluate_effective_events([{'family': 'paidin_capin', 'effective_date': '2026-07-15',
            'effective_date_authority': 'RECORD_DATE'}], '2026-07-01', '2026-09-30')


def test_exact_quotient_rounding_and_provenance():
    price = p.price_receipt(**price_inputs())
    actions = owned_actions(price)
    result = p.current_fper(eps(), price, actions)
    assert result['state'] == 'QUALIFIED'
    assert result['exact_quotient'] == {'numerator': '10', 'denominator': '3'}
    assert result['display_value'] == '3.33' and result['decimal_value_is_rounded_expansion']
    assert result['price_receipt_sha256'] == price['receipt_sha256']
    assert result['corporate_action_receipt_sha256'] == actions['receipt_sha256']
    assert result['allowed_roles'] == list(p.ALLOWED_ROLES) and not result['overall_direction_use']
    p.validate_current_fper(result, eps(), price, actions)
    with pytest.raises(SemanticGap):
        p.validate_current_fper(reseal(result, display_value='9.99'), eps(), price, actions)


@pytest.mark.parametrize('value', ['0', '-2'])
def test_qualified_nonpositive_eps_is_nm(value):
    result = p.current_fper(eps(value), None, None)
    assert result['state'] == 'NOT_MEANINGFUL' and result['display_value'] == 'N/M'
    assert result['value'] is None


def test_missing_eps_not_nm_and_no_action_adjustment():
    assert p.current_fper(None, None, None)['state'] == 'UNAVAILABLE_EPS'
    price = p.price_receipt(**price_inputs())
    result = p.current_fper(eps(), price, owned_actions(price,
        state='SHARE_UNIT_CHANGE_REQUIRES_ADJUSTMENT', share_unit_changing=True))
    assert result['state'] == 'UNAVAILABLE_POST_ESTIMATE_SHARE_UNIT_CHANGE'
    assert result['value'] is None


@pytest.mark.parametrize(('field', 'value'), [('security_code', '654321'), ('currency', 'USD'),
    ('fid_org_adj_prc', '1'), ('price_basis', 'adjusted_close'), ('session_date', '2026-10-01'),
    ('overall_direction_use', True), ('standard_code', 'KR7654321007')])
def test_fper_price_contract_denials(field, value):
    price = p.price_receipt(**price_inputs())
    with pytest.raises(SemanticGap):
        p.current_fper(eps(), reseal(price, **{field: value}), owned_actions(price))


def test_three_metrics_remain_separate_provider_difference_not_rejected():
    price = p.price_receipt(**price_inputs())
    derived = p.current_fper(eps(), price, owned_actions(price))
    provider = reseal(eps(), metric='PER', state='KIS_PROVIDER_FY1_PER_SNAPSHOT', value='9.5', unit='MULTIPLE')
    trailing = {'value': '75', 'source': 'existing_current_per'}
    before = deepcopy((trailing, provider, derived))
    metrics = p.metric_set(trailing, provider, derived)
    assert metrics['current_trailing_per']['value'] == '75'
    assert metrics['kis_provider_fy1_per']['value'] == '9.5'
    assert metrics['current_price_fy1_fper']['display_value'] == '3.33'
    assert metrics['provider_per_diagnostic']['state'].startswith('DIAGNOSTIC_ONLY')
    assert before == (trailing, provider, derived)


def test_readonly_transport_pacing_budget_no_retry_or_estimate(tmp_path, monkeypatch):
    requests = [{'kind': 'price', 'subject': CODE, 'path': p.PRICE_PATH,
                 'tr_id': p.PRICE_TR, 'params': p.price_params(CODE)}]
    plan = {'requests': requests}
    waits = []
    monkeypatch.setattr(t.time, 'sleep', waits.append)
    with httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(200,
            json={'rt_cd': '0', 'output': []}, headers={'tr_cont': 'D'}))) as client:
        probe = t.CurrentProbe(tmp_path, Credentials('synthetic-key', 'synthetic-secret'), client, plan=plan)
        probe.token = 'synthetic-token'
        probe.fetch(requests[0])
        with pytest.raises(ProbeStop):
            probe.fetch(requests[0])
        with pytest.raises(ProbeStop):
            probe.fetch({**requests[0], 'path': '/uapi/domestic-stock/v1/trading/order-cash'})
        assert probe.counters()['data_total'] == 1 and probe.counters()['estimate_refresh'] == 0
        assert waits[0] > 1
        text = ''.join(p.read_text() for p in tmp_path.rglob('*') if p.is_file())
        assert 'synthetic-key' not in text and 'synthetic-secret' not in text
        assert 'synthetic-token' not in text


def test_rate_limit_stops_without_retry(tmp_path, monkeypatch):
    request = {'kind': 'price', 'subject': CODE, 'path': p.PRICE_PATH, 'tr_id': p.PRICE_TR, 'params': p.price_params(CODE)}
    monkeypatch.setattr(t.time, 'sleep', lambda _: None)
    with httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(200,
            json={'rt_cd': '1', 'msg_cd': 'EGW00201'}))) as client:
        probe = t.CurrentProbe(tmp_path, Credentials('synthetic-key', 'synthetic-secret'), client, plan={'requests': [request]})
        probe.token = 'synthetic-token'
        with pytest.raises(ProbeStop, match='RATE_LIMIT'):
            probe.fetch(request)
        assert probe.data_count == 1


@pytest.mark.parametrize(('value', 'display'), [('40', '2.50'), ('32', '3.13'), ('800', '0.13')])
def test_stable_half_up_decimal_rounding(value, display):
    price = p.price_receipt(**price_inputs())
    result = p.current_fper(eps(value), price, owned_actions(price))
    assert result['display_value'] == display


@pytest.mark.parametrize('change', [
    {'security_code': '654321'}, {'estimate_date': '2026-07-02'},
    {'price_date': '2026-09-29'}, {'canonical_security_id': 'other-security'},
])
def test_action_identity_window_exact_binding(change):
    price = p.price_receipt(**price_inputs())
    with pytest.raises(SemanticGap, match='ACTION_BINDING'):
        p.current_fper(eps(), price, owned_actions(price, **change))


def test_data_budget_hard_stop_before_network(tmp_path):
    request = {'kind': 'price', 'subject': CODE, 'path': p.PRICE_PATH, 'tr_id': p.PRICE_TR, 'params': p.price_params(CODE)}
    probe = t.CurrentProbe(tmp_path, Credentials('synthetic-key', 'synthetic-secret'), None, plan={'requests': [request]})
    probe.token = 'synthetic-token'
    probe.data_count = 20
    with pytest.raises(ProbeStop, match='SCOPE_GAP'):
        probe.fetch(request)
    assert probe.data_count == 20 and not probe.calls


def test_json_round_trip_retains_exact_receipt_identity():
    inputs = price_inputs()
    inputs['eps'] = json.loads(json.dumps(inputs['eps']))
    p.eps_receipt(inputs['eps'])
    price = p.price_receipt(**inputs)
    actions = owned_actions(price)
    candidate = p.current_fper(inputs['eps'], price, actions)
    p.validate_current_fper(json.loads(json.dumps(candidate)), inputs['eps'], price, actions)
