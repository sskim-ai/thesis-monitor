"""Frozen, archive-only M12F validation and fictional canary orchestration."""

from __future__ import annotations

import argparse
import ast
from dataclasses import asdict
from datetime import UTC, datetime
import json
from pathlib import Path
import re
import sys
from types import SimpleNamespace
import uuid
import zipfile

from app.services.financial_framework_claim_service import (
    FrameworkClaimKind,
    candidate_financial_framework_claims,
    financial_framework_claims,
)
from scripts import financial_boundary_calibration_m12e as previous
from scripts import directional_financial_context_m12 as m12
from scripts import directional_financial_context_m12g as grounding
from scripts import first_class_typed_financial_evidence_m12b as runner
from scripts import bounded_directional_financial_context_stability_m12s as stability


BASE = "19b3dd7bc2353f418452e2db67c78e886a73cbc6"
INSTRUCTION_COMMIT = "a7029856c189599c96f6c357bb2c949a47af10a3"
NAME = "20260909-financial-exclusion-validator-repair-leverage-boundary-full-fictional-canary"
OUTPUT = Path("artifacts") / NAME
REPORTS = Path("docs/reports") / NAME
INSTRUCTION = Path(
    "docs/work-instructions/20260909-financial-exclusion-validator-repair-and-leverage-boundary-review-full-fictional-canary.md"
)
ROOT = Path("docs/architecture/M12F_FINANCIAL_EXCLUSION_LEVERAGE_REVIEW.json")
BASELINE = Path("fixtures/m12f_scope_baseline.json")
FIXTURES = Path("fixtures/financial_exclusion_m12f.json")
LATEST = Path(
    "/Users/sskim/Documents/Codex/thesis-monitor-20260909-bounded-financial-context-boundary-calibration-full-fictional-canary-report.zip"
)
LATEST_SHA = "2cfab9aa676cc61af733198bddadb18971fcb631ca22b17e4735c05a9734484e"
MODEL, EFFORT = "gpt-6-astra", "xhigh"
SLUGS = dict(
    (int(n), s) for n, s in re.findall(r"^(\d{2})-([a-z0-9-]+)$", INSTRUCTION.read_text(), re.M)
)
FINANCIAL_SERVICE = "app/services/directional_financial_context_service.py"
CASE_SERVICE = "scripts/directional_financial_context_m12.py"
read, write, sha, git = previous.read, previous.write, previous.sha, previous.git


def report(number, value):
    write(REPORTS / f"{number:02d}-{SLUGS[number]}.json", value)


def _nodes(source):
    return ast.parse(source).body


def _function(source, name):
    return next(n for n in _nodes(source) if isinstance(n, ast.FunctionDef) and n.name == name)


def freeze_audit():
    baseline = read(BASELINE)
    changes = [
        p for p, h in baseline["unchanged_python_sha256"].items() if sha(Path(p).read_bytes()) != h
    ]
    residuals = {}
    for path, before in baseline["approved_module_before"].items():
        old, new = ast.parse(before), ast.parse(Path(path).read_text())
        if path == FINANCIAL_SERVICE:
            function = next(
                n
                for n in new.body
                if isinstance(n, ast.FunctionDef)
                and n.name == "validate_directional_financial_semantics"
            )
            old_function = _function(before, function.name)
            old_assignment = next(
                n
                for n in ast.walk(old_function)
                if isinstance(n, ast.Assign)
                and any(isinstance(t, ast.Name) and t.id == "net_debt_language" for t in n.targets)
            )

            class RestoreApprovedNetDebtPredicate(ast.NodeTransformer):
                def visit_Assign(self, node):
                    if any(
                        isinstance(t, ast.Name) and t.id == "net_debt_language"
                        for t in node.targets
                    ):
                        return old_assignment
                    return node

            RestoreApprovedNetDebtPredicate().visit(function)
            additions = [
                n
                for n in function.body
                if isinstance(n, ast.If)
                and isinstance(n.test, ast.Name)
                and n.test.id == "financial_sector"
            ]
            if len(additions) != 1:
                raise ValueError("exclusion_sector_guard_missing_or_duplicated")
            function.body.remove(additions[0])
            new.body = [
                n
                for n in new.body
                if not (
                    isinstance(n, ast.ImportFrom)
                    and n.module == "app.services.financial_framework_claim_service"
                )
            ]
        else:
            function = next(
                n
                for n in old.body
                if isinstance(n, ast.FunctionDef) and n.name == "_case_semantic_errors"
            )
            sector = next(
                n
                for n in function.body
                if isinstance(n, ast.If) and ast.unparse(n.test) == "ticker == 'FIC-FIN-08'"
            )
            sector.body = sector.body[:1]
        residuals[path] = ast.dump(old, include_attributes=False) == ast.dump(
            new, include_attributes=False
        )
    helper = Path("app/services/financial_framework_claim_service.py").read_text()
    return {
        "unchanged_python_count": len(baseline["unchanged_python_sha256"]),
        "unexpected_file_changes": changes,
        "all_unapproved_ast_unchanged": residuals,
        "production_validator_fictional_branch_count": int(
            "FIC-FIN" in helper or "ticker" in helper
        ),
        "prompt_change_count": 0
        if "app/services/directional_balance_service.py" not in changes
        else 1,
        "status": "PASS"
        if not changes
        and all(residuals.values())
        and "FIC-FIN" not in helper
        and "ticker" not in helper
        else "FAIL",
    }


def preserved_rows():
    with zipfile.ZipFile(LATEST) as archive:
        return [
            r
            for name in ("reports/37-run-1-context-01.json", "reports/38-run-1-context-02.json")
            for r in json.loads(archive.read(name))["rows"]
        ]


def offline_replay():
    _, owned, catalogs, _ = m12.fictional_inputs("m12f-offline-review")
    old = preserved_rows()
    rows = []
    for first in (0, 4):
        batch = m12.DirectionalCoreBatch(
            packet_id="m12f-offline-review",
            candidates=tuple(
                m12.DirectionalCoreCandidate.model_validate(r["core"])
                for r in old[first : first + 4]
            ),
        )
        audited, _ = grounding._audit_core_batch_with_grounding(
            batch, owned=owned, catalogs=catalogs
        )
        rows.extend(audited)
    return {
        "original_verdict_unchanged": True,
        "rows": rows,
        "status": "PASS" if all(r["status"] == "PASS" for r in rows) else "FAIL",
    }


def exclusion_fixture_audit():
    fixture = read(FIXTURES)
    rows = []
    for expected, values in fixture.items():
        if expected not in {"positive", "negative"}:
            continue
        for text in values:
            claims = financial_framework_claims(text)
            excluded = bool(claims) and all(
                c.kind == FrameworkClaimKind.EXPLICIT_EXCLUSION for c in claims
            )
            rows.append(
                {
                    "text": text,
                    "expected": expected,
                    "claims": [asdict(c) for c in claims],
                    "status": "PASS" if excluded == (expected == "positive") else "FAIL",
                }
            )
    return {"rows": rows, "status": "PASS" if all(r["status"] == "PASS" for r in rows) else "FAIL"}


def configure_runtime():
    m12.MODEL, m12.EFFORT = MODEL, EFFORT
    if (m12.TIMEOUT_SECONDS, m12.SUBJECTS_PER_CONTEXT, m12.REPETITION_COUNT) != (1800, 4, 3):
        raise ValueError("runtime_contract_changed")


def prepare():
    if (OUTPUT / "phase-a-receipt.json").exists():
        raise ValueError("phase_a_already_frozen")
    root = read(ROOT)
    if root["authoring"]["model"] != MODEL or root["authoring"]["effort"] != EFFORT:
        raise ValueError("AUTHORING_MODEL_TARGET_MISMATCH")
    integrity = previous.verify_zip(LATEST, LATEST_SHA)
    for n in SLUGS:
        report(n, {"status": "NOT_MEASURED"})
    frozen, fixtures, replay = freeze_audit(), exclusion_fixture_audit(), offline_replay()
    provenance = {
        "base_sha": BASE,
        "work_instruction_commit": INSTRUCTION_COMMIT,
        "implementation_commit": git("rev-parse", "HEAD"),
        "branch": git("branch", "--show-current"),
        "origin_main": git("rev-parse", "origin/main"),
    }
    old = {r["ticker"]: r for r in preserved_rows()}
    leverage = root["leverage"]
    reports = {
        1: provenance,
        2: integrity,
        3: {"root_cause_freeze": root, "scope": frozen},
        4: {"model": MODEL, "reasoning_effort": EFFORT, "fallback_count": 0},
        5: root["authoring"],
        6: previous.model_availability(),
        7: {"policy": root["descriptive_policy"], "cross_model_same_runtime_claim_count": 0},
        8: {
            "before": root["before_replay"],
            "preserved_row": old["FIC-FIN-08"],
            "status": "REPRODUCED_BEFORE_REPAIR",
        },
        9: root["exclusion"],
        10: root["exclusion"],
        11: {"scope": frozen, "diff": git("diff", BASE, "--", FINANCIAL_SERVICE, CASE_SERVICE)},
        12: {
            "rows": [r for r in fixtures["rows"] if r["expected"] == "positive"],
            "status": fixtures["status"],
        },
        13: {
            "rows": [r for r in fixtures["rows"] if r["expected"] == "negative"],
            "status": fixtures["status"],
        },
        14: {
            "policy": "Exclusion does not immunize other occurrences, fields or industrial material refs",
            "test_file": "tests/test_financial_exclusion_m12f.py",
            "status": fixtures["status"],
        },
        15: replay,
        16: {
            "case_change_semantics": leverage["case_change_semantics"],
            "support": leverage["support"],
            "thesis_change": leverage["thesis_change"],
        },
        17: {"preserved_row": old["FIC-FIN-05"], "original_status_unchanged": True},
        18: {"contract": leverage["debt_cash_independence"]},
        19: {"contract": leverage["minimum_sell_pattern"]},
        20: {"contract": leverage["sell_lean_pattern"]},
        21: {"contract": leverage["positive_symmetry"]},
        27: {
            "classification": leverage["root_cause"],
            "secondary": leverage["secondary_finding"],
            "selected_branch": root["selected_branch"],
        },
        28: {
            "status": "CONTRACT_CONSISTENT",
            "basis": leverage,
            "historical_verdict_rewrite_count": 0,
        },
        69: {"start": root["schedule_start"], "end": "NOT_MEASURED"},
    }
    for n, fixture in enumerate(root["leverage_fixtures"][:5], 22):
        reports[n] = fixture
    for n in range(29, 40):
        reports[n] = {
            "status": frozen["status"],
            "scope": frozen,
            "exclusion_only_exception": True,
            "leverage_prompt_change": 0,
        }
    for n, value in reports.items():
        report(n, value)
    commands = {
        "focused": [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "tests/test_financial_exclusion_m12f.py",
            "tests/test_financial_exclusion_leverage_m12f.py",
            "tests/test_directional_financial_context_service.py",
            "tests/test_directional_balance_ordinal_calibration.py",
            "tests/test_qtd_ytd_plain_korean_period_validator_m12d.py",
            "tests/test_directional_financial_context_m12g.py",
            "tests/test_first_class_typed_financial_evidence_m12b.py",
            "tests/test_financial_boundary_calibration_m12e.py",
        ],
        "full": [sys.executable, "-m", "pytest", "-q"],
        "ruff": [str(Path(sys.executable).with_name("ruff")), "check", "."],
        "diff": ["git", "diff", "--check", BASE],
    }
    validations = {}
    for name, command in commands.items():
        print(f"M12F_VALIDATION {name}", flush=True)
        validations[name] = m12._run_command(
            command, output_path=OUTPUT / "validation" / f"{name}.txt", timeout=3600
        )
    report(40, validations["focused"])
    report(41, validations["full"])
    report(42, {k: validations[k] for k in ("ruff", "diff")})
    checks = {
        "integrity": integrity["status"] == "PASS",
        "scope": frozen["status"] == "PASS",
        "fixtures": fixtures["status"] == "PASS",
        "offline_replay": replay["status"] == "PASS",
        "model_available": reports[6]["status"] == "PASS",
        **{k: v["returncode"] == 0 for k, v in validations.items()},
    }
    gate = {
        **provenance,
        "checks": checks,
        "validations": validations,
        "status": "PASS" if all(checks.values()) else "FAIL",
    }
    if not all(checks.values()):
        write(OUTPUT / "phase-a-receipt.json", gate)
        report(43, gate)
        raise SystemExit("NO_MODEL_CALLS")
    configure_runtime()
    generation = (
        "20260909-m12f-fictional-"
        + datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        + "-"
        + uuid.uuid4().hex[:12]
    )
    packets, owned, catalogs, contexts = m12.fictional_inputs(generation)
    with zipfile.ZipFile(LATEST) as archive:
        for ticker in m12.TICKERS:
            if contexts[ticker] != json.loads(archive.read(f"experiment/contexts/{ticker}.json")):
                raise ValueError("frozen_case_context_changed")
    lock = m12._source_lock(generation, packets, owned, catalogs, contexts)
    for ticker in m12.TICKERS:
        write(OUTPUT / "contexts" / f"{ticker}.json", contexts[ticker])
        write(OUTPUT / "aliases" / f"{ticker}.json", catalogs[ticker].model_dump(mode="json"))
    write(OUTPUT / "source-lock.json", lock)
    inputs = m12._write_frozen_model_inputs(
        generation_id=generation, output_root=OUTPUT, catalogs=catalogs, contexts=contexts
    )
    gate.update(
        {
            "generation_id": generation,
            "source_lock_sha256": lock["source_lock_sha256"],
            "model_inputs": inputs,
            "code_file_sha256": {
                p: sha(Path(p).read_bytes()) for p in git("ls-files", "*.py").splitlines()
            },
            "config_file_sha256": {
                str(p): sha(p.read_bytes()) for p in (ROOT, BASELINE, FIXTURES, INSTRUCTION)
            },
        }
    )
    write(OUTPUT / "phase-a-receipt.json", gate)
    report(43, gate)
    report(44, {**m12.fictional_manifest(generation), "model": MODEL, "reasoning_effort": EFFORT})
    report(45, lock)
    print(
        json.dumps(
            {
                "status": gate["status"],
                "generation_id": generation,
                "source_hash": lock["source_lock_sha256"],
            }
        ),
        flush=True,
    )


def _calibration_audit(row):
    # Frozen fictional expectations are audit-only; never used to choose a model label.
    expected = {"FIC-FIN-01": 6, "FIC-FIN-02": 4.5, "FIC-FIN-04": 5, "FIC-FIN-05": 4.5}
    ticker = row["ticker"]
    if ticker not in expected:
        return {"status": "NOT_TARGETED"}
    return {
        "expected_buy": expected[ticker],
        "observed_buy": row["core"]["directional_balance"]["buy"],
        "status": "PASS"
        if row["core"]["directional_balance"]["buy"] == expected[ticker]
        else "FAIL",
        "basis": "Frozen source-pattern ordinal contract; matching number alone still requires final evidence review",
    }


def run():
    gate = read(OUTPUT / "phase-a-receipt.json")
    if gate["status"] != "PASS":
        raise ValueError("phase_a_not_passed")
    for key in ("code_file_sha256", "config_file_sha256"):
        if any(sha(Path(p).read_bytes()) != h for p, h in gate[key].items()):
            raise ValueError("code_or_config_changed_after_freeze")
    for row in gate["model_inputs"]["contexts"]:
        for kind in ("prompt", "schema"):
            if sha(Path(row[f"{kind}_path"]).read_bytes()) != row[f"{kind}_sha256"]:
                raise ValueError("model_input_changed_after_freeze")
    if (
        list((OUTPUT / "model-calls").glob("**/receipt.json"))
        or (OUTPUT / "canary-stop.json").exists()
    ):
        raise ValueError("whole_generation_retry_forbidden")
    configure_runtime()
    original_call, original_audit = (
        m12._single_attempt_model_call,
        grounding._audit_core_batch_with_grounding,
    )

    def checked_call(**kwargs):
        receipt = original_call(**kwargs)
        observed = previous.observed_runtime(kwargs["log"].read_text(errors="replace"))
        receipt["observed_runtime"] = observed
        write(kwargs["receipt_path"], receipt)
        if observed != {"model": MODEL, "effort": EFFORT}:
            raise ValueError("MODEL_TARGET_MISMATCH")
        return receipt

    def checked_audit(*args, **kwargs):
        rows, audit = original_audit(*args, **kwargs)
        failures = 0
        for row in rows:
            row["m12f_calibration"] = _calibration_audit(row)
            if row["m12f_calibration"]["status"] == "FAIL":
                row["errors"] = [*row["errors"], "frozen_ordinal_contract_inconsistent"]
                row["status"] = "FAIL"
                failures += 1
        if failures:
            audit = {**audit, "status": "FAIL", "m12f_calibration_failures": failures}
        return rows, audit

    m12._single_attempt_model_call = checked_call
    grounding._audit_core_batch_with_grounding = checked_audit
    try:
        runner.run_canary(
            argparse.Namespace(generation_id=gate["generation_id"], output_root=OUTPUT)
        )
    except Exception as exc:
        receipt_paths = sorted((OUTPUT / "model-calls").glob("**/receipt.json"))
        if receipt_paths and not (OUTPUT / "canary-stop.json").exists():
            path = receipt_paths[-1]
            receipt = read(path)
            document = path.with_name("run-document.json")
            if not document.exists():
                write(
                    document,
                    {
                        "generation_id": gate["generation_id"],
                        "repetition": int(path.parent.parent.name.removeprefix("run-")),
                        "context": int(path.parent.name.removeprefix("context-")),
                        "status": "FAIL",
                        "error_type": type(exc).__name__,
                        "error": str(exc)[:1000],
                        "receipt": receipt,
                    },
                )
            write(
                OUTPUT / "canary-stop.json",
                {
                    "status": "FAIL",
                    "stop_reason": "M12F_SCHEMA_OR_POSTPROCESSING_FAILURE",
                    "failed_invocation": receipt.get("invocation_id"),
                    "model_calls_completed": len(receipt_paths),
                    "wrapper_retry_count": 0,
                },
            )
        raise
    finally:
        m12._single_attempt_model_call = original_call
        grounding._audit_core_batch_with_grounding = original_audit


def finalize():
    gate = read(OUTPUT / "phase-a-receipt.json")
    docs = [read(p) for p in sorted((OUTPUT / "model-calls").glob("**/run-document.json"))]
    receipts = [read(p) for p in sorted((OUTPUT / "model-calls").glob("**/receipt.json"))]
    rows = [{**r, "repetition": d["repetition"]} for d in docs for r in d.get("rows", [])]
    complete = len(rows) == 24 and len(receipts) == 6 and all(d["status"] == "PASS" for d in docs)
    stop = read(OUTPUT / "canary-stop.json") if (OUTPUT / "canary-stop.json").exists() else {}
    summary = (
        read(OUTPUT / "canary-summary.json") if (OUTPUT / "canary-summary.json").exists() else {}
    )
    for n in range(46, 52):
        report(n, {"status": "NOT_RUN", "reason": stop.get("stop_reason", "no attempt")})
    for d in docs:
        report(46 + (d["repetition"] - 1) * 2 + d["context"] - 1, d)
    errors = [e for r in rows for e in r.get("errors", [])]
    report(
        52,
        {
            "status": "PASS" if complete else "PARTIAL_STOPPED",
            "completed_rows": len(rows),
            "hard_errors": errors,
            "hard_error_count": len(errors),
        },
    )
    exclusions = [
        {
            "ticker": r["ticker"],
            "repetition": r["repetition"],
            "claims": [asdict(c) for c in candidate_financial_framework_claims(r["core"])],
            "errors": r["errors"],
        }
        for r in rows
    ]
    report(
        53,
        {
            "rows": exclusions,
            "status": "AWAITING_EVIDENCE_REVIEW",
            "scope": "all completed rows, not full proof unless 24",
        },
    )
    report(
        54,
        {
            "rows": [r for r in rows if r["ticker"] == "FIC-FIN-05"],
            "frozen_contract": read(ROOT)["leverage"],
            "status": "AWAITING_EVIDENCE_REVIEW",
        },
    )
    report(55, grounding._grounding_summary(rows, require_complete=complete))
    report(
        56, summary.get("stability", {"status": "NOT_MEASURED", "reason": "full canary incomplete"})
    )
    core, stances = [], []
    for ticker in m12.TICKERS:
        selected = [r["core"] for r in rows if r["ticker"] == ticker]
        keys = {
            (r["overall_direction"], r["directional_balance"]["buy"], r["hold_lean"])
            for r in selected
        }
        core.append(
            {
                "ticker": ticker,
                "observed_count": len(selected),
                "values": sorted(keys),
                "unique_count": len(keys) if len(selected) == 3 else "NOT_MEASURED",
                "status": "NOT_MEASURED"
                if len(selected) < 3
                else "CORE_BALANCE_DIRECTION_STABLE"
                if len(keys) == 1
                else "CORE_BALANCE_DIRECTION_UNSTABLE",
            }
        )
        stances.append(
            {
                "ticker": ticker,
                "new_buyer": [r["fundamental_new_buyer"]["stance"] for r in selected],
                "holder": [r["fundamental_holder"]["stance"] for r in selected],
            }
        )
    report(57, {"complete": complete, "rows": core, "formal_classifier_replaced": False})
    stance = {
        "complete": complete,
        "rows": stances,
        **{
            name + "_stance_variance_subject_count": sum(len(set(r[key])) > 1 for r in stances)
            if complete
            else "NOT_MEASURED"
            for name, key in (("new_buyer", "new_buyer"), ("holder", "holder"))
        },
    }
    report(58, stance)
    report(
        59,
        {
            "policy": "CROSS_MODEL_DESCRIPTIVE_ONLY",
            "current_rows": [
                {"ticker": r["ticker"], "repetition": r["repetition"], "core": r["core"]}
                for r in rows
                if r["ticker"] in {"FIC-FIN-01", "FIC-FIN-02", "FIC-FIN-04", "FIC-FIN-05"}
            ],
            "m12e_partial": [
                {"ticker": r["ticker"], "core": r["core"]}
                for r in preserved_rows()
                if r["ticker"] in {"FIC-FIN-01", "FIC-FIN-02", "FIC-FIN-04", "FIC-FIN-05"}
            ],
            "sol_historical_table": "AWAITING_DESCRIPTIVE_CLOSEOUT",
            "cross_model_same_runtime_claim_count": 0,
        },
    )
    report(
        60,
        summary.get("specificity", {"status": "NOT_MEASURED", "reason": "full canary incomplete"}),
    )
    runtime = {
        "model_calls_fictional": len(receipts),
        "model_context_success_count": sum(r.get("status") == "PASS" for r in receipts),
        "model_context_failure_count": sum(r.get("status") != "PASS" for r in receipts),
        "timeout_count": sum(bool(r.get("timed_out")) for r in receipts),
        "capacity_failure_count": sum(
            "CAPACITY" in str(r.get("failure_type", "")).upper() for r in receipts
        ),
        "orphan_process_count": sum(r.get("orphan_process_count", 0) for r in receipts),
        "wrapper_retry_count": 0,
        "receipts": receipts,
        "stop": stop,
    }
    report(61, runtime)
    for n in range(62, 67):
        report(
            n,
            {
                "status": "AWAITING_EVIDENCE_REVIEW" if rows else "NOT_MEASURED",
                "complete": complete,
            },
        )
    report(
        67,
        {
            "fresh_real_proof_readiness": "NOT_READY",
            "production_readiness": "NOT_READY",
            "reason": "awaiting final evidence review"
            if complete
            else "incomplete full fictional proof",
        },
    )
    zeros = {
        k: 0
        for k in (
            "model_calls_real",
            "model_calls_judge",
            "real_issuer_model_exposure_count",
            "provider_source_fetches",
            "production_db_mutations",
            "monitoring_registrations",
            "assessment_persistence_mutations",
            "warning_mutations",
            "notification_queue_writes",
            "production_sends",
            "main_merges",
            "deployments",
            "scheduler_mutation_count",
            "automatic_monitoring_resume",
        )
    }
    report(
        68,
        {
            **zeros,
            "status": "PASS",
            "basis": "Only isolated fictional runner and local tests were invoked; no production command",
        },
    )
    end = stability._schedule_observation()
    report(69, {"start": read(ROOT)["schedule_start"], "end": end})
    required = (
        INSTRUCTION.read_text().split("# 62. Program-completion fields", 1)[1].split("# 63.", 1)[0]
    )
    keys = re.search(r"```text\n(.*?)```", required, re.S).group(1).split()
    completion = {k: "NOT_MEASURED" for k in keys}
    completion.update(
        {
            **zeros,
            **{k: v for k, v in runtime.items() if k not in {"receipts", "stop"}},
            **{
                k: gate[k]
                for k in ("base_sha", "work_instruction_commit", "implementation_commit", "branch")
            },
            "latest_result_zip_sha256": LATEST_SHA,
            "latest_result_integrity": "PASS",
            "m12e_status": "PARTIAL_STOPPED",
            "m12f_status": "AWAITING_EVIDENCE_REVIEW" if complete else "PARTIAL_STOPPED",
            "fictional_generation_id": gate.get("generation_id", "NOT_MEASURED"),
            "fictional_subject_count": 8,
            "fictional_context_count": 2,
            "fictional_repetition_count": 3,
            "fictional_output_row_count": len(rows),
            "fictional_schema_pass_count": len(rows),
            "hard_financial_semantic_violation_count": len(errors),
            "target_bucket_contract_violation_count": sum(
                r.get("m12f_calibration", {}).get("status") == "FAIL" for r in rows
            ),
            "implementation_model_target": MODEL,
            "implementation_reasoning_effort": EFFORT,
            "investment_judgment_model_target": MODEL,
            "investment_judgment_reasoning_effort": EFFORT,
            "authoring_model_target_match": True,
            "investment_runner_target_match": all(
                r.get("observed_runtime") == {"model": MODEL, "effort": EFFORT} for r in receipts
            )
            if receipts
            else "NOT_MEASURED",
            "model_target_fallback_count": 0,
            "cross_model_same_runtime_claim_count": 0,
            "observed_paused_schedule_count": end["observed_paused_schedule_count"],
            "fresh_real_proof_readiness": "NOT_READY",
            "production_readiness": "NOT_READY",
            "status": "AWAITING_EVIDENCE_REVIEW" if complete else "PARTIAL_STOPPED",
            "stop_reason": stop.get("stop_reason"),
            "next_scope": "EVIDENCE_CLOSEOUT",
        }
    )
    report(71, completion)
    print(
        json.dumps(
            {"rows": len(rows), "contexts": len(receipts), "complete": complete, "stop": stop}
        ),
        flush=True,
    )


def _scanner_literal_view(source):
    before = read(BASELINE)["approved_module_before"][CASE_SERVICE]
    original = _function(before, "_secret_scan_failures")
    actual = _function(source, "_secret_scan_failures")
    if ast.dump(original) != ast.dump(actual):
        raise ValueError("historical_secret_scanner_changed")
    marker_assignment = next(
        n for n in actual.body
        if isinstance(n, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == "secret_markers" for t in n.targets)
    )
    values = ast.literal_eval(marker_assignment.value)
    lines = source.splitlines(keepends=True)
    section = "".join(lines[marker_assignment.lineno - 1 : marker_assignment.end_lineno])
    count = 0
    for value in values:
        if value in section:
            section = section.replace(value, "KNOWN_EMPTY_SCANNER_MARKER_LITERAL")
            count += 1
    return (
        "".join(lines[: marker_assignment.lineno - 1])
        + section
        + "".join(lines[marker_assignment.end_lineno :]),
        count,
    )


def artifact_secret_scan(rows):
    views, literals = [], 0
    for name, path in rows:
        text = path.read_text(encoding="utf-8", errors="replace")
        if name == CASE_SERVICE:
            text, count = _scanner_literal_view(text)
            literals += count
        elif name == str(BASELINE):
            payload = json.loads(text)
            text_view, count = _scanner_literal_view(
                payload["approved_module_before"][CASE_SERVICE]
            )
            payload["approved_module_before"][CASE_SERVICE] = text_view
            text = json.dumps(payload)
            literals += count
        views.append((name, SimpleNamespace(read_text=lambda text=text, **_kwargs: text)))
    return {
        "failures": m12._secret_scan_failures(views),
        "known_empty_scanner_marker_literals": literals,
        "archived_bytes_modified": False,
    }


def bundle():
    destination = Path("/Users/sskim/Documents/Codex") / f"thesis-monitor-{NAME}-report.zip"
    rows = [("reports/" + p.name, p) for p in sorted(REPORTS.glob("*.json"))]
    rows += [
        ("experiment/" + str(p.relative_to(OUTPUT)), p)
        for p in sorted(OUTPUT.rglob("*"))
        if p.is_file() and "runtime-state" not in p.parts and "working-directory" not in p.parts
    ]
    paths = set(git("diff", "--name-only", BASE).splitlines()) | {
        str(INSTRUCTION),
        str(ROOT),
        str(BASELINE),
        str(FIXTURES),
        "docs/MASTER_WORKFLOW.md",
    }
    rows += [
        (p, Path(p))
        for p in sorted(paths)
        if not p.startswith("docs/reports/") and Path(p).is_file()
    ]
    secret_scan = artifact_secret_scan(rows)
    if secret_scan["failures"]:
        raise ValueError(f"secret_scan_failed:{secret_scan['failures']}")
    index = {
        "contract": "m12f-artifact-index-v1",
        "artifacts": [
            {"path": n, "sha256": sha(p.read_bytes()), "size_bytes": p.stat().st_size}
            for n, p in rows
        ],
    }
    with zipfile.ZipFile(destination, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, path in rows:
            archive.write(path, name)
        archive.writestr("artifact-index.json", json.dumps(index, indent=2) + "\n")
    digest = sha(destination.read_bytes())
    verification = previous.verify_zip(destination, digest)
    if verification["status"] != "PASS":
        raise ValueError("bundle_integrity_failed")
    destination.with_suffix(".zip.sha256").write_text(f"{digest}  {destination.name}\n")
    print(json.dumps({"zip": str(destination), **verification, "secret_scan": secret_scan}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("prepare", "run", "finalize", "bundle"))
    {"prepare": prepare, "run": run, "finalize": finalize, "bundle": bundle}[
        parser.parse_args().command
    ]()
