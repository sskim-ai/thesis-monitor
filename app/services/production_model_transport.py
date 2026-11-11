"""Separate production authorization over the qualified official byte executor."""
import asyncio
from dataclasses import asdict, dataclass
import json
import os
from pathlib import Path
import signal
import sys
import uuid

from app.services.official_codex_shadow_transport_service import OfficialCodexBinding, validate_binding
from app.services.official_transport_input_preflight import PREFLIGHT_REJECT_EXIT
from app.services.production_b2_execution import ModelTransportError
from app.services.fixture_context_authority import reject_test_only_production
from app.services.unified_run_artifacts import durable_bytes, durable_json, sha256_bytes
from app.services.unified_snapshot_contract import digest, encoded
from app.services.production_model_profile import CONTRACT_V2, SolHighWirePolicy, SolHighCallBudget, sol_high
from app.services.vnext_execution_profile import SOL_HIGH_V1

CONTRACT = "official-codex-production-transport-v1"
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


def request_profile(request):
    request.execution_policy.validate()
    if type(request.execution_policy) is SolHighWirePolicy:
        return SOL_HIGH_V1
    if type(request.execution_policy) is not ProductionWirePolicy:
        raise ValueError('production_wire_policy_type')
    return None


def request_from_frame(frame):
    base = {'contract', 'directory', 'binding', 'request_id', 'prompt_sha256', 'schema_sha256'}
    if frame.get('contract') == CONTRACT_V2 and set(frame) == base | {'execution_policy', 'authorization_sha256'}:
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
    elif frame.get('contract') == CONTRACT and set(frame) == base:
        policy = ProductionWirePolicy()
    else:
        raise ValueError('production_model_worker_contract')
    return ProductionWireRequest(binding_from_json(frame['binding']), frame['request_id'],
        frame['prompt_sha256'], frame['schema_sha256'], policy)


def binding_from_json(value):
    raw = dict(value)
    for name in ("executable", "qualification_path"):
        if raw.get(name) is not None:
            raw[name] = Path(raw[name])
    return OfficialCodexBinding(**raw)


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
                 execution_profile=None, call_budget=None):
        self.execution_profile = sol_high(execution_profile) if execution_profile is not None else None
        if ((self.execution_profile is not None and type(call_budget) is not SolHighCallBudget)
                or (self.execution_profile is None and call_budget is not None)):
            raise ValueError('sol_high_explicit_shared_budget_required')
        self.call_budget = call_budget
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
        if market not in {"us", "kr"} or self.cycle is not None and self.cycle[1] == run_id:
            raise ValueError("production_model_cycle_binding")
        self.cycle = (market, run_id)
        self.counts, self.total = {}, 0

    async def request(self, payload, *, model, effort, timeout, stage="B2", panel=None):
        reject_test_only_production(payload)
        expected = ('gpt-5.6-sol', 'xhigh', 600) if self.execution_profile is None else (
            self.execution_profile.model, self.execution_profile.effort, self.execution_profile.timeout_seconds)
        if (model, effort, timeout) != expected or self.cycle is None:
            raise ValueError("production_model_contract_not_bound")
        validate_binding(self.binding, str(self.binding.executable), profile=self.execution_profile)
        identity = (stage, digest(payload))
        ordinal = self.counts.get(identity, 0) + 1
        maximum = 90 if self.cycle[0] == "us" else 54
        if ordinal > (1 if self.execution_profile else 3) or self.total >= maximum:
            raise ValueError("production_model_call_budget_exhausted")
        prompt, schema = render_prompt(payload, stage), encoded(payload["response_schema"])
        if any(secret in prompt or secret in schema for secret in self.secrets):
            raise ValueError("production_model_input_secret_detected")
        policy = SolHighWirePolicy() if self.execution_profile else ProductionWirePolicy()
        contract = CONTRACT_V2 if self.execution_profile else CONTRACT
        if self.execution_profile:
            if len(prompt) > 384 * 1024:
                raise ValueError('sol_high_input_exceeds_384KiB')
            physical_call = self.call_budget.consume(panel, stage, identity[1])
            maximum = 6
        else:
            physical_call = self.total + 1
        self.counts[identity], self.total = ordinal, self.total + 1
        path = self.runtime_root / (self.cycle[1] + "-" + uuid.uuid4().hex)
        inputs = path / "approved-input"
        inputs.mkdir(parents=True, exist_ok=False, mode=0o700)
        durable_bytes(inputs / "prompt.txt", prompt, exclusive=True)
        durable_bytes(inputs / "provider-wire-schema.json", schema, exclusive=True)
        frame = dict(contract=contract, directory=str(path), binding=self.binding_json,
            request_id=path.name, prompt_sha256=sha256_bytes(prompt), schema_sha256=sha256_bytes(schema))
        authorization = dict(contract=contract,
            purpose=policy.purpose, run_id=self.cycle[1], market=self.cycle[0], stage=stage,
            payload_sha256=identity[1], ordinal=ordinal, physical_call=physical_call, maximum=maximum,
            model=model, effort=effort, timeout=timeout, semantic_retry_allowed=False,
            prompt_sha256=frame["prompt_sha256"], schema_sha256=frame["schema_sha256"])
        if self.execution_profile:
            authorization.update(request_id=frame['request_id'], panel=panel, execution_policy=asdict(policy))
        durable_json(path / "production-authorization.json", authorization, exclusive=True)
        if self.execution_profile:
            frame.update(execution_policy=asdict(policy), authorization_sha256=sha256_bytes(
                (path / 'production-authorization.json').read_bytes()))
        env = {k: os.environ[k] for k in ("PATH", "HOME", "CODEX_HOME", "TMPDIR", "LANG") if k in os.environ}
        env.update(PYTHONPATH=str(ROOT), PYTHONDONTWRITEBYTECODE="1", THESIS_MONITOR_ENV_FILE="",
            DATABASE_URL="sqlite://", NOTIFICATION_DRY_RUN="true", ENABLE_LIVE_PROVIDERS="false",
            UNIFIED_SNAPSHOT_ENABLED="false")
        process = await self.worker_factory(sys.executable, "-B", "-m", "app.jobs.production_model_worker",
            cwd=ROOT, env=env, start_new_session=True, stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        try:
            await asyncio.wait_for(process.communicate(encoded(frame)), timeout)
        except BaseException:
            if process.returncode is None:
                os.killpg(process.pid, signal.SIGKILL)
            await process.wait()
            durable_json(path / "parent-exit.json", dict(status="INTERRUPTED", child_reaped=True), exclusive=True)
            raise
        raw_path = path / "raw-output.json"
        raw = raw_path.read_bytes() if raw_path.is_file() and not raw_path.is_symlink() else b""
        durable_json(path / "parent-exit.json", dict(status="WORKER_EXITED", child_reaped=True,
            returncode=process.returncode, raw_sha256=sha256_bytes(raw), raw_bytes=len(raw)), exclusive=True)
        if process.returncode == PREFLIGHT_REJECT_EXIT:
            raise ValueError("production_official_transport_boundary_reject")
        if process.returncode != 0:
            raise ModelTransportError("WORKER_NONZERO")
        receipt_path = path / "transport-receipt.json"
        receipt = json.loads(receipt_path.read_bytes()) if receipt_path.exists() else {"error_code": "WORKER_FAILED"}
        if receipt.get("status") != "PASS":
            code = receipt.get("error_code")
            if self.execution_profile and code == 'MODEL_ENTITLEMENT_OR_QUOTA_UNAVAILABLE':
                raise ModelTransportError(code)
            if code in {"TRANSPORT_TIMEOUT", "PROCESS_NONZERO", "PROCESS_START_FAILED", "WORKER_FAILED"}:
                raise ModelTransportError(code)
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
        return raw
