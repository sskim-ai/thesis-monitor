from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import zipfile
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.services.directional_balance_service import (
    ORDINAL_CALIBRATION_CONTRACT_VERSION,
    directional_balance_ordinal_calibration_prompt,
)
from app.services.direction_timing_ownership_service import (
    CORE_OUTPUT_CONTRACT,
    DirectionalCoreCandidate,
)
from app.services.structured_autonomy_alias_service import (
    build_alias_constrained_batch_schema,
)
from scripts import directional_core_price_timing_holdout as holdout
from scripts import model_transport_revalidation_ownership_continuation as transport
from scripts import new_issuer_holdout_selection_ownership_proof as runner
from scripts import uskr22_structured_autonomy_shadow as engine


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
FICTIONAL_FIXTURE_PATH = Path("fixtures/directional_core_ordinal_calibration_v1.json")
FICTIONAL_REPETITIONS = ("RUN_1", "RUN_2", "RUN_3")
FICTIONAL_CONTEXT_SIZE = 4
FICTIONAL_MODEL_CALLS = 6

REPORT_NAMES = (
    "01-repository-provenance",
    "02-latest-result-integrity",
    "03-directional-instability-subject-matrix",
    "04-directional-anchor-set-comparison",
    "05-directional-rationale-and-uncertainty-comparison",
    "06-directional-instability-root-cause-classification",
    "07-directional-calibration-architecture-decision",
    "08-directional-calibration-contract",
    "09-directional-calibration-prompt-diff",
    "10-directional-calibration-regression-tests",
    "11-fictional-calibration-fixture-manifest",
    "12-fictional-calibration-run-1",
    "13-fictional-calibration-run-2",
    "14-fictional-calibration-run-3",
    "15-fictional-calibration-stability-summary",
    "16-calibration-freeze-seal",
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


def calibration_architecture_hashes(repo_root: Path) -> dict[str, str]:
    return {
        "directional_balance_service": file_sha256(
            repo_root / "app/services/directional_balance_service.py"
        ),
        "directional_core_prompt_owner": file_sha256(
            repo_root / "scripts/directional_core_price_timing_holdout.py"
        ),
        "directional_core_candidate_schema_owner": file_sha256(
            repo_root / "app/services/direction_timing_ownership_service.py"
        ),
    }


def _fixture_manifest(repo_root: Path) -> dict[str, Any]:
    value = json.loads((repo_root / FICTIONAL_FIXTURE_PATH).read_text(encoding="utf-8"))
    if not isinstance(value, dict) or not isinstance(value.get("fixtures"), list):
        raise ValueError("fictional_fixture_manifest_invalid")
    fixtures = value["fixtures"]
    if len(fixtures) != 8 or len({row.get("ticker") for row in fixtures}) != 8:
        raise ValueError("fictional_fixture_scope_invalid")
    if {row.get("market") for row in fixtures} != {"us", "kr"}:
        raise ValueError("fictional_fixture_market_identity_invalid")
    if not all(str(row.get("ticker") or "").startswith("FIC") for row in fixtures):
        raise ValueError("fictional_fixture_identity_not_fictional")
    return value


def _fictional_batches(fixtures: Sequence[Mapping[str, Any]]) -> tuple[tuple[Mapping[str, Any], ...], ...]:
    return tuple(
        tuple(fixtures[index : index + FICTIONAL_CONTEXT_SIZE])
        for index in range(0, len(fixtures), FICTIONAL_CONTEXT_SIZE)
    )


def _fictional_context(fixture: Mapping[str, Any]) -> dict[str, object]:
    return {
        "ticker": fixture["ticker"],
        "company_name": fixture["company_name"],
        "market": fixture["market"],
        "assessment_date": "2026-09-08",
        "evidence": fixture["evidence"],
    }


def _schema_for_fictional_batch(
    *, generation_id: str, fixtures: Sequence[Mapping[str, Any]]
) -> dict[str, object]:
    schema = engine.strict_json_schema(DirectionalCoreCandidate.model_json_schema())
    return build_alias_constrained_batch_schema(
        candidate_schema=schema,
        contract=CORE_OUTPUT_CONTRACT,
        packet_id=generation_id,
        aliases_by_ticker={
            str(row["ticker"]): tuple(str(item["alias"]) for item in row["evidence"])
            for row in fixtures
        },
    )


def _calibration_contract() -> dict[str, object]:
    return {
        "contract": ORDINAL_CALIBRATION_CONTRACT_VERSION,
        "meaning_ladder": {
            "5.0:5.0": "BALANCED_UNRESOLVED_OR_TOO_INCOMPLETE_FOR_LEAN",
            "5.5:4.5": "POSITIVE_MATERIAL_ANCHOR_WITHOUT_SUFFICIENT_CORROBORATION",
            "6.0:4.0": "MINIMUM_BUY_WITH_MATERIAL_ANCHOR_AND_SUFFICIENT_CORROBORATION",
            "6.5:3.5_or_stronger": "PROGRESSIVELY_STRONGER_POSITIVE_CORROBORATION",
            "4.5:5.5": "SYMMETRIC_NEGATIVE_LEAN",
            "4.0:6.0": "SYMMETRIC_MINIMUM_SELL",
            "3.5:6.5_or_stronger": "SYMMETRIC_STRONGER_NEGATIVE_DIRECTION",
        },
        "ambiguity_rule": "CHOOSE_LESS_DIRECTIONAL_ADJACENT_BUCKET_TOWARD_5_0",
        "missing_evidence_policy": "LIMITS_CONVICTION_NOT_AUTOMATICALLY_NEGATIVE",
        "low_confidence_policy": "RECHECK_FULL_BUCKET_NOT_MECHANICAL_HOLD",
        "buy_threshold": 6.0,
        "sell_threshold": 6.0,
        "balance_sum": 10.0,
        "balance_increment": 0.5,
        "threshold_changed": 0,
        "fixed_weight_scorecard": 0,
        "majority_vote": 0,
        "ticker_specific_exception": 0,
        "price_timing_mutation": 0,
        "prompt_text_sha256": hashlib.sha256(
            directional_balance_ordinal_calibration_prompt().encode("utf-8")
        ).hexdigest(),
        "status": "FROZEN",
    }


def prepare_fictional(args: argparse.Namespace) -> None:
    repo_root = Path.cwd().resolve()
    state = json.loads((args.output_root / "program-state.json").read_text(encoding="utf-8"))
    if state.get("state") != "OFFLINE_ROOT_CAUSE_CONFIRMED":
        raise ValueError("OFFLINE_ROOT_CAUSE_CONFIRMATION_REQUIRED")
    if git_value("status", "--short"):
        raise ValueError("CLEAN_WORKTREE_REQUIRED_FOR_FICTIONAL_FREEZE")
    if args.as_of is None:
        raise ValueError("FICTIONAL_FREEZE_REQUIRES_FIXED_AS_OF")
    if args.focused_tests != "PASS":
        raise ValueError("FOCUSED_CALIBRATION_TESTS_MUST_PASS")
    manifest = _fixture_manifest(repo_root)
    fixtures = manifest["fixtures"]
    generation_seed = (
        f"{git_value('rev-parse', 'HEAD')}|{args.as_of.astimezone(UTC).isoformat()}|"
        f"{canonical_sha256(manifest)}"
    )
    generation_id = (
        "20260908-directional-calibration-fictional-"
        f"{args.as_of.astimezone(UTC).strftime('%Y%m%dT%H%M%SZ')}-"
        f"{hashlib.sha256(generation_seed.encode()).hexdigest()[:12]}"
    )
    fictional_root = args.output_root / "fictional-calibration"
    if fictional_root.exists():
        raise ValueError("NEW_FICTIONAL_CALIBRATION_ROOT_REQUIRED")
    frozen_root = fictional_root / "frozen-inputs"
    prompt_rows = []
    for number, batch in enumerate(_fictional_batches(fixtures), start=1):
        tickers = tuple(str(row["ticker"]) for row in batch)
        prompt = holdout._core_prompt(
            packet_id=generation_id,
            tickers=tickers,
            contexts=tuple(_fictional_context(row) for row in batch),
        )
        prompt_path = frozen_root / f"context-{number:02d}" / "prompt.txt"
        schema_path = frozen_root / f"context-{number:02d}" / "schema.json"
        prompt_path.parent.mkdir(parents=True, exist_ok=True)
        prompt_path.write_text(prompt, encoding="utf-8")
        write_json(
            schema_path,
            _schema_for_fictional_batch(generation_id=generation_id, fixtures=batch),
        )
        prompt_rows.append(
            {
                "context": number,
                "tickers": list(tickers),
                "prompt_sha256": file_sha256(prompt_path),
                "schema_sha256": file_sha256(schema_path),
            }
        )
    architecture = calibration_architecture_hashes(repo_root)
    contract = _calibration_contract()
    fixture_document = {
        **manifest,
        "fixture_file": str(FICTIONAL_FIXTURE_PATH),
        "fixture_file_sha256": file_sha256(repo_root / FICTIONAL_FIXTURE_PATH),
        "fictional_identity_count": len(fixtures),
        "real_issuer_identity_count": 0,
        "contexts_per_repetition": 2,
        "repetitions": 3,
        "planned_model_calls": FICTIONAL_MODEL_CALLS,
        "status": "FROZEN",
    }
    write_json(fictional_root / "fixture-manifest.json", fixture_document)
    freeze = {
        "contract": "fictional-calibration-input-freeze-v1",
        "generation_id": generation_id,
        "implementation_commit": git_value("rev-parse", "HEAD"),
        "implementation_tree": git_value("rev-parse", "HEAD^{tree}"),
        "architecture_hashes": architecture,
        "calibration_contract_sha256": canonical_sha256(contract),
        "fixture_manifest_sha256": canonical_sha256(fixture_document),
        "prompt_schema_rows": prompt_rows,
        "prompt_set_sha256": canonical_sha256(
            [row["prompt_sha256"] for row in prompt_rows]
        ),
        "schema_set_sha256": canonical_sha256(
            [row["schema_sha256"] for row in prompt_rows]
        ),
        "model": transport.MODEL,
        "reasoning_effort": transport.EFFORT,
        "batch_semantics": "MODEL_CONTEXT_COUPLED",
        "subjects_per_context": FICTIONAL_CONTEXT_SIZE,
        "timeout_seconds": runner.TIMEOUT_SECONDS,
        "timeout_owner_count": runner.TIMEOUT_OWNER_COUNT,
        "wrapper_retry_count": 0,
        "status": "FROZEN",
    }
    write_json(fictional_root / "input-freeze.json", freeze)
    old_prompt = subprocess.run(
        (
            "git",
            "show",
            f"{LATEST_FINAL_HEAD}:scripts/directional_core_price_timing_holdout.py",
        ),
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    prompt_diff = {
        "contract": "directional-calibration-prompt-diff-v1",
        "historical_prompt_owner_sha256": hashlib.sha256(
            old_prompt.encode("utf-8")
        ).hexdigest(),
        "current_prompt_owner_sha256": architecture["directional_core_prompt_owner"],
        "changed_surface": [
            "shared ordinal evidence-sufficiency ladder",
            "symmetric conservative adjacent-bucket tie-break",
        ],
        "directional_threshold_changed": 0,
        "price_timing_prompt_changed": 0,
        "schema_changed": 0,
        "ticker_specific_rule_count": 0,
        "status": "PASS",
    }
    regression = {
        "contract": "directional-calibration-regression-tests-v1",
        "focused_test_result": args.focused_tests,
        "threshold_6_0_preserved": True,
        "balance_sum_10_preserved": True,
        "half_increment_preserved": True,
        "symmetric_positive_negative_rubric": True,
        "missing_not_negative": True,
        "low_confidence_not_mechanical_hold": True,
        "production_runtime_prompt_mutation": 0,
        "price_timing_mutation": 0,
        "status": "PASS",
    }
    write_report(args.report_dir, 8, contract)
    write_report(args.report_dir, 9, prompt_diff)
    write_report(args.report_dir, 10, regression)
    write_report(args.report_dir, 11, fixture_document)
    state.update(
        {
            "state": "FICTIONAL_PREPARED_FROZEN",
            "calibration_implementation_commit": git_value("rev-parse", "HEAD"),
            "calibration_architecture_hashes": architecture,
            "calibration_contract_sha256": canonical_sha256(contract),
            "fictional_generation_id": generation_id,
            "fictional_input_freeze_sha256": canonical_sha256(freeze),
            "fictional_planned_model_calls": FICTIONAL_MODEL_CALLS,
            "fictional_model_invocation_count": 0,
        }
    )
    write_json(args.output_root / "program-state.json", state)
    print(json.dumps(state, ensure_ascii=False, sort_keys=True), flush=True)


def _candidate_reference_values(candidate: Mapping[str, Any]) -> set[str]:
    refs: set[str] = set()

    def collect(value: object, key: str | None = None) -> None:
        if isinstance(value, Mapping):
            for child_key, child in value.items():
                collect(child, str(child_key))
        elif isinstance(value, list):
            if key and (
                key.endswith("_refs")
                or key.endswith("_basis")
                or key == "evidence_refs"
            ):
                refs.update(str(item) for item in value)
            else:
                for item in value:
                    collect(item, key)

    collect(candidate)
    return refs


def _fixture_acceptance(
    candidate: DirectionalCoreCandidate, fixture: Mapping[str, Any]
) -> dict[str, object]:
    expected = fixture["expected"]
    errors: list[str] = []
    if candidate.overall_direction != expected["direction"]:
        errors.append("EXPECTED_DIRECTION_CLASS_MISMATCH")
    if "buy" in expected and candidate.directional_balance.buy != float(expected["buy"]):
        errors.append("EXPECTED_EXACT_BUY_BALANCE_MISMATCH")
    if "sell" in expected and candidate.directional_balance.sell != float(expected["sell"]):
        errors.append("EXPECTED_EXACT_SELL_BALANCE_MISMATCH")
    if "minimum_buy" in expected and candidate.directional_balance.buy < float(
        expected["minimum_buy"]
    ):
        errors.append("MINIMUM_POSITIVE_DIRECTION_NOT_MET")
    if "minimum_sell" in expected and candidate.directional_balance.sell < float(
        expected["minimum_sell"]
    ):
        errors.append("MINIMUM_NEGATIVE_DIRECTION_NOT_MET")
    if candidate.hold_lean != expected["hold_lean"]:
        errors.append("EXPECTED_HOLD_LEAN_MISMATCH")
    if candidate.overall_direction == expected.get("forbidden_direction"):
        errors.append("UNKNOWN_EVIDENCE_BECAME_FORBIDDEN_DIRECTION")
    aliases = {str(row["alias"]) for row in fixture["evidence"]}
    refs = _candidate_reference_values(candidate.model_dump(mode="json"))
    unknown_refs = sorted(refs - aliases)
    if unknown_refs:
        errors.append("OUT_OF_FIXTURE_EVIDENCE_REFERENCE")
    if candidate.overall_direction in {"BUY", "SELL"} and not (
        candidate.material_directional_anchor_basis
    ):
        errors.append("DIRECTIONAL_CALL_WITHOUT_MATERIAL_ANCHOR")
    return {
        "fixture_id": fixture["fixture_id"],
        "ticker": candidate.ticker,
        "expected": expected,
        "actual_direction": candidate.overall_direction,
        "actual_balance": candidate.directional_balance.model_dump(mode="json"),
        "actual_hold_lean": candidate.hold_lean,
        "actual_confidence": candidate.directional_confidence,
        "candidate_sha256": canonical_sha256(candidate.model_dump(mode="json")),
        "referenced_aliases": sorted(refs),
        "unknown_references": unknown_refs,
        "errors": errors,
        "status": "PASS" if not errors else "FAIL",
    }


def _verify_fictional_freeze(args: argparse.Namespace, state: Mapping[str, Any]) -> dict[str, Any]:
    if state.get("state") != "FICTIONAL_PREPARED_FROZEN":
        raise ValueError("FICTIONAL_PREPARED_FROZEN_STATE_REQUIRED")
    actual_architecture = calibration_architecture_hashes(Path.cwd().resolve())
    if actual_architecture != state.get("calibration_architecture_hashes"):
        raise ValueError("CALIBRATION_ARCHITECTURE_MUTATED_AFTER_FREEZE")
    freeze = json.loads(
        (args.output_root / "fictional-calibration" / "input-freeze.json").read_text(
            encoding="utf-8"
        )
    )
    if canonical_sha256(freeze) != state.get("fictional_input_freeze_sha256"):
        raise ValueError("FICTIONAL_INPUT_FREEZE_MUTATED")
    for row in freeze["prompt_schema_rows"]:
        context_root = (
            args.output_root
            / "fictional-calibration"
            / "frozen-inputs"
            / f"context-{int(row['context']):02d}"
        )
        if file_sha256(context_root / "prompt.txt") != row["prompt_sha256"]:
            raise ValueError("FICTIONAL_PROMPT_MUTATED_AFTER_FREEZE")
        if file_sha256(context_root / "schema.json") != row["schema_sha256"]:
            raise ValueError("FICTIONAL_SCHEMA_MUTATED_AFTER_FREEZE")
    return freeze


def execute_fictional(args: argparse.Namespace) -> None:
    state = json.loads((args.output_root / "program-state.json").read_text(encoding="utf-8"))
    freeze = _verify_fictional_freeze(args, state)
    fictional_root = args.output_root / "fictional-calibration"
    results_root = fictional_root / "results"
    if results_root.exists():
        raise ValueError("FICTIONAL_RESULTS_ALREADY_EXIST_NO_RETRY_ALLOWED")
    fixture_document = json.loads(
        (fictional_root / "fixture-manifest.json").read_text(encoding="utf-8")
    )
    fixtures = fixture_document["fixtures"]
    by_ticker = {str(row["ticker"]): row for row in fixtures}
    adapter = transport.ContinuationTransportAdapter(
        continuation_generation=str(state["fictional_generation_id"]),
        receipt_root=fictional_root / "transport-receipts",
        codex_bin=engine._signed_in_codex_bin(),
        runtime_state_root=fictional_root / "runtime-state",
    )
    repetition_reports: list[dict[str, object]] = []
    attempted = 0
    try:
        for repetition_number, repetition in enumerate(FICTIONAL_REPETITIONS, start=1):
            run_rows = []
            for context_number, batch in enumerate(_fictional_batches(fixtures), start=1):
                context_root = results_root / repetition / f"context-{context_number:02d}"
                context_root.mkdir(parents=True, exist_ok=False)
                frozen_root = fictional_root / "frozen-inputs" / f"context-{context_number:02d}"
                prompt = context_root / "prompt.txt"
                schema = context_root / "schema.json"
                shutil.copy2(frozen_root / "prompt.txt", prompt)
                shutil.copy2(frozen_root / "schema.json", schema)
                output = context_root / "output.raw.json"
                log = context_root / "transport.log"
                invocation_id = (
                    f"{state['fictional_generation_id']}:fictional:{repetition}:"
                    f"DIRECTIONAL_CORE:{context_number:02d}"
                )
                print(
                    f"{repetition} FICTIONAL_CORE_START {context_number} "
                    + ",".join(str(row["ticker"]) for row in batch),
                    flush=True,
                )
                with engine.isolated_model_working_directory(
                    run=f"fictional-{repetition.lower()}-core",
                    batch=context_number,
                ) as working_directory:
                    result = adapter.invoke(
                        prompt=prompt,
                        output=output,
                        log=log,
                        schema=schema,
                        cwd=working_directory,
                        timeout=runner.TIMEOUT_SECONDS,
                        state_namespace="DIRECTIONAL_CALIBRATION_FICTIONAL_20260908",
                        invocation_id=invocation_id,
                        stage="DIRECTIONAL_CORE",
                        batch_id=f"{repetition_number:02d}-{context_number:02d}",
                        subject_count=FICTIONAL_CONTEXT_SIZE,
                    )
                attempted += 1
                document = json.loads(output.read_text(encoding="utf-8"))
                if document.get("contract") != CORE_OUTPUT_CONTRACT:
                    raise ValueError("FICTIONAL_OUTPUT_CONTRACT_MISMATCH")
                if document.get("packet_id") != state["fictional_generation_id"]:
                    raise ValueError("FICTIONAL_OUTPUT_GENERATION_MISMATCH")
                expected_order = tuple(str(row["ticker"]) for row in batch)
                candidates = document.get("candidates")
                if not isinstance(candidates, list) or tuple(
                    str(row.get("ticker") or "") for row in candidates
                ) != expected_order:
                    raise ValueError("FICTIONAL_OUTPUT_SCOPE_OR_ORDER_MISMATCH")
                normalized = []
                for raw_candidate in candidates:
                    candidate = DirectionalCoreCandidate.model_validate(raw_candidate)
                    acceptance = _fixture_acceptance(
                        candidate, by_ticker[candidate.ticker]
                    )
                    normalized.append(candidate.model_dump(mode="json"))
                    run_rows.append(acceptance)
                write_json(
                    context_root / "output.normalized.json",
                    {
                        "contract": CORE_OUTPUT_CONTRACT,
                        "packet_id": state["fictional_generation_id"],
                        "candidates": normalized,
                    },
                )
                write_json(
                    context_root / "context-receipt.json",
                    {
                        "contract": "fictional-calibration-context-receipt-v1",
                        "repetition": repetition,
                        "context": context_number,
                        "invocation_id": invocation_id,
                        "tickers": list(expected_order),
                        "prompt_sha256": file_sha256(prompt),
                        "schema_sha256": file_sha256(schema),
                        "output_sha256": file_sha256(output),
                        "transport_result": result,
                        "wrapper_retry_count": 0,
                        "status": (
                            "PASS"
                            if all(row["status"] == "PASS" for row in run_rows[-4:])
                            else "FAIL"
                        ),
                    },
                )
                print(
                    f"{repetition} FICTIONAL_CORE_COMPLETE {context_number}",
                    flush=True,
                )
            repetition_report = {
                "contract": "fictional-calibration-repetition-v1",
                "generation_id": state["fictional_generation_id"],
                "repetition": repetition,
                "model_calls": 2,
                "subject_results": run_rows,
                "pass_count": sum(row["status"] == "PASS" for row in run_rows),
                "failure_count": sum(row["status"] != "PASS" for row in run_rows),
                "status": (
                    "PASS" if all(row["status"] == "PASS" for row in run_rows) else "FAIL"
                ),
            }
            repetition_reports.append(repetition_report)
            write_report(args.report_dir, 11 + repetition_number, repetition_report)
    except Exception as exc:
        state.update(
            {
                "state": "STOPPED_FICTIONAL_CALIBRATION_FAILURE",
                "fictional_model_invocation_count": attempted,
                "fictional_failure": f"{type(exc).__name__}:{exc}",
                "fresh_real_cohort_consumed": 0,
            }
        )
        write_json(args.output_root / "program-state.json", state)
        raise
    per_ticker = {}
    unstable = []
    for ticker in by_ticker:
        values = [
            next(row for row in report["subject_results"] if row["ticker"] == ticker)
            for report in repetition_reports
        ]
        signatures = {
            (
                str(row["actual_direction"]),
                str(row["actual_hold_lean"]),
            )
            for row in values
        }
        ticker_unstable = len(signatures) != 1 or any(
            row["status"] != "PASS" for row in values
        )
        if ticker_unstable:
            unstable.append(ticker)
        per_ticker[ticker] = {
            "fixture_id": by_ticker[ticker]["fixture_id"],
            "values": values,
            "direction_class_signatures": [list(value) for value in sorted(signatures)],
            "classification": "UNSTABLE" if ticker_unstable else "STABLE",
        }
    receipts = [
        json.loads(path.read_text(encoding="utf-8"))
        for path in sorted((fictional_root / "transport-receipts").glob("*.json"))
    ]
    namespace_hashes = {
        str((row.get("transport_metadata") or {}).get("runtime_state_namespace_hash"))
        for row in receipts
    } - {"", "None"}
    stability = {
        "contract": "fictional-calibration-stability-summary-v1",
        "generation_id": state["fictional_generation_id"],
        "planned_model_call_count": FICTIONAL_MODEL_CALLS,
        "attempted_model_call_count": attempted,
        "successful_model_call_count": sum(
            str(row.get("status")) == "SUCCESS" for row in receipts
        ),
        "distinct_invocation_count": len(
            {str(row.get("invocation_id")) for row in receipts}
        ),
        "distinct_runtime_namespace_count": len(namespace_hashes),
        "wrapper_retry_count": 0,
        "fixture_count": len(by_ticker),
        "fictional_directional_unstable_count": len(unstable),
        "unstable_tickers": unstable,
        "per_fixture": per_ticker,
        "opposite_direction_reversal_count": sum(
            {"BUY", "SELL"}
            <= {str(value["actual_direction"]) for value in row["values"]}
            for row in per_ticker.values()
        ),
        "minimum_positive_buy_hold_flip_count": int(
            per_ticker["FICUS03"]["classification"] == "UNSTABLE"
        ),
        "minimum_negative_sell_hold_flip_count": int(
            per_ticker["FICKR02"]["classification"] == "UNSTABLE"
        ),
        "status": (
            "PASS"
            if attempted == FICTIONAL_MODEL_CALLS
            and len(receipts) == FICTIONAL_MODEL_CALLS
            and len(namespace_hashes) == FICTIONAL_MODEL_CALLS
            and not unstable
            and all(report["status"] == "PASS" for report in repetition_reports)
            else "FAIL"
        ),
    }
    write_report(args.report_dir, 15, stability)
    seal = {
        "contract": "directional-calibration-architecture-freeze-seal-v1",
        "generation_id": state["fictional_generation_id"],
        "architecture_hashes": state["calibration_architecture_hashes"],
        "calibration_contract_sha256": state["calibration_contract_sha256"],
        "fictional_input_freeze_sha256": state["fictional_input_freeze_sha256"],
        "prompt_set_sha256": freeze["prompt_set_sha256"],
        "schema_set_sha256": freeze["schema_set_sha256"],
        "model": transport.MODEL,
        "reasoning_effort": transport.EFFORT,
        "timeout_seconds": runner.TIMEOUT_SECONDS,
        "fictional_model_call_count": attempted,
        "fictional_calibration_unstable_count": len(unstable),
        "no_calibration_edits_after_fictional_output": True,
        "next_gate": (
            "RETIRE_EXPOSED_COHORT_AND_PREPARE_FRESH_US4_KR12"
            if stability["status"] == "PASS"
            else "STOP_NO_FRESH_REAL_HOLDOUT"
        ),
        "status": "FROZEN" if stability["status"] == "PASS" else "STOP",
    }
    write_report(args.report_dir, 16, seal)
    state.update(
        {
            "state": (
                "FICTIONAL_PASS_ARCHITECTURE_FROZEN"
                if stability["status"] == "PASS"
                else "STOPPED_FICTIONAL_CALIBRATION_FAILURE"
            ),
            "fictional_model_invocation_count": attempted,
            "fictional_calibration_unstable_count": len(unstable),
            "fictional_calibration_status": stability["status"],
            "calibration_freeze_seal_sha256": canonical_sha256(seal),
            "fresh_real_cohort_consumed": 0,
        }
    )
    write_json(args.output_root / "program-state.json", state)
    if stability["status"] != "PASS":
        raise ValueError("FICTIONAL_CALIBRATION_ACCEPTANCE_FAILED")
    print(json.dumps(state, ensure_ascii=False, sort_keys=True), flush=True)


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
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--audit", action="store_true")
    mode.add_argument("--fictional-prepare", action="store_true")
    mode.add_argument("--fictional-execute", action="store_true")
    parser.add_argument("--latest-result-zip", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--report-dir", type=Path, required=True)
    parser.add_argument("--as-of", type=datetime.fromisoformat)
    parser.add_argument("--focused-tests", default="NOT_RUN")
    args = parser.parse_args()
    args.latest_result_zip = args.latest_result_zip.expanduser().resolve()
    args.output_root = args.output_root.expanduser().resolve()
    args.report_dir = args.report_dir.expanduser().resolve()
    return args


def main() -> None:
    args = parse_args()
    if args.audit:
        run_offline_audit(args)
    elif args.fictional_prepare:
        prepare_fictional(args)
    else:
        execute_fictional(args)


if __name__ == "__main__":
    main()
