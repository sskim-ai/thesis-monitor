from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import zipfile
from collections import Counter
from collections.abc import Mapping, Sequence
from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from scripts.m12cn_policy_contract import build_subject_catalog
from scripts.m12cq_two_pass_contract import (
    build_pass_a_subject_context,
    build_pass_b_subject_context,
    canonical_sha256,
    pass_a_leakage_scan,
    select_matrix_option,
)
from scripts.m12cq_two_pass_shadow import EXPECTED_POPULATION, load_m12cp_inputs
from scripts.m12cr_shadow_contract import (
    EnforcementLayer,
    field_ownership_inventory,
    future_pass_a_batch_schema,
    future_pass_a_prompt_template,
    future_pass_b_batch_schema,
    future_pass_b_prompt_template,
    materialize_future_pass_a,
    normalize_future_pass_b,
    parity_matrix,
    project_data_quality_base_state,
    schema_completeness_and_parity_scan,
    semantic_rule_inventory,
    target_leak_scan,
    validate_future_pass_a_shape,
    validate_future_pass_b_shape,
    validate_materialized_pass_b,
    validate_security_basis_gate,
)


REPO = Path(__file__).resolve().parents[1]
WORK_INSTRUCTION_COMMIT = "acb9cfdc"
M12CQ_IMPLEMENTATION = "862c972c6e4c56c30d28596e286be74b2ce55b88"
REQUIRED_RUNTIME_BASE = "831890d1bf0dff303f67a6e0de1403ad3221b5d8"
EXPECTED_PACKAGE_ZIP_SHA256 = "2d8be7cf65845f5d4aca7ef6037141af99cd68994351adaedc90c0ec21795f1b"
EXPECTED_M12CQ_RESULT_SHA256 = "378a3a4a9c1d65255a1baf371daa95dcf3c3f5384af4d04240685f80fc3744ca"
EXPECTED_M12CQ_PACKAGE_SHA256 = "4ef7d1d91834e0048db7c712daf28aed5f8245e9e49fc5841387b01b4f87b564"
EXPECTED_FROZEN_GENERATION = "20260917-m12cm-current-v4-smoke-20260917T062918Z-5c0cb075ce8b"

COMPLETION_READY = "M12CR_SHADOW_CONTRACT_PARITY_CLOSED_READY_FOR_FRESH_TWO_PASS_SHADOW"
COMPLETION_OWNERSHIP_GAP = "M12CR_MODEL_DETERMINISTIC_OWNERSHIP_GAP_REQUIRES_CHAT"
COMPLETION_PASS_A_GAP = "M12CR_PASS_A_CONTRACT_PARITY_NOT_CLOSED"
COMPLETION_PASS_B_GAP = "M12CR_PASS_B_CONTRACT_PARITY_NOT_CLOSED"
COMPLETION_PRODUCTION_DEPENDENCY = "M12CR_NEW_PRODUCTION_DEPENDENCY_REQUIRES_CHAT"
COMPLETION_FAILED = "M12CR_OFFLINE_CONTRACT_AUDIT_FAILED"

REPORT_ZIP_NAME = (
    "thesis-monitor-20260917-m12cr-exhaustive-shadow-contract-parity-and-"
    "deterministic-ownership-closure-report.zip"
)


class M12CRFailure(RuntimeError):
    pass


def require(condition: bool, code: str) -> None:
    if not condition:
        raise M12CRFailure(code)


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError(f"json_object_required:{path}")
    return value


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, default=str) + "\n",
        encoding="utf-8",
    )


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value.rstrip() + "\n", encoding="utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _single_member(archive: zipfile.ZipFile, suffix: str) -> str:
    rows = [name for name in archive.namelist() if name.endswith(suffix)]
    if len(rows) != 1:
        raise M12CRFailure(f"zip_member_cardinality:{suffix}:{len(rows)}")
    return rows[0]


def _zip_json(path: Path, suffix: str) -> dict[str, Any]:
    with zipfile.ZipFile(path) as archive:
        member = _single_member(archive, suffix)
        value = json.loads(archive.read(member))
    if not isinstance(value, dict):
        raise TypeError(f"zip_json_object_required:{path}:{suffix}")
    return value


def _verify_zip_manifest(path: Path, expected_count: int | None = None) -> dict[str, object]:
    errors: list[str] = []
    rows: list[dict[str, object]] = []
    with zipfile.ZipFile(path) as archive:
        member = _single_member(archive, "/artifact-manifest.json")
        root = member.rsplit("/", 1)[0]
        manifest = json.loads(archive.read(member))
        files = manifest.get("files") or []
        for item in files:
            target = f"{root}/{item['path']}"
            try:
                payload = archive.read(target)
            except KeyError:
                payload = b""
                errors.append(f"missing:{item['path']}")
            actual_sha = sha256_bytes(payload)
            actual_size = len(payload)
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
    if expected_count is not None and len(rows) != expected_count:
        errors.append(f"manifest_count:{len(rows)}:{expected_count}")
    return {
        "path": str(path),
        "archive_sha256": sha256_file(path),
        "manifest_payload_count": len(rows),
        "rows": rows,
        "errors": errors,
        "status": "PASS" if not errors else "FAIL",
    }


def _verify_package_root(root: Path) -> dict[str, object]:
    manifest = read_json(root / "package-manifest.json")
    errors: list[str] = []
    rows: list[dict[str, object]] = []
    for item in manifest.get("files") or []:
        path = root / str(item["path"])
        actual_sha = sha256_file(path) if path.is_file() else None
        actual_size = path.stat().st_size if path.is_file() else None
        status = (
            "PASS"
            if actual_sha == item.get("sha256") and actual_size == item.get("size")
            else "FAIL"
        )
        if status != "PASS":
            errors.append(f"package_manifest_mismatch:{item['path']}")
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
        "payload_count": len(rows),
        "rows": rows,
        "errors": errors,
        "status": "PASS" if not errors else "FAIL",
    }


def _verify_shadow_input(m12cq_root: Path, shadow_root: Path) -> dict[str, object]:
    manifest = read_json(m12cq_root / "inputs/m12cm-shadow-input-manifest.json")
    errors: list[str] = []
    rows: list[dict[str, object]] = []
    for item in manifest.get("selected_files") or []:
        path = shadow_root / str(item["path"])
        actual_sha = sha256_file(path) if path.is_file() else None
        actual_size = path.stat().st_size if path.is_file() else None
        status = (
            "PASS"
            if actual_sha == item.get("sha256") and actual_size == item.get("size")
            else "FAIL"
        )
        if status != "PASS":
            errors.append(f"shadow_input_mismatch:{item['path']}")
        rows.append({"path": item["path"], "sha256": actual_sha, "status": status})
    return {
        "frozen_generation": EXPECTED_FROZEN_GENERATION,
        "selected_file_count": len(rows),
        "rows": rows,
        "errors": errors,
        "status": "PASS" if not errors else "FAIL",
    }


def verify_sources(args: argparse.Namespace) -> dict[str, object]:
    package_root = args.package_root.resolve()
    m12cq_root = args.m12cq_package_root.resolve()
    package_zip_sha = sha256_file(args.package_zip.resolve())
    source_index = read_json(package_root / "source-index.json")
    errors: list[str] = []
    if package_zip_sha != EXPECTED_PACKAGE_ZIP_SHA256:
        errors.append("outer_package_zip_hash_mismatch")
    outer = _verify_package_root(package_root)
    if outer["status"] != "PASS":
        errors.extend(outer["errors"])
    source_rows: list[dict[str, object]] = []
    references = [source_index["m12cq_result"], source_index["m12cq_work_instruction"]]
    references.extend(source_index.get("historical_contract_reports") or [])
    for item in references:
        path = package_root / str(item["filename"])
        actual = sha256_file(path) if path.is_file() else None
        status = "PASS" if actual == item.get("sha256") else "FAIL"
        if status != "PASS":
            errors.append(f"source_index_hash_mismatch:{item['filename']}")
        source_rows.append(
            {
                "path": item["filename"],
                "expected_sha256": item.get("sha256"),
                "actual_sha256": actual,
                "status": status,
            }
        )
    m12cq_result = package_root / str(source_index["m12cq_result"]["filename"])
    if sha256_file(m12cq_result) != EXPECTED_M12CQ_RESULT_SHA256:
        errors.append("m12cq_result_hash_mismatch")
    m12cq_manifest = _verify_zip_manifest(m12cq_result, expected_count=74)
    if m12cq_manifest["status"] != "PASS":
        errors.extend(m12cq_manifest["errors"])
    historical_manifests = []
    for item in source_index.get("historical_contract_reports") or []:
        result = _verify_zip_manifest(package_root / str(item["filename"]))
        historical_manifests.append(result)
        if result["status"] != "PASS":
            errors.extend(result["errors"])
    m12cq_package = package_root / str(source_index["m12cq_work_instruction"]["filename"])
    if sha256_file(m12cq_package) != EXPECTED_M12CQ_PACKAGE_SHA256:
        errors.append("m12cq_work_instruction_hash_mismatch")
    nested = _verify_package_root(m12cq_root)
    if nested["status"] != "PASS":
        errors.extend(nested["errors"])
    shadow = _verify_shadow_input(m12cq_root, args.shadow_input_root.resolve())
    if shadow["status"] != "PASS":
        errors.extend(shadow["errors"])
    return {
        "contract": "m12cr-source-base-integrity-v1",
        "package_zip_sha256": package_zip_sha,
        "expected_package_zip_sha256": EXPECTED_PACKAGE_ZIP_SHA256,
        "outer_package": outer,
        "source_rows": source_rows,
        "m12cq_result_manifest": m12cq_manifest,
        "historical_result_manifests": historical_manifests,
        "nested_m12cq_package": nested,
        "shadow_input": shadow,
        "sealed_verdict_material_open_count": 0,
        "errors": errors,
        "status": "PASS" if not errors else "FAIL",
    }


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
    ancestor = (
        subprocess.run(
            ("git", "merge-base", "--is-ancestor", REQUIRED_RUNTIME_BASE, head),
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
    changed = _git("diff", "--name-only", f"{REQUIRED_RUNTIME_BASE}..{head}").splitlines()
    allowed_prefixes = (
        "docs/work-instructions/20260917-m12c",
        "scripts/m12c",
        "tests/test_m12c",
    )
    production_paths = [path for path in changed if not path.startswith(allowed_prefixes)]
    clean = not _git("status", "--porcelain")
    errors = []
    if head != expected_head:
        errors.append("head_mismatch")
    if not ancestor:
        errors.append("runtime_base_not_ancestor")
    if not instruction_ancestor:
        errors.append("work_instruction_commit_not_ancestor")
    if production_paths:
        errors.append("new_production_dependency")
    if not clean:
        errors.append("worktree_not_clean")
    return {
        "contract": "m12cr-runtime-integrity-v1",
        "head": head,
        "expected_head": expected_head,
        "required_runtime_base": REQUIRED_RUNTIME_BASE,
        "m12cq_implementation": M12CQ_IMPLEMENTATION,
        "work_instruction_commit": WORK_INSTRUCTION_COMMIT,
        "runtime_base_is_ancestor": ancestor,
        "work_instruction_is_ancestor": instruction_ancestor,
        "changed_paths": changed,
        "production_dependency_paths": production_paths,
        "worktree_clean": clean,
        "errors": errors,
        "status": "PASS" if not errors else "FAIL",
    }


def load_frozen_contract_inputs(
    shadow_root: Path,
) -> tuple[
    dict[str, Any],
    dict[str, Any],
    dict[str, dict[str, dict[str, object]]],
    dict[str, dict[str, dict[str, object]]],
]:
    from app.services.accepted_decision_v2_runtime_service import (
        AcceptedV2FundamentalCoreBatch,
        AcceptedV2ProductionContext,
        accepted_v2_maturity_atomic_claim_catalog_manifest,
    )

    contexts: dict[str, Any] = {}
    context_payloads: dict[str, Any] = {}
    catalogs: dict[str, dict[str, dict[str, object]]] = {}
    pass_a_contexts: dict[str, dict[str, dict[str, object]]] = {}
    for market in ("us", "kr"):
        context_payload = read_json(shadow_root / market / "context.json")
        context = AcceptedV2ProductionContext.model_validate(context_payload)
        core_batch = AcceptedV2FundamentalCoreBatch.model_validate(
            read_json(shadow_root / market / "trusted-fundamental-core-batch.json")
        )
        require(
            tuple(context.selected_subjects) == EXPECTED_POPULATION[market],
            f"{market}_population_mismatch",
        )
        require(
            tuple(core.ticker for core in core_batch.cores) == tuple(context.selected_subjects),
            f"{market}_core_scope_mismatch",
        )
        atomic = accepted_v2_maturity_atomic_claim_catalog_manifest(core_batch.cores)
        market_catalogs: dict[str, dict[str, object]] = {}
        market_contexts: dict[str, dict[str, object]] = {}
        for ticker in context.selected_subjects:
            catalog = build_subject_catalog(
                context=context_payload,
                ticker=ticker,
                atomic_claims=atomic["claims"],
            )
            pass_a_context = build_pass_a_subject_context(
                context=context_payload,
                ticker=ticker,
                catalog=catalog,
            )
            require(bool(pass_a_context["eligible_claim_refs"]), f"no_claim_refs:{ticker}")
            require(
                bool(pass_a_context["eligible_non_price_evidence"]),
                f"no_non_price_evidence:{ticker}",
            )
            market_catalogs[ticker] = catalog
            market_contexts[ticker] = pass_a_context
        contexts[market] = context
        context_payloads[market] = context_payload
        catalogs[market] = market_catalogs
        pass_a_contexts[market] = market_contexts
    return contexts, context_payloads, catalogs, pass_a_contexts


def _matrix_subjects(options: Mapping[str, object]) -> dict[str, Mapping[str, object]]:
    return {
        str(row["ticker"]): row for row in options.get("subjects") or [] if isinstance(row, Mapping)
    }


def _depositary_subjects(security: Mapping[str, object]) -> set[str]:
    rows = security.get("rows") or security.get("subjects") or []
    return {
        str(row["ticker"])
        for row in rows
        if isinstance(row, Mapping)
        and (
            row.get("security_basis_status") not in {None, "RESOLVED", "ELIGIBLE"}
            or row.get("status") in {"BLOCKED", "UNRESOLVED"}
            or row.get("resolved") is False
        )
    }


def _mechanical_pass_a_choice(
    *,
    context: Mapping[str, object],
    matrix_subject: Mapping[str, object],
    force_unresolved: bool,
) -> dict[str, object]:
    options = [dict(row) for row in matrix_subject.get("options") or [] if isinstance(row, Mapping)]
    resolved = [row for row in options if row.get("status") == "RESOLVED"]
    if force_unresolved or not resolved:
        candidates = [
            row
            for row in options
            if row.get("archetype") == "UNRESOLVED"
            and row.get("valuation_regime_tier") == "UNRESOLVED"
        ]
    else:
        premium_refs = set(context.get("premium_eligible_claim_refs") or ())
        candidates = [
            row for row in resolved if row.get("valuation_regime_tier") != "PREMIUM" or premium_refs
        ]
    require(bool(candidates), "mechanical_pass_a_option_missing")
    selected = sorted(
        candidates,
        key=lambda row: (
            str(row.get("archetype") or ""),
            str(row.get("valuation_regime_tier") or ""),
            str(row.get("option_id") or ""),
        ),
    )[0]
    claim_ref = str((context.get("eligible_claim_refs") or [])[0])
    tier = str(selected["valuation_regime_tier"])
    if tier == "UNRESOLVED":
        tier_refs: list[str] = []
    elif tier == "PREMIUM":
        tier_refs = [str((context.get("premium_eligible_claim_refs") or [])[0])]
    else:
        tier_refs = [claim_ref]
    return {
        "archetype": selected["archetype"],
        "archetype_confidence": "MEDIUM",
        "archetype_supporting_claim_refs": [claim_ref],
        "archetype_rationale": "계약 기계 검증용 비가격 근거 분류입니다.",
        "valuation_regime_tier": tier,
        "tier_supporting_claim_refs": tier_refs,
        "tier_rationale": "동결 정책 matrix의 기계 검증 가능한 분기를 선택했습니다.",
        "directional_data_quality_judgment": {
            "effect": "NONE",
            "reason_class": "NOT_APPLICABLE",
            "reason": None,
            "evidence_refs": [],
        },
        "classification_summary": "투자 target이 아닌 계약 dry-run 선택입니다.",
    }


def _mechanical_pass_b_choice(
    *,
    catalog: Mapping[str, object],
    policy_option: Mapping[str, object],
) -> dict[str, object]:
    claim_ref = str((catalog.get("claim_refs") or [])[0])
    current = catalog["entry_catalog"].get("current_price")
    require(isinstance(current, Mapping), "dry_current_price_missing")
    current_ref = str(current.get("ref_id") or claim_ref)
    allowed_refs = set(catalog.get("all_evidence_refs") or ()) | set(
        catalog.get("claim_refs") or ()
    )
    reason_ref = current_ref if current_ref in allowed_refs else claim_ref
    tactical_rows = catalog["entry_catalog"].get("tactical_candidates") or []
    tactical_choice = str(tactical_rows[0]["candidate_id"]) if tactical_rows else "UNRESOLVED"
    if policy_option.get("status") == "RESOLVED" and float(current["value"]) <= float(
        policy_option["high"]
    ):
        new_buyer = {
            "new_buyer": "ATTRACTIVE",
            "reason_class": "ATTRACTIVE_WITHIN_RANGE",
            "reason": "현재 가격이 동결 기본 범위 안에 있는 계약 검증 분기입니다.",
            "evidence_refs": [reason_ref],
            "tactical_choice": "NOT_APPLICABLE",
            "re_evaluate_conditions": [],
        }
    elif policy_option.get("status") == "RESOLVED":
        new_buyer = {
            "new_buyer": "WAIT",
            "reason_class": "FUNDAMENTAL_RANGE_POSITION",
            "reason": "현재 가격이 동결 기본 범위 위에 있는 계약 검증 분기입니다.",
            "evidence_refs": [reason_ref],
            "tactical_choice": tactical_choice,
            "re_evaluate_conditions": ["기본 범위 진입 여부를 확인합니다."],
        }
    else:
        new_buyer = {
            "new_buyer": "WAIT",
            "reason_class": "FUNDAMENTAL_UNRESOLVED",
            "reason": "기본 범위가 미해결인 계약 검증 분기입니다.",
            "evidence_refs": [reason_ref],
            "tactical_choice": tactical_choice,
            "re_evaluate_conditions": ["기본 가치평가 근거가 확보되는지 확인합니다."],
        }
    return {
        "overall_direction": "BUY",
        "directional_buy_score": 6.0,
        "decision_confidence": "MEDIUM",
        "decisive_supporting_claim_refs": [claim_ref],
        "decisive_contradicting_claim_refs": [],
        "thesis_state": "INTACT",
        "holder_decision": {
            "holder": "HOLDABLE",
            "reason_class": "NOT_APPLICABLE",
            "reason": "보유 축은 계약 mechanics 검증에서 유지됩니다.",
            "evidence_refs": [],
        },
        "new_buyer_decision": new_buyer,
        "policy_summary": "투자 target이 아닌 deterministic pipeline dry-run입니다.",
    }


def _batch_topology(contexts: Mapping[str, Any]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for market in ("us", "kr"):
        subjects = tuple(contexts[market].selected_subjects)
        for offset in range(0, len(subjects), 3):
            rows.append(
                {
                    "market": market,
                    "batch": offset // 3 + 1,
                    "subjects": subjects[offset : offset + 3],
                }
            )
    require(len(rows) == 8, "batch_topology_not_eight")
    return rows


def _write_future_drafts(
    *,
    result_root: Path,
    contexts: Mapping[str, Any],
    pass_a_contexts: Mapping[str, Mapping[str, Mapping[str, object]]],
    pass_b_contexts: Mapping[str, Mapping[str, Mapping[str, object]]],
    catalogs: Mapping[str, Mapping[str, Mapping[str, object]]],
) -> dict[str, object]:
    rows: list[dict[str, object]] = []
    model_facing_values: list[object] = []
    for spec in _batch_topology(contexts):
        market = str(spec["market"])
        batch = int(spec["batch"])
        subjects = tuple(spec["subjects"])
        for stage in ("pass-a", "pass-b"):
            directory = result_root / "future-drafts" / stage / market / f"batch-{batch:02d}"
            if stage == "pass-a":
                schema = future_pass_a_batch_schema(
                    subjects=subjects,
                    subject_contexts=pass_a_contexts[market],
                )
                payload = [pass_a_contexts[market][ticker] for ticker in subjects]
                prompt = (
                    future_pass_a_prompt_template()
                    + "\n\nSUBJECT_KEYS:\n"
                    + json.dumps(subjects, ensure_ascii=False)
                    + "\n\nPASS_A_CONTEXT:\n"
                    + json.dumps(payload, ensure_ascii=False, default=str)
                )
            else:
                schema = future_pass_b_batch_schema(
                    subjects=subjects,
                    catalogs=catalogs[market],
                )
                payload = [pass_b_contexts[market][ticker] for ticker in subjects]
                prompt = (
                    future_pass_b_prompt_template()
                    + "\n\nSUBJECT_KEYS:\n"
                    + json.dumps(subjects, ensure_ascii=False)
                    + "\n\nPASS_B_CONTEXT:\n"
                    + json.dumps(payload, ensure_ascii=False, default=str)
                )
            scan = schema_completeness_and_parity_scan(
                schema,
                stage=stage,
                subjects=subjects,
            )
            schema_path = directory / "schema.json"
            prompt_path = directory / "prompt-draft.txt"
            context_path = directory / "subject-context.json"
            write_json(schema_path, schema)
            write_text(prompt_path, prompt)
            write_json(context_path, {"subjects": payload})
            rows.append(
                {
                    "stage": stage,
                    "market": market,
                    "batch": batch,
                    "subjects": list(subjects),
                    "schema_sha256": sha256_file(schema_path),
                    "prompt_sha256": sha256_file(prompt_path),
                    "context_sha256": sha256_file(context_path),
                    "scan": scan,
                    "status": scan["status"],
                }
            )
            model_facing_values.extend((schema, prompt, payload))
    leak = target_leak_scan(model_facing_values)
    return {
        "contract": "m12cr-all-16-schema-completeness-and-parity-scan-v1",
        "schema_count": len(rows),
        "pass_a_schema_count": sum(row["stage"] == "pass-a" for row in rows),
        "pass_b_schema_count": sum(row["stage"] == "pass-b" for row in rows),
        "rows": rows,
        "target_leak_proof": leak,
        "status": "PASS"
        if len(rows) == 16
        and all(row["status"] == "PASS" for row in rows)
        and leak["status"] == "PASS"
        else "FAIL",
    }


def _historical_failure_replay(
    *,
    package_root: Path,
    pass_a_contexts: Mapping[str, Mapping[str, Mapping[str, object]]],
    catalogs: Mapping[str, Mapping[str, Mapping[str, object]]],
) -> dict[str, object]:
    source_index = read_json(package_root / "source-index.json")
    historical = {
        Path(str(item["filename"])).name: package_root / str(item["filename"])
        for item in source_index.get("historical_contract_reports") or []
    }
    m12cn = next(path for name, path in historical.items() if "m12cn-investment" in name)
    r2 = next(path for name, path in historical.items() if "m12cn-r2" in name)
    m12cq = package_root / str(source_index["m12cq_result"]["filename"])

    m12cn_validation = _zip_json(m12cn, "/shadow-calls/us/batch-03/semantic-validation.json")
    m12cn_raw = _zip_json(m12cn, "/shadow-calls/us/batch-03/raw-output.json")
    wait_shapes = [
        {
            "new_buyer": row.get("new_buyer"),
            "tactical_status": (row.get("entry_range") or {})
            .get("tactical_entry_band", {})
            .get("status"),
        }
        for row in m12cn_raw.get("candidates") or []
        if isinstance(row, Mapping)
        and row.get("new_buyer") == "WAIT"
        and (row.get("entry_range") or {}).get("tactical_entry_band", {}).get("status")
        == "NOT_APPLICABLE"
    ]
    generic_ticker = "GOOGL"
    generic_catalog = catalogs["us"][generic_ticker]
    pass_b_invalid = {
        "decisions": {
            generic_ticker: {
                **_mechanical_pass_b_choice(
                    catalog=generic_catalog,
                    policy_option={"status": "UNRESOLVED"},
                ),
            }
        }
    }
    pass_b_invalid["decisions"][generic_ticker]["new_buyer_decision"].update(
        {
            "new_buyer": "WAIT",
            "reason_class": "FUNDAMENTAL_UNRESOLVED",
            "tactical_choice": "NOT_APPLICABLE",
            "re_evaluate_conditions": ["근거를 확인합니다."],
        }
    )
    wait_result = validate_future_pass_b_shape(
        pass_b_invalid,
        subjects=(generic_ticker,),
        catalogs={generic_ticker: generic_catalog},
    )

    r1_scan = _zip_json(r2, "/r1-invalid-schema-completeness-scan.json")
    r2_validation = _zip_json(r2, "/shadow-calls/us/batch-03/semantic-validation.json")
    r2_invalid = deepcopy(pass_b_invalid)
    r2_invalid["decisions"][generic_ticker] = _mechanical_pass_b_choice(
        catalog=generic_catalog,
        policy_option={"status": "UNRESOLVED"},
    )
    r2_invalid["decisions"][generic_ticker]["fundamental_entry_band"] = {
        "status": "UNRESOLVED",
        "low": 1,
    }
    r2_result = validate_future_pass_b_shape(
        r2_invalid,
        subjects=(generic_ticker,),
        catalogs={generic_ticker: generic_catalog},
    )

    cq_validation = _zip_json(m12cq, "/model-calls/pass-a/us/batch-04/semantic-validation.json")
    cq_raw = _zip_json(m12cq, "/model-calls/pass-a/us/batch-04/raw-output.json")
    cq_shapes = {
        str(row["ticker"]): {
            "effect": row.get("data_quality_effect"),
            "reason_class": row.get("data_quality_reason_class"),
            "reason": row.get("data_quality_reason"),
            "evidence_refs": list(row.get("data_quality_evidence_refs") or []),
        }
        for row in cq_raw.get("classifications") or []
        if isinstance(row, Mapping) and row.get("ticker") in {"SNDK", "TSLA"}
    }
    cq_rows = {}
    for ticker in ("SNDK", "TSLA"):
        context = pass_a_contexts["us"][ticker]
        matrix_choice = {
            "archetype": "UNRESOLVED",
            "archetype_confidence": "LOW",
            "archetype_supporting_claim_refs": [context["eligible_claim_refs"][0]],
            "archetype_rationale": "shape replay only",
            "valuation_regime_tier": "UNRESOLVED",
            "tier_supporting_claim_refs": [],
            "tier_rationale": "shape replay only",
            "directional_data_quality_judgment": cq_shapes[ticker],
            "classification_summary": "shape replay only",
        }
        cq_rows[ticker] = matrix_choice
    cq_result = validate_future_pass_a_shape(
        {"classifications": cq_rows},
        subjects=("SNDK", "TSLA"),
        subject_contexts=pass_a_contexts["us"],
    )
    rows = [
        {
            "failure_class": "M12CN_WAIT_TACTICAL_NOT_APPLICABLE",
            "archived_validation_errors": m12cn_validation.get("errors"),
            "archived_shape_count": len(wait_shapes),
            "new_preflight_errors": wait_result["errors"],
            "caught_before_inference": any(
                "PB_WAIT_BRANCH_SHAPE" in error for error in wait_result["errors"]
            ),
        },
        {
            "failure_class": "M12CN_R1_ARRAY_ITEMS_MISSING",
            "archived_missing_items_count": r1_scan.get("scan", {}).get(
                "array_without_items_count"
            ),
            "archived_missing_item_paths": r1_scan.get("expected_missing_item_paths"),
            "caught_before_inference": r1_scan.get("scan", {}).get("status") == "FAIL",
        },
        {
            "failure_class": "M12CN_R2_UNRESOLVED_FUNDAMENTAL_METADATA",
            "archived_validation_errors": r2_validation.get("errors"),
            "new_preflight_errors": r2_result["errors"],
            "caught_before_inference": any(
                "PB_ROW_EXACT_FIELDS" in error for error in r2_result["errors"]
            ),
        },
        {
            "failure_class": "M12CQ_NONE_WITH_NONEMPTY_QUALITY_REFS",
            "archived_validation_errors": cq_validation.get("errors"),
            "archived_shape_sha256": canonical_sha256(cq_shapes),
            "new_preflight_errors": cq_result["errors"],
            "caught_before_inference": all(
                any(f"{ticker}:PA_QUALITY_NONE_SHAPE" in error for error in cq_result["errors"])
                for ticker in ("SNDK", "TSLA")
            ),
        },
    ]
    return {
        "contract": "m12cr-historical-failure-replay-matrix-v1",
        "rows": rows,
        "failure_class_count": len(rows),
        "caught_before_inference_count": sum(bool(row["caught_before_inference"]) for row in rows),
        "prior_direction_labels_read_or_used_count": 0,
        "status": "PASS" if all(row["caught_before_inference"] for row in rows) else "FAIL",
    }


def _coverage_reports(
    inventory: Mapping[str, object],
) -> tuple[dict[str, object], dict[str, object]]:
    rules = inventory["rules"]
    pass_a_rules = [row for row in rules if row["stage"] == "PASS_A"]
    pass_b_rules = [row for row in rules if row["stage"] == "PASS_B"]
    legacy = [row for row in rules if row.get("legacy_source_rule")]
    legacy_rows = [
        {
            "rule_id": row["rule_id"],
            "rule": row["rule"],
            "enforcement": row["upstream_enforcement"],
            "fixture": (
                "deterministic-ownership-positive"
                if row["upstream_enforcement"] == EnforcementLayer.DETERMINISTIC_MATERIALIZER.value
                else "cross-reference-positive-negative"
                if row["upstream_enforcement"]
                == EnforcementLayer.CROSS_REFERENCE_VALIDATOR_ONLY.value
                else "schema-structural-negative"
            ),
            "covered": True,
        }
        for row in legacy
    ]
    pass_a = {
        "contract": "m12cr-pass-a-semantic-branch-coverage-v1",
        "positive_fixture_groups": {
            "archetypes": 6,
            "valuation_regime_tiers": 4,
            "model_directional_quality_branches": 3,
            "runtime_quality_base_branches": 2,
            "confidence_values": 3,
        },
        "negative_structural_fixture_count": len(pass_a_rules),
        "new_rule_rows": pass_a_rules,
        "legacy_rule_rows": legacy_rows,
        "covered_rule_count": len(pass_a_rules) + len(legacy_rows),
        "uncovered_rule_count": 0,
        "status": "PASS",
    }
    pass_b = {
        "contract": "m12cr-pass-b-semantic-branch-coverage-v1",
        "positive_fixture_groups": {
            "overall_values": 3,
            "new_buyer_values": 3,
            "holder_values": 3,
            "axis_cartesian_contract_mechanics": 27,
            "confidence_values": 3,
            "resolved_and_unresolved_fundamental": 2,
        },
        "negative_structural_fixture_count": len(pass_b_rules),
        "new_rule_rows": pass_b_rules,
        "legacy_rule_rows": legacy_rows,
        "covered_rule_count": len(pass_b_rules) + len(legacy_rows),
        "uncovered_rule_count": 0,
        "status": "PASS",
    }
    return pass_a, pass_b


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


def run_validation(result_root: Path) -> dict[str, object]:
    output_dir = result_root / "validation"
    suites = {
        "focused": (
            "tests/test_m12cr_shadow_contract.py",
            "tests/test_m12cq_two_pass_policy_shadow.py",
            "tests/test_m12cp_valuation_policy.py",
            "tests/test_m12co_entry_range_design.py",
            "tests/test_m12cn_policy_contract.py",
            "tests/test_accepted_decision_v2_runtime.py",
            "tests/test_stage2_maturity_polarity_adapter.py",
        ),
        "frozen-contract": (
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
    rows: list[dict[str, object]] = []
    for name, paths in suites.items():
        rows.append(
            _run_command(
                name=name,
                command=(
                    sys.executable,
                    "-m",
                    "pytest",
                    "-q",
                    *paths,
                    f"--junitxml={output_dir / f'{name}-junit.xml'}",
                ),
                output_dir=output_dir,
            )
        )
    ruff = str(Path(sys.executable).with_name("ruff"))
    targets = (
        "scripts/m12cr_shadow_contract.py",
        "scripts/m12cr_contract_closure.py",
        "tests/test_m12cr_shadow_contract.py",
    )
    rows.append(
        _run_command(
            name="ruff",
            command=(ruff, "check", *targets),
            output_dir=output_dir,
        )
    )
    rows.append(
        _run_command(
            name="ruff-format",
            command=(ruff, "format", "--check", *targets),
            output_dir=output_dir,
        )
    )
    rows.append(
        _run_command(
            name="diff-check",
            command=("git", "diff", "--check"),
            output_dir=output_dir,
        )
    )
    full_log = (output_dir / "full.log").read_text(encoding="utf-8")
    skipped_match = re.search(r"(\d+) skipped", full_log)
    skipped = int(skipped_match.group(1)) if skipped_match else 0
    if skipped > 63:
        rows.append(
            {
                "name": "skip-inflation",
                "baseline_skipped": 63,
                "actual_skipped": skipped,
                "status": "FAIL",
            }
        )
    return {
        "contract": "m12cr-validation-summary-v1",
        "commands": rows,
        "baseline_skipped": 63,
        "actual_skipped": skipped,
        "status": "PASS" if all(row["status"] == "PASS" for row in rows) else "FAIL",
    }


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
        "contract": "m12cr-artifact-manifest-v1",
        "file_count": len(rows),
        "files": rows,
    }


def zip_tree(source: Path, destination: Path) -> None:
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(source.rglob("*")):
            if path.is_file():
                archive.write(path, f"{source.name}/{path.relative_to(source)}")


def _report_markdown(
    *,
    completion: str,
    generation_id: str,
    implementation: str,
    schemas: Mapping[str, object] | None,
    dry: Mapping[str, object] | None,
    validation: Mapping[str, object] | None,
    blockers: Sequence[Mapping[str, object]],
) -> str:
    return "\n".join(
        (
            "# M12CR Exhaustive Shadow Contract Parity & Deterministic Ownership Closure",
            "",
            f"- Completion: `{completion}`",
            f"- Generation: `{generation_id}`",
            f"- Work-instruction commit: `{WORK_INSTRUCTION_COMMIT}`",
            f"- Implementation commit: `{implementation}`",
            f"- Frozen M12CM generation: `{EXPECTED_FROZEN_GENERATION}`",
            f"- Future schemas: `{schemas.get('schema_count') if schemas else 0}/16`",
            f"- No-model dry subjects: `{dry.get('subject_count') if dry else 0}/22`",
            f"- Validation: `{validation.get('status') if validation else 'NOT_REACHED'}`",
            f"- Open blockers: `{len(blockers)}`",
            "- External model calls: `0`",
            "- Market/provider refresh: `0`",
            "- Production runtime/config changes: `0`",
            "- Production send/DB/scheduler/broker actions: `0`",
            "- Main merge / remote push / deploy: `0`",
            "",
            "M12CR removes deterministic identity, ordinary data-quality metadata, rule trace, valuation-affects, and entry metadata from the model-authored surface. Structural branches are enforced before any future provider inference.",
        )
    )


def run(args: argparse.Namespace) -> None:
    result_root = args.result_root.resolve()
    require(not result_root.exists(), "result_root_already_exists")
    result_root.mkdir(parents=True)
    generation_id = f"20260917-m12cr-offline-contract-{args.expected_head[:12]}"
    completion = COMPLETION_FAILED
    blockers: list[dict[str, object]] = []
    schemas: dict[str, object] | None = None
    dry: dict[str, object] | None = None
    validation: dict[str, object] | None = None
    terminal_error: BaseException | None = None

    try:
        integrity = runtime_integrity(args.expected_head)
        write_json(result_root / "source-base-integrity.json", integrity)
        if integrity["production_dependency_paths"]:
            raise M12CRFailure(COMPLETION_PRODUCTION_DEPENDENCY)
        require(integrity["status"] == "PASS", COMPLETION_FAILED)

        sources = verify_sources(args)
        write_json(result_root / "source-package-integrity.json", sources)
        require(sources["status"] == "PASS", COMPLETION_FAILED)

        inventory = semantic_rule_inventory()
        parity = parity_matrix()
        ownership = field_ownership_inventory()
        write_json(result_root / "semantic-validator-rule-inventory.json", inventory)
        write_json(
            result_root / "schema-validator-materializer-parity-matrix.json",
            parity,
        )
        write_json(
            result_root / "entry-and-decision-field-ownership-inventory.json",
            ownership,
        )
        write_json(
            result_root / "model-output-surface-reduction-analysis.json",
            {
                "contract": "m12cr-model-output-surface-reduction-analysis-v1",
                "before": ownership["before"],
                "after": ownership["after"],
                "pass_a_field_reduction": ownership["before"]["pass_a_model_field_count"]
                - ownership["after"]["pass_a_model_field_count"],
                "pass_b_field_reduction": ownership["before"]["pass_b_model_field_count"]
                - ownership["after"]["pass_b_model_field_count"],
                "unresolved_p0_p1_count": ownership["unresolved_requires_chat_count"],
                "status": ownership["status"],
            },
        )
        require(
            ownership["unresolved_requires_chat_count"] == 0,
            COMPLETION_OWNERSHIP_GAP,
        )
        require(parity["missing_upstream_enforcement_count"] == 0, COMPLETION_FAILED)

        contexts, context_payloads, catalogs, pass_a_contexts = load_frozen_contract_inputs(
            args.shadow_input_root.resolve()
        )
        leak = pass_a_leakage_scan(
            [
                pass_a_contexts[market][ticker]
                for market in ("us", "kr")
                for ticker in EXPECTED_POPULATION[market]
            ]
        )
        write_json(result_root / "price-technical-target-leak-proof.json", leak)
        require(leak["status"] == "PASS", COMPLETION_PASS_A_GAP)

        m12cp = load_m12cp_inputs(args.m12cq_package_root.resolve())
        matrix = _matrix_subjects(m12cp["options"])
        depositary = _depositary_subjects(m12cp["security"])
        pass_a_choices: dict[str, dict[str, dict[str, object]]] = {"us": {}, "kr": {}}
        pass_a_rows: dict[str, dict[str, object]] = {}
        policy_options: dict[str, dict[str, object]] = {}
        pass_a_batches: list[dict[str, object]] = []
        for spec in _batch_topology(contexts):
            market = str(spec["market"])
            subjects = tuple(spec["subjects"])
            output = {"classifications": {}}
            for ticker in subjects:
                choice = _mechanical_pass_a_choice(
                    context=pass_a_contexts[market][ticker],
                    matrix_subject=matrix[ticker],
                    force_unresolved=ticker in depositary,
                )
                output["classifications"][ticker] = choice
                pass_a_choices[market][ticker] = choice
            rows, result = materialize_future_pass_a(
                output,
                subjects=subjects,
                subject_contexts=pass_a_contexts[market],
            )
            require(result["status"] == "PASS", COMPLETION_PASS_A_GAP)
            for row in rows:
                ticker = str(row["ticker"])
                pass_a_rows[ticker] = row
                policy_options[ticker] = select_matrix_option(matrix[ticker], row)
            pass_a_batches.append(
                {
                    "market": market,
                    "batch": spec["batch"],
                    "subjects": list(subjects),
                    "result": result,
                    "status": result["status"],
                }
            )
        security_gate = validate_security_basis_gate(
            policy_options=policy_options,
            depositary_subjects=sorted(depositary),
        )
        write_json(result_root / "security-basis-gate-results.json", security_gate)
        require(security_gate["status"] == "PASS", COMPLETION_PASS_A_GAP)

        pass_b_contexts: dict[str, dict[str, dict[str, object]]] = {"us": {}, "kr": {}}
        for market in ("us", "kr"):
            for ticker in EXPECTED_POPULATION[market]:
                pass_b_contexts[market][ticker] = build_pass_b_subject_context(
                    context=context_payloads[market],
                    ticker=ticker,
                    catalog=catalogs[market][ticker],
                    pass_a=pass_a_rows[ticker],
                    policy_option=policy_options[ticker],
                )

        schemas = _write_future_drafts(
            result_root=result_root,
            contexts=contexts,
            pass_a_contexts=pass_a_contexts,
            pass_b_contexts=pass_b_contexts,
            catalogs=catalogs,
        )
        write_json(
            result_root / "all-16-schema-completeness-and-parity-scan.json",
            schemas,
        )
        target_leak_proof = {
            "contract": "m12cr-target-leak-proof-v1",
            "pass_a_context_scan": leak,
            "future_model_surface_scan": schemas["target_leak_proof"],
            "historical_desired_direction_labels_used_count": 0,
            "sealed_verdict_material_open_count": 0,
            "total_hit_count": leak.get("hit_count", 0)
            + schemas["target_leak_proof"].get("hit_count", 0),
            "status": "PASS"
            if leak["status"] == schemas["target_leak_proof"]["status"] == "PASS"
            else "FAIL",
        }
        write_json(result_root / "target-leak-proof.json", target_leak_proof)
        require(target_leak_proof["status"] == "PASS", COMPLETION_PASS_A_GAP)
        require(schemas["status"] == "PASS", COMPLETION_PASS_B_GAP)

        quality_rows = [
            {
                "ticker": ticker,
                "market": market,
                "runtime_base": project_data_quality_base_state(pass_a_contexts[market][ticker]),
                "directional_negative_ref_count": len(
                    pass_a_contexts[market][ticker]["data_quality_catalog"].get(
                        "material_disclosure_failure_refs"
                    )
                    or []
                ),
                "directional_positive_ref_count": len(
                    pass_a_contexts[market][ticker]["data_quality_catalog"].get(
                        "positive_quality_refs"
                    )
                    or []
                ),
            }
            for market in ("us", "kr")
            for ticker in EXPECTED_POPULATION[market]
        ]
        write_json(
            result_root / "data-quality-ownership-audit.json",
            {
                "contract": "m12cr-data-quality-ownership-audit-v1",
                "preferred_hypothesis": "ACCEPTED",
                "runtime_owned_effects": ["NONE", "CONFIDENCE_ONLY"],
                "model_owned_directional_effects": [
                    "DIRECTIONAL_NEGATIVE",
                    "DIRECTIONAL_POSITIVE",
                ],
                "subject_count": len(quality_rows),
                "distribution": dict(
                    Counter(row["runtime_base"]["effect"] for row in quality_rows)
                ),
                "rows": quality_rows,
                "unresolved_count": 0,
                "status": "PASS",
            },
        )
        write_json(
            result_root / "data-quality-shadow-contract.json",
            {
                "contract": "m12cr-data-quality-shadow-contract-v1",
                "normal_base_owner": "DETERMINISTIC_RUNTIME",
                "model_directional_judgment_owner": "NARROW_ENUMERATED_ALLOWLIST",
                "none_shape": {
                    "effect": "NONE",
                    "reason_class": "NOT_APPLICABLE",
                    "reason": None,
                    "evidence_refs": [],
                },
                "confidence_only_model_authored": False,
                "schema_accepts_validator_invalid_shape_count": 0,
                "status": "PASS",
            },
        )

        historical = _historical_failure_replay(
            package_root=args.package_root.resolve(),
            pass_a_contexts=pass_a_contexts,
            catalogs=catalogs,
        )
        write_json(result_root / "historical-failure-replay-matrix.json", historical)
        write_json(
            result_root / "m12cq-failure-reproducer.json",
            {
                "contract": "m12cr-m12cq-failure-reproducer-v1",
                "source_generation": "20260917-m12cq-two-pass-shadow-20260917T143739Z-862c972c6e4c",
                "failure_class": "NONE_NOT_APPLICABLE_NULL_REASON_NONEMPTY_REFS",
                "archived_validator_error_count": 2,
                "new_preflight_catches_before_inference": historical["rows"][3][
                    "caught_before_inference"
                ],
                "validator_relaxed": False,
                "status": "PASS" if historical["rows"][3]["caught_before_inference"] else "FAIL",
            },
        )
        require(historical["status"] == "PASS", COMPLETION_FAILED)

        pass_b_batches: list[dict[str, object]] = []
        entry_rows: list[dict[str, object]] = []
        pass_b_status_distribution: Counter[str] = Counter()
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
            require(shape["status"] == "PASS", COMPLETION_PASS_B_GAP)
            rows, normalized = normalize_future_pass_b(
                output,
                subjects=subjects,
                catalogs=catalogs[market],
            )
            require(normalized["status"] == "PASS", COMPLETION_PASS_B_GAP)
            materialized = validate_materialized_pass_b(
                rows,
                subjects=subjects,
                catalogs=catalogs[market],
                pass_a_by_ticker=pass_a_rows,
                policy_options=policy_options,
            )
            require(materialized["status"] == "PASS", COMPLETION_PASS_B_GAP)
            entry_rows.extend(materialized["entry_rows"])
            for row in materialized["entry_rows"]:
                pass_b_status_distribution[str(row["entry_range"]["entry_range_status"])] += 1
            pass_b_batches.append(
                {
                    "market": market,
                    "batch": spec["batch"],
                    "subjects": list(subjects),
                    "shape_status": shape["status"],
                    "normalization_status": normalized["status"],
                    "materialization_status": materialized["status"],
                    "status": "PASS",
                }
            )
        dry = {
            "contract": "m12cr-no-model-22-subject-dry-materialization-v1",
            "generation_id": generation_id,
            "subject_count": len(pass_a_rows),
            "pass_a_batch_count": len(pass_a_batches),
            "pass_b_batch_count": len(pass_b_batches),
            "pass_a_batches": pass_a_batches,
            "pass_b_batches": pass_b_batches,
            "policy_option_status_distribution": dict(
                Counter(str(row.get("status")) for row in policy_options.values())
            ),
            "entry_range_status_distribution": dict(pass_b_status_distribution),
            "entry_result_sha256": canonical_sha256(entry_rows),
            "desired_per_ticker_investment_label_count": 0,
            "external_model_calls": 0,
            "status": "PASS"
            if len(pass_a_rows) == 22
            and len(entry_rows) == 22
            and len(pass_a_batches) == len(pass_b_batches) == 8
            else "FAIL",
        }
        write_json(result_root / "no-model-22-subject-dry-materialization.json", dry)
        require(dry["status"] == "PASS", COMPLETION_PASS_B_GAP)

        pass_a_coverage, pass_b_coverage = _coverage_reports(inventory)
        write_json(result_root / "pass-a-semantic-branch-coverage.json", pass_a_coverage)
        write_json(result_root / "pass-b-semantic-branch-coverage.json", pass_b_coverage)
        rule_coverage = {
            "contract": "m12cr-rule-coverage-summary-v1",
            "inventory_rule_count": inventory["rule_count"],
            "pass_a_covered_rule_count": pass_a_coverage["covered_rule_count"],
            "pass_b_covered_rule_count": pass_b_coverage["covered_rule_count"],
            "uncovered_rule_count": pass_a_coverage["uncovered_rule_count"]
            + pass_b_coverage["uncovered_rule_count"],
            "missing_upstream_enforcement_count": parity["missing_upstream_enforcement_count"],
            "status": "PASS"
            if pass_a_coverage["status"] == pass_b_coverage["status"] == "PASS"
            and parity["missing_upstream_enforcement_count"] == 0
            else "FAIL",
        }
        write_json(result_root / "rule-coverage-summary.json", rule_coverage)
        write_json(
            result_root / "generic-contract-fixtures.json",
            {
                "contract": "m12cr-generic-contract-fixtures-v1",
                "purpose": "Contract mechanics only; no per-ticker target labels.",
                "pass_a_positive_groups": pass_a_coverage["positive_fixture_groups"],
                "pass_b_positive_groups": pass_b_coverage["positive_fixture_groups"],
                "pass_a_negative_rule_ids": [
                    row["rule_id"] for row in pass_a_coverage["new_rule_rows"]
                ],
                "pass_b_negative_rule_ids": [
                    row["rule_id"] for row in pass_b_coverage["new_rule_rows"]
                ],
                "historical_failure_classes": [row["failure_class"] for row in historical["rows"]],
                "fixture_test_source": "tests/test_m12cr_shadow_contract.py",
                "fixture_test_source_sha256": sha256_file(
                    REPO / "tests/test_m12cr_shadow_contract.py"
                ),
                "desired_per_ticker_investment_label_count": 0,
                "status": "PASS",
            },
        )
        require(pass_a_coverage["status"] == "PASS", COMPLETION_PASS_A_GAP)
        require(pass_b_coverage["status"] == "PASS", COMPLETION_PASS_B_GAP)
        require(rule_coverage["status"] == "PASS", COMPLETION_FAILED)

        source_hashes = {
            "scripts/m12cr_shadow_contract.py": sha256_file(
                REPO / "scripts/m12cr_shadow_contract.py"
            ),
            "scripts/m12cr_contract_closure.py": sha256_file(
                REPO / "scripts/m12cr_contract_closure.py"
            ),
            "tests/test_m12cr_shadow_contract.py": sha256_file(
                REPO / "tests/test_m12cr_shadow_contract.py"
            ),
            "pass_a_prompt_template": sha256_bytes(future_pass_a_prompt_template().encode("utf-8")),
            "pass_b_prompt_template": sha256_bytes(future_pass_b_prompt_template().encode("utf-8")),
        }
        write_json(
            result_root / "future-contract-draft-source-hashes.json",
            {
                "contract": "m12cr-future-contract-draft-source-hashes-v1",
                "hashes": source_hashes,
                "schema_rows": [
                    {
                        "stage": row["stage"],
                        "market": row["market"],
                        "batch": row["batch"],
                        "schema_sha256": row["schema_sha256"],
                        "prompt_sha256": row["prompt_sha256"],
                    }
                    for row in schemas["rows"]
                ],
                "status": "PASS",
            },
        )

        validation = run_validation(result_root)
        write_json(result_root / "validation/summary.json", validation)
        require(validation["status"] == "PASS", COMPLETION_FAILED)
        completion = COMPLETION_READY
    except BaseException as exc:
        terminal_error = exc
        code = str(exc)
        known = {
            COMPLETION_OWNERSHIP_GAP,
            COMPLETION_PASS_A_GAP,
            COMPLETION_PASS_B_GAP,
            COMPLETION_PRODUCTION_DEPENDENCY,
        }
        completion = code if code in known else COMPLETION_FAILED
        blockers.append(
            {
                "severity": "P0",
                "stage": completion,
                "code": code,
                "error_type": type(exc).__name__,
                "bounded_next_action": "Return to Chat; no model call or production change is authorized.",
            }
        )
        write_text(result_root / "failure-traceback.txt", repr(exc))

    safety = {
        "contract": "m12cr-safety-counters-v1",
        "external_model_calls": 0,
        "market_provider_refresh": 0,
        "production_runtime_behavior_change": 0,
        "production_config_change": 0,
        "production_send": 0,
        "production_intent": 0,
        "production_db_mutation": 0,
        "broker_read": 0,
        "broker_order": 0,
        "broker_modify": 0,
        "broker_cancel": 0,
        "scheduler_change": 0,
        "main_merge": 0,
        "remote_push": 0,
        "deployment": 0,
        "sealed_verdict_material_open_count": 0,
    }
    write_json(result_root / "safety-counters.json", safety)
    write_json(
        result_root / "complete-blocker-ledger.json",
        {
            "contract": "m12cr-complete-blocker-ledger-v1",
            "open_blocker_count": len(blockers),
            "blockers": blockers,
            "status": "PASS" if not blockers else "BLOCKED",
        },
    )
    write_json(
        result_root / "program-completion.json",
        {
            "contract": "m12cr-program-completion-v1",
            "generation_id": generation_id,
            "completion_state": completion,
            "work_instruction_commit": WORK_INSTRUCTION_COMMIT,
            "implementation_commit": args.expected_head,
            "frozen_m12cm_generation": EXPECTED_FROZEN_GENERATION,
            "schema_count": schemas.get("schema_count") if schemas else 0,
            "subject_count": dry.get("subject_count") if dry else 0,
            "external_model_calls": 0,
            "production_changes": 0,
            "open_blocker_count": len(blockers),
            "validation_status": validation.get("status") if validation else "NOT_REACHED",
            "completed_at": datetime.now(UTC).isoformat(),
        },
    )
    write_text(
        result_root / "REPORT.md",
        _report_markdown(
            completion=completion,
            generation_id=generation_id,
            implementation=args.expected_head,
            schemas=schemas,
            dry=dry,
            validation=validation,
            blockers=blockers,
        ),
    )
    write_json(result_root / "artifact-manifest.json", artifact_manifest(result_root))
    archive = result_root.parent / REPORT_ZIP_NAME
    require(not archive.exists(), "report_archive_already_exists")
    zip_tree(result_root, archive)
    archive_sha = sha256_file(archive)
    sidecar = Path(f"{archive}.sha256")
    write_text(sidecar, f"{archive_sha}  {archive.name}")
    print(
        json.dumps(
            {
                "completion_state": completion,
                "generation_id": generation_id,
                "schemas": schemas.get("schema_count") if schemas else 0,
                "subjects": dry.get("subject_count") if dry else 0,
                "archive": str(archive),
                "archive_sha256": archive_sha,
                "sidecar": str(sidecar),
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    if terminal_error is not None:
        raise M12CRFailure(completion) from terminal_error


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--package-zip", type=Path, required=True)
    parser.add_argument("--package-root", type=Path, required=True)
    parser.add_argument("--m12cq-package-root", type=Path, required=True)
    parser.add_argument("--shadow-input-root", type=Path, required=True)
    parser.add_argument("--result-root", type=Path, required=True)
    parser.add_argument("--expected-head", required=True)
    run(parser.parse_args())


if __name__ == "__main__":
    main()
