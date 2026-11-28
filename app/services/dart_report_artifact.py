"""Read the selected OpenDART periodic report directly from its original document.zip."""
from datetime import datetime
from io import BytesIO
import json
from pathlib import Path
import re
import zipfile
import zlib

from app.services.unified_run_artifacts import sha256_bytes
from app.services.unified_snapshot_contract import digest


DART_REPORT_URL = 'https://opendart.fss.or.kr/api/document.xml'
_MAX_XML = 128 * 1024 * 1024


def eligible_report_filing(rows, filing):
    if not filing or not re.fullmatch(r'[0-9]{14}', filing['receipt_no']):
        return False
    selected = [r for r in rows if r.get('rcept_no') == filing['receipt_no']]
    return bool(selected) and all(r.get('stock_code') == filing['ticker']
        and r.get('corp_code') == filing['corp_code'] for r in selected)


def document_error_status(raw):
    """JSON/XML OpenDART error envelopes are also returned with HTTP 200."""
    if not raw or len(raw) > 65536:
        return None
    prefix = raw.lstrip()
    if prefix.startswith(b'{'):
        try:
            value = json.loads(raw)
        except ValueError:
            return None
        status = value.get('status') if isinstance(value, dict) else None
        return status if isinstance(status, str) and re.fullmatch(r'[0-9]{3}', status) else None
    if prefix.startswith(b'<'):
        match = re.search(br'<status>\s*([0-9]{3})\s*</status>', prefix, re.I)
        return match.group(1).decode() if match else None
    return None


def extract_dart_xml(raw, receipt_no, *, corp_code=None, report_code=None):
    """Read just the receipt-named main XML. Other ZIP members are never extracted."""
    if (not re.fullmatch(r'[0-9]{14}', str(receipt_no)) or not raw.startswith(b'PK\x03\x04')
            or len(raw) > _MAX_XML):
        raise ValueError('invalid_dart_document')
    name = receipt_no + '.xml'
    try:
        with zipfile.ZipFile(BytesIO(raw)) as archive:
            members = [m for m in archive.infolist() if m.filename == name]
            if len(members) != 1 or not 0 < members[0].file_size <= _MAX_XML:
                raise ValueError('missing_or_ambiguous_dart_report_xml')
            xml = archive.read(members[0])
    except (zipfile.BadZipFile, RuntimeError, EOFError, OSError, zlib.error) as exc:
        raise ValueError('invalid_dart_document_archive') from exc
    header = xml[:65536].split(b'<BODY', 1)[0]
    if not re.search(br'<DOCUMENT(?:\s|>)', header):
        raise ValueError('dart_document_header_missing')
    if corp_code is not None:
        issuer = re.findall(br'<COMPANY-NAME\b[^>]*?\bAREGCIK=["\']([0-9]{8})["\']', header)
        if issuer != [str(corp_code).encode('ascii')]:
            raise ValueError('dart_document_issuer_mismatch')
    if report_code is not None:
        form = re.findall(br'<DOCUMENT-NAME\b[^>]*?\bACODE=["\']([0-9]{5})["\']', header)
        # OpenDART uses one XML quarterly document form for the first and third quarters.
        allowed = {'11014': {b'11013', b'11014'}, '11013': {b'11013'},
                   '11011': {b'11011'}, '11012': {b'11012'}}
        if len(form) != 1 or form[0] not in allowed.get(report_code, ()):
            raise ValueError('dart_document_form_mismatch')
    return xml, name


def verified_dart_report(plan, acquisition, directory, receipts):
    """Optional business context must agree with today's selected filing and original bytes."""
    report = acquisition.get('dart_report') or {}
    if not plan.get('dart_business_report') or report.get('status') not in {'CAPTURED', 'RETAINED'}:
        return None
    filing = report.get('filing')
    current = [f for f in acquisition['selected_filings'] if f['role'] == 'current']
    if (not filing or current != [filing] or filing['corp_code'] != plan['issuer']
            or filing['ticker'] != plan['ticker'] or plan['market'] != 'kr' or plan['provider'] != 'opendart'):
        return None
    matches = [r for r in receipts if r['stage'] == 'dart_report' and not r.get('failure_class')
               and r.get('artifact') == report.get('artifact') and r.get('filing') == filing]
    if len(matches) != 1:
        return None
    r = matches[0]
    retained = 'retained_dart_origin' in r
    artifact = str(r['artifact'])
    if (r['plan_sha256'] != digest(plan) or not re.fullmatch(r'request-\d+-(?:attempt-1|retained)\.body', artifact)
            or retained != (report['status'] == 'RETAINED')
            or (r['attempt'], r['HTTP_status']) != ((0, None) if retained else (1, 200))):
        return None
    try:
        directory = Path(directory)
        local = artifact.split('-retained.')[0].split('-attempt-')[0]
        frozen = json.loads((directory / (local + '.plan.json')).read_bytes())
        if (digest(frozen) != r['request_sha256'] or frozen['plan_sha256'] != r['plan_sha256']
                or frozen['logical_id'] != r['logical_id'] or frozen.get('filing') != filing
                or frozen.get('method') != 'GET' or frozen.get('stage') != 'dart_report'
                or frozen.get('url') != DART_REPORT_URL or frozen.get('params') != {'rcept_no': filing['receipt_no']}):
            return None
        raw = (directory / artifact).read_bytes()
        if sha256_bytes(raw) != r['raw_sha256']:
            return None
        xml, name = extract_dart_xml(raw, filing['receipt_no'], corp_code=filing['corp_code'],
                                     report_code=filing['report_code'])
        if datetime.fromisoformat(r['finished_at']).utcoffset() is None:
            return None
    except (OSError, ValueError):
        return None
    return xml, dict(receipt_no=filing['receipt_no'], corp_code=filing['corp_code'], ticker=filing['ticker'],
        report_code=filing['report_code'], filing_date=filing['receipt_date'], business_year=filing['business_year'],
        zip_sha256=r['raw_sha256'], xml_sha256=sha256_bytes(xml), retrieved_at=r['finished_at'],
        xml_name=name, artifact=artifact, filing=dict(filing))
