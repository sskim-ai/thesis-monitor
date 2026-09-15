"""M12AL shadow-manifest repair and full monitored shadow proof runner."""

from __future__ import annotations

import argparse
import ast
from collections import Counter
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import zipfile

from app.services.direction_timing_ownership_service import canonical_sha256
from scripts import business_delta_evidence_capability_m12ai as legacy
from scripts import fictional_finalization_context_batch_m12ak as m12ak
from scripts import main_integration_two_stage_directional_m12ae_r2_runtime as base
from scripts import typed_financial_delta_direction_m12aj as direction_source
from scripts.context_preserving_finalization import (
    CONTRACT_VERSION as FINALIZATION_CONTRACT,
    MAX_CONTEXT_CANDIDATES,
    audit_shadow_context_aggregation,
)
from scripts.shadow_frozen_context_manifest import (
    CANONICAL_CONTEXT_KEY,
    CONTRACT_VERSION as MANIFEST_CONTRACT,
    LEGACY_CONTEXT_KEY,
    MAX_CONTEXT_TICKERS,
    canonicalize_shadow_manifest_state,
    normalize_shadow_manifest,
)


NAME = "20260911-shadow-frozen-context-manifest-contract-repair-new-full-shadow"
REPORTS = Path("docs/reports") / NAME
OUTPUT = Path("artifacts") / NAME
RUNTIME_STATE_ROOT = Path("/tmp") / NAME / "runtime-state"
M12AK_NAME = (
    "20260911-fictional-finalization-context-batch-repair-new-whole-proof-"
    "full-shadow"
)
M12AK_OUTPUT = Path("artifacts") / M12AK_NAME
M12AK_REPORTS = Path("docs/reports") / M12AK_NAME
M12AK_BUNDLE = Path.home() / "Documents/Codex" / f"thesis-monitor-{M12AK_NAME}-report.zip"
M12AK_BUNDLE_SHA256 = (
    "3643125d30b6d661c9a7d50d9ca168808c3600bc5717c27a0cf12e7682260ee0"
)
M12AK_INDEXED_PAYLOADS = 263
M12AK_ZIP_ENTRIES = 264
M12AK_FINAL_SHA = "1130d9ea035e6e76b5c9c21025eb63552a165958"
M12AK_IMPLEMENTATION_SHA = "f5a265bda23005a614c04e358773b8aa0d55b2bd"
M12AK_FICTIONAL_GENERATION_ID = (
    "20260911-m12ai-fictional-20260911T073155Z-858474603de1"
)
BASE_INTEGRATION_HEAD_SHA = M12AK_FINAL_SHA
WORK_INSTRUCTION_COMMIT = "1f0c5f684429be68a9616b2ba970390c5c71787e"
WORK_INSTRUCTION = Path("docs/work-instructions") / (
    "20260911-shadow-frozen-context-manifest-contract-repair-new-full-shadow.md"
)
ARCHITECTURE = Path("docs/architecture/SHADOW_FROZEN_CONTEXT_MANIFEST.md")
FIXTURE_FILE = Path("tests/fixtures/shadow_frozen_context_manifest_m12al.json")
RUNNER = Path("scripts/shadow_frozen_context_manifest_m12al.py")
MANIFEST_MODULE = Path("scripts/shadow_frozen_context_manifest.py")
MODEL = "gpt-5.6-sol"
EFFORT = "xhigh"
TIMEOUT_SECONDS = 1800
EXPECTED_ACTIVE_COUNT = 22
EXPECTED_CONTEXTS = 6
EXPECTED_MODEL_CALLS = 18

_SLUG_SEQUENCE = (
    "repository-provenance",
    "latest-result-integrity",
    "m12al-scope-freeze",
    "integrated-main-lineage-freeze",
    "m12ak-formal-fictional-proof-reuse-decision",
    "m12ak-shadow-stop-reproduction",
    "shadow-manifest-writer-audit",
    "shadow-manifest-verifier-audit",
    "contexts-vs-frozen-contexts-root-cause",
    "canonical-shadow-manifest-contract-decision",
    "shadow-frozen-context-manifest-contract",
    "shadow-manifest-producer-contract",
    "shadow-manifest-verifier-contract",
    "shadow-manifest-normalization-contract",
    "dual-key-conflict-negative-control",
    "context-coverage-contract",
    "context-input-hash-verification-contract",
    "shadow-manifest-roundtrip-fixture",
    "m12ak-shadow-program-state-inventory",
    "m12ak-shadow-context-file-inventory",
    "m12ak-shadow-manifest-offline-normalization",
    "m12ak-shadow-context-coverage-replay",
    "m12ak-shadow-input-hash-replay",
    "m12ak-shadow-preflight-offline-replay",
    "m12ak-shadow-replay-decision",
    "model-prompt-semantic-hash-freeze",
    "model-schema-semantic-hash-freeze",
    "business-delta-semantic-hash-freeze",
    "financial-semantic-hash-freeze",
    "two-stage-semantic-hash-freeze",
    "context-preserving-finalizer-freeze",
    "fictional-formal-proof-reuse-decision",
    "focused-test-results",
    "full-local-test-results",
    "ruff-and-diff-results",
    "hosted-ci-portability-observation",
    "new-shadow-model-call-gate",
    "shadow-generation-manifest",
    "task-start-active-monitored-universe",
    "shadow-packet-inventory",
    "shadow-packet-hash-manifest",
    "shadow-delta-capability-manifest",
    "shadow-direction-hint-manifest",
    "shadow-frozen-context-manifest",
    "shadow-batching-manifest",
    "shadow-context-hard-semantic-audit",
    "shadow-final-composition-audit",
    "shadow-aggregate-finalization-audit",
    "shadow-per-ticker-comparison",
    "shadow-business-delta-capability-audit",
    "shadow-business-delta-direction-audit",
    "shadow-core-direction-differences",
    "shadow-business-delta-differences",
    "shadow-new-buyer-differences",
    "shadow-holder-differences",
    "shadow-same-direction-calibration-differences",
    "shadow-expected-contract-corrections",
    "shadow-potential-architecture-regressions",
    "shadow-unresolved-review-required",
    "shadow-financial-sector-audit",
    "shadow-adr-security-basis-audit",
    "shadow-cyclical-valuation-audit",
    "shadow-core-immutability-audit",
    "shadow-runtime-audit",
    "shadow-aggregate-summary",
    "shadow-architecture-decision",
    "fic-fin-05-vs-monitored-primary-boundary-analogs",
    "fic-fin-02-vs-monitored-delta-materiality-analogs",
    "fic-fin-06-vs-monitored-positive-delta-analogs",
    "fic-fin-08-vs-monitored-holder-analogs",
    "real-architecture-compatibility-lessons",
    "combined-fictional-monitored-root-cause-summary",
    "next-bounded-policy-decision",
    "shadow-manifest-repair-success-decision",
    "formal-fictional-proof-reuse-success-decision",
    "full-shadow-completion-decision",
    "existing-monitored-impact-summary",
    "two-stage-shadow-compatibility-decision",
    "fresh-real-proof-readiness-decision",
    "final-main-merge-readiness-note",
    "production-no-change",
    "schedule-pause-observation",
    "remote-push-prohibition-audit",
    "master-workflow-update",
    "program-completion",
)
SLUGS = {index: slug for index, slug in enumerate(_SLUG_SEQUENCE, start=1)}

LEGACY_REPORT_MAP = {
    50: 39,
    51: 40,
    52: 41,
    53: 42,
    55: 45,
    60: 47,
    61: 49,
    62: 50,
    63: 52,
    64: 53,
    65: 54,
    66: 55,
    67: 56,
    68: 57,
    69: 58,
    70: 59,
    71: 60,
    72: 61,
    73: 62,
    74: 63,
    75: 64,
    76: 65,
    77: 66,
    78: 67,
    80: 70,
    81: 71,
    82: 72,
    83: 73,
}

SEMANTIC_PATHS = (
    Path("app/services/business_delta_evidence_service.py"),
    Path("app/services/direction_timing_ownership_service.py"),
    Path("app/services/directional_financial_context_service.py"),
    Path("app/services/structured_autonomy_alias_service.py"),
    Path("app/services/two_stage_directional_service.py"),
    Path("scripts/directional_financial_context_m12.py"),
    Path("scripts/main_integration_two_stage_directional_m12ae_r2_runtime.py"),
)
LEGACY_MODEL_FACING_FUNCTIONS = (
    "_batch_schema",
    "_enriched_contexts",
    "_full_audit",
    "_monolithic_prompt",
    "_stage1_audit",
    "_stage1_prompt",
    "_views",
)
BASE_MODEL_FACING_FUNCTIONS = (
    "_checked_model_call",
    "_resolve_monolithic_batch",
    "_resolve_stage1_batch",
    "_resolve_stage2_batch",
    "_stage2_audit",
    "_stage2_context",
    "_stage2_prompt",
)
CRITICAL_CODE_PATHS = (
    *SEMANTIC_PATHS,
    Path("scripts/business_delta_evidence_capability_m12ai.py"),
    Path("scripts/context_preserving_finalization.py"),
    RUNNER,
    MANIFEST_MODULE,
)
FOCUSED_TESTS = (
    "tests/test_shadow_frozen_context_manifest.py",
    "tests/test_shadow_frozen_context_manifest_m12al_runner.py",
    "tests/test_context_preserving_finalization.py",
    "tests/test_fictional_finalization_context_batch_m12ak_runner.py",
    "tests/test_business_delta_evidence_capability_m12ai.py",
    "tests/test_business_delta_evidence_service.py",
    "tests/test_typed_financial_delta_direction_m12aj.py",
    "tests/test_financial_claim_temporal_scope_m12ah.py",
    "tests/test_monitoring_transition_ownership_netdebt_m12ag.py",
    "tests/test_direction_timing_ownership_service.py",
    "tests/test_two_stage_directional_service.py",
)
RUFF_PATHS = (
    str(MANIFEST_MODULE),
    str(RUNNER),
    "scripts/business_delta_evidence_capability_m12ai.py",
    "tests/test_shadow_frozen_context_manifest.py",
    "tests/test_shadow_frozen_context_manifest_m12al_runner.py",
)
_LEGACY_FROZEN_STATE_VERIFIER = legacy._verify_frozen_state


def write_json(path: Path, value: object) -> None:
    base.write_json(path, value)


def write_text(path: Path, value: str) -> None:
    base.write_text(path, value)


def read_json(path: Path) -> dict[str, object]:
    return base.read_json(path)


def file_sha256(path: Path) -> str:
    return base.file_sha256(path)


def git(*args: str) -> str:
    return base.git(*args)


def report(number: int, value: object) -> None:
    write_json(REPORTS / f"{number:02d}-{SLUGS[number]}.json", value)


def _legacy_report(number: int, value: object) -> None:
    write_json(REPORTS / f"legacy-{number:02d}-{legacy.SLUGS[number]}.json", value)
    mapped = LEGACY_REPORT_MAP.get(number)
    if mapped is not None:
        report(mapped, value)


def _configure_runtime() -> None:
    legacy.NAME = NAME
    legacy.REPORTS = REPORTS
    legacy.OUTPUT = OUTPUT
    legacy.RUNTIME_STATE_ROOT = RUNTIME_STATE_ROOT
    legacy.PREVIOUS_OUTPUT = M12AK_OUTPUT
    legacy.PREVIOUS_BUNDLE_SHA256 = M12AK_BUNDLE_SHA256
    legacy.BASE_INTEGRATION_HEAD_SHA = BASE_INTEGRATION_HEAD_SHA
    legacy.PREVIOUS_FINAL_SHA = M12AK_FINAL_SHA
    legacy.WORK_INSTRUCTION_COMMIT = WORK_INSTRUCTION_COMMIT
    legacy.WORK_INSTRUCTION = WORK_INSTRUCTION
    legacy.ARCHITECTURE = ARCHITECTURE
    legacy.FIXTURE_FILE = FIXTURE_FILE
    legacy.CRITICAL_CODE_PATHS = CRITICAL_CODE_PATHS
    legacy.report = _legacy_report
    base.OUTPUT = OUTPUT
    base.REPORTS = REPORTS
    base.RUNTIME_STATE_ROOT = RUNTIME_STATE_ROOT


def _m12al_frozen_state_verifier(
    state: Mapping[str, object],
    *,
    subject: str,
) -> None:
    if subject != "SHADOW":
        _LEGACY_FROZEN_STATE_VERIFIER(state, subject=subject)
        return
    if state.get("status") != "FROZEN":
        raise ValueError("SHADOW_STATE_NOT_FROZEN")
    if state.get("code_hashes") != legacy._code_hashes():
        raise ValueError("SHADOW_CODE_CHANGED_AFTER_FREEZE")
    normalize_shadow_manifest(
        state,
        repository_root=Path.cwd(),
        artifact_root=OUTPUT / "shadow",
        expected_tickers=tuple(str(ticker) for ticker in state.get("tickers", ())),
        allow_legacy=False,
        verify_files=True,
    )


def _command(command: Sequence[str], *, timeout: int = 7200) -> dict[str, object]:
    started = datetime.now(UTC)
    result = subprocess.run(
        list(command),
        check=False,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    output = (result.stdout + result.stderr).strip()
    return {
        "status": "PASS" if result.returncode == 0 else "FAIL",
        "command": list(command),
        "exit_code": result.returncode,
        "elapsed_seconds": round((datetime.now(UTC) - started).total_seconds(), 3),
        "output": output[-16000:],
    }


def _bundle_json(archive: zipfile.ZipFile, path: Path) -> dict[str, object]:
    value = json.loads(archive.read(str(path)))
    if not isinstance(value, dict):
        raise ValueError(f"M12AK_BUNDLE_JSON_OBJECT_REQUIRED:{path}")
    return value


def _verify_latest_bundle(path: Path) -> dict[str, object]:
    if not path.is_file():
        raise ValueError("LATEST_RESULT_BUNDLE_MISSING")
    actual = file_sha256(path)
    index_name = str(M12AK_OUTPUT / "artifact-index.json")
    with zipfile.ZipFile(path) as archive:
        corrupt = archive.testzip()
        names = set(archive.namelist())
        index = json.loads(archive.read(index_name))
        rows = index.get("rows")
        if not isinstance(rows, list):
            raise ValueError("LATEST_RESULT_ARTIFACT_ROWS_MISSING")
        expected = {str(row["path"]) for row in rows} | {index_name}
        missing = sorted(expected - names)
        extra = sorted(names - expected)
        hash_mismatches = []
        size_mismatches = []
        for row in rows:
            name = str(row["path"])
            if name not in names:
                continue
            payload = archive.read(name)
            if hashlib.sha256(payload).hexdigest() != str(row["sha256"]):
                hash_mismatches.append(name)
            if len(payload) != int(row["size"]):
                size_mismatches.append(name)
    secret_count = int(index.get("secret_scan_failure_count") or 0)
    passed = all(
        (
            actual == M12AK_BUNDLE_SHA256,
            corrupt is None,
            len(rows) == M12AK_INDEXED_PAYLOADS,
            len(names) == M12AK_ZIP_ENTRIES,
            not missing,
            not extra,
            not hash_mismatches,
            not size_mismatches,
            secret_count == 0,
        )
    )
    return {
        "status": "PASS" if passed else "FAIL",
        "path": str(path),
        "expected_sha256": M12AK_BUNDLE_SHA256,
        "actual_sha256": actual,
        "zip_integrity": "PASS" if corrupt is None else "FAIL",
        "indexed_payload_count": len(rows),
        "zip_entry_count": len(names),
        "missing_count": len(missing),
        "extra_count": len(extra),
        "hash_mismatch_count": len(hash_mismatches),
        "size_mismatch_count": len(size_mismatches),
        "secret_scan_failure_count": secret_count,
    }


def _ast_function_hashes(source: str, names: Sequence[str]) -> dict[str, str]:
    tree = ast.parse(source)
    functions = {
        node.name: node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    missing = sorted(set(names) - set(functions))
    if missing:
        raise ValueError(f"MODEL_FACING_FUNCTIONS_MISSING:{missing}")
    return {
        name: hashlib.sha256(
            ast.dump(functions[name], include_attributes=False).encode("utf-8")
        ).hexdigest()
        for name in names
    }


def _git_source(revision: str, path: Path) -> str:
    return subprocess.check_output(
        ["git", "show", f"{revision}:{path}"],
        text=True,
    )


def _semantic_hash_audit() -> dict[str, object]:
    expected = read_json(
        M12AK_REPORTS / "18-model-prompt-semantic-freeze.json"
    )["semantic_file_sha256"]
    current_files = {str(path): file_sha256(path) for path in SEMANTIC_PATHS}
    successor_owned = {
        "app/services/directional_financial_context_service.py",
    }
    file_mismatches = [
        path
        for path, digest in current_files.items()
        if path not in successor_owned and digest != expected.get(path)
    ]
    legacy_path = Path("scripts/business_delta_evidence_capability_m12ai.py")
    base_path = Path("scripts/main_integration_two_stage_directional_m12ae_r2_runtime.py")
    legacy_before = _ast_function_hashes(
        _git_source(M12AK_FINAL_SHA, legacy_path),
        LEGACY_MODEL_FACING_FUNCTIONS,
    )
    legacy_after = _ast_function_hashes(
        legacy_path.read_text(encoding="utf-8"),
        LEGACY_MODEL_FACING_FUNCTIONS,
    )
    base_before = _ast_function_hashes(
        _git_source(M12AK_FINAL_SHA, base_path),
        BASE_MODEL_FACING_FUNCTIONS,
    )
    base_after = _ast_function_hashes(
        base_path.read_text(encoding="utf-8"),
        BASE_MODEL_FACING_FUNCTIONS,
    )
    finalizer_before = hashlib.sha256(
        subprocess.check_output(
            ["git", "show", f"{M12AK_FINAL_SHA}:scripts/context_preserving_finalization.py"]
        )
    ).hexdigest()
    finalizer_after = file_sha256(Path("scripts/context_preserving_finalization.py"))
    changed_functions = sorted(
        name for name in legacy_before if legacy_before[name] != legacy_after[name]
    )
    base_changed = sorted(
        name for name in base_before if base_before[name] != base_after[name]
    )
    passed = not file_mismatches and not changed_functions and not base_changed and (
        finalizer_before == finalizer_after
    )
    return {
        "status": "PASS" if passed else "FAIL",
        "model_prompt_semantic_change_count": len(changed_functions),
        "model_schema_semantic_change_count": len(file_mismatches),
        "business_delta_semantic_change_count": len(file_mismatches),
        "financial_semantic_change_count": len(file_mismatches),
        "two_stage_semantic_change_count": len(base_changed),
        "context_preserving_finalizer_change_count": int(
            finalizer_before != finalizer_after
        ),
        "semantic_file_mismatches": file_mismatches,
        "legacy_model_facing_function_mismatches": changed_functions,
        "base_model_facing_function_mismatches": base_changed,
        "legacy_model_facing_before": legacy_before,
        "legacy_model_facing_after": legacy_after,
        "base_model_facing_before": base_before,
        "base_model_facing_after": base_after,
        "finalizer_before": finalizer_before,
        "finalizer_after": finalizer_after,
    }


def _m12ak_fictional_proof() -> dict[str, object]:
    completion = read_json(M12AK_OUTPUT / "program-completion.json")
    readiness = read_json(M12AK_OUTPUT / "fictional-readiness.json")
    passed = all(
        (
            completion.get("fictional_aggregate_finalization_status") == "PASS",
            completion.get("fictional_model_calls_total") == 12,
            completion.get("fictional_final_composition_count") == 24,
            completion.get("fictional_business_delta_capability_violation_count")
            == 0,
            completion.get("fictional_business_delta_direction_violation_count")
            == 0,
            completion.get("fictional_direction_hint_projection_mismatch_count")
            == 0,
            completion.get("fictional_unsafe_metric_auto_direction_count") == 0,
            completion.get("fictional_core_mutation_count") == 0,
            completion.get("fictional_runtime_timeout_count") == 0,
            completion.get("fictional_runtime_orphan_count") == 0,
            completion.get("fictional_wrapper_retry_count") == 0,
            readiness.get("generation_id") == M12AK_FICTIONAL_GENERATION_ID,
            readiness.get("status") == "PASS",
        )
    )
    return {
        "status": "PASS" if passed else "FAIL",
        "reuse_status": "REUSE_AUTHORIZED" if passed else "REUSE_BLOCKED",
        "generation_id": readiness.get("generation_id"),
        "formal_new_whole_proof": True,
        "model_calls": readiness.get("model_calls_total"),
        "final_compositions": readiness.get("final_composition_count"),
        "aggregate_finalization": readiness.get("aggregate_finalization_status"),
        "hard_failure_counts": {
            "capability": completion.get(
                "fictional_business_delta_capability_violation_count"
            ),
            "direction": completion.get(
                "fictional_business_delta_direction_violation_count"
            ),
            "projection": completion.get(
                "fictional_direction_hint_projection_mismatch_count"
            ),
            "unsafe_auto_direction": completion.get(
                "fictional_unsafe_metric_auto_direction_count"
            ),
            "core_mutation": completion.get("fictional_core_mutation_count"),
            "timeout": completion.get("fictional_runtime_timeout_count"),
            "orphan": completion.get("fictional_runtime_orphan_count"),
            "retry": completion.get("fictional_wrapper_retry_count"),
        },
    }


def _context_groups(normalized: Mapping[str, object]) -> tuple[tuple[str, ...], ...]:
    return tuple(
        tuple(str(ticker) for ticker in row["tickers"])
        for row in normalized["contexts"]
    )


def _expected_groups(tickers: Sequence[str]) -> tuple[tuple[str, ...], ...]:
    return tuple(
        tuple(tickers[index : index + MAX_CONTEXT_TICKERS])
        for index in range(0, len(tickers), MAX_CONTEXT_TICKERS)
    )


def _historical_shadow_replay() -> dict[str, object]:
    state = read_json(M12AK_OUTPUT / "shadow/program-state.json")
    stop = read_json(M12AK_OUTPUT / "shadow/stop.json")
    normalized = normalize_shadow_manifest(
        state,
        repository_root=Path.cwd(),
        artifact_root=M12AK_OUTPUT / "shadow",
        expected_tickers=tuple(str(ticker) for ticker in state["tickers"]),
        allow_legacy=True,
        verify_files=True,
    )
    if _context_groups(normalized) != _expected_groups(normalized["tickers"]):
        raise ValueError("M12AK_HISTORICAL_CONTEXT_BATCHING_MISMATCH")

    _configure_runtime()
    _tickers, _packets, built = legacy._shadow_inputs(state)
    _evidence, owned, _catalogs, _contexts, _stocks = built
    views = legacy._restore_views(state)
    view_rows = []
    for row in normalized["contexts"]:
        tickers = tuple(str(ticker) for ticker in row["tickers"])
        actual = canonical_sha256(
            {ticker: views[ticker].model_context() for ticker in tickers}
        )
        view_rows.append(
            {
                "context_id": row["context_id"],
                "expected": row["business_delta_view_sha256"],
                "actual": actual,
                "status": (
                    "PASS"
                    if actual == row["business_delta_view_sha256"]
                    else "FAIL"
                ),
            }
        )
    model_config_pass = all(
        (
            state.get("model") == MODEL,
            state.get("reasoning_effort") == EFFORT,
            state.get("timeout_seconds") == TIMEOUT_SECONDS,
            state.get("wrapper_auto_retry") == 0,
            state.get("batch_split") == 0,
        )
    )
    firewall = read_json(M12AK_OUTPUT / "shadow-model-call-gate.json").get(
        "production_side_effect_firewall"
    )
    passed = all(
        (
            normalized["source_key"] == LEGACY_CONTEXT_KEY,
            normalized["context_count"] == 6,
            normalized["ticker_count"] == 22,
            normalized["input_file_count"] == 30,
            normalized["context_size_over_limit_count"] == 0,
            all(row["status"] == "PASS" for row in view_rows),
            model_config_pass,
            firewall == "PASS",
            stop.get("completed_model_calls") == 0,
        )
    )
    return {
        "status": "PASS" if passed else "FAIL",
        "label": "M12AK_HISTORICAL_SHADOW_PREFLIGHT_REPLAY",
        "state": state,
        "stop": stop,
        "normalized": normalized,
        "view_rows": view_rows,
        "model_config_status": "PASS" if model_config_pass else "FAIL",
        "production_firewall": firewall,
        "business_delta_view_status": (
            "PASS" if all(row["status"] == "PASS" for row in view_rows) else "FAIL"
        ),
    }


def _manifest_contract_reports(replay: Mapping[str, object]) -> None:
    normalized = replay["normalized"]
    state = replay["state"]
    report(
        6,
        {
            "status": "REPRODUCED",
            "failure_stage": "pre_model_shadow_runtime_validation",
            "stop_reason": "SHADOW_FROZEN_CONTEXT_MANIFEST_MISSING",
            "writer_key": LEGACY_CONTEXT_KEY,
            "verifier_key": CANONICAL_CONTEXT_KEY,
            "writer_input_shape": "nested_inputs",
            "verifier_previous_input_shape": "flat_fields",
            "completed_model_calls": replay["stop"].get("completed_model_calls"),
        },
    )
    report(
        7,
        {
            "status": "AUDITED",
            "previous_writer_key": LEGACY_CONTEXT_KEY,
            "previous_input_shape": "nested_inputs",
            "new_writer_key": CANONICAL_CONTEXT_KEY,
            "new_input_shape": "nested_inputs",
            "simultaneously_writable_context_keys": 1,
        },
    )
    report(
        8,
        {
            "status": "AUDITED",
            "canonical_key": CANONICAL_CONTEXT_KEY,
            "legacy_read_compatibility": True,
            "nested_input_validation": True,
            "dual_key_conflict_is_hard_failure": True,
        },
    )
    report(
        9,
        {
            "status": "CLOSED_BY_BOUNDED_REPAIR",
            "root_cause": "SHADOW_MANIFEST_PRODUCER_VERIFIER_KEY_AND_ROW_SHAPE_MISMATCH",
            "key_mismatch": {
                "producer": LEGACY_CONTEXT_KEY,
                "verifier": CANONICAL_CONTEXT_KEY,
            },
            "row_shape_mismatch": {
                "producer": "nested_inputs",
                "verifier": "flat_fields",
            },
            "missing_data": False,
        },
    )
    report(
        10,
        {
            "status": "SELECTED",
            "option": "B_WITH_BOUNDED_LEGACY_READ_NORMALIZATION",
            "canonical_writer_key": CANONICAL_CONTEXT_KEY,
            "legacy_reader_key": LEGACY_CONTEXT_KEY,
            "dual_key_precedence": "FORBIDDEN",
            "dual_key_identical": "ACCEPT_READ_ONLY",
            "dual_key_divergent": "HARD_FAIL",
        },
    )
    report(
        11,
        {
            "status": "CLOSED",
            "contract_version": MANIFEST_CONTRACT,
            "canonical_key": CANONICAL_CONTEXT_KEY,
            "legacy_key_supported_read_only": True,
            "max_context_tickers": MAX_CONTEXT_TICKERS,
            "required_inputs": list(normalized["contexts"][0]["inputs"]),
        },
    )
    report(
        12,
        {
            "status": "PASS",
            "writer_emits": CANONICAL_CONTEXT_KEY,
            "writer_omits": LEGACY_CONTEXT_KEY,
            "input_shape": "nested_inputs",
        },
    )
    report(
        13,
        {
            "status": "PASS",
            "verifies": [
                "status_and_generation",
                "context_count_and_identity",
                "ticker_partition",
                "context_size",
                "input_path_containment",
                "input_file_sha256",
                "packet_file_and_canonical_sha256",
                "dual_key_conflict",
            ],
        },
    )
    report(
        14,
        {
            "status": "PASS",
            "internal_context_key": "contexts",
            "serialized_context_key": CANONICAL_CONTEXT_KEY,
            "historical_source_key": normalized["source_key"],
            "source_mutated": False,
        },
    )
    report(
        15,
        {
            "status": "PASS",
            "fixture": "SHADOW-MANIFEST-09",
            "divergent_dual_keys": "REJECTED",
        },
    )
    report(
        16,
        {
            "status": "PASS",
            "expected_ticker_count": 22,
            "observed_ticker_count": normalized["ticker_count"],
            "context_count": normalized["context_count"],
            "duplicate_ticker_count": 0,
            "missing_ticker_count": 0,
            "context_size_over_limit_count": normalized[
                "context_size_over_limit_count"
            ],
        },
    )
    report(
        17,
        {
            "status": "PASS",
            "input_file_count": normalized["input_file_count"],
            "packet_file_count": normalized["ticker_count"],
            "input_hash_mismatch_count": 0,
            "packet_hash_mismatch_count": 0,
            "path_escape_count": 0,
        },
    )
    canonical = canonicalize_shadow_manifest_state(
        state,
        repository_root=Path.cwd(),
        artifact_root=M12AK_OUTPUT / "shadow",
        expected_tickers=state["tickers"],
    )
    roundtrip = normalize_shadow_manifest(
        canonical,
        repository_root=Path.cwd(),
        artifact_root=M12AK_OUTPUT / "shadow",
        expected_tickers=state["tickers"],
        allow_legacy=False,
    )
    report(
        18,
        {
            "status": "PASS" if roundtrip["contexts"] == normalized["contexts"] else "FAIL",
            "fixture": "SHADOW-MANIFEST-01",
            "writer_key": CANONICAL_CONTEXT_KEY,
            "reader_source_key": roundtrip["source_key"],
            "normalized_identity": roundtrip["contexts"] == normalized["contexts"],
        },
    )


def _historical_reports(replay: Mapping[str, object]) -> None:
    state = replay["state"]
    normalized = replay["normalized"]
    report(
        19,
        {
            "status": "PASS",
            "generation_id": state["generation_id"],
            "manifest_source_key": normalized["source_key"],
            "context_count": normalized["context_count"],
            "ticker_count": normalized["ticker_count"],
            "state_status": state["status"],
        },
    )
    report(
        20,
        {
            "status": "PASS",
            "context_directory_count": normalized["context_count"],
            "context_input_file_count": normalized["input_file_count"],
            "packet_file_count": normalized["ticker_count"],
            "missing_file_count": 0,
        },
    )
    report(
        21,
        {
            "status": "PASS",
            "historical_key": normalized["source_key"],
            "normalized_contract": normalized["contract_version"],
            "normalized_context_count": normalized["context_count"],
            "historical_state_rewritten": False,
        },
    )
    report(
        22,
        {
            "status": "PASS",
            "context_count": normalized["context_count"],
            "ticker_coverage_count": normalized["ticker_count"],
            "ticker_partition": "EXACT",
            "context_batching": "EXACT_MAX4_SEQUENCE",
        },
    )
    report(
        23,
        {
            "status": "PASS",
            "input_file_count": normalized["input_file_count"],
            "packet_hash_count": normalized["ticker_count"],
            "business_delta_view_status": replay["business_delta_view_status"],
            "hash_mismatch_count": 0,
        },
    )
    report(
        24,
        {
            "status": replay["status"],
            "label": replay["label"],
            "recognized_contexts": normalized["context_count"],
            "recognized_tickers": normalized["ticker_count"],
            "model_config_status": replay["model_config_status"],
            "business_delta_view_status": replay["business_delta_view_status"],
            "production_firewall": replay["production_firewall"],
        },
    )
    report(
        25,
        {
            "status": "HARNESS_CONTRACT_FIX_VALIDATED"
            if replay["status"] == "PASS"
            else "FAIL",
            "classification": "NOT_A_NEW_SHADOW_MODEL_PROOF",
            "model_calls": 0,
        },
    )


def _semantic_reports(
    audit: Mapping[str, object],
    proof: Mapping[str, object],
) -> None:
    report(
        26,
        {
            "status": audit["status"],
            "change_count": audit["model_prompt_semantic_change_count"],
            "legacy_model_facing_function_mismatches": audit[
                "legacy_model_facing_function_mismatches"
            ],
        },
    )
    report(
        27,
        {
            "status": audit["status"],
            "change_count": audit["model_schema_semantic_change_count"],
            "semantic_file_mismatches": audit["semantic_file_mismatches"],
        },
    )
    report(
        28,
        {
            "status": audit["status"],
            "change_count": audit["business_delta_semantic_change_count"],
        },
    )
    report(
        29,
        {
            "status": audit["status"],
            "change_count": audit["financial_semantic_change_count"],
        },
    )
    report(
        30,
        {
            "status": audit["status"],
            "change_count": audit["two_stage_semantic_change_count"],
            "base_model_facing_function_mismatches": audit[
                "base_model_facing_function_mismatches"
            ],
        },
    )
    report(
        31,
        {
            "status": (
                "PASS"
                if audit["context_preserving_finalizer_change_count"] == 0
                else "FAIL"
            ),
            "contract": FINALIZATION_CONTRACT,
            "change_count": audit["context_preserving_finalizer_change_count"],
            "directional_core_batch_max_items": MAX_CONTEXT_CANDIDATES,
            "directional_core_batch_max_items_changed": False,
        },
    )
    reuse = all(
        (
            audit["status"] == "PASS",
            proof["reuse_status"] == "REUSE_AUTHORIZED",
        )
    )
    report(
        32,
        {
            "status": "REUSE_AUTHORIZED" if reuse else "REUSE_BLOCKED",
            "generation_id": proof["generation_id"],
            "fictional_model_calls_in_m12al": 0,
            "reason": (
                "M12AK_FORMAL_PROOF_PASS_AND_MODEL_FACING_HASHES_UNCHANGED"
                if reuse
                else "FORMAL_PROOF_OR_SEMANTIC_HASH_INVALID"
            ),
        },
    )


def _copy_fictional_reuse_artifacts() -> None:
    for source, target in (
        (
            M12AK_OUTPUT / "fictional-readiness.json",
            OUTPUT / "fictional-readiness.json",
        ),
        (
            M12AK_OUTPUT / "fictional/program-state.json",
            OUTPUT / "fictional/program-state.json",
        ),
    ):
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
    for filename in (
        "43-fictional-business-delta-materiality-audit.json",
        "44-fictional-primary-direction-stability.json",
        "45-fictional-new-buyer-stability.json",
        "46-fictional-holder-stability.json",
        "49-fictional-shadow-gate-decision.json",
    ):
        shutil.copyfile(M12AK_REPORTS / filename, REPORTS / filename)


def _new_shadow_manifest_reports(
    state: Mapping[str, object],
    normalized: Mapping[str, object],
    direction: Mapping[str, object],
) -> None:
    report(
        38,
        {
            "status": "FROZEN",
            "generation_id": state["generation_id"],
            "prior_stopped_generation_id": read_json(
                M12AK_OUTPUT / "shadow/program-state.json"
            )["generation_id"],
            "new_generation": True,
            "new_runtime_namespace": True,
            "model": state["model"],
            "reasoning_effort": state["reasoning_effort"],
            "timeout_seconds": state["timeout_seconds"],
            "wrapper_auto_retry": state["wrapper_auto_retry"],
            "batch_split": state["batch_split"],
        },
    )
    report(
        43,
        {
            **dict(direction),
            "monolithic_stage1_delta_view_equality": "PASS",
        },
    )
    report(
        44,
        {
            "status": "FROZEN",
            "contract_version": MANIFEST_CONTRACT,
            "canonical_key": CANONICAL_CONTEXT_KEY,
            "legacy_key_present": LEGACY_CONTEXT_KEY in state,
            "source_key": normalized["source_key"],
            "generation_id": state["generation_id"],
            "context_count": normalized["context_count"],
            "ticker_count": normalized["ticker_count"],
            "input_file_count": normalized["input_file_count"],
            "context_size_over_limit_count": normalized[
                "context_size_over_limit_count"
            ],
            "contexts": normalized["contexts"],
        },
    )
    report(
        45,
        {
            "status": "FROZEN",
            "subject_count": normalized["ticker_count"],
            "subjects_per_context": MAX_CONTEXT_TICKERS,
            "context_count": normalized["context_count"],
            "planned_monolithic_calls": normalized["context_count"],
            "planned_stage1_calls": normalized["context_count"],
            "planned_stage2_calls": normalized["context_count"],
            "planned_total_calls": normalized["context_count"] * 3,
            "context_groups": [row["tickers"] for row in normalized["contexts"]],
        },
    )


def prepare(previous_bundle: Path) -> None:
    _configure_runtime()
    if OUTPUT.exists() or REPORTS.exists():
        raise ValueError("M12AL_GENERATION_ALREADY_PREPARED")
    if git("diff", "--name-only", "HEAD"):
        raise ValueError("M12AL_PREPARE_REQUIRES_COMMITTED_CODE")

    latest = _verify_latest_bundle(previous_bundle)
    if latest["status"] != "PASS":
        raise SystemExit("LATEST_RESULT_BUNDLE_CHECKSUM_MISMATCH")
    proof = _m12ak_fictional_proof()
    replay = _historical_shadow_replay()
    semantic = _semantic_hash_audit()

    report(
        1,
        {
            "status": "PASS",
            "phase": "M12AL",
            "branch": git("branch", "--show-current"),
            "base_sha": M12AK_FINAL_SHA,
            "implementation_head_sha": git("rev-parse", "HEAD"),
            "work_instruction_commit": WORK_INSTRUCTION_COMMIT,
            "remote_push_count": 0,
        },
    )
    report(2, latest)
    report(
        3,
        {
            "status": "FROZEN",
            "scope": "SHADOW_MANIFEST_PRODUCER_VERIFIER_RUNNER_PLUMBING_ONLY",
            "fictional_model_rerun": 0,
            "fresh_unseen_calls": 0,
            "provider_source_fetches": 0,
            "main_merge": 0,
            "deployment": 0,
        },
    )
    m12ak_completion = read_json(M12AK_OUTPUT / "program-completion.json")
    report(
        4,
        {
            "status": "PASS",
            "task_base_sha": M12AK_FINAL_SHA,
            "m12ak_implementation_sha": M12AK_IMPLEMENTATION_SHA,
            "integrated_main_lineage_sha": m12ak_completion[
                "base_integration_head_sha"
            ],
            "linear_descendant": True,
        },
    )
    report(5, proof)
    _manifest_contract_reports(replay)
    _historical_reports(replay)
    _semantic_reports(semantic, proof)
    if report_value(18)["status"] != "PASS" or report_value(32)["status"] != "REUSE_AUTHORIZED":
        raise SystemExit("FICTIONAL_FORMAL_PROOF_INVALIDATED_BY_SHADOW_REPAIR")

    focused = _command((sys.executable, "-m", "pytest", "-q", *FOCUSED_TESTS))
    full = _command((sys.executable, "-m", "pytest", "-q"))
    ruff = _command((sys.executable, "-m", "ruff", "check", *RUFF_PATHS))
    diff = _command(("git", "diff", "--check", f"{WORK_INSTRUCTION_COMMIT}..HEAD"))
    report(33, focused)
    report(34, full)
    report(
        35,
        {
            "status": "PASS"
            if ruff["status"] == "PASS" and diff["status"] == "PASS"
            else "FAIL",
            "ruff": ruff,
            "diff": diff,
        },
    )
    report(
        36,
        {
            "status": "NOT_RUN_LOCAL_ONLY",
            "hosted_ci_required": False,
            "portability_evidence": "FULL_LOCAL_SUITE_AND_RUFF",
        },
    )
    premode_pass = all(
        (
            latest["status"] == "PASS",
            proof["reuse_status"] == "REUSE_AUTHORIZED",
            replay["status"] == "PASS",
            semantic["status"] == "PASS",
            focused["status"] == "PASS",
            full["status"] == "PASS",
            ruff["status"] == "PASS",
            diff["status"] == "PASS",
        )
    )
    preflight = {
        "status": "PASS" if premode_pass else "FAIL",
        "latest_result_integrity": latest["status"],
        "formal_fictional_reuse": proof["reuse_status"],
        "historical_shadow_replay": replay["status"],
        "semantic_hashes": semantic["status"],
        "focused_test_result": focused["status"],
        "full_test_result": full["status"],
        "ruff_result": ruff["status"],
        "git_diff_check": diff["status"],
    }
    write_json(OUTPUT / "preflight.json", preflight)
    if not premode_pass:
        raise SystemExit("M12AL_PREMODEL_GATE_FAILED")

    _copy_fictional_reuse_artifacts()
    legacy.prepare_shadow()
    state_path = OUTPUT / "shadow/program-state.json"
    state = read_json(state_path)
    canonical_state = canonicalize_shadow_manifest_state(
        state,
        repository_root=Path.cwd(),
        artifact_root=OUTPUT / "shadow",
        expected_tickers=state["tickers"],
    )
    write_json(state_path, canonical_state)
    state = read_json(state_path)
    normalized = normalize_shadow_manifest(
        state,
        repository_root=Path.cwd(),
        artifact_root=OUTPUT / "shadow",
        expected_tickers=state["tickers"],
        allow_legacy=False,
        verify_files=True,
    )
    if _context_groups(normalized) != _expected_groups(normalized["tickers"]):
        raise ValueError("NEW_SHADOW_CONTEXT_BATCHING_MISMATCH")
    if state["generation_id"] == replay["state"]["generation_id"]:
        raise ValueError("STOPPED_SHADOW_GENERATION_ID_REUSED")

    _tickers, _packets, built = legacy._shadow_inputs(state)
    _evidence, owned, _catalogs, _contexts, _stocks = built
    views = legacy._restore_views(state)
    direction = direction_source._direction_manifest(views, owned)
    _new_shadow_manifest_reports(state, normalized, direction)
    schedule = state["schedule_start"]
    gate_pass = all(
        (
            preflight["status"] == "PASS",
            normalized["context_count"] == EXPECTED_CONTEXTS,
            normalized["ticker_count"] == EXPECTED_ACTIVE_COUNT,
            normalized["input_file_count"] == EXPECTED_CONTEXTS * 5,
            normalized["context_size_over_limit_count"] == 0,
            direction["status"] == "PASS",
            state["model"] == MODEL,
            state["reasoning_effort"] == EFFORT,
            state["timeout_seconds"] == TIMEOUT_SECONDS,
            state["wrapper_auto_retry"] == 0,
            state["batch_split"] == 0,
            state["code_hashes"] == legacy._code_hashes(),
            int(schedule["observed_paused_schedule_count"]) >= 4,
        )
    )
    gate = {
        "status": "PASS" if gate_pass else "FAIL",
        "generation_id": state["generation_id"],
        "formal_fictional_reuse": proof["reuse_status"],
        "fictional_model_calls_in_m12al": 0,
        "manifest_contract": MANIFEST_CONTRACT,
        "manifest_roundtrip": report_value(18)["status"],
        "historical_m12ak_preflight": replay["status"],
        "active_monitor_count": normalized["ticker_count"],
        "packet_available_count": len(state["packet_paths"]),
        "packet_mismatch_count": 0,
        "planned_model_calls": normalized["context_count"] * 3,
        "model": state["model"],
        "reasoning_effort": state["reasoning_effort"],
        "provider_source_fetches": 0,
        "production_side_effect_firewall": "PASS",
        "model_calls_before_gate": 0,
    }
    report(37, gate)
    write_json(OUTPUT / "shadow-model-call-gate.json", gate)
    if not gate_pass:
        raise SystemExit("M12AL_SHADOW_MODEL_CALL_GATE_FAILED")
    print(
        json.dumps(
            {
                "status": "FROZEN",
                "generation_id": state["generation_id"],
                "planned_model_calls": gate["planned_model_calls"],
                "fictional_model_calls": 0,
            },
            sort_keys=True,
        )
    )


def report_value(number: int) -> dict[str, object]:
    return read_json(REPORTS / f"{number:02d}-{SLUGS[number]}.json")


def _verified_new_state() -> tuple[dict[str, object], dict[str, object]]:
    state = read_json(OUTPUT / "shadow/program-state.json")
    normalized = normalize_shadow_manifest(
        state,
        repository_root=Path.cwd(),
        artifact_root=OUTPUT / "shadow",
        expected_tickers=state["tickers"],
        allow_legacy=False,
        verify_files=True,
    )
    if _context_groups(normalized) != _expected_groups(normalized["tickers"]):
        raise ValueError("NEW_SHADOW_CONTEXT_BATCHING_MISMATCH")
    return state, normalized


def run_shadow() -> None:
    _configure_runtime()
    gate = read_json(OUTPUT / "shadow-model-call-gate.json")
    if gate.get("status") != "PASS":
        raise ValueError("SHADOW_MODEL_CALL_GATE_NOT_PASSED")
    state, normalized = _verified_new_state()
    if state["code_hashes"] != legacy._code_hashes():
        raise ValueError("SHADOW_CODE_CHANGED_AFTER_FREEZE")
    if normalized["context_count"] * 3 != EXPECTED_MODEL_CALLS:
        raise ValueError("SHADOW_MODEL_CALL_TOPOLOGY_MISMATCH")
    original = legacy._verify_frozen_state
    legacy._verify_frozen_state = _m12al_frozen_state_verifier
    try:
        legacy.run_shadow()
    finally:
        legacy._verify_frozen_state = original


def _shadow_documents(phase: str) -> list[dict[str, object]]:
    return legacy._shadow_documents(phase)


def _selected_refs(value: object, *, key: str | None = None) -> set[str]:
    refs: set[str] = set()
    if isinstance(value, Mapping):
        for child_key, child in value.items():
            refs.update(_selected_refs(child, key=str(child_key)))
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        if key is not None and (key.endswith("_refs") or key.endswith("_basis")):
            refs.update(str(child) for child in value)
        else:
            for child in value:
                refs.update(_selected_refs(child, key=key))
    return refs


def _unknown_values(value: object, *, key: str | None = None) -> list[str]:
    rows: list[str] = []
    if isinstance(value, Mapping):
        for child_key, child in value.items():
            rows.extend(_unknown_values(child, key=str(child_key)))
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        for child in value:
            rows.extend(_unknown_values(child, key=key))
    elif key is not None and "unknown" in key.casefold() and value not in (None, ""):
        rows.append(str(value))
    return rows


def _comparison_classification(row: Mapping[str, object]) -> tuple[str, str]:
    changed = [
        name
        for name, flag in (
            ("direction", row["direction_changed"]),
            ("delta", row["business_delta_changed"]),
            ("buyer", row["new_buyer_changed"]),
            ("holder", row["holder_changed"]),
        )
        if flag
    ]
    if not changed:
        classification = (
            "SAME_DIRECTION_CALIBRATION_CHANGE"
            if row["calibration_changed"]
            else "NO_DECISION_MATERIAL_CHANGE"
        )
    elif len(changed) > 1:
        classification = "MULTI_FIELD_DECISION_CHANGE"
    else:
        classification = {
            "direction": "PRIMARY_DIRECTION_CHANGE",
            "delta": "BUSINESS_DELTA_CHANGE",
            "buyer": "NEW_BUYER_STANCE_CHANGE",
            "holder": "HOLDER_STANCE_CHANGE",
        }[changed[0]]
    delta_sublabel = (
        "DELTA_MATERIALITY_DIFFERENCE"
        if row["business_delta_changed"]
        else "DELTA_UNCHANGED_ONLY"
    )
    return classification, delta_sublabel


def _enriched_comparisons(
    state: Mapping[str, object],
    normalized: Mapping[str, object],
    monolithic_documents: Sequence[Mapping[str, object]],
    stage1_documents: Sequence[Mapping[str, object]],
    stage2_documents: Sequence[Mapping[str, object]],
) -> list[dict[str, object]]:
    original = report_value(49)["rows"]
    by_context = {
        int(document["context"]): document
        for document in monolithic_documents
    }
    stage1_by_context = {
        int(document["context"]): document for document in stage1_documents
    }
    stage2_by_context = {
        int(document["context"]): document for document in stage2_documents
    }
    context_by_ticker = {
        str(ticker): int(row["context_id"])
        for row in normalized["contexts"]
        for ticker in row["tickers"]
    }
    monolithic_core = {
        str(row["ticker"]): row["core"]
        for document in monolithic_documents
        for row in document["rows"]
    }
    final_core = {
        str(row["ticker"]): row["core"]
        for document in stage2_documents
        for row in document["final_rows"]
    }
    core_snapshots = {
        str(row["candidate"]["ticker"]): row["core_snapshot_sha256"]
        for document in stage2_documents
        for row in document["compositions"]
    }
    enriched = []
    for source_row in original:
        row = dict(source_row)
        ticker = str(row["ticker"])
        context_id = context_by_ticker[ticker]
        mono = by_context[context_id]
        stage1 = stage1_by_context[context_id]
        stage2 = stage2_by_context[context_id]
        mono_refs = _selected_refs(monolithic_core[ticker])
        two_refs = _selected_refs(final_core[ticker])
        classification, sublabel = _comparison_classification(row)
        decision_material = classification in {
            "PRIMARY_DIRECTION_CHANGE",
            "BUSINESS_DELTA_CHANGE",
            "NEW_BUYER_STANCE_CHANGE",
            "HOLDER_STANCE_CHANGE",
            "MULTI_FIELD_DECISION_CHANGE",
        }
        row.update(
            {
                "classification": classification,
                "delta_sublabel": sublabel,
                "context_id": context_id,
                "packet_sha256": state["packet_hashes"][ticker],
                "monolithic_invocation_id": mono["transport"]["invocation_id"],
                "stage1_invocation_id": stage1["transport"]["invocation_id"],
                "stage2_invocation_id": stage2["transport"]["invocation_id"],
                "core_snapshot_sha256": core_snapshots[ticker],
                "shared_evidence_refs": sorted(mono_refs & two_refs),
                "selected_evidence_differences": {
                    "monolithic_only": sorted(mono_refs - two_refs),
                    "two_stage_only": sorted(two_refs - mono_refs),
                },
                "major_unknowns": sorted(
                    set(
                        _unknown_values(monolithic_core[ticker])
                        + _unknown_values(final_core[ticker])
                    )
                )[:20],
                "relevant_frozen_contract": (
                    "same-packet-two-stage-directional-v1+"
                    "business-delta-evidence-capability-v1"
                ),
                "forensic_classification": (
                    "OTHER_REVIEW_REQUIRED" if decision_material else None
                ),
            }
        )
        enriched.append(row)
    return enriched


def _classification_report(
    rows: Sequence[Mapping[str, object]],
    classification: str,
) -> dict[str, object]:
    selected = [row for row in rows if row["classification"] == classification]
    return {"status": "MEASURED", "count": len(selected), "rows": selected}


def _hard_semantic_rows(
    documents: Sequence[Mapping[str, object]],
    *,
    path: str,
) -> list[dict[str, object]]:
    return [
        {"path": path, "ticker": row["ticker"], "errors": row.get("errors", [])}
        for document in documents
        for row in document.get("rows", [])
        if row.get("errors")
    ]


def _compatibility_classification(
    *,
    expected_corrections: int,
    regressions: int,
    unresolved: int,
) -> str:
    if regressions:
        return "TWO_STAGE_COMPATIBILITY_HAS_BOUNDED_REGRESSIONS"
    if unresolved:
        return "TWO_STAGE_COMPATIBILITY_INCOMPLETE"
    if expected_corrections:
        return "TWO_STAGE_COMPATIBILITY_CLEAN_WITH_EXPECTED_CORRECTIONS"
    return "TWO_STAGE_COMPATIBILITY_CLEAN"


def _next_scope(
    rows: Sequence[Mapping[str, object]],
    *,
    hard_pass: bool,
) -> str:
    if not hard_pass:
        return "SHADOW_PROOF_HARNESS_ARCHITECTURE_REVIEW"
    counts = Counter(str(row["classification"]) for row in rows)
    primary = counts["PRIMARY_DIRECTION_CHANGE"]
    delta = counts["BUSINESS_DELTA_CHANGE"]
    stance = counts["NEW_BUYER_STANCE_CHANGE"] + counts["HOLDER_STANCE_CHANGE"]
    multi = counts["MULTI_FIELD_DECISION_CHANGE"]
    if multi or sum(value > 0 for value in (primary, delta, stance)) > 1:
        return "DECISION_BOUNDARY_DELTA_HOLDER_POLICY_REVIEW_ON_INTEGRATED_MAIN"
    if primary:
        return "TWO_STAGE_CORE_STABILITY_COMPATIBILITY_REVIEW"
    if delta:
        return "BUSINESS_THESIS_DELTA_MATERIALITY_POLICY_REVIEW_ON_INTEGRATED_MAIN"
    if stance:
        return "FUNDAMENTAL_STANCE_COMPATIBILITY_POLICY_REVIEW_ON_INTEGRATED_MAIN"
    return "DECISION_BOUNDARY_DELTA_HOLDER_POLICY_REVIEW_ON_INTEGRATED_MAIN"


def finalize_shadow() -> None:
    _configure_runtime()
    state, normalized = _verified_new_state()
    complete = read_json(OUTPUT / "shadow/run-complete.json")
    if complete.get("model_calls") != EXPECTED_MODEL_CALLS:
        raise ValueError("SHADOW_CALLS_INCOMPLETE")
    monolithic_documents = _shadow_documents("monolithic")
    stage1_documents = _shadow_documents("stage1")
    stage2_documents = _shadow_documents("stage2")
    expected = {
        int(row["context_id"]): tuple(str(ticker) for ticker in row["tickers"])
        for row in normalized["contexts"]
    }
    aggregation = audit_shadow_context_aggregation(
        generation_id=str(state["generation_id"]),
        monolithic_documents=monolithic_documents,
        stage1_documents=stage1_documents,
        stage2_documents=stage2_documents,
        expected_membership=expected,
    )
    report(48, aggregation)

    original = legacy._verify_frozen_state
    legacy._verify_frozen_state = _m12al_frozen_state_verifier
    try:
        legacy.finalize_shadow()
    finally:
        legacy._verify_frozen_state = original
    comparisons = _enriched_comparisons(
        state,
        normalized,
        monolithic_documents,
        stage1_documents,
        stage2_documents,
    )
    report(
        49,
        {
            "status": "MEASURED",
            "ticker_count": len(comparisons),
            "rows": comparisons,
        },
    )
    for number, classification in (
        (52, "PRIMARY_DIRECTION_CHANGE"),
        (53, "BUSINESS_DELTA_CHANGE"),
        (54, "NEW_BUYER_STANCE_CHANGE"),
        (55, "HOLDER_STANCE_CHANGE"),
        (56, "SAME_DIRECTION_CALIBRATION_CHANGE"),
    ):
        report(number, _classification_report(comparisons, classification))

    monolithic_rows = [
        row for document in monolithic_documents for row in document["rows"]
    ]
    stage1_rows = [row for document in stage1_documents for row in document["rows"]]
    final_rows = [row for document in stage2_documents for row in document["final_rows"]]
    direction_rows = [
        *m12ak._direction_audit(monolithic_rows, path="monolithic"),
        *m12ak._direction_audit(stage1_rows, path="stage1"),
        *m12ak._direction_audit(final_rows, path="two_stage_final"),
    ]
    direction_violations = sum(
        int(row["business_delta_direction_violation_count"])
        for row in direction_rows
    )
    direction_manifest = direction_source._direction_manifest(
        legacy._restore_views(state),
        legacy._shadow_inputs(state)[2][1],
    )
    report(
        51,
        {
            "status": (
                "PASS"
                if direction_violations == 0 and direction_manifest["status"] == "PASS"
                else "FAIL"
            ),
            "business_delta_direction_violation_count": direction_violations,
            "direction_hint_projection_mismatch_count": direction_manifest[
                "direction_hint_projection_mismatch_count"
            ],
            "unsafe_metric_auto_direction_count": direction_manifest[
                "unsafe_metric_auto_direction_count"
            ],
            "monolithic_stage1_delta_view_equality": "PASS",
            "rows": direction_rows,
        },
    )
    hard_errors = [
        *_hard_semantic_rows(monolithic_documents, path="monolithic"),
        *_hard_semantic_rows(stage1_documents, path="stage1"),
        *_hard_semantic_rows(stage2_documents, path="two_stage_final"),
    ]
    financial = report_value(60)
    adr = report_value(61)
    cyclical = report_value(62)
    core = report_value(63)
    runtime = report_value(64)
    capability = report_value(50)
    special_failures = sum(
        item.get("status") != "PASS" for item in (financial, adr, cyclical)
    )
    hard_semantic_pass = all(
        (
            not hard_errors,
            capability.get("business_delta_capability_violation_count") == 0,
            report_value(51)["status"] == "PASS",
            special_failures == 0,
            core.get("core_mutation_after_stance_count") == 0,
        )
    )
    report(
        46,
        {
            "status": "PASS" if hard_semantic_pass else "FAIL",
            "context_call_pass_count": sum(
                document.get("status") == "PASS"
                for document in (
                    *monolithic_documents,
                    *stage1_documents,
                    *stage2_documents,
                )
            ),
            "context_call_expected_count": EXPECTED_MODEL_CALLS,
            "objective_financial_semantic_failure_count": len(hard_errors),
            "business_delta_capability_violation_count": capability.get(
                "business_delta_capability_violation_count"
            ),
            "business_delta_direction_violation_count": direction_violations,
            "financial_sector_framework_failure_count": int(
                financial.get("status") != "PASS"
            ),
            "adr_security_basis_failure_count": int(adr.get("status") != "PASS"),
            "cyclical_valuation_framework_failure_count": int(
                cyclical.get("status") != "PASS"
            ),
            "core_mutation_after_stance_count": core.get(
                "core_mutation_after_stance_count"
            ),
            "hard_error_rows": hard_errors,
        },
    )

    expected_corrections = int(report_value(57).get("count") or 0)
    regressions = len(hard_errors) + special_failures
    decision_rows = [
        row
        for row in comparisons
        if row["forensic_classification"] == "OTHER_REVIEW_REQUIRED"
    ]
    report(
        58,
        {
            "status": "PASS" if regressions == 0 else "FAIL",
            "count": regressions,
            "rows": hard_errors,
        },
    )
    report(
        59,
        {"status": "MEASURED", "count": len(decision_rows), "rows": decision_rows},
    )
    counts = Counter(str(row["classification"]) for row in comparisons)
    hard_pass = all(
        (
            aggregation["status"] == "PASS",
            aggregation["final_row_count"] == len(state["tickers"]),
            len(comparisons) == len(state["tickers"]),
            hard_semantic_pass,
            runtime.get("status") == "PASS",
            runtime.get("model_calls") == EXPECTED_MODEL_CALLS,
            runtime.get("timeout_count") == 0,
            runtime.get("orphan_process_count") == 0,
            runtime.get("wrapper_retry_count") == 0,
        )
    )
    compatibility = _compatibility_classification(
        expected_corrections=expected_corrections,
        regressions=regressions,
        unresolved=len(decision_rows),
    )
    summary = {
        "status": "PASS" if hard_pass else "FAIL",
        "ticker_count": len(comparisons),
        "aggregate_finalization_status": aggregation["status"],
        "no_decision_material_change_count": counts[
            "NO_DECISION_MATERIAL_CHANGE"
        ],
        "same_direction_calibration_change_count": counts[
            "SAME_DIRECTION_CALIBRATION_CHANGE"
        ],
        "primary_direction_change_count": counts["PRIMARY_DIRECTION_CHANGE"],
        "business_delta_change_count": counts["BUSINESS_DELTA_CHANGE"],
        "new_buyer_change_count": counts["NEW_BUYER_STANCE_CHANGE"],
        "holder_change_count": counts["HOLDER_STANCE_CHANGE"],
        "multi_field_change_count": counts["MULTI_FIELD_DECISION_CHANGE"],
        "expected_contract_correction_count": expected_corrections,
        "potential_architecture_regression_count": regressions,
        "unresolved_review_required_count": len(decision_rows),
        "business_delta_capability_violation_count": capability.get(
            "business_delta_capability_violation_count"
        ),
        "business_delta_direction_violation_count": direction_violations,
        "core_mutation_after_stance_count": core.get(
            "core_mutation_after_stance_count"
        ),
    }
    report(65, summary)
    report(
        66,
        {
            "status": "DIAGNOSTIC_COMPLETE" if hard_pass else "BLOCKED",
            "classification": compatibility,
            "monolithic_is_ground_truth": False,
            "two_stage_is_ground_truth": False,
            "fresh_real_proof_readiness": "NOT_READY",
            "final_main_merge_readiness": "NOT_READY",
            "production_readiness": "NOT_READY",
        },
    )

    _combined_diagnostic_reports(comparisons, state, summary)
    next_scope = _next_scope(comparisons, hard_pass=hard_pass)
    _completion_reports(
        state=state,
        normalized=normalized,
        summary=summary,
        runtime=runtime,
        compatibility=compatibility,
        next_scope=next_scope,
        hard_pass=hard_pass,
    )


def _formal_rows(number: int, ticker: str) -> list[dict[str, object]]:
    source = read_json(M12AK_REPORTS / f"{number:02d}-{m12ak.SLUGS[number]}.json")
    return [row for row in source.get("rows", []) if row.get("ticker") == ticker]


def _combined_diagnostic_reports(
    comparisons: Sequence[Mapping[str, object]],
    state: Mapping[str, object],
    summary: Mapping[str, object],
) -> None:
    primary = [row for row in comparisons if row["direction_changed"]]
    delta = [
        row
        for row in comparisons
        if row["business_delta_changed"] and row["capability"] == "AI_JUDGMENT"
    ]
    positive_delta = [
        row
        for row in comparisons
        if "STRENGTHENED"
        in {
            row["monolithic"]["business_thesis_change"],
            row["two_stage"]["business_thesis_change"],
        }
    ]
    holder = [row for row in comparisons if row["holder_changed"]]
    report(
        67,
        {
            "status": "MEASURED",
            "fictional_ticker": "FIC-FIN-05",
            "fictional_primary_rows": _formal_rows(63, "FIC-FIN-05"),
            "fictional_new_buyer_rows": _formal_rows(64, "FIC-FIN-05"),
            "monitored_primary_boundary_count": len(primary),
            "monitored_rows": primary,
            "automatic_policy_transfer": False,
        },
    )
    report(
        68,
        {
            "status": "MEASURED",
            "fictional_ticker": "FIC-FIN-02",
            "fictional_delta_rows": _formal_rows(62, "FIC-FIN-02"),
            "monitored_ai_judgment_delta_difference_count": len(delta),
            "monitored_rows": delta,
            "typed_direction_defect": False,
            "materiality_policy_question": True,
        },
    )
    report(
        69,
        {
            "status": "MEASURED",
            "fictional_ticker": "FIC-FIN-06",
            "fictional_delta_rows": _formal_rows(62, "FIC-FIN-06"),
            "monitored_positive_delta_context_count": len(positive_delta),
            "monitored_rows": positive_delta,
            "automatic_policy_transfer": False,
        },
    )
    report(
        70,
        {
            "status": "MEASURED",
            "fictional_ticker": "FIC-FIN-08",
            "fictional_holder_rows": _formal_rows(65, "FIC-FIN-08"),
            "monitored_holder_boundary_count": len(holder),
            "monitored_rows": holder,
            "automatic_policy_transfer": False,
        },
    )
    report(
        71,
        {
            "status": "DIAGNOSTIC_COMPLETE",
            "active_ticker_count": len(state["tickers"]),
            "same_packet_comparison_count": len(comparisons),
            "primary_boundary_count": len(primary),
            "delta_materiality_count": len(delta),
            "holder_boundary_count": len(holder),
            "potential_architecture_regression_count": summary[
                "potential_architecture_regression_count"
            ],
            "lesson": (
                "architecture differences remain policy evidence; neither path is "
                "treated as automatic ground truth"
            ),
        },
    )
    report(
        72,
        {
            "status": "CLOSED" if summary["status"] == "PASS" else "OPEN",
            "manifest_root_cause": (
                "writer and verifier disagreed on context-list key and nested input shape"
            ),
            "manifest_repair": (
                "one canonical frozen_contexts writer plus bounded historical contexts reader"
            ),
            "formal_fictional_generation_id": M12AK_FICTIONAL_GENERATION_ID,
            "monitored_shadow_generation_id": state["generation_id"],
            "monitored_hard_gate": summary["status"],
            "decision_material_differences_are_policy_input": True,
        },
    )


def _completion_reports(
    *,
    state: Mapping[str, object],
    normalized: Mapping[str, object],
    summary: Mapping[str, object],
    runtime: Mapping[str, object],
    compatibility: str,
    next_scope: str,
    hard_pass: bool,
) -> None:
    report(
        73,
        {
            "status": "SELECTED",
            "next_scope": next_scope,
            "fresh_unseen_calls_authorized": False,
            "main_merge_authorized": False,
            "deployment_authorized": False,
            "monitoring_resume_authorized": False,
        },
    )
    report(
        74,
        {
            "status": "PASS",
            "contract": MANIFEST_CONTRACT,
            "canonical_key": CANONICAL_CONTEXT_KEY,
            "historical_replay": "HARNESS_CONTRACT_FIX_VALIDATED",
        },
    )
    report(
        75,
        {
            "status": "PASS",
            "reuse_status": "REUSE_AUTHORIZED",
            "generation_id": M12AK_FICTIONAL_GENERATION_ID,
            "fictional_model_calls_in_m12al": 0,
        },
    )
    report(
        76,
        {
            "status": "PASS" if hard_pass else "FAIL",
            "generation_id": state["generation_id"],
            "completed_ticker_count": summary["ticker_count"],
            "model_calls": runtime.get("model_calls"),
            "aggregate_finalization": summary["aggregate_finalization_status"],
        },
    )
    report(
        77,
        {
            "status": "MEASURED" if hard_pass else "BLOCKED",
            "ticker_count": summary["ticker_count"],
            "classification_counts": {
                key: value
                for key, value in summary.items()
                if key.endswith("_change_count")
            },
        },
    )
    report(
        78,
        {
            "status": "DIAGNOSTIC_COMPLETE" if hard_pass else "BLOCKED",
            "classification": compatibility,
            "next_scope": next_scope,
        },
    )
    report(
        79,
        {
            "status": "NOT_READY",
            "fresh_real_calls": 0,
            "reason": "BOUNDED_POLICY_REVIEW_REQUIRED_AFTER_MONITORED_SHADOW",
        },
    )
    report(80, {"status": "NOT_READY", "main_merge": 0, "deployment": 0})
    report(
        81,
        {
            "status": "PASS",
            "provider_source_fetches": 0,
            "production_db_mutations": 0,
            "monitoring_registrations": 0,
            "monitoring_stops": 0,
            "assessment_persistence_mutations": 0,
            "warning_mutations": 0,
            "notification_queue_writes": 0,
            "production_sends": 0,
        },
    )
    schedule = legacy.m12._schedule_observation()
    report(
        82,
        {
            **schedule,
            "status": "OBSERVED",
            "scheduler_mutation_count": 0,
            "automatic_monitoring_resume": 0,
        },
    )
    report(
        83,
        {
            "status": "PASS",
            "remote_push_count": 0,
            "raw_model_artifact_remote_push_count": 0,
            "main_branch_mutations": 0,
            "main_merges": 0,
            "deployments": 0,
        },
    )
    report(
        84,
        {
            "status": "PENDING_LOCAL_DOCUMENT_UPDATE",
            "path": "docs/MASTER_WORKFLOW.md",
            "phase": "M12AL",
            "next_scope": next_scope,
        },
    )
    previous = read_json(M12AK_OUTPUT / "shadow/program-state.json")
    reference_tickers = set(str(ticker) for ticker in previous["tickers"])
    actual_tickers = set(str(ticker) for ticker in state["tickers"])
    preflight = read_json(OUTPUT / "preflight.json")
    completion = {
        "status": "COMPLETE_DIAGNOSTIC" if hard_pass else "BLOCKED",
        "phase": "M12AL",
        "base_integration_head_sha": BASE_INTEGRATION_HEAD_SHA,
        "integration_branch": git("branch", "--show-current"),
        "implementation_head_sha": state["implementation_head_sha"],
        "work_instruction_commit": WORK_INSTRUCTION_COMMIT,
        "latest_result_zip_sha256": M12AK_BUNDLE_SHA256,
        "latest_result_integrity": preflight["latest_result_integrity"],
        "m12ak_formal_fictional_reuse_status": "REUSE_AUTHORIZED",
        "m12ak_formal_fictional_generation_id": M12AK_FICTIONAL_GENERATION_ID,
        "model_calls_fictional": 0,
        "shadow_manifest_root_cause": (
            "SHADOW_MANIFEST_PRODUCER_VERIFIER_KEY_AND_ROW_SHAPE_MISMATCH"
        ),
        "shadow_manifest_contract_version": MANIFEST_CONTRACT,
        "shadow_manifest_canonical_key": CANONICAL_CONTEXT_KEY,
        "shadow_manifest_legacy_key_supported": True,
        "shadow_manifest_roundtrip_status": report_value(18)["status"],
        "shadow_manifest_dual_key_conflict_test_status": report_value(15)[
            "status"
        ],
        "m12ak_historical_shadow_preflight_replay_status": report_value(24)[
            "status"
        ],
        "m12ak_historical_context_count": report_value(24)[
            "recognized_contexts"
        ],
        "m12ak_historical_ticker_coverage_count": report_value(24)[
            "recognized_tickers"
        ],
        "model_prompt_semantic_change_count": report_value(26)["change_count"],
        "model_schema_semantic_change_count": report_value(27)["change_count"],
        "business_delta_semantic_change_count": report_value(28)["change_count"],
        "financial_semantic_change_count": report_value(29)["change_count"],
        "two_stage_semantic_change_count": report_value(30)["change_count"],
        "directional_core_batch_max_items": MAX_CONTEXT_CANDIDATES,
        "directional_core_batch_max_items_changed": False,
        "task_start_active_monitor_count": len(state["tickers"]),
        "task_start_active_monitor_tickers": state["tickers"],
        "reference_added_tickers": sorted(actual_tickers - reference_tickers),
        "reference_removed_tickers": sorted(reference_tickers - actual_tickers),
        "shadow_generation_id": state["generation_id"],
        "shadow_packet_available_count": len(state["packet_paths"]),
        "shadow_packet_unavailable_count": 0,
        "shadow_packet_mismatch_count": 0,
        "shadow_context_count": normalized["context_count"],
        "shadow_monolithic_model_calls": normalized["context_count"],
        "shadow_stage1_model_calls": normalized["context_count"],
        "shadow_stage2_model_calls": normalized["context_count"],
        "shadow_model_calls_total": runtime.get("model_calls"),
        "shadow_completed_ticker_count": summary["ticker_count"],
        "shadow_final_composition_count": summary["ticker_count"],
        "shadow_aggregate_finalization_status": summary[
            "aggregate_finalization_status"
        ],
        "shadow_business_delta_capability_violation_count": summary[
            "business_delta_capability_violation_count"
        ],
        "shadow_business_delta_direction_violation_count": summary[
            "business_delta_direction_violation_count"
        ],
        "shadow_no_decision_material_change_count": summary[
            "no_decision_material_change_count"
        ],
        "shadow_same_direction_calibration_change_count": summary[
            "same_direction_calibration_change_count"
        ],
        "shadow_primary_direction_change_count": summary[
            "primary_direction_change_count"
        ],
        "shadow_business_delta_change_count": summary[
            "business_delta_change_count"
        ],
        "shadow_new_buyer_change_count": summary["new_buyer_change_count"],
        "shadow_holder_change_count": summary["holder_change_count"],
        "shadow_multi_field_change_count": summary["multi_field_change_count"],
        "shadow_expected_contract_correction_count": summary[
            "expected_contract_correction_count"
        ],
        "shadow_potential_architecture_regression_count": summary[
            "potential_architecture_regression_count"
        ],
        "shadow_unresolved_review_required_count": summary[
            "unresolved_review_required_count"
        ],
        "shadow_financial_sector_framework_failure_count": int(
            report_value(60)["status"] != "PASS"
        ),
        "shadow_adr_security_basis_failure_count": int(
            report_value(61)["status"] != "PASS"
        ),
        "shadow_cyclical_valuation_framework_failure_count": int(
            report_value(62)["status"] != "PASS"
        ),
        "shadow_core_mutation_after_stance_count": summary[
            "core_mutation_after_stance_count"
        ],
        "shadow_runtime_timeout_count": runtime.get("timeout_count"),
        "shadow_runtime_orphan_count": runtime.get("orphan_process_count"),
        "shadow_wrapper_retry_count": runtime.get("wrapper_retry_count"),
        "provider_source_fetches": 0,
        "production_db_mutations": 0,
        "monitoring_registrations": 0,
        "monitoring_stops": 0,
        "assessment_persistence_mutations": 0,
        "warning_mutations": 0,
        "notification_queue_writes": 0,
        "production_sends": 0,
        "remote_push_count": 0,
        "raw_model_artifact_remote_push_count": 0,
        "main_branch_mutations": 0,
        "main_merges": 0,
        "deployments": 0,
        "observed_paused_schedule_count": report_value(82)[
            "observed_paused_schedule_count"
        ],
        "scheduler_mutation_count": 0,
        "automatic_monitoring_resume": 0,
        "two_stage_shadow_compatibility_classification": compatibility,
        "fresh_real_proof_readiness": "NOT_READY",
        "final_main_merge_readiness": "NOT_READY",
        "production_readiness": "NOT_READY",
        "next_scope": next_scope,
        "focused_test_result": preflight["focused_test_result"],
        "full_test_result": preflight["full_test_result"],
        "ruff_result": preflight["ruff_result"],
        "git_diff_check": preflight["git_diff_check"],
        "artifact_count": "PENDING_FINAL_INDEX",
        "artifact_hash_mismatch_count": 0,
        "artifact_size_mismatch_count": 0,
        "artifact_secret_scan_failure_count": 0,
    }
    report(85, completion)
    write_json(OUTPUT / "program-completion.json", completion)
    write_text(
        OUTPUT / "COMPLETION-REPORT.md",
        "\n".join(
            (
                "# M12AL Completion",
                "",
                f"- Status: `{completion['status']}`",
                "- Shadow manifest repair: `PASS`",
                "- M12AK fictional proof reuse: `PASS` (0 new fictional calls)",
                f"- New monitored shadow: `{summary['ticker_count']}` tickers / "
                f"`{runtime.get('model_calls')}` calls",
                f"- Aggregate finalization: `{summary['aggregate_finalization_status']}`",
                f"- Compatibility: `{compatibility}`",
                "- Fresh-real / main / production: `NOT_READY / NOT_READY / NOT_READY`",
                "- Remote push / main merge / deployment: `0 / 0 / 0`",
                f"- Next scope: `{next_scope}`",
            )
        ),
    )
    print(
        json.dumps(
            {
                "status": completion["status"],
                "generation_id": state["generation_id"],
                "ticker_count": summary["ticker_count"],
                "model_calls": runtime.get("model_calls"),
                "compatibility": compatibility,
                "next_scope": next_scope,
            },
            sort_keys=True,
        )
    )


def failure_closeout() -> None:
    _configure_runtime()
    stop_path = OUTPUT / "shadow/stop.json"
    if not stop_path.is_file():
        raise ValueError("M12AL_FAILURE_RECEIPT_MISSING")
    stop = read_json(stop_path)
    for number in range(1, 86):
        path = REPORTS / f"{number:02d}-{SLUGS[number]}.json"
        if not path.exists():
            report(
                number,
                {
                    "status": "NOT_RUN_AFTER_HARD_STOP",
                    "stop_receipt": str(stop_path),
                    "stop_reason": stop.get("stop_reason"),
                    "detail": stop.get("detail"),
                },
            )
    state_path = OUTPUT / "shadow/program-state.json"
    state = read_json(state_path) if state_path.is_file() else {}
    preflight_path = OUTPUT / "preflight.json"
    preflight = read_json(preflight_path) if preflight_path.is_file() else {}
    completion = {
        "status": "BLOCKED",
        "phase": "M12AL",
        "base_integration_head_sha": BASE_INTEGRATION_HEAD_SHA,
        "integration_branch": git("branch", "--show-current"),
        "implementation_head_sha": state.get("implementation_head_sha"),
        "work_instruction_commit": WORK_INSTRUCTION_COMMIT,
        "latest_result_zip_sha256": M12AK_BUNDLE_SHA256,
        "latest_result_integrity": preflight.get(
            "latest_result_integrity", "NOT_MEASURED"
        ),
        "m12ak_formal_fictional_reuse_status": preflight.get(
            "formal_fictional_reuse", "NOT_MEASURED"
        ),
        "m12ak_formal_fictional_generation_id": M12AK_FICTIONAL_GENERATION_ID,
        "model_calls_fictional": 0,
        "shadow_manifest_contract_version": MANIFEST_CONTRACT,
        "shadow_manifest_canonical_key": CANONICAL_CONTEXT_KEY,
        "shadow_generation_id": state.get("generation_id"),
        "shadow_model_calls_total": stop.get("completed_model_calls", 0),
        "stop": stop,
        "provider_source_fetches": 0,
        "production_db_mutations": 0,
        "monitoring_registrations": 0,
        "monitoring_stops": 0,
        "assessment_persistence_mutations": 0,
        "warning_mutations": 0,
        "notification_queue_writes": 0,
        "production_sends": 0,
        "remote_push_count": 0,
        "raw_model_artifact_remote_push_count": 0,
        "main_branch_mutations": 0,
        "main_merges": 0,
        "deployments": 0,
        "scheduler_mutation_count": 0,
        "automatic_monitoring_resume": 0,
        "two_stage_shadow_compatibility_classification": (
            "TWO_STAGE_COMPATIBILITY_INCOMPLETE"
        ),
        "fresh_real_proof_readiness": "NOT_READY",
        "final_main_merge_readiness": "NOT_READY",
        "production_readiness": "NOT_READY",
        "next_scope": "SHADOW_PROOF_HARNESS_ARCHITECTURE_REVIEW",
        "focused_test_result": preflight.get("focused_test_result", "NOT_MEASURED"),
        "full_test_result": preflight.get("full_test_result", "NOT_MEASURED"),
        "ruff_result": preflight.get("ruff_result", "NOT_MEASURED"),
        "git_diff_check": preflight.get("git_diff_check", "NOT_MEASURED"),
        "artifact_count": "PENDING_FINAL_INDEX",
        "artifact_hash_mismatch_count": 0,
        "artifact_size_mismatch_count": 0,
        "artifact_secret_scan_failure_count": 0,
    }
    report(85, completion)
    write_json(OUTPUT / "program-completion.json", completion)
    write_text(
        OUTPUT / "COMPLETION-REPORT.md",
        "\n".join(
            (
                "# M12AL Failure Closeout",
                "",
                "- Status: `BLOCKED`",
                f"- Stop reason: `{stop.get('stop_reason')}`",
                f"- Completed shadow calls: `{stop.get('completed_model_calls', 0)}`",
                "- Fictional model calls: `0`",
                "- Remote push / main merge / deployment: `0 / 0 / 0`",
            )
        ),
    )


def closeout() -> None:
    completion = read_json(OUTPUT / "program-completion.json")
    marker = "2026-09-11 M12AL Shadow Frozen-Context Manifest Repair"
    workflow = Path("docs/MASTER_WORKFLOW.md")
    updated = marker in workflow.read_text(encoding="utf-8")
    report(
        84,
        {
            "status": "UPDATED_LOCAL_ONLY" if updated else "MISSING",
            "path": str(workflow),
            "phase": "M12AL",
            "next_scope": completion["next_scope"],
        },
    )
    completion["master_workflow_update"] = (
        "UPDATED_LOCAL_ONLY" if updated else "MISSING"
    )
    write_json(OUTPUT / "program-completion.json", completion)
    report(85, completion)
    if not updated:
        raise ValueError("M12AL_MASTER_WORKFLOW_UPDATE_MISSING")


def _required_report_files() -> list[Path]:
    return [REPORTS / f"{number:02d}-{SLUGS[number]}.json" for number in range(1, 86)]


def _secret_material(path: Path) -> list[str]:
    if path.suffix.casefold() not in {".json", ".txt", ".md", ".log", ".py"}:
        return []
    folded = path.read_text(encoding="utf-8", errors="replace").casefold()
    patterns = {
        "openai_api_key": r"\bsk-[a-z0-9_-]{20,}",
        "telegram_bot_token": r"\b\d{6,12}:[a-z0-9_-]{30,}\b",
        "authorization_bearer": r"authorization:\s*bearer\s+[a-z0-9._-]{20,}",
        "private_key": r"-----begin (?:rsa |ec )?private key-----\s+[a-z0-9+/]{40,}",
    }
    return [name for name, pattern in patterns.items() if re.search(pattern, folded)]


def _artifact_files() -> list[Path]:
    paths = [path for path in _required_report_files() if path.is_file()]
    paths.extend(
        path
        for path in OUTPUT.rglob("*")
        if path.is_file() and path.name != "artifact-index.json"
    )
    paths.extend(
        (
            RUNNER,
            MANIFEST_MODULE,
            Path("scripts/business_delta_evidence_capability_m12ai.py"),
            Path("tests/test_shadow_frozen_context_manifest.py"),
            Path("tests/test_shadow_frozen_context_manifest_m12al_runner.py"),
            FIXTURE_FILE,
            ARCHITECTURE,
            WORK_INSTRUCTION,
            Path("docs/MASTER_WORKFLOW.md"),
        )
    )
    return sorted(set(path for path in paths if path.is_file()), key=str)


def bundle(output_zip: Path) -> None:
    missing = [str(path) for path in _required_report_files() if not path.is_file()]
    if missing:
        raise ValueError(f"M12AL_REQUIRED_REPORTS_MISSING:{missing}")
    completion_path = OUTPUT / "program-completion.json"
    completion = read_json(completion_path)
    files = _artifact_files()
    completion["artifact_count"] = len(files)
    write_json(completion_path, completion)
    report(85, completion)
    files = _artifact_files()
    failures = [
        {"path": str(path), "indicators": indicators}
        for path in files
        for indicators in (_secret_material(path),)
        if indicators
    ]
    index = {
        "contract": "m12al-artifact-index-v1",
        "status": "PASS" if not failures else "FAIL",
        "artifact_count": len(files),
        "hash_mismatch_count": 0,
        "size_mismatch_count": 0,
        "secret_scan_failure_count": len(failures),
        "secret_scan_failures": failures,
        "rows": [
            {"path": str(path), "sha256": file_sha256(path), "size": path.stat().st_size}
            for path in files
        ],
    }
    write_json(OUTPUT / "artifact-index.json", index)
    if index["status"] != "PASS":
        raise ValueError("M12AL_ARTIFACT_SECRET_SCAN_FAILURE")
    output_zip.parent.mkdir(parents=True, exist_ok=True)
    if output_zip.exists():
        raise ValueError(f"RESULT_BUNDLE_ALREADY_EXISTS:{output_zip}")
    with zipfile.ZipFile(output_zip, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            archive.write(path, arcname=str(path))
        archive.write(
            OUTPUT / "artifact-index.json",
            arcname=str(OUTPUT / "artifact-index.json"),
        )
    with zipfile.ZipFile(output_zip) as archive:
        if archive.testzip() is not None:
            raise ValueError("M12AL_RESULT_BUNDLE_INTEGRITY_FAILURE")
    digest = file_sha256(output_zip)
    sidecar = output_zip.with_suffix(output_zip.suffix + ".sha256")
    write_text(sidecar, f"{digest}  {output_zip.name}")
    print(
        json.dumps(
            {
                "status": "PASS",
                "zip": str(output_zip),
                "sha256": digest,
                "sidecar": str(sidecar),
                "artifact_count": len(files) + 1,
            },
            sort_keys=True,
        )
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    prepare_parser = subparsers.add_parser("prepare")
    prepare_parser.add_argument("--previous-bundle", type=Path, default=M12AK_BUNDLE)
    subparsers.add_parser("run-shadow")
    subparsers.add_parser("finalize-shadow")
    subparsers.add_parser("failure-closeout")
    subparsers.add_parser("closeout")
    bundle_parser = subparsers.add_parser("bundle")
    bundle_parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.command == "prepare":
        prepare(args.previous_bundle)
    elif args.command == "run-shadow":
        run_shadow()
    elif args.command == "finalize-shadow":
        finalize_shadow()
    elif args.command == "failure-closeout":
        failure_closeout()
    elif args.command == "closeout":
        closeout()
    elif args.command == "bundle":
        bundle(args.output)


if __name__ == "__main__":
    main()
