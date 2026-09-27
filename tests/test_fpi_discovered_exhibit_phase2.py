import asyncio
from copy import deepcopy
import json
import zipfile

import httpx
import pytest

from app.services.bounded_financial_acquisition import AcquisitionDenied, SystemicStop, sec_base, exhibit_selection
from app.services.bounded_fpi_followup import request_manifest
from app.services.fpi_discovered_exhibit_phase2 import (
    SEC_FPI_MAX_PHASE2_EXHIBIT_DOCS_PER_SUBJECT, eligible_discovered, make_phase2_plan,
    Phase2Reader, verify_phase2, sealed_source,
)
from app.services.unified_run_artifacts import durable_json, sha256_bytes
from app.services.unified_snapshot_contract import digest
from test_bounded_financial_acquisition import plan, filing
from test_residual_financial_semantics import html_statement
from app.services.sec_fpi_financial_purpose import classify_document, select_economic_period


def fixture(n=1, suffix='.htm'):
    p = plan(foreign=True)
    fs = [{**filing('6-K', ordinal=i + 1), 'role': 'current'} for i in range(n)]
    first = {'parent_plan_sha256': digest(p), 'candidates': fs}
    rows, receipts, files = [], [], {}
    prefix = 'followup-phase/followup/' + p['ticker'] + '/'
    for f in fs:
        primary = b'<p>Financial results are attached.</p>'
        index = json.dumps({'directory': {'item': [{'name': 'ex99' + suffix}]}}).encode()
        for stage, raw in [('index', index), ('document', primary)]:
            logical = p['ticker'] + f':request-{len(receipts) + 1:03d}'
            request = {'stage': stage, 'method': 'GET', 'filing': f, 'params': {},
                'url': sec_base(p, f) + ('index.json' if stage == 'index' else f['primaryDocument']),
                'logical_id': logical, 'plan_sha256': digest(first)}
            artifact = logical.split(':')[-1] + '-attempt-1.body'
            receipts.append({'stage': stage, 'filing': f, 'logical_id': logical, 'failure_class': None,
                'artifact': artifact, 'request_sha256': digest(request), 'plan_sha256': digest(first), 'raw_sha256': sha256_bytes(raw)})
            files[prefix + artifact] = raw
            files[prefix + logical.split(':')[-1] + '.plan.json'] = json.dumps(request).encode()
        selected = exhibit_selection(json.loads(index), primary.decode(), p, f)
        rows.append({'ticker': p['ticker'], 'filing': f, 'existing_selector_denial': None,
            'existing_selector_eligible_urls': selected, 'newly_known_exhibit_urls': selected,
            'index_sha256': sha256_bytes(index), 'primary_sha256': sha256_bytes(primary),
            'primary_source_url': sec_base(p, f) + f['primaryDocument']})
    files.update({prefix + 'plan.json': json.dumps(first).encode(), prefix + 'receipts.json': json.dumps(receipts).encode(),
        'source-parent/financial-acquisition-plan.json': json.dumps({'entries': [p]}).encode(),
        'unrequested-exhibit-diagnostics.json': json.dumps(rows).encode()})
    return p, rows, {'files': files, 'zip_sha256': 'a' * 64}


@pytest.mark.parametrize('n', [0, 1, 3, 4, 8])
def test_generic_finite_cap(n):
    p, rows, src = fixture(n)
    result = make_phase2_plan(p, src)
    assert len(result['exact_requests']) == min(n, SEC_FPI_MAX_PHASE2_EXHIBIT_DOCS_PER_SUBJECT)
    assert result['maximum_HTTP_attempts'] == min(n, 3) * 3
    assert len(result['excluded']) == max(0, n - 3)
    assert all(r['reason'] == 'FPI_PHASE2_EXHIBIT_BOUND_EXHAUSTED' for r in result['excluded'])
    assert not result['recursive_discovery']
    assert result['limits']['discovery'] == result['limits']['companyfacts'] == result['limits']['indexes_per_filing'] == 0


def test_duplicate_does_not_consume_slot():
    p, rows, _ = fixture()
    rows[0]['existing_selector_eligible_urls'] *= 2
    requests, excluded = eligible_discovered(p, rows * 2)
    assert len(requests) == 1 and not excluded


@pytest.mark.parametrize('suffix,allowed', [('.html', True), ('.xml', True), ('.txt', True),
    ('.jpg', False), ('.png', False), ('.pdf', False), ('.exe', False)])
def test_supported_types(suffix, allowed):
    p, rows, src = fixture(suffix=suffix)
    value = make_phase2_plan(p, src)
    assert len(value['exact_requests']) == int(allowed)
    if not allowed:
        assert value['excluded'][0]['reason'] == 'UNSUPPORTED_DOCUMENT_TYPE_NO_OCR'


@pytest.mark.parametrize('kind', ['issuer', 'accession', 'host', 'query', 'fragment', 'traversal', 'primary', 'undiscovered'])
def test_exact_identity_negatives(kind):
    p, rows, _ = fixture()
    old = rows[0]['existing_selector_eligible_urls'][0]
    url = {'issuer': old.replace('/123/', '/456/'), 'accession': old.replace('000000000126000001', '000000000126000099'),
        'host': old.replace('www.sec.gov', 'other.invalid'), 'query': old + '?v=1', 'fragment': old + '#table',
        'traversal': old.replace('ex99.htm', '../ex99.htm'), 'primary': rows[0]['primary_source_url'],
        'undiscovered': old.replace('ex99.htm', 'new-ex99.htm')}[kind]
    if kind == 'accession':
        url = sec_base(p, {**rows[0]['filing'], 'accessionNumber': '0000000001-26-999999'}) + 'ex99.htm'
    rows[0]['existing_selector_eligible_urls'] = [url]
    if kind != 'undiscovered':
        rows[0]['newly_known_exhibit_urls'] = [url]
    with pytest.raises((ValueError, AcquisitionDenied)):
        eligible_discovered(p, rows)


@pytest.mark.parametrize('key', ['index_sha256', 'primary_sha256', 'primary_source_url', 'existing_selector_eligible_urls'])
def test_sealed_diagnostic_replayed_not_trusted_label(key):
    p, rows, src = fixture()
    rows[0][key] = [] if key.endswith('urls') else 'tampered'
    src['files']['unrequested-exhibit-diagnostics.json'] = json.dumps(rows).encode()
    with pytest.raises(ValueError):
        make_phase2_plan(p, src)


def test_parent_binding():
    p, _, src = fixture()
    changed = deepcopy(p)
    changed['security']['canonical_company_id'] = 'another'
    with pytest.raises(ValueError, match='parent_plan_binding'):
        make_phase2_plan(changed, src)


def setup_reader(tmp_path, *, n=1, transport=None):
    p, _, src = fixture(n)
    second = make_phase2_plan(p, src)
    durable_json(tmp_path / 'plan.json', second)
    durable_json(tmp_path / 'request-manifest.json', [{'request': r, 'request_sha256': digest(r)} for r in request_manifest(second)])
    reader = Phase2Reader(second, tmp_path, transport=transport)
    reader.select(second['candidates'])
    return p, src, second, reader


def test_zero_request_subject(tmp_path):
    p, src, second, reader = setup_reader(tmp_path, n=0)
    durable_json(tmp_path / 'receipts.json', [])
    result = verify_phase2(p, src, tmp_path)
    assert result['logical_requests'] == 0 and not result['documents'] and not result['unattempted']
    with pytest.raises(SystemicStop):
        asyncio.run(reader.read('discovery', 'https://data.sec.gov/submissions/CIK0000000123.json'))


def test_successful_html_uses_existing_purpose_period_owner_no_recursion(tmp_path):
    calls = []
    def transport(req):
        calls.append(str(req.url))
        return httpx.Response(200, text=html_statement() + '<a href="new.htm">financial statements</a>', headers={'content-type': 'text/html; charset=UTF-8'})
    p, src, second, reader = setup_reader(tmp_path, transport=httpx.MockTransport(transport))
    asyncio.run(reader.read(**second['exact_requests'][0]))
    durable_json(tmp_path / 'receipts.json', reader.receipts)
    result = verify_phase2(p, src, tmp_path)
    doc = result['documents'][0]
    purpose = classify_document(doc['raw'], url=doc['url'], filing=doc['filing'], plan=p)
    assert purpose['financial_authority'] and purpose['occurrences']
    assert select_economic_period([purpose])['status'] == 'PASS'
    assert len(calls) == 1
    with pytest.raises(SystemicStop):
        asyncio.run(reader.read('document', doc['url'].replace('ex99.htm', 'new.htm'), filing=doc['filing']))
    assert len(calls) == 1


@pytest.mark.parametrize('status', [400, 401, 403, 404, 422])
def test_4xx_not_retried_and_independent_next_entry_continues(tmp_path, status):
    count = []
    def transport(req):
        count.append(str(req.url))
        return httpx.Response(status if len(count) == 1 else 200, text=html_statement(), headers={'content-type': 'text/html'})
    p, src, second, reader = setup_reader(tmp_path, n=2, transport=httpx.MockTransport(transport))
    with pytest.raises(AcquisitionDenied) as exc:
        asyncio.run(reader.read(**second['exact_requests'][0]))
    assert not isinstance(exc.value, SystemicStop)
    asyncio.run(reader.read(**second['exact_requests'][1]))
    durable_json(tmp_path / 'receipts.json', reader.receipts)
    result = verify_phase2(p, src, tmp_path)
    assert len(count) == 2 and len(result['documents']) == 1


@pytest.mark.parametrize('mime', ['image/jpeg', 'image/png', 'application/pdf', 'application/octet-stream', ''])
def test_unexpected_response_type_cannot_supply_financial_evidence(tmp_path, mime):
    p, src, second, reader = setup_reader(tmp_path, transport=httpx.MockTransport(
        lambda req: httpx.Response(200, content=html_statement().encode(), headers={'content-type': mime})))
    asyncio.run(reader.read(**second['exact_requests'][0]))
    durable_json(tmp_path / 'receipts.json', reader.receipts)
    result = verify_phase2(p, src, tmp_path)
    assert not result['documents'] and result['denials'][0]['reason'] == 'UNSUPPORTED_RESPONSE_MIME'


def test_transient_retry_byte_identical_bounded(tmp_path):
    requests = []
    def transport(req):
        requests.append((str(req.url), req.method, req.content))
        return httpx.Response(503, text='unavailable', headers={'content-type': 'text/plain'})
    p, src, second, reader = setup_reader(tmp_path, transport=httpx.MockTransport(transport))
    with pytest.raises(AcquisitionDenied):
        asyncio.run(reader.read(**second['exact_requests'][0]))
    durable_json(tmp_path / 'receipts.json', reader.receipts)
    assert len(requests) == 3 and len(set(requests)) == 1
    assert verify_phase2(p, src, tmp_path)['attempts'] == 3


@pytest.mark.parametrize('target', ['body', 'receipt', 'request', 'plan', 'manifest'])
def test_phase2_receipt_tampering_fails_closed(tmp_path, target):
    p, src, second, reader = setup_reader(tmp_path, transport=httpx.MockTransport(
        lambda req: httpx.Response(200, text=html_statement(), headers={'content-type': 'text/html'})))
    asyncio.run(reader.read(**second['exact_requests'][0]))
    durable_json(tmp_path / 'receipts.json', reader.receipts)
    filename = {'body': 'request-001-attempt-1.body', 'receipt': 'receipts.json', 'request': 'request-001.plan.json',
        'plan': 'plan.json', 'manifest': 'request-manifest.json'}[target]
    path = tmp_path / filename
    if target == 'body':
        path.write_bytes(b'changed')
    else:
        value = json.loads(path.read_bytes())
        if target == 'receipt':
            value[0]['request_sha256'] = 'bad'
        elif target == 'manifest':
            value[0]['request']['url'] = 'https://other.invalid'
        else:
            value['changed'] = True
        path.write_text(json.dumps(value))
    with pytest.raises(ValueError):
        verify_phase2(p, src, tmp_path)


def test_sealed_zip_exact_members_hash_size(tmp_path):
    bundle = tmp_path / 'source.zip'
    raw = b'fixed source'
    manifest = {'source.txt': {'sha256': sha256_bytes(raw), 'bytes': len(raw)}}
    with zipfile.ZipFile(bundle, 'x') as archive:
        archive.writestr('source.txt', raw)
        archive.writestr('bundle-manifest.json', json.dumps(manifest))
    sha = sha256_bytes(bundle.read_bytes())
    assert sealed_source(bundle, sha)['files']['source.txt'] == raw
    with pytest.raises(ValueError, match='zip_identity'):
        sealed_source(bundle, 'f' * 64)
    with zipfile.ZipFile(bundle, 'a') as archive:
        archive.writestr('unmanifested', b'bad')
    with pytest.raises(ValueError, match='manifest_members'):
        sealed_source(bundle, sha256_bytes(bundle.read_bytes()))
