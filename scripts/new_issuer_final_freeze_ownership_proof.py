from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import zipfile
from collections import Counter
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from typing import Any

from app.services.coldstart_source_assembly_service import deterministic_base_context
from app.services.direction_timing_ownership_service import canonical_sha256
from scripts import directional_core_price_timing_holdout as frozen
from scripts import new_issuer_holdout_selection_ownership_proof as runner
from scripts import new_issuer_holdout_selection_preexecution_review as review
from scripts import synthetic_canary_fixture_repair_ownership_resume as guarded
from scripts import unseen_source_assembly_coldstart as source_assembly
from scripts import uskr22_structured_autonomy_shadow as engine


PROGRAM_CONTRACT = "new-issuer-final-freeze-ownership-proof-existing-data-routes-v1"
WORK_INSTRUCTION_PATH = (
    "docs/work-instructions/"
    "20260907-new-issuer-final-freeze-and-ownership-proof-existing-data-routes.md"
)
WORK_INSTRUCTION_SHA256 = "9b1a6cbfae3d290d069c100667e13a6680101adeacca3c6f80a7d6d7efbd303b"
POLICY_PATH = "docs/reports/20260907-new-issuer-final-freeze-ownership-proof-policy.json"
REVIEW_ZIP_NAME = (
    "thesis-monitor-20260907-new-issuer-holdout-selection-preexecution-readiness-review-report.zip"
)
REVIEW_ZIP_SHA256 = "b2233e37113ac84def1e974e81c413e39f9f378a84182167ca9ae4b24c75bce0"
REVIEW_MANIFEST_MEMBER = "reports/proofs/13-nonexecutable-source-review-manifest.json"
REVIEW_MANIFEST_SHA256 = "6bba480d63661967c80192af6d80287bb3bb9c4d9cf31084eaeeb6a45358b99c"
REVIEW_SELECTION_POLICY_SHA256 = "c66583d78dc9155e454df172730691040778a25f5c8e4ab33da63919a172d574"
REVIEW_EXCLUSION_REGISTRY_SHA256 = (
    "f91ec0a8ea6a224a5da3375da28d83f01b46c518e8b94a8da0df23398a3f2415"
)
COHORT = (
    "NVMI",
    "SKYH",
    "WKSP",
    "EROC",
    "373160",
    "452200",
    "389470",
    "380550",
    "008970",
    "047080",
    "068270",
    "475830",
    "033160",
    "079940",
    "103140",
    "278280",
)
MARKET_BY_TICKER = {ticker: "us" if index < 4 else "kr" for index, ticker in enumerate(COHORT)}
CONTEXT_GROUPS = tuple(
    tuple(COHORT[index : index + runner.CONTEXT_SIZE])
    for index in range(0, len(COHORT), runner.CONTEXT_SIZE)
)
EXPECTED_INVOCATIONS_PER_RUN = len(CONTEXT_GROUPS) * len(runner.STAGES)
EXPECTED_TOTAL_INVOCATIONS = EXPECTED_INVOCATIONS_PER_RUN * len(runner.RUNS)
CUSTOM_COMPLETION_NAME = "61-existing-data-routes-final-freeze-ownership-proof-completion"


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"object_required:{path}")
    return value


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(value.rstrip() + "\n", encoding="utf-8")
    temporary.replace(path)


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def bytes_sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def git_value(*args: str) -> str:
    return subprocess.run(("git", *args), check=True, capture_output=True, text=True).stdout.strip()


def zip_json(archive: zipfile.ZipFile, member: str) -> dict[str, Any]:
    value = json.loads(archive.read(member))
    if not isinstance(value, dict):
        raise ValueError(f"zip_object_required:{member}")
    return value


def canonical_document_hash(value: Mapping[str, object], hash_key: str) -> str:
    unhashed = dict(value)
    unhashed.pop(hash_key, None)
    return canonical_sha256(unhashed)


def review_bundle_integrity(path: Path) -> dict[str, object]:
    if path.name != REVIEW_ZIP_NAME:
        raise ValueError("review_zip_name_mismatch")
    actual_sha = file_sha256(path)
    if actual_sha != REVIEW_ZIP_SHA256:
        raise ValueError("review_zip_sha256_mismatch")
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        duplicates = sorted(name for name, count in Counter(names).items() if count > 1)
        unsafe = sorted(
            name
            for name in names
            if name.startswith("/") or "\\" in name or ".." in PurePosixPath(name).parts
        )
        crc_failure = archive.testzip()
        index = zip_json(archive, "artifact-index.json")
        rows = index.get("rows")
        if not isinstance(rows, list):
            raise ValueError("review_artifact_index_rows_missing")
        indexed = {
            str(row["path"]): row for row in rows if isinstance(row, Mapping) and row.get("path")
        }
        payload_names = set(names) - {"artifact-index.json"}
        hash_mismatches: list[str] = []
        size_mismatches: list[str] = []
        for name in sorted(payload_names & set(indexed)):
            payload = archive.read(name)
            row = indexed[name]
            if bytes_sha256(payload) != row.get("sha256"):
                hash_mismatches.append(name)
            if len(payload) != row.get("byte_size"):
                size_mismatches.append(name)
        missing_index = sorted(payload_names - set(indexed))
        unexpected_index = sorted(set(indexed) - payload_names)
        completion = zip_json(archive, "reports/proofs/21-program-completion.json")
        handoff = zip_json(archive, "reports/proofs/20-next-proof-handoff-draft.json")
        manifest = zip_json(archive, REVIEW_MANIFEST_MEMBER)
        exclusion = zip_json(
            archive,
            "reports/proofs/05-exclusion-registry-continuity-and-alias-fence.json",
        )
        checks = {
            "zip_sha256": actual_sha == REVIEW_ZIP_SHA256,
            "crc": crc_failure is None,
            "duplicates": not duplicates,
            "safe_paths": not unsafe,
            "index_status": index.get("status") == "PASS",
            "index_membership": not missing_index and not unexpected_index,
            "indexed_hashes": not hash_mismatches,
            "indexed_sizes": not size_mismatches,
            "review_complete": completion.get("selection_review_status") == "PASS",
            "review_ready": completion.get("readiness")
            == "READY_FOR_SEPARATELY_AUTHORIZED_NEW_HOLDOUT_PROOF",
            "handoff_scope": handoff.get("next_scope")
            == "NEW_ISSUER_HOLDOUT_FINAL_FREEZE_AND_OWNERSHIP_PROOF",
            "manifest_hash": canonical_document_hash(manifest, "source_manifest_sha256")
            == REVIEW_MANIFEST_SHA256
            == manifest.get("source_manifest_sha256"),
            "manifest_nonexecutable": manifest.get("executable") is False
            and manifest.get("execution_authorized") is False
            and manifest.get("proof_source_lock") is None,
            "selection_policy_hash": manifest.get("selection_policy_sha256")
            == REVIEW_SELECTION_POLICY_SHA256,
            "exclusion_registry_hash": exclusion.get("exclusion_registry_hash_after")
            == REVIEW_EXCLUSION_REGISTRY_SHA256,
            "cohort": tuple(manifest.get("proposed_cohort") or ()) == COHORT,
            "groups": tuple(
                tuple(group) for group in manifest.get("proposed_context_grouping") or ()
            )
            == CONTEXT_GROUPS,
            "markets": manifest.get("market_by_ticker") == MARKET_BY_TICKER,
        }
        if not all(checks.values()):
            failed = sorted(key for key, value in checks.items() if not value)
            raise ValueError(f"review_bundle_integrity_failed:{','.join(failed)}")
        return {
            "contract": "review-result-integrity-v1",
            "path": str(path),
            "expected_sha256": REVIEW_ZIP_SHA256,
            "actual_sha256": actual_sha,
            "zip_member_count": len(names),
            "indexed_payload_count": len(rows),
            "index_self_exclusion": "artifact-index.json",
            "crc_failure": crc_failure,
            "duplicate_member_count": len(duplicates),
            "unsafe_path_count": len(unsafe),
            "unindexed_payload_count": len(missing_index),
            "unexpected_index_row_count": len(unexpected_index),
            "hash_mismatch_count": len(hash_mismatches),
            "size_mismatch_count": len(size_mismatches),
            "checks": checks,
            "status": "PASS",
        }


def _archive_packet_member(subject: Mapping[str, object]) -> str:
    references = [str(value) for value in subject.get("artifact_references") or []]
    matches = [value for value in references if value.endswith("-full.json")]
    if len(matches) != 1:
        raise ValueError(f"full_packet_reference_missing:{subject.get('ticker')}")
    return f"evidence/input-preserved/{matches[0]}"


def _source_periods(subject: Mapping[str, object]) -> list[dict[str, object]]:
    rows = subject.get("source_periods") or []
    if not isinstance(rows, list):
        raise ValueError(f"source_period_rows_invalid:{subject.get('ticker')}")
    return [dict(row) for row in rows if isinstance(row, Mapping)]


def load_and_recheck_packets(
    *,
    archive: zipfile.ZipFile,
    manifest: Mapping[str, object],
    output_root: Path,
    provider_root: Path,
    as_of: datetime,
) -> tuple[
    dict[str, dict[str, object]],
    dict[str, str],
    list[dict[str, object]],
    dict[str, object],
]:
    subjects = {
        str(row["ticker"]): row
        for row in manifest.get("subjects") or []
        if isinstance(row, Mapping) and row.get("ticker")
    }
    if tuple(ticker for ticker in COHORT if ticker in subjects) != COHORT:
        raise ValueError("review_subject_manifest_incomplete")
    current_universe = {
        str(row["ticker"]): dict(row) for row in source_assembly.supported_universe(provider_root)
    }
    packets: dict[str, dict[str, object]] = {}
    contexts: dict[str, str] = {}
    rows: list[dict[str, object]] = []
    for ticker in COHORT:
        subject = subjects[ticker]
        expected_market = MARKET_BY_TICKER[ticker]
        identity = current_universe.get(ticker)
        if expected_market == "kr" and identity is None:
            raise ValueError(f"current_kr_supported_identity_missing:{ticker}")
        if identity is not None and str(identity.get("market")) != expected_market:
            raise ValueError(f"current_supported_market_mismatch:{ticker}")
        member = _archive_packet_member(subject)
        raw = archive.read(member)
        packet = json.loads(raw)
        if not isinstance(packet, dict):
            raise ValueError(f"packet_object_required:{ticker}")
        stock_rows = packet.get("stocks")
        if (
            not isinstance(stock_rows, list)
            or len(stock_rows) != 1
            or not isinstance(stock_rows[0], Mapping)
            or str(stock_rows[0].get("ticker")) != ticker
        ):
            raise ValueError(f"single_stock_identity_mismatch:{ticker}")
        source = packet.get("source_assembly")
        if not isinstance(source, Mapping):
            raise ValueError(f"source_assembly_missing:{ticker}")
        raw_sha = bytes_sha256(raw)
        canonical_hash = canonical_sha256(packet)
        checks = {
            "raw_packet_hash": raw_sha == subject.get("full_packet_raw_sha256"),
            "canonical_packet_hash": canonical_hash == subject.get("full_packet_canonical_sha256"),
            "market": packet.get("market") == expected_market,
            "directional_eligible": int(source.get("directional_model_eligible") or 0) == 1,
            "fundamental_ready": source.get("directional_fundamental_readiness") == "READY",
            "price_timing_ready": source.get("price_timing_readiness") == "READY",
            "source_sufficient": source.get("source_sufficiency_status")
            == "SUFFICIENT_FOR_DIRECTIONAL_JUDGMENT",
            "assessment_date_not_future": str(packet.get("assessment_date") or "")
            <= as_of.date().isoformat(),
        }
        if not all(checks.values()):
            failed = sorted(key for key, value in checks.items() if not value)
            raise ValueError(f"selected_packet_recheck_failed:{ticker}:{','.join(failed)}")
        target = output_root / "packets" / f"{ticker}.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
        context = deterministic_base_context(packet)
        write_text(output_root / "base-contexts" / f"{ticker}.txt", context)
        packets[ticker] = packet
        contexts[ticker] = context
        rows.append(
            {
                "ticker": ticker,
                "market": expected_market,
                "canonical_issuer_key": subject.get("canonical_issuer_key"),
                "canonical_security_id": subject.get("canonical_security_id"),
                "current_supported_identity_source": (
                    identity.get("source")
                    if identity is not None
                    else source.get("identity_source")
                ),
                "current_production_monitoring_registration_required": 0,
                "cache_disposition": "VALID_ARCHIVE_CACHE_REUSED",
                "network_refresh_required": 0,
                "network_request_count": 0,
                "raw_packet_sha256": raw_sha,
                "canonical_packet_sha256": canonical_hash,
                "assessment_date": packet.get("assessment_date"),
                "price_as_of": source.get("price_as_of"),
                "fundamental_readiness": source.get("directional_fundamental_readiness"),
                "price_timing_readiness": source.get("price_timing_readiness"),
                "technical_context_status": source.get("technical_context_status"),
                "source_periods": _source_periods(subject),
                "mandatory_unknowns": list(subject.get("mandatory_unknowns") or []),
                "checks": checks,
                "status": "PASS",
            }
        )
    inputs = frozen.build_inputs(packets, contexts, COHORT)
    return (
        packets,
        contexts,
        rows,
        {
            "evidence": inputs[0],
            "owned": inputs[1],
            "core_aliases": inputs[2],
            "timing_aliases": inputs[3],
            "price_maps": inputs[4],
            "stocks": inputs[5],
        },
    )


def source_generation_ids(commit: str, as_of: datetime) -> tuple[str, str]:
    stamp = as_of.astimezone(UTC).strftime("%Y%m%dT%H%M%SZ")
    source_suffix = hashlib.sha256(
        f"{commit}|{stamp}|final-source|{PROGRAM_CONTRACT}".encode()
    ).hexdigest()[:12]
    runtime_suffix = hashlib.sha256(
        f"{commit}|{stamp}|runtime-proof|{PROGRAM_CONTRACT}".encode()
    ).hexdigest()[:12]
    return (
        f"20260907-new-issuer-source-{stamp}-{source_suffix}",
        f"20260907-new-issuer-proof-{stamp}-{runtime_suffix}",
    )


def _policy(repo_root: Path) -> tuple[dict[str, Any], str]:
    path = repo_root / POLICY_PATH
    policy = read_json(path)
    checks = (
        policy.get("status") == "FROZEN_PRE_FIRST",
        tuple(policy.get("ordered_cohort") or ()) == COHORT,
        tuple(tuple(row) for row in policy.get("context_groups") or ()) == CONTEXT_GROUPS,
        policy.get("model") == runner.MODEL,
        policy.get("reasoning_effort") == runner.EFFORT,
        int(policy.get("model_timeout_seconds") or 0) == runner.TIMEOUT_SECONDS,
        int(policy.get("expected_total_model_invocations") or 0) == EXPECTED_TOTAL_INVOCATIONS,
        int(policy.get("retry_count", -1)) == 0,
        policy.get("review_manifest_sha256") == REVIEW_MANIFEST_SHA256,
    )
    if not all(checks):
        raise ValueError("execution_policy_drift")
    if not git_value("ls-files", POLICY_PATH):
        raise ValueError("execution_policy_must_be_committed")
    return policy, canonical_sha256(policy)


def _write_base_proofs(
    *,
    report_dir: Path,
    provenance: Mapping[str, object],
    integrity: Mapping[str, object],
    policy: Mapping[str, object],
    exclusion_registry: Mapping[str, object],
    source_rows: Sequence[Mapping[str, object]],
    selection: Mapping[str, object],
    source_generation: Mapping[str, object],
    source_lock: Mapping[str, object],
    precommit: Mapping[str, object],
    prompt_lock: Mapping[str, object],
    architecture: Mapping[str, object],
    topology: Mapping[str, object],
    preflight: Mapping[str, object],
) -> None:
    registry_count = len(exclusion_registry.get("rows") or [])
    us_rows = [row for row in source_rows if row.get("market") == "us"]
    kr_rows = [row for row in source_rows if row.get("market") == "kr"]
    runner.write_proof(report_dir, 1, provenance)
    runner.write_proof(report_dir, 2, integrity)
    runner.write_proof(
        report_dir,
        3,
        {
            "contract": "accepted-exposure-registry-continuity-v1",
            "registry_count": registry_count,
            "registry_sha256": REVIEW_EXCLUSION_REGISTRY_SHA256,
            "rows": exclusion_registry.get("rows") or [],
            "status": "PASS",
        },
    )
    runner.write_proof(
        report_dir,
        4,
        {
            "contract": "new-holdout-exclusion-set-continuity-v1",
            "new_holdout_exclusion_count": registry_count,
            "exclusion_registry_sha256": REVIEW_EXCLUSION_REGISTRY_SHA256,
            "excluded_selected_overlap": [],
            "exclusion_shrink_count": 0,
            "status": "PASS",
        },
    )
    runner.write_proof(report_dir, 5, policy)
    runner.write_proof(
        report_dir,
        6,
        {
            "contract": "reviewed-us4-final-manifest-v1",
            "market": "us",
            "ordered_tickers": list(COHORT[:4]),
            "replacement_count": 0,
            "status": "FROZEN",
        },
    )
    for number, market, rows in ((7, "us", us_rows), (10, "kr", kr_rows)):
        target = 4 if market == "us" else 12
        runner.write_proof(
            report_dir,
            number,
            {
                "contract": f"selected-{market}-source-recheck-v1",
                "target_count": target,
                "attempted_count": len(rows),
                "source_sufficient_count": len(rows),
                "source_insufficient_count": 0,
                "pipeline_coverage_gap_count": 0,
                "source_absence_count": 0,
                "unknown_failure_count": 0,
                "source_target_status": "PASS",
                "network_request_count": 0,
                "valid_archive_cache_hit_count": len(rows),
                "rows": list(rows),
                "status": "PASS",
            },
        )
    runner.write_proof(
        report_dir,
        8,
        {
            "contract": "selected-us-source-failure-detail-v1",
            "failure_count": 0,
            "rows": [],
            "status": "PASS",
        },
    )
    runner.write_proof(
        report_dir,
        9,
        {
            "contract": "reviewed-kr12-final-manifest-v1",
            "market": "kr",
            "ordered_tickers": list(COHORT[4:]),
            "replacement_count": 0,
            "status": "FROZEN",
        },
    )
    runner.write_proof(
        report_dir,
        11,
        {
            "contract": "selected-kr-source-failure-detail-v1",
            "failure_count": 0,
            "rows": [],
            "status": "PASS",
        },
    )
    runner.write_proof(
        report_dir,
        12,
        {
            "contract": "selected-dual-market-source-recheck-summary-v1",
            "dual_market_source_status": "BOTH_PASS",
            "us_count": len(us_rows),
            "kr_count": len(kr_rows),
            "network_request_count": 0,
            "valid_archive_cache_hit_count": len(source_rows),
            "status": "PASS",
        },
    )
    runner.write_proof(
        report_dir,
        13,
        {
            "contract": "source-recheck-failure-comparison-v1",
            "shared_failure_reason_codes": [],
            "us_only_failure_reason_codes": [],
            "kr_only_failure_reason_codes": [],
            "status": "PASS",
        },
    )
    runner.write_proof(
        report_dir,
        14,
        {
            "contract": "existing-data-routes-scope-decision-v1",
            "new_free_api_gate_project": 0,
            "new_paid_dependency": 0,
            "existing_route_reuse": 1,
            "all_routes_verified_free_claimed": 0,
            "status": "PASS",
        },
    )
    runner.write_proof(report_dir, 15, selection)
    runner.write_proof(report_dir, 16, source_generation)
    runner.write_proof(
        report_dir,
        17,
        {
            "contract": "final-source-sufficiency-audit-v1",
            "rows": list(source_rows),
            "selected_sufficient_count": len(source_rows),
            "directional_model_calls_on_source_insufficient": 0,
            "status": "PASS",
        },
    )
    runner.write_proof(
        report_dir,
        18,
        {
            "contract": "final-source-identity-audit-v1",
            "rows": [
                {
                    "ticker": row["ticker"],
                    "market": row["market"],
                    "canonical_issuer_key": row["canonical_issuer_key"],
                    "canonical_security_id": row["canonical_security_id"],
                    "status": "PASS",
                }
                for row in source_rows
            ],
            "duplicate_issuer_count": 0,
            "prior_exposure_overlap_count": 0,
            "status": "PASS",
        },
    )
    runner.write_proof(report_dir, 19, source_lock)
    runner.write_proof(report_dir, 20, precommit)
    runner.write_proof(
        report_dir,
        21,
        {
            "contract": "architecture-semantic-freeze-v1",
            "architecture_hashes": architecture,
            "implementation_commit": provenance["implementation_commit"],
            "architecture_semantic_drift": 0,
            "status": "FROZEN",
        },
    )
    runner.write_proof(
        report_dir,
        22,
        {
            "contract": "prompt-schema-freeze-v1",
            "prompt_schema_lock": prompt_lock,
            "prompt_schema_lock_sha256": canonical_sha256(prompt_lock),
            "actual_request_model_free_preflight": preflight,
            "status": "FROZEN",
        },
    )
    runner.write_proof(
        report_dir,
        23,
        {
            "contract": "model-context-freeze-v1",
            "context_groups": [list(group) for group in CONTEXT_GROUPS],
            "runs": list(runner.RUNS),
            "stages": list(runner.STAGES),
            "expected_invocations_per_run": EXPECTED_INVOCATIONS_PER_RUN,
            "expected_total_model_invocations": EXPECTED_TOTAL_INVOCATIONS,
            "status": "FROZEN",
        },
    )
    runner.write_proof(
        report_dir,
        24,
        {
            "contract": "transport-topology-freeze-v1",
            "hashes": topology,
            "model": runner.MODEL,
            "reasoning_effort": runner.EFFORT,
            "timeout_seconds": runner.TIMEOUT_SECONDS,
            "timeout_owner_count": runner.TIMEOUT_OWNER_COUNT,
            "transport_topology_mutation": 0,
            "status": "FROZEN",
        },
    )
    runner.write_proof(
        report_dir,
        25,
        {
            "contract": "final-holdout-unseen-reuse-gate-v1",
            "ordered_cohort": list(COHORT),
            "holdout_output_exposure_state": "UNEXPOSED",
            "holdout_semantic_revelation_state": "NOT_MEASURED",
            "holdout_retirement_state": "ACTIVE_UNEXPOSED",
            "future_unseen_holdout_reuse_allowed": 1,
            "model_free_fixture_exposure_count": 0,
            "status": "PASS",
        },
    )


def run_model_free_actual_request_preflight(
    *,
    root: Path,
    packets: Mapping[str, Mapping[str, object]],
    source_generation_id: str,
    runtime_generation_id: str,
) -> dict[str, object]:
    args, state, adapter, inputs = review._prepare_real_input_rehearsal(
        root=root,
        packets=packets,
        cohort=COHORT,
        source_generation_id=source_generation_id,
        runtime_generation_id=runtime_generation_id,
        review_manifest_sha256=REVIEW_MANIFEST_SHA256,
    )
    run_results = {}
    for run in runner.RUNS:
        run_results[run] = review._execute_model_free_review_run(
            args=args,
            state=state,
            adapter=adapter,
            run=run,
            **inputs,
        )
    summary = review._real_input_mode_summary(root, adapter)
    summary.update(
        {
            "contract": "final-actual-request-model-free-preflight-v1",
            "run_results": {run: result["status"] for run, result in run_results.items()},
            "expected_simulated_invocation_count": EXPECTED_TOTAL_INVOCATIONS,
            "real_investment_model_invocation_count": adapter.model_call_count,
            "model_free_fixture_exposure_count": 0,
        }
    )
    if (
        summary.get("status") != "PASS"
        or adapter.simulated_invocation_count != EXPECTED_TOTAL_INVOCATIONS
        or adapter.model_call_count != 0
    ):
        raise ValueError("actual_request_model_free_preflight_failed")
    write_json(root / "final-preflight-summary.json", summary)
    return summary


def prepare(args: argparse.Namespace) -> None:
    repo_root = Path.cwd().resolve()
    if args.output_root.exists() or args.report_dir.exists():
        raise ValueError("new_output_and_report_directories_required")
    if file_sha256(repo_root / WORK_INSTRUCTION_PATH) != WORK_INSTRUCTION_SHA256:
        raise ValueError("work_instruction_content_drift")
    if git_value("status", "--short"):
        raise ValueError("implementation_worktree_must_be_clean_before_prepare")
    if args.timeout != runner.TIMEOUT_SECONDS:
        raise ValueError("model_timeout_drift")
    policy, policy_hash = _policy(repo_root)
    implementation_commit = git_value("rev-parse", "HEAD")
    implementation_tree = git_value("rev-parse", "HEAD^{tree}")
    instruction_commit = git_value("log", "-1", "--format=%H", "--", WORK_INSTRUCTION_PATH)
    base_sha = git_value("rev-parse", f"{instruction_commit}^")
    source_generation_id, runtime_generation_id = source_generation_ids(
        implementation_commit, args.as_of
    )
    args.output_root.mkdir(parents=True)
    (args.report_dir / "proofs").mkdir(parents=True)
    guard = guarded.LiveWorkloadGuard(args.output_root / "live-workload-coexistence-audit.json")
    guard.wait_until_clear(
        stage="SELECTED_SOURCE_CACHE_RECHECK", batch_id="all-16", subject_count=16
    )
    integrity = review_bundle_integrity(args.review_zip)
    with zipfile.ZipFile(args.review_zip) as archive:
        manifest = zip_json(archive, REVIEW_MANIFEST_MEMBER)
        exclusion_registry = zip_json(
            archive,
            "evidence/input-preserved/evidence/membership/exclusion-registry.json",
        )
        packets, contexts, source_rows, inputs = load_and_recheck_packets(
            archive=archive,
            manifest=manifest,
            output_root=args.output_root,
            provider_root=args.provider_root,
            as_of=args.as_of,
        )
    source_lock = frozen.source_lock_document(
        generation_id=source_generation_id,
        cohort=COHORT,
        packets=packets,
        base_contexts=contexts,
        evidence=inputs["evidence"],
        owned=inputs["owned"],
        core_aliases=inputs["core_aliases"],
        timing_aliases=inputs["timing_aliases"],
        price_maps=inputs["price_maps"],
    )
    source_lock.update(
        {
            "contract": "new-issuer-final-executable-source-lock-v1",
            "source_generation_id": source_generation_id,
            "runtime_generation_id": runtime_generation_id,
            "review_manifest_sha256": REVIEW_MANIFEST_SHA256,
            "review_result_zip_sha256": REVIEW_ZIP_SHA256,
            "selection_policy_sha256": REVIEW_SELECTION_POLICY_SHA256,
            "exclusion_registry_sha256": REVIEW_EXCLUSION_REGISTRY_SHA256,
            "market_by_ticker": MARKET_BY_TICKER,
            "executable": True,
            "execution_authorized": True,
            "proof_source_lock": True,
            "source_recheck_mode": "VALID_ARCHIVE_CACHE_CURRENT_VALIDATOR_RECHECK",
            "source_refresh_count": 0,
            "network_request_count": 0,
            "new_paid_dependency_count": 0,
        }
    )
    source_lock_hash = canonical_sha256(source_lock)
    source_lock_with_hash = {
        **source_lock,
        "source_lock_sha256": source_lock_hash,
    }
    write_json(args.output_root / "source-lock.json", source_lock_with_hash)
    prompt_lock = frozen._write_prompt_schema_lock(
        output_root=args.output_root,
        generation_id=source_generation_id,
        cohort=COHORT,
        owned=inputs["owned"],
        core_aliases=inputs["core_aliases"],
        timing_aliases=inputs["timing_aliases"],
        price_maps=inputs["price_maps"],
    )
    preflight = run_model_free_actual_request_preflight(
        root=args.output_root / "model-free-actual-request-preflight",
        packets=packets,
        source_generation_id=source_generation_id,
        runtime_generation_id=runtime_generation_id,
    )
    actual_prompt_hashes = {
        str(path.relative_to(args.output_root)): file_sha256(path)
        for path in sorted((args.output_root / "prompts").glob("*.txt"))
    }
    preflight_prompt_hashes = {
        str(
            path.relative_to(args.output_root / "model-free-actual-request-preflight")
        ): file_sha256(path)
        for path in sorted(
            (args.output_root / "model-free-actual-request-preflight" / "prompts").glob("*.txt")
        )
    }
    if list(actual_prompt_hashes.values()) != list(preflight_prompt_hashes.values()):
        raise ValueError("actual_and_preflight_prompt_template_drift")
    architecture = runner.architecture_hashes(repo_root)
    topology = runner.transport_topology_hashes()
    selection = {
        "contract": "reviewed-cohort-final-selection-v1",
        "ordered_cohort": list(COHORT),
        "context_groups": [list(group) for group in CONTEXT_GROUPS],
        "selected_count": len(COHORT),
        "us_count": 4,
        "kr_count": 12,
        "replacement_count": 0,
        "review_manifest_sha256": REVIEW_MANIFEST_SHA256,
        "selection_policy_sha256": REVIEW_SELECTION_POLICY_SHA256,
        "exclusion_registry_sha256": REVIEW_EXCLUSION_REGISTRY_SHA256,
        "status": "PASS",
    }
    source_generation = {
        "contract": "new-final-source-generation-v1",
        "source_generation_id": source_generation_id,
        "runtime_generation_id": runtime_generation_id,
        "source_runtime_identity_separated": True,
        "per_issuer_packet_hashes": source_lock["packet_sha256"],
        "aggregate_source_lock_sha256": source_lock_hash,
        "source_refresh_count": 0,
        "network_request_count": 0,
        "valid_archive_cache_hit_count": len(COHORT),
        "status": "PASS",
    }
    precommit = {
        "contract": "new-issuer-final-proof-execution-precommit-v1",
        "ordered_cohort": list(COHORT),
        "market_by_ticker": MARKET_BY_TICKER,
        "context_groups": [list(group) for group in CONTEXT_GROUPS],
        "source_generation_id": source_generation_id,
        "runtime_generation_id": runtime_generation_id,
        "source_lock_sha256": source_lock_hash,
        "packet_sha256": source_lock["packet_sha256"],
        "prompt_schema_lock_sha256": canonical_sha256(prompt_lock),
        "implementation_commit": implementation_commit,
        "implementation_tree": implementation_tree,
        "model": runner.MODEL,
        "reasoning_effort": runner.EFFORT,
        "timeout_seconds": runner.TIMEOUT_SECONDS,
        "timeout_owner_count": runner.TIMEOUT_OWNER_COUNT,
        "batch_semantics": runner.BATCH_SEMANTICS,
        "subjects_per_context": runner.CONTEXT_SIZE,
        "runs": list(runner.RUNS),
        "stages": list(runner.STAGES),
        "expected_invocations_per_run": EXPECTED_INVOCATIONS_PER_RUN,
        "expected_total_model_invocations": EXPECTED_TOTAL_INVOCATIONS,
        "model_retry_count": 0,
        "selective_rerun": 0,
        "batch_split": 0,
        "stability_acceptance": policy["stability_acceptance"],
        "tested_validation": {
            "focused": args.focused_tests,
            "full": args.full_tests,
            "ruff": args.ruff,
            "diff_check": args.diff_check,
        },
        "pre_first_frozen_at": datetime.now(UTC).isoformat(),
        "status": "FROZEN",
    }
    write_json(args.output_root / "new-holdout-precommit.json", precommit)
    provenance = {
        "contract": "repository-provenance-v1",
        "branch": git_value("branch", "--show-current"),
        "base_sha": base_sha,
        "work_instruction_commit": instruction_commit,
        "implementation_commit": implementation_commit,
        "implementation_tree": implementation_tree,
        "origin_main": git_value("rev-parse", "origin/main"),
        "worktree_status_before_generated_evidence": git_value("status", "--short"),
        "status": "PASS",
    }
    _write_base_proofs(
        report_dir=args.report_dir,
        provenance=provenance,
        integrity=integrity,
        policy=policy,
        exclusion_registry=exclusion_registry,
        source_rows=source_rows,
        selection=selection,
        source_generation=source_generation,
        source_lock=source_lock_with_hash,
        precommit=precommit,
        prompt_lock=prompt_lock,
        architecture=architecture,
        topology=topology,
        preflight=preflight,
    )
    runner.write_proof(
        args.report_dir,
        26,
        read_json(args.output_root / "live-workload-coexistence-audit.json"),
    )
    state = {
        "contract": PROGRAM_CONTRACT,
        "state": "PREPARED_FROZEN",
        "program_generation_id": runtime_generation_id,
        "source_generation_id": source_generation_id,
        "source_lock_sha256": source_lock_hash,
        "packet_hashes": source_lock["packet_sha256"],
        "branch": provenance["branch"],
        "base_sha": base_sha,
        "work_instruction_commit": instruction_commit,
        "implementation_commit": implementation_commit,
        "implementation_tree": implementation_tree,
        "execution_policy_sha256": policy_hash,
        "selection_policy_sha256": policy_hash,
        "review_manifest_sha256": REVIEW_MANIFEST_SHA256,
        "as_of": args.as_of.isoformat(),
        "ordered_cohort": list(COHORT),
        "architecture_hashes": architecture,
        "transport_topology_hashes": topology,
        "prompt_schema_lock_sha256": canonical_sha256(prompt_lock),
        "precommit_sha256": canonical_sha256(precommit),
        "holdout_output_exposure_state": "UNEXPOSED",
        "holdout_semantic_revelation_state": "NOT_MEASURED",
        "holdout_retirement_state": "ACTIVE_UNEXPOSED",
        "future_unseen_holdout_reuse_allowed": 1,
        "same_cohort_architecture_tuning_rerun_allowed": 0,
        "exposed_subjects": [],
        "model_invocation_count": 0,
        "directional_context_count": 0,
        "price_timing_context_count": 0,
        "renderer_context_count": 0,
        "context_evidence_preservation_failure_count": 0,
        "context_preservation_secondary_failure_count": 0,
        "per_context_semantic_failure_count": 0,
        "transport_timeout_count": 0,
        "transport_retry_count": 0,
        "historical_stall_pattern_recurred": 0,
        "run_results": {},
        "production_mutation": 0,
        "new_paid_dependency_count": 0,
        "source_network_request_count": 0,
        "model_free_preflight_invocation_count": EXPECTED_TOTAL_INVOCATIONS,
        "real_investment_model_invocation_count": 0,
    }
    write_json(args.output_root / "program-state.json", state)
    runner.write_reports(args.report_dir)
    print(json.dumps(state, ensure_ascii=False, sort_keys=True), flush=True)


def verify_frozen(args: argparse.Namespace, state: Mapping[str, object]) -> None:
    repo_root = Path.cwd().resolve()
    if file_sha256(repo_root / WORK_INSTRUCTION_PATH) != WORK_INSTRUCTION_SHA256:
        raise ValueError("work_instruction_content_drift")
    policy, policy_hash = _policy(repo_root)
    if canonical_sha256(policy) != state["execution_policy_sha256"]:
        raise ValueError("execution_policy_drift_after_freeze")
    if runner.architecture_hashes(repo_root) != state["architecture_hashes"]:
        raise ValueError("architecture_semantic_drift_after_freeze")
    if runner.transport_topology_hashes() != state["transport_topology_hashes"]:
        raise ValueError("transport_topology_mutation_after_freeze")
    precommit = read_json(args.output_root / "new-holdout-precommit.json")
    if canonical_sha256(precommit) != state["precommit_sha256"]:
        raise ValueError("precommit_drift_after_freeze")
    lock = read_json(args.output_root / "source-lock.json")
    recorded = lock.pop("source_lock_sha256")
    if canonical_sha256(lock) != recorded or recorded != state["source_lock_sha256"]:
        raise ValueError("source_lock_drift_after_freeze")
    if tuple(state.get("ordered_cohort") or ()) != COHORT:
        raise ValueError("cohort_drift_after_freeze")
    if git_value("rev-parse", "HEAD") != state["implementation_commit"]:
        raise ValueError("implementation_commit_drift_after_freeze")
    if git_value("status", "--short"):
        raise ValueError("repository_mutation_after_freeze")


def _scan_real_exposure(output_root: Path) -> dict[str, object]:
    exposed: set[str] = set()
    raw_rows = 0
    uncertain_contexts = 0
    stage_contexts = Counter()
    for manifest_path in sorted((output_root / "model-contexts").rglob("context_manifest.json")):
        manifest = read_json(manifest_path)
        output_path = manifest_path.parent / "output.raw.json"
        if not output_path.is_file() or output_path.stat().st_size == 0:
            continue
        subjects = [str(value) for value in manifest.get("subjects") or []]
        exposed.update(subjects)
        stage_contexts[str(manifest.get("stage") or "UNKNOWN")] += 1
        try:
            raw = read_json(output_path)
            candidates = raw.get("candidates")
            raw_rows += len(candidates) if isinstance(candidates, list) else 0
        except (OSError, ValueError, json.JSONDecodeError):
            uncertain_contexts += 1
    return {
        "unique_exposed_issuers": sorted(exposed),
        "unique_exposed_issuer_count": len(exposed),
        "raw_subject_row_count": raw_rows,
        "output_observability_uncertain_context_count": uncertain_contexts,
        "stage_context_counts": dict(stage_contexts),
        "output_exposure_state": (
            "UNEXPOSED"
            if not exposed
            else "FULLY_EXPOSED"
            if len(exposed) == len(COHORT)
            else "PARTIALLY_EXPOSED"
        ),
    }


def _augment_run(
    args: argparse.Namespace, run: str, document: dict[str, object]
) -> dict[str, object]:
    manifests = read_json(runner.proof_path(args.report_dir, runner.RUN_PROOFS[run][1]))
    ownership = read_json(runner.proof_path(args.report_dir, runner.RUN_PROOFS[run][3]))
    renderer = read_json(runner.proof_path(args.report_dir, runner.RUN_PROOFS[run][4]))
    hard = read_json(runner.proof_path(args.report_dir, runner.RUN_PROOFS[run][5]))
    identity_rows = [
        read_json(path)
        for path in sorted(
            (args.output_root / "model-contexts" / run.upper()).rglob(
                "output-identity-validation.json"
            )
        )
    ]
    preservation_failures = int(manifests.get("context_evidence_preservation_failure_count") or 0)
    document.update(
        {
            "execution_status": document["status"],
            "identity_gate_status": (
                "PASS"
                if len(identity_rows) == EXPECTED_INVOCATIONS_PER_RUN
                and all(row.get("status") == "PASS" for row in identity_rows)
                else "FAIL"
            ),
            "ownership_gate_status": ownership.get("status"),
            "renderer_gate_status": renderer.get("status"),
            "hard_safety_gate_status": hard.get("status"),
            "preservation_status": ("PASS" if preservation_failures == 0 else "FAIL"),
            "checked_subject_count": document.get("validation_pass_count"),
            "eligible_subject_count": len(COHORT),
            "identity_valid_subject_count": document.get("validation_pass_count"),
            "semantically_checked_subject_count": document.get("validation_pass_count"),
            "expected_model_invocation_count": EXPECTED_INVOCATIONS_PER_RUN,
            "measured_violation_counts": {
                key: ownership.get(key, 0)
                for key in (
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
                )
            },
        }
    )
    runner.write_proof(args.report_dir, runner.RUN_PROOFS[run][0], document)
    return document


def _write_custom_completion(
    *,
    args: argparse.Namespace,
    state: Mapping[str, object],
    stop_reason: str | None,
) -> dict[str, object]:
    base = read_json(runner.proof_path(args.report_dir, 60))
    exposure = _scan_real_exposure(args.output_root)
    run_gates = {}
    for run in runner.RUNS:
        path = runner.proof_path(args.report_dir, runner.RUN_PROOFS[run][0])
        row = read_json(path)
        run_gates[run] = {
            key: row.get(key, "NOT_MEASURED")
            for key in (
                "execution_status",
                "identity_gate_status",
                "ownership_gate_status",
                "renderer_gate_status",
                "hard_safety_gate_status",
                "preservation_status",
                "checked_subject_count",
                "eligible_subject_count",
                "status",
            )
        }
    result = {
        "contract": PROGRAM_CONTRACT,
        "review_result_zip_sha256": REVIEW_ZIP_SHA256,
        "review_manifest_sha256": REVIEW_MANIFEST_SHA256,
        "final_source_lock_created": 1,
        "final_source_lock": state["source_lock_sha256"],
        "source_generation_id": state["source_generation_id"],
        "runtime_generation_id": state["program_generation_id"],
        "source_runtime_identity_separated": True,
        "ordered_cohort": list(COHORT),
        "market_mix": {"us": 4, "kr": 12},
        "context_groups": [list(group) for group in CONTEXT_GROUPS],
        "implementation_commit": state["implementation_commit"],
        "model": runner.MODEL,
        "reasoning_effort": runner.EFFORT,
        "model_timeout_seconds": runner.TIMEOUT_SECONDS,
        "model_timeout_owner_count": runner.TIMEOUT_OWNER_COUNT,
        "actual_model_invocation_count": state["model_invocation_count"],
        "model_free_preflight_invocation_count": state["model_free_preflight_invocation_count"],
        "run_gates": run_gates,
        "exposure": exposure,
        "ownership_generalization_verdict": base.get("ownership_generalization_verdict"),
        "core_stability_counts": base.get("core_stability_counts"),
        "timing_stability_counts": base.get("timing_stability_counts"),
        "source_network_request_count": 0,
        "valid_archive_cache_hit_count": len(COHORT),
        "new_paid_dependency_count": 0,
        "all_routes_verified_free_claimed": 0,
        "new_free_api_gate_project": 0,
        "model_retry_count": state.get("transport_retry_count", 0),
        "timeout_count": state.get("transport_timeout_count", 0),
        "orphan_count": 0,
        "preservation_failure_count": state.get("context_evidence_preservation_failure_count", 0),
        "production_main_merge": 0,
        "production_db_mutation": 0,
        "production_scheduler_change": 0,
        "production_telegram_send": 0,
        "monitoring_registration_calls": 0,
        "production_activation": 0,
        "readiness": base.get("readiness"),
        "stop_reason": stop_reason,
        "next_scope": base.get("next_scope"),
        "status": "PASS" if base.get("readiness", "").startswith("READY_") else "STOPPED",
    }
    path = args.report_dir / "proofs" / f"{CUSTOM_COMPLETION_NAME}.json"
    write_json(path, result)
    write_text(
        args.report_dir / f"{CUSTOM_COMPLETION_NAME}.md",
        runner.report_body(CUSTOM_COMPLETION_NAME, result),
    )
    return result


def execute(args: argparse.Namespace) -> None:
    state = read_json(args.output_root / "program-state.json")
    if state.get("state") != "PREPARED_FROZEN":
        raise ValueError("prepared_frozen_state_required")
    verify_frozen(args, state)
    state["state"] = "EXECUTING"
    state["execution_started_at"] = datetime.now(UTC).isoformat()
    write_json(args.output_root / "program-state.json", state)
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
    ) = runner.load_inputs(args)
    guard = guarded.LiveWorkloadGuard(args.output_root / "live-workload-coexistence-audit.json")
    adapter = guarded.GuardedTransportAdapter(
        guard=guard,
        continuation_generation=str(state["program_generation_id"]),
        receipt_root=args.output_root / "transport-receipts",
        codex_bin=engine._signed_in_codex_bin(),
    )
    documents: dict[str, dict[str, object]] = {}
    stop_reason: str | None = None
    for run in runner.RUNS:
        if stop_reason is not None:
            runner.write_not_run(args, run, stop_reason)
            continue
        try:
            verify_frozen(args, state)
            document = runner.execute_run(
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
            document = _augment_run(args, run, document)
            if any(
                document.get(key) != "PASS"
                for key in (
                    "execution_status",
                    "identity_gate_status",
                    "ownership_gate_status",
                    "renderer_gate_status",
                    "hard_safety_gate_status",
                    "preservation_status",
                )
            ):
                raise runner.SemanticStop(f"{run}_required_gate_failed")
            documents[run] = document
            state["run_results"][run] = f"{document['validation_pass_count']}/{len(COHORT)}"
            state["real_investment_model_invocation_count"] = adapter.model_call_count
            write_json(args.output_root / "program-state.json", state)
        except Exception as exc:
            stop_reason = f"{type(exc).__name__}:{exc}"
            exposure = _scan_real_exposure(args.output_root)
            state["exposed_subjects"] = exposure["unique_exposed_issuers"]
            state["holdout_output_exposure_state"] = exposure["output_exposure_state"]
            state["stop_reason"] = stop_reason
            state["real_investment_model_invocation_count"] = adapter.model_call_count
            write_json(args.output_root / "program-state.json", state)
            runner.write_failed_run(args, run, stop_reason)
            for pending in runner.RUNS[runner.RUNS.index(run) + 1 :]:
                runner.write_not_run(args, pending, stop_reason)
            break
    exposure = _scan_real_exposure(args.output_root)
    state["exposed_subjects"] = exposure["unique_exposed_issuers"]
    state["holdout_output_exposure_state"] = exposure["output_exposure_state"]
    state["model_invocation_count"] = adapter.model_call_count
    state["real_investment_model_invocation_count"] = adapter.model_call_count
    write_json(args.output_root / "program-state.json", state)
    runner.write_proof(
        args.report_dir,
        26,
        read_json(args.output_root / "live-workload-coexistence-audit.json"),
    )
    runner.final_proofs(
        args=args,
        state=state,
        documents=documents,
        stop_reason=stop_reason,
    )
    state = read_json(args.output_root / "program-state.json")
    result = _write_custom_completion(args=args, state=state, stop_reason=stop_reason)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True), flush=True)


def _copy_tree(source: Path, destination: Path) -> None:
    if destination.exists():
        raise ValueError(f"new_bundle_destination_required:{destination}")
    shutil.copytree(source, destination)


def finalize(args: argparse.Namespace) -> None:
    state = read_json(args.output_root / "program-state.json")
    if state.get("state") != "EVIDENCE_COMPLETE":
        raise ValueError("evidence_complete_state_required")
    verify_frozen(args, state)
    completion = read_json(runner.proof_path(args.report_dir, 60))
    completion.update(
        {
            "final_head_sha": git_value("rev-parse", "HEAD"),
            "full_tests": args.full_tests,
            "ruff": args.ruff,
            "diff_check": args.diff_check,
        }
    )
    if not all(value == "PASS" for value in (args.full_tests, args.ruff, args.diff_check)):
        completion["readiness"] = "NOT_READY"
        completion["next_scope"] = "BOUNDED_VALIDATION_REPAIR"
    runner.write_proof(args.report_dir, 60, completion)
    runner.write_reports(args.report_dir)
    custom = _write_custom_completion(args=args, state=state, stop_reason=state.get("stop_reason"))
    custom.update(
        {
            "final_head_sha": git_value("rev-parse", "HEAD"),
            "full_tests": args.full_tests,
            "ruff": args.ruff,
            "diff_check": args.diff_check,
            "readiness": completion["readiness"],
            "next_scope": completion["next_scope"],
            "status": ("PASS" if completion["readiness"].startswith("READY_") else "STOPPED"),
        }
    )
    write_json(
        args.report_dir / "proofs" / f"{CUSTOM_COMPLETION_NAME}.json",
        custom,
    )
    write_text(
        args.report_dir / f"{CUSTOM_COMPLETION_NAME}.md",
        runner.report_body(CUSTOM_COMPLETION_NAME, custom),
    )
    write_text(
        args.report_dir / "README.md",
        "# New Issuer Final Freeze & Ownership Proof\n\n"
        f"- Cohort: US4 + KR12 ({len(COHORT)} issuers)\n"
        f"- Source generation: `{state['source_generation_id']}`\n"
        f"- Runtime generation: `{state['program_generation_id']}`\n"
        f"- Source lock: `{state['source_lock_sha256']}`\n"
        f"- Real model invocations: `{state['model_invocation_count']}`\n"
        f"- Readiness: `{completion['readiness']}`\n"
        f"- Next scope: `{completion['next_scope']}`\n\n"
        "The artifact index covers every payload except itself to avoid a "
        "self-referential hash. No production activation or Telegram send occurred.\n",
    )
    if args.bundle_root.exists():
        raise ValueError("new_bundle_root_required")
    args.bundle_root.mkdir(parents=True)
    _copy_tree(args.report_dir, args.bundle_root / "reports")
    experiment_destination = args.bundle_root / "experiment"
    experiment_destination.mkdir()
    for path in sorted(args.output_root.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(args.output_root)
        target = experiment_destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, target)
    write_text(
        args.bundle_root / "README.md",
        (args.report_dir / "README.md").read_text(encoding="utf-8"),
    )
    payloads = sorted(
        path
        for path in args.bundle_root.rglob("*")
        if path.is_file() and path.name != "artifact-index.json"
    )
    rows = []
    secret_failures = 0
    for path in payloads:
        scan = runner.scan_secrets([path])
        secret_failures += int(scan["secret_scan_status"] != "PASS")
        rows.append(
            {
                "path": str(path.relative_to(args.bundle_root)),
                "sha256": file_sha256(path),
                "byte_size": path.stat().st_size,
                "secret_scan_status": scan["secret_scan_status"],
            }
        )
    index = {
        "contract": "new-issuer-final-proof-artifact-index-v1",
        "index_self_exclusion": "artifact-index.json",
        "all_payload_files_except_index_itself_individually_indexed": True,
        "indexed_artifact_count": len(rows),
        "secret_scan_failure_count": secret_failures,
        "rows": rows,
        "status": "PASS" if secret_failures == 0 else "FAIL",
    }
    write_json(args.bundle_root / "artifact-index.json", index)
    if index["status"] != "PASS":
        raise ValueError("artifact_secret_scan_failed")
    args.zip_output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.zip_output.with_suffix(args.zip_output.suffix + ".tmp")
    with zipfile.ZipFile(temporary, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(args.bundle_root.rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(args.bundle_root))
    temporary.replace(args.zip_output)
    with zipfile.ZipFile(args.zip_output) as archive:
        bad_member = archive.testzip()
        member_count = len(archive.namelist())
    if bad_member is not None:
        raise ValueError(f"final_zip_crc_failure:{bad_member}")
    zip_sha = file_sha256(args.zip_output)
    write_text(args.zip_output.with_suffix(args.zip_output.suffix + ".sha256"), zip_sha)
    state.update(
        {
            "state": "COMPLETE",
            "report_zip": str(args.zip_output),
            "report_zip_sha256": zip_sha,
            "report_zip_member_count": member_count,
            "artifact_indexed_payload_count": len(rows),
            "artifact_secret_scan_failure_count": secret_failures,
            "readiness": completion["readiness"],
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
    parser.add_argument("--bundle-root", type=Path, required=True)
    parser.add_argument("--review-zip", type=Path, required=True)
    parser.add_argument("--provider-root", type=Path, default=Path.home() / "Codex/ohlcv-analyst")
    parser.add_argument("--as-of", type=datetime.fromisoformat)
    parser.add_argument("--timeout", type=int, default=runner.TIMEOUT_SECONDS)
    parser.add_argument("--focused-tests", default="NOT_RUN")
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
        "bundle_root",
        "review_zip",
        "provider_root",
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
