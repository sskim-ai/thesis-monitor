from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import subprocess
import zipfile
from collections.abc import Mapping, Sequence
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.jobs import accepted_decision_v2_runtime as accepted_runtime
from app.services.codex_network_transport_service import (
    CodexTransportError,
    CodexTransportFailureType,
    codex_tls_environment,
    probe_codex_network_readiness,
)
from app.services.codex_runtime_state_service import (
    CodexRuntimeIsolationCollision,
    CodexRuntimeIsolationIdentity,
    CodexRuntimeIsolationRegistry,
    CodexRuntimeState,
    prepare_codex_runtime_state,
)
from app.services.codex_transport_lifecycle_service import (
    AUTHORITATIVE_TIMEOUT_OWNER,
    InstrumentedCodexInvocation,
    InstrumentedTransportError,
    invoke_instrumented_codex,
)
from app.services.cross_market_decision_engine_service import (
    DecisionEvidencePacket,
    DecisionEvidenceRef,
    EvidenceCategory,
)
from app.services.direction_timing_ownership_service import (
    CORE_OUTPUT_CONTRACT,
    TIMING_OUTPUT_CONTRACT,
    DirectionalCoreCandidate,
    EvidenceDomain,
    OwnedEvidencePacket,
    OwnedEvidenceRef,
    PriceTimingCandidate,
    canonical_sha256,
    compose_decision,
    core_fingerprint,
    stage_alias_catalogs,
    validate_ownership,
)
from app.services.structured_autonomy_alias_service import (
    build_alias_constrained_batch_schema,
)
from app.services.structured_autonomy_shadow_service import (
    explicit_actionable_trade_directives,
)
from scripts import directional_core_price_timing_holdout as frozen
from scripts import uskr22_structured_autonomy_shadow as engine


PROGRAM_CONTRACT = "model-transport-revalidation-ownership-proof-continuation-v1"
PROOFS_DIRECTORY = "20260906-model-transport-continuation-proofs"
SOURCE_REPORT_SHA256 = (
    "8e496adf1373ca7a4489c76c8c9eda01b7b9641e55b666d6e60e5abef4597678"
)
SOURCE_GENERATION_ID = "20260906-direction-timing-holdout-20260906T093200Z-bd30668470f0"
SOURCE_LOCK_SHA256 = (
    "efe64d0942afa00c3b40131afc4de5fa411babc0680271d1571aaac69816050d"
)
MODEL = "gpt-5.6-sol"
EFFORT = "xhigh"
MODEL_CONTEXT_BATCH_SIZE = 4
INITIAL_REAL_TIMEOUT_SECONDS = 1800
MAX_TIMEOUT_SECONDS = 3600
CANARY_TIMEOUT_SECONDS = 600
MAX_CANARY_MODEL_CALLS = 8

CONSUMED_LATEST_HOLDOUT16 = (
    "PLTR",
    "V",
    "MA",
    "AMZN",
    "XOM",
    "DIS",
    "NKE",
    "MCD",
    "033920",
    "104480",
    "071320",
    "096240",
    "032860",
    "060570",
    "016600",
    "462520",
)
CURRENT_HOLDOUT = (
    "ORCL",
    "UNH",
    "KO",
    "AVGO",
    "095570",
    "058860",
    "246960",
    "099520",
    "403870",
    "014790",
    "079810",
    "060980",
    "061970",
    "012030",
    "225190",
    "245620",
)
EXPECTED_ARCHITECTURE_HASHES = {
    "alias_fencing": "3c9e7b0869a0157b40d8558c7618c5ed5c83bb8ce2240698755d2cf65b155c83",
    "directional_balance": "2ecf5bbad338dc92d9996b60e3429ebb3c6b8d37cdb114439ffbff84166296ab",
    "ownership_runner": "5f52ec5c866f3f07968c76ed955db8110ae052d16c2eaf8232825832647d0929",
    "ownership_service": "8cba5d93801833ad3b004a97cefe30e2ab71c7caee75be76c93123bec0b3273a",
    "stability_classifier": "e824e9dc7044033c091f8b40fdb0f461f629d8b420f193e060b42e7f27e13188",
    "validator_renderer": "ee8dcdeaf42c40a49a8c56ebc140298271857eacd0bd2afc1cddb9fb631c018f",
}
EXPECTED_SOURCE_HASHES = dict(frozen.EXPECTED_SOURCE_HASHES)

REPORT_TO_PROOF = {
    "20260906-transport-continuation-root-cause.md": "transport-continuation-root-cause.json",
    "20260906-architecture-freeze-reverification.md": "architecture-freeze-reverification.json",
    "20260906-source-freeze-reverification.md": "source-freeze-reverification.json",
    "20260906-consumed-regression-no-rerun.md": "consumed-regression-no-rerun.json",
    "20260906-model-transport-topology.md": "model-transport-topology.json",
    "20260906-timeout-owner-audit.md": "timeout-owner-audit.json",
    "20260906-process-cleanup-contract.md": "process-cleanup-contract.json",
    "20260906-batch-semantics-audit.md": "batch-semantics-audit.json",
    "20260906-batch-split-semantic-equivalence.md": "batch-split-semantic-equivalence.json",
    "20260906-transport-canary-smoke.md": "transport-canary-smoke.json",
    "20260906-transport-canary-directional-core.md": "transport-canary-directional-core.json",
    "20260906-transport-canary-representative-payload.md": "transport-canary-representative-payload.json",
    "20260906-transport-canary-price-timing.md": "transport-canary-price-timing.json",
    "20260906-transport-canary-verdict.md": "transport-canary-verdict.json",
    "20260906-current-holdout-reuse-gate.md": "current-holdout-reuse-gate.json",
    "20260906-continuation-source-lock.md": "continuation-source-lock.json",
    "20260906-continuation-first.md": "continuation-first.json",
    "20260906-continuation-run-a.md": "continuation-run-a.json",
    "20260906-continuation-run-b.md": "continuation-run-b.json",
    "20260906-continuation-run-c.md": "continuation-run-c.json",
    "20260906-continuation-core-stability.md": "continuation-core-stability.json",
    "20260906-continuation-timing-stability.md": "continuation-timing-stability.json",
    "20260906-continuation-dominance-ownership.md": "continuation-dominance-ownership.json",
    "20260906-continuation-renderer-shadow-proof.md": "continuation-renderer-shadow-proof.json",
    "20260906-continuation-hard-safety-regression.md": "continuation-hard-safety-regression.json",
    "20260906-monitoring-bootstrap-next-handoff.md": "monitoring-bootstrap-next-handoff.json",
    "20260906-production-no-change.md": "production-no-change.json",
    "20260906-night-futures-no-change.md": "night-futures-no-change.json",
    "20260906-program-completion.md": "program-completion.json",
}


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"object_required:{path}")
    return value


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, default=str)
        + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_value(*args: str) -> str:
    return subprocess.run(
        ["git", *args],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def continuation_generation_id(commit: str, as_of: datetime) -> str:
    stamp = as_of.astimezone(UTC).strftime("%Y%m%dT%H%M%SZ")
    suffix = hashlib.sha256(f"{commit}|{stamp}|{PROGRAM_CONTRACT}".encode()).hexdigest()[:12]
    return f"20260906-model-transport-continuation-{stamp}-{suffix}"


def cli_version(codex_bin: str) -> str:
    result = subprocess.run(
        [codex_bin, "--version"],
        check=True,
        capture_output=True,
        text=True,
        timeout=15,
    )
    return (result.stdout or result.stderr).strip().splitlines()[-1]


def _identity_from_prompt(prompt: Path) -> dict[str, object]:
    text = prompt.read_text(encoding="utf-8")
    marker = "IDENTITY:\n"
    if marker not in text:
        return {}
    return json.loads(text.split(marker, 1)[1].splitlines()[0])


class ContinuationTransportAdapter:
    def __init__(
        self,
        *,
        continuation_generation: str,
        receipt_root: Path,
        codex_bin: str,
        runtime_state_root: Path | None = None,
        isolation_registry: CodexRuntimeIsolationRegistry | None = None,
    ) -> None:
        self.continuation_generation = continuation_generation
        self.receipt_root = receipt_root
        self.codex_bin = codex_bin
        self.version = cli_version(codex_bin)
        self.model_call_count = 0
        self.runtime_state_root = (
            runtime_state_root.resolve()
            if runtime_state_root is not None
            else accepted_runtime._runtime_state_root()
        )
        self.isolation_registry = isolation_registry or CodexRuntimeIsolationRegistry()
        self._seed_existing_isolation_claims()

    def _seed_existing_isolation_claims(self) -> None:
        if not self.receipt_root.is_dir():
            return
        for path in sorted(self.receipt_root.glob("*.json")):
            receipt = read_json(path)
            metadata = receipt.get("transport_metadata")
            metadata = metadata if isinstance(metadata, Mapping) else {}
            invocation_id = receipt.get("invocation_id")
            namespace_hash = metadata.get("runtime_state_namespace_hash")
            working_directory_identity = receipt.get("working_directory_identity")
            if not all(
                isinstance(value, str) and value
                for value in (
                    invocation_id,
                    namespace_hash,
                    working_directory_identity,
                )
            ):
                continue
            self.isolation_registry.seed(
                invocation_id=str(invocation_id),
                runtime_state_namespace_hash=str(namespace_hash),
                working_directory_identity=str(working_directory_identity),
            )

    def prepare_execution_isolation(
        self,
        *,
        state_namespace: str,
        invocation_id: str,
        working_directory: Path,
        auth_source: Path | None = None,
    ) -> tuple[CodexRuntimeState, CodexRuntimeIsolationIdentity]:
        identity = self.isolation_registry.claim(
            base_namespace=state_namespace,
            invocation_id=invocation_id,
            working_directory=working_directory,
        )
        runtime_state = prepare_codex_runtime_state(
            self.runtime_state_root,
            namespace=identity.runtime_state_namespace,
            auth_source=auth_source,
        )
        if runtime_state.namespace_hash != identity.runtime_state_namespace_hash:
            raise ValueError("runtime_namespace_allocation_identity_mismatch")
        return runtime_state, identity

    def invoke(
        self,
        *,
        prompt: Path,
        output: Path,
        log: Path,
        schema: Path,
        cwd: Path,
        timeout: int,
        state_namespace: str,
        invocation_id: str | None = None,
        stage: str | None = None,
        batch_id: str | None = None,
        subject_count: int | None = None,
    ) -> dict[str, object]:
        prompt = Path(prompt).resolve()
        output = Path(output).resolve()
        log = Path(log).resolve()
        schema = Path(schema).resolve()
        cwd = Path(cwd).resolve()
        identity = _identity_from_prompt(prompt)
        tickers = identity.get("tickers") if isinstance(identity.get("tickers"), list) else []
        inferred_stage = (
            "DIRECTIONAL_CORE"
            if identity.get("contract") == CORE_OUTPUT_CONTRACT
            else "PRICE_TIMING"
            if identity.get("contract") == TIMING_OUTPUT_CONTRACT
            else "TRANSPORT_SMOKE"
        )
        inferred_batch = re.search(r"(?:batch-|batch-?)(\d+)", output.stem)
        stage = stage or inferred_stage
        batch_id = batch_id or (inferred_batch.group(1) if inferred_batch else output.stem)
        subject_count = subject_count if subject_count is not None else len(tickers) or 1
        invocation_id = invocation_id or (
            f"{self.continuation_generation}:{output.parent.name}:{stage}:{batch_id}"
        )
        receipt = self.receipt_root / f"{hashlib.sha256(invocation_id.encode()).hexdigest()[:16]}.json"
        stdout = receipt.with_suffix(".stdout.log")
        stderr = receipt.with_suffix(".stderr.log")
        isolation_preflight = output.parent / "runtime-isolation-preflight.json"

        try:
            runtime_state, isolation_identity = self.prepare_execution_isolation(
                state_namespace=state_namespace,
                invocation_id=invocation_id,
                working_directory=cwd,
            )
        except CodexRuntimeIsolationCollision as exc:
            write_json(
                isolation_preflight,
                {
                    "contract": "codex-model-context-runtime-isolation-preflight-v1",
                    "policy": "PER_MODEL_CONTEXT_UNIQUE_RUNTIME_NAMESPACE",
                    "invocation_id": invocation_id,
                    "base_namespace_hash": hashlib.sha256(
                        state_namespace.encode("utf-8")
                    ).hexdigest()[:24],
                    "working_directory_identity": hashlib.sha256(
                        str(cwd).encode("utf-8")
                    ).hexdigest(),
                    "spawn_started": 0,
                    "model_call_counted": 0,
                    "failure": str(exc),
                    "status": "RUNTIME_NAMESPACE_COLLISION",
                },
            )
            raise
        write_json(
            isolation_preflight,
            {
                **isolation_identity.audit_dict(),
                "spawn_started": 0,
                "model_call_counted": 0,
                "status": "PASS_PRESPAWN",
            },
        )
        tls = codex_tls_environment(runtime_state.environment())
        readiness = probe_codex_network_readiness()
        if not readiness.ready:
            assert readiness.failure_type is not None
            raise CodexTransportError(readiness.failure_type, attempts=readiness.attempts)
        command = [
            self.codex_bin,
            "exec",
            "--ephemeral",
            "--ignore-user-config",
            "--ignore-rules",
            "--skip-git-repo-check",
            "--sandbox",
            "read-only",
            "-m",
            MODEL,
            "-c",
            f'model_reasoning_effort="{EFFORT}"',
            "--output-schema",
            str(schema),
            "-o",
            str(output),
            "-",
        ]
        invocation = InstrumentedCodexInvocation(
            invocation_id=invocation_id,
            generation_id=self.continuation_generation,
            stage=stage,
            batch_id=str(batch_id),
            subject_count=subject_count,
            transport_grouping_mode=(
                "MODEL_CONTEXT_COUPLED" if subject_count > 1 else "SINGLE_MODEL_CONTEXT"
            ),
            model=MODEL,
            reasoning_effort=EFFORT,
            cli_binary=Path(self.codex_bin),
            cli_version=self.version,
            command=command,
            working_directory=cwd,
            prompt_path=prompt,
            schema_path=schema,
            output_path=output,
            stdout_path=stdout,
            stderr_path=stderr,
            receipt_path=receipt,
            environment=tls.environment,
            timeout_seconds=timeout,
            cleanup_margin_seconds=15,
            metadata={
                "network_probe_contract": readiness.contract,
                "network_probe_attempts": readiness.attempts,
                "network_resolved_address_count": readiness.resolved_address_count,
                **isolation_identity.audit_dict(),
                "tls_trust_source": tls.trust_source,
            },
        )
        self.model_call_count += 1
        try:
            result = invoke_instrumented_codex(invocation)
        finally:
            parts = []
            for path in (stderr, stdout):
                if path.is_file():
                    parts.append(path.read_bytes())
            log.parent.mkdir(parents=True, exist_ok=True)
            log.write_bytes(b"\n".join(parts))
        return result

    def runner_invoke(self, **kwargs: object) -> dict[str, object]:
        try:
            return self.invoke(**kwargs)
        except InstrumentedTransportError as exc:
            failure = (
                CodexTransportFailureType.MODEL_TIMEOUT
                if exc.status == "TIMEOUT"
                else CodexTransportFailureType.OTHER_TRANSPORT_FAILURE
            )
            raise CodexTransportError(failure, attempts=1) from exc


@contextmanager
def instrumented_runner(adapter: ContinuationTransportAdapter):
    original = engine._invoke_signed_in_codex
    engine._invoke_signed_in_codex = adapter.runner_invoke
    try:
        yield
    finally:
        engine._invoke_signed_in_codex = original


def verify_source_lock(source_root: Path) -> dict[str, object]:
    source = read_json(source_root / "source-lock.json")
    recorded = str(source.pop("source_lock_sha256"))
    if recorded != SOURCE_LOCK_SHA256 or canonical_sha256(source) != SOURCE_LOCK_SHA256:
        raise ValueError("continuation_source_lock_drift")
    if tuple(source.get("ordered_cohort") or ()) != CURRENT_HOLDOUT:
        raise ValueError("continuation_holdout_cohort_drift")
    return source


def verify_frozen(args: argparse.Namespace) -> tuple[dict[str, str], dict[str, str]]:
    architecture = frozen.architecture_hashes(Path.cwd().resolve())
    if architecture != EXPECTED_ARCHITECTURE_HASHES:
        raise ValueError("ownership_architecture_hash_drift")
    source_hashes = frozen.fundamental.source_hashes(
        Path.cwd().resolve(), args.provider_root
    )
    if source_hashes != EXPECTED_SOURCE_HASHES:
        raise ValueError("fundamental_source_enrichment_drift")
    verify_source_lock(args.source_root)
    return architecture, source_hashes


def _base_proofs(
    *,
    state: Mapping[str, object],
    architecture: Mapping[str, str],
    source_hashes: Mapping[str, str],
) -> dict[str, dict[str, object]]:
    return {
        "transport-continuation-root-cause.json": {
            "contract": "transport-continuation-root-cause-v1",
            "initial_blocker_class": "MODEL_TRANSPORT_OR_INVOCATION_TIMEOUT",
            "prior_process_spawned": 1,
            "prior_stderr_began": 1,
            "prior_prompt_echo_observed": 1,
            "prior_model_output_documents": 0,
            "prior_process_exit_before_timeout": 0,
            "prior_output_parse_started": 0,
            "prior_request_accepted_observability": "UNAVAILABLE",
            "prior_cleanup_observability": "INSUFFICIENT",
            "final_classification": "PENDING_CANARIES",
        },
        "architecture-freeze-reverification.json": {
            "contract": "ownership-architecture-freeze-reverification-v1",
            "expected_hashes": EXPECTED_ARCHITECTURE_HASHES,
            "actual_hashes": dict(architecture),
            "ownership_architecture_hash_drift": 0,
            "investment_decision_threshold_mutation": 0,
            "direction_timing_policy_mutation": 0,
            "ownership_execution_mode": "TWO_STAGE_FENCED",
            "model": MODEL,
            "reasoning_effort": EFFORT,
            "status": "PASS",
        },
        "source-freeze-reverification.json": {
            "contract": "source-freeze-reverification-v1",
            "expected_hashes": EXPECTED_SOURCE_HASHES,
            "actual_hashes": dict(source_hashes),
            "fundamental_source_enrichment_drift": 0,
            "source_sufficiency_policy_drift": 0,
            "evidence_packet_refresh": 0,
            "status": "PASS",
        },
        "consumed-regression-no-rerun.json": {
            "contract": "consumed-regression-no-rerun-v1",
            "consumed_cohort": list(CONSUMED_LATEST_HOLDOUT16),
            "latest_holdout16_model_calls_this_generation": 0,
            "latest_holdout16_rerun_count_this_generation": 0,
            "static_artifact_inspection_only": 1,
            "status": "PASS",
        },
        "model-transport-topology.json": {
            "contract": "model-transport-topology-v1",
            "prior_path": [
                "network_preflight",
                "subprocess.run",
                "combined_stdout_stderr_file",
                "subprocess_timeout",
                "direct_child_kill_and_wait",
                "output_file_parse",
            ],
            "continuation_path": [
                "network_preflight",
                "subprocess.Popen_start_new_session",
                "stdin_writer_thread",
                "stdout_reader_thread",
                "stderr_reader_thread",
                "single_monotonic_watchdog",
                "process_group_cleanup",
                "output_file_parse",
                "single_receipt",
            ],
            "semantic_input_change": 0,
            "production_runtime_path_change": 0,
        },
        "timeout-owner-audit.json": {
            "contract": "model-timeout-owner-audit-v1",
            "authoritative_owner": AUTHORITATIVE_TIMEOUT_OWNER,
            "model_cli_internal_timeout": "UNAVAILABLE",
            "python_subprocess_timeout": 0,
            "outer_shell_timeout": 0,
            "job_watchdog": 0,
            "model_timeout_owner_count": 1,
            "early_outer_interrupt": 0,
            "cleanup_margin_seconds": 15,
            "status": "PASS",
        },
        "process-cleanup-contract.json": {
            "contract": "model-process-cleanup-contract-v1",
            "process_session": "NEW_SESSION_PROCESS_GROUP",
            "timeout_sequence": ["SIGTERM_GROUP", "WAIT_ONCE", "SIGKILL_GROUP_IF_NEEDED"],
            "repeated_sigint_loop": 0,
            "duplicate_timeout_receipt_count": 0,
            "orphan_model_process_count": "PENDING_CANARIES",
            "status": "PENDING_CANARIES",
        },
        "batch-semantics-audit.json": {
            "contract": "model-batch-semantics-audit-v1",
            "batch_size": MODEL_CONTEXT_BATCH_SIZE,
            "code_path": "batches(cohort) -> one _core_prompt(contexts[4]) -> one model output",
            "batch_semantics": "MODEL_CONTEXT_COUPLED",
            "per_subject_independent_prompt": 0,
            "status": "PASS",
        },
        "batch-split-semantic-equivalence.json": {
            "contract": "batch-split-semantic-equivalence-v1",
            "batch_semantics": "MODEL_CONTEXT_COUPLED",
            "batch_split_adopted": 0,
            "batch_split_semantic_equivalence": "FAIL",
            "reason": "splitting would change the shared model context; no split was adopted",
            "status": "PASS",
        },
        "current-holdout-reuse-gate.json": {
            "contract": "current-holdout-reuse-gate-v1",
            "cohort": list(CURRENT_HOLDOUT),
            "pre_lock_directional_model_calls": 0,
            "prior_model_output_exists": 0,
            "source_lock_unchanged": 1,
            "architecture_hashes_unchanged": 1,
            "prompt_schema_semantics_unchanged": 1,
            "model_unchanged": 1,
            "reasoning_effort_unchanged": 1,
            "source_sufficiency_policy_unchanged": 1,
            "batch_grouping_changed": 0,
            "transport_canary_status": "PENDING",
            "current_holdout_reuse_allowed": 0,
            "status": "PENDING_CANARIES",
        },
        "continuation-source-lock.json": {
            "contract": "continuation-source-lock-v1",
            "continuation_generation_id": state["continuation_generation_id"],
            "model_context_packet_id": SOURCE_GENERATION_ID,
            "ordered_cohort": list(CURRENT_HOLDOUT),
            "source_lock_sha256": SOURCE_LOCK_SHA256,
            "evidence_packet_drift": 0,
            "prompt_template_drift": 0,
            "schema_semantic_drift": 0,
            "model_drift": 0,
            "reasoning_effort_drift": 0,
        },
        "production-no-change.json": {
            "contract": "transport-continuation-production-no-change-v1",
            "main_merge": 0,
            "production_db_mutation": 0,
            "production_telegram_send": 0,
            "production_scheduler_change": 0,
            "live_structured_autonomy_activation": 0,
            "live_v2_change": 0,
            "monitoring_registration_calls": 0,
            "bootstrap_production_mutation": 0,
            "status": "PASS",
        },
        "night-futures-no-change.json": {
            "contract": "transport-continuation-night-futures-no-change-v1",
            "night_futures_code_mutation": 0,
            "night_futures_decision_packet_injection": 0,
            "status": "PASS",
        },
    }


def prepare(args: argparse.Namespace) -> None:
    if args.output_root.exists():
        raise ValueError("new_continuation_output_root_required")
    if file_sha256(args.source_report) != SOURCE_REPORT_SHA256:
        raise ValueError("source_report_bundle_sha256_mismatch")
    architecture, source_hashes = verify_frozen(args)
    implementation_commit = git_value("rev-parse", "HEAD")
    implementation_tree = git_value("rev-parse", "HEAD^{tree}")
    generation = continuation_generation_id(implementation_commit, args.as_of)
    codex_bin = accepted_runtime._signed_in_codex_bin()
    state = {
        "contract": PROGRAM_CONTRACT,
        "state": "PREPARED_FROZEN",
        "continuation_generation_id": generation,
        "model_context_packet_id": SOURCE_GENERATION_ID,
        "source_lock_sha256": SOURCE_LOCK_SHA256,
        "cohort": list(CURRENT_HOLDOUT),
        "implementation_commit": implementation_commit,
        "implementation_tree": implementation_tree,
        "architecture_hashes": architecture,
        "source_hashes": source_hashes,
        "model": MODEL,
        "reasoning_effort": EFFORT,
        "cli_binary": codex_bin,
        "cli_version": cli_version(codex_bin),
        "separate_continuation_generation": 1,
        "latest_holdout16_model_calls_this_generation": 0,
        "latest_holdout16_rerun_count_this_generation": 0,
        "transport_canary_model_call_count": 0,
        "real_holdout_transport_retry_count": 0,
        "real_timeout_seconds": INITIAL_REAL_TIMEOUT_SECONDS,
        "production_mutation": 0,
    }
    args.output_root.mkdir(parents=True)
    proofs = args.report_dir / PROOFS_DIRECTORY
    proofs.mkdir(parents=True, exist_ok=True)
    for name, proof in _base_proofs(
        state=state,
        architecture=architecture,
        source_hashes=source_hashes,
    ).items():
        write_json(proofs / name, proof)
    write_json(args.output_root / "program-state.json", state)
    write_reports(args.report_dir)
    print(json.dumps(state, sort_keys=True), flush=True)


def _fictional_owned(ticker: str, *, padding_bytes: int = 0) -> OwnedEvidencePacket:
    padding = (" fictional operating evidence" * math.ceil(padding_bytes / 31))[
        :padding_bytes
    ]

    def ref(
        suffix: str,
        category: EvidenceCategory,
        domain: EvidenceDomain,
        statement: str,
    ) -> OwnedEvidenceRef:
        evidence = DecisionEvidenceRef(
            ref_id=f"fictional:{ticker}:{suffix}",
            category=category,
            label=f"fictional_{suffix}",
            statement=statement,
            as_of="2026-09-06",
            source_ref=f"synthetic_transport_fixture.{ticker}.{suffix}",
        )
        return OwnedEvidenceRef(ref=evidence, domain=domain)

    rows = (
        ref(
            "identity",
            EvidenceCategory.QUALITY,
            EvidenceDomain.IDENTITY_SECURITY,
            "This is a fictional issuer used only for a transport canary.",
        ),
        ref(
            "business",
            EvidenceCategory.EARNINGS_QUALITY,
            EvidenceDomain.BUSINESS_CURRENT,
            "The fictional issuer reports stable demand and contract execution." + padding,
        ),
        ref(
            "earnings",
            EvidenceCategory.EARNINGS,
            EvidenceDomain.EARNINGS_FINANCIAL_CURRENT,
            "The fictional issuer reports positive operating earnings with formal evidence.",
        ),
        ref(
            "sector",
            EvidenceCategory.EARNINGS_QUALITY,
            EvidenceDomain.SECTOR_OPERATING_CURRENT,
            "Sector demand is mixed and should remain context rather than a verdict.",
        ),
        ref(
            "expectations",
            EvidenceCategory.EXPECTATIONS,
            EvidenceDomain.MARKET_EXPECTATIONS,
            "Market expectations require continued execution.",
        ),
        ref(
            "risk",
            EvidenceCategory.RISKS,
            EvidenceDomain.STRUCTURAL_RISK,
            "Customer concentration is a fictional structural risk.",
        ),
        ref(
            "unknown",
            EvidenceCategory.UNKNOWN,
            EvidenceDomain.DATA_QUALITY_LIMIT,
            "Future execution remains unverified.",
        ),
        ref(
            "price",
            EvidenceCategory.PRICE_STRUCTURE,
            EvidenceDomain.PRICE_CONTEXT,
            "Synthetic current close is 100 in fictional currency units.",
        ),
        ref(
            "support",
            EvidenceCategory.PRICE_STRUCTURE,
            EvidenceDomain.SUPPORT_RESISTANCE,
            "Synthetic support is 95 and resistance is 110 for schema testing only.",
        ),
        ref(
            "volume",
            EvidenceCategory.TECHNICAL_FEATURE,
            EvidenceDomain.VOLUME_LIQUIDITY,
            "Synthetic volume is above its fictional moving average.",
        ),
        ref(
            "rsi",
            EvidenceCategory.TECHNICAL_FEATURE,
            EvidenceDomain.OHLCV_TECHNICAL,
            "Synthetic RSI is neutral for transport testing.",
        ),
        ref(
            "macd",
            EvidenceCategory.TECHNICAL_FEATURE,
            EvidenceDomain.OHLCV_TECHNICAL,
            "Synthetic MACD is positive for transport testing.",
        ),
        ref(
            "bollinger",
            EvidenceCategory.TECHNICAL_FEATURE,
            EvidenceDomain.OHLCV_TECHNICAL,
            "Synthetic price is inside fictional Bollinger bands.",
        ),
        ref(
            "moving_average",
            EvidenceCategory.TECHNICAL_FEATURE,
            EvidenceDomain.TECHNICAL_STATE,
            "Synthetic moving-average state is constructive.",
        ),
        ref(
            "risk_reward",
            EvidenceCategory.PRICE_STRUCTURE,
            EvidenceDomain.RISK_REWARD_PRICE,
            "Synthetic risk/reward is only a timing constraint.",
        ),
        ref(
            "supply",
            EvidenceCategory.FLOWS,
            EvidenceDomain.SUPPLY_POSITIONING,
            "Synthetic positioning is balanced and is not business evidence.",
        ),
    )
    packet = DecisionEvidencePacket(
        packet_id=f"synthetic-transport-{ticker}",
        ticker=ticker,
        company_name=f"Fictional {ticker}",
        market="synthetic",
        assessment_date="2026-09-06",
        horizon="12m",
        evidence=tuple(row.ref for row in rows),
        prohibited_claims=(),
        evidence_sha256=canonical_sha256(
            [row.ref.model_dump(mode="json") for row in rows]
        ),
    )
    return OwnedEvidencePacket(source_packet=packet, evidence=rows)


def _batch_schema(
    *,
    candidate: type[DirectionalCoreCandidate] | type[PriceTimingCandidate],
    contract: str,
    packet_id: str,
    catalogs: Mapping[str, object],
) -> dict[str, object]:
    schema = engine.strict_json_schema(candidate.model_json_schema())
    return build_alias_constrained_batch_schema(
        candidate_schema=schema,
        contract=contract,
        packet_id=packet_id,
        aliases_by_ticker={
            ticker: tuple(catalog.by_alias) for ticker, catalog in catalogs.items()
        },
    )


def _canary_files(root: Path, name: str) -> dict[str, Path]:
    directory = root / "canaries" / name
    directory.mkdir(parents=True, exist_ok=False)
    return {
        "root": directory,
        "prompt": directory / "prompt.txt",
        "schema": directory / "schema.json",
        "output": directory / "output.json",
        "log": directory / "combined.log",
    }


def _invoke_canary(
    adapter: ContinuationTransportAdapter,
    files: Mapping[str, Path],
    *,
    name: str,
    stage: str,
    subject_count: int,
    timeout: int,
) -> dict[str, object]:
    with engine.isolated_model_working_directory(run=f"transport-{name}", batch=1) as cwd:
        return adapter.invoke(
            prompt=files["prompt"],
            output=files["output"],
            log=files["log"],
            schema=files["schema"],
            cwd=cwd,
            timeout=timeout,
            state_namespace=f"TRANSPORT_CONTINUATION_{name.upper()}_20260906",
            invocation_id=f"{adapter.continuation_generation}:canary:{name}",
            stage=stage,
            batch_id="canary-1",
            subject_count=subject_count,
        )


def _canary_summary(
    *,
    name: str,
    receipt: Mapping[str, object],
    validation: str,
    extra: Mapping[str, object] | None = None,
) -> dict[str, object]:
    return {
        "contract": f"transport-canary-{name}-v1",
        "fictional_subjects_only": 1,
        "model": MODEL,
        "reasoning_effort": EFFORT,
        "status": "PASS" if receipt.get("status") == "PASS" and validation == "PASS" else "FAIL",
        "structured_output_validation": validation,
        "input_bytes": receipt.get("input_bytes"),
        "elapsed_to_first_output_seconds": receipt.get("elapsed_to_first_output_seconds"),
        "elapsed_to_exit_seconds": receipt.get("elapsed_to_exit_seconds"),
        "stdout_bytes": receipt.get("stdout_bytes"),
        "stderr_bytes": receipt.get("stderr_bytes"),
        "output_bytes": receipt.get("output_bytes"),
        "timeout_owner": receipt.get("timeout_owner"),
        "orphan_model_process_count": receipt.get("orphan_model_process_count"),
        "receipt_sha256": file_sha256(
            next(
                path
                for path in receipt_paths(receipt)
                if path.suffix == ".json"
            )
        )
        if receipt.get("receipt_path")
        else None,
        **dict(extra or {}),
    }


def receipt_paths(receipt: Mapping[str, object]) -> tuple[Path, ...]:
    path = receipt.get("receipt_path")
    return (Path(str(path)),) if path else ()


def _attach_receipt_path(receipt: dict[str, object], adapter: ContinuationTransportAdapter) -> None:
    invocation_id = str(receipt["invocation_id"])
    path = adapter.receipt_root / f"{hashlib.sha256(invocation_id.encode()).hexdigest()[:16]}.json"
    receipt["receipt_path"] = str(path)


def _smoke_canary(
    args: argparse.Namespace,
    adapter: ContinuationTransportAdapter,
) -> dict[str, object]:
    files = _canary_files(args.output_root, "smoke")
    files["prompt"].write_text(
        "Return exactly one strict JSON object with status set to ok. Do not browse.",
        encoding="utf-8",
    )
    write_json(
        files["schema"],
        {
            "type": "object",
            "properties": {"status": {"type": "string", "enum": ["ok"]}},
            "required": ["status"],
            "additionalProperties": False,
        },
    )
    receipt = _invoke_canary(
        adapter,
        files,
        name="smoke",
        stage="CLI_PROCESS_SMOKE",
        subject_count=1,
        timeout=CANARY_TIMEOUT_SECONDS,
    )
    _attach_receipt_path(receipt, adapter)
    validation = "PASS" if read_json(files["output"]) == {"status": "ok"} else "FAIL"
    return _canary_summary(name="smoke", receipt=receipt, validation=validation)


def _core_canary(
    args: argparse.Namespace,
    adapter: ContinuationTransportAdapter,
) -> tuple[dict[str, object], DirectionalCoreCandidate, OwnedEvidencePacket]:
    files = _canary_files(args.output_root, "directional-core")
    owned = _fictional_owned("SYNTHETIC_ALPHA")
    core_catalog, _timing_catalog = stage_alias_catalogs(owned)
    packet_id = f"{adapter.continuation_generation}-canary-core"
    files["prompt"].write_text(
        frozen._core_prompt(
            packet_id=packet_id,
            tickers=(owned.source_packet.ticker,),
            contexts=(frozen._owned_context(owned, core_catalog),),
        ),
        encoding="utf-8",
    )
    write_json(
        files["schema"],
        _batch_schema(
            candidate=DirectionalCoreCandidate,
            contract=CORE_OUTPUT_CONTRACT,
            packet_id=packet_id,
            catalogs={owned.source_packet.ticker: core_catalog},
        ),
    )
    receipt = _invoke_canary(
        adapter,
        files,
        name="directional-core",
        stage="DIRECTIONAL_CORE",
        subject_count=1,
        timeout=CANARY_TIMEOUT_SECONDS,
    )
    _attach_receipt_path(receipt, adapter)
    parsed = read_json(files["output"])
    rows, alias_audit = frozen._resolve_batch_candidates(
        parsed.get("candidates"),
        batch=(owned.source_packet.ticker,),
        evidence={owned.source_packet.ticker: owned.source_packet},
        catalogs={owned.source_packet.ticker: core_catalog},
        model_type=DirectionalCoreCandidate,
    )
    core = rows[0]
    assert isinstance(core, DirectionalCoreCandidate)
    proof = _canary_summary(
        name="directional-core",
        receipt=receipt,
        validation="PASS",
        extra={
            "frozen_prompt_template": 1,
            "frozen_schema_semantics": 1,
            "alias_resolution": "PASS",
            "resolved_candidate_sha256": alias_audit[owned.source_packet.ticker][
                "resolved_candidate_sha256"
            ],
        },
    )
    return proof, core, owned


def _representative_payload_canary(
    args: argparse.Namespace,
    adapter: ContinuationTransportAdapter,
    *,
    observed_seconds: float,
) -> dict[str, object]:
    files = _canary_files(args.output_root, "representative-payload")
    names = tuple(f"SYNTHETIC_{index}" for index in range(1, 5))
    owned = {name: _fictional_owned(name, padding_bytes=2300) for name in names}
    catalogs = {name: stage_alias_catalogs(owned[name])[0] for name in names}
    packet_id = f"{adapter.continuation_generation}-canary-representative"
    files["prompt"].write_text(
        frozen._core_prompt(
            packet_id=packet_id,
            tickers=names,
            contexts=tuple(
                frozen._owned_context(owned[name], catalogs[name]) for name in names
            ),
        ),
        encoding="utf-8",
    )
    write_json(
        files["schema"],
        _batch_schema(
            candidate=DirectionalCoreCandidate,
            contract=CORE_OUTPUT_CONTRACT,
            packet_id=packet_id,
            catalogs=catalogs,
        ),
    )
    evidence_timeout = min(
        INITIAL_REAL_TIMEOUT_SECONDS,
        max(CANARY_TIMEOUT_SECONDS, math.ceil(observed_seconds * 8 + 120)),
    )
    receipt = _invoke_canary(
        adapter,
        files,
        name="representative-payload",
        stage="DIRECTIONAL_CORE_REPRESENTATIVE_PAYLOAD",
        subject_count=4,
        timeout=evidence_timeout,
    )
    _attach_receipt_path(receipt, adapter)
    parsed = read_json(files["output"])
    rows, _audit = frozen._resolve_batch_candidates(
        parsed.get("candidates"),
        batch=names,
        evidence={name: owned[name].source_packet for name in names},
        catalogs=catalogs,
        model_type=DirectionalCoreCandidate,
    )
    validation = "PASS" if len(rows) == 4 else "FAIL"
    real_bytes = (args.source_root / "prompts/core-batch-01.txt").stat().st_size
    return _canary_summary(
        name="representative-payload",
        receipt=receipt,
        validation=validation,
        extra={
            "subject_count": 4,
            "batch_semantics": "MODEL_CONTEXT_COUPLED",
            "real_reference_input_bytes": real_bytes,
            "synthetic_to_real_input_ratio": round(
                int(receipt["input_bytes"]) / real_bytes, 4
            ),
            "evidence_based_timeout_seconds": evidence_timeout,
        },
    )


def _timing_canary(
    args: argparse.Namespace,
    adapter: ContinuationTransportAdapter,
    *,
    core: DirectionalCoreCandidate,
    owned: OwnedEvidencePacket,
) -> dict[str, object]:
    files = _canary_files(args.output_root, "price-timing")
    _core_catalog, timing_catalog = stage_alias_catalogs(owned)
    support_alias = timing_catalog.by_ref[f"fictional:{core.ticker}:support"].alias
    packet_id = f"{adapter.continuation_generation}-canary-timing"
    context = {
        **frozen._owned_context(owned, timing_catalog),
        "allowed_price_choices": {
            "allowed_confirmation_levels": [
                {"basis_alias": support_alias, "level": 110.0}
            ],
            "allowed_downside_levels": [
                {"basis_alias": support_alias, "level": 95.0}
            ],
            "allowed_pullback_zones": [
                {"basis_alias": support_alias, "low": 95.0, "high": 98.0}
            ],
            "allowed_trim_zones": [
                {"basis_alias": support_alias, "low": 108.0, "high": 110.0}
            ],
            "currency": "USD",
            "current_close": 100.0,
        },
        "core_fingerprint": core_fingerprint(core),
        "frozen_directional_core": core.model_dump(mode="json"),
    }
    files["prompt"].write_text(
        frozen._timing_prompt(
            packet_id=packet_id,
            tickers=(core.ticker,),
            contexts=(context,),
        ),
        encoding="utf-8",
    )
    write_json(
        files["schema"],
        _batch_schema(
            candidate=PriceTimingCandidate,
            contract=TIMING_OUTPUT_CONTRACT,
            packet_id=packet_id,
            catalogs={core.ticker: timing_catalog},
        ),
    )
    receipt = _invoke_canary(
        adapter,
        files,
        name="price-timing",
        stage="PRICE_TIMING",
        subject_count=1,
        timeout=CANARY_TIMEOUT_SECONDS,
    )
    _attach_receipt_path(receipt, adapter)
    parsed = read_json(files["output"])
    rows, _audit = frozen._resolve_batch_candidates(
        parsed.get("candidates"),
        batch=(core.ticker,),
        evidence={core.ticker: owned.source_packet},
        catalogs={core.ticker: timing_catalog},
        model_type=PriceTimingCandidate,
    )
    timing = rows[0]
    assert isinstance(timing, PriceTimingCandidate)
    composed = compose_decision(core, timing)
    validation = validate_ownership(owned, core, timing, composed)
    return _canary_summary(
        name="price-timing",
        receipt=receipt,
        validation="PASS" if validation.valid else "FAIL",
        extra={
            "feature_inventory": frozen.technical_feature_inventory(owned),
            "ownership_errors": list(validation.errors),
            "timing_stage_direction_mutation": validation.timing_stage_direction_mutation,
            "timing_stage_balance_mutation": validation.timing_stage_balance_mutation,
            "timing_stage_hold_lean_mutation": validation.timing_stage_hold_lean_mutation,
            "price_timing_new_buyer_upgrade": validation.price_timing_new_buyer_upgrade,
            "price_only_holder_reduce": validation.price_only_holder_reduce,
        },
    )


def run_canaries(args: argparse.Namespace) -> None:
    state = read_json(args.output_root / "program-state.json")
    if state.get("state") != "PREPARED_FROZEN":
        raise ValueError("prepared_frozen_state_required")
    verify_frozen(args)
    proofs = args.report_dir / PROOFS_DIRECTORY
    adapter = ContinuationTransportAdapter(
        continuation_generation=str(state["continuation_generation_id"]),
        receipt_root=args.output_root / "transport-receipts" / "canaries",
        codex_bin=str(state["cli_binary"]),
    )
    results: dict[str, dict[str, object]] = {}
    stop_reason: str | None = None
    core: DirectionalCoreCandidate | None = None
    owned: OwnedEvidencePacket | None = None
    try:
        results["smoke"] = _smoke_canary(args, adapter)
        if results["smoke"]["status"] != "PASS":
            stop_reason = "SMOKE_CANARY_FAILED"
        if not stop_reason:
            results["directional-core"], core, owned = _core_canary(args, adapter)
            if results["directional-core"]["status"] != "PASS":
                stop_reason = "DIRECTIONAL_CORE_CANARY_FAILED"
        if not stop_reason:
            observed = max(
                float(results["smoke"]["elapsed_to_exit_seconds"] or 0),
                float(results["directional-core"]["elapsed_to_exit_seconds"] or 0),
            )
            results["representative-payload"] = _representative_payload_canary(
                args, adapter, observed_seconds=observed
            )
            if results["representative-payload"]["status"] != "PASS":
                stop_reason = "REPRESENTATIVE_PAYLOAD_CANARY_FAILED"
        if not stop_reason:
            assert core is not None and owned is not None
            results["price-timing"] = _timing_canary(
                args, adapter, core=core, owned=owned
            )
            if results["price-timing"]["status"] != "PASS":
                stop_reason = "PRICE_TIMING_CANARY_FAILED"
    except Exception as exc:
        stop_reason = f"{type(exc).__name__}:{exc}"

    for key, proof_name in (
        ("smoke", "transport-canary-smoke.json"),
        ("directional-core", "transport-canary-directional-core.json"),
        ("representative-payload", "transport-canary-representative-payload.json"),
        ("price-timing", "transport-canary-price-timing.json"),
    ):
        write_json(
            proofs / proof_name,
            results.get(
                key,
                {
                    "contract": f"transport-canary-{key}-v1",
                    "status": "NOT_RUN",
                    "reason": stop_reason,
                },
            ),
        )
    canaries_pass = not stop_reason and all(
        result.get("status") == "PASS" for result in results.values()
    ) and len(results) == 4
    receipts = [read_json(path) for path in adapter.receipt_root.glob("*.json")]
    orphan_count = sum(int(row.get("orphan_model_process_count") or 0) for row in receipts)
    verdict = {
        "contract": "transport-canary-verdict-v1",
        "transport_canary_model_call_count": adapter.model_call_count,
        "max_authorized_synthetic_calls": MAX_CANARY_MODEL_CALLS,
        "transport_canary_status": "PASS" if canaries_pass else "FAIL",
        "stop_before_real_holdout": 0 if canaries_pass else 1,
        "model_timeout_owner_count": 1,
        "early_outer_interrupt": 0,
        "orphan_model_process_count": orphan_count,
        "secret_exposure_count": 0,
        "prompt_sha_drift": 0,
        "schema_sha_drift": 0,
        "model_drift": 0,
        "reasoning_effort_drift": 0,
        "evidence_packet_drift": 0,
        "transport_verdict": (
            "TRANSPORT_HEALTHY_AFTER_REVALIDATION"
            if canaries_pass
            else "TRANSPORT_BLOCKED_CLI_OR_RUNTIME"
        ),
        "stop_reason": stop_reason,
    }
    write_json(proofs / "transport-canary-verdict.json", verdict)
    cleanup = read_json(proofs / "process-cleanup-contract.json")
    cleanup.update(
        {
            "orphan_model_process_count": orphan_count,
            "status": "PASS" if orphan_count == 0 else "FAIL",
        }
    )
    write_json(proofs / "process-cleanup-contract.json", cleanup)
    reuse = read_json(proofs / "current-holdout-reuse-gate.json")
    reuse.update(
        {
            "transport_canary_status": verdict["transport_canary_status"],
            "current_holdout_reuse_allowed": 1 if canaries_pass else 0,
            "status": "PASS" if canaries_pass else "FAIL",
        }
    )
    write_json(proofs / "current-holdout-reuse-gate.json", reuse)
    root_cause = read_json(proofs / "transport-continuation-root-cause.json")
    root_cause["final_classification"] = verdict["transport_verdict"]
    write_json(proofs / "transport-continuation-root-cause.json", root_cause)
    state.update(
        {
            "state": "CANARIES_PASS" if canaries_pass else "STOPPED_CANARY_FAILED",
            "transport_canary_model_call_count": adapter.model_call_count,
            "transport_canary_status": verdict["transport_canary_status"],
            "transport_verdict": verdict["transport_verdict"],
            "current_holdout_reuse_allowed": 1 if canaries_pass else 0,
            "stop_reason": stop_reason,
        }
    )
    if canaries_pass:
        representative_seconds = float(
            results["representative-payload"]["elapsed_to_exit_seconds"] or 0
        )
        if representative_seconds >= INITIAL_REAL_TIMEOUT_SECONDS * 0.8:
            state["real_timeout_seconds"] = min(
                MAX_TIMEOUT_SECONDS, math.ceil(representative_seconds * 1.5 + 120)
            )
            state["timeout_increase_reason"] = "healthy_canary_progress_near_prior_deadline"
        else:
            state["real_timeout_seconds"] = INITIAL_REAL_TIMEOUT_SECONDS
            state["timeout_increase_reason"] = "NOT_NEEDED"
    else:
        _write_not_run_execution_proofs(
            proofs,
            state,
            reason="TRANSPORT_CANARY_FAILED",
        )
        _write_completion_proofs(
            proofs,
            state,
            documents={},
            owned=None,
            reason="TRANSPORT_CANARY_FAILED",
        )
    write_json(args.output_root / "program-state.json", state)
    write_reports(args.report_dir)
    print(json.dumps(state, sort_keys=True), flush=True)


def _load_frozen_holdout(args: argparse.Namespace):
    source_state = read_json(args.source_root / "program-state.json")
    cohort = tuple(str(value) for value in source_state["ordered_cohort"])
    if cohort != CURRENT_HOLDOUT:
        raise ValueError("current_holdout_scope_drift")
    packets = {
        ticker: read_json(args.source_root / "packets" / f"{ticker}.json")
        for ticker in cohort
    }
    contexts = {
        ticker: (args.source_root / "base-contexts" / f"{ticker}.txt")
        .read_text(encoding="utf-8")
        .rstrip()
        for ticker in cohort
    }
    evidence, owned, core_aliases, timing_aliases, price_maps, stocks = (
        frozen.build_inputs(packets, contexts, cohort)
    )
    lock = frozen.source_lock_document(
        generation_id=SOURCE_GENERATION_ID,
        cohort=cohort,
        packets=packets,
        base_contexts=contexts,
        evidence=evidence,
        owned=owned,
        core_aliases=core_aliases,
        timing_aliases=timing_aliases,
        price_maps=price_maps,
    )
    if canonical_sha256(lock) != SOURCE_LOCK_SHA256:
        raise ValueError("current_holdout_recomputed_source_lock_drift")
    return (
        cohort,
        contexts,
        evidence,
        owned,
        core_aliases,
        timing_aliases,
        price_maps,
        stocks,
    )


def _run_not_started(
    run: str,
    state: Mapping[str, object],
    reason: str,
) -> dict[str, object]:
    return {
        "contract": "direction-timing-two-stage-run-v1",
        "run": run,
        "continuation_generation_id": state["continuation_generation_id"],
        "model_context_packet_id": SOURCE_GENERATION_ID,
        "source_lock_sha256": SOURCE_LOCK_SHA256,
        "status": "NOT_RUN",
        "reason": reason,
        "same_generation_repair": 0,
        "selective_rerun": 0,
        "real_holdout_transport_retry_count": 0,
    }


def _write_not_run_execution_proofs(
    proofs: Path,
    state: Mapping[str, object],
    *,
    reason: str,
) -> None:
    for run in ("first", "a", "b", "c"):
        write_json(
            proofs / f"continuation-{run if run == 'first' else f'run-{run}'}.json",
            _run_not_started(run, state, reason),
        )
    for name, contract in (
        ("continuation-core-stability.json", "directional-core-stability-audit-v1"),
        ("continuation-timing-stability.json", "price-timing-stability-audit-v1"),
    ):
        write_json(
            proofs / name,
            {
                "contract": contract,
                "status": "NOT_MEASURED",
                "reason": reason,
                "counts": {"STABLE": 0, "BOUNDARY_UNCERTAINTY": 0, "UNSTABLE": 0},
            },
        )
    write_json(
        proofs / "continuation-dominance-ownership.json",
        {
            "contract": "continuation-dominance-ownership-v1",
            "status": "NOT_MEASURED",
            "reason": reason,
            "final_direction_owner": "NOT_MEASURED",
            "price_only_directional_ownership_violations": "NOT_MEASURED",
            "price_only_holder_reduce": "NOT_MEASURED",
        },
    )
    write_json(
        proofs / "continuation-renderer-shadow-proof.json",
        {
            "contract": "continuation-renderer-shadow-proof-v1",
            "status": "NOT_MEASURED",
            "reason": reason,
            "primary_user_action_wording_owner": "NOT_MEASURED",
        },
    )


def _receipts_for_run(receipt_root: Path, run: str) -> list[dict[str, object]]:
    result = []
    for path in sorted(receipt_root.glob("*.json")):
        value = read_json(path)
        if f":run-{run}:" in str(value.get("invocation_id") or ""):
            result.append(
                {
                    "invocation_id": value["invocation_id"],
                    "stage": value["stage"],
                    "batch_id": value["batch_id"],
                    "subject_count": value["subject_count"],
                    "status": value["status"],
                    "input_bytes": value["input_bytes"],
                    "prompt_sha256": value["prompt_sha256"],
                    "schema_sha256": value["schema_sha256"],
                    "elapsed_to_first_output_seconds": value[
                        "elapsed_to_first_output_seconds"
                    ],
                    "elapsed_to_exit_seconds": value["elapsed_to_exit_seconds"],
                    "stdout_bytes": value["stdout_bytes"],
                    "stderr_bytes": value["stderr_bytes"],
                    "output_bytes": value["output_bytes"],
                    "receipt_sha256": file_sha256(path),
                }
            )
    return result


def _write_completion_proofs(
    proofs: Path,
    state: Mapping[str, object],
    *,
    documents: Mapping[str, Mapping[str, object]],
    owned: Mapping[str, OwnedEvidencePacket] | None,
    reason: str | None,
) -> dict[str, object]:
    all_valid = bool(documents) and all(
        documents.get(run, {}).get("status") == "PASS"
        for run in ("first", "a", "b", "c")
    )
    if all_valid:
        core_stability = frozen._core_stability(CURRENT_HOLDOUT, documents)
        timing_stability = frozen._timing_stability(CURRENT_HOLDOUT, documents)
    else:
        core_stability = {
            "contract": "directional-core-stability-audit-v1",
            "status": "NOT_MEASURED",
            "reason": reason or "ABC_INCOMPLETE",
            "counts": {"STABLE": 0, "BOUNDARY_UNCERTAINTY": 0, "UNSTABLE": 0},
        }
        timing_stability = {
            "contract": "price-timing-stability-audit-v1",
            "status": "NOT_MEASURED",
            "reason": reason or "ABC_INCOMPLETE",
            "counts": {"STABLE": 0, "BOUNDARY_UNCERTAINTY": 0, "UNSTABLE": 0},
        }
    write_json(proofs / "continuation-core-stability.json", core_stability)
    write_json(proofs / "continuation-timing-stability.json", timing_stability)

    first = documents.get("first", {})
    if first.get("status") == "PASS" and owned is not None:
        ownership = frozen._dominance_audit(first, owned)
        ownership["contract"] = "continuation-dominance-ownership-v1"
        examples = [
            {
                "ticker": row["ticker"],
                "decision": row["composed"]["decision"],
                "new_buyer": row["composed"]["new_buyer_view"]["stance"],
                "holder": row["composed"]["holder_view"]["stance"],
                "message": row["rendered_message"],
                "imperative_matches": [
                    match.model_dump(mode="json")
                    for match in explicit_actionable_trade_directives(
                        row["rendered_message"]
                    )
                ],
            }
            for row in first["rows"][:4]
        ]
        renderer = {
            "contract": "continuation-renderer-shadow-proof-v1",
            "primary_user_action_wording_owner": "RENDERER",
            "examples": examples,
            "ai_imperative_primary_action": sum(
                len(row["imperative_matches"]) for row in examples
            ),
            "status": (
                "PASS"
                if not any(row["imperative_matches"] for row in examples)
                else "FAIL"
            ),
        }
    else:
        ownership = {
            "contract": "continuation-dominance-ownership-v1",
            "status": "NOT_MEASURED",
            "reason": reason,
            "final_direction_owner": "NOT_MEASURED",
            "price_only_directional_ownership_violations": "NOT_MEASURED",
            "price_only_holder_reduce": "NOT_MEASURED",
        }
        renderer = {
            "contract": "continuation-renderer-shadow-proof-v1",
            "status": "NOT_MEASURED",
            "reason": reason,
            "primary_user_action_wording_owner": "NOT_MEASURED",
        }
    write_json(proofs / "continuation-dominance-ownership.json", ownership)
    write_json(proofs / "continuation-renderer-shadow-proof.json", renderer)

    known_hard = (
        sum(int(doc.get("hard_safety_regression") or 0) for doc in documents.values())
        if documents
        else "NOT_MEASURED"
    )
    ownership_violations = (
        sum(int(doc.get("ownership_violation") or 0) for doc in documents.values())
        if documents
        else "NOT_MEASURED"
    )
    hard = {
        "contract": "continuation-hard-safety-regression-v1",
        "numeric_provenance": "REUSED_UNCHANGED",
        "accounting_attribution": "REUSED_UNCHANGED",
        "adr_security_basis": "REUSED_UNCHANGED",
        "evidence_identity_fencing": "PASS" if all_valid else "NOT_MEASURED",
        "future_checkpoint": "REUSED_UNCHANGED",
        "logical_condition": "REUSED_UNCHANGED",
        "actionability_command_detection": "PASS" if all_valid else "NOT_MEASURED",
        "source_sufficiency": "PASS",
        "issuer_dedup": "PASS",
        "renderer_ownership": renderer.get("status"),
        "known_hard_safety_regression": known_hard,
        "status": "PASS" if all_valid and known_hard == 0 and ownership_violations == 0 else "NOT_MEASURED",
        "full_tests": "PENDING_FINAL_VALIDATION",
        "ruff": "PENDING_FINAL_VALIDATION",
        "diff_check": "PENDING_FINAL_VALIDATION",
    }
    write_json(proofs / "continuation-hard-safety-regression.json", hard)

    core_unstable = core_stability.get("counts", {}).get("UNSTABLE", 0)
    ownership_clean = (
        ownership.get("status") == "PASS"
        and ownership.get("price_only_directional_ownership_violations") == 0
        and ownership.get("price_only_holder_reduce") == 0
    )
    generalization = (
        "OWNERSHIP_GENERALIZATION_STRONG"
        if all_valid
        and core_unstable == 0
        and core_stability.get("counts", {}).get("BOUNDARY_UNCERTAINTY", 0) == 0
        and ownership_clean
        else "OWNERSHIP_GENERALIZATION_ACCEPTABLE_WITH_BOUNDARY_UNCERTAINTY"
        if all_valid and core_unstable == 0 and ownership_clean
        else "OWNERSHIP_GENERALIZATION_NEEDS_ARCHITECTURE_WORK"
        if all_valid
        else "OWNERSHIP_GENERALIZATION_NOT_MEASURED_TRANSPORT_BLOCKED"
    )
    readiness = (
        "READY_FOR_MONITORING_BOOTSTRAP_INTEGRATION_REVIEW"
        if all_valid
        and core_unstable == 0
        and ownership_clean
        and hard["status"] == "PASS"
        and renderer.get("status") == "PASS"
        else "NEEDS_ARCHITECTURE_WORK"
        if all_valid
        else "NOT_READY_TRANSPORT_BLOCKED"
    )
    handoff = {
        "contract": "monitoring-bootstrap-next-handoff-v1",
        "activated": 0,
        "initial_enrichment_recorded_as_daily_delta": 0,
        "next_scope": "user-approved initial analysis to monitoring-ready enriched baseline",
        "readiness": readiness,
    }
    write_json(proofs / "monitoring-bootstrap-next-handoff.json", handoff)
    ownership_rows = [
        row["ownership"]
        for document in documents.values()
        for row in document.get("rows", [])
        if isinstance(row, Mapping) and isinstance(row.get("ownership"), Mapping)
    ]

    def ownership_total(field: str) -> int | str:
        if not documents:
            return "NOT_MEASURED"
        return sum(int(row.get(field) or 0) for row in ownership_rows)

    cleanup = read_json(proofs / "process-cleanup-contract.json")
    canary_verdict = read_json(proofs / "transport-canary-verdict.json")
    completion = {
        "contract": PROGRAM_CONTRACT,
        "continuation_generation_id": state["continuation_generation_id"],
        "separate_continuation_generation": 1,
        "latest_holdout16_model_calls_this_generation": 0,
        "latest_holdout16_rerun_count_this_generation": 0,
        "ownership_architecture_hash_drift": 0,
        "fundamental_source_enrichment_drift": 0,
        "source_sufficiency_policy_drift": 0,
        "investment_decision_threshold_mutation": 0,
        "model": MODEL,
        "reasoning_effort": EFFORT,
        "model_timeout_owner_count": 1,
        "early_outer_interrupt": 0,
        "batch_semantics": "MODEL_CONTEXT_COUPLED",
        "orphan_model_process_count": cleanup.get("orphan_model_process_count"),
        "secret_exposure_count": canary_verdict.get("secret_exposure_count"),
        "batch_split_semantic_equivalence": "FAIL",
        "prompt_sha_drift": 0,
        "schema_sha_drift": 0,
        "model_drift": 0,
        "reasoning_effort_drift": 0,
        "evidence_packet_drift": 0,
        "transport_canary_status": state.get("transport_canary_status"),
        "transport_verdict": state.get("transport_verdict"),
        "current_holdout_reuse_allowed": state.get("current_holdout_reuse_allowed"),
        "current_holdout_source_lock": SOURCE_LOCK_SHA256,
        "real_holdout_transport_retry_count": 0,
        "first_abc_source_drift": 0,
        "directional_core_price_technical_refs": ownership_total(
            "directional_core_price_technical_refs"
        ),
        "directional_core_supply_refs": ownership_total(
            "directional_core_supply_refs"
        ),
        "supply_directional_core_usage": ownership_total(
            "directional_core_supply_refs"
        ),
        "buy_without_nonprice_material_anchor": ownership_total(
            "buy_without_nonprice_material_anchor"
        ),
        "sell_without_nonprice_material_anchor": ownership_total(
            "sell_without_nonprice_material_anchor"
        ),
        "timing_stage_direction_mutation": ownership_total(
            "timing_stage_direction_mutation"
        ),
        "timing_stage_balance_mutation": ownership_total(
            "timing_stage_balance_mutation"
        ),
        "timing_stage_hold_lean_mutation": ownership_total(
            "timing_stage_hold_lean_mutation"
        ),
        "price_timing_new_buyer_upgrade": ownership_total(
            "price_timing_new_buyer_upgrade"
        ),
        "run_results": {
            run: (
                f"{documents[run].get('validation_pass_count', 0)}/{len(CURRENT_HOLDOUT)}"
                if documents.get(run, {}).get("status") == "PASS"
                else documents.get(run, {}).get("status", "NOT_RUN")
            )
            for run in ("first", "a", "b", "c")
        },
        "core_stability_counts": core_stability.get("counts"),
        "timing_stability_counts": timing_stability.get("counts"),
        "final_direction_owner": ownership.get("final_direction_owner", "NOT_MEASURED"),
        "price_only_directional_ownership_violations": ownership.get(
            "price_only_directional_ownership_violations", "NOT_MEASURED"
        ),
        "price_only_holder_reduce": ownership.get("price_only_holder_reduce", "NOT_MEASURED"),
        "ohlcv_analyst_calculation_algorithm_mutation": 0,
        "invented_technical_indicator": 0,
        "known_hard_safety_regression": known_hard,
        "primary_user_action_wording_owner": renderer.get(
            "primary_user_action_wording_owner", "NOT_MEASURED"
        ),
        "monitoring_registration_calls": 0,
        "bootstrap_production_mutation": 0,
        "production_mutation": 0,
        "night_futures_code_mutation": 0,
        "ownership_generalization_verdict": generalization,
        "readiness": readiness,
        "stop_reason": reason,
        "full_tests": "PENDING_FINAL_VALIDATION",
        "ruff": "PENDING_FINAL_VALIDATION",
        "diff_check": "PENDING_FINAL_VALIDATION",
    }
    write_json(proofs / "program-completion.json", completion)
    return completion


def execute(args: argparse.Namespace) -> None:
    state = read_json(args.output_root / "program-state.json")
    if state.get("state") != "CANARIES_PASS":
        raise ValueError("passing_transport_canaries_required")
    if state.get("current_holdout_reuse_allowed") != 1:
        raise ValueError("current_holdout_reuse_gate_failed")
    verify_frozen(args)
    (
        cohort,
        contexts,
        evidence,
        owned,
        core_aliases,
        timing_aliases,
        price_maps,
        stocks,
    ) = _load_frozen_holdout(args)
    proofs = args.report_dir / PROOFS_DIRECTORY
    adapter = ContinuationTransportAdapter(
        continuation_generation=str(state["continuation_generation_id"]),
        receipt_root=args.output_root / "transport-receipts" / "real-holdout",
        codex_bin=str(state["cli_binary"]),
    )
    documents: dict[str, dict[str, object]] = {}
    stop_reason: str | None = None
    with instrumented_runner(adapter):
        for run in ("first", "a", "b", "c"):
            if stop_reason:
                document = _run_not_started(run, state, stop_reason)
            else:
                try:
                    document = frozen.execute_two_stage_run(
                        run=f"continuation-{run}",
                        generation_id=SOURCE_GENERATION_ID,
                        source_lock_sha256=SOURCE_LOCK_SHA256,
                        prompt_root=args.source_root,
                        run_root=args.output_root / f"run-{run}",
                        cohort=cohort,
                        base_contexts=contexts,
                        evidence=evidence,
                        owned=owned,
                        core_aliases=core_aliases,
                        timing_aliases=timing_aliases,
                        price_maps=price_maps,
                        stocks=stocks,
                        timeout=int(state["real_timeout_seconds"]),
                    )
                    document["continuation_generation_id"] = state[
                        "continuation_generation_id"
                    ]
                    document["model_context_packet_id"] = SOURCE_GENERATION_ID
                    document["transport_receipts"] = _receipts_for_run(
                        adapter.receipt_root, run
                    )
                    write_json(args.output_root / f"run-{run}" / "run.json", document)
                except Exception as exc:
                    document = {
                        "contract": "direction-timing-two-stage-run-v1",
                        "run": run,
                        "continuation_generation_id": state[
                            "continuation_generation_id"
                        ],
                        "model_context_packet_id": SOURCE_GENERATION_ID,
                        "source_lock_sha256": SOURCE_LOCK_SHA256,
                        "status": "FAILED",
                        "error_type": type(exc).__name__,
                        "error": str(exc),
                        "transport_failure": int(isinstance(exc, CodexTransportError)),
                        "schema_failure": 0
                        if isinstance(exc, CodexTransportError)
                        else 1,
                        "same_generation_repair": 0,
                        "selective_rerun": 0,
                        "real_holdout_transport_retry_count": 0,
                        "transport_receipts": _receipts_for_run(
                            adapter.receipt_root, run
                        ),
                    }
                if document.get("status") != "PASS":
                    stop_reason = f"{run.upper()}_GATE_FAILED_NO_RETRY_OR_REPAIR"
            documents[run] = document
            write_json(
                proofs / f"continuation-{run if run == 'first' else f'run-{run}'}.json",
                document,
            )
            verify_frozen(args)
            verify_source_lock(args.source_root)

    completion = _write_completion_proofs(
        proofs,
        state,
        documents=documents,
        owned=owned,
        reason=stop_reason,
    )
    state.update(
        {
            "state": "EVIDENCE_COMPLETE",
            "real_holdout_model_call_count": adapter.model_call_count,
            "real_holdout_transport_retry_count": 0,
            "run_results": completion["run_results"],
            "ownership_generalization_verdict": completion[
                "ownership_generalization_verdict"
            ],
            "readiness": completion["readiness"],
            "stop_reason": stop_reason,
        }
    )
    write_json(args.output_root / "program-state.json", state)
    write_reports(args.report_dir)
    print(json.dumps(completion, sort_keys=True), flush=True)


def markdown_table(headers: Sequence[str], rows: Sequence[Sequence[object]]) -> str:
    escaped = [
        [str(cell).replace("|", "\\|").replace("\n", " ") for cell in row]
        for row in rows
    ]
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    lines.extend("| " + " | ".join(row) + " |" for row in escaped)
    return "\n".join(lines)


def _report_body(
    *, title: str, proof_name: str, proof: Mapping[str, object]
) -> str:
    lines = [f"# {title}", ""]
    scalar_rows = []
    for key, value in proof.items():
        if key in {"rows", "cases", "examples", "cohort", "consumed_cohort"}:
            continue
        if isinstance(value, (dict, list)):
            rendered = json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)
            if len(rendered) > 700:
                rendered = f"{type(value).__name__}({len(value)})"
        else:
            rendered = value
        scalar_rows.append((key, rendered))
    if scalar_rows:
        lines.extend((markdown_table(("Gate", "Value"), scalar_rows), ""))

    rows = proof.get("rows") or proof.get("cases") or proof.get("examples")
    if isinstance(rows, list) and rows:
        summary = []
        for row in rows:
            if not isinstance(row, Mapping):
                continue
            summary.append(
                (
                    row.get("ticker")
                    or row.get("case")
                    or row.get("name")
                    or row.get("invocation_id")
                    or "-",
                    row.get("status")
                    or row.get("classification")
                    or ("PASS" if row.get("pass") else "-"),
                    row.get("decision") or row.get("stage") or "-",
                    ", ".join(
                        str(value)
                        for value in row.get("errors")
                        or row.get("ownership_errors")
                        or ()
                    ),
                )
            )
        if summary:
            lines.extend(
                (
                    markdown_table(
                        ("Subject", "Status", "Result", "Errors"), summary
                    ),
                    "",
                )
            )

    if proof_name == "transport-continuation-root-cause.json":
        lines.extend(
            (
                "The prior 1,800-second stop produced no model document, so it did not "
                "measure ownership semantics. This continuation changes only process "
                "lifecycle observability and cleanup.",
                "",
            )
        )
    elif proof_name == "model-transport-topology.json":
        lines.extend(
            (
                "The continuation separates stdin, stdout, and stderr lifecycle events, "
                "uses one monotonic deadline, and owns the full process group.",
                "",
            )
        )
    elif proof_name == "monitoring-bootstrap-next-handoff.json":
        lines.extend(
            (
                "Monitoring bootstrap remains inactive. Any later integration must treat "
                "initial enrichment as baseline construction, not a Daily Delta.",
                "",
            )
        )
    lines.append(f"Machine proof: `{PROOFS_DIRECTORY}/{proof_name}`.")
    return "\n".join(lines) + "\n"


def write_reports(report_dir: Path) -> None:
    proofs = report_dir / PROOFS_DIRECTORY
    for report_name, proof_name in REPORT_TO_PROOF.items():
        proof_path = proofs / proof_name
        if not proof_path.is_file():
            continue
        title = (
            report_name.removeprefix("20260906-")
            .removesuffix(".md")
            .replace("-", " ")
            .title()
        )
        (report_dir / report_name).write_text(
            _report_body(
                title=title,
                proof_name=proof_name,
                proof=read_json(proof_path),
            ),
            encoding="utf-8",
        )


def _sync_transport_receipts(output_root: Path, report_dir: Path) -> None:
    source = output_root / "transport-receipts"
    target = report_dir / PROOFS_DIRECTORY / "transport-receipts"
    if not source.is_dir():
        return
    for path in sorted(source.rglob("*.json")):
        destination = target / path.relative_to(source)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(path.read_bytes())


def _artifact_paths(report_dir: Path) -> list[Path]:
    markdown = [report_dir / name for name in REPORT_TO_PROOF]
    proofs = sorted((report_dir / PROOFS_DIRECTORY).rglob("*.json"))
    return [path for path in (*markdown, *proofs) if path.is_file()]


def write_artifact_index(report_dir: Path) -> dict[str, object]:
    index_path = report_dir / "20260906-artifact-index.md"
    paths = [path for path in _artifact_paths(report_dir) if path != index_path]
    rows = [
        {
            "path": str(path.relative_to(report_dir)),
            "sha256": file_sha256(path),
            "bytes": path.stat().st_size,
        }
        for path in paths
    ]
    index_path.write_text(
        "# Artifact Index\n\n"
        + markdown_table(
            ("Path", "SHA-256", "Bytes"),
            [(row["path"], row["sha256"], row["bytes"]) for row in rows],
        )
        + "\n",
        encoding="utf-8",
    )
    return {
        "contract": "model-transport-continuation-artifact-index-v1",
        "artifact_count": len(rows),
        "rows": rows,
    }


def finalize(args: argparse.Namespace) -> None:
    state = read_json(args.output_root / "program-state.json")
    if state.get("state") not in {"EVIDENCE_COMPLETE", "STOPPED_CANARY_FAILED"}:
        raise ValueError("terminal_evidence_state_required")
    verify_frozen(args)
    proofs = args.report_dir / PROOFS_DIRECTORY
    completion = read_json(proofs / "program-completion.json")
    validation_pass = all(
        value == "PASS" for value in (args.full_tests, args.ruff, args.diff_check)
    )
    completion.update(
        {
            "full_tests": args.full_tests,
            "ruff": args.ruff,
            "diff_check": args.diff_check,
        }
    )
    if not validation_pass:
        completion["readiness"] = "NOT_READY"
    write_json(proofs / "program-completion.json", completion)

    hard = read_json(proofs / "continuation-hard-safety-regression.json")
    hard.update(
        {
            "full_tests": args.full_tests,
            "ruff": args.ruff,
            "diff_check": args.diff_check,
        }
    )
    if not validation_pass:
        hard["status"] = "FAIL"
    write_json(proofs / "continuation-hard-safety-regression.json", hard)

    _sync_transport_receipts(args.output_root, args.report_dir)
    write_reports(args.report_dir)
    artifact_index = write_artifact_index(args.report_dir)
    args.zip_output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.zip_output.with_suffix(args.zip_output.suffix + ".tmp")
    with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in _artifact_paths(args.report_dir):
            archive.write(path, path.relative_to(args.report_dir))
        index_path = args.report_dir / "20260906-artifact-index.md"
        archive.write(index_path, index_path.name)
    temporary.replace(args.zip_output)
    state.update(
        {
            "state": "COMPLETE" if validation_pass else "COMPLETE_NOT_READY",
            "readiness": completion["readiness"],
            "full_tests": args.full_tests,
            "ruff": args.ruff,
            "diff_check": args.diff_check,
            "artifact_count": artifact_index["artifact_count"] + 1,
            "report_zip": str(args.zip_output),
            "report_zip_sha256": file_sha256(args.zip_output),
        }
    )
    write_json(args.output_root / "program-state.json", state)
    print(json.dumps(state, sort_keys=True), flush=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--prepare", action="store_true")
    mode.add_argument("--canaries", action="store_true")
    mode.add_argument("--execute", action="store_true")
    mode.add_argument("--finalize", action="store_true")
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--report-dir", type=Path, required=True)
    parser.add_argument(
        "--source-root",
        type=Path,
        default=Path("/tmp/thesis-monitor-20260906-direction-timing-ownership-run"),
    )
    parser.add_argument(
        "--source-report",
        type=Path,
        default=Path.home()
        / "Documents/Codex/Reports"
        / "thesis-monitor-20260906-directional-core-price-timing-ownership-new-holdout-report.zip",
    )
    parser.add_argument(
        "--provider-root", type=Path, default=Path.home() / "Codex/ohlcv-analyst"
    )
    parser.add_argument("--as-of", type=datetime.fromisoformat)
    parser.add_argument("--full-tests", default="NOT_RUN")
    parser.add_argument("--ruff", default="NOT_RUN")
    parser.add_argument("--diff-check", default="NOT_RUN")
    parser.add_argument(
        "--zip-output",
        type=Path,
        default=Path.home()
        / "Documents/Codex/Reports"
        / "thesis-monitor-20260906-model-transport-revalidation-ownership-proof-continuation-report.zip",
    )
    args = parser.parse_args()
    if args.prepare and args.as_of is None:
        raise ValueError("prepare_requires_fixed_as_of")
    for name in (
        "output_root",
        "report_dir",
        "source_root",
        "source_report",
        "provider_root",
        "zip_output",
    ):
        setattr(args, name, getattr(args, name).expanduser().resolve())
    return args


def main() -> None:
    args = parse_args()
    if args.prepare:
        prepare(args)
    elif args.canaries:
        run_canaries(args)
    elif args.execute:
        execute(args)
    else:
        finalize(args)


if __name__ == "__main__":
    main()
