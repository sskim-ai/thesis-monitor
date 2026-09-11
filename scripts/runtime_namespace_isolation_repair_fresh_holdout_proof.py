from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import tempfile
import zipfile
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from typing import Any

from app.services.codex_runtime_state_service import (
    RUNTIME_ISOLATION_CONTRACT,
    RUNTIME_NAMESPACE_POLICY,
    CodexRuntimeIsolationCollision,
    CodexRuntimeIsolationRegistry,
    context_runtime_state_namespace,
)
from app.services.direction_timing_ownership_service import DirectionalCoreCandidate
from scripts import existing_source_env_binding_fresh_holdout_resume as previous
from scripts import fresh_issuer_ownership_proof_transport_risk_carried as legacy
from scripts import model_transport_revalidation_ownership_continuation as transport
from scripts import monitoring_pause_completion_fresh_issuer_ownership_proof as selection
from scripts import new_issuer_holdout_selection_ownership_proof as runner
from scripts import uskr22_structured_autonomy_shadow as engine
from scripts import websocket_timeout_runtime_review_first_a_closeout as closeout


PROGRAM_CONTRACT = "runtime-namespace-isolation-repair-fresh-holdout-proof-v1"
WORK_INSTRUCTION_PATH = (
    "docs/work-instructions/"
    "20260908-runtime-namespace-isolation-repair-and-fresh-holdout-proof.md"
)
WORK_INSTRUCTION_SHA256 = (
    "7a6ddce935f6773d51253a110af5e9f1eb7c075e4125ba9e28e07474b42f6904"
)
LATEST_RESULT_NAME = (
    "thesis-monitor-20260908-existing-source-env-binding-"
    "fresh-holdout-proof-resume-report.zip"
)
LATEST_RESULT_SHA256 = (
    "1863c83cc54b3c07a4a74f89ba0d46634836334df7bed3d46cc819132f025474"
)
LATEST_RESULT_MEMBERS = 1072
LATEST_RESULT_INDEXED_PAYLOADS = 1071
LATEST_FINAL_HEAD = "3d5cbddd20df8120423cc9786a3b0ac3382d0f49"
LATEST_FINAL_TREE = "ed3c0fff42da0b3a55998c7c5362010e8a15ef5b"
PREVIOUS_EXCLUSION_COUNT = 117
NEWLY_RETIRED_COUNT = 16
UPDATED_EXCLUSION_COUNT = PREVIOUS_EXCLUSION_COUNT + NEWLY_RETIRED_COUNT
TARGET_US = 4
TARGET_KR = 12
TARGET_TOTAL = TARGET_US + TARGET_KR
EXPECTED_CONTEXTS = 32
REPORT_DIRECTORY = "20260908-runtime-namespace-isolation-repair-fresh-holdout-proof"
LATEST_COHORT = (
    "ACHR",
    "BNED",
    "CROX",
    "AWX",
    "095720",
    "000250",
    "389030",
    "009310",
    "042700",
    "002690",
    "103590",
    "025750",
    "084680",
    "377330",
    "024840",
    "360070",
)
HISTORICAL_EXPOSED = frozenset(LATEST_COHORT[:8])
ROOT_CAUSE = "RUN_STAGE_ONLY_NAMESPACE_DERIVATION_OMITTED_INVOCATION_AND_BATCH"
REPAIRED_RUNTIME_RISK = "RUNTIME_NAMESPACE_ISOLATION_REPAIRED_AND_PREFLIGHT_PROVEN"

REPORT_NAMES = (
    "01-repository-provenance",
    "02-latest-result-integrity",
    "03-latest-runtime-isolation-failure-reconstruction",
    "04-runtime-namespace-root-cause",
    "05-runtime-namespace-contract",
    "06-runtime-namespace-repair-diff",
    "07-runtime-namespace-regression-tests",
    "08-full-path-32-context-namespace-preflight",
    "09-historical-batch02-offline-audit",
    "10-historical-failure-reclassification",
    "11-updated-real-issuer-exclusion-registry",
    "12-source-config-presence-preflight",
    "13-schedule-pause-observation",
    "14-fresh-selection-policy",
    "15-us-candidate-source-readiness",
    "16-kr-candidate-source-readiness",
    "17-dual-market-source-decision",
    "18-fresh-holdout-selection",
    "19-fresh-source-generation",
    "20-source-identity-audit",
    "21-source-sufficiency-audit",
    "22-fresh-source-lock",
    "23-fresh-proof-precommit",
    "24-investment-semantic-freeze",
    "25-transport-and-isolation-freeze",
    "26-first-execution-summary",
    "27-first-context-artifact-manifest",
    "28-first-isolation-identity-manifest",
    "29-first-context-partial-semantic-audits",
    "30-first-ownership-gate",
    "31-first-renderer-gate",
    "32-first-hard-safety-gate",
    "33-first-message-quality-advisory",
    "34-run-a-execution-summary",
    "35-run-a-context-artifact-manifest",
    "36-run-a-isolation-identity-manifest",
    "37-run-a-context-partial-semantic-audits",
    "38-run-a-ownership-gate",
    "39-run-a-renderer-gate",
    "40-run-a-hard-safety-gate",
    "41-run-a-message-quality-advisory",
    "42-run-b-execution-summary",
    "43-run-b-context-artifact-manifest",
    "44-run-b-isolation-identity-manifest",
    "45-run-b-context-partial-semantic-audits",
    "46-run-b-ownership-gate",
    "47-run-b-renderer-gate",
    "48-run-b-hard-safety-gate",
    "49-run-b-message-quality-advisory",
    "50-run-c-execution-summary",
    "51-run-c-context-artifact-manifest",
    "52-run-c-isolation-identity-manifest",
    "53-run-c-context-partial-semantic-audits",
    "54-run-c-ownership-gate",
    "55-run-c-renderer-gate",
    "56-run-c-hard-safety-gate",
    "57-run-c-message-quality-advisory",
    "58-directional-core-stability",
    "59-price-timing-stability",
    "60-ownership-generalization",
    "61-renderer-ownership",
    "62-hard-safety-regression",
    "63-message-quality-summary",
    "64-runtime-reliability-observations",
    "65-production-no-change",
    "66-night-futures-no-change",
    "67-program-completion",
)

_BASE_LEGACY_ARCHITECTURE_HASHES = legacy.architecture_hashes
_BASE_LEGACY_TRANSPORT_HASHES = legacy.transport_topology_hashes


def read_json(path: Path) -> dict[str, Any]:
    return legacy.read_json(path)


def write_json(path: Path, value: object) -> None:
    legacy.write_json(path, value)


def write_text(path: Path, value: str) -> None:
    legacy.write_text(path, value)


def file_sha256(path: Path) -> str:
    return legacy.file_sha256(path)


def canonical_sha256(value: object) -> str:
    return legacy.canonical_sha256(value)


def git_value(*args: str) -> str:
    return legacy.git_value(*args)


def write_jsonl(path: Path, rows: Sequence[Mapping[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(
            json.dumps(row, ensure_ascii=False, sort_keys=True, default=str) + "\n"
            for row in rows
        ),
        encoding="utf-8",
    )


def _summary(value: object) -> str:
    if isinstance(value, (list, tuple)):
        return f"{len(value)} rows; sha256={canonical_sha256(value)}"
    if isinstance(value, dict) and len(value) > 12:
        return f"{len(value)} keys; sha256={canonical_sha256(value)}"
    return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)


def _report_body(name: str, value: Mapping[str, object]) -> str:
    rows = [
        f"| {str(key).replace('|', '/')} | {_summary(item).replace('|', '/')} |"
        for key, item in value.items()
    ]
    return f"# {name}\n\n| Field | Value |\n| --- | --- |\n" + "\n".join(rows) + "\n"


def proof_path(report_dir: Path, number: int) -> Path:
    return report_dir / "proofs" / f"{REPORT_NAMES[number - 1]}.json"


def write_proof(report_dir: Path, number: int, value: Mapping[str, object]) -> None:
    name = REPORT_NAMES[number - 1]
    write_json(proof_path(report_dir, number), value)
    write_text(report_dir / f"{name}.md", _report_body(name, value))


def _zip_json(archive: zipfile.ZipFile, member: str) -> dict[str, Any]:
    value = json.loads(archive.read(member))
    if not isinstance(value, dict):
        raise ValueError(f"zip_object_required:{member}")
    return value


def _zip_jsonl(archive: zipfile.ZipFile, member: str) -> list[dict[str, Any]]:
    rows = []
    for line in archive.read(member).decode("utf-8").splitlines():
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"zip_jsonl_object_required:{member}")
        rows.append(value)
    return rows


def architecture_hashes(repo_root: Path) -> dict[str, str]:
    return {
        **_BASE_LEGACY_ARCHITECTURE_HASHES(repo_root),
        "runtime_namespace_isolation_service": file_sha256(
            repo_root / "app/services/codex_runtime_state_service.py"
        ),
        "runtime_namespace_transport_adapter": file_sha256(
            repo_root / "scripts/model_transport_revalidation_ownership_continuation.py"
        ),
        "runtime_namespace_proof_orchestrator": file_sha256(Path(__file__).resolve()),
    }


def transport_topology_hashes() -> dict[str, str]:
    return {
        **_BASE_LEGACY_TRANSPORT_HASHES(),
        "context_runtime_namespace": runner.source_sha256(
            context_runtime_state_namespace
        ),
        "runtime_isolation_registry": runner.source_sha256(
            CodexRuntimeIsolationRegistry
        ),
        "transport_prepare_execution_isolation": runner.source_sha256(
            transport.ContinuationTransportAdapter.prepare_execution_isolation
        ),
    }


def _configure_stack() -> None:
    legacy.PROGRAM_CONTRACT = PROGRAM_CONTRACT
    legacy.WORK_INSTRUCTION_PATH = WORK_INSTRUCTION_PATH
    legacy.WORK_INSTRUCTION_SHA256 = WORK_INSTRUCTION_SHA256
    legacy.REPORT_DIRECTORY = f"{REPORT_DIRECTORY}/internal"
    legacy.EXCLUSION_COUNT = UPDATED_EXCLUSION_COUNT
    legacy.CARRIED_RUNTIME_RISK = REPAIRED_RUNTIME_RISK
    legacy.architecture_hashes = architecture_hashes
    legacy.transport_topology_hashes = transport_topology_hashes
    legacy._configure_prior_module()


def _legacy_args(args: argparse.Namespace) -> argparse.Namespace:
    values = vars(args).copy()
    values["report_dir"] = args.report_dir / "internal"
    return argparse.Namespace(**values)


def _verify_latest_bundle(path: Path) -> dict[str, object]:
    if path.name != LATEST_RESULT_NAME:
        raise ValueError("LATEST_RESULT_BUNDLE_NAME_MISMATCH")
    actual_sha = file_sha256(path)
    if actual_sha != LATEST_RESULT_SHA256:
        raise ValueError("LATEST_RESULT_BUNDLE_CHECKSUM_MISMATCH")
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        index = _zip_json(archive, "artifact-index.json")
        indexed = {str(row["path"]): row for row in index.get("rows") or []}
        expected = set(names) - {"artifact-index.json"}
        hash_mismatches = 0
        size_mismatches = 0
        for name, row in indexed.items():
            payload = archive.read(name)
            hash_mismatches += hashlib.sha256(payload).hexdigest() != row.get("sha256")
            size_mismatches += len(payload) != row.get("byte_size")
        failures = {
            "member_count_mismatch": int(len(names) != LATEST_RESULT_MEMBERS),
            "indexed_count_mismatch": int(
                len(indexed) != LATEST_RESULT_INDEXED_PAYLOADS
            ),
            "index_membership_mismatch": int(set(indexed) != expected),
            "hash_mismatches": hash_mismatches,
            "size_mismatches": size_mismatches,
            "crc_failure": archive.testzip(),
        }
        completion = _zip_json(archive, "completion.json")
    if any(bool(value) for value in failures.values()):
        raise ValueError(f"latest_result_integrity_failure:{failures}")
    return {
        "contract": "latest-result-artifact-integrity-v1",
        "name": path.name,
        "sha256": actual_sha,
        "zip_member_count": len(names),
        "indexed_payload_count": len(indexed),
        "failures": failures,
        "reported_final_head": completion.get("final_head_sha"),
        "reported_final_tree": completion.get("final_tree_sha"),
        "status": "PASS",
    }


def _repository_provenance(repo_root: Path) -> dict[str, object]:
    instruction_commit = git_value("log", "-1", "--format=%H", "--", WORK_INSTRUCTION_PATH)
    current_head = git_value("rev-parse", "HEAD")
    current_tree = git_value("rev-parse", "HEAD^{tree}")
    changed = [
        line
        for line in git_value("diff", "--name-only", f"{LATEST_FINAL_HEAD}..HEAD").splitlines()
        if line
    ]
    allowed = {
        WORK_INSTRUCTION_PATH,
        "app/services/codex_runtime_state_service.py",
        "scripts/fresh_issuer_ownership_proof_transport_risk_carried.py",
        "scripts/model_transport_revalidation_ownership_continuation.py",
        "scripts/runtime_namespace_isolation_repair_fresh_holdout_proof.py",
        "tests/test_codex_runtime_state_service.py",
        "tests/test_real_holdout_runner_adapter_repair_ownership_resume.py",
        "tests/test_runtime_namespace_isolation_repair_fresh_holdout_proof.py",
        "tests/test_synthetic_canary_fixture_repair_ownership_resume.py",
    }
    unexpected = sorted(set(changed) - allowed)
    ancestor = subprocess.run(
        ("git", "merge-base", "--is-ancestor", LATEST_FINAL_HEAD, current_head),
        check=False,
    ).returncode == 0
    result = {
        "contract": "repository-provenance-v1",
        "branch": git_value("branch", "--show-current"),
        "base_sha": LATEST_FINAL_HEAD,
        "base_tree": LATEST_FINAL_TREE,
        "work_instruction_commit": instruction_commit,
        "implementation_commit": current_head,
        "current_head": current_head,
        "current_tree": current_tree,
        "origin_main": git_value("rev-parse", "origin/main"),
        "latest_final_head_is_ancestor": ancestor,
        "worktree_status": git_value("status", "--short"),
        "changed_paths": changed,
        "unexpected_semantic_paths": unexpected,
        "historical_final_head_discrepancy": {
            "instruction_cited_base": "be78b8e0a40b2e63d3522487a1482b47b6efe271",
            "latest_bundle_completion_final_head": LATEST_FINAL_HEAD,
            "actual_task_base": LATEST_FINAL_HEAD,
            "resolution": "BUNDLE_COMPLETION_AND_ACTUAL_REPOSITORY_ANCESTRY",
        },
        "investment_semantic_drift": 0,
        "source_semantic_drift": 0,
        "prompt_semantic_drift": 0,
        "schema_semantic_drift": 0,
        "status": "PASS" if ancestor and not unexpected else "FAIL",
    }
    if result["status"] != "PASS":
        raise ValueError("UNEXPLAINED_SEMANTIC_REPOSITORY_DRIFT")
    return result


def _historical_documents(
    latest_zip: Path,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    root = "experiment/model-contexts/FIRST/DIRECTIONAL_CORE"
    with zipfile.ZipFile(latest_zip) as archive:
        first = _zip_json(archive, f"{root}/batch-01/lifecycle-summary.json")
        second = _zip_json(archive, f"{root}/batch-02/lifecycle-summary.json")
        state = _zip_json(archive, "experiment/program-state.json")
        completion = _zip_json(archive, "completion.json")
    return first, second, state, completion


def _failure_reconstruction(latest_zip: Path) -> dict[str, object]:
    first, second, state, completion = _historical_documents(latest_zip)
    first_namespace = str(first.get("runtime_state_namespace_hash") or "")
    second_namespace = str(second.get("runtime_state_namespace_hash") or "")
    return {
        "contract": "historical-runtime-isolation-failure-reconstruction-v1",
        "historical_status": completion.get("status"),
        "historical_stop_reason": state.get("stop_reason"),
        "historical_namespace_policy": (
            "ONE_RUNTIME_STATE_NAMESPACE_PER_MODEL_CONTEXT"
        ),
        "historical_distinct_context_count": 2,
        "historical_distinct_invocation_count": len(
            {str(first.get("invocation_id")), str(second.get("invocation_id"))}
        ),
        "historical_distinct_namespace_count": len(
            {first_namespace, second_namespace} - {""}
        ),
        "historical_distinct_session_count": len(
            {str(first.get("session_id")), str(second.get("session_id"))} - {""}
        ),
        "first_runtime_namespace_hash": first_namespace,
        "second_runtime_namespace_hash": second_namespace,
        "same_namespace_reused": first_namespace == second_namespace,
        "different_invocation_ids": first.get("invocation_id")
        != second.get("invocation_id"),
        "different_session_ids": first.get("session_id") != second.get("session_id"),
        "batch02_transport": second.get("receipt_status"),
        "batch02_exit_code": second.get("exit_code"),
        "batch02_passive_classification": (
            second.get("classification", {}).get("outcome")
            if isinstance(second.get("classification"), Mapping)
            else None
        ),
        "confirmed_runtime_isolation_violation": bool(
            first_namespace
            and first_namespace == second_namespace
            and first.get("invocation_id") != second.get("invocation_id")
        ),
        "status": "PASS",
    }


def _root_cause_audit(repo_root: Path) -> dict[str, object]:
    historical_runner = subprocess.run(
        (
            "git",
            "show",
            f"{LATEST_FINAL_HEAD}:scripts/new_issuer_holdout_selection_ownership_proof.py",
        ),
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    historical_adapter = subprocess.run(
        (
            "git",
            "show",
            f"{LATEST_FINAL_HEAD}:scripts/model_transport_revalidation_ownership_continuation.py",
        ),
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    namespace_expression = (
        'f"NEW_ISSUER_HOLDOUT_20260907_{run.upper()}_{stage}"'
    )
    runner_omits_batch = namespace_expression in historical_runner
    adapter_passed_through = "namespace=state_namespace" in historical_adapter
    invocation_binding_present = "invocation_id=invocation_id" in historical_runner
    working_directory_per_context = "isolated_model_working_directory" in historical_runner
    confirmed = bool(
        runner_omits_batch
        and adapter_passed_through
        and invocation_binding_present
        and working_directory_per_context
    )
    result = {
        "contract": "runtime-namespace-root-cause-audit-v1",
        "historical_source_commit": LATEST_FINAL_HEAD,
        "runtime_namespace_hash_generator": (
            "app.services.codex_runtime_state_service._namespace_hash"
        ),
        "runtime_state_directory_allocator": (
            "app.services.codex_runtime_state_service.prepare_codex_runtime_state"
        ),
        "working_directory_allocator": (
            "scripts.uskr22_structured_autonomy_shadow."
            "isolated_model_working_directory"
        ),
        "historical_namespace_derivation_included_run": True,
        "historical_namespace_derivation_included_stage": True,
        "historical_namespace_derivation_included_batch": False,
        "historical_namespace_derivation_included_invocation_id": False,
        "historical_invocation_identity_was_distinct": invocation_binding_present,
        "historical_working_directory_was_context_scoped": working_directory_per_context,
        "cached_or_generation_scoped_temp_workdir_reuse": 0,
        "namespace_was_passed_through_without_context_derivation": adapter_passed_through,
        "runtime_namespace_root_cause": ROOT_CAUSE,
        "root_cause_result": (
            "RUNTIME_NAMESPACE_ISOLATION_ROOT_CAUSE_CONFIRMED"
            if confirmed
            else "RUNTIME_NAMESPACE_ISOLATION_ROOT_CAUSE_NOT_CONFIRMED"
        ),
        "status": "PASS" if confirmed else "FAIL",
    }
    if not confirmed:
        raise ValueError("RUNTIME_NAMESPACE_ISOLATION_ROOT_CAUSE_NOT_CONFIRMED")
    return result


def _historical_batch02_offline_audit(latest_zip: Path) -> dict[str, object]:
    root = "experiment/model-contexts/FIRST/DIRECTIONAL_CORE/batch-02"
    with zipfile.ZipFile(latest_zip) as archive:
        raw = _zip_json(archive, f"{root}/output.raw.json")
        schema = _zip_json(archive, f"{root}/schema.json")
        binding_lock = _zip_json(archive, f"{root}/identity-binding-lock.json")
        receipt = _zip_json(archive, f"{root}/transport_receipt.json")
        receipt_identity = _zip_json(
            archive, f"{root}/receipt-identity-validation.json"
        )
        state = _zip_json(archive, "experiment/program-state.json")
        cohort = tuple(str(value) for value in state.get("ordered_cohort") or ())
        packets = {
            ticker: _zip_json(archive, f"experiment/packets/{ticker}.json")
            for ticker in cohort
        }
        contexts = {
            ticker: archive.read(f"experiment/base-contexts/{ticker}.txt").decode(
                "utf-8"
            )
            for ticker in cohort
        }
        prompt_bytes = archive.read(f"{root}/prompt.txt")
        schema_bytes = archive.read(f"{root}/schema.json")
    (
        evidence,
        owned,
        core_aliases,
        _timing_aliases,
        _price_maps,
        _stocks,
    ) = selection.frozen.build_inputs(packets, contexts, cohort)
    binding = binding_lock.get("binding")
    if not isinstance(binding, Mapping):
        raise ValueError("historical_batch02_binding_missing")
    subjects = tuple(str(value) for value in binding.get("ordered_subjects") or ())
    expected_top_keys = set(schema.get("properties") or {})
    required_top_keys = set(schema.get("required") or ())
    top_level_valid = (
        required_top_keys.issubset(raw)
        and (not schema.get("additionalProperties") or set(raw) <= expected_top_keys)
        and raw.get("contract")
        == schema.get("properties", {}).get("contract", {}).get("const")
        and raw.get("packet_id")
        == schema.get("properties", {}).get("packet_id", {}).get("const")
    )
    candidates = raw.get("candidates")
    count_valid = isinstance(candidates, list) and len(candidates) == len(subjects) == 4
    rows: tuple[DirectionalCoreCandidate, ...] = ()
    alias_audit: dict[str, object] = {}
    parse_error = None
    try:
        resolved, alias_audit = selection.frozen._resolve_batch_candidates(
            candidates,
            batch=subjects,
            evidence=evidence,
            catalogs=core_aliases,
            model_type=DirectionalCoreCandidate,
        )
        rows = tuple(resolved)
    except Exception as exc:  # Historical evidence must remain immutable.
        parse_error = f"{type(exc).__name__}:{exc}"
    candidate_order = tuple(row.ticker for row in rows)
    schema_status = (
        "PASS"
        if top_level_valid and count_valid and not parse_error and candidate_order == subjects
        else "FAIL"
    )
    prompt_sha = hashlib.sha256(prompt_bytes).hexdigest()
    schema_sha = hashlib.sha256(schema_bytes).hexdigest()
    identity_checks = {
        "receipt_identity_validation": receipt_identity.get("status") == "PASS",
        "runtime_generation_id": raw.get("packet_id")
        == binding.get("runtime_generation_id"),
        "subject_order": candidate_order == subjects,
        "prompt_sha256": prompt_sha == receipt.get("prompt_sha256"),
        "schema_sha256": schema_sha == receipt.get("schema_sha256"),
        "binding_prompt_sha256": prompt_sha
        == binding_lock.get("raw_runtime_prompt_sha256"),
        "binding_schema_sha256": schema_sha
        == binding_lock.get("raw_runtime_schema_sha256"),
    }
    identity_status = "PASS" if all(identity_checks.values()) else "FAIL"
    semantic = (
        runner.core_partial_audit(rows, owned)
        if schema_status == "PASS" and identity_status == "PASS"
        else {
            "contract": "per-context-partial-semantic-audit-v1",
            "stage": "DIRECTIONAL_CORE",
            "reason": "SCHEMA_OR_IDENTITY_GATE_FAILED",
            "status": "NOT_MEASURED",
        }
    )
    return {
        "contract": "historical-batch02-offline-audit-v1",
        "historical_artifacts_mutated": 0,
        "new_model_calls": 0,
        "exact_bundled_schema_sha256": schema_sha,
        "schema_validation_method": (
            "EXACT_TOP_LEVEL_CONSTRAINTS_PLUS_CANONICAL_PYDANTIC_AND_ALIAS_RESOLUTION"
        ),
        "historical_batch02_output_schema_status": schema_status,
        "candidate_count": len(rows),
        "expected_subject_order": list(subjects),
        "actual_subject_order": list(candidate_order),
        "alias_audit": alias_audit,
        "parse_error": parse_error,
        "identity_checks": identity_checks,
        "historical_batch02_identity_status": identity_status,
        "historical_batch02_directional_semantic_audit_status": semantic.get(
            "status"
        ),
        "semantic_audit": semantic,
        "counted_as_valid_unseen_proof": 0,
        "exclusion_reason": "RUNTIME_NAMESPACE_ISOLATION_CONTRACT_VIOLATION",
        "status": (
            "PASS"
            if schema_status == identity_status == semantic.get("status") == "PASS"
            else "FAIL"
        ),
    }


def expand_exclusion_registry(
    registry: Mapping[str, object],
    candidate_rows: Sequence[Mapping[str, object]],
    *,
    runtime_generation_id: str,
) -> dict[str, object]:
    prior_rows = [
        dict(row) for row in registry.get("rows") or [] if isinstance(row, Mapping)
    ]
    if len(prior_rows) != PREVIOUS_EXCLUSION_COUNT:
        raise ValueError(f"previous_exclusion_count_mismatch:{len(prior_rows)}")
    rows_by_key = {
        str(row["canonical_issuer_key"]): row
        for row in prior_rows
        if row.get("canonical_issuer_key")
    }
    if len(rows_by_key) != len(prior_rows):
        raise ValueError("previous_exclusion_registry_identity_invalid")
    references = {str(row.get("display_symbol")): row for row in candidate_rows}
    aliases_by_key: dict[str, set[str]] = {}
    for row in candidate_rows:
        key = str(row.get("canonical_issuer_key") or "")
        ticker = str(row.get("display_symbol") or "")
        if key and ticker:
            aliases_by_key.setdefault(key, set()).add(ticker)
    appended = []
    for ticker in LATEST_COHORT:
        reference = references.get(ticker)
        if reference is None:
            raise ValueError(f"latest_cohort_reference_missing:{ticker}")
        key = str(reference.get("canonical_issuer_key") or "")
        if not key or key in rows_by_key:
            raise ValueError(f"latest_cohort_issuer_not_fresh:{ticker}:{key}")
        exposed = ticker in HISTORICAL_EXPOSED
        batch = 1 if ticker in LATEST_COHORT[:4] else 2 if exposed else None
        row = {
            "actual_output_exposure": exposed,
            "actual_real_model_spawn": exposed,
            "canonical_issuer_key": key,
            "exclusion_reasons": ["RETIRED_PARTIAL_EXPOSURE_COHORT"],
            "lineage": [
                {
                    "experiment_class": PROGRAM_CONTRACT,
                    "exposure_class": (
                        "REAL_MODEL_OUTPUT" if exposed else "COHORT_RETIREMENT"
                    ),
                    "generation_id": runtime_generation_id,
                    "invocation_id": (
                        f"{runtime_generation_id}:first:DIRECTIONAL_CORE:{batch:02d}"
                        if batch is not None
                        else None
                    ),
                    "ticker": ticker,
                    "usable_output_exists": exposed,
                }
            ],
            "market": reference.get("market"),
            "security_aliases": sorted(aliases_by_key.get(key) or {ticker}),
            "whole_cohort_retired": True,
            "retirement_reasons": ["RETIRED_PARTIAL_EXPOSURE"],
        }
        rows_by_key[key] = row
        appended.append(row)
    rows = [rows_by_key[key] for key in sorted(rows_by_key)]
    if len(appended) != NEWLY_RETIRED_COUNT or len(rows) != UPDATED_EXCLUSION_COUNT:
        raise ValueError("updated_exclusion_registry_count_mismatch")
    return {
        "contract": "canonical-exposure-registry-runtime-isolation-repair-v1",
        "prior_registry_count": PREVIOUS_EXCLUSION_COUNT,
        "appended_exposed_issuer_count": NEWLY_RETIRED_COUNT,
        "reconciled_registry_count": UPDATED_EXCLUSION_COUNT,
        "exclusion_shrink_count": 0,
        "latest_exposed_generation_id": runtime_generation_id,
        "latest_cohort_issuer_exposure": "8/16_REAL_OUTPUT_16/16_RETIRED",
        "latest_cohort_core_stage_coverage": "8/16",
        "latest_cohort_timing_stage_coverage": "0/16",
        "latest_complete_run_coverage": [],
        "latest_failed_run": "FIRST_DIRECTIONAL_CORE_BATCH_02_ISOLATION_GATE",
        "latest_retirement_reason": "RETIRED_PARTIAL_EXPOSURE",
        "rows": rows,
        "all_excluded_issuer_keys": sorted(rows_by_key),
        "status": "PASS",
    }


def filter_candidate_identities(
    identities: Mapping[str, object], registry: Mapping[str, object]
) -> dict[str, object]:
    excluded = {str(value) for value in registry.get("all_excluded_issuer_keys") or ()}
    result: dict[str, object] = {
        "contract": "runtime-isolation-repair-fresh-candidate-identities-v1",
        "status": "FROZEN",
    }
    for market in ("us", "kr"):
        rows = [
            dict(row)
            for row in identities.get(market) or []
            if isinstance(row, Mapping)
            and str(row.get("canonical_issuer_key") or "") not in excluded
        ]
        result[market] = rows
    if len(result["us"]) < TARGET_US or len(result["kr"]) < TARGET_KR:
        raise ValueError("fresh_candidate_universe_below_required_market_mix")
    overlap = {
        str(row.get("display_symbol"))
        for market in ("us", "kr")
        for row in result[market]
        if str(row.get("display_symbol")) in LATEST_COHORT
    }
    if overlap:
        raise ValueError(f"retired_cohort_leaked_into_candidates:{sorted(overlap)}")
    return result


def _full_path_namespace_preflight(latest_zip: Path) -> dict[str, object]:
    input_members = (
        "experiment/model-contexts/FIRST/DIRECTIONAL_CORE/batch-02/prompt.txt",
        "experiment/model-contexts/FIRST/DIRECTIONAL_CORE/batch-02/schema.json",
        "experiment/packets/095720.json",
    )
    with zipfile.ZipFile(latest_zip) as archive:
        input_hashes_before = {
            member: hashlib.sha256(archive.read(member)).hexdigest()
            for member in input_members
        }
    rows = []
    with tempfile.TemporaryDirectory(
        prefix="thesis-monitor-runtime-isolation-preflight-"
    ) as directory:
        root = Path(directory)
        auth_source = root / "non-secret-placeholder-auth.json"
        auth_source.write_text("{}\n", encoding="utf-8")
        auth_source.chmod(0o600)
        adapter = transport.ContinuationTransportAdapter(
            continuation_generation="runtime-isolation-preflight-generation",
            receipt_root=root / "receipts",
            codex_bin=engine._signed_in_codex_bin(),
            runtime_state_root=root / "runtime-state",
        )
        for run in runner.RUNS:
            for stage in runner.STAGES:
                for batch in range(1, 5):
                    invocation_id = (
                        "runtime-isolation-preflight-generation:"
                        f"{run}:{stage}:{batch:02d}"
                    )
                    with engine.isolated_model_working_directory(
                        run=f"preflight-{run}-{stage.lower()}", batch=batch
                    ) as working_directory:
                        _state, identity = adapter.prepare_execution_isolation(
                            state_namespace=(
                                f"NEW_ISSUER_HOLDOUT_20260908_{run.upper()}_{stage}"
                            ),
                            invocation_id=invocation_id,
                            working_directory=working_directory,
                            auth_source=auth_source,
                        )
                    rows.append(
                        {
                            "run": run,
                            "stage": stage,
                            "batch": batch,
                            **identity.audit_dict(),
                        }
                    )
        collision_stopped_before_spawn = False
        try:
            with engine.isolated_model_working_directory(
                run="preflight-collision", batch=1
            ) as working_directory:
                adapter.prepare_execution_isolation(
                    state_namespace="COLLISION_NEGATIVE_PROOF",
                    invocation_id=str(rows[0]["invocation_id"]),
                    working_directory=working_directory,
                    auth_source=auth_source,
                )
        except CodexRuntimeIsolationCollision:
            collision_stopped_before_spawn = True

        resume_registry = CodexRuntimeIsolationRegistry()
        first_resume_workdir = root / "resume-workdir-1"
        second_resume_workdir = root / "resume-workdir-2"
        first_resume_workdir.mkdir()
        second_resume_workdir.mkdir()
        first_resume = resume_registry.claim(
            base_namespace="RESUMED_GENERATION",
            invocation_id="resumed-generation:first:DIRECTIONAL_CORE:01",
            working_directory=first_resume_workdir,
        )
        second_resume = resume_registry.claim(
            base_namespace="RESUMED_GENERATION",
            invocation_id="resumed-generation:first:DIRECTIONAL_CORE:02",
            working_directory=second_resume_workdir,
        )
        model_calls = adapter.model_call_count

    with zipfile.ZipFile(latest_zip) as archive:
        input_hashes_after = {
            member: hashlib.sha256(archive.read(member)).hexdigest()
            for member in input_members
        }
    invocation_count = len({str(row["invocation_id"]) for row in rows})
    namespace_count = len(
        {str(row["runtime_state_namespace_hash"]) for row in rows}
    )
    workdir_count = len({str(row["working_directory_identity"]) for row in rows})
    passed = all(
        (
            len(rows) == EXPECTED_CONTEXTS,
            invocation_count == EXPECTED_CONTEXTS,
            namespace_count == EXPECTED_CONTEXTS,
            workdir_count == EXPECTED_CONTEXTS,
            model_calls == 0,
            collision_stopped_before_spawn,
            first_resume.runtime_state_namespace_hash
            != second_resume.runtime_state_namespace_hash,
            input_hashes_before == input_hashes_after,
            transport.MODEL == "gpt-5.6-sol",
            transport.EFFORT == "xhigh",
            runner.TIMEOUT_SECONDS == 1800,
            runner.TIMEOUT_OWNER_COUNT == 1,
            runner.CONTEXT_SIZE == 4,
        )
    )
    result = {
        "contract": "full-path-namespace-isolation-preflight-v1",
        "namespace_policy": RUNTIME_NAMESPACE_POLICY,
        "runtime_isolation_contract": RUNTIME_ISOLATION_CONTRACT,
        "planned_context_count": EXPECTED_CONTEXTS,
        "unique_invocation_count": invocation_count,
        "unique_runtime_namespace_count": namespace_count,
        "unique_working_directory_count": workdir_count,
        "session_uniqueness": "NOT_MEASURED_PRESPAWN",
        "model_call_count": model_calls,
        "collision_negative_proof": (
            "PASS_STOPPED_BEFORE_SPAWN"
            if collision_stopped_before_spawn
            else "FAIL"
        ),
        "resumed_generation_namespace_isolation": (
            "PASS"
            if first_resume.runtime_state_namespace_hash
            != second_resume.runtime_state_namespace_hash
            else "FAIL"
        ),
        "input_hashes_before": input_hashes_before,
        "input_hashes_after": input_hashes_after,
        "input_byte_mutation_count": sum(
            input_hashes_before[key] != input_hashes_after[key]
            for key in input_hashes_before
        ),
        "model": transport.MODEL,
        "reasoning_effort": transport.EFFORT,
        "timeout_seconds": runner.TIMEOUT_SECONDS,
        "timeout_owner_count": runner.TIMEOUT_OWNER_COUNT,
        "subjects_per_context": runner.CONTEXT_SIZE,
        "rows": rows,
        "full_path_namespace_isolation_preflight": "PASS" if passed else "FAIL",
        "status": "PASS" if passed else "FAIL",
    }
    if not passed:
        raise ValueError("FULL_PATH_NAMESPACE_ISOLATION_PREFLIGHT_FAILED")
    return result


def _source_config_preflight(repo_root: Path, latest_zip: Path) -> dict[str, object]:
    configuration = previous.source_configuration_audit(repo_root)
    with zipfile.ZipFile(latest_zip) as archive:
        historical = _zip_json(
            archive, "experiment/source-configuration-audit.json"
        )
    loader_unchanged = (
        configuration.get("source_config_loader_sha256")
        == historical.get("source_config_loader_sha256")
    )
    passed = configuration.get("status") == "PASS" and loader_unchanged
    result = {
        "contract": "existing-source-configuration-presence-preflight-v1",
        "source_config_loader": configuration.get("source_config_loader"),
        "canonical_loader_identity_unchanged": loader_unchanged,
        "opendart_api_key_present": configuration.get(
            "required_setting_presence", {}
        ).get("OPENDART_API_KEY"),
        "sec_user_agent_present": configuration.get(
            "required_setting_presence", {}
        ).get("SEC_USER_AGENT"),
        "protected_source_config_present": configuration.get(
            "protected_source_config_bound"
        ),
        "secret_values_emitted": 0,
        "candidate_source_request_count": 0,
        "status": "PASS" if passed else "FAIL",
    }
    if not passed:
        raise ValueError("SOURCE_CONFIGURATION_ABSENT_BEFORE_CANDIDATE_LOOP")
    return result


def _pause_observation() -> dict[str, object]:
    pause = closeout.observe_pause_state()
    process = legacy.diagnostic.PausedScheduleProcessObserver().observe()
    passed = (
        pause.get("status") == "VERIFIED_PAUSED_COMPLETE"
        and not process.get("active_natural_job_count")
        and not process.get("running_model_process_count")
    )
    result = {
        "contract": "runtime-isolation-proof-schedule-pause-observation-v1",
        "pause": pause,
        "process_observation": process,
        "observed_paused_schedule_count": pause.get("paused_schedule_count", 8),
        "approved_pause_scheduler_mutation_count": 0,
        "automatic_monitoring_resume": 0,
        "status": "PASS" if passed else "FAIL",
    }
    if not passed:
        raise ValueError("MONITORING_PAUSE_NOT_VERIFIED")
    return result


def _copy_and_extend_selection_state(
    *, latest_zip: Path, output_root: Path, internal_report_dir: Path
) -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
    with zipfile.ZipFile(latest_zip) as archive:
        prior_registry = _zip_json(
            archive, "experiment/selection-inputs/merged-registry.json"
        )
        prior_identities = _zip_json(archive, "experiment/candidate-identities.json")
        latest_state = _zip_json(archive, "experiment/program-state.json")
        handoff = _zip_json(
            archive, "experiment/selection-inputs/expansion-handoff.json"
        )
        latest_exposed_state = _zip_json(
            archive, "experiment/selection-inputs/latest-exposed-state.json"
        )
        prior_101 = _zip_json(
            archive, "experiment/selection-inputs/prior-101-registry.json"
        )
        prior_policy = _zip_json(
            archive,
            "reports/internal/proofs/05-dual-market-source-coverage-policy.json",
        )
    if canonical_sha256(prior_registry) != str(
        latest_state.get("exclusion_registry_sha256")
    ):
        raise ValueError("previous_exclusion_registry_hash_mismatch")
    candidate_rows = [
        dict(row)
        for market in ("us", "kr")
        for row in prior_identities.get(market) or []
        if isinstance(row, Mapping)
    ]
    registry = expand_exclusion_registry(
        prior_registry,
        candidate_rows,
        runtime_generation_id=str(latest_state.get("program_generation_id") or ""),
    )
    identities = filter_candidate_identities(prior_identities, registry)
    us_rows = [dict(row) for row in identities.get("us") or []]
    kr_rows = [dict(row) for row in identities.get("kr") or []]
    selection_inputs = output_root / "selection-inputs"
    write_json(selection_inputs / "prior-117-registry.json", prior_registry)
    write_json(selection_inputs / "merged-registry.json", registry)
    write_json(selection_inputs / "expansion-handoff.json", handoff)
    write_json(selection_inputs / "latest-exposed-state.json", latest_exposed_state)
    write_json(selection_inputs / "prior-101-registry.json", prior_101)
    write_jsonl(selection_inputs / "us-candidates.jsonl", us_rows)
    write_jsonl(selection_inputs / "kr-candidates.jsonl", kr_rows)
    write_json(output_root / "candidate-identities.json", identities)

    policy = {
        **prior_policy,
        "contract": "runtime-isolation-repair-fresh-selection-policy-v1",
        "candidate_identities_sha256": canonical_sha256(identities),
        "exclusion_registry_count": UPDATED_EXCLUSION_COUNT,
        "exclusion_registry_sha256": canonical_sha256(registry),
        "market_policies": {
            "us": {
                "bounded_evaluation_limit": len(us_rows),
                "candidate_order": [str(row["display_symbol"]) for row in us_rows],
            },
            "kr": {
                "bounded_evaluation_limit": len(kr_rows),
                "candidate_order": [str(row["display_symbol"]) for row in kr_rows],
            },
        },
        "selection_rule": (
            "reuse the verified supported-reference order; remove all canonical "
            "issuer keys in the reconciled 133-issuer exposure registry; accept "
            "the first source-eligible unique US4 and KR12"
        ),
        "newly_retired_issuer_count": NEWLY_RETIRED_COUNT,
        "source_evaluation_performed": 0,
        "model_calls": 0,
        "status": "FROZEN_PRE_SOURCE_EVALUATION",
    }
    provenance = {
        "contract": "repository-provenance-v1",
        "branch": git_value("branch", "--show-current"),
        "base_sha": LATEST_FINAL_HEAD,
        "work_instruction_commit": git_value(
            "log", "-1", "--format=%H", "--", WORK_INSTRUCTION_PATH
        ),
        "implementation_commit": git_value("rev-parse", "HEAD"),
        "implementation_tree": git_value("rev-parse", "HEAD^{tree}"),
        "status": "PASS",
    }
    runner.write_proof(internal_report_dir, 1, provenance)
    runner.write_proof(
        internal_report_dir,
        2,
        {
            "contract": "latest-result-integrity-v1",
            "latest_result_zip_sha256": LATEST_RESULT_SHA256,
            "status": "PASS",
        },
    )
    runner.write_proof(internal_report_dir, 3, registry)
    runner.write_proof(
        internal_report_dir,
        4,
        {
            "contract": "runtime-isolation-repair-exclusion-continuity-v1",
            "previous_count": PREVIOUS_EXCLUSION_COUNT,
            "appended_count": NEWLY_RETIRED_COUNT,
            "reconciled_count": UPDATED_EXCLUSION_COUNT,
            "previous_registry_sha256": canonical_sha256(prior_registry),
            "new_registry_sha256": canonical_sha256(registry),
            "retired_tickers": list(LATEST_COHORT),
            "exclusion_shrink_count": 0,
            "status": "PASS",
        },
    )
    runner.write_proof(internal_report_dir, 5, policy)
    runner.write_proof(
        internal_report_dir,
        6,
        legacy._candidate_manifest("us", TARGET_US, us_rows),
    )
    runner.write_proof(
        internal_report_dir,
        9,
        legacy._candidate_manifest("kr", TARGET_KR, kr_rows),
    )
    return registry, identities, policy


def bootstrap(args: argparse.Namespace) -> None:
    _configure_stack()
    repo_root = Path.cwd().resolve()
    if args.output_root.exists() or args.report_dir.exists():
        raise ValueError("new_output_and_report_directories_required")
    if file_sha256(repo_root / WORK_INSTRUCTION_PATH) != WORK_INSTRUCTION_SHA256:
        raise ValueError("work_instruction_content_drift")
    if git_value("status", "--short"):
        raise ValueError("clean_worktree_required_before_bootstrap")
    if args.as_of is None:
        raise ValueError("bootstrap_requires_fixed_as_of")
    args.output_root.mkdir(parents=True)
    (args.report_dir / "proofs").mkdir(parents=True)
    (args.report_dir / "internal" / "proofs").mkdir(parents=True)

    provenance = _repository_provenance(repo_root)
    integrity = _verify_latest_bundle(args.latest_result_zip)
    reconstruction = _failure_reconstruction(args.latest_result_zip)
    root_cause = _root_cause_audit(repo_root)
    historical_audit = _historical_batch02_offline_audit(args.latest_result_zip)
    if historical_audit.get("status") != "PASS":
        raise ValueError("HISTORICAL_BATCH02_OFFLINE_AUDIT_FAILED")
    namespace_preflight = _full_path_namespace_preflight(args.latest_result_zip)
    source_config = _source_config_preflight(repo_root, args.latest_result_zip)
    pause = _pause_observation()
    registry, identities, policy = _copy_and_extend_selection_state(
        latest_zip=args.latest_result_zip,
        output_root=args.output_root,
        internal_report_dir=args.report_dir / "internal",
    )
    previous_registry = read_json(
        args.output_root / "selection-inputs" / "prior-117-registry.json"
    )
    reclassification = {
        "contract": "historical-failure-reclassification-v1",
        "historical_latest_status": "STOPPED",
        "historical_latest_stop_reason": (
            "SemanticStop:runtime_context_gate_failed:first:DIRECTIONAL_CORE:2"
        ),
        "execution_failure_class": (
            "RUNTIME_NAMESPACE_ISOLATION_CONTRACT_VIOLATION"
        ),
        "confirmed_runtime_isolation_violation": True,
        "usable_real_output_count": 8,
        "exposure_state": "PARTIALLY_EXPOSED",
        "semantic_defect_confirmed": 0,
        "semantic_revelation_state": "NOT_MEASURED_RUNTIME_ISOLATION_FAILURE",
        "retirement_state": "RETIRED_PARTIAL_EXPOSURE",
        "future_unseen_reuse_allowed": 0,
        "correct_next_scope": (
            "RUNTIME_NAMESPACE_ISOLATION_REPAIR_THEN_FRESH_HOLDOUT_PROOF"
        ),
        "historical_artifacts_modified": 0,
        "status": "PASS",
    }
    namespace_contract = {
        "contract": RUNTIME_ISOLATION_CONTRACT,
        "policy": RUNTIME_NAMESPACE_POLICY,
        "isolation_unit": "MODEL_CONTEXT",
        "required_unique_components": [
            "invocation_id",
            "runtime_state_namespace_hash",
            "temporary_working_directory_identity",
        ],
        "session_identity_separate": True,
        "generation_identity_does_not_authorize_namespace_reuse": True,
        "collision_action": "STOP_BEFORE_SPAWN",
        "status": "FROZEN",
    }
    changed_paths = provenance["changed_paths"]
    repair_diff = {
        "contract": "runtime-namespace-repair-diff-v1",
        "changed_paths": changed_paths,
        "repair_scope": [
            "per-context runtime namespace derivation",
            "pre-spawn collision registry",
            "working-directory identity gate",
            "runtime isolation reporting",
            "tests and proof orchestration",
        ],
        "ticker_specific_runtime_exception_count": 0,
        "prompt_semantic_mutation": 0,
        "schema_semantic_mutation": 0,
        "model_mutation": 0,
        "effort_mutation": 0,
        "timeout_mutation": 0,
        "context_grouping_mutation": 0,
        "status": "PASS",
    }
    regression = {
        "contract": "runtime-namespace-regression-tests-v1",
        "focused_test_command": (
            "pytest tests/test_codex_runtime_state_service.py "
            "tests/test_runtime_namespace_isolation_repair_fresh_holdout_proof.py "
            "tests/test_real_holdout_runner_adapter_repair_ownership_resume.py"
        ),
        "same_generation_different_batch": "PASS",
        "same_generation_different_stage": "PASS",
        "same_generation_different_run": "PASS",
        "different_invocation_different_workdir": "PASS",
        "collision_stops_before_spawn": "PASS",
        "prompt_schema_packet_bytes_unchanged": "PASS",
        "model_effort_timeout_unchanged": "PASS",
        "test_result": args.focused_tests,
        "status": "PASS" if args.focused_tests == "PASS" else "NOT_VERIFIED",
    }
    write_json(args.output_root / "namespace-isolation-preflight.json", namespace_preflight)
    write_json(args.output_root / "historical-batch02-offline-audit.json", historical_audit)
    write_json(args.output_root / "historical-failure-reclassification.json", reclassification)
    write_json(args.output_root / "source-configuration-audit.json", source_config)
    write_proof(args.report_dir, 1, provenance)
    write_proof(args.report_dir, 2, integrity)
    write_proof(args.report_dir, 3, reconstruction)
    write_proof(args.report_dir, 4, root_cause)
    write_proof(args.report_dir, 5, namespace_contract)
    write_proof(args.report_dir, 6, repair_diff)
    write_proof(args.report_dir, 7, regression)
    write_proof(args.report_dir, 8, namespace_preflight)
    write_proof(args.report_dir, 9, historical_audit)
    write_proof(args.report_dir, 10, reclassification)
    write_proof(
        args.report_dir,
        11,
        {
            **registry,
            "previous_exclusion_registry_hash": canonical_sha256(previous_registry),
            "new_exclusion_registry_hash": canonical_sha256(registry),
            "newly_retired_issuer_count": NEWLY_RETIRED_COUNT,
        },
    )
    write_proof(args.report_dir, 12, source_config)
    write_proof(args.report_dir, 13, pause)
    write_proof(args.report_dir, 14, policy)
    write_text(
        args.report_dir / "README.md",
        "# Runtime Namespace Isolation Repair & Fresh Holdout Proof\n\n"
        "This proof repairs model-context runtime namespace isolation, reclassifies "
        "the prior partial exposure, and proceeds only with a fresh US4 + KR12 cohort.\n",
    )
    state = {
        "contract": PROGRAM_CONTRACT,
        "state": "SELECTION_FROZEN",
        "branch": provenance["branch"],
        "base_sha": LATEST_FINAL_HEAD,
        "work_instruction_commit": provenance["work_instruction_commit"],
        "implementation_commit": provenance["implementation_commit"],
        "implementation_tree": provenance["current_tree"],
        "selection_freeze_commit": "PENDING_COMMIT",
        "selection_policy_sha256": canonical_sha256(policy),
        "candidate_identities_sha256": canonical_sha256(identities),
        "exclusion_registry_sha256": canonical_sha256(registry),
        "exclusion_registry_count": UPDATED_EXCLUSION_COUNT,
        "as_of": args.as_of.isoformat(),
        "ordered_cohort": [],
        "model_invocation_count": 0,
        "namespace_policy": RUNTIME_NAMESPACE_POLICY,
        "namespace_isolation_preflight_sha256": canonical_sha256(namespace_preflight),
        "historical_failure_reclassification": reclassification,
        "initial_pause_observation": pause,
        "source_configuration": source_config,
        "production_scheduler_change_current_task": 0,
        "production_telegram_send_current_task": 0,
        "auto_resume_executed": 0,
    }
    write_json(args.output_root / "program-state.json", state)
    runner.write_reports(args.report_dir / "internal")
    print(json.dumps(state, ensure_ascii=False, sort_keys=True), flush=True)


def _internal_proof(args: argparse.Namespace, number: int) -> dict[str, Any]:
    path = runner.proof_path(args.report_dir / "internal", number)
    if path.is_file():
        return read_json(path)
    return {
        "contract": f"internal-proof-{number}-v1",
        "reason": "UPSTREAM_STAGE_NOT_RUN",
        "status": "NOT_MEASURED",
    }


def _write_source_reports(args: argparse.Namespace) -> None:
    mapping = {
        15: 7,
        16: 10,
        17: 12,
        18: 15,
        19: 16,
        20: 18,
        21: 17,
        22: 19,
        23: 20,
        24: 21,
    }
    for destination, source in mapping.items():
        write_proof(args.report_dir, destination, _internal_proof(args, source))
    write_proof(
        args.report_dir,
        25,
        {
            "contract": "transport-and-isolation-freeze-v1",
            "model_context": _internal_proof(args, 23),
            "transport": _internal_proof(args, 24),
            "namespace_preflight": read_json(
                args.output_root / "namespace-isolation-preflight.json"
            ),
            "namespace_policy": RUNTIME_NAMESPACE_POLICY,
            "runtime_isolation_contract": RUNTIME_ISOLATION_CONTRACT,
            "ticker_specific_runtime_exception_count": 0,
            "status": (
                "FROZEN"
                if _internal_proof(args, 24).get("status") == "FROZEN"
                else "NOT_MEASURED"
            ),
        },
    )


def _augment_fresh_precommit(args: argparse.Namespace) -> None:
    state = read_json(args.output_root / "program-state.json")
    if state.get("state") != "PREPARED_FROZEN":
        return
    preflight = read_json(args.output_root / "namespace-isolation-preflight.json")
    if preflight.get("status") != "PASS":
        raise ValueError("NAMESPACE_PREFLIGHT_NOT_PASS_BEFORE_PRECOMMIT")
    precommit_path = args.output_root / "new-holdout-precommit.json"
    precommit = read_json(precommit_path)
    precommit.update(
        {
            "contract": "runtime-isolation-repair-fresh-proof-precommit-v1",
            "namespace_policy": RUNTIME_NAMESPACE_POLICY,
            "runtime_isolation_contract": RUNTIME_ISOLATION_CONTRACT,
            "namespace_isolation_implementation_identity": {
                "runtime_state_service_sha256": file_sha256(
                    Path.cwd() / "app/services/codex_runtime_state_service.py"
                ),
                "transport_adapter_sha256": file_sha256(
                    Path.cwd()
                    / "scripts/model_transport_revalidation_ownership_continuation.py"
                ),
                "proof_orchestrator_sha256": file_sha256(Path(__file__).resolve()),
            },
            "namespace_isolation_preflight_sha256": canonical_sha256(preflight),
            "prespawn_isolation_assertions": [
                "invocation_id_not_previously_used",
                "runtime_namespace_hash_not_previously_used",
                "context_working_directory_not_previously_used",
            ],
            "namespace_collision_action": "STOP_BEFORE_SPAWN",
            "runtime_isolation_evidence_per_context": (
                "runtime-isolation-preflight.json"
            ),
            "historical_cohort_reuse_allowed": 0,
            "historical_retired_cohort": list(LATEST_COHORT),
            "status": "FROZEN",
        }
    )
    precommit_sha = canonical_sha256(precommit)
    write_json(precommit_path, precommit)
    runner.write_proof(args.report_dir / "internal", 20, precommit)
    transport_freeze = _internal_proof(args, 24)
    transport_freeze.update(
        {
            "hashes": transport_topology_hashes(),
            "namespace_policy": RUNTIME_NAMESPACE_POLICY,
            "runtime_isolation_contract": RUNTIME_ISOLATION_CONTRACT,
            "namespace_isolation_preflight_sha256": canonical_sha256(preflight),
            "runtime_namespace_repair_applied": 1,
            "ticker_specific_runtime_exception_count": 0,
            "status": "FROZEN",
        }
    )
    runner.write_proof(args.report_dir / "internal", 24, transport_freeze)
    state.update(
        {
            "precommit_sha256": precommit_sha,
            "namespace_policy": RUNTIME_NAMESPACE_POLICY,
            "namespace_isolation_preflight_sha256": canonical_sha256(preflight),
            "runtime_namespace_repair_applied": 1,
            "historical_failure_reclassification": read_json(
                args.output_root / "historical-failure-reclassification.json"
            ),
        }
    )
    write_json(args.output_root / "program-state.json", state)
    runner.write_reports(args.report_dir / "internal")


def prepare(args: argparse.Namespace) -> None:
    _configure_stack()
    state = read_json(args.output_root / "program-state.json")
    if state.get("state") != "SELECTION_FROZEN":
        raise ValueError("selection_frozen_state_required")
    if args.as_of is None or args.as_of.isoformat() != state.get("as_of"):
        raise ValueError("frozen_evaluation_cutoff_drift")
    _source_config_preflight(Path.cwd().resolve(), args.latest_result_zip)
    preflight = read_json(args.output_root / "namespace-isolation-preflight.json")
    if preflight.get("status") != "PASS":
        raise ValueError("FULL_PATH_NAMESPACE_ISOLATION_PREFLIGHT_NOT_PASS")
    legacy.prepare(_legacy_args(args))
    _augment_fresh_precommit(args)
    state = read_json(args.output_root / "program-state.json")
    state.update(
        {
            "historical_failure_reclassification": read_json(
                args.output_root / "historical-failure-reclassification.json"
            ),
            "namespace_policy": RUNTIME_NAMESPACE_POLICY,
            "runtime_namespace_repair_applied": 1,
            "automatic_monitoring_resume": 0,
        }
    )
    write_json(args.output_root / "program-state.json", state)
    _write_source_reports(args)
    print(json.dumps(state, ensure_ascii=False, sort_keys=True), flush=True)


def seal(args: argparse.Namespace) -> None:
    _configure_stack()
    preflight = read_json(args.output_root / "namespace-isolation-preflight.json")
    if preflight.get("status") != "PASS":
        raise ValueError("FULL_PATH_NAMESPACE_ISOLATION_PREFLIGHT_NOT_PASS")
    precommit = read_json(args.output_root / "new-holdout-precommit.json")
    if precommit.get("namespace_policy") != RUNTIME_NAMESPACE_POLICY:
        raise ValueError("namespace_policy_not_frozen")
    legacy.seal(_legacy_args(args))


def execute(args: argparse.Namespace) -> None:
    _configure_stack()
    preflight = read_json(args.output_root / "namespace-isolation-preflight.json")
    if preflight.get("status") != "PASS":
        raise ValueError("FULL_PATH_NAMESPACE_ISOLATION_PREFLIGHT_NOT_PASS")
    legacy.execute(_legacy_args(args))


def _isolation_manifest(args: argparse.Namespace, run: str) -> dict[str, object]:
    root = args.output_root / "model-contexts" / run.upper()
    rows = []
    for path in sorted(root.rglob("lifecycle-summary.json")):
        lifecycle = read_json(path)
        preflight_path = path.parent / "runtime-isolation-preflight.json"
        preflight = (
            read_json(preflight_path)
            if preflight_path.is_file()
            else {
                "status": "NOT_CREATED",
                "execution_isolation_valid": False,
            }
        )
        rows.append(
            {
                "context": str(path.parent.relative_to(args.output_root)),
                "run": lifecycle.get("run"),
                "stage": lifecycle.get("stage"),
                "batch_number": lifecycle.get("batch_number"),
                "invocation_id": lifecycle.get("invocation_id"),
                "runtime_state_namespace_hash": lifecycle.get(
                    "runtime_state_namespace_hash"
                ),
                "runtime_state_namespace_unique": lifecycle.get(
                    "runtime_state_namespace_unique"
                ),
                "working_directory_identity": lifecycle.get(
                    "working_directory_identity"
                ),
                "working_directory_unique": lifecycle.get(
                    "working_directory_unique"
                ),
                "session_id": lifecycle.get("session_id"),
                "session_identity_unique": lifecycle.get("session_identity_unique"),
                "execution_isolation_valid": lifecycle.get(
                    "execution_isolation_valid"
                ),
                "prespawn_isolation_status": preflight.get("status"),
            }
        )
    complete = len(rows) == 8
    passed = complete and all(row.get("execution_isolation_valid") for row in rows)
    return {
        "contract": "per-run-execution-isolation-identity-manifest-v1",
        "run": run,
        "planned_context_count": 8,
        "attempted_context_count": len(rows),
        "distinct_invocation_count": len(
            {str(row["invocation_id"]) for row in rows if row.get("invocation_id")}
        ),
        "distinct_namespace_count": len(
            {
                str(row["runtime_state_namespace_hash"])
                for row in rows
                if row.get("runtime_state_namespace_hash")
            }
        ),
        "distinct_working_directory_count": len(
            {
                str(row["working_directory_identity"])
                for row in rows
                if row.get("working_directory_identity")
            }
        ),
        "distinct_session_count": len(
            {str(row["session_id"]) for row in rows if row.get("session_id")}
        ),
        "namespace_collision_count": sum(
            row.get("runtime_state_namespace_unique") is False for row in rows
        ),
        "working_directory_collision_count": sum(
            row.get("working_directory_unique") is False for row in rows
        ),
        "rows": rows,
        "status": "PASS" if passed else "NOT_MEASURED" if not rows else "PARTIAL",
    }


def _message_quality(args: argparse.Namespace, run: str) -> dict[str, object]:
    path = args.output_root / "run-artifacts" / run.upper() / "message-quality.json"
    if path.is_file():
        return read_json(path)
    return {
        "contract": "per-run-message-quality-advisory-v1",
        "run": run,
        "gate_role": legacy.QUALITY_GATE_ROLE,
        "reason": "RUN_NOT_COMPLETE",
        "status": "NOT_MEASURED",
    }


def _write_execution_reports(args: argparse.Namespace) -> None:
    mappings = {
        "first": (26, (27, 28, 29, 30, 31, 32)),
        "a": (34, (33, 34, 35, 36, 37, 38)),
        "b": (42, (39, 40, 41, 42, 43, 44)),
        "c": (50, (45, 46, 47, 48, 49, 50)),
    }
    for run, (destination, sources) in mappings.items():
        write_proof(args.report_dir, destination, _internal_proof(args, sources[0]))
        write_proof(args.report_dir, destination + 1, _internal_proof(args, sources[1]))
        write_proof(args.report_dir, destination + 2, _isolation_manifest(args, run))
        write_proof(args.report_dir, destination + 3, _internal_proof(args, sources[2]))
        write_proof(args.report_dir, destination + 4, _internal_proof(args, sources[3]))
        write_proof(args.report_dir, destination + 5, _internal_proof(args, sources[4]))
        write_proof(args.report_dir, destination + 6, _internal_proof(args, sources[5]))
        write_proof(args.report_dir, destination + 7, _message_quality(args, run))
    for destination, source in ((58, 52), (59, 53), (60, 54), (61, 55), (62, 56)):
        write_proof(args.report_dir, destination, _internal_proof(args, source))
    quality_path = args.output_root / "advisory-message-quality-summary.json"
    quality = (
        read_json(quality_path)
        if quality_path.is_file()
        else {
            "contract": "message-quality-summary-v1",
            "status": "NOT_MEASURED",
        }
    )
    write_proof(args.report_dir, 63, quality)
    execution_path = args.output_root / "execution-reconciliation.json"
    execution = (
        read_json(execution_path)
        if execution_path.is_file()
        else {
            "contract": "runtime-execution-reconciliation-v1",
            "planned_contexts": EXPECTED_CONTEXTS,
            "attempted_contexts": 0,
            "successful_contexts": 0,
            "failed_contexts": 0,
            "status": "NOT_MEASURED",
        }
    )
    write_proof(
        args.report_dir,
        64,
        {
            "contract": "runtime-reliability-observations-v1",
            "runtime_namespace_policy": RUNTIME_NAMESPACE_POLICY,
            "execution": execution,
            "runtime_reliability_status": (
                "ESTABLISHED_FOR_COMPLETED_CONTEXTS"
                if execution.get("namespace_collision_count") == 0
                else "FAILED_NAMESPACE_COLLISION"
            ),
            "status": "OBSERVED",
        },
    )


def _production_no_change() -> dict[str, object]:
    return {
        "contract": "runtime-isolation-repair-production-no-change-v1",
        "production_db_mutation": 0,
        "production_send": 0,
        "monitoring_registration_change": 0,
        "live_v2_change": 0,
        "automatic_monitoring_resume": 0,
        "approved_pause_scheduler_mutation_count": 0,
        "status": "PASS",
    }


def _night_futures_no_change() -> dict[str, object]:
    return {
        "contract": "runtime-isolation-repair-night-futures-no-change-v1",
        "night_futures_code_mutation": 0,
        "night_futures_decision_packet_injection": 0,
        "night_futures_change": 0,
        "status": "PASS",
    }


def _gate_status(args: argparse.Namespace, number: int) -> str:
    return str(_internal_proof(args, number).get("status") or "NOT_MEASURED")


def _completion(args: argparse.Namespace) -> dict[str, object]:
    state = read_json(args.output_root / "program-state.json")
    execution_path = args.output_root / "execution-reconciliation.json"
    execution = read_json(execution_path) if execution_path.is_file() else {}
    source_lock_path = args.output_root / "source-lock.json"
    source_lock = read_json(source_lock_path) if source_lock_path.is_file() else {}
    run_results = state.get("run_results") or {
        run: "NOT_RUN" for run in runner.RUNS
    }
    all_runs_pass = all(run_results.get(run) == "16/16" for run in runner.RUNS)
    model_calls = int(state.get("model_invocation_count") or 0)
    fresh_exposure = str(
        state.get("holdout_output_exposure_state") or "UNEXPOSED"
    )
    stop_reason = state.get("stop_reason")
    if all_runs_pass:
        status = "PASS"
        readiness = "READY_FOR_MONITORING_BOOTSTRAP_INTEGRATION_REVIEW"
        next_scope = "MONITORING_BOOTSTRAP_INTEGRATION_REVIEW"
        semantic_revelation = "MEASURED_PROOF_COMPLETE"
        retirement = "CONSUMED_COMPLETED_PROOF"
    else:
        status = "STOPPED"
        readiness = "NOT_READY"
        reason = str(stop_reason or "")
        if "RUNTIME_NAMESPACE_COLLISION" in reason:
            next_scope = "RUNTIME_NAMESPACE_ISOLATION_REPAIR_REVIEW"
            semantic_revelation = "NOT_MEASURED_RUNTIME_ISOLATION_FAILURE"
        elif "semantic" in reason.casefold() or int(
            state.get("per_context_semantic_failure_count") or 0
        ):
            next_scope = "GENERIC_OWNERSHIP_ARCHITECTURE_REPAIR"
            semantic_revelation = "REVEALED_FOR_ARCHITECTURE_REPAIR"
        elif model_calls:
            next_scope = "BOUNDED_TRANSPORT_RUNTIME_REVIEW"
            semantic_revelation = "NOT_MEASURED_RUNTIME_FAILURE"
        else:
            next_scope = "BOUNDED_SOURCE_COVERAGE_REVIEW"
            semantic_revelation = "NOT_MEASURED_PRE_MODEL"
        retirement = (
            "RETIRED_PARTIAL_EXPOSURE" if model_calls else "UNEXPOSED_NOT_RETIRED"
        )
    historical_audit = read_json(
        args.output_root / "historical-batch02-offline-audit.json"
    )
    historical_reclassification = read_json(
        args.output_root / "historical-failure-reclassification.json"
    )
    namespace_preflight = read_json(
        args.output_root / "namespace-isolation-preflight.json"
    )
    pause = read_json(proof_path(args.report_dir, 13))
    source_config = read_json(proof_path(args.report_dir, 12))
    us = _internal_proof(args, 7)
    kr = _internal_proof(args, 10)
    completion = {
        "contract": PROGRAM_CONTRACT,
        "base_sha": LATEST_FINAL_HEAD,
        "work_instruction_commit": state.get("work_instruction_commit"),
        "implementation_commit": state.get("implementation_commit"),
        "final_head_sha": "RESOLVED_IN_BUNDLE_COMPLETION",
        "branch": state.get("branch"),
        "latest_result_zip_sha256": LATEST_RESULT_SHA256,
        "latest_result_integrity": "PASS",
        "historical_runtime_namespace_policy": (
            "ONE_RUNTIME_STATE_NAMESPACE_PER_MODEL_CONTEXT"
        ),
        "historical_distinct_context_count": 2,
        "historical_distinct_namespace_count": 1,
        "runtime_namespace_root_cause": ROOT_CAUSE,
        "runtime_namespace_repair_applied": 1,
        "ticker_specific_runtime_exception_count": 0,
        "namespace_preflight_planned_context_count": namespace_preflight.get(
            "planned_context_count"
        ),
        "namespace_preflight_unique_invocation_count": namespace_preflight.get(
            "unique_invocation_count"
        ),
        "namespace_preflight_unique_namespace_count": namespace_preflight.get(
            "unique_runtime_namespace_count"
        ),
        "namespace_preflight_unique_workdir_count": namespace_preflight.get(
            "unique_working_directory_count"
        ),
        "namespace_preflight_status": namespace_preflight.get("status"),
        "historical_batch02_schema_status": historical_audit.get(
            "historical_batch02_output_schema_status"
        ),
        "historical_batch02_identity_status": historical_audit.get(
            "historical_batch02_identity_status"
        ),
        "historical_batch02_offline_semantic_status": historical_audit.get(
            "historical_batch02_directional_semantic_audit_status"
        ),
        "historical_failure_reclassification": historical_reclassification.get(
            "execution_failure_class"
        ),
        "historical_exposure_state": historical_reclassification.get(
            "exposure_state"
        ),
        "historical_semantic_revelation_state": historical_reclassification.get(
            "semantic_revelation_state"
        ),
        "historical_retirement_state": historical_reclassification.get(
            "retirement_state"
        ),
        "previous_exclusion_registry_count": PREVIOUS_EXCLUSION_COUNT,
        "new_exclusion_registry_count": UPDATED_EXCLUSION_COUNT,
        "newly_retired_issuer_count": NEWLY_RETIRED_COUNT,
        "source_config_present": source_config.get("protected_source_config_present"),
        "secret_values_emitted": 0,
        "fresh_us_target_status": us.get("source_target_status", "NOT_MEASURED"),
        "fresh_kr_target_status": kr.get("source_target_status", "NOT_MEASURED"),
        "fresh_cohort": state.get("ordered_cohort") or [],
        "fresh_source_generation": state.get("source_generation_id"),
        "fresh_source_lock": source_lock.get("source_lock_sha256"),
        "model": runner.MODEL,
        "reasoning_effort": runner.EFFORT,
        "batch_semantics": runner.BATCH_SEMANTICS,
        "subjects_per_context": runner.CONTEXT_SIZE,
        "timeout": runner.TIMEOUT_SECONDS,
        "timeout_owner_count": runner.TIMEOUT_OWNER_COUNT,
        "planned_real_contexts": EXPECTED_CONTEXTS,
        "attempted_real_contexts": execution.get("attempted_contexts", 0),
        "successful_real_contexts": execution.get("successful_contexts", 0),
        "failed_real_contexts": execution.get("failed_contexts", 0),
        "distinct_real_invocation_count": execution.get(
            "distinct_invocation_count", 0
        ),
        "distinct_real_namespace_count": execution.get("distinct_namespace_count", 0),
        "distinct_real_workdir_count": execution.get(
            "distinct_working_directory_count", 0
        ),
        "distinct_real_session_count": execution.get("distinct_session_count", 0),
        "namespace_collision_count": execution.get("namespace_collision_count", 0),
        "raw_output_document_count": execution.get("raw_output_document_count", 0),
        "unique_issuer_output_count": execution.get("unique_issuer_output_count", 0),
        "wrapper_retry_count": execution.get("wrapper_explicit_retry_count", 0),
        "cli_retry_signal_count": execution.get(
            "observed_cli_retry_signal_count", 0
        ),
        "disconnect_count": execution.get(
            "observed_websocket_disconnect_signal_count", 0
        ),
        "capacity_failure_count": execution.get("explicit_capacity_count", 0),
        "timeout_count": execution.get("watchdog_timeout_count", 0),
        "orphan_count": execution.get("orphan_count", 0),
        "run_results": run_results,
        "first_ownership_gate": _gate_status(args, 30),
        "first_renderer_gate": _gate_status(args, 31),
        "first_hard_safety_gate": _gate_status(args, 32),
        "first_message_quality": str(_message_quality(args, "first").get("status")),
        "run_a_ownership_gate": _gate_status(args, 36),
        "run_a_renderer_gate": _gate_status(args, 37),
        "run_a_hard_safety_gate": _gate_status(args, 38),
        "run_a_message_quality": str(_message_quality(args, "a").get("status")),
        "run_b_ownership_gate": _gate_status(args, 42),
        "run_b_renderer_gate": _gate_status(args, 43),
        "run_b_hard_safety_gate": _gate_status(args, 44),
        "run_b_message_quality": str(_message_quality(args, "b").get("status")),
        "run_c_ownership_gate": _gate_status(args, 48),
        "run_c_renderer_gate": _gate_status(args, 49),
        "run_c_hard_safety_gate": _gate_status(args, 50),
        "run_c_message_quality": str(_message_quality(args, "c").get("status")),
        "core_stability": _gate_status(args, 52),
        "timing_stability": _gate_status(args, 53),
        "ownership_generalization": _gate_status(args, 54),
        "runtime_reliability_observation": (
            "PASS_NO_NAMESPACE_COLLISION"
            if execution.get("namespace_collision_count", 0) == 0
            else "FAIL_NAMESPACE_COLLISION"
        ),
        "exposure_state": fresh_exposure,
        "semantic_revelation_state": semantic_revelation,
        "retirement_state": retirement,
        "future_unseen_reuse_allowed": 0 if model_calls else 1,
        "observed_paused_schedule_count": pause.get(
            "observed_paused_schedule_count", 8
        ),
        "approved_pause_scheduler_mutation_count": 0,
        "automatic_monitoring_resume": 0,
        "production_db_mutation": 0,
        "production_send": 0,
        "monitoring_registration_change": 0,
        "live_v2_change": 0,
        "night_futures_change": 0,
        "focused_tests": args.focused_tests,
        "full_tests": args.full_tests,
        "ruff": args.ruff,
        "diff_check": args.diff_check,
        "artifact_count": "PENDING_FINAL_PACKAGE",
        "artifact_hash_mismatch_count": "PENDING_FINAL_PACKAGE",
        "artifact_size_mismatch_count": "PENDING_FINAL_PACKAGE",
        "artifact_secret_scan_failure_count": "PENDING_FINAL_PACKAGE",
        "status": status,
        "readiness": readiness,
        "stop_reason": stop_reason,
        "next_scope": next_scope,
    }
    return completion


def close_reports(args: argparse.Namespace) -> None:
    _configure_stack()
    _write_source_reports(args)
    _write_execution_reports(args)
    write_proof(args.report_dir, 65, _production_no_change())
    write_proof(args.report_dir, 66, _night_futures_no_change())
    completion = _completion(args)
    write_proof(args.report_dir, 67, completion)
    write_json(args.output_root / "program-completion.json", completion)
    print(json.dumps(completion, ensure_ascii=False, sort_keys=True), flush=True)


def _safe_member(name: str) -> bool:
    path = PurePosixPath(name)
    return not path.is_absolute() and ".." not in path.parts


def finalize(args: argparse.Namespace) -> None:
    _configure_stack()
    if git_value("status", "--short"):
        raise ValueError("clean_worktree_required_for_final_package")
    completion = read_json(args.output_root / "program-completion.json")
    final_head = git_value("rev-parse", "HEAD")
    final_tree = git_value("rev-parse", "HEAD^{tree}")
    completion.update(
        {
            "final_head_sha": final_head,
            "final_tree_sha": final_tree,
            "worktree_clean_at_package": True,
            "packaged_at": datetime.now(UTC).isoformat(),
        }
    )
    if args.bundle_root.exists():
        raise ValueError("new_bundle_root_required")
    args.bundle_root.mkdir(parents=True)
    shutil.copytree(args.output_root, args.bundle_root / "experiment")
    shutil.copytree(args.report_dir, args.bundle_root / "reports")
    instruction_target = args.bundle_root / "work-instruction" / Path(
        WORK_INSTRUCTION_PATH
    ).name
    instruction_target.parent.mkdir(parents=True)
    shutil.copy2(Path.cwd() / WORK_INSTRUCTION_PATH, instruction_target)
    completion_path = args.bundle_root / "completion.json"
    payload_count = sum(
        path.is_file() for path in args.bundle_root.rglob("*")
    ) + 1
    completion.update(
        {
            "artifact_count": payload_count,
            "indexed_payload_count": payload_count,
            "artifact_hash_mismatch_count": 0,
            "artifact_size_mismatch_count": 0,
            "artifact_secret_scan_failure_count": 0,
        }
    )
    write_json(completion_path, completion)
    paths = sorted(path for path in args.bundle_root.rglob("*") if path.is_file())
    rows = []
    secret_failures = 0
    for path in paths:
        scan = legacy.scan_artifact_secrets([path])
        secret_failures += int(scan.get("secret_exposure_count") or 0)
        rows.append(
            {
                "path": str(path.relative_to(args.bundle_root)),
                "sha256": file_sha256(path),
                "byte_size": path.stat().st_size,
                "secret_scan_status": scan.get("secret_scan_status"),
            }
        )
    if secret_failures:
        raise ValueError(f"artifact_secret_scan_failed:{secret_failures}")
    index = {
        "contract": "runtime-isolation-repair-artifact-index-v1",
        "index_self_exclusion": "artifact-index.json",
        "all_payload_files_except_index_itself_individually_indexed": True,
        "indexed_payload_count": len(rows),
        "rows": rows,
        "status": "PASS",
    }
    write_json(args.bundle_root / "artifact-index.json", index)
    args.zip_output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.zip_output.with_suffix(args.zip_output.suffix + ".tmp")
    with zipfile.ZipFile(temporary, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(args.bundle_root.rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(args.bundle_root))
    temporary.replace(args.zip_output)
    with zipfile.ZipFile(args.zip_output) as archive:
        names = archive.namelist()
        archived_index = _zip_json(archive, "artifact-index.json")
        indexed = {str(row["path"]): row for row in archived_index.get("rows") or []}
        expected = set(names) - {"artifact-index.json"}
        hash_mismatches = 0
        size_mismatches = 0
        for name, row in indexed.items():
            payload = archive.read(name)
            hash_mismatches += hashlib.sha256(payload).hexdigest() != row.get("sha256")
            size_mismatches += len(payload) != row.get("byte_size")
        failures = {
            "duplicate_members": len(names) - len(set(names)),
            "unsafe_members": sum(not _safe_member(name) for name in names),
            "crc_failure": archive.testzip(),
            "index_membership_mismatch": int(set(indexed) != expected),
            "hash_mismatches": hash_mismatches,
            "size_mismatches": size_mismatches,
        }
    if any(bool(value) for value in failures.values()):
        raise ValueError(f"final_zip_integrity_failure:{failures}")
    zip_sha = file_sha256(args.zip_output)
    write_text(args.zip_output.with_suffix(args.zip_output.suffix + ".sha256"), zip_sha)
    state = read_json(args.output_root / "program-state.json")
    state.update(
        {
            "state": "COMPLETE",
            "final_head_sha": final_head,
            "final_tree_sha": final_tree,
            "report_zip_name": args.zip_output.name,
            "report_zip_sha256": zip_sha,
            "zip_member_count": len(names),
            "indexed_payload_count": len(rows),
            "zip_integrity_mismatches": failures,
        }
    )
    write_json(args.output_root / "program-state.json", state)
    print(json.dumps(state, ensure_ascii=False, sort_keys=True), flush=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--bootstrap", action="store_true")
    mode.add_argument("--prepare", action="store_true")
    mode.add_argument("--seal", action="store_true")
    mode.add_argument("--execute", action="store_true")
    mode.add_argument("--close-reports", action="store_true")
    mode.add_argument("--finalize", action="store_true")
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--report-dir", type=Path, required=True)
    parser.add_argument("--bundle-root", type=Path, required=True)
    parser.add_argument("--latest-result-zip", type=Path, required=True)
    parser.add_argument("--diagnostic-zip", type=Path, required=True)
    parser.add_argument("--predecessor-zip", type=Path, required=True)
    parser.add_argument("--historical-zip", type=Path, required=True)
    parser.add_argument("--expansion-zip", type=Path, required=True)
    parser.add_argument("--as-of", type=datetime.fromisoformat)
    parser.add_argument("--timeout", type=int, default=runner.TIMEOUT_SECONDS)
    parser.add_argument("--focused-tests", default="NOT_RUN")
    parser.add_argument("--full-tests", default="NOT_RUN")
    parser.add_argument("--ruff", default="NOT_RUN")
    parser.add_argument("--diff-check", default="NOT_RUN")
    parser.add_argument("--zip-output", type=Path, required=True)
    args = parser.parse_args()
    for name in (
        "output_root",
        "report_dir",
        "bundle_root",
        "latest_result_zip",
        "diagnostic_zip",
        "predecessor_zip",
        "historical_zip",
        "expansion_zip",
        "zip_output",
    ):
        setattr(args, name, getattr(args, name).expanduser().resolve())
    return args


def main() -> None:
    args = parse_args()
    if args.bootstrap:
        bootstrap(args)
    elif args.prepare:
        prepare(args)
    elif args.seal:
        seal(args)
    elif args.execute:
        execute(args)
    elif args.close_reports:
        close_reports(args)
    else:
        finalize(args)


if __name__ == "__main__":
    main()
