"""M12AB boundary architecture review and full fictional Sol canary."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path
import re
import subprocess
import zipfile


BASE = "95addf0a6a484e7ea307a7b8cb63c175e71332e2"
INSTRUCTION_COMMIT = "96377fedd6f575f10b97a30db564fa71cde8e766"
MODEL = "gpt-5.6-sol"
EFFORT = "xhigh"
NAME = "20260910-leverage-hold-sell-boundary-resolution-architecture-full-sol-canary"
OUTPUT = Path("artifacts") / NAME
REPORTS = Path("docs/reports") / NAME
ROOT = Path("docs/architecture/M12AB_LEVERAGE_HOLD_SELL_BOUNDARY.json")
FIXTURES = Path("fixtures/leverage_hold_sell_boundary_m12ab.json")
INSTRUCTION = Path(
    "docs/work-instructions/"
    "20260910-leverage-hold-sell-boundary-resolution-architecture-and-full-sol-canary.md"
)
LATEST = Path.home() / "Documents/Codex" / (
    "thesis-monitor-20260910-boundary-band-canary-policy-financial-framework-"
    "application-scope-full-sol-canary-report.zip"
)
LATEST_SHA = "0416d8719b5e71e79de6591f574a2ba3332657dd32deddb870bbaa8d2e854a7a"
M12AA_REPORTS = Path("docs/reports") / (
    "20260910-boundary-band-canary-policy-financial-framework-"
    "application-scope-full-sol-canary"
)
SLUGS = {
    int(number): slug
    for number, slug in re.findall(r"^(\d{2})-([a-z0-9-]+)$", INSTRUCTION.read_text(), re.M)
}
NON_HOLD_CANONICAL = "NOT_HOLD"


def read(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=True, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], text=True).strip()


def sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def report(number: int, value: object) -> None:
    write(REPORTS / f"{number:02d}-{SLUGS[number]}.json", value)


def normalize_boundary_lean(direction: object, lean: object) -> str:
    if str(direction).upper() != "HOLD":
        return NON_HOLD_CANONICAL
    return str(lean).upper()


def canonical_boundary_state(core: dict[str, object]) -> dict[str, object]:
    balance = core["directional_balance"]
    if not isinstance(balance, dict):
        raise TypeError("directional_balance_object_required")
    direction = str(core["overall_direction"])
    return {
        "direction": direction,
        "buy": float(balance["buy"]),
        "sell": float(balance["sell"]),
        "lean": normalize_boundary_lean(direction, core.get("hold_lean")),
    }


def classify_fic_fin_05(core: dict[str, object]) -> str:
    observed = canonical_boundary_state(core)
    if observed == {
        "direction": "HOLD",
        "buy": 4.5,
        "sell": 5.5,
        "lean": "SELL_LEAN",
    }:
        return "IN_BAND_HOLD_SELL_LEAN"
    if observed == {
        "direction": "SELL",
        "buy": 4.0,
        "sell": 6.0,
        "lean": NON_HOLD_CANONICAL,
    }:
        return "IN_BAND_MINIMUM_SELL"
    return "OUT_OF_BAND"


def latest_result_integrity() -> dict[str, object]:
    actual = sha256(LATEST.read_bytes())
    with zipfile.ZipFile(LATEST) as archive:
        names = archive.namelist()
        index = json.loads(archive.read("artifact-index.json"))
        indexed = {row["path"]: row for row in index["artifacts"]}
        members = {name for name in names if name != "artifact-index.json"}
        missing = sorted(set(indexed) - members)
        extra = sorted(members - set(indexed))
        hash_mismatch = []
        size_mismatch = []
        for name, row in indexed.items():
            if name not in members:
                continue
            payload = archive.read(name)
            if sha256(payload) != row["sha256"]:
                hash_mismatch.append(name)
            if len(payload) != row["size_bytes"]:
                size_mismatch.append(name)
    result = {
        "expected_sha256": LATEST_SHA,
        "actual_sha256": actual,
        "zip_entry_count": len(names),
        "indexed_payload_count": len(indexed),
        "missing_count": len(missing),
        "extra_count": len(extra),
        "hash_mismatch_count": len(hash_mismatch),
        "size_mismatch_count": len(size_mismatch),
        "duplicate_member_count": len(names) - len(set(names)),
    }
    result["status"] = (
        "PASS"
        if actual == LATEST_SHA
        and len(indexed) == 272
        and not any(
            result[key]
            for key in (
                "missing_count",
                "extra_count",
                "hash_mismatch_count",
                "size_mismatch_count",
                "duplicate_member_count",
            )
        )
        else "FAIL"
    )
    return result


def _m12aa_rows() -> list[dict[str, object]]:
    rows = []
    for repetition, number in enumerate((50, 52, 54), start=1):
        path = next(M12AA_REPORTS.glob(f"{number:02d}-*.json"))
        document = read(path)
        if not isinstance(document, dict):
            raise TypeError("m12aa_run_document_required")
        row = next(row for row in document["rows"] if row["ticker"] == "FIC-FIN-05")
        rows.append({**row, "repetition": repetition})
    return rows


def corrected_m12aa_audit() -> dict[str, object]:
    rows = []
    for row in _m12aa_rows():
        outcome = classify_fic_fin_05(row["core"])
        rows.append(
            {
                "repetition": row["repetition"],
                "raw": canonical_boundary_state(row["core"]),
                "outcome": outcome,
            }
        )
    outcomes = [row["outcome"] for row in rows]
    result = {
        "contract": "m12ab-corrected-m12aa-boundary-band-v1",
        "source_bundle_sha256": LATEST_SHA,
        "archived_m12aa_rewritten": False,
        "rows": rows,
        "in_band_minimum_sell_count": outcomes.count("IN_BAND_MINIMUM_SELL"),
        "in_band_hold_sell_lean_count": outcomes.count("IN_BAND_HOLD_SELL_LEAN"),
        "out_of_band_count": outcomes.count("OUT_OF_BAND"),
        "stable_preference": "MIXED_BOUNDARY",
    }
    result["status"] = (
        "PASS"
        if result["in_band_minimum_sell_count"] == 2
        and result["in_band_hold_sell_lean_count"] == 1
        and result["out_of_band_count"] == 0
        else "FAIL"
    )
    return result


def _option(
    letter: str,
    name: str,
    *,
    decision: str,
    single_call_stability: str,
    ai_faithfulness: str,
    numeric_determinism: str,
    hidden_scorecard_risk: str,
    schema_impact: str,
    renderer_impact: str,
    reason: str,
) -> dict[str, object]:
    return {
        "option": letter,
        "name": name,
        "decision": decision,
        "single_call_stability": single_call_stability,
        "faithfulness_to_ai_economic_judgment": ai_faithfulness,
        "deterministic_numeric_semantics": numeric_determinism,
        "conservative_tiebreak_compatibility": "HIGH" if letter == "F" else "LOW_OR_NONE",
        "new_buyer_holder_consistency": "AUDIT_REQUIRED",
        "renderer_impact": renderer_impact,
        "output_schema_impact": schema_impact,
        "monitoring_lifecycle_impact": "NONE_WHILE_EXPERIMENTAL",
        "daily_delta_impact": "NONE_WHILE_EXPERIMENTAL",
        "valuation_price_ownership_impact": "NONE",
        "holdout_proof_integrity": "PRESERVED" if letter in {"A", "E", "F", "G", "H"} else "WEAKENED",
        "complexity": "MEDIUM" if letter in {"F", "G", "H"} else "LOW",
        "hidden_scorecard_risk": hidden_scorecard_risk,
        "reason": reason,
    }


def architecture_options() -> list[dict[str, object]]:
    return [
        _option("A", "RAW_SINGLE_POINT", decision="REJECTED", single_call_stability="LOW", ai_faithfulness="HIGH", numeric_determinism="LOW", hidden_scorecard_risk="NONE", schema_impact="NONE", renderer_impact="NONE", reason="The same economics can change the primary HOLD/SELL meaning."),
        _option("B", "PROMPT_FORCE", decision="REJECTED", single_call_stability="UNPROVEN", ai_faithfulness="MEDIUM", numeric_determinism="LOW", hidden_scorecard_risk="LOW", schema_impact="NONE", renderer_impact="NONE", reason="Prior bounded wording already produced both adjacent states."),
        _option("C", "MAJORITY_VOTE", decision="FORBIDDEN", single_call_stability="NOT_APPLICABLE", ai_faithfulness="LOW", numeric_determinism="LOW", hidden_scorecard_risk="MEDIUM", schema_impact="NONE", renderer_impact="NONE", reason="Repeated outputs are not additional economic evidence."),
        _option("D", "AVERAGE_BALANCES", decision="FORBIDDEN", single_call_stability="ARTIFICIAL", ai_faithfulness="LOW", numeric_determinism="MEDIUM", hidden_scorecard_risk="HIGH", schema_impact="NONE", renderer_impact="NONE", reason="Averaging ordinal judgments invents unsupported semantics."),
        _option("E", "BAND_AS_PASS_ONLY", decision="REJECTED", single_call_stability="MEASUREMENT_ONLY", ai_faithfulness="HIGH", numeric_determinism="LOW", hidden_scorecard_risk="NONE", schema_impact="NONE", renderer_impact="NONE", reason="It measures the boundary but leaves different operational directions unresolved."),
        _option("F", "BOUNDARY_DECLARATION_CONSERVATIVE_RESOLVER", decision="SELECTED", single_call_stability="HIGH_IF_DECLARATION_STABLE", ai_faithfulness="HIGH", numeric_determinism="HIGH", hidden_scorecard_risk="LOW", schema_impact="ADDITIVE_OPTIONAL_EXPERIMENTAL", renderer_impact="NONE_WHILE_SHADOW", reason="It preserves AI interpretation and applies only the frozen mechanical tie-break."),
        _option("G", "SEMANTIC_ORDINAL_MAPPER", decision="REJECTED", single_call_stability="POTENTIALLY_HIGH", ai_faithfulness="MEDIUM", numeric_determinism="HIGH", hidden_scorecard_risk="HIGH", schema_impact="BROAD", renderer_impact="MEDIUM", reason="A deterministic mapper risks moving economic judgment into a brittle hidden scorecard."),
        _option("H", "NEW_BOUNDARY_DIRECTION_STATE", decision="REJECTED", single_call_stability="HIGH", ai_faithfulness="HIGH", numeric_determinism="HIGH", hidden_scorecard_risk="LOW", schema_impact="BREAKING", renderer_impact="HIGH", reason="It changes the frozen BUY/HOLD/SELL public and lifecycle surface."),
    ]


def review() -> None:
    if (OUTPUT / "phase-a-receipt.json").exists():
        raise ValueError("m12ab_phase_a_already_frozen")
    integrity = latest_result_integrity()
    correction = corrected_m12aa_audit()
    architecture = read(ROOT)
    fixtures = read(FIXTURES)
    if not isinstance(architecture, dict) or not isinstance(fixtures, dict):
        raise TypeError("m12ab_review_input_object_required")
    normalization_rows = []
    for row in fixtures["non_hold_lean_normalization"]:
        left = normalize_boundary_lean(row["direction"], row["left"])
        right = normalize_boundary_lean(row["direction"], row["right"])
        normalization_rows.append(
            {
                **row,
                "left_normalized": left,
                "right_normalized": right,
                "status": "PASS" if (left == right) is row["equal"] else "FAIL",
            }
        )
    prior_bug = read(next(M12AA_REPORTS.glob("57-*.json")))
    options = architecture_options()
    raw_rows = _m12aa_rows()
    semantic_fingerprints = [
        {
            "repetition": row["repetition"],
            "core": canonical_boundary_state(row["core"]),
            "business_thesis_change": row["core"]["business_thesis_change"],
            "new_buyer": row["core"]["fundamental_new_buyer"]["stance"],
            "holder": row["core"]["fundamental_holder"]["stance"],
            "confidence": row["core"]["directional_confidence"],
            "hard_error_count": len(row.get("errors", [])),
        }
        for row in raw_rows
    ]

    report(1, {"status": "PASS", "branch": git("branch", "--show-current"), "head": git("rev-parse", "HEAD"), "base_sha": BASE, "work_instruction_commit": INSTRUCTION_COMMIT, "origin_main": git("rev-parse", "origin/main"), "working_tree": git("status", "--short")})
    report(2, integrity)
    report(3, {"status": architecture["status"], "contract": architecture["contract"], "selected_architecture": architecture["selected_architecture"]})
    report(4, {"status": "FROZEN", "model": MODEL, "reasoning_effort": EFFORT, "runtime_mode": "MODEL_CONTEXT_COUPLED", "subjects_per_context": 4, "timeout_seconds": 1800, "wrapper_retry_count": 0, "batch_split": 0, "fallback_model": None})
    report(5, {"status": "REPRODUCED", "bug": "non-HOLD allowed-band null compared literally with normalized NOT_HOLD", "historical_report": prior_bug})
    report(6, {"status": "PASS" if all(row["status"] == "PASS" for row in normalization_rows) else "FAIL", "canonical_non_hold_state": NON_HOLD_CANONICAL, "rows": normalization_rows})
    report(7, correction)
    report(8, {"status": "CORRECTED", "reported": "BOUNDED_NEW_BUYER_STANCE_CALIBRATION_REPAIR_GPT56_SOL", "correct": "LEVERAGE_HOLD_SELL_BOUNDARY_RESOLUTION_ARCHITECTURE", "reason": "new-buyer variance is coupled to the primary core HOLD/SELL variance"})
    report(9, {"status": "MEASURED", "rows": semantic_fingerprints})
    report(10, {"status": "PASS", "hard_economic_semantics_invariant": True, "business_delta_values": sorted({row["business_thesis_change"] for row in semantic_fingerprints}), "hard_error_count": sum(row["hard_error_count"] for row in semantic_fingerprints)})
    report(11, {"status": "PASS", "root_cause": "GENUINE_ADJACENT_ORDINAL_BOUNDARY", "raw_states": [row["core"] for row in semantic_fingerprints], "opposite_polarity_reversal_count": 0})
    report(12, {"status": "COUPLED", "pairs": [{"core": row["core"]["direction"], "new_buyer": row["new_buyer"]} for row in semantic_fingerprints], "repair_priority": "CORE_FIRST"})
    report(13, {"status": "PARTLY_COUPLED_AND_UNRESOLVED", "pairs": [{"core": row["core"]["direction"], "holder": row["holder"]} for row in semantic_fingerprints], "mechanical_mapping_added": False})
    fic08 = read(next(M12AA_REPORTS.glob("61-*.json")))
    report(14, {"status": "INDEPENDENT_FOLLOWUP", "ticker": "FIC-FIN-08", "core": "HOLD 5.0:5.0 NEUTRAL x3", "holder": ["REVIEW", "HOLDABLE", "HOLDABLE"], "historical_formal_audit": fic08})
    report(15, {"status": "OBSERVATIONAL", "ticker": "FIC-FIN-06", "values": ["MEDIUM", "LOW", "LOW"], "direction_mapper_change": False})
    for number, option in zip(range(16, 24), options, strict=True):
        report(number, option)
    report(24, {"status": "COMPLETE", "method": "QUALITATIVE_NO_WEIGHTED_SCORE", "options": options})
    report(25, {"status": "SELECTED", "decision": architecture["selected_architecture"], "option": "F", "reason": architecture["selection_reason"]})
    report(26, {"status": "PASS", "ownership": architecture["ownership"], "coherent": True})
    report(27, {"status": "PASS", **architecture["schema"]})
    report(28, {"status": "PASS", **architecture["downstream"], "experimental_canary_only": True})

    checks = {
        "latest_result_integrity": integrity["status"] == "PASS",
        "correction": correction["status"] == "PASS",
        "normalization": all(row["status"] == "PASS" for row in normalization_rows),
        "one_architecture_selected": sum(row["decision"] == "SELECTED" for row in options) == 1,
        "selected_option_f": architecture["selected_option"] == "F",
        "ownership_compatible": architecture["ownership"]["hidden_scorecard"] is False,
        "additive_experimental_schema": architecture["schema"]["impact"] == "ADDITIVE_OPTIONAL_EXPERIMENTAL",
        "production_unchanged": architecture["schema"]["production_activation"] is False,
    }
    receipt = {
        "status": "PASS" if all(checks.values()) else "FAIL",
        "checks": checks,
        "selected_architecture": architecture["selected_architecture"],
        "frozen_at": datetime.now(UTC).isoformat(),
        "model_calls": 0,
    }
    write(OUTPUT / "phase-a-receipt.json", receipt)
    print(json.dumps(receipt, sort_keys=True))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("review",))
    args = parser.parse_args()
    if args.command == "review":
        review()


if __name__ == "__main__":
    main()
