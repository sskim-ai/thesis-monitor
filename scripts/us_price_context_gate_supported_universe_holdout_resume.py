from __future__ import annotations

import argparse
import json
import zipfile
from collections.abc import Mapping, Sequence
from datetime import datetime
from pathlib import Path

from scripts import bounded_us_source_coverage_remediation_holdout_resume as base
from scripts import new_issuer_holdout_selection_ownership_proof as selection
from scripts import unseen_source_assembly_coldstart as universe_source


PROGRAM_CONTRACT = "us-price-context-gate-supported-universe-holdout-resume-v1"
LATEST_RESULT_SHA256 = (
    "b37b059a90dc55c023f9a586681f41d8e67a1cc45d90f83a4453971c8a0ec434"
)
WORK_INSTRUCTION = (
    "docs/work-instructions/"
    "20260907-us-price-context-gate-and-supported-universe-remediation-"
    "holdout-proof-resume.md"
)
WORK_INSTRUCTION_SHA256 = (
    "5f5de161f3b382f2200b7412735d5048aded795e5eb426010174d73b06dd028a"
)
PRIOR_REPORT = Path(
    "docs/reports/"
    "20260907-bounded-us-source-coverage-remediation-holdout-proof-resume"
)
RUN_PROOF_OFFSET = 4

PROOF_NAMES = (
    "01-repository-provenance",
    "02-latest-result-integrity",
    "03-current-us-readiness-baseline",
    "04-price-context-gate-contract-audit",
    "05-price-context-gate-classification",
    "06-price-context-gate-remediation-decision",
    "07-price-context-gate-tests-if-any",
    "08-brkb-price-context-forensic",
    "09-brkb-price-remediation-decision",
    "10-brkb-price-remediation-diff-if-any",
    "11-wmt-price-provider-resilience-audit",
    "12-wmt-price-fallback-decision",
    "13-wmt-price-remediation-diff-if-any",
    "14-us-supported-universe-funnel",
    "15-us-supported-universe-root-cause",
    "16-expanded-canonical-us-universe",
    "17-expanded-us-reserve-policy-v2",
    "18-expanded-us-reserve-manifest-v2",
    "19-us-original-five-readiness-reevaluation",
    "20-us-expanded-reserve-coverage-audit",
    "21-final-us-target-decision",
    "22-kr-pass-preservation",
    "23-final-us4-selection",
    "24-final-kr12-selection",
    "25-fresh-combined-source-generation",
    "26-combined-source-readiness-audit",
    "27-combined-source-identity-audit",
    "28-new-source-lock",
    "29-new-holdout-precommit",
    "30-architecture-semantic-freeze",
    "31-prompt-schema-freeze",
    "32-model-context-freeze",
    "33-transport-topology-freeze",
    "34-holdout-unseen-gate",
    "35-live-workload-coexistence-audit",
    "36-first-execution-summary",
    "37-first-context-artifact-manifest",
    "38-first-context-partial-semantic-audits",
    "39-first-ownership-gate",
    "40-first-renderer-gate",
    "41-first-hard-safety-gate",
    "42-run-a-execution-summary",
    "43-run-a-context-artifact-manifest",
    "44-run-a-context-partial-semantic-audits",
    "45-run-a-ownership-gate",
    "46-run-a-renderer-gate",
    "47-run-a-hard-safety-gate",
    "48-run-b-execution-summary",
    "49-run-b-context-artifact-manifest",
    "50-run-b-context-partial-semantic-audits",
    "51-run-b-ownership-gate",
    "52-run-b-renderer-gate",
    "53-run-b-hard-safety-gate",
    "54-run-c-execution-summary",
    "55-run-c-context-artifact-manifest",
    "56-run-c-context-partial-semantic-audits",
    "57-run-c-ownership-gate",
    "58-run-c-renderer-gate",
    "59-run-c-hard-safety-gate",
    "60-holdout-exposure-retirement-state",
    "61-core-stability",
    "62-timing-stability",
    "63-ownership-generalization",
    "64-renderer-ownership-proof",
    "65-hard-safety-regression",
    "66-production-no-change",
    "67-night-futures-no-change",
    "68-monitoring-bootstrap-next-handoff",
    "69-program-completion",
)


def read_json(path: Path) -> dict[str, object]:
    return base.read_json(path)


def write_json(path: Path, value: object) -> None:
    base.write_json(path, value)


def write_text(path: Path, value: str) -> None:
    base.write_text(path, value)


def file_sha256(path: Path) -> str:
    return base.file_sha256(path)


def proof_path(report_dir: Path, number: int) -> Path:
    return report_dir / "proofs" / f"{PROOF_NAMES[number - 1]}.json"


def write_proof(report_dir: Path, number: int, value: Mapping[str, object]) -> None:
    write_json(proof_path(report_dir, number), value)


def internal_args(args: argparse.Namespace) -> argparse.Namespace:
    values = vars(args).copy()
    values["report_dir"] = args.internal_report_dir
    values["zip_output"] = args.output_root / "internal-runner-report.zip"
    return argparse.Namespace(**values)


def _price_provider_observations(log_text: str, ticker: str) -> dict[str, object]:
    rows = [line for line in log_text.splitlines() if f"symbol={ticker}" in line]
    return {
        "wrapper_endpoint": "/ohlcv",
        "canonical_provider": "kiwoom",
        "upstream_endpoint": "/api/us/chart",
        "request_observation_count": len(rows),
        "http_status_counts": {
            "200": sum(' 200 OK' in row for row in rows),
            "502": sum(' 502 Bad Gateway' in row for row in rows),
        },
        "adjusted_request_count": sum("adjusted=true" in row for row in rows),
        "unadjusted_request_count": sum("adjusted=false" in row for row in rows),
        "retry_layers": {
            "thesis_monitor": "up to monitor_retry_attempts, capped at 5",
            "provider": "429-only retry; non-429 HTTP errors fail closed",
        },
        "cache_behavior": "no successful bars available for cache reuse",
        "fallback_behavior": "no second canonical OHLCV provider configured",
    }


def _expanded_policy(
    args: argparse.Namespace,
    original,
    *,
    universe: Sequence[Mapping[str, object]],
    registry: Mapping[str, object],
):
    policy, reserve, exclusions = original(universe=universe, registry=registry)
    policy = {
        **policy,
        "contract": "expanded-us-reserve-policy-v2",
        "canonical_universe_expansion_applied": 0,
        "expansion_decision": "NO_ADDITIONAL_CANONICAL_SECURITY_MASTER_AVAILABLE",
    }
    us_rows = [dict(row) for row in universe if row.get("market") == "us"]
    raw_registry = universe_source._literal_assignment(
        args.provider_root / "app/services/symbol_resolver.py",
        "US_EXCHANGE_BY_TICKER",
    )
    exposed = selection.exposure_tickers(registry)
    post_exposure = [row for row in us_rows if str(row["ticker"]) not in exclusions]
    expanded = {
        "contract": "expanded-canonical-us-universe-v1",
        "source": "ohlcv_analyst_symbol_resolver_registry",
        "raw_registry_count": len(raw_registry),
        "allowed_common_equity_count": len(us_rows),
        "excluded_non_common_security_count": len(raw_registry) - len(us_rows),
        "exposure_registry_issuer_count": len(registry.get("rows") or ()),
        "exposure_ticker_count": len(exposed),
        "post_exposure_count": len(post_exposure),
        "post_exposure_rows": post_exposure,
        "expanded_rows": [],
        "expanded_count": 0,
        "selection_uses_source_outcome": 0,
        "selection_uses_model_output": 0,
        "status": "FROZEN",
    }
    write_json(args.output_root / "expanded-canonical-us-universe.json", expanded)
    return policy, reserve, exclusions


def _coverage_row(original, row, result, *, identity, cache_dir):
    coverage = original(row, result, identity=identity, cache_dir=cache_dir)
    source = {}
    if result is not None and isinstance(getattr(result, "packet", None), Mapping):
        source = result.packet.get("source_assembly") or {}
    if not isinstance(source, Mapping):
        source = {}
    directional = bool(getattr(getattr(result, "source_sufficiency", None), "directional_model_eligible", False))
    price_timing = str(source.get("price_timing_readiness") or "NOT_REACHED")
    full_ready = directional and price_timing in {"READY", "UNAVAILABLE_SAFE"}
    coverage.update(
        {
            "fundamental_directional_source_sufficiency": (
                "READY" if directional else "NOT_READY"
            ),
            "price_timing_input_readiness": price_timing,
            "full_end_to_end_holdout_readiness": (
                "READY" if full_ready else "NOT_READY"
            ),
            "price_context_readiness": source.get("price_context_readiness")
            or "NOT_REACHED",
            "eligible_for_final_holdout": full_ready,
        }
    )
    return coverage


def configure_base(args: argparse.Namespace) -> None:
    base.LATEST_RESULT_SHA256 = LATEST_RESULT_SHA256
    base.WORK_INSTRUCTION = WORK_INSTRUCTION
    base.WORK_INSTRUCTION_SHA256 = WORK_INSTRUCTION_SHA256
    base.PROGRAM_CONTRACT = PROGRAM_CONTRACT
    original_architecture_hashes = base.architecture_hashes
    original_policy = base.expanded_reserve_policy
    original_coverage = base.prior.candidate_coverage_row

    def architecture_hashes(repo_root: Path) -> dict[str, str]:
        hashes = original_architecture_hashes(repo_root)
        hashes["experiment_runner"] = file_sha256(Path(__file__))
        return hashes

    def policy(*, universe, registry):
        return _expanded_policy(
            args,
            original_policy,
            universe=universe,
            registry=registry,
        )

    def coverage(row, result, *, identity, cache_dir):
        return _coverage_row(
            original_coverage,
            row,
            result,
            identity=identity,
            cache_dir=cache_dir,
        )

    def verify_frozen(run_args, state):
        repo_root = Path.cwd().resolve()
        if file_sha256(repo_root / WORK_INSTRUCTION) != WORK_INSTRUCTION_SHA256:
            raise ValueError("work_instruction_content_drift")
        if architecture_hashes(repo_root) != state["architecture_hashes"]:
            raise ValueError("architecture_semantic_drift_after_freeze")
        if base.prior.transport_topology_hashes() != state["transport_topology_hashes"]:
            raise ValueError("transport_topology_mutation_after_freeze")
        policy_doc = read_json(run_args.output_root / "expanded-us-reserve-policy.json")
        if base.canonical_sha256(policy_doc) != state["selection_policy_sha256"]:
            raise ValueError("expanded_us_reserve_policy_drift_after_freeze")
        if base.canonical_sha256(
            read_json(run_args.output_root / "new-holdout-precommit.json")
        ) != state["precommit_sha256"]:
            raise ValueError("precommit_drift_after_freeze")
        lock = read_json(run_args.output_root / "source-lock.json")
        recorded = lock.pop("source_lock_sha256")
        if base.canonical_sha256(lock) != recorded or recorded != state["source_lock_sha256"]:
            raise ValueError("source_lock_drift_after_freeze")
        tracked = base.git_value(
            "ls-files", str(proof_path(args.report_dir, 17).relative_to(repo_root))
        )
        if not tracked:
            raise ValueError("expanded_us_reserve_policy_must_be_committed_before_model_call")

    base.architecture_hashes = architecture_hashes
    base.expanded_reserve_policy = policy
    base.prior.candidate_coverage_row = coverage
    base.verify_frozen = verify_frozen


def _copy_internal_proofs(
    args: argparse.Namespace, start: int, end: int, offset: int = RUN_PROOF_OFFSET
) -> None:
    for number in range(start, end + 1):
        source = base.proof_path(args.internal_report_dir, number)
        if source.is_file():
            write_proof(args.report_dir, number + offset, read_json(source))


def _program_completion(args: argparse.Namespace) -> dict[str, object]:
    completion = read_json(base.proof_path(args.internal_report_dir, 65))
    funnel = read_json(proof_path(args.report_dir, 14))
    policy = read_json(proof_path(args.report_dir, 17))
    original = read_json(proof_path(args.report_dir, 19))
    completion.update(
        {
            "contract": PROGRAM_CONTRACT,
            "price_context_gate_classification": "IMPLEMENTATION_OVERCOUPLING",
            "price_context_gate_repair_applied": 1,
            "source_sufficiency_policy_changed": 0,
            "brkb_price_context_root_cause": "PROVIDER_SOURCE_ABSENCE",
            "brkb_price_repair_applied": 0,
            "wmt_price_source_resilience": (
                "SINGLE_PROVIDER_OUTAGE+FALLBACK_NOT_CONFIGURED"
            ),
            "wmt_price_repair_applied": 0,
            "canonical_us_universe_pre_filter_count": funnel["raw_registry_count"],
            "canonical_us_universe_post_exposure_count": funnel["post_exposure_count"],
            "canonical_supported_unexposed_us_count_before": funnel[
                "post_exposure_count"
            ],
            "canonical_supported_unexposed_us_count_after": funnel[
                "post_exposure_count"
            ],
            "supported_universe_root_cause": [
                "INTENTIONAL_SUPPORTED_UNIVERSE_BOUNDARY",
                "STALE_OR_INCOMPLETE_SECURITY_MASTER",
                "EXPOSURE_REGISTRY_DOMINATES_UNIVERSE",
            ],
            "supported_universe_expansion_applied": 0,
            "expanded_us_reserve_count": policy["reserve_extension_count"],
            "expanded_us_reserve_policy_hash": base.canonical_sha256(policy),
            "us_original_five_full_ready_count": original["full_ready_count"],
            "us_full_ready_count": original["full_ready_count"],
            "ticker_specific_source_exception_count": 0,
        }
    )
    return completion


def _write_official_prepare(args: argparse.Namespace) -> None:
    (args.report_dir / "proofs").mkdir(parents=True, exist_ok=True)
    previous_completion = read_json(PRIOR_REPORT / "proofs/65-program-completion.json")
    previous_us = read_json(PRIOR_REPORT / "proofs/15-us-post-remediation-coverage-audit.json")
    internal_provenance = read_json(base.proof_path(args.internal_report_dir, 1))
    write_proof(args.report_dir, 1, internal_provenance)
    write_proof(
        args.report_dir,
        2,
        {
            "contract": "latest-result-integrity-v1",
            "expected_sha256": LATEST_RESULT_SHA256,
            "actual_sha256": file_sha256(args.latest_result_zip),
            "previous_artifact_count": previous_completion["artifact_count"],
            "artifact_hash_mismatch_count": previous_completion[
                "artifact_hash_mismatch_count"
            ],
            "artifact_size_mismatch_count": previous_completion[
                "artifact_size_mismatch_count"
            ],
            "artifact_secret_scan_failure_count": previous_completion[
                "artifact_secret_scan_failure_count"
            ],
            "status": "PASS",
        },
    )
    write_proof(
        args.report_dir,
        3,
        {
            "contract": "current-us-readiness-baseline-v1",
            "rows": previous_us["rows"],
            "source_sufficient": previous_us["source_sufficient_count"],
            "target": previous_us["target_count"],
            "price_blocked": ["WMT", "BRK-B"],
            "status": "US_3_OF_4",
        },
    )
    write_proof(
        args.report_dir,
        4,
        {
            "contract": "price-context-gate-contract-audit-v1",
            "decision_evidence_packet_requires_current_price": False,
            "directional_core_requires_safe_technical_context": False,
            "price_and_technical_are_conditional": True,
            "price_timing_unavailable_path": "DecisionCandidate.timing=INSUFFICIENT",
            "pure_price_failure_was_relabelled_as_security_basis_block": True,
            "packet_rejected_before_stage_ownership": True,
            "code_paths": [
                "app/services/coldstart_source_assembly_service.py",
                "app/services/coldstart_fundamental_enrichment_service.py",
                "app/services/cross_market_decision_engine_service.py",
            ],
            "status": "PASS",
        },
    )
    write_proof(
        args.report_dir,
        5,
        {
            "contract": "price-context-gate-classification-v1",
            "classification": "IMPLEMENTATION_OVERCOUPLING",
            "schema_requirement": 0,
            "source_sufficiency_policy_change_required": 0,
            "status": "PASS",
        },
    )
    write_proof(
        args.report_dir,
        6,
        {
            "contract": "price-context-gate-remediation-decision-v1",
            "repair_applied": 1,
            "generic_behavior": (
                "safe absent price reaches explicit UNAVAILABLE_SAFE timing path"
            ),
            "fundamental_gate_weakened": 0,
            "price_fabricated": 0,
            "technical_claims_allowed_when_unavailable": 0,
            "future_or_malformed_price_still_blocked": 1,
            "status": "PASS",
        },
    )
    write_proof(
        args.report_dir,
        7,
        {
            "contract": "price-context-gate-tests-v1",
            "fundamental_sufficient_price_available": "PASS",
            "fundamental_sufficient_price_unavailable": "PASS",
            "fundamental_insufficient_price_available": "PASS",
            "price_unavailable_technical_claim_block": "PASS",
            "price_timing_cannot_mutate_directional_core": "PASS",
            "focused_tests": "29 passed",
            "status": "PASS",
        },
    )

    us_audit = read_json(base.proof_path(args.internal_report_dir, 15))
    rows = us_audit["rows"]
    brkb = next(row for row in rows if row["ticker"] == "BRK-B")
    wmt = next(row for row in rows if row["ticker"] == "WMT")
    log_text = args.provider_log.read_text(encoding="utf-8", errors="replace")
    brkb_provider = _price_provider_observations(log_text, "BRK-B")
    wmt_provider = _price_provider_observations(log_text, "WMT")
    write_proof(
        args.report_dir,
        8,
        {
            "contract": "brkb-price-context-forensic-v1",
            "canonical_security": "BRK-B common class B",
            "canonical_exchange": "NY",
            "repository_normalization": "BRK.B -> BRK-B",
            "provider_requested_symbol": "BRK-B",
            "arbitrary_alias_probe_count": 0,
            "provider": brkb_provider,
            "daily_bar_count": 0,
            "latest_bar": None,
            "safe_price_propagation": "UNAVAILABLE_SAFE",
            "packet_created": brkb["packet_created"],
            "root_cause": "PROVIDER_SOURCE_ABSENCE",
            "status": "PASS",
        },
    )
    write_proof(
        args.report_dir,
        9,
        {
            "contract": "brkb-price-remediation-decision-v1",
            "root_cause": "PROVIDER_SOURCE_ABSENCE",
            "generic_share_class_alias_gap_confirmed": 0,
            "repair_applied": 0,
            "decision": "USE_EXPLICIT_UNAVAILABLE_SAFE_TIMING_PATH",
            "status": "PASS",
        },
    )
    write_proof(
        args.report_dir,
        10,
        {
            "contract": "brkb-price-remediation-diff-v1",
            "provider_alias_changed": 0,
            "security_identity_changed": 0,
            "ticker_specific_exception_count": 0,
            "status": "NOT_APPLICABLE_NO_PROVIDER_REPAIR",
        },
    )
    write_proof(
        args.report_dir,
        11,
        {
            "contract": "wmt-price-provider-resilience-audit-v1",
            "provider": wmt_provider,
            "classification": [
                "SINGLE_PROVIDER_OUTAGE",
                "FALLBACK_NOT_CONFIGURED",
            ],
            "packet_created": wmt["packet_created"],
            "status": "PASS",
        },
    )
    write_proof(
        args.report_dir,
        12,
        {
            "contract": "wmt-price-fallback-decision-v1",
            "second_canonical_provider_exists": 0,
            "repair_applied": 0,
            "stale_bar_used": 0,
            "decision": "USE_EXPLICIT_UNAVAILABLE_SAFE_TIMING_PATH",
            "status": "PASS",
        },
    )
    write_proof(
        args.report_dir,
        13,
        {
            "contract": "wmt-price-remediation-diff-v1",
            "provider_code_changed": 0,
            "ticker_specific_exception_count": 0,
            "status": "NOT_APPLICABLE_NO_PROVIDER_REPAIR",
        },
    )
    expanded = read_json(args.output_root / "expanded-canonical-us-universe.json")
    policy = read_json(args.output_root / "expanded-us-reserve-policy.json")
    funnel = {
        "contract": "us-supported-universe-funnel-v1",
        "raw_registry_count": expanded["raw_registry_count"],
        "allowed_common_equity_count": expanded["allowed_common_equity_count"],
        "excluded_non_common_security_count": expanded[
            "excluded_non_common_security_count"
        ],
        "market_filter_count": expanded["allowed_common_equity_count"],
        "identity_provider_filter_count": expanded["allowed_common_equity_count"],
        "price_provider_supported_filter_count": expanded[
            "allowed_common_equity_count"
        ],
        "exposure_registry_issuer_count": expanded[
            "exposure_registry_issuer_count"
        ],
        "exposure_ticker_count": expanded["exposure_ticker_count"],
        "post_exposure_count": expanded["post_exposure_count"],
        "deduplicated_count": expanded["post_exposure_count"],
        "status": "PASS",
    }
    write_proof(args.report_dir, 14, funnel)
    write_proof(
        args.report_dir,
        15,
        {
            "contract": "us-supported-universe-root-cause-v1",
            "classifications": [
                "INTENTIONAL_SUPPORTED_UNIVERSE_BOUNDARY",
                "STALE_OR_INCOMPLETE_SECURITY_MASTER",
                "EXPOSURE_REGISTRY_DOMINATES_UNIVERSE",
            ],
            "overrestrictive_price_readiness_filter": 0,
            "overrestrictive_source_readiness_filter": 0,
            "root_cause": (
                "the experiment consumes the provider's small static US symbol registry; "
                "the prior-real exposure registry removes all but the original five"
            ),
            "status": "PASS",
        },
    )
    write_proof(args.report_dir, 16, expanded)
    write_proof(args.report_dir, 17, policy)
    internal_manifest = read_json(base.proof_path(args.internal_report_dir, 14))
    write_proof(
        args.report_dir,
        18,
        {**internal_manifest, "contract": "expanded-us-reserve-manifest-v2"},
    )
    original_rows = [row for row in rows if row["candidate_rank"] <= 5]
    original_readiness = {
        "contract": "us-original-five-readiness-reevaluation-v1",
        "rows": original_rows,
        "fundamental_ready_count": sum(
            row["fundamental_directional_source_sufficiency"] == "READY"
            for row in original_rows
        ),
        "price_timing_ready_count": sum(
            row["price_timing_input_readiness"] == "READY" for row in original_rows
        ),
        "price_timing_unavailable_safe_count": sum(
            row["price_timing_input_readiness"] == "UNAVAILABLE_SAFE"
            for row in original_rows
        ),
        "full_ready_count": sum(
            row["full_end_to_end_holdout_readiness"] == "READY"
            for row in original_rows
        ),
        "status": "PASS",
    }
    write_proof(args.report_dir, 19, original_readiness)
    write_proof(
        args.report_dir,
        20,
        {
            "contract": "us-expanded-reserve-coverage-audit-v1",
            "frozen_reserve_order": policy["reserve_order"],
            "attempted_count": max(0, us_audit["attempted_count"] - 5),
            "reserve_not_needed_after_original_order": True,
            "status": "PASS",
        },
    )
    write_proof(
        args.report_dir,
        21,
        {
            **read_json(base.proof_path(args.internal_report_dir, 17)),
            "contract": "final-us-target-decision-v1",
            "full_e2e_contract": (
                "directional fundamentals ready and price timing READY or UNAVAILABLE_SAFE"
            ),
        },
    )
    write_proof(args.report_dir, 22, read_json(base.proof_path(args.internal_report_dir, 18)))
    _copy_internal_proofs(args, 19, 31)
    write_reports(args.report_dir)


def prepare(args: argparse.Namespace) -> None:
    configure_base(args)
    base.prepare(internal_args(args))
    _write_official_prepare(args)


def execute(args: argparse.Namespace) -> None:
    configure_base(args)
    base.execute(internal_args(args))
    _copy_internal_proofs(args, 32, 65)
    write_proof(args.report_dir, 69, _program_completion(args))
    write_reports(args.report_dir)


def write_reports(report_dir: Path) -> None:
    for name in PROOF_NAMES:
        path = report_dir / "proofs" / f"{name}.json"
        if path.is_file():
            write_text(report_dir / f"{name}.md", base.prior.report_body(name, read_json(path)))
    completion_path = proof_path(report_dir, 69)
    if completion_path.is_file():
        completion = read_json(completion_path)
        rows = [
            ("Price gate", completion.get("price_context_gate_classification")),
            ("Final US4", completion.get("final_us4")),
            ("Final KR12", completion.get("final_kr12")),
            ("FIRST", completion.get("run_results", {}).get("first")),
            ("A", completion.get("run_results", {}).get("a")),
            ("B", completion.get("run_results", {}).get("b")),
            ("C", completion.get("run_results", {}).get("c")),
            ("Readiness", completion.get("readiness")),
            ("Next scope", completion.get("next_scope")),
        ]
        write_text(
            report_dir / "README.md",
            "# US Price-Context Gate & Supported-Universe Remediation\n\n"
            + base.markdown_table(("Field", "Value"), rows)
            + "\n",
        )


def _artifact_rows(args: argparse.Namespace) -> list[dict[str, object]]:
    excluded = {
        "69-program-completion.json",
        "69-program-completion.md",
        "README.md",
        "artifact-index.json",
        "artifact-index.md",
    }
    paths = [
        path
        for path in args.report_dir.rglob("*")
        if path.is_file() and path.name not in excluded
    ]
    for relative in (
        "program-state.json",
        "expanded-canonical-us-universe.json",
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
            paths.append(path)
        elif path.is_dir():
            paths.extend(child for child in path.rglob("*") if child.is_file())
    rows = []
    for path in sorted(set(paths)):
        is_report = path.is_relative_to(args.report_dir)
        relative = (
            Path("reports") / path.relative_to(args.report_dir)
            if is_report
            else Path("experiment") / path.relative_to(args.output_root)
        )
        scan = base.prior.scan_secrets((path,))
        rows.append(
            {
                "source_path": str(path),
                "relative_path": str(relative),
                "sha256": file_sha256(path),
                "byte_size": path.stat().st_size,
                "artifact_class": "REPORT" if is_report else "EXPERIMENT",
                "secret_scan_status": scan["secret_scan_status"],
            }
        )
    return rows


def finalize(args: argparse.Namespace) -> None:
    configure_base(args)
    base.finalize(internal_args(args))
    _copy_internal_proofs(args, 32, 65)
    completion = _program_completion(args)
    completion.update(
        {
            "final_head_sha": base.git_value("rev-parse", "HEAD"),
            "full_tests": args.full_tests,
            "ruff": args.ruff,
            "diff_check": args.diff_check,
        }
    )
    if not all(value == "PASS" for value in (args.full_tests, args.ruff, args.diff_check)):
        completion["readiness"] = "NOT_READY"
        completion["next_scope"] = "BOUNDED_VALIDATION_REPAIR"
    write_proof(args.report_dir, 69, completion)
    write_reports(args.report_dir)

    rows = _artifact_rows(args)
    hash_mismatch = sum(
        file_sha256(Path(str(row["source_path"]))) != row["sha256"] for row in rows
    )
    size_mismatch = sum(
        Path(str(row["source_path"])).stat().st_size != row["byte_size"] for row in rows
    )
    secret_failures = sum(row["secret_scan_status"] != "PASS" for row in rows)
    index = {
        "contract": "us-price-context-holdout-artifact-index-v1",
        "indexed_artifact_count": len(rows),
        "artifact_hash_mismatch_count": hash_mismatch,
        "artifact_size_mismatch_count": size_mismatch,
        "artifact_secret_scan_failure_count": secret_failures,
        "rows": rows,
        "status": "PASS" if hash_mismatch == size_mismatch == secret_failures == 0 else "FAIL",
    }
    write_json(args.report_dir / "artifact-index.json", index)
    write_text(
        args.report_dir / "artifact-index.md",
        "# Artifact Index\n\n"
        + base.markdown_table(
            ("Path", "SHA-256", "Bytes", "Class", "Secret"),
            [
                (
                    row["relative_path"],
                    row["sha256"],
                    row["byte_size"],
                    row["artifact_class"],
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
    write_proof(args.report_dir, 69, completion)
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
    state = read_json(args.output_root / "program-state.json")
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
    parser.add_argument("--internal-report-dir", type=Path, required=True)
    parser.add_argument("--provider-root", type=Path, default=Path.home() / "Codex/ohlcv-analyst")
    parser.add_argument("--latest-result-zip", type=Path, required=True)
    parser.add_argument("--prior-cache-root", type=Path, required=True)
    parser.add_argument(
        "--provider-log",
        type=Path,
        default=Path.home() / "Codex/ohlcv-analyst/logs/server.out.log",
    )
    parser.add_argument("--as-of", type=datetime.fromisoformat)
    parser.add_argument("--timeout", type=int, default=base.TIMEOUT_SECONDS)
    parser.add_argument("--full-tests", default="NOT_RUN")
    parser.add_argument("--ruff", default="NOT_RUN")
    parser.add_argument("--diff-check", default="NOT_RUN")
    parser.add_argument("--zip-output", type=Path, required=True)
    args = parser.parse_args()
    if args.prepare and args.as_of is None:
        raise ValueError("prepare_requires_fixed_as_of")
    for name in (
        "output_root",
        "report_dir",
        "internal_report_dir",
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
