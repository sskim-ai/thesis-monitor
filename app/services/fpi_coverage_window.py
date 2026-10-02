"""One final FPI window from the same sealed submissions; no rediscovery."""
from copy import deepcopy
import json

from app.services.bounded_financial_acquisition import AcquisitionDenied, sec_base, exhibit_selection
from app.services.bounded_fpi_followup import FrozenFpiReader, verify_frozen_followup
from app.services.sec_fpi_financial_purpose import candidate_inventory, classify_document, SEC_FPI_MAX_PURPOSE_CANDIDATES
from app.services.fpi_discovered_exhibit_phase2 import eligible_discovered, verify_phase2_capture, CONTRACT as EXHIBIT_CONTRACT
from app.services.unified_run_artifacts import sha256_bytes
from app.services.unified_snapshot_contract import digest

SEC_FPI_MAX_COVERAGE_WINDOWS = 2
CONTRACT = 'sec-fpi-second-final-coverage-window-v1'


def make_window_plan(parent, discovery_raw, captured_documents, first, exhibits, *, window_number=2):
    if window_number != SEC_FPI_MAX_COVERAGE_WINDOWS or parent['provider'] != 'sec_edgar' or '6-K' not in parent['forms']:
        raise ValueError('only_second_fpi_window_authorized')
    inventory = candidate_inventory(json.loads(discovery_raw), parent)
    expected = [{**f, 'role': 'current'} for f in inventory['inspection_window']]
    if (first is None or exhibits is None or first['plan']['candidates'] != expected
            or first['plan']['discovery_sha256'] != sha256_bytes(discovery_raw)
            or first['plan']['parent_plan_sha256'] != digest(parent)
            or first['plan']['captured_document_metadata_sha256'] != digest(captured_documents)
            or not first['complete_exact_manifest'] or first['uncaptured']
            or exhibits['plan']['phase1_plan_sha256'] != digest(first['plan'])
            or exhibits['plan']['phase1_receipts_sha256'] != first['receipt_sha256']
            or exhibits['plan']['exact_requests'] or exhibits['documents']):
        raise ValueError('first_window_exhaustion_and_empty_phase2_required')
    window_urls = {sec_base(parent, f) + f['primaryDocument'] for f in expected}
    docs = [*first['documents'], *first.get('captured_window_documents', [])]
    if window_urls != {d['url'] for d in docs}:
        raise ValueError('all_first_window_source_bytes_required')
    for d in docs:
        proof = classify_document(d['raw'], url=d['url'], filing=d['filing'], plan=parent)
        if proof['financial_authority']:
            raise ValueError('financial_source_already_found')
    size = SEC_FPI_MAX_PURPOSE_CANDIDATES
    candidates = [{**f, 'role': 'current'} for f in inventory['candidates'][size:size * 2]]
    if not candidates or {f['accessionNumber'] for f in candidates} & {f['accessionNumber'] for f in expected}:
        raise ValueError('nonoverlapping_additional_sealed_candidates_required')
    requests = [{'stage': stage, 'url': sec_base(parent, f) + filename, 'params': {}, 'filing': f}
        for f in candidates for stage, filename in (('index', 'index.json'), ('document', f['primaryDocument']))]
    result = deepcopy(first['plan'])
    result.update(contract=CONTRACT, run_id=parent['run_id'] + ':fpi-window2', window_number=2,
        maximum_windows=SEC_FPI_MAX_COVERAGE_WINDOWS, candidates=candidates, exact_requests=requests,
        first_window_plan_sha256=digest(first['plan']), first_window_receipts_sha256=first['receipt_sha256'],
        first_window_phase2_sha256=exhibits['phase2_result_sha256'],
        planned_logical_requests=len(requests), maximum_logical_requests=len(requests), maximum_HTTP_attempts=len(requests)*3,
        document_count=len(candidates), index_count=len(candidates), new_discovery_requests=0,
        overall_maximum_logical_requests=19, overall_maximum_HTTP_attempts=57)
    return result


class WindowReader(FrozenFpiReader):
    authorization_denial_is_systemic = False


def make_window_exhibit_plan(parent, phase1, directory):
    plan = phase1['plan']
    if plan['contract'] != CONTRACT or phase1['logical_requests'] != len(plan['exact_requests']):
        raise ValueError('second_window_all_planned_entries_must_terminate')
    receipts = json.loads((directory / 'receipts.json').read_bytes())
    rows = []
    for filing in plan['candidates']:
        payloads = {}
        for stage in ('index', 'document'):
            found = [r for r in receipts if r['stage'] == stage and r['filing'] == filing and not r['failure_class']]
            if len(found) == 1:
                receipt = found[0]
                raw = (directory / receipt['artifact']).read_bytes()
                if sha256_bytes(raw) != receipt['raw_sha256']:
                    raise ValueError('window_raw_binding_mismatch')
                payloads[stage] = raw
        if len(payloads) != 2:
            continue
        try:
            urls = exhibit_selection(json.loads(payloads['index']), payloads['document'].decode(errors='replace'), parent, filing)
            denial = None
        except AcquisitionDenied as exc:
            urls, denial = [], str(exc)
        rows.append({'ticker': parent['ticker'], 'filing': filing, 'existing_selector_eligible_urls': urls,
            'existing_selector_denial': denial, 'newly_known_exhibit_urls': urls,
            'index_sha256': sha256_bytes(payloads['index']), 'primary_sha256': sha256_bytes(payloads['document'])})
    requests, excluded = eligible_discovered(parent, rows)
    result = deepcopy(parent)
    result.update(contract=EXHIBIT_CONTRACT, run_id=parent['run_id'] + ':fpi-window2-exhibits',
        window_number=2, parent_plan_sha256=digest(parent), phase1_plan_sha256=digest(plan),
        phase1_receipts_sha256=phase1['receipt_sha256'], discovery_rows=rows, discovery_rows_sha256=digest(rows),
        exact_requests=requests, candidates=list({r['filing']['accessionNumber']: r['filing'] for r in requests}.values()),
        excluded=excluded, recursive_discovery=False,
        limits={**parent['limits'], 'discovery': 0, 'companyfacts': 0, 'current': 3, 'prior': 0,
            'indexes_per_filing': 0, 'documents_per_filing': 3, 'linked_exhibits': 0},
        planned_logical_requests=len(requests), maximum_logical_requests=len(requests), maximum_HTTP_attempts=len(requests)*3)
    return result


def verify_window(parent, discovery_raw, captured_documents, first, exhibits, *, directory, phase2_directory=None):
    plan = make_window_plan(parent, discovery_raw, captured_documents, first, exhibits)
    result = verify_frozen_followup(plan, [], directory)
    result['final_coverage_exhausted'] = False
    if phase2_directory is not None:
        second_plan = make_window_exhibit_plan(parent, result, directory)
        second = verify_phase2_capture(second_plan, phase2_directory)
        result['documents'].extend(second['documents'])
        result['phase2'] = {k: v for k, v in second.items() if k != 'documents'}
        result['final_coverage_exhausted'] = result['logical_requests'] == len(plan['exact_requests']) and not second['unattempted']
    return result
