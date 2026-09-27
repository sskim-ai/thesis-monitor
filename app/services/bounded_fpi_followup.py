"""Exact-request FPI purpose inspection, reusing the accepted bounded reader.

No response-dependent request is authorized here. Unknown exhibit URLs remain
unavailable; their discovery never expands this one-shot manifest.
"""
from copy import deepcopy
import json
from urllib.parse import urlsplit

from app.services.bounded_financial_acquisition import BoundedReader, SystemicStop, sec_base
from app.services.sec_fpi_financial_purpose import candidate_inventory, SEC_FPI_MAX_PURPOSE_CANDIDATES
from app.services.unified_run_artifacts import sha256_bytes
from app.services.unified_snapshot_contract import digest

CONTRACT = 'bounded-fpi-purpose-followup-v1'


def make_followup_plan(parent, discovery_raw, captured_documents):
    if parent['provider'] != 'sec_edgar' or '6-K' not in parent['forms']:
        raise ValueError('fpi_class_required')
    inventory = candidate_inventory(json.loads(discovery_raw), parent)
    captured = {d['url'] for d in captured_documents}
    candidates = [{**f, 'role': 'current'} for f in inventory['inspection_window']]
    requests = []
    for filing in candidates:
        base = sec_base(parent, filing)
        primary = base + filing['primaryDocument']
        if primary in captured:
            continue
        requests.extend([{'stage': stage, 'url': url, 'filing': filing, 'params': {}}
                         for stage, url in (('index', base + 'index.json'), ('document', primary))])
    value = deepcopy(parent)
    value.update(contract=CONTRACT, parent_plan_sha256=digest(parent),
        discovery_sha256=sha256_bytes(discovery_raw), captured_document_metadata_sha256=digest(captured_documents),
        run_id=parent['run_id'] + ':fpi-purpose', candidates=candidates,
        inspection_inventory=inventory, exact_requests=requests,
        selection='frozen_metadata_order_then_source_owned_purpose_and_economic_period',
        limits={**parent['limits'], 'discovery': 0, 'companyfacts': 0,
                'current': SEC_FPI_MAX_PURPOSE_CANDIDATES, 'prior': 0,
                'documents_per_filing': 1, 'linked_exhibits': 0, 'indexes_per_filing': 1},
        named_caps={'SEC_FPI_MAX_PURPOSE_CANDIDATES': SEC_FPI_MAX_PURPOSE_CANDIDATES,
                    'inherited_document_cap': parent['limits']['documents_per_filing'],
                    'inherited_index_cap': parent['limits']['indexes_per_filing']},
        planned_logical_requests=len(requests), maximum_logical_requests=len(requests),
        maximum_HTTP_attempts=len(requests) * 3, planned_retry_attempts=0,
        pagination_count=0, document_count=sum(r['stage'] == 'document' for r in requests),
        index_count=sum(r['stage'] == 'index' for r in requests),
        unplanned_exhibit_requests='FORBIDDEN_NOT_FROZEN', new_discovery_requests=0)
    return value


def request_manifest(plan):
    return [{**r, 'method': 'GET', 'plan_sha256': digest(plan),
        'logical_id': plan['ticker'] + f':request-{i:03d}'} for i, r in enumerate(plan['exact_requests'], 1)]


class FrozenFpiReader(BoundedReader):
    async def read(self, stage, url, params=None, *, filing=None):
        request = {'stage': stage, 'url': url, 'params': dict(params or {}), 'filing': filing}
        if self.logical >= len(self.plan['exact_requests']) or request != self.plan['exact_requests'][self.logical]:
            raise SystemicStop('fpi_request_not_in_frozen_manifest')
        return await super().read(stage, url, params, filing=filing)


def verify_followup(parent, discovery_raw, captured_documents, directory):
    plan = json.loads((directory / 'plan.json').read_bytes())
    if plan != make_followup_plan(parent, discovery_raw, captured_documents):
        raise ValueError('fpi_plan_source_binding_mismatch')
    return verify_frozen_followup(plan, captured_documents, directory)


def verify_frozen_followup(plan, captured_documents, directory):
    if json.loads((directory / 'plan.json').read_bytes()) != plan:
        raise ValueError('fpi_expected_plan_mismatch')
    manifest = request_manifest(plan)
    frozen_manifest = json.loads((directory / 'request-manifest.json').read_bytes())
    if frozen_manifest != [{'request': r, 'request_sha256': digest(r)} for r in manifest]:
        raise ValueError('fpi_exact_manifest_mismatch')
    receipts = json.loads((directory / 'receipts.json').read_bytes())
    if len(receipts) > plan['maximum_HTTP_attempts']:
        raise ValueError('fpi_attempt_budget_exceeded')
    by_id, documents, succeeded = {}, [], []
    for ordinal, receipt in enumerate(receipts, 1):
        logical = receipt['logical_id']
        if logical in by_id and logical != next(reversed(by_id)):
            raise ValueError('fpi_interleaved_retry_denied')
        if logical not in by_id:
            index = len(by_id)
            if index >= len(manifest) or logical != manifest[index]['logical_id']:
                raise ValueError('fpi_request_order_mismatch')
            by_id[logical] = []
        index = list(by_id).index(logical)
        request = manifest[index]
        attempts = by_id[logical]
        if (receipt['plan_sha256'] != digest(plan) or receipt['request_sha256'] != digest(request)
                or receipt['attempt'] != len(attempts) + 1 or receipt['attempt'] > 3
                or receipt['attempt_ordinal'] != ordinal or receipt.get('filing') != request['filing']
                or receipt['stage'] != request['stage'] or receipt['timeout_seconds'] != 600
                or (attempts and (attempts[-1]['failure_class'] not in {'TRANSIENT_PROVIDER', 'TRANSIENT_TRANSPORT'}))):
            raise ValueError('fpi_receipt_binding_mismatch')
        frozen = json.loads((directory / (logical.split(':')[-1] + '.plan.json')).read_bytes())
        if frozen != request:
            raise ValueError('fpi_dispatched_request_mismatch')
        attempts.append(receipt)
        artifact = receipt.get('artifact')
        if artifact:
            expected = logical.split(':')[-1] + f"-attempt-{receipt['attempt']}.body"
            if artifact != expected:
                raise ValueError('fpi_artifact_identity_mismatch')
            raw = (directory / artifact).read_bytes()
            if sha256_bytes(raw) != receipt['raw_sha256']:
                raise ValueError('fpi_raw_receipt_mismatch')
        if receipt['failure_class']:
            continue
        if not artifact or receipt['HTTP_status'] != 200:
            raise ValueError('fpi_success_without_official_body')
        succeeded.append(logical)
        if request['stage'] == 'document':
            documents.append({'url': request['url'], 'filing': request['filing'],
                'raw': raw, 'artifact': artifact, 'receipt_sha256': digest(receipt)})
        else:
            expected_dir = urlsplit(sec_base(plan, request['filing'])).path.rstrip('/')
            if json.loads(raw).get('directory', {}).get('name') != expected_dir:
                raise ValueError('fpi_index_identity_mismatch')
    return {'plan': plan, 'documents': documents, 'receipt_sha256': digest(receipts),
        'logical_requests': len(by_id), 'attempts': len(receipts),
        'complete_exact_manifest': len(succeeded) == len(manifest),
        'uncaptured': [f for f in plan['candidates'] if sec_base(plan, f) + f['primaryDocument'] not in
                       {d['url'] for d in [*captured_documents, *documents]}]}
