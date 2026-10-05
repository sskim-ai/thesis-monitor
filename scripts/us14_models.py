"""Qualified US14-only official execution. Retry only an unchanged failed call."""
from copy import deepcopy
from dataclasses import asdict
import json
from pathlib import Path
import shutil
import sys
import time
import traceback

from app.services.unified_run_artifacts import durable_bytes, durable_json
from app.services.unified_stock_acquisition import UNIVERSE
from scripts import qualified_official_launch_context as q
from scripts import m12dr_fresh_blind_reproof as p
from scripts.r9_rev11_models import FreshExecution, owner
from scripts.r2b_r5_execution import STAGES
from scripts.us14_source_scope import require_us14_plan
from scripts import scoped_attempt_failure as failures

AUTHORITY = p.REPO/'docs/work-instructions/20260930-rev31-c1-state-ownership-clarification.md'
SUBJECTS = UNIVERSE['us']


class Us14Execution(FreshExecution):
    MARKET_SCOPES = ('us',)
    SUBJECT_COUNT = 14
    MESSAGE_COUNT = 15
    CALL_LIMITS = {'market': 1, 'core': 5, 'pass-a': 5, 'pass-b': 5}
    TIMEOUT_SECONDS = 600
    MAX_RETRIES = 2
    ATTEMPT_BUDGET = 48
    SUCCESS_TERMINAL = 'R2B_R9_REV46_US_15_MESSAGE_PASS'
    FAILURE_TERMINAL = 'R2B_R9_REV46_US_MODEL_MESSAGE_GAP'

    def __init__(self, root, sources, source_only):
        super().__init__(root, sources)
        require_us14_plan(self.source_frozen)
        self.source_only = Path(source_only)
        self.qualified = None
        self.names = q.inventory_names()
        self.entry_environment = q.environment(self.names)
        self.guard = q.ManualMutationGuard([p.OPERATING, Path.home()/'.codex', self.sources,
            self.source_only, Path.home()/'Library/LaunchAgents'])
        self.active_batches = None

    def full_topology(self):
        rows = [r for r in owner._batch_topology() if r['market'] == 'us']
        p.require(len(rows) == 5 and sorted(t for r in rows for t in r['subjects']) == list(SUBJECTS),
            'us14_batch_topology_gap')
        return rows

    def batch_topology(self):
        return [r for r in self.full_topology()
                if self.active_batches is None or r['batch'] in self.active_batches]

    def capture(self, stage_name, spec, context, schema, prompt):
        p.require(spec['market'] == 'us', 'us14_foreign_market_request')
        expected = [] if stage_name == 'market' else next(
            (r['subjects'] for r in self.full_topology() if r['batch'] == spec['batch']), None)
        p.require(expected == spec['subjects'], 'us14_request_subject_scope')
        return super().capture(stage_name, spec, context, schema, prompt)

    def freeze_extra(self):
        return dict(scope='US14_ONLY', source_only_zip_sha256=p.sha(self.source_only),
            capture_contract='US14_15_MESSAGE_CAPTURE_V1',
            maintenance_authorization_sha256=p.sha(AUTHORITY), maximum_attempts=self.ATTEMPT_BUDGET,
            auxiliary_issuer_dependencies=self.source_frozen['candidate']['auxiliary_issuer_dependencies'])

    def prepare(self):
        p.require(self.source_only.is_file(), 'us14_source_only_seal_required')
        super().prepare()

    def verify(self):
        super().verify()
        require_us14_plan(self.source_frozen)
        p.require(self.frozen['scope'] == 'US14_ONLY' and self.frozen['max_calls'] == 16,
            'us14_model_budget_scope')
        p.require(self.frozen['timeout_seconds'] == 600 and self.frozen['retries'] == 2,
            'us14_model_attempt_policy_drift')
        p.require(set(self.prepared) == set(SUBJECTS) and set(self.projected) == {'us'},
            'us14_model_input_scope')
        p.require(self.freeze_extra() == {k: self.frozen[k] for k in self.freeze_extra()},
            'us14_source_or_authority_drift')
        p.require(self.guard.blocked_attempts == 0, 'us14_manual_mutation_attempt')
        p.require(all(r['market'] == 'us' and set(r['subjects']) <= set(SUBJECTS)
            and r['attempts'] <= 3 for r in self.ledger), 'us14_call_scope')
        for stage, limit in self.CALL_LIMITS.items():
            p.require(sum(r['stage'] == stage for r in self.ledger) <= limit, 'us14_logical_call_budget')

    def identity(self):
        return q.LaunchIdentity(implementation_sha=self.frozen['controller']['head'], source_generation_id=self.source_gen,
            whole_source_sha256=self.frozen['fresh_source_replay']['first_sha256'],
            source_only_zip_sha256=self.frozen['source_only_zip_sha256'],
            request_freeze_sha256=p.sha(self.report/'execution-freeze.json'),
            prompt_schema_sha256=q.digest(p.read(self.sealed/'initial-requests.json')),
            executable_sha256=p.binding().executable_sha256,
            launcher_sha256=p.sha(p.REPO/'app/services/official_codex_shadow_transport_service.py'),
            qualification_sha256=p.binding().qualification_sha256, cwd_sha256=q.legacy.digest(str(p.REPO)),
            **asdict(self.execution_policy()))

    def execution_policy(self):
        policy = p.transport.OfficialShadowExecutionPolicy(
            self.frozen['timeout_seconds'], self.frozen['max_calls'], self.frozen['retries'])
        policy.validate()
        p.require((policy.timeout_seconds, policy.max_calls, policy.retries) ==
            (self.TIMEOUT_SECONDS, sum(self.CALL_LIMITS.values()), self.MAX_RETRIES),
            'scoped_execution_policy_drift')
        return policy

    def current_launch_context(self):
        return q.capture_context(self.names)

    def qualify_host(self, secret_scan):
        self.verify()
        context = self.current_launch_context()
        evidence = q.StateWriteEvidence('CONTROLLER_ONLY_OFFICIAL_MAINTENANCE_AUTHORIZED', 0, 0,
            q.digest(context), p.binding().executable_sha256,
            p.sha(p.REPO/'app/services/official_codex_shadow_transport_service.py'), p.sha(AUTHORITY))
        identity = self.identity()
        qualified = q.QualifiedOfficialModelLaunchContext.qualify(identity=identity, expected_identity=identity,
            preparation=p.read(self.report/'host-context.json'), preparation_sha256=self.frozen['host_context_sha256'],
            actual_preparation_sha256=p.sha(self.report/'host-context.json'), context=context,
            entry_environment=self.entry_environment, state_evidence=evidence, binding_verified=True,
            provider_calls=0, secret_scan_passed=secret_scan(dict(context=context, identity=asdict(identity), evidence=asdict(evidence))),
            expected_maintenance_authorization_sha256=self.frozen['maintenance_authorization_sha256'])
        durable_json(self.report/'qualified-actual-host.json', qualified.receipt(), exclusive=True)
        durable_json(self.report/'official-model-execution-context-freeze.json', dict(contract=q.CONTRACT,
            authority_sha256=qualified.sha256, receipt_file_sha256=p.sha(self.report/'qualified-actual-host.json'),
            qualified_at=p.now(), native_internal_maintenance='AUTHORIZED_NOT_MEASURED_AS_ZERO',
            direct_db_write_calls=0, permission_mutations=0, source_only_sha256=p.sha(self.source_only)), exclusive=True)
        self.qualified = qualified
        self.context_freeze_sha = p.sha(self.report/'official-model-execution-context-freeze.json')

    def authorize_launch_context(self, context):
        p.require(self.qualified is not None, 'us14_qualified_host_required')
        self.verify()
        freeze = p.read(self.report/'official-model-execution-context-freeze.json')
        p.require(p.sha(self.report/'official-model-execution-context-freeze.json') == self.context_freeze_sha,
            'us14_context_freeze_drift')
        p.require(p.sha(self.report/'qualified-actual-host.json') == freeze['receipt_file_sha256'], 'us14_host_receipt_drift')
        receipt = self.qualified.verify(context=context, identity=self.identity(),
            preparation_sha256=p.sha(self.report/'host-context.json'), freeze_sha256=freeze['authority_sha256'])
        ordinal = sum(r['attempts'] for r in self.ledger) + 1
        durable_json(self.report/'per-call-contexts'/f'{ordinal:02d}.json', receipt, exclusive=True)

    def invoke(self, stage, spec, request):
        self.verify()
        self.authorize_launch_context(self.current_launch_context())
        src = Path(request['directory'])
        row = self.ledger[-1]
        attempt = row['attempts'] + 1
        p.require(attempt <= 3, 'us14_retry_budget')
        relative = Path(stage)/spec['market']/f"batch-{spec['batch']:02d}"/f'attempt-{attempt}'
        dst, dest = Path('/private/tmp')/self.gen/relative, self.sealed/'calls'/relative
        inp = dst/'approved-input'
        inp.mkdir(parents=True, exist_ok=False)
        dest.mkdir(parents=True, exist_ok=False)
        for name in ('prompt.txt', 'provider-wire-schema.json'):
            shutil.copy2(src/name, inp/name)
        reqid = f"{self.gen}-{stage}-{spec['market']}-{spec['batch']:02d}-attempt-{attempt}"
        req = p.transport.OfficialShadowRequest(p.binding(), reqid, p.sha(inp/'prompt.txt'),
            p.sha(inp/'provider-wire-schema.json'), execution_policy=self.execution_policy())
        hashes = dict(prompt_sha256=req.prompt_sha256, schema_sha256=req.schema_sha256)
        if row['attempts']:
            p.require(all(row[k] == value for k, value in hashes.items()), 'us14_retry_request_drift')
        row.update(status='INVOKING', attempts=attempt, **hashes)
        attempt_receipt = failures.begin(row, generation=self.gen, stage=stage, spec=spec,
            destination=dest, request_hashes={**hashes,
                'internal_schema_sha256': p.sha(src/'internal-semantic-schema.json')})
        self.publish()
        started = time.monotonic()
        try:
            receipt = p.transport.invoke_official_shadow(codex_bin=str(p.BIN), prompt=inp/'prompt.txt',
                schema=inp/'provider-wire-schema.json', output=dst/'raw-output.json', log=dst/'events.jsonl',
                cwd=inp, timeout=self.TIMEOUT_SECONDS, state_namespace=reqid, request=req)
            p.write(dest/'transport-receipt.json', receipt)
        except p.transport.OfficialShadowError as exc:
            p.write(dest/'transport-failure.json', dict(code=exc.code, elapsed_seconds=time.monotonic()-started))
            try:
                p.Reproof.transport_failure(self, exc, dst, time.monotonic()-started)
            except p.BatchFailure as allowed:
                raise failures.ResponseFormFailure(str(allowed)) from exc
        finally:
            row.update(completed_at=p.now(), elapsed_seconds=round(time.monotonic()-started, 3))
            if (dst/'raw-output.json').exists():
                durable_bytes(dest/'raw-output.json', (dst/'raw-output.json').read_bytes(), exclusive=True)
                attempt_receipt['raw_response_sha256'] = p.sha(dest/'raw-output.json')
            # Seal the response bytes before any local validator can reject them.
            durable_json(dest/'raw-response-receipt.json', dict(attempt_receipt), exclusive=True)
            events, unsafe = [], False
            if (dst/'events.jsonl').exists():
                for line in (dst/'events.jsonl').read_bytes().splitlines():
                    try:
                        event = json.loads(line)
                        kind, item = event.get('type'), event.get('item', {}).get('type')
                        unsafe |= (item not in {'reasoning', 'agent_message'} if kind in
                            {'item.started', 'item.updated', 'item.completed'} else kind not in
                            {'thread.started', 'turn.started', 'turn.completed', 'turn.failed', 'error'})
                        events.append(dict(type=kind, item_type=item))
                    except (ValueError, AttributeError):
                        unsafe = True
            p.write(dest/'sanitized-events.json', dict(events=events, hidden_reasoning_exported=False))
            if unsafe:
                raise p.SystemicFailure('UNDECLARED_OR_UNKNOWN_TOOL_EVENT')
        self.verify()
        stderr = (dst/'events.jsonl.stderr').read_text().lower()
        if any(s in stderr for s in ('attempt to write a readonly database', 'unknownissuer',
                                    'invalid peer certificate', 'failed to initialize in-process app-server client')):
            raise p.SystemicFailure('OFFICIAL_RUNTIME_WARNING_RECURRED')
        try:
            output = p.read(dest/'raw-output.json')
        except (FileNotFoundError, json.JSONDecodeError, UnicodeDecodeError) as exc:
            attempt_receipt['provider_schema_status'] = 'FAIL'
            raise failures.ResponseFormFailure('MALFORMED_OR_MISSING_RESPONSE') from exc
        errors = {name: owner.validate_json_schema(output, p.read(src/name))
            for name in ('provider-wire-schema.json', 'internal-semantic-schema.json')}
        p.write(dest/'schema-validation.json', errors)
        attempt_receipt['provider_schema_status'] = 'FAIL' if any(errors.values()) else 'PASS'
        if any(errors.values()):
            raise failures.ResponseFormFailure('SCHEMA_REJECT')
        return output, dest

    def bounded(self, stage, spec, request):
        p.require(not any(r['stage'] == stage and r['batch'] == spec['batch'] for r in self.ledger),
            'logical_call_already_attempted')
        self.ledger.append(dict(stage=stage, **spec, attempts=0, status='NOT_STARTED', failures=[]))
        row = self.ledger[-1]
        for _ in range(self.MAX_RETRIES + 1):
            # A rejected attempt cannot partially seed the next stage or retry.
            snapshot = deepcopy({key: getattr(self, key) for key in
                ('cores', 'arows', 'brows', 'markets', 'entries', 'limits')})
            prior_attempts = row['attempts']
            row['active_attempt'] = None
            error = None
            try:
                getattr(self, stage.replace('-', '_'))(spec, request)
                row.update(status='PASS', failure_class=None, retry_eligible=False)
                break
            except Exception as exc:
                error = exc
                for key, value in snapshot.items():
                    setattr(self, key, value)
                row.update(status='FAIL', failure_type=type(exc).__name__, failure_code=str(exc))
                row['failures'].append(dict(attempt=row['attempts'], type=type(exc).__name__, code=str(exc)))
                self.publish()
                failure_class, retry_eligible = failures.classify(exc, row.get('active_attempt'))
                row.update(failure_class=failure_class, retry_eligible=retry_eligible)
                if failure_class == failures.SYSTEMIC or row['attempts'] == prior_attempts:
                    raise
                if not retry_eligible:
                    break
            finally:
                failures.finish(row, error)
                self.publish()
        return row['status'] == 'PASS'

    def run(self):
        p.require(not (self.report/'model-structural-ledger.json').exists(), 'one_execution_only')
        self.stage_manifests = dict(self.frozen['stage_manifests'])
        terminal, stage = self.FAILURE_TERMINAL, 'market'
        try:
            self.verify()
            initial = p.read(self.sealed/'initial-requests.json')
            p.require(p.sha(self.sealed/'initial-requests.json') == self.frozen['initial_request_manifest_sha256'], 'initial_request_drift')
            for stage in STAGES:
                if stage in initial:
                    requests = initial[stage]
                else:
                    previous = 'core' if stage == 'pass-a' else 'pass-a'
                    self.active_batches = {r['batch'] for r in self.ledger if r['stage'] == previous and r['status'] == 'PASS'}
                    requests = (self.before_a() if stage == 'pass-a' else self.before_b()) if self.active_batches else []
                for request in requests:
                    self.bounded(stage, {k: request[k] for k in ('market', 'batch', 'subjects')}, request)
                accepted = {'market': self.markets, 'core': self.cores, 'pass-a': self.arows, 'pass-b': self.brows}[stage]
                p.write(self.sealed/(stage+'-output-freeze.json'), dict(generation_id=self.gen, accepted=accepted,
                    limits=self.limits[stage], call_files=p.manifest(self.sealed/'calls'/stage)))
            p.require(all(len(rows)+len(self.limits[s]) == self.SUBJECT_COUNT for s, rows in
                [('core', self.cores), ('pass-a', self.arows), ('pass-b', self.brows)])
                and set(self.markets) == set(self.MARKET_SCOPES), 'scoped_stages_incomplete')
            stage = 'render'
            self.render()
            terminal = self.SUCCESS_TERMINAL
        except Exception as exc:
            p.write(self.sealed/'failure.json', dict(stage=stage, type=type(exc).__name__, error=str(exc), traceback=traceback.format_exc()))
        finally:
            p.write(self.report/'execution-complete.json', dict(terminal=terminal, generation_id=self.gen,
                source_generation_id=self.source_gen, calls={s: sum(r['attempts'] for r in self.ledger if r['stage'] == s) for s in STAGES},
                accepted=dict(Market=len(self.markets), Core=len(self.cores), A=len(self.arows), B=len(self.brows)),
                accepted_limits={s: len(v) for s, v in self.limits.items()},
                messages=len(list((self.root/'messages').glob('*.txt'))),
                retry=sum(max(r['attempts']-1, 0) for r in self.ledger), fallback=0, judge=0,
                provider_refresh=0, production_side_effects=0, timeout_seconds=600,
                independent_assessment_content_read=False, reveal_gate='CLOSED_UNTIL_RESULT_SEAL'))
            self.publish()

    def run_qualified(self, secret_scan):
        self.guard.roots += tuple(path.resolve() for path in [self.root/'inputs', self.report/'execution-freeze.json',
            self.report/'host-context.json', self.sealed/'initial-requests.json', self.requests/'core', self.requests/'market'])
        sys.addaudithook(self.guard)
        self.qualify_host(secret_scan)
        self.guard.roots += tuple((self.report/name).resolve() for name in
            ['qualified-actual-host.json', 'official-model-execution-context-freeze.json'])
        try:
            self.run()
        finally:
            durable_json(self.report/'direct-mutation-guard.json', dict(blocked_attempts=self.guard.blocked_attempts,
                direct_db_writes=0, permission_mutations=0, native_internal_state_management='AUTHORIZED_CLI_OWNED'), exclusive=True)
