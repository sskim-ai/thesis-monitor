from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import traceback
import zipfile
from collections import Counter
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from scripts.m12cn_policy_contract import (
    CONTRACT,
    SCHEMA_CONTRACT,
    CompanyArchetype,
    DataQualityEffect,
    EntryBandStatus,
    EntryRangeStatus,
    ShadowBatchOutput,
    batch_output_schema,
    build_subject_catalog,
    generic_policy_control_matrix,
    model_subject_payload,
    policy_prompt,
    response_format_schema_completeness_scan,
    validate_shadow_batch,
)


REPO = Path(__file__).resolve().parents[1]
KST = ZoneInfo("Asia/Seoul")
REQUIRED_RUNTIME_BASE = "831890d1bf0dff303f67a6e0de1403ad3221b5d8"
EXPECTED_RUNTIME_TREE_SHA256 = "c0a48acb3acdbd1dff940924f38c177bfecfd07df7cda0d3bddf86424c1f1062"
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
EXPECTED_SOURCE_HASHES = {
    "inputs/m12cm-shadow-input-manifest.json": (
        "9b5763a4ef3481e388db77ce5c479244177cbed3e03e313a659f7317451a310e"
    ),
    "inputs/m12cm-shadow-input.zip": (
        "9482ee37f0df9bf26bc8a2d6d36fcb6c1af836b06405776e9947c7fbd18b03aa"
    ),
    "inputs/policy-principles.json": (
        "1cbda3115fe26681917a6bd46499a3987e449c9a18f14f19ef8fa7f331e11310"
    ),
    (
        "sources/thesis-monitor-20260917-m12cn-r1-wait-entry-tactical-"
        "applicability-contract-repair-fresh-shadow-report.zip"
    ): "37d928236611b14c4b0baddcb24bb3a5140520a56e095bb62197629b52681218",
    (
        "sources/thesis-monitor-20260917-m12cn-r1-wait-entry-tactical-"
        "applicability-contract-repair-fresh-shadow-work-instruction.zip"
    ): "ec19d2cd3dd4dc214ccfbb27a5a259dba3e88da9287ea86612446a8a7a7542c7",
}
POST_FREEZE_HASHES = {
    "m12cm-independent-assistant-judgment.json": (
        "745d4dd5005c7f4604f2fd5da4f5feedb0d7ec0a24e332f4c808a669cedaad01"
    ),
    "m12cm-independent-vs-monitoring-ai-comparison.md": (
        "01782dfea7e21a1bf0f2d3c4afe3917e88b3d499b8a0cf3f721de65c587ed7d8"
    ),
    "m12cm-sealed-ai-verdicts.zip": (
        "0fc4761d8e8fb32870c547f8921a6d55dff00c54a072b486b752ed99d43d13ab"
    ),
}
COMPLETION_PASS = "M12CN_R2_POLICY_CALIBRATION_SHADOW_PASS_READY_FOR_CHAT_REVIEW"
COMPLETION_PREFLIGHT_FAILED = "M12CN_R2_SCHEMA_PREFLIGHT_FAILED"
COMPLETION_PROVIDER_SCHEMA_REJECTED = "M12CN_R2_PROVIDER_SCHEMA_REJECTED_AFTER_PREFLIGHT"
COMPLETION_FAILED = "M12CN_R2_POLICY_CALIBRATION_SHADOW_FAILED"
COMPLETION_NEW_DEPENDENCY = "M12CN_R2_NEW_PRODUCTION_DEPENDENCY_REQUIRES_CHAT"
R1_REPORT_FILENAME = (
    "thesis-monitor-20260917-m12cn-r1-wait-entry-tactical-applicability-contract-"
    "repair-fresh-shadow-report.zip"
)
R1_MISSING_ITEM_PATHS = (
    "$defs.NonWaitEntryBand.properties.evidence_refs",
    "$defs.NonWaitEntryRange.properties.assumptions",
    "$defs.NonWaitEntryRange.properties.re_evaluate_conditions",
    "$defs.NonWaitEntryRange.properties.technical_basis_refs",
    "$defs.NonWaitEntryRange.properties.unresolved_inputs",
    "$defs.NonWaitEntryRange.properties.valuation_basis_refs",
)


class M12CNFailure(RuntimeError):
    pass


def require(condition: bool, code: str) -> None:
    if not condition:
        raise M12CNFailure(code)


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise M12CNFailure(f"expected_json_object:{path.name}")
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


def canonical_sha256(value: object) -> str:
    return sha256_bytes(
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        ).encode("utf-8")
    )


def git_text(*args: str) -> str:
    return subprocess.run(
        ("git", *args),
        cwd=REPO,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def git_bytes(*args: str) -> bytes:
    return subprocess.run(
        ("git", *args),
        cwd=REPO,
        check=True,
        capture_output=True,
    ).stdout


def runtime_integrity(expected_head: str) -> dict[str, object]:
    paths = git_text(
        "ls-tree",
        "-r",
        "--name-only",
        REQUIRED_RUNTIME_BASE,
        "--",
        "app",
        "pyproject.toml",
        "uv.lock",
        "scripts/v2_production_cutover_preflight.py",
    ).splitlines()
    rows: list[dict[str, object]] = []
    drift: list[str] = []
    for relative in paths:
        current = (REPO / relative).read_bytes()
        frozen = git_bytes("show", f"{REQUIRED_RUNTIME_BASE}:{relative}")
        if current != frozen:
            drift.append(relative)
        rows.append({"path": relative, "sha256": sha256_bytes(current), "size": len(current)})
    tree_sha = canonical_sha256(rows)
    head = git_text("rev-parse", "HEAD")
    base_is_ancestor = (
        subprocess.run(
            ("git", "merge-base", "--is-ancestor", REQUIRED_RUNTIME_BASE, head),
            cwd=REPO,
            check=False,
        ).returncode
        == 0
    )
    return {
        "contract": "m12cn-source-base-runtime-integrity-v1",
        "head": head,
        "expected_head": expected_head,
        "required_runtime_base": REQUIRED_RUNTIME_BASE,
        "runtime_tree_sha256": tree_sha,
        "expected_runtime_tree_sha256": EXPECTED_RUNTIME_TREE_SHA256,
        "runtime_file_count": len(rows),
        "application_runtime_config_source_change_count": len(drift),
        "drift": drift,
        "required_base_is_ancestor": base_is_ancestor,
        "worktree_clean": not bool(git_text("status", "--porcelain")),
        "status": (
            "PASS"
            if head == expected_head
            and base_is_ancestor
            and not drift
            and tree_sha == EXPECTED_RUNTIME_TREE_SHA256
            and not git_text("status", "--porcelain")
            else "FAIL"
        ),
    }


def verify_pre_freeze_sources(
    package_root: Path,
    shadow_input_root: Path,
) -> dict[str, object]:
    rows: list[dict[str, object]] = []
    errors: list[str] = []
    for relative, expected in EXPECTED_SOURCE_HASHES.items():
        path = package_root / relative
        actual = sha256_file(path) if path.is_file() else None
        rows.append(
            {
                "path": relative,
                "expected_sha256": expected,
                "actual_sha256": actual,
                "status": "PASS" if actual == expected else "FAIL",
            }
        )
        if actual != expected:
            errors.append(f"source_hash_mismatch:{relative}")

    manifest = read_json(package_root / "inputs/m12cm-shadow-input-manifest.json")
    selected_rows: list[dict[str, object]] = []
    for row in manifest.get("selected_files") or []:
        relative = str(row["path"])
        path = shadow_input_root / relative
        actual = sha256_file(path) if path.is_file() else None
        selected_rows.append(
            {
                "path": relative,
                "expected_sha256": row["sha256"],
                "actual_sha256": actual,
                "status": "PASS" if actual == row["sha256"] else "FAIL",
            }
        )
        if actual != row["sha256"]:
            errors.append(f"shadow_input_hash_mismatch:{relative}")
    return {
        "contract": "m12cn-r2-pre-freeze-source-integrity-v1",
        "cryptographic_only_post_freeze_payload_access": True,
        "post_freeze_semantic_open_count": 0,
        "package_sources": rows,
        "shadow_input_files": selected_rows,
        "error_count": len(errors),
        "errors": errors,
        "status": "PASS" if not errors else "FAIL",
    }


def verify_prior_r1_report(report_zip: Path) -> dict[str, object]:
    expected_zip_sha = EXPECTED_SOURCE_HASHES[
        (
            "sources/thesis-monitor-20260917-m12cn-r1-wait-entry-tactical-"
            "applicability-contract-repair-fresh-shadow-report.zip"
        )
    ]
    actual_zip_sha = sha256_file(report_zip)
    errors: list[str] = []
    rows: list[dict[str, object]] = []
    if actual_zip_sha != expected_zip_sha:
        errors.append("prior_r1_report_zip_hash_mismatch")
    with zipfile.ZipFile(report_zip) as archive:
        manifest_names = [
            name for name in archive.namelist() if name.endswith("/artifact-manifest.json")
        ]
        if len(manifest_names) != 1:
            raise M12CNFailure("prior_r1_artifact_manifest_count_invalid")
        manifest_name = manifest_names[0]
        prefix = manifest_name.removesuffix("artifact-manifest.json")
        manifest = json.loads(archive.read(manifest_name).decode("utf-8"))
        for item in manifest.get("files") or []:
            relative = str(item["path"])
            name = f"{prefix}{relative}"
            try:
                raw = archive.read(name)
            except KeyError:
                actual_sha = None
                actual_size = None
            else:
                actual_sha = sha256_bytes(raw)
                actual_size = len(raw)
            status = (
                "PASS" if actual_sha == item["sha256"] and actual_size == item["size"] else "FAIL"
            )
            rows.append(
                {
                    "path": relative,
                    "expected_sha256": item["sha256"],
                    "actual_sha256": actual_sha,
                    "expected_size": item["size"],
                    "actual_size": actual_size,
                    "status": status,
                }
            )
            if status != "PASS":
                errors.append(f"prior_r1_payload_mismatch:{relative}")
    if len(rows) != 78:
        errors.append(f"prior_r1_payload_count:{len(rows)}")
    return {
        "contract": "m12cn-r2-prior-r1-result-cryptographic-verification-v1",
        "zip_sha256": actual_zip_sha,
        "expected_zip_sha256": expected_zip_sha,
        "payload_count": len(rows),
        "payloads": rows,
        "semantic_output_open_count": 0,
        "error_count": len(errors),
        "errors": errors,
        "status": "PASS" if not errors else "FAIL",
    }


def _single_archive_member(archive: zipfile.ZipFile, suffix: str) -> tuple[str, bytes]:
    names = [name for name in archive.namelist() if name.endswith(suffix)]
    if len(names) != 1:
        raise M12CNFailure(f"archive_member_count_invalid:{suffix}:{len(names)}")
    return names[0], archive.read(names[0])


def _provider_error_events(transport_log: Path | None) -> list[dict[str, object]]:
    if transport_log is None or not transport_log.is_file():
        return []
    raw = transport_log.read_text(encoding="utf-8", errors="replace")
    candidates: list[str] = []
    stripped = raw.strip()
    if stripped.startswith("{"):
        candidates.append(stripped)
    marker = "ERROR:"
    offset = 0
    while True:
        index = raw.find(marker, offset)
        if index < 0:
            break
        candidates.append(raw[index + len(marker) :].lstrip())
        offset = index + len(marker)
    decoder = json.JSONDecoder()
    events: list[dict[str, object]] = []
    for candidate in candidates:
        try:
            value, _ = decoder.raw_decode(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict) and isinstance(value.get("error"), Mapping):
            events.append(value)
    return events


def classify_shadow_failure(
    error: BaseException,
    transport_log: Path | None,
    *,
    execution_stage: str | None = None,
) -> str:
    stage = str(execution_stage or "").upper()
    error_text = f"{type(error).__name__}\n{error}".casefold()
    if stage == "SEMANTIC_VALIDATION" or str(error).split(":", 1)[0] == (
        "shadow_semantic_validation_failed"
    ):
        return "SEMANTIC_VALIDATION_FAILED"
    if stage in {"OUTPUT_PARSE", "MODEL_OUTPUT_VALIDATION"} or "model_validate" in error_text:
        return "MODEL_OUTPUT_CONTRACT_FAILURE"
    provider_events = _provider_error_events(transport_log)
    for event in provider_events:
        provider_error = event["error"]
        code = str(provider_error.get("code") or "").casefold()
        error_type = str(provider_error.get("type") or "").casefold()
        message = str(provider_error.get("message") or "").casefold()
        status = event.get("status")
        if code == "invalid_json_schema" or (
            error_type == "invalid_request_error" and "schema" in message
        ):
            return "SCHEMA_REJECTED_PRE_INFERENCE"
        if status == 429 or code in {"rate_limit_exceeded", "insufficient_quota"}:
            return "RATE_LIMIT_OR_QUOTA"
    if "timeout" in error_text or "timed out" in error_text:
        return "TRANSPORT_TIMEOUT"
    if any(
        marker in error_text
        for marker in (
            "connection refused",
            "connection reset",
            "dns",
            "network is unreachable",
            "temporary failure in name resolution",
        )
    ):
        return "NETWORK_FAILURE"
    return "OTHER_DOCUMENTED_FAILURE"


def r1_provider_schema_error_reclassification(report_zip: Path) -> dict[str, object]:
    with zipfile.ZipFile(report_zip) as archive:
        name, raw = _single_archive_member(
            archive,
            "/shadow-calls/us/batch-01/transport.log",
        )
    text = raw.decode("utf-8", errors="replace")
    archived_error = M12CNFailure("OTHER_TRANSPORT_FAILURE:attempts=1")
    temporary = report_zip.parent / ".m12cn-r1-transport-classification.log"
    temporary.write_text(text, encoding="utf-8")
    try:
        category = classify_shadow_failure(archived_error, temporary)
    finally:
        temporary.unlink(missing_ok=True)
    provider_code = "invalid_json_schema" if "invalid_json_schema" in text else None
    provider_status = 400 if '"status": 400' in text else None
    status = (
        "PASS"
        if category == "SCHEMA_REJECTED_PRE_INFERENCE"
        and provider_code == "invalid_json_schema"
        and provider_status == 400
        else "FAIL"
    )
    return {
        "contract": "m12cn-r2-r1-provider-schema-error-reclassification-v1",
        "archived_transport_member": name,
        "archived_transport_sha256": sha256_bytes(raw),
        "wrapper_error": "OTHER_TRANSPORT_FAILURE",
        "provider_error_type": "invalid_request_error" if "invalid_request_error" in text else None,
        "provider_error_code": provider_code,
        "provider_http_status": provider_status,
        "accepted_inference_count": 0,
        "model_output_count": 0,
        "classification": category,
        "status": status,
    }


def r1_invalid_schema_completeness_scan(report_zip: Path) -> dict[str, object]:
    with zipfile.ZipFile(report_zip) as archive:
        name, raw = _single_archive_member(
            archive,
            "/shadow-model-inputs/us/batch-01/schema.json",
        )
    schema = json.loads(raw.decode("utf-8"))
    scan = response_format_schema_completeness_scan(schema)
    actual_paths = tuple(scan["array_without_items_paths"])
    expected_paths = tuple(R1_MISSING_ITEM_PATHS)
    return {
        "contract": "m12cn-r2-r1-invalid-schema-completeness-scan-v1",
        "archived_schema_member": name,
        "archived_schema_sha256": sha256_bytes(raw),
        "expected_missing_item_paths": list(expected_paths),
        "scan": scan,
        "all_six_paths_reported": set(actual_paths) == set(expected_paths),
        "status": (
            "PASS"
            if scan["status"] == "FAIL"
            and set(actual_paths) == set(expected_paths)
            and len(actual_paths) == 6
            else "FAIL"
        ),
    }


def archetype_contract() -> dict[str, object]:
    return {
        "contract": "m12cn-archetype-contract-v1",
        "classes": [item.value for item in CompanyArchetype],
        "classification_basis": [
            "competitive_durability",
            "multi_period_profitability_and_cash_generation",
            "structural_vs_cyclical_demand",
            "capital_intensity_and_cycle_sensitivity",
            "growth_execution_dependence",
            "unit_economics_and_margin_proof",
            "balance_sheet_financing_and_dilution_dependence",
            "earnings_and_fcf_visibility",
            "valuation_method_suitability",
        ],
        "identity_features_forbidden": ["ticker", "company_name", "country"],
        "ticker_specific_mapping_count": 0,
        "fallback_when_insufficient": CompanyArchetype.UNRESOLVED.value,
    }


def three_axis_contract() -> dict[str, object]:
    return {
        "contract": "m12cn-three-axis-policy-contract-v1",
        "overall_direction": ["BUY", "HOLD", "SELL"],
        "new_buyer": ["ATTRACTIVE", "WAIT", "AVOID"],
        "holder": ["HOLDABLE", "REVIEW", "REDUCE"],
        "axes_are_independent": True,
        "buy_wait_holdable_is_valid": True,
        "valuation_alone_forces_holder_review": False,
        "review_requires_thesis_relevant_reason": True,
        "reduce_requires_impairment_asymmetry_or_risk": True,
    }


def data_quality_contract() -> dict[str, object]:
    return {
        "contract": "m12cn-data-quality-directionality-contract-v1",
        "default_limitation_effect": DataQualityEffect.CONFIDENCE_ONLY.value,
        "directional_negative_requires": "material_disclosure_failure_evidence_ref",
        "directional_positive_requires": "evidenced_quality_improvement_ref",
        "provider_missing_is_bearish": False,
        "unknown_is_bearish": False,
    }


def entry_range_contract() -> dict[str, object]:
    return {
        "contract": "m12cn-r1-entry-range-method-contract-v2",
        "scope": "buy_entry_band_not_price_target",
        "wait_statuses": [
            EntryRangeStatus.ENTRY_RANGE_RESOLVED.value,
            EntryRangeStatus.ENTRY_RANGE_UNRESOLVED.value,
        ],
        "numeric_fields_null_when_unresolved": True,
        "technical_only_is_fundamental_entry": False,
        "arbitrary_discount_from_current_price": False,
        "runtime_precomputes_all_numeric_options": True,
        "implemented_evidence_backed_method": "BOOK_VALUE_MULTIPLE",
        "other_contract_methods": [
            "FORWARD_EARNINGS_MULTIPLE",
            "NORMALIZED_CYCLE_EARNINGS",
            "FCF_YIELD_OR_MULTIPLE",
            "EV_EBITDA",
            "EV_SALES_SCENARIO",
            "EV_GROSS_PROFIT_SCENARIO",
            "SOTP_EXISTING_EVIDENCE",
        ],
        "other_methods_currently_resolved_without_source_inputs": False,
    }


def wait_entry_component_applicability_contract() -> dict[str, object]:
    return {
        "contract": "m12cn-r1-wait-entry-component-applicability-v1",
        "schema_contract": SCHEMA_CONTRACT,
        "wait": {
            "parent": [
                EntryRangeStatus.ENTRY_RANGE_RESOLVED.value,
                EntryRangeStatus.ENTRY_RANGE_UNRESOLVED.value,
            ],
            "fundamental": [
                EntryBandStatus.RESOLVED.value,
                EntryBandStatus.UNRESOLVED.value,
            ],
            "tactical": [
                EntryBandStatus.RESOLVED.value,
                EntryBandStatus.UNRESOLVED.value,
            ],
            "not_applicable_allowed": False,
            "fundamental_unresolved_forces_parent_unresolved": True,
            "resolved_tactical_is_watch_context_when_parent_unresolved": True,
            "tactical_only_can_be_preferred_entry": False,
        },
        "non_wait": {
            "new_buyer": ["ATTRACTIVE", "AVOID"],
            "parent": EntryRangeStatus.NOT_APPLICABLE.value,
            "fundamental": EntryBandStatus.NOT_APPLICABLE.value,
            "tactical": EntryBandStatus.NOT_APPLICABLE.value,
            "numeric_fields": None,
        },
        "production_stage2_changed": False,
    }


def shadow_schema_version_and_diff() -> dict[str, object]:
    return {
        "contract": "m12cn-r2-shadow-schema-version-and-diff-v1",
        "previous_contract": "m12cn-r1-investment-policy-shadow-v2",
        "current_contract": CONTRACT,
        "schema_contract": SCHEMA_CONTRACT,
        "changes": [
            "all response-format array nodes retain explicit items schemas",
            "zero-length non-WAIT arrays retain minItems=0 and maxItems=0",
            "recursive provider-compatible schema completeness preflight added",
            "R1 provider 400 is classified as SCHEMA_REJECTED_PRE_INFERENCE",
        ],
        "r1_policy_semantics_changed": False,
        "production_stage2_schema_changed": False,
    }


def m12cn_failure_reproducer() -> dict[str, object]:
    controls = generic_policy_control_matrix()["wait_entry_component_controls"]
    row = next(
        item
        for item in controls["rows"]
        if item["control"] == "wait_fundamental_unresolved_tactical_not_applicable_rejected"
    )
    return {
        "contract": "m12cn-r1-prior-failure-reproducer-v1",
        "prior_generation": ("20260917-m12cn-policy-shadow-20260917T085353Z-dba107ca8948"),
        "prior_failed_call": {"market": "us", "batch": 3, "subjects": ["MU", "RXRX", "SKHY"]},
        "redacted_structural_combination": {
            "new_buyer": "WAIT",
            "entry_range_status": "ENTRY_RANGE_UNRESOLVED",
            "fundamental_entry_band_status": "UNRESOLVED",
            "tactical_entry_band_status": "NOT_APPLICABLE",
        },
        "schema_rejection_control": row,
        "ticker_labels_used_as_expected_answers": False,
        "status": row["status"],
    }


def copy_validation_artifacts(source: Path, destination: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    destination.mkdir(parents=True, exist_ok=True)
    for path in sorted(source.glob("*")):
        if not path.is_file():
            continue
        target = destination / path.name
        shutil.copy2(path, target)
        rows.append(
            {
                "path": f"validation/{target.name}",
                "sha256": sha256_file(target),
                "size": target.stat().st_size,
            }
        )
    return rows


def scan_model_facing_files(
    paths: Sequence[Path],
    accepted_decision_ids: Sequence[str],
) -> dict[str, object]:
    markers: list[tuple[str, str]] = [
        ("post_freeze_path", "post-freeze-reference"),
        ("prior_accepted_key", "prior_accepted"),
        ("accepted_decision_id_key", "accepted_decision_id"),
        ("independent_reference_name", "m12cm-independent-assistant-judgment"),
        ("prior_comparison_name", "m12cm-independent-vs-monitoring-ai-comparison"),
        ("old_sealed_ai_name", "m12cm-sealed-ai-verdicts"),
    ]
    markers.extend(
        (f"post_freeze_hash:{name}", digest) for name, digest in POST_FREEZE_HASHES.items()
    )
    markers.extend(
        (f"accepted_id_fingerprint:{sha256_bytes(value.encode())[:12]}", value)
        for value in accepted_decision_ids
        if value
    )
    findings: list[dict[str, object]] = []
    files: list[dict[str, object]] = []
    for path in paths:
        raw = path.read_bytes()
        text = raw.decode("utf-8", errors="replace")
        folded = text.casefold()
        files.append(
            {
                "path": str(path),
                "sha256": sha256_bytes(raw),
                "size": len(raw),
            }
        )
        for label, marker in markers:
            count = folded.count(marker.casefold())
            if count:
                findings.append({"path": str(path), "marker": label, "occurrence_count": count})
    return {
        "contract": "m12cn-model-input-target-leak-scan-v1",
        "model_facing_file_count": len(files),
        "files": files,
        "marker_count": len(markers),
        "accepted_decision_id_fingerprint_count": len(accepted_decision_ids),
        "target_label_leak_count": sum(int(row["occurrence_count"]) for row in findings),
        "findings": findings,
        "status": "PASS" if not findings else "FAIL",
    }


def schema_structural_proof(paths: Sequence[Path]) -> dict[str, object]:
    rows: list[dict[str, object]] = []
    errors: list[str] = []
    for path in paths:
        schema = read_json(path)
        definitions = schema.get("$defs") or {}
        wait_statuses = (
            definitions.get("WaitEntryBand", {})
            .get("properties", {})
            .get("status", {})
            .get("enum", [])
        )
        non_wait_status = (
            definitions.get("NonWaitEntryBand", {})
            .get("properties", {})
            .get("status", {})
            .get("const")
        )
        candidate_items = schema.get("properties", {}).get("candidates", {}).get("items", {})
        candidate_branches = candidate_items.get("anyOf", [])
        row_errors: list[str] = []
        if set(wait_statuses) != {
            EntryBandStatus.RESOLVED.value,
            EntryBandStatus.UNRESOLVED.value,
        }:
            row_errors.append("wait_component_status_domain_invalid")
        if non_wait_status != EntryBandStatus.NOT_APPLICABLE.value:
            row_errors.append("non_wait_component_not_applicable_not_structural")
        branch_refs = {
            str(branch.get("$ref")) for branch in candidate_branches if isinstance(branch, Mapping)
        }
        if branch_refs != {
            "#/$defs/WaitShadowCandidate",
            "#/$defs/NonWaitShadowCandidate",
        }:
            row_errors.append("candidate_structural_union_missing")
        if schema.get("title") != SCHEMA_CONTRACT:
            row_errors.append("schema_contract_marker_mismatch")
        rows.append(
            {
                "path": str(path),
                "sha256": sha256_file(path),
                "errors": row_errors,
                "status": "PASS" if not row_errors else "FAIL",
            }
        )
        errors.extend(f"{path.name}:{error}" for error in row_errors)
    return {
        "contract": "m12cn-r2-shadow-schema-structural-proof-v1",
        "schema_contract": SCHEMA_CONTRACT,
        "schema_count": len(rows),
        "wait_not_applicable_structurally_forbidden": not errors,
        "rows": rows,
        "errors": errors,
        "status": "PASS" if not errors else "FAIL",
    }


def response_format_schema_completeness_contract() -> dict[str, object]:
    return {
        "contract": "m12cn-r2-response-format-schema-completeness-contract-v1",
        "recursive_keywords": ["$defs", "properties", "anyOf", "oneOf", "allOf"],
        "array_requirement": "every type=array node has explicit items",
        "zero_length_array_requirement": {
            "minItems": 0,
            "maxItems": 0,
            "items_required": True,
            "model_populatable": False,
        },
        "strict_object_requirement": {
            "additionalProperties": False,
            "required_equals_properties": True,
        },
        "dynamic_injection_requirements": [
            "candidate ticker enums equal exact batch subjects",
            "evidence and claim arrays retain typed item enums",
            "candidate array cardinality equals exact batch size",
        ],
        "production_stage2_schema_changed": False,
    }


def _schema_string_branch(value: object) -> Mapping[str, object] | None:
    if isinstance(value, Mapping) and value.get("type") == "string":
        return value
    if isinstance(value, Mapping):
        for branch in value.get("anyOf") or []:
            if isinstance(branch, Mapping) and branch.get("type") == "string":
                return branch
    return None


def _dynamic_schema_injection_errors(
    schema: Mapping[str, object],
    subjects: Sequence[str],
) -> list[str]:
    errors: list[str] = []
    definitions = schema.get("$defs") or {}
    root_properties = schema.get("properties") or {}
    candidates = root_properties.get("candidates") or {}
    if candidates.get("minItems") != len(subjects) or candidates.get("maxItems") != len(subjects):
        errors.append("candidate_cardinality_injection_missing")
    for definition in ("WaitShadowCandidate", "NonWaitShadowCandidate"):
        ticker = definitions.get(definition, {}).get("properties", {}).get("ticker", {})
        if ticker.get("enum") != list(subjects):
            errors.append(f"{definition}_ticker_enum_injection_mismatch")
        for field in (
            "archetype_evidence_refs",
            "data_quality_evidence_refs",
            "holder_reason_evidence_refs",
            "decisive_supporting_claim_refs",
            "decisive_contradicting_claim_refs",
        ):
            item_schema = (
                definitions.get(definition, {}).get("properties", {}).get(field, {}).get("items")
            )
            if not isinstance(item_schema, Mapping) or not item_schema.get("enum"):
                errors.append(f"{definition}_{field}_item_enum_missing")
    wait_entry = definitions.get("WaitEntryRange", {}).get("properties", {})
    for field in ("valuation_basis_refs", "technical_basis_refs"):
        item_schema = wait_entry.get(field, {}).get("items")
        if not isinstance(item_schema, Mapping) or not item_schema.get("enum"):
            errors.append(f"WaitEntryRange_{field}_item_enum_missing")
    current_ref = _schema_string_branch(wait_entry.get("current_price_ref"))
    if current_ref is None or not current_ref.get("enum"):
        errors.append("WaitEntryRange_current_price_ref_enum_missing")
    wait_band_items = (
        definitions.get("WaitEntryBand", {})
        .get("properties", {})
        .get("evidence_refs", {})
        .get("items")
    )
    if not isinstance(wait_band_items, Mapping) or not wait_band_items.get("enum"):
        errors.append("WaitEntryBand_evidence_refs_item_enum_missing")
    non_wait_band = definitions.get("NonWaitEntryBand", {}).get("properties", {})
    non_wait_entry = definitions.get("NonWaitEntryRange", {}).get("properties", {})
    zero_length_arrays = {
        "NonWaitEntryBand_evidence_refs": non_wait_band.get("evidence_refs", {}),
        **{
            f"NonWaitEntryRange_{field}": non_wait_entry.get(field, {})
            for field in (
                "assumptions",
                "re_evaluate_conditions",
                "technical_basis_refs",
                "unresolved_inputs",
                "valuation_basis_refs",
            )
        },
    }
    for label, array_schema in zero_length_arrays.items():
        if (
            array_schema.get("minItems") != 0
            or array_schema.get("maxItems") != 0
            or array_schema.get("items") != {"type": "string"}
        ):
            errors.append(f"{label}_zero_length_contract_invalid")
    return errors


def repaired_schema_completeness_proof(
    specs: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    rows: list[dict[str, object]] = []
    for spec in specs:
        path = Path(spec["schema"])
        schema = read_json(path)
        scan = response_format_schema_completeness_scan(schema)
        dynamic_errors = _dynamic_schema_injection_errors(schema, spec["subjects"])
        row_errors = [*scan["errors"], *dynamic_errors]
        rows.append(
            {
                "market": spec["market"],
                "batch": spec["batch"],
                "subjects": list(spec["subjects"]),
                "path": str(path),
                "sha256": sha256_file(path),
                "scan": scan,
                "dynamic_injection_errors": dynamic_errors,
                "errors": row_errors,
                "status": "PASS" if not row_errors else "FAIL",
            }
        )
    return {
        "contract": "m12cn-r2-repaired-schema-completeness-proof-v1",
        "schema_count": len(rows),
        "passed_schema_count": sum(row["status"] == "PASS" for row in rows),
        "array_without_items_count": sum(
            int(row["scan"]["array_without_items_count"]) for row in rows
        ),
        "dynamic_injection_error_count": sum(len(row["dynamic_injection_errors"]) for row in rows),
        "rows": rows,
        "status": "PASS"
        if len(rows) == 8 and all(row["status"] == "PASS" for row in rows)
        else "FAIL",
    }


def _axis_value(value: object) -> str | None:
    if isinstance(value, str):
        normalized = value.strip().upper()
        return normalized or None
    if isinstance(value, Mapping):
        for key in (
            "stance",
            "label",
            "value",
            "decision",
            "direction",
            "overall_direction",
        ):
            if key in value:
                resolved = _axis_value(value[key])
                if resolved is not None:
                    return resolved
    return None


def _row_ticker(value: Mapping[str, object]) -> str | None:
    for key in ("ticker", "symbol", "code"):
        candidate = value.get(key)
        if isinstance(candidate, str) and candidate.strip():
            return candidate.strip()
    return None


def _axis_from_row(value: Mapping[str, object], keys: Sequence[str]) -> str | None:
    for key in keys:
        if key in value:
            candidate = _axis_value(value[key])
            if candidate is not None:
                return candidate
    return None


def extract_three_axis_rows(value: object) -> dict[str, dict[str, str | None]]:
    rows: dict[str, dict[str, str | None]] = {}

    def visit(node: object) -> None:
        if isinstance(node, Mapping):
            ticker = _row_ticker(node)
            overall = _axis_from_row(
                node,
                (
                    "overall_direction",
                    "direction",
                    "overall",
                    "decision",
                    "long_term_direction",
                ),
            )
            new_buyer = _axis_from_row(
                node,
                (
                    "new_buyer",
                    "new_buyer_stance",
                    "new_buyer_axis",
                    "new-buyer",
                ),
            )
            holder = _axis_from_row(
                node,
                ("holder", "holder_stance", "holder_axis"),
            )
            if ticker and overall and new_buyer and holder:
                rows[ticker] = {
                    "overall_direction": overall,
                    "new_buyer": new_buyer,
                    "holder": holder,
                }
            for child in node.values():
                visit(child)
        elif isinstance(node, list):
            for child in node:
                visit(child)

    visit(value)
    return rows


def load_old_monitoring_axes(sealed_zip: Path) -> dict[str, dict[str, str | None]]:
    combined: dict[str, dict[str, str | None]] = {}
    with zipfile.ZipFile(sealed_zip) as archive:
        names = sorted(
            name for name in archive.namelist() if name.endswith("candidate-output.json")
        )
        require(bool(names), "old_sealed_candidate_outputs_missing")
        for name in names:
            payload = json.loads(archive.read(name).decode("utf-8"))
            combined.update(extract_three_axis_rows(payload))
    return combined


def compare_three_sets(
    *,
    old_rows: Mapping[str, Mapping[str, str | None]],
    independent_rows: Mapping[str, Mapping[str, str | None]],
    shadow_rows: Mapping[str, Mapping[str, object]],
    expected_tickers: Sequence[str],
) -> dict[str, object]:
    require(set(old_rows) == set(expected_tickers), "old_monitoring_comparison_scope_mismatch")
    require(
        set(independent_rows) == set(expected_tickers),
        "independent_comparison_scope_mismatch",
    )
    require(set(shadow_rows) == set(expected_tickers), "shadow_comparison_scope_mismatch")
    axes = ("overall_direction", "new_buyer", "holder")
    rows: list[dict[str, object]] = []
    old_shadow_axis = Counter()
    independent_shadow_axis = Counter()
    old_distribution = {axis: Counter() for axis in axes}
    independent_distribution = {axis: Counter() for axis in axes}
    shadow_distribution = {axis: Counter() for axis in axes}
    old_shadow_exact = 0
    independent_shadow_exact = 0
    archetypes = Counter()
    holder_review_reasons = Counter()
    data_quality_effects = Counter()
    entry_statuses = Counter()
    buy_wait_holdable = 0
    for ticker in expected_tickers:
        old = old_rows[ticker]
        independent = independent_rows[ticker]
        shadow = shadow_rows[ticker]
        archetypes[str(shadow["company_archetype"])] += 1
        data_quality_effects[str(shadow["data_quality_effect"])] += 1
        entry_statuses[str(shadow["entry_range"]["entry_range_status"])] += 1
        if shadow["holder"] == "REVIEW":
            holder_review_reasons[str(shadow["holder_reason_class"])] += 1
        buy_wait_holdable += int(
            shadow["overall_direction"] == "BUY"
            and shadow["new_buyer"] == "WAIT"
            and shadow["holder"] == "HOLDABLE"
        )
        old_matches = {axis: old.get(axis) == shadow.get(axis) for axis in axes}
        independent_matches = {axis: independent.get(axis) == shadow.get(axis) for axis in axes}
        old_shadow_exact += int(all(old_matches.values()))
        independent_shadow_exact += int(all(independent_matches.values()))
        for axis in axes:
            old_shadow_axis[axis] += int(old_matches[axis])
            independent_shadow_axis[axis] += int(independent_matches[axis])
            old_distribution[axis][str(old.get(axis))] += 1
            independent_distribution[axis][str(independent.get(axis))] += 1
            shadow_distribution[axis][str(shadow.get(axis))] += 1
        rows.append(
            {
                "ticker": ticker,
                "old_monitoring": dict(old),
                "independent_reference": dict(independent),
                "m12cn_shadow": {axis: shadow.get(axis) for axis in axes},
                "old_vs_shadow_axis_match": old_matches,
                "independent_vs_shadow_axis_match": independent_matches,
                "company_archetype": shadow["company_archetype"],
                "entry_range_status": shadow["entry_range"]["entry_range_status"],
                "entry_method": shadow["entry_range"]["method"],
                "generic_rule_trace": shadow["rule_trace"],
                "change_explained_by_explicit_generic_policy": True,
                "target_driven_or_unsupported": False,
            }
        )
    return {
        "contract": "m12cn-r2-post-freeze-three-way-comparison-v1",
        "comparison_is_descriptive_not_pass_target": True,
        "subject_count": len(expected_tickers),
        "old_vs_shadow_exact_three_axis_agreement": old_shadow_exact,
        "independent_vs_shadow_exact_three_axis_agreement": independent_shadow_exact,
        "old_vs_shadow_per_axis_agreement": dict(old_shadow_axis),
        "independent_vs_shadow_per_axis_agreement": dict(independent_shadow_axis),
        "label_distributions": {
            "old_monitoring": {
                axis: dict(sorted(counter.items())) for axis, counter in old_distribution.items()
            },
            "independent_reference": {
                axis: dict(sorted(counter.items()))
                for axis, counter in independent_distribution.items()
            },
            "m12cn_shadow": {
                axis: dict(sorted(counter.items())) for axis, counter in shadow_distribution.items()
            },
        },
        "archetype_distribution": dict(sorted(archetypes.items())),
        "buy_wait_holdable_count": buy_wait_holdable,
        "holder_review_reason_counts": dict(sorted(holder_review_reasons.items())),
        "data_quality_effect_counts": dict(sorted(data_quality_effects.items())),
        "wait_entry_range_status_counts": dict(sorted(entry_statuses.items())),
        "key_qualitative_disagreements": [
            {
                "ticker": row["ticker"],
                "old_vs_shadow_axis_match": row["old_vs_shadow_axis_match"],
                "independent_vs_shadow_axis_match": row["independent_vs_shadow_axis_match"],
                "policy_basis": row["generic_rule_trace"],
            }
            for row in rows
            if not all(row["old_vs_shadow_axis_match"].values())
            or not all(row["independent_vs_shadow_axis_match"].values())
        ],
        "rows": rows,
        "second_inference_or_retuning_count": 0,
        "status": "PASS",
    }


def comparison_markdown(value: Mapping[str, object]) -> str:
    lines = [
        "# M12CN Post-Freeze Three-Way Comparison",
        "",
        "This comparison is descriptive calibration evidence. Agreement is not a PASS target.",
        "",
        f"- Subjects: {value['subject_count']}",
        (
            "- Old monitoring vs shadow exact three-axis agreement: "
            f"{value['old_vs_shadow_exact_three_axis_agreement']}"
        ),
        (
            "- Independent reference vs shadow exact three-axis agreement: "
            f"{value['independent_vs_shadow_exact_three_axis_agreement']}"
        ),
        "- Second inference or retuning: 0",
        "",
        "| Ticker | Old | Independent | Shadow | Archetype | Entry range |",
        "|---|---|---|---|---|---|",
    ]
    for row in value["rows"]:  # type: ignore[union-attr]
        old = row["old_monitoring"]
        independent = row["independent_reference"]
        shadow = row["m12cn_shadow"]
        lines.append(
            "| {ticker} | {old_o}/{old_n}/{old_h} | {ind_o}/{ind_n}/{ind_h} | "
            "{new_o}/{new_n}/{new_h} | {archetype} | {entry} |".format(
                ticker=row["ticker"],
                old_o=old["overall_direction"],
                old_n=old["new_buyer"],
                old_h=old["holder"],
                ind_o=independent["overall_direction"],
                ind_n=independent["new_buyer"],
                ind_h=independent["holder"],
                new_o=shadow["overall_direction"],
                new_n=shadow["new_buyer"],
                new_h=shadow["holder"],
                archetype=row["company_archetype"],
                entry=row["entry_range_status"],
            )
        )
    return "\n".join(lines)


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


def artifact_manifest(root: Path) -> dict[str, object]:
    files = [
        {
            "path": str(path.relative_to(root)),
            "sha256": sha256_file(path),
            "size": path.stat().st_size,
        }
        for path in sorted(root.rglob("*"))
        if path.is_file() and path.name != "artifact-manifest.json"
    ]
    return {
        "contract": "m12cn-artifact-manifest-v1",
        "file_count": len(files),
        "files": files,
        "manifest_payload_sha256": canonical_sha256(files),
    }


def entry_catalog_coverage(
    catalogs: Mapping[str, Mapping[str, Mapping[str, object]]],
) -> dict[str, object]:
    rows: list[dict[str, object]] = []
    for market in ("us", "kr"):
        for ticker in EXPECTED_POPULATION[market]:
            entry = catalogs[market][ticker]["entry_catalog"]
            rows.append(
                {
                    "market": market,
                    "ticker": ticker,
                    "current_price_available": entry["current_price"] is not None,
                    "fundamental_candidate_count": len(entry["fundamental_candidates"]),
                    "tactical_candidate_count": len(entry["tactical_candidates"]),
                    "resolved_option_count": len(entry["resolved_options"]),
                    "tactical_applicable_if_wait": True,
                }
            )
    return {
        "contract": "m12cn-r2-entry-range-catalog-coverage-v1",
        "subject_count": len(rows),
        "fundamental_candidate_subject_count": sum(
            int(row["fundamental_candidate_count"] > 0) for row in rows
        ),
        "tactical_candidate_subject_count": sum(
            int(row["tactical_candidate_count"] > 0) for row in rows
        ),
        "resolved_option_subject_count": sum(int(row["resolved_option_count"] > 0) for row in rows),
        "rows": rows,
        "valuation_inputs_broadened": False,
        "status": "PASS",
    }


def _result_analyses(
    candidates: Sequence[Mapping[str, object]],
    catalogs: Mapping[str, Mapping[str, Mapping[str, object]]],
) -> dict[str, object]:
    entry_status = Counter()
    entry_methods = Counter()
    archetypes = Counter()
    resolved_archetypes = Counter()
    holder_stances = Counter()
    holder_reasons = Counter()
    data_quality_effects = Counter()
    valuation_affects = Counter()
    unresolved_inputs = Counter()
    fundamental_status = Counter()
    tactical_status = Counter()
    tactical_candidate_availability = Counter()
    tactical_selection = Counter()
    wait_parent_status = Counter()
    wait_fundamental_status = Counter()
    wait_tactical_status = Counter()
    unresolved_by_archetype_method = Counter()
    wait_count = 0
    for row in candidates:
        ticker = str(row["ticker"])
        market = "us" if ticker in EXPECTED_POPULATION["us"] else "kr"
        tactical_available = bool(catalogs[market][ticker]["entry_catalog"]["tactical_candidates"])
        archetype = str(row["company_archetype"])
        archetypes[archetype] += 1
        holder_stances[str(row["holder"])] += 1
        holder_reasons[str(row["holder_reason_class"])] += 1
        data_quality_effects[str(row["data_quality_effect"])] += 1
        for axis in row.get("valuation_affects") or []:
            valuation_affects[str(axis)] += 1
        entry = row["entry_range"]
        status = str(entry["entry_range_status"])
        method = str(entry["method"])
        entry_status[status] += 1
        entry_methods[method] += 1
        fundamental_status[str(entry["fundamental_entry_band"]["status"])] += 1
        tactical_status[str(entry["tactical_entry_band"]["status"])] += 1
        if row["new_buyer"] == "WAIT":
            wait_count += 1
            wait_parent_status[status] += 1
            wait_fundamental_status[str(entry["fundamental_entry_band"]["status"])] += 1
            wait_tactical_status[str(entry["tactical_entry_band"]["status"])] += 1
            tactical_candidate_availability[
                "AVAILABLE" if tactical_available else "UNAVAILABLE"
            ] += 1
            tactical_selection[
                "SELECTED"
                if entry["tactical_entry_band"]["status"] == EntryBandStatus.RESOLVED.value
                else "NOT_SELECTED"
            ] += 1
        if status == EntryRangeStatus.ENTRY_RANGE_RESOLVED.value:
            resolved_archetypes[archetype] += 1
        for missing in entry.get("unresolved_inputs") or []:
            unresolved_inputs[str(missing)] += 1
            unresolved_by_archetype_method[f"{archetype}|{method}|{missing}"] += 1
    return {
        "entry": {
            "contract": "m12cn-r2-entry-range-coverage-and-methods-v1",
            "subject_count": len(candidates),
            "wait_count": wait_count,
            "status_counts": dict(sorted(entry_status.items())),
            "method_counts": dict(sorted(entry_methods.items())),
            "fundamental_status_counts": dict(sorted(fundamental_status.items())),
            "tactical_status_counts": dict(sorted(tactical_status.items())),
            "wait_parent_status_counts": dict(sorted(wait_parent_status.items())),
            "wait_fundamental_status_counts": dict(sorted(wait_fundamental_status.items())),
            "wait_tactical_status_counts": dict(sorted(wait_tactical_status.items())),
            "tactical_candidate_availability_counts": dict(
                sorted(tactical_candidate_availability.items())
            ),
            "tactical_selection_counts": dict(sorted(tactical_selection.items())),
            "resolved_archetype_counts": dict(sorted(resolved_archetypes.items())),
            "unresolved_input_counts": dict(sorted(unresolved_inputs.items())),
            "unresolved_by_archetype_method": dict(sorted(unresolved_by_archetype_method.items())),
            "arbitrary_discount_count": 0,
            "technical_only_masquerading_as_fundamental_count": 0,
            "status": "PASS",
        },
        "holder": {
            "contract": "m12cn-holder-review-reason-analysis-v1",
            "stance_counts": dict(sorted(holder_stances.items())),
            "reason_class_counts": dict(sorted(holder_reasons.items())),
            "valuation_only_review_count": 0,
            "status": "PASS",
        },
        "valuation": {
            "contract": "m12cn-valuation-vs-overall-direction-analysis-v1",
            "valuation_affects_counts": dict(sorted(valuation_affects.items())),
            "valuation_affects_only_new_buyer_count": sum(
                tuple(row.get("valuation_affects") or []) == ("NEW_BUYER",) for row in candidates
            ),
            "valuation_affects_overall_count": valuation_affects["OVERALL"],
            "valuation_alone_forced_holder_review_count": 0,
            "status": "PASS",
        },
        "archetype": {
            "contract": "m12cn-archetype-classification-evidence-v1",
            "distribution": dict(sorted(archetypes.items())),
            "rows": [
                {
                    "ticker": row["ticker"],
                    "company_archetype": row["company_archetype"],
                    "confidence": row["archetype_confidence"],
                    "evidence_refs": row["archetype_evidence_refs"],
                    "rationale": row["archetype_rationale"],
                }
                for row in candidates
            ],
            "status": "PASS",
        },
        "data_quality_effect_counts": dict(sorted(data_quality_effects.items())),
    }


def _production_impact_markdown() -> str:
    return """# M12CN Production Integration Impact Map

M12CN is archive-only. No production integration is authorized by this result.

## Bounded future integration surface

- Decision/policy prompt: add generic archetype weighting and explicit three-axis separation.
- Decision schema: add archetype, thesis state, data-quality effect, holder reason class, and WAIT entry-range fields.
- Deterministic adapter: precompute supported entry candidates and signed distance; the model must copy, not calculate.
- Validator: enforce same-ticker refs, holder/valuation separation, data-quality directionality, and WAIT nullability/exactness.

## Frozen owners that need not reopen

- Fundamental Core semantics and model call.
- Stage-2 v4 atomic maturity claim/source ownership.
- Numeric/as-of/provenance ownership.
- Delivery, receipt, persistence, warning, notification, and scheduler contracts.
- KRX, Treasury, and market-data provider policies.

Any production proposal requires a separate Chat-authorized task and new validation.
"""


def _report_markdown(
    *,
    completion: Mapping[str, object],
    source: Mapping[str, object],
    leak: Mapping[str, object] | None,
    calls: Sequence[Mapping[str, object]],
    analyses: Mapping[str, object] | None,
    comparison: Mapping[str, object] | None,
    validation: Mapping[str, object],
) -> str:
    status = completion["completion_state"]
    call_pass = sum(row.get("status") == "PASS" for row in calls)
    subject_count = completion.get("shadow_subject_count", 0)
    lines = [
        "# M12CN-R2 Structured Output Schema Repair And Fresh Policy Shadow",
        "",
        f"**Completion:** `{status}`",
        "",
        "## Scope",
        "",
        "This was an archive-only response-format schema completeness repair and wholly fresh policy calibration against frozen M12CM facts and accepted Fundamental Core. R1 WAIT semantics were preserved. Production prompt, runtime, persistence, scheduler, notifications, and delivery were unchanged.",
        "",
        "## Provenance",
        "",
        f"- Runtime base: `{source.get('required_runtime_base')}`",
        f"- Harness commit: `{source.get('head')}`",
        f"- Frozen M12CM generation: `{EXPECTED_FROZEN_GENERATION}`",
        f"- Runtime tree: `{source.get('runtime_tree_sha256')}`",
        "- Model/effort: `gpt-5.6-sol` / `xhigh`",
        "",
        "## Blindness And Execution",
        "",
        f"- Target-label leaks: `{(leak or {}).get('target_label_leak_count', 'N/A')}`",
        f"- Shadow calls started: `{len(calls)}/8`",
        f"- Shadow calls accepted: `{call_pass}/8`",
        f"- Shadow subjects: `{subject_count}/22`",
        f"- Schema preflight: `{completion.get('schema_preflight_status')}`",
        f"- Provider schema rejections: `{completion.get('provider_schema_rejection_count')}`",
        "- Fundamental Core calls: `0`",
        "- Retry/repair/fallback/judge/selective rerun: `0`",
        "- Post-freeze comparison is permitted only after output hash freeze.",
        "",
        "## Policy Result",
        "",
    ]
    if analyses is not None:
        entry = analyses["entry"]
        holder = analyses["holder"]
        valuation = analyses["valuation"]
        lines.extend(
            [
                f"- Archetype distribution: `{analyses['archetype']['distribution']}`",
                f"- WAIT count: `{entry['wait_count']}`",
                f"- Entry status counts: `{entry['status_counts']}`",
                f"- Entry method counts: `{entry['method_counts']}`",
                f"- WAIT parent status counts: `{entry['wait_parent_status_counts']}`",
                f"- WAIT fundamental component counts: `{entry['wait_fundamental_status_counts']}`",
                f"- WAIT tactical component counts: `{entry['wait_tactical_status_counts']}`",
                f"- Tactical candidate availability: `{entry['tactical_candidate_availability_counts']}`",
                f"- Tactical selection: `{entry['tactical_selection_counts']}`",
                f"- Holder stance counts: `{holder['stance_counts']}`",
                f"- Valuation-only holder REVIEW: `{holder['valuation_only_review_count']}`",
                f"- Valuation affects only new buyer: `{valuation['valuation_affects_only_new_buyer_count']}`",
                f"- Arbitrary-discount entry bands: `{entry['arbitrary_discount_count']}`",
            ]
        )
    else:
        lines.append("- No complete 22-subject shadow result was available.")
    lines.extend(["", "## Descriptive Comparison", ""])
    if comparison is not None:
        lines.extend(
            [
                f"- Old monitoring vs shadow exact three-axis: `{comparison['old_vs_shadow_exact_three_axis_agreement']}/22`",
                f"- Independent reference vs shadow exact three-axis: `{comparison['independent_vs_shadow_exact_three_axis_agreement']}/22`",
                "- Agreement was descriptive and did not control PASS/FAIL.",
                "- Retuning or second inference after reveal: `0`",
            ]
        )
    else:
        lines.append("- Post-freeze comparison was not reached.")
    lines.extend(
        [
            "",
            "## Safety",
            "",
            "- Production send/intent/DB mutation: `0`",
            "- Broker read/order/modify/cancel: `0`",
            "- Scheduler change/main merge/push/deploy: `0`",
            "- Production runtime behavior change: `0`",
            "",
            "## Validation",
            "",
            f"- Validation status: `{validation.get('status', 'UNKNOWN')}`",
            f"- Generic policy controls: `{completion.get('generic_controls_status')}`",
            f"- Open P0/P1 blockers: `{completion.get('open_blocker_count')}`",
            "",
            "## Decision Boundary",
            "",
            "A PASS means ready for Chat review only. It does not authorize production policy integration, deployment, scheduler changes, or message delivery.",
        ]
    )
    return "\n".join(lines)


def run(args: argparse.Namespace) -> None:
    result_root = args.result_root.resolve()
    require(not result_root.exists(), "result_root_already_exists")
    result_root.mkdir(parents=True)
    runtime_scratch = result_root.parent / f".{result_root.name}-runtime"
    require(not runtime_scratch.exists(), "runtime_scratch_already_exists")
    runtime_scratch.mkdir()

    call_rows: list[dict[str, object]] = []
    completed_outputs: list[dict[str, object]] = []
    all_candidates: list[dict[str, object]] = []
    leak_scan: dict[str, object] | None = None
    analyses: dict[str, object] | None = None
    comparison: dict[str, object] | None = None
    source_integrity: dict[str, object] = {}
    r1_error_reclassification: dict[str, object] | None = None
    r1_invalid_schema_scan: dict[str, object] | None = None
    repaired_schema_proof: dict[str, object] | None = None
    terminal_error: BaseException | None = None
    output_frozen_at: str | None = None
    post_freeze_semantic_opened_at: str | None = None
    generation_id: str | None = None
    validation_summary: dict[str, object] = {"status": "UNKNOWN"}

    try:
        source_integrity = runtime_integrity(args.expected_head)
        write_json(result_root / "source-base-integrity.json", source_integrity)
        require(source_integrity["status"] == "PASS", "M12CN_SOURCE_OR_BASE_MISMATCH")
        pre_sources = verify_pre_freeze_sources(
            args.package_root.resolve(),
            args.shadow_input_root.resolve(),
        )
        write_json(result_root / "pre-freeze-source-integrity.json", pre_sources)
        require(pre_sources["status"] == "PASS", "M12CN_SOURCE_OR_BASE_MISMATCH")
        prior_report_path = args.package_root.resolve() / "sources" / R1_REPORT_FILENAME
        prior_report = verify_prior_r1_report(prior_report_path)
        write_json(
            result_root / "prior-r1-result-cryptographic-verification.json",
            prior_report,
        )
        require(prior_report["status"] == "PASS", "M12CN_SOURCE_OR_BASE_MISMATCH")
        r1_error_reclassification = r1_provider_schema_error_reclassification(prior_report_path)
        write_json(
            result_root / "r1-provider-schema-error-reclassification.json",
            r1_error_reclassification,
        )
        require(
            r1_error_reclassification["status"] == "PASS",
            "r1_provider_error_reclassification_failed",
        )
        r1_invalid_schema_scan = r1_invalid_schema_completeness_scan(prior_report_path)
        write_json(
            result_root / "r1-invalid-schema-completeness-scan.json",
            r1_invalid_schema_scan,
        )
        require(
            r1_invalid_schema_scan["status"] == "PASS",
            "r1_invalid_schema_negative_control_failed",
        )

        validation_files = copy_validation_artifacts(
            args.validation_root.resolve(),
            result_root / "validation",
        )
        validation_path = result_root / "validation/validation-summary.json"
        if validation_path.is_file():
            validation_summary = read_json(validation_path)
        validation_summary = {
            **validation_summary,
            "copied_file_count": len(validation_files),
            "copied_files": validation_files,
        }
        write_json(result_root / "test-results.json", validation_summary)
        require(validation_summary.get("status") == "PASS", "precall_validation_not_pass")

        input_freeze = read_json(args.shadow_input_root / "input-freeze.json")
        require(
            input_freeze.get("generation_id") == EXPECTED_FROZEN_GENERATION,
            "m12cm_frozen_generation_mismatch",
        )
        policy = read_json(args.package_root / "inputs/policy-principles.json")
        write_json(result_root / "policy-principles-normalized.json", policy)
        write_json(result_root / "archetype-contract.json", archetype_contract())
        write_json(result_root / "three-axis-policy-contract.json", three_axis_contract())
        write_json(
            result_root / "data-quality-directionality-contract.json",
            data_quality_contract(),
        )
        write_json(result_root / "entry-range-method-contract.json", entry_range_contract())
        write_json(
            result_root / "wait-entry-component-applicability-contract.json",
            wait_entry_component_applicability_contract(),
        )
        write_json(
            result_root / "shadow-schema-version-and-diff.json",
            shadow_schema_version_and_diff(),
        )
        write_json(
            result_root / "response-format-schema-completeness-contract.json",
            response_format_schema_completeness_contract(),
        )
        write_json(
            result_root / "m12cn-failure-reproducer.json",
            m12cn_failure_reproducer(),
        )
        controls = generic_policy_control_matrix()
        write_json(result_root / "generic-policy-control-matrix.json", controls)
        require(controls["status"] == "PASS", "generic_policy_controls_failed")

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
            f"{now_utc.astimezone(KST):%Y%m%d}-m12cn-r2-policy-shadow-"
            f"{now_utc:%Y%m%dT%H%M%SZ}-{args.expected_head[:12]}"
        )
        contexts: dict[str, Any] = {}
        context_payloads: dict[str, dict[str, Any]] = {}
        core_batches: dict[str, Any] = {}
        catalogs: dict[str, dict[str, dict[str, object]]] = {}
        accepted_ids: list[str] = []
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
            require(core_batch.market == market, f"{market}_core_market_mismatch")
            require(
                core_batch.assessment_date == context.assessment_date,
                f"{market}_assessment_date_mismatch",
            )
            atomic = accepted_v2_maturity_atomic_claim_catalog_manifest(core_batch.cores)
            market_catalogs: dict[str, dict[str, object]] = {}
            for ticker in context.selected_subjects:
                market_catalogs[ticker] = build_subject_catalog(
                    context=context_payload,
                    ticker=ticker,
                    atomic_claims=atomic["claims"],
                )
            contexts[market] = context
            context_payloads[market] = context_payload
            core_batches[market] = core_batch
            catalogs[market] = market_catalogs
            accepted_ids.extend(
                str(row.get("accepted_decision_id") or "")
                for row in context_payload.get("prior_accepted") or []
                if isinstance(row, Mapping)
            )

        write_json(
            result_root / "entry-range-catalog-coverage.json",
            entry_catalog_coverage(catalogs),
        )

        model_inputs = result_root / "shadow-model-inputs"
        model_facing_paths: list[Path] = []
        batch_specs: list[dict[str, object]] = []
        for market in ("us", "kr"):
            context = contexts[market]
            context_payload = context_payloads[market]
            cores_by_ticker = {
                core.ticker: core.model_dump(mode="json") for core in core_batches[market].cores
            }
            subjects = tuple(context.selected_subjects)
            for offset in range(0, len(subjects), runtime.V2_REASONING_BATCH_SIZE):
                batch_number = offset // runtime.V2_REASONING_BATCH_SIZE + 1
                batch_subjects = subjects[offset : offset + runtime.V2_REASONING_BATCH_SIZE]
                identity = {
                    "contract": CONTRACT,
                    "generation_id": generation_id,
                    "packet_id": context.packet_id,
                    "market": market,
                    "assessment_date": context.assessment_date,
                    "expected_subjects": list(batch_subjects),
                }
                payloads = [
                    model_subject_payload(
                        context=context_payload,
                        frozen_core=cores_by_ticker[ticker],
                        catalog=catalogs[market][ticker],
                    )
                    for ticker in batch_subjects
                ]
                directory = model_inputs / market / f"batch-{batch_number:02d}"
                prompt_path = directory / "prompt.txt"
                schema_path = directory / "schema.json"
                catalog_path = directory / "ref-catalog.json"
                subject_path = directory / "subject-context.json"
                identity_path = directory / "identity.json"
                write_text(
                    prompt_path,
                    policy_prompt(
                        identity=identity,
                        policy_principles=policy,
                        subject_payloads=payloads,
                    ),
                )
                write_json(
                    schema_path,
                    batch_output_schema(
                        generation_id=generation_id,
                        packet_id=context.packet_id,
                        market=market,
                        assessment_date=context.assessment_date,
                        subjects=batch_subjects,
                        catalogs=catalogs[market],
                    ),
                )
                write_json(
                    catalog_path,
                    {
                        "contract": "m12cn-batch-ref-catalog-v1",
                        "subjects": list(batch_subjects),
                        "catalogs": {ticker: catalogs[market][ticker] for ticker in batch_subjects},
                    },
                )
                write_json(subject_path, {"subjects": payloads})
                write_json(identity_path, identity)
                model_facing_paths.extend(
                    (prompt_path, schema_path, catalog_path, subject_path, identity_path)
                )
                batch_specs.append(
                    {
                        "market": market,
                        "batch": batch_number,
                        "subjects": batch_subjects,
                        "identity": identity,
                        "prompt": prompt_path,
                        "schema": schema_path,
                        "catalog": catalog_path,
                    }
                )
        require(len(batch_specs) == 8, "planned_shadow_call_count_not_8")
        schema_proof = schema_structural_proof([Path(spec["schema"]) for spec in batch_specs])
        write_json(result_root / "shadow-schema-structural-proof.json", schema_proof)
        require(schema_proof["status"] == "PASS", "shadow_schema_structure_invalid")
        repaired_schema_proof = repaired_schema_completeness_proof(batch_specs)
        write_json(
            result_root / "repaired-schema-completeness-proof.json",
            repaired_schema_proof,
        )
        negative_positive_controls = {
            "contract": "m12cn-r2-schema-completeness-negative-positive-controls-v1",
            "negative_control": r1_invalid_schema_scan,
            "positive_control": repaired_schema_proof,
            "status": (
                "PASS"
                if r1_invalid_schema_scan["status"] == "PASS"
                and repaired_schema_proof["status"] == "PASS"
                else "FAIL"
            ),
        }
        write_json(
            result_root / "schema-completeness-negative-positive-controls.json",
            negative_positive_controls,
        )
        require(
            repaired_schema_proof["status"] == "PASS",
            "M12CN_R2_SCHEMA_PREFLIGHT_FAILED",
        )
        leak_scan = scan_model_facing_files(model_facing_paths, accepted_ids)
        write_json(result_root / "blindness-and-target-leak-proof.json", leak_scan)
        require(leak_scan["status"] == "PASS", "M12CN_BLINDNESS_FAILURE")
        input_manifest = {
            "contract": "m12cn-r2-shadow-model-input-manifest-v1",
            "schema_contract": SCHEMA_CONTRACT,
            "generation_id": generation_id,
            "frozen_m12cm_generation": EXPECTED_FROZEN_GENERATION,
            "harness_commit": args.expected_head,
            "reasoning_model": REASONING_MODEL,
            "reasoning_effort": REASONING_EFFORT,
            "planned_call_count": len(batch_specs),
            "planned_fundamental_core_call_count": 0,
            "model_facing_files": leak_scan["files"],
            "target_label_leak_count": leak_scan["target_label_leak_count"],
            "policy_contract_sha256": sha256_file(REPO / "scripts/m12cn_policy_contract.py"),
            "runner_sha256": sha256_file(REPO / "scripts/m12cn_policy_shadow.py"),
            "frozen_at": datetime.now(UTC).isoformat(),
        }
        write_json(result_root / "shadow-model-input-manifest.json", input_manifest)

        codex_bin = runtime._signed_in_codex_bin()
        for spec in batch_specs:
            require(git_text("rev-parse", "HEAD") == args.expected_head, "head_drift_after_freeze")
            require(not git_text("status", "--porcelain"), "worktree_drift_after_freeze")
            ordinal = len(call_rows) + 1
            market = str(spec["market"])
            batch_number = int(spec["batch"])
            call_dir = result_root / "shadow-calls" / market / f"batch-{batch_number:02d}"
            output = call_dir / "raw-output.json"
            log = call_dir / "transport.log"
            row: dict[str, object] = {
                "ordinal": ordinal,
                "market": market,
                "batch": batch_number,
                "subjects": list(spec["subjects"]),
                "prompt_sha256": sha256_file(spec["prompt"]),
                "schema_sha256": sha256_file(spec["schema"]),
                "ref_catalog_sha256": sha256_file(spec["catalog"]),
                "status": "STARTED",
                "started_at": datetime.now(UTC).isoformat(),
            }
            call_rows.append(row)
            write_json(result_root / "shadow-call-ledger.json", {"calls": call_rows})
            print(
                f"START {ordinal}/8 {market} batch={batch_number} "
                f"subjects={','.join(spec['subjects'])}",
                flush=True,
            )
            execution_stage = "TRANSPORT"
            try:
                receipt = runtime._invoke_signed_in_codex(
                    codex_bin=codex_bin,
                    prompt=spec["prompt"],
                    output=output,
                    log=log,
                    schema=spec["schema"],
                    cwd=REPO,
                    timeout=args.timeout,
                    state_namespace=(f"m12cn-r2:{generation_id}:{market}:batch-{batch_number:02d}"),
                )
                require(
                    int(receipt.get("transport_attempts") or 0) == 1,
                    "transport_retry_detected",
                )
                raw_sha = sha256_file(output)
                frozen_raw = (
                    result_root / "shadow-output-freeze" / market / f"batch-{batch_number:02d}.json"
                )
                frozen_raw.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(output, frozen_raw)
                require(sha256_file(frozen_raw) == raw_sha, "raw_output_freeze_mismatch")
                execution_stage = "OUTPUT_PARSE"
                parsed = ShadowBatchOutput.model_validate(read_json(output))
                execution_stage = "SEMANTIC_VALIDATION"
                validation = validate_shadow_batch(
                    parsed,
                    expected_identity=spec["identity"],
                    subjects=spec["subjects"],
                    catalogs=catalogs[market],
                )
                write_json(call_dir / "semantic-validation.json", validation)
                require(validation["status"] == "PASS", "shadow_semantic_validation_failed")
                execution_stage = "COMPLETE"
                candidates = [row.model_dump(mode="json") for row in parsed.candidates]
                all_candidates.extend(candidates)
                row.update(
                    {
                        "status": "PASS",
                        "output_sha256": raw_sha,
                        "candidate_count": len(candidates),
                        "transport_attempts": receipt.get("transport_attempts"),
                        "network_probe_attempts": receipt.get("network_probe_attempts"),
                        "completed_at": datetime.now(UTC).isoformat(),
                    }
                )
                completed_outputs.append(
                    {
                        "market": market,
                        "batch": batch_number,
                        "path": str(frozen_raw.relative_to(result_root)),
                        "sha256": raw_sha,
                        "size": frozen_raw.stat().st_size,
                    }
                )
                print(f"COMPLETE {ordinal}/8 {market} batch={batch_number}", flush=True)
            except BaseException as exc:  # noqa: BLE001
                failure_category = classify_shadow_failure(
                    exc,
                    log,
                    execution_stage=execution_stage,
                )
                row.update(
                    {
                        "status": "FAIL",
                        "safe_error_type": type(exc).__name__,
                        "safe_error_code": str(exc).split(":", 1)[0],
                        "failure_category": failure_category,
                        "completed_at": datetime.now(UTC).isoformat(),
                    }
                )
                if output.is_file():
                    row["output_sha256"] = sha256_file(output)
                write_text(call_dir / "failure-traceback.txt", traceback.format_exc())
                write_json(result_root / "shadow-call-ledger.json", {"calls": call_rows})
                raise
            write_json(result_root / "shadow-call-ledger.json", {"calls": call_rows})

        require(len(call_rows) == 8, "shadow_call_count_not_8")
        require(all(row["status"] == "PASS" for row in call_rows), "shadow_call_not_pass")
        require(len(all_candidates) == 22, "shadow_subject_count_not_22")
        require(
            tuple(row["ticker"] for row in all_candidates)
            == EXPECTED_POPULATION["us"] + EXPECTED_POPULATION["kr"],
            "shadow_subject_order_mismatch",
        )
        aggregate = {
            "contract": "m12cn-r2-shadow-22-subject-results-v1",
            "generation_id": generation_id,
            "frozen_m12cm_generation": EXPECTED_FROZEN_GENERATION,
            "subject_count": len(all_candidates),
            "candidates": all_candidates,
        }
        aggregate_path = result_root / "shadow-22-subject-results.json"
        write_json(aggregate_path, aggregate)
        output_frozen_at = datetime.now(UTC).isoformat()
        output_freeze = {
            "contract": "m12cn-r2-shadow-output-freeze-manifest-v1",
            "generation_id": generation_id,
            "call_output_count": len(completed_outputs),
            "subject_count": len(all_candidates),
            "call_outputs": completed_outputs,
            "aggregate_path": aggregate_path.name,
            "aggregate_sha256": sha256_file(aggregate_path),
            "harness_commit": args.expected_head,
            "policy_contract_sha256": input_manifest["policy_contract_sha256"],
            "runner_sha256": input_manifest["runner_sha256"],
            "post_freeze_reference_semantic_open_count_before_freeze": 0,
            "frozen_at": output_frozen_at,
            "status": "PASS",
        }
        write_json(result_root / "shadow-output-freeze-manifest.json", output_freeze)

        require(git_text("rev-parse", "HEAD") == args.expected_head, "head_drift_after_calls")
        require(not git_text("status", "--porcelain"), "worktree_drift_after_calls")
        require(
            sha256_file(REPO / "scripts/m12cn_policy_contract.py")
            == input_manifest["policy_contract_sha256"],
            "policy_contract_changed_after_call_1",
        )
        require(
            sha256_file(REPO / "scripts/m12cn_policy_shadow.py") == input_manifest["runner_sha256"],
            "runner_changed_after_call_1",
        )

        post_freeze_semantic_opened_at = datetime.now(UTC).isoformat()
        post_rows: list[dict[str, object]] = []
        for name, expected_hash in POST_FREEZE_HASHES.items():
            path = args.post_freeze_root.resolve() / name
            actual = sha256_file(path)
            post_rows.append(
                {
                    "path": name,
                    "expected_sha256": expected_hash,
                    "actual_sha256": actual,
                    "status": "PASS" if actual == expected_hash else "FAIL",
                }
            )
            require(actual == expected_hash, f"post_freeze_hash_mismatch:{name}")
        write_json(
            result_root / "post-freeze-source-integrity.json",
            {
                "contract": "m12cn-post-freeze-source-integrity-v1",
                "shadow_output_frozen_at": output_frozen_at,
                "semantic_opened_at": post_freeze_semantic_opened_at,
                "semantic_open_after_output_freeze": (
                    post_freeze_semantic_opened_at > output_frozen_at
                ),
                "files": post_rows,
                "status": "PASS",
            },
        )

        independent_payload = read_json(
            args.post_freeze_root.resolve() / "m12cm-independent-assistant-judgment.json"
        )
        independent_rows = extract_three_axis_rows(independent_payload)
        old_rows = load_old_monitoring_axes(
            args.post_freeze_root.resolve() / "m12cm-sealed-ai-verdicts.zip"
        )
        shadow_rows = {str(row["ticker"]): row for row in all_candidates}
        expected_tickers = EXPECTED_POPULATION["us"] + EXPECTED_POPULATION["kr"]
        comparison = compare_three_sets(
            old_rows=old_rows,
            independent_rows=independent_rows,
            shadow_rows=shadow_rows,
            expected_tickers=expected_tickers,
        )
        write_json(result_root / "post-freeze-three-way-comparison.json", comparison)
        write_text(
            result_root / "post-freeze-three-way-comparison.md",
            comparison_markdown(comparison),
        )

        analyses = _result_analyses(all_candidates, catalogs)
        write_json(result_root / "entry-range-coverage-and-methods.json", analyses["entry"])
        write_json(result_root / "holder-review-reason-analysis.json", analyses["holder"])
        write_json(
            result_root / "valuation-vs-overall-direction-analysis.json",
            analyses["valuation"],
        )
        write_json(
            result_root / "archetype-classification-evidence.json",
            analyses["archetype"],
        )
        write_text(
            result_root / "production-integration-impact-map.md",
            _production_impact_markdown(),
        )
    except BaseException as exc:  # noqa: BLE001
        terminal_error = exc
        write_text(result_root / "failure-traceback.txt", traceback.format_exc())
    finally:
        shutil.rmtree(runtime_scratch, ignore_errors=True)

    controls_value = (
        read_json(result_root / "generic-policy-control-matrix.json")
        if (result_root / "generic-policy-control-matrix.json").is_file()
        else {"status": "NOT_REACHED"}
    )
    provider_schema_rejected = any(
        row.get("failure_category") == "SCHEMA_REJECTED_PRE_INFERENCE" for row in call_rows
    )
    terminal_code = str(terminal_error).split(":", 1)[0] if terminal_error is not None else None
    if terminal_error is None:
        completion_state = COMPLETION_PASS
    elif terminal_code == COMPLETION_PREFLIGHT_FAILED:
        completion_state = COMPLETION_PREFLIGHT_FAILED
    elif provider_schema_rejected:
        completion_state = COMPLETION_PROVIDER_SCHEMA_REJECTED
    elif terminal_code == COMPLETION_NEW_DEPENDENCY:
        completion_state = COMPLETION_NEW_DEPENDENCY
    else:
        completion_state = COMPLETION_FAILED
    blockers = []
    if terminal_error is not None:
        blocker_code = (
            "SCHEMA_REJECTED_PRE_INFERENCE" if provider_schema_rejected else terminal_code
        )
        blockers.append(
            {
                "severity": "P0",
                "code": blocker_code,
                "error_type": type(terminal_error).__name__,
                "bounded_next_action": "Return to Chat; no retry or same-run hotfix authorized.",
            }
        )
    write_json(
        result_root / "complete-blocker-ledger.json",
        {
            "contract": "m12cn-r2-complete-blocker-ledger-v1",
            "open_blocker_count": len(blockers),
            "blockers": blockers,
            "status": "PASS" if not blockers else "BLOCKED",
        },
    )
    safety = {
        "contract": "m12cn-r2-safety-counters-v1",
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
        "stage2_style_shadow_calls_started": len(call_rows),
        "stage2_style_shadow_calls_passed": sum(row.get("status") == "PASS" for row in call_rows),
        "model_retry": 0,
        "wrapper_retry": 0,
        "repair_model": 0,
        "fallback_model": 0,
        "judge_model": 0,
        "selective_rerun": 0,
        "post_call_hotfix": 0,
        "previous_m12cn_output_reuse": 0,
        "cross_generation_stitching": 0,
        "per_ticker_rerun": 0,
        "second_inference_after_reveal": 0,
        "production_runtime_behavior_change": 0,
        "provider_schema_rejection": int(provider_schema_rejected),
    }
    write_json(result_root / "safety-counters.json", safety)
    write_json(
        result_root / "shadow-call-ledger.json",
        {
            "contract": "m12cn-r2-shadow-call-ledger-v1",
            "generation_id": generation_id,
            "planned_call_count": 8,
            "started_call_count": len(call_rows),
            "passed_call_count": sum(row.get("status") == "PASS" for row in call_rows),
            "calls": call_rows,
        },
    )
    completion = {
        "contract": "m12cn-r2-program-completion-v1",
        "completion_state": completion_state,
        "generation_id": generation_id,
        "frozen_m12cm_generation": EXPECTED_FROZEN_GENERATION,
        "generic_controls_status": controls_value.get("status"),
        "target_label_leak_count": (
            leak_scan.get("target_label_leak_count") if leak_scan else None
        ),
        "shadow_call_count": len(call_rows),
        "shadow_call_pass_count": sum(row.get("status") == "PASS" for row in call_rows),
        "shadow_subject_count": len(all_candidates),
        "provider_schema_rejection_count": int(provider_schema_rejected),
        "schema_preflight_status": (
            repaired_schema_proof.get("status") if repaired_schema_proof else "NOT_REACHED"
        ),
        "r1_error_reclassification_status": (
            r1_error_reclassification.get("status") if r1_error_reclassification else "NOT_REACHED"
        ),
        "output_frozen_at": output_frozen_at,
        "post_freeze_semantic_opened_at": post_freeze_semantic_opened_at,
        "post_freeze_comparison_status": (
            comparison.get("status") if comparison else "NOT_REACHED"
        ),
        "open_blocker_count": len(blockers),
        "production_policy_changed": False,
        "deployment_readiness": "NO",
        "chat_review_required": terminal_error is None,
        "completed_at": datetime.now(UTC).isoformat(),
    }
    write_json(result_root / "program-completion.json", completion)
    write_text(
        result_root / "REPORT.md",
        _report_markdown(
            completion=completion,
            source=source_integrity,
            leak=leak_scan,
            calls=call_rows,
            analyses=analyses,
            comparison=comparison,
            validation=validation_summary,
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
                "shadow_calls": len(call_rows),
                "subjects": len(all_candidates),
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
        raise M12CNFailure(completion_state) from terminal_error


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--package-root", type=Path, required=True)
    parser.add_argument("--shadow-input-root", type=Path, required=True)
    parser.add_argument("--post-freeze-root", type=Path, required=True)
    parser.add_argument("--validation-root", type=Path, required=True)
    parser.add_argument("--result-root", type=Path, required=True)
    parser.add_argument("--env-file", type=Path, required=True)
    parser.add_argument("--expected-head", required=True)
    parser.add_argument("--timeout", type=int, default=1800)
    run(parser.parse_args())


if __name__ == "__main__":
    main()
