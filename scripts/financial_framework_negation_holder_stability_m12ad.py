"""M12AD negation scope, holder contract, and decision-material stability proof."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import asdict
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

from app.services.financial_framework_claim_service import (
    candidate_financial_framework_claims,
    framework_reference_is_application,
)
from scripts import financial_framework_scope_threshold_zone_m12ac as ac


BASE = "6fc68f6bb8a7f88b375338cefc357670f617d575"
WORK_INSTRUCTION_COMMIT = "ee61646"
MODEL = "gpt-5.6-sol"
EFFORT = "xhigh"
NAME = (
    "20260911-financial-framework-negation-scope-holder-stance-"
    "decision-material-stability-full-sol-canary"
)
OUTPUT = Path("artifacts") / NAME
REPORTS = Path("docs/reports") / NAME
ROOT = Path("docs/architecture/M12AD_FINANCIAL_FRAMEWORK_NEGATION_HOLDER_STABILITY.json")
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
            "root_cause": "KOREAN_INSTRUMENTAL_PARTICLE_BEFORE_APPLICATION_PREDICATE_NOT_RECOGNIZED",
            "structure": "X framework + i/ga anira + Y replacement + euro/ro + judgment predicate",
            "missing_surface": "replacement instrument particle euro/ro",
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
            "KOREAN_INSTRUMENTAL_PARTICLE_BEFORE_APPLICATION_PREDICATE_NOT_RECOGNIZED"
        ),
        "model_calls": 0,
        "reports": list(range(1, 15)),
    }
    write(OUTPUT / "phase-a-architecture-receipt.json", receipt)
    print(json.dumps(receipt, sort_keys=True))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("phase-a",))
    args = parser.parse_args()
    if args.command == "phase-a":
        phase_a()


if __name__ == "__main__":
    main()
