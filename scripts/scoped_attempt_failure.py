"""Failure ownership for the opt-in US/KR shadow controllers."""
from scripts import m12dr_fresh_blind_reproof as p
from app.services.unified_snapshot_contract import digest

TRANSPORT = 'TRANSPORT_OR_RESPONSE_FORM_FAILURE'
SEMANTIC = 'LOCAL_SEMANTIC_VALIDATION_FAILURE'
SYSTEMIC = 'SYSTEMIC_FAILURE'


class ResponseFormFailure(p.BatchFailure):
    """An allowed transport failure or no schema-valid response object."""


def classify(exc, attempt):
    if isinstance(exc, p.SystemicFailure):
        return SYSTEMIC, False
    if isinstance(exc, ResponseFormFailure):
        return TRANSPORT, True
    if (attempt and attempt['provider_schema_status'] == 'PASS'
            and isinstance(exc, ValueError)):
        return SEMANTIC, False
    # Unexpected controller errors are not a reason for another model sample.
    return SYSTEMIC, False


def begin(row, *, generation, stage, spec, destination, request_hashes):
    value = dict(stage=stage, market=spec['market'], batch=spec['batch'],
        subjects=list(spec['subjects']), logical_request_id=f"{generation}:{stage}:{spec['market']}:{spec['batch']}",
        attempt=row['attempts'], request_sha256=digest(request_hashes),
        raw_response_sha256=None, provider_schema_status='NOT_EVALUATED',
        local_semantic_status='NOT_EVALUATED', failure_class=None,
        retry_eligible=False, retry_reason=None)
    row['active_attempt'] = value
    row['attempt_destination'] = str(destination)
    return value


def finish(row, exc=None):
    attempt = row.get('active_attempt')
    if attempt is None:
        return SYSTEMIC, False
    failure, retry = classify(exc, attempt) if exc is not None else (None, False)
    attempt.update(failure_class=failure, retry_eligible=retry,
        retry_reason='EXISTING_BOUNDED_RESPONSE_RETRY' if retry else
        'LOCAL_SEMANTIC_IS_NOT_RESAMPLED' if failure == SEMANTIC else
        'IMMEDIATE_FAIL_STOP' if failure else 'SUCCESS',
        local_semantic_status='FAIL' if failure == SEMANTIC else
        'PASS' if exc is None else attempt['local_semantic_status'])
    if exc is not None:
        attempt.update(error_type=type(exc).__name__, error_code=str(exc))
    from pathlib import Path
    from app.services.unified_run_artifacts import durable_json
    durable_json(Path(row['attempt_destination']) / 'attempt-receipt.json', attempt, exclusive=True)
    row.setdefault('attempt_receipts', []).append(dict(attempt))
    return failure, retry
