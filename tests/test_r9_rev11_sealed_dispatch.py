import asyncio
from datetime import datetime, timezone
import json

import httpx
import pytest

from app.services.sealed_fresh_dispatch import (
    FreshRequestDescriptor, ProviderPlan, SealedDispatcher, consume_bound_result,
    kr_request_budget, wire_identity,
)
from app.services.unified_live_source_transport import SourceSafetyStop
from app.services.unified_run_artifacts import sha256_bytes
from app.services.unified_snapshot_contract import encoded

OWNER = 'a' * 64
CONFIG = 'b' * 64
ROOT = dict(status='PASS', dispatch_allowed=True)


def request(series='DGS10'):
    return httpx.Request('GET', 'https://api.stlouisfed.org/fred/series/observations',
                         params={'series_id': series})


def descriptor(key='fred-1', series='DGS10', **changes):
    value = dict(generation_id='fresh-1', logical_request_id=key, provider='fred',
        source_family='macro', role_id='rates', market='global', subject=series,
        endpoint_operation='fred_observations', request_json=wire_identity(request(series)),
        target_period='2026-09-28', mandatory=True, group_id=key, page_ordinal=1,
        max_pages=1, document_ordinal=1, max_documents=1, timeout_seconds=1,
        transient_retry_max=2, raw_path=f'raw/{key}/source.body', normalizer='test-owner',
        consumer_role='rates', owner_sha256=OWNER, config_identity_sha256=CONFIG)
    return FreshRequestDescriptor(**(value | changes))


def plan(*descriptors, **changes):
    value = dict(generation_id='fresh-1', code_sha='a' * 40, policy_schema_sha256=OWNER,
        rev10_receipt_sha256=sha256_bytes(encoded(ROOT) + b'\n'), frozen_at=datetime.now(timezone.utc),
        descriptors=descriptors or (descriptor(),), mandatory_roles=('rates',))
    return ProviderPlan(**(value | changes))


class Owner:
    identity = ('test-owner', OWNER)

    def __call__(self, raw):
        data = json.loads(raw)
        return dict(value=data['value'], source_period=data['date'], consumer_complete=True)


def runner(tmp_path, p=None):
    return SealedDispatcher(plan=p or plan(), root=tmp_path / 'run', rev10_receipt=ROOT,
        owners={'test-owner': OWNER}, config_identities={'fred': CONFIG}, credential_presence={'fred': True})


def execute(run, response, *, req=None, key='fred-1', owner=None):
    return asyncio.run(run.execute(key, req or request(), transport=httpx.MockTransport(response),
                                  normalize=owner or Owner()))


def ok(_):
    return httpx.Response(200, json={'value': 4, 'date': '2026-09-25'})


def test_exact_roundtrip_and_receipt_chain(tmp_path):
    run = runner(tmp_path)
    final = execute(run, ok)
    norm = consume_bound_result(root=run.root, plan=run.plan, logical_id='fred-1',
                               receipt_sha256=final['receipt_sha256'])
    assert norm['value'] == 4
    assert len(final['attempts']) == 1
    assert final['source_period'] == '2026-09-25'
    assert final['retrieval_time'] != final['source_period']
    assert {p.name for p in (run.root / 'receipts/fred-1').iterdir()} >= {
        'plan.json', 'start.json', 'attempt-1.start.json', 'attempt-1.json', 'attempt-1.body',
        'normalization.json', 'role-binding.json', 'final.json'}


@pytest.mark.parametrize('changes', [dict(raw_path='../out'), dict(raw_path='/tmp/out'),
    dict(page_ordinal=2), dict(document_ordinal=2), dict(provider='massive'),
    dict(transient_retry_max=3), dict(timeout_seconds=601), dict(raw_path='raw/other/source.body')])
def test_descriptor_bounds(changes):
    with pytest.raises(ValueError):
        descriptor(**changes)


def test_immutable_request_not_mutable_mapping():
    d = descriptor()
    with pytest.raises(ValueError):
        d.request_json = '{}'
    value = json.loads(d.request_json)
    value['url'] = 'https://evil.example'
    assert json.loads(d.request_json)['url'] != value['url']
    p = plan()
    assert ProviderPlan.model_validate_json(p.model_dump_json()).plan_sha256 == p.plan_sha256


@pytest.mark.parametrize('change', [dict(generation_id='old'), dict(mandatory_roles=('rates', 'missing')),
    dict(unresolved_roles=('sec_selected_document_unknown',))])
def test_missing_or_old_plan_blocks_before_transport(tmp_path, change):
    with pytest.raises(ValueError):
        runner(tmp_path, plan(**change))
    assert not (tmp_path / 'run').exists()


@pytest.mark.parametrize('kind', ['root', 'owner', 'config', 'presence'])
def test_admission_identity_cannot_be_status_only(kind):
    kwargs = dict(rev10_receipt=ROOT, owners={'test-owner': OWNER}, config_identities={'fred': CONFIG},
                  credential_presence={'fred': True})
    if kind == 'root':
        kwargs['rev10_receipt'] = ROOT | dict(other='changed')
    elif kind == 'presence':
        kwargs['credential_presence'] = {'fred': False}
    else:
        kwargs['owners' if kind == 'owner' else 'config_identities'] = {}
    assert not plan().admission(**kwargs)['live_dispatch_allowed']


def test_changed_request_never_reaches_transport(tmp_path):
    run = runner(tmp_path)
    calls = []
    with pytest.raises(SourceSafetyStop):
        execute(run, lambda r: calls.append(r), req=request('DGS5'))
    assert calls == []
    assert run.used == set()


@pytest.mark.parametrize('code', [408, 429, 500, 502, 503, 504])
def test_only_identical_transient_retries(tmp_path, monkeypatch, code):
    calls = []
    async def no_sleep(_):
        pass
    monkeypatch.setattr(asyncio, 'sleep', no_sleep)
    def send(req):
        calls.append(wire_identity(req))
        return httpx.Response(code) if len(calls) < 3 else ok(req)
    final = execute(runner(tmp_path), send)
    assert final['status'] == 'PASS' and len(final['attempts']) == 3
    assert len(set(calls)) == 1


@pytest.mark.parametrize('code', [301, 302, 400, 404, 422])
def test_no_redirect_or_semantic_retry(tmp_path, code):
    final = execute(runner(tmp_path), lambda _: httpx.Response(code, headers={'location': 'https://evil.example'}))
    assert final['status'] == 'FAILED' and len(final['attempts']) == 1


def test_normalization_failure_not_retried_and_other_request_continues(tmp_path):
    run = runner(tmp_path, plan(descriptor(), descriptor('fred-2', 'DGS5')))
    failed = execute(run, lambda _: httpx.Response(200, json={'other': 1}))
    assert len(failed['attempts']) == 1 and failed['status'] == 'FAILED'
    assert execute(run, ok, key='fred-2', req=request('DGS5'))['status'] == 'PASS'


@pytest.mark.parametrize('code', [401, 403])
def test_systemic_stop_latched(tmp_path, code):
    run = runner(tmp_path, plan(descriptor(), descriptor('fred-2', 'DGS5')))
    with pytest.raises(SourceSafetyStop):
        execute(run, lambda _: httpx.Response(code))
    with pytest.raises(SourceSafetyStop, match='systemic_stop_latched'):
        execute(run, ok, key='fred-2', req=request('DGS5'))
    assert run.results['fred-1']['status'] == 'SYSTEMIC_STOP'
    assert len(run.results) == 1


@pytest.mark.parametrize('target', ['raw/fred-1/source.body', 'receipts/fred-1/normalization.json',
    'receipts/fred-1/role-binding.json', 'receipts/fred-1/final.json'])
def test_consumer_rejects_tamper(tmp_path, target):
    run = runner(tmp_path)
    final = execute(run, ok)
    (run.root / target).write_text('{}')
    with pytest.raises((ValueError, KeyError)):
        consume_bound_result(root=run.root, plan=run.plan, logical_id='fred-1', receipt_sha256=final['receipt_sha256'])


def test_repeat_and_wrong_generation_consumption(tmp_path):
    run = runner(tmp_path)
    final = execute(run, ok)
    with pytest.raises(SourceSafetyStop, match='repeated'):
        execute(run, ok)
    other = plan(descriptor(generation_id='new'), generation_id='new')
    with pytest.raises(ValueError, match='identity'):
        consume_bound_result(root=run.root, plan=other, logical_id='fred-1', receipt_sha256=final['receipt_sha256'])


@pytest.mark.parametrize('count, minimum, complete, expected', [
    (1000, 200, True, 'PASS'), (4001, 200, True, 'R2B_R9_REV11_KR_PAGE_BUDGET_INSUFFICIENT'),
    (1000, None, True, 'PAGE_REQUIREMENT_UNPROVEN'), (1000, 200, False, 'PAGE_REQUIREMENT_UNPROVEN')])
def test_request_local_kr_budget_not_global_cap(count, minimum, complete, expected):
    result = kr_request_budget(global_cap=50, row_count=count, verified_minimum_rows_per_page=minimum,
                               consumer_complete=complete)
    assert result['status'] == expected
    assert result['global_configured_cap'] == 50 and not result['production_setting_modified']


def test_single_response_cap():
    assert kr_request_budget(global_cap=50, row_count=None, verified_minimum_rows_per_page=None,
        consumer_complete=True, single_response=True)['required_max_pages'] == 1


def test_no_broker_route_even_on_authorized_host():
    wire = httpx.Request('POST', 'https://api.kiwoom.com/api/dostk/ordr', json={'stk_cd': '005930'})
    with pytest.raises(ValueError, match='nonreadonly'):
        descriptor(provider='kiwoom', request_json=wire_identity(wire))


def test_unknown_next_page_cannot_be_constructed_from_envelope():
    with pytest.raises(ValueError, match='chain_incomplete'):
        plan(descriptor(page_ordinal=2, max_pages=10))


def test_retry_exhaustion_preserves_all_failed_attempts(tmp_path, monkeypatch):
    async def no_sleep(_):
        pass
    monkeypatch.setattr(asyncio, 'sleep', no_sleep)
    run = runner(tmp_path)
    result = execute(run, lambda _: httpx.Response(503, content=b'unavailable'))
    assert result['status'] == 'FAILED'
    assert len(result['attempts']) == 3
    assert len(list((run.root / 'receipts/fred-1').glob('attempt-*.body'))) == 3


def test_secret_body_never_exported(tmp_path):
    run = runner(tmp_path)
    run.secrets = ('PRIVATE_VALUE_FOR_TEST',)
    with pytest.raises(SourceSafetyStop):
        execute(run, lambda _: httpx.Response(200, content=b'PRIVATE_VALUE_FOR_TEST'))
    assert all(b'PRIVATE_VALUE_FOR_TEST' not in p.read_bytes() for p in run.root.rglob('*') if p.is_file())


def test_timeout_bounded_and_no_protocol_error_retry(tmp_path):
    def fail(_):
        raise httpx.RemoteProtocolError('fixture')
    run = runner(tmp_path)
    receipt = execute(run, fail)
    assert receipt['status'] == 'FAILED' and len(receipt['attempts']) == 1


def test_total_attempt_timeout_applies_to_transport(tmp_path):
    class SlowTransport(httpx.AsyncBaseTransport):
        async def handle_async_request(self, req):
            await asyncio.sleep(10)
            return ok(req)
    run = runner(tmp_path, plan(descriptor(transient_retry_max=0)))
    receipt = asyncio.run(run.execute('fred-1', request(), transport=SlowTransport(), normalize=Owner()))
    assert receipt['status'] == 'FAILED' and receipt['attempts'][0]['error'] == 'TimeoutError'


def test_plan_tamper_before_transport(tmp_path):
    run = runner(tmp_path)
    (run.root / 'plan.json').write_text('{}')
    with pytest.raises(SourceSafetyStop, match='plan_drift'):
        execute(run, ok)


def test_sec_exact_child_request_is_response_dependent():
    from scripts.r9_rev11_provider_inventory import sec_response_dependency_probe
    proof = sec_response_dependency_probe()
    assert proof['different_exact_request'] and proof['network_calls'] == 0


def test_cap_exhaustion_not_qualified_or_retried(tmp_path):
    class Incomplete(Owner):
        def __call__(self, raw):
            return super().__call__(raw) | {'consumer_complete': False}
    run = runner(tmp_path)
    final = execute(run, ok, owner=Incomplete())
    assert final['status'] == 'FAILED' and len(final['attempts']) == 1
    with pytest.raises(ValueError):
        consume_bound_result(root=run.root, plan=run.plan, logical_id='fred-1', receipt_sha256=final['receipt_sha256'])


def test_provider_inventory_does_not_issue_partial_final_plan():
    from test_unified_stock_acquisition import plan as stock_fixture
    from app.services.unified_stock_acquisition import UNIVERSE
    from app.services.sealed_fresh_dispatch import HOSTS
    from scripts.r9_rev11_provider_inventory import inventory
    stock = stock_fixture.__wrapped__()
    identities = {t: dict(ticker=t, canonical_company_id='issuer-' + t, canonical_security_id='security-' + t,
        identity_provider='local', cik=str(i + 100), corp_code=str(i + 100).zfill(8), issuer_type='domestic_us')
        for i, t in enumerate(t for ts in UNIVERSE.values() for t in ts)}
    data = inventory(stock=stock, identities=identities, config_identities={k: CONFIG for k in HOSTS},
        credential_presence={k: True for k in HOSTS}, configured_kr_pages=50, rev10_receipt=ROOT, code_sha='a' * 40)
    assert not data['admission']['live_dispatch_allowed'] and not data['final_provider_plan_issued']
    assert len([r for r in data['role_coverage'] if r['role'].startswith('financial:')]) == 22
    for provider in ('fred', 'eia', 'ecos', 'krx_night_futures'):
        assert any(d['provider'] == provider for d in data['descriptor_inventory'])
    assert not any(d['provider'] in {'alpha_vantage', 'massive'} for d in data['descriptor_inventory'])
    assert all(r['global_configured_cap'] == 50 for r in data['kr_page_proof'])
