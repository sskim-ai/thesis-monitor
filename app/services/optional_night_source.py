"""A failed optional night probe keeps its original attempts, never price facts.

This is an unavailable input on the existing Source path. It neither retries
requests nor creates a separate acquisition, permission, or evidence store.
"""
from datetime import datetime, timedelta
import json
from pathlib import Path
from zoneinfo import ZoneInfo
import httpx

from app.services.selected_source_plan import US_NIGHT_OPTIONAL, us_night_optional
from app.services.unified_snapshot_contract import digest
from app.services.unified_run_artifacts import sha256_bytes

FAILURE = 'optional-night-unavailable-v1'
FAILURE_NOTICES = {
    'UNAVAILABLE_COLLECTION_ERROR': '한국 야간선물: 수집 오류로 이번 수치·등락은 미확보입니다.',
    'UNAVAILABLE_INVALID_DATA': '한국 야간선물: 자료 처리 오류로 이번 수치·등락은 미확보입니다.',
}
STATES = set(FAILURE_NOTICES)
ROUTE = 'https://data-dbg.krx.co.kr/svc/apis/drv/fut_bydd_trd'


async def collect_optional(action, *, frozen, results, run_ledger):
    from app.services.campaign_runtime_cap import OptionalNightCollectionError
    from app.services.bounded_financial_acquisition import SystemicStop
    from app.services.research_artifact_budget import ArtifactCapacityError
    if not us_night_optional(frozen):
        raise ValueError('optional_night_explicit_policy_required')
    try:
        return await action()
    except OptionalNightCollectionError as exc:
        if run_ledger.state()['state'] == 'STOPPED_NO_SEND':
            raise
        return unavailable_value(exc, frozen=frozen, results=results, collection_error=True)
    except (SystemicStop, ArtifactCapacityError):
        raise
    except (ValueError, KeyError, TypeError) as exc:
        # Scope/auth/cap stops, cancellation and filesystem failures are not data.
        if run_ledger.state()['state'] == 'STOPPED_NO_SEND':
            raise
        return unavailable_value(exc, frozen=frozen, results=results,
            collection_error=isinstance(exc.__cause__, httpx.HTTPError))


def error_location(exc):
    """Record code location, not exception text or request credentials."""
    root = Path(__file__).resolve().parents[2]
    frame = None
    tb = exc.__traceback__
    while tb is not None:
        path = Path(tb.tb_frame.f_code.co_filename).resolve()
        if path.is_relative_to(root) and path.parts[len(root.parts)] in {'app', 'scripts'}:
            frame = dict(file=str(path.relative_to(root)), function=tb.tb_frame.f_code.co_name,
                line=tb.tb_lineno)
        tb = tb.tb_next
    return dict(error_class=type(exc).__name__, application_frame=frame)


def unavailable_value(exc, *, frozen, results, collection_error=False):
    if not us_night_optional(frozen):
        raise ValueError('optional_night_explicit_policy_required')
    keys = ['night:KOSPI200:'+day for day in frozen['candidate']['night_query_dates']]
    attempted = [key for key in keys if key in results]
    if not attempted or attempted != keys[:len(attempted)]:
        raise ValueError('optional_night_original_attempt_prefix_required')
    return dict(provider='krx_night_futures', observations=[], optional_night_failure=dict(
        contract=FAILURE, policy=US_NIGHT_OPTIONAL,
        state='UNAVAILABLE_COLLECTION_ERROR' if collection_error else 'UNAVAILABLE_INVALID_DATA',
        code='NIGHT_COLLECTION_FAILED' if collection_error else 'NIGHT_PROCESSING_FAILED',
        observed_at=frozen['frozen_at'], **error_location(exc),
        attempted_logical_ids=attempted,
        final_receipt_sha256=[results[key]['receipt_sha256'] for key in attempted]))


def failure_inputs(root, frozen, outcome, policy, value):
    """Use already-sealed dispatch receipts for both HTTP and transport errors."""
    from app.services.sealed_fresh_dispatch import decode_request_plan, consume_bound_result
    if not us_night_optional(frozen):
        raise ValueError('optional_night_explicit_policy_required')
    root = Path(root)
    plan = decode_request_plan(frozen['plan'])
    descriptors = {d.logical_request_id:d for d in plan.descriptors}
    proof = value['optional_night_failure']
    receipts, bodies = [], {}
    for key, receipt_sha in zip(proof['attempted_logical_ids'], proof['final_receipt_sha256'], strict=True):
        d = descriptors[key]
        base = root/'dispatch/receipts'/key
        final = json.loads((base/'final.json').read_bytes())
        identity = dict(generation_id=plan.generation_id, logical_request_id=key,
            descriptor_sha256=d.descriptor_sha256, plan_sha256=plan.plan_sha256,
            request_sha256=d.request_semantic_sha256, role=d.consumer_role)
        if (final != outcome['logical_results'][key] or final.get('status') not in {'PASS','FAILED'}
                or final.get('receipt_sha256') != receipt_sha
                or digest({k:v for k,v in final.items() if k != 'receipt_sha256'}) != receipt_sha
                or any(final.get(k) != v for k,v in identity.items()) or len(final['attempts']) != 1):
            raise ValueError('optional_night_original_final_mismatch')
        attempt = final['attempts'][0]
        if (json.loads((base/'attempt-1.json').read_bytes()) != attempt
                or any(attempt.get(k) != v for k,v in identity.items())
                or attempt.get('status') in {401,403}
                or attempt.get('error') in {'SECRET_IN_SOURCE_BODY','CREDENTIAL_RESPONSE_INVALID'}):
            raise ValueError('optional_night_original_attempt_mismatch')
        if final['status'] == 'PASS':
            consume_bound_result(root=root/'dispatch', plan=plan, logical_id=key,
                receipt_sha256=receipt_sha)
        artifact = attempt.get('artifact')
        if artifact:
            expected = str((base/'attempt-1.body').relative_to(root/'dispatch'))
            path = root/'dispatch'/artifact
            if artifact != expected or any(p.is_symlink() for p in (path, *path.parents)):
                raise OSError('optional_night_original_body_path')
            raw = path.read_bytes()
            if sha256_bytes(raw) != attempt['raw_sha256']:
                raise OSError('optional_night_original_body_changed')
            bodies[artifact] = raw
        receipts.append(dict(run_id=plan.generation_id, acquisition_id=plan.generation_id+':night',
            provider='krx_night_futures', sealed_logical_id=key, sealed_final_receipt_sha256=receipt_sha,
            request=dict(method='GET', route=ROUTE, params={'basDd':key.rsplit(':',1)[1].replace('-','')}),
            outcome='HTTP_RESPONSE' if attempt.get('status') is not None else 'TRANSPORT_UNKNOWN',
            http_status=attempt.get('status'), artifact=artifact,
            artifact_sha256=attempt.get('raw_sha256'), requested_at=attempt['started_at'],
            received_at=attempt['finished_at']))
    start = datetime.fromisoformat(frozen['frozen_at'])
    return dict(receipts=receipts, bodies=bodies, body_hashes={k:sha256_bytes(v) for k,v in bodies.items()},
        observed_at=start, run_id=plan.generation_id, acquisition_id=plan.generation_id+':night',
        expected_value_sha256=digest(value), policy=policy, run_started_at=start,
        acquisition_cutoff=datetime.fromisoformat(outcome['completed_at']), optional_failure=value)


def validate_failure(value, receipts, body_hashes, *, run_id, acquisition_id, observed_at, start, cutoff):
    proof = value.get('optional_night_failure', {})
    days = [(observed_at.astimezone(ZoneInfo('Asia/Seoul')).date()-timedelta(days=i)).isoformat()
        for i in range(7)]
    keys = ['night:KOSPI200:'+day for day in days[:len(receipts)]]
    if (value.get('provider') != 'krx_night_futures' or value.get('observations') != []
            or proof.get('contract') != FAILURE or proof.get('policy') != US_NIGHT_OPTIONAL
            or proof.get('state') not in STATES or not 1 <= len(receipts) <= 7
            or proof.get('observed_at') != observed_at.isoformat()
            or proof.get('attempted_logical_ids') != keys
            or proof.get('final_receipt_sha256') != [r.get('sealed_final_receipt_sha256') for r in receipts]
            or acquisition_id != run_id+':night' or not start <= observed_at <= cutoff):
        raise ValueError('optional_night_unavailable_binding_mismatch')
    used, previous = set(), start
    for key, day, row in zip(keys, days, receipts):
        begin, end = (datetime.fromisoformat(row[k]) for k in ('requested_at','received_at'))
        if (row['run_id'] != run_id or row['acquisition_id'] != acquisition_id
                or row['provider'] != 'krx_night_futures' or row['sealed_logical_id'] != key
                or row['request'] != dict(method='GET', route=ROUTE, params={'basDd':day.replace('-','')})
                or row['http_status'] in {401,403}
                or row['outcome'] not in {'HTTP_RESPONSE','TRANSPORT_UNKNOWN'}
                or not previous <= begin <= end <= cutoff):
            raise ValueError('optional_night_unavailable_attempt_mismatch')
        previous = end
        artifact = row.get('artifact')
        if artifact:
            if artifact in used or row['artifact_sha256'] != body_hashes.get(artifact):
                raise ValueError('optional_night_unavailable_body_mismatch')
            used.add(artifact)
        elif row.get('artifact_sha256') is not None or row['outcome'] != 'TRANSPORT_UNKNOWN':
            raise ValueError('optional_night_unavailable_missing_body')
    if used != set(body_hashes):
        raise ValueError('optional_night_unavailable_unused_body')
    return dict(state=proof['state'], optional=True, coverage_resolved=True, value=None,
        collected=bool(receipts), physical_requests=len(receipts), error_code=proof['code'],
        error_class=proof['error_class'], application_frame=proof.get('application_frame'),
        producer_observation_count=0, current_consumer_eligible_count=0,
        source_value_sha256=digest(value), request_provenance_sha256=digest(receipts),
        stale_promoted=False, provider_outage_inferred=False)


def replay_failure(*, value, receipts, bodies, body_hashes, observed_at, run_id, acquisition_id,
                   expected_value_sha256, run_started_at, acquisition_cutoff):
    if (digest(value) != expected_value_sha256 or set(bodies) != set(body_hashes)
            or any(sha256_bytes(raw) != body_hashes[key] for key,raw in bodies.items())):
        raise ValueError('optional_night_unavailable_source_changed')
    validate_failure(value, receipts, body_hashes, run_id=run_id, acquisition_id=acquisition_id,
        observed_at=observed_at, start=run_started_at, cutoff=acquisition_cutoff)
    return dict(value=value, value_sha256=expected_value_sha256, original_receipts=receipts,
        source_hashes=body_hashes, original_run_id=run_id, original_acquisition_id=acquisition_id,
        observed_at=observed_at.isoformat(), network_calls=0)
