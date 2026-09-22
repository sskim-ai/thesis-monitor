from __future__ import annotations

import argparse
import hashlib
import io
import json
import shutil
import subprocess
import zipfile
from collections import Counter
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from scripts.m12cp_valuation_policy_contract import (
    Archetype,
    ValuationRegimeTier,
    build_component_inventory,
    build_subject_policy_matrix,
    depositary_basis_audit,
    derive_enterprise_value_input,
    generic_control_matrix,
    historical_projection_gap_analysis,
    method_intersection_analysis,
    policy_contracts,
    scenario_method_source_coverage,
    updated_policy_coverage,
)


REPO = Path(__file__).resolve().parents[1]
EXPECTED_M12CO_RESULT_SHA256 = "ece5d575183a86c25c6fb0762957c07675d15914747cbbab4845ed510b82abe4"
EXPECTED_M12CO_PACKAGE_SHA256 = "5d8ad36d68ddc5a467bb7352966c2d1ce2ad58da7fa6f0c60f9859db489d30f4"
EXPECTED_RUNTIME_BASE = "831890d1bf0dff303f67a6e0de1403ad3221b5d8"
EXPECTED_M12CO_IMPLEMENTATION = "59ea089b1da246dfd87b15a22b03c0312a2d0ae0"
WORK_INSTRUCTION_COMMIT = "dfe5f2ccb010715af52357439a7e748988df4f8a"
EXPECTED_FROZEN_GENERATION = "20260917-m12cm-current-v4-smoke-20260917T062918Z-5c0cb075ce8b"
M12CO_RESULT_NAME = (
    "thesis-monitor-20260917-m12co-fundamental-entry-range-method-coverage-"
    "and-materialization-ownership-design-report.zip"
)
M12CO_PACKAGE_NAME = (
    "thesis-monitor-20260917-m12co-fundamental-entry-range-method-coverage-"
    "and-materialization-ownership-design-work-instruction.zip"
)
R2_PACKAGE_SUFFIX = (
    "thesis-monitor-20260917-m12cn-r2-structured-output-schema-completeness-"
    "repair-fresh-shadow-work-instruction.zip"
)
COMPLETION_READY = "M12CP_ARCHETYPE_VALUATION_POLICY_AND_SOURCE_COVERAGE_READY_FOR_FRESH_SHADOW"
COMPLETION_POLICY_GAP = "M12CP_POLICY_MATERIALIZATION_GAP_REQUIRES_CHAT"
COMPLETION_SCENARIO_GAP = "M12CP_SCENARIO_SOURCE_COVERAGE_INSUFFICIENT_BUT_HISTORICAL_POLICY_READY"
COMPLETION_FAILED = "M12CP_OFFLINE_POLICY_DESIGN_FAILED"


class M12CPFailure(RuntimeError):
    pass


def require(condition: bool, code: str) -> None:
    if not condition:
        raise M12CPFailure(code)


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise M12CPFailure(f"expected_json_object:{path}")
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


def _zip_member(archive: zipfile.ZipFile, suffix: str) -> bytes:
    names = [name for name in archive.namelist() if name.endswith(suffix)]
    if len(names) != 1:
        raise M12CPFailure(f"zip_member_count_invalid:{suffix}:{len(names)}")
    return archive.read(names[0])


def _zip_json(archive: zipfile.ZipFile, suffix: str) -> dict[str, Any]:
    value = json.loads(_zip_member(archive, suffix))
    if not isinstance(value, dict):
        raise M12CPFailure(f"zip_json_not_object:{suffix}")
    return value


def _verify_manifest(
    archive: zipfile.ZipFile,
    *,
    manifest_suffix: str,
) -> tuple[int, int, list[str]]:
    manifest = _zip_json(archive, manifest_suffix)
    rows = manifest.get("files")
    if not isinstance(rows, list):
        return 0, 0, ["manifest_files_missing"]
    errors: list[str] = []
    verified = 0
    by_relative = {name.split("/", 1)[-1]: name for name in archive.namelist()}
    for row in rows:
        if not isinstance(row, Mapping):
            errors.append("manifest_row_invalid")
            continue
        relative = str(row.get("path") or "")
        name = by_relative.get(relative)
        if name is None:
            errors.append(f"artifact_missing:{relative}")
            continue
        raw = archive.read(name)
        if len(raw) != row.get("size"):
            errors.append(f"artifact_size_mismatch:{relative}")
            continue
        if hashlib.sha256(raw).hexdigest() != row.get("sha256"):
            errors.append(f"artifact_hash_mismatch:{relative}")
            continue
        verified += 1
    return len(rows), verified, errors


def _verify_package_root(package_root: Path) -> dict[str, object]:
    manifest = read_json(package_root / "package-manifest.json")
    rows = manifest.get("files")
    require(isinstance(rows, list), "package_manifest_files_missing")
    errors: list[str] = []
    for row in rows:
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
    return {
        "declared_payload_count": len(rows),
        "verified_payload_count": len(rows) - len(errors),
        "errors": errors,
    }


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", *args],
        cwd=REPO,
        check=True,
        text=True,
        capture_output=True,
    ).stdout.strip()


def runtime_integrity(expected_head: str) -> dict[str, object]:
    actual = _git("rev-parse", "HEAD")
    errors: list[str] = []
    if actual != expected_head:
        errors.append("HEAD_MISMATCH")
    for ancestor, label in (
        (EXPECTED_RUNTIME_BASE, "REQUIRED_RUNTIME_BASE_NOT_ANCESTOR"),
        (EXPECTED_M12CO_IMPLEMENTATION, "M12CO_IMPLEMENTATION_NOT_ANCESTOR"),
        (WORK_INSTRUCTION_COMMIT, "WORK_INSTRUCTION_NOT_ANCESTOR"),
    ):
        result = subprocess.run(
            ["git", "merge-base", "--is-ancestor", ancestor, expected_head],
            cwd=REPO,
            check=False,
        )
        if result.returncode != 0:
            errors.append(label)
    changed = _git("diff", "--name-only", f"{EXPECTED_M12CO_IMPLEMENTATION}..{expected_head}")
    changed_paths = [path for path in changed.splitlines() if path]
    allowed = (
        "docs/work-instructions/20260917-m12cp-",
        "scripts/m12cp_",
        "tests/test_m12cp_",
    )
    production_violations = [
        path for path in changed_paths if not any(path.startswith(prefix) for prefix in allowed)
    ]
    if production_violations:
        errors.append("PRODUCTION_OR_OUT_OF_SCOPE_FILE_CHANGED")
    return {
        "expected_head": expected_head,
        "actual_head": actual,
        "required_runtime_base": EXPECTED_RUNTIME_BASE,
        "m12co_implementation": EXPECTED_M12CO_IMPLEMENTATION,
        "work_instruction_commit": WORK_INSTRUCTION_COMMIT,
        "changed_paths_since_m12co": changed_paths,
        "production_path_violations": production_violations,
        "errors": errors,
        "status": "PASS" if not errors else "FAIL",
    }


def load_frozen_sources(package_root: Path) -> dict[str, object]:
    package_check = _verify_package_root(package_root)
    result_zip = package_root / "sources" / M12CO_RESULT_NAME
    source_package = package_root / "sources" / M12CO_PACKAGE_NAME
    errors = list(package_check["errors"])
    if sha256_file(result_zip) != EXPECTED_M12CO_RESULT_SHA256:
        errors.append("m12co_result_hash_mismatch")
    if sha256_file(source_package) != EXPECTED_M12CO_PACKAGE_SHA256:
        errors.append("m12co_package_hash_mismatch")
    with zipfile.ZipFile(result_zip) as archive:
        declared, verified, manifest_errors = _verify_manifest(
            archive,
            manifest_suffix="/artifact-manifest.json",
        )
        errors.extend(manifest_errors)
        completion = _zip_json(archive, "/program-completion.json")
        candidates = _zip_json(archive, "/fundamental-entry-candidates-22.json")
        source_integrity = _zip_json(archive, "/source-base-integrity.json")
    if declared != 40 or verified != 40:
        errors.append(f"m12co_manifest_verification_count:{declared}:{verified}")
    if completion.get("completion_state") != (
        "M12CO_ENTRY_RANGE_METHOD_COVERAGE_READY_FOR_CHAT_POLICY_SELECTION"
    ):
        errors.append("m12co_completion_mismatch")
    if completion.get("implementation_commit") != EXPECTED_M12CO_IMPLEMENTATION:
        errors.append("m12co_implementation_mismatch")
    if candidates.get("frozen_generation") != EXPECTED_FROZEN_GENERATION:
        errors.append("m12co_frozen_generation_mismatch")
    with zipfile.ZipFile(source_package) as m12co_package:
        r2_package_raw = _zip_member(m12co_package, R2_PACKAGE_SUFFIX)
    with zipfile.ZipFile(io.BytesIO(r2_package_raw)) as r2_package:
        m12cm_input_raw = _zip_member(r2_package, "inputs/m12cm-shadow-input.zip")
    with zipfile.ZipFile(io.BytesIO(m12cm_input_raw)) as m12cm_input:
        input_freeze = _zip_json(m12cm_input, "input-freeze.json")
        contexts = {
            "us": _zip_json(m12cm_input, "us/context.json"),
            "kr": _zip_json(m12cm_input, "kr/context.json"),
        }
    if input_freeze.get("generation_id") != EXPECTED_FROZEN_GENERATION:
        errors.append("m12cm_frozen_generation_mismatch")
    subject_count = sum(len(context.get("evidence_packets") or []) for context in contexts.values())
    if subject_count != 22 or candidates.get("subject_count") != 22:
        errors.append(f"subject_count_mismatch:{subject_count}:{candidates.get('subject_count')}")
    return {
        "integrity": {
            "contract": "m12cp-source-base-integrity-v1",
            **package_check,
            "m12co_result_zip_sha256": sha256_file(result_zip),
            "m12co_result_manifest_declared": declared,
            "m12co_result_manifest_verified": verified,
            "m12co_work_instruction_zip_sha256": sha256_file(source_package),
            "m12co_completion": completion.get("completion_state"),
            "m12co_implementation_commit": completion.get("implementation_commit"),
            "m12cm_frozen_generation": input_freeze.get("generation_id"),
            "subject_count": subject_count,
            "prior_source_integrity_status": source_integrity.get("status"),
            "errors": errors,
            "status": "PASS" if not errors else "FAIL",
        },
        "candidates": candidates,
        "contexts": contexts,
        "input_freeze": input_freeze,
        "m12co_completion": completion,
    }


def _packets(contexts: Mapping[str, Mapping[str, object]]) -> list[tuple[str, dict[str, object]]]:
    rows: list[tuple[str, dict[str, object]]] = []
    for market in ("us", "kr"):
        context = contexts[market]
        selected = tuple(context.get("selected_subjects") or [])
        packets = {
            str(packet.get("ticker") or ""): dict(packet)
            for packet in context.get("evidence_packets") or []
            if isinstance(packet, Mapping)
        }
        require(set(selected) == set(packets), f"{market}_selected_packet_mismatch")
        rows.extend((market, packets[ticker]) for ticker in selected)
    return rows


def _historical_gap_summary(rows: Sequence[Mapping[str, object]]) -> dict[str, object]:
    categories = Counter(
        method["category"]
        for row in rows
        for method in row.get("methods") or []
        if method.get("category") != "ALREADY_SAFE"
    )
    safe_projection_count = sum(
        method.get("safe_shadow_projection_performed") is True
        for row in rows
        for method in row.get("methods") or []
    )
    return {
        "contract": "m12cp-historical-method-projection-gap-analysis-v1",
        "subjects": list(rows),
        "gap_category_counts": dict(sorted(categories.items())),
        "safe_existing_source_projection_count": safe_projection_count,
        "new_semantics_invented_count": 0,
    }


def _policy_selection_artifact(chat_review_sha: str) -> dict[str, object]:
    contracts = policy_contracts()
    return {
        "contract": "m12cp-m12co-chat-policy-selection-v1",
        "source_chat_review_sha256": chat_review_sha,
        "policy": contracts["archetype_policy"],
        "regime_tiers": contracts["valuation_regime_tier"],
        "method_averaging_allowed": False,
        "current_price_band_generation_allowed": False,
        "production_integration_authorized": False,
        "fresh_shadow_authorized": False,
        "status": "FROZEN",
    }


def _new_buyer_contract() -> dict[str, object]:
    return {
        "contract": "m12cp-new-buyer-consistency-draft-v1",
        "status": "DRAFT_SHADOW_ONLY",
        "ATTRACTIVE": {
            "requires_resolved_fundamental_option": True,
            "current_price_at_or_below_band_high": True,
            "severe_execution_or_tactical_condition_compatible": True,
        },
        "WAIT": [
            "CURRENT_PRICE_ABOVE_PREFERRED_FUNDAMENTAL_RANGE",
            "FUNDAMENTAL_RANGE_UNRESOLVED",
            "TACTICAL_TIMING_UNFAVORABLE_WITH_POSITIVE_LONG_TERM_THESIS",
        ],
        "AVOID": {
            "material_execution_or_thesis_risk_allowed": True,
            "resolved_price_band_required": False,
        },
        "overall_direction_separate": True,
        "valuation_timing_alone_does_not_force_overall_downgrade": True,
        "holder_separate": True,
        "valuation_alone_does_not_create_review": True,
        "production_changed": False,
    }


def _next_shadow_contract() -> dict[str, object]:
    return {
        "contract": "m12cp-next-shadow-output-contract-draft-v1",
        "status": "DRAFT_REQUIRES_CHAT_AUTHORIZATION",
        "model_outputs_for_wait": {
            "archetype": [value.value for value in Archetype],
            "valuation_regime_tier": [value.value for value in ValuationRegimeTier],
            "tier_supporting_refs": "ELIGIBLE_NON_PRICE_REFS_ONLY",
            "tactical_choice": "candidate_id | UNRESOLVED",
            "re_evaluation_prose": "BOUNDED_NONNUMERIC",
        },
        "model_authors_fundamental_candidate_id": False,
        "runtime_materializes_entire_entry_range": True,
        "multiple_policy_eligible_fundamental_choices": "UNRESOLVED",
        "model_authored_prices_allowed": False,
        "fresh_shadow_automatically_started": False,
    }


def _report_markdown(
    *,
    expected_head: str,
    terminal: str,
    coverage: Mapping[str, object],
    component_inventory: Sequence[Mapping[str, object]],
    ev_rows: Sequence[Mapping[str, object]],
    scenario_rows: Sequence[Mapping[str, object]],
    depositary: Mapping[str, object],
    intersections: Mapping[str, object],
    gaps: Mapping[str, object],
) -> str:
    available_counts = Counter(
        name
        for row in component_inventory
        for name, value in row["components"].items()
        if value["status"] == "AVAILABLE"
    )
    return f"""# M12CP Archetype Valuation Policy & Source Coverage

**Completion:** `{terminal}`

## Integrity

- Work-instruction commit: `{WORK_INSTRUCTION_COMMIT}`
- Implementation commit: `{expected_head}`
- M12CO result SHA-256: `{EXPECTED_M12CO_RESULT_SHA256}`
- Frozen generation: `{EXPECTED_FROZEN_GENERATION}`
- Subjects: `{coverage["subject_count"]}`

## Policy coverage

- Safe arithmetic subjects: `{coverage["safe_arithmetic_subject_count"]}`
- Policy-selectable under at least one archetype/tier: `{coverage["policy_selectable_subject_count"]}`
- Durable primary P/E coverage: `{coverage["durable_primary_pe_subject_count"]}`
- Structural-cyclical primary P/B coverage: `{coverage["structural_cyclical_primary_pb_subject_count"]}`
- Mature-value intersection subjects: `{coverage["mature_value_intersection_subject_count"]}`
- Same-tier intersection candidates: `{intersections["intersection_count"]}`
- Same-tier non-overlap outcomes: `{intersections["non_overlap_count"]}`
- Execution-growth scenario ready: `{coverage["execution_growth_scenario_ready_subject_count"]}`
- No safe policy method: `{coverage["no_safe_policy_method_subject_count"]}`

No archetype or valuation tier was selected in M12CP. The matrix shows deterministic outcomes for each possible future model judgment.

## Frozen source coverage

- Available typed component counts by subject: `{json.dumps(dict(sorted(available_counts.items())), ensure_ascii=False)}`
- Safe derived EV inputs: `{sum(row["status"] == "SAFE_DERIVED_INPUT" for row in ev_rows)}`
- Scenario-ready subjects: `{sum(row["scenario_ready"] for row in scenario_rows)}`
- Depositary basis resolved / unresolved: `{depositary["resolved_count"]} / {depositary["unresolved_count"]}`
- Safe historical source projections added: `{gaps["safe_existing_source_projection_count"]}`

The frozen packets do not own the complete forecast, multiple, enterprise-value, share-basis, and scenario inputs needed for EV/Sales, EV/GP, EV/EBITDA, or FCF scenario methods. No forecast or conversion was fabricated.

## Safety

- External model calls: `0`
- Market refreshes: `0`
- Production runtime/config changes: `0`
- Sends, intents, DB writes, broker actions, scheduler changes: `0`
- Main merges, remote pushes, deployments: `0`
- Model-authored prices: `0`
- Method averages: `0`

This result returns to Chat. It does not authorize a fresh shadow or production integration.
"""


def artifact_manifest(root: Path) -> dict[str, object]:
    files = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.name == "artifact-manifest.json":
            continue
        files.append(
            {
                "path": path.relative_to(root).as_posix(),
                "size": path.stat().st_size,
                "sha256": sha256_file(path),
            }
        )
    return {
        "contract": "m12cp-artifact-manifest-v1",
        "self_excluded": True,
        "files": files,
    }


def zip_tree(source: Path, destination: Path) -> None:
    prefix = source.name
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(source.rglob("*")):
            if path.is_file():
                archive.write(path, f"{prefix}/{path.relative_to(source).as_posix()}")


def run(args: argparse.Namespace) -> None:
    result_root = args.result_root.resolve()
    require(not result_root.exists(), "result_root_already_exists")
    result_root.mkdir(parents=True)
    terminal = COMPLETION_FAILED
    blockers: list[dict[str, object]] = []
    try:
        source = load_frozen_sources(args.package_root.resolve())
        runtime = runtime_integrity(args.expected_head)
        source_integrity = dict(source["integrity"])
        source_integrity["runtime_integrity"] = runtime
        source_integrity["status"] = (
            "PASS"
            if source_integrity["status"] == "PASS" and runtime["status"] == "PASS"
            else "FAIL"
        )
        write_json(result_root / "source-base-integrity.json", source_integrity)
        require(source_integrity["status"] == "PASS", "source_or_runtime_integrity_failed")

        validation = read_json(args.validation_root / "validation-summary.json")
        require(validation.get("status") == "PASS", "validation_not_pass")
        shutil.copytree(args.validation_root, result_root / "validation")

        subjects = source["candidates"]["subjects"]
        packets = _packets(source["contexts"])
        require(len(subjects) == len(packets) == 22, "subject_count_not_22")
        candidate_tickers = {str(row["ticker"]) for row in subjects}
        packet_tickers = {str(packet["ticker"]) for _, packet in packets}
        require(candidate_tickers == packet_tickers, "candidate_packet_identity_mismatch")

        controls = generic_control_matrix()
        require(controls["status"] == "PASS", "generic_policy_controls_failed")
        write_json(result_root / "generic-fixture-control-matrix.json", controls)

        contracts = policy_contracts()
        chat_review = args.package_root / "M12CO_CHAT_REVIEW.md"
        write_json(
            result_root / "m12co-chat-policy-selection.json",
            _policy_selection_artifact(sha256_file(chat_review)),
        )
        write_json(
            result_root / "archetype-primary-method-policy.json",
            {
                "contract": "m12cp-archetype-primary-method-policy-v1",
                "policies": contracts["archetype_policy"],
                "ticker_country_rules": 0,
                "production_changed": False,
            },
        )
        write_json(
            result_root / "valuation-regime-tier-contract.json",
            {
                "contract": "m12cp-valuation-regime-tier-contract-v1",
                "tier_to_quantile_band": contracts["valuation_regime_tier"],
                "tier_evidence": contracts["tier_evidence"],
                "model_judgment_performed_in_m12cp": False,
            },
        )
        write_json(
            result_root / "entry-option-policy-materializer-contract.json",
            {
                "contract": "m12cp-entry-option-policy-materializer-contract-v1",
                "inputs": [
                    "archetype",
                    "valuation_regime_tier",
                    "m12co_safe_candidate_catalog",
                ],
                "outcomes": [
                    "EXACTLY_ONE_ELIGIBLE_FUNDAMENTAL_OPTION",
                    "SAME_TIER_METHOD_INTERSECTION",
                    "UNRESOLVED",
                ],
                "model_authored_prices": False,
                "method_averaging": False,
                "current_price_used_in_band_formula": False,
            },
        )
        write_json(
            result_root / "new-buyer-consistency-draft-contract.json",
            _new_buyer_contract(),
        )
        write_json(
            result_root / "next-shadow-output-contract-draft.json",
            _next_shadow_contract(),
        )

        inventory_rows = [
            build_component_inventory(market=market, packet=packet) for market, packet in packets
        ]
        inventory = {
            "contract": "m12cp-frozen-source-component-inventory-22-v1",
            "frozen_generation": EXPECTED_FROZEN_GENERATION,
            "subject_count": len(inventory_rows),
            "subjects": inventory_rows,
            "prose_inference_count": 0,
        }
        write_json(result_root / "frozen-source-component-inventory-22.json", inventory)

        ev_rows = [derive_enterprise_value_input(row) for row in inventory_rows]
        ev_coverage = {
            "contract": "m12cp-enterprise-value-derived-input-coverage-v1",
            "subject_count": len(ev_rows),
            "safe_derived_count": sum(row["status"] == "SAFE_DERIVED_INPUT" for row in ev_rows),
            "incomplete_count": sum(
                row["status"] == "ENTERPRISE_VALUE_COMPONENTS_INCOMPLETE" for row in ev_rows
            ),
            "subjects": ev_rows,
            "silent_approximation_count": 0,
        }
        write_json(result_root / "enterprise-value-derived-input-coverage.json", ev_coverage)

        ev_by_ticker = {row["ticker"]: row for row in ev_rows}
        scenario_rows = [
            scenario_method_source_coverage(row, ev_by_ticker[row["ticker"]])
            for row in inventory_rows
        ]
        scenario_ready = [row["ticker"] for row in scenario_rows if row["scenario_ready"]]
        write_json(
            result_root / "scenario-method-source-coverage.json",
            {
                "contract": "m12cp-scenario-method-source-coverage-22-v1",
                "subject_count": len(scenario_rows),
                "scenario_ready_subject_count": len(scenario_ready),
                "scenario_ready_subjects": scenario_ready,
                "subjects": scenario_rows,
                "fabricated_forecast_count": 0,
            },
        )

        gap_rows = [historical_projection_gap_analysis(row) for row in subjects]
        gaps = _historical_gap_summary(gap_rows)
        write_json(result_root / "historical-method-projection-gap-analysis.json", gaps)

        depositary_rows = [depositary_basis_audit(packet) for _, packet in packets]
        affected = [row for row in depositary_rows if row["affected"]]
        depositary = {
            "contract": "m12cp-depositary-security-basis-coverage-v1",
            "subject_count": len(depositary_rows),
            "affected_count": len(affected),
            "resolved_count": sum(row["status"] == "RESOLVED" for row in affected),
            "unresolved_count": sum(
                row["status"] == "DEPOSITARY_SECURITY_BASIS_UNRESOLVED" for row in affected
            ),
            "subjects": depositary_rows,
            "underlying_metrics_copied_without_verified_ratio_count": 0,
        }
        write_json(result_root / "depositary-security-basis-coverage.json", depositary)

        matrices = [build_subject_policy_matrix(row) for row in subjects]
        options = {
            "contract": "m12cp-policy-selectable-entry-options-22-v1",
            "frozen_generation": EXPECTED_FROZEN_GENERATION,
            "subject_count": len(matrices),
            "subjects": matrices,
            "archetype_selected": False,
            "valuation_regime_tier_selected": False,
            "final_preferred_range_selected": False,
        }
        write_json(result_root / "policy-selectable-entry-options-22.json", options)
        intersections = method_intersection_analysis(matrices)
        write_json(result_root / "method-intersection-analysis.json", intersections)
        coverage = updated_policy_coverage(
            subjects,
            matrices,
            scenario_ready_subjects=scenario_ready,
            depositary_resolved_count=depositary["resolved_count"],
            depositary_unresolved_count=depositary["unresolved_count"],
        )
        coverage["historical_safe_projection_added_count"] = gaps[
            "safe_existing_source_projection_count"
        ]
        write_json(result_root / "updated-fundamental-entry-candidate-coverage.json", coverage)

        (result_root / "sources").mkdir(parents=True, exist_ok=True)
        source_names = (
            "m12cp_valuation_policy_contract.py",
            "m12cp_valuation_policy_coverage.py",
        )
        for name in source_names:
            shutil.copy2(REPO / "scripts" / name, result_root / "sources" / name)
        write_json(
            result_root / "shadow-only-code-and-source-hashes.json",
            {
                "contract": "m12cp-shadow-only-code-and-source-hashes-v1",
                "files": [
                    {
                        "path": f"scripts/{name}",
                        "sha256": sha256_file(REPO / "scripts" / name),
                    }
                    for name in source_names
                ],
                "production_source_changed": False,
            },
        )

        write_json(
            result_root / "safety-counters.json",
            {
                "external_model_calls": 0,
                "market_refreshes": 0,
                "production_runtime_config_behavior_changes": 0,
                "production_sends": 0,
                "production_intents": 0,
                "production_db_writes": 0,
                "broker_reads_orders_modifies_cancels": 0,
                "scheduler_changes": 0,
                "main_merges": 0,
                "remote_pushes": 0,
                "deployments": 0,
                "model_authored_prices": 0,
                "method_averages": 0,
                "ticker_company_country_rules": 0,
                "fresh_shadow_starts": 0,
            },
        )

        require(coverage["policy_selectable_subject_count"] > 0, "policy_materialization_empty")
        terminal = COMPLETION_READY if scenario_ready else COMPLETION_SCENARIO_GAP
        write_json(
            result_root / "complete-blocker-ledger.json",
            {
                "contract": "m12cp-complete-blocker-ledger-v1",
                "open_p0_count": 0,
                "open_p1_count": 0,
                "blocking_items": [],
                "carried_source_gaps": [
                    {
                        "code": "SCENARIO_SOURCE_CONTRACTS_INCOMPLETE",
                        "subject_count": len(subjects) - len(scenario_ready),
                        "blocks_historical_policy": False,
                        "blocks_execution_growth_scenario_selection": True,
                    }
                ],
                "return_to_chat": True,
                "status": "NO_IMPLEMENTATION_BLOCKERS",
            },
        )
        write_json(
            result_root / "program-completion.json",
            {
                "contract": "m12cp-program-completion-v1",
                "completion_state": terminal,
                "completed_at": datetime.now(UTC).isoformat(),
                "work_instruction_commit": WORK_INSTRUCTION_COMMIT,
                "implementation_commit": args.expected_head,
                "frozen_generation": EXPECTED_FROZEN_GENERATION,
                "subject_count": len(subjects),
                "external_model_call_count": 0,
                "fresh_shadow_authorized": False,
                "production_readiness": "NO",
                "return_to_chat": True,
            },
        )
        write_text(
            result_root / "REPORT.md",
            _report_markdown(
                expected_head=args.expected_head,
                terminal=terminal,
                coverage=coverage,
                component_inventory=inventory_rows,
                ev_rows=ev_rows,
                scenario_rows=scenario_rows,
                depositary=depositary,
                intersections=intersections,
                gaps=gaps,
            ),
        )
    except BaseException as exc:  # noqa: BLE001
        code = str(exc).split(":", 1)[0]
        blockers.append({"severity": "P0", "code": code, "type": type(exc).__name__})
        terminal = (
            COMPLETION_POLICY_GAP
            if code in {"policy_materialization_empty", "generic_policy_controls_failed"}
            else COMPLETION_FAILED
        )
        write_json(
            result_root / "complete-blocker-ledger.json",
            {
                "contract": "m12cp-complete-blocker-ledger-v1",
                "open_p0_count": len(blockers),
                "open_p1_count": 0,
                "blocking_items": blockers,
                "status": "BLOCKED",
            },
        )
        write_json(
            result_root / "program-completion.json",
            {
                "contract": "m12cp-program-completion-v1",
                "completion_state": terminal,
                "completed_at": datetime.now(UTC).isoformat(),
                "work_instruction_commit": WORK_INSTRUCTION_COMMIT,
                "implementation_commit": args.expected_head,
                "external_model_call_count": 0,
                "fresh_shadow_authorized": False,
                "production_readiness": "NO",
            },
        )
        write_text(
            result_root / "REPORT.md",
            f"# M12CP Offline Policy Coverage\n\n**Completion:** `{terminal}`\n\n"
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
    if terminal not in {COMPLETION_READY, COMPLETION_SCENARIO_GAP}:
        raise SystemExit(1)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--package-root", type=Path, required=True)
    parser.add_argument("--validation-root", type=Path, required=True)
    parser.add_argument("--result-root", type=Path, required=True)
    parser.add_argument("--expected-head", required=True)
    run(parser.parse_args())


if __name__ == "__main__":
    main()
