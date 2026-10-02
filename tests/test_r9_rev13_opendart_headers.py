import asyncio
import json

import httpx
import pytest

from app.services.bounded_financial_acquisition import collect, SystemicStop
from app.services.sealed_financial_reader import SealedFinancialReader
from app.services.sealed_financial_slots import financial_slots
from app.services.sealed_fresh_dispatch import FreshRequestDescriptor
from app.services.sealed_opendart_contract import header_contract, opendart_headers
from app.services.unified_snapshot_contract import digest, encoded
from scripts.r9_rev13_dart_diagnostic import classify, diagnose_once, STOP
from tests.test_r9_rev11_full_plan import compiled
from tests.test_r9_rev11_response_slots import financial, run_slots, wire, RawOwner
from tests.test_r9_rev11_sealed_dispatch import CONFIG, OWNER


def slots():
    return financial_slots(financial('kr'), owner='test-owner', owner_sha256=OWNER, config_sha256=CONFIG)


def test_all_kr_slots_exact_provider_headers_no_extra_browser_headers():
    _, _, out = compiled()
    dart = [d for d in out['plan'].descriptors if d.provider == 'opendart']
    assert len({d.subject for d in dart}) == 8
    for d in dart:
        assert json.loads(d.request_json)['headers'] == [list(pair) for pair in header_contract()['headers']]
        assert d.timeout_seconds == 600 and d.transient_retry_max == 2
        assert 'PLAN_CREDENTIAL' not in d.request_json
    assert header_contract()['follow_redirects'] is False


@pytest.mark.parametrize('field,value', [('accept', None), ('user-agent', None),
    ('accept', 'text/html'), ('user-agent', 'Browser/1.0')])
def test_missing_or_wrong_header_changes_hash_and_denies_actual_wire(tmp_path, field, value):
    ds = slots()
    run = run_slots(tmp_path, ds)
    d = ds[0]
    public = json.loads(d.request_json)
    headers = dict(public['headers'])
    if value is None:
        del headers[field]
    else:
        headers[field] = value
    public['headers'] = sorted(headers.items())
    changed = FreshRequestDescriptor.model_validate(d.model_dump() | {'request_json': encoded(public).decode()})
    assert changed.request_semantic_sha256 != d.request_semantic_sha256
    assert changed.descriptor_sha256 != d.descriptor_sha256
    calls = []
    with pytest.raises(BaseException, match='request_not_exact_descriptor'):
        asyncio.run(run.execute(d.logical_request_id, wire(changed.request_json),
            transport=httpx.MockTransport(lambda r: calls.append(r)), normalize=RawOwner()))
    assert calls == []


@pytest.mark.parametrize('change', ['host', 'path', 'query'])
def test_header_contract_does_not_allow_business_route_mutations(tmp_path, change):
    ds = slots()
    run = run_slots(tmp_path, ds)
    req = wire(ds[0].request_json)
    if change == 'host':
        req.url = req.url.copy_with(host='example.invalid')
    elif change == 'path':
        req.url = req.url.copy_with(path='/api/company.json')
    else:
        req.url = req.url.copy_add_param('unexpected_business_parameter', '1')
    calls = []
    with pytest.raises(BaseException, match='request_not_exact_descriptor'):
        asyncio.run(run.execute(ds[0].logical_request_id, req,
            transport=httpx.MockTransport(lambda r: calls.append(r)), normalize=RawOwner()))
    assert calls == []


def test_native_discovery_and_statements_send_same_exact_headers(tmp_path):
    policy = financial('kr')
    run = run_slots(tmp_path, slots())
    calls = []
    def response(req):
        calls.append(req)
        assert {k: v for k, v in req.headers.items() if k != 'host'} == {
            k.lower(): v for k, v in opendart_headers().items()}
        if req.url.path.endswith('/list.json'):
            return httpx.Response(200, json={'status': '000', 'message': 'normal', 'total_page': 1,
                'list': [{'corp_code': policy['issuer'], 'report_nm': '반기보고서 (2026.06)',
                    'rcept_no': '20260814000001', 'rcept_dt': '20260814'}]})
        return httpx.Response(200, json={'status': '013', 'message': 'no data'})
    reader = SealedFinancialReader(policy, tmp_path / 'native', dispatcher=run,
        transport=httpx.MockTransport(response), api_key='PLAN_CREDENTIAL', user_agent='IGNORED_OVERRIDE')
    capture = asyncio.run(collect(reader))
    assert len(calls) == 3 and len(capture['selected_filings']) == 1
    assert all(b'PLAN_CREDENTIAL' not in p.read_bytes() for p in run.root.rglob('*') if p.is_file())


def test_native_302_is_one_attempt_systemic_stop_not_follow_or_retry(tmp_path):
    policy = financial('kr')
    run = run_slots(tmp_path, slots())
    calls = []
    def response(req):
        calls.append(req)
        return httpx.Response(302, headers={'Location': '/error1.html'})
    reader = SealedFinancialReader(policy, tmp_path / 'native', dispatcher=run,
        transport=httpx.MockTransport(response), api_key='PLAN_CREDENTIAL')
    with pytest.raises(SystemicStop, match=STOP):
        asyncio.run(collect(reader))
    assert len(calls) == 1 and len(reader.receipts) == 1
    final = next(iter(run.results.values()))
    assert final['attempts'][0]['redirect_metadata']['follow_authorized'] is False


@pytest.mark.parametrize('http_status,payload,expected', [
    (200, {'status': '000', 'message': 'normal'}, 'PASS'),
    (200, {'status': '013', 'message': 'no data'}, 'PASS'),
    (200, {'status': '010', 'message': 'key rejected'}, STOP),
    (200, {'status': '000'}, STOP),
    (302, {'status': '000', 'message': 'normal'}, STOP)])
def test_diagnostic_classification(http_status, payload, expected):
    assert classify(http_status, encoded(payload))[0] == expected
    assert classify(200, b'<html>Error</html>')[0] == STOP


@pytest.mark.parametrize('status', [200, 302, 503])
def test_diagnostic_never_retries_or_persists_raw(status):
    d = slots()[0].model_copy(update={'transient_retry_max': 0})
    calls = []
    def response(req):
        calls.append(req)
        return httpx.Response(status, json={'status': '000', 'message': 'normal', 'list': ['PRIVATE_NOT_EXPORTED']},
                              headers={'Location': '/error1.html'})
    result = asyncio.run(diagnose_once(d, 'PLAN_CREDENTIAL', httpx.MockTransport(response)))
    assert len(calls) == 1 and result['http_status'] == status
    assert result['status'] == ('PASS' if status == 200 else STOP)
    assert 'PRIVATE_NOT_EXPORTED' not in json.dumps(result) and 'PLAN_CREDENTIAL' not in json.dumps(result)
    assert result['response_sha256']


def test_secret_echo_denied_and_hash_only():
    d = slots()[0].model_copy(update={'transient_retry_max': 0})
    result = asyncio.run(diagnose_once(d, 'PLAN_CREDENTIAL', httpx.MockTransport(lambda _: httpx.Response(
        200, json={'status': '000', 'message': 'PLAN_CREDENTIAL'}))))
    assert result['status'] == STOP and result['json_message'] is None
    assert 'PLAN_CREDENTIAL' not in json.dumps(result)


def test_header_contract_fresh_copy_is_stable():
    old = digest(header_contract())
    opendart_headers()['Accept'] = 'text/html'
    assert digest(header_contract()) == old
