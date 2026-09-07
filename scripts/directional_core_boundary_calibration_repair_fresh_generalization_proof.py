from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import zipfile
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any


PROGRAM_CONTRACT = (
    "directional-core-boundary-calibration-repair-fresh-generalization-proof-v1"
)
WORK_INSTRUCTION_PATH = (
    "docs/work-instructions/"
    "20260908-directional-core-boundary-calibration-repair-and-fresh-"
    "generalization-proof.md"
)
LATEST_RESULT_NAME = (
    "thesis-monitor-20260908-runtime-namespace-isolation-repair-"
    "fresh-holdout-proof-report.zip"
)
LATEST_RESULT_SHA256 = (
    "5ade7e8d06c1ae41343f555ae65ff4979ac94d4f1bcf0d94bda8701e4bd5e8c5"
)
LATEST_RESULT_MEMBERS = 2166
LATEST_RESULT_INDEXED_PAYLOADS = 2165
LATEST_FINAL_HEAD = "05c93cf7d768ddb09b670ca74dc69c2b698e5f6b"
RUNS = ("A", "B", "C")

REPORT_NAMES = (
    "01-repository-provenance",
    "02-latest-result-integrity",
    "03-directional-instability-subject-matrix",
    "04-directional-anchor-set-comparison",
    "05-directional-rationale-and-uncertainty-comparison",
    "06-directional-instability-root-cause-classification",
    "07-directional-calibration-architecture-decision",
)


def read_json_bytes(payload: bytes) -> dict[str, Any]:
    value = json.loads(payload)
    if not isinstance(value, dict):
        raise ValueError("json_object_required")
    return value


def canonical_sha256(value: object) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_value(*args: str) -> str:
    return subprocess.run(
        ("git", *args), check=True, capture_output=True, text=True
    ).stdout.strip()


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, default=str)
        + "\n",
        encoding="utf-8",
    )


def _summary(value: object) -> str:
    if isinstance(value, (list, tuple)):
        return f"{len(value)} rows; sha256={canonical_sha256(value)}"
    if isinstance(value, dict) and len(value) > 10:
        return f"{len(value)} keys; sha256={canonical_sha256(value)}"
    return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)


def write_report(report_dir: Path, number: int, value: Mapping[str, object]) -> None:
    name = REPORT_NAMES[number - 1]
    write_json(report_dir / "proofs" / f"{name}.json", value)
    rows = [
        f"| {str(key).replace('|', '/')} | {_summary(item).replace('|', '/')} |"
        for key, item in value.items()
    ]
    body = f"# {name}\n\n| Field | Value |\n| --- | --- |\n" + "\n".join(rows)
    path = report_dir / f"{name}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body + "\n", encoding="utf-8")


def verify_latest_result(path: Path) -> dict[str, object]:
    if path.name != LATEST_RESULT_NAME:
        raise ValueError("LATEST_RESULT_BUNDLE_NAME_MISMATCH")
    actual_sha = file_sha256(path)
    if actual_sha != LATEST_RESULT_SHA256:
        raise ValueError("LATEST_RESULT_BUNDLE_CHECKSUM_MISMATCH")
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        index = read_json_bytes(archive.read("artifact-index.json"))
        indexed = {str(row["path"]): row for row in index.get("rows") or []}
        expected = set(names) - {"artifact-index.json"}
        hash_mismatches = 0
        size_mismatches = 0
        for name, row in indexed.items():
            payload = archive.read(name)
            hash_mismatches += hashlib.sha256(payload).hexdigest() != row.get("sha256")
            size_mismatches += len(payload) != row.get("byte_size")
        failures = {
            "member_count_mismatch": int(len(names) != LATEST_RESULT_MEMBERS),
            "indexed_count_mismatch": int(
                len(indexed) != LATEST_RESULT_INDEXED_PAYLOADS
            ),
            "index_membership_mismatch": int(set(indexed) != expected),
            "hash_mismatches": hash_mismatches,
            "size_mismatches": size_mismatches,
            "crc_failure": archive.testzip(),
        }
    if any(bool(value) for value in failures.values()):
        raise ValueError(f"LATEST_RESULT_INTEGRITY_FAILURE:{failures}")
    return {
        "contract": "latest-result-integrity-v1",
        "name": path.name,
        "sha256": actual_sha,
        "zip_member_count": len(names),
        "indexed_payload_count": len(indexed),
        "failures": failures,
        "status": "PASS",
    }


def repository_provenance() -> dict[str, object]:
    instruction_commit = git_value("log", "-1", "--format=%H", "--", WORK_INSTRUCTION_PATH)
    ancestor = subprocess.run(
        ("git", "merge-base", "--is-ancestor", LATEST_FINAL_HEAD, "HEAD"),
        check=False,
    ).returncode == 0
    result = {
        "contract": "repository-provenance-v1",
        "branch": git_value("branch", "--show-current"),
        "base_sha": LATEST_FINAL_HEAD,
        "work_instruction_commit": instruction_commit,
        "current_head": git_value("rev-parse", "HEAD"),
        "current_tree": git_value("rev-parse", "HEAD^{tree}"),
        "origin_main": git_value("rev-parse", "origin/main"),
        "base_is_ancestor": ancestor,
        "worktree_status": git_value("status", "--short"),
        "model_calls": 0,
        "architecture_mutation": 0,
        "status": "PASS" if ancestor else "FAIL",
    }
    if not ancestor:
        raise ValueError("REPOSITORY_BASE_ANCESTRY_FAILURE")
    return result


def _all_refs(value: object) -> set[str]:
    refs: set[str] = set()
    if isinstance(value, Mapping):
        for key, item in value.items():
            if key.endswith("evidence_refs") and isinstance(item, list):
                refs.update(str(ref) for ref in item)
            else:
                refs.update(_all_refs(item))
    elif isinstance(value, list):
        for item in value:
            refs.update(_all_refs(item))
    return refs


def _candidate_rows(archive: zipfile.ZipFile) -> dict[str, dict[str, dict[str, Any]]]:
    by_run: dict[str, dict[str, dict[str, Any]]] = {}
    for run in RUNS:
        candidates: dict[str, dict[str, Any]] = {}
        prefix = f"experiment/model-contexts/{run}/DIRECTIONAL_CORE/"
        members = sorted(
            name
            for name in archive.namelist()
            if name.startswith(prefix) and name.endswith("/output.normalized.json")
        )
        if len(members) != 4:
            raise ValueError(f"historical_core_context_count_mismatch:{run}:{len(members)}")
        for member in members:
            document = read_json_bytes(archive.read(member))
            for candidate in document.get("candidates") or []:
                if not isinstance(candidate, dict):
                    raise ValueError(f"candidate_object_required:{member}")
                ticker = str(candidate.get("ticker") or "")
                if not ticker or ticker in candidates:
                    raise ValueError(f"candidate_identity_invalid:{run}:{ticker}")
                candidates[ticker] = candidate
        if len(candidates) != 16:
            raise ValueError(f"historical_candidate_count_mismatch:{run}:{len(candidates)}")
        by_run[run] = candidates
    if len({tuple(sorted(rows)) for rows in by_run.values()}) != 1:
        raise ValueError("historical_run_cohort_mismatch")
    return by_run


def _family(candidate: Mapping[str, Any]) -> str:
    buy = float(candidate["directional_balance"]["buy"])
    if buy > 5.0:
        return "POSITIVE"
    if buy < 5.0:
        return "NEGATIVE"
    return "NEUTRAL"


def _field(candidate: Mapping[str, Any], name: str) -> object:
    return candidate.get(name)


def _run_view(candidate: Mapping[str, Any]) -> dict[str, object]:
    return {
        "overall_direction": candidate.get("overall_direction"),
        "directional_balance": candidate.get("directional_balance"),
        "hold_lean": candidate.get("hold_lean"),
        "directional_confidence": candidate.get("directional_confidence"),
        "material_directional_anchor_basis": candidate.get(
            "material_directional_anchor_basis"
        ),
        "dominant_evidence": candidate.get("dominant_evidence"),
        "buy_drivers": candidate.get("buy_drivers"),
        "sell_drivers": candidate.get("sell_drivers"),
        "core_investment_judgment": candidate.get("core_investment_judgment"),
        "uncertainty_limit": candidate.get("uncertainty_limit"),
        "fundamental_new_buyer": candidate.get("fundamental_new_buyer"),
        "fundamental_holder": candidate.get("fundamental_holder"),
    }


def _ref_set(candidate: Mapping[str, Any], field: str) -> set[str]:
    value = candidate.get(field)
    if field == "material_directional_anchor_basis":
        return {str(ref) for ref in value or []}
    return _all_refs(value)


def _jaccard(left: set[str], right: set[str]) -> float:
    union = left | right
    return 1.0 if not union else len(left & right) / len(union)


def _pairwise_min_overlap(sets: Sequence[set[str]]) -> float:
    return min(
        (_jaccard(sets[left], sets[right]) for left in range(3) for right in range(left + 1, 3)),
        default=1.0,
    )


def _classify(candidates: Sequence[Mapping[str, Any]]) -> tuple[str, list[str]]:
    directions = {str(row.get("overall_direction")) for row in candidates}
    balances = [float(row["directional_balance"]["buy"]) for row in candidates]
    leans = {str(row.get("hold_lean")) for row in candidates}
    confidences = {str(row.get("directional_confidence")) for row in candidates}
    if len(directions) == len(set(balances)) == len(leans) == len(confidences) == 1:
        return "STABLE", ["CORE_BUCKET_AND_CONFIDENCE_IDENTICAL"]
    if len(directions) == len(set(balances)) == len(leans) == 1 and len(confidences) > 1:
        return "CONFIDENCE_ONLY_VARIANCE", ["ONLY_DIRECTIONAL_CONFIDENCE_CHANGED"]
    families = {_family(row) for row in candidates}
    max_distance = max(balances) - min(balances)
    dominant_sets = [_ref_set(row, "dominant_evidence") for row in candidates]
    all_driver_sets = [
        _ref_set(row, "buy_drivers") | _ref_set(row, "sell_drivers")
        for row in candidates
    ]
    same_side = families <= {"POSITIVE", "NEUTRAL"} or families <= {
        "NEGATIVE",
        "NEUTRAL",
    }
    common_anchor = set.intersection(*dominant_sets) if dominant_sets else set()
    common_driver = set.intersection(*all_driver_sets) if all_driver_sets else set()
    if (
        "BUY" not in directions or "SELL" not in directions
    ) and same_side and max_distance <= 1.0 and (common_anchor or common_driver):
        return "ADJACENT_BALANCE_CALIBRATION_AMBIGUITY", [
            "SAME_DIRECTIONAL_FAMILY",
            "MAX_BALANCE_DISTANCE_AT_MOST_ONE_POINT",
            "COMMON_MATERIAL_EVIDENCE_REFS",
            "NO_BUY_SELL_REVERSAL",
        ]
    anchor_sets = [
        _ref_set(row, "material_directional_anchor_basis") for row in candidates
    ]
    if not common_anchor and _pairwise_min_overlap(anchor_sets) < 0.5:
        return "MATERIAL_EVIDENCE_SELECTION_VARIANCE", [
            "MATERIAL_ANCHOR_OR_DOMINANT_EVIDENCE_SET_CHANGED"
        ]
    if "BUY" in directions and "SELL" in directions:
        return "TRUE_SEMANTIC_REASONING_DIVERGENCE", ["BUY_SELL_REVERSAL"]
    if not same_side:
        return "OPPOSING_EVIDENCE_INTERPRETATION_VARIANCE", [
            "DIRECTIONAL_FAMILY_CHANGED"
        ]
    return "MIXED", ["MULTIPLE_VARIANCE_DIMENSIONS"]


def historical_audit(path: Path) -> tuple[dict[str, object], ...]:
    with zipfile.ZipFile(path) as archive:
        by_run = _candidate_rows(archive)
        stability = read_json_bytes(
            archive.read("reports/internal/proofs/52-core-stability.json")
        )
    stability_by_ticker = {
        str(row["ticker"]): row for row in stability.get("rows") or []
    }
    rows = []
    for ticker in sorted(by_run["A"]):
        candidates = [by_run[run][ticker] for run in RUNS]
        classification, reasons = _classify(candidates)
        balances = [float(row["directional_balance"]["buy"]) for row in candidates]
        dominant_sets = [_ref_set(row, "dominant_evidence") for row in candidates]
        anchor_sets = [
            _ref_set(row, "material_directional_anchor_basis") for row in candidates
        ]
        driver_sets = [
            _ref_set(row, "buy_drivers") | _ref_set(row, "sell_drivers")
            for row in candidates
        ]
        rows.append(
            {
                "ticker": ticker,
                "historical_stability_classification": stability_by_ticker[ticker][
                    "classification"
                ],
                "root_cause_classification": classification,
                "classification_reasons": reasons,
                "direction_values": [row.get("overall_direction") for row in candidates],
                "buy_balance_values": balances,
                "hold_lean_values": [row.get("hold_lean") for row in candidates],
                "confidence_values": [
                    row.get("directional_confidence") for row in candidates
                ],
                "max_buy_balance_distance": max(balances) - min(balances),
                "buy_sell_reversal": int(
                    {"BUY", "SELL"}
                    <= {str(row.get("overall_direction")) for row in candidates}
                ),
                "dominant_ref_min_pairwise_jaccard": _pairwise_min_overlap(
                    dominant_sets
                ),
                "anchor_ref_min_pairwise_jaccard": _pairwise_min_overlap(anchor_sets),
                "driver_ref_min_pairwise_jaccard": _pairwise_min_overlap(driver_sets),
                "common_dominant_refs": sorted(set.intersection(*dominant_sets)),
                "common_driver_refs": sorted(set.intersection(*driver_sets)),
                "runs": {run: _run_view(by_run[run][ticker]) for run in RUNS},
            }
        )
    return tuple(rows)


def run_offline_audit(args: argparse.Namespace) -> None:
    if args.output_root.exists() or args.report_dir.exists():
        raise ValueError("NEW_AUDIT_OUTPUT_AND_REPORT_DIRECTORIES_REQUIRED")
    provenance = repository_provenance()
    integrity = verify_latest_result(args.latest_result_zip)
    rows = historical_audit(args.latest_result_zip)
    unstable_rows = [
        row for row in rows if row["historical_stability_classification"] == "UNSTABLE"
    ]
    nonstable_rows = [
        row for row in rows if row["historical_stability_classification"] != "STABLE"
    ]
    classifications = {
        name: sum(row["root_cause_classification"] == name for row in rows)
        for name in (
            "ADJACENT_BALANCE_CALIBRATION_AMBIGUITY",
            "MATERIAL_EVIDENCE_SELECTION_VARIANCE",
            "OPPOSING_EVIDENCE_INTERPRETATION_VARIANCE",
            "CONFIDENCE_ONLY_VARIANCE",
            "TRUE_SEMANTIC_REASONING_DIVERGENCE",
            "MIXED",
            "STABLE",
        )
    }
    unstable_adjacent = sum(
        row["root_cause_classification"]
        == "ADJACENT_BALANCE_CALIBRATION_AMBIGUITY"
        for row in unstable_rows
    )
    unstable_true_divergence = sum(
        row["root_cause_classification"] == "TRUE_SEMANTIC_REASONING_DIVERGENCE"
        for row in unstable_rows
    )
    root_cause_confirmed = bool(
        unstable_rows
        and unstable_adjacent > len(unstable_rows) / 2
        and unstable_true_divergence < unstable_adjacent
        and not any(row["buy_sell_reversal"] for row in unstable_rows)
    )
    matrix = {
        "contract": "directional-instability-subject-matrix-v1",
        "subject_count": len(rows),
        "historical_stability_counts": {
            name: sum(row["historical_stability_classification"] == name for row in rows)
            for name in ("STABLE", "BOUNDARY_UNCERTAINTY", "UNSTABLE")
        },
        "rows": rows,
        "model_calls": 0,
        "historical_artifacts_mutated": 0,
        "status": "PASS",
    }
    anchors = {
        "contract": "directional-anchor-set-comparison-v1",
        "subject_count": len(rows),
        "rows": [
            {
                "ticker": row["ticker"],
                "historical_stability_classification": row[
                    "historical_stability_classification"
                ],
                "root_cause_classification": row["root_cause_classification"],
                "dominant_ref_min_pairwise_jaccard": row[
                    "dominant_ref_min_pairwise_jaccard"
                ],
                "anchor_ref_min_pairwise_jaccard": row[
                    "anchor_ref_min_pairwise_jaccard"
                ],
                "driver_ref_min_pairwise_jaccard": row[
                    "driver_ref_min_pairwise_jaccard"
                ],
                "common_dominant_refs": row["common_dominant_refs"],
                "common_driver_refs": row["common_driver_refs"],
                "per_run_anchor_basis": {
                    run: row["runs"][run]["material_directional_anchor_basis"]
                    for run in RUNS
                },
                "per_run_dominant_refs": {
                    run: (row["runs"][run]["dominant_evidence"] or {}).get(
                        "evidence_refs", []
                    )
                    for run in RUNS
                },
            }
            for row in rows
        ],
        "status": "PASS",
    }
    rationale = {
        "contract": "directional-rationale-uncertainty-comparison-v1",
        "subject_count": len(rows),
        "rows": [
            {
                "ticker": row["ticker"],
                "historical_stability_classification": row[
                    "historical_stability_classification"
                ],
                "root_cause_classification": row["root_cause_classification"],
                "runs": {
                    run: {
                        "core_investment_judgment": row["runs"][run][
                            "core_investment_judgment"
                        ],
                        "uncertainty_limit": row["runs"][run]["uncertainty_limit"],
                        "fundamental_new_buyer": row["runs"][run][
                            "fundamental_new_buyer"
                        ],
                        "fundamental_holder": row["runs"][run][
                            "fundamental_holder"
                        ],
                    }
                    for run in RUNS
                },
            }
            for row in rows
        ],
        "status": "PASS",
    }
    classification = {
        "contract": "directional-instability-root-cause-classification-v1",
        "nonstable_count": len(nonstable_rows),
        "unstable_count": len(unstable_rows),
        "adjacent_calibration_count": unstable_adjacent,
        "all_nonstable_adjacent_calibration_count": sum(
            row["root_cause_classification"]
            == "ADJACENT_BALANCE_CALIBRATION_AMBIGUITY"
            for row in nonstable_rows
        ),
        "material_evidence_variance_count": sum(
            row["root_cause_classification"]
            == "MATERIAL_EVIDENCE_SELECTION_VARIANCE"
            for row in unstable_rows
        ),
        "true_semantic_divergence_count": unstable_true_divergence,
        "buy_sell_reversal_count": sum(row["buy_sell_reversal"] for row in rows),
        "all_subject_classification_counts": classifications,
        "unstable_tickers": [row["ticker"] for row in unstable_rows],
        "root_cause_result": (
            "GENERIC_DIRECTIONAL_CALIBRATION_ROOT_CAUSE_CONFIRMED"
            if root_cause_confirmed
            else "GENERIC_DIRECTIONAL_CALIBRATION_ROOT_CAUSE_NOT_CONFIRMED"
        ),
        "status": "PASS" if root_cause_confirmed else "STOP",
    }
    decision = {
        "contract": "directional-calibration-architecture-decision-v1",
        "root_cause_result": classification["root_cause_result"],
        "architecture_mutation_authorized": root_cause_confirmed,
        "allowed_mutation": (
            "GENERIC_ORDINAL_DIRECTIONAL_BALANCE_RUBRIC_AND_SYMMETRIC_"
            "CONSERVATIVE_ADJACENT_BUCKET_TIE_BREAK"
            if root_cause_confirmed
            else "NONE"
        ),
        "directional_threshold_change_allowed": False,
        "fixed_weight_scorecard_allowed": False,
        "majority_vote_allowed": False,
        "ticker_specific_exception_allowed": False,
        "price_timing_mutation_allowed": False,
        "next_gate": (
            "GENERIC_FICTIONAL_REPEATED_CALIBRATION_CANARY"
            if root_cause_confirmed
            else "STOP_GENERIC_DIRECTIONAL_CORE_REASONING_ARCHITECTURE_REVIEW"
        ),
        "status": "PASS" if root_cause_confirmed else "STOP",
    }
    args.output_root.mkdir(parents=True)
    write_json(args.output_root / "historical-audit-matrix.json", matrix)
    write_json(args.output_root / "root-cause-classification.json", classification)
    for number, document in enumerate(
        (provenance, integrity, matrix, anchors, rationale, classification, decision),
        start=1,
    ):
        write_report(args.report_dir, number, document)
    state = {
        "contract": PROGRAM_CONTRACT,
        "state": (
            "OFFLINE_ROOT_CAUSE_CONFIRMED"
            if root_cause_confirmed
            else "STOPPED_ROOT_CAUSE_NOT_CONFIRMED"
        ),
        "base_sha": LATEST_FINAL_HEAD,
        "work_instruction_commit": provenance["work_instruction_commit"],
        "offline_audit_sha256": canonical_sha256(matrix),
        "root_cause_classification_sha256": canonical_sha256(classification),
        "calibration_root_cause": classification["root_cause_result"],
        "model_invocation_count": 0,
        "fresh_real_cohort_consumed": 0,
    }
    write_json(args.output_root / "program-state.json", state)
    print(json.dumps(state, ensure_ascii=False, sort_keys=True), flush=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--audit", action="store_true", required=True)
    parser.add_argument("--latest-result-zip", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--report-dir", type=Path, required=True)
    args = parser.parse_args()
    args.latest_result_zip = args.latest_result_zip.expanduser().resolve()
    args.output_root = args.output_root.expanduser().resolve()
    args.report_dir = args.report_dir.expanduser().resolve()
    return args


def main() -> None:
    args = parse_args()
    run_offline_audit(args)


if __name__ == "__main__":
    main()
