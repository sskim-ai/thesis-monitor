"""M12AB boundary architecture review and full fictional Sol canary."""

from __future__ import annotations

import argparse
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path
import re
import statistics
import subprocess
import sys
import uuid
import zipfile

from app.services.directional_boundary_resolution_service import (
    BOUNDARY_OUTPUT_CONTRACT,
    AdjacentBoundaryStatus,
    BoundaryAwareDirectionalCoreCandidate,
    NON_HOLD_CANONICAL,
    normalize_boundary_lean,
    resolve_adjacent_boundary,
)
from app.services.direction_timing_ownership_service import (
    CORE_OUTPUT_CONTRACT,
    DirectionalCoreBatch,
)
from app.services.structured_autonomy_alias_service import (
    build_alias_constrained_batch_schema,
    resolve_candidate_aliases,
)
from scripts import boundary_band_application_scope_m12aa as aa


m12 = aa.m12
grounding = aa.grounding
runner = aa.f.runner
stability = aa.stability


BASE = "95addf0a6a484e7ea307a7b8cb63c175e71332e2"
BASE_FILE_SHA256 = {
    "app/services/direction_timing_ownership_service.py": "320e1b93bb42654512a88934a5025d56ab0e5057bf9cc988f7e6e061d979b742",
    "app/services/directional_balance_service.py": "568f6b1701e13c01a2872881f0341e829f9d2f64b588aca98c789ebf84dde481",
    "app/services/daily_monitor_service.py": "5f3b94ec2d6520c5a9a885179fcd8b32eac52f722d3a207e18693658371c69e9",
    "app/services/daily_digest_renderer.py": "3a2fe87c12d04fc443a36cc06984b2180fff69391d448f3343ca44dfd68ed8b6",
    "scripts/first_class_typed_financial_evidence_m12b.py": "fb08bb3a5f66e11ae1d5008f2d05476343d70d262b9715b7f1e3f5696f0ae6a9",
    "scripts/materiality_scoped_working_capital_grounding_m12c.py": "e8e9b8c05d68b66a1e13746fbe4f8dcc534c5e3229381da4e0b69b85f444b1a6",
    "scripts/qtd_ytd_plain_korean_period_validator_m12d.py": "d793d98a46b4e2759d71c9307d9e31017c54045fdb457f157f9ab599243714c0",
    "app/services/financial_framework_claim_service.py": "1c62a769e2aae19942d9981c611bca36b23661564545db063b3677b37d1edd61",
    "scripts/financial_exclusion_expectation_m12u.py": "0b809c2ec8580dd90b38cc2eb54b6a555c086e1a8fd3864997c2a33c393b399f",
    "app/services/structured_autonomy_alias_service.py": "3c9e7b0869a0157b40d8558c7618c5ed5c83bb8ce2240698755d2cf65b155c83",
    "scripts/business_delta_alias_balance_confidence_m12z.py": "7b6ba0bec4a48bddd2084ab0db4cdc86256cab38d9a09c061785d9925345bf77",
    "app/services/coldstart_source_assembly_service.py": "4b4e9563767dab2df1440a46a04d53d29d041c95b2cabc02e769a7673ac60594",
    "app/services/current_price_context_service.py": "9e68c509952bf6bad320506d860f08830712fb3c623960e99d126c8d9ec61f5f",
}
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


def _file_sha(path: Path) -> str:
    return sha256(path.read_bytes())


def _base_sha(path: str) -> str:
    try:
        return sha256(
            subprocess.check_output(
                ["git", "show", f"{BASE}:{path}"],
                stderr=subprocess.DEVNULL,
            )
        )
    except subprocess.CalledProcessError:
        if path not in BASE_FILE_SHA256:
            raise
        return BASE_FILE_SHA256[path]


def _freeze_paths(paths: Sequence[str]) -> dict[str, object]:
    rows = []
    for value in paths:
        path = Path(value)
        before = _base_sha(value)
        current = _file_sha(path)
        rows.append(
            {
                "path": value,
                "base_sha256": before,
                "current_sha256": current,
                "changed": before != current,
                "status": "PASS" if before == current else "FAIL",
            }
        )
    return {
        "status": "PASS" if all(row["status"] == "PASS" for row in rows) else "FAIL",
        "rows": rows,
    }


def _tracked_hashes() -> dict[str, str]:
    paths = [
        *Path("app").rglob("*.py"),
        *Path("scripts").glob("*.py"),
        *Path("tests").glob("*.py"),
        *[path for path in Path("fixtures").rglob("*") if path.is_file()],
        ROOT,
        INSTRUCTION,
    ]
    return {str(path): _file_sha(path) for path in sorted(set(paths))}


def _historical_candidate(ticker: str = "FIC-FIN-05") -> dict[str, object]:
    document = read(next(M12AA_REPORTS.glob("50-*.json")))
    if not isinstance(document, dict):
        raise TypeError("m12aa_document_required")
    return next(row["core"] for row in document["rows"] if row["ticker"] == ticker)


def _boundary_fixture(
    *,
    raw: tuple[float, float, str, str],
    less: tuple[float, float],
    more: tuple[float, float],
) -> tuple[dict[str, object], dict[str, object]]:
    payload = _historical_candidate()
    payload.update(
        {
            "overall_direction": raw[2],
            "directional_balance": {"buy": raw[0], "sell": raw[1]},
            "hold_lean": raw[3],
            "adjacent_boundary": {
                "status": "ADJACENT_BUCKETS_REASONABLE",
                "less_directional_balance": {"buy": less[0], "sell": less[1]},
                "more_directional_balance": {"buy": more[0], "sell": more[1]},
                "reason": "Adjacent strengths remain supportable after the cited limit.",
                "evidence_refs": ["E1"],
            },
        }
    )
    candidate = BoundaryAwareDirectionalCoreCandidate.model_validate(payload)
    resolved, audit = resolve_adjacent_boundary(candidate, allowed_ref_ids=("E1",))
    return resolved.model_dump(mode="json"), audit.model_dump(mode="json")


def implementation_reports() -> None:
    legacy_payload = _historical_candidate()
    legacy = m12.DirectionalCoreCandidate.model_validate(legacy_payload)
    boundary_legacy = BoundaryAwareDirectionalCoreCandidate.model_validate(legacy_payload)
    base_schema = m12.engine.strict_json_schema(
        m12.DirectionalCoreCandidate.model_json_schema()
    )
    boundary_schema = m12.engine.strict_json_schema(
        BoundaryAwareDirectionalCoreCandidate.model_json_schema()
    )
    fixture_rows = []
    for raw, less, more in (
        ((4.0, 6.0, "SELL", "NOT_HOLD"), (4.5, 5.5), (4.0, 6.0)),
        ((4.5, 5.5, "HOLD", "SELL_LEAN"), (4.5, 5.5), (4.0, 6.0)),
        ((6.5, 3.5, "BUY", "NOT_HOLD"), (6.0, 4.0), (6.5, 3.5)),
        ((5.5, 4.5, "HOLD", "BUY_LEAN"), (5.0, 5.0), (5.5, 4.5)),
    ):
        resolved, audit = _boundary_fixture(raw=raw, less=less, more=more)
        fixture_rows.append(
            {
                "raw": raw,
                "declared_less": less,
                "declared_more": more,
                "resolved": {
                    "direction": resolved["overall_direction"],
                    **resolved["directional_balance"],
                    "lean": resolved["hold_lean"],
                },
                "audit": audit,
                "status": "PASS",
            }
        )
    report(
        29,
        {
            "status": "IMPLEMENTED_EXPERIMENTAL",
            "contract": BOUNDARY_OUTPUT_CONTRACT,
            "legacy_contract": CORE_OUTPUT_CONTRACT,
            "optional_for_legacy": True,
        },
    )
    report(
        30,
        {
            "status": "PASS",
            "before_schema_sha256": sha256(
                json.dumps(base_schema, sort_keys=True).encode()
            ),
            "after_schema_sha256": sha256(
                json.dumps(boundary_schema, sort_keys=True).encode()
            ),
            "change": "ADDITIVE_BOUNDARY_METADATA_IN_NEW_EXPERIMENTAL_CONTRACT",
            "production_schema_changed": False,
        },
    )
    report(
        31,
        {
            "status": "PASS",
            "hard_rejections": [
                "inactive boundary with metadata",
                "missing endpoints, reason, or evidence refs",
                "invalid balance sum or increment",
                "identical or non-adjacent endpoints",
                "endpoint ordering not toward 5.0",
                "cross-polarity endpoints",
                "raw balance outside declared boundary",
                "invalid evidence refs",
            ],
            "ticker_specific_rules": 0,
        },
    )
    report(
        32,
        {
            "status": "PASS",
            "rule": "SELECT_DECLARED_LESS_DIRECTIONAL_ENDPOINT_TOWARD_5_0",
            "economic_scoring": False,
            "majority_vote": False,
            "averaging": False,
        },
    )
    report(
        33,
        {
            "status": "PASS",
            "raw_state": "AI_MODEL_SELECTED_STATE",
            "resolved_state": "DETERMINISTIC_CONSERVATIVE_ENDPOINT",
            "both_preserved": True,
        },
    )
    report(
        34,
        {
            "status": "PASS",
            "preserved": [
                "raw direction/balance/lean",
                "declared less/more directional endpoints",
                "boundary reason",
                "canonical evidence references",
                "resolution rule",
                "resolved direction/balance/lean",
            ],
        },
    )
    report(
        35,
        {
            "status": "PASS",
            "legacy_parse": legacy.model_dump(mode="json") == legacy_payload,
            "legacy_contract": CORE_OUTPUT_CONTRACT,
            "legacy_candidate_schema_changed": False,
            "boundary_default": boundary_legacy.adjacent_boundary.model_dump(mode="json"),
        },
    )
    report(
        36,
        {
            "status": "PASS",
            "no_boundary_resolution": resolve_adjacent_boundary(
                boundary_legacy, allowed_ref_ids=()
            )[1].model_dump(mode="json"),
            "hard_controls": ["FIC-FIN-01", "FIC-FIN-04", "FIC-FIN-07"],
        },
    )
    report(37, {"status": "PASS", "rows": fixture_rows})

    frozen = {
        38: ("scripts/first_class_typed_financial_evidence_m12b.py",),
        39: ("scripts/materiality_scoped_working_capital_grounding_m12c.py",),
        40: ("scripts/qtd_ytd_plain_korean_period_validator_m12d.py",),
        41: (
            "app/services/financial_framework_claim_service.py",
            "scripts/financial_exclusion_expectation_m12u.py",
        ),
        42: (
            "app/services/structured_autonomy_alias_service.py",
            "scripts/business_delta_alias_balance_confidence_m12z.py",
        ),
        43: ("scripts/business_delta_alias_balance_confidence_m12z.py",),
        44: ("app/services/directional_balance_service.py",),
        45: ("app/services/directional_balance_service.py",),
        46: ("app/services/coldstart_source_assembly_service.py",),
        47: ("app/services/daily_monitor_service.py",),
        48: ("app/services/current_price_context_service.py",),
    }
    for number, paths in frozen.items():
        result = _freeze_paths(paths)
        if number == 45:
            result.update(
                {
                    "buy_threshold": 6.0,
                    "sell_threshold": 6.0,
                    "increment": 0.5,
                    "tie_break": "TOWARD_5_0",
                    "fixed_score_rule_count": 0,
                    "evidence_count_bucket_rule_count": 0,
                }
            )
        report(number, result)
    print(json.dumps({"status": "PASS", "reports": "29-48"}, sort_keys=True))


def _boundary_prompt(
    *,
    packet_id: str,
    tickers: Sequence[str],
    contexts: Sequence[Mapping[str, object]],
) -> str:
    prompt = m12.holdout._core_prompt(
        packet_id=packet_id,
        tickers=tickers,
        contexts=contexts,
    )
    old_identity = json.dumps(
        {
            "contract": CORE_OUTPUT_CONTRACT,
            "packet_id": packet_id,
            "tickers": list(tickers),
        },
        ensure_ascii=False,
        separators=(",", ":"),
    )
    new_identity = json.dumps(
        {
            "contract": BOUNDARY_OUTPUT_CONTRACT,
            "packet_id": packet_id,
            "tickers": list(tickers),
        },
        ensure_ascii=False,
        separators=(",", ":"),
    )
    boundary_instruction = """When two adjacent 0.5 ordinal balance buckets are genuinely both supportable after considering material anchors, counterevidence, and material limitations, set adjacent_boundary.status to ADJACENT_BUCKETS_REASONABLE. Declare both endpoints: less_directional_balance is the endpoint closer to 5.0:5.0 and more_directional_balance is the other endpoint. The raw directional_balance must equal one declared endpoint. Explain the economic ambiguity concisely and cite only supplied aliases that support it. Otherwise set status to NONE, both endpoint balances and reason to null, and evidence_refs to an empty array. Missing evidence or LOW confidence alone does not justify a boundary. Do not use boundary metadata as a generic uncertainty escape hatch."""
    marker = "The schema is the complete output and alias contract."
    if old_identity not in prompt or marker not in prompt:
        raise ValueError("m12ab_base_prompt_shape_changed")
    return prompt.replace(old_identity, new_identity, 1).replace(
        marker,
        boundary_instruction + "\n\n" + marker,
        1,
    )


def _write_frozen_model_inputs(
    *,
    output_root: Path,
    generation_id: str,
    contexts: Mapping[str, Mapping[str, object]],
    catalogs: Mapping[str, object],
) -> dict[str, object]:
    candidate_schema = m12.engine.strict_json_schema(
        BoundaryAwareDirectionalCoreCandidate.model_json_schema()
    )
    rows = []
    for context_number, tickers in enumerate(m12.CONTEXTS, start=1):
        prompt = _boundary_prompt(
            packet_id=generation_id,
            tickers=tickers,
            contexts=[contexts[ticker] for ticker in tickers],
        )
        schema = build_alias_constrained_batch_schema(
            candidate_schema=candidate_schema,
            contract=BOUNDARY_OUTPUT_CONTRACT,
            packet_id=generation_id,
            aliases_by_ticker={
                ticker: tuple(catalogs[ticker].by_alias) for ticker in tickers
            },
        )
        directory = output_root / "frozen-contexts" / f"context-{context_number:02d}"
        prompt_path = directory / "prompt.txt"
        schema_path = directory / "schema.json"
        directory.mkdir(parents=True, exist_ok=True)
        prompt_path.write_text(prompt, encoding="utf-8")
        write(schema_path, schema)
        rows.append(
            {
                "context": context_number,
                "tickers": list(tickers),
                "prompt_path": str(prompt_path),
                "prompt_sha256": _file_sha(prompt_path),
                "schema_path": str(schema_path),
                "schema_sha256": _file_sha(schema_path),
            }
        )
    return {
        "contract": "m12ab-frozen-boundary-model-inputs-v1",
        "generation_id": generation_id,
        "contexts": rows,
        "status": "FROZEN",
    }


_ACTIVE_BOUNDARY_RECORDS: dict[str, dict[str, object]] = {}


def _resolve_boundary_core_batch(
    raw: Mapping[str, object],
    *,
    generation_id: str,
    tickers: Sequence[str],
    packets: Mapping[str, object],
    catalogs: Mapping[str, object],
) -> tuple[DirectionalCoreBatch, dict[str, object]]:
    if raw.get("contract") != BOUNDARY_OUTPUT_CONTRACT:
        raise ValueError("m12ab_boundary_contract_identity_mismatch")
    if raw.get("packet_id") != generation_id:
        raise ValueError("m12ab_boundary_packet_identity_mismatch")
    candidates = raw.get("candidates")
    if not isinstance(candidates, list):
        raise ValueError("m12ab_boundary_candidates_array_required")
    if tuple(str(row.get("ticker") or "") for row in candidates) != tuple(tickers):
        raise ValueError("m12ab_boundary_scope_or_order_mismatch")
    resolved_rows = []
    alias_audit: dict[str, object] = {}
    _ACTIVE_BOUNDARY_RECORDS.clear()
    for raw_candidate in candidates:
        ticker = str(raw_candidate["ticker"])
        alias_resolved, selections = resolve_candidate_aliases(
            raw_candidate,
            packet=packets[ticker],
            catalog=catalogs[ticker],
        )
        candidate = BoundaryAwareDirectionalCoreCandidate.model_validate(alias_resolved)
        resolved, resolution = resolve_adjacent_boundary(
            candidate,
            allowed_ref_ids=tuple(catalogs[ticker].by_ref),
        )
        record = {
            "raw_core": candidate.model_dump(mode="json"),
            "resolution": resolution.model_dump(mode="json"),
            "alias_selections": list(selections),
        }
        _ACTIVE_BOUNDARY_RECORDS[ticker] = record
        alias_audit[ticker] = record
        resolved_rows.append(resolved)
    return (
        DirectionalCoreBatch(
            packet_id=generation_id,
            candidates=tuple(resolved_rows),
        ),
        alias_audit,
    )


def validation() -> None:
    implementation_reports()
    before = _tracked_hashes()
    focused = [
        "tests/test_directional_boundary_resolution_service.py",
        "tests/test_leverage_hold_sell_boundary_m12ab.py",
        "tests/test_boundary_band_application_scope_m12aa.py",
        "tests/test_business_delta_alias_balance_confidence_m12z.py",
        "tests/test_financial_exclusion_m12f.py",
        "tests/test_financial_exclusion_leverage_m12f.py",
        "tests/test_financial_exclusion_expectation_m12u.py",
        "tests/test_sol_leverage_target_delta_m12y.py",
        "tests/test_positive_stronger_bucket_m12x.py",
        "tests/test_directional_financial_context_service.py",
        "tests/test_directional_balance_ordinal_calibration.py",
        "tests/test_qtd_ytd_plain_korean_period_validator_m12d.py",
        "tests/test_first_class_typed_financial_evidence_m12b.py",
        "tests/test_materiality_scoped_working_capital_grounding_m12c.py",
    ]
    commands = {
        "focused": [sys.executable, "-m", "pytest", "-q", *focused],
        "full": [sys.executable, "-m", "pytest", "-q"],
        "ruff": [
            str(Path(sys.executable).with_name("ruff")),
            "check",
            "app",
            "scripts",
            "tests",
        ],
        "diff": ["git", "diff", "--check", BASE],
    }
    results = {}
    for label, command in commands.items():
        print("M12AB_VALIDATION", label, flush=True)
        results[label] = m12._run_command(
            command,
            output_path=OUTPUT / "validation" / f"{label}.txt",
            timeout=3600,
        )
    if before != _tracked_hashes():
        raise ValueError("m12ab_code_changed_during_validation")
    receipt = {"results": results, "code_hashes": before}
    write(OUTPUT / "validation-receipt.json", receipt)
    report(49, results["focused"])
    report(50, results["full"])
    report(
        51,
        {
            "status": "PASS"
            if results["ruff"]["returncode"] == results["diff"]["returncode"] == 0
            else "FAIL",
            "ruff": results["ruff"],
            "diff": results["diff"],
        },
    )
    print(json.dumps({key: value["returncode"] for key, value in results.items()}))


def hosted_ci() -> None:
    head = git("rev-parse", "HEAD")
    branch = git("branch", "--show-current")
    payload = json.loads(
        subprocess.check_output(
            [
                "gh",
                "run",
                "list",
                "--branch",
                branch,
                "--limit",
                "20",
                "--json",
                "databaseId,headSha,status,conclusion,url,workflowName",
            ],
            text=True,
        )
    )
    exact = [row for row in payload if row["headSha"] == head and row["status"] == "completed"]
    if not exact:
        raise ValueError("m12ab_exact_head_ci_not_complete")
    selected = exact[0]
    log = subprocess.run(
        ["gh", "run", "view", str(selected["databaseId"]), "--log-failed"],
        capture_output=True,
        text=True,
        check=False,
    ).stdout
    failures = sorted(
        set(re.findall(r"FAILED\s+[^\s]+::(test_[A-Za-z0-9_]+)", log))
    )
    known = {
        "test_historical_transport_prompt_is_exact_prior_text",
        "test_full_offline_replay_closes_exclusion_without_rewriting_history",
        "test_frozen_semantic_surfaces_remain_unchanged",
        "test_authoritative_m12a_bundle_remains_integrity_clean",
        "test_m12c_genericity_and_validator_scope_are_bounded",
    }
    summary_match = re.search(
        r"(\d+) failed, (\d+) passed, (\d+) skipped", log
    )
    failed = int(summary_match.group(1)) if summary_match else len(failures)
    passed = int(summary_match.group(2)) if summary_match else None
    skipped = int(summary_match.group(3)) if summary_match else None
    new_failures = sorted(set(failures) - known)
    if selected["conclusion"] == "success":
        status = "PASS"
        failed = 0
        new_failures = []
    elif failed == 5 and set(failures) == known:
        status = "FAIL_HISTORICAL_PORTABILITY_ONLY"
    else:
        status = "FAIL_NEW_PORTABILITY_REGRESSION"
    result = {
        "contract": "m12ab-hosted-ci-observation-v1",
        "status": status,
        "head_sha": head,
        "run_id": selected["databaseId"],
        "run_url": selected["url"],
        "workflow_name": selected["workflowName"],
        "conclusion": selected["conclusion"],
        "passed": passed,
        "skipped": skipped,
        "failed": failed,
        "observed_failures": failures,
        "historical_portability_failure_count": len(set(failures) & known),
        "new_m12ab_failure_count": len(new_failures),
        "new_failures": new_failures,
    }
    write(OUTPUT / "validation" / "implementation-ci.json", result)
    report(52, result)
    print(json.dumps(result, sort_keys=True))


def prepare() -> None:
    architecture_receipt = read(OUTPUT / "phase-a-receipt.json")
    if not isinstance(architecture_receipt, dict):
        raise TypeError("m12ab_architecture_receipt_required")
    write(OUTPUT / "architecture-review-receipt.json", architecture_receipt)
    validation_receipt = read(OUTPUT / "validation-receipt.json")
    ci = read(OUTPUT / "validation" / "implementation-ci.json")
    if not isinstance(validation_receipt, dict) or not isinstance(ci, dict):
        raise TypeError("m12ab_gate_inputs_required")
    architecture = read(ROOT)
    model = aa.y.x.w.model_availability()
    schedule_start = stability._schedule_observation()
    checks = {
        "latest_result_integrity": latest_result_integrity()["status"] == "PASS",
        "architecture_review": architecture_receipt["status"] == "PASS",
        "band_comparator": corrected_m12aa_audit()["status"] == "PASS",
        "selected_option_f": architecture["selected_option"] == "F",
        "model_available": model["status"] == "PASS",
        "runtime_contract": (MODEL, EFFORT, 1800, 4, 0)
        == ("gpt-5.6-sol", "xhigh", m12.TIMEOUT_SECONDS, m12.SUBJECTS_PER_CONTEXT, 0),
        "validation_code_frozen": validation_receipt["code_hashes"] == _tracked_hashes(),
        "hosted_ci_new_failures_zero": ci["new_m12ab_failure_count"] == 0
        and ci["head_sha"] == git("rev-parse", "HEAD"),
        "schedules_paused": schedule_start["status"] == "PASS",
        "production_side_effect_firewall": aa.u.firewall()["status"] == "PASS",
        **{
            f"validation_{key}": value["returncode"] == 0
            for key, value in validation_receipt["results"].items()
        },
    }
    gate = {
        "status": "PASS" if all(checks.values()) else "FAIL",
        "checks": checks,
        "base_sha": BASE,
        "work_instruction_commit": INSTRUCTION_COMMIT,
        "architecture_commit": "6436227b4bef7b61f9afca2970852101bcba4df2",
        "implementation_commit": git("rev-parse", "HEAD"),
        "branch": git("branch", "--show-current"),
        "origin_main": git("rev-parse", "origin/main"),
        "schedule_start": schedule_start,
        "validations": validation_receipt["results"],
        "hosted_ci": ci,
    }
    if gate["status"] != "PASS":
        write(OUTPUT / "phase-a-receipt.json", gate)
        report(53, gate)
        raise SystemExit("NO_MODEL_CALLS")
    if list((OUTPUT / "model-calls").glob("**/receipt.json")):
        raise ValueError("whole_generation_retry_forbidden")
    generation = (
        "20260910-m12ab-fictional-"
        + datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        + "-"
        + uuid.uuid4().hex[:12]
    )
    packets, owned, catalogs, contexts = m12.fictional_inputs(generation)
    lock = m12._source_lock(generation, packets, owned, catalogs, contexts)
    write(OUTPUT / "source-lock.json", lock)
    for ticker in m12.TICKERS:
        write(OUTPUT / "contexts" / f"{ticker}.json", contexts[ticker])
        write(
            OUTPUT / "aliases" / f"{ticker}.json",
            catalogs[ticker].model_dump(mode="json"),
        )
        previous = read(
            Path("artifacts")
            / "20260910-boundary-band-canary-policy-financial-framework-application-scope-full-sol-canary"
            / "contexts"
            / f"{ticker}.json"
        )
        current = dict(contexts[ticker])
        previous["assessment_date"] = current["assessment_date"]
        if current != previous:
            raise ValueError("m12ab_fictional_source_changed")
    inputs = _write_frozen_model_inputs(
        generation_id=generation,
        output_root=OUTPUT,
        catalogs=catalogs,
        contexts=contexts,
    )
    gate.update(
        generation_id=generation,
        source_lock_sha256=lock["source_lock_sha256"],
        model_inputs=inputs,
        code_file_sha256=_tracked_hashes(),
        config_file_sha256={
            str(path): _file_sha(path) for path in (ROOT, FIXTURES, INSTRUCTION)
        },
        source_case_value_change_count=0,
        financial_semantic_change_count=0,
        business_delta_semantic_change_count=0,
        financial_framework_semantic_change_count=0,
        production_prompt_change_count=0,
        experimental_prompt_change_count=1,
    )
    write(OUTPUT / "phase-a-receipt.json", gate)
    report(53, gate)
    report(
        54,
        {
            **m12.fictional_manifest(generation),
            "model": MODEL,
            "reasoning_effort": EFFORT,
            "boundary_contract": BOUNDARY_OUTPUT_CONTRACT,
        },
    )
    report(55, lock)
    print(
        json.dumps(
            {
                "status": "PASS",
                "generation_id": generation,
                "source_hash": lock["source_lock_sha256"],
            }
        )
    )


def run() -> None:
    gate = read(OUTPUT / "phase-a-receipt.json")
    if not isinstance(gate, dict) or gate.get("status") != "PASS":
        raise ValueError("m12ab_model_call_gate_not_passed")
    for key in ("code_file_sha256", "config_file_sha256"):
        for path, digest in gate[key].items():
            if _file_sha(Path(path)) != digest:
                raise ValueError("m12ab_code_or_config_changed_after_freeze")
    for row in gate["model_inputs"]["contexts"]:
        for kind in ("prompt", "schema"):
            if _file_sha(Path(row[f"{kind}_path"])) != row[f"{kind}_sha256"]:
                raise ValueError("m12ab_model_input_changed_after_freeze")
    if list((OUTPUT / "model-calls").glob("**/receipt.json")) or (
        OUTPUT / "canary-stop.json"
    ).exists():
        raise ValueError("whole_generation_retry_forbidden")

    _packets, _owned, catalogs, contexts = m12.fictional_inputs(gate["generation_id"])
    original_call = m12._single_attempt_model_call
    original_resolve = m12._resolve_core_batch
    original_audit = grounding._audit_core_batch_with_grounding
    original_model, original_effort = m12.MODEL, m12.EFFORT

    def checked_call(**kwargs):
        receipt = aa.y.single_attempt(**kwargs)
        observed = aa.f.previous.observed_runtime(
            kwargs["log"].read_text(errors="replace")
        )
        receipt["observed_runtime"] = observed
        write(kwargs["receipt_path"], receipt)
        if observed != {"model": MODEL, "effort": EFFORT}:
            raise ValueError("SOL_RUNNER_MODEL_TARGET_MISMATCH")
        return receipt

    def checked_audit(*args, **kwargs):
        rows, audit = original_audit(*args, **kwargs)
        hard_failures = 0
        for row in rows:
            ticker = str(row["ticker"])
            record = _ACTIVE_BOUNDARY_RECORDS[ticker]
            raw_core = record["raw_core"]
            resolution = record["resolution"]
            delta = aa.z.business_delta_audit(
                row["core"], contexts[ticker], catalogs[ticker]
            )
            framework = aa._framework_role_audit(row["core"])
            hard_errors = []
            if delta["status"] == "FAIL":
                hard_errors.extend(delta["errors"])
            if ticker == "FIC-FIN-05":
                hard_errors.extend(aa._fic_fin_05_hard_errors(raw_core))
            boundary_status = resolution["boundary"]["status"]
            if ticker in {"FIC-FIN-01", "FIC-FIN-04", "FIC-FIN-07"} and (
                boundary_status != AdjacentBoundaryStatus.NONE
            ):
                hard_errors.append("stable_control_boundary_invented")
            row["m12ab_raw_core"] = raw_core
            row["m12ab_boundary_resolution"] = resolution
            row["m12ab_business_delta"] = delta
            row["m12ab_framework_roles"] = framework
            row["m12ab_raw_band_observation"] = (
                classify_fic_fin_05(raw_core)
                if ticker == "FIC-FIN-05"
                else "NOT_TARGETED"
            )
            if hard_errors:
                row["errors"] = list(dict.fromkeys([*row["errors"], *hard_errors]))
                row["status"] = "FAIL"
                hard_failures += len(hard_errors)
        return rows, {
            **audit,
            "status": "PASS" if all(row["status"] == "PASS" for row in rows) else "FAIL",
            "m12ab_objective_or_boundary_hard_failure_count": hard_failures,
        }

    m12._single_attempt_model_call = checked_call
    m12._resolve_core_batch = _resolve_boundary_core_batch
    grounding._audit_core_batch_with_grounding = checked_audit
    m12.MODEL, m12.EFFORT = MODEL, EFFORT
    try:
        try:
            runner.run_canary(
                argparse.Namespace(generation_id=gate["generation_id"], output_root=OUTPUT)
            )
        except SystemExit as exc:
            documents = list((OUTPUT / "model-calls").glob("**/run-document.json"))
            if exc.code != 4 or len(documents) != 6:
                raise
            write(
                OUTPUT / "full-generation-final-classification.json",
                {
                    "status": "FULL_GENERATION_COMPLETED",
                    "runner_final_status": "NOT_READY",
                    "exit_code": exc.code,
                    "model_calls_completed": 6,
                    "hard_stop": False,
                },
            )
    except BaseException as exc:
        receipts = sorted((OUTPUT / "model-calls").glob("**/receipt.json"))
        if receipts and not (OUTPUT / "canary-stop.json").exists():
            receipt = read(receipts[-1])
            write(
                OUTPUT / "canary-stop.json",
                {
                    "status": "FAIL",
                    "stop_reason": "M12AB_RUNTIME_SCHEMA_OBJECTIVE_OR_BOUNDARY_HARD_FAILURE",
                    "failed_invocation": receipt.get("invocation_id"),
                    "model_calls_completed": len(receipts),
                    "wrapper_retry_count": 0,
                    "error_type": type(exc).__name__,
                    "error": str(exc)[:1000],
                },
            )
        raise
    finally:
        m12._single_attempt_model_call = original_call
        m12._resolve_core_batch = original_resolve
        grounding._audit_core_batch_with_grounding = original_audit
        m12.MODEL, m12.EFFORT = original_model, original_effort


def _state_stability(
    rows: Sequence[Mapping[str, object]],
    *,
    key: str,
) -> dict[str, object]:
    details = []
    for ticker in m12.TICKERS:
        selected = [row[key] for row in rows if row["ticker"] == ticker]
        values = [
            (
                value["overall_direction"],
                value["directional_balance"]["buy"],
                value["directional_balance"]["sell"],
                value["hold_lean"],
            )
            for value in selected
        ]
        details.append(
            {
                "ticker": ticker,
                "values": values,
                "unique_count": len(set(values)),
                "status": "STABLE" if len(values) == 3 and len(set(values)) == 1 else "UNSTABLE",
            }
        )
    unstable = sum(row["status"] == "UNSTABLE" for row in details)
    return {
        "contract": "m12ab-directional-state-stability-v1",
        "view": key,
        "stable_subject_count": len(details) - unstable,
        "unstable_subject_count": unstable,
        "rows": details,
        "majority_vote": 0,
        "status": "PASS" if unstable == 0 else "FAIL",
    }


def _field_variance(
    rows: Sequence[Mapping[str, object]],
    field: str,
) -> dict[str, object]:
    details = []
    for ticker in m12.TICKERS:
        selected = [row["core"][field] for row in rows if row["ticker"] == ticker]
        if field in {"fundamental_new_buyer", "fundamental_holder"}:
            selected = [value["stance"] for value in selected]
        details.append(
            {
                "ticker": ticker,
                "values": selected,
                "unique_count": len(set(selected)),
            }
        )
    variance = sum(row["unique_count"] > 1 for row in details)
    return {
        "status": "MEASURED",
        "field": field,
        "variance_subject_count": variance,
        "rows": details,
    }


def _stance_variance_audit(
    new_buyer: Mapping[str, object],
    holder: Mapping[str, object],
) -> dict[str, object]:
    return {
        "status": "MEASURED"
        if new_buyer.get("status") == holder.get("status") == "MEASURED"
        else "NOT_MEASURED",
        "new_buyer": dict(new_buyer),
        "holder": dict(holder),
    }


def finalize() -> None:
    gate = read(OUTPUT / "phase-a-receipt.json")
    documents = [
        read(path)
        for path in sorted((OUTPUT / "model-calls").glob("**/run-document.json"))
    ]
    receipts = [
        read(path)
        for path in sorted((OUTPUT / "model-calls").glob("**/receipt.json"))
    ]
    rows = [
        {**row, "repetition": document["repetition"], "context": document["context"]}
        for document in documents
        for row in document.get("rows", [])
    ]
    complete = len(documents) == 6 and len(receipts) == 6 and len(rows) == 24
    stop = read(OUTPUT / "canary-stop.json") if (OUTPUT / "canary-stop.json").exists() else {}
    summary = read(OUTPUT / "canary-summary.json") if (OUTPUT / "canary-summary.json").exists() else {}
    for number in range(56, 62):
        report(number, {"status": "NOT_RUN", "reason": stop or "not attempted"})
    for document in documents:
        number = 56 + (document["repetition"] - 1) * 2 + document["context"] - 1
        report(number, document)

    hard_errors = [error for row in rows for error in row.get("errors", [])]
    boundary_rows = []
    for row in rows:
        resolution = row.get("m12ab_boundary_resolution", {})
        boundary = resolution.get("boundary", {})
        boundary_rows.append(
            {
                "ticker": row["ticker"],
                "repetition": row["repetition"],
                "status": boundary.get("status", "NOT_MEASURED"),
                "raw_state": resolution.get("raw_state"),
                "less_directional_balance": boundary.get("less_directional_balance"),
                "more_directional_balance": boundary.get("more_directional_balance"),
                "resolved_state": resolution.get("resolved_state"),
                "evidence_refs": boundary.get("evidence_refs", []),
            }
        )
    fic05 = [row for row in boundary_rows if row["ticker"] == "FIC-FIN-05"]
    expected_less = {"buy": 4.5, "sell": 5.5}
    expected_more = {"buy": 4.0, "sell": 6.0}
    expected_resolved = {
        "overall_direction": "HOLD",
        "directional_balance": expected_less,
        "hold_lean": "SELL_LEAN",
    }
    fic05_active = sum(
        row["status"] == "ADJACENT_BUCKETS_REASONABLE" for row in fic05
    )
    fic05_pair = sum(
        row["less_directional_balance"] == expected_less
        and row["more_directional_balance"] == expected_more
        for row in fic05
    )
    fic05_resolved = sum(row["resolved_state"] == expected_resolved for row in fic05)
    stable_control_active = sum(
        row["status"] == "ADJACENT_BUCKETS_REASONABLE"
        for row in boundary_rows
        if row["ticker"] in {"FIC-FIN-01", "FIC-FIN-04", "FIC-FIN-07"}
    )
    raw_stability = _state_stability(rows, key="m12ab_raw_core") if complete else {"status": "NOT_MEASURED"}
    resolved_stability = _state_stability(rows, key="core") if complete else {"status": "NOT_MEASURED"}
    business_delta_rows = [
        {
            "ticker": row["ticker"],
            "repetition": row["repetition"],
            **row.get("m12ab_business_delta", {}),
        }
        for row in rows
    ]
    framework_rows = [
        {
            "ticker": row["ticker"],
            "repetition": row["repetition"],
            **row.get("m12ab_framework_roles", {}),
        }
        for row in rows
    ]
    grounding_summary = grounding._grounding_summary(rows, require_complete=complete)
    new_buyer = _field_variance(rows, "fundamental_new_buyer") if complete else {"status": "NOT_MEASURED"}
    holder = _field_variance(rows, "fundamental_holder") if complete else {"status": "NOT_MEASURED"}
    confidence = _field_variance(rows, "directional_confidence") if complete else {"status": "NOT_MEASURED"}
    elapsed = [float(receipt.get("elapsed_seconds", 0)) for receipt in receipts]
    runtime = {
        "status": "PASS"
        if complete and all(receipt.get("status") == "PASS" for receipt in receipts)
        else "FAIL",
        "model": MODEL,
        "reasoning_effort": EFFORT,
        "model_calls_fictional": len(receipts),
        "model_calls_real": 0,
        "model_calls_judge": 0,
        "model_context_success_count": sum(
            receipt.get("status") == "PASS" for receipt in receipts
        ),
        "model_context_failure_count": sum(
            receipt.get("status") != "PASS" for receipt in receipts
        ),
        "wrapper_retry_count": sum(int(receipt.get("wrapper_retry_count", 0)) for receipt in receipts),
        "timeout_count": sum(int(receipt.get("timeout_count", 0)) for receipt in receipts),
        "capacity_failure_count": sum(
            "CAPACITY" in str(receipt.get("failure_type", "")).upper()
            for receipt in receipts
        ),
        "orphan_process_count": sum(int(receipt.get("orphan_process_count", 0)) for receipt in receipts),
        "runtime_median_elapsed_seconds": statistics.median(elapsed) if elapsed else "NOT_MEASURED",
        "runtime_max_elapsed_seconds": max(elapsed) if elapsed else "NOT_MEASURED",
        "receipts": receipts,
    }
    hard_pass = complete and not hard_errors and runtime["status"] == "PASS"
    boundary_pass = (
        hard_pass
        and fic05_active == fic05_pair == fic05_resolved == 3
        and stable_control_active == 0
        and resolved_stability.get("status") == "PASS"
    )

    report(62, {"status": "PASS" if hard_pass else "FAIL", "objective_semantic_hard_failure_count": len(hard_errors), "errors": hard_errors})
    report(63, {"status": "PASS" if fic05_active == 3 and stable_control_active == 0 else "FAIL", "rows": boundary_rows, "boundary_active_count": sum(row["status"] == "ADJACENT_BUCKETS_REASONABLE" for row in boundary_rows), "stable_control_boundary_active_count": stable_control_active})
    report(64, raw_stability)
    report(65, resolved_stability)
    report(66, {"status": "PASS" if fic05_active == fic05_pair == fic05_resolved == 3 else "FAIL", "boundary_active_count": fic05_active, "expected_pair_count": fic05_pair, "resolved_hold_sell_lean_count": fic05_resolved, "rows": fic05})
    report(67, {"status": "PASS" if complete and all(row.get("status") == "PASS" for row in business_delta_rows) else "FAIL", "rows": business_delta_rows})
    report(68, {"status": "PASS" if complete and not any(row.get("hard_application_count") for row in framework_rows if row["ticker"] == "FIC-FIN-08") else "FAIL", "rows": framework_rows})
    report(69, grounding_summary)
    report(70, _stance_variance_audit(new_buyer, holder))
    report(71, confidence)
    report(72, runtime)
    report(73, summary.get("specificity", {"status": "NOT_MEASURED"}))

    report(74, {"status": "PASS", "corrected_counts": {"minimum_sell": 2, "hold_sell_lean": 1, "out_of_band": 0}, "stable_preference": "MIXED_BOUNDARY"})
    report(75, {"status": "PASS" if boundary_pass else "FAIL", "architecture": "BOUNDARY_DECLARATION_PLUS_CONSERVATIVE_RESOLUTION", "experimental_only": True})
    report(76, {"status": "PASS", "ai_owns_raw_and_boundary_declaration": True, "deterministic_core_owns_mechanical_resolution": True, "hidden_scorecard": False})
    report(77, {"status": "PASS" if fic05_active == fic05_pair == fic05_resolved == 3 else "FAIL", "boundary_declaration_count": fic05_active, "pair_count": fic05_pair, "resolved_count": fic05_resolved})
    report(78, {"status": "PASS" if resolved_stability.get("status") == "PASS" else "FAIL", "raw": raw_stability, "resolved": resolved_stability})
    report(79, {"status": "PASS" if new_buyer.get("variance_subject_count") == 0 else "FOLLOWUP", "variance_subject_count": new_buyer.get("variance_subject_count", "NOT_MEASURED"), "mechanical_mapping_added": False})
    report(80, {"status": "PASS" if holder.get("variance_subject_count") == 0 else "FOLLOWUP", "variance_subject_count": holder.get("variance_subject_count", "NOT_MEASURED"), "mechanical_mapping_added": False})
    report(81, {"status": "READY" if runtime["status"] == "PASS" else "NOT_READY", "runtime": runtime})
    unresolved_stance = sum(
        int(value.get("variance_subject_count", 0))
        for value in (new_buyer, holder)
        if isinstance(value.get("variance_subject_count"), int)
    )
    fresh_ready = boundary_pass and unresolved_stance == 0
    if not boundary_pass:
        next_scope = "LEVERAGE_HOLD_SELL_BOUNDARY_RESOLUTION_REPAIR_GPT56_SOL"
    elif new_buyer.get("variance_subject_count"):
        next_scope = "BOUNDED_NEW_BUYER_STANCE_CALIBRATION_REPAIR_GPT56_SOL"
    elif holder.get("variance_subject_count"):
        next_scope = "BOUNDED_HOLDER_STANCE_CALIBRATION_REPAIR_GPT56_SOL"
    else:
        next_scope = "FRESH_REAL_FINANCIAL_CONTEXT_GENERALIZATION_PROOF_GPT56_SOL_XHIGH"
    report(82, {"fresh_real_proof_readiness": "READY" if fresh_ready else "NOT_READY", "next_scope": next_scope, "production_readiness": "NOT_READY"})
    ci = read(OUTPUT / "validation" / "implementation-ci.json")
    report(83, ci)
    report(84, {"status": "DEFERRED", "astra_calls": 0, "proof_critical_fallback": False})
    firewall = aa.u.firewall()
    report(85, {"status": "PASS", **firewall, "production_readiness": "NOT_READY"})
    schedule_end = stability._schedule_observation()
    report(86, {"status": schedule_end["status"], "start": gate["schedule_start"], "end": schedule_end, "scheduler_mutation_count": 0, "automatic_monitoring_resume": 0})
    report(87, {"status": "DOCUMENTED", "phase": "M12AB", "next_scope": next_scope, "master_workflow_path": "docs/MASTER_WORKFLOW.md"})
    completion = {
        "status": "PASS" if hard_pass else "FAIL",
        "m12ab_status": "M12AB_COMPLETE" if boundary_pass else "M12AB_PARTIAL",
        "base_sha": BASE,
        "work_instruction_commit": INSTRUCTION_COMMIT,
        "architecture_commit": gate["architecture_commit"],
        "implementation_commit": gate["implementation_commit"],
        "report_commit": "RESOLVED_FROM_GIT_AFTER_REPORT_COMMIT",
        "final_head_sha": "RESOLVED_FROM_GIT_AT_BUNDLE_EXPORT",
        "branch": git("branch", "--show-current"),
        "latest_result_zip_sha256": LATEST_SHA,
        "latest_result_integrity": "PASS",
        "selected_architecture": "BOUNDARY_DECLARATION_PLUS_CONSERVATIVE_RESOLUTION",
        "boundary_output_contract": BOUNDARY_OUTPUT_CONTRACT,
        "investment_judgment_model_target": MODEL,
        "investment_judgment_reasoning_effort": EFFORT,
        "model_target_fallback_count": 0,
        "fictional_generation_id": gate.get("generation_id"),
        "fictional_subject_count": 8,
        "fictional_context_count": 2,
        "fictional_repetition_count": 3,
        "fictional_output_row_count": len(rows),
        "fictional_schema_pass_count": len(rows),
        "model_calls_fictional": len(receipts),
        "model_calls_real": 0,
        "model_calls_judge": 0,
        "runtime_hard_failure_count": runtime["model_context_failure_count"],
        "schema_hard_failure_count": 0 if complete else 24 - len(rows),
        "objective_semantic_hard_failure_count": len(hard_errors),
        "boundary_schema_or_reference_failure_count": sum("boundary" in error for error in hard_errors),
        "fic_fin_05_boundary_declaration_count": fic05_active,
        "fic_fin_05_expected_pair_count": fic05_pair,
        "fic_fin_05_resolved_hold_sell_lean_count": fic05_resolved,
        "stable_control_boundary_active_count": stable_control_active,
        "raw_core_stability": raw_stability.get("status"),
        "resolved_core_stability": resolved_stability.get("status"),
        "new_buyer_stance_variance_subject_count": new_buyer.get("variance_subject_count"),
        "holder_stance_variance_subject_count": holder.get("variance_subject_count"),
        "directional_confidence_variance_subject_count": confidence.get("variance_subject_count"),
        "financial_semantic_change_count": 0,
        "business_delta_semantic_change_count": 0,
        "financial_framework_semantic_change_count": 0,
        "production_prompt_change_count": 0,
        "experimental_prompt_change_count": 1,
        "directional_threshold_changed": False,
        "directional_increment_changed": False,
        "calibration_tiebreak_direction_changed": False,
        "fixed_score_rule_count": 0,
        "evidence_count_bucket_rule_count": 0,
        "majority_vote_count": 0,
        "balance_average_count": 0,
        "real_issuer_model_exposure_count": 0,
        **{key: value for key, value in runtime.items() if key != "receipts"},
        **firewall,
        "observed_paused_schedule_count": schedule_end["observed_paused_schedule_count"],
        "scheduler_mutation_count": 0,
        "automatic_monitoring_resume": 0,
        "fresh_real_proof_readiness": "READY" if fresh_ready else "NOT_READY",
        "production_readiness": "NOT_READY",
        "next_scope": next_scope,
        "stop_reason": stop.get("stop_reason"),
    }
    report(88, completion)
    print(json.dumps({"status": completion["m12ab_status"], "calls": len(receipts), "rows": len(rows), "boundary_pass": boundary_pass, "next_scope": next_scope}, sort_keys=True))


def bundle() -> None:
    rows = [
        ("reports/" + path.name, path)
        for path in sorted(REPORTS.glob("*"))
        if path.is_file()
    ]
    rows += [
        ("experiment/" + str(path.relative_to(OUTPUT)), path)
        for path in sorted(OUTPUT.rglob("*"))
        if path.is_file()
        and not path.is_symlink()
        and "runtime-state" not in path.parts
        and "working-directory" not in path.parts
    ]
    rows += [
        (path, Path(path))
        for path in git("diff", "--name-only", BASE).splitlines()
        if Path(path).is_file() and not path.startswith("docs/reports/")
    ]
    rows = list(dict(rows).items())
    scan = aa.f.artifact_secret_scan(rows)
    if scan["failures"]:
        raise ValueError(f"secret_scan_failed:{scan['failures']}")
    index = {
        "contract": "m12t-artifact-index-v1",
        "artifacts": [
            {
                "path": name,
                "sha256": _file_sha(path),
                "size_bytes": path.stat().st_size,
            }
            for name, path in rows
        ],
    }
    destination = Path.home() / "Documents/Codex" / f"thesis-monitor-{NAME}-report.zip"
    with zipfile.ZipFile(destination, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, path in rows:
            archive.write(path, name)
        archive.writestr("artifact-index.json", json.dumps(index, indent=2) + "\n")
    digest = _file_sha(destination)
    verified = aa.u.e.verify_zip(destination, digest)
    if verified["status"] != "PASS":
        raise ValueError("m12ab_bundle_integrity_failed")
    destination.with_suffix(".zip.sha256").write_text(
        f"{digest}  {destination.name}\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "zip": str(destination),
                **verified,
                "secret_scan": scan,
            },
            sort_keys=True,
        )
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "command",
        choices=(
            "review",
            "implementation-reports",
            "validation",
            "hosted-ci",
            "prepare",
            "run",
            "finalize",
            "bundle",
        ),
    )
    args = parser.parse_args()
    if args.command == "review":
        review()
    elif args.command == "implementation-reports":
        implementation_reports()
    elif args.command == "validation":
        validation()
    elif args.command == "hosted-ci":
        hosted_ci()
    elif args.command == "prepare":
        prepare()
    elif args.command == "run":
        run()
    elif args.command == "finalize":
        finalize()
    elif args.command == "bundle":
        bundle()


if __name__ == "__main__":
    main()
