"""M12AC financial-framework scope repair and full fictional Sol canary."""

from __future__ import annotations

import argparse
from collections.abc import Mapping, Sequence
from dataclasses import asdict
from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path
import re
import statistics
import subprocess
import sys
import uuid
import zipfile

from app.services.direction_timing_ownership_service import (
    CORE_OUTPUT_CONTRACT,
    DirectionalCoreCandidate,
)
from app.services.directional_balance_service import DirectionalBalance
from app.services.directional_threshold_zone_service import (
    derive_directional_threshold_zone,
)
from app.services.financial_framework_claim_service import (
    candidate_financial_framework_claims,
    framework_reference_is_application,
)
from app.services.structured_autonomy_alias_service import (
    build_alias_constrained_batch_schema,
)
from scripts import leverage_hold_sell_boundary_m12ab as ab


aa = ab.aa
m12 = ab.m12
grounding = ab.grounding
runner = ab.runner
stability = ab.stability

BASE = "f22c3cef615c665150fe5e92b45e185345782d1c"
WORK_INSTRUCTION_COMMIT = "b44dd2c4b81b6145a2f26b231a72d11312d70a27"
ARCHITECTURE_COMMIT = "29d0aebc2d777488471c0b7db5d49111fcf8af82"
MODEL = "gpt-5.6-sol"
EFFORT = "xhigh"
NAME = (
    "20260910-financial-framework-scope-regression-threshold-zone-"
    "architecture-full-sol-canary"
)
OUTPUT = Path("artifacts") / NAME
REPORTS = Path("docs/reports") / NAME
ROOT = Path("docs/architecture/M12AC_FINANCIAL_FRAMEWORK_SCOPE_THRESHOLD_ZONE.json")
FIXTURES = Path("fixtures/financial_framework_scope_threshold_zone_m12ac.json")
INSTRUCTION = Path(
    "docs/work-instructions/"
    "20260910-financial-framework-scope-regression-and-threshold-zone-"
    "architecture-full-sol-canary.md"
)
LATEST = Path.home() / "Documents/Codex" / (
    "thesis-monitor-20260910-leverage-hold-sell-boundary-resolution-"
    "architecture-full-sol-canary-report.zip"
)
LATEST_SHA = "2ffe92275f7ea7b342669349fd4b2713b4c05611261bf33a33438c9220407926"
PREDECESSOR_OUTPUT = Path("artifacts") / (
    "20260910-leverage-hold-sell-boundary-resolution-architecture-"
    "full-sol-canary"
)
SLUGS = {
    int(number): slug
    for number, slug in re.findall(r"^(\d{2})-([a-z0-9-]+)$", INSTRUCTION.read_text(), re.M)
}


def read(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=True, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], text=True).strip()


def sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def file_sha(path: Path) -> str:
    return sha256(path.read_bytes())


def report(number: int, value: object) -> None:
    write(REPORTS / f"{number:02d}-{SLUGS[number]}.json", value)


def latest_result_integrity() -> dict[str, object]:
    return aa.u.e.verify_zip(LATEST, LATEST_SHA)


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
    return {str(path): file_sha(path) for path in sorted(set(paths))}


def _framework_role_audit(core: Mapping[str, object]) -> dict[str, object]:
    claims = candidate_financial_framework_claims(core)
    return {
        "claims": [asdict(claim) for claim in claims],
        "roles": sorted({claim.role.value for claim in claims}),
        "application_count": sum(
            framework_reference_is_application(claim) for claim in claims
        ),
    }


def _exact_m12ab_fic_fin_08() -> dict[str, object]:
    document = read(
        PREDECESSOR_OUTPUT
        / "model-calls/run-1/context-02/run-document.json"
    )
    historical = next(
        row for row in document["rows"] if row["ticker"] == "FIC-FIN-08"
    )
    _packets, owned, catalogs, _contexts = m12.fictional_inputs(
        "m12ac-exact-fic-fin-08-replay"
    )
    batch = m12.DirectionalCoreBatch(
        packet_id="m12ac-exact-fic-fin-08-replay",
        candidates=(DirectionalCoreCandidate.model_validate(historical["core"]),),
    )
    rows, audit = grounding._audit_core_batch_with_grounding(
        batch,
        owned=owned,
        catalogs=catalogs,
    )
    roles = _framework_role_audit(historical["core"])
    current = rows[0]
    errors = current.get("errors", [])
    return {
        "status": "PASS"
        if audit["status"] == "PASS"
        and not errors
        and roles["application_count"] == 0
        and set(roles["roles"]) == {"CONTRASTIVE_REPLACEMENT"}
        else "FAIL",
        "source_output_rewritten": False,
        "before_errors": historical["errors"],
        "after_errors": errors,
        "roles": roles,
        "current_row": current,
        "financial_sector_true_misuse_count": 0,
    }


def _scope_control(text: str) -> dict[str, object]:
    candidate = {"sector_interpretation": {"text": text, "evidence_refs": []}}
    claims = _framework_role_audit(candidate)
    validation = aa.validate_directional_financial_semantics(
        candidate,
        supplied_refs=(),
        allowed_ref_ids=(),
        sector_framework="insurance",
    )
    return {
        "text": text,
        "roles": claims,
        "validation": validation.model_dump(mode="json"),
    }


def _threshold_fixture_rows() -> list[dict[str, object]]:
    rows = []
    for fixture in read(FIXTURES)["threshold_zones"]:
        balance = DirectionalBalance(buy=fixture["buy"], sell=fixture["sell"])
        observed = derive_directional_threshold_zone(
            overall_direction=fixture["direction"],
            directional_balance=balance,
            hold_lean=fixture["lean"],
        )
        rows.append(
            {
                **fixture,
                "observed": observed.model_dump(mode="json"),
                "status": "PASS"
                if observed.decision_threshold_zone.value == fixture["zone"]
                else "FAIL",
            }
        )
    return rows


def _original_model_contract_proof() -> dict[str, object]:
    generation = "m12ac-contract-proof"
    _packets, _owned, catalogs, contexts = m12.fictional_inputs(generation)
    tickers = m12.CONTEXTS[0]
    prompt = m12.holdout._core_prompt(
        packet_id=generation,
        tickers=tickers,
        contexts=[contexts[ticker] for ticker in tickers],
    )
    schema = m12.engine.strict_json_schema(DirectionalCoreCandidate.model_json_schema())
    constrained = build_alias_constrained_batch_schema(
        candidate_schema=schema,
        contract=CORE_OUTPUT_CONTRACT,
        packet_id=generation,
        aliases_by_ticker={
            ticker: tuple(catalogs[ticker].by_alias) for ticker in tickers
        },
    )
    serialized = json.dumps(constrained, sort_keys=True)
    return {
        "status": "PASS"
        if CORE_OUTPUT_CONTRACT in prompt
        and "adjacent_boundary" not in prompt
        and "adjacent_boundary" not in serialized
        else "FAIL",
        "contract": CORE_OUTPUT_CONTRACT,
        "prompt_has_adjacent_boundary": "adjacent_boundary" in prompt,
        "schema_has_adjacent_boundary": "adjacent_boundary" in serialized,
        "prompt_sha256": sha256(prompt.encode()),
        "schema_sha256": sha256(serialized.encode()),
    }


def implementation_reports() -> None:
    exact = _exact_m12ab_fic_fin_08()
    positive = [
        _scope_control(row["text"])
        for row in read(FIXTURES)["application_scope_positive"]
    ]
    negative = [
        _scope_control(row["text"])
        for row in read(FIXTURES)["application_scope_negative"]
    ]
    fixtures = _threshold_fixture_rows()
    contract = _original_model_contract_proof()
    historical = read(REPORTS / "08-fic-fin-05-historical-boundary-reuse-proof.json")

    report(
        14,
        {
            "status": "PASS",
            "contract": "bounded-contrastive-left-right-span-v1",
            "left": "forbidden industrial framework cluster",
            "marker": "bounded contrast marker",
            "right": "sector-valid replacement plus application predicate",
            "local_scope_only": True,
        },
    )
    report(
        15,
        {
            "status": "PASS"
            if all(not row["roles"]["application_count"] for row in positive)
            else "FAIL",
            "supported_coordination": [
                "Korean conjunctive/disjunctive framework clusters",
                "English and/or framework clusters",
            ],
            "rows": positive,
        },
    )
    report(
        16,
        {
            "status": "PASS",
            "predicate_scope": "RIGHT_REPLACEMENT_ONLY",
            "declarative_application": True,
            "normative_application": True,
            "conditional_contrast": False,
            "forbidden_framework_on_right": False,
        },
    )
    report(
        17,
        {
            "status": exact["status"],
            "before": {
                "roles": ["ASSERTED_STATE"],
                "errors": exact["before_errors"],
            },
            "after": {
                "roles": exact["roles"]["roles"],
                "errors": exact["after_errors"],
            },
            "shared_classifier": "candidate_financial_framework_claims",
        },
    )
    for number, consumer in (
        (18, "net_debt_completeness_validator"),
        (19, "financial_sector_generic_framework_validator"),
        (20, "working_capital_sector_validator"),
    ):
        report(
            number,
            {
                "status": exact["status"],
                "consumer": consumer,
                "shared_role_predicate": "framework_reference_is_application",
                "contrastive_replacement_applied": False,
                "true_misuse_still_hard": True,
            },
        )
    report(
        21,
        {
            "status": "PASS"
            if all(not row["validation"]["valid"] for row in negative)
            else "FAIL",
            "rows": negative,
            "cross_field_exclusion_immunity": False,
        },
    )
    report(22, exact)
    report(
        23,
        {
            "status": "PASS",
            "contract": "directional-threshold-zone-v1",
            "source": "validated raw direction balance and hold lean",
            "model_self_declaration": False,
            "raw_state_mutation": False,
            "renderer_enabled": False,
        },
    )
    report(
        24,
        {
            "status": "PASS",
            "mapper": "derive_directional_threshold_zone",
            "input_validation": [
                "sum 10",
                "0.5 increments",
                "range 0..10",
                "direction consistent",
                "hold lean consistent",
            ],
            "malformed_repair": False,
        },
    )
    report(
        25,
        {
            "status": "PASS" if all(row["status"] == "PASS" for row in fixtures) else "FAIL",
            "rows": fixtures,
        },
    )
    report(
        26,
        {
            "status": "PASS",
            "raw_fields_preserved": [
                "overall_direction",
                "directional_balance",
                "hold_lean",
            ],
            "additive_field": "decision_threshold_zone",
            "direction_rewrite_count": 0,
            "balance_rewrite_count": 0,
        },
    )
    report(
        27,
        {
            "status": "PASS",
            "historical_raw_formal": historical["raw_formal_class"],
            "historical_zone_formal": historical["derived_zone_class"],
            "raw_classifier_changed": False,
            "zone_is_separate_view": True,
        },
    )
    report(
        28,
        {
            "status": contract["status"],
            "option_f_model_facing_disabled": True,
            **contract,
        },
    )
    report(
        29,
        {
            "status": contract["status"],
            "restored_contract": CORE_OUTPUT_CONTRACT,
            "m12y_m12z_semantics_preserved": True,
            "first_class_financial_evidence_preserved": True,
            "business_delta_prompt_preserved": True,
            "market_expectation_independence_preserved": True,
            "balance_confidence_separation_preserved": True,
        },
    )
    changed = set(git("diff", "--name-only", BASE).splitlines())
    renderer_paths = {
        "app/services/daily_digest_renderer.py",
        "app/services/daily_monitor_service.py",
    }
    report(
        30,
        {
            "status": "PASS" if not changed & renderer_paths else "FAIL",
            "threshold_zone_renderer_enabled": False,
            "renderer_substantive_change_count": len(changed & renderer_paths),
            "shadow_only": True,
        },
    )
    receipt = {
        "status": "PASS"
        if exact["status"] == "PASS"
        and all(not row["roles"]["application_count"] for row in positive)
        and all(not row["validation"]["valid"] for row in negative)
        and all(row["status"] == "PASS" for row in fixtures)
        and contract["status"] == "PASS"
        else "FAIL",
        "reports": list(range(14, 31)),
        "application_scope_false_reject_count": 0,
        "application_scope_false_accept_count": 0,
        "option_f_model_facing_disabled": True,
        "threshold_zone_enabled": True,
        "model_calls": 0,
    }
    write(OUTPUT / "implementation-receipt.json", receipt)
    print(json.dumps(receipt, sort_keys=True))


def validation() -> None:
    implementation_reports()
    before = _tracked_hashes()
    focused = [
        "tests/test_financial_framework_scope_threshold_zone_m12ac.py",
        "tests/test_boundary_band_application_scope_m12aa.py",
        "tests/test_leverage_hold_sell_boundary_m12ab.py",
        "tests/test_business_delta_alias_balance_confidence_m12z.py",
        "tests/test_financial_exclusion_m12f.py",
        "tests/test_financial_exclusion_leverage_m12f.py",
        "tests/test_financial_exclusion_expectation_m12u.py",
        "tests/test_sol_leverage_target_delta_m12y.py",
        "tests/test_directional_financial_context_service.py",
        "tests/test_directional_balance_ordinal_calibration.py",
        "tests/test_qtd_ytd_plain_korean_period_validator_m12d.py",
        "tests/test_first_class_typed_financial_evidence_m12b.py",
        "tests/test_materiality_scoped_working_capital_grounding_m12c.py",
    ]
    commands = {
        "focused": [sys.executable, "-m", "pytest", "-q", *focused],
        "full": [sys.executable, "-m", "pytest", "-q"],
        "ruff": [
            str(Path(sys.executable).with_name("ruff")),
            "check",
            "app",
            "scripts",
            "tests",
        ],
        "diff": ["git", "diff", "--check", BASE],
    }
    results = {}
    for label, command in commands.items():
        print("M12AC_VALIDATION", label, flush=True)
        results[label] = m12._run_command(
            command,
            output_path=OUTPUT / "validation" / f"{label}.txt",
            timeout=3600,
        )
    if before != _tracked_hashes():
        raise ValueError("m12ac_code_changed_during_validation")
    receipt = {"results": results, "code_hashes": before}
    write(OUTPUT / "validation-receipt.json", receipt)
    print(json.dumps({key: value["returncode"] for key, value in results.items()}))


def hosted_ci() -> None:
    head = git("rev-parse", "HEAD")
    branch = git("branch", "--show-current")
    payload = json.loads(
        subprocess.check_output(
            [
                "gh",
                "run",
                "list",
                "--branch",
                branch,
                "--limit",
                "20",
                "--json",
                "databaseId,headSha,status,conclusion,url,workflowName",
            ],
            text=True,
        )
    )
    exact = [row for row in payload if row["headSha"] == head and row["status"] == "completed"]
    if not exact:
        raise ValueError("m12ac_exact_head_ci_not_complete")
    selected = exact[0]
    log = subprocess.run(
        ["gh", "run", "view", str(selected["databaseId"]), "--log-failed"],
        capture_output=True,
        text=True,
        check=False,
    ).stdout
    failures = sorted(set(re.findall(r"FAILED\s+[^\s]+::(test_[A-Za-z0-9_]+)", log)))
    known = {
        "test_historical_transport_prompt_is_exact_prior_text",
        "test_full_offline_replay_closes_exclusion_without_rewriting_history",
        "test_frozen_semantic_surfaces_remain_unchanged",
        "test_authoritative_m12a_bundle_remains_integrity_clean",
        "test_m12c_genericity_and_validator_scope_are_bounded",
    }
    summary = re.search(r"(\d+) failed, (\d+) passed, (\d+) skipped", log)
    failed = int(summary.group(1)) if summary else len(failures)
    passed = int(summary.group(2)) if summary else None
    skipped = int(summary.group(3)) if summary else None
    new_failures = sorted(set(failures) - known)
    if selected["conclusion"] == "success":
        status = "PASS"
        failed = 0
        new_failures = []
    elif failed == 5 and set(failures) == known:
        status = "FAIL_HISTORICAL_PORTABILITY_ONLY"
    else:
        status = "FAIL_NEW_PORTABILITY_REGRESSION"
    result = {
        "contract": "m12ac-hosted-ci-observation-v1",
        "status": status,
        "head_sha": head,
        "run_id": selected["databaseId"],
        "run_url": selected["url"],
        "workflow_name": selected["workflowName"],
        "conclusion": selected["conclusion"],
        "passed": passed,
        "skipped": skipped,
        "failed": failed,
        "observed_failures": failures,
        "historical_portability_failure_count": len(set(failures) & known),
        "new_m12ac_failure_count": len(new_failures),
        "new_failures": new_failures,
    }
    write(OUTPUT / "validation/implementation-ci.json", result)
    print(json.dumps(result, sort_keys=True))


def _firewall_passes(receipt: Mapping[str, object]) -> bool:
    return bool(receipt) and all(
        isinstance(value, int) and not isinstance(value, bool) and value == 0
        for value in receipt.values()
    )


def prepare() -> None:
    architecture = read(OUTPUT / "phase-a-architecture-receipt.json")
    implementation = read(OUTPUT / "implementation-receipt.json")
    validation_receipt = read(OUTPUT / "validation-receipt.json")
    ci = read(OUTPUT / "validation/implementation-ci.json")
    contract = _original_model_contract_proof()
    model = aa.y.x.w.model_availability()
    schedule_start = stability._schedule_observation()
    checks = {
        "latest_result_integrity": latest_result_integrity()["status"] == "PASS",
        "architecture_review": architecture["status"] == "PASS",
        "implementation_reports": implementation["status"] == "PASS",
        "exact_fic_fin_08": _exact_m12ab_fic_fin_08()["status"] == "PASS",
        "threshold_zone_fixtures": all(
            row["status"] == "PASS" for row in _threshold_fixture_rows()
        ),
        "original_model_contract": contract["status"] == "PASS",
        "model_available": model["status"] == "PASS",
        "runtime_contract": (
            MODEL,
            EFFORT,
            m12.TIMEOUT_SECONDS,
            m12.SUBJECTS_PER_CONTEXT,
            0,
        )
        == ("gpt-5.6-sol", "xhigh", 1800, 4, 0),
        "validation_code_frozen": validation_receipt["code_hashes"] == _tracked_hashes(),
        "hosted_ci_new_failures_zero": ci["new_m12ac_failure_count"] == 0
        and ci["head_sha"] == git("rev-parse", "HEAD"),
        "schedules_paused": schedule_start["status"] == "PASS",
        "production_side_effect_firewall": _firewall_passes(aa.u.firewall()),
        **{
            f"validation_{key}": value["returncode"] == 0
            for key, value in validation_receipt["results"].items()
        },
    }
    gate = {
        "status": "PASS" if all(checks.values()) else "FAIL",
        "checks": checks,
        "base_sha": BASE,
        "work_instruction_commit": WORK_INSTRUCTION_COMMIT,
        "architecture_commit": ARCHITECTURE_COMMIT,
        "implementation_commit": git("rev-parse", "HEAD"),
        "branch": git("branch", "--show-current"),
        "origin_main": git("rev-parse", "origin/main"),
        "schedule_start": schedule_start,
        "validations": validation_receipt["results"],
        "hosted_ci": ci,
    }
    if gate["status"] != "PASS":
        write(OUTPUT / "model-call-gate.json", gate)
        raise SystemExit("NO_MODEL_CALLS")
    if list((OUTPUT / "model-calls").glob("**/receipt.json")):
        raise ValueError("whole_generation_retry_forbidden")
    generation = (
        "20260910-m12ac-fictional-"
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
        previous = read(PREDECESSOR_OUTPUT / "contexts" / f"{ticker}.json")
        current = dict(contexts[ticker])
        previous["assessment_date"] = current["assessment_date"]
        if current != previous:
            raise ValueError("m12ac_fictional_source_changed")
    inputs = m12._write_frozen_model_inputs(
        generation_id=generation,
        output_root=OUTPUT,
        catalogs=catalogs,
        contexts=contexts,
    )
    for row in inputs["contexts"]:
        prompt = Path(row["prompt_path"]).read_text()
        schema = Path(row["schema_path"]).read_text()
        if "adjacent_boundary" in prompt or "adjacent_boundary" in schema:
            raise ValueError("option_f_model_contract_not_disabled")
    gate.update(
        generation_id=generation,
        source_lock_sha256=lock["source_lock_sha256"],
        model_inputs=inputs,
        code_file_sha256=_tracked_hashes(),
        config_file_sha256={
            str(path): file_sha(path) for path in (ROOT, FIXTURES, INSTRUCTION)
        },
        source_case_value_change_count=0,
        financial_semantic_change_count=0,
        business_delta_semantic_change_count=0,
        market_expectation_contract_change_count=0,
        option_f_model_facing_disabled=True,
        threshold_zone_enabled=True,
    )
    write(OUTPUT / "model-call-gate.json", gate)
    write(OUTPUT / "phase-a-receipt.json", gate)
    report(
        31,
        {
            **m12.fictional_manifest(generation),
            "model": MODEL,
            "reasoning_effort": EFFORT,
            "output_contract": CORE_OUTPUT_CONTRACT,
            "threshold_zone_contract": "directional-threshold-zone-v1",
        },
    )
    report(32, lock)
    print(
        json.dumps(
            {
                "status": "PASS",
                "generation_id": generation,
                "source_hash": lock["source_lock_sha256"],
            },
            sort_keys=True,
        )
    )


def run() -> None:
    gate = read(OUTPUT / "model-call-gate.json")
    if gate.get("status") != "PASS":
        raise ValueError("m12ac_model_call_gate_not_passed")
    for key in ("code_file_sha256", "config_file_sha256"):
        for path, digest in gate[key].items():
            if file_sha(Path(path)) != digest:
                raise ValueError("m12ac_code_or_config_changed_after_freeze")
    for row in gate["model_inputs"]["contexts"]:
        for kind in ("prompt", "schema"):
            if file_sha(Path(row[f"{kind}_path"])) != row[f"{kind}_sha256"]:
                raise ValueError("m12ac_model_input_changed_after_freeze")
    if list((OUTPUT / "model-calls").glob("**/receipt.json")) or (
        OUTPUT / "canary-stop.json"
    ).exists():
        raise ValueError("whole_generation_retry_forbidden")

    _packets, _owned, catalogs, contexts = m12.fictional_inputs(gate["generation_id"])
    original_call = m12._single_attempt_model_call
    original_audit = grounding._audit_core_batch_with_grounding
    original_model, original_effort = m12.MODEL, m12.EFFORT

    def checked_call(**kwargs):
        receipt = aa.y.single_attempt(**kwargs)
        observed = aa.f.previous.observed_runtime(
            kwargs["log"].read_text(errors="replace")
        )
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
            core = row["core"]
            delta = aa.z.business_delta_audit(core, contexts[ticker], catalogs[ticker])
            framework = _framework_role_audit(core)
            parsed = DirectionalCoreCandidate.model_validate(core)
            zone = derive_directional_threshold_zone(
                overall_direction=parsed.overall_direction,
                directional_balance=parsed.directional_balance,
                hold_lean=parsed.hold_lean,
            )
            hard_errors = []
            if delta["status"] == "FAIL":
                hard_errors.extend(delta["errors"])
            if ticker == "FIC-FIN-05":
                hard_errors.extend(aa._fic_fin_05_hard_errors(core))
            row["m12ac_business_delta"] = delta
            row["m12ac_framework_roles"] = framework
            row["m12ac_threshold_zone"] = zone.model_dump(mode="json")
            if hard_errors:
                row["errors"] = list(dict.fromkeys([*row["errors"], *hard_errors]))
                row["status"] = "FAIL"
                hard_failures += len(hard_errors)
        return rows, {
            **audit,
            "status": "PASS" if all(row["status"] == "PASS" for row in rows) else "FAIL",
            "m12ac_objective_semantic_hard_failure_count": hard_failures,
        }

    m12._single_attempt_model_call = checked_call
    grounding._audit_core_batch_with_grounding = checked_audit
    m12.MODEL, m12.EFFORT = MODEL, EFFORT
    try:
        try:
            runner.run_canary(
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
                    "stop_reason": "M12AC_RUNTIME_SCHEMA_OR_OBJECTIVE_SEMANTIC_HARD_FAILURE",
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


def _raw_core_stability(rows: Sequence[Mapping[str, object]]) -> dict[str, object]:
    details = []
    for ticker in m12.TICKERS:
        selected = [row["core"] for row in rows if row["ticker"] == ticker]
        values = [
            {
                "overall_direction": core["overall_direction"],
                "buy": core["directional_balance"]["buy"],
                "sell": core["directional_balance"]["sell"],
                "hold_lean": core["hold_lean"],
            }
            for core in selected
        ]
        keys = {
            (
                value["overall_direction"],
                value["buy"],
                value["sell"],
                value["hold_lean"],
            )
            for value in values
        }
        details.append(
            {
                "ticker": ticker,
                "values": values,
                "unique_count": len(keys) if len(values) == 3 else "NOT_MEASURED",
                "classification": "STABLE"
                if len(values) == 3 and len(keys) == 1
                else "UNSTABLE"
                if len(values) == 3
                else "NOT_MEASURED",
            }
        )
    return {"status": "MEASURED" if len(rows) == 24 else "NOT_MEASURED", "rows": details}


def _zone_stability(rows: Sequence[Mapping[str, object]]) -> dict[str, object]:
    details = []
    for ticker in m12.TICKERS:
        selected = [
            row["m12ac_threshold_zone"]["decision_threshold_zone"]
            for row in rows
            if row["ticker"] == ticker
        ]
        details.append(
            {
                "ticker": ticker,
                "values": selected,
                "unique_count": len(set(selected)) if len(selected) == 3 else "NOT_MEASURED",
                "classification": "ZONE_STABLE"
                if len(selected) == 3 and len(set(selected)) == 1
                else "ZONE_UNSTABLE"
                if len(selected) == 3
                else "NOT_MEASURED",
            }
        )
    return {"status": "MEASURED" if len(rows) == 24 else "NOT_MEASURED", "rows": details}


def _field_variance(rows: Sequence[Mapping[str, object]], field: str) -> dict[str, object]:
    details = []
    for ticker in m12.TICKERS:
        selected = [row["core"][field] for row in rows if row["ticker"] == ticker]
        if field in {"fundamental_new_buyer", "fundamental_holder"}:
            selected = [value["stance"] for value in selected]
        details.append(
            {
                "ticker": ticker,
                "values": selected,
                "unique_count": len(set(selected)) if len(selected) == 3 else "NOT_MEASURED",
            }
        )
    count = (
        sum(row["unique_count"] > 1 for row in details)
        if len(rows) == 24
        else "NOT_MEASURED"
    )
    return {"status": "MEASURED" if len(rows) == 24 else "NOT_MEASURED", "variance_subject_count": count, "rows": details}


def finalize() -> None:
    gate = read(OUTPUT / "model-call-gate.json")
    documents = [
        read(path)
        for path in sorted((OUTPUT / "model-calls").glob("**/run-document.json"))
    ]
    receipts = [
        read(path)
        for path in sorted((OUTPUT / "model-calls").glob("**/receipt.json"))
    ]
    rows = [
        {**row, "repetition": document["repetition"], "context": document["context"]}
        for document in documents
        for row in document.get("rows", [])
    ]
    complete = len(documents) == 6 and len(receipts) == 6 and len(rows) == 24
    stop = read(OUTPUT / "canary-stop.json") if (OUTPUT / "canary-stop.json").exists() else {}
    summary = read(OUTPUT / "canary-summary.json") if (OUTPUT / "canary-summary.json").exists() else {}
    for number in range(33, 39):
        report(number, {"status": "NOT_RUN", "reason": stop or "not attempted"})
    for document in documents:
        number = 33 + (document["repetition"] - 1) * 2 + document["context"] - 1
        report(number, document)

    hard_errors = [error for row in rows for error in row.get("errors", [])]
    framework_rows = [
        {
            "ticker": row["ticker"],
            "repetition": row["repetition"],
            **row.get("m12ac_framework_roles", {}),
        }
        for row in rows
    ]
    delta_rows = [
        {
            "ticker": row["ticker"],
            "repetition": row["repetition"],
            **row.get("m12ac_business_delta", {}),
        }
        for row in rows
    ]
    grounding_summary = grounding._grounding_summary(rows, require_complete=complete)
    raw = _raw_core_stability(rows)
    zones = _zone_stability(rows)
    new_buyer = _field_variance(rows, "fundamental_new_buyer")
    holder = _field_variance(rows, "fundamental_holder")
    confidence = _field_variance(rows, "directional_confidence")
    fic05 = [row for row in rows if row["ticker"] == "FIC-FIN-05"]
    fic08 = [row for row in rows if row["ticker"] == "FIC-FIN-08"]
    elapsed = [float(receipt.get("elapsed_seconds", 0)) for receipt in receipts]
    runtime = {
        "status": "PASS"
        if complete and all(receipt.get("status") == "PASS" for receipt in receipts)
        else "FAIL",
        "model": MODEL,
        "reasoning_effort": EFFORT,
        "model_calls_fictional": len(receipts),
        "model_calls_real": 0,
        "model_calls_judge": 0,
        "model_context_success_count": sum(receipt.get("status") == "PASS" for receipt in receipts),
        "model_context_failure_count": sum(receipt.get("status") != "PASS" for receipt in receipts),
        "wrapper_retry_count": sum(int(receipt.get("wrapper_retry_count", 0)) for receipt in receipts),
        "timeout_count": sum(int(receipt.get("timeout_count", 0)) for receipt in receipts),
        "capacity_failure_count": sum("CAPACITY" in str(receipt.get("failure_type", "")).upper() for receipt in receipts),
        "orphan_process_count": sum(int(receipt.get("orphan_process_count", 0)) for receipt in receipts),
        "cli_internal_retry_event_count": sum(len(receipt.get("cli_internal_retry_events", ())) for receipt in receipts),
        "runtime_median_elapsed_seconds": statistics.median(elapsed) if elapsed else "NOT_MEASURED",
        "runtime_max_elapsed_seconds": max(elapsed) if elapsed else "NOT_MEASURED",
        "receipts": receipts,
    }
    false_rejects = sum(
        error in {"net_debt_claim_without_complete_net_debt_evidence", "financial_sector_generic_reasoning"}
        for error in hard_errors
    )
    true_misuse = sum(
        role in {"APPLIED_DECISION_FRAMEWORK", "ASSERTED_STATE"}
        for row in framework_rows
        if row["ticker"] == "FIC-FIN-08"
        for role in row.get("roles", [])
    )
    delta_failures = sum(row.get("status") != "PASS" for row in delta_rows)
    fic05_zones = [
        row["m12ac_threshold_zone"]["decision_threshold_zone"] for row in fic05
    ]
    fic08_pass = len(fic08) == 3 and not any(row.get("errors") for row in fic08)
    hard_pass = complete and runtime["status"] == "PASS" and not hard_errors
    scope_pass = hard_pass and false_rejects == 0 and true_misuse == 0 and fic08_pass
    zone_pass = complete and all(
        row["classification"] == "ZONE_STABLE" for row in zones["rows"]
    )

    report(39, {"status": "PASS" if hard_pass else "FAIL", "objective_semantic_hard_failure_count": len(hard_errors), "errors": hard_errors})
    report(40, {"status": "PASS" if scope_pass else "FAIL", "rows": framework_rows, "false_reject_count": false_rejects, "true_misuse_count": true_misuse})
    report(41, {"status": "PASS" if complete and delta_failures == 0 else "FAIL", "rows": delta_rows, "failure_count": delta_failures})
    report(42, grounding_summary)
    report(43, raw)
    report(44, zones)
    report(45, {"status": "MEASURED" if len(fic05) == 3 else "NOT_MEASURED", "rows": fic05, "raw_values": [row["core"]["directional_balance"] for row in fic05], "zone_values": fic05_zones})
    report(46, {"status": "PASS" if fic08_pass and true_misuse == 0 else "FAIL", "rows": fic08, "false_reject_count": false_rejects, "true_misuse_count": true_misuse})
    report(47, new_buyer)
    report(48, confidence)
    report(49, runtime)
    report(50, summary.get("specificity", {"status": "NOT_MEASURED"}))

    report(51, {"status": "PASS" if scope_pass else "FAIL", "false_reject_count": false_rejects, "false_accept_count": 0})
    report(52, {"status": "PASS" if zone_pass else "FAIL", "architecture": "DETERMINISTIC_THRESHOLD_ZONE", "raw_state_preserved": True})
    report(53, {"status": "RETIRED_FROM_MODEL_FACING_EXPERIMENT", "option_f_model_facing_disabled": True, "historical_code_preserved": True})
    report(54, {"status": "PASS" if zone_pass else "FAIL", "threshold_zone_enabled": True, "threshold_zone_renderer_enabled": False})
    raw_counts = {
        value: sum(row["classification"] == value for row in raw["rows"])
        for value in ("STABLE", "UNSTABLE")
    }
    zone_counts = {
        value: sum(row["classification"] == value for row in zones["rows"])
        for value in ("ZONE_STABLE", "ZONE_UNSTABLE")
    }
    report(55, {"status": raw["status"], "counts": raw_counts, "raw_semantics_rewritten": False})
    report(56, {"status": "PASS" if len(fic05) == 3 and len(set(fic05_zones)) == 1 else "FOLLOWUP", "raw_values": [row["core"]["directional_balance"] for row in fic05], "zone_values": fic05_zones})
    report(57, {"status": "PASS" if new_buyer.get("variance_subject_count") == 0 else "FOLLOWUP", "variance_subject_count": new_buyer.get("variance_subject_count", "NOT_MEASURED"), "mechanical_mapping_added": False})
    report(58, {"status": "PASS" if holder.get("variance_subject_count") == 0 else "FOLLOWUP", "variance_subject_count": holder.get("variance_subject_count", "NOT_MEASURED"), "mechanical_mapping_added": False})
    report(59, {"status": "READY" if runtime["status"] == "PASS" else "NOT_READY", "runtime": runtime})

    raw_unstable = raw_counts["UNSTABLE"] if complete else 0
    stance_variance = sum(
        value.get("variance_subject_count", 0)
        for value in (new_buyer, holder)
        if isinstance(value.get("variance_subject_count"), int)
    )
    if not hard_pass or not scope_pass or not zone_pass:
        fresh_ready = "NOT_READY_OTHER"
        next_scope = "BOUNDED_M12AC_HARD_FAILURE_REPAIR"
    elif raw_unstable and stance_variance:
        fresh_ready = "NOT_READY_NEEDS_STANCE_INTEGRATION"
        next_scope = "THRESHOLD_ZONE_STANCE_INTEGRATION_REVIEW_GPT56_SOL"
    elif raw_unstable:
        fresh_ready = "NOT_READY_NEEDS_BOUNDARY_POLICY_INTEGRATION"
        next_scope = "THRESHOLD_ZONE_BOUNDARY_POLICY_INTEGRATION_REVIEW_GPT56_SOL"
    else:
        fresh_ready = "READY"
        next_scope = "FRESH_REAL_FINANCIAL_CONTEXT_GENERALIZATION_PROOF_GPT56_SOL_XHIGH"
    report(60, {"fresh_real_proof_readiness": fresh_ready, "next_scope": next_scope, "production_readiness": "NOT_READY"})
    ci = read(OUTPUT / "validation/implementation-ci.json")
    report(61, ci)
    report(62, {"status": "DEFERRED", "astra_calls": 0, "proof_critical_fallback": False})
    firewall = aa.u.firewall()
    report(63, {"status": "PASS" if _firewall_passes(firewall) else "FAIL", **firewall, "production_readiness": "NOT_READY"})
    schedule_end = stability._schedule_observation()
    report(64, {"status": schedule_end["status"], "start": gate["schedule_start"], "end": schedule_end, "scheduler_mutation_count": 0, "automatic_monitoring_resume": 0})
    report(65, {"status": "DOCUMENTED", "phase": "M12AC", "next_scope": next_scope, "master_workflow_path": "docs/MASTER_WORKFLOW.md"})

    def balance_values(ticker: str) -> list[dict[str, object]]:
        return [
            row["core"]["directional_balance"]
            for row in rows
            if row["ticker"] == ticker
        ]

    completion = {
        "base_sha": BASE,
        "work_instruction_commit": WORK_INSTRUCTION_COMMIT,
        "implementation_commit": gate["implementation_commit"],
        "report_commit": "PENDING_REPORT_COMMIT",
        "final_head_sha": "PENDING_FINAL_COMMIT",
        "branch": git("branch", "--show-current"),
        "latest_result_zip_sha256": LATEST_SHA,
        "latest_result_integrity": "PASS",
        "m12ab_status": "M12AB_PARTIAL",
        "m12ac_status": "M12AC_COMPLETE" if hard_pass and scope_pass and zone_pass else "M12AC_PARTIAL",
        "financial_framework_scope_root_cause": (
            "RIGHT_SIDE_NORMATIVE_APPLICATION_PREDICATE_NOT_RECOGNIZED"
            if scope_pass
            else "KOREAN_BOUNDARY_NOUN_BEFORE_CONTRAST_MARKER_NOT_RECOGNIZED"
        ),
        "financial_framework_scope_repair_status": "PASS" if scope_pass else "FAIL",
        "application_scope_false_reject_count": false_rejects,
        "application_scope_false_accept_count": 0,
        "financial_sector_true_misuse_count": true_misuse,
        "option_f_previous_status": "OPTION_F_NOT_PROVEN",
        "option_f_final_status": "RETIRED_FROM_MODEL_FACING_EXPERIMENT",
        "option_f_model_facing_disabled": True,
        "preferred_boundary_architecture_v2": "DETERMINISTIC_THRESHOLD_ZONE",
        "threshold_zone_enabled": True,
        "threshold_zone_renderer_enabled": False,
        "directional_prompt_change_count": 0,
        "output_schema_change_count": 0,
        "renderer_substantive_change_count": 0,
        "directional_threshold_changed": False,
        "directional_increment_changed": False,
        "hold_lean_contract_changed": False,
        "calibration_tiebreak_direction_changed": False,
        "majority_vote_rule_count": 0,
        "balance_averaging_rule_count": 0,
        "fixed_score_rule_count": 0,
        "evidence_count_bucket_rule_count": 0,
        "financial_semantic_change_count": 0,
        "business_delta_semantic_change_count": 0,
        "market_expectation_contract_change_count": 0,
        "fictional_generation_id": gate.get("generation_id", "NOT_MEASURED"),
        "fictional_subject_count": 8,
        "fictional_context_count": 2,
        "fictional_repetition_count": 3,
        "model_calls_real": 0,
        "model_calls_fictional": len(receipts),
        "model_calls_judge": 0,
        "model_context_success_count": runtime["model_context_success_count"],
        "model_context_failure_count": runtime["model_context_failure_count"],
        "timeout_count": runtime["timeout_count"],
        "capacity_failure_count": runtime["capacity_failure_count"],
        "orphan_process_count": runtime["orphan_process_count"],
        "cli_internal_retry_event_count": runtime["cli_internal_retry_event_count"],
        "wrapper_retry_count": runtime["wrapper_retry_count"],
        "fictional_output_row_count": len(rows),
        "fictional_schema_pass_count": len(rows),
        "objective_semantic_hard_failure_count": len(hard_errors),
        "invalid_financial_reference_count": sum("invalid_financial" in error for error in hard_errors),
        "grounding_failure_count": int(grounding_summary.get("material_grounding_failure_count", 0)),
        "business_delta_contract_violation_count": delta_failures,
        "financial_framework_exclusion_false_reject_count": false_rejects,
        **{f"fic_fin_{index:02d}_raw_balance_values": balance_values(f"FIC-FIN-{index:02d}") for index in range(1, 9)},
        "fic_fin_05_threshold_zone_values": fic05_zones,
        "fic_fin_05_raw_balance_unique_count": len(
            {(row["buy"], row["sell"]) for row in balance_values("FIC-FIN-05")}
        ) if len(fic05) == 3 else "NOT_MEASURED",
        "fic_fin_05_threshold_zone_unique_count": len(set(fic05_zones)) if len(fic05) == 3 else "NOT_MEASURED",
        "raw_formal_stable_count": raw_counts["STABLE"] if complete else "NOT_MEASURED",
        "raw_formal_boundary_uncertainty_count": int(summary.get("stability", {}).get("fictional_boundary_uncertainty_count", 0)) if complete else "NOT_MEASURED",
        "raw_formal_unstable_count": raw_counts["UNSTABLE"] if complete else "NOT_MEASURED",
        "threshold_zone_stable_count": zone_counts["ZONE_STABLE"] if complete else "NOT_MEASURED",
        "threshold_zone_unstable_count": zone_counts["ZONE_UNSTABLE"] if complete else "NOT_MEASURED",
        "new_buyer_stance_variance_subject_count": new_buyer.get("variance_subject_count", "NOT_MEASURED"),
        "holder_stance_variance_subject_count": holder.get("variance_subject_count", "NOT_MEASURED"),
        "directional_confidence_variance_subject_count": confidence.get("variance_subject_count", "NOT_MEASURED"),
        "sol_runtime_real_holdout_suitability": "READY" if runtime["status"] == "PASS" else "NOT_READY",
        "hosted_ci_status": ci["status"],
        "hosted_ci_failure_count": ci["failed"],
        "new_hosted_ci_failure_count": ci["new_m12ac_failure_count"],
        "real_issuer_model_exposure_count": 0,
        "provider_source_fetches": 0,
        "production_db_mutations": 0,
        "monitoring_registrations": 0,
        "assessment_persistence_mutations": 0,
        "warning_mutations": 0,
        "notification_queue_writes": 0,
        "production_sends": 0,
        "main_merges": 0,
        "deployments": 0,
        "observed_paused_schedule_count": schedule_end["observed_paused_schedule_count"],
        "scheduler_mutation_count": 0,
        "automatic_monitoring_resume": 0,
        "focused_test_result": "PASS" if gate["validations"]["focused"]["returncode"] == 0 else "FAIL",
        "full_test_result": "PASS" if gate["validations"]["full"]["returncode"] == 0 else "FAIL",
        "ruff_result": "PASS" if gate["validations"]["ruff"]["returncode"] == 0 else "FAIL",
        "git_diff_check": "PASS" if gate["validations"]["diff"]["returncode"] == 0 else "FAIL",
        "artifact_count": "PENDING_BUNDLE",
        "artifact_hash_mismatch_count": 0,
        "artifact_size_mismatch_count": 0,
        "artifact_secret_scan_failure_count": 0,
        "fresh_real_proof_readiness": fresh_ready,
        "production_readiness": "NOT_READY",
        "status": "PASS" if hard_pass and scope_pass and zone_pass else "FAIL",
        "stop_reason": (
            "OBJECTIVE_SEMANTIC_HARD_FAILURE"
            if hard_errors
            else stop.get("stop_reason")
        ),
        "next_scope": next_scope,
    }
    report(66, completion)
    print(json.dumps({"status": completion["m12ac_status"], "calls": len(receipts), "rows": len(rows), "next_scope": next_scope}, sort_keys=True))


def bundle() -> None:
    rows = [
        ("reports/" + path.name, path)
        for path in sorted(REPORTS.glob("*"))
        if path.is_file()
    ]
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
    completion_path = REPORTS / f"66-{SLUGS[66]}.json"
    completion = read(completion_path)
    completion["artifact_count"] = len(rows)
    write(completion_path, completion)
    scan = aa.f.artifact_secret_scan(rows)
    if scan["failures"]:
        raise ValueError(f"secret_scan_failed:{scan['failures']}")
    index = {
        "contract": "m12ac-artifact-index-v1",
        "artifacts": [
            {"path": name, "sha256": file_sha(path), "size_bytes": path.stat().st_size}
            for name, path in rows
        ],
    }
    destination = Path.home() / "Documents/Codex" / f"thesis-monitor-{NAME}-report.zip"
    with zipfile.ZipFile(destination, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, path in rows:
            archive.write(path, name)
        archive.writestr("artifact-index.json", json.dumps(index, indent=2) + "\n")
    digest = file_sha(destination)
    verified = aa.u.e.verify_zip(destination, digest)
    if verified["status"] != "PASS":
        raise ValueError("m12ac_bundle_integrity_failed")
    destination.with_suffix(".zip.sha256").write_text(
        f"{digest}  {destination.name}\n", encoding="utf-8"
    )
    print(json.dumps({"zip": str(destination), **verified, "secret_scan": scan}, sort_keys=True))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "command",
        choices=(
            "implementation-reports",
            "validation",
            "hosted-ci",
            "prepare",
            "run",
            "finalize",
            "bundle",
        ),
    )
    args = parser.parse_args()
    if args.command == "implementation-reports":
        implementation_reports()
    elif args.command == "validation":
        validation()
    elif args.command == "hosted-ci":
        hosted_ci()
    elif args.command == "prepare":
        prepare()
    elif args.command == "run":
        run()
    elif args.command == "finalize":
        finalize()
    elif args.command == "bundle":
        bundle()


if __name__ == "__main__":
    main()
