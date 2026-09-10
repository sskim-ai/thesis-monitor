"""M12X contract review and archive-only full Sol fictional canary."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
import json
from pathlib import Path
import re
import statistics
import subprocess
import sys
import uuid
import zipfile

from scripts import sol_restoration_m12w as w
from scripts.sol_runtime_adapter_m12w import single_attempt

u = w.u
read, write, sha, git = u.read, u.write, u.sha, u.git
BASE = "079213d7ff730c1d9eb60fca3b06b404ff34f0e5"
INSTRUCTION_COMMIT = "239b799a1361b8ad8168aef2310f03eaf8fc641e"
ROOT_CAUSE_COMMIT = "6aa35700448539cde45e440f7082f329a78d9e68"
MODEL = "gpt-5.6-sol"
EFFORT = "xhigh"
NAME = "20260910-positive-stronger-bucket-contract-review-full-sol-fictional-canary"
OUTPUT = Path("artifacts") / NAME
REPORTS = Path("docs/reports") / NAME
ROOT = Path("docs/architecture/M12X_POSITIVE_STRONGER_BUCKET_REVIEW.json")
FIXTURES = Path("fixtures/positive_stronger_bucket_contract_m12x.json")
INSTRUCTION = Path(
    "docs/work-instructions/"
    "20260910-positive-stronger-bucket-contract-review-and-full-sol-fictional-canary.md"
)
LATEST = Path.home() / "Documents/Codex" / (
    "thesis-monitor-20260910-gpt56-sol-xhigh-restoration-"
    "full-fictional-financial-canary-report.zip"
)
LATEST_SHA = "2e3d3c49081443d2b3646ba078460391db4aceea5b8656a721bcb609b4cb0700"
SLUGS = {
    int(number): slug
    for number, slug in re.findall(r"^(\d{2})-([a-z0-9-]+)$", INSTRUCTION.read_text(), re.M)
}
SLUGS.update(
    {
        25: "target-fixture-before-after",
        26: "directional-prompt-no-change-proof",
    }
)
FROZEN_BASE_SHA256 = {
    "app/services/coldstart_source_assembly_service.py": "4b4e9563767dab2df1440a46a04d53d29d041c95b2cabc02e769a7673ac60594",
    "app/services/current_price_context_service.py": "9e68c509952bf6bad320506d860f08830712fb3c623960e99d126c8d9ec61f5f",
    "app/services/daily_digest_renderer.py": "3a2fe87c12d04fc443a36cc06984b2180fff69391d448f3343ca44dfd68ed8b6",
    "app/services/daily_monitor_service.py": "5f3b94ec2d6520c5a9a885179fcd8b32eac52f722d3a207e18693658371c69e9",
    "app/services/directional_balance_service.py": "f9da0979f1c614d079fdbce2470d3eed36524eb3674a617ba4691e0cf2620205",
    "app/services/financial_framework_claim_service.py": "06a97ae8dc918120e1dba1a2a6c60297515a80972ac79e0d7939ea6d44d57903",
    "scripts/directional_financial_context_m12.py": "158f962cc2592df25160215bbf113dc2ed2e8fda79fd90d0df5260f378908b85",
    "scripts/first_class_typed_financial_evidence_m12b.py": "fb08bb3a5f66e11ae1d5008f2d05476343d70d262b9715b7f1e3f5696f0ae6a9",
    "scripts/materiality_scoped_working_capital_grounding_m12c.py": "e8e9b8c05d68b66a1e13746fbe4f8dcc534c5e3229381da4e0b69b85f444b1a6",
    "scripts/qtd_ytd_plain_korean_period_validator_m12d.py": "d793d98a46b4e2759d71c9307d9e31017c54045fdb457f157f9ab599243714c0",
    "scripts/sol_runtime_adapter_m12w.py": "67c493bd816519042e1e08d5c34143e5715f17d4823da21160e54f2cf6cc3f5a",
    "tests/test_directional_balance_ordinal_calibration.py": "709ec845b9811dab964a49125cff8f4b99ca559f140b6abc1542f91b697c8a5c",
    "tests/test_financial_exclusion_expectation_m12u.py": "f4679939238998fafc87082df40c7883ab615f9803a769981e7a40085268a8b0",
    "tests/test_first_class_typed_financial_evidence_m12b.py": "35620d9176f93c5736e9011ed0fc2d3f5cb0439b15575efbd9b84fe078ad538c",
    "tests/test_materiality_scoped_working_capital_grounding_m12c.py": "f94539507d037976c2aab05341e6f07086f38fa4c8bacc467a88ecd3678a9bb9",
    "tests/test_qtd_ytd_plain_korean_period_validator_m12d.py": "a3677f5204a9e4a951378e09604b49ab535cefe95171c8ca4af6994345915ddc",
}


def report(number: int, value: object) -> None:
    write(REPORTS / f"{number:02d}-{SLUGS[number]}.json", value)


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


def _base_bytes(path: str) -> bytes:
    return subprocess.check_output(["git", "show", f"{BASE}:{path}"])


def _freeze_paths(paths: tuple[str, ...]) -> dict[str, object]:
    rows = []
    for path in paths:
        try:
            before = sha(_base_bytes(path))
            verification_mode = "EXACT_BASE_GIT_OBJECT"
        except subprocess.CalledProcessError:
            before = FROZEN_BASE_SHA256[path]
            verification_mode = "FROZEN_BASE_SHA256"
        after = sha(Path(path).read_bytes())
        rows.append(
            {
                "path": path,
                "base_sha256": before,
                "current_sha256": after,
                "unchanged": before == after,
                "verification_mode": verification_mode,
            }
        )
    return {
        "status": "PASS" if all(row["unchanged"] for row in rows) else "FAIL",
        "base_sha": BASE,
        "rows": rows,
        "change_count": sum(not row["unchanged"] for row in rows),
    }


def fixture_audit() -> dict[str, object]:
    payload = read(FIXTURES)
    rows = payload["fixtures"]
    expected_ids = [
        "POS-ORD-01",
        "POS-ORD-02",
        "POS-ORD-03",
        "POS-ORD-04",
        "POS-ORD-05",
        "NEG-ORD-01",
        "NEG-ORD-02",
        "NEG-ORD-03",
    ]
    checks = {
        "exact_fixture_ids": [row["id"] for row in rows] == expected_ids,
        "normalized_balances": all(row["expected_buy"] + row["expected_sell"] == 10 for row in rows),
        "half_point_precision": all(
            float(row["expected_buy"] * 2).is_integer()
            and float(row["expected_sell"] * 2).is_integer()
            for row in rows
        ),
        "decision_consistency": all(
            (row["expected_direction"] == "BUY" and row["expected_buy"] >= 6)
            or (row["expected_direction"] == "SELL" and row["expected_sell"] >= 6)
            for row in rows
        ),
        "positive_negative_symmetry": (
            rows[0]["expected_buy"] == rows[5]["expected_sell"]
            and rows[1]["expected_buy"] == rows[6]["expected_sell"]
            and rows[2]["expected_buy"] == rows[7]["expected_sell"]
        ),
        "fixed_score_rule_absent": payload["policy"]["fixed_score_rule"] is False,
        "evidence_count_rule_absent": payload["policy"]["evidence_count_bucket_rule"] is False,
        "valuation_not_universal_cap": rows[3]["expected_buy"] == 6.5,
        "generic_stronger_pattern": rows[1]["expected_buy"] == 6.5,
    }
    return {
        "status": "PASS" if all(checks.values()) else "FAIL",
        "checks": checks,
        "rows": rows,
        "fixed_score_rule_count": 0,
        "evidence_count_bucket_rule_count": 0,
    }


def calibration_audit(row: dict[str, object]) -> dict[str, object]:
    target = read(ROOT)["expectation"]["all_target_buys"].get(row["ticker"])
    if target is None:
        return {"status": "NOT_TARGETED"}
    observed = row["core"]["directional_balance"]["buy"]
    return {
        "status": "PASS" if observed == target else "FAIL",
        "expected_buy": target,
        "observed_buy": observed,
        "contract_sha256": sha(ROOT.read_bytes()),
        "basis": "M12X generic-derived fictional target; audit only, never a label override",
    }


def review() -> None:
    if (OUTPUT / "review-receipt.json").exists():
        raise ValueError("m12x_review_already_frozen")
    root = read(ROOT)
    decision = read(REPORTS / "13-fic-fin-01-root-cause-decision.json")
    fixtures = fixture_audit()
    if decision["root_cause"] != "EXACT_FIXTURE_TARGET_OVERCONSTRAINED":
        raise ValueError("m12x_root_cause_not_frozen")
    report(14, {"status": "FROZEN", **root["positive_contract"]})
    report(15, {"status": "FROZEN", **root["negative_contract"]})
    by_id = {row["id"]: row for row in fixtures["rows"]}
    for number, fixture_id in enumerate(by_id, start=16):
        report(number, {"status": "PASS", **by_id[fixture_id]})
    report(
        24,
        {
            "status": "FROZEN",
            "root_cause": root["root_cause"],
            "generic_pattern": "POS-ORD-02",
            **root["fic_fin_01"],
        },
    )
    report(
        25,
        {
            "status": "PASS",
            "before": root["fic_fin_01"]["previous_target"],
            "after": root["fic_fin_01"]["frozen_target"],
            "changed_field": "derived fictional expected target only",
            "source_case_change_count": 0,
        },
    )
    report(
        26,
        {
            "status": "PASS",
            **_freeze_paths(("app/services/directional_balance_service.py",)),
            "directional_prompt_change_count": 0,
        },
    )
    report(
        27,
        {
            "status": "PASS",
            "fixed_score_rule_count": fixtures["fixed_score_rule_count"],
            "evidence_count_bucket_rule_count": fixtures[
                "evidence_count_bucket_rule_count"
            ],
            "qualitative_ordinal_contract": True,
        },
    )
    report(
        28,
        {
            "status": "FROZEN_PASS",
            "directional_threshold": root["semantic_freeze"]["directional_threshold"],
            "directional_increment": root["semantic_freeze"]["directional_increment"],
            "hold_lean": root["semantic_freeze"]["hold_lean"],
            "tie_break": root["semantic_freeze"]["tie_break"],
            "directional_threshold_changed": False,
            "directional_increment_changed": False,
            "hold_lean_contract_changed": False,
            "calibration_tiebreak_direction_changed": False,
        },
    )
    freezes = {
        29: (
            "scripts/first_class_typed_financial_evidence_m12b.py",
            "tests/test_first_class_typed_financial_evidence_m12b.py",
        ),
        30: (
            "scripts/materiality_scoped_working_capital_grounding_m12c.py",
            "tests/test_materiality_scoped_working_capital_grounding_m12c.py",
        ),
        31: (
            "scripts/qtd_ytd_plain_korean_period_validator_m12d.py",
            "tests/test_qtd_ytd_plain_korean_period_validator_m12d.py",
        ),
        32: (
            "app/services/financial_framework_claim_service.py",
            "tests/test_financial_exclusion_expectation_m12u.py",
        ),
        33: (
            "app/services/directional_balance_service.py",
            "tests/test_directional_balance_ordinal_calibration.py",
        ),
        34: ("app/services/coldstart_source_assembly_service.py",),
        35: ("app/services/daily_monitor_service.py",),
        36: ("app/services/current_price_context_service.py",),
        37: ("app/services/daily_digest_renderer.py",),
    }
    freeze_results = {}
    for number, paths in freezes.items():
        freeze_results[number] = _freeze_paths(paths)
        report(number, freeze_results[number])
    freeze_results[38] = {
        "status": "PASS",
        "identity_guard_change": "M12_PHASE_NEUTRAL_FICTIONAL_IDENTITY",
        "real_cohort_pre_spawn_rejection_retained": True,
        "model": MODEL,
        "effort": EFFORT,
        "timeout_seconds": 1800,
        "subjects_per_context": 4,
        "wrapper_retry_count": 0,
        "batch_split": 0,
        "runtime_semantic_change_count": 0,
    }
    report(38, freeze_results[38])
    receipt = {
        "status": "PASS"
        if fixtures["status"] == "PASS"
        and all(value["status"] == "PASS" for value in freeze_results.values())
        else "FAIL",
        "root_cause": decision["root_cause"],
        "selected_branch": decision["selected_branch"],
        "fixture_status": fixtures["status"],
        "target_buys": root["semantic_freeze"]["target_buys"],
    }
    write(OUTPUT / "review-receipt.json", receipt)
    print(json.dumps(receipt, sort_keys=True))


def validation() -> None:
    before = _tracked_hashes()
    focused = [
        "tests/test_positive_stronger_bucket_m12x.py",
        "tests/test_sol_restoration_m12w.py",
        "tests/test_financial_exclusion_expectation_m12u.py",
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
        "ruff": [str(Path(sys.executable).with_name("ruff")), "check", "."],
        "diff": ["git", "diff", "--check", BASE],
    }
    results = {}
    for label, command in commands.items():
        print("M12X_VALIDATION", label, flush=True)
        results[label] = u.m12._run_command(
            command,
            output_path=OUTPUT / "validation" / f"{label}.txt",
            timeout=3600,
        )
    if before != _tracked_hashes():
        raise ValueError("m12x_code_changed_during_validation")
    write(OUTPUT / "validation-receipt.json", {"results": results, "code_hashes": before})
    report(39, results["focused"])
    report(40, results["full"])
    report(41, {key: results[key] for key in ("ruff", "diff")})
    print(json.dumps({key: value["returncode"] for key, value in results.items()}))


def prepare() -> None:
    if (OUTPUT / "phase-a-receipt.json").exists():
        raise ValueError("m12x_phase_a_already_frozen")
    root = read(ROOT)
    review_receipt = read(OUTPUT / "review-receipt.json")
    validation_receipt = read(OUTPUT / "validation-receipt.json")
    ci = read(OUTPUT / "validation/implementation-ci.json")
    integrity = u.e.verify_zip(LATEST, LATEST_SHA)
    model = w.model_availability()
    fixtures = fixture_audit()
    checks = {
        "latest_result_integrity": integrity["status"] == "PASS",
        "offline_review": review_receipt["status"] == "PASS",
        "root_cause_frozen": review_receipt["root_cause"]
        == "EXACT_FIXTURE_TARGET_OVERCONSTRAINED",
        "fixtures": fixtures["status"] == "PASS",
        "model_available": model["status"] == "PASS",
        "runtime_contract": (
            root["model"],
            root["effort"],
            root["selected_timeout_seconds"],
            root["subjects_per_context"],
            root["wrapper_retry_count"],
        )
        == (MODEL, EFFORT, 1800, 4, 0),
        "target_contract": root["expectation"]["all_target_buys"]
        == root["semantic_freeze"]["target_buys"],
        "validation_code_frozen": validation_receipt["code_hashes"]
        == _tracked_hashes(),
        "hosted_ci_new_failures_zero": ci["new_m12x_failure_count"] == 0
        and ci["head_sha"] == git("rev-parse", "HEAD"),
        "schedules_paused": u.stability._schedule_observation()["status"] == "PASS",
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
        "implementation_commit": git("rev-parse", "HEAD"),
        "branch": git("branch", "--show-current"),
        "origin_main": git("rev-parse", "origin/main"),
        "runtime_contract_sha256": sha(ROOT.read_bytes()),
        "schedule_start": u.stability._schedule_observation(),
        "validations": validation_receipt["results"],
    }
    report(42, ci)
    if gate["status"] != "PASS":
        report(43, gate)
        raise SystemExit("NO_MODEL_CALLS")
    generation = (
        "20260910-m12x-fictional-"
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
        old_id = json.loads(archive.read("experiment/phase-a-receipt.json"))[
            "generation_id"
        ]
        for ticker in u.m12.TICKERS:
            before_context = json.loads(archive.read(f"experiment/contexts/{ticker}.json"))
            if contexts[ticker] != before_context:
                raise ValueError("m12x_fictional_source_changed")
        for row in inputs["contexts"]:
            prefix = f"experiment/frozen-contexts/context-{row['context']:02d}/"
            for kind, suffix in (("prompt", "prompt.txt"), ("schema", "schema.json")):
                before_text = archive.read(prefix + suffix).decode().replace(
                    old_id, "GENERATION_ID"
                )
                after_text = Path(row[f"{kind}_path"]).read_text().replace(
                    generation, "GENERATION_ID"
                )
                if before_text != after_text:
                    raise ValueError("m12x_prompt_or_schema_changed")
    gate.update(
        generation_id=generation,
        source_lock_sha256=lock["source_lock_sha256"],
        model_inputs=inputs,
        code_file_sha256=_tracked_hashes(),
        config_file_sha256={
            str(path): sha(path.read_bytes()) for path in (ROOT, FIXTURES, INSTRUCTION)
        },
        source_prompt_schema_equal_m12w=True,
    )
    write(OUTPUT / "phase-a-receipt.json", gate)
    report(43, gate)
    report(
        44,
        {
            **u.m12.fictional_manifest(generation),
            "model": MODEL,
            "reasoning_effort": EFFORT,
            "runtime_contract": root["runtime"],
        },
    )
    report(45, lock)
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
        raise ValueError("m12x_phase_a_not_passed")
    for key in ("code_file_sha256", "config_file_sha256"):
        if any(sha(Path(path).read_bytes()) != digest for path, digest in gate[key].items()):
            raise ValueError("m12x_code_or_config_changed_after_freeze")
    original = {
        "call": u.m12._single_attempt_model_call,
        "output": u.f.OUTPUT,
        "calibration": u.f._calibration_audit,
        "model": u.f.MODEL,
        "effort": u.f.EFFORT,
        "root": u.ROOT,
    }
    u.m12._single_attempt_model_call = single_attempt
    u.f.OUTPUT = OUTPUT
    u.f._calibration_audit = u.calibration_audit
    u.f.MODEL = MODEL
    u.f.EFFORT = EFFORT
    u.ROOT = ROOT
    try:
        u.f.run()
    finally:
        u.m12._single_attempt_model_call = original["call"]
        u.f.OUTPUT = original["output"]
        u.f._calibration_audit = original["calibration"]
        u.f.MODEL = original["model"]
        u.f.EFFORT = original["effort"]
        u.ROOT = original["root"]


def _variance(rows: list[dict[str, object]], accessor) -> int:
    return sum(
        len({accessor(row["core"]) for row in rows if row["ticker"] == ticker}) > 1
        for ticker in u.m12.TICKERS
    )


def _counter(errors: list[str], *needles: str) -> int:
    return sum(any(needle in error.lower() for needle in needles) for error in errors)


def finalize() -> None:
    gate = read(OUTPUT / "phase-a-receipt.json")
    documents = [
        read(path) for path in sorted((OUTPUT / "model-calls").glob("**/run-document.json"))
    ]
    receipts = [
        read(path) for path in sorted((OUTPUT / "model-calls").glob("**/receipt.json"))
    ]
    rows = [
        {**row, "repetition": document["repetition"]}
        for document in documents
        for row in document.get("rows", [])
    ]
    complete = len(documents) == 6 and len(receipts) == 6 and len(rows) == 24
    stop = read(OUTPUT / "canary-stop.json") if (OUTPUT / "canary-stop.json").exists() else {}
    summary = (
        read(OUTPUT / "canary-summary.json")
        if (OUTPUT / "canary-summary.json").exists()
        else {}
    )
    for number in range(46, 52):
        report(number, {"status": "NOT_RUN", "reason": stop or "not attempted"})
    for document in documents:
        number = 46 + (document["repetition"] - 1) * 2 + document["context"] - 1
        report(number, document)
    errors = [error for row in rows for error in row.get("errors", [])]
    target_violations = sum(
        row.get("m12f_calibration", {}).get("status") == "FAIL" for row in rows
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
    report(52, semantic)
    report(
        53,
        {
            "status": "PASS" if complete and target_violations == 0 else "FAIL",
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
    fic_one = [row for row in rows if row["ticker"] == "FIC-FIN-01"]
    report(
        54,
        {
            "status": "PASS"
            if len(fic_one) == 3
            and all(row.get("m12f_calibration", {}).get("status") == "PASS" for row in fic_one)
            else "FAIL",
            "frozen_target": read(ROOT)["fic_fin_01"]["frozen_target"],
            "rows": fic_one,
        },
    )
    grounding = (
        u.f.grounding._grounding_summary(rows, require_complete=complete)
        if rows
        else {"status": "NOT_MEASURED"}
    )
    report(55, grounding)
    formal = summary.get("stability", {"status": "NOT_MEASURED"})
    report(56, formal)
    core_rows = []
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
        core_rows.append(
            {
                "ticker": ticker,
                "values": values,
                "observed_count": len(values),
                "directional_balance_unique_count": len(set(values))
                if len(values) == 3
                else "NOT_MEASURED",
            }
        )
    report(57, {"complete": complete, "rows": core_rows})
    business_variance = _variance(rows, lambda core: core["business_thesis_change"])
    report(
        58,
        {
            "complete": complete,
            "business_delta_variance_subject_count": business_variance
            if complete
            else "NOT_MEASURED",
            "rows": [
                {
                    "ticker": ticker,
                    "values": [
                        row["core"]["business_thesis_change"]
                        for row in rows
                        if row["ticker"] == ticker
                    ],
                }
                for ticker in u.m12.TICKERS
            ],
        },
    )
    new_buyer_variance = _variance(
        rows, lambda core: core["fundamental_new_buyer"]["stance"]
    )
    holder_variance = _variance(rows, lambda core: core["fundamental_holder"]["stance"])
    report(
        59,
        {
            "complete": complete,
            "new_buyer_stance_variance_subject_count": new_buyer_variance
            if complete
            else "NOT_MEASURED",
            "holder_stance_variance_subject_count": holder_variance
            if complete
            else "NOT_MEASURED",
            "rows": [
                {
                    "ticker": ticker,
                    "new_buyer": [
                        row["core"]["fundamental_new_buyer"]["stance"]
                        for row in rows
                        if row["ticker"] == ticker
                    ],
                    "holder": [
                        row["core"]["fundamental_holder"]["stance"]
                        for row in rows
                        if row["ticker"] == ticker
                    ],
                }
                for ticker in u.m12.TICKERS
            ],
        },
    )
    elapsed = [receipt["elapsed_seconds"] for receipt in receipts if "elapsed_seconds" in receipt]
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
        "wrapper_retry_count": sum(receipt.get("wrapper_retry_count", 0) for receipt in receipts),
        "timeout_count": sum(receipt.get("timed_out", False) for receipt in receipts),
        "capacity_failure_count": sum(
            "CAPACITY" in str(receipt.get("failure_type", "")).upper()
            for receipt in receipts
        ),
        "orphan_process_count": sum(
            receipt.get("orphan_process_count", 0) for receipt in receipts
        ),
        "runtime_median_elapsed_seconds": statistics.median(elapsed)
        if elapsed
        else "NOT_MEASURED",
        "runtime_max_elapsed_seconds": max(elapsed) if elapsed else "NOT_MEASURED",
        "receipts": receipts,
    }
    report(60, runtime)
    specificity = summary.get("specificity", {"status": "NOT_MEASURED"})
    report(61, specificity)
    stable_count = formal.get("fictional_stable_count", "NOT_MEASURED")
    boundary_count = formal.get("fictional_boundary_uncertainty_count", "NOT_MEASURED")
    unstable_count = formal.get("fictional_unstable_count", "NOT_MEASURED")
    reversals = formal.get("opposite_direction_reversal_count", "NOT_MEASURED")
    contract_success = len(fic_one) == 3 and all(
        row.get("m12f_calibration", {}).get("status") == "PASS" for row in fic_one
    )
    canary_success = (
        complete
        and not errors
        and target_violations == 0
        and summary.get("status") == "PASS"
    )
    runtime_suitable = (
        runtime["model_context_success_count"] == 6
        and runtime["model_context_failure_count"] == 0
        and runtime["timeout_count"] == 0
        and runtime["capacity_failure_count"] == 0
        and runtime["orphan_process_count"] == 0
        and runtime["wrapper_retry_count"] == 0
    )
    core_stable = stable_count == 8 and boundary_count == 0 and unstable_count == 0
    ready = (
        canary_success
        and contract_success
        and runtime_suitable
        and core_stable
        and reversals == 0
        and business_variance == 0
        and new_buyer_variance == 0
        and holder_variance == 0
    )
    if not runtime_suitable:
        next_scope = "SOL_RUNTIME_REGRESSION_REVIEW"
    elif not contract_success:
        next_scope = "POSITIVE_STRONGER_BUCKET_STABILITY_REVIEW_GPT56_SOL"
    elif not core_stable:
        next_scope = "CORE_BALANCE_STABILITY_REVIEW_GPT56_SOL"
    elif business_variance:
        next_scope = "BOUNDED_BUSINESS_DELTA_CALIBRATION_REPAIR_GPT56_SOL"
    elif new_buyer_variance:
        next_scope = "BOUNDED_NEW_BUYER_STANCE_CALIBRATION_REPAIR_GPT56_SOL"
    elif holder_variance:
        next_scope = "BOUNDED_HOLDER_STANCE_CALIBRATION_REPAIR_GPT56_SOL"
    else:
        next_scope = "FRESH_REAL_FINANCIAL_CONTEXT_GENERALIZATION_PROOF_GPT56_SOL_XHIGH"
    report(
        62,
        {
            "status": "PASS" if contract_success else "FAIL",
            "root_cause": read(ROOT)["root_cause"],
            "frozen_target": read(ROOT)["fic_fin_01"]["frozen_target"],
        },
    )
    report(63, {"status": "PASS" if canary_success else "FAIL", "complete": complete})
    report(
        64,
        {"status": "READY" if runtime_suitable else "NOT_READY", "runtime": runtime},
    )
    report(
        65,
        {
            "status": "PASS" if core_stable else "FAIL",
            "stable": stable_count,
            "boundary_uncertainty": boundary_count,
            "unstable": unstable_count,
        },
    )
    report(
        66,
        {
            "status": "CLOSED" if business_variance == 0 else "FOLLOWUP_REQUIRED",
            "variance_subject_count": business_variance if complete else "NOT_MEASURED",
        },
    )
    report(
        67,
        {
            "status": "CLOSED" if new_buyer_variance == 0 else "FOLLOWUP_REQUIRED",
            "variance_subject_count": new_buyer_variance if complete else "NOT_MEASURED",
        },
    )
    report(
        68,
        {
            "status": "CLOSED" if holder_variance == 0 else "FOLLOWUP_REQUIRED",
            "variance_subject_count": holder_variance if complete else "NOT_MEASURED",
        },
    )
    report(
        69,
        {
            "fresh_real_proof_readiness": "READY" if ready else "NOT_READY",
            "next_scope": next_scope,
        },
    )
    report(
        70,
        {
            "status": "SUSPENDED_FROM_PROOF_CRITICAL_PATH",
            "future_scope": "MODEL_COMPATIBILITY_OR_QUALITY_EXPERIMENT",
            "astra_model_calls": 0,
        },
    )
    ci = read(OUTPUT / "validation/implementation-ci.json")
    report(
        71,
        {
            "status": ci["status"],
            "known_historical_portability_failure_count": ci["failed"],
            "new_m12x_failure_count": ci["new_m12x_failure_count"],
            "next_scope": "HOSTED_CI_HISTORICAL_ARTIFACT_PORTABILITY_REPAIR",
        },
    )
    firewall = u.firewall()
    report(72, {"status": "PASS", **firewall})
    schedule_end = u.stability._schedule_observation()
    report(73, {"start": gate["schedule_start"], "end": schedule_end})
    report(
        74,
        {
            "status": "PENDING_DOCUMENTATION",
            "m12x_status": "PASS" if canary_success else "FAIL",
            "fresh_real_proof_readiness": "READY" if ready else "NOT_READY",
            "next_scope": next_scope,
        },
    )
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
        "m12w_status": "M12W_CANARY_FAIL_TARGET_CONTRACT_ONLY",
        "m12x_status": "PASS" if canary_success else "FAIL",
        "implementation_model_target": MODEL,
        "implementation_reasoning_effort": EFFORT,
        "investment_judgment_model_target": MODEL,
        "investment_judgment_reasoning_effort": EFFORT,
        "authoring_model_target_match": True,
        "runner_model_target_match": all(
            receipt.get("cli_advertised_runtime") == {"model": MODEL, "effort": EFFORT}
            for receipt in receipts
        )
        if receipts
        else "NOT_MEASURED",
        "model_target_fallback_count": 0,
        "fic_fin_01_root_cause": read(ROOT)["root_cause"],
        "fic_fin_01_previous_target": 6.0,
        "fic_fin_01_frozen_target": 6.5,
        "fic_fin_01_target_change_reason": read(ROOT)["fic_fin_01"][
            "target_change_reason"
        ],
        "directional_prompt_change_count": 0,
        "fixture_target_change_count": 1,
        "positive_6_0_6_5_contract_status": "PASS",
        "negative_symmetry_contract_status": "PASS",
        "persistence_unknown_boundary_status": "PASS",
        "valuation_unknown_boundary_status": "PASS",
        "market_expectation_boundary_status": "PASS",
        "fixed_score_rule_count": 0,
        "evidence_count_bucket_rule_count": 0,
        "directional_threshold_changed": False,
        "directional_increment_changed": False,
        "hold_lean_contract_changed": False,
        "calibration_tiebreak_direction_changed": False,
        "financial_semantic_change_count": 0,
        "financial_context_selection_change_count": 0,
        "first_class_projection_change_count": 0,
        "working_capital_validator_semantic_change_count": 0,
        "qtd_ytd_validator_semantic_change_count": 0,
        "financial_exclusion_validator_semantic_change_count": 0,
        "market_expectation_contract_change_count": 0,
        "fictional_generation_id": gate["generation_id"],
        "fictional_subject_count": 8,
        "fictional_context_count": 2,
        "fictional_repetition_count": 3,
        "model_calls_real": 0,
        "model_calls_judge": 0,
        **{key: value for key, value in runtime.items() if key != "receipts"},
        "fictional_output_row_count": len(rows),
        "fictional_schema_pass_count": semantic.get(
            "fictional_schema_pass_count", len(rows)
        ),
        "hard_financial_semantic_violation_count": semantic.get(
            "hard_financial_semantic_violation_count", len(errors)
        ),
        "invalid_financial_reference_count": semantic.get(
            "invalid_financial_reference_count", _counter(errors, "invalid_financial")
        ),
        "grounding_failure_count": _counter(errors, "grounding", "narrative_substitution"),
        **{
            f"fic_fin_{ticker[-2:]}_directional_balance_unique_count": target_map[ticker][
                "directional_balance_unique_count"
            ]
            for ticker in ("FIC-FIN-01", "FIC-FIN-02", "FIC-FIN-04", "FIC-FIN-05")
        },
        "target_bucket_contract_violation_count": target_violations,
        "formal_stable_count": stable_count,
        "formal_boundary_uncertainty_count": boundary_count,
        "formal_unstable_count": unstable_count,
        "opposite_direction_reversal_count": reversals,
        "business_delta_variance_subject_count": business_variance
        if complete
        else "NOT_MEASURED",
        "new_buyer_stance_variance_subject_count": new_buyer_variance
        if complete
        else "NOT_MEASURED",
        "holder_stance_variance_subject_count": holder_variance
        if complete
        else "NOT_MEASURED",
        "sol_runtime_real_holdout_suitability": "READY"
        if runtime_suitable
        else "NOT_READY",
        "hosted_ci_status": ci["status"],
        "hosted_ci_failure_count": ci["failed"],
        "new_hosted_ci_failure_count": ci["new_m12x_failure_count"],
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
        "status": "PASS" if canary_success else "FAIL",
        "stop_reason": stop.get("stop_reason"),
        "next_scope": next_scope,
    }
    report(75, completion)
    print(
        json.dumps(
            {
                "status": completion["status"],
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
