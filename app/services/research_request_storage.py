"""Content references for private stage files; logical request bytes are unchanged."""
import json
from pathlib import Path

from app.services.research_artifact_budget import plain_path
from app.services.unified_run_artifacts import durable_bytes, sha256_bytes
from app.services.unified_runtime_v2 import CONTRACT, STAGES, StageResultV2, validate_stage_v2
from app.services.unified_snapshot_contract import digest, encoded

STORAGE = 'prepared-research-request-reference-v1'
HEADER = {'contract', 'run_id', 'stage', 'snapshot_sha256', 'configuration_sha256'}


def _immutable(path, raw, role):
    path = plain_path(path)
    if path.exists():
        if not path.is_file() or path.read_bytes() != raw:
            raise ValueError('research_storage_immutable_conflict')
        return
    durable_bytes(path, raw, exclusive=True, role=role)


def _read(path):
    path = plain_path(path)
    if not path.is_file():
        raise ValueError('research_storage_regular_file_required')
    raw = path.read_bytes()
    return raw, json.loads(raw)


def _scope(request):
    snapshot = request['snapshot']
    collection = snapshot['collection']
    binding = snapshot['child_binding']
    run = request['run_id']
    if (request['contract'] != CONTRACT or request['stage'] not in STAGES[:-1]
            or digest(snapshot) != request['snapshot_sha256']
            or binding['run_id'] != run or collection['production_envelope']['generation_id'] != run
            or binding['market'] != collection['market']
            or binding['source_generation'] != collection['monitoring_input']['source_generation_id']
            or set(request['inputs']) != set(STAGES[:STAGES.index(request['stage'])])):
        raise ValueError('research_storage_logical_scope_drift')
    for stage, response in request['inputs'].items():
        if (response['stage'], response['run_id'], response['generation_id'], response['snapshot_sha256'],
                response['status'], response['errors']) != (stage, run, run, request['snapshot_sha256'], 'PASS', []):
            raise ValueError('research_storage_upstream_scope_drift')
    return dict(market=binding['market'], source_generation=binding['source_generation'], cutoff=binding.get('cutoff'))


def save_stage_request(root, request):
    root = plain_path(root)
    scope = _scope(request)
    header = {key: request[key] for key in HEADER}
    snapshot_ref = f"snapshots/{header['snapshot_sha256']}.json"
    _immutable(root / snapshot_ref, encoded(request['snapshot']) + b'\n', 'source')
    upstream = {}
    for stage, response in request['inputs'].items():
        relative = f'{stage.lower()}/response.json'
        raw, saved = _read(root / relative)
        if saved != response:
            raise ValueError('research_storage_upstream_bytes_drift')
        upstream[stage] = dict(ref=relative, sha256=sha256_bytes(raw))
    record = dict(storage_contract=STORAGE, header=header, scope=scope, snapshot_ref=snapshot_ref,
        upstream=upstream, logical_request_sha256=digest(request))
    raw = encoded(record) + b'\n'
    _immutable(root / request['stage'].lower() / 'request.json', raw, 'result')
    return dict(logical_request_sha256=record['logical_request_sha256'], storage_record_sha256=sha256_bytes(raw))


def load_stage_request(path, *, expected_logical_sha256=None, expected_storage_sha256=None):
    path = plain_path(path)
    raw, record = _read(path)
    if expected_storage_sha256 is not None and sha256_bytes(raw) != expected_storage_sha256:
        raise ValueError('research_storage_record_hash_drift')
    if 'storage_contract' not in record:
        request = record
    else:
        if (record['storage_contract'] != STORAGE or set(record['header']) != HEADER
                or record['header']['stage'] not in STAGES[:-1]
                or path.parent.name != record['header']['stage'].lower()):
            raise ValueError('research_storage_header_drift')
        header = record['header']
        if path.name != 'request.json' or path.parent.parent.name != header['run_id']:
            raise ValueError('research_storage_request_location_drift')
        pin = header['snapshot_sha256']
        if not isinstance(pin, str) or len(pin) != 64 or any(c not in '0123456789abcdef' for c in pin):
            raise ValueError('research_storage_snapshot_pin_invalid')
        if record['snapshot_ref'] != f'snapshots/{pin}.json':
            raise ValueError('research_storage_snapshot_path_drift')
        root = path.parent.parent
        _, snapshot = _read(root / record['snapshot_ref'])
        inputs = {}
        for stage, ref in record['upstream'].items():
            if stage not in STAGES[:-1] or ref['ref'] != f'{stage.lower()}/response.json':
                raise ValueError('research_storage_upstream_path_drift')
            upstream_raw, response = _read(root / ref['ref'])
            if sha256_bytes(upstream_raw) != ref['sha256']:
                raise ValueError('research_storage_upstream_hash_drift')
            inputs[stage] = response
        request = dict(**header, snapshot=snapshot, inputs=inputs)
        if _scope(request) != record['scope'] or digest(request) != record['logical_request_sha256']:
            raise ValueError('research_storage_logical_request_drift')
    _scope(request)
    if expected_logical_sha256 is not None and digest(request) != expected_logical_sha256:
        raise ValueError('research_storage_logical_pin_drift')
    return request


def load_stage_response(path, request):
    _, response = _read(path)
    validate_stage_v2(StageResultV2.model_validate(response), request)
    return response
