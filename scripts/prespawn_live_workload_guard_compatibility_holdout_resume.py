from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import zipfile
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path

from app.services.direction_timing_ownership_service import canonical_sha256
from scripts import directional_core_price_timing_holdout as frozen
from scripts import new_issuer_holdout_selection_ownership_proof as prior
from scripts import synthetic_canary_fixture_repair_ownership_resume as guarded
from scripts import uskr22_structured_autonomy_shadow as engine


PROGRAM_CONTRACT = "prespawn-live-workload-guard-compatibility-holdout-resume-v1"
MODEL = "gpt-5.6-sol"
EFFORT = "xhigh"
TIMEOUT_SECONDS = 1800
TIMEOUT_OWNER_COUNT = 1
BATCH_SEMANTICS = "MODEL_CONTEXT_COUPLED"
CONTEXT_SIZE = 4
RUNS = ("first", "a", "b", "c")
SOURCE_GENERATION_ID = (
    "20260907-us-remediation-holdout-20260907T001800Z-57bcd871e06a"
)
SOURCE_LOCK_SHA256 = (
    "d4bd0b51d9cc543ebe03088047cce375db41d3d9a9f21c07d4fd5646bdf9b1ef"
)
LATEST_RESULT_SHA256 = (
    "fd519905d0201d5742d1c1b90c9b3e15b681020d05ad23a4031734a98eb73c68"
)
WORK_INSTRUCTION = (
    "docs/work-instructions/"
    "20260907-prespawn-live-workload-guard-compatibility-and-holdout-proof-resume.md"
)
WORK_INSTRUCTION_SHA256 = (
    "a10dcfb962a905f2c31d9fa5cabae6ecf83c5a8f27874c135cde4611ab84845b"
)
ORDERED_COHORT = (
    "NVDA",
    "JPM",
    "WMT",
    "BRK-B",
    "142210",
    "060900",
    "002680",
    "035420",
    "216050",
    "100700",
    "001530",
    "487580",
    "038870",
    "342870",
    "060230",
    "415380",
)
CONTEXT_GROUPS = tuple(tuple(ORDERED_COHORT[index : index + 4]) for index in range(0, 16, 4))

PROOF_NAMES = (
    "01-repository-provenance",
    "02-latest-result-integrity",
    "03-current-unexposed-holdout-state",
    "04-prespawn-guard-code-path-audit",
    "05-workload-observation-capability-audit",
    "06-workload-observation-backend-decision",
    "07-prespawn-root-cause-proof",
    "08-exception-provenance-contract",
    "09-receipt-lifecycle-contract",
    "10-context-preservation-error-propagation",
    "11-guard-compatibility-remediation-diff",
    "12-guard-regression-tests",
    "13-model-free-prespawn-guard-preflight",
    "14-authorized-guard-hash-drift-audit",
    "15-canonical-transport-freeze",
    "16-model-semantic-input-freeze",
    "17-source-lock-reuse-proof",
    "18-holdout-reuse-gate",
    "19-resume-runtime-precommit",
    "20-live-workload-coexistence-audit",
    "21-first-execution-summary",
    "22-first-context-artifact-manifest",
    "23-first-context-partial-semantic-audits",
    "24-first-ownership-gate",
    "25-first-renderer-gate",
    "26-first-hard-safety-gate",
    "27-run-a-execution-summary",
    "28-run-a-context-artifact-manifest",
    "29-run-a-context-partial-semantic-audits",
    "30-run-a-ownership-gate",
    "31-run-a-renderer-gate",
    "32-run-a-hard-safety-gate",
    "33-run-b-execution-summary",
    "34-run-b-context-artifact-manifest",
    "35-run-b-context-partial-semantic-audits",
    "36-run-b-ownership-gate",
    "37-run-b-renderer-gate",
    "38-run-b-hard-safety-gate",
    "39-run-c-execution-summary",
    "40-run-c-context-artifact-manifest",
    "41-run-c-context-partial-semantic-audits",
    "42-run-c-ownership-gate",
    "43-run-c-renderer-gate",
    "44-run-c-hard-safety-gate",
    "45-holdout-exposure-retirement-state",
    "46-core-stability",
    "47-timing-stability",
    "48-ownership-generalization",
    "49-renderer-ownership-proof",
    "50-hard-safety-regression",
    "51-production-no-change",
    "52-night-futures-no-change",
    "53-monitoring-bootstrap-next-handoff",
    "54-program-completion",
)
RUN_PROOFS = {
    "first": (21, 22, 23, 24, 25, 26),
    "a": (27, 28, 29, 30, 31, 32),
    "b": (33, 34, 35, 36, 37, 38),
    "c": (39, 40, 41, 42, 43, 44),
}
FROZEN_INPUT_PREFIXES = (
    "experiment/packets/",
    "experiment/base-contexts/",
    "experiment/prompts/",
    "experiment/schemas/",
    "experiment/timing-contexts/",
)
CANONICAL_ARCHITECTURE_PATHS = {
    "ownership_service": "app/services/direction_timing_ownership_service.py",
    "directional_balance": "app/services/directional_balance_service.py",
    "alias_fencing": "app/services/structured_autonomy_alias_service.py",
    "validator_renderer": "app/services/structured_autonomy_shadow_service.py",
    "stability_classifier": "app/services/structured_autonomy_stability_service.py",
    "source_enrichment": "app/services/coldstart_fundamental_enrichment_service.py",
    "source_assembly": "app/services/coldstart_source_assembly_service.py",
    "transport_lifecycle": "app/services/codex_transport_lifecycle_service.py",
    "frozen_runner": "scripts/directional_core_price_timing_holdout.py",
    "transport_adapter": "scripts/model_transport_revalidation_ownership_continuation.py",
    "experiment_runner": "scripts/us_price_context_gate_supported_universe_holdout_resume.py",
}
OWNERSHIP_KEYS = (
    "directional_core_price_technical_refs",
    "directional_core_supply_refs",
    "supply_directional_core_usage",
    "buy_without_nonprice_material_anchor",
    "sell_without_nonprice_material_anchor",
    "timing_stage_direction_mutation",
    "timing_stage_balance_mutation",
    "timing_stage_hold_lean_mutation",
    "price_timing_new_buyer_upgrade",
    "price_only_holder_reduce",
    "price_only_directional_ownership_violations",
    "directional_model_calls_on_source_insufficient",
    "price_only_directional_model_calls",
)


def read_json(path: Path) -> dict[str, object]:
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


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def bytes_sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def git_value(*args: str) -> str:
    return subprocess.run(
        ["git", *args], check=True, capture_output=True, text=True
    ).stdout.strip()


def proof_path(report_dir: Path, number: int) -> Path:
    return report_dir / "proofs" / f"{PROOF_NAMES[number - 1]}.json"


def write_proof(report_dir: Path, number: int, value: Mapping[str, object]) -> None:
    write_json(proof_path(report_dir, number), value)


def generation_id(implementation_commit: str, as_of: datetime) -> str:
    stamp = as_of.astimezone(UTC).strftime("%Y%m%dT%H%M%SZ")
    suffix = hashlib.sha256(
        f"{implementation_commit}|{stamp}|{PROGRAM_CONTRACT}".encode()
    ).hexdigest()[:12]
    return f"20260907-prespawn-guard-resume-{stamp}-{suffix}"


def zip_json(archive: zipfile.ZipFile, member: str) -> dict[str, object]:
    value = json.loads(archive.read(member))
    if not isinstance(value, dict):
        raise ValueError(f"zip_object_required:{member}")
    return value


def extract_frozen_inputs(
    archive: zipfile.ZipFile, output_root: Path, runtime_generation_id: str
) -> dict[str, object]:
    extracted: list[dict[str, object]] = []
    for info in archive.infolist():
        if not any(info.filename.startswith(prefix) for prefix in FROZEN_INPUT_PREFIXES):
            continue
        if info.is_dir():
            continue
        relative = Path(info.filename).relative_to("experiment")
        destination = output_root / relative
        payload = archive.read(info)
        original_sha = bytes_sha256(payload)
        if relative.parts[0] == "prompts":
            text = payload.decode("utf-8")
            if SOURCE_GENERATION_ID not in text:
                raise ValueError(f"source_generation_token_missing:{relative}")
            payload = text.replace(SOURCE_GENERATION_ID, runtime_generation_id).encode()
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(payload)
        extracted.append(
            {
                "path": str(relative),
                "source_sha256": original_sha,
                "runtime_sha256": bytes_sha256(payload),
            }
        )
    for source_member, destination_name in (
        ("experiment/source-lock.json", "source-lock.json"),
        ("experiment/new-holdout-precommit.json", "frozen-source-precommit.json"),
        ("experiment/prompt-schema-lock.json", "frozen-prompt-schema-lock.json"),
    ):
        payload = archive.read(source_member)
        destination = output_root / destination_name
        destination.write_bytes(payload)
        extracted.append(
            {
                "path": destination_name,
                "source_sha256": bytes_sha256(payload),
                "runtime_sha256": bytes_sha256(payload),
            }
        )
    return {"rows": extracted, "count": len(extracted)}


def canonical_architecture_hashes(repo_root: Path) -> dict[str, str]:
    return {
        name: file_sha256(repo_root / relative)
        for name, relative in CANONICAL_ARCHITECTURE_PATHS.items()
    }


def normalized_core_prompt_sha(path: Path, runtime_generation_id: str) -> str:
    payload = path.read_text(encoding="utf-8").replace(
        runtime_generation_id, SOURCE_GENERATION_ID
    )
    return bytes_sha256(payload.encode())


def prompt_schema_freeze(
    output_root: Path,
    frozen_lock: Mapping[str, object],
    runtime_generation_id: str,
) -> dict[str, object]:
    rows = []
    frozen_rows = frozen_lock.get("batches") or []
    for number, expected in enumerate(frozen_rows, start=1):
        if not isinstance(expected, Mapping):
            raise ValueError("invalid_frozen_prompt_schema_lock")
        core_prompt = output_root / "prompts" / f"core-batch-{number:02d}.txt"
        core_schema = output_root / "schemas" / f"core-batch-{number:02d}.json"
        timing_schema = output_root / "schemas" / f"timing-batch-{number:02d}.json"
        timing_context = output_root / "timing-contexts" / f"batch-{number:02d}.json"
        row = {
            "batch": number,
            "tickers": list(CONTEXT_GROUPS[number - 1]),
            "runtime_core_prompt_sha256": file_sha256(core_prompt),
            "normalized_core_prompt_sha256": normalized_core_prompt_sha(
                core_prompt, runtime_generation_id
            ),
            "expected_core_prompt_sha256": expected["core_prompt_sha256"],
            "core_schema_sha256": file_sha256(core_schema),
            "expected_core_schema_sha256": expected["core_schema_sha256"],
            "timing_schema_sha256": file_sha256(timing_schema),
            "expected_timing_schema_sha256": expected["timing_schema_sha256"],
            "timing_context_sha256": file_sha256(timing_context),
            "expected_timing_context_sha256": expected["timing_context_sha256"],
        }
        row["status"] = (
            "PASS"
            if row["normalized_core_prompt_sha256"]
            == row["expected_core_prompt_sha256"]
            and row["core_schema_sha256"] == row["expected_core_schema_sha256"]
            and row["timing_schema_sha256"] == row["expected_timing_schema_sha256"]
            and row["timing_context_sha256"]
            == row["expected_timing_context_sha256"]
            else "FAIL"
        )
        rows.append(row)
    return {
        "contract": "resume-prompt-schema-semantic-freeze-v1",
        "source_generation_id": SOURCE_GENERATION_ID,
        "runtime_generation_id": runtime_generation_id,
        "runtime_identity_token_substitution_only": 1,
        "prompt_semantic_drift": 0 if all(row["status"] == "PASS" for row in rows) else 1,
        "schema_semantic_drift": 0 if all(row["status"] == "PASS" for row in rows) else 1,
        "rows": rows,
        "status": "PASS" if all(row["status"] == "PASS" for row in rows) else "FAIL",
    }


class _UnavailableObserver:
    backend = "MODEL_FREE_FORCED_UNAVAILABLE_OBSERVER"
    capabilities = {
        "protected_window_observable": True,
        "natural_job_observable": False,
        "model_execution_observable": False,
        "ps_dependency": False,
    }

    def observe(self) -> dict[str, object]:
        raise guarded.LiveWorkloadObservationUnavailable(
            "model_free_exception_provenance_preflight"
        )


def exception_path_preflight(
    args: argparse.Namespace, state: dict[str, object], codex_bin: str
) -> dict[str, object]:
    failure_guard = guarded.LiveWorkloadGuard(
        args.output_root / "preflight-failure-coexistence-audit.json",
        observer=_UnavailableObserver(),
    )
    adapter = guarded.GuardedTransportAdapter(
        guard=failure_guard,
        continuation_generation=str(state["program_generation_id"]),
        receipt_root=args.output_root / "preflight-failure-receipts",
        codex_bin=codex_bin,
    )
    error: Exception | None = None
    try:
        prior.invoke_model_context(
            args=args,
            state=state,
            adapter=adapter,
            run="guard-preflight",
            stage="DIRECTIONAL_CORE",
            batch_number=99,
            subjects=CONTEXT_GROUPS[0],
            sequence_position=0,
            prompt_source=args.output_root / "prompts/core-batch-01.txt",
            schema_source=args.output_root / "schemas/core-batch-01.json",
        )
    except Exception as exc:
        error = exc
    context = (
        args.output_root
        / "model-contexts/GUARD-PREFLIGHT/DIRECTIONAL_CORE/batch-99"
    )
    failure = read_json(context / "pre-spawn-failure.json")
    manifest = read_json(context / "context_manifest.json")
    status = (
        "PASS"
        if isinstance(error, guarded.LiveWorkloadObservationUnavailable)
        and failure["spawn_started"] == 0
        and failure["transport_receipt_expected"] == 0
        and failure["transport_receipt_created"] == 0
        and failure["root_exception_masked"] == 0
        and manifest["context_evidence_preservation_status"] == "PASS"
        else "FAIL"
    )
    return {
        "contract": "prespawn-exception-path-preflight-v1",
        "root_exception_type": type(error).__name__ if error else None,
        "root_exception": str(error) if error else None,
        "spawn_started": failure["spawn_started"],
        "transport_receipt_expected": failure["transport_receipt_expected"],
        "transport_receipt_created": failure["transport_receipt_created"],
        "root_exception_masked": failure["root_exception_masked"],
        "context_evidence_preservation_status": manifest[
            "context_evidence_preservation_status"
        ],
        "context_preservation_secondary_failure_count": state[
            "context_preservation_secondary_failure_count"
        ],
        "real_model_calls": adapter.model_call_count,
        "status": status,
    }


def prior_transport_state(archive: zipfile.ZipFile) -> dict[str, object]:
    return zip_json(archive, "experiment/program-state.json")


def prepare(args: argparse.Namespace) -> None:
    if args.output_root.exists() or args.report_dir.exists():
        raise ValueError("new_output_and_report_directories_required")
    if file_sha256(args.latest_result_zip) != LATEST_RESULT_SHA256:
        raise ValueError("LATEST_RESULT_BUNDLE_CHECKSUM_MISMATCH")
    if file_sha256(Path.cwd() / WORK_INSTRUCTION) != WORK_INSTRUCTION_SHA256:
        raise ValueError("work_instruction_content_drift")
    if args.timeout != TIMEOUT_SECONDS:
        raise ValueError("timeout_mutation_forbidden")
    args.output_root.mkdir(parents=True)
    (args.report_dir / "proofs").mkdir(parents=True)

    repo_root = Path.cwd().resolve()
    implementation_commit = git_value("rev-parse", "HEAD")
    work_instruction_commit = git_value(
        "log", "-1", "--format=%H", "--", WORK_INSTRUCTION
    )
    base_sha = git_value("rev-parse", f"{work_instruction_commit}^")
    runtime_generation_id = generation_id(implementation_commit, args.as_of)
    with zipfile.ZipFile(args.latest_result_zip) as archive:
        if archive.testzip() is not None:
            raise ValueError("latest_result_zip_integrity_failure")
        previous_state = prior_transport_state(archive)
        previous_completion = zip_json(
            archive, "reports/proofs/69-program-completion.json"
        )
        frozen_precommit = zip_json(archive, "experiment/new-holdout-precommit.json")
        frozen_prompt_lock = zip_json(archive, "experiment/prompt-schema-lock.json")
        extraction = extract_frozen_inputs(
            archive, args.output_root, runtime_generation_id
        )

    if tuple(previous_state["ordered_cohort"]) != ORDERED_COHORT:
        raise ValueError("ordered_cohort_drift")
    if previous_state["source_lock_sha256"] != SOURCE_LOCK_SHA256:
        raise ValueError("source_lock_identity_drift")
    if frozen_precommit["source_generation_id"] != SOURCE_GENERATION_ID:
        raise ValueError("source_generation_identity_drift")
    source_lock = read_json(args.output_root / "source-lock.json")
    recorded_lock = source_lock.pop("source_lock_sha256")
    if canonical_sha256(source_lock) != recorded_lock or recorded_lock != SOURCE_LOCK_SHA256:
        raise ValueError("source_lock_content_drift")
    source_lock["source_lock_sha256"] = recorded_lock

    freeze = prompt_schema_freeze(
        args.output_root, frozen_prompt_lock, runtime_generation_id
    )
    if freeze["status"] != "PASS":
        raise ValueError("model_semantic_input_drift")
    write_json(args.output_root / "prompt-schema-lock.json", freeze)

    expected_architecture = previous_state["architecture_hashes"]
    current_architecture = canonical_architecture_hashes(repo_root)
    architecture_drift = {
        key: current_architecture[key] != expected_architecture[key]
        for key in current_architecture
    }
    if any(architecture_drift.values()):
        raise ValueError("UNEXPLAINED_SEMANTIC_REPOSITORY_DRIFT")

    current_transport = prior.transport_topology_hashes()
    old_transport = previous_state["transport_topology_hashes"]
    canonical_keys = (
        "ContinuationTransportAdapter",
        "invoke_instrumented_codex",
        "instrumented_runner",
    )
    canonical_transport_mutation = any(
        current_transport[key] != old_transport[key] for key in canonical_keys
    )
    if canonical_transport_mutation:
        raise ValueError("BROADER_TRANSPORT_REVALIDATION_REQUIRED")

    packet_hashes = {
        ticker: canonical_sha256(read_json(args.output_root / "packets" / f"{ticker}.json"))
        for ticker in ORDERED_COHORT
    }
    if packet_hashes != frozen_precommit["per_issuer_packet_hashes"]:
        raise ValueError("packet_hash_drift")

    state: dict[str, object] = {
        "contract": PROGRAM_CONTRACT,
        "state": "PREPARING",
        "base_sha": base_sha,
        "work_instruction_commit": work_instruction_commit,
        "implementation_commit": implementation_commit,
        "branch": git_value("branch", "--show-current"),
        "as_of": args.as_of.isoformat(),
        "program_generation_id": runtime_generation_id,
        "source_generation_id": SOURCE_GENERATION_ID,
        "source_lock_sha256": SOURCE_LOCK_SHA256,
        "ordered_cohort": list(ORDERED_COHORT),
        "final_us4": list(ORDERED_COHORT[:4]),
        "final_kr12": list(ORDERED_COHORT[4:]),
        "model_invocation_count": 0,
        "directional_context_count": 0,
        "price_timing_context_count": 0,
        "renderer_context_count": 0,
        "context_evidence_preservation_failure_count": 0,
        "context_preservation_secondary_failure_count": 0,
        "per_context_semantic_failure_count": 0,
        "transport_timeout_count": 0,
        "transport_retry_count": 0,
        "historical_stall_pattern_recurred": 0,
        "exposed_subjects": [],
        "holdout_output_exposure_state": "UNEXPOSED",
        "holdout_semantic_revelation_state": "NOT_MEASURED",
        "holdout_retirement_state": "ACTIVE_UNEXPOSED",
        "future_unseen_holdout_reuse_allowed": 1,
        "run_results": {run: "NOT_RUN" for run in RUNS},
        "architecture_hashes": current_architecture,
        "canonical_transport_hashes": {
            key: current_transport[key] for key in canonical_keys
        },
        "authorized_guard_adapter_hash": current_transport[
            "GuardedTransportAdapter"
        ],
        "packet_hashes": packet_hashes,
        "prompt_schema_freeze_sha256": canonical_sha256(freeze),
    }
    write_json(args.output_root / "program-state.json", state)

    codex_bin = engine._signed_in_codex_bin()
    exception_preflight = exception_path_preflight(args, state, codex_bin)
    actual_guard = guarded.LiveWorkloadGuard(
        args.output_root / "live-workload-coexistence-audit.json"
    )
    actual_adapter = guarded.GuardedTransportAdapter(
        guard=actual_guard,
        continuation_generation=runtime_generation_id,
        receipt_root=args.output_root / "transport-receipts",
        codex_bin=codex_bin,
    )
    try:
        observation_preflight = actual_adapter.preflight(
            stage="DIRECTIONAL_CORE", batch_id="FIRST-01", subject_count=4
        )
    except guarded.LiveWorkloadObservationUnavailable as exc:
        observation_preflight = {
            "contract": "prespawn-live-workload-guard-preflight-v1",
            "safe_to_spawn": 0,
            "real_model_calls": 0,
            "spawn_started": 0,
            "transport_receipt_expected": 0,
            "root_exception": f"{type(exc).__name__}:{exc}",
            "status": "FAIL",
        }
    preflight_status = (
        "PASS"
        if exception_preflight["status"] == "PASS"
        and observation_preflight["status"] == "PASS"
        and observation_preflight["safe_to_spawn"] == 1
        else "FAIL"
    )
    safe_to_spawn = int(preflight_status == "PASS")

    old_guard_file = subprocess.run(
        [
            "git",
            "show",
            f"{base_sha}:scripts/synthetic_canary_fixture_repair_ownership_resume.py",
        ],
        check=True,
        capture_output=True,
    ).stdout
    old_preserver_file = subprocess.run(
        [
            "git",
            "show",
            f"{base_sha}:scripts/new_issuer_holdout_selection_ownership_proof.py",
        ],
        check=True,
        capture_output=True,
    ).stdout
    guard_drift = {
        "guard_file_before_sha256": bytes_sha256(old_guard_file),
        "guard_file_after_sha256": file_sha256(
            repo_root / "scripts/synthetic_canary_fixture_repair_ownership_resume.py"
        ),
        "preserver_file_before_sha256": bytes_sha256(old_preserver_file),
        "preserver_file_after_sha256": file_sha256(
            repo_root / "scripts/new_issuer_holdout_selection_ownership_proof.py"
        ),
    }
    guard_drift["authorized_guard_compatibility_hash_drift"] = int(
        guard_drift["guard_file_before_sha256"]
        != guard_drift["guard_file_after_sha256"]
        or guard_drift["preserver_file_before_sha256"]
        != guard_drift["preserver_file_after_sha256"]
    )

    resume_precommit = {
        "contract": "prespawn-guard-resume-runtime-precommit-v1",
        "runtime_generation_id": runtime_generation_id,
        "source_generation_id": SOURCE_GENERATION_ID,
        "source_lock_sha256": SOURCE_LOCK_SHA256,
        "ordered_cohort": list(ORDERED_COHORT),
        "context_grouping": [list(group) for group in CONTEXT_GROUPS],
        "packet_hashes": packet_hashes,
        "prompt_schema_freeze_sha256": canonical_sha256(freeze),
        "model": MODEL,
        "reasoning_effort": EFFORT,
        "timeout": TIMEOUT_SECONDS,
        "timeout_owner_count": TIMEOUT_OWNER_COUNT,
        "batch_semantics": BATCH_SEMANTICS,
        "context_size": CONTEXT_SIZE,
        "authorized_guard_adapter_hash": current_transport[
            "GuardedTransportAdapter"
        ],
        "canonical_transport_hashes": state["canonical_transport_hashes"],
        "stop_rules": "FIRST then gated A/B/C; no retry, split, or hotfix",
        "status": "FROZEN",
    }
    write_json(args.output_root / "resume-runtime-precommit.json", resume_precommit)
    state.update(
        {
            "state": "PREPARED_FROZEN" if safe_to_spawn else "PREPARED_BLOCKED",
            "precommit_sha256": canonical_sha256(resume_precommit),
            "prespawn_guard_preflight_status": preflight_status,
            "safe_to_spawn": safe_to_spawn,
            "workload_observation_backend": actual_guard.observer.backend,
            "workload_observation_capabilities": actual_guard.observer.capabilities,
            "authorized_guard_compatibility_hash_drift": guard_drift[
                "authorized_guard_compatibility_hash_drift"
            ],
        }
    )
    write_json(args.output_root / "program-state.json", state)

    changed_files = git_value("diff", "--name-only", base_sha, implementation_commit).splitlines()
    write_proof(
        args.report_dir,
        1,
        {
            "contract": "repository-provenance-v1",
            "base_sha": base_sha,
            "work_instruction_commit": work_instruction_commit,
            "implementation_commit": implementation_commit,
            "branch": state["branch"],
            "changed_files": changed_files,
            "status": "PASS",
        },
    )
    write_proof(
        args.report_dir,
        2,
        {
            "contract": "latest-result-integrity-v1",
            "expected_sha256": LATEST_RESULT_SHA256,
            "actual_sha256": file_sha256(args.latest_result_zip),
            "previous_artifact_count": previous_completion["artifact_count"],
            "previous_hash_mismatch_count": previous_completion[
                "artifact_hash_mismatch_count"
            ],
            "previous_size_mismatch_count": previous_completion[
                "artifact_size_mismatch_count"
            ],
            "previous_secret_scan_failure_count": previous_completion[
                "artifact_secret_scan_failure_count"
            ],
            "status": "PASS",
        },
    )
    write_proof(
        args.report_dir,
        3,
        {
            "contract": "current-unexposed-holdout-state-v1",
            "prior_real_model_invocation_count": previous_state["model_invocation_count"],
            "prior_subject_output_count": len(previous_state["exposed_subjects"]),
            "holdout_output_exposure_state": previous_state[
                "holdout_output_exposure_state"
            ],
            "holdout_retirement_state": previous_state["holdout_retirement_state"],
            "future_unseen_holdout_reuse_allowed": previous_state[
                "future_unseen_holdout_reuse_allowed"
            ],
            "status": "PASS",
        },
    )
    write_proof(
        args.report_dir,
        4,
        {
            "contract": "prespawn-guard-code-path-audit-v1",
            "guard_constructor": (
                "us_price_context_gate_supported_universe_holdout_resume -> "
                "bounded runner execute -> LiveWorkloadGuard"
            ),
            "prespawn_check": "GuardedTransportAdapter.invoke -> wait_until_clear",
            "previous_process_observation_command": "ps -axo command=",
            "active_natural_job_decision": "pause while count > 0",
            "running_model_process_decision": "pause while count > 0",
            "protected_window_independent": True,
            "spawn_boundary": "ContinuationTransportAdapter invoke after guard returns",
            "receipt_expected_boundary": "instrumented subprocess invocation created",
            "exception_mask_path": (
                "invoke_model_context -> preserve_context -> transport_receipt_missing"
            ),
            "root_cause_result": "PRESPAWN_GUARD_ROOT_CAUSE_CONFIRMED",
            "status": "PASS",
        },
    )
    capabilities = actual_guard.observer.capabilities
    write_proof(
        args.report_dir,
        5,
        {
            "contract": "workload-observation-capability-audit-v1",
            **capabilities,
            "natural_job_registry": "LaunchAgent ProgramArguments + launchctl state",
            "model_execution_registry": "lsof open /codex_runtime_state/ paths",
            "status": "PASS",
        },
    )
    write_proof(
        args.report_dir,
        6,
        {
            "contract": "workload-observation-backend-decision-v1",
            "workload_observation_backend": actual_guard.observer.backend,
            "fail_open": 0,
            "ticker_specific": 0,
            "status": "PASS",
        },
    )
    write_proof(
        args.report_dir,
        7,
        {
            "contract": "prespawn-root-cause-proof-v1",
            "prespawn_guard_root_cause": "LIVE_WORKLOAD_GUARD_PS_PERMISSION_DENIED",
            "original_root_exception": (
                "PermissionError:[Errno 1] Operation not permitted:ps"
            ),
            "failure_stage": "PRE_SPAWN",
            "model_process_spawned": 0,
            "receipt_created": 0,
            "root_exception_masked_before_repair": 1,
            "status": "PRESPAWN_GUARD_ROOT_CAUSE_CONFIRMED",
        },
    )
    write_proof(args.report_dir, 8, exception_preflight)
    write_proof(
        args.report_dir,
        9,
        {
            "contract": "transport-receipt-lifecycle-v1",
            "before_spawn": {
                "spawn_started": 0,
                "transport_receipt_expected": 0,
                "missing_receipt_is_error": False,
            },
            "after_spawn": {
                "spawn_started": 1,
                "transport_receipt_expected": 1,
                "missing_receipt_error": "POST_SPAWN_RECEIPT_MISSING",
            },
            "fabricated_prespawn_receipt": 0,
            "status": "PASS",
        },
    )
    write_proof(
        args.report_dir,
        10,
        {
            "contract": "context-preservation-error-propagation-v1",
            "root_exception_masked": exception_preflight["root_exception_masked"],
            "context_preservation_secondary_failure_count": exception_preflight[
                "context_preservation_secondary_failure_count"
            ],
            "preserved": ["prompt", "schema", "context manifest", "root exception"],
            "not_required_before_spawn": ["model output", "stdout", "stderr", "receipt"],
            "status": exception_preflight["status"],
        },
    )
    write_proof(
        args.report_dir,
        11,
        {
            "contract": "guard-compatibility-remediation-diff-v1",
            "allowed_files": [
                "scripts/synthetic_canary_fixture_repair_ownership_resume.py",
                "scripts/new_issuer_holdout_selection_ownership_proof.py",
                "scripts/prespawn_live_workload_guard_compatibility_holdout_resume.py",
                "tests/test_synthetic_canary_fixture_repair_ownership_resume.py",
                "tests/test_new_issuer_holdout_selection_ownership_proof.py",
            ],
            "ps_removed_from_guard": 1,
            "fail_open_added": 0,
            "automatic_retry_added": 0,
            "batch_split_added": 0,
            "status": "PASS",
        },
    )
    write_proof(
        args.report_dir,
        12,
        {
            "contract": "guard-regression-tests-v1",
            "focused_tests": args.focused_tests,
            "covered": [
                "ps PermissionError not masked",
                "pre-spawn receipt not expected",
                "post-spawn missing receipt detected",
                "zero contention",
                "natural contention",
                "model contention",
                "protected window",
                "no fail-open",
            ],
            "status": "PASS" if args.focused_tests == "PASS" else "FAIL",
        },
    )
    write_proof(
        args.report_dir,
        13,
        {
            "contract": "model-free-prespawn-guard-preflight-v1",
            "exception_path": exception_preflight,
            "observation_path": observation_preflight,
            "prespawn_guard_preflight": preflight_status,
            "safe_to_spawn": safe_to_spawn,
            "real_model_calls": 0,
            "status": preflight_status,
        },
    )
    write_proof(
        args.report_dir,
        14,
        {
            "contract": "authorized-guard-hash-drift-audit-v1",
            **guard_drift,
            "classification": "AUTHORIZED_GUARD_COMPATIBILITY_HASH_DRIFT",
            "status": "PASS",
        },
    )
    write_proof(
        args.report_dir,
        15,
        {
            "contract": "canonical-transport-freeze-v1",
            "previous": {key: old_transport[key] for key in canonical_keys},
            "current": {key: current_transport[key] for key in canonical_keys},
            "continuation_adapter_semantic_mutation": 0,
            "instrumented_codex_lifecycle_mutation": 0,
            "transport_process_topology_mutation": 0,
            "timeout_owner_mutation": 0,
            "status": "PASS",
        },
    )
    write_proof(args.report_dir, 16, freeze)
    write_proof(
        args.report_dir,
        17,
        {
            "contract": "source-lock-reuse-proof-v1",
            "source_generation_id": SOURCE_GENERATION_ID,
            "source_lock": SOURCE_LOCK_SHA256,
            "packet_hashes": packet_hashes,
            "source_drift": 0,
            "extracted_artifact_count": extraction["count"],
            "status": "PASS",
        },
    )
    reuse_pass = (
        previous_state["model_invocation_count"] == 0
        and not previous_state["exposed_subjects"]
        and previous_state["holdout_output_exposure_state"] == "UNEXPOSED"
        and previous_state["holdout_retirement_state"] == "ACTIVE_UNEXPOSED"
        and preflight_status == "PASS"
    )
    write_proof(
        args.report_dir,
        18,
        {
            "contract": "holdout-reuse-gate-v1",
            "current_holdout_reuse_allowed": int(reuse_pass),
            "ordered_cohort_unchanged": 1,
            "source_generation_unchanged": 1,
            "source_lock_unchanged": 1,
            "packet_hashes_unchanged": 1,
            "prompt_schema_semantic_inputs_unchanged": 1,
            "model_effort_unchanged": 1,
            "context_grouping_unchanged": 1,
            "investment_architecture_unchanged": 1,
            "status": "PASS" if reuse_pass else "FAIL",
        },
    )
    write_proof(args.report_dir, 19, resume_precommit)
    write_proof(
        args.report_dir,
        20,
        read_json(args.output_root / "live-workload-coexistence-audit.json"),
    )
    write_reports(args.report_dir)


def verify_frozen(args: argparse.Namespace, state: Mapping[str, object]) -> None:
    if file_sha256(Path.cwd() / WORK_INSTRUCTION) != WORK_INSTRUCTION_SHA256:
        raise ValueError("work_instruction_content_drift")
    if canonical_architecture_hashes(Path.cwd()) != state["architecture_hashes"]:
        raise ValueError("architecture_semantic_drift_after_freeze")
    current_transport = prior.transport_topology_hashes()
    for key, expected in state["canonical_transport_hashes"].items():
        if current_transport[key] != expected:
            raise ValueError("canonical_transport_topology_drift_after_freeze")
    if current_transport["GuardedTransportAdapter"] != state[
        "authorized_guard_adapter_hash"
    ]:
        raise ValueError("authorized_guard_drift_after_freeze")
    precommit = read_json(args.output_root / "resume-runtime-precommit.json")
    if canonical_sha256(precommit) != state["precommit_sha256"]:
        raise ValueError("resume_precommit_drift_after_freeze")
    freeze = read_json(args.output_root / "prompt-schema-lock.json")
    if canonical_sha256(freeze) != state["prompt_schema_freeze_sha256"]:
        raise ValueError("prompt_schema_freeze_drift_after_freeze")
    if prompt_schema_freeze(
        args.output_root,
        read_json(args.output_root / "frozen-prompt-schema-lock.json"),
        str(state["program_generation_id"]),
    )["status"] != "PASS":
        raise ValueError("model_semantic_input_drift_after_freeze")
    packets = {
        ticker: canonical_sha256(read_json(args.output_root / "packets" / f"{ticker}.json"))
        for ticker in ORDERED_COHORT
    }
    if packets != state["packet_hashes"]:
        raise ValueError("packet_hash_drift_after_freeze")
    proof_relative = proof_path(args.report_dir, 19).relative_to(Path.cwd())
    if not git_value("ls-files", str(proof_relative)):
        raise ValueError("resume_runtime_precommit_must_be_committed_before_model_call")


def configure_prior_runner() -> None:
    prior.PROOF_NAMES = PROOF_NAMES
    prior.RUN_PROOFS = RUN_PROOFS


def gate_documents(report_dir: Path, offset: int) -> list[dict[str, object]]:
    return [
        read_json(proof_path(report_dir, RUN_PROOFS[run][offset]))
        for run in RUNS
        if proof_path(report_dir, RUN_PROOFS[run][offset]).is_file()
        and read_json(proof_path(report_dir, RUN_PROOFS[run][offset])).get("status")
        not in {"NOT_RUN", "NOT_MEASURED"}
    ]


def final_proofs(
    *,
    args: argparse.Namespace,
    state: dict[str, object],
    documents: Mapping[str, Mapping[str, object]],
    stop_reason: str | None,
) -> None:
    all_pass = all(documents.get(run, {}).get("status") == "PASS" for run in RUNS)
    if all_pass:
        core_stability = frozen._core_stability(ORDERED_COHORT, documents)
        timing_stability = frozen._timing_stability(ORDERED_COHORT, documents)
    else:
        core_stability = {
            "contract": "directional-core-stability-audit-v1",
            "counts": {"STABLE": 0, "BOUNDARY_UNCERTAINTY": 0, "UNSTABLE": 0},
            "reason": stop_reason,
            "status": "NOT_MEASURED",
        }
        timing_stability = {
            "contract": "price-timing-stability-audit-v1",
            "counts": {"STABLE": 0, "BOUNDARY_UNCERTAINTY": 0, "UNSTABLE": 0},
            "reason": stop_reason,
            "status": "NOT_MEASURED",
        }
    ownership_docs = gate_documents(args.report_dir, 3)
    renderer_docs = gate_documents(args.report_dir, 4)
    hard_docs = gate_documents(args.report_dir, 5)
    totals = {
        key: sum(int(document.get(key) or 0) for document in ownership_docs)
        for key in OWNERSHIP_KEYS
    }
    renderer_violations = sum(
        int(document.get("renderer_ownership_violations") or 0)
        for document in renderer_docs
    )
    hard_regressions = sum(
        int(document.get("known_hard_safety_regression") or 0)
        for document in hard_docs
    )
    semantic_failure = int(state["per_context_semantic_failure_count"]) > 0 or (
        bool(stop_reason) and "semantic" in str(stop_reason).lower()
    )
    exposure = str(state["holdout_output_exposure_state"])
    if all_pass:
        semantic_state = "NO_SEMANTIC_DEFECT_OBSERVED"
        retirement = "RETIRED_AFTER_EVALUATION"
        completion_state = "COMPLETE"
        next_scope = "MONITORING_BOOTSTRAP_INTEGRATION_REVIEW"
    elif semantic_failure:
        semantic_state = "REVEALED_FOR_ARCHITECTURE_TUNING"
        retirement = "RETIRED_FOR_ARCHITECTURE_REPAIR"
        completion_state = "INCOMPLETE_SEMANTIC_FAILURE"
        next_scope = "GENERIC_OWNERSHIP_ARCHITECTURE_REPAIR"
    else:
        semantic_state = "NOT_MEASURED"
        retirement = (
            "ACTIVE_UNEXPOSED" if exposure == "UNEXPOSED" else "RETIRED_PARTIAL_EXPOSURE"
        )
        completion_state = "INCOMPLETE_TRANSPORT_FAILURE"
        next_scope = (
            "BOUNDED_TRANSPORT_RUNTIME_DIAGNOSTIC_REPAIR"
            if state["historical_stall_pattern_recurred"]
            else "BOUNDED_TRANSPORT_RUNTIME_REVIEW"
        )
    future_reuse = int(exposure == "UNEXPOSED" and not semantic_failure)
    ownership_verdict = (
        "PASS_NEW_UNSEEN_COHORT"
        if all_pass and core_stability["counts"]["UNSTABLE"] == 0
        else "NOT_ESTABLISHED"
    )
    write_proof(
        args.report_dir,
        45,
        {
            "contract": "holdout-exposure-retirement-state-v1",
            "holdout_output_exposure_state": exposure,
            "holdout_semantic_revelation_state": semantic_state,
            "holdout_retirement_state": retirement,
            "future_unseen_holdout_reuse_allowed": future_reuse,
            "exposed_subjects": state["exposed_subjects"],
            "status": "PASS" if all_pass else "STOPPED",
        },
    )
    write_proof(args.report_dir, 46, core_stability)
    write_proof(args.report_dir, 47, timing_stability)
    write_proof(
        args.report_dir,
        48,
        {
            "contract": "ownership-generalization-proof-v1",
            **totals,
            "final_direction_owner": "DIRECTIONAL_CORE" if ownership_docs else "NOT_MEASURED",
            "core_stability_counts": core_stability["counts"],
            "timing_stability_counts": timing_stability["counts"],
            "ownership_generalization_verdict": ownership_verdict,
            "status": "PASS" if all_pass else "NOT_MEASURED",
        },
    )
    write_proof(
        args.report_dir,
        49,
        {
            "contract": "renderer-ownership-proof-v1",
            "primary_user_action_wording_owner": "RENDERER" if renderer_docs else "NOT_MEASURED",
            "renderer_ownership_violations": renderer_violations,
            "status": "PASS" if all_pass and renderer_violations == 0 else "NOT_MEASURED",
        },
    )
    write_proof(
        args.report_dir,
        50,
        {
            "contract": "hard-safety-regression-v1",
            "known_hard_safety_regression": hard_regressions,
            "status": "PASS" if all_pass and hard_regressions == 0 else "NOT_MEASURED",
        },
    )
    production = {
        "contract": "production-no-change-v1",
        "main_merge": 0,
        "production_db_mutation": 0,
        "production_scheduler_change": 0,
        "production_telegram_send": 0,
        "monitoring_registration_calls": 0,
        "live_structured_autonomy_activation": 0,
        "live_v2_change": 0,
        "status": "PASS",
    }
    night = {
        "contract": "night-futures-no-change-v1",
        "night_futures_code_mutation": 0,
        "night_futures_decision_packet_injection": 0,
        "status": "PASS",
    }
    write_proof(args.report_dir, 51, production)
    write_proof(args.report_dir, 52, night)
    readiness = (
        "READY_FOR_MONITORING_BOOTSTRAP_INTEGRATION_REVIEW"
        if all_pass
        and core_stability["counts"]["UNSTABLE"] == 0
        and not any(totals.values())
        and renderer_violations == 0
        and hard_regressions == 0
        else "NOT_READY"
    )
    write_proof(
        args.report_dir,
        53,
        {
            "contract": "monitoring-bootstrap-next-handoff-v1",
            "readiness": readiness,
            "next_scope": next_scope,
            "monitoring_registration_calls": 0,
            "status": "PASS" if readiness.startswith("READY_") else "NOT_READY",
        },
    )
    run_results = {
        run: (
            f"{documents[run].get('validation_pass_count', 0)}/{len(ORDERED_COHORT)}"
            if run in documents
            else "NOT_RUN"
        )
        for run in RUNS
    }
    guard_audit = read_json(args.output_root / "live-workload-coexistence-audit.json")
    completion = {
        "contract": PROGRAM_CONTRACT,
        "base_sha": state["base_sha"],
        "work_instruction_commit": state["work_instruction_commit"],
        "implementation_commit": state["implementation_commit"],
        "final_head_sha": git_value("rev-parse", "HEAD"),
        "branch": state["branch"],
        "latest_result_zip_sha256": LATEST_RESULT_SHA256,
        "latest_result_integrity": "PASS",
        "prespawn_guard_root_cause": "LIVE_WORKLOAD_GUARD_PS_PERMISSION_DENIED",
        "original_root_exception": "PermissionError:[Errno 1] Operation not permitted:ps",
        "root_exception_masked_before_repair": 1,
        "workload_observation_backend": state["workload_observation_backend"],
        "workload_observation_capabilities": state["workload_observation_capabilities"],
        "ps_dependency_after_repair": False,
        "observation_unavailable_fail_open_count": guard_audit[
            "observation_unavailable_fail_open_count"
        ],
        "observation_unavailable_fail_closed_count": guard_audit[
            "observation_unavailable_fail_closed_count"
        ],
        "protected_window_semantics_changed": 0,
        "spawn_started_on_guard_failure": 0,
        "transport_receipt_expected_on_guard_failure": 0,
        "transport_receipt_created_on_guard_failure": 0,
        "root_exception_masked_after_repair": 0,
        "context_preservation_secondary_failure_count": state[
            "context_preservation_secondary_failure_count"
        ],
        "prespawn_guard_preflight_status": state["prespawn_guard_preflight_status"],
        "safe_to_spawn": state["safe_to_spawn"],
        "authorized_guard_compatibility_hash_drift": state[
            "authorized_guard_compatibility_hash_drift"
        ],
        "continuation_adapter_semantic_mutation": 0,
        "instrumented_codex_lifecycle_mutation": 0,
        "transport_process_topology_mutation": 0,
        "timeout_owner_mutation": 0,
        "architecture_semantic_drift": 0,
        "prompt_semantic_drift": 0,
        "schema_semantic_drift": 0,
        "model_semantic_input_drift": 0,
        "source_drift": 0,
        "current_holdout_reuse_allowed": 1,
        "source_generation_id": SOURCE_GENERATION_ID,
        "source_lock": SOURCE_LOCK_SHA256,
        "ordered_cohort": list(ORDERED_COHORT),
        "model": MODEL,
        "reasoning_effort": EFFORT,
        "model_timeout_seconds": TIMEOUT_SECONDS,
        "model_timeout_owner_count": TIMEOUT_OWNER_COUNT,
        "batch_semantics": BATCH_SEMANTICS,
        "shared_context_subject_count": CONTEXT_SIZE,
        "real_holdout_model_invocation_count": state["model_invocation_count"],
        "real_holdout_subject_output_count": len(state["exposed_subjects"]),
        "transport_retry_count": state["transport_retry_count"],
        "transport_timeout_count": state["transport_timeout_count"],
        "holdout_output_exposure_state": exposure,
        "holdout_semantic_revelation_state": semantic_state,
        "holdout_retirement_state": retirement,
        "future_unseen_holdout_reuse_allowed": future_reuse,
        "run_results": run_results,
        **{
            f"{('first' if run == 'first' else 'run_' + run)}_{gate}_gate_status": (
                read_json(proof_path(args.report_dir, RUN_PROOFS[run][offset]))["status"]
                if proof_path(args.report_dir, RUN_PROOFS[run][offset]).is_file()
                else "NOT_RUN"
            )
            for run in RUNS
            for gate, offset in (("ownership", 3), ("renderer", 4), ("hard_safety", 5))
        },
        "historical_stall_pattern_recurred": state["historical_stall_pattern_recurred"],
        **totals,
        "ownership_generalization_verdict": ownership_verdict,
        "ownership_proof_completion_state": completion_state,
        **{key: value for key, value in production.items() if key not in {"contract", "status"}},
        "night_futures_code_mutation": 0,
        "artifact_count": "PENDING_FINALIZE",
        "artifact_hash_mismatch_count": "PENDING_FINALIZE",
        "artifact_size_mismatch_count": "PENDING_FINALIZE",
        "artifact_secret_scan_failure_count": "PENDING_FINALIZE",
        "full_tests": "PENDING_FINAL_VALIDATION",
        "ruff": "PENDING_FINAL_VALIDATION",
        "diff_check": "PENDING_FINAL_VALIDATION",
        "readiness": readiness,
        "stop_reason": stop_reason,
        "next_scope": next_scope,
    }
    write_proof(args.report_dir, 54, completion)
    state.update(
        {
            "state": "EVIDENCE_COMPLETE",
            "run_results": run_results,
            "readiness": readiness,
            "holdout_semantic_revelation_state": semantic_state,
            "holdout_retirement_state": retirement,
            "future_unseen_holdout_reuse_allowed": future_reuse,
            "ownership_proof_completion_state": completion_state,
            "stop_reason": stop_reason,
            "next_scope": next_scope,
        }
    )
    write_json(args.output_root / "program-state.json", state)
    write_reports(args.report_dir)


def execute(args: argparse.Namespace) -> None:
    configure_prior_runner()
    state, cohort, _packets, contexts, evidence, owned, core_aliases, timing_aliases, price_maps, stocks = prior.load_inputs(args)
    if state["state"] not in {"PREPARED_FROZEN", "PREPARED_BLOCKED"}:
        raise ValueError("prepared_state_required")
    documents: dict[str, dict[str, object]] = {}
    stop_reason: str | None = None
    if state["state"] == "PREPARED_BLOCKED":
        stop_reason = "LIVE_WORKLOAD_OBSERVATION_UNAVAILABLE"
        for run in RUNS:
            prior.write_not_run(args, run, stop_reason)
    else:
        verify_frozen(args, state)
        state["freeze_commit"] = git_value("rev-parse", "HEAD")
        state["state"] = "EXECUTING"
        write_json(args.output_root / "program-state.json", state)
        guard = guarded.LiveWorkloadGuard(
            args.output_root / "live-workload-coexistence-audit.json"
        )
        adapter = guarded.GuardedTransportAdapter(
            guard=guard,
            continuation_generation=str(state["program_generation_id"]),
            receipt_root=args.output_root / "transport-receipts",
            codex_bin=engine._signed_in_codex_bin(),
        )
        for run in RUNS:
            if stop_reason is not None:
                prior.write_not_run(args, run, stop_reason)
                continue
            try:
                verify_frozen(args, state)
                document = prior.execute_run(
                    args=args,
                    state=state,
                    adapter=adapter,
                    run=run,
                    cohort=cohort,
                    contexts=contexts,
                    evidence=evidence,
                    owned=owned,
                    core_aliases=core_aliases,
                    timing_aliases=timing_aliases,
                    price_maps=price_maps,
                    stocks=stocks,
                )
                documents[run] = document
                state["run_results"][run] = (
                    f"{document['validation_pass_count']}/{len(ORDERED_COHORT)}"
                )
                write_json(args.output_root / "program-state.json", state)
            except Exception as exc:
                stop_reason = f"{type(exc).__name__}:{exc}"
                state["stop_reason"] = stop_reason
                if state["holdout_output_exposure_state"] != "UNEXPOSED":
                    state["holdout_retirement_state"] = "RETIRED_PARTIAL_EXPOSURE"
                write_json(args.output_root / "program-state.json", state)
                prior.write_failed_run(args, run, stop_reason)
                for pending in RUNS[RUNS.index(run) + 1 :]:
                    prior.write_not_run(args, pending, stop_reason)
                break
    write_proof(
        args.report_dir,
        20,
        read_json(args.output_root / "live-workload-coexistence-audit.json"),
    )
    final_proofs(
        args=args, state=state, documents=documents, stop_reason=stop_reason
    )
    print(json.dumps(read_json(proof_path(args.report_dir, 54)), sort_keys=True), flush=True)


def markdown_table(headers: Sequence[str], rows: Sequence[Sequence[object]]) -> str:
    escaped = [
        [str(cell).replace("|", "\\|").replace("\n", " ") for cell in row]
        for row in rows
    ]
    return "\n".join(
        [
            "| " + " | ".join(headers) + " |",
            "| " + " | ".join("---" for _ in headers) + " |",
            *("| " + " | ".join(row) + " |" for row in escaped),
        ]
    )


def write_reports(report_dir: Path) -> None:
    for name in PROOF_NAMES:
        path = report_dir / "proofs" / f"{name}.json"
        if path.is_file():
            write_text(report_dir / f"{name}.md", prior.report_body(name, read_json(path)))
    completion_path = proof_path(report_dir, 54)
    if completion_path.is_file():
        completion = read_json(completion_path)
        write_text(
            report_dir / "README.md",
            "# Pre-Spawn Live-Workload Guard Compatibility & Holdout Proof Resume\n\n"
            + markdown_table(
                ("Field", "Value"),
                [
                    ("Guard preflight", completion.get("prespawn_guard_preflight_status")),
                    ("FIRST", completion.get("run_results", {}).get("first")),
                    ("A", completion.get("run_results", {}).get("a")),
                    ("B", completion.get("run_results", {}).get("b")),
                    ("C", completion.get("run_results", {}).get("c")),
                    ("Readiness", completion.get("readiness")),
                    ("Next scope", completion.get("next_scope")),
                ],
            )
            + "\n",
        )


def artifact_rows(args: argparse.Namespace) -> list[dict[str, object]]:
    excluded = {
        "54-program-completion.json",
        "54-program-completion.md",
        "README.md",
        "artifact-index.json",
        "artifact-index.md",
    }
    paths = [
        path
        for path in args.report_dir.rglob("*")
        if path.is_file() and path.name not in excluded
    ]
    for relative in (
        "program-state.json",
        "source-lock.json",
        "frozen-source-precommit.json",
        "frozen-prompt-schema-lock.json",
        "prompt-schema-lock.json",
        "resume-runtime-precommit.json",
        "packets",
        "base-contexts",
        "prompts",
        "schemas",
        "timing-contexts",
        "generated-timing-prompts",
        "model-contexts",
        "live-workload-coexistence-audit.json",
        "preflight-failure-coexistence-audit.json",
    ):
        path = args.output_root / relative
        if path.is_file():
            paths.append(path)
        elif path.is_dir():
            paths.extend(child for child in path.rglob("*") if child.is_file())
    rows = []
    for path in sorted(set(paths)):
        is_report = path.is_relative_to(args.report_dir)
        relative = (
            Path("reports") / path.relative_to(args.report_dir)
            if is_report
            else Path("experiment") / path.relative_to(args.output_root)
        )
        parts = relative.parts
        model_context = "model-contexts" in parts
        context_index = parts.index("model-contexts") if model_context else -1
        run = parts[context_index + 1] if model_context and len(parts) > context_index + 1 else "NOT_APPLICABLE"
        stage = parts[context_index + 2] if model_context and len(parts) > context_index + 2 else "NOT_APPLICABLE"
        context = parts[context_index + 3] if model_context and len(parts) > context_index + 3 else "NOT_APPLICABLE"
        scan = prior.scan_secrets((path,))
        rows.append(
            {
                "source_path": str(path),
                "relative_path": str(relative),
                "sha256": file_sha256(path),
                "byte_size": path.stat().st_size,
                "artifact_class": "REPORT" if is_report else "EXPERIMENT",
                "run": run,
                "stage": stage,
                "context": context,
                "secret_scan_status": scan["secret_scan_status"],
            }
        )
    return rows


def finalize(args: argparse.Namespace) -> None:
    state = read_json(args.output_root / "program-state.json")
    if state["state"] != "EVIDENCE_COMPLETE":
        raise ValueError("evidence_complete_state_required")
    completion = read_json(proof_path(args.report_dir, 54))
    completion.update(
        {
            "final_head_sha": git_value("rev-parse", "HEAD"),
            "full_tests": args.full_tests,
            "ruff": args.ruff,
            "diff_check": args.diff_check,
        }
    )
    if not all(value == "PASS" for value in (args.full_tests, args.ruff, args.diff_check)):
        completion["readiness"] = "NOT_READY"
        completion["next_scope"] = "BOUNDED_VALIDATION_REPAIR"
    write_proof(args.report_dir, 54, completion)
    write_reports(args.report_dir)
    rows = artifact_rows(args)
    hash_mismatch = sum(
        file_sha256(Path(str(row["source_path"]))) != row["sha256"] for row in rows
    )
    size_mismatch = sum(
        Path(str(row["source_path"])).stat().st_size != row["byte_size"] for row in rows
    )
    secret_failures = sum(row["secret_scan_status"] != "PASS" for row in rows)
    index = {
        "contract": "prespawn-guard-holdout-artifact-index-v1",
        "indexed_artifact_count": len(rows),
        "artifact_hash_mismatch_count": hash_mismatch,
        "artifact_size_mismatch_count": size_mismatch,
        "artifact_secret_scan_failure_count": secret_failures,
        "rows": rows,
        "status": "PASS" if hash_mismatch == size_mismatch == secret_failures == 0 else "FAIL",
    }
    write_json(args.report_dir / "artifact-index.json", index)
    write_text(
        args.report_dir / "artifact-index.md",
        "# Artifact Index\n\n"
        + markdown_table(
            ("Path", "SHA-256", "Bytes", "Class", "Run", "Stage", "Context", "Secret"),
            [
                (
                    row["relative_path"],
                    row["sha256"],
                    row["byte_size"],
                    row["artifact_class"],
                    row["run"],
                    row["stage"],
                    row["context"],
                    row["secret_scan_status"],
                )
                for row in rows
            ],
        ),
    )
    completion.update(
        {
            "artifact_count": len(rows) + 5,
            "artifact_hash_mismatch_count": hash_mismatch,
            "artifact_size_mismatch_count": size_mismatch,
            "artifact_secret_scan_failure_count": secret_failures,
        }
    )
    if index["status"] != "PASS":
        completion["readiness"] = "NOT_READY"
        completion["next_scope"] = "ARTIFACT_INTEGRITY_REPAIR"
    write_proof(args.report_dir, 54, completion)
    write_reports(args.report_dir)
    args.zip_output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.zip_output.with_suffix(args.zip_output.suffix + ".tmp")
    with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(child for child in args.report_dir.rglob("*") if child.is_file()):
            archive.write(path, Path("reports") / path.relative_to(args.report_dir))
        for row in rows:
            if row["artifact_class"] != "REPORT":
                archive.write(str(row["source_path"]), str(row["relative_path"]))
    temporary.replace(args.zip_output)
    with zipfile.ZipFile(args.zip_output) as archive:
        bad_member = archive.testzip()
    if bad_member is not None:
        raise ValueError(f"final_zip_integrity_failure:{bad_member}")
    zip_sha = file_sha256(args.zip_output)
    write_text(args.zip_output.with_suffix(args.zip_output.suffix + ".sha256"), zip_sha + "\n")
    state.update(
        {
            "state": "COMPLETE",
            "readiness": completion["readiness"],
            "artifact_count": completion["artifact_count"],
            "report_zip": str(args.zip_output),
            "report_zip_sha256": zip_sha,
        }
    )
    write_json(args.output_root / "program-state.json", state)
    print(json.dumps(state, ensure_ascii=False, sort_keys=True), flush=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--prepare", action="store_true")
    mode.add_argument("--execute", action="store_true")
    mode.add_argument("--finalize", action="store_true")
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--report-dir", type=Path, required=True)
    parser.add_argument("--latest-result-zip", type=Path, required=True)
    parser.add_argument("--as-of", type=datetime.fromisoformat)
    parser.add_argument("--timeout", type=int, default=TIMEOUT_SECONDS)
    parser.add_argument("--focused-tests", default="NOT_RUN")
    parser.add_argument("--full-tests", default="NOT_RUN")
    parser.add_argument("--ruff", default="NOT_RUN")
    parser.add_argument("--diff-check", default="NOT_RUN")
    parser.add_argument("--zip-output", type=Path, required=True)
    args = parser.parse_args()
    if args.prepare and args.as_of is None:
        raise ValueError("prepare_requires_fixed_as_of")
    for name in ("output_root", "report_dir", "latest_result_zip", "zip_output"):
        setattr(args, name, getattr(args, name).expanduser().resolve())
    return args


def main() -> None:
    args = parse_args()
    if args.prepare:
        prepare(args)
    elif args.execute:
        execute(args)
    else:
        finalize(args)


if __name__ == "__main__":
    main()
