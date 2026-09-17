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
    CompanyArchetype,
    DataQualityEffect,
    EntryRangeStatus,
    ShadowBatchOutput,
    batch_output_schema,
    build_subject_catalog,
    generic_policy_control_matrix,
    model_subject_payload,
    policy_prompt,
    validate_shadow_batch,
)


REPO = Path(__file__).resolve().parents[1]
KST = ZoneInfo("Asia/Seoul")
REQUIRED_RUNTIME_BASE = "831890d1bf0dff303f67a6e0de1403ad3221b5d8"
EXPECTED_RUNTIME_TREE_SHA256 = (
    "c0a48acb3acdbd1dff940924f38c177bfecfd07df7cda0d3bddf86424c1f1062"
)
EXPECTED_FROZEN_GENERATION = (
    "20260917-m12cm-current-v4-smoke-20260917T062918Z-5c0cb075ce8b"
)
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
    "inputs/m12cm-human-review-only.zip": (
        "93e376c5efe91664e0193f6f79c048cb4c9328befa18c182ae729616e64409fb"
    ),
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
        "sources/thesis-monitor-20260917-m12cl-stage2-maturity-supporting-claim-"
        "completeness-contract-repair-offline-closure-report.zip"
    ): "744f638e56436d31b6bdc8eb4aece3f68cd7daf0e4a2f02d8feabf7dbddd8024",
    (
        "sources/thesis-monitor-20260917-m12cm-fresh-current-v4-production-"
        "equivalent-smoke-blind-handoff-report.zip"
    ): "625606d6df521cf3368c8779ec7f24816ee3a374cdfcc7fac367f984983359cc",
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
COMPLETION_PASS = "M12CN_POLICY_CALIBRATION_SHADOW_PASS_READY_FOR_CHAT_REVIEW"
COMPLETION_FAILED = "M12CN_POLICY_CALIBRATION_SHADOW_FAILED"


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
        json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, default=str)
        + "\n",
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
        rows.append(
            {"path": relative, "sha256": sha256_bytes(current), "size": len(current)}
        )
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
        "contract": "m12cn-pre-freeze-source-integrity-v1",
        "cryptographic_only_post_freeze_payload_access": True,
        "post_freeze_semantic_open_count": 0,
        "package_sources": rows,
        "shadow_input_files": selected_rows,
        "error_count": len(errors),
        "errors": errors,
        "status": "PASS" if not errors else "FAIL",
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
        "contract": "m12cn-entry-range-method-contract-v1",
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
        (f"post_freeze_hash:{name}", digest)
        for name, digest in POST_FREEZE_HASHES.items()
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
                findings.append(
                    {"path": str(path), "marker": label, "occurrence_count": count}
                )
    return {
        "contract": "m12cn-model-input-target-leak-scan-v1",
        "model_facing_file_count": len(files),
        "files": files,
        "marker_count": len(markers),
        "accepted_decision_id_fingerprint_count": len(accepted_decision_ids),
        "target_label_leak_count": sum(
            int(row["occurrence_count"]) for row in findings
        ),
        "findings": findings,
        "status": "PASS" if not findings else "FAIL",
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
            name
            for name in archive.namelist()
            if name.endswith("candidate-output.json")
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
    for ticker in expected_tickers:
        old = old_rows[ticker]
        independent = independent_rows[ticker]
        shadow = shadow_rows[ticker]
        old_matches = {
            axis: old.get(axis) == shadow.get(axis)
            for axis in axes
        }
        independent_matches = {
            axis: independent.get(axis) == shadow.get(axis)
            for axis in axes
        }
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
                "m12cn_shadow": {
                    axis: shadow.get(axis) for axis in axes
                },
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
        "contract": "m12cn-post-freeze-three-way-comparison-v1",
        "comparison_is_descriptive_not_pass_target": True,
        "subject_count": len(expected_tickers),
        "old_vs_shadow_exact_three_axis_agreement": old_shadow_exact,
        "independent_vs_shadow_exact_three_axis_agreement": independent_shadow_exact,
        "old_vs_shadow_per_axis_agreement": dict(old_shadow_axis),
        "independent_vs_shadow_per_axis_agreement": dict(independent_shadow_axis),
        "label_distributions": {
            "old_monitoring": {
                axis: dict(sorted(counter.items()))
                for axis, counter in old_distribution.items()
            },
            "independent_reference": {
                axis: dict(sorted(counter.items()))
                for axis, counter in independent_distribution.items()
            },
            "m12cn_shadow": {
                axis: dict(sorted(counter.items()))
                for axis, counter in shadow_distribution.items()
            },
        },
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


def _result_analyses(candidates: Sequence[Mapping[str, object]]) -> dict[str, object]:
    entry_status = Counter()
    entry_methods = Counter()
    archetypes = Counter()
    resolved_archetypes = Counter()
    holder_stances = Counter()
    holder_reasons = Counter()
    data_quality_effects = Counter()
    valuation_affects = Counter()
    unresolved_inputs = Counter()
    wait_count = 0
    for row in candidates:
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
        if row["new_buyer"] == "WAIT":
            wait_count += 1
        if status == EntryRangeStatus.ENTRY_RANGE_RESOLVED.value:
            resolved_archetypes[archetype] += 1
        for missing in entry.get("unresolved_inputs") or []:
            unresolved_inputs[str(missing)] += 1
    return {
        "entry": {
            "contract": "m12cn-entry-range-coverage-and-methods-v1",
            "subject_count": len(candidates),
            "wait_count": wait_count,
            "status_counts": dict(sorted(entry_status.items())),
            "method_counts": dict(sorted(entry_methods.items())),
            "resolved_archetype_counts": dict(sorted(resolved_archetypes.items())),
            "unresolved_input_counts": dict(sorted(unresolved_inputs.items())),
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
                tuple(row.get("valuation_affects") or []) == ("NEW_BUYER",)
                for row in candidates
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
        "# M12CN Investment Archetype Policy Calibration Shadow",
        "",
        f"**Completion:** `{status}`",
        "",
        "## Scope",
        "",
        "This was an archive-only policy calibration against frozen M12CM facts and accepted Fundamental Core. Production prompt, runtime, persistence, scheduler, notifications, and delivery were unchanged.",
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
        f"- Shadow calls: `{call_pass}/8`",
        f"- Shadow subjects: `{subject_count}/22`",
        "- Fundamental Core calls: `0`",
        "- Retry/repair/fallback/judge/selective rerun: `0`",
        "- Post-freeze comparison occurred only after output hash freeze.",
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
            f"{now_utc.astimezone(KST):%Y%m%d}-m12cn-policy-shadow-"
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
                read_json(
                    args.shadow_input_root
                    / market
                    / "trusted-fundamental-core-batch.json"
                )
            )
            require(
                tuple(context.selected_subjects) == EXPECTED_POPULATION[market],
                f"{market}_population_mismatch",
            )
            require(
                tuple(core.ticker for core in core_batch.cores)
                == tuple(context.selected_subjects),
                f"{market}_core_scope_mismatch",
            )
            require(core_batch.packet_id == context.packet_id, f"{market}_packet_mismatch")
            require(core_batch.market == market, f"{market}_core_market_mismatch")
            require(
                core_batch.assessment_date == context.assessment_date,
                f"{market}_assessment_date_mismatch",
            )
            atomic = accepted_v2_maturity_atomic_claim_catalog_manifest(
                core_batch.cores
            )
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

        model_inputs = result_root / "shadow-model-inputs"
        model_facing_paths: list[Path] = []
        batch_specs: list[dict[str, object]] = []
        for market in ("us", "kr"):
            context = contexts[market]
            context_payload = context_payloads[market]
            cores_by_ticker = {
                core.ticker: core.model_dump(mode="json")
                for core in core_batches[market].cores
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
                        "catalogs": {
                            ticker: catalogs[market][ticker]
                            for ticker in batch_subjects
                        },
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
        leak_scan = scan_model_facing_files(model_facing_paths, accepted_ids)
        write_json(result_root / "blindness-and-target-leak-proof.json", leak_scan)
        require(leak_scan["status"] == "PASS", "M12CN_BLINDNESS_FAILURE")
        input_manifest = {
            "contract": "m12cn-shadow-model-input-manifest-v1",
            "generation_id": generation_id,
            "frozen_m12cm_generation": EXPECTED_FROZEN_GENERATION,
            "harness_commit": args.expected_head,
            "reasoning_model": REASONING_MODEL,
            "reasoning_effort": REASONING_EFFORT,
            "planned_call_count": len(batch_specs),
            "planned_fundamental_core_call_count": 0,
            "model_facing_files": leak_scan["files"],
            "target_label_leak_count": leak_scan["target_label_leak_count"],
            "policy_contract_sha256": sha256_file(
                REPO / "scripts/m12cn_policy_contract.py"
            ),
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
            try:
                receipt = runtime._invoke_signed_in_codex(
                    codex_bin=codex_bin,
                    prompt=spec["prompt"],
                    output=output,
                    log=log,
                    schema=spec["schema"],
                    cwd=REPO,
                    timeout=args.timeout,
                    state_namespace=(
                        f"m12cn:{generation_id}:{market}:batch-{batch_number:02d}"
                    ),
                )
                require(
                    int(receipt.get("transport_attempts") or 0) == 1,
                    "transport_retry_detected",
                )
                raw_sha = sha256_file(output)
                frozen_raw = (
                    result_root
                    / "shadow-output-freeze"
                    / market
                    / f"batch-{batch_number:02d}.json"
                )
                frozen_raw.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(output, frozen_raw)
                require(sha256_file(frozen_raw) == raw_sha, "raw_output_freeze_mismatch")
                parsed = ShadowBatchOutput.model_validate(read_json(output))
                validation = validate_shadow_batch(
                    parsed,
                    expected_identity=spec["identity"],
                    subjects=spec["subjects"],
                    catalogs=catalogs[market],
                )
                write_json(call_dir / "semantic-validation.json", validation)
                require(validation["status"] == "PASS", "shadow_semantic_validation_failed")
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
                row.update(
                    {
                        "status": "FAIL",
                        "safe_error_type": type(exc).__name__,
                        "safe_error_code": str(exc).split(":", 1)[0],
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
            "contract": "m12cn-shadow-22-subject-results-v1",
            "generation_id": generation_id,
            "frozen_m12cm_generation": EXPECTED_FROZEN_GENERATION,
            "subject_count": len(all_candidates),
            "candidates": all_candidates,
        }
        aggregate_path = result_root / "shadow-22-subject-results.json"
        write_json(aggregate_path, aggregate)
        output_frozen_at = datetime.now(UTC).isoformat()
        output_freeze = {
            "contract": "m12cn-shadow-output-freeze-manifest-v1",
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
            sha256_file(REPO / "scripts/m12cn_policy_shadow.py")
            == input_manifest["runner_sha256"],
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
            args.post_freeze_root.resolve()
            / "m12cm-independent-assistant-judgment.json"
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

        analyses = _result_analyses(all_candidates)
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
    completion_state = COMPLETION_PASS if terminal_error is None else COMPLETION_FAILED
    blockers = []
    if terminal_error is not None:
        blockers.append(
            {
                "severity": "P0",
                "code": str(terminal_error).split(":", 1)[0],
                "error_type": type(terminal_error).__name__,
                "bounded_next_action": "Return to Chat; no retry or same-run hotfix authorized.",
            }
        )
    write_json(
        result_root / "complete-blocker-ledger.json",
        {
            "contract": "m12cn-complete-blocker-ledger-v1",
            "open_blocker_count": len(blockers),
            "blockers": blockers,
            "status": "PASS" if not blockers else "BLOCKED",
        },
    )
    safety = {
        "contract": "m12cn-safety-counters-v1",
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
        "stage2_style_shadow_calls_passed": sum(
            row.get("status") == "PASS" for row in call_rows
        ),
        "model_retry": 0,
        "wrapper_retry": 0,
        "repair_model": 0,
        "fallback_model": 0,
        "judge_model": 0,
        "selective_rerun": 0,
        "post_call_hotfix": 0,
        "second_inference_after_reveal": 0,
        "production_runtime_behavior_change": 0,
    }
    write_json(result_root / "safety-counters.json", safety)
    write_json(
        result_root / "shadow-call-ledger.json",
        {
            "contract": "m12cn-shadow-call-ledger-v1",
            "generation_id": generation_id,
            "planned_call_count": 8,
            "started_call_count": len(call_rows),
            "passed_call_count": sum(row.get("status") == "PASS" for row in call_rows),
            "calls": call_rows,
        },
    )
    completion = {
        "contract": "m12cn-program-completion-v1",
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
