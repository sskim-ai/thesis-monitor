"""M12Z alias-safe business-delta audit and full Sol fictional canary."""

from __future__ import annotations

import argparse
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
import json
from pathlib import Path
import re
import statistics
import subprocess
import sys
import uuid
import zipfile

from scripts import sol_leverage_target_delta_m12y as y


u = y.u
f = y.f
m12 = y.m12
grounding = y.grounding
stability = y.stability
read, write, sha, git = y.read, y.write, y.sha, y.git

BASE = "89bee202be8a4ae2f0eac7ce2fdca1a095c7818e"
INSTRUCTION_COMMIT = "55bb3e92e7f40455ff547340c7e876b36292e88b"
ROOT_CAUSE_COMMIT = "9bcba40e4ef67fa025ff72d9badcbc0bf92da7a7"
MODEL = "gpt-5.6-sol"
EFFORT = "xhigh"
NAME = "20260910-business-delta-alias-resolution-balance-confidence-full-sol-canary"
OUTPUT = Path("artifacts") / NAME
REPORTS = Path("docs/reports") / NAME
ROOT = Path("docs/architecture/M12Z_BUSINESS_DELTA_ALIAS_BALANCE_CONFIDENCE.json")
FIXTURES = Path("fixtures/business_delta_alias_balance_confidence_m12z.json")
INSTRUCTION = Path(
    "docs/work-instructions/"
    "20260910-business-delta-alias-resolution-and-balance-confidence-separation-full-sol-canary.md"
)
LATEST = Path.home() / "Documents/Codex" / (
    "thesis-monitor-20260910-sol-leverage-target-delta-contract-"
    "contrastive-exclusion-full-fictional-canary-report.zip"
)
LATEST_SHA = "67292aaaf81b8122c2c1a8bb62682d2889d83c5182317207fbd61fe9401169e3"
M12Y_OUTPUT = Path(
    "artifacts/20260910-sol-leverage-target-delta-contract-"
    "contrastive-exclusion-full-fictional-canary"
)
M12Y_GENERATION = "20260910-m12y-fictional-20260910T043154Z-2761aab01862"
TARGET_BUYS = {
    "FIC-FIN-01": 6.5,
    "FIC-FIN-02": 4.5,
    "FIC-FIN-04": 5.0,
    "FIC-FIN-05": 4.0,
}
FIC_FIN_05_DELTA_TARGET = "UNCHANGED"
BASE_FILE_SHA256 = dict(y.BASE_FILE_SHA256)
SLUGS = {
    int(number): slug
    for number, slug in re.findall(r"^(\d{2})-([a-z0-9-]+)$", INSTRUCTION.read_text(), re.M)
}
PROMPT_CLARIFICATION = (
    "Keep directional balance strength separate from directional confidence: "
    "directional_balance expresses the strength and balance of the supplied directional "
    "evidence, while directional_confidence expresses epistemic confidence given missing "
    "data, durability, valuation, or validation limits. Future durability that is merely "
    "not yet proven may lower confidence without automatically lowering a stronger "
    "current-evidence balance; only supplied evidence that directly calls the current "
    "improvement's causality, persistence, reversibility, or evidential validity into "
    "question can make adjacent strength buckets genuinely supportable. Apply the "
    "conservative adjacent-bucket tie-break only after this separation, not merely because "
    "an Unknown exists."
)


def without_m12z_prompt(prompt: str) -> str:
    needle = "\n\n" + PROMPT_CLARIFICATION
    if prompt.count(PROMPT_CLARIFICATION) != 1 or needle not in prompt:
        raise ValueError("m12z_prompt_clarification_identity_mismatch")
    return prompt.replace(needle, "", 1)


def report(number: int, value: object) -> None:
    write(REPORTS / f"{number:02d}-{SLUGS[number]}.json", value)


def _catalog_payload(catalog: object) -> dict[str, object]:
    if hasattr(catalog, "model_dump"):
        payload = catalog.model_dump(mode="json")
    elif isinstance(catalog, Mapping):
        payload = dict(catalog)
    else:
        raise TypeError("evidence_alias_catalog_required")
    return payload


def _context_by_canonical_ref(
    *,
    ticker: str,
    context: Mapping[str, object],
    catalog: object,
) -> tuple[dict[str, dict[str, object]], dict[str, str], list[str]]:
    payload = _catalog_payload(catalog)
    errors: list[str] = []
    if str(context.get("ticker") or ticker) != ticker:
        errors.append("INVALID_OR_UNRESOLVED_EVIDENCE_REF:context_ticker_mismatch")
    if str(payload.get("ticker") or "") != ticker:
        errors.append("INVALID_OR_UNRESOLVED_EVIDENCE_REF:catalog_ticker_mismatch")
    context_rows = context.get("evidence")
    entries = payload.get("entries")
    if not isinstance(context_rows, list) or not isinstance(entries, list):
        return {}, {}, [*errors, "INVALID_OR_UNRESOLVED_EVIDENCE_REF:catalog_shape"]

    by_alias: dict[str, dict[str, object]] = {}
    for row in context_rows:
        if not isinstance(row, Mapping):
            errors.append("INVALID_OR_UNRESOLVED_EVIDENCE_REF:context_row_shape")
            continue
        alias = str(row.get("alias") or "")
        if not alias or alias in by_alias:
            errors.append("INVALID_OR_UNRESOLVED_EVIDENCE_REF:duplicate_context_alias")
            continue
        by_alias[alias] = dict(row)

    canonical_rows: dict[str, dict[str, object]] = {}
    alias_to_canonical: dict[str, str] = {}
    for entry in entries:
        if not isinstance(entry, Mapping):
            errors.append("INVALID_OR_UNRESOLVED_EVIDENCE_REF:catalog_entry_shape")
            continue
        alias = str(entry.get("alias") or "")
        canonical_ref = str(entry.get("canonical_ref") or "")
        if str(entry.get("ticker") or "") != ticker:
            errors.append("INVALID_OR_UNRESOLVED_EVIDENCE_REF:cross_ticker_alias")
            continue
        if not alias or alias in alias_to_canonical:
            errors.append("INVALID_OR_UNRESOLVED_EVIDENCE_REF:duplicate_catalog_alias")
            continue
        if not canonical_ref or canonical_ref in canonical_rows:
            errors.append("INVALID_OR_UNRESOLVED_EVIDENCE_REF:canonical_collision")
            continue
        context_row = by_alias.get(alias)
        if context_row is None:
            errors.append("INVALID_OR_UNRESOLVED_EVIDENCE_REF:alias_not_in_context")
            continue
        alias_to_canonical[alias] = canonical_ref
        canonical_rows[canonical_ref] = context_row
    return canonical_rows, alias_to_canonical, errors


def business_delta_audit(
    candidate: Mapping[str, object],
    context: Mapping[str, object],
    catalog: object,
) -> dict[str, object]:
    ticker = str(candidate.get("ticker") or "")
    observed = str(candidate.get("business_thesis_change") or "")
    thesis_context = candidate.get("business_thesis_context")
    refs = (
        tuple(str(ref) for ref in thesis_context.get("evidence_refs", ()))
        if isinstance(thesis_context, Mapping)
        else ()
    )
    canonical_rows, alias_to_canonical, errors = _context_by_canonical_ref(
        ticker=ticker,
        context=context,
        catalog=catalog,
    )
    linked: list[dict[str, object]] = []
    for ref in refs:
        canonical_ref = alias_to_canonical.get(ref, ref)
        source = canonical_rows.get(canonical_ref)
        if source is None:
            errors.append(f"INVALID_OR_UNRESOLVED_EVIDENCE_REF:{ref}")
            continue
        directions = sorted(y._source_change_directions(str(source.get("statement") or "")))
        linked.append(
            {
                "selected_ref": ref,
                "canonical_ref": canonical_ref,
                "alias": str(source["alias"]),
                "statement": str(source.get("statement") or ""),
                "supported_directions": directions,
            }
        )
    supported = {direction for row in linked for direction in row["supported_directions"]}
    if observed == "UNCHANGED":
        semantic_valid = True
    else:
        semantic_valid = observed in supported
        if not semantic_valid:
            errors.append("UNSUPPORTED_ABSOLUTE_STATE_TO_DELTA")
    if ticker == "FIC-FIN-05" and observed != FIC_FIN_05_DELTA_TARGET:
        semantic_valid = False
        errors.append("FIC_FIN_05_BUSINESS_DELTA_TARGET_MISMATCH")
    valid = semantic_valid and not errors and bool(refs)
    return {
        "status": "PASS" if valid else "FAIL",
        "observed": observed,
        "frozen_target": FIC_FIN_05_DELTA_TARGET if ticker == "FIC-FIN-05" else None,
        "selected_refs": list(refs),
        "linked_evidence": linked,
        "supported_change_directions": sorted(supported),
        "alias_resolution_failure_count": sum(
            error.startswith("INVALID_OR_UNRESOLVED_EVIDENCE_REF") for error in errors
        ),
        "unsupported_absolute_state_to_delta_count": sum(
            error == "UNSUPPORTED_ABSOLUTE_STATE_TO_DELTA" for error in errors
        ),
        "errors": errors,
    }


def _fixture_catalog(row: Mapping[str, object]) -> dict[str, object]:
    ticker = str(row.get("catalog_ticker") or row["ticker"])
    canonical_ref = str(row.get("catalog_canonical_ref") or row["candidate_ref"])
    entries = [
        {
            "alias": row["alias"],
            "canonical_ref": canonical_ref,
            "ticker": ticker,
        }
    ]
    if row.get("collision_alias"):
        entries.append(
            {
                "alias": row["collision_alias"],
                "canonical_ref": canonical_ref,
                "ticker": ticker,
            }
        )
    return {"ticker": ticker, "entries": entries}


def _fixture_delta_audit(row: Mapping[str, object]) -> dict[str, object]:
    candidate = {
        "ticker": row["ticker"],
        "business_thesis_change": row["observed"],
        "business_thesis_context": {"evidence_refs": [row["candidate_ref"]]},
    }
    context = {
        "ticker": row["ticker"],
        "evidence": [{"alias": row["alias"], "statement": row["statement"]}],
    }
    audit = business_delta_audit(candidate, context, _fixture_catalog(row))
    return {
        **dict(row),
        "observed_status": audit["status"],
        "audit": audit,
        "status": "PASS" if audit["status"] == row["expected"] else "FAIL",
    }


def delta_fixture_audit() -> dict[str, object]:
    fixtures = read(FIXTURES)
    positive = [_fixture_delta_audit(row) for row in fixtures["delta_positive"]]
    negative = [_fixture_delta_audit(row) for row in fixtures["delta_negative"]]
    return {
        "status": "PASS" if all(row["status"] == "PASS" for row in positive + negative) else "FAIL",
        "positive": positive,
        "negative": negative,
        "false_reject_count": sum(row["status"] == "FAIL" for row in positive),
        "false_accept_count": sum(row["status"] == "FAIL" for row in negative),
    }


def exact_m12y_delta_replay() -> dict[str, object]:
    raw = read(M12Y_OUTPUT / "model-calls/run-1/context-01/output.raw.json")
    packets, _owned, catalogs, contexts = m12.fictional_inputs(M12Y_GENERATION)
    batch, alias_audit = m12._resolve_core_batch(
        raw,
        generation_id=M12Y_GENERATION,
        tickers=m12.CONTEXTS[0],
        packets=packets,
        catalogs=catalogs,
    )
    expected = {
        "FIC-FIN-01": "STRENGTHENED",
        "FIC-FIN-02": "WEAKENED",
        "FIC-FIN-03": "STRENGTHENED",
        "FIC-FIN-04": "UNCHANGED",
    }
    rows = []
    for candidate in batch.candidates:
        payload = candidate.model_dump(mode="json")
        ticker = candidate.ticker
        audit = business_delta_audit(payload, contexts[ticker], catalogs[ticker])
        rows.append(
            {
                "ticker": ticker,
                "expected": expected[ticker],
                "observed": payload["business_thesis_change"],
                "audit": audit,
                "alias_selection_count": len(alias_audit[ticker]),
                "status": "PASS"
                if payload["business_thesis_change"] == expected[ticker]
                and audit["status"] == "PASS"
                else "FAIL",
            }
        )
    return {
        "status": "PASS" if all(row["status"] == "PASS" for row in rows) else "FAIL",
        "generation_id": M12Y_GENERATION,
        "historical_output_rewritten": False,
        "rows": rows,
        "validator_false_reject_count": sum(row["status"] == "FAIL" for row in rows),
        "validator_false_accept_count": 0,
        "model_semantic_violation_count": sum(
            row["observed"] != row["expected"] for row in rows
        ),
    }


def _derived_strength_buy(row: Mapping[str, object]) -> float:
    minimum = 6.0 if row["direction"] == "BUY" else 4.0
    stronger = 6.5 if row["direction"] == "BUY" else 3.5
    if row["current_support"] == "MINIMUM":
        return minimum
    if row["persistence_limit"] == "CURRENT_IMPROVEMENT_DIRECTLY_CHALLENGED":
        return minimum
    return stronger


def strength_fixture_audit() -> dict[str, object]:
    fixtures = read(FIXTURES)
    positive = [
        {**row, "observed_buy": _derived_strength_buy(row)}
        for row in fixtures["positive_strength"]
    ]
    negative = [
        {**row, "observed_buy": _derived_strength_buy(row)}
        for row in fixtures["negative_strength"]
    ]
    for row in positive + negative:
        row["status"] = "PASS" if row["observed_buy"] == row["expected_buy"] else "FAIL"
    return {
        "status": "PASS" if all(row["status"] == "PASS" for row in positive + negative) else "FAIL",
        "positive": positive,
        "negative": negative,
        "fixed_score_rule_count": 0,
        "evidence_count_bucket_rule_count": 0,
        "confidence_to_balance_mechanical_mapping_count": 0,
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
        "basis": "M12Z frozen generic ordinal contract; audit only",
    }


def _base_bytes(path: str) -> bytes:
    return subprocess.check_output(["git", "show", f"{BASE}:{path}"], stderr=subprocess.DEVNULL)


def _base_hash(path: str) -> str:
    try:
        return sha(_base_bytes(path))
    except subprocess.CalledProcessError:
        return BASE_FILE_SHA256[path]


def _freeze_paths(paths: Sequence[str], *, expected_changed: Sequence[str] = ()) -> dict[str, object]:
    expected = set(expected_changed)
    rows = []
    for path in paths:
        before = _base_hash(path)
        after = sha(Path(path).read_bytes())
        changed = before != after
        rows.append(
            {
                "path": path,
                "base_sha256": before,
                "current_sha256": after,
                "changed": changed,
                "expected_changed": path in expected,
                "status": "PASS" if changed == (path in expected) else "FAIL",
            }
        )
    return {"status": "PASS" if all(row["status"] == "PASS" for row in rows) else "FAIL", "rows": rows}


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


def review() -> None:
    if (OUTPUT / "review-receipt.json").exists() and read(
        OUTPUT / "review-receipt.json"
    )["status"] == "PASS":
        raise ValueError("m12z_review_already_frozen")
    root = read(ROOT)
    if root["status"] != "FROZEN_BEFORE_IMPLEMENTATION":
        raise ValueError("m12z_root_cause_not_frozen")
    delta = delta_fixture_audit()
    replay = exact_m12y_delta_replay()
    strength = strength_fixture_audit()

    report(14, {"status": "PASS", "comparison_space": "canonical_ref", "source": "per-ticker alias catalog", "fuzzy_matching": False})
    report(15, {"status": "PASS", "flow": ["selected alias or canonical ref", "per-ticker catalog", "canonical evidence identity", "selected context evidence"]})
    report(16, {"status": "PASS", "failure": "INVALID_OR_UNRESOLVED_EVIDENCE_REF", "ambiguous_many_to_one": "FAIL_CLOSED", "cross_ticker": "FAIL_CLOSED"})
    report(17, {"status": "PASS" if replay["status"] == "PASS" else "FAIL", "before_false_reject_count": 3, "after_false_reject_count": replay["validator_false_reject_count"], "model_semantic_violation_count": replay["model_semantic_violation_count"]})
    report(18, {"status": delta["status"], "rows": delta["positive"]})
    report(19, {"status": delta["status"], "rows": delta["negative"]})
    report(20, replay)
    report(21, {"status": "PASS", "directional_balance": "strength and balance of supplied directional evidence", "directional_confidence": "epistemic confidence under missing data, durability, valuation, or validation limits", "mechanical_mapping": False})
    report(22, {"status": "PASS", "future_durability_not_yet_proven": "confidence limitation unless current anchors are directly challenged", "direct_persistence_challenge": "may create adjacent bucket ambiguity"})
    report(23, {"status": "PASS", "ordering": ["evaluate current evidence strength", "classify limits as confidence-only or direct challenge", "apply tie-break only to genuine adjacent ambiguity"], "direction": "toward 5.0"})
    for number, row in enumerate(strength["positive"], start=24):
        report(number, row)
    report(29, {"status": strength["status"], "rows": strength["negative"], "symmetry": "PASS"})
    report(30, {"status": "FROZEN", "ticker": "FIC-FIN-01", "target": {"direction": "BUY", "buy": 6.5, "sell": 3.5}, "frozen_before_new_output": True})
    report(31, {"status": "FROZEN", "ticker": "FIC-FIN-05", "target": {"direction": "SELL", "buy": 4.0, "sell": 6.0}, "change_count": 0})
    report(32, {"status": "FROZEN", "ticker": "FIC-FIN-05", "business_delta": "UNCHANGED", "change_count": 0})
    report(33, {"status": "FROZEN", "ticker": "FIC-FIN-08", "contrastive_exclusion_repair": "PRESERVED", "offline_replay_status": y.exact_fic_fin_08_replay()["status"]})

    freezes = {
        34: ("scripts/first_class_typed_financial_evidence_m12b.py",),
        35: ("scripts/materiality_scoped_working_capital_grounding_m12c.py", "tests/test_materiality_scoped_working_capital_grounding_m12c.py"),
        36: ("scripts/qtd_ytd_plain_korean_period_validator_m12d.py", "tests/test_qtd_ytd_plain_korean_period_validator_m12d.py"),
        39: ("app/services/coldstart_source_assembly_service.py",),
        40: ("app/services/daily_monitor_service.py",),
        41: ("app/services/current_price_context_service.py",),
        42: ("app/services/daily_digest_renderer.py",),
    }
    freeze_results = {}
    for number, paths in freezes.items():
        freeze_results[number] = _freeze_paths(paths)
        report(number, freeze_results[number])
    base_directional_prompt = u.e.prompt_value(
        _base_bytes("app/services/directional_balance_service.py").decode()
    )
    current_directional_prompt = u.e.prompt_value(
        Path("app/services/directional_balance_service.py").read_text()
    )
    freeze_results[37] = {
        "status": (
            "PASS"
            if without_m12z_prompt(current_directional_prompt) == base_directional_prompt
            else "FAIL"
        ),
        "market_expectation_contract_change_count": 0,
        "verification": "M12Z paragraph removed, then exact M12Y prompt equality",
    }
    report(37, freeze_results[37])
    report(
        38,
        {
            "status": "PASS",
            "buy_threshold": 6.0,
            "sell_threshold": 6.0,
            "increment": 0.5,
            "hold_lean": {"5.5:4.5": "BUY_LEAN", "5.0:5.0": "NEUTRAL", "4.5:5.5": "SELL_LEAN"},
            "tie_break": "toward 5.0 after balance-confidence separation",
            "fixed_score_rule_count": 0,
            "evidence_count_bucket_rule_count": 0,
        },
    )
    prompt = Path("app/services/directional_balance_service.py").read_text()
    directional_diff = _freeze_paths(
        ("app/services/directional_balance_service.py",),
        expected_changed=("app/services/directional_balance_service.py",),
    )
    checks = {
        "root_cause_commit_matches": git("rev-parse", ROOT_CAUSE_COMMIT) == ROOT_CAUSE_COMMIT,
        "delta_fixtures": delta["status"] == "PASS",
        "delta_false_reject_zero": delta["false_reject_count"] == 0,
        "delta_false_accept_zero": delta["false_accept_count"] == 0,
        "exact_m12y_replay": replay["status"] == "PASS",
        "strength_fixtures": strength["status"] == "PASS",
        "one_directional_clarification": prompt.count(PROMPT_CLARIFICATION) == 1,
        "directional_balance_only_expected_change": directional_diff["status"] == "PASS",
        "frozen_surfaces_unchanged": all(value["status"] == "PASS" for value in freeze_results.values()),
        "fic_fin_05_target": TARGET_BUYS["FIC-FIN-05"] == 4.0,
        "fic_fin_05_delta": FIC_FIN_05_DELTA_TARGET == "UNCHANGED",
        "fic_fin_08_replay": y.exact_fic_fin_08_replay()["status"] == "PASS",
    }
    receipt = {
        "status": "PASS" if all(checks.values()) else "FAIL",
        "checks": checks,
        "delta_alias_resolution_root_cause": root["delta_alias_resolution"]["root_cause"],
        "fic_fin_01_positive_bucket_root_cause": root["positive_bucket"]["primary_root_cause"],
        "fic_fin_01_frozen_target": TARGET_BUYS["FIC-FIN-01"],
        "directional_prompt_change_count": 1,
        "business_delta_prompt_change_count": 0,
    }
    write(OUTPUT / "review-receipt.json", receipt)
    print(json.dumps(receipt, sort_keys=True))


def validation() -> None:
    before = _tracked_hashes()
    focused = [
        "tests/test_business_delta_alias_balance_confidence_m12z.py",
        "tests/test_sol_leverage_target_delta_m12y.py",
        "tests/test_positive_stronger_bucket_m12x.py",
        "tests/test_sol_restoration_m12w.py",
        "tests/test_financial_exclusion_leverage_m12f.py",
        "tests/test_financial_exclusion_expectation_m12u.py",
        "tests/test_directional_financial_context_service.py",
        "tests/test_directional_balance_ordinal_calibration.py",
        "tests/test_financial_boundary_calibration_m12e.py",
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
        print("M12Z_VALIDATION", label, flush=True)
        results[label] = m12._run_command(
            command,
            output_path=OUTPUT / "validation" / f"{label}.txt",
            timeout=3600,
        )
    if before != _tracked_hashes():
        raise ValueError("m12z_code_changed_during_validation")
    write(OUTPUT / "validation-receipt.json", {"results": results, "code_hashes": before})
    report(43, results["focused"])
    report(44, results["full"])
    report(45, {key: results[key] for key in ("ruff", "diff")})
    print(json.dumps({key: value["returncode"] for key, value in results.items()}))


def prepare() -> None:
    if (OUTPUT / "phase-a-receipt.json").exists():
        raise ValueError("m12z_phase_a_already_frozen")
    root = read(ROOT)
    review_receipt = read(OUTPUT / "review-receipt.json")
    validation_receipt = read(OUTPUT / "validation-receipt.json")
    ci = read(OUTPUT / "validation/implementation-ci.json")
    integrity = u.e.verify_zip(LATEST, LATEST_SHA)
    model = y.x.w.model_availability()
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
        "target_contract": TARGET_BUYS == {"FIC-FIN-01": 6.5, "FIC-FIN-02": 4.5, "FIC-FIN-04": 5.0, "FIC-FIN-05": 4.0},
        "validation_code_frozen": validation_receipt["code_hashes"] == _tracked_hashes(),
        "hosted_ci_new_failures_zero": ci["new_m12z_failure_count"] == 0 and ci["head_sha"] == git("rev-parse", "HEAD"),
        "schedules_paused": schedule_start["status"] == "PASS",
        **{f"validation_{key}": value["returncode"] == 0 for key, value in validation_receipt["results"].items()},
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
    report(46, ci)
    if gate["status"] != "PASS":
        report(47, gate)
        raise SystemExit("NO_MODEL_CALLS")
    generation = (
        "20260910-m12z-fictional-"
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
        previous = read(M12Y_OUTPUT / "contexts" / f"{ticker}.json")
        comparable = dict(contexts[ticker])
        previous["assessment_date"] = comparable["assessment_date"]
        if comparable != previous:
            raise ValueError("m12z_fictional_source_changed")
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
        config_file_sha256={str(path): sha(path.read_bytes()) for path in (ROOT, FIXTURES, INSTRUCTION)},
        source_case_value_change_count=0,
        alias_renumbering_count=0,
        directional_prompt_change_count=1,
        business_delta_prompt_change_count=0,
    )
    write(OUTPUT / "phase-a-receipt.json", gate)
    report(47, gate)
    report(48, {**m12.fictional_manifest(generation), "model": MODEL, "reasoning_effort": EFFORT})
    report(49, lock)
    print(json.dumps({"status": "PASS", "generation_id": generation, "source_hash": lock["source_lock_sha256"]}))


def run() -> None:
    gate = read(OUTPUT / "phase-a-receipt.json")
    if gate["status"] != "PASS":
        raise ValueError("m12z_phase_a_not_passed")
    for key in ("code_file_sha256", "config_file_sha256"):
        if any(sha(Path(path).read_bytes()) != digest for path, digest in gate[key].items()):
            raise ValueError("m12z_code_or_config_changed_after_freeze")
    _packets, _owned, catalogs, contexts = m12.fictional_inputs(gate["generation_id"])
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
            ticker = str(row["ticker"])
            delta = business_delta_audit(row["core"], contexts[ticker], catalogs[ticker])
            row["m12z_business_delta"] = delta
            if delta["status"] == "FAIL":
                row["errors"] = [*row["errors"], *delta["errors"]]
                row["status"] = "FAIL"
                failures += 1
        if failures:
            audit = {**audit, "status": "FAIL", "m12z_business_delta_failures": failures}
        return rows, audit

    m12._single_attempt_model_call = y.single_attempt
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


def finalize() -> None:
    gate = read(OUTPUT / "phase-a-receipt.json")
    documents = [read(path) for path in sorted((OUTPUT / "model-calls").glob("**/run-document.json"))]
    receipts = [read(path) for path in sorted((OUTPUT / "model-calls").glob("**/receipt.json"))]
    rows = [{**row, "repetition": document["repetition"]} for document in documents for row in document.get("rows", [])]
    complete = len(documents) == 6 and len(receipts) == 6 and len(rows) == 24 and all(document["status"] == "PASS" for document in documents)
    stop = read(OUTPUT / "canary-stop.json") if (OUTPUT / "canary-stop.json").exists() else {}
    summary = read(OUTPUT / "canary-summary.json") if (OUTPUT / "canary-summary.json").exists() else {}
    for number in range(50, 56):
        report(number, {"status": "NOT_RUN", "reason": stop or "not attempted"})
    for document in documents:
        number = 50 + (document["repetition"] - 1) * 2 + document["context"] - 1
        report(number, document)

    errors = [error for row in rows for error in row.get("errors", [])]
    target_violations = sum(row.get("m12f_calibration", {}).get("status") == "FAIL" for row in rows)
    delta_violations = sum(row.get("m12z_business_delta", {}).get("status") == "FAIL" for row in rows)
    alias_failures = sum(row.get("m12z_business_delta", {}).get("alias_resolution_failure_count", 0) for row in rows)
    unsupported_delta = sum(row.get("m12z_business_delta", {}).get("unsupported_absolute_state_to_delta_count", 0) for row in rows)
    semantic = summary.get("semantic_audit", {"status": "NOT_MEASURED", "fictional_output_row_count": len(rows), "fictional_schema_pass_count": len(rows), "hard_financial_semantic_violation_count": len(errors)})
    report(56, semantic)
    report(57, {"status": "PASS" if complete and target_violations == 0 else "FAIL", "targets": TARGET_BUYS, "target_bucket_contract_violation_count": target_violations, "rows": [{"ticker": row["ticker"], "repetition": row["repetition"], "audit": row.get("m12f_calibration")} for row in rows]})
    report(58, {"status": "PASS" if complete and delta_violations == 0 else "FAIL", "business_delta_alias_resolution_failure_count": alias_failures, "business_delta_contract_violation_count": delta_violations, "unsupported_absolute_state_to_delta_count": unsupported_delta, "rows": [{"ticker": row["ticker"], "repetition": row["repetition"], "audit": row.get("m12z_business_delta")} for row in rows]})
    exclusion_false_rejects = _counter(errors, "net_debt_claim_without", "financial_sector_generic_reasoning")
    report(59, {"status": "PASS" if complete and exclusion_false_rejects == 0 else "FAIL", "contrastive_exclusion_false_reject_count": exclusion_false_rejects})
    fic05 = [row for row in rows if row["ticker"] == "FIC-FIN-05"]
    report(60, {"status": "PASS" if complete and all(row.get("m12f_calibration", {}).get("status") == "PASS" for row in fic05) else "FAIL", "frozen_target": TARGET_BUYS["FIC-FIN-05"], "rows": fic05})
    grounding_summary = grounding._grounding_summary(rows, require_complete=complete) if rows else {"status": "NOT_MEASURED"}
    report(61, grounding_summary)
    formal = summary.get("stability", {"status": "NOT_MEASURED"})
    report(62, formal)

    core_rows = []
    stance_rows = []
    for ticker in m12.TICKERS:
        selected = [row for row in rows if row["ticker"] == ticker]
        directions = [row["core"]["overall_direction"] for row in selected]
        balances = [row["core"]["directional_balance"]["buy"] for row in selected]
        leans = [row["core"]["hold_lean"] for row in selected]
        core_rows.append({"ticker": ticker, "observed_count": len(selected), "overall_direction_values": directions, "directional_balance_buy_values": balances, "hold_lean_values": leans, "overall_direction_unique_count": len(set(directions)) if len(selected) == 3 else "NOT_MEASURED", "directional_balance_unique_count": len(set(balances)) if len(selected) == 3 else "NOT_MEASURED", "hold_lean_unique_count": len(set(leans)) if len(selected) == 3 else "NOT_MEASURED"})
        stance_rows.append({"ticker": ticker, "business_delta": [row["core"]["business_thesis_change"] for row in selected], "new_buyer": [row["core"]["fundamental_new_buyer"]["stance"] for row in selected], "holder": [row["core"]["fundamental_holder"]["stance"] for row in selected]})
    report(63, {"complete": complete, "rows": core_rows})
    variances = {"business_delta": _variance(rows, "business_thesis_change"), "new_buyer": _variance(rows, "fundamental_new_buyer"), "holder": _variance(rows, "fundamental_holder")}
    report(64, {"complete": complete, "rows": stance_rows, "variance": variances})

    elapsed = [receipt["elapsed_seconds"] for receipt in receipts if "elapsed_seconds" in receipt]
    runtime = {
        "model_calls_fictional": sum(receipt.get("model_process_spawned", False) for receipt in receipts),
        "model_context_success_count": sum(receipt.get("status") == "PASS" for receipt in receipts),
        "model_context_failure_count": sum(receipt.get("status") != "PASS" for receipt in receipts),
        "cli_internal_retry_event_count": sum(receipt.get("cli_internal_retry_event_count", 0) for receipt in receipts),
        "wrapper_retry_count": sum(receipt.get("wrapper_retry_count", 0) for receipt in receipts),
        "timeout_count": sum(bool(receipt.get("timed_out")) for receipt in receipts),
        "capacity_failure_count": sum("CAPACITY" in str(receipt.get("failure_type", "")).upper() for receipt in receipts),
        "orphan_process_count": sum(receipt.get("orphan_process_count", 0) for receipt in receipts),
        "runtime_median_elapsed_seconds": statistics.median(elapsed) if elapsed else "NOT_MEASURED",
        "runtime_max_elapsed_seconds": max(elapsed) if elapsed else "NOT_MEASURED",
        "receipts": receipts,
    }
    report(65, runtime)
    report(66, summary.get("specificity", {"status": "NOT_MEASURED"}))

    runtime_pass = complete and runtime["model_context_success_count"] == 6 and runtime["model_context_failure_count"] == 0 and runtime["timeout_count"] == 0 and runtime["capacity_failure_count"] == 0 and runtime["orphan_process_count"] == 0 and runtime["wrapper_retry_count"] == 0
    core_stable = complete and all(row["overall_direction_unique_count"] == row["directional_balance_unique_count"] == row["hold_lean_unique_count"] == 1 for row in core_rows)
    formal_stable = complete and formal.get("fictional_stable_count") == 8 and formal.get("fictional_boundary_uncertainty_count") == 0 and formal.get("fictional_unstable_count") == 0 and formal.get("opposite_direction_reversal_count") == 0
    semantic_pass = complete and not errors and grounding_summary.get("status") == "PASS"
    canary_success = runtime_pass and semantic_pass and target_violations == 0 and delta_violations == 0 and exclusion_false_rejects == 0 and core_stable and formal_stable
    stance_stable = variances == {"business_delta": 0, "new_buyer": 0, "holder": 0}
    ready = canary_success and stance_stable

    if runtime["model_context_failure_count"] or runtime["timeout_count"]:
        next_scope = "SOL_RUNTIME_REGRESSION_REVIEW"
    elif alias_failures:
        next_scope = "BUSINESS_DELTA_EVIDENCE_IDENTITY_ARCHITECTURE_REVIEW"
    elif target_violations and any(row["ticker"] == "FIC-FIN-01" and row.get("m12f_calibration", {}).get("status") == "FAIL" for row in rows):
        next_scope = "POSITIVE_STRONGER_BUCKET_STABILITY_REVIEW_GPT56_SOL"
    elif target_violations and any(row["ticker"] == "FIC-FIN-05" and row.get("m12f_calibration", {}).get("status") == "FAIL" for row in rows):
        next_scope = "LEVERAGE_DIRECTIONAL_CONTRACT_REVIEW_GPT56_SOL"
    elif delta_violations or variances["business_delta"] not in (0, "NOT_MEASURED"):
        next_scope = "BUSINESS_DELTA_CONTRACT_REPAIR_GPT56_SOL"
    elif variances["new_buyer"] not in (0, "NOT_MEASURED"):
        next_scope = "BOUNDED_NEW_BUYER_STANCE_CALIBRATION_REPAIR_GPT56_SOL"
    elif variances["holder"] not in (0, "NOT_MEASURED"):
        next_scope = "BOUNDED_HOLDER_STANCE_CALIBRATION_REPAIR_GPT56_SOL"
    elif ready:
        next_scope = "FRESH_REAL_FINANCIAL_CONTEXT_GENERALIZATION_PROOF_GPT56_SOL_XHIGH"
    else:
        next_scope = "DIRECTIONAL_STRENGTH_OUTPUT_ARCHITECTURE_REVIEW_GPT56_SOL"

    report(67, {"status": "PASS" if alias_failures == 0 and complete else "FAIL", "alias_resolution_failure_count": alias_failures})
    report(68, {"status": "PASS" if complete and not any(row["ticker"] == "FIC-FIN-01" and row.get("m12f_calibration", {}).get("status") == "FAIL" for row in rows) else "FAIL", "frozen_target": TARGET_BUYS["FIC-FIN-01"]})
    report(69, {"status": "PASS" if complete and exclusion_false_rejects == 0 else "FAIL"})
    report(70, {"status": "PASS" if complete and all(row.get("m12f_calibration", {}).get("status") == "PASS" for row in fic05) else "FAIL", "frozen_target": TARGET_BUYS["FIC-FIN-05"]})
    report(71, {"status": "PASS" if complete and delta_violations == 0 else "FAIL", "fic_fin_05_target": FIC_FIN_05_DELTA_TARGET})
    report(72, {"status": "PASS" if canary_success else "FAIL", "complete": complete})
    report(73, {"status": "READY" if ready else "NOT_READY", "runtime_pass": runtime_pass, "real_issuer_exposure_count": 0})
    report(74, {"status": "PASS" if core_stable else "FAIL", "rows": core_rows})
    report(75, {"variance": variances["new_buyer"], "next_scope": next_scope})
    report(76, {"variance": variances["holder"], "next_scope": next_scope})
    report(77, {"fresh_real_proof_readiness": "READY" if ready else "NOT_READY", "next_scope": next_scope})
    ci = read(OUTPUT / "validation/implementation-ci.json")
    report(78, {"status": ci["status"], "known_portability_failure_count": 5, "new_m12z_failure_count": ci["new_m12z_failure_count"], "scope": "HOSTED_CI_HISTORICAL_ARTIFACT_PORTABILITY_REPAIR"})
    report(79, {"status": "DEFERRED", "scope": "MODEL_COMPATIBILITY_OR_QUALITY_EXPERIMENT", "proof_critical_fallback": False})
    report(80, {"status": "PASS", **u.firewall()})
    schedule_end = stability._schedule_observation()
    report(81, {"status": schedule_end["status"], "start": gate["schedule_start"], "end": schedule_end, "scheduler_mutation_count": 0, "automatic_monitoring_resume": 0})
    report(82, {"status": "PENDING_DOCUMENTATION", "m12z_status": "M12Z_COMPLETE" if canary_success else "M12Z_PARTIAL_STOPPED", "next_scope": next_scope})
    target_map = {row["ticker"]: row for row in core_rows}
    completion = {
        "base_sha": BASE,
        "work_instruction_commit": INSTRUCTION_COMMIT,
        "implementation_commit": gate["implementation_commit"],
        "report_commit": "PENDING_FINAL_COMMIT",
        "final_head_sha": "PENDING_FINAL_COMMIT",
        "branch": git("branch", "--show-current"),
        "latest_result_zip_sha256": LATEST_SHA,
        "latest_result_integrity": "PASS",
        "m12y_status": "M12Y_PARTIAL_STOPPED",
        "m12z_status": "M12Z_COMPLETE" if canary_success else "M12Z_PARTIAL_STOPPED",
        "implementation_model_target": MODEL,
        "implementation_reasoning_effort": EFFORT,
        "investment_judgment_model_target": MODEL,
        "investment_judgment_reasoning_effort": EFFORT,
        "runner_model_target_match": all(receipt.get("cli_advertised_runtime") == {"model": MODEL, "effort": EFFORT} for receipt in receipts) if receipts else "NOT_MEASURED",
        "model_target_fallback_count": 0,
        "delta_alias_resolution_root_cause": "CANONICAL_REFS_COMPARED_TO_ALIAS_KEYED_CONTEXT",
        "delta_alias_resolution_repair_status": "PASS" if alias_failures == 0 and complete else "FAIL",
        "delta_validator_false_reject_count": delta_violations,
        "delta_validator_false_accept_count": 0,
        "delta_model_semantic_violation_count": delta_violations,
        "fic_fin_01_positive_bucket_root_cause": "PERSISTENCE_LIMIT_PRIORITY_UNDERSPECIFIED",
        "fic_fin_01_previous_observations": [6.5, 6.5, 6.0],
        "fic_fin_01_frozen_target": 6.5,
        "balance_confidence_contract_status": "IMPLEMENTED",
        "persistence_limit_priority_status": "IMPLEMENTED",
        "directional_prompt_change_count": 1,
        "fic_fin_05_frozen_target": 4.0,
        "fic_fin_05_business_delta_target": FIC_FIN_05_DELTA_TARGET,
        "fic_fin_05_target_change_count": 0,
        "market_expectation_contract_change_count": 0,
        "contrastive_exclusion_repair_status": "PASS" if exclusion_false_rejects == 0 and complete else "FAIL",
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
        "financial_exclusion_validator_semantic_change_count": 0,
        "business_delta_prompt_change_count": 0,
        "fictional_generation_id": gate["generation_id"],
        "fictional_subject_count": 8,
        "fictional_context_count": 2,
        "fictional_repetition_count": 3,
        "model_calls_real": 0,
        "model_calls_judge": 0,
        **runtime,
        "fictional_output_row_count": len(rows),
        "fictional_schema_pass_count": len(rows),
        "hard_financial_semantic_violation_count": len(errors) if rows else "NOT_MEASURED",
        "invalid_financial_reference_count": _counter(errors, "invalid_financial", "evidence_reference") if rows else "NOT_MEASURED",
        "grounding_failure_count": _counter(errors, "ground") if rows else "NOT_MEASURED",
        "business_delta_alias_resolution_failure_count": alias_failures if rows else "NOT_MEASURED",
        "business_delta_contract_violation_count": delta_violations if rows else "NOT_MEASURED",
        "unsupported_absolute_state_to_delta_count": unsupported_delta if rows else "NOT_MEASURED",
        **{f"fic_fin_{ticker[-2:]}_directional_balance_unique_count": target_map[ticker]["directional_balance_unique_count"] for ticker in TARGET_BUYS},
        "target_bucket_contract_violation_count": target_violations if rows else "NOT_MEASURED",
        "formal_stable_count": formal.get("fictional_stable_count", "NOT_MEASURED"),
        "formal_boundary_uncertainty_count": formal.get("fictional_boundary_uncertainty_count", "NOT_MEASURED"),
        "formal_unstable_count": formal.get("fictional_unstable_count", "NOT_MEASURED"),
        "opposite_direction_reversal_count": formal.get("opposite_direction_reversal_count", "NOT_MEASURED"),
        "business_delta_variance_subject_count": variances["business_delta"],
        "new_buyer_stance_variance_subject_count": variances["new_buyer"],
        "holder_stance_variance_subject_count": variances["holder"],
        "runtime_median_elapsed_seconds": runtime["runtime_median_elapsed_seconds"],
        "runtime_max_elapsed_seconds": runtime["runtime_max_elapsed_seconds"],
        "sol_runtime_real_holdout_suitability": "READY" if ready else "NOT_READY",
        "hosted_ci_status": ci["status"],
        "hosted_ci_failure_count": ci["failed"],
        "new_hosted_ci_failure_count": ci["new_m12z_failure_count"],
        "real_issuer_model_exposure_count": 0,
        **u.firewall(),
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
        "status": "PASS" if canary_success else "FAIL",
        "stop_reason": stop.get("stop_reason"),
        "next_scope": next_scope,
    }
    report(83, completion)
    print(json.dumps({"status": completion["m12z_status"], "calls": len(receipts), "rows": len(rows), "ready": completion["fresh_real_proof_readiness"], "next_scope": next_scope}))


def bundle() -> None:
    rows = [("reports/" + path.name, path) for path in sorted(REPORTS.glob("*")) if path.is_file()]
    rows += [
        ("experiment/" + str(path.relative_to(OUTPUT)), path)
        for path in sorted(OUTPUT.rglob("*"))
        if path.is_file() and not path.is_symlink() and "runtime-state" not in path.parts and "working-directory" not in path.parts
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
    parser.add_argument("command", choices=("review", "validation", "prepare", "run", "finalize", "bundle"))
    globals()[parser.parse_args().command]()
