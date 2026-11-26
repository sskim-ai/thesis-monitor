"""Exact, local evidence for one timeout recovery. No provider-side claims."""
import hashlib
import json
import os
import re

B2_PER_TICKER_ONE_RETRY_V1 = 'B2_PER_TICKER_ONE_RETRY_V1'
ALL_MODEL_STAGE_ONE_RETRY_V1 = 'ALL_MODEL_STAGE_ONE_RETRY_V1'
FULL_RETRY_POLICIES = (B2_PER_TICKER_ONE_RETRY_V1, ALL_MODEL_STAGE_ONE_RETRY_V1)
B2_US2_DIAGNOSTIC_V1 = 'B2_US2_DIAGNOSTIC_V1'
B2_SR5_DIAGNOSTIC_V1 = 'B2_SR5_DIAGNOSTIC_V1'


def all_stage_retry(binding):
    return binding is not None and binding['policy'] == ALL_MODEL_STAGE_ONE_RETRY_V1


def stock_slot_retry(binding, slot_id):
    return bool(binding and (slot_id in binding['b2_slots'] or all_stage_retry(binding)
        and binding['slot_stages'].get(slot_id) in ('CORE', 'A', 'B', 'B2')))


def roster_model_ceiling(subjects):
    """Pre-Source upper bound; actual frozen slots can only reduce this."""
    n = len(subjects)
    if n < 1:
        raise ValueError('scheduled_monitoring_empty_roster')
    return 2 * (1 + 3 * ((n + 2) // 3) + n)


def retry_policy_limits(policy, *, plan=None):
    if policy in FULL_RETRY_POLICIES:
        if plan is not None:
            plan.validate()
            if (plan.topology != 'CANONICAL_PRODUCTION'
                    or len(plan.cohort.market_subjects) != 1
                    or next(iter(plan.cohort.market_subjects)) not in ('kr','us')
                    or sum(s.stage=='MARKET' for s in plan.slots)!=1
                    or any(len(s.subjects)!=1 or len(s.security_ids)!=1 for s in plan.slots if s.stage=='B2')):
                raise ValueError('model_b2_retry_single_market_plan_required')
            base = len(plan.slots)
            reserves = base if policy == ALL_MODEL_STAGE_ONE_RETRY_V1 else sum(s.stage=='B2' for s in plan.slots)
            return base,reserves,base+reserves
        if policy == ALL_MODEL_STAGE_ONE_RETRY_V1:
            # No fixed population or call count exists for this policy.
            return 0,0,0
        # Legacy callers without a frozen plan retain the original US contract.
        return 29,13,42
    if policy == B2_US2_DIAGNOSTIC_V1:
        return 6,2,8
    if policy == B2_SR5_DIAGNOSTIC_V1:
        return 11,4,15
    raise ValueError('model_b2_retry_policy_unknown')


def b2_retry_binding(plan, policy=B2_PER_TICKER_ONE_RETRY_V1):
    plan.validate()
    if (plan.topology != 'CANONICAL_PRODUCTION' or len(plan.cohort.market_subjects)!=1
            or (policy not in FULL_RETRY_POLICIES and list(plan.cohort.market_subjects)!=['us'])):
        raise ValueError('model_b2_retry_original_us_plan_required')
    if policy == B2_US2_DIAGNOSTIC_V1 and tuple(plan.cohort.market_subjects['us']) != ('GOOGL','MU'):
        raise ValueError('model_b2_retry_exact_diagnostic_subjects_required')
    if policy == B2_SR5_DIAGNOSTIC_V1 and (
            tuple(plan.cohort.market_subjects['us']) != ('CRCL','HUT','SKHY','TSM','WULF')
            or tuple(plan.cohort.limitation_subjects) != ('SKHY',)):
        raise ValueError('model_b2_retry_exact_sr5_limitation_scope_required')
    base,_,maximum=retry_policy_limits(policy,plan=plan)
    value = dict(policy=policy, plan_sha256=plan.sha256,
        base_slots=base, maximum=maximum,
        slot_stages={s.slot_id:s.stage for s in plan.slots},
        b2_slots={s.slot_id:s.subjects[0] for s in plan.slots if s.stage == 'B2' and len(s.subjects) == 1})
    validate_b2_retry_binding(value)
    return value


def validate_b2_retry_binding(value):
    policy=value.get('policy') if isinstance(value,dict) else None
    base,reserves,maximum = retry_policy_limits(policy)
    if policy in FULL_RETRY_POLICIES:
        base = len(value.get('slot_stages',{}))
        reserves = base if policy == ALL_MODEL_STAGE_ONE_RETRY_V1 else len(value.get('b2_slots',{}))
        maximum = base + reserves
    b2_count = list(value.get('slot_stages',{}).values()).count('B2') if policy == ALL_MODEL_STAGE_ONE_RETRY_V1 else reserves
    if (type(value) is not dict or set(value) != {'policy','plan_sha256','base_slots','maximum','slot_stages','b2_slots'}
            or not re.fullmatch('[a-f0-9]{64}', value['plan_sha256'])
            or type(value['base_slots']) is not int or value['base_slots'] != base
            or type(value['maximum']) is not int or value['maximum'] != maximum
            or len(value['slot_stages']) != base or len(value['b2_slots']) != b2_count
            or base<1 or list(value['slot_stages'].values()).count('MARKET')!=1
            or any(stage not in {'MARKET','CORE','A','B','B2'} for stage in value['slot_stages'].values())
            or len(set(value['b2_slots'].values())) != b2_count
            or value['policy'] == B2_US2_DIAGNOSTIC_V1 and set(value['b2_slots'].values()) != {'GOOGL','MU'}
            or value['policy'] == B2_SR5_DIAGNOSTIC_V1 and set(value['b2_slots'].values()) != {'CRCL','HUT','TSM','WULF'}
            or set(value['b2_slots']) != {s for s,stage in value['slot_stages'].items() if stage == 'B2'}
            or any(not s or not t for s,t in value['b2_slots'].items())):
        raise ValueError('model_b2_per_ticker_retry_binding_invalid')
    return value


def market_timeout_retry_cap(binding, *, retry_cap=0, retry_market='us'):
    if binding is not None:
        validate_b2_retry_binding(binding)
        if all_stage_retry(binding):
            if retry_market not in ('kr','us') or type(retry_cap) is not int or retry_cap != 0:
                raise ValueError('model_all_stage_retry_scope_invalid')
            return 1
        if (retry_market not in ('kr','us') or type(retry_cap) is not int or retry_cap not in (0,1)
                or retry_cap and binding['policy']!=B2_PER_TICKER_ONE_RETRY_V1):
            raise ValueError('model_combined_retry_scope_invalid')
        # Explicit cap1 reserves MARKET independently; legacy US cap0 stays unchanged.
        return int(binding['policy']==B2_PER_TICKER_ONE_RETRY_V1 and (retry_cap==1 or retry_market=='us'))
    if retry_market == 'kr':
        if binding is not None or type(retry_cap) is not int or retry_cap != 1:
            raise ValueError('model_kr_market_retry_scope_invalid')
        return 1
    if retry_market != 'us':
        raise ValueError('model_market_retry_market_invalid')
    return 0


def b2_retry_budget_bounds(binding, *, retry_cap=0, retry_market='us'):
    """US retries share the approved remainder after every initial call is reserved."""
    market_timeout_retry_cap(binding, retry_cap=retry_cap, retry_market=retry_market)
    maximum = binding['maximum'] + retry_cap
    if all_stage_retry(binding):
        return maximum, maximum
    minimum = (binding['base_slots']
        if retry_market == 'us' and retry_cap == 0 and binding['policy'] == B2_PER_TICKER_ONE_RETRY_V1
        else maximum)
    return minimum, maximum


def confirmed_timeout(path, *, worker_pid, worker_returncode, receipt, prompt_sha256, schema_sha256,
                      frozen_market=None):
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
        from app.services.production_model_profile import DEFAULT_SOL_INPUT_BYTES, sol_prompt_limit_bytes
        from app.services.unified_run_artifacts import sha256_bytes
        inputs = path/'approved-input'
        caps = ((inputs/'prompt.txt', sol_prompt_limit_bytes(frozen_market)),
                (inputs/'provider-wire-schema.json', DEFAULT_SOL_INPUT_BYTES))
        if (any(f.is_symlink() or not f.is_file() or f.stat().st_size > cap for f,cap in caps)
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
        if (len(plan.cohort.market_subjects)!=1 or tuple(slots) != plan.slots
                or tuple(subjects) != next(iter(plan.cohort.market_subjects.values()))):
            raise ValueError('research_timeout_plan_scope_drift')
        limits = set(plan.cohort.limitation_subjects)
        ordinary = tuple(t for t in subjects if t not in limits)
    verify_b2_coverage(b2, subjects=ordinary, slots=slots, exhausted=journal['exhausted'],
        bound=journal['bound'], attempts=journal['attempts'])
    market=next(iter(plan.cohort.market_subjects)) if plan is not None else 'us'
    if (journal['stopped'] or journal['inherited']
            or set(journal['accepted']) != {s.slot_id for s in slots}-journal['exhausted']
            or journal['used'] != set(journal['accepted']) | journal['exhausted']
            or sorted(m['message_id'] for m in messages) != sorted({'MARKET_'+market.upper(),*subjects}-set(omitted))
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
    market=next(iter(plan.cohort.market_subjects))
    retry_market=identity.get('timeout_retry_market','us')
    if per_ticker is not None and (per_ticker != b2_retry_binding(plan,per_ticker['policy'])
            or cap not in (0,1) or cap and per_ticker['policy']!=B2_PER_TICKER_ONE_RETRY_V1
            or retry_market!=market):
        raise ValueError('research_timeout_cold_per_ticker_scope')
    if type(cap) is not int or cap not in (0,1,2) or (not (cap or per_ticker) and omitted):
        raise ValueError('research_timeout_cold_retry_scope')
    maximum = per_ticker['maximum']+cap if per_ticker else len(plan.slots)+cap
    if per_ticker:
        minimum, full_maximum = b2_retry_budget_bounds(per_ticker, retry_cap=cap, retry_market=retry_market)
        maximum = terminal.get('model_acceptances',{}).get('approved_max_invocations',maximum)
        if type(maximum) is not int or not minimum <= maximum <= full_maximum:
            raise ValueError('research_timeout_cold_retry_budget_scope')
    expected = dict(contract='model-invocation-journal-v1',plan_sha256=plan.sha256, maximum=maximum)
    if cap:
        expected['timeout_retry_cap'] = cap
    if per_ticker:
        expected['b2_retry_policy'] = per_ticker
    if retry_market=='kr':
        expected['timeout_retry_market']='kr'
    journal = read_invocation_journal(raw, expected)
    verify_render_partition(messages=messages,subjects=plan.cohort.market_subjects[market],slots=plan.slots,b2=b2,
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
