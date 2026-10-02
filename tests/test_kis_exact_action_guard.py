"""Fictional exact-security policy fixtures; never live absence evidence."""
from copy import deepcopy
import json

import httpx
import pytest

from scripts import kis_current_fy1_owner as p
from scripts import kis_exact_action_guard as g
from scripts import kis_exact_action_probe as t
from scripts.kis_estimate_capability_probe import Credentials, ProbeStop
from scripts.kis_fy1_semantic_owner import SemanticGap
from test_kis_current_fy1_owner import CODE, eps, ev, price_inputs, reseal, wire_receipt


def docs(cursor=False):
    return {'actions': {v: {'path': '/uapi/domestic-stock/v1/ksdinfo/' + spec[0],
        'tr_id': spec[1], 'extra_params': spec[2], 'method': 'GET', 'security_filter': 'EXACT_SHT_CD',
        'source_sha256': 'a' * 64, 'columns': {f: f for f in g.DATE_FIELDS[v]},
        'cursor_binding': {'response_location': 'body', 'field': 'cts', 'request_param': 'CTS',
                           'source_sha256': 'b' * 64} if cursor else None}
        for v, spec in g.VARIANTS.items()}}


def page(variant='rev_split', rows=None, status='E', cursor='', output_cursor=None, index=1):
    payload = {'rt_cd': '0', 'output1': rows or []}
    if output_cursor is not None:
        payload['cts'] = output_cursor
    evidence = ev(payload)
    route = docs()['actions'][variant]
    receipt = wire_receipt(evidence, route['path'], route['tr_id'],
        g.action_params(variant, CODE, g.envelope('2026-07-01', '2026-09-30'), cursor),
        continuation=status, request_cont='' if index == 1 else 'N')
    return evidence, receipt


def family(variant='rev_split', pages=None, documentation=None):
    return g.family_receipt(variant, CODE, '2026-07-01', '2026-09-30',
        pages if pages is not None else [page(variant)], documentation or docs())


def guard(**changes):
    families = {v: family(v) for v in g.VARIANTS}
    families.update(changes)
    return g.compatibility_receipt(eps(), p.price_receipt(**price_inputs()), families)


def row(variant='rev_split', day='2026-06-30'):
    return {'sht_cd': CODE, **{k: day for k in g.DATE_FIELDS[variant]}}


@pytest.mark.parametrize('variant', g.VARIANTS)
def test_each_exact_route_and_wide_window(variant):
    window = g.envelope('2026-07-01', '2026-09-30')
    assert window['start'] == '2025-07-01' and window['end'] == '2027-09-30'
    params = g.action_params(variant, CODE, window)
    assert params['SHT_CD'] == CODE and params['F_DT'] == '20250701'
    assert params['T_DT'] == '20270930' and params['CTS'] == ''
    if 'gb' in variant:
        assert params['GB1'] == variant[-1]
    assert family(variant)['state'] == 'COMPLETE_QUERY'


def test_leap_day_envelope_calendar_days_not_year_replace():
    window = g.envelope('2024-02-29', '2024-02-29')
    assert window['start'] == '2023-03-01' and window['end'] == '2025-02-28'
    with pytest.raises(SemanticGap):
        g.envelope('2026-10-01', '2026-09-30')


@pytest.mark.parametrize('code', ['', 'A123456', '12345', '12345K', '654321'])
def test_no_blank_global_filter_or_cross_security_binding(code):
    e, receipt = page()
    receipt['request']['params']['SHT_CD'] = code
    result = family(pages=[(e, receipt)])
    assert result['state'] == g.INCOMPLETE


@pytest.mark.parametrize('code', ['654321', '00088K', 'A123456'])
def test_conflicting_exact_response_fails_without_global_parser_poison(code):
    unrelated = {'sht_cd': code}
    assert g.row_identity(unrelated, CODE) == 'CONFLICT'
    assert family()['state'] == 'COMPLETE_QUERY'
    conflict = family(pages=[page(rows=[unrelated])])
    assert conflict['state'] == g.CONFLICT
    assert guard(rev_split=conflict)['state'] == g.CONFLICT


def test_counterparty_is_not_primary_security_identity():
    r = row('merger_split') | {'cust_cd': '12345K', 'opp_cust_cd': '654321'}
    assert family('merger_split', [page('merger_split', [r])])['state'] == 'COMPLETE_QUERY'
    assert g.row_identity({'sht_cd': CODE, 'short_code': '654321'}, CODE) == 'CONFLICT'


@pytest.mark.parametrize('variant', g.VARIANTS)
@pytest.mark.parametrize(('day', 'blocks'), [('2026-06-30', False), ('2026-07-01', False),
    ('2026-07-02', True), ('2026-09-30', True), ('2026-10-01', False)])
def test_all_date_families_critical_boundary(variant, day, blocks):
    decision = g.event_decision(variant, row(variant, day), '2026-07-01', '2026-09-30', docs()['actions'][variant]['columns'])
    assert decision['blocks'] is blocks and not decision['effective_date_inferred']


@pytest.mark.parametrize('value', ['', None, '20261301', '20261001~20260901', '26/09/01', '2026-07-01~'])
def test_ambiguous_dates_fail_closed(value):
    r = row() | {'td_stop_dt': value}
    decision = g.event_decision('rev_split', r, '2026-07-01', '2026-09-30', docs()['actions']['rev_split']['columns'])
    assert decision['blocks'] and decision['classification'] == 'AMBIGUOUS_EXACT_SECURITY_ACTION'


@pytest.mark.parametrize('dates', [
    {'record_date': '2026-06-01', 'list_dt': '2026-10-05', 'td_stop_dt': '20260601~20261005'},
    {'record_date': '2026-06-01', 'list_dt': '2026-10-05', 'td_stop_dt': '2026-06-01'},
])
def test_straddling_is_blocked(dates):
    decision = g.event_decision('rev_split', {'sht_cd': CODE, **dates}, '2026-07-01', '2026-09-30', docs()['actions']['rev_split']['columns'])
    assert decision['blocks'] and decision['classification'] == 'STRADDLING_ACTION_PROCESS'


def test_source_dates_remain_separate_and_unknown_date_blocks():
    r = row() | {'mystery_dt': '20260601'}
    result = g.event_decision('rev_split', r, '2026-07-01', '2026-09-30', docs()['actions']['rev_split']['columns'])
    assert result['blocks'] and result['source_dates']['mystery_dt'] == '20260601'
    assert 'effective_date' not in result


@pytest.mark.parametrize('status', ['F', 'M', '', None, 'X'])
def test_empty_nonterminal_never_qualifies(status):
    result = family(pages=[page(status=status)])
    assert result['state'] == g.INCOMPLETE
    assert guard(rev_split=result)['state'] == g.INCOMPLETE


@pytest.mark.parametrize('mutation', ['http', 'provider', 'hash', 'route', 'tr', 'start', 'end', 'redirect', 'identity_missing'])
def test_source_binding_negative(mutation):
    e, receipt = page()
    if mutation == 'http':
        receipt['http_status'] = 302
    elif mutation == 'provider':
        e = ev({'rt_cd': '1', 'output1': []})
        receipt['raw_sha256'] = e.sha256
    elif mutation == 'hash':
        receipt['raw_sha256'] = '0' * 64
    elif mutation in {'route', 'tr'}:
        receipt['request']['path' if mutation == 'route' else 'tr_id'] = 'wrong'
    elif mutation in {'start', 'end'}:
        receipt['request']['params']['F_DT' if mutation == 'start' else 'T_DT'] = '20260101'
    elif mutation == 'redirect':
        receipt['request']['redirects'] = True
    else:
        e, receipt = page(rows=[{'name': 'same name'}])
    assert family(pages=[(e, receipt)])['state'] == g.INCOMPLETE


@pytest.mark.parametrize('status', ['M', 'F'])
def test_owned_changed_cursor_can_complete(status):
    pages = [page(rows=[row()], status=status, output_cursor='owned-next'),
             page(rows=[row(day='2026-05-01')], cursor='owned-next', index=2)]
    result = family(pages=pages, documentation=docs(cursor=True))
    assert result['state'] == 'COMPLETE_QUERY'
    assert len(result['pages']) == 2


@pytest.mark.parametrize('bad', ['same_cursor', 'missing_cursor', 'unowned', 'duplicate_rows', 'after_terminal', 'wrong_request'])
def test_continuation_loop_and_binding_denials(bad):
    first = page(rows=[row()], status='M', output_cursor='next')
    second = page(rows=[row(day='2026-05-01')], cursor='next', index=2)
    documentation = docs(cursor=True)
    if bad == 'same_cursor':
        second = page(rows=[row(day='2026-05-01')], status='M', cursor='next', output_cursor='next', index=2)
    elif bad == 'missing_cursor':
        first = page(status='F')
    elif bad == 'unowned':
        documentation = docs()
    elif bad == 'duplicate_rows':
        second = page(rows=[row()], cursor='next', index=2)
    elif bad == 'after_terminal':
        first = page(rows=[row()])
    else:
        second[1]['request']['params']['CTS'] = 'wrong'
    assert family(pages=[first, second], documentation=documentation)['state'] == g.INCOMPLETE


def test_clear_v2_permits_existing_decimal_arithmetic_and_exact_refs():
    price, actions = p.price_receipt(**price_inputs()), guard()
    result = p.current_fper(eps(), price, actions)
    assert actions['state'] == g.CLEAR
    assert result['state'] == 'QUALIFIED' and result['display_value'] == '3.33'
    assert result['exact_quotient'] == {'numerator': '10', 'denominator': '3'}
    assert result['corporate_action_policy'] == g.POLICY
    assert result['corporate_action_receipt_sha256'] == actions['receipt_sha256']
    p.validate_current_fper(json.loads(json.dumps(result)), eps(), price, actions)


def test_event_and_incomplete_and_missing_eps_are_distinct():
    price = p.price_receipt(**price_inputs())
    event = family(pages=[page(rows=[row(day='2026-08-01')])])
    assert p.current_fper(eps(), price, guard(rev_split=event))['state'] == 'UNAVAILABLE_POST_ESTIMATE_SHARE_UNIT_CHANGE'
    assert p.current_fper(eps(), price, guard(rev_split=family(pages=[])))['state'] == 'UNAVAILABLE_CORPORATE_ACTION_SOURCE_INCOMPLETE'
    assert p.current_fper(None, None, None)['state'] == 'UNAVAILABLE_EPS'
    assert p.current_fper(eps('0'), None, None)['state'] == 'NOT_MEANINGFUL'


@pytest.mark.parametrize('field', ['security_code', 'estimate_date', 'price_date', 'policy', 'state'])
def test_guard_tamper_is_rejected_even_resealed(field):
    with pytest.raises(SemanticGap):
        p.current_fper(eps(), p.price_receipt(**price_inputs()), reseal(guard(), **{field: 'wrong'}))


def request():
    contract = docs()['actions']['rev_split']
    return {'subject': CODE, 'variant': 'rev_split', 'path': contract['path'], 'tr_id': contract['tr_id'],
        'params': g.action_params('rev_split', CODE, g.envelope('2026-07-01', '2026-09-30'))}


def test_auth_and_data_completion_pacing_no_secrets(tmp_path, monkeypatch):
    clock = [10.0]
    monkeypatch.setattr(t.time, 'monotonic', lambda: clock[0])
    monkeypatch.setattr(t.time, 'sleep', lambda n: clock.__setitem__(0, clock[0] + n))
    def handler(r):
        clock[0] += 3
        if r.method == 'POST':
            return httpx.Response(200, json={'access_token': 'synthetic-token'})
        return httpx.Response(200, json={'rt_cd': '0', 'output1': []}, headers={'tr_cont': 'E'})
    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        probe = t.ExactActionProbe(tmp_path, Credentials('synthetic-key', 'synthetic-secret'), client,
            plan={'requests': [request()]}, documentation=docs())
        probe.authenticate()
        assert probe.last_finished == 13
        probe.fetch(request())
        wire = json.loads((tmp_path / f'action/{CODE}/rev_split-1-request.json').read_bytes())
        assert wire['started_monotonic'] - wire['previous_completed_monotonic'] >= 1.1
        with pytest.raises(ProbeStop):
            probe.fetch(request())
        content = ''.join(f.read_text() for f in tmp_path.rglob('*') if f.is_file())
        assert all(v not in content for v in ['synthetic-key', 'synthetic-secret', 'synthetic-token'])


@pytest.mark.parametrize('rate', ['EGW00201', 'http429'])
def test_explicit_rate_limit_hard_stops(rate, tmp_path, monkeypatch):
    monkeypatch.setattr(t.time, 'sleep', lambda _: None)
    with httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(
            429 if rate == 'http429' else 200, json={'rt_cd': '1', 'msg_cd': rate}))) as client:
        probe = t.ExactActionProbe(tmp_path, Credentials('synthetic-key', 'synthetic-secret'), client,
            plan={'requests': [request()]}, documentation=docs())
        probe.token, probe.last_finished = 'synthetic-token', t.time.monotonic()
        with pytest.raises(ProbeStop, match='RATE_LIMIT'):
            probe.fetch(request())
        assert probe.counters()['action_data_calls'] == 1 and probe.counters()['retries'] == 0


def test_budget_and_nonapproved_path_rejected_before_network(tmp_path):
    probe = t.ExactActionProbe(tmp_path, Credentials('synthetic-key', 'synthetic-secret'), None,
        plan={'requests': [request()]}, documentation=docs())
    probe.token, probe.last_finished = 'synthetic-token', t.time.monotonic()
    probe.data_count = 60
    with pytest.raises(ProbeStop):
        probe.fetch(request())
    probe.data_count = 0
    with pytest.raises(ProbeStop):
        probe.fetch({**request(), 'path': p.PRICE_PATH})
    assert probe.data_count == 0


def test_six_variants_required_not_five_families():
    families = {v: family(v) for v in g.VARIANTS if v != 'paidin_capin_gb1'}
    result = g.compatibility_receipt(eps(), p.price_receipt(**price_inputs()), families)
    assert result['state'] == g.INCOMPLETE


def test_wrong_family_and_window_cannot_be_rebound():
    bad = reseal(family(), security_code='654321')
    with pytest.raises(SemanticGap, match='BINDING'):
        guard(rev_split=bad)
    bad = reseal(family(), guard_envelope=g.envelope('2026-07-02', '2026-09-30'))
    with pytest.raises(SemanticGap, match='BINDING'):
        guard(rev_split=bad)


def test_existing_rounding_and_valuation_roles_unchanged():
    price = p.price_receipt(**price_inputs())
    for denominator, expected in [('32', '3.13'), ('800', '0.13')]:
        result = p.current_fper(eps(denominator), price, guard())
        assert result['display_value'] == expected
        assert result['allowed_roles'] == list(p.ALLOWED_ROLES)
        assert result['overall_direction_use'] is False
        assert result['rounding_policy'] == p.ROUNDING


def test_alphanumeric_row_in_other_response_does_not_invalidate_clean_family():
    bad = family('merger_split', [page('merger_split', [{'sht_cd': '0043C0'}])])
    clean = family('rev_split')
    assert bad['state'] == g.CONFLICT and clean['state'] == 'COMPLETE_QUERY'


def test_documentation_exact_security_contract_required():
    documentation = deepcopy(docs())
    documentation['actions']['rev_split']['security_filter'] = 'ALL'
    with pytest.raises(SemanticGap):
        family(documentation=documentation)


def test_canonical_json_roundtrip_guard_and_plan_parity():
    price, actions = p.price_receipt(**price_inputs()), guard()
    loaded = json.loads(json.dumps(actions, sort_keys=True))
    g.validate_compatibility(loaded, json.loads(json.dumps(eps())), price)
    assert p.current_fper(eps(), price, loaded) == p.current_fper(eps(), price, actions)


def test_data_to_data_spacing_and_transport_stop(tmp_path, monkeypatch):
    clock = [0.0]
    monkeypatch.setattr(t.time, 'monotonic', lambda: clock[0])
    monkeypatch.setattr(t.time, 'sleep', lambda n: clock.__setitem__(0, clock[0] + n))
    second = {**request(), 'subject': '654321', 'params': {**request()['params'], 'SHT_CD': '654321'}}
    def handler(r):
        clock[0] += 2
        return httpx.Response(200, json={'rt_cd': '0', 'output1': []}, headers={'tr_cont': 'E'})
    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        probe = t.ExactActionProbe(tmp_path, Credentials('synthetic-key', 'synthetic-secret'), client,
            plan={'requests': [request(), second]}, documentation=docs())
        probe.token, probe.last_finished = 'synthetic-token', 0
        probe.fetch(request())
        probe.fetch(second)
        assert clock[0] >= 6.2
        for path in tmp_path.rglob('*-request.json'):
            receipt = json.loads(path.read_bytes())
            assert receipt['started_monotonic'] - receipt['previous_completed_monotonic'] >= 1.1
