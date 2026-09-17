from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import tempfile
import zipfile
from collections import Counter
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from scripts.m12cn_policy_contract import ShadowBatchOutput, validate_shadow_batch
from scripts.m12cn_policy_shadow import (
    M12CNFailure,
    classify_shadow_failure,
    runtime_integrity,
)
from scripts.m12co_entry_range_contract import (
    CONTRACT,
    MethodFamily,
    archetype_method_applicability_matrix,
    build_subject_candidate_coverage,
    field_ownership_audit,
    generic_materialization_control_matrix,
    valuation_method_source_contracts,
)


REPO = Path(__file__).resolve().parents[1]
EXPECTED_R2_ZIP_SHA256 = "5f26ad263cf29ef5a3b18c856c6eafc7b74894367e6444e868014dff304c8b37"
EXPECTED_R2_HARNESS = "c4cfb0f2c1ed4326587fac0c493a463beeb2bd0b"
EXPECTED_RUNTIME_BASE = "831890d1bf0dff303f67a6e0de1403ad3221b5d8"
WORK_INSTRUCTION_COMMIT = "965e804d803fd79339129774a1f379362f586b01"
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
R2_REPORT_NAME = (
    "thesis-monitor-20260917-m12cn-r2-structured-output-schema-completeness-"
    "repair-fresh-shadow-report.zip"
)
COMPLETION_READY = "M12CO_ENTRY_RANGE_METHOD_COVERAGE_READY_FOR_CHAT_POLICY_SELECTION"
COMPLETION_OWNERSHIP_GAP = "M12CO_ENTRY_RANGE_OWNERSHIP_DESIGN_GAP"
COMPLETION_COVERAGE_INSUFFICIENT = "M12CO_SAFE_FUNDAMENTAL_METHOD_COVERAGE_INSUFFICIENT"
COMPLETION_FAILED = "M12CO_OFFLINE_DESIGN_FAILED"


class M12COFailure(RuntimeError):
    pass


def require(condition: bool, code: str) -> None:
    if not condition:
        raise M12COFailure(code)


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise M12COFailure(f"expected_json_object:{path}")
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


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_sha256(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        ).encode("utf-8")
    ).hexdigest()


def _zip_member(archive: zipfile.ZipFile, suffix: str) -> bytes:
    names = [name for name in archive.namelist() if name.endswith(suffix)]
    if len(names) != 1:
        raise M12COFailure(f"zip_member_count_invalid:{suffix}:{len(names)}")
    return archive.read(names[0])


def _zip_json(archive: zipfile.ZipFile, suffix: str) -> dict[str, Any]:
    value = json.loads(_zip_member(archive, suffix))
    if not isinstance(value, dict):
        raise M12COFailure(f"zip_json_not_object:{suffix}")
    return value


def verify_package_and_r2_report(package_root: Path) -> dict[str, object]:
    manifest = read_json(package_root / "package-manifest.json")
    file_rows = manifest.get("files")
    require(isinstance(file_rows, list), "package_manifest_files_missing")
    errors: list[str] = []
    for row in file_rows:
        if not isinstance(row, Mapping):
            errors.append("package_manifest_row_invalid")
            continue
        path = package_root / str(row.get("path") or "")
        if not path.is_file():
            errors.append(f"package_file_missing:{row.get('path')}")
            continue
        if path.stat().st_size != row.get("size"):
            errors.append(f"package_size_mismatch:{row.get('path')}")
        if sha256_file(path) != row.get("sha256"):
            errors.append(f"package_hash_mismatch:{row.get('path')}")
    report_zip = package_root / "sources" / R2_REPORT_NAME
    report_hash = sha256_file(report_zip)
    if report_hash != EXPECTED_R2_ZIP_SHA256:
        errors.append("r2_report_zip_hash_mismatch")
    declared = 0
    verified = 0
    with zipfile.ZipFile(report_zip) as archive:
        artifact_manifest = _zip_json(archive, "/artifact-manifest.json")
        rows = artifact_manifest.get("files")
        if isinstance(rows, list):
            declared = len(rows)
            by_suffix = {name.split("/", 1)[-1]: name for name in archive.namelist()}
            for row in rows:
                if not isinstance(row, Mapping):
                    continue
                relative = str(row.get("path") or "")
                name = by_suffix.get(relative)
                if name is None:
                    errors.append(f"r2_artifact_missing:{relative}")
                    continue
                raw = archive.read(name)
                if len(raw) != row.get("size"):
                    errors.append(f"r2_artifact_size_mismatch:{relative}")
                    continue
                if hashlib.sha256(raw).hexdigest() != row.get("sha256"):
                    errors.append(f"r2_artifact_hash_mismatch:{relative}")
                    continue
                verified += 1
    if declared != 94 or verified != 94:
        errors.append(f"r2_manifest_verification_count:{declared}:{verified}")
    return {
        "contract": "m12co-source-base-integrity-v1",
        "package_payload_count": len(file_rows),
        "r2_report_zip_sha256": report_hash,
        "expected_r2_report_zip_sha256": EXPECTED_R2_ZIP_SHA256,
        "r2_manifest_declared_count": declared,
        "r2_manifest_verified_count": verified,
        "errors": errors,
        "status": "PASS" if not errors else "FAIL",
    }


def r2_semantic_failure_reproducer(report_zip: Path) -> dict[str, object]:
    with zipfile.ZipFile(report_zip) as archive:
        raw = _zip_json(archive, "/shadow-calls/us/batch-03/raw-output.json")
        archived_validation = _zip_json(
            archive,
            "/shadow-calls/us/batch-03/semantic-validation.json",
        )
        identity = _zip_json(archive, "/shadow-model-inputs/us/batch-03/identity.json")
        ref_catalog = _zip_json(archive, "/shadow-model-inputs/us/batch-03/ref-catalog.json")
    parsed = ShadowBatchOutput.model_validate(raw)
    reproduced = validate_shadow_batch(
        parsed,
        expected_identity=identity,
        subjects=identity["expected_subjects"],
        catalogs=ref_catalog["catalogs"],
    )
    expected = [
        "MU:unresolved_fundamental_metadata_present",
        "SKHY:unresolved_fundamental_metadata_present",
    ]
    return {
        "contract": "m12co-r2-semantic-failure-reproducer-v1",
        "archived_errors": archived_validation.get("errors"),
        "reproduced_errors": reproduced.get("errors"),
        "expected_errors": expected,
        "provider_output_was_complete": len(parsed.candidates) == 3,
        "weakened_validator": False,
        "status": (
            "PASS"
            if archived_validation.get("errors") == expected
            and reproduced.get("errors") == expected
            else "FAIL"
        ),
    }


def failure_category_correction(report_zip: Path) -> dict[str, object]:
    with zipfile.ZipFile(report_zip) as archive:
        r2_log = _zip_member(archive, "/shadow-calls/us/batch-03/transport.log")
        ledger = _zip_json(archive, "/shadow-call-ledger.json")
    with tempfile.TemporaryDirectory(prefix="m12co-failure-classification-") as temporary:
        root = Path(temporary)
        r2_path = root / "r2.log"
        r2_path.write_bytes(r2_log)
        r2_category = classify_shadow_failure(
            M12CNFailure("shadow_semantic_validation_failed"),
            r2_path,
            execution_stage="SEMANTIC_VALIDATION",
        )
        r1_path = root / "r1.log"
        r1_path.write_text(
            'prefix\nERROR: {"error":{"type":"invalid_request_error",'
            '"code":"invalid_json_schema","message":"schema missing items"},'
            '"status":400}\n',
            encoding="utf-8",
        )
        r1_category = classify_shadow_failure(
            RuntimeError("OTHER_TRANSPORT_FAILURE:attempts=1"),
            r1_path,
        )
        unrelated = root / "unrelated.log"
        unrelated.write_text(
            "source context says rate limit, quota, and 429 as ordinary words",
            encoding="utf-8",
        )
        unrelated_category = classify_shadow_failure(RuntimeError("local failure"), unrelated)
    archived_batch = next(row for row in ledger["calls"] if row.get("ordinal") == 3)
    checks = {
        "r1_provider_schema_error": r1_category == "SCHEMA_REJECTED_PRE_INFERENCE",
        "r2_semantic_validation": r2_category == "SEMANTIC_VALIDATION_FAILED",
        "unrelated_source_words_ignored": unrelated_category == "OTHER_DOCUMENTED_FAILURE",
    }
    return {
        "contract": "m12co-r2-failure-category-correction-v1",
        "archived_r2_category": archived_batch.get("failure_category"),
        "corrected_r2_category": r2_category,
        "r1_replay_category": r1_category,
        "unrelated_source_text_category": unrelated_category,
        "checks": checks,
        "production_transport_taxonomy_changed": False,
        "status": "PASS" if all(checks.values()) else "FAIL",
    }


def _contexts(shadow_input_root: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for market in ("us", "kr"):
        context = read_json(shadow_input_root / market / "context.json")
        require(
            tuple(context.get("selected_subjects") or []) == EXPECTED_POPULATION[market],
            f"{market}_population_mismatch",
        )
        packets = {
            str(row.get("ticker") or ""): row
            for row in context.get("evidence_packets") or []
            if isinstance(row, Mapping)
        }
        ownership = {
            str(row.get("ticker") or ""): row
            for row in context.get("evidence_ownership") or []
            if isinstance(row, Mapping)
        }
        for ticker in EXPECTED_POPULATION[market]:
            rows.append(
                build_subject_candidate_coverage(
                    market=market,
                    packet=packets[ticker],
                    ownership=ownership[ticker],
                )
            )
    return rows


def _candidate_coverage(rows: Sequence[Mapping[str, object]]) -> dict[str, object]:
    family_subjects: Counter[str] = Counter()
    family_candidates: Counter[str] = Counter()
    disagreement = Counter()
    generally_applicable: dict[str, set[str]] = {}
    conditionally_applicable: dict[str, set[str]] = {}
    for row in rows:
        families = set(row.get("safe_method_families") or [])
        for family in families:
            family_subjects[str(family)] += 1
        for candidate in row.get("fundamental_candidates") or []:
            family_candidates[str(candidate["method_family"])] += 1
            for archetype in candidate.get("generally_meaningful_archetypes") or []:
                generally_applicable.setdefault(str(archetype), set()).add(str(row["ticker"]))
            for archetype in candidate.get("conditionally_meaningful_archetypes") or []:
                conditionally_applicable.setdefault(str(archetype), set()).add(str(row["ticker"]))
        disagreement[str(row["method_disagreement"]["status"])] += 1
    any_safe = sum(bool(row.get("fundamental_candidates")) for row in rows)
    return {
        "contract": "m12co-fundamental-entry-candidate-coverage-v1",
        "subject_count": len(rows),
        "any_safe_fundamental_candidate_subject_count": any_safe,
        "no_safe_fundamental_method_subject_count": len(rows) - any_safe,
        "historical_trailing_pe_candidate_subject_count": family_subjects[
            MethodFamily.HISTORICAL_TRAILING_PE_QUANTILE.value
        ],
        "historical_pb_candidate_subject_count": family_subjects[
            MethodFamily.HISTORICAL_PB_QUANTILE.value
        ],
        "forward_book_candidate_subject_count": 0,
        "execution_growth_candidate_subject_count": 0,
        "candidate_count": sum(family_candidates.values()),
        "candidate_count_by_family": dict(sorted(family_candidates.items())),
        "method_disagreement_status_counts": dict(sorted(disagreement.items())),
        "subject_count_by_generally_applicable_archetype": {
            key: len(value) for key, value in sorted(generally_applicable.items())
        },
        "subject_count_by_conditionally_applicable_archetype": {
            key: len(value) for key, value in sorted(conditionally_applicable.items())
        },
        "multi_safe_method_subject_count": sum(
            len(row.get("safe_method_families") or []) > 1 for row in rows
        ),
        "tactical_candidate_subject_count": sum(
            int(row.get("tactical_candidate_count") or 0) > 0 for row in rows
        ),
        "arbitrary_current_price_discount_count": 0,
        "status": "PASS" if len(rows) == 22 and any_safe > 0 else "FAIL",
    }


def _feasibility_matrix(rows: Sequence[Mapping[str, object]]) -> dict[str, object]:
    matrix = []
    for row in rows:
        for method in row["method_feasibility"]:
            matrix.append(
                {
                    "market": row["market"],
                    "ticker": row["ticker"],
                    **method,
                }
            )
    return {
        "contract": "m12co-valuation-method-feasibility-matrix-v1",
        "row_count": len(matrix),
        "rows": matrix,
        "status": "PASS",
    }


def _execution_growth_coverage(rows: Sequence[Mapping[str, object]]) -> dict[str, object]:
    execution_families = {
        MethodFamily.EV_SALES_SCENARIO.value,
        MethodFamily.EV_GROSS_PROFIT_SCENARIO.value,
        MethodFamily.EV_EBITDA_SCENARIO.value,
        MethodFamily.FCF_SCENARIO.value,
    }
    output = []
    for row in rows:
        methods = [
            method
            for method in row["method_feasibility"]
            if method["method_family"] in execution_families
        ]
        output.append({"market": row["market"], "ticker": row["ticker"], "methods": methods})
    return {
        "contract": "m12co-execution-growth-method-input-coverage-v1",
        "subject_count": len(output),
        "arithmetically_feasible_subject_count": sum(
            any(method["arithmetic_feasible"] for method in row["methods"]) for row in output
        ),
        "rows": output,
        "prose_or_ticker_inference_used": False,
        "status": "PASS",
    }


def _discount_prohibition(rows: Sequence[Mapping[str, object]]) -> dict[str, object]:
    checked = 0
    errors = []
    for row in rows:
        for candidate in row["fundamental_candidates"]:
            checked += 1
            inputs = candidate["formula_inputs"]
            denominator = float(inputs["denominator_value"])
            expected_low = round(denominator * float(inputs["multiple_low"]), 6)
            expected_high = round(denominator * float(inputs["multiple_high"]), 6)
            if round(float(candidate["low"]), 6) != expected_low:
                errors.append(f"low_formula_mismatch:{row['ticker']}:{candidate['candidate_id']}")
            if round(float(candidate["high"]), 6) != expected_high:
                errors.append(f"high_formula_mismatch:{row['ticker']}:{candidate['candidate_id']}")
            if "current_price" in inputs:
                errors.append(f"current_price_formula_input:{candidate['candidate_id']}")
    return {
        "contract": "m12co-current-price-discount-prohibition-proof-v1",
        "candidate_count_checked": checked,
        "current_price_used_in_candidate_formula_count": sum(
            error.startswith("current_price_formula_input") for error in errors
        ),
        "arbitrary_current_price_discount_count": 0,
        "formula_mismatch_count": len(errors),
        "errors": errors,
        "status": "PASS" if not errors else "FAIL",
    }


def _draft_materialization_contract(ownership: Mapping[str, object]) -> dict[str, object]:
    return {
        "contract": "m12co-entry-selection-materialization-draft-contract-v1",
        "status": "DRAFT_READY_FOR_CHAT_REVIEW",
        "model_output_for_wait": {
            "fundamental_choice": "candidate_id | UNRESOLVED",
            "tactical_choice": "candidate_id | UNRESOLVED",
            "re_evaluate_conditions": "up to 3 nonnumeric strings, each at most 300 characters",
        },
        "model_output_for_non_wait": "no entry-range selection",
        "runtime_materializes": [
            row["field"]
            for row in ownership["fields"]
            if str(row["owner"]).startswith("DETERMINISTIC_")
        ],
        "fail_closed_rules": [
            "nonexistent candidate ID",
            "cross-ticker candidate ID",
            "tactical candidate used as fundamental price",
            "non-WAIT candidate injection",
            "numeric re-evaluation prose",
        ],
        "current_shadow_contract_replaced": False,
    }


def _builder_contract() -> dict[str, object]:
    return {
        "contract": CONTRACT,
        "candidate_id": "sha256(ticker + method + quantile band + canonical inputs)[:24]",
        "emitted_method_families": [
            MethodFamily.HISTORICAL_TRAILING_PE_QUANTILE.value,
            MethodFamily.HISTORICAL_PB_QUANTILE.value,
        ],
        "quantile_bands": ["P25_P50", "P50_P75", "P75_P90"],
        "final_preferred_option_selected": False,
        "current_price_formula_input_allowed": False,
        "technical_candidate_as_fundamental_allowed": False,
        "production_contract_changed": False,
    }


def _report_markdown(
    *,
    expected_head: str,
    coverage: Mapping[str, object],
    rows: Sequence[Mapping[str, object]],
    failure_correction: Mapping[str, object],
) -> str:
    lines = [
        "# M12CO Fundamental Entry Range Method Coverage And Materialization Ownership",
        "",
        f"**Completion:** `{COMPLETION_READY}`",
        "",
        "## Boundary",
        "",
        "- External model calls: `0`",
        "- Market refresh: `0`",
        "- Production runtime/config changes: `0`",
        "- Main merge/push/deploy: `0`",
        "- This output is diagnostic entry-candidate evidence, not a target-price policy.",
        "",
        "## Provenance",
        "",
        f"- Work/implementation commit: `{expected_head}`",
        f"- Work-instruction commit: `{WORK_INSTRUCTION_COMMIT}`",
        f"- Required runtime base: `{EXPECTED_RUNTIME_BASE}`",
        f"- R2 harness: `{EXPECTED_R2_HARNESS}`",
        f"- Frozen M12CM generation: `{EXPECTED_FROZEN_GENERATION}`",
        "",
        "## Coverage",
        "",
        f"- Subjects: `{coverage['subject_count']}`",
        "- Any safe arithmetic candidate: "
        f"`{coverage['any_safe_fundamental_candidate_subject_count']}`",
        "- Historical trailing-P/E: "
        f"`{coverage['historical_trailing_pe_candidate_subject_count']}` subjects",
        f"- Historical P/B: `{coverage['historical_pb_candidate_subject_count']}` subjects",
        f"- Candidate bands: `{coverage['candidate_count']}`",
        f"- No safe method: `{coverage['no_safe_fundamental_method_subject_count']}`",
        f"- Multi-method: `{coverage['multi_safe_method_subject_count']}`",
        "- Arbitrary current-price discounts: `0`",
        "",
        "## Subject Results",
        "",
        "| Market | Ticker | Safe methods | Candidate bands | Method relation |",
        "|---|---:|---|---:|---|",
    ]
    for row in rows:
        methods = ", ".join(row["safe_method_families"]) or "none"
        lines.append(
            f"| {row['market']} | {row['ticker']} | {methods} | "
            f"{row['fundamental_candidate_count']} | {row['method_disagreement']['status']} |"
        )
    lines.extend(
        [
            "",
            "## Ownership",
            "",
            "The next draft contract gives the model only fundamental/tactical candidate-ID choices "
            "and bounded nonnumeric re-evaluation prose. Runtime projects all prices, refs, statuses, "
            "methods, assumptions, and unresolved reasons.",
            "",
            "## R2 Reporting Correction",
            "",
            f"- Archived category: `{failure_correction['archived_r2_category']}`",
            f"- Correct category: `{failure_correction['corrected_r2_category']}`",
            "- Production transport taxonomy changes: `0`",
            "",
            "## Chat Policy Decisions Still Required",
            "",
            "- Select percentile policy by archetype without ticker rules.",
            "- Decide how structural rerating and cycle normalization affect historical bands.",
            "- Decide whether P/B is economically meaningful for asset-light and execution-growth cases.",
            "- Add explicit forward-book or growth-scenario basis contracts before those methods can emit.",
            "",
            "## Decision Boundary",
            "",
            "Ready means Chat has enough deterministic evidence to choose a later shadow policy. "
            "It does not authorize M12CN-R3, production integration, delivery, or deployment.",
        ]
    )
    return "\n".join(lines)


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
        "contract": "m12co-artifact-manifest-v1",
        "file_count": len(files),
        "files": files,
        "manifest_payload_sha256": canonical_sha256(files),
    }


def zip_tree(source: Path, destination: Path) -> None:
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(source.rglob("*")):
            if path.is_file():
                archive.write(path, f"{source.name}/{path.relative_to(source)}")
    temporary.replace(destination)


def run(args: argparse.Namespace) -> None:
    result_root = args.result_root.resolve()
    require(not result_root.exists(), "result_root_already_exists")
    result_root.mkdir(parents=True)
    terminal = COMPLETION_FAILED
    open_blockers: list[dict[str, object]] = []
    try:
        source_integrity = verify_package_and_r2_report(args.package_root.resolve())
        runtime = runtime_integrity(args.expected_head)
        source_integrity["runtime_integrity"] = runtime
        source_integrity["required_runtime_base"] = EXPECTED_RUNTIME_BASE
        source_integrity["r2_harness_commit"] = EXPECTED_R2_HARNESS
        source_integrity["status"] = (
            "PASS"
            if source_integrity["status"] == "PASS" and runtime["status"] == "PASS"
            else "FAIL"
        )
        write_json(result_root / "source-base-integrity.json", source_integrity)
        require(source_integrity["status"] == "PASS", "source_or_runtime_integrity_failed")

        input_freeze = read_json(args.shadow_input_root / "input-freeze.json")
        require(
            input_freeze.get("generation_id") == EXPECTED_FROZEN_GENERATION,
            "frozen_generation_mismatch",
        )
        validation = read_json(args.validation_root / "validation-summary.json")
        require(validation.get("status") == "PASS", "validation_not_pass")
        shutil.copytree(args.validation_root, result_root / "validation")

        report_zip = args.package_root / "sources" / R2_REPORT_NAME
        reproducer = r2_semantic_failure_reproducer(report_zip)
        failure_correction = failure_category_correction(report_zip)
        write_json(result_root / "r2-semantic-failure-reproducer.json", reproducer)
        write_json(result_root / "r2-failure-category-correction.json", failure_correction)
        require(reproducer["status"] == "PASS", "r2_semantic_failure_reproducer_failed")
        require(failure_correction["status"] == "PASS", "failure_category_correction_failed")

        ownership = field_ownership_audit()
        controls = generic_materialization_control_matrix()
        write_json(result_root / "entry-range-field-ownership-audit.json", ownership)
        write_json(result_root / "generic-materialization-control-matrix.json", controls)
        require(ownership["status"] == "PASS", "field_ownership_incomplete")
        require(controls["status"] == "PASS", "materialization_controls_failed")
        write_json(
            result_root / "entry-range-selection-materialization-draft-contract.json",
            _draft_materialization_contract(ownership),
        )

        rows = _contexts(args.shadow_input_root.resolve())
        coverage = _candidate_coverage(rows)
        feasibility = _feasibility_matrix(rows)
        execution_coverage = _execution_growth_coverage(rows)
        discount_proof = _discount_prohibition(rows)
        method_disagreement = {
            "contract": "m12co-method-disagreement-analysis-v1",
            "rows": [
                {
                    "market": row["market"],
                    "ticker": row["ticker"],
                    **row["method_disagreement"],
                }
                for row in rows
            ],
            "status_counts": coverage["method_disagreement_status_counts"],
            "methods_averaged_count": 0,
            "status": "PASS",
        }
        candidates = {
            "contract": "m12co-fundamental-entry-candidates-22-v1",
            "frozen_generation": EXPECTED_FROZEN_GENERATION,
            "subject_count": len(rows),
            "subjects": rows,
            "final_preferred_option_selected": False,
        }
        write_json(
            result_root / "valuation-method-source-contracts.json",
            valuation_method_source_contracts(),
        )
        write_json(result_root / "valuation-method-feasibility-matrix.json", feasibility)
        write_json(
            result_root / "archetype-method-applicability-matrix.json",
            archetype_method_applicability_matrix(),
        )
        write_json(result_root / "execution-growth-method-input-coverage.json", execution_coverage)
        write_json(
            result_root / "fundamental-entry-candidate-builder-contract.json", _builder_contract()
        )
        write_json(result_root / "fundamental-entry-candidate-coverage.json", coverage)
        write_json(result_root / "fundamental-entry-candidates-22.json", candidates)
        write_json(result_root / "method-disagreement-analysis.json", method_disagreement)
        write_json(
            result_root / "historical-regime-structural-rerating-diagnostics.json",
            {
                "contract": "m12co-historical-regime-structural-rerating-diagnostics-v1",
                "subject_count": len(rows),
                "subjects": [
                    {
                        "market": row["market"],
                        "ticker": row["ticker"],
                        **row["historical_regime_diagnostics"],
                    }
                    for row in rows
                ],
                "status": "PASS",
            },
        )
        write_json(result_root / "current-price-discount-prohibition-proof.json", discount_proof)
        write_json(
            result_root / "generic-positive-negative-fixtures.json",
            {
                "contract": "m12co-generic-positive-negative-fixtures-v1",
                "controls": controls,
                "status": controls["status"],
            },
        )
        require(coverage["status"] == "PASS", "safe_method_coverage_insufficient")
        require(discount_proof["status"] == "PASS", "arbitrary_discount_proof_failed")

        scope_reconciliation = {
            "contract": "m12co-m12cn-r2-chat-scope-reconciliation-v1",
            "r2_schema_completeness_closed": True,
            "r2_terminal_preserved": "M12CN_R2_POLICY_CALIBRATION_SHADOW_FAILED",
            "r2_validator_weakened": False,
            "r2_shadow_rerun_count": 0,
            "external_model_call_count": 0,
            "fundamental_candidate_baseline": 0,
            "fundamental_candidate_subject_count_after_offline_builder": coverage[
                "any_safe_fundamental_candidate_subject_count"
            ],
            "status": "PASS",
        }
        write_json(result_root / "m12cn-r2-chat-scope-reconciliation.json", scope_reconciliation)
        (result_root / "sources").mkdir(parents=True, exist_ok=True)
        shutil.copy2(
            REPO / "scripts/m12co_entry_range_contract.py",
            result_root / "sources/m12co_entry_range_contract.py",
        )
        shutil.copy2(
            REPO / "scripts/m12co_entry_range_design.py",
            result_root / "sources/m12co_entry_range_design.py",
        )
        shutil.copy2(
            REPO / "scripts/m12cn_policy_shadow.py",
            result_root / "sources/m12cn_policy_shadow.py",
        )
        write_json(
            result_root / "shadow-builder-materializer-source-hashes.json",
            {
                "contract": "m12co-shadow-builder-materializer-source-hashes-v1",
                "files": [
                    {
                        "path": name,
                        "sha256": sha256_file(result_root / "sources" / name),
                    }
                    for name in (
                        "m12co_entry_range_contract.py",
                        "m12co_entry_range_design.py",
                        "m12cn_policy_shadow.py",
                    )
                ],
            },
        )
        write_json(
            result_root / "safety-counters.json",
            {
                "external_model_calls": 0,
                "market_refreshes": 0,
                "production_policy_runtime_config_changes": 0,
                "production_sends": 0,
                "production_intents": 0,
                "production_db_writes": 0,
                "broker_reads": 0,
                "broker_orders_modifies_cancels": 0,
                "scheduler_changes": 0,
                "main_merges": 0,
                "remote_pushes": 0,
                "deployments": 0,
                "automatic_m12cn_r3_starts": 0,
            },
        )
        terminal = COMPLETION_READY
        write_json(
            result_root / "complete-blocker-ledger.json",
            {
                "contract": "m12co-complete-blocker-ledger-v1",
                "open_blocker_count": 0,
                "blockers": [],
                "chat_policy_decisions": [
                    "percentile band policy by archetype",
                    "structural-rerating and cycle-normalization treatment",
                    "P/B economic applicability boundary",
                    "future growth-scenario source contracts",
                ],
                "status": "CLEAR_FOR_CHAT_POLICY_SELECTION",
            },
        )
        write_json(
            result_root / "program-completion.json",
            {
                "contract": "m12co-program-completion-v1",
                "completion_state": terminal,
                "completed_at": datetime.now(UTC).isoformat(),
                "implementation_commit": args.expected_head,
                "frozen_generation": EXPECTED_FROZEN_GENERATION,
                "subject_count": len(rows),
                "external_model_call_count": 0,
                "chat_review_required": True,
                "production_readiness": "NO",
                "m12cn_r3_authorized": False,
            },
        )
        write_text(
            result_root / "REPORT.md",
            _report_markdown(
                expected_head=args.expected_head,
                coverage=coverage,
                rows=rows,
                failure_correction=failure_correction,
            ),
        )
    except BaseException as exc:  # noqa: BLE001
        failure_code = str(exc).split(":", 1)[0]
        open_blockers.append(
            {
                "severity": "P0",
                "code": failure_code,
                "error_type": type(exc).__name__,
            }
        )
        if failure_code == "field_ownership_incomplete":
            terminal = COMPLETION_OWNERSHIP_GAP
        elif failure_code == "safe_method_coverage_insufficient":
            terminal = COMPLETION_COVERAGE_INSUFFICIENT
        else:
            terminal = COMPLETION_FAILED
        write_json(
            result_root / "complete-blocker-ledger.json",
            {
                "contract": "m12co-complete-blocker-ledger-v1",
                "open_blocker_count": len(open_blockers),
                "blockers": open_blockers,
                "status": "BLOCKED",
            },
        )
        write_json(
            result_root / "program-completion.json",
            {
                "contract": "m12co-program-completion-v1",
                "completion_state": terminal,
                "completed_at": datetime.now(UTC).isoformat(),
                "implementation_commit": args.expected_head,
                "external_model_call_count": 0,
                "chat_review_required": True,
                "production_readiness": "NO",
            },
        )
        write_text(
            result_root / "REPORT.md",
            f"# M12CO Offline Design\n\n**Completion:** `{terminal}`\n\n"
            f"Blocker: `{type(exc).__name__}: {exc}`",
        )
    finally:
        write_json(result_root / "artifact-manifest.json", artifact_manifest(result_root))
        destination = result_root.with_suffix(".zip")
        zip_tree(result_root, destination)
        write_text(
            destination.with_suffix(destination.suffix + ".sha256"),
            f"{sha256_file(destination)}  {destination.name}",
        )
    print(terminal)
    if terminal != COMPLETION_READY:
        raise SystemExit(1)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--package-root", type=Path, required=True)
    parser.add_argument("--shadow-input-root", type=Path, required=True)
    parser.add_argument("--validation-root", type=Path, required=True)
    parser.add_argument("--result-root", type=Path, required=True)
    parser.add_argument("--expected-head", required=True)
    run(parser.parse_args())


if __name__ == "__main__":
    main()
