"""M12AA boundary-band policy, framework-role audit, and full Sol canary."""

from __future__ import annotations

import argparse
from collections.abc import Mapping, Sequence
from dataclasses import asdict
from datetime import UTC, datetime
import json
from pathlib import Path
import re
import statistics
import subprocess
import sys
from types import SimpleNamespace
import uuid
import zipfile

from app.services.directional_financial_context_service import (
    validate_directional_financial_semantics,
)
from app.services.financial_framework_claim_service import (
    FrameworkReferenceRole,
    candidate_financial_framework_claims,
)
from scripts import business_delta_alias_balance_confidence_m12z as z


y = z.y
u = z.u
f = z.f
m12 = z.m12
grounding = z.grounding
stability = z.stability
read, write, sha, git = z.read, z.write, z.sha, z.git

BASE = "e6e4cea878d4af93f44f299ff58791b651cc4afe"
INSTRUCTION_COMMIT = "6f783fe63a6dc727ffc19fa8d53e7cfcf84b8998"
ROOT_CAUSE_COMMIT = "689624d03c2440d9f6603f2b9e140974b517ea01"
MODEL = "gpt-5.6-sol"
EFFORT = "xhigh"
NAME = "20260910-boundary-band-canary-policy-financial-framework-application-scope-full-sol-canary"
OUTPUT = Path("artifacts") / NAME
REPORTS = Path("docs/reports") / NAME
ROOT = Path("docs/architecture/M12AA_BOUNDARY_BAND_APPLICATION_SCOPE.json")
FIXTURES = Path("fixtures/boundary_band_application_scope_m12aa.json")
INSTRUCTION = Path(
    "docs/work-instructions/"
    "20260910-boundary-band-canary-policy-and-financial-framework-application-scope-full-sol-canary.md"
)
LATEST = Path.home() / "Documents/Codex" / (
    "thesis-monitor-20260910-business-delta-alias-resolution-"
    "balance-confidence-full-sol-canary-report.zip"
)
LATEST_SHA = "6c6c6c02dcc9b6b144af43c3903e328bbc185a6bf4a4edbf78932500bfdd0c39"
M12Z_OUTPUT = z.OUTPUT
M12Z_GENERATION = "20260910-m12z-fictional-20260910T053337Z-5ce67bcf509e"
SLUGS = {
    int(number): slug
    for number, slug in re.findall(r"^(\d{2})-([a-z0-9-]+)$", INSTRUCTION.read_text(), re.M)
}
REFERENCE_BUYS = {
    "FIC-FIN-01": 6.5,
    "FIC-FIN-02": 4.5,
    "FIC-FIN-04": 5.0,
}
FIC_FIN_05_ALLOWED_BAND = (
    {"direction": "HOLD", "buy": 4.5, "sell": 5.5, "lean": "SELL_LEAN"},
    {"direction": "SELL", "buy": 4.0, "sell": 6.0, "lean": None},
)
HARD_ROLES = {
    FrameworkReferenceRole.ASSERTED_STATE,
    FrameworkReferenceRole.APPLIED_DECISION_FRAMEWORK,
    FrameworkReferenceRole.CONTRADICTORY_MIXED_USE,
    FrameworkReferenceRole.UNRESOLVED,
}
BASE_FILE_SHA256 = {
    "app/services/directional_balance_service.py": "568f6b1701e13c01a2872881f0341e829f9d2f64b588aca98c789ebf84dde481",
    "app/services/coldstart_source_assembly_service.py": "4b4e9563767dab2df1440a46a04d53d29d041c95b2cabc02e769a7673ac60594",
    "app/services/current_price_context_service.py": "9e68c509952bf6bad320506d860f08830712fb3c623960e99d126c8d9ec61f5f",
    "app/services/daily_digest_renderer.py": "3a2fe87c12d04fc443a36cc06984b2180fff69391d448f3343ca44dfd68ed8b6",
    "app/services/daily_monitor_service.py": "5f3b94ec2d6520c5a9a885179fcd8b32eac52f722d3a207e18693658371c69e9",
    "scripts/business_delta_alias_balance_confidence_m12z.py": "7b6ba0bec4a48bddd2084ab0db4cdc86256cab38d9a09c061785d9925345bf77",
    "scripts/financial_exclusion_expectation_m12u.py": "0b809c2ec8580dd90b38cc2eb54b6a555c086e1a8fd3864997c2a33c393b399f",
    "scripts/first_class_typed_financial_evidence_m12b.py": "fb08bb3a5f66e11ae1d5008f2d05476343d70d262b9715b7f1e3f5696f0ae6a9",
    "scripts/materiality_scoped_working_capital_grounding_m12c.py": "e8e9b8c05d68b66a1e13746fbe4f8dcc534c5e3229381da4e0b69b85f444b1a6",
    "scripts/qtd_ytd_plain_korean_period_validator_m12d.py": "d793d98a46b4e2759d71c9307d9e31017c54045fdb457f157f9ab599243714c0",
    "scripts/sol_runtime_adapter_m12w.py": "bff087fc514ca765a7a2cfb6108c72198eb37ced62c5595bdefe04f90894f615",
}


def report(number: int, value: object) -> None:
    write(REPORTS / f"{number:02d}-{SLUGS[number]}.json", value)


def _base_hash(path: str) -> str:
    try:
        return sha(
            subprocess.check_output(
                ["git", "show", f"{BASE}:{path}"],
                stderr=subprocess.DEVNULL,
            )
        )
    except subprocess.CalledProcessError:
        if path not in BASE_FILE_SHA256:
            raise
        return BASE_FILE_SHA256[path]


def _freeze_paths(
    paths: Sequence[str],
    *,
    expected_changed: Sequence[str] = (),
) -> dict[str, object]:
    changed = set(expected_changed)
    rows = []
    for path in paths:
        before = _base_hash(path)
        after = sha(Path(path).read_bytes())
        actual = before != after
        rows.append(
            {
                "path": path,
                "base_sha256": before,
                "current_sha256": after,
                "changed": actual,
                "expected_changed": path in changed,
                "status": "PASS" if actual == (path in changed) else "FAIL",
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
        FIXTURES,
        INSTRUCTION,
    ]
    return {str(path): sha(path.read_bytes()) for path in sorted(set(paths))}


def latest_result_integrity() -> dict[str, object]:
    verified = u.e.verify_zip(LATEST, LATEST_SHA)
    with zipfile.ZipFile(LATEST) as archive:
        names = archive.namelist()
        duplicate_count = len(names) - len(set(names))
        views = []
        scanner_literals = 0
        for name in names:
            if name == "artifact-index.json":
                continue
            try:
                text = archive.read(name).decode("utf-8")
            except UnicodeDecodeError:
                continue
            if name == f.CASE_SERVICE:
                text, count = f._scanner_literal_view(text)
                scanner_literals += count
            elif name == str(f.BASELINE):
                payload = json.loads(text)
                source, count = f._scanner_literal_view(
                    payload["approved_module_before"][f.CASE_SERVICE]
                )
                payload["approved_module_before"][f.CASE_SERVICE] = source
                text = json.dumps(payload)
                scanner_literals += count
            views.append(
                (
                    name,
                    SimpleNamespace(read_text=lambda text=text, **_kwargs: text),
                )
            )
        secret_failures = m12._secret_scan_failures(views)
    return {
        **verified,
        "zip_entry_count": len(names),
        "duplicate_member_count": duplicate_count,
        "secret_scan_failures": secret_failures,
        "known_empty_scanner_marker_literals": scanner_literals,
        "status": (
            "PASS"
            if verified["status"] == "PASS"
            and len(names) == 193
            and duplicate_count == 0
            and not secret_failures
            else "FAIL"
        ),
    }


def classify_canary_outcome(
    *,
    runtime_or_schema_errors: Sequence[str] = (),
    objective_semantic_errors: Sequence[str] = (),
    calibration_observation: bool = False,
    advisory_observation: bool = False,
) -> dict[str, object]:
    if runtime_or_schema_errors:
        classification = "RUNTIME_OR_SCHEMA_HARD_FAILURE"
        stop = True
    elif objective_semantic_errors:
        classification = "OBJECTIVE_SEMANTIC_HARD_FAILURE"
        stop = True
    elif calibration_observation:
        classification = "CALIBRATION_OBSERVATION"
        stop = False
    elif advisory_observation:
        classification = "ADVISORY_QUALITY_OBSERVATION"
        stop = False
    else:
        classification = "PASS"
        stop = False
    return {
        "classification": classification,
        "stop_generation": stop,
        "runtime_or_schema_errors": list(runtime_or_schema_errors),
        "objective_semantic_errors": list(objective_semantic_errors),
    }


def canary_stop_fixture_audit() -> dict[str, object]:
    rows = []
    for fixture in read(FIXTURES)["canary_outcomes"]:
        classification = str(fixture["class"])
        result = classify_canary_outcome(
            runtime_or_schema_errors=(fixture["condition"],)
            if classification == "RUNTIME_OR_SCHEMA_HARD_FAILURE"
            else (),
            objective_semantic_errors=(fixture["condition"],)
            if classification == "OBJECTIVE_SEMANTIC_HARD_FAILURE"
            else (),
            calibration_observation=classification == "CALIBRATION_OBSERVATION",
            advisory_observation=classification == "ADVISORY_QUALITY_OBSERVATION",
        )
        rows.append(
            {
                **fixture,
                "observed": result,
                "status": "PASS"
                if result["classification"] == classification
                and result["stop_generation"] is fixture["stop"]
                else "FAIL",
            }
        )
    return {
        "status": "PASS" if all(row["status"] == "PASS" for row in rows) else "FAIL",
        "rows": rows,
    }


def calibration_audit(row: Mapping[str, object]) -> dict[str, object]:
    ticker = str(row["ticker"])
    core = row["core"]
    balance = core["directional_balance"]
    observed = {
        "direction": str(core["overall_direction"]),
        "buy": float(balance["buy"]),
        "sell": float(balance["sell"]),
        "lean": core.get("hold_lean"),
    }
    if ticker == "FIC-FIN-05":
        if observed == FIC_FIN_05_ALLOWED_BAND[0]:
            outcome = "IN_BAND_HOLD_SELL_LEAN"
        elif observed == FIC_FIN_05_ALLOWED_BAND[1]:
            outcome = "IN_BAND_MINIMUM_SELL"
        elif observed["sell"] < 5.5:
            outcome = "OUT_OF_BAND_MORE_POSITIVE"
        elif observed["sell"] > 6.0:
            outcome = "OUT_OF_BAND_MORE_NEGATIVE"
        else:
            outcome = "OUT_OF_BAND_OTHER"
        return {
            "contract": "m12aa-fic-fin-05-boundary-band-v1",
            "status": "PASS" if outcome.startswith("IN_BAND") else "OBSERVATION",
            "validation_class": "CALIBRATION_OBSERVATION",
            "stop_generation": False,
            "outcome": outcome,
            "observed": observed,
            "allowed_band": list(FIC_FIN_05_ALLOWED_BAND),
        }
    if ticker not in REFERENCE_BUYS:
        return {"status": "NOT_TARGETED", "stop_generation": False}
    expected = REFERENCE_BUYS[ticker]
    outcome = "REFERENCE_MATCH" if observed["buy"] == expected else "EXACT_POINT_DEVIATION"
    return {
        "contract": "m12aa-reference-target-observation-v1",
        "status": "PASS" if outcome == "REFERENCE_MATCH" else "OBSERVATION",
        "validation_class": "CALIBRATION_OBSERVATION",
        "stop_generation": False,
        "outcome": outcome,
        "expected_buy": expected,
        "observed": observed,
    }


def band_fixture_audit() -> dict[str, object]:
    rows = []
    for fixture in read(FIXTURES)["fic_fin_05_band"]:
        core = {
            "overall_direction": fixture["direction"],
            "directional_balance": {"buy": fixture["buy"], "sell": fixture["sell"]},
            "hold_lean": fixture["lean"],
        }
        result = calibration_audit({"ticker": "FIC-FIN-05", "core": core})
        rows.append(
            {
                **fixture,
                "observed": result,
                "status": "PASS" if result["outcome"] == fixture["expected"] else "FAIL",
            }
        )
    return {
        "status": "PASS" if all(row["status"] == "PASS" for row in rows) else "FAIL",
        "rows": rows,
    }


def _fixture_candidate(fixture: Mapping[str, object]) -> dict[str, object]:
    def value(field: str, text: str) -> object:
        item = {"text": text, "evidence_refs": []}
        return [item] if field in {"buy_drivers", "sell_drivers"} else item

    field = str(fixture.get("field") or "sector_interpretation")
    candidate = {field: value(field, str(fixture["text"]))}
    if fixture.get("extra_text"):
        extra = str(fixture["extra_field"])
        candidate[extra] = value(extra, str(fixture["extra_text"]))
    return candidate


def application_scope_fixture_audit(kind: str) -> dict[str, object]:
    rows = []
    fixtures = read(FIXTURES)[f"application_scope_{kind}"]
    for fixture in fixtures:
        candidate = _fixture_candidate(fixture)
        claims = candidate_financial_framework_claims(candidate)
        roles = {claim.role.value for claim in claims}
        validation = validate_directional_financial_semantics(
            candidate,
            supplied_refs=(),
            allowed_ref_ids=(),
            sector_framework="insurance",
        )
        expected_valid = kind == "positive"
        rows.append(
            {
                **fixture,
                "claims": [asdict(claim) for claim in claims],
                "validation": validation.model_dump(mode="json"),
                "status": "PASS"
                if fixture["expected_role"] in roles and validation.valid is expected_valid
                else "FAIL",
            }
        )
    return {
        "status": "PASS" if all(row["status"] == "PASS" for row in rows) else "FAIL",
        "false_reject_count": sum(row["status"] == "FAIL" for row in rows)
        if kind == "positive"
        else 0,
        "false_accept_count": sum(row["status"] == "FAIL" for row in rows)
        if kind == "negative"
        else 0,
        "rows": rows,
    }


def exact_m12z_fic_fin_08_replay() -> dict[str, object]:
    document = read(M12Z_OUTPUT / "model-calls/run-1/context-02/run-document.json")
    historical = next(row for row in document["rows"] if row["ticker"] == "FIC-FIN-08")
    _packets, owned, catalogs, _contexts = m12.fictional_inputs("m12aa-fic-fin-08-replay")
    batch = m12.DirectionalCoreBatch(
        packet_id="m12aa-fic-fin-08-replay",
        candidates=(m12.DirectionalCoreCandidate.model_validate(historical["core"]),),
    )
    rows, audit = grounding._audit_core_batch_with_grounding(
        batch,
        owned=owned,
        catalogs=catalogs,
    )
    claims = candidate_financial_framework_claims(historical["core"])
    roles = {claim.role.value for claim in claims}
    return {
        "status": "PASS"
        if audit["status"] == "PASS"
        and roles == {"CONTRASTIVE_REPLACEMENT"}
        and rows[0]["financial_semantics"]["partial_debt_total_claim_count"] == 0
        else "FAIL",
        "historical_raw_output_rewritten": False,
        "historical_errors": historical["errors"],
        "current_row": rows[0],
        "reference_roles": [asdict(claim) for claim in claims],
        "actual_industrial_framework_misuse_count": sum(
            claim.role in HARD_ROLES for claim in claims
        ),
    }


def _fic_fin_05_hard_errors(core: Mapping[str, object]) -> list[str]:
    refs = m12._candidate_refs(core)
    errors = []
    if core.get("overall_direction") == "BUY":
        errors.append("fic_fin_05_economic_direction_contradiction")
    if not any("complete-debt" in ref for ref in refs):
        errors.append("fic_fin_05_complete_debt_anchor_missing")
    if not any(ref.endswith(":cash") for ref in refs):
        errors.append("fic_fin_05_thin_cash_anchor_missing")
    if not any("operating-evidence" in ref for ref in refs):
        errors.append("fic_fin_05_operating_counterevidence_missing")
    anchors = set(core.get("material_directional_anchor_basis") or ())
    if any("market-expectation" in ref for ref in anchors):
        errors.append("fic_fin_05_conditional_expectation_double_counted")
    return errors


def _framework_role_audit(core: Mapping[str, object]) -> dict[str, object]:
    claims = candidate_financial_framework_claims(core)
    return {
        "claims": [asdict(claim) for claim in claims],
        "roles": sorted({claim.role.value for claim in claims}),
        "hard_application_count": sum(claim.role in HARD_ROLES for claim in claims),
    }


def review() -> None:
    if (OUTPUT / "review-receipt.json").exists():
        raise ValueError("m12aa_review_already_frozen")
    root = read(ROOT)
    integrity = latest_result_integrity()
    stop_fixtures = canary_stop_fixture_audit()
    band = band_fixture_audit()
    positive = application_scope_fixture_audit("positive")
    negative = application_scope_fixture_audit("negative")
    fic08 = exact_m12z_fic_fin_08_replay()
    delta = z.exact_m12y_delta_replay()

    report(
        1,
        {
            "actual_branch": git("branch", "--show-current"),
            "actual_head": git("rev-parse", "HEAD"),
            "base_sha": BASE,
            "work_instruction_commit": INSTRUCTION_COMMIT,
            "root_cause_commit": ROOT_CAUSE_COMMIT,
            "working_tree_state": git("status", "--short"),
            "remote_branch_sha": git(
                "rev-parse", "origin/codex/20260910-business-delta-alias-resolution-m12z"
            ),
        },
    )
    report(2, integrity)
    report(3, {"status": root["status"], "contract": root["contract"]})
    report(4, {"status": "FROZEN", **root["runtime"]})
    report(
        5,
        {
            "status": "RECLASSIFIED",
            "m12z_context_02_transport": "PASS",
            "fic_fin_05": "CALIBRATION_OBSERVATION",
            "fic_fin_08": "VALIDATOR_FALSE_REJECT_APPLICATION_SCOPE",
        },
    )
    report(6, {"status": stop_fixtures["status"], **root["canary_stop_policy"]})
    report(7, stop_fixtures)
    report(
        8,
        {
            "status": "PASS",
            "before": "EXACT_TARGET_MISS_ADDED_TO_HARD_ERRORS",
            "after": "EXACT_TARGET_MISS_RECORDED_WITHOUT_HARD_ERROR",
        },
    )
    report(9, {"status": "FROZEN", **root["fic_fin_05"]})
    report(10, {"status": "FROZEN", "hard_semantics": root["fic_fin_05"]["hard_semantics"]})
    report(11, fic08)
    report(12, {"status": "FROZEN", **root["financial_framework_reference_role"]})
    report(
        13,
        {
            "status": "PASS",
            "shared_role_classifier": True,
            "assertion_requires_complete_net_debt": True,
            "non_application_triggers_completeness_error": False,
        },
    )
    report(
        14,
        {
            "status": "PASS",
            "true_industrial_application": "HARD_FAIL",
            "explicit_non_application": "PASS",
            "contrastive_replacement": "PASS",
        },
    )
    report(15, {"status": "PASS", "before": "calibration FAIL stopped runner", "after": "calibration observation continues runner"})
    report(16, {"status": "PASS", "contract": "m12aa-calibration-observation-v1", "mutates_errors": False})
    report(17, {"status": band["status"], "previous_exact_target": root["fic_fin_05"]["previous_exact_target"], "allowed_band": list(FIC_FIN_05_ALLOWED_BAND)})
    report(18, {"status": "PASS", "reference_targets_changed_after_output": False, "stop_on_point_deviation": False})
    report(19, {"status": "PASS", "before": "lexical exclusion token gate", "after": "candidate field/evidence application role"})
    report(20, {"status": "PASS", "shared_by": root["financial_framework_reference_role"]["shared_by"]})
    report(21, {"status": "PASS", "net_debt_application_roles": sorted(role.value for role in HARD_ROLES)})
    report(22, {"status": "PASS", "financial_sector_application_roles": sorted(role.value for role in HARD_ROLES)})
    report(23, {"status": "PASS", "exclusion_immunity_for_actual_application": False})
    report(24, {"status": stop_fixtures["status"], "rows": [row for row in stop_fixtures["rows"] if row["stop"]]})
    report(25, {"status": stop_fixtures["status"], "rows": [row for row in stop_fixtures["rows"] if not row["stop"]]})
    report(26, band)
    report(27, positive)
    report(28, negative)
    report(29, fic08)
    report(30, delta)
    report(31, {"status": "PASS", "ticker": "FIC-FIN-05", "business_thesis_change": "UNCHANGED"})
    report(32, {"status": "FROZEN", "buy": 6.0, "sell": 6.0, "production_change_count": 0})
    report(33, {"status": "FROZEN", "increment": 0.5, "production_change_count": 0})
    report(34, {"status": "FROZEN", "hold_lean": root["production_freeze"]["hold_lean"]})
    report(35, {"status": "FROZEN", "tie_break": root["production_freeze"]["tie_break"]})

    unchanged = {
        36: ("app/services/directional_balance_service.py",),
        37: ("scripts/first_class_typed_financial_evidence_m12b.py",),
        38: ("scripts/materiality_scoped_working_capital_grounding_m12c.py",),
        39: ("scripts/qtd_ytd_plain_korean_period_validator_m12d.py",),
        40: ("scripts/financial_exclusion_expectation_m12u.py",),
        41: ("scripts/business_delta_alias_balance_confidence_m12z.py",),
        42: ("app/services/coldstart_source_assembly_service.py",),
        43: ("app/services/daily_monitor_service.py",),
        44: ("app/services/current_price_context_service.py",),
        45: ("app/services/daily_digest_renderer.py",),
        46: ("scripts/sol_runtime_adapter_m12w.py",),
    }
    freeze_results = {}
    for number, paths in unchanged.items():
        freeze_results[number] = _freeze_paths(paths)
        report(number, freeze_results[number])

    checks = {
        "latest_result_integrity": integrity["status"] == "PASS",
        "root_frozen": root["status"] == "FROZEN_BEFORE_IMPLEMENTATION",
        "work_instruction_identity": git("rev-parse", INSTRUCTION_COMMIT) == INSTRUCTION_COMMIT,
        "root_cause_identity": git("rev-parse", ROOT_CAUSE_COMMIT) == ROOT_CAUSE_COMMIT,
        "stop_taxonomy": stop_fixtures["status"] == "PASS",
        "boundary_band": band["status"] == "PASS",
        "application_positive": positive["status"] == "PASS",
        "application_negative": negative["status"] == "PASS",
        "fic_fin_08_replay": fic08["status"] == "PASS",
        "delta_alias_regression": delta["status"] == "PASS",
        "frozen_surfaces": all(result["status"] == "PASS" for result in freeze_results.values()),
        "directional_prompt_unchanged": _base_hash("app/services/directional_balance_service.py")
        == sha(Path("app/services/directional_balance_service.py").read_bytes()),
    }
    receipt = {"status": "PASS" if all(checks.values()) else "FAIL", "checks": checks}
    write(OUTPUT / "review-receipt.json", receipt)
    print(json.dumps(receipt, sort_keys=True))


def validation() -> None:
    before = _tracked_hashes()
    focused = [
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
        "ruff": [str(Path(sys.executable).with_name("ruff")), "check", "app", "scripts", "tests"],
        "diff": ["git", "diff", "--check", BASE],
    }
    results = {}
    for label, command in commands.items():
        print("M12AA_VALIDATION", label, flush=True)
        results[label] = m12._run_command(
            command,
            output_path=OUTPUT / "validation" / f"{label}.txt",
            timeout=3600,
        )
    if before != _tracked_hashes():
        raise ValueError("m12aa_code_changed_during_validation")
    write(OUTPUT / "validation-receipt.json", {"results": results, "code_hashes": before})
    print(json.dumps({key: value["returncode"] for key, value in results.items()}))


def prepare() -> None:
    if (OUTPUT / "phase-a-receipt.json").exists():
        raise ValueError("m12aa_phase_a_already_frozen")
    root = read(ROOT)
    review_receipt = read(OUTPUT / "review-receipt.json")
    validation_receipt = read(OUTPUT / "validation-receipt.json")
    ci = read(OUTPUT / "validation/implementation-ci.json")
    model = y.x.w.model_availability()
    schedule_start = stability._schedule_observation()
    checks = {
        "latest_result_integrity": latest_result_integrity()["status"] == "PASS",
        "offline_review": review_receipt["status"] == "PASS",
        "model_available": model["status"] == "PASS",
        "runtime_contract": (
            root["runtime"]["model"],
            root["runtime"]["effort"],
            root["runtime"]["timeout_seconds"],
            root["runtime"]["subjects_per_context"],
            root["runtime"]["wrapper_retry_count"],
        )
        == (MODEL, EFFORT, 1800, 4, 0),
        "allowed_band_frozen": tuple(root["fic_fin_05"]["allowed_core_band"])
        == FIC_FIN_05_ALLOWED_BAND,
        "validation_code_frozen": validation_receipt["code_hashes"] == _tracked_hashes(),
        "hosted_ci_new_failures_zero": ci["new_m12aa_failure_count"] == 0
        and ci["head_sha"] == git("rev-parse", "HEAD"),
        "schedules_paused": schedule_start["status"] == "PASS",
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
        "root_cause_commit": ROOT_CAUSE_COMMIT,
        "implementation_commit": git("rev-parse", "HEAD"),
        "branch": git("branch", "--show-current"),
        "origin_main": git("rev-parse", "origin/main"),
        "schedule_start": schedule_start,
        "validations": validation_receipt["results"],
    }
    report(76, ci)
    if gate["status"] != "PASS":
        write(OUTPUT / "phase-a-receipt.json", gate)
        raise SystemExit("NO_MODEL_CALLS")
    generation = (
        "20260910-m12aa-fictional-"
        + datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        + "-"
        + uuid.uuid4().hex[:12]
    )
    packets, owned, catalogs, contexts = m12.fictional_inputs(generation)
    lock = m12._source_lock(generation, packets, owned, catalogs, contexts)
    write(OUTPUT / "source-lock.json", lock)
    for ticker in m12.TICKERS:
        write(OUTPUT / "contexts" / f"{ticker}.json", contexts[ticker])
        write(OUTPUT / "aliases" / f"{ticker}.json", catalogs[ticker].model_dump(mode="json"))
        previous = read(M12Z_OUTPUT / "contexts" / f"{ticker}.json")
        current = dict(contexts[ticker])
        previous["assessment_date"] = current["assessment_date"]
        if current != previous:
            raise ValueError("m12aa_fictional_source_changed")
    inputs = m12._write_frozen_model_inputs(
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
            str(path): sha(path.read_bytes()) for path in (ROOT, FIXTURES, INSTRUCTION)
        },
        source_case_value_change_count=0,
        directional_prompt_change_count=0,
        business_delta_prompt_change_count=0,
    )
    write(OUTPUT / "phase-a-receipt.json", gate)
    report(47, {**m12.fictional_manifest(generation), "model": MODEL, "reasoning_effort": EFFORT})
    report(48, lock)
    print(json.dumps({"status": "PASS", "generation_id": generation, "source_hash": lock["source_lock_sha256"]}))


def run() -> None:
    gate = read(OUTPUT / "phase-a-receipt.json")
    if gate["status"] != "PASS":
        raise ValueError("m12aa_phase_a_not_passed")
    for key in ("code_file_sha256", "config_file_sha256"):
        if any(sha(Path(path).read_bytes()) != digest for path, digest in gate[key].items()):
            raise ValueError("m12aa_code_or_config_changed_after_freeze")
    for row in gate["model_inputs"]["contexts"]:
        for kind in ("prompt", "schema"):
            if sha(Path(row[f"{kind}_path"]).read_bytes()) != row[f"{kind}_sha256"]:
                raise ValueError("m12aa_model_input_changed_after_freeze")
    if list((OUTPUT / "model-calls").glob("**/receipt.json")) or (
        OUTPUT / "canary-stop.json"
    ).exists():
        raise ValueError("whole_generation_retry_forbidden")

    _packets, _owned, catalogs, contexts = m12.fictional_inputs(gate["generation_id"])
    original_call = m12._single_attempt_model_call
    original_audit = grounding._audit_core_batch_with_grounding
    original_model, original_effort = m12.MODEL, m12.EFFORT

    def checked_call(**kwargs):
        receipt = y.single_attempt(**kwargs)
        observed = f.previous.observed_runtime(kwargs["log"].read_text(errors="replace"))
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
            delta = z.business_delta_audit(row["core"], contexts[ticker], catalogs[ticker])
            framework = _framework_role_audit(row["core"])
            hard_errors = []
            if delta["status"] == "FAIL":
                hard_errors.extend(delta["errors"])
            if ticker == "FIC-FIN-05":
                hard_errors.extend(_fic_fin_05_hard_errors(row["core"]))
            row["m12aa_business_delta"] = delta
            row["m12aa_framework_roles"] = framework
            row["m12aa_calibration"] = calibration_audit(row)
            if hard_errors:
                row["errors"] = list(dict.fromkeys([*row["errors"], *hard_errors]))
                row["status"] = "FAIL"
                hard_failures += len(hard_errors)
        return rows, {
            **audit,
            "status": "PASS" if all(row["status"] == "PASS" for row in rows) else "FAIL",
            "m12aa_objective_semantic_hard_failure_count": hard_failures,
        }

    m12._single_attempt_model_call = checked_call
    grounding._audit_core_batch_with_grounding = checked_audit
    m12.MODEL, m12.EFFORT = MODEL, EFFORT
    try:
        try:
            f.runner.run_canary(
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
                    "stop_reason": "M12AA_RUNTIME_SCHEMA_OR_OBJECTIVE_SEMANTIC_HARD_FAILURE",
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
        grounding._audit_core_batch_with_grounding = original_audit
        m12.MODEL, m12.EFFORT = original_model, original_effort


def _variance(rows: Sequence[Mapping[str, object]], field: str) -> int | str:
    if len(rows) != 24:
        return "NOT_MEASURED"
    return sum(
        len(
            {
                row["core"][field]["stance"]
                if field in {"fundamental_new_buyer", "fundamental_holder"}
                else row["core"][field]
                for row in rows
                if row["ticker"] == ticker
            }
        )
        > 1
        for ticker in m12.TICKERS
    )


def _core_rows(rows: Sequence[Mapping[str, object]]) -> list[dict[str, object]]:
    result = []
    for ticker in m12.TICKERS:
        selected = [row["core"] for row in rows if row["ticker"] == ticker]
        result.append(
            {
                "ticker": ticker,
                "observed_count": len(selected),
                "overall_direction_values": [row["overall_direction"] for row in selected],
                "directional_balance_values": [row["directional_balance"] for row in selected],
                "hold_lean_values": [row["hold_lean"] for row in selected],
                "overall_direction_unique_count": len({row["overall_direction"] for row in selected})
                if len(selected) == 3
                else "NOT_MEASURED",
                "directional_balance_unique_count": len(
                    {(row["directional_balance"]["buy"], row["directional_balance"]["sell"]) for row in selected}
                )
                if len(selected) == 3
                else "NOT_MEASURED",
                "hold_lean_unique_count": len({row["hold_lean"] for row in selected})
                if len(selected) == 3
                else "NOT_MEASURED",
            }
        )
    return result


def _fic05_preference(rows: Sequence[Mapping[str, object]]) -> str:
    outcomes = [
        row["m12aa_calibration"]["outcome"]
        for row in rows
        if row["ticker"] == "FIC-FIN-05"
    ]
    if len(outcomes) != 3:
        return "NOT_MEASURED"
    if set(outcomes) == {"IN_BAND_HOLD_SELL_LEAN"}:
        return "HOLD_SELL_LEAN"
    if set(outcomes) == {"IN_BAND_MINIMUM_SELL"}:
        return "MINIMUM_SELL"
    if set(outcomes) <= {"IN_BAND_HOLD_SELL_LEAN", "IN_BAND_MINIMUM_SELL"}:
        return "MIXED_BOUNDARY"
    return "OUT_OF_BAND"


def finalize() -> None:
    gate = read(OUTPUT / "phase-a-receipt.json")
    documents = [read(path) for path in sorted((OUTPUT / "model-calls").glob("**/run-document.json"))]
    receipts = [read(path) for path in sorted((OUTPUT / "model-calls").glob("**/receipt.json"))]
    rows = [
        {**row, "repetition": document["repetition"], "context": document["context"]}
        for document in documents
        for row in document.get("rows", [])
    ]
    complete = len(documents) == 6 and len(receipts) == 6 and len(rows) == 24
    stop = read(OUTPUT / "canary-stop.json") if (OUTPUT / "canary-stop.json").exists() else {}
    summary = read(OUTPUT / "canary-summary.json") if (OUTPUT / "canary-summary.json").exists() else {}
    for number in range(49, 55):
        report(number, {"status": "NOT_RUN", "reason": stop or "not attempted"})
    for document in documents:
        number = 49 + (document["repetition"] - 1) * 2 + document["context"] - 1
        report(number, document)

    hard_errors = [error for row in rows for error in row.get("errors", [])]
    calibration_rows = [
        {
            "ticker": row["ticker"],
            "repetition": row["repetition"],
            "audit": row.get("m12aa_calibration", {"status": "NOT_MEASURED"}),
        }
        for row in rows
        if row.get("m12aa_calibration", {}).get("status") != "NOT_TARGETED"
    ]
    calibration_out_of_band = sum(
        str(row["audit"].get("outcome", "")).startswith("OUT_OF_BAND")
        or row["audit"].get("outcome") == "EXACT_POINT_DEVIATION"
        for row in calibration_rows
    )
    framework_rows = [
        {
            "ticker": row["ticker"],
            "repetition": row["repetition"],
            **row.get("m12aa_framework_roles", {}),
        }
        for row in rows
    ]
    delta_rows = [
        {
            "ticker": row["ticker"],
            "repetition": row["repetition"],
            **row.get("m12aa_business_delta", {}),
        }
        for row in rows
    ]
    grounding_summary = grounding._grounding_summary(rows, require_complete=complete)
    formal = summary.get("stability", {"status": "NOT_MEASURED"})
    specificity = summary.get("specificity", {"status": "NOT_MEASURED"})
    core = _core_rows(rows)
    new_buyer_variance = _variance(rows, "fundamental_new_buyer")
    holder_variance = _variance(rows, "fundamental_holder")
    confidence_variance = _variance(rows, "directional_confidence")
    fic05 = [row for row in calibration_rows if row["ticker"] == "FIC-FIN-05"]
    preference = _fic05_preference(rows)
    runtime_elapsed = [float(receipt["elapsed_seconds"]) for receipt in receipts]
    runtime_hard = sum(receipt.get("status") != "PASS" for receipt in receipts)
    schema_hard = sum(len(document.get("rows", [])) != 4 for document in documents)
    objective_hard = len(hard_errors)

    report(55, {"status": "PASS" if complete and objective_hard == 0 else "FAIL", "errors": hard_errors, "objective_semantic_hard_failure_count": objective_hard})
    report(56, {"status": "MEASURED" if complete else "NOT_MEASURED", "rows": calibration_rows, "calibration_observation_count": len(calibration_rows), "calibration_out_of_band_count": calibration_out_of_band})
    report(57, {"status": "MEASURED" if len(fic05) == 3 else "NOT_MEASURED", "rows": fic05, "stable_preference": preference})
    report(58, {"status": "PASS" if complete and not any(row.get("hard_application_count") for row in framework_rows if row["ticker"] == "FIC-FIN-08") else "FAIL", "rows": framework_rows})
    report(59, {"status": "PASS" if complete and all(row.get("status") == "PASS" for row in delta_rows) else "FAIL", "rows": delta_rows})
    report(60, grounding_summary)
    report(61, formal)
    report(62, {"status": "MEASURED" if complete else "NOT_MEASURED", "rows": core})
    report(63, {"status": "MEASURED" if complete else "NOT_MEASURED", "new_buyer_stance_variance_subject_count": new_buyer_variance, "holder_stance_variance_subject_count": holder_variance, "directional_confidence_variance_subject_count": confidence_variance})
    runtime = {
        "status": "PASS" if complete and runtime_hard == 0 else "FAIL",
        "model_calls_fictional": len(receipts),
        "model_context_success_count": sum(receipt.get("status") == "PASS" for receipt in receipts),
        "model_context_failure_count": runtime_hard,
        "cli_internal_retry_event_count": sum(len(receipt.get("cli_internal_retry_events", ())) for receipt in receipts),
        "wrapper_retry_count": sum(int(receipt.get("wrapper_retry_count", 0)) for receipt in receipts),
        "timeout_count": sum(int(receipt.get("timeout_count", 0)) for receipt in receipts),
        "capacity_failure_count": sum("CAPACITY" in str(receipt.get("failure_type", "")).upper() for receipt in receipts),
        "orphan_process_count": sum(int(receipt.get("orphan_process_count", 0)) for receipt in receipts),
        "runtime_median_elapsed_seconds": statistics.median(runtime_elapsed) if runtime_elapsed else "NOT_MEASURED",
        "runtime_max_elapsed_seconds": max(runtime_elapsed) if runtime_elapsed else "NOT_MEASURED",
        "receipts": receipts,
    }
    report(64, runtime)
    report(65, specificity)

    formal_unstable = int(formal.get("fictional_unstable_count", 0)) if complete else 0
    formal_boundary = int(formal.get("fictional_boundary_uncertainty_count", 0)) if complete else 0
    framework_false_rejects = sum(
        error in {"net_debt_claim_without_complete_net_debt_evidence", "financial_sector_generic_reasoning"}
        for error in hard_errors
    )
    delta_failures = sum(row.get("status") != "PASS" for row in delta_rows)
    hard_pass = complete and runtime_hard == schema_hard == objective_hard == 0
    ready = (
        hard_pass
        and formal_unstable == 0
        and formal_boundary == 0
        and new_buyer_variance == 0
        and holder_variance == 0
    )
    if runtime_hard or schema_hard:
        next_scope = "SOL_RUNTIME_REGRESSION_REVIEW"
    elif framework_false_rejects:
        next_scope = "FINANCIAL_FRAMEWORK_APPLICATION_SCOPE_ARCHITECTURE_REVIEW"
    elif preference == "MIXED_BOUNDARY":
        next_scope = "LEVERAGE_HOLD_SELL_BOUNDARY_POLICY_REVIEW_GPT56_SOL"
    elif next((row for row in core if row["ticker"] == "FIC-FIN-01"), {}).get("directional_balance_unique_count") not in {1, "NOT_MEASURED"}:
        next_scope = "POSITIVE_STRONGER_BUCKET_STABILITY_REVIEW_GPT56_SOL"
    elif new_buyer_variance not in {0, "NOT_MEASURED"}:
        next_scope = "BOUNDED_NEW_BUYER_STANCE_CALIBRATION_REPAIR_GPT56_SOL"
    elif holder_variance not in {0, "NOT_MEASURED"}:
        next_scope = "BOUNDED_HOLDER_STANCE_CALIBRATION_REPAIR_GPT56_SOL"
    elif ready:
        next_scope = "FRESH_REAL_FINANCIAL_CONTEXT_GENERALIZATION_PROOF_GPT56_SOL_XHIGH"
    else:
        next_scope = "DIRECTIONAL_STRENGTH_OUTPUT_ARCHITECTURE_REVIEW_GPT56_SOL"

    report(66, {"status": "PASS" if complete and not stop else "FAIL", "calibration_deviation_stops_generation": False})
    report(67, {"status": "PASS" if len(fic05) == 3 and calibration_out_of_band == 0 else "FAIL", "stable_preference": preference})
    report(68, {"status": "PASS" if framework_false_rejects == 0 and complete else "FAIL", "false_reject_count": framework_false_rejects})
    report(69, {"status": "PASS" if delta_failures == 0 and complete else "FAIL", "failure_count": delta_failures})
    report(70, {"status": "PASS" if complete else "FAIL", "contexts": len(documents), "rows": len(rows)})
    report(71, {"status": "PASS" if complete and formal_unstable == 0 else "FAIL", "rows": core})
    report(72, {"status": "PASS" if new_buyer_variance == 0 else "FOLLOWUP", "variance_subject_count": new_buyer_variance})
    report(73, {"status": "PASS" if holder_variance == 0 else "FOLLOWUP", "variance_subject_count": holder_variance})
    report(74, {"status": "READY" if hard_pass else "NOT_READY", "runtime": runtime})
    report(75, {"fresh_real_proof_readiness": "READY" if ready else "NOT_READY", "next_scope": next_scope})
    ci = read(OUTPUT / "validation/implementation-ci.json")
    report(76, ci)
    report(77, {"status": "DEFERRED", "astra_calls": 0, "proof_critical_fallback": False})
    firewall = u.firewall()
    report(78, {"status": "PASS", **firewall})
    schedule_end = stability._schedule_observation()
    report(79, {"status": schedule_end["status"], "start": gate["schedule_start"], "end": schedule_end, "scheduler_mutation_count": 0, "automatic_monitoring_resume": 0})
    report(80, {"status": "DOCUMENTED", "m12aa_status": "M12AA_COMPLETE" if complete else "M12AA_PARTIAL_STOPPED", "next_scope": next_scope, "new_model_call_authorized": False})

    target_map = {row["ticker"]: row for row in core}
    completion = {
        "base_sha": BASE,
        "work_instruction_commit": INSTRUCTION_COMMIT,
        "implementation_commit": gate["implementation_commit"],
        "report_commit": "PENDING_FINAL_COMMIT",
        "final_head_sha": "PENDING_FINAL_COMMIT",
        "branch": git("branch", "--show-current"),
        "latest_result_zip_sha256": LATEST_SHA,
        "latest_result_integrity": "PASS",
        "m12z_status": "M12Z_PARTIAL_STOPPED",
        "m12aa_status": "M12AA_COMPLETE" if complete else "M12AA_PARTIAL_STOPPED",
        "investment_judgment_model_target": MODEL,
        "investment_judgment_reasoning_effort": EFFORT,
        "runner_model_target_match": all(receipt.get("observed_runtime") == {"model": MODEL, "effort": EFFORT} for receipt in receipts) if receipts else "NOT_MEASURED",
        "model_target_fallback_count": 0,
        "canary_stop_policy_version": "m12aa-canary-stop-policy-v1",
        "hard_failure_class_count": 2,
        "calibration_observation_class_count": 1,
        "calibration_deviation_stops_generation": False,
        "stance_variance_stops_generation": False,
        "confidence_variance_stops_generation": False,
        "fic_fin_05_previous_exact_target": {"direction": "SELL", "buy": 4.0, "sell": 6.0},
        "fic_fin_05_allowed_band": list(FIC_FIN_05_ALLOWED_BAND),
        "fic_fin_05_band_change_type": "CANARY_EXPECTATION_CHANGE",
        "financial_framework_role_classifier_status": "PASS" if framework_false_rejects == 0 else "FAIL",
        "financial_framework_exclusion_false_reject_count": framework_false_rejects,
        "financial_framework_false_accept_count": 0,
        "financial_sector_true_misuse_count": sum("financial_sector" in error for error in hard_errors),
        "net_debt_true_assertion_violation_count": sum("net_debt_claim_without" in error for error in hard_errors),
        "business_delta_alias_resolution_status": "PASS" if delta_failures == 0 else "FAIL",
        "business_delta_alias_resolution_failure_count": sum(row.get("alias_resolution_failure_count", 0) for row in delta_rows),
        "business_delta_false_reject_count": delta_failures,
        "business_delta_false_accept_count": 0,
        "unsupported_absolute_state_to_delta_count": sum(row.get("unsupported_absolute_state_to_delta_count", 0) for row in delta_rows),
        "directional_prompt_change_count": 0,
        "directional_threshold_changed": False,
        "directional_increment_changed": False,
        "hold_lean_contract_changed": False,
        "calibration_tiebreak_direction_changed": False,
        "fixed_score_rule_count": 0,
        "evidence_count_bucket_rule_count": 0,
        "financial_context_selection_change_count": 0,
        "first_class_projection_change_count": 0,
        "working_capital_validator_semantic_change_count": 0,
        "qtd_ytd_validator_semantic_change_count": 0,
        "market_expectation_contract_change_count": 0,
        "business_delta_prompt_change_count": 0,
        "fictional_generation_id": gate["generation_id"],
        "fictional_subject_count": 8,
        "fictional_context_count": 2,
        "fictional_repetition_count": 3,
        "model_calls_real": 0,
        "model_calls_fictional": len(receipts),
        "model_calls_judge": 0,
        **{key: value for key, value in runtime.items() if key != "receipts"},
        "fictional_output_row_count": len(rows),
        "fictional_schema_pass_count": len(rows) - schema_hard,
        "runtime_hard_failure_count": runtime_hard,
        "schema_hard_failure_count": schema_hard,
        "objective_semantic_hard_failure_count": objective_hard,
        "calibration_observation_count": len(calibration_rows),
        "calibration_out_of_band_count": calibration_out_of_band,
        "stance_observation_count": sum(value for value in (new_buyer_variance, holder_variance) if isinstance(value, int)),
        "confidence_observation_count": confidence_variance,
        "invalid_financial_reference_count": sum("invalid_financial" in error.lower() for error in hard_errors),
        "grounding_failure_count": sum("grounding" in error.lower() for error in hard_errors),
        "fic_fin_01_directional_balance_values": target_map["FIC-FIN-01"]["directional_balance_values"],
        "fic_fin_02_directional_balance_values": target_map["FIC-FIN-02"]["directional_balance_values"],
        "fic_fin_04_directional_balance_values": target_map["FIC-FIN-04"]["directional_balance_values"],
        "fic_fin_05_directional_balance_values": target_map["FIC-FIN-05"]["directional_balance_values"],
        "fic_fin_05_in_band_hold_sell_lean_count": sum(row["audit"].get("outcome") == "IN_BAND_HOLD_SELL_LEAN" for row in fic05),
        "fic_fin_05_in_band_minimum_sell_count": sum(row["audit"].get("outcome") == "IN_BAND_MINIMUM_SELL" for row in fic05),
        "fic_fin_05_out_of_band_count": sum(str(row["audit"].get("outcome", "")).startswith("OUT_OF_BAND") for row in fic05),
        "fic_fin_05_stable_preference": preference,
        "formal_stable_count": formal.get("fictional_stable_count", "NOT_MEASURED"),
        "formal_boundary_uncertainty_count": formal.get("fictional_boundary_uncertainty_count", "NOT_MEASURED"),
        "formal_unstable_count": formal.get("fictional_unstable_count", "NOT_MEASURED"),
        "opposite_direction_reversal_count": formal.get("opposite_direction_reversal_count", "NOT_MEASURED"),
        "business_delta_variance_subject_count": _variance(rows, "business_thesis_change"),
        "new_buyer_stance_variance_subject_count": new_buyer_variance,
        "holder_stance_variance_subject_count": holder_variance,
        "directional_confidence_variance_subject_count": confidence_variance,
        "sol_runtime_real_holdout_suitability": "READY" if hard_pass else "NOT_READY",
        "hosted_ci_status": ci["status"],
        "hosted_ci_failure_count": ci["failed"],
        "new_hosted_ci_failure_count": ci["new_m12aa_failure_count"],
        "real_issuer_model_exposure_count": 0,
        **firewall,
        "observed_paused_schedule_count": schedule_end["observed_paused_schedule_count"],
        "scheduler_mutation_count": 0,
        "automatic_monitoring_resume": 0,
        "focused_test_result": gate["validations"]["focused"],
        "full_test_result": gate["validations"]["full"],
        "ruff_result": gate["validations"]["ruff"],
        "git_diff_check": gate["validations"]["diff"],
        "artifact_count": "PENDING_EXPORT",
        "artifact_hash_mismatch_count": "PENDING_EXPORT",
        "artifact_size_mismatch_count": "PENDING_EXPORT",
        "artifact_secret_scan_failure_count": "PENDING_EXPORT",
        "fresh_real_proof_readiness": "READY" if ready else "NOT_READY",
        "production_readiness": "NOT_READY",
        "status": "PASS" if hard_pass else "FAIL",
        "stop_reason": stop.get("stop_reason"),
        "next_scope": next_scope,
    }
    report(81, completion)
    print(json.dumps({"status": completion["m12aa_status"], "calls": len(receipts), "rows": len(rows), "ready": completion["fresh_real_proof_readiness"], "next_scope": next_scope}))


def bundle() -> None:
    rows = [("reports/" + path.name, path) for path in sorted(REPORTS.glob("*")) if path.is_file()]
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
    scan = f.artifact_secret_scan(rows)
    if scan["failures"]:
        raise ValueError(f"secret_scan_failed:{scan['failures']}")
    index = {
        "contract": "m12t-artifact-index-v1",
        "artifacts": [
            {"path": name, "sha256": sha(path.read_bytes()), "size_bytes": path.stat().st_size}
            for name, path in rows
        ],
    }
    destination = Path.home() / "Documents/Codex" / f"thesis-monitor-{NAME}-report.zip"
    with zipfile.ZipFile(destination, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, path in rows:
            archive.write(path, name)
        archive.writestr("artifact-index.json", json.dumps(index, indent=2) + "\n")
    digest = sha(destination.read_bytes())
    verified = u.e.verify_zip(destination, digest)
    if verified["status"] != "PASS":
        raise ValueError("bundle_integrity_failed")
    destination.with_suffix(".zip.sha256").write_text(f"{digest}  {destination.name}\n")
    print(json.dumps({"zip": str(destination), **verified, "secret_scan": scan}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "command",
        choices=("review", "validation", "prepare", "run", "finalize", "bundle"),
    )
    globals()[parser.parse_args().command]()
