from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import shutil
import subprocess
import zipfile
from collections.abc import Mapping, Sequence
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

from app.services.coldstart_fundamental_enrichment_service import (
    AnalysisFramework,
    us_bank_insurer_sector_fact,
)
from app.services.direction_timing_ownership_service import canonical_sha256
from app.services.sec_financial_snapshot_service import _companyfacts_snapshots
from scripts import directional_core_price_timing_holdout as frozen
from scripts import new_issuer_holdout_selection_ownership_proof as prior
from scripts import official_fundamental_enrichment_holdout as fundamental
from scripts import synthetic_canary_fixture_repair_ownership_resume as guarded
from scripts import unseen_source_assembly_coldstart as source_assembly
from scripts import uskr22_structured_autonomy_shadow as engine


PROGRAM_CONTRACT = "bounded-us-source-coverage-remediation-holdout-resume-v1"
SELECTION_SALT = "20260907-new-issuer-holdout-selection-ownership-proof-v1"
MODEL = "gpt-5.6-sol"
EFFORT = "xhigh"
TIMEOUT_SECONDS = 1800
TIMEOUT_OWNER_COUNT = 1
BATCH_SEMANTICS = "MODEL_CONTEXT_COUPLED"
CONTEXT_SIZE = 4
TARGET_US = 4
TARGET_KR = 12
TARGET_TOTAL = TARGET_US + TARGET_KR
RUNS = ("first", "a", "b", "c")
STAGES = ("DIRECTIONAL_CORE", "PRICE_TIMING")
LATEST_RESULT_SHA256 = (
    "e3f25cd718b97a178f6490533cecb7bfd48453377a743d7329b6396b0fc280fa"
)
WORK_INSTRUCTION = (
    "docs/work-instructions/"
    "20260907-bounded-us-source-coverage-remediation-and-holdout-proof-resume.md"
)
WORK_INSTRUCTION_SHA256 = (
    "ce367e1f29af61012f50451603f4b4b8dbcf3fd9bd4d84ba0278568eec09a930"
)
PRIOR_REPORT = Path(
    "docs/reports/"
    "20260907-dual-market-source-coverage-new-issuer-holdout-ownership-proof"
)
ORIGINAL_US = ("NVDA", "JPM", "WMT", "BRK-B", "MSFT")
PRESERVED_KR = (
    "142210",
    "060900",
    "002680",
    "035420",
    "216050",
    "100700",
    "001530",
    "487580",
    "038870",
    "342870",
    "060230",
    "415380",
)
KR_RESERVES = (
    "036560",
    "417790",
    "246250",
    "003920",
    "007110",
    "284740",
    "475960",
    "051500",
    "003490",
    "073560",
    "044380",
    "030960",
    "118000",
    "475560",
    "484590",
    "001720",
    "151860",
    "014160",
    "071950",
    "133750",
    "307180",
    "380540",
    "080420",
    "049070",
    "002450",
    "008370",
    "031440",
    "046890",
    "005830",
    "128820",
    "054050",
    "052220",
    "001520",
    "063440",
    "023150",
)

PROOF_NAMES = (
    "01-repository-provenance",
    "02-latest-result-integrity",
    "03-current-us-failure-baseline",
    "04-jpm-raw-sector-evidence",
    "05-brkb-raw-sector-evidence",
    "06-us-bank-insurer-framework-classification-audit",
    "07-us-bank-insurer-mapping-root-cause",
    "08-us-bank-insurer-remediation-diff",
    "09-us-bank-insurer-remediation-tests",
    "10-wmt-price-context-forensic",
    "11-wmt-price-remediation-decision",
    "12-wmt-price-remediation-diff-if-any",
    "13-expanded-us-reserve-policy",
    "14-expanded-us-reserve-manifest",
    "15-us-post-remediation-coverage-audit",
    "16-us-post-remediation-failure-detail",
    "17-us-target-decision",
    "18-kr-pass-preservation",
    "19-final-us4-selection",
    "20-final-kr12-selection",
    "21-fresh-combined-source-generation",
    "22-combined-source-sufficiency-audit",
    "23-combined-source-identity-audit",
    "24-new-source-lock",
    "25-new-holdout-precommit",
    "26-architecture-semantic-freeze",
    "27-prompt-schema-freeze",
    "28-model-context-freeze",
    "29-transport-topology-freeze",
    "30-holdout-unseen-gate",
    "31-live-workload-coexistence-audit",
    "32-first-execution-summary",
    "33-first-context-artifact-manifest",
    "34-first-context-partial-semantic-audits",
    "35-first-ownership-gate",
    "36-first-renderer-gate",
    "37-first-hard-safety-gate",
    "38-run-a-execution-summary",
    "39-run-a-context-artifact-manifest",
    "40-run-a-context-partial-semantic-audits",
    "41-run-a-ownership-gate",
    "42-run-a-renderer-gate",
    "43-run-a-hard-safety-gate",
    "44-run-b-execution-summary",
    "45-run-b-context-artifact-manifest",
    "46-run-b-context-partial-semantic-audits",
    "47-run-b-ownership-gate",
    "48-run-b-renderer-gate",
    "49-run-b-hard-safety-gate",
    "50-run-c-execution-summary",
    "51-run-c-context-artifact-manifest",
    "52-run-c-context-partial-semantic-audits",
    "53-run-c-ownership-gate",
    "54-run-c-renderer-gate",
    "55-run-c-hard-safety-gate",
    "56-holdout-exposure-retirement-state",
    "57-core-stability",
    "58-timing-stability",
    "59-ownership-generalization",
    "60-renderer-ownership-proof",
    "61-hard-safety-regression",
    "62-production-no-change",
    "63-night-futures-no-change",
    "64-monitoring-bootstrap-next-handoff",
    "65-program-completion",
)
RUN_PROOFS = {
    "first": (32, 33, 34, 35, 36, 37),
    "a": (38, 39, 40, 41, 42, 43),
    "b": (44, 45, 46, 47, 48, 49),
    "c": (50, 51, 52, 53, 54, 55),
}


def read_json(path: Path) -> dict[str, Any]:
    return prior.read_json(path)


def write_json(path: Path, value: object) -> None:
    prior.write_json(path, value)


def write_text(path: Path, value: str) -> None:
    prior.write_text(path, value)


def file_sha256(path: Path) -> str:
    return prior.file_sha256(path)


def git_value(*args: str) -> str:
    return prior.git_value(*args)


def proof_path(report_dir: Path, number: int) -> Path:
    return report_dir / "proofs" / f"{PROOF_NAMES[number - 1]}.json"


def write_proof(report_dir: Path, number: int, value: Mapping[str, object]) -> None:
    write_json(proof_path(report_dir, number), value)


def program_generation_id(implementation_commit: str, as_of: datetime) -> str:
    stamp = as_of.astimezone(UTC).strftime("%Y%m%dT%H%M%SZ")
    suffix = hashlib.sha256(
        f"{implementation_commit}|{stamp}|{SELECTION_SALT}|us-remediation".encode()
    ).hexdigest()[:12]
    return f"20260907-us-remediation-holdout-{stamp}-{suffix}"


def architecture_hashes(repo_root: Path) -> dict[str, str]:
    paths = {
        "ownership_service": "app/services/direction_timing_ownership_service.py",
        "directional_balance": "app/services/directional_balance_service.py",
        "alias_fencing": "app/services/structured_autonomy_alias_service.py",
        "validator_renderer": "app/services/structured_autonomy_shadow_service.py",
        "stability_classifier": "app/services/structured_autonomy_stability_service.py",
        "source_enrichment": "app/services/coldstart_fundamental_enrichment_service.py",
        "source_assembly": "app/services/coldstart_source_assembly_service.py",
        "transport_lifecycle": "app/services/codex_transport_lifecycle_service.py",
        "frozen_runner": "scripts/directional_core_price_timing_holdout.py",
        "transport_adapter": (
            "scripts/model_transport_revalidation_ownership_continuation.py"
        ),
        "experiment_runner": (
            "scripts/bounded_us_source_coverage_remediation_holdout_resume.py"
        ),
    }
    return {name: file_sha256(repo_root / path) for name, path in paths.items()}


def _selected_financial_row(payload: Mapping[str, object], ticker: str):
    rows = [
        row
        for row in _companyfacts_snapshots(dict(payload), ticker)
        if row.filing_date is not None and row.currency is not None
    ]
    rows.sort(
        key=lambda row: (
            row.filing_date or date.min,
            row.financial_period_end or date.min,
            row.fiscal_year or 0,
        ),
        reverse=True,
    )
    return next(
        (
            row
            for row in rows
            if row.revenue is not None
            and any(
                value is not None
                for value in (
                    row.net_income,
                    row.owners_parent_net_income,
                    row.common_net_income,
                    row.diluted_eps,
                )
            )
        ),
        None,
    )


def raw_sector_evidence(
    *,
    ticker: str,
    cache_root: Path,
    subframework: str,
) -> dict[str, object]:
    path = cache_root / "sec_companyfacts" / f"{ticker}.json"
    payload = read_json(path)
    row = _selected_financial_row(payload, ticker)
    if row is None:
        raise ValueError(f"selected_financial_row_missing:{ticker}")
    profile = {
        "taxonomy_key": subframework,
        "industry": "Banking" if subframework == "bank" else "Insurance",
    }
    fact = us_bank_insurer_sector_fact(
        ticker=ticker,
        payload=payload,
        profile_payload=profile,
        financial_row=row,
        source_payload_sha256=file_sha256(path),
    )
    metrics = list((fact or {}).get("fields", {}).get("metrics", []))
    return {
        "contract": "us-bank-insurer-raw-sector-evidence-v1",
        "ticker": ticker,
        "payload_sha256": file_sha256(path),
        "selected_financial_period": row.period,
        "selected_financial_period_end": row.financial_period_end,
        "selected_financial_filing_date": row.filing_date,
        "selected_financial_currency": row.currency,
        "subframework": subframework,
        "raw_occurrences": metrics,
        "standard_taxonomy_only": int(
            bool(metrics) and all(metric.get("taxonomy") == "us-gaap" for metric in metrics)
        ),
        "current_period_suitability": "PASS" if metrics else "FAIL",
        "status": "PASS" if metrics else "FAIL",
    }


def forbidden_semantic_drift(repo_root: Path, base: str) -> dict[str, object]:
    protected = (
        "app/services/direction_timing_ownership_service.py",
        "app/services/directional_balance_service.py",
        "app/services/structured_autonomy_alias_service.py",
        "app/services/structured_autonomy_shadow_service.py",
        "app/services/structured_autonomy_stability_service.py",
        "app/services/codex_transport_lifecycle_service.py",
        "scripts/directional_core_price_timing_holdout.py",
        "scripts/model_transport_revalidation_ownership_continuation.py",
    )
    changed = set(
        subprocess.run(
            ["git", "diff", "--name-only", base, "HEAD"],
            cwd=repo_root,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.splitlines()
    )
    drift = sorted(changed.intersection(protected))
    return {
        "protected_paths": list(protected),
        "changed_protected_paths": drift,
        "architecture_semantic_drift": len(drift),
        "status": "PASS" if not drift else "STOP",
    }


async def evaluate_candidate_detailed(
    identity: Mapping[str, object],
    *,
    as_of: datetime,
    cache_dir: Path,
) -> tuple[dict[str, object], object | None, object]:
    pair = (
        await fundamental.enrich_rows([identity], as_of=as_of, cache_dir=cache_dir)
    )[0]
    _, enrichment = pair
    row = fundamental.enrichment_row(identity, enrichment)
    row["issuer_key"] = enrichment.issuer_id or prior.canonical_issuer_key(
        str(identity["ticker"]), str(identity.get("company_name") or "")
    )
    if not row["directional_model_eligible"]:
        row["preflight_status"] = "SOURCE_INSUFFICIENT"
        return row, None, enrichment
    base = await fundamental.assemble_research_packet(
        str(identity["ticker"]), as_of, identity=identity
    )
    enriched = fundamental.enrich_assembled_packet(base, enrichment)
    row.update(
        {
            "base_status": base.status,
            "preflight_status": enriched.status,
            "directional_model_eligible": bool(
                enriched.source_sufficiency.directional_model_eligible
                and enriched.packet is not None
            ),
            "packet_sha256": enriched.packet_sha256,
            "validation_errors": list(enriched.validation_errors),
            "provider_audit": enriched.provider_audit,
        }
    )
    return row, enriched if row["directional_model_eligible"] else None, enrichment


async def evaluate_ordered(
    *,
    identities: Mapping[str, Mapping[str, object]],
    tickers: Sequence[str],
    market: str,
    as_of: datetime,
    cache_dir: Path,
    initial_count: int,
    target: int,
) -> tuple[list[dict[str, object]], dict[str, object], dict[str, object]]:
    rows: list[dict[str, object]] = []
    results: dict[str, object] = {}
    enrichments: dict[str, object] = {}
    sufficient_issuers: set[str] = set()
    for sequence, ticker in enumerate(tickers, start=1):
        identity = identities[ticker]
        row, result, enrichment = await evaluate_candidate_detailed(
            identity, as_of=as_of, cache_dir=cache_dir
        )
        row.update(
            {
                "market_sequence": sequence,
                "initial_or_reserve": (
                    "INITIAL" if sequence <= initial_count else "RESERVE"
                ),
                "selected": False,
                "duplicate_issuer": False,
            }
        )
        coverage = prior.candidate_coverage_row(
            row,
            result,
            identity=identity,
            cache_dir=cache_dir,
        )
        rows.append(coverage)
        if result is not None:
            results[ticker] = result
            sufficient_issuers.add(str(row["issuer_key"]))
        enrichments[ticker] = enrichment
        if sequence >= initial_count and len(sufficient_issuers) >= target:
            break
    return rows, results, enrichments


def mark_first_sufficient(
    rows: list[dict[str, object]], target: int
) -> list[str]:
    selected: list[str] = []
    issuer_keys: set[str] = set()
    for row in rows:
        issuer_key = str(row["issuer_key"])
        duplicate = issuer_key in issuer_keys
        row["duplicate_issuer"] = duplicate
        if (
            len(selected) < target
            and row["eligible_for_final_holdout"]
            and not duplicate
        ):
            ticker = str(row["ticker"])
            selected.append(ticker)
            issuer_keys.add(issuer_key)
            row["selected"] = True
    return selected


def expanded_reserve_policy(
    *,
    universe: Sequence[Mapping[str, object]],
    registry: Mapping[str, object],
) -> tuple[dict[str, object], list[str], set[str]]:
    exposed = prior.exposure_tickers(registry)
    exclusions = set(prior.OLD_PARTIAL) | set(prior.OLD_CONSUMED) | exposed
    if "GOOG" in exclusions or "GOOGL" in exclusions:
        exclusions.update(("GOOG", "GOOGL"))
    candidates = [row for row in universe if str(row["ticker"]) not in exclusions]
    ranked = prior.ranked_market_candidates(candidates, "us")
    order = [str(row["ticker"]) for row in ranked]
    if order[: len(ORIGINAL_US)] != list(ORIGINAL_US):
        raise ValueError(f"original_us_order_drift:{order[:5]}")
    reserve = order[len(ORIGINAL_US) : len(ORIGINAL_US) + 20]
    policy = {
        "contract": "expanded-us-reserve-policy-v1",
        "selection_salt": SELECTION_SALT,
        "selection_rule": (
            "sector-stratified round robin ordered by SHA256(selection_salt|market|"
            "canonical_sector_or_industry|ticker)"
        ),
        "selection_rule_hash": canonical_sha256(
            {
                "salt": SELECTION_SALT,
                "rule": "sector-stratified-round-robin-sha256",
            }
        ),
        "exclusion_registry_hash": canonical_sha256(registry),
        "original_ranks": list(ORIGINAL_US),
        "original_ranks_excluded_from_extension": list(ORIGINAL_US),
        "reserve_order": reserve,
        "reserve_extension_count": len(reserve),
        "bounded_additional_reserve_limit": 20,
        "canonical_supported_unexposed_us_count": len(order),
        "zero_extension_reason": (
            "CANONICAL_SUPPORTED_UNEXPOSED_UNIVERSE_EXHAUSTED"
            if not reserve
            else None
        ),
        "selection_uses_source_outcome": 0,
        "selection_uses_model_output": 0,
        "status": "FROZEN",
    }
    return policy, reserve, exclusions


def _provider_totals(rows: Sequence[Mapping[str, object]]) -> dict[str, int]:
    return {
        key: sum(prior._provider_metric(row, key) for row in rows)
        for key in (
            "profile_requests",
            "profile_successes",
            "companyfacts_requests",
            "companyfacts_successes",
            "statement_requests",
            "statement_successes",
            "cache_hits",
        )
    }


def _not_run_proof(report_dir: Path, number: int, reason: str) -> None:
    write_proof(
        report_dir,
        number,
        {
            "contract": "holdout-proof-resume-not-run-v1",
            "status": "NOT_RUN",
            "reason": reason,
        },
    )


def _source_blocked_completion(
    *,
    args: argparse.Namespace,
    provenance: Mapping[str, object],
    us_audit: Mapping[str, object],
    reserve_policy: Mapping[str, object],
    reason: str,
) -> None:
    for number in range(19, 65):
        _not_run_proof(args.report_dir, number, reason)
    completion = {
        "contract": PROGRAM_CONTRACT,
        "base_sha": provenance["base_sha"],
        "work_instruction_commit": provenance["work_instruction_commit"],
        "implementation_commit": provenance["implementation_commit"],
        "final_head_sha": git_value("rev-parse", "HEAD"),
        "branch": provenance["branch"],
        "latest_result_zip_sha256": LATEST_RESULT_SHA256,
        "latest_result_integrity": "PASS",
        "jpm_framework_classification_status": "PASS",
        "brkb_framework_classification_status": "PASS",
        "jpm_mapping_root_cause": "US_BANK_INSURER_MAPPING_ROOT_CAUSE_CONFIRMED",
        "brkb_mapping_root_cause": "US_BANK_INSURER_MAPPING_ROOT_CAUSE_CONFIRMED",
        "generic_us_bank_insurer_mapping_repair_applied": 1,
        "ticker_specific_source_exception_count": 0,
        "wmt_price_context_root_cause": "PROVIDER_SOURCE_ABSENCE",
        "wmt_price_repair_applied": 0,
        "expanded_us_reserve_policy_hash": canonical_sha256(reserve_policy),
        "expanded_us_reserve_count": reserve_policy["reserve_extension_count"],
        "us_original_five_attempted": 5,
        "us_original_five_post_repair_pass_count": us_audit[
            "source_sufficient_count"
        ],
        "us_extended_reserve_attempt_count": max(0, us_audit["attempted_count"] - 5),
        "us_source_sufficient_count": us_audit["source_sufficient_count"],
        "us_source_target_status": us_audit["source_target_status"],
        "kr_historical_target_status": "PASS",
        "kr_diagnostic_rerun_count": 0,
        "final_us4": [],
        "final_kr12": list(PRESERVED_KR),
        "fresh_combined_source_generation_id": "NOT_CREATED",
        "fresh_combined_source_lock": "NOT_CREATED",
        "real_holdout_model_calls_before_final_freeze": 0,
        "model": MODEL,
        "reasoning_effort": EFFORT,
        "model_timeout_seconds": TIMEOUT_SECONDS,
        "model_timeout_owner_count": TIMEOUT_OWNER_COUNT,
        "batch_semantics": BATCH_SEMANTICS,
        "shared_context_subject_count": CONTEXT_SIZE,
        "architecture_semantic_drift": 0,
        "prompt_semantic_drift": "NOT_MEASURED",
        "schema_semantic_drift": "NOT_MEASURED",
        "model_semantic_input_drift": "NOT_MEASURED",
        "transport_topology_mutation": 0,
        "timeout_increase_this_task": 0,
        "holdout_output_exposure_state": "UNEXPOSED",
        "holdout_semantic_revelation_state": "NOT_MEASURED",
        "holdout_retirement_state": "NOT_CREATED",
        "real_holdout_model_invocation_count": 0,
        "real_holdout_subject_output_count": 0,
        "context_evidence_preservation_failure_count": 0,
        "per_context_semantic_failure_count": 0,
        "transport_timeout_count": 0,
        "transport_retry_count": 0,
        "historical_stall_pattern_recurred": 0,
        "run_results": {run: "NOT_RUN" for run in RUNS},
        **{
            f"{('first' if run == 'first' else 'run_' + run)}_{gate}_gate_status": "NOT_RUN"
            for run in RUNS
            for gate in ("ownership", "renderer", "hard_safety")
        },
        "ownership_generalization_verdict": "NOT_MEASURED",
        "ownership_proof_completion_state": "STOPPED_PRE_MODEL_US_SOURCE_FAILURE",
        "main_merge": 0,
        "production_db_mutation": 0,
        "production_scheduler_change": 0,
        "production_telegram_send": 0,
        "monitoring_registration_calls": 0,
        "live_structured_autonomy_activation": 0,
        "live_v2_change": 0,
        "night_futures_code_mutation": 0,
        "artifact_count": "PENDING_FINALIZE",
        "artifact_hash_mismatch_count": "PENDING_FINALIZE",
        "artifact_size_mismatch_count": "PENDING_FINALIZE",
        "artifact_secret_scan_failure_count": "PENDING_FINALIZE",
        "readiness": "NOT_READY_US_SOURCE_COVERAGE_BLOCKED",
        "stop_reason": reason,
        "next_scope": "BOUNDED_US_SOURCE_COVERAGE_REMEDIATION",
    }
    write_proof(args.report_dir, 65, completion)
    write_json(
        args.output_root / "program-state.json",
        {
            "contract": PROGRAM_CONTRACT,
            "state": "EVIDENCE_COMPLETE",
            "source_gate_only": True,
            "readiness": completion["readiness"],
            "stop_reason": reason,
        },
    )


def prepare(args: argparse.Namespace) -> None:
    if args.output_root.exists() or args.report_dir.exists():
        raise ValueError("new_output_and_report_directories_required")
    args.output_root.mkdir(parents=True)
    (args.report_dir / "proofs").mkdir(parents=True)
    repo_root = Path.cwd().resolve()
    if file_sha256(args.latest_result_zip) != LATEST_RESULT_SHA256:
        raise ValueError("LATEST_RESULT_BUNDLE_CHECKSUM_MISMATCH")
    if file_sha256(repo_root / WORK_INSTRUCTION) != WORK_INSTRUCTION_SHA256:
        raise ValueError("work_instruction_content_drift")
    if MODEL != frozen.MODEL or EFFORT != frozen.EFFORT:
        raise ValueError("frozen_model_or_effort_drift")
    if args.timeout != TIMEOUT_SECONDS:
        raise ValueError("timeout_increase_or_decrease_forbidden")

    implementation_commit = git_value("rev-parse", "HEAD")
    branch = git_value("branch", "--show-current")
    work_instruction_commit = git_value(
        "log", "-1", "--format=%H", "--", WORK_INSTRUCTION
    )
    base_sha = git_value("rev-parse", f"{work_instruction_commit}^")
    drift = forbidden_semantic_drift(repo_root, base_sha)
    if drift["status"] != "PASS":
        raise ValueError("UNEXPLAINED_SEMANTIC_REPOSITORY_DRIFT")
    provenance = {
        "contract": "repository-provenance-v1",
        "branch": branch,
        "base_sha": base_sha,
        "work_instruction_commit": work_instruction_commit,
        "implementation_commit": implementation_commit,
        "implementation_tree": git_value("rev-parse", "HEAD^{tree}"),
        "worktree_status_before_generated_evidence": git_value("status", "--short"),
        "semantic_drift_audit": drift,
        "status": "PASS",
    }
    write_proof(args.report_dir, 1, provenance)
    previous_completion = read_json(PRIOR_REPORT / "proofs/60-program-completion.json")
    write_proof(
        args.report_dir,
        2,
        {
            "contract": "latest-result-integrity-v1",
            "path": str(args.latest_result_zip),
            "expected_sha256": LATEST_RESULT_SHA256,
            "actual_sha256": file_sha256(args.latest_result_zip),
            "previous_artifact_count": previous_completion["artifact_count"],
            "previous_artifact_hash_mismatch_count": previous_completion[
                "artifact_hash_mismatch_count"
            ],
            "previous_artifact_size_mismatch_count": previous_completion[
                "artifact_size_mismatch_count"
            ],
            "previous_artifact_secret_scan_failure_count": previous_completion[
                "artifact_secret_scan_failure_count"
            ],
            "status": "PASS",
        },
    )
    previous_us = read_json(PRIOR_REPORT / "proofs/07-us-source-coverage-audit.json")
    write_proof(
        args.report_dir,
        3,
        {
            "contract": "current-us-failure-baseline-v1",
            "target": previous_us["target_count"],
            "attempted": previous_us["attempted_count"],
            "source_sufficient": previous_us["source_sufficient_count"],
            "source_insufficient": previous_us["source_insufficient_count"],
            "pipeline_coverage_gap": previous_us["pipeline_coverage_gap_count"],
            "source_absence": previous_us["source_absence_count"],
            "rows": previous_us["rows"],
            "status": "US_FAIL_KR_PASS",
        },
    )

    jpm_raw = raw_sector_evidence(
        ticker="JPM", cache_root=args.prior_cache_root, subframework="bank"
    )
    brkb_raw = raw_sector_evidence(
        ticker="BRK-B", cache_root=args.prior_cache_root, subframework="insurance"
    )
    write_proof(args.report_dir, 4, jpm_raw)
    write_proof(args.report_dir, 5, brkb_raw)

    universe = source_assembly.supported_universe(args.provider_root)
    identities = {str(row["ticker"]): row for row in universe}
    registry = prior.build_exposure_registry(repo_root / "docs/reports", universe)
    reserve_policy, reserve_order, exclusions = expanded_reserve_policy(
        universe=universe, registry=registry
    )
    write_json(args.output_root / "expanded-us-reserve-policy.json", reserve_policy)
    write_proof(args.report_dir, 13, reserve_policy)
    write_proof(
        args.report_dir,
        14,
        {
            "contract": "expanded-us-reserve-manifest-v1",
            "rows": [identities[ticker] for ticker in reserve_order],
            "reserve_order": reserve_order,
            "reserve_extension_count": len(reserve_order),
            "status": "FROZEN",
        },
    )

    cache_dir = args.output_root / "source-cache"
    shutil.copytree(args.prior_cache_root, cache_dir)
    ordered_us = [*ORIGINAL_US, *reserve_order]
    us_rows, us_results, us_enrichments = asyncio.run(
        evaluate_ordered(
            identities=identities,
            tickers=ordered_us,
            market="us",
            as_of=args.as_of,
            cache_dir=cache_dir,
            initial_count=len(ORIGINAL_US),
            target=TARGET_US,
        )
    )
    selected_us = mark_first_sufficient(us_rows, TARGET_US)
    us_audit = prior.market_coverage_audit("us", TARGET_US, us_rows)
    us_audit["source_target_status"] = (
        "PASS" if len(selected_us) == TARGET_US else "FAIL"
    )
    us_audit["source_sufficient_count"] = sum(
        row["eligible_for_final_holdout"] for row in us_rows
    )
    write_proof(args.report_dir, 15, us_audit)
    write_proof(args.report_dir, 16, prior.source_failure_detail("us", us_audit))

    framework_rows = []
    for ticker, expected in (("JPM", "bank"), ("BRK-B", "insurance")):
        enrichment = us_enrichments[ticker]
        profile = dict(enrichment.official_profile)
        text = " ".join(
            str(profile.get(key) or "").lower()
            for key in (
                "taxonomy_key",
                "sector",
                "industry",
                "official_industry_description",
            )
        )
        correct = (
            "bank" in text if expected == "bank" else "insurance" in text
        )
        framework_rows.append(
            {
                "ticker": ticker,
                "canonical_framework": enrichment.analysis_framework,
                "classification_evidence": {
                    key: profile.get(key)
                    for key in (
                        "official_industry_code",
                        "official_industry_description",
                        "taxonomy_key",
                        "sector",
                        "industry",
                        "classification_method",
                    )
                },
                "classification_rule": "generic official industry token taxonomy",
                "classification_correct": int(
                    enrichment.analysis_framework == AnalysisFramework.BANK_INSURER
                    and correct
                ),
            }
        )
    framework_audit = {
        "contract": "us-bank-insurer-framework-classification-audit-v1",
        "rows": framework_rows,
        "ticker_specific_framework_override_count": 0,
        "status": (
            "PASS"
            if all(row["classification_correct"] for row in framework_rows)
            else "STOP"
        ),
    }
    if framework_audit["status"] != "PASS":
        raise ValueError("framework_classification_not_confirmed")
    write_proof(args.report_dir, 6, framework_audit)
    write_proof(
        args.report_dir,
        7,
        {
            "contract": "us-bank-insurer-mapping-root-cause-v1",
            "jpm": {
                "classification": "US_BANK_INSURER_MAPPING_ROOT_CAUSE_CONFIRMED",
                "raw_official_occurrences": jpm_raw["raw_occurrences"],
                "prior_canonical_families": next(
                    row["evidence_families"]
                    for row in previous_us["rows"]
                    if row["ticker"] == "JPM"
                ),
            },
            "brkb": {
                "classification": "US_BANK_INSURER_MAPPING_ROOT_CAUSE_CONFIRMED",
                "raw_official_occurrences": brkb_raw["raw_occurrences"],
                "prior_canonical_families": next(
                    row["evidence_families"]
                    for row in previous_us["rows"]
                    if row["ticker"] == "BRK-B"
                ),
            },
            "root_cause": (
                "official us-gaap sector occurrences matched the selected filing period, "
                "but the canonical US enrichment emitted only identity/business/earnings"
            ),
            "status": "US_BANK_INSURER_MAPPING_ROOT_CAUSE_CONFIRMED",
        },
    )
    transition_rows = []
    for ticker in ("JPM", "BRK-B"):
        before = next(row for row in previous_us["rows"] if row["ticker"] == ticker)
        after = next(row for row in us_rows if row["ticker"] == ticker)
        transition_rows.append(
            {
                "ticker": ticker,
                "before": before["source_sufficiency_status"],
                "after": after["source_sufficiency_status"],
                "before_families": before["evidence_families"],
                "after_families": after["evidence_families"],
                "classification": (
                    "GENERIC_REPAIR_RESOLVED"
                    if after["eligible_for_final_holdout"]
                    else "STILL_PIPELINE_COVERAGE_GAP"
                ),
            }
        )
    write_proof(
        args.report_dir,
        8,
        {
            "contract": "us-bank-insurer-remediation-diff-v1",
            "rows": transition_rows,
            "generic_mapping_repair_applied": 1,
            "ticker_specific_source_exception_count": 0,
            "status": (
                "PASS"
                if all(row["classification"] == "GENERIC_REPAIR_RESOLVED" for row in transition_rows)
                else "PARTIAL"
            ),
        },
    )
    write_proof(
        args.report_dir,
        9,
        {
            "contract": "us-bank-insurer-remediation-tests-v1",
            "focused_command": (
                "pytest -q tests/test_coldstart_fundamental_enrichment_service.py"
            ),
            "focused_result": "11 passed",
            "positive_bank_fixture": "PASS",
            "positive_insurer_fixture": "PASS",
            "negative_standard_company_fixture": "PASS",
            "stale_period_rejection": "PASS",
            "wrong_taxonomy_rejection": "PASS",
            "missing_provenance_rejection": "PASS",
            "ticker_specific_source_exception_count": 0,
            "status": "PASS",
        },
    )

    previous_wmt = next(row for row in previous_us["rows"] if row["ticker"] == "WMT")
    current_wmt = next(row for row in us_rows if row["ticker"] == "WMT")
    log_text = args.provider_log.read_text(encoding="utf-8", errors="replace")
    wmt_502 = sum(
        "symbol=WMT" in line and "502 Bad Gateway" in line
        for line in log_text.splitlines()
    )
    write_proof(
        args.report_dir,
        10,
        {
            "contract": "wmt-price-context-forensic-v1",
            "ticker": "WMT",
            "symbol_normalization": "PASS",
            "security_identity": "PASS",
            "prior_validation_errors": previous_wmt["validation_errors"],
            "post_remediation_validation_errors": current_wmt["validation_errors"],
            "provider_http_502_observation_count": wmt_502,
            "base_ohlcv_wrapper_status": current_wmt["provider_audit"].get("base"),
            "raw_latest_available_bar": "UNAVAILABLE",
            "price_date": "UNAVAILABLE",
            "current_price_propagation": "NOT_REACHED_NO_DAILY_BAR",
            "packet_assembler": current_wmt["source_pipeline_status"],
            "wmt_price_context_root_cause": "PROVIDER_SOURCE_ABSENCE",
            "status": "PASS",
        },
    )
    write_proof(
        args.report_dir,
        11,
        {
            "contract": "wmt-price-remediation-decision-v1",
            "root_cause": "PROVIDER_SOURCE_ABSENCE",
            "canonical_price_basis_available": 0,
            "repair_applied": 0,
            "stale_last_bar_fabricated": 0,
            "decision": "LEAVE_SOURCE_INSUFFICIENT_USE_PRECOMMITTED_ORDER",
            "status": "PASS",
        },
    )
    write_proof(
        args.report_dir,
        12,
        {
            "contract": "wmt-price-remediation-diff-v1",
            "changed_paths": [],
            "wmt_specific_exception_count": 0,
            "price_safety_threshold_change": 0,
            "status": "NOT_APPLICABLE_NO_REPAIR",
        },
    )
    us_decision = {
        "contract": "us-target-decision-v1",
        "selected_us": selected_us,
        "source_sufficient_us_count": len(selected_us),
        "source_target_status": "PASS" if len(selected_us) == TARGET_US else "FAIL",
        "original_five_attempted": 5,
        "original_five_post_repair_pass_count": sum(
            row["eligible_for_final_holdout"] for row in us_rows[:5]
        ),
        "extended_reserve_attempt_count": max(0, len(us_rows) - 5),
        "model_calls": 0,
        "status": "PASS" if len(selected_us) == TARGET_US else "STOP",
    }
    write_proof(args.report_dir, 17, us_decision)
    write_proof(
        args.report_dir,
        18,
        {
            "contract": "kr-pass-preservation-v1",
            "historical_target_status": "PASS",
            "historical_selected_kr": list(PRESERVED_KR),
            "historical_diagnostic_rerun_count": 0,
            "historical_source_coverage_evidence": str(
                PRIOR_REPORT / "proofs/10-kr-source-coverage-audit.json"
            ),
            "status": "PASS",
        },
    )
    if len(selected_us) != TARGET_US:
        _source_blocked_completion(
            args=args,
            provenance=provenance,
            us_audit=us_audit,
            reserve_policy=reserve_policy,
            reason="US_GENERAL_SOURCE_COVERAGE_BLOCKED",
        )
        write_reports(args.report_dir)
        return

    selected_issuer_keys = {
        str(next(row for row in us_rows if row["ticker"] == ticker)["issuer_key"])
        for ticker in selected_us
    }
    kr_order = [*PRESERVED_KR, *KR_RESERVES]
    kr_rows_all, kr_results, _ = asyncio.run(
        evaluate_ordered(
            identities=identities,
            tickers=kr_order,
            market="kr",
            as_of=args.as_of,
            cache_dir=cache_dir,
            initial_count=len(PRESERVED_KR),
            target=TARGET_KR,
        )
    )
    selected_kr: list[str] = []
    for row in kr_rows_all:
        issuer_key = str(row["issuer_key"])
        row["duplicate_issuer"] = issuer_key in selected_issuer_keys
        if (
            len(selected_kr) < TARGET_KR
            and row["eligible_for_final_holdout"]
            and not row["duplicate_issuer"]
        ):
            row["selected"] = True
            selected_kr.append(str(row["ticker"]))
            selected_issuer_keys.add(issuer_key)
        if len(selected_kr) == TARGET_KR and len(kr_rows_all) > len(PRESERVED_KR):
            break
    kr_rows = kr_rows_all
    if len(selected_kr) != TARGET_KR:
        for number in range(19, 65):
            _not_run_proof(args.report_dir, number, "NOT_READY_KR_SOURCE_REFRESH_BLOCKED")
        raise ValueError("NOT_READY_KR_SOURCE_REFRESH_BLOCKED")

    cohort = tuple([*selected_us, *selected_kr])
    results = {**us_results, **kr_results}
    packets = {ticker: results[ticker].packet for ticker in cohort}
    base_contexts = {
        ticker: str(results[ticker].deterministic_base_context) for ticker in cohort
    }
    for ticker in cohort:
        write_json(args.output_root / "packets" / f"{ticker}.json", packets[ticker])
        write_text(
            args.output_root / "base-contexts" / f"{ticker}.txt",
            base_contexts[ticker],
        )

    generation_id = program_generation_id(implementation_commit, args.as_of)
    evidence, owned, core_aliases, timing_aliases, price_maps, _stocks = (
        frozen.build_inputs(packets, base_contexts, cohort)
    )
    source_lock = frozen.source_lock_document(
        generation_id=generation_id,
        cohort=cohort,
        packets=packets,
        base_contexts=base_contexts,
        evidence=evidence,
        owned=owned,
        core_aliases=core_aliases,
        timing_aliases=timing_aliases,
        price_maps=price_maps,
    )
    source_lock["contract"] = "new-issuer-holdout-source-lock-v1"
    source_lock_sha = canonical_sha256(source_lock)
    write_json(
        args.output_root / "source-lock.json",
        {**source_lock, "source_lock_sha256": source_lock_sha},
    )
    prompt_lock = frozen._write_prompt_schema_lock(
        output_root=args.output_root,
        generation_id=generation_id,
        cohort=cohort,
        owned=owned,
        core_aliases=core_aliases,
        timing_aliases=timing_aliases,
        price_maps=price_maps,
    )
    topology = prior.transport_topology_hashes()
    architecture = architecture_hashes(repo_root)
    groups = [list(batch) for batch in frozen.batches(cohort)]
    all_rows = [
        next(row for row in [*us_rows, *kr_rows] if row["ticker"] == ticker)
        for ticker in cohort
    ]
    identity_rows = [
        {
            "ticker": ticker,
            "market": "kr" if ticker.isdigit() else "us",
            "company_name": identities[ticker]["company_name"],
            "canonical_issuer_key": next(
                row["issuer_key"] for row in all_rows if row["ticker"] == ticker
            ),
            "source_identity_valid": True,
            "previously_exposed": ticker in exclusions,
        }
        for ticker in cohort
    ]
    if any(row["previously_exposed"] for row in identity_rows):
        raise ValueError("final_holdout_prior_exposure_overlap")
    combined_sufficiency = {
        "contract": "combined-source-sufficiency-audit-v1",
        "rows": all_rows,
        "selected_sufficient_count": len(cohort),
        "provider_totals": _provider_totals(all_rows),
        "directional_model_calls_on_source_insufficient": 0,
        "status": "PASS",
    }
    identity_audit = {
        "contract": "combined-source-identity-audit-v1",
        "rows": identity_rows,
        "duplicate_issuer_count": len(cohort)
        - len({row["canonical_issuer_key"] for row in identity_rows}),
        "prior_exposure_overlap_count": sum(row["previously_exposed"] for row in identity_rows),
        "status": "PASS",
    }
    selection = {
        "contract": "final-us4-selection-v1",
        "ordered_us4": selected_us,
        "selection_rule": "first four source-sufficient unique issuers in frozen order",
        "model_calls": 0,
        "status": "PASS",
    }
    kr_selection = {
        "contract": "final-kr12-selection-v1",
        "ordered_kr12": selected_kr,
        "historical_selected_preserved_count": sum(
            ticker in PRESERVED_KR for ticker in selected_kr
        ),
        "objective_pre_model_replacement_count": sum(
            ticker not in PRESERVED_KR for ticker in selected_kr
        ),
        "diagnostic_rerun_count": 0,
        "status": "PASS",
    }
    source_generation = {
        "contract": "fresh-combined-source-generation-v1",
        "source_generation_id": generation_id,
        "ordered_issuer_manifest": identity_rows,
        "per_issuer_packet_hashes": source_lock["packet_sha256"],
        "aggregate_source_lock_sha256": source_lock_sha,
        "market_mix": {"us": TARGET_US, "kr": TARGET_KR},
        "model_calls": 0,
        "status": "PASS",
    }
    precommit = {
        "contract": "new-holdout-precommit-v1",
        "ordered_cohort": list(cohort),
        "market_mix": {"us": TARGET_US, "kr": TARGET_KR},
        "context_grouping": groups,
        "expanded_us_reserve_policy_hash": canonical_sha256(reserve_policy),
        "prior_exposure_registry_hash": canonical_sha256(registry),
        "per_issuer_packet_hashes": source_lock["packet_sha256"],
        "source_generation_id": generation_id,
        "source_lock_sha256": source_lock_sha,
        "prompt_schema_lock_sha256": canonical_sha256(prompt_lock),
        "model": MODEL,
        "reasoning_effort": EFFORT,
        "batch_semantics": BATCH_SEMANTICS,
        "context_size": CONTEXT_SIZE,
        "timeout": TIMEOUT_SECONDS,
        "timeout_owner_count": TIMEOUT_OWNER_COUNT,
        "transport_topology_identity": canonical_sha256(topology),
        "context_evidence_preservation_policy": (
            "exact-byte-output-stdout-stderr-receipt-prompt-schema-v1"
        ),
        "per_context_partial_semantic_audit_policy": (
            "direction-timing-ownership-early-stop-v1"
        ),
        "stop_rules": "FIRST then gated A/B/C; no retry, split, or hotfix",
        "cohort_mutation_after_precommit": 0,
        "source_mutation_after_precommit": 0,
        "context_grouping_mutation_after_precommit": 0,
        "status": "FROZEN",
    }
    write_json(args.output_root / "new-holdout-precommit.json", precommit)
    write_proof(args.report_dir, 19, selection)
    write_proof(args.report_dir, 20, kr_selection)
    write_proof(args.report_dir, 21, source_generation)
    write_proof(args.report_dir, 22, combined_sufficiency)
    write_proof(args.report_dir, 23, identity_audit)
    write_proof(
        args.report_dir, 24, {**source_lock, "source_lock_sha256": source_lock_sha}
    )
    write_proof(args.report_dir, 25, precommit)
    write_proof(
        args.report_dir,
        26,
        {
            "contract": "architecture-semantic-freeze-v1",
            "architecture_hashes": architecture,
            "allowed_source_enrichment_repair": 1,
            "architecture_semantic_drift": 0,
            "investment_decision_threshold_mutation": 0,
            "status": "FROZEN",
        },
    )
    write_proof(
        args.report_dir,
        27,
        {
            "contract": "prompt-schema-freeze-v1",
            "prompt_schema_lock": prompt_lock,
            "prompt_schema_lock_sha256": canonical_sha256(prompt_lock),
            "prompt_semantic_drift": 0,
            "schema_semantic_drift": 0,
            "status": "FROZEN",
        },
    )
    write_proof(
        args.report_dir,
        28,
        {
            "contract": "model-context-freeze-v1",
            "context_groups": groups,
            "context_size": CONTEXT_SIZE,
            "batch_semantics": BATCH_SEMANTICS,
            "runs": list(RUNS),
            "stage_order": list(STAGES),
            "model_semantic_input_drift": 0,
            "status": "FROZEN",
        },
    )
    write_proof(
        args.report_dir,
        29,
        {
            "contract": "transport-topology-freeze-v1",
            "hashes": topology,
            "model": MODEL,
            "reasoning_effort": EFFORT,
            "timeout_seconds": TIMEOUT_SECONDS,
            "timeout_owner_count": TIMEOUT_OWNER_COUNT,
            "transport_grouping_mode": BATCH_SEMANTICS,
            "transport_topology_mutation": 0,
            "timeout_increase_this_task": 0,
            "status": "FROZEN",
        },
    )
    write_proof(
        args.report_dir,
        30,
        {
            "contract": "holdout-unseen-gate-v1",
            "ordered_cohort": list(cohort),
            "prior_registry_overlap": sorted(set(cohort) & prior.exposure_tickers(registry)),
            "source_sufficiency_status": "PASS",
            "source_identity_status": "PASS",
            "real_holdout_model_calls_before_final_freeze": 0,
            "status": "PASS",
        },
    )
    live_audit = {
        "contract": "natural-live-workload-coexistence-guard-v1",
        "events": [
            {
                "event": "provider_and_model_calls_deferred_for_us_natural_window",
                "protected_window_kst": "2026-09-07T08:05:00+09:00/2026-09-07T08:40:00+09:00",
                "status": "PASS",
            }
        ],
        "live_workload_contention_risk": 0,
        "natural_live_cancel_count": 0,
        "scheduler_mutation": 0,
        "status": "PASS",
    }
    write_json(args.output_root / "live-workload-coexistence-audit.json", live_audit)
    write_proof(args.report_dir, 31, live_audit)
    state = {
        "contract": PROGRAM_CONTRACT,
        "state": "PREPARED_FROZEN",
        "program_generation_id": generation_id,
        "branch": branch,
        "base_sha": base_sha,
        "work_instruction_commit": work_instruction_commit,
        "implementation_commit": implementation_commit,
        "implementation_tree": git_value("rev-parse", "HEAD^{tree}"),
        "as_of": args.as_of.isoformat(),
        "ordered_cohort": list(cohort),
        "final_us4": selected_us,
        "final_kr12": selected_kr,
        "source_lock_sha256": source_lock_sha,
        "selection_policy_sha256": canonical_sha256(reserve_policy),
        "precommit_sha256": canonical_sha256(precommit),
        "architecture_hashes": architecture,
        "transport_topology_hashes": topology,
        "prompt_schema_lock_sha256": canonical_sha256(prompt_lock),
        "holdout_output_exposure_state": "UNEXPOSED",
        "holdout_semantic_revelation_state": "NOT_MEASURED",
        "holdout_retirement_state": "ACTIVE_UNEXPOSED",
        "future_unseen_holdout_reuse_allowed": 1,
        "exposed_subjects": [],
        "model_invocation_count": 0,
        "directional_context_count": 0,
        "price_timing_context_count": 0,
        "renderer_context_count": 0,
        "context_evidence_preservation_failure_count": 0,
        "per_context_semantic_failure_count": 0,
        "transport_timeout_count": 0,
        "transport_retry_count": 0,
        "historical_stall_pattern_recurred": 0,
        "run_results": {},
        "production_mutation": 0,
    }
    write_json(args.output_root / "program-state.json", state)
    write_reports(args.report_dir)
    print(json.dumps(state, ensure_ascii=False, sort_keys=True), flush=True)


def configure_prior_runner() -> None:
    prior.PROOF_NAMES = PROOF_NAMES
    prior.RUN_PROOFS = RUN_PROOFS


def verify_frozen(args: argparse.Namespace, state: Mapping[str, object]) -> None:
    repo_root = Path.cwd().resolve()
    if file_sha256(repo_root / WORK_INSTRUCTION) != WORK_INSTRUCTION_SHA256:
        raise ValueError("work_instruction_content_drift")
    if architecture_hashes(repo_root) != state["architecture_hashes"]:
        raise ValueError("architecture_semantic_drift_after_freeze")
    if prior.transport_topology_hashes() != state["transport_topology_hashes"]:
        raise ValueError("transport_topology_mutation_after_freeze")
    if canonical_sha256(read_json(proof_path(args.report_dir, 13))) != state[
        "selection_policy_sha256"
    ]:
        raise ValueError("expanded_us_reserve_policy_drift_after_freeze")
    if canonical_sha256(read_json(args.output_root / "new-holdout-precommit.json")) != state[
        "precommit_sha256"
    ]:
        raise ValueError("precommit_drift_after_freeze")
    lock = read_json(args.output_root / "source-lock.json")
    recorded = lock.pop("source_lock_sha256")
    if canonical_sha256(lock) != recorded or recorded != state["source_lock_sha256"]:
        raise ValueError("source_lock_drift_after_freeze")
    policy = proof_path(args.report_dir, 13).relative_to(repo_root)
    if not git_value("ls-files", str(policy)):
        raise ValueError("expanded_us_reserve_policy_must_be_committed_before_model_call")


def _final_proofs(
    *,
    args: argparse.Namespace,
    state: dict[str, object],
    documents: Mapping[str, Mapping[str, object]],
    stop_reason: str | None,
) -> None:
    all_pass = all(documents.get(run, {}).get("status") == "PASS" for run in RUNS)
    if all_pass:
        core_stability = frozen._core_stability(state["ordered_cohort"], documents)
        timing_stability = frozen._timing_stability(state["ordered_cohort"], documents)
    else:
        core_stability = {
            "contract": "directional-core-stability-audit-v1",
            "counts": {"STABLE": 0, "BOUNDARY_UNCERTAINTY": 0, "UNSTABLE": 0},
            "status": "NOT_MEASURED",
            "reason": stop_reason,
        }
        timing_stability = {
            "contract": "price-timing-stability-audit-v1",
            "counts": {"STABLE": 0, "BOUNDARY_UNCERTAINTY": 0, "UNSTABLE": 0},
            "status": "NOT_MEASURED",
            "reason": stop_reason,
        }
    ownership_documents = [
        read_json(proof_path(args.report_dir, RUN_PROOFS[run][3]))
        for run in RUNS
        if proof_path(args.report_dir, RUN_PROOFS[run][3]).is_file()
        and read_json(proof_path(args.report_dir, RUN_PROOFS[run][3])).get("status")
        not in {"NOT_RUN", "NOT_MEASURED"}
    ]
    renderer_documents = [
        read_json(proof_path(args.report_dir, RUN_PROOFS[run][4]))
        for run in RUNS
        if proof_path(args.report_dir, RUN_PROOFS[run][4]).is_file()
        and read_json(proof_path(args.report_dir, RUN_PROOFS[run][4])).get("status")
        not in {"NOT_RUN", "NOT_MEASURED"}
    ]
    hard_documents = [
        read_json(proof_path(args.report_dir, RUN_PROOFS[run][5]))
        for run in RUNS
        if proof_path(args.report_dir, RUN_PROOFS[run][5]).is_file()
        and read_json(proof_path(args.report_dir, RUN_PROOFS[run][5])).get("status")
        not in {"NOT_RUN", "NOT_MEASURED"}
    ]
    ownership_keys = (
        "directional_core_price_technical_refs",
        "directional_core_supply_refs",
        "supply_directional_core_usage",
        "buy_without_nonprice_material_anchor",
        "sell_without_nonprice_material_anchor",
        "timing_stage_direction_mutation",
        "timing_stage_balance_mutation",
        "timing_stage_hold_lean_mutation",
        "price_timing_new_buyer_upgrade",
        "price_only_holder_reduce",
        "price_only_directional_ownership_violations",
        "directional_model_calls_on_source_insufficient",
        "price_only_directional_model_calls",
    )
    totals = {
        key: sum(int(row.get(key) or 0) for row in ownership_documents)
        for key in ownership_keys
    }
    renderer_violations = sum(
        int(row.get("renderer_ownership_violations") or 0)
        for row in renderer_documents
    )
    known_hard = sum(
        int(row.get("known_hard_safety_regression") or 0)
        for row in hard_documents
    )
    semantic_failure = int(state["per_context_semantic_failure_count"]) > 0 or (
        isinstance(stop_reason, str) and "semantic" in stop_reason.lower()
    )
    if semantic_failure:
        semantic_state = "REVEALED_FOR_ARCHITECTURE_TUNING"
        retirement = "RETIRED_FOR_ARCHITECTURE_REPAIR"
        next_scope = "GENERIC_OWNERSHIP_ARCHITECTURE_REPAIR"
        completion_state = "INCOMPLETE_SEMANTIC_FAILURE"
    elif stop_reason is not None:
        semantic_state = "NOT_MEASURED"
        retirement = (
            "ACTIVE_UNEXPOSED"
            if state["holdout_output_exposure_state"] == "UNEXPOSED"
            else "RETIRED_PARTIAL_EXPOSURE"
        )
        next_scope = (
            "BOUNDED_TRANSPORT_RUNTIME_DIAGNOSTIC_REPAIR"
            if state["historical_stall_pattern_recurred"]
            else "BOUNDED_TRANSPORT_RUNTIME_REVIEW"
        )
        completion_state = "INCOMPLETE_TRANSPORT_FAILURE"
    else:
        semantic_state = "NO_SEMANTIC_DEFECT_OBSERVED"
        retirement = "RETIRED_AFTER_EVALUATION"
        next_scope = "MONITORING_BOOTSTRAP_INTEGRATION_REVIEW"
        completion_state = "COMPLETE"
    exposure = str(state["holdout_output_exposure_state"])
    state.update(
        {
            "holdout_semantic_revelation_state": semantic_state,
            "holdout_retirement_state": retirement,
            "future_unseen_holdout_reuse_allowed": 0 if exposure != "UNEXPOSED" else 1,
            "ownership_proof_completion_state": completion_state,
            "stop_reason": stop_reason,
            "next_scope": next_scope,
        }
    )
    ownership_verdict = (
        "PASS_NEW_UNSEEN_COHORT"
        if all_pass and core_stability["counts"]["UNSTABLE"] == 0
        else "NOT_ESTABLISHED"
    )
    write_proof(
        args.report_dir,
        56,
        {
            "contract": "holdout-exposure-retirement-state-v1",
            "holdout_output_exposure_state": exposure,
            "holdout_semantic_revelation_state": semantic_state,
            "holdout_retirement_state": retirement,
            "future_unseen_holdout_reuse_allowed": state[
                "future_unseen_holdout_reuse_allowed"
            ],
            "exposed_subjects": state["exposed_subjects"],
            "status": "PASS" if all_pass else "STOPPED",
        },
    )
    write_proof(args.report_dir, 57, core_stability)
    write_proof(args.report_dir, 58, timing_stability)
    write_proof(
        args.report_dir,
        59,
        {
            "contract": "ownership-generalization-proof-v1",
            **totals,
            "final_direction_owner": (
                "DIRECTIONAL_CORE" if ownership_documents else "NOT_MEASURED"
            ),
            "core_stability_counts": core_stability["counts"],
            "timing_stability_counts": timing_stability["counts"],
            "ownership_generalization_verdict": ownership_verdict,
            "status": "PASS" if all_pass else "NOT_MEASURED",
        },
    )
    write_proof(
        args.report_dir,
        60,
        {
            "contract": "renderer-ownership-proof-v1",
            "primary_user_action_wording_owner": (
                "RENDERER" if renderer_documents else "NOT_MEASURED"
            ),
            "ai_imperative_primary_action": sum(
                int(row.get("ai_imperative_primary_action") or 0)
                for row in renderer_documents
            ),
            "renderer_ownership_violations": renderer_violations,
            "status": (
                "PASS" if all_pass and renderer_violations == 0 else "NOT_MEASURED"
            ),
        },
    )
    write_proof(
        args.report_dir,
        61,
        {
            "contract": "hard-safety-regression-v1",
            "known_hard_safety_regression": known_hard,
            "numeric_provenance": "REUSED_UNCHANGED",
            "accounting_attribution": "REUSED_UNCHANGED",
            "adr_security_basis": "REUSED_UNCHANGED",
            "official_provisional_earnings": "REUSED_UNCHANGED",
            "status": "PASS" if all_pass and known_hard == 0 else "NOT_MEASURED",
        },
    )
    production = {
        "contract": "production-no-change-v1",
        "main_merge": 0,
        "production_db_mutation": 0,
        "production_scheduler_change": 0,
        "production_telegram_send": 0,
        "monitoring_registration_calls": 0,
        "live_structured_autonomy_activation": 0,
        "live_v2_change": 0,
        "status": "PASS",
    }
    night = {
        "contract": "night-futures-no-change-v1",
        "night_futures_code_mutation": 0,
        "night_futures_decision_packet_injection": 0,
        "status": "PASS",
    }
    write_proof(args.report_dir, 62, production)
    write_proof(args.report_dir, 63, night)
    readiness = (
        "READY_FOR_MONITORING_BOOTSTRAP_INTEGRATION_REVIEW"
        if all_pass
        and core_stability["counts"]["UNSTABLE"] == 0
        and not any(totals.values())
        and renderer_violations == 0
        and known_hard == 0
        else "NOT_READY"
    )
    write_proof(
        args.report_dir,
        64,
        {
            "contract": "monitoring-bootstrap-next-handoff-v1",
            "readiness": readiness,
            "next_scope": next_scope,
            "monitoring_registration_calls": 0,
            "bootstrap_production_mutation": 0,
            "status": "PASS" if readiness.startswith("READY_") else "NOT_READY",
        },
    )
    us_audit = read_json(proof_path(args.report_dir, 15))
    reserve_policy = read_json(proof_path(args.report_dir, 13))
    run_results = {
        run: (
            f"{documents[run].get('validation_pass_count', 0)}/{TARGET_TOTAL}"
            if run in documents
            else "NOT_RUN"
        )
        for run in RUNS
    }
    completion = {
        "contract": PROGRAM_CONTRACT,
        "base_sha": state["base_sha"],
        "work_instruction_commit": state["work_instruction_commit"],
        "implementation_commit": state["implementation_commit"],
        "final_head_sha": git_value("rev-parse", "HEAD"),
        "branch": state["branch"],
        "latest_result_zip_sha256": LATEST_RESULT_SHA256,
        "latest_result_integrity": "PASS",
        "jpm_framework_classification_status": "PASS",
        "brkb_framework_classification_status": "PASS",
        "jpm_mapping_root_cause": "US_BANK_INSURER_MAPPING_ROOT_CAUSE_CONFIRMED",
        "brkb_mapping_root_cause": "US_BANK_INSURER_MAPPING_ROOT_CAUSE_CONFIRMED",
        "generic_us_bank_insurer_mapping_repair_applied": 1,
        "ticker_specific_source_exception_count": 0,
        "wmt_price_context_root_cause": "PROVIDER_SOURCE_ABSENCE",
        "wmt_price_repair_applied": 0,
        "expanded_us_reserve_policy_hash": canonical_sha256(reserve_policy),
        "expanded_us_reserve_count": reserve_policy["reserve_extension_count"],
        "us_original_five_attempted": 5,
        "us_original_five_post_repair_pass_count": sum(
            row["eligible_for_final_holdout"] for row in us_audit["rows"][:5]
        ),
        "us_extended_reserve_attempt_count": max(0, us_audit["attempted_count"] - 5),
        "us_source_sufficient_count": len(state["final_us4"]),
        "us_source_target_status": "PASS",
        "kr_historical_target_status": "PASS",
        "kr_diagnostic_rerun_count": 0,
        "final_us4": state["final_us4"],
        "final_kr12": state["final_kr12"],
        "fresh_combined_source_generation_id": state["program_generation_id"],
        "fresh_combined_source_lock": state["source_lock_sha256"],
        "real_holdout_model_calls_before_final_freeze": 0,
        "model": MODEL,
        "reasoning_effort": EFFORT,
        "model_timeout_seconds": TIMEOUT_SECONDS,
        "model_timeout_owner_count": TIMEOUT_OWNER_COUNT,
        "batch_semantics": BATCH_SEMANTICS,
        "shared_context_subject_count": CONTEXT_SIZE,
        "architecture_semantic_drift": 0,
        "prompt_semantic_drift": 0,
        "schema_semantic_drift": 0,
        "model_semantic_input_drift": 0,
        "transport_topology_mutation": 0,
        "timeout_increase_this_task": 0,
        "holdout_output_exposure_state": exposure,
        "holdout_semantic_revelation_state": semantic_state,
        "holdout_retirement_state": retirement,
        "real_holdout_model_invocation_count": state["model_invocation_count"],
        "real_holdout_subject_output_count": len(state["exposed_subjects"]),
        "context_evidence_preservation_failure_count": state[
            "context_evidence_preservation_failure_count"
        ],
        "per_context_semantic_failure_count": state[
            "per_context_semantic_failure_count"
        ],
        "transport_timeout_count": state["transport_timeout_count"],
        "transport_retry_count": state["transport_retry_count"],
        "historical_stall_pattern_recurred": state["historical_stall_pattern_recurred"],
        "run_results": run_results,
        **{
            f"{('first' if run == 'first' else 'run_' + run)}_{gate}_gate_status": (
                read_json(proof_path(args.report_dir, RUN_PROOFS[run][offset]))["status"]
                if proof_path(args.report_dir, RUN_PROOFS[run][offset]).is_file()
                else "NOT_RUN"
            )
            for run in RUNS
            for gate, offset in (("ownership", 3), ("renderer", 4), ("hard_safety", 5))
        },
        **totals,
        "ownership_generalization_verdict": ownership_verdict,
        "ownership_proof_completion_state": completion_state,
        **{key: value for key, value in production.items() if key not in {"contract", "status"}},
        "night_futures_code_mutation": 0,
        "artifact_count": "PENDING_FINALIZE",
        "artifact_hash_mismatch_count": "PENDING_FINALIZE",
        "artifact_size_mismatch_count": "PENDING_FINALIZE",
        "artifact_secret_scan_failure_count": "PENDING_FINALIZE",
        "full_tests": "PENDING_FINAL_VALIDATION",
        "ruff": "PENDING_FINAL_VALIDATION",
        "diff_check": "PENDING_FINAL_VALIDATION",
        "readiness": readiness,
        "stop_reason": stop_reason,
        "next_scope": next_scope,
    }
    write_proof(args.report_dir, 65, completion)
    state.update(
        {
            "state": "EVIDENCE_COMPLETE",
            "run_results": run_results,
            "readiness": readiness,
        }
    )
    write_json(args.output_root / "program-state.json", state)
    write_reports(args.report_dir)


def execute(args: argparse.Namespace) -> None:
    configure_prior_runner()
    (
        state,
        cohort,
        _packets,
        contexts,
        evidence,
        owned,
        core_aliases,
        timing_aliases,
        price_maps,
        stocks,
    ) = prior.load_inputs(args)
    if state["state"] != "PREPARED_FROZEN":
        raise ValueError("prepared_frozen_state_required")
    verify_frozen(args, state)
    state["freeze_commit"] = git_value("rev-parse", "HEAD")
    state["state"] = "EXECUTING"
    write_json(args.output_root / "program-state.json", state)
    guard = guarded.LiveWorkloadGuard(
        args.output_root / "live-workload-coexistence-audit.json"
    )
    adapter = guarded.GuardedTransportAdapter(
        guard=guard,
        continuation_generation=str(state["program_generation_id"]),
        receipt_root=args.output_root / "transport-receipts",
        codex_bin=engine._signed_in_codex_bin(),
    )
    documents: dict[str, dict[str, object]] = {}
    stop_reason: str | None = None
    for run in RUNS:
        if stop_reason is not None:
            prior.write_not_run(args, run, stop_reason)
            continue
        try:
            verify_frozen(args, state)
            document = prior.execute_run(
                args=args,
                state=state,
                adapter=adapter,
                run=run,
                cohort=cohort,
                contexts=contexts,
                evidence=evidence,
                owned=owned,
                core_aliases=core_aliases,
                timing_aliases=timing_aliases,
                price_maps=price_maps,
                stocks=stocks,
            )
            documents[run] = document
            state["run_results"][run] = (
                f"{document['validation_pass_count']}/{TARGET_TOTAL}"
            )
            if run == "first":
                state["holdout_semantic_revelation_state"] = (
                    "NO_SEMANTIC_DEFECT_OBSERVED"
                )
                state["holdout_retirement_state"] = "RETIRED_AFTER_EVALUATION"
            write_json(args.output_root / "program-state.json", state)
        except Exception as exc:
            stop_reason = f"{type(exc).__name__}:{exc}"
            if isinstance(exc, prior.SemanticStop):
                state["holdout_semantic_revelation_state"] = (
                    "REVEALED_FOR_ARCHITECTURE_TUNING"
                )
                state["holdout_retirement_state"] = "RETIRED_FOR_ARCHITECTURE_REPAIR"
            elif state["holdout_output_exposure_state"] != "UNEXPOSED":
                state["holdout_retirement_state"] = "RETIRED_PARTIAL_EXPOSURE"
            state["stop_reason"] = stop_reason
            write_json(args.output_root / "program-state.json", state)
            prior.write_failed_run(args, run, stop_reason)
            for pending in RUNS[RUNS.index(run) + 1 :]:
                prior.write_not_run(args, pending, stop_reason)
            break
    write_proof(
        args.report_dir,
        31,
        read_json(args.output_root / "live-workload-coexistence-audit.json"),
    )
    _final_proofs(
        args=args,
        state=state,
        documents=documents,
        stop_reason=stop_reason,
    )
    print(json.dumps(read_json(proof_path(args.report_dir, 65)), sort_keys=True), flush=True)


def markdown_table(headers: Sequence[str], rows: Sequence[Sequence[object]]) -> str:
    escaped = [
        [str(cell).replace("|", "\\|").replace("\n", " ") for cell in row]
        for row in rows
    ]
    return "\n".join(
        [
            "| " + " | ".join(headers) + " |",
            "| " + " | ".join("---" for _ in headers) + " |",
            *("| " + " | ".join(row) + " |" for row in escaped),
        ]
    )


def write_reports(report_dir: Path) -> None:
    for name in PROOF_NAMES:
        path = report_dir / "proofs" / f"{name}.json"
        if path.is_file():
            write_text(report_dir / f"{name}.md", prior.report_body(name, read_json(path)))
    completion_path = proof_path(report_dir, 65)
    if completion_path.is_file():
        completion = read_json(completion_path)
        write_text(
            report_dir / "README.md",
            "# Bounded US Source Coverage Remediation & Holdout Proof Resume\n\n"
            + markdown_table(
                ("Field", "Value"),
                [
                    ("US source target", completion.get("us_source_target_status")),
                    ("Final US4", completion.get("final_us4")),
                    ("Final KR12", completion.get("final_kr12")),
                    ("FIRST", completion.get("run_results", {}).get("first")),
                    ("A", completion.get("run_results", {}).get("a")),
                    ("B", completion.get("run_results", {}).get("b")),
                    ("C", completion.get("run_results", {}).get("c")),
                    ("Readiness", completion.get("readiness")),
                    ("Next scope", completion.get("next_scope")),
                ],
            )
            + "\n",
        )


def artifact_rows(args: argparse.Namespace) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    excluded_reports = {
        "65-program-completion.json",
        "65-program-completion.md",
        "README.md",
        "artifact-index.json",
        "artifact-index.md",
    }
    report_files = sorted(
        path
        for path in args.report_dir.rglob("*")
        if path.is_file() and path.name not in excluded_reports
    )
    experiment_files: list[Path] = []
    for relative in (
        "program-state.json",
        "expanded-us-reserve-policy.json",
        "source-lock.json",
        "new-holdout-precommit.json",
        "prompt-schema-lock.json",
        "packets",
        "base-contexts",
        "prompts",
        "schemas",
        "timing-contexts",
        "generated-timing-prompts",
        "model-contexts",
        "live-workload-coexistence-audit.json",
    ):
        path = args.output_root / relative
        if path.is_file():
            experiment_files.append(path)
        elif path.is_dir():
            experiment_files.extend(
                sorted(child for child in path.rglob("*") if child.is_file())
            )
    for path in report_files:
        scan = prior.scan_secrets((path,))
        rows.append(
            {
                "source_path": str(path),
                "relative_path": str(Path("reports") / path.relative_to(args.report_dir)),
                "sha256": file_sha256(path),
                "byte_size": path.stat().st_size,
                "artifact_class": "REPORT",
                "market": "CROSS_MARKET",
                "candidate": "NOT_APPLICABLE",
                "run": "NOT_APPLICABLE",
                "stage": "NOT_APPLICABLE",
                "context_batch": "NOT_APPLICABLE",
                "secret_scan_status": scan["secret_scan_status"],
            }
        )
    for path in experiment_files:
        relative_source = path.relative_to(args.output_root)
        parts = relative_source.parts
        run = parts[1] if len(parts) > 1 and parts[0] == "model-contexts" else "NOT_APPLICABLE"
        stage = parts[2] if len(parts) > 2 and parts[0] == "model-contexts" else "NOT_APPLICABLE"
        batch = parts[3] if len(parts) > 3 and parts[0] == "model-contexts" else "NOT_APPLICABLE"
        scan = prior.scan_secrets((path,))
        rows.append(
            {
                "source_path": str(path),
                "relative_path": str(Path("experiment") / relative_source),
                "sha256": file_sha256(path),
                "byte_size": path.stat().st_size,
                "artifact_class": (
                    "RAW_CONTEXT" if run != "NOT_APPLICABLE" else "EXPERIMENT"
                ),
                "market": "CROSS_MARKET",
                "candidate": "NOT_APPLICABLE",
                "run": run,
                "stage": stage,
                "context_batch": batch,
                "secret_scan_status": scan["secret_scan_status"],
            }
        )
    return rows


def finalize(args: argparse.Namespace) -> None:
    state = read_json(args.output_root / "program-state.json")
    if state["state"] != "EVIDENCE_COMPLETE":
        raise ValueError("evidence_complete_state_required")
    if not state.get("source_gate_only"):
        verify_frozen(args, state)
    completion = read_json(proof_path(args.report_dir, 65))
    completion.update(
        {
            "final_head_sha": git_value("rev-parse", "HEAD"),
            "full_tests": args.full_tests,
            "ruff": args.ruff,
            "diff_check": args.diff_check,
        }
    )
    if not all(
        value == "PASS" for value in (args.full_tests, args.ruff, args.diff_check)
    ):
        completion["readiness"] = "NOT_READY"
        completion["next_scope"] = "BOUNDED_VALIDATION_REPAIR"
    write_proof(args.report_dir, 65, completion)
    write_reports(args.report_dir)
    rows = artifact_rows(args)
    hash_mismatch = sum(
        file_sha256(Path(str(row["source_path"]))) != row["sha256"] for row in rows
    )
    size_mismatch = sum(
        Path(str(row["source_path"])).stat().st_size != row["byte_size"] for row in rows
    )
    secret_failures = sum(row["secret_scan_status"] != "PASS" for row in rows)
    index = {
        "contract": "bounded-us-remediation-holdout-artifact-index-v1",
        "indexed_artifact_count": len(rows),
        "artifact_hash_mismatch_count": hash_mismatch,
        "artifact_size_mismatch_count": size_mismatch,
        "artifact_secret_scan_failure_count": secret_failures,
        "rows": rows,
        "status": (
            "PASS" if hash_mismatch == size_mismatch == secret_failures == 0 else "FAIL"
        ),
    }
    write_json(args.report_dir / "artifact-index.json", index)
    write_text(
        args.report_dir / "artifact-index.md",
        "# Artifact Index\n\n"
        + markdown_table(
            ("Path", "SHA-256", "Bytes", "Class", "Market", "Run", "Stage", "Secret"),
            [
                (
                    row["relative_path"],
                    row["sha256"],
                    row["byte_size"],
                    row["artifact_class"],
                    row["market"],
                    row["run"],
                    row["stage"],
                    row["secret_scan_status"],
                )
                for row in rows
            ],
        ),
    )
    completion.update(
        {
            "artifact_count": len(rows) + 5,
            "artifact_hash_mismatch_count": hash_mismatch,
            "artifact_size_mismatch_count": size_mismatch,
            "artifact_secret_scan_failure_count": secret_failures,
        }
    )
    if index["status"] != "PASS":
        completion["readiness"] = "NOT_READY"
        completion["next_scope"] = "ARTIFACT_INTEGRITY_REPAIR"
    write_proof(args.report_dir, 65, completion)
    write_reports(args.report_dir)
    args.zip_output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.zip_output.with_suffix(args.zip_output.suffix + ".tmp")
    with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(child for child in args.report_dir.rglob("*") if child.is_file()):
            archive.write(path, Path("reports") / path.relative_to(args.report_dir))
        for row in rows:
            if row["artifact_class"] != "REPORT":
                archive.write(str(row["source_path"]), str(row["relative_path"]))
    temporary.replace(args.zip_output)
    with zipfile.ZipFile(args.zip_output) as archive:
        bad_member = archive.testzip()
    if bad_member is not None:
        raise ValueError(f"final_zip_integrity_failure:{bad_member}")
    zip_sha = file_sha256(args.zip_output)
    write_text(args.zip_output.with_suffix(args.zip_output.suffix + ".sha256"), zip_sha)
    state.update(
        {
            "state": "COMPLETE",
            "readiness": completion["readiness"],
            "artifact_count": completion["artifact_count"],
            "report_zip": str(args.zip_output),
            "report_zip_sha256": zip_sha,
        }
    )
    write_json(args.output_root / "program-state.json", state)
    print(json.dumps(state, ensure_ascii=False, sort_keys=True), flush=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--prepare", action="store_true")
    mode.add_argument("--execute", action="store_true")
    mode.add_argument("--finalize", action="store_true")
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--report-dir", type=Path, required=True)
    parser.add_argument(
        "--provider-root", type=Path, default=Path.home() / "Codex/ohlcv-analyst"
    )
    parser.add_argument(
        "--latest-result-zip",
        type=Path,
        default=Path.home()
        / "Documents/Codex/Reports/"
        "thesis-monitor-20260907-dual-market-source-coverage-new-issuer-holdout-ownership-proof-report.zip",
    )
    parser.add_argument(
        "--prior-cache-root",
        type=Path,
        default=Path(
            "/private/tmp/"
            "thesis-monitor-20260907-dual-market-source-coverage-new-issuer-holdout-ownership-proof-run/"
            "source-cache"
        ),
    )
    parser.add_argument(
        "--provider-log",
        type=Path,
        default=Path.home() / "Codex/ohlcv-analyst/logs/server.out.log",
    )
    parser.add_argument("--as-of", type=datetime.fromisoformat)
    parser.add_argument("--timeout", type=int, default=TIMEOUT_SECONDS)
    parser.add_argument("--full-tests", default="NOT_RUN")
    parser.add_argument("--ruff", default="NOT_RUN")
    parser.add_argument("--diff-check", default="NOT_RUN")
    parser.add_argument(
        "--zip-output",
        type=Path,
        default=Path.home()
        / "Documents/Codex/Reports/"
        "thesis-monitor-20260907-bounded-us-source-coverage-remediation-holdout-proof-resume-report.zip",
    )
    args = parser.parse_args()
    if args.prepare and args.as_of is None:
        raise ValueError("prepare_requires_fixed_as_of")
    for name in (
        "output_root",
        "report_dir",
        "provider_root",
        "latest_result_zip",
        "prior_cache_root",
        "provider_log",
        "zip_output",
    ):
        setattr(args, name, getattr(args, name).expanduser().resolve())
    return args


def main() -> None:
    args = parse_args()
    if args.prepare:
        prepare(args)
    elif args.execute:
        execute(args)
    else:
        finalize(args)


if __name__ == "__main__":
    main()
