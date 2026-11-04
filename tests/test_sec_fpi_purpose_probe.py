"""Offline HTTP fixtures only. Synthetic pins never confer production authority."""
import asyncio
from copy import deepcopy
from datetime import datetime, timezone
import json

import httpx
import pytest

from app.services import sec_fpi_purpose_probe as probe
from app.services.bounded_financial_acquisition import BoundedReader, SystemicStop, collect, make_plan, sec_base
from app.services.unified_run_artifacts import durable_json, sha256_bytes
from app.services.unified_snapshot_contract import digest


@pytest.fixture
def original(tmp_path, monkeypatch):
    async def no_sleep(_):
        pass
    monkeypatch.setattr(asyncio, 'sleep', no_sleep)
    identity = dict(ticker='UNSEEN_FPI', canonical_company_id='issuer',
        canonical_security_id='security', identity_provider='fixture', cik='123',
        issuer_type='foreign_private_issuer')
    kwargs = dict(market='us', cutoff=datetime(2026, 10, 21, tzinfo=timezone.utc),
        run_id='historical-test-capture', exact_financial_owner=True)
    base = make_plan(identity, **kwargs)
    selected = dict(form='6-K', accessionNumber='0000000123-26-000001',
        primaryDocument='original.htm', filingDate='2026-08-18', reportDate='2026-08-18')
    newer = [dict(form='6-K', filingDate=f'2026-08-{19+i:02d}', reportDate=f'2026-08-{19+i:02d}',
        accessionNumber=f'0000000123-26-{i+20:06d}', primaryDocument=f'unseen{i}.htm') for i in range(9)]
    older = [dict(form='6-K', filingDate='2026-08-01', reportDate='2026-08-01',
        accessionNumber=f'0000000123-26-{i+100:06d}', primaryDocument=f'older{i}.htm') for i in range(12)]
    rows = newer + [selected] + older
    payload = dict(cik='123', filings=dict(recent={k: [r[k] for r in rows] for k in selected}, files=[]))
    nomination = dict(issuer=base['issuer'], run_id=base['run_id'], cutoff=base['cutoff'],
        base_plan_sha256=digest(base), historical_discovery_sha256='a'*64,
        historical_receipt_sha256='b'*64, authorizing_instruction_sha256='c'*64, filings=[selected])
    plan = make_plan(identity, **kwargs, fpi_nomination=nomination)
    def respond(request):
        if 'submissions' in request.url.path:
            return httpx.Response(200, json=payload)
        if 'companyfacts' in request.url.path:
            return httpx.Response(200, json={'cik': '123', 'facts': {}})
        if request.url.path.endswith('index.json'):
            return httpx.Response(200, json={'directory': {'name': request.url.path.rsplit('/', 1)[0], 'item': []}})
        return httpx.Response(200, text='<html>No statement in synthetic original.</html>')
    directory = tmp_path / 'original'
    reader = BoundedReader(plan, directory, transport=httpx.MockTransport(respond))
    acquisition = asyncio.run(collect(reader))
    receipt = reader.receipts[0]
    # The fixture acts as the parent's preseal, before mutations under test.
    source_anchor = {
        'discovery_sha256': sha256_bytes((directory / receipt['artifact']).read_bytes()),
        'discovery_receipt_file_sha256': sha256_bytes((directory / 'request-001-attempt-1.receipt.json').read_bytes()),
    }
    return plan, acquisition, directory, reader.receipts, source_anchor, newer


def anchors(original):
    return {'source_anchor': original[4], 'target_manifest': original[5]}


def planned(original, budget=18):
    return probe.make_probe_plan(*original[:4], 'new-purpose-generation', datetime.now(timezone.utc), budget,
        **anchors(original))


def response_for(plan, request, body=b'<html><body>Notice of resignation of a director.</body></html>', attachment=False):
    filing = next(f for f in plan['filings'] if f['accessionNumber'].replace('-', '') in request.url.path)
    if request.url.path.endswith('index.json'):
        items = [{'name': filing['primaryDocument']}]
        if attachment:
            items.append({'name': 'ex99.htm'})
        return httpx.Response(200, json={'directory': {'name': request.url.path.rsplit('/', 1)[0], 'item': items}})
    return httpx.Response(200, content=body, headers={'Content-Type': 'text/html; charset=utf-8'})


def capture(original, tmp_path, *, plan=None, handler=None):
    plan = plan or planned(original)
    calls = []
    def send(request):
        calls.append(str(request.url))
        return handler(request) if handler else response_for(plan, request)
    reader = probe.PurposeProbeReader(plan, tmp_path / 'probe',
        original_plan=original[0], original_acquisition=original[1], original_directory=original[2],
        original_receipts=original[3], user_agent='offline-fixture-agent', transport=httpx.MockTransport(send),
        **anchors(original))
    result = asyncio.run(probe.collect_probe(reader))
    return reader, result, calls


def test_exact_nine_preserves_economic_bound_outside_inventory_and_original_generation(original):
    before = deepcopy((original[0], original[1], original[3]))
    plan = planned(original)
    assert len(plan['filings']) == 9 and len(plan['exact_requests']) == 18
    assert all(r['stage'] == 'document' for r in plan['exact_requests'][:9])
    assert all(r['stage'] == 'index' for r in plan['exact_requests'][9:])
    assert plan['economic_interim_candidate_cap'] == 2
    assert len(plan['economic_candidate_plan']['outside_bound']) == 21
    assert plan['source_binding']['original_generation'] == original[0]['run_id']
    assert not plan['financial_authority'] and not plan['source_use_eligible']
    assert (original[0], original[1], original[3]) == before


@pytest.mark.parametrize('budget', [-1, 19, True, '18'])
def test_invalid_task_budget_denied(original, budget):
    with pytest.raises(ValueError, match='budget_invalid'):
        planned(original, budget)


@pytest.mark.parametrize('mutation', ['raw', 'receipt', 'plan', 'acquisition', 'label'])
def test_original_provenance_is_replayed_not_caller_asserted(original, mutation):
    plan, acquisition, directory, receipts = original[:4]
    plan, acquisition, receipts = deepcopy(plan), deepcopy(acquisition), deepcopy(receipts)
    if mutation == 'raw':
        (directory / receipts[0]['artifact']).write_bytes(b'{}')
    elif mutation == 'receipt':
        receipts[0]['HTTP_status'] = 200
        receipts[0]['started_at'] = '2026-10-21T00:00:00+00:00'
        durable_json(directory / 'request-001-attempt-1.receipt.json', receipts[0])
    elif mutation == 'plan':
        plan['run_id'] = 'relabeled-original'
    elif mutation == 'acquisition':
        acquisition['current_candidate_plan']['outside_bound'] = []
    else:
        receipts[0]['independently_verified'] = True
    with pytest.raises(ValueError):
        probe.make_probe_plan(plan, acquisition, directory, receipts,
            'new-purpose-generation', datetime.now(timezone.utc), 18, **anchors(original))


def test_body_bound_nonfinancial_and_repeat_replay_have_no_financial_authority(original, tmp_path):
    reader, result, calls = capture(original, tmp_path)
    assert len(calls) == 18 and result['HTTP_attempts'] == 18
    assert result['status'] == 'CLASSIFIED'
    assert {f['classification'] for f in result['filings']} == {'CONFIRMED_NON_FINANCIAL'}
    assert all(f['purpose_evidence'] and f['source_receipts']['document']['raw_sha256'] for f in result['filings'])
    assert result['admitted_fact_count'] == 0 and not result['financial_authority'] and not result['native_ready']
    assert len(result['outside_bound_preserved']) == 21
    assert probe.replay_probe(reader.plan, *original[:4], reader.output,
        expected_capture_sha256=result['capture_sha256'], **anchors(original)) == result
    with pytest.raises(ValueError, match='single_capture'):
        asyncio.run(probe.collect_probe(reader))


@pytest.mark.parametrize('status', [403, 429])
def test_access_denial_is_one_attempt_latched_and_retained_not_absence(original, tmp_path, status):
    reader, result, calls = capture(original, tmp_path, handler=lambda _: httpx.Response(status, content=b'denied'))
    assert len(calls) == result['HTTP_attempts'] == 1
    assert result['status'] == 'STOPPED' and result['failures'][0]['HTTP_status'] == status
    assert result['failures'][0]['failure_class'] == 'SYSTEMIC_STOP'
    assert (reader.output / result['failures'][0]['artifact']).read_bytes() == b'denied'
    assert all(f['classification'] == 'UNKNOWN_UNRESOLVED' for f in result['filings'])
    request = reader.plan['exact_requests'][1]
    with pytest.raises(SystemicStop):
        asyncio.run(reader.read(request['stage'], request['url'], filing=request['filing']))
    assert len(calls) == 1


@pytest.mark.parametrize('error', [httpx.ReadTimeout, httpx.ConnectError])
def test_timeout_and_dns_transport_failure_remain_failure_with_global_cap(original, tmp_path, error):
    def fail(request):
        raise error('synthetic transport failure', request=request)
    _, result, calls = capture(original, tmp_path, handler=fail)
    assert len(calls) == 18 and result['HTTP_attempts'] == 18
    assert result['status'] == 'STOPPED' and result['attempt_budget_exhausted']
    assert all(r['error_type'] == error.__name__ and r['failure_class'] == 'TRANSIENT_TRANSPORT' for r in result['failures'])
    assert all(f['classification'] == 'UNKNOWN_UNRESOLVED' for f in result['filings'])


def test_retry_consumes_shared_budget_and_never_adds_nineteenth_attempt(original, tmp_path):
    reader, result, calls = capture(original, tmp_path, handler=lambda _: httpx.Response(503), plan=planned(original, 5))
    assert len(calls) == 5 and reader.attempts == 5
    assert [r['attempt'] for r in reader.receipts] == [1, 2, 3, 1, 2]
    assert result['task_attempts_reserved_elsewhere'] == 13 and result['attempt_budget_exhausted']


@pytest.mark.parametrize('kind', ['index_attachment', 'body_link', 'cover_reference', 'financial_words', 'unknown', 'monthly_revenue'])
def test_unknown_or_incomplete_content_never_becomes_nonfinancial(original, tmp_path, kind):
    plan = planned(original)
    bodies = {
        'index_attachment': b'<html>Notice of resignation.</html>',
        'body_link': b'<html>Notice of resignation. <a href="ex99.htm">Exhibit</a></html>',
        'cover_reference': b'<html>Notice of resignation. Attached hereto is Exhibit 99.</html>',
        'financial_words': b'<html>Quarterly financial statements. Notice of resignation.</html>',
        'unknown': b'<html>Form 6-K</html>',
        'monthly_revenue': b'<html>Monthly revenue for September.</html>',
    }
    _, result, _ = capture(original, tmp_path, plan=plan,
        handler=lambda r: response_for(plan, r, bodies[kind], kind == 'index_attachment'))
    assert all(f['classification'] == 'UNKNOWN_UNRESOLVED' for f in result['filings'])
    if kind in {'index_attachment', 'body_link', 'cover_reference'}:
        assert all('ATTACHMENT_REQUIRED_REMAINING_BUDGET_GAP' in f['reasons'] for f in result['filings'])


def test_zero_remaining_budget_keeps_all_nine_unknown_without_http(original, tmp_path):
    _, result, calls = capture(original, tmp_path, plan=planned(original, 0))
    assert calls == [] and result['status'] == 'STOPPED' and len(result['filings']) == 9


@pytest.mark.parametrize('reason', ['NG40_RESPONSE_SIZE_CAP', 'NG40_RESOURCE_GUARD',
    'NG40_PURPOSE_HTTP_SCOPE_OR_BUDGET_STOP'])
def test_transport_safety_stop_is_terminal_replayable_and_not_absence(original, tmp_path, reason):
    def stop(_):
        raise SystemicStop(reason)
    reader, result, calls = capture(original, tmp_path, handler=stop)
    assert len(calls) == result['HTTP_attempts'] == 1
    assert result['status'] == 'STOPPED'
    assert result['failures'][0]['systemic_reason'] == reason
    assert all(f['classification'] == 'UNKNOWN_UNRESOLVED' for f in result['filings'])
    assert reader.receipts[0]['HTTP_status'] is None


def test_unknown_transport_stop_cannot_be_relabelled_expected(original, tmp_path):
    def stop(_):
        raise SystemicStop('UNREVIEWED_STOP')
    with pytest.raises(ValueError, match='unrecognized_transport_stop'):
        capture(original, tmp_path, handler=stop)


@pytest.mark.parametrize('mutation', ['body', 'receipt', 'manifest', 'plan', 'omitted_failure', 'seal'])
def test_replay_rejects_tampering(original, tmp_path, mutation):
    reader, result, _ = capture(original, tmp_path)
    if mutation == 'body':
        (reader.output / reader.receipts[0]['artifact']).write_bytes(b'forged')
    elif mutation == 'receipt':
        changed = deepcopy(reader.receipts)
        changed[0]['HTTP_status'] = 429
        durable_json(reader.output / 'receipts.json', changed)
    elif mutation == 'manifest':
        durable_json(reader.output / 'request-manifest.json', [])
    elif mutation == 'plan':
        changed = deepcopy(reader.plan)
        changed['financial_authority'] = True
        durable_json(reader.output / 'plan.json', changed)
    elif mutation == 'omitted_failure':
        durable_json(reader.output / 'receipts.json', reader.receipts[:-1])
    expected = '0'*64 if mutation == 'seal' else result['capture_sha256']
    with pytest.raises(ValueError):
        probe.replay_probe(reader.plan, *original[:4], reader.output, expected_capture_sha256=expected,
            **anchors(original))


def test_unplanned_cross_accession_url_is_rejected_before_http(original, tmp_path):
    plan = planned(original)
    calls = []
    reader = probe.PurposeProbeReader(plan, tmp_path / 'probe', original_plan=original[0],
        original_acquisition=original[1], original_directory=original[2], original_receipts=original[3],
        user_agent='offline-fixture-agent', transport=httpx.MockTransport(lambda r: calls.append(r)),
        **anchors(original))
    with pytest.raises(SystemicStop, match='outside_exact_manifest'):
        asyncio.run(reader.read('document', sec_base(plan, plan['filings'][1]) + 'unlisted.htm', filing=plan['filings'][0]))
    assert calls == []


def test_generic_subset_manifest_does_not_require_nine_or_an_issuer_literal(original, tmp_path):
    subset = (*original[:5], original[5][:1])
    reader, result, calls = capture(subset, tmp_path)
    assert len(reader.plan['filings']) == 1 and len(calls) == 2
    assert result['filings'][0]['classification'] == 'CONFIRMED_NON_FINANCIAL'


@pytest.mark.parametrize('exact_header', [True, False])
def test_exact_sec_index_header_is_metadata_not_an_exhibit(original, tmp_path, exact_header):
    plan = planned(original)
    def response(request):
        result = response_for(plan, request)
        if request.url.path.endswith('index.json'):
            filing = next(f for f in plan['filings'] if f['accessionNumber'].replace('-', '') in request.url.path)
            data = result.json()
            prefix = filing['accessionNumber'] if exact_header else 'unverified-financial'
            data['directory']['item'].append({'name': prefix + '-index-headers.html'})
            return httpx.Response(200, json=data)
        return result
    _, result, _ = capture(original, tmp_path, plan=plan, handler=response)
    expected = 'CONFIRMED_NON_FINANCIAL' if exact_header else 'UNKNOWN_UNRESOLVED'
    assert {r['classification'] for r in result['filings']} == {expected}


def test_original_financial_period_classifier_is_diagnostic_not_field_use(original, tmp_path):
    subset = (*original[:5], original[5][:1])
    plan = planned(subset)
    body = b'''<html><body><h2>Consolidated Statements of Comprehensive Income</h2>
    <p>(In Thousands of New Taiwan Dollars)</p><table>
    <tr><th></th><th>2026-04-01 to 2026-06-30</th><th>2025-04-01 to 2025-06-30</th></tr>
    <tr><td>NET REVENUE</td><td>150</td><td>100</td></tr>
    <tr><td>INCOME FROM OPERATIONS</td><td>30</td><td>10</td></tr>
    </table></body></html>'''
    _, result, calls = capture(subset, tmp_path, plan=plan, handler=lambda r: response_for(plan, r, body))
    filing = result['filings'][0]
    assert len(calls) == 2 and filing['classification'] == 'FINANCIAL_WITH_FIELD_PERIOD'
    assert filing['economic_periods'] and filing['valid_occurrence_ids']
    assert not filing['financial_authority'] and not filing['source_use_eligible']
    assert not filing['economic_candidate'] and result['admitted_fact_count'] == 0
    assert not result['native_ready']


def test_primary_success_and_index_http_failure_stay_unknown(original, tmp_path):
    subset = (*original[:5], original[5][:1])
    plan = planned(subset)
    def handler(request):
        return httpx.Response(404) if request.url.path.endswith('index.json') else response_for(plan, request)
    _, result, calls = capture(subset, tmp_path, plan=plan, handler=handler)
    assert len(calls) == 2 and result['filings'][0]['classification'] == 'UNKNOWN_UNRESOLVED'
    assert result['failures'][0]['HTTP_status'] == 404
    assert result['filings'][0]['reasons'] == ['INDEX_FAILED_OR_NOT_ATTEMPTED']


@pytest.mark.parametrize('change', ['extra', 'duplicate', 'metadata', 'purpose_label', 'absent'])
def test_only_complete_exact_presealed_manifest_is_accepted(original, change):
    targets = deepcopy(original[5])
    if change == 'extra': targets.append(deepcopy(targets[0]))
    if change == 'duplicate': targets[1] = deepcopy(targets[0])
    if change == 'metadata': targets[0]['reportDate'] = '2026-06-30'
    if change == 'purpose_label': targets[0]['purpose'] = 'CONFIRMED_NON_FINANCIAL'
    if change == 'absent': targets[0]['accessionNumber'] = '0000000123-26-999999'
    with pytest.raises(ValueError):
        probe.make_probe_plan(*original[:4], 'new-purpose-generation', datetime.now(timezone.utc), 18,
            source_anchor=original[4], target_manifest=targets)
