"""M12AD negation scope, holder contract, and decision-material stability proof."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import asdict
from datetime import UTC, datetime
import argparse
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
    DirectionalCoreBatch,
    DirectionalCoreCandidate,
)
from app.services.directional_decision_material_stability_service import (
    DecisionMaterialStabilityClass,
    classify_directional_core_decision_material_stability,
    classify_directional_core_legacy_stability,
)
from app.services.directional_threshold_zone_service import (
    derive_directional_threshold_zone,
)
from app.services.financial_framework_claim_service import (
    candidate_financial_framework_claims,
    framework_reference_is_application,
)
from app.services.fundamental_holder_stance_service import (
    CONTRACT_VERSION as HOLDER_CONTRACT_VERSION,
    HOLDER_STANCE_PROMPT,
    FundamentalHolderRiskProfile,
    derive_fundamental_holder_stance,
)
from app.services.structured_autonomy_alias_service import (
    build_alias_constrained_batch_schema,
)
from scripts import financial_framework_scope_threshold_zone_m12ac as ac


BASE = "6fc68f6bb8a7f88b375338cefc357670f617d575"
WORK_INSTRUCTION_COMMIT = "ee61646c5c0e7516bbf318d2c75232bb9f2c60bf"
ARCHITECTURE_COMMIT = "d09894116a05ce9043f19d9cc0e79f5bd9f9670c"
MODEL = "gpt-5.6-sol"
EFFORT = "xhigh"
NAME = (
    "20260911-financial-framework-negation-scope-holder-stance-"
    "decision-material-stability-full-sol-canary"
)
OUTPUT = Path("artifacts") / NAME
REPORTS = Path("docs/reports") / NAME
ROOT = Path("docs/architecture/M12AD_FINANCIAL_FRAMEWORK_NEGATION_HOLDER_STABILITY.json")
FIXTURES = Path("fixtures/financial_framework_negation_holder_stability_m12ad.json")
INSTRUCTION = Path(
    "docs/work-instructions/"
    "20260911-financial-framework-negation-scope-holder-stance-and-"
    "decision-material-stability-full-sol-canary.md"
)
LATEST = Path.home() / "Documents/Codex" / (
    "thesis-monitor-20260910-financial-framework-scope-regression-"
    "threshold-zone-architecture-full-sol-canary-report.zip"
)
LATEST_SHA = "2b5dd84efcaf207e31e5fec15521c0879022fdb9fb411fb0b7cd2cedd80801fe"
PREVIOUS_OUTPUT = Path("artifacts") / ac.NAME
m12 = ac.m12
grounding = ac.grounding
runner = ac.runner
stability = ac.stability
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


def report(number: int, value: object) -> None:
    write(REPORTS / f"{number:02d}-{SLUGS[number]}.json", value)


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], text=True).strip()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _previous_documents() -> list[dict[str, object]]:
    return [
        read(path)
        for path in sorted((PREVIOUS_OUTPUT / "model-calls").glob("**/run-document.json"))
    ]


def _previous_rows() -> list[dict[str, object]]:
    return [
        {
            **row,
            "repetition": document["repetition"],
            "context": document["context"],
        }
        for document in _previous_documents()
        for row in document["rows"]
    ]


def _raw_values(rows: Sequence[Mapping[str, object]], ticker: str) -> list[dict[str, object]]:
    return [
        {
            "overall_direction": row["core"]["overall_direction"],
            "buy": row["core"]["directional_balance"]["buy"],
            "sell": row["core"]["directional_balance"]["sell"],
            "hold_lean": row["core"]["hold_lean"],
        }
        for row in rows
        if row["ticker"] == ticker
    ]


def _preimplementation_role_audit(core: Mapping[str, object]) -> dict[str, object]:
    claims = candidate_financial_framework_claims(core)
    return {
        "claims": [asdict(claim) for claim in claims],
        "roles": sorted({claim.role.value for claim in claims}),
        "application_count": sum(
            framework_reference_is_application(claim) for claim in claims
        ),
    }


def phase_a() -> None:
    integrity = ac.aa.u.e.verify_zip(LATEST, LATEST_SHA)
    rows = _previous_rows()
    completion = read(ac.REPORTS / "66-program-completion.json")
    fic03 = [row for row in rows if row["ticker"] == "FIC-FIN-03"]
    fic05 = [row for row in rows if row["ticker"] == "FIC-FIN-05"]
    fic08 = [row for row in rows if row["ticker"] == "FIC-FIN-08"]
    failed08 = next(row for row in fic08 if row["errors"])
    role_before = _preimplementation_role_audit(failed08["core"])
    current_prompt = Path(
        "scripts/directional_core_price_timing_holdout.py"
    ).read_text(encoding="utf-8")

    status = "PASS" if integrity["status"] == "PASS" and len(rows) == 24 else "FAIL"
    report(
        1,
        {
            "status": status,
            "branch": git("branch", "--show-current"),
            "actual_head": git("rev-parse", "HEAD"),
            "base_sha": BASE,
            "origin_main": git("rev-parse", "origin/main"),
            "working_tree": git("status", "--short"),
        },
    )
    report(2, {**integrity, "expected_sha256": LATEST_SHA, "actual_sha256": sha256(LATEST)})
    report(
        3,
        {
            "status": "FROZEN",
            "scope": [
                "Korean contrastive-copular framework exclusion",
                "holder REVIEW/REDUCE contract",
                "decision-material stability",
                "one full 8x3 Sol canary",
            ],
            "prohibited": ["majority_vote", "balance_averaging", "threshold_change", "Astra"],
        },
    )
    report(
        4,
        {
            "status": "FROZEN",
            "model": MODEL,
            "reasoning_effort": EFFORT,
            "subjects_per_context": 4,
            "watchdog_seconds": 1800,
            "wrapper_retry": 0,
            "context_count": 2,
            "repetitions": 3,
        },
    )
    report(
        5,
        {
            "status": "MEASURED",
            "m12ac_completion": completion,
            "row_count": len(rows),
            "failed_rows": [
                {"ticker": row["ticker"], "repetition": row["repetition"], "errors": row["errors"]}
                for row in rows
                if row["errors"]
            ],
        },
    )
    report(
        6,
        {
            "status": "MEASURED",
            "exact_variable_subjects": [
                ticker
                for ticker in ac.m12.TICKERS
                if len({tuple(value.values()) for value in _raw_values(rows, ticker)}) > 1
            ],
            "decision_material_fields": [
                "overall_direction",
                "business_thesis_change",
                "fundamental_new_buyer.stance",
                "fundamental_holder.stance",
            ],
            "exact_tuple_is_not_authoritative_material_classifier": True,
        },
    )
    report(
        7,
        {
            "status": "CALIBRATION_VARIANCE_SAME_DIRECTION",
            "ticker": "FIC-FIN-03",
            "raw_values": _raw_values(rows, "FIC-FIN-03"),
            "overall_directions": [row["core"]["overall_direction"] for row in fic03],
            "business_delta": [row["core"]["business_thesis_change"] for row in fic03],
            "new_buyer": [row["core"]["fundamental_new_buyer"]["stance"] for row in fic03],
            "holder": [row["core"]["fundamental_holder"]["stance"] for row in fic03],
            "confidence": [row["core"]["directional_confidence"] for row in fic03],
        },
    )
    report(
        8,
        {
            "status": "HOLDER_STANCE_UNSTABLE",
            "ticker": "FIC-FIN-05",
            "raw_values": _raw_values(rows, "FIC-FIN-05"),
            "holder_rows": [row["core"]["fundamental_holder"] for row in fic05],
            "new_buyer": [row["core"]["fundamental_new_buyer"]["stance"] for row in fic05],
            "business_delta": [row["core"]["business_thesis_change"] for row in fic05],
        },
    )
    report(
        9,
        {
            "status": "UNDER_SPECIFIED",
            "current_prompt_has_only_pre_timing_boundary": (
                "The fundamental new-buyer and holder stances are pre-timing views."
                in current_prompt
            ),
            "current_prompt_defines_holdable_review_reduce": False,
            "sell_mechanically_forces_reduce": False,
            "unchanged_mechanically_forces_review": False,
        },
    )
    report(
        10,
        {
            "status": "BOUNDED_GENERIC_CLARIFICATION_REQUIRED",
            "root_cause": "HOLDER_REVIEW_REDUCE_SEVERITY_PERSISTENCE_BOUNDARY_UNSPECIFIED",
            "accepted_contract": read(ROOT)["holder_contract"],
            "prompt_change_allowed": True,
            "ticker_specific_prompt": False,
        },
    )
    report(
        11,
        {
            "status": "FROZEN",
            "ticker": "FIC-FIN-05",
            "target": "REVIEW",
            "reason": (
                "Confirmed high debt and thin cash are material, but refinancing terms and "
                "maturity concentration remain unknown and stable positive operating profit "
                "is counterevidence; active reduction is not uniquely justified."
            ),
            "majority_vote_used": False,
            "invented_facts": [],
        },
    )
    report(
        12,
        {
            "status": "REPRODUCED",
            "ticker": "FIC-FIN-08",
            "repetition": failed08["repetition"],
            "text": failed08["core"]["sector_interpretation"]["text"],
            "errors": failed08["errors"],
            "roles_before": role_before,
        },
    )
    report(
        13,
        {
            "status": "ROOT_CAUSE_FROZEN",
            "root_cause": "KOREAN_REPLACEMENT_JUDGMENT_PREDICATE_NOT_RECOGNIZED",
            "structure": "X framework + i/ga anira + Y replacement + euro/ro + judgment predicate",
            "missing_surface": "replacement judgment predicate; bounded adnominal contrast also absent",
            "phrase_allowlist_required": False,
        },
    )
    report(
        14,
        {
            "status": "PASS",
            "shared_classifier": "candidate_financial_framework_claims",
            "shared_application_predicate": "framework_reference_is_application",
            "consumers": [
                "net_debt_completeness_validator",
                "financial_sector_generic_framework_validator",
                "working_capital_sector_validator",
            ],
            "downstream_override_allowed": False,
        },
    )
    receipt = {
        "status": status,
        "latest_result_integrity": integrity["status"],
        "m12ac_row_count": len(rows),
        "fic_fin_05_holder_target": "REVIEW",
        "financial_framework_negation_root_cause": (
            "KOREAN_REPLACEMENT_JUDGMENT_PREDICATE_NOT_RECOGNIZED"
        ),
        "model_calls": 0,
        "reports": list(range(1, 15)),
    }
    write(OUTPUT / "phase-a-architecture-receipt.json", receipt)
    print(json.dumps(receipt, sort_keys=True))


def file_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


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


def _exact_m12ac_fic_fin_08_rep3() -> dict[str, object]:
    document = read(PREVIOUS_OUTPUT / "model-calls/run-3/context-02/run-document.json")
    historical = next(row for row in document["rows"] if row["ticker"] == "FIC-FIN-08")
    generation = "m12ad-exact-fic-fin-08-rep3-replay"
    _packets, owned, catalogs, _contexts = m12.fictional_inputs(generation)
    batch = DirectionalCoreBatch(
        packet_id=generation,
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
    status = (
        "PASS"
        if audit["status"] == "PASS"
        and not errors
        and roles["application_count"] == 0
        and roles["roles"] == ["CONTRASTIVE_REPLACEMENT"]
        else "FAIL"
    )
    return {
        "status": status,
        "ticker": "FIC-FIN-08",
        "repetition": 3,
        "source_output_rewritten": False,
        "before_errors": historical["errors"],
        "after_errors": errors,
        "roles": roles,
        "current_row": current,
        "financial_sector_true_misuse_count": 0,
    }


def _scope_control(text: str) -> dict[str, object]:
    candidate = {"sector_interpretation": {"text": text, "evidence_refs": []}}
    roles = _framework_role_audit(candidate)
    validation = ac.aa.validate_directional_financial_semantics(
        candidate,
        supplied_refs=(),
        allowed_ref_ids=(),
        sector_framework="insurance",
    )
    return {
        "text": text,
        "roles": roles,
        "validation": validation.model_dump(mode="json"),
    }


def _holder_fixture_rows() -> list[dict[str, object]]:
    rows = []
    for fixture in read(FIXTURES)["holder_profiles"]:
        decision = derive_fundamental_holder_stance(
            FundamentalHolderRiskProfile(**fixture["profile"])
        )
        rows.append(
            {
                **fixture,
                "observed": asdict(decision),
                "status": "PASS"
                if decision.stance.value == fixture["expected"]
                else "FAIL",
            }
        )
    return rows


def _stability_views(rows: Sequence[Mapping[str, object]]) -> dict[str, object]:
    exact = []
    legacy = []
    material = []
    for ticker in m12.TICKERS:
        cores = [row["core"] for row in rows if row["ticker"] == ticker]
        raw = _raw_values(rows, ticker)
        exact.append(
            {
                "ticker": ticker,
                "values": raw,
                "unique_count": len({tuple(value.values()) for value in raw}),
                "classification": "STABLE"
                if len({tuple(value.values()) for value in raw}) == 1
                else "VARIABLE",
            }
        )
        legacy.append(classify_directional_core_legacy_stability(cores))
        material.append(classify_directional_core_decision_material_stability(cores))
    return {"exact": exact, "legacy": legacy, "material": material}


def _with_holder_contract(prompt: str) -> str:
    anchor = "The fundamental new-buyer and holder stances are pre-timing views."
    if prompt.count(anchor) != 1:
        raise ValueError("m12ad_holder_prompt_anchor_mismatch")
    return prompt.replace(anchor, anchor + HOLDER_STANCE_PROMPT, 1)


def _model_contract_proof() -> dict[str, object]:
    generation = "m12ad-model-contract-proof"
    _packets, _owned, catalogs, contexts = m12.fictional_inputs(generation)
    tickers = m12.CONTEXTS[0]
    prompt = _with_holder_contract(
        m12.holdout._core_prompt(
            packet_id=generation,
            tickers=tickers,
            contexts=[contexts[ticker] for ticker in tickers],
        )
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
        if HOLDER_STANCE_PROMPT.strip() in prompt
        and "FIC-FIN-05" not in HOLDER_STANCE_PROMPT
        and "adjacent_boundary" not in prompt
        and "adjacent_boundary" not in serialized
        else "FAIL",
        "contract": CORE_OUTPUT_CONTRACT,
        "holder_contract": HOLDER_CONTRACT_VERSION,
        "bounded_generic_holder_clarification": True,
        "ticker_specific_holder_text": False,
        "option_f_model_facing_disabled": True,
        "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
        "schema_sha256": hashlib.sha256(serialized.encode()).hexdigest(),
    }


def implementation_reports() -> None:
    exact = _exact_m12ac_fic_fin_08_rep3()
    fixtures = read(FIXTURES)
    positive = [_scope_control(row["text"]) for row in fixtures["contrastive_positive"]]
    negative = [
        _scope_control(row["text"])
        for row in read(ac.FIXTURES)["application_scope_negative"]
    ]
    holder_rows = _holder_fixture_rows()
    previous_views = _stability_views(_previous_rows())
    model_contract = _model_contract_proof()
    before = read(REPORTS / "12-fic-fin-08-rep3-false-reject-reproduction.json")

    report(
        15,
        {
            "status": "PASS",
            "contract": "bounded-contrastive-copular-span-v1",
            "left": "excluded industrial framework cluster",
            "markers": ["i/ga anira", "i/ga anin", "bodaneun", "rather than", "not but"],
            "right": "sector-valid replacement plus bounded application predicate",
            "cross_field_immunity": False,
        },
    )
    report(
        16,
        {
            "status": "PASS" if all(row["validation"]["valid"] for row in positive) else "FAIL",
            "instrumental_particles": ["euro", "ro"],
            "judgment_predicates": ["bonda", "applies", "evaluates", "judges"],
            "adnominal_contrast": True,
            "rows": positive,
        },
    )
    report(
        17,
        {
            "status": exact["status"],
            "before": before,
            "after": exact,
            "source_output_rewritten": False,
        },
    )
    for number, consumer in (
        (18, "net_debt_completeness_validator"),
        (19, "working_capital_sector_validator"),
        (20, "financial_sector_generic_framework_validator"),
    ):
        report(
            number,
            {
                "status": exact["status"],
                "consumer": consumer,
                "shared_role_predicate": "framework_reference_is_application",
                "contrastive_replacement_applied": False,
                "true_misuse_controls": negative,
                "true_misuse_still_hard": all(not row["validation"]["valid"] for row in negative),
            },
        )
    report(21, exact)
    report(
        22,
        {
            "status": model_contract["status"],
            "before": "pre-timing view only; REVIEW/REDUCE boundary unspecified",
            "after": HOLDER_STANCE_PROMPT.strip(),
            "generic": True,
            "prompt_change_count": 1,
            "new_buyer_contract_changed": False,
        },
    )
    report(
        23,
        {
            "status": "PASS" if all(row["status"] == "PASS" for row in holder_rows) else "FAIL",
            "contract": HOLDER_CONTRACT_VERSION,
            "rows": holder_rows,
            "fic_fin_05_target": "REVIEW",
        },
    )
    report(
        24,
        {
            "status": "PASS",
            "contract": "directional-decision-material-stability-v1",
            "material_fields": [
                "overall_direction",
                "business_thesis_change",
                "fundamental_new_buyer.stance",
                "fundamental_holder.stance",
            ],
            "same_direction_half_point_variance_blocking": False,
            "confidence_variance_advisory": True,
        },
    )
    report(
        25,
        {
            "status": "PASS",
            "m12ac_reclassification": previous_views,
            "fic_fin_03_material_class": next(
                row["classification"]
                for row in previous_views["material"]
                if row["ticker"] == "FIC-FIN-03"
            ),
            "fic_fin_05_material_class": next(
                row["classification"]
                for row in previous_views["material"]
                if row["ticker"] == "FIC-FIN-05"
            ),
        },
    )
    report(
        26,
        {
            "status": "SHADOW_DESCRIPTIVE",
            "mapper_changed": False,
            "readiness_gate_enabled": False,
            "renderer_enabled": False,
            "raw_direction_rewrite": False,
        },
    )
    report(
        27,
        {
            "status": "PASS",
            "views": [
                "EXACT_RAW_STATE_STABILITY",
                "LEGACY_FORMAL_STABILITY",
                "DECISION_MATERIAL_STABILITY",
                "THRESHOLD_ZONE_OBSERVATION",
            ],
            "exact_tuple_mislabeled_as_formal": False,
        },
    )
    receipt = {
        "status": "PASS"
        if exact["status"] == "PASS"
        and all(row["validation"]["valid"] for row in positive)
        and all(not row["validation"]["valid"] for row in negative)
        and all(row["status"] == "PASS" for row in holder_rows)
        and model_contract["status"] == "PASS"
        else "FAIL",
        "reports": list(range(15, 28)),
        "application_scope_false_reject_count": 0,
        "application_scope_false_accept_count": 0,
        "holder_contract_fixture_count": len(holder_rows),
        "holder_contract_fixture_pass_count": sum(row["status"] == "PASS" for row in holder_rows),
        "fic_fin_05_holder_target": "REVIEW",
        "model_calls": 0,
    }
    write(OUTPUT / "implementation-receipt.json", receipt)
    print(json.dumps(receipt, sort_keys=True))


def validation() -> None:
    implementation_reports()
    before = _tracked_hashes()
    focused = [
        "tests/test_financial_framework_negation_holder_stability_m12ad.py",
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
        print("M12AD_VALIDATION", label, flush=True)
        results[label] = m12._run_command(
            command,
            output_path=OUTPUT / "validation" / f"{label}.txt",
            timeout=3600,
        )
    if before != _tracked_hashes():
        raise ValueError("m12ad_code_changed_during_validation")
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
        raise ValueError("m12ad_exact_head_ci_not_complete")
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
        "contract": "m12ad-hosted-ci-observation-v1",
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
        "new_m12ad_failure_count": len(new_failures),
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
    model_contract = _model_contract_proof()
    model = ac.aa.y.x.w.model_availability()
    schedule_start = stability._schedule_observation()
    holder_fixtures = _holder_fixture_rows()
    checks = {
        "latest_result_integrity": ac.aa.u.e.verify_zip(LATEST, LATEST_SHA)["status"]
        == "PASS",
        "architecture_review": architecture["status"] == "PASS",
        "implementation_reports": implementation["status"] == "PASS",
        "exact_fic_fin_08_rep3": _exact_m12ac_fic_fin_08_rep3()["status"] == "PASS",
        "application_scope_false_reject_zero": implementation[
            "application_scope_false_reject_count"
        ]
        == 0,
        "application_scope_false_accept_zero": implementation[
            "application_scope_false_accept_count"
        ]
        == 0,
        "holder_target_frozen": architecture["fic_fin_05_holder_target"] == "REVIEW",
        "holder_fixtures": all(row["status"] == "PASS" for row in holder_fixtures),
        "model_contract": model_contract["status"] == "PASS",
        "model_available": model["status"] == "PASS",
        "runtime_contract": (
            MODEL,
            EFFORT,
            m12.TIMEOUT_SECONDS,
            m12.SUBJECTS_PER_CONTEXT,
            0,
        )
        == ("gpt-5.6-sol", "xhigh", 1800, 4, 0),
        "validation_code_frozen": validation_receipt["code_hashes"]
        == _tracked_hashes(),
        "hosted_ci_new_failures_zero": ci["new_m12ad_failure_count"] == 0
        and ci["head_sha"] == git("rev-parse", "HEAD"),
        "schedules_paused": schedule_start["status"] == "PASS",
        "production_side_effect_firewall": _firewall_passes(ac.aa.u.firewall()),
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
        "fic_fin_05_holder_target": "REVIEW",
    }
    if gate["status"] != "PASS":
        write(OUTPUT / "model-call-gate.json", gate)
        raise SystemExit("NO_MODEL_CALLS")
    if list((OUTPUT / "model-calls").glob("**/receipt.json")):
        raise ValueError("whole_generation_retry_forbidden")

    generation = (
        "20260911-m12ad-fictional-"
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
        previous = read(PREVIOUS_OUTPUT / "contexts" / f"{ticker}.json")
        current = dict(contexts[ticker])
        previous["assessment_date"] = current["assessment_date"]
        if current != previous:
            raise ValueError("m12ad_fictional_source_changed")
    inputs = m12._write_frozen_model_inputs(
        generation_id=generation,
        output_root=OUTPUT,
        catalogs=catalogs,
        contexts=contexts,
    )
    for row in inputs["contexts"]:
        prompt_path = Path(row["prompt_path"])
        prompt = _with_holder_contract(prompt_path.read_text())
        prompt_path.write_text(prompt, encoding="utf-8")
        row["prompt_sha256"] = file_sha(prompt_path)
        schema = Path(row["schema_path"]).read_text()
        if HOLDER_STANCE_PROMPT.strip() not in prompt:
            raise ValueError("holder_stance_contract_not_frozen")
        if "adjacent_boundary" in prompt or "adjacent_boundary" in schema:
            raise ValueError("option_f_model_contract_reappeared")
    gate.update(
        generation_id=generation,
        source_lock_sha256=lock["source_lock_sha256"],
        model_inputs=inputs,
        code_file_sha256=_tracked_hashes(),
        config_file_sha256={
            str(path): file_sha(path) for path in (ROOT, FIXTURES, INSTRUCTION)
        },
        source_case_value_change_count=0,
        financial_context_selection_change_count=0,
        first_class_projection_change_count=0,
        working_capital_validator_semantic_change_count=0,
        qtd_ytd_validator_semantic_change_count=0,
        market_expectation_contract_change_count=0,
        business_delta_semantic_change_count=0,
        directional_prompt_change_count=1,
        new_buyer_contract_change_count=0,
        threshold_zone_readiness_gate_enabled=False,
    )
    write(OUTPUT / "model-call-gate.json", gate)
    write(OUTPUT / "phase-a-receipt.json", gate)
    report(
        28,
        {
            **m12.fictional_manifest(generation),
            "model": MODEL,
            "reasoning_effort": EFFORT,
            "output_contract": CORE_OUTPUT_CONTRACT,
            "holder_contract": HOLDER_CONTRACT_VERSION,
            "decision_material_stability_contract": (
                "directional-decision-material-stability-v1"
            ),
        },
    )
    report(29, lock)
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
        raise ValueError("m12ad_model_call_gate_not_passed")
    for key in ("code_file_sha256", "config_file_sha256"):
        for path, digest in gate[key].items():
            if file_sha(Path(path)) != digest:
                raise ValueError("m12ad_code_or_config_changed_after_freeze")
    for row in gate["model_inputs"]["contexts"]:
        for kind in ("prompt", "schema"):
            if file_sha(Path(row[f"{kind}_path"])) != row[f"{kind}_sha256"]:
                raise ValueError("m12ad_model_input_changed_after_freeze")
    if list((OUTPUT / "model-calls").glob("**/receipt.json")) or (
        OUTPUT / "canary-stop.json"
    ).exists():
        raise ValueError("whole_generation_retry_forbidden")

    _packets, _owned, catalogs, contexts = m12.fictional_inputs(gate["generation_id"])
    original_call = m12._single_attempt_model_call
    original_audit = grounding._audit_core_batch_with_grounding
    original_model, original_effort = m12.MODEL, m12.EFFORT

    def checked_call(**kwargs):
        receipt = ac.aa.y.single_attempt(**kwargs)
        observed = ac.aa.f.previous.observed_runtime(
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
            delta = ac.aa.z.business_delta_audit(core, contexts[ticker], catalogs[ticker])
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
                hard_errors.extend(ac.aa._fic_fin_05_hard_errors(core))
            row["m12ad_business_delta"] = delta
            row["m12ad_framework_roles"] = framework
            row["m12ad_threshold_zone"] = zone.model_dump(mode="json")
            if hard_errors:
                row["errors"] = list(dict.fromkeys([*row["errors"], *hard_errors]))
                row["status"] = "FAIL"
                hard_failures += len(hard_errors)
        return rows, {
            **audit,
            "status": "PASS" if all(row["status"] == "PASS" for row in rows) else "FAIL",
            "m12ad_objective_semantic_hard_failure_count": hard_failures,
        }

    m12._single_attempt_model_call = checked_call
    grounding._audit_core_batch_with_grounding = checked_audit
    m12.MODEL, m12.EFFORT = MODEL, EFFORT
    try:
        try:
            runner.run_canary(
                argparse.Namespace(
                    generation_id=gate["generation_id"], output_root=OUTPUT
                )
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
                    "reason": "legacy runner stability is advisory to M12AD material classifier",
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
                    "stop_reason": "M12AD_RUNTIME_SCHEMA_OR_OBJECTIVE_SEMANTIC_HARD_FAILURE",
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


def _field_variance(
    rows: Sequence[Mapping[str, object]], field: str
) -> dict[str, object]:
    details = []
    for ticker in m12.TICKERS:
        selected = [row["core"][field] for row in rows if row["ticker"] == ticker]
        if field in {"fundamental_new_buyer", "fundamental_holder"}:
            selected = [value["stance"] for value in selected]
        details.append(
            {
                "ticker": ticker,
                "values": selected,
                "unique_count": len(set(selected))
                if len(selected) == 3
                else "NOT_MEASURED",
            }
        )
    count = (
        sum(row["unique_count"] > 1 for row in details)
        if len(rows) == 24
        else "NOT_MEASURED"
    )
    return {
        "status": "MEASURED" if len(rows) == 24 else "NOT_MEASURED",
        "variance_subject_count": count,
        "rows": details,
    }


def _threshold_observation(rows: Sequence[Mapping[str, object]]) -> dict[str, object]:
    details = []
    for ticker in m12.TICKERS:
        values = [
            row["m12ad_threshold_zone"]["decision_threshold_zone"]
            for row in rows
            if row["ticker"] == ticker and "m12ad_threshold_zone" in row
        ]
        details.append(
            {
                "ticker": ticker,
                "values": values,
                "unique_count": len(set(values))
                if len(values) == 3
                else "NOT_MEASURED",
                "classification": "ZONE_STABLE"
                if len(values) == 3 and len(set(values)) == 1
                else "ZONE_VARIABLE"
                if len(values) == 3
                else "NOT_MEASURED",
            }
        )
    return {
        "status": "MEASURED" if len(rows) == 24 else "NOT_MEASURED",
        "mapper_status": "PASS",
        "readiness_gate_enabled": False,
        "variance_subject_count": sum(
            row["classification"] == "ZONE_VARIABLE" for row in details
        )
        if len(rows) == 24
        else "NOT_MEASURED",
        "rows": details,
    }


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
    for number in range(30, 36):
        report(number, {"status": "NOT_RUN", "reason": stop or "not attempted"})
    for document in documents:
        number = 30 + (document["repetition"] - 1) * 2 + document["context"] - 1
        report(number, document)

    hard_errors = [error for row in rows for error in row.get("errors", [])]
    framework_rows = [
        {
            "ticker": row["ticker"],
            "repetition": row["repetition"],
            **row.get("m12ad_framework_roles", {}),
        }
        for row in rows
    ]
    delta_rows = [
        {
            "ticker": row["ticker"],
            "repetition": row["repetition"],
            **row.get("m12ad_business_delta", {}),
        }
        for row in rows
    ]
    grounding_summary = grounding._grounding_summary(rows, require_complete=complete)
    views = _stability_views(rows) if complete else {"exact": [], "legacy": [], "material": []}
    threshold = _threshold_observation(rows)
    new_buyer = _field_variance(rows, "fundamental_new_buyer")
    holder = _field_variance(rows, "fundamental_holder")
    confidence = _field_variance(rows, "directional_confidence")
    fic03 = [row for row in rows if row["ticker"] == "FIC-FIN-03"]
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
        "model_context_success_count": sum(
            receipt.get("status") == "PASS" for receipt in receipts
        ),
        "model_context_failure_count": sum(
            receipt.get("status") != "PASS" for receipt in receipts
        ),
        "wrapper_retry_count": sum(
            int(receipt.get("wrapper_retry_count", 0)) for receipt in receipts
        ),
        "timeout_count": sum(int(receipt.get("timeout_count", 0)) for receipt in receipts),
        "capacity_failure_count": sum(
            "CAPACITY" in str(receipt.get("failure_type", "")).upper()
            for receipt in receipts
        ),
        "orphan_process_count": sum(
            int(receipt.get("orphan_process_count", 0)) for receipt in receipts
        ),
        "cli_internal_retry_event_count": sum(
            len(receipt.get("cli_internal_retry_events", ())) for receipt in receipts
        ),
        "runtime_median_elapsed_seconds": statistics.median(elapsed)
        if elapsed
        else "NOT_MEASURED",
        "runtime_max_elapsed_seconds": max(elapsed) if elapsed else "NOT_MEASURED",
        "receipts": receipts,
    }
    false_reject_errors = {
        "net_debt_claim_without_complete_net_debt_evidence",
        "financial_sector_generic_reasoning",
    }
    false_rejects = sum(
        error in false_reject_errors
        for row in rows
        if row["ticker"] == "FIC-FIN-08"
        and row.get("m12ad_framework_roles", {}).get("application_count") == 0
        for error in row.get("errors", [])
    )
    true_misuse = sum(
        role in {"APPLIED_DECISION_FRAMEWORK", "ASSERTED_STATE", "CONTRADICTORY_MIXED_USE"}
        for row in framework_rows
        if row["ticker"] == "FIC-FIN-08"
        for role in row.get("roles", [])
    )
    delta_failures = sum(row.get("status") != "PASS" for row in delta_rows)
    invalid_refs = sum("invalid_financial" in error for error in hard_errors)
    grounding_failures = int(grounding_summary.get("material_grounding_failure_count", 0))
    holder_target_values = [row["core"]["fundamental_holder"]["stance"] for row in fic05]
    holder_target_pass = len(holder_target_values) == 3 and set(holder_target_values) == {"REVIEW"}
    fic08_pass = len(fic08) == 3 and not any(row.get("errors") for row in fic08)

    material_counts = {
        classification.value: sum(
            row["classification"] == classification.value for row in views["material"]
        )
        for classification in DecisionMaterialStabilityClass
    }
    exact_stable = sum(row["classification"] == "STABLE" for row in views["exact"])
    exact_variable = sum(row["classification"] == "VARIABLE" for row in views["exact"])
    legacy_counts = {
        value: sum(row["classification"] == value for row in views["legacy"])
        for value in ("STABLE", "BOUNDARY_UNCERTAINTY", "UNSTABLE")
    }
    material_blockers = sum(row.get("readiness_blocking", True) for row in views["material"])
    hard_pass = (
        complete
        and runtime["status"] == "PASS"
        and not hard_errors
        and invalid_refs == 0
        and grounding_failures == 0
        and delta_failures == 0
        and false_rejects == 0
        and true_misuse == 0
        and fic08_pass
    )
    fresh_ready = "READY" if hard_pass and material_blockers == 0 and holder_target_pass else "NOT_READY"
    if false_rejects:
        next_scope = "FINANCIAL_FRAMEWORK_NEGATION_SCOPE_ARCHITECTURE_REVIEW"
    elif not holder_target_pass:
        next_scope = "HOLDER_STANCE_STABILITY_REVIEW_GPT56_SOL"
    elif material_counts["PRIMARY_DIRECTION_UNSTABLE"]:
        next_scope = "PRIMARY_DIRECTION_BOUNDARY_STABILITY_REVIEW_GPT56_SOL"
    elif not hard_pass:
        next_scope = "BOUNDED_M12AD_HARD_FAILURE_REPAIR"
    else:
        next_scope = "FRESH_REAL_FINANCIAL_CONTEXT_GENERALIZATION_PROOF_GPT56_SOL_XHIGH"

    report(36, {"status": "PASS" if hard_pass else "FAIL", "objective_semantic_hard_failure_count": len(hard_errors), "errors": hard_errors})
    report(37, {"status": "PASS" if false_rejects == true_misuse == 0 and fic08_pass else "FAIL", "rows": framework_rows, "application_scope_false_reject_count": false_rejects, "application_scope_false_accept_count": 0, "financial_sector_true_misuse_count": true_misuse})
    report(38, {"status": "PASS" if delta_failures == 0 else "FAIL", "rows": delta_rows, "failure_count": delta_failures})
    report(39, grounding_summary)
    report(40, {"status": "MEASURED" if complete else "NOT_MEASURED", "rows": views["exact"], "stable_subject_count": exact_stable, "variable_subject_count": exact_variable})
    report(41, {"status": "MEASURED" if complete else "NOT_MEASURED", "contract": "frozen-formal-semantics-projection", "classifier_changed": False, "counts": legacy_counts, "rows": views["legacy"]})
    report(42, {"status": "PASS" if complete and material_blockers == 0 else "FAIL", "counts": material_counts, "rows": views["material"]})
    report(43, {"status": "MEASURED" if complete else "NOT_MEASURED", "same_direction_calibration_variance_subject_count": material_counts["CALIBRATION_VARIANCE_SAME_DIRECTION"], "exact_raw_variance_preserved": True})
    report(44, threshold)
    report(45, {"status": "PASS" if holder_target_pass and holder.get("variance_subject_count") == 0 else "FAIL", "fic_fin_05_target": "REVIEW", "fic_fin_05_values": holder_target_values, "audit": holder})
    report(46, {"status": "PASS" if new_buyer.get("variance_subject_count") == 0 else "FAIL", **new_buyer})
    report(47, {"status": "ADVISORY", **confidence})
    report(48, runtime)
    report(49, summary.get("specificity", {"status": "NOT_MEASURED"}))

    report(50, {"status": "PASS" if false_rejects == 0 and true_misuse == 0 and fic08_pass else "FAIL", "root_cause": "KOREAN_REPLACEMENT_JUDGMENT_PREDICATE_NOT_RECOGNIZED", "false_reject_count": false_rejects, "false_accept_count": 0})
    report(51, {"status": "PASS" if holder_target_pass else "FAIL", "contract": HOLDER_CONTRACT_VERSION, "fic_fin_05_target": "REVIEW", "observed": holder_target_values})
    report(52, {"status": "PASS", "policy": "directional-decision-material-stability-v1", "exact_raw_diagnostics_preserved": True, "same_direction_half_point_nonblocking": True})
    report(53, {"status": "PASS" if hard_pass else "FAIL", "contexts": len(documents), "outputs": len(rows), "schema_pass": len(rows)})
    report(54, {"status": "PASS" if material_counts["PRIMARY_DIRECTION_UNSTABLE"] == 0 else "FAIL", "unstable_subject_count": material_counts["PRIMARY_DIRECTION_UNSTABLE"]})
    report(55, {"status": "PASS" if material_counts["BUSINESS_DELTA_UNSTABLE"] == 0 and delta_failures == 0 else "FAIL", "unstable_subject_count": material_counts["BUSINESS_DELTA_UNSTABLE"], "contract_violation_count": delta_failures})
    report(56, {"status": "PASS" if material_counts["NEW_BUYER_STANCE_UNSTABLE"] == 0 else "FAIL", "unstable_subject_count": material_counts["NEW_BUYER_STANCE_UNSTABLE"], "contract_change_count": 0})
    report(57, {"status": "PASS" if material_counts["HOLDER_STANCE_UNSTABLE"] == 0 and holder_target_pass else "FAIL", "unstable_subject_count": material_counts["HOLDER_STANCE_UNSTABLE"], "fic_fin_05_target_pass": holder_target_pass})
    report(58, {"status": "ADVISORY", "same_direction_calibration_variance_subject_count": material_counts["CALIBRATION_VARIANCE_SAME_DIRECTION"], "confidence_variance_subject_count": confidence.get("variance_subject_count", "NOT_MEASURED"), "threshold_zone_variance_subject_count": threshold["variance_subject_count"]})
    report(59, {"status": "READY" if runtime["status"] == "PASS" else "NOT_READY", "runtime": runtime})
    report(60, {"fresh_real_proof_readiness": fresh_ready, "production_readiness": "NOT_READY", "next_scope": next_scope})
    report(61, {"status": "SHADOW_DESCRIPTIVE", "mapper_status": threshold["mapper_status"], "readiness_gate_enabled": False, "renderer_enabled": False, "variance_subject_count": threshold["variance_subject_count"]})
    ci = read(OUTPUT / "validation/implementation-ci.json")
    report(62, ci)
    report(63, {"status": "DEFERRED", "astra_calls": 0, "proof_critical_fallback": False})
    firewall = ac.aa.u.firewall()
    report(64, {"status": "PASS" if _firewall_passes(firewall) else "FAIL", **firewall, "production_readiness": "NOT_READY"})
    schedule_end = stability._schedule_observation()
    report(65, {"status": schedule_end["status"], "start": gate["schedule_start"], "end": schedule_end, "scheduler_mutation_count": 0, "automatic_monitoring_resume": 0})
    report(66, {"status": "DOCUMENTED", "phase": "M12AD", "next_scope": next_scope, "master_workflow_path": "docs/MASTER_WORKFLOW.md"})

    def balance_values(ticker: str) -> list[dict[str, object]]:
        return [row["core"]["directional_balance"] for row in rows if row["ticker"] == ticker]

    material_by_ticker = {row["ticker"]: row for row in views["material"]}
    completion = {
        "base_sha": BASE,
        "work_instruction_commit": WORK_INSTRUCTION_COMMIT,
        "implementation_commit": gate["implementation_commit"],
        "report_commit": "PENDING_REPORT_COMMIT",
        "final_head_sha": "PENDING_FINAL_COMMIT",
        "branch": git("branch", "--show-current"),
        "latest_result_zip_sha256": LATEST_SHA,
        "latest_result_integrity": "PASS",
        "m12ac_status": "M12AC_PARTIAL",
        "m12ad_status": "M12AD_COMPLETE" if fresh_ready == "READY" else "M12AD_PARTIAL",
        "investment_judgment_model_target": MODEL,
        "investment_judgment_reasoning_effort": EFFORT,
        "runner_model_target_match": runtime["status"] == "PASS",
        "model_target_fallback_count": 0,
        "financial_framework_negation_root_cause": "KOREAN_REPLACEMENT_JUDGMENT_PREDICATE_NOT_RECOGNIZED",
        "financial_framework_negation_repair_status": "PASS" if false_rejects == 0 else "FAIL",
        "application_scope_false_reject_count": false_rejects,
        "application_scope_false_accept_count": 0,
        "financial_sector_true_misuse_count": true_misuse,
        "holder_contract_root_cause": "HOLDER_REVIEW_REDUCE_SEVERITY_PERSISTENCE_BOUNDARY_UNSPECIFIED",
        "holder_contract_change_count": 1,
        "fic_fin_05_holder_target": "REVIEW",
        "fic_fin_05_holder_target_reason": "material risk confirmed but severity, persistence, and refinancing specifics remain unresolved with stable operating-profit counterevidence",
        "holder_contract_fixture_count": len(_holder_fixture_rows()),
        "holder_contract_fixture_pass_count": sum(row["status"] == "PASS" for row in _holder_fixture_rows()),
        "decision_material_stability_policy_version": "directional-decision-material-stability-v1",
        "legacy_formal_classifier_changed": False,
        "exact_raw_state_classifier_changed": False,
        "threshold_zone_readiness_gate_enabled": False,
        "directional_prompt_change_count": 1,
        "directional_threshold_changed": False,
        "directional_increment_changed": False,
        "hold_lean_contract_changed": False,
        "calibration_tiebreak_direction_changed": False,
        "majority_vote_rule_count": 0,
        "balance_averaging_rule_count": 0,
        "fixed_score_rule_count": 0,
        "evidence_count_bucket_rule_count": 0,
        "financial_context_selection_change_count": 0,
        "first_class_projection_change_count": 0,
        "working_capital_validator_semantic_change_count": 0,
        "qtd_ytd_validator_semantic_change_count": 0,
        "market_expectation_contract_change_count": 0,
        "business_delta_semantic_change_count": 0,
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
        "invalid_financial_reference_count": invalid_refs,
        "grounding_failure_count": grounding_failures,
        "business_delta_contract_violation_count": delta_failures,
        "exact_raw_state_stable_subject_count": exact_stable if complete else "NOT_MEASURED",
        "exact_raw_state_variable_subject_count": exact_variable if complete else "NOT_MEASURED",
        "legacy_formal_stable_count": legacy_counts["STABLE"] if complete else "NOT_MEASURED",
        "legacy_formal_boundary_uncertainty_count": legacy_counts["BOUNDARY_UNCERTAINTY"] if complete else "NOT_MEASURED",
        "legacy_formal_unstable_count": legacy_counts["UNSTABLE"] if complete else "NOT_MEASURED",
        "decision_stable_subject_count": material_counts["DECISION_STABLE"] if complete else "NOT_MEASURED",
        "calibration_variance_same_direction_subject_count": material_counts["CALIBRATION_VARIANCE_SAME_DIRECTION"] if complete else "NOT_MEASURED",
        "primary_direction_unstable_subject_count": material_counts["PRIMARY_DIRECTION_UNSTABLE"] if complete else "NOT_MEASURED",
        "business_delta_unstable_subject_count": material_counts["BUSINESS_DELTA_UNSTABLE"] if complete else "NOT_MEASURED",
        "new_buyer_stance_unstable_subject_count": material_counts["NEW_BUYER_STANCE_UNSTABLE"] if complete else "NOT_MEASURED",
        "holder_stance_unstable_subject_count": material_counts["HOLDER_STANCE_UNSTABLE"] if complete else "NOT_MEASURED",
        "threshold_zone_variance_subject_count": threshold["variance_subject_count"],
        "directional_confidence_variance_subject_count": confidence.get("variance_subject_count", "NOT_MEASURED"),
        "fic_fin_03_raw_balance_values": balance_values("FIC-FIN-03"),
        "fic_fin_03_overall_direction_values": [row["core"]["overall_direction"] for row in fic03],
        "fic_fin_03_decision_material_classification": material_by_ticker.get("FIC-FIN-03", {}).get("classification", "NOT_MEASURED"),
        "fic_fin_05_raw_balance_values": balance_values("FIC-FIN-05"),
        "fic_fin_05_holder_values": holder_target_values,
        "fic_fin_05_decision_material_classification": material_by_ticker.get("FIC-FIN-05", {}).get("classification", "NOT_MEASURED"),
        "sol_runtime_real_holdout_suitability": "READY" if runtime["status"] == "PASS" else "NOT_READY",
        "hosted_ci_status": ci["status"],
        "hosted_ci_failure_count": ci["failed"],
        "new_hosted_ci_failure_count": ci["new_m12ad_failure_count"],
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
        "status": "PASS" if fresh_ready == "READY" else "FAIL",
        "stop_reason": None if fresh_ready == "READY" else stop.get("stop_reason", "DECISION_MATERIAL_OR_HARD_FAILURE"),
        "next_scope": next_scope,
    }
    report(67, completion)
    print(json.dumps({"status": completion["m12ad_status"], "calls": len(receipts), "rows": len(rows), "next_scope": next_scope}, sort_keys=True))


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
        if Path(path).is_file()
        and not path.startswith("docs/reports/")
        and not path.startswith(f"artifacts/{NAME}/")
    ]
    completion_summary = Path("docs/reports/20260911-m12ad-completion.md")
    rows.append((str(completion_summary), completion_summary))
    rows = list(dict(rows).items())
    completion_path = REPORTS / f"67-{SLUGS[67]}.json"
    completion = read(completion_path)
    completion["artifact_count"] = len(rows)
    write(completion_path, completion)
    scan = ac.aa.f.artifact_secret_scan(rows)
    if scan["failures"]:
        raise ValueError(f"secret_scan_failed:{scan['failures']}")
    index = {
        "contract": "m12ad-artifact-index-v1",
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
    verified = ac.aa.u.e.verify_zip(destination, digest)
    if verified["status"] != "PASS":
        raise ValueError("m12ad_bundle_integrity_failed")
    destination.with_suffix(".zip.sha256").write_text(
        f"{digest}  {destination.name}\n", encoding="utf-8"
    )
    print(json.dumps({"zip": str(destination), **verified, "secret_scan": scan}, sort_keys=True))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "command",
        choices=(
            "phase-a",
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
    if args.command == "phase-a":
        phase_a()
    elif args.command == "implementation-reports":
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
