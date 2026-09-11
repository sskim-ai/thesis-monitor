"""M12V archive-only architecture review and one all-or-stop fictional generation."""

from __future__ import annotations

import argparse
from dataclasses import asdict
from datetime import UTC, datetime
import io
import json
from pathlib import Path
import platform
import re
import statistics
import subprocess
import sys
import tarfile
import uuid
import zipfile

from scripts import financial_exclusion_expectation_m12u as u
from scripts.astra_runtime_adapter_m12v import single_attempt

BASE = "b3bd63ac734047d624d94e08f558d47ce6b679f7"
INSTRUCTION_COMMIT = "f1da357ff8553b0b3d8503b532433d508255af8f"
NAME = "20260910-astra-transport-runtime-architecture-review-full-fictional-canary"
OUTPUT = Path("artifacts") / NAME
REPORTS = Path("docs/reports") / NAME
ROOT = Path("docs/architecture/M12V_RUNTIME_ARCHITECTURE.json")
INSTRUCTION = Path(
    "docs/work-instructions/20260910-astra-transport-runtime-architecture-review-and-full-fictional-canary.md"
)
LATEST = Path.home() / "Documents/Codex" / f"thesis-monitor-{u.NAME}-report.zip"
LATEST_SHA = "73e2c4ca3713689e077507df9f54ca569f7f50055ecdca2426ecc0537b32c976"
SLUGS = {int(n): s for n, s in re.findall(r"^(\d{2})-([a-z0-9-]+)$", INSTRUCTION.read_text(), re.M)}
read, write, sha, git = u.read, u.write, u.sha, u.git


def report(number, data):
    write(REPORTS / f"{number:02d}-{SLUGS[number]}.json", data)


def freeze():
    changed, hashes = [], {}
    with tarfile.open(
        fileobj=io.BytesIO(subprocess.check_output(["git", "archive", BASE]))
    ) as archive:
        for member in archive:
            p = member.name
            if not member.isfile() or not (
                p.endswith((".py", ".toml", ".yaml", ".yml")) or p.startswith("fixtures/")
            ):
                continue
            hashes[p] = sha(archive.extractfile(member).read())
            if not Path(p).is_file() or sha(Path(p).read_bytes()) != hashes[p]:
                changed.append(p)
    return {
        "status": "PASS" if not changed else "FAIL",
        "baseline": BASE,
        "existing_file_sha256": hashes,
        "changed_existing_paths": changed,
        "financial_semantic_change_count": len(changed),
        "directional_semantic_change_count": len(changed),
        "fictional_case_change_count": len([p for p in changed if p.startswith("fixtures/")]),
    }


def history():
    prior = u.t.historical_comparison()
    records, integrity = prior["rows"], prior["integrity"]
    for label, path, digest in (("M12T", u.LATEST, u.LATEST_SHA), ("M12U", LATEST, LATEST_SHA)):
        integrity[label] = u.e.verify_zip(path, digest)
        records[label] = []
        with zipfile.ZipFile(path) as z:
            for name in sorted(z.namelist()):
                if not name.startswith("experiment/model-calls/") or not name.endswith(
                    "/receipt.json"
                ):
                    continue
                prefix = name.removesuffix("receipt.json")
                receipt = json.loads(z.read(name))
                d = u.t.diagnostics(
                    receipt,
                    z.read(prefix + "transport.log").decode(),
                    z.read(prefix + "prompt.txt"),
                    z.read(prefix + "schema.json"),
                )
                d.update(
                    context=int(prefix.split("/")[-2].split("-")[-1]),
                    receipt_sha256=sha(z.read(name)),
                    runtime_mode="MODEL_CONTEXT_COUPLED",
                )
                records[label].append(d)
    return {"integrity": integrity, "rows": records}


def resources():
    observations = {}
    commands = {
        "processes": ["ps", "-axo", "pid,ppid,pcpu,rss,etime,comm"],
        "memory": ["memory_pressure", "-Q"],
        "disk": ["df", "-k", "."],
        "fd": ["sysctl", "kern.num_files", "kern.maxfiles"],
    }
    for name, command in commands.items():
        try:
            p = subprocess.run(command, capture_output=True, text=True, timeout=10)
            text = p.stdout
            if name == "processes":
                text = "\n".join(
                    line
                    for line in text.splitlines()
                    if any(s in line.lower() for s in ("codex", "python", "pid"))
                )
            observations[name] = {"returncode": p.returncode, "output": text}
        except (OSError, subprocess.TimeoutExpired) as exc:
            observations[name] = {"status": "NOT_MEASURED", "error_type": type(exc).__name__}
    return {
        "observed_at": datetime.now(UTC).isoformat(),
        "load_average": __import__("os").getloadavg(),
        "observations": observations,
        "historical_resource_contention": "NOT_MEASURED",
        "causal_conclusion": "No resource cause established; a current snapshot cannot explain historical backend stalls.",
    }


def input_complexity():
    rows = []
    for label, path in (
        ("M12E", u.f.LATEST),
        ("M12F", u.t.LATEST),
        ("M12T", u.LATEST),
        ("M12U", LATEST),
    ):
        with zipfile.ZipFile(path) as archive:
            for name in sorted(archive.namelist()):
                if not name.startswith("experiment/model-calls/") or not name.endswith(
                    "/schema.json"
                ):
                    continue
                schema = json.loads(archive.read(name))
                objects = []

                def visit(value):
                    if isinstance(value, dict):
                        objects.append(value)
                        for child in value.values():
                            visit(child)
                    elif isinstance(value, list):
                        for child in value:
                            visit(child)

                visit(schema)
                prompt = archive.read(name.removesuffix("schema.json") + "prompt.txt").decode()
                paragraphs = [p.strip() for p in prompt.split("\n\n") if p.strip()]
                rows.append(
                    {
                        "generation": label,
                        "path": name,
                        "schema_bytes": len(archive.read(name)),
                        "prompt_bytes": len(prompt.encode()),
                        "schema_object_nodes": len(objects),
                        "schema_property_count": sum(len(n.get("properties", {})) for n in objects),
                        "schema_required_entries": sum(len(n.get("required", [])) for n in objects),
                        "paragraph_count": len(paragraphs),
                        "duplicate_exact_paragraph_count": len(paragraphs) - len(set(paragraphs)),
                        "evidence_row_count": "NOT_MEASURED",
                        "typed_financial_row_count": "NOT_MEASURED",
                    }
                )
    return rows


def review():
    if (OUTPUT / "phase-a-receipt.json").exists():
        raise ValueError("generation_already_frozen")
    root, hist, scope = read(ROOT), history(), freeze()
    for n in SLUGS:
        report(n, {"status": "NOT_MEASURED"})
    report(
        1,
        {
            "base_sha": BASE,
            "work_instruction_commit": INSTRUCTION_COMMIT,
            "actual_head": git("rev-parse", "HEAD"),
            "actual_branch": git("branch", "--show-current"),
            "working_tree_state": git("status", "--short"),
            "remote_base_branch_sha": git(
                "rev-parse", "origin/codex/20260910-financial-exclusion-expectation-m12u"
            ),
            "origin_main": git("rev-parse", "origin/main"),
        },
    )
    report(2, hist["integrity"]["M12U"])
    report(3, scope)
    report(
        4, {"authoring": "gpt-6-astra/xhigh", "judgment": "gpt-6-astra/xhigh", "fallback_count": 0}
    )
    report(5, root["authoring"])
    report(6, u.e.model_availability())
    report(7, hist)
    for n, label in enumerate(("M12E", "M12F", "M12T", "M12U"), 8):
        report(n, {"integrity": hist["integrity"][label], "rows": hist["rows"][label]})
    rows = [r for rr in hist["rows"].values() for r in rr]
    report(
        12,
        {
            "successful_contexts": sum(not r["timeout"] for r in rows),
            "timeout_contexts": sum(r["timeout"] for r in rows),
            "same_cli": sorted({r["cli_version"] for r in rows}),
            "root_cause": root["root_cause"],
            "limits": "2 timeouts are censored at 1800; this sample cannot estimate a completion percentile or prove size/CPU causality.",
        },
    )
    topology = [
        {
            "layer": "canary",
            "function": "first_class_typed_financial_evidence_m12b.run_canary",
            "role": "ordered 2 contexts x3; stop on runtime/semantic/target failure",
        },
        {
            "layer": "prior adapter",
            "function": "directional_financial_context_m12._single_attempt_model_call",
            "role": "one subprocess; merged regular-file stdout/stderr; no readers; absolute wait1800",
        },
        {
            "layer": "M12V adapter",
            "function": "astra_runtime_adapter_m12v.single_attempt",
            "role": "same CLI arguments and isolation; delegates existing lifecycle with2400; no retries",
        },
        {
            "layer": "namespace",
            "function": "prepare_codex_runtime_state / CodexRuntimeIsolationRegistry.claim",
            "role": "unique namespace/workdir; existing saved-auth reference; WAL/isolation audits",
        },
        {
            "layer": "CLI",
            "function": "codex exec v0.153.4",
            "role": "openai Astra/xhigh; internal retry owner; session header observable; backend progress not established",
        },
        {
            "layer": "lifecycle",
            "function": "invoke_instrumented_codex",
            "role": "raw stdout/stderr readers; one monotonic deadline; groupTERM/KILL; cleanup and parse receipts",
        },
        {
            "layer": "semantics",
            "function": "existing M12U grounding/calibration/formal classifier",
            "role": "unchanged facts, prompts, schemas, thresholds and stop logic",
        },
    ]
    report(13, topology)
    report(
        14,
        {
            "prior_timeout_owner": "subprocess.wait timeout1800",
            "selected_timeout_owner": "PYTHON_MONOTONIC_LIFECYCLE_WATCHDOG",
            "wrapper_retry": 0,
            "CLI_retry": "CLI-owned; counted from observed retry logs, not disabled by wrapper",
            "progress_vs_silence": "Local first/last bytes measurable; backend progress unavailable",
        },
    )
    cli = "/Applications/ChatGPT.app/Contents/Resources/codex"
    help_result = subprocess.run(
        [cli, "exec", "--help"], capture_output=True, text=True, timeout=20
    )
    (OUTPUT / "interfaces").mkdir(parents=True, exist_ok=True)
    (OUTPUT / "interfaces/exec-help.txt").write_text(help_result.stdout)
    report(
        15,
        {
            "help_returncode": help_result.returncode,
            "help_sha256": sha(help_result.stdout.encode()),
            "json_supported": "--json" in help_result.stdout,
            "output_schema_supported": "--output-schema" in help_result.stdout,
            "existing_direct_api_owner": "app/services/analysis_report_service.py:InvestmentNarrativeGenerator",
            "official_docs": root["event_capability"]["source"],
        },
    )
    report(16, root["event_capability"])
    report(17, root["direct_transport"])
    report(18, root["topology"])
    report(19, resources())
    report(
        20,
        {
            "structural_counts": input_complexity(),
            "calls": [
                {k: r[k] for k in ("prompt_bytes", "schema_bytes", "elapsed_seconds", "timeout")}
                for r in rows
            ],
            "subject_count": 4,
            "known_M12U_prompt_delta": "one frozen calibration paragraph",
            "size_causality": "NOT_ESTABLISHED: identical M12E/F inputs differ in latency and outcome",
            "no_accidental_duplication": "M12U inputs must compare byte-identical modulo generation in model-call gate",
        },
    )
    report(21, root["instrumentation"])
    for n, option in enumerate(root["options"], 22):
        report(n, option)
    report(28, {"criteria": "Qualitative only; no weighted score", "options": root["options"]})
    report(
        29,
        {
            "selected": root["preferred_runtime_architecture"],
            "rationale": root["timeout_rationale"],
        },
    )
    report(30, root)
    report(
        31,
        {
            "new_runtime_adapter": "scripts/astra_runtime_adapter_m12v.py",
            "existing_runtime_changes": 0,
            "diff": git("diff", BASE, "--", "scripts/astra_runtime_adapter_m12v.py"),
        },
    )
    report(
        32, {"old_seconds": 1800, "selected_seconds": 2400, "rationale": root["timeout_rationale"]}
    )
    report(
        33,
        {
            "before": topology[1],
            "after": topology[2],
            "saved_auth_or_command_semantics_changed": False,
        },
    )
    report(
        34,
        {
            "raw": "lifecycle-receipt.json",
            "compatibility": "receipt.json",
            "owner": root["instrumentation"],
        },
    )
    report(
        35,
        {
            "implementation": "existing codex-transport-lifecycle-v1",
            "new_consumer": "archive-only M12V",
            "python": sys.version,
            "os": platform.platform(),
            "cli": subprocess.check_output([cli, "--version"], text=True).strip(),
            "files": {
                p: sha(Path(p).read_bytes())
                for p in (
                    "app/services/codex_transport_lifecycle_service.py",
                    "scripts/astra_runtime_adapter_m12v.py",
                    "scripts/astra_runtime_m12v.py",
                )
            },
        },
    )
    report(
        36,
        {
            "status": "PENDING_VALIDATION",
            "test_owner": "tests/test_codex_transport_lifecycle_service.py",
        },
    )
    report(
        37,
        {"status": "PENDING_VALIDATION", "test_owner": "tests/test_codex_runtime_state_service.py"},
    )
    for n in range(38, 49):
        report(
            n,
            {
                "status": scope["status"],
                "proof": "03-m12v-scope-freeze.json",
                "changed_existing_paths": scope["changed_existing_paths"],
                "baseline": BASE,
                "contract": root["semantic_freeze"] if n <= 40 else "Existing file bytes unchanged",
            },
        )
    report(
        82, {"next_scope": "HOSTED_CI_HISTORICAL_ARTIFACT_PORTABILITY_REPAIR", "known_failures": 5}
    )
    report(83, u.firewall())
    report(84, {"start": u.stability._schedule_observation(), "end": "NOT_MEASURED"})
    write(
        OUTPUT / "review-receipt.json",
        {
            "scope": scope["status"],
            "history_integrity": all(r["status"] == "PASS" for r in hist["integrity"].values()),
        },
    )
    print(
        json.dumps({"review": "COMPLETE", "history_contexts": len(rows), "scope": scope["status"]})
    )


def validation():
    before = current_hashes()
    tests = [
        "astra_runtime_m12v",
        "codex_transport_lifecycle_service",
        "codex_network_transport_service",
        "codex_runtime_state_service",
        "financial_exclusion_expectation_m12u",
        "financial_exclusion_m12f",
        "directional_financial_context_service",
        "directional_balance_ordinal_calibration",
        "qtd_ytd_plain_korean_period_validator_m12d",
        "first_class_typed_financial_evidence_m12b",
        "materiality_scoped_working_capital_grounding_m12c",
    ]
    # Include repository-owned isolation, sufficiency, delta and renderer regression surfaces.
    extra = [
        str(p)
        for p in Path("tests").glob("test_*.py")
        if any(
            s in p.name
            for s in (
                "source_sufficiency",
                "daily_delta",
                "runtime_isolation",
                "price_timing",
                "renderer",
            )
        )
    ]
    focused = sorted(set([f"tests/test_{n}.py" for n in tests] + extra))
    commands = {
        "focused": [sys.executable, "-m", "pytest", "-q", *focused],
        "full": [sys.executable, "-m", "pytest", "-q"],
        "ruff": [str(Path(sys.executable).with_name("ruff")), "check", "."],
        "diff": ["git", "diff", "--check", BASE],
    }
    results = {}
    for label, command in commands.items():
        print("M12V_VALIDATION", label, flush=True)
        results[label] = u.m12._run_command(
            command, output_path=OUTPUT / "validation" / f"{label}.txt", timeout=3600
        )
    if before != current_hashes():
        raise ValueError("code_changed_during_validation")
    write(OUTPUT / "validation-receipt.json", {"results": results, "code_hashes": before})
    report(49, results["focused"])
    report(50, results["full"])
    report(51, {n: results[n] for n in ("ruff", "diff")})
    for n in (36, 37):
        report(
            n,
            {
                "status": "PASS" if results["focused"]["returncode"] == 0 else "FAIL",
                "focused_receipt": "49-focused-test-results.json",
                "tests": focused,
            },
        )
    print(json.dumps({n: r["returncode"] for n, r in results.items()}))


def current_hashes():
    paths = [
        *Path("app").rglob("*.py"),
        *Path("scripts").glob("*.py"),
        *Path("tests").glob("*.py"),
        *[p for p in Path("fixtures").rglob("*") if p.is_file()],
        u.ROOT,
        u.f.ROOT,
        u.e.FIXTURE,
        ROOT,
        INSTRUCTION,
    ]
    return {str(p): sha(p.read_bytes()) for p in sorted(set(paths))}


def prepare():
    if (OUTPUT / "phase-a-receipt.json").exists():
        raise ValueError("phase_a_already_frozen")
    root, validation = read(ROOT), read(OUTPUT / "validation-receipt.json")
    ci = read(OUTPUT / "validation/implementation-ci.json")
    report(52, ci)
    checks = {
        "review_complete": read(OUTPUT / "review-receipt.json")
        == {"scope": "PASS", "history_integrity": True},
        "scope": freeze()["status"] == "PASS",
        "frozen_validation_code": validation["code_hashes"] == current_hashes(),
        "new_hosted_failures_zero": ci["new_m12v_failure_count"] == 0
        and ci["head_sha"] == git("rev-parse", "HEAD"),
        "authoring": (root["authoring"]["model"], root["authoring"]["effort"])
        == ("gpt-6-astra", "xhigh"),
        "model_available": u.e.model_availability()["status"] == "PASS",
        "schedules_paused": u.stability._schedule_observation()["status"] == "PASS",
        "latest_integrity": u.e.verify_zip(LATEST, LATEST_SHA)["status"] == "PASS",
        **{n: r["returncode"] == 0 for n, r in validation["results"].items()},
    }
    gate = {
        "status": "PASS" if all(checks.values()) else "FAIL",
        "checks": checks,
        "implementation_commit": git("rev-parse", "HEAD"),
        "runtime_contract_sha256": sha(ROOT.read_bytes()),
    }
    if gate["status"] != "PASS":
        report(53, gate)
        raise SystemExit("NO_MODEL_CALLS")
    u.f.configure_runtime()
    generation = (
        "20260910-m12v-fictional-"
        + datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        + "-"
        + uuid.uuid4().hex[:12]
    )
    packets, owned, catalogs, contexts = u.m12.fictional_inputs(generation)
    lock = u.m12._source_lock(generation, packets, owned, catalogs, contexts)
    write(OUTPUT / "source-lock.json", lock)
    for ticker in u.m12.TICKERS:
        write(OUTPUT / "contexts" / f"{ticker}.json", contexts[ticker])
        write(OUTPUT / "aliases" / f"{ticker}.json", catalogs[ticker].model_dump(mode="json"))
    inputs = u.m12._write_frozen_model_inputs(
        generation_id=generation, output_root=OUTPUT, catalogs=catalogs, contexts=contexts
    )
    with zipfile.ZipFile(LATEST) as z:
        old_id = json.loads(z.read("experiment/phase-a-receipt.json"))["generation_id"]
        for ticker in u.m12.TICKERS:
            if contexts[ticker] != json.loads(z.read(f"experiment/contexts/{ticker}.json")):
                raise ValueError("frozen_fictional_source_changed")
        for row in inputs["contexts"]:
            prefix = f"experiment/frozen-contexts/context-{row['context']:02d}/"
            for kind in ("prompt", "schema"):
                suffix = "prompt.txt" if kind == "prompt" else "schema.json"
                before = z.read(prefix + suffix).decode().replace(old_id, "GENERATION_ID")
                after = Path(row[f"{kind}_path"]).read_text().replace(generation, "GENERATION_ID")
                if before != after:
                    raise ValueError("frozen_prompt_or_schema_changed")
    gate.update(
        generation_id=generation,
        source_lock_sha256=lock["source_lock_sha256"],
        model_inputs=inputs,
        code_file_sha256=current_hashes(),
        config_file_sha256={str(ROOT): sha(ROOT.read_bytes())},
        validations=validation["results"],
        source_prompt_schema_equal_M12U=True,
    )
    write(OUTPUT / "phase-a-receipt.json", gate)
    report(53, gate)
    report(
        54,
        {
            **u.m12.fictional_manifest(generation),
            "model": "gpt-6-astra",
            "reasoning_effort": "xhigh",
            "runtime_contract": root,
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


def run():
    original_call, old_output, old_calibration = (
        u.m12._single_attempt_model_call,
        u.f.OUTPUT,
        u.f._calibration_audit,
    )
    u.m12._single_attempt_model_call, u.f.OUTPUT, u.f._calibration_audit = (
        single_attempt,
        OUTPUT,
        u.calibration_audit,
    )
    try:
        u.f.run()
    finally:
        u.m12._single_attempt_model_call, u.f.OUTPUT, u.f._calibration_audit = (
            original_call,
            old_output,
            old_calibration,
        )


def finalize():
    gate = read(OUTPUT / "phase-a-receipt.json")
    docs = [read(p) for p in sorted((OUTPUT / "model-calls").glob("**/run-document.json"))]
    receipts = [read(p) for p in sorted((OUTPUT / "model-calls").glob("**/receipt.json"))]
    rows = [{**r, "repetition": d["repetition"]} for d in docs for r in d.get("rows", [])]
    full = len(docs) == 6 and len(rows) == 24 and all(d["status"] == "PASS" for d in docs)
    stop = read(OUTPUT / "canary-stop.json") if (OUTPUT / "canary-stop.json").exists() else {}
    summary = (
        read(OUTPUT / "canary-summary.json") if (OUTPUT / "canary-summary.json").exists() else {}
    )
    for n in range(56, 62):
        report(n, {"status": "NOT_RUN", "reason": stop})
    for d in docs:
        report(56 + (d["repetition"] - 1) * 2 + d["context"] - 1, d)
    errors = [error for row in rows for error in row.get("errors", [])]
    report(
        62,
        {
            "full": full,
            "rows": rows,
            "errors": errors,
            "final_pass_count": sum(r["status"] == "PASS" for r in rows),
            "legacy_precalibration_pass_count_not_authoritative": True,
        },
    )
    report(
        63,
        {
            "full": full,
            "rows": [
                {
                    "ticker": r["ticker"],
                    "repetition": r["repetition"],
                    "claims": [
                        asdict(c) for c in u.f.candidate_financial_framework_claims(r["core"])
                    ],
                    "errors": r["errors"],
                }
                for r in rows
            ],
        },
    )
    report(
        64,
        {
            "full": full,
            "contract": read(u.ROOT)["expectation"],
            "rows": [r for r in rows if r["ticker"] == "FIC-FIN-05"],
        },
    )
    report(
        65,
        u.f.grounding._grounding_summary(rows, require_complete=full)
        if rows
        else {"status": "NOT_MEASURED"},
    )
    core, stance = [], []
    for ticker in u.m12.TICKERS:
        selected = [r["core"] for r in rows if r["ticker"] == ticker]
        values = [
            (r["overall_direction"], r["directional_balance"]["buy"], r["hold_lean"])
            for r in selected
        ]
        core.append(
            {
                "ticker": ticker,
                "values": values,
                "unique_count": len(set(values)) if full else "NOT_MEASURED",
            }
        )
        stance.append(
            {
                "ticker": ticker,
                **{
                    key: [
                        r[field]["stance"] if field != "business_thesis_change" else r[field]
                        for r in selected
                    ]
                    for key, field in (
                        ("new_buyer", "fundamental_new_buyer"),
                        ("holder", "fundamental_holder"),
                        ("business_delta", "business_thesis_change"),
                    )
                },
            }
        )
    variance = {
        key: sum(len(set(r[key])) > 1 for r in stance) if full else "NOT_MEASURED"
        for key in ("business_delta", "new_buyer", "holder")
    }
    formal = summary.get("stability", {"status": "NOT_MEASURED"})
    report(66, {"rows": stance, "business_delta_variance": variance["business_delta"]})
    report(67, formal)
    report(68, {"full": full, "rows": core})
    report(69, {"rows": stance, "variance": variance})
    elapsed = [r["elapsed_seconds"] for r in receipts if "elapsed_seconds" in r]
    runtime = {
        "model_calls_fictional": sum(r.get("model_process_spawned", False) for r in receipts),
        "model_context_success_count": sum(r["status"] == "PASS" for r in receipts),
        "model_context_failure_count": sum(r["status"] != "PASS" for r in receipts),
        "timeout_count": sum(r.get("timed_out", False) for r in receipts),
        "capacity_failure_count": sum(
            "CAPACITY" in str(r.get("failure_type")).upper() for r in receipts
        ),
        "orphan_process_count": sum(r.get("orphan_process_count", 0) for r in receipts),
        "cli_internal_retry_event_count": sum(
            r.get("cli_internal_retry_event_count", 0) for r in receipts
        ),
        "wrapper_retry_count": sum(r["wrapper_retry_count"] for r in receipts),
        "runtime_median_elapsed_seconds": statistics.median(elapsed) if elapsed else "NOT_MEASURED",
        "runtime_max_elapsed_seconds": max(elapsed) if elapsed else "NOT_MEASURED",
    }
    report(
        70,
        {
            **runtime,
            "min_seconds": min(elapsed) if elapsed else "NOT_MEASURED",
            "calls": receipts,
            "comparison_mode": "SAME_MODEL_RUNTIME_DESCRIPTIVE",
            "contract_change": "1800 ->2400, existing stream lifecycle adapter",
        },
    )
    report(71, summary.get("specificity", {"status": "NOT_MEASURED"}))
    report(
        72,
        {
            "runtime": runtime,
            "stop": stop,
            "backend_root_cause": "NOT_MEASURED",
            "code_after_generation_unchanged": all(
                Path(p).is_file() and sha(Path(p).read_bytes()) == h
                for p, h in gate["code_file_sha256"].items()
            ),
        },
    )
    runtime_pass = (
        len(receipts) == 6
        and runtime["model_context_success_count"] == 6
        and not runtime["orphan_process_count"]
    )
    all_stable = full and all(r["unique_count"] == 1 for r in core)
    ready = (
        runtime_pass
        and full
        and not errors
        and all_stable
        and not any(variance.values())
        and formal.get("status") == "PASS"
        and summary.get("status") == "PASS"
    )
    next_scope = "FRESH_REAL_FINANCIAL_CONTEXT_GENERALIZATION_PROOF_GPT6_ASTRA_XHIGH"
    status = "M12V_COMPLETE" if ready else "M12V_SEMANTIC_PROOF_FAIL"
    if runtime["model_context_failure_count"]:
        status = "M12V_RUNTIME_PROOF_FAIL"
        next_scope = "ASTRA_FINITE_2400_TAIL_TOLERANCE_ASSUMPTION_REVIEW"
    elif errors or not full:
        next_scope = "BOUNDED_DIRECTIONAL_FINANCIAL_CONTEXT_REPAIR_GPT6_ASTRA"
    elif variance["business_delta"]:
        next_scope = "BOUNDED_BUSINESS_DELTA_CONTRACT_REPAIR"
    elif variance["new_buyer"]:
        next_scope = "BOUNDED_NEW_BUYER_STANCE_CALIBRATION_REPAIR_GPT6_ASTRA"
    elif variance["holder"]:
        next_scope = "BOUNDED_HOLDER_STANCE_CALIBRATION_REPAIR_GPT6_ASTRA"
    elif not ready:
        next_scope = "BOUNDED_DIRECTIONAL_FINANCIAL_CONTEXT_REPAIR_GPT6_ASTRA"
    for n, decision in {
        73: {"status": "PASS" if runtime_pass else "NOT_FULLY_PROVEN", "runtime": runtime},
        74: {
            "status": "READY" if ready else "NOT_READY",
            "reason": "Finite-cap/no-retry integrity retained; reliability is observational, not a guarantee. No exposed-cohort retry permitted.",
        },
        75: {"status": "PASS" if full and not errors else "NOT_FULLY_PROVEN", "audit": SLUGS[63]},
        76: {"status": "PASS" if full and not errors else "NOT_FULLY_PROVEN", "audit": SLUGS[64]},
        77: {"status": "PASS" if all_stable else "NOT_FULLY_PROVEN", "rows": core},
        78: {"variance": variance["business_delta"]},
        79: {"variance": variance["new_buyer"]},
        80: {"variance": variance["holder"]},
        81: {"readiness": "READY" if ready else "NOT_READY", "next_scope": next_scope},
    }.items():
        report(n, decision)
    schedule = read(REPORTS / f"84-{SLUGS[84]}.json")
    schedule["end"] = u.stability._schedule_observation()
    report(84, schedule)
    ci = read(OUTPUT / "validation/implementation-ci.json")
    completion = {
        "base_sha": BASE,
        "work_instruction_commit": INSTRUCTION_COMMIT,
        "implementation_commit": gate["implementation_commit"],
        "report_commit": "PENDING_FINAL_COMMIT",
        "final_head_sha": "PENDING_FINAL_COMMIT",
        "branch": git("branch", "--show-current"),
        "latest_result_zip_sha256": LATEST_SHA,
        "latest_result_integrity": "PASS",
        "m12u_status": "PARTIAL_STOPPED",
        "m12v_status": status,
        "implementation_model_target": "gpt-6-astra",
        "implementation_reasoning_effort": "xhigh",
        "investment_judgment_model_target": "gpt-6-astra",
        "investment_judgment_reasoning_effort": "xhigh",
        "authoring_model_target_match": True,
        "runner_model_target_match": all(
            r.get("cli_advertised_runtime") == {"model": "gpt-6-astra", "effort": "xhigh"}
            for r in receipts
        )
        if receipts
        else "NOT_MEASURED",
        "model_target_fallback_count": 0,
        "astra_successful_historical_context_count": 5,
        "astra_timeout_historical_context_count": 2,
        "current_transport_type": "signed-in Codex CLI",
        "current_cli_version": "0.153.4",
        "current_timeout_seconds": 1800,
        "current_wrapper_retry_count": 0,
        "current_subjects_per_context": 4,
        **{f"runtime_option_{r['id'].lower()}_status": r["status"] for r in read(ROOT)["options"]},
        "preferred_runtime_architecture": read(ROOT)["preferred_runtime_architecture"],
        "runtime_code_change_count": 1,
        "existing_runtime_module_change_count": 0,
        "timeout_change_count": 1,
        "selected_timeout_seconds": 2400,
        "wrapper_retry_change_count": 0,
        "selected_wrapper_retry_count": 0,
        "context_topology_change_count": 0,
        "selected_subjects_per_context": 4,
        "event_stream_supported": True,
        "direct_transport_supported": False,
        "request_id_observable": "NOT_MEASURED",
        "response_id_observable": "NOT_MEASURED",
        "first_byte_observable": True,
        "progress_event_observable": False,
        "transport_root_cause_classification": read(ROOT)["root_cause"],
        "fictional_generation_id": gate["generation_id"],
        "source_lock_sha256": gate["source_lock_sha256"],
        "fictional_subject_count": 8,
        "fictional_context_count": 2,
        "fictional_repetition_count": 3,
        **runtime,
        "fictional_output_row_count": len(rows),
        "fictional_schema_pass_count": len(rows),
        **{
            key: "NOT_MEASURED"
            for key in (
                "hard_financial_semantic_violation_count",
                "explicit_exclusion_false_reject_count",
                "financial_sector_true_misuse_count",
                "market_expectation_leverage_target_violation_count",
                "grounding_failure_count",
                "formal_stable_count",
                "formal_boundary_uncertainty_count",
                "formal_unstable_count",
                "opposite_direction_reversal_count",
            )
        },
        **{
            f"fic_fin_{r['ticker'][-2:]}_directional_balance_unique_count": r["unique_count"]
            for r in core
            if r["ticker"] in read(ROOT)["semantic_freeze"]["target_buys"]
        },
        **{f"{key}_variance_subject_count": value for key, value in variance.items()},
        "runtime_real_holdout_suitability": "READY" if ready else "NOT_READY",
        "hosted_ci_status": ci["status"],
        "hosted_ci_failure_count": ci["failed"],
        "new_hosted_ci_failure_count": ci["new_m12v_failure_count"],
        "hosted_ci_portability_backlog_count": 5,
        **u.firewall(),
        "observed_paused_schedule_count": schedule["end"]["observed_paused_schedule_count"],
        **{
            key: gate["validations"][label]
            for key, label in (
                ("focused_test_result", "focused"),
                ("full_test_result", "full"),
                ("ruff_result", "ruff"),
                ("git_diff_check", "diff"),
            )
        },
        "artifact_count": "PENDING_EXPORT",
        "artifact_hash_mismatch_count": "PENDING_EXPORT",
        "artifact_size_mismatch_count": "PENDING_EXPORT",
        "artifact_secret_scan_failure_count": "PENDING_EXPORT",
        "fresh_real_proof_readiness": "READY" if ready else "NOT_READY",
        "production_readiness": "NOT_READY",
        "status": status,
        "stop_reason": stop.get("stop_reason"),
        "next_scope": next_scope,
    }
    if rows:
        completion["market_expectation_leverage_target_violation_count"] = sum(
            r["ticker"] == "FIC-FIN-05" and r.get("m12f_calibration", {}).get("status") == "FAIL"
            for r in rows
        )
        completion["grounding_failure_count"] = sum("ground" in str(e).lower() for e in errors)
        completion["hard_financial_semantic_violation_count"] = len(errors)
    if full:
        for label, field in (
            ("formal_stable_count", "fictional_stable_count"),
            ("formal_boundary_uncertainty_count", "fictional_boundary_uncertainty_count"),
            ("formal_unstable_count", "fictional_unstable_count"),
            ("opposite_direction_reversal_count", "opposite_direction_reversal_count"),
        ):
            completion[label] = formal.get(field, "NOT_MEASURED")
    report(
        85, {"status": "PENDING_DOCUMENTATION", "latest_state": status, "next_scope": next_scope}
    )
    report(86, completion)
    print(
        json.dumps(
            {"status": status, "calls": len(receipts), "rows": len(rows), "next_scope": next_scope}
        )
    )


def bundle():
    previous = u.t.OUTPUT, u.t.REPORTS, u.t.NAME, u.t.BASE
    u.t.OUTPUT, u.t.REPORTS, u.t.NAME, u.t.BASE = OUTPUT, REPORTS, NAME, BASE
    try:
        u.t.bundle()
    finally:
        u.t.OUTPUT, u.t.REPORTS, u.t.NAME, u.t.BASE = previous


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument(
        "command", choices=("review", "validation", "prepare", "run", "finalize", "bundle")
    )
    globals()[p.parse_args().command]()
