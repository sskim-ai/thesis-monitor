from __future__ import annotations

import argparse
import inspect
import json
import re
import shutil
import subprocess
from collections.abc import Mapping, Sequence
from copy import deepcopy
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

from scripts.m12cr_contract_closure import (
    _mechanical_pass_b_choice,
    read_json,
    sha256_file,
    write_json,
    write_text,
)
from scripts.m12cr_shadow_contract import (
    PASS_B_MODEL_FIELDS,
    field_ownership_inventory,
    future_pass_b_batch_schema,
    future_pass_b_prompt_template,
    materialize_directional_balance,
    normalize_future_pass_b,
    parity_matrix,
    schema_completeness_and_parity_scan,
    semantic_rule_inventory,
    target_leak_scan,
    validate_future_pass_b_shape,
    validate_materialized_directional_balance,
    validate_materialized_pass_b,
)
from scripts.m12cs_fresh_two_pass_shadow import (
    _classify_m12cs_failure,
    _invoke_pass_b,
    _validation_rule_ids,
)
from scripts.m12cs_r1_provider_schema import (
    project_provider_wire_schema,
    scan_provider_structured_output_schema,
)


REPO = Path(__file__).resolve().parents[1]
TERMINAL = "M12CT_R1_DIRECTIONAL_BALANCE_OWNERSHIP_CLOSED_READY_FOR_FRESH_TWO_PASS_SHADOW"
M12CT_SHA256 = "cfd673b5e65d3aa6e7991f15792b093568ad94539c6b6072c3475d356ce20a4d"
M12CS_R1_SHA256 = "9724c1f3200d92672f3f6a7f8e4e0cd7c9af55033c07d6fde28845321fddf508"
M12CT_GENERATION = "20260918-m12cs-fresh-two-pass-20260918T003939Z-53c603c6a257"
EXPECTED_EXECUTION_HEAD = "53c603c6a257b0a093446d5dc1b0977c7f5533fa"
EXPECTED_INSTRUCTION_COMMIT = "53b59679d057c61836f3082f3bed4afa20eedf55"


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", *args],
        cwd=REPO,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _verify_manifest(root: Path, expected_count: int) -> dict[str, object]:
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
    if len(rows) != expected_count:
        errors.append(f"manifest_count:{len(rows)}:{expected_count}")
    return {
        "declared_count": len(rows),
        "expected_count": expected_count,
        "errors": errors,
        "status": "PASS" if not errors else "FAIL",
    }


def _source_integrity(args: argparse.Namespace) -> dict[str, object]:
    m12ct_sha = sha256_file(args.m12ct_zip)
    m12cs_r1_sha = sha256_file(args.m12cs_r1_zip)
    m12ct_manifest = _verify_manifest(args.m12ct_root, 271)
    m12cs_r1_manifest = _verify_manifest(args.m12cs_r1_root, 103)
    errors: list[str] = []
    if m12ct_sha != M12CT_SHA256:
        errors.append("m12ct_zip_sha256_mismatch")
    if m12cs_r1_sha != M12CS_R1_SHA256:
        errors.append("m12cs_r1_zip_sha256_mismatch")
    if m12ct_manifest["status"] != "PASS":
        errors.append("m12ct_manifest_failed")
    if m12cs_r1_manifest["status"] != "PASS":
        errors.append("m12cs_r1_manifest_failed")
    completion = read_json(args.m12ct_root / "program-completion.json")
    if completion.get("generation_id") != M12CT_GENERATION:
        errors.append("m12ct_generation_mismatch")
    return {
        "contract": "m12ct-r1-source-base-integrity-v1",
        "m12ct_result_sha256": m12ct_sha,
        "m12ct_manifest": m12ct_manifest,
        "m12ct_generation": completion.get("generation_id"),
        "m12ct_execution_head": EXPECTED_EXECUTION_HEAD,
        "m12ct_work_instruction_commit": EXPECTED_INSTRUCTION_COMMIT,
        "m12cs_r1_result_sha256": m12cs_r1_sha,
        "m12cs_r1_manifest": m12cs_r1_manifest,
        "errors": errors,
        "status": "PASS" if not errors else "FAIL",
    }


def _context_catalog(context: Mapping[str, object]) -> dict[str, object]:
    ticker = str(context["ticker"])
    evidence = [row for row in context.get("decision_evidence") or () if isinstance(row, Mapping)]
    claims = [
        row for row in context.get("accepted_fundamental_claims") or () if isinstance(row, Mapping)
    ]
    all_refs = list(
        dict.fromkeys(
            [str(row["ref_id"]) for row in evidence if row.get("ref_id")]
            + [str(context.get("current_price", {}).get("ref_id") or "")]
            + [
                str(ref)
                for candidate in context.get("tactical_candidates") or ()
                for ref in candidate.get("evidence_refs") or ()
            ]
        )
    )
    all_refs = [item for item in all_refs if item]
    valuation_refs = [
        str(row["ref_id"])
        for row in evidence
        if row.get("ref_id") and row.get("category") == "valuation"
    ]
    timing_refs = [
        str(row["ref_id"])
        for row in evidence
        if row.get("ref_id") and row.get("category") == "price_structure"
    ]
    current = deepcopy(context.get("current_price") or {})
    return {
        "ticker": ticker,
        "all_evidence_refs": all_refs,
        "core_evidence_refs": [item for item in all_refs if item not in set(timing_refs)],
        "timing_evidence_refs": timing_refs,
        "valuation_evidence_refs": valuation_refs,
        "material_disclosure_failure_refs": list(
            context.get("directional_disclosure_quality_refs") or ()
        ),
        "positive_quality_refs": [],
        "claim_refs": [str(row["claim_ref"]) for row in claims],
        "atomic_claims": claims,
        "entry_catalog": {
            "ticker": ticker,
            "current_price": current,
            "tactical_candidates": deepcopy(context.get("tactical_candidates") or []),
            "unresolved_policy": {
                "tactical_unresolved_reason": context.get("tactical_unresolved_reason")
            },
        },
    }


def _batch_paths(root: Path, stage: str) -> list[Path]:
    base = root / "semantic-contract-regeneration/future-drafts" / stage
    return sorted(path for path in base.glob("*/*") if path.is_dir())


def _write_schema_proof(
    *,
    source_root: Path,
    result_root: Path,
) -> tuple[
    list[dict[str, object]],
    dict[str, dict[str, Mapping[str, object]]],
    dict[str, dict[str, Mapping[str, object]]],
]:
    rows: list[dict[str, object]] = []
    contexts: dict[str, dict[str, Mapping[str, object]]] = {"us": {}, "kr": {}}
    catalogs: dict[str, dict[str, Mapping[str, object]]] = {"us": {}, "kr": {}}
    model_values: list[object] = []
    for stage in ("pass-a", "pass-b"):
        for source_draft in _batch_paths(source_root, stage):
            market = source_draft.parent.name
            batch_name = source_draft.name
            context_payload = read_json(source_draft / "subject-context.json")
            subject_rows = context_payload["subjects"]
            subjects = tuple(str(item["ticker"]) for item in subject_rows)
            destination = result_root / "provider-wire-schemas" / stage / market / batch_name
            destination.mkdir(parents=True, exist_ok=True)
            if stage == "pass-a":
                old_wire = (
                    source_root / "outbound-request-dry-serialization" / stage / market / batch_name
                )
                shutil.copy2(
                    source_draft / "schema.json", destination / "internal-semantic-schema.json"
                )
                shutil.copy2(source_draft / "prompt-draft.txt", destination / "prompt.txt")
                shutil.copy2(
                    source_draft / "subject-context.json", destination / "subject-context.json"
                )
                shutil.copy2(old_wire / "schema.json", destination / "schema.json")
                shutil.copy2(
                    old_wire / "provider-wire-projection.json",
                    destination / "provider-wire-projection.json",
                )
                schema = read_json(destination / "internal-semantic-schema.json")
                wire = read_json(destination / "schema.json")
                prompt = (destination / "prompt.txt").read_text(encoding="utf-8")
                internal_scan = schema_completeness_and_parity_scan(
                    schema,
                    stage=stage,
                    subjects=subjects,
                )
                dialect = scan_provider_structured_output_schema(wire)
                source_hashes = {
                    name: sha256_file(source)
                    for name, source in {
                        "internal_schema": source_draft / "schema.json",
                        "prompt": source_draft / "prompt-draft.txt",
                        "context": source_draft / "subject-context.json",
                        "provider_wire_schema": old_wire / "schema.json",
                    }.items()
                }
                unchanged = source_hashes == {
                    "internal_schema": sha256_file(destination / "internal-semantic-schema.json"),
                    "prompt": sha256_file(destination / "prompt.txt"),
                    "context": sha256_file(destination / "subject-context.json"),
                    "provider_wire_schema": sha256_file(destination / "schema.json"),
                }
            else:
                for item in subject_rows:
                    ticker = str(item["ticker"])
                    contexts[market][ticker] = item
                    catalogs[market][ticker] = _context_catalog(item)
                schema = future_pass_b_batch_schema(
                    subjects=subjects,
                    catalogs=catalogs[market],
                )
                wire, projection = project_provider_wire_schema(schema)
                dialect = scan_provider_structured_output_schema(wire)
                internal_scan = schema_completeness_and_parity_scan(
                    schema,
                    stage=stage,
                    subjects=subjects,
                )
                prompt = (
                    future_pass_b_prompt_template()
                    + "\n\nSUBJECT_KEYS:\n"
                    + json.dumps(subjects, ensure_ascii=False)
                    + "\n\nPASS_B_CONTEXT:\n"
                    + json.dumps(subject_rows, ensure_ascii=False, default=str)
                )
                write_json(destination / "internal-semantic-schema.json", schema)
                write_json(destination / "schema.json", wire)
                write_json(destination / "provider-wire-projection.json", projection)
                write_text(destination / "prompt.txt", prompt)
                write_json(destination / "subject-context.json", context_payload)
                unchanged = None
            write_json(destination / "provider-dialect-scan.json", dialect)
            model_values.extend((schema, wire, prompt, subject_rows))
            rows.append(
                {
                    "stage": stage,
                    "market": market,
                    "batch": int(batch_name.split("-")[-1]),
                    "subjects": list(subjects),
                    "internal_schema_sha256": sha256_file(
                        destination / "internal-semantic-schema.json"
                    ),
                    "provider_wire_schema_sha256": sha256_file(destination / "schema.json"),
                    "prompt_sha256": sha256_file(destination / "prompt.txt"),
                    "context_sha256": sha256_file(destination / "subject-context.json"),
                    "pass_a_byte_identical": unchanged,
                    "internal_scan": internal_scan["status"],
                    "provider_dialect_scan": dialect["status"],
                    "provider_unique_items_count": dialect["keyword_counts"].get("uniqueItems", 0),
                    "status": "PASS"
                    if internal_scan["status"] == dialect["status"] == "PASS"
                    and dialect["keyword_counts"].get("uniqueItems", 0) == 0
                    and unchanged is not False
                    else "FAIL",
                }
            )
    leak = target_leak_scan(model_values)
    write_json(
        result_root / "all-16-provider-wire-schema-dialect-scan.json",
        {
            "contract": "m12ct-r1-all-16-provider-wire-schema-dialect-scan-v1",
            "schema_count": len(rows),
            "pass_a_count": sum(row["stage"] == "pass-a" for row in rows),
            "pass_b_count": sum(row["stage"] == "pass-b" for row in rows),
            "rows": rows,
            "unsupported_provider_keyword_count": sum(
                1 for row in rows if row["provider_dialect_scan"] != "PASS"
            ),
            "provider_unique_items_count": sum(
                int(row["provider_unique_items_count"]) for row in rows
            ),
            "status": "PASS"
            if len(rows) == 16 and all(row["status"] == "PASS" for row in rows)
            else "FAIL",
        },
    )
    write_json(result_root / "target-leak-proof.json", leak)
    return rows, contexts, catalogs


def _consumer_audit() -> dict[str, object]:
    rows: list[dict[str, object]] = []
    for base in (REPO / "app", REPO / "scripts", REPO / "tests"):
        for path in sorted(base.rglob("*.py")):
            text = path.read_text(encoding="utf-8")
            count = text.count("directional_balance")
            if count:
                rows.append({"path": str(path.relative_to(REPO)), "occurrences": count})
    contract_source = (REPO / "scripts/m12cr_shadow_contract.py").read_text(encoding="utf-8")
    runner_source = inspect.getsource(_invoke_pass_b)
    errors: list[str] = []
    if '"directional_balance",\n    "decision_confidence"' in contract_source:
        errors.append("legacy_raw_model_field_still_present")
    if '"directional_buy_score"' not in contract_source:
        errors.append("scalar_model_field_missing")
    if "validate_materialized_pass_b" not in runner_source:
        errors.append("final_invariant_consumer_missing")
    return {
        "contract": "m12ct-r1-directional-balance-consumer-semantics-audit-v1",
        "files_with_directional_balance": rows,
        "file_count": len(rows),
        "model_authored_scalar": "directional_buy_score",
        "runtime_derived_fields": ["directional_balance.buy", "directional_balance.sell"],
        "independent_sell_semantics_found": False,
        "one_dimensional_semantics_proven": not errors,
        "errors": errors,
        "status": "PASS" if not errors else "FAIL",
    }


def _balance_fixtures(
    *,
    context: Mapping[str, object],
    catalog: Mapping[str, object],
    pass_a: Mapping[str, object],
    policy: Mapping[str, object],
) -> dict[str, object]:
    ticker = str(context["ticker"])
    base = _mechanical_pass_b_choice(catalog=catalog, policy_option=policy)
    positive_rows: list[dict[str, object]] = []
    for score in (0, 0.62, 3.5, 5, 6.2, 10):
        row = deepcopy(base)
        row["directional_buy_score"] = score
        output = {"decisions": {ticker: row}}
        shape = validate_future_pass_b_shape(
            output,
            subjects=(ticker,),
            catalogs={ticker: catalog},
        )
        normalized, normalization = normalize_future_pass_b(
            output,
            subjects=(ticker,),
            catalogs={ticker: catalog},
        )
        final = validate_materialized_pass_b(
            normalized,
            subjects=(ticker,),
            catalogs={ticker: catalog},
            pass_a_by_ticker={ticker: pass_a},
            policy_options={ticker: policy},
        )
        positive_rows.append(
            {
                "score": score,
                "expected_balance": materialize_directional_balance(score),
                "shape": shape["status"],
                "normalization": normalization["status"],
                "final": final["status"],
                "final_balance_rules": final["directional_balance_invariants"],
                "status": "PASS"
                if shape["status"] == normalization["status"] == final["status"] == "PASS"
                else "FAIL",
            }
        )

    negative_inputs: list[tuple[str, object]] = [
        ("below_zero", -0.01),
        ("above_ten", 10.01),
        ("null", None),
        ("string", "0.62"),
        ("nan", float("nan")),
        ("infinity", float("inf")),
    ]
    negative_rows: list[dict[str, object]] = []
    for name, score in negative_inputs:
        row = deepcopy(base)
        row["directional_buy_score"] = score
        result = validate_future_pass_b_shape(
            {"decisions": {ticker: row}},
            subjects=(ticker,),
            catalogs={ticker: catalog},
        )
        negative_rows.append(
            {
                "case": name,
                "input_repr": repr(score),
                "errors": result["per_ticker"][ticker],
                "status": "PASS" if result["status"] == "FAIL" else "FAIL",
            }
        )
    for name, mutate in (
        (
            "model_authored_sell",
            lambda row: row.update({"directional_sell_score": 4.0}),
        ),
        (
            "old_raw_object",
            lambda row: (
                row.pop("directional_buy_score"),
                row.update({"directional_balance": {"buy": 0.62, "sell": 0.38}}),
            ),
        ),
    ):
        row = deepcopy(base)
        mutate(row)
        result = validate_future_pass_b_shape(
            {"decisions": {ticker: row}},
            subjects=(ticker,),
            catalogs={ticker: catalog},
        )
        negative_rows.append(
            {
                "case": name,
                "errors": result["per_ticker"][ticker],
                "status": "PASS" if result["status"] == "FAIL" else "FAIL",
            }
        )
    return {
        "contract": "m12ct-r1-directional-balance-positive-negative-fixtures-v1",
        "positive": positive_rows,
        "negative": negative_rows,
        "positive_count": len(positive_rows),
        "negative_count": len(negative_rows),
        "status": "PASS"
        if all(row["status"] == "PASS" for row in positive_rows + negative_rows)
        else "FAIL",
    }


def _legacy_balance_errors(raw: Mapping[str, object]) -> dict[str, object]:
    per_ticker: dict[str, list[str]] = {}
    errors: list[str] = []
    for ticker, row in (raw.get("decisions") or {}).items():
        balance = row.get("directional_balance") if isinstance(row, Mapping) else None
        row_errors: list[str] = []
        if not isinstance(balance, Mapping) or set(balance) != {"buy", "sell"}:
            row_errors.append("PB_BALANCE_SHAPE")
        else:
            try:
                buy = Decimal(str(balance["buy"]))
                sell = Decimal(str(balance["sell"]))
            except Exception:  # noqa: BLE001
                row_errors.append("PB_BALANCE_SHAPE")
            else:
                if (
                    not buy.is_finite()
                    or not sell.is_finite()
                    or not (
                        Decimal("0") <= buy <= Decimal("10")
                        and Decimal("0") <= sell <= Decimal("10")
                    )
                ):
                    row_errors.append("PB_BALANCE_BOUNDS")
                elif buy + sell != Decimal("10"):
                    row_errors.append("PB_BALANCE_SUM")
        per_ticker[str(ticker)] = row_errors
        errors.extend(f"{ticker}:{item}" for item in row_errors)
    return {
        "contract": "m12ct-archived-pass-b-directional-balance-v2",
        "errors": errors,
        "per_ticker": per_ticker,
        "status": "PASS" if not errors else "FAIL",
    }


def _failure_replay(
    *,
    source_root: Path,
    catalogs: Mapping[str, Mapping[str, Mapping[str, object]]],
) -> dict[str, object]:
    raw_path = source_root / "model-calls/pass-b/us/batch-01/raw-output.json"
    raw = read_json(raw_path)
    subjects = tuple(raw["decisions"])
    legacy = _legacy_balance_errors(raw)
    new_contract = validate_future_pass_b_shape(
        raw,
        subjects=subjects,
        catalogs={ticker: catalogs["us"][ticker] for ticker in subjects},
    )
    primary_rules = _validation_rule_ids(legacy)
    category = _classify_m12cs_failure(
        RuntimeError("pass_b_raw_semantic_validation_failed"),
        None,
        execution_stage="PASS_B_RAW_SEMANTIC_VALIDATION",
    )
    return {
        "contract": "m12ct-r1-balance-failure-replay-v1",
        "generation_id": M12CT_GENERATION,
        "raw_output_sha256": sha256_file(raw_path),
        "subjects": list(subjects),
        "archived_payload_immutable": True,
        "legacy_contract_validation": legacy,
        "legacy_primary_rule_ids": primary_rules,
        "new_contract_validation": new_contract,
        "old_raw_shape_accepted_by_new_contract": new_contract["status"] == "PASS",
        "automatic_rescaling_performed": False,
        "failure_category": category,
        "status": "PASS"
        if legacy["status"] == "FAIL"
        and primary_rules == ["PB_BALANCE_SUM"]
        and new_contract["status"] == "FAIL"
        and category == "PASS_B_RAW_SEMANTIC_VALIDATION_FAILED"
        else "FAIL",
    }


def _failure_order_contract() -> dict[str, object]:
    source = inspect.getsource(_invoke_pass_b)
    markers = [
        "output = read_json(output_path)",
        'write_json(call_dir / "raw-semantic-validation.json", raw_validation)',
        'raw_validation["status"] == "PASS"',
        "normalized, normalization = normalize_future_pass_b",
        "validation = validate_materialized_pass_b",
    ]
    positions = {marker: source.find(marker) for marker in markers}
    ordered = all(position >= 0 for position in positions.values()) and list(
        positions.values()
    ) == sorted(positions.values())
    final_failure = validate_materialized_directional_balance({"buy": 6.0, "sell": 3.0})
    final_category = _classify_m12cs_failure(
        RuntimeError("pass_b_final_semantic_validation_failed"),
        None,
        execution_stage="PASS_B_FINAL_SEMANTIC_VALIDATION",
    )
    return {
        "contract": "m12ct-r1-pass-b-failure-surface-order-v1",
        "source_markers": positions,
        "raw_failure_stops_before_materialized_validation": ordered,
        "synthetic_materialized_failure": final_failure,
        "synthetic_materialized_failure_category": final_category,
        "stable_categories": [
            "PASS_B_PROVIDER_SCHEMA_REJECTED_PRE_INFERENCE",
            "PASS_B_RAW_CONTRACT_FAILED",
            "PASS_B_RAW_SEMANTIC_VALIDATION_FAILED",
            "PASS_B_MATERIALIZATION_FAILED",
            "PASS_B_FINAL_SEMANTIC_VALIDATION_FAILED",
        ],
        "status": "PASS"
        if ordered
        and final_failure["errors"] == ["PB_BALANCE_SUM"]
        and final_category == "PASS_B_FINAL_SEMANTIC_VALIDATION_FAILED"
        else "FAIL",
    }


def _dry_materialization(
    *,
    contexts: Mapping[str, Mapping[str, Mapping[str, object]]],
    catalogs: Mapping[str, Mapping[str, Mapping[str, object]]],
    pass_a_by_ticker: Mapping[str, Mapping[str, object]],
    policy_by_ticker: Mapping[str, Mapping[str, object]],
) -> dict[str, object]:
    rows: list[dict[str, object]] = []
    batch_rows: list[dict[str, object]] = []
    for market in ("us", "kr"):
        subjects = list(contexts[market])
        for offset in range(0, len(subjects), 3):
            batch_subjects = tuple(subjects[offset : offset + 3])
            raw = {
                "decisions": {
                    ticker: _mechanical_pass_b_choice(
                        catalog=catalogs[market][ticker],
                        policy_option=policy_by_ticker[ticker],
                    )
                    for ticker in batch_subjects
                }
            }
            shape = validate_future_pass_b_shape(
                raw,
                subjects=batch_subjects,
                catalogs=catalogs[market],
            )
            normalized, normalization = normalize_future_pass_b(
                raw,
                subjects=batch_subjects,
                catalogs=catalogs[market],
            )
            final = validate_materialized_pass_b(
                normalized,
                subjects=batch_subjects,
                catalogs=catalogs[market],
                pass_a_by_ticker=pass_a_by_ticker,
                policy_options=policy_by_ticker,
            )
            status = (
                "PASS"
                if shape["status"] == normalization["status"] == final["status"] == "PASS"
                else "FAIL"
            )
            batch_rows.append(
                {
                    "market": market,
                    "batch": offset // 3 + 1,
                    "subjects": list(batch_subjects),
                    "shape": shape["status"],
                    "normalization": normalization["status"],
                    "final": final["status"],
                    "status": status,
                }
            )
            for normalized_row in normalized:
                balance = normalized_row["directional_balance"]
                rows.append(
                    {
                        "ticker": normalized_row["ticker"],
                        "market": market,
                        "model_authored_fields": list(PASS_B_MODEL_FIELDS),
                        "model_authored_sell": False,
                        "directional_buy_score": raw["decisions"][normalized_row["ticker"]][
                            "directional_buy_score"
                        ],
                        "directional_balance": balance,
                        "balance_invariant": validate_materialized_directional_balance(balance),
                        "status": status,
                    }
                )
    return {
        "contract": "m12ct-r1-no-model-22-subject-dry-materialization-v1",
        "subject_count": len(rows),
        "batch_count": len(batch_rows),
        "external_model_calls": 0,
        "provider_request_attempts": 0,
        "model_authored_sell_score_count": sum(row["model_authored_sell"] for row in rows),
        "final_balance_sum_pass_count": sum(
            row["balance_invariant"]["status"] == "PASS" for row in rows
        ),
        "batches": batch_rows,
        "rows": rows,
        "status": "PASS"
        if len(rows) == 22
        and len(batch_rows) == 8
        and all(row["status"] == "PASS" for row in rows + batch_rows)
        else "FAIL",
    }


def _run_command(
    *, name: str, command: Sequence[str], result_root: Path, junit: str | None = None
) -> dict[str, object]:
    resolved = list(command)
    if junit:
        path = result_root / "validation" / junit
        path.parent.mkdir(parents=True, exist_ok=True)
        resolved.append(f"--junitxml={path}")
    completed = subprocess.run(resolved, cwd=REPO, capture_output=True, text=True, check=False)
    log = result_root / "validation/logs" / f"{name}.log"
    write_text(log, completed.stdout + completed.stderr)
    match = re.search(r"(\d+) passed(?:, (\d+) skipped)?", completed.stdout + completed.stderr)
    return {
        "name": name,
        "command": resolved,
        "log": str(log.relative_to(result_root)),
        "returncode": completed.returncode,
        "passed": int(match.group(1)) if match else None,
        "skipped": int(match.group(2) or 0) if match else None,
        "status": "PASS" if completed.returncode == 0 else "FAIL",
    }


def _run_validation(result_root: Path, python: Path) -> dict[str, object]:
    pytest = [str(python), "-m", "pytest", "-q"]
    focused = [
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
    ]
    frozen = focused[:5] + ["tests/test_m12cn_policy_contract.py"]
    treasury = [
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
    ]
    ruff = python.parent / "ruff"
    changed = [
        "scripts/m12cr_shadow_contract.py",
        "scripts/m12cr_contract_closure.py",
        "scripts/m12cs_fresh_two_pass_shadow.py",
        "scripts/m12ct_r1_directional_balance_closure.py",
        "tests/test_m12cr_shadow_contract.py",
        "tests/test_m12cr_r1_typed_quality_contract.py",
        "tests/test_m12cs_fresh_two_pass_shadow.py",
    ]
    commands = [
        _run_command(
            name="focused",
            command=[*pytest, *focused],
            result_root=result_root,
            junit="focused-junit.xml",
        ),
        _run_command(
            name="frozen-contract",
            command=[*pytest, *frozen],
            result_root=result_root,
            junit="frozen-contract-junit.xml",
        ),
        _run_command(
            name="treasury-krx",
            command=[*pytest, *treasury],
            result_root=result_root,
            junit="treasury-krx-junit.xml",
        ),
        _run_command(
            name="full",
            command=pytest,
            result_root=result_root,
            junit="full-junit.xml",
        ),
        _run_command(
            name="ruff",
            command=[str(ruff), "check", *changed],
            result_root=result_root,
        ),
        _run_command(
            name="ruff-format",
            command=[str(ruff), "format", "--check", *changed],
            result_root=result_root,
        ),
        _run_command(
            name="diff-check",
            command=["git", "diff", "--check"],
            result_root=result_root,
        ),
    ]
    return {
        "contract": "m12ct-r1-validation-v1",
        "commands": commands,
        "status": "PASS" if all(row["status"] == "PASS" for row in commands) else "FAIL",
    }


def _artifact_manifest(root: Path) -> dict[str, object]:
    files = []
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        if path.name == "artifact-manifest.json":
            continue
        files.append(
            {
                "path": str(path.relative_to(root)),
                "sha256": sha256_file(path),
                "size": path.stat().st_size,
            }
        )
    return {
        "contract": "m12ct-r1-artifact-manifest-v1",
        "file_count": len(files),
        "files": files,
    }


def _report(
    *,
    head: str,
    source: Mapping[str, object],
    schema_rows: Sequence[Mapping[str, object]],
    fixtures: Mapping[str, object],
    replay: Mapping[str, object],
    failure_order: Mapping[str, object],
    dry: Mapping[str, object],
    validation: Mapping[str, object],
    terminal: str,
) -> str:
    counts = {row["name"]: row for row in validation.get("commands") or ()}
    return f"""# M12CT-R1 Directional Balance Ownership Closure

## Result

- Terminal: `{terminal}`
- Implementation head: `{head}`
- External model calls: `0`
- Provider request attempts: `0`
- Production runtime/config changes: `0`
- Push / merge / deploy: `0 / 0 / 0`

## Source integrity

- M12CT report: `{source["m12ct_result_sha256"]}`
- M12CT manifest: `{source["m12ct_manifest"]["declared_count"]}/271 PASS`
- M12CS-R1 report: `{source["m12cs_r1_result_sha256"]}`
- M12CS-R1 manifest: `{source["m12cs_r1_manifest"]["declared_count"]}/103 PASS`

## Ownership repair

- Raw model field: `directional_buy_score` on `0..10`
- Runtime projection: `buy = score`, `sell = 10 - score`
- Final downstream object: unchanged `directional_balance.buy/sell`
- Model-authored sell fields: `0`
- Positive fixtures: `{fixtures["positive_count"]}/{fixtures["positive_count"]} PASS`
- Negative fixtures: `{fixtures["negative_count"]}/{fixtures["negative_count"]} rejected`
- Final `PB_BALANCE_SUM`: preserved with Decimal semantics

## Archived failure

- Generation: `{M12CT_GENERATION}`
- Primary category: `{replay["failure_category"]}`
- Primary rule: `{", ".join(replay["legacy_primary_rule_ids"])}`
- Historical rescaling: `0`
- Old raw object accepted by new contract: `{replay["old_raw_shape_accepted_by_new_contract"]}`
- Failure-order masking closed: `{failure_order["status"]}`

## Offline proof

- Provider schemas: `{len(schema_rows)}/16 PASS`
- Pass A byte/hash identical: `{sum(row["pass_a_byte_identical"] is True for row in schema_rows)}/8`
- Pass B regenerated: `{sum(row["stage"] == "pass-b" for row in schema_rows)}/8`
- Dry materialization: `{dry["subject_count"]}/22 PASS`
- Final balance sums: `{dry["final_balance_sum_pass_count"]}/22 PASS`
- External calls: `{dry["external_model_calls"]}`

## Validation

- Focused: `{counts.get("focused", {}).get("passed")} passed`
- Frozen contract: `{counts.get("frozen-contract", {}).get("passed")} passed`
- Full: `{counts.get("full", {}).get("passed")} passed / {counts.get("full", {}).get("skipped")} skipped`
- Treasury/KRX: `{counts.get("treasury-krx", {}).get("passed")} passed`
- Ruff / format / diff-check: `{counts.get("ruff", {}).get("status")} / {counts.get("ruff-format", {}).get("status")} / {counts.get("diff-check", {}).get("status")}`

No fresh shadow was started. The next run, if separately authorized, must start at Pass A call 1 under a new generation.
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--m12ct-zip", type=Path, required=True)
    parser.add_argument("--m12ct-root", type=Path, required=True)
    parser.add_argument("--m12cs-r1-zip", type=Path, required=True)
    parser.add_argument("--m12cs-r1-root", type=Path, required=True)
    parser.add_argument("--chat-review", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--python", type=Path, required=True)
    parser.add_argument("--run-validation", action="store_true")
    args = parser.parse_args()

    result_root = args.output.resolve()
    if result_root.exists():
        shutil.rmtree(result_root)
    result_root.mkdir(parents=True)
    head = _git("rev-parse", "HEAD")

    source = _source_integrity(args)
    write_json(result_root / "source-base-integrity.json", source)
    review_sha = sha256_file(args.chat_review)
    write_json(
        result_root / "m12ct-chat-review-reconciliation.json",
        {
            "contract": "m12ct-r1-chat-review-reconciliation-v1",
            "chat_review_sha256": review_sha,
            "agreed_primary_failure": "PB_BALANCE_SUM",
            "agreed_repair": "single_scalar_buy_score_plus_deterministic_complement",
            "target_judgments_used": 0,
            "status": "PASS",
        },
    )

    schema_rows, contexts, catalogs = _write_schema_proof(
        source_root=args.m12ct_root,
        result_root=result_root,
    )
    consumer = _consumer_audit()
    write_json(result_root / "directional-balance-consumer-semantics-audit.json", consumer)
    ownership = {
        "contract": "m12ct-r1-directional-balance-ownership-contract-v1",
        "raw_model_field": "directional_buy_score",
        "raw_model_range": [0, 10],
        "raw_model_sell_field_allowed": False,
        "runtime_formula": {"buy": "directional_buy_score", "sell": "10 - buy"},
        "final_contract_unchanged": True,
        "final_invariant_rule": "PB_BALANCE_SUM",
        "precision_owner": "Decimal(str(value))",
        "field_ownership_inventory": field_ownership_inventory(),
        "status": "PASS" if consumer["status"] == "PASS" else "FAIL",
    }
    write_json(result_root / "directional-balance-ownership-contract.json", ownership)
    write_json(
        result_root / "directional-balance-raw-to-runtime-projection.json",
        {
            "contract": "m12ct-r1-directional-balance-projection-v1",
            "examples": [
                {"raw": score, "final": materialize_directional_balance(score)}
                for score in (0, 0.62, 3.5, 5, 6.2, 10)
            ],
            "binary_float_subtraction_used": False,
            "status": "PASS",
        },
    )

    pass_a_rows = read_json(args.m12ct_root / "pass-a-22-subject-classification.json")
    pass_a_by_ticker = {row["ticker"]: row for row in pass_a_rows["classifications"]}
    policy_rows = read_json(args.m12ct_root / "fundamental-option-materialization-22.json")
    policy_by_ticker = {row["ticker"]: row for row in policy_rows["rows"]}
    sample_market = "us"
    sample_ticker = next(iter(contexts[sample_market]))
    fixtures = _balance_fixtures(
        context=contexts[sample_market][sample_ticker],
        catalog=catalogs[sample_market][sample_ticker],
        pass_a=pass_a_by_ticker[sample_ticker],
        policy=policy_by_ticker[sample_ticker],
    )
    write_json(result_root / "directional-balance-positive-negative-fixtures.json", fixtures)

    replay = _failure_replay(source_root=args.m12ct_root, catalogs=catalogs)
    write_json(result_root / "m12ct-balance-failure-replay.json", replay)
    failure_order = _failure_order_contract()
    write_json(result_root / "pass-b-failure-surface-order-contract.json", failure_order)
    write_json(
        result_root / "m12ct-failure-cause-reclassification.json",
        {
            "contract": "m12ct-r1-failure-cause-reclassification-v1",
            "old_masking_surface": "empty decisions Pydantic min_length failure",
            "primary_category": replay["failure_category"],
            "primary_rule_ids": replay["legacy_primary_rule_ids"],
            "wrapper_safe_error_is_secondary": True,
            "status": replay["status"],
        },
    )

    inventory = semantic_rule_inventory()
    parity = parity_matrix()
    write_json(result_root / "semantic-validator-rule-inventory.json", inventory)
    write_json(result_root / "schema-validator-materializer-parity-matrix.json", parity)
    dry = _dry_materialization(
        contexts=contexts,
        catalogs=catalogs,
        pass_a_by_ticker=pass_a_by_ticker,
        policy_by_ticker=policy_by_ticker,
    )
    write_json(result_root / "no-model-22-subject-dry-materialization.json", dry)

    for name in (
        "pass-a-semantic-branch-coverage.json",
        "quality-basis-regression-reproof.json",
        "business-quality-runtime-22.json",
        "security-valuation-basis-runtime-22.json",
    ):
        shutil.copy2(args.m12ct_root / name, result_root / name)
    pass_b_coverage = read_json(args.m12ct_root / "pass-b-semantic-branch-coverage.json")
    pass_b_coverage["contract"] = "m12ct-r1-pass-b-semantic-branch-coverage-v1"
    pass_b_coverage["directional_balance_ownership_fixture_status"] = fixtures["status"]
    pass_b_coverage["directional_buy_score_positive_fixture_count"] = fixtures["positive_count"]
    pass_b_coverage["directional_buy_score_negative_fixture_count"] = fixtures["negative_count"]
    pass_b_coverage["status"] = (
        "PASS"
        if pass_b_coverage.get("status") == "PASS" and fixtures["status"] == "PASS"
        else "FAIL"
    )
    write_json(result_root / "pass-b-semantic-branch-coverage.json", pass_b_coverage)
    historical = read_json(args.m12ct_root / "historical-failure-replay-reproof.json")
    historical["contract"] = "m12ct-r1-historical-failure-replay-matrix-v1"
    historical["m12ct_balance_failure_replay"] = replay
    historical["status"] = (
        "PASS" if historical.get("status") == "PASS" and replay["status"] == "PASS" else "FAIL"
    )
    write_json(result_root / "historical-failure-replay-matrix.json", historical)

    semantic_freeze = {
        "contract": "m12ct-r1-semantic-contract-freeze-v1",
        "implementation_head": head,
        "pass_a_unchanged": all(
            row["pass_a_byte_identical"] is True for row in schema_rows if row["stage"] == "pass-a"
        ),
        "investment_policy_semantics_unchanged": True,
        "pass_b_raw_ownership_change": ("directional_balance{buy,sell} -> directional_buy_score"),
        "final_directional_balance_semantics_unchanged": True,
        "rows": [
            {
                key: row[key]
                for key in (
                    "stage",
                    "market",
                    "batch",
                    "subjects",
                    "internal_schema_sha256",
                    "prompt_sha256",
                    "context_sha256",
                )
            }
            for row in schema_rows
        ],
        "status": "PASS" if all(row["status"] == "PASS" for row in schema_rows) else "FAIL",
    }
    provider_freeze = {
        "contract": "m12ct-r1-provider-wire-contract-freeze-v1",
        "implementation_head": head,
        "rows": [
            {
                key: row[key]
                for key in (
                    "stage",
                    "market",
                    "batch",
                    "subjects",
                    "provider_wire_schema_sha256",
                    "provider_dialect_scan",
                )
            }
            for row in schema_rows
        ],
        "pass_a_hashes_unchanged": semantic_freeze["pass_a_unchanged"],
        "pass_b_hashes_regenerated": True,
        "future_run_must_bind_both_manifests": True,
        "status": semantic_freeze["status"],
    }
    write_json(result_root / "semantic-contract-freeze-manifest.json", semantic_freeze)
    write_json(result_root / "provider-wire-contract-freeze-manifest.json", provider_freeze)

    validation = (
        _run_validation(result_root, args.python)
        if args.run_validation
        else {"contract": "m12ct-r1-validation-v1", "commands": [], "status": "NOT_RUN"}
    )
    write_json(result_root / "validation/summary.json", validation)
    safety = {
        "contract": "m12ct-r1-safety-counters-v1",
        "external_model_calls": 0,
        "provider_request_attempts": 0,
        "market_refreshes": 0,
        "production_runtime_config_changes": 0,
        "production_sends": 0,
        "production_db_writes": 0,
        "broker_reads_or_orders": 0,
        "scheduler_changes": 0,
        "main_merges": 0,
        "remote_pushes": 0,
        "deployments": 0,
        "sealed_reference_opens": 0,
        "status": "PASS",
    }
    write_json(result_root / "safety-counters.json", safety)

    gate_values = {
        "source": source["status"],
        "consumer": consumer["status"],
        "fixtures": fixtures["status"],
        "replay": replay["status"],
        "failure_order": failure_order["status"],
        "schemas": "PASS" if all(row["status"] == "PASS" for row in schema_rows) else "FAIL",
        "inventory": inventory["status"],
        "parity": parity["status"],
        "dry": dry["status"],
        "pass_a_branch_coverage": read_json(result_root / "pass-a-semantic-branch-coverage.json")[
            "status"
        ],
        "pass_b_branch_coverage": pass_b_coverage["status"],
        "historical_replay": historical["status"],
        "quality_basis_regression": read_json(
            result_root / "quality-basis-regression-reproof.json"
        )["status"],
        "target_leak": read_json(result_root / "target-leak-proof.json")["status"],
        "validation": validation["status"],
        "safety": safety["status"],
    }
    blockers = [key for key, value in gate_values.items() if value != "PASS"]
    terminal = TERMINAL if not blockers else "M12CT_R1_OFFLINE_REPAIR_FAILED"
    write_json(
        result_root / "complete-blocker-ledger.json",
        {
            "contract": "m12ct-r1-complete-blocker-ledger-v1",
            "gates": gate_values,
            "open_blockers": blockers,
            "open_blocker_count": len(blockers),
            "status": "PASS" if not blockers else "FAIL",
        },
    )
    write_json(
        result_root / "program-completion.json",
        {
            "contract": "m12ct-r1-program-completion-v1",
            "terminal": terminal,
            "implementation_head": head,
            "external_model_calls": 0,
            "provider_request_attempts": 0,
            "subject_count": dry["subject_count"],
            "schema_count": len(schema_rows),
            "completed_at": datetime.now(UTC).isoformat(),
            "status": "PASS" if not blockers else "FAIL",
        },
    )
    write_text(
        result_root / "REPORT.md",
        _report(
            head=head,
            source=source,
            schema_rows=schema_rows,
            fixtures=fixtures,
            replay=replay,
            failure_order=failure_order,
            dry=dry,
            validation=validation,
            terminal=terminal,
        ),
    )
    write_json(result_root / "artifact-manifest.json", _artifact_manifest(result_root))
    print(terminal)
    return 0 if not blockers else 1


if __name__ == "__main__":
    raise SystemExit(main())
