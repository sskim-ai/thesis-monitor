"""Second, independently frozen SEC exhibit phase; never discovers new URLs."""
from copy import deepcopy
import io
import json
from pathlib import PurePosixPath
import zipfile

from app.services.bounded_financial_acquisition import (
    AcquisitionDenied, SystemicStop, sec_base, sec_document_identity, exhibit_selection,
)
from app.services.bounded_fpi_followup import FrozenFpiReader, request_manifest
from app.services.unified_run_artifacts import sha256_bytes
from app.services.unified_snapshot_contract import digest

CONTRACT = 'FPI_DISCOVERED_EXHIBIT_PHASE2'
# Fixed resource budget: three independently discovered text exhibits per issuer.
# It never increases in response to financial coverage or semantic outcomes.
SEC_FPI_MAX_PHASE2_EXHIBIT_DOCS_PER_SUBJECT = 3
SUPPORTED_SUFFIXES = frozenset({'.htm', '.html', '.xml', '.txt'})
SUPPORTED_MIMES = frozenset({'text/html', 'application/xhtml+xml', 'application/xml', 'text/xml', 'text/plain'})


def sealed_source(path, expected_sha256):
    raw = path.read_bytes()
    if sha256_bytes(raw) != expected_sha256:
        raise ValueError('phase1_zip_identity_mismatch')
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        manifest = json.loads(archive.read('bundle-manifest.json'))
        if len(archive.namelist()) != len(set(archive.namelist())) or set(archive.namelist()) != set(manifest) | {'bundle-manifest.json'}:
            raise ValueError('phase1_manifest_members_mismatch')
        files = {}
        for name, meta in manifest.items():
            value = archive.read(name)
            if len(value) != meta['bytes'] or sha256_bytes(value) != meta['sha256']:
                raise ValueError('phase1_manifest_hash_mismatch')
            files[name] = value
    return {'zip_sha256': expected_sha256, 'files': files, 'manifest': manifest}


def source_json(source, name):
    return json.loads(source['files'][name])


def eligible_discovered(parent, rows):
    requests, excluded, seen = [], [], set()
    for row in sorted(rows, key=lambda r: (r['filing']['filingDate'], r['filing']['accessionNumber']), reverse=True):
        if row['ticker'] != parent['ticker']:
            raise ValueError('phase2_subject_mismatch')
        filing = row['filing']
        if filing['form'] not in parent['forms'] or not parent['begin'] <= filing['filingDate'] <= parent['cutoff'][:10]:
            raise ValueError('phase2_filing_outside_parent_scope')
        eligible = row['existing_selector_eligible_urls']
        if row['existing_selector_denial'] and eligible:
            raise ValueError('phase2_denied_selector_cannot_authorize')
        if not set(eligible).issubset(row['newly_known_exhibit_urls']):
            raise ValueError('phase2_url_not_in_sealed_discovery')
        for url in sorted(eligible):
            identity = sec_document_identity(url, parent, filing)
            if identity != url or identity == sec_base(parent, filing) + filing['primaryDocument']:
                raise ValueError('phase2_exact_exhibit_identity_required')
            if url in seen:
                continue
            seen.add(url)
            if PurePosixPath(url).suffix.lower() not in SUPPORTED_SUFFIXES:
                excluded.append({'url': url, 'reason': 'UNSUPPORTED_DOCUMENT_TYPE_NO_OCR'})
                continue
            requests.append({'stage': 'document', 'url': url, 'params': {}, 'filing': filing})
    cap = SEC_FPI_MAX_PHASE2_EXHIBIT_DOCS_PER_SUBJECT
    excluded.extend({'url': r['url'], 'reason': 'FPI_PHASE2_EXHIBIT_BOUND_EXHAUSTED'} for r in requests[cap:])
    return requests[:cap], excluded


def make_phase2_plan(parent, source):
    parents = source_json(source, 'source-parent/financial-acquisition-plan.json')['entries']
    if parent not in parents or parent['provider'] != 'sec_edgar' or '6-K' not in parent['forms']:
        raise ValueError('phase2_parent_plan_binding_mismatch')
    all_rows = source_json(source, 'unrequested-exhibit-diagnostics.json')
    rows = [r for r in all_rows if r['ticker'] == parent['ticker']]
    prefix = 'followup-phase/followup/' + parent['ticker'] + '/'
    phase1_plan = source_json(source, prefix + 'plan.json')
    receipts = source_json(source, prefix + 'receipts.json')
    if phase1_plan['parent_plan_sha256'] != digest(parent):
        raise ValueError('phase2_phase1_parent_mismatch')
    # Re-derive the sealed selector result from exact captured index/primary bytes.
    for row in rows:
        filing = row['filing']
        if filing not in phase1_plan['candidates']:
            raise ValueError('phase2_filing_not_in_phase1_window')
        payloads = {}
        for stage in ('index', 'document'):
            matches = [r for r in receipts if r['stage'] == stage and r['filing'] == filing and not r['failure_class']]
            if len(matches) != 1:
                raise ValueError('phase2_unique_phase1_receipt_required')
            receipt = matches[0]
            request = source_json(source, prefix + receipt['logical_id'].split(':')[-1] + '.plan.json')
            expected_url = sec_base(parent, filing) + ('index.json' if stage == 'index' else filing['primaryDocument'])
            if (request['url'] != expected_url or request['filing'] != filing
                    or receipt['request_sha256'] != digest(request) or receipt['plan_sha256'] != digest(phase1_plan)):
                raise ValueError('phase2_phase1_request_binding_mismatch')
            payloads[stage] = source['files'][prefix + receipt['artifact']]
            if sha256_bytes(payloads[stage]) != receipt['raw_sha256']:
                raise ValueError('phase2_phase1_raw_binding_mismatch')
        if (sha256_bytes(payloads['index']) != row['index_sha256']
                or sha256_bytes(payloads['document']) != row['primary_sha256']
                or row['primary_source_url'] != sec_base(parent, filing) + filing['primaryDocument']):
            raise ValueError('phase2_discovery_receipt_mismatch')
        try:
            selected = exhibit_selection(json.loads(payloads['index']), payloads['document'].decode(errors='replace'), parent, filing)
            denial = None
        except AcquisitionDenied as exc:
            selected, denial = [], str(exc)
        if selected != row['existing_selector_eligible_urls'] or denial != row['existing_selector_denial']:
            raise ValueError('phase2_selector_replay_mismatch')
    requests, excluded = eligible_discovered(parent, rows)
    candidates = list({r['filing']['accessionNumber']: r['filing'] for r in requests}.values())
    cap = SEC_FPI_MAX_PHASE2_EXHIBIT_DOCS_PER_SUBJECT
    plan = deepcopy(parent)
    plan.update(contract=CONTRACT, run_id=parent['run_id'] + ':fpi-phase2',
        phase1_zip_sha256=source['zip_sha256'], parent_plan_sha256=digest(parent),
        phase1_plan_sha256=digest(phase1_plan), phase1_receipts_sha256=digest(receipts),
        sealed_discovery_sha256=sha256_bytes(source['files']['unrequested-exhibit-diagnostics.json']),
        discovery_rows_sha256=digest(rows), exact_requests=requests, excluded=excluded, candidates=candidates,
        purpose='FINANCIAL_PURPOSE_INSPECTION', recursive_discovery=False,
        stop_condition='SYSTEMIC_IDENTITY_CONFIG_MANIFEST_OR_BUDGET_FAILURE_ONLY',
        execution_policy='SEQUENTIAL_FROZEN_ENTRIES_NO_SEMANTIC_RETRY',
        named_caps={'SEC_FPI_MAX_PHASE2_EXHIBIT_DOCS_PER_SUBJECT': cap},
        limits={**parent['limits'], 'discovery': 0, 'companyfacts': 0, 'current': cap, 'prior': 0,
                'indexes_per_filing': 0, 'documents_per_filing': cap, 'linked_exhibits': 0},
        planned_logical_requests=len(requests), maximum_logical_requests=len(requests),
        maximum_HTTP_attempts=len(requests) * 3, planned_retry_attempts=0)
    return plan


class Phase2Reader(FrozenFpiReader):
    authorization_denial_is_systemic = False

    def response_metadata(self, response):
        return {'response_content_type': response.headers.get('content-type', '').split(';', 1)[0].strip().lower()}

    async def read(self, stage, url, params=None, *, filing=None):
        if (self.plan['contract'] != CONTRACT or stage != 'document'
                or PurePosixPath(url).suffix.lower() not in SUPPORTED_SUFFIXES):
            raise SystemicStop('phase2_non_exhibit_request_forbidden')
        return await super().read(stage, url, params, filing=filing)


def verify_phase2(parent, source, directory):
    plan = json.loads((directory / 'plan.json').read_bytes())
    if plan != make_phase2_plan(parent, source):
        raise ValueError('phase2_plan_source_binding_mismatch')
    return verify_phase2_capture(plan, directory)


def verify_phase2_capture(plan, directory):
    if json.loads((directory / 'plan.json').read_bytes()) != plan:
        raise ValueError('phase2_expected_plan_mismatch')
    manifest = request_manifest(plan)
    if json.loads((directory / 'request-manifest.json').read_bytes()) != [
            {'request': r, 'request_sha256': digest(r)} for r in manifest]:
        raise ValueError('phase2_request_manifest_mismatch')
    receipts = json.loads((directory / 'receipts.json').read_bytes())
    by_id, documents, denials = {}, [], []
    if len(receipts) > plan['maximum_HTTP_attempts']:
        raise ValueError('phase2_attempt_budget_exceeded')
    for ordinal, receipt in enumerate(receipts, 1):
        logical = receipt['logical_id']
        if logical in by_id and logical != next(reversed(by_id)):
            raise ValueError('phase2_interleaved_retry_denied')
        if logical not in by_id:
            index = len(by_id)
            if index >= len(manifest) or logical != manifest[index]['logical_id']:
                raise ValueError('phase2_request_order_mismatch')
            by_id[logical] = []
        request = manifest[list(by_id).index(logical)]
        attempts = by_id[logical]
        frozen = json.loads((directory / (logical.split(':')[-1] + '.plan.json')).read_bytes())
        if (frozen != request or receipt['request_sha256'] != digest(request)
                or receipt['plan_sha256'] != digest(plan) or receipt['filing'] != request['filing']
                or receipt['stage'] != 'document' or receipt['attempt'] != len(attempts) + 1
                or receipt['attempt'] > 3 or receipt['attempt_ordinal'] != ordinal
                or receipt['timeout_seconds'] != 600
                or (attempts and attempts[-1]['failure_class'] not in {'TRANSIENT_PROVIDER', 'TRANSIENT_TRANSPORT'})):
            raise ValueError('phase2_receipt_binding_mismatch')
        attempts.append(receipt)
        artifact = receipt.get('artifact')
        raw = None
        if artifact:
            if artifact != logical.split(':')[-1] + f"-attempt-{receipt['attempt']}.body":
                raise ValueError('phase2_artifact_identity_mismatch')
            raw = (directory / artifact).read_bytes()
            if sha256_bytes(raw) != receipt['raw_sha256']:
                raise ValueError('phase2_raw_receipt_mismatch')
        if receipt['failure_class']:
            denials.append({'url': request['url'], 'reason': receipt['failure_class']})
            continue
        if raw is None or receipt['HTTP_status'] != 200:
            raise ValueError('phase2_success_without_body')
        if receipt.get('response_content_type') not in SUPPORTED_MIMES:
            denials.append({'url': request['url'], 'reason': 'UNSUPPORTED_RESPONSE_MIME'})
            continue
        documents.append({'url': request['url'], 'filing': request['filing'], 'raw': raw,
            'artifact': artifact, 'receipt_sha256': digest(receipt)})
    return {'plan': plan, 'documents': documents, 'denials': denials,
        'receipt_sha256': digest(receipts), 'logical_requests': len(by_id), 'attempts': len(receipts),
        'unattempted': [r['url'] for r in manifest[len(by_id):]],
        'phase2_result_sha256': digest({'plan': digest(plan), 'receipts': receipts})}
