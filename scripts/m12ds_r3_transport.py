"""At most two identical official attempts; only typed no-response transient failures retry."""
from copy import deepcopy
from pathlib import Path
import json
import shutil
import time

from scripts import m12dr_fresh_blind_reproof as p
from scripts import m12ds_launch_context as launch

POLICY = {'contract': 'm12ds-r3-rev1-identical-transient-retry-v1', 'logical_requests': 26,
          'max_attempts_per_request': 2, 'max_processes': 52, 'timeout_seconds': 1200,
          'offline_substitution': False, 'model': 'gpt-5.6-sol', 'effort': 'xhigh'}
RUNTIME_ROOT = Path('/private/tmp')


def classify(code, *, output_present, event_types, stderr, tool_event=False):
    lowered = stderr.lower()
    if tool_event:
        return 'SYSTEMIC'
    if any(s in lowered for s in ('unknownissuer', 'invalid peer certificate', 'certificate verify failed',
                                  'attempt to write a readonly database', 'failed to initialize in-process app-server client',
                                  'unauthorized', 'authentication', 'invalid api key', 'login required')):
        return 'SYSTEMIC'
    if code is None:
        return 'PASS'
    if code == 'TRANSPORT_TIMEOUT' and not output_present:
        return 'TRANSIENT'
    if code in ('PROCESS_NONZERO', 'FINAL_OUTPUT_EMPTY') and not output_present and 'turn.started' in event_types:
        return 'TRANSIENT'
    if code in ('PROCESS_NONZERO', 'FINAL_OUTPUT_EMPTY', 'FINAL_OUTPUT_MALFORMED', 'TRANSPORT_TIMEOUT'):
        return 'BATCH_LOCAL'
    return 'SYSTEMIC'


def sanitize_events(path):
    events, unsafe = [], False
    for line in path.read_bytes().splitlines() if path.exists() else []:
        try:
            event = json.loads(line)
            kind, item = event.get('type'), event.get('item', {}).get('type')
            if kind in ('item.started', 'item.updated', 'item.completed'):
                unsafe |= item not in ('reasoning', 'agent_message')
            else:
                unsafe |= kind not in ('thread.started', 'turn.started', 'turn.completed', 'turn.failed', 'error')
            events.append({'type': kind, 'item_type': item})
        except (ValueError, AttributeError):
            unsafe = True
    return events, unsafe


def event_security_failure(path):
    for line in path.read_bytes().splitlines() if path.exists() else []:
        try:
            event = json.loads(line)
            if event.get('type') in ('error', 'turn.failed'):
                if classify('PROCESS_NONZERO', output_present=False, event_types={'turn.started'},
                            stderr=json.dumps(event)) == 'SYSTEMIC':
                    return True
        except (ValueError, AttributeError):
            continue
    return False


def request_identity(request, frozen_dependencies):
    source = Path(request['directory'])
    return {'request_files': p.manifest(source), 'frozen_dependencies': deepcopy(frozen_dependencies),
            'model': POLICY['model'], 'effort': POLICY['effort'], 'timeout_seconds': POLICY['timeout_seconds']}


def invoke(proof, stage, spec, request):
    proof.preinvoke(stage, spec, request)
    identity = request_identity(request, proof.dependencies)
    row = proof.ledger[-1]
    row['attempt_receipts'] = []
    for attempt in (1, 2):
        if len(proof.ledger) > POLICY['logical_requests'] or sum(r['attempts'] for r in proof.ledger) >= POLICY['max_processes']:
            raise p.SystemicFailure('R3_PROCESS_BUDGET_EXCEEDED')
        proof.preinvoke(stage, spec, request)
        if request_identity(request, proof.dependencies) != identity:
            raise p.SystemicFailure('RETRY_LOGICAL_REQUEST_IDENTITY_DRIFT')
        context, expected = launch.context_receipt(), p.read(proof.report / 'host-context.json')
        if not (context['state_access']['effective_open_readwrite_without_write']
                and context['uid'] == expected['uid'] and context['gid'] == expected['gid']
                and context['safe_environment'] == expected['safe_environment']):
            raise p.SystemicFailure('HOST_LAUNCH_CONTEXT_DRIFT')
        namespace = f"{proof.gen}-{stage}-{spec['market']}-{spec['batch']:02d}-attempt-{attempt}"
        runtime = RUNTIME_ROOT / namespace
        approved = runtime / 'approved-input'
        approved.mkdir(parents=True, exist_ok=False)
        source = Path(request['directory'])
        for name in ('prompt.txt', 'provider-wire-schema.json'):
            shutil.copy2(source / name, approved / name)
        destination = proof.sealed / 'calls' / stage / spec['market'] / f"batch-{spec['batch']:02d}" / f'attempt-{attempt}'
        destination.mkdir(parents=True, exist_ok=False)
        p.write(destination / 'request-identity.json', identity)
        p.write(destination / 'host-context.json', context)
        req = p.transport.OfficialShadowRequest(p.binding(), namespace,
                    p.sha(approved / 'prompt.txt'), p.sha(approved / 'provider-wire-schema.json'))
        receipt = {'attempt': attempt, 'transport_namespace': namespace, 'started_at': p.now(),
                   'prompt_sha256': req.prompt_sha256, 'schema_sha256': req.schema_sha256,
                   'logical_identity_sha256': p.owner.canonical_sha256(identity), 'directory': str(destination)}
        row.update(status='INVOKING', attempts=attempt, started_at=row.get('started_at') or receipt['started_at'],
                   prompt_sha256=req.prompt_sha256, schema_sha256=req.schema_sha256)
        proof.publish()
        output, log = runtime / 'raw-output.json', runtime / 'events.jsonl'
        start, failure = time.monotonic(), None
        try:
            transport_receipt = p.transport.invoke_official_shadow(
                codex_bin=str(p.BIN), prompt=approved / 'prompt.txt', schema=approved / 'provider-wire-schema.json',
                output=output, log=log, cwd=approved, timeout=1200, state_namespace=namespace, request=req)
            p.write(destination / 'transport-receipt.json', transport_receipt)
        except p.transport.OfficialShadowError as exc:
            failure = exc.code
        except Exception:
            failure = 'UNCLASSIFIED_RUNTIME_EXCEPTION'
        finally:
            elapsed = round(time.monotonic() - start, 3)
            events, unsafe = sanitize_events(log)
            stderr_path = runtime / 'events.jsonl.stderr'
            stderr = stderr_path.read_text() if stderr_path.exists() else ''
            has_output = output.exists() and output.stat().st_size > 0
            classification = classify(failure, output_present=has_output,
                                      event_types={e['type'] for e in events}, stderr=stderr, tool_event=unsafe)
            if event_security_failure(log):
                classification = 'SYSTEMIC'
            if output.exists():
                shutil.copy2(output, destination / 'raw-output.json')
                receipt['raw_output_sha256'] = p.sha(output)
            p.write(destination / 'sanitized-events.json', {'events': events, 'hidden_reasoning_exported': False})
            receipt.update(completed_at=p.now(), elapsed_seconds=elapsed, failure_code=failure,
                           classification=classification, output_present=has_output)
            row['attempt_receipts'].append(receipt)
            row.update(completed_at=receipt['completed_at'], elapsed_seconds=sum(r['elapsed_seconds'] for r in row['attempt_receipts']))
            p.write(destination / 'attempt-receipt.json', receipt)
            proof.publish()
        proof.preinvoke(stage, spec, request)
        if request_identity(request, proof.dependencies) != identity:
            raise p.SystemicFailure('POST_ATTEMPT_REQUEST_IDENTITY_DRIFT')
        if classification == 'SYSTEMIC':
            raise p.SystemicFailure('R3_SYSTEMIC_RUNTIME_OR_SECURITY:' + str(failure))
        if classification == 'TRANSIENT' and attempt == 1:
            continue
        if classification != 'PASS':
            raise p.BatchFailure(str(failure))
        raw = p.read(destination / 'raw-output.json')
        errors = {name: p.owner.validate_json_schema(raw, p.read(source / name))
                  for name in ('provider-wire-schema.json', 'internal-semantic-schema.json')}
        p.write(destination / 'schema-validation.json', errors)
        p.require(not any(errors.values()), 'SCHEMA_REJECT')
        row['accepted_attempt'] = attempt
        row['accepted_directory'] = str(destination)
        row['raw_output_sha256'] = p.sha(destination / 'raw-output.json')
        return raw, destination
    raise AssertionError('unreachable_attempt_limit')
