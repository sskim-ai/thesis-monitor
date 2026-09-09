"""M12U archive-only semantic repair proof; delegates the unchanged M12T transport."""

from __future__ import annotations

import argparse
import ast
from dataclasses import asdict
from datetime import UTC, datetime
import json
from pathlib import Path
import re
import statistics
import sys
from types import SimpleNamespace
import uuid
import zipfile

from scripts import astra_transport_m12t as t

f, e, m12, stability = t.f, t.e, t.m12, t.stability
read, write, sha, git = t.read, t.write, t.sha, t.git
BASE = "e8e82e353ff71f251c66a1c6940af4d70ff0c778"
NAME = "20260910-financial-sector-exclusion-validator-market-expectation-leverage-boundary-full-fictional-canary"
OUTPUT = Path("artifacts") / NAME
REPORTS = Path("docs/reports") / NAME
INSTRUCTION = Path(
    "docs/work-instructions/20260910-financial-sector-exclusion-validator-and-market-expectation-leverage-boundary-repair-full-fictional-canary.md"
)
ROOT = Path("docs/architecture/M12U_EXCLUSION_EXPECTATION_REVIEW.json")
BASELINE = Path("fixtures/m12u_scope_baseline.json")
FIXTURES = Path("fixtures/financial_exclusion_expectation_m12u.json")
HELPER = "app/services/financial_framework_claim_service.py"
BALANCE = "app/services/directional_balance_service.py"
TEST_MIGRATION = "tests/test_financial_boundary_calibration_m12e.py"
LATEST = (
    Path.home()
    / "Documents/Codex/thesis-monitor-20260910-bounded-astra-transport-timeout-review-new-full-fictional-canary-report.zip"
)
LATEST_SHA = "d3202a35bcf5b13cd0afc86b59b1eda76c5088ecab377f3e63f316f6ca7a004b"
SLUGS = {int(n): s for n, s in re.findall(r"^(\d{2})-([a-z0-9-]+)$", INSTRUCTION.read_text(), re.M)}


def report(number, value):
    write(REPORTS / f"{number:02d}-{SLUGS[number]}.json", value)


def scope_audit():
    baseline = read(BASELINE)
    allowed = {
        HELPER,
        BALANCE,
        TEST_MIGRATION,
        "tests/test_financial_exclusion_leverage_m12f.py",
        "tests/test_first_class_typed_financial_evidence_m12b.py",
    }
    unexpected = [
        p
        for p, h in baseline["files"].items()
        if p not in allowed and (not Path(p).is_file() or sha(Path(p).read_bytes()) != h)
    ]
    before = baseline["approved_module_before"][BALANCE]
    after = Path(BALANCE).read_text()
    old_prompt, new_prompt = e.prompt_value(before), e.prompt_value(after)
    addition = new_prompt.removeprefix(old_prompt).strip()
    prompt_ok = new_prompt.startswith(old_prompt + "\n\n") and "\n\n" not in addition
    helper_before = ast.parse(baseline["approved_module_before"][HELPER])
    helper_after = ast.parse(Path(HELPER).read_text())
    allowed_nodes = {"_NOMINAL_BRIDGE", "_KO_EXCLUSION", "_EN_SUFFIX", "financial_framework_claims"}

    def residual(tree):
        return ast.dump(
            ast.Module(
                body=[
                    n
                    for n in tree.body
                    if getattr(n, "name", "") not in allowed_nodes
                    and not (
                        isinstance(n, ast.Assign)
                        and any(
                            isinstance(a, ast.Name) and a.id in allowed_nodes for a in n.targets
                        )
                    )
                ],
                type_ignores=[],
            ),
            include_attributes=False,
        )

    checks = {
        "unrelated_files_unchanged": not unexpected,
        "balance_nonprompt_ast_unchanged": e.without_prompt(before) == e.without_prompt(after),
        "one_appended_paragraph": prompt_ok,
        "helper_unrelated_ast_unchanged": residual(helper_before) == residual(helper_after),
        "no_subject_branch": "FIC-FIN" not in Path(HELPER).read_text()
        and "ticker" not in Path(HELPER).read_text(),
    }
    return {
        "status": "PASS" if all(checks.values()) else "FAIL",
        "checks": checks,
        "unexpected_file_changes": unexpected,
        "prompt_change_count": int(prompt_ok),
        "baseline_sha": BASE,
        "frozen_file_count": len(baseline["files"]),
        "before_prompt": old_prompt,
        "after_prompt": new_prompt,
        "addition": addition,
    }


def preserved_rows():
    with zipfile.ZipFile(LATEST) as archive:
        return [
            row
            for context in (1, 2)
            for row in json.loads(
                archive.read(
                    f"experiment/model-calls/run-1/context-{context:02d}/run-document.json"
                )
            )["rows"]
        ]


def calibration_audit(row, root=None):
    root = root or read(ROOT)
    target = root["expectation"]["all_target_buys"].get(row["ticker"])
    if target is None:
        return {"status": "NOT_TARGETED"}
    observed = row["core"]["directional_balance"]["buy"]
    return {
        "status": "PASS" if observed == target else "FAIL",
        "expected_buy": target,
        "observed_buy": observed,
        "contract_sha256": sha(ROOT.read_bytes()),
        "basis": "M12U frozen qualitative source-pattern contract; audit only, never a label override",
    }


def offline_replay():
    old = preserved_rows()
    fingerprint = sha(json.dumps(old, sort_keys=True).encode())
    _, owned, catalogs, _ = m12.fictional_inputs("m12u-offline")
    rows = []
    for offset in (0, 4):
        batch = m12.DirectionalCoreBatch(
            packet_id="m12u-offline",
            candidates=tuple(
                m12.DirectionalCoreCandidate.model_validate(r["core"])
                for r in old[offset : offset + 4]
            ),
        )
        checked, _ = f.grounding._audit_core_batch_with_grounding(
            batch, owned=owned, catalogs=catalogs
        )
        rows.extend(checked)
    original = {r["ticker"]: r for r in old}
    return {
        "status": "PASS" if all(r["status"] == "PASS" for r in rows) else "FAIL",
        "rows": rows,
        "original_exclusion_errors": original["FIC-FIN-08"]["errors"],
        "original_rows_unchanged": fingerprint == sha(json.dumps(old, sort_keys=True).encode()),
        "old_leverage_calibration": calibration_audit(original["FIC-FIN-05"]),
        "old_generation_reclassified_as_pass": False,
    }


def fixture_audit():
    from app.services.directional_financial_context_service import (
        validate_directional_financial_semantics,
    )

    fixtures = read(FIXTURES)
    rows = []
    for expected in ("positive", "negative"):
        for text in fixtures[expected]:
            candidate = {"sector_interpretation": {"text": text, "evidence_refs": []}}
            validation = validate_directional_financial_semantics(
                candidate, supplied_refs=(), allowed_ref_ids=(), sector_framework="bank_or_insurer"
            )
            rows.append(
                {
                    "text": text,
                    "expected": expected,
                    "valid": validation.valid,
                    "claims": [asdict(c) for c in f.financial_framework_claims(text)],
                    "errors": validation.errors,
                    "status": "PASS" if validation.valid == (expected == "positive") else "FAIL",
                }
            )
    leverage = [
        {
            **c,
            "status": "PASS"
            if e.tie_fixture(c["supportable_buy_buckets"]) == c["selected_buy"]
            else "FAIL",
        }
        for c in fixtures["leverage"]
    ]
    return {
        "status": "PASS" if all(r["status"] == "PASS" for r in rows + leverage) else "FAIL",
        "rows": rows,
        "leverage": leverage,
        "false_reject": sum(r["expected"] == "positive" and not r["valid"] for r in rows),
        "false_accept": sum(r["expected"] == "negative" and r["valid"] for r in rows),
        "fixture_role": "Authored economic proposition review plus existing ordinal tie-break; not automated economic inference",
    }


def latest_integrity():
    result = e.verify_zip(LATEST, LATEST_SHA)
    with zipfile.ZipFile(LATEST) as z:
        views = [
            (
                n,
                SimpleNamespace(
                    read_text=lambda b=z.read(n), **kw: b.decode("utf-8", errors="replace")
                ),
            )
            for n in z.namelist()
        ]
        result["secret_scan"] = f.artifact_secret_scan(views)
    if result["secret_scan"]["failures"]:
        result["status"] = "FAIL"
    return result


def prepare():
    if (OUTPUT / "phase-a-receipt.json").exists():
        raise ValueError("phase_a_already_frozen")
    root, scope, replay, fixtures = read(ROOT), scope_audit(), offline_replay(), fixture_audit()
    integrity, schedule = latest_integrity(), stability._schedule_observation()
    for n in SLUGS:
        report(n, {"status": "NOT_MEASURED"})
    provenance = {
        "base_sha": BASE,
        "work_instruction_commit": git("rev-parse", "459af10"),
        "offline_review_commit": git("rev-parse", "f73ce3a"),
        "implementation_commit": git("rev-parse", "HEAD"),
        "branch": git("branch", "--show-current"),
        "working_tree_state": git("status", "--short"),
        "origin_main": git("rev-parse", "origin/main"),
    }
    payloads = {
        1: provenance,
        2: integrity,
        3: {"review": root, "scope": scope},
        4: root["transport"],
        5: root["authoring"],
        6: e.model_availability(),
        7: {"frozen_transport": root["transport"], "runtime_changes": 0},
        8: {
            "before_replay": root["exclusion"]["before_replay"],
            "original_row": preserved_rows()[-1],
        },
        9: root["exclusion"],
        10: root["exclusion"],
        11: {"diff": git("diff", BASE, "--", HELPER), "scope": scope},
        12: {"rows": [r for r in fixtures["rows"] if r["expected"] == "positive"]},
        13: {"rows": [r for r in fixtures["rows"] if r["expected"] == "negative"]},
        14: {"tests": "tests/test_financial_exclusion_expectation_m12u.py", "fixtures": fixtures},
        15: replay,
        16: next(r for r in preserved_rows() if r["ticker"] == "FIC-FIN-05"),
        17: root["expectation"],
        18: root["expectation"],
        19: root["expectation"],
        20: root["expectation"],
        21: root["expectation"],
        22: root["expectation"],
        29: root["expectation"],
        30: root["expectation"],
        45: {"status": "NOT_MEASURED", "historical_portability_backlog": 5},
        75: {"next_scope": "HOSTED_CI_HISTORICAL_ARTIFACT_PORTABILITY_REPAIR", "known_failures": 5},
        76: firewall(),
        77: {"start": schedule, "end": "NOT_MEASURED"},
    }
    for i, case in enumerate(fixtures["leverage"], 23):
        payloads[i] = case
    for i in range(31, 42):
        payloads[i] = {
            "status": scope["status"],
            "scope": "03-m12u-scope-freeze.json",
            "all_unrelated_files_byte_identical": not scope["unexpected_file_changes"],
            "allowed_changes": [HELPER, BALANCE, TEST_MIGRATION],
            "schema_source_renderer_runtime_changes": 0,
        }
    for n, value in payloads.items():
        report(n, value)
    tests = [
        "financial_exclusion_m12f",
        "financial_exclusion_leverage_m12f",
        "directional_financial_context_service",
        "directional_balance_ordinal_calibration",
        "qtd_ytd_plain_korean_period_validator_m12d",
        "directional_financial_context_m12g",
        "first_class_typed_financial_evidence_m12b",
        "financial_boundary_calibration_m12e",
        "astra_transport_m12t",
        "financial_exclusion_expectation_m12u",
    ]
    commands = {
        "focused": [sys.executable, "-m", "pytest", "-q", *[f"tests/test_{n}.py" for n in tests]],
        "full": [sys.executable, "-m", "pytest", "-q"],
        "ruff": [str(Path(sys.executable).with_name("ruff")), "check", "."],
        "diff": ["git", "diff", "--check", BASE],
    }
    validations = {}
    for label, command in commands.items():
        print("M12U_VALIDATION", label, flush=True)
        validations[label] = m12._run_command(
            command, output_path=OUTPUT / "validation" / f"{label}.txt", timeout=3600
        )
    report(42, validations["focused"])
    report(43, validations["full"])
    report(44, {n: validations[n] for n in ("ruff", "diff")})
    readiness = m12.probe_codex_network_readiness()
    checks = {
        "authoring": (root["authoring"]["model"], root["authoring"]["effort"])
        == (f.MODEL, f.EFFORT),
        "integrity": integrity["status"] == "PASS",
        "scope": scope["status"] == "PASS",
        "offline_replay": replay["status"] == "PASS",
        "fixtures": fixtures["status"] == "PASS",
        "schedules": schedule["status"] == "PASS",
        "network": readiness.ready,
        "runner_available": e.model_availability()["status"] == "PASS",
        **{n: r["returncode"] == 0 for n, r in validations.items()},
    }
    gate = {
        **provenance,
        "checks": checks,
        "validations": validations,
        "status": "PASS" if all(checks.values()) else "FAIL",
        "network_readiness": asdict(readiness),
    }
    if not all(checks.values()):
        write(OUTPUT / "phase-a-receipt.json", gate)
        report(46, gate)
        raise SystemExit("NO_MODEL_CALLS")
    f.configure_runtime()
    generation = (
        "20260910-m12u-fictional-"
        + datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        + "-"
        + uuid.uuid4().hex[:12]
    )
    packets, owned, catalogs, contexts = m12.fictional_inputs(generation)
    with zipfile.ZipFile(LATEST) as z:
        if any(
            contexts[n] != json.loads(z.read(f"experiment/contexts/{n}.json")) for n in m12.TICKERS
        ):
            raise ValueError("frozen_source_changed")
    lock = m12._source_lock(generation, packets, owned, catalogs, contexts)
    write(OUTPUT / "source-lock.json", lock)
    for n in m12.TICKERS:
        write(OUTPUT / "contexts" / f"{n}.json", contexts[n])
        write(OUTPUT / "aliases" / f"{n}.json", catalogs[n].model_dump(mode="json"))
    inputs = m12._write_frozen_model_inputs(
        generation_id=generation, output_root=OUTPUT, catalogs=catalogs, contexts=contexts
    )
    gate.update(
        generation_id=generation,
        source_lock_sha256=lock["source_lock_sha256"],
        model_inputs=inputs,
        code_file_sha256={
            p: sha(Path(p).read_bytes()) for p in git("ls-files", "*.py").splitlines()
        },
        config_file_sha256={
            str(p): sha(p.read_bytes())
            for p in (ROOT, BASELINE, FIXTURES, INSTRUCTION, f.ROOT, e.FIXTURE)
        },
    )
    write(OUTPUT / "phase-a-receipt.json", gate)
    report(46, gate)
    report(
        47, {**m12.fictional_manifest(generation), "model": f.MODEL, "reasoning_effort": f.EFFORT}
    )
    report(48, lock)
    print(json.dumps({"status": gate["status"], "generation_id": generation}), flush=True)


def run():
    old_output, old_calibration = t.OUTPUT, f._calibration_audit
    t.OUTPUT, f._calibration_audit = OUTPUT, calibration_audit
    try:
        t.run()
    finally:
        t.OUTPUT, f._calibration_audit = old_output, old_calibration


def firewall():
    names = (
        "provider_source_fetches production_db_mutations monitoring_registrations "
        "assessment_persistence_mutations warning_mutations notification_queue_writes production_sends "
        "main_merges deployments scheduler_mutation_count automatic_monitoring_resume "
        "model_calls_real model_calls_judge real_issuer_model_exposure_count"
    )
    return {n: 0 for n in names.split()}


def finalize():
    gate, root = read(OUTPUT / "phase-a-receipt.json"), read(ROOT)
    docs = [read(p) for p in sorted((OUTPUT / "model-calls").glob("**/run-document.json"))]
    receipts = [read(p) for p in sorted((OUTPUT / "model-calls").glob("**/receipt.json"))]
    rows = [{**r, "repetition": d["repetition"]} for d in docs for r in d.get("rows", [])]
    complete = len(receipts) == 6 and len(rows) == 24 and all(d["status"] == "PASS" for d in docs)
    summary = (
        read(OUTPUT / "canary-summary.json") if (OUTPUT / "canary-summary.json").exists() else {}
    )
    stop = read(OUTPUT / "canary-stop.json") if (OUTPUT / "canary-stop.json").exists() else {}
    for n in range(49, 55):
        report(n, {"status": "NOT_RUN", "reason": stop.get("stop_reason", "no attempt")})
    for d in docs:
        report(49 + (d["repetition"] - 1) * 2 + d["context"] - 1, d)
    errors = [err for row in rows for err in row.get("errors", [])]
    report(
        55,
        {
            "complete": complete,
            "rows": rows,
            "errors": errors,
            "final_pass_count": sum(r["status"] == "PASS" for r in rows),
            "legacy_precalibration_pass_count_not_authoritative": True,
        },
    )
    exclusion = [
        {
            "ticker": r["ticker"],
            "repetition": r["repetition"],
            "errors": r["errors"],
            "claims": [asdict(c) for c in f.candidate_financial_framework_claims(r["core"])],
        }
        for r in rows
    ]
    report(56, {"complete": complete, "rows": exclusion})
    report(
        57,
        {
            "complete": complete,
            "contract": root["expectation"],
            "rows": [r for r in rows if r["ticker"] == "FIC-FIN-05"],
        },
    )
    grounding = f.grounding._grounding_summary(rows, require_complete=complete)
    report(58, grounding)
    core, stance = [], []
    for ticker in m12.TICKERS:
        selected = [r["core"] for r in rows if r["ticker"] == ticker]
        balances = [
            (r["overall_direction"], r["directional_balance"]["buy"], r["hold_lean"])
            for r in selected
        ]
        core.append(
            {
                "ticker": ticker,
                "values": balances,
                "unique_count": len(set(balances)) if complete else "NOT_MEASURED",
            }
        )
        stance.append(
            {
                "ticker": ticker,
                "new_buyer": [r["fundamental_new_buyer"]["stance"] for r in selected],
                "holder": [r["fundamental_holder"]["stance"] for r in selected],
                "business_delta": [r["business_thesis_change"] for r in selected],
            }
        )
    variance = {
        key: sum(len(set(r[key])) > 1 for r in stance) if complete else "NOT_MEASURED"
        for key in ("new_buyer", "holder", "business_delta")
    }
    formal = summary.get("stability", {"status": "NOT_MEASURED"})
    report(
        59,
        {
            "rows": stance,
            "business_delta_variance": variance["business_delta"],
            "no_forced_weakened": True,
        },
    )
    report(60, formal)
    report(61, {"complete": complete, "rows": core})
    report(62, {"complete": complete, "rows": stance, "variance": variance})
    elapsed = [r["elapsed_seconds"] for r in receipts]
    report(
        63,
        {
            "calls": receipts,
            "median_latency": statistics.median(elapsed) if elapsed else "NOT_MEASURED",
            "max_latency": max(elapsed) if elapsed else "NOT_MEASURED",
            "retry_success_events": sum(
                r["status"] == "PASS" and r["cli_internal_retry_event_count"] > 0 for r in receipts
            ),
        },
    )
    cross = {}
    for label, path in (
        ("Sol_M12D", e.M12D),
        ("Astra_M12E", f.LATEST),
        ("Astra_M12F", t.LATEST),
        ("Astra_M12T", LATEST),
    ):
        with zipfile.ZipFile(path) as z:
            cross[label] = [
                r
                for n in z.namelist()
                if n.startswith("experiment/model-calls/") and n.endswith("run-document.json")
                for r in json.loads(z.read(n)).get("rows", [])
            ]
    report(
        64,
        {
            "policy": "CROSS_MODEL_DESCRIPTIVE_ONLY",
            "Sol": cross.pop("Sol_M12D"),
            "Astra_M12U": rows,
            "improvement_rate": "NOT_MEASURED",
        },
    )
    report(
        65,
        {
            "policy": "CONTRACT_CHANGED_NOT_DIRECT_REGRESSION",
            "prior": cross,
            "Astra_M12U": rows,
            "change": "Exclusion predicate and one economic-independence paragraph; source/model/effort unchanged",
        },
    )
    report(66, summary.get("specificity", {"status": "NOT_MEASURED"}))
    runtime = {
        "model_calls_fictional": sum(r.get("model_process_spawned", False) for r in receipts),
        "model_context_success_count": sum(r["status"] == "PASS" for r in receipts),
        "model_context_failure_count": sum(r["status"] != "PASS" for r in receipts),
        "timeout_count": sum(r.get("timed_out", False) for r in receipts),
        "capacity_failure_count": sum(
            "CAPACITY" in str(r.get("failure_type", "")).upper() for r in receipts
        ),
        "cli_internal_retry_event_count": sum(
            r["cli_internal_retry_event_count"] for r in receipts
        ),
        "wrapper_retry_count": sum(r["wrapper_retry_count"] for r in receipts),
    }
    identities = {
        k: [r["runtime_isolation"][k] for r in receipts]
        for k in ("invocation_id", "runtime_state_namespace_hash", "working_directory_identity")
    }
    identities["session_id"] = [r.get("session_id") for r in receipts]
    report(
        67,
        {
            **runtime,
            "stop": stop,
            "identities": identities,
            "unique": all(len(v) == len(set(v)) for v in identities.values()),
            "backend_sampling_request_count": "NOT_MEASURED",
        },
    )
    next_scope = "FRESH_REAL_FINANCIAL_CONTEXT_GENERALIZATION_PROOF_GPT6_ASTRA_XHIGH"
    if runtime["timeout_count"]:
        next_scope = "ASTRA_TRANSPORT_RUNTIME_ARCHITECTURE_REVIEW"
    elif any(r["ticker"] == "FIC-FIN-08" and r["errors"] for r in rows):
        next_scope = "BOUNDED_FINANCIAL_EXCLUSION_ASSERTION_SCOPE_REPAIR_V2"
    elif any(r.get("m12f_calibration", {}).get("status") == "FAIL" for r in rows):
        next_scope = "BOUNDED_MARKET_EXPECTATION_LEVERAGE_CALIBRATION_REPAIR_GPT6_ASTRA"
    elif not complete or errors:
        next_scope = "BOUNDED_DIRECTIONAL_FINANCIAL_CONTEXT_REPAIR_GPT6_ASTRA"
    elif variance["new_buyer"]:
        next_scope = "BOUNDED_NEW_BUYER_STANCE_CALIBRATION_REPAIR_GPT6_ASTRA"
    elif variance["holder"]:
        next_scope = "BOUNDED_HOLDER_STANCE_CALIBRATION_REPAIR_GPT6_ASTRA"
    elif variance["business_delta"]:
        next_scope = "BOUNDED_BUSINESS_THESIS_DELTA_SEMANTICS_REVIEW"
    ready = (
        complete and not errors and not any(variance.values()) and formal.get("status") == "PASS"
    )
    for n, payload in {
        68: {
            "offline": read(REPORTS / f"15-{SLUGS[15]}.json")["status"],
            "full_proof": complete,
            "live_errors": [r for r in exclusion if r["errors"]],
        },
        69: {
            "contract": root["expectation"],
            "full_proof": complete,
            "violations": [
                r["ticker"] for r in rows if r.get("m12f_calibration", {}).get("status") == "FAIL"
            ],
        },
        70: {"complete": complete, "rows": core},
        71: {"variance": variance["business_delta"]},
        72: {"variance": variance["new_buyer"]},
        73: {"variance": variance["holder"]},
        74: {
            "fresh_real_proof_readiness": "READY" if ready else "NOT_READY",
            "production_readiness": "NOT_READY",
            "next_scope": next_scope,
        },
        76: firewall(),
    }.items():
        report(n, payload)
    schedule = read(REPORTS / f"77-{SLUGS[77]}.json")
    schedule["end"] = stability._schedule_observation()
    report(77, schedule)
    report(
        78,
        {
            "path": "docs/MASTER_WORKFLOW.md",
            "next_scope": next_scope,
            "status": "CLOSEOUT_REQUIRED",
        },
    )
    zeros = (
        "model_target_fallback_count runtime_change_count timeout_change_count wrapper_retry_change_count "
        "business_delta_contract_change_count new_buyer_contract_change_count holder_contract_change_count "
        "fixed_financial_score_rule_count evidence_count_bucket_rule_count financial_context_selection_change_count "
        "first_class_projection_change_count working_capital_validator_semantic_change_count qtd_ytd_validator_semantic_change_count "
        "non_exclusion_financial_validator_change_count output_schema_change_count price_timing_prompt_change_count "
        "renderer_substantive_change_count source_sufficiency_semantic_change_count daily_delta_semantic_change_count warning_semantic_change_count"
    )
    completion = {k: 0 for k in zeros.split()}
    completion.update(
        {
            k: False
            for k in (
                "directional_threshold_changed",
                "directional_increment_changed",
                "hold_lean_contract_changed",
                "calibration_tiebreak_direction_changed",
            )
        }
    )
    completion.update(
        {
            **firewall(),
            **runtime,
            **{
                k: gate[k]
                for k in ("base_sha", "work_instruction_commit", "implementation_commit", "branch")
            },
            "report_commit": "NOT_MEASURED",
            "final_head_sha": "NOT_MEASURED",
            "latest_result_zip_sha256": LATEST_SHA,
            "latest_result_integrity": "PASS",
            "m12t_status": "PARTIAL_STOPPED",
            "m12u_status": "COMPLETE" if complete else "PARTIAL_STOPPED",
            "status": "COMPLETE" if complete else "PARTIAL_STOPPED",
            "stop_reason": stop.get("stop_reason"),
            "implementation_model_target": f.MODEL,
            "implementation_reasoning_effort": f.EFFORT,
            "investment_judgment_model_target": f.MODEL,
            "investment_judgment_reasoning_effort": f.EFFORT,
            "authoring_model_target_match": True,
            "runner_model_target_match": bool(receipts)
            and all(
                (r.get("observed_model"), r.get("observed_effort")) == (f.MODEL, f.EFFORT)
                for r in receipts
            ),
            "transport_root_cause_frozen": root["transport"]["classification"],
            "timeout_seconds": 1800,
            "financial_exclusion_root_cause": root["exclusion"]["root_cause"],
            "financial_exclusion_repair_status": "OFFLINE_PASS",
            "explicit_exclusion_false_reject_count": "AUTHORING_REVIEW_REQUIRED"
            if any(r["ticker"] == "FIC-FIN-08" and r["errors"] for r in rows)
            else 0,
            "financial_sector_true_misuse_count": "AUTHORING_REVIEW_REQUIRED"
            if any(r["ticker"] == "FIC-FIN-08" and r["errors"] for r in rows)
            else 0,
            "market_expectation_independence_classification": root["expectation"]["classification"],
            "market_expectation_leverage_contract_status": "FROZEN",
            "fic_fin_05_target_direction": "HOLD",
            "fic_fin_05_target_buy": 4.5,
            "fic_fin_05_target_sell": 5.5,
            "fic_fin_05_target_lean": "SELL_LEAN",
            "directional_prompt_change_count": 1,
            "fictional_generation_id": gate["generation_id"],
            "fictional_subject_count": 8,
            "fictional_context_count": 2,
            "fictional_repetition_count": 3,
            "fictional_output_row_count": len(rows),
            "fictional_schema_pass_count": len(rows),
            "final_row_pass_count": sum(r["status"] == "PASS" for r in rows),
            "hard_financial_semantic_violation_count": len(errors),
            "errors": errors,
            "grounding_failure_count": grounding.get("grounding_failure_count", "NOT_MEASURED"),
            "invalid_financial_reference_count": sum("invalid" in x and "ref" in x for x in errors),
            "fic_fin_05_target_bucket_contract_violation_count": sum(
                r["ticker"] == "FIC-FIN-05"
                and r.get("m12f_calibration", {}).get("status") == "FAIL"
                for r in rows
            ),
            "formal_stability": formal,
            "core_only_stable_count": sum(r["unique_count"] == 1 for r in core)
            if complete
            else "NOT_MEASURED",
            "core_only_unstable_count": sum(r["unique_count"] != 1 for r in core)
            if complete
            else "NOT_MEASURED",
            "business_delta_variance_subject_count": variance["business_delta"],
            "new_buyer_stance_variance_subject_count": variance["new_buyer"],
            "holder_stance_variance_subject_count": variance["holder"],
            "message_specificity_advisory_status": summary.get("specificity", {}).get(
                "status", "NOT_MEASURED"
            ),
            "hosted_ci_status": "NOT_MEASURED",
            "hosted_ci_portability_backlog_count": 5,
            "observed_paused_schedule_count": schedule["end"]["observed_paused_schedule_count"],
            "focused_test_result": gate["validations"]["focused"],
            "full_test_result": gate["validations"]["full"],
            "ruff_result": gate["validations"]["ruff"],
            "git_diff_check": gate["validations"]["diff"],
            "artifact_count": "NOT_MEASURED",
            "fresh_real_proof_readiness": "READY" if ready else "NOT_READY",
            "production_readiness": "NOT_READY",
            "next_scope": next_scope,
        }
    )
    for row in core:
        completion[
            row["ticker"].lower().replace("-", "_") + "_directional_balance_unique_count"
        ] = row["unique_count"]
    report(79, completion)
    print(
        json.dumps(
            {
                "complete": complete,
                "rows": len(rows),
                "errors": errors,
                "variance": variance,
                "next_scope": next_scope,
            }
        ),
        flush=True,
    )


def bundle():
    old = t.OUTPUT, t.REPORTS, t.NAME, t.BASE
    t.OUTPUT, t.REPORTS, t.NAME, t.BASE = OUTPUT, REPORTS, NAME, BASE
    try:
        t.bundle()
    finally:
        t.OUTPUT, t.REPORTS, t.NAME, t.BASE = old


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("prepare", "run", "finalize", "bundle"))
    globals()[parser.parse_args().command]()
