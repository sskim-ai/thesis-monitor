import asyncio
from datetime import datetime, timezone
from io import BytesIO
import json
import zipfile

import httpx
import pytest

from app.services.bounded_financial_acquisition import SystemicStop, collect, make_plan
from app.services.bounded_financial_projection import verify_capture
from app.services.dart_report_artifact import verified_dart_report
from app.services.sealed_financial_reader import SealedFinancialReader
from app.services.sealed_financial_slots import financial_slots
from tests.test_r9_rev11_response_slots import financial, run_slots
from tests.test_r9_rev11_sealed_dispatch import CONFIG, OWNER


CURRENT = '20261113000001'
AMENDED = '20261116000002'


def archive(receipt=AMENDED, issuer='00000123'):
    body = BytesIO()
    with zipfile.ZipFile(body, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr(receipt + '.xml',
            f'<DOCUMENT><DOCUMENT-NAME ACODE="11013">분기보고서</DOCUMENT-NAME>'
            f'<COMPANY-NAME AREGCIK="{issuer}">회사</COMPANY-NAME><BODY></BODY></DOCUMENT>')
    return body.getvalue()


def reader_case(tmp_path, response):
    p = make_plan(financial('kr')['security'], market='kr', cutoff=datetime(2026, 11, 28, tzinfo=timezone.utc),
        run_id='fresh-1', maximum_retries_per_request=0, dart_business_report=True)
    descriptors = financial_slots(p, owner='test-owner', owner_sha256=OWNER, config_sha256=CONFIG)
    dispatcher = run_slots(tmp_path, descriptors)
    calls = []

    def wire(request):
        calls.append((request.url.path, dict(request.url.params)))
        if request.url.path.endswith('/list.json'):
            rows = [dict(corp_code=p['issuer'], stock_code=p['ticker'], corp_name='회사',
                         report_nm=prefix+'분기보고서 (2026.09)', rcept_no=no, rcept_dt=no[:8])
                    for prefix, no in [('', CURRENT), ('[기재정정]', AMENDED)]]
            return httpx.Response(200, json={'status': '000', 'list': rows, 'total_page': 1})
        if request.url.path.endswith('/fnlttSinglAcntAll.json'):
            return httpx.Response(200, json={'status': '013', 'list': []})
        assert request.url.path == '/api/document.xml'
        assert dict(request.url.params) == {'rcept_no': AMENDED, 'crtfc_key': 'PLAN_CREDENTIAL'}
        status, raw = response
        return httpx.Response(status, content=raw, headers={'Content-Type': 'application/x-msdownload'})

    reader = SealedFinancialReader(p, tmp_path / 'owner', dispatcher=dispatcher, transport=httpx.MockTransport(wire),
                                  api_key='PLAN_CREDENTIAL')
    return reader, calls


def test_correction_only_current_report_exact_wire_replay_and_integrity(tmp_path):
    reader, calls = reader_case(tmp_path, (200, archive()))
    value = asyncio.run(collect(reader))
    verify_capture(reader.plan, value, reader.output, reader.receipts)
    assert [path for path, _ in calls] == ['/api/list.json', '/api/fnlttSinglAcntAll.json',
                                            '/api/fnlttSinglAcntAll.json', '/api/document.xml']
    assert len(value['documents']) == 2 and value['dart_report']['status'] == 'CAPTURED'
    xml, proof = verified_dart_report(reader.plan, value, reader.output, reader.receipts)
    assert proof['receipt_no'] == AMENDED and proof['filing']['correction'] and proof['xml_name'] == AMENDED + '.xml'
    assert b'DOCUMENT' in xml and proof['retrieved_at'] == reader.receipts[-1]['finished_at']
    path = reader.output / 'request-004.plan.json'
    path.write_text(json.dumps(dict(json.loads(path.read_bytes()), params={'rcept_no': CURRENT})))
    assert verified_dart_report(reader.plan, value, reader.output, reader.receipts) is None


@pytest.mark.parametrize('status,raw', [(404, b''), (200, b'not a ZIP'), (200, archive(issuer='99999999')),
    (200, archive(CURRENT)), (200, b'<result><status>014</status></result>')])
def test_optional_report_denial_preserves_statements_and_no_retry(tmp_path, status, raw):
    reader, calls = reader_case(tmp_path, (status, raw))
    value = asyncio.run(collect(reader))
    assert len(calls) == 4 and len(value['documents']) == 2 and not value['denials']
    assert value['dart_report']['status'] == 'UNAVAILABLE'
    assert verified_dart_report(reader.plan, value, reader.output, reader.receipts) is None
    verify_capture(reader.plan, value, reader.output, reader.receipts)


@pytest.mark.parametrize('raw', [b'<result><status>020</status></result>', b'{"status":"010"}'])
def test_report_provider_account_and_rate_errors_keep_systemic_stop(tmp_path, raw):
    reader, calls = reader_case(tmp_path, (200, raw))
    with pytest.raises(SystemicStop, match='systemic_stop'):
        asyncio.run(collect(reader))
    assert len(calls) == 4 and reader.dispatcher.halted


def test_unusable_existing_archive_is_accounted_without_refetching(tmp_path):
    reader, calls = reader_case(tmp_path, (200, archive()))

    class BrokenArchive:
        def find(self, plan, filing):
            raise ValueError('retained_original_hash_mismatch')

    reader.dispatcher.dart_report_store = BrokenArchive()
    value = asyncio.run(collect(reader))
    assert len(calls) == 3 and len(value['documents']) == 2 and not value['denials']
    assert value['dart_report']['reason'] == 'DART_RETAINED_DOCUMENT_UNAVAILABLE'
    final = reader.dispatcher.results['financial:FIXTURE:filing1:report']
    assert final['status'] == 'FAILED' and not final['attempts'] and not final['raw_sha256']
