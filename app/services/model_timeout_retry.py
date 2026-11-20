"""Exact, local evidence for one timeout recovery. No provider-side claims."""
import hashlib
import json
import os
import re

B2_PER_TICKER_ONE_RETRY_V1 = 'B2_PER_TICKER_ONE_RETRY_V1'
B2_US2_DIAGNOSTIC_V1 = 'B2_US2_DIAGNOSTIC_V1'
B2_SR5_DIAGNOSTIC_V1 = 'B2_SR5_DIAGNOSTIC_V1'


def retry_policy_limits(policy):
    if policy == B2_PER_TICKER_ONE_RETRY_V1:
        return 29,13,42
    if policy == B2_US2_DIAGNOSTIC_V1:
        return 6,2,8
    if policy == B2_SR5_DIAGNOSTIC_V1:
        return 11,4,15
    raise ValueError('model_b2_retry_policy_unknown')


def b2_retry_binding(plan, policy=B2_PER_TICKER_ONE_RETRY_V1):
    plan.validate()
    if plan.topology != 'CANONICAL_PRODUCTION' or list(plan.cohort.market_subjects) != ['us']:
        raise ValueError('model_b2_retry_original_us_plan_required')
    if policy == B2_US2_DIAGNOSTIC_V1 and tuple(plan.cohort.market_subjects['us']) != ('GOOGL','MU'):
        raise ValueError('model_b2_retry_exact_diagnostic_subjects_required')
    if policy == B2_SR5_DIAGNOSTIC_V1 and (
            tuple(plan.cohort.market_subjects['us']) != ('CRCL','HUT','SKHY','TSM','WULF')
            or tuple(plan.cohort.limitation_subjects) != ('SKHY',)):
        raise ValueError('model_b2_retry_exact_sr5_limitation_scope_required')
    value = dict(policy=policy, plan_sha256=plan.sha256,
        base_slots=len(plan.slots), maximum=len(plan.slots)+sum(s.stage=='B2' for s in plan.slots),
        slot_stages={s.slot_id:s.stage for s in plan.slots},
        b2_slots={s.slot_id:s.subjects[0] for s in plan.slots if s.stage == 'B2' and len(s.subjects) == 1})
    validate_b2_retry_binding(value)
    return value


def validate_b2_retry_binding(value):
    base,reserves,maximum = retry_policy_limits(value.get('policy') if isinstance(value,dict) else None)
    if (type(value) is not dict or set(value) != {'policy','plan_sha256','base_slots','maximum','slot_stages','b2_slots'}
            or not re.fullmatch('[a-f0-9]{64}', value['plan_sha256'])
            or type(value['base_slots']) is not int or value['base_slots'] != base
            or type(value['maximum']) is not int or value['maximum'] != maximum
            or len(value['slot_stages']) != base or len(value['b2_slots']) != reserves
            or len(set(value['b2_slots'].values())) != reserves
            or value['policy'] == B2_US2_DIAGNOSTIC_V1 and set(value['b2_slots'].values()) != {'GOOGL','MU'}
            or value['policy'] == B2_SR5_DIAGNOSTIC_V1 and set(value['b2_slots'].values()) != {'CRCL','HUT','TSM','WULF'}
            or set(value['b2_slots']) != {s for s,stage in value['slot_stages'].items() if stage == 'B2'}
            or any(not s or not t for s,t in value['b2_slots'].items())):
        raise ValueError('model_b2_per_ticker_retry_binding_invalid')
    return value


def confirmed_timeout(path, *, worker_pid, worker_returncode, receipt, prompt_sha256, schema_sha256):
    if (worker_returncode != 0 or receipt.get('status') != 'FAIL'
            or receipt.get('error_code') != 'TRANSPORT_TIMEOUT' or receipt.get('process_started') is not True
            or receipt.get('cli_returncode') != -9):
        return None
    try:
        os.killpg(worker_pid, 0)
    except ProcessLookupError:
        pass
    except OSError:
        return None
    else:
        return None
    try:
        exit_path, event_path = path/'market-cli-exit.json', path/'events.jsonl'
        dispatch_path = path/'market-cli-dispatch.json'
        raw_path = path/'raw-output.json'
        if raw_path.exists() or raw_path.is_symlink() or any(
                f.is_symlink() or not f.is_file() or f.stat().st_size > 128*1024
                for f in (exit_path,event_path,dispatch_path)):
            return None
        end, dispatch = (json.loads(f.read_bytes()) for f in (exit_path,dispatch_path))
        events = event_path.read_bytes()
        if not events.endswith(b'\n') or [json.loads(line)['type'] for line in events.splitlines()] != [
                'thread.started','turn.started']:
            return None
        from app.services.unified_run_artifacts import sha256_bytes
        inputs = path/'approved-input'
        if (any(f.is_symlink() or not f.is_file() or f.stat().st_size > 384*1024
                for f in (inputs/'prompt.txt',inputs/'provider-wire-schema.json'))
                or sha256_bytes((inputs/'prompt.txt').read_bytes()) != prompt_sha256
                or sha256_bytes((inputs/'provider-wire-schema.json').read_bytes()) != schema_sha256
                or dispatch['timeout_seconds'] != 600 or dispatch['sandbox'] != 'read-only'
                or dispatch['model'] != 'gpt-6.1-sol' or dispatch['effort'] != 'high'
                or end['timed_out'] is not True or end['process_started'] is not True
                or end['event_scan_truncated'] is not False or end['completed_turns'] != 0
                or end['first_event'] != 'thread.started' or end['last_event'] != 'turn.started'
                or end['cli_returncode'] != -9 or not 600 <= end['elapsed_seconds'] <= 630):
            return None
        proof = dict(attempt_id=path.name, prompt_sha256=prompt_sha256, schema_sha256=schema_sha256,
            event_sha256=hashlib.sha256(events).hexdigest(), elapsed_seconds=end['elapsed_seconds'],
            started_at=dispatch['dispatched_at'], ended_at=end['ended_at'], worker_group_reaped=True,
            remote_completion_and_billing='UNOBSERVED', error='TRANSPORT_TIMEOUT')
        validate_timeout(proof)
        return proof
    except (OSError, ValueError, TypeError, KeyError):
        return None


def validate_timeout(proof):
    from datetime import datetime

    if (set(proof) != {'attempt_id','prompt_sha256','schema_sha256','event_sha256','elapsed_seconds',
            'started_at','ended_at','worker_group_reaped','remote_completion_and_billing','error'}
            or not re.fullmatch(r'[A-Za-z0-9_.:-]+-[a-f0-9]{32}', proof['attempt_id'])
            or any(not re.fullmatch('[a-f0-9]{64}', proof[k]) for k in ('prompt_sha256','schema_sha256','event_sha256'))
            or not 600 <= proof['elapsed_seconds'] <= 630 or proof['worker_group_reaped'] is not True
            or proof['remote_completion_and_billing'] != 'UNOBSERVED' or proof['error'] != 'TRANSPORT_TIMEOUT'):
        raise ValueError('model_retry_timeout_proof_invalid')
    started, ended = (datetime.fromisoformat(proof[k]) for k in ('started_at','ended_at'))
    if started.utcoffset() is None or ended.utcoffset() is None or started >= ended:
        raise ValueError('model_retry_timeout_clock_invalid')


def verify_b2_coverage(output, *, subjects, slots, exhausted, bound, attempts):
    omissions = output.get('unissued',{})
    rows = output['rows']
    scope = {s.subjects[0]:s.slot_id for s in slots if s.stage == 'B2'}
    if (set(scope) != set(subjects) or set(rows)&set(omissions) or set(rows)|set(omissions) != set(subjects)
            or set(exhausted) != {scope[t] for t in omissions}):
        raise ValueError('production_partial_b2_original_coverage_gap')
    for t, value in omissions.items():
        slot = scope[t]
        expected = dict(status='B2_UNISSUED_TIMEOUT', slot_id=slot,
            request_sha256=bound[slot]['payload_sha256'], attempts=len(attempts[slot]))
        if value != expected:
            raise ValueError('production_partial_b2_original_timeout_gap')


def verify_render_partition(*, messages, subjects, slots, b2, journal, accepted_content_sha256, plan=None):
    from app.services.unified_snapshot_contract import digest

    omitted = b2.get('unissued',{})
    ordinary = subjects
    if plan is not None:
        from app.services.model_execution_plan import ModelExecutionPlan

        if type(plan) is not ModelExecutionPlan:
            raise ValueError('research_timeout_original_model_plan_required')
        plan.validate()
        if (list(plan.cohort.market_subjects) != ['us'] or tuple(slots) != plan.slots
                or tuple(subjects) != plan.cohort.market_subjects['us']):
            raise ValueError('research_timeout_plan_scope_drift')
        limits = set(plan.cohort.limitation_subjects)
        if limits and omitted:
            raise ValueError('production_limitation_no_send_decision_binding')
        ordinary = tuple(t for t in subjects if t not in limits)
    verify_b2_coverage(b2, subjects=ordinary, slots=slots, exhausted=journal['exhausted'],
        bound=journal['bound'], attempts=journal['attempts'])
    if (journal['stopped'] or journal['inherited']
            or set(journal['accepted']) != {s.slot_id for s in slots}-journal['exhausted']
            or journal['used'] != set(journal['accepted']) | journal['exhausted']
            or sorted(m['message_id'] for m in messages) != sorted({'MARKET_US',*subjects}-set(omitted))
            or digest(messages) != accepted_content_sha256
            or any(m.get('NO_SEND') is not True or not m.get('text') for m in messages)):
        raise ValueError('research_timeout_render_partition_drift')
    for slot in (s for s in slots if s.stage == 'B2' and s.subjects[0] not in omitted):
        row = b2['rows'][slot.subjects[0]]
        result = row['result']
        if (result['status'] != 'PASS' or result['ticker'] != slot.subjects[0]
                or result['request_sha256'] != journal['bound'][slot.slot_id]['payload_sha256']
                or result['attempts'][-1]['raw_sha256'] != journal['accepted'][slot.slot_id]):
            raise ValueError('research_timeout_accepted_b2_drift')


def read_no_send_partition(cycle, *, plan, invocation_journal):
    """Cold integrity readback of validated stage artifacts; no live Owner is issued."""
    from app.services.model_invocation_journal import read_invocation_journal
    from app.services.new_buyer_request_owner import validate_result
    from app.services.research_artifact_budget import plain_path
    from app.services.research_no_send_run import PARTIAL, RESEARCH_STAGES, TERMINAL
    from app.services.research_request_storage import load_stage_request, load_stage_response
    from app.services.unified_snapshot_contract import digest

    plan.validate()
    cycle, invocation_journal = plain_path(cycle), plain_path(invocation_journal)
    terminal = json.loads((cycle/'terminal.json').read_bytes())
    binding = terminal['child_binding']
    if (terminal['status'] not in {PARTIAL,TERMINAL} or terminal['normal_messages_sent'] is not False
            or terminal['failure_notifications_sent'] is not False or binding['plan_sha256'] != plan.sha256
            or binding['run_id'] != plan.cohort.run_id or binding['source_generation'] != plan.cohort.source_generation
            or binding['assessment_date'] != plan.cohort.assessment_date
            or [r['stage'] for r in terminal['stage_receipts']] != list(RESEARCH_STAGES)):
        raise ValueError('research_timeout_cold_terminal_drift')
    outputs = {}
    for row in terminal['stage_receipts']:
        folder = cycle/row['stage'].lower()
        request = load_stage_request(folder/'request.json', expected_logical_sha256=row['logical_request_sha256'],
            expected_storage_sha256=row['storage_record_sha256'])
        response = load_stage_response(folder/'response.json',request)
        if (row['status'] != 'PASS' or request['run_id'] != plan.cohort.run_id
                or request['snapshot']['child_binding'] != binding or request['inputs'] != outputs
                or digest(response) != row['response_sha256']):
            raise ValueError('research_timeout_cold_stage_drift')
        outputs[row['stage']] = response
    b2, messages = outputs['B2']['output'],outputs['RENDER']['output']['messages']
    omitted = b2.get('unissued',{})
    if (bool(omitted) != (terminal['status'] == PARTIAL) or terminal.get('unissued',{}) != omitted
            or terminal['messages'] != messages or terminal['messages_sha256'] != digest(messages)):
        raise ValueError('research_timeout_cold_render_drift')
    raw = invocation_journal.read_bytes()
    if not raw:
        raise ValueError('research_timeout_cold_empty_journal')
    identity = json.loads(raw.split(b'\n',1)[0])['identity']
    cap = identity.get('timeout_retry_cap', 0)
    per_ticker = identity.get('b2_retry_policy')
    if per_ticker is not None and (cap or per_ticker != b2_retry_binding(plan,per_ticker['policy'])):
        raise ValueError('research_timeout_cold_per_ticker_scope')
    if type(cap) is not int or cap not in (0,1,2) or (not (cap or per_ticker) and omitted):
        raise ValueError('research_timeout_cold_retry_scope')
    expected = dict(contract='model-invocation-journal-v1',plan_sha256=plan.sha256,
        maximum=per_ticker['maximum'] if per_ticker else len(plan.slots)+cap)
    if cap:
        expected['timeout_retry_cap'] = cap
    if per_ticker:
        expected['b2_retry_policy'] = per_ticker
    journal = read_invocation_journal(raw, expected)
    verify_render_partition(messages=messages,subjects=plan.cohort.market_subjects['us'],slots=plan.slots,b2=b2,
        journal=journal,accepted_content_sha256=outputs['VALIDATE']['output']['content_sha256'],plan=plan)
    for ticker, row in b2['rows'].items():
        folder = plain_path(cycle/'b2'/ticker)
        result = row['result']
        final = result['attempts'][-1]
        raw = plain_path(folder/f"attempt-{final['ordinal']}"/'response.raw').read_bytes()
        if (hashlib.sha256(raw).hexdigest() != final['raw_sha256'] or json.loads(raw) != result['output']
                or json.loads(plain_path(folder/'accepted.json').read_bytes()) != result
                or json.loads(plain_path(folder/'authorization.json').read_bytes()) != row['authorization']
                or validate_result(result['output'],json.loads(plain_path(folder/'request.json').read_bytes()),
                    expected_request_sha256=result['request_sha256'])['status'] != 'PASS'):
            raise ValueError('research_timeout_cold_b2_artifact_drift')
    for ticker, omission in omitted.items():
        folder = plain_path(cycle/'b2'/ticker)
        if ((folder/'accepted.json').exists() or (folder/'accepted.json').is_symlink()
                or json.loads(plain_path(folder/'unissued.json').read_bytes()) != omission):
            raise ValueError('research_timeout_cold_unissued_artifact_drift')
    return dict(status=terminal['status'], count=len(messages), expected=len(binding['message_ids']),
        unissued=sorted(omitted), message_sha256={m['message_id']:digest(m) for m in messages},
        physical_attempts=journal['physical_calls'], timeout_retries=journal['retry_used'])
