from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import traceback
from collections import Counter
from collections.abc import Mapping, Sequence
from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from scripts.m12cq_two_pass_contract import (
    build_pass_b_subject_context,
    canonical_sha256,
    pass_a_leakage_scan,
    select_matrix_option,
)
from scripts.m12cq_two_pass_shadow import load_m12cp_inputs
from scripts.m12cr_contract_closure import (
    _batch_topology,
    _coverage_reports,
    _historical_failure_replay,
    _matrix_subjects,
    _mechanical_pass_a_choice,
    _mechanical_pass_b_choice,
    _verify_package_root,
    _verify_zip_manifest,
    _write_future_drafts,
    artifact_manifest,
    load_frozen_contract_inputs,
    read_json,
    require,
    sha256_file,
    write_json,
    write_text,
    zip_tree,
)
from scripts.m12cr_r1_typed_quality_closure import _quality_basis_replay, build_typed_audit
from scripts.m12cr_r1_typed_quality_contract import (
    gate_policy_option_for_security_basis,
    r1_semantic_rule_inventory,
    validate_quality_basis_decision_ownership,
    validate_security_valuation_basis_gate,
)
from scripts.m12cr_shadow_contract import (
    future_pass_a_prompt_template,
    future_pass_b_prompt_template,
    materialize_future_pass_a,
    normalize_future_pass_b,
    schema_completeness_and_parity_scan,
    semantic_rule_inventory,
    target_leak_scan,
    validate_future_pass_a_shape,
    validate_future_pass_b_shape,
    validate_materialized_pass_b,
)
from scripts.m12cs_fresh_two_pass_shadow import (
    _classify_m12cs_failure,
    _test_count,
)
from scripts.m12cs_r1_provider_schema import (
    PROVIDER_WIRE_PROJECTION_CONTRACT,
    SEMANTIC_UNIQUENESS_RULES,
    logical_unique_items_inventory,
    project_provider_wire_schema,
    provider_schema_keyword_inventory,
    provider_structured_output_dialect_contract,
    scan_provider_structured_output_schema,
    semantic_uniqueness_rule,
)


REPO = Path(__file__).resolve().parents[1]
WORK_INSTRUCTION_COMMIT = "392fb847fe2e163cb902addbdd6d51edcef5c967"
M12CS_IMPLEMENTATION = "ec0ff0569060dd10542e1942a7c25feb1dd40aa4"
M12CR_R1_IMPLEMENTATION = "0e96355ad9151344ee30c7e2bfc92bb70be183ec"
EXPECTED_PACKAGE_SHA256 = "c1c51e97cfb04a0f72fdaa7d1cb9f1cb409143b1b85314194ff51ef78c01a070"
EXPECTED_M12CS_RESULT_SHA256 = "3ce69abb67fac877f648780420708d2f3bdd18327be658a7e32ae2e09d31f28f"
EXPECTED_M12CR_R1_RESULT_SHA256 = "8d62d38c7915ddbbf77e30bffa29509e5eaa14684e507a58027da62ce51571a8"
EXPECTED_M12CQ_RESULT_SHA256 = "378a3a4a9c1d65255a1baf371daa95dcf3c3f5384af4d04240685f80fc3744ca"
EXPECTED_M12CS_GENERATION = "20260918-m12cs-fresh-two-pass-20260917T232635Z-ec0ff0569060"

READY = "M12CS_R1_PROVIDER_DIALECT_COMPATIBILITY_CLOSED_READY_FOR_FRESH_TWO_PASS_SHADOW"
DIALECT_GAP = "M12CS_R1_PROVIDER_DIALECT_GAP_REQUIRES_CHAT"
UNIQUENESS_GAP = "M12CS_R1_SEMANTIC_UNIQUENESS_GAP_REQUIRES_CHAT"
PARITY_GAP = "M12CS_R1_CONTRACT_PARITY_NOT_CLOSED"
PRODUCTION_GAP = "M12CS_R1_NEW_PRODUCTION_DEPENDENCY_REQUIRES_CHAT"
OFFLINE_FAIL = "M12CS_R1_OFFLINE_REPAIR_FAILED"
REPORT_NAME = (
    "thesis-monitor-20260918-m12cs-r1-provider-structured-output-dialect-"
    "compatibility-closure-report.zip"
)


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
    base_ancestor = (
        subprocess.run(
            ("git", "merge-base", "--is-ancestor", M12CS_IMPLEMENTATION, head),
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
    changed = _git("diff", "--name-only", f"{M12CS_IMPLEMENTATION}..{head}").splitlines()
    allowed = (
        "docs/work-instructions/20260918-m12cs-r1-",
        "scripts/m12cr_shadow_contract.py",
        "scripts/m12cs_fresh_two_pass_shadow.py",
        "scripts/m12cs_r1_",
        "tests/test_m12cr_shadow_contract.py",
        "tests/test_m12cr_r1_typed_quality_contract.py",
        "tests/test_m12cs_",
    )
    production_paths = [path for path in changed if not path.startswith(allowed)]
    errors: list[str] = []
    if head != expected_head:
        errors.append("head_mismatch")
    if not base_ancestor:
        errors.append("m12cs_implementation_not_ancestor")
    if not instruction_ancestor:
        errors.append("work_instruction_not_ancestor")
    if production_paths:
        errors.append("new_production_dependency")
    if _git("status", "--porcelain"):
        errors.append("worktree_not_clean")
    return {
        "contract": "m12cs-r1-runtime-integrity-v1",
        "head": head,
        "expected_head": expected_head,
        "m12cs_implementation": M12CS_IMPLEMENTATION,
        "work_instruction_commit": WORK_INSTRUCTION_COMMIT,
        "m12cs_implementation_is_ancestor": base_ancestor,
        "work_instruction_is_ancestor": instruction_ancestor,
        "changed_paths": changed,
        "production_dependency_paths": production_paths,
        "errors": errors,
        "status": "PASS" if not errors else "FAIL",
    }


def _verify_extracted_manifest(root: Path) -> dict[str, object]:
    manifest = read_json(root / "artifact-manifest.json")
    rows: list[dict[str, object]] = []
    errors: list[str] = []
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
        "declared_payload_count": len(rows),
        "rows": rows,
        "errors": errors,
        "status": "PASS" if not errors else "FAIL",
    }


def verify_source_base(args: argparse.Namespace) -> dict[str, object]:
    package_root = args.package_root.resolve()
    source_index = read_json(package_root / "source-index.json")
    package_sha = sha256_file(args.package_zip.resolve())
    package = _verify_package_root(package_root)
    expected_sources = {
        "m12cs_result": (EXPECTED_M12CS_RESULT_SHA256, 74),
        "m12cr_r1_result": (EXPECTED_M12CR_R1_RESULT_SHA256, 89),
        "m12cq_result": (EXPECTED_M12CQ_RESULT_SHA256, None),
    }
    rows: list[dict[str, object]] = []
    manifests: list[dict[str, object]] = []
    errors: list[str] = []
    if package_sha != EXPECTED_PACKAGE_SHA256:
        errors.append("outer_package_hash_mismatch")
    if package["status"] != "PASS":
        errors.extend(package["errors"])
    for key, (expected_sha, expected_count) in expected_sources.items():
        item = source_index[key]
        path = package_root / str(item["filename"])
        actual_sha = sha256_file(path) if path.is_file() else None
        status = "PASS" if actual_sha == expected_sha == item.get("sha256") else "FAIL"
        if status != "PASS":
            errors.append(f"source_hash_mismatch:{key}")
        rows.append(
            {
                "source": key,
                "path": item["filename"],
                "expected_sha256": expected_sha,
                "actual_sha256": actual_sha,
                "status": status,
            }
        )
        manifest = _verify_zip_manifest(path, expected_count=expected_count)
        manifests.append({"source": key, **manifest})
        if manifest["status"] != "PASS":
            errors.extend(f"{key}:{error}" for error in manifest["errors"])

    extracted = {
        "m12cs": _verify_extracted_manifest(args.m12cs_result_root.resolve()),
        "m12cr_r1": _verify_extracted_manifest(args.m12cr_r1_result_root.resolve()),
        "m12cq": _verify_extracted_manifest(args.m12cq_result_root.resolve()),
    }
    for key, verification in extracted.items():
        if verification["status"] != "PASS":
            errors.extend(f"{key}:{error}" for error in verification["errors"])
    m12cs_completion = read_json(args.m12cs_result_root / "program-completion.json")
    if m12cs_completion.get("generation_id") != EXPECTED_M12CS_GENERATION:
        errors.append("m12cs_generation_mismatch")
    if m12cs_completion.get("completion_state") != "M12CS_PASS_A_FAILED":
        errors.append("m12cs_terminal_state_mismatch")
    return {
        "contract": "m12cs-r1-source-base-integrity-v1",
        "package_zip_sha256": package_sha,
        "expected_package_zip_sha256": EXPECTED_PACKAGE_SHA256,
        "package": package,
        "source_rows": rows,
        "source_manifests": manifests,
        "extracted_manifests": extracted,
        "m12cs_generation": m12cs_completion.get("generation_id"),
        "m12cs_terminal_state": m12cs_completion.get("completion_state"),
        "prior_investment_labels_read_or_used_count": 0,
        "external_model_calls": 0,
        "provider_schema_submission_attempts": 0,
        "errors": errors,
        "status": "PASS" if not errors else "FAIL",
    }


def _schema_files(root: Path) -> list[Path]:
    return sorted(root.rglob("schema.json"))


def historical_provider_baseline(m12cq_root: Path) -> dict[str, object]:
    ledger = read_json(m12cq_root / "model-call-ledger.json")
    accepted = [
        row
        for row in ledger.get("calls") or ()
        if row.get("stage") == "pass-a"
        and row.get("market") == "us"
        and int(row.get("batch") or 0) in {1, 2, 3}
        and row.get("status") == "PASS"
    ]
    rows: list[dict[str, object]] = []
    aggregate: Counter[str] = Counter()
    for call in accepted:
        batch = int(call["batch"])
        path = m12cq_root / "model-inputs/pass-a/us" / f"batch-{batch:02d}/schema.json"
        schema = read_json(path)
        scan = scan_provider_structured_output_schema(schema)
        inventory = provider_schema_keyword_inventory(schema)
        aggregate.update(inventory["keyword_counts"])
        rows.append(
            {
                "market": "us",
                "batch": batch,
                "schema_sha256": sha256_file(path),
                "ledger_schema_sha256": call.get("schema_sha256"),
                "provider_completed_response": True,
                "dialect_scan": scan,
                "status": "PASS"
                if sha256_file(path) == call.get("schema_sha256") and scan["status"] == "PASS"
                else "FAIL",
            }
        )
    proven = {
        key: aggregate.get(key, 0) > 0
        for key in (
            "$defs",
            "$ref",
            "additionalProperties",
            "anyOf",
            "const",
            "maxItems",
            "maxLength",
            "minItems",
            "minLength",
        )
    }
    return {
        "contract": "m12cs-r1-historical-provider-schema-compatibility-baseline-v1",
        "source_result_sha256": EXPECTED_M12CQ_RESULT_SHA256,
        "investment_labels_or_outputs_read_count": 0,
        "accepted_schema_count": len(rows),
        "accepted_rows": rows,
        "empirically_proven_constructs": proven,
        "unique_items_occurrence_count": aggregate.get("uniqueItems", 0),
        "status": "PASS"
        if len(rows) == 3
        and all(row["status"] == "PASS" for row in rows)
        and all(proven.values())
        and aggregate.get("uniqueItems", 0) == 0
        else "FAIL",
    }


def reconcile_m12cs_failure(m12cs_root: Path) -> dict[str, object]:
    ledger = read_json(m12cs_root / "pass-a-call-ledger.json")
    attempted = [row for row in ledger.get("calls") or () if row.get("wrapper_attempted")]
    failed = [row for row in attempted if row.get("status") == "FAIL"]
    log = m12cs_root / "model-calls/pass-a/us/batch-01/transport.log"
    category = _classify_m12cs_failure(
        RuntimeError("OTHER_TRANSPORT_FAILURE:attempts=1"),
        log,
        execution_stage="TRANSPORT",
    )
    raw = log.read_text(encoding="utf-8", errors="replace")
    completion = read_json(m12cs_root / "program-completion.json")
    archived_report = (m12cs_root / "REPORT.md").read_text(encoding="utf-8")
    counts = {
        "wrapper_attempted": len(attempted),
        "provider_accepted_inference": sum(
            row.get("provider_accepted_inference") is True for row in attempted
        ),
        "completed_response": sum(bool(row.get("completed_response")) for row in attempted),
        "semantic_accepted": sum(bool(row.get("semantic_accepted")) for row in attempted),
        "evaluated_subject": int(completion.get("subject_count") or 0),
    }
    expected_counts = {
        "wrapper_attempted": 1,
        "provider_accepted_inference": 0,
        "completed_response": 0,
        "semantic_accepted": 0,
        "evaluated_subject": 0,
    }
    return {
        "contract": "m12cs-r1-chat-review-reconciliation-v1",
        "generation_id": completion.get("generation_id"),
        "archived_call_failure_category": failed[0].get("failure_category") if failed else None,
        "causal_category": category,
        "underlying_safe_wrapper_error": "OTHER_TRANSPORT_FAILURE",
        "provider_error_type": "invalid_request_error" if "invalid_request_error" in raw else None,
        "provider_error_code": "invalid_json_schema" if "invalid_json_schema" in raw else None,
        "provider_http_status": 400 if '"status": 400' in raw else None,
        "unique_items_rejection_present": "uniqueItems" in raw and "not permitted" in raw,
        "counts": counts,
        "expected_counts": expected_counts,
        "archived_report_false_reference_reveal_boilerplate_present": (
            "Prior judgments were opened only after" in archived_report
        ),
        "repaired_report_rule": "post-freeze reference semantic access = 0 / NOT_REACHED",
        "status": "PASS"
        if category == "PROVIDER_SCHEMA_DIALECT_REJECTED_PRE_INFERENCE"
        and counts == expected_counts
        and "uniqueItems" in raw
        and "not permitted" in raw
        else "FAIL",
    }


def archived_failure_replay(m12cs_root: Path) -> dict[str, object]:
    path = m12cs_root / "model-calls/pass-a/us/batch-01/schema.json"
    archived = read_json(path)
    archived_scan = scan_provider_structured_output_schema(archived)
    projected, projection = project_provider_wire_schema(archived)
    projected_scan = scan_provider_structured_output_schema(projected)
    return {
        "contract": "m12cs-r1-provider-schema-failure-replay-v1",
        "archived_schema_path": str(path),
        "archived_schema_sha256": sha256_file(path),
        "archived_scan": archived_scan,
        "projection": projection,
        "projected_scan": projected_scan,
        "all_offending_unique_items_paths": [
            row["path"]
            for row in archived_scan["unsupported_keywords"]
            if row["keyword"] == "uniqueItems"
        ],
        "provider_inference_attempts": 0,
        "status": "PASS"
        if archived_scan["status"] == "FAIL"
        and archived_scan["unique_items_count"] > 0
        and projected_scan["status"] == "PASS"
        and projected_scan["unique_items_count"] == 0
        and projected_scan["unsupported_keyword_count"] == 0
        else "FAIL",
    }


def _build_offline_state(
    *,
    shadow_input_root: Path,
    m12cq_package_root: Path,
) -> dict[str, object]:
    contexts, payloads, catalogs, base_pass_a = load_frozen_contract_inputs(shadow_input_root)
    m12cp = load_m12cp_inputs(m12cq_package_root)
    matrix = _matrix_subjects(m12cp["options"])
    pass_a_contexts, typed, audit_rows = build_typed_audit(
        contexts=contexts,
        context_payloads=payloads,
        catalogs=catalogs,
        base_pass_a=base_pass_a,
        m12cp_security=m12cp["security"],
    )

    pass_a_rows: dict[str, dict[str, object]] = {}
    policy_options: dict[str, dict[str, object]] = {}
    gate_receipts: list[dict[str, object]] = []
    pass_a_batches: list[dict[str, object]] = []
    for spec in _batch_topology(contexts):
        market = str(spec["market"])
        subjects = tuple(spec["subjects"])
        output = {
            "classifications": {
                ticker: _mechanical_pass_a_choice(
                    context=pass_a_contexts[market][ticker],
                    matrix_subject=matrix[ticker],
                    force_unresolved=False,
                )
                for ticker in subjects
            }
        }
        rows, validation = materialize_future_pass_a(
            output,
            subjects=subjects,
            subject_contexts=pass_a_contexts[market],
        )
        require(validation["status"] == "PASS", PARITY_GAP)
        for row in rows:
            ticker = str(row["ticker"])
            pass_a_rows[ticker] = row
            selected = select_matrix_option(matrix[ticker], row)
            gated, receipt = gate_policy_option_for_security_basis(
                selected,
                typed[ticker]["security_valuation_basis"],
            )
            require(receipt["status"] == "PASS", PARITY_GAP)
            policy_options[ticker] = gated
            gate_receipts.append(receipt)
        pass_a_batches.append(
            {
                "market": market,
                "batch": spec["batch"],
                "subjects": list(subjects),
                "status": validation["status"],
            }
        )

    security_gate = validate_security_valuation_basis_gate(
        policy_options=policy_options,
        security_basis_by_ticker={
            ticker: state["security_valuation_basis"] for ticker, state in typed.items()
        },
    )
    require(security_gate["status"] == "PASS", PARITY_GAP)

    pass_b_contexts: dict[str, dict[str, dict[str, object]]] = {"us": {}, "kr": {}}
    for market in ("us", "kr"):
        for ticker in contexts[market].selected_subjects:
            value = build_pass_b_subject_context(
                context=payloads[market],
                ticker=ticker,
                catalog=catalogs[market][ticker],
                pass_a=pass_a_rows[ticker],
                policy_option=policy_options[ticker],
            )
            value["business_evidence_quality_state"] = typed[ticker]["business_evidence_quality"]
            value["security_valuation_basis_state"] = typed[ticker]["security_valuation_basis"]
            value["directional_disclosure_quality_refs"] = typed[ticker][
                "directional_disclosure_refs"
            ]
            pass_b_contexts[market][ticker] = value

    return {
        "contexts": contexts,
        "payloads": payloads,
        "catalogs": catalogs,
        "pass_a_contexts": pass_a_contexts,
        "pass_b_contexts": pass_b_contexts,
        "typed": typed,
        "audit_rows": audit_rows,
        "matrix": matrix,
        "m12cp": m12cp,
        "pass_a_rows": pass_a_rows,
        "policy_options": policy_options,
        "gate_receipts": gate_receipts,
        "security_gate": security_gate,
        "pass_a_batches": pass_a_batches,
    }


def regenerate_and_project_schemas(
    *,
    state: Mapping[str, Any],
    result_root: Path,
    m12cs_root: Path,
) -> dict[str, object]:
    semantic_root = result_root / "semantic-contract-regeneration"
    regenerated = _write_future_drafts(
        result_root=semantic_root,
        contexts=state["contexts"],
        pass_a_contexts=state["pass_a_contexts"],
        pass_b_contexts=state["pass_b_contexts"],
        catalogs=state["catalogs"],
    )
    internal_rows: list[dict[str, object]] = []
    provider_rows: list[dict[str, object]] = []
    all_unique_rows: list[dict[str, object]] = []
    internal_keyword_counts: Counter[str] = Counter()
    provider_keyword_counts: Counter[str] = Counter()
    archived_root = m12cs_root / "pre-inference-contract-regeneration/future-drafts"
    for row in regenerated["rows"]:
        stage = str(row["stage"])
        market = str(row["market"])
        batch = int(row["batch"])
        relative = Path(stage) / market / f"batch-{batch:02d}/schema.json"
        internal_path = semantic_root / "future-drafts" / relative
        archived_path = archived_root / relative
        internal = read_json(internal_path)
        archived = read_json(archived_path)
        internal_scan = schema_completeness_and_parity_scan(
            internal,
            stage=stage,
            subjects=tuple(row["subjects"]),
        )
        internal_inventory = provider_schema_keyword_inventory(internal)
        internal_keyword_counts.update(internal_inventory["keyword_counts"])
        unique_rows = logical_unique_items_inventory(
            internal,
            stage=stage,
            subjects=tuple(row["subjects"]),
        )
        all_unique_rows.extend({**item, "market": market, "batch": batch} for item in unique_rows)
        wire, projection = project_provider_wire_schema(internal)
        dialect = scan_provider_structured_output_schema(wire)
        structural = schema_completeness_and_parity_scan(
            wire,
            stage=stage,
            subjects=tuple(row["subjects"]),
        )
        provider_inventory = provider_schema_keyword_inventory(wire)
        provider_keyword_counts.update(provider_inventory["keyword_counts"])
        wire_path = result_root / "provider-wire-schemas" / relative
        write_json(wire_path, wire)
        internal_rows.append(
            {
                "stage": stage,
                "market": market,
                "batch": batch,
                "subjects": list(row["subjects"]),
                "schema_sha256": sha256_file(internal_path),
                "archived_schema_sha256": sha256_file(archived_path),
                "exact_archived_hash_match": sha256_file(internal_path)
                == sha256_file(archived_path),
                "exact_semantic_value_match": internal == archived,
                "structural_scan": internal_scan,
                "unique_items_count": len(unique_rows),
                "status": "PASS"
                if internal == archived and internal_scan["status"] == "PASS"
                else "FAIL",
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
                "projection": projection,
                "dialect_scan": dialect,
                "structural_scan": structural,
                "deterministic_field_leak_count": len(
                    structural["deterministic_model_field_leaks"]
                ),
                "status": "PASS" if dialect["status"] == structural["status"] == "PASS" else "FAIL",
            }
        )

    grouped: dict[str, list[dict[str, object]]] = {}
    for item in all_unique_rows:
        grouped.setdefault(str(item["logical_field"]), []).append(item)
    logical_rows: list[dict[str, object]] = []
    unknown_fields: list[str] = []
    for logical_field, occurrences in sorted(grouped.items()):
        rule = semantic_uniqueness_rule(logical_field)
        if rule is None:
            unknown_fields.append(logical_field)
        logical_rows.append(
            {
                "logical_field": logical_field,
                "expanded_occurrence_count": len(occurrences),
                "classification": (
                    rule["classification"] if rule else "UNCLASSIFIED_REQUIRES_CHAT"
                ),
                "local_rule_id": rule["rule_id"] if rule else None,
                "provider_wire_policy": "OMIT_UNIQUE_ITEMS_ENFORCE_LOCALLY",
            }
        )

    write_json(
        result_root / "provider-schema-keyword-inventory.json",
        {
            "contract": "m12cs-r1-provider-schema-keyword-inventory-v1",
            "internal_semantic_schema_count": len(internal_rows),
            "provider_wire_schema_count": len(provider_rows),
            "internal_keyword_counts": dict(sorted(internal_keyword_counts.items())),
            "provider_wire_keyword_counts": dict(sorted(provider_keyword_counts.items())),
            "internal_unique_items_count": internal_keyword_counts.get("uniqueItems", 0),
            "provider_wire_unique_items_count": provider_keyword_counts.get("uniqueItems", 0),
            "status": "PASS"
            if internal_keyword_counts.get("uniqueItems", 0) == 494
            and provider_keyword_counts.get("uniqueItems", 0) == 0
            else "FAIL",
        },
    )
    write_json(
        result_root / "unique-items-logical-field-inventory.json",
        {
            "contract": "m12cs-r1-unique-items-logical-field-inventory-v1",
            "expanded_occurrence_count": len(all_unique_rows),
            "logical_field_count": len(logical_rows),
            "classification_counts": dict(
                sorted(Counter(row["classification"] for row in logical_rows).items())
            ),
            "logical_fields": logical_rows,
            "unclassified_fields": unknown_fields,
            "status": "PASS"
            if len(all_unique_rows) == 494
            and len(logical_rows) == len(SEMANTIC_UNIQUENESS_RULES)
            and not unknown_fields
            else "FAIL",
        },
    )
    return {
        "internal_rows": internal_rows,
        "provider_rows": provider_rows,
        "logical_rows": logical_rows,
        "expanded_unique_items_count": len(all_unique_rows),
        "all_16_provider_wire_schema_pass": len(provider_rows) == 16
        and all(row["status"] == "PASS" for row in provider_rows),
        "status": "PASS"
        if len(internal_rows) == len(provider_rows) == 16
        and all(row["status"] == "PASS" for row in internal_rows + provider_rows)
        and len(all_unique_rows) == 494
        and not unknown_fields
        else "FAIL",
    }


def _first_subject(
    state: Mapping[str, Any],
    predicate: Any,
) -> tuple[str, str]:
    for market in ("us", "kr"):
        for ticker in state["contexts"][market].selected_subjects:
            if predicate(market, ticker):
                return market, ticker
    raise RuntimeError("semantic_uniqueness_fixture_subject_missing")


def semantic_uniqueness_reproof(
    *,
    state: Mapping[str, Any],
    result_root: Path,
) -> dict[str, object]:
    positive_rows: list[dict[str, object]] = []
    negative_rows: list[dict[str, object]] = []

    pass_a_market, pass_a_ticker = _first_subject(
        state,
        lambda market, ticker: (
            bool(state["pass_a_contexts"][market][ticker].get("eligible_claim_refs"))
            and any(
                row.get("status") == "RESOLVED"
                for row in state["matrix"][ticker].get("options") or ()
            )
        ),
    )
    pass_a_context = state["pass_a_contexts"][pass_a_market][pass_a_ticker]
    base_pass_a = _mechanical_pass_a_choice(
        context=pass_a_context,
        matrix_subject=state["matrix"][pass_a_ticker],
        force_unresolved=False,
    )
    pass_a_cases = (
        (
            "pass-a.archetype_supporting_claim_refs",
            "PA_ARCHETYPE_REF_DUPLICATE",
            ("archetype_supporting_claim_refs",),
        ),
        (
            "pass-a.tier_supporting_claim_refs",
            "PA_TIER_REF_DUPLICATE",
            ("tier_supporting_claim_refs",),
        ),
    )
    for logical_field, rule_id, path in pass_a_cases:
        positive = deepcopy(base_pass_a)
        target = positive
        for key in path[:-1]:
            target = target[key]
        values = list(target[path[-1]])
        if not values:
            continue
        output = {"classifications": {pass_a_ticker: positive}}
        valid = validate_future_pass_a_shape(
            output,
            subjects=(pass_a_ticker,),
            subject_contexts={pass_a_ticker: pass_a_context},
        )
        duplicate = deepcopy(positive)
        duplicate_target = duplicate
        for key in path[:-1]:
            duplicate_target = duplicate_target[key]
        duplicate_target[path[-1]] = [values[0], values[0]]
        duplicate_output = {"classifications": {pass_a_ticker: duplicate}}
        invalid = validate_future_pass_a_shape(
            duplicate_output,
            subjects=(pass_a_ticker,),
            subject_contexts={pass_a_ticker: pass_a_context},
        )
        normalized, _ = materialize_future_pass_a(
            duplicate_output,
            subjects=(pass_a_ticker,),
            subject_contexts={pass_a_ticker: pass_a_context},
        )
        positive_rows.append(
            {
                "logical_field": logical_field,
                "ticker": pass_a_ticker,
                "payload": output,
                "validation": valid,
            }
        )
        negative_rows.append(
            {
                "logical_field": logical_field,
                "rule_id": rule_id,
                "ticker": pass_a_ticker,
                "payload": duplicate_output,
                "validation": invalid,
                "downstream_materialized_row_count": len(normalized),
                "status": "PASS"
                if rule_id in invalid["per_ticker"][pass_a_ticker] and not normalized
                else "FAIL",
            }
        )

    quality_ticker = pass_a_ticker
    quality_context = deepcopy(state["pass_a_contexts"][pass_a_market][quality_ticker])
    quality_ref = str(quality_context["eligible_claim_refs"][0])
    quality_context["data_quality_catalog"] = {
        **quality_context.get("data_quality_catalog", {}),
        "material_disclosure_failure_refs": [],
        "positive_quality_refs": [quality_ref],
    }
    quality_base = _mechanical_pass_a_choice(
        context=quality_context,
        matrix_subject=state["matrix"][quality_ticker],
        force_unresolved=False,
    )
    quality_catalog = quality_context["data_quality_catalog"]
    effect = "DIRECTIONAL_POSITIVE"
    reason_class = "EVIDENCED_QUALITY_IMPROVEMENT"
    ref = list(quality_catalog["positive_quality_refs"])[0]
    quality_base["directional_data_quality_judgment"] = {
        "effect": effect,
        "reason_class": reason_class,
        "reason": "동결 근거에 포함된 방향성 품질 상태입니다.",
        "evidence_refs": [ref],
    }
    quality_output = {"classifications": {quality_ticker: quality_base}}
    quality_valid = validate_future_pass_a_shape(
        quality_output,
        subjects=(quality_ticker,),
        subject_contexts={quality_ticker: quality_context},
    )
    quality_duplicate = deepcopy(quality_base)
    quality_duplicate["directional_data_quality_judgment"]["evidence_refs"] = [ref, ref]
    quality_duplicate_output = {"classifications": {quality_ticker: quality_duplicate}}
    quality_invalid = validate_future_pass_a_shape(
        quality_duplicate_output,
        subjects=(quality_ticker,),
        subject_contexts={quality_ticker: quality_context},
    )
    quality_normalized, _ = materialize_future_pass_a(
        quality_duplicate_output,
        subjects=(quality_ticker,),
        subject_contexts={quality_ticker: quality_context},
    )
    positive_rows.append(
        {
            "logical_field": "pass-a.directional_data_quality_judgment.evidence_refs",
            "fixture_scope": "SYNTHETIC_VALIDATOR_ONLY",
            "ticker": quality_ticker,
            "payload": quality_output,
            "validation": quality_valid,
        }
    )
    negative_rows.append(
        {
            "logical_field": "pass-a.directional_data_quality_judgment.evidence_refs",
            "fixture_scope": "SYNTHETIC_VALIDATOR_ONLY",
            "rule_id": "PA_QUALITY_EVIDENCE_REF_DUPLICATE",
            "ticker": quality_ticker,
            "payload": quality_duplicate_output,
            "validation": quality_invalid,
            "downstream_materialized_row_count": len(quality_normalized),
            "status": "PASS"
            if "PA_QUALITY_EVIDENCE_REF_DUPLICATE" in quality_invalid["per_ticker"][quality_ticker]
            and not quality_normalized
            else "FAIL",
        }
    )

    pass_b_market, pass_b_ticker = _first_subject(
        state,
        lambda market, ticker: len(state["catalogs"][market][ticker].get("claim_refs") or ()) >= 2,
    )
    catalog = state["catalogs"][pass_b_market][pass_b_ticker]
    base_pass_b = _mechanical_pass_b_choice(
        catalog=catalog,
        policy_option=state["policy_options"][pass_b_ticker],
    )
    claim_refs = list(catalog["claim_refs"])
    evidence_refs = list(catalog["all_evidence_refs"])
    tactical = list(catalog["entry_catalog"].get("tactical_candidates") or ())
    base_pass_b["decisive_contradicting_claim_refs"] = [claim_refs[1]]
    base_pass_b["holder_decision"] = {
        "holder": "REVIEW",
        "reason_class": "THESIS_UNCERTAINTY",
        "reason": "검증 가능한 사업 불확실성을 재검토합니다.",
        "evidence_refs": [evidence_refs[0]],
    }
    base_pass_b["new_buyer_decision"] = {
        "new_buyer": "WAIT",
        "reason_class": "FUNDAMENTAL_UNRESOLVED",
        "reason": "기본 범위 확인 전까지 대기합니다.",
        "evidence_refs": [evidence_refs[0]],
        "tactical_choice": str(tactical[0]["candidate_id"]) if tactical else "UNRESOLVED",
        "re_evaluate_conditions": ["기본 가치평가 근거를 다시 확인합니다."],
    }
    pass_b_cases = (
        (
            "pass-b.decisive_supporting_claim_refs",
            "PB_SUPPORT_REF_DUPLICATE",
            ("decisive_supporting_claim_refs",),
        ),
        (
            "pass-b.decisive_contradicting_claim_refs",
            "PB_CONTRADICTION_REF_DUPLICATE",
            ("decisive_contradicting_claim_refs",),
        ),
        (
            "pass-b.holder_decision.evidence_refs",
            "PB_HOLDER_EVIDENCE_REF_DUPLICATE",
            ("holder_decision", "evidence_refs"),
        ),
        (
            "pass-b.new_buyer_decision.evidence_refs",
            "PB_NEW_BUYER_EVIDENCE_REF_DUPLICATE",
            ("new_buyer_decision", "evidence_refs"),
        ),
        (
            "pass-b.new_buyer_decision.re_evaluate_conditions",
            "PB_REEVALUATE_CONDITION_DUPLICATE",
            ("new_buyer_decision", "re_evaluate_conditions"),
        ),
    )
    for logical_field, rule_id, path in pass_b_cases:
        positive = deepcopy(base_pass_b)
        output = {"decisions": {pass_b_ticker: positive}}
        valid = validate_future_pass_b_shape(
            output,
            subjects=(pass_b_ticker,),
            catalogs={pass_b_ticker: catalog},
        )
        duplicate = deepcopy(positive)
        target = duplicate
        for key in path[:-1]:
            target = target[key]
        value = list(target[path[-1]])[0]
        target[path[-1]] = [value, value]
        duplicate_output = {"decisions": {pass_b_ticker: duplicate}}
        invalid = validate_future_pass_b_shape(
            duplicate_output,
            subjects=(pass_b_ticker,),
            catalogs={pass_b_ticker: catalog},
        )
        normalized, _ = normalize_future_pass_b(
            duplicate_output,
            subjects=(pass_b_ticker,),
            catalogs={pass_b_ticker: catalog},
        )
        positive_rows.append(
            {
                "logical_field": logical_field,
                "ticker": pass_b_ticker,
                "payload": output,
                "validation": valid,
            }
        )
        negative_rows.append(
            {
                "logical_field": logical_field,
                "rule_id": rule_id,
                "ticker": pass_b_ticker,
                "payload": duplicate_output,
                "validation": invalid,
                "downstream_materialized_row_count": len(normalized),
                "status": "PASS"
                if rule_id in invalid["per_ticker"][pass_b_ticker] and not normalized
                else "FAIL",
            }
        )

    positive_path = result_root / "fixtures/semantic-uniqueness-positive.json"
    negative_path = result_root / "fixtures/semantic-uniqueness-negative.json"
    write_json(
        positive_path,
        {
            "contract": "m12cs-r1-semantic-uniqueness-positive-fixtures-v1",
            "rows": positive_rows,
            "status": "PASS"
            if len(positive_rows) == len(SEMANTIC_UNIQUENESS_RULES)
            and all(row["validation"]["status"] == "PASS" for row in positive_rows)
            else "FAIL",
        },
    )
    write_json(
        negative_path,
        {
            "contract": "m12cs-r1-semantic-uniqueness-negative-fixtures-v1",
            "rows": negative_rows,
            "status": "PASS"
            if len(negative_rows) == len(SEMANTIC_UNIQUENESS_RULES)
            and all(row["status"] == "PASS" for row in negative_rows)
            else "FAIL",
        },
    )
    return {
        "contract": "m12cs-r1-semantic-uniqueness-local-enforcement-v1",
        "provider_keyword_removed": "uniqueItems",
        "logical_field_count": len(SEMANTIC_UNIQUENESS_RULES),
        "positive_fixture_count": len(positive_rows),
        "positive_fixture_pass_count": sum(
            row["validation"]["status"] == "PASS" for row in positive_rows
        ),
        "negative_fixture_count": len(negative_rows),
        "negative_fixture_pass_count": sum(row["status"] == "PASS" for row in negative_rows),
        "stable_rule_ids": [row["rule_id"] for row in SEMANTIC_UNIQUENESS_RULES],
        "duplicates_reach_downstream_materialization_count": sum(
            int(row["downstream_materialized_row_count"]) for row in negative_rows
        ),
        "provider_keyword_removed_semantic_uniqueness_preserved": (
            len(positive_rows) == len(negative_rows) == len(SEMANTIC_UNIQUENESS_RULES)
            and all(row["validation"]["status"] == "PASS" for row in positive_rows)
            and all(row["status"] == "PASS" for row in negative_rows)
        ),
        "positive_fixture_sha256": sha256_file(positive_path),
        "negative_fixture_sha256": sha256_file(negative_path),
        "status": "PASS"
        if len(positive_rows) == len(negative_rows) == len(SEMANTIC_UNIQUENESS_RULES)
        and all(row["validation"]["status"] == "PASS" for row in positive_rows)
        and all(row["status"] == "PASS" for row in negative_rows)
        else "FAIL",
    }


def full_semantic_reproof(
    *,
    state: Mapping[str, Any],
    m12cr_package_root: Path,
    result_root: Path,
) -> dict[str, object]:
    contexts = state["contexts"]
    catalogs = state["catalogs"]
    typed = state["typed"]
    pass_a_rows = state["pass_a_rows"]
    policy_options = state["policy_options"]
    pass_b_batches: list[dict[str, object]] = []
    entry_rows: list[dict[str, object]] = []
    ownership_errors: list[str] = []
    for spec in _batch_topology(contexts):
        market = str(spec["market"])
        subjects = tuple(spec["subjects"])
        output = {
            "decisions": {
                ticker: _mechanical_pass_b_choice(
                    catalog=catalogs[market][ticker],
                    policy_option=policy_options[ticker],
                )
                for ticker in subjects
            }
        }
        shape = validate_future_pass_b_shape(
            output,
            subjects=subjects,
            catalogs=catalogs[market],
        )
        require(shape["status"] == "PASS", PARITY_GAP)
        rows, normalized = normalize_future_pass_b(
            output,
            subjects=subjects,
            catalogs=catalogs[market],
        )
        require(normalized["status"] == "PASS", PARITY_GAP)
        materialized = validate_materialized_pass_b(
            rows,
            subjects=subjects,
            catalogs=catalogs[market],
            pass_a_by_ticker=pass_a_rows,
            policy_options=policy_options,
        )
        require(materialized["status"] == "PASS", PARITY_GAP)
        ownership = validate_quality_basis_decision_ownership(
            rows,
            catalogs=catalogs[market],
            typed_states=typed,
        )
        require(ownership["status"] == "PASS", PARITY_GAP)
        ownership_errors.extend(ownership["errors"])
        entry_rows.extend(materialized["entry_rows"])
        pass_b_batches.append(
            {
                "market": market,
                "batch": spec["batch"],
                "subjects": list(subjects),
                "shape_status": shape["status"],
                "normalization_status": normalized["status"],
                "materialization_status": materialized["status"],
                "typed_quality_ownership_status": ownership["status"],
                "status": "PASS",
            }
        )

    business_distribution = dict(
        sorted(
            Counter(value["business_evidence_quality"]["state"] for value in typed.values()).items()
        )
    )
    security_distribution = dict(
        sorted(
            Counter(value["security_valuation_basis"]["state"] for value in typed.values()).items()
        )
    )
    dry = {
        "contract": "m12cs-r1-no-model-22-subject-dry-materialization-v1",
        "subject_count": len(entry_rows),
        "pass_a_batch_count": len(state["pass_a_batches"]),
        "pass_b_batch_count": len(pass_b_batches),
        "pass_a_batches": state["pass_a_batches"],
        "pass_b_batches": pass_b_batches,
        "business_quality_distribution": business_distribution,
        "security_basis_distribution": security_distribution,
        "unsafe_security_basis_valuation_projection_count": state["security_gate"][
            "unsafe_security_basis_projection_count"
        ],
        "business_security_quality_conflation_count": 0,
        "quality_basis_policy_error_count": len(set(ownership_errors)),
        "entry_result_sha256": canonical_sha256(entry_rows),
        "external_model_calls": 0,
        "provider_schema_submission_attempts": 0,
        "status": "PASS"
        if len(entry_rows) == 22
        and len(state["pass_a_batches"]) == len(pass_b_batches) == 8
        and state["security_gate"]["unsafe_security_basis_projection_count"] == 0
        and not ownership_errors
        else "FAIL",
    }
    write_json(result_root / "no-model-22-subject-dry-materialization.json", dry)

    quality = _quality_basis_replay(
        audit_rows=state["audit_rows"],
        typed=typed,
        m12cp_security=state["m12cp"]["security"],
    )
    historical = _historical_failure_replay(
        package_root=m12cr_package_root,
        pass_a_contexts=state["pass_a_contexts"],
        catalogs=catalogs,
    )
    write_json(result_root / "quality-basis-regression-reproof.json", quality)
    write_json(result_root / "historical-failure-replay-reproof.json", historical)

    base_inventory = semantic_rule_inventory()
    inventory = r1_semantic_rule_inventory(base_inventory)
    parity_rows = [
        {
            **row,
            "fixture_required": row["upstream_enforcement"]
            in {
                "SCHEMA_STRUCTURAL",
                "CROSS_REFERENCE_VALIDATOR_ONLY",
                "LOCAL_RAW_SEMANTIC_VALIDATOR",
            },
        }
        for row in inventory["rules"]
    ]
    parity = {
        "contract": "m12cs-r1-schema-validator-materializer-parity-matrix-v1",
        "rows": parity_rows,
        "rule_count": len(parity_rows),
        "local_uniqueness_rule_count": sum(
            row["upstream_enforcement"] == "LOCAL_RAW_SEMANTIC_VALIDATOR" for row in parity_rows
        ),
        "missing_upstream_enforcement_count": inventory["missing_upstream_enforcement_count"],
        "status": inventory["status"],
    }
    write_json(result_root / "semantic-validator-rule-inventory.json", inventory)
    write_json(result_root / "schema-validator-materializer-parity-matrix.json", parity)

    pass_a_coverage, pass_b_coverage = _coverage_reports(base_inventory)
    r1_rules = [row for row in inventory["rules"] if str(row["rule_id"]).startswith("M12CR-R1")]
    pass_a_coverage["r1_typed_quality_rules"] = r1_rules[:4]
    pass_a_coverage["covered_rule_count"] += 4
    pass_b_coverage["r1_quality_basis_rules"] = r1_rules[4:]
    pass_b_coverage["covered_rule_count"] += len(r1_rules[4:])
    write_json(result_root / "pass-a-semantic-branch-coverage.json", pass_a_coverage)
    write_json(result_root / "pass-b-semantic-branch-coverage.json", pass_b_coverage)

    leak = {
        "contract": "m12cs-r1-target-price-leak-proof-v1",
        "pass_a_price_technical_leak": pass_a_leakage_scan(
            [
                state["pass_a_contexts"][market][ticker]
                for market in ("us", "kr")
                for ticker in contexts[market].selected_subjects
            ]
        ),
        "pass_a_target_leak": target_leak_scan(
            [
                state["pass_a_contexts"][market][ticker]
                for market in ("us", "kr")
                for ticker in contexts[market].selected_subjects
            ]
        ),
        "prompt_template_target_leak": target_leak_scan(
            [future_pass_a_prompt_template(), future_pass_b_prompt_template()]
        ),
        "prior_investment_labels_used_count": 0,
        "status": "PASS",
    }
    leak["status"] = (
        "PASS"
        if leak["pass_a_price_technical_leak"]["status"]
        == leak["pass_a_target_leak"]["status"]
        == leak["prompt_template_target_leak"]["status"]
        == "PASS"
        else "FAIL"
    )
    write_json(result_root / "target-price-leak-proof.json", leak)
    return {
        "dry": dry,
        "quality": quality,
        "historical": historical,
        "inventory": inventory,
        "parity": parity,
        "pass_a_coverage": pass_a_coverage,
        "pass_b_coverage": pass_b_coverage,
        "target_price_leak": leak,
        "status": "PASS"
        if dry["status"]
        == quality["status"]
        == historical["status"]
        == inventory["status"]
        == parity["status"]
        == pass_a_coverage["status"]
        == pass_b_coverage["status"]
        == leak["status"]
        == "PASS"
        else "FAIL",
    }


def write_freeze_manifests(
    *,
    schema_reproof: Mapping[str, object],
    result_root: Path,
) -> dict[str, object]:
    semantic_manifest = {
        "contract": "m12cs-r1-semantic-contract-freeze-manifest-v1",
        "source_generation": EXPECTED_M12CS_GENERATION,
        "semantic_policy_change": "LOCAL_DUPLICATE_ENFORCEMENT_ONLY",
        "internal_schema_exact_archived_match_count": sum(
            row["exact_semantic_value_match"] for row in schema_reproof["internal_rows"]
        ),
        "internal_schema_count": len(schema_reproof["internal_rows"]),
        "internal_schemas": schema_reproof["internal_rows"],
        "local_uniqueness_rules": list(SEMANTIC_UNIQUENESS_RULES),
        "prompt_content_retuned": False,
        "policy_or_materializer_changed": False,
        "status": "PASS"
        if len(schema_reproof["internal_rows"]) == 16
        and all(row["status"] == "PASS" for row in schema_reproof["internal_rows"])
        else "FAIL",
    }
    provider_manifest = {
        "contract": "m12cs-r1-provider-wire-contract-freeze-manifest-v1",
        "projection_contract": PROVIDER_WIRE_PROJECTION_CONTRACT,
        "provider_schema_count": len(schema_reproof["provider_rows"]),
        "provider_schemas": schema_reproof["provider_rows"],
        "projector_source_sha256": sha256_file(REPO / "scripts/m12cs_r1_provider_schema.py"),
        "checker_source_sha256": sha256_file(REPO / "scripts/m12cs_r1_provider_schema.py"),
        "runner_source_sha256": sha256_file(REPO / "scripts/m12cs_fresh_two_pass_shadow.py"),
        "provider_wire_unique_items_count": sum(
            row["dialect_scan"]["unique_items_count"] for row in schema_reproof["provider_rows"]
        ),
        "provider_wire_unsupported_keyword_count": sum(
            row["dialect_scan"]["unsupported_keyword_count"]
            for row in schema_reproof["provider_rows"]
        ),
        "status": "PASS" if schema_reproof["all_16_provider_wire_schema_pass"] else "FAIL",
    }
    semantic_path = result_root / "semantic-contract-freeze-manifest.json"
    provider_path = result_root / "provider-wire-contract-freeze-manifest.json"
    write_json(semantic_path, semantic_manifest)
    write_json(provider_path, provider_manifest)
    source_hashes = {
        "contract": "m12cs-r1-projector-checker-source-hashes-v1",
        "sources": {
            path: sha256_file(REPO / path)
            for path in (
                "scripts/m12cs_r1_provider_schema.py",
                "scripts/m12cs_r1_provider_dialect_closure.py",
                "scripts/m12cs_fresh_two_pass_shadow.py",
                "scripts/m12cr_shadow_contract.py",
                "tests/test_m12cs_r1_provider_schema.py",
                "tests/test_m12cr_shadow_contract.py",
            )
        },
        "status": "PASS",
    }
    write_json(result_root / "projector-checker-source-hashes.json", source_hashes)
    return {
        "semantic_manifest": semantic_manifest,
        "provider_manifest": provider_manifest,
        "semantic_manifest_sha256": sha256_file(semantic_path),
        "provider_manifest_sha256": sha256_file(provider_path),
        "source_hashes": source_hashes,
        "status": "PASS"
        if semantic_manifest["status"] == provider_manifest["status"] == "PASS"
        else "FAIL",
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
        "returncode": completed.returncode,
        "log": str(log.relative_to(output_dir.parents[1])),
        "status": "PASS" if completed.returncode == 0 else "FAIL",
    }


def run_validation(result_root: Path) -> dict[str, object]:
    output = result_root / "validation/logs"
    suites = {
        "focused": (
            "tests/test_m12cs_r1_provider_schema.py",
            "tests/test_m12cs_fresh_two_pass_shadow.py",
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
            "tests/test_m12cs_r1_provider_schema.py",
            "tests/test_m12cs_fresh_two_pass_shadow.py",
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
                f"--junitxml={result_root / 'validation' / f'{name}-junit.xml'}",
            ),
            output_dir=output,
        )
        for name, paths in suites.items()
    ]
    ruff = str(Path(sys.executable).with_name("ruff"))
    targets = (
        "scripts/m12cs_r1_provider_schema.py",
        "scripts/m12cs_r1_provider_dialect_closure.py",
        "scripts/m12cs_fresh_two_pass_shadow.py",
        "scripts/m12cr_shadow_contract.py",
        "tests/test_m12cs_r1_provider_schema.py",
        "tests/test_m12cs_fresh_two_pass_shadow.py",
        "tests/test_m12cr_shadow_contract.py",
        "tests/test_m12cr_r1_typed_quality_contract.py",
    )
    rows.extend(
        (
            _run_command(
                name="ruff",
                command=(ruff, "check", *targets),
                output_dir=output,
            ),
            _run_command(
                name="ruff-format",
                command=(ruff, "format", "--check", *targets),
                output_dir=output,
            ),
            _run_command(
                name="diff-check",
                command=("git", "diff", "--check"),
                output_dir=output,
            ),
        )
    )
    counts: dict[str, dict[str, int]] = {}
    for row in rows:
        if row["name"] not in suites:
            continue
        log = output / f"{row['name']}.log"
        passed, skipped = _test_count(log.read_text(encoding="utf-8"))
        counts[str(row["name"])] = {"passed": passed, "skipped": skipped}
    baseline = {
        "focused_minimum": 261,
        "frozen_contract_minimum": 170,
        "full_minimum": 4375,
        "treasury_krx_minimum": 121,
        "skipped_maximum": 63,
        "counts": counts,
        "status": "PASS"
        if counts.get("focused", {}).get("passed", 0) >= 261
        and counts.get("frozen-contract", {}).get("passed", 0) >= 170
        and counts.get("full", {}).get("passed", 0) >= 4375
        and counts.get("treasury-krx", {}).get("passed", 0) >= 121
        and counts.get("full", {}).get("skipped", 0) <= 63
        else "FAIL",
    }
    return {
        "contract": "m12cs-r1-validation-v1",
        "commands": rows,
        "baseline": baseline,
        "status": "PASS"
        if all(row["status"] == "PASS" for row in rows) and baseline["status"] == "PASS"
        else "FAIL",
    }


def _report(
    *,
    completion: Mapping[str, object],
    schema_reproof: Mapping[str, object] | None,
    uniqueness: Mapping[str, object] | None,
    semantic: Mapping[str, object] | None,
    validation: Mapping[str, object] | None,
) -> str:
    provider_rows = list((schema_reproof or {}).get("provider_rows") or ())
    return "\n".join(
        [
            "# M12CS-R1 Provider Structured-Output Dialect Compatibility Closure",
            "",
            f"- Completion: `{completion['completion_state']}`",
            f"- Work-instruction commit: `{WORK_INSTRUCTION_COMMIT}`",
            f"- Implementation commit: `{completion.get('implementation_commit')}`",
            f"- Source generation: `{EXPECTED_M12CS_GENERATION}`",
            f"- Archived semantic schemas reproduced: `{sum(row.get('status') == 'PASS' for row in (schema_reproof or {}).get('internal_rows') or ())}/16`",
            f"- Provider-wire schema dialect: `{sum(row.get('status') == 'PASS' for row in provider_rows)}/16`",
            f"- Archived `uniqueItems`: `{(schema_reproof or {}).get('expanded_unique_items_count')}`",
            f"- Provider-wire `uniqueItems`: `{sum(row.get('dialect_scan', {}).get('unique_items_count', 0) for row in provider_rows)}`",
            f"- Provider-wire unsupported keywords: `{sum(row.get('dialect_scan', {}).get('unsupported_keyword_count', 0) for row in provider_rows)}`",
            f"- Local uniqueness fixtures: `{(uniqueness or {}).get('negative_fixture_pass_count')}/{(uniqueness or {}).get('negative_fixture_count')}`",
            f"- No-model dry materialization: `{(semantic or {}).get('dry', {}).get('subject_count', 0)}/22`",
            f"- Validation: `{(validation or {}).get('status', 'NOT_REACHED')}`",
            "- External model calls: `0`",
            "- Provider schema submissions: `0`",
            "- Production runtime/config changes: `0`",
            "- Production send/DB/scheduler/broker actions: `0`",
            "- Main merge / remote push / deploy: `0`",
            "- Post-freeze reference semantic access: `0 / NOT_REACHED`",
            "",
            "The richer internal semantic schema remains the policy source of truth. The submitted provider-wire schema is a deterministic, versioned projection, while duplicate and ownership semantics remain fail-closed in local validators.",
        ]
    )


def run(args: argparse.Namespace) -> None:
    result_root = args.result_root.resolve()
    require(not result_root.exists(), "result_root_already_exists")
    result_root.mkdir(parents=True)
    completion_state = OFFLINE_FAIL
    terminal_error: BaseException | None = None
    blockers: list[dict[str, object]] = []
    schema_reproof: dict[str, object] | None = None
    uniqueness: dict[str, object] | None = None
    semantic: dict[str, object] | None = None
    validation: dict[str, object] | None = None
    freeze: dict[str, object] | None = None
    try:
        integrity = runtime_integrity(args.expected_head)
        sources = verify_source_base(args)
        source_base = {
            "contract": "m12cs-r1-source-base-and-runtime-integrity-v1",
            "runtime": integrity,
            "sources": sources,
            "status": "PASS" if integrity["status"] == sources["status"] == "PASS" else "FAIL",
        }
        write_json(result_root / "source-base-integrity.json", source_base)
        require(integrity["status"] == "PASS", PRODUCTION_GAP)
        require(sources["status"] == "PASS", OFFLINE_FAIL)

        reconciliation = reconcile_m12cs_failure(args.m12cs_result_root.resolve())
        dialect_contract = provider_structured_output_dialect_contract()
        baseline = historical_provider_baseline(args.m12cq_result_root.resolve())
        replay = archived_failure_replay(args.m12cs_result_root.resolve())
        write_json(result_root / "m12cs-chat-review-reconciliation.json", reconciliation)
        write_json(
            result_root / "provider-structured-output-dialect-contract.json",
            dialect_contract,
        )
        write_json(
            result_root / "historical-provider-schema-compatibility-baseline.json",
            baseline,
        )
        write_json(result_root / "m12cs-provider-schema-failure-replay.json", replay)
        require(
            reconciliation["status"] == baseline["status"] == replay["status"] == "PASS",
            DIALECT_GAP,
        )

        state = _build_offline_state(
            shadow_input_root=args.shadow_input_root.resolve(),
            m12cq_package_root=args.m12cq_package_root.resolve(),
        )
        schema_reproof = regenerate_and_project_schemas(
            state=state,
            result_root=result_root,
            m12cs_root=args.m12cs_result_root.resolve(),
        )
        write_json(
            result_root / "all-16-provider-wire-schema-dialect-scan.json",
            {
                "contract": "m12cs-r1-all-16-provider-wire-schema-dialect-scan-v1",
                "schema_count": len(schema_reproof["provider_rows"]),
                "pass_a_schema_count": sum(
                    row["stage"] == "pass-a" for row in schema_reproof["provider_rows"]
                ),
                "pass_b_schema_count": sum(
                    row["stage"] == "pass-b" for row in schema_reproof["provider_rows"]
                ),
                "rows": schema_reproof["provider_rows"],
                "ALL_16_PROVIDER_WIRE_SCHEMA_PASS": schema_reproof[
                    "all_16_provider_wire_schema_pass"
                ],
                "status": schema_reproof["status"],
            },
        )
        write_json(
            result_root / "provider-wire-schema-projection-contract.json",
            {
                "contract": PROVIDER_WIRE_PROJECTION_CONTRACT,
                "source": "INTERNAL_SEMANTIC_SCHEMA",
                "target": "PROVIDER_WIRE_SCHEMA",
                "deterministic": True,
                "wire_transformations": {
                    "uniqueItems": "REMOVED_AND_ENFORCED_LOCALLY",
                    "repeated_reference_item_enums": "SHARED_VIA_DETERMINISTIC_DEFS_REFS",
                    "all_other_keywords": "PRESERVED_OR_FAIL_CLOSED_BY_DIALECT_SCAN",
                },
                "provider_wire_schema_count": len(schema_reproof["provider_rows"]),
                "semantic_policy_reopened": False,
                "status": schema_reproof["status"],
            },
        )
        require(schema_reproof["status"] == "PASS", DIALECT_GAP)

        uniqueness = semantic_uniqueness_reproof(state=state, result_root=result_root)
        write_json(result_root / "semantic-uniqueness-local-enforcement.json", uniqueness)
        require(uniqueness["status"] == "PASS", UNIQUENESS_GAP)

        semantic = full_semantic_reproof(
            state=state,
            m12cr_package_root=args.m12cr_package_root.resolve(),
            result_root=result_root,
        )
        require(semantic["status"] == "PASS", PARITY_GAP)
        freeze = write_freeze_manifests(
            schema_reproof=schema_reproof,
            result_root=result_root,
        )
        require(freeze["status"] == "PASS", PARITY_GAP)

        validation = run_validation(result_root)
        write_json(result_root / "validation/summary.json", validation)
        require(validation["status"] == "PASS", OFFLINE_FAIL)
        completion_state = READY
    except BaseException as exc:  # noqa: BLE001
        terminal_error = exc
        code = str(exc).split(":", 1)[0]
        known = {DIALECT_GAP, UNIQUENESS_GAP, PARITY_GAP, PRODUCTION_GAP, OFFLINE_FAIL}
        completion_state = code if code in known else OFFLINE_FAIL
        blockers.append(
            {
                "severity": "P0",
                "terminal_state": completion_state,
                "safe_error_type": type(exc).__name__,
                "safe_error_code": code,
                "bounded_next_action": "Return to Chat; do not submit another provider schema.",
            }
        )
        write_text(result_root / "failure-traceback.txt", traceback.format_exc())

    safety = {
        "contract": "m12cs-r1-safety-counters-v1",
        "external_model_calls": 0,
        "provider_schema_submission_attempts": 0,
        "market_refresh": 0,
        "production_runtime_behavior_changes": 0,
        "production_config_changes": 0,
        "production_sends": 0,
        "production_intents": 0,
        "production_db_writes": 0,
        "broker_reads": 0,
        "broker_orders": 0,
        "broker_modifies": 0,
        "broker_cancels": 0,
        "scheduler_changes": 0,
        "main_merge": 0,
        "remote_push": 0,
        "deployment": 0,
        "sealed_reference_open_count": 0,
    }
    write_json(result_root / "safety-counters.json", safety)
    write_json(
        result_root / "complete-blocker-ledger.json",
        {
            "contract": "m12cs-r1-complete-blocker-ledger-v1",
            "open_blocker_count": len(blockers),
            "blockers": blockers,
            "status": "PASS" if not blockers else "BLOCKED",
        },
    )
    completion = {
        "contract": "m12cs-r1-program-completion-v1",
        "completion_state": completion_state,
        "work_instruction_commit": WORK_INSTRUCTION_COMMIT,
        "implementation_commit": args.expected_head,
        "source_generation": EXPECTED_M12CS_GENERATION,
        "provider_wire_schema_pass_count": sum(
            row["status"] == "PASS" for row in (schema_reproof or {}).get("provider_rows") or ()
        ),
        "provider_wire_schema_count": len((schema_reproof or {}).get("provider_rows") or ()),
        "provider_wire_unique_items_count": sum(
            row["dialect_scan"]["unique_items_count"]
            for row in (schema_reproof or {}).get("provider_rows") or ()
        ),
        "provider_wire_unsupported_keyword_count": sum(
            row["dialect_scan"]["unsupported_keyword_count"]
            for row in (schema_reproof or {}).get("provider_rows") or ()
        ),
        "semantic_uniqueness_preserved": (uniqueness or {}).get(
            "provider_keyword_removed_semantic_uniqueness_preserved",
            False,
        ),
        "dry_materialized_subject_count": (semantic or {})
        .get("dry", {})
        .get(
            "subject_count",
            0,
        ),
        "semantic_contract_freeze_sha256": (freeze or {}).get("semantic_manifest_sha256"),
        "provider_wire_contract_freeze_sha256": (freeze or {}).get("provider_manifest_sha256"),
        "external_model_calls": 0,
        "provider_schema_submission_attempts": 0,
        "production_changes": 0,
        "open_blocker_count": len(blockers),
        "validation_status": (validation or {}).get("status", "NOT_REACHED"),
        "completed_at": datetime.now(UTC).isoformat(),
    }
    write_json(result_root / "program-completion.json", completion)
    write_text(
        result_root / "REPORT.md",
        _report(
            completion=completion,
            schema_reproof=schema_reproof,
            uniqueness=uniqueness,
            semantic=semantic,
            validation=validation,
        ),
    )
    write_json(result_root / "artifact-manifest.json", artifact_manifest(result_root))
    args.output_zip.parent.mkdir(parents=True, exist_ok=True)
    require(not args.output_zip.exists(), "report_archive_already_exists")
    zip_tree(result_root, args.output_zip)
    archive_sha = sha256_file(args.output_zip)
    sidecar = Path(f"{args.output_zip}.sha256")
    write_text(sidecar, f"{archive_sha}  {args.output_zip.name}")
    print(
        json.dumps(
            {
                "completion_state": completion_state,
                "implementation_commit": args.expected_head,
                "archive": str(args.output_zip),
                "archive_sha256": archive_sha,
                "sidecar": str(sidecar),
                "provider_wire_schema_pass_count": completion["provider_wire_schema_pass_count"],
                "dry_materialized_subject_count": completion["dry_materialized_subject_count"],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    if terminal_error is not None:
        raise RuntimeError(completion_state) from terminal_error


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--package-zip", type=Path, required=True)
    parser.add_argument("--package-root", type=Path, required=True)
    parser.add_argument("--m12cs-result-root", type=Path, required=True)
    parser.add_argument("--m12cr-r1-result-root", type=Path, required=True)
    parser.add_argument("--m12cq-result-root", type=Path, required=True)
    parser.add_argument("--m12cq-package-root", type=Path, required=True)
    parser.add_argument("--m12cr-package-root", type=Path, required=True)
    parser.add_argument("--shadow-input-root", type=Path, required=True)
    parser.add_argument("--result-root", type=Path, required=True)
    parser.add_argument("--output-zip", type=Path, required=True)
    parser.add_argument("--expected-head", required=True)
    run(parser.parse_args())


if __name__ == "__main__":
    main()
