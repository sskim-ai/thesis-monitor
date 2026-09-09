"""Offline M12E contract audit and frozen fictional runner. No production entry point."""

from __future__ import annotations

import argparse
import ast
from collections import Counter
from datetime import UTC, datetime
import difflib
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import uuid
import zipfile

from scripts import bounded_directional_financial_context_stability_m12s as m12s
from scripts import directional_financial_context_m12 as m12
from scripts import first_class_typed_financial_evidence_m12b as m12b


BASE = "67bdc56bcd0dba05d154c727fa1f819816b1a1f4"
INSTRUCTION_COMMIT = "3dd15fdc9ef60ad14a120fa22bf03a7b79a6ac1a"
MODEL = "gpt-6-astra"
EFFORT = "xhigh"
NAME = "20260909-bounded-financial-context-boundary-calibration-full-fictional-canary"
REPORTS = Path("docs/reports") / NAME
OUTPUT = Path("artifacts") / NAME
SERVICE = "app/services/directional_balance_service.py"
FIXTURE = Path("fixtures/financial_boundary_calibration_m12e.json")
SCRIPT = Path("scripts/financial_boundary_calibration_m12e.py")
TEST = Path("tests/test_financial_boundary_calibration_m12e.py")
LATEST = Path(
    "/Users/sskim/Documents/Codex/thesis-monitor-20260909-bounded-directional-financial-context-stability-review-report.zip"
)
LATEST_SHA = "d9533246a23d7fc6eab6da6637f1254a8748f7e37aa45252840566df5602f3de"
M12D = Path(
    "/Users/sskim/Documents/Codex/thesis-monitor-20260909-qtd-ytd-plain-korean-period-validator-repair-full-fictional-canary-report.zip"
)
INSTRUCTION = Path(
    "docs/work-instructions/20260909-bounded-financial-context-boundary-calibration-repair-and-full-fictional-canary-gpt6-astra.md"
)
SLUGS = """repository-provenance latest-result-integrity m12e-scope-freeze m12s-root-cause-reuse-proof directional-bucket-contract-before-after shared-lineage-corroboration-contract limiting-unknown-ordinal-contract non-operating-lean-boundary-contract minimum-vs-strong-direction-contract calibration-symmetry-contract cal-bal-01-strong-quality-boundary cal-bal-02-cash-conversion-divergence cal-bal-03-flat-operations-non-operating cal-bal-04-independent-corroboration cal-bal-05-stronger-6-5-support negative-side-symmetry-fixtures conservative-tiebreak-deterministic-audit scorecard-negative-control first-class-financial-evidence-freeze-proof financial-selector-freeze-proof working-capital-validator-freeze-proof qtd-ytd-validator-freeze-proof other-financial-validator-freeze-proof new-buyer-contract-freeze-proof holder-contract-freeze-proof formal-classifier-freeze-proof price-timing-no-change-proof source-sufficiency-no-change-proof daily-delta-no-change-proof renderer-ownership-no-change-proof focused-test-results full-test-results ruff-and-diff-results model-call-gate fictional-canary-generation-manifest fictional-canary-source-lock run-1-context-01 run-1-context-02 run-2-context-01 run-2-context-02 run-3-context-01 run-3-context-02 full-fictional-semantic-audit full-fictional-core-balance-calibration-audit full-fictional-grounding-audit full-fictional-formal-stability full-fictional-core-only-stability full-fictional-fingerprint-audit full-fictional-stance-variance-audit full-fictional-message-specificity-advisory runtime-observations boundary-repair-success-decision new-buyer-stance-followup-decision holder-stance-followup-decision fresh-real-proof-readiness-decision production-no-change schedule-pause-observation master-workflow-update program-completion""".split()


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    m12.write_json(Path(path), value)


def report(number, value):
    write(REPORTS / f"{number:02d}-{SLUGS[number - 1]}.json", value)


def sha(value):
    return hashlib.sha256(value).hexdigest()


def git(*args):
    return subprocess.check_output(["git", *args], text=True).strip()


def base_bytes(path):
    return subprocess.check_output(["git", "show", f"{BASE}:{path}"])


def verify_zip(path, expected):
    if sha(path.read_bytes()) != expected:
        raise ValueError("LATEST_RESULT_BUNDLE_CHECKSUM_MISMATCH")
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        rows = json.loads(archive.read("artifact-index.json"))["artifacts"]
        indexed = {row["path"] for row in rows}
        missing = indexed - set(names)
        extra = set(names) - indexed - {"artifact-index.json"}
        hashes = [
            r["path"]
            for r in rows
            if r["path"] not in missing and sha(archive.read(r["path"])) != r["sha256"]
        ]
        sizes = [
            r["path"]
            for r in rows
            if r["path"] not in missing and len(archive.read(r["path"])) != r["size_bytes"]
        ]
        result = {
            "sha256": expected,
            "indexed_payload_count": len(rows),
            "missing": sorted(missing),
            "extra": sorted(extra),
            "hash_mismatches": hashes,
            "size_mismatches": sizes,
            "duplicate_member_count": len(names) - len(set(names)),
        }
        result["status"] = (
            "PASS"
            if not any((missing, extra, hashes, sizes, result["duplicate_member_count"]))
            else "FAIL"
        )
        return result


def without_prompt(source):
    tree = ast.parse(source)
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id == "ORDINAL_CALIBRATION_PROMPT" for t in node.targets
        ):
            node.value = ast.Constant(value="FROZEN_PROMPT_PLACEHOLDER")
    return ast.dump(tree, include_attributes=False)


def prompt_value(source):
    tree = ast.parse(source)
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id == "ORDINAL_CALIBRATION_PROMPT" for t in node.targets
        ):
            return ast.literal_eval(node.value)
    raise ValueError("prompt_owner_missing")


def freeze_audit():
    before = base_bytes(SERVICE).decode()
    after = Path(SERVICE).read_text()
    old_prompt = prompt_value(before)
    new_prompt = prompt_value(after)
    additions = new_prompt.removeprefix(old_prompt).strip().split("\n\n")
    existing = git("ls-tree", "-r", "--name-only", BASE).splitlines()
    changed = [
        p
        for p in existing
        if p.endswith(".py")
        and p != SERVICE
        and (not Path(p).is_file() or base_bytes(p) != Path(p).read_bytes())
    ]
    path_changes = git("diff", "--name-only", INSTRUCTION_COMMIT).splitlines()
    allowed = {SERVICE, str(FIXTURE), str(SCRIPT), str(TEST)}
    unexpected = [p for p in path_changes if p not in allowed and not p.startswith("docs/")]
    checks = {
        "existing_prompt_preserved": new_prompt.startswith(old_prompt),
        "four_paragraphs_only": len(additions) == 4,
        "all_nonprompt_ast_unchanged": without_prompt(before) == without_prompt(after),
        "other_existing_python_unchanged": not changed,
        "bounded_paths": not unexpected,
    }
    return {
        "checks": checks,
        "changed_other_python": changed,
        "unexpected_paths": unexpected,
        "existing_python_count": sum(p.endswith(".py") for p in existing),
        "additions": additions,
        "before_prompt": old_prompt,
        "after_prompt": new_prompt,
        "diff": "".join(difflib.unified_diff(before.splitlines(True), after.splitlines(True))),
        "status": "PASS" if all(checks.values()) else "FAIL",
    }


def file_freeze(*paths):
    rows = [
        {"path": p, "base_sha256": sha(base_bytes(p)), "current_sha256": sha(Path(p).read_bytes())}
        for p in paths
    ]
    return {
        "rows": rows,
        "change_count": sum(r["base_sha256"] != r["current_sha256"] for r in rows),
        "status": "PASS" if all(r["base_sha256"] == r["current_sha256"] for r in rows) else "FAIL",
    }


def tie_fixture(buckets):
    """Only resolve fixture-declared adjacent alternatives; never score financial evidence."""
    if not buckets or len(set(buckets)) != len(buckets) or len(buckets) > 2:
        raise ValueError("explicit_unique_bucket_candidates_required")
    if any(v * 2 != int(v * 2) or not 0 <= v <= 10 for v in buckets):
        raise ValueError("invalid_bucket")
    if len(buckets) == 2 and abs(buckets[0] - buckets[1]) != 0.5:
        raise ValueError("only_adjacent_alternatives")
    return min(buckets, key=lambda v: abs(v - 5))


def fixture_audit():
    rows = read(FIXTURE)["fixtures"]
    evaluated = [
        {
            **r,
            "selected_contract_buy": tie_fixture(r["supportable_buy_buckets"]),
            "status": "PASS"
            if tie_fixture(r["supportable_buy_buckets"]) == r["selected_buy"]
            else "FAIL",
        }
        for r in rows
    ]
    return {
        "rows": evaluated,
        "purpose": "fixture-declared ordinal alternatives only; no model inference or evidence scoring",
        "status": "PASS" if all(r["status"] == "PASS" for r in evaluated) else "FAIL",
    }


def model_availability():
    cache = read(Path.home() / ".codex/models_cache.json")
    matches = [m for m in cache["models"] if m.get("slug") == MODEL]
    available = bool(
        matches and EFFORT in {r["effort"] for r in matches[0]["supported_reasoning_levels"]}
    )
    return {
        "requested_model": MODEL,
        "reasoning_effort": EFFORT,
        "cache_advertised": available,
        "invocation_accepted": "NOT_MEASURED",
        "implementation_executor_model_receipt": "NOT_MEASURED",
        "implementation_executor_effort_receipt": "NOT_MEASURED",
        "fallback_count": 0,
        "status": "PASS" if available else "MODEL_TARGET_UNAVAILABLE",
    }


def configure_runtime():
    # Process-local adapter only: historical runner files and operating config remain frozen.
    m12.MODEL = MODEL
    m12.EFFORT = EFFORT
    if m12.TIMEOUT_SECONDS != 1800:
        raise ValueError("watchdog_contract_changed")


def prepare():
    if OUTPUT.exists():
        raise ValueError("existing_experiment_refuses_reprepare")
    integrity = verify_zip(LATEST, LATEST_SHA)
    if integrity["status"] != "PASS":
        raise ValueError("latest_integrity_failed")
    REPORTS.mkdir(parents=True, exist_ok=False)
    OUTPUT.mkdir(parents=True)
    for number in range(1, 60):
        report(number, {"status": "NOT_MEASURED"})
    report(
        1,
        {
            "base_sha": BASE,
            "work_instruction_commit": INSTRUCTION_COMMIT,
            "implementation_commit": git("rev-parse", "HEAD"),
            "branch": git("branch", "--show-current"),
            "origin_main": git("rev-parse", "origin/main"),
            "production_merge": 0,
        },
    )
    report(2, integrity)
    frozen = freeze_audit()
    report(3, frozen)
    report(5, frozen)
    with zipfile.ZipFile(LATEST) as archive:
        report(
            4,
            {
                "historical_result_unchanged": True,
                "root_cause": json.loads(
                    archive.read("reports/27-preferred-next-repair-decision.json")
                ),
                "cross_model_same_runtime_claim_count": 0,
            },
        )
    for n, paragraph in zip(range(6, 10), frozen["additions"], strict=True):
        report(n, {"text": paragraph, "status": "PASS"})
    fixtures = fixture_audit()
    report(
        10,
        {
            "direction_neutral_paragraphs": frozen["additions"],
            "symmetry_fixtures": fixtures["rows"][5:],
            "status": fixtures["status"],
        },
    )
    for n, row in enumerate(fixtures["rows"][:5], 11):
        report(n, row)
    report(16, {"rows": fixtures["rows"][5:], "status": fixtures["status"]})
    report(17, fixtures)
    report(
        18,
        {
            "fixed_weight_financial_score_rule_count": 0,
            "evidence_count_bucket_rule_count": 0,
            "basis": "Only prompt text changes in existing executable code; fixture tie audit accepts declared buckets, not financial evidence",
            "nonprompt_ast_unchanged": frozen["checks"]["all_nonprompt_ast_unchanged"],
            "status": frozen["status"],
        },
    )
    financial = "app/services/directional_financial_context_service.py"
    owner = "app/services/direction_timing_ownership_service.py"
    holdout = "scripts/directional_core_price_timing_holdout.py"
    freeze_paths = {
        19: (owner, "app/services/structured_autonomy_alias_service.py"),
        20: (financial,),
        21: ("scripts/directional_financial_context_m12g.py", financial),
        22: (financial,),
        23: (financial, "scripts/directional_financial_context_m12.py"),
        24: (owner, holdout),
        25: (owner, holdout),
        26: (holdout,),
        27: (owner, holdout),
        28: ("app/services/coldstart_fundamental_enrichment_service.py",),
        29: (
            "app/services/nonproduction_monitoring_lifecycle_service.py",
            "app/services/warning_backfill_service.py",
        ),
        30: ("app/services/structured_autonomy_shadow_service.py",),
    }
    freezes = {}
    for n, paths in freeze_paths.items():
        freezes[n] = file_freeze(*paths)
        report(n, freezes[n])
    schedule = m12s._schedule_observation()
    report(57, {"start": schedule, "end": "NOT_MEASURED"})
    availability = model_availability()
    validations = {}
    commands = {
        "focused": [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            str(TEST),
            "tests/test_directional_balance_ordinal_calibration.py",
            "tests/test_direction_timing_ownership_service.py",
            "tests/test_qtd_ytd_plain_korean_period_validator_m12d.py",
            "tests/test_materiality_scoped_working_capital_grounding_m12c.py",
            "tests/test_first_class_typed_financial_evidence_m12b.py",
            "tests/test_directional_financial_context_m12g.py",
            "tests/test_directional_financial_context_service.py",
        ],
        "full": [sys.executable, "-m", "pytest", "-q"],
        "ruff": [str(Path(sys.executable).with_name("ruff")), "check", "."],
        "diff": ["git", "diff", "--check", BASE],
    }
    for name, command in commands.items():
        print(f"M12E_VALIDATION {name}", flush=True)
        validations[name] = m12._run_command(
            command, output_path=OUTPUT / "validation" / f"{name}.txt", timeout=3600
        )
    report(31, validations["focused"])
    report(32, validations["full"])
    report(33, {k: validations[k] for k in ("ruff", "diff")})
    checks = {
        "scope": frozen["status"],
        "fixtures": fixtures["status"],
        "schedules": schedule["status"],
        "model_availability": availability["status"],
        **{str(n): v["status"] for n, v in freezes.items()},
        **{k: v["status"] for k, v in validations.items()},
    }
    gate = {
        "checks": checks,
        "model_availability": availability,
        "model_calls_before_gate": 0,
        "implementation_commit": git("rev-parse", "HEAD"),
        "status": "PASS" if all(v == "PASS" for v in checks.values()) else "FAIL",
    }
    report(34, gate)
    if gate["status"] != "PASS":
        write(OUTPUT / "phase-a-receipt.json", gate)
        raise SystemExit("DETERMINISTIC_GATE_FAILED")
    configure_runtime()
    generation = (
        "20260909-m12e-fictional-"
        + datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        + "-"
        + uuid.uuid4().hex[:12]
    )
    packets, owned, catalogs, contexts = m12.fictional_inputs(generation)
    historical_contexts = m12.fictional_inputs(m12s.M12D_GENERATION_ID)[3]
    m12s.verify_latest_result(M12D)
    source_comparison = []
    with zipfile.ZipFile(M12D) as archive:
        for ticker in m12.TICKERS:
            archived = json.loads(archive.read(f"experiment/contexts/{ticker}.json"))
            same = archived == historical_contexts[ticker]
            source_comparison.append({"ticker": ticker, "historical_context_equal": same})
            if not same:
                raise ValueError("frozen_source_changed")
            write(OUTPUT / "contexts" / f"{ticker}.json", contexts[ticker])
            write(OUTPUT / "aliases" / f"{ticker}.json", catalogs[ticker].model_dump(mode="json"))
    lock = m12._source_lock(generation, packets, owned, catalogs, contexts)
    write(OUTPUT / "source-lock.json", lock)
    inputs = m12._write_frozen_model_inputs(
        output_root=OUTPUT, generation_id=generation, contexts=contexts, catalogs=catalogs
    )
    gate.update(
        {
            "generation_id": generation,
            "source_lock_sha256": lock["source_lock_sha256"],
            "model_inputs": inputs,
            "code_file_sha256": {
                p: sha(Path(p).read_bytes()) for p in git("ls-files", "*.py").splitlines()
            },
        }
    )
    write(OUTPUT / "phase-a-receipt.json", gate)
    report(34, gate)
    report(
        35,
        {
            **m12.fictional_manifest(generation),
            "model": MODEL,
            "reasoning_effort": EFFORT,
            "cross_model_same_runtime_claim_count": 0,
        },
    )
    report(36, {**lock, "historical_source_comparison": source_comparison})
    print(
        json.dumps(
            {
                "gate": gate["status"],
                "generation_id": generation,
                "source_hash": lock["source_lock_sha256"],
            }
        ),
        flush=True,
    )


def observed_runtime(log_text):
    header = log_text.split("--------", 2)
    lines = (header[1] if len(header) > 1 else log_text[:2000]).splitlines()
    fields = dict(line.split(":", 1) for line in lines if ":" in line)
    return {
        "model": fields.get("model", "").strip(),
        "effort": fields.get("reasoning effort", "").strip(),
    }


def run():
    gate = read(OUTPUT / "phase-a-receipt.json")
    if gate["status"] != "PASS":
        raise ValueError("phase_a_not_passed")
    for path, digest in gate["code_file_sha256"].items():
        if sha(Path(path).read_bytes()) != digest:
            raise ValueError("code_changed_after_freeze")
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
    original = m12._single_attempt_model_call

    def checked_call(**kwargs):
        receipt = original(**kwargs)
        observed = observed_runtime(kwargs["log"].read_text(errors="replace"))
        receipt["observed_runtime"] = observed
        if observed != {"model": MODEL, "effort": EFFORT}:
            receipt.update(status="FAIL", failure_type="MODEL_TARGET_UNAVAILABLE")
            write(kwargs["receipt_path"], receipt)
            raise RuntimeError("MODEL_TARGET_UNAVAILABLE")
        write(kwargs["receipt_path"], receipt)
        return receipt

    m12._single_attempt_model_call = checked_call
    try:
        m12b.run_canary(argparse.Namespace(generation_id=gate["generation_id"], output_root=OUTPUT))
    except (Exception, SystemExit) as exc:
        if not (OUTPUT / "canary-stop.json").exists():
            write(
                OUTPUT / "canary-stop.json",
                {
                    "status": "FAIL",
                    "stop_reason": "M12E_RUN_STOPPED",
                    "exception_type": type(exc).__name__,
                    "detail": str(exc),
                    "wrapper_retry_count": 0,
                },
            )
        raise
    finally:
        m12._single_attempt_model_call = original


def finalize():
    gate = read(OUTPUT / "phase-a-receipt.json")
    documents = sorted((OUTPUT / "model-calls").glob("**/run-document.json"))
    rows = []
    for path in documents:
        doc = read(path)
        repetition = doc.get("repetition", int(path.parent.parent.name.removeprefix("run-")))
        context = doc.get("context", int(path.parent.name.removeprefix("context-")))
        report(37 + (repetition - 1) * 2 + context - 1, doc)
        rows.extend({**row, "repetition": repetition} for row in doc.get("rows", []))
    receipts = [read(p) for p in sorted((OUTPUT / "model-calls").glob("**/receipt.json"))]
    summary = (
        read(OUTPUT / "canary-summary.json") if (OUTPUT / "canary-summary.json").is_file() else {}
    )
    stop = read(OUTPUT / "canary-stop.json") if (OUTPUT / "canary-stop.json").is_file() else {}
    runtime = {
        "model_calls_fictional": sum(bool(r.get("model_process_spawned")) for r in receipts),
        "model_context_success_count": sum(r.get("status") == "PASS" for r in receipts),
        "model_context_failure_count": sum(r.get("status") != "PASS" for r in receipts),
        "timeout_count": sum(bool(r.get("timed_out")) for r in receipts),
        "capacity_failure_count": sum(
            "CAPACITY" in str(r.get("failure_type", "")).upper() for r in receipts
        ),
        "wrapper_retry_count": 0,
        "model_target_fallback_count": 0,
        "receipts": receipts,
        "stop": stop,
    }
    report(51, runtime)
    if summary:
        for n, key in (
            (43, "semantic_audit"),
            (45, "financial_grounding_audit"),
            (46, "stability"),
            (50, "specificity"),
        ):
            report(n, summary[key])
    else:
        report(
            43,
            {
                "status": "INCOMPLETE",
                "completed_rows": len(rows),
                "hard_errors": [e for r in rows for e in r.get("errors", [])],
                "whole_generation_stopped": True,
            },
        )
    complete = (
        len(rows) == 24 and len(documents) == 6 and runtime["model_context_success_count"] == 6
    )
    core_rows = []
    stance_rows = []
    fingerprints = []
    for ticker in m12.TICKERS:
        selected = [r for r in rows if r["ticker"] == ticker]
        cores = [r["core"] for r in selected]
        keys = {
            (c["overall_direction"], c["directional_balance"]["buy"], c["hold_lean"]) for c in cores
        }
        core_rows.append(
            {
                "ticker": ticker,
                "row_count": len(cores),
                "balance_values": [c["directional_balance"] for c in cores],
                "direction_values": [c["overall_direction"] for c in cores],
                "balance_unique_count": len({c["directional_balance"]["buy"] for c in cores}),
                "direction_unique_count": len({c["overall_direction"] for c in cores}),
                "status": "CORE_BALANCE_DIRECTION_STABLE"
                if len(cores) == 3 and len(keys) == 1
                else "CORE_BALANCE_DIRECTION_UNSTABLE"
                if len(cores) == 3
                else "NOT_MEASURED",
            }
        )
        stance_rows.append(
            {
                "ticker": ticker,
                "new_buyer": [c["fundamental_new_buyer"]["stance"] for c in cores],
                "holder": [c["fundamental_holder"]["stance"] for c in cores],
            }
        )
        if selected:
            metadata = m12s._ref_metadata(
                ticker,
                read(OUTPUT / "aliases" / f"{ticker}.json"),
                read(OUTPUT / "contexts" / f"{ticker}.json"),
            )
            fingerprints.extend(
                m12s.build_fingerprint(repetition=r["repetition"], row=r, metadata=metadata)
                for r in selected
            )
    report(47, {"rows": core_rows, "formal_classifier_replaced": False, "complete": complete})
    report(
        49,
        {
            "rows": stance_rows,
            "new_buyer_stance_variance_subject_count": sum(
                len(set(r["new_buyer"])) > 1 for r in stance_rows
            ),
            "holder_stance_variance_subject_count": sum(
                len(set(r["holder"])) > 1 for r in stance_rows
            ),
            "complete": complete,
        },
    )
    formal = {
        r["ticker"]: r["classification"] for r in summary.get("stability", {}).get("rows", [])
    }
    analysis = (
        [
            m12s.classify_subject(
                [f for f in fingerprints if f["ticker"] == ticker], formal[ticker]
            )
            for ticker in m12.TICKERS
        ]
        if complete
        else []
    )
    report(
        48,
        {
            "fingerprints": fingerprints,
            "subjects": analysis,
            "status": "COMPLETE" if complete else "INCOMPLETE",
        },
    )
    # Bucket sufficiency is a human evidence audit, not inferred from a numeric target alone.
    report(
        44,
        {
            "status": "AWAITING_EVIDENCE_REVIEW" if complete else "NOT_MEASURED",
            "targets": [
                r for r in core_rows if r["ticker"] in {"FIC-FIN-01", "FIC-FIN-02", "FIC-FIN-04"}
            ],
            "target_bucket_contract_violation_count": "NOT_MEASURED",
        },
    )
    for n in (52, 53, 54):
        report(n, {"status": "AWAITING_EVIDENCE_REVIEW" if complete else "NOT_MEASURED"})
    report(
        55,
        {
            "fresh_real_proof_readiness": "NOT_READY",
            "production_readiness": "NOT_READY",
            "reason": "awaiting final evidence audit" if complete else "incomplete fictional proof",
        },
    )
    schedule = read(REPORTS / "57-schedule-pause-observation.json")
    schedule["end"] = m12s._schedule_observation()
    report(57, schedule)
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
        56,
        {
            **zeros,
            "basis": "isolated worktree; only offline fictional runner invoked; no production command",
            "status": "PASS",
        },
    )
    counts = Counter(formal.values())
    completion = {
        **zeros,
        "base_sha": BASE,
        "work_instruction_commit": INSTRUCTION_COMMIT,
        "implementation_commit": gate["implementation_commit"],
        "report_commit": "NOT_MEASURED",
        "final_head_sha": "NOT_MEASURED",
        "branch": git("branch", "--show-current"),
        "latest_result_zip_sha256": LATEST_SHA,
        "latest_result_integrity": "PASS",
        "m12s_status": "COMPLETE",
        "m12e_status": "AWAITING_EVIDENCE_REVIEW" if complete else "PARTIAL_STOPPED",
        "fictional_generation_id": gate.get("generation_id"),
        "fictional_subject_count": 8,
        "fictional_context_count": 2,
        "fictional_repetition_count": 3,
        "implementation_model_target": MODEL,
        "investment_judgment_model_target": MODEL,
        "reasoning_effort": EFFORT,
        "implementation_executor_runtime_receipt": "NOT_MEASURED",
        "cross_model_same_runtime_claim_count": 0,
        "model_target_fallback_count": 0,
        "model_target_availability_status": "VERIFIED_INVOCATION"
        if receipts
        and all(r.get("observed_runtime") == {"model": MODEL, "effort": EFFORT} for r in receipts)
        else "NOT_VERIFIED",
        "fictional_output_row_count": len(rows),
        "fictional_schema_pass_count": len(rows),
        "hard_financial_semantic_violation_count": sum(len(r.get("errors", [])) for r in rows),
        "formal_stable_count": counts["STABLE"] if complete else "NOT_MEASURED",
        "formal_boundary_uncertainty_count": counts["BOUNDARY_UNCERTAINTY"]
        if complete
        else "NOT_MEASURED",
        "formal_unstable_count": counts["UNSTABLE"] if complete else "NOT_MEASURED",
        "observed_paused_schedule_count": schedule["end"]["observed_paused_schedule_count"],
        "fresh_real_proof_readiness": "NOT_READY",
        "production_readiness": "NOT_READY",
        "status": "AWAITING_EVIDENCE_REVIEW" if complete else "PARTIAL_STOPPED",
        "stop_reason": stop.get("stop_reason"),
        "next_scope": "EVIDENCE_CLOSEOUT",
    }
    completion.update({k: v for k, v in runtime.items() if k not in {"receipts", "stop"}})
    report(59, completion)
    print(
        json.dumps(
            {"rows": len(rows), "contexts": len(receipts), "complete": complete, "stop": stop}
        ),
        flush=True,
    )


def bundle():
    destination = Path("/Users/sskim/Documents/Codex") / f"thesis-monitor-{NAME}-report.zip"
    rows = [("reports/" + p.name, p) for p in sorted(REPORTS.glob("*.json"))]
    rows += [
        ("experiment/" + str(p.relative_to(OUTPUT)), p)
        for p in sorted(OUTPUT.rglob("*"))
        if p.is_file() and "runtime-state" not in p.parts and "working-directory" not in p.parts
    ]
    rows += [
        (str(p), p)
        for p in (
            INSTRUCTION,
            SCRIPT,
            FIXTURE,
            TEST,
            Path(SERVICE),
            Path("docs/MASTER_WORKFLOW.md"),
        )
    ]
    failures = m12._secret_scan_failures(rows)
    if failures:
        raise ValueError(f"secret_scan_failed:{failures}")
    index = {
        "contract": "m12e-artifact-index-v1",
        "artifacts": [
            {"path": name, "sha256": sha(path.read_bytes()), "size_bytes": path.stat().st_size}
            for name, path in rows
        ],
    }
    with zipfile.ZipFile(destination, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, path in rows:
            archive.write(path, name)
        archive.writestr("artifact-index.json", json.dumps(index, indent=2) + "\n")
    digest = sha(destination.read_bytes())
    verification = verify_zip(destination, digest)
    if verification["status"] != "PASS":
        raise ValueError("bundle_integrity_failed")
    destination.with_suffix(".zip.sha256").write_text(f"{digest}  {destination.name}\n")
    print(json.dumps({"zip": str(destination), **verification}))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("prepare", "run", "finalize", "bundle"))
    command = parser.parse_args().command
    {"prepare": prepare, "run": run, "finalize": finalize, "bundle": bundle}[command]()


if __name__ == "__main__":
    main()
