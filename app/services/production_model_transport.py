"""Separate production authorization over the qualified official byte executor."""
import asyncio
from dataclasses import asdict, dataclass
import json
import os
from pathlib import Path
import signal
import sys
import uuid

from app.services.official_codex_shadow_transport_service import OfficialCodexBinding
from app.services.codex_runtime_binding import CurrentOfficialCodexBinding, validate_binding, binding_from_json
from app.services.official_transport_input_preflight import PREFLIGHT_REJECT_EXIT
from app.services.production_b2_execution import ModelTransportError
from app.services.fixture_context_authority import reject_test_only_production
from app.services.unified_run_artifacts import durable_bytes, durable_json, sha256_bytes
from app.services.unified_snapshot_contract import digest, encoded
from app.services.production_model_profile import CONTRACT_V2, SolHighWirePolicy, SolHighCallBudget, sol_high
from app.services.vnext_execution_profile import SOL_HIGH_V1

CONTRACT = "official-codex-production-transport-v1"
CONTRACT_V3 = 'official-codex-production-transport-v3-dynamic-sol-high'
ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class ProductionWirePolicy:
    timeout_seconds: int = 600
    max_calls: int = 1
    retries: int = 0
    purpose: str = "PRODUCTION_MONITORING"

    def validate(self):
        if (self.timeout_seconds, self.max_calls, self.retries, self.purpose) != (600, 1, 0, "PRODUCTION_MONITORING"):
            raise ValueError("production_wire_policy_drift")


@dataclass(frozen=True)
class ProductionWireRequest:
    binding: OfficialCodexBinding
    request_id: str
    prompt_sha256: str
    schema_sha256: str
    execution_policy: ProductionWirePolicy | SolHighWirePolicy = ProductionWirePolicy()
    model_plan_scope: dict | None = None
    observe_timeout: bool = False


def request_profile(request):
    request.execution_policy.validate()
    if type(request.execution_policy) is SolHighWirePolicy:
        return SOL_HIGH_V1
    if type(request.execution_policy) is not ProductionWirePolicy:
        raise ValueError('production_wire_policy_type')
    return None


def request_from_frame(frame):
    base = {'contract', 'directory', 'binding', 'request_id', 'prompt_sha256', 'schema_sha256'}
    dynamic = frame.get('contract') == CONTRACT_V3
    extras = {'execution_policy', 'authorization_sha256'} | ({'execution_plan', 'slot_scope'} if dynamic else set())
    if frame.get('contract') in (CONTRACT_V2, CONTRACT_V3) and set(frame) == base | extras:
        policy = SolHighWirePolicy(**frame['execution_policy'])
        policy.validate()
        auth = Path(frame['directory']) / 'production-authorization.json'
        raw = auth.read_bytes()
        if sha256_bytes(raw) != frame['authorization_sha256']:
            raise ValueError('production_worker_authorization_drift')
        value = json.loads(raw)
        if any(value.get(k) != frame[k] for k in ('contract', 'request_id', 'prompt_sha256', 'schema_sha256', 'execution_policy')):
            raise ValueError('production_worker_profile_drift')
        if (value.get('model'), value.get('effort'), value.get('timeout')) != (policy.model, policy.effort, policy.timeout_seconds):
            raise ValueError('production_worker_model_drift')
        if dynamic:
            from app.services.model_execution_plan import ModelExecutionPlan, validate_slot_scope
            plan = ModelExecutionPlan.from_dict(frame['execution_plan'])
            scope = frame['slot_scope']
            validate_slot_scope(plan, scope)
            inherited = value.get('inherited_market_slot')
            physical_slots = len(plan.slots)
            if inherited is not None:
                from app.services.model_invocation_journal import read_invocation_journal
                from app.services.research_artifact_budget import plain_path

                market_slots = [slot.slot_id for slot in plan.slots if slot.stage == 'MARKET']
                if market_slots != [inherited] or scope['market'] != 'kr' or scope['stage'] == 'MARKET':
                    raise ValueError('production_worker_invalid_inherited_market_slot')
                journal = plain_path(auth.parent.parent / 'invocation-ledger' / plan.cohort.run_id / 'events.jsonl')
                identity = dict(contract='model-invocation-journal-v1', plan_sha256=plan.sha256,
                    maximum=value['maximum'], inherited_market_slot=inherited)
                state = read_invocation_journal(journal.read_bytes(), identity)
                if (state['stopped'] or set(state['inherited']) != {inherited}
                        or state['bound'].get(scope['slot_id']) != scope
                        or state['used'] - state['accepted'].keys() != {scope['slot_id']}
                        or len(state['used']) != value['physical_call']):
                    raise ValueError('production_worker_inherited_market_journal_drift')
                physical_slots -= 1
            if (value.get('slot_scope') != frame['slot_scope'] or value.get('execution_plan_sha256') != plan.sha256
                    or value.get('payload_sha256') != frame['slot_scope']['payload_sha256']
                    or value.get('planned_slots') != len(plan.slots)
                    or type(value.get('maximum')) is not int or value['maximum'] < physical_slots
                    or not 1 <= value.get('physical_call', 0) <= value['maximum']):
                raise ValueError('production_worker_dynamic_plan_or_budget_drift')
            if 'timeout_retry_cap' in value or 'b2_retry_policy' in value:
                from app.services.model_invocation_journal import read_invocation_journal
                from app.services.research_artifact_budget import plain_path

                from app.services.model_timeout_retry import b2_retry_binding, b2_retry_budget_bounds
                per_ticker = value.get('b2_retry_policy')
                cap = value.get('timeout_retry_cap', 0)
                retry_market = value.get('timeout_retry_market','us')
                kr_market_retry = (retry_market=='kr' and (cap==1 or per_ticker is not None)
                    and list(plan.cohort.market_subjects)==['kr'])
                slot_id = scope['slot_id']
                attempt = value['attempt']
                if (type(cap) is not int or (cap not in (1,2) if per_ticker is None else cap not in (0,1))
                        or per_ticker is not None and per_ticker != b2_retry_binding(plan,per_ticker['policy']) or inherited is not None
                        or retry_market not in ('us','kr')
                        or (list(plan.cohort.market_subjects) != ['us'] and not kr_market_retry)
                        or retry_market=='kr' and not kr_market_retry
                        or (not b2_retry_budget_bounds(per_ticker,retry_cap=cap,retry_market=retry_market)[0]
                            <= value['maximum'] <= per_ticker['maximum']+cap
                            if per_ticker else value['maximum'] != len(plan.slots)+cap)
                        or attempt != dict(attempt_id=frame['request_id'], ordinal=value['ordinal'],
                            prompt_sha256=frame['prompt_sha256'], schema_sha256=frame['schema_sha256'])):
                    raise ValueError('production_worker_timeout_attempt_authorization_drift')
                journal = plain_path(auth.parent.parent / 'invocation-ledger' / plan.cohort.run_id / 'events.jsonl')
                identity = dict(contract='model-invocation-journal-v1', plan_sha256=plan.sha256, maximum=value['maximum'])
                if per_ticker:
                    identity['b2_retry_policy']=per_ticker
                if cap:
                    identity['timeout_retry_cap']=cap
                if kr_market_retry:
                    identity['timeout_retry_market']='kr'
                state = read_invocation_journal(journal.read_bytes(), identity)
                if (state['stopped'] or state['bound'].get(slot_id) != scope
                        or state['used']-state['accepted'].keys()-state['exhausted'] != {slot_id}
                        or state['attempts'][slot_id][-1] != attempt
                        or len(state['timeouts'].get(slot_id, ())) != attempt['ordinal']-1
                        or state['physical_calls'] != value['physical_call']):
                    raise ValueError('production_worker_timeout_attempt_journal_drift')
    elif frame.get('contract') == CONTRACT and set(frame) == base:
        policy = ProductionWirePolicy()
    else:
        raise ValueError('production_model_worker_contract')
    return ProductionWireRequest(binding_from_json(frame['binding']), frame['request_id'],
        frame['prompt_sha256'], frame['schema_sha256'], policy,
        frame['slot_scope'] if dynamic else None, dynamic and ('timeout_retry_cap' in value or 'b2_retry_policy' in value))


def render_prompt(payload, stage):
    reject_test_only_production(payload)
    if set(payload) != {"prompt", "response_schema", "input"}:
        raise ValueError("production_native_payload_shape")
    if stage in {"MARKET", "CORE", "A", "B"}:
        delimiter = "\nFROZEN_CONTEXT:\n"
        if delimiter not in payload["prompt"] or json.loads(payload["prompt"].rsplit(delimiter, 1)[1]) != payload["input"]:
            raise ValueError("production_native_prompt_context_mismatch")
        return payload["prompt"].encode()
    if stage != "B2":
        raise ValueError("production_model_stage_not_authorized")
    return (payload["prompt"] + "\nFROZEN_CONTEXT:\n" + json.dumps(payload["input"], ensure_ascii=False, sort_keys=True) + "\n").encode()


class OfficialProductionModelTransport:
    def __init__(self, *, binding, runtime_root, secrets=(), worker_factory=asyncio.create_subprocess_exec,
                 execution_profile=None, call_budget=None, cohort_source_owner=None):
        self.execution_profile = sol_high(execution_profile) if execution_profile is not None else None
        if ((self.execution_profile is not None and type(call_budget) is not SolHighCallBudget)
                or (self.execution_profile is None and call_budget is not None)):
            raise ValueError('sol_high_explicit_shared_budget_required')
        self.call_budget = call_budget
        self.cohort_source_owner = cohort_source_owner
        if cohort_source_owner is not None and (call_budget is None or call_budget.plan is None):
            raise ValueError('explicit_dynamic_model_plan_required')
        self.binding = binding_from_json(binding)
        self.binding_json = binding
        self.runtime_root = Path(runtime_root).resolve()
        if any((p / ".git").exists() for p in (self.runtime_root, *self.runtime_root.parents)):
            raise ValueError("production_model_input_root_inside_repository")
        validate_binding(self.binding, str(self.binding.executable), profile=self.execution_profile)
        self.worker_factory = worker_factory
        self.secrets = tuple(s.encode() for s in secrets if isinstance(s, str) and len(s) >= 8)
        self.cycle = None
        self.counts = {}
        self.total = 0

    def bind_cycle(self, *, market, run_id):
        if self.call_budget is not None and self.call_budget.plan is not None:
            if market not in self.call_budget.plan.cohort.market_subjects or run_id != self.call_budget.plan.cohort.run_id:
                raise ValueError('model_plan_run_or_market_drift')
            self.cycle = (market, run_id)
            # Diagnostics are cycle-local; the shared budget is deliberately untouched.
            self.counts, self.total = {}, 0
            return
        if market not in {"us", "kr"} or self.cycle is not None and self.cycle[1] == run_id:
            raise ValueError("production_model_cycle_binding")
        self.cycle = (market, run_id)
        self.counts, self.total = {}, 0

    async def request(self, payload, *, model, effort, timeout, stage="B2", panel=None, slot_scope=None):
        kwargs = dict(model=model, effort=effort, timeout=timeout, stage=stage, panel=panel, slot_scope=slot_scope)
        if not getattr(self.call_budget,'retry_enabled',False):
            return await self._request_once(payload, **kwargs)
        try:
            return await self._request_once(payload, **kwargs)
        except ModelTransportError as exc:
            if getattr(exc,'confirmed_timeout',None) is None:
                raise
            if not self.call_budget.confirmed_timeout(exc.slot_id,exc.confirmed_timeout):
                raise
        try:
            return await self._request_once(payload, **kwargs, retry=True)
        except ModelTransportError as exc:
            if getattr(exc,'confirmed_timeout',None) is not None:
                if self.call_budget.confirmed_timeout(exc.slot_id,exc.confirmed_timeout):
                    raise ValueError('model_retry_second_retry_forbidden') from exc
            raise

    async def _request_once(self, payload, *, model, effort, timeout, stage, panel, slot_scope, retry=False):
        reject_test_only_production(payload)
        expected = ('gpt-5.6-sol', 'xhigh', 600) if self.execution_profile is None else (
            self.execution_profile.model, self.execution_profile.effort, self.execution_profile.timeout_seconds)
        if (model, effort, timeout) != expected or self.cycle is None:
            raise ValueError("production_model_contract_not_bound")
        validate_binding(self.binding, str(self.binding.executable), profile=self.execution_profile)
        dynamic = self.call_budget is not None and self.call_budget.plan is not None
        payload_sha256 = digest(payload)
        if dynamic:
            slot_scope = self.call_budget.resolve_scope(panel, stage, payload_sha256, slot_scope)
            if not isinstance(slot_scope, dict):
                raise ValueError('frozen_model_slot_scope_required')
        identity = (stage, slot_scope['slot_id']) if dynamic else (stage, payload_sha256)
        ordinal = self.counts.get(identity, 0) + 1
        retry_cap = getattr(self.call_budget,'timeout_retry_cap',0)
        retry_enabled = getattr(self.call_budget,'retry_enabled',False)
        if retry_enabled:
            from app.services.research_no_send_run import current_stage_timer
            if current_stage_timer() is None:
                raise ValueError('production_model_retry_requires_campaign_timer')
        maximum = self.call_budget.maximum if self.execution_profile else (90 if self.cycle[0] == "us" else 54)
        if (ordinal > (1+retry_enabled if self.execution_profile else 3) or self.total >= maximum
                or retry_enabled and ordinal != 1 + retry):
            raise ValueError("production_model_call_budget_exhausted")
        prompt, schema = render_prompt(payload, stage), encoded(payload["response_schema"])
        if any(secret in prompt or secret in schema for secret in self.secrets):
            raise ValueError("production_model_input_secret_detected")
        policy = SolHighWirePolicy() if self.execution_profile else ProductionWirePolicy()
        contract = CONTRACT_V2 if self.execution_profile else CONTRACT
        path = self.runtime_root / (self.cycle[1] + "-" + uuid.uuid4().hex)
        from app.services.research_artifact_budget import (
            ArtifactCapacityError, active_budget, CLI_WORK_ALLOWANCE, MODEL_RESULT_ALLOWANCE,
        )
        artifacts = active_budget()
        if artifacts is not None:
            artifacts.declare_cli_context(path,getattr(self.binding,'auth_source',None),
                qualified_cli=self.binding.executable if sys.platform=='darwin'
                and type(self.binding) is CurrentOfficialCodexBinding else None)
            artifacts.check(path=path, added_work=len(prompt)+len(schema)+CLI_WORK_ALLOWANCE+MODEL_RESULT_ALLOWANCE,
                added_result=MODEL_RESULT_ALLOWANCE, role='scratch')
        if self.execution_profile:
            if len(prompt) > 384 * 1024:
                raise ValueError('sol_high_input_exceeds_384KiB')
            if dynamic:
                self.call_budget.plan.cohort.verify_source_owner(self.cohort_source_owner)
                if not isinstance(slot_scope, dict) or slot_scope.get('market') != self.cycle[0]:
                    raise ValueError('model_slot_market_cycle_drift')
                contract = CONTRACT_V3
            from app.services.research_no_send_run import current_stage_timer
            if (timer := current_stage_timer()) is not None:
                timer.check()
            attempt = dict(attempt_id=path.name, ordinal=ordinal, prompt_sha256=sha256_bytes(prompt),
                schema_sha256=sha256_bytes(schema)) if retry_enabled else None
            extra = dict(attempt=attempt) if attempt is not None else {}
            physical_call = self.call_budget.consume(panel, stage, payload_sha256, slot_scope=slot_scope, **extra)
        else:
            timer = None
            physical_call = self.total + 1
        self.counts[identity], self.total = ordinal, self.total + 1
        inputs = path / "approved-input"
        inputs.mkdir(parents=True, exist_ok=False, mode=0o700)
        durable_bytes(inputs / "prompt.txt", prompt, exclusive=True)
        durable_bytes(inputs / "provider-wire-schema.json", schema, exclusive=True)
        frame = dict(contract=contract, directory=str(path), binding=self.binding_json,
            request_id=path.name, prompt_sha256=sha256_bytes(prompt), schema_sha256=sha256_bytes(schema))
        authorization = dict(contract=contract,
            purpose=policy.purpose, run_id=self.cycle[1], market=self.cycle[0], stage=stage,
            payload_sha256=payload_sha256, ordinal=ordinal, physical_call=physical_call, maximum=maximum,
            model=model, effort=effort, timeout=timeout, semantic_retry_allowed=False,
            prompt_sha256=frame["prompt_sha256"], schema_sha256=frame["schema_sha256"])
        if self.execution_profile:
            authorization.update(request_id=frame['request_id'], panel=panel, execution_policy=asdict(policy))
        if dynamic:
            authorization.update(slot_scope=slot_scope, execution_plan_sha256=self.call_budget.plan.sha256,
                planned_slots=len(self.call_budget.slots), remaining_invocations=self.call_budget.maximum-physical_call)
            if self.call_budget.inherited_market_slot is not None:
                authorization['inherited_market_slot'] = self.call_budget.inherited_market_slot
            if retry_cap:
                authorization.update(timeout_retry_cap=retry_cap, attempt=attempt)
                if getattr(self.call_budget,'retry_market','us')=='kr':
                    authorization['timeout_retry_market']='kr'
            if getattr(self.call_budget,'b2_retry_policy',None):
                authorization.update(b2_retry_policy=self.call_budget.b2_retry_policy, attempt=attempt)
                if getattr(self.call_budget,'retry_market','us')=='kr':
                    authorization['timeout_retry_market']='kr'
        durable_json(path / "production-authorization.json", authorization, exclusive=True)
        if self.execution_profile:
            frame.update(execution_policy=asdict(policy), authorization_sha256=sha256_bytes(
                (path / 'production-authorization.json').read_bytes()))
        if dynamic:
            frame.update(execution_plan=self.call_budget.plan.to_dict(), slot_scope=slot_scope)
        env = {k: os.environ[k] for k in ("PATH", "HOME", "CODEX_HOME", "TMPDIR", "LANG") if k in os.environ}
        from app.services.codex_runtime_binding import parent_environment
        if type(self.binding) is CurrentOfficialCodexBinding:
            env=parent_environment(self.binding,env)
        env.update(PYTHONPATH=str(ROOT), PYTHONDONTWRITEBYTECODE="1", THESIS_MONITOR_ENV_FILE="",
            DATABASE_URL="sqlite://", NOTIFICATION_DRY_RUN="true", ENABLE_LIVE_PROVIDERS="false",
            UNIFIED_SNAPSHOT_ENABLED="false")
        if artifacts is not None:
            env['THESIS_MONITOR_BOUNDED_RESEARCH_RECEIPT'] = '1'
        # The CLI keeps its own exact timeout; the parent only bounds worker setup and cleanup.
        worker_timeout = timeout
        if timer is not None:
            self.call_budget.run_ledger.worker_binding()
            timer.switch('worker')
            worker_timeout = timeout+timer.deadline['overhead_seconds']
        process = await self.worker_factory(sys.executable, "-B", "-m", "app.jobs.production_model_worker",
            cwd=ROOT, env=env, start_new_session=True, stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        try:
            if artifacts is None:
                await asyncio.wait_for(process.communicate(encoded(frame)), worker_timeout)
            else:
                async def communicate_and_measure():
                    task = asyncio.create_task(process.communicate(encoded(frame)))
                    try:
                        while not (await asyncio.wait({task}, timeout=5))[0]:
                            artifacts.check(path=path)
                        return await task
                    finally:
                        if not task.done():
                            task.cancel()
                            await asyncio.gather(task, return_exceptions=True)

                await asyncio.wait_for(communicate_and_measure(), worker_timeout)
        except BaseException as exc:
            if process.returncode is None:
                os.killpg(process.pid, signal.SIGKILL)
            await process.wait()
            try:
                durable_json(path / "parent-exit.json", dict(status="INTERRUPTED", child_reaped=True), exclusive=True)
            except ArtifactCapacityError:
                if not isinstance(exc, ArtifactCapacityError):
                    raise
            raise
        raw_path = path / "raw-output.json"
        raw = raw_path.read_bytes() if raw_path.is_file() and not raw_path.is_symlink() else b""
        durable_json(path / "parent-exit.json", dict(status="WORKER_EXITED", child_reaped=True,
            returncode=process.returncode, raw_sha256=sha256_bytes(raw), raw_bytes=len(raw)), exclusive=True)
        if timer is not None:
            timer.switch('local')
        if process.returncode == PREFLIGHT_REJECT_EXIT:
            raise ValueError("production_official_transport_boundary_reject")
        if process.returncode != 0:
            raise ModelTransportError("WORKER_NONZERO")
        receipt_path = path / "transport-receipt.json"
        receipt = json.loads(receipt_path.read_bytes()) if receipt_path.exists() else {"error_code": "WORKER_FAILED"}
        if receipt.get("status") != "PASS":
            code = receipt.get("error_code")
            if self.execution_profile and code in {'MODEL_ENTITLEMENT_OR_QUOTA_UNAVAILABLE',
                    'MODEL_AUTHENTICATION_FAILED','MODEL_WORKSPACE_MISMATCH'}:
                error=ModelTransportError(code)
                error.diagnosis=receipt.get('diagnosis')
                error.cli_returncode=receipt.get('cli_returncode')
                error.worker_returncode=process.returncode
                raise error
            if code in {"TRANSPORT_TIMEOUT", "PROCESS_NONZERO", "PROCESS_START_FAILED", "WORKER_FAILED"}:
                error=ModelTransportError(code)
                error.diagnosis=receipt.get('diagnosis')
                error.cli_returncode=receipt.get('cli_returncode')
                error.worker_returncode=process.returncode
                if retry_enabled and code == 'TRANSPORT_TIMEOUT':
                    from app.services.model_timeout_retry import confirmed_timeout

                    error.confirmed_timeout = confirmed_timeout(path, worker_pid=process.pid,
                        worker_returncode=process.returncode, receipt=receipt,
                        prompt_sha256=frame['prompt_sha256'], schema_sha256=frame['schema_sha256'])
                    if error.confirmed_timeout is None:
                        raise ModelTransportError('RECONCILIATION_REQUIRED') from error
                    error.slot_id = slot_scope['slot_id']
                raise error
            if code not in {"FINAL_OUTPUT_EMPTY", "FINAL_OUTPUT_MALFORMED"}:
                raise ValueError("production_official_transport_boundary_reject")
        if self.execution_profile:
            from app.services.official_codex_shadow_transport_service import command_prefix
            proof = receipt.get('transport', {})
            expected_command = [str(self.binding.executable), *command_prefix(self.execution_profile),
                '--output-schema', str(inputs / 'provider-wire-schema.json'), '-o', str(raw_path), '-']
            if (len(raw) > 128 * 1024 or proof.get('execution_policy') != asdict(policy)
                    or proof.get('command') != expected_command
                    or proof.get('request_id') != frame['request_id']
                    or proof.get('qualification_sha256') != self.binding.qualification_sha256
                    or proof.get('prompt_sha256') != frame['prompt_sha256']
                    or proof.get('schema_sha256') != frame['schema_sha256']):
                raise ValueError('sol_high_worker_receipt_drift_or_output_limit')
            if dynamic and proof.get('model_plan_scope') != slot_scope:
                raise ValueError('sol_high_worker_slot_receipt_drift')
        if artifacts is not None:
            artifacts.check(path=path)
        return raw
