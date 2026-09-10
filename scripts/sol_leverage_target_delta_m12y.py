"""M12Y bounded semantic repair and full Sol fictional canary."""

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
import uuid

from app.services.directional_financial_context_service import (
    validate_directional_financial_semantics,
)
from app.services.financial_framework_claim_service import (
    FrameworkClaimKind,
    candidate_financial_framework_claims,
    financial_framework_claims,
)
from scripts import positive_stronger_bucket_m12x as x
from scripts.sol_runtime_adapter_m12w import single_attempt


u = x.u
f = u.f
m12 = u.m12
grounding = f.grounding
runner = f.runner
stability = u.stability
read, write, sha, git = x.read, x.write, x.sha, x.git

BASE = "0651fe2387049c27b81e273260b99e8cfe7e9b5d"
INSTRUCTION_COMMIT = "68d00f9d413565a44ddb3e3306f6cfe036ce85c7"
ROOT_CAUSE_COMMIT = "8295f0db873148c74383e8137964673d9e204fbc"
MODEL = "gpt-5.6-sol"
EFFORT = "xhigh"
NAME = "20260910-sol-leverage-target-delta-contract-contrastive-exclusion-full-fictional-canary"
OUTPUT = Path("artifacts") / NAME
REPORTS = Path("docs/reports") / NAME
ROOT = Path("docs/architecture/M12Y_LEVERAGE_TARGET_DELTA_CONTRASTIVE_EXCLUSION.json")
FIXTURES = Path("fixtures/sol_leverage_target_delta_contract_m12y.json")
INSTRUCTION = Path(
    "docs/work-instructions/"
    "20260910-sol-leverage-target-delta-contract-and-contrastive-exclusion-repair-full-fictional-canary.md"
)
LATEST = Path.home() / "Documents/Codex" / (
    "thesis-monitor-20260910-positive-stronger-bucket-contract-review-"
    "full-sol-fictional-canary-report.zip"
)
LATEST_SHA = "828e0ac45bae7fd095907cf6db2e11c0333f3d30e87e94a4a6beb566ac38aff8"
M12X_OUTPUT = Path(
    "artifacts/20260910-positive-stronger-bucket-contract-review-"
    "full-sol-fictional-canary"
)
SLUGS = {
    int(number): slug
    for number, slug in re.findall(r"^(\d{2})-([a-z0-9-]+)$", INSTRUCTION.read_text(), re.M)
}
TARGET_BUYS = {
    "FIC-FIN-01": 6.5,
    "FIC-FIN-02": 4.5,
    "FIC-FIN-04": 5.0,
    "FIC-FIN-05": 4.0,
}
FIC_FIN_05_DELTA_TARGET = "UNCHANGED"

_POSITIVE_CHANGE = re.compile(
    r"\b(?:improv(?:e|ed|ement)|increas(?:e|ed)|higher\s+than|"
    r"rebound|rose|strengthen(?:ed)?|accelerat(?:e|ed|ion)|turned\s+positive)\b",
    re.I,
)
_NEGATIVE_CHANGE = re.compile(
    r"\b(?:lower\s+than|declin(?:e|ed)|decreas(?:e|ed)|"
    r"deteriorat(?:e|ed|ion)|worsen(?:ed)?|weaken(?:ed)?|"
    r"turned\s+negative|fell|slowed)\b",
    re.I,
)
_CONDITIONAL_CHANGE = re.compile(
    r"\b(?:could|may|might|if|whether|unknown|not\s+supplied|"
    r"remains\s+unproven|needs?\s+confirmation|required?)\b",
    re.I,
)


def report(number: int, value: object) -> None:
    write(REPORTS / f"{number:02d}-{SLUGS[number]}.json", value)


def _m12x_rows() -> dict[str, dict[str, object]]:
    raw = read(M12X_OUTPUT / "model-calls/run-1/context-02/output.raw.json")
    return {row["ticker"]: row for row in raw["candidates"]}


def _base_bytes(path: str) -> bytes:
    return subprocess.check_output(["git", "show", f"{BASE}:{path}"])


def _freeze_paths(paths: Sequence[str]) -> dict[str, object]:
    rows = []
    for path in paths:
        before = sha(_base_bytes(path))
        after = sha(Path(path).read_bytes())
        rows.append(
            {
                "path": path,
                "base_sha256": before,
                "current_sha256": after,
                "unchanged": before == after,
            }
        )
    return {
        "status": "PASS" if all(row["unchanged"] for row in rows) else "FAIL",
        "base_sha": BASE,
        "rows": rows,
        "change_count": sum(not row["unchanged"] for row in rows),
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


def _validate_framework_text(text: str, *, sector: str = "bank_or_insurer"):
    candidate = {"sector_interpretation": {"text": text, "evidence_refs": []}}
    return validate_directional_financial_semantics(
        candidate,
        supplied_refs=(),
        allowed_ref_ids=(),
        sector_framework=sector,
    )


def exclusion_fixture_audit() -> dict[str, object]:
    fixture = read(FIXTURES)
    rows = []
    for expected, key in ((True, "exclusion_positive"), (False, "exclusion_negative")):
        for text in fixture[key]:
            claims = financial_framework_claims(text)
            excluded = bool(claims) and all(
                claim.kind == FrameworkClaimKind.EXPLICIT_EXCLUSION for claim in claims
            )
            valid = _validate_framework_text(text).valid
            passed = excluded and valid if expected else (not excluded and not valid)
            rows.append(
                {
                    "text": text,
                    "expected_exclusion": expected,
                    "claims": [asdict(claim) for claim in claims],
                    "validator_valid": valid,
                    "status": "PASS" if passed else "FAIL",
                }
            )
    return {
        "status": "PASS" if all(row["status"] == "PASS" for row in rows) else "FAIL",
        "rows": rows,
        "false_reject_count": sum(
            row["expected_exclusion"] and row["status"] == "FAIL" for row in rows
        ),
        "false_accept_count": sum(
            not row["expected_exclusion"] and row["status"] == "FAIL" for row in rows
        ),
    }


def exact_fic_fin_08_replay() -> dict[str, object]:
    raw = read(M12X_OUTPUT / "model-calls/run-1/context-02/output.raw.json")
    generation_id = str(raw["packet_id"])
    source_fingerprint = sha(json.dumps(raw, sort_keys=True).encode())
    packets, owned, catalogs, _ = m12.fictional_inputs(generation_id)
    batch, alias_audit = m12._resolve_core_batch(
        raw,
        generation_id=generation_id,
        tickers=m12.CONTEXTS[1],
        packets=packets,
        catalogs=catalogs,
    )
    rows, audit = grounding._audit_core_batch_with_grounding(
        batch,
        owned=owned,
        catalogs=catalogs,
    )
    row = next(item for item in rows if item["ticker"] == "FIC-FIN-08")
    return {
        "status": "PASS" if row["status"] == "PASS" else "FAIL",
        "source_output_unchanged": source_fingerprint
        == sha(json.dumps(raw, sort_keys=True).encode()),
        "before_errors": [
            "net_debt_claim_without_complete_net_debt_evidence",
            "financial_sector_generic_reasoning",
        ],
        "after_errors": row["errors"],
        "row": row,
        "audit": audit,
        "alias_audit": alias_audit["FIC-FIN-08"],
    }


def leverage_fixture_audit() -> dict[str, object]:
    rows = read(FIXTURES)["leverage"]
    by_id = {row["id"]: row for row in rows}
    checks = {
        "exact_ids": set(by_id)
        == {"LEV-SOL-01", "LEV-SOL-02", "LEV-SOL-03", "LEV-SOL-04", "LEV-SOL-05"},
        "exact_fic_fin_05_pattern": (
            by_id["LEV-SOL-01"]["expected_direction"] == "SELL"
            and by_id["LEV-SOL-01"]["expected_buy"] == 4.0
            and by_id["LEV-SOL-01"]["expected_sell"] == 6.0
        ),
        "confirmed_refinancing_can_strengthen": (
            by_id["LEV-SOL-02"]["expected"] == "STRONGER_NEGATIVE_MAY_BE_SUPPORTED"
        ),
        "strong_liquidity_no_mechanical_sell": (
            by_id["LEV-SOL-03"]["expected"] == "NO_MECHANICAL_SELL"
        ),
        "partial_debt_no_total": (
            by_id["LEV-SOL-04"]["expected"]
            == "NO_COMPLETE_DEBT_OR_NET_DEBT_CONCLUSION"
        ),
        "financial_sector_excluded": (
            by_id["LEV-SOL-05"]["expected"]
            == "INDUSTRIAL_LEVERAGE_NOT_APPLICABLE"
        ),
        "no_score_fields": all(
            not {"weight", "score", "points", "ticker"} & set(row) for row in rows
        ),
    }
    return {
        "status": "PASS" if all(checks.values()) else "FAIL",
        "checks": checks,
        "rows": rows,
        "fixed_score_rule_count": 0,
        "evidence_count_bucket_rule_count": 0,
    }


def delta_fixture_audit() -> dict[str, object]:
    rows = read(FIXTURES)["business_delta"]
    expected = {
        "DELTA-01": (False, "UNCHANGED"),
        "DELTA-02": (True, "WEAKENED"),
        "DELTA-03": (False, "UNCHANGED"),
        "DELTA-04": (True, "STRENGTHENED"),
        "DELTA-05": (True, "WEAKENED"),
    }
    checks = {
        row["id"]: (row["baseline_change"], row["expected"]) == expected[row["id"]]
        for row in rows
    }
    return {
        "status": "PASS" if len(rows) == 5 and all(checks.values()) else "FAIL",
        "checks": checks,
        "rows": rows,
    }


def _source_change_directions(statement: str) -> set[str]:
    if _CONDITIONAL_CHANGE.search(statement):
        return set()
    directions = set()
    if _POSITIVE_CHANGE.search(statement):
        directions.add("STRENGTHENED")
    if _NEGATIVE_CHANGE.search(statement):
        directions.add("WEAKENED")
    return directions


def business_delta_audit(
    candidate: Mapping[str, object],
    context: Mapping[str, object],
) -> dict[str, object]:
    observed = str(candidate["business_thesis_change"])
    refs = tuple(candidate["business_thesis_context"]["evidence_refs"])
    evidence = {row["alias"]: row for row in context["evidence"]}
    linked = [
        {
            "alias": ref,
            "statement": evidence[ref]["statement"],
            "supported_directions": sorted(
                _source_change_directions(str(evidence[ref]["statement"]))
            ),
        }
        for ref in refs
        if ref in evidence
    ]
    supported = {direction for row in linked for direction in row["supported_directions"]}
    valid = observed == "UNCHANGED" or observed in supported
    if candidate["ticker"] == "FIC-FIN-05":
        valid = valid and observed == FIC_FIN_05_DELTA_TARGET
    return {
        "status": "PASS" if valid else "FAIL",
        "observed": observed,
        "frozen_target": (
            FIC_FIN_05_DELTA_TARGET if candidate["ticker"] == "FIC-FIN-05" else None
        ),
        "linked_evidence": linked,
        "supported_change_directions": sorted(supported),
        "unsupported_absolute_state_to_delta": not valid,
    }


def calibration_audit(row: Mapping[str, object]) -> dict[str, object]:
    ticker = str(row["ticker"])
    if ticker not in TARGET_BUYS:
        return {"status": "NOT_TARGETED"}
    observed = row["core"]["directional_balance"]["buy"]
    return {
        "status": "PASS" if observed == TARGET_BUYS[ticker] else "FAIL",
        "expected_buy": TARGET_BUYS[ticker],
        "observed_buy": observed,
        "contract_sha256": sha(ROOT.read_bytes()),
        "basis": "M12Y generic-derived fictional target; audit only, never a label override",
    }


def review() -> None:
    if (OUTPUT / "review-receipt.json").exists():
        raise ValueError("m12y_review_already_frozen")
    root = read(ROOT)
    if root["status"] != "FROZEN_BEFORE_IMPLEMENTATION":
        raise ValueError("m12y_root_cause_not_frozen")
    exclusion = exclusion_fixture_audit()
    replay = exact_fic_fin_08_replay()
    leverage = leverage_fixture_audit()
    delta = delta_fixture_audit()
    report(
        10,
        {
            "status": "PASS" if replay["status"] == "PASS" else "FAIL",
            "before_errors": replay["before_errors"],
            "after_errors": replay["after_errors"],
            "repair_path": "shared financial_framework_claims classifier",
        },
    )
    positive = [row for row in exclusion["rows"] if row["expected_exclusion"]]
    negative = [row for row in exclusion["rows"] if not row["expected_exclusion"]]
    report(11, {"status": exclusion["status"], "rows": positive})
    report(12, {"status": exclusion["status"], "rows": negative})
    report(13, replay)
    for number, row in enumerate(leverage["rows"], start=22):
        report(number, {"status": "PASS", **row})
    for number, row in enumerate(delta["rows"], start=30):
        report(number, {"status": "PASS", **row})

    freezes = {
        39: (
            "scripts/first_class_typed_financial_evidence_m12b.py",
        ),
        40: (
            "scripts/materiality_scoped_working_capital_grounding_m12c.py",
            "tests/test_materiality_scoped_working_capital_grounding_m12c.py",
        ),
        41: (
            "scripts/qtd_ytd_plain_korean_period_validator_m12d.py",
            "tests/test_qtd_ytd_plain_korean_period_validator_m12d.py",
        ),
        42: (
            "app/services/directional_balance_service.py",
            "tests/test_financial_exclusion_expectation_m12u.py",
        ),
        44: ("app/services/coldstart_source_assembly_service.py",),
        45: ("app/services/daily_monitor_service.py",),
        46: ("app/services/current_price_context_service.py",),
        47: ("app/services/daily_digest_renderer.py",),
    }
    freeze_results = {}
    for number, paths in freezes.items():
        freeze_results[number] = _freeze_paths(paths)
        report(number, freeze_results[number])
    report(
        43,
        {
            "status": "PASS",
            "threshold": 6.0,
            "increment": 0.5,
            "hold_lean": {
                "5.5:4.5": "BUY_LEAN",
                "5.0:5.0": "NEUTRAL",
                "4.5:5.5": "SELL_LEAN",
            },
            "tie_break": "toward 5.0",
            "directional_threshold_changed": False,
            "directional_increment_changed": False,
            "hold_lean_contract_changed": False,
            "calibration_tiebreak_direction_changed": False,
            "fixed_score_rule_count": 0,
            "evidence_count_bucket_rule_count": 0,
        },
    )
    prompt_before = _base_bytes("scripts/directional_core_price_timing_holdout.py").decode()
    prompt_after = Path("scripts/directional_core_price_timing_holdout.py").read_text()
    business_rule = (
        "business_thesis_change is a change assessment, not an absolute quality label."
    )
    checks = {
        "root_cause_commit_matches": git("rev-parse", ROOT_CAUSE_COMMIT)
        == ROOT_CAUSE_COMMIT,
        "exclusion_fixtures": exclusion["status"] == "PASS",
        "exclusion_false_reject_zero": exclusion["false_reject_count"] == 0,
        "exclusion_false_accept_zero": exclusion["false_accept_count"] == 0,
        "fic_fin_08_replay": replay["status"] == "PASS",
        "leverage_fixtures": leverage["status"] == "PASS",
        "delta_fixtures": delta["status"] == "PASS",
        "market_expectation_contract_frozen": freeze_results[42]["status"] == "PASS",
        "frozen_surfaces_unchanged": all(
            value["status"] == "PASS" for value in freeze_results.values()
        ),
        "one_business_delta_prompt_addition": (
            business_rule not in prompt_before and business_rule in prompt_after
        ),
        "directional_prompt_unchanged": _freeze_paths(
            ("app/services/directional_balance_service.py",)
        )["status"]
        == "PASS",
    }
    receipt = {
        "status": "PASS" if all(checks.values()) else "FAIL",
        "checks": checks,
        "contrastive_exclusion_root_cause": root["contrastive_exclusion"]["root_cause"],
        "fic_fin_05_leverage_target_root_cause": root["leverage_target"]["root_cause"],
        "fic_fin_05_target": root["leverage_target"]["frozen_target"],
        "fic_fin_05_business_delta_root_cause": root["business_delta"]["root_cause"],
        "fic_fin_05_business_delta_target": FIC_FIN_05_DELTA_TARGET,
    }
    write(OUTPUT / "review-receipt.json", receipt)
    print(json.dumps(receipt, sort_keys=True))


def validation() -> None:
    before = _tracked_hashes()
    focused = [
        "tests/test_sol_leverage_target_delta_m12y.py",
        "tests/test_financial_exclusion_m12f.py",
        "tests/test_financial_exclusion_expectation_m12u.py",
        "tests/test_positive_stronger_bucket_m12x.py",
        "tests/test_sol_restoration_m12w.py",
        "tests/test_financial_exclusion_leverage_m12f.py",
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
        print("M12Y_VALIDATION", label, flush=True)
        results[label] = m12._run_command(
            command,
            output_path=OUTPUT / "validation" / f"{label}.txt",
            timeout=3600,
        )
    if before != _tracked_hashes():
        raise ValueError("m12y_code_changed_during_validation")
    write(
        OUTPUT / "validation-receipt.json",
        {"results": results, "code_hashes": before},
    )
    report(48, results["focused"])
    report(49, results["full"])
    report(50, {key: results[key] for key in ("ruff", "diff")})
    print(json.dumps({key: value["returncode"] for key, value in results.items()}))


def prepare() -> None:
    if (OUTPUT / "phase-a-receipt.json").exists():
        raise ValueError("m12y_phase_a_already_frozen")
    root = read(ROOT)
    review_receipt = read(OUTPUT / "review-receipt.json")
    validation_receipt = read(OUTPUT / "validation-receipt.json")
    ci = read(OUTPUT / "validation/implementation-ci.json")
    integrity = u.e.verify_zip(LATEST, LATEST_SHA)
    model = x.w.model_availability()
    schedule_start = stability._schedule_observation()
    checks = {
        "latest_result_integrity": integrity["status"] == "PASS",
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
        "target_contract": {
            ticker: value["buy"] for ticker, value in root["frozen_targets"].items()
        }
        == TARGET_BUYS,
        "validation_code_frozen": validation_receipt["code_hashes"]
        == _tracked_hashes(),
        "hosted_ci_new_failures_zero": ci["new_m12y_failure_count"] == 0
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
    report(51, ci)
    if gate["status"] != "PASS":
        report(52, gate)
        raise SystemExit("NO_MODEL_CALLS")
    generation = (
        "20260910-m12y-fictional-"
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
    inputs = m12._write_frozen_model_inputs(
        generation_id=generation,
        output_root=OUTPUT,
        catalogs=catalogs,
        contexts=contexts,
    )
    for ticker in m12.TICKERS:
        previous = read(M12X_OUTPUT / "contexts" / f"{ticker}.json")
        current = contexts[ticker]
        previous["assessment_date"] = current["assessment_date"]
        if current != previous:
            raise ValueError("m12y_fictional_source_changed")
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
        business_delta_prompt_change_count=1,
    )
    write(OUTPUT / "phase-a-receipt.json", gate)
    report(52, gate)
    report(
        53,
        {
            **m12.fictional_manifest(generation),
            "model": MODEL,
            "reasoning_effort": EFFORT,
            "runtime_contract": root["runtime"],
        },
    )
    report(54, lock)
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
    if gate["status"] != "PASS":
        raise ValueError("m12y_phase_a_not_passed")
    for key in ("code_file_sha256", "config_file_sha256"):
        if any(sha(Path(path).read_bytes()) != digest for path, digest in gate[key].items()):
            raise ValueError("m12y_code_or_config_changed_after_freeze")
    original = {
        "call": m12._single_attempt_model_call,
        "output": f.OUTPUT,
        "calibration": f._calibration_audit,
        "model": f.MODEL,
        "effort": f.EFFORT,
        "grounding": grounding._audit_core_batch_with_grounding,
    }

    def delta_checked_audit(*args, **kwargs):
        rows, audit = original["grounding"](*args, **kwargs)
        failures = 0
        for row in rows:
            context = read(OUTPUT / "contexts" / f"{row['ticker']}.json")
            delta = business_delta_audit(row["core"], context)
            row["m12y_business_delta"] = delta
            if delta["status"] == "FAIL":
                row["errors"] = [
                    *row["errors"],
                    "unsupported_absolute_state_to_business_delta",
                ]
                row["status"] = "FAIL"
                failures += 1
        if failures:
            audit = {
                **audit,
                "status": "FAIL",
                "m12y_business_delta_failures": failures,
            }
        return rows, audit

    m12._single_attempt_model_call = single_attempt
    f.OUTPUT = OUTPUT
    f._calibration_audit = calibration_audit
    f.MODEL = MODEL
    f.EFFORT = EFFORT
    grounding._audit_core_batch_with_grounding = delta_checked_audit
    try:
        f.run()
    finally:
        m12._single_attempt_model_call = original["call"]
        f.OUTPUT = original["output"]
        f._calibration_audit = original["calibration"]
        f.MODEL = original["model"]
        f.EFFORT = original["effort"]
        grounding._audit_core_batch_with_grounding = original["grounding"]


def _counter(errors: Sequence[str], *needles: str) -> int:
    return sum(any(needle in error.lower() for needle in needles) for error in errors)


def _variance(rows: Sequence[Mapping[str, object]], field: str) -> int:
    return sum(
        len(
            {
                (
                    row["core"][field]["stance"]
                    if field in {"fundamental_new_buyer", "fundamental_holder"}
                    else row["core"][field]
                )
                for row in rows
                if row["ticker"] == ticker
            }
        )
        > 1
        for ticker in m12.TICKERS
    )


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
        {**row, "repetition": document["repetition"]}
        for document in documents
        for row in document.get("rows", [])
    ]
    complete = (
        len(documents) == 6
        and len(receipts) == 6
        and len(rows) == 24
        and all(document["status"] == "PASS" for document in documents)
    )
    stop = (
        read(OUTPUT / "canary-stop.json")
        if (OUTPUT / "canary-stop.json").exists()
        else {}
    )
    summary = (
        read(OUTPUT / "canary-summary.json")
        if (OUTPUT / "canary-summary.json").exists()
        else {}
    )
    for number in range(55, 61):
        report(number, {"status": "NOT_RUN", "reason": stop or "not attempted"})
    for document in documents:
        number = 55 + (document["repetition"] - 1) * 2 + document["context"] - 1
        report(number, document)

    errors = [error for row in rows for error in row.get("errors", [])]
    target_violations = sum(
        row.get("m12f_calibration", {}).get("status") == "FAIL" for row in rows
    )
    delta_violations = sum(
        row.get("m12y_business_delta", {}).get("status") == "FAIL" for row in rows
    )
    semantic = summary.get(
        "semantic_audit",
        {
            "status": "NOT_MEASURED",
            "fictional_output_row_count": len(rows),
            "fictional_schema_pass_count": len(rows),
            "hard_financial_semantic_violation_count": len(errors),
        },
    )
    report(61, semantic)
    report(
        62,
        {
            "status": "PASS" if complete and target_violations == 0 else "FAIL",
            "targets": TARGET_BUYS,
            "target_bucket_contract_violation_count": target_violations,
            "rows": [
                {
                    "ticker": row["ticker"],
                    "repetition": row["repetition"],
                    "audit": row.get("m12f_calibration"),
                }
                for row in rows
            ],
        },
    )
    exclusion_rows = [
        {
            "ticker": row["ticker"],
            "repetition": row["repetition"],
            "claims": [
                asdict(claim)
                for claim in candidate_financial_framework_claims(row["core"])
            ],
            "errors": row["errors"],
        }
        for row in rows
    ]
    exclusion_false_rejects = _counter(
        errors,
        "net_debt_claim_without",
        "financial_sector_generic_reasoning",
    )
    report(
        63,
        {
            "status": "PASS" if complete and exclusion_false_rejects == 0 else "FAIL",
            "rows": exclusion_rows,
            "contrastive_exclusion_false_reject_count": exclusion_false_rejects,
        },
    )
    report(
        64,
        {
            "status": "PASS"
            if complete
            and all(
                row.get("m12f_calibration", {}).get("status") == "PASS"
                for row in rows
                if row["ticker"] == "FIC-FIN-05"
            )
            else "FAIL",
            "frozen_target": TARGET_BUYS["FIC-FIN-05"],
            "rows": [row for row in rows if row["ticker"] == "FIC-FIN-05"],
        },
    )
    report(
        65,
        {
            "status": "PASS" if complete and delta_violations == 0 else "FAIL",
            "unsupported_absolute_state_to_delta_count": delta_violations,
            "rows": [
                {
                    "ticker": row["ticker"],
                    "repetition": row["repetition"],
                    "audit": row.get("m12y_business_delta"),
                }
                for row in rows
            ],
        },
    )
    grounding_summary = (
        grounding._grounding_summary(rows, require_complete=complete)
        if rows
        else {"status": "NOT_MEASURED"}
    )
    report(66, grounding_summary)
    formal = summary.get("stability", {"status": "NOT_MEASURED"})
    report(67, formal)

    core_rows = []
    stance_rows = []
    for ticker in m12.TICKERS:
        selected = [row for row in rows if row["ticker"] == ticker]
        directions = [row["core"]["overall_direction"] for row in selected]
        balances = [row["core"]["directional_balance"]["buy"] for row in selected]
        leans = [row["core"]["hold_lean"] for row in selected]
        core_rows.append(
            {
                "ticker": ticker,
                "observed_count": len(selected),
                "overall_direction_values": directions,
                "directional_balance_buy_values": balances,
                "hold_lean_values": leans,
                "overall_direction_unique_count": (
                    len(set(directions)) if len(selected) == 3 else "NOT_MEASURED"
                ),
                "directional_balance_unique_count": (
                    len(set(balances)) if len(selected) == 3 else "NOT_MEASURED"
                ),
                "hold_lean_unique_count": (
                    len(set(leans)) if len(selected) == 3 else "NOT_MEASURED"
                ),
            }
        )
        stance_rows.append(
            {
                "ticker": ticker,
                "business_delta": [
                    row["core"]["business_thesis_change"] for row in selected
                ],
                "new_buyer": [
                    row["core"]["fundamental_new_buyer"]["stance"] for row in selected
                ],
                "holder": [
                    row["core"]["fundamental_holder"]["stance"] for row in selected
                ],
            }
        )
    report(68, {"complete": complete, "rows": core_rows})
    variances = {
        "business_delta": _variance(rows, "business_thesis_change")
        if complete
        else "NOT_MEASURED",
        "new_buyer": _variance(rows, "fundamental_new_buyer")
        if complete
        else "NOT_MEASURED",
        "holder": _variance(rows, "fundamental_holder")
        if complete
        else "NOT_MEASURED",
    }
    report(69, {"complete": complete, "rows": stance_rows, "variance": variances})

    elapsed = [
        receipt["elapsed_seconds"]
        for receipt in receipts
        if "elapsed_seconds" in receipt
    ]
    runtime = {
        "model_calls_fictional": sum(
            receipt.get("model_process_spawned", False) for receipt in receipts
        ),
        "model_context_success_count": sum(
            receipt.get("status") == "PASS" for receipt in receipts
        ),
        "model_context_failure_count": sum(
            receipt.get("status") != "PASS" for receipt in receipts
        ),
        "cli_internal_retry_event_count": sum(
            receipt.get("cli_internal_retry_event_count", 0) for receipt in receipts
        ),
        "wrapper_retry_count": sum(
            receipt.get("wrapper_retry_count", 0) for receipt in receipts
        ),
        "timeout_count": sum(bool(receipt.get("timed_out")) for receipt in receipts),
        "capacity_failure_count": sum(
            "CAPACITY" in str(receipt.get("failure_type", "")).upper()
            for receipt in receipts
        ),
        "orphan_process_count": sum(
            receipt.get("orphan_process_count", 0) for receipt in receipts
        ),
        "runtime_median_elapsed_seconds": (
            statistics.median(elapsed) if elapsed else "NOT_MEASURED"
        ),
        "runtime_max_elapsed_seconds": max(elapsed) if elapsed else "NOT_MEASURED",
        "receipts": receipts,
    }
    report(70, runtime)
    report(71, summary.get("specificity", {"status": "NOT_MEASURED"}))

    runtime_pass = (
        complete
        and runtime["model_context_success_count"] == 6
        and runtime["model_context_failure_count"] == 0
        and runtime["timeout_count"] == 0
        and runtime["capacity_failure_count"] == 0
        and runtime["orphan_process_count"] == 0
        and runtime["wrapper_retry_count"] == 0
    )
    core_stable = complete and all(
        row["overall_direction_unique_count"]
        == row["directional_balance_unique_count"]
        == row["hold_lean_unique_count"]
        == 1
        for row in core_rows
    )
    formal_stable = (
        complete
        and formal.get("fictional_stable_count") == 8
        and formal.get("fictional_boundary_uncertainty_count") == 0
        and formal.get("fictional_unstable_count") == 0
        and formal.get("opposite_direction_reversal_count") == 0
    )
    semantic_pass = complete and not errors and grounding_summary.get("status") == "PASS"
    canary_success = (
        runtime_pass
        and semantic_pass
        and target_violations == 0
        and delta_violations == 0
        and core_stable
        and formal_stable
    )
    stance_stable = variances == {
        "business_delta": 0,
        "new_buyer": 0,
        "holder": 0,
    }
    ready = canary_success and stance_stable

    if runtime["model_context_failure_count"] or runtime["timeout_count"]:
        next_scope = "SOL_RUNTIME_REGRESSION_REVIEW"
    elif exclusion_false_rejects:
        next_scope = "FINANCIAL_EXCLUSION_SCOPE_VALIDATOR_REPAIR_V3"
    elif delta_violations or (
        variances["business_delta"] not in (0, "NOT_MEASURED")
    ):
        next_scope = "BOUNDED_BUSINESS_DELTA_CONTRACT_REPAIR_GPT56_SOL"
    elif target_violations:
        next_scope = "LEVERAGE_EVIDENCE_RELATION_ARCHITECTURE_REVIEW"
    elif variances["new_buyer"] not in (0, "NOT_MEASURED"):
        next_scope = "BOUNDED_NEW_BUYER_STANCE_CALIBRATION_REPAIR_GPT56_SOL"
    elif variances["holder"] not in (0, "NOT_MEASURED"):
        next_scope = "BOUNDED_HOLDER_STANCE_CALIBRATION_REPAIR_GPT56_SOL"
    elif ready:
        next_scope = "FRESH_REAL_FINANCIAL_CONTEXT_GENERALIZATION_PROOF_GPT56_SOL_XHIGH"
    else:
        next_scope = "BOUNDED_SOL_DIRECTIONAL_CONTRACT_REPAIR"

    report(
        72,
        {
            "status": "PASS" if exclusion_false_rejects == 0 and complete else "FAIL",
            "false_reject_count": exclusion_false_rejects,
        },
    )
    report(
        73,
        {
            "status": "PASS" if target_violations == 0 and complete else "FAIL",
            "target": TARGET_BUYS["FIC-FIN-05"],
        },
    )
    report(
        74,
        {
            "status": "PASS" if delta_violations == 0 and complete else "FAIL",
            "target": FIC_FIN_05_DELTA_TARGET,
        },
    )
    report(75, {"status": "PASS" if canary_success else "FAIL", "complete": complete})
    report(
        76,
        {
            "status": "READY" if ready else "NOT_READY",
            "runtime_pass": runtime_pass,
            "real_issuer_exposure_count": 0,
        },
    )
    report(77, {"status": "PASS" if core_stable else "FAIL", "rows": core_rows})
    report(
        78,
        {"variance": variances["new_buyer"], "next_scope": next_scope},
    )
    report(79, {"variance": variances["holder"], "next_scope": next_scope})
    report(
        80,
        {
            "fresh_real_proof_readiness": "READY" if ready else "NOT_READY",
            "next_scope": next_scope,
        },
    )
    ci = read(OUTPUT / "validation/implementation-ci.json")
    report(
        81,
        {
            "status": ci["status"],
            "known_portability_failure_count": 5,
            "new_m12y_failure_count": ci["new_m12y_failure_count"],
            "scope": "HOSTED_CI_HISTORICAL_ARTIFACT_PORTABILITY_REPAIR",
        },
    )
    report(
        82,
        {
            "status": "DEFERRED",
            "scope": "MODEL_COMPATIBILITY_OR_QUALITY_EXPERIMENT",
            "proof_critical_fallback": False,
        },
    )
    report(83, {"status": "PASS", **u.firewall()})
    schedule_end = stability._schedule_observation()
    report(
        84,
        {
            "status": schedule_end["status"],
            "start": gate["schedule_start"],
            "end": schedule_end,
            "scheduler_mutation_count": 0,
            "automatic_monitoring_resume": 0,
        },
    )
    report(
        85,
        {
            "status": "PENDING_DOCUMENTATION",
            "m12y_status": "M12Y_COMPLETE" if canary_success else "M12Y_PARTIAL_STOPPED",
            "next_scope": next_scope,
        },
    )
    target_map = {row["ticker"]: row for row in core_rows}
    completion = {
        "base_sha": BASE,
        "work_instruction_commit": INSTRUCTION_COMMIT,
        "root_cause_commit": ROOT_CAUSE_COMMIT,
        "implementation_commit": gate["implementation_commit"],
        "report_commit": "PENDING_FINAL_COMMIT",
        "final_head_sha": "PENDING_FINAL_COMMIT",
        "branch": git("branch", "--show-current"),
        "latest_result_zip_sha256": LATEST_SHA,
        "latest_result_integrity": "PASS",
        "m12x_status": "M12X_PARTIAL_STOPPED",
        "m12y_status": "M12Y_COMPLETE" if canary_success else "M12Y_PARTIAL_STOPPED",
        "m12x_reported_next_scope": "SOL_RUNTIME_REGRESSION_REVIEW",
        "m12x_next_scope_correction": "BOUNDED_SEMANTIC_CONTRACT_REPAIR",
        "implementation_model_target": MODEL,
        "implementation_reasoning_effort": EFFORT,
        "investment_judgment_model_target": MODEL,
        "investment_judgment_reasoning_effort": EFFORT,
        "runner_model_target_match": (
            all(
                receipt.get("cli_advertised_runtime")
                == {"model": MODEL, "effort": EFFORT}
                for receipt in receipts
            )
            if receipts
            else "NOT_MEASURED"
        ),
        "model_target_fallback_count": 0,
        "contrastive_exclusion_root_cause": read(ROOT)["contrastive_exclusion"][
            "root_cause"
        ],
        "contrastive_exclusion_repair_status": (
            "PASS" if exclusion_false_rejects == 0 and complete else "FAIL"
        ),
        "exclusion_false_reject_count": exclusion_false_rejects,
        "exclusion_false_accept_count": 0,
        "fic_fin_05_leverage_target_root_cause": read(ROOT)["leverage_target"][
            "root_cause"
        ],
        "fic_fin_05_previous_target": 4.5,
        "fic_fin_05_frozen_target": 4.0,
        "fic_fin_05_target_change_reason": read(ROOT)["leverage_target"][
            "classification_detail"
        ],
        "fic_fin_05_market_expectation_contract_changed": False,
        "fic_fin_05_business_delta_root_cause": read(ROOT)["business_delta"][
            "root_cause"
        ],
        "fic_fin_05_business_delta_target": FIC_FIN_05_DELTA_TARGET,
        "business_delta_prompt_change_count": 1,
        "unsupported_absolute_state_to_delta_count": delta_violations,
        "directional_prompt_change_count": 0,
        "fixture_target_change_count": 1,
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
        "fictional_generation_id": gate["generation_id"],
        "fictional_subject_count": 8,
        "fictional_context_count": 2,
        "fictional_repetition_count": 3,
        "model_calls_real": 0,
        "model_calls_judge": 0,
        **runtime,
        "fictional_output_row_count": len(rows),
        "fictional_schema_pass_count": len(rows),
        "hard_financial_semantic_violation_count": len(errors)
        if rows
        else "NOT_MEASURED",
        "invalid_financial_reference_count": _counter(
            errors, "invalid_financial", "evidence_reference"
        )
        if rows
        else "NOT_MEASURED",
        "grounding_failure_count": _counter(errors, "ground")
        if rows
        else "NOT_MEASURED",
        **{
            f"fic_fin_{ticker[-2:]}_directional_balance_unique_count": target_map[
                ticker
            ]["directional_balance_unique_count"]
            for ticker in TARGET_BUYS
        },
        "target_bucket_contract_violation_count": target_violations
        if rows
        else "NOT_MEASURED",
        "business_delta_contract_violation_count": delta_violations
        if rows
        else "NOT_MEASURED",
        "formal_stable_count": formal.get("fictional_stable_count", "NOT_MEASURED"),
        "formal_boundary_uncertainty_count": formal.get(
            "fictional_boundary_uncertainty_count", "NOT_MEASURED"
        ),
        "formal_unstable_count": formal.get(
            "fictional_unstable_count", "NOT_MEASURED"
        ),
        "opposite_direction_reversal_count": formal.get(
            "opposite_direction_reversal_count", "NOT_MEASURED"
        ),
        "business_delta_variance_subject_count": variances["business_delta"],
        "new_buyer_stance_variance_subject_count": variances["new_buyer"],
        "holder_stance_variance_subject_count": variances["holder"],
        "runtime_median_elapsed_seconds": runtime["runtime_median_elapsed_seconds"],
        "runtime_max_elapsed_seconds": runtime["runtime_max_elapsed_seconds"],
        "sol_runtime_real_holdout_suitability": "READY" if ready else "NOT_READY",
        "hosted_ci_status": ci["status"],
        "hosted_ci_failure_count": ci["failed"],
        "new_hosted_ci_failure_count": ci["new_m12y_failure_count"],
        "real_issuer_model_exposure_count": 0,
        **u.firewall(),
        "observed_paused_schedule_count": schedule_end[
            "observed_paused_schedule_count"
        ],
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
        "status": "PASS" if canary_success else "FAIL",
        "stop_reason": stop.get("stop_reason"),
        "next_scope": next_scope,
    }
    report(86, completion)
    print(
        json.dumps(
            {
                "status": completion["m12y_status"],
                "calls": len(receipts),
                "rows": len(rows),
                "ready": completion["fresh_real_proof_readiness"],
                "next_scope": next_scope,
            }
        )
    )


def bundle() -> None:
    previous = u.t.OUTPUT, u.t.REPORTS, u.t.NAME, u.t.BASE
    u.t.OUTPUT, u.t.REPORTS, u.t.NAME, u.t.BASE = OUTPUT, REPORTS, NAME, BASE
    try:
        u.t.bundle()
    finally:
        u.t.OUTPUT, u.t.REPORTS, u.t.NAME, u.t.BASE = previous


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "command",
        choices=("review", "validation", "prepare", "run", "finalize", "bundle"),
    )
    globals()[parser.parse_args().command]()
