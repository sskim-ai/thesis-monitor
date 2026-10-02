import asyncio
from datetime import datetime, timezone
import json

import httpx
import pytest

from app.services.bounded_financial_acquisition import make_plan
from app.services.sealed_financial_slots import financial_slots
from app.services.sealed_fresh_dispatch import (
    FreshRequestDescriptor, SealedDispatcher, consume_bound_result, wire_identity,
)
from app.services.sealed_response_binding import ResponseBinding, SlotNotSelected, binding_owner_hash
from app.services.unified_snapshot_contract import digest, encoded
from tests.test_r9_rev11_sealed_dispatch import CONFIG, OWNER, ROOT, descriptor, plan


def financial(market='us', kind='domestic_us'):
    return make_plan(dict(ticker='FIXTURE', canonical_company_id='issuer', canonical_security_id='security',
        identity_provider='local', cik='123', corp_code='00000123', issuer_type=kind), market=market,
        cutoff=datetime(2026, 9, 28, tzinfo=timezone.utc), run_id='fresh-1', all_subjects_fresh=True)


def filings():
    return {'cik': '123', 'filings': {'recent': {'form': ['10-Q'],
        'accessionNumber': ['0000000123-26-000001'], 'primaryDocument': ['actual.htm'],
        'filingDate': ['2026-08-01'], 'reportDate': ['2026-06-30']}, 'files': []}}


class RawOwner:
    identity = ('test-owner', OWNER)

    def __call__(self, raw):
        return dict(value={'raw_size': len(raw)}, source_period='SOURCE_FRAGMENT_NOT_PERIOD_QUALIFIED', consumer_complete=True)


def run_slots(tmp_path, slots):
    p = plan(*slots, mandatory_roles=tuple(sorted({d.consumer_role for d in slots})), binding_owner_sha256=binding_owner_hash())
    return SealedDispatcher(plan=p, root=tmp_path / 'run', rev10_receipt=ROOT, owners={'test-owner': OWNER},
        config_identities={d.provider: CONFIG for d in slots}, credential_presence={d.provider: True for d in slots},
        secrets=('PLAN_CREDENTIAL',))


def wire(public):
    r = json.loads(public)
    return httpx.Request(r['method'], r['url'].replace('[REDACTED]', 'PLAN_CREDENTIAL'),
        content=r['body'], headers=[(k, v.replace('[REDACTED]', 'PLAN_CREDENTIAL')) for k, v in r['headers']])


def send(run, key, payload, headers=None):
    req, _, _ = run.resolve(key)
    return asyncio.run(run.execute(key, wire(req), transport=httpx.MockTransport(
        lambda _: httpx.Response(200, json=payload, headers=headers)), normalize=RawOwner()))


@pytest.mark.parametrize('market,kind,count', [('us', 'domestic_us', 4), ('us', 'foreign_private_issuer', 18), ('kr', 'domestic_us', 6)])
def test_compile_before_data_exact_existing_budget(tmp_path, market, kind, count):
    slots = financial_slots(financial(market, kind), owner='test-owner', owner_sha256=OWNER, config_sha256=CONFIG)
    run = run_slots(tmp_path, slots)
    assert len(slots) == count
    assert run.admission['total_theoretical_max'] == count * 3
    assert not run.results
    assert all(d.generation_id == 'fresh-1' for d in slots)


def test_selected_sec_wire_uses_original_slots_and_parent_hash(tmp_path):
    slots = financial_slots(financial(), owner='test-owner', owner_sha256=OWNER, config_sha256=CONFIG)
    run = run_slots(tmp_path, slots)
    before = run.plan.plan_sha256
    discovery = send(run, slots[0].logical_request_id, filings())
    resolved, parents, _ = run.resolve(slots[2].logical_request_id)
    assert json.loads(resolved)['url'].endswith('/000000012326000001/actual.htm')
    assert parents == {slots[0].logical_request_id: discovery['receipt_sha256']}
    child = send(run, slots[2].logical_request_id, {'statement': 42})
    assert child['parent_receipts'] == parents
    assert consume_bound_result(root=run.root, plan=run.plan, logical_id=slots[2].logical_request_id,
                                receipt_sha256=child['receipt_sha256'])['value']['raw_size'] > 0
    assert before == run.plan.plan_sha256
    assert run.skip_unselected(slots[3].logical_request_id)['status'] == 'NOT_SELECTED'


def test_sec_selected_request_cannot_be_replaced(tmp_path):
    slots = financial_slots(financial(), owner='test-owner', owner_sha256=OWNER, config_sha256=CONFIG)
    run = run_slots(tmp_path, slots)
    send(run, slots[0].logical_request_id, filings())
    public, _, _ = run.resolve(slots[2].logical_request_id)
    req = json.loads(public)
    req['url'] = req['url'].replace('actual.htm', 'unselected.htm')
    calls = []
    with pytest.raises(BaseException, match='request_not_exact_descriptor'):
        asyncio.run(run.execute(slots[2].logical_request_id, wire(encoded(req).decode()),
            transport=httpx.MockTransport(lambda r: calls.append(r)), normalize=RawOwner()))
    assert calls == []


def test_parent_artifact_tamper_denied_before_child(tmp_path):
    slots = financial_slots(financial(), owner='test-owner', owner_sha256=OWNER, config_sha256=CONFIG)
    run = run_slots(tmp_path, slots)
    send(run, slots[0].logical_request_id, filings())
    (run.root / slots[0].raw_path).write_bytes(b'{}')
    with pytest.raises(ValueError, match='artifact_hash_mismatch'):
        run.resolve(slots[2].logical_request_id)


def test_no_forward_dependency_or_other_issuer(tmp_path):
    slots = financial_slots(financial(), owner='test-owner', owner_sha256=OWNER, config_sha256=CONFIG)
    with pytest.raises(ValueError, match='parent_must_precede'):
        run_slots(tmp_path, (slots[2], slots[0]))
    bad = slots[2].model_dump()
    bad['subject'] = 'OTHER'
    with pytest.raises(ValueError, match='generation_subject'):
        FreshRequestDescriptor.model_validate(bad)


def pages():
    req = httpx.Request('POST', 'https://api.kiwoom.com/api/dostk/chart', json={'stk_cd': '000001'},
                        headers={'api-id': 'ka10081', 'cont-yn': 'N', 'next-key': ''})
    first = descriptor('page1', provider='kiwoom', market='kr', subject='000001', role_id='chart', consumer_role='chart',
        group_id='chart', max_pages=2, request_json=wire_identity(req))
    policy = {'rule': 'previous_page_exact_continuation'}
    second = descriptor('page2', provider='kiwoom', market='kr', subject='000001', role_id='chart', consumer_role='chart',
        group_id='chart', max_pages=2, page_ordinal=2, request_json=wire_identity(req),
        response_binding=ResponseBinding(kind='KIWOOM_CONTINUATION', parents=('page1',),
            policy_json=encoded(policy).decode(), policy_sha256=digest(policy)))
    return first, second


def test_cursor_binding_exact_and_no_descriptor_added(tmp_path):
    run = run_slots(tmp_path, pages())
    old = run.plan.model_dump_json()
    send(run, 'page1', {'rows': []}, {'cont-yn': 'Y', 'next-key': 'response-owned-value'})
    public, _, _ = run.resolve('page2')
    assert dict(json.loads(public)['headers'])['next-key'] == 'response-owned-value'
    send(run, 'page2', {'rows': []})
    assert run.plan.model_dump_json() == old and len(run.results) == 2


def test_no_continuation_is_not_fabricated_page(tmp_path):
    run = run_slots(tmp_path, pages())
    send(run, 'page1', {'rows': []})
    with pytest.raises(SlotNotSelected):
        run.resolve('page2')
    result = run.skip_unselected('page2')
    assert result['status'] == 'NOT_SELECTED' and result['attempts'] == []


def test_binding_policy_cannot_be_widened():
    p = financial()
    p['limits']['current'] += 1
    with pytest.raises(ValueError, match='not_existing_financial_policy'):
        ResponseBinding(kind='SEC_PRIMARY', parents=('discovery',), policy_json=encoded(p).decode(), policy_sha256=digest(p))


def test_binding_code_hash_drift_is_pre_dispatch_gap(tmp_path):
    slots = financial_slots(financial(), owner='test-owner', owner_sha256=OWNER, config_sha256=CONFIG)
    p = plan(*slots, mandatory_roles=('financial:FIXTURE',), binding_owner_sha256='f' * 64)
    assert 'response_binding_owner_drift' in p.admission(rev10_receipt=ROOT, owners={'test-owner': OWNER},
        config_identities={'sec_edgar': CONFIG}, credential_presence={'sec_edgar': True})['gaps']


@pytest.mark.parametrize('market', ['us', 'kr'])
def test_native_financial_owner_consumes_only_sealed_receipts(tmp_path, market):
    from app.services.bounded_financial_acquisition import collect
    from app.services.bounded_financial_projection import verify_capture
    from app.services.sealed_financial_reader import SealedFinancialReader
    p = financial(market)
    slots = financial_slots(p, owner='test-owner', owner_sha256=OWNER, config_sha256=CONFIG)
    run = run_slots(tmp_path, slots)
    calls = []
    def response(req):
        calls.append(str(req.url))
        if 'submissions' in req.url.path:
            return httpx.Response(200, json=filings())
        if 'companyfacts' in req.url.path:
            return httpx.Response(200, json={'cik': '123', 'facts': {}})
        if req.url.path.endswith('list.json'):
            return httpx.Response(200, json={'status': '000', 'total_page': 1, 'list': [{
                'corp_code': p['issuer'], 'report_nm': '반기보고서 (2026.06)',
                'rcept_no': '20260814000001', 'rcept_dt': '20260814'}]})
        if req.url.path.endswith('fnlttSinglAcntAll.json'):
            assert req.url.params['bsns_year'] == '2026'
            assert req.url.params['reprt_code'] == '11012'
            return httpx.Response(200, json={'status': '013'})
        return httpx.Response(200, content=b'<html>official selected document</html>')
    reader = SealedFinancialReader(p, tmp_path / 'native', dispatcher=run,
        transport=httpx.MockTransport(response),
        **({'user_agent': 'PLAN_CREDENTIAL'} if market == 'us' else {'api_key': 'PLAN_CREDENTIAL'}))
    capture = asyncio.run(collect(reader))
    verify_capture(p, capture, reader.output, reader.receipts)
    assert len(calls) == 3 and len(capture['selected_filings']) == 1
    assert all(r['sealed_final_receipt_sha256'] == run.results[r['sealed_logical_id']]['receipt_sha256'] for r in reader.receipts)
    assert len(run.plan.descriptors) == (4 if market == 'us' else 6)


def test_foreign_exhibit_resolution_uses_same_selected_index_and_primary(tmp_path):
    slots = financial_slots(financial(kind='foreign_private_issuer'), owner='test-owner', owner_sha256=OWNER, config_sha256=CONFIG)
    run = run_slots(tmp_path, slots)
    payload = filings()
    payload['filings']['recent']['form'] = ['6-K']
    send(run, slots[0].logical_request_id, payload)
    send(run, slots[2].logical_request_id, {'directory': {'item': [{'name': 'ex99.htm'}]}})
    # A document response need not be JSON; use the raw fragment owner.
    key = slots[3].logical_request_id
    resolved, _, _ = run.resolve(key)
    asyncio.run(run.execute(key, wire(resolved), transport=httpx.MockTransport(
        lambda _: httpx.Response(200, content=b'<html></html>')), normalize=RawOwner()))
    public, _, _ = run.resolve(slots[4].logical_request_id)
    assert json.loads(public)['url'].endswith('/000000012326000001/ex99.htm')
    assert run.skip_unselected(slots[5].logical_request_id)['reason'] == 'NO_SELECTED_EXHIBIT'


def test_dart_transient_provider_status_uses_same_slot_budget(tmp_path, monkeypatch):
    async def no_wait(_):
        pass
    monkeypatch.setattr(asyncio, 'sleep', no_wait)
    slots = financial_slots(financial('kr'), owner='test-owner', owner_sha256=OWNER, config_sha256=CONFIG)
    run = run_slots(tmp_path, slots)
    calls = []
    def response(req):
        calls.append(wire_identity(req))
        return httpx.Response(200, json={'status': '800' if len(calls) < 3 else '013'})
    final = asyncio.run(run.execute(slots[0].logical_request_id, wire(slots[0].request_json),
        transport=httpx.MockTransport(response), normalize=RawOwner()))
    assert final['status'] == 'PASS' and len(calls) == 3 and len(set(calls)) == 1


def test_all_header_credentials_are_redacted_before_plan_or_receipt():
    req = httpx.Request('POST', 'https://api.kiwoom.com/api/dostk/chart', json={'stk_cd': '123'},
        headers={'authorization': 'Bearer fixture-secret-token', 'X-Naver-Client-Secret': 'fixture-secret-header',
                 'api-id': 'ka10081', 'cont-yn': 'Y', 'next-key': 'public-response-cursor'})
    value = wire_identity(req, ('fixture-secret-token', 'fixture-secret-header'))
    assert 'fixture-secret' not in value
    assert 'public-response-cursor' in value and 'ka10081' in value


def test_response_header_secret_is_never_archived(tmp_path):
    run = run_slots(tmp_path, pages())
    with pytest.raises(BaseException, match='source_secret_or_authorization_failure'):
        send(run, 'page1', {'rows': []}, {'cont-yn': 'Y', 'next-key': 'PLAN_CREDENTIAL'})
    assert not any(b'PLAN_CREDENTIAL' in p.read_bytes() for p in run.root.rglob('*') if p.is_file())


def test_response_slot_inventory_closes_financial_but_does_not_fake_whole_gate():
    from tests.test_unified_stock_acquisition import plan as stock_fixture
    from scripts.r9_rev11_provider_inventory import response_slot_inventory
    stock = stock_fixture.__wrapped__()
    identities = {}
    for ordinal, r in enumerate(stock.reads, 1):
        if r.subject not in identities:
            identities[r.subject] = dict(ticker=r.subject, canonical_company_id='issuer-' + r.subject,
                canonical_security_id='security-' + r.subject, identity_provider='local',
                cik=str(ordinal), corp_code=f'{ordinal:08d}', issuer_type='domestic_us')
    providers = ['kiwoom', 'sec_edgar', 'opendart', 'fred', 'eia', 'ecos', 'krx_night_futures']
    audit = response_slot_inventory(stock=stock, identities=identities,
        config_identities={p: CONFIG for p in providers}, credential_presence={p: True for p in providers},
        configured_kr_pages=50, rev10_receipt=ROOT, code_sha='a' * 40)
    assert sum(r['status'] == 'SEALED_FINANCIAL_OWNER_BOUND' for r in audit['role_coverage']) == 22
    assert not audit['admission']['live_dispatch_allowed']
    assert 'whole_graph:fresh_receipt_collector' in audit['admission']['gaps']
    assert not audit['final_provider_plan_issued']


def test_paginated_cursor_cycle_denied(tmp_path):
    from app.services.sealed_chart_slots import chart_slots
    first, _ = pages()
    run = run_slots(tmp_path, chart_slots(first, maximum_pages=4))
    keys = [d.logical_request_id for d in run.plan.descriptors]
    send(run, keys[0], {'rows': []}, {'cont-yn': 'Y', 'next-key': 'cursor-a'})
    send(run, keys[1], {'rows': []}, {'cont-yn': 'Y', 'next-key': 'cursor-b'})
    send(run, keys[2], {'rows': []}, {'cont-yn': 'Y', 'next-key': 'cursor-a'})
    with pytest.raises(BaseException, match='binding_cursor_cycle'):
        run.resolve(keys[3])


def test_slot_skip_is_replayed_through_ancestor_chain(tmp_path):
    from app.services.sealed_chart_slots import chart_slots
    first, _ = pages()
    run = run_slots(tmp_path, chart_slots(first, maximum_pages=3))
    keys = [d.logical_request_id for d in run.plan.descriptors]
    send(run, keys[0], {'rows': []})
    run.skip_unselected(keys[1])
    assert run.skip_unselected(keys[2])['reason'] == 'ANCESTOR_NO_CONTINUATION'


def test_credential_exchange_only_exports_sanitized_receipt(tmp_path):
    req = httpx.Request('POST', 'https://api.kiwoom.com/oauth2/token',
        json={'grant_type': 'client_credentials', 'appkey': 'PLAN_CREDENTIAL', 'secretkey': 'PLAN_CREDENTIAL'})
    d = descriptor('auth', provider='kiwoom', endpoint_operation='credential_exchange',
        consumer_role='kiwoom:credential_exchange', request_json=wire_identity(req, ('PLAN_CREDENTIAL',)))
    run = run_slots(tmp_path, (d,))
    final = asyncio.run(run.execute('auth', req, transport=httpx.MockTransport(lambda _: httpx.Response(200,
        json={'token': 'private-token-never-export', 'expires_dt': '20260929000000'})), normalize=RawOwner()))
    assert final['status'] == 'PASS'
    assert run.credential_response.json()['token'] == 'private-token-never-export'
    assert not any(b'private-token-never-export' in p.read_bytes() or b'PLAN_CREDENTIAL' in p.read_bytes()
                   for p in run.root.rglob('*') if p.is_file())
    assert json.loads((run.root / d.raw_path).read_bytes()) == {'exchange_succeeded': True, 'http_status': 200}
