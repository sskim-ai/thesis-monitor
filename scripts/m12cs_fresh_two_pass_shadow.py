from __future__ import annotations

import argparse
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

from scripts.m12cn_policy_shadow import classify_shadow_failure
from scripts.m12cq_two_pass_contract import (
    build_pass_b_subject_context,
    canonical_sha256,
    pass_a_leakage_scan,
    select_matrix_option,
    validate_new_buyer_consistency,
)
from scripts.m12cq_two_pass_shadow import (
    EXPECTED_POPULATION,
    _post_freeze_comparison,
    load_m12cp_inputs,
)
from scripts.m12cr_contract_closure import (
    _batch_topology,
    _matrix_subjects,
    _mechanical_pass_a_choice,
    _verify_package_root,
    _verify_shadow_input,
    _verify_zip_manifest,
    _write_future_drafts,
    artifact_manifest,
    load_frozen_contract_inputs,
    read_json,
    require,
    sha256_file,
    write_json,
    write_text,
)
from scripts.m12cr_r1_typed_quality_closure import (
    _quality_basis_replay,
    build_typed_audit,
)
from scripts.m12cr_r1_typed_quality_contract import (
    gate_policy_option_for_security_basis,
    validate_quality_basis_decision_ownership,
    validate_security_valuation_basis_gate,
)
from scripts.m12cr_shadow_contract import (
    future_pass_a_batch_schema,
    future_pass_a_prompt_template,
    future_pass_b_batch_schema,
    future_pass_b_prompt_template,
    materialize_future_pass_a,
    normalize_future_pass_b,
    schema_completeness_and_parity_scan,
    target_leak_scan,
    validate_future_pass_b_shape,
    validate_materialized_pass_b,
)
from scripts.m12cs_r1_provider_schema import (
    PROVIDER_WIRE_PROJECTION_CONTRACT,
    SEMANTIC_UNIQUENESS_RULES,
    project_provider_wire_schema,
    scan_provider_structured_output_schema,
)


REPO = Path(__file__).resolve().parents[1]
KST = ZoneInfo("Asia/Seoul")
WORK_INSTRUCTION_COMMIT = "06798ddd8caf330c48fea3bf65e13670dca44f3d"
M12CR_R1_IMPLEMENTATION = "0e96355ad9151344ee30c7e2bfc92bb70be183ec"
EXPECTED_OUTER_PACKAGE_SHA256 = "2462d8507c25fa704b75a774e11ef5bb5e54772d29220dde7445ff89ceab4050"
EXPECTED_M12CR_R1_RESULT_SHA256 = "8d62d38c7915ddbbf77e30bffa29509e5eaa14684e507a58027da62ce51571a8"
EXPECTED_FROZEN_INPUT_SHA256 = "9482ee37f0df9bf26bc8a2d6d36fcb6c1af836b06405776e9947c7fbd18b03aa"
EXPECTED_POST_FREEZE_REFERENCE_SHA256 = (
    "e83f77f4e1872c54c08ef9dca00c4c8f7c07446390c3f40c1ba1d9d5e6f9843f"
)
EXPECTED_FROZEN_GENERATION = "20260917-m12cm-current-v4-smoke-20260917T062918Z-5c0cb075ce8b"

PASS = "M12CS_FRESH_TWO_PASS_CALIBRATION_SHADOW_PASS_READY_FOR_CHAT_REVIEW"
FROZEN_DRIFT = "M12CS_FROZEN_CONTRACT_DRIFT"
PASS_A_FAILED = "M12CS_PASS_A_FAILED"
MATERIALIZATION_FAILED = "M12CS_DETERMINISTIC_MATERIALIZATION_FAILED"
PASS_B_FAILED = "M12CS_PASS_B_FAILED"
BLINDNESS_FAILED = "M12CS_BLINDNESS_OR_TARGET_LEAK_FAILURE"
NEW_DEPENDENCY = "M12CS_NEW_PRODUCTION_DEPENDENCY_REQUIRES_CHAT"

REPORT_NAME = (
    "thesis-monitor-20260918-m12cs-fresh-two-pass-typed-quality-valuation-"
    "calibration-shadow-report.zip"
)


class M12CSFailure(RuntimeError):
    pass


def _git(*args: str) -> str:
    return subprocess.run(
        ("git", *args),
        cwd=REPO,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def runtime_integrity(expected_head: str) -> dict[str, object]:
    head = _git("rev-parse", "HEAD")
    implementation_ancestor = (
        subprocess.run(
            ("git", "merge-base", "--is-ancestor", M12CR_R1_IMPLEMENTATION, head),
            cwd=REPO,
            check=False,
        ).returncode
        == 0
    )
    instruction_ancestor = (
        subprocess.run(
            ("git", "merge-base", "--is-ancestor", WORK_INSTRUCTION_COMMIT, head),
            cwd=REPO,
            check=False,
        ).returncode
        == 0
    )
    changed = _git("diff", "--name-only", f"{M12CR_R1_IMPLEMENTATION}..{head}").splitlines()
    allowed = (
        "docs/work-instructions/20260918-m12cs-",
        "scripts/m12cr_shadow_contract.py",
        "scripts/m12cs_",
        "tests/test_m12cs_",
    )
    production_paths = [path for path in changed if not path.startswith(allowed)]
    errors: list[str] = []
    if head != expected_head:
        errors.append("head_mismatch")
    if not implementation_ancestor:
        errors.append("m12cr_r1_implementation_not_ancestor")
    if not instruction_ancestor:
        errors.append("work_instruction_not_ancestor")
    if production_paths:
        errors.append("new_production_dependency")
    if _git("status", "--porcelain"):
        errors.append("worktree_not_clean")
    return {
        "contract": "m12cs-runtime-integrity-v1",
        "head": head,
        "expected_head": expected_head,
        "m12cr_r1_implementation": M12CR_R1_IMPLEMENTATION,
        "work_instruction_commit": WORK_INSTRUCTION_COMMIT,
        "m12cr_r1_implementation_is_ancestor": implementation_ancestor,
        "work_instruction_is_ancestor": instruction_ancestor,
        "changed_paths": changed,
        "production_dependency_paths": production_paths,
        "errors": errors,
        "status": "PASS" if not errors else "FAIL",
    }


def _verify_extracted_manifest(root: Path) -> dict[str, object]:
    manifest = read_json(root / "artifact-manifest.json")
    errors: list[str] = []
    rows: list[dict[str, object]] = []
    for item in manifest.get("files") or ():
        path = root / str(item["path"])
        actual_sha = sha256_file(path) if path.is_file() else None
        actual_size = path.stat().st_size if path.is_file() else None
        status = (
            "PASS"
            if actual_sha == item.get("sha256") and actual_size == item.get("size")
            else "FAIL"
        )
        if status != "PASS":
            errors.append(f"manifest_mismatch:{item['path']}")
        rows.append(
            {
                "path": item["path"],
                "sha256": actual_sha,
                "size": actual_size,
                "status": status,
            }
        )
    return {
        "root": str(root),
        "manifest_payload_count": len(rows),
        "rows": rows,
        "errors": errors,
        "status": "PASS" if not errors else "FAIL",
    }


def verify_source_base(args: argparse.Namespace) -> dict[str, object]:
    package_root = args.package_root.resolve()
    source_index = read_json(package_root / "source-index.json")
    errors: list[str] = []
    package_sha = sha256_file(args.package_zip.resolve())
    if package_sha != EXPECTED_OUTER_PACKAGE_SHA256:
        errors.append("outer_package_hash_mismatch")
    package = _verify_package_root(package_root)
    if package["status"] != "PASS":
        errors.extend(package["errors"])

    r1_zip = package_root / str(source_index["m12cr_r1_result"]["filename"])
    r1_sha = sha256_file(r1_zip)
    if r1_sha != EXPECTED_M12CR_R1_RESULT_SHA256:
        errors.append("m12cr_r1_result_hash_mismatch")
    r1_manifest = _verify_zip_manifest(r1_zip, expected_count=89)
    if r1_manifest["status"] != "PASS":
        errors.extend(r1_manifest["errors"])
    extracted_manifest = _verify_extracted_manifest(args.m12cr_r1_result_root.resolve())
    if extracted_manifest["status"] != "PASS":
        errors.extend(extracted_manifest["errors"])

    frozen_zip = package_root / str(source_index["frozen_shadow_input"]["filename"])
    frozen_sha = sha256_file(frozen_zip)
    if frozen_sha != EXPECTED_FROZEN_INPUT_SHA256:
        errors.append("frozen_input_hash_mismatch")
    shadow = _verify_shadow_input(package_root, args.shadow_input_root.resolve())
    if shadow["status"] != "PASS":
        errors.extend(shadow["errors"])

    m12cq_package = _verify_package_root(args.m12cq_package_root.resolve())
    if m12cq_package["status"] != "PASS":
        errors.extend(f"m12cq:{item}" for item in m12cq_package["errors"])

    reference = package_root / str(source_index["post_freeze_reference"]["filename"])
    reference_sha = sha256_file(reference)
    if reference_sha != EXPECTED_POST_FREEZE_REFERENCE_SHA256:
        errors.append("post_freeze_reference_hash_mismatch")
    return {
        "contract": "m12cs-source-base-integrity-v1",
        "outer_package_sha256": package_sha,
        "outer_package": package,
        "m12cr_r1_result_sha256": r1_sha,
        "m12cr_r1_result_manifest": r1_manifest,
        "m12cr_r1_extracted_manifest": extracted_manifest,
        "frozen_input_sha256": frozen_sha,
        "frozen_input": shadow,
        "m12cq_package": m12cq_package,
        "post_freeze_reference_sha256": reference_sha,
        "post_freeze_reference_semantic_open_count": 0,
        "frozen_generation": EXPECTED_FROZEN_GENERATION,
        "errors": errors,
        "status": "PASS" if not errors else "FAIL",
    }


def _contract_key(row: Mapping[str, object]) -> tuple[str, str, int]:
    return str(row["stage"]), str(row["market"]), int(row["batch"])


def compare_frozen_draft_hashes(
    regenerated: Mapping[str, object],
    submitted: Mapping[str, object],
) -> dict[str, object]:
    regenerated_rows = {
        _contract_key(row): row for row in regenerated.get("rows") or () if isinstance(row, Mapping)
    }
    submitted_rows = {
        _contract_key(row): row for row in submitted.get("rows") or () if isinstance(row, Mapping)
    }
    keys = sorted(set(regenerated_rows) | set(submitted_rows))
    rows: list[dict[str, object]] = []
    for key in keys:
        actual = regenerated_rows.get(key, {})
        expected = submitted_rows.get(key, {})
        comparisons = {
            field: actual.get(field) == expected.get(field)
            for field in ("schema_sha256", "prompt_sha256", "context_sha256")
        }
        rows.append(
            {
                "stage": key[0],
                "market": key[1],
                "batch": key[2],
                "subjects_match": actual.get("subjects") == expected.get("subjects"),
                "hash_matches": comparisons,
                "scan_status": actual.get("scan", {}).get("status")
                if isinstance(actual.get("scan"), Mapping)
                else None,
                "status": "PASS"
                if all(comparisons.values())
                and actual.get("subjects") == expected.get("subjects")
                and actual.get("status") == "PASS"
                else "FAIL",
            }
        )
    return {
        "contract": "m12cs-m12cr-r1-frozen-draft-hash-parity-v1",
        "expected_count": 16,
        "actual_count": len(rows),
        "rows": rows,
        "mismatch_count": sum(row["status"] != "PASS" for row in rows),
        "status": "PASS"
        if len(rows) == 16 and all(row["status"] == "PASS" for row in rows)
        else "FAIL",
    }


def compare_source_hashes(
    submitted: Mapping[str, object],
) -> dict[str, object]:
    rows = []
    for relative, expected in sorted((submitted.get("source_hashes") or {}).items()):
        path = REPO / str(relative)
        actual = sha256_file(path) if path.is_file() else None
        rows.append(
            {
                "path": relative,
                "expected_sha256": expected,
                "actual_sha256": actual,
                "status": "PASS" if actual == expected else "FAIL",
            }
        )
    return {
        "contract": "m12cs-m12cr-r1-source-hash-binding-v1",
        "rows": rows,
        "mismatch_count": sum(row["status"] != "PASS" for row in rows),
        "status": "PASS" if rows and all(row["status"] == "PASS" for row in rows) else "FAIL",
    }


def pass_a_output_leak_scan(output: Mapping[str, object]) -> dict[str, object]:
    forbidden = (
        "current price",
        "technical",
        "entry range",
        "new buyer",
        "holder",
        "현재가",
        "기술적",
        "진입가",
        "진입 범위",
        "신규 매수",
        "보유자",
    )
    hits: list[dict[str, str]] = []

    def visit(value: object, path: str) -> None:
        if isinstance(value, Mapping):
            for key, item in value.items():
                visit(item, f"{path}.{key}")
        elif isinstance(value, list):
            for index, item in enumerate(value):
                visit(item, f"{path}[{index}]")
        elif isinstance(value, str):
            folded = value.casefold()
            for token in forbidden:
                if token.casefold() in folded:
                    hits.append({"path": path, "token": token})

    visit(output, "$output")
    return {
        "contract": "m12cs-pass-a-output-price-technical-language-scan-v1",
        "forbidden_tokens": list(forbidden),
        "hits": hits,
        "hit_count": len(hits),
        "status": "PASS" if not hits else "FAIL",
    }


def _build_preflight(
    *,
    args: argparse.Namespace,
    result_root: Path,
) -> tuple[
    dict[str, Any],
    dict[str, Mapping[str, object]],
    dict[str, dict[str, dict[str, object]]],
    dict[str, dict[str, Mapping[str, object]]],
    dict[str, dict[str, dict[str, object]]],
    dict[str, Mapping[str, object]],
    dict[str, object],
]:
    contexts, payloads, catalogs, base_pass_a = load_frozen_contract_inputs(
        args.shadow_input_root.resolve()
    )
    m12cp = load_m12cp_inputs(args.m12cq_package_root.resolve())
    matrix = _matrix_subjects(m12cp["options"])
    pass_a_contexts, typed, audit_rows = build_typed_audit(
        contexts=contexts,
        context_payloads=payloads,
        catalogs=catalogs,
        base_pass_a=base_pass_a,
        m12cp_security=m12cp["security"],
    )

    dry_pass_a: dict[str, dict[str, object]] = {}
    dry_options: dict[str, dict[str, object]] = {}
    for spec in _batch_topology(contexts):
        market = str(spec["market"])
        subjects = tuple(spec["subjects"])
        output = {"classifications": {}}
        for ticker in subjects:
            output["classifications"][ticker] = _mechanical_pass_a_choice(
                context=pass_a_contexts[market][ticker],
                matrix_subject=matrix[ticker],
                force_unresolved=False,
            )
        rows, validation = materialize_future_pass_a(
            output,
            subjects=subjects,
            subject_contexts=pass_a_contexts[market],
        )
        require(validation["status"] == "PASS", FROZEN_DRIFT)
        for row in rows:
            ticker = str(row["ticker"])
            dry_pass_a[ticker] = row
            selected = select_matrix_option(matrix[ticker], row)
            gated, receipt = gate_policy_option_for_security_basis(
                selected, typed[ticker]["security_valuation_basis"]
            )
            require(receipt["status"] == "PASS", FROZEN_DRIFT)
            dry_options[ticker] = gated

    dry_pass_b: dict[str, dict[str, dict[str, object]]] = {"us": {}, "kr": {}}
    for market in ("us", "kr"):
        for ticker in contexts[market].selected_subjects:
            value = build_pass_b_subject_context(
                context=payloads[market],
                ticker=ticker,
                catalog=catalogs[market][ticker],
                pass_a=dry_pass_a[ticker],
                policy_option=dry_options[ticker],
            )
            value["business_evidence_quality_state"] = typed[ticker]["business_evidence_quality"]
            value["security_valuation_basis_state"] = typed[ticker]["security_valuation_basis"]
            value["directional_disclosure_quality_refs"] = typed[ticker][
                "directional_disclosure_refs"
            ]
            dry_pass_b[market][ticker] = value

    regenerated_root = result_root / "pre-inference-contract-regeneration"
    regenerated = _write_future_drafts(
        result_root=regenerated_root,
        contexts=contexts,
        pass_a_contexts=pass_a_contexts,
        pass_b_contexts=dry_pass_b,
        catalogs=catalogs,
    )
    schema_freezes = _write_schema_freeze_manifests(
        result_root=result_root,
        regenerated_root=regenerated_root,
        regenerated=regenerated,
    )
    submitted = read_json(
        args.m12cr_r1_result_root / "all-16-schema-completeness-and-parity-scan.json"
    )
    parity = compare_frozen_draft_hashes(regenerated, submitted)
    write_json(
        result_root / "pre-inference-16-schema-reproof.json",
        {**regenerated, "parity": parity, "schema_freezes": schema_freezes},
    )

    submitted_hashes = read_json(
        args.m12cr_r1_result_root / "future-contract-draft-source-hashes.json"
    )
    source_binding = compare_source_hashes(submitted_hashes)
    binding = {
        "contract": "m12cs-m12cr-r1-frozen-contract-binding-v1",
        "m12cr_r1_implementation": M12CR_R1_IMPLEMENTATION,
        "submitted_completion": read_json(args.m12cr_r1_result_root / "program-completion.json"),
        "source_hash_binding": source_binding,
        "draft_hash_parity": parity,
        "status": "PASS" if source_binding["status"] == parity["status"] == "PASS" else "FAIL",
    }
    write_json(result_root / "m12cr-r1-frozen-contract-binding.json", binding)

    regression = _quality_basis_replay(
        audit_rows=audit_rows,
        typed=typed,
        m12cp_security=m12cp["security"],
    )
    write_json(result_root / "quality-basis-regression-reproof.json", regression)
    pass_a_price_leak = pass_a_leakage_scan(
        [
            pass_a_contexts[market][ticker]
            for market in ("us", "kr")
            for ticker in contexts[market].selected_subjects
        ]
    )
    pass_a_target_leak = target_leak_scan(
        [
            pass_a_contexts[market][ticker]
            for market in ("us", "kr")
            for ticker in contexts[market].selected_subjects
        ]
    )
    future_leak = regenerated["target_leak_proof"]
    leak = {
        "contract": "m12cs-target-and-price-leak-proof-v1",
        "pass_a_price_technical_leak": pass_a_price_leak,
        "pass_a_target_leak": pass_a_target_leak,
        "future_target_leak": future_leak,
        "prior_labels_used_count": 0,
        "sealed_reference_open_count": 0,
        "status": "PASS"
        if pass_a_price_leak["status"]
        == pass_a_target_leak["status"]
        == future_leak["status"]
        == "PASS"
        else "FAIL",
    }
    write_json(result_root / "target-and-price-leak-proof.json", leak)
    require(binding["status"] == "PASS", FROZEN_DRIFT)
    require(regenerated["status"] == "PASS" and parity["status"] == "PASS", FROZEN_DRIFT)
    require(regression["status"] == "PASS", FROZEN_DRIFT)
    require(leak["status"] == "PASS", BLINDNESS_FAILED)
    return contexts, payloads, catalogs, pass_a_contexts, typed, matrix, m12cp


def _write_schema_freeze_manifests(
    *,
    result_root: Path,
    regenerated_root: Path,
    regenerated: Mapping[str, object],
) -> dict[str, object]:
    semantic_rows: list[dict[str, object]] = []
    provider_rows: list[dict[str, object]] = []
    for row in regenerated.get("rows") or ():
        stage = str(row["stage"])
        market = str(row["market"])
        batch = int(row["batch"])
        relative = Path(stage) / market / f"batch-{batch:02d}" / "schema.json"
        internal_path = regenerated_root / "future-drafts" / relative
        internal = read_json(internal_path)
        wire, projection = project_provider_wire_schema(internal)
        scan = scan_provider_structured_output_schema(wire)
        wire_path = result_root / "provider-wire-contract" / relative
        write_json(wire_path, wire)
        semantic_rows.append(
            {
                "stage": stage,
                "market": market,
                "batch": batch,
                "subjects": list(row["subjects"]),
                "schema_sha256": sha256_file(internal_path),
                "canonical_schema_sha256": projection["internal_semantic_schema_sha256"],
                "status": row["status"],
            }
        )
        provider_rows.append(
            {
                "stage": stage,
                "market": market,
                "batch": batch,
                "subjects": list(row["subjects"]),
                "path": str(wire_path.relative_to(result_root)),
                "schema_sha256": sha256_file(wire_path),
                "canonical_schema_sha256": projection["provider_wire_schema_sha256"],
                "projection": projection,
                "dialect_scan": scan,
                "status": scan["status"],
            }
        )
    semantic_manifest = {
        "contract": "m12cs-r1-semantic-contract-freeze-manifest-v1",
        "schema_count": len(semantic_rows),
        "schemas": semantic_rows,
        "local_uniqueness_rules": list(SEMANTIC_UNIQUENESS_RULES),
        "semantic_policy_change": "LOCAL_DUPLICATE_ENFORCEMENT_ONLY",
        "status": "PASS"
        if len(semantic_rows) == 16 and all(row["status"] == "PASS" for row in semantic_rows)
        else "FAIL",
    }
    provider_manifest = {
        "contract": "m12cs-r1-provider-wire-contract-freeze-manifest-v1",
        "projection_contract": PROVIDER_WIRE_PROJECTION_CONTRACT,
        "schema_count": len(provider_rows),
        "schemas": provider_rows,
        "unique_items_count": sum(
            row["dialect_scan"]["unique_items_count"] for row in provider_rows
        ),
        "unsupported_keyword_count": sum(
            row["dialect_scan"]["unsupported_keyword_count"] for row in provider_rows
        ),
        "status": "PASS"
        if len(provider_rows) == 16 and all(row["status"] == "PASS" for row in provider_rows)
        else "FAIL",
    }
    semantic_path = result_root / "semantic-contract-freeze-manifest.json"
    provider_path = result_root / "provider-wire-contract-freeze-manifest.json"
    write_json(semantic_path, semantic_manifest)
    write_json(provider_path, provider_manifest)
    require(semantic_manifest["status"] == provider_manifest["status"] == "PASS", FROZEN_DRIFT)
    return {
        "semantic_contract_freeze_sha256": sha256_file(semantic_path),
        "provider_wire_contract_freeze_sha256": sha256_file(provider_path),
        "status": "PASS",
    }


def _planned_ledger(contexts: Mapping[str, Any]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    ordinal = 0
    for stage in ("pass-a", "pass-b"):
        for stage_ordinal, spec in enumerate(_batch_topology(contexts), start=1):
            ordinal += 1
            rows.append(
                {
                    "ordinal": ordinal,
                    "stage_ordinal": stage_ordinal,
                    "stage": stage,
                    "market": spec["market"],
                    "batch": spec["batch"],
                    "subjects": list(spec["subjects"]),
                    "planned": True,
                    "wrapper_attempted": False,
                    "provider_accepted_inference": None,
                    "completed_response": False,
                    "raw_contract_accepted": False,
                    "semantic_accepted": False,
                    "status": "PLANNED",
                }
            )
    return rows


def _ledger_row(
    rows: Sequence[dict[str, object]],
    *,
    stage: str,
    market: str,
    batch: int,
) -> dict[str, object]:
    return next(
        row
        for row in rows
        if row["stage"] == stage and row["market"] == market and row["batch"] == batch
    )


def _write_execution_draft(
    *,
    stage: str,
    call_dir: Path,
    subjects: tuple[str, ...],
    payloads: Sequence[Mapping[str, object]],
    schema: Mapping[str, object],
) -> tuple[Path, Path, Path]:
    template = (
        future_pass_a_prompt_template() if stage == "pass-a" else future_pass_b_prompt_template()
    )
    label = "PASS_A_CONTEXT" if stage == "pass-a" else "PASS_B_CONTEXT"
    prompt = (
        template
        + "\n\nSUBJECT_KEYS:\n"
        + json.dumps(subjects, ensure_ascii=False)
        + f"\n\n{label}:\n"
        + json.dumps(list(payloads), ensure_ascii=False, default=str)
    )
    internal_schema_path = call_dir / "internal-semantic-schema.json"
    schema_path = call_dir / "schema.json"
    prompt_path = call_dir / "prompt.txt"
    context_path = call_dir / "subject-context.json"
    provider_schema, projection = project_provider_wire_schema(schema)
    dialect = scan_provider_structured_output_schema(provider_schema)
    require(dialect["status"] == "PASS", "provider_wire_schema_dialect_preflight_failed")
    write_json(internal_schema_path, schema)
    write_json(schema_path, provider_schema)
    write_json(call_dir / "provider-wire-projection.json", projection)
    write_json(call_dir / "provider-dialect-scan.json", dialect)
    write_text(prompt_path, prompt)
    write_json(context_path, {"subjects": list(payloads)})
    return prompt_path, schema_path, context_path


def _classify_m12cs_failure(
    error: BaseException,
    transport_log: Path | None,
    *,
    execution_stage: str | None = None,
) -> str:
    category = classify_shadow_failure(
        error,
        transport_log,
        execution_stage=execution_stage,
    )
    stage = str(execution_stage or "").upper()
    if category == "SCHEMA_REJECTED_PRE_INFERENCE":
        return (
            "PASS_B_PROVIDER_SCHEMA_REJECTED_PRE_INFERENCE"
            if stage.startswith("PASS_B")
            else "PROVIDER_SCHEMA_DIALECT_REJECTED_PRE_INFERENCE"
        )
    if stage == "PASS_B_OUTPUT_PARSE":
        return "PASS_B_RAW_CONTRACT_FAILED"
    if stage == "PASS_B_RAW_SEMANTIC_VALIDATION":
        return "PASS_B_RAW_SEMANTIC_VALIDATION_FAILED"
    if stage == "PASS_B_MATERIALIZATION":
        return "PASS_B_MATERIALIZATION_FAILED"
    if stage == "PASS_B_FINAL_SEMANTIC_VALIDATION":
        return "PASS_B_FINAL_SEMANTIC_VALIDATION_FAILED"
    return category


def _validation_rule_ids(validation: Mapping[str, object]) -> list[str]:
    return sorted(
        {str(error).rsplit(":", 1)[-1] for error in validation.get("errors") or () if str(error)}
    )


def _assert_execution_freeze(expected_head: str, code_hashes: Mapping[str, str]) -> None:
    require(_git("rev-parse", "HEAD") == expected_head, "head_drift_after_freeze")
    require(not _git("status", "--porcelain"), "worktree_drift_after_freeze")
    for relative, expected in code_hashes.items():
        require(sha256_file(REPO / relative) == expected, f"code_hash_drift:{relative}")


def _invoke_pass_a(
    *,
    contexts: Mapping[str, Any],
    pass_a_contexts: Mapping[str, Mapping[str, Mapping[str, object]]],
    result_root: Path,
    generation_id: str,
    expected_head: str,
    code_hashes: Mapping[str, str],
    runtime: Any,
    codex_bin: str,
    timeout: int,
    ledger: list[dict[str, object]],
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    rows: list[dict[str, object]] = []
    frozen_outputs: list[dict[str, object]] = []
    for spec in _batch_topology(contexts):
        _assert_execution_freeze(expected_head, code_hashes)
        market = str(spec["market"])
        batch = int(spec["batch"])
        subjects = tuple(spec["subjects"])
        call_dir = result_root / "model-calls/pass-a" / market / f"batch-{batch:02d}"
        payload = [pass_a_contexts[market][ticker] for ticker in subjects]
        schema = future_pass_a_batch_schema(
            subjects=subjects,
            subject_contexts=pass_a_contexts[market],
        )
        scan = schema_completeness_and_parity_scan(schema, stage="pass-a", subjects=subjects)
        require(scan["status"] == "PASS", PASS_A_FAILED)
        prompt_path, schema_path, context_path = _write_execution_draft(
            stage="pass-a",
            call_dir=call_dir,
            subjects=subjects,
            payloads=payload,
            schema=schema,
        )
        output_path = call_dir / "raw-output.json"
        log_path = call_dir / "transport.log"
        ledger_row = _ledger_row(ledger, stage="pass-a", market=market, batch=batch)
        ledger_row.update(
            {
                "wrapper_attempted": True,
                "status": "STARTED",
                "prompt_sha256": sha256_file(prompt_path),
                "schema_sha256": sha256_file(schema_path),
                "context_sha256": sha256_file(context_path),
                "started_at": datetime.now(UTC).isoformat(),
            }
        )
        write_json(result_root / "pass-a-call-ledger.json", {"calls": ledger[:8]})
        execution_stage = "TRANSPORT"
        try:
            receipt = runtime._invoke_signed_in_codex(
                codex_bin=codex_bin,
                prompt=prompt_path,
                output=output_path,
                log=log_path,
                schema=schema_path,
                cwd=REPO,
                timeout=timeout,
                state_namespace=f"m12cs:{generation_id}:pass-a:{market}:batch-{batch:02d}",
            )
            require(int(receipt.get("transport_attempts") or 0) == 1, "transport_retry_detected")
            ledger_row["provider_accepted_inference"] = True
            ledger_row["completed_response"] = True
            execution_stage = "OUTPUT_PARSE"
            output = read_json(output_path)
            normalized, validation = materialize_future_pass_a(
                output,
                subjects=subjects,
                subject_contexts=pass_a_contexts[market],
            )
            ledger_row["raw_contract_accepted"] = (
                validation.get("shape", {}).get("status") == "PASS"
            )
            output_leak = pass_a_output_leak_scan(output)
            write_json(call_dir / "output-leak-validation.json", output_leak)
            execution_stage = "PASS_A_SEMANTIC_VALIDATION"
            write_json(call_dir / "semantic-validation.json", validation)
            require(validation["status"] == "PASS", "pass_a_semantic_validation_failed")
            require(output_leak["status"] == "PASS", BLINDNESS_FAILED)
            ledger_row["semantic_accepted"] = True
            output_sha = sha256_file(output_path)
            frozen = result_root / "output-freeze/pass-a" / market / f"batch-{batch:02d}.json"
            frozen.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(output_path, frozen)
            require(sha256_file(frozen) == output_sha, "pass_a_output_freeze_mismatch")
            rows.extend(normalized)
            frozen_outputs.append(
                {
                    "market": market,
                    "batch": batch,
                    "subjects": list(subjects),
                    "path": str(frozen.relative_to(result_root)),
                    "sha256": output_sha,
                    "size": frozen.stat().st_size,
                }
            )
            ledger_row.update(
                {
                    "status": "PASS",
                    "subject_count": len(normalized),
                    "transport_attempts": receipt.get("transport_attempts"),
                    "network_probe_attempts": receipt.get("network_probe_attempts"),
                    "output_sha256": output_sha,
                    "completed_at": datetime.now(UTC).isoformat(),
                }
            )
        except BaseException as exc:  # noqa: BLE001
            ledger_row.update(
                {
                    "status": "FAIL",
                    "safe_error_type": type(exc).__name__,
                    "safe_error_code": str(exc).split(":", 1)[0],
                    "failure_category": _classify_m12cs_failure(
                        exc,
                        log_path,
                        execution_stage=execution_stage,
                    ),
                    "completed_at": datetime.now(UTC).isoformat(),
                }
            )
            write_text(call_dir / "failure-traceback.txt", traceback.format_exc())
            write_json(result_root / "pass-a-call-ledger.json", {"calls": ledger[:8]})
            raise
        write_json(result_root / "pass-a-call-ledger.json", {"calls": ledger[:8]})
    return rows, frozen_outputs


def _invoke_pass_b(
    *,
    contexts: Mapping[str, Any],
    pass_b_contexts: Mapping[str, Mapping[str, Mapping[str, object]]],
    catalogs: Mapping[str, Mapping[str, Mapping[str, object]]],
    pass_a_by_ticker: Mapping[str, Mapping[str, object]],
    policy_options: Mapping[str, Mapping[str, object]],
    typed: Mapping[str, Mapping[str, Mapping[str, object]]],
    result_root: Path,
    generation_id: str,
    expected_head: str,
    code_hashes: Mapping[str, str],
    runtime: Any,
    codex_bin: str,
    timeout: int,
    ledger: list[dict[str, object]],
) -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]]]:
    rows: list[dict[str, object]] = []
    entry_rows: list[dict[str, object]] = []
    frozen_outputs: list[dict[str, object]] = []
    for spec in _batch_topology(contexts):
        _assert_execution_freeze(expected_head, code_hashes)
        market = str(spec["market"])
        batch = int(spec["batch"])
        subjects = tuple(spec["subjects"])
        call_dir = result_root / "model-calls/pass-b" / market / f"batch-{batch:02d}"
        payload = [pass_b_contexts[market][ticker] for ticker in subjects]
        schema = future_pass_b_batch_schema(subjects=subjects, catalogs=catalogs[market])
        scan = schema_completeness_and_parity_scan(schema, stage="pass-b", subjects=subjects)
        require(scan["status"] == "PASS", PASS_B_FAILED)
        prompt_path, schema_path, context_path = _write_execution_draft(
            stage="pass-b",
            call_dir=call_dir,
            subjects=subjects,
            payloads=payload,
            schema=schema,
        )
        output_path = call_dir / "raw-output.json"
        log_path = call_dir / "transport.log"
        ledger_row = _ledger_row(ledger, stage="pass-b", market=market, batch=batch)
        ledger_row.update(
            {
                "wrapper_attempted": True,
                "status": "STARTED",
                "prompt_sha256": sha256_file(prompt_path),
                "schema_sha256": sha256_file(schema_path),
                "context_sha256": sha256_file(context_path),
                "started_at": datetime.now(UTC).isoformat(),
            }
        )
        write_json(result_root / "pass-b-call-ledger.json", {"calls": ledger[8:]})
        execution_stage = "PASS_B_PROVIDER_REQUEST"
        try:
            receipt = runtime._invoke_signed_in_codex(
                codex_bin=codex_bin,
                prompt=prompt_path,
                output=output_path,
                log=log_path,
                schema=schema_path,
                cwd=REPO,
                timeout=timeout,
                state_namespace=f"m12cs:{generation_id}:pass-b:{market}:batch-{batch:02d}",
            )
            require(int(receipt.get("transport_attempts") or 0) == 1, "transport_retry_detected")
            ledger_row["provider_accepted_inference"] = True
            ledger_row["completed_response"] = True
            execution_stage = "PASS_B_OUTPUT_PARSE"
            output = read_json(output_path)
            output_sha = sha256_file(output_path)
            ledger_row["output_sha256"] = output_sha
            execution_stage = "PASS_B_RAW_SEMANTIC_VALIDATION"
            raw_validation = validate_future_pass_b_shape(
                output,
                subjects=subjects,
                catalogs=catalogs[market],
            )
            write_json(call_dir / "raw-semantic-validation.json", raw_validation)
            ledger_row["raw_contract_accepted"] = raw_validation["status"] == "PASS"
            ledger_row["primary_rule_ids"] = _validation_rule_ids(raw_validation)
            require(
                raw_validation["status"] == "PASS",
                "pass_b_raw_semantic_validation_failed",
            )
            execution_stage = "PASS_B_MATERIALIZATION"
            normalized, normalization = normalize_future_pass_b(
                output,
                subjects=subjects,
                catalogs=catalogs[market],
            )
            require(normalization["status"] == "PASS", "pass_b_materialization_failed")
            execution_stage = "PASS_B_FINAL_SEMANTIC_VALIDATION"
            validation = validate_materialized_pass_b(
                normalized,
                subjects=subjects,
                catalogs=catalogs[market],
                pass_a_by_ticker=pass_a_by_ticker,
                policy_options=policy_options,
            )
            ownership = validate_quality_basis_decision_ownership(
                normalized,
                catalogs=catalogs[market],
                typed_states=typed,
            )
            write_json(
                call_dir / "semantic-validation.json",
                {
                    "raw_contract": raw_validation,
                    "normalization": normalization,
                    "materialized": validation,
                    "typed_quality_ownership": ownership,
                    "status": "PASS"
                    if raw_validation["status"]
                    == validation["status"]
                    == ownership["status"]
                    == "PASS"
                    else "FAIL",
                },
            )
            ledger_row["primary_rule_ids"] = _validation_rule_ids(validation)
            require(
                validation["status"] == "PASS",
                "pass_b_final_semantic_validation_failed",
            )
            require(ownership["status"] == "PASS", "pass_b_quality_basis_ownership_failed")
            ledger_row["semantic_accepted"] = True
            frozen = result_root / "output-freeze/pass-b" / market / f"batch-{batch:02d}.json"
            frozen.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(output_path, frozen)
            require(sha256_file(frozen) == output_sha, "pass_b_output_freeze_mismatch")
            rows.extend(normalized)
            entry_rows.extend(validation["entry_rows"])
            frozen_outputs.append(
                {
                    "market": market,
                    "batch": batch,
                    "subjects": list(subjects),
                    "path": str(frozen.relative_to(result_root)),
                    "sha256": output_sha,
                    "size": frozen.stat().st_size,
                }
            )
            ledger_row.update(
                {
                    "status": "PASS",
                    "subject_count": len(normalized),
                    "transport_attempts": receipt.get("transport_attempts"),
                    "network_probe_attempts": receipt.get("network_probe_attempts"),
                    "output_sha256": output_sha,
                    "completed_at": datetime.now(UTC).isoformat(),
                }
            )
        except BaseException as exc:  # noqa: BLE001
            ledger_row.update(
                {
                    "status": "FAIL",
                    "safe_error_type": type(exc).__name__,
                    "safe_error_code": str(exc).split(":", 1)[0],
                    "failure_category": _classify_m12cs_failure(
                        exc,
                        log_path,
                        execution_stage=execution_stage,
                    ),
                    "completed_at": datetime.now(UTC).isoformat(),
                }
            )
            write_text(call_dir / "failure-traceback.txt", traceback.format_exc())
            write_json(result_root / "pass-b-call-ledger.json", {"calls": ledger[8:]})
            raise
        write_json(result_root / "pass-b-call-ledger.json", {"calls": ledger[8:]})
    return rows, entry_rows, frozen_outputs


def _coverage_analysis(
    *,
    rows: Sequence[Mapping[str, object]],
    typed: Mapping[str, Mapping[str, Mapping[str, object]]],
    consistency_rows: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    archetypes = Counter(str(row["company_archetype"]) for row in rows)
    tiers = Counter(str(row["valuation_regime_tier"]) for row in rows)
    unresolved = sorted(
        ticker
        for ticker, state in typed.items()
        if state["security_valuation_basis"]["state"] == "UNRESOLVED"
    )
    resolved_wait = []
    for row in rows:
        entry = row["entry_range"]
        if row["new_buyer"] != "WAIT" or entry["entry_range_status"] != "ENTRY_RANGE_RESOLVED":
            continue
        resolved_wait.append(
            {
                "ticker": row["ticker"],
                "current_price": entry["current_price"],
                "current_price_as_of": entry["current_price_as_of"],
                "fundamental_method": entry["method"],
                "valuation_regime_tier": row["valuation_regime_tier"],
                "preferred_entry_low": entry["preferred_entry_low"],
                "preferred_entry_high": entry["preferred_entry_high"],
                "distance_to_band_pct": entry["distance_to_band_pct"],
                "tactical_context": entry["tactical_entry_band"],
                "canonical_valuation_refs": entry["valuation_basis_refs"],
                "canonical_technical_refs": entry["technical_basis_refs"],
            }
        )
    return {
        "contract": "m12cs-entry-range-coverage-and-methods-v1",
        "subject_count": len(rows),
        "archetype_distribution": dict(sorted(archetypes.items())),
        "valuation_regime_distribution": dict(sorted(tiers.items())),
        "archetype_tier_distribution": dict(
            sorted(
                Counter(
                    f"{row['company_archetype']}|{row['valuation_regime_tier']}" for row in rows
                ).items()
            )
        ),
        "business_quality_distribution": dict(
            sorted(
                Counter(
                    state["business_evidence_quality"]["state"] for state in typed.values()
                ).items()
            )
        ),
        "security_valuation_basis_distribution": dict(
            sorted(
                Counter(
                    state["security_valuation_basis"]["state"] for state in typed.values()
                ).items()
            )
        ),
        "axis_distributions": {
            field: dict(sorted(Counter(str(row[field]) for row in rows).items()))
            for field in ("overall_direction", "new_buyer", "holder")
        },
        "buy_wait_holdable_count": sum(
            row["overall_direction"] == "BUY"
            and row["new_buyer"] == "WAIT"
            and row["holder"] == "HOLDABLE"
            for row in rows
        ),
        "holder_review_count": sum(row["holder"] == "REVIEW" for row in rows),
        "holder_review_reason_classes": dict(
            sorted(
                Counter(
                    str(row["holder_reason_class"]) for row in rows if row["holder"] == "REVIEW"
                ).items()
            )
        ),
        "security_basis_unresolved_subjects": unresolved,
        "security_basis_unresolved_new_buyer_outcomes": {
            ticker: next(row["new_buyer"] for row in rows if row["ticker"] == ticker)
            for ticker in unresolved
        },
        "fundamental_status": dict(
            sorted(Counter(str(row["fundamental_option"]["status"]) for row in rows).items())
        ),
        "wait_with_resolved_entry_range_count": len(resolved_wait),
        "wait_with_unresolved_fundamental_count": sum(
            row["new_buyer"] == "WAIT" and row["fundamental_option"]["status"] != "RESOLVED"
            for row in rows
        ),
        "resolved_wait_ranges": resolved_wait,
        "tactical_status": dict(
            sorted(
                Counter(
                    str(row["entry_range"]["tactical_entry_band"]["status"]) for row in rows
                ).items()
            )
        ),
        "directional_quality_distribution": dict(
            sorted(Counter(str(row["data_quality_effect"]) for row in rows).items())
        ),
        "new_buyer_consistency_pass_count": sum(
            row.get("status") == "PASS" for row in consistency_rows
        ),
        "status": "PASS" if len(rows) == 22 else "FAIL",
    }


def _run_command(
    *,
    name: str,
    command: Sequence[str],
    output_dir: Path,
) -> dict[str, object]:
    output_dir.mkdir(parents=True, exist_ok=True)
    completed = subprocess.run(
        tuple(command),
        cwd=REPO,
        env=os.environ.copy(),
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
        "log": str(log.relative_to(output_dir.parent.parent)),
        "status": "PASS" if completed.returncode == 0 else "FAIL",
    }


def _test_count(log: str) -> tuple[int, int]:
    passed = re.search(r"(\d+) passed", log)
    skipped = re.search(r"(\d+) skipped", log)
    return (int(passed.group(1)) if passed else 0, int(skipped.group(1)) if skipped else 0)


def run_validation(result_root: Path, *, phase: str) -> dict[str, object]:
    output = result_root / "validation" / phase
    if phase == "precall":
        suites = {
            "focused": (
                "tests/test_m12cs_fresh_two_pass_shadow.py",
                "tests/test_m12cs_r1_provider_schema.py",
                "tests/test_m12cr_r1_typed_quality_contract.py",
                "tests/test_m12cr_shadow_contract.py",
                "tests/test_m12cq_two_pass_policy_shadow.py",
                "tests/test_m12cp_valuation_policy.py",
                "tests/test_m12co_entry_range_design.py",
                "tests/test_m12cn_policy_contract.py",
                "tests/test_accepted_decision_v2_runtime.py",
                "tests/test_stage2_maturity_polarity_adapter.py",
            ),
            "frozen-contract": (
                "tests/test_m12cs_fresh_two_pass_shadow.py",
                "tests/test_m12cs_r1_provider_schema.py",
                "tests/test_m12cr_r1_typed_quality_contract.py",
                "tests/test_m12cr_shadow_contract.py",
                "tests/test_m12cq_two_pass_policy_shadow.py",
                "tests/test_m12cn_policy_contract.py",
            ),
        }
    else:
        suites = {
            "focused": (
                "tests/test_m12cs_fresh_two_pass_shadow.py",
                "tests/test_m12cs_r1_provider_schema.py",
                "tests/test_m12cr_r1_typed_quality_contract.py",
                "tests/test_m12cr_shadow_contract.py",
                "tests/test_m12cq_two_pass_policy_shadow.py",
                "tests/test_m12cp_valuation_policy.py",
                "tests/test_m12co_entry_range_design.py",
                "tests/test_m12cn_policy_contract.py",
                "tests/test_accepted_decision_v2_runtime.py",
                "tests/test_stage2_maturity_polarity_adapter.py",
            ),
            "frozen-contract": (
                "tests/test_m12cs_fresh_two_pass_shadow.py",
                "tests/test_m12cs_r1_provider_schema.py",
                "tests/test_m12cr_r1_typed_quality_contract.py",
                "tests/test_m12cr_shadow_contract.py",
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
    rows = [
        _run_command(
            name=name,
            command=(
                sys.executable,
                "-m",
                "pytest",
                "-q",
                *paths,
                f"--junitxml={output / f'{name}-junit.xml'}",
            ),
            output_dir=output,
        )
        for name, paths in suites.items()
    ]
    ruff = str(Path(sys.executable).with_name("ruff"))
    targets = (
        "scripts/m12cs_fresh_two_pass_shadow.py",
        "scripts/m12cs_r1_provider_schema.py",
        "tests/test_m12cs_fresh_two_pass_shadow.py",
        "tests/test_m12cs_r1_provider_schema.py",
        "scripts/m12cr_r1_typed_quality_contract.py",
        "scripts/m12cr_shadow_contract.py",
    )
    rows.extend(
        (
            _run_command(name="ruff", command=(ruff, "check", *targets), output_dir=output),
            _run_command(
                name="ruff-format",
                command=(ruff, "format", "--check", *targets),
                output_dir=output,
            ),
            _run_command(name="diff-check", command=("git", "diff", "--check"), output_dir=output),
        )
    )
    counts = {}
    for row in rows:
        if row["name"] not in suites:
            continue
        log = (output / f"{row['name']}.log").read_text(encoding="utf-8")
        passed, skipped = _test_count(log)
        counts[row["name"]] = {"passed": passed, "skipped": skipped}
    baseline = {"status": "PASS"}
    if phase == "postcall":
        baseline = {
            "focused_minimum": 254,
            "frozen_contract_minimum": 163,
            "full_minimum": 4375,
            "treasury_krx_minimum": 121,
            "skipped_maximum": 63,
            "counts": counts,
            "status": "PASS"
            if counts.get("focused", {}).get("passed", 0) >= 254
            and counts.get("frozen-contract", {}).get("passed", 0) >= 163
            and counts.get("full", {}).get("passed", 0) >= 4375
            and counts.get("treasury-krx", {}).get("passed", 0) >= 121
            and counts.get("full", {}).get("skipped", 0) <= 63
            else "FAIL",
        }
    return {
        "contract": f"m12cs-{phase}-validation-v1",
        "commands": rows,
        "counts": counts,
        "baseline": baseline,
        "status": "PASS"
        if all(row["status"] == "PASS" for row in rows) and baseline["status"] == "PASS"
        else "FAIL",
    }


def _report_markdown(
    *,
    completion: Mapping[str, object],
    coverage: Mapping[str, object] | None,
    validation: Mapping[str, object] | None,
    comparison: Mapping[str, object] | None,
    ledger: Sequence[Mapping[str, object]],
) -> str:
    pass_a = sum(row.get("stage") == "pass-a" and row.get("status") == "PASS" for row in ledger)
    pass_b = sum(row.get("stage") == "pass-b" and row.get("status") == "PASS" for row in ledger)
    reference_line = (
        "Post-freeze reference semantic access: `1 / REACHED_AFTER_FINAL_FREEZE`."
        if comparison is not None
        else "Post-freeze reference semantic access: `0 / NOT_REACHED`."
    )
    return "\n".join(
        [
            "# M12CS Fresh Two-Pass Typed-Quality / Valuation Calibration Shadow",
            "",
            f"- Completion: `{completion['completion_state']}`",
            f"- Generation: `{completion.get('generation_id')}`",
            f"- Work-instruction commit: `{WORK_INSTRUCTION_COMMIT}`",
            f"- Implementation commit: `{completion.get('implementation_commit')}`",
            f"- Frozen M12CM generation: `{EXPECTED_FROZEN_GENERATION}`",
            f"- Pass A accepted calls: `{pass_a}/8`",
            f"- Pass B accepted calls: `{pass_b}/8`",
            f"- Subjects: `{completion.get('subject_count', 0)}/22`",
            f"- Business quality: `{(coverage or {}).get('business_quality_distribution')}`",
            f"- Security valuation basis: `{(coverage or {}).get('security_valuation_basis_distribution')}`",
            f"- Overall: `{(coverage or {}).get('axis_distributions', {}).get('overall_direction')}`",
            f"- New Buyer: `{(coverage or {}).get('axis_distributions', {}).get('new_buyer')}`",
            f"- Holder: `{(coverage or {}).get('axis_distributions', {}).get('holder')}`",
            f"- BUY / WAIT / HOLDABLE: `{(coverage or {}).get('buy_wait_holdable_count')}`",
            f"- Holder REVIEW: `{(coverage or {}).get('holder_review_count')}`",
            f"- Validation: `{(validation or {}).get('status', 'NOT_REACHED')}`",
            f"- Post-freeze comparison: `{(comparison or {}).get('status', 'NOT_REACHED')}`",
            "- Production runtime/config changes: `0`",
            "- Production send/DB/scheduler/broker actions: `0`",
            "- Main merge / remote push / deploy: `0`",
            "",
            "M12CS executed the frozen M12CR-R1 semantic contract with its separately frozen provider-wire schema projection.",
            reference_line,
        ]
    )


def _zip_tree(source: Path, destination: Path) -> dict[str, object]:
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


def run(args: argparse.Namespace) -> None:
    result_root = args.result_root.resolve()
    require(not result_root.exists(), "result_root_already_exists")
    result_root.mkdir(parents=True)
    scratch = result_root.parent / f".{result_root.name}-runtime"
    require(not scratch.exists(), "runtime_scratch_already_exists")
    scratch.mkdir()

    stage = "SOURCE_PREFLIGHT"
    completion_state = NEW_DEPENDENCY
    terminal_error: BaseException | None = None
    generation_id: str | None = None
    coverage: dict[str, object] | None = None
    comparison: dict[str, object] | None = None
    validation: dict[str, object] | None = None
    combined_rows: list[dict[str, object]] = []
    ledger: list[dict[str, object]] = []
    final_frozen_at: str | None = None
    model_calls_started = False

    try:
        integrity = runtime_integrity(args.expected_head)
        sources = verify_source_base(args)
        write_json(
            result_root / "source-base-integrity.json",
            {
                "runtime": integrity,
                "sources": sources,
                "status": "PASS" if integrity["status"] == sources["status"] == "PASS" else "FAIL",
            },
        )
        require(integrity["status"] == "PASS", NEW_DEPENDENCY)
        require(sources["status"] == "PASS", NEW_DEPENDENCY)

        stage = "FROZEN_CONTRACT_PREFLIGHT"
        contexts, payloads, catalogs, pass_a_contexts, typed, matrix, m12cp = _build_preflight(
            args=args,
            result_root=result_root,
        )
        ledger = _planned_ledger(contexts)
        write_json(result_root / "pass-a-call-ledger.json", {"calls": ledger[:8]})
        write_json(result_root / "pass-b-call-ledger.json", {"calls": ledger[8:]})

        precall = run_validation(result_root, phase="precall")
        write_json(result_root / "validation/precall/summary.json", precall)
        require(precall["status"] == "PASS", FROZEN_DRIFT)

        os.environ["THESIS_MONITOR_ENV_FILE"] = str(args.env_file.resolve())
        os.environ["DATA_DIR"] = str(scratch)
        os.environ["DATABASE_URL"] = f"sqlite:///{scratch / 'shadow.sqlite3'}"
        os.environ["NOTIFICATION_DRY_RUN"] = "true"
        os.environ["NOTIFICATION_RECIPIENT_CLASS"] = "test"
        os.environ["AI_REVIEW_MODE"] = "shadow"
        os.environ["PERSISTENCE_V2_WRITER_ENABLED"] = "false"
        os.environ["PERSISTENCE_V2_OUTBOX_DELIVERY_ENABLED"] = "false"

        from app.jobs import accepted_decision_v2_runtime as runtime
        from app.services.accepted_decision_v2_runtime_service import (
            REASONING_EFFORT,
            REASONING_MODEL,
        )

        require(REASONING_MODEL == "gpt-5.6-sol", "configured_model_drift")
        require(REASONING_EFFORT == "xhigh", "configured_effort_drift")
        runtime.V2_TRANSPORT_ATTEMPT_LIMIT = 1
        now = datetime.now(UTC)
        generation_id = (
            f"{now.astimezone(KST):%Y%m%d}-m12cs-fresh-two-pass-"
            f"{now:%Y%m%dT%H%M%SZ}-{args.expected_head[:12]}"
        )
        code_paths = (
            "scripts/m12cs_fresh_two_pass_shadow.py",
            "scripts/m12cs_r1_provider_schema.py",
            "scripts/m12cr_r1_typed_quality_closure.py",
            "scripts/m12cr_r1_typed_quality_contract.py",
            "scripts/m12cr_contract_closure.py",
            "scripts/m12cr_shadow_contract.py",
            "scripts/m12cq_two_pass_contract.py",
        )
        code_hashes = {path: sha256_file(REPO / path) for path in code_paths}
        input_freeze = {
            "contract": "m12cs-model-input-and-contract-freeze-v1",
            "generation_id": generation_id,
            "implementation_commit": args.expected_head,
            "model": REASONING_MODEL,
            "effort": REASONING_EFFORT,
            "frozen_generation": EXPECTED_FROZEN_GENERATION,
            "planned_calls": 16,
            "transport_attempt_limit": 1,
            "code_hashes": code_hashes,
            "semantic_contract_freeze_sha256": sha256_file(
                result_root / "semantic-contract-freeze-manifest.json"
            ),
            "provider_wire_contract_freeze_sha256": sha256_file(
                result_root / "provider-wire-contract-freeze-manifest.json"
            ),
            "post_freeze_reference_semantic_open_count": 0,
            "frozen_at": datetime.now(UTC).isoformat(),
        }
        write_json(result_root / "model-input-freeze.json", input_freeze)
        codex_bin = runtime._signed_in_codex_bin()

        stage = "PASS_A_CALLS"
        model_calls_started = True
        pass_a_rows, pass_a_outputs = _invoke_pass_a(
            contexts=contexts,
            pass_a_contexts=pass_a_contexts,
            result_root=result_root,
            generation_id=generation_id,
            expected_head=args.expected_head,
            code_hashes=code_hashes,
            runtime=runtime,
            codex_bin=codex_bin,
            timeout=args.timeout,
            ledger=ledger,
        )
        expected_tickers = list(EXPECTED_POPULATION["us"] + EXPECTED_POPULATION["kr"])
        require(len(pass_a_rows) == 22, PASS_A_FAILED)
        require([row["ticker"] for row in pass_a_rows] == expected_tickers, PASS_A_FAILED)
        pass_a_path = result_root / "pass-a-22-subject-classification.json"
        write_json(
            pass_a_path,
            {
                "contract": "m12cs-pass-a-22-subject-classification-v1",
                "generation_id": generation_id,
                "subject_count": 22,
                "classifications": pass_a_rows,
            },
        )
        pass_a_frozen_at = datetime.now(UTC).isoformat()
        write_json(
            result_root / "pass-a-output-freeze-manifest.json",
            {
                "contract": "m12cs-pass-a-output-freeze-manifest-v1",
                "generation_id": generation_id,
                "call_output_count": len(pass_a_outputs),
                "subject_count": 22,
                "call_outputs": pass_a_outputs,
                "aggregate_sha256": sha256_file(pass_a_path),
                "frozen_at": pass_a_frozen_at,
                "status": "PASS",
            },
        )

        stage = "DETERMINISTIC_MATERIALIZATION"
        pass_a_by_ticker = {str(row["ticker"]): row for row in pass_a_rows}
        policy_options: dict[str, dict[str, object]] = {}
        gate_receipts: list[dict[str, object]] = []
        for ticker in expected_tickers:
            selected = select_matrix_option(matrix[ticker], pass_a_by_ticker[ticker])
            gated, receipt = gate_policy_option_for_security_basis(
                selected,
                typed[ticker]["security_valuation_basis"],
            )
            require(receipt["status"] == "PASS", MATERIALIZATION_FAILED)
            policy_options[ticker] = gated
            gate_receipts.append(receipt)
        gate = validate_security_valuation_basis_gate(
            policy_options=policy_options,
            security_basis_by_ticker={
                ticker: state["security_valuation_basis"] for ticker, state in typed.items()
            },
        )
        require(gate["status"] == "PASS", MATERIALIZATION_FAILED)
        write_json(
            result_root / "fundamental-option-materialization-22.json",
            {
                "contract": "m12cs-fundamental-option-materialization-22-v1",
                "generation_id": generation_id,
                "subject_count": 22,
                "model_authored_fundamental_price_ref_status_count": 0,
                "rows": [policy_options[ticker] for ticker in expected_tickers],
                "gate_receipts": gate_receipts,
                "security_basis_gate": gate,
                "status": "PASS",
            },
        )
        write_json(
            result_root / "business-quality-runtime-22.json",
            {
                "contract": "m12cs-business-quality-runtime-22-v1",
                "rows": [
                    {"ticker": ticker, **typed[ticker]["business_evidence_quality"]}
                    for ticker in expected_tickers
                ],
                "status": "PASS",
            },
        )
        write_json(
            result_root / "security-valuation-basis-runtime-22.json",
            {
                "contract": "m12cs-security-valuation-basis-runtime-22-v1",
                "rows": [
                    {"ticker": ticker, **typed[ticker]["security_valuation_basis"]}
                    for ticker in expected_tickers
                ],
                "status": "PASS",
            },
        )

        pass_b_contexts: dict[str, dict[str, dict[str, object]]] = {"us": {}, "kr": {}}
        for market in ("us", "kr"):
            for ticker in contexts[market].selected_subjects:
                value = build_pass_b_subject_context(
                    context=payloads[market],
                    ticker=ticker,
                    catalog=catalogs[market][ticker],
                    pass_a=pass_a_by_ticker[ticker],
                    policy_option=policy_options[ticker],
                )
                value["business_evidence_quality_state"] = typed[ticker][
                    "business_evidence_quality"
                ]
                value["security_valuation_basis_state"] = typed[ticker]["security_valuation_basis"]
                value["directional_disclosure_quality_refs"] = typed[ticker][
                    "directional_disclosure_refs"
                ]
                pass_b_contexts[market][ticker] = value
        write_json(
            result_root / "pass-b-fresh-context-binding.json",
            {
                "contract": "m12cs-pass-b-fresh-context-binding-v1",
                "pass_a_aggregate_sha256": sha256_file(pass_a_path),
                "pass_a_frozen_at": pass_a_frozen_at,
                "template_sha256": canonical_sha256(future_pass_b_prompt_template()),
                "context_builder_sha256": code_hashes["scripts/m12cq_two_pass_contract.py"],
                "schema_contract_sha256": code_hashes["scripts/m12cr_shadow_contract.py"],
                "subject_count": 22,
                "status": "PASS",
            },
        )

        stage = "PASS_B_CALLS"
        pass_b_rows, entry_rows, pass_b_outputs = _invoke_pass_b(
            contexts=contexts,
            pass_b_contexts=pass_b_contexts,
            catalogs=catalogs,
            pass_a_by_ticker=pass_a_by_ticker,
            policy_options=policy_options,
            typed=typed,
            result_root=result_root,
            generation_id=generation_id,
            expected_head=args.expected_head,
            code_hashes=code_hashes,
            runtime=runtime,
            codex_bin=codex_bin,
            timeout=args.timeout,
            ledger=ledger,
        )
        require(len(pass_b_rows) == 22, PASS_B_FAILED)
        require([row["ticker"] for row in pass_b_rows] == expected_tickers, PASS_B_FAILED)
        pass_b_path = result_root / "pass-b-22-subject-decisions.json"
        write_json(
            pass_b_path,
            {
                "contract": "m12cs-pass-b-22-subject-decisions-v1",
                "generation_id": generation_id,
                "subject_count": 22,
                "decisions": pass_b_rows,
            },
        )
        write_json(
            result_root / "pass-b-output-freeze-manifest.json",
            {
                "contract": "m12cs-pass-b-output-freeze-manifest-v1",
                "generation_id": generation_id,
                "call_output_count": len(pass_b_outputs),
                "subject_count": 22,
                "call_outputs": pass_b_outputs,
                "aggregate_sha256": sha256_file(pass_b_path),
                "frozen_at": datetime.now(UTC).isoformat(),
                "status": "PASS",
            },
        )

        stage = "FINAL_MATERIALIZATION"
        pass_b_by_ticker = {str(row["ticker"]): row for row in pass_b_rows}
        entry_by_ticker = {str(row["ticker"]): row["entry_range"] for row in entry_rows}
        consistency_rows: list[dict[str, object]] = []
        market_by_ticker = {
            ticker: market for market in ("us", "kr") for ticker in EXPECTED_POPULATION[market]
        }
        for ticker in expected_tickers:
            market = market_by_ticker[ticker]
            decision = pass_b_by_ticker[ticker]
            entry = entry_by_ticker[ticker]
            consistency = validate_new_buyer_consistency(
                decision=decision,
                policy_option=policy_options[ticker],
                entry_range=entry,
                catalog=catalogs[market][ticker],
            )
            require(consistency["status"] == "PASS", MATERIALIZATION_FAILED)
            consistency_rows.append(consistency)
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
                    "business_evidence_quality": typed[ticker]["business_evidence_quality"],
                    "security_valuation_basis": typed[ticker]["security_valuation_basis"],
                    "fundamental_option": policy_options[ticker],
                    "entry_range": entry,
                }
            )
        ownership = validate_quality_basis_decision_ownership(
            pass_b_rows,
            catalogs={
                ticker: catalogs[market_by_ticker[ticker]][ticker] for ticker in expected_tickers
            },
            typed_states=typed,
        )
        require(ownership["status"] == "PASS", PASS_B_FAILED)
        write_json(
            result_root / "runtime-entry-range-materialization-22.json",
            {
                "contract": "m12cs-runtime-entry-range-materialization-22-v1",
                "subject_count": 22,
                "rows": entry_rows,
                "model_authored_deterministic_entry_metadata_count": 0,
                "status": "PASS",
            },
        )
        write_json(
            result_root / "new-buyer-consistency-results.json",
            {
                "contract": "m12cs-new-buyer-consistency-results-v1",
                "subject_count": 22,
                "pass_count": sum(row["status"] == "PASS" for row in consistency_rows),
                "rows": consistency_rows,
                "status": "PASS",
            },
        )
        write_json(
            result_root / "quality-basis-policy-results.json",
            ownership,
        )
        write_json(
            result_root / "overall-holder-policy-validation.json",
            {
                "contract": "m12cs-overall-holder-policy-validation-v1",
                "subject_count": 22,
                "typed_quality_ownership": ownership,
                "valuation_only_holder_review_count": 0,
                "security_basis_sole_overall_downgrade_count": 0,
                "security_basis_sole_holder_downgrade_count": 0,
                "status": ownership["status"],
            },
        )
        aggregate_path = result_root / "shadow-22-subject-results.json"
        write_json(
            aggregate_path,
            {
                "contract": "m12cs-shadow-22-subject-results-v1",
                "generation_id": generation_id,
                "frozen_m12cm_generation": EXPECTED_FROZEN_GENERATION,
                "subject_count": 22,
                "candidates": combined_rows,
            },
        )
        coverage = _coverage_analysis(
            rows=combined_rows,
            typed=typed,
            consistency_rows=consistency_rows,
        )
        write_json(result_root / "entry-range-coverage-and-methods.json", coverage)
        require(coverage["status"] == "PASS", MATERIALIZATION_FAILED)

        _assert_execution_freeze(args.expected_head, code_hashes)
        final_frozen_at = datetime.now(UTC).isoformat()
        freeze_manifest = {
            "contract": "m12cs-final-shadow-freeze-manifest-v1",
            "generation_id": generation_id,
            "subject_count": 22,
            "pass_a_call_output_count": len(pass_a_outputs),
            "pass_b_call_output_count": len(pass_b_outputs),
            "aggregate_sha256": sha256_file(aggregate_path),
            "entry_materialization_sha256": sha256_file(
                result_root / "runtime-entry-range-materialization-22.json"
            ),
            "coverage_sha256": sha256_file(result_root / "entry-range-coverage-and-methods.json"),
            "post_freeze_reference_semantic_open_count_before_freeze": 0,
            "frozen_at": final_frozen_at,
            "status": "PASS",
        }
        write_json(result_root / "final-shadow-freeze-manifest.json", freeze_manifest)

        stage = "POST_FREEZE_COMPARISON"
        comparison = _post_freeze_comparison(
            archive_path=args.package_root / "post-freeze-reference/post-freeze-reference.zip",
            rows=combined_rows,
            frozen_at=final_frozen_at,
            result_root=result_root,
        )
        comparison["contract"] = "m12cs-post-freeze-three-way-comparison-v1"
        comparison["security_basis_unresolved_descriptive_rows"] = [
            row
            for row in comparison.get("rows") or ()
            if row.get("ticker") in set(coverage["security_basis_unresolved_subjects"])
        ]
        write_json(result_root / "post-freeze-three-way-comparison.json", comparison)

        stage = "POSTCALL_VALIDATION"
        validation = run_validation(result_root, phase="postcall")
        write_json(result_root / "validation/postcall/summary.json", validation)
        require(validation["status"] == "PASS", NEW_DEPENDENCY)
        completion_state = PASS
    except BaseException as exc:  # noqa: BLE001
        terminal_error = exc
        write_text(result_root / "failure-traceback.txt", traceback.format_exc())
        code = str(exc).split(":", 1)[0]
        if code in {FROZEN_DRIFT, BLINDNESS_FAILED}:
            completion_state = code
        elif stage.startswith("PASS_A"):
            completion_state = PASS_A_FAILED
        elif stage in {"DETERMINISTIC_MATERIALIZATION", "FINAL_MATERIALIZATION"}:
            completion_state = MATERIALIZATION_FAILED
        elif stage.startswith("PASS_B"):
            completion_state = PASS_B_FAILED
        else:
            completion_state = NEW_DEPENDENCY
    finally:
        shutil.rmtree(scratch, ignore_errors=True)

    blockers = []
    if terminal_error is not None:
        failed_call = next(
            (row for row in reversed(ledger) if row.get("status") == "FAIL"),
            None,
        )
        causal_category = (
            failed_call.get("failure_category") if isinstance(failed_call, Mapping) else None
        )
        blockers.append(
            {
                "stage": stage,
                "causal_category": causal_category,
                "safe_error_type": type(terminal_error).__name__,
                "underlying_safe_wrapper_error_code": str(terminal_error).split(":", 1)[0],
            }
        )
    completion = {
        "contract": "m12cs-program-completion-v1",
        "completion_state": completion_state,
        "generation_id": generation_id,
        "implementation_commit": args.expected_head,
        "work_instruction_commit": WORK_INSTRUCTION_COMMIT,
        "frozen_generation": EXPECTED_FROZEN_GENERATION,
        "subject_count": len(combined_rows),
        "planned_external_model_calls": 16,
        "wrapper_attempted_calls": sum(bool(row.get("wrapper_attempted")) for row in ledger),
        "completed_model_responses": sum(bool(row.get("completed_response")) for row in ledger),
        "semantic_accepted_calls": sum(bool(row.get("semantic_accepted")) for row in ledger),
        "model_calls_started": model_calls_started,
        "final_shadow_frozen_at": final_frozen_at,
        "post_freeze_reference_semantic_open_count": 1 if comparison is not None else 0,
        "validation_status": (validation or {}).get("status"),
        "open_blocker_count": len(blockers),
        "completed_at": datetime.now(UTC).isoformat(),
    }
    write_json(
        result_root / "complete-blocker-ledger.json", {"blockers": blockers, "count": len(blockers)}
    )
    write_json(
        result_root / "safety-counters.json",
        {
            "contract": "m12cs-safety-counters-v1",
            "external_model_calls_planned": 16,
            "external_model_wrappers_attempted": completion["wrapper_attempted_calls"],
            "market_refresh": 0,
            "production_runtime_behavior_changes": 0,
            "production_config_changes": 0,
            "production_sends": 0,
            "production_intents": 0,
            "production_db_writes": 0,
            "scheduler_changes": 0,
            "broker_reads": 0,
            "broker_orders": 0,
            "broker_modifies": 0,
            "broker_cancels": 0,
            "main_merge": 0,
            "remote_push": 0,
            "deployment": 0,
            "repair_model_calls": 0,
            "judge_model_calls": 0,
            "fallback_model_calls": 0,
            "selective_reruns": 0,
            "post_call_hotfixes": 0,
            "sealed_reference_open_count": 1 if comparison is not None else 0,
        },
    )
    write_json(result_root / "program-completion.json", completion)
    write_text(
        result_root / "REPORT.md",
        _report_markdown(
            completion=completion,
            coverage=coverage,
            validation=validation,
            comparison=comparison,
            ledger=ledger,
        ),
    )
    write_json(result_root / "artifact-manifest.json", artifact_manifest(result_root))
    args.output_zip.parent.mkdir(parents=True, exist_ok=True)
    archive = _zip_tree(result_root, args.output_zip.resolve())
    write_text(args.output_zip.with_suffix(args.output_zip.suffix + ".sha256"), archive["sha256"])
    print(json.dumps({"completion": completion, "archive": archive}, ensure_ascii=False, indent=2))
    if terminal_error is not None:
        raise SystemExit(1)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--package-zip", type=Path, required=True)
    parser.add_argument("--package-root", type=Path, required=True)
    parser.add_argument("--m12cr-r1-result-root", type=Path, required=True)
    parser.add_argument("--m12cq-package-root", type=Path, required=True)
    parser.add_argument("--shadow-input-root", type=Path, required=True)
    parser.add_argument("--result-root", type=Path, required=True)
    parser.add_argument("--output-zip", type=Path, required=True)
    parser.add_argument("--expected-head", required=True)
    parser.add_argument("--env-file", type=Path, default=REPO / ".env")
    parser.add_argument("--timeout", type=int, default=1800)
    run(parser.parse_args())


if __name__ == "__main__":
    main()
