"""Exact selected OpenDART documents retained under the regular run root."""
from datetime import datetime
import json
from pathlib import Path
import re
import tempfile
from urllib.parse import parse_qs, urlsplit
from zoneinfo import ZoneInfo

from app.services.unified_run_artifacts import durable_bytes, durable_json, sha256_bytes
from app.services.unified_snapshot_contract import digest


def filing_identity(filing):
    identity = {k: filing[k] for k in ('ticker', 'corp_code', 'receipt_no', 'receipt_date',
                                       'report_code', 'business_year')}
    if (not re.fullmatch(r'[0-9]{6}', identity['ticker'])
            or not re.fullmatch(r'[0-9]{8}', identity['corp_code'])
            or not re.fullmatch(r'[0-9]{14}', identity['receipt_no'])):
        raise ValueError('dart_retained_identity_invalid')
    return identity


def document_proof(filing, raw, origin, received_at):
    """Keep original wire evidence distinct from a new generation's selection."""
    start = origin['attempt']['at'] if origin['kind'] == 'independent' else origin['attempts'][-1]['started_at']
    receipt = dict(started_at=start, finished_at=received_at)
    return dict(pin=dict(filing=filing_identity(filing), raw_sha256=sha256_bytes(raw),
                         origin_sha256=digest(origin), retrieved_at=received_at),
                original_receipt=receipt, origin=origin)


def check_origin(filing, proof, raw):
    pin, origin = proof['pin'], proof['origin']
    if pin['filing'] != filing_identity(filing) or pin['origin_sha256'] != digest(origin) or pin['raw_sha256'] != sha256_bytes(raw):
        raise ValueError('dart_retained_source_mismatch')
    if origin['kind'] == 'independent':
        a, r = origin['attempt'], origin['result']
        if (a['event'] != 'ATTEMPT' or r['event'] != 'RESULT' or a['number'] != r['number']
                or a['endpoint'] != 'document.xml' or r['endpoint'] != a['endpoint']
                or a['subject'] != filing['ticker'] or r['subject'] != a['subject']
                or a['params'] != {'rcept_no': filing['receipt_no']} or r['http'] != 200
                or r['error'] is not None or r['bytes'] != len(raw)
                or r['transport_outcome'] != 'RESPONSE_CONFIRMED'):
            raise ValueError('dart_independent_origin_invalid')
        start, finish = a['at'], r['at']
    elif origin['kind'] == 'regular':
        final = {k: v for k, v in origin.items() if k != 'kind'}
        attempt, = final['attempts']
        if (digest({k:v for k,v in final.items() if k != 'receipt_sha256'}) != final['receipt_sha256']
                or final['status'] != 'PASS' or attempt['status'] != 200 or attempt['error'] is not None
                or final['raw_sha256'] != pin['raw_sha256'] or attempt['raw_sha256'] != final['raw_sha256']
                or final['retrieval_time'] != attempt['finished_at']
                or pin['retrieved_at'] != final['retrieval_time']):
            raise ValueError('dart_regular_origin_invalid')
        start, finish = attempt['started_at'], attempt['finished_at']
    else:
        raise ValueError('dart_retained_origin_kind')
    original = proof['original_receipt']
    times = [datetime.fromisoformat(v) for v in (start, finish, pin['retrieved_at'])]
    if (original != dict(started_at=start, finished_at=pin['retrieved_at'])
            or any(t.utcoffset() is None for t in times) or not times[0] <= times[1] <= times[2]
            or filing['receipt_date'] > times[2].astimezone(ZoneInfo('Asia/Seoul')).date().isoformat()):
        raise ValueError('dart_retained_origin_time_invalid')
    return original


def verify_retained_dart_document(descriptor, wire, filing, proof, raw, *, frozen_at, selected_at, discovery_finished_at):
    binding = descriptor.response_binding
    url = urlsplit(wire['url'])
    if (descriptor.market != 'kr' or descriptor.provider != 'opendart' or descriptor.endpoint_operation != 'dart_report'
            or binding is None or binding.kind != 'DART_REPORT' or wire['method'] != 'GET'
            or (url.scheme, url.netloc, url.path) != ('https', 'opendart.fss.or.kr', '/api/document.xml')
            or parse_qs(url.query).get('rcept_no') != [filing['receipt_no']]
            or descriptor.subject != filing['ticker'] or filing['role'] != 'current'
            or json.loads(binding.policy_json)['issuer'] != filing['corp_code']):
        raise ValueError('dart_retained_current_selection_required')
    original = check_origin(filing, proof, raw)
    if not (datetime.fromisoformat(original['finished_at']) < frozen_at <=
            datetime.fromisoformat(discovery_finished_at) <= datetime.fromisoformat(selected_at)):
        raise ValueError('dart_retained_document_time_mismatch')
    return original


class DartReportStore:
    def __init__(self, run_root, *, source_root=None):
        self.source_root = Path(source_root) if source_root is not None else None
        self.root = Path(run_root) / 'retained-dart'

    def _directory(self, filing):
        identity = filing_identity(filing)
        directory = self.root / identity['corp_code'] / identity['receipt_no']
        if any(p.is_symlink() for p in (directory, *directory.parents)):
            raise ValueError('dart_retained_path_invalid')
        return directory

    def find(self, plan, filing):
        if (plan['provider'] != 'opendart' or filing['role'] != 'current'
                or (plan['issuer'], plan['ticker']) != (filing['corp_code'], filing['ticker'])):
            raise ValueError('dart_retained_current_selection_required')
        directory = self._directory(filing)
        if directory.exists():
            proof_path, doc_path = directory/'origin.json', directory/'document.zip'
        else:
            # A regular miss saves its original body in dispatch. A small accession-named
            # file in that same source tree makes it discoverable across regular cycles.
            marker = Path('source')/'financial'/filing['ticker']/('dart-origin-'+filing['receipt_no']+'.json')
            for session in sorted(self.root.parent.glob('kr-????-??-??'), reverse=True):
                if self.source_root is not None and session == self.source_root.parent:
                    continue
                proof_path = session/marker
                if proof_path.exists() or proof_path.is_symlink():
                    key = f"financial:{filing['ticker']}:filing1:report"
                    doc_path = session/'source'/'dispatch'/'raw'/key/'source.body'
                    break
            else:
                return None
        for path in (proof_path, doc_path):
            if not path.is_file() or any(p.is_symlink() for p in (path, *path.parents)):
                raise ValueError('dart_retained_file_invalid')
        try:
            proof, raw = json.loads(proof_path.read_bytes()), doc_path.read_bytes()
            original = check_origin(filing, proof, raw)
            if 'cutoff' in plan and datetime.fromisoformat(original['finished_at']) >= datetime.fromisoformat(plan['cutoff']):
                raise ValueError('dart_retained_capture_after_cutoff')
        except (IndexError, KeyError, TypeError) as exc:
            raise ValueError('dart_retained_origin_invalid') from exc
        return proof, raw

    def save(self, filing, raw, proof):
        from app.services.dart_report_artifact import extract_dart_xml
        check_origin(filing, proof, raw)
        extract_dart_xml(raw, filing['receipt_no'], corp_code=filing['corp_code'], report_code=filing['report_code'])
        directory = self._directory(filing)
        directory.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        with tempfile.TemporaryDirectory(dir=directory.parent) as tmp:
            pending = Path(tmp)/'new'
            durable_json(pending/'origin.json', proof, exclusive=True)
            durable_bytes(pending/'document.zip', raw, exclusive=True)
            try:
                pending.rename(directory)
            except OSError:
                if not directory.exists():
                    raise
                plan = dict(provider='opendart', issuer=filing['corp_code'], ticker=filing['ticker'])
                existing = self.find(plan, filing)
                if existing is None or existing[1] != raw:
                    raise ValueError('dart_retained_original_conflict')

    def put(self, plan, filing, raw, final):
        if (plan['issuer'] != filing['corp_code'] or plan['ticker'] != filing['ticker']
                or plan['run_id'] != final['generation_id'] or filing['role'] != 'current'
                or final['logical_request_id'] != f"financial:{filing['ticker']}:filing1:report"):
            raise ValueError('dart_retained_document_slot_mismatch')
        proof = document_proof(filing, raw, dict(kind='regular', **final), final['retrieval_time'])
        check_origin(filing, proof, raw)
        if self.source_root is None:
            raise ValueError('dart_regular_source_directory_required')
        directory = self.source_root / 'financial' / filing['ticker']
        durable_json(directory / ('dart-origin-'+filing['receipt_no']+'.json'), proof, exclusive=True)
