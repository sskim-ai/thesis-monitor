"""Selected report failures across original discovery, sealed GET and cold physical replay."""
import asyncio
import json

import httpx
import pytest

from app.services.bounded_financial_acquisition import collect
from app.services.campaign_runtime_cap import MeteredSyncTransport, RuntimeCap
from app.services.sealed_financial_reader import SealedFinancialReader
from app.services.selected_run_lifecycle import SelectedRunLedger
from app.services.selected_source_dispatch import SelectedSourceDispatcher
from app.services.unified_live_source_transport import SourceSafetyStop
from tests.test_regular_plan_http_budget import regular_campaign


@pytest.mark.parametrize('outcome,optional', [
    (404, True), (410, True), ('timeout', True), ('deadline', True),
    ('malformed', True), ('no-document', True),
    (401, False), (429, False), (503, False), ('connect', False), ('cancel', False), ('provider-quota', False),
])
def test_optional_report_preserves_cfs_ofs_and_systemic_stops(tmp_path, monkeypatch, outcome, optional):
    ledger, plan, kis, _ = regular_campaign(tmp_path, 'kr', dart_report=True)
    ledger.bind_source_plan('kr', plan, kis_plan=kis)
    binding = ledger.worker_binding()
    run = object.__new__(SelectedSourceDispatcher)
    run.plan, run.run_ledger = plan, ledger
    run.admission = {'SYNTHETIC_ONLY': True}
    run._require_current = lambda: None  # Synthetic registration fixture; exercise the actual dispatch and egress.
    run._initialize(root=tmp_path/'dispatch', secrets=('PLAN_CREDENTIAL',))
    doc = next(d for d in plan.descriptors if d.endpoint_operation == 'dart_report')
    policy = json.loads(doc.response_binding.policy_json)
    calls = []
    if outcome == 'deadline':
        real_timeout = asyncio.timeout
        monkeypatch.setattr(asyncio, 'timeout', lambda delay: real_timeout(0.02))

    async def send(request):
        calls.append(request.url.path)
        if request.url.path.endswith('/list.json'):
            return httpx.Response(200, json={'status':'000', 'total_page':1, 'list':[
                {'corp_code':policy['issuer'], 'stock_code':doc.subject, 'report_nm':'반기보고서 (2026.06)',
                 'rcept_no':'20260814000001','rcept_dt':'20260814'}]})
        if request.url.path.endswith('/fnlttSinglAcntAll.json'):
            return httpx.Response(200, json={'status':'013'})
        assert request.url.path == '/api/document.xml'
        if outcome == 'timeout':
            raise httpx.ReadTimeout('synthetic')
        if outcome == 'deadline':
            await asyncio.Event().wait()
        if outcome == 'connect':
            raise httpx.ConnectError('synthetic')
        if outcome == 'cancel':
            raise asyncio.CancelledError
        if outcome in ('no-document', 'provider-quota'):
            status = '014' if outcome == 'no-document' else '020'
            return httpx.Response(200, content=f'<result><status>{status}</status></result>'.encode())
        return httpx.Response(200 if outcome == 'malformed' else outcome,
                              content=b'fixture body', request=request)
    reader = SealedFinancialReader(policy, tmp_path/'native', dispatcher=run,
        transport=httpx.MockTransport(send), api_key='PLAN_CREDENTIAL')
    if optional:
        acquired = asyncio.run(collect(reader))
        assert acquired['dart_report']['status'] == 'UNAVAILABLE'
        assert {row['filing']['basis'] for row in acquired['documents']} == {'CFS','OFS'}
        assert not run.halted
    else:
        with pytest.raises((SourceSafetyStop, ValueError, asyncio.CancelledError)):
            asyncio.run(collect(reader))
    # Each reported attempt consumed exactly one slot. A new worker sees the same outcome.
    assert calls == ['/api/list.json', '/api/fnlttSinglAcntAll.json', '/api/fnlttSinglAcntAll.json',
                     '/api/document.xml']
    state = SelectedRunLedger.attach_worker(binding).state()
    physical = RuntimeCap(binding).state()
    assert physical['providers'] == {'opendart':4} and state['http_total'] == 4
    if optional:
        assert physical['first_external_failure'] is None and not physical['stopped_providers']
        assert state['state'] != 'STOPPED_NO_SEND'
    else:
        assert physical['first_external_failure'] or state['state'] == 'STOPPED_NO_SEND'


def test_report_requires_exact_route_and_own_pending_slot_before_wire(tmp_path):
    ledger, plan, kis, _ = regular_campaign(tmp_path, 'kr', dart_report=True)
    ledger.bind_source_plan('kr', plan, kis_plan=kis)
    binding = ledger.worker_binding()
    report = next(d for d in plan.descriptors if d.endpoint_operation == 'dart_report')
    listing = next(d for d in plan.descriptors if d.provider == 'opendart' and not d.response_binding)
    calls = []
    def send(req):
        calls.append(req)
        return httpx.Response(200, content=b'synthetic')
    transport = MeteredSyncTransport(binding=binding, market='kr', subject=report.subject, phase='SOURCE',
        owner='SelectedSourceDispatcher', inner=httpx.MockTransport(send))
    url = 'https://opendart.fss.or.kr/api/document.xml'
    params = dict(crtfc_key='SYNTHETIC', rcept_no='20261111000123')
    key = ledger.before_http(market='kr', provider='opendart', logical_id=listing.logical_request_id,
        plan_sha256=plan.plan_sha256)
    with pytest.raises(ValueError, match='DART_ROUTE_MISMATCH'):
        transport.handle_request(httpx.Request('GET', url, params=params))
    ledger.result(key, ok=True)
    key = ledger.before_http(market='kr', provider='opendart', logical_id=report.logical_request_id,
        plan_sha256=plan.plan_sha256)
    for uri, query, error in (
            (url+'.bak', params, 'DART_ROUTE_MISMATCH'),
            (url, dict(params, extra='x'), 'DART_RECEIPT_REQUIRED'),
            (url, dict(params, rcept_no='unknown'), 'DART_RECEIPT_REQUIRED'),
            (url.replace('document.xml', 'list.json'), params, 'DART_ROUTE_MISMATCH')):
        with pytest.raises(ValueError, match=error):
            transport.handle_request(httpx.Request('GET', uri, params=query))
    for method, uri, error in (
            ('POST', url, 'ENDPOINT_PROVIDER_UNBOUND'),
            ('GET', url.replace('.or.kr', '.example'), 'ENDPOINT_PROVIDER_UNBOUND'),
            ('GET', url.replace('.or.kr', '.or.kr:444'), 'TLS_OR_PORT_OUTSIDE')):
        with pytest.raises(ValueError, match=error):
            transport.handle_request(httpx.Request(method, uri, params=params))
    assert not calls and RuntimeCap(binding).state()['total'] == 0
    transport.handle_request(httpx.Request('GET', url, params=params))
    ledger.result(key, ok=True)
    assert len(calls) == ledger.state()['http_total'] == 1
