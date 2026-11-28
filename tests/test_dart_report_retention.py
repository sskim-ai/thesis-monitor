from copy import deepcopy
from datetime import datetime, timezone
from io import BytesIO
from types import SimpleNamespace
import zipfile

import pytest

from app.services.retained_dart_reports import DartReportStore, document_proof, verify_retained_dart_document
from app.services.unified_run_artifacts import sha256_bytes
from app.services.unified_snapshot_contract import digest


def fixture():
    f = dict(ticker='111111', corp_code='12345678', receipt_no='20261110001234', role='current',
             business_year=2026, receipt_date='2026-11-10', report_code='11014')
    xml = b'<DOCUMENT><DOCUMENT-NAME ACODE="11013">Quarterly</DOCUMENT-NAME><COMPANY-NAME AREGCIK="12345678">Example</COMPANY-NAME><BODY/></DOCUMENT>'
    out = BytesIO()
    with zipfile.ZipFile(out, 'w') as archive:
        archive.writestr(f['receipt_no'] + '.xml', xml)
    data = out.getvalue()
    plan = dict(provider='opendart', ticker=f['ticker'], issuer=f['corp_code'], run_id='synthetic-old')
    attempt = dict(status=200, error=None, raw_sha256=sha256_bytes(data), started_at='2026-11-11T01:00:00+00:00',
                   finished_at='2026-11-11T01:00:02+00:00')
    final = dict(status='PASS', attempts=[attempt], logical_request_id='financial:111111:filing1:report',
                 generation_id=plan['run_id'], raw_sha256=sha256_bytes(data), retrieval_time=attempt['finished_at'])
    final['receipt_sha256'] = digest(final)
    return f, data, plan, final


def test_wire_once_then_reuse_same_document_after_next_discovery(tmp_path):
    f, raw, plan, final = fixture()
    source = tmp_path/'kr-2026-11-11'/'source'
    store = DartReportStore(tmp_path, source_root=source)
    body = source/'dispatch'/'raw'/final['logical_request_id']/'source.body'
    body.parent.mkdir(parents=True)
    body.write_bytes(raw)
    assert store.find(plan, f) is None
    store.put(plan, f, raw, final)
    next_run = dict(plan, run_id='synthetic-new')
    store = DartReportStore(tmp_path, source_root=tmp_path/'kr-2026-11-12'/'source')
    proof, doc = store.find(next_run, f)
    assert doc == raw
    d = SimpleNamespace(market='kr', provider='opendart', endpoint_operation='dart_report', subject=f['ticker'],
                        response_binding=SimpleNamespace(kind='DART_REPORT',policy_json='{"issuer":"12345678"}'))
    wire = dict(method='GET', url='https://opendart.fss.or.kr/api/document.xml?rcept_no='+f['receipt_no'])
    receipt = verify_retained_dart_document(d,wire,f,proof,doc,
        frozen_at=datetime(2026,11,12,tzinfo=timezone.utc),selected_at='2026-11-12T01:00:01+00:00',
        discovery_finished_at='2026-11-12T01:00:00+00:00')
    assert receipt['finished_at'] == final['attempts'][0]['finished_at']
    assert store.find(next_run, dict(f,receipt_no='20261112001235')) is None
    with pytest.raises(ValueError):
        store.find(dict(next_run,issuer='87654321'), f)


@pytest.mark.parametrize('change', ['data', 'time', 'failed', 'other-slot'])
def test_invalid_origin_cannot_create_reusable_entry(tmp_path, change):
    f, raw, plan, final = fixture()
    store = DartReportStore(tmp_path)
    if change == 'data':
        raw += b'altered'
    if change == 'time':
        final['attempts'][0]['started_at'] = '2026-11-12T00:00:00+00:00'
    if change == 'failed':
        final['attempts'][0]['status'] = 403
    if change == 'other-slot':
        final['logical_request_id'] = 'financial:222222:filing1:report'
    final['receipt_sha256'] = digest({k:v for k,v in final.items() if k != 'receipt_sha256'})
    with pytest.raises(ValueError):
        store.put(plan,f,raw,final)
    assert store.find(plan,f) is None


def test_import_is_idempotent_and_preserves_first_acquisition(tmp_path):
    f, raw, plan, final = fixture()
    store = DartReportStore(tmp_path)
    store.save(f,raw,document_proof(f,raw,dict(kind='regular', **final),final['retrieval_time']))
    again = deepcopy(final)
    again['generation_id'] = 'synthetic-second'
    again['receipt_sha256'] = digest({k:v for k,v in again.items() if k != 'receipt_sha256'})
    store.save(f,raw,document_proof(f,raw,dict(kind='regular', **again),again['retrieval_time']))
    assert store.find(plan,f)[0] == document_proof(f,raw,dict(kind='regular', **final),final['retrieval_time'])
