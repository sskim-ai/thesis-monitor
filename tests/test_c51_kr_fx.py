"""KR quote collection, sealed replay and final renderer; all HTTP is synthetic."""
import asyncio
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import json
import socket
from types import SimpleNamespace

import httpx
import pytest

from app.macro.providers.ecos import EcosProvider
from app.macro.providers.ecos_daily_fx import DAILY_FX, TABLE, daily_fx_requests
from app.services.fresh_publication_replay import public_request, replay_fresh_publications
from app.services.production_message_renderer import market_message
from app.services.sealed_fresh_dispatch import read_route, wire_identity
from app.services.unified_snapshot_contract import digest
from app.services.unified_run_artifacts import sha256_bytes
from app.services.unified_source_policy import UnifiedSourcePolicy
from tests.test_c22ab_selected_source import compile_market
from tests.test_c47_optional_night_market import decision
from tests.test_r2b_r5_market_adapter import fixture, project

AT = datetime(2026, 9, 27, 8, tzinfo=timezone.utc)
POLICY = UnifiedSourcePolicy(frozenset({'ecos'}))


@pytest.fixture(autouse=True)
def no_live_network(monkeypatch):
    def deny(*args, **kwargs):
        raise AssertionError('C51_NO_LIVE_NETWORK')
    monkeypatch.setattr(socket.socket, 'connect', deny)
    monkeypatch.setattr(socket, 'getaddrinfo', deny)


def quote_rows(series):
    code, name, _ = DAILY_FX[series]
    values = (('20260924', '918'), ('20260925', '920')) if 'JPY' in series else (
        ('20260923', '1490'), ('20260924', '1500'))
    return [dict(STAT_CODE=TABLE, ITEM_CODE1=code, ITEM_NAME1=name, UNIT_NAME='원',
        TIME=day, DATA_VALUE=value) for day, value in values]


def captured_replay(change=None, series=tuple(DAILY_FX)):
    calls, receipts, bodies = [], [], {}
    def send(request):
        calls.append(request)
        if '/KeyStatisticList/' in request.url.path:
            body = dict(KeyStatisticList=dict(row=[dict(KEYSTAT_NAME='원/달러 환율(종가)',
                DATA_VALUE='1310', CYCLE='20260925', UNIT_NAME='원', CLASS_NAME='환율')]))
            status = 200
        else:
            name = next(s for s, (code, _, _) in DAILY_FX.items() if request.url.path.endswith('/' + code))
            rows = quote_rows(name)
            if change == 'one_date':
                rows = rows[-1:]
            if name.startswith('JPY'):
                if change == 'unit':
                    rows[-1]['UNIT_NAME'] = '달러'
                elif change == 'item':
                    rows[-1]['ITEM_NAME1'] = '원/미국달러(매매기준율)'
                elif change == 'future':
                    rows[-1]['TIME'] = '20260928'
                elif change == 'duplicate':
                    rows.append(deepcopy(rows[-1]))
                elif change == 'transport':
                    raise httpx.ConnectError('synthetic_optional_fx_failure', request=request)
            body = dict(StatisticSearch=dict(row=rows, list_total_count=len(rows)))
            status = 503 if change == 'http' and name.startswith('JPY') else 200
            if change == 'missing' and name.startswith('JPY'):
                body = {'RESULT': {'CODE': 'INFO-200'}}
        response = httpx.Response(status, json=body, request=request)
        artifact = 'synthetic-' + str(len(receipts))
        bodies[artifact] = response.content
        receipts.append(dict(run_id='c51-fx', provider='ecos', artifact=artifact,
            artifact_sha256=sha256_bytes(response.content), requested_at=AT.isoformat(),
            received_at=AT.isoformat(), outcome='HTTP_RESPONSE', http_status=status,
            request=public_request(request)))
        return response
    provider = EcosProvider(httpx.MockTransport(send), clock=lambda: AT, daily_fx=series)
    provider.settings = SimpleNamespace(ecos_api_key='synthetic-key', macro_provider_timeout_seconds=1)
    collected = asyncio.run(provider.collect(AT))
    replayed = replay_fresh_publications(run_id='c51-fx', run_started_at=AT,
        acquisition_cutoff=AT + timedelta(seconds=1), as_of=AT, market_scope='SELECTED_KR', policy=POLICY,
        providers={'ecos': dict(receipts=receipts, bodies=bodies,
            body_hashes={name: sha256_bytes(raw) for name, raw in bodies.items()})})
    return collected, replayed, calls


def projection(publications):
    packet, seed, graph = fixture('kr', run='c51-fx')
    source = graph['markets']['kr']
    values = source['component']['value']
    values['indices'].append(dict(values['indices'][0], symbol='KOSDAQ', label='KOSDAQ',
                                 source_ref='source:second'))
    source['component']['value_sha256'] = digest(values)
    seed['attempt_hashes']['kr'] = digest(source)
    graph.update(publication_context=publications, run_seed_sha256=digest(seed))
    packet.update(publication_context=publications, market_sources=deepcopy(source),
        run_seed_sha256=digest(seed), authority_graph_sha256=digest(graph))
    return project((packet, seed, graph))


def render(publications):
    projected = projection(publications)
    output = dict(decision(projected['context']), market='KR')
    return projected, market_message(SimpleNamespace(market='kr', gen='c51-fx',
        projected={'kr': projected}, markets={'kr': output}, fresh_stocks={}))['text']


def test_kr_plan_has_two_optional_one_attempt_fx_requests_and_us_keeps_one_ecos():
    kr, args, _ = compile_market('kr', '123456')
    us, _, _ = compile_market('us', 'NEWX')
    fx = [d for d in kr['plan'].descriptors if d.provider == 'ecos']
    assert len(fx) == 3
    assert len([d for d in us['plan'].descriptors if d.provider == 'ecos']) == 1
    for descriptor, (series, request) in zip(fx[1:], daily_fx_requests(args['stock'].frozen_at, 'PLAN_CREDENTIAL')):
        assert descriptor.subject == series and descriptor.endpoint_operation == 'StatisticSearch'
        assert descriptor.request_json == wire_identity(request, ('PLAN_CREDENTIAL',))
        assert descriptor.max_transport_attempts == 1 and descriptor.mandatory is False
        assert descriptor.consumer_role not in kr['plan'].mandatory_roles
        path = httpx.URL(json.loads(descriptor.request_json)['url']).path
        assert read_route('ecos', 'GET', path)
        assert not read_route('ecos', 'GET', path.replace('731Y001', '731Y003'))


def test_current_capture_replays_to_source_facts_and_actual_kr_market_message():
    collected, replayed, calls = captured_replay()
    assert len(calls) == 3
    assert all('synthetic-key' not in str(r['request']) for r in replayed['providers']['ecos']['original_receipts'])
    projected, text = render(replayed)
    assert '원/달러: 1,310.00원 (2026-09-25 관측)' in text
    assert '원/100엔: 920.00원 (2026-09-25 관측)' in text
    assert '원/유로: 1,500.00원 (2026-09-24 관측)' in text
    assert '원/100엔: 920.00원 (2026-09-25 관측) · +2.00원 (+0.22%, 2026-09-24 대비) · ECOS 일별 환율' in text
    assert '원/유로: 1,500.00원 (2026-09-24 관측) · +10.00원 (+0.67%, 2026-09-23 대비) · ECOS 일별 환율' in text
    assert '92,000' not in text
    facts = projected['packet']['market_context']['fact_catalog']
    rows = {f['fields'].get('series_code'): f for f in facts}
    assert {s: rows[s]['fields']['value'] for s in DAILY_FX} == {
        'JPYKRW100_KR_CLOSE': 920, 'EURKRW_KR_CLOSE': 1500}
    for series in DAILY_FX:
        fact = rows[series]
        assert fact['fact_id'] not in projected['context']['request_eligible_refs']
        assert fact['fields']['publication_context']['direction_eligible'] is False
        assert fact['fields']['fx_quote_unit'] == DAILY_FX[series][2]
    assert len([r for r in collected.observations if r.series_code in DAILY_FX]) == 4


@pytest.mark.parametrize('change', ['unit', 'item', 'future', 'duplicate', 'http', 'transport', 'missing'])
def test_parser_optional_jpy_failure_preserves_other_quotes_and_honest_missing_message(change):
    # Provider/replay behavior only. The existing production transport/account
    # stop on uncertain transport and any external HTTP >=400 remains in force.
    collected, replayed, calls = captured_replay(change)
    assert len(calls) == 3
    assert not any(r.series_code.startswith('JPY') for r in collected.observations)
    assert any(warning.startswith('JPYKRW100_KR_CLOSE:') for warning in collected.warnings)
    _, text = render(replayed)
    assert '원/100엔: 관측값 미확보' in text
    assert '원/달러: 1,310.00원' in text and '원/유로: 1,500.00원' in text


def test_old_single_ecos_capture_remains_readable_without_invented_fx_calls():
    _, replayed, calls = captured_replay(series=())
    assert len(calls) == 1
    _, text = render(replayed)
    assert '원/달러: 1,310.00원' in text
    assert '원/100엔: 관측값 미확보' in text and '원/유로: 관측값 미확보' in text


def test_one_observation_does_not_invent_a_zero_change():
    _, replayed, _ = captured_replay('one_date')
    _, text = render(replayed)
    assert '원/100엔: 920.00원 (2026-09-25 관측) · 비교 자료 미확보' in text
    assert '원/유로: 1,500.00원 (2026-09-24 관측) · 비교 자료 미확보' in text
    assert '+0.00원' not in text


def test_registered_kr_budget_and_metered_endpoints_admit_three_distinct_fx_requests(tmp_path):
    from app.jobs.unified_market_snapshot import LOCAL_CAPS
    from app.services import prospective_class_c_owner as approvals
    from app.services.campaign_runtime_cap import MeteredAsyncTransport, RuntimeCap
    from app.services.selected_run_lifecycle import SelectedRunLedger
    from app.services.selected_source_plan import SelectedConsumerPolicy, compile_selected_plan, request_budget

    _, args, kis = compile_market('kr', '123456')
    args['selected_consumer_policy'] = SelectedConsumerPolicy()
    compiled = compile_selected_plan(compiler_args=args, kis_plan=kis)
    budget = request_budget(compiled, kis)
    caps = LOCAL_CAPS['kr']
    assert caps['ecos'] == 3 and sum(caps.values()) == 334
    assert sum(LOCAL_CAPS['us'].values()) == 710
    assert budget['total'] <= sum(caps.values())
    assert all(count <= caps.get(provider, 0) for provider, count in budget['providers'].items())
    endpoints = {provider: [] for provider in caps}
    endpoints['ecos'] = [dict(methods=['GET'], host='ecos.bok.or.kr', prefix='/api/' + operation + '/',
        endpoint='ECOS_' + operation.upper(), path_contains_credentials=True)
        for operation in ('KeyStatisticList', 'StatisticSearch')]
    now = datetime.now(timezone.utc)
    approval = approvals.record_backend_approval(approvals.ApprovalDecision(
        event_id='C51_SYNTHETIC_FX', approved=True, user_message_sha256=digest('TEST_ONLY'),
        effective_at=now-timedelta(seconds=1), expires_at=now+timedelta(hours=1),
        subjects=('TEST', '123456')))
    journal = SelectedRunLedger(path=tmp_path/'campaign.jsonl', approval=approval,
        master_id='C51_SYNTHETIC_FX', children={'us': dict(generation='FX_US', subjects=['TEST']),
            'kr': dict(generation='FX_KR', subjects=['123456'])},
        provider_caps=caps, max_http=sum(caps.values()), max_models=14,
        database_identity={'synthetic': True}, runtime_cap=dict(endpoints=endpoints,
            stop_on_first_external_failure=True))
    cap = RuntimeCap(journal.worker_binding())
    requests = [httpx.Request('GET',
        'https://ecos.bok.or.kr/api/KeyStatisticList/synthetic-secret/json/kr/1/100'),
        *(request for _, request in daily_fx_requests(args['stock'].frozen_at, 'synthetic-secret'))]
    calls = []
    async def run():
        transport = MeteredAsyncTransport(binding=journal.worker_binding(), market='kr', phase='SOURCE',
            owner='SelectedSourceDispatcher', inner=httpx.MockTransport(
                lambda request: calls.append(request) or httpx.Response(200, json={})))
        for request in requests[:2]:
            assert (await transport.handle_async_request(request)).status_code == 200
        assert cap.state()['total'] == 2
        with pytest.raises(ValueError, match='CAP_EXHAUSTED_OR_ATTEMPT_ALREADY_USED'):
            await transport.handle_async_request(requests[1])
        assert cap.state()['total'] == 2
        assert (await transport.handle_async_request(requests[2])).status_code == 200
    asyncio.run(run())
    assert len(calls) == cap.state()['total'] == 3
    assert cap.state()['providers']['ecos'] == 3
    assert len({row['request_sha256'] for row in cap.state()['attempts'].values()}) == 3
    assert 'synthetic-secret' not in journal.path.read_text()
