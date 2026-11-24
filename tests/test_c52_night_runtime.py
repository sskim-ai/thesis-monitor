"""Optional KRX failures remain bounded without stopping unrelated US work.

Synthetic registration/accounting inputs and mock HTTP only. The original
SelectedSourceDispatcher, sealed receipts and durable run ledger are exercised.
"""
import asyncio
from datetime import datetime, timedelta, timezone
import json
import socket
from types import SimpleNamespace

import httpx
import pytest

from app.services import prospective_class_c_owner as approvals
from app.services.campaign_runtime_cap import OPTIONAL_NIGHT, OptionalNightCollectionError, RuntimeCap
from app.services.sealed_source_transport import CapturedFragment
from app.services.selected_run_lifecycle import SelectedRunLedger
from app.services.selected_source_dispatch import SelectedSourceDispatcher
from app.services.selected_source_plan import SelectedConsumerPolicy, compile_selected_plan
from app.services.unified_live_source_transport import SourceSafetyStop
from app.services.unified_snapshot_contract import digest
from tests.test_c22ab_selected_source import compile_market


@pytest.fixture(autouse=True)
def no_external(monkeypatch):
    def denied(*args, **kwargs):
        raise AssertionError('C52_RUNTIME_NO_REAL_IO')
    monkeypatch.setattr(socket.socket, 'connect', denied)
    monkeypatch.setattr(socket, 'getaddrinfo', denied)


def setup_case(tmp_path, *, enabled=True, optional=True, maximum=8, request_timeout=None):
    _, args, _ = compile_market('us', 'NEWX')
    args['selected_consumer_policy'] = SelectedConsumerPolicy(
        us_night='OPTIONAL_CURRENT_PROBE' if optional else 'ORIGINAL_CURRENT_PROBE_ONLY')
    plan = compile_selected_plan(compiler_args=args)['plan']
    if request_timeout is not None:
        plan = plan.model_copy(update={'descriptors':tuple(
            d.model_copy(update={'timeout_seconds':request_timeout}) if d.provider == 'krx_night_futures' else d
            for d in plan.descriptors)})
    now = datetime.now(timezone.utc)
    approval = approvals.record_backend_approval(approvals.ApprovalDecision(
        event_id='C52_SYNTHETIC_NIGHT', approved=True, user_message_sha256=digest('TEST_ONLY'),
        effective_at=now-timedelta(seconds=1), expires_at=now+timedelta(hours=1),
        subjects=('NEWX', '123456')))
    endpoints = {
        'krx_night_futures': [dict(methods=['GET'], host='data-dbg.krx.co.kr',
            prefix='/svc/apis/drv/fut_bydd_trd', endpoint='KRX_FUTURES_DAILY')],
        'fred': [dict(methods=['GET'], host='api.stlouisfed.org',
            prefix='/fred/series/observations', endpoint='FRED_OBSERVATIONS')],
    }
    ledger = SelectedRunLedger(path=tmp_path/'campaign.jsonl', approval=approval,
        master_id='C52_SYNTHETIC_NIGHT', children={
            'us': dict(generation=plan.generation_id, subjects=['NEWX']),
            'kr': dict(generation='SYNTHETIC_KR', subjects=['123456'])},
        provider_caps={'krx_night_futures': 7, 'fred': 1}, max_http=maximum, max_models=14,
        database_identity={'synthetic': True}, runtime_cap=dict(endpoints=endpoints,
            stop_on_first_external_failure=True,
            **({'optional_night': OPTIONAL_NIGHT} if enabled else {})))
    # Synthetic registration port only; no DB or Source/model acceptance occurs.
    receipt = {'SYNTHETIC': True, 'cutoff': now.isoformat()}
    ledger._event('DB_INTENT')
    ledger._event('REGISTRATION', selects=1, receipt=receipt, sha256=digest(receipt))
    ledger._event('PLAN', market='us', sha256=plan.plan_sha256)
    ledger._event('PLAN', market='kr', sha256=digest('SYNTHETIC_KR_PLAN'))
    run = object.__new__(SelectedSourceDispatcher)
    run.plan, run.run_ledger = plan, ledger
    run.admission = {'SYNTHETIC_TEST_NO_SOURCE_RIGHTS': True}
    run._require_current = lambda: None
    run._initialize(root=tmp_path/'dispatch', secrets=())
    night = next(d for d in plan.descriptors if d.provider == 'krx_night_futures')
    fred = next(d for d in plan.descriptors if d.provider == 'fred')
    return run, ledger, night, fred


def execute(run, descriptor, respond):
    wire = json.loads(descriptor.request_json)
    request = httpx.Request(wire['method'], wire['url'], headers=wire['headers'], content=wire['body'].encode())
    return asyncio.run(run.execute(descriptor.logical_request_id, request,
        transport=httpx.MockTransport(respond), normalize=CapturedFragment(descriptor)))


def enter_model_budget(ledger):
    # The downstream admission ports are synthetic; the original durable state
    # transitions and before_model physical-failure check remain unchanged.
    for market in ('us', 'kr'):
        ledger.source_captured(market)
        ledger._event('SOURCE', market=market, sha256=digest('SYNTHETIC_SOURCE_'+market))
    for market in ('us', 'kr'):
        ledger._event('MODEL_PLAN', market=market, sha256=digest('SYNTHETIC_MODEL_'+market),
            slots=1, slot_ids=['MARKET_'+market.upper()])
    plan = SimpleNamespace(sha256=digest('SYNTHETIC_MODEL_us'), cohort=SimpleNamespace(run_id='SYNTHETIC_MODEL'))
    key = ledger.before_model(plan, {'market':'us', 'slot_id':'MARKET_US'})
    assert key.startswith('MODEL:')
    ledger.result(key, ok=True)


@pytest.mark.parametrize('failure', ['http503', 'http429', 'transport'])
def test_optional_failure_is_recorded_once_and_other_provider_and_model_continue(tmp_path, failure):
    run, ledger, night, fred = setup_case(tmp_path)
    calls = []
    def respond(request):
        calls.append(request)
        if failure == 'transport':
            raise httpx.ReadTimeout('SYNTHETIC_TIMEOUT', request=request)
        return httpx.Response(503 if failure == 'http503' else 429, content=b'unavailable', request=request)
    with pytest.raises(OptionalNightCollectionError) as caught:
        execute(run, night, respond)
    assert len(calls) == 1 and not run.halted
    final = run.results[night.logical_request_id]
    assert final['status'] == 'FAILED' and len(final['attempts']) == 1
    assert caught.value.logical_request_id == night.logical_request_id
    state = ledger.state()
    cap = RuntimeCap(ledger.worker_binding())
    assert state['state'] == 'REGISTRATION_CAPTURED' and state['pending'] is None
    assert cap.state()['first_external_failure'] is None
    assert cap.state()['stopped_providers'] == ['krx_night_futures']
    original = cap.state()['attempts'][caught.value.physical_attempt_id]
    assert original['optional_night']['plan_sha256'] == run.plan.plan_sha256
    assert original['outcome'] == ('TRANSPORT_UNKNOWN' if failure == 'transport' else 'HTTP_RESPONSE')
    assert ledger.state()['http_total'] == 1
    # The stopped provider cannot issue a second physical request.
    with pytest.raises(ValueError, match='CAP_EXHAUSTED'):
        cap.reserve(provider='krx_night_futures', method='GET', host='data-dbg.krx.co.kr',
            path='/svc/apis/drv/fut_bydd_trd', market='us', subject='*', phase='SOURCE',
            owner='SelectedSourceDispatcher', request_sha256=digest('FORBIDDEN_SECOND_REQUEST'))
    assert execute(run, fred, lambda r: httpx.Response(200, json={}, request=r))['status'] == 'PASS'
    assert ledger.state()['http_total'] == 2
    enter_model_budget(ledger)
    assert ledger.state()['model_total'] == 1


@pytest.mark.parametrize('case', ['auth401', 'auth403', 'legacy_policy', 'mandatory_night', 'other_provider'])
def test_auth_and_other_scopes_keep_global_stop(tmp_path, case):
    run, ledger, night, fred = setup_case(tmp_path,
        enabled=case != 'legacy_policy', optional=case != 'mandatory_night')
    descriptor = fred if case == 'other_provider' else night
    status = 401 if case == 'auth401' else 403 if case == 'auth403' else 503
    try:
        execute(run, descriptor, lambda r: httpx.Response(status, content=b'error', request=r))
    except SourceSafetyStop:
        pass
    state = ledger.state()
    assert state['runtime']['first_external_failure'] is not None
    assert state['http_total'] == 1
    assert not any(row.get('optional_unavailable') for row in (
        json.loads(line)['value'] for line in ledger.path.read_bytes().splitlines()))


@pytest.mark.parametrize('kind', ['storage', 'implementation', 'cancel', 'secret', 'budget'])
def test_non_network_failures_are_not_downgraded_to_optional_data(tmp_path, kind):
    run, ledger, night, _ = setup_case(tmp_path, maximum=0 if kind == 'budget' else 8)
    calls = []
    def respond(request):
        calls.append(request)
        if kind == 'storage': raise OSError('SYNTHETIC_DISK_ERROR')
        if kind == 'implementation': raise ValueError('SYNTHETIC_BUG')
        if kind == 'cancel': raise asyncio.CancelledError()
        if kind == 'secret': return httpx.Response(503, json={'api_key':'SYNTHETIC_SECRET'}, request=request)
        return httpx.Response(200, json={}, request=request)
    with pytest.raises(BaseException) as caught:
        execute(run, night, respond)
    assert not isinstance(caught.value, OptionalNightCollectionError)
    assert ledger.state()['state'] == 'STOPPED_NO_SEND'
    assert ledger.state()['http_total'] == len(calls) == (0 if kind == 'budget' else 1)


def test_forged_optional_plan_metadata_fails_before_http(tmp_path, monkeypatch):
    from app.services import selected_source_dispatch as module
    run, ledger, night, _ = setup_case(tmp_path)
    original = module.optional_night_scope
    monkeypatch.setattr(module, 'optional_night_scope',
        lambda plan, d: {**original(plan, d), 'plan_sha256':digest('ANOTHER_PLAN')})
    calls = []
    with pytest.raises(ValueError, match='OPTIONAL_NIGHT_FROZEN_PLAN_MISMATCH'):
        execute(run, night, lambda r: calls.append(r) or httpx.Response(200, json={}))
    assert not calls and ledger.state()['http_total'] == 0
    assert ledger.state()['state'] == 'STOPPED_NO_SEND'


def test_actual_request_deadline_is_optional_but_keeps_original_timeout_receipts(tmp_path):
    run, ledger, night, fred = setup_case(tmp_path, request_timeout=1)
    async def hung(request):
        await asyncio.Event().wait()
    with pytest.raises(OptionalNightCollectionError):
        execute(run, night, hung)
    final = run.results[night.logical_request_id]
    assert len(final['attempts']) == 1 and final['attempts'][0]['error'] == 'TimeoutError'
    state = ledger.state()
    attempt = next(iter(state['runtime']['attempts'].values()))
    assert attempt['outcome'] == 'TRANSPORT_UNKNOWN' and attempt['error_type'] == 'TimeoutError'
    assert state['runtime']['first_external_failure'] is None and state['pending'] is None
    assert state['runtime']['stopped_providers'] == ['krx_night_futures']
    assert execute(run, fred, lambda r: httpx.Response(200, json={}, request=r))['status'] == 'PASS'
    assert ledger.state()['http_total'] == 2
