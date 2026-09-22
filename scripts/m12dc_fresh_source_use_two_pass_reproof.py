from __future__ import annotations

import argparse
import ast
import hashlib
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
from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from scripts import m12db_model_view_readiness as m12db
from scripts import m12db_r1_request_composition_closure as m12db_r1
from scripts.m12cn_policy_shadow import classify_shadow_failure
from scripts.m12cq_two_pass_contract import (
    PassABatchOutput,
    PassBBatchOutput,
    build_pass_a_subject_context,
    build_pass_b_subject_context,
    canonical_sha256,
    pass_a_leakage_scan,
    select_matrix_option,
    validate_new_buyer_consistency,
    validate_pass_a_batch,
    validate_pass_b_batch,
)
from scripts.m12cr_contract_closure import _matrix_subjects
from scripts.m12cr_r1_typed_quality_contract import (
    build_r1_pass_a_context,
    gate_policy_option_for_security_basis,
    validate_quality_basis_decision_ownership,
    validate_security_valuation_basis_gate,
)
from scripts.m12cr_shadow_contract import (
    future_pass_a_batch_schema,
    future_pass_a_prompt_template,
    materialize_future_pass_a,
    normalize_future_pass_b,
    schema_completeness_and_parity_scan,
    validate_future_pass_b_shape,
    validate_materialized_pass_b,
)
from scripts.m12cs_fresh_two_pass_shadow import pass_a_output_leak_scan
from scripts.m12cs_r1_provider_schema import (
    project_provider_wire_schema,
    scan_provider_structured_output_schema,
)
from scripts.m12cv_pass_b_capability_contract import (
    build_pass_b_capability_catalog,
    capability_pass_b_batch_schema,
    capability_prompt_template,
    validate_capability_selection,
)
from scripts.m12da_source_use_contract import (
    build_source_use_projection,
    freeze_source_use_binding,
    freeze_source_use_input_expectation,
    SourceUse,
    validate_selected_refs,
    validate_source_use_current_input,
)
from scripts.websocket_timeout_runtime_review_first_a_closeout import validate_json_schema


REPO = Path(__file__).resolve().parents[1]
KST = ZoneInfo("Asia/Seoul")
MODEL = "gpt-5.6-sol"
EFFORT = "xhigh"
TIMEOUT_SECONDS = 1_200
BASE_IMPLEMENTATION = "793c48416653c738e2e44c57c66bb7f09c0cbb28"
BASELINE_EXECUTION_GENERATION = "20260919-m12db-request-preparation-no-inference"
ASSESSMENT_DATE = "2026-09-19"
EXPECTED_CLI_VERSION = "codex-cli 0.153.4"
EXPECTED_M12CP_SHA256 = "fe63ee201bdb0937a4936af0d89f7013adee0209b3ef01d83d210d0e93456100"
EXPECTED_HISTORICAL_COMBINED_SHA256 = (
    "34aace744021cc0b4b150dcd47e9c31bb2f48d8ec4a136cc4123c4de64646f4c"
)
EXPECTED_CRCL_RAW_SHA256 = "82d56065367b7aa07251d04b1fef86d0c7bbcc93afeb6a089ac317c6718d3035"

PASS = "M12DC_FRESH_SOURCE_USE_TWO_PASS_CALIBRATION_PASS_READY_FOR_CHAT_REVIEW"
PREINFERENCE_BLOCKED = "M12DC_PREINFERENCE_BINDING_OR_EXECUTION_PATH_BLOCKED"
PASS_A_FAILED = "M12DC_PASS_A_FAILED"
POST_A_BLOCKED = "M12DC_POST_A_MATERIALIZATION_OR_B_CAPABILITY_BLOCKED"
PASS_B_FAILED = "M12DC_PASS_B_FAILED"
POSTRUN_INCOMPLETE = "M12DC_ANALYTICAL_PASS_POSTRUN_VALIDATION_INCOMPLETE"
SOURCE_DRIFT = "M12DC_SOURCE_OR_POLICY_DRIFT_REQUIRES_CHAT"
SAFETY_FAILURE = "M12DC_SAFETY_OR_REFERENCE_CONTAMINATION_FAILURE"

R1_MODE = "PASS_B_ONLY_REPROOF_WITH_FROZEN_FRESH_M12DC_PASS_A"
UPSTREAM_HEAD = "3e1bdeab6176f6e6996f4e389529d4a7034f9b46"
UPSTREAM_GENERATION = "20260919-m12dc-fresh-source-use-two-pass-20260919T074953Z-3e1bdeab"
UPSTREAM_FILES = {
    "pass-a-22-subject-classification.json": "30d094b9b90f9a687162db4db8562dd619068ed03de6f8b316e62c66b92e8a9b",
    "pass-a-output-freeze-manifest.json": "834af664114a43ee8c2cd6441f9f9a16c5c54c8b85f6e1f0eed84b24be013d07",
    "fresh-deterministic-fundamental-options-22.json": "93e56b1bb701f488b48d4338101b826e653962d81e581e7e62911ed205bd4f8b",
}

REPORT_NAME = (
    "thesis-monitor-20260919-m12dc-fresh-source-use-aware-two-pass-calibration-reproof-report.zip"
)

CODE_PATHS = (
    "scripts/m12dc_fresh_source_use_two_pass_reproof.py",
    "scripts/m12db_model_view_readiness.py",
    "scripts/m12db_r1_request_composition_closure.py",
    "scripts/m12da_source_use_contract.py",
    "scripts/m12cv_pass_b_capability_contract.py",
    "scripts/m12cs_r1_provider_schema.py",
    "scripts/m12cr_r1_typed_quality_contract.py",
    "scripts/m12cr_shadow_contract.py",
    "scripts/m12cq_two_pass_contract.py",
    "app/jobs/accepted_decision_v2_runtime.py",
    "app/services/accepted_decision_v2_runtime_service.py",
    "scripts/websocket_timeout_runtime_review_first_a_closeout.py",
)

BASE_SOURCE_HASHES = {
    "scripts/m12db_model_view_readiness.py": (
        "a1a492a15ac973e856717c12b35e314505c19eff9c431efec8d2942ed381edb9"
    ),
    "scripts/m12db_r1_request_composition_closure.py": (
        "c839e1f0d7d13ca52631069d6ada4a5689928277d2ea00b3fa81095474dd691f"
    ),
    "tests/test_m12db_r1_request_composition_closure.py": (
        "3997559db4a87a8fba61e044aa63fdb9c32e4b724509e5d5147dd34a5c7c1d61"
    ),
}

RUNTIME_EXCLUSIONS = {
    "source_use_projection": (
        "binding_sha256",
        "current_input_expectation_sha256",
        "execution_generation_id",
        "model_permission_view_sha256",
        "projection_sha256",
    ),
    "source_evidence_binding": (
        "actual_final_view_sha256",
        "expected_final_view_sha256",
        "intermediate_receipt_sha256",
        "model_permission_view_sha256",
        "source_use_binding_sha256",
    ),
}


class M12DCFailure(RuntimeError):
    pass


def require(condition: bool, code: str) -> None:
    if not condition:
        raise M12DCFailure(code)


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise M12DCFailure(f"expected_json_object:{path}")
    return value


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value.rstrip() + "\n", encoding="utf-8")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _git(*args: str) -> str:
    return subprocess.run(
        ("git", *args),
        cwd=REPO,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _batch_topology() -> list[dict[str, object]]:
    return m12db._batch_topology()


def _expected_tickers() -> list[str]:
    return list(m12db.POPULATION["us"] + m12db.POPULATION["kr"])


def _manifest_verification(root: Path, expected_count: int) -> dict[str, object]:
    return m12db._manifest_verification(root, expected_count=expected_count)


def _verify_package_manifest(package_root: Path) -> dict[str, object]:
    manifest = read_json(package_root / "package-manifest.json")
    rows: list[dict[str, object]] = []
    for item in manifest.get("files") or ():
        path = package_root / str(item["path"])
        actual_sha = sha256_file(path) if path.is_file() else None
        actual_size = path.stat().st_size if path.is_file() else None
        status = (
            "PASS"
            if actual_sha == item.get("sha256") and actual_size == item.get("size")
            else "FAIL"
        )
        rows.append(
            {
                "path": item["path"],
                "actual_sha256": actual_sha,
                "actual_size": actual_size,
                "status": status,
            }
        )
    return {
        "contract": "m12dc-package-verification-v1",
        "payload_count": len(rows),
        "rows": rows,
        "status": "PASS"
        if len(rows) == 23 and all(row["status"] == "PASS" for row in rows)
        else "FAIL",
    }


def _verify_source_archives(args: argparse.Namespace) -> dict[str, object]:
    source_index = read_json(args.package_root / "source-index.json")
    rows: list[dict[str, object]] = []
    for item in source_index["sources"]:
        path = args.package_root / str(item["path"])
        actual = sha256_file(path)
        rows.append(
            {
                "path": item["path"],
                "expected_sha256": item["sha256"],
                "actual_sha256": actual,
                "size": path.stat().st_size,
                "status": "PASS" if actual == item["sha256"] else "FAIL",
            }
        )
    manifests = {
        "m12db_r1_outer": _manifest_verification(args.m12db_r1_root, 198),
        "m12db_r1_nested": _manifest_verification(
            args.m12db_r1_root / "actual-caller-capture", 184
        ),
        "m12da_r3": _manifest_verification(args.r3_root, 47),
        "m12cx": _manifest_verification(args.m12cx_root, 239),
        "m12cx_supplemental": _manifest_verification(args.supplemental_root, 90),
        "m12cu": _manifest_verification(args.m12cu_root, 347),
    }
    base_hash_rows = [
        {
            "path": path,
            "expected_sha256": expected,
            "actual_sha256": sha256_file(REPO / path),
            "status": "PASS" if sha256_file(REPO / path) == expected else "FAIL",
        }
        for path, expected in BASE_SOURCE_HASHES.items()
    ]
    m12cp_sha = sha256_file(args.m12cp_zip)
    combined = (
        args.supplemental_root
        / "cross-run-offline-validation/combined-fresh-a-m12cx-b-22-subject-results.json"
    )
    crcl_raw = args.m12cu_root / "model-calls/pass-b/us/batch-01/raw-output.json"
    checks = {
        "m12cp_sha256": m12cp_sha,
        "m12cp_status": "PASS" if m12cp_sha == EXPECTED_M12CP_SHA256 else "FAIL",
        "historical_combined_sha256": sha256_file(combined),
        "historical_combined_status": (
            "PASS" if sha256_file(combined) == EXPECTED_HISTORICAL_COMBINED_SHA256 else "FAIL"
        ),
        "crcl_raw_sha256": sha256_file(crcl_raw),
        "crcl_raw_status": (
            "PASS" if sha256_file(crcl_raw) == EXPECTED_CRCL_RAW_SHA256 else "FAIL"
        ),
    }
    status = (
        all(row["status"] == "PASS" for row in rows + base_hash_rows)
        and all(row["status"] == "PASS" for row in manifests.values())
        and all(value == "PASS" for key, value in checks.items() if key.endswith("_status"))
    )
    return {
        "contract": "m12dc-finite-source-integrity-v1",
        "archives": rows,
        "extracted_manifests": manifests,
        "base_source_hashes": base_hash_rows,
        "checks": checks,
        "known_packaging_metadata": {
            "m12db_r1_macosx_files": 225,
            "outer_manifest_excludes_nested_manifest": True,
            "runtime_loader_ignores_macosx": True,
        },
        "status": "PASS" if status else "FAIL",
    }


def _runtime_integrity(args: argparse.Namespace) -> dict[str, object]:
    head = _git("rev-parse", "HEAD")
    base = _git("rev-parse", f"{BASE_IMPLEMENTATION}^{{commit}}")
    instruction = _git("rev-parse", f"{args.work_instruction_commit}^{{commit}}")
    changed = _git("diff", "--name-only", f"{BASE_IMPLEMENTATION}..{head}").splitlines()
    allowed = {
        "docs/work-instructions/20260919-m12dc-fresh-source-use-aware-two-pass-calibration-reproof.md",
        "scripts/m12dc_fresh_source_use_two_pass_reproof.py",
        "tests/test_m12dc_fresh_source_use_two_pass_reproof.py",
    }
    if getattr(args, "frozen_a_root", None):
        allowed.update(
            {
                "docs/work-instructions/20260919-m12dc-r1-pass-b-decisive-ref-schema-parity-and-frozen-a-reproof.md",
                "scripts/m12cv_pass_b_capability_contract.py",
                "tests/test_m12cv_pass_b_capability_contract.py",
            }
        )
    errors: list[str] = []
    if head != args.expected_head:
        errors.append("head_mismatch")
    if base != BASE_IMPLEMENTATION:
        errors.append("base_implementation_mismatch")
    if instruction != args.work_instruction_commit:
        errors.append("instruction_commit_resolution_mismatch")
    if subprocess.run(
        ("git", "merge-base", "--is-ancestor", BASE_IMPLEMENTATION, head), cwd=REPO
    ).returncode:
        errors.append("base_not_ancestor")
    if subprocess.run(
        ("git", "merge-base", "--is-ancestor", args.work_instruction_commit, head), cwd=REPO
    ).returncode:
        errors.append("instruction_not_ancestor")
    unexpected = sorted(set(changed) - allowed)
    if unexpected:
        errors.append("unexpected_changed_paths")
    if _git("status", "--porcelain"):
        errors.append("worktree_not_clean")
    return {
        "contract": "m12dc-runtime-integrity-v1",
        "head": head,
        "expected_head": args.expected_head,
        "base_implementation": base,
        "work_instruction_commit": instruction,
        "changed_paths": changed,
        "unexpected_changed_paths": unexpected,
        "remote_push": False,
        "main_merge": False,
        "deployment": False,
        "errors": errors,
        "status": "PASS" if not errors else "FAIL",
    }


def _source_chains(
    *,
    subjects: Mapping[str, Mapping[str, object]],
    catalogs: Mapping[str, Mapping[str, object]],
    r3_root: Path,
    generation_id: str,
) -> dict[str, dict[str, object]]:
    authorities = read_json(r3_root / "source-authority-manifests-22.json")["subjects"]
    old_expectations = read_json(r3_root / "source-use-input-expectations-22.json")["subjects"]
    old_projections = read_json(r3_root / "source-use-projections-22.json")["subjects"]
    old_bindings = read_json(r3_root / "source-use-bindings-22.json")["subjects"]
    chains: dict[str, dict[str, object]] = {}
    for ticker in _expected_tickers():
        metadata = list(subjects[ticker].get("decision_evidence") or ())
        authority = authorities[ticker]
        source_generation = str(authority["source_generation_id"])
        expectation = freeze_source_use_input_expectation(
            ticker=ticker,
            source_generation_id=source_generation,
            execution_generation_id=generation_id,
            catalog=catalogs[ticker],
            source_metadata=metadata,
            authority_manifest=authority,
        )
        projection = build_source_use_projection(
            ticker=ticker,
            input_generation_id=source_generation,
            execution_generation_id=generation_id,
            catalog=catalogs[ticker],
            authority_manifest=authority,
            current_input_expectation=expectation,
        )
        binding = freeze_source_use_binding(
            projection=projection,
            authority_manifest=authority,
            current_input_expectation=expectation,
        )
        validation = validate_source_use_current_input(
            projection,
            binding,
            expectation,
            ticker=ticker,
            source_generation_id=source_generation,
            execution_generation_id=generation_id,
            catalog=catalogs[ticker],
            source_metadata=metadata,
        )
        require(validation["status"] == "PASS", f"source_binding_failed:{ticker}")
        old_expectation = old_expectations[ticker]
        old_projection = old_projections[ticker]
        old_binding = old_bindings[ticker]
        chains[ticker] = {
            "authority": authority,
            "expectation": expectation,
            "projection": projection,
            "binding": binding,
            "validation": validation,
            "source_generation_id": source_generation,
            "execution_generation_id": generation_id,
            "source_identity_unchanged": (
                expectation["source_metadata_sha256"] == old_expectation["source_metadata_sha256"]
                and expectation["catalog_sha256"] == old_expectation["catalog_sha256"]
                and expectation["authority_manifest_sha256"]
                == old_expectation["authority_manifest_sha256"]
            ),
            "permission_semantics_unchanged": (
                projection["permission_derivation_sha256"]
                == old_projection["permission_derivation_sha256"]
            ),
            "execution_binding_rebased": (
                projection["projection_sha256"] != old_projection["projection_sha256"]
                and binding["binding_sha256"] != old_binding["binding_sha256"]
            ),
        }
    return chains


def _build_pass_a_contexts(
    *,
    subjects: Mapping[str, Mapping[str, object]],
    catalogs: Mapping[str, Mapping[str, object]],
    chains: Mapping[str, Mapping[str, object]],
    generation_id: str,
) -> tuple[dict[str, dict[str, object]], dict[str, dict[str, object]]]:
    contexts: dict[str, dict[str, object]] = {}
    source_contexts: dict[str, dict[str, object]] = {}
    for ticker in _expected_tickers():
        chain = chains[ticker]
        source_context = m12db._source_context(ticker, subjects[ticker])
        source_contexts[ticker] = source_context
        intermediate = build_pass_a_subject_context(
            context=source_context,
            ticker=ticker,
            catalog=catalogs[ticker],
            source_use_view=chain["projection"],
            source_use_binding=chain["binding"],
            source_use_expectation=chain["expectation"],
            source_generation_id=str(chain["source_generation_id"]),
            execution_generation_id=generation_id,
            require_source_use=True,
        )
        filtered = build_r1_pass_a_context(intermediate, source_packet=subjects[ticker])
        contexts[ticker] = m12db.bind_final_pass_a_model_view(
            intermediate_context=intermediate,
            final_context=filtered,
            source_packet=subjects[ticker],
        )
    return contexts, source_contexts


def _load_baseline_a_contexts(root: Path) -> dict[str, dict[str, object]]:
    rows: dict[str, dict[str, object]] = {}
    for spec in _batch_topology():
        market = str(spec["market"])
        batch = int(spec["batch"])
        payload = read_json(
            root
            / "actual-caller-capture/pass-a-inputs"
            / market
            / f"batch-{batch:02d}"
            / "subject-context.json"
        )
        for row in payload["subjects"]:
            rows[str(row["ticker"])] = row
    return rows


def _substantive_a_view(context: Mapping[str, object]) -> dict[str, object]:
    value = deepcopy(dict(context))
    for section, keys in RUNTIME_EXCLUSIONS.items():
        payload = value.get(section)
        if isinstance(payload, dict):
            for key in keys:
                payload.pop(key, None)
    return value


def _a_semantic_parity(
    current: Mapping[str, Mapping[str, object]],
    baseline: Mapping[str, Mapping[str, object]],
) -> dict[str, object]:
    rows = []
    for ticker in _expected_tickers():
        current_hash = canonical_sha256(_substantive_a_view(current[ticker]))
        baseline_hash = canonical_sha256(_substantive_a_view(baseline[ticker]))
        rows.append(
            {
                "ticker": ticker,
                "current_substantive_sha256": current_hash,
                "baseline_substantive_sha256": baseline_hash,
                "status": "PASS" if current_hash == baseline_hash else "FAIL",
            }
        )
    return {
        "contract": "m12dc-pass-a-substantive-semantic-parity-v1",
        "excluded_runtime_fields": RUNTIME_EXCLUSIONS,
        "subject_count": len(rows),
        "rows": rows,
        "status": "PASS" if all(row["status"] == "PASS" for row in rows) else "FAIL",
    }


def _request_capture(
    *,
    root: Path,
    stage: str,
    market: str,
    batch: int,
    subjects: Sequence[str],
    contexts: Mapping[str, Mapping[str, object]],
    catalogs: Mapping[str, Mapping[str, object]],
    chains: Mapping[str, Mapping[str, object]],
    generation_id: str,
    fixture_only: bool,
    capabilities: Mapping[str, Mapping[str, object]] | None = None,
    raw_source_metadata_by_ticker: Mapping[str, Sequence[Mapping[str, object]]] | None = None,
) -> dict[str, object]:
    directory = root / stage / market / f"batch-{batch:02d}"
    require(not directory.exists(), "request_directory_already_frozen")
    payloads = [contexts[ticker] for ticker in subjects]
    if stage == "pass-a":
        require(capabilities is None, "pass_a_capability_not_expected")
        internal_schema = future_pass_a_batch_schema(
            subjects=subjects,
            subject_contexts=contexts,
            source_use_inputs={ticker: {
                "catalog": catalogs[ticker], "chain": chains[ticker],
                "source_metadata": raw_source_metadata_by_ticker[ticker],
                "source_generation_id": chains[ticker]["source_generation_id"],
                "execution_generation_id": generation_id,
            } for ticker in subjects} if raw_source_metadata_by_ticker is not None else None,
        )
        prompt_template = future_pass_a_prompt_template()
        ref_catalog = {
            ticker: {
                "eligible_claim_refs": contexts[ticker]["eligible_claim_refs"],
                "premium_eligible_claim_refs": contexts[ticker]["premium_eligible_claim_refs"],
                "data_quality_catalog": contexts[ticker]["data_quality_catalog"],
            }
            for ticker in subjects
        }
    else:
        require(capabilities is not None, "pass_b_capability_required")
        for ticker in subjects:
            require(
                canonical_sha256(contexts[ticker].get("pass_b_capability_catalog"))
                == canonical_sha256(capabilities[ticker]),
                f"pass_b_context_capability_mismatch:{ticker}",
            )
            require(
                capabilities[ticker].get("source_use_required") is True,
                f"pass_b_source_use_required:{ticker}",
            )
            if capabilities[ticker].get("source_use_required"):
                chain = chains[ticker]
                require(raw_source_metadata_by_ticker is not None, "pass_b_raw_source_required")
                trusted = build_pass_b_capability_catalog(
                    context=contexts[ticker],
                    catalog=catalogs[ticker],
                    pass_a=contexts[ticker]["frozen_pass_a_classification"],
                    policy_option=contexts[ticker]["deterministic_fundamental_option"],
                    source_use_view=chain.get("projection"),
                    source_use_binding=chain.get("binding"),
                    source_use_expectation=chain.get("expectation"),
                    source_generation_id=str(chain.get("source_generation_id") or ""),
                    execution_generation_id=generation_id,
                    require_source_use=True,
                    raw_source_metadata=raw_source_metadata_by_ticker[ticker],
                )
                require(trusted == capabilities[ticker], f"pass_b_untrusted_capability:{ticker}")
        internal_schema = capability_pass_b_batch_schema(
            subjects=subjects,
            catalogs=catalogs,
            capabilities=capabilities,
        )
        prompt_template = capability_prompt_template()
        ref_catalog = {ticker: catalogs[ticker] for ticker in subjects}
    internal_scan = schema_completeness_and_parity_scan(
        internal_schema,
        stage=stage,
        subjects=subjects,
    )
    wire_schema, projection = project_provider_wire_schema(internal_schema)
    dialect = scan_provider_structured_output_schema(wire_schema)
    require(internal_scan["status"] == "PASS", f"internal_schema_failed:{stage}:{market}:{batch}")
    require(dialect["status"] == "PASS", f"wire_schema_failed:{stage}:{market}:{batch}")
    require(dialect["unsupported_keyword_count"] == 0, "wire_unsupported_keyword")
    require(dialect["unique_items_count"] == 0, "wire_unique_items_present")

    write_text(
        directory / "prompt.txt",
        m12db._prompt(prompt_template, stage=stage, subjects=subjects, payloads=payloads),
    )
    write_json(directory / "subject-context.json", {"subjects": payloads})
    write_json(directory / "internal-semantic-schema.json", internal_schema)
    write_json(directory / "provider-wire-schema.json", wire_schema)
    write_json(directory / "provider-wire-projection.json", projection)
    write_json(directory / "provider-dialect-scan.json", dialect)
    write_json(directory / "internal-schema-scan.json", internal_scan)
    write_json(directory / "ref-catalog.json", ref_catalog)
    if capabilities is not None:
        write_json(
            directory / "capability-catalog.json",
            {ticker: capabilities[ticker] for ticker in subjects},
        )
    binding = {
        "contract": "m12dc-source-use-consumed-view-request-binding-v1",
        "execution_generation_id": generation_id,
        "subjects": {
            ticker: {
                "source_generation_id": chains[ticker]["source_generation_id"],
                "authority_manifest_sha256": chains[ticker]["authority"][
                    "authority_manifest_sha256"
                ],
                "expectation_sha256": chains[ticker]["expectation"]["expectation_sha256"],
                "projection_sha256": chains[ticker]["projection"]["projection_sha256"],
                "binding_sha256": chains[ticker]["binding"]["binding_sha256"],
                "permission_derivation_sha256": chains[ticker]["projection"][
                    "permission_derivation_sha256"
                ],
                "consumed_source_binding": contexts[ticker].get("source_evidence_binding"),
                "capability_sha256": (
                    canonical_sha256(capabilities[ticker]) if capabilities is not None else None
                ),
                "pass_a_sha256": (
                    canonical_sha256(contexts[ticker].get("frozen_pass_a_classification"))
                    if stage == "pass-b"
                    else None
                ),
                "deterministic_option_sha256": (
                    canonical_sha256(contexts[ticker].get("deterministic_fundamental_option"))
                    if stage == "pass-b"
                    else None
                ),
            }
            for ticker in subjects
        },
        "status": "PASS",
    }
    write_json(directory / "source-use-and-consumed-source-binding.json", binding)
    files = {
        "prompt": directory / "prompt.txt",
        "context": directory / "subject-context.json",
        "internal_schema": directory / "internal-semantic-schema.json",
        "wire_schema": directory / "provider-wire-schema.json",
        "ref_catalog": directory / "ref-catalog.json",
        "source_binding": directory / "source-use-and-consumed-source-binding.json",
    }
    if capabilities is not None:
        files["capability_catalog"] = directory / "capability-catalog.json"
    identity = {
        "stage": stage,
        "market": market,
        "batch": batch,
        "subjects": list(subjects),
        "model": MODEL,
        "effort": EFFORT,
        "timeout_seconds": TIMEOUT_SECONDS,
        "execution_generation_id": generation_id,
        "request_composition": (
            "CAPABILITY_AWARE_FINAL" if stage == "pass-b" else "FINAL_POST_QUALITY_BOUND"
        ),
        "file_sha256": {key: sha256_file(path) for key, path in files.items()},
    }
    receipt = {
        "contract": "m12dc-frozen-outbound-request-v1",
        **identity,
        "request_sha256": canonical_sha256(identity),
        "fixture_only": fixture_only,
        "transport_prompt": str((directory / "prompt.txt").resolve()),
        "transport_wire_schema": str((directory / "provider-wire-schema.json").resolve()),
        "internal_schema_not_submitted": True,
        "wrapper_invoked": False,
        "provider_calls": 0,
        "status": "PASS",
    }
    write_json(directory / "request-receipt.json", receipt)
    return {**receipt, "directory": str(directory), "dialect": dialect}


def _load_m12cp(zip_path: Path) -> dict[str, object]:
    suffixes = {
        "options": "/policy-selectable-entry-options-22.json",
        "security": "/depositary-security-basis-coverage.json",
        "completion": "/program-completion.json",
        "policy": "/m12co-chat-policy-selection.json",
    }
    values: dict[str, object] = {}
    with zipfile.ZipFile(zip_path) as archive:
        names = archive.namelist()
        for key, suffix in suffixes.items():
            matches = [name for name in names if name.endswith(suffix)]
            require(len(matches) == 1, f"m12cp_member_scope:{key}")
            values[key] = json.loads(archive.read(matches[0]).decode("utf-8"))
    options = values["options"]
    require(isinstance(options, Mapping) and options.get("subject_count") == 22, "m12cp_count")
    return values


def _typed_states(subjects: Mapping[str, Mapping[str, object]]) -> dict[str, dict[str, object]]:
    return {
        ticker: {
            "business_evidence_quality": deepcopy(
                subjects[ticker].get("business_evidence_quality_state") or {}
            ),
            "security_valuation_basis": deepcopy(
                subjects[ticker].get("security_valuation_basis_state") or {}
            ),
            "directional_disclosure_refs": deepcopy(
                subjects[ticker].get("directional_disclosure_quality_refs") or []
            ),
        }
        for ticker in _expected_tickers()
    }


def _build_pass_b_inputs(
    *,
    source_contexts: Mapping[str, Mapping[str, object]],
    source_packets: Mapping[str, Mapping[str, object]],
    catalogs: Mapping[str, Mapping[str, object]],
    chains: Mapping[str, Mapping[str, object]],
    pass_a_by_ticker: Mapping[str, Mapping[str, object]],
    policy_options: Mapping[str, Mapping[str, object]],
    typed: Mapping[str, Mapping[str, object]],
    generation_id: str,
) -> tuple[dict[str, dict[str, object]], dict[str, dict[str, object]]]:
    contexts: dict[str, dict[str, object]] = {}
    capabilities: dict[str, dict[str, object]] = {}
    for ticker in _expected_tickers():
        chain = chains[ticker]
        context = build_pass_b_subject_context(
            context=source_contexts[ticker],
            ticker=ticker,
            catalog=catalogs[ticker],
            pass_a=pass_a_by_ticker[ticker],
            policy_option=policy_options[ticker],
            source_use_view=chain["projection"],
            source_use_binding=chain["binding"],
            source_use_expectation=chain["expectation"],
            source_generation_id=str(chain["source_generation_id"]),
            execution_generation_id=generation_id,
            require_source_use=True,
        )
        context["business_evidence_quality_state"] = deepcopy(
            typed[ticker]["business_evidence_quality"]
        )
        context["security_valuation_basis_state"] = deepcopy(
            typed[ticker]["security_valuation_basis"]
        )
        context["directional_disclosure_quality_refs"] = deepcopy(
            typed[ticker]["directional_disclosure_refs"]
        )
        capability = build_pass_b_capability_catalog(
            context=context,
            catalog=catalogs[ticker],
            pass_a=pass_a_by_ticker[ticker],
            policy_option=policy_options[ticker],
            source_use_view=chain["projection"],
            source_use_binding=chain["binding"],
            source_use_expectation=chain["expectation"],
            source_generation_id=str(chain["source_generation_id"]),
            execution_generation_id=generation_id,
            require_source_use=True,
            raw_source_metadata=source_packets[ticker]["decision_evidence"],
        )
        context["pass_b_capability_catalog"] = deepcopy(capability)
        require(
            context["ticker"] == source_packets[ticker]["ticker"],
            f"pass_b_source_subject_mismatch:{ticker}",
        )
        contexts[ticker] = context
        capabilities[ticker] = capability
    return contexts, capabilities


def _validate_fixture_b(
    *,
    contexts: Mapping[str, Mapping[str, object]],
    catalogs: Mapping[str, Mapping[str, object]],
    capabilities: Mapping[str, Mapping[str, object]],
    chains: Mapping[str, Mapping[str, object]],
    source_packets: Mapping[str, Mapping[str, object]],
    generation_id: str,
) -> dict[str, object]:
    rows: list[dict[str, object]] = []
    source_generations = {str(chain["source_generation_id"]) for chain in chains.values()}
    require(len(source_generations) == 1, "mixed_source_generations")
    source_generation = next(iter(source_generations))
    for spec in _batch_topology():
        market = str(spec["market"])
        batch = int(spec["batch"])
        batch_subjects = tuple(str(value) for value in spec["subjects"])
        output = {
            "decisions": {
                ticker: m12db_r1._synthetic_row(capabilities[ticker]) for ticker in batch_subjects
            }
        }
        raw = validate_capability_selection(
            output,
            subjects=batch_subjects,
            catalogs=catalogs,
            capabilities=capabilities,
            source_use_views={ticker: chains[ticker]["projection"] for ticker in batch_subjects},
            source_use_bindings={ticker: chains[ticker]["binding"] for ticker in batch_subjects},
            source_use_expectations={
                ticker: chains[ticker]["expectation"] for ticker in batch_subjects
            },
            source_metadata_by_ticker={
                ticker: source_packets[ticker]["decision_evidence"] for ticker in batch_subjects
            },
            source_generation_id=source_generation,
            execution_generation_id=generation_id,
            require_source_use=True,
        )
        normalized, normalization = normalize_future_pass_b(
            output,
            subjects=batch_subjects,
            catalogs=catalogs,
        )
        materialized = validate_materialized_pass_b(
            normalized,
            subjects=batch_subjects,
            catalogs=catalogs,
            pass_a_by_ticker={
                ticker: contexts[ticker]["frozen_pass_a_classification"]
                for ticker in batch_subjects
            },
            policy_options={
                ticker: contexts[ticker]["deterministic_fundamental_option"]
                for ticker in batch_subjects
            },
            capabilities=capabilities,
        )
        envelope = PassBBatchOutput.model_validate(
            {
                "contract": "m12cq-pass-b-decision-tactical-v1",
                "generation_id": generation_id,
                "packet_id": f"m12dc-fixture-{market}-batch-{batch:02d}",
                "market": market,
                "assessment_date": ASSESSMENT_DATE,
                "decisions": normalized,
            }
        )
        final = validate_pass_b_batch(
            envelope,
            expected_identity={
                "generation_id": generation_id,
                "packet_id": f"m12dc-fixture-{market}-batch-{batch:02d}",
                "market": market,
                "assessment_date": ASSESSMENT_DATE,
            },
            subjects=batch_subjects,
            catalogs=catalogs,
            pass_a_by_ticker={
                ticker: contexts[ticker]["frozen_pass_a_classification"]
                for ticker in batch_subjects
            },
            source_use_views={ticker: chains[ticker]["projection"] for ticker in batch_subjects},
            source_use_bindings={ticker: chains[ticker]["binding"] for ticker in batch_subjects},
            source_use_expectations={
                ticker: chains[ticker]["expectation"] for ticker in batch_subjects
            },
            source_metadata_by_ticker={
                ticker: source_packets[ticker]["decision_evidence"] for ticker in batch_subjects
            },
            source_generation_id=source_generation,
            execution_generation_id=generation_id,
            require_source_use=True,
        )
        status = (
            "PASS"
            if raw["status"]
            == normalization["status"]
            == materialized["status"]
            == final["status"]
            == "PASS"
            else "FAIL"
        )
        rows.append(
            {
                "market": market,
                "batch": batch,
                "subjects": list(batch_subjects),
                "raw_capability": raw,
                "normalization": normalization,
                "materialized": materialized,
                "final_source_use": final,
                "status": status,
            }
        )
    return {
        "contract": "m12dc-fixture-b-full-consumer-preflight-v1",
        "fixture_only": True,
        "batch_count": len(rows),
        "subject_count": sum(len(row["subjects"]) for row in rows),
        "rows": rows,
        "status": "PASS" if all(row["status"] == "PASS" for row in rows) else "FAIL",
    }


def _historical_crcl_control(
    *,
    m12cu_root: Path,
    catalogs: Mapping[str, Mapping[str, object]],
    capabilities: Mapping[str, Mapping[str, object]],
) -> dict[str, object]:
    raw_path = m12cu_root / "model-calls/pass-b/us/batch-01/raw-output.json"
    output = read_json(raw_path)
    subjects = ("CORZ", "CPNG", "CRCL")
    old_shape = validate_future_pass_b_shape(output, subjects=subjects, catalogs=catalogs)
    current = validate_capability_selection(
        output,
        subjects=subjects,
        catalogs=catalogs,
        capabilities=capabilities,
    )
    crcl_errors = current["per_ticker"]["CRCL"]
    result = {
        "contract": "m12dc-historical-crcl-negative-control-v1",
        "raw_sha256": sha256_file(raw_path),
        "old_generic_shape": old_shape,
        "capability_validation": current,
        "expected_crcl_error": "PB_CAP_NEW_BUYER_BRANCH_FORBIDDEN",
        "expected_crcl_error_present": "PB_CAP_NEW_BUYER_BRANCH_FORBIDDEN" in crcl_errors,
    }
    result["status"] = (
        "PASS"
        if result["raw_sha256"] == EXPECTED_CRCL_RAW_SHA256
        and old_shape["status"] == "PASS"
        and current["status"] == "FAIL"
        and result["expected_crcl_error_present"]
        else "FAIL"
    )
    return result


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
        "log": str(log),
        "status": "PASS" if completed.returncode == 0 else "FAIL",
    }


def _test_counts(log: Path) -> dict[str, int]:
    value = log.read_text(encoding="utf-8")
    passed = re.search(r"(\d+) passed", value)
    skipped = re.search(r"(\d+) skipped", value)
    return {
        "passed": int(passed.group(1)) if passed else 0,
        "skipped": int(skipped.group(1)) if skipped else 0,
    }


def _run_validation(result_root: Path, *, phase: str, full: bool = False) -> dict[str, object]:
    output = result_root / "validation" / phase
    focused = (
        "tests/test_m12dc_fresh_source_use_two_pass_reproof.py",
        "tests/test_m12db_r1_request_composition_closure.py",
        "tests/test_m12db_model_view_readiness.py",
        "tests/test_m12da_r3_projection_consumed_evidence_closure.py",
        "tests/test_m12da_source_use_contract.py",
        "tests/test_m12cv_pass_b_capability_contract.py",
        "tests/test_m12cr_shadow_contract.py",
        "tests/test_m12cr_r1_typed_quality_contract.py",
        "tests/test_m12cq_two_pass_policy_shadow.py",
    )
    suites: dict[str, tuple[str, ...]] = {"focused": focused}
    if phase == "postrun" or full:
        suites.update(
            {
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
        )
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
    targets = (
        "scripts/m12dc_fresh_source_use_two_pass_reproof.py",
        "tests/test_m12dc_fresh_source_use_two_pass_reproof.py",
        "scripts/m12db_model_view_readiness.py",
        "scripts/m12db_r1_request_composition_closure.py",
        "scripts/m12cv_pass_b_capability_contract.py",
        "tests/test_m12cv_pass_b_capability_contract.py",
    )
    ruff = str(Path(sys.executable).with_name("ruff"))
    rows.extend(
        (
            _run_command(name="ruff", command=(ruff, "check", *targets), output_dir=output),
            _run_command(
                name="ruff-format",
                command=(ruff, "format", "--check", *targets),
                output_dir=output,
            ),
            _run_command(name="diff-check", command=("git", "diff", "--check"), output_dir=output),
            _run_command(
                name="compile",
                command=(sys.executable, "-m", "py_compile", *targets[:2]),
                output_dir=output,
            ),
        )
    )
    counts = {
        name: _test_counts(output / f"{name}.log")
        for name in suites
        if (output / f"{name}.log").is_file()
    }
    return {
        "contract": f"m12dc-{phase}-validation-v1",
        "commands": rows,
        "counts": counts,
        "status": "PASS" if all(row["status"] == "PASS" for row in rows) else "FAIL",
    }


def _planned_ledger(*, b_only: bool = False) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    ordinal = 0
    for stage in ("pass-b",) if b_only else ("pass-a", "pass-b"):
        for spec in _batch_topology():
            ordinal += 1
            rows.append(
                {
                    "ordinal": ordinal,
                    "stage": stage,
                    "market": spec["market"],
                    "batch": spec["batch"],
                    "subjects": list(spec["subjects"]),
                    "planned": True,
                    "wrapper_attempted": False,
                    "request_rejected": False,
                    "usable_final_response": False,
                    "raw_accepted": False,
                    "semantic_accepted": False,
                    "materialized_final_accepted": False,
                    "status": "PLANNED",
                }
            )
    return rows


def _ledger_row(
    ledger: Sequence[dict[str, object]], *, stage: str, market: str, batch: int
) -> dict[str, object]:
    return next(
        row
        for row in ledger
        if row["stage"] == stage and row["market"] == market and row["batch"] == batch
    )


def _assert_execution_freeze(expected_head: str, code_hashes: Mapping[str, str]) -> None:
    require(_git("rev-parse", "HEAD") == expected_head, "head_drift_after_freeze")
    require(not _git("status", "--porcelain"), "worktree_drift_after_freeze")
    for path, expected in code_hashes.items():
        require(sha256_file(REPO / path) == expected, f"code_hash_drift:{path}")


def _invoke(
    *,
    stage: str,
    market: str,
    batch: int,
    request_dir: Path,
    result_root: Path,
    generation_id: str,
    runtime: Any,
    codex_bin: str,
    expected_head: str,
    code_hashes: Mapping[str, str],
    ledger: list[dict[str, object]],
    official_binding=None,
) -> dict[str, object]:
    _assert_execution_freeze(expected_head, code_hashes)
    call_dir = result_root / "model-calls" / stage / market / f"batch-{batch:02d}"
    call_dir.mkdir(parents=True, exist_ok=False)
    prompt = request_dir / "prompt.txt"
    wire_schema = request_dir / "provider-wire-schema.json"
    output = call_dir / "raw-output.json"
    log = call_dir / "transport.log"
    capture = read_json(request_dir / "request-receipt.json")
    for key, filename in {
        "prompt": "prompt.txt",
        "wire_schema": "provider-wire-schema.json",
        "context": "subject-context.json",
        "internal_schema": "internal-semantic-schema.json",
        "ref_catalog": "ref-catalog.json",
        "source_binding": "source-use-and-consumed-source-binding.json",
    }.items():
        require(
            sha256_file(request_dir / filename) == capture["file_sha256"][key],
            f"outbound_capture_changed:{key}",
        )
    if stage == "pass-b":
        require(
            sha256_file(request_dir / "capability-catalog.json")
            == capture["file_sha256"]["capability_catalog"],
            "outbound_capture_changed:capability_catalog",
        )
    namespace = f"m12dc:{generation_id}:{stage}:{market}:batch-{batch:02d}"
    invocation_cwd = REPO
    transport_options = {}
    if official_binding is not None:
        from app.services.official_codex_shadow_transport_service import OfficialShadowRequest

        identity = {
            key: capture[key]
            for key in (
                "stage",
                "market",
                "batch",
                "subjects",
                "model",
                "effort",
                "timeout_seconds",
                "execution_generation_id",
                "request_composition",
                "file_sha256",
            )
        }
        require(canonical_sha256(identity) == capture["request_sha256"], "request_identity_drift")
        expected_subjects = next(
            spec["subjects"]
            for spec in _batch_topology()
            if spec["market"] == market and spec["batch"] == batch
        )
        require(
            (
                capture["stage"],
                capture["market"],
                capture["batch"],
                capture["execution_generation_id"],
                capture["model"],
                capture["effort"],
                capture["timeout_seconds"],
            )
            == (stage, market, batch, generation_id, MODEL, EFFORT, TIMEOUT_SECONDS)
            and list(capture["subjects"]) == list(expected_subjects),
            "request_batch_binding_mismatch",
        )
        invocation_cwd = call_dir / "approved-input"
        invocation_cwd.mkdir(exist_ok=False)
        shutil.copyfile(prompt, invocation_cwd / "prompt.txt")
        shutil.copyfile(wire_schema, invocation_cwd / "provider-wire-schema.json")
        prompt = invocation_cwd / "prompt.txt"
        wire_schema = invocation_cwd / "provider-wire-schema.json"
        transport_options["official_shadow"] = OfficialShadowRequest(
            official_binding,
            namespace,
            capture["file_sha256"]["prompt"],
            capture["file_sha256"]["wire_schema"],
        )
    row = _ledger_row(ledger, stage=stage, market=market, batch=batch)
    row.update(
        {
            "wrapper_attempted": True,
            "request_sha256": read_json(request_dir / "request-receipt.json")["request_sha256"],
            "prompt_sha256": sha256_file(prompt),
            "wire_schema_sha256": sha256_file(wire_schema),
            "timeout_seconds": TIMEOUT_SECONDS,
            "transport_attempt_limit": 1,
            "started_at": datetime.now(UTC).isoformat(),
            "status": "STARTED",
        }
    )
    write_json(result_root / "call-ledger.json", {"calls": ledger})
    try:
        receipt = runtime._invoke_signed_in_codex(
            codex_bin=codex_bin,
            prompt=prompt,
            output=output,
            log=log,
            schema=wire_schema,
            cwd=invocation_cwd,
            timeout=TIMEOUT_SECONDS,
            state_namespace=namespace,
            **transport_options,
        )
        require(int(receipt.get("transport_attempts") or 0) == 1, "hidden_retry_detected")
        row.update(
            {
                "usable_final_response": output.is_file() and output.stat().st_size > 0,
                "transport_attempts": receipt.get("transport_attempts"),
                "network_probe_attempts": receipt.get("network_probe_attempts"),
                "retry_recovered": receipt.get("retry_recovered"),
                "output_sha256": sha256_file(output),
                "status": "RESPONSE_RECEIVED",
                **({"official_transport": receipt} if official_binding is not None else {}),
            }
        )
        require(bool(row["usable_final_response"]), "usable_response_missing")
        return read_json(output)
    except BaseException as exc:  # noqa: BLE001
        row.update(
            {
                "status": "FAIL",
                "request_rejected": not output.exists(),
                "inference_may_have_occurred": (
                    getattr(exc, "process_started", True) if official_binding is not None else True
                ),
                "safe_error_type": type(exc).__name__,
                "safe_error_code": str(exc).split(":", 1)[0],
                "failure_category": classify_shadow_failure(exc, log, execution_stage=stage),
                "completed_at": datetime.now(UTC).isoformat(),
            }
        )
        write_text(call_dir / "failure-traceback.txt", traceback.format_exc())
        write_json(result_root / "call-ledger.json", {"calls": ledger})
        raise


def _source_generation(chains: Mapping[str, Mapping[str, object]]) -> str:
    values = {str(chain["source_generation_id"]) for chain in chains.values()}
    require(len(values) == 1, "mixed_source_generation")
    return next(iter(values))


def _run_pass_a(
    *,
    pass_a_contexts: Mapping[str, Mapping[str, object]],
    catalogs: Mapping[str, Mapping[str, object]],
    chains: Mapping[str, Mapping[str, object]],
    source_packets: Mapping[str, Mapping[str, object]],
    request_root: Path,
    result_root: Path,
    generation_id: str,
    runtime: Any,
    codex_bin: str,
    expected_head: str,
    code_hashes: Mapping[str, str],
    ledger: list[dict[str, object]],
    official_binding=None,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    output_rows: list[dict[str, object]] = []
    source_generation = _source_generation(chains)
    for spec in _batch_topology():
        market = str(spec["market"])
        batch = int(spec["batch"])
        subjects = tuple(str(value) for value in spec["subjects"])
        request_dir = request_root / "pass-a" / market / f"batch-{batch:02d}"
        output = _invoke(
            stage="pass-a",
            market=market,
            batch=batch,
            request_dir=request_dir,
            result_root=result_root,
            generation_id=generation_id,
            runtime=runtime,
            codex_bin=codex_bin,
            expected_head=expected_head,
            code_hashes=code_hashes,
            ledger=ledger,
            **({"official_binding": official_binding} if official_binding is not None else {}),
        )
        call_dir = result_root / "model-calls/pass-a" / market / f"batch-{batch:02d}"
        normalized, materialization = materialize_future_pass_a(
            output,
            subjects=subjects,
            subject_contexts=pass_a_contexts,
        )
        write_json(call_dir / "materialization-validation.json", materialization)
        require(materialization["status"] == "PASS", "pass_a_raw_or_materialization_failed")
        envelope = PassABatchOutput.model_validate(
            {
                "contract": "m12cq-pass-a-archetype-regime-v1",
                "generation_id": generation_id,
                "packet_id": f"m12dc-{market}-batch-{batch:02d}",
                "market": market,
                "assessment_date": ASSESSMENT_DATE,
                "classifications": normalized,
            }
        )
        semantic = validate_pass_a_batch(
            envelope,
            expected_identity={
                "generation_id": generation_id,
                "packet_id": f"m12dc-{market}-batch-{batch:02d}",
                "market": market,
                "assessment_date": ASSESSMENT_DATE,
            },
            subjects=subjects,
            subject_contexts=pass_a_contexts,
            source_catalogs=catalogs,
            source_use_views={ticker: chains[ticker]["projection"] for ticker in subjects},
            source_use_bindings={ticker: chains[ticker]["binding"] for ticker in subjects},
            source_use_expectations={ticker: chains[ticker]["expectation"] for ticker in subjects},
            source_metadata_by_ticker={
                ticker: source_packets[ticker]["decision_evidence"] for ticker in subjects
            },
            source_generation_id=source_generation,
            execution_generation_id=generation_id,
            require_source_use=True,
        )
        leak = pass_a_output_leak_scan(output)
        write_json(call_dir / "source-use-semantic-validation.json", semantic)
        write_json(call_dir / "output-leak-validation.json", leak)
        require(semantic["status"] == "PASS", "pass_a_source_use_semantic_failed")
        require(leak["status"] == "PASS", "pass_a_output_leak_failed")
        ledger_row = _ledger_row(ledger, stage="pass-a", market=market, batch=batch)
        ledger_row.update(
            {
                "raw_accepted": True,
                "semantic_accepted": True,
                "materialized_final_accepted": True,
                "subject_count": len(normalized),
                "status": "PASS",
                "completed_at": datetime.now(UTC).isoformat(),
            }
        )
        rows.extend(normalized)
        raw_path = call_dir / "raw-output.json"
        freeze = result_root / "output-freeze/pass-a" / market / f"batch-{batch:02d}.json"
        freeze.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(raw_path, freeze)
        require(sha256_file(freeze) == sha256_file(raw_path), "pass_a_freeze_mismatch")
        output_rows.append(
            {
                "market": market,
                "batch": batch,
                "subjects": list(subjects),
                "path": str(freeze.relative_to(result_root)),
                "sha256": sha256_file(freeze),
            }
        )
        write_json(result_root / "call-ledger.json", {"calls": ledger})
    require([str(row["ticker"]) for row in rows] == _expected_tickers(), "pass_a_22_scope")
    aggregate = result_root / "pass-a-22-subject-classification.json"
    write_json(
        aggregate,
        {
            "contract": "m12dc-pass-a-22-subject-classification-v1",
            "generation_id": generation_id,
            "subject_count": len(rows),
            "classifications": rows,
        },
    )
    write_json(
        result_root / "pass-a-output-freeze-manifest.json",
        {
            "contract": "m12dc-pass-a-output-freeze-manifest-v1",
            "generation_id": generation_id,
            "call_count": len(output_rows),
            "subject_count": len(rows),
            "outputs": output_rows,
            "aggregate_sha256": sha256_file(aggregate),
            "frozen_at": datetime.now(UTC).isoformat(),
            "status": "PASS",
        },
    )
    return rows


def _materialize_options(
    *,
    pass_a_rows: Sequence[Mapping[str, object]],
    matrix: Mapping[str, Mapping[str, object]],
    typed: Mapping[str, Mapping[str, object]],
    result_root: Path,
    generation_id: str,
) -> dict[str, dict[str, object]]:
    pass_a = {str(row["ticker"]): row for row in pass_a_rows}
    options: dict[str, dict[str, object]] = {}
    receipts: list[dict[str, object]] = []
    for ticker in _expected_tickers():
        selected = select_matrix_option(matrix[ticker], pass_a[ticker])
        gated, receipt = gate_policy_option_for_security_basis(
            selected,
            typed[ticker]["security_valuation_basis"],
        )
        require(receipt["status"] == "PASS", f"security_basis_gate_failed:{ticker}")
        options[ticker] = gated
        receipts.append(receipt)
    gate = validate_security_valuation_basis_gate(
        policy_options=options,
        security_basis_by_ticker={
            ticker: typed[ticker]["security_valuation_basis"] for ticker in _expected_tickers()
        },
    )
    require(gate["status"] == "PASS", "security_basis_aggregate_gate_failed")
    write_json(
        result_root / "fresh-deterministic-fundamental-options-22.json",
        {
            "contract": "m12dc-fresh-deterministic-fundamental-options-v1",
            "generation_id": generation_id,
            "subject_count": len(options),
            "rows": [options[ticker] for ticker in _expected_tickers()],
            "gate_receipts": receipts,
            "security_basis_gate": gate,
            "status": "PASS",
        },
    )
    return options


def _run_pass_b(
    *,
    contexts: Mapping[str, Mapping[str, object]],
    capabilities: Mapping[str, Mapping[str, object]],
    catalogs: Mapping[str, Mapping[str, object]],
    chains: Mapping[str, Mapping[str, object]],
    source_packets: Mapping[str, Mapping[str, object]],
    pass_a_by_ticker: Mapping[str, Mapping[str, object]],
    policy_options: Mapping[str, Mapping[str, object]],
    typed: Mapping[str, Mapping[str, object]],
    request_root: Path,
    result_root: Path,
    generation_id: str,
    runtime: Any,
    codex_bin: str,
    expected_head: str,
    code_hashes: Mapping[str, str],
    ledger: list[dict[str, object]],
    official_binding=None,
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    rows: list[dict[str, object]] = []
    entry_rows: list[dict[str, object]] = []
    output_rows: list[dict[str, object]] = []
    source_generation = _source_generation(chains)
    for spec in _batch_topology():
        market = str(spec["market"])
        batch = int(spec["batch"])
        subjects = tuple(str(value) for value in spec["subjects"])
        request_dir = request_root / "pass-b" / market / f"batch-{batch:02d}"
        output = _invoke(
            stage="pass-b",
            market=market,
            batch=batch,
            request_dir=request_dir,
            result_root=result_root,
            generation_id=generation_id,
            runtime=runtime,
            codex_bin=codex_bin,
            expected_head=expected_head,
            code_hashes=code_hashes,
            ledger=ledger,
            **({"official_binding": official_binding} if official_binding is not None else {}),
        )
        call_dir = result_root / "model-calls/pass-b" / market / f"batch-{batch:02d}"
        wire_errors = validate_json_schema(
            output, read_json(request_dir / "provider-wire-schema.json")
        )
        internal_errors = validate_json_schema(
            output, read_json(request_dir / "internal-semantic-schema.json")
        )
        schema_check = {
            "wire_errors": [str(error) for error in wire_errors],
            "internal_errors": [str(error) for error in internal_errors],
            "status": "FAIL" if wire_errors or internal_errors else "PASS",
        }
        write_json(call_dir / "actual-schema-validation.json", schema_check)
        require(schema_check["status"] == "PASS", "pass_b_captured_schema_failed")
        raw = validate_capability_selection(
            output,
            subjects=subjects,
            catalogs=catalogs,
            capabilities=capabilities,
            source_use_views={ticker: chains[ticker]["projection"] for ticker in subjects},
            source_use_bindings={ticker: chains[ticker]["binding"] for ticker in subjects},
            source_use_expectations={ticker: chains[ticker]["expectation"] for ticker in subjects},
            source_metadata_by_ticker={
                ticker: source_packets[ticker]["decision_evidence"] for ticker in subjects
            },
            source_generation_id=source_generation,
            execution_generation_id=generation_id,
            require_source_use=True,
        )
        write_json(call_dir / "raw-capability-source-use-validation.json", raw)
        require(raw["status"] == "PASS", "pass_b_raw_capability_failed:" + ";".join(raw["errors"]))
        normalized, normalization = normalize_future_pass_b(
            output,
            subjects=subjects,
            catalogs=catalogs,
        )
        write_json(call_dir / "normalization-validation.json", normalization)
        require(normalization["status"] == "PASS", "pass_b_normalization_failed")
        materialized = validate_materialized_pass_b(
            normalized,
            subjects=subjects,
            catalogs=catalogs,
            pass_a_by_ticker=pass_a_by_ticker,
            policy_options=policy_options,
            capabilities=capabilities,
        )
        write_json(call_dir / "materialized-policy-validation.json", materialized)
        require(materialized["status"] == "PASS", "pass_b_materialized_policy_failed")
        envelope = PassBBatchOutput.model_validate(
            {
                "contract": "m12cq-pass-b-decision-tactical-v1",
                "generation_id": generation_id,
                "packet_id": f"m12dc-{market}-batch-{batch:02d}",
                "market": market,
                "assessment_date": ASSESSMENT_DATE,
                "decisions": normalized,
            }
        )
        final = validate_pass_b_batch(
            envelope,
            expected_identity={
                "generation_id": generation_id,
                "packet_id": f"m12dc-{market}-batch-{batch:02d}",
                "market": market,
                "assessment_date": ASSESSMENT_DATE,
            },
            subjects=subjects,
            catalogs=catalogs,
            pass_a_by_ticker=pass_a_by_ticker,
            source_use_views={ticker: chains[ticker]["projection"] for ticker in subjects},
            source_use_bindings={ticker: chains[ticker]["binding"] for ticker in subjects},
            source_use_expectations={ticker: chains[ticker]["expectation"] for ticker in subjects},
            source_metadata_by_ticker={
                ticker: source_packets[ticker]["decision_evidence"] for ticker in subjects
            },
            source_generation_id=source_generation,
            execution_generation_id=generation_id,
            require_source_use=True,
        )
        ownership = validate_quality_basis_decision_ownership(
            normalized,
            catalogs=catalogs,
            typed_states=typed,
        )
        write_json(
            call_dir / "final-semantic-validation.json",
            {"source_use": final, "typed_ownership": ownership},
        )
        require(final["status"] == "PASS", "pass_b_final_source_use_failed")
        require(ownership["status"] == "PASS", "pass_b_typed_ownership_failed")
        ledger_row = _ledger_row(ledger, stage="pass-b", market=market, batch=batch)
        ledger_row.update(
            {
                "raw_accepted": True,
                "semantic_accepted": True,
                "materialized_final_accepted": True,
                "subject_count": len(normalized),
                "status": "PASS",
                "completed_at": datetime.now(UTC).isoformat(),
            }
        )
        rows.extend(normalized)
        entry_rows.extend(materialized["entry_rows"])
        write_json(call_dir / "accepted-normalized-decisions.json", {"decisions": normalized})
        raw_path = call_dir / "raw-output.json"
        freeze = result_root / "output-freeze/pass-b" / market / f"batch-{batch:02d}.json"
        freeze.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(raw_path, freeze)
        require(sha256_file(freeze) == sha256_file(raw_path), "pass_b_freeze_mismatch")
        output_rows.append(
            {
                "market": market,
                "batch": batch,
                "subjects": list(subjects),
                "path": str(freeze.relative_to(result_root)),
                "sha256": sha256_file(freeze),
            }
        )
        write_json(result_root / "call-ledger.json", {"calls": ledger})
        write_json(
            result_root / "pass-b-partial-accepted.json",
            {
                "decisions": rows,
                "entry_rows": entry_rows,
                "accepted_batches": len(output_rows),
                "subject_count": len(rows),
                "complete": False,
            },
        )
    require([str(row["ticker"]) for row in rows] == _expected_tickers(), "pass_b_22_scope")
    aggregate = result_root / "pass-b-22-subject-decisions.json"
    write_json(
        aggregate,
        {
            "contract": "m12dc-pass-b-22-subject-decisions-v1",
            "generation_id": generation_id,
            "subject_count": len(rows),
            "decisions": rows,
        },
    )
    write_json(
        result_root / "pass-b-output-freeze-manifest.json",
        {
            "contract": "m12dc-pass-b-output-freeze-manifest-v1",
            "generation_id": generation_id,
            "call_count": len(output_rows),
            "subject_count": len(rows),
            "outputs": output_rows,
            "aggregate_sha256": sha256_file(aggregate),
            "frozen_at": datetime.now(UTC).isoformat(),
            "status": "PASS",
        },
    )
    return rows, entry_rows


def _source_as_of(source_packet: Mapping[str, object]) -> dict[str, object]:
    dates: set[str] = set()
    for row in source_packet.get("decision_evidence") or ():
        if not isinstance(row, Mapping):
            continue
        for key in ("as_of", "source_date", "filing_date", "period_end"):
            value = row.get(key)
            if value:
                dates.add(str(value))
    current = source_packet.get("current_price")
    current_as_of = current.get("as_of") if isinstance(current, Mapping) else None
    return {
        "evidence_dates": sorted(dates),
        "current_price_as_of": current_as_of,
        "execution_time_is_not_source_time": True,
    }


def _finalize_rows(
    *,
    pass_a_rows: Sequence[Mapping[str, object]],
    pass_b_rows: Sequence[Mapping[str, object]],
    entry_rows: Sequence[Mapping[str, object]],
    options: Mapping[str, Mapping[str, object]],
    typed: Mapping[str, Mapping[str, object]],
    source_packets: Mapping[str, Mapping[str, object]],
) -> list[dict[str, object]]:
    pass_a = {str(row["ticker"]): row for row in pass_a_rows}
    pass_b = {str(row["ticker"]): row for row in pass_b_rows}
    entries = {str(row["ticker"]): row["entry_range"] for row in entry_rows}
    market_by_ticker = {
        ticker: market for market in ("us", "kr") for ticker in m12db.POPULATION[market]
    }
    rows: list[dict[str, object]] = []
    for ticker in _expected_tickers():
        a = pass_a[ticker]
        rows.append(
            {
                "ticker": ticker,
                "market": market_by_ticker[ticker],
                "company_archetype": a["archetype"],
                "archetype_confidence": a["archetype_confidence"],
                "archetype_supporting_claim_refs": a["archetype_supporting_claim_refs"],
                "archetype_rationale": a["archetype_rationale"],
                "valuation_regime_tier": a["valuation_regime_tier"],
                "tier_supporting_claim_refs": a["tier_supporting_claim_refs"],
                "tier_rationale": a["tier_rationale"],
                "data_quality_effect": a["data_quality_effect"],
                "data_quality_reason_class": a["data_quality_reason_class"],
                "data_quality_reason": a["data_quality_reason"],
                "data_quality_evidence_refs": a["data_quality_evidence_refs"],
                **pass_b[ticker],
                "business_evidence_quality": typed[ticker]["business_evidence_quality"],
                "security_valuation_basis": typed[ticker]["security_valuation_basis"],
                "fundamental_option": options[ticker],
                "entry_range": entries[ticker],
                "source_time": _source_as_of(source_packets[ticker]),
            }
        )
    return rows


def _post_freeze_comparison(
    *, rows: Sequence[Mapping[str, object]], supplemental_root: Path
) -> dict[str, object]:
    historical_path = (
        supplemental_root
        / "cross-run-offline-validation/combined-fresh-a-m12cx-b-22-subject-results.json"
    )
    historical = read_json(historical_path)["candidates"]
    old = {str(row["ticker"]): row for row in historical}
    fields = (
        "company_archetype",
        "valuation_regime_tier",
        "overall_direction",
        "new_buyer",
        "holder",
        "directional_balance",
    )
    comparison_rows = []
    for row in rows:
        ticker = str(row["ticker"])
        changes = {
            field: {"historical": old[ticker].get(field), "fresh": row.get(field)}
            for field in fields
            if old[ticker].get(field) != row.get(field)
        }
        comparison_rows.append(
            {
                "ticker": ticker,
                "changed_fields": changes,
                "changed_field_count": len(changes),
                "fresh_wait_reason": (
                    row.get("new_buyer_reason") if row.get("new_buyer") == "WAIT" else None
                ),
                "risk_wait_holdable_coexistence": (
                    row.get("new_buyer") == "WAIT"
                    and row.get("new_buyer_reason_class") == "EXECUTION_OR_THESIS_RISK"
                    and row.get("holder") == "HOLDABLE"
                ),
            }
        )
    return {
        "contract": "m12dc-post-freeze-descriptive-comparison-v1",
        "development_exposed_not_blind": True,
        "historical_reference_sha256": sha256_file(historical_path),
        "subject_count": len(comparison_rows),
        "changed_subject_count": sum(row["changed_field_count"] > 0 for row in comparison_rows),
        "risk_wait_holdable_count": sum(
            bool(row["risk_wait_holdable_coexistence"]) for row in comparison_rows
        ),
        "rows": comparison_rows,
        "comparison_used_as_acceptance_threshold": False,
        "status": "PASS",
    }


def _distribution(rows: Sequence[Mapping[str, object]]) -> dict[str, object]:
    keys = (
        "company_archetype",
        "valuation_regime_tier",
        "overall_direction",
        "new_buyer",
        "holder",
    )
    return {
        "contract": "m12dc-final-distribution-v1",
        "subject_count": len(rows),
        "counts": {
            key: dict(sorted(Counter(str(row[key]) for row in rows).items())) for key in keys
        },
        "wait_rows": [
            {
                "ticker": row["ticker"],
                "primary_reason_class": row["new_buyer_reason_class"],
                "reason": row["new_buyer_reason"],
                "fundamental_option": row["fundamental_option"],
                "tactical_choice": row["tactical_choice"],
                "re_evaluate_conditions": row["re_evaluate_conditions"],
                "source_time": row["source_time"],
            }
            for row in rows
            if row["new_buyer"] == "WAIT"
        ],
        "status": "PASS" if len(rows) == 22 else "FAIL",
    }


def _artifact_manifest(root: Path) -> dict[str, object]:
    files = []
    for path in sorted(root.rglob("*")):
        if path.is_file() and path.name != "artifact-manifest.json":
            files.append(
                {
                    "path": str(path.relative_to(root)),
                    "sha256": sha256_file(path),
                    "size": path.stat().st_size,
                }
            )
    return {"contract": "m12dc-artifact-manifest-v1", "file_count": len(files), "files": files}


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


def _report(
    *,
    completion: Mapping[str, object],
    ledger: Sequence[Mapping[str, object]],
    distribution: Mapping[str, object] | None,
    comparison: Mapping[str, object] | None,
    validation: Mapping[str, object] | None,
) -> str:
    pass_a = [row for row in ledger if row["stage"] == "pass-a"]
    pass_b = [row for row in ledger if row["stage"] == "pass-b"]
    b_only = completion.get("mode") == R1_MODE
    lines = [
        "# M12DC Fresh Source-Use-Aware Two-Pass Calibration Reproof",
        "",
        f"- Terminal: `{completion['terminal']}`",
        f"- Generation: `{completion.get('generation_id')}`",
        f"- Implementation: `{completion.get('implementation_commit')}`",
        f"- Work instruction: `{completion.get('work_instruction_commit')}`",
        (
            f"- Accepted frozen M12DC A: `{completion.get('accepted_a_fixture_subjects', 0)}/22` subjects; new A calls `0`"
            if b_only
            else f"- Pass A: `{sum(row['status'] == 'PASS' for row in pass_a)}/8` batches"
        ),
        f"- Pass B: `{sum(row['status'] == 'PASS' for row in pass_b)}/8` batches",
        f"- Newly accepted B subjects: `{completion.get('newly_accepted_b_subjects', 0)}/22`",
        f"- Complete final aggregate subjects: `{completion.get('subject_count', 0)}/22`",
        f"- Wrapper attempts: `{completion.get('wrapper_attempted_calls', 0)}/{8 if b_only else 16}`",
        "- Retry / fallback / judge / repair calls: `0`",
        "- Source refresh / DB / send / scheduler / broker actions: `0`",
        "- Main merge / remote push / deploy: `0`",
        f"- Postrun validation: `{(validation or {}).get('status', 'NOT_RUN')}`",
    ]
    if distribution is not None:
        lines.extend(
            [
                "",
                "## Final distributions",
                "",
                f"```json\n{json.dumps(distribution['counts'], ensure_ascii=False, indent=2)}\n```",
            ]
        )
    if comparison is not None:
        lines.extend(
            [
                "",
                "## Descriptive comparison",
                "",
                f"- Changed subjects versus revealed historical M12CX: `{comparison['changed_subject_count']}/22`",
                f"- Risk-WAIT with HOLDABLE: `{comparison['risk_wait_holdable_count']}`",
                "- Historical labels were opened only after the new final freeze and were not acceptance targets.",
            ]
        )
    blocker = completion.get("blocker")
    if blocker:
        lines.extend(["", "## Blocker", "", f"```json\n{json.dumps(blocker, indent=2)}\n```"])
    return "\n".join(lines)


def _prepare_execution_environment(
    args: argparse.Namespace, scratch: Path
) -> tuple[Any, str, dict[str, object]]:
    os.environ["THESIS_MONITOR_ENV_FILE"] = str(args.env_file)
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

    require(REASONING_MODEL == MODEL, "configured_model_drift")
    require(REASONING_EFFORT == EFFORT, "configured_effort_drift")
    runtime.V2_TRANSPORT_ATTEMPT_LIMIT = 1
    codex_bin = runtime._signed_in_codex_bin()
    version = subprocess.run(
        (codex_bin, "--version"), check=True, capture_output=True, text=True
    ).stdout.strip()
    require(version == EXPECTED_CLI_VERSION, "codex_cli_version_drift")
    return (
        runtime,
        codex_bin,
        {
            "contract": "m12dc-transport-model-config-freeze-v1",
            "model": REASONING_MODEL,
            "reasoning_effort": REASONING_EFFORT,
            "codex_cli": codex_bin,
            "codex_cli_sha256": sha256_file(Path(codex_bin)),
            "codex_cli_version": version,
            "timeout_seconds_per_request": TIMEOUT_SECONDS,
            "transport_attempt_limit": runtime.V2_TRANSPORT_ATTEMPT_LIMIT,
            "fallback": False,
            "status": "PASS",
        },
    )


def _load_frozen_a(args: argparse.Namespace) -> tuple[list[dict[str, object]], dict[str, object]]:
    root = args.frozen_a_root
    require(
        sha256_file(args.upstream_report_zip)
        == "54428273276e986c8fe1c36be705bed3967e8647290b8ebe3cce70fb643de6e7",
        "M12DC_R1_UPSTREAM_FIXTURE_BINDING_FAILED",
    )
    verification = _manifest_verification(root, 347)
    require(verification["status"] == "PASS", "M12DC_R1_UPSTREAM_FIXTURE_BINDING_FAILED")
    for filename, digest in UPSTREAM_FILES.items():
        require(sha256_file(root / filename) == digest, "M12DC_R1_UPSTREAM_FIXTURE_BINDING_FAILED")
        shutil.copy2(root / filename, args.result_root / filename)
    a = read_json(root / "pass-a-22-subject-classification.json")
    freeze = read_json(root / "pass-a-output-freeze-manifest.json")
    require(
        a["generation_id"] == freeze["generation_id"] == UPSTREAM_GENERATION,
        "M12DC_R1_UPSTREAM_FIXTURE_BINDING_FAILED",
    )
    require(
        freeze["aggregate_sha256"] == UPSTREAM_FILES["pass-a-22-subject-classification.json"],
        "M12DC_R1_UPSTREAM_FIXTURE_BINDING_FAILED",
    )
    ledger = read_json(root / "call-ledger.json")["calls"]
    a_calls = [row for row in ledger if row["stage"] == "pass-a"]
    require(
        len(a_calls) == 8 and all(row["semantic_accepted"] for row in a_calls),
        "M12DC_R1_UPSTREAM_FIXTURE_BINDING_FAILED",
    )
    b_start = min(
        row["started_at"] for row in ledger if row["stage"] == "pass-b" and row["wrapper_attempted"]
    )
    b_freeze = read_json(root / "pass-b-request-freeze-manifest.json")["frozen_at"]
    require(freeze["frozen_at"] < b_freeze < b_start, "M12DC_R1_UPSTREAM_FIXTURE_BINDING_FAILED")
    for item in freeze["outputs"]:
        require(
            sha256_file(root / item["path"]) == item["sha256"],
            "M12DC_R1_UPSTREAM_FIXTURE_BINDING_FAILED",
        )
    for dirname in ("model-calls/pass-a", "frozen-requests/pass-a", "output-freeze/pass-a"):
        shutil.copytree(root / dirname, args.result_root / "upstream-a" / dirname)
    for name in (
        "artifact-manifest.json",
        "call-ledger.json",
        "pass-a-request-freeze-manifest.json",
    ):
        shutil.copy2(root / name, args.result_root / "upstream-a" / name)
    options_envelope = read_json(root / "fresh-deterministic-fundamental-options-22.json")
    options = {row["ticker"]: row for row in options_envelope["rows"]}
    require(
        set(options) == {row["ticker"] for row in a["classifications"]} == set(_expected_tickers()),
        "M12DC_R1_UPSTREAM_FIXTURE_BINDING_FAILED",
    )
    write_json(
        args.result_root / "immutable-upstream-a-binding.json",
        {
            "mode": R1_MODE,
            "upstream_implementation": UPSTREAM_HEAD,
            "upstream_execution_generation_id": UPSTREAM_GENERATION,
            "new_execution_generation_id": args.generation_id,
            "file_sha256": UPSTREAM_FILES,
            "manifest": verification,
            "accepted_a_subjects": 22,
            "new_a_calls": 0,
            "status": "PASS",
        },
    )
    return a["classifications"], options


def _decisive_ref_parity(
    *,
    contexts,
    catalogs,
    capabilities,
    chains,
    source_packets,
    captures,
    upstream_root: Path,
    result_root: Path,
    generation_id: str,
) -> None:
    fields = ("decisive_supporting_claim_refs", "decisive_contradicting_claim_refs")
    rows = []
    for capture in captures:
        directory = Path(capture["directory"])
        schemas = {
            name: read_json(directory / name)
            for name in ("internal-semantic-schema.json", "provider-wire-schema.json")
        }
        synthetic = {
            "decisions": {
                ticker: m12db_r1._synthetic_row(capabilities[ticker])
                for ticker in capture["subjects"]
            }
        }
        for schema in schemas.values():
            require(
                not validate_json_schema(synthetic, schema),
                "synthetic_captured_schema_rejected",
            )
        for ticker in capture["subjects"]:
            chain = chains[ticker]
            eligible = set(capabilities[ticker]["evidence_classes"]["material_business_claim_refs"])
            for ref in catalogs[ticker]["claim_refs"]:
                accepted = (
                    validate_selected_refs(
                        chain["projection"],
                        refs=[ref],
                        use=SourceUse.OVERALL_DIRECTION,
                        require_any=True,
                        binding=chain["binding"],
                    )["status"]
                    == "PASS"
                )
                for field in fields:
                    trial = deepcopy(synthetic)
                    trial["decisions"][ticker][field] = [ref]
                    membership = {
                        name: not validate_json_schema(trial, schema)
                        for name, schema in schemas.items()
                    }
                    rows.append(
                        {
                            "ticker": ticker,
                            "field": field,
                            "ref": ref,
                            "source_use_accepted": accepted,
                            "schema_membership": membership,
                            "status": "PASS"
                            if all(value == accepted for value in membership.values())
                            and ((ref in eligible) == accepted)
                            else "FAIL",
                        }
                    )
    write_json(
        result_root / "per-field-reference-permission-parity-22.json",
        {
            "rows": rows,
            "subject_count": len(contexts),
            "positive_controls": sum(row["source_use_accepted"] for row in rows),
            "negative_controls": sum(not row["source_use_accepted"] for row in rows),
            "status": "PASS" if all(row["status"] == "PASS" for row in rows) else "FAIL",
        },
    )
    require(all(row["status"] == "PASS" for row in rows), "decisive_ref_parity_gap")
    old_request = upstream_root / "frozen-requests/pass-b/us/batch-03"
    raw = read_json(upstream_root / "model-calls/pass-b/us/batch-03/raw-output.json")
    new_request = next(
        Path(row["directory"]) for row in captures if row["market"] == "us" and row["batch"] == 3
    )
    errors = {}
    for name in ("internal-semantic-schema.json", "provider-wire-schema.json"):
        require(
            not validate_json_schema(raw, read_json(old_request / name)),
            "archived_mu_schema_did_not_accept",
        )
        errors[name] = validate_json_schema(raw, read_json(new_request / name))
        require(
            "$.decisions.MU.decisive_supporting_claim_refs[0]:enum_mismatch" in errors[name],
            "new_mu_schema_missing_exact_rejection",
        )
    selected = validate_selected_refs(
        chains["MU"]["projection"],
        refs=raw["decisions"]["MU"]["decisive_supporting_claim_refs"],
        use=SourceUse.OVERALL_DIRECTION,
        require_any=True,
        binding=chains["MU"]["binding"],
    )
    require(selected["status"] == "FAIL", "archived_mu_consumer_not_rejected")
    subjects = ("MU", "RXRX", "SKHY")
    consumer = validate_capability_selection(
        raw,
        subjects=subjects,
        catalogs=catalogs,
        capabilities=capabilities,
        source_use_views={ticker: chains[ticker]["projection"] for ticker in subjects},
        source_use_bindings={ticker: chains[ticker]["binding"] for ticker in subjects},
        source_use_expectations={ticker: chains[ticker]["expectation"] for ticker in subjects},
        source_metadata_by_ticker={
            ticker: source_packets[ticker]["decision_evidence"] for ticker in subjects
        },
        source_generation_id=_source_generation(chains),
        execution_generation_id=generation_id,
        require_source_use=True,
    )
    require(
        any(
            error.startswith("MU:PB_SOURCE_USE_OVERALL_SOURCE_USE_REF_FORBIDDEN:")
            for error in consumer["errors"]
        ),
        "archived_mu_actual_consumer_missing_rejection",
    )
    write_json(
        result_root / "immutable-mu-negative-control.json",
        {
            "old_internal_and_wire": "PASS",
            "new_schema_error_paths": errors,
            "unchanged_source_use_consumer": selected,
            "actual_raw_capability_consumer": consumer,
            "status": "PASS",
        },
    )
    shutil.copy2(
        upstream_root / "model-calls/pass-b/us/batch-03/raw-output.json",
        result_root / "immutable-mu-raw-output.json",
    )
    # Exercise the actual capture boundary with broken current-chain inputs, not a mock.
    ticker = next(iter(contexts))
    controls = []
    for kind in (
        "missing_projection",
        "missing_binding",
        "missing_expectation",
        "invalid_binding",
        "wrong_subject",
        "stale_capability",
        "forged_capability",
    ):
        c, caps, bound = deepcopy(contexts), deepcopy(capabilities), deepcopy(chains)
        if kind.startswith("missing_"):
            bound[ticker][kind.removeprefix("missing_")] = None
        elif kind == "invalid_binding":
            bound[ticker]["binding"]["binding_sha256"] = "invalid"
        elif kind == "wrong_subject":
            bound[ticker]["projection"]["ticker"] = "DIFFERENT_SUBJECT"
        elif kind == "stale_capability":
            caps[ticker]["source_use_execution_generation_id"] = "old-generation"
        else:
            caps[ticker]["evidence_classes"]["material_business_claim_refs"] = list(
                catalogs[ticker]["claim_refs"]
            )
        c[ticker]["pass_b_capability_catalog"] = deepcopy(caps[ticker])
        try:
            _request_capture(
                root=result_root / "negative-capture" / kind,
                stage="pass-b",
                market="us",
                batch=1,
                subjects=(ticker,),
                contexts=c,
                catalogs=catalogs,
                chains=bound,
                generation_id=generation_id,
                fixture_only=True,
                capabilities=caps,
                raw_source_metadata_by_ticker={
                    t: source_packets[t]["decision_evidence"] for t in (ticker,)
                },
            )
        except (ValueError, M12DCFailure) as exc:
            controls.append({"case": kind, "error": str(exc), "status": "PASS"})
        else:
            controls.append({"case": kind, "status": "FAIL"})
    write_json(result_root / "actual-capture-negative-controls.json", {"rows": controls})
    require(all(row["status"] == "PASS" for row in controls), "actual_capture_binding_gap")
    axis_rows = []
    for ticker, capability in capabilities.items():
        for axis, use in (
            ("holder", SourceUse.HOLDER_STANCE),
            ("new_buyer", SourceUse.NEW_BUYER_EXECUTION_RISK),
        ):
            for branch in capability[axis]["branches"]:
                if axis == "holder" and branch["stance"] == "HOLDABLE":
                    continue
                if axis == "new_buyer" and branch["reason_class"] != "EXECUTION_OR_THESIS_RISK":
                    continue
                for ref in branch["allowed_evidence_refs"]:
                    validation = validate_selected_refs(
                        chains[ticker]["projection"],
                        refs=[ref],
                        use=use,
                        require_any=True,
                        binding=chains[ticker]["binding"],
                    )
                    axis_rows.append(
                        {
                            "ticker": ticker,
                            "axis": axis,
                            "ref": ref,
                            "use": str(use),
                            "status": validation["status"],
                        }
                    )
    write_json(
        result_root / "holder-risk-current-use-mapping.json",
        {
            "rows": axis_rows,
            "blanket_entry_constraint_added": False,
            "status": "PASS" if all(row["status"] == "PASS" for row in axis_rows) else "FAIL",
        },
    )
    require(all(row["status"] == "PASS" for row in axis_rows), "holder_risk_use_mapping_gap")


def _export_r1_source_proof(result_root: Path) -> None:
    paths = (
        *CODE_PATHS,
        "tests/test_m12cv_pass_b_capability_contract.py",
        "tests/test_m12dc_fresh_source_use_two_pass_reproof.py",
    )
    for path in paths:
        old = _git("show", f"{UPSTREAM_HEAD}:{path}") + "\n"
        current = (REPO / path).read_text(encoding="utf-8")
        write_text(result_root / "source-export/old" / path, old)
        write_text(result_root / "source-export/new" / path, current)
        if path == "scripts/m12cv_pass_b_capability_contract.py":
            trees = [ast.parse(value) for value in (old, current)]
            for tree in trees:
                tree.body = [
                    node
                    for node in tree.body
                    if not (isinstance(node, ast.FunctionDef) and node.name == "_row_schema")
                ]
            require(ast.dump(trees[0]) == ast.dump(trees[1]), SOURCE_DRIFT)
        elif path in CODE_PATHS and path != "scripts/m12dc_fresh_source_use_two_pass_reproof.py":
            require(old == current, SOURCE_DRIFT)
    write_text(
        result_root / "source-export/changed-paths.diff", _git("diff", UPSTREAM_HEAD, "--", *paths)
    )
    write_json(
        result_root / "unchanged-authority-and-validator-predicates.json",
        {
            "m12cv_only_function_changed": "_row_schema",
            "source_use_and_final_validator_bodies_unchanged": True,
            "comparison": "AST excluding only _row_schema; other owners byte-equal",
            "status": "PASS",
        },
    )


def _upstream_b_parity(*, args, source_packets, catalogs, typed, frozen_a, frozen_options):
    chains = _source_chains(
        subjects=source_packets,
        catalogs=catalogs,
        r3_root=args.r3_root,
        generation_id=UPSTREAM_GENERATION,
    )
    _, source_contexts = _build_pass_a_contexts(
        subjects=source_packets, catalogs=catalogs, chains=chains, generation_id=UPSTREAM_GENERATION
    )
    contexts, _ = _build_pass_b_inputs(
        source_contexts=source_contexts,
        source_packets=source_packets,
        catalogs=catalogs,
        chains=chains,
        pass_a_by_ticker={row["ticker"]: row for row in frozen_a},
        policy_options=frozen_options,
        typed=typed,
        generation_id=UPSTREAM_GENERATION,
    )
    rows = []
    for spec in _batch_topology():
        directory = (
            args.frozen_a_root
            / "frozen-requests/pass-b"
            / spec["market"]
            / f"batch-{spec['batch']:02d}"
        )
        archived = read_json(directory / "subject-context.json")["subjects"]
        for old in archived:
            ticker = old["ticker"]
            rows.append(
                {
                    "ticker": ticker,
                    "archived_sha256": canonical_sha256(old),
                    "rebuilt_sha256": canonical_sha256(contexts[ticker]),
                    "status": "PASS" if old == contexts[ticker] else "FAIL",
                }
            )
    write_json(
        args.result_root / "unchanged-a-option-quality-source-context-proof.json",
        {
            "rows": rows,
            "comparison": "Rebuilt old execution against actual archived B contexts",
            "status": "PASS" if all(row["status"] == "PASS" for row in rows) else "FAIL",
        },
    )
    require(all(row["status"] == "PASS" for row in rows), SOURCE_DRIFT)


def run(args: argparse.Namespace) -> None:
    require(args.timeout == TIMEOUT_SECONDS, "timeout_must_be_1200")
    require(args.generation_id.startswith("20260919-m12dc-"), "generation_id_scope")
    require(not args.result_root.exists(), "result_root_must_not_exist")
    require(not args.output_zip.exists(), "output_zip_must_not_exist")
    args.result_root.mkdir(parents=True)
    scratch = args.result_root.parent / f".{args.result_root.name}-runtime"
    require(not scratch.exists(), "runtime_scratch_exists")
    scratch.mkdir()

    stage = "SOURCE_PREFLIGHT"
    terminal = PREINFERENCE_BLOCKED
    terminal_error: BaseException | None = None
    blocker: dict[str, object] | None = None
    b_only = bool(getattr(args, "frozen_a_root", None))
    ledger = _planned_ledger(b_only=b_only)
    write_json(args.result_root / "call-ledger.json", {"calls": ledger})
    final_rows: list[dict[str, object]] = []
    distribution: dict[str, object] | None = None
    comparison: dict[str, object] | None = None
    postrun_validation: dict[str, object] | None = None
    pass_a_status = "NOT_RUN"
    fundamental_status = "NOT_RUN"
    pass_b_status = "NOT_RUN"
    final_frozen_at: str | None = None

    try:
        if b_only:
            frozen_a, frozen_options = _load_frozen_a(args)
            _export_r1_source_proof(args.result_root)
            pass_a_status = "REUSED_FROZEN_PASS"
        package = _verify_package_manifest(args.package_root)
        sources = _verify_source_archives(args)
        integrity = _runtime_integrity(args)
        write_json(
            args.result_root / "source-base-code-equivalence.json",
            {"package": package, "sources": sources, "runtime": integrity},
        )
        require(package["status"] == "PASS", SOURCE_DRIFT)
        require(sources["status"] == "PASS", SOURCE_DRIFT)
        require(integrity["status"] == "PASS", SOURCE_DRIFT)

        source_packets, catalogs, archived_batches = m12db._load_archived_inputs(args.m12cx_root)
        chains = _source_chains(
            subjects=source_packets,
            catalogs=catalogs,
            r3_root=args.r3_root,
            generation_id=args.generation_id,
        )
        require(
            all(
                chain["source_identity_unchanged"]
                and chain["permission_semantics_unchanged"]
                and chain["execution_binding_rebased"]
                for chain in chains.values()
            ),
            SOURCE_DRIFT,
        )
        pass_a_contexts, source_contexts = _build_pass_a_contexts(
            subjects=source_packets,
            catalogs=catalogs,
            chains=chains,
            generation_id=args.generation_id,
        )
        baseline_a = _load_baseline_a_contexts(args.m12db_r1_root)
        parity = _a_semantic_parity(pass_a_contexts, baseline_a)
        write_json(args.result_root / "pass-a-substantive-semantic-parity.json", parity)
        require(parity["status"] == "PASS", SOURCE_DRIFT)
        leak = pass_a_leakage_scan(list(pass_a_contexts.values()))
        write_json(args.result_root / "pass-a-price-blindness.json", leak)
        require(leak["status"] == "PASS", SAFETY_FAILURE)

        request_root = args.result_root / "frozen-requests"
        a_captures = []
        unresolved_rows = []
        source_generation = _source_generation(chains)
        for spec in () if b_only else _batch_topology():
            market = str(spec["market"])
            batch = int(spec["batch"])
            batch_subjects = tuple(str(value) for value in spec["subjects"])
            a_captures.append(
                _request_capture(
                    root=request_root,
                    stage="pass-a",
                    market=market,
                    batch=batch,
                    subjects=batch_subjects,
                    contexts=pass_a_contexts,
                    catalogs=catalogs,
                    chains=chains,
                    generation_id=args.generation_id,
                    fixture_only=False,
                    raw_source_metadata_by_ticker={
                        ticker: source_packets[ticker]["decision_evidence"] for ticker in batch_subjects
                    },
                )
            )
            fixture = m12db._unresolved_fixture(batch_subjects, pass_a_contexts)
            normalized, materialization = materialize_future_pass_a(
                fixture,
                subjects=batch_subjects,
                subject_contexts=pass_a_contexts,
            )
            envelope = PassABatchOutput.model_validate(
                {
                    "contract": "m12cq-pass-a-archetype-regime-v1",
                    "generation_id": args.generation_id,
                    "packet_id": f"m12dc-preflight-{market}-batch-{batch:02d}",
                    "market": market,
                    "assessment_date": ASSESSMENT_DATE,
                    "classifications": normalized,
                }
            )
            final = validate_pass_a_batch(
                envelope,
                expected_identity={
                    "generation_id": args.generation_id,
                    "packet_id": f"m12dc-preflight-{market}-batch-{batch:02d}",
                    "market": market,
                    "assessment_date": ASSESSMENT_DATE,
                },
                subjects=batch_subjects,
                subject_contexts=pass_a_contexts,
                source_catalogs=catalogs,
                source_use_views={
                    ticker: chains[ticker]["projection"] for ticker in batch_subjects
                },
                source_use_bindings={
                    ticker: chains[ticker]["binding"] for ticker in batch_subjects
                },
                source_use_expectations={
                    ticker: chains[ticker]["expectation"] for ticker in batch_subjects
                },
                source_metadata_by_ticker={
                    ticker: source_packets[ticker]["decision_evidence"] for ticker in batch_subjects
                },
                source_generation_id=source_generation,
                execution_generation_id=args.generation_id,
                require_source_use=True,
            )
            unresolved_rows.append(
                {
                    "market": market,
                    "batch": batch,
                    "materialization": materialization,
                    "source_use": final,
                    "status": (
                        "PASS" if materialization["status"] == final["status"] == "PASS" else "FAIL"
                    ),
                }
            )
        write_json(
            args.result_root / "pass-a-honest-unresolved-preflight.json",
            {
                "rows": unresolved_rows,
                "status": (
                    "PASS" if all(row["status"] == "PASS" for row in unresolved_rows) else "FAIL"
                ),
            },
        )
        require(all(row["status"] == "PASS" for row in unresolved_rows), PREINFERENCE_BLOCKED)

        typed = _typed_states(source_packets)
        fixture_a = {
            ticker: source_packets[ticker]["frozen_pass_a_classification"]
            for ticker in _expected_tickers()
        }
        fixture_options = {
            ticker: source_packets[ticker]["deterministic_fundamental_option"]
            for ticker in _expected_tickers()
        }
        if b_only:
            fixture_a = {row["ticker"]: row for row in frozen_a}
            fixture_options = frozen_options
            _upstream_b_parity(
                args=args,
                source_packets=source_packets,
                catalogs=catalogs,
                typed=typed,
                frozen_a=frozen_a,
                frozen_options=frozen_options,
            )
        fixture_contexts, fixture_capabilities = _build_pass_b_inputs(
            source_contexts=source_contexts,
            source_packets=source_packets,
            catalogs=catalogs,
            chains=chains,
            pass_a_by_ticker=fixture_a,
            policy_options=fixture_options,
            typed=typed,
            generation_id=args.generation_id,
        )
        fixture_captures = [
            _request_capture(
                root=args.result_root / "preflight-fixture-requests",
                stage="pass-b",
                market=str(spec["market"]),
                batch=int(spec["batch"]),
                subjects=tuple(str(value) for value in spec["subjects"]),
                contexts=fixture_contexts,
                catalogs=catalogs,
                chains=chains,
                generation_id=args.generation_id,
                fixture_only=True,
                capabilities=fixture_capabilities,
                raw_source_metadata_by_ticker={
                    t: p["decision_evidence"] for t, p in source_packets.items()
                },
            )
            for spec in _batch_topology()
        ]
        fixture_validation = _validate_fixture_b(
            contexts=fixture_contexts,
            catalogs=catalogs,
            capabilities=fixture_capabilities,
            chains=chains,
            source_packets=source_packets,
            generation_id=args.generation_id,
        )
        crcl = _historical_crcl_control(
            m12cu_root=args.m12cu_root,
            catalogs=catalogs,
            capabilities=fixture_capabilities,
        )
        write_json(args.result_root / "preflight-fixture-b-consumer-chain.json", fixture_validation)
        write_json(args.result_root / "historical-crcl-negative-control.json", crcl)
        require(fixture_validation["status"] == "PASS", PREINFERENCE_BLOCKED)
        require(crcl["status"] == "PASS", PREINFERENCE_BLOCKED)

        if b_only:
            _decisive_ref_parity(
                contexts=fixture_contexts,
                catalogs=catalogs,
                capabilities=fixture_capabilities,
                chains=chains,
                captures=fixture_captures,
                source_packets=source_packets,
                upstream_root=args.frozen_a_root,
                result_root=args.result_root,
                generation_id=args.generation_id,
            )
        precall_validation = _run_validation(args.result_root, phase="precall", full=b_only)
        write_json(args.result_root / "precall-validation-summary.json", precall_validation)
        require(precall_validation["status"] == "PASS", PREINFERENCE_BLOCKED)
        runtime, codex_bin, transport = _prepare_execution_environment(args, scratch)
        write_json(args.result_root / "transport-model-config-freeze.json", transport)
        code_hashes = {path: sha256_file(REPO / path) for path in CODE_PATHS}
        plan = {
            "contract": "m12dc-finite-execution-driver-argument-plan-v1",
            "generation_id": args.generation_id,
            "implementation_commit": args.expected_head,
            "work_instruction_commit": args.work_instruction_commit,
            "model": MODEL,
            "effort": EFFORT,
            "timeout_seconds": TIMEOUT_SECONDS,
            "mode": R1_MODE if b_only else "FRESH_A_AND_B",
            "planned_a_calls": 0 if b_only else 8,
            "planned_b_calls": 8,
            "retry": 0,
            "fallback": 0,
            "judge": 0,
            "repair": 0,
            "source_generation_id": source_generation,
            "code_hashes": code_hashes,
            "pass_a_requests": [
                {
                    "market": row["market"],
                    "batch": row["batch"],
                    "subjects": row["subjects"],
                    "request_sha256": row["request_sha256"],
                }
                for row in a_captures
            ],
            "fixture_b_request_count": len(fixture_captures),
            "archived_batch_count": len(archived_batches),
            "status": "PASS",
        }
        write_json(args.result_root / "execution-driver-argument-plan.json", plan)
        write_json(
            args.result_root / "pass-a-request-freeze-manifest.json",
            {
                "contract": "m12dc-pass-a-request-freeze-manifest-v1",
                "generation_id": args.generation_id,
                "request_count": len(a_captures),
                "requests": a_captures,
                "frozen_at": datetime.now(UTC).isoformat(),
                "status": "PASS",
            },
        )
        freeze = {
            "contract": "m12dc-pre-inference-execution-freeze-v1",
            "generation_id": args.generation_id,
            "plan_sha256": sha256_file(args.result_root / "execution-driver-argument-plan.json"),
            "pass_a_request_manifest_sha256": sha256_file(
                args.result_root / "pass-a-request-freeze-manifest.json"
            ),
            "source_base_sha256": sha256_file(
                args.result_root / "source-base-code-equivalence.json"
            ),
            "transport_config_sha256": sha256_file(
                args.result_root / "transport-model-config-freeze.json"
            ),
            "substantive_a_parity_sha256": sha256_file(
                args.result_root / "pass-a-substantive-semantic-parity.json"
            ),
            "precall_validation_sha256": sha256_file(
                args.result_root / "precall-validation-summary.json"
            ),
            "frozen_at": datetime.now(UTC).isoformat(),
            "status": "PASS",
        }
        write_json(args.result_root / "pre-inference-execution-freeze.json", freeze)
        _assert_execution_freeze(args.expected_head, code_hashes)

        stage = "PASS_A"
        pass_a_rows = (
            frozen_a
            if b_only
            else _run_pass_a(
                pass_a_contexts=pass_a_contexts,
                catalogs=catalogs,
                chains=chains,
                source_packets=source_packets,
                request_root=request_root,
                result_root=args.result_root,
                generation_id=args.generation_id,
                runtime=runtime,
                codex_bin=codex_bin,
                expected_head=args.expected_head,
                code_hashes=code_hashes,
                ledger=ledger,
            )
        )
        pass_a_status = "REUSED_FROZEN_PASS" if b_only else "PASS"

        stage = "POST_A_MATERIALIZATION"
        m12cp = _load_m12cp(args.m12cp_zip)
        matrix = _matrix_subjects(m12cp["options"])
        pass_a_by_ticker = {str(row["ticker"]): row for row in pass_a_rows}
        options = (
            frozen_options
            if b_only
            else _materialize_options(
                pass_a_rows=pass_a_rows,
                matrix=matrix,
                typed=typed,
                result_root=args.result_root,
                generation_id=args.generation_id,
            )
        )
        b_contexts, capabilities = _build_pass_b_inputs(
            source_contexts=source_contexts,
            source_packets=source_packets,
            catalogs=catalogs,
            chains=chains,
            pass_a_by_ticker=pass_a_by_ticker,
            policy_options=options,
            typed=typed,
            generation_id=args.generation_id,
        )
        b_captures = [
            _request_capture(
                root=request_root,
                stage="pass-b",
                market=str(spec["market"]),
                batch=int(spec["batch"]),
                subjects=tuple(str(value) for value in spec["subjects"]),
                contexts=b_contexts,
                catalogs=catalogs,
                chains=chains,
                generation_id=args.generation_id,
                fixture_only=False,
                capabilities=capabilities,
                raw_source_metadata_by_ticker={
                    t: p["decision_evidence"] for t, p in source_packets.items()
                },
            )
            for spec in _batch_topology()
        ]
        write_json(
            args.result_root / "pass-b-request-freeze-manifest.json",
            {
                "contract": "m12dc-pass-b-request-freeze-manifest-v1",
                "generation_id": args.generation_id,
                "pass_a_aggregate_sha256": sha256_file(
                    args.result_root / "pass-a-22-subject-classification.json"
                ),
                "request_count": len(b_captures),
                "requests": b_captures,
                "capability_sha256": canonical_sha256(capabilities),
                "frozen_at": datetime.now(UTC).isoformat(),
                "status": "PASS",
            },
        )
        _assert_execution_freeze(args.expected_head, code_hashes)
        fundamental_status = "PASS"

        stage = "PASS_B"
        pass_b_rows, entry_rows = _run_pass_b(
            contexts=b_contexts,
            capabilities=capabilities,
            catalogs=catalogs,
            chains=chains,
            source_packets=source_packets,
            pass_a_by_ticker=pass_a_by_ticker,
            policy_options=options,
            typed=typed,
            request_root=request_root,
            result_root=args.result_root,
            generation_id=args.generation_id,
            runtime=runtime,
            codex_bin=codex_bin,
            expected_head=args.expected_head,
            code_hashes=code_hashes,
            ledger=ledger,
        )
        pass_b_status = "PASS"

        stage = "FINAL_FREEZE"
        final_rows = _finalize_rows(
            pass_a_rows=pass_a_rows,
            pass_b_rows=pass_b_rows,
            entry_rows=entry_rows,
            options=options,
            typed=typed,
            source_packets=source_packets,
        )
        consistency = []
        entries = {str(row["ticker"]): row["entry_range"] for row in entry_rows}
        pass_b_by_ticker = {str(row["ticker"]): row for row in pass_b_rows}
        for ticker in _expected_tickers():
            result = validate_new_buyer_consistency(
                decision=pass_b_by_ticker[ticker],
                policy_option=options[ticker],
                entry_range=entries[ticker],
                catalog=catalogs[ticker],
                capability=capabilities[ticker],
            )
            require(result["status"] == "PASS", f"final_consistency:{ticker}")
            consistency.append(result)
        write_json(
            args.result_root / "final-22-source-use-aware-results.json",
            {
                "contract": "m12dc-final-22-source-use-aware-results-v1",
                "generation_id": args.generation_id,
                "subject_count": len(final_rows),
                "pass_a_origin": UPSTREAM_GENERATION if b_only else args.generation_id,
                "mode": R1_MODE if b_only else "FRESH_A_AND_B",
                "candidates": final_rows,
            },
        )
        write_json(
            args.result_root / "final-new-buyer-consistency.json",
            {"rows": consistency, "status": "PASS"},
        )
        distribution = _distribution(final_rows)
        write_json(
            args.result_root / "final-distributions-and-wait-explanations.json", distribution
        )
        final_frozen_at = datetime.now(UTC).isoformat()
        write_json(
            args.result_root / "final-output-freeze-manifest.json",
            {
                "contract": "m12dc-final-output-freeze-manifest-v1",
                "generation_id": args.generation_id,
                "subject_count": len(final_rows),
                "aggregate_sha256": sha256_file(
                    args.result_root / "final-22-source-use-aware-results.json"
                ),
                "pass_a_sha256": sha256_file(
                    args.result_root / "pass-a-22-subject-classification.json"
                ),
                "pass_b_sha256": sha256_file(args.result_root / "pass-b-22-subject-decisions.json"),
                "frozen_at": final_frozen_at,
                "status": "PASS",
            },
        )

        stage = "POST_FREEZE_COMPARISON"
        comparison = _post_freeze_comparison(
            rows=final_rows,
            supplemental_root=args.supplemental_root,
        )
        write_json(args.result_root / "post-freeze-descriptive-comparison.json", comparison)

        stage = "POSTRUN_VALIDATION"
        postrun_validation = _run_validation(args.result_root, phase="postrun")
        write_json(args.result_root / "postrun-validation-summary.json", postrun_validation)
        require(postrun_validation["status"] == "PASS", POSTRUN_INCOMPLETE)
        terminal = PASS
    except BaseException as exc:  # noqa: BLE001
        terminal_error = exc
        code = str(exc).split(":", 1)[0]
        if code in {SOURCE_DRIFT, SAFETY_FAILURE}:
            terminal = code
        elif stage == "PASS_A":
            terminal = PASS_A_FAILED
            pass_a_status = "FAIL"
        elif stage == "POST_A_MATERIALIZATION":
            terminal = POST_A_BLOCKED
            fundamental_status = "FAIL"
        elif stage == "PASS_B":
            terminal = PASS_B_FAILED
            pass_b_status = "FAIL"
        elif stage == "POSTRUN_VALIDATION":
            terminal = POSTRUN_INCOMPLETE
        else:
            terminal = PREINFERENCE_BLOCKED
        pending = next(
            (row for row in reversed(ledger) if row["status"] == "RESPONSE_RECEIVED"), None
        )
        if pending is not None:
            pending.update(
                {
                    "status": "FAIL",
                    "failure_stage": stage,
                    "safe_error_code": code,
                    "first_error": str(exc),
                    "semantic_accepted": False,
                    "completed_at": datetime.now(UTC).isoformat(),
                }
            )
        failed_call = next((row for row in reversed(ledger) if row["status"] == "FAIL"), None)
        blocker = {
            "stage": stage,
            "safe_error_type": type(exc).__name__,
            "safe_error_code": code,
            "first_error": str(exc),
            "failed_call": failed_call,
        }
        write_text(args.result_root / "failure-traceback.txt", traceback.format_exc())
    finally:
        shutil.rmtree(scratch, ignore_errors=True)

    completion = {
        "contract": "m12dc-program-completion-v1",
        "terminal": terminal,
        "generation_id": args.generation_id,
        "implementation_commit": args.expected_head,
        "work_instruction_commit": args.work_instruction_commit,
        "source_generation_id": (_source_generation(chains) if "chains" in locals() else None),
        "offline_request_preflight_status": (
            "PASS"
            if terminal not in {PREINFERENCE_BLOCKED, SOURCE_DRIFT, SAFETY_FAILURE}
            else "FAIL"
        ),
        "pass_a_status": pass_a_status,
        "fundamental_and_capability_status": fundamental_status,
        "pass_b_status": pass_b_status,
        "postrun_validation_status": (postrun_validation or {}).get("status", "NOT_RUN"),
        "semantic_trial_complete": terminal in {PASS, POSTRUN_INCOMPLETE},
        "single_attempt_execution_complete": terminal in {PASS, POSTRUN_INCOMPLETE},
        "subject_count": len(final_rows),
        "mode": R1_MODE if b_only else "FRESH_A_AND_B",
        "accepted_a_fixture_subjects": len(frozen_a) if b_only and "frozen_a" in locals() else 0,
        "newly_accepted_b_subjects": sum(
            len(row["subjects"])
            for row in ledger
            if row["stage"] == "pass-b" and row["semantic_accepted"]
        ),
        "wrapper_attempted_calls": sum(bool(row["wrapper_attempted"]) for row in ledger),
        "usable_final_responses": sum(bool(row["usable_final_response"]) for row in ledger),
        "semantic_accepted_calls": sum(bool(row["semantic_accepted"]) for row in ledger),
        "retry_calls": 0,
        "fallback_calls": 0,
        "judge_calls": 0,
        "repair_calls": 0,
        "final_frozen_at": final_frozen_at,
        "deployment_authorized": False,
        "blocker": blocker,
        "completed_at": datetime.now(UTC).isoformat(),
    }
    if b_only:
        completion["terminal"] = {
            PASS: "M12DC_R1_FROZEN_A_PASS_B_PER_USE_REF_REPROOF_PASS_READY_FOR_CHAT_REVIEW",
            PASS_B_FAILED: "M12DC_R1_PASS_B_FAILED",
            POSTRUN_INCOMPLETE: "M12DC_R1_ANALYTICAL_PASS_POSTRUN_VALIDATION_INCOMPLETE",
            SOURCE_DRIFT: "M12DC_R1_SOURCE_OR_A_SEMANTIC_DRIFT_REQUIRES_CHAT",
            PREINFERENCE_BLOCKED: "M12DC_R1_OFFLINE_REF_ENUM_PARITY_GAP",
        }.get(terminal, "M12DC_R1_EXECUTION_PATH_OR_TRANSPORT_BLOCKED")
        if blocker and blocker["safe_error_code"].startswith("M12DC_R1_"):
            completion["terminal"] = blocker["safe_error_code"]
    write_json(args.result_root / "call-ledger.json", {"calls": ledger})
    write_json(args.result_root / "program-completion.json", completion)
    write_json(
        args.result_root / "safety-counters.json",
        {
            "external_inference_wrapper_attempts": completion["wrapper_attempted_calls"],
            "maximum_authorized": 8 if b_only else 16,
            "retry_calls": 0,
            "fallback_calls": 0,
            "judge_calls": 0,
            "repair_calls": 0,
            "financial_source_network_reads": 0,
            "market_refreshes": 0,
            "production_db_writes": 0,
            "production_notifications": 0,
            "production_intents": 0,
            "scheduler_changes": 0,
            "broker_operations": 0,
            "operating_checkout_changes": 0,
            "main_merges": 0,
            "remote_pushes": 0,
            "deployments": 0,
            "status": "PASS",
        },
    )
    write_text(
        args.result_root / "REPORT.md",
        _report(
            completion=completion,
            ledger=ledger,
            distribution=distribution,
            comparison=comparison,
            validation=postrun_validation,
        ),
    )
    if b_only:
        shutil.copy2(
            args.result_root / "REPORT.md",
            args.result_root / "DECISIVE_REF_PARITY_AND_B_REPROOF_RESULT.md",
        )
    write_json(args.result_root / "artifact-manifest.json", _artifact_manifest(args.result_root))
    args.output_zip.parent.mkdir(parents=True, exist_ok=True)
    archive = _zip_tree(args.result_root, args.output_zip)
    sidecar = args.output_zip.with_suffix(args.output_zip.suffix + ".sha256")
    write_text(sidecar, archive["sha256"])
    print(json.dumps({"completion": completion, "archive": archive}, ensure_ascii=False, indent=2))
    if terminal_error is not None:
        raise SystemExit(1)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--package-zip", type=Path, required=True)
    parser.add_argument("--package-root", type=Path, required=True)
    parser.add_argument("--m12db-r1-root", type=Path, required=True)
    parser.add_argument("--r3-root", type=Path, required=True)
    parser.add_argument("--m12cx-root", type=Path, required=True)
    parser.add_argument("--supplemental-root", type=Path, required=True)
    parser.add_argument("--m12cu-root", type=Path, required=True)
    parser.add_argument("--m12cp-zip", type=Path, required=True)
    parser.add_argument("--result-root", type=Path, required=True)
    parser.add_argument("--output-zip", type=Path, required=True)
    parser.add_argument("--expected-head", required=True)
    parser.add_argument("--work-instruction-commit", required=True)
    parser.add_argument("--generation-id", required=True)
    parser.add_argument("--env-file", type=Path, required=True)
    parser.add_argument("--timeout", type=int, default=TIMEOUT_SECONDS)
    parser.add_argument("--frozen-a-root", type=Path)
    parser.add_argument("--upstream-report-zip", type=Path)
    return parser.parse_args()


if __name__ == "__main__":
    run(parse_args())
