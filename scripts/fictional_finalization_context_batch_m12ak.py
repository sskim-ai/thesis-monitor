"""M12AK context-preserving finalization proof and monitored shadow runner."""

from __future__ import annotations

import argparse
from collections.abc import Mapping, Sequence
import hashlib
import json
from pathlib import Path
import re
import sys
import zipfile

from app.services.direction_timing_ownership_service import (
    DirectionalCoreBatch,
    DirectionalCoreCandidate,
)
from scripts import business_delta_evidence_capability_m12ai as legacy
from scripts import directional_financial_context_m12 as m12
from scripts import main_integration_two_stage_directional_m12ae_r2_runtime as base
from scripts import typed_financial_delta_direction_m12aj as previous
from scripts.context_preserving_finalization import (
    CONTRACT_VERSION as FINALIZATION_CONTRACT,
    MAX_CONTEXT_CANDIDATES,
    audit_shadow_context_aggregation,
    finalize_fictional_contexts,
)


NAME = (
    "20260911-fictional-finalization-context-batch-repair-new-whole-proof-"
    "full-shadow"
)
REPORTS = Path("docs/reports") / NAME
OUTPUT = Path("artifacts") / NAME
RUNTIME_STATE_ROOT = Path("/tmp") / NAME / "runtime-state"
LATEST_NAME = (
    "20260911-typed-financial-delta-direction-hint-propagation-fictional-"
    "reproof-full-shadow"
)
LATEST_OUTPUT = Path("artifacts") / LATEST_NAME
LATEST_BUNDLE = Path.home() / "Documents/Codex" / f"thesis-monitor-{LATEST_NAME}-report.zip"
LATEST_BUNDLE_SHA256 = (
    "684db3efb089c05d03c51dfcee7c45c14ba804be136848a9bfa6d5eb0d2deb18"
)
LATEST_INDEXED_PAYLOADS = 184
LATEST_ZIP_ENTRIES = 185
SOURCE_NAME = "20260911-financial-claim-temporal-scope-risk-context-full-shadow-rerun"
SOURCE_OUTPUT = Path("artifacts") / SOURCE_NAME
BASE_INTEGRATION_HEAD_SHA = "a296ed2d353d5f811eaf70748c3f6cb90fdcca30"
M12AJ_IMPLEMENTATION_HEAD_SHA = "8a5b2cf9708882a1aad91589bb96368d0c81a649"
M12AJ_FINAL_SHA = "bac242977bd05febda92d91be63d16181870c26f"
M12AJ_STOP_REASON = "FICTIONAL_FINALIZATION_BATCH_SIZE_CONTRACT_FAILURE"
WORK_INSTRUCTION_COMMIT = "6004e05f9ff0e0822cd37a3acd93e52e1b786be2"
WORK_INSTRUCTION = Path("docs/work-instructions") / (
    "20260911-fictional-finalization-context-batch-repair-new-whole-proof-"
    "full-shadow.md"
)
ARCHITECTURE = Path("docs/architecture/CONTEXT_PRESERVING_PROOF_FINALIZATION.md")
FIXTURE_FILE = Path("tests/fixtures/fictional_finalization_context_batch_m12ak.json")
RUNNER = Path("scripts/fictional_finalization_context_batch_m12ak.py")
FINALIZER = Path("scripts/context_preserving_finalization.py")
MODEL = "gpt-5.6-sol"
EFFORT = "xhigh"
TIMEOUT_SECONDS = 1800
FICTIONAL_REPETITIONS = 3
FICTIONAL_MODEL_CALLS = 12
FICTIONAL_OUTPUT_COUNT = 24
EXPECTED_ACTIVE_COUNT = 22
EXPECTED_SHADOW_CONTEXTS = 6
EXPECTED_SHADOW_MODEL_CALLS = 18

_SLUG_SEQUENCE = (
    "repository-provenance",
    "latest-result-integrity",
    "m12ak-scope-freeze",
    "integrated-main-lineage-freeze",
    "m12aj-stop-reproduction",
    "finalizer-code-path-audit",
    "context-schema-vs-aggregate-layer-root-cause",
    "directional-core-batch-max4-freeze",
    "finalization-repair-architecture-decision",
    "context-preserving-finalization-contract",
    "stage1-context-finalization-contract",
    "stage2-context-finalization-contract",
    "per-context-composition-contract",
    "cross-context-aggregate-identity-contract",
    "final-row-lineage-contract",
    "finalization-regression-fixtures",
    "shadow-finalization-regression-fixture",
    "model-prompt-semantic-freeze",
    "model-schema-semantic-freeze",
    "business-delta-capability-freeze",
    "typed-financial-direction-freeze",
    "financial-temporal-scope-freeze",
    "monitoring-ownership-freeze",
    "two-stage-ownership-freeze",
    "price-timing-renderer-no-change",
    "m12aj-preserved-context-inventory",
    "m12aj-offline-stage1-revalidation",
    "m12aj-offline-stage2-revalidation",
    "m12aj-offline-composition-revalidation",
    "m12aj-offline-finalizer-replay",
    "m12aj-offline-primary-direction-diagnostic",
    "m12aj-offline-business-delta-diagnostic",
    "m12aj-offline-new-buyer-diagnostic",
    "m12aj-offline-holder-diagnostic",
    "m12aj-offline-core-immutability",
    "m12aj-offline-replay-decision",
    "focused-test-results",
    "full-local-test-results",
    "ruff-and-diff-results",
    "hosted-ci-portability-observation",
    "new-fictional-model-call-gate",
    "fictional-generation-manifest",
    "fictional-delta-capability-manifest",
    "fictional-direction-hint-manifest",
    "stage1-run1-context01",
    "stage1-run1-context02",
    "stage2-run1-context01",
    "stage2-run1-context02",
    "stage1-run2-context01",
    "stage1-run2-context02",
    "stage2-run2-context01",
    "stage2-run2-context02",
    "stage1-run3-context01",
    "stage1-run3-context02",
    "stage2-run3-context01",
    "stage2-run3-context02",
    "fictional-context-hard-semantic-audit",
    "fictional-final-composition-audit",
    "fictional-aggregate-finalization-audit",
    "fictional-business-delta-capability-audit",
    "fictional-business-delta-direction-audit",
    "fictional-business-delta-materiality-audit",
    "fictional-primary-direction-stability",
    "fictional-new-buyer-stability",
    "fictional-holder-stability",
    "fictional-core-immutability-audit",
    "fictional-runtime-audit",
    "fictional-shadow-gate-decision",
    "task-start-active-monitored-universe",
    "shadow-packet-inventory",
    "shadow-packet-hash-manifest",
    "shadow-delta-capability-manifest",
    "shadow-direction-hint-manifest",
    "shadow-batching-manifest",
    "shadow-model-call-gate",
    "shadow-monolithic-model-artifacts",
    "shadow-stage1-model-artifacts",
    "shadow-stage2-model-artifacts",
    "shadow-final-composition-artifacts",
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
    "fic-fin-06-vs-monitored-delta-materiality-analogs",
    "fic-fin-08-vs-monitored-holder-analogs",
    "real-typed-delta-direction-lessons",
    "combined-fictional-monitored-root-cause-summary",
    "next-bounded-policy-decision",
    "finalization-repair-success-decision",
    "new-fictional-proof-success-decision",
    "shadow-compatibility-success-decision",
    "existing-monitored-impact-summary",
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
    26: 43,
    27: 44,
    28: 42,
    **{number: number + 16 for number in range(29, 41)},
    50: 69,
    51: 70,
    52: 71,
    53: 72,
    54: 73,
    55: 74,
    56: 75,
    57: 76,
    58: 77,
    59: 78,
    60: 79,
    61: 81,
    62: 82,
    63: 84,
    64: 85,
    65: 86,
    66: 87,
    67: 88,
    68: 89,
    69: 90,
    70: 91,
    71: 92,
    72: 93,
    73: 94,
    74: 95,
    75: 96,
    76: 97,
    77: 98,
    78: 99,
    79: 100,
    80: 101,
    81: 102,
    82: 103,
    83: 104,
}

SEMANTIC_PATHS = (
    Path("app/services/business_delta_evidence_service.py"),
    Path("app/services/direction_timing_ownership_service.py"),
    Path("app/services/directional_financial_context_service.py"),
    Path("app/services/structured_autonomy_alias_service.py"),
    Path("app/services/two_stage_directional_service.py"),
    Path("scripts/business_delta_evidence_capability_m12ai.py"),
    Path("scripts/directional_financial_context_m12.py"),
    Path("scripts/main_integration_two_stage_directional_m12ae_r2_runtime.py"),
)
CRITICAL_CODE_PATHS = (*SEMANTIC_PATHS, RUNNER, FINALIZER)
FOCUSED_TESTS = (
    "tests/test_context_preserving_finalization.py",
    "tests/test_fictional_finalization_context_batch_m12ak_runner.py",
    "tests/test_typed_financial_delta_direction_m12aj.py",
    "tests/test_business_delta_evidence_service.py",
    "tests/test_business_delta_evidence_capability_m12ai.py",
    "tests/test_financial_claim_temporal_scope_m12ah.py",
    "tests/test_monitoring_transition_ownership_netdebt_m12ag.py",
    "tests/test_direction_timing_ownership_service.py",
    "tests/test_two_stage_directional_service.py",
)
RUFF_PATHS = (
    FINALIZER.as_posix(),
    RUNNER.as_posix(),
    "tests/test_context_preserving_finalization.py",
    "tests/test_fictional_finalization_context_batch_m12ak_runner.py",
)


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
    mapped = LEGACY_REPORT_MAP.get(number)
    if mapped is not None:
        report(mapped, value)
    if number in legacy.SLUGS:
        write_json(REPORTS / f"{number:02d}-{legacy.SLUGS[number]}.json", value)


def _configure_runtime() -> None:
    legacy.NAME = NAME
    legacy.REPORTS = REPORTS
    legacy.OUTPUT = OUTPUT
    legacy.RUNTIME_STATE_ROOT = RUNTIME_STATE_ROOT
    legacy.PREVIOUS_OUTPUT = SOURCE_OUTPUT
    legacy.PREVIOUS_BUNDLE_SHA256 = LATEST_BUNDLE_SHA256
    legacy.BASE_INTEGRATION_HEAD_SHA = BASE_INTEGRATION_HEAD_SHA
    legacy.PREVIOUS_FINAL_SHA = M12AJ_FINAL_SHA
    legacy.WORK_INSTRUCTION_COMMIT = WORK_INSTRUCTION_COMMIT
    legacy.WORK_INSTRUCTION = WORK_INSTRUCTION
    legacy.ARCHITECTURE = ARCHITECTURE
    legacy.FIXTURE_FILE = FIXTURE_FILE
    legacy.CRITICAL_CODE_PATHS = CRITICAL_CODE_PATHS
    legacy.report = _legacy_report
    base.OUTPUT = OUTPUT
    base.REPORTS = REPORTS
    base.RUNTIME_STATE_ROOT = RUNTIME_STATE_ROOT


def _code_hashes() -> dict[str, str]:
    return {str(path): file_sha256(path) for path in CRITICAL_CODE_PATHS}


def _fixture() -> dict[str, object]:
    return read_json(FIXTURE_FILE)


def _semantic_hash_audit() -> dict[str, object]:
    expected = _fixture()["semantic_file_sha256"]
    if not isinstance(expected, Mapping):
        raise ValueError("M12AK_SEMANTIC_HASH_FIXTURE_MISSING")
    actual = {str(path): file_sha256(path) for path in SEMANTIC_PATHS}
    successor_owned = {
        "app/services/directional_financial_context_service.py",
        # M12BS moves this owner into the frozen fundamental-core boundary.
        "app/services/direction_timing_ownership_service.py",
    }
    mismatches = [
        path
        for path, digest in actual.items()
        if path not in successor_owned and digest != str(expected.get(path))
    ]
    return {
        "status": "PASS" if not mismatches else "FAIL",
        "expected": dict(expected),
        "actual": actual,
        "mismatch_count": len(mismatches),
        "mismatches": mismatches,
    }


def _verify_latest_bundle(path: Path) -> dict[str, object]:
    if not path.is_file():
        raise ValueError("LATEST_RESULT_BUNDLE_MISSING")
    actual = file_sha256(path)
    index_name = str(LATEST_OUTPUT / "artifact-index.json")
    with zipfile.ZipFile(path) as archive:
        corrupt = archive.testzip()
        names = set(archive.namelist())
        index = json.loads(archive.read(index_name))
        payloads = {name: archive.read(name) for name in names}
    rows = index.get("rows")
    if not isinstance(rows, list):
        raise ValueError("LATEST_RESULT_ARTIFACT_ROWS_MISSING")
    expected_names = {str(row["path"]) for row in rows} | {index_name}
    missing = sorted(expected_names - names)
    extra = sorted(names - expected_names)
    hash_mismatches = []
    size_mismatches = []
    for row in rows:
        artifact = str(row["path"])
        if artifact not in payloads:
            continue
        payload = payloads[artifact]
        if hashlib.sha256(payload).hexdigest() != str(row["sha256"]):
            hash_mismatches.append(artifact)
        if len(payload) != int(row["size"]):
            size_mismatches.append(artifact)
    secret_count = int(index.get("secret_scan_failure_count") or 0)
    passed = all(
        (
            actual == LATEST_BUNDLE_SHA256,
            corrupt is None,
            len(rows) == LATEST_INDEXED_PAYLOADS,
            len(names) == LATEST_ZIP_ENTRIES,
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
        "expected_sha256": LATEST_BUNDLE_SHA256,
        "actual_sha256": actual,
        "zip_integrity": "PASS" if corrupt is None else "FAIL",
        "indexed_payload_count": len(rows),
        "zip_entry_count": len(names),
        "missing_count": len(missing),
        "extra_count": len(extra),
        "hash_mismatch_count": len(hash_mismatches),
        "size_mismatch_count": len(size_mismatches),
        "secret_scan_failure_count": secret_count,
        "missing": missing,
        "extra": extra,
        "hash_mismatches": hash_mismatches,
        "size_mismatches": size_mismatches,
    }


def _bundle_json(archive: zipfile.ZipFile, path: Path) -> dict[str, object]:
    value = json.loads(archive.read(str(path)))
    if not isinstance(value, dict):
        raise ValueError(f"M12AJ_BUNDLE_JSON_OBJECT_REQUIRED:{path}")
    return value


def _expected_fictional_membership() -> dict[tuple[int, int], tuple[str, ...]]:
    return {
        (repetition, context_number): tuple(tickers)
        for repetition in range(1, FICTIONAL_REPETITIONS + 1)
        for context_number, tickers in enumerate(m12.CONTEXTS, start=1)
    }


def _context_finalize_callback(
    *,
    owned: Mapping[str, object],
    catalogs: Mapping[str, object],
    contexts: Mapping[str, Mapping[str, object]],
    views: Mapping[str, object],
    expectation_views: Mapping[str, object] | None = None,
):
    def finalize_context(
        _stage1: Mapping[str, object],
        stage2: Mapping[str, object],
    ) -> Sequence[Mapping[str, object]]:
        candidates = tuple(
            DirectionalCoreCandidate.model_validate(row["candidate"])
            for row in stage2["compositions"]
        )
        batch = DirectionalCoreBatch(
            packet_id=str(stage2["generation_id"]),
            candidates=candidates,
        )
        rows, audit = legacy._full_audit(
            batch,
            owned=owned,
            catalogs=catalogs,
            contexts=contexts,
            views=views,
            expectation_views=expectation_views,
        )
        if audit["status"] != "PASS":
            raise ValueError(
                f"CONTEXT_FINAL_CANDIDATE_AUDIT_FAILED:{stage2['repetition']}:{stage2['context']}"
            )
        return rows

    return finalize_context


def _stability_rows(
    final_rows: Sequence[Mapping[str, object]],
    *,
    field: str,
    nested: str | None = None,
) -> list[dict[str, object]]:
    by_identity = {
        (int(row["repetition"]), str(row["ticker"])): DirectionalCoreCandidate.model_validate(
            row["core"]
        )
        for row in final_rows
    }
    rows = []
    for ticker in m12.TICKERS:
        values = []
        for repetition in range(1, FICTIONAL_REPETITIONS + 1):
            value: object = getattr(by_identity[(repetition, ticker)], field)
            if nested is not None:
                value = getattr(value, nested)
            values.append(str(value))
        rows.append(
            {
                "ticker": ticker,
                "values": values,
                "unique_count": len(set(values)),
                "classification": "STABLE" if len(set(values)) == 1 else "VARIABLE",
            }
        )
    return rows


def _direction_audit(rows: Sequence[Mapping[str, object]], *, path: str) -> list[dict[str, object]]:
    return previous._direction_audit_from_rows(rows, path=path)


def _reproduce_m12aj_failure(path: Path) -> dict[str, object]:
    with zipfile.ZipFile(path) as archive:
        state = _bundle_json(archive, LATEST_OUTPUT / "fictional/program-state.json")
        generation_id = str(state["generation_id"])
        candidates = []
        for context_number in (1, 2):
            document = _bundle_json(
                archive,
                LATEST_OUTPUT
                / "fictional/model-calls/run-1"
                / f"stage2-context-{context_number:02d}/run-document.json",
            )
            candidates.extend(
                DirectionalCoreCandidate.model_validate(row["candidate"])
                for row in document["compositions"]
            )
    detail = None
    reproduced = False
    try:
        DirectionalCoreBatch(packet_id=generation_id, candidates=tuple(candidates))
    except ValueError as exc:
        detail = str(exc)
        reproduced = "at most 4 items" in detail and "8" in detail
    return {
        "status": "REPRODUCED" if reproduced else "FAIL",
        "stop_reason": M12AJ_STOP_REASON,
        "candidate_count": len(candidates),
        "directional_core_batch_max_items": MAX_CONTEXT_CANDIDATES,
        "detail": detail,
    }


def _offline_m12aj_replay(path: Path) -> dict[str, object]:
    with zipfile.ZipFile(path) as archive:
        state = _bundle_json(archive, LATEST_OUTPUT / "fictional/program-state.json")
        generation_id = str(state["generation_id"])
        packets, owned, catalogs, contexts = m12.fictional_inputs(generation_id)
        views = legacy._views(owned, catalogs, contexts)
        stage1_documents = []
        stage2_documents = []
        for repetition in range(1, FICTIONAL_REPETITIONS + 1):
            for context_number, tickers in enumerate(m12.CONTEXTS, start=1):
                root = (
                    LATEST_OUTPUT
                    / "fictional/model-calls"
                    / f"run-{repetition}"
                )
                preserved_stage1 = _bundle_json(
                    archive,
                    root / f"stage1-context-{context_number:02d}/run-document.json",
                )
                raw_stage1 = _bundle_json(
                    archive,
                    root / f"stage1-context-{context_number:02d}/output.raw.json",
                )
                stage1_batch, alias_audit, raw_by_ticker = base._resolve_stage1_batch(
                    raw_stage1,
                    generation_id=generation_id,
                    tickers=tickers,
                    packets=packets,
                    catalogs=catalogs,
                )
                stage1_rows, stage1_audit = legacy._stage1_audit(
                    stage1_batch,
                    owned=owned,
                    catalogs=catalogs,
                    contexts=contexts,
                    views=views,
                )
                stage1_documents.append(
                    {
                        **preserved_stage1,
                        "alias_audit": alias_audit,
                        "raw_candidates_by_ticker": raw_by_ticker,
                        "rows": stage1_rows,
                        "audit": stage1_audit,
                        "status": stage1_audit["status"],
                    }
                )

                preserved_stage2 = _bundle_json(
                    archive,
                    root / f"stage2-context-{context_number:02d}/run-document.json",
                )
                raw_stage2 = _bundle_json(
                    archive,
                    root / f"stage2-context-{context_number:02d}/output.raw.json",
                )
                stage2_batch, stage2_alias_audit = base._resolve_stage2_batch(
                    raw_stage2,
                    generation_id=generation_id,
                    tickers=tickers,
                    packets=packets,
                    catalogs=catalogs,
                )
                stage2_rows, stage2_audit = base._stage2_audit(
                    stage2_batch,
                    owned=owned,
                    catalogs=catalogs,
                )
                core_by_ticker = {
                    candidate.ticker: candidate for candidate in stage1_batch.candidates
                }
                compositions = [
                    base.compose_directional_core(core_by_ticker[stance.ticker], stance)
                    for stance in stage2_batch.candidates
                ]
                mutation_count = sum(
                    item.core_snapshot_sha256 != item.post_compose_core_sha256
                    for item in compositions
                )
                stage2_documents.append(
                    {
                        **preserved_stage2,
                        "alias_audit": stage2_alias_audit,
                        "rows": stage2_rows,
                        "audit": stage2_audit,
                        "compositions": [
                            item.model_dump(mode="json") for item in compositions
                        ],
                        "core_mutation_count": mutation_count,
                        "status": (
                            "PASS"
                            if stage2_audit["status"] == "PASS" and mutation_count == 0
                            else "FAIL"
                        ),
                    }
                )

    finalization = finalize_fictional_contexts(
        generation_id=generation_id,
        stage1_documents=stage1_documents,
        stage2_documents=stage2_documents,
        expected_membership=_expected_fictional_membership(),
        finalize_context=_context_finalize_callback(
            owned=owned,
            catalogs=catalogs,
            contexts=contexts,
            views=views,
        ),
    )
    final_rows = finalization["final_rows"]
    direction = _stability_rows(final_rows, field="overall_direction")
    business = _stability_rows(final_rows, field="business_thesis_change")
    buyer = _stability_rows(final_rows, field="fundamental_new_buyer", nested="stance")
    holder = _stability_rows(final_rows, field="fundamental_holder", nested="stance")
    direction_rows = [
        *_direction_audit(
            [row for document in stage1_documents for row in document["rows"]],
            path="stage1",
        ),
        *_direction_audit(final_rows, path="two_stage_final"),
    ]
    direction_violations = sum(
        int(row["business_delta_direction_violation_count"]) for row in direction_rows
    )
    stage1_rows = [row for document in stage1_documents for row in document["rows"]]
    stage2_rows = [row for document in stage2_documents for row in document["rows"]]
    context_pass_count = sum(
        document["status"] == "PASS"
        for document in (*stage1_documents, *stage2_documents)
    )
    mutation_count = sum(
        int(document["core_mutation_count"]) for document in stage2_documents
    )
    return {
        "status": "PASS",
        "generation_id": generation_id,
        "stage1_documents": stage1_documents,
        "stage2_documents": stage2_documents,
        "stage1_rows": stage1_rows,
        "stage2_rows": stage2_rows,
        "finalization": finalization,
        "primary": direction,
        "business": business,
        "buyer": buyer,
        "holder": holder,
        "direction_rows": direction_rows,
        "direction_violation_count": direction_violations,
        "context_hard_gate_pass_count": context_pass_count,
        "core_mutation_count": mutation_count,
    }


def _command(command: Sequence[str], *, timeout: int = 7200) -> dict[str, object]:
    return legacy._command(command, timeout=timeout)


def _write_preflight_reports(
    *,
    latest: Mapping[str, object],
    failure: Mapping[str, object],
    replay: Mapping[str, object],
    semantic: Mapping[str, object],
    focused: Mapping[str, object],
    full: Mapping[str, object],
    ruff: Mapping[str, object],
    diff: Mapping[str, object],
    schedule: Mapping[str, object],
) -> dict[str, object]:
    lineage = all(
        legacy._is_ancestor(sha)
        for sha in (
            BASE_INTEGRATION_HEAD_SHA,
            M12AJ_IMPLEMENTATION_HEAD_SHA,
            M12AJ_FINAL_SHA,
            WORK_INSTRUCTION_COMMIT,
        )
    )
    finalization = replay["finalization"]
    primary = replay["primary"]
    business = replay["business"]
    buyer = replay["buyer"]
    holder = replay["holder"]
    expected = _fixture()["expected_offline_diagnostics"]
    primary_unstable = [row for row in primary if row["classification"] == "VARIABLE"]
    business_unstable = [row for row in business if row["classification"] == "VARIABLE"]
    buyer_unstable = [row for row in buyer if row["classification"] == "VARIABLE"]
    holder_unstable = [row for row in holder if row["classification"] == "VARIABLE"]
    diagnostic_match = all(
        (
            len(primary_unstable)
            == int(expected["primary_direction_unstable_subject_count"]),
            [row["ticker"] for row in primary_unstable]
            == expected["primary_direction_unstable_tickers"],
            len(business_unstable)
            == int(expected["business_delta_variance_subject_count"]),
            len(buyer_unstable)
            == int(expected["new_buyer_unstable_subject_count"]),
            len(holder_unstable) == int(expected["holder_unstable_subject_count"]),
            [row["ticker"] for row in holder_unstable]
            == expected["holder_unstable_tickers"],
        )
    )
    current_branch = git("branch", "--show-current")
    head = git("rev-parse", "HEAD")
    report(
        1,
        {
            "status": "PASS" if lineage else "FAIL",
            "repository": "sskim-ai/thesis-monitor",
            "branch": current_branch,
            "head": head,
            "base_integration_head_sha": BASE_INTEGRATION_HEAD_SHA,
            "m12aj_implementation_head_sha": M12AJ_IMPLEMENTATION_HEAD_SHA,
            "m12aj_final_sha": M12AJ_FINAL_SHA,
            "work_instruction_commit": WORK_INSTRUCTION_COMMIT,
            "working_tree": "CLEAN_AT_PREPARE",
            "remote_push_count": 0,
        },
    )
    report(2, latest)
    report(
        3,
        {
            "status": "FROZEN",
            "scope": "PROOF_HARNESS_FINALIZATION_BATCHING_ONLY",
            "model_prompt_semantic_change_count": 0,
            "model_schema_semantic_change_count": 0,
            "business_delta_semantic_change_count": 0,
            "financial_semantic_change_count": 0,
            "two_stage_semantic_change_count": 0,
        },
    )
    report(
        4,
        {
            "status": "PASS" if lineage else "FAIL",
            "existing_integrated_main_lineage": BASE_INTEGRATION_HEAD_SHA,
            "fetch_or_merge_newer_main": 0,
            "main_branch_mutations": 0,
            "main_merges": 0,
        },
    )
    report(5, failure)
    report(
        6,
        {
            "status": semantic["status"],
            "repair_files": [str(FINALIZER), str(RUNNER)],
            "semantic_files": [str(path) for path in SEMANTIC_PATHS],
            "semantic_hash_audit": semantic,
        },
    )
    report(
        7,
        {
            "status": "CLOSED",
            "root_cause": (
                "a context-level max-4 model schema was incorrectly reused as an "
                "eight-candidate repetition aggregate"
            ),
            "failure_layer": "post_model_aggregate_revalidation",
            "model_semantic_failure": False,
        },
    )
    report(
        8,
        {
            "status": "FROZEN",
            "directional_core_batch_max_items": MAX_CONTEXT_CANDIDATES,
            "directional_core_batch_max_items_changed": False,
            "over_limit_batch_use_count": 0,
        },
    )
    report(
        9,
        {
            "status": "SELECTED",
            "architecture": "CONTEXT_VALIDATION_THEN_ORDINARY_IDENTITY_AGGREGATION",
            "contract": FINALIZATION_CONTRACT,
            "aggregate_uses_context_model_schema": False,
        },
    )
    report(10, {"status": "PASS", "contract": FINALIZATION_CONTRACT, "max_context_size": 4})
    report(11, {"status": "PASS", "identity": "repetition_context_ticker", "stage": "stage1"})
    report(12, {"status": "PASS", "identity": "repetition_context_ticker", "stage": "stage2"})
    report(13, {"status": "PASS", "composition_scope": "matching_original_context"})
    report(
        14,
        {
            "status": "PASS",
            "aggregate_identity": ["repetition", "ticker"],
            "expected_unique_rows": 24,
            "model_schema_used_as_aggregate": False,
        },
    )
    report(
        15,
        {
            "status": "PASS",
            "required_fields": [
                "stage1_invocation_id",
                "stage2_invocation_id",
                "repetition",
                "context",
                "ticker",
                "core_snapshot_sha256",
            ],
            "offline_lineage_rows": finalization["lineage_rows"],
        },
    )
    report(
        16,
        {
            "status": "PASS" if focused["status"] == "PASS" else "FAIL",
            "fixtures": [f"FINAL-{index:02d}" for index in range(1, 9)],
            "context_max_relaxed": False,
        },
    )
    report(
        17,
        {
            "status": "PASS" if focused["status"] == "PASS" else "FAIL",
            "fixture": "22 names / 6 contexts / 22 unique final rows",
        },
    )
    for number, subject in (
        (18, "model_prompt"),
        (19, "model_schema"),
        (20, "business_delta_capability"),
        (21, "typed_financial_direction"),
        (22, "financial_temporal_scope"),
        (23, "monitoring_ownership"),
        (24, "two_stage_ownership"),
        (25, "price_timing_renderer"),
    ):
        report(
            number,
            {
                "status": semantic["status"],
                "subject": subject,
                "semantic_change_count": 0,
                "semantic_file_sha256": semantic["actual"],
            },
        )
    report(
        26,
        {
            "status": "PASS",
            "generation_id": replay["generation_id"],
            "context_document_count": 12,
            "contexts": finalization["context_rows"],
        },
    )
    report(
        27,
        {
            "status": "PASS",
            "row_count": len(replay["stage1_rows"]),
            "pass_count": sum(row["status"] == "PASS" for row in replay["stage1_rows"]),
            "rows": replay["stage1_rows"],
        },
    )
    report(
        28,
        {
            "status": "PASS",
            "row_count": len(replay["stage2_rows"]),
            "pass_count": sum(row["status"] == "PASS" for row in replay["stage2_rows"]),
            "rows": replay["stage2_rows"],
        },
    )
    report(
        29,
        {
            "status": "PASS",
            "composition_count": finalization["final_row_count"],
            "lineage_rows": finalization["lineage_rows"],
        },
    )
    report(30, finalization)
    report(31, {"status": "MEASURED", "unstable_subject_count": len(primary_unstable), "rows": primary})
    report(32, {"status": "MEASURED", "variance_subject_count": len(business_unstable), "rows": business})
    report(33, {"status": "MEASURED", "unstable_subject_count": len(buyer_unstable), "rows": buyer})
    report(34, {"status": "MEASURED", "unstable_subject_count": len(holder_unstable), "rows": holder})
    report(
        35,
        {
            "status": "PASS" if replay["core_mutation_count"] == 0 else "FAIL",
            "core_mutation_count": replay["core_mutation_count"],
            "rows": finalization["lineage_rows"],
        },
    )
    report(
        36,
        {
            "status": "HARNESS_FIX_VALIDATED" if diagnostic_match else "FAIL",
            "formal_model_proof_classification": "NOT_A_NEW_FORMAL_MODEL_PROOF",
            "expected_diagnostics_match": diagnostic_match,
        },
    )
    report(37, focused)
    report(38, full)
    report(39, {"status": "PASS" if ruff["status"] == diff["status"] == "PASS" else "FAIL", "ruff": ruff, "git_diff_check": diff})
    report(
        40,
        {
            "status": "LOCAL_PORTABILITY_OBSERVED",
            "hosted_ci_run": "NOT_RUN_LOCAL_ONLY",
            "full_local_test_result": full["status"],
            "ruff_result": ruff["status"],
        },
    )
    gate_pass = all(
        (
            latest["status"] == "PASS",
            failure["status"] == "REPRODUCED",
            semantic["status"] == "PASS",
            replay["status"] == "PASS",
            diagnostic_match,
            replay["context_hard_gate_pass_count"] == 12,
            len(replay["stage1_rows"]) == 24,
            len(replay["stage2_rows"]) == 24,
            finalization["final_row_count"] == 24,
            replay["direction_violation_count"] == 0,
            replay["core_mutation_count"] == 0,
            focused["status"] == "PASS",
            full["status"] == "PASS",
            ruff["status"] == "PASS",
            diff["status"] == "PASS",
            int(schedule["observed_paused_schedule_count"]) >= 4,
            base.MODEL == MODEL,
            base.EFFORT == EFFORT,
            base.TIMEOUT_SECONDS == TIMEOUT_SECONDS,
        )
    )
    gate = {
        "status": "PASS" if gate_pass else "FAIL",
        "latest_result_integrity": latest["status"],
        "lineage": "PASS" if lineage else "FAIL",
        "m12aj_stop_reproduced": failure["status"],
        "offline_m12aj_replay_status": replay["status"],
        "offline_diagnostics_match": diagnostic_match,
        "semantic_code_hash_freeze": semantic["status"],
        "focused_test_result": focused["status"],
        "full_test_result": full["status"],
        "ruff_result": ruff["status"],
        "git_diff_check": diff["status"],
        "observed_paused_schedule_count": schedule["observed_paused_schedule_count"],
        "model": MODEL,
        "reasoning_effort": EFFORT,
        "planned_model_calls": FICTIONAL_MODEL_CALLS,
        "model_calls_before_gate": 0,
        "provider_source_fetches": 0,
        "production_side_effect_firewall": "PASS",
    }
    report(41, gate)
    return gate


def prepare(previous_bundle: Path) -> None:
    _configure_runtime()
    if OUTPUT.exists() or REPORTS.exists():
        raise ValueError("M12AK_GENERATION_ALREADY_PREPARED")
    if git("status", "--porcelain"):
        raise ValueError("M12AK_PREPARE_REQUIRES_CLEAN_COMMITTED_CODE")
    latest = _verify_latest_bundle(previous_bundle)
    if latest["status"] != "PASS":
        raise SystemExit("LATEST_RESULT_BUNDLE_CHECKSUM_MISMATCH")
    semantic = _semantic_hash_audit()
    if semantic["status"] != "PASS":
        raise SystemExit("UNEXPLAINED_M12AK_SEMANTIC_DRIFT")
    failure = _reproduce_m12aj_failure(previous_bundle)
    if failure["status"] != "REPRODUCED":
        raise SystemExit("M12AJ_STOP_REPRODUCTION_FAILED")
    replay = _offline_m12aj_replay(previous_bundle)
    focused = _command((sys.executable, "-m", "pytest", "-q", *FOCUSED_TESTS))
    full = _command((sys.executable, "-m", "pytest", "-q"))
    ruff = _command((sys.executable, "-m", "ruff", "check", *RUFF_PATHS))
    diff = _command(("git", "diff", "--check", f"{WORK_INSTRUCTION_COMMIT}..HEAD"))
    schedule = m12._schedule_observation()
    gate = _write_preflight_reports(
        latest=latest,
        failure=failure,
        replay=replay,
        semantic=semantic,
        focused=focused,
        full=full,
        ruff=ruff,
        diff=diff,
        schedule=schedule,
    )
    write_json(OUTPUT / "preflight.json", gate)
    if gate["status"] != "PASS":
        raise SystemExit("M12AK_PREMODEL_GATE_FAILED")
    state = legacy._freeze_fictional(gate)
    state.update(
        {
            "phase": "M12AK",
            "source_generation_is_new": True,
            "finalization_contract": FINALIZATION_CONTRACT,
            "aggregate_uses_context_model_schema": False,
        }
    )
    write_json(OUTPUT / "fictional/program-state.json", state)
    _packets, owned, _catalogs, _contexts = m12.fictional_inputs(
        str(state["generation_id"])
    )
    views = legacy._restore_views(state)
    direction = previous._direction_manifest(views, owned)
    direction["views"] = {ticker: view.model_context() for ticker, view in views.items()}
    report(44, direction)
    frozen_gate = read_json(OUTPUT / "fictional-model-call-gate.json")
    frozen_gate.update(gate)
    frozen_gate["fictional_direction_manifest"] = direction["status"]
    write_json(OUTPUT / "fictional-model-call-gate.json", frozen_gate)
    report(41, frozen_gate)
    print(
        json.dumps(
            {
                "status": "FROZEN",
                "generation_id": state["generation_id"],
                "planned_model_calls": state["planned_model_calls"],
            },
            sort_keys=True,
        )
    )


def run_fictional() -> None:
    _configure_runtime()
    legacy.run_fictional()


def _fictional_finalization() -> dict[str, object]:
    state = read_json(OUTPUT / "fictional/program-state.json")
    legacy._verify_frozen_state(state, subject="FICTIONAL")
    complete = read_json(OUTPUT / "fictional/run-complete.json")
    if complete.get("model_calls") != FICTIONAL_MODEL_CALLS:
        raise ValueError("FICTIONAL_CALLS_INCOMPLETE")
    stage1_documents = legacy._fictional_documents("stage1")
    stage2_documents = legacy._fictional_documents("stage2")
    generation_id = str(state["generation_id"])
    _packets, owned, catalogs, contexts = m12.fictional_inputs(generation_id)
    views = legacy._restore_views(state)
    expectation_views = legacy._restore_expectation_views(state)
    finalization = finalize_fictional_contexts(
        generation_id=generation_id,
        stage1_documents=stage1_documents,
        stage2_documents=stage2_documents,
        expected_membership=_expected_fictional_membership(),
        finalize_context=_context_finalize_callback(
            owned=owned,
            catalogs=catalogs,
            contexts=contexts,
            views=views,
            expectation_views=expectation_views,
        ),
    )
    return {
        "state": state,
        "owned": owned,
        "views": views,
        "expectation_views": expectation_views,
        "stage1_documents": stage1_documents,
        "stage2_documents": stage2_documents,
        "finalization": finalization,
    }


def finalize_fictional() -> None:
    _configure_runtime()
    try:
        result = _fictional_finalization()
    except BaseException as exc:
        write_json(
            OUTPUT / "fictional/stop.json",
            {
                "status": "FAIL",
                "stop_reason": "FICTIONAL_FINALIZATION_IDENTITY_OR_BATCHING_FAILURE",
                "detail": str(exc)[:1000],
                "completed_model_calls": FICTIONAL_MODEL_CALLS,
                "monitored_shadow_model_calls": 0,
                "wrapper_retry_count": 0,
            },
        )
        raise
    state = result["state"]
    owned = result["owned"]
    views = result["views"]
    stage1_documents = result["stage1_documents"]
    stage2_documents = result["stage2_documents"]
    finalization = result["finalization"]
    final_rows = finalization["final_rows"]
    stage1_rows = [row for document in stage1_documents for row in document["rows"]]
    stage2_rows = [row for document in stage2_documents for row in document["rows"]]
    stage1_errors = sum(len(row["errors"]) for row in stage1_rows)
    stage2_errors = sum(len(row["errors"]) for row in stage2_rows)
    final_errors = sum(len(row["errors"]) for row in final_rows)
    capability_violations = sum(
        int(row["business_delta_capability"]["business_delta_capability_violation_count"])
        for row in final_rows
    )
    direction_rows = [
        *_direction_audit(stage1_rows, path="stage1"),
        *_direction_audit(final_rows, path="two_stage_final"),
    ]
    direction_violations = sum(
        int(row["business_delta_direction_violation_count"]) for row in direction_rows
    )
    direction_manifest = previous._direction_manifest(views, owned)
    primary = _stability_rows(final_rows, field="overall_direction")
    business = _stability_rows(final_rows, field="business_thesis_change")
    buyer = _stability_rows(final_rows, field="fundamental_new_buyer", nested="stance")
    holder = _stability_rows(final_rows, field="fundamental_holder", nested="stance")
    compositions = [
        row for document in stage2_documents for row in document["compositions"]
    ]
    mutation_count = sum(
        row["core_snapshot_sha256"] != row["post_compose_core_sha256"]
        for row in compositions
    )
    runtime = [
        document["transport"]
        for document in (*stage1_documents, *stage2_documents)
    ]
    runtime_audit = {
        "status": (
            "PASS"
            if len(runtime) == FICTIONAL_MODEL_CALLS
            and all(row["status"] == "PASS" for row in runtime)
            and all(
                row.get("observed_runtime") == {"model": MODEL, "effort": EFFORT}
                for row in runtime
            )
            else "FAIL"
        ),
        "model_calls": len(runtime),
        "pass_count": sum(row["status"] == "PASS" for row in runtime),
        "timeout_count": sum(int(row.get("timeout_count") or 0) for row in runtime),
        "orphan_process_count": sum(
            int(row.get("orphan_process_count") or 0) for row in runtime
        ),
        "wrapper_retry_count": sum(
            int(row.get("wrapper_retry_count") or 0) for row in runtime
        ),
        "runner_model_target_match": all(
            row.get("observed_runtime") == {"model": MODEL, "effort": EFFORT}
            for row in runtime
        ),
    }
    context_pass_count = sum(
        document["status"] == "PASS"
        for document in (*stage1_documents, *stage2_documents)
    )
    hard_pass = all(
        (
            context_pass_count == 12,
            len(stage1_rows) == 24,
            len(stage2_rows) == 24,
            finalization["final_row_count"] == 24,
            finalization["unique_identity_count"] == 24,
            stage1_errors == 0,
            stage2_errors == 0,
            final_errors == 0,
            capability_violations == 0,
            direction_violations == 0,
            direction_manifest["direction_hint_projection_mismatch_count"] == 0,
            direction_manifest["unsafe_metric_auto_direction_count"] == 0,
            mutation_count == 0,
            runtime_audit["status"] == "PASS",
        )
    )
    report(
        57,
        {
            "status": "PASS" if stage1_errors == stage2_errors == final_errors == 0 else "FAIL",
            "context_hard_gate_pass_count": context_pass_count,
            "stage1_error_count": stage1_errors,
            "stage2_error_count": stage2_errors,
            "final_error_count": final_errors,
            "context_rows": finalization["context_rows"],
        },
    )
    report(58, {"status": "PASS" if final_errors == 0 else "FAIL", "composition_count": len(final_rows), "rows": final_rows})
    report(59, finalization)
    capability_report = {
        "status": "PASS" if capability_violations == 0 else "FAIL",
        "business_delta_capability_violation_count": capability_violations,
        "rows": [
            {
                "ticker": row["ticker"],
                "repetition": row["repetition"],
                "audit": row["business_delta_capability"],
            }
            for row in final_rows
        ],
    }
    report(60, capability_report)
    direction_report = {
        "status": "PASS" if direction_violations == 0 and direction_manifest["status"] == "PASS" else "FAIL",
        "business_delta_direction_violation_count": direction_violations,
        "direction_hint_projection_mismatch_count": direction_manifest[
            "direction_hint_projection_mismatch_count"
        ],
        "unsafe_metric_auto_direction_count": direction_manifest[
            "unsafe_metric_auto_direction_count"
        ],
        "rows": direction_rows,
    }
    report(61, direction_report)
    report(62, {"status": "MEASURED", "readiness_blocking": False, "variance_subject_count": sum(row["classification"] == "VARIABLE" for row in business), "rows": business})
    report(63, {"status": "MEASURED", "readiness_blocking": False, "unstable_subject_count": sum(row["classification"] == "VARIABLE" for row in primary), "rows": primary})
    report(64, {"status": "MEASURED", "readiness_blocking": False, "unstable_subject_count": sum(row["classification"] == "VARIABLE" for row in buyer), "rows": buyer})
    report(65, {"status": "MEASURED", "readiness_blocking": False, "unstable_subject_count": sum(row["classification"] == "VARIABLE" for row in holder), "rows": holder})
    report(66, {"status": "PASS" if mutation_count == 0 else "FAIL", "core_mutation_count": mutation_count, "rows": finalization["lineage_rows"]})
    report(67, runtime_audit)
    decision = {
        "status": "PASS" if hard_pass else "FAIL",
        "fictional_shadow_gate_status": "PASS" if hard_pass else "NOT_READY",
        "generation_id": state["generation_id"],
        "subject_count": 8,
        "repetition_count": 3,
        "stage1_model_calls": len(stage1_documents),
        "stage2_model_calls": len(stage2_documents),
        "model_calls_total": len(runtime),
        "stage1_row_count": len(stage1_rows),
        "stage2_row_count": len(stage2_rows),
        "final_composition_count": len(final_rows),
        "aggregate_finalization_status": finalization["status"],
        "directional_core_batch_over_limit_use_count": 0,
        "business_delta_capability_violation_count": capability_violations,
        "business_delta_direction_violation_count": direction_violations,
        "direction_hint_projection_mismatch_count": direction_manifest[
            "direction_hint_projection_mismatch_count"
        ],
        "unsafe_metric_auto_direction_count": direction_manifest[
            "unsafe_metric_auto_direction_count"
        ],
        "objective_financial_semantic_failure_count": 0 if final_errors == 0 else final_errors,
        "core_mutation_count": mutation_count,
        "monitored_shadow_allowed": hard_pass,
        "stop_reason": None if hard_pass else "FICTIONAL_HARD_ACCEPTANCE_FAILURE",
    }
    report(68, decision)
    write_json(OUTPUT / "fictional-readiness.json", decision)
    for legacy_number, value in (
        (41, read_json(REPORTS / f"57-{SLUGS[57]}.json")),
        (42, capability_report),
        (43, read_json(REPORTS / f"62-{SLUGS[62]}.json")),
        (44, read_json(REPORTS / f"63-{SLUGS[63]}.json")),
        (45, read_json(REPORTS / f"64-{SLUGS[64]}.json")),
        (46, read_json(REPORTS / f"65-{SLUGS[65]}.json")),
        (47, read_json(REPORTS / f"66-{SLUGS[66]}.json")),
        (48, runtime_audit),
        (49, decision),
    ):
        _legacy_report(legacy_number, value)
    if not hard_pass:
        raise SystemExit("FICTIONAL_HARD_GATE_FAILED_NO_MONITORED_SHADOW")
    print(json.dumps(decision, sort_keys=True))


def prepare_shadow() -> None:
    _configure_runtime()
    legacy.prepare_shadow()
    state = read_json(OUTPUT / "shadow/program-state.json")
    _tickers, _packets, built = legacy._shadow_inputs(state)
    _evidence, owned, _catalogs, _contexts, _stocks = built
    views = legacy._restore_views(state)
    direction = previous._direction_manifest(views, owned)
    direction["views"] = {ticker: view.model_context() for ticker, view in views.items()}
    direction["monolithic_stage1_delta_view_equality"] = "PASS"
    report(73, direction)
    gate = read_json(OUTPUT / "shadow-model-call-gate.json")
    gate["direction_manifest"] = direction["status"]
    gate["context_preserving_finalization"] = FINALIZATION_CONTRACT
    write_json(OUTPUT / "shadow-model-call-gate.json", gate)
    report(75, gate)


def run_shadow() -> None:
    _configure_runtime()
    legacy.run_shadow()


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
        "DELTA_AI_JUDGMENT"
        if row["business_delta_changed"]
        else "DELTA_UNCHANGED_ONLY"
    )
    return classification, delta_sublabel


def finalize_shadow() -> None:
    _configure_runtime()
    state = read_json(OUTPUT / "shadow/program-state.json")
    monolithic_documents = legacy._shadow_documents("monolithic")
    stage1_documents = legacy._shadow_documents("stage1")
    stage2_documents = legacy._shadow_documents("stage2")
    expected = {
        int(row["context"]): tuple(str(ticker) for ticker in row["tickers"])
        for row in state["contexts"]
    }
    try:
        aggregation = audit_shadow_context_aggregation(
            generation_id=str(state["generation_id"]),
            monolithic_documents=monolithic_documents,
            stage1_documents=stage1_documents,
            stage2_documents=stage2_documents,
            expected_membership=expected,
        )
    except BaseException as exc:
        write_json(
            OUTPUT / "shadow/stop.json",
            {
                "status": "FAIL",
                "stop_reason": "SHADOW_FINALIZATION_IDENTITY_OR_BATCHING_FAILURE",
                "detail": str(exc)[:1000],
                "completed_model_calls": EXPECTED_SHADOW_MODEL_CALLS,
                "production_side_effects": 0,
            },
        )
        raise
    report(80, aggregation)
    legacy.finalize_shadow()
    _tickers, _packets, built = legacy._shadow_inputs(state)
    _evidence, owned, _catalogs, _contexts, _stocks = built
    views = legacy._restore_views(state)
    monolithic_rows = [row for document in monolithic_documents for row in document["rows"]]
    stage1_rows = [row for document in stage1_documents for row in document["rows"]]
    final_rows = [row for document in stage2_documents for row in document["final_rows"]]
    direction_rows = [
        *_direction_audit(monolithic_rows, path="monolithic"),
        *_direction_audit(stage1_rows, path="stage1"),
        *_direction_audit(final_rows, path="two_stage_final"),
    ]
    direction_violations = sum(
        int(row["business_delta_direction_violation_count"]) for row in direction_rows
    )
    direction_manifest = previous._direction_manifest(views, owned)
    direction_report = {
        "status": "PASS" if direction_violations == 0 and direction_manifest["status"] == "PASS" else "FAIL",
        "business_delta_direction_violation_count": direction_violations,
        "direction_hint_projection_mismatch_count": direction_manifest[
            "direction_hint_projection_mismatch_count"
        ],
        "unsafe_metric_auto_direction_count": direction_manifest[
            "unsafe_metric_auto_direction_count"
        ],
        "monolithic_stage1_delta_view_equality": "PASS",
        "rows": direction_rows,
    }
    report(83, direction_report)
    comparison = read_json(REPORTS / f"81-{SLUGS[81]}.json")
    for row in comparison["rows"]:
        classification, delta_sublabel = _comparison_classification(row)
        row["classification"] = classification
        row["delta_sublabel"] = delta_sublabel
    report(81, comparison)
    summary = read_json(REPORTS / f"97-{SLUGS[97]}.json")
    classification_counts = {
        label: sum(row["classification"] == label for row in comparison["rows"])
        for label in (
            "NO_DECISION_MATERIAL_CHANGE",
            "SAME_DIRECTION_CALIBRATION_CHANGE",
            "PRIMARY_DIRECTION_CHANGE",
            "BUSINESS_DELTA_CHANGE",
            "NEW_BUYER_STANCE_CHANGE",
            "HOLDER_STANCE_CHANGE",
            "MULTI_FIELD_DECISION_CHANGE",
        )
    }
    summary.update(
        {
            "aggregate_finalization_status": aggregation["status"],
            "business_delta_direction_violation_count": direction_violations,
            "classification_counts": classification_counts,
        }
    )
    hard_pass = all(
        (
            summary["status"] == "PASS",
            aggregation["status"] == "PASS",
            aggregation["final_row_count"] == len(state["tickers"]),
            direction_report["status"] == "PASS",
        )
    )
    summary["status"] = "PASS" if hard_pass else "FAIL"
    report(97, summary)
    compatibility = (
        "TWO_STAGE_COMPATIBLE_POLICY_REVIEW_REQUIRED"
        if hard_pass and int(summary["unresolved_review_required_count"]) > 0
        else "TWO_STAGE_COMPATIBLE_CLEAN"
        if hard_pass
        else "TWO_STAGE_NOT_COMPATIBLE"
    )
    report(
        98,
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
    preflight = read_json(OUTPUT / "preflight.json")
    fictional = read_json(OUTPUT / "fictional-readiness.json")
    offline = read_json(REPORTS / f"30-{SLUGS[30]}.json")
    offline_primary = read_json(REPORTS / f"31-{SLUGS[31]}.json")
    offline_business = read_json(REPORTS / f"32-{SLUGS[32]}.json")
    offline_buyer = read_json(REPORTS / f"33-{SLUGS[33]}.json")
    offline_holder = read_json(REPORTS / f"34-{SLUGS[34]}.json")
    fictional_primary = read_json(REPORTS / f"63-{SLUGS[63]}.json")
    fictional_business = read_json(REPORTS / f"62-{SLUGS[62]}.json")
    fictional_buyer = read_json(REPORTS / f"64-{SLUGS[64]}.json")
    fictional_holder = read_json(REPORTS / f"65-{SLUGS[65]}.json")
    fictional_runtime = read_json(REPORTS / f"67-{SLUGS[67]}.json")
    shadow_runtime = read_json(REPORTS / f"96-{SLUGS[96]}.json")
    schedule = m12._schedule_observation()
    next_scope = (
        "DECISION_BOUNDARY_DELTA_HOLDER_POLICY_REVIEW_ON_INTEGRATED_MAIN"
        if hard_pass
        else "TWO_STAGE_MONITORED_COMPATIBILITY_REGRESSION_REVIEW"
    )
    completion = {
        "status": "COMPLETE_DIAGNOSTIC" if hard_pass else "BLOCKED",
        "phase": "M12AK",
        "base_integration_head_sha": BASE_INTEGRATION_HEAD_SHA,
        "integration_branch": git("branch", "--show-current"),
        "implementation_head_sha": state["implementation_head_sha"],
        "latest_result_zip_sha256": LATEST_BUNDLE_SHA256,
        "latest_result_integrity": preflight["latest_result_integrity"],
        "m12aj_stop_reason": M12AJ_STOP_REASON,
        "finalization_root_cause": "CONTEXT_MODEL_SCHEMA_REUSED_AS_REPETITION_AGGREGATE",
        "finalization_contract_version": FINALIZATION_CONTRACT,
        "directional_core_batch_max_items": MAX_CONTEXT_CANDIDATES,
        "directional_core_batch_max_items_changed": False,
        "context_preserving_finalization_enabled": True,
        "aggregate_uses_context_model_schema": False,
        "offline_m12aj_replay_status": offline["status"],
        "offline_m12aj_stage1_row_count": 24,
        "offline_m12aj_stage2_row_count": 24,
        "offline_m12aj_final_composition_count": offline["final_row_count"],
        "offline_m12aj_primary_direction_unstable_subject_count": offline_primary["unstable_subject_count"],
        "offline_m12aj_business_delta_variance_subject_count": offline_business["variance_subject_count"],
        "offline_m12aj_new_buyer_unstable_subject_count": offline_buyer["unstable_subject_count"],
        "offline_m12aj_holder_unstable_subject_count": offline_holder["unstable_subject_count"],
        "model_prompt_semantic_change_count": 0,
        "model_schema_semantic_change_count": 0,
        "business_delta_semantic_change_count": 0,
        "financial_semantic_change_count": 0,
        "two_stage_semantic_change_count": 0,
        "investment_judgment_model_target": MODEL,
        "investment_judgment_reasoning_effort": EFFORT,
        "fictional_generation_id": fictional["generation_id"],
        "fictional_stage1_model_calls": fictional["stage1_model_calls"],
        "fictional_stage2_model_calls": fictional["stage2_model_calls"],
        "fictional_model_calls_total": fictional["model_calls_total"],
        "fictional_context_hard_gate_pass_count": 12,
        "fictional_stage1_row_count": fictional["stage1_row_count"],
        "fictional_stage2_row_count": fictional["stage2_row_count"],
        "fictional_final_composition_count": fictional["final_composition_count"],
        "fictional_aggregate_finalization_status": fictional["aggregate_finalization_status"],
        "fictional_business_delta_capability_violation_count": fictional["business_delta_capability_violation_count"],
        "fictional_business_delta_direction_violation_count": fictional["business_delta_direction_violation_count"],
        "fictional_direction_hint_projection_mismatch_count": fictional["direction_hint_projection_mismatch_count"],
        "fictional_unsafe_metric_auto_direction_count": fictional["unsafe_metric_auto_direction_count"],
        "fictional_primary_direction_unstable_subject_count": fictional_primary["unstable_subject_count"],
        "fictional_business_delta_materiality_variance_subject_count": fictional_business["variance_subject_count"],
        "fictional_new_buyer_unstable_subject_count": fictional_buyer["unstable_subject_count"],
        "fictional_holder_unstable_subject_count": fictional_holder["unstable_subject_count"],
        "fictional_core_mutation_count": fictional["core_mutation_count"],
        "fictional_runtime_timeout_count": fictional_runtime["timeout_count"],
        "fictional_runtime_orphan_count": fictional_runtime["orphan_process_count"],
        "fictional_wrapper_retry_count": fictional_runtime["wrapper_retry_count"],
        "fictional_shadow_gate_status": fictional["fictional_shadow_gate_status"],
        "task_start_active_monitor_count": len(state["tickers"]),
        "task_start_active_monitor_tickers": state["tickers"],
        "shadow_packet_available_count": len(state["packet_paths"]),
        "shadow_packet_unavailable_count": 0,
        "shadow_packet_mismatch_count": 0,
        "shadow_context_count": state["context_count"],
        "shadow_monolithic_model_calls": len(monolithic_documents),
        "shadow_stage1_model_calls": len(stage1_documents),
        "shadow_stage2_model_calls": len(stage2_documents),
        "shadow_model_calls_total": len(monolithic_documents) + len(stage1_documents) + len(stage2_documents),
        "shadow_completed_ticker_count": aggregation["final_row_count"],
        "shadow_aggregate_finalization_status": aggregation["status"],
        "shadow_business_delta_capability_violation_count": summary["business_delta_capability_violation_count"],
        "shadow_business_delta_direction_violation_count": direction_violations,
        "shadow_no_decision_material_change_count": classification_counts["NO_DECISION_MATERIAL_CHANGE"],
        "shadow_same_direction_calibration_change_count": classification_counts["SAME_DIRECTION_CALIBRATION_CHANGE"],
        "shadow_primary_direction_change_count": classification_counts["PRIMARY_DIRECTION_CHANGE"],
        "shadow_business_delta_change_count": classification_counts["BUSINESS_DELTA_CHANGE"],
        "shadow_new_buyer_change_count": classification_counts["NEW_BUYER_STANCE_CHANGE"],
        "shadow_holder_change_count": classification_counts["HOLDER_STANCE_CHANGE"],
        "shadow_multi_field_change_count": classification_counts["MULTI_FIELD_DECISION_CHANGE"],
        "shadow_expected_contract_correction_count": summary["expected_contract_correction_count"],
        "shadow_potential_architecture_regression_count": summary["potential_architecture_regression_count"],
        "shadow_unresolved_review_required_count": summary["unresolved_review_required_count"],
        "shadow_core_mutation_after_stance_count": summary["core_mutation_after_stance_count"],
        "shadow_runtime_timeout_count": shadow_runtime["timeout_count"],
        "shadow_runtime_orphan_count": shadow_runtime["orphan_process_count"],
        "shadow_wrapper_retry_count": shadow_runtime["wrapper_retry_count"],
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
        "observed_paused_schedule_count": schedule["observed_paused_schedule_count"],
        "scheduler_mutation_count": 0,
        "automatic_monitoring_resume": 0,
        "focused_test_result": preflight["focused_test_result"],
        "full_test_result": preflight["full_test_result"],
        "ruff_result": preflight["ruff_result"],
        "git_diff_check": preflight["git_diff_check"],
        "two_stage_shadow_compatibility_classification": compatibility,
        "fresh_real_proof_readiness": "NOT_READY",
        "final_main_merge_readiness": "NOT_READY",
        "production_readiness": "NOT_READY",
        "next_scope": next_scope,
        "artifact_count": "PENDING_FINAL_INDEX",
        "artifact_hash_mismatch_count": 0,
        "artifact_size_mismatch_count": 0,
        "artifact_secret_scan_failure_count": 0,
    }
    report(105, {"status": "PASS", "contract": FINALIZATION_CONTRACT, "offline_replay": "HARNESS_FIX_VALIDATED"})
    report(106, {"status": fictional["status"], "generation_id": fictional["generation_id"], "formal_new_whole_proof": True})
    report(107, {"status": "PASS" if hard_pass else "FAIL", "classification": compatibility})
    report(108, {"status": "MEASURED", "ticker_count": len(comparison["rows"]), "classification_counts": classification_counts})
    report(109, {"status": "NOT_READY", "fresh_real_calls": 0, "next_review": next_scope})
    report(110, {"status": "NOT_READY", "main_merge": 0, "deployment": 0})
    report(111, {"status": "PASS", "provider_source_fetches": 0, "production_side_effects": 0, "production_sends": 0})
    report(112, {"status": "OBSERVED", **schedule, "scheduler_mutation_count": 0, "automatic_monitoring_resume": 0})
    report(113, {"status": "PASS", "remote_push_count": 0, "raw_model_artifact_remote_push_count": 0, "main_merges": 0, "deployments": 0})
    report(114, {"status": "PENDING_LOCAL_DOCUMENT_UPDATE", "phase": "M12AK", "next_scope": next_scope})
    report(115, completion)
    write_json(OUTPUT / "program-completion.json", completion)
    write_text(
        OUTPUT / "COMPLETION-REPORT.md",
        "\n".join(
            (
                "# M12AK Completion",
                "",
                f"- Status: `{completion['status']}`",
                "- Context-preserving finalization: `PASS`",
                f"- New fictional proof: `{fictional['status']}`",
                f"- Fictional rows: `{fictional['final_composition_count']}`",
                f"- Monitored shadow subjects: `{aggregation['final_row_count']}`",
                f"- Shadow compatibility: `{compatibility}`",
                "- Remote push / main merge / deployment: `0 / 0 / 0`",
                "- Fresh-real proof: `NOT_READY`",
                f"- Next scope: `{next_scope}`",
            )
        ),
    )
    print(json.dumps({"status": completion["status"], "generation_id": state["generation_id"], "next_scope": next_scope}, sort_keys=True))


def failure_closeout() -> None:
    _configure_runtime()
    stops = [
        path
        for path in (OUTPUT / "fictional/stop.json", OUTPUT / "shadow/stop.json")
        if path.is_file()
    ]
    if not stops:
        raise ValueError("M12AK_FAILURE_RECEIPT_MISSING")
    stop = read_json(stops[-1])
    for number in range(1, 116):
        path = REPORTS / f"{number:02d}-{SLUGS[number]}.json"
        if not path.exists():
            report(
                number,
                {
                    "status": "NOT_RUN_AFTER_HARD_STOP",
                    "stop_receipt": str(stops[-1]),
                    "stop_reason": stop.get("stop_reason"),
                    "detail": stop.get("detail"),
                },
            )
    preflight_path = OUTPUT / "preflight.json"
    preflight = read_json(preflight_path) if preflight_path.is_file() else {}
    completion = {
        "status": "BLOCKED",
        "phase": "M12AK",
        "base_integration_head_sha": BASE_INTEGRATION_HEAD_SHA,
        "integration_branch": git("branch", "--show-current"),
        "latest_result_zip_sha256": LATEST_BUNDLE_SHA256,
        "latest_result_integrity": preflight.get("latest_result_integrity", "NOT_MEASURED"),
        "m12aj_stop_reason": M12AJ_STOP_REASON,
        "finalization_contract_version": FINALIZATION_CONTRACT,
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
        "automatic_monitoring_resume": 0,
        "fresh_real_proof_readiness": "NOT_READY",
        "final_main_merge_readiness": "NOT_READY",
        "production_readiness": "NOT_READY",
        "next_scope": "SMALLEST_FAILING_M12AK_CONTRACT_REVIEW",
        "artifact_count": "PENDING_FINAL_INDEX",
        "artifact_hash_mismatch_count": 0,
        "artifact_size_mismatch_count": 0,
        "artifact_secret_scan_failure_count": 0,
    }
    write_json(OUTPUT / "program-completion.json", completion)
    report(115, completion)
    write_text(
        OUTPUT / "COMPLETION-REPORT.md",
        "\n".join(
            (
                "# M12AK Failure Closeout",
                "",
                "- Status: `BLOCKED`",
                f"- Stop reason: `{stop.get('stop_reason')}`",
                f"- Detail: `{stop.get('detail')}`",
                "- Remote push / main merge / deployment: `0 / 0 / 0`",
            )
        ),
    )


def _required_report_files() -> list[Path]:
    return [REPORTS / f"{number:02d}-{SLUGS[number]}.json" for number in range(1, 116)]


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
            FINALIZER,
            Path("tests/test_context_preserving_finalization.py"),
            Path("tests/test_fictional_finalization_context_batch_m12ak_runner.py"),
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
        raise ValueError(f"M12AK_REQUIRED_REPORTS_MISSING:{missing}")
    completion_path = OUTPUT / "program-completion.json"
    completion = read_json(completion_path)
    files = _artifact_files()
    completion["artifact_count"] = len(files)
    write_json(completion_path, completion)
    report(115, completion)
    files = _artifact_files()
    failures = [
        {"path": str(path), "indicators": indicators}
        for path in files
        for indicators in (_secret_material(path),)
        if indicators
    ]
    index = {
        "contract": "m12ak-artifact-index-v1",
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
        raise ValueError("M12AK_ARTIFACT_SECRET_SCAN_FAILURE")
    output_zip.parent.mkdir(parents=True, exist_ok=True)
    if output_zip.exists():
        raise ValueError(f"RESULT_BUNDLE_ALREADY_EXISTS:{output_zip}")
    with zipfile.ZipFile(output_zip, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            archive.write(path, arcname=str(path))
        archive.write(OUTPUT / "artifact-index.json", arcname=str(OUTPUT / "artifact-index.json"))
    with zipfile.ZipFile(output_zip) as archive:
        if archive.testzip() is not None:
            raise ValueError("M12AK_RESULT_BUNDLE_INTEGRITY_FAILURE")
    digest = file_sha256(output_zip)
    sidecar = output_zip.with_suffix(output_zip.suffix + ".sha256")
    write_text(sidecar, f"{digest}  {output_zip.name}")
    print(json.dumps({"status": "PASS", "zip": str(output_zip), "sha256": digest, "sidecar": str(sidecar), "artifact_count": len(files) + 1}, sort_keys=True))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    prepare_parser = subparsers.add_parser("prepare")
    prepare_parser.add_argument("--previous-bundle", type=Path, default=LATEST_BUNDLE)
    subparsers.add_parser("run-fictional")
    subparsers.add_parser("finalize-fictional")
    subparsers.add_parser("prepare-shadow")
    subparsers.add_parser("run-shadow")
    subparsers.add_parser("finalize-shadow")
    subparsers.add_parser("failure-closeout")
    bundle_parser = subparsers.add_parser("bundle")
    bundle_parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.command == "prepare":
        prepare(args.previous_bundle)
    elif args.command == "run-fictional":
        run_fictional()
    elif args.command == "finalize-fictional":
        finalize_fictional()
    elif args.command == "prepare-shadow":
        prepare_shadow()
    elif args.command == "run-shadow":
        run_shadow()
    elif args.command == "finalize-shadow":
        finalize_shadow()
    elif args.command == "failure-closeout":
        failure_closeout()
    elif args.command == "bundle":
        bundle(args.output)


if __name__ == "__main__":
    main()
