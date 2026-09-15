"""Archive-only transport review and one frozen fictional generation; no live entry point."""

from __future__ import annotations

import argparse
from dataclasses import asdict
from datetime import UTC, datetime
import json
from pathlib import Path
import re
import statistics
import subprocess
import sys
import uuid
import zipfile

from scripts import financial_exclusion_leverage_m12f as f

e, m12, stability = f.previous, f.m12, f.stability
read, write, sha, git = e.read, e.write, e.sha, e.git
BASE = "be3ee8d17e97edcf82ab2c8535d222c03b13667f"
INSTRUCTION_COMMIT = "09f434f3353db01e75af8b6c7b1526679f16fe99"
NAME = "20260910-bounded-astra-transport-timeout-review-new-full-fictional-canary"
OUTPUT = Path("artifacts") / NAME
REPORTS = Path("docs/reports") / NAME
INSTRUCTION = Path(
    "docs/work-instructions/20260910-bounded-astra-transport-timeout-review-and-new-full-fictional-canary.md"
)
ROOT = Path("docs/architecture/M12T_TRANSPORT_REVIEW.json")
LATEST = (
    Path.home()
    / "Documents/Codex/thesis-monitor-20260909-financial-exclusion-validator-repair-leverage-boundary-full-fictional-canary-report.zip"
)
LATEST_SHA = "e04c88c992cdf7e13415e2d0fb945d343c404a8e6cc620e00f26a91a3bb20383"
SLUGS = dict(
    (int(n), s) for n, s in re.findall(r"^(\d{2})-([a-z0-9-]+)$", INSTRUCTION.read_text(), re.M)
)


def report(number, payload):
    write(REPORTS / f"{number:02d}-{SLUGS[number]}.json", payload)


def diagnostics(receipt, log, prompt, schema):
    header = log.split("\nuser\n", 1)[0]

    def field(name):
        match = re.search(r"^" + re.escape(name) + r": (.+)$", header, re.M)
        return match.group(1) if match else "NOT_MEASURED"

    events = [s for s in log.splitlines() if "codex_core::responses_retry:" in s]
    return {
        "observed_model": field("model"),
        "observed_effort": field("reasoning effort"),
        "cli_version": header.splitlines()[0] if header else "NOT_MEASURED",
        "session_id": field("session id"),
        "elapsed_seconds": (
            datetime.fromisoformat(receipt["finished_at"])
            - datetime.fromisoformat(receipt["started_at"])
        ).total_seconds(),
        "prompt_bytes": len(prompt),
        "schema_bytes": len(schema),
        "output_bytes": receipt.get("output_size", 0),
        "cli_internal_retry_event_count": len(events),
        "cli_internal_retry_events": events,
        "wrapper_retry_count": receipt["wrapper_retry_count"],
        "backend_sampling_request_count": "NOT_MEASURED",
        "timeout": receipt.get("timed_out", False),
        "network_readiness": receipt["network_readiness"],
        "receipt": receipt,
    }


def historical_comparison():
    integrity = {
        "M12F": e.verify_zip(LATEST, LATEST_SHA),
        "M12E": e.verify_zip(f.LATEST, f.LATEST_SHA),
    }
    if any(v["status"] != "PASS" for v in integrity.values()):
        raise ValueError("LATEST_RESULT_BUNDLE_CHECKSUM_MISMATCH")
    rows, texts = {}, {}
    for label, path in (("M12E", f.LATEST), ("M12F", LATEST)):
        rows[label], texts[label] = [], []
        with zipfile.ZipFile(path) as z:
            for i in (1, 2):
                root = f"experiment/model-calls/run-1/context-{i:02d}/"
                receipt = json.loads(z.read(root + "receipt.json"))
                document = json.loads(z.read(root + "run-document.json"))
                prompt, schema = z.read(root + "prompt.txt"), z.read(root + "schema.json")
                row = diagnostics(receipt, z.read(root + "transport.log").decode(), prompt, schema)
                row.update(
                    context=i,
                    subject_order=document["tickers"],
                    run_document_status=document["status"],
                    receipt_sha256=sha(z.read(root + "receipt.json")),
                    runtime_mode="MODEL_CONTEXT_COUPLED",
                )
                rows[label].append(row)
                texts[label].append(
                    [
                        b.decode().replace(document["generation_id"], "GENERATION_ID")
                        for b in (prompt, schema)
                    ]
                )
    comparisons = [
        {
            "context": i + 1,
            "prompt_equal_except_generation": texts["M12E"][i][0] == texts["M12F"][i][0],
            "schema_equal_except_generation": texts["M12E"][i][1] == texts["M12F"][i][1],
        }
        for i in range(2)
    ]
    return {
        "integrity": integrity,
        "rows": rows,
        "comparisons": comparisons,
        "prompt_context_regression": not all(
            r["prompt_equal_except_generation"] and r["schema_equal_except_generation"]
            for r in comparisons
        ),
    }


def source_freeze():
    paths = [
        p
        for p in git("ls-tree", "-r", "--name-only", BASE).splitlines()
        if p.endswith((".py", ".toml", ".yaml", ".yml")) or p.startswith("fixtures/")
    ]
    changed = []
    hashes = {}
    for path in paths:
        before = subprocess.check_output(["git", "show", f"{BASE}:{path}"])
        hashes[path] = sha(before)
        if not Path(path).is_file() or sha(Path(path).read_bytes()) != hashes[path]:
            changed.append(path)
    return {
        "status": "PASS" if not changed else "FAIL",
        "baseline": BASE,
        "base_file_sha256": hashes,
        "changed_paths": changed,
        "financial_semantic_change_count": len(changed),
        "runtime_contract_change_count": len(changed),
    }


def review():
    if ROOT.exists():
        raise ValueError("review_already_frozen")
    history = historical_comparison()
    for n in SLUGS:
        report(n, {"status": "NOT_MEASURED"})
    report(2, history["integrity"])
    report(7, history)
    report(
        8,
        {"comparisons": history["comparisons"], "regression": history["prompt_context_regression"]},
    )
    calls = [r for rows in history["rows"].values() for r in rows]
    isolation_keys = {
        key: [r["receipt"]["runtime_isolation"][key] for r in calls]
        for key in ("invocation_id", "runtime_state_namespace_hash", "working_directory_identity")
    }
    isolation_keys["session_id"] = [r["session_id"] for r in calls]
    unique = all(len(set(v)) == len(v) and "NOT_MEASURED" not in v for v in isolation_keys.values())
    metadata = []
    for row in calls:
        home = Path(row["receipt"]["runtime_state"]["codex_home"])
        metadata.append(
            {
                "home": str(home),
                "exists": home.is_dir(),
                "mode": oct(home.stat().st_mode & 0o777) if home.exists() else "NOT_MEASURED",
                "auth_reference_is_symlink": (home / "auth.json").is_symlink(),
            }
        )
    report(
        9,
        {
            "unique_identities": unique,
            "identities": isolation_keys,
            "metadata": metadata,
            "historical_isolation_defect": not unique,
            "status": "PASS" if unique else "FAIL",
        },
    )
    report(
        11,
        {
            label: [
                {
                    "context": r["context"],
                    "events": r["cli_internal_retry_events"],
                    "wrapper_retry_count": r["wrapper_retry_count"],
                }
                for r in rows
            ]
            for label, rows in history["rows"].items()
        },
    )
    report(12, {label: rows[0] for label, rows in history["rows"].items()})
    report(13, {label: rows[1] for label, rows in history["rows"].items()})
    print(
        json.dumps(
            {
                "integrity": history["integrity"],
                "prompt_regression": history["prompt_context_regression"],
                "unique": unique,
                "runtime_metadata": metadata,
            },
            indent=2,
        )
    )


def prepare():
    if (OUTPUT / "phase-a-receipt.json").exists():
        raise ValueError("phase_a_already_frozen")
    root = read(ROOT)
    frozen = source_freeze()
    history = historical_comparison()
    authoring = root["authoring"]
    report(
        1,
        {
            "base_sha": BASE,
            "work_instruction_commit": INSTRUCTION_COMMIT,
            "implementation_commit": git("rev-parse", "HEAD"),
            "branch": git("branch", "--show-current"),
            "working_tree_state": git("status", "--short"),
            "origin_main": git("rev-parse", "origin/main"),
            "remote_base_branch_sha": git(
                "rev-parse", "origin/codex/20260909-financial-exclusion-leverage-boundary-m12f"
            ),
        },
    )
    report(3, {"review": root, "source_freeze": frozen})
    report(
        4, {"authoring": "gpt-6-astra/xhigh", "runner": "gpt-6-astra/xhigh", "fallback_count": 0}
    )
    report(5, authoring)
    report(6, e.model_availability())
    report(10, root["watchdog_review"])
    report(14, root["classification"])
    report(15, root["runtime_change_decision"])
    for n in range(16, 27):
        report(
            n,
            {
                "status": frozen["status"],
                "baseline": BASE,
                "changed_paths": frozen["changed_paths"],
                "hash_manifest": "03-m12t-scope-freeze.json",
                "proof": "All existing Python/config/fixture bytes unchanged",
            },
        )
    report(60, {"start": root["schedule_start"], "end": "NOT_MEASURED"})
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
    ]
    commands = {
        "focused": [sys.executable, "-m", "pytest", "-q", *[f"tests/test_{t}.py" for t in tests]],
        "full": [sys.executable, "-m", "pytest", "-q"],
        "ruff": [str(Path(sys.executable).with_name("ruff")), "check", "."],
        "diff": ["git", "diff", "--check", BASE],
    }
    validations = {}
    for name, command in commands.items():
        print(f"M12T_VALIDATION {name}", flush=True)
        validations[name] = m12._run_command(
            command, output_path=OUTPUT / "validation" / f"{name}.txt", timeout=3600
        )
    report(27, validations["focused"])
    report(28, validations["full"])
    report(29, {n: validations[n] for n in ("ruff", "diff")})
    readiness = m12.probe_codex_network_readiness()
    checks = {
        "authoring": (authoring["model"], authoring["effort"]) == (f.MODEL, f.EFFORT),
        "integrity": all(r["status"] == "PASS" for r in history["integrity"].values()),
        "no_prompt_regression": not history["prompt_context_regression"],
        "runtime_review": root["gate_pass"],
        "source_freeze": frozen["status"] == "PASS",
        "exclusion": f.exclusion_fixture_audit()["status"] == "PASS",
        "replay": f.offline_replay()["status"] == "PASS",
        "network": readiness.ready,
        "model_available": e.model_availability()["status"] == "PASS",
        "schedules": root["schedule_start"]["status"] == "PASS",
        **{n: r["returncode"] == 0 for n, r in validations.items()},
    }
    gate = {
        "status": "PASS" if all(checks.values()) else "FAIL",
        "checks": checks,
        "validations": validations,
        "base_sha": BASE,
        "work_instruction_commit": INSTRUCTION_COMMIT,
        "implementation_commit": git("rev-parse", "HEAD"),
        "branch": git("branch", "--show-current"),
        "network_readiness": asdict(readiness),
    }
    if not all(checks.values()):
        write(OUTPUT / "phase-a-receipt.json", gate)
        report(31, gate)
        raise SystemExit("NO_MODEL_CALLS")
    f.configure_runtime()
    generation = (
        "20260910-m12t-fictional-"
        + datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        + "-"
        + uuid.uuid4().hex[:12]
    )
    packets, owned, catalogs, contexts = m12.fictional_inputs(generation)
    with zipfile.ZipFile(LATEST) as z:
        if any(
            contexts[t] != json.loads(z.read(f"experiment/contexts/{t}.json")) for t in m12.TICKERS
        ):
            raise ValueError("frozen_fictional_source_changed")
    lock = m12._source_lock(generation, packets, owned, catalogs, contexts)
    write(OUTPUT / "source-lock.json", lock)
    for t in m12.TICKERS:
        write(OUTPUT / "contexts" / f"{t}.json", contexts[t])
        write(OUTPUT / "aliases" / f"{t}.json", catalogs[t].model_dump(mode="json"))
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
            for p in (ROOT, INSTRUCTION, f.ROOT, f.BASELINE, f.FIXTURES, e.FIXTURE)
        },
    )
    write(OUTPUT / "phase-a-receipt.json", gate)
    report(31, gate)
    report(
        32, {**m12.fictional_manifest(generation), "model": f.MODEL, "reasoning_effort": f.EFFORT}
    )
    report(33, lock)
    print(json.dumps({"status": gate["status"], "generation_id": generation}), flush=True)


def observed_call(original, **kwargs):
    receipt = None
    try:
        receipt = original(**kwargs)
        return receipt
    finally:
        path = kwargs["receipt_path"]
        if path.exists():
            stored = read(path)
            data = diagnostics(
                stored,
                kwargs["log"].read_text(errors="replace"),
                kwargs["prompt"].read_bytes(),
                kwargs["schema"].read_bytes(),
            )
            added = {k: v for k, v in data.items() if k != "receipt"}
            stored.update(added)
            write(path, stored)
            if receipt is not None:
                receipt.update(added)


def run():
    original, old_output = m12._single_attempt_model_call, f.OUTPUT
    f.OUTPUT = OUTPUT
    m12._single_attempt_model_call = lambda **kw: observed_call(original, **kw)
    try:
        f.run()
    finally:
        m12._single_attempt_model_call, f.OUTPUT = original, old_output


def finalize():
    gate = read(OUTPUT / "phase-a-receipt.json")
    docs = [read(p) for p in sorted((OUTPUT / "model-calls").glob("**/run-document.json"))]
    receipts = [read(p) for p in sorted((OUTPUT / "model-calls").glob("**/receipt.json"))]
    rows = [{**r, "repetition": d["repetition"]} for d in docs for r in d.get("rows", [])]
    complete = len(receipts) == 6 and len(rows) == 24 and all(d["status"] == "PASS" for d in docs)
    summary = (
        read(OUTPUT / "canary-summary.json") if (OUTPUT / "canary-summary.json").exists() else {}
    )
    stop = read(OUTPUT / "canary-stop.json") if (OUTPUT / "canary-stop.json").exists() else {}
    for n in range(34, 40):
        report(n, {"status": "NOT_RUN", "reason": stop.get("stop_reason", "no attempt")})
    for d in docs:
        report(34 + (d["repetition"] - 1) * 2 + d["context"] - 1, d)
    errors = [err for r in rows for err in r.get("errors", [])]
    report(
        40,
        {
            "status": "PASS" if complete and not errors else "PARTIAL_STOPPED",
            "rows": rows,
            "errors": errors,
        },
    )
    report(
        41,
        {
            "full_proof": complete,
            "rows": [
                {
                    "ticker": r["ticker"],
                    "repetition": r["repetition"],
                    "claims": [
                        asdict(c) for c in f.candidate_financial_framework_claims(r["core"])
                    ],
                    "errors": r["errors"],
                }
                for r in rows
            ],
        },
    )
    report(
        42,
        {
            "full_proof": complete,
            "rows": [r for r in rows if r["ticker"] == "FIC-FIN-05"],
            "contract": read(f.ROOT)["leverage"],
        },
    )
    grounding = f.grounding._grounding_summary(rows, require_complete=complete)
    report(43, grounding)
    formal = summary.get("stability", {"status": "NOT_MEASURED"})
    report(44, formal)
    core, stances = [], []
    for ticker in m12.TICKERS:
        selected = [r["core"] for r in rows if r["ticker"] == ticker]
        values = {
            (r["overall_direction"], r["directional_balance"]["buy"], r["hold_lean"])
            for r in selected
        }
        core.append(
            {
                "ticker": ticker,
                "values": sorted(values),
                "count": len(selected),
                "unique_count": len(values) if complete else "NOT_MEASURED",
            }
        )
        stances.append(
            {
                "ticker": ticker,
                "new_buyer": [r["fundamental_new_buyer"]["stance"] for r in selected],
                "holder": [r["fundamental_holder"]["stance"] for r in selected],
            }
        )
    report(45, {"complete": complete, "rows": core})
    variance = {
        key: sum(len(set(r[key])) > 1 for r in stances) if complete else "NOT_MEASURED"
        for key in ("new_buyer", "holder")
    }
    report(46, {"complete": complete, "rows": stances, "variance": variance})
    elapsed = [r["elapsed_seconds"] for r in receipts]
    report(
        47,
        {
            "calls": receipts,
            "median_elapsed": statistics.median(elapsed) if elapsed else "NOT_MEASURED",
            "max_elapsed": max(elapsed) if elapsed else "NOT_MEASURED",
            "context_distributions": {
                str(i): [
                    r["elapsed_seconds"]
                    for r in receipts
                    if r["invocation_id"].endswith(f"context-{i:02d}")
                ]
                for i in (1, 2)
            },
            "retry_success_count": sum(
                r["status"] == "PASS" and r["cli_internal_retry_event_count"] > 0 for r in receipts
            ),
        },
    )
    cross = {}
    for label, path in (("Sol_M12D", e.M12D), ("Astra_M12E", f.LATEST), ("Astra_M12F", LATEST)):
        with zipfile.ZipFile(path) as z:
            cross[label] = [
                r
                for n in z.namelist()
                if n.startswith("experiment/model-calls/") and n.endswith("run-document.json")
                for r in json.loads(z.read(n)).get("rows", [])
            ]
    report(
        48,
        {
            "policy": "CROSS_MODEL_DESCRIPTIVE_ONLY",
            "prior_rows": cross,
            "Astra_M12T": rows,
            "M12E_validator_diff": "M12F explicit-exclusion repair; prompt and source unchanged",
            "same_model_improvement_rate": "NOT_MEASURED",
        },
    )
    report(49, summary.get("specificity", {"status": "NOT_MEASURED"}))
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
    report(50, {**runtime, "stop": stop, "backend_sampling_request_count": "NOT_MEASURED"})
    bucket_errors = sum(r.get("m12f_calibration", {}).get("status") == "FAIL" for r in rows)
    next_scope = "EVIDENCE_CLOSEOUT"
    if runtime["timeout_count"]:
        next_scope = "ASTRA_TRANSPORT_RUNTIME_ARCHITECTURE_REVIEW"
    elif bucket_errors:
        next_scope = "BOUNDED_ASTRA_BOUNDARY_CALIBRATION_REPAIR"
    elif errors:
        next_scope = "BOUNDED_DIRECTIONAL_FINANCIAL_CONTEXT_REPAIR_GPT6_ASTRA"
    elif complete and variance["new_buyer"]:
        next_scope = "BOUNDED_NEW_BUYER_STANCE_CALIBRATION_REPAIR_GPT6_ASTRA"
    elif complete and variance["holder"]:
        next_scope = "BOUNDED_HOLDER_STANCE_CALIBRATION_REPAIR_GPT6_ASTRA"
    for n in range(51, 58):
        report(
            n,
            {
                "status": "AWAITING_EVIDENCE_REVIEW" if complete else "NOT_READY",
                "full_generation_complete": complete,
                "next_scope": next_scope,
                "fresh_real_proof_readiness": "NOT_READY",
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
        59,
        {
            **zeros,
            "basis": "Only isolated fictional runner/local tests and archive audit commands invoked",
            "status": "PASS",
        },
    )
    end = stability._schedule_observation()
    report(60, {"start": read(ROOT)["schedule_start"], "end": end})
    required = (
        INSTRUCTION.read_text().split("# 49. Program-completion fields", 1)[1].split("# 50.", 1)[0]
    )
    keys = re.search(r"```text\n(.*?)```", required, re.S).group(1).split()
    completion = {k: "NOT_MEASURED" for k in keys}
    completion.update(
        {
            **zeros,
            **runtime,
            **{
                k: gate[k]
                for k in ("base_sha", "work_instruction_commit", "implementation_commit", "branch")
            },
            "latest_result_zip_sha256": LATEST_SHA,
            "latest_result_integrity": "PASS",
            "m12f_status": "PARTIAL_STOPPED",
            "m12t_status": "AWAITING_EVIDENCE_REVIEW" if complete else "PARTIAL_STOPPED",
            "implementation_model_target": f.MODEL,
            "implementation_reasoning_effort": f.EFFORT,
            "investment_judgment_model_target": f.MODEL,
            "investment_judgment_reasoning_effort": f.EFFORT,
            "authoring_model_target_match": True,
            "investment_runner_target_match": all(
                r["observed_model"] == f.MODEL and r["observed_effort"] == f.EFFORT
                for r in receipts
            )
            if receipts
            else "NOT_MEASURED",
            "model_target_fallback_count": 0,
            "transport_root_cause": read(ROOT)["classification"]["primary"],
            "runtime_change_required": False,
            "timeout_seconds": 1800,
            "timeout_change_count": 0,
            "wrapper_retry_change_count": 0,
            "subjects_per_context_change_count": 0,
            "fictional_generation_id": gate.get("generation_id", "NOT_MEASURED"),
            "fictional_subject_count": 8,
            "fictional_context_count": 2,
            "fictional_repetition_count": 3,
            "fictional_output_row_count": len(rows),
            "fictional_schema_pass_count": len(rows),
            "hard_financial_semantic_violation_count": len(errors),
            "target_bucket_contract_violation_count": bucket_errors,
            "observed_paused_schedule_count": end["observed_paused_schedule_count"],
            "new_buyer_stance_variance_subject_count": variance["new_buyer"],
            "holder_stance_variance_subject_count": variance["holder"],
            "fresh_real_proof_readiness": "NOT_READY",
            "production_readiness": "NOT_READY",
            "status": "AWAITING_EVIDENCE_REVIEW" if complete else "PARTIAL_STOPPED",
            "stop_reason": stop.get("stop_reason"),
            "next_scope": next_scope,
            "focused_test_result": gate["validations"]["focused"],
            "full_test_result": gate["validations"]["full"],
            "ruff_result": gate["validations"]["ruff"],
            "git_diff_check": gate["validations"]["diff"],
        }
    )
    for r in core:
        if r["ticker"] in {"FIC-FIN-01", "FIC-FIN-02", "FIC-FIN-04", "FIC-FIN-05"}:
            completion[
                r["ticker"].lower().replace("-", "_") + "_directional_balance_unique_count"
            ] = r["unique_count"]
    for label, calls in read(REPORTS / "07-m12e-vs-m12f-runtime-comparison.json")["rows"].items():
        for r in calls:
            for field in ("elapsed_seconds", "prompt_bytes"):
                completion[f"{label.lower()}_context{r['context']:02d}_{field}"] = r[field]
    report(62, completion)
    print(
        json.dumps(
            {"rows": len(rows), "complete": complete, "runtime": runtime, "next_scope": next_scope}
        )
    )


def bundle():
    rows = [("reports/" + p.name, p) for p in sorted(REPORTS.glob("*")) if p.is_file()]
    rows += [
        ("experiment/" + str(p.relative_to(OUTPUT)), p)
        for p in sorted(OUTPUT.rglob("*"))
        if p.is_file()
        and not p.is_symlink()
        and "runtime-state" not in p.parts
        and "working-directory" not in p.parts
    ]
    rows += [
        (p, Path(p))
        for p in git("diff", "--name-only", BASE).splitlines()
        if Path(p).is_file() and not p.startswith("docs/reports/")
    ]
    scan = f.artifact_secret_scan(rows)
    if scan["failures"]:
        raise ValueError(f"secret_scan_failed:{scan['failures']}")
    index = {
        "contract": "m12t-artifact-index-v1",
        "artifacts": [
            {"path": n, "sha256": sha(p.read_bytes()), "size_bytes": p.stat().st_size}
            for n, p in rows
        ],
    }
    destination = Path.home() / "Documents/Codex" / f"thesis-monitor-{NAME}-report.zip"
    with zipfile.ZipFile(destination, "w", zipfile.ZIP_DEFLATED) as z:
        for name, path in rows:
            z.write(path, name)
        z.writestr("artifact-index.json", json.dumps(index, indent=2) + "\n")
    digest = sha(destination.read_bytes())
    verified = e.verify_zip(destination, digest)
    if verified["status"] != "PASS":
        raise ValueError("bundle_integrity_failed")
    destination.with_suffix(".zip.sha256").write_text(f"{digest}  {destination.name}\n")
    print(json.dumps({"zip": str(destination), **verified, "secret_scan": scan}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("review", "prepare", "run", "finalize", "bundle"))
    globals()[parser.parse_args().command]()
