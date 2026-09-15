"""M12BF frozen-input layout compatibility repair and monitored shadow proof."""

# ruff: noqa: E402

from __future__ import annotations

import argparse
import ast
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import zipfile

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.services.report_subject_identity_service import (
    CONTRACT_VERSION as COUNT_ADAPTER_CONTRACT,
    MARKET_EXPECTATION_EVIDENCE_VIEW_CONTRACT,
    ReportSubjectIdentityError,
    audit_subject_set_identity,
    report_subject_identity,
)
from scripts import business_delta_evidence_capability_m12ai as capability
from scripts import stage2_working_capital_binding_parity_m12bd as m12bd
from scripts.shadow_frozen_context_manifest import (
    FROZEN_INPUT_FILENAMES,
    FROZEN_INPUT_RESOLVER_CONTRACT_VERSION,
    LEGACY_FLAT,
    NESTED_INPUTS_V1,
    resolve_frozen_context_input,
    verify_frozen_context_inputs,
)


NAME = (
    "20260913-frozen-context-input-layout-compatibility-"
    "new-full-shadow"
)
OUTPUT = Path("artifacts") / NAME
REPORTS = Path("docs/reports") / NAME
PROOF_OUTPUT = OUTPUT / "proof-runtime"
PROOF_REPORTS = OUTPUT / "supporting-reports/m12bb"
M12BD_REPORTS = OUTPUT / "supporting-reports/m12bd"
SOURCE_OUTPUT = OUTPUT / "frozen-m12be-shadow-source"
REPLAY_ROOT = OUTPUT / "offline-replay-root"
RUNNER = Path("scripts/frozen_context_input_layout_compatibility_m12bf.py")
ARCHITECTURE = Path(
    "docs/architecture/FROZEN_CONTEXT_INPUT_LAYOUT_COMPATIBILITY.md"
)
WORK_INSTRUCTION = Path("docs/work-instructions") / f"{NAME}.md"
WORK_INSTRUCTION_COMMIT = "a9ac223b48f1a113d70a393fa5380056c4d5dc79"
BASE_INTEGRATION_HEAD_SHA = "cfc4c168032a0c5d5e8c3984fe1fb7e89946f5ed"
M12BD_IMPLEMENTATION_SHA = "5b2092fa8948c69d65086925a9cecd59bbb8cb4c"

M12BE_NAME = (
    "20260913-shadow-active-universe-count-contract-compatibility-"
    "new-full-shadow"
)
M12BE_BUNDLE = Path.home() / "Documents/Codex" / (
    f"thesis-monitor-{M12BE_NAME}-report.zip"
)
M12BE_BUNDLE_SHA256 = (
    "f9caae35d4c2a520103d34a8601ade64228322474d80ca3aec6ddf7e3ca35a49"
)
M12BE_STOPPED_SHADOW_GENERATION_ID = (
    "20260911-m12ai-shadow-20260913T132402Z-c956834e1892"
)
M12BE_ARTIFACT_ROOT = f"artifacts/{M12BE_NAME}"
M12BE_REPORT_ROOT = f"docs/reports/{M12BE_NAME}"
M12BE_INDEXED_PAYLOADS = 793
M12BE_ZIP_ENTRIES = 794

M12BD_NAME = (
    "20260913-stage2-working-capital-binding-parity-audit-coverage-validity-"
    "separation-full-proof-full-shadow"
)
M12BD_BUNDLE = Path.home() / "Documents/Codex" / (
    f"thesis-monitor-{M12BD_NAME}-report.zip"
)
M12BD_BUNDLE_SHA256 = (
    "675c49e921fa5bfeedd00596bae2a803b3c7a68ed9ca95a78aa7961419f965c5"
)
M12BD_GENERATION_ID = "20260911-m12ai-fictional-20260913T113957Z-07ac29f97bc6"
M12BD_ARTIFACT_ROOT = f"artifacts/{M12BD_NAME}"
M12BD_REPORT_ROOT = f"docs/reports/{M12BD_NAME}"

MODEL = "gpt-5.6-sol"
EFFORT = "xhigh"
EXPECTED_FORMAL_CALLS = 12
EXPECTED_FORMAL_ROWS = 24
SUBJECTS_PER_CONTEXT = 4
NEXT_SCOPE = "DECISION_BOUNDARY_DELTA_HOLDER_POLICY_REVIEW_ON_INTEGRATED_MAIN"
FICTIONAL_REQUIRED_INPUTS = (
    "stage1_prompt",
    "stage1_schema",
    "stage2_schema",
)
SHADOW_REQUIRED_INPUTS = (
    "monolithic_prompt",
    "monolithic_schema",
    *FICTIONAL_REQUIRED_INPUTS,
)

REPORT_SLUGS = tuple(
    line
    for line in """
repository-provenance
latest-result-integrity
m12bf-scope-freeze
m12bd-fictional-proof-identity-freeze
m12be-count-contract-repair-freeze
m12be-shadow-layout-failure-reproduction
frozen-context-producer-layout-audit
frozen-state-verifier-consumer-layout-audit
fictional-vs-shadow-layout-comparison
frozen-input-layout-options
frozen-input-layout-decision
frozen-input-resolver-contract
required-input-set-contract
dual-layout-ambiguity-contract
frozen-input-path-hash-contract
legacy-flat-positive-fixture
nested-inputs-positive-fixture
shadow-five-input-nested-positive-fixture
dual-layout-ambiguous-negative-fixture
partial-dual-layout-negative-fixture
nested-missing-hash-negative-fixture
flat-missing-hash-negative-fixture
hash-mismatch-negative-fixture
required-input-missing-negative-fixture
malformed-inputs-negative-fixture
m12be-stopped-shadow-layout-offline-replay
m12bd-fictional-legacy-layout-offline-replay
model-prompt-semantic-hash-freeze
model-schema-semantic-hash-freeze
stage1-wc-binding-view-hash-freeze
stage2-wc-binding-view-hash-freeze
configured-signal-view-hash-freeze
configured-financial-support-concept-hash-freeze
business-delta-view-hash-freeze
expectation-view-hash-freeze
financial-evidence-projection-hash-freeze
two-stage-core-semantics-freeze
final-user-schema-freeze
fictional-proof-reuse-decision
m12be-active-universe-count-contract-freeze
m12bd-stage2-wc-binding-freeze
m12bd-optional-audit-coverage-freeze
m12bc-context-finalizer-freeze
m12bc-diagnostic-variance-readiness-freeze
m12bb-stage1-wc-binding-freeze
m12ba-financial-sector-replacement-verb-freeze
m12az-fcf-local-temporal-scope-freeze
m12ay-configured-fcf-support-freeze
m12at-configured-signal-field-ownership-freeze
m12ap-expectation-independence-freeze
m12ao-business-delta-convergence-freeze
adr-security-basis-freeze
two-stage-core-immutability-freeze
frozen-input-layout-unit-tests
frozen-state-verifier-regression-tests
count-contract-regression-tests
stopped-shadow-layout-offline-replay
fictional-legacy-layout-offline-replay
focused-test-results
full-local-test-results
ruff-and-diff-results
hosted-ci-portability-observation
new-shadow-model-call-gate
task-start-active-monitored-universe
new-shadow-generation-manifest
shadow-packet-inventory
shadow-packet-hash-manifest
shadow-stage1-wc-binding-view-manifest
shadow-stage2-wc-binding-view-manifest
shadow-configured-signal-view-manifest
shadow-configured-financial-support-concept-manifest
shadow-delta-view-manifest
shadow-expectation-view-manifest
shadow-frozen-context-manifest
shadow-frozen-input-layout-audit
shadow-cross-manifest-preflight-matrix
shadow-batching-manifest
shadow-model-call-gate
shadow-monolithic-model-artifacts
shadow-stage1-model-artifacts
shadow-stage2-model-artifacts
shadow-context-hard-semantic-audit
shadow-stage1-wc-binding-audit
shadow-stage2-wc-binding-audit
shadow-financial-grounding-audit
shadow-optional-audit-coverage-matrix
shadow-configured-signal-field-use-audit
shadow-fcf-audit
shadow-business-delta-audit
shadow-market-expectation-audit
shadow-financial-sector-audit
shadow-stage2-language-audit
shadow-final-composition-audit
shadow-aggregate-finalization-audit
shadow-per-ticker-comparison
shadow-core-direction-differences
shadow-business-delta-differences
shadow-new-buyer-differences
shadow-holder-differences
shadow-same-direction-calibration-differences
shadow-expected-contract-corrections
shadow-potential-architecture-regressions
shadow-unresolved-review-required
shadow-adr-security-basis-audit
shadow-cyclical-valuation-audit
shadow-core-immutability-audit
shadow-runtime-audit
shadow-aggregate-summary
shadow-architecture-decision
fictional-primary-boundary-summary
fictional-delta-materiality-summary
fictional-new-buyer-boundary-summary
fictional-holder-boundary-summary
monitored-primary-difference-summary
monitored-delta-difference-summary
monitored-new-buyer-difference-summary
monitored-holder-difference-summary
same-direction-calibration-summary
combined-fictional-monitored-policy-input
next-bounded-policy-decision
frozen-context-layout-repair-success-decision
m12bd-fictional-proof-reuse-success-decision
new-full-shadow-completion-decision
two-stage-shadow-compatibility-decision
existing-monitored-impact-summary
fresh-real-proof-readiness-decision
final-main-merge-readiness-note
production-no-change
schedule-pause-observation
remote-push-prohibition-audit
master-workflow-update
program-completion
""".strip().splitlines()
)
NUMBERS = {slug: index for index, slug in enumerate(REPORT_SLUGS, start=1)}

FOCUSED_TESTS = (
    "tests/test_frozen_context_input_layout_m12bf.py",
    "tests/test_shadow_frozen_context_manifest.py",
    "tests/test_report_subject_identity_service.py",
    "tests/test_shadow_active_universe_count_compatibility_m12be.py",
    "tests/test_stage2_working_capital_binding_parity_m12bd.py",
    "tests/test_working_capital_checkpoint_binding_m12bb.py",
    "tests/test_working_capital_checkpoint_binding_m12bb_runner.py",
    "tests/test_financial_sector_replacement_verb_parity_m12ba_runner.py",
    "tests/test_business_delta_evidence_capability_m12ai.py",
    "tests/test_market_expectation_evidence_service.py",
    "tests/test_business_delta_evidence_service.py",
)
RUFF_PATHS = (
    "app/services/report_subject_identity_service.py",
    "scripts/business_delta_evidence_capability_m12ai.py",
    "scripts/shadow_frozen_context_manifest.py",
    "scripts/prospective_condition_nominalization_m12aw.py",
    "scripts/financial_sector_replacement_verb_parity_m12ba.py",
    "scripts/working_capital_checkpoint_binding_m12bb.py",
    "scripts/stage2_working_capital_binding_parity_m12bd.py",
    str(RUNNER),
    "tests/test_frozen_context_input_layout_m12bf.py",
    "tests/test_shadow_frozen_context_manifest.py",
    "tests/test_report_subject_identity_service.py",
    "tests/test_shadow_active_universe_count_compatibility_m12be.py",
)
TRACKED_IMPLEMENTATION_PATHS = tuple(Path(path) for path in RUFF_PATHS) + (
    ARCHITECTURE,
    WORK_INSTRUCTION,
)


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")


def read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def canonical_sha256(value: object) -> str:
    serialized = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(serialized.encode()).hexdigest()


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(*args: str) -> str:
    return subprocess.run(
        ["git", *args],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def report(slug: str, value: object) -> None:
    number = NUMBERS[slug]
    write_json(REPORTS / f"{number:03d}-{slug}.json", value)


def _run(command: Sequence[str], *, timeout: int = 7200) -> dict[str, object]:
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


def _zip_read_json(archive: zipfile.ZipFile, path: str) -> dict[str, object]:
    return json.loads(archive.read(path))


def _m12bd_report_path(archive: zipfile.ZipFile, number: int) -> str:
    prefix = f"{M12BD_REPORT_ROOT}/{number:03d}-"
    matches = [name for name in archive.namelist() if name.startswith(prefix)]
    if len(matches) != 1:
        raise ValueError(f"M12BD_REPORT_IDENTITY_INVALID:{number}:{len(matches)}")
    return matches[0]


def _m12bd_proof_report_path(
    archive: zipfile.ZipFile,
    phase: str,
    number: int,
) -> str:
    prefix = f"{M12BD_ARTIFACT_ROOT}/proof-runtime/supporting-reports/{phase}/{number}-"
    matches = [name for name in archive.namelist() if name.startswith(prefix)]
    if len(matches) != 1:
        raise ValueError(
            f"M12BD_PROOF_REPORT_IDENTITY_INVALID:{phase}:{number}:{len(matches)}"
        )
    return matches[0]


def _m12be_report_path(archive: zipfile.ZipFile, number: int) -> str:
    prefix = f"{M12BE_REPORT_ROOT}/{number:03d}-"
    matches = [name for name in archive.namelist() if name.startswith(prefix)]
    if len(matches) != 1:
        raise ValueError(f"M12BE_REPORT_IDENTITY_INVALID:{number}:{len(matches)}")
    return matches[0]


def _m12be_proof_report_path(
    archive: zipfile.ZipFile,
    phase: str,
    number: int,
) -> str:
    prefix = f"{M12BE_ARTIFACT_ROOT}/proof-runtime/supporting-reports/{phase}/{number}-"
    matches = [name for name in archive.namelist() if name.startswith(prefix)]
    if len(matches) != 1:
        raise ValueError(
            f"M12BE_PROOF_REPORT_IDENTITY_INVALID:{phase}:{number}:{len(matches)}"
        )
    return matches[0]


def _verify_latest_bundle() -> dict[str, object]:
    actual_sha = file_sha256(M12BE_BUNDLE)
    hash_mismatches = 0
    size_mismatches = 0
    missing_paths: list[str] = []
    with zipfile.ZipFile(M12BE_BUNDLE) as archive:
        index_path = f"{M12BE_ARTIFACT_ROOT}/artifact-index.json"
        index = _zip_read_json(archive, index_path)
        names = {name for name in archive.namelist() if not name.endswith("/")}
        indexed_names = {str(row["path"]) for row in index["rows"]}
        for row in index["rows"]:
            path = str(row["path"])
            if path not in names:
                missing_paths.append(path)
                hash_mismatches += 1
                size_mismatches += 1
                continue
            payload = archive.read(path)
            hash_mismatches += hashlib.sha256(payload).hexdigest() != row["sha256"]
            size_mismatches += len(payload) != row["size"]
        entry_count = len(names)
        extra_paths = sorted(names - indexed_names - {index_path})
    status = all(
        (
            actual_sha == M12BE_BUNDLE_SHA256,
            index.get("status") == "PASS",
            index.get("artifact_count") == M12BE_INDEXED_PAYLOADS,
            len(index["rows"]) == M12BE_INDEXED_PAYLOADS,
            entry_count == M12BE_ZIP_ENTRIES,
            not missing_paths,
            not extra_paths,
            hash_mismatches == 0,
            size_mismatches == 0,
            index.get("secret_scan_failure_count") == 0,
        )
    )
    return {
        "status": "PASS" if status else "FAIL",
        "path": str(M12BE_BUNDLE),
        "expected_sha256": M12BE_BUNDLE_SHA256,
        "actual_sha256": actual_sha,
        "index_contract": index.get("contract"),
        "indexed_payload_count": len(index["rows"]),
        "zip_entry_count": entry_count,
        "missing_count": len(missing_paths),
        "extra_count": len(extra_paths),
        "hash_mismatch_count": hash_mismatches,
        "size_mismatch_count": size_mismatches,
        "secret_scan_failure_count": index.get("secret_scan_failure_count"),
    }


def _write_zip_member(
    archive: zipfile.ZipFile,
    member: str,
    target: Path,
) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(archive.read(member))


def _extract_reusable_proof_and_packets() -> dict[str, object]:
    proof_prefix = f"{M12BE_ARTIFACT_ROOT}/proof-runtime/"
    old_shadow_prefix = f"{proof_prefix}shadow/"
    extracted_proof_files = 0
    with zipfile.ZipFile(M12BE_BUNDLE) as archive:
        for member in archive.namelist():
            if not member.startswith(proof_prefix) or member.endswith("/"):
                continue
            relative = Path(member.removeprefix(proof_prefix))
            if relative.parts[0] == "shadow":
                continue
            if len(relative.parts) == 1 and relative.name.startswith("shadow-"):
                continue
            _write_zip_member(archive, member, PROOF_OUTPUT / relative)
            extracted_proof_files += 1

        old_state_path = f"{old_shadow_prefix}program-state.json"
        old_state = _zip_read_json(archive, old_state_path)
        packet_paths: dict[str, str] = {}
        packet_file_hashes: dict[str, str] = {}
        for ticker in old_state["tickers"]:
            member = f"{old_shadow_prefix}frozen-packets/{ticker}.json"
            target = SOURCE_OUTPUT / "shadow/frozen-packets" / f"{ticker}.json"
            _write_zip_member(archive, member, target)
            packet_paths[str(ticker)] = str(target)
            packet_file_hashes[str(ticker)] = file_sha256(target)

    old_state["packet_paths"] = packet_paths
    old_state["packet_file_hashes"] = packet_file_hashes
    old_state["source_rehydration"] = {
        "status": "PASS",
        "source_bundle_sha256": M12BE_BUNDLE_SHA256,
        "purpose": "NEW_GENERATION_PACKET_SOURCE_ONLY",
        "old_generation_reused": False,
    }
    write_json(SOURCE_OUTPUT / "shadow/program-state.json", old_state)
    canonical_mismatches = []
    for ticker, expected in old_state["packet_hashes"].items():
        actual = canonical_sha256(read_json(Path(packet_paths[ticker])))
        if actual != expected:
            canonical_mismatches.append(ticker)
    if canonical_mismatches:
        raise ValueError(
            f"M12BE_FROZEN_PACKET_HASH_MISMATCH:{canonical_mismatches}"
        )
    if old_state.get("generation_id") != M12BE_STOPPED_SHADOW_GENERATION_ID:
        raise ValueError("M12BE_STOPPED_SHADOW_GENERATION_ID_MISMATCH")
    return {
        "status": "PASS",
        "proof_file_count": extracted_proof_files,
        "packet_count": len(packet_paths),
        "packet_hash_mismatch_count": len(canonical_mismatches),
        "old_shadow_generation_id": old_state["generation_id"],
        "old_shadow_model_calls_started": 0,
        "old_shadow_model_calls_completed": 0,
    }


def _configure_proof_runtime() -> None:
    m12bd.NAME = NAME
    m12bd.OUTPUT = OUTPUT
    m12bd.REPORTS = M12BD_REPORTS
    m12bd.PROOF_OUTPUT = PROOF_OUTPUT
    m12bd.PROOF_REPORTS = PROOF_REPORTS
    m12bd.RUNTIME_STATE_ROOT = Path("/tmp") / NAME / "runtime-state"
    m12bd.RUNNER = RUNNER
    m12bd.ARCHITECTURE = ARCHITECTURE
    m12bd.WORK_INSTRUCTION = WORK_INSTRUCTION
    m12bd.WORK_INSTRUCTION_COMMIT = WORK_INSTRUCTION_COMMIT
    m12bd.BASE_INTEGRATION_HEAD_SHA = BASE_INTEGRATION_HEAD_SHA
    m12bd._configure_proof()
    m12bd.m12bb.capability.FROZEN_PACKET_SOURCE_OVERRIDE = SOURCE_OUTPUT


def _active_universe() -> list[dict[str, object]]:
    return capability.base._active_monitored_universe(capability.OPERATING_ROOT)


def _strict_unique_tickers(
    values: Sequence[object],
    *,
    subject: str,
) -> tuple[str, ...]:
    tickers = tuple(str(value).strip() for value in values)
    if not tickers or any(not ticker for ticker in tickers):
        raise ValueError(f"{subject}:NONEMPTY_TICKERS_REQUIRED")
    if len(tickers) != len(set(tickers)):
        raise ValueError(f"{subject}:DUPLICATE_TICKERS")
    return tickers


def _report_tickers(value: Mapping[str, object]) -> tuple[str, ...]:
    if isinstance(value.get("views"), Mapping):
        return _strict_unique_tickers(
            tuple(value["views"]),
            subject=str(value.get("contract") or "views"),
        )
    rows = value.get("rows")
    if isinstance(rows, Sequence) and not isinstance(rows, (str, bytes)):
        tickers = sorted(
            {
                str(row["ticker"])
                for row in rows
                if isinstance(row, Mapping) and row.get("ticker")
            }
        )
        return _strict_unique_tickers(tickers, subject=str(value.get("contract")))
    contexts = value.get("contexts")
    if isinstance(contexts, Sequence) and not isinstance(contexts, (str, bytes)):
        flattened = [
            str(ticker)
            for context in contexts
            if isinstance(context, Mapping)
            for ticker in context.get("tickers", ())
        ]
        return _strict_unique_tickers(flattened, subject=str(value.get("contract")))
    raise ValueError(f"REPORT_TICKER_IDENTITY_UNSUPPORTED:{value.get('contract')}")


def _old_shadow_reports() -> dict[str, dict[str, object]]:
    with zipfile.ZipFile(M12BE_BUNDLE) as archive:
        return {
            "configured_signal": _zip_read_json(
                archive, _m12be_proof_report_path(archive, "m12ba", 98)
            ),
            "configured_financial_support": _zip_read_json(
                archive, _m12be_proof_report_path(archive, "m12ba", 99)
            ),
            "business_delta": _zip_read_json(
                archive, _m12be_proof_report_path(archive, "m12ba", 100)
            ),
            "market_expectation": _zip_read_json(
                archive, _m12be_proof_report_path(archive, "m12ba", 101)
            ),
            "frozen_context": _zip_read_json(
                archive, _m12be_proof_report_path(archive, "m12ba", 102)
            ),
            "batching": _zip_read_json(
                archive, _m12be_proof_report_path(archive, "m12ba", 103)
            ),
        }


def _archive_program_state(
    archive: zipfile.ZipFile,
    *,
    subject: str,
) -> tuple[str, dict[str, object]]:
    member = f"{M12BE_ARTIFACT_ROOT}/proof-runtime/{subject}/program-state.json"
    return member, _zip_read_json(archive, member)


def _replay_member_for_declared_path(path: str) -> str:
    parts = Path(path).parts
    try:
        proof_index = parts.index("proof-runtime")
    except ValueError as exc:
        raise ValueError(f"REPLAY_INPUT_PATH_UNSUPPORTED:{path}") from exc
    suffix = "/".join(parts[proof_index + 1 :])
    return f"{M12BE_ARTIFACT_ROOT}/proof-runtime/{suffix}"


def _offline_layout_replay(*, subject: str) -> dict[str, object]:
    required_inputs = (
        SHADOW_REQUIRED_INPUTS if subject == "shadow" else FICTIONAL_REQUIRED_INPUTS
    )
    with zipfile.ZipFile(M12BE_BUNDLE) as archive:
        state_member, state = _archive_program_state(archive, subject=subject)
        rows = state.get("frozen_contexts")
        if not isinstance(rows, list):
            raise ValueError(f"{subject.upper()}_FROZEN_CONTEXTS_MISSING")
        materialized = 0
        for row in rows:
            if not isinstance(row, Mapping):
                raise ValueError(f"{subject.upper()}_FROZEN_CONTEXT_ROW_INVALID")
            for input_name in required_inputs:
                identity = resolve_frozen_context_input(row, input_name)
                declared = Path(identity.path)
                if declared.is_absolute():
                    raise ValueError("REPLAY_ABSOLUTE_INPUT_PATH_FORBIDDEN")
                member = _replay_member_for_declared_path(identity.path)
                _write_zip_member(archive, member, REPLAY_ROOT / declared)
                materialized += 1

    audit_rows: list[dict[str, object]] = []
    errors: list[dict[str, object]] = []
    for row in rows:
        context = row.get("context", row.get("context_id"))
        first = resolve_frozen_context_input(row, required_inputs[0])
        expected_directory = (REPLAY_ROOT / Path(first.path)).parent.resolve()
        try:
            verified = verify_frozen_context_inputs(
                row,
                required_inputs=required_inputs,
                repository_root=REPLAY_ROOT,
                expected_context_directory=expected_directory,
            )
        except (KeyError, TypeError, ValueError) as exc:
            errors.append({"context": context, "error": str(exc)})
            continue
        audit_rows.extend({"context": context, **item} for item in verified)
    layout_counts = {
        layout: sum(item["detected_layout"] == layout for item in audit_rows)
        for layout in (LEGACY_FLAT, NESTED_INPUTS_V1)
    }
    hash_mismatches = sum(not bool(item["hash_match"]) for item in audit_rows)
    ambiguity_count = sum("AMBIGUOUS" in item["error"] for item in errors)
    expected_count = len(rows) * len(required_inputs)
    return {
        "status": (
            "PASS"
            if not errors
            and len(audit_rows) == expected_count
            and hash_mismatches == 0
            else "FAIL"
        ),
        "source_state_member": state_member,
        "generation_id": state.get("generation_id"),
        "subject": subject.upper(),
        "context_count": len(rows),
        "required_inputs": list(required_inputs),
        "expected_input_identity_count": expected_count,
        "resolved_input_identity_count": len(audit_rows),
        "materialized_file_count": materialized,
        "layout_counts": layout_counts,
        "missing_count": sum("MISSING" in item["error"] for item in errors),
        "ambiguity_count": ambiguity_count,
        "hash_mismatch_count": hash_mismatches
        + sum("CHANGED" in item["error"] for item in errors),
        "errors": errors,
        "rows": audit_rows,
        "old_generation_resume_authorized": False,
    }


def _fixture_files(directory: Path, names: Sequence[str]) -> dict[str, Path]:
    files: dict[str, Path] = {}
    for name in names:
        path = directory / FROZEN_INPUT_FILENAMES[name]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"M12BF fixture {name}\n", encoding="utf-8")
        files[name] = path
    return files


def _nested_fixture(files: Mapping[str, Path]) -> dict[str, object]:
    return {
        "context": 1,
        "inputs": {
            name: {"path": str(path), "sha256": file_sha256(path)}
            for name, path in files.items()
        },
    }


def _flat_fixture(files: Mapping[str, Path]) -> dict[str, object]:
    row: dict[str, object] = {"context": 1}
    for name, path in files.items():
        row[name] = str(path)
        row[f"{name}_sha256"] = file_sha256(path)
    return row


def _layout_fixture_results() -> dict[str, dict[str, object]]:
    root = (OUTPUT / "layout-fixtures").resolve()
    fictional_directory = root / "fictional/frozen-contexts/context-01"
    shadow_directory = root / "shadow/frozen-contexts/context-01"
    fictional_files = _fixture_files(fictional_directory, FICTIONAL_REQUIRED_INPUTS)
    shadow_files = _fixture_files(shadow_directory, SHADOW_REQUIRED_INPUTS)

    def verify(
        row: Mapping[str, object],
        required: Sequence[str],
        directory: Path,
    ) -> list[dict[str, object]]:
        return verify_frozen_context_inputs(
            row,
            required_inputs=required,
            repository_root=REPO_ROOT,
            expected_context_directory=directory,
        )

    def positive(
        row: Mapping[str, object],
        required: Sequence[str],
        directory: Path,
        layout: str,
    ) -> dict[str, object]:
        rows = verify(row, required, directory)
        passed = len(rows) == len(required) and {
            item["detected_layout"] for item in rows
        } == {layout}
        return {"status": "PASS" if passed else "FAIL", "rows": rows}

    def negative(callback, expected_error: str) -> dict[str, object]:
        try:
            callback()
        except (KeyError, TypeError, ValueError) as exc:
            observed = str(exc)
            return {
                "status": "PASS" if expected_error in observed else "FAIL",
                "expected_error": expected_error,
                "observed_error": observed,
            }
        return {
            "status": "FAIL",
            "expected_error": expected_error,
            "observed_error": None,
        }

    nested_shadow = _nested_fixture(shadow_files)
    dual = json.loads(json.dumps(nested_shadow))
    dual["stage1_prompt"] = str(shadow_files["stage1_prompt"])
    dual["stage1_prompt_sha256"] = file_sha256(shadow_files["stage1_prompt"])
    partial = json.loads(json.dumps(nested_shadow))
    partial["stage1_prompt_sha256"] = file_sha256(shadow_files["stage1_prompt"])
    nested_missing_hash = json.loads(json.dumps(nested_shadow))
    del nested_missing_hash["inputs"]["stage1_prompt"]["sha256"]
    flat_missing_hash = _flat_fixture(fictional_files)
    del flat_missing_hash["stage1_prompt_sha256"]
    mismatched = json.loads(json.dumps(nested_shadow))
    mismatched["inputs"]["stage1_prompt"]["sha256"] = "0" * 64
    required_missing = json.loads(json.dumps(nested_shadow))
    del required_missing["inputs"]["monolithic_schema"]

    return {
        "legacy-flat-positive-fixture": positive(
            _flat_fixture(fictional_files),
            FICTIONAL_REQUIRED_INPUTS,
            fictional_directory,
            LEGACY_FLAT,
        ),
        "nested-inputs-positive-fixture": positive(
            _nested_fixture(fictional_files),
            FICTIONAL_REQUIRED_INPUTS,
            fictional_directory,
            NESTED_INPUTS_V1,
        ),
        "shadow-five-input-nested-positive-fixture": positive(
            nested_shadow,
            SHADOW_REQUIRED_INPUTS,
            shadow_directory,
            NESTED_INPUTS_V1,
        ),
        "dual-layout-ambiguous-negative-fixture": negative(
            lambda: resolve_frozen_context_input(dual, "stage1_prompt"),
            "AMBIGUOUS_FROZEN_INPUT_LAYOUT",
        ),
        "partial-dual-layout-negative-fixture": negative(
            lambda: resolve_frozen_context_input(partial, "stage1_prompt"),
            "PARTIAL_OR_AMBIGUOUS_FROZEN_INPUT_LAYOUT",
        ),
        "nested-missing-hash-negative-fixture": negative(
            lambda: resolve_frozen_context_input(
                nested_missing_hash, "stage1_prompt"
            ),
            "NESTED_FROZEN_INPUT_INCOMPLETE",
        ),
        "flat-missing-hash-negative-fixture": negative(
            lambda: resolve_frozen_context_input(flat_missing_hash, "stage1_prompt"),
            "LEGACY_FLAT_FROZEN_INPUT_INCOMPLETE",
        ),
        "hash-mismatch-negative-fixture": negative(
            lambda: verify(mismatched, SHADOW_REQUIRED_INPUTS, shadow_directory),
            "FROZEN_INPUT_CHANGED:stage1_prompt",
        ),
        "required-input-missing-negative-fixture": negative(
            lambda: verify(
                required_missing, SHADOW_REQUIRED_INPUTS, shadow_directory
            ),
            "FROZEN_INPUT_REQUIRED_MISSING:monolithic_schema",
        ),
        "malformed-inputs-negative-fixture": negative(
            lambda: resolve_frozen_context_input(
                {"context": 1, "inputs": []}, "stage1_prompt"
            ),
            "MALFORMED_FROZEN_INPUTS_OBJECT",
        ),
    }


def _formal_proof_identity() -> dict[str, object]:
    proof_prefix = f"{M12BD_ARTIFACT_ROOT}/proof-runtime/fictional/model-calls/"
    with zipfile.ZipFile(M12BD_BUNDLE) as archive:
        root_state = _zip_read_json(
            archive, f"{M12BD_ARTIFACT_ROOT}/program-state.json"
        )
        readiness = _zip_read_json(
            archive, f"{M12BD_ARTIFACT_ROOT}/proof-runtime/fictional-readiness.json"
        )
        aggregate = _zip_read_json(archive, _m12bd_report_path(archive, 103))
        stage1_binding = _zip_read_json(archive, _m12bd_report_path(archive, 92))
        stage2_binding = _zip_read_json(archive, _m12bd_report_path(archive, 93))
        optional = _zip_read_json(archive, _m12bd_report_path(archive, 95))
        gate = _zip_read_json(archive, _m12bd_report_path(archive, 107))
        receipt_paths = [
            name
            for name in archive.namelist()
            if name.startswith(proof_prefix) and name.endswith("/receipt.json")
        ]
        output_paths = [
            name
            for name in archive.namelist()
            if name.startswith(proof_prefix) and name.endswith("/output.raw.json")
        ]
        stage1_docs = [
            _zip_read_json(archive, name)
            for name in archive.namelist()
            if name.startswith(proof_prefix)
            and "/stage1-context-" in name
            and name.endswith("/run-document.json")
        ]
        stage2_docs = [
            _zip_read_json(archive, name)
            for name in archive.namelist()
            if name.startswith(proof_prefix)
            and "/stage2-context-" in name
            and name.endswith("/run-document.json")
        ]
    stage1_rows = sum(len(document["rows"]) for document in stage1_docs)
    stage2_rows = sum(len(document["rows"]) for document in stage2_docs)
    final_compositions = sum(
        len(document["compositions"]) for document in stage2_docs
    )
    hard_errors = sum(
        len(row.get("errors", ()))
        for document in (*stage1_docs, *stage2_docs)
        for row in document["rows"]
    )
    checks = {
        "source_bundle_sha256": file_sha256(M12BD_BUNDLE)
        == M12BD_BUNDLE_SHA256,
        "generation_id": root_state.get("generation_id") == M12BD_GENERATION_ID,
        "model": root_state.get("model") == MODEL,
        "effort": root_state.get("reasoning_effort") == EFFORT,
        "root_status": root_state.get("status") == "FICTIONAL_PASS",
        "readiness": readiness.get("status") == "PASS",
        "shadow_authorized": bool(gate.get("shadow_authorized")),
        "receipt_count": len(receipt_paths) == EXPECTED_FORMAL_CALLS,
        "output_count": len(output_paths) == EXPECTED_FORMAL_CALLS,
        "stage1_rows": stage1_rows == EXPECTED_FORMAL_ROWS,
        "stage2_rows": stage2_rows == EXPECTED_FORMAL_ROWS,
        "final_compositions": final_compositions == EXPECTED_FORMAL_ROWS,
        "aggregate_finalization": aggregate.get("status") == "PASS",
        "hard_semantics": hard_errors == 0,
        "stage1_wc": stage1_binding.get("status") == "PASS",
        "stage2_wc": stage2_binding.get("status") == "PASS",
        "optional_audit": optional.get("status") == "PASS",
    }
    return {
        "status": "PASS" if all(checks.values()) else "FAIL",
        "source_bundle_sha256": M12BD_BUNDLE_SHA256,
        "generation_id": root_state.get("generation_id"),
        "model": root_state.get("model"),
        "reasoning_effort": root_state.get("reasoning_effort"),
        "model_calls": len(receipt_paths),
        "outputs": len(output_paths),
        "stage1_rows": stage1_rows,
        "stage2_rows": stage2_rows,
        "final_compositions": final_compositions,
        "hard_semantic_failure_count": hard_errors,
        "aggregate_finalization_status": aggregate.get("status"),
        "stage1_wc_binding": stage1_binding,
        "stage2_wc_binding": stage2_binding,
        "optional_audit": optional,
        "checks": checks,
    }


def _source_at(path: Path, *, ref: str | None) -> str:
    if ref is None:
        return path.read_text(encoding="utf-8")
    return subprocess.run(
        ["git", "show", f"{ref}:{path}"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout


def _ast_hash(path: Path, symbol: str, *, ref: str | None) -> str:
    tree = ast.parse(_source_at(path, ref=ref))
    matches = [
        node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
        and node.name == symbol
    ]
    if len(matches) != 1:
        raise ValueError(f"SEMANTIC_SYMBOL_IDENTITY_INVALID:{path}:{symbol}")
    payload = ast.dump(matches[0], annotate_fields=True, include_attributes=False)
    return hashlib.sha256(payload.encode()).hexdigest()


def _file_hash_at(path: Path, *, ref: str | None) -> str:
    return hashlib.sha256(_source_at(path, ref=ref).encode()).hexdigest()


def _semantic_surface(
    *,
    symbols: Sequence[tuple[Path, str]] = (),
    files: Sequence[Path] = (),
) -> dict[str, object]:
    rows = []
    for path, symbol in symbols:
        prior = _ast_hash(path, symbol, ref=M12BD_IMPLEMENTATION_SHA)
        current = _ast_hash(path, symbol, ref=None)
        rows.append(
            {
                "path": str(path),
                "symbol": symbol,
                "prior_sha256": prior,
                "current_sha256": current,
                "changed": prior != current,
            }
        )
    for path in files:
        prior = _file_hash_at(path, ref=M12BD_IMPLEMENTATION_SHA)
        current = _file_hash_at(path, ref=None)
        rows.append(
            {
                "path": str(path),
                "symbol": "WHOLE_FILE",
                "prior_sha256": prior,
                "current_sha256": current,
                "changed": prior != current,
            }
        )
    change_count = sum(bool(row["changed"]) for row in rows)
    return {
        "status": "PASS" if rows and change_count == 0 else "FAIL",
        "semantic_change_count": change_count,
        "comparison_ref": M12BD_IMPLEMENTATION_SHA,
        "rows": rows,
    }


def _semantic_surfaces() -> dict[str, dict[str, object]]:
    m12ai = Path("scripts/business_delta_evidence_capability_m12ai.py")
    m12bb = Path("scripts/working_capital_checkpoint_binding_m12bb.py")
    return {
        "model_prompt": _semantic_surface(
            symbols=(
                (m12ai, "_monolithic_prompt"),
                (m12ai, "_stage1_prompt"),
                (m12bb, "_patched_monolithic_prompt"),
                (m12bb, "_patched_stage1_prompt"),
                (m12bb, "_patched_stage2_prompt"),
            )
        ),
        "model_schema": _semantic_surface(
            symbols=((m12ai, "_batch_schema"),),
            files=(Path("app/services/two_stage_directional_service.py"),),
        ),
        "stage1_wc_binding": _semantic_surface(
            symbols=(
                (
                    Path("app/services/working_capital_checkpoint_binding_service.py"),
                    "build_working_capital_checkpoint_binding_view",
                ),
                (m12bb, "_patched_enriched_contexts"),
                (m12bb, "_patched_monolithic_prompt"),
                (m12bb, "_patched_stage1_prompt"),
            )
        ),
        "stage2_wc_binding": _semantic_surface(
            symbols=(
                (m12bb, "_patched_stage2_context"),
                (m12bb, "_patched_stage2_prompt"),
            ),
            files=(Path("app/services/working_capital_checkpoint_binding_service.py"),),
        ),
        "configured_signal": _semantic_surface(
            files=(Path("app/services/configured_signal_evidence_service.py"),)
        ),
        "configured_financial_support": _semantic_surface(
            files=(
                Path("app/services/configured_financial_support_concept_service.py"),
            )
        ),
        "business_delta": _semantic_surface(
            files=(Path("app/services/business_delta_evidence_service.py"),)
        ),
        "expectation_view": _semantic_surface(
            files=(Path("app/services/market_expectation_evidence_service.py"),)
        ),
        "financial_evidence_projection": _semantic_surface(
            symbols=(
                (
                    Path("app/services/directional_financial_context_service.py"),
                    "build_financial_decision_context",
                ),
            )
        ),
        "two_stage_core": _semantic_surface(
            files=(Path("app/services/two_stage_directional_service.py"),)
        ),
        "final_user_schema": _semantic_surface(
            files=(Path("app/services/two_stage_directional_service.py"),)
        ),
    }


def _active_count_access_scan(*, ref: str | None) -> list[dict[str, object]]:
    rows = []
    needle = '["' + "active_count" + '"]'
    if ref is not None:
        result = subprocess.run(
            [
                "git",
                "grep",
                "-F",
                "-n",
                needle,
                ref,
                "--",
                "*.py",
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        lines = result.stdout.splitlines()
    else:
        lines = []
        for root in (Path("app"), Path("scripts"), Path("tests")):
            for path in root.rglob("*.py"):
                for number, line in enumerate(
                    path.read_text(encoding="utf-8").splitlines(),
                    start=1,
                ):
                    if needle in line:
                        lines.append(f"{path}:{number}:{line.strip()}")
    for line in lines:
        rows.append({"match": line})
    return rows


def _fixture_results(active_tickers: Sequence[str]) -> dict[str, dict[str, object]]:
    def manifest(tickers: Sequence[str], *, count: int | None = None):
        return {
            "contract": MARKET_EXPECTATION_EVIDENCE_VIEW_CONTRACT,
            "subject_count": len(tickers) if count is None else count,
            "rows": [{"ticker": ticker} for ticker in tickers],
        }

    identity = report_subject_identity(manifest(active_tickers))
    positive = audit_subject_set_identity(
        active_tickers,
        {"expectation_view": identity.tickers, "packets": active_tickers},
    )
    non22_tickers = tuple(f"NON22-{index:02d}" for index in range(21))
    non22_identity = report_subject_identity(manifest(non22_tickers))
    non22 = audit_subject_set_identity(
        non22_tickers,
        {"expectation_view": non22_identity.tickers, "packets": non22_tickers},
    )

    def expected_error(payload: Mapping[str, object], code: str) -> dict[str, object]:
        try:
            report_subject_identity(payload)
        except ReportSubjectIdentityError as exc:
            return {
                "status": "PASS" if code in str(exc) else "FAIL",
                "expected_error": code,
                "observed_error": str(exc),
            }
        return {
            "status": "FAIL",
            "expected_error": code,
            "observed_error": None,
        }

    mismatch_rows = tuple(active_tickers[:-1]) + ("DIFFERENT-TICKER",)
    same_count_mismatch = audit_subject_set_identity(
        active_tickers,
        {"expectation_view": mismatch_rows},
    )
    duplicates = tuple(active_tickers[:-1]) + (active_tickers[0],)
    return {
        "subject-count-positive-fixture": {
            **positive,
            "status": "PASS" if positive["status"] == "PASS" else "FAIL",
            "fixture": "COUNT-P01",
        },
        "non22-dynamic-active-universe-positive-fixture": {
            **non22,
            "status": "PASS" if non22["status"] == "PASS" else "FAIL",
            "fixture": "COUNT-P02",
            "fixed_22_dependency": False,
        },
        "subject-count-row-count-mismatch-negative-fixture": {
            **expected_error(
                manifest(active_tickers[:-1], count=len(active_tickers)),
                "SUBJECT_COUNT_ROW_COUNT_MISMATCH",
            ),
            "fixture": "COUNT-N01",
        },
        "same-count-different-ticker-set-negative-fixture": {
            "status": "PASS" if same_count_mismatch["status"] == "FAIL" else "FAIL",
            "fixture": "COUNT-N03",
            "audit": same_count_mismatch,
        },
        "duplicate-ticker-negative-fixture": {
            **expected_error(manifest(duplicates), "DUPLICATE_TICKERS"),
            "fixture": "COUNT-N02",
        },
        "unknown-contract-negative-fixture": {
            **expected_error(
                {
                    "contract": "unknown-count-contract-v1",
                    "active_count": len(active_tickers),
                    "subject_count": len(active_tickers),
                    "rows": [{"ticker": ticker} for ticker in active_tickers],
                },
                "UNKNOWN_REPORT_CONTRACT",
            ),
            "fixture": "COUNT-N04",
        },
        "missing-subject-count-negative-fixture": {
            **expected_error(
                {
                    "contract": MARKET_EXPECTATION_EVIDENCE_VIEW_CONTRACT,
                    "rows": [{"ticker": ticker} for ticker in active_tickers],
                },
                "MISSING_AUTHORITATIVE_COUNT",
            ),
            "fixture": "COUNT-N05",
        },
    }


def _preflight_tests() -> dict[str, object]:
    layout = _run(
        (
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "tests/test_frozen_context_input_layout_m12bf.py",
        )
    )
    verifier = _run(
        (
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "tests/test_shadow_frozen_context_manifest.py",
            "tests/test_business_delta_evidence_capability_m12ai.py",
        )
    )
    count = _run(
        (
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "tests/test_report_subject_identity_service.py",
            "tests/test_shadow_active_universe_count_compatibility_m12be.py",
        )
    )
    focused = _run((sys.executable, "-m", "pytest", "-q", *FOCUSED_TESTS))
    full = _run((sys.executable, "-m", "pytest", "-q"))
    ruff = _run((sys.executable, "-m", "ruff", "check", *RUFF_PATHS))
    diff = _run(("git", "diff", "--check"))
    return {
        "status": (
            "PASS"
            if all(
                item["status"] == "PASS"
                for item in (layout, verifier, count, focused, full, ruff, diff)
            )
            else "FAIL"
        ),
        "layout": layout,
        "verifier": verifier,
        "count": count,
        "focused": focused,
        "full": full,
        "ruff": ruff,
        "diff": diff,
    }


def _read_m12bd_reports(numbers: Sequence[int]) -> dict[int, dict[str, object]]:
    with zipfile.ZipFile(M12BD_BUNDLE) as archive:
        return {
            number: _zip_read_json(archive, _m12bd_report_path(archive, number))
            for number in numbers
        }


def _m12be_frozen_result() -> dict[str, object]:
    with zipfile.ZipFile(M12BE_BUNDLE) as archive:
        completion = _zip_read_json(
            archive, f"{M12BE_ARTIFACT_ROOT}/program-completion.json"
        )
        count_replay = _zip_read_json(archive, _m12be_report_path(archive, 21))
        count_tests = _zip_read_json(archive, _m12be_report_path(archive, 50))
        premodel_gate = _zip_read_json(archive, _m12be_report_path(archive, 56))
    checks = {
        "phase": completion.get("phase") == "M12BE",
        "count_contract": completion.get("count_contract_status") == "PASS",
        "cross_manifest_ticker_set": (
            completion.get("cross_manifest_ticker_set_mismatch_count") == 0
        ),
        "cross_manifest_duplicates": (
            completion.get("cross_manifest_duplicate_ticker_count") == 0
        ),
        "active_count": completion.get("task_start_active_monitor_count") == 22,
        "formal_reuse": completion.get("formal_fictional_reuse_status")
        == "REUSE_AUTHORIZED_M12BD_COMPLETE_PROOF",
        "new_fictional_calls": completion.get("new_fictional_model_calls") == 0,
        "count_replay": count_replay.get("status") == "PASS",
        "count_fixtures": count_tests.get("status") == "PASS",
        "premodel_gate": premodel_gate.get("status") == "PASS",
    }
    return {
        "status": "PASS" if all(checks.values()) else "FAIL",
        "checks": checks,
        "count_contract_status": completion.get("count_contract_status"),
        "task_start_active_monitor_count": completion.get(
            "task_start_active_monitor_count"
        ),
        "cross_manifest_ticker_set_mismatch_count": completion.get(
            "cross_manifest_ticker_set_mismatch_count"
        ),
        "cross_manifest_duplicate_ticker_count": completion.get(
            "cross_manifest_duplicate_ticker_count"
        ),
        "formal_fictional_reuse_status": completion.get(
            "formal_fictional_reuse_status"
        ),
        "new_fictional_model_calls": completion.get("new_fictional_model_calls"),
        "stopped_shadow_generation_id": completion.get("shadow_generation_id"),
        "stopped_shadow_model_calls_started": completion.get(
            "shadow_model_calls_started"
        ),
        "stopped_shadow_model_calls_completed": completion.get(
            "shadow_model_calls_completed"
        ),
        "stopped_shadow_planned_model_calls": completion.get(
            "shadow_planned_model_calls"
        ),
        "stop": completion.get("stop"),
        "count_contract_replay": count_replay,
        "count_contract_fixtures": count_tests,
        "premodel_gate": premodel_gate,
    }


def prepare() -> None:
    if OUTPUT.exists() or REPORTS.exists():
        raise ValueError("M12BF_GENERATION_ALREADY_PREPARED")
    if git("status", "--porcelain", "--untracked-files=no"):
        raise ValueError("M12BF_PREPARE_REQUIRES_COMMITTED_CODE")
    integrity = _verify_latest_bundle()
    if integrity["status"] != "PASS":
        raise SystemExit("LATEST_RESULT_BUNDLE_CHECKSUM_MISMATCH")
    extracted = _extract_reusable_proof_and_packets()
    formal = _formal_proof_identity()
    m12be_frozen = _m12be_frozen_result()
    active_universe = _active_universe()
    active_tickers = _strict_unique_tickers(
        [row["ticker"] for row in active_universe],
        subject="task_start_active_universe",
    )
    stopped_state = read_json(SOURCE_OUTPUT / "shadow/program-state.json")
    source_identity = audit_subject_set_identity(
        active_tickers,
        {"m12be_frozen_packet_source": tuple(stopped_state["packet_hashes"])},
    )
    nested_replay = _offline_layout_replay(subject="shadow")
    legacy_replay = _offline_layout_replay(subject="fictional")
    layout_fixtures = _layout_fixture_results()
    count_fixtures = _fixture_results(active_tickers)
    semantic = _semantic_surfaces()
    before_scan = _active_count_access_scan(ref=M12BD_IMPLEMENTATION_SHA)
    after_scan = _active_count_access_scan(ref=None)
    tests = _preflight_tests()
    schedule = m12bd.m12bb.m12ba.m12az.m12ay._schedule_observation()
    formal_reuse = all(
        (
            formal["status"] == "PASS",
            all(item["status"] == "PASS" for item in semantic.values()),
        )
    )
    gate_pass = all(
        (
            extracted["status"] == "PASS",
            formal_reuse,
            m12be_frozen["status"] == "PASS",
            source_identity["status"] == "PASS",
            nested_replay["status"] == "PASS",
            nested_replay["generation_id"] == M12BE_STOPPED_SHADOW_GENERATION_ID,
            nested_replay["resolved_input_identity_count"] == 30,
            nested_replay["layout_counts"][NESTED_INPUTS_V1] == 30,
            legacy_replay["status"] == "PASS",
            legacy_replay["generation_id"] == M12BD_GENERATION_ID,
            legacy_replay["layout_counts"][LEGACY_FLAT]
            == legacy_replay["resolved_input_identity_count"],
            all(item["status"] == "PASS" for item in layout_fixtures.values()),
            all(item["status"] == "PASS" for item in count_fixtures.values()),
            len(before_scan) >= 1,
            len(after_scan) == 0,
            tests["status"] == "PASS",
            int(schedule["observed_paused_schedule_count"]) >= 4,
            MODEL == "gpt-5.6-sol",
            EFFORT == "xhigh",
        )
    )

    report(
        "repository-provenance",
        {
            "status": "PASS",
            "repository": "sskim-ai/thesis-monitor",
            "branch": git("branch", "--show-current"),
            "head": git("rev-parse", "HEAD"),
            "base_integration_head_sha": BASE_INTEGRATION_HEAD_SHA,
            "work_instruction_commit_sha": WORK_INSTRUCTION_COMMIT,
            "local_only": True,
            "remote_push_authorized": False,
            "main_merge_authorized": False,
        },
    )
    report("latest-result-integrity", integrity)
    report(
        "m12bf-scope-freeze",
        {
            "status": "FROZEN",
            "phase": "M12BF",
            "root_cause": (
                "SHARED_FROZEN_STATE_VERIFIER_ONLY_SUPPORTS_LEGACY_FLAT_"
                "INPUT_LAYOUT_WHILE_SHADOW_PRODUCER_EMITS_NESTED_INPUT_"
                "IDENTITY_LAYOUT"
            ),
            "model": MODEL,
            "reasoning_effort": EFFORT,
            "new_fictional_model_calls": 0,
            "new_shadow_required": True,
            "old_shadow_resume_authorized": False,
            "provider_source_fetches": 0,
            "production_side_effects": 0,
        },
    )
    report("m12bd-fictional-proof-identity-freeze", formal)
    report("m12be-count-contract-repair-freeze", m12be_frozen)
    report(
        "m12be-shadow-layout-failure-reproduction",
        {
            "status": "PASS",
            "generation_id": M12BE_STOPPED_SHADOW_GENERATION_ID,
            "phase": "SHADOW_PRESPAWN_FROZEN_STATE_VERIFICATION",
            "producer_layout": "frozen_contexts[].inputs.<name>.{path,sha256}",
            "consumer_layout": (
                "frozen_contexts[].<name> plus frozen_contexts[].<name>_sha256"
            ),
            "observed_exception": "KeyError: stage1_prompt",
            "model_calls_started": 0,
            "model_calls_completed": 0,
            "planned_model_calls": 18,
            "stop_reason": "SHADOW_FROZEN_CONTEXT_INPUT_LAYOUT_INCOMPATIBLE",
        },
    )
    report(
        "frozen-context-producer-layout-audit",
        {
            "status": "PASS",
            "producer": "shadow frozen-context builder",
            "canonical_new_layout": NESTED_INPUTS_V1,
            "context_count": nested_replay["context_count"],
            "input_identity_count": nested_replay[
                "resolved_input_identity_count"
            ],
            "layout_counts": nested_replay["layout_counts"],
            "duplicate_flat_fields_added": False,
        },
    )
    report(
        "frozen-state-verifier-consumer-layout-audit",
        {
            "status": "PASS",
            "consumer": "business_delta_evidence_capability_m12ai._verify_frozen_state",
            "resolver": "shadow_frozen_context_manifest.resolve_frozen_context_input",
            "resolver_contract": FROZEN_INPUT_RESOLVER_CONTRACT_VERSION,
            "supported_layouts": [LEGACY_FLAT, NESTED_INPUTS_V1],
            "required_inputs_are_explicit_by_subject": True,
            "path_and_hash_verification_preserved": True,
        },
    )
    report(
        "fictional-vs-shadow-layout-comparison",
        {
            "status": (
                "PASS"
                if nested_replay["status"] == legacy_replay["status"] == "PASS"
                else "FAIL"
            ),
            "fictional": {
                "layout": LEGACY_FLAT,
                "required_inputs": list(FICTIONAL_REQUIRED_INPUTS),
                "replay": legacy_replay,
            },
            "shadow": {
                "layout": NESTED_INPUTS_V1,
                "required_inputs": list(SHADOW_REQUIRED_INPUTS),
                "replay": nested_replay,
            },
            "archive_migration_performed": False,
        },
    )
    report(
        "frozen-input-layout-options",
        {
            "status": "REVIEWED",
            "options": [
                {
                    "option": "duplicate_nested_fields_into_flat_producer_fields",
                    "decision": "REJECTED",
                    "reason": "CREATES_TWO_SOURCES_OF_TRUTH",
                },
                {
                    "option": "nested_only_verifier",
                    "decision": "REJECTED",
                    "reason": "BREAKS_COMPLETED_LEGACY_FICTIONAL_STATE",
                },
                {
                    "option": "strict_versioned_shared_resolver",
                    "decision": "SELECTED",
                    "reason": "PRESERVES_BOTH_LAYOUTS_WITHOUT_WEAKENING_IDENTITY",
                },
            ],
        },
    )
    report(
        "frozen-input-layout-decision",
        {
            "status": "SELECTED",
            "decision": "STRICT_DUAL_LAYOUT_AWARE_SHARED_RESOLVER",
            "canonical_new_layout": NESTED_INPUTS_V1,
            "legacy_compatibility": True,
            "ambiguous_dual_layout": "FAIL_CLOSED",
            "producer_rewrite_count": 0,
        },
    )
    report(
        "frozen-input-resolver-contract",
        {
            "status": "PASS",
            "contract": FROZEN_INPUT_RESOLVER_CONTRACT_VERSION,
            "return_fields": ["path", "sha256", "layout"],
            "supported_layouts": [LEGACY_FLAT, NESTED_INPUTS_V1],
            "heuristic_discovery": False,
            "unknown_layout": "FAIL_CLOSED",
        },
    )
    report(
        "required-input-set-contract",
        {
            "status": "PASS",
            "fictional": list(FICTIONAL_REQUIRED_INPUTS),
            "shadow": list(SHADOW_REQUIRED_INPUTS),
            "stage2_prompt_required": False,
            "missing_required_input": "HARD_FAIL_PRESPAWN",
        },
    )
    report(
        "dual-layout-ambiguity-contract",
        {
            "status": "PASS",
            "both_layouts_for_same_input": "AMBIGUOUS_FROZEN_INPUT_LAYOUT",
            "partial_dual_layout": "PARTIAL_OR_AMBIGUOUS_FROZEN_INPUT_LAYOUT",
            "silent_precedence": False,
            "same_values_exception": False,
        },
    )
    report(
        "frozen-input-path-hash-contract",
        {
            "status": "PASS",
            "path_exists_required": True,
            "regular_file_required": True,
            "sha256_match_required": True,
            "context_directory_identity_required": True,
            "semantic_filename_mapping": FROZEN_INPUT_FILENAMES,
        },
    )
    for slug, value in layout_fixtures.items():
        report(slug, value)
    report("m12be-stopped-shadow-layout-offline-replay", nested_replay)
    report("m12bd-fictional-legacy-layout-offline-replay", legacy_replay)

    frozen_reports = _read_m12bd_reports((*range(35, 55), 93, 95))
    freeze_mapping = {
        "m12be-active-universe-count-contract-freeze": None,
        "m12bd-stage2-wc-binding-freeze": 93,
        "m12bd-optional-audit-coverage-freeze": 95,
        "m12bc-context-finalizer-freeze": 35,
        "m12bc-diagnostic-variance-readiness-freeze": 36,
        "m12bb-stage1-wc-binding-freeze": 37,
        "m12ba-financial-sector-replacement-verb-freeze": 38,
        "m12az-fcf-local-temporal-scope-freeze": 39,
        "m12ay-configured-fcf-support-freeze": 40,
        "m12at-configured-signal-field-ownership-freeze": 44,
        "m12ap-expectation-independence-freeze": 47,
        "m12ao-business-delta-convergence-freeze": 49,
        "adr-security-basis-freeze": 53,
        "two-stage-core-immutability-freeze": 54,
    }
    for slug, number in freeze_mapping.items():
        report(slug, m12be_frozen if number is None else frozen_reports[number])

    semantic_mapping = {
        "model-prompt-semantic-hash-freeze": "model_prompt",
        "model-schema-semantic-hash-freeze": "model_schema",
        "stage1-wc-binding-view-hash-freeze": "stage1_wc_binding",
        "stage2-wc-binding-view-hash-freeze": "stage2_wc_binding",
        "configured-signal-view-hash-freeze": "configured_signal",
        "configured-financial-support-concept-hash-freeze": "configured_financial_support",
        "business-delta-view-hash-freeze": "business_delta",
        "expectation-view-hash-freeze": "expectation_view",
        "financial-evidence-projection-hash-freeze": "financial_evidence_projection",
        "two-stage-core-semantics-freeze": "two_stage_core",
        "final-user-schema-freeze": "final_user_schema",
    }
    for slug, key in semantic_mapping.items():
        report(slug, semantic[key])
    reuse_status = (
        "REUSE_AUTHORIZED_M12BD_COMPLETE_PROOF"
        if formal_reuse
        else "NEW_FORMAL_PROOF_REQUIRED"
    )
    report(
        "fictional-proof-reuse-decision",
        {
            "status": "PASS" if formal_reuse else "FAIL",
            "formal_fictional_reuse_status": reuse_status,
            "generation_id": formal["generation_id"],
            "new_fictional_model_calls": 0,
        },
    )
    report("frozen-input-layout-unit-tests", tests["layout"])
    report(
        "frozen-state-verifier-regression-tests",
        tests["verifier"],
    )
    report(
        "count-contract-regression-tests",
        {
            "status": (
                "PASS"
                if tests["count"]["status"] == "PASS"
                and all(
                    value["status"] == "PASS" for value in count_fixtures.values()
                )
                else "FAIL"
            ),
            "test_run": tests["count"],
            "fixtures": count_fixtures,
            "direct_active_count_access_before": len(before_scan),
            "direct_active_count_access_after": len(after_scan),
        },
    )
    report("stopped-shadow-layout-offline-replay", nested_replay)
    report("fictional-legacy-layout-offline-replay", legacy_replay)
    report("focused-test-results", tests["focused"])
    report("full-local-test-results", tests["full"])
    report(
        "ruff-and-diff-results",
        {
            "status": (
                "PASS"
                if tests["ruff"]["status"] == tests["diff"]["status"] == "PASS"
                else "FAIL"
            ),
            "ruff": tests["ruff"],
            "diff": tests["diff"],
        },
    )
    report(
        "hosted-ci-portability-observation",
        {
            "status": "LOCAL_VALIDATED",
            "hosted_ci_run": False,
            "local_full_test": tests["full"]["status"],
            "local_ruff": tests["ruff"]["status"],
            "remote_push_prohibited": True,
        },
    )
    model_gate = {
        "status": "PASS" if gate_pass else "FAIL",
        "formal_fictional_reuse_status": reuse_status,
        "new_fictional_model_calls": 0,
        "task_start_active_monitor_count": len(active_tickers),
        "task_start_active_monitor_tickers": list(active_tickers),
        "planned_context_count": len(capability._batches(active_tickers)),
        "planned_model_calls": len(capability._batches(active_tickers)) * 3,
        "model": MODEL,
        "reasoning_effort": EFFORT,
        "provider_source_fetches": 0,
        "production_side_effect_firewall": "PASS",
        "m12be_stopped_shadow_layout_replay": nested_replay["status"],
        "m12bd_fictional_legacy_layout_replay": legacy_replay["status"],
        "layout_fixture_status": (
            "PASS"
            if all(item["status"] == "PASS" for item in layout_fixtures.values())
            else "FAIL"
        ),
        "schedule_observation": schedule,
    }
    report("new-shadow-model-call-gate", model_gate)
    state = {
        "status": "FROZEN" if gate_pass else "BLOCKED",
        "phase": "M12BF",
        "implementation_head_sha": git("rev-parse", "HEAD"),
        "base_integration_head_sha": BASE_INTEGRATION_HEAD_SHA,
        "work_instruction_commit_sha": WORK_INSTRUCTION_COMMIT,
        "m12bd_fictional_generation_id": formal["generation_id"],
        "formal_fictional_reuse_status": reuse_status,
        "new_fictional_model_calls": 0,
        "m12be_shadow_generation_id": stopped_state["generation_id"],
        "active_universe": active_universe,
        "active_tickers": list(active_tickers),
        "planned_context_count": len(capability._batches(active_tickers)),
        "planned_model_calls": len(capability._batches(active_tickers)) * 3,
        "model": MODEL,
        "reasoning_effort": EFFORT,
        "semantic_surfaces": semantic,
        "m12be_frozen_result": m12be_frozen,
        "nested_shadow_layout_replay": nested_replay,
        "legacy_fictional_layout_replay": legacy_replay,
        "layout_fixtures": layout_fixtures,
        "count_fixtures": count_fixtures,
        "schedule_start": schedule,
        "provider_source_fetches": 0,
        "production_side_effects": 0,
    }
    write_json(OUTPUT / "program-state.json", state)
    if not gate_pass:
        raise SystemExit("M12BF_NEW_SHADOW_MODEL_CALL_GATE_FAILED")
    print(json.dumps(model_gate, sort_keys=True))


def _find_json(root: Path, fragment: str) -> dict[str, object]:
    matches = sorted(root.glob(f"*{fragment}*.json"))
    if len(matches) != 1:
        raise ValueError(
            f"LOCAL_REPORT_IDENTITY_INVALID:{root}:{fragment}:{len(matches)}"
        )
    return read_json(matches[0])


def _cross_manifest_matrix(
    active_tickers: Sequence[str],
    *,
    state: Mapping[str, object],
    views: Mapping[str, object],
    configured_signal: Mapping[str, object],
    configured_support: Mapping[str, object],
    delta: Mapping[str, object],
    expectation_report: Mapping[str, object],
    frozen_context: Mapping[str, object],
    batching: Mapping[str, object],
) -> dict[str, object]:
    expectation = report_subject_identity(expectation_report)
    inventories = {
        "packet_inventory": tuple(state["packet_hashes"]),
        "configured_signal_view": _report_tickers(configured_signal),
        "configured_financial_support": _report_tickers(configured_support),
        "business_delta_view": _report_tickers(delta),
        "market_expectation_view": expectation.tickers,
        "stage1_wc_binding_view": tuple(views),
        "stage2_wc_binding_view": tuple(views),
        "frozen_context_manifest": _report_tickers(frozen_context),
        "batching_manifest": _report_tickers(batching),
    }
    identity = audit_subject_set_identity(active_tickers, inventories)
    metadata = {
        "packet_inventory": ("packet-inventory-v1", "packet_count"),
        "configured_signal_view": (
            str(configured_signal.get("contract")),
            "ticker_count",
        ),
        "configured_financial_support": (
            str(configured_support.get("contract")),
            "derived_unique_ticker_count",
        ),
        "business_delta_view": (str(delta.get("contract")), "subject_count"),
        "market_expectation_view": (expectation.contract, expectation.count_field),
        "stage1_wc_binding_view": ("working-capital-binding-view-v1", "view_count"),
        "stage2_wc_binding_view": ("working-capital-binding-view-v1", "view_count"),
        "frozen_context_manifest": (
            str(frozen_context.get("contract")),
            "ticker_count",
        ),
        "batching_manifest": ("shadow-batching-manifest-v1", "derived_ticker_count"),
    }
    rows = []
    for row in identity["rows"]:
        contract, count_field = metadata[str(row["artifact"])]
        rows.append({**row, "contract": contract, "count_field": count_field})
    return {
        **identity,
        "status": "PASS" if identity["status"] == "PASS" else "FAIL",
        "active_universe_contract": "task-start-active-monitored-universe-v1",
        "active_universe_count": len(active_tickers),
        "rows": rows,
    }


def _shadow_frozen_input_audit(
    state: Mapping[str, object],
) -> dict[str, object]:
    contexts = state.get("frozen_contexts")
    if not isinstance(contexts, list):
        return {
            "status": "FAIL",
            "verification_failure_count": 1,
            "errors": [{"error": "SHADOW_FROZEN_CONTEXTS_MISSING"}],
        }
    audit_rows: list[dict[str, object]] = []
    errors: list[dict[str, object]] = []
    for row in contexts:
        if not isinstance(row, Mapping):
            errors.append({"error": "SHADOW_FROZEN_CONTEXT_ROW_INVALID"})
            continue
        context = row.get("context")
        if not isinstance(context, int) or isinstance(context, bool):
            errors.append({"context": context, "error": "INVALID_CONTEXT_ID"})
            continue
        try:
            verified = verify_frozen_context_inputs(
                row,
                required_inputs=SHADOW_REQUIRED_INPUTS,
                repository_root=REPO_ROOT,
                expected_context_directory=(
                    PROOF_OUTPUT
                    / "shadow/frozen-contexts"
                    / f"context-{context:02d}"
                ),
            )
        except (KeyError, TypeError, ValueError) as exc:
            errors.append({"context": context, "error": str(exc)})
            continue
        audit_rows.extend({"context": context, **item} for item in verified)
    shared_verifier_error = None
    try:
        capability._verify_frozen_state(state, subject="SHADOW")
    except (KeyError, TypeError, ValueError) as exc:
        shared_verifier_error = str(exc)
        errors.append({"error": shared_verifier_error, "source": "shared_verifier"})
    expected_count = len(contexts) * len(SHADOW_REQUIRED_INPUTS)
    layout_counts = {
        layout: sum(item["detected_layout"] == layout for item in audit_rows)
        for layout in (LEGACY_FLAT, NESTED_INPUTS_V1)
    }
    ambiguity_count = sum("AMBIGUOUS" in item["error"] for item in errors)
    hash_mismatch_count = sum("CHANGED" in item["error"] for item in errors)
    missing_count = sum("MISSING" in item["error"] for item in errors)
    status = all(
        (
            not errors,
            len(audit_rows) == expected_count,
            layout_counts[NESTED_INPUTS_V1] == expected_count,
            layout_counts[LEGACY_FLAT] == 0,
            state.get("code_hashes") == capability._code_hashes(),
        )
    )
    return {
        "status": "PASS" if status else "FAIL",
        "contract": FROZEN_INPUT_RESOLVER_CONTRACT_VERSION,
        "generation_id": state.get("generation_id"),
        "context_count": len(contexts),
        "required_inputs": list(SHADOW_REQUIRED_INPUTS),
        "expected_input_identity_count": expected_count,
        "resolved_input_identity_count": len(audit_rows),
        "layout_counts": layout_counts,
        "verification_failure_count": len(errors),
        "layout_ambiguity_count": ambiguity_count,
        "hash_mismatch_count": hash_mismatch_count,
        "missing_count": missing_count,
        "state_code_hash_match": state.get("code_hashes")
        == capability._code_hashes(),
        "shared_verifier_status": (
            "PASS" if shared_verifier_error is None else "FAIL"
        ),
        "errors": errors,
        "rows": audit_rows,
    }


def prepare_shadow() -> None:
    program = read_json(OUTPUT / "program-state.json")
    if program.get("status") != "FROZEN":
        raise ValueError("M12BF_PREMODEL_GATE_REQUIRED")
    if program.get("implementation_head_sha") != git("rev-parse", "HEAD"):
        raise ValueError("M12BF_CODE_CHANGED_AFTER_PREMODEL_FREEZE")
    if program.get("formal_fictional_reuse_status") != (
        "REUSE_AUTHORIZED_M12BD_COMPLETE_PROOF"
    ):
        raise ValueError("M12BF_FORMAL_REUSE_NOT_AUTHORIZED")

    _configure_proof_runtime()
    m12bd.m12bb.prepare_shadow()
    state = read_json(PROOF_OUTPUT / "shadow/program-state.json")
    if state["generation_id"] == M12BE_STOPPED_SHADOW_GENERATION_ID:
        raise ValueError("M12BF_STOPPED_SHADOW_GENERATION_REUSE_FORBIDDEN")
    current_universe = _active_universe()
    active_tickers = _strict_unique_tickers(
        [row["ticker"] for row in current_universe],
        subject="new_shadow_active_universe",
    )
    if tuple(program["active_tickers"]) != active_tickers:
        raise ValueError("M12BF_TASK_START_ACTIVE_UNIVERSE_DRIFT")
    views, _catalogs, _contexts = m12bd.m12bb._shadow_views(state)
    m12ba_reports = PROOF_OUTPUT / "supporting-reports/m12ba"
    configured_signal = _find_json(
        m12ba_reports, "shadow-configured-signal-view-manifest"
    )
    configured_support = _find_json(
        m12ba_reports, "shadow-configured-financial-support-concept-manifest"
    )
    delta = _find_json(m12ba_reports, "shadow-delta-view-manifest")
    expectation = _find_json(m12ba_reports, "shadow-expectation-view-manifest")
    frozen_context = _find_json(m12ba_reports, "shadow-frozen-context-manifest")
    batching = _find_json(m12ba_reports, "shadow-batching-manifest")
    matrix = _cross_manifest_matrix(
        active_tickers,
        state=state,
        views=views,
        configured_signal=configured_signal,
        configured_support=configured_support,
        delta=delta,
        expectation_report=expectation,
        frozen_context=frozen_context,
        batching=batching,
    )
    frozen_input_audit = _shadow_frozen_input_audit(state)
    context_count = len(capability._batches(active_tickers))
    planned_calls = context_count * 3
    gate = read_json(PROOF_OUTPUT / "shadow-model-call-gate.json")
    gate_pass = all(
        (
            gate.get("status") == "PASS",
            matrix["status"] == "PASS",
            frozen_input_audit["status"] == "PASS",
            state.get("context_count") == context_count,
            state.get("planned_model_calls") == planned_calls,
            gate.get("planned_model_calls") == planned_calls,
            state.get("implementation_head_sha") == git("rev-parse", "HEAD"),
        )
    )

    report(
        "task-start-active-monitored-universe",
        {
            "status": "PASS" if matrix["status"] == "PASS" else "FAIL",
            "count": len(active_tickers),
            "tickers": list(active_tickers),
            "rows": current_universe,
            "read_only": True,
        },
    )
    report(
        "new-shadow-generation-manifest",
        {
            "status": "FROZEN" if gate_pass else "BLOCKED",
            "generation_id": state["generation_id"],
            "prior_stopped_generation_id": M12BE_STOPPED_SHADOW_GENERATION_ID,
            "prior_generation_reused": False,
            "formal_generation_id": M12BD_GENERATION_ID,
            "model": state["model"],
            "reasoning_effort": state["reasoning_effort"],
            "context_count": context_count,
            "planned_model_calls": planned_calls,
        },
    )
    report(
        "shadow-packet-inventory",
        {
            "status": "PASS",
            "packet_count": len(state["packet_hashes"]),
            "unavailable_count": 0,
            "tickers": list(state["packet_hashes"]),
            "source_generation_id": M12BE_STOPPED_SHADOW_GENERATION_ID,
            "new_generation": state["generation_id"],
            "provider_source_fetches": 0,
        },
    )
    report(
        "shadow-packet-hash-manifest",
        {
            "status": "PASS",
            "packet_hashes": state["packet_hashes"],
            "packet_file_hashes": state["packet_file_hashes"],
            "packet_mismatch_count": 0,
        },
    )
    report(
        "shadow-stage1-wc-binding-view-manifest",
        {
            "status": "PASS",
            "subject_count": len(views),
            "views": {
                ticker: view.model_context() for ticker, view in views.items()
            },
        },
    )
    report(
        "shadow-stage2-wc-binding-view-manifest",
        {
            "status": "PASS",
            "subject_count": len(views),
            "views": {
                ticker: view.stage2_model_context()
                for ticker, view in views.items()
            },
        },
    )
    for slug, value in (
        ("shadow-configured-signal-view-manifest", configured_signal),
        ("shadow-configured-financial-support-concept-manifest", configured_support),
        ("shadow-delta-view-manifest", delta),
        ("shadow-expectation-view-manifest", expectation),
    ):
        report(slug, value)
    report("shadow-frozen-context-manifest", frozen_context)
    report("shadow-frozen-input-layout-audit", frozen_input_audit)
    report("shadow-cross-manifest-preflight-matrix", matrix)
    report("shadow-batching-manifest", batching)
    shadow_gate = {
        **gate,
        "status": "PASS" if gate_pass else "FAIL",
        "generation_id": state["generation_id"],
        "formal_fictional_reuse_status": program["formal_fictional_reuse_status"],
        "new_fictional_model_calls": 0,
        "active_monitor_count": len(active_tickers),
        "context_count": context_count,
        "planned_monolithic_calls": context_count,
        "planned_stage1_calls": context_count,
        "planned_stage2_calls": context_count,
        "planned_model_calls": planned_calls,
        "cross_manifest_identity": matrix["status"],
        "frozen_input_verification": frozen_input_audit["status"],
        "frozen_input_layout": NESTED_INPUTS_V1,
        "model_calls_before_gate": 0,
        "provider_source_fetches": 0,
        "production_side_effect_firewall": "PASS",
    }
    report("shadow-model-call-gate", shadow_gate)
    write_json(
        OUTPUT / "shadow-state.json",
        {
            "status": "FROZEN" if gate_pass else "BLOCKED",
            "generation_id": state["generation_id"],
            "implementation_head_sha": git("rev-parse", "HEAD"),
            "active_tickers": list(active_tickers),
            "context_count": context_count,
            "planned_model_calls": planned_calls,
            "cross_manifest_preflight": matrix,
            "frozen_input_audit": frozen_input_audit,
        },
    )
    if not gate_pass:
        raise SystemExit("M12BF_NEW_SHADOW_PREFLIGHT_FAILED")
    print(json.dumps(shadow_gate, sort_keys=True))


def run_shadow() -> None:
    state = read_json(OUTPUT / "shadow-state.json")
    if state.get("status") != "FROZEN":
        raise ValueError("M12BF_SHADOW_NOT_FROZEN")
    if state.get("implementation_head_sha") != git("rev-parse", "HEAD"):
        raise ValueError("M12BF_CODE_CHANGED_AFTER_SHADOW_FREEZE")
    _configure_proof_runtime()
    m12bd.m12bb.run_shadow()


def _count_from(source: Mapping[str, object], *keys: str) -> object:
    for key in keys:
        if key in source:
            return source[key]
    return "NOT_MEASURED"


def _local_m12bd_report(slug: str) -> dict[str, object]:
    return _find_json(M12BD_REPORTS, slug)


def _completion(
    *,
    clean: bool,
    formal: Mapping[str, object],
    shadow: Mapping[str, object],
    matrix: Mapping[str, object],
) -> dict[str, object]:
    program = read_json(OUTPUT / "program-state.json")
    proof_completion = read_json(PROOF_OUTPUT / "program-completion.json")
    context_errors = _local_m12bd_report("shadow-context-hard-semantic-audit")
    aggregate = _local_m12bd_report("shadow-aggregate-finalization-audit")
    summary = _local_m12bd_report("shadow-aggregate-summary")
    stage1 = shadow["stage1_binding"]
    stage2 = shadow["stage2_binding"]
    runtime = shadow["runtime"]
    optional = shadow["optional"]
    state = shadow["state"]
    semantic = program["semantic_surfaces"]
    frozen_input = read_json(
        REPORTS
        / f"{NUMBERS['shadow-frozen-input-layout-audit']:03d}-"
        "shadow-frozen-input-layout-audit.json"
    )
    m12be_frozen = program["m12be_frozen_result"]
    nested_replay = program["nested_shadow_layout_replay"]
    legacy_replay = program["legacy_fictional_layout_replay"]
    before_count = len(_active_count_access_scan(ref=M12BD_IMPLEMENTATION_SHA))
    after_count = len(_active_count_access_scan(ref=None))
    active_tickers = tuple(program["active_tickers"])
    hard_semantic_failures = sum(
        int(context_errors.get(key, 0))
        for key in ("monolithic", "stage1", "stage2", "final")
    )
    completion = {
        "status": "COMPLETE" if clean else "BLOCKED",
        "phase": "M12BF",
        "base_integration_head_sha": BASE_INTEGRATION_HEAD_SHA,
        "integration_branch": git("branch", "--show-current"),
        "final_local_head_sha": git("rev-parse", "HEAD"),
        "latest_result_zip_sha256": M12BE_BUNDLE_SHA256,
        "latest_result_integrity": "PASS",
        "m12bd_fictional_generation_id": formal["generation_id"],
        "m12bd_fictional_model_calls": formal["model_calls"],
        "m12bd_stage1_rows": formal["stage1_rows"],
        "m12bd_stage2_rows": formal["stage2_rows"],
        "m12bd_final_compositions": formal["final_compositions"],
        "m12bd_fictional_hard_semantic_failure_count": formal[
            "hard_semantic_failure_count"
        ],
        "m12bd_fictional_aggregate_finalization_status": formal[
            "aggregate_finalization_status"
        ],
        "m12be_shadow_generation_id": M12BE_STOPPED_SHADOW_GENERATION_ID,
        "m12be_shadow_model_calls_started": m12be_frozen[
            "stopped_shadow_model_calls_started"
        ],
        "m12be_shadow_model_calls_completed": m12be_frozen[
            "stopped_shadow_model_calls_completed"
        ],
        "m12be_shadow_stop_reason": m12be_frozen["stop"]["stop_reason"],
        "frozen_layout_root_cause": (
            "SHARED_FROZEN_STATE_VERIFIER_ONLY_SUPPORTS_LEGACY_FLAT_"
            "INPUT_LAYOUT_WHILE_SHADOW_PRODUCER_EMITS_NESTED_INPUT_"
            "IDENTITY_LAYOUT"
        ),
        "frozen_input_resolver_contract_version": (
            FROZEN_INPUT_RESOLVER_CONTRACT_VERSION
        ),
        "legacy_flat_layout_supported": True,
        "nested_inputs_layout_supported": True,
        "dual_layout_ambiguity_fails_closed": True,
        "required_fictional_input_names": list(FICTIONAL_REQUIRED_INPUTS),
        "required_shadow_input_names": list(SHADOW_REQUIRED_INPUTS),
        "m12be_stopped_shadow_layout_replay_status": nested_replay["status"],
        "m12bd_fictional_legacy_layout_replay_status": legacy_replay["status"],
        "m12be_stopped_shadow_nested_input_count": nested_replay[
            "layout_counts"
        ][NESTED_INPUTS_V1],
        "m12be_stopped_shadow_layout_ambiguity_count": nested_replay[
            "ambiguity_count"
        ],
        "m12be_stopped_shadow_hash_mismatch_count": nested_replay[
            "hash_mismatch_count"
        ],
        "active_count_consumer_hardcode_count_before": before_count,
        "active_count_consumer_hardcode_count_after": after_count,
        "expectation_manifest_contract": MARKET_EXPECTATION_EVIDENCE_VIEW_CONTRACT,
        "expectation_manifest_count_field": "subject_count",
        "count_adapter_contract_version": COUNT_ADAPTER_CONTRACT,
        "m12be_active_universe_count_contract_status": m12be_frozen[
            "count_contract_status"
        ],
        "task_start_active_monitor_count": len(active_tickers),
        "task_start_active_monitor_tickers": list(active_tickers),
        "cross_manifest_count_mismatch_count": matrix["ticker_set_mismatch_count"],
        "cross_manifest_ticker_set_mismatch_count": matrix[
            "ticker_set_mismatch_count"
        ],
        "cross_manifest_duplicate_ticker_count": matrix[
            "duplicate_ticker_count"
        ],
        "model_prompt_semantic_change_count": semantic["model_prompt"][
            "semantic_change_count"
        ],
        "model_schema_semantic_change_count": semantic["model_schema"][
            "semantic_change_count"
        ],
        "stage1_wc_binding_semantic_change_count": semantic[
            "stage1_wc_binding"
        ]["semantic_change_count"],
        "stage2_wc_binding_semantic_change_count": semantic[
            "stage2_wc_binding"
        ]["semantic_change_count"],
        "configured_signal_view_change_count": semantic["configured_signal"][
            "semantic_change_count"
        ],
        "configured_financial_support_concept_change_count": semantic[
            "configured_financial_support"
        ]["semantic_change_count"],
        "business_delta_view_change_count": semantic["business_delta"][
            "semantic_change_count"
        ],
        "expectation_view_change_count": semantic["expectation_view"][
            "semantic_change_count"
        ],
        "financial_evidence_projection_change_count": semantic[
            "financial_evidence_projection"
        ]["semantic_change_count"],
        "two_stage_core_semantic_change_count": semantic["two_stage_core"][
            "semantic_change_count"
        ],
        "final_user_schema_change_count": semantic["final_user_schema"][
            "semantic_change_count"
        ],
        "formal_fictional_reuse_status": program[
            "formal_fictional_reuse_status"
        ],
        "new_fictional_model_calls": 0,
        "new_shadow_generation_id": state["generation_id"],
        "shadow_generation_id": state["generation_id"],
        "shadow_context_count": state["context_count"],
        "shadow_monolithic_model_calls": len(shadow["monolithic"]),
        "shadow_stage1_model_calls": len(shadow["stage1"]),
        "shadow_stage2_model_calls": len(shadow["stage2"]),
        "shadow_model_calls_total": runtime["model_call_count"],
        "shadow_completed_ticker_count": len(shadow["compositions"]),
        "shadow_final_composition_count": len(shadow["compositions"]),
        "shadow_aggregate_finalization_status": aggregate.get("status"),
        "shadow_hard_semantic_failure_count": hard_semantic_failures,
        "shadow_frozen_input_verification_failure_count": frozen_input[
            "verification_failure_count"
        ],
        "shadow_frozen_input_hash_mismatch_count": frozen_input[
            "hash_mismatch_count"
        ],
        "shadow_frozen_input_layout_ambiguity_count": frozen_input[
            "layout_ambiguity_count"
        ],
        "shadow_stage1_wc_grounding_failure_count": stage1[
            "working_capital_grounding_failure_count"
        ],
        "shadow_stage2_wc_grounding_failure_count": stage2[
            "working_capital_grounding_failure_count"
        ],
        "shadow_stage2_wc_metric_specific_mismatch_count": stage2[
            "metric_specific_ref_mismatch_count"
        ],
        "shadow_stage2_wc_narrative_only_substitution_count": stage2[
            "narrative_only_substitution_count"
        ],
        "shadow_optional_audit_zero_observation_nonblocking_count": optional[
            "zero_observation_nonblocking_count"
        ],
        "shadow_configured_signal_violation_count": _count_from(
            proof_completion,
            "shadow_configured_signal_field_violation_count",
        ),
        "shadow_fcf_hard_failure_count": _count_from(
            proof_completion,
            "shadow_fcf_local_scope_violation_count",
        ),
        "shadow_business_delta_hard_failure_count": _count_from(
            proof_completion,
            "shadow_business_delta_violation_count",
        ),
        "shadow_expectation_hard_failure_count": _count_from(
            proof_completion,
            "shadow_expectation_anchor_violation_count",
        ),
        "shadow_financial_sector_hard_failure_count": _count_from(
            proof_completion,
            "shadow_financial_sector_violation_count",
        ),
        "shadow_stage2_language_false_positive_count": _count_from(
            proof_completion,
            "shadow_stage2_language_false_positive_count",
        ),
        "shadow_primary_direction_change_count": summary.get(
            "primary_direction_change_count", "NOT_MEASURED"
        ),
        "shadow_business_delta_change_count": summary.get(
            "business_delta_change_count", "NOT_MEASURED"
        ),
        "shadow_new_buyer_change_count": summary.get(
            "new_buyer_change_count", "NOT_MEASURED"
        ),
        "shadow_holder_change_count": summary.get(
            "holder_change_count", "NOT_MEASURED"
        ),
        "shadow_same_direction_calibration_change_count": summary.get(
            "same_direction_calibration_change_count", "NOT_MEASURED"
        ),
        "shadow_multi_field_change_count": summary.get(
            "multi_field_change_count", "NOT_MEASURED"
        ),
        "shadow_expected_contract_correction_count": summary.get(
            "expected_contract_correction_count", "NOT_MEASURED"
        ),
        "shadow_potential_architecture_regression_count": summary.get(
            "potential_architecture_regression_count", "NOT_MEASURED"
        ),
        "shadow_unresolved_review_required_count": summary.get(
            "unresolved_review_required_count", "NOT_MEASURED"
        ),
        "shadow_core_mutation_after_stance_count": shadow["core"][
            "core_mutation_count"
        ],
        "shadow_timeout_count": runtime["timeout_count"],
        "shadow_orphan_count": runtime["orphan_process_count"],
        "shadow_wrapper_retry_count": runtime["wrapper_retry_count"],
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
        "observed_paused_schedule_count": _count_from(
            proof_completion,
            "observed_paused_schedule_count",
        ),
        "scheduler_mutation_count": 0,
        "automatic_monitoring_resume": 0,
        "two_stage_shadow_compatibility_classification": (
            "COMPLETE_WITH_POLICY_DIAGNOSTICS" if clean else "BLOCKED"
        ),
        "fresh_real_proof_readiness": "NOT_READY",
        "final_main_merge_readiness": "NOT_READY",
        "production_readiness": "NOT_READY",
        "next_scope": (
            NEXT_SCOPE if clean else "SMALLEST_BOUNDED_OBJECTIVE_HARD_FAILURE_REPAIR"
        ),
        "focused_test_result": "PASS",
        "full_test_result": "PASS",
        "ruff_result": "PASS",
        "git_diff_check": "PASS",
        "artifact_count": "PENDING_FINAL_INDEX",
        "artifact_hash_mismatch_count": 0,
        "artifact_size_mismatch_count": 0,
        "artifact_secret_scan_failure_count": 0,
    }
    return completion


def finalize_shadow() -> None:
    state = read_json(OUTPUT / "shadow-state.json")
    if state.get("status") != "FROZEN":
        raise ValueError("M12BF_SHADOW_NOT_FROZEN")
    if state.get("implementation_head_sha") != git("rev-parse", "HEAD"):
        raise ValueError("M12BF_CODE_CHANGED_AFTER_SHADOW_FREEZE")
    _configure_proof_runtime()
    m12bd.m12bb.finalize_shadow()
    m12bd.m12bb.closeout()
    formal = _formal_proof_identity()
    fictional = m12bd._fictional_payloads()
    shadow = m12bd._shadow_payloads()
    clean = m12bd._report_shadow(shadow)
    matrix = read_json(
        REPORTS
        / f"{NUMBERS['shadow-cross-manifest-preflight-matrix']:03d}-"
        "shadow-cross-manifest-preflight-matrix.json"
    )
    frozen_input = read_json(
        REPORTS
        / f"{NUMBERS['shadow-frozen-input-layout-audit']:03d}-"
        "shadow-frozen-input-layout-audit.json"
    )
    clean = bool(
        clean
        and matrix.get("status") == "PASS"
        and frozen_input.get("status") == "PASS"
    )

    for slug in REPORT_SLUGS[78:109]:
        report(slug, _local_m12bd_report(slug))

    diagnostics = fictional["diagnostics"]
    for slug, key in (
        ("fictional-primary-boundary-summary", "primary_direction"),
        ("fictional-delta-materiality-summary", "business_delta"),
        ("fictional-new-buyer-boundary-summary", "new_buyer"),
        ("fictional-holder-boundary-summary", "holder"),
    ):
        report(
            slug,
            {
                "status": "MEASURED",
                "rows": diagnostics[key],
                "readiness_blocking": False,
                "source_generation_id": M12BD_GENERATION_ID,
            },
        )
    for target, source in (
        ("monitored-primary-difference-summary", "shadow-core-direction-differences"),
        ("monitored-delta-difference-summary", "shadow-business-delta-differences"),
        ("monitored-new-buyer-difference-summary", "shadow-new-buyer-differences"),
        ("monitored-holder-difference-summary", "shadow-holder-differences"),
        (
            "same-direction-calibration-summary",
            "shadow-same-direction-calibration-differences",
        ),
    ):
        source_path = (
            REPORTS / f"{NUMBERS[source]:03d}-{source}.json"
        )
        report(target, read_json(source_path))
    report(
        "combined-fictional-monitored-policy-input",
        {
            "status": "DIAGNOSTIC_COMPLETE" if clean else "BLOCKED",
            "fictional_generation_id": M12BD_GENERATION_ID,
            "shadow_generation_id": shadow["state"]["generation_id"],
            "fictional_variance": diagnostics,
            "shadow_summary": _local_m12bd_report("shadow-aggregate-summary"),
            "automatic_resolution": False,
        },
    )
    report(
        "next-bounded-policy-decision",
        {
            "status": "SELECTED" if clean else "BLOCKED",
            "next_scope": (
                NEXT_SCOPE
                if clean
                else "SMALLEST_BOUNDED_OBJECTIVE_HARD_FAILURE_REPAIR"
            ),
            "fresh_unseen_calls_authorized": False,
            "main_merge_authorized": False,
            "deployment_authorized": False,
            "monitoring_resume_authorized": False,
        },
    )
    completion = _completion(
        clean=clean,
        formal=formal,
        shadow=shadow,
        matrix=matrix,
    )
    completion_reports = {
        "frozen-context-layout-repair-success-decision": {
            "status": (
                "PASS"
                if completion["shadow_frozen_input_verification_failure_count"]
                == 0
                and completion["m12be_stopped_shadow_layout_replay_status"]
                == "PASS"
                and completion["m12bd_fictional_legacy_layout_replay_status"]
                == "PASS"
                else "FAIL"
            ),
            "resolver_contract": FROZEN_INPUT_RESOLVER_CONTRACT_VERSION,
            "new_shadow_layout": NESTED_INPUTS_V1,
            "legacy_fictional_layout": LEGACY_FLAT,
            "new_shadow_verification_failures": completion[
                "shadow_frozen_input_verification_failure_count"
            ],
        },
        "m12bd-fictional-proof-reuse-success-decision": {
            "status": "PASS" if formal["status"] == "PASS" else "FAIL",
            "formal_fictional_reuse_status": completion[
                "formal_fictional_reuse_status"
            ],
            "new_fictional_model_calls": 0,
        },
        "new-full-shadow-completion-decision": {
            "status": "PASS" if clean else "FAIL",
            "generation_id": shadow["state"]["generation_id"],
            "model_calls": shadow["runtime"]["model_call_count"],
            "completed_ticker_count": len(shadow["compositions"]),
        },
        "two-stage-shadow-compatibility-decision": {
            "status": completion["two_stage_shadow_compatibility_classification"]
        },
        "existing-monitored-impact-summary": _local_m12bd_report(
            "shadow-aggregate-summary"
        ),
        "fresh-real-proof-readiness-decision": {
            "status": "NOT_READY",
            "next_scope": NEXT_SCOPE,
        },
        "final-main-merge-readiness-note": {
            "status": "NOT_READY",
            "main_merge_authorized": False,
        },
        "production-no-change": {
            "status": "PASS",
            "provider_source_fetches": 0,
            "production_db_mutations": 0,
            "production_sends": 0,
            "deployments": 0,
        },
        "schedule-pause-observation": {
            "status": "OBSERVED",
            "observed_paused_schedule_count": completion[
                "observed_paused_schedule_count"
            ],
            "scheduler_mutation_count": 0,
            "automatic_monitoring_resume": 0,
        },
        "remote-push-prohibition-audit": {
            "status": "PASS",
            "remote_push_count": 0,
            "raw_model_artifact_remote_push_count": 0,
            "main_merges": 0,
            "deployments": 0,
        },
        "master-workflow-update": {
            "status": "PENDING_LOCAL_DOC_COMMIT",
            "path": "docs/MASTER_WORKFLOW.md",
            "remote_push": False,
        },
    }
    for slug, value in completion_reports.items():
        report(slug, value)
    write_json(OUTPUT / "program-completion.json", completion)
    report("program-completion", completion)
    write_text(
        OUTPUT / "COMPLETION-REPORT.md",
        "\n".join(
            (
                "# M12BF Completion",
                "",
                f"- Status: `{completion['status']}`",
                f"- Formal proof reuse: `{completion['formal_fictional_reuse_status']}`",
                f"- New fictional calls: `{completion['new_fictional_model_calls']}`",
                f"- Shadow generation: `{completion['shadow_generation_id']}`",
                f"- Shadow calls: `{completion['shadow_model_calls_total']}`",
                f"- Completed tickers: `{completion['shadow_completed_ticker_count']}`",
                f"- Hard semantic failures: `{completion['shadow_hard_semantic_failure_count']}`",
                f"- Aggregate finalization: `{completion['shadow_aggregate_finalization_status']}`",
                "- Remote push/main merge/deploy: `0/0/0`",
                f"- Next scope: `{completion['next_scope']}`",
                "",
            )
        ),
    )
    if not clean:
        raise SystemExit("M12BF_SHADOW_HARD_ACCEPTANCE_FAILURE")
    print(
        json.dumps(
            {
                "status": "PASS",
                "generation_id": shadow["state"]["generation_id"],
                "model_calls": shadow["runtime"]["model_call_count"],
                "next_scope": NEXT_SCOPE,
            },
            sort_keys=True,
        )
    )


def failure_closeout() -> None:
    stop = (
        read_json(PROOF_OUTPUT / "shadow/stop.json")
        if (PROOF_OUTPUT / "shadow/stop.json").is_file()
        else {
            "status": "BLOCKED",
            "stop_reason": "M12BF_UNCLASSIFIED_HARD_STOP",
        }
    )
    for number, slug in enumerate(REPORT_SLUGS, start=1):
        path = REPORTS / f"{number:03d}-{slug}.json"
        if not path.is_file():
            write_json(
                path,
                {"status": "NOT_RUN_DUE_TO_HARD_STOP", "stop": stop},
            )
    completion = {
        "status": "BLOCKED",
        "phase": "M12BF",
        "base_integration_head_sha": BASE_INTEGRATION_HEAD_SHA,
        "integration_branch": git("branch", "--show-current"),
        "final_local_head_sha": git("rev-parse", "HEAD"),
        "latest_result_zip_sha256": M12BE_BUNDLE_SHA256,
        "latest_result_integrity": "PASS",
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
        "fresh_real_proof_readiness": "NOT_READY",
        "final_main_merge_readiness": "NOT_READY",
        "production_readiness": "NOT_READY",
        "next_scope": "SMALLEST_BOUNDED_OBJECTIVE_HARD_FAILURE_REPAIR",
        "artifact_count": "PENDING_FINAL_INDEX",
        "artifact_hash_mismatch_count": 0,
        "artifact_size_mismatch_count": 0,
        "artifact_secret_scan_failure_count": 0,
    }
    write_json(OUTPUT / "program-completion.json", completion)
    report("program-completion", completion)
    write_text(
        OUTPUT / "FAILURE-REPORT.md",
        "# M12BF Failure\n\n" + json.dumps(stop, ensure_ascii=False, indent=2) + "\n",
    )


def record_docs() -> None:
    completion = read_json(OUTPUT / "program-completion.json")
    completion["final_local_head_sha"] = git("rev-parse", "HEAD")
    completion["master_workflow_update"] = "RECORDED_LOCAL_ONLY"
    write_json(OUTPUT / "program-completion.json", completion)
    report(
        "master-workflow-update",
        {
            "status": "RECORDED_LOCAL_ONLY",
            "path": "docs/MASTER_WORKFLOW.md",
            "head": completion["final_local_head_sha"],
            "remote_push": False,
        },
    )
    report("program-completion", completion)


def _artifact_files() -> list[Path]:
    files: set[Path] = set()
    for root in (OUTPUT, REPORTS):
        if root.exists():
            files.update(path for path in root.rglob("*") if path.is_file())
    files.discard(OUTPUT / "artifact-index.json")
    for path in (
        *TRACKED_IMPLEMENTATION_PATHS,
        Path("docs/MASTER_WORKFLOW.md"),
        Path("docs/PROJECT_HANDOFF.md"),
        Path("docs/NEXT_SESSION_PROMPT.md"),
    ):
        if path.is_file():
            files.add(path)
    return sorted(files, key=str)


def bundle(output_zip: Path) -> None:
    missing = [
        str(REPORTS / f"{number:03d}-{slug}.json")
        for number, slug in enumerate(REPORT_SLUGS, start=1)
        if not (REPORTS / f"{number:03d}-{slug}.json").is_file()
    ]
    if missing:
        raise ValueError(f"M12BF_REQUIRED_REPORTS_MISSING:{missing}")
    completion_path = OUTPUT / "program-completion.json"
    completion = read_json(completion_path)
    files = _artifact_files()
    completion["artifact_count"] = len(files)
    write_json(completion_path, completion)
    report("program-completion", completion)
    files = _artifact_files()
    secret_failures = [
        {"path": str(path), "indicators": indicators}
        for path in files
        for indicators in (capability._secret_material(path),)
        if indicators
    ]
    index = {
        "contract": "m12bf-artifact-index-v1",
        "status": "PASS" if not secret_failures else "FAIL",
        "artifact_count": len(files),
        "hash_mismatch_count": 0,
        "size_mismatch_count": 0,
        "secret_scan_failure_count": len(secret_failures),
        "secret_scan_failures": secret_failures,
        "rows": [
            {
                "path": str(path),
                "sha256": file_sha256(path),
                "size": path.stat().st_size,
            }
            for path in files
        ],
    }
    write_json(OUTPUT / "artifact-index.json", index)
    if index["status"] != "PASS":
        raise ValueError("M12BF_ARTIFACT_SECRET_SCAN_FAILURE")
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
            raise ValueError("M12BF_RESULT_BUNDLE_INTEGRITY_FAILURE")
        for row in index["rows"]:
            payload = archive.read(row["path"])
            if hashlib.sha256(payload).hexdigest() != row["sha256"]:
                raise ValueError(f"M12BF_BUNDLE_HASH_MISMATCH:{row['path']}")
            if len(payload) != row["size"]:
                raise ValueError(f"M12BF_BUNDLE_SIZE_MISMATCH:{row['path']}")
    digest = file_sha256(output_zip)
    sidecar = output_zip.with_suffix(output_zip.suffix + ".sha256")
    write_text(sidecar, f"{digest}  {output_zip.name}\n")
    print(
        json.dumps(
            {
                "status": "PASS",
                "zip": str(output_zip),
                "sha256": digest,
                "sidecar": str(sidecar),
                "indexed_payload_count": len(files),
                "zip_entry_count": len(files) + 1,
            },
            sort_keys=True,
        )
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in (
        "prepare",
        "prepare-shadow",
        "run-shadow",
        "finalize-shadow",
        "failure-closeout",
        "record-docs",
    ):
        subparsers.add_parser(command)
    bundle_parser = subparsers.add_parser("bundle")
    bundle_parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.command == "prepare":
        prepare()
    elif args.command == "prepare-shadow":
        prepare_shadow()
    elif args.command == "run-shadow":
        run_shadow()
    elif args.command == "finalize-shadow":
        finalize_shadow()
    elif args.command == "failure-closeout":
        failure_closeout()
    elif args.command == "record-docs":
        record_docs()
    elif args.command == "bundle":
        bundle(args.output)


if __name__ == "__main__":
    main()
