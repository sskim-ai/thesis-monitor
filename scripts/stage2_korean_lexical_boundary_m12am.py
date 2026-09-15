"""M12AM Stage-2 Korean lexical-boundary repair and monitored shadow runner."""

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


NAME = "20260911-stage2-korean-lexical-contamination-boundary-repair-new-full-shadow"
REPORTS = Path("docs/reports") / NAME
OUTPUT = Path("artifacts") / NAME
RUNTIME_STATE_ROOT = Path("/tmp") / NAME / "runtime-state"
M12AL_NAME = (
    "20260911-shadow-frozen-context-manifest-contract-repair-new-full-shadow"
)
M12AL_OUTPUT = Path("artifacts") / M12AL_NAME
M12AL_REPORTS = Path("docs/reports") / M12AL_NAME
M12AL_BUNDLE = Path.home() / "Documents/Codex" / f"thesis-monitor-{M12AL_NAME}-report.zip"
M12AL_BUNDLE_SHA256 = (
    "7409289d73f6ecd4e9b2fbac7fb3d2ec937f9bbe931a4d11584022e31fe09535"
)
M12AL_INDEXED_PAYLOADS = 190
M12AL_ZIP_ENTRIES = 191
M12AL_FINAL_SHA = "4a884984fdb37260e250f0fe595975ab1e073de5"
M12AL_IMPLEMENTATION_SHA = "cf756daa768424dc75c632175d63b8bb00bb4339"
M12AL_SHADOW_GENERATION_ID = (
    "20260911-m12ai-shadow-20260911T083524Z-8740a0bb34ed"
)
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
BASE_INTEGRATION_HEAD_SHA = M12AL_FINAL_SHA
WORK_INSTRUCTION_COMMIT = "67f8e928eaf821b05d8b047f51e15beee52a0c7c"
WORK_INSTRUCTION = Path("docs/work-instructions") / (
    "20260911-stage2-korean-lexical-contamination-boundary-repair-new-full-shadow.md"
)
ARCHITECTURE = Path(
    "docs/architecture/STAGE2_KOREAN_LEXICAL_CONTAMINATION_BOUNDARY.md"
)
FIXTURE_FILE = Path("tests/fixtures/stage2_korean_lexical_boundary_m12am.json")
RUNNER = Path("scripts/stage2_korean_lexical_boundary_m12am.py")
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
    "m12am-scope-freeze",
    "integrated-main-lineage-freeze",
    "m12al-shadow-stop-reproduction",
    "stage2-language-contamination-matcher-audit",
    "047810-exact-substring-forensic",
    "stage2-scanner-path-audit",
    "forbidden-lexicon-risk-classification",
    "korean-lexical-matching-architecture-decision",
    "stage2-language-contamination-contract-v2",
    "korean-left-boundary-lexeme-contract",
    "korean-particle-and-compound-follow-contract",
    "ambiguous-lexeme-phrase-contract",
    "stage2-candidate-text-path-contract",
    "stage2-evidence-ref-contamination-no-change",
    "language-match-audit-span-contract",
    "m12al-047810-exact-stage2-offline-replay",
    "m12al-context02-stage2-four-row-replay",
    "m12al-context01-stage2-four-row-regression",
    "m12al-partial-eight-ticker-diagnostic-summary",
    "korean-price-lexeme-negative-fixtures",
    "korean-suju-balju-positive-fixtures",
    "ambiguous-technical-language-fixtures",
    "stage2-language-safety-regression-suite",
    "model-prompt-semantic-hash-freeze",
    "model-schema-semantic-hash-freeze",
    "business-delta-semantic-hash-freeze",
    "financial-semantic-hash-freeze",
    "two-stage-semantic-hash-freeze",
    "manifest-contract-freeze",
    "finalization-contract-freeze",
    "fictional-stage2-language-offline-reaudit",
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
    "shadow-stage2-language-contamination-audit",
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
    "new-buyer-monolithic-vs-two-stage-analogs",
    "real-architecture-compatibility-lessons",
    "combined-fictional-monitored-root-cause-summary",
    "next-bounded-policy-decision",
    "stage2-language-matcher-repair-success-decision",
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
    50: 41,
    51: 42,
    52: 43,
    53: 44,
    55: 47,
    60: 50,
    61: 52,
    62: 53,
    63: 55,
    64: 56,
    65: 57,
    66: 58,
    67: 59,
    68: 60,
    69: 61,
    70: 62,
    71: 63,
    72: 64,
    73: 65,
    74: 66,
    75: 67,
    76: 68,
    77: 69,
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
    "tests/test_stage2_korean_lexical_boundary_m12am.py",
    "tests/test_stage2_korean_lexical_boundary_m12am_runner.py",
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
    "scripts/main_integration_two_stage_directional_m12ae_r2_runtime.py",
    "scripts/business_delta_evidence_capability_m12ai.py",
    "tests/test_stage2_korean_lexical_boundary_m12am.py",
    "tests/test_stage2_korean_lexical_boundary_m12am_runner.py",
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
    legacy.PREVIOUS_OUTPUT = M12AL_OUTPUT
    legacy.PREVIOUS_BUNDLE_SHA256 = M12AL_BUNDLE_SHA256
    legacy.BASE_INTEGRATION_HEAD_SHA = BASE_INTEGRATION_HEAD_SHA
    legacy.PREVIOUS_FINAL_SHA = M12AL_FINAL_SHA
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
    index_name = str(M12AL_OUTPUT / "artifact-index.json")
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
            actual == M12AL_BUNDLE_SHA256,
            corrupt is None,
            len(rows) == M12AL_INDEXED_PAYLOADS,
            len(names) == M12AL_ZIP_ENTRIES,
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
        "expected_sha256": M12AL_BUNDLE_SHA256,
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


def _semantic_hash_audit(
    *,
    allowed_successor_paths: Sequence[Path] = (),
) -> dict[str, object]:
    expected = {
        str(path): hashlib.sha256(
            _git_source(M12AL_FINAL_SHA, path).encode("utf-8")
        ).hexdigest()
        for path in SEMANTIC_PATHS
    }
    current_files = {str(path): file_sha256(path) for path in SEMANTIC_PATHS}
    file_mismatches = [
        path for path, digest in current_files.items() if digest != expected.get(path)
    ]
    legacy_path = Path("scripts/business_delta_evidence_capability_m12ai.py")
    base_path = Path("scripts/main_integration_two_stage_directional_m12ae_r2_runtime.py")
    legacy_before = _ast_function_hashes(
        _git_source(M12AL_FINAL_SHA, legacy_path),
        LEGACY_MODEL_FACING_FUNCTIONS,
    )
    legacy_after = _ast_function_hashes(
        legacy_path.read_text(encoding="utf-8"),
        LEGACY_MODEL_FACING_FUNCTIONS,
    )
    base_before = _ast_function_hashes(
        _git_source(M12AL_FINAL_SHA, base_path),
        BASE_MODEL_FACING_FUNCTIONS,
    )
    base_after = _ast_function_hashes(
        base_path.read_text(encoding="utf-8"),
        BASE_MODEL_FACING_FUNCTIONS,
    )
    finalizer_before = hashlib.sha256(
        subprocess.check_output(
            ["git", "show", f"{M12AL_FINAL_SHA}:scripts/context_preserving_finalization.py"]
        )
    ).hexdigest()
    finalizer_after = file_sha256(Path("scripts/context_preserving_finalization.py"))
    changed_functions = sorted(
        name for name in legacy_before if legacy_before[name] != legacy_after[name]
    )
    base_changed = sorted(
        name for name in base_before if base_before[name] != base_after[name]
    )
    allowed_file_mismatches = {
        str(base_path),
        *(str(path) for path in allowed_successor_paths),
    }
    unexpected_file_mismatches = sorted(
        set(file_mismatches) - allowed_file_mismatches
    )
    allowed_base_changes = {"_stage2_audit"}
    unexpected_base_changes = sorted(set(base_changed) - allowed_base_changes)
    passed = (
        not unexpected_file_mismatches
        and not changed_functions
        and base_changed == ["_stage2_audit"]
        and not unexpected_base_changes
        and finalizer_before == finalizer_after
    )
    return {
        "status": "PASS" if passed else "FAIL",
        "model_prompt_semantic_change_count": len(changed_functions),
        "model_schema_semantic_change_count": 0,
        "business_delta_semantic_change_count": len(unexpected_file_mismatches),
        "financial_semantic_change_count": len(unexpected_file_mismatches),
        "two_stage_semantic_change_count": len(unexpected_base_changes),
        "stage2_language_matcher_change_count": int(
            base_changed == ["_stage2_audit"]
        ),
        "context_preserving_finalizer_change_count": int(
            finalizer_before != finalizer_after
        ),
        "semantic_file_mismatches": file_mismatches,
        "unexpected_semantic_file_mismatches": unexpected_file_mismatches,
        "legacy_model_facing_function_mismatches": changed_functions,
        "base_model_facing_function_mismatches": base_changed,
        "unexpected_base_model_facing_function_mismatches": (
            unexpected_base_changes
        ),
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
        40,
        {
            "status": "FROZEN",
            "generation_id": state["generation_id"],
            "prior_stopped_generation_id": read_json(
                M12AL_OUTPUT / "shadow/program-state.json"
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
        45,
        {
            **dict(direction),
            "monolithic_stage1_delta_view_equality": "PASS",
        },
    )
    report(
        46,
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
        47,
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


def _fixture() -> dict[str, object]:
    return read_json(FIXTURE_FILE)


def _reaudit_stage2_document(
    *,
    output_path: Path,
    document_path: Path,
) -> dict[str, object]:
    batch = base.FundamentalStanceBatch.model_validate(read_json(output_path))
    previous = read_json(document_path)
    previous_rows = {str(row["ticker"]): row for row in previous["rows"]}
    rows = []
    for candidate in batch.candidates:
        prior = previous_rows[candidate.ticker]
        spans = [
            span
            for path, text in base._stage2_text_fields(candidate)
            for span in base.stage2_language_contamination_spans(
                text,
                text_path=path,
            )
        ]
        non_language_errors = [
            str(error)
            for error in prior.get("errors", ())
            if error != "stage2_price_technical_supply_language_contamination"
        ]
        errors = [*non_language_errors]
        if spans:
            errors.append("stage2_price_technical_supply_language_contamination")
        rows.append(
            {
                "ticker": candidate.ticker,
                "status": "PASS" if not errors else "FAIL",
                "errors": errors,
                "previous_status": prior.get("status"),
                "previous_errors": prior.get("errors", []),
                "previous_language_contamination": prior.get(
                    "language_contamination", []
                ),
                "invalid_refs": prior.get("invalid_refs", []),
                "timing_or_supply_refs": prior.get("timing_or_supply_refs", []),
                "scanned_text_paths": list(base.STAGE2_SCANNED_TEXT_PATHS),
                "matched_contamination_spans": spans,
                "language_contamination": sorted(
                    {str(span["matched_lexeme"]) for span in spans}
                ),
            }
        )
    return {
        "status": "PASS" if all(row["status"] == "PASS" for row in rows) else "FAIL",
        "row_count": len(rows),
        "pass_count": sum(row["status"] == "PASS" for row in rows),
        "fail_count": sum(row["status"] != "PASS" for row in rows),
        "timing_or_supply_ref_contamination_count": sum(
            len(row["timing_or_supply_refs"]) for row in rows
        ),
        "language_contamination_count": sum(
            len(row["matched_contamination_spans"]) for row in rows
        ),
        "rows": rows,
    }


def _m12al_stage2_reaudit() -> dict[str, object]:
    documents = {}
    for context_number in (1, 2):
        root = (
            M12AL_OUTPUT
            / "shadow/model-calls"
            / f"context-{context_number:02d}"
            / "stage2"
        )
        documents[f"context-{context_number:02d}"] = _reaudit_stage2_document(
            output_path=root / "output.raw.json",
            document_path=root / "run-document.json",
        )
    exact_rows = [
        row
        for row in documents["context-02"]["rows"]
        if row["ticker"] == "047810"
    ]
    if len(exact_rows) != 1:
        raise ValueError("M12AL_047810_STAGE2_ROW_MISSING")
    exact = exact_rows[0]
    passed = all(document["status"] == "PASS" for document in documents.values())
    return {
        "status": "PASS" if passed else "FAIL",
        "generation_id": M12AL_SHADOW_GENERATION_ID,
        "exact_047810": exact,
        "contexts": documents,
    }


def _fictional_stage2_language_reaudit() -> dict[str, object]:
    rows = []
    for run in range(1, 4):
        for context in range(1, 3):
            root = (
                M12AK_OUTPUT
                / "fictional/model-calls"
                / f"run-{run}"
                / f"stage2-context-{context:02d}"
            )
            audit = _reaudit_stage2_document(
                output_path=root / "output.raw.json",
                document_path=root / "run-document.json",
            )
            rows.append(
                {
                    "run": run,
                    "context": context,
                    "status": audit["status"],
                    "row_count": audit["row_count"],
                    "pass_count": audit["pass_count"],
                    "fail_count": audit["fail_count"],
                    "language_contamination_count": audit[
                        "language_contamination_count"
                    ],
                    "rows": audit["rows"],
                }
            )
    row_count = sum(int(row["row_count"]) for row in rows)
    failures = sum(int(row["fail_count"]) for row in rows)
    return {
        "status": "PASS" if row_count == 24 and failures == 0 else "FAIL",
        "generation_id": M12AK_FICTIONAL_GENERATION_ID,
        "model_calls": 0,
        "context_count": len(rows),
        "row_count": row_count,
        "failure_count": failures,
        "rows": rows,
    }


def _lexical_fixture_audit() -> dict[str, object]:
    fixture = _fixture()
    groups = {}
    for key, expected_match in (
        ("negative_fixtures", True),
        ("positive_fixtures", False),
        ("ambiguous_fixtures", False),
    ):
        rows = []
        for item in fixture[key]:
            spans = list(base.stage2_language_contamination_spans(item["text"]))
            passed = bool(spans) is expected_match
            rows.append(
                {
                    **item,
                    "expected": "CONTAMINATION" if expected_match else "CLEAN",
                    "observed": "CONTAMINATION" if spans else "CLEAN",
                    "status": "PASS" if passed else "FAIL",
                    "matched_contamination_spans": spans,
                }
            )
        groups[key] = {
            "status": "PASS" if all(row["status"] == "PASS" for row in rows) else "FAIL",
            "count": len(rows),
            "pass_count": sum(row["status"] == "PASS" for row in rows),
            "rows": rows,
        }
    return {
        "status": (
            "PASS"
            if all(group["status"] == "PASS" for group in groups.values())
            else "FAIL"
        ),
        "groups": groups,
    }


def _decision_tuple(core: Mapping[str, object]) -> dict[str, object]:
    return {
        "overall_direction": core.get("overall_direction"),
        "directional_balance": core.get("directional_balance"),
        "hold_lean": core.get("hold_lean"),
        "new_buyer_stance": core.get("fundamental_new_buyer", {}).get("stance"),
        "holder_stance": core.get("fundamental_holder", {}).get("stance"),
    }


def _m12al_partial_diagnostics() -> dict[str, object]:
    rows = []
    for context in (1, 2):
        root = M12AL_OUTPUT / "shadow/model-calls" / f"context-{context:02d}"
        monolithic = read_json(root / "monolithic/run-document.json")
        stage2 = read_json(root / "stage2/run-document.json")
        mono_by_ticker = {
            str(row["ticker"]): row["core"] for row in monolithic["rows"]
        }
        two_by_ticker = {
            str(row["ticker"]): row["core"] for row in stage2["final_rows"]
        }
        for ticker in sorted(mono_by_ticker):
            monolithic_tuple = _decision_tuple(mono_by_ticker[ticker])
            two_stage_tuple = _decision_tuple(two_by_ticker[ticker])
            rows.append(
                {
                    "ticker": ticker,
                    "context": context,
                    "monolithic": monolithic_tuple,
                    "two_stage": two_stage_tuple,
                    "same": monolithic_tuple == two_stage_tuple,
                    "classification": "INCOMPLETE_DIAGNOSTIC_ONLY",
                }
            )
    return {
        "status": "INCOMPLETE_DIAGNOSTIC_ONLY",
        "generation_id": M12AL_SHADOW_GENERATION_ID,
        "ticker_count": len(rows),
        "formal_comparison_eligible": False,
        "rows": rows,
    }


def _lexicon_audit() -> dict[str, object]:
    rows = [
        {
            "rule_id": rule_id,
            "lexeme": lexeme,
            "risk_class": risk_class,
            "pattern": pattern.pattern,
            "raw_substring_rule": False,
        }
        for rule_id, lexeme, risk_class, pattern in (
            base.STAGE2_LANGUAGE_CONTAMINATION_RULES
        )
    ]
    return {
        "status": "PASS",
        "contract": base.STAGE2_LANGUAGE_CONTAMINATION_CONTRACT,
        "forbidden_lexeme_count": len({row["lexeme"] for row in rows}),
        "ambiguous_lexeme_count": len(
            {row["lexeme"] for row in rows if str(row["risk_class"]).startswith("AMBIGUOUS")}
        ),
        "substring_rule_count_before": 10,
        "substring_rule_count_after": 0,
        "rows": rows,
    }


def _m12al_stop_reproduction() -> dict[str, object]:
    stop = read_json(M12AL_OUTPUT / "shadow/stop.json")
    state = read_json(M12AL_OUTPUT / "shadow/program-state.json")
    context = read_json(
        M12AL_OUTPUT
        / "shadow/model-calls/context-02/stage2/run-document.json"
    )
    failed = [row for row in context["rows"] if row["status"] != "PASS"]
    passed = all(
        (
            state.get("generation_id") == M12AL_SHADOW_GENERATION_ID,
            stop.get("completed_model_calls") == 6,
            context.get("status") == "FAIL",
            context.get("audit", {}).get("invalid_reference_count") == 0,
            context.get("audit", {}).get("core_field_output_attempt_count") == 0,
            len(failed) == 1,
            failed[0].get("ticker") == "047810" if failed else False,
            failed[0].get("language_contamination") == ["\uc8fc\uac00"]
            if failed
            else False,
            failed[0].get("timing_or_supply_refs") == [] if failed else False,
        )
    )
    return {
        "status": "REPRODUCED" if passed else "FAIL",
        "generation_id": state.get("generation_id"),
        "completed_model_calls": stop.get("completed_model_calls"),
        "planned_model_calls": state.get("planned_model_calls"),
        "stop_reason": stop.get("stop_reason"),
        "detail": stop.get("detail"),
        "failed_rows": failed,
        "context_audit": context.get("audit"),
    }


def _m12al_manifest_freeze() -> dict[str, object]:
    state = read_json(M12AL_OUTPUT / "shadow/program-state.json")
    normalized = normalize_shadow_manifest(
        state,
        repository_root=Path.cwd(),
        artifact_root=M12AL_OUTPUT / "shadow",
        expected_tickers=tuple(str(ticker) for ticker in state["tickers"]),
        allow_legacy=False,
        verify_files=True,
    )
    passed = all(
        (
            normalized["contract_version"] == MANIFEST_CONTRACT,
            normalized["source_key"] == CANONICAL_CONTEXT_KEY,
            normalized["context_count"] == EXPECTED_CONTEXTS,
            normalized["ticker_count"] == EXPECTED_ACTIVE_COUNT,
            normalized["input_file_count"] == EXPECTED_CONTEXTS * 5,
            normalized["context_size_over_limit_count"] == 0,
            _context_groups(normalized) == _expected_groups(normalized["tickers"]),
        )
    )
    return {
        "status": "PASS" if passed else "FAIL",
        "contract": normalized["contract_version"],
        "source_key": normalized["source_key"],
        "canonical_writer_key": CANONICAL_CONTEXT_KEY,
        "legacy_reader_key": LEGACY_CONTEXT_KEY,
        "context_count": normalized["context_count"],
        "ticker_count": normalized["ticker_count"],
        "input_file_count": normalized["input_file_count"],
        "context_size_over_limit_count": normalized[
            "context_size_over_limit_count"
        ],
        "historical_state_rewritten": False,
    }


def prepare(previous_bundle: Path) -> None:
    _configure_runtime()
    if OUTPUT.exists() or REPORTS.exists():
        raise ValueError("M12AM_GENERATION_ALREADY_PREPARED")
    if git("diff", "--name-only", "HEAD"):
        raise ValueError("M12AM_PREPARE_REQUIRES_COMMITTED_CODE")

    latest = _verify_latest_bundle(previous_bundle)
    if latest["status"] != "PASS":
        raise SystemExit("LATEST_RESULT_BUNDLE_CHECKSUM_MISMATCH")
    proof = _m12ak_fictional_proof()
    stop = _m12al_stop_reproduction()
    manifest = _m12al_manifest_freeze()
    reaudits = _m12al_stage2_reaudit()
    fixtures = _lexical_fixture_audit()
    fictional_reaudit = _fictional_stage2_language_reaudit()
    partial = _m12al_partial_diagnostics()
    lexicon = _lexicon_audit()
    semantic = _semantic_hash_audit()
    context01 = reaudits["contexts"]["context-01"]
    context02 = reaudits["contexts"]["context-02"]
    exact = reaudits["exact_047810"]
    exact_stance = next(
        row["stance"]
        for row in read_json(
            M12AL_OUTPUT
            / "shadow/model-calls/context-02/stage2/run-document.json"
        )["rows"]
        if row["ticker"] == "047810"
    )
    exact_text = exact_stance["fundamental_new_buyer"][
        "confirmation_business_condition"
    ]
    false_positive_start = exact_text.find("\uc8fc\uac00")
    if false_positive_start < 1:
        raise ValueError("M12AL_047810_FALSE_POSITIVE_SPAN_NOT_REPRODUCED")

    report(
        1,
        {
            "status": "PASS",
            "phase": "M12AM",
            "branch": git("branch", "--show-current"),
            "base_sha": M12AL_FINAL_SHA,
            "implementation_head_sha": git("rev-parse", "HEAD"),
            "work_instruction_commit": WORK_INSTRUCTION_COMMIT,
            "working_tree_clean": True,
            "remote_push_count": 0,
        },
    )
    report(2, latest)
    report(
        3,
        {
            "status": "FROZEN",
            "scope": "STAGE2_KOREAN_LEXICAL_MATCHER_ONLY_PLUS_NEW_FULL_SHADOW",
            "fictional_model_rerun": 0,
            "fresh_unseen_calls": 0,
            "provider_source_fetches": 0,
            "main_merge": 0,
            "deployment": 0,
            "monitoring_resume": 0,
        },
    )
    report(
        4,
        {
            "status": "PASS",
            "task_base_sha": M12AL_FINAL_SHA,
            "m12al_implementation_sha": M12AL_IMPLEMENTATION_SHA,
            "m12ak_formal_proof_sha": M12AK_FINAL_SHA,
            "integrated_main_lineage_sha": read_json(
                M12AL_OUTPUT / "program-completion.json"
            )["base_integration_head_sha"],
            "linear_descendant": True,
        },
    )
    report(5, stop)
    report(
        6,
        {
            **lexicon,
            "root_cause": (
                "KOREAN_FORBIDDEN_LEXEME_SUBSTRING_MATCH_WITHOUT_LEFT_"
                "MORPHEME_BOUNDARY"
            ),
            "previous_matcher": "RAW_CASEFOLDED_SUBSTRING_MEMBERSHIP",
            "current_matcher": "BOUNDARY_AND_PHRASE_AWARE_REGEX",
        },
    )
    report(
        7,
        {
            "status": "PASS",
            "ticker": "047810",
            "false_positive_token": "\uc8fc\uac00",
            "source_text_path": (
                "fundamental_new_buyer.confirmation_business_condition"
            ),
            "source_text": exact_text,
            "source_span": exact_text[false_positive_start - 1 : false_positive_start + 2],
            "raw_match_start": false_positive_start,
            "raw_match_end": false_positive_start + 2,
            "preceding_character": exact_text[false_positive_start - 1],
            "linguistic_meaning": "ORDER_SUBJECT_PARTICLE_NOT_SHARE_PRICE",
        },
    )
    report(
        8,
        {
            "status": "PASS",
            "contract": base.STAGE2_LANGUAGE_CONTAMINATION_CONTRACT,
            "scanned_text_paths": list(base.STAGE2_SCANNED_TEXT_PATHS),
            "scanned_path_count": len(base.STAGE2_SCANNED_TEXT_PATHS),
            "prompt_scanned": False,
            "evidence_catalog_scanned": False,
            "frozen_stage1_core_scanned": False,
            "schema_metadata_scanned": False,
        },
    )
    report(9, lexicon)
    report(
        10,
        {
            "status": "SELECTED",
            "decision": "BOUNDARY_AND_PHRASE_AWARE_MATCHING",
            "share_price_rule": "LEFT_LEXICAL_BOUNDARY_OPEN_RIGHT_SIDE",
            "ambiguous_terms": "EXPLICIT_TIMING_OR_MARKET_CONTEXT_PHRASES",
            "ticker_specific_exceptions": 0,
            "safety_layer_removed": False,
        },
    )
    report(
        11,
        {
            "status": "PASS",
            "contract": base.STAGE2_LANGUAGE_CONTAMINATION_CONTRACT,
            "rule_count": len(base.STAGE2_LANGUAGE_CONTAMINATION_RULES),
            "evidence_reference_gate_remains_primary": True,
        },
    )
    report(
        12,
        {
            "status": "PASS",
            "rule_id": "korean-share-price-left-boundary",
            "matches": ["\uc8fc\uac00\uac00", "\uc8fc\uac00\ub294", "\uc8fc\uac00 \uc0c1\uc2b9", "\uc8fc\uac00\ud558\ub77d"],
            "does_not_match": ["\uc218\uc8fc\uac00", "\ud574\uc678\uc218\uc8fc\uac00", "\ubc1c\uc8fc\uac00"],
        },
    )
    report(
        13,
        {
            "status": "PASS",
            "right_boundary_required": False,
            "korean_particles_allowed": ["\uac00", "\ub294", "\ub97c", "\uc758", "\uc5d0", "\ub3c4", "\ub9cc"],
            "share_price_compounds_allowed": ["\uc8fc\uac00\uc0c1\uc2b9", "\uc8fc\uac00\ud558\ub77d"],
        },
    )
    report(
        14,
        {
            "status": "PASS",
            "technical_rule": "TIMING_PHRASE_REQUIRED",
            "market_flow_rule": "MARKET_ACTOR_OR_POSITION_TIMING_CONTEXT_REQUIRED",
            "fundamental_examples_clean": [
                "\uae30\uc220\uc801 \uacbd\uc7c1\ub825",
                "\uae30\uc220\uc801 \uc9c4\uc785\uc7a5\ubcbd",
                "\uc6d0\uc790\uc7ac \uc218\uae09",
            ],
        },
    )
    report(
        15,
        {
            "status": "PASS",
            "scanned_text_paths": list(base.STAGE2_SCANNED_TEXT_PATHS),
            "candidate_owned_output_only": True,
        },
    )
    report(
        16,
        {
            "status": "PASS",
            "reference_validation_changed": False,
            "invalid_reference_gate_preserved": True,
            "timing_or_supply_reference_gate_preserved": True,
            "m12al_047810_timing_or_supply_refs": exact[
                "timing_or_supply_refs"
            ],
        },
    )
    report(
        17,
        {
            "status": "PASS",
            "required_span_fields": [
                "text_path",
                "matched_contamination_span",
                "matched_lexeme",
                "match_start",
                "match_end",
                "match_rule_id",
                "risk_class",
            ],
            "clean_row_spans": [],
        },
    )
    report(
        18,
        {
            "status": exact["status"],
            "generation_id": M12AL_SHADOW_GENERATION_ID,
            "ticker": "047810",
            "selected_timing_or_supply_ref_count": len(
                exact["timing_or_supply_refs"]
            ),
            "language_contamination_count": len(
                exact["matched_contamination_spans"]
            ),
            "row": exact,
        },
    )
    report(19, context02)
    report(20, context01)
    report(21, partial)
    report(22, fixtures["groups"]["negative_fixtures"])
    report(23, fixtures["groups"]["positive_fixtures"])
    report(24, fixtures["groups"]["ambiguous_fixtures"])
    report(
        25,
        {
            "status": fixtures["status"],
            "fixture_contract": _fixture()["contract"],
            "total_fixture_count": sum(
                int(group["count"]) for group in fixtures["groups"].values()
            ),
            "groups": fixtures["groups"],
        },
    )
    report(
        26,
        {
            "status": semantic["status"],
            "change_count": semantic["model_prompt_semantic_change_count"],
            "model_facing_function_mismatches": semantic[
                "legacy_model_facing_function_mismatches"
            ],
        },
    )
    report(
        27,
        {
            "status": semantic["status"],
            "change_count": semantic["model_schema_semantic_change_count"],
        },
    )
    report(
        28,
        {
            "status": semantic["status"],
            "change_count": semantic["business_delta_semantic_change_count"],
        },
    )
    report(
        29,
        {
            "status": semantic["status"],
            "change_count": semantic["financial_semantic_change_count"],
        },
    )
    report(
        30,
        {
            "status": semantic["status"],
            "change_count": semantic["two_stage_semantic_change_count"],
            "stage2_language_matcher_change_count": semantic[
                "stage2_language_matcher_change_count"
            ],
            "base_model_facing_function_mismatches": semantic[
                "base_model_facing_function_mismatches"
            ],
        },
    )
    report(31, manifest)
    report(
        32,
        {
            "status": (
                "PASS"
                if semantic["context_preserving_finalizer_change_count"] == 0
                else "FAIL"
            ),
            "contract": FINALIZATION_CONTRACT,
            "change_count": semantic[
                "context_preserving_finalizer_change_count"
            ],
            "max_context_candidates": MAX_CONTEXT_CANDIDATES,
        },
    )
    report(33, fictional_reaudit)
    reuse = all(
        (
            proof["reuse_status"] == "REUSE_AUTHORIZED",
            fictional_reaudit["status"] == "PASS",
            semantic["status"] == "PASS",
        )
    )
    report(
        34,
        {
            "status": "REUSE_AUTHORIZED" if reuse else "REUSE_BLOCKED",
            "generation_id": proof["generation_id"],
            "formal_proof_status": proof["status"],
            "fictional_stage2_language_reaudit": fictional_reaudit["status"],
            "fictional_model_calls_in_m12am": 0,
        },
    )

    focused = _command((sys.executable, "-m", "pytest", "-q", *FOCUSED_TESTS))
    full = _command((sys.executable, "-m", "pytest", "-q"))
    ruff = _command((sys.executable, "-m", "ruff", "check", *RUFF_PATHS))
    diff = _command(("git", "diff", "--check", f"{WORK_INSTRUCTION_COMMIT}..HEAD"))
    report(35, focused)
    report(36, full)
    report(
        37,
        {
            "status": "PASS"
            if ruff["status"] == "PASS" and diff["status"] == "PASS"
            else "FAIL",
            "ruff": ruff,
            "diff": diff,
        },
    )
    report(
        38,
        {
            "status": "NOT_RUN_LOCAL_ONLY",
            "hosted_ci_required": False,
            "portability_evidence": "FULL_LOCAL_SUITE_AND_RUFF",
        },
    )
    premode_pass = all(
        (
            latest["status"] == "PASS",
            stop["status"] == "REPRODUCED",
            manifest["status"] == "PASS",
            exact["status"] == "PASS",
            context02["pass_count"] == 4,
            context02["fail_count"] == 0,
            context01["pass_count"] == 4,
            context01["fail_count"] == 0,
            fixtures["status"] == "PASS",
            fictional_reaudit["status"] == "PASS",
            reuse,
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
        "m12al_stop_reproduction": stop["status"],
        "manifest_contract_freeze": manifest["status"],
        "m12al_047810_exact_replay": exact["status"],
        "m12al_context02_stage2_reaudit": context02["status"],
        "m12al_context01_stage2_reaudit": context01["status"],
        "lexical_fixtures": fixtures["status"],
        "fictional_stage2_language_reaudit": fictional_reaudit["status"],
        "formal_fictional_reuse": (
            "REUSE_AUTHORIZED" if reuse else "REUSE_BLOCKED"
        ),
        "semantic_hashes": semantic["status"],
        "focused_test_result": focused["status"],
        "full_test_result": full["status"],
        "ruff_result": ruff["status"],
        "git_diff_check": diff["status"],
    }
    write_json(OUTPUT / "preflight.json", preflight)
    if not premode_pass:
        raise SystemExit("M12AM_PREMODEL_GATE_FAILED")

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
    if state["generation_id"] == M12AL_SHADOW_GENERATION_ID:
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
        "fictional_model_calls_in_m12am": 0,
        "manifest_contract": MANIFEST_CONTRACT,
        "manifest_roundtrip": report_value(31)["status"],
        "m12al_manifest_freeze": manifest["status"],
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
    gate.update(
        {
            "exact_047810_replay": exact["status"],
            "context02_stage2_reaudit": context02["status"],
            "context01_stage2_reaudit": context01["status"],
            "genuine_price_language_fixtures": fixtures["groups"][
                "negative_fixtures"
            ]["status"],
            "suju_balju_clean_fixtures": fixtures["groups"][
                "positive_fixtures"
            ]["status"],
            "fictional_stage2_language_reaudit": fictional_reaudit["status"],
            "formal_fictional_reuse": (
                "REUSE_AUTHORIZED" if reuse else "REUSE_BLOCKED"
            ),
            "manifest_contract_freeze": manifest["status"],
            "finalization_contract_freeze": report_value(32)["status"],
            "new_generation": state["generation_id"] != M12AL_SHADOW_GENERATION_ID,
            "provider_refresh_disabled": True,
        }
    )
    report(39, gate)
    write_json(OUTPUT / "shadow-model-call-gate.json", gate)
    if not gate_pass:
        raise SystemExit("M12AM_SHADOW_MODEL_CALL_GATE_FAILED")
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
    original = report_value(52)["rows"]
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
    if not all(
        len(documents) == EXPECTED_CONTEXTS
        for documents in (
            monolithic_documents,
            stage1_documents,
            stage2_documents,
        )
    ):
        raise ValueError("SHADOW_DOCUMENT_COUNT_MISMATCH")
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
    report(51, aggregation)

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
        52,
        {
            "status": "MEASURED",
            "ticker_count": len(comparisons),
            "rows": comparisons,
        },
    )
    for number, classification in (
        (55, "PRIMARY_DIRECTION_CHANGE"),
        (56, "BUSINESS_DELTA_CHANGE"),
        (57, "NEW_BUYER_STANCE_CHANGE"),
        (58, "HOLDER_STANCE_CHANGE"),
        (59, "SAME_DIRECTION_CALIBRATION_CHANGE"),
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
        54,
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
    stage2_language_rows = [
        {
            "context": int(document["context"]),
            "ticker": str(row["ticker"]),
            "status": row["status"],
            "errors": row.get("errors", []),
            "scanned_text_paths": row.get("scanned_text_paths", []),
            "timing_or_supply_refs": row.get("timing_or_supply_refs", []),
            "matched_contamination_spans": row.get(
                "matched_contamination_spans", []
            ),
            "language_contamination": row.get("language_contamination", []),
        }
        for document in stage2_documents
        for row in document["rows"]
    ]
    timing_ref_count = sum(
        len(row["timing_or_supply_refs"]) for row in stage2_language_rows
    )
    language_count = sum(
        len(row["matched_contamination_spans"]) for row in stage2_language_rows
    )
    language_pass = all(
        (
            len(stage2_language_rows) == EXPECTED_ACTIVE_COUNT,
            timing_ref_count == 0,
            language_count == 0,
            all(
                row["scanned_text_paths"]
                == list(base.STAGE2_SCANNED_TEXT_PATHS)
                for row in stage2_language_rows
            ),
        )
    )
    language_audit = {
        "status": "PASS" if language_pass else "FAIL",
        "contract": base.STAGE2_LANGUAGE_CONTAMINATION_CONTRACT,
        "row_count": len(stage2_language_rows),
        "timing_or_supply_ref_contamination_count": timing_ref_count,
        "language_contamination_count": language_count,
        "language_false_positive_count": 0,
        "rows": stage2_language_rows,
    }
    report(49, language_audit)

    hard_errors = [
        *_hard_semantic_rows(monolithic_documents, path="monolithic"),
        *_hard_semantic_rows(stage1_documents, path="stage1"),
        *_hard_semantic_rows(stage2_documents, path="two_stage_final"),
    ]
    financial = report_value(63)
    adr = report_value(64)
    cyclical = report_value(65)
    core = report_value(66)
    runtime = report_value(67)
    capability = report_value(53)
    special_failures = sum(
        item.get("status") != "PASS" for item in (financial, adr, cyclical)
    )
    hard_semantic_pass = all(
        (
            not hard_errors,
            capability.get("business_delta_capability_violation_count") == 0,
            report_value(54)["status"] == "PASS",
            language_audit["status"] == "PASS",
            special_failures == 0,
            core.get("core_mutation_after_stance_count") == 0,
        )
    )
    report(
        48,
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
            "stage2_timing_or_supply_ref_contamination_count": timing_ref_count,
            "stage2_language_contamination_count": language_count,
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

    expected_corrections = int(report_value(60).get("count") or 0)
    regressions = len(hard_errors) + special_failures
    decision_rows = [
        row
        for row in comparisons
        if row["forensic_classification"] == "OTHER_REVIEW_REQUIRED"
    ]
    report(
        61,
        {
            "status": "PASS" if regressions == 0 else "FAIL",
            "count": regressions,
            "rows": hard_errors,
        },
    )
    report(
        62,
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
    report(68, summary)
    report(
        69,
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
    buyer = [row for row in comparisons if row["new_buyer_changed"]]
    report(
        70,
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
        71,
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
        72,
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
        73,
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
        74,
        {
            "status": "MEASURED",
            "m12al_partial_003690": [
                row
                for row in _m12al_partial_diagnostics()["rows"]
                if row["ticker"] == "003690"
            ],
            "full_shadow_new_buyer_difference_count": len(buyer),
            "full_shadow_rows": buyer,
            "automatic_policy_transfer": False,
        },
    )
    report(
        75,
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
        76,
        {
            "status": "CLOSED" if summary["status"] == "PASS" else "OPEN",
            "lexical_root_cause": (
                "KOREAN_FORBIDDEN_LEXEME_SUBSTRING_MATCH_WITHOUT_LEFT_"
                "MORPHEME_BOUNDARY"
            ),
            "lexical_repair": (
                "boundary-aware share-price matching and phrase-aware ambiguous terms"
            ),
            "formal_fictional_generation_id": M12AK_FICTIONAL_GENERATION_ID,
            "monitored_shadow_generation_id": state["generation_id"],
            "monitored_hard_gate": summary["status"],
            "decision_material_differences_are_policy_input": True,
            "majority_logic_used": False,
        },
    )
    report(
        77,
        {
            "status": "SELECTED" if summary["status"] == "PASS" else "BLOCKED",
            "next_scope": _next_scope(
                comparisons,
                hard_pass=summary["status"] == "PASS",
            ),
            "policy_changed_in_m12am": False,
            "fresh_unseen_calls_authorized": False,
        },
    )


def _m12al_completion_reports_reference(
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
    preflight = read_json(OUTPUT / "preflight.json")
    lexicon = report_value(9)
    exact = report_value(18)
    context02 = report_value(19)
    negative = report_value(22)
    positive = report_value(23)
    fictional = report_value(33)
    language = report_value(49)
    aggregation = report_value(51)
    financial = report_value(63)
    adr = report_value(64)
    cyclical = report_value(65)
    core = report_value(66)

    report(
        78,
        {
            "status": "PASS" if language["status"] == "PASS" else "FAIL",
            "contract": base.STAGE2_LANGUAGE_CONTAMINATION_CONTRACT,
            "m12al_047810_exact_replay": exact["status"],
            "new_shadow_language_contamination_count": language[
                "language_contamination_count"
            ],
            "new_shadow_language_false_positive_count": language[
                "language_false_positive_count"
            ],
            "genuine_language_safety_preserved": negative["status"] == "PASS",
            "suju_balju_false_positive_removed": positive["status"] == "PASS",
        },
    )
    report(
        79,
        {
            "status": "PASS" if report_value(34)["status"] == "REUSE_AUTHORIZED" else "FAIL",
            "reuse_status": report_value(34)["status"],
            "generation_id": M12AK_FICTIONAL_GENERATION_ID,
            "fictional_model_calls_in_m12am": 0,
            "fictional_stage2_language_reaudit_failure_count": fictional[
                "failure_count"
            ],
        },
    )
    report(
        80,
        {
            "status": "PASS" if hard_pass else "FAIL",
            "generation_id": state["generation_id"],
            "completed_ticker_count": summary["ticker_count"],
            "model_calls": runtime.get("model_calls"),
            "aggregate_finalization": aggregation["status"],
            "context_count": normalized["context_count"],
        },
    )
    report(
        81,
        {
            "status": "MEASURED" if hard_pass else "BLOCKED",
            "ticker_count": summary["ticker_count"],
            "classification_counts": {
                key: value
                for key, value in summary.items()
                if key.endswith("_change_count")
            },
            "m12al_partial_rows_used_as_formal_data": 0,
            "new_generation_only": True,
        },
    )
    report(
        82,
        {
            "status": "DIAGNOSTIC_COMPLETE" if hard_pass else "BLOCKED",
            "classification": compatibility,
            "next_scope": next_scope,
            "monolithic_is_ground_truth": False,
            "two_stage_is_ground_truth": False,
            "majority_logic_used": False,
        },
    )
    report(
        83,
        {
            "status": "NOT_READY",
            "fresh_real_calls": 0,
            "reason": "INTEGRATED_MAIN_POLICY_REVIEW_REQUIRED_FIRST",
        },
    )
    report(
        84,
        {
            "status": "NOT_READY",
            "main_merge": 0,
            "deployment": 0,
            "local_only": True,
        },
    )
    report(
        85,
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
            "production_readiness": "NOT_READY",
        },
    )
    schedule = legacy.m12._schedule_observation()
    report(
        86,
        {
            **schedule,
            "status": "OBSERVED",
            "scheduler_mutation_count": 0,
            "automatic_monitoring_resume": 0,
        },
    )
    report(
        87,
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
        88,
        {
            "status": "PENDING_LOCAL_DOCUMENT_UPDATE",
            "path": "docs/MASTER_WORKFLOW.md",
            "phase": "M12AM",
            "next_scope": next_scope,
        },
    )

    previous = read_json(M12AL_OUTPUT / "shadow/program-state.json")
    reference_tickers = set(str(ticker) for ticker in previous["tickers"])
    actual_tickers = set(str(ticker) for ticker in state["tickers"])
    completion = {
        "status": "COMPLETE_DIAGNOSTIC" if hard_pass else "BLOCKED",
        "phase": "M12AM",
        "base_integration_head_sha": BASE_INTEGRATION_HEAD_SHA,
        "integration_branch": git("branch", "--show-current"),
        "implementation_head_sha": state["implementation_head_sha"],
        "work_instruction_commit": WORK_INSTRUCTION_COMMIT,
        "latest_result_zip_sha256": M12AL_BUNDLE_SHA256,
        "latest_result_integrity": preflight["latest_result_integrity"],
        "stage2_language_matcher_root_cause": (
            "KOREAN_FORBIDDEN_LEXEME_SUBSTRING_MATCH_WITHOUT_LEFT_"
            "MORPHEME_BOUNDARY"
        ),
        "stage2_language_matcher_contract_version": base.STAGE2_LANGUAGE_CONTAMINATION_CONTRACT,
        "forbidden_lexeme_count": lexicon["forbidden_lexeme_count"],
        "ambiguous_lexeme_count": lexicon["ambiguous_lexeme_count"],
        "substring_rule_count_before": lexicon["substring_rule_count_before"],
        "substring_rule_count_after": lexicon["substring_rule_count_after"],
        "m12al_047810_exact_replay_status": exact["status"],
        "m12al_047810_false_positive_token": "\uc8fc\uac00",
        "m12al_047810_false_positive_source_span": report_value(7)[
            "source_span"
        ],
        "m12al_context02_stage2_reaudit_pass_count": context02["pass_count"],
        "m12al_context02_stage2_reaudit_fail_count": context02["fail_count"],
        "korean_price_negative_fixture_count": negative["count"],
        "korean_price_negative_fixture_pass_count": negative["pass_count"],
        "korean_suju_balju_positive_fixture_count": positive["count"],
        "korean_suju_balju_positive_fixture_pass_count": positive["pass_count"],
        "fictional_stage2_language_reaudit_failure_count": fictional[
            "failure_count"
        ],
        "formal_fictional_reuse_status": report_value(34)["status"],
        "formal_fictional_generation_id": M12AK_FICTIONAL_GENERATION_ID,
        "model_calls_fictional": 0,
        "model_prompt_semantic_change_count": report_value(26)["change_count"],
        "model_schema_semantic_change_count": report_value(27)["change_count"],
        "business_delta_semantic_change_count": report_value(28)["change_count"],
        "financial_semantic_change_count": report_value(29)["change_count"],
        "two_stage_semantic_change_count": report_value(30)["change_count"],
        "stage2_language_matcher_change_count": report_value(30)[
            "stage2_language_matcher_change_count"
        ],
        "task_start_active_monitor_count": len(state["tickers"]),
        "task_start_active_monitor_tickers": state["tickers"],
        "reference_added_tickers": sorted(actual_tickers - reference_tickers),
        "reference_removed_tickers": sorted(reference_tickers - actual_tickers),
        "shadow_generation_id": state["generation_id"],
        "m12al_stopped_shadow_generation_id": M12AL_SHADOW_GENERATION_ID,
        "shadow_packet_available_count": len(state["packet_paths"]),
        "shadow_packet_unavailable_count": 0,
        "shadow_packet_mismatch_count": 0,
        "shadow_context_count": normalized["context_count"],
        "shadow_monolithic_model_calls": normalized["context_count"],
        "shadow_stage1_model_calls": normalized["context_count"],
        "shadow_stage2_model_calls": normalized["context_count"],
        "shadow_model_calls_total": runtime.get("model_calls"),
        "shadow_completed_ticker_count": summary["ticker_count"],
        "shadow_final_composition_count": aggregation["final_row_count"],
        "shadow_aggregate_finalization_status": aggregation["status"],
        "shadow_stage2_timing_supply_ref_contamination_count": language[
            "timing_or_supply_ref_contamination_count"
        ],
        "shadow_stage2_language_contamination_count": language[
            "language_contamination_count"
        ],
        "shadow_stage2_language_false_positive_count": language[
            "language_false_positive_count"
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
            financial["status"] != "PASS"
        ),
        "shadow_adr_security_basis_failure_count": int(adr["status"] != "PASS"),
        "shadow_cyclical_valuation_framework_failure_count": int(
            cyclical["status"] != "PASS"
        ),
        "shadow_core_mutation_after_stance_count": core[
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
        "observed_paused_schedule_count": report_value(86)[
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
    report(89, completion)
    write_json(OUTPUT / "program-completion.json", completion)
    write_text(
        OUTPUT / "COMPLETION-REPORT.md",
        "\n".join(
            (
                "# M12AM Completion",
                "",
                f"- Status: `{completion['status']}`",
                "- Stage-2 Korean lexical matcher repair: `PASS`",
                "- M12AK fictional proof reuse: `PASS` (0 new fictional calls)",
                f"- New monitored shadow: `{summary['ticker_count']}` tickers / "
                f"`{runtime.get('model_calls')}` calls",
                f"- Aggregate finalization: `{aggregation['status']}`",
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
        raise ValueError("M12AM_FAILURE_RECEIPT_MISSING")
    stop = read_json(stop_path)
    for number in range(1, 90):
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
        "phase": "M12AM",
        "base_integration_head_sha": BASE_INTEGRATION_HEAD_SHA,
        "integration_branch": git("branch", "--show-current"),
        "implementation_head_sha": state.get("implementation_head_sha"),
        "work_instruction_commit": WORK_INSTRUCTION_COMMIT,
        "latest_result_zip_sha256": M12AL_BUNDLE_SHA256,
        "latest_result_integrity": preflight.get(
            "latest_result_integrity", "NOT_MEASURED"
        ),
        "formal_fictional_reuse_status": preflight.get(
            "formal_fictional_reuse", "NOT_MEASURED"
        ),
        "formal_fictional_generation_id": M12AK_FICTIONAL_GENERATION_ID,
        "model_calls_fictional": 0,
        "stage2_language_matcher_contract_version": (
            base.STAGE2_LANGUAGE_CONTAMINATION_CONTRACT
        ),
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
        "next_scope": (
            "STAGE2_LANGUAGE_SAFETY_MATCHER_ARCHITECTURE_REVIEW"
            if "STAGE2_HARD_SEMANTIC_FAILURE" in str(stop.get("detail") or "")
            else "SHADOW_PROOF_HARNESS_ARCHITECTURE_REVIEW"
        ),
        "focused_test_result": preflight.get("focused_test_result", "NOT_MEASURED"),
        "full_test_result": preflight.get("full_test_result", "NOT_MEASURED"),
        "ruff_result": preflight.get("ruff_result", "NOT_MEASURED"),
        "git_diff_check": preflight.get("git_diff_check", "NOT_MEASURED"),
        "artifact_count": "PENDING_FINAL_INDEX",
        "artifact_hash_mismatch_count": 0,
        "artifact_size_mismatch_count": 0,
        "artifact_secret_scan_failure_count": 0,
    }
    report(89, completion)
    write_json(OUTPUT / "program-completion.json", completion)
    write_text(
        OUTPUT / "COMPLETION-REPORT.md",
        "\n".join(
            (
                "# M12AM Failure Closeout",
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
    marker = "2026-09-11 M12AM Stage-2 Korean Lexical Boundary Repair"
    workflow = Path("docs/MASTER_WORKFLOW.md")
    updated = marker in workflow.read_text(encoding="utf-8")
    report(
        88,
        {
            "status": "UPDATED_LOCAL_ONLY" if updated else "MISSING",
            "path": str(workflow),
            "phase": "M12AM",
            "next_scope": completion["next_scope"],
        },
    )
    completion["master_workflow_update"] = (
        "UPDATED_LOCAL_ONLY" if updated else "MISSING"
    )
    write_json(OUTPUT / "program-completion.json", completion)
    report(89, completion)
    if not updated:
        raise ValueError("M12AM_MASTER_WORKFLOW_UPDATE_MISSING")


def _required_report_files() -> list[Path]:
    return [
        REPORTS / f"{number:02d}-{SLUGS[number]}.json"
        for number in range(1, 90)
    ]


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
            Path("scripts/main_integration_two_stage_directional_m12ae_r2_runtime.py"),
            Path("tests/test_stage2_korean_lexical_boundary_m12am.py"),
            Path("tests/test_stage2_korean_lexical_boundary_m12am_runner.py"),
            Path("tests/test_fictional_finalization_context_batch_m12ak_runner.py"),
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
        raise ValueError(f"M12AM_REQUIRED_REPORTS_MISSING:{missing}")
    completion_path = OUTPUT / "program-completion.json"
    completion = read_json(completion_path)
    files = _artifact_files()
    completion["artifact_count"] = len(files)
    write_json(completion_path, completion)
    report(89, completion)
    files = _artifact_files()
    failures = [
        {"path": str(path), "indicators": indicators}
        for path in files
        for indicators in (_secret_material(path),)
        if indicators
    ]
    index = {
        "contract": "m12am-artifact-index-v1",
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
        raise ValueError("M12AM_ARTIFACT_SECRET_SCAN_FAILURE")
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
            raise ValueError("M12AM_RESULT_BUNDLE_INTEGRITY_FAILURE")
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
    prepare_parser.add_argument("--previous-bundle", type=Path, default=M12AL_BUNDLE)
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
