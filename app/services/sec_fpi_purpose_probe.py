"""NG40 primary/index purpose probe; never a financial source-use grant.

The original capture is replayed as historical evidence, not reauthorized.
The parent owns live dispatch permission, credentials and the task-wide budget.
No settings, database, scheduler or financial-owner mutation occurs here.
"""
from copy import deepcopy
from datetime import datetime
from html.parser import HTMLParser
import json
from pathlib import Path
import re
from urllib.parse import urljoin, urlsplit

from app.services.bounded_financial_acquisition import (
    AcquisitionDenied, BoundedReader, SystemicStop, sec_base,
)
from app.services.bounded_fpi_followup import request_manifest
from app.services.sec_current_financial_candidates import NOMINATED_CONTRACT
from app.services.sec_fpi_financial_purpose import (
    FINANCIAL, candidate_inventory, classify_document,
)
from app.services.unified_run_artifacts import durable_json, sha256_bytes
from app.services.unified_snapshot_contract import digest

CONTRACT = 'sec-fpi-purpose-probe-v1'
PURPOSE = 'PURPOSE_CLASSIFICATION_ONLY'
MAX_HTTP_ATTEMPTS = 18
MAX_PURPOSE_FILINGS = 9
NONFINANCIAL = frozenset({
    'RUMOR_OR_DISCLOSURE_RESPONSE', 'DIVIDEND_OR_CAPITAL_RETURN',
    'GOVERNANCE_OR_COMPENSATION', 'CORPORATE_EVENT_NONFINANCIAL',
})
TRANSIENT = frozenset({'TRANSIENT_PROVIDER', 'TRANSIENT_TRANSPORT'})


def _read(directory, name):
    path = Path(directory) / name
    if Path(name).name != name or name in {'', '.', '..'} or path.is_symlink():
        raise ValueError('purpose_probe_artifact_path_denied')
    return path.read_bytes()


def _time(value):
    value = value.isoformat() if isinstance(value, datetime) else value
    parsed = datetime.fromisoformat(value)
    if parsed.utcoffset() is None:
        raise ValueError('purpose_probe_aware_time_required')
    return parsed


def _original_source(plan, acquisition, directory, receipts, source_anchor, target_manifest):
    from app.services.bounded_financial_projection import verify_capture

    if (set(source_anchor) != {'discovery_sha256', 'discovery_receipt_file_sha256'}
            or any(not isinstance(v, str) or not re.fullmatch(r'[a-f0-9]{64}', v) for v in source_anchor.values())):
        raise ValueError('purpose_probe_presealed_source_anchor_required')
    if plan.get('fpi_candidate_contract') != NOMINATED_CONTRACT:
        raise ValueError('purpose_probe_original_nominated_plan_required')
    for row in receipts:
        name = row['logical_id'].split(':')[-1]
        if not re.fullmatch(r'request-\d{3}', name):
            raise ValueError('purpose_probe_original_request_path_denied')
        if row.get('artifact'):
            _read(directory, row['artifact'])
        frozen = json.loads(_read(directory, f'{name}-attempt-{row["attempt"]}.receipt.json'))
        if frozen != row:
            raise ValueError('purpose_probe_original_receipt_mismatch')
    verify_capture(plan, acquisition, Path(directory), receipts)
    discoveries = [r for r in receipts if r['stage'] == 'discovery' and not r['failure_class']]
    if len(discoveries) != 1:
        raise ValueError('purpose_probe_unique_original_discovery_required')
    receipt = discoveries[0]
    name = receipt['logical_id'].split(':')[-1]
    receipt_bytes = _read(directory, f'{name}-attempt-{receipt["attempt"]}.receipt.json')
    raw = _read(directory, receipt['artifact'])
    if (sha256_bytes(raw) != source_anchor['discovery_sha256']
            or sha256_bytes(receipt_bytes) != source_anchor['discovery_receipt_file_sha256']
            or receipt['HTTP_status'] != 200 or receipt.get('error_type')
            or receipt['raw_sha256'] != sha256_bytes(raw)):
        raise ValueError('purpose_probe_original_source_anchor_mismatch')
    request = json.loads(_read(directory, name + '.plan.json'))
    if (request['url'] != f'https://data.sec.gov/submissions/CIK{plan["issuer"]}.json'
            or request['method'] != 'GET' or request['params'] or request['filing'] is not None):
        raise ValueError('purpose_probe_original_discovery_route_mismatch')
    inventory = candidate_inventory(json.loads(raw), plan)
    financial = inventory['current_financial_plan']
    if financial['interim_candidate_cap'] != 2 or financial['candidate_cap'] != 3:
        raise ValueError('purpose_probe_economic_bound_changed')
    fields = {'form', 'accessionNumber', 'primaryDocument', 'filingDate', 'reportDate'}
    if (not isinstance(target_manifest, list) or not 1 <= len(target_manifest) <= MAX_PURPOSE_FILINGS
            or any(not isinstance(r, dict) or set(r) != fields for r in target_manifest)
            or len({r['accessionNumber'] for r in target_manifest}) != len(target_manifest)):
        raise ValueError('purpose_probe_bounded_exact_manifest_required')
    for target in target_manifest:
        matches = [r for r in inventory['candidates'] if r['accessionNumber'] == target['accessionNumber']]
        if len(matches) != 1 or matches[0] != target or target['form'] not in {'6-K', '6-K/A'}:
            raise ValueError('purpose_probe_exact_discovery_membership_required')
        if any(d.get('url') == sec_base(plan, target) + target['primaryDocument'] for d in acquisition['documents']):
            raise ValueError('purpose_probe_target_already_captured_reuse_original')
    filings = [{**r, 'role': 'purpose_only'} for r in target_manifest]
    binding = {**source_anchor, 'target_manifest_sha256': digest(target_manifest), 'original_plan_sha256': digest(plan),
        'original_acquisition_sha256': digest(acquisition), 'original_receipts_sha256': digest(receipts),
        'original_discovery_receipt_sha256': digest(receipt),
        'original_generation': plan['run_id'], 'original_cutoff': plan['cutoff'],
        'original_started_at': receipt['started_at'], 'original_finished_at': receipt['finished_at'],
        'original_request_sha256': receipt['request_sha256']}
    return binding, financial, filings


def make_probe_plan(original_plan, original_acquisition, original_directory,
                    original_receipts, new_execution_generation, cutoff, budget=18, *,
                    source_anchor, target_manifest):
    """Freeze <=9 exact primary/index pairs. budget is REMAINING task attempts.

    All original arguments are retained capture inputs, not a rewritten current
    plan. Replaying them does not revive their expired dispatch authorization.
    source_anchor and target_manifest must come from the parent's independently
    presealed task evidence, never from an untrusted probe result being replayed.
    """
    binding, financial, filings = _original_source(
        original_plan, original_acquisition, original_directory, original_receipts, source_anchor, target_manifest)
    if (not isinstance(new_execution_generation, str) or not new_execution_generation.strip()
            or new_execution_generation == original_plan['run_id']):
        raise ValueError('purpose_probe_distinct_execution_generation_required')
    stamp = _time(cutoff)
    if stamp < _time(binding['original_finished_at']):
        raise ValueError('purpose_probe_cutoff_precedes_original_capture')
    if type(budget) is not int or not 0 <= budget <= MAX_HTTP_ATTEMPTS:
        raise ValueError('purpose_probe_task_attempt_budget_invalid')
    requests = [{'stage': stage, 'url': sec_base(original_plan, filing) + (
        filing['primaryDocument'] if stage == 'document' else 'index.json'),
        'params': {}, 'filing': filing}
        for stage in ('document', 'index') for filing in filings]
    return {'contract': CONTRACT, 'purpose': PURPOSE, 'provider': 'sec_edgar',
        'run_id': new_execution_generation, 'cutoff': stamp.isoformat(),
        'ticker': original_plan['ticker'], 'issuer': original_plan['issuer'],
        'forms': sorted({r['form'] for r in filings}), 'source_binding': binding, 'filings': filings,
        'economic_candidate_plan': deepcopy(financial), 'economic_interim_candidate_cap': 2,
        'financial_authority': False, 'source_use_eligible': False,
        'exact_requests': requests, 'maximum_logical_requests': len(requests),
        'maximum_HTTP_attempts': budget, 'task_HTTP_attempt_ceiling': MAX_HTTP_ATTEMPTS,
        'task_attempts_reserved_elsewhere': MAX_HTTP_ATTEMPTS - budget,
        'maximum_attempts_per_request': 3, 'timeout_seconds': 600, 'redirects': False,
        'stop_without_retry_HTTP_statuses': [401, 403, 429],
        'attachment_fetch': 'ATTACHMENT_REQUIRED_REMAINING_BUDGET_GAP',
        # These are purpose-only request slots, not changed economic candidates.
        'limits': {'discovery': 0, 'companyfacts': 0, 'current': len(filings), 'prior': 0,
            'candidates': len(filings), 'documents_per_filing': 1, 'linked_exhibits': 0, 'indexes_per_filing': 1}}


def _verify_plan(plan, original_plan, original_acquisition, original_directory, original_receipts, *,
                 source_anchor, target_manifest):
    expected = make_probe_plan(original_plan, original_acquisition, original_directory,
        original_receipts, plan['run_id'], plan['cutoff'], plan['maximum_HTTP_attempts'],
        source_anchor=source_anchor, target_manifest=target_manifest)
    if plan != expected:
        raise ValueError('purpose_probe_plan_replay_mismatch')


class PurposeProbeReader(BoundedReader):
    """Original HTTP/receipt implementation, with a stricter task budget/stop."""
    def __init__(self, plan, output, *, original_plan, original_acquisition,
                 original_directory, original_receipts, source_anchor, target_manifest,
                 user_agent, transport, guard=None):
        self.source_anchor, self.target_manifest = deepcopy(source_anchor), deepcopy(target_manifest)
        _verify_plan(plan, original_plan, original_acquisition, original_directory, original_receipts,
            source_anchor=self.source_anchor, target_manifest=self.target_manifest)
        if not isinstance(user_agent, str) or not user_agent.strip() or transport is None:
            raise ValueError('purpose_probe_explicit_transport_and_original_user_agent_required')
        self.original = (deepcopy(original_plan), deepcopy(original_acquisition),
                         Path(original_directory), deepcopy(original_receipts))
        self.external_guard, self.stopped, self.capture_started = guard, None, False
        super().__init__(plan, Path(output), user_agent=user_agent, transport=transport, guard=self._attempt_guard)

    def _attempt_guard(self):
        if self.stopped:
            raise SystemicStop(self.stopped)
        if self.attempts >= self.plan['maximum_HTTP_attempts']:
            self.stopped = 'purpose_probe_total_attempt_budget_exhausted'
            raise SystemicStop(self.stopped)
        if self.external_guard:
            self.external_guard()

    def response_metadata(self, response):
        if self.user_agent.encode() in response.content:
            raise SystemicStop('provider_response_secret_echo')
        if response.status_code == 429:
            raise SystemicStop('purpose_probe_rate_limited')
        content_type = response.headers.get('content-type', '').split(';')[0].strip().lower()
        if content_type not in {'text/html', 'application/xhtml+xml', 'text/plain', 'application/json'}:
            content_type = 'unavailable_or_unsupported'
        return {'purpose': PURPOSE, 'content_type': content_type}

    async def read(self, stage, url, params=None, *, filing=None):
        if self.stopped or self.attempts >= self.plan['maximum_HTTP_attempts']:
            self._attempt_guard()
        request = {'stage': stage, 'url': url, 'params': dict(params or {}), 'filing': filing}
        if (self.logical >= len(self.plan['exact_requests'])
                or request != self.plan['exact_requests'][self.logical]):
            raise SystemicStop('purpose_probe_request_outside_exact_manifest')
        try:
            return await super().read(stage, url, params, filing=filing)
        except SystemicStop as exc:
            self.stopped = str(exc)
            raise


async def collect_probe(reader):
    """Parent-invoked only. Preserve failed attempts and stop, never empty success."""
    if type(reader) is not PurposeProbeReader or reader.capture_started:
        raise ValueError('purpose_probe_single_capture_required')
    _verify_plan(reader.plan, *reader.original,
        source_anchor=reader.source_anchor, target_manifest=reader.target_manifest)
    reader.capture_started = True
    durable_json(reader.output / 'plan.json', reader.plan, exclusive=True)
    manifest = request_manifest(reader.plan)
    durable_json(reader.output / 'request-manifest.json',
        [{'request': r, 'request_sha256': digest(r)} for r in manifest], exclusive=True)
    reader.select(reader.plan['filings'])
    terminal = {'status': 'CAPTURED', 'reason': None}
    try:
        for request in reader.plan['exact_requests']:
            try:
                await reader.read(request['stage'], request['url'], request['params'], filing=request['filing'])
            except SystemicStop as exc:
                terminal = {'status': 'STOPPED', 'reason': str(exc)}
                break
            except AcquisitionDenied:
                terminal = {'status': 'PARTIAL', 'reason': 'purpose_probe_request_failed'}
    except Exception as exc:
        terminal = {'status': 'INTERRUPTED', 'reason': type(exc).__name__}
        raise
    finally:
        durable_json(reader.output / 'receipts.json', reader.receipts, exclusive=True)
        durable_json(reader.output / 'terminal.json', terminal, exclusive=True)
    return replay_probe(reader.plan, *reader.original, reader.output,
        source_anchor=reader.source_anchor, target_manifest=reader.target_manifest)


def _verified_receipts(plan, directory):
    manifest = request_manifest(plan)
    if json.loads(_read(directory, 'request-manifest.json')) != [
            {'request': r, 'request_sha256': digest(r)} for r in manifest]:
        raise ValueError('purpose_probe_manifest_mismatch')
    receipts = json.loads(_read(directory, 'receipts.json'))
    if len(receipts) > plan['maximum_HTTP_attempts']:
        raise ValueError('purpose_probe_attempt_budget_exceeded')
    groups, bodies, paths, stopped = {}, {}, set(), False
    for ordinal, receipt in enumerate(receipts, 1):
        logical = receipt['logical_id']
        if stopped or logical in groups and logical != next(reversed(groups)):
            raise ValueError('purpose_probe_receipt_after_stop_or_interleaved_retry')
        if logical not in groups:
            if len(groups) >= len(manifest) or logical != manifest[len(groups)]['logical_id']:
                raise ValueError('purpose_probe_request_order_mismatch')
            if groups:
                previous = next(reversed(groups.values()))[-1]
                if previous['failure_class'] in TRANSIENT and previous['attempt'] < 3:
                    raise ValueError('purpose_probe_incomplete_retry_sequence')
            groups[logical] = []
        request = manifest[list(groups).index(logical)]
        attempts = groups[logical]
        attempt = len(attempts) + 1
        if (receipt['plan_sha256'] != digest(plan) or receipt['request_sha256'] != digest(request)
                or receipt['attempt_ordinal'] != ordinal or receipt['attempt'] != attempt or attempt > 3
                or receipt['stage'] != request['stage'] or receipt['filing'] != request['filing']
                or receipt['timeout_seconds'] != 600 or receipt.get('provider_status') is not None
                or receipt['retry'] != (attempt > 1)
                or receipt['retry_reason'] != (attempts[-1]['failure_class'] if attempts else None)
                or attempts and attempts[-1]['failure_class'] not in TRANSIENT):
            raise ValueError('purpose_probe_receipt_binding_mismatch')
        if _time(receipt['finished_at']) < _time(receipt['started_at']) or _time(receipt['started_at']) < _time(plan['cutoff']):
            raise ValueError('purpose_probe_receipt_time_mismatch')
        name = logical.split(':')[-1]
        receipt_name = f'{name}-attempt-{attempt}.receipt.json'
        paths.add(receipt_name)
        if (json.loads(_read(directory, name + '.plan.json')) != request
                or json.loads(_read(directory, receipt_name)) != receipt):
            raise ValueError('purpose_probe_persisted_receipt_mismatch')
        raw = None
        if receipt.get('artifact'):
            if receipt['artifact'] != f'{name}-attempt-{attempt}.body':
                raise ValueError('purpose_probe_body_identity_mismatch')
            raw = _read(directory, receipt['artifact'])
            if sha256_bytes(raw) != receipt['raw_sha256']:
                raise ValueError('purpose_probe_body_hash_mismatch')
        elif receipt.get('raw_sha256') is not None:
            raise ValueError('purpose_probe_missing_body')
        status, failure = receipt['HTTP_status'], receipt['failure_class']
        if status in {401, 403, 429}:
            expected = 'purpose_probe_rate_limited' if status == 429 else 'provider_authorization_denied'
            if failure != 'SYSTEMIC_STOP' or receipt.get('systemic_reason') not in {expected, 'provider_response_secret_echo'}:
                raise ValueError('purpose_probe_denial_not_terminal')
        elif failure is None:
            if status != 200 or raw is None or receipt.get('error_type') or receipt.get('purpose') != PURPOSE:
                raise ValueError('purpose_probe_false_success')
            bodies[(request['filing']['accessionNumber'], request['stage'])] = (raw, receipt)
        elif status is not None and failure != 'SYSTEMIC_STOP':
            expected = 'TRANSIENT_PROVIDER' if status in {408, 500, 502, 503, 504} else 'PROVIDER_DENIAL'
            if status == 200 or failure != expected:
                raise ValueError('purpose_probe_http_failure_mismatch')
        elif status is None and failure == 'SYSTEMIC_STOP':
            if (receipt.get('error_type') is not None or raw is not None
                    or receipt.get('systemic_reason') not in {
                        'NG40_RESPONSE_SIZE_CAP', 'NG40_RESOURCE_GUARD',
                        'NG40_PURPOSE_HTTP_SCOPE_OR_BUDGET_STOP'}):
                raise ValueError('purpose_probe_unrecognized_transport_stop')
        elif status is None and (not receipt.get('error_type') or failure not in {
                'TRANSIENT_TRANSPORT', 'NONRETRYABLE_TRANSPORT_OR_SCHEMA'}):
            raise ValueError('purpose_probe_transport_failure_missing')
        stopped = failure == 'SYSTEMIC_STOP'
        attempts.append(receipt)
    if {p.name for p in Path(directory).glob('request-*-attempt-*.receipt.json')} != paths:
        raise ValueError('purpose_probe_omitted_attempt_receipt')
    return receipts, bodies


class _Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        attribute = {'a': 'href', 'iframe': 'src', 'object': 'data', 'embed': 'src'}.get(tag)
        if attribute and dict(attrs).get(attribute):
            self.links.append(dict(attrs)[attribute])


def _attachment_gaps(index_raw, primary_raw, plan, filing):
    index = json.loads(index_raw).get('directory', {})
    base = sec_base(plan, filing)
    if index.get('name') != urlsplit(base).path.rstrip('/') or not isinstance(index.get('item'), list):
        return ['INDEX_IDENTITY_OR_SCHEMA_UNRESOLVED']
    names = [item.get('name') for item in index['item'] if isinstance(item, dict)]
    if len(names) != len(index['item']) or any(not isinstance(n, str) or Path(n).name != n for n in names):
        return ['INDEX_MEMBER_IDENTITY_UNRESOLVED']
    if filing['primaryDocument'] not in names:
        return ['PRIMARY_NOT_IN_OFFICIAL_INDEX']
    accession = filing['accessionNumber']
    duplicates = {filing['primaryDocument'], accession + '.txt', accession + '-index.html', accession + '-index.htm',
        accession + '-index-headers.html'}
    # Only media/styles and the exact SEC submission container are non-body assets.
    missing = [n for n in names if n not in duplicates and not re.search(r'\.(?:gif|jpg|jpeg|png|css|js|ico)$', n, re.I)]
    links = _Links()
    html = primary_raw.decode('utf-8', errors='replace')
    links.feed(html)
    primary = base + filing['primaryDocument']
    for href in links.links:
        target = urljoin(primary, href).split('#', 1)[0]
        if target != primary and (target.startswith(base) or re.search(r'(?i)\.(?:pdf|htm|html|txt|xml)(?:[?#]|$)', target)):
            missing.append(target)
    if re.search(r'(?i)attached (?:hereto|as)|furnished (?:herewith|as exhibit)|incorporated (?:herein )?by reference', html):
        missing.append('ATTACHMENT_OR_REFERENCE_REQUIRES_SEPARATE_VERIFICATION')
    return sorted(set(missing))


def _classify_filing(plan, filing, bodies):
    key = filing['accessionNumber']
    result = {'filing': filing, 'classification': 'UNKNOWN_UNRESOLVED',
        'financial_authority': False, 'source_use_eligible': False, 'economic_candidate': False,
        'reasons': [], 'economic_periods': [], 'purpose_evidence': [], 'source_receipts': {}}
    primary, index = bodies.get((key, 'document')), bodies.get((key, 'index'))
    for stage, captured in (('document', primary), ('index', index)):
        if captured:
            raw, receipt = captured
            result['source_receipts'][stage] = {'raw_sha256': sha256_bytes(raw),
                'receipt_sha256': digest(receipt), 'artifact': receipt['artifact'],
                'content_type': receipt.get('content_type'), 'HTTP_status': receipt['HTTP_status']}
    if not primary:
        result['reasons'] = ['PRIMARY_FAILED_OR_NOT_ATTEMPTED']
        return result
    raw, receipt = primary
    url = sec_base(plan, filing) + filing['primaryDocument']
    result['source_url'] = url
    if receipt.get('content_type') not in {'text/html', 'application/xhtml+xml', 'text/plain'}:
        result['reasons'] = ['PRIMARY_CONTENT_TYPE_UNRESOLVED']
        return result
    # The original classifier owns periods/occurrences. Its diagnostic field
    # eligibility is not exported as this probe's financial-use authority.
    classifier_plan = {**plan, 'financial_owner_policy': 'EXACT_FISCAL_ANNUAL_AND_CURRENT_FPI_V1'}
    classified = classify_document(raw, url=url, filing=filing, plan=classifier_plan)
    result.update(classifier_receipt_sha256=classified['receipt_sha256'],
        original_purpose=classified['purpose'], purpose_evidence=classified['purpose_evidence'],
        economic_periods=classified['economic_periods'], valid_occurrence_ids=classified['valid_occurrence_ids'])
    if not index:
        result['reasons'] = ['INDEX_FAILED_OR_NOT_ATTEMPTED']
        return result
    try:
        gaps = _attachment_gaps(index[0], raw, plan, filing)
    except (ValueError, TypeError, AttributeError):
        gaps = ['INDEX_SCHEMA_UNRESOLVED']
    if gaps:
        result.update(reasons=['ATTACHMENT_REQUIRED_REMAINING_BUDGET_GAP'], attachment_gaps=gaps)
    elif classified['purpose'] in FINANCIAL and classified['valid_occurrence_ids'] and classified['economic_periods']:
        result['classification'] = 'FINANCIAL_WITH_FIELD_PERIOD'
    elif (classified['purpose'] in NONFINANCIAL and classified['purpose_evidence']
            and not classified['occurrences'] and not classified.get('unresolved_financial_content')
            and not classified.get('source_precedence_conflicts')):
        result['classification'] = 'CONFIRMED_NON_FINANCIAL'
    else:
        result['reasons'] = ['ORIGINAL_PURPOSE_OR_FIELD_PERIOD_UNRESOLVED']
    return result


def replay_probe(plan, original_plan, original_acquisition, original_directory,
                 original_receipts, directory, *, source_anchor, target_manifest,
                 expected_capture_sha256=None):
    """Offline replay from raw bytes, never caller-supplied classification labels."""
    _verify_plan(plan, original_plan, original_acquisition, original_directory, original_receipts,
        source_anchor=source_anchor, target_manifest=target_manifest)
    if (json.loads(_read(directory, 'plan.json')) != plan
            or json.loads(_read(directory, 'selected-filings.json')) != plan['filings']):
        raise ValueError('purpose_probe_frozen_plan_mismatch')
    receipts, bodies = _verified_receipts(plan, directory)
    capture_sha = digest({'plan': plan, 'receipts': receipts})
    if expected_capture_sha256 is not None and capture_sha != expected_capture_sha256:
        raise ValueError('purpose_probe_capture_seal_mismatch')
    filings = [_classify_filing(plan, filing, bodies) for filing in plan['filings']]
    failures = [r for r in receipts if r['failure_class']]
    terminal = json.loads(_read(directory, 'terminal.json'))
    budget_exhausted = (len(receipts) == plan['maximum_HTTP_attempts']
        and len({r['logical_id'] for r in receipts}) < len(plan['exact_requests']))
    result = {'contract': CONTRACT, 'purpose': PURPOSE, 'execution_generation': plan['run_id'],
        'cutoff': plan['cutoff'], 'source_binding': plan['source_binding'],
        'plan_sha256': digest(plan), 'capture_sha256': capture_sha,
        'original_attempt_receipts_sha256': digest(receipts), 'HTTP_attempts': len(receipts),
        'task_HTTP_attempt_ceiling': MAX_HTTP_ATTEMPTS,
        'task_attempts_reserved_elsewhere': plan['task_attempts_reserved_elsewhere'],
        'failures': failures, 'filings': filings, 'capture_terminal': terminal,
        'attempt_budget_exhausted': budget_exhausted,
        'status': 'STOPPED' if budget_exhausted or terminal.get('status') in {'STOPPED', 'INTERRUPTED'}
            or any(r['failure_class'] == 'SYSTEMIC_STOP' for r in receipts)
            else 'PARTIAL' if any(f['classification'] == 'UNKNOWN_UNRESOLVED' for f in filings) else 'CLASSIFIED',
        'financial_authority': False, 'source_use_eligible': False, 'admitted_fact_count': 0,
        'native_ready': False, 'economic_interim_candidate_cap': 2,
        'economic_candidate_plan_sha256': digest(plan['economic_candidate_plan']),
        'outside_bound_preserved': deepcopy(plan['economic_candidate_plan']['outside_bound']),
        'consumer_gate': 'ORIGINAL_FIELD_COMPLETENESS_AND_SELECTED_OWNER_STILL_REQUIRED'}
    result['receipt_sha256'] = digest(result)
    return result
