from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import traceback
import zipfile
from collections import Counter
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from scripts.m12cn_policy_contract import build_subject_catalog
from scripts.m12cn_policy_shadow import (
    classify_shadow_failure,
    comparison_markdown,
    compare_three_sets,
    extract_three_axis_rows,
    runtime_integrity,
)
from scripts.m12cq_two_pass_contract import (
    PASS_A_CONTRACT,
    PASS_B_CONTRACT,
    PassABatchOutput,
    PassBBatchOutput,
    build_pass_a_subject_context,
    build_pass_b_subject_context,
    canonical_sha256,
    generic_control_matrix,
    materialize_policy_entry_range,
    pass_a_batch_schema,
    pass_a_leakage_scan,
    pass_a_prompt,
    pass_b_batch_schema,
    pass_b_prompt,
    schema_preflight,
    select_matrix_option,
    validate_new_buyer_consistency,
    validate_pass_a_batch,
    validate_pass_b_batch,
)


REPO = Path(__file__).resolve().parents[1]
KST = ZoneInfo("Asia/Seoul")
REQUIRED_RUNTIME_BASE = "831890d1bf0dff303f67a6e0de1403ad3221b5d8"
M12CP_IMPLEMENTATION = "491eaef3172f5234d244f2627a57776528f2768d"
WORK_INSTRUCTION_COMMIT = "8f75c719e5f10c50d3a57a574fe7d140d9009e14"
EXPECTED_FROZEN_GENERATION = "20260917-m12cm-current-v4-smoke-20260917T062918Z-5c0cb075ce8b"
EXPECTED_POPULATION = {
    "us": (
        "CORZ",
        "CPNG",
        "CRCL",
        "GOOGL",
        "HUT",
        "IBM",
        "MU",
        "RXRX",
        "SKHY",
        "SNDK",
        "TSLA",
        "TSM",
        "WRD",
        "WULF",
    ),
    "kr": (
        "000660",
        "003690",
        "005490",
        "005930",
        "010120",
        "012450",
        "047810",
        "086280",
    ),
}
EXPECTED_PACKAGE_HASHES = {
    "inputs/m12cm-shadow-input.zip": (
        "9482ee37f0df9bf26bc8a2d6d36fcb6c1af836b06405776e9947c7fbd18b03aa"
    ),
    "inputs/m12cm-shadow-input-manifest.json": (
        "9b5763a4ef3481e388db77ce5c479244177cbed3e03e313a659f7317451a310e"
    ),
    "inputs/policy-principles.json": (
        "1cbda3115fe26681917a6bd46499a3987e449c9a18f14f19ef8fa7f331e11310"
    ),
    (
        "sources/thesis-monitor-20260917-m12cp-archetype-valuation-policy-regime-tier-"
        "and-scenario-source-coverage-report.zip"
    ): "fe63ee201bdb0937a4936af0d89f7013adee0209b3ef01d83d210d0e93456100",
    "post-freeze-reference/post-freeze-reference.zip": (
        "e83f77f4e1872c54c08ef9dca00c4c8f7c07446390c3f40c1ba1d9d5e6f9843f"
    ),
}
M12CP_REPORT_NAME = (
    "thesis-monitor-20260917-m12cp-archetype-valuation-policy-regime-tier-and-"
    "scenario-source-coverage-report.zip"
)
COMPLETION_PASS = "M12CQ_TWO_PASS_POLICY_CALIBRATION_SHADOW_PASS_READY_FOR_CHAT_REVIEW"
COMPLETION_PASS_A_FAILED = "M12CQ_PASS_A_FAILED"
COMPLETION_MATERIALIZATION_FAILED = "M12CQ_FUNDAMENTAL_MATERIALIZATION_FAILED"
COMPLETION_PASS_B_FAILED = "M12CQ_PASS_B_FAILED"
COMPLETION_BLINDNESS_FAILED = "M12CQ_BLINDNESS_OR_TARGET_LEAK_FAILURE"
COMPLETION_NEW_DEPENDENCY = "M12CQ_NEW_PRODUCTION_DEPENDENCY_REQUIRES_CHAT"


class M12CQFailure(RuntimeError):
    pass


def require(condition: bool, code: str) -> None:
    if not condition:
        raise M12CQFailure(code)


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise M12CQFailure(f"expected_json_object:{path.name}")
    return value


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, default=str) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(value.rstrip() + "\n", encoding="utf-8")
    temporary.replace(path)


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_text(*args: str) -> str:
    return subprocess.run(
        ("git", *args),
        cwd=REPO,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _single_member(archive: zipfile.ZipFile, suffix: str) -> str:
    names = [name for name in archive.namelist() if name.endswith(suffix)]
    if len(names) != 1:
        raise M12CQFailure(f"archive_member_cardinality:{suffix}:{len(names)}")
    return names[0]


def _read_zip_json(archive: zipfile.ZipFile, suffix: str) -> dict[str, Any]:
    value = json.loads(archive.read(_single_member(archive, suffix)).decode("utf-8"))
    if not isinstance(value, dict):
        raise M12CQFailure(f"zip_json_not_object:{suffix}")
    return value


def _verify_artifact_manifest(
    archive: zipfile.ZipFile,
    *,
    expected_payload_count: int,
) -> dict[str, object]:
    manifest_name = _single_member(archive, "/artifact-manifest.json")
    prefix = manifest_name.removesuffix("artifact-manifest.json")
    manifest = json.loads(archive.read(manifest_name).decode("utf-8"))
    rows: list[dict[str, object]] = []
    errors: list[str] = []
    for item in manifest.get("files") or []:
        relative = str(item["path"])
        name = f"{prefix}{relative}"
        try:
            raw = archive.read(name)
        except KeyError:
            raw = b""
            actual_sha = None
            actual_size = None
        else:
            actual_sha = sha256_bytes(raw)
            actual_size = len(raw)
        status = (
            "PASS"
            if actual_sha == item.get("sha256") and actual_size == item.get("size")
            else "FAIL"
        )
        rows.append(
            {
                "path": relative,
                "expected_sha256": item.get("sha256"),
                "actual_sha256": actual_sha,
                "expected_size": item.get("size"),
                "actual_size": actual_size,
                "status": status,
            }
        )
        if status != "PASS":
            errors.append(f"manifest_payload_mismatch:{relative}")
    if len(rows) != expected_payload_count:
        errors.append(f"manifest_payload_count:{len(rows)}")
    return {
        "declared_payload_count": len(rows),
        "expected_payload_count": expected_payload_count,
        "rows": rows,
        "errors": errors,
        "status": "PASS" if not errors else "FAIL",
    }


def verify_sources(package_root: Path, shadow_input_root: Path) -> dict[str, object]:
    errors: list[str] = []
    package_rows: list[dict[str, object]] = []
    for relative, expected in EXPECTED_PACKAGE_HASHES.items():
        path = package_root / relative
        actual = sha256_file(path) if path.is_file() else None
        status = "PASS" if actual == expected else "FAIL"
        package_rows.append(
            {
                "path": relative,
                "expected_sha256": expected,
                "actual_sha256": actual,
                "status": status,
            }
        )
        if status != "PASS":
            errors.append(f"source_hash_mismatch:{relative}")
    package_manifest = read_json(package_root / "package-manifest.json")
    for item in package_manifest.get("files") or []:
        path = package_root / str(item["path"])
        if (
            not path.is_file()
            or sha256_file(path) != item["sha256"]
            or path.stat().st_size != item["size"]
        ):
            errors.append(f"package_manifest_mismatch:{item['path']}")
    shadow_manifest = read_json(package_root / "inputs/m12cm-shadow-input-manifest.json")
    shadow_rows: list[dict[str, object]] = []
    for item in shadow_manifest.get("selected_files") or []:
        path = shadow_input_root / str(item["path"])
        actual = sha256_file(path) if path.is_file() else None
        status = (
            "PASS" if actual == item["sha256"] and path.stat().st_size == item["size"] else "FAIL"
        )
        shadow_rows.append(
            {
                "path": item["path"],
                "expected_sha256": item["sha256"],
                "actual_sha256": actual,
                "status": status,
            }
        )
        if status != "PASS":
            errors.append(f"shadow_input_mismatch:{item['path']}")
    report_path = package_root / "sources" / M12CP_REPORT_NAME
    with zipfile.ZipFile(report_path) as archive:
        report_manifest = _verify_artifact_manifest(archive, expected_payload_count=37)
    if report_manifest["status"] != "PASS":
        errors.extend(str(value) for value in report_manifest["errors"])
    return {
        "contract": "m12cq-source-base-integrity-v1",
        "m12cp_implementation": M12CP_IMPLEMENTATION,
        "required_runtime_base": REQUIRED_RUNTIME_BASE,
        "frozen_generation": EXPECTED_FROZEN_GENERATION,
        "package_payload_count": len(package_manifest.get("files") or []),
        "package_sources": package_rows,
        "shadow_input_files": shadow_rows,
        "m12cp_report_manifest": report_manifest,
        "post_freeze_reference_access_before_shadow_freeze": "HASH_ONLY",
        "post_freeze_semantic_open_count": 0,
        "errors": errors,
        "status": "PASS" if not errors else "FAIL",
    }


def load_m12cp_inputs(package_root: Path) -> dict[str, object]:
    report_path = package_root / "sources" / M12CP_REPORT_NAME
    with zipfile.ZipFile(report_path) as archive:
        options = _read_zip_json(archive, "/policy-selectable-entry-options-22.json")
        security = _read_zip_json(archive, "/depositary-security-basis-coverage.json")
        completion = _read_zip_json(archive, "/program-completion.json")
        policy = _read_zip_json(archive, "/m12co-chat-policy-selection.json")
    require(options.get("subject_count") == 22, "m12cp_option_subject_count_mismatch")
    require(
        completion.get("completion_state")
        == "M12CP_SCENARIO_SOURCE_COVERAGE_INSUFFICIENT_BUT_HISTORICAL_POLICY_READY",
        "m12cp_completion_mismatch",
    )
    return {
        "options": options,
        "security": security,
        "completion": completion,
        "policy": policy,
    }


def _run_command(
    *,
    name: str,
    command: Sequence[str],
    output_dir: Path,
    env: Mapping[str, str],
) -> dict[str, object]:
    output_dir.mkdir(parents=True, exist_ok=True)
    completed = subprocess.run(
        tuple(command),
        cwd=REPO,
        env=dict(env),
        check=False,
        capture_output=True,
        text=True,
    )
    log = output_dir / f"{name}.log"
    write_text(log, completed.stdout + completed.stderr)
    return {
        "name": name,
        "command": list(command),
        "exit_code": completed.returncode,
        "log": str(log.name),
        "status": "PASS" if completed.returncode == 0 else "FAIL",
    }


def run_precall_validation(result_root: Path) -> dict[str, object]:
    validation = result_root / "validation/precall"
    env = os.environ.copy()
    focused = _run_command(
        name="focused",
        command=(
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "tests/test_m12cq_two_pass_policy_shadow.py",
            "tests/test_m12cp_valuation_policy.py",
            "tests/test_m12co_entry_range_design.py",
            "tests/test_m12cn_policy_contract.py",
            f"--junitxml={validation / 'focused-junit.xml'}",
        ),
        output_dir=validation,
        env=env,
    )
    result = {
        "contract": "m12cq-precall-validation-v1",
        "commands": [focused],
        "external_model_calls": 0,
        "status": focused["status"],
    }
    write_json(validation / "summary.json", result)
    return result


def run_postcall_validation(result_root: Path) -> dict[str, object]:
    validation = result_root / "validation/postcall"
    env = os.environ.copy()
    tests = {
        "focused": (
            "tests/test_m12cq_two_pass_policy_shadow.py",
            "tests/test_m12cp_valuation_policy.py",
            "tests/test_m12co_entry_range_design.py",
            "tests/test_m12cn_policy_contract.py",
            "tests/test_accepted_decision_v2_runtime.py",
            "tests/test_stage2_maturity_polarity_adapter.py",
        ),
        "frozen-contract": (
            "tests/test_m12cq_two_pass_policy_shadow.py",
            "tests/test_m12cn_policy_contract.py",
        ),
        "treasury-krx": (
            "tests/test_fred_provider.py",
            "tests/test_krx_night_futures_probe.py",
            "tests/test_krx_night_history_service.py",
            "tests/test_krx_night_leading_market_adapter_service.py",
            "tests/test_krx_night_session_contract_service.py",
            "tests/test_market_context_adapter.py",
            "tests/test_night_futures_session_mapping_service.py",
            "tests/test_night_futures_summary_canonicalization.py",
            "tests/test_night_futures_visibility_service.py",
            "tests/test_structured_market_data_quality_v2.py",
        ),
        "full": (),
    }
    rows: list[dict[str, object]] = []
    for name, paths in tests.items():
        command = [sys.executable, "-m", "pytest", "-q", *paths]
        command.append(f"--junitxml={validation / f'{name}-junit.xml'}")
        rows.append(
            _run_command(
                name=name,
                command=command,
                output_dir=validation,
                env=env,
            )
        )
    ruff = str(Path(sys.executable).with_name("ruff"))
    targets = (
        "scripts/m12cq_two_pass_contract.py",
        "scripts/m12cq_two_pass_shadow.py",
        "tests/test_m12cq_two_pass_policy_shadow.py",
    )
    rows.append(
        _run_command(
            name="ruff",
            command=(ruff, "check", *targets),
            output_dir=validation,
            env=env,
        )
    )
    rows.append(
        _run_command(
            name="ruff-format",
            command=(ruff, "format", "--check", *targets),
            output_dir=validation,
            env=env,
        )
    )
    rows.append(
        _run_command(
            name="diff-check",
            command=("git", "diff", "--check"),
            output_dir=validation,
            env=env,
        )
    )
    full_log = (validation / "full.log").read_text(encoding="utf-8")
    skipped_match = re.search(r"(\d+) skipped", full_log)
    skipped = int(skipped_match.group(1)) if skipped_match else 0
    if skipped > 63:
        rows.append(
            {
                "name": "skip-inflation",
                "exit_code": 1,
                "baseline_skipped": 63,
                "actual_skipped": skipped,
                "status": "FAIL",
            }
        )
    result = {
        "contract": "m12cq-postcall-validation-v1",
        "commands": rows,
        "baseline_skipped": 63,
        "actual_skipped": skipped,
        "status": "PASS" if all(row["status"] == "PASS" for row in rows) else "FAIL",
    }
    write_json(validation / "summary.json", result)
    return result


def _batch_specs(
    *,
    stage: str,
    generation_id: str,
    contexts: Mapping[str, Any],
    payloads: Mapping[str, Mapping[str, Mapping[str, object]]],
    catalogs: Mapping[str, Mapping[str, Mapping[str, object]]],
    policy: Mapping[str, object],
    result_root: Path,
) -> tuple[list[dict[str, object]], list[Path]]:
    specs: list[dict[str, object]] = []
    model_paths: list[Path] = []
    for market in ("us", "kr"):
        context = contexts[market]
        subjects = tuple(context.selected_subjects)
        for offset in range(0, len(subjects), 3):
            batch = offset // 3 + 1
            batch_subjects = subjects[offset : offset + 3]
            identity = {
                "contract": PASS_A_CONTRACT if stage == "pass-a" else PASS_B_CONTRACT,
                "generation_id": generation_id,
                "packet_id": context.packet_id,
                "market": market,
                "assessment_date": context.assessment_date,
                "expected_subjects": list(batch_subjects),
            }
            subject_payloads = [payloads[market][ticker] for ticker in batch_subjects]
            directory = result_root / "model-inputs" / stage / market / f"batch-{batch:02d}"
            prompt_path = directory / "prompt.txt"
            schema_path = directory / "schema.json"
            catalog_path = directory / "ref-catalog.json"
            subject_path = directory / "subject-context.json"
            identity_path = directory / "identity.json"
            if stage == "pass-a":
                prompt = pass_a_prompt(
                    identity=identity,
                    policy_principles=policy,
                    subject_contexts=subject_payloads,
                )
                schema = pass_a_batch_schema(
                    generation_id=generation_id,
                    packet_id=context.packet_id,
                    market=market,
                    assessment_date=context.assessment_date,
                    subjects=batch_subjects,
                    subject_contexts=payloads[market],
                )
                ref_catalog = {
                    ticker: {
                        "eligible_claim_refs": payloads[market][ticker]["eligible_claim_refs"],
                        "premium_eligible_claim_refs": payloads[market][ticker][
                            "premium_eligible_claim_refs"
                        ],
                        "data_quality_catalog": payloads[market][ticker]["data_quality_catalog"],
                    }
                    for ticker in batch_subjects
                }
            else:
                prompt = pass_b_prompt(
                    identity=identity,
                    policy_principles=policy,
                    subject_contexts=subject_payloads,
                )
                schema = pass_b_batch_schema(
                    generation_id=generation_id,
                    packet_id=context.packet_id,
                    market=market,
                    assessment_date=context.assessment_date,
                    subjects=batch_subjects,
                    catalogs=catalogs[market],
                )
                ref_catalog = {
                    ticker: {
                        "claim_refs": catalogs[market][ticker]["claim_refs"],
                        "core_evidence_refs": catalogs[market][ticker]["core_evidence_refs"],
                        "timing_evidence_refs": catalogs[market][ticker]["timing_evidence_refs"],
                        "tactical_candidate_ids": [
                            row["candidate_id"]
                            for row in catalogs[market][ticker]["entry_catalog"].get(
                                "tactical_candidates"
                            )
                            or []
                        ],
                    }
                    for ticker in batch_subjects
                }
            write_text(prompt_path, prompt)
            write_json(schema_path, schema)
            write_json(catalog_path, {"subjects": list(batch_subjects), "catalogs": ref_catalog})
            write_json(subject_path, {"subjects": subject_payloads})
            write_json(identity_path, identity)
            model_paths.extend(
                (prompt_path, schema_path, catalog_path, subject_path, identity_path)
            )
            specs.append(
                {
                    "stage": stage,
                    "market": market,
                    "batch": batch,
                    "subjects": batch_subjects,
                    "identity": identity,
                    "prompt": prompt_path,
                    "schema": schema_path,
                    "catalog": catalog_path,
                }
            )
    require(len(specs) == 8, f"{stage}_planned_call_count_not_8")
    return specs, model_paths


def _schema_suite(specs: Sequence[Mapping[str, object]], *, stage: str) -> dict[str, object]:
    rows = []
    for spec in specs:
        scan = schema_preflight(read_json(Path(spec["schema"])))
        rows.append(
            {
                "market": spec["market"],
                "batch": spec["batch"],
                "subjects": list(spec["subjects"]),
                "scan": scan,
                "status": scan["status"],
            }
        )
    return {
        "contract": f"m12cq-{stage}-schema-and-validator-v1",
        "schema_count": len(rows),
        "rows": rows,
        "status": "PASS"
        if len(rows) == 8 and all(row["status"] == "PASS" for row in rows)
        else "FAIL",
    }


def _assert_frozen_head(expected_head: str, code_hashes: Mapping[str, str]) -> None:
    require(git_text("rev-parse", "HEAD") == expected_head, "head_drift_after_freeze")
    require(not git_text("status", "--porcelain"), "worktree_drift_after_freeze")
    for relative, expected in code_hashes.items():
        require(sha256_file(REPO / relative) == expected, f"code_hash_drift:{relative}")


def _invoke_stage(
    *,
    stage: str,
    specs: Sequence[Mapping[str, object]],
    catalogs: Mapping[str, Mapping[str, Mapping[str, object]]],
    pass_a_contexts: Mapping[str, Mapping[str, Mapping[str, object]]],
    pass_a_by_ticker: Mapping[str, Mapping[str, object]],
    result_root: Path,
    expected_head: str,
    code_hashes: Mapping[str, str],
    runtime: Any,
    codex_bin: str,
    timeout: int,
    call_rows: list[dict[str, object]],
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    outputs: list[dict[str, object]] = []
    frozen_rows: list[dict[str, object]] = []
    for stage_ordinal, spec in enumerate(specs, start=1):
        _assert_frozen_head(expected_head, code_hashes)
        market = str(spec["market"])
        batch = int(spec["batch"])
        call_dir = result_root / "model-calls" / stage / market / f"batch-{batch:02d}"
        output_path = call_dir / "raw-output.json"
        log_path = call_dir / "transport.log"
        overall_ordinal = len(call_rows) + 1
        ledger = {
            "ordinal": overall_ordinal,
            "stage_ordinal": stage_ordinal,
            "stage": stage,
            "market": market,
            "batch": batch,
            "subjects": list(spec["subjects"]),
            "prompt_sha256": sha256_file(Path(spec["prompt"])),
            "schema_sha256": sha256_file(Path(spec["schema"])),
            "ref_catalog_sha256": sha256_file(Path(spec["catalog"])),
            "status": "STARTED",
            "started_at": datetime.now(UTC).isoformat(),
        }
        call_rows.append(ledger)
        write_json(result_root / "model-call-ledger.json", {"calls": call_rows})
        print(
            f"START {stage} {stage_ordinal}/8 {market} batch={batch} "
            f"subjects={','.join(spec['subjects'])}",
            flush=True,
        )
        execution_stage = "TRANSPORT"
        try:
            receipt = runtime._invoke_signed_in_codex(
                codex_bin=codex_bin,
                prompt=spec["prompt"],
                output=output_path,
                log=log_path,
                schema=spec["schema"],
                cwd=REPO,
                timeout=timeout,
                state_namespace=(
                    f"m12cq:{spec['identity']['generation_id']}:{stage}:{market}:batch-{batch:02d}"
                ),
            )
            require(int(receipt.get("transport_attempts") or 0) == 1, "transport_retry_detected")
            raw_sha = sha256_file(output_path)
            frozen = result_root / "output-freeze" / stage / market / f"batch-{batch:02d}.json"
            frozen.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(output_path, frozen)
            require(sha256_file(frozen) == raw_sha, "raw_output_freeze_mismatch")
            execution_stage = "OUTPUT_PARSE"
            if stage == "pass-a":
                parsed = PassABatchOutput.model_validate(read_json(output_path))
                execution_stage = "PASS_A_SEMANTIC_VALIDATION"
                validation = validate_pass_a_batch(
                    parsed,
                    expected_identity=spec["identity"],
                    subjects=spec["subjects"],
                    subject_contexts=pass_a_contexts[market],
                )
                rows = [row.model_dump(mode="json") for row in parsed.classifications]
            else:
                parsed = PassBBatchOutput.model_validate(read_json(output_path))
                execution_stage = "PASS_B_SEMANTIC_VALIDATION"
                validation = validate_pass_b_batch(
                    parsed,
                    expected_identity=spec["identity"],
                    subjects=spec["subjects"],
                    catalogs=catalogs[market],
                    pass_a_by_ticker=pass_a_by_ticker,
                )
                rows = [row.model_dump(mode="json") for row in parsed.decisions]
            write_json(call_dir / "semantic-validation.json", validation)
            require(validation["status"] == "PASS", f"{stage}_semantic_validation_failed")
            outputs.extend(rows)
            frozen_rows.append(
                {
                    "market": market,
                    "batch": batch,
                    "path": str(frozen.relative_to(result_root)),
                    "sha256": raw_sha,
                    "size": frozen.stat().st_size,
                }
            )
            ledger.update(
                {
                    "status": "PASS",
                    "output_sha256": raw_sha,
                    "subject_count": len(rows),
                    "transport_attempts": receipt.get("transport_attempts"),
                    "network_probe_attempts": receipt.get("network_probe_attempts"),
                    "completed_at": datetime.now(UTC).isoformat(),
                }
            )
            print(f"COMPLETE {stage} {stage_ordinal}/8 {market} batch={batch}", flush=True)
        except BaseException as exc:  # noqa: BLE001
            ledger.update(
                {
                    "status": "FAIL",
                    "safe_error_type": type(exc).__name__,
                    "safe_error_code": str(exc).split(":", 1)[0],
                    "failure_category": classify_shadow_failure(
                        exc,
                        log_path,
                        execution_stage=execution_stage,
                    ),
                    "completed_at": datetime.now(UTC).isoformat(),
                }
            )
            write_text(call_dir / "failure-traceback.txt", traceback.format_exc())
            write_json(result_root / "model-call-ledger.json", {"calls": call_rows})
            raise
        write_json(result_root / "model-call-ledger.json", {"calls": call_rows})
    return outputs, frozen_rows


def _option_subjects(value: Mapping[str, object]) -> dict[str, Mapping[str, object]]:
    return {
        str(row.get("ticker") or ""): row
        for row in value.get("subjects") or []
        if isinstance(row, Mapping)
    }


def _depositary_subjects(value: Mapping[str, object]) -> set[str]:
    rows: list[Mapping[str, object]] = []
    for key in ("rows", "subjects", "cases"):
        candidate = value.get(key)
        if isinstance(candidate, list):
            rows.extend(row for row in candidate if isinstance(row, Mapping))
    result = set()
    for row in rows:
        ticker = str(row.get("ticker") or "")
        if ticker and row.get("affected") is True:
            result.add(ticker)
    return result


def _coverage_analysis(
    rows: Sequence[Mapping[str, object]],
    consistency: Sequence[Mapping[str, object]],
    depositary_subjects: set[str],
) -> dict[str, object]:
    archetypes = Counter(str(row["company_archetype"]) for row in rows)
    tiers = Counter(str(row["valuation_regime_tier"]) for row in rows)
    matrix = Counter(f"{row['company_archetype']}|{row['valuation_regime_tier']}" for row in rows)
    axes = {
        axis: Counter(str(row[axis]) for row in rows)
        for axis in ("overall_direction", "new_buyer", "holder")
    }
    fundamental = Counter(str(row["fundamental_option"]["status"]) for row in rows)
    tactical = Counter(str(row["entry_range"]["tactical_entry_band"]["status"]) for row in rows)
    methods = Counter(
        str(row["entry_range"]["method"])
        for row in rows
        if row["entry_range"]["entry_range_status"] == "ENTRY_RANGE_RESOLVED"
    )
    resolved_wait = [
        {
            "ticker": row["ticker"],
            "current_price": row["entry_range"]["current_price"],
            "current_price_as_of": row["entry_range"]["current_price_as_of"],
            "preferred_entry_low": row["entry_range"]["preferred_entry_low"],
            "preferred_entry_high": row["entry_range"]["preferred_entry_high"],
            "distance_to_band_pct": row["entry_range"]["distance_to_band_pct"],
            "fundamental_method": row["entry_range"]["method"],
            "valuation_regime_tier": row["valuation_regime_tier"],
            "tactical_component": row["entry_range"]["tactical_entry_band"],
            "valuation_basis_refs": row["entry_range"]["valuation_basis_refs"],
            "technical_basis_refs": row["entry_range"]["technical_basis_refs"],
        }
        for row in rows
        if row["new_buyer"] == "WAIT"
        and row["entry_range"]["entry_range_status"] == "ENTRY_RANGE_RESOLVED"
    ]
    return {
        "contract": "m12cq-entry-range-coverage-and-methods-v1",
        "subject_count": len(rows),
        "archetype_distribution": dict(sorted(archetypes.items())),
        "valuation_tier_distribution": dict(sorted(tiers.items())),
        "archetype_tier_matrix": dict(sorted(matrix.items())),
        "axis_distributions": {key: dict(sorted(value.items())) for key, value in axes.items()},
        "buy_wait_holdable_count": sum(
            row["overall_direction"] == "BUY"
            and row["new_buyer"] == "WAIT"
            and row["holder"] == "HOLDABLE"
            for row in rows
        ),
        "wait_count": sum(row["new_buyer"] == "WAIT" for row in rows),
        "fundamental_status": dict(sorted(fundamental.items())),
        "resolved_price_band_methods": dict(sorted(methods.items())),
        "execution_growth_unresolved_count": sum(
            row["company_archetype"] == "EXECUTION_DEPENDENT_GROWTH"
            and row["fundamental_option"]["status"] != "RESOLVED"
            for row in rows
        ),
        "tactical_status": dict(sorted(tactical.items())),
        "wait_with_resolved_preferred_entry_count": len(resolved_wait),
        "wait_with_unresolved_fundamental_count": sum(
            row["new_buyer"] == "WAIT" and row["fundamental_option"]["status"] != "RESOLVED"
            for row in rows
        ),
        "attractive_consistency_case_count": sum(row["new_buyer"] == "ATTRACTIVE" for row in rows),
        "new_buyer_consistency_pass_count": sum(row.get("status") == "PASS" for row in consistency),
        "holder_review_reason_classes": dict(
            sorted(
                Counter(
                    str(row["holder_reason_class"]) for row in rows if row["holder"] == "REVIEW"
                ).items()
            )
        ),
        "data_quality_effect_distribution": dict(
            sorted(Counter(str(row["data_quality_effect"]) for row in rows).items())
        ),
        "depositary_security_basis_unresolved_cases": sorted(
            ticker
            for ticker in depositary_subjects
            if next(row for row in rows if row["ticker"] == ticker)["fundamental_option"]["status"]
            != "RESOLVED"
        ),
        "premium_tier_support": [
            {
                "ticker": row["ticker"],
                "supporting_claim_refs": row["tier_supporting_claim_refs"],
            }
            for row in rows
            if row["valuation_regime_tier"] == "PREMIUM"
        ],
        "method_intersection_cases": [
            row["ticker"]
            for row in rows
            if row["fundamental_option"].get("method_family") == "METHOD_INTERSECTION"
        ],
        "resolved_wait_ranges": resolved_wait,
        "status": "PASS",
    }


def _load_old_axes_from_bytes(raw: bytes) -> dict[str, dict[str, str | None]]:
    rows: dict[str, dict[str, str | None]] = {}
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        names = sorted(
            name for name in archive.namelist() if name.endswith("candidate-output.json")
        )
        require(bool(names), "sealed_candidate_outputs_missing")
        for name in names:
            rows.update(extract_three_axis_rows(json.loads(archive.read(name).decode("utf-8"))))
    return rows


def _post_freeze_comparison(
    *,
    archive_path: Path,
    rows: Sequence[Mapping[str, object]],
    frozen_at: str,
    result_root: Path,
) -> dict[str, object]:
    opened_at = datetime.now(UTC).isoformat()
    require(opened_at > frozen_at, "post_freeze_reference_opened_too_early")
    with zipfile.ZipFile(archive_path) as archive:
        independent = _read_zip_json(archive, "m12cm-independent-assistant-judgment.json")
        sealed_name = _single_member(archive, "m12cm-sealed-ai-verdicts.zip")
        old_rows = _load_old_axes_from_bytes(archive.read(sealed_name))
    independent_rows = extract_three_axis_rows(independent)
    shadow_rows = {str(row["ticker"]): row for row in rows}
    expected = EXPECTED_POPULATION["us"] + EXPECTED_POPULATION["kr"]
    comparison = compare_three_sets(
        old_rows=old_rows,
        independent_rows=independent_rows,
        shadow_rows=shadow_rows,
        expected_tickers=expected,
    )
    comparison["contract"] = "m12cq-post-freeze-three-way-comparison-v1"
    comparison["m12cq_shadow_frozen_at"] = frozen_at
    comparison["post_freeze_reference_opened_at"] = opened_at
    comparison["reference_open_count"] = 1
    comparison["large_core_descriptive_differences"] = [
        item
        for item in comparison["rows"]
        if shadow_rows[item["ticker"]]["company_archetype"]
        in {"DURABLE_FRANCHISE", "STRUCTURAL_CYCLICAL_LEADER", "MATURE_VALUE_DEFENSIVE"}
        and (
            not all(item["old_vs_shadow_axis_match"].values())
            or not all(item["independent_vs_shadow_axis_match"].values())
        )
    ]
    comparison["execution_growth_descriptive_differences"] = [
        item
        for item in comparison["rows"]
        if shadow_rows[item["ticker"]]["company_archetype"] == "EXECUTION_DEPENDENT_GROWTH"
        and (
            not all(item["old_vs_shadow_axis_match"].values())
            or not all(item["independent_vs_shadow_axis_match"].values())
        )
    ]
    comparison["resolved_wait_examples"] = [
        {
            "ticker": row["ticker"],
            "current_price": row["entry_range"]["current_price"],
            "preferred_entry_low": row["entry_range"]["preferred_entry_low"],
            "preferred_entry_high": row["entry_range"]["preferred_entry_high"],
        }
        for row in rows
        if row["new_buyer"] == "WAIT"
        and row["entry_range"]["entry_range_status"] == "ENTRY_RANGE_RESOLVED"
    ]
    comparison["remaining_unresolved_price_coverage"] = sum(
        row["entry_range"]["entry_range_status"] == "ENTRY_RANGE_UNRESOLVED" for row in rows
    )
    write_json(result_root / "post-freeze-three-way-comparison.json", comparison)
    write_text(
        result_root / "post-freeze-three-way-comparison.md",
        comparison_markdown(comparison).replace("M12CN", "M12CQ").replace("m12cn", "m12cq"),
    )
    return comparison


def artifact_manifest(root: Path) -> dict[str, object]:
    rows = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.name == "artifact-manifest.json":
            continue
        rows.append(
            {
                "path": str(path.relative_to(root)),
                "sha256": sha256_file(path),
                "size": path.stat().st_size,
            }
        )
    return {
        "contract": "m12cq-artifact-manifest-v1",
        "file_count": len(rows),
        "files": rows,
    }


def zip_tree(source: Path, destination: Path) -> dict[str, object]:
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    temporary.unlink(missing_ok=True)
    with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(source.rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(source.parent))
    temporary.replace(destination)
    return {
        "path": str(destination),
        "sha256": sha256_file(destination),
        "size": destination.stat().st_size,
    }


def _report_markdown(
    *,
    completion: Mapping[str, object],
    coverage: Mapping[str, object] | None,
    calls: Sequence[Mapping[str, object]],
    validation: Mapping[str, object] | None,
    comparison: Mapping[str, object] | None,
) -> str:
    return "\n".join(
        [
            "# M12CQ Two-Pass Policy Calibration Shadow",
            "",
            f"- Completion: `{completion['completion_state']}`",
            f"- Generation: `{completion.get('generation_id')}`",
            f"- Work-instruction commit: `{WORK_INSTRUCTION_COMMIT}`",
            f"- Implementation commit: `{completion.get('implementation_commit')}`",
            f"- Frozen M12CM generation: `{EXPECTED_FROZEN_GENERATION}`",
            f"- Pass A calls: `{sum(row.get('stage') == 'pass-a' and row.get('status') == 'PASS' for row in calls)}/8`",
            f"- Pass B calls: `{sum(row.get('stage') == 'pass-b' and row.get('status') == 'PASS' for row in calls)}/8`",
            f"- Subjects: `{completion.get('subject_count')}/22`",
            f"- Fundamental resolved/unresolved: `{(coverage or {}).get('fundamental_status')}`",
            f"- BUY/WAIT/HOLDABLE: `{(coverage or {}).get('buy_wait_holdable_count')}`",
            f"- Validation: `{(validation or {}).get('status', 'NOT_REACHED')}`",
            f"- Post-freeze comparison: `{(comparison or {}).get('status', 'NOT_REACHED')}`",
            "- Production runtime/config changes: `0`",
            "- Production send/DB/scheduler/broker actions: `0`",
            "- Main merge / remote push / deploy: `0`",
            "",
            "The shadow separates price-blind archetype/regime classification from current-price/timing decisions. Agreement with prior judgments is descriptive only and was not a pass target.",
        ]
    )


def run(args: argparse.Namespace) -> None:
    result_root = args.result_root.resolve()
    require(not result_root.exists(), "result_root_already_exists")
    result_root.mkdir(parents=True)
    runtime_scratch = result_root.parent / f".{result_root.name}-runtime"
    require(not runtime_scratch.exists(), "runtime_scratch_already_exists")
    runtime_scratch.mkdir()

    stage = "SOURCE_PREFLIGHT"
    call_rows: list[dict[str, object]] = []
    pass_a_rows: list[dict[str, object]] = []
    pass_b_rows: list[dict[str, object]] = []
    combined_rows: list[dict[str, object]] = []
    coverage: dict[str, object] | None = None
    comparison: dict[str, object] | None = None
    validation: dict[str, object] | None = None
    leak_proof: dict[str, object] | None = None
    generation_id: str | None = None
    output_frozen_at: str | None = None
    terminal_error: BaseException | None = None
    implementation_commit = args.expected_head

    try:
        integrity = runtime_integrity(args.expected_head)
        integrity["contract"] = "m12cq-source-base-runtime-integrity-v1"
        write_json(result_root / "source-base-integrity.json", integrity)
        require(integrity["status"] == "PASS", COMPLETION_NEW_DEPENDENCY)
        sources = verify_sources(args.package_root.resolve(), args.shadow_input_root.resolve())
        write_json(result_root / "source-package-integrity.json", sources)
        require(sources["status"] == "PASS", COMPLETION_NEW_DEPENDENCY)
        m12cp = load_m12cp_inputs(args.package_root.resolve())
        write_json(
            result_root / "m12cp-policy-input-binding.json",
            {
                "contract": "m12cq-m12cp-policy-input-binding-v1",
                "m12cp_implementation": M12CP_IMPLEMENTATION,
                "m12cp_completion": m12cp["completion"],
                "policy": m12cp["policy"],
                "option_matrix_sha256": canonical_sha256(m12cp["options"]),
                "security_basis_sha256": canonical_sha256(m12cp["security"]),
                "status": "PASS",
            },
        )
        controls = generic_control_matrix()
        write_json(result_root / "generic-policy-control-matrix.json", controls)
        require(controls["status"] == "PASS", COMPLETION_NEW_DEPENDENCY)

        os.environ["THESIS_MONITOR_ENV_FILE"] = str(args.env_file.resolve())
        os.environ["DATA_DIR"] = str(runtime_scratch)
        os.environ["DATABASE_URL"] = f"sqlite:///{runtime_scratch / 'shadow.sqlite3'}"
        os.environ["NOTIFICATION_DRY_RUN"] = "true"
        os.environ["NOTIFICATION_RECIPIENT_CLASS"] = "test"
        os.environ["AI_REVIEW_MODE"] = "shadow"
        os.environ["PERSISTENCE_V2_WRITER_ENABLED"] = "false"
        os.environ["PERSISTENCE_V2_OUTBOX_DELIVERY_ENABLED"] = "false"

        from app.jobs import accepted_decision_v2_runtime as runtime
        from app.services.accepted_decision_v2_runtime_service import (
            REASONING_EFFORT,
            REASONING_MODEL,
            AcceptedV2FundamentalCoreBatch,
            AcceptedV2ProductionContext,
            accepted_v2_maturity_atomic_claim_catalog_manifest,
        )

        require(REASONING_MODEL == "gpt-5.6-sol", "configured_model_drift")
        require(REASONING_EFFORT == "xhigh", "configured_effort_drift")
        require(runtime.V2_REASONING_BATCH_SIZE == 3, "batch_size_drift")
        runtime.V2_TRANSPORT_ATTEMPT_LIMIT = 1

        now_utc = datetime.now(UTC)
        generation_id = (
            f"{now_utc.astimezone(KST):%Y%m%d}-m12cq-two-pass-shadow-"
            f"{now_utc:%Y%m%dT%H%M%SZ}-{args.expected_head[:12]}"
        )
        contexts: dict[str, Any] = {}
        context_payloads: dict[str, dict[str, Any]] = {}
        catalogs: dict[str, dict[str, dict[str, object]]] = {}
        pass_a_payloads: dict[str, dict[str, dict[str, object]]] = {}
        for market in ("us", "kr"):
            context_payload = read_json(args.shadow_input_root / market / "context.json")
            context = AcceptedV2ProductionContext.model_validate(context_payload)
            core_batch = AcceptedV2FundamentalCoreBatch.model_validate(
                read_json(args.shadow_input_root / market / "trusted-fundamental-core-batch.json")
            )
            require(
                tuple(context.selected_subjects) == EXPECTED_POPULATION[market],
                f"{market}_population_mismatch",
            )
            require(
                tuple(core.ticker for core in core_batch.cores) == tuple(context.selected_subjects),
                f"{market}_core_scope_mismatch",
            )
            require(core_batch.packet_id == context.packet_id, f"{market}_packet_mismatch")
            atomic = accepted_v2_maturity_atomic_claim_catalog_manifest(core_batch.cores)
            market_catalogs: dict[str, dict[str, object]] = {}
            market_pass_a: dict[str, dict[str, object]] = {}
            for ticker in context.selected_subjects:
                catalog = build_subject_catalog(
                    context=context_payload,
                    ticker=ticker,
                    atomic_claims=atomic["claims"],
                )
                payload = build_pass_a_subject_context(
                    context=context_payload,
                    ticker=ticker,
                    catalog=catalog,
                )
                require(bool(payload["eligible_claim_refs"]), f"pass_a_no_eligible_claims:{ticker}")
                require(
                    bool(payload["eligible_non_price_evidence"]),
                    f"pass_a_no_eligible_evidence:{ticker}",
                )
                market_catalogs[ticker] = catalog
                market_pass_a[ticker] = payload
            contexts[market] = context
            context_payloads[market] = context_payload
            catalogs[market] = market_catalogs
            pass_a_payloads[market] = market_pass_a

        leak_proof = pass_a_leakage_scan(
            [
                pass_a_payloads[market][ticker]
                for market in ("us", "kr")
                for ticker in EXPECTED_POPULATION[market]
            ]
        )
        write_json(result_root / "price-technical-target-leak-proof.json", leak_proof)
        require(leak_proof["status"] == "PASS", COMPLETION_BLINDNESS_FAILED)

        policy = read_json(args.package_root / "inputs/policy-principles.json")
        stage = "PASS_A_PREFLIGHT"
        pass_a_specs, pass_a_model_paths = _batch_specs(
            stage="pass-a",
            generation_id=generation_id,
            contexts=contexts,
            payloads=pass_a_payloads,
            catalogs=catalogs,
            policy=policy,
            result_root=result_root,
        )
        pass_a_schema = _schema_suite(pass_a_specs, stage="pass-a")
        write_json(result_root / "pass-a-schema-and-validator.json", pass_a_schema)
        require(pass_a_schema["status"] == "PASS", COMPLETION_PASS_A_FAILED)
        write_json(
            result_root / "pass-a-price-blind-input-contract.json",
            {
                "contract": "m12cq-pass-a-price-blind-input-contract-v1",
                "generation_id": generation_id,
                "model_facing_file_count": len(pass_a_model_paths),
                "model_facing_files": [
                    {"path": str(path.relative_to(result_root)), "sha256": sha256_file(path)}
                    for path in pass_a_model_paths
                ],
                "leak_proof": leak_proof,
                "status": "PASS",
            },
        )
        precall = run_precall_validation(result_root)
        require(precall["status"] == "PASS", COMPLETION_NEW_DEPENDENCY)

        code_hashes = {
            "scripts/m12cq_two_pass_contract.py": sha256_file(
                REPO / "scripts/m12cq_two_pass_contract.py"
            ),
            "scripts/m12cq_two_pass_shadow.py": sha256_file(
                REPO / "scripts/m12cq_two_pass_shadow.py"
            ),
            "scripts/m12cp_valuation_policy_contract.py": sha256_file(
                REPO / "scripts/m12cp_valuation_policy_contract.py"
            ),
        }
        input_freeze = {
            "contract": "m12cq-model-input-freeze-v1",
            "generation_id": generation_id,
            "implementation_commit": args.expected_head,
            "model": REASONING_MODEL,
            "effort": REASONING_EFFORT,
            "frozen_generation": EXPECTED_FROZEN_GENERATION,
            "pass_a_planned_calls": 8,
            "pass_b_planned_calls": 8,
            "code_hashes": code_hashes,
            "post_freeze_reference_semantic_open_count": 0,
            "frozen_at": datetime.now(UTC).isoformat(),
        }
        write_json(result_root / "model-input-freeze.json", input_freeze)
        codex_bin = runtime._signed_in_codex_bin()

        stage = "PASS_A_CALLS"
        pass_a_rows, pass_a_outputs = _invoke_stage(
            stage="pass-a",
            specs=pass_a_specs,
            catalogs=catalogs,
            pass_a_contexts=pass_a_payloads,
            pass_a_by_ticker={},
            result_root=result_root,
            expected_head=args.expected_head,
            code_hashes=code_hashes,
            runtime=runtime,
            codex_bin=codex_bin,
            timeout=args.timeout,
            call_rows=call_rows,
        )
        require(len(pass_a_rows) == 22, COMPLETION_PASS_A_FAILED)
        require(
            tuple(row["ticker"] for row in pass_a_rows)
            == EXPECTED_POPULATION["us"] + EXPECTED_POPULATION["kr"],
            COMPLETION_PASS_A_FAILED,
        )
        pass_a_aggregate = {
            "contract": "m12cq-pass-a-22-subject-classification-v1",
            "generation_id": generation_id,
            "subject_count": 22,
            "classifications": pass_a_rows,
        }
        pass_a_path = result_root / "pass-a-22-subject-classification.json"
        write_json(pass_a_path, pass_a_aggregate)
        write_json(
            result_root / "pass-a-output-freeze-manifest.json",
            {
                "contract": "m12cq-pass-a-output-freeze-manifest-v1",
                "generation_id": generation_id,
                "call_output_count": len(pass_a_outputs),
                "subject_count": 22,
                "call_outputs": pass_a_outputs,
                "aggregate_sha256": sha256_file(pass_a_path),
                "price_technical_target_leak_count": 0,
                "frozen_at": datetime.now(UTC).isoformat(),
                "status": "PASS",
            },
        )

        stage = "FUNDAMENTAL_MATERIALIZATION"
        matrix = _option_subjects(m12cp["options"])
        pass_a_by_ticker = {str(row["ticker"]): row for row in pass_a_rows}
        depositary_subjects = _depositary_subjects(m12cp["security"])
        policy_options: dict[str, dict[str, object]] = {}
        materialization_rows: list[dict[str, object]] = []
        for ticker in EXPECTED_POPULATION["us"] + EXPECTED_POPULATION["kr"]:
            option = select_matrix_option(matrix[ticker], pass_a_by_ticker[ticker])
            if ticker in depositary_subjects:
                require(option.get("status") != "RESOLVED", f"security_basis_violation:{ticker}")
            policy_options[ticker] = option
            materialization_rows.append(option)
        write_json(
            result_root / "fundamental-option-materialization-22.json",
            {
                "contract": "m12cq-fundamental-option-materialization-22-v1",
                "generation_id": generation_id,
                "subject_count": 22,
                "model_authored_fundamental_price_count": 0,
                "arbitrary_current_price_discount_count": 0,
                "rows": materialization_rows,
                "status": "PASS",
            },
        )
        write_json(
            result_root / "security-basis-gate-results.json",
            {
                "contract": "m12cq-security-basis-gate-results-v1",
                "depositary_subjects": sorted(depositary_subjects),
                "resolved_depositary_subjects": sorted(
                    ticker
                    for ticker in depositary_subjects
                    if policy_options[ticker]["status"] == "RESOLVED"
                ),
                "violation_count": 0,
                "status": "PASS",
            },
        )

        pass_b_payloads: dict[str, dict[str, dict[str, object]]] = {}
        for market in ("us", "kr"):
            pass_b_payloads[market] = {
                ticker: build_pass_b_subject_context(
                    context=context_payloads[market],
                    ticker=ticker,
                    catalog=catalogs[market][ticker],
                    pass_a=pass_a_by_ticker[ticker],
                    policy_option=policy_options[ticker],
                )
                for ticker in EXPECTED_POPULATION[market]
            }
        stage = "PASS_B_PREFLIGHT"
        pass_b_specs, pass_b_model_paths = _batch_specs(
            stage="pass-b",
            generation_id=generation_id,
            contexts=contexts,
            payloads=pass_b_payloads,
            catalogs=catalogs,
            policy=policy,
            result_root=result_root,
        )
        pass_b_schema = _schema_suite(pass_b_specs, stage="pass-b")
        write_json(result_root / "pass-b-schema-and-validator.json", pass_b_schema)
        require(pass_b_schema["status"] == "PASS", COMPLETION_PASS_B_FAILED)
        write_json(
            result_root / "pass-b-input-contract.json",
            {
                "contract": "m12cq-pass-b-input-contract-v1",
                "generation_id": generation_id,
                "model_facing_file_count": len(pass_b_model_paths),
                "model_authored_fundamental_fields": [],
                "runtime_owned_fields": [
                    "fundamental option",
                    "preferred low/high",
                    "distance",
                    "valuation refs",
                    "technical refs",
                    "combination rule",
                ],
                "model_facing_files": [
                    {"path": str(path.relative_to(result_root)), "sha256": sha256_file(path)}
                    for path in pass_b_model_paths
                ],
                "status": "PASS",
            },
        )
        _assert_frozen_head(args.expected_head, code_hashes)

        stage = "PASS_B_CALLS"
        pass_b_rows, pass_b_outputs = _invoke_stage(
            stage="pass-b",
            specs=pass_b_specs,
            catalogs=catalogs,
            pass_a_contexts=pass_a_payloads,
            pass_a_by_ticker=pass_a_by_ticker,
            result_root=result_root,
            expected_head=args.expected_head,
            code_hashes=code_hashes,
            runtime=runtime,
            codex_bin=codex_bin,
            timeout=args.timeout,
            call_rows=call_rows,
        )
        require(len(pass_b_rows) == 22, COMPLETION_PASS_B_FAILED)
        require(
            tuple(row["ticker"] for row in pass_b_rows)
            == EXPECTED_POPULATION["us"] + EXPECTED_POPULATION["kr"],
            COMPLETION_PASS_B_FAILED,
        )
        pass_b_path = result_root / "pass-b-22-subject-decisions.json"
        write_json(
            pass_b_path,
            {
                "contract": "m12cq-pass-b-22-subject-decisions-v1",
                "generation_id": generation_id,
                "subject_count": 22,
                "decisions": pass_b_rows,
            },
        )
        write_json(
            result_root / "pass-b-output-freeze-manifest.json",
            {
                "contract": "m12cq-pass-b-output-freeze-manifest-v1",
                "generation_id": generation_id,
                "call_output_count": len(pass_b_outputs),
                "subject_count": 22,
                "call_outputs": pass_b_outputs,
                "aggregate_sha256": sha256_file(pass_b_path),
                "frozen_at": datetime.now(UTC).isoformat(),
                "status": "PASS",
            },
        )

        stage = "RUNTIME_MATERIALIZATION"
        pass_b_by_ticker = {str(row["ticker"]): row for row in pass_b_rows}
        consistency_rows: list[dict[str, object]] = []
        entry_rows: list[dict[str, object]] = []
        market_by_ticker = {
            ticker: market for market in ("us", "kr") for ticker in EXPECTED_POPULATION[market]
        }
        for ticker in EXPECTED_POPULATION["us"] + EXPECTED_POPULATION["kr"]:
            market = market_by_ticker[ticker]
            decision = pass_b_by_ticker[ticker]
            entry = materialize_policy_entry_range(
                ticker=ticker,
                new_buyer=str(decision["new_buyer"]),
                policy_option=policy_options[ticker],
                entry_catalog=catalogs[market][ticker]["entry_catalog"],
                tactical_choice=str(decision["tactical_choice"]),
                re_evaluate_conditions=decision["re_evaluate_conditions"],
            )
            consistency = validate_new_buyer_consistency(
                decision=decision,
                policy_option=policy_options[ticker],
                entry_range=entry,
                catalog=catalogs[market][ticker],
            )
            consistency_rows.append(consistency)
            require(consistency["status"] == "PASS", f"new_buyer_consistency_failed:{ticker}")
            entry_rows.append({"ticker": ticker, "entry_range": entry})
            pass_a = pass_a_by_ticker[ticker]
            combined_rows.append(
                {
                    "ticker": ticker,
                    "market": market,
                    "company_archetype": pass_a["archetype"],
                    "archetype_confidence": pass_a["archetype_confidence"],
                    "archetype_supporting_claim_refs": pass_a["archetype_supporting_claim_refs"],
                    "archetype_rationale": pass_a["archetype_rationale"],
                    "valuation_regime_tier": pass_a["valuation_regime_tier"],
                    "tier_supporting_claim_refs": pass_a["tier_supporting_claim_refs"],
                    "tier_rationale": pass_a["tier_rationale"],
                    "data_quality_effect": pass_a["data_quality_effect"],
                    "data_quality_reason_class": pass_a["data_quality_reason_class"],
                    "data_quality_reason": pass_a["data_quality_reason"],
                    "data_quality_evidence_refs": pass_a["data_quality_evidence_refs"],
                    **decision,
                    "fundamental_option": policy_options[ticker],
                    "entry_range": entry,
                }
            )
        write_json(
            result_root / "runtime-entry-range-materialization-22.json",
            {
                "contract": "m12cq-runtime-entry-range-materialization-22-v1",
                "subject_count": 22,
                "rows": entry_rows,
                "model_authored_deterministic_entry_metadata_count": 0,
                "status": "PASS",
            },
        )
        write_json(
            result_root / "new-buyer-consistency-results.json",
            {
                "contract": "m12cq-new-buyer-consistency-results-v1",
                "subject_count": 22,
                "pass_count": sum(row["status"] == "PASS" for row in consistency_rows),
                "rows": consistency_rows,
                "status": "PASS",
            },
        )
        write_json(
            result_root / "overall-holder-policy-validation.json",
            {
                "contract": "m12cq-overall-holder-policy-validation-v1",
                "subject_count": 22,
                "pass_b_semantic_validation_owned": True,
                "valuation_only_holder_review_count": 0,
                "valuation_only_durable_or_cyclical_nonbuy_count": 0,
                "status": "PASS",
            },
        )
        aggregate_path = result_root / "shadow-22-subject-results.json"
        write_json(
            aggregate_path,
            {
                "contract": "m12cq-shadow-22-subject-results-v1",
                "generation_id": generation_id,
                "frozen_m12cm_generation": EXPECTED_FROZEN_GENERATION,
                "subject_count": 22,
                "candidates": combined_rows,
            },
        )
        coverage = _coverage_analysis(combined_rows, consistency_rows, depositary_subjects)
        write_json(result_root / "entry-range-coverage-and-methods.json", coverage)
        write_json(
            result_root / "premium-tier-evidence-audit.json",
            {
                "contract": "m12cq-premium-tier-evidence-audit-v1",
                "rows": coverage["premium_tier_support"],
                "unsupported_premium_count": 0,
                "status": "PASS",
            },
        )
        write_json(
            result_root / "data-quality-effect-analysis.json",
            {
                "contract": "m12cq-data-quality-effect-analysis-v1",
                "distribution": coverage["data_quality_effect_distribution"],
                "unknown_as_bearish_count": 0,
                "status": "PASS",
            },
        )

        _assert_frozen_head(args.expected_head, code_hashes)
        output_frozen_at = datetime.now(UTC).isoformat()
        write_json(
            result_root / "complete-shadow-output-freeze-manifest.json",
            {
                "contract": "m12cq-complete-shadow-output-freeze-manifest-v1",
                "generation_id": generation_id,
                "subject_count": 22,
                "pass_a_call_output_count": len(pass_a_outputs),
                "pass_b_call_output_count": len(pass_b_outputs),
                "aggregate_sha256": sha256_file(aggregate_path),
                "entry_materialization_sha256": sha256_file(
                    result_root / "runtime-entry-range-materialization-22.json"
                ),
                "post_freeze_reference_semantic_open_count_before_freeze": 0,
                "frozen_at": output_frozen_at,
                "status": "PASS",
            },
        )

        stage = "POST_FREEZE_COMPARISON"
        comparison = _post_freeze_comparison(
            archive_path=args.package_root.resolve()
            / "post-freeze-reference/post-freeze-reference.zip",
            rows=combined_rows,
            frozen_at=output_frozen_at,
            result_root=result_root,
        )

        stage = "POSTCALL_VALIDATION"
        validation = run_postcall_validation(result_root)
        require(validation["status"] == "PASS", COMPLETION_NEW_DEPENDENCY)
    except BaseException as exc:  # noqa: BLE001
        terminal_error = exc
        write_text(result_root / "failure-traceback.txt", traceback.format_exc())
    finally:
        shutil.rmtree(runtime_scratch, ignore_errors=True)

    if terminal_error is None:
        completion_state = COMPLETION_PASS
    elif str(terminal_error).split(":", 1)[0] == COMPLETION_BLINDNESS_FAILED:
        completion_state = COMPLETION_BLINDNESS_FAILED
    elif stage.startswith("PASS_A"):
        completion_state = COMPLETION_PASS_A_FAILED
    elif stage.startswith("FUNDAMENTAL") or stage.startswith("RUNTIME_MATERIALIZATION"):
        completion_state = COMPLETION_MATERIALIZATION_FAILED
    elif stage.startswith("PASS_B"):
        completion_state = COMPLETION_PASS_B_FAILED
    else:
        completion_state = COMPLETION_NEW_DEPENDENCY
    blockers = []
    if terminal_error is not None:
        blockers.append(
            {
                "severity": "P0",
                "stage": stage,
                "code": str(terminal_error).split(":", 1)[0],
                "error_type": type(terminal_error).__name__,
                "bounded_next_action": "Return to Chat; retry and same-run hotfix are forbidden.",
            }
        )
    write_json(
        result_root / "complete-blocker-ledger.json",
        {
            "contract": "m12cq-complete-blocker-ledger-v1",
            "open_blocker_count": len(blockers),
            "blockers": blockers,
            "status": "PASS" if not blockers else "BLOCKED",
        },
    )
    safety = {
        "contract": "m12cq-safety-counters-v1",
        "production_send": 0,
        "production_intent": 0,
        "production_db_mutation": 0,
        "broker_read": 0,
        "broker_order": 0,
        "broker_modify": 0,
        "broker_cancel": 0,
        "market_provider_refresh": 0,
        "scheduler_change": 0,
        "main_merge": 0,
        "remote_push": 0,
        "deployment": 0,
        "fundamental_core_model_calls": 0,
        "pass_a_calls_started": sum(row.get("stage") == "pass-a" for row in call_rows),
        "pass_a_calls_passed": sum(
            row.get("stage") == "pass-a" and row.get("status") == "PASS" for row in call_rows
        ),
        "pass_b_calls_started": sum(row.get("stage") == "pass-b" for row in call_rows),
        "pass_b_calls_passed": sum(
            row.get("stage") == "pass-b" and row.get("status") == "PASS" for row in call_rows
        ),
        "model_retry": 0,
        "wrapper_retry": 0,
        "repair_model": 0,
        "fallback_model": 0,
        "judge_model": 0,
        "selective_rerun": 0,
        "per_ticker_rerun": 0,
        "cross_generation_stitching": 0,
        "post_call_hotfix": 0,
        "second_inference_after_reveal": 0,
        "production_runtime_behavior_change": 0,
    }
    write_json(result_root / "safety-counters.json", safety)
    write_json(
        result_root / "model-call-ledger.json",
        {
            "contract": "m12cq-model-call-ledger-v1",
            "generation_id": generation_id,
            "planned_pass_a_calls": 8,
            "planned_pass_b_calls": 8,
            "started_call_count": len(call_rows),
            "passed_call_count": sum(row.get("status") == "PASS" for row in call_rows),
            "calls": call_rows,
        },
    )
    completion = {
        "contract": "m12cq-program-completion-v1",
        "completion_state": completion_state,
        "generation_id": generation_id,
        "frozen_m12cm_generation": EXPECTED_FROZEN_GENERATION,
        "work_instruction_commit": WORK_INSTRUCTION_COMMIT,
        "implementation_commit": implementation_commit,
        "pass_a_call_pass_count": safety["pass_a_calls_passed"],
        "pass_b_call_pass_count": safety["pass_b_calls_passed"],
        "subject_count": len(combined_rows),
        "price_technical_target_leak_count": (
            leak_proof.get("current_price_leak_count") if leak_proof else None
        ),
        "post_freeze_reference_open_count": 1 if comparison else 0,
        "validation_status": validation.get("status") if validation else "NOT_REACHED",
        "open_blocker_count": len(blockers),
        "production_integration_authorized": False,
        "return_to_chat": terminal_error is None,
        "completed_at": datetime.now(UTC).isoformat(),
    }
    write_json(result_root / "program-completion.json", completion)
    write_text(
        result_root / "REPORT.md",
        _report_markdown(
            completion=completion,
            coverage=coverage,
            calls=call_rows,
            validation=validation,
            comparison=comparison,
        ),
    )
    write_json(result_root / "artifact-manifest.json", artifact_manifest(result_root))
    archive_path = result_root.parent / f"{result_root.name}.zip"
    archive = zip_tree(result_root, archive_path)
    sidecar = archive_path.with_suffix(archive_path.suffix + ".sha256")
    write_text(sidecar, f"{archive['sha256']}  {archive_path.name}")
    print(
        json.dumps(
            {
                "completion_state": completion_state,
                "generation_id": generation_id,
                "pass_a": f"{safety['pass_a_calls_passed']}/8",
                "pass_b": f"{safety['pass_b_calls_passed']}/8",
                "subjects": len(combined_rows),
                "archive": str(archive_path),
                "archive_sha256": archive["sha256"],
                "sidecar": str(sidecar),
            },
            ensure_ascii=False,
            sort_keys=True,
        ),
        flush=True,
    )
    if terminal_error is not None:
        raise M12CQFailure(completion_state) from terminal_error


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--package-root", type=Path, required=True)
    parser.add_argument("--shadow-input-root", type=Path, required=True)
    parser.add_argument("--result-root", type=Path, required=True)
    parser.add_argument("--env-file", type=Path, required=True)
    parser.add_argument("--expected-head", required=True)
    parser.add_argument("--timeout", type=int, default=1800)
    run(parser.parse_args())


if __name__ == "__main__":
    main()
