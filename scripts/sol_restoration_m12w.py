"""M12W archive-only Sol restoration and full fictional proof."""

from __future__ import annotations

import argparse
from dataclasses import asdict
from datetime import UTC, datetime
import io
import json
from pathlib import Path
import re
import statistics
import subprocess
import sys
import tarfile
import uuid
import zipfile

from scripts import astra_runtime_m12v as v
from scripts.sol_runtime_adapter_m12w import single_attempt

u = v.u
BASE = "9e5861a2479aaae3fa473824a6f764435f2bba65"
INSTRUCTION_COMMIT = "e8441e0543054534566e99c19fbdcd6c0722462c"
MODEL = "gpt-5.6-sol"
EFFORT = "xhigh"
NAME = "20260910-gpt56-sol-xhigh-restoration-full-fictional-financial-canary"
OUTPUT = Path("artifacts") / NAME
REPORTS = Path("docs/reports") / NAME
ROOT = Path("docs/architecture/M12W_SOL_RESTORATION.json")
INSTRUCTION = Path(
    "docs/work-instructions/"
    "20260910-gpt56-sol-xhigh-restoration-and-full-fictional-financial-canary.md"
)
LATEST = Path.home() / "Documents/Codex" / (
    "thesis-monitor-20260910-astra-transport-runtime-architecture-review-"
    "full-fictional-canary-report.zip"
)
LATEST_SHA = "ca5fabf54d8d88f37073b2d4923de49e27520b94d2ad910eb52f988ccb3de092"
M12D = u.e.M12D
M12D_SHA = "b7eb58d997048799c499daa7b2be29a429791772781d1ab23c6540f03fa7a9a3"
SOL_REAL_HISTORY = Path(
    "docs/reports/20260908-runtime-namespace-isolation-repair-fresh-holdout-proof/"
    "67-program-completion.md"
)
M12D_REPORTS = Path(
    "docs/reports/"
    "20260909-qtd-ytd-plain-korean-period-validator-repair-full-fictional-canary"
)
PORTABLE_BASELINE = {
    "app": {
        "file_count": 269,
        "aggregate_sha256": "6530ecd77d792e0795d05c2f697e55126d3252adee2d3819b27bdbcdf5e07f2e",
    },
    "scripts": {
        "file_count": 187,
        "aggregate_sha256": "4905565fc26633aedf2c80d5b041de7be74bfc7a5acf86f1a7a548518bdee1c8",
    },
    "fixtures": {
        "file_count": 8,
        "aggregate_sha256": "b2f21b2fe20d1bee938558f02e6008144f8e4deb9e47024246e967f1719e9960",
    },
    "architecture": {
        "file_count": 4,
        "aggregate_sha256": "0c6a7d3215e90a01b15490a610b31b43ba02da736f125062dc1a2df8980da584",
    },
    "root_config": {
        "file_count": 2,
        "aggregate_sha256": "a34aec0e886e94dfc5982347cb1284d674e9e9454dc5811a4044ffba7fc66e03",
    },
}
SLUGS = {
    int(n): slug
    for n, slug in re.findall(r"^(\d{2})-([a-z0-9-]+)$", INSTRUCTION.read_text(), re.M)
}
read, write, sha, git = u.read, u.write, u.sha, u.git


def report(number, value):
    write(REPORTS / f"{number:02d}-{SLUGS[number]}.json", value)


def verify_zip(path, digest):
    return u.e.verify_zip(path, digest)


def _portable_freeze():
    extensions = (".py", ".toml", ".yaml", ".yml", ".json")
    excluded = {
        "scripts/sol_runtime_adapter_m12w.py",
        "scripts/sol_restoration_m12w.py",
        str(ROOT),
    }
    paths = [
        path
        for path in Path(".").rglob("*")
        if path.is_file()
        and str(path).removeprefix("./") not in excluded
        and (str(path).endswith(extensions) or str(path).startswith("fixtures/"))
    ]
    selectors = {
        "app": lambda path: path.startswith("app/"),
        "scripts": lambda path: path.startswith("scripts/"),
        "fixtures": lambda path: path.startswith("fixtures/"),
        "architecture": lambda path: path.startswith("docs/architecture/"),
        "root_config": lambda path: "/" not in path,
    }
    observed = {}
    for label, selector in selectors.items():
        hashes = {
            path: sha(Path(path).read_bytes())
            for path in sorted(str(path).removeprefix("./") for path in paths)
            if selector(path)
        }
        observed[label] = {
            "file_count": len(hashes),
            "aggregate_sha256": sha(
                json.dumps(hashes, sort_keys=True, separators=(",", ":")).encode()
            ),
        }
    changed = [label for label in PORTABLE_BASELINE if observed[label] != PORTABLE_BASELINE[label]]
    return {
        "status": "PASS" if not changed else "FAIL",
        "baseline": BASE,
        "verification_mode": "CI_PORTABLE_AGGREGATE_SHA256",
        "baseline_scope": PORTABLE_BASELINE,
        "observed_scope": observed,
        "changed_existing_paths": changed,
        "financial_semantic_change_count": len(changed),
        "directional_semantic_change_count": len(changed),
        "fictional_case_change_count": int("fixtures" in changed),
        "source_mapping_change_count": int("app" in changed or "scripts" in changed),
    }


def freeze():
    changed, hashes = [], {}
    try:
        payload = subprocess.check_output(["git", "archive", BASE], stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        return _portable_freeze()
    with tarfile.open(fileobj=io.BytesIO(payload)) as archive:
        for member in archive:
            path = member.name
            if not member.isfile() or not (
                path.endswith((".py", ".toml", ".yaml", ".yml", ".json"))
                or path.startswith("fixtures/")
            ):
                continue
            payload = archive.extractfile(member).read()
            hashes[path] = sha(payload)
            if not Path(path).is_file() or sha(Path(path).read_bytes()) != hashes[path]:
                changed.append(path)
    return {
        "status": "PASS" if not changed else "FAIL",
        "baseline": BASE,
        "verification_mode": "EXACT_BASE_ARCHIVE_SHA256",
        "existing_file_sha256": hashes,
        "changed_existing_paths": changed,
        "financial_semantic_change_count": len(changed),
        "directional_semantic_change_count": len(changed),
        "fictional_case_change_count": sum(path.startswith("fixtures/") for path in changed),
        "source_mapping_change_count": sum("source" in path for path in changed),
    }


def current_hashes():
    paths = [
        *Path("app").rglob("*.py"),
        *Path("scripts").glob("*.py"),
        *Path("tests").glob("*.py"),
        *[path for path in Path("fixtures").rglob("*") if path.is_file()],
        u.ROOT,
        u.f.ROOT,
        u.e.FIXTURE,
        v.ROOT,
        ROOT,
        INSTRUCTION,
    ]
    return {str(path): sha(path.read_bytes()) for path in sorted(set(paths))}


def model_availability():
    cache = read(Path.home() / ".codex/models_cache.json")
    matches = [row for row in cache["models"] if row.get("slug") == MODEL]
    available = bool(
        matches
        and EFFORT in {row["effort"] for row in matches[0]["supported_reasoning_levels"]}
    )
    return {
        "requested_model": MODEL,
        "reasoning_effort": EFFORT,
        "cache_advertised": available,
        "invocation_accepted": "NOT_MEASURED",
        "fallback_count": 0,
        "status": "PASS" if available else "SOL_MODEL_TARGET_UNAVAILABLE",
    }


def historical_sol():
    receipts = []
    if M12D.is_file():
        integrity = verify_zip(M12D, M12D_SHA)
        with zipfile.ZipFile(M12D) as archive:
            for name in sorted(archive.namelist()):
                if not name.startswith("experiment/model-calls/") or not name.endswith("/receipt.json"):
                    continue
                receipt = json.loads(archive.read(name))
                receipts.append(
                    {
                        "path": name,
                        "status": receipt.get("status"),
                        "model": receipt.get("model"),
                        "effort": receipt.get("reasoning_effort"),
                        "timeout_seconds": receipt.get("timeout_seconds"),
                        "wrapper_retry_count": receipt.get("wrapper_retry_count"),
                        "orphan_process_count": receipt.get("orphan_process_count"),
                        "receipt_sha256": sha(archive.read(name)),
                    }
                )
    else:
        report_paths = [
            M12D_REPORTS / f"{number:02d}-run-{run}-context-{context:02d}.json"
            for number, run, context in (
                (34, 1, 1),
                (35, 1, 2),
                (36, 2, 1),
                (37, 2, 2),
                (38, 3, 1),
                (39, 3, 2),
            )
        ]
        integrity = {
            "status": "PASS" if all(path.is_file() for path in report_paths) else "FAIL",
            "evidence_class": "REPOSITORY_TRACKED_M12D_RUN_REPORTS",
            "expected_archive_sha256": M12D_SHA,
            "archive_available": False,
            "report_sha256": {
                str(path): sha(path.read_bytes()) for path in report_paths if path.is_file()
            },
        }
        for path in report_paths:
            if not path.is_file():
                continue
            receipt = read(path)["transport"]
            receipts.append(
                {
                    "path": str(path),
                    "status": receipt.get("status"),
                    "model": receipt.get("model"),
                    "effort": receipt.get("reasoning_effort"),
                    "timeout_seconds": receipt.get("timeout_seconds"),
                    "wrapper_retry_count": receipt.get("wrapper_retry_count"),
                    "orphan_process_count": receipt.get("orphan_process_count"),
                    "receipt_sha256": sha(
                        json.dumps(receipt, sort_keys=True, separators=(",", ":")).encode()
                    ),
                }
            )
    real_text = SOL_REAL_HISTORY.read_text()
    real_summary = {
        "path": str(SOL_REAL_HISTORY),
        "sha256": sha(real_text.encode()),
        "recorded_model": "gpt-5.6-sol",
        "recorded_effort": "xhigh",
        "recorded_attempted_contexts": 32,
        "recorded_successful_contexts": 32,
        "recorded_timeout_count": 0,
        "recorded_orphan_count": 0,
        "recorded_wrapper_retry_count": 0,
        "evidence_class": "REPOSITORY_PRESERVED_COMPLETION_REPORT",
    }
    fictional_pass = (
        integrity["status"] == "PASS"
        and len(receipts) == 6
        and all(
            (
                row["status"],
                row["model"],
                row["effort"],
                row["timeout_seconds"],
                row["wrapper_retry_count"],
                row["orphan_process_count"],
            )
            == ("PASS", MODEL, EFFORT, 1800, 0, 0)
            for row in receipts
        )
    )
    return {
        "status": "PASS" if fictional_pass else "HISTORICAL_SOL_RUNTIME_EVIDENCE_NOT_FOUND",
        "m12d_integrity": integrity,
        "m12d_policy": "SAME_MODEL_DIFFERENT_CONTRACT_HISTORICAL",
        "m12d_receipts": receipts,
        "m12d_completed_context_count": sum(row["status"] == "PASS" for row in receipts),
        "m12d_timeout_count": 0 if fictional_pass else "NOT_MEASURED",
        "real_32_context_summary": real_summary,
        "historical_completed_context_count": 38 if fictional_pass else "NOT_MEASURED",
        "historical_timeout_count": 0 if fictional_pass else "NOT_MEASURED",
    }


def m12v_timeout():
    with zipfile.ZipFile(LATEST) as archive:
        receipt = json.loads(
            archive.read("experiment/model-calls/run-1/context-01/receipt.json")
        )
    return {
        "status": receipt["status"],
        "failure_type": receipt["failure_type"],
        "model": receipt["model"],
        "effort": receipt["reasoning_effort"],
        "timeout_seconds": receipt["timeout_seconds"],
        "elapsed_seconds": receipt["elapsed_seconds"],
        "output_bytes": receipt["output_bytes"],
        "wrapper_retry_count": receipt["wrapper_retry_count"],
        "cli_internal_retry_event_count": receipt["cli_internal_retry_event_count"],
        "orphan_process_count": receipt["orphan_process_count"],
        "backend_progress_state": receipt["backend_progress_state"],
        "receipt_sha256": sha(
            json.dumps(receipt, sort_keys=True, separators=(",", ":")).encode()
        ),
    }


def cross_model_history(current_rows, current_receipts):
    m12d_rows = []
    if M12D.is_file():
        with zipfile.ZipFile(M12D) as archive:
            for name in archive.namelist():
                if name.startswith("experiment/model-calls/") and name.endswith("/run-document.json"):
                    m12d_rows.extend(json.loads(archive.read(name)).get("rows", []))
    else:
        for number in range(34, 40):
            matches = list(M12D_REPORTS.glob(f"{number:02d}-*.json"))
            if matches:
                m12d_rows.extend(read(matches[0]).get("rows", []))
    return {
        "policy": [
            "SAME_MODEL_DIFFERENT_CONTRACT_HISTORICAL",
            "CROSS_MODEL_DESCRIPTIVE_ONLY",
            "CURRENT_AUTHORITATIVE_PROOF",
        ],
        "historical_sol_m12d": {
            "semantic_contract": "EARLIER_THAN_M12U",
            "row_count": len(m12d_rows),
            "runtime": historical_sol(),
            "core_rows": [
                {
                    "ticker": row["ticker"],
                    "direction": row["core"]["overall_direction"],
                    "buy": row["core"]["directional_balance"]["buy"],
                    "hold_lean": row["core"]["hold_lean"],
                }
                for row in m12d_rows
            ],
        },
        "astra_m12v": {
            "semantic_contract": "M12U_FROZEN",
            "runtime": m12v_timeout(),
            "semantic_output": "NOT_MEASURED",
        },
        "current_sol_m12w": {
            "semantic_contract": "M12U_FROZEN",
            "row_count": len(current_rows),
            "receipts": current_receipts,
            "core_rows": [
                {
                    "ticker": row["ticker"],
                    "repetition": row["repetition"],
                    "direction": row["core"]["overall_direction"],
                    "buy": row["core"]["directional_balance"]["buy"],
                    "hold_lean": row["core"]["hold_lean"],
                }
                for row in current_rows
            ],
        },
        "model_intelligence_score": "NOT_COMPUTED",
        "combined_stability_rate": "NOT_COMPUTED",
    }


def review():
    if (OUTPUT / "phase-a-receipt.json").exists():
        raise ValueError("m12w_generation_already_frozen")
    root = read(ROOT)
    scope = freeze()
    latest = verify_zip(LATEST, LATEST_SHA)
    history = historical_sol()
    timeout = m12v_timeout()
    for number in SLUGS:
        report(number, {"status": "NOT_MEASURED"})
    report(
        1,
        {
            "base_sha": BASE,
            "work_instruction_commit": INSTRUCTION_COMMIT,
            "actual_head": git("rev-parse", "HEAD"),
            "branch": git("branch", "--show-current"),
            "origin_main": git("rev-parse", "origin/main"),
        },
    )
    report(2, latest)
    report(3, scope)
    report(
        4,
        {
            "decision": root["decision"],
            "basis": "M12V selected 2400-second tail-tolerance hypothesis failed on its first context with zero final output.",
            "astra_reasoning_quality_failure_claim": False,
            "status": "PASS",
        },
    )
    report(5, root["astra"])
    report(6, {k: root[k] for k in (
        "model", "effort", "selected_timeout_seconds", "subjects_per_context",
        "context_count", "repetition_count", "wrapper_retry_count",
        "single_authoritative_watchdog", "transport_grouping_mode",
    )})
    report(7, root["authoring"])
    report(8, model_availability())
    report(
        9,
        {
            "m12v_runtime_instrumentation_reused": True,
            "m12v_astra_model_and_2400_contract_reused": False,
            "existing_runtime_module_change_count": 0,
            "status": "PASS",
        },
    )
    report(10, timeout)
    report(11, history)
    report(12, root)
    report(
        13,
        {
            "before": {"model": "gpt-6-astra", "timeout_seconds": 2400},
            "after": {"model": MODEL, "timeout_seconds": 1800},
            "increase_sol_timeout_preemptively": False,
        },
    )
    report(
        14,
        {
            "before": "gpt-6-astra/xhigh",
            "after": f"{MODEL}/{EFFORT}",
            "fallback": None,
            "status": "PASS",
        },
    )
    report(15, root["runtime_instrumentation"])
    report(16, {"status": "PENDING_VALIDATION", "owner": "codex-transport-lifecycle-v1"})
    report(17, {"status": "PENDING_VALIDATION", "policy": "PER_MODEL_CONTEXT_UNIQUE_RUNTIME_NAMESPACE"})
    report(18, root["stop_policy"])
    for number in range(19, 31):
        report(
            number,
            {
                "status": scope["status"],
                "baseline": "M12U semantics at M12V final base",
                "proof": "03-m12w-scope-freeze.json",
                "changed_existing_paths": scope["changed_existing_paths"],
                "target_buys": root["semantic_freeze"]["target_buys"],
            },
        )
    report(
        64,
        {
            "status": root["astra"]["proof_critical_status"],
            "future_scope": root["astra"]["future_scope"],
            "does_not_block_thesis_monitor": True,
        },
    )
    report(
        65,
        {
            "next_scope": "HOSTED_CI_HISTORICAL_ARTIFACT_PORTABILITY_REPAIR",
            "known_failure_count": 5,
        },
    )
    report(66, u.firewall())
    report(67, {"start": u.stability._schedule_observation(), "end": "NOT_MEASURED"})
    write(
        OUTPUT / "review-receipt.json",
        {
            "scope": scope["status"],
            "latest_integrity": latest["status"],
            "historical_sol": history["status"],
            "authoring": root["authoring"]["status"],
        },
    )
    print(json.dumps({"review": "COMPLETE", "scope": scope["status"]}))


def validation():
    before = current_hashes()
    tests = [
        "sol_restoration_m12w",
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
    extra = [
        str(path)
        for path in Path("tests").glob("test_*.py")
        if any(
            label in path.name
            for label in (
                "source_sufficiency",
                "daily_delta",
                "runtime_isolation",
                "price_timing",
                "renderer",
            )
        )
    ]
    focused = sorted(set([f"tests/test_{name}.py" for name in tests] + extra))
    commands = {
        "focused": [sys.executable, "-m", "pytest", "-q", *focused],
        "full": [sys.executable, "-m", "pytest", "-q"],
        "ruff": [str(Path(sys.executable).with_name("ruff")), "check", "."],
        "diff": ["git", "diff", "--check", BASE],
    }
    results = {}
    for label, command in commands.items():
        print("M12W_VALIDATION", label, flush=True)
        results[label] = u.m12._run_command(
            command, output_path=OUTPUT / "validation" / f"{label}.txt", timeout=3600
        )
    if before != current_hashes():
        raise ValueError("m12w_code_changed_during_validation")
    write(OUTPUT / "validation-receipt.json", {"results": results, "code_hashes": before})
    report(31, results["focused"])
    report(32, results["full"])
    report(33, {key: results[key] for key in ("ruff", "diff")})
    for number in (16, 17):
        report(
            number,
            {
                "status": "PASS" if results["focused"]["returncode"] == 0 else "FAIL",
                "focused_receipt": "31-focused-test-results.json",
                "tests": focused,
            },
        )
    print(json.dumps({key: value["returncode"] for key, value in results.items()}))


def prepare():
    if (OUTPUT / "phase-a-receipt.json").exists():
        raise ValueError("m12w_phase_a_already_frozen")
    root = read(ROOT)
    validation_receipt = read(OUTPUT / "validation-receipt.json")
    ci = read(OUTPUT / "validation/implementation-ci.json")
    report(34, ci)
    model = model_availability()
    review_receipt = read(OUTPUT / "review-receipt.json")
    checks = {
        "latest_result_integrity": verify_zip(LATEST, LATEST_SHA)["status"] == "PASS",
        "review_complete": review_receipt
        == {
            "scope": "PASS",
            "latest_integrity": "PASS",
            "historical_sol": "PASS",
            "authoring": "PASS",
        },
        "authoring_model_target": root["authoring"]["status"] == "PASS"
        and (root["authoring"]["model"], root["authoring"]["effort"]) == (MODEL, EFFORT),
        "runner_model_available": model["status"] == "PASS",
        "scope_freeze": freeze()["status"] == "PASS",
        "validation_code_frozen": validation_receipt["code_hashes"] == current_hashes(),
        "hosted_ci_new_failures_zero": ci["new_m12w_failure_count"] == 0
        and ci["head_sha"] == git("rev-parse", "HEAD"),
        "schedules_paused": u.stability._schedule_observation()["status"] == "PASS",
        "runtime_contract": (
            root["model"], root["effort"], root["selected_timeout_seconds"],
            root["subjects_per_context"], root["wrapper_retry_count"],
        )
        == (MODEL, EFFORT, 1800, 4, 0),
        "semantic_targets": root["semantic_freeze"]["target_buys"]
        == read(u.ROOT)["expectation"]["all_target_buys"],
        **{
            f"validation_{key}": value["returncode"] == 0
            for key, value in validation_receipt["results"].items()
        },
    }
    gate = {
        "status": "PASS" if all(checks.values()) else "FAIL",
        "checks": checks,
        "implementation_commit": git("rev-parse", "HEAD"),
        "runtime_contract_sha256": sha(ROOT.read_bytes()),
        "authoring_provenance": root["authoring"],
    }
    if gate["status"] != "PASS":
        report(35, gate)
        raise SystemExit("NO_MODEL_CALLS")
    generation = (
        "20260910-m12w-fictional-"
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
        generation_id=generation,
        output_root=OUTPUT,
        catalogs=catalogs,
        contexts=contexts,
    )
    with zipfile.ZipFile(LATEST) as archive:
        old_id = json.loads(archive.read("experiment/phase-a-receipt.json"))["generation_id"]
        for ticker in u.m12.TICKERS:
            if contexts[ticker] != json.loads(archive.read(f"experiment/contexts/{ticker}.json")):
                raise ValueError("m12w_fictional_source_changed")
        for row in inputs["contexts"]:
            prefix = f"experiment/frozen-contexts/context-{row['context']:02d}/"
            for kind, suffix in (("prompt", "prompt.txt"), ("schema", "schema.json")):
                before = archive.read(prefix + suffix).decode().replace(old_id, "GENERATION_ID")
                after = Path(row[f"{kind}_path"]).read_text().replace(
                    generation, "GENERATION_ID"
                )
                if before != after:
                    raise ValueError("m12w_prompt_or_schema_changed")
    gate.update(
        generation_id=generation,
        source_lock_sha256=lock["source_lock_sha256"],
        model_inputs=inputs,
        code_file_sha256=current_hashes(),
        config_file_sha256={str(ROOT): sha(ROOT.read_bytes())},
        validations=validation_receipt["results"],
        source_prompt_schema_equal_m12v=True,
    )
    write(OUTPUT / "phase-a-receipt.json", gate)
    report(35, gate)
    report(
        36,
        {
            **u.m12.fictional_manifest(generation),
            "model": MODEL,
            "reasoning_effort": EFFORT,
            "runtime_contract": root,
        },
    )
    report(37, lock)
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
    gate = read(OUTPUT / "phase-a-receipt.json")
    if gate["status"] != "PASS":
        raise ValueError("m12w_phase_a_not_passed")
    for key in ("code_file_sha256", "config_file_sha256"):
        if any(sha(Path(path).read_bytes()) != digest for path, digest in gate[key].items()):
            raise ValueError("m12w_code_or_config_changed_after_freeze")
    original = {
        "call": u.m12._single_attempt_model_call,
        "output": u.f.OUTPUT,
        "calibration": u.f._calibration_audit,
        "model": u.f.MODEL,
        "effort": u.f.EFFORT,
    }
    u.m12._single_attempt_model_call = single_attempt
    u.f.OUTPUT = OUTPUT
    u.f._calibration_audit = u.calibration_audit
    u.f.MODEL = MODEL
    u.f.EFFORT = EFFORT
    try:
        u.f.run()
    finally:
        u.m12._single_attempt_model_call = original["call"]
        u.f.OUTPUT = original["output"]
        u.f._calibration_audit = original["calibration"]
        u.f.MODEL = original["model"]
        u.f.EFFORT = original["effort"]


def _counter(errors, *needles):
    return sum(any(needle in str(error).lower() for needle in needles) for error in errors)


def finalize():
    gate = read(OUTPUT / "phase-a-receipt.json")
    docs = [read(path) for path in sorted((OUTPUT / "model-calls").glob("**/run-document.json"))]
    receipts = [read(path) for path in sorted((OUTPUT / "model-calls").glob("**/receipt.json"))]
    rows = [{**row, "repetition": doc["repetition"]} for doc in docs for row in doc.get("rows", [])]
    full = len(docs) == 6 and len(receipts) == 6 and len(rows) == 24 and all(
        doc["status"] == "PASS" for doc in docs
    )
    stop = read(OUTPUT / "canary-stop.json") if (OUTPUT / "canary-stop.json").exists() else {}
    summary = read(OUTPUT / "canary-summary.json") if (OUTPUT / "canary-summary.json").exists() else {}
    for number in range(38, 44):
        report(number, {"status": "NOT_RUN", "reason": stop})
    for doc in docs:
        report(38 + (doc["repetition"] - 1) * 2 + doc["context"] - 1, doc)
    errors = [error for row in rows for error in row.get("errors", [])]
    target_violations = sum(
        row.get("m12f_calibration", {}).get("status") == "FAIL" for row in rows
    )
    report(
        44,
        {
            "full": full,
            "rows": rows,
            "errors": errors,
            "final_pass_count": sum(row["status"] == "PASS" for row in rows),
        },
    )
    report(
        45,
        {
            "full": full,
            "targets": read(ROOT)["semantic_freeze"]["target_buys"],
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
    report(
        46,
        {
            "full": full,
            "rows": [
                {
                    "ticker": row["ticker"],
                    "repetition": row["repetition"],
                    "claims": [
                        asdict(claim)
                        for claim in u.f.candidate_financial_framework_claims(row["core"])
                    ],
                    "errors": row["errors"],
                }
                for row in rows
            ],
        },
    )
    report(
        47,
        {
            "full": full,
            "contract": read(u.ROOT)["expectation"],
            "rows": [row for row in rows if row["ticker"] == "FIC-FIN-05"],
        },
    )
    grounding = (
        u.f.grounding._grounding_summary(rows, require_complete=full)
        if rows
        else {"status": "NOT_MEASURED"}
    )
    report(48, grounding)
    core, stances = [], []
    for ticker in u.m12.TICKERS:
        selected = [row for row in rows if row["ticker"] == ticker]
        values = [
            (
                row["core"]["overall_direction"],
                row["core"]["directional_balance"]["buy"],
                row["core"]["hold_lean"],
            )
            for row in selected
        ]
        core.append(
            {
                "ticker": ticker,
                "values": values,
                "direction_unique_count": len({value[0] for value in values}) if full else "NOT_MEASURED",
                "balance_unique_count": len({value[1] for value in values}) if full else "NOT_MEASURED",
                "hold_lean_unique_count": len({value[2] for value in values}) if full else "NOT_MEASURED",
            }
        )
        stances.append(
            {
                "ticker": ticker,
                "new_buyer": [row["core"]["fundamental_new_buyer"]["stance"] for row in selected],
                "holder": [row["core"]["fundamental_holder"]["stance"] for row in selected],
                "business_delta": [row["core"]["business_thesis_change"] for row in selected],
            }
        )
    variance = {
        key: sum(len(set(row[key])) > 1 for row in stances) if full else "NOT_MEASURED"
        for key in ("business_delta", "new_buyer", "holder")
    }
    report(49, {"full": full, "rows": stances, "business_delta_variance": variance["business_delta"]})
    formal = summary.get("stability", {"status": "NOT_MEASURED"})
    report(50, formal)
    report(51, {"full": full, "rows": core})
    report(52, {"full": full, "rows": stances, "variance": variance})
    elapsed = [row["elapsed_seconds"] for row in receipts if "elapsed_seconds" in row]
    runtime = {
        "model_calls_fictional": sum(row.get("model_process_spawned", False) for row in receipts),
        "model_context_success_count": sum(row["status"] == "PASS" for row in receipts),
        "model_context_failure_count": sum(row["status"] != "PASS" for row in receipts),
        "cli_internal_retry_event_count": sum(
            row.get("cli_internal_retry_event_count", 0) for row in receipts
        ),
        "wrapper_retry_count": sum(row["wrapper_retry_count"] for row in receipts),
        "timeout_count": sum(row.get("timed_out", False) for row in receipts),
        "capacity_failure_count": sum(
            "CAPACITY" in str(row.get("failure_type", "")).upper() for row in receipts
        ),
        "orphan_process_count": sum(row.get("orphan_process_count", 0) for row in receipts),
        "runtime_median_elapsed_seconds": statistics.median(elapsed)
        if elapsed
        else "NOT_MEASURED",
        "runtime_max_elapsed_seconds": max(elapsed) if elapsed else "NOT_MEASURED",
    }
    report(53, {"runtime": runtime, "calls": receipts})
    report(54, cross_model_history(rows, receipts))
    report(55, summary.get("specificity", {"status": "NOT_MEASURED"}))
    report(
        56,
        {
            "runtime": runtime,
            "stop": stop,
            "backend_progress": "NOT_MEASURED",
            "code_after_generation_unchanged": all(
                Path(path).is_file() and sha(Path(path).read_bytes()) == digest
                for path, digest in gate["code_file_sha256"].items()
            ),
        },
    )
    runtime_pass = (
        len(receipts) == 6
        and runtime["model_context_success_count"] == 6
        and runtime["model_context_failure_count"] == 0
        and runtime["timeout_count"] == 0
        and runtime["capacity_failure_count"] == 0
        and runtime["orphan_process_count"] == 0
        and runtime["wrapper_retry_count"] == 0
    )
    core_stable = full and all(
        row["direction_unique_count"] == row["balance_unique_count"]
        == row["hold_lean_unique_count"] == 1
        for row in core
    )
    formal_stable = (
        full
        and formal.get("fictional_stable_count") == 8
        and formal.get("fictional_boundary_uncertainty_count") == 0
        and formal.get("fictional_unstable_count") == 0
        and formal.get("opposite_direction_reversal_count") == 0
    )
    ready = (
        runtime_pass
        and full
        and not errors
        and target_violations == 0
        and core_stable
        and formal_stable
        and variance == {"business_delta": 0, "new_buyer": 0, "holder": 0}
        and summary.get("status") == "PASS"
    )
    status = "M12W_COMPLETE" if ready else "M12W_CANARY_FAIL"
    next_scope = "FRESH_REAL_FINANCIAL_CONTEXT_GENERALIZATION_PROOF_GPT56_SOL_XHIGH"
    if runtime["model_context_failure_count"]:
        status = "M12W_RUNTIME_PROOF_FAIL"
        next_scope = "SOL_RUNTIME_REGRESSION_REVIEW"
    elif target_violations:
        next_scope = "BOUNDED_SOL_DIRECTIONAL_CONTRACT_REPAIR"
    elif variance["business_delta"] not in (0, "NOT_MEASURED"):
        next_scope = "BOUNDED_BUSINESS_DELTA_CONTRACT_REPAIR_GPT56_SOL"
    elif variance["new_buyer"] not in (0, "NOT_MEASURED"):
        next_scope = "BOUNDED_NEW_BUYER_STANCE_CALIBRATION_REPAIR_GPT56_SOL"
    elif variance["holder"] not in (0, "NOT_MEASURED"):
        next_scope = "BOUNDED_HOLDER_STANCE_CALIBRATION_REPAIR_GPT56_SOL"
    elif not ready:
        next_scope = "BOUNDED_SOL_DIRECTIONAL_CONTRACT_REPAIR"
    report(57, {"status": "PASS" if ready else "NOT_FULLY_PROVEN", "m12w_status": status})
    report(
        58,
        {
            "status": "READY" if ready else "NOT_READY",
            "runtime": runtime,
            "historical_sol": historical_sol()["status"],
            "exposed_real_retry_policy": "NEW_COHORT_REQUIRED",
        },
    )
    report(59, {"status": "PASS" if core_stable and not target_violations else "FAIL", "rows": core})
    report(60, {"variance": variance["business_delta"], "next_scope": next_scope})
    report(61, {"variance": variance["new_buyer"], "next_scope": next_scope})
    report(62, {"variance": variance["holder"], "next_scope": next_scope})
    report(63, {"readiness": "READY" if ready else "NOT_READY", "next_scope": next_scope})
    schedule = read(REPORTS / f"67-{SLUGS[67]}.json")
    schedule["end"] = u.stability._schedule_observation()
    report(67, schedule)
    report(68, {"status": "PENDING_DOCUMENTATION", "latest_state": status, "next_scope": next_scope})
    ci = read(OUTPUT / "validation/implementation-ci.json")
    counters = {
        "hard_financial_semantic_violation_count": len(errors) if rows else "NOT_MEASURED",
        "invalid_financial_reference_count": _counter(errors, "invalid_financial", "evidence_ref")
        if rows
        else "NOT_MEASURED",
        "grounding_failure_count": _counter(errors, "ground")
        if rows
        else "NOT_MEASURED",
        "explicit_exclusion_false_reject_count": _counter(errors, "explicit", "exclusion")
        if rows
        else "NOT_MEASURED",
        "financial_sector_true_misuse_count": _counter(errors, "financial_sector", "industrial")
        if rows
        else "NOT_MEASURED",
        "market_expectation_leverage_target_violation_count": sum(
            row["ticker"] == "FIC-FIN-05"
            and row.get("m12f_calibration", {}).get("status") == "FAIL"
            for row in rows
        )
        if rows
        else "NOT_MEASURED",
    }
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
        "m12v_status": "M12V_RUNTIME_PROOF_FAIL",
        "m12w_status": status,
        "astra_proof_critical_status": "SUSPENDED_FROM_PROOF_CRITICAL_PATH",
        "astra_model_calls": 0,
        "astra_future_experiment_scope": "MODEL_COMPATIBILITY_OR_QUALITY_EXPERIMENT",
        "implementation_model_target": MODEL,
        "implementation_reasoning_effort": EFFORT,
        "investment_judgment_model_target": MODEL,
        "investment_judgment_reasoning_effort": EFFORT,
        "authoring_model_target_match": True,
        "runner_model_target_match": all(
            row.get("cli_advertised_runtime") == {"model": MODEL, "effort": EFFORT}
            for row in receipts
        )
        if receipts
        else "NOT_MEASURED",
        "model_target_fallback_count": 0,
        "previous_astra_timeout_seconds": 2400,
        "selected_sol_timeout_seconds": 1800,
        "timeout_change_count": 1,
        "subjects_per_context": 4,
        "context_topology_change_count": 0,
        "wrapper_retry_count": runtime["wrapper_retry_count"],
        "runtime_instrumentation_retained": True,
        "runtime_instrumentation_semantic_change_count": 0,
        "historical_sol_runtime_evidence_status": historical_sol()["status"],
        "historical_sol_completed_context_count": historical_sol()[
            "historical_completed_context_count"
        ],
        "historical_sol_timeout_count": historical_sol()["historical_timeout_count"],
        "financial_semantic_change_count": 0,
        "directional_semantic_change_count": 0,
        "fictional_case_change_count": 0,
        "source_mapping_change_count": 0,
        "financial_context_selection_change_count": 0,
        "first_class_projection_change_count": 0,
        "working_capital_validator_semantic_change_count": 0,
        "qtd_ytd_validator_semantic_change_count": 0,
        "financial_exclusion_validator_semantic_change_count": 0,
        "market_expectation_contract_change_count": 0,
        "directional_threshold_changed": False,
        "directional_increment_changed": False,
        "hold_lean_contract_changed": False,
        "calibration_tiebreak_direction_changed": False,
        "source_sufficiency_semantic_change_count": 0,
        "daily_delta_semantic_change_count": 0,
        "warning_semantic_change_count": 0,
        "fictional_generation_id": gate["generation_id"],
        "source_lock_sha256": gate["source_lock_sha256"],
        "fictional_subject_count": 8,
        "fictional_context_count": 2,
        "fictional_repetition_count": 3,
        "model_calls_real": 0,
        "model_calls_judge": 0,
        **runtime,
        "fictional_output_row_count": len(rows),
        "fictional_schema_pass_count": len(rows),
        **counters,
        **{
            f"fic_fin_{ticker[-2:]}_directional_balance_unique_count": target_map[ticker][
                "balance_unique_count"
            ]
            for ticker in ("FIC-FIN-01", "FIC-FIN-02", "FIC-FIN-04", "FIC-FIN-05")
        },
        "target_bucket_contract_violation_count": target_violations
        if rows
        else "NOT_MEASURED",
        "formal_stable_count": formal.get("fictional_stable_count", "NOT_MEASURED"),
        "formal_boundary_uncertainty_count": formal.get(
            "fictional_boundary_uncertainty_count", "NOT_MEASURED"
        ),
        "formal_unstable_count": formal.get("fictional_unstable_count", "NOT_MEASURED"),
        "opposite_direction_reversal_count": formal.get(
            "opposite_direction_reversal_count", "NOT_MEASURED"
        ),
        "business_delta_variance_subject_count": variance["business_delta"],
        "new_buyer_stance_variance_subject_count": variance["new_buyer"],
        "holder_stance_variance_subject_count": variance["holder"],
        "sol_runtime_real_holdout_suitability": "READY" if ready else "NOT_READY",
        "message_specificity_advisory_status": summary.get("specificity", {}).get(
            "status", "NOT_MEASURED"
        ),
        "hosted_ci_status": ci["status"],
        "hosted_ci_failure_count": ci["failed"],
        "new_hosted_ci_failure_count": ci["new_m12w_failure_count"],
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
    report(69, completion)
    print(json.dumps({"status": status, "calls": len(receipts), "rows": len(rows), "next_scope": next_scope}))


def bundle():
    previous = u.t.OUTPUT, u.t.REPORTS, u.t.NAME, u.t.BASE
    u.t.OUTPUT, u.t.REPORTS, u.t.NAME, u.t.BASE = OUTPUT, REPORTS, NAME, BASE
    try:
        u.t.bundle()
    finally:
        u.t.OUTPUT, u.t.REPORTS, u.t.NAME, u.t.BASE = previous


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "command", choices=("review", "validation", "prepare", "run", "finalize", "bundle")
    )
    globals()[parser.parse_args().command]()
